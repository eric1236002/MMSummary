from __future__ import annotations

from typing import Any, Optional, Tuple

from backend.core import generate_summary

from .roles import plan_parameters, review_summary
from .state import AgentMeta, EffectiveParams, Plan, ReviewResult


def summarize_with_agents(
    *,
    request: Any,
    agent_mode: str,
    quality_check: bool,
    max_iters: int,
    planner_model: Optional[str] = None,
    reviewer_model: Optional[str] = None,
) -> Tuple[str, dict]:
    """Run Planner/Executor/Reviewer flow.

    - Executor reuses existing `backend.core.generate_summary`.
    - Returns (summary, meta_dict).

    This function is intentionally decoupled from FastAPI/Pydantic types.
    """

    effective = EffectiveParams.from_request(request)

    # Fast path for deterministic tests: skip planner/reviewer to keep snapshots stable.
    # 理由：測試模式下我們希望整個流程可重現且不受外部 agent 回應波動影響。
    # Planner/Reviewer 會呼叫外部模型，回傳可能不穩定，會使快照測試失敗。
    if getattr(request, "test_mode", False):
        summary = generate_summary(
            text=request.text,
            model=effective.model,
            chunk_size_1=effective.chunk_size_1,
            chunk_overlap_1=effective.chunk_overlap_1,
            chunk_size_2=effective.chunk_size_2,
            chunk_overlap_2=effective.chunk_overlap_2,
            token_max=effective.token_max,
            use_map=effective.use_map,
            test_mode=True,
            map_template=effective.map_template,
            reduce_template=effective.reduce_template,
            reduce_temperature=effective.reduce_temperature,
        )
        meta = AgentMeta(mode="test_mode", effective_params=effective)
        return summary, meta.to_dict()

    plan: Optional[Plan] = None
    review: Optional[ReviewResult] = None

    # Gate the optional planner/reviewer flow; "off" keeps legacy behavior.
    # 理由：允許透過 `agent_mode` 控制是否啟用自動調參/審查，
    # 方便在成本或延遲敏感時關閉這些額外步驟。
    enable_agents = agent_mode in {"on"}

    # Planner may adjust chunking/limits; fall back to original params on invalid JSON.
    # 理由：Planner 的目的是根據文字特性自動調整 `EffectiveParams`（例如 chunk_size），
    # 但 planner 可能回傳格式錯誤或未知值，因此在 `Plan()`（空計畫）時保留原參數。
    # 這樣可以避免 planner 錯誤導致整個摘要流程失敗。
    if enable_agents:
        plan = plan_parameters(text=request.text, effective=effective, planner_model=planner_model)
        if plan == Plan():
            print("Planner failed to return valid JSON. Proceeding with original parameters.")
        else:
            effective = effective.apply_plan(plan)

    summary = generate_summary(
        text=request.text,
        model=effective.model,
        chunk_size_1=effective.chunk_size_1,
        chunk_overlap_1=effective.chunk_overlap_1,
        chunk_size_2=effective.chunk_size_2,
        chunk_overlap_2=effective.chunk_overlap_2,
        token_max=effective.token_max,
        use_map=effective.use_map,
        test_mode=False,
        map_template=effective.map_template,
        reduce_template=effective.reduce_template,
        reduce_temperature=effective.reduce_temperature,
    )

    # Reviewer runs only when explicitly enabled and allowed by iteration budget.
    # 理由：Reviewer 會檢查並可能改寫摘要，這會增加成本與延遲；
    # 因此只有在使用者允許（quality_check）且剩餘檢查次數（max_iters）大於 0 時才執行。
    if enable_agents and quality_check and max_iters > 0:
        review = review_summary(
            text=request.text,
            draft_summary=summary,
            effective=effective,
            reviewer_model=reviewer_model,
        )
        if review.verdict == "revise" and review.revised_summary:
            summary = review.revised_summary

    meta = AgentMeta(mode=agent_mode, effective_params=effective, plan=plan, review=review)
    return summary, meta.to_dict()

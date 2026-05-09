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

    enable_agents = agent_mode in {"on"}

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

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional


# 使用 `@dataclass(frozen=True)`：將實例設為不可變（immutable）。
# 原因與好處：
# - 預防意外修改：流程中共享同一個 `EffectiveParams` 時，不會被其他程式碼不小心改寫，降低副作用。
# - 容易推理與測試：狀態變更會回傳新實例（例如 `apply_plan`），有助於重現與快照測試。
# - 執行緒安全性：不可變物件在多執行緒/非同步場景下更安全，降低 race condition 風險。
# - 可哈希（在欄位皆可 hash 時）：方便用於 cache 或當作 dict key（視欄位而定）。
# - 設計契合：搭配 `from_request`（工廠）與 `apply_plan`（回傳新實例）的模式，鼓勵純函式式更新。



@dataclass(frozen=True)
class EffectiveParams:
    model: str
    chunk_size_1: int
    chunk_overlap_1: int
    chunk_size_2: int
    chunk_overlap_2: int
    token_max: int
    use_map: bool
    map_template: Optional[str]
    reduce_template: Optional[str]
    reduce_temperature: float

    @classmethod
    # `@classmethod`：這是一個綁定到類別的工廠方法，第一個參數是類別本身（慣用名稱為 `cls`）。
    # 為何用 classmethod：
    # - 集中處理如何從外部請求（或 dict）建立 `EffectiveParams` 的邏輯（欄位對應、預設值、安全取值）。
    # - 使用 `cls(...)` 建構，對繼承友好：若有子類繼承並呼叫 `from_request`，會回傳子類的實例而非固定父類，保留多型性。
    # - 比起寫成外部函式或硬編碼類名，class method 更易於維護與擴充。
    def from_request(cls, request: Any) -> "EffectiveParams":
        return cls(
            model=request.model,
            chunk_size_1=request.chunk_size_1,
            chunk_overlap_1=request.chunk_overlap_1,
            chunk_size_2=request.chunk_size_2,
            chunk_overlap_2=request.chunk_overlap_2,
            token_max=request.token_max,
            use_map=request.use_map,
            map_template=getattr(request, "map_temple", None),
            reduce_template=getattr(request, "reduce_temple", None),
            reduce_temperature=getattr(request, "reduce_temperature", 0.0),
        )

    # 說明：`EffectiveParams` 包含摘要執行時需要的所有參數。
    # - 將使用者請求中的欄位轉成不可變的 dataclass，方便在流程中安全傳遞與序列化。
    # - `map_template`/`reduce_template` 允許自訂 map/reduce 的提示模板；若使用者未提供則為 None。

    def apply_plan(self, plan: "Plan") -> "EffectiveParams":
        # 理由：當 Planner 建議部分變更時，我們採用「局部覆蓋」策略：
        # 只有在 Plan 明確提供非 None 值時才覆蓋原參數，否則保留原值。
        # 這避免 planner 回傳不完整資料時意外重置重要欄位。
        return EffectiveParams(
            model=self.model if plan.model is None else plan.model,
            chunk_size_1=self.chunk_size_1 if plan.chunk_size_1 is None else plan.chunk_size_1,
            chunk_overlap_1=plan.chunk_overlap_1 if plan.chunk_overlap_1 is not None else self.chunk_overlap_1,
            chunk_size_2=self.chunk_size_2 if plan.chunk_size_2 is None else plan.chunk_size_2,
            chunk_overlap_2=plan.chunk_overlap_2 if plan.chunk_overlap_2 is not None else self.chunk_overlap_2,
            token_max=self.token_max if plan.token_max is None else plan.token_max,
            use_map=plan.use_map if plan.use_map is not None else self.use_map,
            map_template=plan.map_template if plan.map_template is not None else self.map_template,
            reduce_template=plan.reduce_template if plan.reduce_template is not None else self.reduce_template,
            reduce_temperature=(
                plan.reduce_temperature if plan.reduce_temperature is not None else self.reduce_temperature
            ),
        )

    # 說明：`apply_plan` 的設計保證了參數更新是可預測與安全的，
    # 並且維持 `EffectiveParams` 的不可變性（frozen dataclass），
    # 這降低在多步驟流程中出現副作用或競爭條件的風險。

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Plan:
    use_map: Optional[bool] = None
    chunk_size_1: Optional[int] = None
    chunk_overlap_1: Optional[int] = None
    chunk_size_2: Optional[int] = None
    chunk_overlap_2: Optional[int] = None
    token_max: Optional[int] = None
    reduce_temperature: Optional[float] = None
    model: Optional[str] = None
    map_template: Optional[str] = None
    reduce_template: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewResult:
    verdict: str  # "pass" | "revise"
    revised_summary: Optional[str] = None
    issues: Optional[list[str]] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentMeta:
    mode: str
    effective_params: EffectiveParams
    plan: Optional[Plan] = None
    review: Optional[ReviewResult] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "effective_params": self.effective_params.to_dict(),
            "plan": self.plan.to_dict() if self.plan else None,
            "review": self.review.to_dict() if self.review else None,
        }

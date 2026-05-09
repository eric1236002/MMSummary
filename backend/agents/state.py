from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional


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

    def apply_plan(self, plan: "Plan") -> "EffectiveParams":
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

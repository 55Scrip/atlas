"""HTTP response schemas for Decision Path & Required Progress. Wire
format is camelCase via the shared Core `CamelModel` (ADR-004). Every
field is a direct read of an already-computed `DecisionPath`/
comparison -- nothing is recomputed or reworded here."""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionPathChange,
    DecisionPathComparison,
    DecisionPathSummary,
    DecisionStep,
    PortfolioDecisionPathBreakdown,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class DecisionStepView(CamelModel):
    source: str
    code: str
    progress_kind: str
    reachability: str

    @classmethod
    def from_domain(cls, step: DecisionStep) -> "DecisionStepView":
        return cls(
            source=step.dependency.source.value,
            code=step.dependency.code,
            progress_kind=step.progress_kind.value,
            reachability=step.reachability.value,
        )


class DecisionPathView(CamelModel):
    case_id: str
    current_action: str
    current_strength: str
    steps: list[DecisionStepView]
    immediate_blocker: DecisionStepView | None
    next_achievable_improvement: DecisionStepView | None
    final_reachable_state: str
    generated_at: datetime

    @classmethod
    def from_domain(cls, path: DecisionPath) -> "DecisionPathView":
        return cls(
            case_id=path.case_id,
            current_action=path.current_action.value,
            current_strength=path.current_strength.value,
            steps=[DecisionStepView.from_domain(s) for s in path.steps],
            immediate_blocker=DecisionStepView.from_domain(path.immediate_blocker)
            if path.immediate_blocker is not None
            else None,
            next_achievable_improvement=DecisionStepView.from_domain(path.next_achievable_improvement)
            if path.next_achievable_improvement is not None
            else None,
            final_reachable_state=path.final_reachable_state.value,
            generated_at=path.generated_at,
        )


class DecisionPathSummaryView(CamelModel):
    case_id: str
    current_action: str
    final_reachable_state: str
    immediate_blocker: DecisionStepView | None
    next_achievable_improvement: DecisionStepView | None
    remaining_step_count: int
    generated_at: datetime

    @classmethod
    def from_domain(cls, summary: DecisionPathSummary) -> "DecisionPathSummaryView":
        return cls(
            case_id=summary.case_id,
            current_action=summary.current_action.value,
            final_reachable_state=summary.final_reachable_state.value,
            immediate_blocker=DecisionStepView.from_domain(summary.immediate_blocker)
            if summary.immediate_blocker is not None
            else None,
            next_achievable_improvement=DecisionStepView.from_domain(summary.next_achievable_improvement)
            if summary.next_achievable_improvement is not None
            else None,
            remaining_step_count=summary.remaining_step_count,
            generated_at=summary.generated_at,
        )


class DecisionPathComparisonView(CamelModel):
    a: DecisionPathView
    b: DecisionPathView
    shorter_path_case_id: str | None
    fewer_remaining_blockers_case_id: str | None
    more_operationally_dependent_case_id: str | None
    more_evidence_dependent_case_id: str | None

    @classmethod
    def from_domain(cls, comparison: DecisionPathComparison) -> "DecisionPathComparisonView":
        return cls(
            a=DecisionPathView.from_domain(comparison.a),
            b=DecisionPathView.from_domain(comparison.b),
            shorter_path_case_id=comparison.shorter_path_case_id,
            fewer_remaining_blockers_case_id=comparison.fewer_remaining_blockers_case_id,
            more_operationally_dependent_case_id=comparison.more_operationally_dependent_case_id,
            more_evidence_dependent_case_id=comparison.more_evidence_dependent_case_id,
        )


class DecisionPathChangeView(CamelModel):
    case_id: str
    previous_final_reachable_state: str
    current_final_reachable_state: str
    resolved_steps: list[DecisionStepView]
    new_steps: list[DecisionStepView]
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: DecisionPathChange) -> "DecisionPathChangeView":
        return cls(
            case_id=change.case_id,
            previous_final_reachable_state=change.previous_final_reachable_state.value,
            current_final_reachable_state=change.current_final_reachable_state.value,
            resolved_steps=[DecisionStepView.from_domain(s) for s in change.resolved_steps],
            new_steps=[DecisionStepView.from_domain(s) for s in change.new_steps],
            detected_at=change.detected_at,
        )


class PortfolioDecisionPathBreakdownView(CamelModel):
    """Deliverable 7 -- ticker lists only, in holdings order; never a
    ranking, never an allocation suggestion."""

    closest_to_investable: list[str]
    operationally_blocked: list[str]
    requiring_more_evidence: list[str]
    requiring_dependency_resolution: list[str]

    @classmethod
    def from_domain(cls, breakdown: PortfolioDecisionPathBreakdown) -> "PortfolioDecisionPathBreakdownView":
        return cls(
            closest_to_investable=list(breakdown.closest_to_investable),
            operationally_blocked=list(breakdown.operationally_blocked),
            requiring_more_evidence=list(breakdown.requiring_more_evidence),
            requiring_dependency_resolution=list(breakdown.requiring_dependency_resolution),
        )

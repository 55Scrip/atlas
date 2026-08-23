"""HTTP response schemas for Decision Explanation. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004). Every field is a
direct read of an already-computed `DecisionExplanation`/
`DecisionExplanationChange` -- nothing is recomputed or reworded here.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_explanation.models import (
    BlockingFinding,
    DecisionExplanation,
    DecisionExplanationChange,
    DecisionExplanationComparison,
    DecisionExplanationSummary,
    ExplanationChain,
    ExplanationReference,
    ExplanationSection,
    PortfolioDecisionExplanationBreakdown,
    SupportingFinding,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class ExplanationReferenceView(CamelModel):
    kind: str
    id: str

    @classmethod
    def from_domain(cls, reference: ExplanationReference) -> "ExplanationReferenceView":
        return cls(kind=reference.kind.value, id=reference.id)


class SupportingFindingView(CamelModel):
    reference: ExplanationReferenceView
    named_by: list[str]

    @classmethod
    def from_domain(cls, finding: SupportingFinding) -> "SupportingFindingView":
        return cls(
            reference=ExplanationReferenceView.from_domain(finding.reference),
            named_by=[layer.value for layer in finding.named_by],
        )


class BlockingFindingView(CamelModel):
    reference: ExplanationReferenceView
    named_by: list[str]
    is_change_trigger: bool

    @classmethod
    def from_domain(cls, finding: BlockingFinding) -> "BlockingFindingView":
        return cls(
            reference=ExplanationReferenceView.from_domain(finding.reference),
            named_by=[layer.value for layer in finding.named_by],
            is_change_trigger=finding.is_change_trigger,
        )


class ExplanationSectionView(CamelModel):
    kind: str
    item_count: int

    @classmethod
    def from_domain(cls, section: ExplanationSection) -> "ExplanationSectionView":
        return cls(kind=section.kind.value, item_count=section.item_count)


class ExplanationChainView(CamelModel):
    case_id: str
    order: list[ExplanationSectionView]
    supporting: list[SupportingFindingView]
    blocking: list[BlockingFindingView]
    dependency_steps: list[ExplanationReferenceView]
    historical_reference: ExplanationReferenceView | None

    @classmethod
    def from_domain(cls, chain: ExplanationChain) -> "ExplanationChainView":
        return cls(
            case_id=chain.case_id,
            order=[ExplanationSectionView.from_domain(s) for s in chain.order],
            supporting=[SupportingFindingView.from_domain(s) for s in chain.supporting],
            blocking=[BlockingFindingView.from_domain(b) for b in chain.blocking],
            dependency_steps=[ExplanationReferenceView.from_domain(r) for r in chain.dependency_steps],
            historical_reference=ExplanationReferenceView.from_domain(chain.historical_reference)
            if chain.historical_reference is not None
            else None,
        )


class DecisionExplanationView(CamelModel):
    case_id: str
    action: str
    conviction_strength: str
    chain: ExplanationChainView
    primary_supporting: SupportingFindingView | None
    primary_blocking: BlockingFindingView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, explanation: DecisionExplanation) -> "DecisionExplanationView":
        return cls(
            case_id=explanation.case_id,
            action=explanation.action.value,
            conviction_strength=explanation.conviction_strength.value,
            chain=ExplanationChainView.from_domain(explanation.chain),
            primary_supporting=SupportingFindingView.from_domain(explanation.primary_supporting)
            if explanation.primary_supporting is not None
            else None,
            primary_blocking=BlockingFindingView.from_domain(explanation.primary_blocking)
            if explanation.primary_blocking is not None
            else None,
            generated_at=explanation.generated_at,
        )


class DecisionExplanationSummaryView(CamelModel):
    case_id: str
    action: str
    primary_supporting: SupportingFindingView | None
    primary_blocking: BlockingFindingView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, summary: DecisionExplanationSummary) -> "DecisionExplanationSummaryView":
        return cls(
            case_id=summary.case_id,
            action=summary.action.value,
            primary_supporting=SupportingFindingView.from_domain(summary.primary_supporting)
            if summary.primary_supporting is not None
            else None,
            primary_blocking=BlockingFindingView.from_domain(summary.primary_blocking)
            if summary.primary_blocking is not None
            else None,
            generated_at=summary.generated_at,
        )


class DecisionExplanationChangeView(CamelModel):
    case_id: str
    new_supporting: list[SupportingFindingView]
    resolved_blocking: list[BlockingFindingView]
    new_blocking: list[BlockingFindingView]
    evidence_expanded: bool
    conviction_direction: str | None
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: DecisionExplanationChange) -> "DecisionExplanationChangeView":
        return cls(
            case_id=change.case_id,
            new_supporting=[SupportingFindingView.from_domain(s) for s in change.new_supporting],
            resolved_blocking=[BlockingFindingView.from_domain(b) for b in change.resolved_blocking],
            new_blocking=[BlockingFindingView.from_domain(b) for b in change.new_blocking],
            evidence_expanded=change.evidence_expanded,
            conviction_direction=change.conviction_direction.value if change.conviction_direction is not None else None,
            detected_at=change.detected_at,
        )


class DecisionExplanationComparisonView(CamelModel):
    a: DecisionExplanationView
    b: DecisionExplanationView
    shared_supporting: list[ExplanationReferenceView]
    differing_blocking_a: list[ExplanationReferenceView]
    differing_blocking_b: list[ExplanationReferenceView]
    shared_dependencies: list[ExplanationReferenceView]

    @classmethod
    def from_domain(cls, comparison: DecisionExplanationComparison) -> "DecisionExplanationComparisonView":
        return cls(
            a=DecisionExplanationView.from_domain(comparison.a),
            b=DecisionExplanationView.from_domain(comparison.b),
            shared_supporting=[ExplanationReferenceView.from_domain(r) for r in comparison.shared_supporting],
            differing_blocking_a=[ExplanationReferenceView.from_domain(r) for r in comparison.differing_blocking_a],
            differing_blocking_b=[ExplanationReferenceView.from_domain(r) for r in comparison.differing_blocking_b],
            shared_dependencies=[ExplanationReferenceView.from_domain(r) for r in comparison.shared_dependencies],
        )


class PortfolioDecisionExplanationBreakdownView(CamelModel):
    recently_changed: list[str]
    new_supporting_findings: list[str]
    resolved_blockers: list[str]
    recently_strengthened: list[str]

    @classmethod
    def from_domain(cls, breakdown: PortfolioDecisionExplanationBreakdown) -> "PortfolioDecisionExplanationBreakdownView":
        return cls(
            recently_changed=list(breakdown.recently_changed),
            new_supporting_findings=list(breakdown.new_supporting_findings),
            resolved_blockers=list(breakdown.resolved_blockers),
            recently_strengthened=list(breakdown.recently_strengthened),
        )

"""HTTP response schemas for Investment Decision Synthesis. Wire format
is camelCase via the shared Core `CamelModel` (ADR-004). Every field is
a direct read of an already-computed `InvestmentDecision`/comparison --
nothing is recomputed or reworded here."""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.investment_decision.models import (
    DecisionAction,
    DecisionChange,
    DecisionComparison,
    DecisionQualifier,
    DecisionReason,
    DecisionSummary,
    InvestmentDecision,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class DecisionReasonView(CamelModel):
    source: str
    code: str

    @classmethod
    def from_domain(cls, reason: DecisionReason) -> "DecisionReasonView":
        return cls(source=reason.source.value, code=reason.code)


class DecisionQualifierView(CamelModel):
    kind: str

    @classmethod
    def from_domain(cls, qualifier: DecisionQualifier) -> "DecisionQualifierView":
        return cls(kind=qualifier.kind.value)


class InvestmentDecisionView(CamelModel):
    case_id: str
    action: str
    qualifiers: list[DecisionQualifierView]
    supporting_reasons: list[DecisionReasonView]
    blockers: list[DecisionReasonView]
    change_trigger: DecisionReasonView | None
    generated_at: datetime

    #: The canonical analytical rationale, projected verbatim from the
    #: persisted payload. Deliberately passed through rather than
    #: re-modelled: every value is already a closed-vocabulary token in
    #: camelCase, and re-typing it here would create a second schema
    #: for one contract and invite the two to drift.
    #:
    #: Never translated and never turned into prose -- display text is
    #: derived at the presentation edge from these tokens, so wording
    #: can change without rewriting stored history.
    #:
    #: Three states, all distinct and all meaningful:
    #:   `None`            the row predates reasoning persistence
    #:                     (LEGACY_RESULT_WITHOUT_REASONING), or no
    #:                     directional recommendation existed;
    #:   present, empty    reasoning was computed and found nothing;
    #:   present, populated the canonical rationale.
    #:
    #: `change_trigger` above remains a readiness blocker kept for
    #: compatibility. It is NOT a fallback for this field, and nothing
    #: here reads it.
    reasoning: dict | None = None

    @classmethod
    def from_domain(cls, decision: InvestmentDecision) -> "InvestmentDecisionView":
        return cls(
            case_id=decision.case_id,
            action=decision.action.value,
            qualifiers=[DecisionQualifierView.from_domain(q) for q in decision.qualifiers],
            supporting_reasons=[DecisionReasonView.from_domain(r) for r in decision.supporting_reasons],
            blockers=[DecisionReasonView.from_domain(r) for r in decision.blockers],
            change_trigger=DecisionReasonView.from_domain(decision.change_trigger)
            if decision.change_trigger is not None
            else None,
            generated_at=decision.generated_at,
            # Projection only: the persisted payload is the source. This
            # layer never reconstructs rationale from process fields.
            reasoning=decision.reasoning_payload,
        )


class DecisionSummaryView(CamelModel):
    case_id: str
    action: str
    primary_qualifier: str | None
    primary_supporting_reason: DecisionReasonView | None
    primary_blocker: DecisionReasonView | None
    change_trigger: DecisionReasonView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, summary: DecisionSummary) -> "DecisionSummaryView":
        return cls(
            case_id=summary.case_id,
            action=summary.action.value,
            primary_qualifier=summary.primary_qualifier.value if summary.primary_qualifier is not None else None,
            primary_supporting_reason=DecisionReasonView.from_domain(summary.primary_supporting_reason)
            if summary.primary_supporting_reason is not None
            else None,
            primary_blocker=DecisionReasonView.from_domain(summary.primary_blocker)
            if summary.primary_blocker is not None
            else None,
            change_trigger=DecisionReasonView.from_domain(summary.change_trigger)
            if summary.change_trigger is not None
            else None,
            generated_at=summary.generated_at,
        )


class DecisionComparisonView(CamelModel):
    a: InvestmentDecisionView
    b: InvestmentDecisionView
    differing_qualifier_kinds: list[str]
    shared_blocker_codes: list[str]
    shared_supporting_reason_codes: list[str]

    @classmethod
    def from_domain(cls, comparison: DecisionComparison) -> "DecisionComparisonView":
        return cls(
            a=InvestmentDecisionView.from_domain(comparison.a),
            b=InvestmentDecisionView.from_domain(comparison.b),
            differing_qualifier_kinds=[k.value for k in comparison.differing_qualifier_kinds],
            shared_blocker_codes=list(comparison.shared_blocker_codes),
            shared_supporting_reason_codes=list(comparison.shared_supporting_reason_codes),
        )


class DecisionChangeView(CamelModel):
    case_id: str
    previous_action: str
    current_action: str
    previous_qualifier_kinds: list[str]
    current_qualifier_kinds: list[str]
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: DecisionChange) -> "DecisionChangeView":
        return cls(
            case_id=change.case_id,
            previous_action=change.previous_action.value,
            current_action=change.current_action.value,
            previous_qualifier_kinds=[k.value for k in change.previous_qualifier_kinds],
            current_qualifier_kinds=[k.value for k in change.current_qualifier_kinds],
            detected_at=change.detected_at,
        )


class PortfolioActionDistributionView(CamelModel):
    """Deliverable 7 -- ticker lists only, grouped by action; never a
    ranking within a group."""

    buy: list[str]
    add: list[str]
    hold: list[str]
    reduce: list[str]
    exit: list[str]
    wait: list[str]
    no_decision: list[str]

    @classmethod
    def from_domain(cls, buckets: dict[str, tuple[str, ...]]) -> "PortfolioActionDistributionView":
        return cls(
            buy=list(buckets.get(DecisionAction.BUY.value, ())),
            add=list(buckets.get(DecisionAction.ADD.value, ())),
            hold=list(buckets.get(DecisionAction.HOLD.value, ())),
            reduce=list(buckets.get(DecisionAction.REDUCE.value, ())),
            exit=list(buckets.get(DecisionAction.EXIT.value, ())),
            wait=list(buckets.get(DecisionAction.WAIT.value, ())),
            no_decision=list(buckets.get(DecisionAction.NO_DECISION.value, ())),
        )

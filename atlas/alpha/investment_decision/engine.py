"""The Decision Synthesis Engine itself (Deliverable 3), Decision
Qualification (Deliverable 4), and Decision Explanation (Deliverable
5). Every function here is pure and deterministic -- no AI, no
heuristics, no new investment analysis. Input is a small bundle of
already-computed real signals (`SynthesisInputs`); output is one
`InvestmentDecision`.

**Why `DecisionSupportLevel` is the synthesis engine's anchor, not
Stance.** Sprint 11's own audit already established `DecisionSupportLevel
.INSUFFICIENT_EVIDENCE` as "the single closest existing signal to 'is a
decision justified'" -- the mapping to `DecisionAction` below is a
direct, one-to-one re-expression of it (`ENTRY_SUPPORTED`->`BUY`,
`INCREASE_SUPPORTED`->`ADD`, `THESIS_INTACT`->`HOLD`,
`REDUCTION_SUPPORTED`->`REDUCE`, `EXIT_SUPPORTED`->`EXIT`,
`NO_ACTION_SUPPORTED`->`WAIT`, `INSUFFICIENT_EVIDENCE`->`NO_DECISION`).
Stance answers a different question ("what does Atlas currently
believe," a directional read -- see `atlas.alpha.decision_readiness
.models`'s own docstring for the full distinction) and is folded in
here only as *explanation* (a supporting reason) and as one specific
*qualifier* trigger (`AVOID_DECISION` -> `decision_blocked`), never as
a second, competing action signal -- computing the action from two
disagreeing sources would stop being deterministic reuse and start
being a new judgment.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionReadinessReason,
    DecisionReadinessStatus,
)
from atlas.alpha.decision_support import DecisionSupportLevel
from atlas.alpha.investment_decision.models import (
    DecisionAction,
    DecisionChange,
    DecisionComparison,
    DecisionQualifier,
    DecisionQualifierKind,
    DecisionReason,
    DecisionReasonSource,
    DecisionSummary,
    InvestmentDecision,
)
from atlas.alpha.stance.models import StanceLevel, StanceReasonCode

__all__ = [
    "SynthesisInputs",
    "synthesize_decision",
    "summarize_decision",
    "compare_decisions",
    "detect_decision_change",
    "ACTION_BY_DECISION_SUPPORT_LEVEL",
]


@dataclass(frozen=True)
class SynthesisInputs:
    """Every real, already-computed fact this engine reads -- nothing
    here is derived by this module."""

    decision_support_level: DecisionSupportLevel
    readiness_status: DecisionReadinessStatus
    readiness_blockers: tuple[DecisionBlocker, ...]
    readiness_supporting_reasons: tuple[DecisionReadinessReason, ...]
    stance_level: StanceLevel | None
    stance_top_reason_code: StanceReasonCode | None
    is_thesis_stale: bool


ACTION_BY_DECISION_SUPPORT_LEVEL: dict[DecisionSupportLevel, DecisionAction] = {
    DecisionSupportLevel.ENTRY_SUPPORTED: DecisionAction.BUY,
    DecisionSupportLevel.INCREASE_SUPPORTED: DecisionAction.ADD,
    DecisionSupportLevel.THESIS_INTACT: DecisionAction.HOLD,
    DecisionSupportLevel.REDUCTION_SUPPORTED: DecisionAction.REDUCE,
    DecisionSupportLevel.EXIT_SUPPORTED: DecisionAction.EXIT,
    DecisionSupportLevel.NO_ACTION_SUPPORTED: DecisionAction.WAIT,
    DecisionSupportLevel.INSUFFICIENT_EVIDENCE: DecisionAction.NO_DECISION,
}

_EVIDENCE_LIMITING_BLOCKER_KINDS = frozenset(
    {"missing_observation", "missing_thesis_evidence", "coverage_incomplete", "unknown_valuation"}
)
"""Deliverable 4 -- the real `DecisionBlockerKind` values (see
`atlas.alpha.decision_readiness.models`) that mean "the action above is
real, but Atlas's own underlying evidence for it is thin," Atlas
Decision Layer Sprint 1's own `evidence_limited` qualifier trigger."""


def _detect_qualifiers(inputs: SynthesisInputs) -> tuple[DecisionQualifier, ...]:
    """Deliverable 4 -- exhaustive, fixed declared order, each member
    triggered by one already-real fact; never invented."""
    qualifiers: list[DecisionQualifierKind] = []

    if inputs.readiness_status is DecisionReadinessStatus.BLOCKED or inputs.stance_level is StanceLevel.AVOID_DECISION:
        qualifiers.append(DecisionQualifierKind.DECISION_BLOCKED)
    if inputs.readiness_status is DecisionReadinessStatus.UNAVAILABLE:
        qualifiers.append(DecisionQualifierKind.OPERATIONALLY_DELAYED)
    if any(b.kind.value in _EVIDENCE_LIMITING_BLOCKER_KINDS for b in inputs.readiness_blockers):
        qualifiers.append(DecisionQualifierKind.EVIDENCE_LIMITED)
    if inputs.is_thesis_stale:
        qualifiers.append(DecisionQualifierKind.TEMPORARY_DECISION)
    if inputs.readiness_status is DecisionReadinessStatus.ALMOST_READY or inputs.stance_level is StanceLevel.REVIEW:
        qualifiers.append(DecisionQualifierKind.CAREFUL_DECISION)
    if (
        inputs.readiness_status is DecisionReadinessStatus.READY
        and inputs.decision_support_level is not DecisionSupportLevel.INSUFFICIENT_EVIDENCE
        and not qualifiers
    ):
        qualifiers.append(DecisionQualifierKind.STRONG_DECISION)

    return tuple(DecisionQualifier(kind) for kind in qualifiers)


def synthesize_decision(case_id: str, inputs: SynthesisInputs, *, generated_at: datetime) -> InvestmentDecision:
    """Deliverable 3 -- one action, read directly off
    `ACTION_BY_DECISION_SUPPORT_LEVEL`; never combines signals into a
    score, never overrides the action from a second source (see this
    module's own docstring for why)."""
    action = ACTION_BY_DECISION_SUPPORT_LEVEL[inputs.decision_support_level]
    qualifiers = _detect_qualifiers(inputs)

    blockers = tuple(
        DecisionReason(DecisionReasonSource.READINESS_BLOCKER, blocker.kind.value) for blocker in inputs.readiness_blockers
    )
    supporting_reasons = tuple(
        DecisionReason(DecisionReasonSource.READINESS_SUPPORT, reason.kind.value)
        for reason in inputs.readiness_supporting_reasons
    )
    if inputs.stance_top_reason_code is not None:
        supporting_reasons = (
            DecisionReason(DecisionReasonSource.STANCE, inputs.stance_top_reason_code.value),
        ) + supporting_reasons

    change_trigger = blockers[0] if blockers else None

    return InvestmentDecision(
        case_id=case_id,
        action=action,
        qualifiers=qualifiers,
        supporting_reasons=supporting_reasons,
        blockers=blockers,
        change_trigger=change_trigger,
        generated_at=generated_at,
    )


def summarize_decision(decision: InvestmentDecision) -> DecisionSummary:
    """Deliverable 6/7 -- `primary_*` is simply the first entry of each
    already-fixed-order tuple/list; no separately invented ranking."""
    return DecisionSummary(
        case_id=decision.case_id,
        action=decision.action,
        primary_qualifier=decision.qualifiers[0].kind if decision.qualifiers else None,
        primary_supporting_reason=decision.supporting_reasons[0] if decision.supporting_reasons else None,
        primary_blocker=decision.blockers[0] if decision.blockers else None,
        change_trigger=decision.change_trigger,
        generated_at=decision.generated_at,
    )


def compare_decisions(a: InvestmentDecision, b: InvestmentDecision) -> DecisionComparison:
    """Deliverable 9 -- "never choose a winner": no ranking, only real
    differences and real overlaps."""
    kinds_a = {q.kind for q in a.qualifiers}
    kinds_b = {q.kind for q in b.qualifiers}
    differing = tuple(sorted((kinds_a ^ kinds_b), key=lambda k: k.value))

    blocker_codes_a = {r.code for r in a.blockers}
    blocker_codes_b = {r.code for r in b.blockers}
    shared_blockers = tuple(sorted(blocker_codes_a & blocker_codes_b))

    reason_codes_a = {r.code for r in a.supporting_reasons}
    reason_codes_b = {r.code for r in b.supporting_reasons}
    shared_reasons = tuple(sorted(reason_codes_a & reason_codes_b))

    return DecisionComparison(
        a=a,
        b=b,
        differing_qualifier_kinds=differing,
        shared_blocker_codes=shared_blockers,
        shared_supporting_reason_codes=shared_reasons,
    )


def detect_decision_change(
    previous: InvestmentDecision | None, current: InvestmentDecision, *, detected_at: datetime
) -> DecisionChange | None:
    """Deliverable 10/11 -- `None` whenever nothing real changed
    (`previous is None`, or an identical action *and* an identical
    qualifier set): never a manufactured "change" from a Case simply
    being read twice, the same discipline `atlas.alpha.decision_readiness
    .engine.detect_readiness_change` already establishes."""
    if previous is None:
        return None
    previous_kinds = tuple(sorted((q.kind for q in previous.qualifiers), key=lambda k: k.value))
    current_kinds = tuple(sorted((q.kind for q in current.qualifiers), key=lambda k: k.value))
    if previous.action == current.action and previous_kinds == current_kinds:
        return None
    return DecisionChange(
        case_id=current.case_id,
        previous_action=previous.action,
        current_action=current.action,
        previous_qualifier_kinds=previous_kinds,
        current_qualifier_kinds=current_kinds,
        detected_at=detected_at,
    )

"""Decision Reliability engine (Atlas Decision Layer Sprint 7). Pure,
deterministic functions only -- no I/O, matching every sibling
Decision Layer engine in this program.

**Computes nothing new.** Every function below reclassifies three
already-real, already-computed judgments -- `CoverageAssessment
.overall_confidence` (Atlas Intelligence Sprint 1), `EvidenceQualityReport
.quality`/`.warnings` (Atlas Intelligence Sprint 4), and `DecisionReadiness
.status`/`.blockers`/`.supporting_reasons` (Atlas Intelligence Sprint
11, itself already incorporating Monitoring's own operational facts)
-- into one closed `ReliabilityLevel`. See this package's own
`__init__.py` for the full audit these functions are built from.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.coverage.models import ConfidenceLevel, ConfidenceReasonCode, CoverageAssessment
from atlas.alpha.decision_readiness.models import DecisionReadiness, DecisionReadinessStatus
from atlas.alpha.decision_explanation.models import ChangeDirection, ExplanationReferenceKind
from atlas.alpha.evidence_quality.models import EvidenceQualityLevel, EvidenceQualityReport

from .models import (
    DecisionReliability,
    DecisionReliabilitySummary,
    PortfolioReliabilityBreakdown,
    ReliabilityChange,
    ReliabilityComparison,
    ReliabilityLevel,
    ReliabilityReason,
    ReliabilityReference,
    ReliabilitySource,
)

__all__ = [
    "classify_reliability",
    "build_decision_reliability",
    "summarize_decision_reliability",
    "compare_decision_reliability",
    "detect_reliability_change",
    "build_portfolio_reliability_breakdown",
]

#: Deliverable 4 -- worst-to-best, used both for classification's own
#: cascade and for `ReliabilityComparison`/`ReliabilityChange`'s "more
#: reliable"/"direction" reading. Declared once, locally, the same
#: "each package owns its own rank table" discipline Sprint 5/6 already
#: established (`decision_memory`/`decision_explanation`'s own private
#: `_STRENGTH_RANK`).
_LEVEL_RANK: dict[ReliabilityLevel, int] = {
    ReliabilityLevel.UNKNOWN: 0,
    ReliabilityLevel.UNAVAILABLE: 1,
    ReliabilityLevel.LIMITED: 2,
    ReliabilityLevel.MODERATE: 3,
    ReliabilityLevel.HIGH: 4,
}

_LIMITING_CONFIDENCE_CODES = frozenset(
    {
        ConfidenceReasonCode.NO_COMPANY_DATA,
        ConfidenceReasonCode.DIMENSIONS_UNAVAILABLE,
        ConfidenceReasonCode.DIMENSIONS_PARTIAL,
        ConfidenceReasonCode.CONTRADICTING_EVIDENCE_PRESENT,
        ConfidenceReasonCode.THESIS_STALE,
    }
)
_LIMITING_EVIDENCE_QUALITY_LEVELS = frozenset(
    {
        EvidenceQualityLevel.CONFLICTING,
        EvidenceQualityLevel.UNSUPPORTED,
        EvidenceQualityLevel.INCOMPLETE,
        EvidenceQualityLevel.SUPERSEDED,
    }
)
_AGED_EVIDENCE_QUALITY_LEVELS = frozenset({EvidenceQualityLevel.OLD, EvidenceQualityLevel.STALE})
_FRESH_EVIDENCE_QUALITY_LEVELS = frozenset({EvidenceQualityLevel.FRESH, EvidenceQualityLevel.RECENT})
_WAITING_READINESS_STATUSES = frozenset({DecisionReadinessStatus.WAITING, DecisionReadinessStatus.ALMOST_READY})


def classify_reliability(
    readiness_status: DecisionReadinessStatus,
    confidence_level: ConfidenceLevel,
    evidence_quality_level: EvidenceQualityLevel,
) -> ReliabilityLevel:
    """Deliverable 4 -- a fixed priority cascade, never a score. Each
    step below is a real, disclosed rule; the first one that matches
    decides the level, the same "declared order, never invented"
    discipline `DecisionReadinessStatus`'s own `derive_decision_readiness`
    already established one layer down."""
    if readiness_status is DecisionReadinessStatus.UNKNOWN:
        return ReliabilityLevel.UNKNOWN
    if readiness_status is DecisionReadinessStatus.UNAVAILABLE:
        return ReliabilityLevel.UNAVAILABLE
    if readiness_status is DecisionReadinessStatus.BLOCKED:
        return ReliabilityLevel.LIMITED
    if confidence_level in (ConfidenceLevel.VERY_LIMITED, ConfidenceLevel.LIMITED):
        return ReliabilityLevel.LIMITED
    if evidence_quality_level in _LIMITING_EVIDENCE_QUALITY_LEVELS:
        return ReliabilityLevel.LIMITED
    if confidence_level is ConfidenceLevel.MODERATE:
        return ReliabilityLevel.MODERATE
    if evidence_quality_level in _AGED_EVIDENCE_QUALITY_LEVELS:
        return ReliabilityLevel.MODERATE
    if readiness_status in _WAITING_READINESS_STATUSES:
        return ReliabilityLevel.MODERATE
    return ReliabilityLevel.HIGH


def build_decision_reliability(
    case_id: str,
    *,
    coverage: CoverageAssessment,
    evidence_quality: EvidenceQualityReport,
    readiness: DecisionReadiness,
    generated_at: datetime,
) -> DecisionReliability:
    """Deliverable 3 -- one deterministic builder, three already-
    computed inputs, nothing recomputed."""
    level = classify_reliability(readiness.status, coverage.overall_confidence, evidence_quality.quality)

    supporting: list[ReliabilityReason] = []
    limiting: list[ReliabilityReason] = []

    for reason in coverage.reasoning:
        ref = ReliabilityReference(kind=ExplanationReferenceKind.REASON_CODE, id=reason.code.value)
        target = limiting if reason.code in _LIMITING_CONFIDENCE_CODES else supporting
        target.append(ReliabilityReason(ReliabilitySource.CONFIDENCE, ref, count=reason.count, total=reason.total))

    if evidence_quality.quality in _FRESH_EVIDENCE_QUALITY_LEVELS:
        supporting.append(
            ReliabilityReason(
                ReliabilitySource.EVIDENCE_QUALITY,
                ReliabilityReference(kind=ExplanationReferenceKind.REASON_CODE, id=evidence_quality.quality.value),
            )
        )
    for warning in evidence_quality.warnings:
        limiting.append(
            ReliabilityReason(
                ReliabilitySource.EVIDENCE_QUALITY,
                ReliabilityReference(kind=ExplanationReferenceKind.REASON_CODE, id=warning.value),
            )
        )

    for support in readiness.supporting_reasons:
        supporting.append(
            ReliabilityReason(
                ReliabilitySource.READINESS_SUPPORT,
                ReliabilityReference(kind=ExplanationReferenceKind.REASON_CODE, id=support.kind.value),
            )
        )
    for blocker in readiness.blockers:
        limiting.append(
            ReliabilityReason(
                ReliabilitySource.READINESS_BLOCKER,
                ReliabilityReference(kind=ExplanationReferenceKind.REASON_CODE, id=blocker.kind.value),
            )
        )

    return DecisionReliability(
        case_id=case_id,
        level=level,
        supporting_reasons=tuple(supporting),
        limiting_reasons=tuple(limiting),
        primary_limiting_reason=limiting[0] if limiting else None,
        generated_at=generated_at,
    )


def summarize_decision_reliability(reliability: DecisionReliability) -> DecisionReliabilitySummary:
    return DecisionReliabilitySummary(
        case_id=reliability.case_id,
        level=reliability.level,
        primary_limiting_reason=reliability.primary_limiting_reason,
        generated_at=reliability.generated_at,
    )


def compare_decision_reliability(a: DecisionReliability, b: DecisionReliability) -> ReliabilityComparison:
    """Deliverable 10 -- more reliable side (by the same fixed level
    rank, `None` on a genuine tie), shared/differing limitations,
    shared strengths. Never a "better investment" verdict."""
    more_reliable_case_id: str | None
    if _LEVEL_RANK[a.level] == _LEVEL_RANK[b.level]:
        more_reliable_case_id = None
    elif _LEVEL_RANK[a.level] > _LEVEL_RANK[b.level]:
        more_reliable_case_id = a.case_id
    else:
        more_reliable_case_id = b.case_id

    a_limiting_by_id = {r.reference.id: r.reference for r in a.limiting_reasons}
    b_limiting_by_id = {r.reference.id: r.reference for r in b.limiting_reasons}
    shared_limiting = tuple(a_limiting_by_id[i] for i in sorted(set(a_limiting_by_id) & set(b_limiting_by_id)))
    differing_a = tuple(a_limiting_by_id[i] for i in sorted(set(a_limiting_by_id) - set(b_limiting_by_id)))
    differing_b = tuple(b_limiting_by_id[i] for i in sorted(set(b_limiting_by_id) - set(a_limiting_by_id)))

    a_supporting_by_id = {r.reference.id: r.reference for r in a.supporting_reasons}
    b_supporting_by_id = {r.reference.id: r.reference for r in b.supporting_reasons}
    shared_supporting = tuple(a_supporting_by_id[i] for i in sorted(set(a_supporting_by_id) & set(b_supporting_by_id)))

    return ReliabilityComparison(
        a=a,
        b=b,
        more_reliable_case_id=more_reliable_case_id,
        shared_limiting=shared_limiting,
        differing_limiting_a=differing_a,
        differing_limiting_b=differing_b,
        shared_supporting=shared_supporting,
    )


def detect_reliability_change(
    previous: DecisionReliability | None, current: DecisionReliability, *, detected_at: datetime
) -> ReliabilityChange | None:
    """"No event, no timestamp" -- `None` on the first-ever computation
    or when nothing about the reliability actually moved."""
    if previous is None:
        return None

    previous_limiting = {r.reference.id: r for r in previous.limiting_reasons}
    current_limiting = {r.reference.id: r for r in current.limiting_reasons}
    new_limiting = tuple(current_limiting[i] for i in current_limiting if i not in previous_limiting)
    resolved_limiting = tuple(previous_limiting[i] for i in previous_limiting if i not in current_limiting)

    direction: ChangeDirection | None = None
    if previous.level != current.level:
        direction = (
            ChangeDirection.STRONGER
            if _LEVEL_RANK[current.level] > _LEVEL_RANK[previous.level]
            else ChangeDirection.WEAKER
        )

    if not new_limiting and not resolved_limiting and direction is None:
        return None

    return ReliabilityChange(
        case_id=current.case_id,
        previous_level=previous.level,
        current_level=current.level,
        direction=direction,
        new_limiting=new_limiting,
        resolved_limiting=resolved_limiting,
        detected_at=detected_at,
    )


def build_portfolio_reliability_breakdown(
    items: tuple[tuple[str, DecisionReliability], ...],
    changes: tuple[tuple[str, ReliabilityChange | None], ...],
) -> PortfolioReliabilityBreakdown:
    """Deliverable 8 -- ticker groupings only, in the caller's own
    existing order; never re-ranked. `most_reliable`/`least_reliable`
    are threshold buckets over the current level (mirrors
    `PortfolioConvictionBreakdown.highest_conviction`/`.lowest_conviction`'s
    own membership-not-sort discipline), never a sorted top-N."""
    most_reliable = tuple(ticker for ticker, r in items if r.level is ReliabilityLevel.HIGH)
    least_reliable = tuple(
        ticker
        for ticker, r in items
        if r.level in (ReliabilityLevel.LIMITED, ReliabilityLevel.UNAVAILABLE, ReliabilityLevel.UNKNOWN)
    )
    recently_improved = tuple(
        ticker for ticker, change in changes if change is not None and change.direction is ChangeDirection.STRONGER
    )
    recently_weakened = tuple(
        ticker for ticker, change in changes if change is not None and change.direction is ChangeDirection.WEAKER
    )
    return PortfolioReliabilityBreakdown(
        most_reliable=most_reliable,
        least_reliable=least_reliable,
        recently_improved=recently_improved,
        recently_weakened=recently_weakened,
    )

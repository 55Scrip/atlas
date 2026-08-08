"""Deterministic Attention rules (ATLAS-028 Phase 19/20) -- confirmed
design: combine position size with real analytical signals, first-match
-wins, no hidden weighting.

**Rule table, documented before it was implemented:**

`large` = `weight_percent >= ELEVATED_CONCENTRATION_WEIGHT_PERCENT`
(25.0) -- the exact threshold `atlas.alpha.portfolio_intelligence
.thresholds` already uses for concentration, reused verbatim, not a new
number invented for Attention specifically. Size never changes a
signal's own analytical severity; it only changes how urgently a real
signal deserves review, because more capital is exposed.

Five real signals (`AttentionReasonKind`), each read from an
already-computed canonical value, never re-derived:

1. `HIGH_FINANCIAL_RISK` -- `risk_analysis`'s `FINANCIAL_RISK` is `HIGH`.
2. `HIGH_VALUATION_RISK` -- `risk_analysis`'s `VALUATION_RISK` is `HIGH`.
3. `LOW_CONVICTION` -- `conviction.level` is `ConvictionLevel.LOW`.
4. `CONTRADICTING_EVIDENCE` -- `risk_analysis`'s `THESIS_RISK` is `HIGH`.
5. `INSUFFICIENT_EVIDENCE` -- case-wide `confidence` is `NOT_APPLICABLE`
   or `NONE`.

`reasons` always names every signal that fired, not only the one
deciding `priority` (mirrors `ConvictionAssessment.reasons`'s own
"always name every applicable code" discipline). `priority`, in this
fixed order, first match wins:

1. `large` AND any of {1, 2, 3, 4} fired -> `PRIORITY_REVIEW`.
2. `large` AND only {5} fired (no priority-tier signal) -> `EVIDENCE_REVIEW`.
3. Any of {1, 2, 3, 4, 5} fired, regardless of size -> `STANDARD_REVIEW`.
4. No signal fired -> `NONE`.

Never a numeric score, never an additive weighting between reasons --
`priority` is a categorical classification of the *combination*, exactly
the same first-match-wins style `conviction.calculate_conviction`
already established.
"""
from __future__ import annotations

from atlas.alpha.portfolio_cockpit.contracts import AttentionReasonKind, ReviewPriority
from atlas.alpha.portfolio_cockpit.models import HoldingAttention
from atlas.alpha.portfolio_intelligence.thresholds import ELEVATED_CONCENTRATION_WEIGHT_PERCENT
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["determine_attention"]

_INSUFFICIENT_EVIDENCE_COVERAGE = (EvidenceCoverageLevel.NOT_APPLICABLE, EvidenceCoverageLevel.NONE)

_PRIORITY_TIER_REASONS = (
    AttentionReasonKind.HIGH_FINANCIAL_RISK,
    AttentionReasonKind.HIGH_VALUATION_RISK,
    AttentionReasonKind.LOW_CONVICTION,
    AttentionReasonKind.CONTRADICTING_EVIDENCE,
)


def determine_attention(
    *,
    weight_percent: float,
    conviction: ConvictionAssessment,
    confidence: EvidenceCoverageLevel,
    risk_findings: tuple[RiskFinding, ...],
) -> HoldingAttention:
    findings_by_category = {f.category: f for f in risk_findings}
    reasons: list[AttentionReasonKind] = []

    if findings_by_category[RiskCategory.FINANCIAL_RISK].status is RiskStatus.HIGH:
        reasons.append(AttentionReasonKind.HIGH_FINANCIAL_RISK)
    if findings_by_category[RiskCategory.VALUATION_RISK].status is RiskStatus.HIGH:
        reasons.append(AttentionReasonKind.HIGH_VALUATION_RISK)
    if conviction.level is ConvictionLevel.LOW:
        reasons.append(AttentionReasonKind.LOW_CONVICTION)
    if findings_by_category[RiskCategory.THESIS_RISK].status is RiskStatus.HIGH:
        reasons.append(AttentionReasonKind.CONTRADICTING_EVIDENCE)
    if confidence in _INSUFFICIENT_EVIDENCE_COVERAGE:
        reasons.append(AttentionReasonKind.INSUFFICIENT_EVIDENCE)

    large = weight_percent >= ELEVATED_CONCENTRATION_WEIGHT_PERCENT
    has_priority_signal = any(reason in _PRIORITY_TIER_REASONS for reason in reasons)

    if large and has_priority_signal:
        priority = ReviewPriority.PRIORITY_REVIEW
    elif large and reasons:
        priority = ReviewPriority.EVIDENCE_REVIEW
    elif reasons:
        priority = ReviewPriority.STANDARD_REVIEW
    else:
        priority = ReviewPriority.NONE

    return HoldingAttention(priority=priority, reasons=tuple(reasons))

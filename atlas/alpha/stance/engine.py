"""Stance Engine (Atlas Intelligence Sprint 2 -- Recommendation Quality
& Actionability).

Answers the one question this Sprint exists for: "what should the
investor do now?" -- **never** as a trade-sizing instruction (no BUY/
SELL, no share counts; that remains Decision Support's own, narrower,
already-real question). This engine answers a different, broader one:
"how favorable is Atlas's current view of this Case, and how confident
should the investor be in that view?" `StanceLevel.INCREASE`/`REDUCE`
describe the *direction* of that view (strengthening/weakening), never
a position-size recommendation -- see `models.py`'s own docstring.

This module computes **nothing** new. It reads already-computed
`CanonicalAnalysis.conviction`/`.recommendation`/`.risk_analysis`, an
already-computed `CoverageAssessment` (Atlas Intelligence Sprint 1), an
already-computed `ChangeIntelligence` (Investment Case Monitoring),
and an already-computed `PortfolioFitAssessment` (Portfolio Fit Engine)
-- and classifies, via an ordered decision table over real facts, the
same "deterministic classification, never an invented score" style
`atlas.analysis_engine.conviction.calculate_conviction` and
`atlas.alpha.coverage.engine.assess_coverage` already established.

**Deliverable 4's own gating doctrine, implemented literally**: the
engine becomes *less* decisive as Atlas's own coverage/confidence
drops, never the opposite. The gate runs before any directional signal
is even read -- a "Strong Investment Case + Weak Coverage" input can
therefore never reach `INCREASE`, because the function returns from the
confidence gate before the directional branch runs at all.

**Why this reads `coverage.reasoning`, never `coverage.overall_coverage`,
anywhere in this module.** An audit for this Sprint found
`AnalysisCoverageLevel` (`atlas.analysis_engine.analysis_coverage`) can
read `NO_COVERAGE` even when real, conclusive per-dimension findings
exist -- `atlas.analysis_engine.business_data.completeness
.assess_data_completeness` only recognizes the literal
`FINANCIAL_STATEMENT` source kind, not `ANNUAL_REPORT`/
`QUARTERLY_REPORT` (a real, pre-existing Core gap, left unmodified per
this Sprint's own "no Core redesign" instruction and documented in the
Final Report). `coverage.overall_confidence` (Sprint 1's own, finer-
grained, per-dimension-derived signal) does not share that gap, so
every gate below reads it instead -- both the absolute floor (`coverage
.reasoning` naming `ConfidenceReasonCode.NO_COMPANY_DATA`) and the
finer confidence tiers.
"""
from __future__ import annotations

from enum import Enum, auto

from atlas.alpha.coverage import ConfidenceLevel, ConfidenceReasonCode, CoverageAssessment, has_contradiction
from atlas.alpha.decision_support import DecisionSupportLevel, describe_recommendation
from atlas.alpha.portfolio_fit.models import FitRating, PortfolioFitAssessment
from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.investment_case_change import ChangeIntelligence, ThesisImpact
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.projection import risk_projection

from .models import (
    Stance,
    StanceComparison,
    StanceComparisonReason,
    StanceComparisonReasonCode,
    StanceLevel,
    StanceReason,
    StanceReasonCode,
)

__all__ = ["determine_stance", "compare_stance"]


class _Direction(Enum):
    STRENGTHENED = auto()
    WEAKENED = auto()
    MIXED = auto()
    UNCHANGED = auto()


def _direction_signal(
    analysis: CanonicalAnalysis, change_intelligence: ChangeIntelligence | None
) -> tuple[StanceReason, _Direction]:
    """The one real "has Atlas's view moved" signal, preferring Change
    Intelligence's own real snapshot-to-snapshot delta when one exists.
    Falls back to Decision Support's real, single-snapshot level only
    for a baseline Case (no prior snapshot exists to compare against) --
    a present-tense reading ("current evidence favors this"), never
    mislabeled as a comparative "strengthened.\""""
    if change_intelligence is not None and not change_intelligence.is_baseline:
        impact = change_intelligence.thesis_impact
        if impact is ThesisImpact.STRENGTHENED:
            return StanceReason(StanceReasonCode.THESIS_STRENGTHENED), _Direction.STRENGTHENED
        if impact is ThesisImpact.WEAKENED:
            return StanceReason(StanceReasonCode.THESIS_WEAKENED), _Direction.WEAKENED
        if impact is ThesisImpact.MIXED:
            return StanceReason(StanceReasonCode.THESIS_MIXED), _Direction.MIXED
        return StanceReason(StanceReasonCode.THESIS_UNCHANGED), _Direction.UNCHANGED

    level = describe_recommendation(analysis.recommendation).level
    if level in (DecisionSupportLevel.ENTRY_SUPPORTED, DecisionSupportLevel.INCREASE_SUPPORTED):
        return StanceReason(StanceReasonCode.DECISION_SUPPORT_FAVORABLE), _Direction.STRENGTHENED
    if level in (DecisionSupportLevel.REDUCTION_SUPPORTED, DecisionSupportLevel.EXIT_SUPPORTED):
        return StanceReason(StanceReasonCode.DECISION_SUPPORT_UNFAVORABLE), _Direction.WEAKENED
    return StanceReason(StanceReasonCode.DECISION_SUPPORT_NEUTRAL), _Direction.UNCHANGED


def determine_stance(
    analysis: CanonicalAnalysis,
    *,
    coverage: CoverageAssessment,
    change_intelligence: ChangeIntelligence | None,
    portfolio_fit: PortfolioFitAssessment | None,
) -> Stance:
    """Deterministic: identical inputs always produce an identical
    `Stance`. Reads `analysis.conviction`/`.recommendation`/
    `.risk_analysis`, `coverage`, `change_intelligence`, and
    `portfolio_fit` -- nothing else, and never mutates or re-evaluates
    any of them."""

    # 1. Absolute floor: no company data at all. Deliberately keyed off
    # `coverage.reasoning` (Atlas Intelligence Sprint 1's own per-
    # dimension-derived `ConfidenceReasonCode.NO_COMPANY_DATA`), never
    # `coverage.overall_coverage` -- an audit for this Sprint found
    # `AnalysisCoverageLevel` can read `NO_COVERAGE` even when real,
    # conclusive per-dimension findings exist, because
    # `atlas.analysis_engine.business_data.completeness
    # .assess_data_completeness` only recognizes the literal
    # `FINANCIAL_STATEMENT` source kind, not `ANNUAL_REPORT`/
    # `QUARTERLY_REPORT` (a real, pre-existing Core gap, left
    # unmodified per this Sprint's own "no Core redesign" instruction
    # and documented in the final report). `coverage.reasoning`'s own
    # `NO_COMPANY_DATA` code is reliable here because it is derived
    # from the same per-dimension `.status` reads this whole engine
    # already trusts everywhere else.
    if any(r.code is ConfidenceReasonCode.NO_COMPANY_DATA for r in coverage.reasoning):
        reason = StanceReason(StanceReasonCode.NO_COMPANY_DATA)
        return Stance(
            level=StanceLevel.NO_RECOMMENDATION,
            reasoning=(reason,),
            supporting_signals=(),
            limiting_signals=(reason,),
            confidence=coverage.overall_confidence,
            missing_information=coverage.missing_dimensions,
        )

    # 2. Real red flags: contradiction or conviction itself unreachable.
    contradiction = has_contradiction(analysis)
    conviction_insufficient = analysis.conviction.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
    if contradiction or conviction_insufficient:
        reasons = tuple(
            StanceReason(code)
            for code, present in (
                (StanceReasonCode.CONTRADICTING_EVIDENCE_PRESENT, contradiction),
                (StanceReasonCode.CONVICTION_INSUFFICIENT, conviction_insufficient),
            )
            if present
        )
        return Stance(
            level=StanceLevel.AVOID_DECISION,
            reasoning=reasons,
            supporting_signals=(),
            limiting_signals=reasons,
            confidence=coverage.overall_confidence,
            missing_information=coverage.missing_dimensions,
        )

    # 3. Confidence gate -- Deliverable 4's own doctrine: never more
    # decisive than Atlas's actual confidence supports.
    if coverage.overall_confidence in (ConfidenceLevel.VERY_LIMITED, ConfidenceLevel.LIMITED):
        code = (
            StanceReasonCode.CONFIDENCE_VERY_LIMITED
            if coverage.overall_confidence is ConfidenceLevel.VERY_LIMITED
            else StanceReasonCode.CONFIDENCE_LIMITED
        )
        reason = StanceReason(code)
        return Stance(
            level=StanceLevel.WAIT,
            reasoning=(reason,),
            supporting_signals=(),
            limiting_signals=(reason,),
            confidence=coverage.overall_confidence,
            missing_information=coverage.missing_dimensions,
        )

    if coverage.overall_confidence is ConfidenceLevel.MODERATE:
        reason = StanceReason(StanceReasonCode.CONFIDENCE_MODERATE)
        return Stance(
            level=StanceLevel.REVIEW,
            reasoning=(reason,),
            supporting_signals=(),
            limiting_signals=(reason,),
            confidence=coverage.overall_confidence,
            missing_information=coverage.missing_dimensions,
        )

    # 4. High confidence: a real direction may now be stated.
    direction_reason, direction = _direction_signal(analysis, change_intelligence)

    fit_weak = portfolio_fit is not None and portfolio_fit.overall in (FitRating.WEAK, FitRating.POOR)
    fit_favorable = portfolio_fit is not None and portfolio_fit.overall in (FitRating.EXCELLENT, FitRating.GOOD)
    high_risk = risk_projection(analysis.risk_analysis).status is RiskStatus.HIGH

    supporting: list[StanceReason] = []
    limiting: list[StanceReason] = []
    if fit_weak:
        limiting.append(StanceReason(StanceReasonCode.PORTFOLIO_FIT_WEAK))
    elif fit_favorable:
        supporting.append(StanceReason(StanceReasonCode.PORTFOLIO_FIT_FAVORABLE))
    if high_risk:
        limiting.append(StanceReason(StanceReasonCode.HIGH_RISK_PRESENT))
    else:
        supporting.append(StanceReason(StanceReasonCode.NO_HIGH_RISK))

    if direction is _Direction.MIXED:
        level = StanceLevel.REVIEW
    elif direction is _Direction.STRENGTHENED:
        supporting.append(direction_reason)
        # Deliverable 7's own worked example: an otherwise-favorable
        # direction alongside a weak Portfolio Fit or high risk must
        # downgrade to Review, never state a confident Increase over a
        # real, disclosed tension.
        level = StanceLevel.REVIEW if (fit_weak or high_risk) else StanceLevel.INCREASE
    elif direction is _Direction.WEAKENED:
        limiting.append(direction_reason)
        level = StanceLevel.REDUCE
    else:
        level = StanceLevel.MAINTAIN

    # `direction_reason` is already included once, in whichever of
    # `supporting`/`limiting` it was appended to above (STRENGTHENED/
    # WEAKENED); for MIXED/UNCHANGED it was never appended to either
    # (neither favorable nor limiting on its own), so it is named here
    # instead -- `reasoning` always names every applicable fact exactly
    # once, the same discipline `ConvictionAssessment.reasons` already
    # established.
    if direction in (_Direction.MIXED, _Direction.UNCHANGED):
        reasoning = (direction_reason, *supporting, *limiting)
    else:
        reasoning = (*supporting, *limiting)

    return Stance(
        level=level,
        reasoning=reasoning,
        supporting_signals=tuple(supporting),
        limiting_signals=tuple(limiting),
        confidence=coverage.overall_confidence,
        missing_information=coverage.missing_dimensions,
    )


#: Best-to-worst order for the four levels a real, confident preference
#: can be drawn from. `WAIT`/`AVOID_DECISION`/`NO_RECOMMENDATION` are
#: deliberately absent -- Deliverable 9's own instruction ("when Atlas
#: cannot honestly choose, say so") means those three must never be
#: ranked against anything, including each other.
_PREFERENCE_RANK = {
    StanceLevel.INCREASE: 0,
    StanceLevel.MAINTAIN: 1,
    StanceLevel.REVIEW: 2,
    StanceLevel.REDUCE: 3,
}


def compare_stance(ticker_a: str, stance_a: Stance, ticker_b: str, stance_b: Stance) -> StanceComparison:
    """Deliverable 9 (Compare Integration). Reads the two already-
    computed `Stance`s verbatim -- never recomputes either, the same
    "compute nothing new" discipline `atlas.alpha.portfolio_fit.engine
    .compare_fit` already established."""
    if stance_a.level not in _PREFERENCE_RANK or stance_b.level not in _PREFERENCE_RANK:
        return StanceComparison(
            ticker_a=ticker_a,
            stance_a=stance_a,
            ticker_b=ticker_b,
            stance_b=stance_b,
            preferred_ticker=None,
            reasoning=(StanceComparisonReason(StanceComparisonReasonCode.ONE_OR_BOTH_TOO_UNCERTAIN_TO_COMPARE),),
        )
    if stance_a.level is stance_b.level:
        return StanceComparison(
            ticker_a=ticker_a,
            stance_a=stance_a,
            ticker_b=ticker_b,
            stance_b=stance_b,
            preferred_ticker=None,
            reasoning=(StanceComparisonReason(StanceComparisonReasonCode.BOTH_STANCES_TIED),),
        )
    preferred = ticker_a if _PREFERENCE_RANK[stance_a.level] < _PREFERENCE_RANK[stance_b.level] else ticker_b
    return StanceComparison(
        ticker_a=ticker_a,
        stance_a=stance_a,
        ticker_b=ticker_b,
        stance_b=stance_b,
        preferred_ticker=preferred,
        reasoning=(StanceComparisonReason(StanceComparisonReasonCode.PREFERRED_HAS_A_MORE_FAVORABLE_STANCE, ticker=preferred),),
    )

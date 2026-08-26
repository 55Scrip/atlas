"""The Portfolio Fit Engine itself -- pure, deterministic, no I/O.

Every function here is a total function of its arguments: the same
`CanonicalAnalysis` + `AlphaPortfolioState` + holding always produces the
exact same `PortfolioFitAssessment` (Deliverable 1/10). Nothing in this
module reads a repository, a clock beyond the `now` argument, or any
other ambient state.

**Why six dimensions, not eight.** The sprint brief names eight example
dimensions. Two are not separate computations here:

- **Diversification Fit** would need sector/country/asset-class spread.
  `AlphaHolding` carries none of those fields (confirmed against
  `atlas.alpha.portfolio_intelligence`'s own module docstring, which
  already disclosed the identical gap for Key Findings). Computing it
  would mean inventing a new field on an existing model -- forbidden by
  this sprint's own "no new domain objects" instruction. What *is* real
  and available -- portfolio-wide concentration -- is exactly what
  `_allocation_fit` below already reads, so a separate "Diversification
  Fit" dimension would just be a second label over the same one input.
- **Position Size Impact** is, for the data this engine has (no trade
  size input exists anywhere in Atlas today), the identical question
  `_allocation_fit` already answers: does this holding's size (current,
  for a holding; portfolio-context only, for a candidate with no size to
  evaluate) create concentration risk. Splitting it into a second
  dimension would duplicate the same computation under a second name --
  exactly what Deliverable 10 requires this engine prove it does not do.

Both gaps are disclosed on every `PortfolioFitAssessment.data_gaps`
rather than silently folded away.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.coverage import assess_coverage
from atlas.alpha.investment_case.models import InvestmentCaseComposition
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio_fit.models import (
    FitComparison,
    FitDimension,
    FitDimensionKind,
    FitRating,
    FitTrend,
    FitVerdictReasonCode,
    PortfolioFitAssessment,
)
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.investment_case_change import ThesisImpact
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.outlook import HorizonOutlook
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES, RiskAnalysisResult, RiskStatus
from atlas.analysis_engine.valuation.models import ValuationEngineResult, ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupport, ValuationSupportStatus
from atlas.domains.portfolio.models import ConcentrationLevel

__all__ = ["assess_portfolio_fit", "compare_fit"]

# The exact thresholds `atlas.domains.portfolio.calculations
# .concentration_level` uses (0.35/0.25, as a fraction of total portfolio
# value) -- reused verbatim here, expressed as percentages, rather than
# re-derived. See this module's own docstring: no new business rule, the
# same rule applied to one holding's own weight instead of only the
# portfolio's largest position.
_HIGH_CONCENTRATION_WEIGHT_PERCENT = 35.0
_ELEVATED_CONCENTRATION_WEIGHT_PERCENT = 25.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------
# Business Fit
# ---------------------------------------------------------------------


#: Trust Hardening Sprint: `BusinessAnalysisResult.state` is *always*
#: `EvaluationState.EVALUATED` (see that class's own docstring --
#: "assembling six conclusions, honest or real, is itself a real,
#: deterministic result"), so gating on `.state` here was dead code --
#: it never distinguished a company with real findings from one where
#: every category came back `INSUFFICIENT_INPUT`/`NOT_EVALUATED`. The
#: real signal is whether any *individual* category reached a real
#: conclusion, the same `WEAK`/`MODERATE`/`STRONG` set
#: `investment_case_lifecycle.engine._BUSINESS_REAL_STATUSES` and
#: `direction_selector._INCONCLUSIVE_BUSINESS_STATUSES` already both
#: use for the identical distinction -- defined locally here rather
#: than imported, mirroring how `direction_selector.py` itself defines
#: its own copy rather than reaching into a sibling package.
_REAL_BUSINESS_STATUSES = frozenset(
    {BusinessCategoryStatus.WEAK, BusinessCategoryStatus.MODERATE, BusinessCategoryStatus.STRONG}
)


def _business_fit(business_analysis) -> FitDimension:  # noqa: ANN001 -- BusinessAnalysisResult
    statuses = [finding.status for finding in business_analysis.findings]
    if not any(status in _REAL_BUSINESS_STATUSES for status in statuses):
        return FitDimension(
            kind=FitDimensionKind.BUSINESS,
            rating=FitRating.UNAVAILABLE,
            reasoning=(),
            unavailable_reason="Business analysis has not reached a full evaluation for this Case yet.",
        )

    strong = statuses.count(BusinessCategoryStatus.STRONG)
    moderate = statuses.count(BusinessCategoryStatus.MODERATE)
    weak = statuses.count(BusinessCategoryStatus.WEAK)
    total = len(statuses)

    if weak >= 3:
        rating = FitRating.POOR
    elif weak >= 1 and strong == 0:
        rating = FitRating.WEAK
    elif strong >= 4:
        rating = FitRating.EXCELLENT
    elif strong >= 2 and weak == 0:
        rating = FitRating.GOOD
    else:
        rating = FitRating.NEUTRAL

    reasoning = (f"{strong} of {total} business categories rated Strong, {moderate} Moderate, {weak} Weak.",)
    return FitDimension(kind=FitDimensionKind.BUSINESS, rating=rating, reasoning=reasoning)


# ---------------------------------------------------------------------
# Valuation Fit
# ---------------------------------------------------------------------

# Decision table: (primary FCF-yield status, capital-deployment support
# status) -> rating. `INSUFFICIENT_INPUT`/`NOT_EVALUATED` on the primary
# status are treated identically here (both mean "no real valuation
# conclusion"), matching how every other dimension in this module folds
# `EvaluationState`'s two non-evaluated members together.
_VALUATION_TABLE: dict[tuple[ValuationStatus, ValuationSupportStatus], FitRating] = {
    (ValuationStatus.UNDERVALUED, ValuationSupportStatus.SUPPORTED): FitRating.EXCELLENT,
    (ValuationStatus.UNDERVALUED, ValuationSupportStatus.NOT_SUPPORTED): FitRating.GOOD,
    (ValuationStatus.UNDERVALUED, ValuationSupportStatus.INSUFFICIENT_INPUT): FitRating.GOOD,
    (ValuationStatus.FAIRLY_VALUED, ValuationSupportStatus.SUPPORTED): FitRating.GOOD,
    (ValuationStatus.FAIRLY_VALUED, ValuationSupportStatus.NOT_SUPPORTED): FitRating.NEUTRAL,
    (ValuationStatus.FAIRLY_VALUED, ValuationSupportStatus.INSUFFICIENT_INPUT): FitRating.NEUTRAL,
    (ValuationStatus.EXPENSIVE, ValuationSupportStatus.SUPPORTED): FitRating.NEUTRAL,
    (ValuationStatus.EXPENSIVE, ValuationSupportStatus.NOT_SUPPORTED): FitRating.POOR,
    (ValuationStatus.EXPENSIVE, ValuationSupportStatus.INSUFFICIENT_INPUT): FitRating.WEAK,
}


def _valuation_fit(valuation_engine: ValuationEngineResult, valuation_support: ValuationSupport) -> FitDimension:
    primary = next(
        (f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE),
        None,
    )
    primary_status = primary.status if primary is not None else ValuationStatus.NOT_EVALUATED
    has_primary = primary_status in (ValuationStatus.UNDERVALUED, ValuationStatus.FAIRLY_VALUED, ValuationStatus.EXPENSIVE)

    if not has_primary and valuation_support.status is ValuationSupportStatus.INSUFFICIENT_INPUT:
        return FitDimension(
            kind=FitDimensionKind.VALUATION,
            rating=FitRating.UNAVAILABLE,
            reasoning=(),
            unavailable_reason="Neither the relative valuation conclusion nor capital-deployment support has enough data yet.",
        )

    if has_primary:
        rating = _VALUATION_TABLE[(primary_status, valuation_support.status)]
    else:
        # No conclusive relative-valuation finding, but capital-deployment
        # support did resolve -- lean on that alone, one notch more
        # cautious than the matching "fairly valued" row since the primary
        # conclusion itself is still unresolved.
        rating = {
            ValuationSupportStatus.SUPPORTED: FitRating.NEUTRAL,
            ValuationSupportStatus.NOT_SUPPORTED: FitRating.WEAK,
        }.get(valuation_support.status, FitRating.NEUTRAL)

    reasoning = [
        f"Relative valuation: {primary_status.value.replace('_', ' ')}."
        if has_primary
        else "Relative valuation not yet conclusive.",
        f"Capital-deployment support: {valuation_support.status.value.replace('_', ' ')}.",
    ]
    return FitDimension(kind=FitDimensionKind.VALUATION, rating=rating, reasoning=tuple(reasoning))


# ---------------------------------------------------------------------
# Risk Fit
# ---------------------------------------------------------------------

#: Trust Hardening Sprint: the same dead-code gate as `_business_fit`
#: above -- `RiskAnalysisResult.state` is always `EVALUATED` by its own
#: contract. Real signal is whether any evaluated category reached a
#: real conclusion (`LOW`/`MODERATE`/`HIGH`), matching
#: `investment_case_lifecycle.engine._RISK_REAL_STATUSES` exactly.
_REAL_RISK_STATUSES = frozenset({RiskStatus.LOW, RiskStatus.MODERATE, RiskStatus.HIGH})


def _risk_fit(risk_analysis: RiskAnalysisResult) -> FitDimension:
    relevant = [f for f in risk_analysis.findings if f.category in EVALUATED_RISK_CATEGORIES]
    statuses = [f.status for f in relevant]
    if not any(status in _REAL_RISK_STATUSES for status in statuses):
        return FitDimension(
            kind=FitDimensionKind.RISK,
            rating=FitRating.UNAVAILABLE,
            reasoning=(),
            unavailable_reason="Risk analysis has not reached a full evaluation for this Case yet.",
        )

    high = statuses.count(RiskStatus.HIGH)
    moderate = statuses.count(RiskStatus.MODERATE)
    low = statuses.count(RiskStatus.LOW)

    if high >= 2:
        rating = FitRating.POOR
    elif high == 1:
        rating = FitRating.WEAK
    elif moderate >= 3:
        rating = FitRating.NEUTRAL
    elif moderate >= 1:
        rating = FitRating.GOOD
    else:
        rating = FitRating.EXCELLENT

    reasoning = (f"{high} of {len(relevant)} evaluated risk categories rated High, {moderate} Moderate, {low} Low.",)
    return FitDimension(kind=FitDimensionKind.RISK, rating=rating, reasoning=reasoning)


# ---------------------------------------------------------------------
# Allocation Fit
# ---------------------------------------------------------------------


def _allocation_fit(
    holding: AlphaHolding | None,
    portfolio_state: AlphaPortfolioState,
) -> FitDimension:
    summary = derive_portfolio_view(portfolio_state)

    if holding is not None:
        weight = holding.weight_percent
        if weight >= _HIGH_CONCENTRATION_WEIGHT_PERCENT:
            rating = FitRating.POOR
        elif weight >= _ELEVATED_CONCENTRATION_WEIGHT_PERCENT:
            rating = FitRating.WEAK
        elif weight >= 15.0:
            rating = FitRating.NEUTRAL
        elif weight >= 5.0:
            rating = FitRating.GOOD
        else:
            rating = FitRating.EXCELLENT
        reasoning = (
            f"This holding is {weight:.1f}% of the portfolio "
            f"(portfolio concentration overall: {summary.concentration.level.value}).",
        )
        return FitDimension(kind=FitDimensionKind.ALLOCATION, rating=rating, reasoning=reasoning)

    # A candidate has no real weight to evaluate -- no trade-size input
    # exists anywhere in Atlas today (Deliverable 1's own input list has
    # no such field). Rating reflects the portfolio's existing
    # concentration context only, never a fabricated projected weight.
    level = summary.concentration.level
    rating = {
        ConcentrationLevel.HIGH: FitRating.WEAK,
        ConcentrationLevel.ELEVATED: FitRating.NEUTRAL,
        ConcentrationLevel.MODERATE: FitRating.GOOD,
        ConcentrationLevel.LOW: FitRating.GOOD,
    }[level]
    reasoning = (
        f"No trade size is available to project a resulting weight; portfolio concentration is "
        f"currently {level.value}.",
    )
    return FitDimension(kind=FitDimensionKind.ALLOCATION, rating=rating, reasoning=reasoning)


# ---------------------------------------------------------------------
# Expected Contribution
# ---------------------------------------------------------------------


def _expected_contribution_fit(long_term: HorizonOutlook) -> FitDimension:
    if long_term.expected_return is None:
        return FitDimension(
            kind=FitDimensionKind.EXPECTED_CONTRIBUTION,
            rating=FitRating.UNAVAILABLE,
            reasoning=(),
            unavailable_reason=(
                long_term.expected_return_gap.value.replace("_", " ")
                if long_term.expected_return_gap is not None
                else "No long-term expected-return range is available."
            ),
        )

    # `ExpectedReturnRange.low_percent`/`high_percent` are fractional
    # returns (e.g. `0.15` for +15%), matching `ValuationFinding
    # .current_yield`'s own convention (`outlook.py`'s own docstring) --
    # converted to percentage points here, once, for both the threshold
    # comparisons below and the disclosed reasoning text.
    er = long_term.expected_return
    low_pct = er.low_percent * 100
    high_pct = er.high_percent * 100
    midpoint = (low_pct + high_pct) / 2
    if low_pct <= -10.0:
        rating = FitRating.POOR
    elif midpoint < 0.0:
        rating = FitRating.WEAK
    elif midpoint < 8.0:
        rating = FitRating.NEUTRAL
    elif midpoint < 15.0:
        rating = FitRating.GOOD
    else:
        rating = FitRating.EXCELLENT

    reasoning = (
        f"Long-term valuation-implied re-rating range: {low_pct:.1f}% to {high_pct:.1f}% "
        f"annualized (a re-rating estimate, not a full forecast).",
    )
    return FitDimension(kind=FitDimensionKind.EXPECTED_CONTRIBUTION, rating=rating, reasoning=reasoning)


# ---------------------------------------------------------------------
# Cash Impact
# ---------------------------------------------------------------------


def _cash_impact_fit(portfolio_state: AlphaPortfolioState) -> FitDimension:
    cash = portfolio_state.cash_weight_percent
    if cash is None:
        return FitDimension(
            kind=FitDimensionKind.CASH_IMPACT,
            rating=FitRating.UNAVAILABLE,
            reasoning=(),
            unavailable_reason="Portfolio cash position has not been recorded.",
        )

    if cash >= 15.0:
        rating = FitRating.EXCELLENT
    elif cash >= 8.0:
        rating = FitRating.GOOD
    elif cash >= 3.0:
        rating = FitRating.NEUTRAL
    elif cash >= 1.0:
        rating = FitRating.WEAK
    else:
        rating = FitRating.POOR

    reasoning = (f"Portfolio cash position is {cash:.1f}%.",)
    return FitDimension(kind=FitDimensionKind.CASH_IMPACT, rating=rating, reasoning=reasoning)


# ---------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------

_TREND_BY_THESIS_IMPACT = {
    ThesisImpact.STRENGTHENED: FitTrend.IMPROVING,
    ThesisImpact.WEAKENED: FitTrend.DECLINING,
    ThesisImpact.MIXED: FitTrend.MIXED,
    ThesisImpact.UNCHANGED: FitTrend.UNCHANGED,
}


def _trend(composition: InvestmentCaseComposition) -> FitTrend:
    change_intelligence = composition.change_intelligence
    if change_intelligence is None or change_intelligence.is_baseline:
        return FitTrend.UNAVAILABLE
    return _TREND_BY_THESIS_IMPACT.get(change_intelligence.thesis_impact, FitTrend.UNAVAILABLE)


# ---------------------------------------------------------------------
# Overall aggregation
# ---------------------------------------------------------------------

_ORDERED_RATINGS = (FitRating.POOR, FitRating.WEAK, FitRating.NEUTRAL, FitRating.GOOD, FitRating.EXCELLENT)


def _overall_fit(
    dimensions: tuple[FitDimension, ...],
) -> tuple[FitRating, tuple[str, ...], FitVerdictReasonCode, int | None]:
    """Deterministic, rule-based aggregation -- explicit gates over the
    *set* of dimension ratings, the same reasoning style
    `atlas.analysis_engine.recommendation`'s own conviction gate uses,
    never a weighted average or any other hidden numeric score.

    Implementation Sprint B1.2: the 3rd/4th return values are additive
    -- `FitVerdictReasonCode` names which of the 8 branches below fired
    (`FitRating` alone conflates `RISK_GATE`/`MULTIPLE_POOR`, both
    `POOR`); the trailing `int | None` is the one real count two of
    those branches already compute (`MULTIPLE_POOR`'s Poor count,
    `MOSTLY_EXCELLENT`'s Excellent-of-evaluated count) -- `None` for
    every other branch, never a fabricated number."""

    evaluated = [d for d in dimensions if d.rating is not FitRating.UNAVAILABLE]
    if not evaluated:
        return FitRating.UNAVAILABLE, ("No dimension could be evaluated for this company.",), FitVerdictReasonCode.NO_DIMENSION_EVALUATED, None

    # Trust Hardening Sprint: an overall verdict is a statement about
    # how well *this company* fits the portfolio -- it must never rest
    # solely on portfolio-structural dimensions (Allocation, Expected
    # Contribution, Cash Impact) that need no company-specific data at
    # all. Business/Valuation/Risk are the only dimensions that read
    # real, ingested company analysis (`CanonicalAnalysis`) -- if none
    # of the three ever reached a real conclusion, Atlas knows nothing
    # about the company itself, and no overall rating may be produced,
    # regardless of how favorable the structural dimensions look (this
    # is exactly how a zero-data holding like BTC previously reached
    # "Good"/"Excellent" fit purely from its position size and the
    # portfolio's cash level).
    analytical_kinds = (FitDimensionKind.BUSINESS, FitDimensionKind.VALUATION, FitDimensionKind.RISK)
    if not any(d.kind in analytical_kinds for d in evaluated):
        return (
            FitRating.UNAVAILABLE,
            (
                "No company-level analysis (Business, Valuation, or Risk) has been evaluated yet -- "
                "portfolio-context dimensions alone cannot establish a fit verdict for this company.",
            ),
            FitVerdictReasonCode.NO_COMPANY_LEVEL_ANALYSIS,
            None,
        )

    counts = {rating: sum(1 for d in evaluated if d.rating is rating) for rating in _ORDERED_RATINGS}
    risk = next((d for d in evaluated if d.kind is FitDimensionKind.RISK), None)

    if risk is not None and risk.rating is FitRating.POOR:
        return (
            FitRating.POOR,
            ("Risk Fit is Poor, which this engine treats as a gate on the overall verdict.",),
            FitVerdictReasonCode.RISK_GATE,
            None,
        )
    if counts[FitRating.POOR] >= 2:
        return FitRating.POOR, (f"{counts[FitRating.POOR]} dimensions rated Poor.",), FitVerdictReasonCode.MULTIPLE_POOR, counts[FitRating.POOR]
    if counts[FitRating.POOR] + counts[FitRating.WEAK] > counts[FitRating.GOOD] + counts[FitRating.EXCELLENT]:
        return (
            FitRating.WEAK,
            ("More dimensions rated Weak/Poor than Good/Excellent.",),
            FitVerdictReasonCode.MORE_WEAK_POOR_THAN_GOOD_EXCELLENT,
            None,
        )
    if counts[FitRating.EXCELLENT] >= (len(evaluated) + 1) // 2 and counts[FitRating.WEAK] == 0 and counts[FitRating.POOR] == 0:
        return (
            FitRating.EXCELLENT,
            (f"{counts[FitRating.EXCELLENT]} of {len(evaluated)} evaluated dimensions rated Excellent, none Weak or Poor.",),
            FitVerdictReasonCode.MOSTLY_EXCELLENT,
            counts[FitRating.EXCELLENT],
        )
    if counts[FitRating.GOOD] + counts[FitRating.EXCELLENT] > counts[FitRating.WEAK] + counts[FitRating.POOR]:
        return (
            FitRating.GOOD,
            ("More dimensions rated Good/Excellent than Weak/Poor.",),
            FitVerdictReasonCode.MORE_GOOD_EXCELLENT_THAN_WEAK_POOR,
            None,
        )
    return FitRating.NEUTRAL, ("Dimension ratings are mixed, with no clear lean either way.",), FitVerdictReasonCode.MIXED, None


# ---------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------


def assess_portfolio_fit(
    *,
    composition: InvestmentCaseComposition,
    portfolio_state: AlphaPortfolioState,
    holding: AlphaHolding | None,
    ticker: str,
    now: datetime | None = None,
) -> PortfolioFitAssessment:
    """The Portfolio Fit Engine's one real entry point (Deliverable 1).

    `holding` is the linked `AlphaHolding` when this Case is an existing
    Portfolio position, else `None` (a Watchlist Case or a bare
    Candidate) -- the exact distinction `AlphaHolding.case_id`/
    `InvestmentCaseComposition.holding_context` already carry, not a new
    concept. `ticker` is always given explicitly by the caller rather
    than derived here: `composition.holding_context` only ever resolves
    a *Portfolio* holding (see `InvestmentCaseCompositionService`'s own
    scope), so deriving it internally silently fell back to the raw
    `case_id` UUID for every Watchlist-only Case -- a real bug found
    during this sprint's own live verification. `service.py` (which
    already knows the real ticker from `known_cases()`/the URL/the
    linked holding for every one of its callers) is the correct, single
    place to resolve it.
    """
    analysis: CanonicalAnalysis = composition.canonical_analysis
    dimensions = (
        _business_fit(analysis.business_analysis),
        _valuation_fit(analysis.valuation_engine, analysis.valuation_support),
        _risk_fit(analysis.risk_analysis),
        _allocation_fit(holding, portfolio_state),
        _expected_contribution_fit(analysis.outlook.long_term),
        _cash_impact_fit(portfolio_state),
    )
    overall, overall_reasoning, overall_reasoning_code, overall_reasoning_count = _overall_fit(dimensions)

    data_gaps = tuple(f"{d.kind.value}: {d.unavailable_reason}" for d in dimensions if d.unavailable_reason is not None)

    return PortfolioFitAssessment(
        case_id=composition.case_id,
        ticker=ticker,
        is_existing_holding=holding is not None,
        current_weight_percent=holding.weight_percent if holding is not None else None,
        overall=overall,
        overall_reasoning=overall_reasoning,
        overall_reasoning_code=overall_reasoning_code,
        overall_reasoning_count=overall_reasoning_count,
        dimensions=dimensions,
        trend=_trend(composition),
        data_gaps=data_gaps,
        coverage=assess_coverage(analysis, is_thesis_stale=composition.is_thesis_stale),
        generated_at=now or _utc_now(),
    )


def compare_fit(assessment_a: PortfolioFitAssessment, assessment_b: PortfolioFitAssessment) -> FitComparison:
    """Deliverable 4 -- Company Comparison. Reads two already-computed
    assessments; computes nothing new about either company."""

    rank = {rating: index for index, rating in enumerate(_ORDERED_RATINGS)}
    rank_a = rank.get(assessment_a.overall, -1)
    rank_b = rank.get(assessment_b.overall, -1)

    if assessment_a.overall is FitRating.UNAVAILABLE and assessment_b.overall is FitRating.UNAVAILABLE:
        preferred = None
        reasoning = ("Neither company has an evaluated Portfolio Fit yet.",)
    elif rank_a == rank_b:
        preferred = None
        reasoning = (f"Both companies rate {assessment_a.overall.value.title()} overall.",)
    else:
        preferred_assessment = assessment_a if rank_a > rank_b else assessment_b
        other_assessment = assessment_b if rank_a > rank_b else assessment_a
        preferred = preferred_assessment.ticker
        reasoning = [
            f"{preferred_assessment.ticker} rates {preferred_assessment.overall.value.title()} overall, "
            f"{other_assessment.ticker} rates {other_assessment.overall.value.title()}.",
        ]
        by_kind_a = {d.kind: d for d in assessment_a.dimensions}
        by_kind_b = {d.kind: d for d in assessment_b.dimensions}
        for kind, dim_a in by_kind_a.items():
            dim_b = by_kind_b.get(kind)
            if dim_b is None or dim_a.rating is dim_b.rating:
                continue
            better = assessment_a.ticker if rank.get(dim_a.rating, -1) > rank.get(dim_b.rating, -1) else assessment_b.ticker
            reasoning.append(
                f"{kind.value.replace('_', ' ').title()}: {better} rates higher "
                f"({dim_a.rating.value if better == assessment_a.ticker else dim_b.rating.value})."
            )
        reasoning = tuple(reasoning)

    return FitComparison(
        assessment_a=assessment_a,
        assessment_b=assessment_b,
        preferred_ticker=preferred,
        reasoning=reasoning,
    )

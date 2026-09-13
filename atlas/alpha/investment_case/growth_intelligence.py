"""Growth Knowledge Model + Multi-Year Growth History + Growth
Intelligence + Growth Durability + Segment Growth (Capability
Expansion Sprint 6: Growth Intelligence, Phases 1 + 3 through 6).

**Builds directly on `financial_statement_intelligence.py` (Sprint 3)**
for every raw level (`revenue`/`net_income`/`eps`/`operating_cash_flow`
/`free_cash_flow`/`equity`) -- the same "second-order transformation of
already-covered data" convention `financial_quality_intelligence.py`
(Sprint 5) already establishes, applied here to growth rather than
quality.

**Phase 2 audit finding, corrected after an initial mistake this
sprint's own "validate every architectural assumption against the real
code" discipline caught**: `atlas.analysis_engine.growth.classify_
metric_trend` is a real, public function, and its own docstring even
invites reuse -- but `tests/unit/alpha/investment_case/test_boundaries
.py::TestNoForbiddenDependencies.test_no_forbidden_imports` is a real,
pre-existing, enforced rule that `atlas.alpha.investment_case` (this
whole package -- every prior capability-sprint module lives here) may
*never* import an individual `analysis_engine` evaluator module
directly, only the canonical `assemble_analysis` entry point ("Phase
9/14's own 'never duplicate Business/Valuation/Risk/Conviction' rule,
checked structurally," per that test's own docstring). An earlier
version of this module imported `classify_metric_trend` directly and
was caught immediately by that test. `_consistency_from_values` below
duplicates that function's own monotonic rule instead -- for every
metric, including Revenue/Free Cash Flow, not only the four with no
`BusinessFactKind` counterpart -- the same "small, justified
duplication over a forbidden import" discipline every prior capability
sprint already followed for its own trend algorithm, now understood to
be a real enforced boundary rather than only a stylistic preference.
This module's own test suite still calls the real `classify_metric_
trend` as a consistency oracle -- from the test file, which sits
outside `atlas/alpha/investment_case/` and is not subject to this
boundary -- verifying the two independent implementations agree,
rather than production code calling the real one.

**"Share Count Adjusted Growth" (Phase 1) is represented by earnings-
per-share growth**, not a hand-derived revenue-per-share ratio: diluted
EPS (`IncomeStatementPeriod.eps`, already a real, filed Sprint 3 field)
already divides earnings by share count, so its own growth rate already
answers "does growth survive dilution" without this module inventing a
second, cross-referenced per-share calculation.

**Segment/Geographic Growth (Phase 6) is honestly unavailable.**
`FinancialStatementHistory.segments` is always empty (see Sprint 3's
own module docstring for why) -- `SegmentGrowthInformation` exposes
that absence as real structured knowledge, never a fabricated segment
breakdown.

**"Cyclicality" (Phase 5) and "sustainability" (Phase 5) are
deliberately not implemented.** Detecting a genuine business cycle
needs real time-series decomposition (seasonality, autocorrelation)
this sprint does not attempt -- inventing a heuristic with no real
grounding would be exactly the "never fabricate historical growth"
instruction this sprint's own discipline forbids. "Sustainability"
would require judging whether growth *can continue* -- a forward-
looking claim this sprint's own non-goals explicitly rule out ("must
not predict future growth"). `GrowthDurability.recovery_status`
(a real, historical, backward-looking fact -- did a decline get
followed by renewed growth) is implemented instead.

**CAGR is `None`, never fabricated, whenever the start or end value is
non-positive** -- a compound annual growth rate computed across a sign
change (loss to profit, or vice versa) is not a real percentage; `None`
is the honest answer, not a misleadingly large or negative number.

**Years are fiscal years, never list positions.** CAGR and year-over-year
growth read the analysis engine's fiscal-year identity
(`business_facts.growth_primitives.fiscal_years_apart`) -- an opinion-free
primitive, not an evaluator, so importing it is not the recomputation the
boundary above forbids. A CAGR spans the fiscal years between its ends;
year-over-year growth exists only between consecutive fiscal years;
duplicate labels of one year are that one year.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.financial_statement_intelligence import FinancialStatementHistory, TrendDirection
from atlas.analysis_engine.business_facts.growth_primitives import fiscal_calendar, fiscal_years_apart

__all__ = [
    "TrendDirection",
    "GrowthMetric",
    "GrowthConsistency",
    "GrowthPattern",
    "RecoveryStatus",
    "GrowthObservation",
    "GrowthDurability",
    "GrowthTrendKnowledge",
    "SegmentGrowthInformation",
    "GrowthKnowledge",
    "extract_growth_knowledge",
]

_MIN_PERIODS_FOR_TREND = 3
_MIN_PERIODS_FOR_PATTERN = 3
_TREND_THRESHOLD = 0.1
_PATTERN_VOLATILITY_THRESHOLD_STD = 0.25
"""The standard deviation of year-over-year growth rates above which a
metric's own growth is called `VOLATILE` rather than accelerating/
decelerating/stable -- a disclosed bucket boundary (a 25-percentage-
-point typical swing), not a fabricated cutoff."""


def _trend_direction(values: tuple[float, ...]) -> TrendDirection:
    """Duplicated (not imported) from `financial_statement_intelligence
    ._trend_direction` -- that function is private; see this module's
    own docstring for what *is* reused from Sprint 3 (its public data
    shapes) and from `growth.py` (its own public trend function)."""
    if len(values) < _MIN_PERIODS_FOR_TREND:
        return TrendDirection.INSUFFICIENT_DATA
    spread = max(values) - min(values)
    if spread == 0:
        return TrendDirection.STABLE
    midpoint = len(values) // 2
    earlier_avg = sum(values[:midpoint]) / midpoint
    later_avg = sum(values[midpoint:]) / (len(values) - midpoint)
    relative_change = (later_avg - earlier_avg) / spread
    if relative_change > _TREND_THRESHOLD:
        return TrendDirection.RISING
    if relative_change < -_TREND_THRESHOLD:
        return TrendDirection.FALLING
    return TrendDirection.STABLE


class GrowthMetric(str, Enum):
    REVENUE = "revenue"
    EARNINGS = "earnings"
    OPERATING_CASH_FLOW = "operating_cash_flow"
    FREE_CASH_FLOW = "free_cash_flow"
    BOOK_VALUE = "book_value"
    EARNINGS_PER_SHARE = "earnings_per_share"


class GrowthConsistency(str, Enum):
    """Mirrors `analysis_engine.growth.MetricTrend`'s own three-way
    vocabulary (never imported -- see this module's own docstring),
    plus a fourth, honest `INSUFFICIENT_DATA` state that function's own
    zero/one-period edge case does not distinguish (see this module's
    own `_consistency_from_values`)."""

    CONSISTENT_GROWTH = "consistent_growth"
    CONSISTENT_DECLINE = "consistent_decline"
    MIXED = "mixed"
    INSUFFICIENT_DATA = "insufficient_data"


class GrowthPattern(str, Enum):
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    STABLE = "stable"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class RecoveryStatus(str, Enum):
    RECOVERED = "recovered"
    """The most recent known period grew, after at least one earlier
    period declined -- a real, historical, backward-looking fact."""
    NO_DECLINE_OBSERVED = "no_decline_observed"
    CURRENTLY_DECLINING = "currently_declining"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class GrowthObservation:
    period_end: date
    value: float | None
    year_over_year_growth: float | None


@dataclass(frozen=True)
class GrowthDurability:
    consistency: GrowthConsistency
    consecutive_growth_periods: int
    """Trailing consecutive periods of positive year-over-year growth,
    ending at the most recent known period -- `0` if the most recent
    known period did not grow."""
    recovery_status: RecoveryStatus


@dataclass(frozen=True)
class GrowthTrendKnowledge:
    metric: GrowthMetric
    observations: tuple[GrowthObservation, ...]
    """Chronological, oldest first."""
    cagr: float | None
    direction: TrendDirection
    pattern: GrowthPattern
    durability: GrowthDurability
    periods_considered: int


@dataclass(frozen=True)
class SegmentGrowthInformation:
    available: bool = False
    """Always `False` in this build -- see this module's own docstring."""


@dataclass(frozen=True)
class GrowthKnowledge:
    revenue: GrowthTrendKnowledge
    earnings: GrowthTrendKnowledge
    operating_cash_flow: GrowthTrendKnowledge
    free_cash_flow: GrowthTrendKnowledge
    book_value: GrowthTrendKnowledge
    earnings_per_share: GrowthTrendKnowledge
    segment_growth: SegmentGrowthInformation


def _consistency_from_values(values: tuple[float | None, ...]) -> GrowthConsistency:
    """Mirrors `analysis_engine.growth.classify_metric_trend`'s own
    monotonic rule exactly -- duplicated, never imported, for every
    metric (see this module's own docstring for why). Guarded to `< 2`
    known values *before* classifying -- that real function's own
    `all(... for ... in [])` on zero deltas returns `True` (vacuously
    "consistent growth"), a real edge case this module deliberately
    does not inherit for a company Atlas simply has no history for."""
    known = tuple(v for v in values if v is not None)
    if len(known) < 2:
        return GrowthConsistency.INSUFFICIENT_DATA
    signs: list[int] = []
    for previous, current in zip(known, known[1:]):
        if current > previous:
            signs.append(1)
        elif current < previous:
            signs.append(-1)
        else:
            signs.append(0)
    if all(sign > 0 for sign in signs):
        return GrowthConsistency.CONSISTENT_GROWTH
    if all(sign < 0 for sign in signs):
        return GrowthConsistency.CONSISTENT_DECLINE
    return GrowthConsistency.MIXED


@dataclass
class _FiscalYear:
    """One fiscal year's known reports: the period end and row index of
    its first report, and its value -- `None` when its reports disagree."""

    period_end: date
    first_index: int
    value: float | None


def _years_apart(earlier: date, later: date) -> int | None:
    return fiscal_years_apart(earlier.isoformat(), later.isoformat())


def _fiscal_years(period_ends: tuple[date, ...], values: tuple[float | None, ...]) -> list[_FiscalYear]:
    """Known values grouped into fiscal years, oldest first, by the
    analysis engine's own fiscal-year identity (`growth_primitives`):
    a report within two weeks of a year's first report is that same year
    (DE labels one fiscal year both 2015-10-31 and 2015-11-01). Reports of
    one year that disagree -- a restated comparative -- leave the year
    without a value, never averaged or chosen by order."""
    years: list[_FiscalYear] = []
    for index, (period_end, value) in enumerate(zip(period_ends, values)):
        if value is None:
            continue
        if years and _years_apart(years[-1].period_end, period_end) == 0:
            if years[-1].value != value:
                years[-1].value = None
            continue
        years.append(_FiscalYear(period_end=period_end, first_index=index, value=value))
    return years


def _build_observations(period_ends: tuple[date, ...], values: tuple[float | None, ...]) -> tuple[GrowthObservation, ...]:
    """Year-over-year growth only between two consecutive fiscal years,
    carried on the later year's first report: never across a missing year
    (NVDA's FY2012 -> FY2022 is not one year's growth), never between two
    reports of one year, never from a year whose reports disagree."""
    years = _fiscal_years(period_ends, values)
    growth_at: dict[int, float] = {}
    for previous, current in zip(years, years[1:]):
        if previous.value is None or current.value is None or previous.value == 0:
            continue
        if _years_apart(previous.period_end, current.period_end) == 1:
            growth_at[current.first_index] = (current.value - previous.value) / abs(previous.value)
    return tuple(
        GrowthObservation(period_end=period_end, value=value, year_over_year_growth=growth_at.get(index))
        for index, (period_end, value) in enumerate(zip(period_ends, values))
    )


def _cagr(period_ends: tuple[date, ...], values: tuple[float | None, ...]) -> float | None:
    """First to last fiscal year with a single value, annualised over the
    fiscal years between them -- never over the number of reports, which
    read NVDA's FY2010 -> FY2026 Free Cash Flow as seven years, not
    sixteen. Only years on the company's own fiscal calendar count, so a
    change of year end (GS: November, then December from 2009) starts the
    span at the first year of the current calendar."""
    known = [year for year in _fiscal_years(period_ends, values) if year.value is not None]
    on_calendar = fiscal_calendar([year.period_end.isoformat() for year in known])
    known = [year for year in known if year.period_end.isoformat() in on_calendar]
    if len(known) < 2:
        return None
    start, end = known[0], known[-1]
    if start.value <= 0 or end.value <= 0:
        return None
    years = _years_apart(start.period_end, end.period_end)
    if not years:
        return None
    return (end.value / start.value) ** (1 / years) - 1


def _pattern(yoy_rates: tuple[float, ...]) -> GrowthPattern:
    if len(yoy_rates) < _MIN_PERIODS_FOR_PATTERN:
        return GrowthPattern.INSUFFICIENT_DATA
    mean = sum(yoy_rates) / len(yoy_rates)
    variance = sum((rate - mean) ** 2 for rate in yoy_rates) / len(yoy_rates)
    std = variance**0.5
    if std > _PATTERN_VOLATILITY_THRESHOLD_STD:
        return GrowthPattern.VOLATILE
    direction = _trend_direction(yoy_rates)
    if direction is TrendDirection.RISING:
        return GrowthPattern.ACCELERATING
    if direction is TrendDirection.FALLING:
        return GrowthPattern.DECELERATING
    return GrowthPattern.STABLE


def _consecutive_growth_periods(yoy_rates: tuple[float | None, ...]) -> int:
    count = 0
    for rate in reversed(yoy_rates):
        if rate is None or rate <= 0:
            break
        count += 1
    return count


def _recovery_status(yoy_rates: tuple[float | None, ...]) -> RecoveryStatus:
    known = tuple(rate for rate in yoy_rates if rate is not None)
    if not known:
        return RecoveryStatus.INSUFFICIENT_DATA
    if known[-1] < 0:
        return RecoveryStatus.CURRENTLY_DECLINING
    if any(rate < 0 for rate in known[:-1]):
        return RecoveryStatus.RECOVERED
    return RecoveryStatus.NO_DECLINE_OBSERVED


def _growth_trend(
    metric: GrowthMetric, period_ends: tuple[date, ...], values: tuple[float | None, ...]
) -> GrowthTrendKnowledge:
    observations = _build_observations(period_ends, values)
    known_values = tuple(o.value for o in observations if o.value is not None)
    yoy_rates = tuple(o.year_over_year_growth for o in observations)
    known_yoy_rates = tuple(rate for rate in yoy_rates if rate is not None)
    return GrowthTrendKnowledge(
        metric=metric,
        observations=observations,
        cagr=_cagr(period_ends, values),
        direction=_trend_direction(known_values),
        pattern=_pattern(known_yoy_rates),
        durability=GrowthDurability(
            consistency=_consistency_from_values(values),
            consecutive_growth_periods=_consecutive_growth_periods(yoy_rates),
            recovery_status=_recovery_status(yoy_rates),
        ),
        periods_considered=len(known_values),
    )


def extract_growth_knowledge(history: FinancialStatementHistory) -> GrowthKnowledge:
    """Pure, no I/O. `history.income_statements == ()` yields every
    dimension at its own honest `INSUFFICIENT_DATA` default -- never a
    fabricated growth history (this sprint's own "never fabricate
    historical growth" instruction)."""
    income_period_ends = tuple(p.period_end for p in history.income_statements)
    revenue_values = tuple(p.revenue for p in history.income_statements)
    earnings_values = tuple(p.net_income for p in history.income_statements)
    eps_values = tuple(p.eps for p in history.income_statements)

    cash_flow_period_ends = tuple(p.period_end for p in history.cash_flow_statements)
    ocf_values = tuple(p.operating_cash_flow for p in history.cash_flow_statements)
    fcf_values = tuple(p.free_cash_flow for p in history.cash_flow_statements)

    balance_sheet_period_ends = tuple(p.period_end for p in history.balance_sheets)
    equity_values = tuple(p.equity for p in history.balance_sheets)

    return GrowthKnowledge(
        revenue=_growth_trend(GrowthMetric.REVENUE, income_period_ends, revenue_values),
        earnings=_growth_trend(GrowthMetric.EARNINGS, income_period_ends, earnings_values),
        operating_cash_flow=_growth_trend(GrowthMetric.OPERATING_CASH_FLOW, cash_flow_period_ends, ocf_values),
        free_cash_flow=_growth_trend(GrowthMetric.FREE_CASH_FLOW, cash_flow_period_ends, fcf_values),
        book_value=_growth_trend(GrowthMetric.BOOK_VALUE, balance_sheet_period_ends, equity_values),
        earnings_per_share=_growth_trend(GrowthMetric.EARNINGS_PER_SHARE, income_period_ends, eps_values),
        segment_growth=SegmentGrowthInformation(),
    )

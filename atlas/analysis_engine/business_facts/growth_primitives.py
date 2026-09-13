"""Shared, opinion-free analytical primitives (`DE-015` §17) -- the
"shared descriptive analytical primitive" layer `DE-015` requires to sit
between raw `BusinessFact`s and any domain (Valuation, Outlook) that wants
to reason about realized, multi-period growth without owning a second copy
of the same rolling-window/corroboration arithmetic.

**This module computes facts about facts. It never interprets them.**
Every function here answers a question of the form "what does the data
literally say," never "is that enough," "which extreme is favorable," or
"what should Atlas conclude." Concretely, this module contains, and will
never contain:

- eligibility (a `≥2 observations` floor, a "no legitimate growth basis"
  refusal, or any other sufficiency judgment) -- each domain applies its
  own;
- scenario labels (`Bull`/`Base`/`Bear`, `SUPPORTED`/`NOT_SUPPORTED`) --
  domain-owned;
- `ValuationSupport`/Outlook/Business status of any kind;
- proof logic of any kind;
- a numeric hurdle, threshold, or fabricated assumption of any kind.

**Why this lives in `business_facts`, not `valuation/` or as a new
top-level package.** This package's own module docstring already states
its purpose precisely: "produces no findings, no conclusions... Reusable
by design... a future Valuation stage can read the identical facts Growth
already extracts, without this package or its taxonomy needing to
change." That is exactly this module's role, one layer up (rolling
statistics over facts, not the facts themselves) -- not a new home, the
natural extension of an already-adopted one.

**Provenance.** Every function here was extracted, not reinvented, from
`atlas.analysis_engine.outlook`'s own rolling-CAGR/revenue-corroboration/
future-date-exclusion/annualized-return math (Calibration Sprint). Since
Calendar-True Rolling Windows this module is the one rolling-growth
implementation: Outlook's Long-Term range, Valuation Support's Scenario
eligibility and Growth's full-span CAGR all read it.

**Fiscal-year identity (Calendar-True Rolling Windows).** A fact carries
only its period end, so which fiscal year it describes is read from the
calendar, never from its position in a list. The rolling windows used to
pair list item `i` with item `i + N` and annualise over `N`: NVDA's history
jumps from FY2012 to FY2022, so 13-year spans were reported as 4-year
growth, and DE's filings label one fiscal year both 2015-10-31 and
2015-11-01, so 2- and 3-year spans passed as 4. The rules now:

- *Same fiscal year.* Period ends within `FISCAL_YEAR_END_TOLERANCE_DAYS`
  of each other describe one fiscal year. A 52/53-week calendar moves its
  year end within a seven-day band (2015-10-31 -> 2016-10-30 is one year);
  two weeks absorbs that band and any weekend shift while staying far
  below a quarter, so a quarter end can never join an annual one.
- *One value per fiscal year.* Reports of one fiscal year that agree are
  one observation. Reports that disagree -- a restated comparative -- are
  an ambiguity: the year is withheld, never averaged and never chosen by
  input order (the same rule the FCF-yield history applies per period).
- *N fiscal years apart.* Two fiscal years are N apart when the days
  between their period ends lie within the same tolerance of
  `N * FISCAL_YEAR_DAYS`. An N-year window exists only between two such
  years: a missing endpoint year means no window -- never the nearest
  available year, never a longer or shorter span annualised as N.
- A period that is not an ISO date has no place on a calendar and takes no
  part (every extracted fact's period is its record's ISO period end).

**Not exported here:** metric-trend classification
(`atlas.analysis_engine.growth.classify_metric_trend`/`MetricTrend`).
That function is already a neutral, mechanical, raw-fact-only classifier
(consecutive-period delta signs -> `STRONG_METRIC`/`WEAK_METRIC`/
`MIXED_METRIC` -- never `BusinessCategoryStatus`), and is already reused
directly across domain lines by `outlook.py` today. Re-extracting it here
would duplicate, not clarify, an already-established, already-neutral
utility; the valuation-native eligibility rule (`valuation/eligibility.py`)
imports it the same way `outlook.py` already does.
"""
from __future__ import annotations

import statistics
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact

__all__ = [
    "FISCAL_YEAR_DAYS",
    "FISCAL_YEAR_END_TOLERANCE_DAYS",
    "ROLLING_GROWTH_METHODOLOGY",
    "FiscalYearValue",
    "GrowthObservation",
    "DistributionSummary",
    "sorted_facts_of_kind",
    "exclude_future_dated",
    "real_periods",
    "fiscal_calendar",
    "fiscal_year_values",
    "fiscal_years_apart",
    "rolling_growth_observations",
    "corroborated_by",
    "distribution_summary",
    "compound_and_reprice_return",
]


def sorted_facts_of_kind(facts: tuple[BusinessFact, ...], kind: BusinessFactKind) -> list[BusinessFact]:
    """Every real fact of one kind, sorted by `period` ascending --
    the same one-line filter+sort every caller of this module needs
    before doing anything else, written once."""
    return sorted((f for f in facts if f.kind is kind), key=lambda f: f.period)


def exclude_future_dated(facts_sorted_asc: list[BusinessFact], *, as_of: datetime) -> list[BusinessFact]:
    """A `period` ending after `as_of` cannot be a *realized* historical
    observation by definition. Extracted verbatim from
    `outlook.py::_exclude_future_dated` -- see that function's own
    docstring for the real data-integrity bug this guard was written to
    make structurally unreachable, independent of whether the
    contaminating record itself is ever cleaned up."""
    cutoff = as_of.date().isoformat()
    return [f for f in facts_sorted_asc if f.period <= cutoff]


def real_periods(facts_sorted_asc: list[BusinessFact]) -> frozenset[str]:
    """The exact set of periods a real fact series actually covers --
    used for per-year corroboration (`corroborated_by`), never a bounds
    check (earliest-to-latest), since a bounds check would wrongly treat a
    genuine multi-year ingestion gap as covered."""
    return frozenset(f.period for f in facts_sorted_asc)


#: Names how rolling growth windows are built, so the Decision Layer never
#: reads the change to fiscal-year windows as a change in the company
#: (`atlas.analysis_engine.methodology`). v1 paired list positions.
ROLLING_GROWTH_METHODOLOGY = "fiscal_year_windows_v2"

#: The mean Gregorian year. Fiscal calendars are pinned to the civil
#: calendar (a fixed date, or the weekday nearest one), so a year end
#: never drifts from `N * FISCAL_YEAR_DAYS` by more than its own
#: seven-day band, however many years apart.
FISCAL_YEAR_DAYS = 365.2425

#: How far apart two period ends may be and still describe one fiscal
#: year -- and how far a span may miss a whole number of fiscal years.
#: See the module docstring.
FISCAL_YEAR_END_TOLERANCE_DAYS = 14


def _period_end(period: str) -> date | None:
    try:
        return date.fromisoformat(period)
    except ValueError:
        return None


@dataclass(frozen=True)
class FiscalYearValue:
    """One fiscal year's single, unambiguous value. `period` is the
    earliest period end reported for the year; `fact_ids` are every fact
    that reported it."""

    period: str
    period_end: date
    value: float
    fact_ids: tuple[str, ...]


def fiscal_year_values(facts: list[BusinessFact]) -> tuple[FiscalYearValue, ...]:
    """The facts as one value per fiscal year, oldest first -- see the
    module docstring. Input order never matters: facts are ordered by
    period end, then id. A group of period ends wider than the tolerance
    (a chain of near-duplicates) has no single identity and is withheld,
    like a year whose reports disagree."""
    dated = sorted(
        ((end, fact) for fact in facts if (end := _period_end(fact.period)) is not None),
        key=lambda pair: (pair[0], pair[1].id),
    )
    groups: list[list[tuple[date, BusinessFact]]] = []
    for end, fact in dated:
        if groups and (end - groups[-1][-1][0]).days <= FISCAL_YEAR_END_TOLERANCE_DAYS:
            groups[-1].append((end, fact))
        else:
            groups.append([(end, fact)])
    values: list[FiscalYearValue] = []
    for group in groups:
        first_end = group[0][0]
        if (group[-1][0] - first_end).days > FISCAL_YEAR_END_TOLERANCE_DAYS:
            continue
        if len({(fact.value, fact.unit) for _, fact in group}) != 1:
            continue
        values.append(FiscalYearValue(
            period=first_end.isoformat(),
            period_end=first_end,
            value=group[0][1].value,
            fact_ids=tuple(sorted(fact.id for _, fact in group)),
        ))
    return _on_fiscal_calendar(values)


def _on_fiscal_calendar(values: list[FiscalYearValue]) -> tuple[FiscalYearValue, ...]:
    on_calendar = fiscal_calendar([value.period for value in values])
    return tuple(value for value in values if value.period in on_calendar)


def fiscal_calendar(periods: list[str]) -> frozenset[str]:
    """The periods (oldest first) on the company's own fiscal calendar: the
    year end most of its years share (whole fiscal years apart), the most
    recent calendar on a tie. A quarter end, or a year from before a change
    of fiscal year end, is off that calendar and takes no part -- no span
    from it is a whole number of the company's fiscal years."""
    calendars: list[list[str]] = []
    for period in periods:
        for calendar in calendars:
            if fiscal_years_apart(calendar[0], period) is not None:
                calendar.append(period)
                break
        else:
            calendars.append([period])
    if not calendars:
        return frozenset()
    return frozenset(max(calendars, key=lambda calendar: (len(calendar), calendar[-1])))


def fiscal_years_apart(start_period: str, end_period: str) -> int | None:
    """How many whole fiscal years separate two period ends, or `None`
    when the span is not a whole number of fiscal years within the
    tolerance (or either period is not a date). `0` is the same year."""
    start, end = _period_end(start_period), _period_end(end_period)
    if start is None or end is None:
        return None
    days = (end - start).days
    years = round(days / FISCAL_YEAR_DAYS)
    if abs(days - years * FISCAL_YEAR_DAYS) > FISCAL_YEAR_END_TOLERANCE_DAYS:
        return None
    return years


@dataclass(frozen=True)
class GrowthObservation:
    """One rolling-window growth-rate observation -- a fact about the
    data, not a conclusion. `rate` is the compound annual growth rate
    between two positive fiscal-year values exactly `years` fiscal years
    apart; the endpoints and their facts are kept so the window's identity
    can always be checked."""

    start_period: str
    end_period: str
    rate: float
    years: int
    start_value: float
    end_value: float
    source_fact_ids: tuple[str, ...]


def rolling_growth_observations(
    facts_sorted_asc: list[BusinessFact], *, years: int
) -> tuple[GrowthObservation, ...]:
    """Every window from a fiscal year to the fiscal year exactly `years`
    later where both values are positive, oldest first. The years come
    from `fiscal_year_values`, so the window is a real `years`-year span
    and `rate` annualises over exactly that. A start year whose `years`
    -later year Atlas lacks forms no window at all. A single noisy period
    can no longer swing the whole distribution the way a raw year-over-year
    delta could: each observation smooths `years` worth of timing noise.
    (`facts_sorted_asc` is named for its callers; order is not relied on.)"""
    series = fiscal_year_values(facts_sorted_asc)
    ends = [value.period_end for value in series]
    span, window = timedelta(days=years * FISCAL_YEAR_DAYS), timedelta(days=FISCAL_YEAR_END_TOLERANCE_DAYS)
    observations: list[GrowthObservation] = []
    for start in series:
        target = start.period_end + span
        candidates = series[bisect_left(ends, target - window):bisect_right(ends, target + window)]
        matches = [end for end in candidates if fiscal_years_apart(start.period, end.period) == years]
        if len(matches) != 1:
            continue
        end = matches[0]
        if start.value > 0 and end.value > 0:
            observations.append(GrowthObservation(
                start_period=start.period,
                end_period=end.period,
                rate=(end.value / start.value) ** (1.0 / years) - 1.0,
                years=years,
                start_value=start.value,
                end_value=end.value,
                source_fact_ids=start.fact_ids + end.fact_ids,
            ))
    return tuple(observations)


def corroborated_by(
    observations: tuple[GrowthObservation, ...], corroborating_periods: frozenset[str]
) -> tuple[GrowthObservation, ...]:
    """The subset of `observations` where an independent fact series
    reports both endpoint fiscal years -- per-year presence, never a
    bounds check (see `real_periods`): a corroborating period counts for
    an endpoint when it is the same fiscal year. Generalized beyond
    Revenue: this function does not know or care which metric supplied
    the corroborating periods, only that they are real."""

    def reported(period: str) -> bool:
        return any(fiscal_years_apart(period, other) == 0 for other in corroborating_periods)

    return tuple(obs for obs in observations if reported(obs.start_period) and reported(obs.end_period))


@dataclass(frozen=True)
class DistributionSummary:
    """Plain descriptive statistics over a real, non-empty number
    sequence -- no label, no meaning, no Bull/Bear assignment. Assigning
    economic meaning to `minimum`/`maximum` (e.g. "Bull means the
    maximum") is each domain's own, separately-owned decision."""

    minimum: float
    median: float
    maximum: float


def distribution_summary(values: tuple[float, ...]) -> DistributionSummary | None:
    """`None` when `values` is empty -- there is no distribution to
    describe, and this module never invents one."""
    if not values:
        return None
    return DistributionSummary(minimum=min(values), median=statistics.median(values), maximum=max(values))


def compound_and_reprice_return(
    *, current_value: float, growth_rate: float, years: int, terminal_value: float
) -> float:
    """`((1+g)**years) * (current_value/terminal_value)` is the total
    -return multiple; its own `years`-th root minus one annualizes it.
    Extracted and generalized from `outlook.py::_annualized_return` --
    `terminal_value` is a real parameter here (not fixed), so a caller
    may vary it exactly as freely as `growth_rate`. Pure arithmetic: no
    eligibility, no scenario labeling, no sign judgment beyond the
    defensive `<= 0` guard already present in the source this was
    extracted from."""
    total_multiple = ((1.0 + growth_rate) ** years) * (current_value / terminal_value)
    if total_multiple <= 0:
        return -1.0
    return total_multiple ** (1.0 / years) - 1.0

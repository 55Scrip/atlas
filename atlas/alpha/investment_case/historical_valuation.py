"""Historical Valuation Knowledge Model + Historical Context Extraction
(Capability Expansion Sprint 1: Historical Valuation Intelligence,
Phases 1 + 3).

A small, read-only projection -- the same shape `regulatory_filings.py`/
`financial_history.py` already establish -- turning already-ingested,
already-extracted facts into structured *knowledge*, never a new
opinion: "is today's valuation historically cheap, expensive, or
consistent with the company's own history" is answered here as
percentiles, ranges, and trend/stability buckets, not as a
BUY/SELL-flavored conclusion. That conclusion already exists, entirely
unmodified, as `atlas.analysis_engine.valuation.cash_flow
.evaluate_fcf_yield_relative`'s own `UNDERVALUED`/`FAIRLY_VALUED`/
`EXPENSIVE` classification -- this module never recomputes or
second-guesses it.

**Per-period FCF-yield computation is intentionally duplicated here,
not imported, from `cash_flow.py`'s own no-look-ahead rule** (confirmed
by reading its source: a market observation's *eligible* Free Cash Flow
fact is the most recent one whose `published_at` is on or before that
observation's own date; `market_cap = share_price x shares_outstanding`;
`yield = FCF / market_cap`, excluded when FCF or market cap is
non-positive). Importing `cash_flow.py`'s own private helpers would
couple this package to the protected valuation-methodology module this
sprint's own non-goals forbid redesigning; duplicating this one small,
pure, well-documented rule keeps this package independent while
guaranteeing identical numbers for identical inputs -- verified by this
module's own test suite calling `evaluate_fcf_yield_relative` directly
as a consistency oracle.

Reads `BusinessFact`/`ValuationFact` -- the exact same, already-
extracted, already-deterministic facts `InvestmentCaseComposition
.business_facts`/`.market_facts` already carry for resolving a
`ValuationFinding`'s own `supporting_facts` ids (Product Sprint 14) --
never a `BusinessRecord`, provider object, or document content.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.valuation.facts import ValuationFact, ValuationFactKind

__all__ = [
    "ValuationMetricKind",
    "ValuationRangePosition",
    "ValuationTrend",
    "ValuationStability",
    "ValuationDataQuality",
    "ValuationObservation",
    "ValuationDeviation",
    "ValuationMetricHistory",
    "HistoricalValuationKnowledge",
    "extract_historical_valuation",
]


class ValuationMetricKind(str, Enum):
    """Closed, growing -- the same "framework, not complete dataset"
    discipline `KnowledgeDomain`'s own docstring establishes. `FCF_YIELD`
    is the only member with a real, wired computation today (Atlas's
    only real Valuation method, `ValuationMethodKind.FCF_YIELD_RELATIVE`
    -- the scenario methods never populate `current_yield`/
    `historical_yields` at all). A future method (P/E, EV/EBIT) adds one
    more member and one more branch in `extract_historical_valuation`;
    it never changes this enum's existing members or this module's
    public shape."""

    FCF_YIELD = "fcf_yield"


class ValuationRangePosition(str, Enum):
    """Where the current (most recent) observation sits relative to
    this metric's own historical range -- purely descriptive, never
    "cheap"/"expensive" (those words are `cash_flow.py`'s own
    `ValuationStatus` vocabulary, reserved for the Decision Layer)."""

    AT_OR_BELOW_HISTORICAL_LOW = "at_or_below_historical_low"
    BELOW_HISTORICAL_AVERAGE = "below_historical_average"
    AT_HISTORICAL_AVERAGE = "at_historical_average"
    ABOVE_HISTORICAL_AVERAGE = "above_historical_average"
    AT_OR_ABOVE_HISTORICAL_HIGH = "at_or_above_historical_high"
    INSUFFICIENT_DATA = "insufficient_data"


class ValuationTrend(str, Enum):
    """The later half of this metric's own chronological observations
    compared to the earlier half -- a real, disclosed statistical
    comparison, never a forecast or a fitted model."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class ValuationStability(str, Enum):
    """Coefficient of variation across every known observation, bucketed
    -- the same "categorical bucket over a continuous, disclosed
    threshold" discipline `EvidenceFreshness`'s own day-thresholds
    already use."""

    STABLE = "stable"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class ValuationDataQuality(str, Enum):
    """How much history this metric's own knowledge is built on --
    independent of `atlas.alpha.evidence_quality`'s own per-fact
    freshness grading (that answers "how recent"; this answers "how
    much")."""

    SUFFICIENT = "sufficient"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class ValuationObservation:
    period_end: date
    value: float


@dataclass(frozen=True)
class ValuationDeviation:
    """One observation whose value sits meaningfully outside this
    metric's own typical range -- a real, computed statistical fact
    ("significant historical deviations", Phase 3), never a flagged
    investment risk (that judgment belongs to the Decision Layer)."""

    period_end: date
    value: float
    deviation_from_average: float


@dataclass(frozen=True)
class ValuationMetricHistory:
    metric: ValuationMetricKind
    current_value: float | None
    """The most recent valid observation's own value -- `None` only
    when zero valid observations exist at all for this metric (mirrors
    `ValuationFinding.current_yield`'s own "real even with no history"
    contract)."""
    current_period_end: date | None
    observations: tuple[ValuationObservation, ...]
    """Every valid observation, chronological (oldest first), current
    included -- the full time series this metric's own statistics below
    are computed from."""
    historical_average: float | None
    historical_median: float | None
    historical_minimum: float | None
    historical_maximum: float | None
    """Computed over every observation *except* the current one --
    identical scope to `cash_flow.py`'s own `historical` dict, so
    `position_in_range` below is directly verifiable against
    `ValuationStatus`: `AT_OR_ABOVE_HISTORICAL_HIGH` <-> `UNDERVALUED`,
    `AT_OR_BELOW_HISTORICAL_LOW` <-> `EXPENSIVE`."""
    current_percentile: float | None
    """The share of historical observations at or below the current
    value, 0-100. `None` when there is no history to rank against."""
    position_in_range: ValuationRangePosition
    trend: ValuationTrend
    stability: ValuationStability
    significant_deviations: tuple[ValuationDeviation, ...]
    coverage_period_start: date | None
    coverage_period_end: date | None
    missing_periods: tuple[date, ...]
    """Market-data dates Atlas actually sampled a price for but could
    not turn into a valid observation (no eligible fundamental yet, a
    non-positive fundamental, or a non-positive market cap) -- a real,
    named gap, distinct from a date Atlas never sampled at all."""
    data_quality: ValuationDataQuality


@dataclass(frozen=True)
class HistoricalValuationKnowledge:
    metrics: tuple[ValuationMetricHistory, ...]
    """Empty, never fabricated, when no metric has enough data to say
    anything about -- one entry per `ValuationMetricKind` with at least
    one valid observation. Today: zero or one entries (only `FCF_YIELD`
    is wired)."""


_MIN_OBSERVATIONS_FOR_TREND = 4
_MIN_OBSERVATIONS_FOR_STABILITY = 2
_MIN_OBSERVATIONS_FOR_DEVIATIONS = 3
_TREND_THRESHOLD = 0.1
"""The later-half/earlier-half average gap, as a fraction of this
metric's own full observed range, that counts as a real trend rather
than noise -- a disclosed bucket boundary, not a fabricated score."""
_VOLATILITY_THRESHOLD = 0.15
"""Coefficient of variation above which a metric's own history is
called `VOLATILE` rather than `STABLE` -- disclosed, not derived from
any external benchmark."""
_DEVIATION_THRESHOLD_STD = 1.5
_SUFFICIENT_OBSERVATION_COUNT = 6
_LIMITED_OBSERVATION_COUNT = 2


def _parse_period_date(period: str) -> date | None:
    try:
        return date.fromisoformat(period)
    except ValueError:
        return None


def _eligible_fcf_as_of(fcf_facts: list[BusinessFact], as_of: date) -> BusinessFact | None:
    """Mirrors `cash_flow._eligible_fcf_as_of` exactly: the most recent
    Free Cash Flow fact (by `period`) among those whose `published_at`
    is on or before `as_of`."""
    eligible = [fact for fact in fcf_facts if fact.published_at.date() <= as_of]
    if not eligible:
        return None
    return max(eligible, key=lambda fact: (fact.period, fact.published_at, fact.id))


def _fcf_yield_observations(
    business_facts: tuple[BusinessFact, ...], market_facts: tuple[ValuationFact, ...]
) -> tuple[tuple[ValuationObservation, ...], tuple[date, ...]]:
    """Returns (valid observations, chronological; dates sampled but
    excluded). Mirrors `cash_flow.evaluate_fcf_yield_relative`'s own
    market-observation/no-look-ahead rule -- see this module's own
    docstring for why it is duplicated rather than imported."""
    fcf_facts = [f for f in business_facts if f.kind is BusinessFactKind.FREE_CASH_FLOW]
    price_by_period = {f.period: f for f in market_facts if f.kind is ValuationFactKind.SHARE_PRICE}
    shares_by_period = {f.period: f for f in market_facts if f.kind is ValuationFactKind.SHARES_OUTSTANDING}
    market_periods = sorted(set(price_by_period) & set(shares_by_period))

    observations: list[ValuationObservation] = []
    excluded: list[date] = []
    for period in market_periods:
        observation_date = _parse_period_date(period)
        if observation_date is None:
            continue
        eligible_fcf = _eligible_fcf_as_of(fcf_facts, observation_date)
        if eligible_fcf is None or eligible_fcf.value <= 0:
            excluded.append(observation_date)
            continue
        price_fact = price_by_period[period]
        shares_fact = shares_by_period[period]
        market_cap = price_fact.value * shares_fact.value
        if market_cap <= 0:
            excluded.append(observation_date)
            continue
        observations.append(ValuationObservation(period_end=observation_date, value=eligible_fcf.value / market_cap))

    observations.sort(key=lambda obs: obs.period_end)
    return tuple(observations), tuple(sorted(excluded))


def _position_in_range(current: float, historical: tuple[float, ...]) -> ValuationRangePosition:
    if not historical:
        return ValuationRangePosition.INSUFFICIENT_DATA
    if current <= min(historical):
        return ValuationRangePosition.AT_OR_BELOW_HISTORICAL_LOW
    if current >= max(historical):
        return ValuationRangePosition.AT_OR_ABOVE_HISTORICAL_HIGH
    average = sum(historical) / len(historical)
    if current < average:
        return ValuationRangePosition.BELOW_HISTORICAL_AVERAGE
    if current > average:
        return ValuationRangePosition.ABOVE_HISTORICAL_AVERAGE
    return ValuationRangePosition.AT_HISTORICAL_AVERAGE


def _percentile(current: float, historical: tuple[float, ...]) -> float | None:
    if not historical:
        return None
    at_or_below = sum(1 for value in historical if value <= current)
    return 100.0 * at_or_below / len(historical)


def _median(values: tuple[float, ...]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _trend(observations: tuple[ValuationObservation, ...]) -> ValuationTrend:
    if len(observations) < _MIN_OBSERVATIONS_FOR_TREND:
        return ValuationTrend.INSUFFICIENT_DATA
    values = [obs.value for obs in observations]
    spread = max(values) - min(values)
    if spread == 0:
        return ValuationTrend.STABLE
    midpoint = len(observations) // 2
    earlier_avg = sum(values[:midpoint]) / midpoint
    later_avg = sum(values[midpoint:]) / (len(values) - midpoint)
    relative_change = (later_avg - earlier_avg) / spread
    if relative_change > _TREND_THRESHOLD:
        return ValuationTrend.RISING
    if relative_change < -_TREND_THRESHOLD:
        return ValuationTrend.FALLING
    return ValuationTrend.STABLE


def _stability(observations: tuple[ValuationObservation, ...]) -> ValuationStability:
    if len(observations) < _MIN_OBSERVATIONS_FOR_STABILITY:
        return ValuationStability.INSUFFICIENT_DATA
    values = [obs.value for obs in observations]
    mean = sum(values) / len(values)
    if mean == 0:
        return ValuationStability.INSUFFICIENT_DATA
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    coefficient_of_variation = (variance**0.5) / abs(mean)
    return ValuationStability.VOLATILE if coefficient_of_variation > _VOLATILITY_THRESHOLD else ValuationStability.STABLE


def _significant_deviations(observations: tuple[ValuationObservation, ...]) -> tuple[ValuationDeviation, ...]:
    if len(observations) < _MIN_OBSERVATIONS_FOR_DEVIATIONS:
        return ()
    values = [obs.value for obs in observations]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = variance**0.5
    if std == 0:
        return ()
    return tuple(
        ValuationDeviation(period_end=obs.period_end, value=obs.value, deviation_from_average=obs.value - mean)
        for obs in observations
        if abs(obs.value - mean) > _DEVIATION_THRESHOLD_STD * std
    )


def _data_quality(observation_count: int) -> ValuationDataQuality:
    if observation_count >= _SUFFICIENT_OBSERVATION_COUNT:
        return ValuationDataQuality.SUFFICIENT
    if observation_count >= _LIMITED_OBSERVATION_COUNT:
        return ValuationDataQuality.LIMITED
    return ValuationDataQuality.INSUFFICIENT


def _fcf_yield_metric_history(
    business_facts: tuple[BusinessFact, ...], market_facts: tuple[ValuationFact, ...]
) -> ValuationMetricHistory | None:
    observations, missing_periods = _fcf_yield_observations(business_facts, market_facts)
    if not observations:
        return None

    current = observations[-1]
    historical_values = tuple(obs.value for obs in observations[:-1])

    return ValuationMetricHistory(
        metric=ValuationMetricKind.FCF_YIELD,
        current_value=current.value,
        current_period_end=current.period_end,
        observations=observations,
        historical_average=sum(historical_values) / len(historical_values) if historical_values else None,
        historical_median=_median(historical_values),
        historical_minimum=min(historical_values) if historical_values else None,
        historical_maximum=max(historical_values) if historical_values else None,
        current_percentile=_percentile(current.value, historical_values),
        position_in_range=_position_in_range(current.value, historical_values),
        trend=_trend(observations),
        stability=_stability(observations),
        significant_deviations=_significant_deviations(observations),
        coverage_period_start=observations[0].period_end,
        coverage_period_end=observations[-1].period_end,
        missing_periods=missing_periods,
        data_quality=_data_quality(len(observations)),
    )


def extract_historical_valuation(
    business_facts: tuple[BusinessFact, ...], market_facts: tuple[ValuationFact, ...]
) -> HistoricalValuationKnowledge:
    """Pure, no I/O: organizes already-extracted facts into structured
    knowledge (Phase 3) -- generates no investment conclusion. `metrics`
    is empty when no `ValuationMetricKind` has at least one valid
    observation."""
    metrics: list[ValuationMetricHistory] = []
    fcf_yield = _fcf_yield_metric_history(business_facts, market_facts)
    if fcf_yield is not None:
        metrics.append(fcf_yield)
    return HistoricalValuationKnowledge(metrics=tuple(metrics))

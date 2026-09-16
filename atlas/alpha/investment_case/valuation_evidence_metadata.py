"""Valuation Evidence Metadata -- descriptive, never decisional.

The FCF-yield classification compares today's yield with the lowest and
highest of the company's own prior fiscal years, and nothing else: how
many years those are, how far apart they lie, how far today's yield sits
from the boundary it would cross, whether today's free cash flow looks
like the recent ones, and which share basis the denominator rests on are
all invisible to it (`analysis_engine.valuation.cash_flow`). They are
exactly what a reader needs to judge how much the conclusion is worth.

This module reads the finding Atlas already produced and the financial
statements it already extracted, and describes that evidence -- the same
read-only projection doctrine as `historical_valuation.py`. It forms no
opinion: no "good"/"bad" evidence label, no alternative valuation, no
normalised cash flow, no recomputed classification. Nothing in the
decision path imports it (`atlas.analysis_engine`/`atlas.decision_engine`
never see it); it reaches the Investment Case view only.

**Categories come from the evidence itself, never from a number invented
here.** A history is "at minimum depth" when it has no more prior years
than `cash_flow.MINIMUM_PRIOR_EPOCHS` already demands. Today's free cash
flow is "outside recent" when it falls outside the range of the most
recent prior years -- as many as that same minimum. Capital intensity is
"above the prior range" when it exceeds every prior year's own intensity.
A classification is "closer than the typical move" when its distance to
the boundary is smaller than the median year-to-year move of the very
yields it is compared with. Each says what the evidence shows; none says
whether the valuation is right.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.financial_statement_intelligence import FinancialStatementHistory
from atlas.analysis_engine.valuation.contracts import HistoricalYieldPosition, ValuationStatus
from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation, ValuationFinding, position_of

__all__ = [
    "RangePosition",
    "HistoryEvidence",
    "BoundaryEvidence",
    "CurrentCashFlowEvidence",
    "CapitalIntensityEvidence",
    "DenominatorEvidence",
    "EdgeObservation",
    "RangeEdgeEvidence",
    "ValuationEvidenceMetadata",
    "describe_valuation_evidence",
]


class RangePosition(str, Enum):
    """Where one value sits relative to a set of comparable values."""

    BELOW = "below_range"
    WITHIN = "within_range"
    ABOVE = "above_range"


@dataclass(frozen=True)
class HistoryEvidence:
    """How much history the comparison rests on. `missing_fiscal_years`
    are years between the first and latest prior that formed no epoch (a
    non-positive free cash flow, or one the issuer basis could not
    price); `at_minimum_depth` means the comparison has no more years
    than the method itself demands."""

    valid_prior_count: int
    minimum_prior_count: int
    at_minimum_depth: bool
    span_years: float | None
    first_prior_fiscal_period: str | None
    latest_prior_fiscal_period: str | None
    missing_fiscal_years: tuple[int, ...]
    yield_minimum: float | None = None
    yield_median: float | None = None
    yield_maximum: float | None = None
    #: Population coefficient of variation of the prior yields.
    yield_dispersion: float | None = None
    #: Median relative move between consecutive prior years' yields.
    typical_year_over_year_move: float | None = None


@dataclass(frozen=True)
class BoundaryEvidence:
    """How far today's yield is from the classification it would take
    instead. `closer_than_typical_move` compares that distance with the
    history's own median year-to-year move -- never with a threshold
    chosen here."""

    current_yield: float | None
    nearest_classification: str | None
    boundary_yield: float | None
    distance: float | None
    distance_percent: float | None
    closer_than_typical_move: bool | None


@dataclass(frozen=True)
class CurrentCashFlowEvidence:
    """Today's free cash flow beside the prior years' own -- the exact
    figures the valuation used (attributable to common equity)."""

    current_free_cash_flow: float | None
    prior_year_free_cash_flow: float | None
    recent_median_free_cash_flow: float | None
    historical_median_free_cash_flow: float | None
    recent_years_compared: int
    versus_prior_year: float | None
    versus_recent_median: float | None
    versus_historical_median: float | None
    recent_range: tuple[float, float] | None
    position_versus_recent: RangePosition | None


@dataclass(frozen=True)
class CapitalIntensityEvidence:
    """Capital expenditure beside revenue, today and in the prior years
    -- reported figures only. Every field is `None` when the statements
    do not carry them; nothing is inferred from their absence."""

    current_capital_expenditure: float | None
    current_revenue: float | None
    current_intensity: float | None
    prior_intensity_minimum: float | None
    prior_intensity_median: float | None
    prior_intensity_maximum: float | None
    prior_years_compared: int
    versus_prior_median: float | None
    position_versus_prior_range: RangePosition | None
    current_operating_cash_flow: float | None
    operating_cash_flow_versus_prior_year: float | None
    capital_expenditure_versus_prior_year: float | None


@dataclass(frozen=True)
class DenominatorEvidence:
    """Which issuer denominator each epoch was priced on."""

    current_treatment: str | None
    prior_treatments: tuple[str, ...]
    all_exact: bool


@dataclass(frozen=True)
class EdgeObservation:
    """One fiscal year that owns an end of the observed historical range."""

    fiscal_period: str
    fiscal_year: int
    fcf_yield: float
    denominator_quality: str | None
    #: Fiscal years between this observation and the current one. Measured
    #: from the evidence itself, never from a wall clock, so the description
    #: stays deterministic.
    age_years: int
    #: `False` when more than one prior year shares this exact yield -- an
    #: edge owned by several years is not owned by one.
    uniquely_owned: bool


@dataclass(frozen=True)
class RangeEdgeEvidence:
    """Which fiscal years form the ends of the observed historical range, and
    how much of the rest of the history agrees with today's position inside
    it.

    The classification itself is unchanged and untouched: `fiscal_epoch_v3`
    compares today's yield with the lowest and highest prior, and an edge
    observation is decisive *by design*. What this describes is how lonely
    that edge is -- whether a single year is the only one placing today's
    yield inside the range, or whether many years agree.

    `single_low_edge_dependency` is the one case worth a reader's attention:
    a FAIRLY_VALUED Case whose current yield is below every prior except the
    single year that owns the low edge. It is a fact about corroboration, not
    a judgement about the edge year, which remains valid evidence.
    """

    low_edge: EdgeObservation | None
    high_edge: EdgeObservation | None
    #: The next distinct yield inward from each edge. `None` when the edge is
    #: tied, or when the history has only one distinct yield.
    second_lowest: EdgeObservation | None
    second_highest: EdgeObservation | None

    distance_to_low_edge: float | None
    distance_to_high_edge: float | None
    distance_to_second_lowest: float | None
    distance_to_second_highest: float | None

    #: Primitives, not a score: how many prior years sit at or below, and at
    #: or above, today's yield. A FAIRLY_VALUED Case with exactly one prior
    #: at or below today's yield is corroborated by that one year alone.
    priors_at_or_below_current: int
    priors_at_or_above_current: int

    single_low_edge_dependency: bool
    single_high_edge_dependency: bool

    #: Raw isolation measure, never a label: the step from the edge to the
    #: next distinct yield, beside the median step across this history's own
    #: sorted yields. No threshold is applied here.
    low_edge_gap: float | None
    high_edge_gap: float | None
    median_history_gap: float | None


@dataclass(frozen=True)
class ValuationEvidenceMetadata:
    history: HistoryEvidence
    boundary: BoundaryEvidence
    current_cash_flow: CurrentCashFlowEvidence
    capital_intensity: CapitalIntensityEvidence
    denominator: DenominatorEvidence
    range_edge: RangeEdgeEvidence | None = None


_EXACT_TREATMENT = "issuer_exact"


def _ratio(value: float | None, base: float | None) -> float | None:
    if value is None or base in (None, 0):
        return None
    return value / base


def _position(value: float | None, values: tuple[float, ...]) -> RangePosition | None:
    if value is None or not values:
        return None
    if value < min(values):
        return RangePosition.BELOW
    if value > max(values):
        return RangePosition.ABOVE
    return RangePosition.WITHIN


def _year(fiscal_period: str) -> int:
    return date.fromisoformat(fiscal_period).year


def _history(evidence, priors: tuple[FcfYieldEpochObservation, ...]) -> HistoryEvidence:
    years = [_year(p.fiscal_period) for p in priors]
    yields = [p.fcf_yield for p in priors]
    moves = [abs(b - a) / a for a, b in zip(yields, yields[1:]) if a]
    return HistoryEvidence(
        valid_prior_count=len(priors),
        minimum_prior_count=evidence.minimum_prior_epochs,
        at_minimum_depth=bool(priors) and len(priors) <= evidence.minimum_prior_epochs,
        span_years=evidence.span_years,
        first_prior_fiscal_period=priors[0].fiscal_period if priors else None,
        latest_prior_fiscal_period=priors[-1].fiscal_period if priors else None,
        missing_fiscal_years=tuple(y for y in range(min(years), max(years) + 1) if y not in years) if years else (),
        yield_minimum=min(yields) if yields else None,
        yield_median=statistics.median(yields) if yields else None,
        yield_maximum=max(yields) if yields else None,
        yield_dispersion=(statistics.pstdev(yields) / statistics.mean(yields)) if len(yields) > 1 and statistics.mean(yields) else None,
        typical_year_over_year_move=statistics.median(moves) if moves else None,
    )


def _boundary(status: ValuationStatus, current, priors: tuple[FcfYieldEpochObservation, ...],
              history: HistoryEvidence) -> BoundaryEvidence:
    """The yield at which this Case would classify differently: the prior
    minimum for a yield below it or inside the range from below, the prior
    maximum for one above it or inside from above. Whichever of the two is
    nearer is the one reported."""
    empty = BoundaryEvidence(None, None, None, None, None, None)
    if current is None or not priors or history.yield_minimum is None:
        return empty
    low, high = history.yield_minimum, history.yield_maximum
    value = current.fcf_yield
    if status is ValuationStatus.EXPENSIVE:
        nearest, boundary = ValuationStatus.FAIRLY_VALUED, low
    elif status is ValuationStatus.UNDERVALUED:
        nearest, boundary = ValuationStatus.FAIRLY_VALUED, high
    elif status is ValuationStatus.FAIRLY_VALUED:
        below, above = abs(value - low), abs(high - value)
        nearest, boundary = ((ValuationStatus.EXPENSIVE, low) if below <= above
                             else (ValuationStatus.UNDERVALUED, high))
    else:
        return empty
    distance = abs(value - boundary)
    percent = _ratio(distance, boundary)
    typical = history.typical_year_over_year_move
    return BoundaryEvidence(
        current_yield=value, nearest_classification=nearest.value, boundary_yield=boundary, distance=distance,
        distance_percent=percent,
        closer_than_typical_move=None if percent is None or typical is None else percent < typical,
    )


def _current_cash_flow(current, priors: tuple[FcfYieldEpochObservation, ...], recent_years: int) -> CurrentCashFlowEvidence:
    values = [p.free_cash_flow for p in priors]
    recent = values[-recent_years:] if values else []
    value = current.free_cash_flow if current is not None else None
    return CurrentCashFlowEvidence(
        current_free_cash_flow=value,
        prior_year_free_cash_flow=values[-1] if values else None,
        recent_median_free_cash_flow=statistics.median(recent) if recent else None,
        historical_median_free_cash_flow=statistics.median(values) if values else None,
        recent_years_compared=len(recent),
        versus_prior_year=_ratio(value, values[-1] if values else None),
        versus_recent_median=_ratio(value, statistics.median(recent) if recent else None),
        versus_historical_median=_ratio(value, statistics.median(values) if values else None),
        recent_range=(min(recent), max(recent)) if recent else None,
        position_versus_recent=_position(value, tuple(recent)),
    )


def _capital_intensity(current, priors: tuple[FcfYieldEpochObservation, ...],
                       statements: FinancialStatementHistory | None) -> CapitalIntensityEvidence:
    empty = CapitalIntensityEvidence(None, None, None, None, None, None, 0, None, None, None, None, None)
    if statements is None or current is None:
        return empty
    revenue = {p.period_end: p.revenue for p in statements.income_statements}
    cash_flow = {p.period_end: p for p in statements.cash_flow_statements}

    def intensity(fiscal_period: str) -> float | None:
        end = date.fromisoformat(fiscal_period)
        period = cash_flow.get(end)
        return _ratio(period.capital_expenditure, revenue.get(end)) if period is not None else None

    current_end = date.fromisoformat(current.fiscal_period)
    current_period = cash_flow.get(current_end)
    prior_intensities = tuple(v for v in (intensity(p.fiscal_period) for p in priors) if v is not None)
    prior_period = cash_flow.get(date.fromisoformat(priors[-1].fiscal_period)) if priors else None
    now = intensity(current.fiscal_period)
    return CapitalIntensityEvidence(
        current_capital_expenditure=current_period.capital_expenditure if current_period else None,
        current_revenue=revenue.get(current_end),
        current_intensity=now,
        prior_intensity_minimum=min(prior_intensities) if prior_intensities else None,
        prior_intensity_median=statistics.median(prior_intensities) if prior_intensities else None,
        prior_intensity_maximum=max(prior_intensities) if prior_intensities else None,
        prior_years_compared=len(prior_intensities),
        versus_prior_median=_ratio(now, statistics.median(prior_intensities) if prior_intensities else None),
        position_versus_prior_range=_position(now, prior_intensities),
        current_operating_cash_flow=current_period.operating_cash_flow if current_period else None,
        operating_cash_flow_versus_prior_year=_ratio(
            current_period.operating_cash_flow if current_period else None,
            prior_period.operating_cash_flow if prior_period else None),
        capital_expenditure_versus_prior_year=_ratio(
            current_period.capital_expenditure if current_period else None,
            prior_period.capital_expenditure if prior_period else None),
    )


def _edge_observation(epoch: FcfYieldEpochObservation, current_year: int,
                      priors: tuple[FcfYieldEpochObservation, ...]) -> EdgeObservation:
    return EdgeObservation(
        fiscal_period=epoch.fiscal_period,
        fiscal_year=_year(epoch.fiscal_period),
        fcf_yield=epoch.fcf_yield,
        denominator_quality=epoch.denominator_quality,
        age_years=current_year - _year(epoch.fiscal_period),
        uniquely_owned=sum(1 for p in priors if p.fcf_yield == epoch.fcf_yield) == 1,
    )


def _range_edges(status: ValuationStatus, current, priors: tuple[FcfYieldEpochObservation, ...]
                 ) -> RangeEdgeEvidence | None:
    """Who owns each end of the observed range, and how much of the history
    corroborates today's position inside it.

    Derived from exactly the epochs `fiscal_epoch_v3` accepted -- the same
    tuple the classification itself compared -- so the description can never
    describe a valuation Atlas did not make.

    **Ties.** An edge shared by several years is owned by none of them: the
    "second" yield is the next *distinct* one inward, and a tied edge can
    never establish single-edge dependence, because removing one of the tied
    years leaves the other holding the same edge.
    """
    if current is None or not priors:
        return None
    ordered = sorted(priors, key=lambda p: (p.fcf_yield, p.fiscal_period))
    low, high = ordered[0], ordered[-1]
    current_year = _year(current.fiscal_period)
    value = current.fcf_yield

    second_low = next((p for p in ordered if p.fcf_yield > low.fcf_yield), None)
    second_high = next((p for p in reversed(ordered) if p.fcf_yield < high.fcf_yield), None)

    def dependency(edge: FcfYieldEpochObservation, second, target: HistoricalYieldPosition) -> bool:
        """The edge is load-bearing when, and only when, removing that one
        uniquely owned year would move today's yield outside the range. The
        same `position_of` the engine uses decides it -- never a second rule."""
        if status is not ValuationStatus.FAIRLY_VALUED or second is None:
            return False
        if sum(1 for p in priors if p.fcf_yield == edge.fcf_yield) != 1:
            return False
        remaining = tuple(p.fcf_yield for p in priors if p is not edge)
        if not remaining:
            return False
        return position_of(value, remaining) is target

    yields = sorted(p.fcf_yield for p in priors)
    gaps = [b - a for a, b in zip(yields, yields[1:])]
    return RangeEdgeEvidence(
        low_edge=_edge_observation(low, current_year, priors),
        high_edge=_edge_observation(high, current_year, priors),
        second_lowest=_edge_observation(second_low, current_year, priors) if second_low else None,
        second_highest=_edge_observation(second_high, current_year, priors) if second_high else None,
        distance_to_low_edge=_ratio(value - low.fcf_yield, low.fcf_yield),
        distance_to_high_edge=_ratio(value - high.fcf_yield, high.fcf_yield),
        distance_to_second_lowest=(_ratio(value - second_low.fcf_yield, second_low.fcf_yield)
                                   if second_low else None),
        distance_to_second_highest=(_ratio(value - second_high.fcf_yield, second_high.fcf_yield)
                                    if second_high else None),
        priors_at_or_below_current=sum(1 for p in priors if p.fcf_yield <= value),
        priors_at_or_above_current=sum(1 for p in priors if p.fcf_yield >= value),
        single_low_edge_dependency=dependency(low, second_low, HistoricalYieldPosition.BELOW_ALL_PRIOR),
        single_high_edge_dependency=dependency(high, second_high, HistoricalYieldPosition.ABOVE_ALL_PRIOR),
        low_edge_gap=(second_low.fcf_yield - low.fcf_yield) if second_low else None,
        high_edge_gap=(high.fcf_yield - second_high.fcf_yield) if second_high else None,
        median_history_gap=statistics.median(gaps) if gaps else None,
    )


def describe_valuation_evidence(
    finding: ValuationFinding, statements: FinancialStatementHistory | None = None
) -> ValuationEvidenceMetadata | None:
    """The FCF-yield finding's own evidence, described. `None` when the
    finding formed no evidence at all. Pure: identical inputs always
    produce a deeply equal result, and nothing here is read by any
    decision."""
    evidence = finding.fcf_yield_evidence
    if evidence is None:
        return None
    priors = tuple(evidence.prior_epochs)
    current = evidence.current
    history = _history(evidence, priors)
    return ValuationEvidenceMetadata(
        history=history,
        boundary=_boundary(finding.status, current, priors, history),
        current_cash_flow=_current_cash_flow(current, priors, evidence.minimum_prior_epochs),
        capital_intensity=_capital_intensity(current, priors, statements),
        denominator=DenominatorEvidence(
            current_treatment=current.denominator_quality if current is not None else None,
            prior_treatments=tuple(sorted({p.denominator_quality for p in priors if p.denominator_quality})),
            all_exact=bool(current is not None and current.denominator_quality == _EXACT_TREATMENT
                           and all(p.denominator_quality == _EXACT_TREATMENT for p in priors)),
        ),
        range_edge=_range_edges(finding.status, current, priors),
    )

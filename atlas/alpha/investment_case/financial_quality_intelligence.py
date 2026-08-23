"""Financial Quality Knowledge Model + Cash Conversion + Working Capital
+ Profitability Durability + Capital Efficiency + Financial Durability
(Capability Expansion Sprint 5: Financial Quality Intelligence, Phases
1 + 3 through 8).

**This module builds directly on top of `financial_statement_
intelligence.py` (Sprint 3) -- deliberately, per this sprint's own
Long-Term Vision ("Financial Quality Intelligence builds directly on
Financial Statement Intelligence"), not a fifth independent re-read of
raw `BusinessRecord`s.** It takes an already-built `FinancialStatement
History` and reuses that module's own public `compute_trend_
intelligence`/`compute_cash_flow_consistency`/`TrendDirection` directly
-- real reuse, not a parallel computation -- for every dimension Sprint
3 already covers (margin trend, working-capital trend, cash-flow
consistency, capital intensity). This module never imports Sprint 3's
private helpers and never modifies that file at all, honoring this
sprint's own "must not redesign Financial Statement Intelligence"
non-goal while still building on its output.

**Phase 2 audit finding**: `income_statements`/`balance_sheets`/`cash_
flow_statements` on a `FinancialStatementHistory` are built from the
same, single, sorted loop in `extract_financial_statement_history` --
same length, same order, the same index in every tuple is always the
same fiscal period. This module relies on that positional alignment
(confirmed by reading that function's own source) rather than
re-matching by `period_end` a second time.

**"Earnings Quality" (Phase 3) and "Cash Conversion Quality" (Phase 4)
are modeled as one dimension, not two** -- the brief's own Phase 1
knowledge model lists "Earnings-to-cash relationship" under both
headings; they are the same underlying analysis (does reported profit
convert into cash) under two names, and building two near-identical
dataclasses would be exactly the redundant computation this sprint's
own engineering discipline asks to avoid.

**ROIC is deliberately not implemented.** A textbook ROIC needs NOPAT
(tax-adjusted operating income); this codebase has no income-tax-rate
or income-tax-expense input anywhere, and inventing one -- or silently
mislabeling pre-tax operating income as post-tax NOPAT -- is exactly
the "fabricate ... unsupported accounting adjustments" this sprint's
own non-goals forbid. `CapitalEfficiencyKnowledge.return_on_invested_
capital_unavailable_reason` names this honestly as structured
knowledge (Phase 7's own "expose the limitation" instruction) rather
than silently omitting the field. Return on Assets, Return on Equity,
and Asset Turnover are implemented instead -- every input (`net_income`,
`equity`, `total_assets`, `revenue`) is a real, already-available
Sprint 3 figure, and each ratio's own definition needs no invented
adjustment.

**Every threshold below is a disclosed, textbook-standard convention
(90%/50% cash conversion bands, a 15% coefficient-of-variation
stability cutoff, a 1.5-standard-deviation reversal threshold) -- never
a composite or weighted score.** Every dimension stays independently
inspectable per Phase 1's own instruction; `FinancialDurabilityKnowledge
.findings` (Phase 8) is a tuple of named, closed-vocabulary findings
assembled from the already-computed dimensions below, never a single
opaque rating.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.financial_statement_intelligence import (
    ConsistencyLevel,
    FinancialStatementHistory,
    FinancialTrendMetric,
    TrendDirection,
    compute_cash_flow_consistency,
    compute_trend_intelligence,
)

__all__ = [
    "TrendDirection",
    "StabilityLevel",
    "ConversionPattern",
    "CashConversionObservation",
    "CashConversionKnowledge",
    "CashFlowDirection",
    "WorkingCapitalObservation",
    "WorkingCapitalIntelligence",
    "MarginKind",
    "MarginReversal",
    "MarginDurability",
    "ProfitabilityDurability",
    "UnsupportedMeasureReason",
    "CapitalEfficiencyObservation",
    "CapitalEfficiencyKnowledge",
    "DurabilityFinding",
    "FinancialDurabilityKnowledge",
    "FinancialQualityKnowledge",
    "extract_financial_quality",
]

_MIN_PERIODS_FOR_TREND = 3
_MIN_PERIODS_FOR_PATTERN = 2
_MIN_PERIODS_FOR_STABILITY = 2
_MIN_PERIODS_FOR_REVERSALS = 3
_TREND_THRESHOLD = 0.1
_VOLATILITY_THRESHOLD = 0.15
_MODERATE_VOLATILITY_THRESHOLD = 0.30
_DEVIATION_THRESHOLD_STD = 1.5


def _margin(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _trend_direction(values: tuple[float, ...]) -> TrendDirection:
    """Duplicated (not imported) from `financial_statement_intelligence
    ._trend_direction` -- that function is private, and importing a
    protected sibling's own private helper would be exactly the kind
    of coupling this sprint's own non-goal list exists to prevent. See
    this module's own docstring for what *is* reused from that module
    (its public functions and the shared `TrendDirection` vocabulary)."""
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


class StabilityLevel(str, Enum):
    """Coefficient of variation across known observations, bucketed --
    the same disclosed-threshold discipline `historical_valuation
    .ValuationStability` already establishes. Answers both "how stable"
    and "how volatile" (Phase 6's own two framings of the identical
    axis) with one field."""

    STABLE = "stable"
    MODERATE = "moderate"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


def _stability(values: tuple[float, ...]) -> StabilityLevel:
    if len(values) < _MIN_PERIODS_FOR_STABILITY:
        return StabilityLevel.INSUFFICIENT_DATA
    mean = sum(values) / len(values)
    if mean == 0:
        return StabilityLevel.INSUFFICIENT_DATA
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    coefficient_of_variation = (variance**0.5) / abs(mean)
    if coefficient_of_variation <= _VOLATILITY_THRESHOLD:
        return StabilityLevel.STABLE
    if coefficient_of_variation <= _MODERATE_VOLATILITY_THRESHOLD:
        return StabilityLevel.MODERATE
    return StabilityLevel.VOLATILE


def _trend_from_metric(metric: FinancialTrendMetric, history: FinancialStatementHistory) -> TrendDirection:
    """Reuses `financial_statement_intelligence.compute_trend_
    intelligence` verbatim -- never a second computation of a trend
    that module already produces."""
    return next(o.direction for o in compute_trend_intelligence(history) if o.metric is metric)


# -- Phase 3 + 4: Earnings Quality / Cash Conversion Intelligence -------


class ConversionPattern(str, Enum):
    """The average ratio across known periods, bucketed against
    disclosed, textbook-standard bands -- 90%+ average cash conversion
    is commonly treated as strong earnings quality; below 50% is
    commonly flagged as a real divergence. Never a fabricated cutoff."""

    STRONGLY_SUPPORTED = "strongly_supported"
    MODERATELY_SUPPORTED = "moderately_supported"
    PERSISTENTLY_DIVERGENT = "persistently_divergent"
    INSUFFICIENT_HISTORY = "insufficient_history"


_STRONG_CONVERSION_RATIO = 0.9
_MODERATE_CONVERSION_RATIO = 0.5


def _conversion_pattern(values: tuple[float, ...]) -> ConversionPattern:
    if len(values) < _MIN_PERIODS_FOR_PATTERN:
        return ConversionPattern.INSUFFICIENT_HISTORY
    average = sum(values) / len(values)
    if average >= _STRONG_CONVERSION_RATIO:
        return ConversionPattern.STRONGLY_SUPPORTED
    if average >= _MODERATE_CONVERSION_RATIO:
        return ConversionPattern.MODERATELY_SUPPORTED
    return ConversionPattern.PERSISTENTLY_DIVERGENT


@dataclass(frozen=True)
class CashConversionObservation:
    period_end: date
    ocf_to_net_income: float | None
    fcf_to_net_income: float | None
    fcf_to_operating_income: float | None
    source_reference: str | None
    """(Cleanup Sprint 1) The cash-flow-statement period's own real
    `source_reference` (Sprint 3) -- these ratios' own numerators
    (`operating_cash_flow`/`free_cash_flow`) both come from that
    statement. Never fabricated; `None` only when the underlying period
    itself has no source reference."""


@dataclass(frozen=True)
class CashConversionKnowledge:
    observations: tuple[CashConversionObservation, ...]
    """Chronological, oldest first. Empty when no period has both a
    known cash-flow figure and a known earnings figure to compare."""
    ocf_conversion_pattern: ConversionPattern
    ocf_conversion_trend: TrendDirection
    ocf_conversion_stability: StabilityLevel
    fcf_conversion_pattern: ConversionPattern
    fcf_conversion_trend: TrendDirection
    fcf_conversion_stability: StabilityLevel


def _cash_conversion(history: FinancialStatementHistory) -> CashConversionKnowledge:
    observations: list[CashConversionObservation] = []
    for income, cash_flow in zip(history.income_statements, history.cash_flow_statements):
        observations.append(
            CashConversionObservation(
                period_end=income.period_end,
                ocf_to_net_income=_margin(cash_flow.operating_cash_flow, income.net_income),
                fcf_to_net_income=_margin(cash_flow.free_cash_flow, income.net_income),
                fcf_to_operating_income=_margin(cash_flow.free_cash_flow, income.operating_income),
                source_reference=cash_flow.source_reference,
            )
        )

    ocf_ratios = tuple(o.ocf_to_net_income for o in observations if o.ocf_to_net_income is not None)
    fcf_ratios = tuple(o.fcf_to_net_income for o in observations if o.fcf_to_net_income is not None)

    return CashConversionKnowledge(
        observations=tuple(observations),
        ocf_conversion_pattern=_conversion_pattern(ocf_ratios),
        ocf_conversion_trend=_trend_direction(ocf_ratios),
        ocf_conversion_stability=_stability(ocf_ratios),
        fcf_conversion_pattern=_conversion_pattern(fcf_ratios),
        fcf_conversion_trend=_trend_direction(fcf_ratios),
        fcf_conversion_stability=_stability(fcf_ratios),
    )


# -- Phase 5: Working Capital Intelligence -------------------------------


class CashFlowDirection(str, Enum):
    CASH_ABSORBED = "cash_absorbed"
    """Working capital increased period-over-period -- a use of cash."""
    CASH_RELEASED = "cash_released"
    """Working capital decreased period-over-period -- a source of cash."""
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class WorkingCapitalObservation:
    period_end: date
    working_capital: float | None
    working_capital_to_revenue: float | None
    change_from_prior_period: float | None
    source_reference: str | None
    """(Cleanup Sprint 1) The balance-sheet period's own real
    `source_reference` (Sprint 3) -- working capital is itself a
    balance-sheet-derived figure. `None` only when the underlying
    period has no source reference."""


@dataclass(frozen=True)
class WorkingCapitalIntelligence:
    observations: tuple[WorkingCapitalObservation, ...]
    trend: TrendDirection
    """Reused verbatim from `financial_statement_intelligence
    .compute_trend_intelligence`'s own `WORKING_CAPITAL` metric."""
    most_recent_direction: CashFlowDirection
    stability: StabilityLevel


def _working_capital(history: FinancialStatementHistory) -> WorkingCapitalIntelligence:
    observations: list[WorkingCapitalObservation] = []
    previous_wc: float | None = None
    for balance_sheet, income in zip(history.balance_sheets, history.income_statements):
        change = (
            balance_sheet.working_capital - previous_wc
            if balance_sheet.working_capital is not None and previous_wc is not None
            else None
        )
        observations.append(
            WorkingCapitalObservation(
                period_end=balance_sheet.period_end,
                working_capital=balance_sheet.working_capital,
                working_capital_to_revenue=_margin(balance_sheet.working_capital, income.revenue),
                change_from_prior_period=change,
                source_reference=balance_sheet.source_reference,
            )
        )
        if balance_sheet.working_capital is not None:
            previous_wc = balance_sheet.working_capital

    known_changes = tuple(o.change_from_prior_period for o in observations if o.change_from_prior_period is not None)
    most_recent_direction = CashFlowDirection.INSUFFICIENT_DATA
    if known_changes:
        latest_change = known_changes[-1]
        if latest_change > 0:
            most_recent_direction = CashFlowDirection.CASH_ABSORBED
        elif latest_change < 0:
            most_recent_direction = CashFlowDirection.CASH_RELEASED
        else:
            most_recent_direction = CashFlowDirection.STABLE

    known_levels = tuple(o.working_capital for o in observations if o.working_capital is not None)

    return WorkingCapitalIntelligence(
        observations=tuple(observations),
        trend=_trend_from_metric(FinancialTrendMetric.WORKING_CAPITAL, history),
        most_recent_direction=most_recent_direction,
        stability=_stability(known_levels),
    )


# -- Phase 6: Profitability Durability -----------------------------------


class MarginKind(str, Enum):
    GROSS = "gross"
    OPERATING = "operating"
    NET = "net"


@dataclass(frozen=True)
class MarginReversal:
    period_end: date
    margin_value: float
    deviation_from_average: float
    source_reference: str | None
    """(Cleanup Sprint 1) The income-statement period's own real
    `source_reference` (Sprint 3) this margin figure was reported in.
    `None` only when the underlying period has no source reference."""


@dataclass(frozen=True)
class MarginDurability:
    margin: MarginKind
    current_level: float | None
    trend: TrendDirection
    stability: StabilityLevel
    reversals: tuple[MarginReversal, ...]
    periods_considered: int


def _reversals(
    period_ends: tuple[date, ...], values: tuple[float, ...], source_references: tuple[str | None, ...],
) -> tuple[MarginReversal, ...]:
    if len(values) < _MIN_PERIODS_FOR_REVERSALS:
        return ()
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = variance**0.5
    if std == 0:
        return ()
    return tuple(
        MarginReversal(
            period_end=period_end, margin_value=value, deviation_from_average=value - mean,
            source_reference=source_reference,
        )
        for period_end, value, source_reference in zip(period_ends, values, source_references)
        if abs(value - mean) > _DEVIATION_THRESHOLD_STD * std
    )


def _margin_durability(
    margin: MarginKind, metric: FinancialTrendMetric, history: FinancialStatementHistory, attr: str
) -> MarginDurability:
    known = [
        (p.period_end, getattr(p, attr), p.source_reference)
        for p in history.income_statements if getattr(p, attr) is not None
    ]
    period_ends = tuple(period_end for period_end, _, _ in known)
    values = tuple(value for _, value, _ in known)
    source_references = tuple(source_reference for _, _, source_reference in known)
    return MarginDurability(
        margin=margin,
        current_level=values[-1] if values else None,
        trend=_trend_from_metric(metric, history),
        stability=_stability(values),
        reversals=_reversals(period_ends, values, source_references),
        periods_considered=len(values),
    )


@dataclass(frozen=True)
class ProfitabilityDurability:
    gross_margin: MarginDurability
    operating_margin: MarginDurability
    net_margin: MarginDurability


def _profitability_durability(history: FinancialStatementHistory) -> ProfitabilityDurability:
    return ProfitabilityDurability(
        gross_margin=_margin_durability(MarginKind.GROSS, FinancialTrendMetric.GROSS_MARGIN, history, "gross_margin"),
        operating_margin=_margin_durability(
            MarginKind.OPERATING, FinancialTrendMetric.OPERATING_MARGIN, history, "operating_margin"
        ),
        net_margin=_margin_durability(MarginKind.NET, FinancialTrendMetric.NET_MARGIN, history, "net_margin"),
    )


# -- Phase 7: Capital Efficiency Knowledge -------------------------------


class UnsupportedMeasureReason(str, Enum):
    MISSING_TAX_RATE_INPUT = "missing_tax_rate_input"


@dataclass(frozen=True)
class CapitalEfficiencyObservation:
    period_end: date
    return_on_assets: float | None
    return_on_equity: float | None
    asset_turnover: float | None
    source_reference: str | None
    """(Cleanup Sprint 1) The income-statement period's own real
    `source_reference` (Sprint 3) -- `net_income`/`revenue`, the
    numerator for all three ratios, both come from that statement.
    `None` only when the underlying period has no source reference."""


@dataclass(frozen=True)
class CapitalEfficiencyKnowledge:
    observations: tuple[CapitalEfficiencyObservation, ...]
    return_on_assets_trend: TrendDirection
    return_on_equity_trend: TrendDirection
    asset_turnover_trend: TrendDirection
    capital_intensity_trend: TrendDirection
    """Reused verbatim from `financial_statement_intelligence
    .compute_trend_intelligence`'s own `CAPITAL_INTENSITY` metric."""
    return_on_invested_capital_unavailable_reason: UnsupportedMeasureReason
    """Always `MISSING_TAX_RATE_INPUT` in this build -- see this
    module's own docstring for why ROIC is not implemented."""


def _capital_efficiency(history: FinancialStatementHistory) -> CapitalEfficiencyKnowledge:
    observations: list[CapitalEfficiencyObservation] = []
    for income, balance_sheet in zip(history.income_statements, history.balance_sheets):
        observations.append(
            CapitalEfficiencyObservation(
                period_end=income.period_end,
                return_on_assets=_margin(income.net_income, balance_sheet.total_assets),
                return_on_equity=_margin(income.net_income, balance_sheet.equity),
                asset_turnover=_margin(income.revenue, balance_sheet.total_assets),
                source_reference=income.source_reference,
            )
        )

    roa = tuple(o.return_on_assets for o in observations if o.return_on_assets is not None)
    roe = tuple(o.return_on_equity for o in observations if o.return_on_equity is not None)
    turnover = tuple(o.asset_turnover for o in observations if o.asset_turnover is not None)

    return CapitalEfficiencyKnowledge(
        observations=tuple(observations),
        return_on_assets_trend=_trend_direction(roa),
        return_on_equity_trend=_trend_direction(roe),
        asset_turnover_trend=_trend_direction(turnover),
        capital_intensity_trend=_trend_from_metric(FinancialTrendMetric.CAPITAL_INTENSITY, history),
        return_on_invested_capital_unavailable_reason=UnsupportedMeasureReason.MISSING_TAX_RATE_INPUT,
    )


# -- Phase 8: Financial Durability Knowledge -----------------------------


class DurabilityFinding(str, Enum):
    """Closed, presence-only findings -- assembled from the already-
    computed dimensions above, never a new computation and never
    combined into a score (Phase 8's own "not a score" instruction)."""

    CASH_GENERATION_CONSISTENTLY_POSITIVE = "cash_generation_consistently_positive"
    CASH_GENERATION_INCONSISTENT = "cash_generation_inconsistent"
    PROFITABILITY_HIGHLY_STABLE = "profitability_highly_stable"
    PROFITABILITY_VOLATILE = "profitability_volatile"
    CASH_CONVERSION_DETERIORATING = "cash_conversion_deteriorating"
    CASH_CONVERSION_IMPROVING = "cash_conversion_improving"
    CAPITAL_EFFICIENCY_STRENGTHENING = "capital_efficiency_strengthening"
    CAPITAL_EFFICIENCY_WEAKENING = "capital_efficiency_weakening"
    HISTORY_INSUFFICIENT = "history_insufficient"


@dataclass(frozen=True)
class FinancialDurabilityKnowledge:
    findings: tuple[DurabilityFinding, ...]


def _financial_durability(
    history: FinancialStatementHistory,
    cash_conversion: CashConversionKnowledge,
    profitability: ProfitabilityDurability,
    capital_efficiency: CapitalEfficiencyKnowledge,
) -> FinancialDurabilityKnowledge:
    findings: list[DurabilityFinding] = []

    consistency = compute_cash_flow_consistency(history)
    if consistency is ConsistencyLevel.CONSISTENT:
        findings.append(DurabilityFinding.CASH_GENERATION_CONSISTENTLY_POSITIVE)
    elif consistency is ConsistencyLevel.INCONSISTENT:
        findings.append(DurabilityFinding.CASH_GENERATION_INCONSISTENT)

    if profitability.net_margin.stability is StabilityLevel.STABLE:
        findings.append(DurabilityFinding.PROFITABILITY_HIGHLY_STABLE)
    elif profitability.net_margin.stability is StabilityLevel.VOLATILE:
        findings.append(DurabilityFinding.PROFITABILITY_VOLATILE)

    if cash_conversion.ocf_conversion_trend is TrendDirection.FALLING:
        findings.append(DurabilityFinding.CASH_CONVERSION_DETERIORATING)
    elif cash_conversion.ocf_conversion_trend is TrendDirection.RISING:
        findings.append(DurabilityFinding.CASH_CONVERSION_IMPROVING)

    if capital_efficiency.return_on_assets_trend is TrendDirection.RISING:
        findings.append(DurabilityFinding.CAPITAL_EFFICIENCY_STRENGTHENING)
    elif capital_efficiency.return_on_assets_trend is TrendDirection.FALLING:
        findings.append(DurabilityFinding.CAPITAL_EFFICIENCY_WEAKENING)

    if not findings:
        findings.append(DurabilityFinding.HISTORY_INSUFFICIENT)

    return FinancialDurabilityKnowledge(findings=tuple(findings))


# -- Composition -----------------------------------------------------------


@dataclass(frozen=True)
class FinancialQualityKnowledge:
    cash_conversion: CashConversionKnowledge
    working_capital: WorkingCapitalIntelligence
    profitability_durability: ProfitabilityDurability
    capital_efficiency: CapitalEfficiencyKnowledge
    financial_durability: FinancialDurabilityKnowledge


def extract_financial_quality(history: FinancialStatementHistory) -> FinancialQualityKnowledge:
    """Pure, no I/O. `history.income_statements == ()` yields every
    dimension at its own honest `INSUFFICIENT_DATA`/`INSUFFICIENT_
    HISTORY` default -- never a fabricated assessment."""
    cash_conversion = _cash_conversion(history)
    profitability = _profitability_durability(history)
    capital_efficiency = _capital_efficiency(history)
    return FinancialQualityKnowledge(
        cash_conversion=cash_conversion,
        working_capital=_working_capital(history),
        profitability_durability=profitability,
        capital_efficiency=capital_efficiency,
        financial_durability=_financial_durability(history, cash_conversion, profitability, capital_efficiency),
    )

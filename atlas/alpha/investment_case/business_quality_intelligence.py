"""Business Quality Knowledge Model + Business Stability + Business
Durability + Business Efficiency + Business Consistency + Business
Evolution (Capability Expansion Sprint 7: Business Quality Intelligence,
Phases 1, 3 through 6, 8).

**A pure, higher-order aggregation over four already-built sibling
capabilities' own outputs -- `FinancialHealthKnowledge` (Sprint 3),
`ManagementCapitalAllocationKnowledge` (Sprint 4), `FinancialQuality
Knowledge` (Sprint 5), `GrowthKnowledge` (Sprint 6).** This module
computes zero new statistics from raw `BusinessRecord`s or raw period
values -- every field below is either a direct pass-through of an
already-computed sibling value, or a closed-vocabulary grouping of
several already-computed sibling values (e.g. "of the six tracked
growth metrics, which ones show consistent growth" -- a grouping
operation over values Sprint 6 already produced, never a new
computation over raw revenue/earnings/cash-flow figures). This is the
same "second-order transformation" discipline Sprint 5 established for
building on Sprint 3, extended one layer further: Business Quality is a
*third*-order transformation, reusing Sprints 3/4/5/6's own public
outputs directly rather than re-reading `BusinessRecord`s a seventh
time.

**Phase 2 audit finding**: Historical Valuation Intelligence (Sprint 1)
and Earnings Call Intelligence (Sprint 2) were both read and
deliberately NOT reused as inputs here. Historical Valuation describes
whether the market price is cheap or expensive relative to its own
history -- a question about the stock, not the business; blending it in
would silently conflate "cheap" with "good," exactly the kind of
unsupported inference this sprint's own non-goals forbid ("never infer
competitive advantages without evidence"). Earnings Call Intelligence
captures qualitative management commentary (what management *said*),
not quantified financial evidence -- it sits outside this sprint's own
"quality/durability/economic characteristics" scope, and folding
narrative commentary into a business-quality reading would require the
kind of editorial interpretation this sprint's own non-goals forbid
("no LLM-generated interpretation").

**Every combining rule below is a closed grouping or worst-case/any-
signal rule over already-bucketed categorical values (e.g. "any
`FALLING` signal alongside any `RISING` signal is `MIXED`") -- never a
weighted score, a majority vote, or an invented numeric threshold.**
Every dimension stays independently inspectable per Phase 1's own
instruction, and every sibling capability's own honest "insufficient
data"/"insufficient history" default propagates through unchanged when
that sibling itself had no evidence -- never silently overridden or
upgraded here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.capital_allocation_intelligence import (
    BuybackConsistency,
    CapitalAllocationHistory,
    DebtDiscipline,
    ManagementCapitalAllocationKnowledge,
    assess_management_capital_allocation,
)
from atlas.alpha.investment_case.financial_quality_intelligence import (
    CapitalEfficiencyKnowledge,
    FinancialDurabilityKnowledge,
    FinancialQualityKnowledge,
    MarginKind,
    ProfitabilityDurability,
    StabilityLevel,
    TrendDirection,
)
from atlas.alpha.investment_case.financial_statement_intelligence import (
    ConsistencyLevel,
    FinancialStatementHistory,
    assess_financial_health,
    compute_cash_flow_consistency,
)
from atlas.alpha.investment_case.growth_intelligence import (
    GrowthConsistency,
    GrowthKnowledge,
    GrowthMetric,
    RecoveryStatus,
)

__all__ = [
    "StabilityLevel",
    "TrendDirection",
    "ConsistencyLevel",
    "BusinessStability",
    "GrowthDurabilitySummary",
    "BusinessDurability",
    "BusinessEfficiency",
    "HistoricalDisruption",
    "BusinessConsistency",
    "EvolutionDirection",
    "BusinessEvolution",
    "BusinessQualityFindingKind",
    "BusinessQualityFinding",
    "BusinessQualityKnowledge",
    "extract_business_quality",
]

_MIN_DURABLE_GROWTH_METRICS = 3


# -- Phase 3: Business Stability -----------------------------------------

_STABILITY_SEVERITY = {StabilityLevel.STABLE: 0, StabilityLevel.MODERATE: 1, StabilityLevel.VOLATILE: 2}


def _aggregate_stability(levels: tuple[StabilityLevel, ...]) -> StabilityLevel:
    """Worst-case of several already-computed `StabilityLevel` values --
    a grouping rule, not a new computation over raw margin figures."""
    known = tuple(level for level in levels if level is not StabilityLevel.INSUFFICIENT_DATA)
    if not known:
        return StabilityLevel.INSUFFICIENT_DATA
    return max(known, key=lambda level: _STABILITY_SEVERITY[level])


@dataclass(frozen=True)
class BusinessStability:
    """Phase 3. Every field is a direct reuse, or a worst-case
    aggregation of several already-computed sibling values -- no new
    statistic is computed here."""

    profitability_stability: StabilityLevel
    """Worst case of the three already-computed `ProfitabilityDurability`
    margin stabilities (gross/operating/net) -- Sprint 5's own
    `_stability` output, never recomputed here."""
    revenue_stability: GrowthConsistency
    """Direct reuse of `GrowthKnowledge.revenue.durability.consistency`
    (Sprint 6). `CONSISTENT_GROWTH` and `CONSISTENT_DECLINE` both
    describe a stable, predictable revenue trajectory; `MIXED` describes
    an unstable one."""
    cash_generation_stability: ConsistencyLevel
    """Direct reuse of `financial_statement_intelligence.compute_cash_
    flow_consistency` (Sprint 3) -- was Operating Cash Flow positive in
    every known period."""
    capital_allocation_stability: BuybackConsistency
    """Direct reuse of `ManagementCapitalAllocationKnowledge.capital_
    allocation_consistency` (Sprint 4)."""


# -- Phase 4: Business Durability ----------------------------------------


@dataclass(frozen=True)
class GrowthDurabilitySummary:
    """Phase 4's own "resilience across multiple periods" and "recovery
    following difficult periods" -- a pure grouping of the six already-
    computed per-metric `GrowthDurability` objects (Sprint 6), never a
    new computation over raw revenue/earnings/cash-flow values."""

    metrics_with_consistent_growth: tuple[GrowthMetric, ...]
    metrics_with_consistent_decline: tuple[GrowthMetric, ...]
    metrics_recovered_from_decline: tuple[GrowthMetric, ...]


def _growth_durability_summary(growth: GrowthKnowledge) -> GrowthDurabilitySummary:
    per_metric = (
        (GrowthMetric.REVENUE, growth.revenue),
        (GrowthMetric.EARNINGS, growth.earnings),
        (GrowthMetric.OPERATING_CASH_FLOW, growth.operating_cash_flow),
        (GrowthMetric.FREE_CASH_FLOW, growth.free_cash_flow),
        (GrowthMetric.BOOK_VALUE, growth.book_value),
        (GrowthMetric.EARNINGS_PER_SHARE, growth.earnings_per_share),
    )
    return GrowthDurabilitySummary(
        metrics_with_consistent_growth=tuple(
            metric for metric, trend in per_metric if trend.durability.consistency is GrowthConsistency.CONSISTENT_GROWTH
        ),
        metrics_with_consistent_decline=tuple(
            metric for metric, trend in per_metric if trend.durability.consistency is GrowthConsistency.CONSISTENT_DECLINE
        ),
        metrics_recovered_from_decline=tuple(
            metric for metric, trend in per_metric if trend.durability.recovery_status is RecoveryStatus.RECOVERED
        ),
    )


@dataclass(frozen=True)
class BusinessDurability:
    financial_durability: FinancialDurabilityKnowledge
    """Direct pass-through of Sprint 5's own closed-vocabulary
    findings -- "sustained cash generation"/"sustained profitability"
    (Phase 4)."""
    earnings_durability: ConsistencyLevel
    """Direct reuse of `FinancialHealthKnowledge.earnings_durability`
    (Sprint 3) -- was net income positive in every known period."""
    growth_durability: GrowthDurabilitySummary
    capital_discipline: ManagementCapitalAllocationKnowledge
    """Direct pass-through of Sprint 4's own management capital
    allocation assessment -- "sustained capital discipline" (Phase 4)."""


# -- Phase 5: Business Efficiency ----------------------------------------


@dataclass(frozen=True)
class BusinessEfficiency:
    capital_efficiency: CapitalEfficiencyKnowledge
    """Direct pass-through of Sprint 5's own `CapitalEfficiencyKnowledge`
    -- Phase 5's own "Reuse Financial Quality wherever possible. Do not
    compute duplicate metrics.\""""
    asset_efficiency_trend: TrendDirection
    """= `capital_efficiency.asset_turnover_trend` -- a convenience
    pass-through, not a second computation."""
    operating_efficiency_trend: TrendDirection
    """= `profitability_durability.operating_margin.trend` -- operating
    margin trend already is the standard proxy for operating efficiency;
    reused, not recomputed."""


def _business_efficiency(financial_quality: FinancialQualityKnowledge) -> BusinessEfficiency:
    return BusinessEfficiency(
        capital_efficiency=financial_quality.capital_efficiency,
        asset_efficiency_trend=financial_quality.capital_efficiency.asset_turnover_trend,
        operating_efficiency_trend=financial_quality.profitability_durability.operating_margin.trend,
    )


# -- Phase 1 + 6: Business Consistency -------------------------------------


@dataclass(frozen=True)
class HistoricalDisruption:
    """A pass-through re-labeling of an already-computed margin reversal
    (Sprint 5's own `MarginReversal` -- a period more than 1.5 standard
    deviations from that margin's own average) -- Phase 1's own "major
    historical disruptions," never a new statistic."""

    margin: MarginKind
    period_end: date
    margin_value: float
    deviation_from_average: float


@dataclass(frozen=True)
class BusinessConsistency:
    stable_dimensions: tuple[str, ...]
    """Which of the `BusinessStability` fields above resolved to a
    stable/consistent reading -- named by that field's own attribute
    name, never a score."""
    volatile_dimensions: tuple[str, ...]
    major_historical_disruptions: tuple[HistoricalDisruption, ...]


def _business_consistency(
    stability: BusinessStability, profitability_durability: ProfitabilityDurability
) -> BusinessConsistency:
    stable: list[str] = []
    volatile: list[str] = []

    if stability.profitability_stability is StabilityLevel.STABLE:
        stable.append("profitability_stability")
    elif stability.profitability_stability is StabilityLevel.VOLATILE:
        volatile.append("profitability_stability")

    if stability.revenue_stability in (GrowthConsistency.CONSISTENT_GROWTH, GrowthConsistency.CONSISTENT_DECLINE):
        stable.append("revenue_stability")
    elif stability.revenue_stability is GrowthConsistency.MIXED:
        volatile.append("revenue_stability")

    if stability.cash_generation_stability is ConsistencyLevel.CONSISTENT:
        stable.append("cash_generation_stability")
    elif stability.cash_generation_stability is ConsistencyLevel.INCONSISTENT:
        volatile.append("cash_generation_stability")

    if stability.capital_allocation_stability is BuybackConsistency.CONSISTENT:
        stable.append("capital_allocation_stability")
    elif stability.capital_allocation_stability is BuybackConsistency.INTERMITTENT:
        volatile.append("capital_allocation_stability")

    disruptions = tuple(
        HistoricalDisruption(
            margin=margin.margin, period_end=reversal.period_end, margin_value=reversal.margin_value,
            deviation_from_average=reversal.deviation_from_average,
        )
        for margin in (
            profitability_durability.gross_margin, profitability_durability.operating_margin,
            profitability_durability.net_margin,
        )
        for reversal in margin.reversals
    )

    return BusinessConsistency(
        stable_dimensions=tuple(stable), volatile_dimensions=tuple(volatile), major_historical_disruptions=disruptions,
    )


# -- Phase 6: Business Evolution -------------------------------------------


class EvolutionDirection(str, Enum):
    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"
    STABLE = "stable"
    MIXED = "mixed"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class BusinessEvolution:
    direction: EvolutionDirection
    strengthening_signals: tuple[str, ...]
    """Named `TrendDirection` fields (dot-path strings) already computed
    by a sibling capability that read `RISING`."""
    weakening_signals: tuple[str, ...]


def _evolution_signals(
    financial_quality: FinancialQualityKnowledge, growth: GrowthKnowledge
) -> tuple[tuple[str, TrendDirection], ...]:
    return (
        ("profitability_durability.net_margin.trend", financial_quality.profitability_durability.net_margin.trend),
        ("cash_conversion.ocf_conversion_trend", financial_quality.cash_conversion.ocf_conversion_trend),
        ("capital_efficiency.return_on_assets_trend", financial_quality.capital_efficiency.return_on_assets_trend),
        ("growth.revenue.direction", growth.revenue.direction),
        ("growth.free_cash_flow.direction", growth.free_cash_flow.direction),
    )


def _business_evolution(financial_quality: FinancialQualityKnowledge, growth: GrowthKnowledge) -> BusinessEvolution:
    strengthening: list[str] = []
    weakening: list[str] = []
    known_count = 0
    for label, direction in _evolution_signals(financial_quality, growth):
        if direction is TrendDirection.INSUFFICIENT_DATA:
            continue
        known_count += 1
        if direction is TrendDirection.RISING:
            strengthening.append(label)
        elif direction is TrendDirection.FALLING:
            weakening.append(label)

    if known_count == 0:
        direction_result = EvolutionDirection.INSUFFICIENT_DATA
    elif strengthening and weakening:
        direction_result = EvolutionDirection.MIXED
    elif strengthening:
        direction_result = EvolutionDirection.STRENGTHENING
    elif weakening:
        direction_result = EvolutionDirection.WEAKENING
    else:
        direction_result = EvolutionDirection.STABLE

    return BusinessEvolution(
        direction=direction_result, strengthening_signals=tuple(strengthening), weakening_signals=tuple(weakening),
    )


# -- Phase 9: Explainable Findings -----------------------------------------


class BusinessQualityFindingKind(str, Enum):
    """Closed, presence-only findings assembled from the already-
    computed dimensions above -- never a new computation and never
    combined into a score (this sprint's own "not a score" non-goal)."""

    CONSISTENT_VALUE_CREATION = "consistent_value_creation"
    """Profitability, cash generation, and revenue all show a stable or
    consistent-growth pattern."""
    PROFITABILITY_SURVIVES_DIFFICULT_PERIODS = "profitability_survives_difficult_periods"
    """Net income positive in every known period, and at least one
    growth metric has genuinely recovered from a real historical
    decline."""
    DURABLE_GROWTH = "durable_growth"
    """At least three of the six tracked growth metrics show consistent
    growth."""
    STRENGTHENING_BUSINESS = "strengthening_business"
    WEAKENING_BUSINESS = "weakening_business"
    EFFICIENT_CAPITAL_DEPLOYMENT = "efficient_capital_deployment"
    """Return on assets and asset turnover both rising."""
    DISCIPLINED_CAPITAL_ALLOCATION = "disciplined_capital_allocation"
    """Debt repayment has kept pace with issuance, and buyback activity
    has been consistent."""
    INSUFFICIENT_HISTORY = "insufficient_history"


@dataclass(frozen=True)
class BusinessQualityFinding:
    kind: BusinessQualityFindingKind
    supporting_dimensions: tuple[str, ...]
    """Dot-path names of the exact `BusinessQualityKnowledge` field(s)
    that produced this finding -- Phase 9's own "supporting evidence"
    and "traceable" requirement, satisfied by naming the already-
    computed field itself rather than introducing a new citation
    system."""


def _findings(
    stability: BusinessStability, durability: BusinessDurability, efficiency: BusinessEfficiency,
    evolution: BusinessEvolution,
) -> tuple[BusinessQualityFinding, ...]:
    findings: list[BusinessQualityFinding] = []

    if (
        stability.profitability_stability is StabilityLevel.STABLE
        and stability.cash_generation_stability is ConsistencyLevel.CONSISTENT
        and stability.revenue_stability is GrowthConsistency.CONSISTENT_GROWTH
    ):
        findings.append(
            BusinessQualityFinding(
                kind=BusinessQualityFindingKind.CONSISTENT_VALUE_CREATION,
                supporting_dimensions=(
                    "stability.profitability_stability", "stability.cash_generation_stability",
                    "stability.revenue_stability",
                ),
            )
        )

    if durability.earnings_durability is ConsistencyLevel.CONSISTENT and durability.growth_durability.metrics_recovered_from_decline:
        findings.append(
            BusinessQualityFinding(
                kind=BusinessQualityFindingKind.PROFITABILITY_SURVIVES_DIFFICULT_PERIODS,
                supporting_dimensions=("durability.earnings_durability", "durability.growth_durability.metrics_recovered_from_decline"),
            )
        )

    if len(durability.growth_durability.metrics_with_consistent_growth) >= _MIN_DURABLE_GROWTH_METRICS:
        findings.append(
            BusinessQualityFinding(
                kind=BusinessQualityFindingKind.DURABLE_GROWTH,
                supporting_dimensions=("durability.growth_durability.metrics_with_consistent_growth",),
            )
        )

    if evolution.direction is EvolutionDirection.STRENGTHENING:
        findings.append(
            BusinessQualityFinding(
                kind=BusinessQualityFindingKind.STRENGTHENING_BUSINESS, supporting_dimensions=("evolution.strengthening_signals",),
            )
        )
    elif evolution.direction is EvolutionDirection.WEAKENING:
        findings.append(
            BusinessQualityFinding(
                kind=BusinessQualityFindingKind.WEAKENING_BUSINESS, supporting_dimensions=("evolution.weakening_signals",),
            )
        )

    if (
        efficiency.capital_efficiency.return_on_assets_trend is TrendDirection.RISING
        and efficiency.asset_efficiency_trend is TrendDirection.RISING
    ):
        findings.append(
            BusinessQualityFinding(
                kind=BusinessQualityFindingKind.EFFICIENT_CAPITAL_DEPLOYMENT,
                supporting_dimensions=("efficiency.capital_efficiency.return_on_assets_trend", "efficiency.asset_efficiency_trend"),
            )
        )

    if (
        durability.capital_discipline.debt_discipline is DebtDiscipline.DISCIPLINED
        and durability.capital_discipline.capital_allocation_consistency is BuybackConsistency.CONSISTENT
    ):
        findings.append(
            BusinessQualityFinding(
                kind=BusinessQualityFindingKind.DISCIPLINED_CAPITAL_ALLOCATION,
                supporting_dimensions=(
                    "durability.capital_discipline.debt_discipline", "durability.capital_discipline.capital_allocation_consistency",
                ),
            )
        )

    if not findings:
        findings.append(BusinessQualityFinding(kind=BusinessQualityFindingKind.INSUFFICIENT_HISTORY, supporting_dimensions=()))

    return tuple(findings)


# -- Composition -------------------------------------------------------------


@dataclass(frozen=True)
class BusinessQualityKnowledge:
    stability: BusinessStability
    durability: BusinessDurability
    efficiency: BusinessEfficiency
    consistency: BusinessConsistency
    evolution: BusinessEvolution
    findings: tuple[BusinessQualityFinding, ...]


def extract_business_quality(
    financial_statement_history: FinancialStatementHistory,
    capital_allocation_history: CapitalAllocationHistory,
    financial_quality: FinancialQualityKnowledge,
    growth: GrowthKnowledge,
) -> BusinessQualityKnowledge:
    """Pure, no I/O. Computes zero new statistics from raw periods --
    see this module's own docstring. Every sibling's own honest
    "insufficient data"/"insufficient history" default propagates
    through unchanged when that sibling itself had no evidence -- never
    overridden here."""
    financial_health = assess_financial_health(financial_statement_history)
    management_capital_allocation = assess_management_capital_allocation(capital_allocation_history)
    cash_generation_stability = compute_cash_flow_consistency(financial_statement_history)

    stability = BusinessStability(
        profitability_stability=_aggregate_stability(
            (
                financial_quality.profitability_durability.gross_margin.stability,
                financial_quality.profitability_durability.operating_margin.stability,
                financial_quality.profitability_durability.net_margin.stability,
            )
        ),
        revenue_stability=growth.revenue.durability.consistency,
        cash_generation_stability=cash_generation_stability,
        capital_allocation_stability=management_capital_allocation.capital_allocation_consistency,
    )
    durability = BusinessDurability(
        financial_durability=financial_quality.financial_durability,
        earnings_durability=financial_health.earnings_durability,
        growth_durability=_growth_durability_summary(growth),
        capital_discipline=management_capital_allocation,
    )
    efficiency = _business_efficiency(financial_quality)
    consistency = _business_consistency(stability, financial_quality.profitability_durability)
    evolution = _business_evolution(financial_quality, growth)
    findings = _findings(stability, durability, efficiency, evolution)

    return BusinessQualityKnowledge(
        stability=stability, durability=durability, efficiency=efficiency, consistency=consistency,
        evolution=evolution, findings=findings,
    )

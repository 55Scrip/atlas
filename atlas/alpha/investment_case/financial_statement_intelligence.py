"""Financial Statement Knowledge Model + Multi-Year History + Trend
Intelligence + Financial Health Knowledge (Capability Expansion Sprint
3: Financial Statement Intelligence, Phases 1 + 3 + 4 + 5).

A small, read-only projection over already-ingested `FINANCIAL_
STATEMENT` `BusinessRecord`s -- the same "what does Atlas actually
know" convention `financial_history.py`'s own `FinancialPeriod`
already establishes, deliberately independent of it (a new, additive
module, never a modification of that pre-existing one -- this sprint's
own non-goal list protects prior capability sprints' own work the same
way it protects this one).

**Every new field here is read directly from `BusinessRecord.metadata`,
never through `atlas.analysis_engine.business_facts.BusinessFactKind`.**
That enum is the Decision Layer's own input contract (`growth.py`/
`capital_allocation.py` read it); adding members to it, or wiring these
new figures into `extract_facts`, would risk exactly the "redesign the
Decision Layer" this sprint's own non-goals forbid. This module reads
the identical raw provider metadata a real evaluator could someday
choose to consume, through its own, completely separate path -- the
Decision Layer's own inputs are untouched by construction, not by
convention.

**Segment Information (Phase 1's fourth statement group) is a real,
declared knowledge shape with no extractor wired this sprint** -- SEC
EDGAR's `companyfacts` endpoint this provider already uses reports one
value per concept per period, not per business/geographic segment
(genuine per-segment XBRL data requires a structurally different,
dimensional query this provider does not perform). Modeled honestly as
always-empty, the identical "framework, not complete dataset"
discipline `KnowledgeDomain`'s own docstring already establishes for
32 of its 36 members.

**Trend/Financial Health thresholds are disclosed, textbook accounting
conventions (a current ratio of 2.0, a debt-to-equity of 0.5, etc.),
never an Atlas-invented composite score** -- each dimension reads
exactly one real, computed ratio; none are combined or weighted
together, honoring this sprint's own "must not introduce investment
scoring" non-goal.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = [
    "IncomeStatementPeriod",
    "BalanceSheetPeriod",
    "CashFlowStatementPeriod",
    "SegmentPeriod",
    "SegmentInformation",
    "FinancialStatementHistory",
    "TrendDirection",
    "FinancialTrendMetric",
    "FinancialTrendObservation",
    "ConsistencyLevel",
    "FinancialHealthTier",
    "SolvencyTier",
    "FinancialHealthKnowledge",
    "extract_financial_statement_history",
    "compute_trend_intelligence",
    "compute_cash_flow_consistency",
    "assess_financial_health",
]


@dataclass(frozen=True)
class IncomeStatementPeriod:
    period_end: date
    revenue: float | None
    gross_profit: float | None
    operating_income: float | None
    ebitda: float | None
    net_income: float | None
    eps: float | None
    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
    currency: str | None
    accounting_basis: str | None
    """The filing form this period's own figures were reported under
    (e.g. `"10-K"`) -- real provider metadata (`sec_form`), never
    inferred or assumed. `None` only for a record predating this field's
    own introduction."""
    source_reference: str | None
    """The real filing reference `BusinessRecord.source_reference`
    already carries -- traceability back to the underlying filing
    (Phase 8), never manufactured when the provider did not supply
    one."""


@dataclass(frozen=True)
class BalanceSheetPeriod:
    period_end: date
    cash: float | None
    total_debt: float | None
    equity: float | None
    current_assets: float | None
    current_liabilities: float | None
    working_capital: float | None
    total_assets: float | None
    tangible_assets: float | None
    intangible_assets: float | None
    currency: str | None
    accounting_basis: str | None
    source_reference: str | None


@dataclass(frozen=True)
class CashFlowStatementPeriod:
    period_end: date
    operating_cash_flow: float | None
    investing_cash_flow: float | None
    financing_cash_flow: float | None
    free_cash_flow: float | None
    capital_expenditure: float | None
    currency: str | None
    accounting_basis: str | None
    source_reference: str | None


class SegmentKind(str, Enum):
    BUSINESS = "business"
    GEOGRAPHIC = "geographic"


@dataclass(frozen=True)
class SegmentPeriod:
    period_end: date
    segment_kind: SegmentKind
    segment_name: str
    revenue: float | None
    operating_income: float | None


@dataclass(frozen=True)
class SegmentInformation:
    segments: tuple[SegmentPeriod, ...] = ()
    """Always empty in this build of Atlas -- see this module's own
    docstring for why. A future sprint wiring real per-segment XBRL
    extraction populates this without changing its own shape."""


@dataclass(frozen=True)
class FinancialStatementHistory:
    income_statements: tuple[IncomeStatementPeriod, ...]
    balance_sheets: tuple[BalanceSheetPeriod, ...]
    cash_flow_statements: tuple[CashFlowStatementPeriod, ...]
    segments: SegmentInformation
    """Every tuple is chronological, oldest first -- Phase 3's own
    "preserve history rather than only current values.\""""


def _margin(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def extract_financial_statement_history(business_records: tuple[BusinessRecord, ...]) -> FinancialStatementHistory:
    """Pure, no I/O: every `FINANCIAL_STATEMENT` record, oldest period
    first, projected into the three statement groups. Margins are
    always derived here (`gross_profit / revenue`, etc.), never a raw
    filed tag -- consistent with `MarketSnapshot.market_cap`'s own
    "derive cheap, deterministic ratios at the read boundary, never
    persist them" precedent."""
    statements = [r for r in business_records if r.document_type is SourceKind.FINANCIAL_STATEMENT]
    statements.sort(key=lambda r: r.period_end or r.published_at.date())

    income_statements: list[IncomeStatementPeriod] = []
    balance_sheets: list[BalanceSheetPeriod] = []
    cash_flow_statements: list[CashFlowStatementPeriod] = []

    for record in statements:
        period_end = record.period_end or record.published_at.date()
        metadata = record.metadata
        currency = metadata.get("currency")
        accounting_basis = metadata.get("sec_form")
        source_reference = record.source_reference

        revenue = metadata.get("revenue")
        gross_profit = metadata.get("gross_profit")
        operating_income = metadata.get("operating_income")

        income_statements.append(
            IncomeStatementPeriod(
                period_end=period_end,
                revenue=revenue,
                gross_profit=gross_profit,
                operating_income=operating_income,
                ebitda=metadata.get("ebitda"),
                net_income=metadata.get("net_income"),
                eps=metadata.get("eps"),
                gross_margin=_margin(gross_profit, revenue),
                operating_margin=_margin(operating_income, revenue),
                net_margin=_margin(metadata.get("net_income"), revenue),
                currency=currency,
                accounting_basis=accounting_basis,
                source_reference=source_reference,
            )
        )
        balance_sheets.append(
            BalanceSheetPeriod(
                period_end=period_end,
                cash=metadata.get("cash"),
                total_debt=metadata.get("total_debt"),
                equity=metadata.get("equity"),
                current_assets=metadata.get("current_assets"),
                current_liabilities=metadata.get("current_liabilities"),
                working_capital=metadata.get("working_capital"),
                total_assets=metadata.get("total_assets"),
                tangible_assets=metadata.get("tangible_assets"),
                intangible_assets=metadata.get("intangible_assets"),
                currency=currency,
                accounting_basis=accounting_basis,
                source_reference=source_reference,
            )
        )
        cash_flow_statements.append(
            CashFlowStatementPeriod(
                period_end=period_end,
                operating_cash_flow=metadata.get("operating_cash_flow"),
                investing_cash_flow=metadata.get("investing_cash_flow"),
                financing_cash_flow=metadata.get("financing_cash_flow"),
                free_cash_flow=metadata.get("free_cash_flow"),
                capital_expenditure=metadata.get("capital_expenditure"),
                currency=currency,
                accounting_basis=accounting_basis,
                source_reference=source_reference,
            )
        )

    return FinancialStatementHistory(
        income_statements=tuple(income_statements),
        balance_sheets=tuple(balance_sheets),
        cash_flow_statements=tuple(cash_flow_statements),
        segments=SegmentInformation(),
    )


# -- Phase 4: Financial Trend Intelligence -----------------------------


class TrendDirection(str, Enum):
    """A later-half/earlier-half average comparison over a metric's own
    known periods -- the identical "categorical bucket over a disclosed
    threshold" discipline `historical_valuation.ValuationTrend` already
    establishes (duplicated here rather than imported, to keep this
    module independent of that sprint's own protected package -- see
    this module's own docstring)."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class FinancialTrendMetric(str, Enum):
    REVENUE_GROWTH = "revenue_growth"
    GROSS_MARGIN = "gross_margin"
    OPERATING_MARGIN = "operating_margin"
    NET_MARGIN = "net_margin"
    CAPITAL_INTENSITY = "capital_intensity"
    DEBT_TRAJECTORY = "debt_trajectory"
    EQUITY_GROWTH = "equity_growth"
    WORKING_CAPITAL = "working_capital"
    SEGMENT_EVOLUTION = "segment_evolution"
    """Always `INSUFFICIENT_DATA` in this build -- mirrors `SegmentInformation`'s
    own always-empty state."""


@dataclass(frozen=True)
class FinancialTrendObservation:
    metric: FinancialTrendMetric
    direction: TrendDirection
    periods_considered: int


class ConsistencyLevel(str, Enum):
    """Cash Flow Consistency's own vocabulary -- distinct from
    `TrendDirection` because "was Operating Cash Flow positive every
    year" is a consistency question, not a rising/falling one."""

    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    INSUFFICIENT_DATA = "insufficient_data"


_MIN_PERIODS_FOR_TREND = 3
_TREND_THRESHOLD = 0.1
_MIN_PERIODS_FOR_CONSISTENCY = 2


def _trend_direction(values: tuple[float, ...]) -> TrendDirection:
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


def _observation(metric: FinancialTrendMetric, values: list[float]) -> FinancialTrendObservation:
    direction = _trend_direction(tuple(values))
    return FinancialTrendObservation(metric=metric, direction=direction, periods_considered=len(values))


def compute_trend_intelligence(history: FinancialStatementHistory) -> tuple[FinancialTrendObservation, ...]:
    """Pure, no I/O: one `FinancialTrendObservation` per named metric,
    computed from `history`'s own already-organized periods. Never a
    recommendation -- a `RISING`/`FALLING` direction describes what the
    numbers did, not whether that is good or bad."""
    revenue = [p.revenue for p in history.income_statements if p.revenue is not None]
    gross_margin = [p.gross_margin for p in history.income_statements if p.gross_margin is not None]
    operating_margin = [p.operating_margin for p in history.income_statements if p.operating_margin is not None]
    net_margin = [p.net_margin for p in history.income_statements if p.net_margin is not None]
    equity = [p.equity for p in history.balance_sheets if p.equity is not None]
    total_debt = [p.total_debt for p in history.balance_sheets if p.total_debt is not None]
    working_capital = [p.working_capital for p in history.balance_sheets if p.working_capital is not None]

    capital_intensity: list[float] = []
    for period in history.cash_flow_statements:
        matching_income = next(
            (i for i in history.income_statements if i.period_end == period.period_end), None
        )
        if period.capital_expenditure is not None and matching_income is not None and matching_income.revenue:
            capital_intensity.append(period.capital_expenditure / matching_income.revenue)

    return (
        _observation(FinancialTrendMetric.REVENUE_GROWTH, revenue),
        _observation(FinancialTrendMetric.GROSS_MARGIN, gross_margin),
        _observation(FinancialTrendMetric.OPERATING_MARGIN, operating_margin),
        _observation(FinancialTrendMetric.NET_MARGIN, net_margin),
        _observation(FinancialTrendMetric.CAPITAL_INTENSITY, capital_intensity),
        _observation(FinancialTrendMetric.DEBT_TRAJECTORY, total_debt),
        _observation(FinancialTrendMetric.EQUITY_GROWTH, equity),
        _observation(FinancialTrendMetric.WORKING_CAPITAL, working_capital),
        FinancialTrendObservation(
            metric=FinancialTrendMetric.SEGMENT_EVOLUTION, direction=TrendDirection.INSUFFICIENT_DATA, periods_considered=0
        ),
    )


def compute_cash_flow_consistency(history: FinancialStatementHistory) -> ConsistencyLevel:
    values = [p.operating_cash_flow for p in history.cash_flow_statements if p.operating_cash_flow is not None]
    if len(values) < _MIN_PERIODS_FOR_CONSISTENCY:
        return ConsistencyLevel.INSUFFICIENT_DATA
    return ConsistencyLevel.CONSISTENT if all(v > 0 for v in values) else ConsistencyLevel.INCONSISTENT


# -- Phase 5: Financial Health Knowledge --------------------------------


class FinancialHealthTier(str, Enum):
    """Shared 4-tier vocabulary for every Financial Health dimension
    whose own ratio has a natural "is this reassuring" polarity
    (Liquidity, Profitability, Cash Generation, Capital Efficiency,
    Balance Sheet Strength, Financial Flexibility)."""

    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
    NEGATIVE = "negative"
    INSUFFICIENT_DATA = "insufficient_data"


class SolvencyTier(str, Enum):
    """Solvency's own vocabulary -- inverted polarity from
    `FinancialHealthTier` (lower leverage is the reassuring direction),
    so it is never described as "strong"/"weak.\""""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    LEVERAGED = "leveraged"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class FinancialHealthKnowledge:
    liquidity: FinancialHealthTier
    solvency: SolvencyTier
    profitability: FinancialHealthTier
    cash_generation: FinancialHealthTier
    capital_efficiency: FinancialHealthTier
    balance_sheet_strength: FinancialHealthTier
    earnings_durability: ConsistencyLevel
    financial_flexibility: FinancialHealthTier


def _tier_from_ratio(ratio: float | None, *, strong: float, adequate: float, negative_below_zero: bool = False) -> FinancialHealthTier:
    if ratio is None:
        return FinancialHealthTier.INSUFFICIENT_DATA
    if negative_below_zero and ratio < 0:
        return FinancialHealthTier.NEGATIVE
    if ratio >= strong:
        return FinancialHealthTier.STRONG
    if ratio >= adequate:
        return FinancialHealthTier.ADEQUATE
    return FinancialHealthTier.WEAK


def _latest(periods: tuple) -> object | None:
    return periods[-1] if periods else None


def assess_financial_health(history: FinancialStatementHistory) -> FinancialHealthKnowledge:
    """Pure, no I/O: one real, standard, single-ratio-based categorical
    tier per dimension, computed from the most recent known period
    (earnings durability alone reads the full history). Never combined
    or weighted into one composite -- see this module's own docstring."""
    latest_balance_sheet = _latest(history.balance_sheets)
    latest_income = _latest(history.income_statements)
    latest_cash_flow = _latest(history.cash_flow_statements)

    # Liquidity: current_ratio = current_assets / current_liabilities.
    # >= 2.0 "strong", >= 1.0 "adequate" -- textbook accounting
    # thresholds (a current ratio below 1.0 means current liabilities
    # exceed current assets), never an Atlas-invented cutoff.
    current_ratio = None
    if latest_balance_sheet is not None:
        current_ratio = _margin(latest_balance_sheet.current_assets, latest_balance_sheet.current_liabilities)
    liquidity = _tier_from_ratio(current_ratio, strong=2.0, adequate=1.0)

    # Solvency: debt_to_equity = total_debt / equity. < 0.5 "conservative",
    # < 1.5 "moderate", otherwise "leveraged" -- standard finance
    # textbook bands.
    solvency = SolvencyTier.INSUFFICIENT_DATA
    if latest_balance_sheet is not None:
        debt_to_equity = _margin(latest_balance_sheet.total_debt, latest_balance_sheet.equity)
        if debt_to_equity is not None:
            if debt_to_equity < 0.5:
                solvency = SolvencyTier.CONSERVATIVE
            elif debt_to_equity < 1.5:
                solvency = SolvencyTier.MODERATE
            else:
                solvency = SolvencyTier.LEVERAGED

    # Profitability: net_margin, most recent period.
    net_margin = latest_income.net_margin if latest_income is not None else None
    profitability = _tier_from_ratio(net_margin, strong=0.15, adequate=0.05, negative_below_zero=True)

    # Cash Generation: operating_cash_flow / net_income -- a real,
    # standard earnings-quality proxy (cash backing reported profit).
    cash_generation = FinancialHealthTier.INSUFFICIENT_DATA
    if latest_cash_flow is not None and latest_income is not None:
        ocf_to_net_income = _margin(latest_cash_flow.operating_cash_flow, latest_income.net_income)
        if ocf_to_net_income is not None:
            if latest_income.net_income is not None and latest_income.net_income <= 0:
                cash_generation = FinancialHealthTier.NEGATIVE
            else:
                cash_generation = _tier_from_ratio(ocf_to_net_income, strong=1.0, adequate=0.5)

    # Capital Efficiency: FCF margin = free_cash_flow / revenue.
    capital_efficiency = FinancialHealthTier.INSUFFICIENT_DATA
    if latest_cash_flow is not None and latest_income is not None:
        fcf_margin = _margin(latest_cash_flow.free_cash_flow, latest_income.revenue)
        capital_efficiency = _tier_from_ratio(fcf_margin, strong=0.15, adequate=0.05, negative_below_zero=True)

    # Balance Sheet Strength: equity / total_assets (capitalization
    # ratio) -- how much of the balance sheet is funded by equity
    # rather than liabilities.
    balance_sheet_strength = FinancialHealthTier.INSUFFICIENT_DATA
    if latest_balance_sheet is not None:
        equity_ratio = _margin(latest_balance_sheet.equity, latest_balance_sheet.total_assets)
        balance_sheet_strength = _tier_from_ratio(equity_ratio, strong=0.5, adequate=0.25)

    # Earnings Durability: was net income positive in every known period.
    earnings_durability = ConsistencyLevel.INSUFFICIENT_DATA
    net_income_values = [p.net_income for p in history.income_statements if p.net_income is not None]
    if len(net_income_values) >= _MIN_PERIODS_FOR_CONSISTENCY:
        earnings_durability = (
            ConsistencyLevel.CONSISTENT if all(v > 0 for v in net_income_values) else ConsistencyLevel.INCONSISTENT
        )

    # Financial Flexibility: cash / total_debt -- how much of total debt
    # cash alone could retire. No debt at all is maximal flexibility,
    # not "insufficient data."
    financial_flexibility = FinancialHealthTier.INSUFFICIENT_DATA
    if latest_balance_sheet is not None and latest_balance_sheet.cash is not None:
        if latest_balance_sheet.total_debt is not None and latest_balance_sheet.total_debt > 0:
            cash_to_debt = latest_balance_sheet.cash / latest_balance_sheet.total_debt
            financial_flexibility = _tier_from_ratio(cash_to_debt, strong=1.0, adequate=0.5)
        elif latest_balance_sheet.total_debt == 0:
            financial_flexibility = FinancialHealthTier.STRONG

    return FinancialHealthKnowledge(
        liquidity=liquidity,
        solvency=solvency,
        profitability=profitability,
        cash_generation=cash_generation,
        capital_efficiency=capital_efficiency,
        balance_sheet_strength=balance_sheet_strength,
        earnings_durability=earnings_durability,
        financial_flexibility=financial_flexibility,
    )

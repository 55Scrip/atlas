"""Capital Allocation Knowledge Model + Multi-Year History + Trend
Intelligence + Management Capital Allocation Knowledge (Capability
Expansion Sprint 4: Capital Allocation Intelligence, Phases 1 + 3 + 4
+ 5).

**Phase 2 audit finding, confirmed by reading the real code before any
of this was written**: every Capital Allocation raw fact except
acquisitions/disposals/treasury-share-count already existed in this
codebase before this sprint -- `SecEdgarFundamentalsProvider` was
already fetching `capital_expenditure`, `share_buybacks`,
`share_issuance`, `dividends`, `debt_issuance`, `debt_repayment`, and
`shares_outstanding`, and `atlas.analysis_engine.capital_allocation
.evaluate_capital_allocation` was already a real, running evaluator
reading exactly those seven as `BusinessFactKind` members. This module
does not duplicate that evaluator's own `capital_return`/`leverage`
signal (`STRONG`/`MODERATE`/`WEAK`/`INSUFFICIENT_INPUT`) -- it is left
completely unmodified, per this sprint's own Phase 7 instruction to
preserve existing Decision Layer behavior. This module instead reads
the identical raw `BusinessRecord.metadata` a second, independent way
-- the same "what does Atlas actually know" convention `financial_
statement_intelligence.py`'s own module docstring already establishes
-- to build genuinely richer, presentation-facing, multi-year
structured knowledge the evaluator itself has no need for (a full
history, trend directions, consistency classifications).

**"Maintenance capex" vs "growth capex" is a genuine, disclosed
limitation, not an oversight**: SEC XBRL reports one aggregate
Property/Plant/Equipment capital-expenditure figure per period; the
maintenance/growth split is an analyst judgment with no corresponding
filed fact, so both fields always resolve to `None` here rather than
being estimated from an invented formula (this sprint's own "never
fabricate financial information" instruction).

**`investment_activity` reuses `financial_statement_intelligence
.CashFlowStatementPeriod.investing_cash_flow` (Sprint 3) rather than
introducing a new provider field** -- the aggregate investing-activities
cash flow this sprint's own Phase 1 "investment activity" bullet asks
for already exists; re-fetching or re-deriving it here would be exactly
the "parallel provider" this sprint's own Phase 2 instruction forbids.

**Every trend classification is a disclosed, categorical bucket over a
later-half/earlier-half average comparison -- the `_trend_direction`
algorithm below is duplicated (not imported), the same "small justified
duplication over touching a protected sibling" discipline every other
capability module in this package follows for its own copy of this
algorithm.** The *vocabulary* it returns, `TrendDirection`, is reused
directly from `financial_statement_intelligence.py` (Cleanup Sprint 1)
rather than independently redeclared: six of this module's own sibling
capabilities already import that identical type, and a plain enum of
closed string values carries no logic of its own to protect against
"redesigning a protected sibling" -- only the `_trend_direction`
function's own algorithm is the thing worth keeping independent.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.financial_statement_intelligence import TrendDirection
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = [
    "CapitalAllocationPeriod",
    "CapitalAllocationHistory",
    "TrendDirection",
    "CapitalAllocationTrendMetric",
    "CapitalAllocationTrendObservation",
    "DividendContinuity",
    "BuybackConsistency",
    "ShareholderReturnPolicy",
    "AcquisitionBehavior",
    "DebtDiscipline",
    "ManagementCapitalAllocationKnowledge",
    "extract_capital_allocation_history",
    "compute_capital_allocation_trends",
    "assess_dividend_continuity",
    "assess_buyback_consistency",
    "assess_management_capital_allocation",
]


@dataclass(frozen=True)
class CapitalAllocationPeriod:
    period_end: date
    capital_expenditure: float | None
    maintenance_capex: float | None
    """Always `None` in this build -- see this module's own docstring."""
    growth_capex: float | None
    """Always `None` in this build -- see this module's own docstring."""
    dividends: float | None
    share_buybacks: float | None
    treasury_shares_acquired: float | None
    share_issuance: float | None
    shares_outstanding: float | None
    debt_issuance: float | None
    debt_repayment: float | None
    total_debt: float | None
    acquisitions: float | None
    disposals: float | None
    investment_activity: float | None
    currency: str | None
    accounting_basis: str | None
    source_reference: str | None


@dataclass(frozen=True)
class CapitalAllocationHistory:
    periods: tuple[CapitalAllocationPeriod, ...]
    """Chronological, oldest first -- Phase 3's own "preserve history
    rather than only current state." Empty, never fabricated, when no
    `FINANCIAL_STATEMENT` record has been ingested yet."""


def extract_capital_allocation_history(business_records: tuple[BusinessRecord, ...]) -> CapitalAllocationHistory:
    """Pure, no I/O: every `FINANCIAL_STATEMENT` record, oldest period
    first, projected into one Capital Allocation view per period. Uses
    only real, already-ingested observations -- never invents a period
    to satisfy the model (Phase 3's own instruction)."""
    statements = [r for r in business_records if r.document_type is SourceKind.FINANCIAL_STATEMENT]
    statements.sort(key=lambda r: r.period_end or r.published_at.date())

    periods: list[CapitalAllocationPeriod] = []
    for record in statements:
        metadata = record.metadata
        periods.append(
            CapitalAllocationPeriod(
                period_end=record.period_end or record.published_at.date(),
                capital_expenditure=metadata.get("capital_expenditure"),
                maintenance_capex=None,
                growth_capex=None,
                dividends=metadata.get("dividends"),
                share_buybacks=metadata.get("share_buybacks"),
                treasury_shares_acquired=metadata.get("treasury_shares_acquired"),
                share_issuance=metadata.get("share_issuance"),
                shares_outstanding=metadata.get("shares_outstanding"),
                debt_issuance=metadata.get("debt_issuance"),
                debt_repayment=metadata.get("debt_repayment"),
                total_debt=metadata.get("total_debt"),
                acquisitions=metadata.get("acquisitions"),
                disposals=metadata.get("disposals"),
                investment_activity=metadata.get("investing_cash_flow"),
                currency=metadata.get("currency"),
                accounting_basis=metadata.get("sec_form"),
                source_reference=record.source_reference,
            )
        )
    return CapitalAllocationHistory(periods=tuple(periods))


# -- Phase 4: Capital Allocation Trend Intelligence ----------------------


class CapitalAllocationTrendMetric(str, Enum):
    SHARE_COUNT = "share_count"
    """Rising = shareholder dilution; falling = net share retirement."""
    BUYBACK_ACTIVITY = "buyback_activity"
    DIVIDEND_TREND = "dividend_trend"
    DEBT_TRAJECTORY = "debt_trajectory"
    CAPITAL_EXPENDITURE_TREND = "capital_expenditure_trend"
    ACQUISITION_ACTIVITY = "acquisition_activity"


@dataclass(frozen=True)
class CapitalAllocationTrendObservation:
    metric: CapitalAllocationTrendMetric
    direction: TrendDirection
    periods_considered: int


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


def _observation(metric: CapitalAllocationTrendMetric, values: list[float]) -> CapitalAllocationTrendObservation:
    return CapitalAllocationTrendObservation(
        metric=metric, direction=_trend_direction(tuple(values)), periods_considered=len(values)
    )


def compute_capital_allocation_trends(history: CapitalAllocationHistory) -> tuple[CapitalAllocationTrendObservation, ...]:
    """Pure, no I/O: one observation per named metric. Never a
    recommendation -- `RISING`/`FALLING` describes what the numbers
    did, not whether that is good or bad (Phase 4's own "these are
    observations, not recommendations")."""
    share_count = [p.shares_outstanding for p in history.periods if p.shares_outstanding is not None]
    buybacks = [p.share_buybacks for p in history.periods if p.share_buybacks is not None]
    dividends = [p.dividends for p in history.periods if p.dividends is not None]
    debt = [p.total_debt for p in history.periods if p.total_debt is not None]
    capex = [p.capital_expenditure for p in history.periods if p.capital_expenditure is not None]
    acquisitions = [p.acquisitions for p in history.periods if p.acquisitions is not None]

    return (
        _observation(CapitalAllocationTrendMetric.SHARE_COUNT, share_count),
        _observation(CapitalAllocationTrendMetric.BUYBACK_ACTIVITY, buybacks),
        _observation(CapitalAllocationTrendMetric.DIVIDEND_TREND, dividends),
        _observation(CapitalAllocationTrendMetric.DEBT_TRAJECTORY, debt),
        _observation(CapitalAllocationTrendMetric.CAPITAL_EXPENDITURE_TREND, capex),
        _observation(CapitalAllocationTrendMetric.ACQUISITION_ACTIVITY, acquisitions),
    )


class DividendContinuity(str, Enum):
    CONSISTENTLY_PAID = "consistently_paid"
    SUSPENDED = "suspended"
    """The most recent known period reported zero dividends immediately
    after a period that reported a positive amount -- a real, recent
    event, not a lifetime label."""
    NEVER_PAID = "never_paid"
    INSUFFICIENT_DATA = "insufficient_data"


def assess_dividend_continuity(history: CapitalAllocationHistory) -> DividendContinuity:
    known = [(p.period_end, p.dividends) for p in history.periods if p.dividends is not None]
    if len(known) < _MIN_PERIODS_FOR_CONSISTENCY:
        return DividendContinuity.INSUFFICIENT_DATA
    if all(value == 0 for _, value in known):
        return DividendContinuity.NEVER_PAID
    latest, previous = known[-1][1], known[-2][1]
    if latest == 0 and previous > 0:
        return DividendContinuity.SUSPENDED
    return DividendContinuity.CONSISTENTLY_PAID


class BuybackConsistency(str, Enum):
    CONSISTENT = "consistent"
    INTERMITTENT = "intermittent"
    NONE = "none"
    INSUFFICIENT_DATA = "insufficient_data"


def assess_buyback_consistency(history: CapitalAllocationHistory) -> BuybackConsistency:
    known = [p.share_buybacks for p in history.periods if p.share_buybacks is not None]
    if len(known) < _MIN_PERIODS_FOR_CONSISTENCY:
        return BuybackConsistency.INSUFFICIENT_DATA
    active_count = sum(1 for value in known if value > 0)
    if active_count == 0:
        return BuybackConsistency.NONE
    if active_count == len(known):
        return BuybackConsistency.CONSISTENT
    return BuybackConsistency.INTERMITTENT


# -- Phase 5: Management Capital Allocation Knowledge ---------------------


class ShareholderReturnPolicy(str, Enum):
    ACTIVE = "active"
    """Dividends and/or buybacks present in the most recent known period."""
    LIMITED = "limited"
    """Dividends/buybacks occurred historically, but not in the most
    recent known period."""
    NONE = "none"
    """No dividend or buyback activity in any known period."""
    INSUFFICIENT_DATA = "insufficient_data"


class AcquisitionBehavior(str, Enum):
    ACTIVE_ACQUIRER = "active_acquirer"
    """Acquisition activity present in at least half of known periods."""
    OPPORTUNISTIC = "opportunistic"
    """Acquisition activity present in some, but fewer than half, known periods."""
    NONE = "none"
    INSUFFICIENT_DATA = "insufficient_data"


class DebtDiscipline(str, Enum):
    DISCIPLINED = "disciplined"
    """Cumulative repayment is at least 80% of cumulative issuance --
    or no debt was issued at all across known history."""
    MODERATE = "moderate"
    ACCUMULATING = "accumulating"
    """Cumulative repayment is under 30% of cumulative issuance --
    borrowed debt is mostly not being repaid."""
    INSUFFICIENT_DATA = "insufficient_data"


_DISCIPLINED_REPAYMENT_RATIO = 0.8
_MODERATE_REPAYMENT_RATIO = 0.3
_ACTIVE_ACQUIRER_RATIO = 0.5


@dataclass(frozen=True)
class ManagementCapitalAllocationKnowledge:
    """Every field is one real, disclosed, single-signal classification
    -- never combined or weighted into a composite (this sprint's own
    "do not introduce management scoring" non-goal). `reinvestment_
    discipline`/`financing_strategy` intentionally reuse `TrendDirection`
    directly -- a management-oriented reading of the identical `CAPITAL_
    EXPENDITURE_TREND`/`DEBT_TRAJECTORY` observations above, not a
    second computation of the same thing under a different name."""

    reinvestment_discipline: TrendDirection
    shareholder_return_policy: ShareholderReturnPolicy
    financing_strategy: TrendDirection
    acquisition_behavior: AcquisitionBehavior
    debt_discipline: DebtDiscipline
    capital_allocation_consistency: BuybackConsistency


def _shareholder_return_policy(history: CapitalAllocationHistory) -> ShareholderReturnPolicy:
    known_dividends = [p.dividends for p in history.periods if p.dividends is not None]
    known_buybacks = [p.share_buybacks for p in history.periods if p.share_buybacks is not None]
    if not known_dividends and not known_buybacks:
        return ShareholderReturnPolicy.INSUFFICIENT_DATA
    latest = history.periods[-1]
    active_now = (latest.dividends is not None and latest.dividends > 0) or (
        latest.share_buybacks is not None and latest.share_buybacks > 0
    )
    if active_now:
        return ShareholderReturnPolicy.ACTIVE
    ever_active = any((p.dividends or 0) > 0 or (p.share_buybacks or 0) > 0 for p in history.periods)
    return ShareholderReturnPolicy.LIMITED if ever_active else ShareholderReturnPolicy.NONE


def _acquisition_behavior(history: CapitalAllocationHistory) -> AcquisitionBehavior:
    known = [p.acquisitions for p in history.periods if p.acquisitions is not None]
    if len(known) < _MIN_PERIODS_FOR_CONSISTENCY:
        return AcquisitionBehavior.INSUFFICIENT_DATA
    active_ratio = sum(1 for value in known if value > 0) / len(known)
    if active_ratio == 0:
        return AcquisitionBehavior.NONE
    if active_ratio >= _ACTIVE_ACQUIRER_RATIO:
        return AcquisitionBehavior.ACTIVE_ACQUIRER
    return AcquisitionBehavior.OPPORTUNISTIC


def _debt_discipline(history: CapitalAllocationHistory) -> DebtDiscipline:
    known_issuance = [p.debt_issuance for p in history.periods if p.debt_issuance is not None]
    known_repayment = [p.debt_repayment for p in history.periods if p.debt_repayment is not None]
    if not known_issuance or not known_repayment:
        return DebtDiscipline.INSUFFICIENT_DATA
    total_issuance = sum(known_issuance)
    total_repayment = sum(known_repayment)
    if total_issuance == 0:
        return DebtDiscipline.DISCIPLINED
    ratio = total_repayment / total_issuance
    if ratio >= _DISCIPLINED_REPAYMENT_RATIO:
        return DebtDiscipline.DISCIPLINED
    if ratio >= _MODERATE_REPAYMENT_RATIO:
        return DebtDiscipline.MODERATE
    return DebtDiscipline.ACCUMULATING


def assess_management_capital_allocation(history: CapitalAllocationHistory) -> ManagementCapitalAllocationKnowledge:
    """Pure, no I/O. `history.periods == ()` yields every field at its
    own honest `INSUFFICIENT_DATA`/`NONE`-shaped default -- never a
    fabricated assessment (Phase 5's own "do not infer management
    quality unless supported by real historical evidence")."""
    trends = {o.metric: o.direction for o in compute_capital_allocation_trends(history)}
    return ManagementCapitalAllocationKnowledge(
        reinvestment_discipline=trends[CapitalAllocationTrendMetric.CAPITAL_EXPENDITURE_TREND],
        shareholder_return_policy=_shareholder_return_policy(history),
        financing_strategy=trends[CapitalAllocationTrendMetric.DEBT_TRAJECTORY],
        acquisition_behavior=_acquisition_behavior(history),
        debt_discipline=_debt_discipline(history),
        capital_allocation_consistency=assess_buyback_consistency(history),
    )

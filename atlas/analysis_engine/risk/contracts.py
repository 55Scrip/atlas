"""Shared Risk Analysis vocabulary (ATLAS-025, Phase 4/5) -- `RiskStatus`,
`RiskDataGapKind`, `severity_for_risk_status` -- plus the closed vocabulary
a Financial Risk basis is stated in (`FinancialRiskSignal`,
`FinancialRiskMetric`, `FinancialRiskCondition`, `FinancialRiskRule`).

Mirrors `atlas.analysis_engine.business_contracts`'s own reason for
existing: `financial_risk.py`, `business_risk.py`, `valuation_risk.py`,
`thesis_risk.py`, and `pipeline.py` all need this shared vocabulary
without importing each other back and forth.

`atlas.analysis_engine.contracts.RiskCategory` (the closed, ten-member
taxonomy) is deliberately *not* redefined here -- it already lives one
level up, shared with `RiskSection` (ATLAS-020) and this sprint's own
per-category evaluators, which import it directly.
"""
from __future__ import annotations

from enum import Enum

from atlas.analysis_engine.findings import FindingSeverity

__all__ = [
    "FinancialRiskCondition",
    "FinancialRiskMetric",
    "FinancialRiskRule",
    "FinancialRiskSignal",
    "RiskStatus",
    "RiskDataGapKind",
    "severity_for_risk_status",
]


class RiskStatus(str, Enum):
    """Categorical, five levels, never numeric -- Phase 5's own list,
    applied verbatim, deliberately structured the same way
    `atlas.analysis_engine.business_contracts.BusinessCategoryStatus`
    and `atlas.analysis_engine.valuation.contracts.ValuationStatus` are
    (a `NOT_EVALUATED`/`INSUFFICIENT_INPUT` pair plus three real
    categorical outcomes), for consistency across sibling evaluators.
    `NOT_EVALUATED` is reserved, never constructed -- every category this
    sprint ships a real evaluator for reaches a genuine conclusion (`LOW`/
    `MODERATE`/`HIGH`) or an honest `INSUFFICIENT_INPUT`."""

    NOT_EVALUATED = "not_evaluated"
    INSUFFICIENT_INPUT = "insufficient_input"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class RiskDataGapKind(str, Enum):
    """Why a category could not reach a `LOW`/`MODERATE`/`HIGH`
    conclusion -- always a real, named reason, never a placeholder guess
    or a silent treatment of absence as zero. Same discipline
    `atlas.analysis_engine.business_contracts.BusinessDataGapKind` and
    `atlas.analysis_engine.valuation.contracts.ValuationDataGapKind`
    already established for their sibling packages."""

    GROWTH_ASSESSMENT_UNAVAILABLE = "growth_assessment_unavailable"
    """Business Risk: the upstream `GrowthFinding.status` is itself
    `INSUFFICIENT_INPUT` -- Atlas does not know enough about growth to
    say anything about Business Risk either. Missing evidence, not a
    negative signal (Phase 7's own critical distinction)."""

    CAPITAL_ALLOCATION_ASSESSMENT_UNAVAILABLE = "capital_allocation_assessment_unavailable"
    """Financial Risk: the upstream `CapitalAllocationFinding.status` is
    itself `INSUFFICIENT_INPUT`."""

    MISSING_CASH_FLOW_LEVEL = "missing_cash_flow_level"
    """Financial Risk: no `FREE_CASH_FLOW` fact exists at all, so the
    direct cash-generation sign check cannot run."""

    VALUATION_ASSESSMENT_UNAVAILABLE = "valuation_assessment_unavailable"
    """Valuation Risk: the upstream `FCF_YIELD_RELATIVE` `ValuationFinding
    .status` is itself `INSUFFICIENT_INPUT` (or `NOT_EVALUATED`)."""

    NO_EVIDENCE_TO_EVALUATE = "no_evidence_to_evaluate"
    """Thesis Risk: case-wide `EvidenceCoverageLevel` is `NOT_APPLICABLE`
    or `NONE` -- there is no Evidence recorded to check for contradiction
    at all, which is a different fact from "checked, found none"."""

    MISSING_DEBT_HISTORY = "missing_debt_history"
    """Financial Risk (Company Data Foundation v1): fewer than two
    `TOTAL_DEBT` facts across distinct periods, so the debt-trend
    signal could not be assessed. Always informational -- see
    `financial_risk.py`'s own module docstring for why this signal
    never lowers `confidence` and only ever escalates `status`, never
    the reverse."""


def severity_for_risk_status(status: RiskStatus) -> FindingSeverity:
    """Deterministic, mechanical mapping -- severity describes how much
    attention a Risk conclusion deserves, never how likely a loss is.
    Mirrors `business_contracts.severity_for_status`'s own three-tier
    shape: the single worst real conclusion (`HIGH`) is `MATERIAL`, a
    gap is `ATTENTION` (worth closing), everything else is `INFO`."""
    if status in (RiskStatus.NOT_EVALUATED, RiskStatus.INSUFFICIENT_INPUT):
        return FindingSeverity.ATTENTION
    if status is RiskStatus.HIGH:
        return FindingSeverity.MATERIAL
    return FindingSeverity.INFO


class FinancialRiskSignal(str, Enum):
    """The three signals `financial_risk.py`'s own rule table reads, in
    that table's own order. A name for each, so the basis of a Financial
    Risk level can say which one it rests on."""

    CAPITAL_ALLOCATION = "capital_allocation"
    CASH_GENERATION = "cash_generation"
    DEBT_TREND = "debt_trend"


class FinancialRiskMetric(str, Enum):
    """The reported figures Financial Risk reads directly. Values match
    `BusinessFactKind`'s own, so an observation names the fact it came
    from without every reader importing the fact layer."""

    FREE_CASH_FLOW = "free_cash_flow"
    TOTAL_DEBT = "total_debt"


class FinancialRiskCondition(str, Enum):
    """Which branch of a signal's own rule matched -- the rule restated,
    one member per branch, never a judgment beyond it.

    Debt trend compares reported total debt in absolute terms between
    consecutive evaluated periods: nothing here is a ratio, a coverage or
    a rating, and "increased every period" says only that each evaluated
    period's figure was higher than the one before."""

    CAPITAL_ALLOCATION_WEAK = "capital_allocation_weak"
    CAPITAL_ALLOCATION_MODERATE = "capital_allocation_moderate"
    CAPITAL_ALLOCATION_STRONG = "capital_allocation_strong"
    CAPITAL_ALLOCATION_UNAVAILABLE = "capital_allocation_unavailable"
    LATEST_FREE_CASH_FLOW_NEGATIVE = "latest_free_cash_flow_negative"
    LATEST_FREE_CASH_FLOW_NOT_NEGATIVE = "latest_free_cash_flow_not_negative"
    NO_FREE_CASH_FLOW = "no_free_cash_flow"
    TOTAL_DEBT_INCREASED_EVERY_PERIOD = "total_debt_increased_every_period"
    TOTAL_DEBT_DECREASED_EVERY_PERIOD = "total_debt_decreased_every_period"
    TOTAL_DEBT_NO_CONSISTENT_DIRECTION = "total_debt_no_consistent_direction"
    TOTAL_DEBT_FEWER_THAN_TWO_PERIODS = "total_debt_fewer_than_two_periods"


class FinancialRiskRule(str, Enum):
    """Which line of Financial Risk's combination table decided the
    level -- first match wins, in this order."""

    ANY_SIGNAL_HIGH = "any_signal_high"
    """`HIGH`: at least one signal is `HIGH`. Every `HIGH` signal is
    named; none offsets another and none is ranked first."""
    NO_CORE_SIGNAL_ASSESSED = "no_core_signal_assessed"
    """`INSUFFICIENT_INPUT`: neither capital allocation nor cash
    generation could be assessed."""
    CORE_SIGNALS_BOTH_LOW = "core_signals_both_low"
    """`LOW`: capital allocation and cash generation both `LOW`."""
    CORE_SIGNAL_NOT_LOW = "core_signal_not_low"
    """`MODERATE`: no signal `HIGH`, and capital allocation or cash
    generation is `MODERATE` or could not be assessed."""

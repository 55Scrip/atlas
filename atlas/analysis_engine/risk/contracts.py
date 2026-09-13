"""Shared Risk Analysis vocabulary (ATLAS-025, Phase 4/5) -- `RiskStatus`,
`RiskDataGapKind`, `severity_for_risk_status` -- plus the closed vocabulary
a Financial Risk basis is stated in (`FinancialRiskMeasure`,
`FinancialRiskCondition`, `FinancialRiskExclusionReason`).

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
    "FinancialRiskExclusionReason",
    "FinancialRiskMeasure",
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
    `MODERATE`/`HIGH`) or an honest `INSUFFICIENT_INPUT`.

    `NOT_APPLICABLE` (Financial Risk v2) is neither a conclusion nor a
    gap: the category's measure does not apply to this kind of business
    (a bank's debt funds its balance sheet, not its operations), so no
    amount of data would produce a `LOW`/`MODERATE`/`HIGH` from it. It is
    never a reassurance and never "risk is low"."""

    NOT_EVALUATED = "not_evaluated"
    INSUFFICIENT_INPUT = "insufficient_input"
    NOT_APPLICABLE = "not_applicable"
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
    """Financial Risk v1 (Company Data Foundation v1): fewer than two
    `TOTAL_DEBT` facts across distinct periods. No longer emitted since
    Financial Risk v2 -- kept, like the two v1 gaps above, so stored
    history still reads back."""

    MISSING_DEBT = "missing_debt"
    """Financial Risk v2: no eligible `TOTAL_DEBT` fact. Absent debt is
    never read as zero debt."""

    MISSING_OPERATING_CASH_FLOW = "missing_operating_cash_flow"
    """Financial Risk v2: no eligible `FREE_CASH_FLOW` and
    `CAPITAL_EXPENDITURE` pair, so operating cash flow cannot be
    derived."""

    NO_ALIGNED_PERIOD = "no_aligned_period"
    """Financial Risk v2: debt and cash-flow figures exist, but never for
    the same fiscal period end in the same unit -- Atlas never divides
    one year's debt by another year's cash flow."""

    STALE_FINANCIAL_STATEMENTS = "stale_financial_statements"
    """Financial Risk v2: the latest aligned period ended more than the
    maximum statement age before the evaluation date."""

    INDUSTRY_UNKNOWN = "industry_unknown"
    """Financial Risk v2: no company-profile industry, so Atlas cannot
    establish that its corporate debt measure applies (it does not for
    banks, dealers or insurers)."""


def severity_for_risk_status(status: RiskStatus) -> FindingSeverity:
    """Deterministic, mechanical mapping -- severity describes how much
    attention a Risk conclusion deserves, never how likely a loss is.
    Mirrors `business_contracts.severity_for_status`'s own three-tier
    shape: the single worst real conclusion (`HIGH`) is `MATERIAL`, a
    gap is `ATTENTION` (worth closing), everything else is `INFO`."""
    if status in (RiskStatus.NOT_EVALUATED, RiskStatus.INSUFFICIENT_INPUT):
        return FindingSeverity.ATTENTION
    # Not a gap worth closing -- more data would not make the measure apply.
    if status is RiskStatus.NOT_APPLICABLE:
        return FindingSeverity.INFO
    if status is RiskStatus.HIGH:
        return FindingSeverity.MATERIAL
    return FindingSeverity.INFO


class FinancialRiskMeasure(str, Enum):
    """The one measure Financial Risk v2 classifies on."""

    GROSS_DEBT_TO_OPERATING_CASH_FLOW = "gross_debt_to_operating_cash_flow"
    """Reported total debt divided by operating cash flow (free cash flow
    plus capital expenditure) for the same fiscal period end. Gross, not
    net: Atlas's cash figure excludes marketable securities, so a net
    figure would overstate some companies' debt and flatter none."""


class FinancialRiskCondition(str, Enum):
    """Why Financial Risk v2 reached its level -- one member per branch of
    `financial_risk.py`'s rule, never a judgment beyond it."""

    DEBT_BURDEN_LOW = "debt_burden_low"
    DEBT_BURDEN_MODERATE = "debt_burden_moderate"
    DEBT_BURDEN_HIGH = "debt_burden_high"
    OPERATING_CASH_FLOW_NEGATIVE = "operating_cash_flow_negative"
    """Operations consumed cash in the latest aligned period. Says
    exactly that -- nothing about solvency or distress."""
    OPERATING_CASH_FLOW_ZERO = "operating_cash_flow_zero"
    """Operations generated no net cash; the ratio is undefined and is
    never computed."""
    MEASURE_NOT_APPLICABLE = "measure_not_applicable"
    NO_ELIGIBLE_EVIDENCE = "no_eligible_evidence"


class FinancialRiskExclusionReason(str, Enum):
    """Why a debt or cash-flow fact was left out before anything was
    computed from it."""

    FUTURE_PERIOD = "future_period"
    """The period ends after the evaluation date -- not a realized
    figure."""
    NOT_A_FINANCIAL_STATEMENT = "not_a_financial_statement"
    """The source record is not a structured financial statement."""

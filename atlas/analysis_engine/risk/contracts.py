"""Shared Risk Analysis vocabulary (ATLAS-025, Phase 4/5) -- `RiskStatus`,
`RiskDataGapKind`, `severity_for_risk_status`.

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

__all__ = ["RiskStatus", "RiskDataGapKind", "severity_for_risk_status"]


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

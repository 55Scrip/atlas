"""Leverage Interpretation (Calibration Phase 7, Phase 7/9) -- the one
clear, repeated pattern across the brief's own examples: high leverage
means something structurally different depending on industry.

**Never changes the underlying signal.** `atlas.analysis_engine
.capital_allocation`'s own `BusinessCategoryStatus` and
`atlas.analysis_engine.risk.financial_risk`'s own debt-trend-driven
`RiskStatus` are computed exactly as before -- this module only adds a
named, disclosed annotation for how to read them, attached alongside
the original signal, never replacing it (the design doc's own Part D
"attach, never override" rule).

Three interpretations:

- `STRUCTURALLY_NORMAL` -- Utilities, Telecom, Real Estate: debt-funded
  capital investment against a regulated or contracted, relatively
  stable cash-flow base is a normal, structural financing choice, not
  a warning sign by itself.
- `METRIC_NOT_APPROPRIATE` -- Banks, Insurance: the whole leverage
  concept does not transfer from an operating-company frame; a
  financial institution's balance sheet *is* the regulated business,
  and the standard capital-adequacy framework (not a debt-trend read)
  is the appropriate lens Atlas does not currently implement.
- `GENERIC_INTERPRETATION_APPLIES` -- every other family: the existing
  Capital Allocation/Financial Risk read stands unadjusted; this is
  the honest default, not a fallback failure.
"""
from __future__ import annotations

from atlas.alpha.industry_intelligence.models import IndustryFamily, IndustryLeverageNote, LeverageInterpretation

__all__ = ["interpret_leverage"]

STRUCTURALLY_NORMAL_REASONING = {
    IndustryFamily.UTILITIES: (
        "Debt-funded capex against a regulated asset base with allowed, contracted "
        "returns is a normal, structural financing choice for this industry, not by "
        "itself equivalent to industrial-company financial distress."
    ),
    IndustryFamily.TELECOM: (
        "Network infrastructure is a long-lived, contracted-revenue-backed asset -- "
        "debt-funded buildout is a normal financing pattern here, similar in kind to "
        "a regulated utility."
    ),
    IndustryFamily.REAL_ESTATE: (
        "Real estate is financed with leverage against a portfolio of appreciating, "
        "income-producing assets as a matter of ordinary practice, not a distress "
        "signal by itself."
    ),
}

METRIC_NOT_APPROPRIATE_REASONING = {
    IndustryFamily.BANKS: (
        "A bank's balance-sheet leverage is the regulated business itself -- the "
        "appropriate lens is capital adequacy relative to a regulatory requirement, "
        "which this codebase does not currently implement, not a generic debt trend."
    ),
    IndustryFamily.INSURANCE: (
        "An insurer's leverage includes policy reserves and float, not the same "
        "concept a generic debt-trend read assumes."
    ),
}


def interpret_leverage(family: IndustryFamily) -> IndustryLeverageNote:
    """Deterministic: identical `family` always produces an identical
    `IndustryLeverageNote`."""
    if family in STRUCTURALLY_NORMAL_REASONING:
        return IndustryLeverageNote(
            interpretation=LeverageInterpretation.STRUCTURALLY_NORMAL,
            reasoning=STRUCTURALLY_NORMAL_REASONING[family],
        )
    if family in METRIC_NOT_APPROPRIATE_REASONING:
        return IndustryLeverageNote(
            interpretation=LeverageInterpretation.METRIC_NOT_APPROPRIATE,
            reasoning=METRIC_NOT_APPROPRIATE_REASONING[family],
        )
    if family in (IndustryFamily.UNCLASSIFIED, IndustryFamily.UNKNOWN):
        return IndustryLeverageNote(
            interpretation=LeverageInterpretation.UNKNOWN,
            reasoning="Industry family is not classified -- no basis to adjust the generic interpretation.",
        )
    return IndustryLeverageNote(
        interpretation=LeverageInterpretation.GENERIC_INTERPRETATION_APPLIES,
        reasoning="No industry-specific leverage adjustment applies -- the existing Capital Allocation/Financial Risk read stands.",
    )

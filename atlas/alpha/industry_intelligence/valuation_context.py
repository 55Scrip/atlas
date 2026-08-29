"""Valuation Applicability (Calibration Phase 7, Phase 8) -- the single
most valuable, lowest-risk addition this sprint makes.

`FCF_YIELD_RELATIVE` (`atlas.analysis_engine.valuation.cash_flow`) is
`current FCF / market_cap`, compared against the same company's own
historical range. This fits an operating company with a real,
representative free-cash-flow figure. It fits poorly for:

- **Banks/Insurance** -- the balance sheet *is* the business; a bank's
  or insurer's "free cash flow" is not the same economic concept as an
  industrial company's, and market cap relative to it does not answer
  the same question.
- **Real Estate/REITs** -- GAAP earnings (and by extension a naive FCF
  read) are structurally distorted by depreciation on long-lived
  assets; the standard REIT metric (funds from operations) is a
  different, adjusted figure this codebase does not compute.
- **Holding Companies** -- there is no single consolidated operating
  P&L to read a "free cash flow" from in the same sense the method
  assumes; the company's own economics are about capital allocation
  across subsidiaries/positions, not one operating cash-flow stream.

**No alternative valuation model is built here.** For `POOR_FIT`
families, the honest answer is the disclosure itself -- "Unknown is
better than false precision" (the brief's own instruction). This
module never changes what `FCF_YIELD_RELATIVE` itself computes; it
only classifies whether the reader should trust that computation as a
primary valuation lens for this company's industry.
"""
from __future__ import annotations

from atlas.alpha.industry_intelligence.models import IndustryFamily, IndustryValuationNote, ValuationApplicability

__all__ = ["assess_valuation_applicability"]

POOR_FIT_REASONING = {
    IndustryFamily.BANKS: (
        "A bank's balance sheet is its business -- free cash flow relative to market "
        "cap does not answer the same question it does for an operating company."
    ),
    IndustryFamily.INSURANCE: (
        "An insurer's economics are driven by underwriting and float, not a "
        "representative operating free-cash-flow figure."
    ),
    IndustryFamily.REAL_ESTATE: (
        "GAAP earnings and free cash flow are structurally distorted by depreciation "
        "on long-lived real estate assets; the standard REIT metric (funds from "
        "operations) is a different figure this method does not compute."
    ),
    IndustryFamily.HOLDING_COMPANIES: (
        "A capital-allocation holding company has no single consolidated operating "
        "cash-flow stream this method's own model assumes."
    ),
}

USEFUL_WITH_CAVEATS_REASONING = {
    IndustryFamily.UTILITIES: (
        "Free cash flow is a real, meaningful figure here, but large, lumpy, "
        "regulated capex programs make period-to-period FCF noisier than a typical "
        "operating company, widening the historical range this method reverts toward."
    ),
    IndustryFamily.ASSET_MANAGERS: (
        "Free cash flow is real and meaningful, but AUM-driven revenue swings with "
        "market levels can move the current yield independent of the underlying "
        "business's own quality."
    ),
}


def assess_valuation_applicability(family: IndustryFamily) -> IndustryValuationNote:
    """Deterministic: identical `family` always produces an identical
    `IndustryValuationNote`."""
    if family in POOR_FIT_REASONING:
        return IndustryValuationNote(
            applicability=ValuationApplicability.POOR_FIT, reasoning=POOR_FIT_REASONING[family]
        )
    if family in USEFUL_WITH_CAVEATS_REASONING:
        return IndustryValuationNote(
            applicability=ValuationApplicability.USEFUL_WITH_CAVEATS,
            reasoning=USEFUL_WITH_CAVEATS_REASONING[family],
        )
    if family in (IndustryFamily.UNCLASSIFIED, IndustryFamily.UNKNOWN):
        return IndustryValuationNote(
            applicability=ValuationApplicability.UNKNOWN,
            reasoning="Industry family is not classified -- no basis to assess fit.",
        )
    return IndustryValuationNote(
        applicability=ValuationApplicability.APPROPRIATE,
        reasoning="An operating company with a representative free-cash-flow figure -- the method's own intended use case.",
    )

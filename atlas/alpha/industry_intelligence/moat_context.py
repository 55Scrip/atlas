"""Moat Context (Calibration Phase 7, Phase 6) -- Business Quality
integration.

Reuses Calibration Phase 5's real `MoatAssessment` directly -- never
recomputed, never overridden. This module adds one further, honest
layer: for each industry family, which qualitative moat-evidence
*types* would be most relevant to look for, given that industry's own
economics. **Always phrased as "this is the evidence type that would
matter here," never "this company has it"** -- Atlas has no direct
data source for any of these (the identical disclosed gap
`atlas.alpha.business_quality_assessment.moat.UNASSESSED_MOAT
_DIMENSIONS` already names generically; this module makes the same
disclosure industry-specific rather than generic, without fabricating
a verdict).

Families with no single dominant moat-evidence type in the brief's own
economics research get an empty `relevant_evidence_types` -- honestly
disclosing "no distinguishing evidence type identified" rather than
forcing every family into this scheme.
"""
from __future__ import annotations

from atlas.alpha.industry_intelligence.models import IndustryFamily, IndustryMoatContext

__all__ = ["derive_moat_context"]

RELEVANT_EVIDENCE: dict[IndustryFamily, tuple[str, ...]] = {
    IndustryFamily.PAYMENTS: (
        ("network_effects", "acceptance_density"),
        "Payments networks compound through two-sided network effects -- "
        "acceptance density on the merchant side and adoption on the cardholder/user "
        "side reinforcing each other.",
    ),
    IndustryFamily.LUXURY: (
        ("brand_strength",),
        "Luxury pricing power is typically defended by brand scarcity and perceived "
        "exclusivity, not cost leadership or switching costs.",
    ),
    IndustryFamily.SEMICONDUCTORS: (
        ("technology_leadership", "ecosystem"),
        "Semiconductor moats are typically defended by process/technology leadership "
        "and ecosystem position (design wins, tooling lock-in), not scale alone.",
    ),
    IndustryFamily.INDUSTRIALS: (
        ("distribution", "switching_costs"),
        "Industrial moats typically come from an installed base creating aftermarket/"
        "service revenue and switching costs from integration into a customer's own "
        "operating processes.",
    ),
    IndustryFamily.PHARMA_BIOTECH: (
        ("regulatory_barriers",),
        "Pharmaceutical moats are typically time-boxed by patent-protected "
        "exclusivity and regulatory approval barriers, not a durable structural "
        "advantage independent of any single product's patent life.",
    ),
    IndustryFamily.INTERNET_PLATFORMS: (
        ("network_effects", "ecosystem"),
        "Platform moats are typically defended by user/engagement network effects "
        "and ecosystem lock-in.",
    ),
    IndustryFamily.SOFTWARE: (
        ("switching_costs",),
        "Software moats are typically defended by switching costs from workflow "
        "integration and data lock-in, not brand or scale.",
    ),
    IndustryFamily.MEDICAL_DEVICES: (
        ("switching_costs", "regulatory_barriers"),
        "Medical device moats typically come from clinical workflow integration "
        "(switching costs) and regulatory approval barriers to a competing device.",
    ),
    IndustryFamily.UTILITIES: (
        ("regulatory_barriers",),
        "Regulated utility moats come from the regulatory franchise itself (an "
        "exclusive service territory), not competitive dynamics in the usual sense.",
    ),
}


def derive_moat_context(family: IndustryFamily) -> IndustryMoatContext:
    """Deterministic: identical `family` always produces an identical
    `IndustryMoatContext`."""
    if family in RELEVANT_EVIDENCE:
        evidence_types, reasoning = RELEVANT_EVIDENCE[family]
        return IndustryMoatContext(relevant_evidence_types=evidence_types, reasoning=reasoning)
    return IndustryMoatContext(
        relevant_evidence_types=(),
        reasoning="No single dominant moat-evidence type identified for this industry family.",
    )

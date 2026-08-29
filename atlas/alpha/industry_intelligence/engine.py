"""Industry Context integration (Calibration Phase 7) -- combines
classification with every interpretation layer into one
`IndustryContext`, without replacing any of them.
"""
from __future__ import annotations

from atlas.alpha.industry_intelligence.capital_allocation_context import interpret_leverage
from atlas.alpha.industry_intelligence.classification import classify_industry
from atlas.alpha.industry_intelligence.models import IndustryContext
from atlas.alpha.industry_intelligence.moat_context import derive_moat_context
from atlas.alpha.industry_intelligence.support import industry_support_level
from atlas.alpha.industry_intelligence.valuation_context import assess_valuation_applicability

__all__ = ["derive_industry_context"]


def derive_industry_context(sector: str | None, industry: str | None) -> IndustryContext:
    """Deterministic: identical `(sector, industry)` always produces an
    identical `IndustryContext`."""
    classification = classify_industry(sector, industry)
    family = classification.family
    return IndustryContext(
        classification=classification,
        support_level=industry_support_level(family),
        valuation_note=assess_valuation_applicability(family),
        leverage_note=interpret_leverage(family),
        moat_context=derive_moat_context(family),
    )

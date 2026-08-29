"""Industry Intelligence (Calibration Phase 7).

Answers "does this generic signal need industry context to be read
correctly" -- never replaces a generic engine's own output, never
fabricates evidence Atlas does not have, never asserts a company
property merely because it is common in that company's industry. See
`docs/Calibration-Phase-7-Industry-Intelligence.md` for the full
research, model, and architecture rationale.

A closed `IndustryFamily` classification (from Alpha Vantage's own real
`sector`/`industry` strings, translated the same way `atlas.alpha
.canonical_security_gate`'s `SecurityType` translation already
establishes) feeds three independent, deterministic interpretation
layers -- Valuation Applicability, Leverage Interpretation, Moat
Context -- each attached alongside, never instead of, the generic
signal it annotates.
"""
from __future__ import annotations

from .capital_allocation_context import interpret_leverage
from .classification import classify_industry
from .engine import derive_industry_context
from .models import (
    IndustryClassification,
    IndustryContext,
    IndustryFamily,
    IndustryLeverageNote,
    IndustryMoatContext,
    IndustrySupportLevel,
    IndustryValuationNote,
    LeverageInterpretation,
    ValuationApplicability,
)
from .moat_context import derive_moat_context
from .service import IndustryIntelligenceService
from .support import industry_support_level
from .valuation_context import assess_valuation_applicability

__all__ = [
    "classify_industry",
    "derive_industry_context",
    "derive_moat_context",
    "assess_valuation_applicability",
    "interpret_leverage",
    "industry_support_level",
    "IndustryClassification",
    "IndustryContext",
    "IndustryFamily",
    "IndustryIntelligenceService",
    "IndustryLeverageNote",
    "IndustryMoatContext",
    "IndustrySupportLevel",
    "IndustryValuationNote",
    "LeverageInterpretation",
    "ValuationApplicability",
]

"""Tests for `atlas.alpha.industry_intelligence.engine
.derive_industry_context` -- the full integration, exercised end to
end from raw sector/industry strings through every interpretation
layer."""
from __future__ import annotations

from atlas.alpha.industry_intelligence.engine import derive_industry_context
from atlas.alpha.industry_intelligence.models import (
    IndustryFamily,
    IndustrySupportLevel,
    LeverageInterpretation,
    ValuationApplicability,
)


class TestFullIntegration:
    def test_a_bank_gets_poor_fit_valuation_and_metric_not_appropriate_leverage(self):
        context = derive_industry_context("FINANCIAL SERVICES", "BANKS - REGIONAL")
        assert context.classification.family is IndustryFamily.BANKS
        assert context.support_level is IndustrySupportLevel.STRONG
        assert context.valuation_note.applicability is ValuationApplicability.POOR_FIT
        assert context.leverage_note.interpretation is LeverageInterpretation.METRIC_NOT_APPROPRIATE

    def test_a_utility_gets_useful_with_caveats_valuation_and_structurally_normal_leverage(self):
        context = derive_industry_context("UTILITIES", "UTILITIES - REGULATED ELECTRIC")
        assert context.classification.family is IndustryFamily.UTILITIES
        assert context.valuation_note.applicability is ValuationApplicability.USEFUL_WITH_CAVEATS
        assert context.leverage_note.interpretation is LeverageInterpretation.STRUCTURALLY_NORMAL

    def test_no_company_profile_at_all_yields_a_fully_honest_unknown_context(self):
        context = derive_industry_context(None, None)
        assert context.classification.family is IndustryFamily.UNKNOWN
        assert context.support_level is IndustrySupportLevel.UNSUPPORTED
        assert context.valuation_note.applicability is ValuationApplicability.UNKNOWN
        assert context.leverage_note.interpretation is LeverageInterpretation.UNKNOWN
        assert context.moat_context.relevant_evidence_types == ()


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_context(self):
        first = derive_industry_context("TECHNOLOGY", "SOFTWARE - INFRASTRUCTURE")
        second = derive_industry_context("TECHNOLOGY", "SOFTWARE - INFRASTRUCTURE")
        assert first == second

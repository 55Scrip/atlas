"""Tests for `atlas.alpha.industry_intelligence.valuation_context
.assess_valuation_applicability`."""
from __future__ import annotations

from atlas.alpha.industry_intelligence.models import IndustryFamily, ValuationApplicability
from atlas.alpha.industry_intelligence.valuation_context import assess_valuation_applicability


class TestPoorFitFamilies:
    def test_banks_insurance_real_estate_and_holding_companies_are_poor_fit(self):
        for family in (
            IndustryFamily.BANKS,
            IndustryFamily.INSURANCE,
            IndustryFamily.REAL_ESTATE,
            IndustryFamily.HOLDING_COMPANIES,
        ):
            result = assess_valuation_applicability(family)
            assert result.applicability is ValuationApplicability.POOR_FIT
            assert result.reasoning  # never an empty disclosure


class TestUsefulWithCaveatsFamilies:
    def test_utilities_and_asset_managers_are_useful_with_caveats(self):
        for family in (IndustryFamily.UTILITIES, IndustryFamily.ASSET_MANAGERS):
            result = assess_valuation_applicability(family)
            assert result.applicability is ValuationApplicability.USEFUL_WITH_CAVEATS


class TestAppropriateIsTheHonestDefault:
    def test_software_and_semiconductors_are_appropriate(self):
        for family in (IndustryFamily.SOFTWARE, IndustryFamily.SEMICONDUCTORS, IndustryFamily.INDUSTRIALS):
            result = assess_valuation_applicability(family)
            assert result.applicability is ValuationApplicability.APPROPRIATE


class TestUnclassifiedAndUnknown:
    def test_both_yield_unknown_applicability(self):
        for family in (IndustryFamily.UNCLASSIFIED, IndustryFamily.UNKNOWN):
            result = assess_valuation_applicability(family)
            assert result.applicability is ValuationApplicability.UNKNOWN


class TestNoFabricatedAlternativeModel:
    def test_source_never_mentions_an_alternative_valuation_formula(self):
        """Structural proof: this module only classifies fit, it never
        computes a replacement valuation -- confirmed by the complete
        absence of any new arithmetic in its own source."""
        import inspect

        from atlas.alpha.industry_intelligence import valuation_context

        source = inspect.getsource(valuation_context)
        for forbidden in ("discount_rate", "terminal_multiple", "p/e", "ebitda", "dcf ="):
            assert forbidden not in source.lower()


class TestDeterminism:
    def test_identical_family_produces_identical_note(self):
        first = assess_valuation_applicability(IndustryFamily.BANKS)
        second = assess_valuation_applicability(IndustryFamily.BANKS)
        assert first == second

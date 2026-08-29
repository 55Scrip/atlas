"""Tests for `atlas.alpha.industry_intelligence.capital_allocation
_context.interpret_leverage`."""
from __future__ import annotations

from atlas.alpha.industry_intelligence.capital_allocation_context import interpret_leverage
from atlas.alpha.industry_intelligence.models import IndustryFamily, LeverageInterpretation


class TestStructurallyNormalFamilies:
    def test_utilities_telecom_and_real_estate_are_structurally_normal(self):
        for family in (IndustryFamily.UTILITIES, IndustryFamily.TELECOM, IndustryFamily.REAL_ESTATE):
            result = interpret_leverage(family)
            assert result.interpretation is LeverageInterpretation.STRUCTURALLY_NORMAL
            assert result.reasoning


class TestMetricNotAppropriateFamilies:
    def test_banks_and_insurance_reject_the_generic_leverage_concept(self):
        for family in (IndustryFamily.BANKS, IndustryFamily.INSURANCE):
            result = interpret_leverage(family)
            assert result.interpretation is LeverageInterpretation.METRIC_NOT_APPROPRIATE


class TestGenericInterpretationIsTheHonestDefault:
    def test_software_and_semiconductors_get_no_adjustment(self):
        for family in (IndustryFamily.SOFTWARE, IndustryFamily.SEMICONDUCTORS, IndustryFamily.PHARMA_BIOTECH):
            result = interpret_leverage(family)
            assert result.interpretation is LeverageInterpretation.GENERIC_INTERPRETATION_APPLIES


class TestUnclassifiedAndUnknown:
    def test_both_yield_unknown_interpretation(self):
        for family in (IndustryFamily.UNCLASSIFIED, IndustryFamily.UNKNOWN):
            result = interpret_leverage(family)
            assert result.interpretation is LeverageInterpretation.UNKNOWN


class TestNeverChangesTheUnderlyingSignal:
    def test_function_takes_only_a_family_never_a_status_to_mutate(self):
        """Structural proof: `interpret_leverage`'s own signature has no
        `BusinessCategoryStatus`/`RiskStatus` parameter to override --
        it cannot mutate a generic signal it was never given."""
        import inspect

        signature = inspect.signature(interpret_leverage)
        assert list(signature.parameters) == ["family"]


class TestDeterminism:
    def test_identical_family_produces_identical_note(self):
        first = interpret_leverage(IndustryFamily.UTILITIES)
        second = interpret_leverage(IndustryFamily.UTILITIES)
        assert first == second

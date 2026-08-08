"""Tests for `atlas.analysis_engine.contracts` (ATLAS-020 Phase 8,
extended ATLAS-025 Phase 3) -- confirms the `RiskCategory` taxonomy is
exactly the closed set this sprint designed (the original sprint's
eight suggested categories, plus `THESIS_RISK` (ATLAS-020) and
`VALUATION_RISK` (ATLAS-025)) and that `CapabilityStatus` stays a
single-member "not yet implemented" marker, never a general status
enum."""
from __future__ import annotations

from atlas.analysis_engine.contracts import CapabilityStatus, RiskCategory


class TestRiskCategoryTaxonomy:
    def test_exactly_ten_members(self):
        assert len(RiskCategory) == 10

    def test_contains_all_eight_sprint_suggested_categories(self):
        expected = {
            "business_risk",
            "execution_risk",
            "financial_risk",
            "industry_risk",
            "macro_risk",
            "portfolio_risk",
            "behavioral_risk",
            "regulatory_risk",
        }
        assert expected.issubset({member.value for member in RiskCategory})

    def test_contains_the_two_self_added_categories(self):
        assert RiskCategory.THESIS_RISK.value == "thesis_risk"
        assert RiskCategory.VALUATION_RISK.value == "valuation_risk"

    def test_is_a_closed_string_enum(self):
        assert issubclass(RiskCategory, str)
        for member in RiskCategory:
            assert isinstance(member.value, str)


class TestCapabilityStatus:
    def test_exactly_one_member(self):
        assert len(CapabilityStatus) == 1
        assert CapabilityStatus.NOT_YET_IMPLEMENTED.value == "not_yet_implemented"

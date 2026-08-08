"""Tests for `atlas.analysis_engine.contracts` (ATLAS-020 Phase 8) --
confirms the `RiskCategory` taxonomy is exactly the closed set this
sprint designed (the sprint's own eight suggested categories plus the
one this package adds, `THESIS_RISK`) and that `CapabilityStatus`
stays a single-member "not yet implemented" marker, never a general
status enum."""
from __future__ import annotations

from atlas.analysis_engine.contracts import CapabilityStatus, RiskCategory


class TestRiskCategoryTaxonomy:
    def test_exactly_nine_members(self):
        assert len(RiskCategory) == 9

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

    def test_contains_the_one_self_added_producible_category(self):
        assert RiskCategory.THESIS_RISK.value == "thesis_risk"

    def test_is_a_closed_string_enum(self):
        assert issubclass(RiskCategory, str)
        for member in RiskCategory:
            assert isinstance(member.value, str)


class TestCapabilityStatus:
    def test_exactly_one_member(self):
        assert len(CapabilityStatus) == 1
        assert CapabilityStatus.NOT_YET_IMPLEMENTED.value == "not_yet_implemented"

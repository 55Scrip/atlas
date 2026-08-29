"""Tests for `atlas.alpha.industry_intelligence.support
.industry_support_level` -- generated directly from the real rule
tables, never asserted independently."""
from __future__ import annotations

from atlas.alpha.industry_intelligence.capital_allocation_context import (
    METRIC_NOT_APPROPRIATE_REASONING,
    STRUCTURALLY_NORMAL_REASONING,
)
from atlas.alpha.industry_intelligence.models import IndustryFamily, IndustrySupportLevel
from atlas.alpha.industry_intelligence.moat_context import RELEVANT_EVIDENCE
from atlas.alpha.industry_intelligence.support import industry_support_level
from atlas.alpha.industry_intelligence.valuation_context import POOR_FIT_REASONING, USEFUL_WITH_CAVEATS_REASONING


class TestStrongRequiresARealDedicatedRule:
    def test_every_family_with_a_valuation_rule_is_strong(self):
        for family in (*POOR_FIT_REASONING, *USEFUL_WITH_CAVEATS_REASONING):
            assert industry_support_level(family) is IndustrySupportLevel.STRONG

    def test_every_family_with_a_leverage_rule_is_strong(self):
        for family in (*STRUCTURALLY_NORMAL_REASONING, *METRIC_NOT_APPROPRIATE_REASONING):
            assert industry_support_level(family) is IndustrySupportLevel.STRONG

    def test_every_family_with_a_moat_context_rule_is_strong(self):
        for family in RELEVANT_EVIDENCE:
            assert industry_support_level(family) is IndustrySupportLevel.STRONG


class TestPartialIsAClassifiedFamilyWithNoDedicatedRuleAnywhere:
    def test_a_family_absent_from_every_rule_table_is_partial(self):
        all_dedicated = {
            *POOR_FIT_REASONING,
            *USEFUL_WITH_CAVEATS_REASONING,
            *STRUCTURALLY_NORMAL_REASONING,
            *METRIC_NOT_APPROPRIATE_REASONING,
            *RELEVANT_EVIDENCE,
        }
        undedicated = [
            f
            for f in IndustryFamily
            if f not in all_dedicated and f not in (IndustryFamily.UNCLASSIFIED, IndustryFamily.UNKNOWN)
        ]
        assert undedicated, "expected at least one family with no dedicated rule, to prove PARTIAL is reachable"
        for family in undedicated:
            assert industry_support_level(family) is IndustrySupportLevel.PARTIAL


class TestUnsupported:
    def test_unclassified_and_unknown_are_always_unsupported(self):
        assert industry_support_level(IndustryFamily.UNCLASSIFIED) is IndustrySupportLevel.UNSUPPORTED
        assert industry_support_level(IndustryFamily.UNKNOWN) is IndustrySupportLevel.UNSUPPORTED


class TestDeterminism:
    def test_identical_family_produces_identical_level(self):
        first = industry_support_level(IndustryFamily.BANKS)
        second = industry_support_level(IndustryFamily.BANKS)
        assert first is second

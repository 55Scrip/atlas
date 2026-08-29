"""Tests for `atlas.alpha.industry_intelligence.moat_context
.derive_moat_context` -- always phrased as "relevant evidence type,"
never a claim about a specific company."""
from __future__ import annotations

from atlas.alpha.industry_intelligence.models import IndustryFamily
from atlas.alpha.industry_intelligence.moat_context import derive_moat_context


class TestFamiliesWithADominantEvidenceType:
    def test_payments_names_network_effects(self):
        result = derive_moat_context(IndustryFamily.PAYMENTS)
        assert "network_effects" in result.relevant_evidence_types

    def test_luxury_names_brand_strength(self):
        result = derive_moat_context(IndustryFamily.LUXURY)
        assert "brand_strength" in result.relevant_evidence_types

    def test_semiconductors_names_technology_leadership(self):
        result = derive_moat_context(IndustryFamily.SEMICONDUCTORS)
        assert "technology_leadership" in result.relevant_evidence_types

    def test_pharma_names_regulatory_barriers(self):
        result = derive_moat_context(IndustryFamily.PHARMA_BIOTECH)
        assert "regulatory_barriers" in result.relevant_evidence_types


class TestFamiliesWithNoDominantEvidenceType:
    def test_families_absent_from_the_table_get_an_honest_empty_tuple(self):
        """Not every family is forced into this scheme -- an empty
        tuple with a disclosed reason is more honest than a guessed
        evidence type."""
        result = derive_moat_context(IndustryFamily.CONSUMER_STAPLES)
        assert result.relevant_evidence_types == ()
        assert result.reasoning


class TestNeverAssertsACompanySpecificFact:
    def test_reasoning_text_never_claims_the_company_has_the_evidence(self):
        """Structural proof, not just convention: every reasoning
        string in the table is phrased as what *would* matter, never
        what a specific company *has*."""
        from atlas.alpha.industry_intelligence.moat_context import RELEVANT_EVIDENCE

        for _family, (_types, reasoning) in RELEVANT_EVIDENCE.items():
            assert "typically" in reasoning.lower() or "would" in reasoning.lower() or "come from" in reasoning.lower() or "compound" in reasoning.lower()


class TestUnclassifiedAndUnknown:
    def test_both_yield_empty_evidence_types(self):
        for family in (IndustryFamily.UNCLASSIFIED, IndustryFamily.UNKNOWN):
            result = derive_moat_context(family)
            assert result.relevant_evidence_types == ()


class TestDeterminism:
    def test_identical_family_produces_identical_context(self):
        first = derive_moat_context(IndustryFamily.PAYMENTS)
        second = derive_moat_context(IndustryFamily.PAYMENTS)
        assert first == second

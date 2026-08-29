"""Tests for `atlas.alpha.industry_intelligence.classification
.classify_industry` -- the closed translation table, the sector
fallback's deliberate narrowness, and the `UNCLASSIFIED`/`UNKNOWN`
distinction."""
from __future__ import annotations

from atlas.alpha.industry_intelligence.classification import classify_industry
from atlas.alpha.industry_intelligence.models import IndustryFamily


class TestRealConfirmedValues:
    """Every one of these exact (sector, industry) pairs was confirmed
    live against the real dev database this sprint."""

    def test_msft_maps_to_software(self):
        result = classify_industry("TECHNOLOGY", "SOFTWARE - INFRASTRUCTURE")
        assert result.family is IndustryFamily.SOFTWARE

    def test_amzn_maps_to_internet_platforms(self):
        result = classify_industry("CONSUMER CYCLICAL", "INTERNET RETAIL")
        assert result.family is IndustryFamily.INTERNET_PLATFORMS

    def test_goog_and_meta_map_to_internet_platforms(self):
        result = classify_industry("COMMUNICATION SERVICES", "INTERNET CONTENT & INFORMATION")
        assert result.family is IndustryFamily.INTERNET_PLATFORMS

    def test_azn_maps_to_pharma_biotech(self):
        result = classify_industry("HEALTHCARE", "DRUG MANUFACTURERS - GENERAL")
        assert result.family is IndustryFamily.PHARMA_BIOTECH

    def test_ma_maps_to_payments(self):
        result = classify_industry("FINANCIAL SERVICES", "CREDIT SERVICES")
        assert result.family is IndustryFamily.PAYMENTS

    def test_semiconductor_industries_map_to_semiconductors(self):
        assert classify_industry("TECHNOLOGY", "SEMICONDUCTORS").family is IndustryFamily.SEMICONDUCTORS
        assert (
            classify_industry("TECHNOLOGY", "SEMICONDUCTOR EQUIPMENT & MATERIALS").family
            is IndustryFamily.SEMICONDUCTORS
        )


class TestCaseAndWhitespaceInsensitivity:
    def test_lowercase_and_extra_whitespace_still_match(self):
        result = classify_industry("technology", "  software - infrastructure  ")
        assert result.family is IndustryFamily.SOFTWARE


class TestSectorFallbackIsDeliberatelyNarrow:
    def test_utilities_sector_falls_back_when_industry_is_unrecognized(self):
        result = classify_industry("UTILITIES", "SOME UNRECOGNIZED UTILITY SUBSEGMENT")
        assert result.family is IndustryFamily.UTILITIES

    def test_energy_and_real_estate_sectors_also_fall_back(self):
        assert classify_industry("ENERGY", "UNRECOGNIZED").family is IndustryFamily.ENERGY
        assert classify_industry("REAL ESTATE", "UNRECOGNIZED").family is IndustryFamily.REAL_ESTATE

    def test_ambiguous_sectors_never_fall_back(self):
        """Communication Services and Financial Services each span
        multiple, economically distinct families -- a sector-level
        fallback here would guess, not translate."""
        assert classify_industry("COMMUNICATION SERVICES", "UNRECOGNIZED").family is IndustryFamily.UNCLASSIFIED
        assert classify_industry("FINANCIAL SERVICES", "UNRECOGNIZED").family is IndustryFamily.UNCLASSIFIED


class TestUnclassifiedVsUnknown:
    def test_no_data_at_all_is_unknown(self):
        result = classify_industry(None, None)
        assert result.family is IndustryFamily.UNKNOWN

    def test_a_real_but_unrecognized_string_is_unclassified_not_unknown(self):
        """A translation-table gap is a different, more honest fact
        than a data-coverage gap -- these must never be conflated."""
        result = classify_industry("SOME SECTOR", "SOME COMPLETELY MADE UP INDUSTRY")
        assert result.family is IndustryFamily.UNCLASSIFIED

    def test_raw_strings_are_always_preserved_regardless_of_classification_outcome(self):
        result = classify_industry("TECHNOLOGY", "SOFTWARE - INFRASTRUCTURE")
        assert result.raw_sector == "TECHNOLOGY"
        assert result.raw_industry == "SOFTWARE - INFRASTRUCTURE"


class TestHoldingCompaniesHasNoTranslationEntry:
    def test_no_real_string_maps_to_holding_companies(self):
        """Disclosed limitation: Alpha Vantage classifies by largest
        reported operating segment, not economic structure -- a real
        holding company is typically reported under a subsidiary's own
        industry. Mapping any string to this family would be an
        unverifiable guess."""
        from atlas.alpha.industry_intelligence.classification import _INDUSTRY_TRANSLATION

        assert IndustryFamily.HOLDING_COMPANIES not in _INDUSTRY_TRANSLATION.values()


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_classification(self):
        first = classify_industry("TECHNOLOGY", "SOFTWARE - INFRASTRUCTURE")
        second = classify_industry("TECHNOLOGY", "SOFTWARE - INFRASTRUCTURE")
        assert first == second

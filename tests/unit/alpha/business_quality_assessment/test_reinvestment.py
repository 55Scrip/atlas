"""Tests for `atlas.alpha.business_quality_assessment.reinvestment
.assess_reinvestment` -- every evidence signal exercised, plus the
deliberate asymmetry on `reinvestment_discipline` (only `RISING` is
rewarded; `FALLING` is honestly `UNKNOWN`, never penalized)."""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.models import ReinvestmentEvidenceKind, ReinvestmentOpportunityLevel
from atlas.alpha.business_quality_assessment.reinvestment import UNASSESSED_REINVESTMENT_DIMENSIONS, assess_reinvestment
from atlas.alpha.investment_case.financial_statement_intelligence import TrendDirection
from tests.unit.alpha.business_quality_assessment._fixtures import (
    business_quality_from,
    declining_volatile_records,
    steady_growing_records,
)


class TestNoEvidence:
    def test_no_records_at_all_is_unknown(self):
        result = assess_reinvestment(business_quality_from(()), reinvestment_discipline=TrendDirection.INSUFFICIENT_DATA)
        assert result.level is ReinvestmentOpportunityLevel.UNKNOWN
        assert result.supporting_evidence == ()


class TestUnassessedDimensionsAlwaysDisclosed:
    def test_present_regardless_of_level(self):
        result = assess_reinvestment(business_quality_from(steady_growing_records()), reinvestment_discipline=TrendDirection.RISING)
        assert result.unassessed_dimensions == UNASSESSED_REINVESTMENT_DIMENSIONS
        assert "addressable_market_size" in UNASSESSED_REINVESTMENT_DIMENSIONS


class TestExcellentRequiresAllFourSignals:
    def test_durable_growth_efficient_capital_cash_generation_and_rising_reinvestment_is_excellent(self):
        quality = business_quality_from(steady_growing_records())
        result = assess_reinvestment(quality, reinvestment_discipline=TrendDirection.RISING)
        assert result.level is ReinvestmentOpportunityLevel.EXCELLENT
        assert ReinvestmentEvidenceKind.DURABLE_GROWTH_ACROSS_MULTIPLE_METRICS in result.supporting_evidence
        assert ReinvestmentEvidenceKind.RISING_RETURNS_ON_CAPITAL in result.supporting_evidence
        assert ReinvestmentEvidenceKind.SUSTAINED_CASH_GENERATION in result.supporting_evidence
        assert ReinvestmentEvidenceKind.RISING_REINVESTMENT_ACTIVITY in result.supporting_evidence


class TestFallingReinvestmentDisciplineIsNeverPenalized:
    def test_falling_reinvestment_discipline_still_reaches_good_not_downgraded(self):
        """Falling capex could mean genuine capital discipline or a
        saturated market -- Atlas cannot honestly tell the two apart
        without segment/TAM data, so `FALLING` never subtracts from an
        otherwise-strong picture; the same three underlying signals
        that gave `EXCELLENT` above still give `GOOD`, not less."""
        quality = business_quality_from(steady_growing_records())
        result = assess_reinvestment(quality, reinvestment_discipline=TrendDirection.FALLING)
        assert result.level is ReinvestmentOpportunityLevel.GOOD
        assert ReinvestmentEvidenceKind.RISING_REINVESTMENT_ACTIVITY not in result.supporting_evidence

    def test_missing_reinvestment_discipline_data_behaves_identically_to_falling(self):
        quality = business_quality_from(steady_growing_records())
        falling = assess_reinvestment(quality, reinvestment_discipline=TrendDirection.FALLING)
        insufficient = assess_reinvestment(quality, reinvestment_discipline=TrendDirection.INSUFFICIENT_DATA)
        assert falling.level is insufficient.level is ReinvestmentOpportunityLevel.GOOD


class TestLimitedRequiresNegativesToOutweighPositives:
    def test_volatile_declining_business_is_limited(self):
        quality = business_quality_from(declining_volatile_records())
        result = assess_reinvestment(quality, reinvestment_discipline=TrendDirection.FALLING)
        assert result.level is ReinvestmentOpportunityLevel.LIMITED
        assert ReinvestmentEvidenceKind.FALLING_RETURNS_ON_CAPITAL in result.supporting_evidence
        assert ReinvestmentEvidenceKind.INCONSISTENT_CASH_GENERATION in result.supporting_evidence

    def test_a_declining_business_with_rising_reinvestment_is_still_limited(self):
        """One real positive signal (rising reinvestment activity)
        does not outweigh two real negatives -- more capital being
        deployed into a deteriorating business is not itself good
        news."""
        quality = business_quality_from(declining_volatile_records())
        result = assess_reinvestment(quality, reinvestment_discipline=TrendDirection.RISING)
        assert result.level is ReinvestmentOpportunityLevel.LIMITED


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_assessment(self):
        quality = business_quality_from(steady_growing_records())
        first = assess_reinvestment(quality, reinvestment_discipline=TrendDirection.RISING)
        second = assess_reinvestment(quality, reinvestment_discipline=TrendDirection.RISING)
        assert first == second

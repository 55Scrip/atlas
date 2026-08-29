"""Tests for `atlas.alpha.business_quality_assessment.engine
.assess_business_quality` -- the integrated score's own combination
rule, driver derivation, and greatest-advantage/greatest-concern
tie-breaking, exercised directly against hand-built sub-assessments
(never through the full pipeline -- this is a decision-table test)."""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.engine import assess_business_quality
from atlas.alpha.business_quality_assessment.models import (
    BusinessQualityDriverKind,
    BusinessQualityLevel,
    ManagementAssessment,
    ManagementQualityLevel,
    MoatAssessment,
    MoatLevel,
    ReinvestmentAssessment,
    ReinvestmentOpportunityLevel,
)


def _moat(level: MoatLevel) -> MoatAssessment:
    return MoatAssessment(level=level, supporting_evidence=(), unassessed_dimensions=("market_share",))


def _management(level: ManagementQualityLevel) -> ManagementAssessment:
    return ManagementAssessment(level=level, dimensions=(), unassessed_dimensions=("governance",))


def _reinvestment(level: ReinvestmentOpportunityLevel) -> ReinvestmentAssessment:
    return ReinvestmentAssessment(level=level, supporting_evidence=(), unassessed_dimensions=("addressable_market_size",))


class TestOverallLevel:
    def test_all_three_unknown_is_unknown(self):
        result = assess_business_quality(_moat(MoatLevel.UNKNOWN), _management(ManagementQualityLevel.UNKNOWN), _reinvestment(ReinvestmentOpportunityLevel.UNKNOWN))
        assert result.overall_level is BusinessQualityLevel.UNKNOWN

    def test_all_three_moderate_is_moderate_not_unknown(self):
        """A real, computed `MODERATE`/`GOOD` reading is not the same
        as `UNKNOWN` -- an unremarkable-but-real business quality
        picture must read `MODERATE` overall, never silently downgraded
        to 'no evidence.'"""
        result = assess_business_quality(_moat(MoatLevel.MODERATE), _management(ManagementQualityLevel.MODERATE), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert result.overall_level is BusinessQualityLevel.MODERATE

    def test_two_strong_and_zero_negative_reaches_strong(self):
        result = assess_business_quality(_moat(MoatLevel.STRONG), _management(ManagementQualityLevel.STRONG), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert result.overall_level is BusinessQualityLevel.STRONG

    def test_all_three_strong_reaches_exceptional(self):
        result = assess_business_quality(_moat(MoatLevel.EXCEPTIONAL), _management(ManagementQualityLevel.STRONG), _reinvestment(ReinvestmentOpportunityLevel.EXCELLENT))
        assert result.overall_level is BusinessQualityLevel.EXCEPTIONAL

    def test_negatives_outweighing_positives_is_weak(self):
        result = assess_business_quality(_moat(MoatLevel.WEAK), _management(ManagementQualityLevel.WEAK), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert result.overall_level is BusinessQualityLevel.WEAK

    def test_one_strong_and_one_weak_is_moderate_not_weak(self):
        """Negatives must genuinely outweigh positives -- a tie is
        honestly mixed."""
        result = assess_business_quality(_moat(MoatLevel.STRONG), _management(ManagementQualityLevel.WEAK), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert result.overall_level is BusinessQualityLevel.MODERATE


class TestDriversAreNamedAndTraceable:
    def test_exceptional_moat_produces_the_named_strength_driver(self):
        result = assess_business_quality(_moat(MoatLevel.EXCEPTIONAL), _management(ManagementQualityLevel.MODERATE), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert len(result.strengths) == 1
        assert result.strengths[0].kind is BusinessQualityDriverKind.EXCEPTIONAL_COMPETITIVE_POSITION
        assert result.strengths[0].source == "moat.level"

    def test_weak_management_produces_the_named_weakness_driver(self):
        result = assess_business_quality(_moat(MoatLevel.MODERATE), _management(ManagementQualityLevel.WEAK), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert len(result.weaknesses) == 1
        assert result.weaknesses[0].kind is BusinessQualityDriverKind.WEAK_MANAGEMENT_QUALITY

    def test_moderate_and_unknown_produce_no_drivers_at_all(self):
        result = assess_business_quality(_moat(MoatLevel.MODERATE), _management(ManagementQualityLevel.UNKNOWN), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert result.strengths == ()
        assert result.weaknesses == ()


class TestGreatestAdvantageTieBreak:
    def test_exceptional_beats_strong_regardless_of_which_engine_it_came_from(self):
        result = assess_business_quality(_moat(MoatLevel.STRONG), _management(ManagementQualityLevel.EXCEPTIONAL), _reinvestment(ReinvestmentOpportunityLevel.GOOD))
        assert result.greatest_advantage.kind is BusinessQualityDriverKind.EXCEPTIONAL_MANAGEMENT_QUALITY

    def test_moat_wins_the_tie_over_management_and_reinvestment_at_equal_tier(self):
        result = assess_business_quality(_moat(MoatLevel.STRONG), _management(ManagementQualityLevel.STRONG), _reinvestment(ReinvestmentOpportunityLevel.GOOD))
        assert result.greatest_advantage.kind is BusinessQualityDriverKind.STRONG_COMPETITIVE_POSITION

    def test_no_strengths_yields_no_greatest_advantage(self):
        result = assess_business_quality(_moat(MoatLevel.MODERATE), _management(ManagementQualityLevel.MODERATE), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert result.greatest_advantage is None


class TestGreatestConcernTieBreak:
    def test_moat_wins_the_tie_over_management_and_reinvestment(self):
        result = assess_business_quality(_moat(MoatLevel.WEAK), _management(ManagementQualityLevel.WEAK), _reinvestment(ReinvestmentOpportunityLevel.LIMITED))
        assert result.greatest_concern.kind is BusinessQualityDriverKind.WEAK_COMPETITIVE_POSITION

    def test_no_weaknesses_yields_no_greatest_concern(self):
        result = assess_business_quality(_moat(MoatLevel.STRONG), _management(ManagementQualityLevel.MODERATE), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert result.greatest_concern is None


class TestUnknownsAreTheDeduplicatedUnion:
    def test_unknowns_combine_all_three_engines_own_disclosures(self):
        result = assess_business_quality(_moat(MoatLevel.MODERATE), _management(ManagementQualityLevel.MODERATE), _reinvestment(ReinvestmentOpportunityLevel.MODERATE))
        assert result.unknowns == ("addressable_market_size", "governance", "market_share")


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_assessment(self):
        first = assess_business_quality(_moat(MoatLevel.STRONG), _management(ManagementQualityLevel.STRONG), _reinvestment(ReinvestmentOpportunityLevel.GOOD))
        second = assess_business_quality(_moat(MoatLevel.STRONG), _management(ManagementQualityLevel.STRONG), _reinvestment(ReinvestmentOpportunityLevel.GOOD))
        assert first == second

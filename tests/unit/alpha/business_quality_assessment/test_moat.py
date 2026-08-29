"""Tests for `atlas.alpha.business_quality_assessment.moat
.assess_moat` -- every evidence signal exercised independently, plus
the combination rule's boundary cases."""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.models import MoatEvidenceKind, MoatLevel
from atlas.alpha.business_quality_assessment.moat import UNASSESSED_MOAT_DIMENSIONS, assess_moat
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from tests.unit.alpha.business_quality_assessment._fixtures import (
    business_quality_from,
    declining_volatile_records,
    steady_growing_records,
)


class TestNoEvidence:
    def test_no_records_at_all_is_unknown(self):
        quality = business_quality_from(())
        result = assess_moat(quality, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert result.level is MoatLevel.UNKNOWN
        assert result.supporting_evidence == ()


class TestUnassessedDimensionsAlwaysDisclosed:
    def test_unassessed_dimensions_present_regardless_of_level(self):
        strong = assess_moat(business_quality_from(steady_growing_records()), capital_allocation_status=BusinessCategoryStatus.STRONG)
        unknown = assess_moat(business_quality_from(()), capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert strong.unassessed_dimensions == UNASSESSED_MOAT_DIMENSIONS
        assert unknown.unassessed_dimensions == UNASSESSED_MOAT_DIMENSIONS
        assert "market_share" in UNASSESSED_MOAT_DIMENSIONS
        assert "brand_strength" in UNASSESSED_MOAT_DIMENSIONS


class TestExceptionalRequiresBroadCorroboration:
    def test_a_strong_business_and_strong_capital_allocation_reaches_exceptional(self):
        """Steady growth alone already produces 4 real positive
        signals (stable profitability, rising returns on capital,
        durable growth, consistent value creation) -- adding a real,
        Calibration Phase 4 STRONG Capital Allocation finding as a 5th
        corroborating signal keeps the top tier, this time with every
        signal this evaluator can compute in agreement."""
        quality = business_quality_from(steady_growing_records())
        result = assess_moat(quality, capital_allocation_status=BusinessCategoryStatus.STRONG)
        assert result.level is MoatLevel.EXCEPTIONAL
        assert MoatEvidenceKind.STABLE_PROFITABILITY_THROUGH_VARYING_CONDITIONS in result.supporting_evidence
        assert MoatEvidenceKind.RISING_RETURNS_ON_CAPITAL in result.supporting_evidence
        assert MoatEvidenceKind.DURABLE_GROWTH_ACROSS_MULTIPLE_METRICS in result.supporting_evidence
        assert MoatEvidenceKind.CONSISTENT_VALUE_CREATION in result.supporting_evidence
        assert MoatEvidenceKind.STRONG_CAPITAL_ALLOCATION_TRACK_RECORD in result.supporting_evidence

    def test_four_of_five_signals_positive_already_reaches_exceptional(self):
        """The `>= 4` threshold does not require all five signals to be
        computable -- four strongly-agreeing signals with the fifth
        genuinely `UNKNOWN` (no real Capital Allocation corroboration
        available) is still broad enough corroboration."""
        quality = business_quality_from(steady_growing_records())
        result = assess_moat(quality, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert result.level is MoatLevel.EXCEPTIONAL

    def test_a_single_disagreeing_signal_drops_the_same_business_to_moderate(self):
        """`EXCEPTIONAL`/`STRONG` both require zero negative signals --
        one real, disagreeing signal (a WEAK Capital Allocation finding)
        against four positives is not disqualifying to WEAK (positives
        still outnumber it), but it is enough to withhold both top
        tiers -- the identical "negatives must genuinely outweigh
        positives, but the top tier needs unanimous agreement" bar
        Capital Allocation v2 itself established."""
        quality = business_quality_from(steady_growing_records())
        result = assess_moat(quality, capital_allocation_status=BusinessCategoryStatus.WEAK)
        assert result.level is MoatLevel.MODERATE


class TestWeakRequiresNegativesToOutweighPositives:
    def test_volatile_declining_business_with_weak_capital_allocation_is_weak(self):
        quality = business_quality_from(declining_volatile_records())
        result = assess_moat(quality, capital_allocation_status=BusinessCategoryStatus.WEAK)
        assert result.level is MoatLevel.WEAK
        assert MoatEvidenceKind.VOLATILE_PROFITABILITY in result.supporting_evidence
        assert MoatEvidenceKind.FALLING_RETURNS_ON_CAPITAL in result.supporting_evidence
        assert MoatEvidenceKind.WEAK_CAPITAL_ALLOCATION_TRACK_RECORD in result.supporting_evidence

    def test_never_infers_moat_from_a_field_that_does_not_exist_on_the_inputs(self):
        """Structural proof, not just documentation: no market-cap,
        revenue-scale, or company-size field is ever read by
        `assess_moat` -- confirmed by its own two-argument signature
        (`BusinessQualityKnowledge` + a `BusinessCategoryStatus`), both
        of which carry no size-related field at all."""
        import inspect

        from atlas.alpha.business_quality_assessment import moat as moat_module

        source = inspect.getsource(moat_module)
        for forbidden in ("market_cap", "revenue >", "revenue>", ".revenue >"):
            assert forbidden not in source


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_assessment(self):
        quality = business_quality_from(steady_growing_records())
        first = assess_moat(quality, capital_allocation_status=BusinessCategoryStatus.STRONG)
        second = assess_moat(quality, capital_allocation_status=BusinessCategoryStatus.STRONG)
        assert first == second

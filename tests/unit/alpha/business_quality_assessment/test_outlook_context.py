"""Tests for `atlas.alpha.business_quality_assessment.outlook_context
.derive_outlook_quality_drivers` -- every Moat/Reinvestment level maps
to its own driver direction, `UNKNOWN` never constructs a driver at
all, and the function never touches anything beyond the two new,
informational `OutlookDriverKind` members."""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.models import (
    ManagementAssessment,
    ManagementQualityLevel,
    MoatAssessment,
    MoatLevel,
    ReinvestmentAssessment,
    ReinvestmentOpportunityLevel,
)
from atlas.alpha.business_quality_assessment.engine import assess_business_quality
from atlas.alpha.business_quality_assessment.outlook_context import derive_outlook_quality_drivers
from atlas.analysis_engine.outlook import DriverDirection, OutlookDriverKind


def _assessment(moat_level: MoatLevel, reinvestment_level: ReinvestmentOpportunityLevel):
    moat = MoatAssessment(level=moat_level, supporting_evidence=(), unassessed_dimensions=())
    management = ManagementAssessment(level=ManagementQualityLevel.UNKNOWN, dimensions=(), unassessed_dimensions=())
    reinvestment = ReinvestmentAssessment(level=reinvestment_level, supporting_evidence=(), unassessed_dimensions=())
    return assess_business_quality(moat, management, reinvestment)


class TestMoatDriver:
    def test_exceptional_and_strong_are_positive(self):
        for level in (MoatLevel.EXCEPTIONAL, MoatLevel.STRONG):
            drivers = derive_outlook_quality_drivers(_assessment(level, ReinvestmentOpportunityLevel.UNKNOWN))
            moat_driver = next(d for d in drivers if d.kind is OutlookDriverKind.MOAT)
            assert moat_driver.direction is DriverDirection.POSITIVE

    def test_moderate_is_neutral(self):
        drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.MODERATE, ReinvestmentOpportunityLevel.UNKNOWN))
        moat_driver = next(d for d in drivers if d.kind is OutlookDriverKind.MOAT)
        assert moat_driver.direction is DriverDirection.NEUTRAL

    def test_weak_is_negative(self):
        drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.WEAK, ReinvestmentOpportunityLevel.UNKNOWN))
        moat_driver = next(d for d in drivers if d.kind is OutlookDriverKind.MOAT)
        assert moat_driver.direction is DriverDirection.NEGATIVE

    def test_unknown_constructs_no_moat_driver_at_all(self):
        drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.UNKNOWN, ReinvestmentOpportunityLevel.UNKNOWN))
        assert not any(d.kind is OutlookDriverKind.MOAT for d in drivers)

    def test_source_finding_id_is_always_none(self):
        """Neither Moat nor Reinvestment is a single analysis_engine
        Finding -- this package's own synthesis, the same convention
        FCF_GROWTH_TREND/DEBT_TREND/MARGIN_TREND already use."""
        drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.STRONG, ReinvestmentOpportunityLevel.GOOD))
        assert all(d.source_finding_id is None for d in drivers)


class TestReinvestmentDriver:
    def test_excellent_and_good_are_positive(self):
        for level in (ReinvestmentOpportunityLevel.EXCELLENT, ReinvestmentOpportunityLevel.GOOD):
            drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.UNKNOWN, level))
            driver = next(d for d in drivers if d.kind is OutlookDriverKind.REINVESTMENT_OPPORTUNITY)
            assert driver.direction is DriverDirection.POSITIVE

    def test_moderate_is_neutral(self):
        drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.UNKNOWN, ReinvestmentOpportunityLevel.MODERATE))
        driver = next(d for d in drivers if d.kind is OutlookDriverKind.REINVESTMENT_OPPORTUNITY)
        assert driver.direction is DriverDirection.NEUTRAL

    def test_limited_is_negative(self):
        drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.UNKNOWN, ReinvestmentOpportunityLevel.LIMITED))
        driver = next(d for d in drivers if d.kind is OutlookDriverKind.REINVESTMENT_OPPORTUNITY)
        assert driver.direction is DriverDirection.NEGATIVE

    def test_unknown_constructs_no_reinvestment_driver_at_all(self):
        drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.UNKNOWN, ReinvestmentOpportunityLevel.UNKNOWN))
        assert not any(d.kind is OutlookDriverKind.REINVESTMENT_OPPORTUNITY for d in drivers)


class TestBothUnknownYieldsNoDrivers:
    def test_zero_drivers_when_both_are_unknown(self):
        drivers = derive_outlook_quality_drivers(_assessment(MoatLevel.UNKNOWN, ReinvestmentOpportunityLevel.UNKNOWN))
        assert drivers == ()


class TestDeterminism:
    def test_identical_inputs_produce_identical_drivers(self):
        assessment = _assessment(MoatLevel.STRONG, ReinvestmentOpportunityLevel.GOOD)
        first = derive_outlook_quality_drivers(assessment)
        second = derive_outlook_quality_drivers(assessment)
        assert first == second

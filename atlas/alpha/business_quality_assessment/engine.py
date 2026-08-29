"""Business Quality Score (Calibration Phase 5, Phase 6) -- integrates
Moat, Management, and Reinvestment into one `BusinessQualityAssessment`
without replacing any of them. The score summarizes the underlying
analysis; every driver it names is a direct read of one real
sub-assessment field, never invented commentary (Phase 8's own "drivers
must be backed by actual engine outputs").
"""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.models import (
    BusinessQualityAssessment,
    BusinessQualityDriver,
    BusinessQualityDriverKind,
    BusinessQualityLevel,
    ManagementAssessment,
    ManagementQualityLevel,
    MoatAssessment,
    MoatLevel,
    ReinvestmentAssessment,
    ReinvestmentOpportunityLevel,
)

__all__ = ["assess_business_quality"]

_MIN_STRONG_FOR_EXCEPTIONAL = 3
_MIN_STRONG_FOR_STRONG = 2

# Priority order for tie-breaking `greatest_advantage`/`greatest_concern`
# when more than one sub-assessment qualifies -- Moat first (the most
# durable, hardest-to-change dimension), then Management, then
# Reinvestment (the most forward-looking, most uncertain dimension).
_STRENGTH_PRIORITY: tuple[tuple[BusinessQualityDriverKind, int, str], ...] = (
    (BusinessQualityDriverKind.EXCEPTIONAL_COMPETITIVE_POSITION, 2, "moat.level"),
    (BusinessQualityDriverKind.STRONG_COMPETITIVE_POSITION, 1, "moat.level"),
    (BusinessQualityDriverKind.EXCEPTIONAL_MANAGEMENT_QUALITY, 2, "management.level"),
    (BusinessQualityDriverKind.STRONG_MANAGEMENT_QUALITY, 1, "management.level"),
    (BusinessQualityDriverKind.EXCELLENT_REINVESTMENT_RUNWAY, 2, "reinvestment.level"),
    (BusinessQualityDriverKind.GOOD_REINVESTMENT_RUNWAY, 1, "reinvestment.level"),
)
_WEAKNESS_PRIORITY: tuple[tuple[BusinessQualityDriverKind, str], ...] = (
    (BusinessQualityDriverKind.WEAK_COMPETITIVE_POSITION, "moat.level"),
    (BusinessQualityDriverKind.WEAK_MANAGEMENT_QUALITY, "management.level"),
    (BusinessQualityDriverKind.LIMITED_REINVESTMENT_RUNWAY, "reinvestment.level"),
)


def _strengths(moat: MoatAssessment, management: ManagementAssessment, reinvestment: ReinvestmentAssessment) -> tuple[BusinessQualityDriver, ...]:
    drivers: list[BusinessQualityDriver] = []
    if moat.level is MoatLevel.EXCEPTIONAL:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.EXCEPTIONAL_COMPETITIVE_POSITION, source="moat.level"))
    elif moat.level is MoatLevel.STRONG:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.STRONG_COMPETITIVE_POSITION, source="moat.level"))

    if management.level is ManagementQualityLevel.EXCEPTIONAL:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.EXCEPTIONAL_MANAGEMENT_QUALITY, source="management.level"))
    elif management.level is ManagementQualityLevel.STRONG:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.STRONG_MANAGEMENT_QUALITY, source="management.level"))

    if reinvestment.level is ReinvestmentOpportunityLevel.EXCELLENT:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.EXCELLENT_REINVESTMENT_RUNWAY, source="reinvestment.level"))
    elif reinvestment.level is ReinvestmentOpportunityLevel.GOOD:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.GOOD_REINVESTMENT_RUNWAY, source="reinvestment.level"))

    return tuple(drivers)


def _weaknesses(moat: MoatAssessment, management: ManagementAssessment, reinvestment: ReinvestmentAssessment) -> tuple[BusinessQualityDriver, ...]:
    drivers: list[BusinessQualityDriver] = []
    if moat.level is MoatLevel.WEAK:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.WEAK_COMPETITIVE_POSITION, source="moat.level"))
    if management.level is ManagementQualityLevel.WEAK:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.WEAK_MANAGEMENT_QUALITY, source="management.level"))
    if reinvestment.level is ReinvestmentOpportunityLevel.LIMITED:
        drivers.append(BusinessQualityDriver(kind=BusinessQualityDriverKind.LIMITED_REINVESTMENT_RUNWAY, source="reinvestment.level"))
    return tuple(drivers)


def _greatest_advantage(strengths: tuple[BusinessQualityDriver, ...]) -> BusinessQualityDriver | None:
    present = {driver.kind: driver for driver in strengths}
    best_rank = -1
    best: BusinessQualityDriver | None = None
    for kind, rank, _ in _STRENGTH_PRIORITY:
        if kind in present and rank > best_rank:
            best_rank = rank
            best = present[kind]
    return best


def _greatest_concern(weaknesses: tuple[BusinessQualityDriver, ...]) -> BusinessQualityDriver | None:
    present = {driver.kind: driver for driver in weaknesses}
    for kind, _ in _WEAKNESS_PRIORITY:
        if kind in present:
            return present[kind]
    return None


def assess_business_quality(
    moat: MoatAssessment, management: ManagementAssessment, reinvestment: ReinvestmentAssessment
) -> BusinessQualityAssessment:
    """Deterministic: identical inputs always produce an identical
    `BusinessQualityAssessment`."""
    moat_is_positive = moat.level in (MoatLevel.EXCEPTIONAL, MoatLevel.STRONG)
    management_is_positive = management.level in (ManagementQualityLevel.EXCEPTIONAL, ManagementQualityLevel.STRONG)
    reinvestment_is_positive = reinvestment.level in (ReinvestmentOpportunityLevel.EXCELLENT, ReinvestmentOpportunityLevel.GOOD)
    positive_count = sum((moat_is_positive, management_is_positive, reinvestment_is_positive))

    moat_is_negative = moat.level is MoatLevel.WEAK
    management_is_negative = management.level is ManagementQualityLevel.WEAK
    reinvestment_is_negative = reinvestment.level is ReinvestmentOpportunityLevel.LIMITED
    negative_count = sum((moat_is_negative, management_is_negative, reinvestment_is_negative))

    # A `MODERATE`/`GOOD` sub-assessment is real, computed evidence --
    # not the absence of evidence `UNKNOWN` is. Only the count of
    # genuinely `UNKNOWN` sub-assessments should gate the overall
    # `UNKNOWN` floor; a company that is merely unremarkable across all
    # three (never `UNKNOWN`, never `STRONG`/`WEAK`) must read
    # `MODERATE`, not `UNKNOWN`.
    non_unknown_count = sum(
        (
            moat.level is not MoatLevel.UNKNOWN,
            management.level is not ManagementQualityLevel.UNKNOWN,
            reinvestment.level is not ReinvestmentOpportunityLevel.UNKNOWN,
        )
    )

    if non_unknown_count == 0:
        overall = BusinessQualityLevel.UNKNOWN
    elif negative_count > positive_count:
        overall = BusinessQualityLevel.WEAK
    elif positive_count >= _MIN_STRONG_FOR_EXCEPTIONAL and negative_count == 0:
        overall = BusinessQualityLevel.EXCEPTIONAL
    elif positive_count >= _MIN_STRONG_FOR_STRONG and negative_count == 0:
        overall = BusinessQualityLevel.STRONG
    else:
        overall = BusinessQualityLevel.MODERATE

    strengths = _strengths(moat, management, reinvestment)
    weaknesses = _weaknesses(moat, management, reinvestment)
    unknowns = tuple(sorted({*moat.unassessed_dimensions, *management.unassessed_dimensions, *reinvestment.unassessed_dimensions}))

    return BusinessQualityAssessment(
        moat=moat,
        management=management,
        reinvestment=reinvestment,
        overall_level=overall,
        strengths=strengths,
        weaknesses=weaknesses,
        greatest_advantage=_greatest_advantage(strengths),
        greatest_concern=_greatest_concern(weaknesses),
        unknowns=unknowns,
    )

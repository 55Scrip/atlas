"""Outlook Quality Drivers (Calibration Phase 6 -- Valuation & Expected
Return Calibration).

Business Quality (Calibration Phase 5) had zero interaction with
Expected Return -- confirmed by reading `atlas.analysis_engine.outlook`
directly: it never imports this package. This module is the narrow,
disclosed fix: Moat and Reinvestment (not Management -- its dominant
real sub-signal, Capital Allocation, is already a Long-Term Outlook
driver; adding a second Management driver would double-count the
identical evidence under two labels) become two new, purely
informational `OutlookDriverKind` members, constructed here rather than
inside `outlook.py` itself because `atlas.analysis_engine` (Core)
cannot import `atlas.alpha` (the same one-way boundary that already
keeps Conviction's `is_thesis_stale` a caller-supplied parameter).

**Never touches the return arithmetic.** `ExpectedReturnRange`/
`OutlookScenario` are computed entirely inside `outlook.py`, from pure
yield ratios, deliberately excluding share-count/margin data (the
disclosed AAPL stock-split hazard -- see `outlook.py`'s own module
docstring). This module only ever appends `OutlookDriver` instances to
a `key_drivers` view list at the API layer, exactly mirroring how
Capital Allocation's own Long-Term driver already works: `STRONG`-tier
-> `POSITIVE`, `MODERATE`-tier -> `NEUTRAL`, `WEAK`-tier -> `NEGATIVE`,
`UNKNOWN` -> no driver constructed at all (the identical "do not
construct a driver from insufficient evidence" rule
`_status_direction_business`'s own `INSUFFICIENT_INPUT` skip already
establishes).
"""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.models import (
    BusinessQualityAssessment,
    MoatLevel,
    ReinvestmentOpportunityLevel,
)
from atlas.analysis_engine.outlook import DriverDirection, OutlookDriver, OutlookDriverKind

__all__ = ["derive_outlook_quality_drivers"]

_MOAT_DIRECTION = {
    MoatLevel.EXCEPTIONAL: DriverDirection.POSITIVE,
    MoatLevel.STRONG: DriverDirection.POSITIVE,
    MoatLevel.MODERATE: DriverDirection.NEUTRAL,
    MoatLevel.WEAK: DriverDirection.NEGATIVE,
}
_REINVESTMENT_DIRECTION = {
    ReinvestmentOpportunityLevel.EXCELLENT: DriverDirection.POSITIVE,
    ReinvestmentOpportunityLevel.GOOD: DriverDirection.POSITIVE,
    ReinvestmentOpportunityLevel.MODERATE: DriverDirection.NEUTRAL,
    ReinvestmentOpportunityLevel.LIMITED: DriverDirection.NEGATIVE,
}


def derive_outlook_quality_drivers(assessment: BusinessQualityAssessment) -> tuple[OutlookDriver, ...]:
    """Pure. Deterministic: identical `assessment` always produces
    identical drivers. `source_finding_id=None` on both -- neither Moat
    nor Reinvestment is a single `analysis_engine` Finding; they are
    this package's own synthesis, the same "no single evaluated Finding
    backs this" convention `FCF_GROWTH_TREND`/`DEBT_TREND`/
    `MARGIN_TREND` already use for their own derived, non-Finding
    signals."""
    drivers: list[OutlookDriver] = []

    moat_direction = _MOAT_DIRECTION.get(assessment.moat.level)
    if moat_direction is not None:
        drivers.append(OutlookDriver(OutlookDriverKind.MOAT, moat_direction, None))

    reinvestment_direction = _REINVESTMENT_DIRECTION.get(assessment.reinvestment.level)
    if reinvestment_direction is not None:
        drivers.append(OutlookDriver(OutlookDriverKind.REINVESTMENT_OPPORTUNITY, reinvestment_direction, None))

    return tuple(drivers)

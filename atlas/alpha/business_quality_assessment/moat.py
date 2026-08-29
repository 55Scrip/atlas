"""Moat Engine (Calibration Phase 5, Phase 3) -- an explicit,
evidence-driven competitive-advantage assessment.

**Never inferred from market cap, revenue scale, or company size** -- no
signal below reads any of those. Every signal is a trend or stability
classification already computed by `atlas.alpha.investment_case
.business_quality_intelligence` (a pure third-order aggregation over
Growth/Capital-Allocation/Financial-Quality Intelligence) or reused
directly from `atlas.analysis_engine`'s own real Capital Allocation
`BusinessFinding` -- nothing here is a new statistic.

**What this cannot assess, ever, this sprint, regardless of the level
reached**: market share, brand strength, network effects, switching
costs (as directly observed rather than inferred from margin behavior),
ecosystem lock-in, regulatory barriers, distribution advantages, and
technology leadership. Atlas has no data source for any of these --
see `docs/Calibration-Phase-5-Business-Quality-Engine.md` Part C for
why. `unassessed_dimensions` names this list on every single
assessment, never only when the level is uncertain, because even an
`EXCEPTIONAL` read here is proxy-based -- a genuine competitive-advantage
verdict would need real qualitative evidence this codebase does not
have.

**Five evidence signals**, each `POSITIVE`/`NEGATIVE`/`UNKNOWN`:

1. `pricing_power` -- `BusinessQualityKnowledge.stability.profitability
   _stability`. `STABLE` (margins hold up through varying conditions --
   the only externally-visible trace pricing power leaves in financial
   statements) -> `POSITIVE`; `VOLATILE` -> `NEGATIVE`; else `UNKNOWN`.
2. `capital_efficiency` -- `.efficiency.capital_efficiency
   .return_on_assets_trend`. `RISING` -> `POSITIVE`; `FALLING` ->
   `NEGATIVE`; else `UNKNOWN`.
3. `growth_durability` -- at least 3 of the 6 tracked growth metrics
   show consistent growth (`.durability.growth_durability
   .metrics_with_consistent_growth`) -> `POSITIVE`. The identical
   threshold `business_quality_intelligence.py` itself uses for its own
   `DURABLE_GROWTH` finding -- reused, not reinvented.
4. `consistent_value_creation` -- `BusinessQualityFindingKind
   .CONSISTENT_VALUE_CREATION` present in `.findings` -> `POSITIVE`.
5. `capital_allocation_corroboration` -- `analysis_engine`'s own,
   Calibration Phase 4 Capital Allocation `BusinessFinding.status`:
   `STRONG` -> `POSITIVE`; `WEAK` -> `NEGATIVE`; else `UNKNOWN`.

**Combination** -- the identical "negatives must outweigh positives, the
top tier needs broad corroboration" rule Capital Allocation v2 already
established, one level up:

    if computable_count == 0:                        UNKNOWN
    elif negative_count > positive_count:             WEAK
    elif positive_count >= 4 and negative_count == 0: EXCEPTIONAL
    elif positive_count >= 3 and negative_count == 0: STRONG
    else:                                              MODERATE
"""
from __future__ import annotations

from enum import Enum

from atlas.alpha.business_quality_assessment.models import MoatAssessment, MoatEvidenceKind, MoatLevel
from atlas.alpha.investment_case.business_quality_intelligence import (
    BusinessQualityFindingKind,
    BusinessQualityKnowledge,
    StabilityLevel,
    TrendDirection,
)
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus

__all__ = ["UNASSESSED_MOAT_DIMENSIONS", "assess_moat"]

UNASSESSED_MOAT_DIMENSIONS: tuple[str, ...] = (
    "market_share",
    "brand_strength",
    "network_effects",
    "switching_costs",
    "ecosystem",
    "regulatory_barriers",
    "distribution",
    "technology_leadership",
)

_MIN_DURABLE_GROWTH_METRICS = 3


class _Signal(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


def assess_moat(
    business_quality: BusinessQualityKnowledge, *, capital_allocation_status: BusinessCategoryStatus
) -> MoatAssessment:
    """Deterministic: identical inputs always produce an identical
    `MoatAssessment`."""
    signals: list[tuple[_Signal, MoatEvidenceKind | None, MoatEvidenceKind | None]] = []

    stability = business_quality.stability.profitability_stability
    if stability is StabilityLevel.STABLE:
        signals.append((_Signal.POSITIVE, MoatEvidenceKind.STABLE_PROFITABILITY_THROUGH_VARYING_CONDITIONS, None))
    elif stability is StabilityLevel.VOLATILE:
        signals.append((_Signal.NEGATIVE, None, MoatEvidenceKind.VOLATILE_PROFITABILITY))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    roa_trend = business_quality.efficiency.capital_efficiency.return_on_assets_trend
    if roa_trend is TrendDirection.RISING:
        signals.append((_Signal.POSITIVE, MoatEvidenceKind.RISING_RETURNS_ON_CAPITAL, None))
    elif roa_trend is TrendDirection.FALLING:
        signals.append((_Signal.NEGATIVE, None, MoatEvidenceKind.FALLING_RETURNS_ON_CAPITAL))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    if len(business_quality.durability.growth_durability.metrics_with_consistent_growth) >= _MIN_DURABLE_GROWTH_METRICS:
        signals.append((_Signal.POSITIVE, MoatEvidenceKind.DURABLE_GROWTH_ACROSS_MULTIPLE_METRICS, None))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    if any(f.kind is BusinessQualityFindingKind.CONSISTENT_VALUE_CREATION for f in business_quality.findings):
        signals.append((_Signal.POSITIVE, MoatEvidenceKind.CONSISTENT_VALUE_CREATION, None))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    if capital_allocation_status is BusinessCategoryStatus.STRONG:
        signals.append((_Signal.POSITIVE, MoatEvidenceKind.STRONG_CAPITAL_ALLOCATION_TRACK_RECORD, None))
    elif capital_allocation_status is BusinessCategoryStatus.WEAK:
        signals.append((_Signal.NEGATIVE, None, MoatEvidenceKind.WEAK_CAPITAL_ALLOCATION_TRACK_RECORD))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    positive_evidence = tuple(kind for signal, kind, _ in signals if signal is _Signal.POSITIVE and kind is not None)
    negative_evidence = tuple(kind for signal, _, kind in signals if signal is _Signal.NEGATIVE and kind is not None)
    positive_count = len(positive_evidence)
    negative_count = len(negative_evidence)
    computable_count = positive_count + negative_count

    if computable_count == 0:
        level = MoatLevel.UNKNOWN
    elif negative_count > positive_count:
        level = MoatLevel.WEAK
    elif positive_count >= 4 and negative_count == 0:
        level = MoatLevel.EXCEPTIONAL
    elif positive_count >= 3 and negative_count == 0:
        level = MoatLevel.STRONG
    else:
        level = MoatLevel.MODERATE

    return MoatAssessment(
        level=level,
        supporting_evidence=tuple(sorted({*positive_evidence, *negative_evidence}, key=lambda k: k.value)),
        unassessed_dimensions=UNASSESSED_MOAT_DIMENSIONS,
    )

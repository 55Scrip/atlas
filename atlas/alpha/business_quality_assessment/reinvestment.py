"""Reinvestment Engine (Calibration Phase 5, Phase 5) -- estimates
whether a company still has high-quality reinvestment opportunities,
from real, already-computed financial evidence only.

**Four signals**, each `POSITIVE`/`NEGATIVE`/`UNKNOWN`:

1. `growth_durability` -- reused verbatim from the Moat Engine's own
   computation (at least 3 of 6 tracked growth metrics show consistent
   growth): the same real evidence answers both "is the business
   advantaged" and "does growth have real durability" -- never
   duplicated as two different numbers.
2. `capital_efficiency` -- reused verbatim from Moat
   (`return_on_assets_trend`): rising returns on capital means the
   business is reinvesting at attractive returns, not just growing for
   growth's sake.
3. `cash_generation_capacity` -- `FinancialDurabilityKnowledge.findings`
   presence of `CASH_GENERATION_CONSISTENTLY_POSITIVE` ->  `POSITIVE`
   (sustained cash generation funds reinvestment without external
   capital); `CASH_GENERATION_INCONSISTENT` -> `NEGATIVE`.
4. `reinvestment_activity` -- `ManagementCapitalAllocationKnowledge
   .reinvestment_discipline`. `RISING` -> `POSITIVE` (real, ongoing
   capital deployment). **Deliberately never `NEGATIVE` on `FALLING`**
   -- falling capex could mean either harvesting a mature, saturated
   market or genuine capital discipline, and Atlas cannot honestly
   distinguish the two without segment/TAM data it does not have, so
   `FALLING` resolves to `UNKNOWN` rather than guessed.

**What this cannot assess, ever, this sprint**: addressable market size,
market saturation, adjacent-product opportunities, international
expansion headroom, industry maturity -- Atlas has no TAM, segment, or
geographic revenue data. Always disclosed via `unassessed_dimensions`,
regardless of the level reached.

Same combination rule as Moat/Management.
"""
from __future__ import annotations

from enum import Enum

from atlas.alpha.business_quality_assessment.models import (
    ReinvestmentAssessment,
    ReinvestmentEvidenceKind,
    ReinvestmentOpportunityLevel,
)
from atlas.alpha.investment_case.business_quality_intelligence import BusinessQualityKnowledge, TrendDirection
from atlas.alpha.investment_case.financial_quality_intelligence import DurabilityFinding

__all__ = ["UNASSESSED_REINVESTMENT_DIMENSIONS", "assess_reinvestment"]

UNASSESSED_REINVESTMENT_DIMENSIONS: tuple[str, ...] = (
    "addressable_market_size",
    "market_saturation",
    "adjacent_product_opportunities",
    "international_expansion_headroom",
    "industry_maturity",
)

_MIN_DURABLE_GROWTH_METRICS = 3


class _Signal(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


def assess_reinvestment(business_quality: BusinessQualityKnowledge, *, reinvestment_discipline: TrendDirection) -> ReinvestmentAssessment:
    """Deterministic: identical inputs always produce an identical
    `ReinvestmentAssessment`."""
    signals: list[tuple[_Signal, ReinvestmentEvidenceKind | None, ReinvestmentEvidenceKind | None]] = []

    if len(business_quality.durability.growth_durability.metrics_with_consistent_growth) >= _MIN_DURABLE_GROWTH_METRICS:
        signals.append((_Signal.POSITIVE, ReinvestmentEvidenceKind.DURABLE_GROWTH_ACROSS_MULTIPLE_METRICS, None))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    roa_trend = business_quality.efficiency.capital_efficiency.return_on_assets_trend
    if roa_trend is TrendDirection.RISING:
        signals.append((_Signal.POSITIVE, ReinvestmentEvidenceKind.RISING_RETURNS_ON_CAPITAL, None))
    elif roa_trend is TrendDirection.FALLING:
        signals.append((_Signal.NEGATIVE, None, ReinvestmentEvidenceKind.FALLING_RETURNS_ON_CAPITAL))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    findings = business_quality.durability.financial_durability.findings
    if DurabilityFinding.CASH_GENERATION_CONSISTENTLY_POSITIVE in findings:
        signals.append((_Signal.POSITIVE, ReinvestmentEvidenceKind.SUSTAINED_CASH_GENERATION, None))
    elif DurabilityFinding.CASH_GENERATION_INCONSISTENT in findings:
        signals.append((_Signal.NEGATIVE, None, ReinvestmentEvidenceKind.INCONSISTENT_CASH_GENERATION))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    if reinvestment_discipline is TrendDirection.RISING:
        signals.append((_Signal.POSITIVE, ReinvestmentEvidenceKind.RISING_REINVESTMENT_ACTIVITY, None))
    else:
        signals.append((_Signal.UNKNOWN, None, None))

    positive_evidence = tuple(kind for signal, kind, _ in signals if signal is _Signal.POSITIVE and kind is not None)
    negative_evidence = tuple(kind for signal, _, kind in signals if signal is _Signal.NEGATIVE and kind is not None)
    positive_count = len(positive_evidence)
    negative_count = len(negative_evidence)
    computable_count = positive_count + negative_count

    if computable_count == 0:
        level = ReinvestmentOpportunityLevel.UNKNOWN
    elif negative_count > positive_count:
        level = ReinvestmentOpportunityLevel.LIMITED
    elif positive_count >= 4 and negative_count == 0:
        level = ReinvestmentOpportunityLevel.EXCELLENT
    elif positive_count >= 3 and negative_count == 0:
        level = ReinvestmentOpportunityLevel.GOOD
    else:
        level = ReinvestmentOpportunityLevel.MODERATE

    return ReinvestmentAssessment(
        level=level,
        supporting_evidence=tuple(sorted({*positive_evidence, *negative_evidence}, key=lambda k: k.value)),
        unassessed_dimensions=UNASSESSED_REINVESTMENT_DIMENSIONS,
    )

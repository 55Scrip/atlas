"""Management Quality Engine (Calibration Phase 5, Phase 4) -- evaluates
management *behavior*, never personality, charisma, or communication
style as such.

Seven dimensions, per the brief. Real source and live-population status
for each (see `docs/Calibration-Phase-5-Business-Quality-Engine.md`
Part D for the full investigation):

- `CAPITAL_ALLOCATION` -- reuses `atlas.analysis_engine.capital
  _allocation`'s own Calibration Phase 4 `BusinessFinding.status`
  directly. Live for any company with real financial facts.
- `EXECUTION` -- `ManagementCredibilityKnowledge.execution_consistency`:
  did commitments made on earnings calls actually get fulfilled. Live
  for companies with ingested earnings-call transcripts.
- `CONSISTENCY` -- `ManagementCredibilityKnowledge.guidance_reliability`:
  fulfilled vs. withdrawn guidance track record. Live, same requirement.
- `COMMUNICATION` -- `ManagementCredibilityKnowledge
  .communication_consistency.direction`: did messaging/emphasis shift
  materially quarter to quarter. Live, same requirement.
- `LONG_TERM_THINKING` -- `ManagementCapitalAllocationKnowledge
  .reinvestment_discipline` trend. Only rewards a clear `RISING`
  signal; `FALLING` is honestly `UNKNOWN` rather than penalized, since
  Atlas cannot distinguish real capital discipline from underinvestment
  without segment/TAM data it does not have.
- `SHAREHOLDER_ALIGNMENT` -- `ManagementCapitalAllocationKnowledge
  .shareholder_return_policy`. Partial: the more direct insider-
  ownership alignment signal is structurally dormant in production
  today (no filing-content fetch path exists) -- disclosed via
  `unassessed_dimensions`, not silently assumed.
- `GOVERNANCE` -- **always `UNKNOWN`**. `governance_intelligence.py` is
  wired but called with an empty tuple in production (no DEF 14A/10-K
  content-fetch path exists anywhere in Atlas today) -- a real,
  disclosed data gap, not an oversight.

Overall `ManagementQualityLevel` combines the six *computable* dimensions
(Governance always excluded from the count) with the identical
positive/negative-count rule Moat and Capital Allocation v2 already
establish.
"""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.models import (
    ManagementAssessment,
    ManagementDimensionAssessment,
    ManagementDimensionKind,
    ManagementQualityLevel,
)
from atlas.alpha.investment_case.capital_allocation_intelligence import (
    ManagementCapitalAllocationKnowledge,
    ShareholderReturnPolicy,
)
from atlas.alpha.investment_case.financial_statement_intelligence import TrendDirection
from atlas.alpha.investment_case.management_credibility_intelligence import (
    CommunicationDirection,
    ExecutionConsistency,
    ManagementCredibilityKnowledge,
)
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus

__all__ = ["UNASSESSED_MANAGEMENT_DIMENSIONS", "assess_management"]

UNASSESSED_MANAGEMENT_DIMENSIONS: tuple[str, ...] = (
    "governance",
    "insider_ownership_alignment",
    "executive_compensation_structure",
)

_MIN_STRONG_FOR_EXCEPTIONAL = 4
_MIN_STRONG_FOR_STRONG = 3

Level = ManagementQualityLevel


def _capital_allocation_level(status: BusinessCategoryStatus) -> Level:
    if status is BusinessCategoryStatus.STRONG:
        return Level.STRONG
    if status is BusinessCategoryStatus.WEAK:
        return Level.WEAK
    if status is BusinessCategoryStatus.MODERATE:
        return Level.MODERATE
    return Level.UNKNOWN


def _execution_level(execution_consistency: ExecutionConsistency) -> Level:
    if execution_consistency is ExecutionConsistency.STRONG_FOLLOW_THROUGH:
        return Level.STRONG
    if execution_consistency is ExecutionConsistency.MIXED_FOLLOW_THROUGH:
        return Level.MODERATE
    if execution_consistency is ExecutionConsistency.WEAK_FOLLOW_THROUGH:
        return Level.WEAK
    return Level.UNKNOWN


def _consistency_level(credibility: ManagementCredibilityKnowledge) -> Level:
    guidance = credibility.guidance_reliability
    if not guidance.guidance_history:
        return Level.UNKNOWN
    if guidance.fulfilled_guidance_count > 0 and guidance.withdrawn_guidance_count == 0:
        return Level.STRONG
    if guidance.withdrawn_guidance_count > 0 and guidance.fulfilled_guidance_count == 0:
        return Level.WEAK
    return Level.MODERATE


def _communication_level(direction: CommunicationDirection) -> Level:
    if direction in (CommunicationDirection.STABLE, CommunicationDirection.STRENGTHENED):
        return Level.STRONG
    if direction is CommunicationDirection.WEAKENED:
        return Level.WEAK
    if direction is CommunicationDirection.MIXED:
        return Level.MODERATE
    return Level.UNKNOWN


def _long_term_thinking_level(reinvestment_discipline: TrendDirection) -> Level:
    if reinvestment_discipline is TrendDirection.RISING:
        return Level.STRONG
    return Level.UNKNOWN


def _shareholder_alignment_level(policy: ShareholderReturnPolicy) -> Level:
    if policy is ShareholderReturnPolicy.ACTIVE:
        return Level.STRONG
    if policy is ShareholderReturnPolicy.LIMITED:
        return Level.MODERATE
    return Level.UNKNOWN


def assess_management(
    credibility: ManagementCredibilityKnowledge,
    capital_allocation_knowledge: ManagementCapitalAllocationKnowledge,
    *,
    capital_allocation_status: BusinessCategoryStatus,
) -> ManagementAssessment:
    """Deterministic: identical inputs always produce an identical
    `ManagementAssessment`."""
    dimension_levels = {
        ManagementDimensionKind.CAPITAL_ALLOCATION: _capital_allocation_level(capital_allocation_status),
        ManagementDimensionKind.EXECUTION: _execution_level(credibility.execution_consistency),
        ManagementDimensionKind.CONSISTENCY: _consistency_level(credibility),
        ManagementDimensionKind.COMMUNICATION: _communication_level(credibility.communication_consistency.direction),
        ManagementDimensionKind.LONG_TERM_THINKING: _long_term_thinking_level(
            capital_allocation_knowledge.reinvestment_discipline
        ),
        ManagementDimensionKind.SHAREHOLDER_ALIGNMENT: _shareholder_alignment_level(
            capital_allocation_knowledge.shareholder_return_policy
        ),
        ManagementDimensionKind.GOVERNANCE: Level.UNKNOWN,
    }

    dimensions = tuple(
        ManagementDimensionAssessment(kind=kind, level=dimension_levels[kind]) for kind in ManagementDimensionKind
    )

    computable = {kind: level for kind, level in dimension_levels.items() if kind is not ManagementDimensionKind.GOVERNANCE}
    non_unknown_count = sum(1 for level in computable.values() if level is not Level.UNKNOWN)
    positive_count = sum(1 for level in computable.values() if level is Level.STRONG)
    negative_count = sum(1 for level in computable.values() if level is Level.WEAK)

    if non_unknown_count == 0:
        overall = Level.UNKNOWN
    elif negative_count > positive_count:
        overall = Level.WEAK
    elif positive_count >= _MIN_STRONG_FOR_EXCEPTIONAL and negative_count == 0:
        overall = Level.EXCEPTIONAL
    elif positive_count >= _MIN_STRONG_FOR_STRONG and negative_count == 0:
        overall = Level.STRONG
    else:
        overall = Level.MODERATE

    return ManagementAssessment(
        level=overall, dimensions=dimensions, unassessed_dimensions=UNASSESSED_MANAGEMENT_DIMENSIONS
    )

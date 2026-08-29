"""Tests for `atlas.alpha.business_quality_assessment.management
.assess_management` -- every dimension's mapping from its own real
source exercised directly, plus the overall combination rule."""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.management import UNASSESSED_MANAGEMENT_DIMENSIONS, assess_management
from atlas.alpha.business_quality_assessment.models import ManagementDimensionKind, ManagementQualityLevel
from atlas.alpha.investment_case.capital_allocation_intelligence import (
    AcquisitionBehavior,
    BuybackConsistency,
    DebtDiscipline,
    ManagementCapitalAllocationKnowledge,
    ShareholderReturnPolicy,
)
from atlas.alpha.investment_case.financial_statement_intelligence import TrendDirection
from atlas.alpha.investment_case.management_credibility_intelligence import (
    CommunicationConsistency,
    CommunicationDirection,
    ExecutionConsistency,
    GuidanceReliabilityKnowledge,
    ManagementCredibilityKnowledge,
)
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus

_EMPTY_GUIDANCE = GuidanceReliabilityKnowledge(
    guidance_history=(), guidance_revisions=(), fulfilled_guidance_count=0, withdrawn_guidance_count=0,
    unresolved_guidance_count=0,
)
_NO_COMMUNICATION_DATA = CommunicationConsistency(
    direction=CommunicationDirection.INSUFFICIENT_DATA, strengthened_categories=(), weakened_categories=(),
    guidance_changed=False, strategic_emphasis_shifted=False,
)
_INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE = ManagementCapitalAllocationKnowledge(
    reinvestment_discipline=TrendDirection.INSUFFICIENT_DATA,
    shareholder_return_policy=ShareholderReturnPolicy.INSUFFICIENT_DATA,
    financing_strategy=TrendDirection.INSUFFICIENT_DATA,
    acquisition_behavior=AcquisitionBehavior.INSUFFICIENT_DATA,
    debt_discipline=DebtDiscipline.INSUFFICIENT_DATA,
    capital_allocation_consistency=BuybackConsistency.INSUFFICIENT_DATA,
)


def _credibility(
    *, execution=ExecutionConsistency.INSUFFICIENT_EVIDENCE, communication=_NO_COMMUNICATION_DATA, guidance=_EMPTY_GUIDANCE
) -> ManagementCredibilityKnowledge:
    return ManagementCredibilityKnowledge(
        commitments=(), communication_consistency=communication, guidance_reliability=guidance,
        execution_consistency=execution, findings=(),
    )


class TestGovernanceIsAlwaysUnknown:
    def test_governance_is_unknown_regardless_of_every_other_signal(self):
        result = assess_management(
            _credibility(execution=ExecutionConsistency.STRONG_FOLLOW_THROUGH),
            _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE,
            capital_allocation_status=BusinessCategoryStatus.STRONG,
        )
        governance = next(d for d in result.dimensions if d.kind is ManagementDimensionKind.GOVERNANCE)
        assert governance.level is ManagementQualityLevel.UNKNOWN
        assert "governance" in result.unassessed_dimensions
        assert result.unassessed_dimensions == UNASSESSED_MANAGEMENT_DIMENSIONS

    def test_all_seven_dimensions_are_always_named(self):
        result = assess_management(_credibility(), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert {d.kind for d in result.dimensions} == set(ManagementDimensionKind)


class TestCapitalAllocationDimension:
    def test_reuses_analysis_engines_own_capital_allocation_finding_directly(self):
        strong = assess_management(_credibility(), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.STRONG)
        weak = assess_management(_credibility(), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.WEAK)
        dim = ManagementDimensionKind.CAPITAL_ALLOCATION
        assert next(d for d in strong.dimensions if d.kind is dim).level is ManagementQualityLevel.STRONG
        assert next(d for d in weak.dimensions if d.kind is dim).level is ManagementQualityLevel.WEAK


class TestExecutionDimension:
    def test_strong_follow_through_maps_to_strong(self):
        result = assess_management(_credibility(execution=ExecutionConsistency.STRONG_FOLLOW_THROUGH), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.EXECUTION).level is ManagementQualityLevel.STRONG

    def test_weak_follow_through_maps_to_weak(self):
        result = assess_management(_credibility(execution=ExecutionConsistency.WEAK_FOLLOW_THROUGH), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.EXECUTION).level is ManagementQualityLevel.WEAK

    def test_insufficient_evidence_maps_to_unknown(self):
        result = assess_management(_credibility(execution=ExecutionConsistency.INSUFFICIENT_EVIDENCE), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.EXECUTION).level is ManagementQualityLevel.UNKNOWN


class TestConsistencyDimension:
    def test_fulfilled_guidance_with_no_withdrawals_is_strong(self):
        guidance = GuidanceReliabilityKnowledge(
            guidance_history=("placeholder",), guidance_revisions=(), fulfilled_guidance_count=2,
            withdrawn_guidance_count=0, unresolved_guidance_count=0,
        )
        result = assess_management(_credibility(guidance=guidance), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.CONSISTENCY).level is ManagementQualityLevel.STRONG

    def test_withdrawn_guidance_with_no_fulfillment_is_weak(self):
        guidance = GuidanceReliabilityKnowledge(
            guidance_history=("placeholder",), guidance_revisions=(), fulfilled_guidance_count=0,
            withdrawn_guidance_count=2, unresolved_guidance_count=0,
        )
        result = assess_management(_credibility(guidance=guidance), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.CONSISTENCY).level is ManagementQualityLevel.WEAK

    def test_no_guidance_history_at_all_is_unknown(self):
        result = assess_management(_credibility(guidance=_EMPTY_GUIDANCE), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.CONSISTENCY).level is ManagementQualityLevel.UNKNOWN


class TestCommunicationDimension:
    def test_stable_communication_is_strong(self):
        communication = CommunicationConsistency(direction=CommunicationDirection.STABLE, strengthened_categories=(), weakened_categories=(), guidance_changed=False, strategic_emphasis_shifted=False)
        result = assess_management(_credibility(communication=communication), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.COMMUNICATION).level is ManagementQualityLevel.STRONG

    def test_weakened_communication_is_weak(self):
        communication = CommunicationConsistency(direction=CommunicationDirection.WEAKENED, strengthened_categories=(), weakened_categories=(), guidance_changed=False, strategic_emphasis_shifted=False)
        result = assess_management(_credibility(communication=communication), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.COMMUNICATION).level is ManagementQualityLevel.WEAK


class TestLongTermThinkingDimension:
    def test_rising_reinvestment_discipline_is_strong(self):
        knowledge = ManagementCapitalAllocationKnowledge(
            reinvestment_discipline=TrendDirection.RISING, shareholder_return_policy=ShareholderReturnPolicy.INSUFFICIENT_DATA,
            financing_strategy=TrendDirection.INSUFFICIENT_DATA, acquisition_behavior=AcquisitionBehavior.INSUFFICIENT_DATA,
            debt_discipline=DebtDiscipline.INSUFFICIENT_DATA, capital_allocation_consistency=BuybackConsistency.INSUFFICIENT_DATA,
        )
        result = assess_management(_credibility(), knowledge, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.LONG_TERM_THINKING).level is ManagementQualityLevel.STRONG

    def test_falling_reinvestment_discipline_is_honestly_unknown_not_penalized(self):
        """Falling capex could mean genuine capital discipline or
        underinvestment -- Atlas cannot honestly distinguish the two
        without segment/TAM data it does not have, so this never reads
        `WEAK`."""
        knowledge = ManagementCapitalAllocationKnowledge(
            reinvestment_discipline=TrendDirection.FALLING, shareholder_return_policy=ShareholderReturnPolicy.INSUFFICIENT_DATA,
            financing_strategy=TrendDirection.INSUFFICIENT_DATA, acquisition_behavior=AcquisitionBehavior.INSUFFICIENT_DATA,
            debt_discipline=DebtDiscipline.INSUFFICIENT_DATA, capital_allocation_consistency=BuybackConsistency.INSUFFICIENT_DATA,
        )
        result = assess_management(_credibility(), knowledge, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.LONG_TERM_THINKING).level is ManagementQualityLevel.UNKNOWN


class TestShareholderAlignmentDimension:
    def test_active_return_policy_is_strong(self):
        knowledge = ManagementCapitalAllocationKnowledge(
            reinvestment_discipline=TrendDirection.INSUFFICIENT_DATA, shareholder_return_policy=ShareholderReturnPolicy.ACTIVE,
            financing_strategy=TrendDirection.INSUFFICIENT_DATA, acquisition_behavior=AcquisitionBehavior.INSUFFICIENT_DATA,
            debt_discipline=DebtDiscipline.INSUFFICIENT_DATA, capital_allocation_consistency=BuybackConsistency.INSUFFICIENT_DATA,
        )
        result = assess_management(_credibility(), knowledge, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.SHAREHOLDER_ALIGNMENT).level is ManagementQualityLevel.STRONG

    def test_no_return_policy_is_unknown_never_penalized(self):
        """Matches Capital Allocation v2's own dividend ethos: absence
        of shareholder returns is a legitimate strategy, never a
        negative signal by itself."""
        knowledge = ManagementCapitalAllocationKnowledge(
            reinvestment_discipline=TrendDirection.INSUFFICIENT_DATA, shareholder_return_policy=ShareholderReturnPolicy.NONE,
            financing_strategy=TrendDirection.INSUFFICIENT_DATA, acquisition_behavior=AcquisitionBehavior.INSUFFICIENT_DATA,
            debt_discipline=DebtDiscipline.INSUFFICIENT_DATA, capital_allocation_consistency=BuybackConsistency.INSUFFICIENT_DATA,
        )
        result = assess_management(_credibility(), knowledge, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert next(d for d in result.dimensions if d.kind is ManagementDimensionKind.SHAREHOLDER_ALIGNMENT).level is ManagementQualityLevel.UNKNOWN


class TestOverallCombinationRule:
    def test_four_strong_dimensions_reach_exceptional_overall(self):
        result = assess_management(
            _credibility(execution=ExecutionConsistency.STRONG_FOLLOW_THROUGH),
            ManagementCapitalAllocationKnowledge(
                reinvestment_discipline=TrendDirection.RISING, shareholder_return_policy=ShareholderReturnPolicy.ACTIVE,
                financing_strategy=TrendDirection.INSUFFICIENT_DATA, acquisition_behavior=AcquisitionBehavior.INSUFFICIENT_DATA,
                debt_discipline=DebtDiscipline.INSUFFICIENT_DATA, capital_allocation_consistency=BuybackConsistency.INSUFFICIENT_DATA,
            ),
            capital_allocation_status=BusinessCategoryStatus.STRONG,
        )
        assert result.level is ManagementQualityLevel.EXCEPTIONAL

    def test_three_strong_dimensions_reach_strong_overall(self):
        result = assess_management(
            _credibility(execution=ExecutionConsistency.STRONG_FOLLOW_THROUGH),
            ManagementCapitalAllocationKnowledge(
                reinvestment_discipline=TrendDirection.RISING, shareholder_return_policy=ShareholderReturnPolicy.INSUFFICIENT_DATA,
                financing_strategy=TrendDirection.INSUFFICIENT_DATA, acquisition_behavior=AcquisitionBehavior.INSUFFICIENT_DATA,
                debt_discipline=DebtDiscipline.INSUFFICIENT_DATA, capital_allocation_consistency=BuybackConsistency.INSUFFICIENT_DATA,
            ),
            capital_allocation_status=BusinessCategoryStatus.STRONG,
        )
        assert result.level is ManagementQualityLevel.STRONG

    def test_a_single_moderate_dimension_alone_is_moderate_not_unknown(self):
        """A real, computed `MODERATE` (Capital Allocation) is not the
        same as no evidence -- it must not be silently treated as
        `UNKNOWN` overall."""
        result = assess_management(_credibility(), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.MODERATE)
        assert result.level is ManagementQualityLevel.MODERATE

    def test_zero_computable_dimensions_is_unknown(self):
        result = assess_management(_credibility(), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT)
        assert result.level is ManagementQualityLevel.UNKNOWN

    def test_negatives_outweighing_positives_is_weak(self):
        result = assess_management(
            _credibility(execution=ExecutionConsistency.WEAK_FOLLOW_THROUGH),
            _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE,
            capital_allocation_status=BusinessCategoryStatus.WEAK,
        )
        assert result.level is ManagementQualityLevel.WEAK


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_assessment(self):
        first = assess_management(_credibility(execution=ExecutionConsistency.STRONG_FOLLOW_THROUGH), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.STRONG)
        second = assess_management(_credibility(execution=ExecutionConsistency.STRONG_FOLLOW_THROUGH), _INSUFFICIENT_CAPITAL_ALLOCATION_KNOWLEDGE, capital_allocation_status=BusinessCategoryStatus.STRONG)
        assert first == second

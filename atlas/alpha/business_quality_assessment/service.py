"""Orchestration for the Business Quality Assessment engine -- the only
part of this package that performs I/O. Composes `atlas.alpha
.investment_case.InvestmentCaseCompositionService` (unmodified) and
hands its already-computed sibling outputs to the pure `moat.py`/
`management.py`/`reinvestment.py`/`engine.py` -- no new repository, no
new table, no new persistence, mirroring `atlas.alpha.stance.service
.StanceService`'s own shape and reuse discipline exactly.
"""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.engine import assess_business_quality
from atlas.alpha.business_quality_assessment.management import assess_management
from atlas.alpha.business_quality_assessment.models import BusinessQualityAssessment
from atlas.alpha.business_quality_assessment.moat import assess_moat
from atlas.alpha.business_quality_assessment.reinvestment import assess_reinvestment
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.analysis_engine.business_contracts import BusinessCategory, BusinessCategoryStatus

__all__ = ["BusinessQualityAssessmentService"]


class BusinessQualityAssessmentService:
    def __init__(self, composition_service: InvestmentCaseCompositionService) -> None:
        self._composition_service = composition_service
        # Request-scoped memoization -- the identical justification and
        # pattern `StanceService._assess_for_case_cache` already
        # establishes: this dict is as request-scoped as the instance
        # itself, so caching by `case_id` changes no observable
        # behavior, only how many times an identical assessment is
        # repeated within one request.
        self._assess_for_case_cache: dict[str, BusinessQualityAssessment | None] = {}

    def assess_for_case(self, case_id: str) -> BusinessQualityAssessment | None:
        if case_id in self._assess_for_case_cache:
            return self._assess_for_case_cache[case_id]
        result = self._assess(case_id)
        self._assess_for_case_cache[case_id] = result
        return result

    def _assess(self, case_id: str) -> BusinessQualityAssessment | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None

        capital_allocation_status = next(
            (
                f.status
                for f in composition.canonical_analysis.business_analysis.findings
                if f.kind is BusinessCategory.CAPITAL_ALLOCATION
            ),
            BusinessCategoryStatus.INSUFFICIENT_INPUT,
        )
        business_quality_knowledge = composition.business_quality_intelligence
        capital_allocation_knowledge = business_quality_knowledge.durability.capital_discipline

        moat = assess_moat(business_quality_knowledge, capital_allocation_status=capital_allocation_status)
        management = assess_management(
            composition.management_credibility_intelligence,
            capital_allocation_knowledge,
            capital_allocation_status=capital_allocation_status,
        )
        reinvestment = assess_reinvestment(
            business_quality_knowledge, reinvestment_discipline=capital_allocation_knowledge.reinvestment_discipline
        )
        return assess_business_quality(moat, management, reinvestment)

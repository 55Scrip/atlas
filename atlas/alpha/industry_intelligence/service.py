"""Orchestration for Industry Intelligence -- the only part of this
package that performs I/O. Composes `atlas.alpha.investment_case
.InvestmentCaseCompositionService` (unmodified) and hands its already-
computed `company_profile.sector`/`.industry` to the pure `engine.py`
-- no new repository, no new table, no new persistence, mirroring
`atlas.alpha.business_quality_assessment.service
.BusinessQualityAssessmentService`'s own shape exactly.
"""
from __future__ import annotations

from atlas.alpha.industry_intelligence.engine import derive_industry_context
from atlas.alpha.industry_intelligence.models import IndustryContext
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService

__all__ = ["IndustryIntelligenceService"]


class IndustryIntelligenceService:
    def __init__(self, composition_service: InvestmentCaseCompositionService) -> None:
        self._composition_service = composition_service
        # Request-scoped memoization -- the identical justification and
        # pattern `BusinessQualityAssessmentService._assess_for_case_cache`
        # already establishes.
        self._context_for_case_cache: dict[str, IndustryContext | None] = {}

    def context_for_case(self, case_id: str) -> IndustryContext | None:
        if case_id in self._context_for_case_cache:
            return self._context_for_case_cache[case_id]
        result = self._context(case_id)
        self._context_for_case_cache[case_id] = result
        return result

    def _context(self, case_id: str) -> IndustryContext | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None
        profile = composition.company_profile
        sector = profile.sector if profile is not None else None
        industry = profile.industry if profile is not None else None
        return derive_industry_context(sector, industry)

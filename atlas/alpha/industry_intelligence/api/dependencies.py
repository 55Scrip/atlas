"""Composition wiring for the Industry Intelligence API. Same "each
Alpha package wires its own dependencies" convention
`atlas.alpha.business_quality_assessment.api.dependencies`'s own module
docstring documents.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.industry_intelligence.service import IndustryIntelligenceService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService

__all__ = ["get_industry_intelligence_service"]


def get_industry_intelligence_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
) -> IndustryIntelligenceService:
    return IndustryIntelligenceService(composition_service=composition_service)

"""Composition wiring for the Business Quality Assessment API. Same
"each Alpha package wires its own dependencies" convention
`atlas.alpha.stance.api.dependencies`'s own module docstring documents.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.business_quality_assessment.service import BusinessQualityAssessmentService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService

__all__ = ["get_business_quality_assessment_service"]


def get_business_quality_assessment_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
) -> BusinessQualityAssessmentService:
    return BusinessQualityAssessmentService(composition_service=composition_service)

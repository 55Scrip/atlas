"""Business Quality Assessment (Calibration Phase 5 -- Business Quality
Engine).

Answers "is this genuinely a great business, not just a cheap one" --
an explicit, evidence-driven Moat/Management/Reinvestment assessment,
synthesized from `atlas.analysis_engine`'s real Growth/Capital
Allocation findings plus the already-live alpha-layer intelligence
modules (`business_quality_intelligence`, `management_credibility
_intelligence`, `capital_allocation_intelligence`). Never a numeric
score, never inferred from market cap, always honest about what Atlas
structurally cannot assess (`unassessed_dimensions` on every
sub-assessment). See `docs/Calibration-Phase-5-Business-Quality
-Engine.md` for the full research, model, and architecture rationale.

This is a pure orchestration/synthesis layer over already-real signals
-- never a second Growth/Capital Allocation engine, never a second
Business Quality Intelligence. See `engine.py`'s own module docstring
for the integration rule.
"""
from __future__ import annotations

from .engine import assess_business_quality
from .management import assess_management
from .models import (
    BusinessQualityAssessment,
    BusinessQualityDriver,
    BusinessQualityDriverKind,
    BusinessQualityLevel,
    ManagementAssessment,
    ManagementDimensionAssessment,
    ManagementDimensionKind,
    ManagementQualityLevel,
    MoatAssessment,
    MoatEvidenceKind,
    MoatLevel,
    ReinvestmentAssessment,
    ReinvestmentEvidenceKind,
    ReinvestmentOpportunityLevel,
)
from .moat import assess_moat
from .outlook_context import derive_outlook_quality_drivers
from .reinvestment import assess_reinvestment
from .service import BusinessQualityAssessmentService

__all__ = [
    "assess_business_quality",
    "assess_management",
    "assess_moat",
    "assess_reinvestment",
    "derive_outlook_quality_drivers",
    "BusinessQualityAssessment",
    "BusinessQualityAssessmentService",
    "BusinessQualityDriver",
    "BusinessQualityDriverKind",
    "BusinessQualityLevel",
    "ManagementAssessment",
    "ManagementDimensionAssessment",
    "ManagementDimensionKind",
    "ManagementQualityLevel",
    "MoatAssessment",
    "MoatEvidenceKind",
    "MoatLevel",
    "ReinvestmentAssessment",
    "ReinvestmentEvidenceKind",
    "ReinvestmentOpportunityLevel",
]

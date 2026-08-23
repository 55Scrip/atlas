"""Coverage & Confidence Engine (Atlas Intelligence Sprint 1). See
`engine.py`'s module docstring for the full design rationale."""
from __future__ import annotations

from .engine import assess_coverage, has_contradiction
from .models import (
    ConfidenceLevel,
    ConfidenceReason,
    ConfidenceReasonCode,
    CoverageAssessment,
    DimensionCoverage,
    DimensionCoverageLevel,
)

__all__ = [
    "assess_coverage",
    "has_contradiction",
    "ConfidenceLevel",
    "ConfidenceReason",
    "ConfidenceReasonCode",
    "CoverageAssessment",
    "DimensionCoverage",
    "DimensionCoverageLevel",
]

"""Evidence Quality Engine (Atlas Intelligence Sprint 4 -- Evidence
Quality & Conflict Resolution).

Classifies the reliability of evidence already sitting inside
`atlas.analysis_engine` -- freshness, conflict, dominance, and
unsupported conclusions -- purely by re-reading already-computed
`BusinessRecord`/`BusinessFact`/`ValuationFact`/`Finding` fields.
Performs no new investment analysis. See `engine.py`'s own module
docstring for the full audit and derivation rules.
"""
from __future__ import annotations

from .engine import assess_evidence_quality
from .models import (
    EvidenceConflict,
    EvidenceConflictStatus,
    EvidenceDominance,
    EvidenceFreshness,
    EvidenceQualityLevel,
    EvidenceQualityReport,
    EvidenceWarningCode,
    FactQuality,
    UnsupportedFinding,
)

__all__ = [
    "assess_evidence_quality",
    "EvidenceConflict",
    "EvidenceConflictStatus",
    "EvidenceDominance",
    "EvidenceFreshness",
    "EvidenceQualityLevel",
    "EvidenceQualityReport",
    "EvidenceWarningCode",
    "FactQuality",
    "UnsupportedFinding",
]

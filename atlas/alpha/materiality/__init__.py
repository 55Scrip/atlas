"""Materiality Engine (Atlas Intelligence Sprint -- Materiality &
Priority Engine).

Classifies each already-real `StanceReason` `Explanation` (Sprint 3)
already produced against a fixed, declared `MaterialityLevel`, and
surfaces the single most material item per bucket -- top supporting
evidence, top contradicting evidence, top limiting factor (missing
evidence's own "most valuable" pick is reused verbatim from
Explainability, never recomputed). Performs no new investment analysis.
See `engine.py`'s own module docstring for the full audit and
derivation rules.
"""
from __future__ import annotations

from .engine import assess_materiality
from .models import MaterialEvidence, MaterialityAssessment, MaterialityLevel

__all__ = ["assess_materiality", "MaterialEvidence", "MaterialityAssessment", "MaterialityLevel"]

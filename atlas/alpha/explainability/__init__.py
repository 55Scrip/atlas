"""Explainability Engine (Atlas Intelligence Sprint 3 -- Decision
Explainability & Evidence Trace).

Answers "what drove this conclusion, what argues against it, what is
still missing, and what would help most" -- purely by reclassifying
already-computed `Stance` (Sprint 2) and `CoverageAssessment` (Sprint 1)
fields, never a new analysis engine. See `engine.py`'s own module
docstring for the full derivation rules.
"""
from __future__ import annotations

from .engine import compare_evidence, explain
from .models import ComparisonEvidence, Explanation

__all__ = ["explain", "compare_evidence", "Explanation", "ComparisonEvidence"]

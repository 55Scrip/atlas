"""Exceptions for the Analysis Engine's own contract violations.

Mirrors `atlas.decision_engine.exceptions`'s own discipline exactly:
these represent only an actual contract violation — never ordinary
analytical incompleteness, which the typed `BusinessCategoryStatus`,
`EvaluationState`, and their sibling result types already represent
without raising.
"""
from __future__ import annotations


class AnalysisEngineError(Exception):
    """Base class for all Analysis Engine errors."""


class AnalysisEngineContractError(AnalysisEngineError, ValueError):
    """An Analysis Engine contract type was constructed in a way its own
    invariants forbid — for example, a `BusinessAnalysisResult` claiming
    `EVALUATED` without naming all six `BusinessCategory` members."""

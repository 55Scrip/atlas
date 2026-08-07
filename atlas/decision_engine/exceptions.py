"""Exceptions for the Atlas Decision Engine's own contract violations.

Per the Decision Engine Implementation Sprint 1 (Phase 5): exceptions
here represent only an actual programming error or contract violation —
never ordinary pipeline incompleteness, which the typed
`EvaluationState` and `RecommendationWithheld` result types already
represent without raising.
"""
from __future__ import annotations


class DecisionEngineError(Exception):
    """Base class for all Decision Engine errors."""


class DecisionEngineContractError(DecisionEngineError, ValueError):
    """A Decision Engine contract type was constructed in a way its own
    invariants forbid — for example, a stage result claiming
    `NOT_EVALUATED` with no reason code."""

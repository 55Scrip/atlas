"""Valuation stage placeholder (`Doctrine` §5; Sprint Phase 4).

Deterministic, no-op this sprint: returns `NOT_EVALUATED`
unconditionally. No fair value, price target, buying range, upside,
downside, valuation score, multiple, or DCF value is produced — by
explicit Sprint scope.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    EvaluationState,
    StageNotImplementedReason,
    ValuationResult,
)


def evaluate_valuation(engine_input: DecisionEngineInput) -> ValuationResult:
    """Always returns `NOT_EVALUATED`: the evaluator itself does not exist yet."""
    del engine_input  # unused this sprint; kept for a stable, future-proof stage signature
    return ValuationResult(
        state=EvaluationState.NOT_EVALUATED,
        reason=StageNotImplementedReason.EVALUATOR_NOT_IMPLEMENTED,
    )

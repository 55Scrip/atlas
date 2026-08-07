"""Business Evaluation stage placeholder (`Doctrine` §4; Sprint Phase 4).

Deterministic, no-op this sprint: returns `NOT_EVALUATED`
unconditionally. No quality score, moat score, management score, growth
score, conclusion, or recommendation is produced — by explicit Sprint
scope.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    DecisionEngineInput,
    EvaluationState,
    StageNotImplementedReason,
)


def evaluate_business(engine_input: DecisionEngineInput) -> BusinessEvaluationResult:
    """Always returns `NOT_EVALUATED`: the evaluator itself does not exist yet."""
    del engine_input  # unused this sprint; kept for a stable, future-proof stage signature
    return BusinessEvaluationResult(
        state=EvaluationState.NOT_EVALUATED,
        reason=StageNotImplementedReason.EVALUATOR_NOT_IMPLEMENTED,
    )

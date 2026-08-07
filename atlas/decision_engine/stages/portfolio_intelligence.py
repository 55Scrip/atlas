"""Portfolio Intelligence stage placeholder (`DE-003`; Sprint Phase 4).

Deterministic, no-op this sprint: returns `NOT_EVALUATED`
unconditionally. No concentration, diversification, correlation,
suitability, or portfolio-fit logic is derived — by explicit Sprint
scope, even though `DecisionEngineInput.portfolio_holding` may already
carry real data.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    EvaluationState,
    PortfolioIntelligenceResult,
    StageNotImplementedReason,
)


def evaluate_portfolio_intelligence(
    engine_input: DecisionEngineInput,
) -> PortfolioIntelligenceResult:
    """Always returns `NOT_EVALUATED`: the evaluator itself does not exist yet."""
    del engine_input  # unused this sprint; kept for a stable, future-proof stage signature
    return PortfolioIntelligenceResult(
        state=EvaluationState.NOT_EVALUATED,
        reason=StageNotImplementedReason.EVALUATOR_NOT_IMPLEMENTED,
    )

"""Reasoning stage placeholder (`DE-002`; Sprint Phase 4).

Does not simulate `DE-002`'s seven-part structure with fabricated
prose. Reflects, deterministically, exactly which prior stage results
prevented Reasoning from running — derived from the real prior-stage
states passed in, never hardcoded.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    DecisionEngineInput,
    EvaluationState,
    PortfolioIntelligenceResult,
    ReasoningBlockedBy,
    ReasoningResult,
    ValuationResult,
)


def evaluate_reasoning(
    engine_input: DecisionEngineInput,
    *,
    business_evaluation: BusinessEvaluationResult,
    valuation: ValuationResult,
    portfolio_intelligence: PortfolioIntelligenceResult,
) -> ReasoningResult:
    """Always returns `NOT_EVALUATED` this sprint — Reasoning's own
    evaluator does not exist yet, regardless of upstream progress.
    `blocked_by` is computed from the real upstream states passed in,
    never hardcoded, so it stays correct as upstream stages become real.

    Sprint 4: Business Evaluation, Valuation, and Portfolio Intelligence
    are all `EVALUATED` for every input now, so none of the three
    upstream `ReasoningBlockedBy` members ever fires any more. Rather
    than let `blocked_by` fall silently empty — which the type's own
    contract forbids for a `NOT_EVALUATED` result, and which would also
    misleadingly imply nothing at all blocks Reasoning — the upstream
    list is appended with `REASONING_EVALUATOR_NOT_IMPLEMENTED` whenever
    it is otherwise empty: the honest reason left once no upstream stage
    blocks it is that Reasoning's own evaluator has not been built.
    """
    del engine_input  # unused this sprint; kept for a stable, future-proof stage signature
    blocked_by: list[ReasoningBlockedBy] = []
    if business_evaluation.state is not EvaluationState.EVALUATED:
        blocked_by.append(ReasoningBlockedBy.BUSINESS_EVALUATION_NOT_EVALUATED)
    if valuation.state is not EvaluationState.EVALUATED:
        blocked_by.append(ReasoningBlockedBy.VALUATION_NOT_EVALUATED)
    if portfolio_intelligence.state is not EvaluationState.EVALUATED:
        blocked_by.append(ReasoningBlockedBy.PORTFOLIO_INTELLIGENCE_NOT_EVALUATED)
    if not blocked_by:
        blocked_by.append(ReasoningBlockedBy.REASONING_EVALUATOR_NOT_IMPLEMENTED)

    return ReasoningResult(
        state=EvaluationState.NOT_EVALUATED,
        blocked_by=tuple(blocked_by),
    )

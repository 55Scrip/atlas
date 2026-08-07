"""Recommendation Outcome stage (`DE-001` §2's "Recommendation Withheld
(Not a Seventh Direction)"; `DE-004` §4; Sprint Phase 3/4).

Inspects prior stage results and derives Recommendation Withheld's
`missing_evaluations` from their actual states — never hardcoded
display text. Because no substantive evaluator is implemented this
sprint, every pipeline run returns Recommendation Withheld; this stage
contains no branch that could ever produce a directional outcome.
"""
from __future__ import annotations

from datetime import datetime

from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    DecisionEngineInput,
    EvaluationState,
    MissingEvaluationCategory,
    PortfolioIntelligenceResult,
    ReasoningResult,
    RecommendationOutcomeKind,
    RecommendationWithheld,
    RecommendationWithheldReason,
    RequiredBeforeRecommendation,
    ValuationResult,
)

_REQUIRED_BEFORE_RECOMMENDATION: tuple[RequiredBeforeRecommendation, ...] = (
    RequiredBeforeRecommendation.COMPLETED_BUSINESS_EVALUATION,
    RequiredBeforeRecommendation.COMPLETED_VALUATION_EVALUATION,
    RequiredBeforeRecommendation.COMPLETED_PORTFOLIO_CONTEXT,
    RequiredBeforeRecommendation.COMPLETED_REASONING,
)


def determine_recommendation(
    engine_input: DecisionEngineInput,
    *,
    business_evaluation: BusinessEvaluationResult,
    valuation: ValuationResult,
    portfolio_intelligence: PortfolioIntelligenceResult,
    reasoning: ReasoningResult,
    generated_at: datetime,
) -> RecommendationWithheld:
    """Always returns Recommendation Withheld this sprint. `missing_evaluations`
    is derived from the real stage results passed in, not hardcoded, so
    it stays accurate once a future sprint starts returning `EVALUATED`
    results for some, but not yet all, stages.
    """
    del engine_input  # not yet used to populate current_situation/portfolio_context
    missing: list[MissingEvaluationCategory] = []
    if business_evaluation.state is not EvaluationState.EVALUATED:
        missing.append(MissingEvaluationCategory.BUSINESS_EVALUATION)
    if valuation.state is not EvaluationState.EVALUATED:
        missing.append(MissingEvaluationCategory.VALUATION)
    if portfolio_intelligence.state is not EvaluationState.EVALUATED:
        missing.append(MissingEvaluationCategory.PORTFOLIO_INTELLIGENCE)
    if reasoning.state is not EvaluationState.EVALUATED:
        missing.append(MissingEvaluationCategory.REASONING)

    return RecommendationWithheld(
        kind=RecommendationOutcomeKind.RECOMMENDATION_WITHHELD,
        reason=RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED,
        missing_evaluations=tuple(missing),
        required_before_recommendation=_REQUIRED_BEFORE_RECOMMENDATION,
        generated_at=generated_at,
        current_situation=None,
        portfolio_context=None,
    )

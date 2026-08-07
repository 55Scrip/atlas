"""Decision Engine pipeline orchestration (Sprint Phase 5).

Single public entry point: `run_pipeline`. Executes the five stages in
the fixed order the Doctrine's own architectural principle states:

    Business Evaluation -> Valuation -> Portfolio Intelligence
    -> Reasoning -> Recommendation Outcome

Every stage is a deterministic placeholder this sprint (Phase 4); the
final Recommendation is always Recommendation Withheld (Phase 3). No
stage is ever silently omitted from the output. No exception represents
ordinary incompleteness — exceptions signal only an actual contract
violation (Phase 5's own instruction; see
`atlas.decision_engine.exceptions`).
"""
from __future__ import annotations

from datetime import datetime

from atlas.decision_engine.contracts import DecisionEngineInput, DecisionEngineOutput
from atlas.decision_engine.stages.business_evaluation import evaluate_business
from atlas.decision_engine.stages.portfolio_intelligence import (
    evaluate_portfolio_intelligence,
)
from atlas.decision_engine.stages.reasoning import evaluate_reasoning
from atlas.decision_engine.stages.recommendation import determine_recommendation
from atlas.decision_engine.stages.valuation import evaluate_valuation


def run_pipeline(
    engine_input: DecisionEngineInput, *, generated_at: datetime
) -> DecisionEngineOutput:
    """Run one full Decision Engine pipeline pass.

    `generated_at` is supplied by the caller, never read from the
    system clock inside this function or any stage (Phase 6,
    Determinism): identical `engine_input` and `generated_at` always
    produce a deeply equal `DecisionEngineOutput`. `engine_input` is
    never mutated.
    """
    business_evaluation = evaluate_business(engine_input)
    valuation = evaluate_valuation(engine_input)
    portfolio_intelligence = evaluate_portfolio_intelligence(engine_input)
    reasoning = evaluate_reasoning(
        engine_input,
        business_evaluation=business_evaluation,
        valuation=valuation,
        portfolio_intelligence=portfolio_intelligence,
    )
    recommendation = determine_recommendation(
        engine_input,
        business_evaluation=business_evaluation,
        valuation=valuation,
        portfolio_intelligence=portfolio_intelligence,
        reasoning=reasoning,
        generated_at=generated_at,
    )
    return DecisionEngineOutput(
        case_id=engine_input.case_id,
        evaluated_at=engine_input.evaluated_at,
        business_evaluation=business_evaluation,
        valuation=valuation,
        portfolio_intelligence=portfolio_intelligence,
        reasoning=reasoning,
        recommendation=recommendation,
        generated_at=generated_at,
    )

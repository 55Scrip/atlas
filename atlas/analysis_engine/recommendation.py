"""Recommendation Gate (ATLAS-020, Phase 10).

Wraps `atlas.decision_engine.stages.recommendation.determine_recommendation`
-- reused verbatim, never reimplemented -- and adds the one new gate
condition this sprint introduces: Conviction must clear a threshold.

**No `DirectionalRecommendation` type is defined here, or anywhere in
this codebase.** `atlas.decision_engine.contracts
.RecommendationOutcomeKind.DIRECTIONAL` is a reserved enum member with
no corresponding type -- inventing one now, even an empty/unused one,
would be exactly the kind of fabricated-shape-with-no-real-content this
sprint's "do not fabricate recommendations" constraint forbids. This
module can only ever produce the same `RecommendationWithheld` outcome
`atlas.decision_engine` already produces, plus an honest, additional
fact about whether the one new gate this sprint adds has been met --
never a directional conclusion.

The gate, in full, once a real `DirectionalRecommendation` type exists
in a future sprint:

    Business Analysis EVALUATED
    AND Valuation EVALUATED
    AND Portfolio Intelligence EVALUATED
    AND Reasoning EVALUATED
    AND Conviction >= MODERATE
    -> Directional Recommendation allowed

    otherwise -> RecommendationWithheld

The first four conditions are exactly
`atlas.decision_engine.stages.recommendation`'s own existing
`missing_evaluations` check (reused, not duplicated). The fifth is new.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    DecisionEngineInput,
    PortfolioIntelligenceResult,
    ReasoningResult,
    RecommendationWithheld,
    ValuationResult,
)
from atlas.decision_engine.stages.recommendation import determine_recommendation

__all__ = ["RECOMMENDATION_GATE_MINIMUM_CONVICTION", "RecommendationGateResult", "evaluate_recommendation_gate"]

#: The one new gate condition this sprint adds. Not a magic number --
#: `MODERATE` is the first `ConvictionLevel` this codebase's own
#: Conviction model (`conviction.py`) treats as "the evidence base is
#: genuinely settled" (full coverage, no open contradiction) rather
#: than "still forming."
RECOMMENDATION_GATE_MINIMUM_CONVICTION = ConvictionLevel.MODERATE

_CONVICTION_ORDER = (
    ConvictionLevel.INSUFFICIENT_EVIDENCE,
    ConvictionLevel.LOW,
    ConvictionLevel.MODERATE,
    ConvictionLevel.HIGH,
    ConvictionLevel.VERY_HIGH,
)


@dataclass(frozen=True)
class RecommendationGateResult:
    """`recommendation` is always `RecommendationWithheld` today -- see
    module docstring. `conviction_gate_met` is the one new fact this
    sprint adds: whether Conviction alone would clear the threshold, so
    a future sprint that finally builds a real `DirectionalRecommendation`
    type can see immediately which of its two gates (decision-engine
    evaluation completeness, Conviction) is the blocking one, without
    re-deriving either."""

    recommendation: RecommendationWithheld
    conviction_gate_met: bool
    conviction: ConvictionAssessment


def evaluate_recommendation_gate(
    engine_input: DecisionEngineInput,
    *,
    business_evaluation: BusinessEvaluationResult,
    valuation: ValuationResult,
    portfolio_intelligence: PortfolioIntelligenceResult,
    reasoning: ReasoningResult,
    conviction: ConvictionAssessment,
    generated_at: datetime,
) -> RecommendationGateResult:
    """Deterministic: identical inputs always produce an identical
    `RecommendationGateResult`. Delegates the four-stage completeness
    check entirely to `determine_recommendation` (reused, not
    duplicated); only the Conviction gate is computed here."""
    recommendation = determine_recommendation(
        engine_input,
        business_evaluation=business_evaluation,
        valuation=valuation,
        portfolio_intelligence=portfolio_intelligence,
        reasoning=reasoning,
        generated_at=generated_at,
    )
    conviction_gate_met = _CONVICTION_ORDER.index(conviction.level) >= _CONVICTION_ORDER.index(
        RECOMMENDATION_GATE_MINIMUM_CONVICTION
    )
    return RecommendationGateResult(
        recommendation=recommendation, conviction_gate_met=conviction_gate_met, conviction=conviction
    )

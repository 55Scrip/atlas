"""Recommendation Gate (ATLAS-020, Phase 10) and the Recommendation
domain model (DE-007, "Implementation Step 1").

Wraps `atlas.decision_engine.stages.recommendation.determine_recommendation`
-- reused verbatim, never reimplemented -- and adds the one new gate
condition ATLAS-020 introduced: Conviction must clear a threshold.

**`ComputedDirectionalRecommendation` is now defined** (below) -- the
type `docs/atlas_decision_engine/DE-007-Recommendation-Domain-Model.md`
specifies and `atlas.decision_engine.contracts
.RecommendationOutcomeKind.DIRECTIONAL` has reserved a discriminant value
for since Sprint 1. Defining the type is not the same as being able to
construct one from a real analysis run: **no code anywhere in this
package ever constructs a `ComputedDirectionalRecommendation`.**
`evaluate_recommendation_gate` below still always returns
`RecommendationWithheld`, for a specific, documented reason -- see that
function's own docstring. Two genuine capability gaps block it, found
during DE-007 "Implementation Step 1" and reported rather than papered
over:

1. **No Direction selector exists.** Nothing in `atlas.decision_engine`
   or `atlas.analysis_engine` decides *which* of `DE-001` §2's six
   directions (Buy/Add/Hold/Trim/Exit/No Action) a given analysis
   supports. `conviction_gate_met` (below) has always meant "Conviction
   alone would not block a direction" -- it has never meant a direction
   was actually selected.
2. **No Direction selector to feed a Recommendation-specific Conviction
   assessment into.** `ConvictionLevel` (`conviction.py`, five levels)
   remains a different, already-real, case-wide field -- `DE-004` §3's
   own 3-level Atlas Conviction Level (`RecommendationConvictionLevel`,
   imported below from `recommendation_conviction.py`, "Recommendation
   Backend Step 2") is a distinct field DE-007 §11 requires be
   independently computed, never silently derived from the five-level
   scale. That computation now exists
   (`recommendation_conviction.calculate_recommendation_conviction`) --
   but it is not yet consumed anywhere, because gap 1 (no Direction
   selector) still blocks `ComputedDirectionalRecommendation` from ever
   being constructed by real code. A conviction level with no direction
   to attach it to is not a Recommendation.

Inventing a Direction selector to make `ComputedDirectionalRecommendation`
constructible would be exactly the "do not invent a decision rule"
constraint this sprint forbids. The type exists so a future sprint that
builds one has a doctrine-correct shape, and a real Conviction
computation, ready to populate; this sprint stops here.

The gate, in full, once a real Direction selector and Recommendation
Conviction computation both exist:

    Business Analysis EVALUATED
    AND Valuation EVALUATED
    AND Portfolio Intelligence EVALUATED
    AND Reasoning EVALUATED
    AND Conviction >= MODERATE
    -> Directional Recommendation allowed

    otherwise -> RecommendationWithheld

The first four conditions are exactly
`atlas.decision_engine.stages.recommendation`'s own existing
`missing_evaluations` check (reused, not duplicated). The fifth
(`conviction_gate_met`) was ATLAS-020's addition.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.recommendation_conviction import RecommendationConvictionLevel
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.outcome.entity import Outcome
from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    ContradictionSummary,
    DecisionEngineInput,
    OpenQuestion,
    PortfolioContextSummary,
    PortfolioFinding,
    PortfolioIntelligenceResult,
    ReasoningResult,
    ReasoningSummary,
    RecommendationWithheld,
    SupportingEvidenceSummary,
    ValuationResult,
)
from atlas.decision_engine.stages.recommendation import determine_recommendation

__all__ = [
    "RECOMMENDATION_GATE_MINIMUM_CONVICTION",
    "RecommendationGateResult",
    "evaluate_recommendation_gate",
    "RecommendationDirection",
    "RecommendationConvictionLevel",
    "RecommendationReasoning",
    "RecommendationAlternative",
    "ComputedDirectionalRecommendation",
]


# ---------------------------------------------------------------------------
# Recommendation domain model (DE-007, "Implementation Step 1")
# ---------------------------------------------------------------------------


class RecommendationDirection(str, Enum):
    """`DE-001` §2's six directions, exactly as doctrine defines them --
    never reused from, and never mapped to, the Investor's own recorded
    `BUY | SELL | HOLD | WATCH | PASS` decision type. `DE-006` §4
    already draws this boundary for Atlas Recommendation generally;
    this enum enforces it structurally by construction: no member name
    or value overlaps the Investor's own vocabulary."""

    BUY = "buy"
    ADD = "add"
    HOLD = "hold"
    TRIM = "trim"
    EXIT = "exit"
    NO_ACTION = "no_action"


# `RecommendationConvictionLevel` -- `DE-004` §3's Atlas Conviction
# Level, a distinct, three-level scale specific to a Recommendation's
# own Direction, deliberately **not**
# `atlas.analysis_engine.conviction.ConvictionLevel` (five levels,
# case-wide, already real -- `DE-007` §11's own disambiguation) -- is
# now defined in, and imported above from, `recommendation_conviction.py`
# ("Recommendation Backend Step 2"), which also owns the actual
# computation (`calculate_recommendation_conviction`). Re-exported via
# `__all__` above for backward-compatible imports, since
# `ComputedDirectionalRecommendation` below was originally authored
# referencing this name from this module.


@dataclass(frozen=True)
class RecommendationReasoning:
    """`DE-002`'s reasoning content a Recommendation carries, per `DE-007`
    §8A -- each field embeds, by reference, the exact
    `atlas.decision_engine.contracts` type `DE-002`'s own structure
    already produces (`current_situation`/`supporting_evidence`/
    `contradicting_evidence`/`portfolio_context` are never duplicated
    into a parallel shape). `what_would_change` is `DE-002` §2.7 -- unlike
    `atlas.decision_engine.contracts.ReasoningFinding`, which
    structurally forces this field empty because *it* is not the
    provider `DE-002` §2.7 requires, a `ComputedDirectionalRecommendation`
    is that provider (`DE-007` §8A's own note); this type does not
    forbid populating it. No code populates it yet -- there is no
    change-trigger computation to draw from -- but the field is not
    artificially locked shut the way `ReasoningFinding.what_would_change`
    is.
    """

    current_situation: ReasoningSummary
    supporting_evidence: SupportingEvidenceSummary
    contradicting_evidence: ContradictionSummary
    portfolio_context: PortfolioContextSummary
    what_would_change: tuple[OpenQuestion, ...] = ()


@dataclass(frozen=True)
class RecommendationAlternative:
    """`DE-007` §8A `alternatives` entry -- qualitative Opportunity Cost
    content (`DE-003` §Opportunity Cost), never a numeric score or
    ranking (`UX-012B` Comparison precedent, already cited by `DE-003`).
    """

    label: str
    rationale: str

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise AnalysisEngineContractError(
                "RecommendationAlternative.label must be non-empty."
            )
        if not self.rationale.strip():
            raise AnalysisEngineContractError(
                "RecommendationAlternative.rationale must be non-empty -- an "
                "alternative with no stated rationale is exactly the "
                "unattributed claim DE-002 §2.2/§2.3 forbid."
            )


@dataclass(frozen=True)
class ComputedDirectionalRecommendation:
    """`DE-007` §8A -- derived, current-state analysis. **Not persisted
    merely because it is computed** (`DE-007` §1, §9 -- the locked
    Recommendation Ontology Decision): this type carries no
    `HistoricalRecommendationSnapshot` field, no `RecommendationResponse`
    / accepted-dismissed-acted-upon state, no Execution Guidance field
    (`DE-006` §4's one-way dependency stays exactly as `DE-006` §9
    defined it -- `ExecutionGuidance.recommendationId` references this
    type's own `recommendation_instance_id`; nothing here references
    back), and no persistence identity beyond the one `DE-007` §6
    requires: a value stable for the lifetime of one computed instance,
    generated by whatever mechanism the caller chooses -- this type
    does not canonize an algorithm.

    `RecommendationWithheld` (`atlas.decision_engine.contracts`) is the
    other member of the same `RecommendationOutcomeKind` union and is
    untouched by this type -- see that type and `RecommendationGateResult`
    below for how the two relate.
    """

    recommendation_instance_id: str
    case_id: CaseId
    generated_at: datetime
    direction: RecommendationDirection
    direction_statement: str
    conviction_level: RecommendationConvictionLevel
    conviction_reason: str
    reasoning: RecommendationReasoning
    portfolio_factors: PortfolioFinding
    alternatives: tuple[RecommendationAlternative, ...] = ()
    decision_history: tuple[Decision, ...] = ()
    outcome_history: tuple[Outcome, ...] = ()

    def __post_init__(self) -> None:
        if not self.recommendation_instance_id.strip():
            raise AnalysisEngineContractError(
                "ComputedDirectionalRecommendation.recommendation_instance_id "
                "must be non-empty -- DE-007 §6 requires a stable "
                "computed-instance identity, even though this type does not "
                "specify how it is generated."
            )
        if not isinstance(self.direction, RecommendationDirection):
            raise AnalysisEngineContractError(
                "ComputedDirectionalRecommendation.direction must be a "
                "RecommendationDirection -- DE-001 §2's six directions "
                "only, never the Investor's own BUY/SELL/HOLD/WATCH/PASS "
                "decision type (DE-006 §4's boundary)."
            )
        if not self.direction_statement.strip():
            raise AnalysisEngineContractError(
                "ComputedDirectionalRecommendation.direction_statement must "
                "be non-empty -- DE-001 §3's Why element requires a stated "
                "conclusion, never a bare label."
            )
        if not isinstance(self.conviction_level, RecommendationConvictionLevel):
            raise AnalysisEngineContractError(
                "ComputedDirectionalRecommendation.conviction_level must be "
                "a RecommendationConvictionLevel (DE-004 §3's own 3-level "
                "scale) -- never atlas.analysis_engine.conviction"
                ".ConvictionLevel or any other value. DE-007 §11 requires "
                "these two Conviction concepts stay structurally distinct, "
                "never silently interchangeable."
            )
        if not self.conviction_reason.strip():
            raise AnalysisEngineContractError(
                "ComputedDirectionalRecommendation.conviction_reason must be "
                "non-empty -- DE-004 §3 requires the specific evidentiary "
                "basis for the level, never a bare label."
            )


# ---------------------------------------------------------------------------
# Recommendation Gate (ATLAS-020, Phase 10)
# ---------------------------------------------------------------------------

#: The one new gate condition ATLAS-020 added. Not a magic number --
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
    """`recommendation` is always a `RecommendationWithheld` instance
    today -- see module docstring for the two specific capability gaps
    (no Direction selector, no Recommendation-specific Conviction
    computation) that keep it that way. The field's type is widened to
    `RecommendationWithheld | ComputedDirectionalRecommendation` so
    downstream code has a doctrine-correct shape to narrow against once
    a future sprint closes those gaps -- this is a type-level statement
    of intent, not a behavior change: `evaluate_recommendation_gate`
    below never constructs the second branch.

    This widening intentionally happens here, in `atlas.analysis_engine`,
    not on `atlas.decision_engine.contracts.DecisionEngineOutput` --
    `ComputedDirectionalRecommendation` depends on Conviction (this
    package's exclusive domain, per `__init__.py`'s own ownership
    statement), and `atlas.decision_engine` may never import
    `atlas.analysis_engine` (the one-way boundary
    `tests/test_architecture_boundaries.py
    ::test_analysis_engine_only_reads_core_and_decision_engine` already
    enforces in the other direction). `DecisionEngineOutput.recommendation`
    stays exactly `RecommendationWithheld`, untouched.

    `conviction_gate_met` is the one new fact ATLAS-020 added: whether
    Conviction alone would clear the threshold, so a future sprint that
    finally builds a real Direction selector can see immediately which
    of its two gates (decision-engine evaluation completeness,
    Conviction) is the blocking one, without re-deriving either."""

    recommendation: RecommendationWithheld | ComputedDirectionalRecommendation
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
    duplicated); only the Conviction gate is computed here.

    Always returns a `RecommendationWithheld` in `.recommendation` --
    per this module's own docstring, no Direction selector and no
    Recommendation-specific Conviction computation exist yet, so
    constructing a `ComputedDirectionalRecommendation` here would
    require inventing both, which this sprint's own constraints
    forbid. `RecommendationOutcomeKind.DIRECTIONAL` stays a reserved,
    unconstructed discriminant, exactly as before."""
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

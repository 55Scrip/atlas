"""Shared contracts for the Atlas Decision Engine pipeline.

Governed by `docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` and
`docs/atlas_decision_engine/DE-001` through `DE-005`. See
`atlas/decision_engine/__init__.py` for this package's architectural
boundary (not a Core Domain Object; one-way reads from `atlas.core`
only; no directional recommendation is ever produced this sprint).

Every type below is `@dataclass(frozen=True)` or `class X(str, Enum)`,
matching the convention already established throughout
`atlas/core/domain/*` — no Pydantic (reserved, in this codebase, for
the API serialization boundary only) and no unrestricted string map.

Absent vs. empty vs. unsupported vs. unevaluated (Sprint Phase 2):

- **Absent** — a field holds `None`. `DecisionEngineInput.portfolio_holding`
  is `None` when no holding is linked to the Case at all.
- **Empty** — a tuple field is `()`. `DecisionEngineInput.decisions` is
  `()` when the Case has been looked up and genuinely has zero recorded
  Decisions yet — a real, meaningful fact, distinct from absence.
- **Unsupported** — a data category this sprint's doctrine explicitly
  excludes (market data, news, valuation inputs, correlation data) has
  **no field here at all**. Unsupported data is represented by absence
  from this contract's shape, not by a null value within it, so a
  future reviewer cannot mistake "not modeled" for "modeled but empty."
- **Unevaluated** — not a property of input data. It is a pipeline
  *stage result's own* state (`EvaluationState.NOT_EVALUATED`, below),
  produced from this input; it is never carried by the input itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.outcome.entity import Outcome
from atlas.decision_engine.exceptions import DecisionEngineContractError

# ---------------------------------------------------------------------------
# Evaluation state (Phase 2 — Evaluation State)
# ---------------------------------------------------------------------------


class EvaluationState(str, Enum):
    """The status of a single pipeline stage's evaluation.

    A small, closed set — not a large generic status taxonomy (explicit
    Sprint instruction). `NOT_EVALUATED` is this sprint's only real
    state: the evaluator has not been implemented yet. It is never
    labeled a failure. `INSUFFICIENT_INPUT` and `EVALUATED` are reserved
    for a future sprint with a real evaluator; no code in this sprint
    ever constructs either, so a later sprint can start returning them
    without widening this enum's meaning.
    """

    NOT_EVALUATED = "not_evaluated"
    EVALUATED = "evaluated"
    INSUFFICIENT_INPUT = "insufficient_input"


class StageNotImplementedReason(str, Enum):
    """Why a stage returned `NOT_EVALUATED` in this sprint."""

    EVALUATOR_NOT_IMPLEMENTED = "evaluator_not_implemented"


def _require_reason_when_not_evaluated(
    state: EvaluationState, reason: StageNotImplementedReason | None
) -> None:
    if state is EvaluationState.NOT_EVALUATED and reason is None:
        raise DecisionEngineContractError(
            "A NOT_EVALUATED stage result must carry a reason code."
        )


# ---------------------------------------------------------------------------
# Decision Engine Input (Phase 2 — Decision Engine Input)
# ---------------------------------------------------------------------------


class ReconciliationState(str, Enum):
    """Mirrors `atlas.alpha.portfolio.models.ReconciliationStatus`'s three
    values by shape only. This package does not import `atlas.alpha`
    directly — this sprint's locked scope is one-way reads from
    `atlas.core` only. A future sprint's composition layer is
    responsible for mapping Alpha's own enum onto this one, or for
    importing it directly once that coupling is explicitly authorized.
    """

    NONE = "NONE"
    UPDATED = "UPDATED"
    AWAITING_RECONCILIATION = "AWAITING_RECONCILIATION"


@dataclass(frozen=True)
class PortfolioHoldingContext:
    """Read-only snapshot of one portfolio holding, shaped to mirror
    `AlphaHolding`'s own fields — see `ReconciliationState` above for why
    this sprint does not import `atlas.alpha` directly. Populated by a
    future sprint's caller, not by this package.
    """

    ticker: str
    weight_percent: float
    value_absolute: float | None = None
    reconciliation_status: ReconciliationState = ReconciliationState.NONE


@dataclass(frozen=True)
class TradeLogEntry:
    """Read-only snapshot of one executed trade, shaped to mirror
    `AlphaTradeLogEntry`'s own fields (see `PortfolioHoldingContext`).
    """

    security: str
    transaction_type: str
    quantity: float
    execution_price: float
    executed_at: datetime


@dataclass(frozen=True)
class DecisionEngineInput:
    """The single immutable input to one Decision Engine pipeline run.

    Every field is real, already-captured data this package reads
    one-way from `atlas.core.domain` — nothing here is fabricated, and
    no field the current backend cannot supply is modeled.

    `evaluated_at` is supplied by the caller, never read from the system
    clock inside this package, so a full pipeline run is reproducible
    (Phase 6, Determinism).
    """

    case_id: CaseId
    evaluated_at: datetime
    decisions: tuple[Decision, ...] = ()
    outcomes: tuple[Outcome, ...] = ()
    observations: tuple[Observation, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    portfolio_holding: PortfolioHoldingContext | None = None
    trade_log: tuple[TradeLogEntry, ...] = ()


# ---------------------------------------------------------------------------
# Stage results (Phase 2 — Business Evaluation / Valuation / Portfolio
# Intelligence / Reasoning Result)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessEvaluationResult:
    """`Doctrine` §4 (Business Evaluation) output shape.

    Contains no quality score, moat score, management score, growth
    score, conclusion, or recommendation — by explicit Sprint scope.
    This sprint's placeholder evaluator always returns `NOT_EVALUATED`.
    """

    state: EvaluationState
    reason: StageNotImplementedReason | None = None

    def __post_init__(self) -> None:
        _require_reason_when_not_evaluated(self.state, self.reason)


@dataclass(frozen=True)
class ValuationResult:
    """`Doctrine` §5 (Valuation Philosophy) output shape.

    Contains no fair value, price target, buying range, upside,
    downside, valuation score, multiple, or DCF value — by explicit
    Sprint scope. This sprint's placeholder evaluator always returns
    `NOT_EVALUATED`.
    """

    state: EvaluationState
    reason: StageNotImplementedReason | None = None

    def __post_init__(self) -> None:
        _require_reason_when_not_evaluated(self.state, self.reason)


@dataclass(frozen=True)
class PortfolioIntelligenceResult:
    """`DE-003` (Portfolio Intelligence) output shape.

    No concentration, diversification, correlation, suitability, or
    portfolio-fit logic is computed this sprint — by explicit Sprint
    scope. This sprint's placeholder evaluator always returns
    `NOT_EVALUATED`.
    """

    state: EvaluationState
    reason: StageNotImplementedReason | None = None

    def __post_init__(self) -> None:
        _require_reason_when_not_evaluated(self.state, self.reason)


class ReasoningBlockedBy(str, Enum):
    """Which prior stage(s) prevented Reasoning from running, per
    `DE-002` §4's own dependency: Reasoning cannot proceed while
    Business Evaluation, Valuation, or Portfolio Intelligence is
    unevaluated."""

    BUSINESS_EVALUATION_NOT_EVALUATED = "business_evaluation_not_evaluated"
    VALUATION_NOT_EVALUATED = "valuation_not_evaluated"
    PORTFOLIO_INTELLIGENCE_NOT_EVALUATED = "portfolio_intelligence_not_evaluated"


@dataclass(frozen=True)
class ReasoningResult:
    """`DE-002`'s seven-part Reasoning Structure output shape.

    Does not simulate the seven-part structure with fabricated prose —
    by explicit Sprint scope. States only that Reasoning has not been
    performed, and exactly which prior stage results prevented it.
    """

    state: EvaluationState
    blocked_by: tuple[ReasoningBlockedBy, ...] = ()

    def __post_init__(self) -> None:
        if self.state is EvaluationState.NOT_EVALUATED and not self.blocked_by:
            raise DecisionEngineContractError(
                "A NOT_EVALUATED ReasoningResult must name at least one "
                "blocking prior stage."
            )


# ---------------------------------------------------------------------------
# Recommendation Outcome (Phase 3 — Formal Recommendation Withheld Outcome)
# ---------------------------------------------------------------------------


class RecommendationOutcomeKind(str, Enum):
    """The two future branches `DE-001` §2 and `DE-004` §4 define.

    Only `RECOMMENDATION_WITHHELD` is ever produced by this sprint.
    `DIRECTIONAL` is named now, as a reserved discriminant value, so a
    later sprint does not need to widen this enum — but no type for a
    directional outcome exists yet in this package, and no code anywhere
    in this sprint constructs one. Deliberately minimal: defining a full
    directional-outcome shape (with a direction and a conviction level)
    is recommendation logic, out of this sprint's explicit scope.
    """

    DIRECTIONAL = "directional"
    RECOMMENDATION_WITHHELD = "recommendation_withheld"


class RecommendationWithheldReason(str, Enum):
    """Tightly scoped, per the Sprint's explicit instruction not to
    introduce an unrestricted string map. This sprint only ever produces
    `ENGINE_NOT_IMPLEMENTED`. `EVIDENCE_INSUFFICIENT` is named now so a
    later sprint with real evaluators does not need to widen this enum
    for the ordinary "ran the evaluators, still not enough evidence"
    case (`DE-004` §4's own general definition of Recommendation
    Withheld, of which "the engine isn't built yet" is this sprint's
    only instance).
    """

    ENGINE_NOT_IMPLEMENTED = "engine_not_implemented"
    EVIDENCE_INSUFFICIENT = "evidence_insufficient"


class MissingEvaluationCategory(str, Enum):
    """Which pipeline stage(s) have not produced a real evaluation."""

    BUSINESS_EVALUATION = "business_evaluation"
    VALUATION = "valuation"
    PORTFOLIO_INTELLIGENCE = "portfolio_intelligence"
    REASONING = "reasoning"


class RequiredBeforeRecommendation(str, Enum):
    """What `DE-004` §4 requires before a direction could ever be
    selected."""

    COMPLETED_BUSINESS_EVALUATION = "completed_business_evaluation"
    COMPLETED_VALUATION_EVALUATION = "completed_valuation_evaluation"
    COMPLETED_PORTFOLIO_CONTEXT = "completed_portfolio_context"
    COMPLETED_REASONING = "completed_reasoning"


@dataclass(frozen=True)
class RecommendationWithheld:
    """The only Recommendation Outcome this sprint's pipeline may
    produce (`DE-001` §2's "Recommendation Withheld (Not a Seventh
    Direction)"; `DE-004` §4). Structurally guarantees the Doctrine's
    own invariants:

    - no `direction` field exists on this type at all — nothing here
      could be misread as Buy/Add/Hold/Trim/Exit/No Action (`DE-002`
      §4's "Direction ... is omitted entirely");
    - no `conviction` field exists on this type at all (`DE-002` §4's
      "Conviction ... is omitted entirely");
    - `reason` and `missing_evaluations` together state *why*, per
      `DE-004` §4's "Atlas states, specifically, why the available
      evidence is insufficient";
    - `required_before_recommendation` states what `DE-004` §4 calls
      "what evidence or clarification would allow it to form a view";
    - `current_situation` and `portfolio_context` are optional and,
      per this sprint's explicit scope, always `None` — included as
      fields now (`DE-002` §4 permits, does not require, stating them)
      so a later sprint can populate them from real data without
      changing this type's shape.
    """

    kind: RecommendationOutcomeKind
    reason: RecommendationWithheldReason
    missing_evaluations: tuple[MissingEvaluationCategory, ...]
    required_before_recommendation: tuple[RequiredBeforeRecommendation, ...]
    generated_at: datetime
    current_situation: str | None = None
    portfolio_context: str | None = None

    def __post_init__(self) -> None:
        if self.kind is not RecommendationOutcomeKind.RECOMMENDATION_WITHHELD:
            raise DecisionEngineContractError(
                "RecommendationWithheld.kind must be RECOMMENDATION_WITHHELD; "
                "no other outcome type exists in this sprint."
            )


# ---------------------------------------------------------------------------
# Pipeline output (Phase 5 — Pipeline Orchestration)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionEngineOutput:
    """The single, always-structurally-complete result of one Decision
    Engine pipeline run. Per Phase 5: "The final output must always be
    complete and structurally valid, even when every substantive stage
    is unevaluated." No stage is ever omitted from this type.
    """

    case_id: CaseId
    evaluated_at: datetime
    business_evaluation: BusinessEvaluationResult
    valuation: ValuationResult
    portfolio_intelligence: PortfolioIntelligenceResult
    reasoning: ReasoningResult
    recommendation: RecommendationWithheld
    generated_at: datetime

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
from atlas.core.domain.observation.value_objects import ObservationId
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


class DurabilityNotAssessableReason(str, Enum):
    """Why Durability (`Doctrine` §4 dimension 1) could not be assessed."""

    NO_BUSINESS_FACT_DATA_IN_INPUT = "no_business_fact_data_in_input"


@dataclass(frozen=True)
class DurabilityFinding:
    """`Doctrine` §4 dimension 1 (Durability): "Does the business have a
    reason to still exist, on comparable or better terms... a defensible
    position relative to competitors or substitutes, and a balance sheet
    that can survive a bad year."

    Always `EvaluationState.INSUFFICIENT_INPUT` this sprint, by explicit
    Sprint 2 lock: `DecisionEngineInput` carries only Case-scoped
    Decision/Outcome/Observation/Evidence records — no external
    company-fact, financial, or market data — so there is no factual
    basis here to conclude anything about competitive position,
    balance-sheet resilience, moat, management, or growth quality.
    Structurally guarantees this: no `moat`, `competitive_position`,
    `balance_sheet`, `management`, `business_quality`, or
    `growth_quality` field exists on this type at all, and
    `__post_init__` forbids constructing it with any state other than
    `INSUFFICIENT_INPUT`.

    Not to be confused with `atlas.core.domain.evaluation` — a distinct,
    unrelated Core Domain Object: the Investor's own assessment of an
    Outcome ("did it confirm or contradict what was expected, and why").
    That Core concept is never read, modified, or referenced here.
    """

    state: EvaluationState
    reason: DurabilityNotAssessableReason

    def __post_init__(self) -> None:
        if self.state is not EvaluationState.INSUFFICIENT_INPUT:
            raise DecisionEngineContractError(
                "DurabilityFinding.state must be INSUFFICIENT_INPUT this "
                "sprint; DecisionEngineInput carries no business-fact data "
                "to assess durability from."
            )


class ObservationEpistemicStatus(str, Enum):
    """`Doctrine` §4 dimension 3 (what is knowable vs. what is assumed),
    applied per-Observation using only structural, id-based facts
    already present in `DecisionEngineInput` — never a semantic or
    NLP-derived judgment about an Observation's or Evidence's own
    statement text.

    - `SUPPORTED` — at least one `Evidence` item with `direction ==
      SUPPORTS` is linked, and none with `direction == CHALLENGES`.
    - `CHALLENGED` — at least one `CHALLENGES` item is linked, and none
      with `SUPPORTS`.
    - `CONTRADICTED` — both a `SUPPORTS` and a `CHALLENGES` item are
      linked to the same Observation — an unresolved area, per Doctrine
      §4 dimension 3's "unresolved or contradictory areas."
    - `ASSUMED` — no `Evidence` at all is linked to this Observation: an
      unsubstantiated claim, per Doctrine §4 dimension 3's "claims that
      remain assumptions."
    """

    SUPPORTED = "supported"
    CHALLENGED = "challenged"
    CONTRADICTED = "contradicted"
    ASSUMED = "assumed"


@dataclass(frozen=True)
class ObservationEvidenceClassification:
    """One Observation's evidence status — the atomic fact both Evidence
    Quality (dimension 2) and Knowable-vs-Assumed (dimension 3) findings
    below are built from."""

    observation_id: ObservationId
    status: ObservationEpistemicStatus
    supporting_evidence_count: int
    challenging_evidence_count: int


class EvidenceGapKind(str, Enum):
    """A specific, named kind of missing evidence — never a bare,
    unrestricted string."""

    NO_EVIDENCE_RECORDED = "no_evidence_recorded"
    """Case-wide: zero Evidence items exist anywhere in this input."""

    OBSERVATION_WITHOUT_EVIDENCE = "observation_without_evidence"
    """One specific Observation (`reference`) has zero linked Evidence."""

    DECISION_WITHOUT_LINKED_OBSERVATION = "decision_without_linked_observation"
    """One specific Decision (`reference`) has no `observation_id` at
    all, so its stated reason has no Observation to trace evidence
    through."""


@dataclass(frozen=True)
class EvidenceGap:
    """One explicit, named evidence gap (`Doctrine` §4 dimension 3:
    "explicit evidence gaps"). `reference` is `str(ObservationId)` or
    `str(DecisionId)` depending on `kind`; `None` for the case-wide
    `NO_EVIDENCE_RECORDED` kind, which names no single reference."""

    kind: EvidenceGapKind
    reference: str | None = None


class EvidenceCoverageLevel(str, Enum):
    """How many of the Case's recorded Observations have at least one
    linked Evidence item — a categorical bucket derived from a real
    count comparison, never a percentage or a score."""

    NOT_APPLICABLE = "not_applicable"
    """Zero Observations are recorded in this input at all."""

    NONE = "none"
    """At least one Observation is recorded; none has any Evidence."""

    PARTIAL = "partial"
    """Some, but not all, recorded Observations have Evidence."""

    FULL = "full"
    """Every recorded Observation has at least one Evidence item."""


@dataclass(frozen=True)
class EvidenceQualityFindings:
    """`Doctrine` §4 dimensions 2 (quality of the evidence available) and
    3 (what is knowable vs. what is assumed), together — the only two of
    the three Business Evaluation dimensions `DecisionEngineInput` can
    honestly support this sprint (see `DurabilityFinding`).

    Every field here is a direct, structural fact: a count, a
    categorical bucket derived from a count comparison, or a
    cross-reference between real ids already present in
    `DecisionEngineInput`. No semantic or NLP-derived judgment about any
    statement's content is performed anywhere in this module, and no
    field here is a numeric score, probability, or percentage.
    """

    total_evidence_count: int
    supporting_evidence_count: int
    challenging_evidence_count: int
    coverage: EvidenceCoverageLevel
    observation_classifications: tuple[ObservationEvidenceClassification, ...]
    evidence_gaps: tuple[EvidenceGap, ...]


@dataclass(frozen=True)
class BusinessEvaluationResult:
    """`Doctrine` §4 (Business Evaluation) output shape.

    Sprint 1: always `NOT_EVALUATED` (no evaluator existed).

    Sprint 2: the evaluator is real for two of Doctrine §4's three
    dimensions. `evidence_quality` (dimensions 2 and 3) is always
    populated with a genuine, deterministic conclusion — even "no
    evidence recorded" is a real, honest finding, not a failure to
    evaluate — so `state` is always `EVALUATED` this sprint.
    `durability` (dimension 1) is carried separately and is always
    `INSUFFICIENT_INPUT` (see `DurabilityFinding`).

    Still contains no quality score, moat score, management score,
    growth score, business-quality verdict, or recommendation of any
    kind — by explicit Sprint 2 lock. `state`/`reason` retain Sprint 1's
    original shape unchanged (additive expansion only), so a future
    input this evaluator genuinely cannot process would still have a
    `NOT_EVALUATED` path available without a further contract change.
    """

    state: EvaluationState
    reason: StageNotImplementedReason | None = None
    durability: DurabilityFinding | None = None
    evidence_quality: EvidenceQualityFindings | None = None

    def __post_init__(self) -> None:
        _require_reason_when_not_evaluated(self.state, self.reason)
        if self.state is EvaluationState.EVALUATED and (
            self.durability is None or self.evidence_quality is None
        ):
            raise DecisionEngineContractError(
                "An EVALUATED BusinessEvaluationResult must carry both "
                "durability and evidence_quality findings."
            )


class ValuationNotAssessableReason(str, Enum):
    """Why substantive Valuation (`Doctrine` §5) could not be assessed."""

    NO_VALUATION_DATA_IN_INPUT = "no_valuation_data_in_input"


@dataclass(frozen=True)
class ValuationFinding:
    """`Doctrine` §5's substantive content: valuation thesis, named
    assumptions, ranges, and change triggers — intrinsic value, fair
    value, multiples, upside/downside.

    Always `EvaluationState.INSUFFICIENT_INPUT` this sprint, by explicit
    Sprint 3 lock: `DecisionEngineInput` carries no market price,
    financial-statement, multiple, or forecast data, and — unlike
    Business Evaluation's Observation/Evidence records — nothing in the
    input marks any Decision, Observation, or Evidence as being *about*
    valuation specifically, so there is no honest way to identify a
    "valuation thesis" among the undifferentiated records even
    structurally. Parsing free text to infer topic is explicitly
    forbidden this sprint. Structurally guarantees this: no `cheap`,
    `expensive`, `undervalued`, `overvalued`, `fair_value`,
    `intrinsic_value`, `buying_range`, `target_price`,
    `margin_of_safety`, `expected_return`, `upside`, `downside`, or
    `valuation_score` field exists on this type at all, and
    `__post_init__` forbids constructing it with any state other than
    `INSUFFICIENT_INPUT`.
    """

    state: EvaluationState
    reason: ValuationNotAssessableReason

    def __post_init__(self) -> None:
        if self.state is not EvaluationState.INSUFFICIENT_INPUT:
            raise DecisionEngineContractError(
                "ValuationFinding.state must be INSUFFICIENT_INPUT this "
                "sprint; DecisionEngineInput carries no valuation-specific "
                "data to assess substantive valuation from."
            )


class ExecutionPriceHistoryCoverage(str, Enum):
    """Whether any recorded execution-price history exists for the Case
    — a structural coverage fact, never a judgment about the price
    level itself."""

    ABSENT = "absent"
    PRESENT = "present"


@dataclass(frozen=True)
class ExecutionPriceHistoryFinding:
    """Execution-price-**history coverage** only — built entirely from
    `DecisionEngineInput.trade_log` presence, count, and timestamps. Not
    a valuation-quality, fair-value-history, valuation-correctness, or
    valuation-thesis-support finding: no inference from the price level
    itself (whether a price was high, low, good, or bad) is ever
    performed anywhere in this type or the module that produces it.

    `earliest_executed_at`/`latest_executed_at` are `None` when
    `coverage` is `ABSENT` — there is nothing to bound.
    """

    coverage: ExecutionPriceHistoryCoverage
    entry_count: int
    earliest_executed_at: datetime | None = None
    latest_executed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.coverage is ExecutionPriceHistoryCoverage.ABSENT and self.entry_count != 0:
            raise DecisionEngineContractError(
                "ExecutionPriceHistoryFinding: ABSENT coverage must have "
                "entry_count == 0."
            )
        if self.coverage is ExecutionPriceHistoryCoverage.PRESENT and self.entry_count < 1:
            raise DecisionEngineContractError(
                "ExecutionPriceHistoryFinding: PRESENT coverage must have "
                "entry_count >= 1."
            )


@dataclass(frozen=True)
class ValuationResult:
    """`Doctrine` §5 (Valuation Philosophy) output shape.

    Sprint 1: always `NOT_EVALUATED` (no evaluator existed).

    Sprint 3: the evaluator is real. `execution_price_history` is
    always populated with a genuine, deterministic finding — even "no
    execution-price history recorded" is a real, honest finding, not a
    failure to evaluate — so `state` is always `EVALUATED`, the same
    top-level semantics `BusinessEvaluationResult` already established:
    a stage can be `EVALUATED` while one of its dimensions honestly
    reports `INSUFFICIENT_INPUT`. `substantive_valuation` (Doctrine §5's
    actual valuation content) is carried separately and is always
    `INSUFFICIENT_INPUT` (see `ValuationFinding`).

    Still contains no fair value, price target, buying range, upside,
    downside, valuation score, multiple, or DCF value — by explicit
    Sprint 3 lock. `state`/`reason` retain Sprint 1's original shape
    unchanged (additive expansion only, mirroring how Sprint 2 expanded
    `BusinessEvaluationResult`).
    """

    state: EvaluationState
    reason: StageNotImplementedReason | None = None
    substantive_valuation: ValuationFinding | None = None
    execution_price_history: ExecutionPriceHistoryFinding | None = None

    def __post_init__(self) -> None:
        _require_reason_when_not_evaluated(self.state, self.reason)
        if self.state is EvaluationState.EVALUATED and (
            self.substantive_valuation is None or self.execution_price_history is None
        ):
            raise DecisionEngineContractError(
                "An EVALUATED ValuationResult must carry both "
                "substantive_valuation and execution_price_history findings."
            )


class HoldingLinkage(str, Enum):
    """Whether a portfolio holding is linked to this Case at all."""

    ABSENT = "absent"
    PRESENT = "present"


@dataclass(frozen=True)
class HoldingContextFinding:
    """Real, deterministic structural facts about the single holding
    linked to this Case (if any) and this Case's trade history — built
    entirely from `DecisionEngineInput.portfolio_holding` and
    `DecisionEngineInput.trade_log`.

    No field here is interpreted. `weight_percent` and `value_absolute`
    are reported verbatim; this type never labels a weight "high,"
    "low," "overweight," or "concentrated," and never infers risk,
    diversification, suitability, or portfolio quality from them. That
    is precisely the boundary between this finding (Sprint 4) and the
    seven DE-003 factors (`PortfolioFinding`, below), which require
    portfolio-wide data this single-holding shape cannot honestly
    provide.
    """

    linkage: HoldingLinkage
    ticker: str | None = None
    weight_percent: float | None = None
    value_absolute: float | None = None
    reconciliation_status: ReconciliationState | None = None
    trade_count: int = 0
    transaction_types: tuple[str, ...] = ()
    earliest_executed_at: datetime | None = None
    latest_executed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.linkage is HoldingLinkage.ABSENT and (
            self.ticker is not None
            or self.weight_percent is not None
            or self.value_absolute is not None
            or self.reconciliation_status is not None
        ):
            raise DecisionEngineContractError(
                "HoldingContextFinding: ABSENT linkage must not carry any "
                "holding field."
            )
        if self.linkage is HoldingLinkage.PRESENT and (
            self.ticker is None or self.weight_percent is None
        ):
            raise DecisionEngineContractError(
                "HoldingContextFinding: PRESENT linkage must carry at least "
                "ticker and weight_percent."
            )
        if self.trade_count == 0 and (
            self.earliest_executed_at is not None or self.latest_executed_at is not None
        ):
            raise DecisionEngineContractError(
                "HoldingContextFinding: zero trade_count must not carry "
                "execution timestamps."
            )
        if self.trade_count > 0 and (
            self.earliest_executed_at is None or self.latest_executed_at is None
        ):
            raise DecisionEngineContractError(
                "HoldingContextFinding: nonzero trade_count must carry both "
                "execution timestamp bounds."
            )


class PortfolioDataNotAvailableReason(str, Enum):
    """Why the seven `DE-003` doctrine factors could not be assessed."""

    NO_PORTFOLIO_WIDE_DATA_IN_INPUT = "no_portfolio_wide_data_in_input"


class PortfolioDoctrineFactor(str, Enum):
    """`DE-003` §3's seven factors — every one of them portfolio-wide or
    cross-Case by its own doctrine definition (allocation and
    concentration are portfolio totals; diversification and correlation
    compare against sibling holdings; opportunity cost compares against
    portfolio-wide alternatives; existing thesis and previous decisions
    require Decision Memory's cross-Case history, `DE-005`)."""

    ALLOCATION = "allocation"
    CONCENTRATION = "concentration"
    DIVERSIFICATION = "diversification"
    CORRELATION = "correlation"
    OPPORTUNITY_COST = "opportunity_cost"
    EXISTING_THESIS = "existing_thesis"
    PREVIOUS_DECISIONS = "previous_decisions"


@dataclass(frozen=True)
class PortfolioFinding:
    """`DE-003`'s seven substantive factors, together.

    Always `EvaluationState.INSUFFICIENT_INPUT` this sprint, by explicit
    Sprint 4 lock: `DecisionEngineInput.portfolio_holding` is a single
    optional holding, not a collection — there is no sibling-holdings,
    sector/country/market-cap, correlation, or cross-Case data on the
    contract at all, so none of the seven factors can be honestly
    computed. Synthesizing a one-holding "portfolio" to force a
    computation is explicitly forbidden — that would fabricate a
    portfolio-wide judgment from single-holding data. Structurally
    guarantees this: `__post_init__` forbids constructing this type with
    any state other than `INSUFFICIENT_INPUT`, and `factors` must always
    name all seven `PortfolioDoctrineFactor` members — never a partial
    list — so no factor can be silently omitted from the "not yet
    assessable" disclosure.
    """

    state: EvaluationState
    reason: PortfolioDataNotAvailableReason
    factors: tuple[PortfolioDoctrineFactor, ...]

    def __post_init__(self) -> None:
        if self.state is not EvaluationState.INSUFFICIENT_INPUT:
            raise DecisionEngineContractError(
                "PortfolioFinding.state must be INSUFFICIENT_INPUT this "
                "sprint; DecisionEngineInput carries no portfolio-wide data "
                "to assess the seven DE-003 factors from."
            )
        if set(self.factors) != set(PortfolioDoctrineFactor):
            raise DecisionEngineContractError(
                "PortfolioFinding.factors must name all seven "
                "PortfolioDoctrineFactor members, never a partial list."
            )


@dataclass(frozen=True)
class PortfolioIntelligenceResult:
    """`DE-003` (Portfolio Intelligence) output shape.

    Sprint 1: always `NOT_EVALUATED` (no evaluator existed).

    Sprint 4: the evaluator is real. `holding_context` is always
    populated with a genuine, deterministic finding — even "no holding
    linked" is a real, honest finding, not a failure to evaluate — so
    `state` is always `EVALUATED`, the same top-level semantics
    `BusinessEvaluationResult` and `ValuationResult` already established:
    a stage can be `EVALUATED` while one of its dimensions honestly
    reports `INSUFFICIENT_INPUT`. `portfolio_factors` (all seven DE-003
    factors) is carried separately and is always `INSUFFICIENT_INPUT`
    (see `PortfolioFinding`).

    Still contains no concentration, diversification, correlation,
    suitability, or portfolio-fit score of any kind — by explicit
    Sprint 4 lock. `state`/`reason` retain Sprint 1's original shape
    unchanged (additive expansion only, mirroring Sprint 2 and 3).
    """

    state: EvaluationState
    reason: StageNotImplementedReason | None = None
    holding_context: HoldingContextFinding | None = None
    portfolio_factors: PortfolioFinding | None = None

    def __post_init__(self) -> None:
        _require_reason_when_not_evaluated(self.state, self.reason)
        if self.state is EvaluationState.EVALUATED and (
            self.holding_context is None or self.portfolio_factors is None
        ):
            raise DecisionEngineContractError(
                "An EVALUATED PortfolioIntelligenceResult must carry both "
                "holding_context and portfolio_factors findings."
            )


class ReasoningBlockedBy(str, Enum):
    """Which prior stage(s) prevented Reasoning from running, per
    `DE-002` §4's own dependency: Reasoning cannot proceed while
    Business Evaluation, Valuation, or Portfolio Intelligence is
    unevaluated.

    `REASONING_EVALUATOR_NOT_IMPLEMENTED` (Sprint 4): once all three
    upstream stages are `EVALUATED` (true for every input, from Sprint 4
    onward), Reasoning is no longer blocked by any of them — but its own
    evaluator still does not exist. This member names that honestly,
    the same way `StageNotImplementedReason.EVALUATOR_NOT_IMPLEMENTED`
    already does for the other placeholder stages, so `ReasoningResult`
    is never constructed as `NOT_EVALUATED` with an empty, unexplained
    `blocked_by`."""

    BUSINESS_EVALUATION_NOT_EVALUATED = "business_evaluation_not_evaluated"
    VALUATION_NOT_EVALUATED = "valuation_not_evaluated"
    PORTFOLIO_INTELLIGENCE_NOT_EVALUATED = "portfolio_intelligence_not_evaluated"
    REASONING_EVALUATOR_NOT_IMPLEMENTED = "reasoning_evaluator_not_implemented"


@dataclass(frozen=True)
class ReasoningSummary:
    """`DE-002` §2.1 Current Situation, under the Recommendation Withheld
    structural exception (`DE-002` §4: Current Situation "MAY still be
    stated"). A pure structural echo of each upstream stage's own
    top-level state and coverage/linkage facts — copied, never inferred,
    generalized, or classified. Answers only "where do things stand,"
    per `DE-002` §2.1's own prohibition on any forward-looking claim.
    """

    business_evaluation_state: EvaluationState
    valuation_state: EvaluationState
    portfolio_intelligence_state: EvaluationState
    evidence_coverage: EvidenceCoverageLevel
    execution_price_history_coverage: ExecutionPriceHistoryCoverage
    holding_linkage: HoldingLinkage


@dataclass(frozen=True)
class SupportingEvidenceSummary:
    """`DE-002` §2.2 Evidence, under Recommendation Withheld. Every
    `ObservationEvidenceClassification` from Business Evaluation with
    `supporting_evidence_count > 0` — copied verbatim, never
    reinterpreted, rescored, or newly classified. A `CONTRADICTED`
    observation (nonzero on both sides) legitimately appears here and in
    `ContradictionSummary` at once — both counts are simultaneously
    true."""

    observation_classifications: tuple[ObservationEvidenceClassification, ...]


@dataclass(frozen=True)
class ContradictionSummary:
    """`DE-002` §2.3 Counter-Evidence, under Recommendation Withheld.
    Every `ObservationEvidenceClassification` from Business Evaluation
    with `challenging_evidence_count > 0` — copied verbatim, same
    non-reinterpretation guarantee as `SupportingEvidenceSummary`."""

    observation_classifications: tuple[ObservationEvidenceClassification, ...]


@dataclass(frozen=True)
class KnownUnknownSummary:
    """`DE-002` §4's "why insufficient" content, assembled from every
    explicit gap and `INSUFFICIENT_INPUT` finding already produced
    upstream — nothing here is inferred or newly discovered by
    Reasoning. `durability_gap`/`valuation_gap` are typed `| None` (not
    unconditionally required) so a future sprint in which either
    dimension becomes genuinely assessable does not require a contract
    change here — this sprint, both are always populated, since both
    are always `INSUFFICIENT_INPUT` (see `DurabilityFinding`,
    `ValuationFinding`).
    """

    evidence_gaps: tuple[EvidenceGap, ...]
    durability_gap: DurabilityFinding | None
    valuation_gap: ValuationFinding | None
    portfolio_factor_gaps: tuple[PortfolioDoctrineFactor, ...]


@dataclass(frozen=True)
class PortfolioContextSummary:
    """`DE-002` §2.4 Portfolio Context, under Recommendation Withheld
    ("MAY still be stated"). Wraps Portfolio Intelligence's own
    `HoldingContextFinding` verbatim — weights, trade history, and
    reconciliation state are never recomputed here."""

    holding_context: HoldingContextFinding


class OpenQuestionKind(str, Enum):
    """A deterministic, template-free question directly implied by one
    specific upstream finding or gap — never freely generated prose.
    Each member corresponds 1:1 to a structured fact already produced
    upstream; a future presentation layer maps `kind` to localized text
    (e.g. `VALUATION_THESIS_NOT_DOCUMENTED` -> "No valuation thesis has
    been documented."). This module itself never stores that prose,
    matching this codebase's own separation of domain output from
    presentation, already established for `StageNotImplementedReason`
    and every other reason enum in this file.
    """

    NO_EVIDENCE_RECORDED_FOR_CASE = "no_evidence_recorded_for_case"
    OBSERVATION_WITHOUT_EVIDENCE = "observation_without_evidence"
    DECISION_WITHOUT_LINKED_OBSERVATION = "decision_without_linked_observation"
    BUSINESS_DURABILITY_NOT_ASSESSABLE = "business_durability_not_assessable"
    VALUATION_THESIS_NOT_DOCUMENTED = "valuation_thesis_not_documented"
    PORTFOLIO_FACTOR_NOT_ASSESSABLE = "portfolio_factor_not_assessable"


@dataclass(frozen=True)
class OpenQuestion:
    """One machine-readable open question. `reference` is
    `str(ObservationId)`, `str(DecisionId)`, or a `PortfolioDoctrineFactor`
    value, depending on `kind`; `None` for case-wide or dimension-wide
    kinds that name no single reference."""

    kind: OpenQuestionKind
    reference: str | None = None


@dataclass(frozen=True)
class ReasoningFinding:
    """`DE-002`'s Reasoning Structure, assembled under the Recommendation
    Withheld structural exception (`DE-002` §4). Direction and Conviction
    are permanently absent this sprint — no field for either exists on
    this type, the same structural guarantee `RecommendationWithheld`
    itself already makes. `what_would_change` is always `()`: per
    explicit Sprint 5 lock, no upstream stage exposes a distinct
    change-trigger concept, and none is derived or synthesized from
    `known_unknowns`/`open_questions` here — it remains empty until a
    prior stage genuinely provides one.
    """

    current_situation: ReasoningSummary
    supporting_evidence: SupportingEvidenceSummary
    contradicting_evidence: ContradictionSummary
    known_unknowns: KnownUnknownSummary
    portfolio_context: PortfolioContextSummary
    open_questions: tuple[OpenQuestion, ...]
    what_would_change: tuple[OpenQuestion, ...] = ()

    def __post_init__(self) -> None:
        if self.what_would_change:
            raise DecisionEngineContractError(
                "ReasoningFinding.what_would_change must be empty this "
                "sprint; no upstream stage exposes a change-trigger "
                "concept to assemble it from."
            )


@dataclass(frozen=True)
class ReasoningResult:
    """`DE-002`'s seven-part Reasoning Structure output shape.

    Sprint 1: always `NOT_EVALUATED` (no evaluator existed).

    Sprint 5: the evaluator is real. Reasoning is an assembly layer, not
    a second evaluator — it consumes only `BusinessEvaluationResult`,
    `ValuationResult`, and `PortfolioIntelligenceResult` (never
    `DecisionEngineInput`, never raw Observation/Evidence/Decision/
    Outcome entities directly). `finding` is always populated with a
    genuine, deterministic assembly of what those three stages already
    produced — even an audit trail that is mostly "not yet assessable"
    is a real, honest result, not a failure to evaluate — so `state` is
    always `EVALUATED`, the same top-level semantics every prior stage
    already established. `blocked_by` becomes permanently empty from
    this sprint onward; the type keeps the field, and keeps enforcing
    it for the `NOT_EVALUATED` branch, entirely for contract-shape
    stability with Sprints 1-4 rather than because that branch is still
    reachable.

    No `direction` or `conviction` field exists anywhere in this type
    or in `ReasoningFinding` — structurally guaranteed, mirroring
    `RecommendationWithheld`'s own guarantee.
    """

    state: EvaluationState
    blocked_by: tuple[ReasoningBlockedBy, ...] = ()
    finding: ReasoningFinding | None = None

    def __post_init__(self) -> None:
        if self.state is EvaluationState.NOT_EVALUATED and not self.blocked_by:
            raise DecisionEngineContractError(
                "A NOT_EVALUATED ReasoningResult must name at least one "
                "blocking prior stage."
            )
        if self.state is EvaluationState.EVALUATED and self.finding is None:
            raise DecisionEngineContractError(
                "An EVALUATED ReasoningResult must carry a finding."
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

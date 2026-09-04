"""Recommendation Gate (ATLAS-020, Phase 10; "Recommendation Backend Step
3" wiring) and the Recommendation domain model (DE-007, "Implementation
Step 1").

Wraps `atlas.decision_engine.stages.recommendation.determine_recommendation`
-- reused verbatim, never reimplemented, still the sole producer of a
`RecommendationWithheld` instance -- and adds two things ATLAS-020/this
sprint introduced: the `conviction_gate_met` fact (ATLAS-020's five-level
Conviction threshold check, unchanged), and, new this sprint, an actual
attempt to select a Direction and construct a
`ComputedDirectionalRecommendation` from it.

**`ComputedDirectionalRecommendation` can now be constructed by real
code.** The two capability gaps this module's docstring previously named
are both closed:

1. **Direction selector**: `atlas.analysis_engine.direction_selector
   .select_direction` (`docs/atlas_decision_engine/DE-008-Direction-Selection.md`,
   "Recommendation Backend Step 3"; `DE-016` "Recommendation Integration
   Design"/implementation sprint) now decides *which* of `DE-001` §2's six
   directions -- Hold/Trim/No Action/Buy/Add, or `None` for
   RecommendationWithheld -- a given analysis supports. BUY and ADD are
   reachable now that `DE-015`'s `ValuationSupport` supplies the
   previously-missing Valuation Support for Capital Deployment
   prerequisite (`select_direction` reads only its public `.status`,
   `DE-015` §18); EXIT remains currently unreachable -- pre-commit review
   found that the only candidate signal for its "thesis dependency
   failed" trigger (ordinary Counter-Evidence) is not doctrinally
   sufficient (`DE-004` §3 treats it as compatible with a continuing
   direction at Medium conviction, not as grounds for a forced exit).
   See that module's own docstring for the full reasoning on all three.
2. **Recommendation-specific Conviction, now consumed**:
   `recommendation_conviction.calculate_recommendation_conviction` is
   called below whenever a Direction is selected, and its
   `RecommendationConvictionLevel` populates the constructed
   `ComputedDirectionalRecommendation.conviction_level` -- the two
   Conviction scales stay exactly as independently computed as DE-007
   §11 requires; `evaluate_recommendation_gate`'s own `conviction`
   parameter (the five-level `ConvictionAssessment`) is untouched and
   still only feeds `conviction_gate_met`.

The gate, in full:

    select_direction(...) returns a real RecommendationDirection
    AND calculate_recommendation_conviction(...) returns a real assessment
    -> ComputedDirectionalRecommendation constructed

    otherwise (select_direction returns None, i.e. any of DE-008 §4's
    hard-gate conditions fail, or DE-008 itself requires
    RecommendationWithheld for this evidence pattern)
    -> RecommendationWithheld, via determine_recommendation, unchanged

`select_direction` and `calculate_recommendation_conviction` share the
identical existence-floor check (the same four `EvaluationState` fields
plus `EvidenceCoverageLevel`) for the identical reason (`DE-008` §4), so
in practice the two either both succeed or both return the "nothing to
report" case together -- this module still checks both explicitly rather
than assuming that equivalence, so a future divergence between the two
modules would surface as `RecommendationWithheld`, never as a
partially-populated `ComputedDirectionalRecommendation`.

`conviction_gate_met` (the five-level, ATLAS-020 field) is unaffected by
any of this -- it remains a separate fact computed from the `conviction`
parameter alone, exactly as before.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_contracts import (
    BusinessAnalysisResult,
    BusinessCategory,
    BusinessCategoryStatus,
)
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.reasoning import (
    ConvictionReasoning,
    InvestmentReason,
    KeyUnknown,
    SignalContribution,
    build_conviction_reasoning,
    build_drivers,
    build_key_unknowns,
    build_signal_summary,
)
from atlas.analysis_engine.recommendation_conviction import (
    RecommendationConvictionLevel,
    calculate_recommendation_conviction,
)
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.analysis_engine.valuation.support import ValuationSupport, ValuationSupportStatus
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.outcome.entity import Outcome
from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    ContradictionSummary,
    DecisionEngineInput,
    EvaluationState,
    EvidenceCoverageLevel,
    HoldingLinkage,
    PortfolioContextSummary,
    PortfolioFinding,
    PortfolioIntelligenceResult,
    ReasoningResult,
    ReasoningSummary,
    RecommendationWithheld,
    RecommendationWithheldReason,
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
    "ChangeTriggerKind",
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


class ChangeTriggerKind(str, Enum):
    """Calibration Phase 2 (Investment Case Coherence Implementation),
    Phase 6 -- the closed, deterministic vocabulary for
    `RecommendationReasoning.what_would_change`. Each member names one
    condition that would most plausibly move *this* recommendation, not
    generic investing advice -- selected by `_derive_what_would_change`
    from the exact same categorical facts `evaluate_recommendation_gate`
    already reads to select the Direction itself (Growth/Capital
    Allocation status, Valuation Support, Valuation status, high-risk
    flag). No new analysis is performed to produce this: it is a
    presentation-level selection over already-computed conclusions,
    the same discipline `DecisionSupportLevel`/`StanceReasonCode`
    already established elsewhere in this codebase.

    `NO_CREDIBLE_TRIGGER_IDENTIFIED` is a real, disclosed member, never
    an empty tuple standing in for "not computed" -- Phase 6's own
    instruction: "If Atlas cannot identify a credible change condition,
    say so honestly."
    """

    # Reversal conditions -- a present weakness resolving. These were
    # the only kind this vocabulary had, which is why a case with no
    # weakness at all could produce nothing but the fallback.
    REDUCED_RISK = "reduced_risk"
    MORE_ATTRACTIVE_VALUATION = "more_attractive_valuation"
    IMPROVED_GROWTH_EVIDENCE = "improved_growth_evidence"
    IMPROVED_CAPITAL_ALLOCATION_EVIDENCE = "improved_capital_allocation_evidence"
    LOWER_VALUATION = "lower_valuation"

    #: Deterioration conditions -- a present *strength* breaking. For a
    #: HOLD backed by healthy signals the credible change is not that a
    #: weakness heals, it is that a strength fails; without these the
    #: only honest answer available was
    #: `NO_CREDIBLE_TRIGGER_IDENTIFIED`, which dominated 7 of 9 real
    #: cases and made the field useless for monitoring.
    #:
    #: Each names the inverse of a state `select_direction` already
    #: reads, so none introduces a new analytical fact.
    FINANCIAL_RISK_BECOMES_ELEVATED = "financial_risk_becomes_elevated"
    VALUATION_BECOMES_EXPENSIVE = "valuation_becomes_expensive"
    VALUATION_SUPPORT_LOST = "valuation_support_lost"
    GROWTH_DETERIORATES = "growth_deteriorates"
    CAPITAL_ALLOCATION_DETERIORATES = "capital_allocation_deteriorates"

    #: Emitted only when no dimension yields a condition at all -- now
    #: genuinely rare rather than the default answer.
    NO_CREDIBLE_TRIGGER_IDENTIFIED = "no_credible_trigger_identified"


def _derive_what_would_change(
    *,
    has_high_financial_or_valuation_risk: bool,
    valuation_support_status: ValuationSupportStatus,
    growth_status: BusinessCategoryStatus,
    capital_allocation_status: BusinessCategoryStatus,
    valuation_status: ValuationStatus,
    has_real_risk_evidence: bool = False,
) -> tuple[ChangeTriggerKind, ...]:
    """Every condition that would materially change this recommendation
    -- derived from exactly the facts `select_direction` already reads,
    never a second analysis.

    Two corrections to the original, both found by the 2026-09-04
    canonical reasoning benchmark:

    **Every applicable condition is emitted, not just the first.** The
    original returned on first match, so AZN -- which carries elevated
    risk *and* an expensive valuation -- reported only `REDUCED_RISK`
    and silently lost `LOWER_VALUATION`. A monitor cannot watch a
    condition it was never told about.

    **Deterioration conditions exist.** The original vocabulary
    contained only reversals, so a case whose signals are all healthy
    had no expressible answer and fell through to
    `NO_CREDIBLE_TRIGGER_IDENTIFIED` -- 7 of 9 real cases. For a HOLD
    the credible change is that a strength breaks, which is now
    representable per dimension.

    One dimension is deliberately silent: `INSUFFICIENT_INPUT`
    valuation support emits nothing. That is a data gap, not an
    investment condition, and `key_unknowns` already reports it as
    `ANALYSIS_INPUT_MISSING`. Emitting it here too would give one fact
    two owners.

    Order is the existing disclosed precedence -- risk, then valuation,
    then business quality -- so this list and the driver list tell the
    same story in the same order. Deterministic: no set iteration, no
    clock, identical inputs give an identical tuple.
    """
    triggers: list[ChangeTriggerKind] = []

    if has_high_financial_or_valuation_risk:
        triggers.append(ChangeTriggerKind.REDUCED_RISK)
    elif has_real_risk_evidence:
        # Only when risk was genuinely assessed. Absent evidence must
        # not masquerade as a reassuring "risk is currently fine".
        triggers.append(ChangeTriggerKind.FINANCIAL_RISK_BECOMES_ELEVATED)

    if valuation_status is ValuationStatus.EXPENSIVE:
        triggers.append(ChangeTriggerKind.LOWER_VALUATION)
    elif valuation_status in (ValuationStatus.FAIRLY_VALUED, ValuationStatus.UNDERVALUED):
        triggers.append(ChangeTriggerKind.VALUATION_BECOMES_EXPENSIVE)

    if valuation_support_status is ValuationSupportStatus.NOT_SUPPORTED:
        triggers.append(ChangeTriggerKind.MORE_ATTRACTIVE_VALUATION)
    elif valuation_support_status is ValuationSupportStatus.SUPPORTED:
        triggers.append(ChangeTriggerKind.VALUATION_SUPPORT_LOST)

    if growth_status is BusinessCategoryStatus.WEAK:
        triggers.append(ChangeTriggerKind.IMPROVED_GROWTH_EVIDENCE)
    elif growth_status is BusinessCategoryStatus.STRONG:
        triggers.append(ChangeTriggerKind.GROWTH_DETERIORATES)

    if capital_allocation_status is BusinessCategoryStatus.WEAK:
        triggers.append(ChangeTriggerKind.IMPROVED_CAPITAL_ALLOCATION_EVIDENCE)
    elif capital_allocation_status is BusinessCategoryStatus.STRONG:
        triggers.append(ChangeTriggerKind.CAPITAL_ALLOCATION_DETERIORATES)

    return tuple(triggers) or (ChangeTriggerKind.NO_CREDIBLE_TRIGGER_IDENTIFIED,)


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
    forbid populating it. Calibration Phase 2, Phase 6: populated by
    `_derive_what_would_change` at every real construction site below --
    a closed `ChangeTriggerKind`, never the free-text `OpenQuestion` type
    `ReasoningFinding.what_would_change` uses (that type names an
    evidence-linkage gap; this one names a genuine change condition,
    a different concept that deserves its own vocabulary).
    """

    current_situation: ReasoningSummary
    supporting_evidence: SupportingEvidenceSummary
    contradicting_evidence: ContradictionSummary
    portfolio_context: PortfolioContextSummary
    what_would_change: tuple[ChangeTriggerKind, ...] = ()

    #: Reasoning Domain Closure. Every field below is additive and
    #: defaults to empty, so the pre-existing construction sites (and
    #: every test fixture) keep working unchanged. They are populated
    #: only at this module's own single producer -- see
    #: `evaluate_recommendation_gate` -- because only there are the
    #: exact statuses `select_direction` read still in scope. A
    #: downstream layer that populated them would be reasoning from a
    #: different set of facts than the direction it explains.
    primary_drivers: tuple[InvestmentReason, ...] = ()
    counter_drivers: tuple[InvestmentReason, ...] = ()
    key_unknowns: tuple[KeyUnknown, ...] = ()
    signal_summary: tuple[SignalContribution, ...] = ()
    conviction_reasoning: ConvictionReasoning | None = None


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
    """`recommendation` is `RecommendationWithheld` whenever
    `atlas.analysis_engine.direction_selector.select_direction` returns
    `None`, and a real `ComputedDirectionalRecommendation` exactly when
    it returns a `RecommendationDirection` (see
    `evaluate_recommendation_gate`'s own docstring for the full gate).
    The field stays typed as the union it always was --
    `RecommendationWithheld | ComputedDirectionalRecommendation` -- no
    shape change was needed to go from "always the first branch" to
    "either branch, for real."

    This widening intentionally lives here, in `atlas.analysis_engine`,
    not on `atlas.decision_engine.contracts.DecisionEngineOutput` --
    `ComputedDirectionalRecommendation` depends on Conviction (this
    package's exclusive domain, per `__init__.py`'s own ownership
    statement), and `atlas.decision_engine` may never import
    `atlas.analysis_engine` (the one-way boundary
    `tests/test_architecture_boundaries.py
    ::test_analysis_engine_only_reads_core_and_decision_engine` already
    enforces in the other direction). `DecisionEngineOutput.recommendation`
    stays exactly `RecommendationWithheld`, untouched.

    `conviction_gate_met` remains ATLAS-020's own, separate fact: whether
    the five-level `ConvictionAssessment` alone would clear its
    threshold. It is computed from the `conviction` parameter only, and
    plays no role in whether `select_direction`/
    `calculate_recommendation_conviction` produce a directional
    result -- the two gates are independent facts, both reported."""

    recommendation: RecommendationWithheld | ComputedDirectionalRecommendation
    conviction_gate_met: bool
    conviction: ConvictionAssessment


_DIRECTION_STATEMENTS: dict[RecommendationDirection, str] = {
    RecommendationDirection.BUY: (
        "Current evidence -- the business, the position's absence, and the valuation-support "
        "standard -- together support initiating a position in this security."
    ),
    RecommendationDirection.ADD: (
        "Current evidence -- the business, the intact thesis, and the valuation-support "
        "standard -- together support increasing this position."
    ),
    RecommendationDirection.HOLD: (
        "Current evidence, actively reviewed, does not support a change to this position."
    ),
    RecommendationDirection.TRIM: (
        "Current evidence supports reducing, but not eliminating, this position."
    ),
    RecommendationDirection.NO_ACTION: (
        "Current evidence does not support initiating a position in this security."
    ),
}
"""One deterministic, evidence-only statement per reachable direction
(`DE-001` §3's "Why" element). BUY/ADD's own statements deliberately name
the full, multi-part standard ("together support") rather than crediting
Valuation Support alone -- `DE-015` §6's own disclosure requirement
("any presentation of a SUPPORTED conclusion SHALL disclose this
narrower meaning, never imply the broader one") applies with full force
the moment that status can produce a real BUY/ADD; neither statement
names a scenario, a return figure, Net-Cash, or any other private
proof-path content (`DE-015` §18). Deliberately keyed, not
`.get()`-defaulted -- EXIT is never looked up here because
`select_direction` never returns it; a `KeyError` on it would be a loud
signal that `RecommendationDirection.EXIT` leaked past
`direction_selector.py`, never a case to silently paper over."""


def _safe_holding_linkage(portfolio_intelligence: PortfolioIntelligenceResult) -> HoldingLinkage:
    """`holding_context` is only guaranteed non-`None` once
    `portfolio_intelligence.state is EVALUATED` (`PortfolioIntelligenceResult`'s
    own `__post_init__`). The default returned otherwise is inert: any
    time it would matter, `select_direction`'s own stage-1 hard gate has
    already returned `None` (RecommendationWithheld) before this value is
    used for anything."""
    if portfolio_intelligence.state is not EvaluationState.EVALUATED or portfolio_intelligence.holding_context is None:
        return HoldingLinkage.ABSENT
    return portfolio_intelligence.holding_context.linkage


def _safe_evidence_coverage(business_evaluation: BusinessEvaluationResult) -> EvidenceCoverageLevel:
    """Same inertness guarantee as `_safe_holding_linkage` -- see that
    function's own docstring."""
    if business_evaluation.state is not EvaluationState.EVALUATED or business_evaluation.evidence_quality is None:
        return EvidenceCoverageLevel.NOT_APPLICABLE
    return business_evaluation.evidence_quality.coverage


def _safe_has_contradicting_evidence(reasoning: ReasoningResult) -> bool:
    """Same inertness guarantee as `_safe_holding_linkage` -- see that
    function's own docstring."""
    if reasoning.state is not EvaluationState.EVALUATED or reasoning.finding is None:
        return False
    return bool(reasoning.finding.contradicting_evidence.observation_classifications)


def evaluate_recommendation_gate(
    engine_input: DecisionEngineInput,
    *,
    business_evaluation: BusinessEvaluationResult,
    valuation: ValuationResult,
    portfolio_intelligence: PortfolioIntelligenceResult,
    reasoning: ReasoningResult,
    conviction: ConvictionAssessment,
    business_analysis: BusinessAnalysisResult,
    valuation_engine: ValuationEngineResult,
    valuation_support: ValuationSupport,
    has_high_financial_or_valuation_risk: bool,
    has_open_questions: bool,
    generated_at: datetime,
    has_portfolio_dampening: bool = False,
    has_real_risk_evidence: bool = False,
) -> RecommendationGateResult:
    """Deterministic: identical inputs always produce an identical
    `RecommendationGateResult`.

    `business_analysis`/`valuation_engine` are the richer,
    `atlas.analysis_engine`-level results (`business.py`'s
    `BusinessAnalysisResult`, `valuation.pipeline`'s
    `ValuationEngineResult`) -- distinct from, and a superset of,
    `business_evaluation`/`valuation` (the plain `decision_engine`-level
    results this function already took). Both are required here because
    `direction_selector.select_direction` needs Growth/Capital Allocation
    status and `ValuationStatus`, neither of which the plain
    `decision_engine` results carry (Sprint 2/3 locks: those two types
    are permanently `INSUFFICIENT_INPUT` for their substantive content).

    `valuation_support` (`DE-015`'s `ValuationSupport`, real as of
    `DE-016`) is read for exactly one thing: its public `.status` field is
    forwarded to `select_direction`, which is now the only place BUY/ADD
    can be constructed. This function never reads `.reasoning` or `.gap`
    (`DE-015` §18) and never branches on `valuation_support` itself.

    `has_portfolio_dampening` defaults `False` -- `PortfolioFinding` is
    permanently `INSUFFICIENT_INPUT` (Sprint 4 lock), so no real
    call site can honestly supply `True` yet; see
    `direction_selector.py`'s own docstring.

    `has_real_risk_evidence` (Recommendation Evidence Sufficiency
    Alignment) defaults `False` for the same reason `has_portfolio
    _dampening` does -- an explicit opt-in signal, never inferred here.
    Forwarded to `select_direction`'s own Stage-1 gate unchanged; see
    that function's own docstring for what it does.

    First attempts to select a real Direction and a real
    Recommendation-specific Conviction; falls back to the existing
    `determine_recommendation`-produced `RecommendationWithheld`
    whenever either is unavailable -- see this function's own module
    docstring for the full gate and why the two are checked
    independently rather than assumed equivalent."""
    # Imported here, not at module level: `direction_selector` imports
    # `RecommendationDirection` from this module, so a top-level import
    # here would be a circular import. This function-local import is the
    # standard, minimal-footprint break -- both modules are fully loaded
    # by the time this function is ever called.
    from atlas.analysis_engine.direction_selector import has_company_fundamentals_evidence, select_direction

    conviction_gate_met = _CONVICTION_ORDER.index(conviction.level) >= _CONVICTION_ORDER.index(
        RECOMMENDATION_GATE_MINIMUM_CONVICTION
    )

    growth_finding = next(f for f in business_analysis.findings if f.kind is BusinessCategory.GROWTH)
    capital_allocation_finding = next(
        f for f in business_analysis.findings if f.kind is BusinessCategory.CAPITAL_ALLOCATION
    )
    fcf_yield_finding = next(
        f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
    )

    evidence_coverage = _safe_evidence_coverage(business_evaluation)
    has_contradicting_evidence = _safe_has_contradicting_evidence(reasoning)

    fundamentals_evidence_present = has_company_fundamentals_evidence(
        growth_status=growth_finding.status,
        capital_allocation_status=capital_allocation_finding.status,
        valuation_status=fcf_yield_finding.status,
        has_real_risk_evidence=has_real_risk_evidence,
    )

    recommendation_conviction = calculate_recommendation_conviction(
        business_state=business_evaluation.state,
        valuation_state=valuation.state,
        portfolio_intelligence_state=portfolio_intelligence.state,
        reasoning_state=reasoning.state,
        evidence_coverage=evidence_coverage,
        has_contradicting_evidence=has_contradicting_evidence,
        has_open_questions=has_open_questions,
        has_company_fundamentals_evidence=fundamentals_evidence_present,
    )

    direction = select_direction(
        holding_linkage=_safe_holding_linkage(portfolio_intelligence),
        business_evaluation_state=business_evaluation.state,
        valuation_state=valuation.state,
        portfolio_intelligence_state=portfolio_intelligence.state,
        reasoning_state=reasoning.state,
        evidence_coverage=evidence_coverage,
        growth_status=growth_finding.status,
        capital_allocation_status=capital_allocation_finding.status,
        valuation_status=fcf_yield_finding.status,
        valuation_support_status=valuation_support.status,
        has_portfolio_dampening=has_portfolio_dampening,
        has_high_financial_or_valuation_risk=has_high_financial_or_valuation_risk,
        has_real_risk_evidence=has_real_risk_evidence,
    )

    # Reasoning Domain Closure: computed once, from exactly the
    # statuses `select_direction` was handed above. Cheap, pure, and
    # deliberately positioned after the direction call so it can never
    # be mistaken for an input to it.
    _signal_summary = build_signal_summary(
        # Projected from the finding that owns them; never recomputed.
        growth_revenue_cagr=growth_finding.revenue_cagr,
        growth_free_cash_flow_cagr=growth_finding.free_cash_flow_cagr,
        valuation_current_yield=fcf_yield_finding.current_yield,
        valuation_historical_yields=fcf_yield_finding.historical_yields,
        growth_status=growth_finding.status,
        capital_allocation_status=capital_allocation_finding.status,
        valuation_status=fcf_yield_finding.status,
        valuation_support_status=valuation_support.status,
        has_high_financial_or_valuation_risk=has_high_financial_or_valuation_risk,
        has_real_risk_evidence=has_real_risk_evidence,
    )
    _signal_drivers = build_drivers(
        growth_status=growth_finding.status,
        capital_allocation_status=capital_allocation_finding.status,
        valuation_status=fcf_yield_finding.status,
        valuation_support_status=valuation_support.status,
        has_high_financial_or_valuation_risk=has_high_financial_or_valuation_risk,
        has_real_risk_evidence=has_real_risk_evidence,
    )

    recommendation: RecommendationWithheld | ComputedDirectionalRecommendation
    if direction is not None and recommendation_conviction is not None:
        assert reasoning.finding is not None  # guaranteed: select_direction's own hard gate requires reasoning EVALUATED for `direction` to be non-None
        assert portfolio_intelligence.portfolio_factors is not None  # same guarantee, for portfolio_intelligence
        recommendation = ComputedDirectionalRecommendation(
            recommendation_instance_id=f"{engine_input.case_id}:{generated_at.isoformat()}",
            case_id=engine_input.case_id,
            generated_at=generated_at,
            direction=direction,
            direction_statement=_DIRECTION_STATEMENTS[direction],
            conviction_level=recommendation_conviction.level,
            conviction_reason=", ".join(reason.value for reason in recommendation_conviction.reasons),
            reasoning=RecommendationReasoning(
                current_situation=reasoning.finding.current_situation,
                supporting_evidence=reasoning.finding.supporting_evidence,
                contradicting_evidence=reasoning.finding.contradicting_evidence,
                portfolio_context=reasoning.finding.portfolio_context,
                what_would_change=_derive_what_would_change(
                    has_real_risk_evidence=has_real_risk_evidence,
                    has_high_financial_or_valuation_risk=has_high_financial_or_valuation_risk,
                    valuation_support_status=valuation_support.status,
                    growth_status=growth_finding.status,
                    capital_allocation_status=capital_allocation_finding.status,
                    valuation_status=fcf_yield_finding.status,
                ),
                # Reasoning Domain Closure -- built here and nowhere
                # else, from the identical statuses passed to
                # `select_direction` immediately above. Restatement
                # only: no new analysis, no new engine, and nothing
                # here can alter the direction already chosen.
                primary_drivers=_signal_drivers[0],
                counter_drivers=_signal_drivers[1],
                signal_summary=_signal_summary,
                key_unknowns=build_key_unknowns(
                    _signal_summary,
                    # DE-015 §18 as amended: `gap` crosses for
                    # explanatory projection only. It reaches no
                    # recommendation-semantic call above.
                    valuation_support_gap=(
                        valuation_support.gap.value if valuation_support.gap is not None else None
                    ),
                ),
                conviction_reasoning=build_conviction_reasoning(recommendation_conviction),
            ),
            portfolio_factors=portfolio_intelligence.portfolio_factors,
        )
    else:
        recommendation = determine_recommendation(
            engine_input,
            business_evaluation=business_evaluation,
            valuation=valuation,
            portfolio_intelligence=portfolio_intelligence,
            reasoning=reasoning,
            generated_at=generated_at,
        )
        if not recommendation.missing_evaluations:
            # `determine_recommendation` always stamps `ENGINE_NOT
            # _IMPLEMENTED` (accurate at its own, lower `decision_engine`
            # call site, which genuinely has no Direction selector).
            # Reached from here, that label is stale: `select_direction`
            # is real and ran (Recommendation Evidence Sufficiency
            # Alignment) -- an empty `missing_evaluations` means every
            # prerequisite stage was EVALUATED, so a withheld outcome at
            # this call site is always "ran the real evaluators, still
            # not enough evidence" (`RecommendationWithheldReason`'s own
            # docstring), never "the engine isn't built."
            recommendation = replace(recommendation, reason=RecommendationWithheldReason.EVIDENCE_INSUFFICIENT)

    return RecommendationGateResult(
        recommendation=recommendation, conviction_gate_met=conviction_gate_met, conviction=conviction
    )

"""Canonical Recommendation Reasoning (Reasoning Domain Closure).

The analytical rationale behind a recommendation, preserved as a domain
fact rather than reconstructed downstream.

**Produced exactly once**, inside `recommendation.evaluate_recommendation
_gate`, from the same statuses `select_direction` reads to pick the
Direction. That co-location is the whole point: a second producer
reading a different set would eventually disagree with the direction it
claims to explain, which is exactly what happened before this module
existed -- `alpha.investment_decision.engine` derived a "change trigger"
from readiness blockers because the real one never reached it.

**The governing separation.** An `InvestmentReason` describes the
company ("valuation is expensive"). A `ProcessStateReason` describes
Atlas ("evidence coverage is partial"). Both are true and both matter,
but only the first explains a recommendation. The two types share no
member and no supertype, so a process state cannot be constructed where
an investment driver is required -- the Calibration Phase 9 defect,
where `monitoring_current` and `decision_support_reached` were the
recorded reasons for a REDUCE, becomes unrepresentable rather than
merely discouraged.

This module computes no new analysis. Every value it carries is a
restatement of an already-computed status, plus the polarity that
status already implies.

**Forward context is the one exception to "from the direction's own
statuses", and it is kept out of every directional path.** A
`ForwardReasoningContext` restates verified forward evidence --
guidance revisions and executed customer commitments -- that Atlas holds
but that does not decide the direction: "what else a user should know",
never "why the direction should change". It has no polarity, no score
and no driver slot; it is built by `atlas.analysis_engine.forward_context`
(the only analysis module allowed to read forward evidence) and placed
into the reasoning after the direction is chosen. Reaffirmed guidance is
"unchanged", not "supportive"; contracted volume travels with the
economics it does not establish.

**The risk basis is carried the same way.** A `RiskDriverBasis` discloses
what the `financial_risk` driver rests on -- which risk categories are
`HIGH`, and Financial Risk v2's own retained basis (the latest aligned
debt-burden observation, its trend context, the policy bands, or why no
level was reached). It explains the driver; it is not a driver, adds
none, and is placed into the reasoning after the direction is chosen.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.recommendation_conviction import (
    RecommendationConvictionAssessment,
    RecommendationConvictionLevel,
    RecommendationConvictionReasonCode,
)
from atlas.analysis_engine.risk.contracts import (
    FinancialRiskCondition,
    FinancialRiskExclusionReason,
    FinancialRiskMeasure,
    RiskDataGapKind,
    RiskStatus,
)
from atlas.analysis_engine.risk.models import (
    DebtBurdenBands,
    DebtBurdenObservation,
    FinancialRiskBasis,
    FinancialRiskExclusion,
)
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupportStatus

__all__ = [
    "CanonicalEngine",
    "ContractedVolumeContext",
    "ConvictionReasoning",
    "ELEVATING_RISK_CATEGORIES",
    "RISK_BASIS_VERSION",
    "RiskDriverBasis",
    "ForwardGuidanceContext",
    "ForwardGuidanceSubject",
    "ForwardReasoningContext",
    "GuidanceRevisionKind",
    "UnestablishedEconomics",
    "InvestmentReason",
    "InvestmentReasonKind",
    "KeyUnknown",
    "KeyUnknownKind",
    "ProcessStateReason",
    "ProcessStateReasonKind",
    "ReasoningPolarity",
    "SignalContribution",
    "SignalState",
    "build_conviction_reasoning",
    "build_key_unknowns",
    "build_drivers",
    "build_signal_summary",
    "deserialize_reasoning",
    "serialize_reasoning",
    "LEGACY_RESULT_WITHOUT_REASONING",
    "REASONING_SCHEMA_VERSION",
    "StoredReasoning",
]


class CanonicalEngine(str, Enum):
    """Every analytical engine the recommendation architecture names --
    including the three deliberately outside the direction contract, so
    their exclusion is a recorded fact rather than a silence."""

    GROWTH = "growth"
    CAPITAL_ALLOCATION = "capital_allocation"
    VALUATION = "valuation"
    VALUATION_SUPPORT = "valuation_support"
    FINANCIAL_RISK = "financial_risk"
    BUSINESS_QUALITY = "business_quality"
    INDUSTRY_CONTEXT = "industry_context"
    EXPECTED_RETURN = "expected_return"


#: Precedence for ordering drivers. Not invented here: it is the same
#: order `_derive_what_would_change` already documents and applies --
#: "a real risk concern outranks a valuation concern, which outranks a
#: business-quality concern". Reusing it keeps the driver list and the
#: change trigger telling the same story in the same order.
_ENGINE_PRECEDENCE: tuple[CanonicalEngine, ...] = (
    CanonicalEngine.FINANCIAL_RISK,
    CanonicalEngine.VALUATION,
    CanonicalEngine.VALUATION_SUPPORT,
    CanonicalEngine.GROWTH,
    CanonicalEngine.CAPITAL_ALLOCATION,
)


class SignalState(str, Enum):
    """One engine's state for this recommendation. `NOT_IN_DIRECTION
    _CONTRACT` is deliberately distinct from `NOT_EVALUATED`: Business
    Quality is computed and real, it simply does not participate in
    direction selection yet. Collapsing the two would reproduce exactly
    the ambiguity the Phase 9 benchmark could not see through."""

    CONCLUSIVE = "conclusive"
    INCONCLUSIVE = "inconclusive"
    NOT_EVALUATED = "not_evaluated"
    NOT_IN_DIRECTION_CONTRACT = "not_in_direction_contract"


class ReasoningPolarity(str, Enum):
    SUPPORTIVE = "supportive"
    ADVERSE = "adverse"
    NEUTRAL = "neutral"


class InvestmentReasonKind(str, Enum):
    """Closed vocabulary describing the COMPANY. Every member restates
    one already-computed analytical status -- never a new judgement."""

    GROWTH_STRONG = "growth_strong"
    GROWTH_MODERATE = "growth_moderate"
    GROWTH_WEAK = "growth_weak"
    CAPITAL_ALLOCATION_STRONG = "capital_allocation_strong"
    CAPITAL_ALLOCATION_MODERATE = "capital_allocation_moderate"
    CAPITAL_ALLOCATION_WEAK = "capital_allocation_weak"
    VALUATION_UNDERVALUED = "valuation_undervalued"
    VALUATION_FAIRLY_VALUED = "valuation_fairly_valued"
    VALUATION_EXPENSIVE = "valuation_expensive"
    VALUATION_SUPPORTED = "valuation_supported"
    VALUATION_NOT_SUPPORTED = "valuation_not_supported"
    FINANCIAL_RISK_ELEVATED = "financial_risk_elevated"
    FINANCIAL_RISK_NOT_ELEVATED = "financial_risk_not_elevated"


class ProcessStateReasonKind(str, Enum):
    """Closed vocabulary describing ATLAS, never the company. Disjoint
    from `InvestmentReasonKind` by construction -- see the module
    docstring for why that disjointness is the point."""

    EVIDENCE_COVERAGE_PARTIAL = "evidence_coverage_partial"
    EVIDENCE_COVERAGE_FULL = "evidence_coverage_full"
    CONTRADICTING_EVIDENCE_PRESENT = "contradicting_evidence_present"
    NO_CONTRADICTING_EVIDENCE = "no_contradicting_evidence"
    OPEN_QUESTIONS_REMAIN = "open_questions_remain"
    NO_OPEN_QUESTIONS = "no_open_questions"
    COMPANY_FUNDAMENTALS_EVIDENCE_ONLY = "company_fundamentals_evidence_only"


class KeyUnknownKind(str, Enum):
    """Why something the recommendation would have used is absent.
    `NOT_CONNECTED_TO_DIRECTION` is not a gap in Atlas's knowledge -- it
    is a deliberate architectural state, recorded so a reader can tell
    the two apart."""

    ANALYSIS_INPUT_MISSING = "analysis_input_missing"
    NOT_CONNECTED_TO_DIRECTION = "not_connected_to_direction"
    #: The analysis ran to completion on sufficient data and reached a
    #: genuinely mixed result. Nothing is missing.
    #:
    #: `ValuationSupportStatus.INSUFFICIENT_INPUT` deliberately collapses
    #: causes that are not alike (`DE-015` §6/§7), and describing all of
    #: them as a missing input was false for two of them. A
    #: `SCENARIO_ENVELOPE_INCONCLUSIVE` gap means a real,
    #: historically-grounded forward-return range was built and
    #: straddles zero; `CONFLICTING_VALUATION_PROOFS` means two
    #: independent real proofs disagree.
    #:
    #: Never to be read as negative, neutral, or failed -- only as
    #: unresolved. Explanatory only, per `DE-015` §18 as amended.
    ANALYSIS_COMPLETE_UNRESOLVED = "analysis_complete_unresolved"


@dataclass(frozen=True)
class InvestmentReason:
    """One company-describing reason, traceable to the engine whose
    already-computed status produced it. `source_status` is that status
    verbatim, so a reader can audit the restatement without re-running
    anything."""

    kind: InvestmentReasonKind
    polarity: ReasoningPolarity
    engine: CanonicalEngine
    source_status: str


@dataclass(frozen=True)
class ProcessStateReason:
    kind: ProcessStateReasonKind


@dataclass(frozen=True)
class SignalContribution:
    engine: CanonicalEngine
    state: SignalState
    influenced_direction: bool
    source_status: str | None = None

    #: Continuous magnitude behind a categorical status, projected
    #: verbatim from the engine's own finding -- never recomputed here.
    #:
    #: `source_status` alone cannot separate companies whose category
    #: matches but whose economics do not: NVDA and AMAT are both
    #: `moderate` growth while compounding free cash flow at roughly
    #: +118%/yr and +6%/yr. That difference was measured and preserved
    #: on `BusinessFinding`, and stopped here.
    #:
    #: Explanatory only. No threshold is attached, no qualitative label
    #: is derived, and nothing in the recommendation path reads these:
    #: `select_direction`, `build_drivers` and
    #: `_derive_what_would_change` all take an explicit status
    #: argument, so a magnitude cannot reach them.
    #:
    #: `None` means no principled rate exists (fewer than two
    #: observations, or a non-positive endpoint) and stays distinct
    #: from a computed `0.0`.
    revenue_cagr: float | None = None
    free_cash_flow_cagr: float | None = None

    #: Self-relative valuation context, projected from
    #: `ValuationFinding` and populated on the valuation contribution
    #: only.
    #:
    #: `source_status` alone hides where a company sits inside its own
    #: history, and `current_yield` alone actively misleads: MSFT
    #: (0.01816) and NVDA (0.01840) look near-identical while sitting
    #: at the 10th and 58.8th percentile of their own distributions.
    #: The median anchors the level, and the observation count is what
    #: keeps a percentile honest -- AVGO and MA are both at the 50th,
    #: but from 2 and 14 observations respectively.
    #:
    #: Descriptive only. No threshold, no bucket, no qualitative word:
    #: `ValuationStatus` remains the sole categorical valuation
    #: judgement, and nothing in the recommendation path reads these.
    #:
    #: `historical_percentile` is a fraction in [0.0, 1.0] -- the share
    #: of historical observations strictly below `current_yield`, ties
    #: excluded, so the raw series' ordering cannot affect it.
    current_yield: float | None = None
    historical_median_yield: float | None = None
    historical_percentile: float | None = None
    historical_observation_count: int | None = None


#: Valuation-support gaps meaning "the analysis completed and the answer
#: is mixed", as opposed to "an input was missing".
#:
#: Mirrors `alpha.decision_readiness.engine`'s own
#: `_CONCLUSIVE_BUT_MIXED_VALUATION_GAPS`, which draws the identical
#: line for readiness blockers. Duplicated rather than shared because
#: Core may not import alpha; the classification is of Core's own
#: `ValuationSupportGapKind`, so Core owning a copy is correct rather
#: than a second authority. Compared as strings to keep this module
#: free of a valuation-package import.
_COMPLETE_BUT_MIXED_VALUATION_GAPS: frozenset[str] = frozenset(
    {"scenario_envelope_inconclusive", "conflicting_valuation_proofs"}
)


@dataclass(frozen=True)
class KeyUnknown:
    kind: KeyUnknownKind
    engine: CanonicalEngine


@dataclass(frozen=True)
class ConvictionReasoning:
    """Recommendation conviction, with its two kinds of reason kept
    apart. `analytical_reasons` is empty today and deliberately so:
    every member of `RecommendationConvictionReasonCode` describes
    evidence state rather than the company. Keeping the field present
    and empty is the honest representation -- it says "no analytical
    reason was recorded", not "this distinction does not exist"."""

    level: RecommendationConvictionLevel | None
    analytical_reasons: tuple[InvestmentReason, ...] = ()
    evidential_reasons: tuple[ProcessStateReason, ...] = ()


class ForwardGuidanceSubject(str, Enum):
    """The guided measure, as the forward-evidence layer names it. The
    two management-defined measures are flagged on each item: VST's
    "adjusted free cash flow before growth" is guidance for *a*
    free-cash-flow measure, never Atlas's own FCF figure."""

    REVENUE = "revenue"
    ADJUSTED_EBITDA = "adjusted_ebitda"
    FREE_CASH_FLOW = "free_cash_flow"
    CAPITAL_EXPENDITURE = "capital_expenditure"


class GuidanceRevisionKind(str, Enum):
    """What management's figure did -- and nothing about whether that is
    good. `REAFFIRMED` means the numbers did not move."""

    RAISED = "raised"
    LOWERED = "lowered"
    REAFFIRMED = "reaffirmed"


class UnestablishedEconomics(str, Enum):
    """Economics a customer commitment does not establish. Carried with
    every contracted-volume item so volume is never read as money."""

    PRICE = "price"
    REVENUE_CONTRIBUTION = "revenue_contribution"
    EARNINGS_CONTRIBUTION = "earnings_contribution"
    CASH_FLOW_CONTRIBUTION = "cash_flow_contribution"


_HORIZON_KINDS = frozenset({"fiscal_year", "calendar_year", "unspecified_year"})


@dataclass(frozen=True)
class ForwardGuidanceContext:
    """The latest verified revision of one guided measure for one horizon."""

    signal_id: str
    """The guidance revision's id -- the provenance link back through the
    interpretation, the revision and its claims to the transcript."""
    subject: ForwardGuidanceSubject
    measure_defined_by_management: bool
    horizon_period: str
    horizon_kind: str
    revision: GuidanceRevisionKind
    value_text: str
    """The new figure verbatim ("$6.8 billion-$7.6 billion")."""
    prior_value_text: str | None
    source_period: str | None
    revision_count: int
    """How many verified revisions of this measure and horizon exist,
    this one included (GOOGL's capex: 2)."""

    def __post_init__(self) -> None:
        if self.horizon_kind not in _HORIZON_KINDS:
            raise ValueError(f"unknown horizon kind {self.horizon_kind!r}")
        if self.revision_count < 1:
            raise ValueError("a guidance item is at least one revision")


@dataclass(frozen=True)
class ContractedVolumeContext:
    """One source observation of contracted customer volume. Observations
    are not agreements: the same agreement can be restated in several, so
    nothing here may be counted or summed as distinct contracts. Stated
    quantities are verbatim text only -- there is no number to add up."""

    signal_id: str
    source_period: str | None
    counterparty_text: str | None
    agreement_text: str
    quantity_texts: tuple[str, ...]
    """"up to 1,200 megawatts of new load" -- bound words, figure and
    measure, as stated."""
    term_years: float | None
    delivery_start_years: tuple[int, ...]
    delivery_end_years: tuple[int, ...]
    not_established: tuple[UnestablishedEconomics, ...]

    def __post_init__(self) -> None:
        if not self.quantity_texts:
            raise ValueError("a contracted-volume item states at least one quantity")
        if not self.not_established:
            raise ValueError("a contracted-volume item must say which economics it does not establish")


@dataclass(frozen=True)
class ForwardReasoningContext:
    """Verified forward evidence a user should know alongside the
    recommendation, which does not decide its direction. No polarity, no
    score, no materiality; ordered guidance first (by horizon and measure),
    then contracted volume (fiscal order)."""

    guidance: tuple[ForwardGuidanceContext, ...] = ()
    contracted_volume: tuple[ContractedVolumeContext, ...] = ()

    def __post_init__(self) -> None:
        if not self.guidance and not self.contracted_volume:
            raise ValueError("an empty forward context is None, never an empty object")

    @property
    def counterparty_texts(self) -> tuple[str, ...]:
        """Distinct customer names exactly as the sources state them --
        "Amazon" and "Amazon Web Services" stay two strings, and two
        strings are not two customers."""
        names = {c.counterparty_text for c in self.contracted_volume if c.counterparty_text is not None}
        return tuple(sorted(names, key=str.casefold))

    @property
    def unnamed_observation_count(self) -> int:
        return sum(1 for c in self.contracted_volume if c.counterparty_text is None)

    @property
    def unestablished_economics(self) -> tuple[UnestablishedEconomics, ...]:
        """Economics no contracted-volume observation establishes, in the
        enum's own order."""
        if not self.contracted_volume:
            return ()
        common = set.intersection(*(set(c.not_established) for c in self.contracted_volume))
        return tuple(aspect for aspect in UnestablishedEconomics if aspect in common)


#: The risk categories whose `HIGH` raises the `financial_risk` driver
#: (and dampens the direction), in the order `RiskCategory` declares
#: them. Valuation Risk is one of them: a `FINANCIAL_RISK_ELEVATED` driver
#: can rest on valuation alone, and its basis must say so.
ELEVATING_RISK_CATEGORIES = (RiskCategory.FINANCIAL_RISK, RiskCategory.VALUATION_RISK)


@dataclass(frozen=True)
class RiskDriverBasis:
    """What the `financial_risk` driver restates -- disclosed, never an
    input to it.

    `elevated_categories` names every category in
    `ELEVATING_RISK_CATEGORIES` that is `HIGH`: empty exactly when the
    driver is not elevated, and naming Valuation Risk when that is what
    raised it. `financial_risk` is the Financial Risk evaluator's own
    basis, whatever its level -- so a driver raised by valuation alone
    still shows that Financial Risk itself was not `HIGH`, rather than
    borrowing a financial explanation it does not have.

    Placed into the reasoning after the direction is chosen, like
    forward context; nothing that selects a direction, drivers, change
    triggers, unknowns or conviction reads it."""

    elevated_categories: tuple[RiskCategory, ...]
    financial_risk: FinancialRiskBasis

    def __post_init__(self) -> None:
        if self.elevated_categories != tuple(c for c in ELEVATING_RISK_CATEGORIES if c in self.elevated_categories):
            raise ValueError("elevated categories are Financial and/or Valuation Risk, once each, in that order")
        financial_high = self.financial_risk.level is RiskStatus.HIGH
        if financial_high != (RiskCategory.FINANCIAL_RISK in self.elevated_categories):
            raise ValueError("Financial Risk is elevated exactly when its own basis is HIGH")


#: `RecommendationConvictionReasonCode` -> process vs investment.
#: Additive: the source enum is untouched, so no stored value changes
#: meaning. Every current member is evidential; the mapping exists so a
#: future analytical member classifies correctly rather than silently
#: joining the evidential list.
_CONVICTION_PROCESS_CODES: dict[RecommendationConvictionReasonCode, ProcessStateReasonKind] = {
    RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_PARTIAL:
        ProcessStateReasonKind.EVIDENCE_COVERAGE_PARTIAL,
    RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_FULL:
        ProcessStateReasonKind.EVIDENCE_COVERAGE_FULL,
    RecommendationConvictionReasonCode.CONTRADICTING_EVIDENCE_PRESENT:
        ProcessStateReasonKind.CONTRADICTING_EVIDENCE_PRESENT,
    RecommendationConvictionReasonCode.NO_CONTRADICTING_EVIDENCE:
        ProcessStateReasonKind.NO_CONTRADICTING_EVIDENCE,
    RecommendationConvictionReasonCode.OPEN_QUESTIONS_REMAIN:
        ProcessStateReasonKind.OPEN_QUESTIONS_REMAIN,
    RecommendationConvictionReasonCode.NO_OPEN_QUESTIONS:
        ProcessStateReasonKind.NO_OPEN_QUESTIONS,
    RecommendationConvictionReasonCode.COMPANY_FUNDAMENTALS_EVIDENCE_ONLY:
        ProcessStateReasonKind.COMPANY_FUNDAMENTALS_EVIDENCE_ONLY,
}

_GROWTH_REASONS = {
    BusinessCategoryStatus.STRONG: (InvestmentReasonKind.GROWTH_STRONG, ReasoningPolarity.SUPPORTIVE),
    BusinessCategoryStatus.MODERATE: (InvestmentReasonKind.GROWTH_MODERATE, ReasoningPolarity.NEUTRAL),
    BusinessCategoryStatus.WEAK: (InvestmentReasonKind.GROWTH_WEAK, ReasoningPolarity.ADVERSE),
}
_CAPITAL_REASONS = {
    BusinessCategoryStatus.STRONG:
        (InvestmentReasonKind.CAPITAL_ALLOCATION_STRONG, ReasoningPolarity.SUPPORTIVE),
    BusinessCategoryStatus.MODERATE:
        (InvestmentReasonKind.CAPITAL_ALLOCATION_MODERATE, ReasoningPolarity.NEUTRAL),
    BusinessCategoryStatus.WEAK:
        (InvestmentReasonKind.CAPITAL_ALLOCATION_WEAK, ReasoningPolarity.ADVERSE),
}
_VALUATION_REASONS = {
    ValuationStatus.UNDERVALUED: (InvestmentReasonKind.VALUATION_UNDERVALUED, ReasoningPolarity.SUPPORTIVE),
    ValuationStatus.FAIRLY_VALUED: (InvestmentReasonKind.VALUATION_FAIRLY_VALUED, ReasoningPolarity.NEUTRAL),
    ValuationStatus.EXPENSIVE: (InvestmentReasonKind.VALUATION_EXPENSIVE, ReasoningPolarity.ADVERSE),
}
_VALUATION_SUPPORT_REASONS = {
    ValuationSupportStatus.SUPPORTED:
        (InvestmentReasonKind.VALUATION_SUPPORTED, ReasoningPolarity.SUPPORTIVE),
    ValuationSupportStatus.NOT_SUPPORTED:
        (InvestmentReasonKind.VALUATION_NOT_SUPPORTED, ReasoningPolarity.ADVERSE),
}

#: Statuses that mean "no conclusion", for every status vocabulary here.
_INCONCLUSIVE = frozenset({"not_evaluated", "insufficient_input"})
_NOT_APPLICABLE = "not_applicable"


def _median(values: tuple[float, ...]) -> float | None:
    """Standard median of the historical yields. Sorts, so the raw
    series' ordering is irrelevant; `None` when there is no history to
    take a median of."""
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _percentile(current: float | None, values: tuple[float, ...]) -> float | None:
    """Share of historical observations strictly below `current`, in
    [0.0, 1.0].

    Ties are excluded from the numerator, which makes the result
    independent of the series' ordering -- `historical_yields` is built
    from a dict and its order is not guaranteed, so nothing here may
    depend on it. `None` when there is no history, or no current
    observation to place within it.

    Computable at n=1 and n=2 and projected there, because
    `historical_observation_count` travels alongside and lets a reader
    judge how thin that history is. This function attaches no meaning
    to the number.
    """
    if current is None or not values:
        return None
    return sum(1 for value in values if value < current) / len(values)


def _reason(table, status, engine: CanonicalEngine) -> InvestmentReason | None:
    entry = table.get(status)
    if entry is None:
        return None
    kind, polarity = entry
    return InvestmentReason(kind=kind, polarity=polarity, engine=engine, source_status=status.value)


def build_drivers(
    *,
    growth_status: BusinessCategoryStatus,
    capital_allocation_status: BusinessCategoryStatus,
    valuation_status: ValuationStatus,
    valuation_support_status: ValuationSupportStatus,
    has_high_financial_or_valuation_risk: bool,
    financial_risk_assessed: bool,
) -> tuple[tuple[InvestmentReason, ...], tuple[InvestmentReason, ...]]:
    """`(primary_drivers, counter_drivers)` -- supportive and adverse,
    each already in `_ENGINE_PRECEDENCE` order.

    Every reason restates a status this function was handed; an engine
    that reached no conclusion contributes no driver at all rather than
    a neutral-looking one. `NEUTRAL` polarity appears in neither list:
    "fairly valued" is a real finding, carried in `signal_summary`, but
    it argues for nothing and must not pad a driver list.
    """
    risk_reason: InvestmentReason | None = None
    if has_high_financial_or_valuation_risk:
        risk_reason = InvestmentReason(
            kind=InvestmentReasonKind.FINANCIAL_RISK_ELEVATED,
            polarity=ReasoningPolarity.ADVERSE,
            engine=CanonicalEngine.FINANCIAL_RISK,
            source_status="high",
        )
    elif financial_risk_assessed:
        # Only a Financial Risk that reached a level can be "not
        # elevated". Insufficient or not-applicable is silence, never a
        # reassurance borrowed from another risk category.
        risk_reason = InvestmentReason(
            kind=InvestmentReasonKind.FINANCIAL_RISK_NOT_ELEVATED,
            polarity=ReasoningPolarity.SUPPORTIVE,
            engine=CanonicalEngine.FINANCIAL_RISK,
            source_status="not_high",
        )

    by_engine: dict[CanonicalEngine, InvestmentReason | None] = {
        CanonicalEngine.FINANCIAL_RISK: risk_reason,
        CanonicalEngine.VALUATION: _reason(_VALUATION_REASONS, valuation_status, CanonicalEngine.VALUATION),
        CanonicalEngine.VALUATION_SUPPORT: _reason(
            _VALUATION_SUPPORT_REASONS, valuation_support_status, CanonicalEngine.VALUATION_SUPPORT),
        CanonicalEngine.GROWTH: _reason(_GROWTH_REASONS, growth_status, CanonicalEngine.GROWTH),
        CanonicalEngine.CAPITAL_ALLOCATION: _reason(
            _CAPITAL_REASONS, capital_allocation_status, CanonicalEngine.CAPITAL_ALLOCATION),
    }
    ordered = [by_engine[engine] for engine in _ENGINE_PRECEDENCE if by_engine.get(engine) is not None]
    primary = tuple(r for r in ordered if r.polarity is ReasoningPolarity.SUPPORTIVE)
    counter = tuple(r for r in ordered if r.polarity is ReasoningPolarity.ADVERSE)
    return primary, counter


def build_signal_summary(
    *,
    growth_status: BusinessCategoryStatus,
    capital_allocation_status: BusinessCategoryStatus,
    valuation_status: ValuationStatus,
    valuation_support_status: ValuationSupportStatus,
    has_high_financial_or_valuation_risk: bool,
    financial_risk_assessed: bool,
    financial_risk_not_applicable: bool = False,
    growth_revenue_cagr: float | None = None,
    growth_free_cash_flow_cagr: float | None = None,
    valuation_current_yield: float | None = None,
    valuation_historical_yields: tuple[float, ...] = (),
) -> tuple[SignalContribution, ...]:
    """Total: one entry per `CanonicalEngine` member, every time.

    The three engines outside the direction contract are reported as
    `NOT_IN_DIRECTION_CONTRACT`, not omitted -- a benchmark reading this
    can then distinguish "negative", "neutral", "unknown", "not
    evaluated" and "not connected", which is precisely the distinction
    Calibration Phase 9 could not make.
    """
    def state(status_value: str) -> SignalState:
        if status_value == _NOT_APPLICABLE:
            return SignalState.NOT_EVALUATED
        return SignalState.INCONCLUSIVE if status_value in _INCONCLUSIVE else SignalState.CONCLUSIVE

    # `not_applicable` is its own token: the measure does not describe
    # this business, which is not a missing input (see build_key_unknowns).
    risk_status = "high" if has_high_financial_or_valuation_risk else (
        "not_high" if financial_risk_assessed else (
            "not_applicable" if financial_risk_not_applicable else "not_evaluated"))
    connected = (
        (CanonicalEngine.GROWTH, growth_status.value),
        (CanonicalEngine.CAPITAL_ALLOCATION, capital_allocation_status.value),
        (CanonicalEngine.VALUATION, valuation_status.value),
        (CanonicalEngine.VALUATION_SUPPORT, valuation_support_status.value),
        (CanonicalEngine.FINANCIAL_RISK, risk_status),
    )
    contributions = [
        SignalContribution(engine=engine, state=state(value), influenced_direction=True, source_status=value)
        for engine, value in connected
    ]
    # Attached to the growth contribution only -- these are growth's
    # own measurements, and giving them to another engine's entry
    # would misattribute them.
    contributions = [
        replace(c, revenue_cagr=growth_revenue_cagr, free_cash_flow_cagr=growth_free_cash_flow_cagr)
        if c.engine is CanonicalEngine.GROWTH else c
        for c in contributions
    ]
    contributions = [
        replace(
            c,
            current_yield=valuation_current_yield,
            historical_median_yield=_median(valuation_historical_yields),
            historical_percentile=_percentile(valuation_current_yield, valuation_historical_yields),
            historical_observation_count=len(valuation_historical_yields) or None,
        )
        if c.engine is CanonicalEngine.VALUATION else c
        for c in contributions
    ]
    contributions.extend(
        SignalContribution(
            engine=engine, state=SignalState.NOT_IN_DIRECTION_CONTRACT,
            influenced_direction=False, source_status=None)
        for engine in (CanonicalEngine.BUSINESS_QUALITY, CanonicalEngine.INDUSTRY_CONTEXT,
                       CanonicalEngine.EXPECTED_RETURN)
    )
    return tuple(contributions)


def build_key_unknowns(
    signal_summary: tuple[SignalContribution, ...],
    *,
    valuation_support_gap: str | None = None,
) -> tuple[KeyUnknown, ...]:
    """Derived from `signal_summary` alone, so the two can never
    disagree. Deliberately not built from readiness blockers: a blocker
    describes Atlas's workflow, and reusing it here would smuggle
    process state back into investment reasoning through a side door."""
    unknowns: list[KeyUnknown] = []
    for contribution in signal_summary:
        if contribution.source_status == _NOT_APPLICABLE:
            # The engine's measure does not describe this business; no
            # input would resolve it, so it is not an unknown to list.
            continue
        if contribution.state is SignalState.INCONCLUSIVE or contribution.state is SignalState.NOT_EVALUATED:
            # `gap` is authoritative about which of two very different
            # situations produced INSUFFICIENT_INPUT. This projects that
            # existing classification; it never re-derives it, and an
            # absent or unrecognised gap keeps the conservative default.
            complete_but_mixed = (
                contribution.engine is CanonicalEngine.VALUATION_SUPPORT
                and valuation_support_gap in _COMPLETE_BUT_MIXED_VALUATION_GAPS
            )
            unknowns.append(KeyUnknown(
                kind=KeyUnknownKind.ANALYSIS_COMPLETE_UNRESOLVED if complete_but_mixed
                else KeyUnknownKind.ANALYSIS_INPUT_MISSING,
                engine=contribution.engine))
        elif contribution.state is SignalState.NOT_IN_DIRECTION_CONTRACT:
            unknowns.append(KeyUnknown(
                kind=KeyUnknownKind.NOT_CONNECTED_TO_DIRECTION, engine=contribution.engine))
    return tuple(unknowns)


def build_conviction_reasoning(
    assessment: RecommendationConvictionAssessment | None,
) -> ConvictionReasoning:
    """Splits an already-computed assessment's reasons by kind. Reads
    the assessment; never recomputes a level."""
    if assessment is None:
        return ConvictionReasoning(level=None)
    evidential = tuple(
        ProcessStateReason(kind=_CONVICTION_PROCESS_CODES[code])
        for code in assessment.reasons
        if code in _CONVICTION_PROCESS_CODES
    )
    return ConvictionReasoning(level=assessment.level, evidential_reasons=evidential)


# --- Serialization ----------------------------------------------------
#
# Covers the canonical *analytical* rationale only: drivers, signal
# summary, unknowns, the change trigger and conviction reasoning. The
# `current_situation`/`supporting_evidence`/`contradicting_evidence`/
# `portfolio_context` summaries embedded alongside them are existing
# `decision_engine` structures with their own owners, and duplicating
# them into this payload would make a second copy of a fact that
# already has a home.
#
# Every value written is a closed-vocabulary `.value` string, so the
# payload is stable across releases and readable without importing a
# single engine -- the property that lets a benchmark score a stored
# row directly.

#: Marks a payload written by this version. Absence is meaningful: see
#: `LEGACY_RESULT_WITHOUT_REASONING`.
REASONING_SCHEMA_VERSION = 1

#: A historical row produced before reasoning was persisted. This is
#: NOT "Atlas had no reasoning" -- it is "this row predates reasoning
#: being stored". Nothing recomputes it, because a reconstruction from
#: today's code would silently claim to be what the run actually
#: concluded.
LEGACY_RESULT_WITHOUT_REASONING = "legacy_result_without_reasoning"


def serialize_reasoning(reasoning) -> dict:
    """Deterministic and total. Field order is fixed and every value is
    a closed-vocabulary string."""
    conviction = reasoning.conviction_reasoning
    return {
        "schemaVersion": REASONING_SCHEMA_VERSION,
        "primaryDrivers": [_reason_payload(r) for r in reasoning.primary_drivers],
        "counterDrivers": [_reason_payload(r) for r in reasoning.counter_drivers],
        "signalSummary": [
            {
                "engine": c.engine.value,
                "state": c.state.value,
                "influencedDirection": c.influenced_direction,
                "sourceStatus": c.source_status,
                # Explicit nulls: absent and zero must stay
                # distinguishable through storage and the API.
                "revenueCagr": c.revenue_cagr,
                "freeCashFlowCagr": c.free_cash_flow_cagr,
                "currentYield": c.current_yield,
                "historicalMedianYield": c.historical_median_yield,
                "historicalPercentile": c.historical_percentile,
                "historicalObservationCount": c.historical_observation_count,
            }
            for c in reasoning.signal_summary
        ],
        "keyUnknowns": [{"kind": u.kind.value, "engine": u.engine.value} for u in reasoning.key_unknowns],
        "whatWouldChange": [t.value for t in reasoning.what_would_change],
        "recommendationConviction": None if conviction is None else {
            "level": conviction.level.value if conviction.level is not None else None,
            "analyticalReasons": [_reason_payload(r) for r in conviction.analytical_reasons],
            "evidentialReasons": [r.kind.value for r in conviction.evidential_reasons],
        },
        # Additive: `null` when Atlas holds no verified forward evidence
        # for the company; absent on rows written before it existed.
        # `getattr`: the serializer has always accepted any reasoning-shaped
        # object, and one written before forward context existed has none.
        "forwardContext": _forward_context_payload(getattr(reasoning, "forward_context", None)),
        # Additive, same rules: `null` when no basis was carried, absent
        # on rows written before it existed.
        "riskBasis": _risk_basis_payload(getattr(reasoning, "risk_basis", None)),
    }


#: The risk-basis wire format. v1 (the Financial-Risk Basis Disclosure
#: sprint's signal basis) was never read back; a payload without this
#: version is not interpreted as v2 -- it reads as no basis.
RISK_BASIS_VERSION = 2


def _observation_payload(o: DebtBurdenObservation) -> dict:
    return {
        "period": o.period,
        "unit": o.unit,
        "totalDebt": o.total_debt,
        "freeCashFlow": o.free_cash_flow,
        "capitalExpenditure": o.capital_expenditure,
        # Derived, stated once so no reader re-derives it.
        "operatingCashFlow": o.operating_cash_flow,
        "ratio": o.ratio,
        "totalDebtFactId": o.total_debt_fact_id,
        "freeCashFlowFactId": o.free_cash_flow_fact_id,
        "capitalExpenditureFactId": o.capital_expenditure_fact_id,
        "sourceRecordIds": list(o.source_record_ids),
    }


def _risk_basis_payload(basis: RiskDriverBasis | None) -> dict | None:
    if basis is None:
        return None
    financial = basis.financial_risk
    return {
        "version": RISK_BASIS_VERSION,
        "elevatedCategories": [c.value for c in basis.elevated_categories],
        "financialRisk": {
            "level": financial.level.value,
            "condition": financial.condition.value,
            "measure": financial.measure.value if financial.measure else None,
            "bands": {"lowBelow": financial.bands.low_below, "highFrom": financial.bands.high_from},
            "latest": _observation_payload(financial.latest) if financial.latest else None,
            "history": [_observation_payload(o) for o in financial.history],
            "industry": financial.industry,
            "gaps": [g.value for g in financial.gaps],
            "excluded": [{"factId": e.fact_id, "reason": e.reason.value} for e in financial.excluded],
        },
    }


def _observation_from_payload(o: dict) -> DebtBurdenObservation:
    return DebtBurdenObservation(
        period=o["period"],
        unit=o["unit"],
        total_debt=o["totalDebt"],
        free_cash_flow=o["freeCashFlow"],
        capital_expenditure=o["capitalExpenditure"],
        total_debt_fact_id=o["totalDebtFactId"],
        free_cash_flow_fact_id=o["freeCashFlowFactId"],
        capital_expenditure_fact_id=o["capitalExpenditureFactId"],
        source_record_ids=tuple(o["sourceRecordIds"]),
    )


def _risk_basis_from_payload(payload: dict | None) -> RiskDriverBasis | None:
    if not payload or payload.get("version") != RISK_BASIS_VERSION:
        return None
    financial = payload["financialRisk"]
    latest = _observation_from_payload(financial["latest"]) if financial.get("latest") else None
    history = tuple(_observation_from_payload(o) for o in financial.get("history", ()))
    return RiskDriverBasis(
        elevated_categories=tuple(RiskCategory(c) for c in payload["elevatedCategories"]),
        financial_risk=FinancialRiskBasis(
            level=RiskStatus(financial["level"]),
            condition=FinancialRiskCondition(financial["condition"]),
            bands=DebtBurdenBands(low_below=financial["bands"]["lowBelow"], high_from=financial["bands"]["highFrom"]),
            measure=FinancialRiskMeasure(financial["measure"]) if financial.get("measure") else None,
            # The latest is the last history entry; reuse it so the two stay one object.
            latest=history[-1] if latest is not None and history else latest,
            history=history,
            industry=financial.get("industry"),
            gaps=tuple(RiskDataGapKind(g) for g in financial.get("gaps", ())),
            excluded=tuple(
                FinancialRiskExclusion(e["factId"], FinancialRiskExclusionReason(e["reason"]))
                for e in financial.get("excluded", ())
            ),
        ),
    )


def _forward_context_payload(context: ForwardReasoningContext | None) -> dict | None:
    if context is None:
        return None
    return {
        "guidance": [
            {
                "signalId": g.signal_id,
                "subject": g.subject.value,
                "measureDefinedByManagement": g.measure_defined_by_management,
                "horizonPeriod": g.horizon_period,
                "horizonKind": g.horizon_kind,
                "revision": g.revision.value,
                "valueText": g.value_text,
                "priorValueText": g.prior_value_text,
                "sourcePeriod": g.source_period,
                "revisionCount": g.revision_count,
            }
            for g in context.guidance
        ],
        "contractedVolume": [
            {
                "signalId": c.signal_id,
                "sourcePeriod": c.source_period,
                "counterpartyText": c.counterparty_text,
                "agreementText": c.agreement_text,
                "quantityTexts": list(c.quantity_texts),
                "termYears": c.term_years,
                "deliveryStartYears": list(c.delivery_start_years),
                "deliveryEndYears": list(c.delivery_end_years),
                "notEstablished": [a.value for a in c.not_established],
            }
            for c in context.contracted_volume
        ],
        # Projections of the items above, stated once so no reader has to
        # re-derive them -- and so none is tempted to count contracts.
        "counterpartyTexts": list(context.counterparty_texts),
        "unnamedObservationCount": context.unnamed_observation_count,
        "unestablishedEconomics": [a.value for a in context.unestablished_economics],
        "identityResolved": False,
    }


def _forward_context_from_payload(payload: dict | None) -> ForwardReasoningContext | None:
    if not payload:
        return None
    return ForwardReasoningContext(
        guidance=tuple(
            ForwardGuidanceContext(
                signal_id=g["signalId"],
                subject=ForwardGuidanceSubject(g["subject"]),
                measure_defined_by_management=g["measureDefinedByManagement"],
                horizon_period=g["horizonPeriod"],
                horizon_kind=g["horizonKind"],
                revision=GuidanceRevisionKind(g["revision"]),
                value_text=g["valueText"],
                prior_value_text=g.get("priorValueText"),
                source_period=g.get("sourcePeriod"),
                revision_count=g["revisionCount"],
            )
            for g in payload.get("guidance", ())
        ),
        contracted_volume=tuple(
            ContractedVolumeContext(
                signal_id=c["signalId"],
                source_period=c.get("sourcePeriod"),
                counterparty_text=c.get("counterpartyText"),
                agreement_text=c["agreementText"],
                quantity_texts=tuple(c["quantityTexts"]),
                term_years=c.get("termYears"),
                delivery_start_years=tuple(c.get("deliveryStartYears", ())),
                delivery_end_years=tuple(c.get("deliveryEndYears", ())),
                not_established=tuple(UnestablishedEconomics(a) for a in c["notEstablished"]),
            )
            for c in payload.get("contractedVolume", ())
        ),
    )


def _reason_payload(reason: InvestmentReason) -> dict:
    return {
        "kind": reason.kind.value,
        "polarity": reason.polarity.value,
        "engine": reason.engine.value,
        "sourceStatus": reason.source_status,
    }


def _to_reason(payload: dict) -> InvestmentReason:
    return InvestmentReason(
        kind=InvestmentReasonKind(payload["kind"]),
        polarity=ReasoningPolarity(payload["polarity"]),
        engine=CanonicalEngine(payload["engine"]),
        source_status=payload["sourceStatus"],
    )


@dataclass(frozen=True)
class StoredReasoning:
    """What a stored row yields. Deliberately not a
    `RecommendationReasoning`: the persisted payload carries the
    analytical rationale, not the embedded `decision_engine` summaries,
    and pretending otherwise would invite a reader to expect fields
    that were never written."""

    primary_drivers: tuple[InvestmentReason, ...]
    counter_drivers: tuple[InvestmentReason, ...]
    signal_summary: tuple[SignalContribution, ...]
    key_unknowns: tuple[KeyUnknown, ...]
    what_would_change: tuple[str, ...]
    conviction: ConvictionReasoning | None
    schema_version: int = REASONING_SCHEMA_VERSION
    forward_context: ForwardReasoningContext | None = None
    risk_basis: RiskDriverBasis | None = None


def deserialize_reasoning(payload: dict | None) -> StoredReasoning | None:
    """`None` for a legacy row -- callers must report that as
    `LEGACY_RESULT_WITHOUT_REASONING`, never as empty reasoning."""
    if not payload:
        return None
    conviction_payload = payload.get("recommendationConviction")
    conviction = None
    if conviction_payload is not None:
        level = conviction_payload.get("level")
        conviction = ConvictionReasoning(
            level=RecommendationConvictionLevel(level) if level else None,
            analytical_reasons=tuple(_to_reason(r) for r in conviction_payload.get("analyticalReasons", ())),
            evidential_reasons=tuple(
                ProcessStateReason(kind=ProcessStateReasonKind(k))
                for k in conviction_payload.get("evidentialReasons", ())
            ),
        )
    return StoredReasoning(
        primary_drivers=tuple(_to_reason(r) for r in payload.get("primaryDrivers", ())),
        counter_drivers=tuple(_to_reason(r) for r in payload.get("counterDrivers", ())),
        signal_summary=tuple(
            SignalContribution(
                engine=CanonicalEngine(c["engine"]),
                state=SignalState(c["state"]),
                influenced_direction=c["influencedDirection"],
                source_status=c.get("sourceStatus"),
                # `.get`: a row written before these existed simply has
                # no key, and must read back as absent rather than zero.
                revenue_cagr=c.get("revenueCagr"),
                free_cash_flow_cagr=c.get("freeCashFlowCagr"),
                current_yield=c.get("currentYield"),
                historical_median_yield=c.get("historicalMedianYield"),
                historical_percentile=c.get("historicalPercentile"),
                historical_observation_count=c.get("historicalObservationCount"),
            )
            for c in payload.get("signalSummary", ())
        ),
        key_unknowns=tuple(
            KeyUnknown(kind=KeyUnknownKind(u["kind"]), engine=CanonicalEngine(u["engine"]))
            for u in payload.get("keyUnknowns", ())
        ),
        what_would_change=tuple(payload.get("whatWouldChange", ())),
        conviction=conviction,
        schema_version=payload.get("schemaVersion", REASONING_SCHEMA_VERSION),
        forward_context=_forward_context_from_payload(payload.get("forwardContext")),
        risk_basis=_risk_basis_from_payload(payload.get("riskBasis")),
    )

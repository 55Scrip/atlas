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
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.recommendation_conviction import (
    RecommendationConvictionAssessment,
    RecommendationConvictionLevel,
    RecommendationConvictionReasonCode,
)
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupportStatus

__all__ = [
    "CanonicalEngine",
    "ConvictionReasoning",
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
    has_real_risk_evidence: bool,
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
    elif has_real_risk_evidence:
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
    has_real_risk_evidence: bool,
) -> tuple[SignalContribution, ...]:
    """Total: one entry per `CanonicalEngine` member, every time.

    The three engines outside the direction contract are reported as
    `NOT_IN_DIRECTION_CONTRACT`, not omitted -- a benchmark reading this
    can then distinguish "negative", "neutral", "unknown", "not
    evaluated" and "not connected", which is precisely the distinction
    Calibration Phase 9 could not make.
    """
    def state(status_value: str) -> SignalState:
        return SignalState.INCONCLUSIVE if status_value in _INCONCLUSIVE else SignalState.CONCLUSIVE

    risk_status = "high" if has_high_financial_or_valuation_risk else (
        "not_high" if has_real_risk_evidence else "not_evaluated")
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
    contributions.extend(
        SignalContribution(
            engine=engine, state=SignalState.NOT_IN_DIRECTION_CONTRACT,
            influenced_direction=False, source_status=None)
        for engine in (CanonicalEngine.BUSINESS_QUALITY, CanonicalEngine.INDUSTRY_CONTEXT,
                       CanonicalEngine.EXPECTED_RETURN)
    )
    return tuple(contributions)


def build_key_unknowns(signal_summary: tuple[SignalContribution, ...]) -> tuple[KeyUnknown, ...]:
    """Derived from `signal_summary` alone, so the two can never
    disagree. Deliberately not built from readiness blockers: a blocker
    describes Atlas's workflow, and reusing it here would smuggle
    process state back into investment reasoning through a side door."""
    unknowns: list[KeyUnknown] = []
    for contribution in signal_summary:
        if contribution.state is SignalState.INCONCLUSIVE or contribution.state is SignalState.NOT_EVALUATED:
            unknowns.append(KeyUnknown(
                kind=KeyUnknownKind.ANALYSIS_INPUT_MISSING, engine=contribution.engine))
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

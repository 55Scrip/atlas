"""Conviction (ATLAS-020, Phase 9; extended ATLAS-024, ATLAS-026) --
the real Conviction model.

Conviction answers "how strongly does the available analysis support an
investment conclusion" -- distinct from Confidence
(`confidence.py`, "how trustworthy is Atlas's own analysis") and never
to be confused with investor-entered `Decision.confidence`. It is not
company quality, not valuation, not a recommendation -- it consumes
`atlas.analysis_engine.business`/`.valuation`/`.risk`'s own conclusions,
it never recomputes or overrides any of them.

Categorical, five levels, **never numeric, never weighted, never
manually entered**. `calculate_conviction` is a pure, deterministic
function: an ordered decision table over signals `atlas.decision_engine`
and this package's own stages already compute today, evaluated top to
bottom, first match wins -- the same style
`atlas.domains.portfolio.calculations.concentration_level`'s own
if/elif chain already established for "deterministic classification,
never an invented score."

**`business_conclusive`** (real since ATLAS-026): `True` exactly when
both of `atlas.analysis_engine.business`'s currently real evaluators --
Growth and Capital Allocation -- reach a genuine categorical conclusion
(not `NOT_EVALUATED`/`INSUFFICIENT_INPUT`). Deliberately does not wait
on the other four `BusinessCategory` members (including Durability,
still structurally locked) -- those are known capability gaps, not
evidence that the two implemented evaluators failed. This definition is
expected to widen naturally as future sprints add real evaluators for
the remaining categories, the same way `valuation_conclusive` (real
since ATLAS-024) already means "the one real Valuation method today
reached a conclusion," not "every `ValuationMethodKind` did."

**`has_high_financial_or_valuation_risk`** (real since ATLAS-026):
`True` when `atlas.analysis_engine.risk`'s `FINANCIAL_RISK` or
`VALUATION_RISK` category reaches `RiskStatus.HIGH`. Deliberately
excludes `BUSINESS_RISK` (itself a direct reinterpretation of Growth's
own status, already reflected here via `business_conclusive`) and
`THESIS_RISK` (itself a direct reinterpretation of the same
`ContradictionSummary` `has_contradicting_evidence` already reads) --
folding either back in would count one underlying fact twice under two
different names. A Risk category that is `INSUFFICIENT_INPUT` never
moves Conviction by itself: missing risk evidence is uncertainty, the
same "missing is not automatically negative" principle
`atlas.analysis_engine.risk` itself applies to every one of its own
categories.

`is_thesis_stale`, `has_contradicting_evidence`, and `has_open_questions`
are supplied by the caller rather than recomputed here, because their
underlying data (Alpha portfolio staleness threshold, Core Evidence/
Observation records) belongs to layers this package's own architectural
boundary does not read (`atlas.alpha`) or that a sibling
`atlas.decision_engine` stage already computed (Reasoning's own
contradicting-evidence/open-question findings) -- passing them in avoids
recomputing what already exists exactly once, elsewhere.

**Scenario Availability is deliberately never read here.**
`CanonicalAnalysis.scenario_analysis` is structurally
`CapabilityStatus.NOT_YET_IMPLEMENTED` on every run, with no exception --
a permanent constant carries no information to condition on, the same
reason Durability's own permanent lock stays out of
`atlas.analysis_engine.risk.business_risk`. Conviction ignoring it is a
deliberate choice, not an oversight.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

__all__ = ["ConvictionLevel", "ConvictionReasonCode", "ConvictionAssessment", "calculate_conviction"]


class ConvictionLevel(str, Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ConvictionReasonCode(str, Enum):
    """Every reason that contributed to a Conviction assessment --
    `ConvictionAssessment.reasons` always names every applicable code,
    not only the single deciding one, so "why did conviction change"
    has a complete answer rather than the first branch that happened to
    match."""

    UPSTREAM_STAGE_NOT_EVALUATED = "upstream_stage_not_evaluated"
    EVIDENCE_COVERAGE_INSUFFICIENT = "evidence_coverage_insufficient"
    EVIDENCE_COVERAGE_PARTIAL = "evidence_coverage_partial"
    EVIDENCE_COVERAGE_FULL = "evidence_coverage_full"
    CONTRADICTING_EVIDENCE_PRESENT = "contradicting_evidence_present"
    NO_CONTRADICTING_EVIDENCE = "no_contradicting_evidence"
    THESIS_STALE = "thesis_stale"
    THESIS_NOT_STALE = "thesis_not_stale"
    OPEN_QUESTIONS_REMAIN = "open_questions_remain"
    NO_OPEN_QUESTIONS = "no_open_questions"
    BUSINESS_OR_VALUATION_NOT_YET_CONCLUSIVE = "business_or_valuation_not_yet_conclusive"
    BUSINESS_AND_VALUATION_CONCLUSIVE = "business_and_valuation_conclusive"
    HIGH_FINANCIAL_OR_VALUATION_RISK_PRESENT = "high_financial_or_valuation_risk_present"
    NO_HIGH_FINANCIAL_OR_VALUATION_RISK = "no_high_financial_or_valuation_risk"


@dataclass(frozen=True)
class ConvictionAssessment:
    level: ConvictionLevel
    reasons: tuple[ConvictionReasonCode, ...]


def calculate_conviction(
    *,
    business_state: EvaluationState,
    valuation_state: EvaluationState,
    evidence_coverage: EvidenceCoverageLevel,
    has_contradicting_evidence: bool,
    has_open_questions: bool,
    is_thesis_stale: bool,
    business_conclusive: bool = False,
    valuation_conclusive: bool = False,
    has_high_financial_or_valuation_risk: bool = False,
) -> ConvictionAssessment:
    """Deterministic: identical inputs always produce an identical
    `ConvictionAssessment`. No wall-clock read, no randomness, no
    partial credit -- every branch below is a real signal already
    computed elsewhere in this codebase.

    `reasons` is always built in the same fixed order regardless of
    which branch decides the level, so two assessments are trivially
    diffable field-by-field: upstream-stage reason (only when it fired),
    then coverage, then contradiction, then risk, then staleness, then
    open questions, then business/valuation conclusiveness (only once
    coverage is known to be FULL with no contradiction, no high risk,
    no staleness, and no open questions -- the only region where it can
    change the outcome).
    """
    if business_state is not EvaluationState.EVALUATED or valuation_state is not EvaluationState.EVALUATED:
        return ConvictionAssessment(
            level=ConvictionLevel.INSUFFICIENT_EVIDENCE,
            reasons=(ConvictionReasonCode.UPSTREAM_STAGE_NOT_EVALUATED,),
        )

    if evidence_coverage in (EvidenceCoverageLevel.NOT_APPLICABLE, EvidenceCoverageLevel.NONE):
        return ConvictionAssessment(
            level=ConvictionLevel.INSUFFICIENT_EVIDENCE,
            reasons=(ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,),
        )

    coverage_reason = (
        ConvictionReasonCode.EVIDENCE_COVERAGE_FULL
        if evidence_coverage is EvidenceCoverageLevel.FULL
        else ConvictionReasonCode.EVIDENCE_COVERAGE_PARTIAL
    )
    contradiction_reason = (
        ConvictionReasonCode.CONTRADICTING_EVIDENCE_PRESENT
        if has_contradicting_evidence
        else ConvictionReasonCode.NO_CONTRADICTING_EVIDENCE
    )
    risk_reason = (
        ConvictionReasonCode.HIGH_FINANCIAL_OR_VALUATION_RISK_PRESENT
        if has_high_financial_or_valuation_risk
        else ConvictionReasonCode.NO_HIGH_FINANCIAL_OR_VALUATION_RISK
    )
    staleness_reason = (
        ConvictionReasonCode.THESIS_STALE if is_thesis_stale else ConvictionReasonCode.THESIS_NOT_STALE
    )
    open_questions_reason = (
        ConvictionReasonCode.OPEN_QUESTIONS_REMAIN if has_open_questions else ConvictionReasonCode.NO_OPEN_QUESTIONS
    )
    base_reasons = (coverage_reason, contradiction_reason, risk_reason, staleness_reason, open_questions_reason)

    if (
        has_contradicting_evidence
        or evidence_coverage is EvidenceCoverageLevel.PARTIAL
        or has_high_financial_or_valuation_risk
    ):
        return ConvictionAssessment(level=ConvictionLevel.LOW, reasons=base_reasons)

    # From here: coverage is FULL, no contradicting evidence, no high
    # Financial/Valuation Risk.
    if is_thesis_stale or has_open_questions:
        return ConvictionAssessment(level=ConvictionLevel.MODERATE, reasons=base_reasons)

    if not (business_conclusive and valuation_conclusive):
        return ConvictionAssessment(
            level=ConvictionLevel.HIGH,
            reasons=base_reasons + (ConvictionReasonCode.BUSINESS_OR_VALUATION_NOT_YET_CONCLUSIVE,),
        )

    return ConvictionAssessment(
        level=ConvictionLevel.VERY_HIGH,
        reasons=base_reasons + (ConvictionReasonCode.BUSINESS_AND_VALUATION_CONCLUSIVE,),
    )

"""Conviction (ATLAS-020, Phase 9) -- the first real Conviction model.

Conviction answers "how strongly does the available analysis support an
investment conclusion" -- distinct from Confidence
(`confidence.py`, "how trustworthy is Atlas's own analysis") and never
to be confused with investor-entered `Decision.confidence`.

Categorical, five levels, **never numeric, never weighted, never
manually entered**. `calculate_conviction` is a pure, deterministic
function: an ordered decision table over signals
`atlas.decision_engine` already computes today, evaluated top to
bottom, first match wins -- the same style
`atlas.domains.portfolio.calculations.concentration_level`'s own
if/elif chain already established for "deterministic classification,
never an invented score."

Two inputs (`business_conclusive`, `valuation_conclusive`) are always
`False` under current data: `atlas.decision_engine.stages
.business_evaluation`'s Durability finding and
`atlas.decision_engine.stages.valuation`'s substantive Valuation finding
are both structurally locked to `INSUFFICIENT_INPUT` today (no external
data source exists to compute them from) -- so `VERY_HIGH` is honestly
unreachable under today's data, by construction, not by an arbitrary
cap. The parameters exist so this function is complete now and needs no
change the day Business/Valuation genuinely start producing
conclusions.

`is_thesis_stale`, `has_contradicting_evidence`, and `has_open_questions`
are supplied by the caller rather than recomputed here, because their
underlying data (Alpha portfolio staleness threshold, Core Evidence/
Observation records) belongs to layers this package's own architectural
boundary does not read (`atlas.alpha`) or that a sibling
`atlas.decision_engine` stage already computed (Reasoning's own
contradicting-evidence/open-question findings) -- passing them in avoids
recomputing what already exists exactly once, elsewhere.
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
) -> ConvictionAssessment:
    """Deterministic: identical inputs always produce an identical
    `ConvictionAssessment`. No wall-clock read, no randomness, no
    partial credit -- every branch below is a real signal already
    computed elsewhere in this codebase.

    `reasons` is always built in the same fixed order regardless of
    which branch decides the level, so two assessments are trivially
    diffable field-by-field: upstream-stage reason (only when it fired),
    then coverage, then contradiction, then staleness, then open
    questions, then business/valuation conclusiveness (only once
    coverage is known to be FULL with no contradiction, staleness, or
    open questions -- the only region where it can change the outcome).
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
    staleness_reason = (
        ConvictionReasonCode.THESIS_STALE if is_thesis_stale else ConvictionReasonCode.THESIS_NOT_STALE
    )
    open_questions_reason = (
        ConvictionReasonCode.OPEN_QUESTIONS_REMAIN if has_open_questions else ConvictionReasonCode.NO_OPEN_QUESTIONS
    )
    base_reasons = (coverage_reason, contradiction_reason, staleness_reason, open_questions_reason)

    if has_contradicting_evidence or evidence_coverage is EvidenceCoverageLevel.PARTIAL:
        return ConvictionAssessment(level=ConvictionLevel.LOW, reasons=base_reasons)

    # From here: coverage is FULL and there is no contradicting evidence.
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

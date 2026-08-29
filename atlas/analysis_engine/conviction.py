"""Conviction (ATLAS-020, Phase 9; extended ATLAS-024, ATLAS-026;
redesigned Calibration Phase 4 -- Conviction & Capital Allocation
Repair) -- the real Conviction model.

Conviction answers "how strongly does the available analysis support an
investment conclusion" -- distinct from Confidence
(`confidence.py`, "how trustworthy is Atlas's own analysis") and never
to be confused with investor-entered `Decision.confidence`. It is not
company quality, not valuation, not a recommendation -- it consumes
`atlas.analysis_engine.business`/`.valuation`/`.risk`'s own conclusions,
it never recomputes or overrides any of them.

**Calibration Phase 4: Conviction no longer requires investor-recorded
notes.** Calibration Phase 3 (a live 25-company diagnosis) confirmed
every real holding read `INSUFFICIENT_EVIDENCE` regardless of how deep
Atlas's own company analysis was, because this function's own
`evidence_coverage` parameter was, at its one real call site, literally
`business_evaluation.evidence_quality.coverage` -- `EvidenceCoverageLevel`,
a value structurally defined as "how many investor-recorded Observations
have linked Evidence" (`decision_engine/contracts.py`'s own enum
docstrings), not a fact about the company or Atlas's own analysis of it.
`atlas.analysis_engine.analysis_coverage` (a prior sprint, "Internal
Alpha Fix Sprint 1, Part 2") had already diagnosed almost this exact
gap and built a second, purely company-data-driven signal
(`AnalysisCoverageLevel`) -- but deliberately chose to add it *alongside*
Conviction rather than fix Conviction's own definition, on the belief
that Conviction was correctly answering the question it was built to
answer. Calibration Phase 4's own brief explicitly overrides that
belief: three inputs below are now sourced from Atlas's own knowledge
instead of investor history (`analysis_coverage` replaces
`evidence_coverage`; `has_contradicting_evidence` now reads a finding's
own supporting-vs-contradicting evidence, never an investor's Observation
classification; `has_open_questions` now reads the curated,
business-analysis-derived open questions, never `decision_engine`'s
evidence-linkage gap list). See
`docs/Calibration-Phase-4-Conviction-And-Capital-Allocation-Redesign.md`
for the full investigation and design. `is_thesis_stale` remains
investor-Decision-based and is unchanged this sprint -- see that same
document's own disclosed scope boundary for why. Investor Decisions/
Observations are not deleted or devalued by this change; they continue
to feed Stance and `AnalysisCoverageLevel`'s own sibling display --
removed from Conviction specifically, per the brief's own instruction
that past investor decisions "may still influence personalization, but
never the analytical conviction itself."

The reason codes below (`EVIDENCE_COVERAGE_*`) keep their existing wire
names even though their real meaning shifted from "investor evidence
coverage" to "Atlas's own analysis coverage" -- renaming them would be
a wire-facing, presentation-layer change this sprint's own "no
presentation changes mixed into engine work" instruction forbids;
`ConvictionAssessmentView`/the frontend's own translation keys are
unmodified.

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

from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.decision_engine.contracts import EvaluationState

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
    analysis_coverage: AnalysisCoverageLevel,
    business_conclusive: bool,
    valuation_conclusive: bool,
    has_contradicting_evidence: bool,
    has_open_questions: bool,
    is_thesis_stale: bool,
    has_high_financial_or_valuation_risk: bool = False,
) -> ConvictionAssessment:
    """Deterministic: identical inputs always produce an identical
    `ConvictionAssessment`. No wall-clock read, no randomness, no
    partial credit -- every branch below is a real signal already
    computed elsewhere in this codebase.

    Calibration Phase 4: `analysis_coverage` (Atlas's own knowledge --
    does real company data exist, did Business Analysis and Valuation
    reach real conclusions from it) replaces the old `evidence_coverage`
    parameter (investor-recorded-Observation coverage) as this gate's
    primary signal -- see this module's own docstring. `has_contradicting
    _evidence`/`has_open_questions` keep their names but are now expected
    to be sourced from Atlas's own analysis (a finding's own supporting-
    vs-contradicting evidence; `investment_case_synthesis
    .derive_case_open_questions`), never investor Observations -- see
    the real call site in `pipeline.py`.

    `reasons` is always built in the same fixed order regardless of
    which branch decides the level, so two assessments are trivially
    diffable field-by-field: upstream-stage reason (only when it fired),
    then coverage, then contradiction, then risk, then staleness, then
    open questions, then business/valuation conclusiveness.

    `analysis_coverage` gates only the `NO_COVERAGE` floor (does real
    company data exist at all) -- `AnalysisCoverageLevel.SUBSTANTIAL
    _COVERAGE` is, by that module's own definition, exactly
    `business_conclusive and valuation_conclusive`, so gating the `LOW`
    branch on `PARTIAL_COVERAGE` as well would make `business_conclusive`/
    `valuation_conclusive` redundant with coverage and leave `HIGH`
    permanently unreachable (by the time coverage is confirmed
    `SUBSTANTIAL`, both are already true). `business_conclusive`/
    `valuation_conclusive` are therefore the sole signal for both the
    `LOW` trigger below (neither has concluded anything yet -- real data
    exists but nothing concrete has been found in it) and the `HIGH`
    vs. `VERY_HIGH` split (exactly one concluded vs. both) -- restoring
    the same "one of business/valuation not yet conclusive stays HIGH"
    tier ATLAS-026 originally established, before this sprint's coverage
    rewiring nearly collapsed it.
    """
    if business_state is not EvaluationState.EVALUATED or valuation_state is not EvaluationState.EVALUATED:
        return ConvictionAssessment(
            level=ConvictionLevel.INSUFFICIENT_EVIDENCE,
            reasons=(ConvictionReasonCode.UPSTREAM_STAGE_NOT_EVALUATED,),
        )

    if analysis_coverage is AnalysisCoverageLevel.NO_COVERAGE:
        return ConvictionAssessment(
            level=ConvictionLevel.INSUFFICIENT_EVIDENCE,
            reasons=(ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,),
        )

    coverage_reason = (
        ConvictionReasonCode.EVIDENCE_COVERAGE_FULL
        if business_conclusive and valuation_conclusive
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
        or not (business_conclusive or valuation_conclusive)
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

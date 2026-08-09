"""Recommendation-Specific Atlas Conviction Level (`DE-004` §3;
"Recommendation Backend Step 2").

**A completely separate concept from `atlas.analysis_engine.conviction`'s
existing `ConvictionLevel`** (five levels: VERY_HIGH/HIGH/MODERATE/LOW/
INSUFFICIENT_EVIDENCE; already real, already shipped, already shown in
the Evidence section today). `DE-004` §3 defines a **distinct, three-level**
scale (High/Medium/Low) specific to a Recommendation's own Direction --
`DE-007` §11 already identified this as an ambiguity `DE-004` itself
leaves open and resolved it: the two scales are independently computed,
never merged, never presented under the same label, and never
interchangeable. This module is that independent computation. It does
not read, call, or import `atlas.analysis_engine.conviction` at all --
not because doing so would be technically wrong, but because the two
algorithms below are deliberately derived fresh from `DE-004` §3's own
three evidence patterns, not by re-deriving or narrowing the five-level
scale's own output.

**Inputs are restricted to exactly what `DE-004` names**: Business
Evaluation, Valuation, Portfolio Intelligence, and Reasoning -- the same
four stages `atlas.decision_engine.contracts.RequiredBeforeRecommendation`
already names as required before any recommendation. Deliberately
excluded: Financial/Valuation Risk (`atlas.analysis_engine.risk`) --
`DE-004` §3's own prose never mentions Risk in any of its three evidence
patterns, and Risk is not one of the four stages `DE-004` names; the
existing five-level `conviction.py` does read Risk, which is one more
reason the two computations are genuinely different, not a relabeling.

**Not yet consumed anywhere.** No stage, pipeline, or output contract
calls `calculate_recommendation_conviction` yet -- `atlas.analysis_engine
.recommendation.evaluate_recommendation_gate` is unchanged by this module
and continues to always return `RecommendationWithheld`, because no
Direction selector exists (see that module's own docstring). This module
exists on its own, ready for a future sprint that builds one.

The algorithm, derived directly from `DE-004` §3's own prose, using only
signals `atlas.decision_engine` and `atlas.analysis_engine` already
compute today:

    Business Evaluation EVALUATED
    AND Valuation EVALUATED
    AND Portfolio Intelligence EVALUATED
    AND Reasoning EVALUATED
    AND Evidence Coverage in (PARTIAL, FULL)
        -> otherwise: no assessment (DE-004 §4 -- precedes the scale)

    Evidence Coverage == PARTIAL
        -> LOW ("thin, mixed, or largely inferential" -- DE-004 §3)

    Evidence Coverage == FULL
    AND (Contradicting Evidence present OR Open Questions remain)
        -> MEDIUM ("meaningfully supports... but leaves real, specific
           open questions -- genuine Counter-Evidence... not fully
           resolved" -- DE-004 §3)

    Evidence Coverage == FULL
    AND no Contradicting Evidence
    AND no Open Questions
        -> HIGH ("extensive, consistent... Counter-Evidence, if any, is
           minor" -- DE-004 §3)

`business_conclusive`/`valuation_conclusive` (the extra distinction the
five-level scale uses to separate HIGH from VERY_HIGH) are deliberately
not read here -- `DE-004` §3's High pattern describes evidence
extensiveness, consistency, and the absence of meaningful Counter-Evidence,
never a conclusiveness requirement, and this scale has no fourth tier to
reserve for it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

__all__ = [
    "RecommendationConvictionLevel",
    "RecommendationConvictionReasonCode",
    "RecommendationConvictionAssessment",
    "calculate_recommendation_conviction",
]


class RecommendationConvictionLevel(str, Enum):
    """`DE-004` §3's Atlas Conviction Level -- exactly three values. No
    fourth member is ever added here: `DE-004` §4's "Recommendation
    Withheld" is not a value of this scale, it precedes it entirely
    (`calculate_recommendation_conviction` below returns `None`, never a
    fourth enum member, for that case)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationConvictionReasonCode(str, Enum):
    """Every reason that contributed to a Recommendation Conviction
    assessment -- `RecommendationConvictionAssessment.reasons` always
    names every applicable code, not only the single deciding one,
    mirroring `atlas.analysis_engine.conviction.ConvictionReasonCode`'s
    own "complete answer, not just the first match" discipline, applied
    fresh to this scale's own, narrower signal set."""

    EVIDENCE_COVERAGE_PARTIAL = "evidence_coverage_partial"
    EVIDENCE_COVERAGE_FULL = "evidence_coverage_full"
    CONTRADICTING_EVIDENCE_PRESENT = "contradicting_evidence_present"
    NO_CONTRADICTING_EVIDENCE = "no_contradicting_evidence"
    OPEN_QUESTIONS_REMAIN = "open_questions_remain"
    NO_OPEN_QUESTIONS = "no_open_questions"


@dataclass(frozen=True)
class RecommendationConvictionAssessment:
    """The two, and only two, outputs `calculate_recommendation_conviction`
    produces: `level` and `reasons`. Nothing else -- no timestamp, no
    identity, no Direction, no Execution Guidance field of any kind."""

    level: RecommendationConvictionLevel
    reasons: tuple[RecommendationConvictionReasonCode, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.level, RecommendationConvictionLevel):
            raise AnalysisEngineContractError(
                "RecommendationConvictionAssessment.level must be a "
                "RecommendationConvictionLevel -- never "
                "atlas.analysis_engine.conviction.ConvictionLevel or any "
                "other value (DE-004 §3 / DE-007 §11's disambiguation)."
            )
        if not self.reasons:
            raise AnalysisEngineContractError(
                "RecommendationConvictionAssessment.reasons must be "
                "non-empty -- every assessed level SHALL name the "
                "specific evidence pattern that produced it (DE-004 §3), "
                "never an unexplained category."
            )
        for reason in self.reasons:
            if not isinstance(reason, RecommendationConvictionReasonCode):
                raise AnalysisEngineContractError(
                    "RecommendationConvictionAssessment.reasons must "
                    "contain only RecommendationConvictionReasonCode "
                    "members."
                )


def calculate_recommendation_conviction(
    *,
    business_state: EvaluationState,
    valuation_state: EvaluationState,
    portfolio_intelligence_state: EvaluationState,
    reasoning_state: EvaluationState,
    evidence_coverage: EvidenceCoverageLevel,
    has_contradicting_evidence: bool,
    has_open_questions: bool,
) -> RecommendationConvictionAssessment | None:
    """Deterministic: identical inputs always produce an identical
    result (or identically `None`). No wall-clock read, no randomness,
    no partial credit.

    Returns `None` when the evidence does not support even Low
    conviction -- `DE-004` §4's own territory, which precedes this
    scale entirely rather than occupying its bottom. Every non-`None`
    return names every applicable reason, in the same fixed order,
    regardless of which one decided the level -- the same
    "trivially diffable" discipline `conviction.py`'s own
    `calculate_conviction` already established.
    """
    if (
        business_state is not EvaluationState.EVALUATED
        or valuation_state is not EvaluationState.EVALUATED
        or portfolio_intelligence_state is not EvaluationState.EVALUATED
        or reasoning_state is not EvaluationState.EVALUATED
    ):
        return None

    if evidence_coverage in (EvidenceCoverageLevel.NOT_APPLICABLE, EvidenceCoverageLevel.NONE):
        return None

    if evidence_coverage is EvidenceCoverageLevel.PARTIAL:
        return RecommendationConvictionAssessment(
            level=RecommendationConvictionLevel.LOW,
            reasons=(RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_PARTIAL,),
        )

    # From here: evidence_coverage is FULL.
    contradiction_reason = (
        RecommendationConvictionReasonCode.CONTRADICTING_EVIDENCE_PRESENT
        if has_contradicting_evidence
        else RecommendationConvictionReasonCode.NO_CONTRADICTING_EVIDENCE
    )
    open_questions_reason = (
        RecommendationConvictionReasonCode.OPEN_QUESTIONS_REMAIN
        if has_open_questions
        else RecommendationConvictionReasonCode.NO_OPEN_QUESTIONS
    )
    base_reasons = (
        RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_FULL,
        contradiction_reason,
        open_questions_reason,
    )

    if has_contradicting_evidence or has_open_questions:
        return RecommendationConvictionAssessment(level=RecommendationConvictionLevel.MEDIUM, reasons=base_reasons)

    return RecommendationConvictionAssessment(level=RecommendationConvictionLevel.HIGH, reasons=base_reasons)

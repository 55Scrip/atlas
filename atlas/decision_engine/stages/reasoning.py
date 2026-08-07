"""Reasoning stage (`DE-002`; Sprint 5).

Reasoning is an assembly layer, not a second evaluator: it consumes
only `BusinessEvaluationResult`, `ValuationResult`, and
`PortfolioIntelligenceResult` — never `DecisionEngineInput`, and never
raw Observation/Evidence/Decision/Outcome entities directly. Every
fact assembled here already existed, exactly as-is, in one of those
three upstream results; nothing is reinterpreted, rescored, or
newly classified, and no free-text statement content is ever
inspected.

Assembled under the Recommendation Withheld structural exception
(`DE-002` §4): Direction and Conviction are permanently absent — no
field for either exists anywhere in this module's output. Evidence and
Counter-Evidence are populated from Business Evaluation's own
`ObservationEvidenceClassification`s; Known Unknowns and Open Questions
carry the "why insufficient" content §4 requires; `what_would_change`
is always empty this sprint, per explicit lock — no upstream stage
exposes a distinct change-trigger concept, and none is derived or
synthesized here.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    ContradictionSummary,
    EvaluationState,
    EvidenceGapKind,
    KnownUnknownSummary,
    OpenQuestion,
    OpenQuestionKind,
    PortfolioContextSummary,
    PortfolioIntelligenceResult,
    ReasoningFinding,
    ReasoningResult,
    ReasoningSummary,
    SupportingEvidenceSummary,
    ValuationResult,
)


def _current_situation(
    business_evaluation: BusinessEvaluationResult,
    valuation: ValuationResult,
    portfolio_intelligence: PortfolioIntelligenceResult,
) -> ReasoningSummary:
    return ReasoningSummary(
        business_evaluation_state=business_evaluation.state,
        valuation_state=valuation.state,
        portfolio_intelligence_state=portfolio_intelligence.state,
        evidence_coverage=business_evaluation.evidence_quality.coverage,
        execution_price_history_coverage=valuation.execution_price_history.coverage,
        holding_linkage=portfolio_intelligence.holding_context.linkage,
    )


def _supporting_evidence(
    business_evaluation: BusinessEvaluationResult,
) -> SupportingEvidenceSummary:
    classifications = tuple(
        classification
        for classification in business_evaluation.evidence_quality.observation_classifications
        if classification.supporting_evidence_count > 0
    )
    return SupportingEvidenceSummary(observation_classifications=classifications)


def _contradicting_evidence(
    business_evaluation: BusinessEvaluationResult,
) -> ContradictionSummary:
    classifications = tuple(
        classification
        for classification in business_evaluation.evidence_quality.observation_classifications
        if classification.challenging_evidence_count > 0
    )
    return ContradictionSummary(observation_classifications=classifications)


def _known_unknowns(
    business_evaluation: BusinessEvaluationResult,
    valuation: ValuationResult,
    portfolio_intelligence: PortfolioIntelligenceResult,
) -> KnownUnknownSummary:
    return KnownUnknownSummary(
        evidence_gaps=business_evaluation.evidence_quality.evidence_gaps,
        durability_gap=business_evaluation.durability,
        valuation_gap=valuation.substantive_valuation,
        portfolio_factor_gaps=portfolio_intelligence.portfolio_factors.factors,
    )


def _portfolio_context(
    portfolio_intelligence: PortfolioIntelligenceResult,
) -> PortfolioContextSummary:
    return PortfolioContextSummary(holding_context=portfolio_intelligence.holding_context)


def _open_questions(known_unknowns: KnownUnknownSummary) -> tuple[OpenQuestion, ...]:
    """Deterministic 1:1 mapping from each already-known gap/finding to
    a machine-readable question — no free-form generation, no NLP."""
    questions: list[OpenQuestion] = []

    for gap in known_unknowns.evidence_gaps:
        if gap.kind is EvidenceGapKind.NO_EVIDENCE_RECORDED:
            questions.append(OpenQuestion(kind=OpenQuestionKind.NO_EVIDENCE_RECORDED_FOR_CASE))
        elif gap.kind is EvidenceGapKind.OBSERVATION_WITHOUT_EVIDENCE:
            questions.append(
                OpenQuestion(
                    kind=OpenQuestionKind.OBSERVATION_WITHOUT_EVIDENCE,
                    reference=gap.reference,
                )
            )
        elif gap.kind is EvidenceGapKind.DECISION_WITHOUT_LINKED_OBSERVATION:
            questions.append(
                OpenQuestion(
                    kind=OpenQuestionKind.DECISION_WITHOUT_LINKED_OBSERVATION,
                    reference=gap.reference,
                )
            )

    if known_unknowns.durability_gap is not None:
        questions.append(OpenQuestion(kind=OpenQuestionKind.BUSINESS_DURABILITY_NOT_ASSESSABLE))

    if known_unknowns.valuation_gap is not None:
        questions.append(OpenQuestion(kind=OpenQuestionKind.VALUATION_THESIS_NOT_DOCUMENTED))

    for factor in known_unknowns.portfolio_factor_gaps:
        questions.append(
            OpenQuestion(
                kind=OpenQuestionKind.PORTFOLIO_FACTOR_NOT_ASSESSABLE,
                reference=factor.value,
            )
        )

    return tuple(questions)


def evaluate_reasoning(
    *,
    business_evaluation: BusinessEvaluationResult,
    valuation: ValuationResult,
    portfolio_intelligence: PortfolioIntelligenceResult,
) -> ReasoningResult:
    """Always returns `EVALUATED`: assembling the audit trail from
    whatever the three upstream results already contain — including an
    audit trail that is mostly "not yet assessable" — is itself a real,
    deterministic, honest conclusion. Deterministic: identical upstream
    results always produce a deeply equal `ReasoningResult`, since every
    step here only filters or copies already-deterministic upstream
    tuples, never re-sorts by a new key or reads a wall clock.
    """
    known_unknowns = _known_unknowns(business_evaluation, valuation, portfolio_intelligence)
    finding = ReasoningFinding(
        current_situation=_current_situation(
            business_evaluation, valuation, portfolio_intelligence
        ),
        supporting_evidence=_supporting_evidence(business_evaluation),
        contradicting_evidence=_contradicting_evidence(business_evaluation),
        known_unknowns=known_unknowns,
        portfolio_context=_portfolio_context(portfolio_intelligence),
        open_questions=_open_questions(known_unknowns),
        what_would_change=(),
    )
    return ReasoningResult(state=EvaluationState.EVALUATED, blocked_by=(), finding=finding)

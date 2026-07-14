"""DecisionTimelineQuery — assembles a DecisionTimeline (ATLAS-004).

Depends only on repository interfaces, never on a SQLAlchemy Engine or
any concrete persistence detail — composition.py is the only place in
this module aware of an Engine. This mirrors the domain/application vs.
infrastructure separation already used everywhere else in this codebase,
and is what makes this query independently testable against fakes and
reusable by a future coaching/analytics capability without modification.

Never calls .add(...) on any repository — Timeline never owns Decisions,
Outcomes, Evaluations, or Learnings, it only reads them.
"""
from __future__ import annotations

from atlas.core.application.decision_timeline.timeline import (
    DecisionReviewChain,
    DecisionTimeline,
    DecisionTimelineEntry,
    EvaluationWithLearnings,
)
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evaluation.repository import EvaluationRepository
from atlas.core.domain.learning.repository import LearningRepository
from atlas.core.domain.outcome.repository import OutcomeRepository


class DecisionTimelineQuery:
    def __init__(
        self,
        decision_repository: DecisionRepository,
        outcome_repository: OutcomeRepository,
        evaluation_repository: EvaluationRepository,
        learning_repository: LearningRepository,
    ) -> None:
        self._decisions = decision_repository
        self._outcomes = outcome_repository
        self._evaluations = evaluation_repository
        self._learnings = learning_repository

    def build(self) -> DecisionTimeline:
        entries = tuple(
            self._build_entry(decision) for decision in self._decisions.list_all()
        )
        ordered = sorted(
            entries, key=lambda entry: (entry.decision.decided_at, entry.decision.id.value)
        )
        return DecisionTimeline(entries=tuple(ordered))

    def _build_entry(self, decision) -> DecisionTimelineEntry:
        outcomes = sorted(
            self._outcomes.list_by_decision_id(decision.id),
            key=lambda outcome: (outcome.recorded_at, outcome.id.value),
        )
        review_chains = tuple(self._build_review_chain(outcome) for outcome in outcomes)
        return DecisionTimelineEntry(decision=decision, review_chains=review_chains)

    def _build_review_chain(self, outcome) -> DecisionReviewChain:
        evaluations = sorted(
            self._evaluations.list_by_outcome_id(outcome.id),
            key=lambda evaluation: (evaluation.recorded_at, evaluation.id.value),
        )
        evaluations_with_learnings = tuple(
            self._build_evaluation_with_learnings(evaluation) for evaluation in evaluations
        )
        return DecisionReviewChain(outcome=outcome, evaluations=evaluations_with_learnings)

    def _build_evaluation_with_learnings(self, evaluation) -> EvaluationWithLearnings:
        learnings = sorted(
            self._learnings.list_by_evaluation_id(evaluation.id),
            key=lambda learning: (learning.recorded_at, learning.id.value),
        )
        return EvaluationWithLearnings(evaluation=evaluation, learnings=tuple(learnings))

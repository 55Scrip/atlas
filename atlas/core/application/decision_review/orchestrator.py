"""DecisionReviewOrchestrator — the application boundary for Decision
Review (ATLAS-003).

Review orchestration owns session state, Decision lookup/selection,
which question to ask next, and elicitation. The three existing,
unmodified Core Loop services (Outcome, Evaluation, Learning) remain the
sole owners of domain creation, validation, and reasoning records. This
orchestrator may list and read Decisions but never writes to
DecisionRepository — the only repository this increment reads without
also being permitted to write to. It copies the person's own words into
Evaluation's statement verbatim: Atlas never evaluates the investor, it
records the investor's own reflection.

Each review always produces exactly one full, fresh Outcome ->
Evaluation -> Learning triple. See session.py's module docstring for the
explicit, accepted limitation this implies for interrupted reviews.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.application.decision_review import prompts
from atlas.core.application.decision_review.lookup import (
    list_decisions_for_selection,
    select_decision,
)
from atlas.core.application.decision_review.session import (
    DecisionReviewSession,
    DecisionReviewStep,
)
from atlas.core.application.evaluation.capture_evaluation import (
    CaptureEvaluationRequest,
    EvaluationService,
)
from atlas.core.application.learning.capture_learning import (
    CaptureLearningRequest,
    LearningService,
)
from atlas.core.application.outcome.capture_outcome import CaptureOutcomeRequest, OutcomeService
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ReviewTurn:
    prompt: str
    is_complete: bool


class DecisionReviewOrchestrator:
    def __init__(
        self,
        decision_repository: DecisionRepository,
        outcome_service: OutcomeService,
        evaluation_service: EvaluationService,
        learning_service: LearningService,
    ) -> None:
        self._decisions = decision_repository
        self._outcome_service = outcome_service
        self._evaluation_service = evaluation_service
        self._learning_service = learning_service

    def list_decisions(self) -> list[tuple[int, Decision]]:
        """Pure read against DecisionRepository — never a write."""
        return list_decisions_for_selection(self._decisions)

    def select(
        self, numbered_decisions: list[tuple[int, Decision]], answer: str
    ) -> DecisionReviewSession | None:
        """Resolve a selection answer to a fresh DecisionReviewSession.

        Returns None if the answer doesn't match a listed decision, so
        the caller can re-ask instead of guessing.
        """
        decision = select_decision(numbered_decisions, answer)
        if decision is None:
            return None
        return DecisionReviewSession(decision_id=decision.id.value)

    def respond(self, session: DecisionReviewSession, answer: str) -> ReviewTurn:
        handler = self._HANDLERS[session.current_step]
        return handler(self, session, answer)

    def _handle_outcome(self, session: DecisionReviewSession, answer: str) -> ReviewTurn:
        try:
            outcome = self._outcome_service.capture(
                CaptureOutcomeRequest(
                    decision_id=session.decision_id, statement=answer, occurred_at=_now()
                )
            )
        except Exception:
            return ReviewTurn(prompt=prompts.OUTCOME_PROMPT, is_complete=False)
        session.outcome_id = outcome.id.value
        session.current_step = DecisionReviewStep.EVALUATION
        return ReviewTurn(prompt=prompts.EVALUATION_PROMPT, is_complete=False)

    def _handle_evaluation(self, session: DecisionReviewSession, answer: str) -> ReviewTurn:
        try:
            evaluation = self._evaluation_service.capture(
                CaptureEvaluationRequest(
                    outcome_id=session.outcome_id, statement=answer, evaluated_at=_now()
                )
            )
        except Exception:
            return ReviewTurn(prompt=prompts.EVALUATION_PROMPT, is_complete=False)
        session.evaluation_id = evaluation.id.value
        session.current_step = DecisionReviewStep.LEARNING
        return ReviewTurn(prompt=prompts.LEARNING_PROMPT, is_complete=False)

    def _handle_learning(self, session: DecisionReviewSession, answer: str) -> ReviewTurn:
        try:
            learning = self._learning_service.capture(
                CaptureLearningRequest(
                    evaluation_id=session.evaluation_id, statement=answer, learned_at=_now()
                )
            )
        except Exception:
            return ReviewTurn(prompt=prompts.LEARNING_PROMPT, is_complete=False)
        session.learning_id = learning.id.value
        session.current_step = DecisionReviewStep.REVIEW_RECORDED
        return ReviewTurn(prompt=prompts.CLOSING_MESSAGE, is_complete=True)

    _HANDLERS = {
        DecisionReviewStep.OUTCOME: _handle_outcome,
        DecisionReviewStep.EVALUATION: _handle_evaluation,
        DecisionReviewStep.LEARNING: _handle_learning,
    }

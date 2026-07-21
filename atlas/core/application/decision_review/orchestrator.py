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
from atlas.core.application.judgment.capture_judgment import (
    CaptureJudgmentRequest,
    JudgmentService,
)
from atlas.core.application.learning.capture_learning import (
    CaptureLearningRequest,
    LearningService,
)
from atlas.core.application.outcome.capture_outcome import CaptureOutcomeRequest, OutcomeService
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference


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
        judgment_service: JudgmentService,
    ) -> None:
        self._decisions = decision_repository
        self._outcome_service = outcome_service
        self._evaluation_service = evaluation_service
        self._learning_service = learning_service
        self._judgment_service = judgment_service

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

        # The review is now permanently recorded, and the session has
        # already reached its terminal step — REVIEW_RECORDED has no
        # entry in _HANDLERS, so nothing below this point can cause
        # `respond()` to invoke Outcome, Evaluation, or Learning capture
        # again. The Judgment capture below is therefore a second,
        # independent write in its own try/except, never sharing any of
        # those three steps' own retry/reprompt boundaries: a failure
        # here can surface as a different closing message, but can
        # never retry, duplicate, or roll back any of the three
        # already-committed legacy/canonical writes above
        # (Evaluation-to-Judgment-Reduction-Design.md, Sections 17-18,
        # 23, Package M2). This is an additive canonical fact
        # characterizing the Outcome, not a replacement for Outcome,
        # Evaluation, or Learning. The semantic content of this
        # characterization was already fully settled the moment
        # Evaluation was captured, above — Learning's own success is
        # only the operationally safe boundary after which this write
        # is attempted; Learning's own content contributes nothing to
        # the Judgment.
        try:
            evaluation = self._evaluation_service.get(EvaluationId(session.evaluation_id))
            outcome = self._outcome_service.get(OutcomeId(evaluation.outcome_id.value))
            self._judgment_service.capture(
                CaptureJudgmentRequest(
                    case_id=outcome.case_id.value,
                    characterization=evaluation.statement.value,
                    subject=TypedDomainObjectReference(
                        target_type=DomainObjectType.OUTCOME,
                        target_id=evaluation.outcome_id.value,
                    ),
                )
            )
        except Exception:
            return ReviewTurn(prompt=prompts.CLOSING_MESSAGE_JUDGMENT_FAILED, is_complete=True)
        return ReviewTurn(prompt=prompts.CLOSING_MESSAGE, is_complete=True)

    _HANDLERS = {
        DecisionReviewStep.OUTCOME: _handle_outcome,
        DecisionReviewStep.EVALUATION: _handle_evaluation,
        DecisionReviewStep.LEARNING: _handle_learning,
    }

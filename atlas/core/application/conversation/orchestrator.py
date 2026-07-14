"""ConversationOrchestrator — the application boundary for the First
Decision Conversation (ATLAS-002).

Conversation owns session state, which question to ask next, and
elicitation. The seven existing, unmodified Core Loop services remain the
sole owners of domain creation, validation, and reasoning records. This
orchestrator never constructs a domain entity itself, never decides
whether something supports or challenges anything on its own (that word
always comes from the person, only translated literally via
prompts.parse_direction), and never forms a hypothesis, conclusion, or
decision — the person supplies every one of those in their own words.

The conversation covers exactly Question through Decision. It does not
ask about, infer, or fabricate an Outcome, Evaluation, or Learning — its
terminal state after Decision is a hard stop, not a soft pause. See
docs/FirstDecisionConversationATLAS002.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.application.conclusion.capture_conclusion import (
    CaptureConclusionRequest,
    ConclusionService,
)
from atlas.core.application.conversation import prompts
from atlas.core.application.conversation.session import ConversationSession, ConversationStep
from atlas.core.application.interpretation.capture_interpretation import (
    CaptureInterpretationRequest,
    InterpretationService,
)
from atlas.core.application.question.capture_question import (
    CaptureQuestionRequest,
    QuestionService,
)
from atlas.core.application.reasoning_link.capture_evidence_from_hypothesis import (
    CaptureEvidenceFromHypothesisRequest,
    CaptureEvidenceFromHypothesisService,
)
from atlas.core.application.reasoning_link.commit_decision_from_conclusion import (
    CommitDecisionFromConclusionRequest,
    CommitDecisionFromConclusionService,
)
from atlas.core.application.reasoning_link.form_hypothesis_from_interpretation import (
    FormHypothesisFromInterpretationRequest,
    FormHypothesisFromInterpretationService,
)
from atlas.core.application.reasoning_link.observe_from_question import (
    ObserveFromQuestionRequest,
    ObserveFromQuestionService,
)
from atlas.core.domain.decision.value_objects import UserId


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ConversationTurn:
    prompt: str
    is_complete: bool


class ConversationOrchestrator:
    def __init__(
        self,
        question_service: QuestionService,
        observe_from_question_service: ObserveFromQuestionService,
        interpretation_service: InterpretationService,
        form_hypothesis_service: FormHypothesisFromInterpretationService,
        capture_evidence_service: CaptureEvidenceFromHypothesisService,
        conclusion_service: ConclusionService,
        commit_decision_service: CommitDecisionFromConclusionService,
        investor_id: UserId,
    ) -> None:
        self._question_service = question_service
        self._observe_from_question_service = observe_from_question_service
        self._interpretation_service = interpretation_service
        self._form_hypothesis_service = form_hypothesis_service
        self._capture_evidence_service = capture_evidence_service
        self._conclusion_service = conclusion_service
        self._commit_decision_service = commit_decision_service
        self._investor_id = investor_id

    def start(self) -> ConversationSession:
        return ConversationSession()

    def respond(self, session: ConversationSession, answer: str) -> ConversationTurn:
        handler = self._HANDLERS[session.current_step]
        return handler(self, session, answer)

    def _handle_question(self, session: ConversationSession, answer: str) -> ConversationTurn:
        try:
            question = self._question_service.capture(
                CaptureQuestionRequest(statement=answer, raised_at=_now())
            )
        except Exception:
            return ConversationTurn(prompt=prompts.QUESTION_PROMPT, is_complete=False)
        session.question_id = question.id.value
        session.current_step = ConversationStep.OBSERVATION
        return ConversationTurn(prompt=prompts.OBSERVATION_SUBJECT_PROMPT, is_complete=False)

    def _handle_observation(self, session: ConversationSession, answer: str) -> ConversationTurn:
        if "subject" not in session.pending:
            session.pending["subject"] = answer
            return ConversationTurn(
                prompt=prompts.OBSERVATION_STATEMENT_PROMPT, is_complete=False
            )
        subject = session.pending["subject"]
        try:
            result = self._observe_from_question_service.observe(
                ObserveFromQuestionRequest(
                    question_id=session.question_id,
                    subject=subject,
                    statement=answer,
                    observed_at=_now(),
                )
            )
        except Exception:
            return ConversationTurn(
                prompt=prompts.OBSERVATION_STATEMENT_PROMPT, is_complete=False
            )
        session.pending.clear()
        session.observation_id = result.observation.id.value
        session.observation_subject = subject
        session.current_step = ConversationStep.INTERPRETATION
        return ConversationTurn(prompt=prompts.INTERPRETATION_PROMPT, is_complete=False)

    def _handle_interpretation(
        self, session: ConversationSession, answer: str
    ) -> ConversationTurn:
        try:
            interpretation = self._interpretation_service.capture(
                CaptureInterpretationRequest(
                    observation_id=session.observation_id,
                    statement=answer,
                    interpreted_at=_now(),
                )
            )
        except Exception:
            return ConversationTurn(prompt=prompts.INTERPRETATION_PROMPT, is_complete=False)
        session.interpretation_id = interpretation.id.value
        session.current_step = ConversationStep.HYPOTHESIS
        return ConversationTurn(prompt=prompts.HYPOTHESIS_PROMPT, is_complete=False)

    def _handle_hypothesis(self, session: ConversationSession, answer: str) -> ConversationTurn:
        try:
            result = self._form_hypothesis_service.form(
                FormHypothesisFromInterpretationRequest(
                    interpretation_id=session.interpretation_id,
                    statement=answer,
                    formulated_at=_now(),
                )
            )
        except Exception:
            return ConversationTurn(prompt=prompts.HYPOTHESIS_PROMPT, is_complete=False)
        session.hypothesis_id = result.hypothesis.id.value
        session.current_step = ConversationStep.EVIDENCE
        return ConversationTurn(prompt=prompts.EVIDENCE_STATEMENT_PROMPT, is_complete=False)

    def _handle_evidence(self, session: ConversationSession, answer: str) -> ConversationTurn:
        if "statement" not in session.pending:
            session.pending["statement"] = answer
            return ConversationTurn(prompt=prompts.EVIDENCE_DIRECTION_PROMPT, is_complete=False)
        direction = prompts.parse_direction(answer)
        if direction is None:
            return ConversationTurn(
                prompt=prompts.UNRECOGNIZED_DIRECTION_PROMPT, is_complete=False
            )
        statement = session.pending["statement"]
        try:
            result = self._capture_evidence_service.capture(
                CaptureEvidenceFromHypothesisRequest(
                    hypothesis_id=session.hypothesis_id,
                    statement=statement,
                    direction=direction,
                    observed_at=_now(),
                )
            )
        except Exception:
            return ConversationTurn(prompt=prompts.EVIDENCE_DIRECTION_PROMPT, is_complete=False)
        session.pending.clear()
        session.evidence_id = result.evidence.id.value
        session.current_step = ConversationStep.CONCLUSION
        return ConversationTurn(prompt=prompts.CONCLUSION_PROMPT, is_complete=False)

    def _handle_conclusion(self, session: ConversationSession, answer: str) -> ConversationTurn:
        try:
            conclusion = self._conclusion_service.capture(
                CaptureConclusionRequest(
                    evidence_id=session.evidence_id,
                    statement=answer,
                    concluded_at=_now(),
                )
            )
        except Exception:
            return ConversationTurn(prompt=prompts.CONCLUSION_PROMPT, is_complete=False)
        session.conclusion_id = conclusion.id.value
        session.conclusion_statement = answer
        session.current_step = ConversationStep.DECISION
        return ConversationTurn(prompt=prompts.DECISION_TYPE_PROMPT, is_complete=False)

    def _handle_decision(self, session: ConversationSession, answer: str) -> ConversationTurn:
        if "decision_type" not in session.pending:
            decision_type = prompts.parse_decision_type(answer)
            if decision_type is None:
                return ConversationTurn(
                    prompt=prompts.UNRECOGNIZED_DECISION_TYPE_PROMPT, is_complete=False
                )
            session.pending["decision_type"] = decision_type
            return ConversationTurn(
                prompt=prompts.DECISION_CONFIDENCE_PROMPT, is_complete=False
            )
        confidence = prompts.parse_confidence(answer)
        if confidence is None:
            return ConversationTurn(
                prompt=prompts.DECISION_CONFIDENCE_PROMPT, is_complete=False
            )
        decision_type = session.pending["decision_type"]
        try:
            result = self._commit_decision_service.commit(
                CommitDecisionFromConclusionRequest(
                    conclusion_id=session.conclusion_id,
                    user_id=self._investor_id.value,
                    decision_type=decision_type,
                    subject=session.observation_subject,
                    reason=session.conclusion_statement,
                    confidence=confidence,
                    decided_at=_now(),
                )
            )
        except Exception:
            return ConversationTurn(
                prompt=prompts.DECISION_CONFIDENCE_PROMPT, is_complete=False
            )
        session.pending.clear()
        session.decision_id = result.decision.id.value
        session.current_step = ConversationStep.DECISION_RECORDED
        return ConversationTurn(prompt=prompts.CLOSING_MESSAGE, is_complete=True)

    _HANDLERS = {
        ConversationStep.QUESTION: _handle_question,
        ConversationStep.OBSERVATION: _handle_observation,
        ConversationStep.INTERPRETATION: _handle_interpretation,
        ConversationStep.HYPOTHESIS: _handle_hypothesis,
        ConversationStep.EVIDENCE: _handle_evidence,
        ConversationStep.CONCLUSION: _handle_conclusion,
        ConversationStep.DECISION: _handle_decision,
    }

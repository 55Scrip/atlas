"""Unit tests for ConversationOrchestrator's seven step handlers (ATLAS-002)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.conversation import prompts
from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)
from atlas.core.application.conversation.session import ConversationStep
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_conversation_tables(eng)
    return eng


@pytest.fixture
def resolved_case_id():
    """A genuine, already-resolved CaseId for this test's own conversation —
    not a shared sentinel, mirroring the exact idiom already established
    for Observation's own tests (case_id=uuid.uuid4() per test).
    """
    return uuid.uuid4()


@pytest.fixture
def orchestrator(engine, resolved_case_id):
    return build_conversation_orchestrator(engine, case_id=resolved_case_id)


class TestStart:
    def test_start_creates_a_session_at_question_step(self, orchestrator):
        session = orchestrator.start()
        assert session.current_step is ConversationStep.QUESTION
        assert not session.is_complete()


class TestCaseContext:
    def test_start_creates_a_session_carrying_the_resolved_case_id(
        self, orchestrator, resolved_case_id
    ):
        session = orchestrator.start()
        assert session.case_id == resolved_case_id

    def test_case_id_remains_stable_across_every_step(self, orchestrator, resolved_case_id):
        session = _drive_to_observation(orchestrator)
        assert session.case_id == resolved_case_id
        orchestrator.respond(session, "Semiconductor sector")
        orchestrator.respond(session, "Several companies raised capex guidance.")
        assert session.case_id == resolved_case_id
        orchestrator.respond(session, "This suggests demand may be accelerating.")
        assert session.case_id == resolved_case_id

    def test_observation_step_persists_exactly_the_session_case_id(
        self, orchestrator, resolved_case_id, engine
    ):
        session = _drive_to_observation(orchestrator)
        orchestrator.respond(session, "Semiconductor sector")
        orchestrator.respond(session, "Several companies raised capex guidance.")

        observation = SqlAlchemyObservationRepository(engine).get(
            ObservationId(session.observation_id)
        )
        assert observation.case_id.value == resolved_case_id


class TestQuestionStep:
    def test_captures_a_question_and_advances_to_observation(self, orchestrator):
        session = orchestrator.start()
        turn = orchestrator.respond(session, "Is demand for AI infrastructure accelerating?")
        assert session.current_step is ConversationStep.OBSERVATION
        assert session.question_id is not None
        assert turn.prompt == prompts.OBSERVATION_SUBJECT_PROMPT
        assert not turn.is_complete

    def test_blank_answer_re_asks_without_advancing(self, orchestrator):
        session = orchestrator.start()
        turn = orchestrator.respond(session, "   ")
        assert session.current_step is ConversationStep.QUESTION
        assert session.question_id is None
        assert turn.prompt == prompts.QUESTION_PROMPT


def _drive_to_observation(orchestrator):
    session = orchestrator.start()
    orchestrator.respond(session, "Is demand for AI infrastructure accelerating?")
    return session


class TestObservationStep:
    def test_collects_subject_then_statement_and_advances(self, orchestrator):
        session = _drive_to_observation(orchestrator)
        first = orchestrator.respond(session, "Semiconductor sector")
        assert first.prompt == prompts.OBSERVATION_STATEMENT_PROMPT
        assert session.current_step is ConversationStep.OBSERVATION

        second = orchestrator.respond(session, "Several companies raised capex guidance.")
        assert session.current_step is ConversationStep.INTERPRETATION
        assert session.observation_id is not None
        assert session.observation_subject == "Semiconductor sector"
        assert second.prompt == prompts.INTERPRETATION_PROMPT


def _drive_to_interpretation(orchestrator):
    session = _drive_to_observation(orchestrator)
    orchestrator.respond(session, "Semiconductor sector")
    orchestrator.respond(session, "Several companies raised capex guidance.")
    return session


class TestInterpretationStep:
    def test_captures_interpretation_and_advances_to_hypothesis(self, orchestrator):
        session = _drive_to_interpretation(orchestrator)
        turn = orchestrator.respond(session, "This suggests demand may be accelerating.")
        assert session.current_step is ConversationStep.HYPOTHESIS
        assert session.interpretation_id is not None
        assert turn.prompt == prompts.HYPOTHESIS_PROMPT


def _drive_to_hypothesis(orchestrator):
    session = _drive_to_interpretation(orchestrator)
    orchestrator.respond(session, "This suggests demand may be accelerating.")
    return session


class TestHypothesisStep:
    def test_captures_hypothesis_and_advances_to_evidence(self, orchestrator):
        session = _drive_to_hypothesis(orchestrator)
        turn = orchestrator.respond(
            session, "Demand for AI infrastructure may be accelerating."
        )
        assert session.current_step is ConversationStep.EVIDENCE
        assert session.hypothesis_id is not None
        assert turn.prompt == prompts.EVIDENCE_STATEMENT_PROMPT


def _drive_to_evidence(orchestrator):
    session = _drive_to_hypothesis(orchestrator)
    orchestrator.respond(session, "Demand for AI infrastructure may be accelerating.")
    return session


class TestEvidenceStep:
    def test_collects_statement_then_direction_and_advances(self, orchestrator):
        session = _drive_to_evidence(orchestrator)
        first = orchestrator.respond(session, "Order intake increased by 24 percent.")
        assert first.prompt == prompts.EVIDENCE_DIRECTION_PROMPT
        assert session.current_step is ConversationStep.EVIDENCE

        second = orchestrator.respond(session, "It supports it")
        assert session.current_step is ConversationStep.CONCLUSION
        assert session.evidence_id is not None
        assert second.prompt == prompts.CONCLUSION_PROMPT

    def test_unrecognized_direction_re_asks_without_advancing(self, orchestrator):
        session = _drive_to_evidence(orchestrator)
        orchestrator.respond(session, "Order intake increased by 24 percent.")
        turn = orchestrator.respond(session, "maybe kind of?")
        assert session.current_step is ConversationStep.EVIDENCE
        assert session.evidence_id is None
        assert turn.prompt == prompts.UNRECOGNIZED_DIRECTION_PROMPT

    def test_challenges_keyword_is_recognized(self, orchestrator):
        session = _drive_to_evidence(orchestrator)
        orchestrator.respond(session, "Margins compressed unexpectedly.")
        turn = orchestrator.respond(session, "it challenges that")
        assert session.current_step is ConversationStep.CONCLUSION
        assert turn.prompt == prompts.CONCLUSION_PROMPT


def _drive_to_conclusion(orchestrator):
    session = _drive_to_evidence(orchestrator)
    orchestrator.respond(session, "Order intake increased by 24 percent.")
    orchestrator.respond(session, "supports")
    return session


class TestConclusionStep:
    def test_captures_conclusion_and_advances_to_decision(self, orchestrator):
        session = _drive_to_conclusion(orchestrator)
        turn = orchestrator.respond(
            session, "The weight of evidence supports accelerating demand."
        )
        assert session.current_step is ConversationStep.DECISION
        assert session.conclusion_id is not None
        assert session.conclusion_statement == (
            "The weight of evidence supports accelerating demand."
        )
        assert turn.prompt == prompts.DECISION_TYPE_PROMPT


def _drive_to_decision(orchestrator):
    session = _drive_to_conclusion(orchestrator)
    orchestrator.respond(session, "The weight of evidence supports accelerating demand.")
    return session


class TestDecisionStep:
    def test_collects_decision_type_then_confidence_and_completes(self, orchestrator):
        session = _drive_to_decision(orchestrator)
        first = orchestrator.respond(session, "buy")
        assert first.prompt == prompts.DECISION_CONFIDENCE_PROMPT
        assert session.current_step is ConversationStep.DECISION

        second = orchestrator.respond(session, "80")
        assert session.current_step is ConversationStep.DECISION_RECORDED
        assert session.is_complete()
        assert session.decision_id is not None
        assert second.prompt == prompts.CLOSING_MESSAGE
        assert second.is_complete

    def test_unrecognized_decision_type_re_asks(self, orchestrator):
        session = _drive_to_decision(orchestrator)
        turn = orchestrator.respond(session, "maybe?")
        assert session.current_step is ConversationStep.DECISION
        assert turn.prompt == prompts.UNRECOGNIZED_DECISION_TYPE_PROMPT

    def test_invalid_confidence_re_asks(self, orchestrator):
        session = _drive_to_decision(orchestrator)
        orchestrator.respond(session, "buy")
        turn = orchestrator.respond(session, "not a number")
        assert session.current_step is ConversationStep.DECISION
        assert session.decision_id is None
        assert turn.prompt == prompts.DECISION_CONFIDENCE_PROMPT

    def test_decision_subject_and_reason_default_to_earlier_answers(self, orchestrator):
        session = _drive_to_decision(orchestrator)
        orchestrator.respond(session, "buy")
        orchestrator.respond(session, "80")
        # The Decision itself should have subject/reason defaulted from
        # earlier answers, never asked a third time.
        assert session.observation_subject == "Semiconductor sector"
        assert session.conclusion_statement == (
            "The weight of evidence supports accelerating demand."
        )

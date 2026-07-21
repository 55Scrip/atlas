"""Tests for Reasoning Trace capture at Decision commitment (Package M1,
Legacy-Core-Loop-Canonical-Reconciliation-Investigation.md, Section 21).

Covers exactly what the package requires: success-path integration,
ordering relative to Decision success, the failure boundary (Reasoning
Trace capture failing must never retry or duplicate the already-committed
Decision), at-most-once behavior, exact-identity propagation of the
conversation's own Observation, and composition wiring. Uses the same
in-memory-SQLite fixture idiom already established by
test_orchestrator.py — never the real on-disk database.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.core.application.conversation import prompts
from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)
from atlas.core.application.conversation.session import ConversationStep
from atlas.core.application.reasoning_trace.capture_reasoning_trace import ReasoningTraceService
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.infrastructure.persistence.decision.table import decisions_table
from atlas.core.infrastructure.persistence.reasoning_trace.table import (
    reasoning_trace_supports_table,
    reasoning_traces_table,
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
    return uuid.uuid4()


@pytest.fixture
def orchestrator(engine, resolved_case_id):
    return build_conversation_orchestrator(engine, case_id=resolved_case_id)


def _decision_row_count(engine) -> int:
    with engine.connect() as connection:
        return len(connection.execute(select(decisions_table)).fetchall())


def _reasoning_trace_rows(engine):
    with engine.connect() as connection:
        traces = connection.execute(select(reasoning_traces_table)).fetchall()
        supports = connection.execute(select(reasoning_trace_supports_table)).fetchall()
    return traces, supports


def _drive_to_decision_confidence_prompt(orchestrator):
    """Walks a full conversation up to, but not including, the final
    confidence answer that triggers Decision commitment. Returns the
    session, positioned so the caller supplies only the last answer.
    """
    session = orchestrator.start()
    orchestrator.respond(session, "Is demand for AI infrastructure accelerating?")
    orchestrator.respond(session, "Semiconductor sector")
    orchestrator.respond(session, "Several companies raised capex guidance.")
    orchestrator.respond(session, "This suggests demand may be accelerating.")
    orchestrator.respond(session, "Demand for AI infrastructure may be accelerating.")
    orchestrator.respond(session, "Order intake increased by 24 percent.")
    orchestrator.respond(session, "supports")
    orchestrator.respond(session, "The weight of evidence supports accelerating demand.")
    orchestrator.respond(session, "buy")
    return session


class _FailingReasoningTraceService:
    """A fake standing in for ReasoningTraceService that always raises,
    counting how many times capture() is attempted.
    """

    def __init__(self) -> None:
        self.capture_calls = 0

    def capture(self, request):
        self.capture_calls += 1
        raise RuntimeError("simulated Reasoning Trace capture failure")


class TestSuccessfulLiveIntegration:
    def test_exactly_one_reasoning_trace_captured_after_decision(
        self, orchestrator, engine, resolved_case_id
    ):
        session = _drive_to_decision_confidence_prompt(orchestrator)
        turn = orchestrator.respond(session, "80")

        assert turn.prompt == prompts.CLOSING_MESSAGE
        assert turn.is_complete
        assert session.current_step is ConversationStep.DECISION_RECORDED
        assert session.decision_id is not None
        assert session.observation_id is not None

        traces, supports = _reasoning_trace_rows(engine)
        assert len(traces) == 1
        assert traces[0][1] == str(resolved_case_id)
        assert len(supports) == 1

    def test_support_set_contains_exactly_the_observation_reference(
        self, orchestrator, engine
    ):
        session = _drive_to_decision_confidence_prompt(orchestrator)
        orchestrator.respond(session, "80")

        _, supports = _reasoning_trace_rows(engine)
        assert len(supports) == 1
        support_row = supports[0]
        # (support_id, reasoning_trace_id, target_type, target_id)
        assert support_row[2] == DomainObjectType.OBSERVATION.value
        assert support_row[3] == str(session.observation_id)

    def test_legacy_conversation_flow_still_completes_normally(self, orchestrator):
        session = _drive_to_decision_confidence_prompt(orchestrator)
        turn = orchestrator.respond(session, "80")
        assert session.is_complete()
        assert turn.is_complete
        # Legacy identities untouched by this package.
        assert session.question_id is not None
        assert session.interpretation_id is not None
        assert session.hypothesis_id is not None
        assert session.evidence_id is not None
        assert session.conclusion_id is not None


class TestOrdering:
    def test_no_reasoning_trace_exists_before_decision_succeeds(self, orchestrator, engine):
        session = orchestrator.start()
        orchestrator.respond(session, "Is demand for AI infrastructure accelerating?")
        orchestrator.respond(session, "Semiconductor sector")
        orchestrator.respond(session, "Several companies raised capex guidance.")
        # Decision has not been reached yet.
        traces, _ = _reasoning_trace_rows(engine)
        assert traces == []

    def test_decision_committed_even_if_reasoning_trace_capture_fails(
        self, orchestrator, engine
    ):
        orchestrator._reasoning_trace_service = _FailingReasoningTraceService()
        session = _drive_to_decision_confidence_prompt(orchestrator)
        turn = orchestrator.respond(session, "80")

        assert session.decision_id is not None
        assert session.current_step is ConversationStep.DECISION_RECORDED
        assert _decision_row_count(engine) == 1
        assert turn.prompt == prompts.CLOSING_MESSAGE_REASONING_TRACE_FAILED
        assert turn.is_complete


class TestFailureBoundary:
    def test_failure_is_surfaced_and_no_trace_persisted(self, orchestrator, engine):
        fake_service = _FailingReasoningTraceService()
        orchestrator._reasoning_trace_service = fake_service

        session = _drive_to_decision_confidence_prompt(orchestrator)
        turn = orchestrator.respond(session, "80")

        assert fake_service.capture_calls == 1
        assert turn.prompt == prompts.CLOSING_MESSAGE_REASONING_TRACE_FAILED
        traces, supports = _reasoning_trace_rows(engine)
        assert traces == []
        assert supports == []

    def test_decision_capture_called_exactly_once_despite_trace_failure(
        self, orchestrator, engine
    ):
        orchestrator._reasoning_trace_service = _FailingReasoningTraceService()
        session = _drive_to_decision_confidence_prompt(orchestrator)
        orchestrator.respond(session, "80")
        assert _decision_row_count(engine) == 1

    def test_no_retry_or_reprompt_path_exists_after_trace_failure(self, orchestrator):
        orchestrator._reasoning_trace_service = _FailingReasoningTraceService()
        session = _drive_to_decision_confidence_prompt(orchestrator)
        orchestrator.respond(session, "80")

        # The session is terminal; DECISION_RECORDED has no handler, so
        # no code path can re-invoke _handle_decision (and therefore
        # commit_decision_service) again.
        with pytest.raises(KeyError):
            orchestrator.respond(session, "anything")


class TestAtMostOnce:
    def test_successful_decision_step_creates_exactly_one_trace(self, orchestrator, engine):
        session = _drive_to_decision_confidence_prompt(orchestrator)
        orchestrator.respond(session, "80")
        traces, _ = _reasoning_trace_rows(engine)
        assert len(traces) == 1

    def test_reentering_after_terminal_state_does_not_create_another_trace(
        self, orchestrator, engine
    ):
        session = _drive_to_decision_confidence_prompt(orchestrator)
        orchestrator.respond(session, "80")
        with pytest.raises(KeyError):
            orchestrator.respond(session, "irrelevant")
        traces, _ = _reasoning_trace_rows(engine)
        assert len(traces) == 1

    def test_reprompts_before_decision_success_never_create_a_premature_trace(
        self, orchestrator, engine
    ):
        session = _drive_to_decision_confidence_prompt(orchestrator)
        # An invalid confidence answer re-asks without advancing or
        # committing anything.
        orchestrator.respond(session, "not a number")
        assert session.current_step is ConversationStep.DECISION
        traces, _ = _reasoning_trace_rows(engine)
        assert traces == []


class TestIdentityPropagation:
    def test_trace_references_the_exact_observation_id_from_this_conversation(
        self, orchestrator, engine
    ):
        session = _drive_to_decision_confidence_prompt(orchestrator)
        orchestrator.respond(session, "80")

        _, supports = _reasoning_trace_rows(engine)
        assert len(supports) == 1
        assert supports[0][3] == str(session.observation_id)

    def test_two_separate_conversations_each_get_their_own_traced_observation(
        self, engine
    ):
        orchestrator_one = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
        orchestrator_two = build_conversation_orchestrator(engine, case_id=uuid.uuid4())

        session_one = _drive_to_decision_confidence_prompt(orchestrator_one)
        orchestrator_one.respond(session_one, "80")
        session_two = _drive_to_decision_confidence_prompt(orchestrator_two)
        orchestrator_two.respond(session_two, "80")

        assert session_one.observation_id != session_two.observation_id
        _, supports = _reasoning_trace_rows(engine)
        target_ids = {row[3] for row in supports}
        assert target_ids == {str(session_one.observation_id), str(session_two.observation_id)}


class TestComposition:
    def test_real_composition_supplies_a_reasoning_trace_service(self, orchestrator):
        assert isinstance(orchestrator._reasoning_trace_service, ReasoningTraceService)

    def test_uses_in_memory_database_not_the_real_repository_file(self, engine):
        assert str(engine.url) == "sqlite:///:memory:"

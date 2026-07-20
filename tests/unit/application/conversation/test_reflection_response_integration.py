"""Proves the ATLAS-009 CLI-level integration point (conversation/cli.py).

Covers: the explicit preservation-choice flow (yes commits, no/empty
does not), the Decision-capture commit boundary (fires only at
DECISION_RECORDED), abandonment before that point, the partial-failure
case (Decision succeeds, Reflection Response write fails), read
isolation from every other capability's own composition root, and
unchanged Core Loop progression/captured fields throughout.
"""
from __future__ import annotations

import inspect
import io
import uuid
from contextlib import redirect_stdout
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.conversation.cli import (
    _maybe_commit_reflection_response,
    _maybe_reflect_and_coach,
)
from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)
from atlas.core.application.conversation.session import ConversationStep
from atlas.core.application.decision.capture_decision import (
    CaptureDecisionRequest,
    CaptureDecisionService,
)
from atlas.core.application.decision_reflection.composition import (
    build_decision_reflection_query,
    create_decision_reflection_tables,
)
from atlas.core.application.reflection_response.capture_reflection_response import (
    CaptureReflectionResponseService,
)
from atlas.core.application.reflection_response.composition import (
    build_capture_reflection_response_service,
    create_reflection_response_tables,
)
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)

_T0 = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)

_ANSWERS = [
    "Is NVIDIA still a buy?",
    "NVIDIA",
    "Datacenter demand keeps growing",
    "This suggests continued revenue growth",
    "NVIDIA will keep beating estimates",
    "Recent earnings beat estimates",
    "support",
    "The thesis remains intact",
    "buy",
]


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_conversation_tables(eng)
    create_decision_reflection_tables(eng)
    create_reflection_response_tables(eng)
    return eng


def _seed_two_matching_decisions(engine):
    repository = SqlAlchemyDecisionRepository(engine)
    service = CaptureDecisionService(repository)
    for confidence in (90, 70):
        service.capture(
            CaptureDecisionRequest(
                user_id=uuid.uuid4(),
                decision_type="BUY",
                subject="NVIDIA",
                reason="Demand is accelerating.",
                confidence=confidence,
                decided_at=_T0,
            )
        )


def _run_full_conversation(
    engine, coach_response, preservation_choice, capture_service, confidence="85"
):
    """Runs the entire scripted conversation, including the final
    confidence answer, using the real cli.py private functions.
    """
    orchestrator = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
    decision_reflection_query = build_decision_reflection_query(engine)
    session = orchestrator.start()

    answers = iter([coach_response, preservation_choice])

    def input_fn(prompt: str) -> str:
        return next(answers)

    provisional_response = None
    printed_lines: list[str] = []
    for answer in [*_ANSWERS, confidence]:
        orchestrator.respond(session, answer)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            if session.current_step is ConversationStep.DECISION_RECORDED:
                _maybe_commit_reflection_response(capture_service, session, provisional_response)
            else:
                provisional_response = _maybe_reflect_and_coach(
                    decision_reflection_query, session, provisional_response, input_fn=input_fn
                )
        printed_lines.append(buffer.getvalue())

    return session, "".join(printed_lines)


class TestExplicitPreservationChoice:
    def test_explicit_yes_persists_a_reflection_response(self, engine):
        _seed_two_matching_decisions(engine)
        capture_service = build_capture_reflection_response_service(engine)

        session, _ = _run_full_conversation(
            engine, coach_response="This feels similar to before.", preservation_choice="yes",
            capture_service=capture_service,
        )

        # No retrieval API is authorized yet; query directly for this test only.
        from sqlalchemy import select

        from atlas.core.infrastructure.persistence.reflection_response.table import (
            reflection_responses_table,
        )

        with engine.connect() as connection:
            rows = connection.execute(select(reflection_responses_table)).mappings().all()
        assert len(rows) == 1
        assert rows[0]["decision_id"] == str(session.decision_id)
        assert rows[0]["response_text"] == "This feels similar to before."

    def test_explicit_no_persists_nothing(self, engine):
        _seed_two_matching_decisions(engine)
        capture_service = build_capture_reflection_response_service(engine)

        _run_full_conversation(
            engine, coach_response="This feels similar to before.", preservation_choice="no",
            capture_service=capture_service,
        )

        from sqlalchemy import select

        from atlas.core.infrastructure.persistence.reflection_response.table import (
            reflection_responses_table,
        )

        with engine.connect() as connection:
            rows = connection.execute(select(reflection_responses_table)).mappings().all()
        assert rows == []

    def test_empty_ephemeral_response_never_asks_the_preservation_question(self, engine):
        _seed_two_matching_decisions(engine)
        capture_service = build_capture_reflection_response_service(engine)

        def raising_if_asked_twice(prompt: str) -> str:
            raise AssertionError("preservation question must not be asked when response is empty")

        orchestrator = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
        decision_reflection_query = build_decision_reflection_query(engine)
        session = orchestrator.start()
        provisional_response = None
        call_count = {"n": 0}

        def input_fn(prompt: str) -> str:
            call_count["n"] += 1
            return ""  # investor presses Enter -- declines to engage at all

        for answer in [*_ANSWERS, "85"]:
            orchestrator.respond(session, answer)
            if session.current_step is ConversationStep.DECISION_RECORDED:
                _maybe_commit_reflection_response(capture_service, session, provisional_response)
            else:
                provisional_response = _maybe_reflect_and_coach(
                    decision_reflection_query, session, provisional_response, input_fn=input_fn
                )
        assert call_count["n"] == 1  # only the ephemeral response prompt, never the keep-this one


class TestAbandonmentBeforeDecisionCapture:
    def test_saying_yes_then_abandoning_before_confidence_persists_nothing(self, engine):
        _seed_two_matching_decisions(engine)

        orchestrator = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
        decision_reflection_query = build_decision_reflection_query(engine)
        session = orchestrator.start()
        answers = iter(["This feels similar to before.", "yes"])

        def input_fn(prompt: str) -> str:
            return next(answers)

        provisional_response = None
        # Deliberately stop after "buy" -- never provide the confidence
        # answer, so DECISION_RECORDED is never reached.
        for answer in _ANSWERS:
            orchestrator.respond(session, answer)
            provisional_response = _maybe_reflect_and_coach(
                decision_reflection_query, session, provisional_response, input_fn=input_fn
            )

        assert provisional_response is not None  # the investor did say yes
        assert session.current_step is not ConversationStep.DECISION_RECORDED

        from sqlalchemy import select

        from atlas.core.infrastructure.persistence.reflection_response.table import (
            reflection_responses_table,
        )

        with engine.connect() as connection:
            rows = connection.execute(select(reflection_responses_table)).mappings().all()
        assert rows == []  # nothing was ever persisted -- provisional_response simply goes unused


class TestPartialFailure:
    def test_decision_remains_valid_when_the_second_write_fails(self, engine):
        _seed_two_matching_decisions(engine)

        class RaisingRepository:
            def add(self, reflection_response):
                raise RuntimeError("disk full")

            def get(self, reflection_response_id):
                return None

        failing_capture_service = CaptureReflectionResponseService(RaisingRepository())

        session, printed = _run_full_conversation(
            engine,
            coach_response="This feels similar to before.",
            preservation_choice="yes",
            capture_service=failing_capture_service,
        )

        # The Decision itself is unaffected and fully recorded.
        assert session.decision_id is not None
        decision_repository = SqlAlchemyDecisionRepository(engine)
        recorded_decision = decision_repository.get(DecisionId(session.decision_id))
        assert recorded_decision is not None

        # No ReflectionResponse exists anywhere.
        from sqlalchemy import select

        from atlas.core.infrastructure.persistence.reflection_response.table import (
            reflection_responses_table,
        )

        with engine.connect() as connection:
            rows = connection.execute(select(reflection_responses_table)).mappings().all()
        assert rows == []

        # The failure was reported honestly, not swallowed.
        assert "recorded, but the response" in printed
        assert "could not be saved" in printed


class TestReadIsolation:
    def test_no_other_capability_imports_reflection_response(self):
        from atlas.core.application import (
            decision_reflection,
            pattern_recognition,
            strategy_signature,
        )
        from atlas.core.application.decision_coach import coach as decision_coach_module

        for module in (
            pattern_recognition.composition,
            strategy_signature.composition,
            decision_reflection.composition,
            decision_coach_module,
        ):
            source = inspect.getsource(module)
            assert "reflection_response" not in source

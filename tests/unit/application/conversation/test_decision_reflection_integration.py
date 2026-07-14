"""Proves the ATLAS-007/ATLAS-008 CLI-level integration point (conversation/cli.py).

Scripts the same seven-step conversation twice against
ConversationOrchestrator.respond() directly — once with no prior
recorded Decisions (no Reflection/Coach possible) and once with two
prior matching Decisions already recorded (a Reflection and a Coach
question fire) — and asserts the sequence of turn.prompt values and the
final captured Decision fields are identical in both cases. Also
exercises conversation.cli._maybe_reflect_and_coach directly, with a
fake input_fn standing in for the ephemeral response opportunity, to
confirm it fires only at the documented moment, prints the expected
content, and never lets the ephemeral input reach the orchestrator.
"""
from __future__ import annotations

import io
import uuid
from contextlib import redirect_stdout
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.conversation.cli import _maybe_reflect_and_coach
from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)
from atlas.core.application.decision.capture_decision import (
    CaptureDecisionRequest,
    CaptureDecisionService,
)
from atlas.core.application.decision_reflection.composition import (
    build_decision_reflection_query,
    create_decision_reflection_tables,
)
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)

_T0 = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)

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
    "90",
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
    return eng


def _never_called_input(prompt: str) -> str:
    raise AssertionError("input_fn must not be called when no Reflection fires")


def _run_scripted_conversation(engine, ephemeral_response: str = ""):
    orchestrator = build_conversation_orchestrator(engine)
    decision_reflection_query = build_decision_reflection_query(engine)
    session = orchestrator.start()

    call_count = {"n": 0}

    def input_fn(prompt: str) -> str:
        call_count["n"] += 1
        return ephemeral_response

    prompts_seen: list[str] = []
    reflections_and_coaching_printed: list[str] = []
    provisional_response = None
    for answer in _ANSWERS:
        turn = orchestrator.respond(session, answer)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            provisional_response = _maybe_reflect_and_coach(
                decision_reflection_query, session, provisional_response, input_fn=input_fn
            )
        printed = buffer.getvalue()
        if printed:
            reflections_and_coaching_printed.append(printed)
        prompts_seen.append(turn.prompt)

    return session, prompts_seen, reflections_and_coaching_printed, call_count["n"]


class TestProgressionUnaffectedByReflectionAndCoach:
    def test_prompt_sequence_and_captured_decision_identical_with_and_without_a_reflection(
        self, engine
    ):
        (
            without_session,
            without_prompts,
            without_printed,
            without_input_calls,
        ) = _run_scripted_conversation(engine)
        assert without_printed == []  # no prior Decisions recorded yet
        assert without_input_calls == 0  # no Reflection -> input_fn never called

        # Now seed two prior matching Decisions so the third, identical
        # conversation script has a genuine Pattern to be reflected on.
        decision_repository = SqlAlchemyDecisionRepository(engine)
        service = CaptureDecisionService(decision_repository)
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

        (
            with_session,
            with_prompts,
            with_printed,
            with_input_calls,
        ) = _run_scripted_conversation(engine, ephemeral_response="90")

        assert with_prompts == without_prompts
        assert len(with_printed) == 1
        assert "(Reflection)" in with_printed[0]
        assert "(Coach)" in with_printed[0]
        # Two input_fn calls: the ephemeral response itself, then the
        # ATLAS-009 preservation choice (declined here, since "90" is not
        # an affirmative keyword) — this test file covers ATLAS-007/008
        # only; the full preservation/commit flow has its own dedicated
        # test file, test_reflection_response_integration.py.
        assert with_input_calls == 2

        assert with_session.observation_subject == without_session.observation_subject
        assert with_session.conclusion_statement == without_session.conclusion_statement
        assert with_session.is_complete() and without_session.is_complete()

    def test_no_reflection_never_invokes_input_fn(self, engine):
        session_result = _run_scripted_conversation(engine)
        # _never_called_input is exercised directly here to make the
        # "never called" guarantee explicit and independently checkable.
        orchestrator = build_conversation_orchestrator(engine)
        decision_reflection_query = build_decision_reflection_query(engine)
        session = orchestrator.start()
        provisional_response = None
        for answer in _ANSWERS:
            orchestrator.respond(session, answer)
            provisional_response = _maybe_reflect_and_coach(
                decision_reflection_query,
                session,
                provisional_response,
                input_fn=_never_called_input,
            )  # must not raise, since no Reflection ever fires here
        assert session_result[3] == 0

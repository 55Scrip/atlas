"""Proves the ATLAS-007 CLI-level integration point (conversation/cli.py).

Scripts the same seven-step conversation twice against
ConversationOrchestrator.respond() directly — once with no prior
recorded Decisions (no Reflection possible) and once with two prior
matching Decisions already recorded (a Reflection fires) — and asserts
the sequence of turn.prompt values and the final captured Decision
fields are identical in both cases. Also exercises
conversation.cli._maybe_print_reflection directly to confirm it fires
only at the documented moment and prints the expected content.
"""
from __future__ import annotations

import io
import uuid
from contextlib import redirect_stdout
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.conversation.cli import _maybe_print_reflection
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


def _run_scripted_conversation(engine):
    orchestrator = build_conversation_orchestrator(engine)
    decision_reflection_query = build_decision_reflection_query(engine)
    session = orchestrator.start()

    prompts_seen: list[str] = []
    reflections_printed: list[str] = []
    for answer in _ANSWERS:
        turn = orchestrator.respond(session, answer)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            _maybe_print_reflection(decision_reflection_query, session)
        printed = buffer.getvalue()
        if printed:
            reflections_printed.append(printed)
        prompts_seen.append(turn.prompt)

    return session, prompts_seen, reflections_printed


class TestProgressionUnaffectedByReflection:
    def test_prompt_sequence_and_captured_decision_identical_with_and_without_a_reflection(
        self, engine
    ):
        without_session, without_prompts, without_reflections = _run_scripted_conversation(
            engine
        )
        assert without_reflections == []  # no prior Decisions recorded yet

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

        with_session, with_prompts, with_reflections = _run_scripted_conversation(engine)

        assert with_prompts == without_prompts
        assert len(with_reflections) == 1
        assert "(Reflection)" in with_reflections[0]

        assert with_session.observation_subject == without_session.observation_subject
        assert with_session.conclusion_statement == without_session.conclusion_statement
        assert with_session.is_complete() and without_session.is_complete()

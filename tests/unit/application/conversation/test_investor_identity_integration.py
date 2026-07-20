"""Integration tests proving the Investor Identity defect is fixed (ATLAS-009B).

Before this increment, `Decision.user_id` was populated from
`ConversationSession.session_id` — a fresh random UUID on every
`ConversationSession()` construction. Two separate conversations against
the same store therefore produced Decisions with two different,
unrelated `user_id` values. These tests prove that no longer happens,
while confirming `ConversationSession.session_id` itself is completely
unchanged.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)
from atlas.core.infrastructure.persistence.decision.table import decisions_table

SCRIPTED_ANSWERS = [
    "Is demand for AI infrastructure accelerating?",  # Question
    "Semiconductor sector",  # Observation subject
    "Several companies raised capex guidance.",  # Observation statement
    "This suggests demand may be accelerating.",  # Interpretation
    "Demand for AI infrastructure may be accelerating.",  # Hypothesis
    "Order intake increased by 24 percent.",  # Evidence statement
    "it supports it",  # Evidence direction
    "The weight of evidence supports accelerating demand.",  # Conclusion
    "buy",  # Decision type
    "80",  # Decision confidence
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
    return eng


def _run_conversation_to_decision(orchestrator):
    session = orchestrator.start()
    for answer in SCRIPTED_ANSWERS:
        orchestrator.respond(session, answer)
    return session


class TestTwoSeparateProcessInvocationsShareOneInvestorIdentity:
    def test_two_orchestrator_builds_produce_decisions_with_the_same_user_id(self, engine):
        # Each build_conversation_orchestrator(engine) call simulates a
        # separate process invocation of conversation/cli.py against the
        # same ATLAS_HOME database.
        first_orchestrator = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
        first_session = _run_conversation_to_decision(first_orchestrator)

        second_orchestrator = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
        second_session = _run_conversation_to_decision(second_orchestrator)

        with engine.connect() as connection:
            rows = (
                connection.execute(
                    select(decisions_table.c.id, decisions_table.c.user_id)
                )
                .mappings()
                .all()
            )
        user_ids_by_decision_id = {row["id"]: row["user_id"] for row in rows}

        first_user_id = user_ids_by_decision_id[str(first_session.decision_id)]
        second_user_id = user_ids_by_decision_id[str(second_session.decision_id)]
        assert first_user_id == second_user_id

    def test_conversation_session_ids_remain_distinct_and_random(self, engine):
        # ConversationSession.session_id must stay exactly what it was:
        # ephemeral, per-conversation, and independent of Investor Identity.
        first_orchestrator = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
        first_session = _run_conversation_to_decision(first_orchestrator)

        second_orchestrator = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
        second_session = _run_conversation_to_decision(second_orchestrator)

        assert first_session.session_id != second_session.session_id


class TestLegacyDecisionsAreReconciledOnFirstUse:
    def test_pre_existing_session_derived_decisions_are_reconciled(self, engine):
        # Simulate a store that already has Decisions recorded under the
        # old, unstable session-derived user_id scheme, before this
        # increment's Investor Identity resolver ever ran.
        import uuid
        from datetime import datetime, timezone

        from sqlalchemy import insert

        legacy_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        now = datetime(2026, 7, 1, tzinfo=timezone.utc).isoformat()
        with engine.begin() as connection:
            for i, legacy_user_id in enumerate(legacy_ids):
                connection.execute(
                    insert(decisions_table).values(
                        id=str(uuid.uuid4()),
                        user_id=legacy_user_id,
                        decision_type="BUY",
                        subject=f"Legacy Subject {i}",
                        reason="Legacy reason.",
                        confidence=70,
                        decided_at=now,
                        recorded_at=now,
                        source="MANUAL",
                    )
                )

        # The first conversation run after this increment ships resolves
        # Investor Identity and, in the same transaction, reconciles every
        # existing Decision to it.
        orchestrator = build_conversation_orchestrator(engine, case_id=uuid.uuid4())
        _run_conversation_to_decision(orchestrator)

        with engine.connect() as connection:
            rows = connection.execute(select(decisions_table.c.user_id)).all()
        all_user_ids = {row[0] for row in rows}

        # Every Decision in the store — the two legacy ones and the new
        # one just recorded — now shares exactly one user_id.
        assert len(all_user_ids) == 1
        new_decision_user_id = list(all_user_ids)[0]
        assert new_decision_user_id not in legacy_ids

"""Tests for reflection_comparison's CLI (ATLAS-011).

Covers list-position -> ReflectionResponseId mapping, verbatim display,
and an end-to-end run confirming honest, non-crashing behavior on an
invalid selection with no unexpected writes.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.core.application.investor_identity.composition import resolve_investor_identity
from atlas.core.application.reflection_comparison import cli as reflection_comparison_cli
from atlas.core.application.reflection_history.composition import (
    create_reflection_history_tables,
)
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    Subject,
)
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ResponseText,
)
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import decisions_table
from atlas.core.infrastructure.persistence.investor_identity.table import (
    investor_identity_table,
)
from atlas.core.infrastructure.persistence.reflection_response.sqlalchemy_repository import (
    SqlAlchemyReflectionResponseRepository,
)
from atlas.core.infrastructure.persistence.reflection_response.table import (
    reflection_responses_table,
)

_T0 = datetime(2026, 7, 22, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    return create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )


class TestPromptForSelection:
    def test_valid_number_maps_to_the_corresponding_entry_id(self):
        entry_a = _build_entry(_T0, "A")
        entry_b = _build_entry(_T0.replace(hour=15), "B")
        history = ReflectionHistory(entries=(entry_a, entry_b))
        answers = iter(["2"])

        selected_id = reflection_comparison_cli._prompt_for_selection(
            history, "> ", input_fn=lambda prompt: next(answers)
        )

        assert selected_id == entry_b.id

    def test_non_numeric_input_reprompts_until_valid(self, capsys):
        entry_a = _build_entry(_T0, "A")
        history = ReflectionHistory(entries=(entry_a,))
        answers = iter(["not a number", "1"])

        selected_id = reflection_comparison_cli._prompt_for_selection(
            history, "> ", input_fn=lambda prompt: next(answers)
        )

        assert selected_id == entry_a.id
        assert "Please type a number" in capsys.readouterr().out

    def test_out_of_range_number_reprompts_until_valid(self, capsys):
        entry_a = _build_entry(_T0, "A")
        history = ReflectionHistory(entries=(entry_a,))
        answers = iter(["99", "1"])

        selected_id = reflection_comparison_cli._prompt_for_selection(
            history, "> ", input_fn=lambda prompt: next(answers)
        )

        assert selected_id == entry_a.id
        assert "Please type a number" in capsys.readouterr().out


class TestVerbatimDisplay:
    def test_print_full_entry_shows_every_field_completely(self, capsys):
        entry = _build_entry(_T0, "  This time feels DIFFERENT.  ")

        reflection_comparison_cli._print_full_entry("First:", entry)

        output = capsys.readouterr().out
        assert entry.response_text.value in output
        assert entry.provenance.reflection_description in output
        assert entry.provenance.coaching_question_text in output
        assert entry.provenance.grounding_pattern.strategy_name in output


def _build_entry(recorded_at, text, decision_id=None):
    from atlas.core.domain.decision.value_objects import DecisionId

    if decision_id is None:
        decision_id = DecisionId()
    return ReflectionResponse.register(
        decision_id=decision_id,
        response_text=ResponseText(text),
        provenance=ProvenanceSnapshot(
            reflection_description="You have made 2 BUY decisions on NVIDIA.",
            coaching_question_text="What's similar or different this time?",
            grounding_pattern=PatternMembershipSnapshot(
                strategy_name="same_subject_and_type",
                member_decision_ids=(decision_id,),
            ),
            strategy_signature_patterns=(),
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=80,
        ),
        clock=lambda: recorded_at,
    )


class TestRunEndToEnd:
    def test_duplicate_selection_prints_honest_message_and_causes_no_extra_writes(
        self, engine, monkeypatch, capsys
    ):
        create_reflection_history_tables(engine)
        owner_user_id = resolve_investor_identity(engine)

        decision_repo = SqlAlchemyDecisionRepository(engine)
        response_repo = SqlAlchemyReflectionResponseRepository(engine)
        decision = Decision.register(
            user_id=owner_user_id,
            decision_type=DecisionType.BUY,
            subject=Subject("NVIDIA"),
            investment_case=InvestmentCase("Demand accelerating."),
            confidence=Confidence(80),
            decided_at=_T0,
            clock=lambda: _T0,
        )
        decision_repo.add(decision)
        entry_a = _build_entry(_T0, "First response.", decision_id=decision.id)
        entry_b = _build_entry(_T0.replace(hour=15), "Second response.", decision_id=decision.id)
        response_repo.add(entry_a)
        response_repo.add(entry_b)

        monkeypatch.setattr(
            reflection_comparison_cli, "create_database_engine", lambda: engine
        )

        def _snapshot():
            with engine.connect() as connection:
                return {
                    "investor_identity": sorted(
                        map(tuple, connection.execute(select(investor_identity_table)).all())
                    ),
                    "decisions": sorted(
                        map(tuple, connection.execute(select(decisions_table)).all())
                    ),
                    "reflection_responses": sorted(
                        map(
                            tuple,
                            connection.execute(select(reflection_responses_table)).all(),
                        )
                    ),
                }

        before = _snapshot()
        answers = iter(["1", "1"])  # same number twice -> duplicate selection
        reflection_comparison_cli.run(input_fn=lambda prompt: next(answers))
        after = _snapshot()

        output = capsys.readouterr().out
        assert "different Reflection Responses" in output
        assert before == after

    def test_fewer_than_two_preserved_responses_prints_honest_message(
        self, engine, monkeypatch, capsys
    ):
        create_reflection_history_tables(engine)
        monkeypatch.setattr(
            reflection_comparison_cli, "create_database_engine", lambda: engine
        )

        reflection_comparison_cli.run(input_fn=lambda prompt: (_ for _ in ()).throw(
            AssertionError("input must not be requested when fewer than two entries exist")
        ))

        output = capsys.readouterr().out
        assert "at least two" in output

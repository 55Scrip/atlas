"""Tests for reflection_exploration's CLI (ATLAS-012).

Covers list-position -> ReflectionResponseId mapping (including
deduplication and reprompt on malformed input), verbatim display, and
end-to-end runs against a real store. UnreachableReflectionResponseError
can never be triggered through this CLI's own legitimate selection
mechanism, by construction — _prompt_for_selection only ever returns
ids drawn from the already-owner-scoped, already-displayed entries —
mirroring the same situation reflection_comparison/cli.py's own
"not owned" path is in.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.investor_identity.composition import resolve_investor_identity
from atlas.core.application.reflection_exploration import cli as reflection_exploration_cli
from atlas.core.application.reflection_history.composition import (
    create_reflection_history_tables,
)
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionId,
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
from atlas.core.infrastructure.persistence.reflection_response.sqlalchemy_repository import (
    SqlAlchemyReflectionResponseRepository,
)

_T0 = datetime(2026, 7, 23, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    return create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )


def _build_entry(recorded_at, text, decision_id=None):
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


class TestPromptForSelection:
    def test_valid_numbers_map_to_corresponding_entry_ids(self):
        entry_a = _build_entry(_T0, "A")
        entry_b = _build_entry(_T0.replace(hour=15), "B")
        ordered = (entry_a, entry_b)
        answers = iter(["1 2"])

        selected_ids = reflection_exploration_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == (entry_a.id, entry_b.id)

    def test_empty_input_returns_empty_selection(self):
        entry_a = _build_entry(_T0, "A")
        ordered = (entry_a,)
        answers = iter([""])

        selected_ids = reflection_exploration_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == ()

    def test_duplicate_numbers_are_preserved_as_given_to_the_query(self):
        # The CLI itself does not deduplicate — ReflectionExplorationQuery
        # does. This test confirms the CLI passes duplicates through
        # unmodified, trusting the query's own set semantics.
        entry_a = _build_entry(_T0, "A")
        ordered = (entry_a,)
        answers = iter(["1 1"])

        selected_ids = reflection_exploration_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == (entry_a.id, entry_a.id)

    def test_non_numeric_token_reprompts_until_valid(self, capsys):
        entry_a = _build_entry(_T0, "A")
        ordered = (entry_a,)
        answers = iter(["not a number", "1"])

        selected_ids = reflection_exploration_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == (entry_a.id,)
        assert "Please type only the numbers shown above" in capsys.readouterr().out

    def test_out_of_range_number_reprompts_until_valid(self, capsys):
        entry_a = _build_entry(_T0, "A")
        ordered = (entry_a,)
        answers = iter(["99", "1"])

        selected_ids = reflection_exploration_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == (entry_a.id,)
        assert "Please type only the numbers shown above" in capsys.readouterr().out


class TestVerbatimDisplay:
    def test_print_full_entry_shows_every_field_completely(self, capsys):
        entry = _build_entry(_T0, "  This time feels DIFFERENT.  ")

        reflection_exploration_cli._print_full_entry(entry)

        output = capsys.readouterr().out
        assert entry.response_text.value in output
        assert entry.provenance.reflection_description in output
        assert entry.provenance.coaching_question_text in output
        assert entry.provenance.grounding_pattern.strategy_name in output


class TestSortedEntries:
    def test_sorted_entries_orders_by_recorded_at_ascending(self):
        later = _build_entry(_T0.replace(hour=15), "later")
        earlier = _build_entry(_T0, "earlier")
        history = ReflectionHistory(entries=(later, earlier))

        ordered = reflection_exploration_cli._sorted_entries(history)

        assert ordered == (earlier, later)


class TestRunEndToEnd:
    def test_empty_store_prints_honest_message_and_never_prompts(self, engine, monkeypatch):
        create_reflection_history_tables(engine)
        monkeypatch.setattr(
            reflection_exploration_cli, "create_database_engine", lambda: engine
        )

        reflection_exploration_cli.run(
            input_fn=lambda prompt: (_ for _ in ()).throw(
                AssertionError("input must not be requested when no entries exist")
            )
        )

    def test_selecting_two_of_three_produces_a_scope_of_two_verbatim(
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
        entry_b = _build_entry(_T0.replace(hour=12), "Second response.", decision_id=decision.id)
        entry_c = _build_entry(_T0.replace(hour=18), "Third response.", decision_id=decision.id)
        response_repo.add(entry_a)
        response_repo.add(entry_b)
        response_repo.add(entry_c)

        monkeypatch.setattr(
            reflection_exploration_cli, "create_database_engine", lambda: engine
        )

        answers = iter(["1 3"])
        reflection_exploration_cli.run(input_fn=lambda prompt: next(answers))

        output = capsys.readouterr().out
        assert "2 Reflection Response(s)" in output
        # entry_b legitimately appears once, in the initial pointer
        # list shown before selection — it must not appear in the
        # detail section (after the summary line) reserved for the
        # investor's actual two selected entries.
        detail_section = output.split("2 Reflection Response(s)")[1]
        assert entry_a.response_text.value in detail_section
        assert entry_c.response_text.value in detail_section
        assert entry_b.response_text.value not in detail_section

    def test_empty_selection_prints_empty_exploration_message(self, engine, monkeypatch, capsys):
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
        response_repo.add(_build_entry(_T0, "Only response.", decision_id=decision.id))

        monkeypatch.setattr(
            reflection_exploration_cli, "create_database_engine", lambda: engine
        )

        answers = iter([""])
        reflection_exploration_cli.run(input_fn=lambda prompt: next(answers))

        output = capsys.readouterr().out
        assert "Your exploration is empty." in output

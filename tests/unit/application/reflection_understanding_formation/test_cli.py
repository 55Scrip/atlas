"""Tests for reflection_understanding_formation's CLI (ATLAS-013).

Covers list-position -> ReflectionResponseId mapping, the explicit
request confirmation as a separate step from selection and from content,
and end-to-end runs against a real store. This CLI never solicits an
"Atlas contribution" or "joint content," and never presents a
mode-selection prompt — it always asserts INVESTOR_SUBSTANCE_AUTHORED /
INVESTOR_ARTICULATED, the one attribution this increment has an honest
source for.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.investor_identity.composition import resolve_investor_identity
from atlas.core.application.reflection_history.composition import (
    create_reflection_history_tables,
)
from atlas.core.application.reflection_understanding_formation import (
    cli as reflection_understanding_formation_cli,
)
from atlas.core.application.reflection_understanding_formation.formation import (
    ArticulationAuthorshipMode,
    SubstanceAuthorshipMode,
)
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

        selected_ids = reflection_understanding_formation_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == (entry_a.id, entry_b.id)

    def test_empty_input_returns_empty_selection(self):
        entry_a = _build_entry(_T0, "A")
        ordered = (entry_a,)
        answers = iter([""])

        selected_ids = reflection_understanding_formation_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == ()

    def test_non_numeric_token_reprompts_until_valid(self, capsys):
        entry_a = _build_entry(_T0, "A")
        ordered = (entry_a,)
        answers = iter(["not a number", "1"])

        selected_ids = reflection_understanding_formation_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == (entry_a.id,)
        assert "Please type only the numbers shown above" in capsys.readouterr().out

    def test_out_of_range_number_reprompts_until_valid(self, capsys):
        entry_a = _build_entry(_T0, "A")
        ordered = (entry_a,)
        answers = iter(["99", "1"])

        selected_ids = reflection_understanding_formation_cli._prompt_for_selection(
            ordered, input_fn=lambda prompt: next(answers)
        )

        assert selected_ids == (entry_a.id,)
        assert "Please type only the numbers shown above" in capsys.readouterr().out


class TestPromptForExplicitRequest:
    def test_yes_confirms(self):
        answers = iter(["yes"])
        assert reflection_understanding_formation_cli._prompt_for_explicit_request(
            input_fn=lambda prompt: next(answers)
        )

    def test_y_confirms(self):
        answers = iter(["y"])
        assert reflection_understanding_formation_cli._prompt_for_explicit_request(
            input_fn=lambda prompt: next(answers)
        )

    def test_no_does_not_confirm(self):
        answers = iter(["no"])
        assert not reflection_understanding_formation_cli._prompt_for_explicit_request(
            input_fn=lambda prompt: next(answers)
        )

    def test_blank_does_not_confirm(self):
        answers = iter([""])
        assert not reflection_understanding_formation_cli._prompt_for_explicit_request(
            input_fn=lambda prompt: next(answers)
        )


class TestPromptForContent:
    def test_returns_non_empty_answer(self):
        answers = iter(["This time feels different."])
        content = reflection_understanding_formation_cli._prompt_for_content(
            input_fn=lambda prompt: next(answers)
        )
        assert content == "This time feels different."

    def test_reprompts_on_blank(self, capsys):
        answers = iter(["   ", "Finally, an interpretation."])
        content = reflection_understanding_formation_cli._prompt_for_content(
            input_fn=lambda prompt: next(answers)
        )
        assert content == "Finally, an interpretation."
        assert "An interpretation is required" in capsys.readouterr().out


class TestPromptForQualification:
    def test_blank_returns_none(self):
        answers = iter([""])
        assert (
            reflection_understanding_formation_cli._prompt_for_qualification(
                input_fn=lambda prompt: next(answers)
            )
            is None
        )

    def test_non_blank_returns_the_text(self):
        answers = iter(["fairly tentative"])
        assert (
            reflection_understanding_formation_cli._prompt_for_qualification(
                input_fn=lambda prompt: next(answers)
            )
            == "fairly tentative"
        )


class TestRunEndToEnd:
    def test_empty_store_prints_honest_message_and_never_prompts(self, engine, monkeypatch):
        create_reflection_history_tables(engine)
        monkeypatch.setattr(
            reflection_understanding_formation_cli, "create_database_engine", lambda: engine
        )

        reflection_understanding_formation_cli.run(
            input_fn=lambda prompt: (_ for _ in ()).throw(
                AssertionError("input must not be requested when no entries exist")
            )
        )

    def _seed_one_entry(self, engine):
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
        entry = _build_entry(_T0, "First response.", decision_id=decision.id)
        response_repo.add(entry)
        return entry

    def test_empty_selection_aborts_without_further_prompts(self, engine, monkeypatch):
        self._seed_one_entry(engine)
        monkeypatch.setattr(
            reflection_understanding_formation_cli, "create_database_engine", lambda: engine
        )

        answers = iter([""])
        reflection_understanding_formation_cli.run(
            input_fn=lambda prompt: next(answers)
        )
        # Only one input call (the selection prompt) should ever occur;
        # StopIteration would be raised if run() tried to prompt again.

    def test_declining_explicit_request_aborts_before_content_is_solicited(
        self, engine, monkeypatch, capsys
    ):
        entry = self._seed_one_entry(engine)
        monkeypatch.setattr(
            reflection_understanding_formation_cli, "create_database_engine", lambda: engine
        )

        answers = iter(["1", "no"])
        reflection_understanding_formation_cli.run(
            input_fn=lambda prompt: next(answers)
        )

        output = capsys.readouterr().out
        assert "No Formation requested." in output
        assert entry.response_text.value in output  # shown in the pointer list only

    def test_full_successful_investor_substance_authored_formation(
        self, engine, monkeypatch, capsys
    ):
        entry = self._seed_one_entry(engine)
        monkeypatch.setattr(
            reflection_understanding_formation_cli, "create_database_engine", lambda: engine
        )

        answers = iter(["1", "yes", "This time feels different.", "fairly confident"])
        reflection_understanding_formation_cli.run(
            input_fn=lambda prompt: next(answers)
        )

        output = capsys.readouterr().out
        assert (
            f"Substance authorship: {SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED.value}"
            in output
        )
        assert (
            f"Articulation authorship: {ArticulationAuthorshipMode.INVESTOR_ARTICULATED.value}"
            in output
        )
        assert "This time feels different." in output
        assert "fairly confident" in output
        assert entry.response_text.value in output

    def test_blank_qualification_prints_none_recorded_not_a_confidence_claim(
        self, engine, monkeypatch, capsys
    ):
        self._seed_one_entry(engine)
        monkeypatch.setattr(
            reflection_understanding_formation_cli, "create_database_engine", lambda: engine
        )

        answers = iter(["1", "yes", "An interpretation.", ""])
        reflection_understanding_formation_cli.run(
            input_fn=lambda prompt: next(answers)
        )

        output = capsys.readouterr().out
        assert "Qualification: (none recorded)" in output

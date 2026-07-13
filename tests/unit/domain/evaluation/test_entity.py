"""Tests for the Evaluation aggregate root (ATLAS-001 Core Loop)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.evaluation.entity import Evaluation
from atlas.core.domain.evaluation.exceptions import InvalidEvaluatedAtError
from atlas.core.domain.evaluation.value_objects import Statement
from atlas.core.domain.outcome.value_objects import OutcomeId

_OUTCOME_ID = OutcomeId()
_STATEMENT = Statement("The decision proved correct; demand did accelerate.")
_EVALUATED_AT = datetime(2026, 10, 15, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestEvaluationCapture:
    def test_captures_the_given_fields(self):
        evaluation = Evaluation.capture(
            outcome_id=_OUTCOME_ID, statement=_STATEMENT, evaluated_at=_EVALUATED_AT
        )
        assert evaluation.outcome_id == _OUTCOME_ID
        assert evaluation.statement == _STATEMENT
        assert evaluation.evaluated_at == _EVALUATED_AT

    def test_assigns_a_fresh_id(self):
        first = Evaluation.capture(
            outcome_id=_OUTCOME_ID, statement=_STATEMENT, evaluated_at=_EVALUATED_AT
        )
        second = Evaluation.capture(
            outcome_id=_OUTCOME_ID, statement=_STATEMENT, evaluated_at=_EVALUATED_AT
        )
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 10, 15, 7, 0, tzinfo=timezone.utc)
        evaluation = Evaluation.capture(
            outcome_id=_OUTCOME_ID,
            statement=_STATEMENT,
            evaluated_at=_EVALUATED_AT,
            clock=_fixed_clock(now),
        )
        assert evaluation.recorded_at == now

    def test_evaluated_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 10, 15, 7, 0, tzinfo=timezone.utc)
        evaluation = Evaluation.capture(
            outcome_id=_OUTCOME_ID,
            statement=_STATEMENT,
            evaluated_at=_EVALUATED_AT,
            clock=_fixed_clock(now_utc),
        )
        assert evaluation.evaluated_at.utcoffset() == timedelta(hours=2)
        assert evaluation.evaluated_at.isoformat() == "2026-10-15T09:00:00+02:00"
        assert evaluation.recorded_at.utcoffset() == timedelta(0)

    def test_note_defaults_to_none(self):
        evaluation = Evaluation.capture(
            outcome_id=_OUTCOME_ID, statement=_STATEMENT, evaluated_at=_EVALUATED_AT
        )
        assert evaluation.note is None

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        evaluation = Evaluation.capture(
            outcome_id=_OUTCOME_ID, statement=_STATEMENT, evaluated_at=_EVALUATED_AT, note=blank
        )
        assert evaluation.note is None

    def test_rejects_missing_evaluated_at(self):
        with pytest.raises(InvalidEvaluatedAtError):
            Evaluation.capture(outcome_id=_OUTCOME_ID, statement=_STATEMENT, evaluated_at=None)

    def test_rejects_naive_evaluated_at(self):
        with pytest.raises(InvalidEvaluatedAtError):
            Evaluation.capture(
                outcome_id=_OUTCOME_ID,
                statement=_STATEMENT,
                evaluated_at=datetime(2026, 10, 15, 9, 0, 0),
            )

    def test_requires_an_outcome_id(self):
        with pytest.raises(TypeError):
            Evaluation.capture(statement=_STATEMENT, evaluated_at=_EVALUATED_AT)

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Evaluation.capture(outcome_id=_OUTCOME_ID, evaluated_at=_EVALUATED_AT)


class TestEvaluationImmutability:
    def test_is_frozen(self):
        evaluation = Evaluation.capture(
            outcome_id=_OUTCOME_ID, statement=_STATEMENT, evaluated_at=_EVALUATED_AT
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            evaluation.statement = Statement("changed")

"""Tests for the Learning aggregate root (ATLAS-001 Core Loop)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.learning.entity import Learning
from atlas.core.domain.learning.exceptions import InvalidLearnedAtError
from atlas.core.domain.learning.value_objects import Statement

_EVALUATION_ID = EvaluationId()
_STATEMENT = Statement("Weigh capex guidance more heavily than headline revenue growth.")
_LEARNED_AT = datetime(2026, 10, 16, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestLearningCapture:
    def test_captures_the_given_fields(self):
        learning = Learning.capture(
            evaluation_id=_EVALUATION_ID, statement=_STATEMENT, learned_at=_LEARNED_AT
        )
        assert learning.evaluation_id == _EVALUATION_ID
        assert learning.statement == _STATEMENT
        assert learning.learned_at == _LEARNED_AT

    def test_assigns_a_fresh_id(self):
        first = Learning.capture(
            evaluation_id=_EVALUATION_ID, statement=_STATEMENT, learned_at=_LEARNED_AT
        )
        second = Learning.capture(
            evaluation_id=_EVALUATION_ID, statement=_STATEMENT, learned_at=_LEARNED_AT
        )
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 10, 16, 7, 0, tzinfo=timezone.utc)
        learning = Learning.capture(
            evaluation_id=_EVALUATION_ID,
            statement=_STATEMENT,
            learned_at=_LEARNED_AT,
            clock=_fixed_clock(now),
        )
        assert learning.recorded_at == now

    def test_learned_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 10, 16, 7, 0, tzinfo=timezone.utc)
        learning = Learning.capture(
            evaluation_id=_EVALUATION_ID,
            statement=_STATEMENT,
            learned_at=_LEARNED_AT,
            clock=_fixed_clock(now_utc),
        )
        assert learning.learned_at.utcoffset() == timedelta(hours=2)
        assert learning.learned_at.isoformat() == "2026-10-16T09:00:00+02:00"
        assert learning.recorded_at.utcoffset() == timedelta(0)

    def test_note_defaults_to_none(self):
        learning = Learning.capture(
            evaluation_id=_EVALUATION_ID, statement=_STATEMENT, learned_at=_LEARNED_AT
        )
        assert learning.note is None

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        learning = Learning.capture(
            evaluation_id=_EVALUATION_ID, statement=_STATEMENT, learned_at=_LEARNED_AT, note=blank
        )
        assert learning.note is None

    def test_rejects_missing_learned_at(self):
        with pytest.raises(InvalidLearnedAtError):
            Learning.capture(evaluation_id=_EVALUATION_ID, statement=_STATEMENT, learned_at=None)

    def test_rejects_naive_learned_at(self):
        with pytest.raises(InvalidLearnedAtError):
            Learning.capture(
                evaluation_id=_EVALUATION_ID,
                statement=_STATEMENT,
                learned_at=datetime(2026, 10, 16, 9, 0, 0),
            )

    def test_requires_an_evaluation_id(self):
        with pytest.raises(TypeError):
            Learning.capture(statement=_STATEMENT, learned_at=_LEARNED_AT)

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Learning.capture(evaluation_id=_EVALUATION_ID, learned_at=_LEARNED_AT)


class TestLearningImmutability:
    def test_is_frozen(self):
        learning = Learning.capture(
            evaluation_id=_EVALUATION_ID, statement=_STATEMENT, learned_at=_LEARNED_AT
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            learning.statement = Statement("changed")

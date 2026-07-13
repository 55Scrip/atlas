"""Tests for the Question aggregate root (ATLAS-001 Core Loop)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.question.entity import Question
from atlas.core.domain.question.exceptions import InvalidRaisedAtError
from atlas.core.domain.question.value_objects import Statement

_STATEMENT = Statement("Is demand for AI infrastructure accelerating?")
_RAISED_AT = datetime(2026, 7, 13, 8, 0, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestQuestionCapture:
    def test_captures_the_given_fields(self):
        question = Question.capture(statement=_STATEMENT, raised_at=_RAISED_AT)
        assert question.statement == _STATEMENT
        assert question.raised_at == _RAISED_AT

    def test_assigns_a_fresh_id(self):
        first = Question.capture(statement=_STATEMENT, raised_at=_RAISED_AT)
        second = Question.capture(statement=_STATEMENT, raised_at=_RAISED_AT)
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 13, 6, 0, tzinfo=timezone.utc)
        question = Question.capture(
            statement=_STATEMENT, raised_at=_RAISED_AT, clock=_fixed_clock(now)
        )
        assert question.recorded_at == now

    def test_raised_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 7, 13, 6, 0, tzinfo=timezone.utc)
        question = Question.capture(
            statement=_STATEMENT, raised_at=_RAISED_AT, clock=_fixed_clock(now_utc)
        )
        assert question.raised_at.utcoffset() == timedelta(hours=2)
        assert question.raised_at.isoformat() == "2026-07-13T08:00:00+02:00"
        assert question.recorded_at.utcoffset() == timedelta(0)

    def test_note_defaults_to_none(self):
        question = Question.capture(statement=_STATEMENT, raised_at=_RAISED_AT)
        assert question.note is None

    def test_accepts_note(self):
        question = Question.capture(
            statement=_STATEMENT, raised_at=_RAISED_AT, note="Prompted by the earnings call."
        )
        assert question.note == "Prompted by the earnings call."

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        question = Question.capture(statement=_STATEMENT, raised_at=_RAISED_AT, note=blank)
        assert question.note is None

    def test_note_is_stripped_not_just_kept(self):
        question = Question.capture(
            statement=_STATEMENT, raised_at=_RAISED_AT, note="  keep watching  "
        )
        assert question.note == "keep watching"

    def test_rejects_missing_raised_at(self):
        with pytest.raises(InvalidRaisedAtError):
            Question.capture(statement=_STATEMENT, raised_at=None)

    def test_rejects_naive_raised_at(self):
        with pytest.raises(InvalidRaisedAtError):
            Question.capture(statement=_STATEMENT, raised_at=datetime(2026, 7, 13, 8, 0, 0))

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Question.capture(raised_at=_RAISED_AT)


class TestQuestionImmutability:
    def test_is_frozen(self):
        question = Question.capture(statement=_STATEMENT, raised_at=_RAISED_AT)
        with pytest.raises(dataclasses.FrozenInstanceError):
            question.statement = Statement("changed")

"""Tests for the Hypothesis aggregate root (API-004 Hypothesis Capture)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.hypothesis.entity import Hypothesis
from atlas.core.domain.hypothesis.exceptions import InvalidFormulatedAtError
from atlas.core.domain.hypothesis.value_objects import Statement

_STATEMENT = Statement(
    "Demand for AI infrastructure may be accelerating faster than the market "
    "expects."
)
_FORMULATED_AT = datetime(2026, 7, 13, 18, 30, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestHypothesisCapture:
    def test_captures_the_given_fields(self):
        hypothesis = Hypothesis.capture(statement=_STATEMENT, formulated_at=_FORMULATED_AT)
        assert hypothesis.statement == _STATEMENT
        assert hypothesis.formulated_at == _FORMULATED_AT

    def test_assigns_a_fresh_id(self):
        first = Hypothesis.capture(statement=_STATEMENT, formulated_at=_FORMULATED_AT)
        second = Hypothesis.capture(statement=_STATEMENT, formulated_at=_FORMULATED_AT)
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 13, 16, 31, tzinfo=timezone.utc)
        hypothesis = Hypothesis.capture(
            statement=_STATEMENT, formulated_at=_FORMULATED_AT, clock=_fixed_clock(now)
        )
        assert hypothesis.recorded_at == now

    def test_formulated_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 7, 13, 16, 31, tzinfo=timezone.utc)
        hypothesis = Hypothesis.capture(
            statement=_STATEMENT, formulated_at=_FORMULATED_AT, clock=_fixed_clock(now_utc)
        )
        assert hypothesis.formulated_at.utcoffset() == timedelta(hours=2)
        assert hypothesis.formulated_at.isoformat() == "2026-07-13T18:30:00+02:00"
        assert hypothesis.recorded_at.utcoffset() == timedelta(0)

    def test_note_defaults_to_none(self):
        hypothesis = Hypothesis.capture(statement=_STATEMENT, formulated_at=_FORMULATED_AT)
        assert hypothesis.note is None

    def test_accepts_note(self):
        hypothesis = Hypothesis.capture(
            statement=_STATEMENT,
            formulated_at=_FORMULATED_AT,
            note="Revisit after the next reporting cycle.",
        )
        assert hypothesis.note == "Revisit after the next reporting cycle."

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        hypothesis = Hypothesis.capture(
            statement=_STATEMENT, formulated_at=_FORMULATED_AT, note=blank
        )
        assert hypothesis.note is None

    def test_note_is_stripped_not_just_kept(self):
        hypothesis = Hypothesis.capture(
            statement=_STATEMENT,
            formulated_at=_FORMULATED_AT,
            note="  keep watching  ",
        )
        assert hypothesis.note == "keep watching"

    def test_rejects_missing_formulated_at(self):
        with pytest.raises(InvalidFormulatedAtError):
            Hypothesis.capture(statement=_STATEMENT, formulated_at=None)

    def test_rejects_naive_formulated_at(self):
        with pytest.raises(InvalidFormulatedAtError):
            Hypothesis.capture(
                statement=_STATEMENT,
                formulated_at=datetime(2026, 7, 13, 18, 30, 0),
            )

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Hypothesis.capture(formulated_at=_FORMULATED_AT)


class TestHypothesisImmutability:
    def test_is_frozen(self):
        hypothesis = Hypothesis.capture(statement=_STATEMENT, formulated_at=_FORMULATED_AT)
        with pytest.raises(dataclasses.FrozenInstanceError):
            hypothesis.statement = Statement("changed")

"""Tests for the Interpretation aggregate root (ATLAS-001 Core Loop)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.interpretation.entity import Interpretation
from atlas.core.domain.interpretation.exceptions import InvalidInterpretedAtError
from atlas.core.domain.interpretation.value_objects import Statement
from atlas.core.domain.observation.value_objects import ObservationId

_OBSERVATION_ID = ObservationId()
_STATEMENT = Statement("This suggests demand may be accelerating.")
_INTERPRETED_AT = datetime(2026, 7, 13, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestInterpretationCapture:
    def test_captures_the_given_fields(self):
        interpretation = Interpretation.capture(
            observation_id=_OBSERVATION_ID, statement=_STATEMENT, interpreted_at=_INTERPRETED_AT
        )
        assert interpretation.observation_id == _OBSERVATION_ID
        assert interpretation.statement == _STATEMENT
        assert interpretation.interpreted_at == _INTERPRETED_AT

    def test_assigns_a_fresh_id(self):
        first = Interpretation.capture(
            observation_id=_OBSERVATION_ID, statement=_STATEMENT, interpreted_at=_INTERPRETED_AT
        )
        second = Interpretation.capture(
            observation_id=_OBSERVATION_ID, statement=_STATEMENT, interpreted_at=_INTERPRETED_AT
        )
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 13, 7, 0, tzinfo=timezone.utc)
        interpretation = Interpretation.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            interpreted_at=_INTERPRETED_AT,
            clock=_fixed_clock(now),
        )
        assert interpretation.recorded_at == now

    def test_interpreted_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 7, 13, 7, 0, tzinfo=timezone.utc)
        interpretation = Interpretation.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            interpreted_at=_INTERPRETED_AT,
            clock=_fixed_clock(now_utc),
        )
        assert interpretation.interpreted_at.utcoffset() == timedelta(hours=2)
        assert interpretation.interpreted_at.isoformat() == "2026-07-13T09:00:00+02:00"
        assert interpretation.recorded_at.utcoffset() == timedelta(0)

    def test_note_defaults_to_none(self):
        interpretation = Interpretation.capture(
            observation_id=_OBSERVATION_ID, statement=_STATEMENT, interpreted_at=_INTERPRETED_AT
        )
        assert interpretation.note is None

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        interpretation = Interpretation.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            interpreted_at=_INTERPRETED_AT,
            note=blank,
        )
        assert interpretation.note is None

    def test_rejects_missing_interpreted_at(self):
        with pytest.raises(InvalidInterpretedAtError):
            Interpretation.capture(
                observation_id=_OBSERVATION_ID, statement=_STATEMENT, interpreted_at=None
            )

    def test_rejects_naive_interpreted_at(self):
        with pytest.raises(InvalidInterpretedAtError):
            Interpretation.capture(
                observation_id=_OBSERVATION_ID,
                statement=_STATEMENT,
                interpreted_at=datetime(2026, 7, 13, 9, 0, 0),
            )

    def test_requires_an_observation_id(self):
        with pytest.raises(TypeError):
            Interpretation.capture(statement=_STATEMENT, interpreted_at=_INTERPRETED_AT)

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Interpretation.capture(observation_id=_OBSERVATION_ID, interpreted_at=_INTERPRETED_AT)


class TestInterpretationImmutability:
    def test_is_frozen(self):
        interpretation = Interpretation.capture(
            observation_id=_OBSERVATION_ID, statement=_STATEMENT, interpreted_at=_INTERPRETED_AT
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            interpretation.statement = Statement("changed")

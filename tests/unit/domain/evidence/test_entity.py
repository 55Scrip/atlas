"""Tests for the Evidence aggregate root (API-005 Evidence Capture)."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.exceptions import InvalidDirectionError, InvalidObservedAtError
from atlas.core.domain.evidence.value_objects import Direction, Statement
from atlas.core.domain.observation.value_objects import ObservationId

_STATEMENT = Statement(
    "Order intake increased by 24 percent and management raised full-year "
    "guidance for the second consecutive quarter."
)
_OBSERVED_AT = datetime(2026, 7, 13, 9, 15, 0, tzinfo=timezone(timedelta(hours=2)))
_OBSERVATION_ID = ObservationId()


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestEvidenceCapture:
    def test_captures_the_given_fields(self):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
        )
        assert evidence.observation_id == _OBSERVATION_ID
        assert evidence.statement == _STATEMENT
        assert evidence.direction == Direction.SUPPORTS
        assert evidence.observed_at == _OBSERVED_AT

    def test_supports_is_accepted(self):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction="SUPPORTS",
            observed_at=_OBSERVED_AT,
        )
        assert evidence.direction == Direction.SUPPORTS

    def test_challenges_is_accepted(self):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction="CHALLENGES",
            observed_at=_OBSERVED_AT,
        )
        assert evidence.direction == Direction.CHALLENGES

    def test_rejects_invalid_direction(self):
        with pytest.raises(InvalidDirectionError):
            Evidence.capture(
                observation_id=_OBSERVATION_ID,
                statement=_STATEMENT,
                direction="PROVES",
                observed_at=_OBSERVED_AT,
            )

    def test_assigns_a_fresh_id(self):
        first = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
        )
        second = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
        )
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 13, 17, 16, tzinfo=timezone.utc)
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
            clock=_fixed_clock(now),
        )
        assert evidence.recorded_at == now

    def test_observed_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 7, 13, 17, 16, tzinfo=timezone.utc)
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
            clock=_fixed_clock(now_utc),
        )
        assert evidence.observed_at.utcoffset() == timedelta(hours=2)
        assert evidence.observed_at.isoformat() == "2026-07-13T09:15:00+02:00"
        assert evidence.recorded_at.utcoffset() == timedelta(0)

    def test_optional_fields_default_to_none(self):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
        )
        assert evidence.source is None
        assert evidence.note is None

    def test_accepts_source_and_note(self):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
            source="Quarterly earnings report",
            note="The comparison benefits from a weak prior-year period.",
        )
        assert evidence.source == "Quarterly earnings report"
        assert evidence.note == "The comparison benefits from a weak prior-year period."

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_source_normalizes_to_none(self, blank):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
            source=blank,
        )
        assert evidence.source is None

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
            note=blank,
        )
        assert evidence.note is None

    def test_source_and_note_are_stripped_not_just_kept(self):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
            source="  Financial Times  ",
            note="  keep an eye on this  ",
        )
        assert evidence.source == "Financial Times"
        assert evidence.note == "keep an eye on this"

    def test_rejects_missing_observed_at(self):
        with pytest.raises(InvalidObservedAtError):
            Evidence.capture(
                observation_id=_OBSERVATION_ID,
                statement=_STATEMENT,
                direction=Direction.SUPPORTS,
                observed_at=None,
            )

    def test_rejects_naive_observed_at(self):
        with pytest.raises(InvalidObservedAtError):
            Evidence.capture(
                observation_id=_OBSERVATION_ID,
                statement=_STATEMENT,
                direction=Direction.SUPPORTS,
                observed_at=datetime(2026, 7, 13, 9, 15, 0),
            )

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Evidence.capture(
                observation_id=_OBSERVATION_ID,
                direction=Direction.SUPPORTS,
                observed_at=_OBSERVED_AT,
            )

    def test_requires_a_direction(self):
        with pytest.raises(TypeError):
            Evidence.capture(
                observation_id=_OBSERVATION_ID, statement=_STATEMENT, observed_at=_OBSERVED_AT
            )

    def test_requires_an_observation_id(self):
        with pytest.raises(TypeError):
            Evidence.capture(
                statement=_STATEMENT, direction=Direction.SUPPORTS, observed_at=_OBSERVED_AT
            )


class TestEvidenceImmutability:
    def test_is_frozen(self):
        evidence = Evidence.capture(
            observation_id=_OBSERVATION_ID,
            statement=_STATEMENT,
            direction=Direction.SUPPORTS,
            observed_at=_OBSERVED_AT,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            evidence.statement = Statement("changed")

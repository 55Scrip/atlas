"""Tests for the Observation aggregate root (API-003 Observation Capture)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.exceptions import InvalidObservedAtError
from atlas.core.domain.observation.value_objects import Statement, Subject

_SUBJECT = Subject("Semiconductor sector")
_STATEMENT = Statement(
    "Several semiconductor companies raised capital expenditure guidance "
    "during the same reporting period."
)
_OBSERVED_AT = datetime(2026, 7, 13, 10, 30, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestObservationCapture:
    def test_captures_the_given_fields(self):
        observation = Observation.capture(
            subject=_SUBJECT, statement=_STATEMENT, observed_at=_OBSERVED_AT
        )
        assert observation.subject == _SUBJECT
        assert observation.statement == _STATEMENT
        assert observation.observed_at == _OBSERVED_AT

    def test_assigns_a_fresh_id(self):
        first = Observation.capture(
            subject=_SUBJECT, statement=_STATEMENT, observed_at=_OBSERVED_AT
        )
        second = Observation.capture(
            subject=_SUBJECT, statement=_STATEMENT, observed_at=_OBSERVED_AT
        )
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 13, 17, 30, tzinfo=timezone.utc)
        observation = Observation.capture(
            subject=_SUBJECT,
            statement=_STATEMENT,
            observed_at=_OBSERVED_AT,
            clock=_fixed_clock(now),
        )
        assert observation.recorded_at == now

    def test_observed_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 7, 13, 17, 30, tzinfo=timezone.utc)
        observation = Observation.capture(
            subject=_SUBJECT,
            statement=_STATEMENT,
            observed_at=_OBSERVED_AT,
            clock=_fixed_clock(now_utc),
        )
        assert observation.observed_at.utcoffset() == timedelta(hours=2)
        assert observation.observed_at.isoformat() == "2026-07-13T10:30:00+02:00"
        assert observation.recorded_at.utcoffset() == timedelta(0)

    def test_optional_fields_default_to_none(self):
        observation = Observation.capture(
            subject=_SUBJECT, statement=_STATEMENT, observed_at=_OBSERVED_AT
        )
        assert observation.source is None
        assert observation.note is None

    def test_accepts_source_and_note(self):
        observation = Observation.capture(
            subject=_SUBJECT,
            statement=_STATEMENT,
            observed_at=_OBSERVED_AT,
            source="Quarterly earnings reports",
            note="Follow whether equipment suppliers report the same pattern.",
        )
        assert observation.source == "Quarterly earnings reports"
        assert observation.note == "Follow whether equipment suppliers report the same pattern."

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_source_normalizes_to_none(self, blank):
        observation = Observation.capture(
            subject=_SUBJECT, statement=_STATEMENT, observed_at=_OBSERVED_AT, source=blank
        )
        assert observation.source is None

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        observation = Observation.capture(
            subject=_SUBJECT, statement=_STATEMENT, observed_at=_OBSERVED_AT, note=blank
        )
        assert observation.note is None

    def test_source_and_note_are_stripped_not_just_kept(self):
        observation = Observation.capture(
            subject=_SUBJECT,
            statement=_STATEMENT,
            observed_at=_OBSERVED_AT,
            source="  Financial Times  ",
            note="  keep watching  ",
        )
        assert observation.source == "Financial Times"
        assert observation.note == "keep watching"

    def test_rejects_missing_observed_at(self):
        with pytest.raises(InvalidObservedAtError):
            Observation.capture(subject=_SUBJECT, statement=_STATEMENT, observed_at=None)

    def test_rejects_naive_observed_at(self):
        with pytest.raises(InvalidObservedAtError):
            Observation.capture(
                subject=_SUBJECT,
                statement=_STATEMENT,
                observed_at=datetime(2026, 7, 13, 10, 30, 0),
            )

    def test_requires_a_subject(self):
        with pytest.raises(TypeError):
            Observation.capture(statement=_STATEMENT, observed_at=_OBSERVED_AT)

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Observation.capture(subject=_SUBJECT, observed_at=_OBSERVED_AT)


class TestObservationImmutability:
    def test_is_frozen(self):
        observation = Observation.capture(
            subject=_SUBJECT, statement=_STATEMENT, observed_at=_OBSERVED_AT
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            observation.statement = Statement("changed")

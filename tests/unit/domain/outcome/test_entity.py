"""Tests for the Outcome aggregate root (ATLAS-001 Core Loop)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.exceptions import InvalidOccurredAtError
from atlas.core.domain.outcome.value_objects import Statement

_DECISION_ID = DecisionId()
_STATEMENT = Statement("Revenue growth accelerated as expected.")
_OCCURRED_AT = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestOutcomeCapture:
    def test_captures_the_given_fields(self):
        outcome = Outcome.capture(
            decision_id=_DECISION_ID, statement=_STATEMENT, occurred_at=_OCCURRED_AT
        )
        assert outcome.decision_id == _DECISION_ID
        assert outcome.statement == _STATEMENT
        assert outcome.occurred_at == _OCCURRED_AT

    def test_assigns_a_fresh_id(self):
        first = Outcome.capture(
            decision_id=_DECISION_ID, statement=_STATEMENT, occurred_at=_OCCURRED_AT
        )
        second = Outcome.capture(
            decision_id=_DECISION_ID, statement=_STATEMENT, occurred_at=_OCCURRED_AT
        )
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
        outcome = Outcome.capture(
            decision_id=_DECISION_ID,
            statement=_STATEMENT,
            occurred_at=_OCCURRED_AT,
            clock=_fixed_clock(now),
        )
        assert outcome.recorded_at == now

    def test_occurred_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
        outcome = Outcome.capture(
            decision_id=_DECISION_ID,
            statement=_STATEMENT,
            occurred_at=_OCCURRED_AT,
            clock=_fixed_clock(now_utc),
        )
        assert outcome.occurred_at.utcoffset() == timedelta(hours=2)
        assert outcome.occurred_at.isoformat() == "2026-10-01T12:00:00+02:00"
        assert outcome.recorded_at.utcoffset() == timedelta(0)

    def test_note_defaults_to_none(self):
        outcome = Outcome.capture(
            decision_id=_DECISION_ID, statement=_STATEMENT, occurred_at=_OCCURRED_AT
        )
        assert outcome.note is None

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        outcome = Outcome.capture(
            decision_id=_DECISION_ID, statement=_STATEMENT, occurred_at=_OCCURRED_AT, note=blank
        )
        assert outcome.note is None

    def test_rejects_missing_occurred_at(self):
        with pytest.raises(InvalidOccurredAtError):
            Outcome.capture(decision_id=_DECISION_ID, statement=_STATEMENT, occurred_at=None)

    def test_rejects_naive_occurred_at(self):
        with pytest.raises(InvalidOccurredAtError):
            Outcome.capture(
                decision_id=_DECISION_ID,
                statement=_STATEMENT,
                occurred_at=datetime(2026, 10, 1, 12, 0, 0),
            )

    def test_requires_a_decision_id(self):
        with pytest.raises(TypeError):
            Outcome.capture(statement=_STATEMENT, occurred_at=_OCCURRED_AT)

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Outcome.capture(decision_id=_DECISION_ID, occurred_at=_OCCURRED_AT)


class TestOutcomeImmutability:
    def test_is_frozen(self):
        outcome = Outcome.capture(
            decision_id=_DECISION_ID, statement=_STATEMENT, occurred_at=_OCCURRED_AT
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            outcome.statement = Statement("changed")

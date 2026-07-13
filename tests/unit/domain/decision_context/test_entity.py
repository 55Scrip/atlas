"""Tests for the DecisionContext aggregate root (API-002 Decision Context)."""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.entity import DecisionContext
from atlas.core.domain.decision_context.exceptions import InvalidCapturedAtError
from atlas.core.domain.decision_context.value_objects import (
    AlternativesConsidered,
    Situation,
    Uncertainties,
)

_DECISION_ID = DecisionId(uuid.uuid4())
_SITUATION = Situation(
    "The portfolio already had large exposure to semiconductors, the position "
    "was small, and I wanted to preserve cash before the Fed announcement."
)
_CAPTURED_AT = datetime(2026, 6, 17, 0, 54, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestDecisionContextCapture:
    def test_captures_the_given_fields(self):
        context = DecisionContext.capture(
            decision_id=_DECISION_ID,
            situation=_SITUATION,
            captured_at=_CAPTURED_AT,
        )
        assert context.decision_id == _DECISION_ID
        assert context.situation == _SITUATION
        assert context.captured_at == _CAPTURED_AT

    def test_assigns_a_fresh_context_id(self):
        first = DecisionContext.capture(
            decision_id=_DECISION_ID, situation=_SITUATION, captured_at=_CAPTURED_AT
        )
        second = DecisionContext.capture(
            decision_id=_DECISION_ID, situation=_SITUATION, captured_at=_CAPTURED_AT
        )
        assert first.context_id != second.context_id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 13, tzinfo=timezone.utc)
        context = DecisionContext.capture(
            decision_id=_DECISION_ID,
            situation=_SITUATION,
            captured_at=_CAPTURED_AT,
            clock=_fixed_clock(now),
        )
        assert context.recorded_at == now

    def test_captured_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 7, 13, tzinfo=timezone.utc)
        context = DecisionContext.capture(
            decision_id=_DECISION_ID,
            situation=_SITUATION,
            captured_at=_CAPTURED_AT,
            clock=_fixed_clock(now_utc),
        )
        assert context.captured_at.utcoffset() == timedelta(hours=2)
        assert context.captured_at.isoformat() == "2026-06-17T00:54:00+02:00"
        assert context.recorded_at.utcoffset() == timedelta(0)

    def test_optional_fields_default_to_none_and_empty_collections(self):
        context = DecisionContext.capture(
            decision_id=_DECISION_ID, situation=_SITUATION, captured_at=_CAPTURED_AT
        )
        assert context.portfolio_relevance is None
        assert context.capital_considerations is None
        assert context.alternatives_considered == AlternativesConsidered()
        assert context.uncertainties == Uncertainties()

    def test_accepts_all_optional_fields(self):
        context = DecisionContext.capture(
            decision_id=_DECISION_ID,
            situation=_SITUATION,
            captured_at=_CAPTURED_AT,
            portfolio_relevance="Portfolio lacked real-estate exposure",
            capital_considerations="Did not want to invest too much at once",
            alternatives_considered=AlternativesConsidered(("Buy Arm",)),
            uncertainties=Uncertainties(("Market reaction to the Fed announcement",)),
        )
        assert context.portfolio_relevance == "Portfolio lacked real-estate exposure"
        assert context.capital_considerations == "Did not want to invest too much at once"
        assert list(context.alternatives_considered) == ["Buy Arm"]
        assert list(context.uncertainties) == ["Market reaction to the Fed announcement"]

    def test_rejects_missing_captured_at(self):
        with pytest.raises(InvalidCapturedAtError):
            DecisionContext.capture(
                decision_id=_DECISION_ID, situation=_SITUATION, captured_at=None
            )

    def test_rejects_naive_captured_at(self):
        with pytest.raises(InvalidCapturedAtError):
            DecisionContext.capture(
                decision_id=_DECISION_ID,
                situation=_SITUATION,
                captured_at=datetime(2026, 6, 17, 0, 54, 0),
            )

    def test_requires_a_decision_id(self):
        with pytest.raises(TypeError):
            DecisionContext.capture(situation=_SITUATION, captured_at=_CAPTURED_AT)

    def test_requires_a_situation(self):
        with pytest.raises(TypeError):
            DecisionContext.capture(decision_id=_DECISION_ID, captured_at=_CAPTURED_AT)


class TestDecisionContextImmutability:
    def test_is_frozen(self):
        context = DecisionContext.capture(
            decision_id=_DECISION_ID, situation=_SITUATION, captured_at=_CAPTURED_AT
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            context.situation = Situation("changed")

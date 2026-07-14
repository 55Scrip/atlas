"""Tests for the ReflectionExploration read model (ATLAS-012)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from atlas.core.application.reflection_exploration.exploration import ReflectionExploration
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ResponseText,
)

_T0 = datetime(2026, 7, 23, 9, 0, 0, tzinfo=timezone.utc)


def _make_response(recorded_at: datetime) -> ReflectionResponse:
    decision_id = DecisionId()
    return ReflectionResponse.register(
        decision_id=decision_id,
        response_text=ResponseText("Keeping this."),
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
            reasoning_context_confidence=None,
        ),
        clock=lambda: recorded_at,
    )


class TestReflectionExploration:
    def test_holds_its_entries(self):
        first = _make_response(_T0)
        second = _make_response(_T0.replace(hour=15))

        exploration = ReflectionExploration(entries=(first, second))

        assert exploration.entries == (first, second)

    def test_empty_entries_is_valid(self):
        exploration = ReflectionExploration(entries=())
        assert exploration.entries == ()

    def test_is_immutable(self):
        exploration = ReflectionExploration(entries=())

        with pytest.raises(dataclasses.FrozenInstanceError):
            exploration.entries = (_make_response(_T0),)  # type: ignore[misc]

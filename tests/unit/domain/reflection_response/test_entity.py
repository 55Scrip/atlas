"""Tests for the ReflectionResponse aggregate root (ATLAS-009)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ResponseText,
)

_DECISION_ID = DecisionId()
_RESPONSE_TEXT = ResponseText("This time feels different because guidance keeps beating.")
_PROVENANCE = ProvenanceSnapshot(
    reflection_description="You have made 2 BUY decisions on NVIDIA.",
    coaching_question_text=(
        "What's similar or different about this situation compared with "
        "what you just saw, if anything?"
    ),
    grounding_pattern=PatternMembershipSnapshot(
        strategy_name="same_subject_and_type", member_decision_ids=(DecisionId(), DecisionId())
    ),
    strategy_signature_patterns=(),
    reasoning_context_subject="NVIDIA",
    reasoning_context_decision_type="BUY",
    reasoning_context_confidence=None,
)


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestReflectionResponseRegister:
    def test_captures_the_given_fields(self):
        response = ReflectionResponse.register(
            decision_id=_DECISION_ID, response_text=_RESPONSE_TEXT, provenance=_PROVENANCE
        )
        assert response.decision_id == _DECISION_ID
        assert response.response_text == _RESPONSE_TEXT
        assert response.provenance == _PROVENANCE

    def test_assigns_a_fresh_id(self):
        first = ReflectionResponse.register(
            decision_id=_DECISION_ID, response_text=_RESPONSE_TEXT, provenance=_PROVENANCE
        )
        second = ReflectionResponse.register(
            decision_id=_DECISION_ID, response_text=_RESPONSE_TEXT, provenance=_PROVENANCE
        )
        assert first.id != second.id

    def test_recorded_at_comes_from_the_clock(self):
        now = datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc)
        response = ReflectionResponse.register(
            decision_id=_DECISION_ID,
            response_text=_RESPONSE_TEXT,
            provenance=_PROVENANCE,
            clock=_fixed_clock(now),
        )
        assert response.recorded_at == now

    def test_is_immutable(self):
        response = ReflectionResponse.register(
            decision_id=_DECISION_ID, response_text=_RESPONSE_TEXT, provenance=_PROVENANCE
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            response.decision_id = DecisionId()  # type: ignore[misc]

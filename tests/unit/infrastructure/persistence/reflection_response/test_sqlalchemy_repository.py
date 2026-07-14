"""Tests for SqlAlchemyReflectionResponseRepository (ATLAS-009).

Round-trip proof, including the JSON-encoded nested provenance fields
and verbatim text preservation through a real database write/read.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ResponseText,
)
from atlas.core.infrastructure.persistence.reflection_response.sqlalchemy_repository import (
    SqlAlchemyReflectionResponseRepository,
)
from atlas.core.infrastructure.persistence.reflection_response.table import (
    create_reflection_response_table,
)

_RECORDED_AT = datetime(2026, 7, 17, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_reflection_response_table(eng)
    return eng


@pytest.fixture
def repository(engine):
    return SqlAlchemyReflectionResponseRepository(engine)


def _make_response(decision_id, response_text_value, strategy_signature_patterns=()):
    return ReflectionResponse.register(
        decision_id=decision_id,
        response_text=ResponseText(response_text_value),
        provenance=ProvenanceSnapshot(
            reflection_description="You have made 2 BUY decisions on NVIDIA.",
            coaching_question_text=(
                "What's similar or different about this situation compared "
                "with what you just saw, if anything?"
            ),
            grounding_pattern=PatternMembershipSnapshot(
                strategy_name="same_subject_and_type",
                member_decision_ids=(DecisionId(), DecisionId()),
            ),
            strategy_signature_patterns=strategy_signature_patterns,
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=None,
        ),
        clock=lambda: _RECORDED_AT,
    )


class TestRoundTrip:
    def test_add_then_get_returns_an_equal_entity(self, repository):
        decision_id = DecisionId()
        response = _make_response(decision_id, "  This time feels DIFFERENT!  ")

        repository.add(response)
        retrieved = repository.get(response.id)

        assert retrieved == response

    def test_response_text_round_trips_verbatim(self, repository):
        decision_id = DecisionId()
        weird_text = "  Multiple   spaces, Mixed CASE, punctuation?! ...yes.  "
        response = _make_response(decision_id, weird_text)

        repository.add(response)
        retrieved = repository.get(response.id)

        assert retrieved.response_text.value == weird_text

    def test_strategy_signature_patterns_round_trip(self, repository):
        decision_id = DecisionId()
        signature_pattern = PatternMembershipSnapshot(
            strategy_name="same_confidence", member_decision_ids=(DecisionId(),)
        )
        response = _make_response(
            decision_id, "Keeping this.", strategy_signature_patterns=(signature_pattern,)
        )

        repository.add(response)
        retrieved = repository.get(response.id)

        assert retrieved.provenance.strategy_signature_patterns == (signature_pattern,)

    def test_get_returns_none_for_unknown_id(self, repository):
        from atlas.core.domain.reflection_response.value_objects import ReflectionResponseId

        assert repository.get(ReflectionResponseId()) is None

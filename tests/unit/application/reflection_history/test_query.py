"""Tests for ReflectionHistoryQuery (ATLAS-010).

Constructs ReflectionHistoryQuery directly from a fake repository — no
composition.py, no Engine — proving assembly is independently testable
and that the query, not the repository, owns final ordering.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from atlas.core.application.reflection_history.query import ReflectionHistoryQuery
from atlas.core.domain.decision.value_objects import DecisionId, UserId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ResponseText,
)

_T0 = datetime(2026, 7, 21, 9, 0, 0, tzinfo=timezone.utc)


class _FakeReflectionResponseRepository:
    """Implements only list_all_for_owner — the one method
    ReflectionHistoryQuery actually calls — and records what it was
    called with."""

    def __init__(self, responses):
        self._responses = responses
        self.requested_owner_user_id = None

    def list_all_for_owner(self, user_id: UserId) -> list[ReflectionResponse]:
        self.requested_owner_user_id = user_id
        return list(self._responses)


def _make_response(
    recorded_at: datetime, response_id_seed: int | None = None
) -> ReflectionResponse:
    response = ReflectionResponse.register(
        decision_id=DecisionId(),
        response_text=ResponseText("Keeping this."),
        provenance=ProvenanceSnapshot(
            reflection_description="You have made 2 BUY decisions on NVIDIA.",
            coaching_question_text="What's similar or different this time?",
            grounding_pattern=PatternMembershipSnapshot(
                strategy_name="same_subject_and_type",
                member_decision_ids=(DecisionId(),),
            ),
            strategy_signature_patterns=(),
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=None,
        ),
        clock=lambda: recorded_at,
    )
    if response_id_seed is not None:
        # Force a deterministic id ordering for the tie-break test below.
        import dataclasses

        response = dataclasses.replace(
            response, id=type(response.id)(uuid.UUID(int=response_id_seed))
        )
    return response


class TestEmptyHistory:
    def test_empty_repository_returns_empty_history(self):
        query = ReflectionHistoryQuery(
            repository=_FakeReflectionResponseRepository([]),
            owner_user_id=UserId(uuid.uuid4()),
        )

        history = query.build()

        assert history.entries == ()


class TestDeterministicOrdering:
    def test_out_of_order_repository_results_are_sorted_ascending_by_recorded_at(self):
        earliest = _make_response(_T0)
        latest = _make_response(_T0.replace(hour=15))
        repository = _FakeReflectionResponseRepository([latest, earliest])
        query = ReflectionHistoryQuery(repository=repository, owner_user_id=UserId(uuid.uuid4()))

        history = query.build()

        assert history.entries == (earliest, latest)

    def test_equal_recorded_at_breaks_the_tie_by_ascending_id_value(self):
        lower_id_response = _make_response(_T0, response_id_seed=1)
        higher_id_response = _make_response(_T0, response_id_seed=2)
        repository = _FakeReflectionResponseRepository(
            [higher_id_response, lower_id_response]
        )
        query = ReflectionHistoryQuery(repository=repository, owner_user_id=UserId(uuid.uuid4()))

        history = query.build()

        assert history.entries == (lower_id_response, higher_id_response)


class TestOwnerScoping:
    def test_only_the_injected_owner_is_ever_requested_from_the_repository(self):
        owner_user_id = UserId(uuid.uuid4())
        repository = _FakeReflectionResponseRepository([])
        query = ReflectionHistoryQuery(repository=repository, owner_user_id=owner_user_id)

        query.build()

        assert repository.requested_owner_user_id == owner_user_id

"""Tests for ReflectionComparisonQuery (ATLAS-011).

Constructs the query directly from a plain ReflectionHistory value — no
Engine, no repository, no fake needed — proving the query is a pure,
dependency-free in-memory operation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from atlas.core.application.reflection_comparison.exceptions import (
    DuplicateReflectionResponseSelectionError,
    ReflectionResponseNotOwnedError,
)
from atlas.core.application.reflection_comparison.query import ReflectionComparisonQuery
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ReflectionResponseId,
    ResponseText,
)

_T0 = datetime(2026, 7, 22, 9, 0, 0, tzinfo=timezone.utc)


def _make_response(
    recorded_at: datetime,
    text: str = "Keeping this.",
    strategy_signature_patterns=(),
) -> ReflectionResponse:
    decision_id = DecisionId()
    return ReflectionResponse.register(
        decision_id=decision_id,
        response_text=ResponseText(text),
        provenance=ProvenanceSnapshot(
            reflection_description="You have made 2 BUY decisions on NVIDIA.",
            coaching_question_text="What's similar or different this time?",
            grounding_pattern=PatternMembershipSnapshot(
                strategy_name="same_subject_and_type",
                member_decision_ids=(decision_id,),
            ),
            strategy_signature_patterns=strategy_signature_patterns,
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=80,
        ),
        clock=lambda: recorded_at,
    )


class TestValidSelection:
    def test_two_distinct_owned_ids_produce_a_comparison(self):
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(earlier, later))
        query = ReflectionComparisonQuery(history)

        comparison = query.build(earlier.id, later.id)

        assert comparison.first == earlier
        assert comparison.second == later

    def test_ordering_is_independent_of_input_order(self):
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(earlier, later))
        query = ReflectionComparisonQuery(history)

        # Selecting the later one first, then the earlier one.
        comparison = query.build(later.id, earlier.id)

        assert comparison.first == earlier
        assert comparison.second == later

    def test_equal_recorded_at_breaks_the_tie_by_ascending_id_value(self):
        lower = _make_response(_T0)
        higher = _make_response(_T0)
        object.__setattr__(lower, "id", ReflectionResponseId(uuid.UUID(int=1)))
        object.__setattr__(higher, "id", ReflectionResponseId(uuid.UUID(int=2)))
        history = ReflectionHistory(entries=(higher, lower))
        query = ReflectionComparisonQuery(history)

        comparison = query.build(higher.id, lower.id)

        assert comparison.first == lower
        assert comparison.second == higher

    def test_full_provenance_is_returned_exactly_as_persisted_no_projection(self):
        signature_pattern = PatternMembershipSnapshot(
            strategy_name="same_confidence", member_decision_ids=(DecisionId(),)
        )
        first = _make_response(_T0, strategy_signature_patterns=(signature_pattern,))
        second = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(first, second))
        query = ReflectionComparisonQuery(history)

        comparison = query.build(first.id, second.id)

        assert comparison.first is first
        assert comparison.first.provenance == first.provenance
        assert comparison.first.provenance.strategy_signature_patterns == (signature_pattern,)
        assert comparison.second is second
        assert comparison.second.provenance == second.provenance


class TestInvalidSelection:
    def test_selecting_the_same_response_twice_raises(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionComparisonQuery(history)

        with pytest.raises(DuplicateReflectionResponseSelectionError):
            query.build(entry.id, entry.id)

    def test_an_id_absent_from_history_raises_not_owned(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionComparisonQuery(history)
        nonexistent_id = ReflectionResponseId()

        with pytest.raises(ReflectionResponseNotOwnedError):
            query.build(entry.id, nonexistent_id)

    def test_an_id_belonging_to_a_different_owner_is_indistinguishable_from_nonexistent(self):
        # Simulates what a future multi-investor store might contain: a
        # Reflection Response that exists, but was never included in
        # *this* investor's own owner-scoped ReflectionHistory. From
        # ReflectionComparisonQuery's point of view this must be
        # completely indistinguishable from an id that doesn't exist at
        # all — both raise the same exception, with the same message.
        owned_entry = _make_response(_T0)
        other_owners_entry = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(owned_entry,))  # other owner's entry excluded
        query = ReflectionComparisonQuery(history)

        with pytest.raises(ReflectionResponseNotOwnedError):
            query.build(owned_entry.id, other_owners_entry.id)

    def test_both_ids_absent_raises_not_owned(self):
        history = ReflectionHistory(entries=())
        query = ReflectionComparisonQuery(history)

        with pytest.raises(ReflectionResponseNotOwnedError):
            query.build(ReflectionResponseId(), ReflectionResponseId())

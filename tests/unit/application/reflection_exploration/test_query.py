"""Tests for ReflectionExplorationQuery (ATLAS-012).

Constructs the query directly from a plain ReflectionHistory value — no
Engine, no repository, no fake needed — proving the query is a pure,
dependency-free in-memory operation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from atlas.core.application.reflection_exploration.exceptions import (
    UnreachableReflectionResponseError,
)
from atlas.core.application.reflection_exploration.query import ReflectionExplorationQuery
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ReflectionResponseId,
    ResponseText,
)

_T0 = datetime(2026, 7, 23, 9, 0, 0, tzinfo=timezone.utc)


def _make_response(recorded_at: datetime, text: str = "Keeping this.") -> ReflectionResponse:
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
            strategy_signature_patterns=(),
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=80,
        ),
        clock=lambda: recorded_at,
    )


class TestEmptySelection:
    def test_empty_selection_produces_an_empty_exploration(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionExplorationQuery(history)

        exploration = query.build(())

        assert exploration.entries == ()


class TestValidSelection:
    def test_a_single_selected_id_produces_a_one_member_scope(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionExplorationQuery(history)

        exploration = query.build((entry.id,))

        assert exploration.entries == (entry,)

    def test_several_selected_ids_are_all_included(self):
        a = _make_response(_T0)
        b = _make_response(_T0.replace(hour=12))
        c = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(a, b, c))
        query = ReflectionExplorationQuery(history)

        exploration = query.build((a.id, b.id, c.id))

        assert set(entry.id for entry in exploration.entries) == {a.id, b.id, c.id}

    def test_ordering_is_independent_of_input_order(self):
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(earlier, later))
        query = ReflectionExplorationQuery(history)

        exploration = query.build((later.id, earlier.id))

        assert exploration.entries == (earlier, later)

    def test_equal_recorded_at_breaks_the_tie_by_ascending_id_value(self):
        lower = _make_response(_T0)
        higher = _make_response(_T0)
        object.__setattr__(lower, "id", ReflectionResponseId(uuid.UUID(int=1)))
        object.__setattr__(higher, "id", ReflectionResponseId(uuid.UUID(int=2)))
        history = ReflectionHistory(entries=(higher, lower))
        query = ReflectionExplorationQuery(history)

        exploration = query.build((higher.id, lower.id))

        assert exploration.entries == (lower, higher)

    def test_full_provenance_is_returned_exactly_as_persisted_no_projection(self):
        signature_pattern = PatternMembershipSnapshot(
            strategy_name="same_confidence", member_decision_ids=(DecisionId(),)
        )
        entry = ReflectionResponse.register(
            decision_id=DecisionId(),
            response_text=ResponseText("Keeping this."),
            provenance=ProvenanceSnapshot(
                reflection_description="You have made 2 BUY decisions on NVIDIA.",
                coaching_question_text="What's similar or different this time?",
                grounding_pattern=PatternMembershipSnapshot(
                    strategy_name="same_subject_and_type",
                    member_decision_ids=(DecisionId(),),
                ),
                strategy_signature_patterns=(signature_pattern,),
                reasoning_context_subject="NVIDIA",
                reasoning_context_decision_type="BUY",
                reasoning_context_confidence=80,
            ),
            clock=lambda: _T0,
        )
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionExplorationQuery(history)

        exploration = query.build((entry.id,))

        assert exploration.entries[0] is entry
        assert exploration.entries[0].provenance == entry.provenance
        assert exploration.entries[0].provenance.strategy_signature_patterns == (
            signature_pattern,
        )


class TestDuplicateSelectionSemantics:
    def test_duplicate_ids_are_silently_deduplicated_no_exception(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionExplorationQuery(history)

        exploration = query.build((entry.id, entry.id, entry.id))

        assert exploration.entries == (entry,)

    def test_duplicates_mixed_with_other_selections_appear_at_most_once(self):
        a = _make_response(_T0)
        b = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(a, b))
        query = ReflectionExplorationQuery(history)

        exploration = query.build((a.id, b.id, a.id))

        assert exploration.entries == (a, b)
        assert len(exploration.entries) == 2


class TestUnreachableSelection:
    def test_a_nonexistent_id_fails_the_entire_request(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionExplorationQuery(history)
        nonexistent_id = ReflectionResponseId()

        with pytest.raises(UnreachableReflectionResponseError):
            query.build((entry.id, nonexistent_id))

    def test_an_id_belonging_to_a_different_owner_is_indistinguishable_from_nonexistent(self):
        # Simulates what a future multi-investor store might contain: a
        # Reflection Response that exists, but was never included in
        # *this* investor's own owner-scoped ReflectionHistory.
        owned_entry = _make_response(_T0)
        other_owners_entry = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(owned_entry,))  # other owner's entry excluded
        query = ReflectionExplorationQuery(history)

        with pytest.raises(UnreachableReflectionResponseError):
            query.build((owned_entry.id, other_owners_entry.id))

    def test_no_partial_scope_is_returned_when_one_of_several_ids_is_unreachable(self):
        a = _make_response(_T0)
        b = _make_response(_T0.replace(hour=12))
        history = ReflectionHistory(entries=(a, b))
        query = ReflectionExplorationQuery(history)
        nonexistent_id = ReflectionResponseId()

        # Even though a.id and b.id are both valid, the presence of one
        # unreachable id must fail the whole request — never silently
        # narrowing to {a, b}.
        with pytest.raises(UnreachableReflectionResponseError):
            query.build((a.id, b.id, nonexistent_id))


class TestInputImmutability:
    def test_history_and_entries_are_unchanged_after_a_successful_build(self):
        a = _make_response(_T0)
        b = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(a, b))
        query = ReflectionExplorationQuery(history)

        query.build((a.id,))

        assert history.entries == (a, b)
        assert history.entries[0] is a
        assert history.entries[1] is b

    def test_history_and_entries_are_unchanged_after_a_failed_build(self):
        a = _make_response(_T0)
        b = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(a, b))
        query = ReflectionExplorationQuery(history)

        with pytest.raises(UnreachableReflectionResponseError):
            query.build((a.id, ReflectionResponseId()))

        assert history.entries == (a, b)
        assert history.entries[0] is a
        assert history.entries[1] is b

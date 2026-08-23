"""Tests for the CaseCondition aggregate root (ADR-CC-001):
`CaseConditionEvent` construction/immutability, `is_terminal`, and the
`reconstruct_current_state` projection.
"""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone

import pytest

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.entity import (
    CaseConditionEvent,
    is_terminal,
    reconstruct_current_state,
)
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.value_objects import DecisionId

_CASE_ID = CaseId()
_CONDITION_ID = CaseConditionId()


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestIsTerminal:
    def test_revised_and_evaluated_satisfied_are_not_terminal(self):
        assert is_terminal("revised") is False
        assert is_terminal("evaluated_satisfied") is False

    def test_superseded_and_retired_are_terminal(self):
        assert is_terminal("superseded") is True
        assert is_terminal("retired") is True


class TestCaseConditionEventRevised:
    def test_carries_the_given_content(self):
        event = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            predicate_text="China revenue trend",
            role="monitoring",
            authorship="atlas",
            structured_kind="threshold",
            threshold_metric="china_revenue_growth",
            threshold_operator="<",
            threshold_value=0.05,
            event_id="event-1",
        )
        assert event.event_type == "revised"
        assert event.predicate_text == "China revenue trend"
        assert event.role == "monitoring"
        assert event.authorship == "atlas"
        assert event.structured_kind == "threshold"
        assert event.threshold_operator == "<"
        assert event.threshold_value == 0.05

    def test_all_content_fields_default_to_none(self):
        event = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None, event_id="event-1"
        )
        assert event.predicate_text is None
        assert event.role is None
        assert event.structured_kind is None

    def test_recorded_at_comes_from_the_given_clock(self):
        now = datetime(2026, 7, 13, tzinfo=timezone.utc)
        event = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            event_id="event-1",
            clock=_fixed_clock(now),
        )
        assert event.recorded_at == now


class TestCaseConditionEventEvaluatedSatisfied:
    def test_carries_the_observed_value(self):
        event = CaseConditionEvent.evaluated_satisfied(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            observed_value=0.02,
            event_id="event-2",
        )
        assert event.event_type == "evaluated_satisfied"
        assert event.observed_value == 0.02
        assert event.predicate_text is None


class TestCaseConditionEventSuperseded:
    def test_carries_the_replacement_reference(self):
        event = CaseConditionEvent.superseded(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            superseded_by_condition_id="new-condition-id",
            event_id="event-3",
        )
        assert event.event_type == "superseded"
        assert event.superseded_by_condition_id == "new-condition-id"


class TestCaseConditionEventRetired:
    def test_carries_no_content(self):
        event = CaseConditionEvent.retired(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None, event_id="event-4"
        )
        assert event.event_type == "retired"
        assert event.superseded_by_condition_id is None


class TestCaseConditionEventImmutability:
    def test_is_frozen(self):
        event = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None, event_id="event-1"
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.predicate_text = "changed"


class TestReconstructCurrentState:
    def test_returns_none_for_an_empty_stream(self):
        assert reconstruct_current_state([]) is None

    def test_a_single_revision_yields_an_active_view(self):
        event = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            predicate_text="China revenue trend",
            role="monitoring",
            event_id="event-1",
        )
        view = reconstruct_current_state([event])
        assert view.status == "active"
        assert view.is_active is True
        assert view.predicate_text == "China revenue trend"
        assert view.created_at == event.recorded_at

    def test_decision_id_is_optional(self):
        decision_id = DecisionId(uuid.uuid4())
        event = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=decision_id, event_id="event-1"
        )
        view = reconstruct_current_state([event])
        assert view.decision_id == decision_id

    def test_evaluated_satisfied_status_still_shows_last_known_content(self):
        revision = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            predicate_text="China revenue trend",
            event_id="event-1",
            clock=_fixed_clock(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        )
        satisfied = CaseConditionEvent.evaluated_satisfied(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            observed_value=0.02,
            event_id="event-2",
            clock=_fixed_clock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        )
        view = reconstruct_current_state([revision, satisfied])
        assert view.status == "satisfied"
        assert view.is_active is True  # still active: not terminal
        assert view.predicate_text == "China revenue trend"
        assert view.last_observed_value == 0.02

    def test_superseded_status_is_not_active_and_shows_last_known_content(self):
        revision = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            predicate_text="China revenue trend",
            event_id="event-1",
        )
        superseded = CaseConditionEvent.superseded(
            condition_id=_CONDITION_ID,
            case_id=_CASE_ID,
            decision_id=None,
            superseded_by_condition_id="new-id",
            event_id="event-2",
        )
        view = reconstruct_current_state([revision, superseded])
        assert view.status == "superseded"
        assert view.is_active is False
        assert view.predicate_text == "China revenue trend"
        assert view.superseded_by_condition_id == "new-id"

    def test_retired_status_is_not_active(self):
        revision = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None, event_id="event-1"
        )
        retired = CaseConditionEvent.retired(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None, event_id="event-2"
        )
        view = reconstruct_current_state([revision, retired])
        assert view.status == "retired"
        assert view.is_active is False

    def test_last_observed_value_reflects_the_most_recent_evaluation(self):
        revision = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None, event_id="event-1"
        )
        first_eval = CaseConditionEvent.evaluated_satisfied(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None,
            observed_value=0.03, event_id="event-2",
        )
        second_revision = CaseConditionEvent.revised(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None, event_id="event-3"
        )
        second_eval = CaseConditionEvent.evaluated_satisfied(
            condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None,
            observed_value=0.01, event_id="event-4",
        )
        view = reconstruct_current_state([revision, first_eval, second_revision, second_eval])
        assert view.last_observed_value == 0.01

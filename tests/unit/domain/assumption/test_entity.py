"""Tests for the Assumption aggregate root (ADR-AS-001):
`AssumptionEvent` construction/immutability, `is_terminal`, and the
`reconstruct_current_state` projection.
"""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone

import pytest

from atlas.core.domain.assumption.entity import (
    AssumptionEvent,
    is_terminal,
    reconstruct_current_state,
)
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId

_CASE_ID = CaseId()
_DECISION_ID = DecisionId(uuid.uuid4())
_ASSUMPTION_ID = AssumptionId()


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestIsTerminal:
    def test_revised_and_challenged_are_not_terminal(self):
        assert is_terminal("revised") is False
        assert is_terminal("challenged") is False

    def test_superseded_and_retired_are_terminal(self):
        assert is_terminal("superseded") is True
        assert is_terminal("retired") is True


class TestAssumptionEventRevised:
    def test_carries_the_given_content(self):
        event = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID,
            decision_id=_DECISION_ID,
            case_id=_CASE_ID,
            statement="GCP margin expansion continues",
            authorship="atlas",
            linked_case_condition_ids=("cc-1",),
            event_id="event-1",
        )
        assert event.event_type == "revised"
        assert event.statement == "GCP margin expansion continues"
        assert event.authorship == "atlas"
        assert event.linked_case_condition_ids == ("cc-1",)

    def test_all_content_fields_default_to_none_or_empty(self):
        event = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-1"
        )
        assert event.statement is None
        assert event.authorship is None
        assert event.linked_case_condition_ids == ()

    def test_recorded_at_comes_from_the_given_clock(self):
        now = datetime(2026, 7, 13, tzinfo=timezone.utc)
        event = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            event_id="event-1", clock=_fixed_clock(now),
        )
        assert event.recorded_at == now


class TestAssumptionEventChallenged:
    def test_defaults_to_challenged_severity(self):
        event = AssumptionEvent.challenged(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-2"
        )
        assert event.event_type == "challenged"
        assert event.severity == "challenged"
        assert event.statement is None

    def test_carries_evidence_and_note(self):
        event = AssumptionEvent.challenged(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            evidence_id="ev-1", note="margins compressed", severity="invalidated",
            event_id="event-2",
        )
        assert event.evidence_id == "ev-1"
        assert event.note == "margins compressed"
        assert event.severity == "invalidated"


class TestAssumptionEventSuperseded:
    def test_carries_the_replacement_reference(self):
        event = AssumptionEvent.superseded(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            superseded_by_assumption_id="new-assumption-id", event_id="event-3",
        )
        assert event.event_type == "superseded"
        assert event.superseded_by_assumption_id == "new-assumption-id"


class TestAssumptionEventRetired:
    def test_carries_no_content(self):
        event = AssumptionEvent.retired(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-4"
        )
        assert event.event_type == "retired"
        assert event.statement is None


class TestAssumptionEventImmutability:
    def test_is_frozen(self):
        event = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-1"
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.statement = "changed"


class TestReconstructCurrentState:
    def test_returns_none_for_an_empty_stream(self):
        assert reconstruct_current_state([]) is None

    def test_a_single_revision_yields_a_supported_view(self):
        event = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            statement="GCP margin expansion continues", event_id="event-1",
        )
        view = reconstruct_current_state([event])
        assert view.status == "supported"
        assert view.is_active is True
        assert view.statement == "GCP margin expansion continues"
        assert view.decision_id == _DECISION_ID
        assert view.case_id == _CASE_ID
        assert view.created_at == event.recorded_at

    def test_challenged_severity_yields_challenged_status(self):
        revision = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            statement="GCP margin expansion continues", event_id="event-1",
            clock=_fixed_clock(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        )
        challenge = AssumptionEvent.challenged(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            severity="challenged", note="mixed signals", event_id="event-2",
            clock=_fixed_clock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        )
        view = reconstruct_current_state([revision, challenge])
        assert view.status == "challenged"
        assert view.is_active is True
        assert view.statement == "GCP margin expansion continues"  # last-known content
        assert view.last_challenge_note == "mixed signals"

    def test_invalidated_severity_yields_invalidated_status(self):
        revision = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-1"
        )
        challenge = AssumptionEvent.challenged(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            severity="invalidated", event_id="event-2",
        )
        view = reconstruct_current_state([revision, challenge])
        assert view.status == "invalidated"
        assert view.is_active is True

    def test_superseded_status_is_not_active(self):
        revision = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-1"
        )
        superseded = AssumptionEvent.superseded(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            superseded_by_assumption_id="new-id", event_id="event-2",
        )
        view = reconstruct_current_state([revision, superseded])
        assert view.status == "superseded"
        assert view.is_active is False
        assert view.superseded_by_assumption_id == "new-id"

    def test_retired_status_is_not_active(self):
        revision = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-1"
        )
        retired = AssumptionEvent.retired(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-2"
        )
        view = reconstruct_current_state([revision, retired])
        assert view.status == "retired"
        assert view.is_active is False

    def test_a_later_revision_resets_status_to_supported_after_a_challenge(self):
        revision = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-1"
        )
        challenge = AssumptionEvent.challenged(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID, event_id="event-2"
        )
        reaffirmed = AssumptionEvent.revised(
            assumption_id=_ASSUMPTION_ID, decision_id=_DECISION_ID, case_id=_CASE_ID,
            statement="Reaffirmed after review", event_id="event-3",
        )
        view = reconstruct_current_state([revision, challenge, reaffirmed])
        assert view.status == "supported"
        assert view.statement == "Reaffirmed after review"

"""Tests for the DecisionDraft aggregate root (ADR-DD-001):
`DecisionDraftEvent` construction/immutability and the
`reconstruct_current_state` projection.
"""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone

import pytest

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.decision_draft.entity import (
    DecisionDraftEvent,
    reconstruct_current_state,
)
from atlas.core.domain.decision_draft.value_objects import DraftId

_CASE_ID = CaseId()
_USER_ID = UserId(uuid.uuid4())
_DRAFT_ID = DraftId()


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestDecisionDraftEventRevised:
    def test_carries_the_given_content(self):
        event = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            decision_type="BUY",
            subject="ASML",
            reason="Durable moat",
            confidence=75,
            situation="Large exposure already",
            alternatives_considered=("Buy Arm",),
            uncertainties=("Fed announcement",),
            event_id="event-1",
        )
        assert event.event_type == "revised"
        assert event.draft_id == _DRAFT_ID
        assert event.case_id == _CASE_ID
        assert event.user_id == _USER_ID
        assert event.decision_type == "BUY"
        assert event.subject == "ASML"
        assert event.reason == "Durable moat"
        assert event.confidence == 75
        assert event.situation == "Large exposure already"
        assert event.alternatives_considered == ("Buy Arm",)
        assert event.uncertainties == ("Fed announcement",)
        assert event.committed_decision_id is None

    def test_all_content_fields_default_to_none_or_empty(self):
        event = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID, case_id=_CASE_ID, user_id=_USER_ID, event_id="event-1"
        )
        assert event.decision_type is None
        assert event.subject is None
        assert event.reason is None
        assert event.confidence is None
        assert event.decided_at is None
        assert event.source is None
        assert event.situation is None
        assert event.portfolio_relevance is None
        assert event.capital_considerations is None
        assert event.alternatives_considered == ()
        assert event.uncertainties == ()

    def test_recorded_at_comes_from_the_given_clock(self):
        now = datetime(2026, 7, 13, tzinfo=timezone.utc)
        event = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            event_id="event-1",
            clock=_fixed_clock(now),
        )
        assert event.recorded_at == now


class TestDecisionDraftEventAbandoned:
    def test_carries_no_content(self):
        event = DecisionDraftEvent.abandoned(
            draft_id=_DRAFT_ID, case_id=_CASE_ID, user_id=_USER_ID, event_id="event-2"
        )
        assert event.event_type == "abandoned"
        assert event.decision_type is None
        assert event.subject is None
        assert event.committed_decision_id is None


class TestDecisionDraftEventCommitted:
    def test_carries_the_committed_decision_id(self):
        event = DecisionDraftEvent.committed(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            committed_decision_id="decision-123",
            event_id="event-3",
        )
        assert event.event_type == "committed"
        assert event.committed_decision_id == "decision-123"
        assert event.subject is None


class TestDecisionDraftEventImmutability:
    def test_is_frozen(self):
        event = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID, case_id=_CASE_ID, user_id=_USER_ID, event_id="event-1"
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.subject = "changed"


class TestReconstructCurrentState:
    def test_returns_none_for_an_empty_stream(self):
        assert reconstruct_current_state([]) is None

    def test_a_single_revision_yields_an_active_view(self):
        event = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="ASML",
            event_id="event-1",
        )
        view = reconstruct_current_state([event])
        assert view.status == "active"
        assert view.subject == "ASML"
        assert view.latest_event_id == "event-1"
        assert view.created_at == event.recorded_at
        assert view.updated_at == event.recorded_at

    def test_a_later_revision_overrides_content_and_updated_at(self):
        first = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="ASML",
            event_id="event-1",
            clock=_fixed_clock(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        )
        second = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="ASML Holding NV",
            event_id="event-2",
            clock=_fixed_clock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        )
        view = reconstruct_current_state([first, second])
        assert view.subject == "ASML Holding NV"
        assert view.created_at == first.recorded_at
        assert view.updated_at == second.recorded_at
        assert view.latest_event_id == "event-2"

    def test_abandoned_status_still_shows_last_known_content(self):
        revision = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="ASML",
            event_id="event-1",
        )
        abandonment = DecisionDraftEvent.abandoned(
            draft_id=_DRAFT_ID, case_id=_CASE_ID, user_id=_USER_ID, event_id="event-2"
        )
        view = reconstruct_current_state([revision, abandonment])
        assert view.status == "abandoned"
        assert view.subject == "ASML"  # last-known content, not blanked out
        assert view.latest_event_id == "event-2"

    def test_committed_status_shows_last_known_content_and_decision_id(self):
        revision = DecisionDraftEvent.revised(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="ASML",
            event_id="event-1",
        )
        commit = DecisionDraftEvent.committed(
            draft_id=_DRAFT_ID,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            committed_decision_id="decision-123",
            event_id="event-2",
        )
        view = reconstruct_current_state([revision, commit])
        assert view.status == "committed"
        assert view.subject == "ASML"
        assert view.committed_decision_id == "decision-123"

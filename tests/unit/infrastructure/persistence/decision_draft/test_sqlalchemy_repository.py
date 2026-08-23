"""Persistence tests for SqlAlchemyDecisionDraftEventRepository (ADR-DD-001)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.decision_draft.entity import DecisionDraftEvent
from atlas.core.domain.decision_draft.value_objects import DraftId
from atlas.core.infrastructure.persistence.decision_draft.sqlalchemy_repository import (
    SqlAlchemyDecisionDraftEventRepository,
)
from atlas.core.infrastructure.persistence.decision_draft.table import (
    create_decision_draft_events_table,
)

_CASE_ID = CaseId()
_USER_ID = UserId(uuid.uuid4())


def _fixed_clock(dt: datetime):
    return lambda: dt


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_draft_events_table(engine)
    return SqlAlchemyDecisionDraftEventRepository(engine)


class TestAddAndGetLatestEvent:
    def test_round_trips_a_revised_event(self, repository):
        draft_id = DraftId()
        event = DecisionDraftEvent.revised(
            draft_id=draft_id,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            decision_type="BUY",
            subject="ASML",
            reason="Durable moat",
            confidence=75,
            decided_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            source="Manual",
            situation="Large exposure already",
            portfolio_relevance="Complements existing holdings",
            capital_considerations="Only deploy part of capital",
            alternatives_considered=("Buy Arm", "Buy TSM"),
            uncertainties=("Fed announcement",),
            event_id=str(uuid.uuid4()),
        )

        repository.add(event)
        latest = repository.get_latest_event(draft_id)

        assert latest == event

    def test_returns_none_when_no_event_exists(self, repository):
        assert repository.get_latest_event(DraftId()) is None

    def test_latest_event_is_the_most_recently_recorded(self, repository):
        draft_id = DraftId()
        first = DecisionDraftEvent.revised(
            draft_id=draft_id,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="ASML",
            event_id=str(uuid.uuid4()),
            clock=_fixed_clock(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        )
        second = DecisionDraftEvent.revised(
            draft_id=draft_id,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="ASML Holding NV",
            event_id=str(uuid.uuid4()),
            clock=_fixed_clock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        )
        repository.add(first)
        repository.add(second)

        latest = repository.get_latest_event(draft_id)
        assert latest.subject == "ASML Holding NV"

    def test_ordering_falls_back_to_id_when_recorded_at_ties(self, repository):
        draft_id = DraftId()
        same_instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = DecisionDraftEvent.revised(
            draft_id=draft_id,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="first",
            event_id="a-event",
            clock=_fixed_clock(same_instant),
        )
        second = DecisionDraftEvent.revised(
            draft_id=draft_id,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="second",
            event_id="b-event",
            clock=_fixed_clock(same_instant),
        )
        repository.add(first)
        repository.add(second)

        latest = repository.get_latest_event(draft_id)
        assert latest.id == "b-event"  # higher id wins the deterministic tiebreak


class TestListEvents:
    def test_returns_full_history_oldest_first(self, repository):
        draft_id = DraftId()
        first = DecisionDraftEvent.revised(
            draft_id=draft_id,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            subject="first",
            event_id=str(uuid.uuid4()),
            clock=_fixed_clock(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        )
        second = DecisionDraftEvent.abandoned(
            draft_id=draft_id,
            case_id=_CASE_ID,
            user_id=_USER_ID,
            event_id=str(uuid.uuid4()),
            clock=_fixed_clock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        )
        repository.add(second)  # inserted out of order on purpose
        repository.add(first)

        events = repository.list_events(draft_id)
        assert [event.event_type for event in events] == ["revised", "abandoned"]

    def test_returns_empty_list_for_unknown_draft(self, repository):
        assert repository.list_events(DraftId()) == []


class TestListLatestByCase:
    def test_returns_the_latest_event_per_draft(self, repository):
        case_id = CaseId()
        draft_a = DraftId()
        draft_b = DraftId()
        repository.add(
            DecisionDraftEvent.revised(
                draft_id=draft_a, case_id=case_id, user_id=_USER_ID, subject="A",
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            DecisionDraftEvent.revised(
                draft_id=draft_b, case_id=case_id, user_id=_USER_ID, subject="B",
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_case(case_id)
        assert {event.draft_id for event in latest} == {draft_a, draft_b}

    def test_excludes_drafts_from_other_cases(self, repository):
        case_id = CaseId()
        other_case_id = CaseId()
        repository.add(
            DecisionDraftEvent.revised(
                draft_id=DraftId(), case_id=case_id, user_id=_USER_ID,
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            DecisionDraftEvent.revised(
                draft_id=DraftId(), case_id=other_case_id, user_id=_USER_ID,
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_case(case_id)
        assert len(latest) == 1
        assert latest[0].case_id == case_id


class TestListLatestByUser:
    def test_returns_the_latest_event_per_draft_across_cases(self, repository):
        user_id = UserId(uuid.uuid4())
        repository.add(
            DecisionDraftEvent.revised(
                draft_id=DraftId(), case_id=CaseId(), user_id=user_id,
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            DecisionDraftEvent.revised(
                draft_id=DraftId(), case_id=CaseId(), user_id=user_id,
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_user(user_id)
        assert len(latest) == 2

    def test_excludes_other_users(self, repository):
        user_id = UserId(uuid.uuid4())
        other_user_id = UserId(uuid.uuid4())
        repository.add(
            DecisionDraftEvent.revised(
                draft_id=DraftId(), case_id=_CASE_ID, user_id=user_id,
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            DecisionDraftEvent.revised(
                draft_id=DraftId(), case_id=_CASE_ID, user_id=other_user_id,
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_user(user_id)
        assert len(latest) == 1
        assert latest[0].user_id == user_id

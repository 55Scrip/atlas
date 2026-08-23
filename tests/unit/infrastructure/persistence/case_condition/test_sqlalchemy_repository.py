"""Persistence tests for SqlAlchemyCaseConditionEventRepository (ADR-CC-001)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.entity import CaseConditionEvent
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.persistence.case_condition.sqlalchemy_repository import (
    SqlAlchemyCaseConditionEventRepository,
)
from atlas.core.infrastructure.persistence.case_condition.table import (
    create_case_condition_events_table,
)

_CASE_ID = CaseId()


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
    create_case_condition_events_table(engine)
    return SqlAlchemyCaseConditionEventRepository(engine)


class TestAddAndGetLatestEvent:
    def test_round_trips_a_revised_event(self, repository):
        condition_id = CaseConditionId()
        decision_id = DecisionId(uuid.uuid4())
        event = CaseConditionEvent.revised(
            condition_id=condition_id,
            case_id=_CASE_ID,
            decision_id=decision_id,
            predicate_text="China revenue trend",
            role="monitoring",
            authorship="atlas",
            structured_kind="threshold",
            threshold_metric="china_revenue_growth",
            threshold_operator="<",
            threshold_value=0.05,
            event_id=str(uuid.uuid4()),
        )

        repository.add(event)
        latest = repository.get_latest_event(condition_id)

        assert latest == event

    def test_returns_none_when_no_event_exists(self, repository):
        assert repository.get_latest_event(CaseConditionId()) is None

    def test_ordering_falls_back_to_id_when_recorded_at_ties(self, repository):
        condition_id = CaseConditionId()
        same_instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = CaseConditionEvent.revised(
            condition_id=condition_id, case_id=_CASE_ID, decision_id=None,
            predicate_text="first", event_id="a-event", clock=_fixed_clock(same_instant),
        )
        second = CaseConditionEvent.revised(
            condition_id=condition_id, case_id=_CASE_ID, decision_id=None,
            predicate_text="second", event_id="b-event", clock=_fixed_clock(same_instant),
        )
        repository.add(first)
        repository.add(second)

        latest = repository.get_latest_event(condition_id)
        assert latest.id == "b-event"


class TestListEvents:
    def test_returns_full_history_oldest_first(self, repository):
        condition_id = CaseConditionId()
        first = CaseConditionEvent.revised(
            condition_id=condition_id, case_id=_CASE_ID, decision_id=None,
            event_id=str(uuid.uuid4()), clock=_fixed_clock(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        )
        second = CaseConditionEvent.retired(
            condition_id=condition_id, case_id=_CASE_ID, decision_id=None,
            event_id=str(uuid.uuid4()), clock=_fixed_clock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        )
        repository.add(second)
        repository.add(first)

        events = repository.list_events(condition_id)
        assert [event.event_type for event in events] == ["revised", "retired"]

    def test_returns_empty_list_for_unknown_condition(self, repository):
        assert repository.list_events(CaseConditionId()) == []


class TestListLatestByCase:
    def test_returns_the_latest_event_per_condition(self, repository):
        case_id = CaseId()
        condition_a = CaseConditionId()
        condition_b = CaseConditionId()
        repository.add(
            CaseConditionEvent.revised(
                condition_id=condition_a, case_id=case_id, decision_id=None,
                predicate_text="A", event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            CaseConditionEvent.revised(
                condition_id=condition_b, case_id=case_id, decision_id=None,
                predicate_text="B", event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_case(case_id)
        assert {event.condition_id for event in latest} == {condition_a, condition_b}

    def test_excludes_conditions_from_other_cases(self, repository):
        case_id = CaseId()
        other_case_id = CaseId()
        repository.add(
            CaseConditionEvent.revised(
                condition_id=CaseConditionId(), case_id=case_id, decision_id=None,
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            CaseConditionEvent.revised(
                condition_id=CaseConditionId(), case_id=other_case_id, decision_id=None,
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_case(case_id)
        assert len(latest) == 1
        assert latest[0].case_id == case_id


class TestListLatestByDecision:
    def test_returns_the_latest_event_per_condition_for_a_decision(self, repository):
        decision_id = DecisionId(uuid.uuid4())
        repository.add(
            CaseConditionEvent.revised(
                condition_id=CaseConditionId(), case_id=_CASE_ID, decision_id=decision_id,
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            CaseConditionEvent.revised(
                condition_id=CaseConditionId(), case_id=_CASE_ID, decision_id=None,
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_decision(decision_id)
        assert len(latest) == 1
        assert latest[0].decision_id == decision_id

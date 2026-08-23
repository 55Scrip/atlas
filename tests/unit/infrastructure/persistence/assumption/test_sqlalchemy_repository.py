"""Persistence tests for SqlAlchemyAssumptionEventRepository (ADR-AS-001)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.assumption.entity import AssumptionEvent
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.persistence.assumption.sqlalchemy_repository import (
    SqlAlchemyAssumptionEventRepository,
)
from atlas.core.infrastructure.persistence.assumption.table import create_assumption_events_table

_CASE_ID = CaseId()
_DECISION_ID = DecisionId(uuid.uuid4())


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
    create_assumption_events_table(engine)
    return SqlAlchemyAssumptionEventRepository(engine)


class TestAddAndGetLatestEvent:
    def test_round_trips_a_revised_event(self, repository):
        assumption_id = AssumptionId()
        event = AssumptionEvent.revised(
            assumption_id=assumption_id,
            decision_id=_DECISION_ID,
            case_id=_CASE_ID,
            statement="GCP margin expansion continues",
            authorship="atlas",
            linked_case_condition_ids=("cc-1", "cc-2"),
            event_id=str(uuid.uuid4()),
        )

        repository.add(event)
        latest = repository.get_latest_event(assumption_id)

        assert latest == event

    def test_returns_none_when_no_event_exists(self, repository):
        assert repository.get_latest_event(AssumptionId()) is None

    def test_ordering_falls_back_to_id_when_recorded_at_ties(self, repository):
        assumption_id = AssumptionId()
        same_instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = AssumptionEvent.revised(
            assumption_id=assumption_id, decision_id=_DECISION_ID, case_id=_CASE_ID,
            statement="first", event_id="a-event", clock=_fixed_clock(same_instant),
        )
        second = AssumptionEvent.revised(
            assumption_id=assumption_id, decision_id=_DECISION_ID, case_id=_CASE_ID,
            statement="second", event_id="b-event", clock=_fixed_clock(same_instant),
        )
        repository.add(first)
        repository.add(second)

        latest = repository.get_latest_event(assumption_id)
        assert latest.id == "b-event"


class TestListEvents:
    def test_returns_full_history_oldest_first(self, repository):
        assumption_id = AssumptionId()
        first = AssumptionEvent.revised(
            assumption_id=assumption_id, decision_id=_DECISION_ID, case_id=_CASE_ID,
            event_id=str(uuid.uuid4()), clock=_fixed_clock(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        )
        second = AssumptionEvent.challenged(
            assumption_id=assumption_id, decision_id=_DECISION_ID, case_id=_CASE_ID,
            event_id=str(uuid.uuid4()), clock=_fixed_clock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        )
        repository.add(second)
        repository.add(first)

        events = repository.list_events(assumption_id)
        assert [event.event_type for event in events] == ["revised", "challenged"]

    def test_returns_empty_list_for_unknown_assumption(self, repository):
        assert repository.list_events(AssumptionId()) == []


class TestListLatestByDecision:
    def test_returns_the_latest_event_per_assumption(self, repository):
        decision_id = DecisionId(uuid.uuid4())
        assumption_a = AssumptionId()
        assumption_b = AssumptionId()
        repository.add(
            AssumptionEvent.revised(
                assumption_id=assumption_a, decision_id=decision_id, case_id=_CASE_ID,
                statement="A", event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            AssumptionEvent.revised(
                assumption_id=assumption_b, decision_id=decision_id, case_id=_CASE_ID,
                statement="B", event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_decision(decision_id)
        assert {event.assumption_id for event in latest} == {assumption_a, assumption_b}

    def test_excludes_assumptions_from_other_decisions(self, repository):
        decision_id = DecisionId(uuid.uuid4())
        other_decision_id = DecisionId(uuid.uuid4())
        repository.add(
            AssumptionEvent.revised(
                assumption_id=AssumptionId(), decision_id=decision_id, case_id=_CASE_ID,
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            AssumptionEvent.revised(
                assumption_id=AssumptionId(), decision_id=other_decision_id, case_id=_CASE_ID,
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_decision(decision_id)
        assert len(latest) == 1
        assert latest[0].decision_id == decision_id


class TestListLatestByCase:
    def test_returns_assumptions_across_decisions_in_the_same_case(self, repository):
        case_id = CaseId()
        repository.add(
            AssumptionEvent.revised(
                assumption_id=AssumptionId(), decision_id=DecisionId(uuid.uuid4()), case_id=case_id,
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            AssumptionEvent.revised(
                assumption_id=AssumptionId(), decision_id=DecisionId(uuid.uuid4()), case_id=case_id,
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_case(case_id)
        assert len(latest) == 2

    def test_excludes_other_cases(self, repository):
        case_id = CaseId()
        other_case_id = CaseId()
        repository.add(
            AssumptionEvent.revised(
                assumption_id=AssumptionId(), decision_id=DecisionId(uuid.uuid4()), case_id=case_id,
                event_id=str(uuid.uuid4()),
            )
        )
        repository.add(
            AssumptionEvent.revised(
                assumption_id=AssumptionId(), decision_id=DecisionId(uuid.uuid4()), case_id=other_case_id,
                event_id=str(uuid.uuid4()),
            )
        )

        latest = repository.list_latest_by_case(case_id)
        assert len(latest) == 1
        assert latest[0].case_id == case_id

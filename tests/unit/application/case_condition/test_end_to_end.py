"""End-to-end test for the full CaseCondition product flow (ADR-CC-001).

Create (time-based Invalidation Condition, originating from a real
Decision) -> revise -> evaluate mechanically -> confirm the satisfied
transition -> supersede with a replacement. Against real, non-mocked
repositories throughout, mirroring
`tests/unit/application/decision_draft/test_end_to_end.py` (Sprint 9).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.case_condition.case_condition_service import (
    CaseConditionContent,
    CaseConditionService,
)
from atlas.core.domain.case.entity import Case
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
    SqlAlchemyCaseRepository,
)
from atlas.core.infrastructure.persistence.case.table import create_case_table
from atlas.core.infrastructure.persistence.case_condition.sqlalchemy_repository import (
    SqlAlchemyCaseConditionEventRepository,
)
from atlas.core.infrastructure.persistence.case_condition.table import (
    create_case_condition_events_table,
)
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_case_table(eng)
    create_decision_table(eng)
    create_case_condition_events_table(eng)
    return eng


def test_full_create_revise_evaluate_supersede_flow(engine):
    case_repository = SqlAlchemyCaseRepository(engine)
    decision_repository = SqlAlchemyDecisionRepository(engine)
    condition_repository = SqlAlchemyCaseConditionEventRepository(engine)
    service = CaseConditionService(condition_repository, case_repository, decision_repository)

    case = Case.create()
    case_repository.add(case)
    decision = Decision.register(
        case_id=case.id,
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat, undervalued relative to peers"),
        confidence=Confidence(75),
    )
    decision_repository.add(decision)

    # 1. Create an Invalidation Condition originating from this Decision.
    created = service.create(
        case_id=case.id,
        decision_id=decision.id,
        content=CaseConditionContent(
            predicate_text="Review within 90 days",
            role="invalidation",
            authorship="atlas",
            structured_kind="date",
            threshold_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
        ),
    )
    assert created.status == "active"
    assert created.decision_id == decision.id

    # 2. Revise it -- the investor tightens the review window.
    revised = service.revise(
        created.condition_id,
        content=CaseConditionContent(
            predicate_text="Review within 60 days",
            role="invalidation",
            authorship="user",  # the investor edited Atlas's own proposal
            structured_kind="date",
            threshold_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
        ),
    )
    assert revised.predicate_text == "Review within 60 days"
    assert revised.authorship == "user"
    assert revised.decision_id == decision.id  # identity carried forward, unchanged

    # 3. Evaluate before the threshold: no transition.
    before = service.evaluate(
        revised.condition_id, evaluated_at=datetime(2026, 7, 1, tzinfo=timezone.utc)
    )
    assert before.satisfied is False
    assert before.transitioned is False

    # 4. Evaluate after the threshold: transitions to satisfied.
    after = service.evaluate(
        revised.condition_id, evaluated_at=datetime(2026, 8, 15, tzinfo=timezone.utc)
    )
    assert after.satisfied is True
    assert after.transitioned is True
    assert after.view.status == "satisfied"

    # 5. The investor decides this condition is superseded by a fresh one.
    replacement = service.create(case_id=case.id, decision_id=decision.id, content=CaseConditionContent())
    final = service.supersede(
        revised.condition_id, superseded_by_condition_id=str(replacement.condition_id)
    )
    assert final.status == "superseded"
    assert final.superseded_by_condition_id == str(replacement.condition_id)
    assert final.is_active is False

    # 6. Neither Decision nor Case was ever touched by any of this.
    assert decision_repository.get(decision.id) == decision
    assert case_repository.get(case.id) == case

    # 7. Full history is intact and correctly ordered.
    history = service.list_events(revised.condition_id)
    assert [event.event_type for event in history] == [
        "revised",
        "revised",
        "evaluated_satisfied",
        "superseded",
    ]

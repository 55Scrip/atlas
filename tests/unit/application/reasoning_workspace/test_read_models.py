"""Projection tests for the reasoning-workspace read models (Sprint 12 §3)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.assumption.assumption_service import (
    AssumptionContent,
    AssumptionService,
)
from atlas.core.application.case_condition.case_condition_service import (
    CaseConditionContent,
    CaseConditionService,
)
from atlas.core.application.decision_draft.decision_draft_service import (
    DecisionDraftContent,
    DecisionDraftService,
)
from atlas.core.application.reasoning_workspace.read_models import (
    list_active_assumptions,
    list_active_case_conditions,
    list_open_decision_drafts,
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
from atlas.core.infrastructure.persistence.assumption.sqlalchemy_repository import (
    SqlAlchemyAssumptionEventRepository,
)
from atlas.core.infrastructure.persistence.assumption.table import create_assumption_events_table
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
from atlas.core.infrastructure.persistence.decision_context.sqlalchemy_repository import (
    SqlAlchemyDecisionContextRepository,
)
from atlas.core.infrastructure.persistence.decision_context.table import (
    create_decision_context_table,
)
from atlas.core.infrastructure.persistence.decision_draft.sqlalchemy_repository import (
    SqlAlchemyDecisionDraftEventRepository,
)
from atlas.core.infrastructure.persistence.decision_draft.table import (
    create_decision_draft_events_table,
)


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
    create_decision_context_table(eng)
    create_decision_draft_events_table(eng)
    create_case_condition_events_table(eng)
    create_assumption_events_table(eng)
    return eng


@pytest.fixture
def existing_case(engine) -> Case:
    case = Case.create()
    SqlAlchemyCaseRepository(engine).add(case)
    return case


@pytest.fixture
def existing_decision(engine, existing_case) -> Decision:
    decision = Decision.register(
        case_id=existing_case.id, user_id=UserId(uuid.uuid4()), decision_type=DecisionType.BUY,
        subject=Subject("ASML"), investment_case=InvestmentCase("Durable moat"), confidence=Confidence(75),
    )
    SqlAlchemyDecisionRepository(engine).add(decision)
    return decision


class TestListActiveAssumptions:
    def test_returns_only_non_terminal_assumptions(self, engine, existing_decision):
        assumption_service = AssumptionService(
            SqlAlchemyAssumptionEventRepository(engine),
            SqlAlchemyDecisionRepository(engine),
            SqlAlchemyCaseConditionEventRepository(engine),
        )
        active = assumption_service.create(
            decision_id=existing_decision.id, content=AssumptionContent(statement="active one")
        )
        retired = assumption_service.create(
            decision_id=existing_decision.id, content=AssumptionContent(statement="retired one")
        )
        assumption_service.retire(retired.assumption_id)

        rows = list_active_assumptions(assumption_service, existing_decision.case_id)

        assert len(rows) == 1
        assert rows[0].assumption_id == active.assumption_id
        assert rows[0].statement == "active one"
        assert rows[0].status == "supported"


class TestListActiveCaseConditions:
    def test_returns_only_non_terminal_conditions(self, engine, existing_case):
        service = CaseConditionService(
            SqlAlchemyCaseConditionEventRepository(engine),
            SqlAlchemyCaseRepository(engine),
            SqlAlchemyDecisionRepository(engine),
        )
        active = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(predicate_text="active", role="monitoring"),
        )
        retired = service.create(
            case_id=existing_case.id, decision_id=None, content=CaseConditionContent(predicate_text="retired")
        )
        service.retire(retired.condition_id)

        rows = list_active_case_conditions(service, existing_case.id)

        assert len(rows) == 1
        assert rows[0].condition_id == active.condition_id
        assert rows[0].predicate_text == "active"
        assert rows[0].role == "monitoring"


class TestListOpenDecisionDrafts:
    def test_returns_only_active_drafts_for_the_user(self, engine, existing_case):
        service = DecisionDraftService(
            SqlAlchemyDecisionDraftEventRepository(engine),
            SqlAlchemyCaseRepository(engine),
            SqlAlchemyDecisionRepository(engine),
            SqlAlchemyDecisionContextRepository(engine),
        )
        user_id = UserId(uuid.uuid4())
        open_draft = service.create(
            case_id=existing_case.id, user_id=user_id,
            content=DecisionDraftContent(subject="ASML"),
        )
        other_user_draft = service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()),
            content=DecisionDraftContent(subject="MSFT"),
        )

        rows = list_open_decision_drafts(service, user_id)

        assert len(rows) == 1
        assert rows[0].draft_id == open_draft.draft_id
        assert rows[0].subject == "ASML"
        # narrow projection: no reason/confidence/situation field exists on the row at all
        assert not hasattr(rows[0], "reason")
        assert not hasattr(rows[0], "situation")

    def test_excludes_committed_drafts(self, engine, existing_case):
        service = DecisionDraftService(
            SqlAlchemyDecisionDraftEventRepository(engine),
            SqlAlchemyCaseRepository(engine),
            SqlAlchemyDecisionRepository(engine),
            SqlAlchemyDecisionContextRepository(engine),
        )
        user_id = UserId(uuid.uuid4())
        created = service.create(
            case_id=existing_case.id, user_id=user_id,
            content=DecisionDraftContent(
                decision_type="BUY", subject="ASML", reason="Durable moat", confidence=75,
            ),
        )
        service.commit(created.draft_id)

        rows = list_open_decision_drafts(service, user_id)

        assert rows == []

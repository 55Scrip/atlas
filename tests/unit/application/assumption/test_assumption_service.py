"""Application-layer tests for AssumptionService (ADR-AS-001).

Against real (in-memory) repositories for Case, Decision,
CaseCondition, and Assumption throughout — mirrors
`tests/unit/application/case_condition/test_case_condition_service.py`'s
own real-repository fixture style (Sprint 10).
"""
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
from atlas.core.domain.assumption.exceptions import (
    AssumptionNotFoundError,
    AssumptionTerminatedError,
    CaseConditionNotFoundForLinkError,
)
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.entity import Case
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.domain.decision_context.exceptions import (
    DecisionNotFoundError as DecisionContextDecisionNotFoundError,
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
    create_assumption_events_table(eng)
    return eng


@pytest.fixture
def case_repository(engine):
    return SqlAlchemyCaseRepository(engine)


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def case_condition_repository(engine):
    return SqlAlchemyCaseConditionEventRepository(engine)


@pytest.fixture
def assumption_repository(engine):
    return SqlAlchemyAssumptionEventRepository(engine)


@pytest.fixture
def case_condition_service(case_condition_repository, case_repository, decision_repository):
    return CaseConditionService(case_condition_repository, case_repository, decision_repository)


@pytest.fixture
def service(assumption_repository, decision_repository, case_condition_repository):
    return AssumptionService(assumption_repository, decision_repository, case_condition_repository)


@pytest.fixture
def existing_case(case_repository) -> Case:
    case = Case.create()
    case_repository.add(case)
    return case


@pytest.fixture
def existing_decision(existing_case, decision_repository) -> Decision:
    decision = Decision.register(
        case_id=existing_case.id,
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat, undervalued relative to peers"),
        confidence=Confidence(75),
    )
    decision_repository.add(decision)
    return decision


class TestCreate:
    def test_creates_an_assumption_anchored_to_the_decision(self, service, existing_decision, existing_case):
        view = service.create(
            decision_id=existing_decision.id, content=AssumptionContent(statement="GCP margin expansion continues")
        )
        assert view.status == "supported"
        assert view.decision_id == existing_decision.id
        assert view.statement == "GCP margin expansion continues"

    def test_derives_case_id_transitively_from_the_decision(self, service, existing_decision, existing_case):
        view = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        assert view.case_id == existing_case.id  # never separately supplied by the caller

    def test_rejects_an_unknown_decision(self, service):
        from atlas.core.domain.decision.value_objects import DecisionId

        with pytest.raises(DecisionContextDecisionNotFoundError):
            service.create(decision_id=DecisionId(uuid.uuid4()), content=AssumptionContent())


class TestRevise:
    def test_appends_a_new_revision_without_mutating_the_prior_one(
        self, service, existing_decision, assumption_repository
    ):
        created = service.create(
            decision_id=existing_decision.id, content=AssumptionContent(statement="v1")
        )
        revised = service.revise(created.assumption_id, content=AssumptionContent(statement="v2"))

        assert revised.statement == "v2"
        history = assumption_repository.list_events(created.assumption_id)
        assert len(history) == 2
        assert history[0].statement == "v1"

    def test_preserves_linked_case_conditions_across_a_plain_revise(
        self, service, existing_decision, existing_case, case_condition_service
    ):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent(statement="v1"))
        condition = case_condition_service.create(
            case_id=existing_case.id, decision_id=None, content=CaseConditionContent()
        )
        service.attach_case_condition(created.assumption_id, condition.condition_id)

        revised = service.revise(created.assumption_id, content=AssumptionContent(statement="v2"))

        assert revised.linked_case_condition_ids == (str(condition.condition_id),)

    def test_rejects_revising_an_unknown_assumption(self, service):
        with pytest.raises(AssumptionNotFoundError):
            service.revise(AssumptionId(), content=AssumptionContent())

    def test_rejects_revising_a_retired_assumption(self, service, existing_decision):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        service.retire(created.assumption_id)

        with pytest.raises(AssumptionTerminatedError):
            service.revise(created.assumption_id, content=AssumptionContent())

    def test_can_revise_after_being_challenged(self, service, existing_decision):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent(statement="v1"))
        service.challenge(created.assumption_id, note="new evidence emerged")

        revised = service.revise(created.assumption_id, content=AssumptionContent(statement="reaffirmed"))

        assert revised.status == "supported"
        assert revised.statement == "reaffirmed"


class TestChallenge:
    def test_transitions_to_challenged_by_default(self, service, existing_decision):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        view = service.challenge(created.assumption_id, note="mixed signals")
        assert view.status == "challenged"
        assert view.last_challenge_note == "mixed signals"

    def test_transitions_to_invalidated_with_explicit_severity(self, service, existing_decision):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        view = service.challenge(created.assumption_id, severity="invalidated", evidence_id="ev-1")
        assert view.status == "invalidated"

    def test_rejects_challenging_a_retired_assumption(self, service, existing_decision):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        service.retire(created.assumption_id)

        with pytest.raises(AssumptionTerminatedError):
            service.challenge(created.assumption_id)


class TestAttachDetachCaseCondition:
    def test_attach_links_a_real_case_condition(
        self, service, existing_decision, existing_case, case_condition_service
    ):
        assumption = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        condition = case_condition_service.create(
            case_id=existing_case.id, decision_id=None, content=CaseConditionContent()
        )

        view = service.attach_case_condition(assumption.assumption_id, condition.condition_id)

        assert view.linked_case_condition_ids == (str(condition.condition_id),)

    def test_attach_is_idempotent(self, service, existing_decision, existing_case, case_condition_service):
        assumption = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        condition = case_condition_service.create(
            case_id=existing_case.id, decision_id=None, content=CaseConditionContent()
        )

        service.attach_case_condition(assumption.assumption_id, condition.condition_id)
        second = service.attach_case_condition(assumption.assumption_id, condition.condition_id)

        assert second.linked_case_condition_ids == (str(condition.condition_id),)

    def test_attach_preserves_the_statement(self, service, existing_decision, existing_case, case_condition_service):
        assumption = service.create(
            decision_id=existing_decision.id, content=AssumptionContent(statement="GCP margin expansion")
        )
        condition = case_condition_service.create(
            case_id=existing_case.id, decision_id=None, content=CaseConditionContent()
        )

        view = service.attach_case_condition(assumption.assumption_id, condition.condition_id)

        assert view.statement == "GCP margin expansion"

    def test_attach_rejects_an_unknown_case_condition(self, service, existing_decision):
        assumption = service.create(decision_id=existing_decision.id, content=AssumptionContent())

        with pytest.raises(CaseConditionNotFoundForLinkError):
            service.attach_case_condition(assumption.assumption_id, CaseConditionId())

    def test_detach_unlinks_a_case_condition(
        self, service, existing_decision, existing_case, case_condition_service
    ):
        assumption = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        condition = case_condition_service.create(
            case_id=existing_case.id, decision_id=None, content=CaseConditionContent()
        )
        service.attach_case_condition(assumption.assumption_id, condition.condition_id)

        view = service.detach_case_condition(assumption.assumption_id, condition.condition_id)

        assert view.linked_case_condition_ids == ()

    def test_detach_is_idempotent_when_never_linked(self, service, existing_decision):
        assumption = service.create(decision_id=existing_decision.id, content=AssumptionContent())

        view = service.detach_case_condition(assumption.assumption_id, CaseConditionId())

        assert view.linked_case_condition_ids == ()

    def test_attach_rejects_on_a_terminal_assumption(
        self, service, existing_decision, existing_case, case_condition_service
    ):
        assumption = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        service.retire(assumption.assumption_id)
        condition = case_condition_service.create(
            case_id=existing_case.id, decision_id=None, content=CaseConditionContent()
        )

        with pytest.raises(AssumptionTerminatedError):
            service.attach_case_condition(assumption.assumption_id, condition.condition_id)


class TestRetire:
    def test_retires_a_supported_assumption(self, service, existing_decision):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        view = service.retire(created.assumption_id)
        assert view.status == "retired"
        assert view.is_active is False

    def test_is_idempotent(self, service, existing_decision, assumption_repository):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        service.retire(created.assumption_id)
        service.retire(created.assumption_id)

        history = assumption_repository.list_events(created.assumption_id)
        retired_events = [event for event in history if event.event_type == "retired"]
        assert len(retired_events) == 1

    def test_rejects_retiring_a_superseded_assumption(self, service, existing_decision):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        service.supersede(created.assumption_id)

        with pytest.raises(AssumptionTerminatedError):
            service.retire(created.assumption_id)


class TestSupersede:
    def test_supersedes_with_a_replacement_reference(self, service, existing_decision):
        old = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        new = service.create(decision_id=existing_decision.id, content=AssumptionContent())

        view = service.supersede(old.assumption_id, superseded_by_assumption_id=str(new.assumption_id))

        assert view.status == "superseded"
        assert view.superseded_by_assumption_id == str(new.assumption_id)

    def test_rejects_superseding_a_retired_assumption(self, service, existing_decision):
        created = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        service.retire(created.assumption_id)

        with pytest.raises(AssumptionTerminatedError):
            service.supersede(created.assumption_id)


class TestReadAndListEvents:
    def test_read_returns_the_current_view(self, service, existing_decision):
        created = service.create(
            decision_id=existing_decision.id, content=AssumptionContent(statement="GCP margin expansion")
        )
        view = service.read(created.assumption_id)
        assert view.statement == "GCP margin expansion"

    def test_read_rejects_an_unknown_assumption(self, service):
        with pytest.raises(AssumptionNotFoundError):
            service.read(AssumptionId())


class TestListForDecision:
    def test_excludes_terminal_by_default(self, service, existing_decision):
        active = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        retired = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        service.retire(retired.assumption_id)

        views = service.list_for_decision(existing_decision.id)

        assert {view.assumption_id for view in views} == {active.assumption_id}

    def test_includes_terminal_when_requested(self, service, existing_decision):
        active = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        retired = service.create(decision_id=existing_decision.id, content=AssumptionContent())
        service.retire(retired.assumption_id)

        views = service.list_for_decision(existing_decision.id, include_terminal=True)

        assert {view.assumption_id for view in views} == {active.assumption_id, retired.assumption_id}


class TestListForCase:
    def test_returns_assumptions_across_decisions_in_the_same_case(
        self, service, existing_case, decision_repository
    ):
        decision_a = Decision.register(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), decision_type=DecisionType.BUY,
            subject=Subject("ASML"), investment_case=InvestmentCase("Reason A"), confidence=Confidence(70),
        )
        decision_b = Decision.register(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), decision_type=DecisionType.HOLD,
            subject=Subject("ASML"), investment_case=InvestmentCase("Reason B"), confidence=Confidence(60),
        )
        decision_repository.add(decision_a)
        decision_repository.add(decision_b)

        service.create(decision_id=decision_a.id, content=AssumptionContent())
        service.create(decision_id=decision_b.id, content=AssumptionContent())

        views = service.list_for_case(existing_case.id)

        assert len(views) == 2

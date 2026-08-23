"""Application-layer tests for CaseConditionService (ADR-CC-001).

Against real (in-memory) repositories for Case, Decision, and
CaseCondition throughout — mirrors
`tests/unit/application/decision_draft/test_decision_draft_service.py`'s
own real-repository fixture style (Sprint 9).
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
from atlas.core.domain.case.exceptions import CaseNotFoundError
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.exceptions import (
    CaseConditionNotFoundError,
    CaseConditionTerminatedError,
    CrossCaseDecisionError,
)
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


@pytest.fixture
def case_repository(engine):
    return SqlAlchemyCaseRepository(engine)


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def condition_repository(engine):
    return SqlAlchemyCaseConditionEventRepository(engine)


@pytest.fixture
def service(condition_repository, case_repository, decision_repository):
    return CaseConditionService(condition_repository, case_repository, decision_repository)


@pytest.fixture
def existing_case(case_repository) -> Case:
    case = Case.create()
    case_repository.add(case)
    return case


def _decision_in_case(decision_repository, case_id: CaseId) -> Decision:
    decision = Decision.register(
        case_id=case_id,
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat"),
        confidence=Confidence(75),
    )
    decision_repository.add(decision)
    return decision


class TestCreate:
    def test_creates_a_condition_with_a_fresh_id(self, service, existing_case):
        view = service.create(
            case_id=existing_case.id, decision_id=None, content=CaseConditionContent()
        )
        assert view.status == "active"
        assert view.case_id == existing_case.id
        assert view.decision_id is None

    def test_carries_the_given_content(self, service, existing_case):
        content = CaseConditionContent(predicate_text="China revenue trend", role="monitoring")
        view = service.create(case_id=existing_case.id, decision_id=None, content=content)
        assert view.predicate_text == "China revenue trend"
        assert view.role == "monitoring"

    def test_accepts_a_decision_id_in_the_same_case(self, service, existing_case, decision_repository):
        decision = _decision_in_case(decision_repository, existing_case.id)
        view = service.create(
            case_id=existing_case.id, decision_id=decision.id, content=CaseConditionContent()
        )
        assert view.decision_id == decision.id

    def test_rejects_an_unknown_case(self, service):
        with pytest.raises(CaseNotFoundError):
            service.create(case_id=CaseId(), decision_id=None, content=CaseConditionContent())

    def test_rejects_an_unknown_decision(self, service, existing_case):
        from atlas.core.domain.decision.value_objects import DecisionId

        with pytest.raises(DecisionContextDecisionNotFoundError):
            service.create(
                case_id=existing_case.id,
                decision_id=DecisionId(uuid.uuid4()),
                content=CaseConditionContent(),
            )

    def test_rejects_a_decision_from_a_different_case(
        self, service, existing_case, case_repository, decision_repository
    ):
        other_case = Case.create()
        case_repository.add(other_case)
        decision = _decision_in_case(decision_repository, other_case.id)

        with pytest.raises(CrossCaseDecisionError):
            service.create(case_id=existing_case.id, decision_id=decision.id, content=CaseConditionContent())


class TestRevise:
    def test_appends_a_new_revision_without_mutating_the_prior_one(
        self, service, existing_case, condition_repository
    ):
        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(predicate_text="China revenue trend"),
        )

        revised = service.revise(
            created.condition_id, content=CaseConditionContent(predicate_text="China revenue growth")
        )

        assert revised.predicate_text == "China revenue growth"
        history = condition_repository.list_events(created.condition_id)
        assert len(history) == 2
        assert history[0].predicate_text == "China revenue trend"

    def test_rejects_revising_an_unknown_condition(self, service):
        with pytest.raises(CaseConditionNotFoundError):
            service.revise(CaseConditionId(), content=CaseConditionContent())

    def test_rejects_revising_a_retired_condition(self, service, existing_case):
        created = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        service.retire(created.condition_id)

        with pytest.raises(CaseConditionTerminatedError):
            service.revise(created.condition_id, content=CaseConditionContent())

    def test_rejects_revising_a_superseded_condition(self, service, existing_case):
        created = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        service.supersede(created.condition_id)

        with pytest.raises(CaseConditionTerminatedError):
            service.revise(created.condition_id, content=CaseConditionContent())

    def test_can_revise_after_being_satisfied(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(
                structured_kind="date", threshold_date=datetime(2020, 1, 1, tzinfo=timezone.utc)
            ),
        )
        service.evaluate(created.condition_id, evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc))

        revised = service.revise(
            created.condition_id, content=CaseConditionContent(predicate_text="re-armed")
        )
        assert revised.status == "active"
        assert revised.predicate_text == "re-armed"


class TestEvaluateDateBased:
    def test_transitions_to_satisfied_when_the_threshold_date_has_passed(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(
                structured_kind="date", threshold_date=datetime(2020, 1, 1, tzinfo=timezone.utc)
            ),
        )

        result = service.evaluate(
            created.condition_id, evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )

        assert result.satisfied is True
        assert result.transitioned is True
        assert result.view.status == "satisfied"

    def test_no_transition_before_the_threshold_date(self, service, existing_case, condition_repository):
        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(
                structured_kind="date", threshold_date=datetime(2030, 1, 1, tzinfo=timezone.utc)
            ),
        )

        result = service.evaluate(
            created.condition_id, evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )

        assert result.satisfied is False
        assert result.transitioned is False
        # no new event was written for the routine "still not met" check
        assert len(condition_repository.list_events(created.condition_id)) == 1


class TestEvaluateThresholdBased:
    def test_transitions_to_satisfied_when_the_threshold_is_crossed(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(
                structured_kind="threshold", threshold_metric="china_revenue_growth",
                threshold_operator="<", threshold_value=0.05,
            ),
        )

        result = service.evaluate(created.condition_id, observed_value=0.02)

        assert result.satisfied is True
        assert result.view.last_observed_value == 0.02

    def test_raises_without_an_observed_value(self, service, existing_case):
        from atlas.core.domain.case_condition.exceptions import MissingObservedValueError

        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(
                structured_kind="threshold", threshold_metric="china_revenue_growth",
                threshold_operator="<", threshold_value=0.05,
            ),
        )

        with pytest.raises(MissingObservedValueError):
            service.evaluate(created.condition_id)


class TestEvaluateRepeatedSatisfaction:
    def test_re_evaluating_an_already_satisfied_condition_writes_no_new_event(
        self, service, existing_case, condition_repository
    ):
        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(
                structured_kind="date", threshold_date=datetime(2020, 1, 1, tzinfo=timezone.utc)
            ),
        )
        service.evaluate(created.condition_id, evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc))

        second = service.evaluate(
            created.condition_id, evaluated_at=datetime(2026, 2, 1, tzinfo=timezone.utc)
        )

        assert second.transitioned is False
        assert len(condition_repository.list_events(created.condition_id)) == 2  # revised + one satisfaction


class TestEvaluateHumanOverride:
    def test_human_assertion_bypasses_mechanical_evaluation(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(predicate_text="Management changes capital allocation"),
        )

        result = service.evaluate(created.condition_id, human_asserted_satisfied=True)

        assert result.satisfied is True
        assert result.transitioned is True

    def test_free_text_condition_raises_without_a_human_assertion(self, service, existing_case):
        from atlas.core.domain.case_condition.exceptions import ConditionNotMechanicallyEvaluableError

        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(predicate_text="Management changes capital allocation"),
        )

        with pytest.raises(ConditionNotMechanicallyEvaluableError):
            service.evaluate(created.condition_id)


class TestRetire:
    def test_retires_an_active_condition(self, service, existing_case):
        created = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        view = service.retire(created.condition_id)
        assert view.status == "retired"
        assert view.is_active is False

    def test_is_idempotent(self, service, existing_case, condition_repository):
        created = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        service.retire(created.condition_id)
        service.retire(created.condition_id)

        history = condition_repository.list_events(created.condition_id)
        retired_events = [event for event in history if event.event_type == "retired"]
        assert len(retired_events) == 1

    def test_rejects_retiring_a_superseded_condition(self, service, existing_case):
        created = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        service.supersede(created.condition_id)

        with pytest.raises(CaseConditionTerminatedError):
            service.retire(created.condition_id)

    def test_rejects_retiring_an_unknown_condition(self, service):
        with pytest.raises(CaseConditionNotFoundError):
            service.retire(CaseConditionId())


class TestSupersede:
    def test_supersedes_an_active_condition_with_a_replacement_reference(self, service, existing_case):
        old = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        new = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())

        view = service.supersede(old.condition_id, superseded_by_condition_id=str(new.condition_id))

        assert view.status == "superseded"
        assert view.superseded_by_condition_id == str(new.condition_id)

    def test_rejects_superseding_an_already_terminal_condition(self, service, existing_case):
        created = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        service.retire(created.condition_id)

        with pytest.raises(CaseConditionTerminatedError):
            service.supersede(created.condition_id)


class TestReadAndListEvents:
    def test_read_returns_the_current_view(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, decision_id=None,
            content=CaseConditionContent(predicate_text="China revenue trend"),
        )
        view = service.read(created.condition_id)
        assert view.predicate_text == "China revenue trend"

    def test_read_rejects_an_unknown_condition(self, service):
        with pytest.raises(CaseConditionNotFoundError):
            service.read(CaseConditionId())

    def test_list_events_rejects_an_unknown_condition(self, service):
        with pytest.raises(CaseConditionNotFoundError):
            service.list_events(CaseConditionId())


class TestListForCase:
    def test_excludes_terminal_conditions_by_default(self, service, existing_case):
        active = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        retired = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        service.retire(retired.condition_id)

        views = service.list_for_case(existing_case.id)

        assert {view.condition_id for view in views} == {active.condition_id}

    def test_includes_terminal_conditions_when_requested(self, service, existing_case):
        active = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        retired = service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())
        service.retire(retired.condition_id)

        views = service.list_for_case(existing_case.id, include_terminal=True)

        assert {view.condition_id for view in views} == {active.condition_id, retired.condition_id}


class TestListForDecision:
    def test_returns_only_conditions_referencing_the_decision(
        self, service, existing_case, decision_repository
    ):
        decision = _decision_in_case(decision_repository, existing_case.id)
        with_decision = service.create(
            case_id=existing_case.id, decision_id=decision.id, content=CaseConditionContent()
        )
        service.create(case_id=existing_case.id, decision_id=None, content=CaseConditionContent())

        views = service.list_for_decision(decision.id)

        assert {view.condition_id for view in views} == {with_decision.condition_id}

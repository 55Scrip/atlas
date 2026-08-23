"""Orchestration/integration tests for ReasoningWorkspaceService (Sprint 12).

Against real (in-memory) repositories and the real, unmodified
`DecisionDraftService`/`AssumptionService`/`CaseConditionService`
throughout — the behavior under test is precisely whether this
orchestration layer composes those three existing services correctly,
without reimplementing any of their own logic.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

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
from atlas.core.application.reasoning_workspace.reasoning_workspace_service import (
    AssumptionWithLinkedConditions,
    ReasoningWorkspaceService,
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
from atlas.core.domain.decision.value_objects import DecisionId
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
def case_repository(engine):
    return SqlAlchemyCaseRepository(engine)


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def decision_context_repository(engine):
    return SqlAlchemyDecisionContextRepository(engine)


@pytest.fixture
def draft_repository(engine):
    return SqlAlchemyDecisionDraftEventRepository(engine)


@pytest.fixture
def case_condition_repository(engine):
    return SqlAlchemyCaseConditionEventRepository(engine)


@pytest.fixture
def assumption_repository(engine):
    return SqlAlchemyAssumptionEventRepository(engine)


@pytest.fixture
def draft_service(draft_repository, case_repository, decision_repository, decision_context_repository):
    return DecisionDraftService(
        draft_repository, case_repository, decision_repository, decision_context_repository
    )


@pytest.fixture
def case_condition_service(case_condition_repository, case_repository, decision_repository):
    return CaseConditionService(case_condition_repository, case_repository, decision_repository)


@pytest.fixture
def assumption_service(assumption_repository, decision_repository, case_condition_repository):
    return AssumptionService(assumption_repository, decision_repository, case_condition_repository)


@pytest.fixture
def service(
    decision_repository,
    decision_context_repository,
    draft_repository,
    draft_service,
    assumption_service,
    case_condition_service,
):
    return ReasoningWorkspaceService(
        decision_repository,
        decision_context_repository,
        draft_repository,
        draft_service,
        assumption_service,
        case_condition_service,
    )


@pytest.fixture
def existing_case(case_repository) -> Case:
    case = Case.create()
    case_repository.add(case)
    return case


def _complete_draft_content(**overrides) -> DecisionDraftContent:
    defaults = dict(
        decision_type="BUY",
        subject="ASML",
        reason="Durable moat, undervalued relative to peers",
        confidence=75,
        decided_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return DecisionDraftContent(**defaults)


class TestCommitDraftWithReasoning:
    def test_commit_alone_reuses_the_unmodified_draft_commit(self, service, draft_service, existing_case):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=_complete_draft_content()
        )

        result = service.commit_draft_with_reasoning(created.draft_id)

        assert result.decision.subject.value == "ASML"
        assert result.draft.status == "committed"
        assert result.assumptions == ()
        assert result.case_conditions == ()

    def test_creates_requested_assumptions_anchored_to_the_new_decision(
        self, service, draft_service, existing_case
    ):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=_complete_draft_content()
        )

        result = service.commit_draft_with_reasoning(
            created.draft_id,
            assumptions=(
                AssumptionWithLinkedConditions(
                    content=AssumptionContent(statement="GCP margin expansion continues")
                ),
            ),
        )

        assert len(result.assumptions) == 1
        assert result.assumptions[0].decision_id == result.decision.id
        assert result.assumptions[0].statement == "GCP margin expansion continues"

    def test_creates_and_links_case_conditions_to_their_assumption(
        self, service, draft_service, existing_case, assumption_service
    ):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=_complete_draft_content()
        )

        result = service.commit_draft_with_reasoning(
            created.draft_id,
            assumptions=(
                AssumptionWithLinkedConditions(
                    content=AssumptionContent(statement="GCP margin expansion continues"),
                    linked_condition_contents=(
                        CaseConditionContent(predicate_text="GCP margin trend", role="monitoring"),
                    ),
                ),
            ),
        )

        assert len(result.case_conditions) == 1
        condition = result.case_conditions[0]
        assert condition.case_id == result.decision.case_id
        assert condition.decision_id == result.decision.id

        refreshed_assumption = assumption_service.read(result.assumptions[0].assumption_id)
        assert refreshed_assumption.linked_case_condition_ids == (str(condition.condition_id),)

    def test_creates_standalone_case_conditions_not_linked_to_any_assumption(
        self, service, draft_service, existing_case
    ):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=_complete_draft_content()
        )

        result = service.commit_draft_with_reasoning(
            created.draft_id,
            standalone_case_condition_contents=(
                CaseConditionContent(predicate_text="Review within 90 days", structured_kind="date"),
            ),
        )

        assert len(result.case_conditions) == 1
        assert result.assumptions == ()

    def test_propagates_missing_subject_unmodified(self, service, draft_service, existing_case):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()),
            content=_complete_draft_content(subject=None),
        )
        from atlas.core.domain.decision.exceptions import MissingSubjectError

        with pytest.raises(MissingSubjectError):
            service.commit_draft_with_reasoning(created.draft_id)

    def test_does_not_create_a_second_decision_on_recommit(
        self, service, draft_service, existing_case, decision_repository
    ):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=_complete_draft_content()
        )
        service.commit_draft_with_reasoning(created.draft_id)

        from atlas.core.domain.decision_draft.exceptions import DecisionDraftAlreadyCommittedError

        with pytest.raises(DecisionDraftAlreadyCommittedError):
            service.commit_draft_with_reasoning(created.draft_id)

        assert len(decision_repository.list_all()) == 1


class TestLoadWorkspace:
    def test_assembles_decision_and_context(
        self, service, decision_repository, decision_context_repository, existing_case
    ):
        decision = Decision.register(
            case_id=existing_case.id,
            user_id=UserId(uuid.uuid4()),
            decision_type=DecisionType.BUY,
            subject=Subject("ASML"),
            investment_case=InvestmentCase("Durable moat"),
            confidence=Confidence(75),
        )
        decision_repository.add(decision)

        workspace = service.load_workspace(decision.id)

        assert workspace.decision == decision
        assert workspace.decision_context is None
        assert workspace.originating_draft is None
        assert workspace.active_case_drafts == ()
        assert workspace.assumptions == ()
        assert workspace.case_conditions == ()

    def test_assembles_the_originating_draft(self, service, draft_service, existing_case):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=_complete_draft_content()
        )
        result = service.commit_draft_with_reasoning(created.draft_id)

        workspace = service.load_workspace(result.decision.id)

        assert workspace.originating_draft is not None
        assert workspace.originating_draft.draft_id == created.draft_id
        assert workspace.originating_draft.status == "committed"

    def test_assembles_other_active_drafts_on_the_same_case(
        self, service, draft_service, existing_case, decision_repository
    ):
        decision = Decision.register(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), decision_type=DecisionType.BUY,
            subject=Subject("ASML"), investment_case=InvestmentCase("Reason"), confidence=Confidence(70),
        )
        decision_repository.add(decision)
        other_draft = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=DecisionDraftContent()
        )

        workspace = service.load_workspace(decision.id)

        assert len(workspace.active_case_drafts) == 1
        assert workspace.active_case_drafts[0].draft_id == other_draft.draft_id

    def test_assembles_assumptions_and_case_conditions(self, service, draft_service, existing_case):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=_complete_draft_content()
        )
        result = service.commit_draft_with_reasoning(
            created.draft_id,
            assumptions=(
                AssumptionWithLinkedConditions(content=AssumptionContent(statement="GCP margin expansion")),
            ),
            standalone_case_condition_contents=(CaseConditionContent(predicate_text="Review in 90 days"),),
        )

        workspace = service.load_workspace(result.decision.id)

        assert len(workspace.assumptions) == 1
        assert len(workspace.case_conditions) == 1

    def test_excludes_retired_assumptions_and_conditions(
        self, service, draft_service, existing_case, assumption_service, case_condition_service
    ):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), content=_complete_draft_content()
        )
        result = service.commit_draft_with_reasoning(
            created.draft_id,
            assumptions=(
                AssumptionWithLinkedConditions(content=AssumptionContent(statement="will retire")),
            ),
        )
        assumption_service.retire(result.assumptions[0].assumption_id)

        workspace = service.load_workspace(result.decision.id)

        assert workspace.assumptions == ()

    def test_raises_for_an_unknown_decision(self, service):
        with pytest.raises(DecisionContextDecisionNotFoundError):
            service.load_workspace(DecisionId(uuid.uuid4()))

    def test_does_not_mutate_any_underlying_aggregate(
        self, service, draft_service, existing_case, decision_repository, decision_context_repository
    ):
        created = draft_service.create(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()),
            content=_complete_draft_content(situation="Large exposure already"),
        )
        result = service.commit_draft_with_reasoning(created.draft_id)
        before_decision = decision_repository.get(result.decision.id)
        before_context = decision_context_repository.get_by_decision_id(result.decision.id)

        service.load_workspace(result.decision.id)

        assert decision_repository.get(result.decision.id) == before_decision
        assert decision_context_repository.get_by_decision_id(result.decision.id) == before_context

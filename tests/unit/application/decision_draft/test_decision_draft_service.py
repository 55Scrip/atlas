"""Application-layer tests for DecisionDraftService (ADR-DD-001).

Exercises the full cross-aggregate orchestration against real (in-memory)
repositories for Case, Decision, DecisionContext, and DecisionDraft —
not fakes — since the behavior under test (does commit really call the
real, unmodified Decision.register()/DecisionContext.capture()?) is
precisely the interaction between these real repositories. Mirrors
`tests/unit/application/decision_context/test_capture_decision_context.py`'s
own real-repository fixture style.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.decision_draft.decision_draft_service import (
    DecisionDraftContent,
    DecisionDraftService,
)
from atlas.core.domain.case.entity import Case
from atlas.core.domain.case.exceptions import CaseNotFoundError
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.exceptions import (
    InvalidConfidenceError,
    MissingReasonError,
    MissingSubjectError,
)
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.decision_draft.exceptions import (
    DecisionDraftAlreadyAbandonedError,
    DecisionDraftAlreadyCommittedError,
    DecisionDraftConflictError,
    DecisionDraftNotFoundError,
)
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
    SqlAlchemyCaseRepository,
)
from atlas.core.infrastructure.persistence.case.table import create_case_table
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
def service(draft_repository, case_repository, decision_repository, decision_context_repository):
    return DecisionDraftService(
        draft_repository, case_repository, decision_repository, decision_context_repository
    )


@pytest.fixture
def existing_case(case_repository) -> Case:
    case = Case.create()
    case_repository.add(case)
    return case


def _user_id() -> UserId:
    return UserId(uuid.uuid4())


class TestCreate:
    def test_creates_a_draft_with_a_fresh_id(self, service, existing_case):
        view = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent()
        )
        assert view.status == "active"
        assert view.case_id == existing_case.id

    def test_two_creates_yield_two_distinct_drafts(self, service, existing_case):
        first = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent()
        )
        second = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent()
        )
        assert first.draft_id != second.draft_id  # no cap on concurrent drafts per Case

    def test_carries_the_given_partial_content(self, service, existing_case):
        content = DecisionDraftContent(subject="ASML", reason="Durable moat")
        view = service.create(case_id=existing_case.id, user_id=_user_id(), content=content)
        assert view.subject == "ASML"
        assert view.reason == "Durable moat"
        assert view.confidence is None  # incomplete content is fine on a draft

    def test_rejects_an_unknown_case(self, service):
        with pytest.raises(CaseNotFoundError):
            service.create(case_id=CaseId(), user_id=_user_id(), content=DecisionDraftContent())


class TestRevise:
    def test_appends_a_new_revision_without_mutating_the_prior_one(
        self, service, existing_case, draft_repository
    ):
        user_id = _user_id()
        created = service.create(
            case_id=existing_case.id, user_id=user_id, content=DecisionDraftContent(subject="ASML")
        )

        revised = service.revise(
            created.draft_id, content=DecisionDraftContent(subject="ASML Holding NV")
        )

        assert revised.subject == "ASML Holding NV"
        history = draft_repository.list_events(created.draft_id)
        assert len(history) == 2
        assert history[0].subject == "ASML"  # the first event is untouched

    def test_rejects_revising_an_unknown_draft(self, service):
        from atlas.core.domain.decision_draft.value_objects import DraftId

        with pytest.raises(DecisionDraftNotFoundError):
            service.revise(DraftId(), content=DecisionDraftContent())

    def test_rejects_revising_an_abandoned_draft(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent()
        )
        service.abandon(created.draft_id)

        with pytest.raises(DecisionDraftAlreadyAbandonedError):
            service.revise(created.draft_id, content=DecisionDraftContent())

    def test_rejects_revising_a_committed_draft(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id,
            user_id=_user_id(),
            content=_complete_content(),
        )
        service.commit(created.draft_id)

        with pytest.raises(DecisionDraftAlreadyCommittedError):
            service.revise(created.draft_id, content=DecisionDraftContent())

    def test_rejects_a_stale_expected_latest_event_id(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent()
        )
        service.revise(created.draft_id, content=DecisionDraftContent(subject="first edit"))

        with pytest.raises(DecisionDraftConflictError):
            service.revise(
                created.draft_id,
                content=DecisionDraftContent(subject="second edit"),
                expected_latest_event_id=created.latest_event_id,  # now stale
            )

    def test_accepts_a_matching_expected_latest_event_id(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent()
        )
        revised = service.revise(
            created.draft_id,
            content=DecisionDraftContent(subject="edit"),
            expected_latest_event_id=created.latest_event_id,
        )
        assert revised.subject == "edit"


class TestAbandon:
    def test_abandons_an_active_draft(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent()
        )
        view = service.abandon(created.draft_id)
        assert view.status == "abandoned"

    def test_is_idempotent(self, service, existing_case, draft_repository):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent()
        )
        service.abandon(created.draft_id)
        service.abandon(created.draft_id)

        history = draft_repository.list_events(created.draft_id)
        abandon_events = [event for event in history if event.event_type == "abandoned"]
        assert len(abandon_events) == 1  # only one abandoned event was ever written

    def test_rejects_abandoning_a_committed_draft(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=_complete_content()
        )
        service.commit(created.draft_id)

        with pytest.raises(DecisionDraftAlreadyCommittedError):
            service.abandon(created.draft_id)

    def test_rejects_abandoning_an_unknown_draft(self, service):
        from atlas.core.domain.decision_draft.value_objects import DraftId

        with pytest.raises(DecisionDraftNotFoundError):
            service.abandon(DraftId())


def _complete_content(**overrides) -> DecisionDraftContent:
    defaults = dict(
        decision_type="BUY",
        subject="ASML",
        reason="Durable moat, undervalued relative to peers",
        confidence=75,
        decided_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return DecisionDraftContent(**defaults)


class TestCommit:
    def test_constructs_a_real_decision_via_the_unmodified_register(
        self, service, existing_case, decision_repository
    ):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=_complete_content()
        )

        result = service.commit(created.draft_id)

        assert result.decision.subject.value == "ASML"
        assert result.decision.investment_case.reason.startswith("Durable moat")
        assert result.decision.confidence.value == 75
        assert result.decision.case_id == existing_case.id
        assert decision_repository.get(result.decision.id) == result.decision

    def test_constructs_a_real_decision_context_when_situation_is_present(
        self, service, existing_case, decision_context_repository
    ):
        created = service.create(
            case_id=existing_case.id,
            user_id=_user_id(),
            content=_complete_content(
                situation="Large exposure already",
                alternatives_considered=("Buy Arm",),
                uncertainties=("Fed announcement",),
            ),
        )

        result = service.commit(created.draft_id)

        assert result.decision_context is not None
        assert result.decision_context.situation.value == "Large exposure already"
        assert result.decision_context.decision_id == result.decision.id
        stored = decision_context_repository.get_by_decision_id(result.decision.id)
        assert stored == result.decision_context

    def test_no_decision_context_when_situation_is_absent(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=_complete_content()
        )

        result = service.commit(created.draft_id)

        assert result.decision_context is None

    def test_marks_the_draft_committed_with_the_decision_id_backreference(
        self, service, existing_case
    ):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=_complete_content()
        )

        result = service.commit(created.draft_id)

        assert result.draft.status == "committed"
        assert result.draft.committed_decision_id == str(result.decision.id.value)

    def test_propagates_missing_subject_unmodified(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id,
            user_id=_user_id(),
            content=_complete_content(subject=None),
        )
        with pytest.raises(MissingSubjectError):
            service.commit(created.draft_id)

    def test_propagates_missing_reason_unmodified(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id,
            user_id=_user_id(),
            content=_complete_content(reason=None),
        )
        with pytest.raises(MissingReasonError):
            service.commit(created.draft_id)

    def test_propagates_invalid_confidence_unmodified(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id,
            user_id=_user_id(),
            content=_complete_content(confidence=150),
        )
        with pytest.raises(InvalidConfidenceError):
            service.commit(created.draft_id)

    def test_does_not_create_a_duplicate_decision_on_recommit(
        self, service, existing_case, decision_repository
    ):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=_complete_content()
        )
        service.commit(created.draft_id)

        with pytest.raises(DecisionDraftAlreadyCommittedError):
            service.commit(created.draft_id)

        assert len(decision_repository.list_all()) == 1  # no second Decision was created

    def test_rejects_committing_an_abandoned_draft(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=_complete_content()
        )
        service.abandon(created.draft_id)

        with pytest.raises(DecisionDraftAlreadyAbandonedError):
            service.commit(created.draft_id)

    def test_rejects_committing_an_unknown_draft(self, service):
        from atlas.core.domain.decision_draft.value_objects import DraftId

        with pytest.raises(DecisionDraftNotFoundError):
            service.commit(DraftId())


class TestGet:
    def test_returns_the_current_view(self, service, existing_case):
        created = service.create(
            case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent(subject="ASML")
        )
        view = service.get(created.draft_id)
        assert view.subject == "ASML"

    def test_rejects_an_unknown_draft(self, service):
        from atlas.core.domain.decision_draft.value_objects import DraftId

        with pytest.raises(DecisionDraftNotFoundError):
            service.get(DraftId())


class TestListActiveForCase:
    def test_returns_only_active_drafts(self, service, existing_case):
        user_id = _user_id()
        active = service.create(case_id=existing_case.id, user_id=user_id, content=DecisionDraftContent())
        abandoned = service.create(case_id=existing_case.id, user_id=user_id, content=DecisionDraftContent())
        service.abandon(abandoned.draft_id)

        views = service.list_active_for_case(existing_case.id)

        assert {view.draft_id for view in views} == {active.draft_id}

    def test_returns_empty_list_for_a_case_with_no_drafts(self, service, existing_case):
        assert service.list_active_for_case(existing_case.id) == []


class TestDailyBriefSummary:
    def test_returns_only_narrow_fields_for_active_drafts(self, service, existing_case):
        user_id = _user_id()
        service.create(
            case_id=existing_case.id,
            user_id=user_id,
            content=_complete_content(subject="ASML"),
        )

        summaries = service.daily_brief_summary(user_id)

        assert len(summaries) == 1
        summary = summaries[0]
        assert summary.subject == "ASML"
        assert summary.case_id == existing_case.id
        # DecisionDraftSummary has no reason/confidence/situation fields at all --
        # the narrow-projection invariant enforced by the type itself.
        assert not hasattr(summary, "reason")
        assert not hasattr(summary, "confidence")
        assert not hasattr(summary, "situation")

    def test_excludes_committed_and_abandoned_drafts(self, service, existing_case):
        user_id = _user_id()
        committed = service.create(
            case_id=existing_case.id, user_id=user_id, content=_complete_content()
        )
        service.commit(committed.draft_id)
        abandoned = service.create(
            case_id=existing_case.id, user_id=user_id, content=DecisionDraftContent()
        )
        service.abandon(abandoned.draft_id)

        assert service.daily_brief_summary(user_id) == []

    def test_excludes_other_users_drafts(self, service, existing_case):
        service.create(case_id=existing_case.id, user_id=_user_id(), content=DecisionDraftContent())
        assert service.daily_brief_summary(_user_id()) == []

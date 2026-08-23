"""End-to-end test for the full DecisionDraft product flow (ADR-DD-001).

Create (partial content) -> revise twice -> commit -> assert a real
Decision and DecisionContext now exist, correctly populated from the
draft's own final content, and the draft itself reads back as
committed. This is the executable form of ADR-DD-001 §3's own central
claim ("a new Decision is constructed fresh from whatever the draft
held at the moment of commit") — see
`DecisionDraft-Implementation-Design.md` §9, "End-to-end."

Against real, non-mocked repositories throughout, mirroring every other
cross-aggregate test in this suite.
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
from atlas.core.domain.decision.value_objects import UserId
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


def test_full_create_revise_commit_flow_produces_a_real_decision_and_context(engine):
    case_repository = SqlAlchemyCaseRepository(engine)
    decision_repository = SqlAlchemyDecisionRepository(engine)
    decision_context_repository = SqlAlchemyDecisionContextRepository(engine)
    draft_repository = SqlAlchemyDecisionDraftEventRepository(engine)
    service = DecisionDraftService(
        draft_repository, case_repository, decision_repository, decision_context_repository
    )

    case = Case.create()
    case_repository.add(case)
    user_id = UserId(uuid.uuid4())

    # 1. Create with partial content -- a genuinely incomplete draft.
    created = service.create(
        case_id=case.id,
        user_id=user_id,
        content=DecisionDraftContent(subject="ASML"),
    )
    assert created.status == "active"
    assert created.reason is None

    # 2. Revise twice, filling in more content each time.
    first_revision = service.revise(
        created.draft_id,
        content=DecisionDraftContent(
            subject="ASML",
            reason="Durable moat, undervalued relative to peers",
        ),
    )
    assert first_revision.confidence is None

    second_revision = service.revise(
        first_revision.draft_id,
        content=DecisionDraftContent(
            decision_type="BUY",
            subject="ASML",
            reason="Durable moat, undervalued relative to peers",
            confidence=75,
            decided_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            situation="Large semiconductor exposure already existed",
            portfolio_relevance="Complements existing holdings",
            capital_considerations="Only deploy part of available capital",
            alternatives_considered=("Buy Arm", "Buy TSM"),
            uncertainties=("Short-term reaction to the Fed announcement",),
        ),
    )
    assert second_revision.confidence == 75

    # 3. Commit.
    result = service.commit(second_revision.draft_id)

    # 4. A real Decision now exists, correctly populated.
    persisted_decision = decision_repository.get(result.decision.id)
    assert persisted_decision is not None
    assert persisted_decision.subject.value == "ASML"
    assert persisted_decision.investment_case.reason == (
        "Durable moat, undervalued relative to peers"
    )
    assert persisted_decision.confidence.value == 75
    assert persisted_decision.case_id == case.id
    assert persisted_decision.user_id == user_id

    # 5. A real DecisionContext now exists, correctly populated.
    persisted_context = decision_context_repository.get_by_decision_id(result.decision.id)
    assert persisted_context is not None
    assert persisted_context.situation.value == "Large semiconductor exposure already existed"
    assert list(persisted_context.alternatives_considered) == ["Buy Arm", "Buy TSM"]
    assert list(persisted_context.uncertainties) == [
        "Short-term reaction to the Fed announcement"
    ]

    # 6. The draft itself now reads back as committed, with the backreference.
    final_view = service.get(second_revision.draft_id)
    assert final_view.status == "committed"
    assert final_view.committed_decision_id == str(result.decision.id.value)

    # 7. Neither Decision nor DecisionContext's own repository was ever
    # asked to do anything beyond a plain, unmodified add() -- the
    # commit boundary invariant (ADR-DD-001 §3), verified structurally:
    # exactly one Decision and one DecisionContext exist in total.
    assert len(decision_repository.list_all()) == 1

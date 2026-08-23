"""End-to-end test for the full Assumption product flow (ADR-AS-001),
including its integration with `Decision` and `CaseCondition`.

Create (anchored to a real Decision) -> revise -> attach a real
CaseCondition -> challenge -> reaffirm via revise -> supersede with a
replacement. Against real, non-mocked repositories throughout,
mirroring `tests/unit/application/case_condition/test_end_to_end.py`
(Sprint 10).
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


def test_full_create_revise_attach_challenge_reaffirm_supersede_flow(engine):
    case_repository = SqlAlchemyCaseRepository(engine)
    decision_repository = SqlAlchemyDecisionRepository(engine)
    case_condition_repository = SqlAlchemyCaseConditionEventRepository(engine)
    assumption_repository = SqlAlchemyAssumptionEventRepository(engine)

    case_condition_service = CaseConditionService(
        case_condition_repository, case_repository, decision_repository
    )
    assumption_service = AssumptionService(
        assumption_repository, decision_repository, case_condition_repository
    )

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

    # 1. Create an Assumption anchored to this Decision. case_id is
    # derived transitively, never separately supplied.
    created = assumption_service.create(
        decision_id=decision.id,
        content=AssumptionContent(statement="GCP margin expansion continues", authorship="atlas"),
    )
    assert created.decision_id == decision.id
    assert created.case_id == case.id
    assert created.status == "supported"

    # 2. The investor edits Atlas's own proposal -- authorship transfers.
    revised = assumption_service.revise(
        created.assumption_id,
        content=AssumptionContent(statement="GCP margin expansion continues through 2027", authorship="user"),
    )
    assert revised.authorship == "user"

    # 3. Create a real CaseCondition and attach it -- a loose,
    # optional cross-reference using existing ids only (ADR-AS-001 §8).
    condition = case_condition_service.create(
        case_id=case.id, decision_id=decision.id,
        content=CaseConditionContent(predicate_text="GCP margin trend", role="monitoring"),
    )
    attached = assumption_service.attach_case_condition(revised.assumption_id, condition.condition_id)
    assert attached.linked_case_condition_ids == (str(condition.condition_id),)

    # 4. New evidence challenges the assumption.
    challenged = assumption_service.challenge(
        attached.assumption_id, note="GCP margin growth decelerated last quarter", severity="challenged"
    )
    assert challenged.status == "challenged"
    assert challenged.linked_case_condition_ids == (str(condition.condition_id),)  # link survives a challenge

    # 5. The investor reviews the evidence and reaffirms, revising the
    # statement -- status resets to supported, the CaseCondition link
    # is preserved (revise() carries forward the current link set).
    reaffirmed = assumption_service.revise(
        challenged.assumption_id,
        content=AssumptionContent(
            statement="GCP margin expansion continues, though more slowly than expected", authorship="user"
        ),
    )
    assert reaffirmed.status == "supported"
    assert reaffirmed.linked_case_condition_ids == (str(condition.condition_id),)

    # 6. Later, the investor decides this assumption is superseded by
    # a fresh, more precise one.
    replacement = assumption_service.create(decision_id=decision.id, content=AssumptionContent())
    final = assumption_service.supersede(
        reaffirmed.assumption_id, superseded_by_assumption_id=str(replacement.assumption_id)
    )
    assert final.status == "superseded"
    assert final.superseded_by_assumption_id == str(replacement.assumption_id)
    assert final.is_active is False

    # 7. Neither Decision, Case, nor the CaseCondition it referenced
    # was ever mutated by any of this.
    assert decision_repository.get(decision.id) == decision
    assert case_repository.get(case.id) == case
    assert case_condition_repository.get_latest_event(condition.condition_id).event_type == "revised"

    # 8. Full history is intact and correctly ordered.
    history = assumption_service.list_events(reaffirmed.assumption_id)
    assert [event.event_type for event in history] == [
        "revised",  # create
        "revised",  # authorship transfer
        "revised",  # attach
        "challenged",
        "revised",  # reaffirm
        "superseded",
    ]

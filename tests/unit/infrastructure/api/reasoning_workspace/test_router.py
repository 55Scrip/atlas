"""API tests for the Reasoning Workspace REST controller (Sprint 12)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.entity import Case
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.assumption.dependencies import get_assumption_repository
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.case_condition.dependencies import (
    get_case_condition_repository,
)
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.decision_context.dependencies import (
    get_decision_context_repository,
)
from atlas.core.infrastructure.api.decision_draft.dependencies import (
    get_decision_draft_repository,
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
def repositories():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_case_table(engine)
    create_decision_table(engine)
    create_decision_context_table(engine)
    create_decision_draft_events_table(engine)
    create_case_condition_events_table(engine)
    create_assumption_events_table(engine)
    return {
        "case": SqlAlchemyCaseRepository(engine),
        "decision": SqlAlchemyDecisionRepository(engine),
        "decision_context": SqlAlchemyDecisionContextRepository(engine),
        "decision_draft": SqlAlchemyDecisionDraftEventRepository(engine),
        "case_condition": SqlAlchemyCaseConditionEventRepository(engine),
        "assumption": SqlAlchemyAssumptionEventRepository(engine),
    }


@pytest.fixture
def client(repositories):
    app = create_app()
    app.dependency_overrides[get_case_repository] = lambda: repositories["case"]
    app.dependency_overrides[get_decision_repository] = lambda: repositories["decision"]
    app.dependency_overrides[get_decision_context_repository] = (
        lambda: repositories["decision_context"]
    )
    app.dependency_overrides[get_decision_draft_repository] = lambda: repositories["decision_draft"]
    app.dependency_overrides[get_case_condition_repository] = lambda: repositories["case_condition"]
    app.dependency_overrides[get_assumption_repository] = lambda: repositories["assumption"]
    return TestClient(app)


@pytest.fixture
def existing_case(repositories) -> Case:
    case = Case.create()
    repositories["case"].add(case)
    return case


def _complete_draft_payload(**overrides) -> dict:
    payload = {
        "userId": str(uuid.uuid4()),
        "decisionType": "BUY",
        "subject": "ASML",
        "reason": "Durable moat, undervalued relative to peers",
        "confidence": 75,
    }
    payload.update(overrides)
    return payload


class TestCommitDraftWithReasoning:
    def test_commits_and_creates_assumptions_and_conditions(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_complete_draft_payload()
        ).json()

        response = client.post(
            f"/decision-drafts/{created['draftId']}/commit-with-reasoning",
            json={
                "assumptions": [
                    {
                        "statement": "GCP margin expansion continues",
                        "authorship": "atlas",
                        "linkedConditions": [
                            {"predicateText": "GCP margin trend", "role": "monitoring"}
                        ],
                    }
                ],
                "standaloneCaseConditions": [{"predicateText": "Review in 90 days"}],
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["subject"] == "ASML"
        assert body["draft"]["status"] == "committed"
        assert len(body["assumptions"]) == 1
        assert body["assumptions"][0]["statement"] == "GCP margin expansion continues"
        assert len(body["caseConditions"]) == 2  # one linked + one standalone
        linked_condition_id = body["assumptions"][0]["linkedCaseConditionIds"][0]
        assert linked_condition_id in [c["conditionId"] for c in body["caseConditions"]]

    def test_commit_alone_with_no_reasoning_payload(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_complete_draft_payload()
        ).json()

        response = client.post(
            f"/decision-drafts/{created['draftId']}/commit-with-reasoning", json={}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["assumptions"] == []
        assert body["caseConditions"] == []

    def test_returns_422_for_missing_subject(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_complete_draft_payload(subject=None),
        ).json()

        response = client.post(
            f"/decision-drafts/{created['draftId']}/commit-with-reasoning", json={}
        )

        assert response.status_code == 422

    def test_returns_404_for_an_unknown_draft(self, client):
        response = client.post(
            f"/decision-drafts/{uuid.uuid4()}/commit-with-reasoning", json={}
        )
        assert response.status_code == 404


class TestGetDecisionReasoningWorkspace:
    def test_assembles_the_full_workspace(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_complete_draft_payload()
        ).json()
        commit = client.post(
            f"/decision-drafts/{created['draftId']}/commit-with-reasoning",
            json={"assumptions": [{"statement": "GCP margin expansion continues"}]},
        ).json()

        response = client.get(f"/decisions/{commit['decision']['id']}/reasoning-workspace")

        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["id"] == commit["decision"]["id"]
        assert body["originatingDraft"]["draftId"] == created["draftId"]
        assert body["originatingDraft"]["status"] == "committed"
        assert len(body["assumptions"]) == 1
        assert body["activeCaseDrafts"] == []

    def test_returns_404_for_an_unknown_decision(self, client):
        response = client.get(f"/decisions/{uuid.uuid4()}/reasoning-workspace")
        assert response.status_code == 404


class TestReadModelEndpoints:
    def test_active_assumptions(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_complete_draft_payload()
        ).json()
        client.post(
            f"/decision-drafts/{created['draftId']}/commit-with-reasoning",
            json={"assumptions": [{"statement": "GCP margin expansion continues"}]},
        )

        response = client.get(f"/cases/{existing_case.id.value}/reasoning/active-assumptions")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["statement"] == "GCP margin expansion continues"

    def test_active_case_conditions(self, client, existing_case):
        client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={"predicateText": "Review in 90 days"},
        )

        response = client.get(f"/cases/{existing_case.id.value}/reasoning/active-case-conditions")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_open_decision_drafts(self, client, existing_case):
        user_id = str(uuid.uuid4())
        client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json={"userId": user_id, "subject": "ASML"},
        )

        response = client.get("/reasoning/open-decision-drafts", params={"userId": user_id})

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["subject"] == "ASML"
        assert set(response.json()[0].keys()) == {"draftId", "caseId", "subject", "createdAt"}

"""API tests for the DecisionDraft REST controller (ADR-DD-001)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.entity import Case
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.decision_context.dependencies import (
    get_decision_context_repository,
)
from atlas.core.infrastructure.api.decision_draft.dependencies import (
    get_decision_draft_repository,
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
    return {
        "case": SqlAlchemyCaseRepository(engine),
        "decision": SqlAlchemyDecisionRepository(engine),
        "decision_context": SqlAlchemyDecisionContextRepository(engine),
        "decision_draft": SqlAlchemyDecisionDraftEventRepository(engine),
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
    return TestClient(app)


@pytest.fixture
def existing_case(repositories) -> Case:
    case = Case.create()
    repositories["case"].add(case)
    return case


def _create_payload(**overrides) -> dict:
    payload = {"userId": str(uuid.uuid4())}
    payload.update(overrides)
    return payload


def _complete_payload(**overrides) -> dict:
    payload = _create_payload(
        decisionType="BUY",
        subject="ASML",
        reason="Durable moat, undervalued relative to peers",
        confidence=75,
    )
    payload.update(overrides)
    return payload


class TestCreateDecisionDraft:
    def test_returns_201_with_the_created_draft(self, client, existing_case):
        response = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_create_payload(subject="ASML"),
        )
        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["draftId"])
        assert body["caseId"] == str(existing_case.id.value)
        assert body["status"] == "active"
        assert body["subject"] == "ASML"
        assert body["reason"] is None

    def test_returns_404_for_an_unknown_case(self, client):
        response = client.post(
            f"/cases/{uuid.uuid4()}/decision-drafts", json=_create_payload()
        )
        assert response.status_code == 404


class TestListDecisionDraftsForCase:
    def test_returns_only_active_drafts(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_create_payload()
        ).json()
        abandoned = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_create_payload()
        ).json()
        client.post(f"/decision-drafts/{abandoned['draftId']}/abandon")

        response = client.get(f"/cases/{existing_case.id.value}/decision-drafts")

        assert response.status_code == 200
        draft_ids = {draft["draftId"] for draft in response.json()}
        assert draft_ids == {created["draftId"]}


class TestGetDecisionDraft:
    def test_returns_the_current_state(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_create_payload(subject="ASML"),
        ).json()

        response = client.get(f"/decision-drafts/{created['draftId']}")

        assert response.status_code == 200
        assert response.json()["subject"] == "ASML"

    def test_returns_404_for_an_unknown_draft(self, client):
        response = client.get(f"/decision-drafts/{uuid.uuid4()}")
        assert response.status_code == 404


class TestListDecisionDraftEvents:
    def test_returns_full_history(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_create_payload()
        ).json()
        client.patch(f"/decision-drafts/{created['draftId']}", json={"subject": "ASML"})

        response = client.get(f"/decision-drafts/{created['draftId']}/events")

        assert response.status_code == 200
        events = response.json()
        assert len(events) == 2
        assert [event["eventType"] for event in events] == ["revised", "revised"]


class TestReviseDecisionDraft:
    def test_returns_200_with_the_revised_content(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_create_payload(subject="ASML"),
        ).json()

        response = client.patch(
            f"/decision-drafts/{created['draftId']}", json={"subject": "ASML Holding NV"}
        )

        assert response.status_code == 200
        assert response.json()["subject"] == "ASML Holding NV"

    def test_returns_409_on_a_stale_expected_latest_event_id(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_create_payload()
        ).json()
        client.patch(f"/decision-drafts/{created['draftId']}", json={"subject": "first edit"})

        response = client.patch(
            f"/decision-drafts/{created['draftId']}",
            json={
                "subject": "second edit",
                "expectedLatestEventId": created["latestEventId"],
            },
        )

        assert response.status_code == 409

    def test_returns_409_when_already_abandoned(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_create_payload()
        ).json()
        client.post(f"/decision-drafts/{created['draftId']}/abandon")

        response = client.patch(f"/decision-drafts/{created['draftId']}", json={})

        assert response.status_code == 409

    def test_returns_404_for_an_unknown_draft(self, client):
        response = client.patch(f"/decision-drafts/{uuid.uuid4()}", json={})
        assert response.status_code == 404


class TestAbandonDecisionDraft:
    def test_returns_204(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_create_payload()
        ).json()

        response = client.post(f"/decision-drafts/{created['draftId']}/abandon")

        assert response.status_code == 204
        assert client.get(f"/decision-drafts/{created['draftId']}").json()["status"] == "abandoned"

    def test_is_idempotent(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_create_payload()
        ).json()

        first = client.post(f"/decision-drafts/{created['draftId']}/abandon")
        second = client.post(f"/decision-drafts/{created['draftId']}/abandon")

        assert first.status_code == 204
        assert second.status_code == 204

    def test_returns_409_for_a_committed_draft(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_complete_payload(),
        ).json()
        client.post(f"/decision-drafts/{created['draftId']}/commit")

        response = client.post(f"/decision-drafts/{created['draftId']}/abandon")

        assert response.status_code == 409


class TestCommitDecisionDraft:
    def test_returns_200_with_the_composed_response(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_complete_payload(),
        ).json()

        response = client.post(f"/decision-drafts/{created['draftId']}/commit")

        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["subject"] == "ASML"
        assert body["decisionContext"] is None
        assert body["draft"]["status"] == "committed"
        assert body["draft"]["committedDecisionId"] == body["decision"]["id"]

    def test_includes_decision_context_when_situation_is_present(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_complete_payload(situation="Large exposure already"),
        ).json()

        response = client.post(f"/decision-drafts/{created['draftId']}/commit")

        assert response.status_code == 200
        assert response.json()["decisionContext"]["situation"] == "Large exposure already"

    def test_returns_422_for_missing_subject(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_complete_payload(subject=None),
        ).json()

        response = client.post(f"/decision-drafts/{created['draftId']}/commit")

        assert response.status_code == 422

    def test_returns_409_on_recommit(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_complete_payload(),
        ).json()
        client.post(f"/decision-drafts/{created['draftId']}/commit")

        response = client.post(f"/decision-drafts/{created['draftId']}/commit")

        assert response.status_code == 409

    def test_returns_404_for_an_unknown_draft(self, client):
        response = client.post(f"/decision-drafts/{uuid.uuid4()}/commit")
        assert response.status_code == 404


class TestDailyBriefSummary:
    def test_returns_only_narrow_fields(self, client, existing_case):
        user_id = str(uuid.uuid4())
        client.post(
            f"/cases/{existing_case.id.value}/decision-drafts",
            json=_complete_payload(userId=user_id, situation="Large exposure already"),
        )

        response = client.get("/decision-drafts/daily-brief-summary", params={"userId": user_id})

        assert response.status_code == 200
        summaries = response.json()
        assert len(summaries) == 1
        summary = summaries[0]
        assert set(summary.keys()) == {"draftId", "caseId", "subject", "createdAt"}
        assert "reason" not in summary
        assert "confidence" not in summary
        assert "situation" not in summary

    def test_is_routed_before_the_draft_id_path_and_never_matched_as_one(self, client):
        response = client.get(
            "/decision-drafts/daily-brief-summary", params={"userId": str(uuid.uuid4())}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_excludes_other_users(self, client, existing_case):
        client.post(
            f"/cases/{existing_case.id.value}/decision-drafts", json=_complete_payload()
        )

        response = client.get(
            "/decision-drafts/daily-brief-summary", params={"userId": str(uuid.uuid4())}
        )

        assert response.json() == []

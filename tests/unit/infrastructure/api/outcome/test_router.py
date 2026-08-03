"""API tests for the Outcome REST controller (ATLAS-001 Core Loop).

Outcome's first REST API of any kind (Atlas Alpha, Outcome Sprint 1).
Per ADR-004, the wire format is camelCase.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table

_DECIDED_AT = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
_OCCURRED_AT = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(eng)
    create_outcome_table(eng)
    return eng


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def outcome_repository(engine):
    return SqlAlchemyOutcomeRepository(engine)


@pytest.fixture
def client(decision_repository, outcome_repository):
    app = create_app()
    app.dependency_overrides[get_decision_repository] = lambda: decision_repository
    app.dependency_overrides[get_outcome_repository] = lambda: outcome_repository
    return TestClient(app)


def _seed_decision(decision_repository, *, case_id: uuid.UUID | None = None) -> Decision:
    decision = Decision.register(
        case_id=CaseId(case_id) if case_id is not None else CaseId(),
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("NVIDIA"),
        investment_case=InvestmentCase("Demand for AI infrastructure is accelerating."),
        confidence=Confidence(80),
        decided_at=_DECIDED_AT,
    )
    decision_repository.add(decision)
    return decision


def _valid_payload(decision_id, **overrides) -> dict:
    payload = {
        "decisionId": str(decision_id),
        "statement": "Revenue growth accelerated as expected.",
        "occurredAt": _OCCURRED_AT.isoformat(),
        "note": "Confirmed by the following quarter's report.",
    }
    payload.update(overrides)
    return payload


class TestCreateOutcome:
    def test_returns_201_with_the_recorded_outcome(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        response = client.post("/outcomes", json=_valid_payload(decision.id.value))

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["id"])
        assert body["decisionId"] == str(decision.id.value)
        assert body["caseId"] == str(decision.case_id.value)
        assert body["statement"] == "Revenue growth accelerated as expected."
        assert body["note"] == "Confirmed by the following quarter's report."
        assert "occurredAt" in body
        assert "recordedAt" in body

    def test_case_id_is_derived_from_the_decision_not_caller_supplied(
        self, client, decision_repository
    ):
        decision = _seed_decision(decision_repository)
        response = client.post("/outcomes", json=_valid_payload(decision.id.value))
        assert response.json()["caseId"] == str(decision.case_id.value)

    def test_omitting_note_is_accepted(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        payload = _valid_payload(decision.id.value)
        del payload["note"]
        response = client.post("/outcomes", json=payload)
        assert response.status_code == 201
        assert response.json()["note"] is None

    def test_persists_the_outcome_so_it_can_be_read_back(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        created = client.post("/outcomes", json=_valid_payload(decision.id.value)).json()
        fetched = client.get(f"/outcomes/{created['id']}")
        assert fetched.status_code == 200
        assert fetched.json() == created

    def test_a_decision_may_accrue_multiple_outcomes(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        first = client.post("/outcomes", json=_valid_payload(decision.id.value)).json()
        second = client.post("/outcomes", json=_valid_payload(decision.id.value)).json()
        assert first["id"] != second["id"]
        assert first["decisionId"] == second["decisionId"]


class TestCreateOutcomeValidationFailures:
    def test_rejects_an_unknown_decision(self, client):
        response = client.post("/outcomes", json=_valid_payload(uuid.uuid4()))
        assert response.status_code == 400

    def test_rejects_blank_statement(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        response = client.post("/outcomes", json=_valid_payload(decision.id.value, statement="   "))
        assert response.status_code == 400

    def test_rejects_missing_decision_id(self, client):
        payload = _valid_payload(uuid.uuid4())
        del payload["decisionId"]
        response = client.post("/outcomes", json=payload)
        assert response.status_code == 422

    def test_rejects_malformed_decision_id(self, client):
        payload = _valid_payload(uuid.uuid4())
        payload["decisionId"] = "not-a-uuid"
        response = client.post("/outcomes", json=payload)
        assert response.status_code == 422

    def test_rejects_missing_occurred_at(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        payload = _valid_payload(decision.id.value)
        del payload["occurredAt"]
        response = client.post("/outcomes", json=payload)
        assert response.status_code == 422


class TestListOutcomes:
    def test_returns_empty_list_when_nothing_recorded(self, client):
        response = client.get("/outcomes")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_every_recorded_outcome(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        first = client.post(
            "/outcomes", json=_valid_payload(decision.id.value, statement="First reading.")
        ).json()
        second = client.post(
            "/outcomes", json=_valid_payload(decision.id.value, statement="Final reading.")
        ).json()

        response = client.get("/outcomes")

        assert response.status_code == 200
        ids = {outcome["id"] for outcome in response.json()}
        assert ids == {first["id"], second["id"]}


class TestGetOutcome:
    def test_returns_404_for_unknown_id(self, client):
        response = client.get(f"/outcomes/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_rejects_malformed_id(self, client):
        response = client.get("/outcomes/not-a-uuid")
        assert response.status_code == 422


class TestNoDeleteOrUpdate:
    def test_no_delete_route_exists(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        created = client.post("/outcomes", json=_valid_payload(decision.id.value)).json()
        response = client.delete(f"/outcomes/{created['id']}")
        assert response.status_code == 405

    def test_no_patch_route_exists(self, client, decision_repository):
        decision = _seed_decision(decision_repository)
        created = client.post("/outcomes", json=_valid_payload(decision.id.value)).json()
        response = client.patch(f"/outcomes/{created['id']}", json={"statement": "Revised."})
        assert response.status_code == 405


class TestAppMounting:
    def test_outcome_router_is_mounted(self):
        app = create_app()
        paths = set(app.openapi()["paths"])
        assert "/outcomes" in paths
        assert "/outcomes/{outcome_id}" in paths

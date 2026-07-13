"""API tests for the Decision Capture REST controller (API-001)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    repository = SqlAlchemyDecisionRepository(engine)

    app = create_app()
    app.dependency_overrides[get_decision_repository] = lambda: repository
    return TestClient(app)


def _valid_payload(**overrides) -> dict:
    payload = {
        "user_id": str(uuid.uuid4()),
        "decision_type": "BUY",
        "reason": "Durable moat, undervalued relative to peers",
        "confidence": 75,
        "subject": "ASML",
    }
    payload.update(overrides)
    return payload


class TestCreateDecision:
    def test_returns_201_with_the_recorded_decision(self, client):
        payload = _valid_payload()
        response = client.post("/decisions", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["decision_type"] == "BUY"
        assert body["reason"] == payload["reason"]
        assert body["confidence"] == 75
        assert body["subject"] == "ASML"
        assert body["source"] == "Manual"
        assert uuid.UUID(body["id"])
        assert uuid.UUID(body["user_id"]) == uuid.UUID(payload["user_id"])

    def test_communicates_that_atlas_is_still_learning(self, client):
        response = client.post("/decisions", json=_valid_payload())
        assert "does not yet understand" in response.json()["message"]

    def test_defaults_source_to_manual_when_omitted(self, client):
        response = client.post("/decisions", json=_valid_payload())
        assert response.json()["source"] == "Manual"

    def test_accepts_an_explicit_source(self, client):
        response = client.post("/decisions", json=_valid_payload(source="BrokerSync"))
        assert response.status_code == 201
        assert response.json()["source"] == "BrokerSync"

    def test_persists_the_decision_so_it_can_be_read_back(self, client):
        created = client.post("/decisions", json=_valid_payload()).json()
        fetched = client.get(f"/decisions/{created['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == created["id"]


class TestCreateDecisionValidationFailures:
    def test_rejects_missing_reason(self, client):
        response = client.post("/decisions", json=_valid_payload(reason=""))
        assert response.status_code == 422

    def test_rejects_missing_subject(self, client):
        response = client.post("/decisions", json=_valid_payload(subject=""))
        assert response.status_code == 422

    def test_rejects_missing_decision_type(self, client):
        response = client.post("/decisions", json=_valid_payload(decision_type=""))
        assert response.status_code == 422

    def test_rejects_invalid_decision_type(self, client):
        response = client.post("/decisions", json=_valid_payload(decision_type="STRONG_BUY"))
        assert response.status_code == 422

    @pytest.mark.parametrize("confidence", [-1, 101, 1000])
    def test_rejects_confidence_outside_0_100(self, client, confidence):
        response = client.post("/decisions", json=_valid_payload(confidence=confidence))
        assert response.status_code == 422

    def test_rejects_malformed_user_id(self, client):
        response = client.post("/decisions", json=_valid_payload(user_id="not-a-uuid"))
        assert response.status_code == 422

    def test_rejects_unknown_source(self, client):
        response = client.post("/decisions", json=_valid_payload(source="Telepathy"))
        assert response.status_code == 422


class TestListDecisions:
    def test_returns_empty_list_when_nothing_recorded(self, client):
        response = client.get("/decisions")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_every_recorded_decision(self, client):
        client.post("/decisions", json=_valid_payload(subject="ASML"))
        client.post("/decisions", json=_valid_payload(subject="MSFT"))

        response = client.get("/decisions")

        assert response.status_code == 200
        subjects = {decision["subject"] for decision in response.json()}
        assert subjects == {"ASML", "MSFT"}


class TestGetDecision:
    def test_returns_the_matching_decision(self, client):
        created = client.post("/decisions", json=_valid_payload()).json()
        created.pop("message")

        response = client.get(f"/decisions/{created['id']}")

        assert response.status_code == 200
        assert response.json() == created

    def test_returns_404_for_unknown_id(self, client):
        response = client.get(f"/decisions/{uuid.uuid4()}")
        assert response.status_code == 404

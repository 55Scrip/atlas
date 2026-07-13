"""API tests for the Hypothesis Capture REST controller (API-004)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.hypothesis.dependencies import get_hypothesis_repository
from atlas.core.infrastructure.persistence.hypothesis.sqlalchemy_repository import (
    SqlAlchemyHypothesisRepository,
)
from atlas.core.infrastructure.persistence.hypothesis.table import create_hypothesis_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_hypothesis_table(engine)
    repository = SqlAlchemyHypothesisRepository(engine)

    app = create_app()
    app.dependency_overrides[get_hypothesis_repository] = lambda: repository
    return TestClient(app)


def _valid_payload(**overrides) -> dict:
    payload = {
        "statement": (
            "Demand for AI infrastructure may be accelerating faster than "
            "the market expects."
        ),
        "note": "Revisit after the next reporting cycle.",
        "formulatedAt": "2026-07-13T18:30:00+02:00",
    }
    payload.update(overrides)
    return payload


class TestCreateHypothesis:
    def test_returns_201_with_the_recorded_hypothesis(self, client):
        payload = _valid_payload()
        response = client.post("/hypotheses", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["hypothesisId"])
        assert body["statement"] == payload["statement"]
        assert body["note"] == "Revisit after the next reporting cycle."
        assert body["formulatedAt"] == "2026-07-13T18:30:00+02:00"
        assert "recordedAt" in body

    def test_optional_note_may_be_omitted(self, client):
        payload = {
            "statement": "The company's margin pressure may be temporary rather than structural.",
            "formulatedAt": "2026-07-13T18:30:00+02:00",
        }
        response = client.post("/hypotheses", json=payload)

        assert response.status_code == 201
        assert response.json()["note"] is None

    def test_blank_note_normalizes_to_none(self, client):
        response = client.post("/hypotheses", json=_valid_payload(note="   "))
        assert response.status_code == 201
        assert response.json()["note"] is None

    def test_accepts_snake_case_request_body_for_backward_compatibility(self, client):
        payload = {
            "statement": (
                "Higher interest rates may create refinancing risk for "
                "smaller property companies."
            ),
            "formulated_at": "2026-07-13T18:30:00+02:00",
        }
        response = client.post("/hypotheses", json=payload)
        assert response.status_code == 201
        assert response.json()["statement"] == payload["statement"]

    def test_persists_the_hypothesis_so_it_can_be_read_back(self, client):
        created = client.post("/hypotheses", json=_valid_payload()).json()
        fetched = client.get(f"/hypotheses/{created['hypothesisId']}")
        assert fetched.status_code == 200
        assert fetched.json()["hypothesisId"] == created["hypothesisId"]


class TestCreateHypothesisValidationFailures:
    def test_rejects_blank_statement(self, client):
        response = client.post("/hypotheses", json=_valid_payload(statement="   "))
        assert response.status_code == 400

    def test_rejects_empty_statement(self, client):
        response = client.post("/hypotheses", json=_valid_payload(statement=""))
        assert response.status_code == 400

    def test_rejects_missing_formulated_at(self, client):
        payload = _valid_payload()
        del payload["formulatedAt"]
        response = client.post("/hypotheses", json=payload)
        assert response.status_code == 422  # malformed request shape, FastAPI default

    def test_rejects_malformed_formulated_at(self, client):
        response = client.post(
            "/hypotheses", json=_valid_payload(formulatedAt="not-a-datetime")
        )
        assert response.status_code == 422


class TestListHypotheses:
    def test_returns_empty_list_when_nothing_recorded(self, client):
        response = client.get("/hypotheses")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_every_recorded_hypothesis(self, client):
        client.post(
            "/hypotheses",
            json=_valid_payload(statement="NVIDIA demand may keep accelerating."),
        )
        client.post(
            "/hypotheses",
            json=_valid_payload(statement="US rate cuts may arrive sooner than priced in."),
        )

        response = client.get("/hypotheses")

        assert response.status_code == 200
        statements = {h["statement"] for h in response.json()}
        assert statements == {
            "NVIDIA demand may keep accelerating.",
            "US rate cuts may arrive sooner than priced in.",
        }


class TestGetHypothesis:
    def test_returns_the_matching_hypothesis(self, client):
        created = client.post("/hypotheses", json=_valid_payload()).json()

        response = client.get(f"/hypotheses/{created['hypothesisId']}")

        assert response.status_code == 200
        assert response.json() == created

    def test_returns_404_for_unknown_hypothesis(self, client):
        response = client.get(f"/hypotheses/{uuid.uuid4()}")
        assert response.status_code == 404

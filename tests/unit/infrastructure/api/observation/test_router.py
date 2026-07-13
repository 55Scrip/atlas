"""API tests for the Observation Capture REST controller (API-003)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_observation_table(engine)
    repository = SqlAlchemyObservationRepository(engine)

    app = create_app()
    app.dependency_overrides[get_observation_repository] = lambda: repository
    return TestClient(app)


def _valid_payload(**overrides) -> dict:
    payload = {
        "subject": "Semiconductor sector",
        "statement": (
            "Several semiconductor companies raised capital expenditure "
            "guidance during the same reporting period."
        ),
        "source": "Quarterly earnings reports",
        "note": "Follow whether equipment suppliers report the same pattern.",
        "observedAt": "2026-07-13T10:30:00+02:00",
    }
    payload.update(overrides)
    return payload


class TestCreateObservation:
    def test_returns_201_with_the_recorded_observation(self, client):
        payload = _valid_payload()
        response = client.post("/observations", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["observationId"])
        assert body["subject"] == "Semiconductor sector"
        assert body["statement"] == payload["statement"]
        assert body["source"] == "Quarterly earnings reports"
        assert body["note"] == "Follow whether equipment suppliers report the same pattern."
        assert body["observedAt"] == "2026-07-13T10:30:00+02:00"
        assert "recordedAt" in body

    def test_optional_fields_may_be_omitted(self, client):
        payload = {
            "subject": "NVIDIA",
            "statement": "The company raised full-year guidance.",
            "observedAt": "2026-07-13T10:30:00+02:00",
        }
        response = client.post("/observations", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["source"] is None
        assert body["note"] is None

    def test_blank_optional_fields_normalize_to_none(self, client):
        response = client.post(
            "/observations", json=_valid_payload(source="   ", note="")
        )
        assert response.status_code == 201
        body = response.json()
        assert body["source"] is None
        assert body["note"] is None

    def test_persists_the_observation_so_it_can_be_read_back(self, client):
        created = client.post("/observations", json=_valid_payload()).json()
        fetched = client.get(f"/observations/{created['observationId']}")
        assert fetched.status_code == 200
        assert fetched.json()["observationId"] == created["observationId"]


class TestCreateObservationValidationFailures:
    def test_rejects_blank_subject(self, client):
        response = client.post("/observations", json=_valid_payload(subject="   "))
        assert response.status_code == 400

    def test_rejects_blank_statement(self, client):
        response = client.post("/observations", json=_valid_payload(statement=""))
        assert response.status_code == 400

    def test_rejects_missing_observed_at(self, client):
        payload = _valid_payload()
        del payload["observedAt"]
        response = client.post("/observations", json=payload)
        assert response.status_code == 422  # malformed request shape, FastAPI default

    def test_rejects_naive_observed_at(self, client):
        # No timezone offset at all is rejected by pydantic's datetime
        # parsing before it ever reaches the domain, so this is also 422
        # (shape), not 400 (domain rule) — the domain rule is exercised
        # directly in tests/unit/domain/observation/test_entity.py.
        response = client.post(
            "/observations", json=_valid_payload(observedAt="not-a-datetime")
        )
        assert response.status_code == 422


class TestListObservations:
    def test_returns_empty_list_when_nothing_recorded(self, client):
        response = client.get("/observations")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_every_recorded_observation(self, client):
        client.post("/observations", json=_valid_payload(subject="NVIDIA"))
        client.post("/observations", json=_valid_payload(subject="US interest rates"))

        response = client.get("/observations")

        assert response.status_code == 200
        subjects = {o["subject"] for o in response.json()}
        assert subjects == {"NVIDIA", "US interest rates"}


class TestGetObservation:
    def test_returns_the_matching_observation(self, client):
        created = client.post("/observations", json=_valid_payload()).json()

        response = client.get(f"/observations/{created['observationId']}")

        assert response.status_code == 200
        assert response.json() == created

    def test_returns_404_for_unknown_observation(self, client):
        response = client.get(f"/observations/{uuid.uuid4()}")
        assert response.status_code == 404

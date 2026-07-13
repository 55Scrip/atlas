"""API tests for the Evidence Capture REST controller (API-005)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_evidence_table(engine)
    repository = SqlAlchemyEvidenceRepository(engine)

    app = create_app()
    app.dependency_overrides[get_evidence_repository] = lambda: repository
    return TestClient(app)


def _valid_payload(**overrides) -> dict:
    payload = {
        "statement": (
            "Order intake increased by 24 percent and management raised "
            "full-year guidance for the second consecutive quarter."
        ),
        "direction": "SUPPORTS",
        "source": "Quarterly earnings report",
        "note": "The comparison benefits from a weak prior-year period.",
        "observedAt": "2026-07-13T09:15:00+02:00",
    }
    payload.update(overrides)
    return payload


class TestCreateEvidence:
    def test_returns_201_with_the_recorded_evidence(self, client):
        payload = _valid_payload()
        response = client.post("/evidence", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["evidenceId"])
        assert body["statement"] == payload["statement"]
        assert body["direction"] == "SUPPORTS"
        assert body["source"] == "Quarterly earnings report"
        assert body["note"] == "The comparison benefits from a weak prior-year period."
        assert body["observedAt"] == "2026-07-13T09:15:00+02:00"
        assert "recordedAt" in body

    def test_challenges_direction_is_accepted(self, client):
        response = client.post("/evidence", json=_valid_payload(direction="CHALLENGES"))
        assert response.status_code == 201
        assert response.json()["direction"] == "CHALLENGES"

    def test_invalid_direction_is_rejected(self, client):
        response = client.post("/evidence", json=_valid_payload(direction="PROVES"))
        assert response.status_code == 400

    def test_optional_fields_may_be_omitted(self, client):
        payload = {
            "statement": "Free cash flow declined despite higher reported earnings.",
            "direction": "CHALLENGES",
            "observedAt": "2026-07-13T09:15:00+02:00",
        }
        response = client.post("/evidence", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["source"] is None
        assert body["note"] is None

    def test_blank_source_normalizes_to_none(self, client):
        response = client.post("/evidence", json=_valid_payload(source="   "))
        assert response.status_code == 201
        assert response.json()["source"] is None

    def test_blank_note_normalizes_to_none(self, client):
        response = client.post("/evidence", json=_valid_payload(note=""))
        assert response.status_code == 201
        assert response.json()["note"] is None

    def test_accepts_snake_case_request_body_for_backward_compatibility(self, client):
        payload = {
            "statement": "Free cash flow declined despite higher reported earnings.",
            "direction": "CHALLENGES",
            "observed_at": "2026-07-13T09:15:00+02:00",
        }
        response = client.post("/evidence", json=payload)
        assert response.status_code == 201
        assert response.json()["statement"] == payload["statement"]

    def test_persists_the_evidence_so_it_can_be_read_back(self, client):
        created = client.post("/evidence", json=_valid_payload()).json()
        fetched = client.get(f"/evidence/{created['evidenceId']}")
        assert fetched.status_code == 200
        assert fetched.json()["evidenceId"] == created["evidenceId"]


class TestCreateEvidenceValidationFailures:
    def test_rejects_blank_statement(self, client):
        response = client.post("/evidence", json=_valid_payload(statement="   "))
        assert response.status_code == 400

    def test_rejects_empty_statement(self, client):
        response = client.post("/evidence", json=_valid_payload(statement=""))
        assert response.status_code == 400

    def test_rejects_missing_observed_at(self, client):
        payload = _valid_payload()
        del payload["observedAt"]
        response = client.post("/evidence", json=payload)
        assert response.status_code == 422  # malformed request shape, FastAPI default

    def test_rejects_malformed_observed_at(self, client):
        response = client.post("/evidence", json=_valid_payload(observedAt="not-a-datetime"))
        assert response.status_code == 422


class TestListEvidence:
    def test_returns_empty_list_when_nothing_recorded(self, client):
        response = client.get("/evidence")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_every_recorded_evidence(self, client):
        client.post(
            "/evidence",
            json=_valid_payload(statement="NVIDIA demand may keep accelerating."),
        )
        client.post(
            "/evidence",
            json=_valid_payload(
                direction="CHALLENGES",
                statement="Free cash flow declined despite higher reported earnings.",
            ),
        )

        response = client.get("/evidence")

        assert response.status_code == 200
        statements = {e["statement"] for e in response.json()}
        assert statements == {
            "NVIDIA demand may keep accelerating.",
            "Free cash flow declined despite higher reported earnings.",
        }


class TestGetEvidence:
    def test_returns_the_matching_evidence(self, client):
        created = client.post("/evidence", json=_valid_payload()).json()

        response = client.get(f"/evidence/{created['evidenceId']}")

        assert response.status_code == 200
        assert response.json() == created

    def test_returns_404_for_unknown_evidence(self, client):
        response = client.get(f"/evidence/{uuid.uuid4()}")
        assert response.status_code == 404

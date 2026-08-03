"""API tests for the Evidence Capture REST controller (API-005)."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement, Subject
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table


@pytest.fixture
def repositories():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_observation_table(engine)
    create_evidence_table(engine)
    return SqlAlchemyObservationRepository(engine), SqlAlchemyEvidenceRepository(engine)


@pytest.fixture
def client(repositories):
    observation_repository, evidence_repository = repositories
    app = create_app()
    app.dependency_overrides[get_observation_repository] = lambda: observation_repository
    app.dependency_overrides[get_evidence_repository] = lambda: evidence_repository
    return TestClient(app)


def _existing_observation_id(repositories) -> str:
    observation_repository, _ = repositories
    observation = Observation.capture(
        case_id=CaseId(),
        subject=Subject("Semiconductor sector"),
        statement=Statement("Revenue increased by 18 percent."),
        observed_at=datetime.fromisoformat("2026-07-13T09:15:00+02:00"),
    )
    observation_repository.add(observation)
    return str(observation.id)


def _valid_payload(observation_id: str, **overrides) -> dict:
    payload = {
        "observationId": observation_id,
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
    def test_returns_201_with_the_recorded_evidence(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        payload = _valid_payload(observation_id)
        response = client.post("/evidence", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["evidenceId"])
        assert body["observationId"] == observation_id
        assert body["statement"] == payload["statement"]
        assert body["direction"] == "SUPPORTS"
        assert body["source"] == "Quarterly earnings report"
        assert body["note"] == "The comparison benefits from a weak prior-year period."
        assert body["observedAt"] == "2026-07-13T09:15:00+02:00"
        assert "recordedAt" in body

    def test_challenges_direction_is_accepted(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        response = client.post(
            "/evidence", json=_valid_payload(observation_id, direction="CHALLENGES")
        )
        assert response.status_code == 201
        assert response.json()["direction"] == "CHALLENGES"

    def test_invalid_direction_is_rejected(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        response = client.post(
            "/evidence", json=_valid_payload(observation_id, direction="PROVES")
        )
        assert response.status_code == 400

    def test_rejects_a_nonexistent_observation(self, client):
        response = client.post("/evidence", json=_valid_payload(str(uuid.uuid4())))
        assert response.status_code == 404

    def test_optional_fields_may_be_omitted(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        payload = {
            "observationId": observation_id,
            "statement": "Free cash flow declined despite higher reported earnings.",
            "direction": "CHALLENGES",
            "observedAt": "2026-07-13T09:15:00+02:00",
        }
        response = client.post("/evidence", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["source"] is None
        assert body["note"] is None

    def test_blank_source_normalizes_to_none(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        response = client.post("/evidence", json=_valid_payload(observation_id, source="   "))
        assert response.status_code == 201
        assert response.json()["source"] is None

    def test_blank_note_normalizes_to_none(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        response = client.post("/evidence", json=_valid_payload(observation_id, note=""))
        assert response.status_code == 201
        assert response.json()["note"] is None

    def test_accepts_snake_case_request_body_for_backward_compatibility(
        self, client, repositories
    ):
        observation_id = _existing_observation_id(repositories)
        payload = {
            "observation_id": observation_id,
            "statement": "Free cash flow declined despite higher reported earnings.",
            "direction": "CHALLENGES",
            "observed_at": "2026-07-13T09:15:00+02:00",
        }
        response = client.post("/evidence", json=payload)
        assert response.status_code == 201
        assert response.json()["statement"] == payload["statement"]

    def test_persists_the_evidence_so_it_can_be_read_back(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        created = client.post("/evidence", json=_valid_payload(observation_id)).json()
        fetched = client.get(f"/evidence/{created['evidenceId']}")
        assert fetched.status_code == 200
        assert fetched.json()["evidenceId"] == created["evidenceId"]


class TestCreateEvidenceValidationFailures:
    def test_rejects_blank_statement(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        response = client.post("/evidence", json=_valid_payload(observation_id, statement="   "))
        assert response.status_code == 400

    def test_rejects_empty_statement(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        response = client.post("/evidence", json=_valid_payload(observation_id, statement=""))
        assert response.status_code == 400

    def test_rejects_missing_observed_at(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        payload = _valid_payload(observation_id)
        del payload["observedAt"]
        response = client.post("/evidence", json=payload)
        assert response.status_code == 422  # malformed request shape, FastAPI default

    def test_rejects_malformed_observed_at(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        response = client.post(
            "/evidence", json=_valid_payload(observation_id, observedAt="not-a-datetime")
        )
        assert response.status_code == 422

    def test_rejects_missing_observation_id(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        payload = _valid_payload(observation_id)
        del payload["observationId"]
        response = client.post("/evidence", json=payload)
        assert response.status_code == 422  # malformed request shape, FastAPI default


class TestListEvidence:
    def test_returns_empty_list_when_nothing_recorded(self, client):
        response = client.get("/evidence")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_every_recorded_evidence(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        client.post(
            "/evidence",
            json=_valid_payload(observation_id, statement="NVIDIA demand may keep accelerating."),
        )
        client.post(
            "/evidence",
            json=_valid_payload(
                observation_id,
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
    def test_returns_the_matching_evidence(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        created = client.post("/evidence", json=_valid_payload(observation_id)).json()

        response = client.get(f"/evidence/{created['evidenceId']}")

        assert response.status_code == 200
        assert response.json() == created

    def test_returns_404_for_unknown_evidence(self, client):
        response = client.get(f"/evidence/{uuid.uuid4()}")
        assert response.status_code == 404


class TestDeleteEvidence:
    def test_returns_204_and_removes_the_record(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        created = client.post("/evidence", json=_valid_payload(observation_id)).json()

        response = client.delete(f"/evidence/{created['evidenceId']}")

        assert response.status_code == 204
        assert client.get(f"/evidence/{created['evidenceId']}").status_code == 404

    def test_returns_404_for_unknown_evidence(self, client):
        response = client.delete(f"/evidence/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_deleted_evidence_no_longer_appears_in_list(self, client, repositories):
        observation_id = _existing_observation_id(repositories)
        created = client.post("/evidence", json=_valid_payload(observation_id)).json()

        client.delete(f"/evidence/{created['evidenceId']}")

        remaining_ids = [e["evidenceId"] for e in client.get("/evidence").json()]
        assert created["evidenceId"] not in remaining_ids

    def test_survives_a_second_client_reading_the_list_after_deletion(self, client, repositories):
        # Simulates "reload the page": a fresh GET after deletion, on the
        # same underlying repository, must not resurrect the record.
        observation_id = _existing_observation_id(repositories)
        created = client.post("/evidence", json=_valid_payload(observation_id)).json()
        client.delete(f"/evidence/{created['evidenceId']}")

        first_reload_ids = [e["evidenceId"] for e in client.get("/evidence").json()]
        second_reload_ids = [e["evidenceId"] for e in client.get("/evidence").json()]
        assert created["evidenceId"] not in first_reload_ids
        assert created["evidenceId"] not in second_reload_ids

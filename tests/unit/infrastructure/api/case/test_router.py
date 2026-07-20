"""API tests for the Case REST controller (DO-IMP-001)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
    SqlAlchemyCaseRepository,
)
from atlas.core.infrastructure.persistence.case.table import create_case_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_case_table(engine)
    repository = SqlAlchemyCaseRepository(engine)

    app = create_app()
    app.dependency_overrides[get_case_repository] = lambda: repository
    return TestClient(app)


class TestCreateCase:
    def test_returns_201_with_the_recorded_case(self, client):
        response = client.post("/cases", json={})

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["caseId"])
        assert "recordedAt" in body

    def test_accepts_a_request_with_no_body_at_all(self, client):
        # Case creation takes no semantic input at all (OE-002 §3.1).
        response = client.post("/cases")
        assert response.status_code == 201

    def test_response_contains_only_canonical_fields(self, client):
        response = client.post("/cases", json={})
        assert set(response.json().keys()) == {"caseId", "recordedAt"}

    def test_persists_the_case_so_it_can_be_read_back(self, client):
        created = client.post("/cases", json={}).json()
        fetched = client.get(f"/cases/{created['caseId']}")
        assert fetched.status_code == 200
        assert fetched.json()["caseId"] == created["caseId"]

    def test_each_request_creates_a_distinct_case(self, client):
        first = client.post("/cases", json={}).json()
        second = client.post("/cases", json={}).json()
        assert first["caseId"] != second["caseId"]


class TestGetCase:
    def test_returns_the_matching_case(self, client):
        created = client.post("/cases", json={}).json()

        response = client.get(f"/cases/{created['caseId']}")

        assert response.status_code == 200
        assert response.json() == created

    def test_returns_404_for_unknown_case(self, client):
        response = client.get(f"/cases/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_rejects_malformed_case_id(self, client):
        response = client.get("/cases/not-a-uuid")
        assert response.status_code == 422

"""API tests for the Decision Context REST controller (API-002)."""
from __future__ import annotations

import uuid

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
from atlas.core.infrastructure.api.decision_context.dependencies import (
    get_decision_context_repository,
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


@pytest.fixture
def repositories():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    create_decision_context_table(engine)
    return SqlAlchemyDecisionRepository(engine), SqlAlchemyDecisionContextRepository(engine)


@pytest.fixture
def client(repositories):
    decision_repository, context_repository = repositories
    app = create_app()
    app.dependency_overrides[get_decision_repository] = lambda: decision_repository
    app.dependency_overrides[get_decision_context_repository] = lambda: context_repository
    return TestClient(app)


def _existing_decision(repositories) -> Decision:
    decision_repository, _ = repositories
    decision = Decision.register(
        case_id=CaseId(),
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat, undervalued relative to peers"),
        confidence=Confidence(75),
    )
    decision_repository.add(decision)
    return decision


def _valid_payload(**overrides) -> dict:
    payload = {
        "situation": (
            "The portfolio already had significant AI exposure, several recently "
            "sold positions had continued rising, and a Federal Reserve "
            "announcement was expected the following day."
        ),
        "portfolioRelevance": "Applied Materials would complement existing holdings.",
        "capitalConsiderations": "Only part of the available capital should be deployed.",
        "alternativesConsidered": ["Buy Applied Materials", "Buy Arm"],
        "uncertainties": ["Short-term market reaction to the Fed announcement"],
        "capturedAt": "2026-06-17T00:54:00+02:00",
    }
    payload.update(overrides)
    return payload


class TestCreateDecisionContext:
    def test_returns_201_with_the_recorded_context(self, client, repositories):
        decision = _existing_decision(repositories)

        response = client.post(f"/decisions/{decision.id.value}/context", json=_valid_payload())

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["contextId"])
        assert body["decisionId"] == str(decision.id.value)
        assert body["situation"] == _valid_payload()["situation"]
        assert body["portfolioRelevance"] == "Applied Materials would complement existing holdings."
        assert body["alternativesConsidered"] == ["Buy Applied Materials", "Buy Arm"]
        assert body["uncertainties"] == ["Short-term market reaction to the Fed announcement"]
        assert body["capturedAt"] == "2026-06-17T00:54:00+02:00"
        assert "recordedAt" in body

    def test_optional_fields_may_be_omitted(self, client, repositories):
        decision = _existing_decision(repositories)
        payload = {
            "situation": "Wanted to preserve cash before the Fed announcement.",
            "capturedAt": "2026-06-17T00:54:00+02:00",
        }

        response = client.post(f"/decisions/{decision.id.value}/context", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["portfolioRelevance"] is None
        assert body["capitalConsiderations"] is None
        assert body["alternativesConsidered"] == []
        assert body["uncertainties"] == []

    def test_does_not_modify_the_referenced_decision(self, client, repositories):
        decision_repository, _ = repositories
        decision = _existing_decision(repositories)

        client.post(f"/decisions/{decision.id.value}/context", json=_valid_payload())

        assert decision_repository.get(decision.id) == decision


class TestCreateDecisionContextValidationFailures:
    def test_rejects_blank_situation(self, client, repositories):
        decision = _existing_decision(repositories)
        response = client.post(
            f"/decisions/{decision.id.value}/context", json=_valid_payload(situation="   ")
        )
        assert response.status_code == 400

    def test_rejects_an_empty_alternative(self, client, repositories):
        decision = _existing_decision(repositories)
        response = client.post(
            f"/decisions/{decision.id.value}/context",
            json=_valid_payload(alternativesConsidered=["Buy Arm", ""]),
        )
        assert response.status_code == 400

    def test_rejects_an_empty_uncertainty(self, client, repositories):
        decision = _existing_decision(repositories)
        response = client.post(
            f"/decisions/{decision.id.value}/context",
            json=_valid_payload(uncertainties=["   "]),
        )
        assert response.status_code == 400


class TestCreateDecisionContextUnknownDecision:
    def test_returns_404_when_decision_does_not_exist(self, client):
        response = client.post(
            f"/decisions/{uuid.uuid4()}/context", json=_valid_payload()
        )
        assert response.status_code == 404


class TestCreateDecisionContextDuplicate:
    def test_returns_409_when_context_already_exists(self, client, repositories):
        decision = _existing_decision(repositories)
        first = client.post(f"/decisions/{decision.id.value}/context", json=_valid_payload())
        assert first.status_code == 201

        second = client.post(f"/decisions/{decision.id.value}/context", json=_valid_payload())
        assert second.status_code == 409


class TestGetDecisionContext:
    def test_returns_the_captured_context(self, client, repositories):
        decision = _existing_decision(repositories)
        created = client.post(
            f"/decisions/{decision.id.value}/context", json=_valid_payload()
        ).json()

        response = client.get(f"/decisions/{decision.id.value}/context")

        assert response.status_code == 200
        assert response.json() == created

    def test_returns_404_when_decision_has_no_context_yet(self, client, repositories):
        decision = _existing_decision(repositories)
        response = client.get(f"/decisions/{decision.id.value}/context")
        assert response.status_code == 404

    def test_returns_404_when_decision_does_not_exist(self, client):
        response = client.get(f"/decisions/{uuid.uuid4()}/context")
        assert response.status_code == 404

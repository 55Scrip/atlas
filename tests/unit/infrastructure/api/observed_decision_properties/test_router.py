"""ATLAS Sprint 13 -- Observed Decision Properties v1: exercises `GET
/observed-decision-properties` end-to-end through the real app and the
real `/cases`/`/decisions` endpoints -- nothing mocked, following the
exact fixture/helper pattern already established in
`test_portfolio_status_v1_scenarios.py`.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def client() -> TestClient:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _record_decision(client: TestClient, *, subject: str, decision_type: str, confidence: int) -> dict:
    case_id = client.post("/cases").json()["caseId"]
    payload = {
        "caseId": case_id,
        "userId": "00000000-0000-0000-0000-000000000001",
        "decisionType": decision_type,
        "subject": subject,
        "reason": "Testing.",
        "confidence": confidence,
    }
    response = client.post("/decisions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestEmptyHistory:
    def test_zero_decisions_returns_200_with_empty_properties(self, client: TestClient) -> None:
        response = client.get("/observed-decision-properties")
        assert response.status_code == 200
        body = response.json()
        assert body["properties"] == []
        assert len(body["limitations"]) > 0

    def test_one_decision_returns_empty_properties_not_an_error(self, client: TestClient) -> None:
        _record_decision(client, subject="AMD", decision_type="BUY", confidence=70)
        response = client.get("/observed-decision-properties")
        assert response.status_code == 200
        assert response.json()["properties"] == []


class TestRealRecurrence:
    def test_two_matching_decisions_produce_traceable_properties(self, client: TestClient) -> None:
        d1 = _record_decision(client, subject="AMD", decision_type="BUY", confidence=70)
        d2 = _record_decision(client, subject="AMD", decision_type="BUY", confidence=70)
        response = client.get("/observed-decision-properties")
        assert response.status_code == 200
        body = response.json()
        types = {p["propertyType"] for p in body["properties"]}
        assert types == {"same_subject_and_type", "same_confidence"}
        for prop in body["properties"]:
            assert prop["observedCount"] == 2
            assert set(prop["supportingDecisionIds"]) == {d1["id"], d2["id"]}
            assert prop["outcomeAware"] is False
            assert prop["sampleSizeWarning"] is True

    def test_scope_field_present_and_correct(self, client: TestClient) -> None:
        _record_decision(client, subject="AMD", decision_type="BUY", confidence=70)
        _record_decision(client, subject="AMD", decision_type="BUY", confidence=80)
        _record_decision(client, subject="MSFT", decision_type="SELL", confidence=70)
        body = client.get("/observed-decision-properties").json()
        by_type = {p["propertyType"]: p for p in body["properties"]}
        assert by_type["same_subject_and_type"]["scope"] == "single_company"
        assert by_type["same_confidence"]["scope"] == "portfolio_wide"


class TestSignatureExclusion:
    def test_response_never_contains_signature_or_strategy_vocabulary(self, client: TestClient) -> None:
        for i in range(3):
            _record_decision(client, subject="AMD", decision_type="BUY", confidence=50)
        for i in range(2):
            _record_decision(client, subject="META", decision_type="BUY", confidence=50)
        response = client.get("/observed-decision-properties")
        raw_text = response.text.lower()
        for forbidden in ("signature", "strategy", "connectedpatterns"):
            assert forbidden not in raw_text, f"{forbidden!r} leaked into response body"


class TestDeterminism:
    def test_repeated_calls_return_identical_json(self, client: TestClient) -> None:
        _record_decision(client, subject="AMD", decision_type="BUY", confidence=70)
        _record_decision(client, subject="AMD", decision_type="BUY", confidence=70)
        first = client.get("/observed-decision-properties").json()
        second = client.get("/observed-decision-properties").json()
        assert first == second


class TestFailureHandling:
    def test_no_query_parameters_required_and_none_accepted_causes_error(self, client: TestClient) -> None:
        # A no-request-body, no-parameter GET: confirm the route ignores
        # (rather than errors on) an unexpected query string, matching
        # ordinary FastAPI behavior for undeclared params -- no crash.
        response = client.get("/observed-decision-properties?unexpected=1")
        assert response.status_code == 200

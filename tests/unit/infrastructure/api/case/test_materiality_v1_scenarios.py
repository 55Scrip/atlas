"""Materiality Engine -- the real HTTP surface (`/materiality/*`),
powered by `atlas.alpha.materiality.service.MaterialityService`.
Follows the exact fixture/helper pattern `test_explainability_v1_scenarios
.py` already established.
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
def client():
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


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]})
    assert response.status_code == 201, response.text
    return response.json()["holdings"][0]["caseId"]


class TestCaseAndTickerEndpoints:
    def test_assessment_for_a_fresh_holding_is_available_via_both_case_and_ticker(self, client):
        case_id = _import_holding(client, "AAPL")
        by_case = client.get(f"/materiality/case/{case_id}")
        by_ticker = client.get("/materiality/ticker/AAPL")
        assert by_case.status_code == 200
        assert by_ticker.status_code == 200
        assert by_case.json() == by_ticker.json()

    def test_returns_404_for_an_unknown_case_id(self, client):
        response = client.get("/materiality/case/00000000-0000-0000-0000-000000000099")
        assert response.status_code == 404

    def test_returns_404_for_a_ticker_with_no_case(self, client):
        response = client.get("/materiality/ticker/ZZZZZ")
        assert response.status_code == 404


class TestAssessmentShape:
    def test_a_fresh_holding_with_no_data_names_a_real_top_limiting_factor(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/materiality/case/{case_id}").json()
        assert set(body) == {
            "supportingEvidence", "contradictingEvidence", "limitingFactors",
            "topSupportingEvidence", "topContradictingEvidence", "topLimitingFactor", "topMissingEvidence",
        }
        assert body["topLimitingFactor"] is not None
        assert body["topLimitingFactor"]["materiality"] in {"critical", "high", "medium", "low", "background"}

    def test_every_bucket_is_ordered_most_material_first(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/materiality/case/{case_id}").json()
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "background": 4, "unknown": 5}
        for bucket in ("supportingEvidence", "contradictingEvidence", "limitingFactors"):
            ranks = [order[item["materiality"]] for item in body[bucket]]
            assert ranks == sorted(ranks)

    def test_top_missing_evidence_matches_the_dedicated_explainability_endpoint(self, client):
        case_id = _import_holding(client, "NVDA")
        materiality_body = client.get(f"/materiality/case/{case_id}").json()
        explainability_body = client.get(f"/explainability/case/{case_id}").json()
        assert materiality_body["topMissingEvidence"] == explainability_body["mostValuableMissingInformation"]

    def test_every_reason_is_a_closed_code_never_free_text(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/materiality/case/{case_id}").json()
        for bucket in ("supportingEvidence", "contradictingEvidence", "limitingFactors"):
            for item in body[bucket]:
                assert set(item["reason"]) == {"code"}

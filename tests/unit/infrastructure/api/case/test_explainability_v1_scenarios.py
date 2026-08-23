"""Explainability Engine -- the real HTTP surface (`/explainability/*`),
powered by `atlas.alpha.explainability.service.ExplainabilityService`.
Follows the exact fixture/helper pattern `test_stance_v1_scenarios.py`
already established.
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


def _import_holdings(client, tickers_and_weights: list[tuple[str, float]]) -> dict[str, str]:
    response = client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": ticker, "weightPercent": weight} for ticker, weight in tickers_and_weights]},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return {h["ticker"]: h["caseId"] for h in body["holdings"]}


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    return _import_holdings(client, [(ticker, weight_percent)])[ticker]


class TestCaseAndTickerEndpoints:
    def test_explanation_for_a_fresh_holding_is_available_via_both_case_and_ticker(self, client):
        case_id = _import_holding(client, "AAPL")
        by_case = client.get(f"/explainability/case/{case_id}")
        by_ticker = client.get("/explainability/ticker/AAPL")
        assert by_case.status_code == 200
        assert by_ticker.status_code == 200
        assert by_case.json() == by_ticker.json()

    def test_returns_404_for_an_unknown_case_id(self, client):
        response = client.get("/explainability/case/00000000-0000-0000-0000-000000000099")
        assert response.status_code == 404

    def test_returns_404_for_a_ticker_with_no_case(self, client):
        response = client.get("/explainability/ticker/ZZZZZ")
        assert response.status_code == 404


class TestExplanationShape:
    def test_a_fresh_holding_with_no_data_names_a_real_limiting_factor(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/explainability/case/{case_id}").json()
        assert set(body) == {
            "supportingEvidence", "contradictingEvidence", "limitingFactors",
            "missingEvidence", "confidenceDrivers", "mostValuableMissingInformation",
        }
        assert body["limitingFactors"]
        assert all("code" in r for r in body["limitingFactors"])

    def test_most_valuable_missing_information_names_a_real_dimension_with_real_reasoning(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/explainability/case/{case_id}").json()
        top = body["mostValuableMissingInformation"]
        assert top is not None
        assert top["dimension"]
        assert top["reasoning"]
        assert top in body["missingEvidence"]

    def test_every_reason_is_a_closed_code_never_free_text(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/explainability/case/{case_id}").json()
        for bucket in ("supportingEvidence", "contradictingEvidence", "limitingFactors", "confidenceDrivers"):
            for reason in body[bucket]:
                assert set(reason) <= {"code", "count", "total"}


class TestCompareIntegration:
    def test_compare_returns_a_real_evidence_breakdown(self, client):
        _import_holdings(client, [("NVDA", 50), ("AMD", 50)])
        body = client.get("/explainability/compare?tickerA=NVDA&tickerB=AMD").json()
        assert set(body) == {"favoringA", "favoringB", "shared", "missingForBoth"}

    def test_two_equally_uncertain_companies_share_the_same_missing_information(self, client):
        _import_holdings(client, [("NVDA", 50), ("AMD", 50)])
        body = client.get("/explainability/compare?tickerA=NVDA&tickerB=AMD").json()
        assert "growth" in body["missingForBoth"]

    def test_returns_404_when_either_ticker_has_no_case(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/explainability/compare?tickerA=NVDA&tickerB=ZZZZZ")
        assert response.status_code == 404

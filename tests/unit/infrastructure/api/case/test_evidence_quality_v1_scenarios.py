"""Evidence Quality Engine -- the real HTTP surface (`/evidence-quality/
*`), powered by `atlas.alpha.evidence_quality.service
.EvidenceQualityService`. Follows the exact fixture/helper pattern
`test_explainability_v1_scenarios.py` already established.
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
    def test_report_for_a_fresh_holding_is_available_via_both_case_and_ticker(self, client):
        case_id = _import_holding(client, "AAPL")
        by_case = client.get(f"/evidence-quality/case/{case_id}")
        by_ticker = client.get("/evidence-quality/ticker/AAPL")
        assert by_case.status_code == 200
        assert by_ticker.status_code == 200
        assert by_case.json() == by_ticker.json()

    def test_returns_404_for_an_unknown_case_id(self, client):
        response = client.get("/evidence-quality/case/00000000-0000-0000-0000-000000000099")
        assert response.status_code == 404

    def test_returns_404_for_a_ticker_with_no_case(self, client):
        response = client.get("/evidence-quality/ticker/ZZZZZ")
        assert response.status_code == 404


class TestReportShape:
    def test_a_fresh_holding_with_no_business_data_is_honestly_not_applicable(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/evidence-quality/case/{case_id}").json()
        assert set(body) == {
            "quality", "conflictStatus", "freshness", "dominance", "warnings", "facts", "conflicts", "unsupportedFindings",
        }
        assert body["quality"] == "not_applicable"
        assert body["conflictStatus"] == "not_applicable"
        assert "no_evidence" in body["warnings"]
        assert body["facts"] == []
        assert body["conflicts"] == []

    def test_every_field_is_a_closed_code_never_free_text(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/evidence-quality/case/{case_id}").json()
        for warning in body["warnings"]:
            assert warning.replace("_", "").isalpha()


class TestPortfolioAndDiscoverySurfaces:
    def test_holdings_endpoint_returns_one_entry_per_holding_with_a_report(self, client):
        _import_holdings(client, [("NVDA", 50), ("AMD", 50)])
        body = client.get("/evidence-quality/holdings").json()
        tickers = {row["ticker"] for row in body}
        assert tickers == {"NVDA", "AMD"}
        for row in body:
            assert set(row["report"]) == {
                "quality", "conflictStatus", "freshness", "dominance", "warnings", "facts", "conflicts", "unsupportedFindings",
            }

    def test_candidates_endpoint_matches_the_dedicated_ticker_endpoint(self, client):
        case_id = _import_holding(client, "NVDA")
        client.post("/alpha-watchlist", json={"ticker": "AMD"})
        candidates = client.get("/evidence-quality/candidates").json()
        amd_row = next((row for row in candidates if row["ticker"] == "AMD"), None)
        assert amd_row is not None
        direct = client.get("/evidence-quality/ticker/AMD").json()
        assert amd_row["report"] == direct

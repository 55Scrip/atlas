"""API tests for the Portfolio Cockpit REST controller (ATLAS-028).

`GET /alpha-portfolio/cockpit` -- schema shape, holding ordering, empty
state, unresolved-identity handling, and the "no analytical computation
happens in this layer, only serialization" boundary.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio.api.dependencies import get_case_generation_service
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


class _NoOpCaseGenerationService:
    """Test double: `ensure_cases` returns holdings unchanged, exactly
    the "no case_generation_service" fallback `AlphaPortfolioService`
    itself already accepts -- used only to exercise the unresolved-
    holding branch through the real HTTP surface, mirroring the
    `disable_case_generation` pattern already established for the
    discovery router's own tests (ATLAS-027)."""

    def ensure_cases(self, holdings, *, known_case_ids_by_ticker=None):
        return holdings


def _import(client, holdings: list[dict]) -> dict:
    response = client.post("/alpha-portfolio/import", json={"holdings": holdings})
    assert response.status_code == 201, response.text
    return response.json()


class TestBeforePortfolioEstablished:
    def test_returns_200_with_exists_false_and_empty_collections(self, client):
        response = client.get("/alpha-portfolio/cockpit")
        assert response.status_code == 200
        body = response.json()
        assert body["exists"] is False
        assert body["holdings"] == []
        assert body["unresolvedHoldings"] == []
        assert body["summary"] is None
        assert body["convictionDistribution"] == []
        assert body["valuationDistribution"] == []
        assert body["priorityReviewCount"] == 0


class TestAfterImport:
    def test_returns_200_with_a_fully_shaped_holding(self, client):
        _import(client, [{"ticker": "NVDA", "weightPercent": 100}])
        response = client.get("/alpha-portfolio/cockpit")
        assert response.status_code == 200
        body = response.json()
        assert body["exists"] is True
        assert len(body["holdings"]) == 1
        holding = body["holdings"][0]
        assert holding["ticker"] == "NVDA"
        assert holding["caseId"] is not None
        assert set(holding) == {
            "ticker",
            "caseId",
            "weightPercent",
            "valueAbsolute",
            "reconciliationStatus",
            "conviction",
            "analysisCoverage",  # Internal Alpha Fix Sprint 1 (IA-003): separate from conviction
            "valuation",
            "business",
            "riskProjection",
            "riskFindings",
            "confidence",
            "isThesisStale",
            "attention",
            "decisionSupport",  # Workspace Migration Phase 1: evidence-support presentation, see atlas.alpha.decision_support
        }
        assert set(holding["conviction"]) == {"level", "reasons"}
        assert set(holding["business"]) == {"growth", "capitalAllocation"}
        assert set(holding["riskProjection"]) == {"category", "status"}
        assert len(holding["riskFindings"]) == 4
        assert {f["category"] for f in holding["riskFindings"]} == {
            "business_risk",
            "financial_risk",
            "valuation_risk",
            "thesis_risk",
        }
        assert set(holding["attention"]) == {"priority", "reasons"}

    def test_holding_order_matches_import_order(self, client):
        _import(
            client,
            [
                {"ticker": "NVDA", "weightPercent": 40},
                {"ticker": "AMD", "weightPercent": 30},
                {"ticker": "META", "weightPercent": 30},
            ],
        )
        body = client.get("/alpha-portfolio/cockpit").json()
        assert [h["ticker"] for h in body["holdings"]] == ["NVDA", "AMD", "META"]

    def test_summary_and_distributions_are_present_and_consistent(self, client):
        _import(
            client,
            [{"ticker": "NVDA", "weightPercent": 60}, {"ticker": "AMD", "weightPercent": 40}],
        )
        body = client.get("/alpha-portfolio/cockpit").json()
        assert body["summary"]["holdingsCount"] == 2
        assert sum(c["count"] for c in body["convictionDistribution"]) == 2
        assert sum(c["count"] for c in body["valuationDistribution"]) == 2

    def test_no_duplicate_cases_created_by_reading_the_cockpit_twice(self, client):
        _import(client, [{"ticker": "NVDA", "weightPercent": 100}])
        first = client.get("/alpha-portfolio/cockpit").json()
        second = client.get("/alpha-portfolio/cockpit").json()
        assert first["holdings"][0]["caseId"] == second["holdings"][0]["caseId"]


class TestUnresolvedHoldings:
    def test_a_holding_with_no_case_id_is_named_in_unresolved_holdings(self, client):
        client.app.dependency_overrides[get_case_generation_service] = _NoOpCaseGenerationService
        _import(client, [{"ticker": "NVDA", "weightPercent": 100}])
        body = client.get("/alpha-portfolio/cockpit").json()
        assert body["holdings"] == []
        assert body["unresolvedHoldings"] == [{"ticker": "NVDA", "caseId": None}]


class TestAttentionOrdering:
    def test_a_large_holding_with_no_evidence_is_flagged_for_evidence_review(self, client):
        _import(client, [{"ticker": "NVDA", "weightPercent": 100}])
        body = client.get("/alpha-portfolio/cockpit").json()
        assert body["holdings"][0]["attention"]["priority"] == "evidence_review"
        assert body["holdings"][0]["attention"]["reasons"] == ["insufficient_evidence"]


class TestNoAnalyticalFieldsLeakFromTheFrontend:
    """This endpoint is read-only and takes no analytical input from the
    request -- there is no field on the GET request body/query that
    could inject a client-derived conviction, risk, or valuation value."""

    def test_get_cockpit_accepts_no_query_parameters_that_affect_analysis(self, client):
        _import(client, [{"ticker": "NVDA", "weightPercent": 100}])
        plain = client.get("/alpha-portfolio/cockpit").json()
        with_bogus_params = client.get(
            "/alpha-portfolio/cockpit", params={"conviction": "very_high", "riskScore": "0"}
        ).json()
        plain.pop("generatedAt")
        with_bogus_params.pop("generatedAt")
        assert plain == with_bogus_params

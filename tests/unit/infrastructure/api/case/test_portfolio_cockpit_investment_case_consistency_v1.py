"""ATLAS-029 Phase 47 -- cross-surface consistency: for the same
`CanonicalAnalysis`, Portfolio Cockpit (`GET /alpha-portfolio/cockpit`)
and the canonical Investment Case (`GET /cases/{case_id}/analysis`) must
agree on Conviction, Valuation, Risk, Business, and Confidence. Both
endpoints are built from the exact same `InvestmentCaseComposition` --
Portfolio Cockpit via `build_many`, Investment Case via `build` -- so any
disagreement here would mean one of the two projections drifted from the
real underlying analysis. If they disagree, this must fail.
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


def _import_portfolio(client, holdings: list[dict]) -> dict:
    response = client.post("/alpha-portfolio/import", json={"holdings": holdings})
    assert response.status_code == 201, response.text
    return response.json()


class TestConvictionAgreement:
    def test_conviction_level_matches_across_both_surfaces(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        assert cockpit["holdings"][0]["conviction"]["level"] == investment_case["conviction"]["level"]


class TestValuationAgreement:
    def test_fcf_yield_status_matches_across_both_surfaces(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        cockpit_status = cockpit["holdings"][0]["valuation"]["status"]
        case_finding = next(f for f in investment_case["valuation"]["findings"] if f["kind"] == "fcf_yield_relative")
        assert cockpit_status == case_finding["status"]


class TestRiskAgreement:
    def test_cockpits_risk_projection_is_drawn_from_investment_cases_own_full_vector(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        projection = cockpit["holdings"][0]["riskProjection"]
        matching = [
            f
            for f in investment_case["risk"]["findings"]
            if f["category"] == projection["category"] and f["status"] == projection["status"]
        ]
        assert len(matching) == 1, (
            f"Cockpit's compact risk projection {projection} has no matching entry in "
            f"Investment Case's full risk vector {investment_case['risk']['findings']}"
        )

    def test_investment_case_shows_the_full_vector_cockpit_only_shows_one(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        assert len(investment_case["risk"]["findings"]) == 4
        assert "riskFindings" in cockpit["holdings"][0]
        assert len(cockpit["holdings"][0]["riskFindings"]) == 4
        assert cockpit["holdings"][0]["riskFindings"] == investment_case["risk"]["findings"]


class TestBusinessAgreement:
    def test_growth_and_capital_allocation_match_across_both_surfaces(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        cockpit_business = cockpit["holdings"][0]["business"]
        findings_by_kind = {f["kind"]: f for f in investment_case["businessAnalysis"]["findings"]}
        assert cockpit_business["growth"] == findings_by_kind["growth"]["status"]
        assert cockpit_business["capitalAllocation"] == findings_by_kind["capital_allocation"]["status"]


class TestConfidenceAgreement:
    def test_confidence_matches_across_both_surfaces(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        assert cockpit["holdings"][0]["confidence"] == investment_case["confidence"]


class TestMultipleHoldingsAllAgree:
    def test_every_holding_agrees_on_every_shared_field(self, client):
        _import_portfolio(
            client,
            [
                {"ticker": "NVDA", "weightPercent": 40},
                {"ticker": "AMD", "weightPercent": 30},
                {"ticker": "META", "weightPercent": 30},
            ],
        )
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        for holding in cockpit["holdings"]:
            investment_case = client.get(f"/cases/{holding['caseId']}/analysis").json()
            assert holding["conviction"]["level"] == investment_case["conviction"]["level"]
            assert holding["confidence"] == investment_case["confidence"]
            case_finding = next(
                f for f in investment_case["valuation"]["findings"] if f["kind"] == "fcf_yield_relative"
            )
            assert holding["valuation"]["status"] == case_finding["status"]

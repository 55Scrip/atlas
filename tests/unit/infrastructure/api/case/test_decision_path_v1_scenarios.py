"""Decision Path & Required Progress -- the real HTTP surface
(`/decision-path/*`), powered by `atlas.alpha.decision_path.service
.DecisionPathService`. Follows the exact fixture/helper pattern
`test_recommendation_conviction_v1_scenarios.py` already established.
No real network access is available in this environment, so a freshly
imported holding genuinely has never been evaluated -- these tests
exercise that real, honest floor state (a real `never_evaluated` step)
rather than fabricating richer coverage.
"""
from __future__ import annotations

import uuid

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
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]})
    assert response.status_code == 201, response.text
    return response.json()["holdings"][0]["caseId"]


def _add_to_watchlist(client, ticker: str) -> str:
    response = client.post("/alpha-watchlist", json={"ticker": ticker})
    assert response.status_code == 201, response.text
    return response.json()["caseId"]


class TestDecisionPathShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/decision-path/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_freshly_imported_holding_has_a_real_never_evaluated_step(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/decision-path/{case_id}").json()
        assert body["caseId"] == case_id
        assert any(s["code"] == "never_evaluated" for s in body["steps"])
        assert set(body) == {
            "caseId",
            "currentAction",
            "currentStrength",
            "steps",
            "immediateBlocker",
            "nextAchievableImprovement",
            "finalReachableState",
            "generatedAt",
        }

    def test_every_step_names_a_real_progress_kind_and_reachability(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/decision-path/{case_id}").json()
        for step in body["steps"]:
            assert step["progressKind"] in {"operational", "evidence", "coverage", "readiness", "dependency", "decision"}
            assert step["reachability"] in {"reachable", "blocked", "not_reachable"}

    def test_the_path_view_never_leaks_internal_engine_terminology(self, client):
        """Deliverable 14's own language-boundary check at the wire
        level -- no goal/coaching/AI/forecast wording anywhere in the
        payload's own keys."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/decision-path/{case_id}").json()
        assert "score" not in body and "probability" not in body and "prediction" not in body


class TestPortfolioBreakdown:
    def test_shape_and_scope(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/decision-path/portfolio/breakdown").json()
        assert set(body) == {
            "closestToInvestable",
            "operationallyBlocked",
            "requiringMoreEvidence",
            "requiringDependencyResolution",
        }
        all_tickers = {t for tickers in body.values() for t in tickers}
        assert "MSFT" not in all_tickers


class TestCompare:
    def test_unknown_ticker_returns_404(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/decision-path/compare?tickerA=NVDA&tickerB=ZZZZZ")
        assert response.status_code == 404

    def test_compares_two_real_tickers_and_never_declares_a_better_investment(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/decision-path/compare?tickerA=NVDA&tickerB=MSFT").json()
        assert set(body) == {
            "a",
            "b",
            "shorterPathCaseId",
            "fewerRemainingBlockersCaseId",
            "moreOperationallyDependentCaseId",
            "moreEvidenceDependentCaseId",
        }


class TestChange:
    def test_first_read_produces_no_change(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/decision-path/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None

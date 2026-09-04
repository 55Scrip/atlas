"""Investment Decision Synthesis -- the real HTTP surface
(`/investment-decision/*`), powered by `atlas.alpha.investment_decision
.service.InvestmentDecisionService`. Follows the exact fixture/helper
pattern `test_decision_readiness_v1_scenarios.py` already established.
No real network access is available in this environment, so a freshly
imported holding genuinely has `NO_COVERAGE` -- these tests exercise
that real, honest floor state (`no_decision`) rather than fabricating
richer coverage.
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


class TestInvestmentDecisionShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/investment-decision/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_freshly_imported_holding_with_no_ingested_data_is_no_decision(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/investment-decision/{case_id}").json()
        assert body["caseId"] == case_id
        assert body["action"] == "no_decision"
        # `reasoning` is the canonical analytical rationale, added
        # additively so the persisted payload can reach the benchmark
        # without being reconstructed from process-state fields. It is
        # `None` here: a freshly imported holding with no ingested data
        # produces no directional recommendation, so there is no
        # rationale to project -- which is distinct from a legacy row,
        # where the key would be absent from storage entirely.
        assert set(body) == {"caseId", "action", "qualifiers", "supportingReasons",
                             "blockers", "changeTrigger", "generatedAt", "reasoning"}
        assert body["reasoning"] is None

    def test_the_decision_view_never_leaks_internal_engine_terminology(self, client):
        """Deliverable 12's own language-boundary check at the wire
        level."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/investment-decision/{case_id}").json()
        assert "score" not in body and "probability" not in body and "confidence" not in body


class TestPortfolioDistribution:
    def test_shape_and_scope(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/investment-decision/portfolio/distribution").json()
        assert set(body) == {"buy", "add", "hold", "reduce", "exit", "wait", "noDecision"}
        assert "NVDA" in body["noDecision"]
        all_tickers = {t for tickers in body.values() for t in tickers}
        assert "MSFT" not in all_tickers


class TestCompare:
    def test_unknown_ticker_returns_404(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/investment-decision/compare?tickerA=NVDA&tickerB=ZZZZZ")
        assert response.status_code == 404

    def test_compares_two_real_tickers(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/investment-decision/compare?tickerA=NVDA&tickerB=MSFT").json()
        assert body["a"]["action"] == "no_decision"
        assert body["b"]["action"] == "no_decision"
        assert set(body) == {"a", "b", "differingQualifierKinds", "sharedBlockerCodes", "sharedSupportingReasonCodes"}


class TestChange:
    def test_first_read_produces_no_change(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/investment-decision/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None

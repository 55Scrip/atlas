"""Investment Case Decision Layer Bundle (`/cases/{case_id}/decision-
layer-bundle`) -- Opportunity Cost Cross-Case Computation Review,
follow-up implementation sprint. Follows the exact fixture/helper
pattern `test_decision_explanation_v1_scenarios.py` already
established.

Verifies:
1. each field of the bundle is semantically identical to what the
   corresponding, unmodified separate endpoint returns,
2. the expensive cross-case scan inside `OpportunityCostService
   ._other_case_summaries` runs exactly once per bundle request, not
   once per section,
3. the five existing separate endpoints still work unchanged,
4. a genuine failure in one section does not take the other three
   down with it -- the bundle always returns 200, never a bundle-wide
   500.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.opportunity_cost.service import OpportunityCostService
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


def _import_holdings(client, weights_by_ticker: dict[str, float]) -> dict[str, str]:
    response = client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": ticker, "weightPercent": weight} for ticker, weight in weights_by_ticker.items()]},
    )
    assert response.status_code == 201, response.text
    return {h["ticker"]: h["caseId"] for h in response.json()["holdings"]}


class TestSemanticIdentity:
    """The bundle's own five fields must be byte-identical to what the
    unmodified separate endpoints already return for the same case."""

    def test_opportunity_cost_matches_the_separate_endpoint(self, client):
        """`generatedAt` is excluded from the comparison: the bundle
        call and this follow-up call are two genuinely separate HTTP
        requests, each with its own `_utc_now()` -- the same reason two
        independent calls to any "always computed live" Decision Layer
        endpoint have always differed by a fraction of a second, not a
        bug this sprint introduces."""
        case_id = _import_holding(client, "NVDA")
        bundle = client.get(f"/cases/{case_id}/decision-layer-bundle").json()
        separate = client.get(f"/opportunity-cost/{case_id}").json()
        assert {k: v for k, v in bundle["opportunityCost"].items() if k != "generatedAt"} == {
            k: v for k, v in separate.items() if k != "generatedAt"
        }

    def test_opportunity_cost_change_matches_the_separate_endpoint(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/cases/{case_id}/decision-layer-bundle")  # first computation, establishes a baseline
        bundle = client.get(f"/cases/{case_id}/decision-layer-bundle").json()
        separate = client.get(f"/opportunity-cost/{case_id}/change").json()
        assert bundle["opportunityCostChange"] == separate

    def test_decision_memory_matches_the_separate_endpoint(self, client):
        case_id = _import_holding(client, "NVDA")
        bundle = client.get(f"/cases/{case_id}/decision-layer-bundle").json()
        separate = client.get(f"/decision-memory/{case_id}").json()
        assert bundle["decisionMemory"] == separate

    def test_decision_explanation_matches_the_separate_endpoint(self, client):
        case_id = _import_holding(client, "NVDA")
        bundle = client.get(f"/cases/{case_id}/decision-layer-bundle").json()
        separate = client.get(f"/decision-explanation/{case_id}").json()
        assert {k: v for k, v in bundle["decisionExplanation"].items() if k != "generatedAt"} == {
            k: v for k, v in separate.items() if k != "generatedAt"
        }

    def test_portfolio_decision_matches_the_separate_endpoint(self, client):
        case_id = _import_holding(client, "NVDA")
        bundle = client.get(f"/cases/{case_id}/decision-layer-bundle").json()
        separate = client.get(f"/portfolio-decision/{case_id}").json()
        assert {k: v for k, v in bundle["portfolioDecision"].items() if k != "generatedAt"} == {
            k: v for k, v in separate.items() if k != "generatedAt"
        }

    def test_unknown_case_returns_200_with_every_field_null(self, client):
        response = client.get(f"/cases/{uuid.uuid4()}/decision-layer-bundle")
        assert response.status_code == 200
        body = response.json()
        assert body == {
            "opportunityCost": None,
            "opportunityCostChange": None,
            "decisionMemory": None,
            "decisionExplanation": None,
            "portfolioDecision": None,
        }


class TestSingleCrossCaseScan:
    """The expensive part -- `_other_case_summaries`, which evaluates
    every other known Case -- must run exactly once per bundle
    request, regardless of how many of the four sections internally
    reach `opportunity_cost_service.assess_for_case` for the same
    `case_id` (the bundle itself, decision_memory, decision_explanation
    via decision_memory, and portfolio_decision all do)."""

    def test_other_case_summaries_runs_once_with_a_multi_case_portfolio(self, client, monkeypatch):
        case_ids = _import_holdings(client, {"NVDA": 25.0, "AAPL": 25.0, "MSFT": 25.0, "GOOGL": 25.0})
        target_case_id = case_ids["NVDA"]

        calls = {"n": 0}
        original = OpportunityCostService._other_case_summaries

        def counting(self, exclude_case_id):
            calls["n"] += 1
            return original(self, exclude_case_id)

        monkeypatch.setattr(OpportunityCostService, "_other_case_summaries", counting)

        response = client.get(f"/cases/{target_case_id}/decision-layer-bundle")
        assert response.status_code == 200

        assert calls["n"] == 1

    def test_a_second_bundle_request_recomputes_independently(self, client, monkeypatch):
        """Confirms this is genuinely request-scoped, not an
        accidental global cache: a second, separate HTTP request must
        trigger its own fresh scan, not reuse the first request's."""
        case_ids = _import_holdings(client, {"NVDA": 50.0, "AAPL": 50.0})
        target_case_id = case_ids["NVDA"]

        calls = {"n": 0}
        original = OpportunityCostService._other_case_summaries

        def counting(self, exclude_case_id):
            calls["n"] += 1
            return original(self, exclude_case_id)

        monkeypatch.setattr(OpportunityCostService, "_other_case_summaries", counting)

        client.get(f"/cases/{target_case_id}/decision-layer-bundle")
        client.get(f"/cases/{target_case_id}/decision-layer-bundle")

        assert calls["n"] == 2


class TestExistingEndpointsUnaffected:
    """The five separate endpoints this bundle composes must continue
    to work completely unchanged."""

    def test_opportunity_cost_endpoint_still_works(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/opportunity-cost/{case_id}")
        assert response.status_code == 200

    def test_opportunity_cost_change_endpoint_still_works(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/opportunity-cost/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None  # first computation, no baseline yet

    def test_decision_memory_endpoint_still_works(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/decision-memory/{case_id}")
        assert response.status_code == 200

    def test_decision_explanation_endpoint_still_works(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/decision-explanation/{case_id}")
        assert response.status_code == 200

    def test_portfolio_decision_endpoint_still_works(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/portfolio-decision/{case_id}")
        assert response.status_code == 200

    def test_unknown_case_still_returns_404_on_the_separate_endpoint(self, client):
        response = client.get(f"/opportunity-cost/{uuid.uuid4()}")
        assert response.status_code == 404


class TestFailureIsolation:
    """A genuine, unexpected exception in one section must not take
    the other three down with it -- the bundle always returns 200,
    exactly matching how the four separate endpoints already fail
    independently of each other today."""

    def test_a_broken_section_degrades_to_null_without_failing_the_others(self, client, monkeypatch):
        case_id = _import_holding(client, "NVDA")

        def broken(self, case_id, *, ticker=None):
            raise RuntimeError("simulated failure")

        from atlas.alpha.portfolio_decision.service import PortfolioDecisionService

        monkeypatch.setattr(PortfolioDecisionService, "assess_for_case", broken)

        response = client.get(f"/cases/{case_id}/decision-layer-bundle")
        assert response.status_code == 200
        body = response.json()
        assert body["portfolioDecision"] is None
        assert body["opportunityCost"] is not None
        assert body["decisionMemory"] is not None
        assert body["decisionExplanation"] is not None

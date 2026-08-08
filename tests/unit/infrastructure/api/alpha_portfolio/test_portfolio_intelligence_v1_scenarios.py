"""ATLAS-016 — Portfolio Intelligence: consumes the canonical Decision
Engine pipeline plus `PortfolioStatusService` (ATLAS-015) to derive Key
Findings/Consider/Risk Signals/Missing Evidence.

Exercises `GET /alpha-portfolio/intelligence` end-to-end through the
real Case/Decision/Outcome/Observation/Evidence/Alpha-portfolio APIs --
nothing mocked, following the exact fixture/helper pattern already
established in `test_portfolio_status_v1_scenarios.py`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

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


def _open_case(client) -> str:
    return client.post("/cases").json()["caseId"]


def _holding_case_id(client, ticker: str) -> str:
    """ATLAS-027: portfolio import now auto-generates and links a Case
    for every recognized holding, so tests that need "the Case already
    linked to this holding" read it back from the holdings list rather
    than manually opening and linking one (that manual step is now a
    no-op: `link_case_to_holding` is idempotent and the holding already
    has a real, auto-created `case_id` by the time any test runs)."""
    view = client.get("/alpha-portfolio").json()
    holding = next(h for h in view["holdings"] if h["ticker"] == ticker)
    assert holding["caseId"] is not None
    return holding["caseId"]


def _record_decision(client, *, case_id: str, subject: str, decision_type: str = "BUY", **overrides) -> dict:
    payload = {
        "caseId": case_id,
        "userId": "00000000-0000-0000-0000-000000000001",
        "decisionType": decision_type,
        "subject": subject,
        "reason": "Testing.",
        "confidence": 70,
    }
    payload.update(overrides)
    response = client.post("/decisions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _record_outcome(client, decision: dict, **overrides) -> dict:
    payload = {
        "decisionId": decision["id"],
        "statement": "Something happened.",
        "occurredAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/outcomes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _record_observation(client, *, case_id: str, subject: str, **overrides) -> dict:
    payload = {
        "caseId": case_id,
        "subject": subject,
        "statement": "Noted something.",
        "observedAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/observations", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _record_evidence(client, *, observation_id: str, direction: str = "SUPPORTS", **overrides) -> dict:
    payload = {
        "observationId": observation_id,
        "statement": "Corroborating detail.",
        "direction": direction,
        "observedAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/evidence", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestEmptyAndUnestablishedPortfolio:
    def test_returns_exists_false_before_a_portfolio_is_established(self, client):
        response = client.get("/alpha-portfolio/intelligence")
        assert response.status_code == 200
        body = response.json()
        assert body["exists"] is False
        assert body["overview"] is None
        assert body["keyFindings"] == []
        assert body["considerItems"] == []
        assert body["riskSignals"] == []
        assert body["missingEvidence"] == []
        assert body["portfolioFit"] == {"available": False, "reason": "not_yet_implemented"}


class TestOverviewReusesPortfolioStatus:
    def test_overview_matches_portfolio_status_summary(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        status_summary = client.get("/alpha-portfolio/status").json()["summary"]
        intelligence_overview = client.get("/alpha-portfolio/intelligence").json()["overview"]
        assert intelligence_overview == status_summary


class TestMissingCase:
    """ATLAS-027: importing a recognized holding now auto-generates and
    links a canonical Case, so the `MISSING_CASE`/`open_investment_case`
    signal this class used to prove is no longer reachable through a
    normal import -- proving that obsolescence directly (Phase 26) is
    this class's job now. The underlying detection mechanism itself
    (`holding.case_id is None`) is unchanged and still real; it fires
    only when Case generation genuinely could not run -- proven at the
    service level in `tests/unit/alpha/portfolio/test_case_generation_wiring.py`.
    """

    def test_import_no_longer_produces_missing_case_or_open_investment_case(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 20}]},
        )
        body = client.get("/alpha-portfolio/intelligence").json()

        considers = [c for c in body["considerItems"] if c["ticker"] == "AMD"]
        assert not any(c["kind"] == "open_investment_case" for c in considers)

        risks = [r for r in body["riskSignals"] if r["ticker"] == "AMD"]
        assert not any(r["kind"] == "missing_case" for r in risks)

        findings = {f["kind"]: f for f in body["keyFindings"]}
        assert "multiple_missing_cases" not in findings

    def test_import_links_a_real_case_id_to_the_holding(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 20}]},
        )
        assert _holding_case_id(client, "AMD") is not None


class TestEvidenceGaps:
    def test_case_with_zero_evidence_surfaces_missing_evidence_and_gather_evidence(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 20}]},
        )
        case_id = _holding_case_id(client, "AMD")
        _record_decision(client, case_id=case_id, subject="AMD")

        body = client.get("/alpha-portfolio/intelligence").json()

        gaps = [m for m in body["missingEvidence"] if m["ticker"] == "AMD"]
        assert any(g["gapKind"] == "no_evidence_recorded" for g in gaps)

        considers = [c for c in body["considerItems"] if c["ticker"] == "AMD"]
        assert any(c["kind"] == "gather_evidence" for c in considers)

        risks = [r for r in body["riskSignals"] if r["ticker"] == "AMD"]
        assert any(r["kind"] == "missing_evidence" for r in risks)

    def test_fully_evidenced_observation_does_not_surface_evidence_gap_for_it(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 20}]},
        )
        case_id = _holding_case_id(client, "AMD")
        observation = _record_observation(client, case_id=case_id, subject="AMD")
        _record_evidence(client, observation_id=observation["observationId"])

        body = client.get("/alpha-portfolio/intelligence").json()

        gaps = [m for m in body["missingEvidence"] if m["ticker"] == "AMD"]
        assert gaps == []
        considers = [c for c in body["considerItems"] if c["ticker"] == "AMD" and c["kind"] == "gather_evidence"]
        assert considers == []


class TestStaleReview:
    def test_very_old_case_produces_review_thesis_consider_and_stale_risk_signal(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 20}]},
        )
        case_id = _holding_case_id(client, "AMD")
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        decision = _record_decision(client, case_id=case_id, subject="AMD", decidedAt=old_timestamp)
        _record_outcome(client, decision)

        body = client.get("/alpha-portfolio/intelligence").json()

        considers = [c for c in body["considerItems"] if c["ticker"] == "AMD"]
        review_thesis = [c for c in considers if c["kind"] == "review_thesis"]
        assert len(review_thesis) == 1
        assert review_thesis[0]["ageDays"] >= 200

        risks = [r for r in body["riskSignals"] if r["ticker"] == "AMD"]
        stale = [r for r in risks if r["kind"] == "stale_review"]
        assert len(stale) == 1
        assert stale[0]["ageDays"] >= 200

        findings = {f["kind"]: f for f in body["keyFindings"]}
        assert "multiple_stale_cases" in findings


class TestPendingWorkflowUpdateCase:
    def test_decision_without_outcome_produces_a_single_update_case_consider(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 20}]},
        )
        case_id = _holding_case_id(client, "AMD")
        _record_decision(client, case_id=case_id, subject="AMD")

        body = client.get("/alpha-portfolio/intelligence").json()
        update_case = [c for c in body["considerItems"] if c["ticker"] == "AMD" and c["kind"] == "update_case"]
        assert len(update_case) == 1
        assert update_case[0]["pendingItemCount"] == 1
        assert update_case[0]["caseId"] == case_id


class TestConcentration:
    def test_elevated_weight_produces_review_concentration_but_not_high_risk(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 28},
                    {"ticker": "NVDA", "weightPercent": 10},
                ]
            },
        )
        body = client.get("/alpha-portfolio/intelligence").json()
        considers = [c for c in body["considerItems"] if c["ticker"] == "AMD"]
        assert any(c["kind"] == "review_concentration" for c in considers)
        risks = [r for r in body["riskSignals"] if r["ticker"] == "AMD"]
        assert not any(r["kind"] == "high_concentration" for r in risks)

    def test_high_weight_produces_high_concentration_risk_signal(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 40},
                    {"ticker": "NVDA", "weightPercent": 10},
                ]
            },
        )
        body = client.get("/alpha-portfolio/intelligence").json()
        risks = [r for r in body["riskSignals"] if r["ticker"] == "AMD"]
        assert any(r["kind"] == "high_concentration" for r in risks)
        findings = {f["kind"] for f in body["keyFindings"]}
        assert "high_concentration" in findings

    def test_low_weight_produces_no_concentration_signal(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 10}]},
        )
        body = client.get("/alpha-portfolio/intelligence").json()
        considers = [c for c in body["considerItems"] if c["ticker"] == "AMD" and c["kind"] == "review_concentration"]
        assert considers == []


class TestPortfolioFitPlaceholder:
    def test_portfolio_fit_is_always_unavailable_this_sprint(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        body = client.get("/alpha-portfolio/intelligence").json()
        assert body["portfolioFit"] == {"available": False, "reason": "not_yet_implemented"}


class TestRegressionOtherEndpointsUnaffected:
    def test_portfolio_and_status_endpoints_unaffected(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        portfolio = client.get("/alpha-portfolio")
        assert portfolio.status_code == 200
        assert portfolio.json()["holdings"][0]["ticker"] == "AMD"

        status = client.get("/alpha-portfolio/status")
        assert status.status_code == 200
        assert status.json()["exists"] is True

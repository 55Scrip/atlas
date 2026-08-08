"""ATLAS-017 -- Case Intelligence: consumes the canonical Decision
Engine pipeline for a single Case, plus `PortfolioStatusService`
(ATLAS-015), to derive Current Thesis/Evidence/Key Risks/Portfolio
Context/Consider for that Case.

Exercises `GET /cases/{case_id}/intelligence` end-to-end through the
real Case/Decision/Outcome/Observation/Evidence/Alpha-portfolio APIs --
nothing mocked, following the exact fixture/helper pattern already
established in `test_portfolio_intelligence_v1_scenarios.py`.
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


def _link_holding(client, ticker: str, weight_percent: float = 20.0) -> str:
    """ATLAS-027: importing `ticker` now auto-generates and links a real
    Case immediately -- there is no separate "open a case, then link
    it" step left to perform. Returns that auto-created `case_id` so
    the caller records everything against the Case actually linked to
    the holding, not an orphan."""
    client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]})
    view = client.get("/alpha-portfolio").json()
    holding = next(h for h in view["holdings"] if h["ticker"] == ticker)
    assert holding["caseId"] is not None
    return holding["caseId"]


class TestNotFound:
    def test_returns_404_for_a_nonexistent_case(self, client):
        response = client.get("/cases/00000000-0000-0000-0000-000000000099/intelligence")
        assert response.status_code == 404


class TestUnheldCase:
    def test_brand_new_case_returns_an_honest_report_with_no_holding(self, client):
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/intelligence").json()

        assert body["currentView"] == {
            "ticker": None,
            "held": False,
            "weightPercent": None,
            "valueAbsolute": None,
            "reconciliationStatus": None,
        }
        assert body["portfolioContext"]["held"] is False
        assert body["portfolioContext"]["facts"] == []
        assert body["considerItems"] == []
        assert body["conviction"] == {"available": False, "reason": "no_atlas_computed_conviction_exists"}
        assert body["portfolioFit"] == {"available": False, "reason": "not_yet_implemented"}
        assert body["confidence"] == "not_applicable"
        assert body["evidenceQuality"]["coverage"] == "not_applicable"
        assert any(gap["kind"] == "no_evidence_recorded" for gap in body["missingEvidence"])


class TestCurrentThesis:
    def test_reflects_the_investors_own_words_verbatim(self, client):
        case_id = _link_holding(client, "AMD")
        observation = _record_observation(client, case_id=case_id, subject="AMD", statement="Margins expanding.")
        _record_decision(
            client, case_id=case_id, subject="AMD", reason="Durable moat and cheap valuation.",
            observationId=observation["observationId"],
        )

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert body["currentThesis"]["latestDecisionReason"] == "Durable moat and cheap valuation."
        assert body["currentThesis"]["latestDecisionType"] == "BUY"
        assert body["currentThesis"]["latestObservationStatement"] == "Margins expanding."


class TestEvidenceQualityAndConfidence:
    def test_confidence_reuses_evidence_coverage_verbatim(self, client):
        case_id = _link_holding(client, "AMD")
        observation = _record_observation(client, case_id=case_id, subject="AMD")
        _record_evidence(client, observation_id=observation["observationId"])

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert body["confidence"] == "full"
        assert body["evidenceQuality"]["coverage"] == "full"
        assert body["missingEvidence"] == []

    def test_challenging_evidence_appears_as_contradicting_evidence_and_key_risk(self, client):
        case_id = _link_holding(client, "AMD")
        observation = _record_observation(client, case_id=case_id, subject="AMD")
        _record_evidence(client, observation_id=observation["observationId"], direction="CHALLENGES")

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert len(body["contradictingEvidence"]["observationClassifications"]) == 1
        assert body["contradictingEvidence"]["observationClassifications"][0]["challengingEvidenceCount"] == 1
        assert any(risk["kind"] == "contradicting_evidence" for risk in body["keyRisks"])


class TestOpenQuestions:
    def test_decision_without_linked_observation_surfaces_as_open_question(self, client):
        case_id = _link_holding(client, "AMD")
        _record_decision(client, case_id=case_id, subject="AMD")

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert any(
            q["kind"] == "decision_without_linked_observation" for q in body["openQuestions"]
        )


class TestReviewStatusAndConsiderThesis:
    def test_very_old_case_is_stale_and_produces_review_thesis_consider(self, client):
        case_id = _link_holding(client, "AMD")
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        decision = _record_decision(client, case_id=case_id, subject="AMD", decidedAt=old_timestamp)
        _record_outcome(client, decision)

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert body["reviewStatus"]["isStale"] is True
        assert body["reviewStatus"]["ageDays"] >= 200
        assert any(c["kind"] == "review_thesis" for c in body["considerItems"])


class TestDecisionHistory:
    def test_decision_joined_with_its_latest_outcome(self, client):
        case_id = _link_holding(client, "AMD")
        decision = _record_decision(client, case_id=case_id, subject="AMD", reason="Initial thesis.", confidence=80)
        outcome = _record_outcome(client, decision, statement="Confirmed thesis.")

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert len(body["decisionHistory"]) == 1
        entry = body["decisionHistory"][0]
        assert entry["reason"] == "Initial thesis."
        assert entry["investorConfidence"] == 80
        assert entry["outcomeId"] == outcome["id"]
        assert entry["outcomeStatement"] == "Confirmed thesis."


class TestObservationTimeline:
    def test_observation_carries_its_evidence_count_and_epistemic_status(self, client):
        case_id = _link_holding(client, "AMD")
        observation = _record_observation(client, case_id=case_id, subject="AMD", statement="Noted growth.")
        _record_evidence(client, observation_id=observation["observationId"])

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert len(body["observationTimeline"]) == 1
        entry = body["observationTimeline"][0]
        assert entry["statement"] == "Noted growth."
        assert entry["evidenceCount"] == 1
        assert entry["epistemicStatus"] == "supported"


class TestPendingWorkflowAndUpdateCase:
    def test_decision_without_outcome_produces_update_case_consider(self, client):
        case_id = _link_holding(client, "AMD")
        _record_decision(client, case_id=case_id, subject="AMD")

        body = client.get(f"/cases/{case_id}/intelligence").json()
        update_case = [c for c in body["considerItems"] if c["kind"] == "update_case"]
        assert len(update_case) == 1
        assert update_case[0]["pendingItemCount"] == 1
        assert "pending_workflow" in body["portfolioContext"]["facts"]


class TestConcentration:
    def test_high_weight_produces_high_concentration_key_risk_and_consider(self, client):
        case_id = _link_holding(client, "AMD", weight_percent=40.0)

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert any(r["kind"] == "high_concentration" for r in body["keyRisks"])
        assert any(c["kind"] == "review_concentration" for c in body["considerItems"])
        assert "high_concentration" in body["portfolioContext"]["facts"]

    def test_low_weight_produces_no_concentration_signal(self, client):
        case_id = _link_holding(client, "AMD", weight_percent=10.0)

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert not any(r["kind"] == "high_concentration" for r in body["keyRisks"])
        assert not any(c["kind"] == "review_concentration" for c in body["considerItems"])


class TestPortfolioContextLargestHolding:
    def test_largest_position_is_flagged_as_largest_holding(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 30},
                    {"ticker": "NVDA", "weightPercent": 10},
                ]
            },
        )
        view = client.get("/alpha-portfolio").json()
        case_id = next(h for h in view["holdings"] if h["ticker"] == "AMD")["caseId"]
        assert case_id is not None

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert "largest_holding" in body["portfolioContext"]["facts"]


class TestConvictionNeverInvented:
    def test_conviction_is_always_unavailable_regardless_of_decision_confidence(self, client):
        case_id = _link_holding(client, "AMD")
        _record_decision(client, case_id=case_id, subject="AMD", confidence=99)

        body = client.get(f"/cases/{case_id}/intelligence").json()
        assert body["conviction"]["available"] is False
        # The investor's own confidence is shown only on Decision History,
        # correctly labeled, never folded into "conviction".
        assert body["decisionHistory"][0]["investorConfidence"] == 99


class TestRegressionOtherEndpointsUnaffected:
    def test_case_decision_outcome_and_portfolio_status_endpoints_unaffected(self, client):
        case_id = _link_holding(client, "AMD")
        decision = _record_decision(client, case_id=case_id, subject="AMD")
        _record_outcome(client, decision)

        assert client.get(f"/cases/{case_id}").status_code == 200
        assert client.get("/decisions").status_code == 200
        assert client.get("/outcomes").status_code == 200
        assert client.get("/alpha-portfolio").status_code == 200
        status = client.get("/alpha-portfolio/status")
        assert status.status_code == 200
        assert status.json()["exists"] is True
        intelligence = client.get("/alpha-portfolio/intelligence")
        assert intelligence.status_code == 200
        assert intelligence.json()["exists"] is True

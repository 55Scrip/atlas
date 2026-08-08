"""ATLAS-015 — Portfolio Status: workflow-completeness report.

Exercises `GET /alpha-portfolio/status` end-to-end through the real
Case/Decision/Outcome/Observation/Alpha-portfolio APIs -- nothing
mocked, following the exact fixture/helper pattern already established
in `test_router.py` and `test_execution_v1_scenarios.py`.
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
    than manually opening and linking one."""
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


def _apply_trade(client, decision: dict, outcome: dict, **overrides) -> dict:
    payload = {
        "outcomeId": outcome["id"],
        "decisionId": decision["id"],
        "security": decision["subject"],
        "transactionType": "BUY",
        "quantity": 1,
        "executionPrice": 100,
        "executedAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/alpha-portfolio/apply-trade", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


class TestEmptyAndUnestablishedPortfolio:
    def test_returns_exists_false_before_a_portfolio_is_established(self, client):
        response = client.get("/alpha-portfolio/status")
        assert response.status_code == 200
        body = response.json()
        assert body["exists"] is False
        assert body["summary"] is None
        assert body["attentionItems"] == []
        assert body["reviewQueue"] == []
        assert body["health"] is None


class TestPortfolioSummaryPopulated:
    def test_summary_reflects_holdings_and_concentration(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 60},
                    {"ticker": "NVDA", "weightPercent": 20},
                ],
            },
        )
        body = client.get("/alpha-portfolio/status").json()
        assert body["exists"] is True
        summary = body["summary"]
        assert summary["holdingsCount"] == 2
        assert summary["largestPositionTicker"] == "AMD"
        # The plain `weight_percent` already shown on the Holdings list
        # -- not the reused calculation engine's `largest_weight`, which
        # would read 75% here (60 / (60+20), a share of known holdings
        # only) and visibly disagree with "AMD -- 60%" in Holdings.
        assert summary["largestPositionWeightPercent"] == pytest.approx(60.0, abs=0.1)
        assert summary["unallocatedPercent"] == pytest.approx(20.0, abs=0.01)
        assert summary["concentrationLevel"] is not None
        # ATLAS-027: both holdings are auto-cased by import; no
        # decisions, outcomes, or trades recorded yet.
        assert summary["numberOfInvestmentCases"] == 2
        assert summary["openDecisions"] == 0
        assert summary["pendingOutcomes"] == 0
        assert summary["pendingExecutions"] == 0


class TestNeedsAttentionGenerated:
    def test_import_no_longer_flags_missing_case(self, client):
        """ATLAS-027: import auto-generates and links a Case for every
        recognized holding, so a freshly-imported holding with no
        further activity has zero attention items -- not MISSING_CASE."""
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        body = client.get("/alpha-portfolio/status").json()
        categories = {item["category"] for item in body["attentionItems"] if item["ticker"] == "AMD"}
        assert categories == set()
        assert body["summary"]["numberOfInvestmentCases"] == 1

    def test_decision_without_outcome(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        case_id = _holding_case_id(client, "AMD")
        _record_decision(client, case_id=case_id, subject="AMD")

        body = client.get("/alpha-portfolio/status").json()
        items = [item for item in body["attentionItems"] if item["ticker"] == "AMD"]
        assert any(item["category"] == "DECISION_WITHOUT_OUTCOME" for item in items)
        assert body["summary"]["numberOfInvestmentCases"] == 1
        assert body["summary"]["openDecisions"] == 1

    def test_outcome_without_execution(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        case_id = _holding_case_id(client, "AMD")
        decision = _record_decision(client, case_id=case_id, subject="AMD")
        _record_outcome(client, decision)

        body = client.get("/alpha-portfolio/status").json()
        items = [item for item in body["attentionItems"] if item["ticker"] == "AMD"]
        assert any(item["category"] == "OUTCOME_WITHOUT_EXECUTION" for item in items)
        assert not any(item["category"] == "DECISION_WITHOUT_OUTCOME" for item in items)
        assert body["summary"]["pendingOutcomes"] == 1

    def test_fully_reported_execution_raises_no_flags_for_that_chain(self, client):
        # Mode A (absolute values known): a confirmed trade reconciles
        # automatically, so a fully-reported chain truly has nothing
        # left outstanding. Mode B would still leave the holding
        # AWAITING_RECONCILIATION -- covered separately below.
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "AMD", "weightPercent": 40, "valueAbsolute": 400}],
                "cashWeightPercent": 60,
                "cashValueAbsolute": 600,
            },
        )
        case_id = _holding_case_id(client, "AMD")
        decision = _record_decision(client, case_id=case_id, subject="AMD")
        outcome = _record_outcome(client, decision)
        _apply_trade(client, decision, outcome, security="AMD")

        body = client.get("/alpha-portfolio/status").json()
        items = [item for item in body["attentionItems"] if item["ticker"] == "AMD"]
        assert items == []
        assert body["summary"]["openDecisions"] == 0
        assert body["summary"]["pendingOutcomes"] == 0

    def test_observation_without_decision(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        case_id = _holding_case_id(client, "AMD")
        client.post(
            "/observations",
            json={
                "caseId": case_id,
                "subject": "AMD",
                "statement": "Noted something.",
                "observedAt": datetime.now(timezone.utc).isoformat(),
            },
        )

        body = client.get("/alpha-portfolio/status").json()
        items = [item for item in body["attentionItems"] if item["ticker"] == "AMD"]
        assert any(item["category"] == "OBSERVATION_WITHOUT_DECISION" for item in items)

    def test_very_old_case_flagged_past_the_threshold(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        case_id = _holding_case_id(client, "AMD")
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        decision = _record_decision(client, case_id=case_id, subject="AMD", decidedAt=old_timestamp)
        _record_outcome(client, decision)

        body = client.get("/alpha-portfolio/status").json()
        items = [item for item in body["attentionItems"] if item["ticker"] == "AMD"]
        old_case_items = [item for item in items if item["category"] == "VERY_OLD_CASE"]
        assert len(old_case_items) == 1
        assert old_case_items[0]["ageDays"] >= 200

    def test_awaiting_reconciliation_is_flagged(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        case_id = _holding_case_id(client, "AMD")
        decision = _record_decision(client, case_id=case_id, subject="AMD")
        outcome = _record_outcome(client, decision)
        _apply_trade(client, decision, outcome, security="AMD")  # Mode B -> AWAITING_RECONCILIATION

        body = client.get("/alpha-portfolio/status").json()
        items = [item for item in body["attentionItems"] if item["ticker"] == "AMD"]
        assert any(item["category"] == "AWAITING_RECONCILIATION" for item in items)
        assert body["summary"]["pendingExecutions"] == 1


class TestReviewQueueGenerated:
    def test_review_queue_is_sorted_by_reason_count_then_ticker(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 30},
                    {"ticker": "NVDA", "weightPercent": 30},
                ],
            },
        )
        # AMD: auto-cased by import, one decision without outcome AND
        # (via an observation) an observation-without-decision flag ->
        # 2 reasons.
        amd_case = _holding_case_id(client, "AMD")
        _record_decision(client, case_id=amd_case, subject="AMD")
        client.post(
            "/observations",
            json={
                "caseId": amd_case,
                "subject": "AMD",
                "statement": "Unrelated note.",
                "observedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        # NVDA: also auto-cased (ATLAS-027 -- MISSING_CASE can no longer
        # happen here), but has its own observation-without-decision ->
        # 1 reason.
        nvda_case = _holding_case_id(client, "NVDA")
        client.post(
            "/observations",
            json={
                "caseId": nvda_case,
                "subject": "NVDA",
                "statement": "Unrelated note.",
                "observedAt": datetime.now(timezone.utc).isoformat(),
            },
        )

        body = client.get("/alpha-portfolio/status").json()
        queue = body["reviewQueue"]
        assert queue[0]["ticker"] == "AMD"
        assert queue[0]["reasonCount"] == 2
        assert queue[1]["ticker"] == "NVDA"
        assert queue[1]["reasonCount"] == 1


class TestPortfolioHealthPopulated:
    def test_health_reflects_coverage_and_completeness(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 40},
                    {"ticker": "NVDA", "weightPercent": 30},
                ],
            },
        )

        body = client.get("/alpha-portfolio/status").json()
        health = body["health"]
        assert health["holdingsCount"] == 2
        # ATLAS-027: both holdings are auto-cased by import.
        assert health["holdingsWithCaseCount"] == 2
        assert health["allocatedPercent"] == pytest.approx(70.0, abs=0.01)
        assert health["unknownInstrumentTickers"] == []

    def test_malformed_ticker_surfaces_as_unknown_instrument(self, client):
        # `AlphaHolding` itself only uppercases/trims a ticker -- it has
        # no character-set validation -- so a structurally odd string
        # (here, an embedded space) can still reach persistence. Health
        # must surface it rather than silently treat it as a normal
        # holding.
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 30},
                    {"ticker": "ODD TICKER", "weightPercent": 10},
                ]
            },
        )
        body = client.get("/alpha-portfolio/status").json()
        assert body["health"]["unknownInstrumentTickers"] == ["ODD TICKER"]


class TestHoldingsAndImportUnchanged:
    def test_portfolio_view_endpoint_is_unaffected(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}]},
        )
        response = client.get("/alpha-portfolio")
        assert response.status_code == 200
        body = response.json()
        assert body["exists"] is True
        assert body["holdings"][0]["ticker"] == "AMD"

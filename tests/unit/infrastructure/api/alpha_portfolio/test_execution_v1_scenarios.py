"""ATLAS-014 — Decision Execution -> Portfolio Update (Alpha).

Builds on Alpha Sprint 1B's existing trade-application pipeline
(`apply_confirmed_trade` / `POST /alpha-portfolio/apply-trade`) rather
than introducing a parallel execution model — see
`atlas/alpha/portfolio/service.py::TransactionType`. These tests cover
the one genuinely new behavior this sprint adds (EXIT fully removes a
holding, in both Mode A and Mode B) plus the sprint's own explicit
acceptance criteria: Decision immutability, immediate portfolio
reflection, multiple sequential executions, and state surviving a
fresh read. Nothing here duplicates `test_router.py::TestApplyTrade` —
it already covers BUY/SELL basics, outcome/decision verification, and
duplicate-apply rejection.

Follows the exact fixture and helper pattern already established in
`test_router.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone

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


def _record_decision(client, *, subject="NVDA") -> dict:
    case_id = client.post("/cases").json()["caseId"]
    response = client.post(
        "/decisions",
        json={
            "caseId": case_id,
            "userId": "00000000-0000-0000-0000-000000000001",
            "decisionType": "BUY",
            "subject": subject,
            "reason": "Testing execution.",
            "confidence": 70,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _record_outcome(client, decision: dict, **overrides) -> dict:
    payload = {
        "decisionId": decision["id"],
        "statement": "Executed.",
        "occurredAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/outcomes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _apply(client, decision: dict, outcome: dict, **overrides) -> dict:
    payload = {
        "outcomeId": outcome["id"],
        "decisionId": decision["id"],
        "security": "NVDA",
        "transactionType": "BUY",
        "quantity": 1,
        "executionPrice": 100,
        "executedAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/alpha-portfolio/apply-trade", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


class TestBuyAddSellUseTheExistingWeightBasedModel:
    """No quantity-based accounting introduced: BUY/ADD/SELL still only
    ever touch `weightPercent` / `valueAbsolute`, exactly as Alpha
    Sprint 1B already established."""

    def test_add_behaves_identically_to_buy_in_absolute_mode(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60, "valueAbsolute": 600}],
                "cashWeightPercent": 40,
                "cashValueAbsolute": 400,
            },
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        body = _apply(client, decision, outcome, transactionType="ADD", quantity=1, executionPrice=100)

        holding = next(h for h in body["holdings"] if h["ticker"] == "NVDA")
        assert holding["valueAbsolute"] == 700
        assert holding["reconciliationStatus"] == "UPDATED"

    def test_buy_increases_position_in_percentage_mode_and_flags_reconciliation(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        body = _apply(client, decision, outcome, transactionType="BUY")

        holding = next(h for h in body["holdings"] if h["ticker"] == "NVDA")
        assert holding["reconciliationStatus"] == "AWAITING_RECONCILIATION"
        assert body["awaitingReconciliation"] is True
        # Never invents a new percentage in Mode B.
        assert holding["weightPercent"] == 60

    def test_sell_decreases_position_in_absolute_mode(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60, "valueAbsolute": 600}],
                "cashWeightPercent": 40,
                "cashValueAbsolute": 400,
            },
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        body = _apply(client, decision, outcome, transactionType="SELL", quantity=1, executionPrice=100)

        holding = next(h for h in body["holdings"] if h["ticker"] == "NVDA")
        assert holding["valueAbsolute"] == 500
        assert holding["reconciliationStatus"] == "UPDATED"


class TestExitRemovesTheHolding:
    """ATLAS-014's one genuinely new behavior: a confirmed EXIT removes
    the holding from the active portfolio outright, in both modes."""

    def test_exit_removes_the_holding_in_absolute_mode(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "NVDA", "weightPercent": 60, "valueAbsolute": 600},
                    {"ticker": "AMD", "weightPercent": 20, "valueAbsolute": 200},
                ],
                "cashWeightPercent": 20,
                "cashValueAbsolute": 200,
            },
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        body = _apply(client, decision, outcome, transactionType="EXIT", quantity=6, executionPrice=100)

        tickers = {h["ticker"] for h in body["holdings"]}
        assert "NVDA" not in tickers
        assert "AMD" in tickers
        assert body["numberOfHoldings"] == 1
        # Proceeds credited to cash, remaining holding's weight recomputed.
        assert body["cashValueAbsolute"] == 800
        amd = next(h for h in body["holdings"] if h["ticker"] == "AMD")
        assert amd["weightPercent"] == pytest.approx(20.0, abs=0.01)

    def test_exit_removes_the_holding_in_percentage_mode_without_renormalizing(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "NVDA", "weightPercent": 60},
                    {"ticker": "AMD", "weightPercent": 20},
                ],
            },
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        body = _apply(client, decision, outcome, transactionType="EXIT", quantity=6, executionPrice=100)

        tickers = {h["ticker"] for h in body["holdings"]}
        assert "NVDA" not in tickers
        assert "AMD" in tickers
        # AMD's own weight is untouched -- no invented renormalization.
        amd = next(h for h in body["holdings"] if h["ticker"] == "AMD")
        assert amd["weightPercent"] == 20

    def test_exit_drops_the_holdings_case_link_but_the_case_itself_is_untouched(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        case_link = client.post("/cases").json()["caseId"]
        client.post("/alpha-portfolio/holdings/NVDA/case-link", json={"candidateCaseId": case_link})

        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        body = _apply(client, decision, outcome, transactionType="EXIT", quantity=6, executionPrice=100)

        assert not any(h["ticker"] == "NVDA" for h in body["holdings"])
        # The Investment Case itself still exists in Core, untouched.
        response = client.get(f"/cases/{case_link}")
        assert response.status_code == 200

    def test_exit_requires_an_existing_holding(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 20}]},
        )
        decision = _record_decision(client, subject="NVDA")
        outcome = _record_outcome(client, decision)
        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "EXIT",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 400

    def test_reload_after_exit_confirms_the_holding_is_gone(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        _apply(client, decision, outcome, transactionType="EXIT", quantity=6, executionPrice=100)

        reloaded = client.get("/alpha-portfolio")
        assert reloaded.status_code == 200
        assert not any(h["ticker"] == "NVDA" for h in reloaded.json()["holdings"])


class TestDecisionRemainsImmutableAfterExecution:
    def test_decision_fields_are_identical_before_and_after_exit(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        decision = _record_decision(client)
        before = client.get(f"/decisions/{decision['id']}")
        assert before.status_code == 200

        outcome = _record_outcome(client, decision)
        _apply(client, decision, outcome, transactionType="EXIT", quantity=6, executionPrice=100)

        after = client.get(f"/decisions/{decision['id']}")
        assert after.status_code == 200
        assert after.json() == before.json()


class TestMultipleExecutionsInSequence:
    def test_buy_then_sell_then_exit_all_apply_in_order(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60, "valueAbsolute": 600}],
                "cashWeightPercent": 40,
                "cashValueAbsolute": 400,
            },
        )

        decision_1 = _record_decision(client)
        outcome_1 = _record_outcome(client, decision_1)
        body_1 = _apply(client, decision_1, outcome_1, transactionType="BUY", quantity=1, executionPrice=100)
        assert next(h for h in body_1["holdings"] if h["ticker"] == "NVDA")["valueAbsolute"] == 700

        decision_2 = _record_decision(client)
        outcome_2 = _record_outcome(client, decision_2)
        body_2 = _apply(client, decision_2, outcome_2, transactionType="SELL", quantity=2, executionPrice=100)
        assert next(h for h in body_2["holdings"] if h["ticker"] == "NVDA")["valueAbsolute"] == 500

        decision_3 = _record_decision(client)
        outcome_3 = _record_outcome(client, decision_3)
        body_3 = _apply(client, decision_3, outcome_3, transactionType="EXIT", quantity=5, executionPrice=100)
        assert not any(h["ticker"] == "NVDA" for h in body_3["holdings"])

        # Every execution left its own durable trade-log entry.
        trade_log = client.get("/alpha-portfolio/trade-log").json()
        assert len(trade_log) == 3
        assert [entry["transactionType"] for entry in trade_log] == ["BUY", "SELL", "EXIT"]

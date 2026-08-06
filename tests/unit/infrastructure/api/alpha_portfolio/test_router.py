"""API tests for the Alpha Portfolio REST controller.

Includes the Alpha Sprint 1A Foundation Patch regressions (holding-to-
Investment-Case reuse, cash-consistency rejection, duplicate-ticker
rejection) and Alpha Sprint 1B (external trade application, portfolio
reconciliation, trade log).
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
    """One shared in-memory engine overrides `get_decision_engine` for
    the whole app -- every endpoint (cases, decisions, observations,
    outcomes, alpha-portfolio) reads and writes the same clean database
    for this test only, exactly mirroring how the real app shares one
    physical `atlas.db` file, and never touching it.

    `create_decision_table` is called explicitly because the real
    `get_decision_engine()` calls it internally, once, as part of
    constructing the engine itself (every other table is created by its
    own dependency provider, per-request) -- overriding the provider
    wholesale bypasses that one-time call, so it must be repeated here.
    """
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
            "reason": "Testing.",
            "confidence": 70,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _record_outcome(client, decision: dict, **overrides) -> dict:
    payload = {
        "decisionId": decision["id"],
        "statement": "Bought shares.",
        "occurredAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/outcomes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestGetPortfolioBeforeEstablished:
    def test_returns_200_with_exists_false(self, client):
        response = client.get("/alpha-portfolio")
        assert response.status_code == 200
        assert response.json() == {"exists": False, **_empty_fields()}


class TestImportPortfolio:
    def test_returns_201_with_derived_view(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["exists"] is True
        assert body["entryMode"] == "IMPORTED"
        assert body["numberOfHoldings"] == 1
        assert body["hasAbsoluteValues"] is False
        assert body["totalValue"] is None
        assert body["holdings"][0]["caseId"] is None
        assert body["holdings"][0]["reconciliationStatus"] == "NONE"

    def test_rejects_empty_holdings_with_400(self, client):
        response = client.post(
            "/alpha-portfolio/import", json={"holdings": [], "cashWeightPercent": None}
        )
        assert response.status_code == 400

    def test_percentages_alone_are_accepted_no_absolute_value_required(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 100}]},
        )
        assert response.status_code == 201

    def test_absolute_values_yield_a_real_total(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60, "valueAbsolute": 600}],
                "cashWeightPercent": 40,
                "cashValueAbsolute": 400,
            },
        )
        body = response.json()
        assert body["hasAbsoluteValues"] is True
        assert body["totalValue"] == 1000

    def test_get_after_import_reflects_the_established_state(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 100}]},
        )
        response = client.get("/alpha-portfolio")
        assert response.status_code == 200
        assert response.json()["exists"] is True


class TestCashConsistencyValidation:
    """Alpha Sprint 1A Foundation Patch, Defect 2."""

    def test_rejects_cash_value_without_cash_weight(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60}],
                "cashValueAbsolute": 1000,
            },
        )
        assert response.status_code == 400

    def test_rejects_cash_weight_without_cash_value(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60}],
                "cashWeightPercent": 40,
            },
        )
        assert response.status_code == 400

    def test_accepts_neither_cash_field(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 100}]},
        )
        assert response.status_code == 201

    def test_accepts_both_cash_fields(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60}],
                "cashWeightPercent": 40,
                "cashValueAbsolute": 400,
            },
        )
        assert response.status_code == 201

    def test_rejected_import_never_zeroes_out_a_previously_established_cash_figure(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60}],
                "cashWeightPercent": 40,
                "cashValueAbsolute": 400,
            },
        )
        rejected = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "AMD", "weightPercent": 50}],
                "cashValueAbsolute": 999,
            },
        )
        assert rejected.status_code == 400

        unchanged = client.get("/alpha-portfolio")
        assert unchanged.json()["cashWeightPercent"] == 40
        assert unchanged.json()["cashValueAbsolute"] == 400


class TestDuplicateTickerValidation:
    """Alpha Sprint 1A Foundation Patch, Defect 3."""

    @pytest.mark.parametrize("second_ticker", ["NVDA", "nvda", "nvda "])
    def test_rejects_duplicate_ticker_after_normalization(self, client, second_ticker):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "NVDA", "weightPercent": 50},
                    {"ticker": second_ticker, "weightPercent": 50},
                ],
            },
        )
        assert response.status_code == 400

    def test_distinct_tickers_are_accepted(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "NVDA", "weightPercent": 50},
                    {"ticker": "AMD", "weightPercent": 50},
                ],
            },
        )
        assert response.status_code == 201


class TestAllocationBoundsValidation:
    def test_rejects_a_single_weight_above_100(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 150}]},
        )
        assert response.status_code == 400

    def test_rejects_total_allocation_above_100(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "NVDA", "weightPercent": 70},
                    {"ticker": "AMD", "weightPercent": 40},
                ],
            },
        )
        assert response.status_code == 400

    def test_accepts_total_allocation_below_100(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        assert response.status_code == 201


class TestFromScratch:
    def test_returns_201_with_empty_holdings(self, client):
        response = client.post(
            "/alpha-portfolio/from-scratch",
            json={"objective": "Grow capital", "horizon": "Long"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["exists"] is True
        assert body["entryMode"] == "FROM_SCRATCH"
        assert body["holdings"] == []
        assert body["objective"] == "Grow capital"
        assert body["horizon"] == "Long"

    def test_requires_objective(self, client):
        response = client.post(
            "/alpha-portfolio/from-scratch", json={"objective": "", "horizon": "Long"}
        )
        assert response.status_code == 400

    def test_requires_horizon(self, client):
        response = client.post(
            "/alpha-portfolio/from-scratch", json={"objective": "Grow", "horizon": ""}
        )
        assert response.status_code == 400


class TestHoldingCaseLink:
    """Alpha Sprint 1A Foundation Patch, Defect 1: a holding must reuse
    its existing Investment Case rather than creating a new one on every
    "Open Investment Case" click."""

    def test_returns_404_before_a_portfolio_is_established(self, client):
        response = client.post(
            "/alpha-portfolio/holdings/NVDA/case-link", json={"candidateCaseId": "abc"}
        )
        assert response.status_code == 404

    def test_returns_404_for_an_unknown_ticker(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 100}]},
        )
        response = client.post(
            "/alpha-portfolio/holdings/AMD/case-link", json={"candidateCaseId": "abc"}
        )
        assert response.status_code == 404

    def test_first_call_persists_the_candidate_case_id(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 100}]},
        )
        response = client.post(
            "/alpha-portfolio/holdings/NVDA/case-link", json={"candidateCaseId": "case-1"}
        )
        assert response.status_code == 200
        assert response.json()["caseId"] == "case-1"

        view = client.get("/alpha-portfolio").json()
        assert view["holdings"][0]["caseId"] == "case-1"

    def test_repeated_calls_reuse_the_first_case_id(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 100}]},
        )
        client.post("/alpha-portfolio/holdings/NVDA/case-link", json={"candidateCaseId": "case-1"})
        second = client.post(
            "/alpha-portfolio/holdings/NVDA/case-link", json={"candidateCaseId": "case-2"}
        )
        third = client.post(
            "/alpha-portfolio/holdings/NVDA/case-link", json={"candidateCaseId": "case-3"}
        )

        assert second.json()["caseId"] == "case-1"
        assert third.json()["caseId"] == "case-1"

    def test_ticker_lookup_is_normalization_insensitive(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 100}]},
        )
        response = client.post(
            "/alpha-portfolio/holdings/nvda /case-link", json={"candidateCaseId": "case-1"}
        )
        assert response.status_code == 200
        assert response.json()["caseId"] == "case-1"


class TestHoldingCaseLinkPreservesObservationVisibility:
    """End-to-end proof for Defect 1's third requirement: reopening the
    same Case must still show its previously recorded Observation. Uses
    the real, unmodified Case and Observation Core APIs mounted in the
    same app -- nothing here is mocked."""

    def test_reopening_the_reused_case_still_shows_its_observation(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 100}]},
        )

        real_case = client.post("/cases").json()
        real_case_id = real_case["caseId"]

        observation = client.post(
            "/observations",
            json={
                "caseId": real_case_id,
                "subject": "NVDA",
                "statement": "Data center revenue reaccelerated.",
                "observedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert observation.status_code == 201

        first_link = client.post(
            "/alpha-portfolio/holdings/NVDA/case-link",
            json={"candidateCaseId": real_case_id},
        )
        assert first_link.json()["caseId"] == real_case_id

        # A second "Open Investment Case" click with a different candidate
        # (as if the frontend had created a fresh, unlinked Case) must
        # still resolve back to the same, already-linked real Case.
        another_case = client.post("/cases").json()
        second_link = client.post(
            "/alpha-portfolio/holdings/NVDA/case-link",
            json={"candidateCaseId": another_case["caseId"]},
        )
        assert second_link.json()["caseId"] == real_case_id

        all_observations = client.get("/observations").json()
        observations_for_case = [o for o in all_observations if o["caseId"] == real_case_id]
        assert len(observations_for_case) == 1
        assert observations_for_case[0]["statement"] == "Data center revenue reaccelerated."


class TestApplyTrade:
    """Alpha Sprint 1B: external trade recording via the real Case,
    Decision, and Outcome Core APIs -- nothing mocked."""

    def test_verifies_outcome_exists(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": "00000000-0000-0000-0000-000000000099",
                "decisionId": "00000000-0000-0000-0000-000000000098",
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 404

    def test_verifies_outcome_belongs_to_decision(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)

        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": "00000000-0000-0000-0000-000000000098",
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 400

    def test_decision_and_outcome_require_no_observation(self, client):
        """Investment Case v2's decision-action UI ("Add to Position",
        "Trim Position", "Remove Position") records a Decision directly
        against a Case and later an Outcome against that Decision, with
        no Observation ever created first --
        `Decision.observation_id` is optional
        (`atlas/core/domain/decision/entity.py`) and `Outcome` has no
        Observation dependency at all (`atlas/core/domain/outcome/
        entity.py`). Every trade-flow test in this class already
        exercises that exact path via `_record_decision`/
        `_record_outcome` (neither ever sends `observationId`); this
        test makes the invariant explicit and named rather than an
        incidental side effect, and confirms the full chain -- Decision
        with no Observation, through Outcome, through apply-trade --
        still updates the portfolio."""
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60, "valueAbsolute": 600}]},
        )
        decision = _record_decision(client)
        assert decision["observationId"] is None

        outcome = _record_outcome(client, decision)

        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 200

    def test_rejects_a_second_apply_for_the_same_outcome(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        payload = {
            "outcomeId": outcome["id"],
            "decisionId": decision["id"],
            "security": "NVDA",
            "transactionType": "BUY",
            "quantity": 1,
            "executionPrice": 100,
            "executedAt": datetime.now(timezone.utc).isoformat(),
        }
        first = client.post("/alpha-portfolio/apply-trade", json=payload)
        assert first.status_code == 200
        second = client.post("/alpha-portfolio/apply-trade", json=payload)
        assert second.status_code == 409

    def test_absolute_mode_updates_automatically(self, client):
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

        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 200
        body = response.json()
        holding = next(h for h in body["holdings"] if h["ticker"] == "NVDA")
        assert holding["valueAbsolute"] == 700
        assert holding["reconciliationStatus"] == "UPDATED"
        assert body["awaitingReconciliation"] is False

    def test_rejects_a_buy_costing_more_than_available_cash(self, client):
        # Independent verification regression.
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 67, "valueAbsolute": 200}],
                "cashWeightPercent": 33,
                "cashValueAbsolute": 100,
            },
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)

        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 10,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 400

        unchanged = client.get("/alpha-portfolio").json()
        assert unchanged["holdings"][0]["valueAbsolute"] == 200
        assert unchanged["cashValueAbsolute"] == 100
        assert client.get("/alpha-portfolio/trade-log").json() == []

    def test_rejects_a_sell_exceeding_the_holdings_current_value(self, client):
        # Independent verification regression.
        client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 33, "valueAbsolute": 50}],
                "cashWeightPercent": 67,
                "cashValueAbsolute": 100,
            },
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)

        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "SELL",
                "quantity": 10,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 400

        unchanged = client.get("/alpha-portfolio").json()
        assert unchanged["holdings"][0]["valueAbsolute"] == 50
        assert unchanged["cashValueAbsolute"] == 100

    def test_percentage_mode_marks_awaiting_reconciliation(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)

        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 200
        body = response.json()
        holding = next(h for h in body["holdings"] if h["ticker"] == "NVDA")
        assert holding["weightPercent"] == 60
        assert holding["reconciliationStatus"] == "AWAITING_RECONCILIATION"
        assert body["awaitingReconciliation"] is True

    def test_trade_log_lists_the_applied_trade(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 3,
                "executionPrice": 118.5,
                "executedAt": datetime.now(timezone.utc).isoformat(),
                "fees": 1.5,
            },
        )
        log = client.get("/alpha-portfolio/trade-log").json()
        assert len(log) == 1
        assert log[0]["security"] == "NVDA"
        assert log[0]["outcomeId"] == outcome["id"]
        assert log[0]["decisionId"] == decision["id"]
        assert log[0]["fees"] == 1.5

    def test_reconciliation_status_survives_a_fresh_read_after_persistence(self, client):
        # Regression: apply-trade's own direct response correctly showed
        # the new status, but a *separate* GET /alpha-portfolio issued
        # afterwards -- reading the persisted state back from the store,
        # exactly like the real Portfolio page does after a navigation --
        # silently lost it. Caught during Alpha Sprint 1B manual
        # verification, not by tests that only checked a mutating
        # endpoint's own immediate response.
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
        apply_response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert apply_response.json()["holdings"][0]["reconciliationStatus"] == "UPDATED"

        fresh_read = client.get("/alpha-portfolio").json()
        assert fresh_read["holdings"][0]["reconciliationStatus"] == "UPDATED"


class TestReconcile:
    def _percentage_only_awaiting_reconciliation(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 60}]},
        )
        decision = _record_decision(client)
        outcome = _record_outcome(client, decision)
        client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )

    def test_update_holding_weight_clears_status(self, client):
        self._percentage_only_awaiting_reconciliation(client)
        response = client.post(
            "/alpha-portfolio/reconcile",
            json={"mode": "UPDATE_HOLDING_WEIGHT", "ticker": "NVDA", "weightPercent": 65},
        )
        assert response.status_code == 200
        holding = response.json()["holdings"][0]
        assert holding["weightPercent"] == 65
        assert holding["reconciliationStatus"] == "NONE"
        assert response.json()["awaitingReconciliation"] is False

    def test_replace_allocation_clears_status(self, client):
        self._percentage_only_awaiting_reconciliation(client)
        response = client.post(
            "/alpha-portfolio/reconcile",
            json={
                "mode": "REPLACE_ALLOCATION",
                "holdings": [{"ticker": "NVDA", "weightPercent": 70}],
                "cashWeightPercent": 30,
                "cashValueAbsolute": 300,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["holdings"][0]["weightPercent"] == 70
        assert body["holdings"][0]["reconciliationStatus"] == "NONE"
        assert body["awaitingReconciliation"] is False

    def test_update_holding_weight_requires_ticker_and_weight(self, client):
        self._percentage_only_awaiting_reconciliation(client)
        response = client.post(
            "/alpha-portfolio/reconcile", json={"mode": "UPDATE_HOLDING_WEIGHT"}
        )
        assert response.status_code == 400

    def test_returns_404_when_no_portfolio_established(self, client):
        response = client.post(
            "/alpha-portfolio/reconcile",
            json={"mode": "UPDATE_HOLDING_WEIGHT", "ticker": "NVDA", "weightPercent": 50},
        )
        assert response.status_code == 404


def _empty_fields() -> dict:
    return {
        "entryMode": None,
        "hasAbsoluteValues": False,
        "holdings": [],
        "cashWeightPercent": None,
        "cashValueAbsolute": None,
        "totalValue": None,
        "numberOfHoldings": 0,
        "concentrationLevel": None,
        "objective": None,
        "horizon": None,
        "awaitingReconciliation": False,
    }

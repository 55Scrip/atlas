"""Portfolio Import v1 — explicit API-level regression coverage.

No backend code was changed for this sprint: the frontend import flow
reuses `POST /alpha-portfolio/import` (fresh portfolio) and
`POST /alpha-portfolio/reconcile` with `mode: REPLACE_ALLOCATION`
(replacing an existing one) exactly as they already existed and were
already tested elsewhere (`test_router.py`). These tests exist to prove
— at the API level, using the sprint's own worked examples verbatim —
the specific guarantees Portfolio Import v1's UX depends on: that a
replace only touches the *active* portfolio's holdings, that Decision/
Outcome history is untouched, and that a still-present ticker keeps its
Investment Case link rather than getting a duplicate.

Follows the exact fixture pattern already established in
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


def _record_decision(client, *, subject: str) -> dict:
    case_id = client.post("/cases").json()["caseId"]
    response = client.post(
        "/decisions",
        json={
            "caseId": case_id,
            "userId": "00000000-0000-0000-0000-000000000001",
            "decisionType": "BUY",
            "subject": subject,
            "reason": "Portfolio Import v1 regression fixture.",
            "confidence": 70,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _record_outcome(client, decision: dict) -> dict:
    response = client.post(
        "/outcomes",
        json={
            "decisionId": decision["id"],
            "statement": "Bought shares.",
            "occurredAt": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


class TestReplacementRemovesOnlyActivePortfolioHoldings:
    """Phase 9's own worked example, verbatim:

    Current portfolio: AMD, NVDA.
    Import: META, V, ASML.
    After import: Portfolio contains only META, V, ASML.
    History still contains prior AMD/NVDA decisions.
    """

    def test_active_portfolio_contains_exactly_the_new_tickers(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}, {"ticker": "NVDA", "weightPercent": 30}]},
        )
        amd_decision = _record_decision(client, subject="AMD")
        nvda_decision = _record_decision(client, subject="NVDA")
        _record_outcome(client, amd_decision)
        _record_outcome(client, nvda_decision)

        response = client.post(
            "/alpha-portfolio/reconcile",
            json={
                "mode": "REPLACE_ALLOCATION",
                "holdings": [
                    {"ticker": "META", "weightPercent": 20},
                    {"ticker": "V", "weightPercent": 20},
                    {"ticker": "ASML", "weightPercent": 20},
                ],
            },
        )

        assert response.status_code == 200, response.text
        body = response.json()
        active_tickers = {h["ticker"] for h in body["holdings"]}
        assert active_tickers == {"META", "V", "ASML"}
        assert body["numberOfHoldings"] == 3

    def test_prior_amd_and_nvda_decisions_are_untouched_after_replacement(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}, {"ticker": "NVDA", "weightPercent": 30}]},
        )
        amd_decision = _record_decision(client, subject="AMD")
        nvda_decision = _record_decision(client, subject="NVDA")
        _record_outcome(client, amd_decision)
        _record_outcome(client, nvda_decision)

        client.post(
            "/alpha-portfolio/reconcile",
            json={
                "mode": "REPLACE_ALLOCATION",
                "holdings": [
                    {"ticker": "META", "weightPercent": 20},
                    {"ticker": "V", "weightPercent": 20},
                    {"ticker": "ASML", "weightPercent": 20},
                ],
            },
        )

        all_decisions = client.get("/decisions").json()
        subjects = {d["subject"] for d in all_decisions}
        assert {"AMD", "NVDA"}.issubset(subjects)

        all_outcomes = client.get("/outcomes").json()
        assert len(all_outcomes) == 2

        # And each Decision/Outcome is still individually fetchable.
        assert client.get(f"/decisions/{amd_decision['id']}").status_code == 200
        assert client.get(f"/decisions/{nvda_decision['id']}").status_code == 200


class TestInvestmentCaseContinuityAcrossReplacement:
    """Phase 10's own worked example, verbatim:

    Before: AMD -> case A, NVDA -> case B.
    Import: AMD, META.
    After: AMD still links to case A. META has no case yet. NVDA leaves
    active Portfolio but case B and its history remain preserved
    elsewhere. No duplicate Cases are generated.
    """

    def test_amd_keeps_its_existing_case_link_after_replacement(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 50}, {"ticker": "NVDA", "weightPercent": 30}]},
        )
        case_a = client.post("/cases").json()["caseId"]
        client.post("/alpha-portfolio/holdings/AMD/case-link", json={"candidateCaseId": case_a})
        case_b = client.post("/cases").json()["caseId"]
        client.post("/alpha-portfolio/holdings/NVDA/case-link", json={"candidateCaseId": case_b})

        response = client.post(
            "/alpha-portfolio/reconcile",
            json={
                "mode": "REPLACE_ALLOCATION",
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 50},
                    {"ticker": "META", "weightPercent": 30},
                ],
            },
        )

        body = response.json()
        amd = next(h for h in body["holdings"] if h["ticker"] == "AMD")
        meta = next(h for h in body["holdings"] if h["ticker"] == "META")
        assert amd["caseId"] == case_a
        assert meta["caseId"] is None
        assert {h["ticker"] for h in body["holdings"]} == {"AMD", "META"}

    def test_nvdas_case_is_not_deleted_when_it_leaves_the_active_portfolio(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 50}, {"ticker": "NVDA", "weightPercent": 30}]},
        )
        case_a = client.post("/cases").json()["caseId"]
        client.post("/alpha-portfolio/holdings/AMD/case-link", json={"candidateCaseId": case_a})
        case_b = client.post("/cases").json()["caseId"]
        client.post("/alpha-portfolio/holdings/NVDA/case-link", json={"candidateCaseId": case_b})

        client.post(
            "/alpha-portfolio/reconcile",
            json={
                "mode": "REPLACE_ALLOCATION",
                "holdings": [
                    {"ticker": "AMD", "weightPercent": 50},
                    {"ticker": "META", "weightPercent": 30},
                ],
            },
        )

        # Case B (NVDA's) still exists in Core even though NVDA is no
        # longer an active holding -- Alpha only ever held a case_id
        # reference on its own holding row, never owned the Case itself.
        response = client.get(f"/cases/{case_b}")
        assert response.status_code == 200
        assert response.json()["caseId"] == case_b

    def test_re_linking_amd_after_replacement_does_not_create_a_duplicate_case(self, client):
        client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "AMD", "weightPercent": 50}]})
        case_a = client.post("/cases").json()["caseId"]
        client.post("/alpha-portfolio/holdings/AMD/case-link", json={"candidateCaseId": case_a})

        client.post(
            "/alpha-portfolio/reconcile",
            json={"mode": "REPLACE_ALLOCATION", "holdings": [{"ticker": "AMD", "weightPercent": 50}]},
        )

        # A repeated "open Investment Case" attempt for AMD (the same
        # idempotent get-or-set the frontend already relies on) must
        # return the same case, never mint a second one.
        another_candidate = client.post("/cases").json()["caseId"]
        response = client.post(
            "/alpha-portfolio/holdings/AMD/case-link", json={"candidateCaseId": another_candidate}
        )
        assert response.json()["caseId"] == case_a
        assert response.json()["caseId"] != another_candidate


class TestIncompleteAllocationDisclosure:
    """Phase 6 / Scenario D: importing weights that total less than 100%
    must never invent cash to fill the gap -- the existing frontend
    disclosure (`PortfolioPage.tsx`'s own `unallocatedPercent`
    computation) already handles this honestly from real data; this
    test only confirms the backend never invents a value either."""

    def test_partial_allocation_is_persisted_as_is_with_no_invented_cash(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 40}, {"ticker": "NVDA", "weightPercent": 40}]},
        )
        body = response.json()
        assert body["cashWeightPercent"] is None
        total_holdings_weight = sum(h["weightPercent"] for h in body["holdings"])
        assert total_holdings_weight == 80

"""Sprint 20 -- exercises `POST`/`GET
/decisions/{decision_id}/security-confirmation` end-to-end through the
real app and the real `/cases`/`/decisions` endpoints -- nothing
mocked, following the exact fixture/helper pattern already established
in `test_router.py` (Sprint 13's observed-decision-properties suite).
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
def client() -> TestClient:
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


def _record_decision(client: TestClient, *, subject: str, decision_type: str = "BUY", confidence: int = 70) -> dict:
    case_id = client.post("/cases").json()["caseId"]
    payload = {
        "caseId": case_id,
        "userId": "00000000-0000-0000-0000-000000000001",
        "decisionType": decision_type,
        "subject": subject,
        "reason": "Testing.",
        "confidence": confidence,
    }
    response = client.post("/decisions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


_NVDA_CONFIRMATION_PAYLOAD = {
    "ticker": "NVDA",
    "displayName": "NVIDIA CORP",
    "cik": 1045810,
    "discoveryMethod": "title_canonical",
    "source": "sec_company_tickers",
}


class TestCreateConfirmation:
    def test_confirm_returns_201_with_camel_case_body(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        response = client.post(
            f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_CONFIRMATION_PAYLOAD
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["confirmedTicker"] == "NVDA"
        assert body["confirmedDisplayName"] == "NVIDIA CORP"
        assert body["confirmedCik"] == 1045810
        assert body["discoveryMethod"] == "title_canonical"
        assert body["discoverySource"] == "sec_company_tickers"
        assert body["decisionId"] == decision["id"]
        assert "id" in body and "confirmedAt" in body

    def test_get_returns_the_confirmation(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_CONFIRMATION_PAYLOAD)
        response = client.get(f"/decisions/{decision['id']}/security-confirmation")
        assert response.status_code == 200
        assert response.json()["confirmedTicker"] == "NVDA"


class TestUnknownDecision:
    def test_confirm_against_unknown_decision_returns_404(self, client: TestClient) -> None:
        response = client.post(
            "/decisions/00000000-0000-0000-0000-000000000099/security-confirmation",
            json=_NVDA_CONFIRMATION_PAYLOAD,
        )
        assert response.status_code == 404

    def test_get_with_no_confirmation_returns_404(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="AAPL")
        response = client.get(f"/decisions/{decision['id']}/security-confirmation")
        assert response.status_code == 404


class TestUnsupportedSource:
    def test_unknown_source_returns_422(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        payload = {**_NVDA_CONFIRMATION_PAYLOAD, "source": "made_up_provider"}
        response = client.post(f"/decisions/{decision['id']}/security-confirmation", json=payload)
        assert response.status_code == 422


class TestIdempotencyAndConflict:
    def test_same_ticker_resubmitted_is_idempotent(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        first = client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_CONFIRMATION_PAYLOAD)
        second = client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_CONFIRMATION_PAYLOAD)
        assert first.json()["id"] == second.json()["id"]

    def test_different_ticker_returns_409_and_does_not_replace(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_CONFIRMATION_PAYLOAD)
        conflicting_payload = {**_NVDA_CONFIRMATION_PAYLOAD, "ticker": "AVGO", "displayName": "BROADCOM INC"}
        response = client.post(f"/decisions/{decision['id']}/security-confirmation", json=conflicting_payload)
        assert response.status_code == 409
        still_original = client.get(f"/decisions/{decision['id']}/security-confirmation")
        assert still_original.json()["confirmedTicker"] == "NVDA"


class TestMultiCaseIsolation:
    def test_confirming_one_nvidia_decision_never_affects_a_separate_nvda_decision(
        self, client: TestClient
    ) -> None:
        """Real-world scenario: an 'NVDA' Decision and an 'NVIDIA'
        Decision recorded against two separate Cases (Sprint 16's own
        real finding) -- confirming one must leave the other alone."""
        nvidia_decision = _record_decision(client, subject="NVIDIA")
        nvda_decision = _record_decision(client, subject="NVDA")

        client.post(f"/decisions/{nvidia_decision['id']}/security-confirmation", json=_NVDA_CONFIRMATION_PAYLOAD)

        assert client.get(f"/decisions/{nvda_decision['id']}/security-confirmation").status_code == 404
        assert (
            client.get(f"/decisions/{nvidia_decision['id']}/security-confirmation").json()["confirmedTicker"]
            == "NVDA"
        )


class TestDecisionImmutability:
    def test_decision_fields_unchanged_before_and_after_confirmation(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        before = client.get(f"/decisions/{decision['id']}").json()

        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_CONFIRMATION_PAYLOAD)

        after = client.get(f"/decisions/{decision['id']}").json()
        assert before == after
        assert after["subject"] == "NVIDIA"  # never rewritten to "NVDA"

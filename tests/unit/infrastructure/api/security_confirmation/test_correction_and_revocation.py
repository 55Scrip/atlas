"""Sprint 22 -- exercises `POST .../correct` and `POST .../revoke`
end-to-end through the real app, mirroring `test_router.py`'s own
fixture/helper pattern exactly (Sprint 20's own established shape)."""
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


_NVDA_PAYLOAD = {
    "ticker": "NVDA",
    "displayName": "NVIDIA CORP",
    "cik": 1045810,
    "discoveryMethod": "title_canonical",
    "source": "sec_company_tickers",
}
_AVGO_PAYLOAD = {
    "ticker": "AVGO",
    "displayName": "BROADCOM INC",
    "cik": 1730168,
    "discoveryMethod": "ticker_exact",
    "source": "sec_company_tickers",
}


class TestCorrect:
    def test_correct_changes_current_selection(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_PAYLOAD)

        response = client.post(f"/decisions/{decision['id']}/security-confirmation/correct", json=_AVGO_PAYLOAD)
        assert response.status_code == 200
        assert response.json()["confirmedTicker"] == "AVGO"

        current = client.get(f"/decisions/{decision['id']}/security-confirmation")
        assert current.json()["confirmedTicker"] == "AVGO"

    def test_correct_without_prior_confirmation_returns_404(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        response = client.post(f"/decisions/{decision['id']}/security-confirmation/correct", json=_NVDA_PAYLOAD)
        assert response.status_code == 404

    def test_correct_same_ticker_is_noop_returns_existing(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        first = client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_PAYLOAD).json()

        response = client.post(f"/decisions/{decision['id']}/security-confirmation/correct", json=_NVDA_PAYLOAD)
        assert response.status_code == 200
        assert response.json()["id"] == first["id"]

    def test_correct_does_not_rewrite_decision(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_PAYLOAD)
        before = client.get(f"/decisions/{decision['id']}").json()

        client.post(f"/decisions/{decision['id']}/security-confirmation/correct", json=_AVGO_PAYLOAD)

        after = client.get(f"/decisions/{decision['id']}").json()
        assert before == after
        assert after["subject"] == "NVIDIA"


class TestRevoke:
    def test_revoke_clears_current_confirmation(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_PAYLOAD)

        response = client.post(f"/decisions/{decision['id']}/security-confirmation/revoke")
        assert response.status_code == 204

        current = client.get(f"/decisions/{decision['id']}/security-confirmation")
        assert current.status_code == 404

    def test_revoke_when_never_confirmed_is_safe_204(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        response = client.post(f"/decisions/{decision['id']}/security-confirmation/revoke")
        assert response.status_code == 204

    def test_reconfirm_after_revoke_succeeds(self, client: TestClient) -> None:
        decision = _record_decision(client, subject="NVIDIA")
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_PAYLOAD)
        client.post(f"/decisions/{decision['id']}/security-confirmation/revoke")

        response = client.post(f"/decisions/{decision['id']}/security-confirmation", json=_NVDA_PAYLOAD)
        assert response.status_code == 201
        assert client.get(f"/decisions/{decision['id']}/security-confirmation").json()["confirmedTicker"] == "NVDA"


class TestSiblingIsolation:
    def test_correcting_one_decision_never_affects_a_sibling(self, client: TestClient) -> None:
        first = _record_decision(client, subject="NVIDIA")
        second = _record_decision(client, subject="NVIDIA")
        client.post(f"/decisions/{first['id']}/security-confirmation", json=_NVDA_PAYLOAD)
        client.post(f"/decisions/{second['id']}/security-confirmation", json=_NVDA_PAYLOAD)

        client.post(f"/decisions/{first['id']}/security-confirmation/correct", json=_AVGO_PAYLOAD)

        assert client.get(f"/decisions/{first['id']}/security-confirmation").json()["confirmedTicker"] == "AVGO"
        assert client.get(f"/decisions/{second['id']}/security-confirmation").json()["confirmedTicker"] == "NVDA"

    def test_revoking_one_decision_never_affects_a_sibling(self, client: TestClient) -> None:
        first = _record_decision(client, subject="NVIDIA")
        second = _record_decision(client, subject="NVIDIA")
        client.post(f"/decisions/{first['id']}/security-confirmation", json=_NVDA_PAYLOAD)
        client.post(f"/decisions/{second['id']}/security-confirmation", json=_NVDA_PAYLOAD)

        client.post(f"/decisions/{first['id']}/security-confirmation/revoke")

        assert client.get(f"/decisions/{first['id']}/security-confirmation").status_code == 404
        assert client.get(f"/decisions/{second['id']}/security-confirmation").json()["confirmedTicker"] == "NVDA"

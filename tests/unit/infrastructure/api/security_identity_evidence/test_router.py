"""Sprint 23 -- exercises `POST .../verify` and `GET .../verification`
end-to-end through the real app, mirroring `security_confirmation`'s
own fixture/helper pattern exactly. The OpenFIGI provider is overridden
via FastAPI's own dependency-injection mechanism (not monkeypatched)
so no test ever makes a real network call, following the same pattern
`security_discovery`'s router tests already established for its own
external index dependency.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.security_identity_evidence.api.dependencies import get_security_verification_service
from atlas.alpha.security_identity_evidence.openfigi_adapter import OpenFigiMappingResult, OpenFigiMatch
from atlas.alpha.security_identity_evidence.repository import SqlAlchemySecurityIdentityEvidenceRepository
from atlas.alpha.security_identity_evidence.service import SecurityVerificationService
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(eng)
    return eng


@pytest.fixture
def client(engine):
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _record_decision(client: TestClient, *, subject: str = "MSFT") -> dict:
    case_id = client.post("/cases").json()["caseId"]
    payload = {
        "caseId": case_id,
        "userId": "00000000-0000-0000-0000-000000000001",
        "decisionType": "BUY",
        "subject": subject,
        "reason": "Testing.",
        "confidence": 70,
    }
    response = client.post("/decisions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


_MSFT_CONFIRM_PAYLOAD = {
    "ticker": "MSFT",
    "displayName": "MICROSOFT CORP",
    "cik": 789019,
    "discoveryMethod": "ticker_exact",
    "source": "sec_company_tickers",
}


def _override_verification_provider(client: TestClient, engine, provider) -> None:
    from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
    from atlas.alpha.security_confirmation.table import create_security_confirmation_table
    from atlas.alpha.security_identity_evidence.table import create_security_identity_evidence_table

    create_security_confirmation_table(engine)
    create_security_identity_evidence_table(engine)
    client.app.dependency_overrides[get_security_verification_service] = lambda: SecurityVerificationService(
        SqlAlchemySecurityConfirmationRepository(engine),
        SqlAlchemySecurityIdentityEvidenceRepository(engine),
        provider=provider,
    )


class TestVerifyEndpoint:
    def test_verify_returns_201_with_verified_status(self, client: TestClient, engine) -> None:
        decision = _record_decision(client)
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_MSFT_CONFIRM_PAYLOAD)
        _override_verification_provider(
            client,
            engine,
            lambda ticker: OpenFigiMappingResult(
                matches=(OpenFigiMatch("F1", "MSFT", "MICROSOFT CORP", "US", "Common Stock", "Equity"),)
            ),
        )

        response = client.post(f"/decisions/{decision['id']}/security-confirmation/verify")
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "verified"
        assert body["providerIdentifier"] == "F1"
        assert body["provider"] == "openfigi"

    def test_verify_without_confirmation_returns_404(self, client: TestClient, engine) -> None:
        decision = _record_decision(client)
        _override_verification_provider(client, engine, lambda ticker: OpenFigiMappingResult(matches=()))

        response = client.post(f"/decisions/{decision['id']}/security-confirmation/verify")
        assert response.status_code == 404

    def test_verify_does_not_rewrite_decision(self, client: TestClient, engine) -> None:
        decision = _record_decision(client)
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_MSFT_CONFIRM_PAYLOAD)
        before = client.get(f"/decisions/{decision['id']}").json()
        _override_verification_provider(client, engine, lambda ticker: OpenFigiMappingResult(matches=()))

        client.post(f"/decisions/{decision['id']}/security-confirmation/verify")

        after = client.get(f"/decisions/{decision['id']}").json()
        assert before == after

    def test_verify_does_not_change_confirmation(self, client: TestClient, engine) -> None:
        decision = _record_decision(client)
        confirm_response = client.post(
            f"/decisions/{decision['id']}/security-confirmation", json=_MSFT_CONFIRM_PAYLOAD
        ).json()
        _override_verification_provider(client, engine, lambda ticker: OpenFigiMappingResult(matches=()))

        client.post(f"/decisions/{decision['id']}/security-confirmation/verify")

        current_confirmation = client.get(f"/decisions/{decision['id']}/security-confirmation").json()
        assert current_confirmation == confirm_response


class TestVerificationReadEndpoint:
    def test_get_verification_before_any_verify_returns_404(self, client: TestClient) -> None:
        decision = _record_decision(client)
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_MSFT_CONFIRM_PAYLOAD)

        response = client.get(f"/decisions/{decision['id']}/security-confirmation/verification")
        assert response.status_code == 404

    def test_get_verification_returns_latest_after_verify(self, client: TestClient, engine) -> None:
        decision = _record_decision(client)
        client.post(f"/decisions/{decision['id']}/security-confirmation", json=_MSFT_CONFIRM_PAYLOAD)
        _override_verification_provider(client, engine, lambda ticker: OpenFigiMappingResult(matches=()))
        client.post(f"/decisions/{decision['id']}/security-confirmation/verify")

        response = client.get(f"/decisions/{decision['id']}/security-confirmation/verification")
        assert response.status_code == 200
        assert response.json()["status"] == "not_verified"


class TestHistoryEndpoint:
    """Sprint 24 -- the new read-only lifecycle-traceability endpoint."""

    def test_history_empty_before_any_confirmation(self, client: TestClient) -> None:
        decision = _record_decision(client)
        response = client.get(f"/decisions/{decision['id']}/security-confirmation/history")
        assert response.status_code == 200
        assert response.json() == []

    def test_history_reflects_confirm_verify_revoke_correct_sequence(self, client: TestClient, engine) -> None:
        decision = _record_decision(client)
        decision_id = decision["id"]
        client.post(f"/decisions/{decision_id}/security-confirmation", json=_MSFT_CONFIRM_PAYLOAD)
        _override_verification_provider(
            client,
            engine,
            lambda ticker: OpenFigiMappingResult(
                matches=(OpenFigiMatch("F1", "MSFT", "MICROSOFT CORP", "US", "Common Stock", "Equity"),)
            ),
        )
        client.post(f"/decisions/{decision_id}/security-confirmation/verify")
        client.post(f"/decisions/{decision_id}/security-confirmation/revoke")

        nvda_payload = {
            "ticker": "NVDA",
            "displayName": "NVIDIA CORP",
            "cik": 1045810,
            "discoveryMethod": "ticker_exact",
            "source": "sec_company_tickers",
        }
        client.post(f"/decisions/{decision_id}/security-confirmation", json=nvda_payload)

        history = client.get(f"/decisions/{decision_id}/security-confirmation/history").json()
        assert len(history) == 3  # confirmed MSFT, revoked MSFT, confirmed NVDA
        assert history[0]["eventType"] == "confirmed"
        assert history[0]["confirmedTicker"] == "MSFT"
        assert len(history[0]["evidence"]) == 1
        assert history[0]["evidence"][0]["status"] == "verified"

        assert history[1]["eventType"] == "revoked"
        assert history[1]["confirmedTicker"] == "MSFT"
        assert history[1]["evidence"] == []  # revocation event itself was never verified

        assert history[2]["eventType"] == "confirmed"
        assert history[2]["confirmedTicker"] == "NVDA"
        assert history[2]["evidence"] == []  # fresh confirmation, no evidence yet -- never inherits MSFT's


class TestSiblingIsolation:
    def test_verifying_one_decision_never_affects_a_sibling(self, client: TestClient, engine) -> None:
        first = _record_decision(client)
        second = _record_decision(client)
        client.post(f"/decisions/{first['id']}/security-confirmation", json=_MSFT_CONFIRM_PAYLOAD)
        client.post(f"/decisions/{second['id']}/security-confirmation", json=_MSFT_CONFIRM_PAYLOAD)
        _override_verification_provider(client, engine, lambda ticker: OpenFigiMappingResult(matches=()))

        client.post(f"/decisions/{first['id']}/security-confirmation/verify")

        assert client.get(f"/decisions/{first['id']}/security-confirmation/verification").status_code == 200
        assert client.get(f"/decisions/{second['id']}/security-confirmation/verification").status_code == 404

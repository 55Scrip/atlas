"""API tests for the Discovery chat REST controller.

Follows the exact fixture pattern
`tests/unit/infrastructure/api/alpha_portfolio/test_router.py` already
establishes: a shared in-memory SQLite engine overriding
`get_decision_engine`. `get_discovery_provider` is additionally
overridden per test with a fake, in-process provider — no real, paid
provider call is ever made.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.ai.api.dependencies import get_discovery_provider
from atlas.ai.discovery_chat import ChatMessage
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


class RecordingFakeProvider:
    def __init__(self, reply: str = "a generated reply") -> None:
        self.reply = reply
        self.received_system_prompt: str | None = None
        self.received_messages: tuple[ChatMessage, ...] | None = None

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> str:
        self.received_system_prompt = system_prompt
        self.received_messages = messages
        return self.reply


class RaisingFakeProvider:
    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> str:
        raise RuntimeError("provider unavailable")


@pytest.fixture
def client_factory():
    """Returns a function building a fresh `TestClient` sharing one
    in-memory engine, so each test controls its own provider override
    without leaking into others."""

    def _build(provider=None):
        engine = create_engine(
            "sqlite:///:memory:",
            future=True,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        create_decision_table(engine)
        app = create_app()
        app.dependency_overrides[get_decision_engine] = lambda: engine
        app.dependency_overrides[get_discovery_provider] = lambda: provider
        return TestClient(app)

    return _build


def test_successful_chat_request_returns_generated_mode(client_factory):
    provider = RecordingFakeProvider(reply="Here is a considered answer.")
    client = client_factory(provider)

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "How should I think about higher rates?"}], "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "generated"
    assert body["message"] == "Here is a considered answer."


def test_no_provider_configured_returns_truthful_bounded_fallback(client_factory):
    client = client_factory(provider=None)

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "What would strengthen my portfolio?"}], "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "not_configured"
    assert body["message"] is None


def test_provider_failure_does_not_crash_and_returns_provider_error(client_factory):
    client = client_factory(provider=RaisingFakeProvider())

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "Compare Visa and Mastercard."}], "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "provider_error"
    assert body["message"] is None


def test_no_portfolio_established_still_works(client_factory):
    provider = RecordingFakeProvider()
    client = client_factory(provider)

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "General question"}], "language": "en"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "generated"
    assert "recorded Alpha portfolio state" not in provider.received_system_prompt


def test_portfolio_context_included_when_portfolio_exists(client_factory):
    provider = RecordingFakeProvider()
    client = client_factory(provider)

    client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": "AMD", "weightPercent": 65.0}], "cashWeightPercent": None},
    )

    client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "What would strengthen my portfolio?"}], "language": "en"},
    )

    assert "AMD" in provider.received_system_prompt
    assert "65.0" in provider.received_system_prompt


def test_swedish_language_produces_swedish_instruction(client_factory):
    provider = RecordingFakeProvider()
    client = client_factory(provider)

    client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "Hur ska jag tänka kring min portfölj?"}], "language": "sv"},
    )

    assert "Respond in Swedish" in provider.received_system_prompt


def test_english_language_produces_english_instruction(client_factory):
    provider = RecordingFakeProvider()
    client = client_factory(provider)

    client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "How should I think about my portfolio?"}], "language": "en"},
    )

    assert "Respond in English" in provider.received_system_prompt


def test_user_message_reaches_provider_verbatim(client_factory):
    provider = RecordingFakeProvider()
    client = client_factory(provider)
    text = "I received this idea from ChatGPT — ÅÄÖ. What do you think?"

    client.post("/discovery/chat", json={"messages": [{"role": "user", "content": text}], "language": "en"})

    assert provider.received_messages[0].content == text


def test_session_message_history_passed_in_original_order(client_factory):
    provider = RecordingFakeProvider()
    client = client_factory(provider)

    client.post(
        "/discovery/chat",
        json={
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "atlas", "content": "First reply"},
                {"role": "user", "content": "Follow-up question"},
            ],
            "language": "en",
        },
    )

    assert [m.content for m in provider.received_messages] == [
        "First question",
        "First reply",
        "Follow-up question",
    ]
    assert [m.role for m in provider.received_messages] == ["user", "atlas", "user"]

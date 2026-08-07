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
from atlas.ai.discovery_chat import CREATE_OR_OPEN_INVESTMENT_CASE_TOOL, ChatMessage, ProviderReply, ToolCallRequest
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.case.dependencies import get_case_service
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


class RecordingFakeProvider:
    def __init__(self, reply: str = "a generated reply") -> None:
        self.reply = reply
        self.received_system_prompt: str | None = None
        self.received_messages: tuple[ChatMessage, ...] | None = None

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply:
        self.received_system_prompt = system_prompt
        self.received_messages = messages
        return ProviderReply(text=self.reply)


class RaisingFakeProvider:
    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply:
        raise RuntimeError("provider unavailable")


class ToolCallingFakeProvider:
    def __init__(self, ticker: str, tool_name: str = CREATE_OR_OPEN_INVESTMENT_CASE_TOOL) -> None:
        self.ticker = ticker
        self.tool_name = tool_name

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply:
        return ProviderReply(text=None, tool_call=ToolCallRequest(tool_name=self.tool_name, ticker=self.ticker))


class FailingCaseService:
    """A stub standing in for `CaseService` whose `.create()` always
    raises — used only to prove a genuine tool-execution failure
    degrades to an honest `"failed"` outcome rather than a crash or a
    false success claim."""

    def create(self):
        raise RuntimeError("simulated Case creation failure")


@pytest.fixture
def client_factory():
    """Returns a function building a fresh `TestClient` sharing one
    in-memory engine, so each test controls its own provider override
    without leaking into others."""

    def _build(provider=None, case_service=None):
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
        if case_service is not None:
            app.dependency_overrides[get_case_service] = lambda: case_service
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

    assert "in Swedish" in provider.received_system_prompt


def test_english_language_produces_english_instruction(client_factory):
    provider = RecordingFakeProvider()
    client = client_factory(provider)

    client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "How should I think about my portfolio?"}], "language": "en"},
    )

    assert "in English" in provider.received_system_prompt


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


# ── Discovery Tool Calling v1 ────────────────────────────────────────────────


def test_explicit_ticker_produces_a_tool_call_response(client_factory):
    client = client_factory(ToolCallingFakeProvider(ticker="META"))
    client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": "META", "weightPercent": 20.0}], "cashWeightPercent": None},
    )

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "Open an Investment Case for Meta"}], "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "tool_call"
    assert body["message"] is None
    assert body["toolResult"]["tool"] == "create_or_open_investment_case"
    assert body["toolResult"]["outcome"] == "created"
    assert body["toolResult"]["ticker"] == "META"
    assert body["toolResult"]["caseId"] is not None


def test_holding_already_linked_to_a_case_is_reused_not_duplicated(client_factory):
    client = client_factory(ToolCallingFakeProvider(ticker="AMD"))
    client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": "AMD", "weightPercent": 65.0}], "cashWeightPercent": None},
    )
    existing_case_id = client.post("/cases").json()["caseId"]
    client.post(
        "/alpha-portfolio/holdings/AMD/case-link", json={"candidateCaseId": existing_case_id}
    )

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "Open my AMD case"}], "language": "en"},
    )

    body = response.json()
    assert body["toolResult"]["outcome"] == "opened"
    assert body["toolResult"]["caseId"] == existing_case_id


def test_holding_without_a_case_is_created_and_linked(client_factory):
    client = client_factory(ToolCallingFakeProvider(ticker="NVDA"))
    client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": "NVDA", "weightPercent": 30.0}], "cashWeightPercent": None},
    )

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "Create an Investment Case for NVDA"}], "language": "en"},
    )

    body = response.json()
    assert body["toolResult"]["outcome"] == "created"
    case_id = body["toolResult"]["caseId"]
    assert case_id is not None

    # The link actually persisted -- confirmed via the real Portfolio read path.
    portfolio = client.get("/alpha-portfolio").json()
    nvda = next(h for h in portfolio["holdings"] if h["ticker"] == "NVDA")
    assert nvda["caseId"] == case_id


def test_unknown_ticker_asks_for_clarification_and_creates_no_case(client_factory):
    client = client_factory(ToolCallingFakeProvider(ticker="ZZZZ"))
    client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": "AMD", "weightPercent": 65.0}], "cashWeightPercent": None},
    )

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "Open an Investment Case for ZZZZ"}], "language": "en"},
    )

    body = response.json()
    assert body["toolResult"]["outcome"] == "unresolved"
    assert body["toolResult"]["caseId"] is None

    portfolio = client.get("/alpha-portfolio").json()
    amd = next(h for h in portfolio["holdings"] if h["ticker"] == "AMD")
    assert amd["caseId"] is None  # no case silently created for anything


def test_tool_execution_failure_returns_honest_failed_outcome(client_factory):
    client = client_factory(ToolCallingFakeProvider(ticker="META"), case_service=FailingCaseService())
    client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": "META", "weightPercent": 20.0}], "cashWeightPercent": None},
    )

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "Open an Investment Case for Meta"}], "language": "en"},
    )

    assert response.status_code == 200  # never crashes the endpoint
    body = response.json()
    assert body["toolResult"]["outcome"] == "failed"
    assert body["toolResult"]["caseId"] is None


def test_normal_investment_question_produces_no_tool_call(client_factory):
    provider = RecordingFakeProvider(reply="Here is a considered, ordinary answer.")
    client = client_factory(provider)

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "What would strengthen my portfolio?"}], "language": "en"},
    )

    body = response.json()
    assert body["mode"] == "generated"
    assert body["toolResult"] is None
    assert body["message"] == "Here is a considered, ordinary answer."


def test_tool_call_never_mutates_holding_weight_or_creates_a_holding(client_factory):
    """No direct portfolio mutation: the tool may only create/link a
    Case to an *existing* holding, never change its weight, never add a
    brand-new holding for an unresolved ticker."""
    client = client_factory(ToolCallingFakeProvider(ticker="ZZZZ"))
    client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": "AMD", "weightPercent": 65.0}], "cashWeightPercent": None},
    )
    before = client.get("/alpha-portfolio").json()

    client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "Open a case for ZZZZ"}], "language": "en"},
    )

    after = client.get("/alpha-portfolio").json()
    assert after["holdings"] == before["holdings"]
    assert after["numberOfHoldings"] == 1


def test_no_arbitrary_tool_execution_unknown_tool_name_is_refused(client_factory):
    client = client_factory(ToolCallingFakeProvider(ticker="META", tool_name="delete_portfolio"))
    client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": "META", "weightPercent": 20.0}], "cashWeightPercent": None},
    )

    response = client.post(
        "/discovery/chat",
        json={"messages": [{"role": "user", "content": "irrelevant"}], "language": "en"},
    )

    body = response.json()
    assert body["mode"] == "provider_error"
    assert body["toolResult"] is None
    # And the portfolio is provably untouched.
    portfolio = client.get("/alpha-portfolio").json()
    assert portfolio["holdings"][0]["caseId"] is None

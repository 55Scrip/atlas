"""Discovery Intelligence v1 — pure orchestration logic tests.

Every test here uses a fake, in-process `ConversationProvider` — no
real, paid provider call is ever made or required.
"""
from __future__ import annotations

import pytest

from atlas.ai.discovery_chat import (
    ChatMessage,
    HoldingContextInput,
    PortfolioContextInput,
    build_system_prompt,
    render_portfolio_context,
    run_discovery_chat,
)


class FakeProvider:
    """Records exactly what it was called with, returns a fixed reply."""

    def __init__(self, reply: str = "a generated reply") -> None:
        self.reply = reply
        self.received_system_prompt: str | None = None
        self.received_messages: tuple[ChatMessage, ...] | None = None

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> str:
        self.received_system_prompt = system_prompt
        self.received_messages = messages
        return self.reply


class RaisingProvider:
    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> str:
        raise RuntimeError("provider unavailable")


ONE_MESSAGE = (ChatMessage(role="user", content="How should I think about higher interest rates?"),)


class TestNoProviderConfigured:
    def test_returns_not_configured_with_no_message(self):
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=None)
        assert outcome.mode == "not_configured"
        assert outcome.message is None


class TestSuccessfulExchange:
    def test_returns_generated_mode_with_provider_reply(self):
        provider = FakeProvider(reply="Here is a considered answer.")
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert outcome.mode == "generated"
        assert outcome.message == "Here is a considered answer."

    def test_user_message_content_reaches_the_provider_verbatim(self):
        provider = FakeProvider()
        run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert provider.received_messages == ONE_MESSAGE
        assert provider.received_messages[0].content == "How should I think about higher interest rates?"


class TestProviderFailure:
    def test_returns_provider_error_mode_never_raises(self):
        outcome = run_discovery_chat(
            messages=ONE_MESSAGE, language="en", portfolio=None, provider=RaisingProvider()
        )
        assert outcome.mode == "provider_error"
        assert outcome.message is None


class TestSessionHistoryOrder:
    def test_full_session_passed_through_in_original_order(self):
        provider = FakeProvider()
        history = (
            ChatMessage(role="user", content="First question"),
            ChatMessage(role="atlas", content="First reply"),
            ChatMessage(role="user", content="Follow-up question"),
        )
        run_discovery_chat(messages=history, language="en", portfolio=None, provider=provider)
        assert provider.received_messages == history


class TestLanguage:
    def test_swedish_system_prompt_names_swedish(self):
        prompt = build_system_prompt("sv", None)
        assert "Respond in Swedish" in prompt

    def test_english_system_prompt_names_english(self):
        prompt = build_system_prompt("en", None)
        assert "Respond in English" in prompt

    def test_language_reaches_the_provider_via_system_prompt(self):
        provider = FakeProvider()
        run_discovery_chat(messages=ONE_MESSAGE, language="sv", portfolio=None, provider=provider)
        assert "Respond in Swedish" in provider.received_system_prompt


class TestPortfolioContext:
    def test_no_portfolio_renders_no_context_block(self):
        assert render_portfolio_context(None) is None

    def test_empty_holdings_renders_no_context_block(self):
        empty = PortfolioContextInput(
            holdings=(), cash_weight_percent=None, has_absolute_values=False, concentration_level=None
        )
        assert render_portfolio_context(empty) is None

    def test_real_holding_appears_in_rendered_context(self):
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="AMD", weight_percent=65.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level="High",
        )
        rendered = render_portfolio_context(portfolio)
        assert "AMD" in rendered
        assert "65.0" in rendered
        assert "High" in rendered

    def test_no_portfolio_still_works_end_to_end(self):
        provider = FakeProvider()
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert outcome.mode == "generated"
        assert "recorded Alpha portfolio state" not in provider.received_system_prompt

    def test_portfolio_context_included_in_system_prompt(self):
        provider = FakeProvider()
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="NVDA", weight_percent=40.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=10.0,
            has_absolute_values=False,
            concentration_level="Moderate",
        )
        run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=portfolio, provider=provider)
        assert "NVDA" in provider.received_system_prompt
        assert "40.0" in provider.received_system_prompt

    def test_portfolio_never_fabricates_beyond_given_fields(self):
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="TSM", weight_percent=10.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
        )
        rendered = render_portfolio_context(portfolio)
        for forbidden in ("fair value", "price target", "conviction", "valuation multiple"):
            assert forbidden not in rendered.lower()


class TestSystemInstructionsRequireChallenge:
    def test_instructions_require_challenging_assumptions_not_agreement(self):
        prompt = build_system_prompt("en", None)
        assert "challenge" in prompt.lower()
        assert "uncertainty" in prompt.lower()

    def test_instructions_forbid_claiming_live_data_access(self):
        prompt = build_system_prompt("en", None)
        assert "current prices" in prompt.lower() or "today's news" in prompt.lower()

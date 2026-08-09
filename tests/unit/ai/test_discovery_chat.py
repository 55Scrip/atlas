"""Discovery Intelligence v1 — pure orchestration logic tests.

Every test here uses a fake, in-process `ConversationProvider` — no
real, paid provider call is ever made or required.
"""
from __future__ import annotations

import pytest

from atlas.ai.discovery_chat import (
    CREATE_OR_OPEN_INVESTMENT_CASE_TOOL,
    CaseContextInput,
    ChatMessage,
    ConsiderContextInput,
    HoldingContextInput,
    KeyFindingContextInput,
    PortfolioContextInput,
    ProviderReply,
    RiskSignalContextInput,
    ToolCallRequest,
    _strip_leaked_reasoning,
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

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply:
        self.received_system_prompt = system_prompt
        self.received_messages = messages
        return ProviderReply(text=self.reply)


class RaisingProvider:
    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply:
        raise RuntimeError("provider unavailable")


class ToolCallingFakeProvider:
    """Simulates the provider deciding to call a tool instead of (or
    alongside) returning text."""

    def __init__(self, tool_name: str, ticker: str, text: str | None = None) -> None:
        self.tool_name = tool_name
        self.ticker = ticker
        self.text = text

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply:
        return ProviderReply(
            text=self.text, tool_call=ToolCallRequest(tool_name=self.tool_name, ticker=self.ticker)
        )


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
        assert "in Swedish" in prompt

    def test_english_system_prompt_names_english(self):
        prompt = build_system_prompt("en", None)
        assert "in English" in prompt

    def test_language_reaches_the_provider_via_system_prompt(self):
        provider = FakeProvider()
        run_discovery_chat(messages=ONE_MESSAGE, language="sv", portfolio=None, provider=provider)
        assert "in Swedish" in provider.received_system_prompt


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


class TestPortfolioIntelligenceContext:
    """ATLAS-016: Discovery renders the same Key Findings/Consider/Risk
    Signals the Portfolio page shows -- passed in via the same
    `PortfolioContextInput` shape, never reconstructed here."""

    def test_defaults_to_empty_and_renders_nothing_extra(self):
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="AMD", weight_percent=20.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
        )
        rendered = render_portfolio_context(portfolio)
        assert "Portfolio Intelligence" not in rendered

    def test_key_finding_appears_in_rendered_context(self):
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="AMD", weight_percent=40.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level="High",
            key_findings=(KeyFindingContextInput(kind="high_concentration", count=1, tickers=("AMD",)),),
        )
        rendered = render_portfolio_context(portfolio)
        assert "high concentration" in rendered
        assert "AMD" in rendered

    def test_consider_item_never_reads_as_a_trade_instruction(self):
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="AMD", weight_percent=40.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            consider_items=(
                ConsiderContextInput(kind="review_concentration", ticker="AMD", confidence="not_applicable"),
            ),
        )
        rendered = render_portfolio_context(portfolio)
        assert "not a recommendation to buy or sell" in rendered
        for forbidden in ("Sell AMD", "Buy AMD", "Trim AMD"):
            assert forbidden not in rendered

    def test_risk_signal_appears_in_rendered_context(self):
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="AMD", weight_percent=40.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            risk_signals=(RiskSignalContextInput(kind="missing_case", ticker="AMD"),),
        )
        rendered = render_portfolio_context(portfolio)
        assert "no Investment Case" in rendered

    def test_unknown_kind_degrades_to_a_readable_phrase_rather_than_crashing(self):
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="AMD", weight_percent=40.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            key_findings=(KeyFindingContextInput(kind="future_unknown_kind", count=1, tickers=("AMD",)),),
        )
        rendered = render_portfolio_context(portfolio)
        assert "future unknown kind" in rendered


class TestCaseIntelligenceContext:
    """ATLAS-017/018: Discovery renders the exact same Case Intelligence
    facts the Investment Case page shows -- via `CaseContextInput`,
    never reconstructed here."""

    def test_current_thesis_appears_verbatim(self):
        portfolio = PortfolioContextInput(
            holdings=(),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            case_context=CaseContextInput(
                ticker="AMD",
                held=True,
                current_thesis_reason="Durable moat and cheap valuation.",
                confidence="full",
                conviction_level="moderate",
                is_stale=False,
                missing_evidence_kinds=(),
                open_questions=(),
                key_risks=(),
                consider_kinds=(),
            ),
        )
        rendered = render_portfolio_context(portfolio)
        assert "Durable moat and cheap valuation." in rendered
        assert "discussing AMD specifically" in rendered

    def test_unheld_case_states_it_is_not_a_holding(self):
        portfolio = PortfolioContextInput(
            holdings=(),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            case_context=CaseContextInput(
                ticker=None,
                held=False,
                current_thesis_reason=None,
                confidence="not_applicable",
                conviction_level="insufficient_evidence",
                is_stale=False,
                missing_evidence_kinds=(),
                open_questions=(),
                key_risks=(),
                consider_kinds=(),
            ),
        )
        rendered = render_portfolio_context(portfolio)
        assert "not currently a portfolio holding" in rendered

    def test_key_risk_and_missing_evidence_render_readable_phrases(self):
        portfolio = PortfolioContextInput(
            holdings=(),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            case_context=CaseContextInput(
                ticker="AMD",
                held=True,
                current_thesis_reason=None,
                confidence="partial",
                conviction_level="low",
                is_stale=False,
                missing_evidence_kinds=("no_evidence_recorded",),
                open_questions=(),
                key_risks=("contradicting_evidence",),
                consider_kinds=(),
            ),
        )
        rendered = render_portfolio_context(portfolio)
        assert "no evidence recorded for this Investment Case" in rendered
        assert "evidence that contradicts the current thesis" in rendered

    def test_conviction_and_open_questions_render_readable_phrases(self):
        """ATLAS-030: Discovery previously never saw a real Conviction
        (hardcoded unavailable) or any Open Question at all."""
        portfolio = PortfolioContextInput(
            holdings=(),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            case_context=CaseContextInput(
                ticker="AMD",
                held=True,
                current_thesis_reason=None,
                confidence="full",
                conviction_level="high",
                is_stale=False,
                missing_evidence_kinds=(),
                open_questions=("business_durability_not_assessable", "portfolio_factor_not_assessable"),
                key_risks=(),
                consider_kinds=(),
            ),
        )
        rendered = render_portfolio_context(portfolio)
        assert "Conviction: high" in rendered
        assert "Atlas has no business-fact data to assess durability from" in rendered
        assert "a portfolio-wide factor is not yet assessable" in rendered

    def test_repeated_open_question_kinds_are_stated_only_once(self):
        portfolio = PortfolioContextInput(
            holdings=(),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            case_context=CaseContextInput(
                ticker="AMD",
                held=True,
                current_thesis_reason=None,
                confidence="full",
                conviction_level="moderate",
                is_stale=False,
                missing_evidence_kinds=(),
                open_questions=("portfolio_factor_not_assessable",) * 7,
                key_risks=(),
                consider_kinds=(),
            ),
        )
        rendered = render_portfolio_context(portfolio)
        assert rendered.count("a portfolio-wide factor is not yet assessable") == 1

    def test_portfolio_context_facts_render_readable_phrases(self):
        portfolio = PortfolioContextInput(
            holdings=(),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            case_context=CaseContextInput(
                ticker="AMD",
                held=True,
                current_thesis_reason=None,
                confidence="full",
                conviction_level="moderate",
                is_stale=False,
                missing_evidence_kinds=(),
                open_questions=(),
                key_risks=(),
                consider_kinds=(),
                portfolio_context_facts=("largest_holding", "pending_workflow"),
            ),
        )
        rendered = render_portfolio_context(portfolio)
        assert "largest position" in rendered
        assert "pending workflow items" in rendered

    def test_case_context_alone_produces_content_even_with_no_holdings(self):
        portfolio = PortfolioContextInput(
            holdings=(),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            case_context=CaseContextInput(
                ticker=None,
                held=False,
                current_thesis_reason="Early-stage research.",
                confidence="not_applicable",
                conviction_level="insufficient_evidence",
                is_stale=False,
                missing_evidence_kinds=(),
                open_questions=(),
                key_risks=(),
                consider_kinds=(),
            ),
        )
        rendered = render_portfolio_context(portfolio)
        assert rendered is not None
        assert "Early-stage research." in rendered


class TestUnresolvedIdentity:
    """ATLAS-018 Phase 3: a `caseId` that could not be resolved to a
    real Investment Case is disclosed honestly -- never silently
    dropped, never guessed at."""

    def test_unresolved_case_id_is_disclosed_even_with_no_portfolio(self):
        portfolio = PortfolioContextInput(
            holdings=(),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
            unresolved_case_id="not-a-real-uuid",
        )
        rendered = render_portfolio_context(portfolio)
        assert rendered is not None
        assert "could not confirm" in rendered
        assert "Do not guess" in rendered

    def test_no_unresolved_case_id_produces_no_disclosure(self):
        portfolio = PortfolioContextInput(
            holdings=(
                HoldingContextInput(
                    ticker="AMD", weight_percent=20.0, value_absolute=None, reconciliation_status="NONE"
                ),
            ),
            cash_weight_percent=None,
            has_absolute_values=False,
            concentration_level=None,
        )
        rendered = render_portfolio_context(portfolio)
        assert "could not confirm" not in rendered


class TestSystemInstructionsRequireChallenge:
    def test_instructions_require_challenging_assumptions_not_agreement(self):
        prompt = build_system_prompt("en", None)
        assert "challenge" in prompt.lower()
        assert "uncertainty" in prompt.lower()

    def test_instructions_forbid_claiming_live_data_access(self):
        prompt = build_system_prompt("en", None)
        assert "current prices" in prompt.lower() or "today's news" in prompt.lower()


class TestResponseGroundingCategories:
    """ATLAS-018 Phase 7/8: every statement must belong to one of five
    distinct categories (observed facts, evidence, uncertainty, missing
    information, considerations), never blurred together, and every
    non-obvious claim must be traceable to given context."""

    def test_instructions_name_all_five_response_categories(self):
        prompt = build_system_prompt("en", None).lower()
        assert "observed facts" in prompt
        assert "evidence" in prompt
        assert "uncertainty" in prompt
        assert "missing information" in prompt
        assert "considerations" in prompt

    def test_instructions_forbid_blurring_categories_together(self):
        prompt = build_system_prompt("en", None).lower()
        assert "never blur" in prompt or "blur" in prompt

    def test_instructions_require_traceability_to_given_context(self):
        prompt = build_system_prompt("en", None).lower()
        assert "traceable" in prompt


class TestSystemInstructionsForbidVisibleReasoning:
    """Regression coverage for the leak this sprint fixes: a live
    response once began with "Internal reasoning (English):" followed
    by hidden reasoning before the real Swedish answer. The prompt
    itself must never invite that structure."""

    def test_prompt_no_longer_tells_the_model_reasoning_stays_in_english(self):
        prompt = build_system_prompt("sv", None)
        assert "internal reasoning stays in" not in prompt.lower()

    def test_prompt_explicitly_forbids_labeled_reasoning_sections(self):
        prompt = build_system_prompt("en", None)
        lowered = prompt.lower()
        assert "chain of thought" in lowered
        assert "never write out your reasoning" in lowered or "think" in lowered

    def test_prompt_never_itself_contains_the_leaked_phrase_as_an_instruction_to_emit_it(self):
        # The prompt is allowed to *name* the forbidden phrase so it can
        # forbid it; it must never instruct the model to produce it.
        prompt = build_system_prompt("sv", None)
        assert "internal reasoning stays in english" not in prompt.lower()


class LeakingFakeProvider:
    """Simulates the exact defect observed live: a labeled reasoning
    block ahead of the real answer, in the wrong language."""

    def __init__(self, leaked_reasoning: str, real_answer: str) -> None:
        self.leaked_reasoning = leaked_reasoning
        self.real_answer = real_answer

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply:
        return ProviderReply(text=f"{self.leaked_reasoning}\n\n{self.real_answer}")


class TestBackendNeverReturnsLeakedReasoningVerbatim:
    """`_strip_leaked_reasoning` is the narrow backend safety net —
    defense in depth behind the prompt fix, not a replacement for it.
    Each test uses one of the exact forbidden markers the sprint names."""

    def test_internal_reasoning_marker_is_removed_end_to_end(self):
        provider = LeakingFakeProvider(
            leaked_reasoning="Internal reasoning: the investor is asking about AI valuations.",
            real_answer="AI-aktier har fallit, men det är inte tillräckligt för att göra dem attraktiva på egen hand.",
        )
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="sv", portfolio=None, provider=provider)
        raw = f"{provider.leaked_reasoning}\n\n{provider.real_answer}"
        assert outcome.message != raw
        assert "internal reasoning" not in outcome.message.lower()
        assert "AI-aktier har fallit" in outcome.message

    def test_chain_of_thought_marker_is_removed(self):
        provider = LeakingFakeProvider(
            leaked_reasoning="Chain of thought: first consider valuation, then sentiment.",
            real_answer="Here is my actual answer to your question.",
        )
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert "chain of thought" not in outcome.message.lower()
        assert outcome.message == "Here is my actual answer to your question."

    def test_thinking_tag_marker_is_removed(self):
        provider = LeakingFakeProvider(
            leaked_reasoning="<thinking>\nWeighing the investor's concentration risk.\n</thinking>",
            real_answer="Given your concentration, I would be cautious about adding more of the same sector.",
        )
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert "<thinking>" not in outcome.message.lower()
        assert "Given your concentration" in outcome.message

    def test_system_prompt_marker_is_removed(self):
        provider = LeakingFakeProvider(
            leaked_reasoning="System prompt: you are Atlas, an investment decision partner.",
            real_answer="Let's look at the actual question you asked.",
        )
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert "system prompt" not in outcome.message.lower()
        assert outcome.message == "Let's look at the actual question you asked."

    def test_clean_response_with_no_marker_passes_through_unchanged(self):
        provider = FakeProvider(reply="A perfectly ordinary, clean answer with no leak markers.")
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert outcome.message == "A perfectly ordinary, clean answer with no leak markers."


class TestSafetyNetDoesNotDestroyLegitimateContent:
    """The sprint explicitly warns against an aggressive sanitizer.
    Ordinary investment prose legitimately uses the words "reasoning"
    and "thinking" in sentences — only an exact leak-shaped line prefix
    may ever trigger stripping."""

    def test_sentence_containing_the_word_reasoning_is_untouched(self):
        text = "My reasoning here is that concentration risk matters more than headline valuation."
        assert _strip_leaked_reasoning(text) == text

    def test_sentence_containing_thinking_about_is_untouched(self):
        text = "Thinking about your portfolio's concentration, I would look at diversifying first."
        assert _strip_leaked_reasoning(text) == text

    def test_multi_paragraph_legitimate_answer_is_fully_preserved(self):
        text = (
            "The recent decline could improve the setup, but price weakness alone isn't "
            "enough to make the group attractive.\n\n"
            "Given your current portfolio, adding another semiconductor position would "
            "increase concentration."
        )
        assert _strip_leaked_reasoning(text) == text

    def test_no_marker_present_returns_input_unchanged(self):
        text = "Here is a considered, multi-sentence answer with no reasoning label at all."
        assert _strip_leaked_reasoning(text) is text or _strip_leaked_reasoning(text) == text


class TestToolAwareness:
    def test_prompt_mentions_the_tool_and_when_to_prefer_it(self):
        prompt = build_system_prompt("en", None)
        assert CREATE_OR_OPEN_INVESTMENT_CASE_TOOL in prompt

    def test_prompt_instructs_confirming_uncertain_tickers_rather_than_guessing(self):
        prompt = build_system_prompt("en", None)
        assert "confirm" in prompt.lower()

    def test_prompt_forbids_claiming_a_case_was_opened_in_its_own_words(self):
        prompt = build_system_prompt("en", None)
        assert "only the tool result determines what actually happened" in prompt.lower()


class TestToolCallDetection:
    """`run_discovery_chat` only *detects* and validates a tool call —
    it never resolves a ticker or touches the Case API itself (this
    module never imports `atlas.alpha`); that is the router's job."""

    def test_supported_tool_call_is_passed_through_as_tool_call_requested(self):
        provider = ToolCallingFakeProvider(tool_name=CREATE_OR_OPEN_INVESTMENT_CASE_TOOL, ticker="META")
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert outcome.mode == "tool_call_requested"
        assert outcome.message is None
        assert outcome.tool_call_request == ToolCallRequest(
            tool_name=CREATE_OR_OPEN_INVESTMENT_CASE_TOOL, ticker="META"
        )

    def test_ticker_reaches_the_outcome_verbatim(self):
        provider = ToolCallingFakeProvider(tool_name=CREATE_OR_OPEN_INVESTMENT_CASE_TOOL, ticker="tsm")
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert outcome.tool_call_request.ticker == "tsm"

    def test_unrecognized_tool_name_is_refused_never_executed(self):
        """No arbitrary tool execution: a tool name outside the strict
        allowlist is refused as a provider error, never passed through
        as something the router might act on."""
        provider = ToolCallingFakeProvider(tool_name="delete_portfolio", ticker="META")
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert outcome.mode == "provider_error"
        assert outcome.tool_call_request is None
        assert outcome.message is None

    def test_normal_question_with_no_tool_call_behaves_exactly_as_before(self):
        provider = FakeProvider(reply="A considered answer with no tool involved.")
        outcome = run_discovery_chat(messages=ONE_MESSAGE, language="en", portfolio=None, provider=provider)
        assert outcome.mode == "generated"
        assert outcome.tool_call_request is None
        assert outcome.message == "A considered answer with no tool involved."

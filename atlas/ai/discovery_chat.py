"""Discovery Intelligence v1 — the first real conversational layer.

Deliberately built as a fresh module rather than an implementation of
`DiscoveryService` (`atlas/ai/interfaces.py`): that Protocol's shape —
`discover(prompt: str) -> tuple[str, ...]` — has no notion of session
history, portfolio context, or target language, and nothing in the
repository implements or consumes it today (confirmed by repository
investigation before writing this module). Building a fit-for-purpose
shape here is not a competing AI architecture; it lives in the same
package `atlas/ai/` already reserves for "AI service contracts and
future AI orchestration boundaries" (`atlas/domains/ai/__init__.py`).

This module contains only pure, deterministic logic — building the
system prompt, rendering a portfolio context block from real data, and
orchestrating one exchange against an injected provider. It never
imports `atlas.alpha` (enforced by
`tests/test_architecture_boundaries.py::test_ai_discovery_chat_does_not_import_atlas_alpha`,
mirroring the identical precedent `atlas/decision_engine/` already
established for its own one-way, provider-agnostic core). Composing
this module with real Alpha portfolio state and a real provider is the
router's job (`atlas/ai/api/router.py`), exactly the same "one
deliberate composition point" pattern `atlas/core/infrastructure/api/app.py`
already uses for the Alpha portfolio router itself.

`HoldingContextInput`/`PortfolioContextInput` mirror `AlphaHolding`/
`AlphaPortfolioState`'s own field names without importing them — the
same boundary technique `atlas.decision_engine.contracts.PortfolioHoldingContext`
already uses for an identical reason.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["user", "atlas"]
Language = Literal["sv", "en"]
ChatMode = Literal["generated", "not_configured", "provider_error"]


@dataclass(frozen=True)
class ChatMessage:
    """One turn in the current Discovery session. `role` is `"user"` or
    `"atlas"` — never translated, never altered; `content` is rendered
    or sent verbatim."""

    role: Role
    content: str


@dataclass(frozen=True)
class HoldingContextInput:
    ticker: str
    weight_percent: float
    value_absolute: float | None
    reconciliation_status: str


@dataclass(frozen=True)
class PortfolioContextInput:
    """Only real, currently-recorded Alpha state — never a forecast,
    never a fabricated fundamental. `None` fields are omitted from the
    rendered context rather than padded."""

    holdings: tuple[HoldingContextInput, ...]
    cash_weight_percent: float | None
    has_absolute_values: bool
    concentration_level: str | None


@dataclass(frozen=True)
class ChatOutcome:
    mode: ChatMode
    message: str | None


class ConversationProvider(Protocol):
    """The seam a real LLM adapter implements (`atlas/ai/provider.py`)
    and a test double stands in for — this module never imports a
    specific provider SDK."""

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> str: ...


_SYSTEM_INSTRUCTIONS = """You are Atlas, an investment decision partner having a conversation \
with an individual investor inside the Atlas application's Discovery surface.

Your role:
- Reason about the investor's question rather than merely summarizing it back to them.
- Make uncertainty visible rather than smoothing over it.
- Actively challenge assumptions and the investor's own framing — do not simply agree with \
or mirror what they say.
- Separate assumptions from established facts, and clearly say which is which.
- Distinguish facts you are actually given (in this system prompt or by the investor) from \
claims the investor has merely asserted or pasted in.
- Where the investor's own portfolio context is provided below, consider it — but never \
invent portfolio facts beyond what is given.
- Avoid unnecessary jargon; write like a thoughtful, direct human advisor, not a report.
- Avoid false precision: never state an exact price target, exact valuation multiple, or \
exact percentage return unless you were actually given that number as data.
- Never imply you can execute a trade, monitor the market in real time, or take any action \
on the investor's behalf.
- Never claim knowledge of current prices, today's news, current earnings results, or \
current valuation levels unless that information was explicitly given to you above. If the \
question requires such information and you were not given it, say plainly that you don't \
have it connected right now — this is expected and honest, not a failure.
- When it would genuinely help, suggest a concrete next step — for example, comparing named \
companies, or opening an Investment Case for one specific company already under discussion. \
Never create anything yourself; only suggest it as a question back to the investor.
- Keep your reply conversational, not a rigid template — but where relevant, naturally cover \
what looks attractive, what argues against the idea, portfolio implications if a portfolio \
was provided, what information is missing, and a possible next step.

Respond in {language_name}. Internal reasoning stays in English; only your reply to the \
investor is in {language_name}."""

_LANGUAGE_NAMES: dict[Language, str] = {"sv": "Swedish", "en": "English"}


def build_system_prompt(language: Language, portfolio_context: str | None) -> str:
    """The one place Discovery's behavioral contract (Phase 7) is
    encoded. `portfolio_context`, if given, is appended verbatim as a
    clearly-labeled factual block — never woven into the instructions
    themselves, so the model can never mistake instruction text for
    investor data."""
    prompt = _SYSTEM_INSTRUCTIONS.format(language_name=_LANGUAGE_NAMES[language])
    if portfolio_context:
        prompt += (
            "\n\nThe investor's real, currently recorded Alpha portfolio state "
            "(nothing here is inferred or estimated — treat it as fact, and "
            "nothing beyond it as fact):\n" + portfolio_context
        )
    return prompt


def render_portfolio_context(portfolio: PortfolioContextInput | None) -> str | None:
    """Plain-text summary of only what is actually recorded. Returns
    `None` (never an empty or padded block) when there is nothing real
    to report."""
    if portfolio is None or len(portfolio.holdings) == 0:
        return None

    lines: list[str] = []
    for holding in portfolio.holdings:
        value_part = f", value {holding.value_absolute}" if holding.value_absolute is not None else ""
        lines.append(
            f"- {holding.ticker}: {holding.weight_percent}% of portfolio{value_part} "
            f"(reconciliation: {holding.reconciliation_status})"
        )
    if portfolio.cash_weight_percent is not None:
        lines.append(f"- Cash: {portfolio.cash_weight_percent}%")
    lines.append(
        "- Values are "
        + ("absolute currency amounts and percentages." if portfolio.has_absolute_values else "percentage-only; no absolute portfolio value has been entered.")
    )
    if portfolio.concentration_level is not None:
        lines.append(f"- Concentration level: {portfolio.concentration_level}")
    return "\n".join(lines)


def run_discovery_chat(
    *,
    messages: tuple[ChatMessage, ...],
    language: Language,
    portfolio: PortfolioContextInput | None,
    provider: ConversationProvider | None,
) -> ChatOutcome:
    """The one orchestration function the router calls. Deterministic
    given its inputs except for the provider's own reply — degrades to
    `not_configured` when no provider is injected, and to
    `provider_error` on any provider exception, never raising out of
    this function and never fabricating a reply in either case."""
    if provider is None:
        return ChatOutcome(mode="not_configured", message=None)

    system_prompt = build_system_prompt(language, render_portfolio_context(portfolio))
    try:
        reply = provider.complete(system_prompt=system_prompt, messages=messages)
    except Exception:
        return ChatOutcome(mode="provider_error", message=None)
    return ChatOutcome(mode="generated", message=reply)

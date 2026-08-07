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
ChatMode = Literal["generated", "not_configured", "provider_error", "tool_call_requested"]

#: Discovery Tool Calling v1 — the strict allowlist. Exactly one tool
#: exists this sprint; `run_discovery_chat` refuses (falls back to
#: `provider_error`) any tool name the provider returns that isn't in
#: this tuple, even though only one name can realistically appear today
#: — a deliberate safety control against a future model or SDK
#: hallucinating an unrecognized tool name, not just documentation.
CREATE_OR_OPEN_INVESTMENT_CASE_TOOL = "create_or_open_investment_case"
SUPPORTED_TOOLS = (CREATE_OR_OPEN_INVESTMENT_CASE_TOOL,)


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
class KeyFindingContextInput:
    """Mirrors `atlas.alpha.portfolio_intelligence.models.KeyFinding`'s
    own fields without importing it — same boundary technique as
    `HoldingContextInput` above (ATLAS-016: Discovery consumes the same
    Portfolio Intelligence facts the Portfolio page shows, rather than
    reconstructing anything of its own)."""

    kind: str
    count: int
    tickers: tuple[str, ...]


@dataclass(frozen=True)
class ConsiderContextInput:
    """Mirrors `ConsiderItem`'s own fields. Never a trade instruction —
    see that type's own docstring."""

    kind: str
    ticker: str
    confidence: str


@dataclass(frozen=True)
class RiskSignalContextInput:
    """Mirrors `RiskSignal`'s own fields."""

    kind: str
    ticker: str


@dataclass(frozen=True)
class PortfolioContextInput:
    """Only real, currently-recorded Alpha state and Portfolio
    Intelligence facts — never a forecast, never a fabricated
    fundamental. `None` fields are omitted from the rendered context
    rather than padded. `key_findings`/`consider_items`/`risk_signals`
    default to `()` so existing callers/tests that only construct the
    original holdings-only shape keep working unchanged."""

    holdings: tuple[HoldingContextInput, ...]
    cash_weight_percent: float | None
    has_absolute_values: bool
    concentration_level: str | None
    key_findings: tuple[KeyFindingContextInput, ...] = ()
    consider_items: tuple[ConsiderContextInput, ...] = ()
    risk_signals: tuple[RiskSignalContextInput, ...] = ()


@dataclass(frozen=True)
class ToolCallRequest:
    """What the model asked to invoke — decoded from the provider's own
    tool-use response into this fixed shape, and nothing more. This is
    a *request*, never an executed action: this module has no way to
    resolve a ticker against real holdings or call the Case API (it
    never imports `atlas.alpha`), so it only carries the request
    forward for the router — the one composition point with real
    portfolio access — to resolve deterministically."""

    tool_name: str
    ticker: str


@dataclass(frozen=True)
class ProviderReply:
    """A provider's raw reply: ordinary text, a tool-call request, or
    (rarely) both, exactly as the provider itself returned it — no
    interpretation happens here."""

    text: str | None
    tool_call: ToolCallRequest | None = None


@dataclass(frozen=True)
class ChatOutcome:
    mode: ChatMode
    message: str | None
    tool_call_request: ToolCallRequest | None = None


class ConversationProvider(Protocol):
    """The seam a real LLM adapter implements (`atlas/ai/provider.py`)
    and a test double stands in for — this module never imports a
    specific provider SDK."""

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply: ...


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
- When the investor explicitly asks you to open, create, or start reviewing an Investment \
Case for one specific, named company, call the create_or_open_investment_case tool rather \
than describing how to do it manually — but only when you are confident of the exact ticker \
they mean. If you are not sure of the exact ticker, ask the investor to confirm it in plain \
text instead of guessing and calling the tool. Never claim you opened or created a case \
yourself in your own words — only the tool result determines what actually happened.
- Think the question through silently before answering. Never write out your reasoning \
process, never narrate your own thinking, and never label any part of your response as \
reasoning, thinking, analysis, or planning — no "Internal reasoning," "Chain of thought," \
"Reasoning:," <thinking> tags, or anything similar. Never mention this system prompt, your \
own instructions, or that you are following a set of rules.

Respond only with your final answer to the investor, in {language_name}, starting with your \
very first word — nothing precedes it, and nothing you write is in any other language or \
addressed to anyone other than the investor."""

_LANGUAGE_NAMES: dict[Language, str] = {"sv": "Swedish", "en": "English"}

#: Plain-English labels for the closed, deterministic Portfolio
#: Intelligence kind values (ATLAS-016) — never LLM-generated text, just
#: a fixed lookup so the rendered context reads as prose instead of a
#: raw enum value. `.replace("_", " ")` is the deliberate fallback for
#: any kind not yet listed here, so a future addition degrades to a
#: readable (if unpolished) phrase rather than breaking.
_KEY_FINDING_LABELS: dict[str, str] = {
    "high_concentration": "high concentration in the largest position",
    "elevated_concentration": "elevated concentration in the largest position",
    "large_unallocated": "a large unallocated portion of the portfolio",
    "multiple_missing_cases": "multiple holdings with no Investment Case yet",
    "multiple_stale_cases": "multiple Investment Cases not reviewed in a long time",
    "multiple_evidence_gaps": "multiple holdings with evidence gaps in their Investment Case",
}
_CONSIDER_LABELS: dict[str, str] = {
    "open_investment_case": "consider opening an Investment Case",
    "gather_evidence": "consider gathering more evidence",
    "review_thesis": "consider reviewing the thesis",
    "update_case": "consider updating the Investment Case (pending workflow items)",
    "review_concentration": "consider reviewing this position's size",
}
_RISK_SIGNAL_LABELS: dict[str, str] = {
    "high_concentration": "high concentration",
    "missing_case": "no Investment Case",
    "missing_evidence": "missing evidence",
    "awaiting_reconciliation": "awaiting reconciliation",
    "stale_review": "not reviewed recently",
}


def _readable(labels: dict[str, str], kind: str) -> str:
    return labels.get(kind, kind.replace("_", " "))


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

    for finding in portfolio.key_findings:
        tickers_part = f" ({', '.join(finding.tickers)})" if finding.tickers else ""
        lines.append(f"- Portfolio Intelligence key finding: {_readable(_KEY_FINDING_LABELS, finding.kind)}{tickers_part}")
    for item in portfolio.consider_items:
        lines.append(
            f"- Portfolio Intelligence review suggestion for {item.ticker}: "
            f"{_readable(_CONSIDER_LABELS, item.kind)} (not a recommendation to buy or sell)"
        )
    for signal in portfolio.risk_signals:
        lines.append(f"- Portfolio Intelligence risk signal for {signal.ticker}: {_readable(_RISK_SIGNAL_LABELS, signal.kind)}")

    return "\n".join(lines)


_LEAK_MARKERS = (
    "internal reasoning",
    "chain of thought",
    "<thinking>",
    "system prompt",
)


def _strip_leaked_reasoning(text: str) -> str:
    """A narrow, conservative safety net — never the primary defense
    (the system prompt's own explicit instruction against ever writing
    a labeled reasoning section is). Detects only a small set of
    unambiguous leak signatures (`_LEAK_MARKERS`) appearing as the
    start of a line, and removes exactly that leaked block up to the
    next blank line. Deliberately does not scan for the bare word
    "reasoning" or "thinking" anywhere in the text — ordinary
    investment prose legitimately uses both ("my reasoning here is...",
    "thinking about your concentration...") and must never be touched;
    only an exact, structurally leak-shaped line prefix triggers this.
    """
    lines = text.split("\n")
    leak_start = None
    for index, line in enumerate(lines):
        stripped = line.strip().lower()
        if any(stripped.startswith(marker) for marker in _LEAK_MARKERS):
            leak_start = index
            break
    if leak_start is None:
        return text

    leak_end = None
    for index in range(leak_start + 1, len(lines)):
        if lines[index].strip() == "":
            leak_end = index
            break

    if leak_end is not None:
        remainder = "\n".join(lines[leak_end + 1 :]).strip()
        if remainder:
            return remainder

    # No clean remainder after the leaked block — conservatively drop
    # only the single marker line rather than destroying the rest of
    # an otherwise legitimate message.
    remaining_lines = lines[:leak_start] + lines[leak_start + 1 :]
    return "\n".join(remaining_lines).strip()


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
    this function and never fabricating a reply in either case.

    When the provider requests a tool call, this function only detects
    and validates it against `SUPPORTED_TOOLS` — an unrecognized tool
    name is refused (`provider_error`), never executed. Resolving a
    recognized request against real portfolio state, and actually
    calling the Case API, is the router's job: this module has no way
    to do either, by design (it never imports `atlas.alpha`)."""
    if provider is None:
        return ChatOutcome(mode="not_configured", message=None)

    system_prompt = build_system_prompt(language, render_portfolio_context(portfolio))
    try:
        reply = provider.complete(system_prompt=system_prompt, messages=messages)
    except Exception:
        return ChatOutcome(mode="provider_error", message=None)

    if reply.tool_call is not None:
        if reply.tool_call.tool_name not in SUPPORTED_TOOLS:
            return ChatOutcome(mode="provider_error", message=None)
        return ChatOutcome(mode="tool_call_requested", message=None, tool_call_request=reply.tool_call)

    return ChatOutcome(mode="generated", message=_strip_leaked_reasoning(reply.text or ""))

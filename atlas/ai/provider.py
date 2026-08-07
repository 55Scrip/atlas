"""The one real `ConversationProvider` implementation, and how it is
configured.

Follows this repository's existing, only configuration convention — a
plain `os.environ.get(...)` read (see `atlas/config.py`,
`atlas/core/infrastructure/config/database.py`) — rather than
introducing a new settings abstraction the rest of the app doesn't use.
No secret is ever hardcoded; `ANTHROPIC_API_KEY` unset is a fully
supported, expected state (Discovery Intelligence v1 Phase 5): the
application must still start and Discovery must still degrade cleanly
to its truthful bounded reply.
"""
from __future__ import annotations

import os

from atlas.ai.discovery_chat import (
    CREATE_OR_OPEN_INVESTMENT_CASE_TOOL,
    ChatMessage,
    ProviderReply,
    ToolCallRequest,
)

_DEFAULT_MODEL = "claude-sonnet-4-5"
_MAX_TOKENS = 1024

#: The one tool this sprint exposes to the model. The name is imported
#: from `discovery_chat`, not redeclared here, so there is exactly one
#: place that name is spelled — the router's allowlist check
#: (`SUPPORTED_TOOLS`) and this schema can never silently drift apart.
_TOOLS = [
    {
        "name": CREATE_OR_OPEN_INVESTMENT_CASE_TOOL,
        "description": (
            "Create a new Investment Case for a company the investor already holds in "
            "their Alpha portfolio, or open the existing one if one is already linked. "
            "Only call this when the investor explicitly asks to open, create, or start "
            "reviewing an Investment Case for one specific, named company or ticker. "
            "Never call this for a general question, a hypothetical, a company comparison, "
            "or a company not clearly named by the investor. If you are not confident of "
            "the exact ticker, ask the investor to confirm it in plain text instead of "
            "calling this tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The exact ticker or company name as the investor stated it "
                        "(e.g. META, AAPL, TSM). Never guess or infer a ticker the "
                        "investor did not themselves name."
                    ),
                }
            },
            "required": ["ticker"],
        },
    }
]


class AnthropicProvider:
    """Thin adapter around the Anthropic SDK. Import of `anthropic` is
    deferred to `__init__` rather than module scope, so importing this
    module (and therefore the whole `atlas.ai` package) never requires
    the SDK to be installed — only actually configuring a provider
    does."""

    def __init__(self, *, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> ProviderReply:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            system=system_prompt,
            tools=_TOOLS,
            messages=[
                {"role": "user" if m.role == "user" else "assistant", "content": m.content}
                for m in messages
            ],
        )

        text_parts = [block.text for block in response.content if block.type == "text"]
        text = "".join(text_parts) or None

        tool_call: ToolCallRequest | None = None
        for block in response.content:
            if block.type != "tool_use":
                continue
            ticker = block.input.get("ticker") if isinstance(block.input, dict) else None
            # A malformed tool call (missing/empty/non-string ticker) is
            # never executed — fall back to treating this as if no tool
            # call happened rather than passing a bad request onward.
            if isinstance(ticker, str) and ticker.strip() != "":
                tool_call = ToolCallRequest(tool_name=block.name, ticker=ticker.strip())
            break

        return ProviderReply(text=text, tool_call=tool_call)


def get_configured_provider() -> AnthropicProvider | None:
    """`None` means "no provider configured" — a normal, expected
    outcome this app must run correctly under, not an error."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    model = os.environ.get("ATLAS_DISCOVERY_MODEL", _DEFAULT_MODEL)
    return AnthropicProvider(api_key=api_key, model=model)

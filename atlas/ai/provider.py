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

from atlas.ai.discovery_chat import ChatMessage

_DEFAULT_MODEL = "claude-sonnet-4-5"
_MAX_TOKENS = 1024


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

    def complete(self, *, system_prompt: str, messages: tuple[ChatMessage, ...]) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            system=system_prompt,
            messages=[
                {"role": "user" if m.role == "user" else "assistant", "content": m.content}
                for m in messages
            ],
        )
        return "".join(block.text for block in response.content if block.type == "text")


def get_configured_provider() -> AnthropicProvider | None:
    """`None` means "no provider configured" — a normal, expected
    outcome this app must run correctly under, not an error."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    model = os.environ.get("ATLAS_DISCOVERY_MODEL", _DEFAULT_MODEL)
    return AnthropicProvider(api_key=api_key, model=model)

"""HTTP request/response schemas for the Discovery chat API.

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
reused here for consistency — a read-only import from `atlas.core`, not
a modification to it, matching `atlas/alpha/portfolio/api/schemas.py`'s
own precedent for a sibling provisional package.
"""
from __future__ import annotations

from typing import Literal

from atlas.core.infrastructure.api.serialization import CamelModel


class ChatMessageBody(CamelModel):
    role: Literal["user", "atlas"]
    content: str


class DiscoveryChatRequest(CamelModel):
    messages: list[ChatMessageBody]
    language: Literal["sv", "en"]
    # ATLAS-017: when the investor is discussing one specific Investment
    # Case (e.g. arrived here via a "Discuss in Discovery" link from that
    # Case's own page), the router resolves this into the exact same
    # `CaseIntelligenceReport` the Investment Case page shows -- never a
    # second reconstruction. Optional and additive: existing callers that
    # never send it are unaffected.
    case_id: str | None = None


class ToolResultBody(CamelModel):
    """The one tool result shape this sprint supports — always the
    router's own deterministic finding, never model-authored text. The
    frontend renders `outcome` through its own translated copy, never
    through anything the model wrote."""

    tool: Literal["create_or_open_investment_case"]
    outcome: Literal["opened", "created", "unresolved", "failed"]
    ticker: str
    case_id: str | None = None


class DiscoveryChatResponse(CamelModel):
    message: str | None
    mode: Literal["generated", "not_configured", "provider_error", "tool_call"]
    tool_result: ToolResultBody | None = None

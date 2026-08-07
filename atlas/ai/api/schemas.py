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


class DiscoveryChatResponse(CamelModel):
    message: str | None
    mode: Literal["generated", "not_configured", "provider_error"]

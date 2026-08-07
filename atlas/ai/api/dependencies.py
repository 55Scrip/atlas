"""Composition wiring for the Discovery chat API.

`get_discovery_provider` exists as its own dependency function — rather
than calling `get_configured_provider()` inline in the router — purely
so tests can override it with a fake provider via
`app.dependency_overrides`, the same pattern
`tests/unit/infrastructure/api/alpha_portfolio/test_router.py` already
uses for `get_decision_engine`. No real, paid provider call is ever
required for a test to pass.
"""
from __future__ import annotations

from atlas.ai.discovery_chat import ConversationProvider
from atlas.ai.provider import get_configured_provider


def get_discovery_provider() -> ConversationProvider | None:
    return get_configured_provider()

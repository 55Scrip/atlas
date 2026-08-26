"""HTTP request/response schema for the Daily Brief View State API.

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
matching every other Alpha schema module.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.daily_brief_view_state.models import DailyBriefViewState
from atlas.core.infrastructure.api.serialization import CamelModel


class DailyBriefViewStateView(CamelModel):
    last_viewed_at: datetime | None

    @staticmethod
    def from_domain(state: DailyBriefViewState) -> "DailyBriefViewStateView":
        return DailyBriefViewStateView(last_viewed_at=state.last_viewed_at)

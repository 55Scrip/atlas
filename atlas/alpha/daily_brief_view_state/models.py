"""The one domain object this package owns. See this package's own
`__init__.py` for why nothing else exists here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

__all__ = ["DailyBriefViewState"]


@dataclass(frozen=True)
class DailyBriefViewState:
    user_id: str
    last_viewed_at: datetime | None
    """`None` only when this user has never successfully loaded the
    Daily Brief before -- the real, honest "first visit" case, never a
    fabricated past timestamp. A first visit's own "since you were
    here" window is therefore unbounded: every existing agenda item is
    in scope, exactly as Phase 4's own rule requires."""

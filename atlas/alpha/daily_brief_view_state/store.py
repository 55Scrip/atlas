"""Persistence for Since You Were Here's one piece of new state.

`mark_viewed` is an upsert keyed by `user_id` (the table's own primary
key) -- the same pattern `AlphaWatchlistStore.add` already establishes
for a table with no soft-delete concept to worry about.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Engine

from atlas.alpha.daily_brief_view_state.models import DailyBriefViewState
from atlas.alpha.daily_brief_view_state.table import daily_brief_view_state_table


class DailyBriefViewStateStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get(self, user_id: str) -> DailyBriefViewState:
        """Never raises for an unknown `user_id` -- a user who has
        never viewed the Daily Brief before is a real, expected state
        (`last_viewed_at=None`), not an error."""
        with self._engine.begin() as connection:
            row = connection.execute(
                select(daily_brief_view_state_table.c.last_viewed_at).where(
                    daily_brief_view_state_table.c.user_id == user_id
                )
            ).first()
        last_viewed_at = datetime.fromisoformat(row[0]) if row is not None and row[0] is not None else None
        return DailyBriefViewState(user_id=user_id, last_viewed_at=last_viewed_at)

    def mark_viewed(self, user_id: str, *, now: datetime | None = None) -> DailyBriefViewState:
        """Sets `last_viewed_at` to `now` (defaulting to the real wall
        clock) -- an upsert, since the first call for a given
        `user_id` has no existing row yet."""
        viewed_at = now or datetime.now(timezone.utc)
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(daily_brief_view_state_table.c.user_id).where(
                    daily_brief_view_state_table.c.user_id == user_id
                )
            ).first()
            if existing is None:
                connection.execute(
                    insert(daily_brief_view_state_table).values(
                        user_id=user_id, last_viewed_at=viewed_at.isoformat()
                    )
                )
            else:
                connection.execute(
                    update(daily_brief_view_state_table)
                    .where(daily_brief_view_state_table.c.user_id == user_id)
                    .values(last_viewed_at=viewed_at.isoformat())
                )
        return DailyBriefViewState(user_id=user_id, last_viewed_at=viewed_at)

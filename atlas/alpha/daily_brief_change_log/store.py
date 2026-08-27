"""Persistence for Daily Brief 2.0's change log.

`record_if_new` is the one write path: given the eligible facts this
build of the agenda just observed (`eligibility.py::extract_eligible_
changes`), insert a durable row for each one not already present under
its own natural key. This is what makes a real transition survive past
the single `build_agenda()` call that would otherwise be its only
chance to be seen (see this package's own `__init__.py`).

`list_recent`/`mark_seen` are the two read/update paths Daily Brief 2.0
needs (Phase 8/9): a NEW entry has `seen_at is None`; a SEEN entry has
`seen_at` set but stays visible; an entry older than `archive_after`
(Phase 8's own "24-72 hours depending on the existing product
architecture" -- 72 hours here, the wider end of that range, since
this codebase's only other staleness precedent,
`VERY_OLD_CASE_THRESHOLD_DAYS`, already favors giving real signals room
before treating them as gone) is excluded from `list_recent` entirely,
though the row itself is never deleted -- it remains real, queryable
history for a future Weekly/Monthly Review (Phase 20), not a second
consumer feed.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, insert, select, update
from sqlalchemy.engine import Engine

from atlas.alpha.daily_brief_change_log.eligibility import EligibleChange
from atlas.alpha.daily_brief_change_log.models import ChangeLogEntry
from atlas.alpha.daily_brief_change_log.table import daily_brief_change_log_table

DEFAULT_ARCHIVE_AFTER = timedelta(hours=72)


def _row_to_entry(row) -> ChangeLogEntry:
    return ChangeLogEntry(
        id=row.id,
        user_id=row.user_id,
        ticker=row.ticker,
        case_id=row.case_id,
        reason_code=row.reason_code,
        value=row.value,
        secondary_value=row.secondary_value,
        label=row.label,
        headline=row.headline,
        priority_rank=row.priority_rank,
        detected_at=datetime.fromisoformat(row.detected_at),
        seen_at=datetime.fromisoformat(row.seen_at) if row.seen_at is not None else None,
    )


class DailyBriefChangeLogStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record_if_new(
        self, user_id: str, changes: tuple[EligibleChange, ...], *, now: datetime | None = None
    ) -> tuple[ChangeLogEntry, ...]:
        """Idempotent: a change already logged under its own natural
        key (`user_id`, `ticker`, `reason_code`, `value`,
        `secondary_value`) is left untouched, not re-inserted and not
        re-timestamped -- `detected_at` always reflects the first time
        Atlas told the user about it, never the most recent read.
        Returns only the entries that were genuinely new this call."""
        detected_at = now or datetime.now(timezone.utc)
        newly_recorded: list[ChangeLogEntry] = []
        with self._engine.begin() as connection:
            for change in changes:
                existing = connection.execute(
                    select(daily_brief_change_log_table.c.id).where(
                        and_(
                            daily_brief_change_log_table.c.user_id == user_id,
                            daily_brief_change_log_table.c.ticker == change.ticker,
                            daily_brief_change_log_table.c.reason_code == change.reason_code,
                            daily_brief_change_log_table.c.value == change.value,
                            daily_brief_change_log_table.c.secondary_value == change.secondary_value,
                        )
                    )
                ).first()
                if existing is not None:
                    continue
                entry_id = str(uuid.uuid4())
                connection.execute(
                    insert(daily_brief_change_log_table).values(
                        id=entry_id,
                        user_id=user_id,
                        ticker=change.ticker,
                        case_id=change.case_id,
                        reason_code=change.reason_code,
                        value=change.value,
                        secondary_value=change.secondary_value,
                        label=change.label,
                        headline=change.headline,
                        detected_at=detected_at.isoformat(),
                        seen_at=None,
                        priority_rank=change.priority_rank,
                    )
                )
                newly_recorded.append(
                    ChangeLogEntry(
                        id=entry_id,
                        user_id=user_id,
                        ticker=change.ticker,
                        case_id=change.case_id,
                        reason_code=change.reason_code,
                        value=change.value,
                        secondary_value=change.secondary_value,
                        label=change.label,
                        headline=change.headline,
                        priority_rank=change.priority_rank,
                        detected_at=detected_at,
                        seen_at=None,
                    )
                )
        return tuple(newly_recorded)

    def list_recent(
        self, user_id: str, *, now: datetime | None = None, archive_after: timedelta = DEFAULT_ARCHIVE_AFTER
    ) -> tuple[ChangeLogEntry, ...]:
        """Every still-live entry for this user -- `detected_at >= now
        - archive_after`, oldest excluded entirely (Phase 8's ARCHIVED
        state), never soft-hidden client-side. Ordered oldest-first;
        callers that want "most important first" use each entry's own
        real reason code, never a client-invented recency guess (see
        `synthesis.py`)."""
        cutoff = (now or datetime.now(timezone.utc)) - archive_after
        with self._engine.begin() as connection:
            rows = connection.execute(
                select(daily_brief_change_log_table)
                .where(
                    and_(
                        daily_brief_change_log_table.c.user_id == user_id,
                        daily_brief_change_log_table.c.detected_at >= cutoff.isoformat(),
                    )
                )
                .order_by(daily_brief_change_log_table.c.detected_at.asc())
            ).all()
        return tuple(_row_to_entry(row) for row in rows)

    def mark_seen(self, user_id: str, entry_ids: tuple[str, ...], *, now: datetime | None = None) -> None:
        """Sets `seen_at` only for entries that don't already have one
        -- an entry already seen keeps its own original `seen_at`,
        never bumped forward by a later view (Phase 8's own "do not
        confuse seen with resolved": re-viewing an already-seen change
        must not reset anything)."""
        if not entry_ids:
            return
        seen_at = now or datetime.now(timezone.utc)
        with self._engine.begin() as connection:
            connection.execute(
                update(daily_brief_change_log_table)
                .where(
                    and_(
                        daily_brief_change_log_table.c.user_id == user_id,
                        daily_brief_change_log_table.c.id.in_(entry_ids),
                        daily_brief_change_log_table.c.seen_at.is_(None),
                    )
                )
                .values(seen_at=seen_at.isoformat())
            )

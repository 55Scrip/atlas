"""Daily Brief RC-3, Phase 3 -- per-case baseline.

The problem: a persistent-finding-shaped fact (Case Condition,
Assumption Status, Business Quality, Management Credibility -- see
`eligibility.py`'s own `BASELINE_SENSITIVE_CODES`) has no real
"previous" semantics. It fires whenever the current case's own state
satisfies it, whether that became true five minutes ago or has been
true since the case's very first synthesis. A brand-new company added
to an already-established portfolio could therefore generate one false
"new" Daily Brief change on its own first analysis pass, purely because
Atlas looked at it for the first time -- not because anything changed.

The fix does not fabricate a "previous state" for that case (explicitly
forbidden by this sprint's own brief). Instead it tracks, honestly and
minimally, the one real fact this codebase already has: whether Daily
Brief has ever observed this `case_id` before. `mark_seen_and_get_new`
is called once per agenda build with every `case_id` present in that
pass (not only the ones with an eligible fact -- a case with nothing
eligible still needs its baseline established, or a later persistent
finding for it would be wrongly treated as non-baseline). Whichever of
those case_ids were NOT already known becomes this pass's baseline set;
`store.py::record_if_new` uses it to mark baseline-sensitive facts on
those cases as `is_baseline=True` (recorded, but never surfaced) rather
than as a live NEW change.

A real transition (Investment Decision, Recommendation Conviction,
Portfolio Decision, ...) needs no such gate: it cannot fire on a case's
own first synthesis by construction (the Decision Layer's own
`previous is None` check) -- it only ever reflects a real,
already-computed previous->current move, baseline case or not.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table, and_, insert, select
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

daily_brief_case_baseline_table = Table(
    "daily_brief_case_baseline",
    metadata,
    Column("user_id", String, primary_key=True),
    Column("case_id", String, primary_key=True),
    # ISO-8601 string -- when this case was first observed by the
    # change log. Informational only; nothing currently reads it back,
    # kept for the same honest-audit-trail reason every other
    # first-seen/detected_at column in this package is kept.
    Column("first_seen_at", String, nullable=False),
)


def create_daily_brief_case_baseline_table(engine: Engine) -> None:
    sync_table_schema(engine, daily_brief_case_baseline_table)


class CaseBaselineStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def mark_seen_and_get_new(self, user_id: str, case_ids: frozenset[str], *, now) -> frozenset[str]:
        """Returns the subset of `case_ids` never seen before this call
        for this user, then records every id in `case_ids` (the newly
        seen ones and the already-known ones alike) as seen -- so the
        very next call, even later the same day, no longer treats any
        of them as new. Idempotent and safe to call with an empty set."""
        if not case_ids:
            return frozenset()
        with self._engine.begin() as connection:
            existing_rows = connection.execute(
                select(daily_brief_case_baseline_table.c.case_id).where(
                    and_(
                        daily_brief_case_baseline_table.c.user_id == user_id,
                        daily_brief_case_baseline_table.c.case_id.in_(case_ids),
                    )
                )
            ).all()
            known_case_ids = {row.case_id for row in existing_rows}
            newly_seen = frozenset(case_ids) - known_case_ids
            for case_id in newly_seen:
                connection.execute(
                    insert(daily_brief_case_baseline_table).values(
                        user_id=user_id, case_id=case_id, first_seen_at=now.isoformat()
                    )
                )
        return newly_seen

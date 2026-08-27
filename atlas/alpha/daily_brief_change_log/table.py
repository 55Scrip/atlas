"""SQL schema for Daily Brief 2.0's one piece of new durable state.

One row per (user_id, ticker, reason_code, value, secondary_value)
tuple ever observed -- normalized, not a JSON blob, since the read
path (`store.py::list_recent`) needs to filter/order/group by these
columns, not just replay an opaque history. `id` is still the real
primary key (server-generated) so a later row with the same natural
key but a different `label`/`headline` -- the same transition observed
again with a freshly-worded sentence -- can be recognized as a dup by
`record_if_new`'s own lookup without needing the natural key itself to
be the primary key.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

daily_brief_change_log_table = Table(
    "daily_brief_change_log",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("ticker", String, nullable=False),
    Column("case_id", String, nullable=True),
    Column("reason_code", String, nullable=False),
    Column("value", String, nullable=True),
    Column("secondary_value", String, nullable=True),
    Column("label", String, nullable=True),
    Column("headline", String, nullable=False),
    # ISO-8601 strings, the same convention `daily_brief_view_state`
    # already uses for its own `last_viewed_at`.
    Column("detected_at", String, nullable=False),
    # NULL means NEW (Phase 8) -- an honest absence, never a
    # fabricated past timestamp standing in for "not yet seen."
    Column("seen_at", String, nullable=True),
    # Real, already-computed data used for ordering/materiality at
    # read time -- never re-derived from `value` string-matching.
    Column("priority_rank", Integer, nullable=False),
    # RC-3, Phase 3 (Per-Case Baseline). True only for a persistent-
    # finding-shaped fact (case_condition_status/assumption_status/
    # business_quality/management_credibility -- see `eligibility.py`'s
    # own `BASELINE_SENSITIVE_CODES`) recorded on the first pass this
    # case was ever observed by the change log. Occupies its natural
    # key (so an unchanged repeat of the same fact is never re-surfaced
    # later) but is excluded from `list_recent` -- the row is real, only
    # its visibility as a "change" is suppressed. Real transitions
    # (Investment Decision, Recommendation Conviction, Portfolio
    # Decision, ...) are never marked baseline: they cannot fire on a
    # case's own first synthesis by construction (the engine's own
    # `previous is None` check), so a transition recorded here always
    # reflects a real, already-computed previous->current move.
    #
    # Nullable, matching `seen_at`'s own precedent and this codebase's
    # `sync_table_schema` discipline (a new NOT NULL column on an
    # already-existing table would raise `IncompatibleSchemaError`
    # rather than fabricate a default for pre-existing rows) -- NULL
    # and `False` are treated identically everywhere this column is
    # read (`store.py::list_recent`).
    Column("is_baseline", Boolean, nullable=True),
)


def create_daily_brief_change_log_table(engine: Engine) -> None:
    sync_table_schema(engine, daily_brief_change_log_table)

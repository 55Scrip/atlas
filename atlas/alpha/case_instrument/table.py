"""SQL schema for the Case -> operative-instrument binding.

Own `MetaData`, no SQL ForeignKey, `sync_table_schema` for create-or-
safely-add -- the same convention every other Alpha table module
follows (`atlas/alpha/watchlist/table.py`, `atlas/alpha/canonical_security
/table.py`). No foreign key to `cases` means this table can never
cascade into Core Case, Decision, Evidence or Company data.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

case_instrument_binding_table = Table(
    "case_instrument_bindings",
    metadata,
    # One binding per Case, enforced by the database rather than by
    # convention: a Case is about exactly one instrument.
    Column("case_id", String, primary_key=True),
    # Indexed, not unique. The current corpus holds exactly one Case
    # per operative security and `bind` enforces that, but a UNIQUE
    # constraint here would also forbid the historical thesis-episode
    # shape (several Cases over time for one company) that Atlas has
    # not decided against. The invariant is enforced where it can be
    # explained and raised on; the schema stays permissive.
    Column("instrument_key", String, nullable=False, index=True),
    Column("bound_at", String, nullable=False),
    # The seam to `atlas.alpha.canonical_security`. Nullable and unset
    # today -- see this package's `__init__` for why.
    Column("canonical_security_id", String, nullable=True, index=True),
)


def create_case_instrument_binding_table(engine: Engine) -> None:
    sync_table_schema(engine, case_instrument_binding_table)

"""SQL schema for Resolution shadow persistence -- Sprint N Phase 9/10.

Own `MetaData`, no SQL ForeignKey, matching every other Alpha
persistence table's established convention (see
`atlas.alpha.canonical_security.table`'s own docstring for the same
rationale, restated for this package). Two tables: one row per
resolution attempt (`resolution_records_table`), and one row per
candidate that attempt considered (`resolution_evidence_table`) --
never just the winner. A candidate's *entire* field set is persisted on
its evidence row (not only the fields that happened to matter for this
resolution), so a stored resolution can be fully reconstructed and
replayed (`replay.py`) without needing anything beyond what this table
already holds.

Shadow mode only: nothing outside this package (and its own tests)
reads from these tables yet -- there is no consumer, by design (Sprint
N's own scope: "shadow mode only... nothing downstream should consume
these records yet").
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

resolution_records_table = Table(
    "canonical_security_resolution_records",
    metadata,
    Column("id", String, primary_key=True),
    Column("resolution_version", String, nullable=False),
    Column("investor_company_text", String, nullable=True),
    Column("investor_ticker", String, nullable=False, index=True),
    Column("normalized_company_text", String, nullable=False),
    Column("normalized_ticker", String, nullable=False, index=True),
    Column("outcome", String, nullable=False, index=True),
    Column("existing_canonical_security_id", String, nullable=True, index=True),
    Column("resulting_canonical_security_id", String, nullable=True, index=True),
    Column("resolved_at", String, nullable=False),
)

resolution_evidence_table = Table(
    "canonical_security_resolution_evidence",
    metadata,
    Column("id", String, primary_key=True),
    Column("resolution_record_id", String, nullable=False, index=True),
    Column("sequence", String, nullable=False),  # zero-padded index, preserves deterministic candidate order on read
    Column("provider_name", String, nullable=False),
    Column("symbol", String, nullable=False),
    Column("provider_security_id", String, nullable=True),
    Column("exchange_mic", String, nullable=True),
    Column("exchange_display_name", String, nullable=True),
    Column("country", String, nullable=True),
    Column("currency", String, nullable=True),
    Column("company_name", String, nullable=True),
    Column("security_type", String, nullable=True),
    Column("listing_relationship", String, nullable=True),
    Column("isin", String, nullable=True),
    Column("figi", String, nullable=True),
    Column("cusip", String, nullable=True),
    Column("sedol", String, nullable=True),
    Column("provider_confidence", String, nullable=True),
    Column("raw_metadata_json", String, nullable=False),
    Column("confidence", String, nullable=False),
    Column("accepted", Boolean, nullable=False),
    Column("comparisons_json", String, nullable=False),
)


def create_resolution_tables(engine: Engine) -> None:
    sync_table_schema(engine, resolution_records_table)
    sync_table_schema(engine, resolution_evidence_table)

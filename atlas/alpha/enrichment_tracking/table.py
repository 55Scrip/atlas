"""SQL schema for enrichment progress rows.

One row per (batch_id, ticker) -- the composite primary key -- so a
batch's whole progress is one `WHERE batch_id = ?` query, and a
duplicate ticker within one batch (harmless per `enrich_holdings`'s own
docstring) simply overwrites its own row rather than producing two.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

enrichment_progress_table = Table(
    "enrichment_progress",
    metadata,
    Column("batch_id", String, primary_key=True),
    Column("ticker", String, primary_key=True),
    Column("company_name", String, nullable=True),
    Column("status", String, nullable=False),
    Column("updated_at", String, nullable=False),
    # The order tickers were queued in (weight-prioritized) -- explicit,
    # since SQL row order is never guaranteed without one.
    Column("sequence", Integer, nullable=False),
)


def create_enrichment_progress_table(engine: Engine) -> None:
    sync_table_schema(engine, enrichment_progress_table)

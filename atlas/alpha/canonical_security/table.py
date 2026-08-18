"""SQL schema for the Canonical Security Foundation.

Own `MetaData`, no SQL ForeignKey -- matching every other Alpha
persistence table's convention (see `atlas.alpha.security_confirmation.
table`'s own docstring, and `atlas.core.infrastructure.persistence.
decision.table`, which established this convention first). Four tables,
one per Sprint L Phase 11's design: the aggregate root, and three
append-only child collections (listings, provider mappings,
identifiers), each keyed back to `canonical_security_id` as a plain
indexed string column, never a foreign key.

This module is inert: nothing outside `repository.py` and this
package's own tests calls `create_canonical_security_tables`. No
existing table, migration, or startup path is touched by adding this
module (Sprint M's own "gain a complete subsystem without changing
existing runtime behaviour").
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

canonical_securities_table = Table(
    "canonical_securities",
    metadata,
    Column("id", String, primary_key=True),
    Column("canonical_company_name", String, nullable=False),
    Column("native_ticker", String, nullable=False, index=True),
    Column("primary_exchange_mic", String, nullable=False),
    Column("country", String, nullable=False),
    Column("trading_currency", String, nullable=False),
    Column("resolution_status", String, nullable=False, index=True),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
)

canonical_security_listings_table = Table(
    "canonical_security_listings",
    metadata,
    Column("id", String, primary_key=True),
    Column("canonical_security_id", String, nullable=False, index=True),
    Column("ticker", String, nullable=False),
    Column("exchange_mic", String, nullable=False),
    Column("currency", String, nullable=False),
    Column("relationship", String, nullable=False),
    Column("security_type", String, nullable=False),
    Column("provider_symbol", String, nullable=True),
)

canonical_security_provider_mappings_table = Table(
    "canonical_security_provider_mappings",
    metadata,
    Column("id", String, primary_key=True),
    Column("canonical_security_id", String, nullable=False, index=True),
    Column("provider_name", String, nullable=False),
    Column("provider_ticker", String, nullable=False),
    Column("provider_security_id", String, nullable=True),
    Column("provider_exchange_code", String, nullable=True),
    Column("confidence", String, nullable=False),
    Column("verification_status", String, nullable=False),
    Column("mapped_at", String, nullable=False),
    Column("verified_at", String, nullable=True),
)

canonical_security_identifiers_table = Table(
    "canonical_security_identifiers",
    metadata,
    Column("id", String, primary_key=True),
    Column("canonical_security_id", String, nullable=False, index=True),
    Column("identifier_type", String, nullable=False),
    Column("value", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_canonical_security_tables(engine: Engine) -> None:
    sync_table_schema(engine, canonical_securities_table)
    sync_table_schema(engine, canonical_security_listings_table)
    sync_table_schema(engine, canonical_security_provider_mappings_table)
    sync_table_schema(engine, canonical_security_identifiers_table)

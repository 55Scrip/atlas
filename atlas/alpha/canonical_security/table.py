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
    # Issuer Identity Foundation. Nullable by necessity: `sync_table_schema`
    # only auto-adds nullable columns -- a NOT NULL column here would make
    # the existing development database refuse to migrate rather than
    # fabricate a value. The backfill fills every existing row.
    Column("issuer_id", String, nullable=True, index=True),
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
    Column("share_class", String, nullable=True),
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


canonical_issuers_table = Table(
    "canonical_issuers",
    metadata,
    Column("id", String, primary_key=True),
    Column("legal_name", String, nullable=False),
    Column("jurisdiction", String, nullable=True),
    Column("created_at", String, nullable=False),
)

canonical_issuer_identifiers_table = Table(
    "canonical_issuer_identifiers",
    metadata,
    Column("issuer_id", String, primary_key=True),
    Column("identifier_type", String, primary_key=True),
    Column("value", String, primary_key=True),
    Column("recorded_at", String, nullable=False),
)


#: Provider symbol routing (2026-09-04). Deliberately NOT hung off a
#: CanonicalSecurity, unlike `canonical_security_provider_mappings`.
#:
#: The case that forced this: Berkshire Class B had no CanonicalSecurity
#: precisely *because* Alpha Vantage could not be asked about `BRK.B`,
#: so a route recorded against a security could never have been created
#: -- the security cannot exist until the route does. A ProviderMapping
#: remains the right home for a provider's claim about a security that
#: already exists; this table is the bootstrap that gets there, keyed by
#: canonical ticker alone.
#:
#: Holds stored facts only. Nothing derives one spelling from another.
provider_symbol_routes_table = Table(
    "provider_symbol_routes",
    metadata,
    Column("provider_name", String, primary_key=True),
    Column("canonical_ticker", String, primary_key=True),
    Column("provider_symbol", String, nullable=False),
    Column("evidence", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_canonical_security_tables(engine: Engine) -> None:
    # Issuer first: securities reference it. Both new tables are created
    # fresh, and the two added columns below are nullable so
    # `sync_table_schema` can ALTER them into the existing development
    # database automatically -- a NOT NULL column would make it refuse
    # rather than fabricate a value (see that module's own docstring).
    sync_table_schema(engine, canonical_issuers_table)
    sync_table_schema(engine, canonical_issuer_identifiers_table)
    sync_table_schema(engine, canonical_securities_table)
    sync_table_schema(engine, canonical_security_listings_table)
    sync_table_schema(engine, canonical_security_provider_mappings_table)
    sync_table_schema(engine, canonical_security_identifiers_table)
    sync_table_schema(engine, provider_symbol_routes_table)

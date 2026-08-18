"""SQLAlchemy-backed store for the Canonical Security Foundation --
Sprint M Phase 7's `CanonicalSecurityRepository`.

`save` persists the *entire* current aggregate state in one transaction:
the root row is inserted or updated (whichever applies), and every child
collection (listings, provider mappings, identifiers) is fully replaced
-- delete-then-reinsert -- rather than diffed. This is a deliberate
simplification appropriate to an inert foundation with no caller yet:
nothing today calls `save` more than once for the same aggregate, so
there is no lost-update risk to guard against, and a diffing
upsert-per-child-row strategy would be speculative complexity for a
capability nothing yet exercises. A future service layer that saves
incrementally (e.g. "just add one listing") can still call `save` with
the full, already-updated aggregate `add_listing` returns -- the
aggregate's own pure methods (`models.py`) already produce that full,
consistent state; this repository does not need its own partial-update
API to support that usage.

No existing code calls this repository (Sprint M Phase 12's own
integration-safety requirement) -- see `tests/unit/alpha/canonical_
security/test_integration_safety.py`.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine

from atlas.alpha.canonical_security.models import (
    CanonicalSecurity,
    ListingRef,
    ProviderMapping,
    SecurityIdentifier,
)
from atlas.alpha.canonical_security.table import (
    canonical_security_identifiers_table,
    canonical_security_listings_table,
    canonical_security_provider_mappings_table,
    canonical_securities_table,
)
from atlas.alpha.canonical_security.value_objects import (
    CanonicalSecurityId,
    MicCode,
    TradingCurrency,
)

__all__ = ["SqlAlchemyCanonicalSecurityRepository"]


class SqlAlchemyCanonicalSecurityRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, security: CanonicalSecurity) -> None:
        security_id = str(security.id)
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(canonical_securities_table.c.id).where(
                    canonical_securities_table.c.id == security_id
                )
            ).first()
            root_values = _root_to_row(security)
            if existing is None:
                connection.execute(insert(canonical_securities_table).values(**root_values))
            else:
                connection.execute(
                    update(canonical_securities_table)
                    .where(canonical_securities_table.c.id == security_id)
                    .values(**root_values)
                )

            connection.execute(
                delete(canonical_security_listings_table).where(
                    canonical_security_listings_table.c.canonical_security_id == security_id
                )
            )
            for listing in security.listings:
                connection.execute(
                    insert(canonical_security_listings_table).values(
                        **_listing_to_row(security_id, listing)
                    )
                )

            connection.execute(
                delete(canonical_security_provider_mappings_table).where(
                    canonical_security_provider_mappings_table.c.canonical_security_id == security_id
                )
            )
            for mapping in security.provider_mappings:
                connection.execute(
                    insert(canonical_security_provider_mappings_table).values(
                        **_mapping_to_row(security_id, mapping)
                    )
                )

            connection.execute(
                delete(canonical_security_identifiers_table).where(
                    canonical_security_identifiers_table.c.canonical_security_id == security_id
                )
            )
            for identifier in security.identifiers:
                connection.execute(
                    insert(canonical_security_identifiers_table).values(
                        **_identifier_to_row(security_id, identifier)
                    )
                )

    def load(self, security_id: str) -> CanonicalSecurity | None:
        with self._engine.connect() as connection:
            root_row = (
                connection.execute(
                    select(canonical_securities_table).where(
                        canonical_securities_table.c.id == security_id
                    )
                )
                .mappings()
                .first()
            )
            if root_row is None:
                return None
            return self._assemble(connection, root_row)

    def exists(self, security_id: str) -> bool:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(canonical_securities_table.c.id).where(
                    canonical_securities_table.c.id == security_id
                )
            ).first()
        return row is not None

    def find_by_provider_mapping(self, provider_name: str, provider_ticker: str) -> CanonicalSecurity | None:
        with self._engine.connect() as connection:
            mapping_row = (
                connection.execute(
                    select(canonical_security_provider_mappings_table.c.canonical_security_id)
                    .where(canonical_security_provider_mappings_table.c.provider_name == provider_name)
                    .where(canonical_security_provider_mappings_table.c.provider_ticker == provider_ticker)
                )
                .mappings()
                .first()
            )
            if mapping_row is None:
                return None
            root_row = (
                connection.execute(
                    select(canonical_securities_table).where(
                        canonical_securities_table.c.id == mapping_row["canonical_security_id"]
                    )
                )
                .mappings()
                .first()
            )
            if root_row is None:
                return None
            return self._assemble(connection, root_row)

    def find_by_identifier(self, identifier_type: str, value: str) -> CanonicalSecurity | None:
        with self._engine.connect() as connection:
            identifier_row = (
                connection.execute(
                    select(canonical_security_identifiers_table.c.canonical_security_id)
                    .where(canonical_security_identifiers_table.c.identifier_type == identifier_type)
                    .where(canonical_security_identifiers_table.c.value == value)
                )
                .mappings()
                .first()
            )
            if identifier_row is None:
                return None
            root_row = (
                connection.execute(
                    select(canonical_securities_table).where(
                        canonical_securities_table.c.id == identifier_row["canonical_security_id"]
                    )
                )
                .mappings()
                .first()
            )
            if root_row is None:
                return None
            return self._assemble(connection, root_row)

    def _assemble(self, connection: Any, root_row: Mapping[str, Any]) -> CanonicalSecurity:
        security_id = root_row["id"]
        listing_rows = (
            connection.execute(
                select(canonical_security_listings_table).where(
                    canonical_security_listings_table.c.canonical_security_id == security_id
                )
            )
            .mappings()
            .all()
        )
        mapping_rows = (
            connection.execute(
                select(canonical_security_provider_mappings_table).where(
                    canonical_security_provider_mappings_table.c.canonical_security_id == security_id
                )
            )
            .mappings()
            .all()
        )
        identifier_rows = (
            connection.execute(
                select(canonical_security_identifiers_table).where(
                    canonical_security_identifiers_table.c.canonical_security_id == security_id
                )
            )
            .mappings()
            .all()
        )
        return _row_to_security(root_row, listing_rows, mapping_rows, identifier_rows)


def _root_to_row(security: CanonicalSecurity) -> dict[str, Any]:
    return {
        "id": str(security.id),
        "canonical_company_name": security.canonical_company_name,
        "native_ticker": security.native_ticker,
        "primary_exchange_mic": security.primary_exchange_mic.value,
        "country": security.country,
        "trading_currency": security.trading_currency.value,
        "resolution_status": security.resolution_status,
        "created_at": security.created_at.isoformat(),
        "updated_at": security.updated_at.isoformat(),
    }


def _listing_to_row(security_id: str, listing: ListingRef) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "canonical_security_id": security_id,
        "ticker": listing.ticker,
        "exchange_mic": listing.exchange_mic.value,
        "currency": listing.currency.value,
        "relationship": listing.relationship,
        "security_type": listing.security_type,
        "provider_symbol": listing.provider_symbol,
    }


def _mapping_to_row(security_id: str, mapping: ProviderMapping) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "canonical_security_id": security_id,
        "provider_name": mapping.provider_name,
        "provider_ticker": mapping.provider_ticker,
        "provider_security_id": mapping.provider_security_id,
        "provider_exchange_code": mapping.provider_exchange_code,
        "confidence": mapping.confidence,
        "verification_status": mapping.verification_status,
        "mapped_at": mapping.mapped_at.isoformat(),
        "verified_at": mapping.verified_at.isoformat() if mapping.verified_at is not None else None,
    }


def _identifier_to_row(security_id: str, identifier: SecurityIdentifier) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "canonical_security_id": security_id,
        "identifier_type": identifier.identifier_type,
        "value": identifier.value,
        "recorded_at": identifier.recorded_at.isoformat(),
    }


def _row_to_security(
    root_row: Mapping[str, Any],
    listing_rows: list[Mapping[str, Any]],
    mapping_rows: list[Mapping[str, Any]],
    identifier_rows: list[Mapping[str, Any]],
) -> CanonicalSecurity:
    return CanonicalSecurity(
        id=CanonicalSecurityId(uuid.UUID(root_row["id"])),
        canonical_company_name=root_row["canonical_company_name"],
        native_ticker=root_row["native_ticker"],
        primary_exchange_mic=MicCode(root_row["primary_exchange_mic"]),
        country=root_row["country"],
        trading_currency=TradingCurrency(root_row["trading_currency"]),
        resolution_status=root_row["resolution_status"],
        listings=tuple(
            ListingRef(
                ticker=row["ticker"],
                exchange_mic=MicCode(row["exchange_mic"]),
                currency=TradingCurrency(row["currency"]),
                relationship=row["relationship"],
                security_type=row["security_type"],
                provider_symbol=row["provider_symbol"],
            )
            for row in listing_rows
        ),
        provider_mappings=tuple(
            ProviderMapping(
                provider_name=row["provider_name"],
                provider_ticker=row["provider_ticker"],
                confidence=row["confidence"],
                verification_status=row["verification_status"],
                mapped_at=datetime.fromisoformat(row["mapped_at"]),
                provider_security_id=row["provider_security_id"],
                provider_exchange_code=row["provider_exchange_code"],
                verified_at=(
                    datetime.fromisoformat(row["verified_at"]) if row["verified_at"] is not None else None
                ),
            )
            for row in mapping_rows
        ),
        identifiers=tuple(
            SecurityIdentifier(
                identifier_type=row["identifier_type"],
                value=row["value"],
                recorded_at=datetime.fromisoformat(row["recorded_at"]),
            )
            for row in identifier_rows
        ),
        created_at=datetime.fromisoformat(root_row["created_at"]),
        updated_at=datetime.fromisoformat(root_row["updated_at"]),
    )

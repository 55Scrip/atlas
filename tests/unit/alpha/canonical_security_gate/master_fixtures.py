"""A populated security master, for tests that live outside this package.

`atlas.alpha.canonical_security` may only be imported directly by its own
package and tests, the Resolution Service and the Identity Gate -- enforced
by `tests/unit/alpha/canonical_security/test_integration_safety.py`, which
walks the filesystem and does not care that the importer is a test. A
portfolio test that needs a master therefore cannot build one itself.

So it asks here. This module sits inside the Gate's own test package, which
is on the allowed side of that boundary, and hands back nothing but an
engine and a `{ISIN: canonical id}` mapping -- the same shape of favour the
Gate's `factory` does for production code, which reaches the master through
a plain callable rather than through the aggregate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.engine import Engine

from atlas.alpha.canonical_security.models import CanonicalSecurity, ListingRef, SecurityIdentifier
from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalSecurityRepository
from atlas.alpha.canonical_security.table import create_canonical_security_tables
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency

__all__ = ["MasterSecurity", "create_master_tables", "seed_master"]

_RECORDED = datetime(2026, 9, 16, tzinfo=timezone.utc)


@dataclass(frozen=True)
class MasterSecurity:
    """One row shaped like the live ones: a listing, a share-class FIGI from
    OpenFIGI, and -- unlike any live row today -- a recorded ISIN, which is
    the only correspondence an offline resolution can match on."""

    name: str
    ticker: str
    mic: str
    country: str
    share_class_figi: str
    isin: str
    currency: str | None = None


def create_master_tables(engine: Engine) -> None:
    create_canonical_security_tables(engine)


def seed_master(engine: Engine, *securities: MasterSecurity) -> dict[str, str]:
    """Persist each security and return `{isin: canonical security id}`.

    Returning ids rather than aggregates is the point: a caller on the far
    side of the boundary gets the identifier it needs to make assertions
    without ever holding a `CanonicalSecurity`.
    """
    create_canonical_security_tables(engine)
    repository = SqlAlchemyCanonicalSecurityRepository(engine)
    ids: dict[str, str] = {}
    for spec in securities:
        currency = TradingCurrency(spec.currency) if spec.currency else None
        security = CanonicalSecurity.discover(
            canonical_company_name=spec.name,
            native_ticker=spec.ticker,
            primary_exchange_mic=MicCode(spec.mic),
            country=spec.country,
            trading_currency=currency,
        ).add_listing(
            ListingRef(
                ticker=spec.ticker, exchange_mic=MicCode(spec.mic), currency=currency,
                relationship="NATIVE", security_type="COMMON_STOCK",
            )
        ).add_identifier(
            SecurityIdentifier(
                identifier_type="SHARE_CLASS_FIGI", value=spec.share_class_figi,
                recorded_at=_RECORDED, provider="OPENFIGI",
            )
        ).add_identifier(
            SecurityIdentifier(
                identifier_type="ISIN", value=spec.isin, recorded_at=_RECORDED,
                provider="BROKER_IMPORT",
            )
        )
        repository.save(security)
        ids[spec.isin] = str(security.id)
    return ids

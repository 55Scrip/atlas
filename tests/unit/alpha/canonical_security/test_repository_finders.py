"""Sprint N Phase 14 -- new finder methods on
`SqlAlchemyCanonicalSecurityRepository` (find_active, find_by_provider_id,
find_by_figi, find_by_isin, find_by_listing, find_by_ticker_and_exchange).
Kept in this package's own test directory since these methods live on
`atlas.alpha.canonical_security.repository`, extended by Sprint N rather
than moved."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.models import CanonicalSecurity, ListingRef, ProviderMapping, SecurityIdentifier
from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalSecurityRepository
from atlas.alpha.canonical_security.table import create_canonical_security_tables
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency

_FIXED_CLOCK = lambda: datetime(2026, 8, 18, tzinfo=timezone.utc)  # noqa: E731


def _make_repository() -> SqlAlchemyCanonicalSecurityRepository:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_canonical_security_tables(engine)
    return SqlAlchemyCanonicalSecurityRepository(engine)


def _lvmh() -> CanonicalSecurity:
    security = CanonicalSecurity.discover(
        canonical_company_name="LVMH",
        native_ticker="MC",
        primary_exchange_mic=MicCode("XPAR"),
        country="France",
        trading_currency=TradingCurrency("EUR"),
        clock=_FIXED_CLOCK,
    )
    listing = ListingRef(
        ticker="MC", exchange_mic=MicCode("XPAR"), currency=TradingCurrency("EUR"),
        relationship="NATIVE", security_type="COMMON_STOCK",
    )
    mapping = ProviderMapping(
        provider_name="TWELVE_DATA", provider_ticker="MC", provider_security_id="TD-MC-001",
        confidence="HIGH", verification_status="CORROBORATED", mapped_at=_FIXED_CLOCK(),
    )
    identifier = SecurityIdentifier(identifier_type="FIGI", value="BBG000BPXBQ8", recorded_at=_FIXED_CLOCK())
    return (
        security.add_listing(listing, clock=_FIXED_CLOCK)
        .add_provider_mapping(mapping, clock=_FIXED_CLOCK)
        .add_identifier(identifier, clock=_FIXED_CLOCK)
    )


def test_find_active_returns_only_active_securities() -> None:
    repository = _make_repository()
    lvmh = _lvmh()
    repository.save(lvmh)  # CANONICAL, not ACTIVE
    assert repository.find_active() == ()

    active = (
        lvmh.transition_to("CANDIDATES_FOUND", clock=_FIXED_CLOCK)
        .transition_to("IDENTITY_VERIFIED", clock=_FIXED_CLOCK)
        .transition_to("CONFIRMED", clock=_FIXED_CLOCK)
        .transition_to("CANONICAL", clock=_FIXED_CLOCK)
        .transition_to("ACTIVE", clock=_FIXED_CLOCK)
    )
    repository.save(active)
    found = repository.find_active()
    assert len(found) == 1
    assert found[0].id == active.id


def test_find_by_provider_id_distinct_from_find_by_provider_mapping() -> None:
    repository = _make_repository()
    lvmh = _lvmh()
    repository.save(lvmh)
    found = repository.find_by_provider_id("TWELVE_DATA", "TD-MC-001")
    assert found is not None
    assert found.id == lvmh.id

    assert repository.find_by_provider_id("TWELVE_DATA", "WRONG-ID") is None


def test_find_by_figi() -> None:
    repository = _make_repository()
    lvmh = _lvmh()
    repository.save(lvmh)
    found = repository.find_by_figi("BBG000BPXBQ8")
    assert found is not None
    assert found.id == lvmh.id
    assert repository.find_by_figi("NONEXISTENT") is None


def test_find_by_isin() -> None:
    repository = _make_repository()
    security = _lvmh().add_identifier(
        SecurityIdentifier(identifier_type="ISIN", value="FR0000121014", recorded_at=_FIXED_CLOCK()), clock=_FIXED_CLOCK
    )
    repository.save(security)
    found = repository.find_by_isin("FR0000121014")
    assert found is not None
    assert found.id == security.id


def test_find_by_listing_requires_exact_relationship_match() -> None:
    repository = _make_repository()
    lvmh = _lvmh()
    repository.save(lvmh)
    found = repository.find_by_listing("MC", "XPAR", "NATIVE")
    assert found is not None
    assert repository.find_by_listing("MC", "XPAR", "ADR") is None


def test_find_by_ticker_and_exchange_ignores_relationship() -> None:
    repository = _make_repository()
    lvmh = _lvmh()
    repository.save(lvmh)
    found = repository.find_by_ticker_and_exchange("MC", "XPAR")
    assert found is not None
    assert found.id == lvmh.id
    assert repository.find_by_ticker_and_exchange("MC", "XNYS") is None

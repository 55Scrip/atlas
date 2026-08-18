"""Repository persistence tests -- Sprint M Phase 7/11. Isolated,
in-memory SQLite, same fixture pattern as `atlas.alpha.security_
confirmation`'s own repository tests -- never touches the real
`atlas.db`.
"""
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


def _lvmh_with_listing_and_mapping() -> CanonicalSecurity:
    security = CanonicalSecurity.discover(
        canonical_company_name="LVMH Moët Hennessy Louis Vuitton SE",
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
        provider_name="TWELVE_DATA", provider_ticker="MC", confidence="HIGH",
        verification_status="CORROBORATED", mapped_at=_FIXED_CLOCK(),
    )
    identifier = SecurityIdentifier(identifier_type="ISIN", value="FR0000121014", recorded_at=_FIXED_CLOCK())
    return (
        security.add_listing(listing, clock=_FIXED_CLOCK)
        .add_provider_mapping(mapping, clock=_FIXED_CLOCK)
        .add_identifier(identifier, clock=_FIXED_CLOCK)
    )


def test_save_then_load_round_trips_full_aggregate() -> None:
    repository = _make_repository()
    security = _lvmh_with_listing_and_mapping()
    repository.save(security)

    loaded = repository.load(str(security.id))
    assert loaded == security


def test_load_returns_none_for_unknown_id() -> None:
    repository = _make_repository()
    assert repository.load("00000000-0000-0000-0000-000000000000") is None


def test_exists_reflects_save() -> None:
    repository = _make_repository()
    security = _lvmh_with_listing_and_mapping()
    assert repository.exists(str(security.id)) is False
    repository.save(security)
    assert repository.exists(str(security.id)) is True


def test_save_is_idempotent_full_replace_on_second_save() -> None:
    """Saving an aggregate a second time (e.g. after a status
    transition) replaces the child rows rather than accumulating
    duplicates."""
    repository = _make_repository()
    security = _lvmh_with_listing_and_mapping()
    repository.save(security)

    transitioned = security.transition_to("CANDIDATES_FOUND", clock=_FIXED_CLOCK)
    repository.save(transitioned)

    loaded = repository.load(str(security.id))
    assert loaded is not None
    assert loaded.resolution_status == "CANDIDATES_FOUND"
    assert len(loaded.listings) == 1
    assert len(loaded.provider_mappings) == 1
    assert len(loaded.identifiers) == 1


def test_find_by_provider_mapping_locates_the_aggregate() -> None:
    repository = _make_repository()
    security = _lvmh_with_listing_and_mapping()
    repository.save(security)

    found = repository.find_by_provider_mapping("TWELVE_DATA", "MC")
    assert found == security


def test_find_by_provider_mapping_returns_none_when_absent() -> None:
    repository = _make_repository()
    assert repository.find_by_provider_mapping("SEC_EDGAR", "MC") is None


def test_find_by_identifier_locates_the_aggregate() -> None:
    repository = _make_repository()
    security = _lvmh_with_listing_and_mapping()
    repository.save(security)

    found = repository.find_by_identifier("ISIN", "FR0000121014")
    assert found == security


def test_find_by_identifier_returns_none_when_absent() -> None:
    repository = _make_repository()
    assert repository.find_by_identifier("ISIN", "SE0000108227") is None

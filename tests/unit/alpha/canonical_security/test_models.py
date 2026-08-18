"""CanonicalSecurity aggregate tests -- Sprint M Phase 11 (creation,
mapping addition/replacement, status transitions, validation rules).

Several tests use the live MC/EVO collision shapes from Sprints H/I as
realistic fixtures (a `REJECTED`-confidence SEC EDGAR mapping alongside
a `HIGH`-confidence Twelve Data mapping on the same aggregate) --
grounding these unit tests in the exact evidence this foundation exists
to prevent a recurrence of, not synthetic placeholder data.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.alpha.canonical_security.exceptions import (
    CanonicalStatusRequiresListingError,
    DuplicateListingError,
    DuplicateProviderMappingError,
    EmptyTickerError,
)
from atlas.alpha.canonical_security.models import CanonicalSecurity, ListingRef, ProviderMapping
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency

_FIXED_CLOCK = lambda: datetime(2026, 8, 18, tzinfo=timezone.utc)  # noqa: E731


def _lvmh() -> CanonicalSecurity:
    return CanonicalSecurity.discover(
        canonical_company_name="LVMH Moët Hennessy Louis Vuitton SE",
        native_ticker="MC",
        primary_exchange_mic=MicCode("XPAR"),
        country="France",
        trading_currency=TradingCurrency("EUR"),
        clock=_FIXED_CLOCK,
    )


def test_discover_creates_discovered_status_with_no_listings_or_mappings() -> None:
    security = _lvmh()
    assert security.resolution_status == "DISCOVERED"
    assert security.listings == ()
    assert security.provider_mappings == ()
    assert security.identifiers == ()
    assert security.created_at == security.updated_at == datetime(2026, 8, 18, tzinfo=timezone.utc)


def test_id_is_stable_uuid_and_string_representation_is_the_uuid() -> None:
    security = _lvmh()
    assert str(security.id) == str(security.id.value)


def test_blank_native_ticker_rejected() -> None:
    with pytest.raises(EmptyTickerError):
        CanonicalSecurity.discover(
            canonical_company_name="Some Company",
            native_ticker="   ",
            primary_exchange_mic=MicCode("XPAR"),
            country="France",
            trading_currency=TradingCurrency("EUR"),
        )


def test_blank_company_name_rejected() -> None:
    with pytest.raises(ValueError):
        CanonicalSecurity.discover(
            canonical_company_name="",
            native_ticker="MC",
            primary_exchange_mic=MicCode("XPAR"),
            country="France",
            trading_currency=TradingCurrency("EUR"),
        )


def test_add_listing_is_additive_and_returns_new_instance() -> None:
    original = _lvmh()
    listing = ListingRef(
        ticker="MC",
        exchange_mic=MicCode("XPAR"),
        currency=TradingCurrency("EUR"),
        relationship="NATIVE",
        security_type="COMMON_STOCK",
    )
    updated = original.add_listing(listing, clock=_FIXED_CLOCK)

    assert original.listings == ()  # original untouched -- immutability
    assert updated.listings == (listing,)
    assert updated.id == original.id  # id never changes


def test_add_listing_rejects_duplicate_exchange_ticker_pair() -> None:
    listing = ListingRef(
        ticker="MC",
        exchange_mic=MicCode("XPAR"),
        currency=TradingCurrency("EUR"),
        relationship="NATIVE",
        security_type="COMMON_STOCK",
    )
    security = _lvmh().add_listing(listing, clock=_FIXED_CLOCK)
    with pytest.raises(DuplicateListingError):
        security.add_listing(listing, clock=_FIXED_CLOCK)


def test_native_and_adr_listings_coexist_as_distinct_entries() -> None:
    """Sprint J Phase 10 -- native and ADR listings are never merged."""
    native = ListingRef(
        ticker="TSM",
        exchange_mic=MicCode("ROCO"),
        currency=TradingCurrency("TWD"),
        relationship="NATIVE",
        security_type="COMMON_STOCK",
    )
    adr = ListingRef(
        ticker="TSM",
        exchange_mic=MicCode("XNYS"),
        currency=TradingCurrency("USD"),
        relationship="ADR",
        security_type="DEPOSITARY_RECEIPT",
    )
    security = (
        CanonicalSecurity.discover(
            canonical_company_name="Taiwan Semiconductor Manufacturing Co. Ltd.",
            native_ticker="TSM",
            primary_exchange_mic=MicCode("ROCO"),
            country="Taiwan",
            trading_currency=TradingCurrency("TWD"),
            clock=_FIXED_CLOCK,
        )
        .add_listing(native, clock=_FIXED_CLOCK)
        .add_listing(adr, clock=_FIXED_CLOCK)
    )
    assert len(security.listings) == 2
    assert security.primary_listing == native  # NATIVE preferred over ADR


def test_primary_listing_falls_back_to_sole_adr_when_no_native_exists() -> None:
    adr = ListingRef(
        ticker="TSM",
        exchange_mic=MicCode("XNYS"),
        currency=TradingCurrency("USD"),
        relationship="ADR",
        security_type="DEPOSITARY_RECEIPT",
    )
    security = _lvmh().add_listing(adr, clock=_FIXED_CLOCK)
    assert security.primary_listing == adr


def test_primary_listing_is_none_with_multiple_non_native_listings() -> None:
    adr = ListingRef(
        ticker="TSM", exchange_mic=MicCode("XNYS"), currency=TradingCurrency("USD"),
        relationship="ADR", security_type="DEPOSITARY_RECEIPT",
    )
    otc = ListingRef(
        ticker="TSMWY", exchange_mic=MicCode("OTCM"), currency=TradingCurrency("USD"),
        relationship="OTC", security_type="OTHER",
    )
    security = _lvmh().add_listing(adr, clock=_FIXED_CLOCK).add_listing(otc, clock=_FIXED_CLOCK)
    assert security.primary_listing is None


def test_add_provider_mapping_is_additive() -> None:
    mapping = ProviderMapping(
        provider_name="TWELVE_DATA",
        provider_ticker="MC",
        confidence="HIGH",
        verification_status="UNVERIFIED",
        mapped_at=_FIXED_CLOCK(),
    )
    security = _lvmh().add_provider_mapping(mapping, clock=_FIXED_CLOCK)
    assert security.provider_mappings == (mapping,)


def test_add_provider_mapping_rejects_duplicate_active_pair() -> None:
    mapping = ProviderMapping(
        provider_name="TWELVE_DATA",
        provider_ticker="MC",
        confidence="HIGH",
        verification_status="UNVERIFIED",
        mapped_at=_FIXED_CLOCK(),
    )
    security = _lvmh().add_provider_mapping(mapping, clock=_FIXED_CLOCK)
    with pytest.raises(DuplicateProviderMappingError):
        security.add_provider_mapping(mapping, clock=_FIXED_CLOCK)


def test_add_provider_mapping_allows_reinsertion_once_prior_mapping_is_superseded() -> None:
    """A superseded mapping frees the (provider_name, provider_ticker)
    pair for a fresh, active mapping -- e.g. a re-resolution after a
    ticker's provider-side symbol changed."""
    from dataclasses import replace

    original = ProviderMapping(
        provider_name="TWELVE_DATA",
        provider_ticker="MC",
        confidence="HIGH",
        verification_status="UNVERIFIED",
        mapped_at=_FIXED_CLOCK(),
    )
    security = _lvmh().add_provider_mapping(original, clock=_FIXED_CLOCK)
    superseded = replace(security, provider_mappings=(
        replace(original, verification_status="SUPERSEDED_MAPPING"),
    ))
    fresh = ProviderMapping(
        provider_name="TWELVE_DATA",
        provider_ticker="MC",
        confidence="HIGH",
        verification_status="UNVERIFIED",
        mapped_at=_FIXED_CLOCK(),
    )
    result = superseded.add_provider_mapping(fresh, clock=_FIXED_CLOCK)
    assert len(result.provider_mappings) == 2


def test_mc_collision_shape_one_corroborated_one_rejected_mapping_coexist() -> None:
    """Live evidence from Sprints H/I: SEC EDGAR's flat ticker map
    resolves 'MC' to Moelis & Co (rejected here), while Twelve Data
    correctly resolves it to LVMH (corroborated) -- both must be
    representable on the same aggregate simultaneously."""
    twelve_data_mapping = ProviderMapping(
        provider_name="TWELVE_DATA",
        provider_ticker="MC",
        provider_exchange_code="XPAR",
        confidence="HIGH",
        verification_status="CORROBORATED",
        mapped_at=_FIXED_CLOCK(),
    )
    sec_edgar_mapping = ProviderMapping(
        provider_name="SEC_EDGAR",
        provider_ticker="MC",
        confidence="REJECTED",
        verification_status="REJECTED",
        mapped_at=_FIXED_CLOCK(),
    )
    security = (
        _lvmh()
        .add_provider_mapping(twelve_data_mapping, clock=_FIXED_CLOCK)
        .add_provider_mapping(sec_edgar_mapping, clock=_FIXED_CLOCK)
    )
    assert len(security.provider_mappings) == 2
    rejected = [m for m in security.provider_mappings if m.confidence == "REJECTED"]
    assert len(rejected) == 1
    assert rejected[0].provider_name == "SEC_EDGAR"


def test_transition_to_canonical_without_listings_is_rejected() -> None:
    security = _lvmh()
    with pytest.raises(CanonicalStatusRequiresListingError):
        (
            security.transition_to("CANDIDATES_FOUND", clock=_FIXED_CLOCK)
            .transition_to("IDENTITY_VERIFIED", clock=_FIXED_CLOCK)
            .transition_to("CONFIRMED", clock=_FIXED_CLOCK)
            .transition_to("CANONICAL", clock=_FIXED_CLOCK)
        )


def test_full_happy_path_transition_to_active_requires_a_listing() -> None:
    listing = ListingRef(
        ticker="MC", exchange_mic=MicCode("XPAR"), currency=TradingCurrency("EUR"),
        relationship="NATIVE", security_type="COMMON_STOCK",
    )
    security = (
        _lvmh()
        .add_listing(listing, clock=_FIXED_CLOCK)
        .transition_to("CANDIDATES_FOUND", clock=_FIXED_CLOCK)
        .transition_to("IDENTITY_VERIFIED", clock=_FIXED_CLOCK)
        .transition_to("CONFIRMED", clock=_FIXED_CLOCK)
        .transition_to("CANONICAL", clock=_FIXED_CLOCK)
        .transition_to("ACTIVE", clock=_FIXED_CLOCK)
    )
    assert security.resolution_status == "ACTIVE"


def test_add_identifier_is_additive() -> None:
    from atlas.alpha.canonical_security.models import SecurityIdentifier

    identifier = SecurityIdentifier(identifier_type="ISIN", value="FR0000121014", recorded_at=_FIXED_CLOCK())
    security = _lvmh().add_identifier(identifier, clock=_FIXED_CLOCK)
    assert security.identifiers == (identifier,)

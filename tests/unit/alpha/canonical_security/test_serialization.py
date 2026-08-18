"""JSON round-trip tests -- Sprint M Phase 9."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.canonical_security.models import (
    CanonicalSecurity,
    ListingRef,
    ProviderMapping,
    SecurityIdentifier,
)
from atlas.alpha.canonical_security.serialization import from_json_dict, to_json_dict
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency

_FIXED_CLOCK = lambda: datetime(2026, 8, 18, tzinfo=timezone.utc)  # noqa: E731


def _full_security() -> CanonicalSecurity:
    security = CanonicalSecurity.discover(
        canonical_company_name="Evolution AB (publ)",
        native_ticker="EVO",
        primary_exchange_mic=MicCode("XSTO"),
        country="Sweden",
        trading_currency=TradingCurrency("SEK"),
        clock=_FIXED_CLOCK,
    )
    listing = ListingRef(
        ticker="EVO", exchange_mic=MicCode("XSTO"), currency=TradingCurrency("SEK"),
        relationship="NATIVE", security_type="COMMON_STOCK", provider_symbol="EVO",
    )
    mapping = ProviderMapping(
        provider_name="TWELVE_DATA", provider_ticker="EVO", confidence="HIGH",
        verification_status="CORROBORATED", mapped_at=_FIXED_CLOCK(), verified_at=_FIXED_CLOCK(),
    )
    identifier = SecurityIdentifier(identifier_type="FIGI", value="BBG000BLNNH6", recorded_at=_FIXED_CLOCK())
    return security.add_listing(listing, clock=_FIXED_CLOCK).add_provider_mapping(
        mapping, clock=_FIXED_CLOCK
    ).add_identifier(identifier, clock=_FIXED_CLOCK)


def test_round_trip_preserves_every_field() -> None:
    original = _full_security()
    data = to_json_dict(original)
    restored = from_json_dict(data)
    assert restored == original


def test_round_trip_preserves_empty_collections() -> None:
    original = CanonicalSecurity.discover(
        canonical_company_name="Volvo AB",
        native_ticker="VOLV-B",
        primary_exchange_mic=MicCode("XSTO"),
        country="Sweden",
        trading_currency=TradingCurrency("SEK"),
        clock=_FIXED_CLOCK,
    )
    restored = from_json_dict(to_json_dict(original))
    assert restored == original


def test_to_json_dict_uses_camel_case_keys() -> None:
    data = to_json_dict(_full_security())
    assert "canonicalCompanyName" in data
    assert "nativeTicker" in data
    assert "providerMappings" in data
    assert data["providerMappings"][0]["providerName"] == "TWELVE_DATA"

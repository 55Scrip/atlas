"""Comparison tests -- Sprint N Phase 5 steps 3-10."""
from __future__ import annotations

from atlas.alpha.canonical_security.models import CanonicalSecurity, ListingRef
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.comparison import (
    compare_candidate_to_existing,
    compare_candidates,
    filter_impossible_candidates,
)


def test_filter_impossible_candidates_dedups_same_provider_and_symbol() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    b = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    c = ProviderCandidate(provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.")
    survivors = filter_impossible_candidates((a, b, c))
    assert survivors == (a, c)


def test_filter_impossible_candidates_preserves_order() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC")
    assert filter_impossible_candidates((a, b)) == (a, b)


def test_compare_candidates_company_name_uses_canonicalization() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="AAPL", company_name="APPLE INC")
    comparisons = compare_candidates(a, b)
    name_comparison = next(c for c in comparisons if c.field_name == "company_name")
    assert name_comparison.agrees is True


def test_compare_candidates_mc_collision_disagrees_on_name() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Co")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH")
    comparisons = compare_candidates(a, b)
    name_comparison = next(c for c in comparisons if c.field_name == "company_name")
    assert name_comparison.agrees is False


def test_compare_candidates_missing_field_is_none_not_false() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH")
    comparisons = compare_candidates(a, b)
    name_comparison = next(c for c in comparisons if c.field_name == "company_name")
    assert name_comparison.agrees is None


def test_compare_candidate_to_existing_detects_wrong_exchange() -> None:
    existing = CanonicalSecurity.discover(
        canonical_company_name="Evolution AB",
        native_ticker="EVO",
        primary_exchange_mic=MicCode("XSTO"),
        country="Sweden",
        trading_currency=TradingCurrency("SEK"),
    )
    wrong_exchange_candidate = ProviderCandidate(
        provider_name="SEC_EDGAR",
        symbol="EVO",
        company_name="Evolution AB",
        exchange_mic=MicCode("XNGS"),
    )
    comparisons = compare_candidate_to_existing(wrong_exchange_candidate, existing)
    exchange_comparison = next(c for c in comparisons if c.field_name == "exchange_mic")
    assert exchange_comparison.agrees is False


def test_compare_candidate_to_existing_detects_wrong_country() -> None:
    existing = CanonicalSecurity.discover(
        canonical_company_name="Evolution AB",
        native_ticker="EVO",
        primary_exchange_mic=MicCode("XSTO"),
        country="Sweden",
        trading_currency=TradingCurrency("SEK"),
    )
    wrong_country_candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="EVO", country="Germany")
    comparisons = compare_candidate_to_existing(wrong_country_candidate, existing)
    country_comparison = next(c for c in comparisons if c.field_name == "country")
    assert country_comparison.agrees is False


def test_compare_candidate_to_existing_security_type_uses_primary_listing() -> None:
    existing = CanonicalSecurity.discover(
        canonical_company_name="Taiwan Semiconductor",
        native_ticker="TSM",
        primary_exchange_mic=MicCode("XNYS"),
        country="Taiwan",
        trading_currency=TradingCurrency("USD"),
    ).add_listing(
        ListingRef(
            ticker="TSM", exchange_mic=MicCode("XNYS"), currency=TradingCurrency("USD"),
            relationship="ADR", security_type="DEPOSITARY_RECEIPT",
        )
    )
    candidate = ProviderCandidate(provider_name="ALPHA_VANTAGE", symbol="TSM", security_type="DEPOSITARY_RECEIPT")
    comparisons = compare_candidate_to_existing(candidate, existing)
    type_comparison = next(c for c in comparisons if c.field_name == "security_type")
    assert type_comparison.agrees is True

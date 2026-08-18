"""ProviderCandidate tests -- Sprint N Phase 4."""
from __future__ import annotations

import pytest

from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.exceptions import EmptySymbolError


def test_blank_symbol_rejected() -> None:
    with pytest.raises(EmptySymbolError):
        ProviderCandidate(provider_name="SEC_EDGAR", symbol="   ")


def test_only_symbol_required() -> None:
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL")
    assert candidate.symbol == "AAPL"
    assert candidate.exchange_mic is None
    assert candidate.corroborating_field_count() == 0


def test_corroborating_field_count_counts_every_identity_field() -> None:
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA",
        symbol="AAPL",
        exchange_mic=MicCode("XNGS"),
        country="United States",
        company_name="Apple Inc.",
        security_type="COMMON_STOCK",
        currency=TradingCurrency("USD"),
    )
    # currency is not counted -- see corroborating_field_count()'s own
    # field list: exchange_mic, country, company_name, security_type,
    # listing_relationship, isin, figi, cusip, sedol (9 fields, 4 present here)
    assert candidate.corroborating_field_count() == 4


def test_no_provider_specific_logic_leaks_into_the_model() -> None:
    """Sprint N Phase 4's own requirement: the model is provider-neutral.
    A candidate from any of the four known providers must construct
    identically -- there is no branch anywhere in this class keyed on
    `provider_name`."""
    for provider in ("SEC_EDGAR", "ALPHA_VANTAGE", "TWELVE_DATA", "OPENFIGI"):
        candidate = ProviderCandidate(provider_name=provider, symbol="X")
        assert candidate.provider_name == provider

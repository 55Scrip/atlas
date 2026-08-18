"""Value-object validation -- Sprint M Phase 3/10."""
from __future__ import annotations

import pytest

from atlas.alpha.canonical_security.exceptions import (
    InvalidExchangeCodeError,
    InvalidMicCodeError,
    InvalidTradingCurrencyError,
    UnsupportedIdentifierTypeError,
    UnsupportedIdentityConfidenceError,
    UnsupportedListingRelationshipError,
    UnsupportedProviderNameError,
    UnsupportedResolutionStatusError,
    UnsupportedSecurityTypeError,
    UnsupportedVerificationStatusError,
)
from atlas.alpha.canonical_security.value_objects import (
    ExchangeCode,
    MicCode,
    TradingCurrency,
    validate_identifier_type,
    validate_identity_confidence,
    validate_listing_relationship,
    validate_provider_name,
    validate_resolution_status,
    validate_security_type,
    validate_verification_status,
)


def test_exchange_code_rejects_blank() -> None:
    with pytest.raises(InvalidExchangeCodeError):
        ExchangeCode("   ")


def test_mic_code_normalizes_to_uppercase() -> None:
    assert MicCode("xsto").value == "XSTO"


def test_mic_code_rejects_blank() -> None:
    with pytest.raises(InvalidMicCodeError):
        MicCode("")


def test_trading_currency_normalizes_and_validates_length() -> None:
    assert TradingCurrency("sek").value == "SEK"
    with pytest.raises(InvalidTradingCurrencyError):
        TradingCurrency("SE")
    with pytest.raises(InvalidTradingCurrencyError):
        TradingCurrency("SEK1")


def test_provider_name_closed_allow_list() -> None:
    assert validate_provider_name("TWELVE_DATA") == "TWELVE_DATA"
    with pytest.raises(UnsupportedProviderNameError):
        validate_provider_name("FINNHUB")


def test_security_type_closed_allow_list() -> None:
    assert validate_security_type("COMMON_STOCK") == "COMMON_STOCK"
    with pytest.raises(UnsupportedSecurityTypeError):
        validate_security_type("WARRANT")


def test_listing_relationship_closed_allow_list() -> None:
    assert validate_listing_relationship("ADR") == "ADR"
    with pytest.raises(UnsupportedListingRelationshipError):
        validate_listing_relationship("SPONSORED_ADR")


def test_identity_confidence_closed_allow_list() -> None:
    assert validate_identity_confidence("HIGH") == "HIGH"
    with pytest.raises(UnsupportedIdentityConfidenceError):
        validate_identity_confidence("VERY_HIGH")


def test_verification_status_closed_allow_list() -> None:
    assert validate_verification_status("CORROBORATED") == "CORROBORATED"
    with pytest.raises(UnsupportedVerificationStatusError):
        validate_verification_status("PENDING")


def test_resolution_status_closed_allow_list() -> None:
    assert validate_resolution_status("CANONICAL") == "CANONICAL"
    with pytest.raises(UnsupportedResolutionStatusError):
        validate_resolution_status("PENDING")


def test_identifier_type_closed_allow_list() -> None:
    assert validate_identifier_type("ISIN") == "ISIN"
    with pytest.raises(UnsupportedIdentifierTypeError):
        validate_identifier_type("LEI")

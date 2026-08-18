"""Confidence Engine tests -- Sprint N Phase 7."""
from __future__ import annotations

from atlas.alpha.canonical_security.models import CanonicalSecurity
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.confidence import calculate_confidence
from atlas.alpha.canonical_security_resolution.provider_agreement import evaluate_provider_agreement


def test_ticker_alone_never_reaches_high() -> None:
    """The one rule Sprint N Phase 7 names explicitly."""
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="XYZ")
    agreement = evaluate_provider_agreement((candidate,))
    confidence = calculate_confidence(candidate, agreement=agreement)
    assert confidence == "LOW"


def test_ticker_alone_never_reaches_high_even_with_provider_agreement_boost() -> None:
    """Two providers agreeing on a bare ticker (no company name at all)
    never conflict (Phase 8: absence of data is not disagreement), and
    the boost rule must not be able to promote a ticker-only candidate
    past LOW."""
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="XYZ")
    b = ProviderCandidate(provider_name="ALPHA_VANTAGE", symbol="XYZ")
    agreement = evaluate_provider_agreement((a, b))
    assert calculate_confidence(a, agreement=agreement) == "LOW"


def test_full_corroboration_reaches_high() -> None:
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA",
        symbol="AAPL",
        company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"),
        country="United States",
        security_type="COMMON_STOCK",
    )
    agreement = evaluate_provider_agreement((candidate,))
    assert calculate_confidence(candidate, agreement=agreement) == "HIGH"


def test_partial_corroboration_reaches_medium() -> None:
    candidate = ProviderCandidate(provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.")
    agreement = evaluate_provider_agreement((candidate,))
    assert calculate_confidence(candidate, agreement=agreement) == "MEDIUM"


def test_provider_disagreement_caps_dominant_group_at_medium() -> None:
    """Conflicting providers must never be silently merged into HIGH,
    even for the majority side."""
    a = ProviderCandidate(
        provider_name="SEC_EDGAR", symbol="MC", company_name="LVMH",
        exchange_mic=MicCode("XPAR"), country="France", security_type="COMMON_STOCK",
    )
    b = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH",
        exchange_mic=MicCode("XPAR"), country="France", security_type="COMMON_STOCK",
    )
    c = ProviderCandidate(provider_name="OPENFIGI", symbol="MC", company_name="Moelis & Company")
    agreement = evaluate_provider_agreement((a, b, c))
    assert calculate_confidence(a, agreement=agreement) == "MEDIUM"


def test_provider_disagreement_caps_minority_at_low() -> None:
    a = ProviderCandidate(
        provider_name="SEC_EDGAR", symbol="MC", company_name="LVMH",
        exchange_mic=MicCode("XPAR"), country="France", security_type="COMMON_STOCK",
    )
    b = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH",
        exchange_mic=MicCode("XPAR"), country="France", security_type="COMMON_STOCK",
    )
    c = ProviderCandidate(
        provider_name="OPENFIGI", symbol="MC", company_name="Moelis & Company",
        exchange_mic=MicCode("XNYS"), country="United States", security_type="COMMON_STOCK",
    )
    agreement = evaluate_provider_agreement((a, b, c))
    assert calculate_confidence(c, agreement=agreement) == "LOW"


def test_provider_agreement_boosts_medium_to_high() -> None:
    """Multiple providers agreeing increases confidence (Phase 8)."""
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.")
    agreement = evaluate_provider_agreement((a, b))
    assert calculate_confidence(a, agreement=agreement) == "HIGH"


def test_contradiction_against_existing_identity_is_rejected() -> None:
    existing = CanonicalSecurity.discover(
        canonical_company_name="Evolution AB",
        native_ticker="EVO",
        primary_exchange_mic=MicCode("XSTO"),
        country="Sweden",
        trading_currency=TradingCurrency("SEK"),
    )
    contradicting = ProviderCandidate(provider_name="SEC_EDGAR", symbol="EVO", company_name="Evotec SE", country="Germany")
    agreement = evaluate_provider_agreement((contradicting,))
    assert calculate_confidence(contradicting, agreement=agreement, existing=existing) == "REJECTED"


def test_agreement_with_existing_identity_does_not_downgrade() -> None:
    existing = CanonicalSecurity.discover(
        canonical_company_name="Apple Inc.",
        native_ticker="AAPL",
        primary_exchange_mic=MicCode("XNGS"),
        country="United States",
        trading_currency=TradingCurrency("USD"),
    )
    agreeing = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", security_type="COMMON_STOCK",
    )
    agreement = evaluate_provider_agreement((agreeing,))
    assert calculate_confidence(agreeing, agreement=agreement, existing=existing) == "HIGH"

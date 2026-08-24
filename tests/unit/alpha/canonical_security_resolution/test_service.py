"""`CanonicalSecurityResolutionService` tests -- Sprint N Phase 3/11/17.

Covers the brief's own required scenarios: MC collision, EVO collision,
native vs ADR, duplicate identifiers, wrong exchange, wrong country,
multiple provider agreement, provider disagreement, manual
confirmation, plus the structural "never touches BusinessRecord/Case"
guarantee.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.alpha.canonical_security.models import CanonicalSecurity
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.exceptions import (
    CandidateNotInEvidenceError,
    ManualConfirmationNotApplicableError,
    NoCandidatesToResolveError,
)
from atlas.alpha.canonical_security_resolution.service import (
    RESOLUTION_ALGORITHM_VERSION,
    CanonicalSecurityResolutionService,
    ResolutionRequest,
)

_FIXED_CLOCK = lambda: datetime(2026, 8, 18, tzinfo=timezone.utc)  # noqa: E731


def _service() -> CanonicalSecurityResolutionService:
    return CanonicalSecurityResolutionService()


def test_resolve_requires_at_least_one_candidate() -> None:
    with pytest.raises(NoCandidatesToResolveError):
        _service().resolve(ResolutionRequest(investor_ticker="AAPL", candidates=()))


def test_mc_collision_produces_ambiguous_never_auto_merges() -> None:
    sec = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Company")
    twelve_data = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH Moët Hennessy Louis Vuitton SE",
        exchange_mic=MicCode("XPAR"), country="France", currency=TradingCurrency("EUR"), security_type="COMMON_STOCK",
    )
    result = _service().resolve(ResolutionRequest(investor_ticker="MC", candidates=(sec, twelve_data)))
    assert result.outcome == "AMBIGUOUS"
    assert result.canonical_security is None
    assert len(result.evidence) == 2  # neither candidate discarded


def test_evo_collision_produces_ambiguous() -> None:
    sec = ProviderCandidate(provider_name="SEC_EDGAR", symbol="EVO", company_name="Evotec SE")
    openfigi = ProviderCandidate(
        provider_name="OPENFIGI", symbol="EVO", company_name="Evolution AB",
        exchange_mic=MicCode("XSTO"), country="Sweden", currency=TradingCurrency("SEK"), security_type="COMMON_STOCK",
    )
    result = _service().resolve(ResolutionRequest(investor_ticker="EVO", candidates=(sec, openfigi)))
    assert result.outcome == "AMBIGUOUS"
    assert result.canonical_security is None


def test_native_vs_adr_produces_two_linked_listings_never_merged() -> None:
    native = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="TSM", company_name="Taiwan Semiconductor Manufacturing Co. Ltd.",
        exchange_mic=MicCode("ROCO"), country="Taiwan", currency=TradingCurrency("TWD"),
        security_type="COMMON_STOCK", listing_relationship="NATIVE",
    )
    result = _service().resolve(ResolutionRequest(investor_ticker="TSM", candidates=(native,), existing_canonical_security=None))
    assert result.outcome == "AUTO_ACCEPT"
    assert result.canonical_security is not None
    assert result.canonical_security.listings[0].relationship == "NATIVE"

    adr = ProviderCandidate(
        provider_name="ALPHA_VANTAGE", symbol="TSM", company_name="Taiwan Semiconductor Manufacturing Co. Ltd.",
        exchange_mic=MicCode("XNYS"), country="Taiwan", currency=TradingCurrency("USD"),
        security_type="DEPOSITARY_RECEIPT", listing_relationship="ADR",
    )
    extended = _service().resolve(
        ResolutionRequest(investor_ticker="TSM", candidates=(adr,), existing_canonical_security=result.canonical_security)
    )
    assert extended.outcome == "AUTO_ACCEPT"
    assert len(extended.canonical_security.listings) == 2
    relationships = {listing.relationship for listing in extended.canonical_security.listings}
    assert relationships == {"NATIVE", "ADR"}


def test_duplicate_identifiers_do_not_produce_duplicate_mappings() -> None:
    """Resolving the same candidate against an already-CANONICAL
    security twice must not raise or duplicate the mapping -- idempotent
    re-resolution."""
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"),
        security_type="COMMON_STOCK",
    )
    first = _service().resolve(ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)))
    second = _service().resolve(
        ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,), existing_canonical_security=first.canonical_security)
    )
    assert len(second.canonical_security.provider_mappings) == 1
    assert len(second.canonical_security.listings) == 1


def test_wrong_exchange_against_existing_identity_is_rejected() -> None:
    existing = CanonicalSecurity.discover(
        canonical_company_name="Evolution AB",
        native_ticker="EVO",
        primary_exchange_mic=MicCode("XSTO"),
        country="Sweden",
        trading_currency=TradingCurrency("SEK"),
    )
    wrong_exchange = ProviderCandidate(
        provider_name="SEC_EDGAR", symbol="EVO", company_name="Evolution AB", exchange_mic=MicCode("XNGS"),
    )
    result = _service().resolve(
        ResolutionRequest(investor_ticker="EVO", candidates=(wrong_exchange,), existing_canonical_security=existing)
    )
    assert result.outcome == "REJECT"
    assert result.canonical_security is None


def test_wrong_country_against_existing_identity_is_rejected() -> None:
    existing = CanonicalSecurity.discover(
        canonical_company_name="Evolution AB",
        native_ticker="EVO",
        primary_exchange_mic=MicCode("XSTO"),
        country="Sweden",
        trading_currency=TradingCurrency("SEK"),
    )
    wrong_country = ProviderCandidate(
        provider_name="SEC_EDGAR", symbol="EVO", company_name="Evolution AB", country="Germany"
    )
    result = _service().resolve(
        ResolutionRequest(investor_ticker="EVO", candidates=(wrong_country,), existing_canonical_security=existing)
    )
    assert result.outcome == "REJECT"


def test_multiple_provider_agreement_reaches_auto_accept() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    b = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"), security_type="COMMON_STOCK",
    )
    result = _service().resolve(ResolutionRequest(investor_ticker="AAPL", candidates=(a, b)))
    assert result.outcome == "AUTO_ACCEPT"


def test_missing_security_type_on_the_winning_candidate_falls_back_to_other_never_common_stock() -> None:
    """Import Robustness (Internal Alpha Stabilization 1) regression:
    a candidate that corroborates on name/exchange/country/currency
    alone, with no provider ever supplying a security type, must reach
    `ListingRef.security_type == "OTHER"` -- never silently guessed as
    `"COMMON_STOCK"`. Same two candidates as
    `test_multiple_provider_agreement_reaches_auto_accept` above, minus
    `security_type` on the corroborating one, to isolate exactly the
    fallback in `_listing_from_candidate`."""
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    b = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"),
    )
    result = _service().resolve(ResolutionRequest(investor_ticker="AAPL", candidates=(a, b)))
    assert result.outcome == "AUTO_ACCEPT"
    assert result.canonical_security is not None
    assert result.canonical_security.listings[0].security_type == "OTHER"


def test_provider_disagreement_never_silently_merged() -> None:
    a = ProviderCandidate(
        provider_name="SEC_EDGAR", symbol="MC", company_name="LVMH",
        exchange_mic=MicCode("XPAR"), country="France", currency=TradingCurrency("EUR"), security_type="COMMON_STOCK",
    )
    b = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="MC", company_name="Moelis & Company",
        exchange_mic=MicCode("XNYS"), country="United States", currency=TradingCurrency("USD"), security_type="COMMON_STOCK",
    )
    result = _service().resolve(ResolutionRequest(investor_ticker="MC", candidates=(a, b)))
    assert result.outcome == "AMBIGUOUS"
    assert result.canonical_security is None
    # both candidates retained in evidence, neither silently dropped
    symbols_seen = {item.candidate.provider_name for item in result.evidence}
    assert symbols_seen == {"SEC_EDGAR", "TWELVE_DATA"}


def test_manual_confirmation_produces_canonical_security() -> None:
    ambiguous_a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Company")
    ambiguous_b = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH",
        exchange_mic=MicCode("XPAR"), country="France", currency=TradingCurrency("EUR"), security_type="COMMON_STOCK",
    )
    result = _service().resolve(ResolutionRequest(investor_ticker="MC", candidates=(ambiguous_a, ambiguous_b)))
    assert result.outcome == "AMBIGUOUS"

    confirmed = _service().confirm_manually(result, chosen_candidate=ambiguous_b, clock=_FIXED_CLOCK)
    assert confirmed.resolution_status == "CANONICAL"
    assert confirmed.canonical_company_name == "LVMH"


def test_manual_confirmation_rejects_candidate_not_in_evidence() -> None:
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    result = _service().resolve(ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)))
    assert result.outcome == "MANUAL_CONFIRMATION"

    foreign_candidate = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MSFT", company_name="Microsoft")
    with pytest.raises(CandidateNotInEvidenceError):
        _service().confirm_manually(result, chosen_candidate=foreign_candidate)


def test_manual_confirmation_rejects_auto_accept_outcome() -> None:
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"), security_type="COMMON_STOCK",
    )
    result = _service().resolve(ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)))
    assert result.outcome == "AUTO_ACCEPT"
    with pytest.raises(ManualConfirmationNotApplicableError):
        _service().confirm_manually(result, chosen_candidate=candidate)


def test_resolution_result_carries_algorithm_version() -> None:
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL")
    result = _service().resolve(ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)))
    assert result.resolution_version == RESOLUTION_ALGORITHM_VERSION


def test_same_request_produces_same_result_deterministic() -> None:
    """Same input, same clock -> the same outcome, confidence, and
    selected candidate every time -- the property `replay.py` depends
    on. `canonical_security.id` is deliberately excluded from this
    comparison: a fresh UUID is assigned on every new-aggregate
    construction (`CanonicalSecurityId`'s own `default_factory=uuid.
    uuid4`, matching `CaseId`'s identical pattern), so two independent
    `resolve()` calls legitimately mint two different ids for what is
    otherwise an identical result -- `replay.py`'s own `verify_replay`
    never asserts id equality either, only outcome/confidence/selected
    candidate."""
    a = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"), security_type="COMMON_STOCK",
    )
    request = ResolutionRequest(investor_ticker="AAPL", candidates=(a,))
    result1 = _service().resolve(request, clock=_FIXED_CLOCK)
    result2 = _service().resolve(request, clock=_FIXED_CLOCK)
    assert result1.outcome == result2.outcome
    assert result1.canonical_security.canonical_company_name == result2.canonical_security.canonical_company_name
    assert result1.canonical_security.native_ticker == result2.canonical_security.native_ticker
    assert result1.canonical_security.resolution_status == result2.canonical_security.resolution_status
    assert result1.canonical_security.listings == result2.canonical_security.listings
    assert [item.confidence for item in result1.evidence] == [item.confidence for item in result2.evidence]


def test_resolve_never_mutates_input_candidates() -> None:
    """Candidates are frozen; this test proves resolve() never
    constructs a modified copy that could be mistaken for mutation."""
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    original_repr = repr(candidate)
    _service().resolve(ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)))
    assert repr(candidate) == original_repr


def test_service_module_never_imports_business_record_or_case() -> None:
    """Structural guarantee, not just a docstring claim -- see
    `service.py`'s own docstring for the full list this proves. Checks
    actual `import`/`from ... import` statements via `ast`, not a raw
    text search -- `service.py`'s own docstring names these modules in
    prose to explain the guarantee, which a plain substring search would
    misread as a violation of the very thing it describes."""
    import ast

    import atlas.alpha.canonical_security_resolution.service as service_module

    tree = ast.parse(open(service_module.__file__, encoding="utf-8").read())
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    for forbidden in (
        "atlas.analysis_engine.business_data",
        "atlas.alpha.business_data_refresh",
        "atlas.core.domain.case",
        "atlas.alpha.case_generation",
    ):
        assert not any(module.startswith(forbidden) for module in imported_modules), forbidden

"""Resolution Outcome tests -- Sprint N Phase 6."""
from __future__ import annotations

import pytest

from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.outcomes import (
    UnsupportedResolutionOutcomeError,
    determine_outcome,
    validate_resolution_outcome,
)
from atlas.alpha.canonical_security_resolution.provider_agreement import evaluate_provider_agreement


def test_validate_resolution_outcome_closed_allow_list() -> None:
    assert validate_resolution_outcome("AUTO_ACCEPT") == "AUTO_ACCEPT"
    with pytest.raises(UnsupportedResolutionOutcomeError):
        validate_resolution_outcome("MAYBE")


def test_no_match_on_empty_candidates() -> None:
    agreement = evaluate_provider_agreement(())
    outcome, candidate = determine_outcome((), (), agreement)
    assert outcome == "NO_MATCH"
    assert candidate is None


def test_ambiguous_takes_priority_over_conflict_candidates() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Company")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH")
    agreement = evaluate_provider_agreement((a, b))
    outcome, candidate = determine_outcome((a, b), ("REJECTED", "HIGH"), agreement)
    assert outcome == "AMBIGUOUS"
    assert candidate is None


def test_auto_accept_requires_constructible_candidate() -> None:
    """A HIGH-confidence candidate missing a field CanonicalSecurity
    construction requires (the exchange, here) is downgraded to
    MANUAL_CONFIRMATION rather than crashing or fabricating a value."""
    incomplete = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        country="United States", security_type="COMMON_STOCK",
        currency=TradingCurrency("USD"),
        # exchange_mic deliberately omitted -- without a venue there is no
        # security, only a ticker, and a ticker is what cannot tell
        # Schneider Electric from Suncor Energy.
    )
    agreement = evaluate_provider_agreement((incomplete,))
    outcome, candidate = determine_outcome((incomplete,), ("HIGH",), agreement)
    assert outcome == "MANUAL_CONFIRMATION"
    assert candidate is incomplete


def test_a_missing_currency_no_longer_blocks_construction() -> None:
    """Currency is not identity. A provider that knows exactly which
    security this is -- company, venue, country -- can create it even
    when nothing has yet proven what the listing quotes in; the security
    is then recorded with an unproven currency, and valuation goes on
    withholding on its own currency evidence, which is where that
    question actually belongs.

    This is what kept every Stockholm and Paris holding unidentifiable.
    """
    without_currency = ProviderCandidate(
        provider_name="OPENFIGI", symbol="VOLV-B", company_name="Volvo AB",
        exchange_mic=MicCode("XSTO"), country="Sweden", security_type="COMMON_STOCK",
        # currency deliberately omitted
    )
    agreement = evaluate_provider_agreement((without_currency,))
    outcome, candidate = determine_outcome((without_currency,), ("HIGH",), agreement)
    assert outcome == "AUTO_ACCEPT"
    assert candidate is without_currency


@pytest.mark.parametrize(
    "missing",
    [
        {"company_name": None},
        {"exchange_mic": None},
        {"country": None},
    ],
)
def test_identity_fields_are_still_required(missing) -> None:
    """Company, venue and country remain mandatory -- dropping currency
    from the rule must not have loosened the rest of it."""
    fields = dict(
        provider_name="OPENFIGI", symbol="VOLV-B", company_name="Volvo AB",
        exchange_mic=MicCode("XSTO"), country="Sweden", security_type="COMMON_STOCK",
        currency=TradingCurrency("SEK"),
    )
    fields.update(missing)
    candidate = ProviderCandidate(**fields)
    agreement = evaluate_provider_agreement((candidate,))
    outcome, _ = determine_outcome((candidate,), ("HIGH",), agreement)
    assert outcome == "MANUAL_CONFIRMATION"


def test_auto_accept_with_fully_constructible_high_confidence_candidate() -> None:
    complete = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", security_type="COMMON_STOCK",
        currency=TradingCurrency("USD"),
    )
    agreement = evaluate_provider_agreement((complete,))
    outcome, candidate = determine_outcome((complete,), ("HIGH",), agreement)
    assert outcome == "AUTO_ACCEPT"
    assert candidate is complete


def test_reject_on_single_rejected_candidate_no_conflict() -> None:
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="EVO", company_name="Evotec SE")
    agreement = evaluate_provider_agreement((candidate,))
    outcome, selected = determine_outcome((candidate,), ("REJECTED",), agreement)
    assert outcome == "REJECT"
    assert selected is None


def test_low_confidence_outcome() -> None:
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="XYZ")
    agreement = evaluate_provider_agreement((candidate,))
    outcome, selected = determine_outcome((candidate,), ("LOW",), agreement)
    assert outcome == "LOW_CONFIDENCE"
    assert selected is candidate


def test_manual_confirmation_outcome() -> None:
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    agreement = evaluate_provider_agreement((candidate,))
    outcome, selected = determine_outcome((candidate,), ("MEDIUM",), agreement)
    assert outcome == "MANUAL_CONFIRMATION"
    assert selected is candidate


def test_an_auto_accepted_candidate_can_actually_be_built() -> None:
    """The gap the previous sprint left between the two ends of this.

    `_is_constructible` stopped requiring a currency, so a Stockholm
    candidate reached `AUTO_ACCEPT` -- and `_build_or_extend` then
    asserted the currency was present and crashed on the very candidate
    the outcome had just accepted. Both halves were tested and passed;
    nothing tested them joined together, which is where every Stockholm
    holding actually died.

    Constructibility is a promise about what the next step can build, so
    it is only worth anything if the next step is the one asked.
    """
    from atlas.alpha.canonical_security_resolution.service import (
        CanonicalSecurityResolutionService,
        ResolutionRequest,
    )

    candidate = ProviderCandidate(
        provider_name="OPENFIGI", symbol="VOLV-B", company_name="VOLVO AB-B SHS",
        exchange_mic=MicCode("XSTO"), country="Sweden", security_type="COMMON_STOCK",
        # currency deliberately omitted -- no identity provider returns one
    )
    agreement = evaluate_provider_agreement((candidate,))
    outcome, _ = determine_outcome((candidate,), ("HIGH",), agreement)
    assert outcome == "AUTO_ACCEPT"

    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="VOLV-B", candidates=(candidate,))
    )
    security = result.canonical_security
    assert security is not None
    assert security.resolution_status == "CANONICAL"
    assert security.trading_currency is None
    # CANONICAL requires a listing, so the listing must survive the missing
    # currency too -- a venue is what makes a listing, not a currency.
    assert [(l.exchange_mic.value, l.currency) for l in security.listings] == [("XSTO", None)]

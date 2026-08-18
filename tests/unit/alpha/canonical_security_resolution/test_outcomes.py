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
    construction requires (currency, here) is downgraded to
    MANUAL_CONFIRMATION rather than crashing or fabricating a value."""
    incomplete = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", security_type="COMMON_STOCK",
        # currency deliberately omitted
    )
    agreement = evaluate_provider_agreement((incomplete,))
    outcome, candidate = determine_outcome((incomplete,), ("HIGH",), agreement)
    assert outcome == "MANUAL_CONFIRMATION"
    assert candidate is incomplete


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

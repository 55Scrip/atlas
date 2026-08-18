"""JSON serialization round-trip tests -- Sprint N Phase 15."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.comparison import FieldComparison
from atlas.alpha.canonical_security_resolution.serialization import (
    candidate_from_json_dict,
    candidate_to_json_dict,
    comparison_from_json_dict,
    comparison_to_json_dict,
    comparisons_from_json,
    comparisons_to_json,
    evidence_from_json_dict,
    evidence_to_json_dict,
    resolution_result_to_json_dict,
)
from atlas.alpha.canonical_security_resolution.service import (
    CanonicalSecurityResolutionService,
    ResolutionEvidence,
    ResolutionRequest,
)

_FIXED_CLOCK = lambda: datetime(2026, 8, 18, tzinfo=timezone.utc)  # noqa: E731


def test_candidate_round_trip_full_fields() -> None:
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA",
        symbol="MC",
        provider_security_id="12345",
        exchange_mic=MicCode("XPAR"),
        exchange_display_name="Euronext Paris",
        country="France",
        currency=TradingCurrency("EUR"),
        company_name="LVMH",
        security_type="COMMON_STOCK",
        listing_relationship="NATIVE",
        isin="FR0000121014",
        figi="BBG000BPXBQ8",
        cusip=None,
        sedol=None,
        provider_confidence="HIGH",
        raw_metadata={"source": "test"},
    )
    round_tripped = candidate_from_json_dict(candidate_to_json_dict(candidate))
    assert round_tripped == candidate


def test_candidate_round_trip_minimal_fields() -> None:
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL")
    round_tripped = candidate_from_json_dict(candidate_to_json_dict(candidate))
    assert round_tripped == candidate


def test_comparison_round_trip() -> None:
    comparison = FieldComparison(field_name="company_name", agrees=False, left_value="A", right_value="B")
    round_tripped = comparison_from_json_dict(comparison_to_json_dict(comparison))
    assert round_tripped == comparison


def test_comparisons_json_round_trip_preserves_order() -> None:
    comparisons = (
        FieldComparison("company_name", True, "X", "X"),
        FieldComparison("country", None, None, "France"),
        FieldComparison("exchange_mic", False, "XPAR", "XNYS"),
    )
    round_tripped = comparisons_from_json(comparisons_to_json(comparisons))
    assert round_tripped == comparisons


def test_evidence_round_trip() -> None:
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    evidence = ResolutionEvidence(
        candidate=candidate, confidence="MEDIUM",
        comparisons_against_existing=(FieldComparison("country", True, "US", "US"),), accepted=False,
    )
    round_tripped = evidence_from_json_dict(evidence_to_json_dict(evidence))
    assert round_tripped == evidence


def test_resolution_result_json_dict_deterministic_key_order() -> None:
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"), security_type="COMMON_STOCK",
    )
    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)), clock=_FIXED_CLOCK
    )
    data = resolution_result_to_json_dict(result)
    assert list(data.keys()) == [
        "outcome", "canonicalSecurityId", "selectedCandidate", "evidence",
        "normalizedCompanyText", "normalizedTicker", "resolvedAt", "resolutionVersion",
    ]
    assert data["outcome"] == "AUTO_ACCEPT"
    assert data["canonicalSecurityId"] is not None


def test_evidence_order_preserved_in_result_json() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Company")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH")
    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="MC", candidates=(a, b)), clock=_FIXED_CLOCK
    )
    data = resolution_result_to_json_dict(result)
    provider_order = [item["candidate"]["providerName"] for item in data["evidence"]]
    assert provider_order == ["SEC_EDGAR", "TWELVE_DATA"]

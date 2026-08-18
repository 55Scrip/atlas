"""JSON serialization for `ProviderCandidate`, `FieldComparison`,
`ResolutionEvidence`, and `ResolutionResult` -- Sprint N Phase 15.

Deterministic ordering throughout: every dict below is built with a
fixed, explicit key order (never derived from set/dict iteration over
unordered input), and every list (`evidence`, `comparisons`) preserves
the exact sequence the resolution algorithm produced it in -- this is
what lets `repository.py` and `replay.py` round-trip a resolution
without silently reordering candidates, which would itself break
`determine_outcome`'s index-aligned `confidences` contract
(`outcomes.py`'s own docstring on why it uses index alignment rather
than dict-keying).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.comparison import FieldComparison
from atlas.alpha.canonical_security_resolution.service import ResolutionEvidence, ResolutionResult


def candidate_to_json_dict(candidate: ProviderCandidate) -> dict[str, Any]:
    return {
        "providerName": candidate.provider_name,
        "symbol": candidate.symbol,
        "providerSecurityId": candidate.provider_security_id,
        "exchangeMic": candidate.exchange_mic.value if candidate.exchange_mic else None,
        "exchangeDisplayName": candidate.exchange_display_name,
        "country": candidate.country,
        "currency": candidate.currency.value if candidate.currency else None,
        "companyName": candidate.company_name,
        "securityType": candidate.security_type,
        "listingRelationship": candidate.listing_relationship,
        "isin": candidate.isin,
        "figi": candidate.figi,
        "cusip": candidate.cusip,
        "sedol": candidate.sedol,
        "providerConfidence": candidate.provider_confidence,
        "rawMetadata": dict(sorted(candidate.raw_metadata.items())),
    }


def candidate_from_json_dict(data: dict[str, Any]) -> ProviderCandidate:
    return ProviderCandidate(
        provider_name=data["providerName"],
        symbol=data["symbol"],
        provider_security_id=data["providerSecurityId"],
        exchange_mic=MicCode(data["exchangeMic"]) if data["exchangeMic"] else None,
        exchange_display_name=data["exchangeDisplayName"],
        country=data["country"],
        currency=TradingCurrency(data["currency"]) if data["currency"] else None,
        company_name=data["companyName"],
        security_type=data["securityType"],
        listing_relationship=data["listingRelationship"],
        isin=data["isin"],
        figi=data["figi"],
        cusip=data["cusip"],
        sedol=data["sedol"],
        provider_confidence=data["providerConfidence"],
        raw_metadata=data["rawMetadata"],
    )


def comparison_to_json_dict(comparison: FieldComparison) -> dict[str, Any]:
    return {
        "fieldName": comparison.field_name,
        "agrees": comparison.agrees,
        "leftValue": comparison.left_value,
        "rightValue": comparison.right_value,
    }


def comparison_from_json_dict(data: dict[str, Any]) -> FieldComparison:
    return FieldComparison(
        field_name=data["fieldName"], agrees=data["agrees"], left_value=data["leftValue"], right_value=data["rightValue"]
    )


def comparisons_to_json(comparisons: tuple[FieldComparison, ...]) -> str:
    return json.dumps([comparison_to_json_dict(c) for c in comparisons])


def comparisons_from_json(raw: str) -> tuple[FieldComparison, ...]:
    return tuple(comparison_from_json_dict(item) for item in json.loads(raw))


def evidence_to_json_dict(evidence: ResolutionEvidence) -> dict[str, Any]:
    return {
        "candidate": candidate_to_json_dict(evidence.candidate),
        "confidence": evidence.confidence,
        "comparisonsAgainstExisting": [comparison_to_json_dict(c) for c in evidence.comparisons_against_existing],
        "accepted": evidence.accepted,
    }


def evidence_from_json_dict(data: dict[str, Any]) -> ResolutionEvidence:
    return ResolutionEvidence(
        candidate=candidate_from_json_dict(data["candidate"]),
        confidence=data["confidence"],
        comparisons_against_existing=tuple(
            comparison_from_json_dict(item) for item in data["comparisonsAgainstExisting"]
        ),
        accepted=data["accepted"],
    )


def resolution_result_to_json_dict(result: ResolutionResult) -> dict[str, Any]:
    return {
        "outcome": result.outcome,
        "canonicalSecurityId": str(result.canonical_security.id) if result.canonical_security else None,
        "selectedCandidate": candidate_to_json_dict(result.selected_candidate) if result.selected_candidate else None,
        "evidence": [evidence_to_json_dict(item) for item in result.evidence],
        "normalizedCompanyText": result.normalized_company_text,
        "normalizedTicker": result.normalized_ticker,
        "resolvedAt": result.resolved_at.isoformat(),
        "resolutionVersion": result.resolution_version,
    }

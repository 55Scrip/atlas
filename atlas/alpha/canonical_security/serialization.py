"""JSON serialization for `CanonicalSecurity` -- Sprint M Phase 9.

Kept separate from `repository.py`'s own row (de)serialization
(`_root_to_row`/`_row_to_security`), which targets SQL column shapes
specifically. This module targets a plain, `json.dumps`-safe `dict` --
the shape a future API layer would actually return, distinct from a SQL
row shape even though both ultimately derive from the same aggregate
fields. Round-trip tests (`tests/unit/alpha/canonical_security/
test_serialization.py`) confirm `from_json_dict(to_json_dict(x)) == x`
for every field, including nested listings/mappings/identifiers.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from atlas.alpha.canonical_security.models import (
    CanonicalSecurity,
    ListingRef,
    ProviderMapping,
    SecurityIdentifier,
)
from atlas.alpha.canonical_security.value_objects import (
    CanonicalSecurityId,
    MicCode,
    TradingCurrency,
)


def to_json_dict(security: CanonicalSecurity) -> dict[str, Any]:
    return {
        "id": str(security.id),
        "canonicalCompanyName": security.canonical_company_name,
        "nativeTicker": security.native_ticker,
        "primaryExchangeMic": security.primary_exchange_mic.value,
        "country": security.country,
        "tradingCurrency": security.trading_currency.value,
        "resolutionStatus": security.resolution_status,
        "listings": [_listing_to_dict(listing) for listing in security.listings],
        "providerMappings": [_mapping_to_dict(mapping) for mapping in security.provider_mappings],
        "identifiers": [_identifier_to_dict(identifier) for identifier in security.identifiers],
        "createdAt": security.created_at.isoformat(),
        "updatedAt": security.updated_at.isoformat(),
    }


def from_json_dict(data: dict[str, Any]) -> CanonicalSecurity:
    return CanonicalSecurity(
        id=CanonicalSecurityId(uuid.UUID(data["id"])),
        canonical_company_name=data["canonicalCompanyName"],
        native_ticker=data["nativeTicker"],
        primary_exchange_mic=MicCode(data["primaryExchangeMic"]),
        country=data["country"],
        trading_currency=TradingCurrency(data["tradingCurrency"]),
        resolution_status=data["resolutionStatus"],
        listings=tuple(_listing_from_dict(item) for item in data["listings"]),
        provider_mappings=tuple(_mapping_from_dict(item) for item in data["providerMappings"]),
        identifiers=tuple(_identifier_from_dict(item) for item in data["identifiers"]),
        created_at=datetime.fromisoformat(data["createdAt"]),
        updated_at=datetime.fromisoformat(data["updatedAt"]),
    )


def _listing_to_dict(listing: ListingRef) -> dict[str, Any]:
    return {
        "ticker": listing.ticker,
        "exchangeMic": listing.exchange_mic.value,
        "currency": listing.currency.value,
        "relationship": listing.relationship,
        "securityType": listing.security_type,
        "providerSymbol": listing.provider_symbol,
    }


def _listing_from_dict(data: dict[str, Any]) -> ListingRef:
    return ListingRef(
        ticker=data["ticker"],
        exchange_mic=MicCode(data["exchangeMic"]),
        currency=TradingCurrency(data["currency"]),
        relationship=data["relationship"],
        security_type=data["securityType"],
        provider_symbol=data["providerSymbol"],
    )


def _mapping_to_dict(mapping: ProviderMapping) -> dict[str, Any]:
    return {
        "providerName": mapping.provider_name,
        "providerTicker": mapping.provider_ticker,
        "confidence": mapping.confidence,
        "verificationStatus": mapping.verification_status,
        "mappedAt": mapping.mapped_at.isoformat(),
        "providerSecurityId": mapping.provider_security_id,
        "providerExchangeCode": mapping.provider_exchange_code,
        "verifiedAt": mapping.verified_at.isoformat() if mapping.verified_at is not None else None,
    }


def _mapping_from_dict(data: dict[str, Any]) -> ProviderMapping:
    return ProviderMapping(
        provider_name=data["providerName"],
        provider_ticker=data["providerTicker"],
        confidence=data["confidence"],
        verification_status=data["verificationStatus"],
        mapped_at=datetime.fromisoformat(data["mappedAt"]),
        provider_security_id=data["providerSecurityId"],
        provider_exchange_code=data["providerExchangeCode"],
        verified_at=datetime.fromisoformat(data["verifiedAt"]) if data["verifiedAt"] is not None else None,
    )


def _identifier_to_dict(identifier: SecurityIdentifier) -> dict[str, Any]:
    return {
        "identifierType": identifier.identifier_type,
        "value": identifier.value,
        "recordedAt": identifier.recorded_at.isoformat(),
    }


def _identifier_from_dict(data: dict[str, Any]) -> SecurityIdentifier:
    return SecurityIdentifier(
        identifier_type=data["identifierType"],
        value=data["value"],
        recorded_at=datetime.fromisoformat(data["recordedAt"]),
    )

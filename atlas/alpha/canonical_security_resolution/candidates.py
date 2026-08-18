"""`ProviderCandidate` -- Sprint N Phase 4. A provider-neutral raw
identity claim: exactly what a provider returned for a lookup, before
any Atlas-side judgment is applied. No Twelve Data-specific (or any
other provider-specific) logic exists here or anywhere in this module --
every field is generic across the `ProviderName` vocabulary Sprint M
already established (`SEC_EDGAR`, `ALPHA_VANTAGE`, `TWELVE_DATA`,
`OPENFIGI`), and adding a fifth provider requires no change to this
class at all.

Frozen, matching every other value object in this codebase. `raw_metadata`
is a plain `Mapping[str, str]`, the same lightness-of-enforcement already
used by `atlas.analysis_engine.business_data.models.BusinessRecord.
metadata` -- not deep-frozen, but never mutated by anything in this
package (`resolve()` never writes to a candidate's `raw_metadata`, only
reads it for evidence persistence).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from atlas.alpha.canonical_security.value_objects import (
    IdentityConfidence,
    ListingRelationship,
    MicCode,
    ProviderName,
    SecurityType,
    TradingCurrency,
)
from atlas.alpha.canonical_security_resolution.exceptions import EmptySymbolError


@dataclass(frozen=True)
class ProviderCandidate:
    """One provider's raw claim about a security's identity.

    Only `provider_name` and `symbol` are required -- every identity
    field below is optional, since real providers routinely return
    partial data (Sprint H/I confirmed SEC EDGAR carries no exchange
    field at all, and Twelve Data's own responses vary in which
    identifiers are populated per symbol). The resolution algorithm
    (`comparison.py`, `confidence.py`) is built to work correctly with
    however many of these fields are actually present -- see
    `confidence.py`'s own "ticker alone is never sufficient" rule.
    """

    provider_name: ProviderName
    symbol: str
    provider_security_id: str | None = None
    exchange_mic: MicCode | None = None
    exchange_display_name: str | None = None
    country: str | None = None
    currency: TradingCurrency | None = None
    company_name: str | None = None
    security_type: SecurityType | None = None
    listing_relationship: ListingRelationship | None = None
    isin: str | None = None
    figi: str | None = None
    cusip: str | None = None
    sedol: str | None = None
    provider_confidence: IdentityConfidence | None = None
    raw_metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise EmptySymbolError()

    def corroborating_field_count(self) -> int:
        """How many identity-bearing fields beyond `symbol` this
        candidate actually carries -- used by `confidence.py`'s
        ticker-alone rule (Sprint N Phase 7): a candidate with zero
        corroborating fields can never reach `HIGH` confidence,
        regardless of how confidently a provider's API responded."""
        fields = (
            self.exchange_mic,
            self.country,
            self.company_name,
            self.security_type,
            self.listing_relationship,
            self.isin,
            self.figi,
            self.cusip,
            self.sedol,
        )
        return sum(1 for value in fields if value is not None)

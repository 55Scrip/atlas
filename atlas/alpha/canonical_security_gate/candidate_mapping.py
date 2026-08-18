"""`RawBusinessDocument` -> `ProviderCandidate` mapping -- Sprint O
Phase 3.

The one deterministic translation from "whatever a provider's raw
`COMPANY_PROFILE` document happens to carry in `metadata`" to Sprint
N's `ProviderCandidate` shape, so the identity gate can call
`CanonicalSecurityResolutionService.resolve()` with real evidence
rather than nothing.

Reads only `SourceKind.COMPANY_PROFILE` documents --
`FINANCIAL_STATEMENT`/`MARKET_DATA_SNAPSHOT` documents carry no
identity fields for either currently-wired provider (confirmed: SEC
EDGAR's own CIK resolution reads a company `title` from
`company_tickers.json` but its `_ticker_to_cik` cache discards it,
keeping only ticker->CIK; Alpha Vantage's `fetch`/
`fetch_historical_snapshots` calls return price/shares/currency only,
never identity) and are never handed to this mapper by
`refresh_company_data`.

**No provider adapter is touched or imported by name here.** Only
`provider_id` (a plain string already on every `RawBusinessDocument`)
selects the provider-name mapping below -- adding a fifth provider
later means adding one entry to `_PROVIDER_ID_TO_NAME`, never changing
this module's logic, and this module never imports
`atlas.business_data_providers.*`.

**Honest about what today's real providers can supply.**
`security_type` is read from an optional, generic `"security_type"`
metadata key if a provider happens to populate it -- neither shipped
provider adapter does today (confirmed via `alpha_vantage.py`'s own
`_IDENTITY_FIELD_MAP`, which has no such key, and SEC EDGAR supplies no
identity metadata at all). A real Alpha Vantage-derived candidate built
here therefore always has `security_type=None`. This is not a bug in
this mapper -- see the Sprint O readiness assessment
(`docs/canonical_security_identity_gate.md`) for what that means for
`calculate_confidence`'s own HIGH-confidence rule, and why it is an
honest, structural finding rather than something this mapper should
work around by inventing a value.
"""
from __future__ import annotations

from atlas.alpha.canonical_security.exceptions import InvalidTradingCurrencyError
from atlas.alpha.canonical_security.value_objects import (
    MicCode,
    ProviderName,
    SecurityType,
    TradingCurrency,
    validate_security_type,
)
from atlas.alpha.canonical_security_gate.exchange_mapping import map_exchange_display_name_to_mic
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["candidates_from_documents"]

#: Closed, additive mapping from `RawBusinessDocument.provider_id`
#: (the plain string every provider adapter already stamps on its own
#: documents) to Sprint M's `ProviderName` vocabulary. Adding a fifth
#: provider is exactly one new entry here -- never a change to the
#: mapping logic below.
_PROVIDER_ID_TO_NAME: dict[str, ProviderName] = {
    "alpha_vantage": "ALPHA_VANTAGE",
    "sec_edgar": "SEC_EDGAR",
}


def candidates_from_documents(documents: tuple[RawBusinessDocument, ...]) -> tuple[ProviderCandidate, ...]:
    candidates: list[ProviderCandidate] = []
    for document in documents:
        if document.source_kind != SourceKind.COMPANY_PROFILE.value:
            continue
        candidate = _candidate_from_profile_document(document)
        if candidate is not None:
            candidates.append(candidate)
    return tuple(candidates)


def _candidate_from_profile_document(document: RawBusinessDocument) -> ProviderCandidate | None:
    if document.provider_id is None or document.company is None:
        return None
    provider_name = _PROVIDER_ID_TO_NAME.get(document.provider_id)
    if provider_name is None:
        return None

    metadata = document.metadata
    company_name = _clean_str(metadata.get("name"))
    country = _clean_str(metadata.get("country"))
    exchange_display_name = _clean_str(metadata.get("exchange"))
    exchange_mic: MicCode | None = map_exchange_display_name_to_mic(exchange_display_name)
    currency = _parse_currency(_clean_str(metadata.get("currency")))
    security_type = _parse_security_type(_clean_str(metadata.get("security_type")))

    return ProviderCandidate(
        provider_name=provider_name,
        symbol=document.company,
        exchange_mic=exchange_mic,
        exchange_display_name=exchange_display_name,
        country=country,
        currency=currency,
        company_name=company_name,
        security_type=security_type,
        raw_metadata={key: str(value) for key, value in metadata.items() if value is not None},
    )


def _parse_currency(raw: str | None) -> TradingCurrency | None:
    if raw is None:
        return None
    try:
        return TradingCurrency(raw)
    except InvalidTradingCurrencyError:
        return None


def _parse_security_type(raw: str | None) -> SecurityType | None:
    if raw is None:
        return None
    try:
        return validate_security_type(raw)
    except Exception:  # noqa: BLE001 -- any unrecognized value is honestly omitted, never guessed
        return None


def _clean_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None

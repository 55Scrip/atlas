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

**Sprint O.1: `security_type` now has two possible sources.** An
optional, generic `"security_type"` metadata key is read first, exactly
as before -- any provider that already supplies an exact, canonical
`SecurityType` string (`"COMMON_STOCK"`/`"DEPOSITARY_RECEIPT"`/
`"ETF"`/`"OTHER"`) directly continues to work completely unchanged, and
an unrecognized value there is still honestly omitted (`None`), never
guessed. Falling back only when that key is absent, Alpha Vantage's
real `OVERVIEW.AssetType` field (extracted, untranslated, into
`metadata["asset_type"]` by `alpha_vantage.py`'s own
`_IDENTITY_FIELD_MAP` as of Sprint O.1) is translated through a small,
closed, deterministic lookup table (`_ASSET_TYPE_TRANSLATION`, below)
-- exact-string matching only, no fuzzy matching, no inference. A
recognized display string (`"Common Stock"`, `"ETF"`, `"Depositary
Receipt"`) maps to its named `SecurityType`; any other non-blank
`AssetType` value Atlas has not seen before maps to `"OTHER"` --
itself a real, closed-vocabulary member meaning exactly "a security
type Alpha Vantage did report, that Atlas has not specifically
categorized," never a fabricated guess at what the security actually
is. This is Sprint O's own honest finding corrected, not superseded:
Sprint O found `_IDENTITY_FIELD_MAP` had no `security_type`/`AssetType`
entry at all; Sprint O.1's live-documentation verification found
`AssetType` was present in the real API response the whole time and
simply discarded -- see the Sprint O readiness assessment
(`docs/canonical_security_identity_gate.md`) for the full correction.
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

#: Sprint O.1 -- closed, deterministic translation from Alpha Vantage's
#: real `OVERVIEW.AssetType` display string to Atlas' closed
#: `SecurityType` vocabulary. Exact-string lookup only. Any value not
#: explicitly listed here (a real Alpha Vantage value Atlas has not
#: seen before, e.g. `"Preferred Stock"`) deterministically falls
#: through to `"OTHER"`, below -- never `None`, since the provider did
#: genuinely report *some* asset type; `"OTHER"` says exactly that,
#: honestly, without inventing which specific category it is.
_ASSET_TYPE_TRANSLATION: dict[str, SecurityType] = {
    "Common Stock": "COMMON_STOCK",
    "ETF": "ETF",
    "Depositary Receipt": "DEPOSITARY_RECEIPT",
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
    if security_type is None:
        security_type = _translate_asset_type(_clean_str(metadata.get("asset_type")))

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


def _translate_asset_type(raw: str | None) -> SecurityType | None:
    """Sprint O.1 -- `raw` is Alpha Vantage's own `AssetType` display
    string, never an already-canonical value (that path is
    `_parse_security_type`, above, checked first). `None` only when no
    `AssetType` was supplied at all; a supplied-but-unrecognized value
    deterministically becomes `"OTHER"`, never `None` -- see this
    module's own docstring for why that is honest, not a guess."""
    if raw is None:
        return None
    return _ASSET_TYPE_TRANSLATION.get(raw, "OTHER")


def _clean_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None

"""Shared SEC EDGAR ticker->CIK identity resolution (Automatic Knowledge
Ingestion Framework, Foundation Provider).

Extracted from `SecEdgarFundamentalsProvider` so a second SEC-sourced
provider (`SecEdgarFilingHistoryProvider`) can reuse the identical,
already-live, already-cached ticker->CIK resolution rather than
duplicating it. `SecEdgarFundamentalsProvider`'s own public behavior is
unchanged by this extraction -- it now holds a `SecEdgarIdentity`
instance internally instead of the same logic inlined, nothing else.
"""
from __future__ import annotations

import os

from atlas.business_data_providers.errors import CompanyNotFound, MalformedProviderResponse
from atlas.business_data_providers.http import JsonFetcher, fetch_json

__all__ = ["SecEdgarIdentity", "sec_ticker_candidates", "sec_user_agent"]

_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"

#: SEC's fair-access policy requires every automated caller to
#: identify itself as "company name + contact email" -- not a secret,
#: not authentication, but confirmed live to be strictly enforced: a
#: `User-Agent` without an email-shaped contact gets a genuine `403`,
#: not just a polite warning. Override with a real contact via
#: `ATLAS_SEC_EDGAR_USER_AGENT`.
_DEFAULT_USER_AGENT = "Atlas Investment OS admin@atlas-investment-os.local (set ATLAS_SEC_EDGAR_USER_AGENT)"


def sec_user_agent() -> str:
    return os.environ.get("ATLAS_SEC_EDGAR_USER_AGENT", _DEFAULT_USER_AGENT)


def sec_ticker_candidates(ticker: str) -> tuple[str, ...]:
    """Provider-local normalization only -- Atlas's own ticker identity
    is never changed by this; only the candidate strings tried against
    SEC's own ticker map. SEC's `company_tickers.json` commonly uses a
    hyphen where Atlas (and most retail-facing data) uses a dot for
    multi-class tickers -- confirmed live: Atlas's `BRK.B` has no entry
    in SEC's map, but `BRK-B` does. Tried in order; the exact ticker
    always wins first so an already-SEC-format ticker never pays for a
    wasted lookup or behaves differently."""
    upper = ticker.upper()
    candidates = [upper]
    if "." in upper:
        candidates.append(upper.replace(".", "-"))
    return tuple(candidates)


class SecEdgarIdentity:
    """Ticker->CIK resolution, shared across every SEC EDGAR-sourced
    provider. One instance per provider (each provider keeps its own
    cache, the same isolation `SecEdgarFundamentalsProvider` already
    had before this extraction -- two providers never share a mutable
    cache instance, avoiding any cross-provider coupling)."""

    def __init__(self, fetch_json_fn: JsonFetcher | None = None, *, ticker_cik_map: dict[str, str] | None = None) -> None:
        self._fetch_json = fetch_json_fn or fetch_json
        self._ticker_cik_cache: dict[str, str] | None = ticker_cik_map

    def headers(self) -> dict[str, str]:
        return {"User-Agent": sec_user_agent()}

    def fetch_json(self, url: str) -> object:
        return self._fetch_json(url, self.headers())

    def _ticker_to_cik(self) -> dict[str, str]:
        if self._ticker_cik_cache is not None:
            return self._ticker_cik_cache
        payload = self._fetch_json(_TICKER_MAP_URL, self.headers())
        if not isinstance(payload, dict):
            raise MalformedProviderResponse("SEC ticker map response was not a JSON object")
        mapping: dict[str, str] = {}
        for entry in payload.values():
            ticker = entry.get("ticker") if isinstance(entry, dict) else None
            cik = entry.get("cik_str") if isinstance(entry, dict) else None
            if isinstance(ticker, str) and cik is not None:
                mapping[ticker.upper()] = f"{int(cik):010d}"
        self._ticker_cik_cache = mapping
        return mapping

    def resolve_cik(self, company_identifier: str) -> str:
        mapping = self._ticker_to_cik()
        for candidate in sec_ticker_candidates(company_identifier):
            cik = mapping.get(candidate)
            if cik is not None:
                return cik
        raise CompanyNotFound(f"{company_identifier!r} did not resolve to any SEC-registered filer")

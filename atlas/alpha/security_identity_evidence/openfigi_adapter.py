"""Real OpenFIGI `POST /v3/mapping` adapter (Sprint 23 Phase 6).

Live-verified against OpenFIGI's own current public documentation
during this sprint's investigation (no OpenFIGI code existed anywhere
in this repository before now -- Sprint 18 only ever *researched*
FIGI feasibility, never built a client; see
`atlas.alpha.security_discovery.__init__`'s own citation of that
finding). Confirmed real behavior this sprint relied on:

- Request: `POST https://api.openfigi.com/v3/mapping` with a JSON
  array body, one object per lookup: `{"idType": "TICKER", "idValue":
  "MSFT", "exchCode": "US"}`.
- No API key is required for basic use (25 requests/minute, 10 jobs
  per request); an optional `X-OPENFIGI-APIKEY` header raises those
  limits (25 req/6s, 100 jobs/request) -- this adapter sends the key
  only when `ATLAS_OPENFIGI_API_KEY` is set, mirroring
  `atlas.alpha.security_discovery.sec_source`'s own optional-env-var
  pattern for `ATLAS_SEC_EDGAR_USER_AGENT`.
- A ticker with **no match** still returns HTTP 200, with a `warning`
  string in place of a `data` array -- this is not an error and must
  not be treated as `provider_unavailable`.
- A ticker with **multiple matches** returns HTTP 200 with multiple
  entries in `data` -- Atlas cannot honestly pick one (see
  `models.py`'s own `"ambiguous"` status).
- Response fields actually present on each `data` entry: `figi`,
  `securityType`, `marketSector`, `ticker`, `name`, `exchCode`,
  `shareClassFIGI`, `compositeFIGI`, `securityType2`,
  `securityDescription`. No `currency` or `shareClass` (plain, not
  FIGI) field exists on this endpoint -- `models.py` deliberately does
  not carry either, matching `security_discovery.models`'s own
  discipline of never fabricating a field a provider does not actually
  return.

Does NOT reuse `atlas.business_data_providers.http.fetch_json` --
same reasoning as `security_discovery.sec_source`: that package is
architecturally reserved for exactly one caller
(`atlas.alpha.business_data_refresh`), and this endpoint needs a JSON
POST body that helper does not support in any case.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

import httpx

_MAPPING_URL = "https://api.openfigi.com/v3/mapping"
_TIMEOUT_SECONDS = 10.0
_DEFAULT_EXCHANGE_CODE = "US"

#: `(url, body, headers) -> parsed JSON`. Local to this module, mirroring
#: `security_discovery.sec_source.JsonFetcher`'s own reasoning for not
#: sharing a type with `atlas.business_data_providers`.
JsonPoster = Callable[[str, "list[dict[str, Any]]", "dict[str, str]"], Any]


class OpenFigiProviderUnavailable(Exception):
    """A genuine infrastructure failure (network, timeout, HTTP 4xx/5xx
    other than the provider's own normal "no match" 200 response) --
    never raised for a ticker that simply has no or multiple matches,
    which are both ordinary 200 responses (see module docstring)."""


@dataclass(frozen=True)
class OpenFigiMatch:
    figi: str
    ticker: str | None
    name: str | None
    exch_code: str | None
    security_type: str | None
    market_sector: str | None


@dataclass(frozen=True)
class OpenFigiMappingResult:
    """`matches` is empty exactly when the provider's own response
    carried a `warning` (no identifier found) -- a real, honest zero,
    never conflated with a provider failure."""

    matches: tuple[OpenFigiMatch, ...]


def _api_key() -> str | None:
    return os.environ.get("ATLAS_OPENFIGI_API_KEY")


def _post_json(url: str, body: list[dict[str, Any]], headers: dict[str, str]) -> Any:
    try:
        response = httpx.post(url, json=body, headers=headers, timeout=_TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise OpenFigiProviderUnavailable(f"Request to {url} failed: {exc}") from exc
    if response.status_code >= 400:
        raise OpenFigiProviderUnavailable(f"{url} returned {response.status_code}: {response.text[:200]!r}")
    try:
        return response.json()
    except ValueError as exc:
        raise OpenFigiProviderUnavailable(f"{url} did not return valid JSON") from exc


def map_ticker(
    ticker: str,
    *,
    exchange_code: str = _DEFAULT_EXCHANGE_CODE,
    post_json_fn: JsonPoster | None = None,
) -> OpenFigiMappingResult:
    """One-ticker lookup. `post_json_fn` defaults to the real HTTP
    call; tests inject a plain fake function, matching every other
    provider adapter in this codebase."""
    post_json = post_json_fn or _post_json
    headers = {"Content-Type": "application/json"}
    key = _api_key()
    if key:
        headers["X-OPENFIGI-APIKEY"] = key

    payload = post_json(
        _MAPPING_URL,
        [{"idType": "TICKER", "idValue": ticker, "exchCode": exchange_code}],
        headers,
    )
    if not isinstance(payload, list) or not payload:
        raise OpenFigiProviderUnavailable("OpenFIGI returned an unexpected response shape")

    entry = payload[0]
    if not isinstance(entry, dict):
        raise OpenFigiProviderUnavailable("OpenFIGI returned an unexpected response shape")
    if "warning" in entry:
        return OpenFigiMappingResult(matches=())

    raw_matches = entry.get("data")
    if not isinstance(raw_matches, list):
        raise OpenFigiProviderUnavailable("OpenFIGI returned an unexpected response shape")

    matches = tuple(
        OpenFigiMatch(
            figi=row["figi"],
            ticker=row.get("ticker"),
            name=row.get("name"),
            exch_code=row.get("exchCode"),
            security_type=row.get("securityType"),
            market_sector=row.get("marketSector"),
        )
        for row in raw_matches
        if isinstance(row, dict) and isinstance(row.get("figi"), str)
    )
    return OpenFigiMappingResult(matches=matches)

"""Fetches SEC's real `company_tickers.json` into the `SecTickerEntry`
shape `service.py` needs (ticker, cik, **and** title) -- unlike
`SecEdgarFundamentalsProvider._ticker_to_cik()` (Sprint 16), which
discards `title` since it only ever needed the ticker->CIK direction,
this module keeps `title` because Sprint 19's own title-canonical
discovery path depends on it.

`SecTitleIndexSource` caches its own result **once per instance, for
the lifetime of the process** -- deliberately not a TTL/refresh/
persistence system (Sprint 21 ground rule: "do not build a
complicated cache system"). SEC's own ticker map changes on the order
of days, not requests; re-fetching it on every discovery call would
turn a click into a ~10,000-entry network fetch for no benefit, and a
full cache-invalidation design is scope this sprint does not need.
This mirrors, at module scope, exactly the per-instance caching
pattern `SecEdgarFundamentalsProvider._ticker_cik_cache` already
established for the ticker->CIK direction.

Does NOT reuse `atlas.business_data_providers.http.fetch_json`, even
though the shape is nearly identical -- `atlas.business_data_providers`
is architecturally reserved for exactly one caller,
`atlas.alpha.business_data_refresh` (enforced by
`tests/test_architecture_boundaries.py::
test_only_business_data_refresh_imports_business_data_providers`), so a
second importer would be an undisclosed second path to a real network
call. Instead this module owns a small, local `_fetch_json` with the
same injectable-callable shape, so tests can still inject a plain fake
function with no mocking library.
"""
from __future__ import annotations

import os
from typing import Any, Callable

import httpx

from atlas.alpha.security_discovery.models import SecTickerEntry

#: `(url, headers) -> parsed JSON`. Local to this module -- see the
#: module docstring for why it does not reuse
#: `atlas.business_data_providers.http.JsonFetcher`.
JsonFetcher = Callable[[str, "dict[str, str] | None"], Any]

_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
_TIMEOUT_SECONDS = 10.0

#: Matches `atlas.business_data_providers.sec_edgar`'s own default
#: exactly -- SEC's fair-access policy requires a descriptive
#: User-Agent; reusing the same env var means one operator setting
#: covers both call sites rather than two independently-configured ones.
_DEFAULT_USER_AGENT = "Atlas Investment OS admin@atlas-investment-os.local (set ATLAS_SEC_EDGAR_USER_AGENT)"


def _user_agent() -> str:
    return os.environ.get("ATLAS_SEC_EDGAR_USER_AGENT", _DEFAULT_USER_AGENT)


def _fetch_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """The one real implementation of `JsonFetcher` for this module --
    a bare `httpx.get` with `raise_for_status`. No typed error taxonomy
    (unlike `atlas.business_data_providers.http.fetch_json`): an SEC
    fetch failure here surfaces as a plain exception, which is enough
    for a read-only discovery endpoint that already tolerates and
    returns `[]` for "no candidates" -- see the router's own docstring
    on not overbuilding failure handling."""
    response = httpx.get(url, headers=headers, timeout=_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _parse_entries(payload: Any) -> tuple[SecTickerEntry, ...]:
    if not isinstance(payload, dict):
        return ()
    entries: list[SecTickerEntry] = []
    for row in payload.values():
        if not isinstance(row, dict):
            continue
        cik = row.get("cik_str")
        ticker = row.get("ticker")
        title = row.get("title")
        if isinstance(cik, int) and isinstance(ticker, str) and isinstance(title, str):
            entries.append(SecTickerEntry(cik=cik, ticker=ticker, title=title))
    return tuple(entries)


class SecTitleIndexSource:
    """Process-local, lazily-fetched source of every `SecTickerEntry`
    SEC publishes. Never called from Pattern Recognition, History
    render, Decision Review render, or Observed Decision Properties --
    only from the discovery API's own request handler, and only when a
    user explicitly requests discovery (Sprint 21 Phase 3/9)."""

    def __init__(self, fetch_json_fn: JsonFetcher | None = None) -> None:
        self._fetch_json = fetch_json_fn or _fetch_json
        self._cache: tuple[SecTickerEntry, ...] | None = None

    def entries(self) -> tuple[SecTickerEntry, ...]:
        if self._cache is None:
            payload = self._fetch_json(_TICKER_MAP_URL, {"User-Agent": _user_agent()})
            self._cache = _parse_entries(payload)
        return self._cache

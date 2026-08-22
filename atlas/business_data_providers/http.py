"""Shared, injectable JSON-fetch helper (ATLAS-031, Phase 14).

One `httpx` call, a bounded timeout, and typed error mapping -- no
retry loop. Phase 14 explicitly asks for a conservative v1: no
infinite retry, no silent fallback, no chain that changes results
depending on transient ordering. A single deterministic attempt per
call satisfies that; automatic retry is left for a future sprint if
real operational experience shows it's needed.

Mirrors `atlas.providers.yahoo`'s own injectable-fetcher shape
(`fetcher: JsonFetcher | None`) deliberately -- proven in this
repository to make a network-calling provider fully testable without
an HTTP-mocking library (there isn't one installed; see the Phase 1
audit). Every provider in this package takes its own `fetch_json`
callable at construction, defaulting to `fetch_json` below; tests
inject a plain fake function instead.
"""
from __future__ import annotations

import json
from typing import Any, Callable

import httpx

from atlas.business_data_providers.errors import (
    CompanyNotFound,
    MalformedProviderResponse,
    ProviderTimeout,
    ProviderUnavailable,
    RateLimited,
)

__all__ = ["JsonFetcher", "TextFetcher", "DEFAULT_TIMEOUT_SECONDS", "fetch_json", "fetch_text"]

#: `(url, headers) -> parsed JSON`. Never raises anything but the
#: typed errors in `atlas.business_data_providers.errors`.
JsonFetcher = Callable[[str, "dict[str, str] | None"], Any]

#: `(url, headers) -> raw response text`. (Capability Expansion Sprint
#: 13: SEC Filing Content Intelligence.) The identical injectable shape
#: `JsonFetcher` already establishes -- a filing document is HTML, not
#: JSON, so this returns the raw decoded text body instead of a parsed
#: object, and lets the caller (`filing_content_intelligence.py`) do
#: its own deterministic parsing.
TextFetcher = Callable[[str, "dict[str, str] | None"], str]

DEFAULT_TIMEOUT_SECONDS = 10.0


def fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Any:
    """The one real implementation of `JsonFetcher` -- a bare `httpx.get`
    with typed failure mapping. Never called directly by a test; tests
    inject their own fake `JsonFetcher` instead."""
    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise ProviderTimeout(f"Request to {url} timed out after {timeout}s") from exc
    except httpx.HTTPError as exc:
        raise ProviderUnavailable(f"Request to {url} failed: {exc}") from exc

    if response.status_code == 404:
        raise CompanyNotFound(f"{url} returned 404")
    if response.status_code == 429:
        raise RateLimited(f"{url} returned 429 (rate limited)")
    if response.status_code >= 500:
        raise ProviderUnavailable(f"{url} returned {response.status_code}")
    if response.status_code >= 400:
        raise MalformedProviderResponse(f"{url} returned {response.status_code}: {response.text[:200]!r}")

    try:
        return response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise MalformedProviderResponse(f"{url} did not return valid JSON") from exc


def fetch_text(
    url: str,
    headers: dict[str, str] | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """The one real implementation of `TextFetcher` -- identical control
    flow to `fetch_json` above, down to the same status-code mapping,
    but returns the raw decoded body instead of parsing it as JSON.
    Never called directly by a test; tests inject their own fake
    `TextFetcher` instead."""
    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise ProviderTimeout(f"Request to {url} timed out after {timeout}s") from exc
    except httpx.HTTPError as exc:
        raise ProviderUnavailable(f"Request to {url} failed: {exc}") from exc

    if response.status_code == 404:
        raise CompanyNotFound(f"{url} returned 404")
    if response.status_code == 429:
        raise RateLimited(f"{url} returned 429 (rate limited)")
    if response.status_code >= 500:
        raise ProviderUnavailable(f"{url} returned {response.status_code}")
    if response.status_code >= 400:
        raise MalformedProviderResponse(f"{url} returned {response.status_code}: {response.text[:200]!r}")

    return response.text

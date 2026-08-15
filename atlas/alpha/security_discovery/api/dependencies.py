"""Composition wiring for Security Discovery's API.

`_source` is a **module-level singleton** -- deliberately, not a
per-request `Depends()` object -- so `SecTitleIndexSource`'s own
process-local cache (see `sec_source.py`) is actually shared across
requests within this process, matching Sprint 21's own "cheap to load
once, do not build a complicated cache system" instruction. A fresh
instance per request would silently defeat the entire point of that
cache.
"""
from __future__ import annotations

from atlas.alpha.security_discovery.sec_source import SecTitleIndexSource
from atlas.alpha.security_discovery.service import (
    TickerIndex,
    TitleIndex,
    build_ticker_index,
    build_title_index,
)

_source = SecTitleIndexSource()


def get_security_discovery_indexes() -> tuple[TitleIndex, TickerIndex]:
    entries = _source.entries()
    return build_title_index(entries), build_ticker_index(entries)

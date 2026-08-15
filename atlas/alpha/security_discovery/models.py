"""Data shapes for Security Discovery (Sprint 19).

`SecurityCandidate.status` is a fixed literal, not a field a caller can
set -- every candidate this package ever produces is, by construction,
unconfirmed. There is no `confidence` field: Sprint 19's own Phase 9
evaluated and rejected an invented confidence score, since nothing here
is scored -- a query either produces exact-canonical-form matches or it
does not. `exchange`/`region`/`currency` are deliberately absent: SEC's
`company_tickers.json` does not carry them, and this package never
fabricates a field its one data source does not actually supply.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DiscoveryMethod = Literal["ticker_exact", "title_canonical"]


@dataclass(frozen=True)
class SecTickerEntry:
    """One row of SEC's own `company_tickers.json`, exactly as SEC
    publishes it -- `cik` kept as the bare integer SEC uses, `ticker`
    and `title` kept verbatim (never case-folded here; canonicalization
    happens only inside `canonicalize.py`, and only for matching, never
    for display)."""

    cik: int
    ticker: str
    title: str


@dataclass(frozen=True)
class SecurityCandidate:
    """An unconfirmed discovery result. Never identity proof -- see
    this package's own `__init__.py` for why `status` can only ever be
    `"candidate_only"`."""

    ticker: str
    display_name: str
    cik: int
    discovery_method: DiscoveryMethod
    source: str = "sec_company_tickers"
    status: Literal["candidate_only"] = "candidate_only"

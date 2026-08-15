"""Pure discovery logic (Sprint 19). No network call anywhere in this
module -- `build_title_index` takes an already-fetched sequence of
`SecTickerEntry`; obtaining those from SEC's real `company_tickers.json`
is the caller's job, done only at explicit enrichment time, never from
this module.

`discover_security_candidates` tries an exact ticker-symbol match
first (Case D of Sprint 19's own test matrix: the query is already a
ticker) before falling through to canonical-title matching (Case A/B/C:
the query is a company name). Both paths are deterministic lookups
against an in-memory mapping -- there is no ranking between them, and
a query that matches as a ticker never also runs the title path.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping

from atlas.alpha.security_discovery.canonicalize import canonicalize_company_text
from atlas.alpha.security_discovery.models import SecTickerEntry, SecurityCandidate

TitleIndex = Mapping[str, tuple[SecTickerEntry, ...]]
TickerIndex = Mapping[str, SecTickerEntry]


def build_title_index(entries: Iterable[SecTickerEntry]) -> TitleIndex:
    """Groups entries by canonical title -- the exact mechanism that
    surfaces Berkshire Hathaway's BRK-A/BRK-B and Alphabet's
    GOOG/GOOGL/GOOGM/GOOGN as separate candidates rather than picking
    one: every entry whose title canonicalizes identically stays in the
    same group, unranked, and every group is returned in full."""
    index: dict[str, tuple[SecTickerEntry, ...]] = {}
    for entry in entries:
        key = canonicalize_company_text(entry.title)
        index[key] = index.get(key, ()) + (entry,)
    return index


def build_ticker_index(entries: Iterable[SecTickerEntry]) -> TickerIndex:
    """Exact ticker symbol -> entry. Case-sensitive on the stored form
    (SEC's own tickers are already upper-case); lookups upper-case the
    query before matching, never fuzz it."""
    return {entry.ticker.upper(): entry for entry in entries}


def discover_security_candidates(
    query: str,
    *,
    title_index: TitleIndex,
    ticker_index: TickerIndex,
) -> tuple[SecurityCandidate, ...]:
    """Returns zero or more `SecurityCandidate`s, every one carrying
    `status="candidate_only"`. Never raises for an unmatched query --
    an empty tuple is the correct, honest result for Case E (unknown
    company), exactly as it is for any other miss."""
    stripped = query.strip()
    if not stripped:
        return ()

    ticker_match = ticker_index.get(stripped.upper())
    if ticker_match is not None:
        return (
            SecurityCandidate(
                ticker=ticker_match.ticker,
                display_name=ticker_match.title,
                cik=ticker_match.cik,
                discovery_method="ticker_exact",
            ),
        )

    canonical = canonicalize_company_text(stripped)
    if not canonical:
        return ()
    matches = title_index.get(canonical, ())
    return tuple(
        SecurityCandidate(
            ticker=entry.ticker,
            display_name=entry.title,
            cik=entry.cik,
            discovery_method="title_canonical",
        )
        for entry in matches
    )

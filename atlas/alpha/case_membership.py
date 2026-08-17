"""Which Cases exist because of Portfolio or Watchlist membership --
shared by every Alpha capability that needs "every Case Daily Brief/
History/etc. should consider," so this definition lives in exactly one
place rather than one slightly-different copy per consumer (first
extracted here when `atlas.alpha.investment_case_history` needed the
exact same list `atlas.alpha.daily_brief` already computed).
"""
from __future__ import annotations

from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["known_cases", "resolve_case_id_for_ticker"]


def known_cases(
    portfolio_store: AlphaPortfolioStore, watchlist_store: AlphaWatchlistStore
) -> tuple[tuple[str, str | None], ...]:
    """Every distinct `case_id` a cross-Case capability should consider,
    paired with its own ticker -- Portfolio holdings first, then any
    Watchlist entry whose `case_id` was not already seen (a Case that is
    both held and watchlisted is real -- see `atlas.alpha.watchlist`'s
    own "Watchlist and Portfolio are membership contexts around the same
    company knowledge" doctrine -- and must never be counted, or
    appear in a caller's own output, twice)."""
    seen: dict[str, str | None] = {}

    state = portfolio_store.get()
    if state is not None:
        for holding in state.holdings:
            if holding.case_id is not None and holding.case_id not in seen:
                seen[holding.case_id] = holding.ticker

    for entry in watchlist_store.list_all():
        if entry.case_id not in seen:
            seen[entry.case_id] = entry.ticker

    return tuple(seen.items())


def resolve_case_id_for_ticker(
    ticker: str,
    portfolio_store: AlphaPortfolioStore | None,
    watchlist_store: AlphaWatchlistStore,
) -> str | None:
    """Return the `case_id` Atlas has already created for `ticker`, if
    any -- the complement of `known_cases` (which asks "which Cases
    exist"; this asks "does this specific ticker already have one").

    Read-only: never creates, reactivates, or otherwise mutates any
    Portfolio or Watchlist row. Checked in priority order, each a
    composition of data this codebase already persists for a different
    purpose -- no new storage, no new ontology:

    1. A current Portfolio holding for `ticker` -- the live,
       authoritative membership state, so it wins over anything else.
    2. A current Watchlist entry for `ticker`.
    3. `ticker`'s own prior Watchlist entry, even if since removed
       (`AlphaWatchlistStore.get_by_ticker_including_removed`) -- the
       fact this sprint exists to restore: removing a ticker from the
       Watchlist does not erase which Case it was already linked to.

    Portfolio is checked first deliberately, not arbitrarily: if a
    ticker is both currently held (case C2) and has stale, removed
    Watchlist history pointing at a different, older case (C1),
    resurrecting C1 here would silently split one ticker across two
    Cases across contexts -- exactly what "Watchlist and Portfolio are
    membership contexts around the same company knowledge" (this
    codebase's own established doctrine, see `AlphaWatchlistService.
    _known_case_ids_by_ticker`'s own docstring) forbids. Returns `None`
    only if no Case has ever been linked to `ticker` through either
    context -- the genuinely-new-ticker case, where creating a fresh
    Case is correct.
    """
    normalized = ticker.strip().upper()

    if portfolio_store is not None:
        state = portfolio_store.get()
        if state is not None:
            for holding in state.holdings:
                if holding.ticker == normalized and holding.case_id is not None:
                    return holding.case_id

    active_entry = watchlist_store.get_by_ticker(normalized)
    if active_entry is not None:
        return active_entry.case_id

    historical_entry = watchlist_store.get_by_ticker_including_removed(normalized)
    if historical_entry is not None:
        return historical_entry.case_id

    return None

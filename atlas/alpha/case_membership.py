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

__all__ = ["known_cases"]


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

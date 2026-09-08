"""Deterministic backfill of the Case -> instrument binding from the
membership state Atlas already persists.

Reads three sources, all local: current Portfolio holdings, current
Watchlist entries, and *removed* Watchlist entries. The third matters:
`AlphaWatchlistStore.get_by_case_id` was deliberately left unfiltered
so a removed prospect's Case kept resolving its ticker, and that
history is exactly as authoritative for a backfill as an active row.

Makes no provider call, resolves no canonical security, normalizes no
ticker, and creates no Case. It records what the data already says.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from atlas.alpha.case_instrument.exceptions import ConflictingCaseInstrumentBindingError
from atlas.alpha.case_instrument.models import CaseInstrumentBinding
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["BackfillReport", "backfill_case_instrument_bindings"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class BackfillReport:
    """What the backfill did, in enough detail to audit afterwards."""

    bound: tuple[str, ...] = ()
    """`case_id`s given a binding by this run."""
    already_bound: tuple[str, ...] = ()
    """`case_id`s that already had one -- the idempotent path."""
    conflicts: tuple[tuple[str, tuple[str, ...]], ...] = ()
    """`(case_id, tickers)` where membership named more than one
    security for a single Case. Never resolved by preferring one
    source over another: a conflict is an integrity defect, and
    picking Portfolio over Watchlist would be the same backwards guess
    this whole change removes."""

    @property
    def is_clean(self) -> bool:
        return not self.conflicts


def collect_associations(
    portfolio_store: AlphaPortfolioStore,
    watchlist_store: AlphaWatchlistStore,
) -> dict[str, set[str]]:
    """`case_id -> {instrument_key}`, from every membership source.

    A set, not a first-wins pick, so a Case associated with two
    different securities surfaces as exactly that rather than being
    silently collapsed.
    """
    associations: dict[str, set[str]] = {}

    state = portfolio_store.get()
    if state is not None:
        for holding in state.holdings:
            if holding.case_id is not None:
                associations.setdefault(holding.case_id, set()).add(holding.ticker)

    for entry in watchlist_store.list_all_including_removed():
        associations.setdefault(entry.case_id, set()).add(entry.ticker)

    return associations


def backfill_case_instrument_bindings(
    repository: CaseInstrumentBindingRepository,
    portfolio_store: AlphaPortfolioStore,
    watchlist_store: AlphaWatchlistStore,
    *,
    bound_at: datetime | None = None,
) -> BackfillReport:
    """Idempotent: running it twice binds nothing the second time.

    Conflicts are collected and reported, and those Cases are left
    unbound -- the run does not abort, so one bad row cannot block
    every good one, and the caller decides what to do with the list.
    """
    stamp = bound_at or _utc_now()
    associations = collect_associations(portfolio_store, watchlist_store)

    bound: list[str] = []
    already: list[str] = []
    conflicts: list[tuple[str, tuple[str, ...]]] = []

    for case_id in sorted(associations):
        tickers = associations[case_id]
        if len(tickers) > 1:
            conflicts.append((case_id, tuple(sorted(tickers))))
            continue
        instrument_key = next(iter(tickers))
        if repository.get_by_case_id(case_id) is not None:
            already.append(case_id)
            continue
        repository.bind(
            CaseInstrumentBinding(case_id=case_id, instrument_key=instrument_key, bound_at=stamp)
        )
        bound.append(case_id)

    return BackfillReport(
        bound=tuple(bound), already_bound=tuple(already), conflicts=tuple(conflicts)
    )

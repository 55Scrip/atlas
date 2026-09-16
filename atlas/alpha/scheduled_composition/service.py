"""Compose the Cases the investor actually follows, on a schedule.

Atlas can freeze the evidence behind a conclusion, read it back, page it and
measure it. None of that records anything unless a Case is actually composed,
and until now the only thing that composed a Case was a person opening it. So
the longitudinal record stayed empty: an investor would have had to visit
twenty-six Cases by hand just so Atlas could notice how its own evidence
moved.

This service does that walk instead. It is the smallest mechanism that makes
the record accumulate, and it is deliberately unambitious about everything
else.

**It asks one question: what does Atlas conclude from the evidence it already
has?** It never asks whether newer evidence exists anywhere outside. No
provider is called, no filing is fetched, no quote is refreshed -- composition
simply cannot reach the network (proven by sabotaging the socket layer and
composing the whole scope). A Case whose stored data is stale composes
honestly from that stale data and says so; it does not go looking.

**It is not a heartbeat.** Running it changes nothing by itself. A snapshot is
written only when the existing persistence doctrine says the record moved --
a changed conclusion, or changed evidence beneath an unchanged conclusion --
so composing the same unchanged Case every hour writes exactly one row, ever.

**It adds no semantics of its own.** It calls the same composition every
opened Case calls, and whatever that produces -- a new snapshot, a decision
change, a Daily Brief item -- happens for the ordinary reasons and is
attributable to the stored evidence. The scheduler never emits an event
saying it ran; "Atlas looked again" is not news about a company.

**One bad Case is one bad Case.** The batch composes the rest and reports the
failure against the Case it belongs to.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

from atlas.alpha.case_membership import known_cases
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = [
    "CaseCompositionOutcome",
    "ScheduledCompositionResult",
    "ScheduledCompositionService",
    "scheduled_scope",
]


_RUN_LOCK = threading.Lock()
"""Process-wide, module-level for the same reason `monitoring.service`'s is:
the service is built per caller, so an instance lock would not serialize two
callers against each other. Two batches composing the same Case concurrently
would both read the same snapshot head, both find it changed, and both write
-- turning one analytical movement into two rows and corrupting the very
record this sprint exists to build.

In-process only. A batch run as a separate command against a database the API
is also serving is *not* protected by this; only SQLite's own file locking
stands between them. That is a real limit, stated here rather than papered
over: the one-shot command says so when it starts."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def scheduled_scope(
    portfolio_store: AlphaPortfolioStore, watchlist_store: AlphaWatchlistStore
) -> tuple[tuple[str, str | None], ...]:
    """The Cases a scheduled run composes: exactly the ones the investor is
    holding or watching, deduplicated by Case identity.

    This is `known_cases` -- the same membership History and coverage already
    mean by "whose history is this" -- and not a second definition of
    relevance. A Case that is merely analysed, or that Discover surfaced and
    nobody kept, is not composed: Atlas accumulates history for positions and
    candidates someone is actually carrying, not for the market at large.

    Ordering is by Case identity so a batch is deterministic rather than
    whatever order a table happened to return.
    """
    return tuple(sorted(known_cases(portfolio_store, watchlist_store), key=lambda entry: entry[0]))


@dataclass(frozen=True)
class CaseCompositionOutcome:
    case_id: str
    ticker: str | None
    composed: bool
    snapshot_written: bool
    #: A short, safe summary -- never a stack trace, never provider
    #: credentials, and never anything a product surface should not carry.
    error: str | None = None


@dataclass(frozen=True)
class ScheduledCompositionResult:
    started_at: datetime
    duration_seconds: float
    attempted: int
    succeeded: int
    failed: int
    snapshots_written: int
    snapshots_deduplicated: int
    outcomes: tuple[CaseCompositionOutcome, ...] = field(default_factory=tuple)

    @property
    def partial(self) -> bool:
        """True when some Cases composed and some did not -- the honest state
        a batch reports rather than calling itself a success or a failure."""
        return self.failed > 0 and self.succeeded > 0

    @property
    def summary(self) -> str:
        outcome = "ok" if self.failed == 0 else ("partial" if self.succeeded else "failed")
        return (f"{outcome}: attempted {self.attempted}, succeeded {self.succeeded}, failed {self.failed}, "
                f"snapshots written {self.snapshots_written}, unchanged {self.snapshots_deduplicated}, "
                f"{self.duration_seconds:.1f}s")


class ScheduledCompositionService:
    """Runs one batch. How it is triggered -- a command, a cron entry, a
    future in-process scheduler -- is deliberately not this class's business.
    """

    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
        snapshot_repository: SqlAlchemyInvestmentCaseSnapshotRepository,
    ) -> None:
        self._composition_service = composition_service
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        self._snapshot_repository = snapshot_repository

    def scope(self) -> tuple[tuple[str, str | None], ...]:
        return scheduled_scope(self._portfolio_store, self._watchlist_store)

    def _snapshot_identity(self, case_id: str) -> str | None:
        head = self._snapshot_repository.get_latest(case_id)
        return None if head is None else f"{head.content_hash}:{head.captured_at.isoformat()}"

    def run(self, *, scope: Sequence[tuple[str, str | None]] | None = None) -> ScheduledCompositionResult:
        """Compose every Case in scope. Waits its turn if another batch is
        already running, because someone who explicitly asked for a batch
        expects one to happen.
        """
        with _RUN_LOCK:
            return self._run_locked(scope=scope)

    def trigger_scheduled_run(
        self, *, scope: Sequence[tuple[str, str | None]] | None = None
    ) -> ScheduledCompositionResult | None:
        """The entry point a recurring trigger would call. Returns `None`
        immediately if a batch is already in flight, rather than queuing
        behind it.

        Skipping loses nothing. A batch does not carry work forward -- it
        asks what Atlas concludes from what is stored right now -- so a tick
        that arrives while the previous one is still running is genuinely
        redundant, and the next tick asks the same question against strictly
        newer state. Queueing them instead would let a slow batch accumulate
        a backlog of ticks that all want to do the work the running one is
        already doing.

        Nothing calls this yet: no recurring trigger is wired anywhere in
        Atlas. It exists so that when one is, it has a correct entry point
        to call rather than inventing its own.
        """
        if not _RUN_LOCK.acquire(blocking=False):
            return None
        try:
            return self._run_locked(scope=scope)
        finally:
            _RUN_LOCK.release()

    def _run_locked(self, *, scope: Sequence[tuple[str, str | None]] | None) -> ScheduledCompositionResult:
        """Compose each Case in scope, once, in order.

        Whether a snapshot was written is read from the store rather than
        assumed: the composition path owns that decision, and this only
        reports what it did. Each Case is composed on its own, so a failure
        costs that Case and no other -- and nothing already written is rolled
        back because something later went wrong.
        """
        started_at = _utc_now()
        began = time.perf_counter()
        cases = tuple(scope) if scope is not None else self.scope()

        outcomes: list[CaseCompositionOutcome] = []
        for case_id, ticker in cases:
            before = self._snapshot_identity(case_id)
            try:
                composition = self._composition_service.build(case_id)
            except Exception as error:  # noqa: BLE001 -- one Case's failure is not the batch's
                outcomes.append(CaseCompositionOutcome(
                    case_id=case_id, ticker=ticker, composed=False, snapshot_written=False,
                    error=f"{type(error).__name__}: {str(error)[:200]}"))
                continue
            if composition is None:
                # The Case identifier does not resolve to a real Case. Recorded
                # as a failure rather than silently skipped, and never a reason
                # to go looking for an identity somewhere outside.
                outcomes.append(CaseCompositionOutcome(
                    case_id=case_id, ticker=ticker, composed=False, snapshot_written=False,
                    error="Case does not resolve"))
                continue
            after = self._snapshot_identity(case_id)
            outcomes.append(CaseCompositionOutcome(
                case_id=case_id, ticker=ticker, composed=True, snapshot_written=after != before))

        succeeded = sum(1 for outcome in outcomes if outcome.composed)
        written = sum(1 for outcome in outcomes if outcome.snapshot_written)
        return ScheduledCompositionResult(
            started_at=started_at,
            duration_seconds=time.perf_counter() - began,
            attempted=len(outcomes),
            succeeded=succeeded,
            failed=len(outcomes) - succeeded,
            snapshots_written=written,
            snapshots_deduplicated=succeeded - written,
            outcomes=tuple(outcomes),
        )

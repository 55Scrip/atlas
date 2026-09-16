"""Scheduled Case composition -- scope, batch mechanics, failure isolation
and locking.

The service is deliberately thin, so these tests are mostly about what it
must *not* do: invent scope, invent semantics, let one Case take down a
batch, or claim a snapshot was written when the persistence layer declined
to write one.
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

import pytest

from atlas.alpha.scheduled_composition.service import (
    CaseCompositionOutcome,
    ScheduledCompositionResult,
    ScheduledCompositionService,
    scheduled_scope,
)


class _Holding:
    def __init__(self, case_id: str | None, ticker: str | None) -> None:
        self.case_id = case_id
        self.ticker = ticker


class _State:
    def __init__(self, holdings) -> None:
        self.holdings = holdings


class _PortfolioStore:
    def __init__(self, holdings=()) -> None:
        self._state = _State(list(holdings))

    def get(self):
        return self._state


class _WatchlistEntry:
    def __init__(self, case_id: str, ticker: str | None) -> None:
        self.case_id = case_id
        self.ticker = ticker


class _WatchlistStore:
    def __init__(self, entries=()) -> None:
        self._entries = list(entries)

    def list_all(self):
        return tuple(self._entries)


class _Head:
    def __init__(self, content_hash: str, captured_at: datetime) -> None:
        self.content_hash = content_hash
        self.captured_at = captured_at


class _SnapshotRepository:
    """Stands in for the real repository's dedup decision.

    The service must *read* whether a row appeared rather than assume one
    did, so this lets a test say "composing this Case moved the head" or
    "it did not" independently of whether composition succeeded.
    """

    def __init__(self, heads: dict[str, _Head] | None = None) -> None:
        self.heads = dict(heads or {})
        self.reads: list[str] = []

    def get_latest(self, case_id: str):
        self.reads.append(case_id)
        return self.heads.get(case_id)

    def move(self, case_id: str) -> None:
        at = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
        existing = self.heads.get(case_id)
        self.heads[case_id] = _Head(f"hash-{len(self.reads)}", at if existing is None else at + timedelta(days=1))


class _CompositionService:
    """Composes by moving the snapshot head, the way the real one does."""

    def __init__(self, repository: _SnapshotRepository, *, writes=True, fails=(), missing=()) -> None:
        self._repository = repository
        self._writes = writes
        self._fails = set(fails)
        self._missing = set(missing)
        self.built: list[str] = []

    def build(self, case_id: str):
        self.built.append(case_id)
        if case_id in self._fails:
            raise RuntimeError("provider exploded\nline two\nline three")
        if case_id in self._missing:
            return None
        if self._writes:
            self._repository.move(case_id)
        return object()


def _service(*, holdings=(), entries=(), heads=None, **kwargs):
    repository = _SnapshotRepository(heads)
    composition = _CompositionService(repository, **kwargs)
    service = ScheduledCompositionService(
        composition_service=composition,
        portfolio_store=_PortfolioStore(holdings),
        watchlist_store=_WatchlistStore(entries),
        snapshot_repository=repository,
    )
    return service, composition, repository


# --- Scope -------------------------------------------------------------


def test_scope_is_portfolio_holdings_and_watchlist_entries() -> None:
    scope = scheduled_scope(
        _PortfolioStore([_Holding("c1", "AAA")]),
        _WatchlistStore([_WatchlistEntry("c2", "BBB")]),
    )
    assert scope == (("c1", "AAA"), ("c2", "BBB"))


def test_scope_counts_a_case_that_is_both_held_and_watched_once() -> None:
    """Membership contexts overlap; Case identity does not. Composing the
    same Case twice in one batch would read its own write back."""
    scope = scheduled_scope(
        _PortfolioStore([_Holding("c1", "AAA")]),
        _WatchlistStore([_WatchlistEntry("c1", "AAA"), _WatchlistEntry("c2", "BBB")]),
    )
    assert scope == (("c1", "AAA"), ("c2", "BBB"))


def test_scope_is_ordered_by_case_identity_not_table_order() -> None:
    """A batch must be reproducible, so its order cannot depend on whichever
    order Portfolio and Watchlist happened to return."""
    scope = scheduled_scope(
        _PortfolioStore([_Holding("zeta", "ZZZ"), _Holding("alpha", "AAA")]),
        _WatchlistStore([_WatchlistEntry("mid", "MMM")]),
    )
    assert [case_id for case_id, _ in scope] == ["alpha", "mid", "zeta"]


def test_scope_skips_holdings_with_no_case() -> None:
    scope = scheduled_scope(
        _PortfolioStore([_Holding(None, "AAA"), _Holding("c1", "BBB")]),
        _WatchlistStore([]),
    )
    assert scope == (("c1", "BBB"),)


def test_empty_membership_is_an_empty_scope_not_an_error() -> None:
    assert scheduled_scope(_PortfolioStore([]), _WatchlistStore([])) == ()


# --- Batch mechanics ---------------------------------------------------


def test_run_composes_every_case_in_scope_once() -> None:
    service, composition, _ = _service(
        holdings=[_Holding("c1", "AAA"), _Holding("c2", "BBB")],
        entries=[_WatchlistEntry("c3", "CCC")],
    )
    result = service.run()
    assert composition.built == ["c1", "c2", "c3"]
    assert (result.attempted, result.succeeded, result.failed) == (3, 3, 0)


def test_a_written_snapshot_is_read_from_the_store_not_assumed() -> None:
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")])
    result = service.run()
    assert result.snapshots_written == 1
    assert result.outcomes[0].snapshot_written is True


def test_an_unchanged_case_is_reported_as_deduplicated_not_written() -> None:
    """Composing an unchanged Case is the normal case, not a failure: the
    Case composed, and the persistence layer correctly declined to write."""
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")], writes=False)
    result = service.run()
    assert result.succeeded == 1
    assert result.snapshots_written == 0
    assert result.snapshots_deduplicated == 1
    assert result.outcomes[0].composed is True
    assert result.outcomes[0].snapshot_written is False


def test_deduplicated_count_never_includes_failures() -> None:
    """`deduplicated` means "composed and unchanged". A Case that never
    composed is not evidence that nothing changed."""
    service, _, _ = _service(
        holdings=[_Holding("c1", "AAA"), _Holding("c2", "BBB")], writes=False, fails=["c2"]
    )
    result = service.run()
    assert (result.succeeded, result.failed) == (1, 1)
    assert result.snapshots_deduplicated == 1


def test_outcomes_follow_scope_order_and_carry_the_ticker() -> None:
    service, _, _ = _service(holdings=[_Holding("c2", "BBB"), _Holding("c1", "AAA")])
    result = service.run()
    assert [(o.case_id, o.ticker) for o in result.outcomes] == [("c1", "AAA"), ("c2", "BBB")]


def test_an_explicit_scope_replaces_the_computed_one() -> None:
    service, composition, _ = _service(holdings=[_Holding("c1", "AAA"), _Holding("c2", "BBB")])
    service.run(scope=[("c2", "BBB")])
    assert composition.built == ["c2"]


def test_an_empty_scope_is_a_clean_zero_result() -> None:
    service, composition, _ = _service()
    result = service.run()
    assert composition.built == []
    assert (result.attempted, result.succeeded, result.failed) == (0, 0, 0)
    assert result.partial is False


def test_duration_and_start_time_are_recorded() -> None:
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")])
    result = service.run()
    assert result.duration_seconds >= 0.0
    assert result.started_at.tzinfo is not None


# --- Failure isolation -------------------------------------------------


def test_one_failing_case_does_not_stop_the_batch() -> None:
    service, composition, _ = _service(
        holdings=[_Holding("c1", "AAA"), _Holding("c2", "BBB"), _Holding("c3", "CCC")],
        fails=["c2"],
    )
    result = service.run()
    assert composition.built == ["c1", "c2", "c3"]
    assert (result.succeeded, result.failed) == (2, 1)
    assert result.partial is True


def test_a_failure_is_attributed_to_its_own_case() -> None:
    service, _, _ = _service(holdings=[_Holding("c1", "AAA"), _Holding("c2", "BBB")], fails=["c2"])
    failed = [o for o in service.run().outcomes if not o.composed]
    assert [o.case_id for o in failed] == ["c2"]
    assert failed[0].composed is False
    assert failed[0].snapshot_written is False


def test_a_failure_is_summarised_not_dumped() -> None:
    """The error reaches an operator report, so it carries the exception
    type and a bounded message -- never a traceback."""
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")], fails=["c1"])
    error = service.run().outcomes[0].error
    assert error is not None
    assert error.startswith("RuntimeError: provider exploded")
    assert len(error) <= len("RuntimeError: ") + 200


def test_a_long_error_message_is_truncated() -> None:
    repository = _SnapshotRepository()

    class _Exploding:
        def build(self, case_id):
            raise ValueError("x" * 5000)

    service = ScheduledCompositionService(
        composition_service=_Exploding(),
        portfolio_store=_PortfolioStore([_Holding("c1", "AAA")]),
        watchlist_store=_WatchlistStore([]),
        snapshot_repository=repository,
    )
    error = service.run().outcomes[0].error
    assert len(error) == len("ValueError: ") + 200


def test_a_case_that_does_not_resolve_is_a_failure_not_a_silent_skip() -> None:
    """`build` returning `None` means the identifier names no real Case.
    Counting that as success would let scope rot go unnoticed."""
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")], missing=["c1"])
    result = service.run()
    assert (result.succeeded, result.failed) == (0, 1)
    assert result.outcomes[0].error == "Case does not resolve"


def test_work_done_before_a_failure_is_kept() -> None:
    service, _, repository = _service(
        holdings=[_Holding("c1", "AAA"), _Holding("c2", "BBB")], fails=["c2"]
    )
    result = service.run()
    assert "c1" in repository.heads
    assert result.snapshots_written == 1


def test_an_all_failed_batch_is_failed_rather_than_partial() -> None:
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")], fails=["c1"])
    result = service.run()
    assert result.partial is False
    assert result.summary.startswith("failed:")


def test_summary_states_the_outcome_in_one_line() -> None:
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")])
    summary = service.run().summary
    assert summary.startswith("ok:")
    assert "attempted 1" in summary and "snapshots written 1" in summary


# --- Locking -----------------------------------------------------------


def test_a_scheduled_trigger_skips_rather_than_queues_while_a_batch_runs() -> None:
    """Two batches composing the same Case concurrently would both see the
    same head and both write, turning one movement into two rows."""
    service, composition, _ = _service(holdings=[_Holding("c1", "AAA")])
    entered = threading.Event()
    release = threading.Event()
    returned = threading.Event()
    skipped: list[object] = []

    original = composition.build

    def blocking(case_id):
        entered.set()
        release.wait(5)
        return original(case_id)

    def trigger():
        skipped.append(service.trigger_scheduled_run())
        returned.set()

    composition.build = blocking
    worker = threading.Thread(target=service.run)
    worker.start()
    try:
        assert entered.wait(5)
        threading.Thread(target=trigger, daemon=True).start()
        # It must come back *now*, not when the running batch finishes:
        # a trigger that waits its turn is a queued tick, which is the
        # backlog this skip exists to prevent.
        assert returned.wait(2), "trigger_scheduled_run queued instead of skipping"
    finally:
        release.set()
        worker.join(5)

    assert skipped == [None]


def test_a_scheduled_trigger_runs_when_nothing_holds_the_lock() -> None:
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")])
    result = service.trigger_scheduled_run()
    assert isinstance(result, ScheduledCompositionResult)
    assert result.succeeded == 1


def test_the_lock_is_released_after_a_batch_and_after_a_skip() -> None:
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")])
    assert service.run().attempted == 1
    assert service.trigger_scheduled_run() is not None
    assert service.run().attempted == 1


def test_a_raising_scope_lookup_still_releases_the_lock() -> None:
    """A batch that dies before composing anything must not wedge every
    future batch in the process."""
    class _Broken:
        def get(self):
            raise RuntimeError("portfolio unreadable")

    repository = _SnapshotRepository()
    service = ScheduledCompositionService(
        composition_service=_CompositionService(repository),
        portfolio_store=_Broken(),
        watchlist_store=_WatchlistStore([]),
        snapshot_repository=repository,
    )
    with pytest.raises(RuntimeError):
        service.run()
    assert service.run(scope=[]).attempted == 0


# --- What a batch must not do -----------------------------------------


def test_the_service_reaches_persistence_only_through_its_collaborators() -> None:
    """No provider, no HTTP client, no second definition of composing."""
    service, composition, repository = _service(holdings=[_Holding("c1", "AAA")])
    service.run()
    assert composition.built == ["c1"]
    assert repository.reads == ["c1", "c1"]


def test_a_second_batch_over_unchanged_data_writes_nothing() -> None:
    service, _, _ = _service(holdings=[_Holding("c1", "AAA")], writes=False)
    first = service.run()
    second = service.run()
    assert first.snapshots_written == 0
    assert second.snapshots_written == 0
    assert second.succeeded == 1


def test_outcome_is_a_value_not_a_mutable_report() -> None:
    outcome = CaseCompositionOutcome(case_id="c1", ticker="AAA", composed=True, snapshot_written=False)
    with pytest.raises(Exception):
        outcome.composed = False  # type: ignore[misc]

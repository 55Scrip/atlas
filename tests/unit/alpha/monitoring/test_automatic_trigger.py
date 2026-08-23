"""Tests for Internal Alpha Fix Sprint 1's own additions to
`MonitoringService`: `trigger_automatic_run` (the non-blocking,
best-effort sibling of `run`) and the process-wide lock both methods
now share (Deliverable 3/9 -- no overlapping runs, no duplicate
execution). Reuses `test_service.py`'s own harness construction
verbatim rather than re-deriving it -- the same "one canonical harness
per package" convention this test suite already follows elsewhere.
"""
from __future__ import annotations

import threading
import time

from atlas.alpha.monitoring.models import OperationalRunStatus
from atlas.alpha.monitoring.service import _RUN_LOCK
from tests.unit.alpha.monitoring.test_service import _Harness, _new_engine


def _harness() -> _Harness:
    return _Harness(_new_engine())


def test_trigger_automatic_run_behaves_like_a_normal_run_when_nothing_else_is_running():
    h = _harness()
    h.add_to_watchlist("AAPL")

    result = h.monitoring_service.trigger_automatic_run()

    assert result is not None
    assert len(result.results) == 1


def test_trigger_automatic_run_returns_none_when_a_run_is_already_in_progress():
    h = _harness()
    h.add_to_watchlist("AAPL")

    assert _RUN_LOCK.acquire(blocking=False)
    try:
        result = h.monitoring_service.trigger_automatic_run()
    finally:
        _RUN_LOCK.release()

    assert result is None


def test_trigger_automatic_run_never_loses_the_dirty_case_it_skipped():
    """Deliverable 3/9's own core claim: skipping an automatic trigger
    because a run is already in progress never drops the underlying
    dirty state -- the very next trigger still finds it and evaluates
    it, because `needs_recompute` is a fact about the Case, not about
    whether some earlier trigger happened to run."""
    h = _harness()
    h.add_to_watchlist("AAPL")

    assert _RUN_LOCK.acquire(blocking=False)
    try:
        skipped = h.monitoring_service.trigger_automatic_run()
    finally:
        _RUN_LOCK.release()
    assert skipped is None

    recovered = h.monitoring_service.trigger_automatic_run()
    assert recovered is not None
    assert len(recovered.results) == 1


def test_run_still_executes_while_a_prior_run_holds_the_lock_it_just_waits():
    """`run()` (the manual, canonical path) must still always execute,
    unlike `trigger_automatic_run`. Simulated by holding `_RUN_LOCK` on
    a background thread for a short, bounded window and confirming the
    foreground `run()` call only returns after that window -- i.e. it
    waited for the lock rather than erroring or silently no-opping."""
    h = _harness()
    h.add_to_watchlist("AAPL")

    released_at: list[float] = []

    def _hold_lock_briefly() -> None:
        _RUN_LOCK.acquire()
        time.sleep(0.2)
        released_at.append(time.monotonic())
        _RUN_LOCK.release()

    holder = threading.Thread(target=_hold_lock_briefly)
    holder.start()
    time.sleep(0.05)  # give the holder thread time to actually acquire first

    started_waiting_at = time.monotonic()
    result = h.monitoring_service.run(force=False)
    finished_at = time.monotonic()
    holder.join()

    assert result is not None
    assert len(released_at) == 1
    # `run()` could only have returned after the holder released the lock.
    assert finished_at >= released_at[0]
    assert finished_at - started_waiting_at >= 0.1


def test_repeated_automatic_triggers_with_no_new_dirty_state_are_idempotent():
    """Deliverable 9 -- calling `trigger_automatic_run` again immediately
    after a completed run, with nothing new having happened, produces
    the identical result set (every Case skipped, cached result carried
    forward) rather than re-evaluating or duplicating anything."""
    h = _harness()
    h.add_to_watchlist("AAPL")
    h.add_to_watchlist("MSFT")

    first = h.monitoring_service.trigger_automatic_run()
    second = h.monitoring_service.trigger_automatic_run()

    assert first is not None and second is not None
    first_by_case = {r.case_id: r.generated_at for r in first.results}
    second_by_case = {r.case_id: r.generated_at for r in second.results}
    assert first_by_case == second_by_case


def test_repeated_automatic_triggers_create_one_run_record_each_but_never_overlap():
    """A run record is still written per real call (unchanged pre-
    existing behavior), but Deliverable 9's own concern -- overlapping
    execution -- never happens: every recorded run's own started_at/
    completed_at window is disjoint from every other's."""
    h = _harness()
    h.add_to_watchlist("AAPL")

    h.monitoring_service.trigger_automatic_run()
    h.monitoring_service.trigger_automatic_run()
    h.monitoring_service.trigger_automatic_run()

    rows = []
    with h.engine.connect() as connection:
        from atlas.alpha.monitoring.table import monitoring_run_record_table
        from sqlalchemy import select

        for row in connection.execute(select(monitoring_run_record_table)).mappings():
            rows.append(row)

    assert len(rows) == 3
    windows = sorted(
        (row["started_at"], row["completed_at"] or row["started_at"]) for row in rows
    )
    for (_, end_a), (start_b, _) in zip(windows, windows[1:]):
        assert end_a <= start_b
    assert all(row["status"] == OperationalRunStatus.COMPLETED.value for row in rows)


def test_one_case_failing_never_blocks_trigger_automatic_run_from_covering_the_rest():
    """Mirrors `run()`'s own existing per-Case failure isolation
    (Deliverable 6/8) -- `trigger_automatic_run` calls the identical
    locked evaluation loop, so a composition failure for one Case must
    still leave every other Case evaluated."""
    h = _harness()
    h.add_to_watchlist("AAPL")
    broken_case_id = h.add_to_watchlist("ZZZZ")

    original_build = h.composition_service.build

    def _flaky_build(case_id: str):
        if case_id == broken_case_id:
            raise RuntimeError("simulated composition failure")
        return original_build(case_id)

    h.composition_service.build = _flaky_build  # type: ignore[assignment]

    result = h.monitoring_service.trigger_automatic_run()

    assert result is not None
    case_ids = {r.case_id for r in result.results}
    assert broken_case_id not in case_ids
    assert any(cid != broken_case_id for cid in case_ids)

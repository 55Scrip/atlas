"""Activation: the due check, the cross-process lock, and what advances the
cadence.

The composition engine is proven elsewhere. These tests are about the parts
that only matter when nobody is watching: that two processes cannot compose
the same Case at once, that a crashed process does not wedge the scheduler
forever, and that a successful batch which writes nothing still counts as
having run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta, timezone

import pytest

from atlas.alpha.scheduled_composition.activation import (
    ScheduledRunOutcome,
    process_lock,
    read_state,
    run_scheduled_composition,
)
from atlas.alpha.scheduled_composition.service import (
    CaseCompositionOutcome,
    ScheduledCompositionResult,
)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
T0 = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
DAY = timedelta(hours=24)


def _result(**kwargs) -> ScheduledCompositionResult:
    defaults = dict(
        started_at=T0, duration_seconds=0.5, attempted=26, succeeded=26, failed=0,
        snapshots_written=0, snapshots_deduplicated=26,
        outcomes=(CaseCompositionOutcome(case_id="c1", ticker="AAA", composed=True, snapshot_written=False),),
    )
    defaults.update(kwargs)
    return ScheduledCompositionResult(**defaults)


class _Service:
    def __init__(self, result=None, raises=None) -> None:
        self._result = result if result is not None else _result()
        self._raises = raises
        self.runs = 0

    def run(self, *, scope=None):
        self.runs += 1
        if self._raises is not None:
            raise self._raises
        return self._result


@pytest.fixture
def paths(tmp_path):
    return {"state_path": tmp_path / "state.json", "lock_path": tmp_path / "run.lock"}


# --- Due-state ---------------------------------------------------------


def test_the_first_scheduled_run_is_due(paths) -> None:
    service = _Service()
    report = run_scheduled_composition(service, now=T0, interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.RAN
    assert service.runs == 1


def test_a_successful_run_records_its_completion(paths) -> None:
    run_scheduled_composition(_Service(), now=T0, interval=DAY, **paths)
    state = read_state(paths["state_path"])
    assert state.last_success_at is not None
    assert state.last_outcome == "ok"


def test_an_immediate_second_trigger_is_not_due(paths) -> None:
    service = _Service()
    run_scheduled_composition(service, now=T0, interval=DAY, **paths)
    report = run_scheduled_composition(service, interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.NOT_DUE
    assert service.runs == 1, "a not-due trigger must compose nothing"


def test_not_due_just_before_the_interval_elapses(paths) -> None:
    service = _Service()
    paths["state_path"].write_text(json.dumps({"last_success_at": T0.isoformat()}))
    report = run_scheduled_composition(service, now=T0 + DAY - timedelta(seconds=1), interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.NOT_DUE
    assert service.runs == 0


def test_due_exactly_on_the_interval_boundary(paths) -> None:
    service = _Service()
    paths["state_path"].write_text(json.dumps({"last_success_at": T0.isoformat()}))
    report = run_scheduled_composition(service, now=T0 + DAY, interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.RAN
    assert service.runs == 1


def test_a_run_that_writes_nothing_still_advances_the_cadence(paths) -> None:
    """The expected steady state. If an unchanged corpus did not advance the
    cadence, every single tick would re-run the whole batch forever."""
    service = _Service(_result(snapshots_written=0, snapshots_deduplicated=26))
    first = run_scheduled_composition(service, now=T0, interval=DAY, **paths)
    assert first.outcome is ScheduledRunOutcome.RAN
    assert first.result.snapshots_written == 0
    assert run_scheduled_composition(service, interval=DAY, **paths).outcome is ScheduledRunOutcome.NOT_DUE


def test_snapshot_time_is_never_used_as_scheduler_state(paths) -> None:
    """Cadence is read from the operational state file, not from history: a
    successful batch can write no snapshot at all."""
    run_scheduled_composition(_Service(), now=T0, interval=DAY, **paths)
    payload = json.loads(paths["state_path"].read_text())
    assert payload["schema"] == "scheduled_composition_state_v1"
    assert payload["last_success_at"]


def test_not_due_is_answered_even_while_a_batch_is_running(paths) -> None:
    """Cadence is checked before the lock is contested. An hourly trigger
    that is not due should say so, not report that something else holds the
    lock -- those are different facts, and only one of them is true."""
    service = _Service()
    paths["state_path"].write_text(json.dumps({"last_success_at": T0.isoformat()}))
    with process_lock(paths["lock_path"]) as held:
        assert held
        report = run_scheduled_composition(service, now=T0 + timedelta(hours=1), interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.NOT_DUE
    assert service.runs == 0


def test_a_naive_stored_timestamp_is_read_as_utc(paths) -> None:
    """Operational state is a plain file a human can open and edit. A
    timestamp written without an offset must not make every later comparison
    raise -- that would stop the scheduler permanently."""
    paths["state_path"].write_text(json.dumps({"last_success_at": "2026-09-16T12:00:00"}))
    state = read_state(paths["state_path"])
    assert state.last_success_at == T0
    report = run_scheduled_composition(_Service(), now=T0 + timedelta(hours=1), interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.NOT_DUE


def test_the_next_due_time_is_reported(paths) -> None:
    report = run_scheduled_composition(_Service(), now=T0, interval=DAY, **paths)
    assert report.next_due_at == report.last_success_at + DAY


# --- Failure semantics -------------------------------------------------


def test_an_infrastructure_failure_does_not_advance_the_cadence(paths) -> None:
    """This batch did not happen, so the next trigger must retry rather than
    wait out a full interval."""
    service = _Service(raises=RuntimeError("database is locked"))
    report = run_scheduled_composition(service, now=T0, interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.FAILED
    assert read_state(paths["state_path"]).last_success_at is None
    assert run_scheduled_composition(_Service(), now=T0, interval=DAY, **paths).outcome is ScheduledRunOutcome.RAN


def test_a_failure_is_summarised_not_dumped(paths) -> None:
    report = run_scheduled_composition(_Service(raises=RuntimeError("x" * 900)), now=T0, interval=DAY, **paths)
    assert report.detail.startswith("RuntimeError: ")
    assert len(report.detail) == len("RuntimeError: ") + 200


def test_isolated_case_failures_still_advance_the_cadence(paths) -> None:
    """The documented doctrine: the invocation completed, and `service.run`
    already isolated the failures. Withholding the advance would let one
    permanently broken Case turn a daily job into a batch on every tick."""
    service = _Service(_result(attempted=26, succeeded=25, failed=1))
    report = run_scheduled_composition(service, now=T0, interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.RAN
    assert read_state(paths["state_path"]).last_outcome == "partial"
    assert run_scheduled_composition(service, interval=DAY, **paths).outcome is ScheduledRunOutcome.NOT_DUE


def test_corrupt_state_means_never_ran_rather_than_crashing(paths) -> None:
    paths["state_path"].write_text("{not json")
    assert read_state(paths["state_path"]).last_success_at is None
    assert run_scheduled_composition(_Service(), now=T0, interval=DAY, **paths).outcome is ScheduledRunOutcome.RAN


# --- Manual override ---------------------------------------------------


def test_a_forced_run_ignores_the_cadence(paths) -> None:
    service = _Service()
    run_scheduled_composition(service, now=T0, interval=DAY, **paths)
    report = run_scheduled_composition(service, now=T0, interval=DAY, force=True, **paths)
    assert report.outcome is ScheduledRunOutcome.RAN
    assert service.runs == 2


def test_a_forced_run_still_respects_the_lock(paths) -> None:
    """Forcing a batch is not a reason to run two at once."""
    service = _Service()
    with process_lock(paths["lock_path"]) as acquired:
        assert acquired
        report = run_scheduled_composition(service, now=T0, interval=DAY, force=True, **paths)
    assert report.outcome is ScheduledRunOutcome.ALREADY_RUNNING
    assert service.runs == 0


# --- The cross-process lock -------------------------------------------


def test_a_second_holder_is_refused_rather_than_blocked(paths) -> None:
    with process_lock(paths["lock_path"]) as first:
        assert first
        with process_lock(paths["lock_path"]) as second:
            assert second is False


def test_the_lock_is_released_after_use(paths) -> None:
    with process_lock(paths["lock_path"]) as acquired:
        assert acquired
    with process_lock(paths["lock_path"]) as again:
        assert again


def test_the_lock_is_released_when_the_body_raises(paths) -> None:
    with pytest.raises(ValueError):
        with process_lock(paths["lock_path"]):
            raise ValueError("boom")
    with process_lock(paths["lock_path"]) as again:
        assert again


def _child(lock_path, script_tail: str) -> subprocess.Popen:
    script = textwrap.dedent(f"""
        import sys, time
        sys.path.insert(0, {REPO!r})
        from pathlib import Path
        from atlas.alpha.scheduled_composition.activation import process_lock
        with process_lock(Path({str(lock_path)!r})) as got:
            print("ACQUIRED" if got else "REFUSED", flush=True)
            {script_tail}
    """)
    return subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, text=True)


def test_a_separate_process_cannot_take_a_held_lock(paths) -> None:
    """The reason `threading.Lock` is not enough: a batch run from a command
    and the API serving a page are two processes."""
    with process_lock(paths["lock_path"]) as acquired:
        assert acquired
        child = _child(paths["lock_path"], "pass")
        assert child.stdout.readline().strip() == "REFUSED"
        child.wait(10)


def test_a_later_process_acquires_once_the_first_exits(paths) -> None:
    child = _child(paths["lock_path"], "pass")
    assert child.stdout.readline().strip() == "ACQUIRED"
    child.wait(10)
    with process_lock(paths["lock_path"]) as acquired:
        assert acquired, "the lock file outlived the process that held it"


def test_a_killed_process_does_not_wedge_the_scheduler(paths) -> None:
    """The whole reason for an OS advisory lock rather than a lock file: the
    kernel drops it when the holder dies, so a crash cannot leave the daily
    job permanently locked with nobody to clean up."""
    child = _child(paths["lock_path"], "time.sleep(60)")
    assert child.stdout.readline().strip() == "ACQUIRED"
    child.kill()
    child.wait(10)
    with process_lock(paths["lock_path"]) as acquired:
        assert acquired, "a killed holder left the lock stuck"
    assert paths["lock_path"].exists(), "the lock file is deliberately never unlinked"


def test_two_due_processes_produce_exactly_one_batch(paths) -> None:
    """The lock's primary responsibility."""
    service = _Service()
    with process_lock(paths["lock_path"]) as held:
        assert held
        blocked = run_scheduled_composition(service, now=T0, interval=DAY, **paths)
    assert blocked.outcome is ScheduledRunOutcome.ALREADY_RUNNING
    assert service.runs == 0
    assert run_scheduled_composition(service, now=T0, interval=DAY, **paths).outcome is ScheduledRunOutcome.RAN
    assert service.runs == 1


def test_a_batch_finishing_between_the_check_and_the_lock_is_not_repeated(paths, monkeypatch) -> None:
    """Two triggers can both see "due" before either takes the lock. The
    loser must re-read the state under the lock, or it composes the whole
    scope a second time immediately."""
    service = _Service()
    real = process_lock
    raced = []

    def racing(path):
        if not raced:
            raced.append(True)
            # Another process completes the batch while this one waits.
            run_scheduled_composition(_Service(), now=T0, interval=DAY, **paths)
        return real(path)

    monkeypatch.setattr("atlas.alpha.scheduled_composition.activation.process_lock", racing)
    report = run_scheduled_composition(service, now=T0, interval=DAY, **paths)
    assert report.outcome is ScheduledRunOutcome.NOT_DUE
    assert service.runs == 0


# --- Operational separation -------------------------------------------


def test_scheduler_state_stays_outside_the_database(paths) -> None:
    """It records when a job ran. It is not evidence, not a BusinessFact, and
    must never become part of what Atlas concluded about a company."""
    run_scheduled_composition(_Service(), now=T0, interval=DAY, **paths)
    payload = json.loads(paths["state_path"].read_text())
    assert set(payload) <= {"schema", "last_success_at", "last_outcome", "last_run"}
    assert "case_id" not in paths["state_path"].read_text()


def test_the_report_states_the_outcome_rather_than_implying_it(paths) -> None:
    assert {o.value for o in ScheduledRunOutcome} == {"ran", "not_due", "already_running", "failed"}

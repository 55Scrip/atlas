"""Making a scheduled batch safe to run unattended, repeatedly, forever.

Composing the followed Cases is already proven. What was missing is the part
that decides *whether to run at all* when nobody is watching, and that has
two jobs.

**Only one batch at a time, across processes.** The service's own
`threading.Lock` serializes callers inside one interpreter and nothing else:
a batch launched from a terminal and the API serving a page are two
processes, and that lock is invisible between them. Two batches composing the
same Case concurrently would both read the same snapshot head, both conclude
the record moved, and both write -- turning one analytical movement into two
rows in the history this exists to build. So the authoritative guard is a
POSIX advisory lock (`flock`), which is held by the *file descriptor*: when a
process dies, crashes, or is killed -9, the kernel drops the lock. A plain
"does the lock file exist" check cannot say that, and a crash would wedge the
scheduler until someone noticed and deleted a file. The lock file is created
once and never deleted -- deleting it is what reintroduces the race.

Snapshot dedup is deliberately *not* used as the lock. Dedup decides whether
the record moved; this decides whether a batch may run. Both exist, and
neither substitutes for the other.

**Due, not driven.** A trigger firing is an opportunity to compose, never an
instruction to write. What defines "last run" is the completion of a
successful batch, recorded here -- explicitly not the newest snapshot
timestamp, because a perfectly successful batch over unchanged evidence
writes zero snapshots, and reading cadence off snapshots would make an
unchanged corpus re-run the full batch on every single tick, forever.

The state this keeps is operational. It records when a job ran. It is not a
BusinessFact, not evidence, not Decision Memory, and nothing in it is
allowed to become part of what Atlas concluded about a company.
"""
from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Iterator

from atlas.alpha.scheduled_composition.cadence import configured_interval, is_due
from atlas.alpha.scheduled_composition.service import ScheduledCompositionResult

__all__ = [
    "STATE_SCHEMA",
    "ScheduledRunOutcome",
    "ScheduledRunReport",
    "SchedulerState",
    "process_lock",
    "read_state",
    "resolve_lock_path",
    "resolve_state_path",
    "run_scheduled_composition",
]

#: `fcntl` is POSIX. Atlas Internal Alpha runs on one macOS machine, which is
#: the whole deployment, so this is stated rather than abstracted away. A
#: Windows port would need its own lock; silently falling back to a weaker
#: one would be worse than failing to import.
STATE_SCHEMA = "scheduled_composition_state_v1"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _runtime_dir() -> Path:
    """Operational state, deliberately beside the database rather than in it:
    no table, no migration, and no chance of it being mistaken for history."""
    from atlas.config import BASE_DIR

    return Path(BASE_DIR) / "runtime"


def resolve_lock_path(explicit: str | Path | None = None) -> Path:
    return Path(explicit) if explicit is not None else _runtime_dir() / "scheduled_composition.lock"


def resolve_state_path(explicit: str | Path | None = None) -> Path:
    return Path(explicit) if explicit is not None else _runtime_dir() / "scheduled_composition.json"


class ScheduledRunOutcome(str, Enum):
    """What a trigger actually did -- stated, never inferred from logs."""

    RAN = "ran"
    NOT_DUE = "not_due"
    ALREADY_RUNNING = "already_running"
    FAILED = "failed"


@dataclass(frozen=True)
class SchedulerState:
    last_success_at: datetime | None = None
    last_outcome: str | None = None


@dataclass(frozen=True)
class ScheduledRunReport:
    outcome: ScheduledRunOutcome
    last_success_at: datetime | None = None
    next_due_at: datetime | None = None
    result: ScheduledCompositionResult | None = None
    detail: str | None = None

    @property
    def summary(self) -> str:
        if self.outcome is ScheduledRunOutcome.RAN and self.result is not None:
            return f"ran: {self.result.summary}"
        if self.outcome is ScheduledRunOutcome.NOT_DUE:
            return f"not due: next at {self.next_due_at.isoformat() if self.next_due_at else 'unknown'}"
        if self.outcome is ScheduledRunOutcome.ALREADY_RUNNING:
            return "already running: another scheduled batch holds the lock; skipped"
        return f"failed: {self.detail}"


@contextmanager
def process_lock(path: Path) -> Iterator[bool]:
    """Yield True if this process now owns the scheduled-run lock.

    Non-blocking on purpose: a tick that arrives while a batch is running is
    redundant, not urgent. It asks what Atlas concludes from what is stored
    right now, and the batch already running is asking exactly that against
    strictly newer state -- so skipping loses nothing, while queueing would
    let a slow batch accumulate ticks that all want its work.

    The file is never unlinked. The lock lives on the open descriptor, so the
    kernel releases it if this process dies; removing the file would let a
    second process create and lock a *different* inode under the same name.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            os.ftruncate(descriptor, 0)
            os.write(descriptor, f"pid={os.getpid()} since={_utc_now().isoformat()}\n".encode())
            os.fsync(descriptor)
            yield True
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def read_state(path: Path) -> SchedulerState:
    """A missing, empty or corrupt state file means "never ran successfully",
    which is due. Operational bookkeeping must not be able to stop Atlas."""
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return SchedulerState()
    raw = payload.get("last_success_at")
    try:
        at = datetime.fromisoformat(raw) if raw else None
    except (TypeError, ValueError):
        at = None
    if at is not None and at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    return SchedulerState(last_success_at=at, last_outcome=payload.get("last_outcome"))


def _write_state(path: Path, state: SchedulerState, result: ScheduledCompositionResult | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": STATE_SCHEMA,
        "last_success_at": state.last_success_at.isoformat() if state.last_success_at else None,
        "last_outcome": state.last_outcome,
    }
    if result is not None:
        payload["last_run"] = {
            "attempted": result.attempted, "succeeded": result.succeeded, "failed": result.failed,
            "snapshots_written": result.snapshots_written,
            "snapshots_deduplicated": result.snapshots_deduplicated,
            "duration_seconds": round(result.duration_seconds, 3),
        }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=1, sort_keys=True))
    os.replace(temporary, path)


def run_scheduled_composition(
    service,
    *,
    scope=None,
    state_path: Path | None = None,
    lock_path: Path | None = None,
    now: datetime | None = None,
    interval: timedelta | None = None,
    force: bool = False,
) -> ScheduledRunReport:
    """The canonical entry point a recurring trigger calls.

    Checks whether a batch is due, takes the cross-process lock, runs one
    batch, and records the completion that defines the next due time.

    `force` is the operator's manual run: it still takes the lock -- forcing a
    batch is not a reason to run two at once -- but ignores the cadence.

    `scope` is passed straight through, so a caller that has already reported
    which Cases it is about to compose composes exactly those, rather than
    re-reading membership that may have changed in between.
    """
    now = now or _utc_now()
    interval = interval if interval is not None else configured_interval()
    state_path = resolve_state_path(state_path)
    lock_path = resolve_lock_path(lock_path)

    state = read_state(state_path)
    if not force and not is_due(state.last_success_at, now, interval):
        return ScheduledRunReport(
            outcome=ScheduledRunOutcome.NOT_DUE, last_success_at=state.last_success_at,
            next_due_at=state.last_success_at + interval if state.last_success_at else now)

    with process_lock(lock_path) as acquired:
        if not acquired:
            return ScheduledRunReport(
                outcome=ScheduledRunOutcome.ALREADY_RUNNING, last_success_at=state.last_success_at,
                next_due_at=state.last_success_at + interval if state.last_success_at else None)

        # Re-read under the lock. Between the check above and acquiring it,
        # another process may have completed the very batch this would repeat.
        state = read_state(state_path)
        if not force and not is_due(state.last_success_at, now, interval):
            return ScheduledRunReport(
                outcome=ScheduledRunOutcome.NOT_DUE, last_success_at=state.last_success_at,
                next_due_at=state.last_success_at + interval if state.last_success_at else now)

        try:
            result = service.run(scope=scope)
        except Exception as error:  # noqa: BLE001 -- infrastructure failed, not a Case
            # The cadence is not advanced: this batch did not happen, so the
            # next trigger should retry rather than wait a full interval.
            # Cases already composed keep their rows; dedup makes the retry
            # cost nothing for them.
            return ScheduledRunReport(
                outcome=ScheduledRunOutcome.FAILED, last_success_at=state.last_success_at,
                next_due_at=now, detail=f"{type(error).__name__}: {str(error)[:200]}")

        # A completed invocation advances the cadence even when isolated Cases
        # failed. The batch ran; `service.run` already isolated those failures
        # and they retry on the next ordinary run. Withholding the advance
        # instead would let one permanently broken Case turn a daily job into
        # a full batch on every tick, forever -- the retry storm this cadence
        # exists to prevent. A run that writes zero snapshots is likewise a
        # complete success: unchanged evidence is the expected steady state.
        completed = _utc_now()
        _write_state(state_path, SchedulerState(last_success_at=completed,
                                                last_outcome="partial" if result.failed else "ok"), result)
        return ScheduledRunReport(outcome=ScheduledRunOutcome.RAN, last_success_at=completed,
                                  next_due_at=completed + interval, result=result)

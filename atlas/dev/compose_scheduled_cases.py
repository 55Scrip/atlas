"""Compose every Portfolio and Watchlist Case once, from stored evidence
only -- Scheduled Case Composition v1.

Atlas can freeze the evidence behind a conclusion and read it back, but only
a composed Case records anything, and until now only a person opening a Case
composed one. This walks the Cases the investor holds or watches and composes
each through the ordinary production path, so the longitudinal record
accumulates without anyone visiting twenty-six pages by hand.

**No provider is called.** Composition reads SQLite and cannot reach the
network -- no quote, no filing, no refresh. A Case whose stored data is stale
composes honestly from that stale data; it does not go looking. This command
therefore makes Atlas's conclusions *observable over time*; it does not make
them *newer*. Refreshing data is a different, explicit operation.

**Re-running is safe and usually writes nothing.** A snapshot is written only
when the existing persistence doctrine says the record moved -- a changed
conclusion, or changed evidence beneath an unchanged conclusion -- so a second
run over unchanged data writes zero rows. One Case failing costs that Case
and no other.

**Two modes.** By default this composes immediately: the operator asked for a
batch, so a batch happens regardless of when the last one ran. With
`--scheduled` it is due-aware -- the mode the recurring trigger uses -- and
composes only if the configured interval has elapsed since the last
*successful* batch, reporting `not_due` otherwise. Either way it takes a
cross-process lock and reports `already_running` rather than queueing if
another batch is in flight, so two overlapping invocations can never both
compose the same Case.

    python -m atlas.dev.compose_scheduled_cases [--database PATH]
        [--scheduled] [--list-scope] [--dry-run] [--state PATH] [--lock PATH]
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine

from atlas.alpha.scheduled_composition.activation import (
    ScheduledRunOutcome,
    read_state,
    resolve_lock_path,
    resolve_state_path,
    run_scheduled_composition,
)
from atlas.alpha.scheduled_composition.cadence import INTERVAL_ENV_VAR, configured_interval
from atlas.alpha.scheduled_composition.factory import build_scheduled_composition_service
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def main(argv: list[str] | None = None) -> int:
    ensure_development_environment()

    parser = argparse.ArgumentParser(
        prog="python -m atlas.dev.compose_scheduled_cases",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--database", default=None, help="Path to the Atlas database (default: the resolved one).")
    parser.add_argument("--list-scope", action="store_true",
                        help="Print the Cases a batch would compose, then stop. Composes nothing.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report the scope and cadence without composing. Writes nothing.")
    parser.add_argument("--scheduled", action="store_true",
                        help="Due-aware mode, for the recurring trigger: compose only if the configured "
                             "interval has elapsed since the last successful batch, and skip if another "
                             "batch is already running. Without it this command composes immediately.")
    parser.add_argument("--state", default=None, help="Scheduler state file (default: <ATLAS_HOME>/runtime).")
    parser.add_argument("--lock", default=None, help="Scheduler lock file (default: <ATLAS_HOME>/runtime).")
    arguments = parser.parse_args(argv)

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    service = build_scheduled_composition_service(engine)
    scope = service.scope()

    state_path = resolve_state_path(arguments.state)
    lock_path = resolve_lock_path(arguments.lock)
    state = read_state(state_path)
    interval = configured_interval()

    header = [
        f"database        : {path}",
        f"scope           : {len(scope)} Cases (Portfolio holdings + Watchlist entries)",
        f"cadence         : {int(interval.total_seconds())}s (${INTERVAL_ENV_VAR}); "
        f"{'due-aware run' if arguments.scheduled else 'manual run, cadence ignored'}",
        f"last success    : {state.last_success_at.isoformat() if state.last_success_at else 'never'}",
        f"next due        : "
        f"{(state.last_success_at + interval).isoformat() if state.last_success_at else 'now'}",
        "providers       : none reachable from composition (0 requests)",
    ]

    if arguments.list_scope or arguments.dry_run:
        for line in header:
            print(line)
        for case_id, ticker in scope:
            print(f"    {ticker or '-':<8} {case_id}")
        print("\n[dry run] nothing composed, nothing written.")
        return 0

    report = run_scheduled_composition(
        service, scope=scope, state_path=state_path, lock_path=lock_path,
        interval=interval, force=not arguments.scheduled)

    # A recurring trigger fires far more often than the cadence, so the
    # ordinary answer is "not yet". Printing the whole report every time would
    # turn an hourly job into an unbounded log of non-events; one line keeps
    # the record useful without a rotation mechanism nobody asked for.
    if arguments.scheduled and report.outcome in (
            ScheduledRunOutcome.NOT_DUE, ScheduledRunOutcome.ALREADY_RUNNING):
        print(f"{_utc_now().isoformat()} scheduled composition: {report.summary}")
        return 0

    for line in header:
        print(line)
    print(f"\noutcome         : {report.outcome.value}")
    if report.outcome is not ScheduledRunOutcome.RAN:
        print(f"                  {report.summary}")
        if report.next_due_at is not None:
            print(f"next due        : {report.next_due_at.isoformat()}")
        # Nothing was composed, and that is a correct, expected answer for a
        # recurring trigger -- not a failure to report to the OS scheduler.
        return 0 if report.outcome is not ScheduledRunOutcome.FAILED else 1

    result = report.result

    print(f"\nstarted         : {result.started_at.isoformat()}")
    for outcome in result.outcomes:
        if outcome.error is not None:
            print(f"    FAILED    {outcome.ticker or '-':<8} {outcome.case_id}: {outcome.error}", file=sys.stderr)
        elif outcome.snapshot_written:
            print(f"    recorded  {outcome.ticker or '-':<8} {outcome.case_id}")
    print(f"attempted       : {result.attempted}")
    print(f"succeeded       : {result.succeeded}")
    print(f"failed          : {result.failed}")
    print(f"snapshots written: {result.snapshots_written}")
    print(f"unchanged (deduplicated): {result.snapshots_deduplicated}")
    print(f"duration        : {result.duration_seconds:.1f}s")
    print("provider calls  : 0")
    print(f"next due        : {report.next_due_at.isoformat() if report.next_due_at else '-'}")
    if result.failed:
        print(f"  {result.failed} Case(s) did not compose -- the rest did", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

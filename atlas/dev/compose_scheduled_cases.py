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

**In-process locking only.** If the API is serving the same database, that
process's own composition is not serialized against this one by anything but
SQLite's file lock. Prefer running this when the app is idle.

    python -m atlas.dev.compose_scheduled_cases [--database PATH] [--list-scope] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine

from atlas.alpha.scheduled_composition.cadence import INTERVAL_ENV_VAR, configured_interval
from atlas.alpha.scheduled_composition.factory import build_scheduled_composition_service
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment


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
    arguments = parser.parse_args(argv)

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    service = build_scheduled_composition_service(engine)
    scope = service.scope()

    print(f"database        : {path}")
    print(f"scope           : {len(scope)} Cases (Portfolio holdings + Watchlist entries)")
    print(f"cadence         : {int(configured_interval().total_seconds())}s (${INTERVAL_ENV_VAR}); "
          f"no recurring trigger is wired -- this command is the only way a batch runs")
    print("providers       : none reachable from composition (0 requests)")

    if arguments.list_scope or arguments.dry_run:
        for case_id, ticker in scope:
            print(f"    {ticker or '-':<8} {case_id}")
        print("\n[dry run] nothing composed, nothing written.")
        return 0

    result = service.run(scope=scope)

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
    if result.failed:
        print(f"  {result.failed} Case(s) did not compose -- the rest did", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

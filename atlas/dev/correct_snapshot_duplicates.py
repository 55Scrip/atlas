"""Retract snapshot rows duplicated by the pre-atomic persistence race.

Before `repository.add` took SQLite's write lock before reading the head, two
composers of the same Case could both decide the record had moved and both
insert -- leaving two rows identical in every semantic field, milliseconds
apart. Each such pair makes the history say Atlas observed something twice
when it observed it once. The race is fixed; these are the rows it already
left behind.

Nothing is deleted. The later row is retracted -- it keeps every column it
had and gains a pointer to a ledger entry naming the row that survived, the
reason, and every check that had to pass first.

**Discovery proposes; it never applies.** `--discover` prints the pairs it can
prove, as ready-to-paste `--pair` arguments. Applying then names explicit row
ids, so what was corrected is exactly what was reviewed, and a correction can
never quietly widen its own scope.

A pair is only proposed when every semantic field matches -- conclusion,
stored payload, transition, frozen evidence -- and the two rows are adjacent
in the surviving timeline. Being milliseconds apart is what makes the race the
likely explanation; it is never the proof. Two rows with the same conclusion
separated by a different observation are a real return to an earlier state,
and rows whose evidence differs beneath an unchanged conclusion are exactly
what Snapshot Evidence Persistence exists to keep.

    python -m atlas.dev.correct_snapshot_duplicates --discover [--database PATH]
    python -m atlas.dev.correct_snapshot_duplicates --pair CANONICAL_ID::DUPLICATE_ID [...]
        [--correction-id ID] [--dry-run] [--database PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from sqlalchemy import create_engine, select

from atlas.alpha.investment_case_change.table import investment_case_snapshot_table
from atlas.alpha.snapshot_correction.service import (
    CorrectionRefused,
    DuplicateCorrectionRequest,
    DuplicatePair,
    apply_correction,
    ensure_schema,
    plan_correction,
)
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

_DEFAULT_REASON = (
    "Concurrent snapshot duplicate: written twice by two composers of the same Case racing "
    "before snapshot persistence became atomic (repository.add now takes the write lock before "
    "reading the head). Both rows are identical in conclusion, stored payload, transition and "
    "frozen evidence, and adjacent in the surviving timeline; the earlier row survives."
)


def _tickers(connection) -> dict[str, str]:
    try:
        rows = connection.exec_driver_sql(
            "select case_id, instrument_key from case_instrument_bindings").fetchall()
    except Exception:  # noqa: BLE001 -- display only; a missing binding table is not an error here
        return {}
    return {case_id: ticker for case_id, ticker in rows}


def _discover(connection) -> list[tuple[str, str, str, float]]:
    """Adjacent live pairs that are identical in every semantic field."""
    rows = (
        connection.execute(
            select(investment_case_snapshot_table)
            .where(investment_case_snapshot_table.c.retracted_by.is_(None))
            .order_by(investment_case_snapshot_table.c.case_id,
                      investment_case_snapshot_table.c.captured_at)
        )
        .mappings()
        .all()
    )
    by_case: dict[str, list] = {}
    for row in rows:
        by_case.setdefault(row["case_id"], []).append(row)

    found = []
    for case_id, entries in by_case.items():
        for earlier, later in zip(entries, entries[1:]):
            if (earlier["content_hash"] == later["content_hash"]
                    and earlier["snapshot_json"] == later["snapshot_json"]
                    and earlier["change_intelligence_json"] == later["change_intelligence_json"]
                    and earlier["current_yield"] == later["current_yield"]):
                gap = ((datetime.fromisoformat(later["captured_at"])
                        - datetime.fromisoformat(earlier["captured_at"])).total_seconds() * 1000)
                found.append((case_id, earlier["id"], later["id"], round(gap, 3)))
    return found


def main(argv: list[str] | None = None) -> int:
    ensure_development_environment()

    parser = argparse.ArgumentParser(
        prog="python -m atlas.dev.correct_snapshot_duplicates",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--discover", action="store_true",
                        help="Print the provable pairs and stop. Corrects nothing.")
    parser.add_argument("--pair", action="append", default=[], metavar="CANONICAL::DUPLICATE",
                        help="Explicit row ids to correct. Repeatable.")
    parser.add_argument("--correction-id", default=None,
                        help="Ledger id. Re-using one makes the correction idempotent.")
    parser.add_argument("--reason", default=_DEFAULT_REASON)
    parser.add_argument("--dry-run", action="store_true", help="Plan and report; write nothing.")
    arguments = parser.parse_args(argv)

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    ensure_schema(engine)
    print(f"database        : {path}")

    if arguments.discover:
        with engine.connect() as connection:
            tickers = _tickers(connection)
            found = _discover(connection)
        print(f"provable duplicate pairs: {len(found)}\n")
        for case_id, canonical, duplicate, gap in found:
            print(f"  {tickers.get(case_id, case_id):8} gap {gap:9.3f} ms")
            print(f"    --pair '{canonical}::{duplicate}' \\")
        print("\n[discovery] nothing corrected. Re-run with the --pair arguments above.")
        return 0

    if not arguments.pair:
        parser.error("give --discover, or one or more --pair CANONICAL::DUPLICATE")

    pairs = []
    for raw in arguments.pair:
        canonical, separator, duplicate = raw.partition("::")
        if not separator or not canonical or not duplicate:
            parser.error(f"--pair must be CANONICAL_ID::DUPLICATE_ID, got {raw!r}")
        pairs.append(DuplicatePair(canonical_row_id=canonical, duplicate_row_id=duplicate))

    correction_id = arguments.correction_id or "concurrency-duplicates-v1"
    request = DuplicateCorrectionRequest(
        correction_id=correction_id, reason=arguments.reason, pairs=tuple(pairs))

    with engine.connect() as connection:
        tickers = _tickers(connection)

    try:
        plan = plan_correction(engine, request) if arguments.dry_run else apply_correction(engine, request)
    except CorrectionRefused as refusal:
        print(f"\nREFUSED: {refusal}", file=sys.stderr)
        return 2

    print(f"correction id   : {correction_id}")
    print(f"kind            : {request.kind}")
    print(f"pairs given     : {len(plan.retractions)}")
    print(f"already applied : {len(plan.retractions) - len(plan.pending)}")
    print(f"{'would retract' if arguments.dry_run else 'retracted'}   : {len(plan.pending)}\n")
    for retraction in plan.retractions:
        mark = "already" if retraction.already_applied else ("plan" if arguments.dry_run else "done")
        print(f"  [{mark:7}] {tickers.get(retraction.case_id, retraction.case_id):8} "
              f"gap {retraction.gap_milliseconds:9.3f} ms  hash {retraction.content_hash[:12]}")
        print(f"             survives  {retraction.canonical_row_id}")
        print(f"             retracted {retraction.duplicate_row_id}")
        failed = [k for k, v in retraction.verification.items() if v is False]
        print(f"             checks    {len(retraction.verification)} recorded"
              + (f", FAILED {failed}" if failed else ", all passed"))
    if arguments.dry_run:
        print("\n[dry run] nothing written.")
    print("provider calls  : 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())

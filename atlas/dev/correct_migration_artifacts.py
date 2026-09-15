"""Correct the artifacts a methodology migration wrote by running in the
wrong order (`atlas.alpha.migration_correction`): retract transient rows and
recompute the transitions diffed against them. Rows are named by explicit id,
of one explicit Case; nothing is deleted; every write is audited in
`migration_artifact_corrections`.

The default is a dry run, which writes nothing: when the database does not
yet have the correction schema, the plan is made against a temporary copy
that has it. `--apply` adds the schema, re-verifies and writes in one
transaction; a second `--apply` of the same correction writes nothing.

    python -m atlas.dev.correct_migration_artifacts --database PATH --case-id ID \\
        --reason TEXT --window-start ISO --window-end ISO \\
        [--retract-snapshot ID]... [--recompute-snapshot ID]... \\
        [--retract-memory ID]... [--recompute-memory ID]... \\
        [--retract-change-log ID]... [--apply]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine

from atlas.alpha.migration_correction.service import (
    CorrectionPlan,
    CorrectionRefused,
    CorrectionRequest,
    apply_correction,
    correction_schema_present,
    ensure_correction_schema,
    plan_correction,
)
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment


def _print_plan(plan: CorrectionPlan) -> None:
    print(f"correction {plan.correction_id}  case {plan.request.case_id}")
    print(f"  reason: {plan.request.reason}")
    print(f"  window: {plan.request.window_start.isoformat()} .. {plan.request.window_end.isoformat()}")
    print(f"  methodology: {plan.methodology}")
    for write in plan.writes:
        state = "already applied" if write.already_applied else "pending"
        print(f"  [{state}] {write.action} {write.target_table} {write.target_row_id}")
        if write.predecessor_row_id is not None:
            print(f"      against surviving predecessor {write.predecessor_row_id}")
        for column, value in write.after.items():
            print(f"      {column}: {write.before.get(column)!r}")
            print(f"        -> {value!r}")
    print("  verification:")
    print(json.dumps(plan.verification, indent=2, sort_keys=True, default=str))
    print(f"  {len(plan.pending)} pending of {len(plan.writes)} writes")


def main(argv: list[str] | None = None) -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--window-start", required=True, type=datetime.fromisoformat)
    parser.add_argument("--window-end", required=True, type=datetime.fromisoformat)
    for flag in ("retract-snapshot", "recompute-snapshot", "retract-memory", "recompute-memory", "retract-change-log"):
        parser.add_argument(f"--{flag}", action="append", default=[], metavar="ID")
    parser.add_argument("--apply", action="store_true", help="write the correction (default: dry run)")
    arguments = parser.parse_args(argv)

    request = CorrectionRequest(
        case_id=arguments.case_id,
        reason=arguments.reason,
        window_start=arguments.window_start,
        window_end=arguments.window_end,
        retract_snapshot_ids=tuple(arguments.retract_snapshot),
        recompute_snapshot_ids=tuple(arguments.recompute_snapshot),
        retract_memory_ids=tuple(arguments.retract_memory),
        recompute_memory_ids=tuple(arguments.recompute_memory),
        retract_change_log_ids=tuple(arguments.retract_change_log),
    )
    database = Path(arguments.database or resolve_database_path())
    if not database.is_file():
        print(f"REFUSED: no database at {database}", file=sys.stderr)
        return 2
    engine = create_engine(f"sqlite:///{database}", future=True)

    try:
        if arguments.apply:
            ensure_correction_schema(engine)
            plan = plan_correction(engine, request)
            _print_plan(plan)
            written = apply_correction(engine, plan)
            print(f"APPLIED: {written} rows corrected" if written else "NOTHING TO DO: already applied")
            return 0
        if correction_schema_present(engine):
            _print_plan(plan_correction(engine, request))
        else:
            with tempfile.TemporaryDirectory() as scratch:
                copy_path = Path(scratch) / "plan.db"
                source = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
                with sqlite3.connect(copy_path) as copy:
                    source.backup(copy)
                source.close()
                copy_engine = create_engine(f"sqlite:///{copy_path}", future=True)
                ensure_correction_schema(copy_engine)
                print("(planned against a temporary copy with the correction schema added; --apply adds it)")
                _print_plan(plan_correction(copy_engine, request))
                copy_engine.dispose()
        print("DRY RUN: nothing written")
        return 0
    except CorrectionRefused as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 2
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())

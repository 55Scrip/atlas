"""Schema-compatibility helper shared by every bounded context's table module.

Sprint 1, Commit 7 (Revised) — SQLite Schema Validation & Safe Bootstrap.

Every `create_X_table(engine)` function across `persistence/*/table.py`
calls `metadata.create_all(engine, tables=[...])`, whose own `checkfirst`
behavior only ever *creates* a table that does not yet exist — it never
alters one that already exists. That gap is what caused Commit 6's
Dashboard validation failure: the `decisions` table predated `case_id`
being added to its model, and no code path ever updated the
already-existing table, so the schema drifted silently until a real
request hit it.

`sync_table_schema` closes that gap, but strictly within schema — never
domain data:

- A missing column that is nullable is added as-is. This is a purely
  structural repair: NULL is the honest, non-fabricated representation
  of "this row predates the column, no value was ever recorded" — it
  invents nothing.
- A missing column that is NOT NULL represents required domain
  information (e.g. `case_id`, `confidence`) that this function has no
  legitimate way to know for a row recorded before the column existed.
  An earlier version of this function synthesized a placeholder value
  (`''` for String, `0` for Integer) to satisfy the NOT NULL constraint.
  That was rejected: `case_id=''` is not a repaired schema, it is a
  fabricated fact — a row that looks structurally valid while being
  semantically meaningless (it does not reference any real Case).
  Atlas must never do this. Instead, `sync_table_schema` raises
  `IncompatibleSchemaError` — a clear, actionable failure naming the
  exact table and columns — and makes no change to that table at all.

The database this guards (`database/atlas.db`) is confirmed disposable:
gitignored, no migration framework or production persistence strategy
exists anywhere in this repository (Sprint 1, Commit 7 investigation).
`IncompatibleSchemaError`'s message reflects that — deleting the file and
restarting is the correct, developer-initiated fix; this function does
not do that automatically, since silently discarding a developer's local
data is also not this function's decision to make.

Sprint 1, Commit 11 — Persistence Table Initialization Concurrency:
every `create_X_table(engine)` function across `persistence/*/table.py`
runs on every request (via its own module's FastAPI dependency), not
just once at startup — so concurrent requests can call this function for
the same table at the same time. `create_all`'s own `checkfirst` existence
check and the `CREATE TABLE` it guards are not atomic across threads,
which is exactly the race Commit 2 first found and fixed for `cases`
(with a lock local to that one module) and Commit 10 then reproduced for
`observations` (which had no such lock). Rather than repeating that fix
in all eighteen table modules, the lock now lives here, once, keyed by
table name so unrelated tables never block each other: every module that
calls `sync_table_schema` is protected automatically, with no per-module
lock of its own to remember or forget.
"""

from __future__ import annotations

import threading
from collections import defaultdict

from sqlalchemy import Table
from sqlalchemy.engine import Engine
from sqlalchemy.inspection import inspect as sa_inspect

_table_locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)


class IncompatibleSchemaError(RuntimeError):
    """Raised when an existing table is missing a NOT NULL column.

    This is a schema incompatibility, not a domain data question:
    fabricating a value for the missing column is out of scope by
    design (see module docstring). `database/atlas.db` is a disposable,
    gitignored local development database with no migration tooling —
    deleting it and restarting the application produces a fresh,
    compatible schema.
    """


def sync_table_schema(engine: Engine, table: Table) -> None:
    """Create `table` if missing. For an existing table, add any missing
    nullable columns; raise `IncompatibleSchemaError` if any missing
    column is NOT NULL rather than fabricating a value for it.

    Concurrency-safe: serialized per table name (Sprint 1, Commit 11), so
    two threads calling this for the same table at the same time can
    never both attempt the same `CREATE TABLE`/`ALTER TABLE`. Different
    tables never block each other — each has its own lock.
    """
    with _table_locks[table.name]:
        table.metadata.create_all(engine, tables=[table], checkfirst=True)

        inspector = sa_inspect(engine)
        existing_column_names = {row["name"] for row in inspector.get_columns(table.name)}
        missing_columns = [
            column for column in table.columns if column.name not in existing_column_names
        ]

        if not missing_columns:
            return

        required_missing = [column.name for column in missing_columns if not column.nullable]
        if required_missing:
            raise IncompatibleSchemaError(
                f"Table '{table.name}' is missing required (NOT NULL) column(s) "
                f"{required_missing} that its current model declares. This table "
                "predates those columns; no value can be safely invented for rows "
                "recorded before they existed, so no automatic repair is possible. "
                f"'{table.name}' lives in a disposable local development database "
                "(database/atlas.db, gitignored, no migration framework) — delete "
                "that file and restart the application to get a fresh, compatible "
                "schema."
            )

        with engine.begin() as connection:
            for column in missing_columns:
                column_type = column.type.compile()
                connection.exec_driver_sql(
                    f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {column_type}'
                )

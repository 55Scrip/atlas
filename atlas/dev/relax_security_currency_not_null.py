"""Let the live database hold a security whose currency is unproven.

`trading_currency` and a listing's `currency` became optional in the model
(`96e0ea5`), and every test passed, because a test database is created fresh
from the current table definitions. The live database was not: it was created
when both columns were mandatory, and `sync_table_schema` only ever *adds*
columns -- SQLite cannot drop a NOT NULL constraint with `ALTER TABLE` at all.

So the previous sprint's conclusion was true of the code and false of the one
database that matters. Nothing caught it because nothing had yet tried to
write a currency-less security to the live file; the first attempt failed with
`NOT NULL constraint failed: canonical_securities.trading_currency`.

The only way to change a column's nullability in SQLite is to rebuild the
table, which is what this does: create the table as the model now defines it,
copy every row across unchanged, swap the names, restore the indexes. No value
is rewritten -- the 37 securities that have currencies keep them, and the
column merely stops *requiring* one.

    python -m atlas.dev.relax_security_currency_not_null [--database PATH] [--apply]

Dry run by default: it reports what it would change and writes nothing.
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

#: (table, column) pairs that must stop being mandatory, plus the exact
#: rebuilt schema and the indexes to restore. Written out rather than
#: generated so the migration is reviewable as the SQL it actually runs.
_REBUILDS = (
    (
        "canonical_securities",
        "trading_currency",
        """CREATE TABLE canonical_securities (
            id VARCHAR NOT NULL,
            canonical_company_name VARCHAR NOT NULL,
            native_ticker VARCHAR NOT NULL,
            primary_exchange_mic VARCHAR NOT NULL,
            country VARCHAR NOT NULL,
            trading_currency VARCHAR,
            resolution_status VARCHAR NOT NULL,
            created_at VARCHAR NOT NULL,
            updated_at VARCHAR NOT NULL,
            issuer_id VARCHAR,
            PRIMARY KEY (id)
        )""",
        (
            "CREATE INDEX ix_canonical_securities_resolution_status "
            "ON canonical_securities (resolution_status)",
            "CREATE INDEX ix_canonical_securities_native_ticker "
            "ON canonical_securities (native_ticker)",
            "CREATE INDEX ix_canonical_securities_issuer_id ON canonical_securities (issuer_id)",
        ),
    ),
    (
        "canonical_security_listings",
        "currency",
        """CREATE TABLE canonical_security_listings (
            id VARCHAR NOT NULL,
            canonical_security_id VARCHAR NOT NULL,
            ticker VARCHAR NOT NULL,
            exchange_mic VARCHAR NOT NULL,
            currency VARCHAR,
            relationship VARCHAR NOT NULL,
            security_type VARCHAR NOT NULL,
            provider_symbol VARCHAR,
            share_class VARCHAR,
            PRIMARY KEY (id)
        )""",
        (
            "CREATE INDEX ix_canonical_security_listings_canonical_security_id "
            "ON canonical_security_listings (canonical_security_id)",
        ),
    ),
)


def _columns(connection: sqlite3.Connection, table: str) -> list[tuple[str, int]]:
    return [(row[1], row[3]) for row in connection.execute(f"pragma table_info({table})")]


def _is_mandatory(connection: sqlite3.Connection, table: str, column: str) -> bool:
    return any(name == column and notnull for name, notnull in _columns(connection, table))


def _fingerprint(connection: sqlite3.Connection, table: str) -> list[tuple]:
    """Every row, ordered, so "nothing was rewritten" is checkable rather
    than asserted."""
    names = [name for name, _ in _columns(connection, table)]
    ordered = ", ".join(names)
    return list(connection.execute(f"select {ordered} from {table} order by id"))


def main(argv: list[str] | None = None) -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(
        prog="python -m atlas.dev.relax_security_currency_not_null",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--apply", action="store_true", help="Write. Without this, nothing is written.")
    arguments = parser.parse_args(argv)

    path = Path(arguments.database or resolve_database_path())
    print(f"database : {path}")
    print(f"mode     : {'APPLY' if arguments.apply else 'dry run -- nothing is written'}\n")

    connection = sqlite3.connect(path)
    pending = [r for r in _REBUILDS if _is_mandatory(connection, r[0], r[1])]
    for table, column, _, _ in _REBUILDS:
        state = "MANDATORY -- needs rebuild" if _is_mandatory(connection, table, column) else "already optional"
        rows = connection.execute(f"select count(*) from {table}").fetchone()[0]
        populated = connection.execute(
            f"select count(*) from {table} where {column} is not null").fetchone()[0]
        print(f"  {table}.{column:18} {state:26} {rows} rows, {populated} with a value")
    if not pending:
        print("\nNothing to do.")
        return 0
    if not arguments.apply:
        print("\n[dry run] nothing written.")
        return 0

    backup = path.with_name(f"{path.name}.before-currency-nullable-"
                            f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    shutil.copy2(path, backup)
    print(f"\nbackup   : {backup}")

    before = {table: _fingerprint(connection, table) for table, _, _, _ in pending}

    # `foreign_keys` must be off across the rename, and it cannot be changed
    # inside a transaction -- the documented order for a SQLite table rebuild.
    connection.execute("pragma foreign_keys=off")
    try:
        with connection:
            for table, _, schema, indexes in pending:
                names = ", ".join(name for name, _ in _columns(connection, table))
                connection.execute(f"alter table {table} rename to {table}__old")
                connection.execute(schema)
                connection.execute(f"insert into {table} ({names}) select {names} from {table}__old")
                connection.execute(f"drop table {table}__old")
                for index in indexes:
                    connection.execute(index)
    finally:
        connection.execute("pragma foreign_keys=on")

    problems = 0
    for table, column, _, _ in pending:
        after = _fingerprint(connection, table)
        if after != before[table]:
            print(f"  !! {table}: row contents changed", file=sys.stderr)
            problems += 1
        if _is_mandatory(connection, table, column):
            print(f"  !! {table}.{column} is still mandatory", file=sys.stderr)
            problems += 1
        print(f"  {table:32} {len(after)} rows, byte-identical: {after == before[table]}")

    integrity = connection.execute("pragma integrity_check").fetchone()[0]
    print(f"integrity_check: {integrity}")
    connection.close()
    return 1 if problems or integrity != "ok" else 0


if __name__ == "__main__":
    sys.exit(main())

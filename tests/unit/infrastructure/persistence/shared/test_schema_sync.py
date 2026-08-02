"""Tests for the Sprint 1, Commit 7 (Revised) schema-compatibility helper.

Reproduces the exact class of failure Commit 6's Dashboard validation
hit: a table that already exists on disk, created before a column was
added to its model, so `metadata.create_all`'s own `checkfirst` silently
leaves it stale. Each test uses a real file-backed SQLite engine (not an
in-memory StaticPool one) — the earlier concurrency work (Commit 2) found
StaticPool masks behavior a real file-backed engine exposes.

An earlier version of `sync_table_schema` fabricated a placeholder value
(`''`/`0`) for a missing NOT NULL column so the ALTER would succeed. That
was rejected — a fabricated `case_id=''` is a structurally valid but
semantically meaningless row. This suite tests the replacement behavior:
nullable gaps are repaired (NULL, not a fabricated value); NOT NULL gaps
raise `IncompatibleSchemaError` and change nothing.
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from atlas.core.infrastructure.persistence.shared.schema_sync import (
    IncompatibleSchemaError,
    _table_locks,
    sync_table_schema,
)

THREAD_COUNT = 20


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "atlas.db"


@pytest.fixture
def engine(db_path):
    return create_engine(f"sqlite:///{db_path}", future=True)


def _current_columns(engine, table_name: str) -> dict[str, dict]:
    with engine.begin() as connection:
        rows = connection.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1]: {"type": row[2], "notnull": bool(row[3])} for row in rows}


class TestFreshDatabase:
    def test_creates_the_table_with_every_declared_column(self, engine):
        metadata = MetaData()
        table = Table(
            "widgets",
            metadata,
            Column("id", String, primary_key=True),
            Column("case_id", String, nullable=False),
            Column("count", Integer, nullable=False),
        )

        sync_table_schema(engine, table)

        assert set(_current_columns(engine, "widgets")) == {"id", "case_id", "count"}


class TestUpToDateExistingDatabase:
    def test_is_a_no_op_and_does_not_raise(self, engine):
        metadata = MetaData()
        table = Table(
            "widgets",
            metadata,
            Column("id", String, primary_key=True),
            Column("count", Integer, nullable=False),
        )
        sync_table_schema(engine, table)

        sync_table_schema(engine, table)  # second call against an already-correct table

        assert set(_current_columns(engine, "widgets")) == {"id", "count"}


class TestNullableSchemaGapIsRepaired:
    def test_adds_a_missing_nullable_column_leaving_old_rows_null(self, engine):
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE decisions (id VARCHAR NOT NULL, PRIMARY KEY (id))"
            )
            connection.exec_driver_sql("INSERT INTO decisions (id) VALUES ('d1')")

        metadata = MetaData()
        decisions_table = Table(
            "decisions",
            metadata,
            Column("id", String, primary_key=True),
            Column("note", String, nullable=True),
        )

        sync_table_schema(engine, decisions_table)

        assert _current_columns(engine, "decisions")["note"]["notnull"] is False
        with engine.begin() as connection:
            row = connection.exec_driver_sql(
                "SELECT note FROM decisions WHERE id = 'd1'"
            ).fetchone()
        assert row == (None,)  # honest "unknown", never a fabricated value


class TestRequiredSchemaGapFailsClearlyInsteadOfFabricating:
    def test_raises_and_names_the_missing_not_null_column(self, engine):
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE decisions (id VARCHAR NOT NULL, subject VARCHAR NOT NULL, "
                "PRIMARY KEY (id))"
            )

        metadata = MetaData()
        decisions_table = Table(
            "decisions",
            metadata,
            Column("id", String, primary_key=True),
            Column("subject", String, nullable=False),
            Column("case_id", String, nullable=False),
        )

        with pytest.raises(IncompatibleSchemaError, match="case_id"):
            sync_table_schema(engine, decisions_table)

    def test_does_not_alter_the_table_or_fabricate_a_value(self, engine):
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE decisions (id VARCHAR NOT NULL, PRIMARY KEY (id))"
            )
            connection.exec_driver_sql("INSERT INTO decisions (id) VALUES ('d1')")

        metadata = MetaData()
        decisions_table = Table(
            "decisions",
            metadata,
            Column("id", String, primary_key=True),
            Column("case_id", String, nullable=False),
        )

        with pytest.raises(IncompatibleSchemaError):
            sync_table_schema(engine, decisions_table)

        # the table is untouched: no case_id column, no fabricated value anywhere
        assert set(_current_columns(engine, "decisions")) == {"id"}

    def test_the_real_commit_6_case_fails_clearly_rather_than_fabricating(self, engine):
        """The exact shape Dashboard validation hit: `decisions` created
        before `case_id` existed on the model. The correct behavior is a
        clear failure, not a fabricated case_id."""
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE decisions (id VARCHAR NOT NULL, user_id VARCHAR NOT NULL, "
                "decision_type VARCHAR NOT NULL, subject VARCHAR NOT NULL, "
                "reason VARCHAR NOT NULL, confidence INTEGER NOT NULL, "
                "decided_at VARCHAR NOT NULL, recorded_at VARCHAR NOT NULL, "
                "source VARCHAR NOT NULL, PRIMARY KEY (id))"
            )

        from atlas.core.infrastructure.persistence.decision.table import decisions_table

        with pytest.raises(IncompatibleSchemaError, match="case_id"):
            sync_table_schema(engine, decisions_table)


class TestRepeatedStartup:
    def test_three_consecutive_calls_against_a_compatible_table_are_idempotent(self, engine):
        metadata = MetaData()
        table = Table(
            "widgets",
            metadata,
            Column("id", String, primary_key=True),
            Column("note", String, nullable=True),
        )

        for _ in range(3):
            sync_table_schema(engine, table)

        assert set(_current_columns(engine, "widgets")) == {"id", "note"}

    def test_repeated_calls_against_an_incompatible_table_keep_failing_the_same_way(self, engine):
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE widgets (id VARCHAR NOT NULL, PRIMARY KEY (id))"
            )

        metadata = MetaData()
        table = Table(
            "widgets",
            metadata,
            Column("id", String, primary_key=True),
            Column("case_id", String, nullable=False),
        )

        for _ in range(3):
            with pytest.raises(IncompatibleSchemaError):
                sync_table_schema(engine, table)

        assert set(_current_columns(engine, "widgets")) == {"id"}


class TestConcurrentTableInitialization:
    """Sprint 1, Commit 11 — the shared mechanism's own concurrency
    coverage, independent of any one persistence module. Commit 2 found
    and fixed this race for Case alone; Commit 10 reproduced it for
    Observation, which had no lock of its own. This tests the fix at its
    actual source: `sync_table_schema` itself, so every one of the
    eighteen modules that calls it is covered by construction, not by
    having its own, easily-forgotten copy of this test.
    """

    def test_concurrent_first_calls_for_a_brand_new_table_do_not_raise(self, engine):
        metadata = MetaData()
        table = Table(
            "widgets",
            metadata,
            Column("id", String, primary_key=True),
            Column("case_id", String, nullable=False),
        )
        errors: list[Exception] = []
        barrier = threading.Barrier(THREAD_COUNT)

        def init():
            barrier.wait()
            try:
                sync_table_schema(engine, table)
            except Exception as exc:  # noqa: BLE001 - capturing for assertion below
                errors.append(exc)

        threads = [threading.Thread(target=init) for _ in range(THREAD_COUNT)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert errors == []
        assert set(_current_columns(engine, "widgets")) == {"id", "case_id"}

    def test_locks_are_scoped_per_table_not_global(self):
        # Two different tables must never contend on the same lock — an
        # unrelated table's first-request initialization should never be
        # blocked by this one's.
        assert _table_locks["table_a"] is not _table_locks["table_b"]
        assert _table_locks["table_a"] is _table_locks["table_a"]

"""Reproduces the Case table initialization race from Platform Bootstrap.

`create_case_table` runs on every request via the API's `get_case_repository`
dependency (not once at startup), so concurrent requests can call it at the
same time. `MetaData.create_all(..., checkfirst=True)` is not atomic across
threads: two threads can both see "table does not exist" before either has
issued `CREATE TABLE`, so the second `CREATE TABLE` fails.
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy import create_engine

from atlas.core.domain.case.entity import Case
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
    SqlAlchemyCaseRepository,
)
from atlas.core.infrastructure.persistence.case.table import create_case_table

THREAD_COUNT = 20


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "atlas.db"


def _shared_engine(db_path):
    # Deliberately mirrors get_decision_engine()'s construction (a real
    # file-backed engine, default QueuePool) rather than an in-memory
    # StaticPool engine: StaticPool hands every thread the same single
    # connection and serializes access to it, which masks this race.
    return create_engine(f"sqlite:///{db_path}", future=True)


class TestConcurrentInitialization:
    def test_concurrent_calls_do_not_raise(self, db_path):
        engine = _shared_engine(db_path)
        errors: list[Exception] = []
        barrier = threading.Barrier(THREAD_COUNT)

        def init():
            barrier.wait()
            try:
                create_case_table(engine)
            except Exception as exc:  # noqa: BLE001 - capturing for assertion below
                errors.append(exc)

        threads = [threading.Thread(target=init) for _ in range(THREAD_COUNT)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert errors == []

    def test_repository_usable_after_concurrent_initialization(self, db_path):
        engine = _shared_engine(db_path)
        barrier = threading.Barrier(THREAD_COUNT)

        def init():
            barrier.wait()
            create_case_table(engine)

        threads = [threading.Thread(target=init) for _ in range(THREAD_COUNT)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        repository = SqlAlchemyCaseRepository(engine)
        case = Case.create()
        repository.add(case)
        assert repository.get(case.id) == case

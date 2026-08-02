"""Reproduces the Observation table initialization race from Commit 10.

`create_observation_table` runs on every request via the API's
`get_observation_repository` dependency (not once at startup), so
concurrent requests can call it at the same time. `MetaData.create_all(
..., checkfirst=True)` is not atomic across threads: two threads can both
see "table does not exist" before either has issued `CREATE TABLE`, so
the second `CREATE TABLE` fails — exactly what Commit 10's Observation
Capture Flow hit on its very first `GET /observations` after a fresh
backend start. Unlike Case (fixed locally in Commit 2), Observation had
no lock of its own; Commit 11 fixes this for both, and every other
persistence module, in one shared place
(atlas/core/infrastructure/persistence/shared/schema_sync.py).

Mirrors tests/unit/infrastructure/persistence/case/test_table_concurrency.py
exactly, module-for-module.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement, Subject
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table

THREAD_COUNT = 20


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "atlas.db"


def _shared_engine(db_path):
    # Real file-backed engine (default QueuePool), matching production's
    # get_decision_engine() — not an in-memory StaticPool one, which
    # serializes on its single shared connection and masks this race
    # (see the Case concurrency test's own identical note).
    return create_engine(f"sqlite:///{db_path}", future=True)


class TestConcurrentInitialization:
    def test_concurrent_calls_do_not_raise(self, db_path):
        engine = _shared_engine(db_path)
        errors: list[Exception] = []
        barrier = threading.Barrier(THREAD_COUNT)

        def init():
            barrier.wait()
            try:
                create_observation_table(engine)
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
            create_observation_table(engine)

        threads = [threading.Thread(target=init) for _ in range(THREAD_COUNT)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        repository = SqlAlchemyObservationRepository(engine)
        observation = Observation.capture(
            case_id=CaseId(),
            subject=Subject("US 10-year Treasury yield"),
            statement=Statement("Yield rose above 4.5% for the first time this quarter."),
            observed_at=datetime(2026, 8, 2, 22, 0, 0, tzinfo=timezone.utc),
        )
        repository.add(observation)
        assert repository.get(observation.id) == observation

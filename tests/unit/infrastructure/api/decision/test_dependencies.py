"""Regression tests for the shared decision-engine connection pool
(Internal Alpha Stabilization 1, Fas 1 -- Backend 500).

Root cause (confirmed via the real uvicorn log and a request-scoped
SQLAlchemy pool `checkout` event listener attached to the real Engine
while loading Portfolio for real, against a real 31-holding
portfolio): `get_decision_engine()` was already correctly
`@lru_cache`'d (one shared Engine for the process, never one per
request) -- the crash was that Engine's own connection pool being
left at SQLAlchemy's unconfigured default (`pool_size=5`,
`max_overflow=10`, 15 total), which a single real Portfolio page load
already saturates completely (measured peak: 15/15 checked out, 0
spare capacity).

`get_decision_engine()` itself is never called directly here -- it
points at the real, on-disk `atlas.db`, and these are unit tests.
`TestDecisionEnginePoolConfiguration` inspects the real function's own
configured pool numbers (cheap, no connections opened). `TestPool
CheckoutMechanics` proves the actual checkout/timeout mechanics against
an isolated, file-backed SQLite engine built with the identical pool
parameters (SQLite's default `:memory:` engine uses `SingletonThreadPool`,
which doesn't accept `pool_size`/`max_overflow`/`pool_timeout` at all --
a file path is required to get the same `QueuePool` class production
uses, confirmed directly against a temp file), so the mechanism is
verified without ever touching the shared database file.
"""
from __future__ import annotations

import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import TimeoutError as SATimeoutError

from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

# The peak measured against a real, realistic (31-holding) Portfolio
# page load on the unconfigured default pool -- SQLAlchemy's own
# pool_size=5 + max_overflow=10 ceiling, exactly matched (0 headroom).
_MEASURED_PEAK_CONCURRENT_CHECKOUTS = 15


class TestDecisionEnginePoolConfiguration:
    def test_pool_gives_real_headroom_above_the_measured_real_world_peak(self):
        engine = get_decision_engine()
        pool = engine.pool
        total_capacity = pool.size() + pool._max_overflow
        assert total_capacity > _MEASURED_PEAK_CONCURRENT_CHECKOUTS

    def test_pool_size_and_overflow_are_the_chosen_values(self):
        """Pinned exactly, not just "> old default" -- a future change
        to these numbers should be a deliberate, visible decision."""
        pool = get_decision_engine().pool
        assert pool.size() == 10
        assert pool._max_overflow == 20

    def test_engine_is_still_the_one_shared_process_lifetime_instance(self):
        """The fix is pool sizing, not the caching -- `@lru_cache` must
        still mean exactly one Engine for the process, never a fresh
        one per call/request."""
        assert get_decision_engine() is get_decision_engine()


def _pooled_engine(tmp_path, *, pool_size: int, max_overflow: int, pool_timeout: float) -> Engine:
    """A real, file-backed (never `:memory:`) SQLite engine with the
    same pool shape as `get_decision_engine()`'s own configuration --
    `:memory:` uses `SingletonThreadPool`, which silently ignores
    concurrent-pool semantics entirely; a temp file gets the real
    `QueuePool` class production uses, isolated from the shared
    database."""
    db_path = tmp_path / "pool_mechanics_test.db"
    return create_engine(
        f"sqlite:///{db_path}",
        future=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
    )


class TestPoolCheckoutMechanics:
    """The pool must still protect against genuine over-demand -- this
    change is "size it to reality," never "remove the limit." A short
    `pool_timeout` (1s, vs. production's real 30s) keeps these tests
    fast without changing what they prove."""

    def test_can_check_out_up_to_the_full_configured_capacity_without_timing_out(self, tmp_path):
        engine = _pooled_engine(tmp_path, pool_size=10, max_overflow=20, pool_timeout=1)
        connections = [engine.connect() for _ in range(30)]  # pool_size + max_overflow
        try:
            assert engine.pool.checkedout() == 30
        finally:
            for connection in connections:
                connection.close()

    def test_exceeding_full_capacity_still_raises_a_real_timeout(self, tmp_path):
        engine = _pooled_engine(tmp_path, pool_size=10, max_overflow=20, pool_timeout=1)
        connections = [engine.connect() for _ in range(30)]
        try:
            start = time.monotonic()
            with pytest.raises(SATimeoutError):
                engine.connect()
            # Fails fast on the configured pool_timeout, never hangs.
            assert time.monotonic() - start < 5
        finally:
            for connection in connections:
                connection.close()

    def test_connections_are_returned_to_the_pool_after_use(self, tmp_path):
        engine = _pooled_engine(tmp_path, pool_size=10, max_overflow=20, pool_timeout=1)
        with engine.connect():
            assert engine.pool.checkedout() == 1
        assert engine.pool.checkedout() == 0

    def test_the_old_unconfigured_default_capacity_is_exactly_what_a_real_portfolio_load_already_saturates(
        self, tmp_path
    ):
        """Documents the regression itself: 15 concurrent connections
        -- the exact measured real-world peak -- already exhausted
        SQLAlchemy's own unconfigured default (pool_size=5,
        max_overflow=10). This is why the fix is a real pool-size
        increase, not a false alarm."""
        old_default_engine = _pooled_engine(tmp_path, pool_size=5, max_overflow=10, pool_timeout=1)
        connections = [old_default_engine.connect() for _ in range(_MEASURED_PEAK_CONCURRENT_CHECKOUTS)]
        try:
            with pytest.raises(SATimeoutError):
                old_default_engine.connect()
        finally:
            for connection in connections:
                connection.close()

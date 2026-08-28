"""Tests for `EnrichmentProgressStore`."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.enrichment_tracking.models import EnrichmentProgressStatus
from atlas.alpha.enrichment_tracking.store import EnrichmentProgressStore
from atlas.alpha.enrichment_tracking.table import create_enrichment_progress_table


@pytest.fixture
def engine() -> Engine:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_enrichment_progress_table(engine)
    return engine


@pytest.fixture
def store(engine) -> EnrichmentProgressStore:
    return EnrichmentProgressStore(engine)


class TestStartBatch:
    def test_get_batch_returns_none_for_an_unknown_batch(self, store):
        assert store.get_batch("nope") is None

    def test_start_batch_seeds_every_ticker_as_pending_in_order(self, store):
        store.start_batch("b1", (("AAPL", "Apple Inc."), ("MSFT", "Microsoft Corp")))
        batch = store.get_batch("b1")
        assert [e.ticker for e in batch.entries] == ["AAPL", "MSFT"]
        assert all(e.status == EnrichmentProgressStatus.PENDING for e in batch.entries)
        assert batch.total == 2
        assert batch.done_count == 0
        assert batch.complete is False

    def test_starting_the_same_batch_id_again_replaces_it(self, store):
        store.start_batch("b1", (("AAPL", "Apple Inc."),))
        store.start_batch("b1", (("MSFT", "Microsoft Corp"),))
        batch = store.get_batch("b1")
        assert [e.ticker for e in batch.entries] == ["MSFT"]


class TestStatusTransitions:
    def test_mark_analyzing_then_done(self, store):
        store.start_batch("b1", (("AAPL", "Apple Inc."),))
        store.mark_analyzing("b1", "AAPL")
        batch = store.get_batch("b1")
        assert batch.entries[0].status == EnrichmentProgressStatus.ANALYZING
        assert batch.currently_analyzing == "Apple Inc."

        store.mark_done("b1", "AAPL")
        batch = store.get_batch("b1")
        assert batch.entries[0].status == EnrichmentProgressStatus.DONE
        assert batch.done_count == 1
        assert batch.complete is True
        assert batch.currently_analyzing is None

    def test_mark_deferred(self, store):
        store.start_batch("b1", (("AAPL", "Apple Inc."),))
        store.mark_deferred("b1", "AAPL")
        batch = store.get_batch("b1")
        assert batch.entries[0].status == EnrichmentProgressStatus.DEFERRED
        # Deferred counts toward "complete" -- it's a resolved terminal
        # state (quota exhausted), not still-pending work.
        assert batch.complete is True
        assert batch.done_count == 0

    def test_two_batches_never_interfere(self, store):
        store.start_batch("b1", (("AAPL", "Apple Inc."),))
        store.start_batch("b2", (("AAPL", "Apple Inc."),))
        store.mark_done("b1", "AAPL")
        assert store.get_batch("b1").entries[0].status == EnrichmentProgressStatus.DONE
        assert store.get_batch("b2").entries[0].status == EnrichmentProgressStatus.PENDING

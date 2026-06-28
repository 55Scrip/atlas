from dataclasses import FrozenInstanceError

import pytest

from atlas.memory import (
    DailyBriefSnapshot,
    InMemoryMemoryStore,
    PortfolioSnapshot,
    Timeline,
    WatchlistSnapshot,
)


def _portfolio_snapshot(
    timestamp: str = "2026-06-28T09:00:00+00:00",
    payload: dict | None = None,
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        timestamp=timestamp,
        source_version="test-v1",
        metadata={"source": "unit-test", "tags": ["portfolio", "baseline"]},
        payload=payload or {"positions": {"MSFT": 0.20, "NVDA": 0.15}, "risk": "balanced"},
    )


def test_snapshots_are_frozen_and_deeply_immutable():
    snapshot = _portfolio_snapshot()

    with pytest.raises(FrozenInstanceError):
        snapshot.timestamp = "changed"
    with pytest.raises(TypeError):
        snapshot.metadata["source"] = "changed"
    with pytest.raises(TypeError):
        snapshot.payload["risk"] = "changed"

    assert snapshot.metadata["tags"] == ("portfolio", "baseline")


def test_snapshot_types_share_required_fields():
    portfolio = _portfolio_snapshot()
    watchlist = WatchlistSnapshot(
        timestamp="2026-06-28T10:00:00+00:00",
        source_version="test-v1",
        metadata={"source": "unit-test"},
        payload={"tickers": ["MSFT", "NVDA"]},
    )
    daily = DailyBriefSnapshot(
        timestamp="2026-06-28T11:00:00+00:00",
        source_version="test-v1",
        metadata={"source": "unit-test"},
        payload={"bottom_line": "No meaningful changes since your last review."},
    )

    for snapshot in (portfolio, watchlist, daily):
        assert snapshot.timestamp
        assert snapshot.source_version == "test-v1"
        assert snapshot.metadata["source"] == "unit-test"
        assert snapshot.payload


def test_in_memory_store_saves_loads_and_orders_snapshots():
    early = _portfolio_snapshot("2026-06-28T08:00:00+00:00")
    late = _portfolio_snapshot("2026-06-28T09:00:00+00:00")
    store = InMemoryMemoryStore[PortfolioSnapshot]()

    assert store.latest() is None
    assert not store.exists(early.timestamp)

    store.save(late)
    store.save(early)

    assert store.exists(early.timestamp)
    assert store.get(early.timestamp) == early
    assert store.latest() == late
    assert store.list() == (early, late)


def test_store_replaces_snapshot_with_same_timestamp():
    original = _portfolio_snapshot(payload={"risk": "balanced"})
    replacement = _portfolio_snapshot(payload={"risk": "lower"})
    store = InMemoryMemoryStore((original,))

    store.save(replacement)

    assert store.list() == (replacement,)
    assert store.latest() == replacement


def test_timeline_compares_added_removed_and_modified_items():
    previous = _portfolio_snapshot(
        "2026-06-28T08:00:00+00:00",
        payload={"positions": {"MSFT": 0.20}, "risk": "balanced", "cash": 0.10},
    )
    current = _portfolio_snapshot(
        "2026-06-28T09:00:00+00:00",
        payload={"positions": {"MSFT": 0.25}, "risk": "balanced", "quality": "high"},
    )
    timeline = Timeline(InMemoryMemoryStore((previous, current)))

    comparison = timeline.compare(previous, current)

    assert comparison.previous_timestamp == previous.timestamp
    assert comparison.current_timestamp == current.timestamp
    assert comparison.added_items == ("quality",)
    assert comparison.removed_items == ("cash",)
    assert comparison.modified_items == ("positions",)
    assert comparison.has_changes


def test_timeline_changes_since_last_snapshot_uses_latest_two_snapshots():
    first = _portfolio_snapshot("2026-06-28T08:00:00+00:00", {"risk": "balanced"})
    second = _portfolio_snapshot("2026-06-28T09:00:00+00:00", {"risk": "balanced"})
    third = _portfolio_snapshot("2026-06-28T10:00:00+00:00", {"risk": "higher"})
    timeline = Timeline(InMemoryMemoryStore((third, first, second)))

    comparison = timeline.changes_since_last_snapshot()

    assert comparison is not None
    assert comparison.previous_timestamp == second.timestamp
    assert comparison.current_timestamp == third.timestamp
    assert comparison.modified_items == ("risk",)


def test_timeline_handles_empty_and_single_snapshot_edges():
    empty_timeline = Timeline(InMemoryMemoryStore[PortfolioSnapshot]())
    single_timeline = Timeline(InMemoryMemoryStore((_portfolio_snapshot(),)))

    assert empty_timeline.latest_snapshot() is None
    assert empty_timeline.snapshot_at("missing") is None
    assert empty_timeline.changes_since_last_snapshot() is None
    assert single_timeline.latest_snapshot() == _portfolio_snapshot()
    assert single_timeline.changes_since_last_snapshot() is None


def test_timeline_comparison_is_deterministic():
    previous = _portfolio_snapshot(payload={"z": 1, "a": 1, "m": 1})
    current = _portfolio_snapshot(payload={"b": 2, "a": 2, "m": 1})
    timeline = Timeline(InMemoryMemoryStore[PortfolioSnapshot]())

    first = timeline.compare(previous, current)
    second = timeline.compare(previous, current)

    assert first == second
    assert first.added_items == ("b",)
    assert first.removed_items == ("z",)
    assert first.modified_items == ("a",)

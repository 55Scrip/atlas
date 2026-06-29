from atlas.history import ChangeSeverity, ChangeType, HistoricalChangeEngine
from atlas.memory import InMemoryMemoryStore, PortfolioSnapshot, WatchlistSnapshot


def _portfolio_snapshot(timestamp: str, positions: dict) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        timestamp=timestamp,
        source_version="test-v1",
        metadata={"source": "unit-test"},
        payload={"positions": positions},
    )


def _watchlist_snapshot(timestamp: str, tickers: list[str]) -> WatchlistSnapshot:
    return WatchlistSnapshot(
        timestamp=timestamp,
        source_version="test-v1",
        metadata={"source": "unit-test"},
        payload={"tickers": tickers},
    )


def _change_types(comparison) -> tuple[ChangeType, ...]:
    return tuple(change.change_type for change in comparison.changes)


def test_detects_added_portfolio_position():
    previous = _portfolio_snapshot("2026-06-28T09:00:00+00:00", {"MSFT": {"weight": 0.20}})
    current = _portfolio_snapshot(
        "2026-06-28T10:00:00+00:00",
        {"MSFT": {"weight": 0.20}, "NVDA": {"weight": 0.10}},
    )

    comparison = HistoricalChangeEngine().compare(previous, current)

    assert _change_types(comparison) == (ChangeType.PORTFOLIO_POSITION_ADDED,)
    assert comparison.changes[0].subject == "NVDA"
    assert comparison.changes[0].severity == ChangeSeverity.MODERATE


def test_detects_removed_portfolio_position():
    previous = _portfolio_snapshot(
        "2026-06-28T09:00:00+00:00",
        {"MSFT": {"weight": 0.20}, "NVDA": {"weight": 0.10}},
    )
    current = _portfolio_snapshot("2026-06-28T10:00:00+00:00", {"MSFT": {"weight": 0.20}})

    comparison = HistoricalChangeEngine().compare(previous, current)

    assert _change_types(comparison) == (ChangeType.PORTFOLIO_POSITION_REMOVED,)
    assert comparison.changes[0].subject == "NVDA"
    assert comparison.changes[0].current_value is None


def test_detects_modified_weight():
    previous = _portfolio_snapshot("2026-06-28T09:00:00+00:00", {"MSFT": {"weight": 0.20}})
    current = _portfolio_snapshot("2026-06-28T10:00:00+00:00", {"MSFT": {"weight": 0.26}})

    comparison = HistoricalChangeEngine().compare(previous, current)

    assert _change_types(comparison) == (ChangeType.PORTFOLIO_WEIGHT_CHANGED,)
    assert comparison.changes[0].previous_value == 0.20
    assert comparison.changes[0].current_value == 0.26


def test_detects_watchlist_additions_and_removals():
    previous = _watchlist_snapshot("2026-06-28T09:00:00+00:00", ["MSFT", "NVDA"])
    current = _watchlist_snapshot("2026-06-28T10:00:00+00:00", ["MSFT", "TSM"])

    comparison = HistoricalChangeEngine().compare(previous, current)

    assert _change_types(comparison) == (
        ChangeType.WATCHLIST_ITEM_REMOVED,
        ChangeType.WATCHLIST_ITEM_ADDED,
    )
    assert tuple(change.subject for change in comparison.changes) == ("NVDA", "TSM")


def test_detects_significant_quality_and_risk_score_changes():
    previous = _portfolio_snapshot(
        "2026-06-28T09:00:00+00:00",
        {"MSFT": {"weight": 0.20, "quality_score": 80, "risk_score": 35}},
    )
    current = _portfolio_snapshot(
        "2026-06-28T10:00:00+00:00",
        {"MSFT": {"weight": 0.20, "quality_score": 87, "risk_score": 45}},
    )

    comparison = HistoricalChangeEngine().compare(previous, current)

    assert _change_types(comparison) == (
        ChangeType.QUALITY_SCORE_CHANGED,
        ChangeType.RISK_SCORE_CHANGED,
    )
    assert comparison.changes[0].previous_value == 80.0
    assert comparison.changes[0].current_value == 87.0
    assert comparison.changes[1].severity == ChangeSeverity.HIGH


def test_ignores_insignificant_score_and_weight_changes():
    previous = _portfolio_snapshot(
        "2026-06-28T09:00:00+00:00",
        {"MSFT": {"weight": 0.2000, "quality_score": 80, "risk_score": 35}},
    )
    current = _portfolio_snapshot(
        "2026-06-28T10:00:00+00:00",
        {"MSFT": {"weight": 0.2005, "quality_score": 84, "risk_score": 39}},
    )

    comparison = HistoricalChangeEngine().compare(previous, current)

    assert not comparison.has_changes
    assert comparison.changes == ()


def test_detects_multiple_simultaneous_changes_in_deterministic_order():
    previous = _portfolio_snapshot(
        "2026-06-28T09:00:00+00:00",
        {
            "MSFT": {"weight": 0.20, "quality_score": 80, "risk_score": 35},
            "NVDA": {"weight": 0.10},
        },
    )
    current = _portfolio_snapshot(
        "2026-06-28T10:00:00+00:00",
        {
            "MSFT": {"weight": 0.30, "quality_score": 88, "risk_score": 35},
            "TSM": {"weight": 0.12},
        },
    )

    comparison = HistoricalChangeEngine().compare(previous, current)

    assert tuple((change.subject, change.change_type) for change in comparison.changes) == (
        ("MSFT", ChangeType.PORTFOLIO_WEIGHT_CHANGED),
        ("MSFT", ChangeType.QUALITY_SCORE_CHANGED),
        ("NVDA", ChangeType.PORTFOLIO_POSITION_REMOVED),
        ("TSM", ChangeType.PORTFOLIO_POSITION_ADDED),
    )


def test_compare_latest_uses_previous_and_current_snapshots():
    first = _portfolio_snapshot("2026-06-28T08:00:00+00:00", {"MSFT": {"weight": 0.20}})
    second = _portfolio_snapshot("2026-06-28T09:00:00+00:00", {"MSFT": {"weight": 0.20}})
    third = _portfolio_snapshot("2026-06-28T10:00:00+00:00", {"MSFT": {"weight": 0.25}})
    store = InMemoryMemoryStore((third, first, second))

    comparison = HistoricalChangeEngine(store).compare_latest()

    assert comparison is not None
    assert comparison.previous_timestamp == second.timestamp
    assert comparison.current_timestamp == third.timestamp
    assert _change_types(comparison) == (ChangeType.PORTFOLIO_WEIGHT_CHANGED,)


def test_compare_latest_returns_none_for_insufficient_history():
    store = InMemoryMemoryStore((_portfolio_snapshot("2026-06-28T09:00:00+00:00", {}),))

    assert HistoricalChangeEngine(store).compare_latest() is None


def test_compare_latest_requires_store():
    try:
        HistoricalChangeEngine().compare_latest()
    except ValueError as exc:
        assert "MemoryStore" in str(exc)
    else:
        raise AssertionError("Expected compare_latest to require a MemoryStore.")

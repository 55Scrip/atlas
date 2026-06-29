from typing import Mapping

from atlas.history.models import (
    ChangeSeverity,
    ChangeType,
    HistoricalChange,
    HistoricalComparison,
)
from atlas.memory import MemoryStore, Snapshot

QUALITY_CHANGE_THRESHOLD = 5.0
RISK_CHANGE_THRESHOLD = 5.0
WEIGHT_CHANGE_THRESHOLD = 0.001


class HistoricalChangeEngine:
    """Detect deterministic structural changes between historical snapshots."""

    def __init__(self, store: MemoryStore[Snapshot] | None = None) -> None:
        self.store = store

    def compare_latest(self) -> HistoricalComparison | None:
        """Compare the two latest snapshots from the configured store."""

        if self.store is None:
            raise ValueError("A MemoryStore is required to compare latest snapshots.")
        snapshots = self.store.list()
        if len(snapshots) < 2:
            return None
        return self.compare(snapshots[-2], snapshots[-1])

    def compare(self, previous: Snapshot, current: Snapshot) -> HistoricalComparison:
        """Compare two snapshots and return structured historical changes."""

        changes = (
            *_portfolio_position_changes(previous, current),
            *_watchlist_changes(previous, current),
        )
        return HistoricalComparison(
            previous_timestamp=previous.timestamp,
            current_timestamp=current.timestamp,
            changes=tuple(sorted(changes, key=_change_sort_key)),
        )


def _portfolio_position_changes(
    previous: Snapshot,
    current: Snapshot,
) -> tuple[HistoricalChange, ...]:
    previous_positions = _positions(previous.payload)
    current_positions = _positions(current.payload)
    previous_tickers = set(previous_positions)
    current_tickers = set(current_positions)
    changes: list[HistoricalChange] = []
    for ticker in sorted(current_tickers - previous_tickers):
        changes.append(
            HistoricalChange(
                change_type=ChangeType.PORTFOLIO_POSITION_ADDED,
                subject=ticker,
                previous_value=None,
                current_value=current_positions[ticker],
                severity=ChangeSeverity.MODERATE,
            )
        )
    for ticker in sorted(previous_tickers - current_tickers):
        changes.append(
            HistoricalChange(
                change_type=ChangeType.PORTFOLIO_POSITION_REMOVED,
                subject=ticker,
                previous_value=previous_positions[ticker],
                current_value=None,
                severity=ChangeSeverity.MODERATE,
            )
        )
    for ticker in sorted(previous_tickers & current_tickers):
        changes.extend(_position_metric_changes(ticker, previous_positions[ticker], current_positions[ticker]))
    return tuple(changes)


def _position_metric_changes(
    ticker: str,
    previous_position: Mapping[str, object],
    current_position: Mapping[str, object],
) -> tuple[HistoricalChange, ...]:
    changes: list[HistoricalChange] = []
    previous_weight = _number(previous_position.get("weight"))
    current_weight = _number(current_position.get("weight"))
    if _changed(previous_weight, current_weight, WEIGHT_CHANGE_THRESHOLD):
        changes.append(
            HistoricalChange(
                change_type=ChangeType.PORTFOLIO_WEIGHT_CHANGED,
                subject=ticker,
                previous_value=previous_weight,
                current_value=current_weight,
                severity=_score_delta_severity(previous_weight, current_weight, 0.05, 0.10),
            )
        )
    changes.extend(
        _score_change(
            ticker,
            ChangeType.QUALITY_SCORE_CHANGED,
            previous_position.get("quality_score"),
            current_position.get("quality_score"),
            QUALITY_CHANGE_THRESHOLD,
        )
    )
    changes.extend(
        _score_change(
            ticker,
            ChangeType.RISK_SCORE_CHANGED,
            previous_position.get("risk_score"),
            current_position.get("risk_score"),
            RISK_CHANGE_THRESHOLD,
        )
    )
    return tuple(changes)


def _watchlist_changes(previous: Snapshot, current: Snapshot) -> tuple[HistoricalChange, ...]:
    previous_items = _watchlist_items(previous.payload)
    current_items = _watchlist_items(current.payload)
    changes = [
        HistoricalChange(
            change_type=ChangeType.WATCHLIST_ITEM_ADDED,
            subject=item,
            previous_value=None,
            current_value=item,
            severity=ChangeSeverity.LOW,
        )
        for item in sorted(current_items - previous_items)
    ]
    changes.extend(
        HistoricalChange(
            change_type=ChangeType.WATCHLIST_ITEM_REMOVED,
            subject=item,
            previous_value=item,
            current_value=None,
            severity=ChangeSeverity.LOW,
        )
        for item in sorted(previous_items - current_items)
    )
    return tuple(changes)


def _positions(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    raw_positions = payload.get("positions")
    if not isinstance(raw_positions, Mapping):
        return {}
    positions: dict[str, Mapping[str, object]] = {}
    for raw_ticker, raw_position in raw_positions.items():
        ticker = str(raw_ticker).upper()
        if isinstance(raw_position, Mapping):
            positions[ticker] = raw_position
        else:
            positions[ticker] = {"weight": raw_position}
    return positions


def _watchlist_items(payload: Mapping[str, object]) -> set[str]:
    raw_tickers = payload.get("tickers")
    if isinstance(raw_tickers, (tuple, frozenset, list, set)):
        return {str(ticker).upper() for ticker in raw_tickers}
    raw_items = payload.get("items")
    if isinstance(raw_items, (tuple, frozenset, list, set)):
        return {str(item).upper() for item in raw_items}
    return set()


def _score_change(
    ticker: str,
    change_type: ChangeType,
    previous_raw: object,
    current_raw: object,
    threshold: float,
) -> tuple[HistoricalChange, ...]:
    previous_value = _number(previous_raw)
    current_value = _number(current_raw)
    if not _changed(previous_value, current_value, threshold):
        return ()
    return (
        HistoricalChange(
            change_type=change_type,
            subject=ticker,
            previous_value=previous_value,
            current_value=current_value,
            severity=_score_delta_severity(previous_value, current_value, threshold, threshold * 2),
        ),
    )


def _changed(previous_value: float | None, current_value: float | None, threshold: float) -> bool:
    if previous_value is None or current_value is None:
        return previous_value != current_value
    return abs(current_value - previous_value) >= threshold


def _score_delta_severity(
    previous_value: float | None,
    current_value: float | None,
    moderate_threshold: float,
    high_threshold: float,
) -> ChangeSeverity:
    if previous_value is None or current_value is None:
        return ChangeSeverity.LOW
    delta = abs(current_value - previous_value)
    if delta >= high_threshold:
        return ChangeSeverity.HIGH
    if delta >= moderate_threshold:
        return ChangeSeverity.MODERATE
    return ChangeSeverity.LOW


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _change_sort_key(change: HistoricalChange) -> tuple[str, str]:
    return (change.subject, change.change_type.value)

from dataclasses import dataclass

from atlas.memory.memory_store import MemoryStore, SnapshotT
from atlas.memory.snapshot import SnapshotValue


@dataclass(frozen=True)
class TimelineComparison:
    """Deterministic diff between two snapshots."""

    previous_timestamp: str
    current_timestamp: str
    added_items: tuple[str, ...]
    removed_items: tuple[str, ...]
    modified_items: tuple[str, ...]

    @property
    def has_changes(self) -> bool:
        """Return whether any added, removed, or modified items were detected."""

        return bool(self.added_items or self.removed_items or self.modified_items)


class Timeline:
    """Timeline view over a MemoryStore that compares historical snapshots."""

    def __init__(self, store: MemoryStore[SnapshotT]) -> None:
        self.store = store

    def latest_snapshot(self) -> SnapshotT | None:
        """Return the latest snapshot from the underlying store."""

        return self.store.latest()

    def snapshot_at(self, timestamp: str) -> SnapshotT | None:
        """Return the snapshot for the timestamp, if present."""

        return self.store.get(timestamp)

    def changes_since_last_snapshot(self) -> TimelineComparison | None:
        """Compare the two most recent snapshots, or return None if unavailable."""

        snapshots = self.store.list()
        if len(snapshots) < 2:
            return None
        return self.compare(snapshots[-2], snapshots[-1])

    def compare(self, snapshot_a: SnapshotT, snapshot_b: SnapshotT) -> TimelineComparison:
        """Compare two snapshots by their payload keys and values."""

        previous = dict(snapshot_a.payload)
        current = dict(snapshot_b.payload)
        previous_keys = set(previous)
        current_keys = set(current)
        added = tuple(sorted(current_keys - previous_keys))
        removed = tuple(sorted(previous_keys - current_keys))
        modified = tuple(
            key
            for key in sorted(previous_keys & current_keys)
            if _normalize(previous[key]) != _normalize(current[key])
        )
        return TimelineComparison(
            previous_timestamp=snapshot_a.timestamp,
            current_timestamp=snapshot_b.timestamp,
            added_items=added,
            removed_items=removed,
            modified_items=modified,
        )


def _normalize(value: SnapshotValue) -> object:
    if hasattr(value, "items"):
        return tuple(
            (key, _normalize(item))
            for key, item in sorted(value.items())
        )
    if isinstance(value, tuple):
        return tuple(_normalize(item) for item in value)
    if isinstance(value, frozenset):
        return tuple(sorted((_normalize(item) for item in value), key=repr))
    return value

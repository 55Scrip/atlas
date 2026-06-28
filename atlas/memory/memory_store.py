from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from atlas.memory.snapshot import Snapshot

SnapshotT = TypeVar("SnapshotT", bound=Snapshot)


class MemoryStore(ABC, Generic[SnapshotT]):
    """Storage abstraction for immutable Atlas snapshots."""

    @abstractmethod
    def save(self, snapshot: SnapshotT) -> SnapshotT:
        """Store a snapshot and return the stored snapshot."""

    @abstractmethod
    def latest(self) -> SnapshotT | None:
        """Return the most recent snapshot, or None when the store is empty."""

    @abstractmethod
    def get(self, timestamp: str) -> SnapshotT | None:
        """Return the snapshot for a timestamp, or None when it does not exist."""

    @abstractmethod
    def list(self) -> tuple[SnapshotT, ...]:
        """Return all snapshots in deterministic timestamp order."""

    @abstractmethod
    def exists(self, timestamp: str) -> bool:
        """Return whether a snapshot exists for the timestamp."""


class InMemoryMemoryStore(MemoryStore[SnapshotT]):
    """Deterministic in-memory snapshot store for tests and early orchestration."""

    def __init__(self, snapshots: tuple[SnapshotT, ...] = ()) -> None:
        self._snapshots: dict[str, SnapshotT] = {}
        for snapshot in snapshots:
            self.save(snapshot)

    def save(self, snapshot: SnapshotT) -> SnapshotT:
        self._snapshots[snapshot.timestamp] = snapshot
        return snapshot

    def latest(self) -> SnapshotT | None:
        snapshots = self.list()
        if not snapshots:
            return None
        return snapshots[-1]

    def get(self, timestamp: str) -> SnapshotT | None:
        return self._snapshots.get(timestamp)

    def list(self) -> tuple[SnapshotT, ...]:
        return tuple(self._snapshots[timestamp] for timestamp in sorted(self._snapshots))

    def exists(self, timestamp: str) -> bool:
        return timestamp in self._snapshots

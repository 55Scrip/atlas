from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

SnapshotValue = (
    str
    | int
    | float
    | bool
    | None
    | tuple["SnapshotValue", ...]
    | frozenset["SnapshotValue"]
    | Mapping[str, "SnapshotValue"]
)


@dataclass(frozen=True)
class Snapshot:
    """Immutable historical record used by Atlas memory and timeline systems."""

    timestamp: str
    source_version: str
    metadata: Mapping[str, SnapshotValue] = field(default_factory=dict)
    payload: Mapping[str, SnapshotValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        object.__setattr__(self, "payload", _freeze_mapping(self.payload))


@dataclass(frozen=True)
class PortfolioSnapshot(Snapshot):
    """Historical snapshot of portfolio context."""


@dataclass(frozen=True)
class WatchlistSnapshot(Snapshot):
    """Historical snapshot of watchlist context."""


@dataclass(frozen=True)
class DailyBriefSnapshot(Snapshot):
    """Historical snapshot of a generated Daily Brief."""


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, SnapshotValue]:
    return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: Any) -> SnapshotValue:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, frozenset):
        return frozenset(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    return value

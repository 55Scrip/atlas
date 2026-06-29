from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

EntityValue = (
    str
    | int
    | float
    | bool
    | None
    | tuple["EntityValue", ...]
    | frozenset["EntityValue"]
    | Mapping[str, "EntityValue"]
)


@dataclass(frozen=True)
class Company:
    """Canonical company entity shared across Atlas domains."""

    id: str
    name: str
    ticker: str
    exchange: str = ""
    sector: str = ""
    industry: str = ""
    country: str = ""


@dataclass(frozen=True)
class Holding:
    """Canonical portfolio holding entity."""

    company_id: str
    ticker: str
    quantity: float = 0.0
    market_value: float = 0.0
    weight: float = 0.0


@dataclass(frozen=True)
class Portfolio:
    """Canonical portfolio entity."""

    id: str
    name: str
    holdings: tuple[Holding, ...] = ()
    owner_id: str = ""
    metadata: Mapping[str, EntityValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class Watchlist:
    """Canonical watchlist entity."""

    id: str
    name: str
    tickers: tuple[str, ...] = ()
    owner_id: str = ""
    metadata: Mapping[str, EntityValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class ResearchNote:
    """Canonical research note entity."""

    id: str
    title: str
    body: str
    created_at: str
    author_id: str = ""
    related_tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class JournalEntry:
    """Canonical decision journal entry entity."""

    id: str
    title: str
    asset_or_idea: str
    thesis: str
    created_at: str
    owner_id: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class User:
    """Canonical user entity."""

    id: str
    display_name: str
    email: str = ""
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class MarketEvent:
    """Canonical market event entity."""

    id: str
    title: str
    occurred_at: str
    source: str = ""
    affected_tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Decision:
    """Canonical investment decision context entity."""

    id: str
    title: str
    decision_type: str
    created_at: str
    owner_id: str = ""
    related_tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeNode:
    """Canonical knowledge graph node entity."""

    id: str
    label: str
    node_type: str
    related_ids: tuple[str, ...] = ()
    metadata: Mapping[str, EntityValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, EntityValue]:
    return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: Any) -> EntityValue:
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

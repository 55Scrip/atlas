from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from atlas.shared import KnowledgeNode


class KnowledgeNodeType(str, Enum):
    """Supported knowledge node types."""

    COMPANY = "Company"
    SECTOR = "Sector"
    INDUSTRY = "Industry"
    COUNTRY = "Country"
    TECHNOLOGY = "Technology"
    THEME = "Theme"
    CONCEPT = "Concept"


class KnowledgeRelationship(str, Enum):
    """Explicit knowledge relationships with no inference."""

    COMPANY_SECTOR = "Company -> Sector"
    COMPANY_INDUSTRY = "Company -> Industry"
    COMPANY_COUNTRY = "Company -> Country"
    COMPANY_COMPETITOR = "Company -> Competitor"
    COMPANY_SUPPLIER = "Company -> Supplier"
    COMPANY_CUSTOMER = "Company -> Customer"
    COMPANY_TECHNOLOGY = "Company -> Technology"
    COMPANY_THEME = "Company -> Theme"
    THEME_THEME = "Theme -> Theme"


@dataclass(frozen=True)
class KnowledgeSource:
    """Source attribution for a knowledge fact."""

    id: str
    name: str
    source_type: str
    url: str = ""


@dataclass(frozen=True)
class KnowledgeReference:
    """Reference that links knowledge to supporting evidence."""

    id: str
    source_id: str
    citation: str
    locator: str = ""


@dataclass(frozen=True)
class KnowledgeFact:
    """Attributed fact stored by the knowledge domain."""

    id: str
    subject_node_id: str
    statement: str
    source: KnowledgeSource
    timestamp: str
    confidence: int
    evidence_reference: KnowledgeReference
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0, min(100, self.confidence)))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class KnowledgeEdge:
    """Explicit relationship between two knowledge nodes."""

    id: str
    from_node_id: str
    to_node_id: str
    relationship: KnowledgeRelationship
    fact_id: str | None = None


@dataclass(frozen=True)
class KnowledgeCollection:
    """In-memory deterministic collection of knowledge nodes, edges, and facts."""

    nodes: tuple[KnowledgeNode, ...] = ()
    edges: tuple[KnowledgeEdge, ...] = ()
    facts: tuple[KnowledgeFact, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", _deduplicate_by_id(self.nodes))
        object.__setattr__(self, "edges", _deduplicate_by_id(self.edges))
        object.__setattr__(self, "facts", _deduplicate_by_id(self.facts))


def _deduplicate_by_id(items: tuple[Any, ...]) -> tuple[Any, ...]:
    by_id = {item.id: item for item in items}
    return tuple(by_id[key] for key in sorted(by_id))


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    if isinstance(value, frozenset):
        return frozenset(_freeze_value(item) for item in value)
    return value

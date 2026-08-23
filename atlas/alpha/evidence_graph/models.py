"""Evidence Graph domain model (Atlas Intelligence Sprint 10, Deliverable
2). Alpha-only -- no Core change.

Deliberately a single node/edge shape (`GraphNode`/`GraphEdge`), not the
brief's own longer example list (`EvidenceNode`/`EvidenceEdge`/
`Dependency`/`GraphNode`/`GraphEdge`) -- every kind of thing this graph
represents (Observation, Evidence, Decision, Outcome, CaseCondition,
Assumption, Finding) already has its own real, distinct identity via
`GraphNodeKind`; a second parallel node/edge type would duplicate that
distinction rather than add one. This mirrors `Finding`'s own precedent
(`atlas.analysis_engine.findings`): one shape, a closed `kind` enum, and
a structured `details` dict -- never free text.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

__all__ = [
    "GraphNodeKind",
    "DependencyKind",
    "GraphNode",
    "GraphEdge",
    "EvidenceGraph",
    "WeaknessKind",
    "WeakDependency",
    "EvidenceGraphComparisonSide",
    "EvidenceGraphComparison",
    "ImpactedChange",
]


class GraphNodeKind(str, Enum):
    """Every kind of thing the graph represents -- each maps to one real
    Core or Alpha object, never a synthetic/derived placeholder."""

    OBSERVATION = "observation"
    EVIDENCE = "evidence"
    DECISION = "decision"
    OUTCOME = "outcome"
    CASE_CONDITION = "case_condition"
    ASSUMPTION = "assumption"
    FINDING = "finding"


class DependencyKind(str, Enum):
    """A closed, deliberately small relationship vocabulary -- an edge
    is constructed only when a real field on a real object names
    another real object (Deliverable 3's "endast verkliga relationer").

    `MISSING`, `EXPLAINS`, and `BLOCKS` are reserved, not constructed
    anywhere in this sprint -- each named in the brief's own example
    list, but none has a real, already-existing field this codebase
    can build an honest edge from today:
    - `MISSING` -- an edge needs two real endpoints, and an absence (a
      Decision with no `observation_id`, a Finding with no supporting
      evidence) has only one. Surfacing that honestly is `WeaknessKind
      .NO_SUPPORT` (Deliverable 5)'s own job, a node-level fact rather
      than a fabricated edge.
    - `EXPLAINS` -- would need a node for `Stance`/`StanceReason` (the
      thing being explained); this graph deliberately stops at
      `FINDING` (see `engine.py`'s own docstring for why), so there is
      nothing on the other end yet.
    - `BLOCKS` -- nothing in this codebase's Core domain actually
      blocks another object from proceeding (a Decision is never
      gated on a CaseCondition being satisfied); there is no real
      blocking relationship to name today.

    This follows the same "reserve the name, never construct it
    without a real case" discipline `atlas.analysis_engine.provenance
    .SourceKind.EXTERNAL_DATA_SOURCE` already established in this
    codebase."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends_on"
    DERIVED_FROM = "derived_from"
    EXPLAINS = "explains"
    FEEDS = "feeds"
    BLOCKS = "blocks"
    MISSING = "missing"


@dataclass(frozen=True)
class GraphNode:
    """One real object, represented once. `details` holds only
    structured, closed-vocabulary or short-text facts already present
    on the source object -- never invented, never AI-generated prose,
    the same discipline `Finding.details` already enforces."""

    id: str
    kind: GraphNodeKind
    case_id: str
    recorded_at: datetime | None
    details: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    """One real, directional relationship between two `GraphNode`s
    already present in the same `EvidenceGraph`. `id` is deterministic
    (`f"{source_id}:{kind.value}:{target_id}"`), so the same input
    always produces the same edge id -- no random generation, matching
    `Finding.id`'s own determinism guarantee."""

    id: str
    source_id: str
    target_id: str
    kind: DependencyKind


@dataclass(frozen=True)
class EvidenceGraph:
    case_id: str
    generated_at: datetime
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]


class WeaknessKind(str, Enum):
    """Deliverable 5 -- structure only, never a new analysis. Each
    member is a purely structural fact about the graph's own shape."""

    SINGLE_SUPPORT = "single_support"
    """Exactly one incoming `SUPPORTS` edge and no `CONTRADICTS` --
    "noder med endast ett stöd." Losing that one supporting node would
    leave this conclusion with none."""

    NO_SUPPORT = "no_support"
    """A conclusion (`FINDING`) with zero incoming `SUPPORTS`/
    `CONTRADICTS` edges at all -- "svagt underbyggda slutsatser.\""""

    CRITICAL_DEPENDENCY = "critical_dependency"
    """A node many other nodes depend on (in-degree at or above a fixed,
    disclosed threshold) -- "kritiska beroenden." Removing it would
    affect several conclusions at once."""

    ISOLATED_CHAIN = "isolated_chain"
    """An `OBSERVATION` no `DECISION` or `FINDING` ever references --
    "ensamma observationskedjor": recorded, possibly evidenced, but
    never actually used in any conclusion."""


@dataclass(frozen=True)
class WeakDependency:
    node_id: str
    kind: WeaknessKind
    detail: int
    """The structural count the classification is based on (the
    support count for `SINGLE_SUPPORT`/`NO_SUPPORT`, the in-degree for
    `CRITICAL_DEPENDENCY`, always `0` for `ISOLATED_CHAIN`)."""


@dataclass(frozen=True)
class EvidenceGraphComparisonSide:
    """Deliverable 9 (Compare Integration) -- three real, structural
    counts, never a score and never a recommendation."""

    ticker: str
    case_id: str
    independent_observation_chains: int
    """`OBSERVATION` nodes actually used by a `DECISION`/`FINDING` --
    i.e. every `OBSERVATION` node that is not `ISOLATED_CHAIN`."""
    critical_dependency_count: int
    weak_link_count: int
    """Every `WeakDependency`, of any kind, this Case has."""


@dataclass(frozen=True)
class EvidenceGraphComparison:
    a: EvidenceGraphComparisonSide
    b: EvidenceGraphComparisonSide


@dataclass(frozen=True)
class ImpactedChange:
    """Deliverable 10 (Daily Brief Integration) -- "detta påverkar tre
    slutsatser." A real, counted fact: how many other `FINDING` nodes
    transitively depend (via `provenance.dependencies`) on the Finding
    a real `ChangeFinding` names."""

    change_id: str
    affected_finding_count: int

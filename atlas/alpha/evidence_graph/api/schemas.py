"""HTTP response schemas for Evidence Graph. Wire format is camelCase
via the shared Core `CamelModel` (ADR-004). Every field is a direct
read of an already-computed `EvidenceGraph`/`WeakDependency` -- nothing
is recomputed or reworded here."""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.evidence_graph.models import (
    EvidenceGraph,
    EvidenceGraphComparison,
    EvidenceGraphComparisonSide,
    GraphEdge,
    GraphNode,
    ImpactedChange,
    WeakDependency,
    WeaknessKind,
)
from atlas.alpha.evidence_graph.portfolio import PortfolioSharedWeakPoints, SharedWeakPoint
from atlas.core.infrastructure.api.serialization import CamelModel


class GraphNodeView(CamelModel):
    id: str
    kind: str
    recorded_at: datetime | None
    details: dict[str, str | int | float | bool | None]

    @classmethod
    def from_domain(cls, node: GraphNode) -> "GraphNodeView":
        return cls(id=node.id, kind=node.kind.value, recorded_at=node.recorded_at, details=node.details)


class GraphEdgeView(CamelModel):
    id: str
    source_id: str
    target_id: str
    kind: str

    @classmethod
    def from_domain(cls, edge: GraphEdge) -> "GraphEdgeView":
        return cls(id=edge.id, source_id=edge.source_id, target_id=edge.target_id, kind=edge.kind.value)


class WeakDependencyView(CamelModel):
    node_id: str
    kind: str
    detail: int

    @classmethod
    def from_domain(cls, weak: WeakDependency) -> "WeakDependencyView":
        return cls(node_id=weak.node_id, kind=weak.kind.value, detail=weak.detail)


class EvidenceGraphSummaryView(CamelModel):
    """Deliverable 6's own "kompakt" entry point -- a compact digest a
    caller can render without walking the full node/edge list at all;
    the full graph is still there underneath for anything that wants to
    go deeper ("progressivt")."""

    node_count: int
    edge_count: int
    single_support_count: int
    no_support_count: int
    critical_dependency_count: int
    isolated_chain_count: int
    most_critical_node_id: str | None
    """The `CRITICAL_DEPENDENCY` node with the highest in-degree, or
    `None` when there is none -- ties broken by node id (stable,
    deterministic, never arbitrary)."""


class ImpactedChangeView(CamelModel):
    change_id: str
    affected_finding_count: int

    @classmethod
    def from_domain(cls, impacted: ImpactedChange) -> "ImpactedChangeView":
        return cls(change_id=impacted.change_id, affected_finding_count=impacted.affected_finding_count)


class EvidenceGraphView(CamelModel):
    case_id: str
    generated_at: datetime
    nodes: list[GraphNodeView]
    edges: list[GraphEdgeView]
    weak_dependencies: list[WeakDependencyView]
    impacted_changes: list[ImpactedChangeView]
    summary: EvidenceGraphSummaryView

    @classmethod
    def from_domain(
        cls,
        graph: EvidenceGraph,
        weak_dependencies: tuple[WeakDependency, ...],
        impacted_changes: tuple[ImpactedChange, ...] = (),
    ) -> "EvidenceGraphView":
        critical = [w for w in weak_dependencies if w.kind is WeaknessKind.CRITICAL_DEPENDENCY]
        most_critical = max(critical, key=lambda w: (w.detail, w.node_id), default=None)
        summary = EvidenceGraphSummaryView(
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            single_support_count=sum(1 for w in weak_dependencies if w.kind is WeaknessKind.SINGLE_SUPPORT),
            no_support_count=sum(1 for w in weak_dependencies if w.kind is WeaknessKind.NO_SUPPORT),
            critical_dependency_count=len(critical),
            isolated_chain_count=sum(1 for w in weak_dependencies if w.kind is WeaknessKind.ISOLATED_CHAIN),
            most_critical_node_id=most_critical.node_id if most_critical is not None else None,
        )
        return cls(
            case_id=graph.case_id,
            generated_at=graph.generated_at,
            nodes=[GraphNodeView.from_domain(n) for n in graph.nodes],
            edges=[GraphEdgeView.from_domain(e) for e in graph.edges],
            weak_dependencies=[WeakDependencyView.from_domain(w) for w in weak_dependencies],
            impacted_changes=[ImpactedChangeView.from_domain(i) for i in impacted_changes],
            summary=summary,
        )


class EvidenceGraphComparisonSideView(CamelModel):
    ticker: str
    case_id: str
    independent_observation_chains: int
    critical_dependency_count: int
    weak_link_count: int

    @classmethod
    def from_domain(cls, side: EvidenceGraphComparisonSide) -> "EvidenceGraphComparisonSideView":
        return cls(
            ticker=side.ticker,
            case_id=side.case_id,
            independent_observation_chains=side.independent_observation_chains,
            critical_dependency_count=side.critical_dependency_count,
            weak_link_count=side.weak_link_count,
        )


class EvidenceGraphComparisonView(CamelModel):
    """Deliverable 9 -- "ingen rekommendation": three real counts per
    side, nothing that ranks or recommends one over the other."""

    a: EvidenceGraphComparisonSideView
    b: EvidenceGraphComparisonSideView

    @classmethod
    def from_domain(cls, comparison: EvidenceGraphComparison) -> "EvidenceGraphComparisonView":
        return cls(
            a=EvidenceGraphComparisonSideView.from_domain(comparison.a),
            b=EvidenceGraphComparisonSideView.from_domain(comparison.b),
        )


class SharedWeakPointView(CamelModel):
    signature: str
    case_ids: list[str]
    tickers: list[str]

    @classmethod
    def from_domain(cls, point: SharedWeakPoint) -> "SharedWeakPointView":
        return cls(signature=point.signature, case_ids=list(point.case_ids), tickers=list(point.tickers))


class PortfolioSharedWeakPointsView(CamelModel):
    """Deliverable 7 -- "ingen ny ranking, endast förståelse": every
    list here is a real grouping of already-real facts, never a score."""

    shared_weak_assumptions: list[SharedWeakPointView]
    shared_conditions: list[SharedWeakPointView]
    shared_missing_evidence: list[SharedWeakPointView]

    @classmethod
    def from_domain(cls, points: PortfolioSharedWeakPoints) -> "PortfolioSharedWeakPointsView":
        return cls(
            shared_weak_assumptions=[SharedWeakPointView.from_domain(p) for p in points.shared_weak_assumptions],
            shared_conditions=[SharedWeakPointView.from_domain(p) for p in points.shared_conditions],
            shared_missing_evidence=[SharedWeakPointView.from_domain(p) for p in points.shared_missing_evidence],
        )

"""The graph builder itself (Deliverable 3) and structure-only
traversal/weak-dependency functions (Deliverable 5). Every function
here is pure and deterministic -- no AI, no probabilities, no I/O.

**Why the flat `CanonicalAnalysis.findings` list, not the richer
per-section `BusinessFinding`/`ValuationFinding`/`RiskFinding` types.**
Only the flat list carries `Finding.provenance.dependencies` -- the
real backbone this graph needs to answer "why did conviction change"
(Conviction's own Finding depends on Coverage's own Finding, etc; see
`atlas.analysis_engine.provenance.Provenance`). The richer per-section
types carry a *better* discriminated `supporting_evidence`/
`contradicting_evidence` split, but using both would create two nodes
for the same real conclusion (the flat `BUSINESS_CATEGORY_ASSESSED`
Finding is documented, in `atlas.analysis_engine.findings`, as "a flat,
cross-cutting projection of the richer `BusinessFinding` type" -- the
same fact, twice). This module takes the flat list as the single
source of truth and accepts a disclosed, coarser limitation instead:
`Finding.evidence_references` mixes supporting and contradicting ids
with no per-reference discriminator for three Finding kinds
(`BUSINESS_CATEGORY_ASSESSED`/`VALUATION_METHOD_ASSESSED`/
`RISK_CATEGORY_ASSESSED`) -- see `_edge_kind_for_finding` below. Only
`CONTRADICTING_EVIDENCE` Findings are unambiguous (their entire purpose
is contradiction, per `atlas.analysis_engine.pipeline`'s own
construction), and are classified as `CONTRADICTS` accordingly; every
other kind's references are classified `SUPPORTS`.

**Only `Observation` ids are resolved from `evidence_references`.**
That field is also known to sometimes hold `BusinessFact`/
`ValuationFact` ids (see this package's own audit in `__init__.py`).
This graph deliberately has no node for individual facts -- Deliverable
6 asks for a compact, investor-legible graph, and dozens of raw XBRL
facts per Case would defeat that. A reference that does not resolve to
a known `Observation` id is silently skipped, never guessed at --
Deliverable 3's "endast verkliga relationer."

**Live Verification finding (Deliverable 14), corrected here.** An
early version of `detect_weak_dependencies` flagged every `FINDING`
node with zero incoming evidence edges as `NO_SUPPORT` -- but nine
`FindingKind` members (`EVIDENCE_COVERAGE`/`BUSINESS_ANALYSIS
_UNAVAILABLE`/`VALUATION_UNAVAILABLE`/`EXECUTION_PRICE_HISTORY`/
`HOLDING_CONTEXT`/`PORTFOLIO_FACTOR_UNAVAILABLE`/`CONVICTION_ASSESSED`/
`RECOMMENDATION_WITHHELD`/`RECOMMENDATION_DIRECTION_SELECTED`) are
constructed with `evidence_references=()` **always**, by
`atlas.analysis_engine.pipeline`'s own unconditional construction --
confirmed by reading every one of that module's own `Finding(...)`
call sites. Flagging these as "weakly supported" overstates a weakness
that isn't real: these Findings are disclosures/structural facts, not
evidence-grounded claims, and their own emptiness is permanent and
expected, not a signal about this run's data. `_EVIDENCE_BEARING_KINDS`
below is the corrected, narrower set `NO_SUPPORT`/`SINGLE_SUPPORT`
apply to -- the six kinds whose `evidence_references` genuinely vary
with the underlying data (confirmed the same way)."""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.findings import Finding, FindingKind
from atlas.analysis_engine.investment_case_change import ChangeFinding
from atlas.core.domain.assumption.entity import AssumptionView
from atlas.core.domain.case_condition.entity import CaseConditionView
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.value_objects import Direction
from atlas.core.domain.observation.entity import Observation

from atlas.alpha.evidence_graph.models import (
    DependencyKind,
    EvidenceGraph,
    GraphEdge,
    GraphNode,
    GraphNodeKind,
    ImpactedChange,
    WeakDependency,
    WeaknessKind,
)

__all__ = [
    "build_evidence_graph",
    "detect_weak_dependencies",
    "downstream_impact",
    "upstream_support",
    "compute_impact_summary",
    "CRITICAL_DEPENDENCY_THRESHOLD",
]

CRITICAL_DEPENDENCY_THRESHOLD = 3
"""A fixed, disclosed threshold, not an invented score -- an in-degree
at or above this many real edges is what `CRITICAL_DEPENDENCY` means.
Chosen as the smallest count past "a couple" that still reads as
"several conclusions," matching this codebase's existing preference for
plain, explainable constants over any computed/weighted score."""

_SUPPORT_EDGE_KINDS = (DependencyKind.SUPPORTS, DependencyKind.CONTRADICTS)

_EVIDENCE_BEARING_KINDS = frozenset(
    {
        FindingKind.CONTRADICTING_EVIDENCE.value,
        FindingKind.MISSING_EVIDENCE.value,
        FindingKind.BUSINESS_CATEGORY_ASSESSED.value,
        FindingKind.VALUATION_METHOD_ASSESSED.value,
        FindingKind.RISK_CATEGORY_ASSESSED.value,
    }
)
"""The five `FindingKind` members whose `evidence_references` genuinely
vary with the underlying data (see this module's own "Live
Verification finding" docstring above for how this was confirmed). The
other ten members are always constructed with `evidence_references=()`
-- flagging them `NO_SUPPORT`/`SINGLE_SUPPORT` would overstate a
weakness that is permanent and structural, not a fact about this
Case's own evidence.

**Sprint 12 (Analysis Coverage Expansion, Deliverable 6) -- `OPEN_QUESTION`
removed.** An open question already discloses its own gap by
existing at all ("Atlas has an unresolved question about X"); flagging
it `NO_SUPPORT`/`SINGLE_SUPPORT` on top of that double-counts the same
fact under a second name rather than reporting anything new."""

_THESIS_RISK_LOW_STATUS = ("thesis_risk", "low")


def _is_permanently_unsupported_by_design(node_kind_value: str, details: dict) -> bool:
    """Sprint 12 (Analysis Coverage Expansion, Deliverable 6) -- audited
    against a real company (AAPL): `atlas.analysis_engine.risk
    .thesis_risk.evaluate_thesis_risk` constructs `RiskStatus.LOW`
    ("Evidence exists and was checked; none of it contradicts the
    recorded thesis") with `supporting_facts=()` unconditionally, by
    design -- an absence-of-contradiction conclusion has nothing
    positive to cite. Flagging it `NO_SUPPORT` would relabel a complete,
    honest "checked, found nothing" conclusion as a gap. Every other
    `risk_category_assessed`/`business_category_assessed`/
    `valuation_method_assessed` combination is left exactly as it was
    -- this is a single, narrowly-scoped, audited exception, not a
    general softening of the check."""
    if node_kind_value != FindingKind.RISK_CATEGORY_ASSESSED.value:
        return False
    return (details.get("risk_category"), details.get("status")) == _THESIS_RISK_LOW_STATUS

_DEPENDENCY_EDGE_KINDS = (
    DependencyKind.SUPPORTS,
    DependencyKind.CONTRADICTS,
    DependencyKind.DEPENDS_ON,
    DependencyKind.DERIVED_FROM,
    DependencyKind.FEEDS,
)


def _edge(source_id: str, target_id: str, kind: DependencyKind) -> GraphEdge:
    return GraphEdge(id=f"{source_id}:{kind.value}:{target_id}", source_id=source_id, target_id=target_id, kind=kind)


def _edge_kind_for_finding(finding: Finding) -> DependencyKind:
    """See this module's own docstring for why this is Finding-kind-
    level, not reference-level."""
    if finding.kind is FindingKind.CONTRADICTING_EVIDENCE:
        return DependencyKind.CONTRADICTS
    return DependencyKind.SUPPORTS


def build_evidence_graph(
    case_id: str,
    *,
    observations: tuple[Observation, ...],
    evidence: tuple[Evidence, ...],
    decisions: tuple[Decision, ...],
    outcomes: tuple,
    # Untyped, deliberately -- `atlas.core.domain.outcome.entity` is
    # Outcome's own write path; `atlas/test_architecture_boundaries.py
    # ::test_alpha_does_not_write_to_outcome` forbids Alpha from
    # importing it at all, matching `InvestmentCaseComposition
    # Service._assemble`'s own identical `outcomes: tuple` type hint
    # for the exact same reason.
    case_conditions: tuple[CaseConditionView, ...],
    assumptions: tuple[AssumptionView, ...],
    findings: tuple[Finding, ...],
    generated_at: datetime,
) -> EvidenceGraph:
    """Input: an already-composed analysis (this Case's own
    Observations/Evidence/Decisions/Outcomes, its active CaseConditions/
    Assumptions, and its `CanonicalAnalysis.findings`). Output: the
    dependency network among them. Never recomputes any analysis --
    every node is a direct read of an already-real object; every edge
    is a direct read of an already-real reference field."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    node_ids: set[str] = set()

    def add_node(node_id: str, kind: GraphNodeKind, recorded_at: datetime | None, details: dict) -> None:
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        nodes.append(GraphNode(id=node_id, kind=kind, case_id=case_id, recorded_at=recorded_at, details=details))

    def add_edge(source_id: str, target_id: str, kind: DependencyKind) -> None:
        if source_id not in node_ids or target_id not in node_ids:
            return
        edges.append(_edge(source_id, target_id, kind))

    for observation in observations:
        add_node(
            str(observation.id),
            GraphNodeKind.OBSERVATION,
            observation.recorded_at,
            {"statement": str(observation.statement)},
        )

    for item in evidence:
        add_node(
            str(item.id),
            GraphNodeKind.EVIDENCE,
            item.recorded_at,
            {"statement": str(item.statement), "direction": item.direction.value},
        )

    for decision in decisions:
        add_node(
            str(decision.id),
            GraphNodeKind.DECISION,
            decision.recorded_at,
            {"decision_type": decision.decision_type.value, "reason": decision.investment_case.reason},
        )

    for outcome in outcomes:
        add_node(str(outcome.id), GraphNodeKind.OUTCOME, outcome.recorded_at, {"statement": str(outcome.statement)})

    for condition in case_conditions:
        add_node(
            str(condition.condition_id),
            GraphNodeKind.CASE_CONDITION,
            condition.updated_at,
            {
                "predicate_text": condition.predicate_text,
                "status": condition.status,
                "role": condition.role,
            },
        )

    for assumption in assumptions:
        add_node(
            str(assumption.assumption_id),
            GraphNodeKind.ASSUMPTION,
            assumption.updated_at,
            {"statement": assumption.statement, "status": assumption.status},
        )

    for finding in findings:
        add_node(
            finding.id,
            GraphNodeKind.FINDING,
            finding.provenance.computed_at,
            {
                # Sprint 12 (Analysis Coverage Expansion, Deliverable 6)
                # -- `Finding.details` is real, already-computed
                # structured fact this graph previously discarded (e.g.
                # `{"risk_category": "thesis_risk", "status": "low"}`).
                # Forwarded first so the fixed keys below always win any
                # (currently nonexistent) collision.
                **finding.details,
                "kind": finding.kind.value,
                "severity": finding.severity.value,
                "producer": finding.producer.value,
                "evidence_reference_count": len(finding.evidence_references),
                # Deliverable 5/14 -- the real, raw count `Finding.evidence
                # _references` itself carries, independent of whether a
                # given reference resolves to a node in *this* graph (most
                # do not: they are usually `BusinessFact`/`ValuationFact`
                # ids, which this graph deliberately never turns into
                # nodes -- see this module's own docstring). Weak-
                # dependency detection reads this real count, not resolved
                # edges, so a Finding genuinely grounded in ingested
                # financial data is never misclassified `NO_SUPPORT` just
                # because that data isn't itself a node here.
            },
        )

    # Evidence -> Observation: real, mandatory `observation_id`, direction
    # taken verbatim from the investor's own `Direction`.
    for item in evidence:
        kind = DependencyKind.SUPPORTS if item.direction is Direction.SUPPORTS else DependencyKind.CONTRADICTS
        add_edge(str(item.id), str(item.observation_id), kind)

    # Decision -> Observation: only when the optional anchor is set.
    for decision in decisions:
        if decision.observation_id is not None:
            add_edge(str(decision.id), str(decision.observation_id), DependencyKind.DEPENDS_ON)

    # Outcome -> Decision: real, mandatory `decision_id`.
    for outcome in outcomes:
        add_edge(str(outcome.id), str(outcome.decision_id), DependencyKind.DERIVED_FROM)

    # CaseCondition -> Decision: only when the optional anchor is set.
    for condition in case_conditions:
        if condition.decision_id is not None:
            add_edge(str(condition.condition_id), str(condition.decision_id), DependencyKind.DEPENDS_ON)

    # Assumption -> Decision: real, mandatory `decision_id`.
    for assumption in assumptions:
        add_edge(str(assumption.assumption_id), str(assumption.decision_id), DependencyKind.DEPENDS_ON)

    # CaseCondition -> Assumption: real, investor-linked via
    # `AssumptionService.attach_case_condition` -- "this condition's
    # evaluation feeds whether the assumption still holds."
    for assumption in assumptions:
        for linked_id in assumption.linked_case_condition_ids:
            add_edge(linked_id, str(assumption.assumption_id), DependencyKind.FEEDS)

    # Evidence -> Assumption: real, only when the assumption's latest
    # challenge named a real Evidence id (`AssumptionService.challenge`
    # is documented as "the challenges direction" -- always CONTRADICTS).
    for assumption in assumptions:
        if assumption.last_challenge_evidence_id is not None:
            add_edge(assumption.last_challenge_evidence_id, str(assumption.assumption_id), DependencyKind.CONTRADICTS)

    # Finding -> Finding: real `provenance.dependencies`.
    for finding in findings:
        for dep_id in finding.provenance.dependencies:
            add_edge(finding.id, dep_id, DependencyKind.DEPENDS_ON)

    # Observation -> Finding: real `evidence_references`, resolved only
    # against known Observation ids (see module docstring).
    for finding in findings:
        edge_kind = _edge_kind_for_finding(finding)
        for reference in finding.evidence_references:
            add_edge(reference, finding.id, edge_kind)

    return EvidenceGraph(case_id=case_id, generated_at=generated_at, nodes=tuple(nodes), edges=tuple(edges))


def _in_degree(graph: EvidenceGraph, node_id: str, kinds: tuple[DependencyKind, ...]) -> int:
    return sum(1 for e in graph.edges if e.target_id == node_id and e.kind in kinds)


def detect_weak_dependencies(graph: EvidenceGraph) -> tuple[WeakDependency, ...]:
    """Deliverable 5 -- structure only. Every rule reads only the
    already-built graph's own edges; nothing here re-runs any
    analysis."""
    nodes_by_id = {n.id: n for n in graph.nodes}
    results: list[WeakDependency] = []

    for node in graph.nodes:
        node_kind_value = node.details.get("kind")
        if (
            node.kind is GraphNodeKind.FINDING
            and node_kind_value in _EVIDENCE_BEARING_KINDS
            and not _is_permanently_unsupported_by_design(node_kind_value, node.details)
        ):
            # Real evidence count (see `build_evidence_graph`'s own
            # comment on this field) -- not resolved-edge count, so a
            # Finding grounded in ingested financial data (never a node
            # here) is never misclassified as unsupported.
            real_evidence_count = node.details.get("evidence_reference_count", 0)
            if not isinstance(real_evidence_count, int):
                real_evidence_count = 0
            if real_evidence_count == 1:
                results.append(WeakDependency(node_id=node.id, kind=WeaknessKind.SINGLE_SUPPORT, detail=1))
            elif real_evidence_count == 0:
                results.append(WeakDependency(node_id=node.id, kind=WeaknessKind.NO_SUPPORT, detail=0))

        dependency_in_degree = _in_degree(graph, node.id, _DEPENDENCY_EDGE_KINDS)
        if dependency_in_degree >= CRITICAL_DEPENDENCY_THRESHOLD:
            results.append(
                WeakDependency(node_id=node.id, kind=WeaknessKind.CRITICAL_DEPENDENCY, detail=dependency_in_degree)
            )

        if node.kind is GraphNodeKind.OBSERVATION:
            used_by = any(
                e.target_id == node.id and nodes_by_id[e.source_id].kind in (GraphNodeKind.DECISION, GraphNodeKind.FINDING)
                for e in graph.edges
                if e.source_id in nodes_by_id
            )
            if not used_by:
                results.append(WeakDependency(node_id=node.id, kind=WeaknessKind.ISOLATED_CHAIN, detail=0))

    return tuple(results)


def downstream_impact(graph: EvidenceGraph, node_id: str) -> tuple[str, ...]:
    """Every node that transitively depends on `node_id` -- "if this
    disappears, what does it affect." Follows edges in reverse (a node
    X with an edge X -> node_id is affected by node_id)."""
    visited: set[str] = set()
    frontier = [node_id]
    while frontier:
        current = frontier.pop()
        incoming = [e.source_id for e in graph.edges if e.target_id == current and e.source_id not in visited]
        for source_id in incoming:
            visited.add(source_id)
            frontier.append(source_id)
    return tuple(visited)


def compute_impact_summary(graph: EvidenceGraph, changes: tuple[ChangeFinding, ...]) -> tuple[ImpactedChange, ...]:
    """Deliverable 10 -- "detta påverkar tre slutsatser." Only real,
    resolvable changes produce a result: a `ChangeFinding` with no
    `source_finding_id`, or one that does not resolve to a `FINDING`
    node in *this* (current) graph, is silently skipped -- never a
    fabricated "0 affected" entry."""
    finding_ids = {n.id for n in graph.nodes if n.kind is GraphNodeKind.FINDING}
    results: list[ImpactedChange] = []
    for change in changes:
        if change.source_finding_id is None or change.source_finding_id not in finding_ids:
            continue
        affected = [node_id for node_id in downstream_impact(graph, change.source_finding_id) if node_id in finding_ids]
        if affected:
            results.append(ImpactedChange(change_id=change.id, affected_finding_count=len(affected)))
    return tuple(results)


def upstream_support(graph: EvidenceGraph, node_id: str) -> tuple[str, ...]:
    """Every node `node_id` transitively rests on -- "follow the support
    backward." Follows edges forward (node_id -> Y means node_id rests
    on Y)."""
    visited: set[str] = set()
    frontier = [node_id]
    while frontier:
        current = frontier.pop()
        outgoing = [e.target_id for e in graph.edges if e.source_id == current and e.target_id not in visited]
        for target_id in outgoing:
            visited.add(target_id)
            frontier.append(target_id)
    return tuple(visited)

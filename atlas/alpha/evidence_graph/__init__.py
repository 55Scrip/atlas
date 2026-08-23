"""Evidence Graph & Dependency Understanding (Atlas Intelligence Sprint
10). Alpha-only, no Core change.

**Deliverable 1 (Dependency Audit) -- summary of the findings this
package is built on** (full detail in this sprint's own Final Report):

- Core objects carry a small, real, typed set of foreign-key-like
  fields: `Decision.observation_id` (optional), `Evidence
  .observation_id` (mandatory), `Outcome.decision_id` (mandatory),
  `CaseConditionEvent.decision_id` (optional), `AssumptionEvent
  .decision_id` (mandatory) and `.linked_case_condition_ids`/
  `.evidence_id` (both untyped strings, the latter unvalidated --
  `AssumptionService` has no `EvidenceRepository` and never checks
  `evidence_id` names a real `Evidence`).
- The analysis pipeline (`atlas.analysis_engine`) is a strict,
  already-existing DAG: `assemble_analysis` -> `CoverageAssessment` ->
  `Stance`/`PortfolioFitAssessment` -> `EvidenceSnapshot` ->
  `MonitoringResult` -> `DailyBriefAgenda`, each stage reading only
  already-computed upstream output, never recomputing it (Deliverable
  1's "no redesign" -- confirmed, not changed, by this sprint).
- The one real, already-existing traceability primitive is `Finding
  .provenance` (`atlas.analysis_engine.provenance.Provenance`):
  `dependencies` names other `Finding.id`s; `evidence_references` names
  `ObservationId`/`BusinessFact`/`ValuationFact` ids, as a bare string
  tuple with no per-reference discriminator of which kind. This graph
  is built directly from those two fields (see `engine.py`'s own
  docstring for exactly how, and its disclosed limitation).
- No genuine cycle exists anywhere in the audited scope. `ChangeIntelligence`'s
  own snapshot comparison (`compare_snapshots`) is a time-series diff of
  two distinct, timestamped values, not self-reference -- excluded from
  this graph as a different kind of relationship entirely (see
  `atlas.alpha.monitoring`'s own module for how Monitoring already
  consumes it).
- Several real relationships exist in intent but are currently
  unenforced or uncaptured (`AssumptionEvent.evidence_id`'s missing
  validation; `CaseConditionEvent.observed_value`'s missing source
  field; `AgendaItem`'s missing `condition_id`/`assumption_id`). None
  of these is fixed by this sprint (Deliverable 1's "no redesign") --
  each is carried into this graph only where a real, resolvable id is
  actually present (see `engine.py`'s `add_edge`, which silently skips
  any reference that does not resolve to a real node).

Re-exports: `GraphNodeKind`, `DependencyKind`, `GraphNode`, `GraphEdge`,
`EvidenceGraph`, `WeaknessKind`, `WeakDependency`,
`EvidenceGraphService`.
"""
from __future__ import annotations

from atlas.alpha.evidence_graph.models import (
    DependencyKind,
    EvidenceGraph,
    GraphEdge,
    GraphNode,
    GraphNodeKind,
    WeakDependency,
    WeaknessKind,
)
from atlas.alpha.evidence_graph.service import CaseEvidenceGraph, EvidenceGraphService

__all__ = [
    "GraphNodeKind",
    "DependencyKind",
    "GraphNode",
    "GraphEdge",
    "EvidenceGraph",
    "WeaknessKind",
    "WeakDependency",
    "EvidenceGraphService",
    "CaseEvidenceGraph",
]

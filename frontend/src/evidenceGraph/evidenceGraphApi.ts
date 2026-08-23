/**
 * Thin typed client for the Evidence Graph (Atlas Intelligence Sprint
 * 10, `atlas/alpha/evidence_graph/api/`). Field names mirror the
 * backend's own `CamelModel` views exactly. This module adds no logic
 * of its own beyond the wire-format mapping.
 */

export type GraphNodeKind = "observation" | "evidence" | "decision" | "outcome" | "case_condition" | "assumption" | "finding";

export type DependencyKind =
  | "supports"
  | "contradicts"
  | "depends_on"
  | "derived_from"
  | "explains"
  | "feeds"
  | "blocks"
  | "missing";

export type WeaknessKind = "single_support" | "no_support" | "critical_dependency" | "isolated_chain";

export interface GraphNodeView {
  id: string;
  kind: GraphNodeKind;
  recordedAt: string | null;
  details: Record<string, string | number | boolean | null>;
}

export interface GraphEdgeView {
  id: string;
  sourceId: string;
  targetId: string;
  kind: DependencyKind;
}

export interface WeakDependencyView {
  nodeId: string;
  kind: WeaknessKind;
  detail: number;
}

export interface ImpactedChangeView {
  changeId: string;
  affectedFindingCount: number;
}

export interface EvidenceGraphSummaryView {
  nodeCount: number;
  edgeCount: number;
  singleSupportCount: number;
  noSupportCount: number;
  criticalDependencyCount: number;
  isolatedChainCount: number;
  mostCriticalNodeId: string | null;
}

export interface EvidenceGraphView {
  caseId: string;
  generatedAt: string;
  nodes: GraphNodeView[];
  edges: GraphEdgeView[];
  weakDependencies: WeakDependencyView[];
  impactedChanges: ImpactedChangeView[];
  summary: EvidenceGraphSummaryView;
}

export async function fetchEvidenceGraph(caseId: string, signal?: AbortSignal): Promise<EvidenceGraphView> {
  const response = await fetch(`/api/evidence-graph/${encodeURIComponent(caseId)}`, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as EvidenceGraphView;
}

import type { TranslationKey } from "../i18n";
import type { GraphNodeKind, GraphNodeView, WeaknessKind } from "./evidenceGraphApi";

/**
 * Language Audit (Deliverable 11) -- this module is the one place
 * `GraphNodeKind`/`WeaknessKind` (real, technical, backend-internal
 * names) are turned into the plain vocabulary the brief requires:
 * "stöd" / "bygger på" / "påverkar" / "saknar stöd" -- never "node",
 * "edge", "dependency graph", or "DAG" anywhere in rendered copy.
 */

export const NODE_KIND_KEY: Record<GraphNodeKind, TranslationKey> = {
  observation: "evidenceGraph.node.observation",
  evidence: "evidenceGraph.node.evidence",
  decision: "evidenceGraph.node.decision",
  outcome: "evidenceGraph.node.outcome",
  case_condition: "evidenceGraph.node.caseCondition",
  assumption: "evidenceGraph.node.assumption",
  finding: "evidenceGraph.node.finding",
};

export const WEAKNESS_KEY: Record<WeaknessKind, TranslationKey> = {
  single_support: "evidenceGraph.weakness.singleSupport",
  no_support: "evidenceGraph.weakness.noSupport",
  critical_dependency: "evidenceGraph.weakness.criticalDependency",
  isolated_chain: "evidenceGraph.weakness.isolatedChain",
};

/**
 * A short, real label for one node -- the node's own statement/
 * predicate text when it has one (an investor's or Atlas's own words,
 * never invented here), otherwise the translated kind name.
 */
export function nodeLabel(node: GraphNodeView, t: (key: TranslationKey) => string): string {
  const details = node.details;
  // `details` is a raw structured-facts dict (`Finding.details`'s own
  // convention) -- its keys are never camelCased by `CamelModel`,
  // unlike this view's own declared fields.
  const text = details.statement ?? details.predicate_text ?? details.reason;
  if (typeof text === "string" && text.trim().length > 0) return text;
  return t(NODE_KIND_KEY[node.kind]);
}

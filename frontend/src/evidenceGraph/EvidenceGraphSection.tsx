import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { NODE_KIND_KEY, WEAKNESS_KEY, nodeLabel } from "./describeEvidenceGraph";
import type { EvidenceGraphView, WeaknessKind } from "./evidenceGraphApi";

/**
 * Investment Case Integration (Atlas Intelligence Sprint 10,
 * Deliverable 6). "Kompakt": one always-visible summary line, no full
 * node/edge listing. "Progressivt": the specific weak links are one
 * click away, in `<ExpandableDetail>` -- the same primitive every
 * other progressive-disclosure section on this page already uses.
 * Renders nothing (not even the heading) when the graph is genuinely
 * empty -- an honest absence, never a placeholder for a Case with no
 * recorded activity yet.
 */

const WEAKNESS_TONE: Record<WeaknessKind, StatusTone> = {
  single_support: "caution",
  no_support: "critical",
  critical_dependency: "caution",
  isolated_chain: "neutral",
};

export function EvidenceGraphSection({ graph, t }: { graph: EvidenceGraphView; t: (key: TranslationKey, params?: Record<string, string | number>) => string }) {
  if (graph.summary.nodeCount === 0) return null;

  const nodesById = new Map(graph.nodes.map((n) => [n.id, n]));
  const weakCount = graph.summary.singleSupportCount + graph.summary.isolatedChainCount;
  const maxImpact = graph.impactedChanges.reduce((max, i) => Math.max(max, i.affectedFindingCount), 0);

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Heading level={3}>{t("evidenceGraph.section.heading")}</Heading>
        <Text color="secondary">
          {t("evidenceGraph.section.summary", {
            critical: graph.summary.criticalDependencyCount,
            weak: weakCount,
            missing: graph.summary.noSupportCount,
          })}
        </Text>
        {maxImpact > 0 && <Text color="secondary">{t("evidenceGraph.section.impact", { count: maxImpact })}</Text>}
        {graph.weakDependencies.length > 0 ? (
          <ExpandableDetail summaryLabel={t("evidenceGraph.section.expandLabel")}>
            <Stack gap="metadata">
              {graph.weakDependencies.map((weak) => {
                const node = nodesById.get(weak.nodeId);
                return (
                  <Inline key={`${weak.nodeId}:${weak.kind}`} gap="row" align="center" wrap>
                    <StatusBadge label={t(WEAKNESS_KEY[weak.kind])} tone={WEAKNESS_TONE[weak.kind]} />
                    <Text as="span" color="secondary">
                      {node ? nodeLabel(node, t) : t(NODE_KIND_KEY.finding)}
                    </Text>
                  </Inline>
                );
              })}
            </Stack>
          </ExpandableDetail>
        ) : (
          <Text color="tertiary">{t("evidenceGraph.section.noWeakLinks")}</Text>
        )}
      </Stack>
    </Surface>
  );
}

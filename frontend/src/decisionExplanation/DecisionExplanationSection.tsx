import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { ACTION_KEY } from "../investmentDecision/describeInvestmentDecision";
import { STRENGTH_KEY } from "../recommendationConviction/describeRecommendationConviction";
import { LAYER_KEY, referenceLabel } from "./describeDecisionExplanation";
import type {
  BlockingFindingView,
  DecisionExplanationView,
  ExplanationReferenceView,
  SupportingFindingView,
} from "./decisionExplanationApi";

/**
 * Investment Case Integration (Atlas Decision Layer Sprint 6,
 * Deliverable 6). One coherent, traceable explanation for why Atlas
 * reached this Case's own current decision -- progressively
 * disclosed: the primary supporting/blocking fact always visible, the
 * full four-section chain one click away. Every fact renders through
 * `referenceLabel` (never raw technical ids/codes as prose) and
 * carries its own `named_by` provenance, so a reader can always see
 * which real Atlas layer surfaced it.
 */
export function DecisionExplanationSection({
  explanation,
  t,
}: {
  explanation: DecisionExplanationView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const hasMore =
    explanation.chain.supporting.length > 0 ||
    explanation.chain.blocking.length > 0 ||
    explanation.chain.dependencySteps.length > 0;

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Heading level={3}>{t("decisionExplanation.section.heading")}</Heading>
        <Inline gap="row" align="center" wrap>
          <StatusBadge label={t(ACTION_KEY[explanation.action as keyof typeof ACTION_KEY])} tone="neutral" />
          <StatusBadge label={t(STRENGTH_KEY[explanation.convictionStrength as keyof typeof STRENGTH_KEY])} tone="neutral" />
        </Inline>
        {explanation.primarySupporting ? (
          <Text color="secondary">{t("decisionExplanation.section.primarySupporting", { fact: referenceLabel(explanation.primarySupporting.reference, t) })}</Text>
        ) : (
          <Text color="tertiary">{t("decisionExplanation.section.noSupporting")}</Text>
        )}
        {explanation.primaryBlocking ? (
          <Text color="secondary">{t("decisionExplanation.section.primaryBlocking", { fact: referenceLabel(explanation.primaryBlocking.reference, t) })}</Text>
        ) : (
          <Text color="tertiary">{t("decisionExplanation.section.noBlocking")}</Text>
        )}
        {hasMore && (
          <ExpandableDetail summaryLabel={t("decisionExplanation.section.expandLabel")}>
            <Stack gap="intra-section">
              <SectionList
                heading={t("decisionExplanation.section.supportingHeading")}
                items={explanation.chain.supporting}
                render={(item) => <FindingRow key={item.reference.id} reference={item.reference} namedBy={item.namedBy} t={t} />}
              />
              <SectionList
                heading={t("decisionExplanation.section.blockingHeading")}
                items={explanation.chain.blocking}
                render={(item) => (
                  <FindingRow
                    key={item.reference.id}
                    reference={item.reference}
                    namedBy={item.namedBy}
                    isChangeTrigger={item.isChangeTrigger}
                    t={t}
                  />
                )}
              />
              <SectionList
                heading={t("decisionExplanation.section.dependencyHeading")}
                items={explanation.chain.dependencySteps}
                render={(item) => (
                  <Text key={item.id} color="secondary">
                    {referenceLabel(item, t)}
                  </Text>
                )}
              />
              <Stack gap="metadata">
                <Text as="span" style={{ fontWeight: 600 }}>
                  {t("decisionExplanation.section.historicalHeading")}
                </Text>
                {explanation.chain.historicalReference ? (
                  <Text color="secondary">{t("decisionExplanation.section.historicalChangeExists")}</Text>
                ) : (
                  <Text color="tertiary">{t("decisionExplanation.section.noHistoricalChange")}</Text>
                )}
              </Stack>
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}

function SectionList<T>({ heading, items, render }: { heading: string; items: T[]; render: (item: T) => React.ReactNode }) {
  if (items.length === 0) return null;
  return (
    <Stack gap="metadata">
      <Text as="span" style={{ fontWeight: 600 }}>
        {heading}
      </Text>
      {items.map(render)}
    </Stack>
  );
}

function FindingRow({
  reference,
  namedBy,
  isChangeTrigger,
  t,
}: {
  reference: ExplanationReferenceView;
  namedBy: (SupportingFindingView | BlockingFindingView)["namedBy"];
  isChangeTrigger?: boolean;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Inline gap="row" align="center" wrap>
      <Text color="secondary">{referenceLabel(reference, t)}</Text>
      {isChangeTrigger && <StatusBadge label={t("decisionExplanation.section.changeTrigger")} tone="caution" />}
      <Text color="tertiary" as="span">
        {t("decisionExplanation.section.namedBy", { layers: namedBy.map((layer) => t(LAYER_KEY[layer])).join(" · ") })}
      </Text>
    </Inline>
  );
}

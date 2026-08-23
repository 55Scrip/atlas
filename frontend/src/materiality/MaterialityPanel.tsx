import { Inline, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { MATERIALITY_LEVEL_TONE } from "../status/statusTone";
import { coverageDimensionLabel, coverageReasonLabel } from "../coverage/describeCoverage";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { materialEvidenceSentence, materialityLevelLabel } from "./describeMateriality";
import type { MaterialEvidenceView, MaterialityAssessmentView } from "./materialityApi";

/**
 * Atlas Intelligence -- Materiality & Priority Engine, Deliverable 5.
 * Leads with the single most material item per bucket -- top
 * supporting/contradicting/limiting/missing evidence, each already
 * picked server-side by a fixed classification, never re-ranked here.
 * The full, materiality-ordered membership of every bucket (background
 * items included, never removed) sits behind one `ExpandableDetail` --
 * "important evidence first, background collapsed," never information
 * lost.
 */
export function MaterialityPanel({ assessment, t }: { assessment: MaterialityAssessmentView; t: Translate }) {
  return (
    <Stack gap="metadata">
      <Text color="secondary" style={{ fontWeight: 600 }}>
        {t("materiality.panel.heading")}
      </Text>

      <Stack gap="metadata">
        {assessment.topSupportingEvidence && (
          <TopPick label={t("materiality.panel.supportingHeading")} item={assessment.topSupportingEvidence} t={t} />
        )}
        {assessment.topContradictingEvidence && (
          <TopPick label={t("materiality.panel.contradictingHeading")} item={assessment.topContradictingEvidence} t={t} />
        )}
        {assessment.topLimitingFactor && (
          <TopPick label={t("materiality.panel.limitingHeading")} item={assessment.topLimitingFactor} t={t} />
        )}
        {assessment.topMissingEvidence && (
          <Stack gap="metadata">
            <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
              {t("materiality.panel.missingHeading")}
            </Text>
            <Text color="tertiary" as="p">
              {coverageDimensionLabel(assessment.topMissingEvidence.dimension, t)}
              {assessment.topMissingEvidence.reasoning[0]
                ? ` — ${coverageReasonLabel(assessment.topMissingEvidence.dimension, assessment.topMissingEvidence.reasoning[0], t)}`
                : ""}
            </Text>
          </Stack>
        )}
      </Stack>

      <ExpandableDetail summaryLabel={t("materiality.panel.expandLabel")}>
        <Stack gap="inter-section">
          <EvidenceList heading={t("materiality.panel.supportingHeading")} items={assessment.supportingEvidence} t={t} />
          <EvidenceList heading={t("materiality.panel.contradictingHeading")} items={assessment.contradictingEvidence} t={t} />
          <EvidenceList heading={t("materiality.panel.limitingHeading")} items={assessment.limitingFactors} t={t} />
        </Stack>
      </ExpandableDetail>
    </Stack>
  );
}

function TopPick({ label, item, t }: { label: string; item: MaterialEvidenceView; t: Translate }) {
  return (
    <Stack gap="metadata">
      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
        {label}
      </Text>
      <Inline gap="metadata" align="center">
        <StatusBadge label={materialityLevelLabel(item, t)} tone={MATERIALITY_LEVEL_TONE[item.materiality]} />
        <Text color="tertiary" as="span">
          {materialEvidenceSentence(item, t)}
        </Text>
      </Inline>
    </Stack>
  );
}

function EvidenceList({ heading, items, t }: { heading: string; items: MaterialEvidenceView[]; t: Translate }) {
  if (items.length === 0) return null;
  return (
    <Stack gap="metadata">
      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
        {heading}
      </Text>
      {items.map((item, index) => (
        <Inline key={index} gap="metadata" align="center">
          <StatusBadge label={materialityLevelLabel(item, t)} tone={MATERIALITY_LEVEL_TONE[item.materiality]} />
          <Text color="tertiary" as="span">
            {materialEvidenceSentence(item, t)}
          </Text>
        </Inline>
      ))}
    </Stack>
  );
}

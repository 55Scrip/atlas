import type { ReactNode } from "react";
import { Stack, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { confidenceReasonSentence, coverageDimensionLabel, coverageReasonLabel } from "../coverage/describeCoverage";
import { stanceReasonSentence } from "../stance/describeStance";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { mostValuableMissingInformationSentence } from "./describeExplanation";
import type { ExplanationView } from "./explainabilityApi";

/**
 * Atlas Intelligence Sprint 3 (Decision Explainability & Evidence
 * Trace, Deliverables 3 + 4 + 9). Answers "why / why not / what's
 * missing / what would help most" for one conclusion, using only
 * already-computed, already-translated reason sentences --
 * `stanceReasonSentence` (Sprint 2) and `confidenceReasonSentence`/
 * `coverageDimensionLabel`/`coverageReasonLabel` (Sprint 1). This
 * component writes no new evidence classification of its own.
 *
 * Deliverable 9 (Missing Information) keeps the single most valuable
 * missing piece always visible, never buried -- the rest of the trace
 * (all five evidence buckets in full) sits behind one `ExpandableDetail`
 * so the page stays calm by default, per the brief's own "never
 * overwhelming" instruction.
 */
export function ExplanationPanel({ explanation, t }: { explanation: ExplanationView; t: Translate }) {
  const { supportingEvidence, contradictingEvidence, limitingFactors, missingEvidence, confidenceDrivers } =
    explanation;

  return (
    <Stack gap="metadata">
      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
        {t("explainability.panel.mostValuableMissingLabel")}
      </Text>
      <Text as="p" color="tertiary">
        {explanation.mostValuableMissingInformation
          ? mostValuableMissingInformationSentence(explanation.mostValuableMissingInformation, t)
          : t("explainability.panel.mostValuableMissingNone")}
      </Text>

      <ExpandableDetail summaryLabel={t("explainability.panel.expandLabel")}>
        <Stack gap="inter-section">
          <EvidenceGroup
            heading={t("explainability.panel.supportingHeading")}
            emptyLabel={t("explainability.panel.noneSupporting")}
          >
            {supportingEvidence.map((reason, index) => (
              <Text key={index} as="p" color="tertiary">
                {stanceReasonSentence(reason, t)}
              </Text>
            ))}
          </EvidenceGroup>

          <EvidenceGroup
            heading={t("explainability.panel.contradictingHeading")}
            emptyLabel={t("explainability.panel.noneContradicting")}
          >
            {contradictingEvidence.map((reason, index) => (
              <Text key={index} as="p" color="tertiary">
                {stanceReasonSentence(reason, t)}
              </Text>
            ))}
          </EvidenceGroup>

          <EvidenceGroup
            heading={t("explainability.panel.limitingHeading")}
            emptyLabel={t("explainability.panel.noneLimiting")}
          >
            {limitingFactors.map((reason, index) => (
              <Text key={index} as="p" color="tertiary">
                {stanceReasonSentence(reason, t)}
              </Text>
            ))}
          </EvidenceGroup>

          <EvidenceGroup
            heading={t("explainability.panel.missingHeading")}
            emptyLabel={t("explainability.panel.noneMissing")}
          >
            {missingEvidence.map((dimension) => (
              <Text key={dimension.dimension} as="p" color="tertiary">
                {coverageDimensionLabel(dimension.dimension, t)}
                {dimension.reasoning[0]
                  ? ` — ${coverageReasonLabel(dimension.dimension, dimension.reasoning[0], t)}`
                  : ""}
              </Text>
            ))}
          </EvidenceGroup>

          <EvidenceGroup
            heading={t("explainability.panel.confidenceHeading")}
            emptyLabel={t("explainability.panel.noneConfidenceDrivers")}
          >
            {confidenceDrivers.map((reason, index) => (
              <Text key={index} as="p" color="tertiary">
                {confidenceReasonSentence(reason, t)}
              </Text>
            ))}
          </EvidenceGroup>
        </Stack>
      </ExpandableDetail>
    </Stack>
  );
}

function EvidenceGroup({
  heading,
  emptyLabel,
  children,
}: {
  heading: string;
  emptyLabel: string;
  children: ReactNode[];
}) {
  return (
    <Stack gap="metadata">
      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
        {heading}
      </Text>
      {children.length > 0 ? children : <Text color="tertiary">{emptyLabel}</Text>}
    </Stack>
  );
}

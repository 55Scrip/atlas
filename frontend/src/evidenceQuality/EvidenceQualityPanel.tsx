import { Inline, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import {
  EVIDENCE_CONFLICT_STATUS_KEY,
  EVIDENCE_DOMINANCE_KEY,
  EVIDENCE_FRESHNESS_KEY,
  EVIDENCE_QUALITY_LEVEL_KEY,
  EVIDENCE_QUALITY_LEVEL_TONE,
} from "../status/statusTone";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { conflictSentence, evidenceWarningSentence, factQualitySentence, unsupportedFindingLabel } from "./describeEvidenceQuality";
import type { EvidenceQualityReportView } from "./evidenceQualityApi";

/**
 * Atlas Intelligence Sprint 4 (Evidence Quality & Conflict Resolution,
 * Deliverable 5). Answers "do I trust this evidence, and why" -- one
 * compact, always-visible summary (quality/freshness/consistency/
 * source-diversity badges plus real warning sentences), the full
 * per-fact/per-conflict/per-unsupported-finding detail behind one
 * `ExpandableDetail`, matching `ExplanationPanel`'s own "never
 * overwhelming" precedent exactly.
 */
export function EvidenceQualityPanel({ report, t }: { report: EvidenceQualityReportView; t: Translate }) {
  return (
    <Stack gap="metadata">
      <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
        <Text color="secondary" style={{ fontWeight: 600 }}>
          {t("evidenceQuality.panel.heading")}
        </Text>
      </Inline>

      <Inline gap="inter-section" wrap align="start">
        <Stack gap="metadata">
          <Text color="secondary" style={{ fontWeight: 600 }}>
            {t("evidenceQuality.panel.qualityLabel")}
          </Text>
          <StatusBadge label={t(EVIDENCE_QUALITY_LEVEL_KEY[report.quality])} tone={EVIDENCE_QUALITY_LEVEL_TONE[report.quality]} />
        </Stack>
        <Stack gap="metadata">
          <Text color="secondary" style={{ fontWeight: 600 }}>
            {t("evidenceQuality.panel.conflictStatusLabel")}
          </Text>
          <StatusBadge label={t(EVIDENCE_CONFLICT_STATUS_KEY[report.conflictStatus])} tone={report.conflictStatus === "conflicting" ? "critical" : "neutral"} />
        </Stack>
        <Stack gap="metadata">
          <Text color="secondary" style={{ fontWeight: 600 }}>
            {t("evidenceQuality.panel.dominanceLabel")}
          </Text>
          <StatusBadge label={t(EVIDENCE_DOMINANCE_KEY[report.dominance])} tone={report.dominance === "single_source" ? "caution" : "neutral"} />
        </Stack>
      </Inline>

      {report.warnings.length > 0 && (
        <Stack gap="metadata">
          {report.warnings.map((code, index) => (
            <Text key={index} as="p" color="tertiary">
              {evidenceWarningSentence(code, t)}
            </Text>
          ))}
        </Stack>
      )}

      <ExpandableDetail summaryLabel={t("evidenceQuality.panel.expandLabel")}>
        <Stack gap="inter-section">
          <Stack gap="metadata">
            <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
              {t("evidenceQuality.panel.factsHeading")}
            </Text>
            {report.facts.length > 0 ? (
              report.facts.map((fact) => (
                <Text key={fact.factKind} as="p" color="tertiary">
                  {factQualitySentence(fact, t)} — {t(EVIDENCE_FRESHNESS_KEY[fact.freshness])}
                </Text>
              ))
            ) : (
              <Text color="tertiary">{t("evidenceQuality.panel.noneFacts")}</Text>
            )}
          </Stack>

          <Stack gap="metadata">
            <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
              {t("evidenceQuality.panel.conflictsHeading")}
            </Text>
            {report.conflicts.length > 0 ? (
              report.conflicts.map((conflict, index) => (
                <Text key={index} as="p" color="tertiary">
                  {conflictSentence(conflict, t)}
                </Text>
              ))
            ) : (
              <Text color="tertiary">{t("evidenceQuality.panel.noneConflicts")}</Text>
            )}
          </Stack>

          <Stack gap="metadata">
            <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
              {t("evidenceQuality.panel.unsupportedHeading")}
            </Text>
            {report.unsupportedFindings.length > 0 ? (
              report.unsupportedFindings.map((finding, index) => (
                <Text key={index} as="p" color="tertiary">
                  {unsupportedFindingLabel(finding, t)}
                </Text>
              ))
            ) : (
              <Text color="tertiary">{t("evidenceQuality.panel.noneUnsupported")}</Text>
            )}
          </Stack>
        </Stack>
      </ExpandableDetail>
    </Stack>
  );
}

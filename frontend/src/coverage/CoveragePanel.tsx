import { Inline, Label, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import {
  ANALYSIS_COVERAGE_LEVEL_KEY,
  ANALYSIS_COVERAGE_TONE,
  COVERAGE_CONFIDENCE_KEY,
  COVERAGE_CONFIDENCE_TONE,
  DIMENSION_COVERAGE_TONE,
} from "../status/statusTone";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { confidenceReasonSentence, coverageDimensionLabel, coverageReasonLabel } from "./describeCoverage";
import type { CoverageAssessmentView } from "./coverageApi";

/**
 * Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine,
 * Deliverable 5). A compact panel, not a new large section -- two
 * badges (Overall Coverage, reused verbatim from the existing
 * `AnalysisCoverageLevel`; Overall Confidence, this Sprint's own new
 * qualitative signal), the real counted reasoning behind them, and two
 * short dimension lists. Dimensions this build of Atlas does not yet
 * evaluate for any company (`notApplicableDimensions`) are tucked
 * behind a collapsed note rather than padding either list -- showing
 * "Scenario Bull: not applicable" next to real per-company gaps would
 * blur "Atlas doesn't have your company's data" with "Atlas doesn't
 * build this kind of analysis yet," the exact false-precision this
 * engine exists to remove (see `atlas.alpha.coverage.models
 * .DimensionCoverageLevel`'s own docstring).
 */
export function CoveragePanel({ coverage, t }: { coverage: CoverageAssessmentView; t: Translate }) {
  const available = coverage.dimensions.filter((d) => d.level === "available" || d.level === "partially_available");
  const missing = coverage.dimensions.filter(
    (d) => d.level === "unavailable" || d.level === "insufficient_evidence",
  );

  return (
    <Stack gap="intra-section">
      <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
        <Label>{t("coverage.panel.heading")}</Label>
      </Inline>
      <Inline gap="inter-section" wrap align="start">
        <Stack gap="metadata">
          <Text color="secondary" style={{ fontWeight: 600 }}>
            {t("coverage.panel.overallCoverageLabel")}
          </Text>
          <StatusBadge
            label={t(ANALYSIS_COVERAGE_LEVEL_KEY[coverage.overallCoverage])}
            tone={ANALYSIS_COVERAGE_TONE[coverage.overallCoverage]}
          />
        </Stack>
        <Stack gap="metadata">
          <Text color="secondary" style={{ fontWeight: 600 }}>
            {t("coverage.panel.confidenceLabel")}
          </Text>
          <StatusBadge
            label={t(COVERAGE_CONFIDENCE_KEY[coverage.overallConfidence])}
            tone={COVERAGE_CONFIDENCE_TONE[coverage.overallConfidence]}
          />
        </Stack>
      </Inline>

      {coverage.reasoning.length > 0 && (
        <Stack gap="metadata">
          {coverage.reasoning.map((reason, index) => (
            <Text key={index} as="p" color="tertiary">
              {confidenceReasonSentence(reason, t)}
            </Text>
          ))}
        </Stack>
      )}

      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("coverage.panel.availableHeading")}
        </Text>
        {available.length === 0 ? (
          <Text color="tertiary">{t("coverage.panel.noneAvailable")}</Text>
        ) : (
          <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
            {available.map((d) => (
              <li key={d.dimension}>
                <Inline gap="metadata" align="center">
                  <Text as="span">{coverageDimensionLabel(d.dimension, t)}</Text>
                  {d.level === "partially_available" && (
                    <StatusBadge
                      label={t("coverage.dimension.partiallyAvailable")}
                      tone={DIMENSION_COVERAGE_TONE.partially_available}
                    />
                  )}
                </Inline>
              </li>
            ))}
          </ul>
        )}
      </Stack>

      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("coverage.panel.missingHeading")}
        </Text>
        {missing.length === 0 ? (
          <Text color="tertiary">{t("coverage.panel.noneMissing")}</Text>
        ) : (
          <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
            {missing.map((d) => (
              <li key={d.dimension}>
                <Text as="span" color="secondary">
                  {coverageDimensionLabel(d.dimension, t)}
                  {d.reasoning.length > 0
                    ? ` — ${d.reasoning.map((r) => coverageReasonLabel(d.dimension, r, t)).join(", ")}`
                    : ""}
                </Text>
              </li>
            ))}
          </ul>
        )}
      </Stack>

      {coverage.notApplicableDimensions.length > 0 && (
        <ExpandableDetail
          summaryLabel={t(
            coverage.notApplicableDimensions.length === 1
              ? "coverage.panel.notApplicableExpandLabelOne"
              : "coverage.panel.notApplicableExpandLabelOther",
            { count: coverage.notApplicableDimensions.length },
          )}
        >
          <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
            {coverage.notApplicableDimensions.map((dimension) => (
              <li key={dimension}>
                <Text as="span" color="tertiary">
                  {coverageDimensionLabel(dimension, t)}
                </Text>
              </li>
            ))}
          </ul>
        </ExpandableDetail>
      )}
    </Stack>
  );
}

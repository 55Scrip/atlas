import { Divider, Heading, Inline, Stack, Text } from "../foundation";
import { useTranslation } from "../i18n";
import { FIT_TREND_KEY } from "../status/statusTone";
import { FitBadge } from "./FitBadge";
import { FitDimensionRow } from "./FitDimensionRow";
import { groupFitDimensions } from "./groupFitDimensions";
import type { PortfolioFitAssessmentView } from "./portfolioFitApi";

/**
 * Deliverable 8 (Product Sprint 4) -- Investment Case's own "Portfolio
 * Fit" section. Answers, in order: why it fits (dimensions rated
 * Good/Excellent), what argues against it (dimensions rated Weak/Poor),
 * how the position affects the portfolio (Allocation Fit + Cash Impact,
 * already dimensions here, not re-explained separately), and what
 * would improve or worsen the fit (`trend`, sourced from the existing
 * Change Intelligence signal -- this component computes no history of
 * its own). Every sentence rendered here is `assessment`'s own
 * `reasoning`/`overallReasoning` text, verbatim -- this component adds
 * no generated prose.
 *
 * The favorable/unfavorable/other grouping and the per-dimension row
 * (`groupFitDimensions`/`FitDimensionRow`) are shared with Discovery's
 * `DiscoveryCandidateCard` (Product Sprint 5) -- extracted here rather
 * than duplicated, per that sprint's own "no duplicated logic" rule.
 */
export function PortfolioFitSection({ assessment }: { assessment: PortfolioFitAssessmentView | null }) {
  const { t } = useTranslation();

  if (assessment === null) {
    return (
      <Stack gap="metadata">
        <Heading level={3}>{t("portfolioFit.section.heading")}</Heading>
        <Text color="tertiary">{t("portfolioFit.section.unavailable")}</Text>
      </Stack>
    );
  }

  const { favorable, unfavorable, other } = groupFitDimensions(assessment.dimensions);

  return (
    <Stack gap="metadata">
      <Heading level={3}>{t("portfolioFit.section.heading")}</Heading>

      <Inline gap="row" align="center">
        <FitBadge rating={assessment.overall} />
        {assessment.trend !== "unavailable" && (
          <Text color="tertiary" as="span">
            {t(FIT_TREND_KEY[assessment.trend])}
          </Text>
        )}
      </Inline>
      {assessment.overallReasoning.map((line, index) => (
        <Text key={index} color="secondary" as="p">
          {line}
        </Text>
      ))}

      {favorable.length > 0 && (
        <Stack gap="metadata">
          <Text as="p" style={{ fontWeight: 600 }}>
            {t("portfolioFit.section.whyItFits")}
          </Text>
          {favorable.map((dimension) => (
            <FitDimensionRow key={dimension.kind} dimension={dimension} />
          ))}
        </Stack>
      )}

      {unfavorable.length > 0 && (
        <Stack gap="metadata">
          <Text as="p" style={{ fontWeight: 600 }}>
            {t("portfolioFit.section.whatArguesAgainst")}
          </Text>
          {unfavorable.map((dimension) => (
            <FitDimensionRow key={dimension.kind} dimension={dimension} />
          ))}
        </Stack>
      )}

      {other.length > 0 && (
        <Stack gap="metadata">
          <Text as="p" style={{ fontWeight: 600 }}>
            {t("portfolioFit.section.other")}
          </Text>
          {other.map((dimension) => (
            <FitDimensionRow key={dimension.kind} dimension={dimension} />
          ))}
        </Stack>
      )}

      {assessment.dataGaps.length > 0 && (
        <>
          <Divider tone="hairline" />
          <Stack gap="metadata">
            <Text color="tertiary" as="p">
              {t("portfolioFit.section.dataGapsHeading")}
            </Text>
            {assessment.dataGaps.map((gap, index) => (
              <Text key={index} color="tertiary" as="p">
                {gap}
              </Text>
            ))}
          </Stack>
        </>
      )}
    </Stack>
  );
}

import { Divider, Heading, Inline, Stack, Text } from "../foundation";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { useTranslation } from "../i18n";
import { FIT_TREND_KEY } from "../status/statusTone";
import { describeFitVerdict } from "./describeFitVerdict";
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
 * Convergence Sprint 1 (Investment Case Compression): the default view
 * is now the rating badge, the trend and the one-sentence verdict --
 * the distilled result and its implication. The per-dimension rows
 * (why it fits / what argues against it / other) and the data-gap list
 * move behind one disclosure: on a real Case they ran to roughly a full
 * screen of allocation/risk/business/valuation/contribution/cash rows,
 * ahead of the page's own Atlas conclusion. Nothing is dropped and no
 * rating is recomputed -- every row remains one click away, rendered by
 * the same `FitDimensionRow` from the same `assessment`.
 *
 * The favorable/unfavorable/other grouping and the per-dimension row
 * (`groupFitDimensions`/`FitDimensionRow`) are shared with Discovery's
 * `DiscoveryCandidateCard` (Product Sprint 5) -- extracted here rather
 * than duplicated, per that sprint's own "no duplicated logic" rule.
 */
export function PortfolioFitSection({
  assessment,
  showHeading = true,
}: {
  assessment: PortfolioFitAssessmentView | null;
  /** Product Convergence Sprint 1 (Investment Case Hierarchy): the
   * Investment Case now renders this inside a Portfolio Fit chapter
   * whose own heading is the same word, so it passes `false` and keeps
   * one title. Defaults to the previous behaviour for every other
   * caller. */
  showHeading?: boolean;
}) {
  const { t } = useTranslation();

  if (assessment === null) {
    return (
      <Stack gap="metadata">
        {showHeading && <Heading level={3}>{t("portfolioFit.section.heading")}</Heading>}
        <Text color="tertiary">{t("portfolioFit.section.unavailable")}</Text>
      </Stack>
    );
  }

  const verdictText = describeFitVerdict(assessment, t);
  /* Position Editor v1 / semantic cleanup. Of the five dimensions this
     engine produces, only `allocation` asks a portfolio question --
     how big this position is against the portfolio's own
     concentration. `business`, `valuation` and `risk` are properties of
     the company, and `cash_impact` is a property of the portfolio that
     is identical for every holding.
     
     That matters because the overall verdict is a vote across all five,
     with a Poor Risk Fit acting as a hard gate -- so "Weak Fit" was
     often a restatement of "expensive, with valuation risk", which the
     Case already says at length in its own Valuation and Risk chapters.
     A great company at a great price can still fit a portfolio badly,
     and this chapter has to be able to say so.
     
     So the chapter now leads with what Atlas can actually assess about
     portfolio fit, and states plainly what it cannot yet. The
     case-derived dimensions are not deleted -- they are real, and they
     stay one disclosure down under their own honest heading -- but they
     no longer masquerade as the portfolio verdict. */
  const allocation = assessment.dimensions.find((d) => d.kind === "allocation");
  /* Allocation is promoted to the primary surface above, so it is not
     repeated in the grouped listing -- the same sentence appearing twice
     on one screen reads as two findings. `cash_impact` stays in the
     listing: it is portfolio-level, but it is identical for every
     holding, so it says nothing about *this* position's fit. */
  const { favorable, unfavorable, other } = groupFitDimensions(
    assessment.dimensions.filter((d) => d.kind !== "allocation"),
  );

  return (
    <Stack gap="metadata">
      {showHeading && <Heading level={3}>{t("portfolioFit.section.heading")}</Heading>}

      {/* What Atlas can assess today. */}
      {allocation && allocation.rating !== "unavailable" ? (
        <>
          <Inline gap="row" align="center">
            <FitBadge rating={allocation.rating} />
            <Text color="tertiary" as="span">
              {t("portfolioFit.section.positionSizeOnly")}
            </Text>
          </Inline>
          {allocation.reasoning.map((line) => (
            <Text color="secondary" as="p" key={line}>
              {line}
            </Text>
          ))}
        </>
      ) : (
        <Text color="secondary" as="p">
          {t("portfolioFit.section.noPortfolioRelativeAssessment")}
        </Text>
      )}

      {/* And what it cannot. Stated every time, not only when something
          is missing: the absence is a standing property of Atlas today,
          not a gap in this particular holding's data. */}
      <Text color="tertiary" as="p">
        {t("portfolioFit.section.notYetAssessed")}
      </Text>

      {(favorable.length > 0 || unfavorable.length > 0 || other.length > 0 || assessment.dataGaps.length > 0) && (
        <ExpandableDetail summaryLabel={t("portfolioFit.section.allDimensions")}>
          <Stack gap="metadata">
            {/* The engine's own overall verdict and its case-derived
                dimensions, kept in full but named for what they are.
                Nothing is deleted; it simply no longer reads as the
                portfolio answer. */}
            <Inline gap="row" align="center">
              <FitBadge rating={assessment.overall} />
              <Text color="tertiary" as="span">
                {t("portfolioFit.section.overallIncludesCaseQuality")}
              </Text>
              {assessment.trend !== "unavailable" && (
                <Text color="tertiary" as="span">
                  {t(FIT_TREND_KEY[assessment.trend])}
                </Text>
              )}
            </Inline>
            {verdictText && (
              <Text color="secondary" as="p">
                {verdictText}
              </Text>
            )}

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
        </ExpandableDetail>
      )}

    </Stack>
  );
}

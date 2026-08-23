import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { CATEGORY_KEY, CATEGORY_TONE, SOURCE_KEY, portfolioDecisionReasonLabel } from "./describePortfolioDecision";
import type { PortfolioDecisionReasonView, PortfolioDecisionView } from "./portfolioDecisionApi";

/**
 * Investment Case Integration (Atlas Decision Layer Sprint 8,
 * Deliverable 7). What this decision means for the portfolio --
 * category, primary limitation, capital competition, and current
 * portfolio limitations, progressively disclosed: the category and
 * primary limitation always visible, the full breakdown one click
 * away. Every reason renders through `portfolioDecisionReasonLabel`
 * (never a raw technical code as prose) and carries its own `source`
 * tag, so a reader can always see which real Atlas layer surfaced it.
 */
export function PortfolioDecisionSection({
  decision,
  t,
}: {
  decision: PortfolioDecisionView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const competingCount = decision.capitalCompetition.competingAlternatives.length;
  const hasMore = decision.supportingReasons.length > 0 || decision.limitingReasons.length > 0 || competingCount > 0;

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Heading level={3}>{t("portfolioDecision.section.heading")}</Heading>
        <StatusBadge label={t(CATEGORY_KEY[decision.category])} tone={CATEGORY_TONE[decision.category]} />
        {decision.primaryLimitingReason ? (
          <Text color="secondary">
            {t("portfolioDecision.section.primaryLimiting", { fact: portfolioDecisionReasonLabel(decision.primaryLimitingReason, t) })}
          </Text>
        ) : (
          <Text color="tertiary">{t("portfolioDecision.section.noLimiting")}</Text>
        )}
        {competingCount > 0 && (
          <Text color="secondary">
            {t(
              competingCount === 1
                ? "portfolioDecision.section.capitalCompetitionSummaryOne"
                : "portfolioDecision.section.capitalCompetitionSummaryOther",
              { count: competingCount },
            )}
          </Text>
        )}
        {hasMore && (
          <ExpandableDetail summaryLabel={t("portfolioDecision.section.expandLabel")}>
            <Stack gap="intra-section">
              <ReasonList heading={t("portfolioDecision.section.supportingHeading")} reasons={decision.supportingReasons} t={t} />
              <ReasonList heading={t("portfolioDecision.section.limitingHeading")} reasons={decision.limitingReasons} t={t} />
              {competingCount > 0 && (
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("portfolioDecision.section.competitionHeading")}
                  </Text>
                  {decision.capitalCompetition.competingAlternatives.map((alt, index) => (
                    <Text key={`${alt.kind}:${alt.caseId ?? index}`} color="secondary">
                      {alt.ticker ?? t("portfolioDecision.section.unnamedCompetitor")}
                    </Text>
                  ))}
                </Stack>
              )}
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}

function ReasonList({
  heading,
  reasons,
  t,
}: {
  heading: string;
  reasons: PortfolioDecisionReasonView[];
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (reasons.length === 0) return null;
  return (
    <Stack gap="metadata">
      <Text as="span" style={{ fontWeight: 600 }}>
        {heading}
      </Text>
      {reasons.map((reason, index) => (
        <Inline key={`${reason.source}:${reason.reference.id}:${index}`} gap="row" align="center" wrap>
          <Text color="secondary">{portfolioDecisionReasonLabel(reason, t)}</Text>
          <Text color="tertiary" as="span">
            {t(SOURCE_KEY[reason.source])}
          </Text>
        </Inline>
      ))}
    </Stack>
  );
}

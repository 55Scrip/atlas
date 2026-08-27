import { Button, Divider, Heading, Inline, Link, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { FitBadge } from "../portfolioFit/FitBadge";
import { FitDimensionRow } from "../portfolioFit/FitDimensionRow";
import { groupFitDimensions } from "../portfolioFit/groupFitDimensions";
import type { PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import { StanceBadge } from "../stance/StanceBadge";
import type { StanceLevel } from "../stance/stanceApi";
import { TickerExplanationDetail } from "../explainability/TickerExplanationDetail";
import { TickerEvidenceQualityDetail } from "../evidenceQuality/TickerEvidenceQualityDetail";
import { TickerEvidenceTimelineDetail } from "../evidenceTimeline/TickerEvidenceTimelineDetail";

/**
 * Discover Doctrine (2026-08-27) -- three variants, one component:
 *
 * `"primary"` -- a Highest-opportunity card (Phase 2): ticker, Stance +
 * Fit verdict, one sentence, Open Investment Case as the one primary
 * action, Compare and Remove from Watchlist available but visually
 * secondary/tertiary (Phase 7). No expandables, no raw event headline,
 * no dimension breakdown -- everything below the one sentence belongs
 * to Investment Case, not here (Phase 4/10/11).
 *
 * `"secondary"` -- a Worth-reviewing / Everything-else row (Phase 3):
 * ticker, rating, one-line verdict, Open Investment Case. Nothing more
 * -- no Surface/card chrome, deliberately a plain scannable row so the
 * visual weight difference from a primary card is immediate, not
 * something a reader has to notice by counting elements.
 *
 * `"full"` -- Candidate Detail's own full-page rendering, unchanged
 * from before except the raw Agenda headline is gone (Phase 5) --
 * still the complete dimension breakdown and evidence disclosures,
 * since a user reaching this page has already opted into depth.
 */
export function DiscoveryCandidateCard({
  ticker,
  displayName,
  reasonKey,
  assessment,
  stance = null,
  variant,
  isOnWatchlist,
  isHolding,
  onOpenCase,
  onAddToWatchlist,
  onRemoveFromWatchlist,
  onCompare,
}: {
  ticker: string;
  displayName?: string | null;
  /** Only rendered for `variant="full"` -- Discover's own primary/
   * secondary cards are exclusively Watchlist candidates by
   * construction, so a generic "On your Watchlist" line would only
   * repeat what the section heading above it already says. */
  reasonKey?: TranslationKey;
  assessment: PortfolioFitAssessmentView | null;
  stance?: StanceLevel | null;
  variant: "primary" | "secondary" | "full";
  /** Only meaningful for `variant="full"` -- `resolve_case_id_for_
   * ticker` can resolve a real, evaluable Case through a path neither
   * boolean covers on its own, so `assessment !== null` is checked
   * first; these two only extend `canEvaluate` further for a ticker
   * that has a real Case but no Fit assessment yet. Discover's own
   * primary/secondary cards never need either -- every candidate
   * reaching them is already a Watchlist entry, which always has a
   * real `caseId` by construction. */
  isOnWatchlist?: boolean;
  isHolding?: boolean;
  onOpenCase: () => void;
  onAddToWatchlist?: (() => void) | undefined;
  onRemoveFromWatchlist?: (() => void) | undefined;
  onCompare?: (() => void) | undefined;
}) {
  const { t } = useTranslation();
  const canEvaluate = assessment !== null || isOnWatchlist === true || isHolding === true;
  const verdictSentence = assessment !== null && assessment.overallReasoning.length > 0 ? assessment.overallReasoning[0] : null;

  if (variant === "secondary") {
    return (
      <Inline gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
        <Inline gap="row" align="baseline" wrap>
          <Text as="span" style={{ fontWeight: 600 }}>
            {ticker}
          </Text>
          {assessment !== null ? (
            <FitBadge rating={assessment.overall} />
          ) : (
            <Text color="tertiary" as="span">
              {t(canEvaluate ? "discovery.card.fitPending" : "discovery.card.noCaseYet")}
            </Text>
          )}
          {verdictSentence && (
            <Text color="tertiary" as="span">
              {verdictSentence}
            </Text>
          )}
        </Inline>
        <Button variant="tertiary" onClick={onOpenCase}>
          {t("discovery.card.openCase")}
        </Button>
      </Inline>
    );
  }

  if (variant === "primary") {
    return (
      <Surface tier="primary">
        <Stack gap="metadata">
          <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
            <Heading level={4}>
              {ticker}
              {displayName ? <Text as="span" color="tertiary"> — {displayName}</Text> : null}
            </Heading>
            <Inline gap="metadata" align="center">
              {stance !== null && <StanceBadge level={stance} />}
              {assessment !== null && <FitBadge rating={assessment.overall} />}
            </Inline>
          </Inline>
          {verdictSentence && (
            <Text color="secondary" as="p">
              {verdictSentence}
            </Text>
          )}
          <Inline gap="row" align="center" wrap>
            <Button variant="primary" onClick={onOpenCase}>
              {t("discovery.card.openCase")}
            </Button>
            {onCompare && (
              <Button variant="tertiary" onClick={onCompare}>
                {t("discovery.card.compare")}
              </Button>
            )}
            {onRemoveFromWatchlist && (
              <Link
                href="#"
                onClick={(event) => {
                  event.preventDefault();
                  onRemoveFromWatchlist();
                }}
              >
                {t("discovery.card.removeFromWatchlist")}
              </Link>
            )}
          </Inline>
        </Stack>
      </Surface>
    );
  }

  // variant === "full" -- Candidate Detail's own complete rendering,
  // unchanged apart from the removed raw Agenda headline (Phase 5).
  const grouped = assessment !== null ? groupFitDimensions(assessment.dimensions) : null;

  return (
    <Surface tier="elevated">
      <Stack gap="metadata">
        <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
          <Stack gap="metadata">
            <Heading level={2}>
              {ticker}
              {displayName ? <Text as="span" color="tertiary"> — {displayName}</Text> : null}
            </Heading>
            {reasonKey && (
              <Text color="tertiary" as="p">
                {t(reasonKey)}
              </Text>
            )}
          </Stack>
          {assessment !== null && (
            <Inline gap="metadata" align="center">
              {stance !== null && <StanceBadge level={stance} />}
              <FitBadge rating={assessment.overall} />
            </Inline>
          )}
        </Inline>

        {assessment === null && (
          <Text color="tertiary" as="p">
            {t(canEvaluate ? "discovery.card.fitPending" : "discovery.card.noCaseYet")}
          </Text>
        )}

        {verdictSentence && (
          <Text color="secondary" as="p">
            {verdictSentence}
          </Text>
        )}

        {assessment !== null && (
          <TickerExplanationDetail ticker={ticker} summaryLabel={t("explainability.discovery.expandLabel")} t={t} />
        )}
        {assessment !== null && (
          <TickerEvidenceQualityDetail ticker={ticker} summaryLabel={t("evidenceQuality.discovery.expandLabel")} t={t} />
        )}
        {assessment !== null && (
          <TickerEvidenceTimelineDetail ticker={ticker} summaryLabel={t("evidenceTimeline.discovery.expandLabel")} t={t} />
        )}

        {grouped !== null && (
          <>
            {grouped.favorable.length > 0 && (
              <Stack gap="metadata">
                <Text as="p" style={{ fontWeight: 600 }}>
                  {t("portfolioFit.section.whyItFits")}
                </Text>
                {grouped.favorable.map((dimension) => (
                  <FitDimensionRow key={dimension.kind} dimension={dimension} />
                ))}
              </Stack>
            )}
            {grouped.unfavorable.length > 0 && (
              <Stack gap="metadata">
                <Text as="p" style={{ fontWeight: 600 }}>
                  {t("portfolioFit.section.whatArguesAgainst")}
                </Text>
                {grouped.unfavorable.map((dimension) => (
                  <FitDimensionRow key={dimension.kind} dimension={dimension} />
                ))}
              </Stack>
            )}
            {grouped.other.length > 0 && (
              <Stack gap="metadata">
                <Text as="p" style={{ fontWeight: 600 }}>
                  {t("portfolioFit.section.other")}
                </Text>
                {grouped.other.map((dimension) => (
                  <FitDimensionRow key={dimension.kind} dimension={dimension} />
                ))}
              </Stack>
            )}
            {assessment !== null && assessment.dataGaps.length > 0 && (
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
          </>
        )}

        <Inline gap="row" align="center" wrap>
          {canEvaluate ? (
            <Button variant="primary" onClick={onOpenCase}>
              {t("discovery.card.openCase")}
            </Button>
          ) : (
            onAddToWatchlist && (
              <Button variant="primary" onClick={onAddToWatchlist}>
                {t("discovery.card.addToWatchlistToEvaluate")}
              </Button>
            )
          )}
          {onRemoveFromWatchlist && (
            <Button variant="tertiary" onClick={onRemoveFromWatchlist}>
              {t("discovery.card.removeFromWatchlist")}
            </Button>
          )}
          {canEvaluate && onCompare && (
            <Button variant="tertiary" onClick={onCompare}>
              {t("discovery.card.compare")}
            </Button>
          )}
        </Inline>
      </Stack>
    </Surface>
  );
}

import { Button, Divider, Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { FitBadge } from "../portfolioFit/FitBadge";
import { FitDimensionRow } from "../portfolioFit/FitDimensionRow";
import { groupFitDimensions } from "../portfolioFit/groupFitDimensions";
import type { FitRating, PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import { StanceBadge } from "../stance/StanceBadge";
import type { StanceLevel } from "../stance/stanceApi";
import {
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_STATEMENT_KEY,
  DECISION_SUPPORT_TONE,
  type DecisionSupportLevel,
} from "../status/statusTone";
import { TickerExplanationDetail } from "../explainability/TickerExplanationDetail";
import { TickerEvidenceQualityDetail } from "../evidenceQuality/TickerEvidenceQualityDetail";
import { TickerEvidenceTimelineDetail } from "../evidenceTimeline/TickerEvidenceTimelineDetail";

/**
 * Discover Doctrine (2026-08-27) -- three variants, one component:
 *
 * `"primary"` -- a Highest-opportunity card (Phase 2): ticker, Decision
 * Support + Stance + Fit verdict, one sentence, Open Investment Case as
 * the one primary action, Compare available but visually tertiary
 * (Phase 7). No expandables, no raw event headline, no dimension
 * breakdown -- everything below the one sentence belongs to Investment
 * Case, not here (Phase 4/10/11).
 *
 * Sprint 4C compacts it to three lines and gives it the one sentence
 * it had been missing since Sprint 4B removed the backend's
 * pre-rendered English Fit prose: the Decision Support *statement*,
 * looked up locally from the canonical level the candidate already
 * carries. That is "why Atlas shows this" said in Atlas's own
 * vocabulary, not a new claim -- and "Remove from Watchlist" is gone,
 * because the candidate universe excludes actively watched companies
 * by construction, so on a Discovery card that control could only ever
 * be an action that silently did nothing.
 *
 * `"secondary"` -- a Worth-reviewing / Everything-else row (Phase 3):
 * ticker, rating, one-line verdict, Open Investment Case. Nothing more
 * -- no Surface/card chrome, deliberately a plain scannable row so the
 * visual weight difference from a primary card is immediate, not
 * something a reader has to notice by counting elements. Sprint 4C
 * renders the two lower tiers as `DiscoveryCandidateTable` instead --
 * a dense row could carry one signal, and fourteen of them made a
 * list rather than a comparison -- so this variant currently has no
 * caller. It is kept, still covered, as the one lightweight rendering
 * for a context that wants a candidate without a table around it;
 * nothing in the product renders it today.
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
  fit,
  assessment = null,
  stance = null,
  decisionSupport = null,
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
  /** Only rendered for `variant="full"`. Discovery's own ranked tiers
   * never pass one: since Sprint 4B they are the independent candidate
   * universe -- companies the investor neither owns nor watches -- so
   * a membership line there would state something that is true of
   * every row by construction. */
  reasonKey?: TranslationKey;
  /** Sprint 4B: the canonical Fit *rating*, not the whole assessment.
   * The card only ever needed `.overall` -- and the assessment's
   * `overallReasoning[0]`, a pre-rendered English sentence, was
   * backend prose rendered verbatim into a Swedish UI. It is gone;
   * the badge already says what the rating is. */
  fit: FitRating | null;
  /** Only the `"full"` variant needs the whole assessment, for its
   * per-dimension breakdown. The compact variants read `fit` alone. */
  assessment?: PortfolioFitAssessmentView | null;
  stance?: StanceLevel | null;
  /** Sprint 4C, `"primary"` only. The candidate's canonical
   * `DecisionSupportLevel`, straight off `DiscoveryCandidateView` --
   * rendered as the same badge and the same sentence Portfolio,
   * Watchlist and Investment Case already show for that level, never a
   * Discovery-specific rewording of it. */
  decisionSupport?: DecisionSupportLevel | null;
  variant: "primary" | "secondary" | "full";
  /** Only meaningful for `variant="full"` -- `resolve_case_id_for_
   * ticker` can resolve a real, evaluable Case through a path neither
   * boolean covers on its own, so `assessment !== null` is checked
   * first; these two only extend `canEvaluate` further for a ticker
   * that has a real Case but no Fit assessment yet. Discovery's own
   * ranked tiers never need either -- every candidate reaching them
   * arrives from the backend universe with a real bound `caseId`. */
  isOnWatchlist?: boolean;
  isHolding?: boolean;
  onOpenCase: () => void;
  onAddToWatchlist?: (() => void) | undefined;
  onRemoveFromWatchlist?: (() => void) | undefined;
  onCompare?: (() => void) | undefined;
}) {
  const { t } = useTranslation();
  const canEvaluate = fit !== null || isOnWatchlist === true || isHolding === true;

  if (variant === "secondary") {
    return (
      <Inline gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
        <Inline gap="row" align="baseline" wrap>
          <Text as="span" style={{ fontWeight: 600 }}>
            {ticker}
          </Text>
          {fit !== null ? (
            <FitBadge rating={fit} />
          ) : (
            <Text color="tertiary" as="span">
              {t(canEvaluate ? "discovery.card.fitPending" : "discovery.card.noCaseYet")}
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
          <Inline gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
            <Heading level={4}>
              {ticker}
              {displayName ? <Text as="span" color="tertiary"> — {displayName}</Text> : null}
            </Heading>
            <Inline gap="metadata" align="center" wrap>
              {decisionSupport !== null && (
                <StatusBadge
                  label={t(DECISION_SUPPORT_BADGE_KEY[decisionSupport])}
                  tone={DECISION_SUPPORT_TONE[decisionSupport]}
                  weight="strong"
                />
              )}
              {stance !== null && <StanceBadge level={stance} />}
              {fit !== null && <FitBadge rating={fit} />}
            </Inline>
          </Inline>
          {decisionSupport !== null && (
            <Text color="secondary" as="p">
              {t(DECISION_SUPPORT_STATEMENT_KEY[decisionSupport])}
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

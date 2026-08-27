import { Button, Divider, Heading, Inline, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { FitBadge } from "../portfolioFit/FitBadge";
import { FitDimensionRow } from "../portfolioFit/FitDimensionRow";
import { groupFitDimensions } from "../portfolioFit/groupFitDimensions";
import type { PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import { FIT_RATING_TONE, STANCE_LEVEL_TONE } from "../status/statusTone";
import { StanceBadge } from "../stance/StanceBadge";
import type { StanceView } from "../stance/stanceApi";
import { TickerExplanationDetail } from "../explainability/TickerExplanationDetail";
import { TickerEvidenceQualityDetail } from "../evidenceQuality/TickerEvidenceQualityDetail";
import { TickerEvidenceTimelineDetail } from "../evidenceTimeline/TickerEvidenceTimelineDetail";

/**
 * Deliverable 4 -- the one reusable Discovery candidate presentation,
 * used both in the compact list on `/discovery` and the full detail
 * view on `/discovery/candidate/:ticker`. Answers, in order: what is
 * this company, why is Atlas showing it, how does it fit the portfolio,
 * strongest positives, strongest limitations, what to inspect next.
 *
 * `assessment === null` means no Portfolio Fit exists yet for this
 * ticker (no Investment Case, or no Watchlist/Portfolio link resolves
 * it) -- rendered as a real, disclosed gap (Deliverable 10's own
 * "Build the Investment Case before Atlas can evaluate Portfolio Fit"),
 * never a fabricated rating.
 *
 * Product Sprint 9 (Discovery Excellence, Deliverable 3 -- Why Atlas
 * Found This): `agendaHeadline`, when present, is the real, already-
 * computed reason the shared Daily Brief Agenda (`group: "watchlist"`)
 * flagged this exact ticker -- an improving/declining Fit trend, a
 * strengthened/weakened thesis (Change Intelligence), a satisfied Case
 * Condition, or a challenged Assumption. It replaces the generic
 * membership-category text (`reasonKey`, "On your Watchlist") as the
 * card's headline reason whenever a real, specific one exists; the
 * generic category always still renders underneath, since "why you're
 * seeing this at all" (Watchlist/Portfolio/search) and "why it matters
 * right now" (the Agenda signal) are two different, both-real facts,
 * never collapsed into one. Never a synthesized explanation -- if no
 * Agenda item exists for this ticker, only the generic category shows,
 * honestly.
 */
/** Atlas UX Phase 7B, Phase 3 -- Stance and Portfolio Fit are two real,
 * independently-computed engines (Stance folds in thesis change/risk
 * signals Fit's own dimension math doesn't weigh the same way), so they
 * can legitimately disagree -- confirmed live, "Red flag found" next to
 * "Good Fit" for the same real candidate. Shown with no explanation,
 * that reads as a contradiction rather than two real, different
 * questions answered honestly. This bridging line only renders when the
 * two badges' own tones genuinely oppose (one positive, one critical) --
 * never for a merely different-but-compatible pairing (e.g. neutral
 * Stance beside a Good Fit), so it never manufactures tension that
 * isn't really there. */
function stanceFitTensionKey(stance: StanceView | null, assessment: PortfolioFitAssessmentView | null): TranslationKey | null {
  if (stance === null || assessment === null) return null;
  const stanceTone = STANCE_LEVEL_TONE[stance.level];
  const fitTone = FIT_RATING_TONE[assessment.overall];
  if (stanceTone === "critical" && fitTone === "positive") return "discovery.card.tension.stanceNegativeFitPositive";
  if (stanceTone === "positive" && fitTone === "critical") return "discovery.card.tension.stancePositiveFitNegative";
  return null;
}

/** The generic "no trade size available, so concentration reads as the
 * default favorable fact" line (`atlas/alpha/portfolio_fit/engine.py`'s
 * own `_allocation_fit` for any non-held candidate) repeats near-
 * verbatim across almost every card, since it is the allocation
 * dimension's default reasoning whenever no real position size exists
 * yet to evaluate -- not a real differentiator between candidates.
 * Filtered out of the short compact-variant preview only; the full
 * detail view (`variant="full"`) still shows every real dimension,
 * including this one, as part of a complete breakdown. */
const GENERIC_ALLOCATION_REASONING_PREFIX = "No trade size is available";
function isGenericAllocationReasoning(reasoning: string | undefined): boolean {
  return reasoning !== undefined && reasoning.startsWith(GENERIC_ALLOCATION_REASONING_PREFIX);
}

export function DiscoveryCandidateCard({
  ticker,
  displayName,
  reasonKey,
  agendaHeadline = null,
  assessment,
  stance = null,
  isOnWatchlist,
  isHolding,
  variant = "compact",
  onOpenCase,
  onAddToWatchlist,
  onRemoveFromWatchlist,
  onCompare,
}: {
  ticker: string;
  displayName?: string | null;
  reasonKey: TranslationKey;
  agendaHeadline?: string | null;
  assessment: PortfolioFitAssessmentView | null;
  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 7) -- `null` when no `StanceService`
   * result exists for this ticker (mirrors `assessment`'s own `null`
   * case). Rendered as the leftmost, most prominent badge: this is the
   * one synthesized answer to "what should I do now," Fit/Coverage
   * remain the supporting detail beside it. Never stronger than the
   * underlying evidence -- see `StanceBadge`'s own docstring for why
   * `increase`/`reduce` never read as trade-size advice. */
  stance?: StanceView | null;
  isOnWatchlist: boolean;
  isHolding: boolean;
  variant?: "compact" | "full";
  onOpenCase: () => void;
  onAddToWatchlist?: (() => void) | undefined;
  onRemoveFromWatchlist?: (() => void) | undefined;
  onCompare?: (() => void) | undefined;
}) {
  const { t } = useTranslation();
  const grouped = assessment !== null ? groupFitDimensions(assessment.dimensions) : null;
  // Live-verification finding (Deliverable 14): `isOnWatchlist`/
  // `isHolding` reflect *current* Portfolio/Watchlist membership, but
  // `resolve_case_id_for_ticker` (and therefore `assessment`) can
  // resolve a real, evaluable Case through a path neither boolean
  // covers (e.g. a ticker previously watchlisted then removed, whose
  // Case still exists). `assessment !== null` is the authoritative
  // signal Atlas can actually show a result for -- checked first,
  // never contradicted by the two narrower membership flags.
  const canEvaluate = assessment !== null || isOnWatchlist || isHolding;

  return (
    <Surface tier={variant === "full" ? "elevated" : "primary"}>
      <Stack gap="metadata">
        <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
          <Stack gap="metadata">
            <Heading level={variant === "full" ? 2 : 4}>
              {ticker}
              {displayName ? <Text as="span" color="tertiary"> — {displayName}</Text> : null}
            </Heading>
            {agendaHeadline && (
              <Text as="p" style={{ fontWeight: 600 }}>
                {agendaHeadline}
              </Text>
            )}
            <Text color="tertiary" as="p">
              {t(reasonKey)}
            </Text>
          </Stack>
          {assessment !== null && (
            <Inline gap="metadata" align="center">
              {/* Atlas Intelligence Sprint 2 (Deliverable 7): the one
                  synthesized answer to "what should I do now" -- leftmost
                  and most prominent. Already accounts for a weak Fit or
                  high risk downgrading an otherwise-favorable direction
                  (this Sprint's own "Excellent company, Weak Fit -> Watch,
                  not Consider adding" worked example), so it is never
                  stronger than Fit/Coverage beside it would justify. */}
              {stance !== null && <StanceBadge level={stance.level} />}
              {/* RC-2, Phase 1 (Badge Audit) -- the standalone Confidence
                  badge that used to sit here answered the same underlying
                  question ("how much does Atlas actually know here") that
                  Evidence Rating answers elsewhere in the product, just in
                  a different word. Removed, not lost: the "Evidence
                  quality"/"Evidence history" disclosures immediately below
                  still open onto the identical coverage/confidence data,
                  one click away instead of a permanent third badge on
                  every one of ~11 cards. */}
              <FitBadge rating={assessment.overall} />
            </Inline>
          )}
        </Inline>

        {assessment === null && (
          <Text color="tertiary" as="p">
            {t(canEvaluate ? "discovery.card.fitPending" : "discovery.card.noCaseYet")}
          </Text>
        )}

        {stanceFitTensionKey(stance, assessment) !== null && (
          <Text color="secondary" as="p">
            {t(stanceFitTensionKey(stance, assessment)!)}
          </Text>
        )}

        {assessment !== null && assessment.overallReasoning.length > 0 && (
          <Text color="secondary" as="p">
            {assessment.overallReasoning[0]}
          </Text>
        )}

        {/* Atlas Intelligence Sprint 3 (Decision Explainability &
            Evidence Trace, Deliverable 6). `assessment !== null` is
            the same "a real Case exists to explain" gate this whole
            card already uses above. */}
        {assessment !== null && (
          <TickerExplanationDetail ticker={ticker} summaryLabel={t("explainability.discovery.expandLabel")} t={t} />
        )}

        {/* Atlas Intelligence Sprint 4 (Evidence Quality & Conflict
            Resolution, Deliverable 7). Same gate as the Explanation
            detail immediately above -- distinguishes strong/weak/
            conflicting/fresh/old evidence without affecting candidate
            ranking (this card's own list order is untouched). */}
        {assessment !== null && (
          <TickerEvidenceQualityDetail ticker={ticker} summaryLabel={t("evidenceQuality.discovery.expandLabel")} t={t} />
        )}

        {/* Atlas Intelligence Sprint 5 (Evidence Timeline & Historical
            Understanding, Deliverable 7). Same gate, distinguishes
            recently improving/deteriorating/stable/unknown-history
            evidence without affecting this card's own ranking. */}
        {assessment !== null && (
          <TickerEvidenceTimelineDetail ticker={ticker} summaryLabel={t("evidenceTimeline.discovery.expandLabel")} t={t} />
        )}

        {variant === "full" && grouped !== null && (
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

        {variant === "compact" &&
          grouped !== null &&
          (() => {
            const favorable = grouped.favorable.filter((d) => !isGenericAllocationReasoning(d.reasoning[0]));
            const unfavorable = grouped.unfavorable.filter((d) => !isGenericAllocationReasoning(d.reasoning[0]));
            if (!favorable[0] && !unfavorable[0]) return null;
            return (
              <Stack gap="metadata">
                {favorable[0] && (
                  <Text color="tertiary" as="p">
                    + {favorable[0].reasoning[0] ?? t(`portfolioFit.dimension.${favorable[0].kind}` as TranslationKey)}
                  </Text>
                )}
                {unfavorable[0] && (
                  <Text color="tertiary" as="p">
                    − {unfavorable[0].reasoning[0] ?? t(`portfolioFit.dimension.${unfavorable[0].kind}` as TranslationKey)}
                  </Text>
                )}
              </Stack>
            );
          })()}

        <Inline gap="row" align="center" wrap>
          {canEvaluate ? (
            <Button variant="tertiary" onClick={onOpenCase}>
              {t("discovery.card.openCase")}
            </Button>
          ) : (
            onAddToWatchlist && (
              <Button variant="primary" onClick={onAddToWatchlist}>
                {t("discovery.card.addToWatchlistToEvaluate")}
              </Button>
            )
          )}
          {isOnWatchlist && onRemoveFromWatchlist && (
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

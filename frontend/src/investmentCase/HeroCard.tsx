import type { CSSProperties, ReactNode } from "react";
import { Button, Divider, Heading, Inline, Label, Stack, StatusBadge, StatusText, Text, VisuallyHidden } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import {
  type AnalysisBusinessStatus,
  type AnalysisHighlightKind,
  type AnalysisRiskCategory,
  type AnalysisValuationStatus,
} from "../changeIntelligence/describeChange";
import {
  CONVICTION_LEVEL_KEY,
  CONVICTION_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_STATEMENT_KEY,
  DECISION_SUPPORT_TONE,
  MISSING_EVALUATION_COPY_KEY,
  OUTLOOK_ALIGNMENT_KEY,
  VALUATION_SUPPORT_GAP_COPY_KEY,
  VALUATION_SUPPORT_LABEL_KEY,
  VALUATION_SUPPORT_TONE,
  type ConvictionLevel,
  type DecisionSupportLevel,
  type MissingEvaluationCategory,
  type OutlookRecommendationRelationship,
  type ValuationSupportStatus,
} from "../status/statusTone";
import { formatRelativeTime } from "../activity/deriveActivity";
import {
  deriveCurrentPriority,
  findMostSevereRisk,
  type CurrentPriorityKind,
  type LimitingFactor,
  type OutstandingWorkKind,
  type RiskFindingLite,
} from "./deriveExecutiveSummary";
import { formatFinancialValue } from "./FinancialsTable";
import { deriveHeroHasNotableChange, deriveHeroTension, type HeroTensionKind } from "./deriveHeroNarrative";
import { formatPercent, GAP_KEY, type OutlookGapKind } from "./AtlasOutlookSection";
import type { TranslationKey } from "../i18n";
import { StanceSummary } from "../stance/StanceSummary";
import type { StanceView } from "../stance/stanceApi";

/**
 * Investment Case Hero (Figma-fidelity rebuild, on top of `APP-003`'s
 * Thought Model and `APP-002`'s language). The Figma wins on structure:
 * a short Atlas sentence, a Key Metrics field row (Recommendation,
 * Conviction, Expected Return, Upside/Downside), and a Biggest
 * Strength/Concern/Priority row -- all inside one card. `APP-003` still
 * governs which sentence is worth saying (the conclusion, stated
 * plainly, per the reasoning sequence already adopted); `APP-002` still
 * governs its register. Prose is now one sentence, not a paragraph --
 * it supports the hierarchy below it, it does not replace it.
 *
 * Expected Return and Upside/Downside now render Long-Term Outlook's real
 * figures (Long-Term Expected Return v1 / Calibration Sprint) -- Expected
 * Return is `outlook.longTerm.expectedReturn`'s own low/high range;
 * Upside/Downside is the Bull/Bear scenario's own `returnPercent` from
 * that same horizon. Both still render an honest "not yet available"
 * state, unchanged, whenever this specific company's Outlook does not
 * clear Long-Term's own eligibility gate (`OutlookGapKind`) -- never a
 * fabricated figure. This is still a re-rating-plus-growth range, not a
 * price target or a scenario-based valuation -- see
 * `atlas.analysis_engine.outlook`'s own module docstring.
 *
 * Recommendation / Decision Intelligence Sprint 1: a single, disclosed
 * line beneath Key Metrics reports whether Long-Term Outlook currently
 * corroborates or diverges from this Recommendation
 * (`outlookAlignmentLongTerm`) -- computed entirely independently of
 * Direction selection (`atlas.analysis_engine.recommendation_outlook_context`),
 * never its cause. Omitted entirely when unavailable (Recommendation
 * Withheld, or this horizon's Outlook itself unavailable) -- no line is
 * better than a noisy, uninformative one.
 */

const HERO_WHY_KEY: Record<HeroTensionKind, TranslationKey> = {
  aligned_positive: "investmentCase.hero.why.aligned_positive",
  aligned_negative: "investmentCase.hero.why.aligned_negative",
  business_strong_valuation_weak: "investmentCase.hero.why.business_strong_valuation_weak",
  business_weak_valuation_strong: "investmentCase.hero.why.business_weak_valuation_strong",
  insufficient: "investmentCase.hero.why.insufficient",
  neutral: "investmentCase.hero.why.neutral",
};

const PRIORITY_SENTENCE_KEY: Record<CurrentPriorityKind, TranslationKey> = {
  outcomeMissing: "investmentCase.hero.closing.outcomeMissing",
  reconciliationNeeded: "investmentCase.hero.closing.reconciliationNeeded",
  thesisStale: "investmentCase.hero.closing.thesisStale",
  openQuestion: "investmentCase.hero.closing.openQuestion",
  none: "investmentCase.currentPriority.none",
};

/** Shared with `InvestmentArgumentSection`'s Supports column -- the same
 * real classification, the same sentence, never restated differently in
 * two places. `HighlightKind` (`atlas.analysis_engine.investment_case_synthesis`)
 * is directional, not fixed-valence: Growth/Capital Allocation/Valuation
 * each land in `strengths[]` when their finding is positive and in
 * `risks[]` when it's negative (`_business_highlights`/
 * `_valuation_highlights`), so this bank must only ever be read against
 * `strengths[]`. Reading it against `risks[]` would print a positive
 * sentence under a negative heading -- see `CHALLENGE_SENTENCE_KEY`
 * below for that direction. */
export const STRENGTH_SENTENCE_KEY: Record<AnalysisHighlightKind, TranslationKey> = {
  growth: "investmentCase.argument.supports.growth",
  capital_allocation: "investmentCase.argument.supports.capital_allocation",
  valuation: "investmentCase.argument.supports.valuation",
  business_risk: "investmentCase.argument.challenges.business_risk",
  financial_risk: "investmentCase.argument.challenges.financial_risk",
  valuation_risk: "investmentCase.argument.challenges.valuation_risk",
};

/** Shared with `InvestmentArgumentSection`'s Challenges column -- the
 * negative-direction counterpart to `STRENGTH_SENTENCE_KEY` above, for
 * reading against `risks[]`. Business Risk/Financial Risk/Valuation Risk
 * only ever appear as risks server-side, so their sentence is identical
 * either way; Growth/Capital Allocation/Valuation need their own
 * negative framing here since the same `kind` can legitimately appear in
 * either column depending on the underlying finding's direction. */
export const CHALLENGE_SENTENCE_KEY: Record<AnalysisHighlightKind, TranslationKey> = {
  growth: "investmentCase.argument.challenges.growth",
  capital_allocation: "investmentCase.argument.challenges.capital_allocation",
  valuation: "investmentCase.argument.challenges.valuation",
  business_risk: "investmentCase.argument.challenges.business_risk",
  financial_risk: "investmentCase.argument.challenges.financial_risk",
  valuation_risk: "investmentCase.argument.challenges.valuation_risk",
};

export const CONCERN_SENTENCE_KEY: Record<AnalysisRiskCategory, TranslationKey> = {
  business_risk: "investmentCase.argument.challenges.business_risk",
  financial_risk: "investmentCase.argument.challenges.financial_risk",
  valuation_risk: "investmentCase.argument.challenges.valuation_risk",
  thesis_risk: "investmentCase.concern.thesis_risk",
};

export interface HeroAnalysisInput {
  recommendationLevel: DecisionSupportLevel;
  convictionLevel: ConvictionLevel;
  growthStatus: AnalysisBusinessStatus;
  capitalAllocationStatus: AnalysisBusinessStatus;
  valuationStatus: AnalysisValuationStatus;
  riskFindings: RiskFindingLite[];
  topStrengthKind: AnalysisHighlightKind | null;
  isBaselineCase: boolean;
  latestChangeCount: number;
  currentAnalysisAt: string;
  /** Long-Term Expected Return v1 / Calibration Sprint -- `null` exactly
   * when `longTermExpectedReturnGap` is non-null (mirrors the backend's
   * own `HorizonOutlook` "exactly one of the two" invariant). */
  longTermExpectedReturn: { lowPercent: number; highPercent: number } | null;
  longTermExpectedReturnGap: OutlookGapKind | null;
  /** The Long-Term Bull/Bear scenario's own `returnPercent` -- `null`
   * whenever Long-Term's scenarios are themselves gapped (the same
   * `expectedReturnGap` case in practice, since both are gated by the
   * identical eligibility check, but read independently rather than
   * assumed equivalent -- see `atlas.analysis_engine.outlook`'s own
   * "checked independently" convention for `expected_return`/`scenarios`). */
  longTermBullReturnPercent: number | null;
  longTermBearReturnPercent: number | null;
  /** Recommendation / Decision Intelligence Sprint 1 -- see this file's
   * own module docstring. */
  outlookAlignmentLongTerm: OutlookRecommendationRelationship;
  /** Alpha Freeze correction sprint (Principal Engineer Review 2.0,
   * finding M-2) -- `DE-015`'s `ValuationSupport.status`, rendered under
   * the safe presentation labels `UX-021`/`UX-022` already specified,
   * never the raw enum value. */
  valuationSupportStatus: ValuationSupportStatus;
  /** Beta Recommendation Experience implementation sprint (`UX-022`
   * §3/§6): the real, at-most-2 "what limits this conclusion" facts --
   * see `deriveLimitingFactors`'s own docstring. Only the first (highest
   * -priority) entry renders here, as the hero's compact "Limited by:"
   * line -- real value on Company Workspace, where this Hero renders
   * standalone with nothing below it. Internal Alpha Stabilization:
   * `InvestmentCasePage.tsx` renders `ValuationSupportCard` then
   * `LimitingFactorsCard` immediately below this same Hero (only
   * hairline dividers between them), which restated this exact sentence
   * up to two more times before this fix -- that page now passes
   * `suppressLimitingFactorPreview` to omit this line there specifically,
   * rather than removing the fact everywhere it has real value. */
  limitingFactors: LimitingFactor[];
  /** Beta Recommendation Experience implementation sprint (`UX-022`
   * §4): real, per-case Withheld reasons -- always `[]` when
   * `recommendationLevel !== "insufficient_evidence"`. */
  missingEvaluations: MissingEvaluationCategory[];
  /** `MarketSnapshotView.sharePrice`/`.currency` -- real, already
   * fetched, previously not placed in the Key Metrics row (`UX-022`'s
   * own corrected component table: "Current Price only (real)"). */
  sharePrice: number | null;
  currency: string | null;
  /** Internal Alpha Stabilization 1 (MSFT price root cause fix) -- the
   * real trading day this price is from (ISO date string), and the
   * server-computed freshness status against it. Never derived
   * client-side. Both optional: `CompanyWorkspacePage.tsx` also reuses
   * this component verbatim and does not (yet) fetch either value --
   * omitting them there falls back to "unavailable" (no badge, no
   * button), never a fabricated status. */
  tradingDay?: string | null;
  priceFreshness?: "fresh" | "stale" | "refreshing" | "failed" | "unavailable";
  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 5) -- `null` only when no `StanceService`
   * was wired for this build (mirrors `changeIntelligenceAvailable`'s
   * own precedent elsewhere on this page); every real API call site
   * wires one. Reuses this existing Hero area rather than a new
   * section -- see `StanceSummary`'s own docstring. */
  stance: StanceView | null;
  /** Import Robustness (Internal Alpha Stabilization 1) --
   * `InvestmentCaseAnalysisView.noProviderDataFound`, verbatim. `True`
   * only for a real, persisted "no provider ever returned any identity
   * data for this ticker" fact (see the backend's own
   * `CanonicalSecurityIdentityGate.latest_resolution_was_no_match`
   * docstring) -- never a guess. Only ever meaningful while
   * `recommendationLevel === "insufficient_evidence"`; optional so
   * `CompanyWorkspacePage.tsx`'s older call site (which does not fetch
   * this field) keeps its unchanged generic withheld message. */
  noProviderDataFound?: boolean;
}

interface HeroCardProps {
  ticker: string;
  analysis: HeroAnalysisInput;
  outstandingWorkKinds: OutstandingWorkKind[];
  isThesisStale: boolean;
  openQuestionCount: number;
  t: Translate;
  locale: string;
  /** Internal Alpha Stabilization -- see `HeroAnalysisInput.limitingFactors`'s
   * own docstring. Defaults to `false` (shows the preview line), the
   * original behavior every existing caller still gets; only
   * `InvestmentCasePage.tsx` opts in, since it alone renders the fuller
   * detail immediately below this same card. */
  suppressLimitingFactorPreview?: boolean;
  /** Internal Alpha Stabilization 1 (MSFT price root cause fix) -- the
   * manual "Uppdatera" escape hatch next to "Aktuellt pris". Optional
   * so this component stays usable without it (e.g. in tests that
   * don't exercise the refresh flow); when omitted, no button renders. */
  onRefreshPrice?: () => void;
  isRefreshingPrice?: boolean;
}

const HERO_SENTENCE_STYLE: CSSProperties = {
  fontFamily: "var(--type-family-prose)",
  fontSize: "var(--type-size-h5)",
  lineHeight: 1.6,
  color: "var(--color-text-primary)",
  maxWidth: "70ch",
};

function MetricField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Stack gap="metadata" style={{ minWidth: "9rem" }}>
      <Label>{label}</Label>
      <div>{children}</div>
    </Stack>
  );
}

export function HeroCard({
  ticker,
  analysis,
  outstandingWorkKinds,
  isThesisStale,
  openQuestionCount,
  t,
  locale,
  suppressLimitingFactorPreview = false,
  onRefreshPrice,
  isRefreshingPrice = false,
}: HeroCardProps) {
  const isWithheld = analysis.recommendationLevel === "insufficient_evidence";
  const topLimitingFactor: LimitingFactor | undefined = analysis.limitingFactors[0];

  const priority = deriveCurrentPriority({ outstandingWorkKinds, isThesisStale, openQuestionCount });
  const hasNotableChange = deriveHeroHasNotableChange({
    isBaselineCase: analysis.isBaselineCase,
    latestChangeCount: analysis.latestChangeCount,
  });
  const tension = deriveHeroTension({
    growthStatus: analysis.growthStatus,
    capitalAllocationStatus: analysis.capitalAllocationStatus,
    valuationStatus: analysis.valuationStatus,
  });
  const mostSevereRisk = findMostSevereRisk(analysis.riskFindings);
  const freshness = formatRelativeTime(analysis.currentAnalysisAt, t);

  return (
    <Stack gap="metadata">
      <Heading level={2}>
        <VisuallyHidden>{t("investmentCase.hero.srHeading")}</VisuallyHidden>
      </Heading>

      <Divider tone="hairline" />

      {isWithheld ? (
        <>
          {analysis.noProviderDataFound ? (
            <Text as="p" style={HERO_SENTENCE_STYLE}>
              {t("investmentCase.hero.noProviderData", { ticker })}
            </Text>
          ) : (
            <Text as="p" style={HERO_SENTENCE_STYLE}>
              {t("investmentCase.hero.withheld.opening", { ticker })} {t("investmentCase.hero.withheld.reason")}{" "}
              {t("investmentCase.hero.withheld.closing")}
            </Text>
          )}
          <StatusBadge
            label={t(DECISION_SUPPORT_BADGE_KEY[analysis.recommendationLevel])}
            tone={DECISION_SUPPORT_TONE[analysis.recommendationLevel]}
          />
          {/* `UX-022` §4: the real, per-case missing-evaluation stages --
              alongside the fixed sentence above, never replacing it. */}
          {analysis.missingEvaluations.length > 0 && (
            <Stack gap="metadata">
              {analysis.missingEvaluations.map((category) => (
                <Text as="p" color="secondary" key={category}>
                  {t(MISSING_EVALUATION_COPY_KEY[category])}
                </Text>
              ))}
            </Stack>
          )}
          {analysis.stance && (
            <>
              <Divider tone="hairline" />
              <StanceSummary stance={analysis.stance} t={t} />
            </>
          )}
        </>
      ) : (
        <>
          {/* One sentence -- the conclusion, plus its tension where one
              genuinely exists (`APP-003` ATM-R-002). Prose supports the
              Key Metrics row below, it does not restate it. */}
          <Text as="p" style={HERO_SENTENCE_STYLE}>
            {t(DECISION_SUPPORT_STATEMENT_KEY[analysis.recommendationLevel])} {t(HERO_WHY_KEY[tension])}
          </Text>

          {/* `UX-022` §3/§6: the single highest-priority real limiting
              factor, compact hero placement. Internal Alpha Stabilization:
              suppressed specifically on Investment Case, where
              `ValuationSupportCard` then `LimitingFactorsCard` render
              immediately below this same card (only hairline dividers
              between them) -- a real investor reading top to bottom saw
              the identical sentence (e.g. "the valuation range contains
              both an upside and a downside") up to three times in one
              screen's worth of content before this fix. Company
              Workspace renders this Hero standalone with nothing below
              it, so it still gets this line -- the fact is never lost
              where it's the only place stating it. */}
          {topLimitingFactor && !suppressLimitingFactorPreview && (
            <Text as="p" color="secondary">
              {t("investmentCase.hero.limitedByPrefix")}{" "}
              {topLimitingFactor.kind === "valuationGap"
                ? t(VALUATION_SUPPORT_GAP_COPY_KEY[topLimitingFactor.gap])
                : t(CONCERN_SENTENCE_KEY[topLimitingFactor.category])}
            </Text>
          )}

          {analysis.stance && (
            <>
              <Divider tone="hairline" />
              <StanceSummary stance={analysis.stance} t={t} />
            </>
          )}

          <Divider tone="hairline" />

          {/* Key Metrics -- Figma's own labeled-field row. Expected
              Return / Upside-Downside render Long-Term Outlook's real
              figures when this company's Outlook clears its own
              eligibility gate, and an honest "not yet available" state
              (with the real, named reason) otherwise -- never a
              fabricated figure. See file header. */}
          <Label>{t("investmentCase.keyMetrics.heading")}</Label>
          <Inline gap="inter-section" wrap align="start">
            <MetricField label={t("investmentCase.keyMetrics.recommendationLabel")}>
              <Text as="span" style={{ fontWeight: 600 }}>
                {t(DECISION_SUPPORT_BADGE_KEY[analysis.recommendationLevel])}
              </Text>
            </MetricField>
            <MetricField label={t("investmentCase.keyMetrics.convictionLabel")}>
              <StatusBadge
                label={t(CONVICTION_LEVEL_KEY[analysis.convictionLevel])}
                tone={CONVICTION_TONE[analysis.convictionLevel]}
              />
            </MetricField>
            <MetricField label={t("investmentCase.keyMetrics.valuationSupportLabel")}>
              <StatusBadge
                label={t(VALUATION_SUPPORT_LABEL_KEY[analysis.valuationSupportStatus])}
                tone={VALUATION_SUPPORT_TONE[analysis.valuationSupportStatus]}
                style={{ whiteSpace: "normal" }}
              />
            </MetricField>
            <MetricField label={t("investmentCase.keyMetrics.currentPriceLabel")}>
              <Stack gap="metadata">
                <Text as="span" style={{ fontWeight: 600 }}>
                  {formatFinancialValue(analysis.sharePrice, analysis.currency, locale)}
                </Text>
                {analysis.tradingDay && (
                  <Text as="span" color="tertiary">
                    {t("investmentCase.keyMetrics.priceUpdatedLabel", {
                      date: new Date(analysis.tradingDay).toLocaleDateString(locale, { month: "short", day: "numeric" }),
                    })}
                  </Text>
                )}
                {analysis.priceFreshness === "stale" && (
                  <StatusBadge label={t("investmentCase.keyMetrics.priceStale")} tone="caution" />
                )}
                {analysis.priceFreshness === "refreshing" && (
                  <StatusBadge label={t("investmentCase.keyMetrics.priceRefreshing")} tone="neutral" />
                )}
                {analysis.priceFreshness === "failed" && (
                  <StatusBadge label={t("investmentCase.keyMetrics.priceRefreshFailed")} tone="critical" />
                )}
                {onRefreshPrice && (analysis.priceFreshness ?? "unavailable") !== "unavailable" && (
                  <Button
                    variant="tertiary"
                    onClick={onRefreshPrice}
                    disabled={isRefreshingPrice || analysis.priceFreshness === "refreshing"}
                  >
                    {isRefreshingPrice || analysis.priceFreshness === "refreshing"
                      ? t("investmentCase.keyMetrics.priceRefreshing")
                      : t("investmentCase.keyMetrics.priceRefreshButton")}
                  </Button>
                )}
              </Stack>
            </MetricField>
            <MetricField label={t("investmentCase.keyMetrics.expectedReturnLabel")}>
              {analysis.longTermExpectedReturn ? (
                <>
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {formatPercent(analysis.longTermExpectedReturn.lowPercent)} {"→"}{" "}
                    {formatPercent(analysis.longTermExpectedReturn.highPercent)}
                  </Text>
                  <Text as="p" color="tertiary">
                    {t("investmentCase.keyMetrics.expectedReturnCaption")}
                  </Text>
                </>
              ) : (
                <>
                  <StatusText label={t("investmentCase.keyMetrics.notYetAvailable")} tone="neutral" />
                  {analysis.longTermExpectedReturnGap && (
                    <Text as="p" color="tertiary">
                      {t(GAP_KEY[analysis.longTermExpectedReturnGap])}
                    </Text>
                  )}
                </>
              )}
            </MetricField>
            <MetricField label={t("investmentCase.keyMetrics.upsideDownsideLabel")}>
              {analysis.longTermBullReturnPercent != null && analysis.longTermBearReturnPercent != null ? (
                <Text as="span" style={{ fontWeight: 600 }}>
                  {formatPercent(analysis.longTermBullReturnPercent)} {"/"}{" "}
                  {formatPercent(analysis.longTermBearReturnPercent)}
                </Text>
              ) : (
                <StatusText label={t("investmentCase.keyMetrics.notYetAvailable")} tone="neutral" />
              )}
            </MetricField>
          </Inline>

          {analysis.outlookAlignmentLongTerm !== "unavailable" && (
            <Text as="p" color="tertiary">
              {t(OUTLOOK_ALIGNMENT_KEY[analysis.outlookAlignmentLongTerm])}
            </Text>
          )}

          <Divider tone="hairline" />

          {/* Biggest Strength / Biggest Concern / Current Priority --
              three real, already-computed facts, never restated
              elsewhere in different words: Strength reuses the same
              sentence bank `InvestmentArgumentSection` uses for its
              Supports column; Concern reuses the same `findMostSevereRisk`
              selection already used for the supporting-strip risk chip;
              Priority reuses `deriveCurrentPriority` unchanged. */}
          <Inline gap="inter-section" wrap align="start">
            <Stack gap="metadata" style={{ flex: "1 1 220px", minWidth: 0 }}>
              <Label>{t("investmentCase.strengthConcernPriority.strengthLabel")}</Label>
              <Text as="p">
                {analysis.topStrengthKind
                  ? t(STRENGTH_SENTENCE_KEY[analysis.topStrengthKind])
                  : t("investmentCase.strengthConcernPriority.noStrength")}
              </Text>
            </Stack>
            <Stack gap="metadata" style={{ flex: "1 1 220px", minWidth: 0 }}>
              <Label>{t("investmentCase.strengthConcernPriority.concernLabel")}</Label>
              <Text as="p">
                {mostSevereRisk
                  ? t(CONCERN_SENTENCE_KEY[mostSevereRisk.category])
                  : t("investmentCase.strengthConcernPriority.noConcern")}
              </Text>
            </Stack>
            <Stack gap="metadata" style={{ flex: "1 1 220px", minWidth: 0 }}>
              <Label>{t("investmentCase.strengthConcernPriority.priorityLabel")}</Label>
              <Text as="p">
                {hasNotableChange && priority === "none"
                  ? t("investmentCase.hero.closing.changed")
                  : t(PRIORITY_SENTENCE_KEY[priority])}
              </Text>
            </Stack>
          </Inline>
        </>
      )}

      <Text as="p" color="tertiary">
        {t("investmentCase.hero.asOf", { when: freshness })}
      </Text>
    </Stack>
  );
}

import type { CSSProperties, ReactNode } from "react";
import { Button, Divider, Heading, Inline, Label, Stack, StatusBadge, StatusText, Surface, Text, VisuallyHidden } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import {
  type AnalysisBusinessStatus,
  type AnalysisHighlightKind,
  type AnalysisRiskCategory,
  type AnalysisValuationStatus,
} from "../changeIntelligence/describeChange";
import {
  CHANGE_TRIGGER_KEY,
  CONVICTION_LEVEL_KEY,
  CONVICTION_REASON_KEY,
  CONVICTION_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_STATEMENT_KEY,
  DECISION_SUPPORT_TONE,
  MISSING_EVALUATION_COPY_KEY,
  OUTLOOK_ALIGNMENT_KEY,
  VALUATION_SUPPORT_GAP_COPY_KEY,
  VALUATION_SUPPORT_LABEL_KEY,
  VALUATION_SUPPORT_TONE,
  type ChangeTriggerKind,
  type ConvictionLevel,
  type ConvictionReasonCode,
  type DecisionSupportLevel,
  type MissingEvaluationCategory,
  type OutlookRecommendationRelationship,
  type ValuationSupportStatus,
} from "../status/statusTone";
import { formatRelativeTime } from "../activity/deriveActivity";
import {
  deriveCurrentPriority,
  deriveRecommendationDrivers,
  findMostSevereRisk,
  type CurrentPriorityKind,
  type LimitingFactor,
  type OutstandingWorkKind,
  type RecommendationDriverKind,
  type RiskFindingLite,
} from "./deriveExecutiveSummary";
import { formatFinancialValue } from "./FinancialsTable";
import { deriveHeroHasNotableChange, deriveHeroTension, type HeroTensionKind } from "./deriveHeroNarrative";
import { formatPercent, GAP_KEY, type OutlookGapKind } from "./AtlasOutlookSection";
import type { TranslationKey } from "../i18n";
import { StanceSummary } from "../stance/StanceSummary";
import type { StanceView } from "../stance/stanceApi";
import { ExpandableDetail } from "./ExpandableDetail";

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

/** Exported for `SevenCategoriesSection.tsx`'s `CaseDnaLine` -- the
 * one home for this lookup, reused, never duplicated. */
export const HERO_WHY_KEY: Record<HeroTensionKind, TranslationKey> = {
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
  /** Implementation Sprint B2 (Hero Reordering) -- `ConvictionAssessment
   * .reasons`, real, already-fetched, previously never surfaced
   * anywhere on this page (`report.conviction.reasons` was fetched and
   * silently unused). Only the first (highest-priority) entry renders,
   * as the Hero's own "Conviction" step's supporting reason -- the same
   * "compact fact in the hero, never a fabricated one" discipline every
   * other field on this card already follows. Empty array is a normal,
   * honest state (Conviction reached its level without a specific
   * disclosed reason to name), never treated as missing data. */
  convictionReasonCodes: ConvictionReasonCode[];
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
  /** Calibration Phase 2 (Investment Case Coherence Implementation),
   * Phase 5 -- `strengths[]`/`risks[]` mapped to their `kind`, fed
   * straight into `deriveRecommendationDrivers`. Real, already-fetched,
   * already-decisive-only classifications; this component invents no
   * new selection of its own. */
  strengthKinds: RecommendationDriverKind[];
  challengeKinds: RecommendationDriverKind[];
  /** Calibration Phase 2, Phase 6 -- `report.recommendation.whatWouldChange`,
   * verbatim. Empty for a withheld recommendation (no Direction was
   * ever selected, so there is nothing specific to name). */
  whatWouldChange: ChangeTriggerKind[];
}

interface HeroCardProps {
  ticker: string;
  analysis: HeroAnalysisInput;
  outstandingWorkKinds: OutstandingWorkKind[];
  isThesisStale: boolean;
  openQuestionCount: number;
  /** Implementation Sprint B2 (Hero Reordering) -- the real, already-
   * resolved translation key for `report.openQuestions[0]` (the exact
   * same resolution `EvidenceCoverageCard` already performs, computed
   * once by the caller and passed in rather than re-derived here, so
   * this presentation-only component never needs to know the backend's
   * open-question kind vocabulary). `null` when there is no open
   * question at all -- a genuinely good state, rendered as such, never
   * hidden or padded with a fabricated one. */
  primaryOpenQuestionKey?: TranslationKey | null;
  t: Translate;
  locale: string;
  /** Internal Alpha Stabilization -- see `HeroAnalysisInput.limitingFactors`'s
   * own docstring. Defaults to `false` (shows the preview line), the
   * original behavior every existing caller still gets; only
   * `InvestmentCasePage.tsx` opts in, since it alone renders the fuller
   * detail immediately below this same card. */
  suppressLimitingFactorPreview?: boolean;
  /** Atlas UX Phase 7A (Semantic Investment Model) -- the tension
   * sentence (`HERO_WHY_KEY[tension]`) is promoted to its own "Case
   * DNA" line elsewhere on the page (`SevenCategoriesSection.tsx`'s
   * `CaseDnaLine`), so this card renders only the Recommendation
   * statement here, never both -- the exact "compact fact in the
   * story, full detail as its own labeled block" split
   * `suppressLimitingFactorPreview` already established. Defaults to
   * `false` (shows the full two-sentence paragraph, unchanged), so
   * every existing caller (`CompanyWorkspacePage.tsx`) keeps its
   * current behavior; only `InvestmentCasePage.tsx` opts in. */
  suppressTensionSentence?: boolean;
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

function SummaryStat({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Stack gap="metadata" style={{ minWidth: "8rem" }}>
      <Label>{label}</Label>
      {children}
    </Stack>
  );
}

/**
 * Editorial Design Sprint P3 (Phase 5/10) -- the "readable in under
 * three seconds" executive summary row: Recommendation, Conviction,
 * Expected Return, Upside/Downside, in one compact strip above
 * everything else on the card. Every field is data this component
 * already receives and already renders further down (unchanged
 * `DECISION_SUPPORT_BADGE_KEY`/`CONVICTION_LEVEL_KEY`/long-term
 * expected-return figures) -- this recomposes it into a single glance,
 * it does not compute or fetch anything new. Recommendation is the
 * one PRIMARY signal on this card (Sprint B3's own "one company, one
 * primary message" discipline), rendered with the new `weight="strong"`
 * treatment; Conviction/Expected Return/Upside-Downside are SECONDARY,
 * one visual step down. Deliberately omits a separate "current status"
 * chip: Recommendation already is that status in this codebase, and a
 * second badge naming the same thing would reintroduce exactly the
 * competing-badges problem Sprint B3 removed.
 *
 * Alpha Integration Fix (One Product Pass): this field's own label was
 * "Confidence" even though it has always rendered `convictionLevel` via
 * `CONVICTION_LEVEL_KEY` -- a direct contradiction of this codebase's
 * own doctrine (`status/statusTone.ts`) that Conviction and Confidence
 * are intentionally separate signals. It reads "Conviction" now,
 * matching every other correct usage of this same field elsewhere in
 * the app (Alpha Product Integration Review, Phase 3).
 */
function ExecutiveSummaryBar({ analysis, t }: { analysis: HeroAnalysisInput; t: Translate }) {
  return (
    <Inline
      gap="inter-section"
      wrap
      align="center"
      style={{
        padding: "var(--space-card-padding)",
        background: "var(--surface-elevated)",
        borderRadius: "var(--radius-card)",
      }}
    >
      <SummaryStat label={t("investmentCase.keyMetrics.recommendationLabel")}>
        <StatusBadge
          label={t(DECISION_SUPPORT_BADGE_KEY[analysis.recommendationLevel])}
          tone={DECISION_SUPPORT_TONE[analysis.recommendationLevel]}
          weight="strong"
        />
      </SummaryStat>
      <SummaryStat label={t("investmentCase.hero.convictionLabel")}>
        <StatusBadge
          label={t(CONVICTION_LEVEL_KEY[analysis.convictionLevel])}
          tone={CONVICTION_TONE[analysis.convictionLevel]}
        />
      </SummaryStat>
      <SummaryStat label={t("investmentCase.keyMetrics.expectedReturnLabel")}>
        {analysis.longTermExpectedReturn ? (
          <Text as="span" style={{ fontWeight: 600, fontSize: "var(--type-size-h5)", fontVariantNumeric: "tabular-nums" }}>
            {formatPercent(analysis.longTermExpectedReturn.lowPercent)} {"→"}{" "}
            {formatPercent(analysis.longTermExpectedReturn.highPercent)}
          </Text>
        ) : (
          <Stack gap="metadata">
            <StatusText label={t("investmentCase.keyMetrics.notYetAvailable")} tone="neutral" />
            {/* Redesign From Zero Sprint V2: the gap explanation used to
                live in a now-removed duplicate Expected Return block --
                folded in here so the real reason Expected Return isn't
                available yet stays reachable, not lost in the merge. */}
            {analysis.longTermExpectedReturnGap && (
              <Text as="p" color="tertiary">
                {t(GAP_KEY[analysis.longTermExpectedReturnGap])}
              </Text>
            )}
          </Stack>
        )}
      </SummaryStat>
      <SummaryStat label={t("investmentCase.keyMetrics.upsideDownsideLabel")}>
        {analysis.longTermBullReturnPercent != null && analysis.longTermBearReturnPercent != null ? (
          <Text as="span" style={{ fontWeight: 600, fontSize: "var(--type-size-h5)", fontVariantNumeric: "tabular-nums" }}>
            {formatPercent(analysis.longTermBullReturnPercent)} {"/"}{" "}
            {formatPercent(analysis.longTermBearReturnPercent)}
          </Text>
        ) : (
          <StatusText label={t("investmentCase.keyMetrics.notYetAvailable")} tone="neutral" />
        )}
      </SummaryStat>
    </Inline>
  );
}

export function HeroCard({
  ticker,
  analysis,
  outstandingWorkKinds,
  isThesisStale,
  openQuestionCount,
  primaryOpenQuestionKey = null,
  t,
  locale,
  suppressLimitingFactorPreview = false,
  suppressTensionSentence = false,
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
  const drivers = deriveRecommendationDrivers({
    strengthKinds: analysis.strengthKinds,
    challengeKinds: analysis.challengeKinds,
  });

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
          <ExecutiveSummaryBar analysis={analysis} t={t} />

          {/* Calibration Phase 2 (Investment Case Coherence
              Implementation), Phase 2/C5: Stance is the superset
              judgment (it reads Conviction, Recommendation, Risk,
              Coverage, Change Intelligence, AND Portfolio Fit --
              `atlas.alpha.stance.engine.determine_stance`'s own module
              docstring), so it is the one true "what does Atlas think
              right now" headline, moved to render first. The Decision
              Support statement immediately below it is real, narrower,
              supporting input -- never a second, competing headline. */}
          {analysis.stance && <StanceSummary stance={analysis.stance} t={t} />}

          {/* Redesign From Zero Sprint V2 (Phase: Investment Case
              reconstruction) -- the narrative block right below the
              three-second Summary Bar now carries every sentence that
              explains *why* the bar says what it says: the conclusion,
              its tension, the top limiting factor, and Conviction's own
              reason -- one continuous read, not four re-labeled
              sub-sections each repeating a badge the Summary Bar
              already showed. Conviction's own badge is deliberately not
              repeated here (it's the Summary Bar's own second field);
              only the reason sentence, previously stranded under its
              own "Conviction" heading below a divider, moved up next to
              the conclusion it actually explains. */}
          <Text as="p" color="secondary">
            {t(DECISION_SUPPORT_STATEMENT_KEY[analysis.recommendationLevel])}
            {!suppressTensionSentence && ` ${t(HERO_WHY_KEY[tension])}`}
          </Text>

          {topLimitingFactor && !suppressLimitingFactorPreview && (
            <Text as="p" color="secondary">
              {t("investmentCase.hero.limitedByPrefix")}{" "}
              {topLimitingFactor.kind === "valuationGap"
                ? t(VALUATION_SUPPORT_GAP_COPY_KEY[topLimitingFactor.gap])
                : t(CONCERN_SENTENCE_KEY[topLimitingFactor.category])}
            </Text>
          )}

          {analysis.convictionReasonCodes[0] && (
            <Text as="p" color="secondary">
              {t(CONVICTION_REASON_KEY[analysis.convictionReasonCodes[0]])}
            </Text>
          )}

          {analysis.outlookAlignmentLongTerm !== "unavailable" && (
            <Text as="p" color="tertiary">
              {t(OUTLOOK_ALIGNMENT_KEY[analysis.outlookAlignmentLongTerm])}
            </Text>
          )}

          {/* Calibration Phase 2, Phase 5: the 3-5 real, already-
              decisive factors behind the recommendation -- never every
              available signal, only `strengths[]`/`risks[]`'s own
              closed classification, capped and combined. */}
          {drivers.length > 0 && (
            <Stack gap="metadata">
              <Label>{t("investmentCase.drivers.heading")}</Label>
              <ul style={{ margin: 0, paddingLeft: "1.25em", display: "flex", flexDirection: "column", gap: "var(--space-metadata)" }}>
                {drivers.map((driver, index) => (
                  <li key={`${driver.kind}-${index}`}>
                    <Text as="span">
                      {t(
                        driver.direction === "supports"
                          ? STRENGTH_SENTENCE_KEY[driver.kind]
                          : CHALLENGE_SENTENCE_KEY[driver.kind],
                      )}
                    </Text>
                  </li>
                ))}
              </ul>
            </Stack>
          )}

          {/* Calibration Phase 2, Phase 6: `RecommendationReasoning
              .what_would_change`, genuinely populated -- a real,
              disclosed answer even when nothing here would credibly
              move the call (`no_credible_trigger_identified`), never
              silence standing in for "not computed." Always `[]` for a
              withheld recommendation, so this never renders in that
              branch. */}
          {analysis.whatWouldChange.length > 0 && (
            <Stack gap="metadata">
              <Label>{t("investmentCase.whatWouldChange.heading")}</Label>
              <ul style={{ margin: 0, paddingLeft: "1.25em", display: "flex", flexDirection: "column", gap: "var(--space-metadata)" }}>
                {analysis.whatWouldChange.map((trigger) => (
                  <li key={trigger}>
                    <Text as="span">{t(CHANGE_TRIGGER_KEY[trigger])}</Text>
                  </li>
                ))}
              </ul>
            </Stack>
          )}

          <Divider tone="hairline" />

          {/* Since you were here -- the same real facts
              (`isBaselineCase`/`latestChangeCount`) as before, unchanged
              placement. The full, itemized change list remains exactly
              where it already was, one section down
              (`WhatChangedSection`) -- this is a preview, not a
              duplicate. */}
          <Stack gap="metadata">
            <Label>{t("investmentCase.hero.sinceYouWereHere.heading")}</Label>
            <Text as="p">
              {analysis.isBaselineCase
                ? t("investmentCase.whatChanged.baseline")
                : analysis.latestChangeCount === 0
                  ? t("investmentCase.whatChanged.noChange")
                  : t(
                      analysis.latestChangeCount === 1
                        ? "investmentCase.hero.sinceYouWereHere.countOne"
                        : "investmentCase.hero.sinceYouWereHere.countOther",
                      { count: analysis.latestChangeCount },
                    )}
            </Text>
          </Stack>

          <Divider tone="hairline" />

          {/* Biggest Strength / Biggest Concern / Open Question --
              unchanged since Sprint P4's card-grid treatment. Now sits
              directly after Since You Were Here, one section earlier
              than before, since the Expected Return/Upside-Downside
              block that used to separate them has been removed as a
              pure duplicate of the Summary Bar above (Redesign From
              Zero Sprint V2). Strength reuses the same sentence bank
              `InvestmentArgumentSection` uses for its Supports column;
              risk (labeled "Concern" in this codebase, same fact)
              reuses the same `findMostSevereRisk` selection already
              used for the supporting-strip risk chip; the open
              question is the same real, resolved question
              `EvidenceCoverageCard` shows in its own expandable detail. */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "var(--space-row)",
            }}
          >
            <Surface tier="elevated">
              <Stack gap="metadata">
                <Label>{t("investmentCase.strengthConcernPriority.strengthLabel")}</Label>
                <Text as="p">
                  {analysis.topStrengthKind
                    ? t(STRENGTH_SENTENCE_KEY[analysis.topStrengthKind])
                    : t("investmentCase.strengthConcernPriority.noStrength")}
                </Text>
              </Stack>
            </Surface>
            <Surface tier="elevated">
              <Stack gap="metadata">
                <Label>{t("investmentCase.strengthConcernPriority.concernLabel")}</Label>
                <Text as="p">
                  {mostSevereRisk
                    ? t(CONCERN_SENTENCE_KEY[mostSevereRisk.category])
                    : t("investmentCase.strengthConcernPriority.noConcern")}
                </Text>
              </Stack>
            </Surface>
            <Surface tier="elevated">
              <Stack gap="metadata">
                <Label>{t("investmentCase.hero.openQuestionLabel")}</Label>
                <Text as="p">{primaryOpenQuestionKey ? t(primaryOpenQuestionKey) : t("investmentCase.hero.openQuestion.none")}</Text>
              </Stack>
            </Surface>
          </div>

          <Divider tone="hairline" />

          {/* Redesign From Zero Sprint V2: renamed from "Key Metrics" to
              "Additional details" -- Recommendation and Expected Return/
              Upside-Downside, the two fields that used to anchor this
              row, are now exclusively the Summary Bar's own job; what's
              left (Valuation Support, Current Price, Current Priority)
              is genuinely supporting reference data, and the heading
              already said so.
              RC-2, Phase 5 (Investment Case Compression): the section's
              own docstring already called this "genuinely supporting
              reference data," yet it rendered eagerly, ahead of Seven
              Categories/Case DNA lower on the page -- exactly backwards
              from "first screen answers What/Why/Risk/Upside/Horizon,
              nothing else." Now behind the same `ExpandableDetail`
              disclosure primitive already used everywhere else in this
              codebase for secondary reference data -- collapsed by
              default, one click away, nothing removed (the price-
              refresh action inside still works once expanded). */}
          <ExpandableDetail summaryLabel={t("investmentCase.hero.additionalDetailsHeading")}>
            <Inline gap="inter-section" wrap align="start">
              <MetricField label={t("investmentCase.keyMetrics.valuationSupportLabel")}>
              <StatusBadge
                label={t(VALUATION_SUPPORT_LABEL_KEY[analysis.valuationSupportStatus])}
                tone={VALUATION_SUPPORT_TONE[analysis.valuationSupportStatus]}
                style={{ whiteSpace: "normal" }}
              />
            </MetricField>
            <MetricField label={t("investmentCase.keyMetrics.currentPriceLabel")}>
              <Stack gap="metadata">
                <Text as="span" style={{ fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
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
            <MetricField label={t("investmentCase.strengthConcernPriority.priorityLabel")}>
              <Text as="p">
                {hasNotableChange && priority === "none"
                  ? t("investmentCase.hero.closing.changed")
                  : t(PRIORITY_SENTENCE_KEY[priority])}
              </Text>
            </MetricField>
            </Inline>
          </ExpandableDetail>
        </>
      )}

      <Text as="p" color="tertiary">
        {t("investmentCase.hero.asOf", { when: freshness })}
      </Text>
    </Stack>
  );
}

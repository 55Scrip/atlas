import { Inline, Label, Stack, StatusBadge, Text } from "../foundation";
import {
  BUSINESS_STATUS_KEY,
  RISK_STATUS_KEY,
  VALUATION_STATUS_KEY,
  type AnalysisBusinessStatus,
  type AnalysisRiskStatus,
  type AnalysisValuationStatus,
  type Translate,
} from "../changeIntelligence/describeChange";
import { BUSINESS_STATUS_TONE, RISK_STATUS_TONE, VALUATION_STATUS_TONE } from "../status/statusTone";
import type { TranslationKey } from "../i18n";

/**
 * Atlas Reasoning (Figma-fidelity rebuild): four compact, terse,
 * non-expandable cards -- the quick "so what" read, deliberately
 * shallower than `CompanyHealthAssessmentSection`'s fuller, expandable
 * cards below it, even where both draw on the same underlying finding
 * (Business Quality here vs. Business Quality Assessment there). This
 * is the explicit differentiation the brief asks for: not a different
 * topic, a different depth -- one sentence and no expand here, a
 * summary plus real evidence on demand there. Every status is real
 * (`businessAnalysis`/`valuation`/`risk` findings this page already
 * fetches); every interpretation sentence is new copy, but grounded
 * in, and never contradicting, that real status.
 *
 * Product Sprint 13 (Company Intelligence Excellence): the generic
 * per-status sentence above was, until now, the card's entire content
 * -- every company at `growthStatus: "moderate"` rendered the exact
 * same English sentence, regardless of ticker. Each card now also
 * shows the real supporting/contradicting facts already computed for
 * this specific company (the same arrays `CompanyHealthAssessmentSection`
 * and `RiskSection` already render further down this same page) --
 * no new interpretation invented, only real, already-fetched evidence
 * surfaced where it was previously dropped.
 */

const GROWTH_INTERPRETATION_KEY: Record<AnalysisBusinessStatus, TranslationKey> = {
  strong: "investmentCase.reasoning.growth.strong",
  moderate: "investmentCase.reasoning.growth.moderate",
  weak: "investmentCase.reasoning.growth.weak",
  insufficient_input: "investmentCase.reasoning.notYetEvaluated",
  not_evaluated: "investmentCase.reasoning.notYetEvaluated",
};

const VALUATION_INTERPRETATION_KEY: Record<AnalysisValuationStatus, TranslationKey> = {
  undervalued: "investmentCase.reasoning.valuation.undervalued",
  fairly_valued: "investmentCase.reasoning.valuation.fairly_valued",
  expensive: "investmentCase.reasoning.valuation.expensive",
  insufficient_input: "investmentCase.reasoning.notYetEvaluated",
  not_evaluated: "investmentCase.reasoning.notYetEvaluated",
};

const FINANCIAL_HEALTH_INTERPRETATION_KEY: Record<AnalysisRiskStatus, TranslationKey> = {
  low: "investmentCase.reasoning.financialHealth.low",
  moderate: "investmentCase.reasoning.financialHealth.moderate",
  high: "investmentCase.reasoning.financialHealth.high",
  insufficient_input: "investmentCase.reasoning.notYetEvaluated",
  not_evaluated: "investmentCase.reasoning.notYetEvaluated",
};

const BUSINESS_QUALITY_INTERPRETATION_KEY: Record<AnalysisBusinessStatus, TranslationKey> = {
  strong: "investmentCase.reasoning.businessQuality.strong",
  moderate: "investmentCase.reasoning.businessQuality.moderate",
  weak: "investmentCase.reasoning.businessQuality.weak",
  insufficient_input: "investmentCase.reasoning.notYetEvaluated",
  not_evaluated: "investmentCase.reasoning.notYetEvaluated",
};

/** Product Sprint 13 (Company Intelligence Excellence, Deliverable 2 --
 * Atlas Reasoning): a real fact pair already computed for this exact
 * company, one function-scope away on `InvestmentCasePage.tsx` (the
 * same `supportingEvidence`/`contradictingEvidence`/`supportingFacts`/
 * `contradictingFacts` arrays `CompanyHealthAssessmentSection` and
 * `RiskSection` already render, further down the same page) -- never a
 * new computation, only wiring what already exists into a card that
 * previously showed the byte-identical sentence for every company at a
 * given status. */
export interface ReasoningFacts {
  supporting: string[];
  contradicting: string[];
}

/** Product Sprint 13: live-testing found that, for real data, these
 * arrays sometimes hold raw internal evidence-reference ids (e.g.
 * `21ea5c5cd63a91e1eebaea01df3a9645:v1:free_cash_flow:2017-06-30`,
 * `business_finding:growth`) instead of resolved prose -- already true
 * of `RiskSection`'s own pre-existing, unrelated rendering of this same
 * field, just not previously noticed there. That's a backend/data gap
 * (the evidence-reference isn't resolved to a sentence before this
 * page ever sees it), not something a frontend fix can correct, and
 * squarely Core -- out of this sprint's scope to touch. Rather than
 * surface it more prominently, every fact is filtered through this
 * before rendering: reference ids are colon/underscore-joined tokens
 * with no whitespace, real sentences always contain at least one
 * space, so this fails safe -- a fact that isn't real prose is simply
 * dropped, never shown as broken text, and an already-resolved sentence
 * is never filtered out incorrectly. */
export function isReadableFact(fact: string): boolean {
  return fact.includes(" ");
}

/** Product Sprint 14 (Evidence & Explanation Quality): live-testing the
 * real resolver found some findings (e.g. Growth, evaluated across a
 * company's full multi-year history) carry 20-30+ resolved facts --
 * joining every one produces an unreadable wall of text, exactly the
 * "duplicated wording" / low-signal density this sprint's own
 * Deliverable 7 warns against. The backend's own evidence-reference
 * order is a hash-string sort, not chronological -- not safe to assume
 * "first N" means "most recent N" -- so this caps to a small, still
 * genuinely representative sample rather than claiming a false
 * "most relevant" ordering it cannot back up. A future pass could sort
 * by each fact's own real `period` before this cap is applied. */
export const MAX_DISPLAYED_FACTS = 2;

export function capFacts(facts: string[]): string[] {
  return facts.slice(0, MAX_DISPLAYED_FACTS);
}

export interface AtlasReasoningInput {
  growthStatus: AnalysisBusinessStatus;
  growthFacts: ReasoningFacts;
  valuationStatus: AnalysisValuationStatus;
  valuationFacts: ReasoningFacts;
  financialHealthStatus: AnalysisRiskStatus;
  financialHealthFacts: ReasoningFacts;
  businessQualityStatus: AnalysisBusinessStatus;
  businessQualityFacts: ReasoningFacts;
}

function ReasoningCard({
  label,
  statusLabel,
  tone,
  interpretation,
  facts,
  t,
}: {
  label: string;
  statusLabel: string;
  tone: "positive" | "caution" | "critical" | "neutral";
  interpretation: string;
  facts: ReasoningFacts;
  t: Translate;
}) {
  const supporting = capFacts(facts.supporting.filter(isReadableFact));
  const contradicting = capFacts(facts.contradicting.filter(isReadableFact));

  return (
    <Stack gap="metadata" style={{ flex: "1 1 220px", minWidth: 0 }}>
      <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
        <Label>{label}</Label>
        <StatusBadge label={statusLabel} tone={tone} />
      </Inline>
      <Text as="p">{interpretation}</Text>
      {supporting.length > 0 && (
        <Text color="tertiary" as="p">
          {t("investmentCase.analysis.business.supportingLabel")}: {supporting.join(", ")}
        </Text>
      )}
      {contradicting.length > 0 && (
        <Text color="tertiary" as="p">
          {t("investmentCase.analysis.business.contradictingLabel")}: {contradicting.join(", ")}
        </Text>
      )}
    </Stack>
  );
}

export function AtlasReasoningSection({ input, t }: { input: AtlasReasoningInput; t: Translate }) {
  return (
    <Stack gap="intra-section">
      <Label>{t("investmentCase.reasoning.heading")}</Label>
      <Inline gap="inter-section" wrap align="start">
        <ReasoningCard
          label={t("investmentCase.reasoning.growthLabel")}
          statusLabel={t(BUSINESS_STATUS_KEY[input.growthStatus])}
          tone={BUSINESS_STATUS_TONE[input.growthStatus]}
          interpretation={t(GROWTH_INTERPRETATION_KEY[input.growthStatus])}
          facts={input.growthFacts}
          t={t}
        />
        <ReasoningCard
          label={t("investmentCase.reasoning.valuationLabel")}
          statusLabel={t(VALUATION_STATUS_KEY[input.valuationStatus])}
          tone={VALUATION_STATUS_TONE[input.valuationStatus]}
          interpretation={t(VALUATION_INTERPRETATION_KEY[input.valuationStatus])}
          facts={input.valuationFacts}
          t={t}
        />
        <ReasoningCard
          label={t("investmentCase.reasoning.financialHealthLabel")}
          statusLabel={t(RISK_STATUS_KEY[input.financialHealthStatus])}
          tone={RISK_STATUS_TONE[input.financialHealthStatus]}
          interpretation={t(FINANCIAL_HEALTH_INTERPRETATION_KEY[input.financialHealthStatus])}
          facts={input.financialHealthFacts}
          t={t}
        />
        <ReasoningCard
          label={t("investmentCase.reasoning.businessQualityLabel")}
          statusLabel={t(BUSINESS_STATUS_KEY[input.businessQualityStatus])}
          tone={BUSINESS_STATUS_TONE[input.businessQualityStatus]}
          interpretation={t(BUSINESS_QUALITY_INTERPRETATION_KEY[input.businessQualityStatus])}
          facts={input.businessQualityFacts}
          t={t}
        />
      </Inline>
    </Stack>
  );
}

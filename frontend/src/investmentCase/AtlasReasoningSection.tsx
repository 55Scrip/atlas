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

export interface AtlasReasoningInput {
  growthStatus: AnalysisBusinessStatus;
  valuationStatus: AnalysisValuationStatus;
  financialHealthStatus: AnalysisRiskStatus;
  businessQualityStatus: AnalysisBusinessStatus;
}

function ReasoningCard({
  label,
  statusLabel,
  tone,
  interpretation,
}: {
  label: string;
  statusLabel: string;
  tone: "positive" | "caution" | "critical" | "neutral";
  interpretation: string;
}) {
  return (
    <Stack gap="metadata" style={{ flex: "1 1 220px", minWidth: 0 }}>
      <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
        <Label>{label}</Label>
        <StatusBadge label={statusLabel} tone={tone} />
      </Inline>
      <Text as="p">{interpretation}</Text>
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
        />
        <ReasoningCard
          label={t("investmentCase.reasoning.valuationLabel")}
          statusLabel={t(VALUATION_STATUS_KEY[input.valuationStatus])}
          tone={VALUATION_STATUS_TONE[input.valuationStatus]}
          interpretation={t(VALUATION_INTERPRETATION_KEY[input.valuationStatus])}
        />
        <ReasoningCard
          label={t("investmentCase.reasoning.financialHealthLabel")}
          statusLabel={t(RISK_STATUS_KEY[input.financialHealthStatus])}
          tone={RISK_STATUS_TONE[input.financialHealthStatus]}
          interpretation={t(FINANCIAL_HEALTH_INTERPRETATION_KEY[input.financialHealthStatus])}
        />
        <ReasoningCard
          label={t("investmentCase.reasoning.businessQualityLabel")}
          statusLabel={t(BUSINESS_STATUS_KEY[input.businessQualityStatus])}
          tone={BUSINESS_STATUS_TONE[input.businessQualityStatus]}
          interpretation={t(BUSINESS_QUALITY_INTERPRETATION_KEY[input.businessQualityStatus])}
        />
      </Inline>
    </Stack>
  );
}

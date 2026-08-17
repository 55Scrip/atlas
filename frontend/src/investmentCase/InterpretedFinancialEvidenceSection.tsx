import { Inline, Label, Stack, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import type { TranslationKey } from "../i18n";
import { CHANGE_DIRECTION_SYMBOL } from "../changeIntelligence/describeChange";
import { formatFinancialValue, FinancialsTable, MISSING_VALUE_PLACEHOLDER, type FinancialPeriodView } from "./FinancialsTable";
import { deriveInterpretedFinancialRows, type FinancialMetricKey, type MetricDirection } from "./deriveFinancialInterpretation";
import { ExpandableDetail } from "./ExpandableDetail";

/**
 * Interpreted Financial Evidence (Figma-fidelity rebuild): the approved
 * design's own explicit requirement -- metric, value, direction,
 * interpretation, never a raw number alone. Rows come from
 * `deriveFinancialInterpretation.ts`, a pure read of the same
 * `financialHistory[]` this page already fetches; nothing here is a new
 * backend call or a fabricated figure. The full, dense, per-period raw
 * table (`FinancialsTable`, unchanged) moves behind an expandable
 * "Detailed Financials, Sources & Methodology" disclosure -- the
 * numbers themselves are not removed, only demoted from the primary
 * read, per the brief's own progressive-disclosure instruction.
 */

const METRIC_LABEL_KEY: Record<FinancialMetricKey, TranslationKey> = {
  revenue: "investmentCase.analysis.financials.revenueLabel",
  operatingMargin: "investmentCase.financialEvidence.operatingMarginLabel",
  freeCashFlow: "investmentCase.analysis.financials.freeCashFlowLabel",
  totalDebt: "investmentCase.analysis.financials.totalDebtLabel",
};

const INTERPRETATION_KEY: Record<FinancialMetricKey, Partial<Record<MetricDirection, TranslationKey>>> = {
  revenue: {
    up: "investmentCase.financialEvidence.revenue.up",
    down: "investmentCase.financialEvidence.revenue.down",
    flat: "investmentCase.financialEvidence.revenue.flat",
  },
  operatingMargin: {
    up: "investmentCase.financialEvidence.operatingMargin.up",
    down: "investmentCase.financialEvidence.operatingMargin.down",
    flat: "investmentCase.financialEvidence.operatingMargin.flat",
  },
  freeCashFlow: {
    up: "investmentCase.financialEvidence.freeCashFlow.up",
    down: "investmentCase.financialEvidence.freeCashFlow.down",
    flat: "investmentCase.financialEvidence.freeCashFlow.flat",
  },
  totalDebt: {
    up: "investmentCase.financialEvidence.totalDebt.up",
    down: "investmentCase.financialEvidence.totalDebt.down",
    flat: "investmentCase.financialEvidence.totalDebt.flat",
  },
};

const DIRECTION_ARROW: Record<MetricDirection, string> = {
  up: CHANGE_DIRECTION_SYMBOL.positive,
  down: CHANGE_DIRECTION_SYMBOL.negative,
  flat: CHANGE_DIRECTION_SYMBOL.neutral,
  unavailable: MISSING_VALUE_PLACEHOLDER,
};

function formatMetricValue(
  key: FinancialMetricKey,
  latestValue: number | null,
  latestMarginPercent: number | null,
  currency: string | null,
  locale: string,
): string {
  if (key === "operatingMargin") {
    return latestMarginPercent === null ? MISSING_VALUE_PLACEHOLDER : `${latestMarginPercent.toFixed(1)}%`;
  }
  return formatFinancialValue(latestValue, currency, locale);
}

export function InterpretedFinancialEvidenceSection({
  financialHistory,
  t,
  locale,
}: {
  financialHistory: FinancialPeriodView[];
  t: Translate;
  locale: string;
}) {
  const rows = deriveInterpretedFinancialRows(financialHistory);

  return (
    <Stack gap="intra-section">
      <Label>{t("investmentCase.financialEvidence.heading")}</Label>

      <Stack gap="metadata">
        {rows.map((row) => (
          <Inline key={row.key} gap="row" align="baseline" wrap>
            <Text as="span" style={{ minWidth: "9rem", fontWeight: 600 }}>
              {t(METRIC_LABEL_KEY[row.key])}
            </Text>
            <Text as="span" style={{ minWidth: "7rem", fontVariantNumeric: "tabular-nums" }}>
              <span aria-hidden="true">{DIRECTION_ARROW[row.direction]} </span>
              {formatMetricValue(row.key, row.latestValue, row.latestMarginPercent, row.currency, locale)}
            </Text>
            <Text as="span" color="secondary">
              {row.direction === "unavailable"
                ? t("investmentCase.financialEvidence.notEnoughHistory")
                : t(INTERPRETATION_KEY[row.key][row.direction]!)}
            </Text>
          </Inline>
        ))}
      </Stack>

      <ExpandableDetail summaryLabel={t("investmentCase.financialEvidence.detailedFinancialsLabel")}>
        {financialHistory.length === 0 ? (
          <Text color="secondary">{t("investmentCase.analysis.financials.empty")}</Text>
        ) : (
          <FinancialsTable periods={financialHistory} t={t} locale={locale} />
        )}
      </ExpandableDetail>
    </Stack>
  );
}

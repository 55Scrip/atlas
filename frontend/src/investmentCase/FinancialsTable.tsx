import type { CSSProperties } from "react";
import type { TranslationKey } from "../i18n";
import type { Translate } from "../changeIntelligence/describeChange";

/**
 * Workspace Migration (Foundation extraction) -- moved verbatim out of
 * `InvestmentCasePage.tsx` (Investment Case Engine v1 slice; extended
 * Company Data Foundation v1), no behavior change. Renders only real,
 * already-ingested `BusinessRecord` data (see
 * `atlas/alpha/investment_case/company_profile.py`/
 * `financial_history.py`); a missing value is always the em-dash
 * placeholder below, never rendered as 0 or blank (which would visually
 * imply zero).
 */

export interface FinancialPeriodView {
  periodStart: string | null;
  periodEnd: string | null;
  revenue: number | null;
  operatingIncome: number | null;
  netIncome: number | null;
  eps: number | null;
  freeCashFlow: number | null;
  capitalExpenditure: number | null;
  shareBuybacks: number | null;
  shareIssuance: number | null;
  dividends: number | null;
  cash: number | null;
  totalDebt: number | null;
  sharesOutstanding: number | null;
  currency: string | null;
}

export const MISSING_VALUE_PLACEHOLDER = "—";

/**
 * Integration Sprint fix: `locale` is required, not optional -- these
 * three formatters previously called `toLocaleString(undefined, ...)`,
 * which defers to the browser/OS locale rather than the app's own
 * language toggle (`useTranslation()`'s `language`). That meant a
 * Swedish-locale machine showed comma-decimal financial figures (e.g.
 * "313,3 USD") even with English explicitly selected in-app, and the
 * same page could show one figure with a comma and another with a
 * period depending on which formatter rendered it. Every call site now
 * passes the caller's own `language === "sv" ? "sv-SE" : "en-US"`
 * locale, the same pattern already established in HistoryPage.tsx/
 * DailyBriefPage.tsx/WatchlistPage.tsx.
 */
export function formatFinancialValue(value: number | null, currency: string | null, locale: string): string {
  if (value === null) return MISSING_VALUE_PLACEHOLDER;
  const formatted = value.toLocaleString(locale, { maximumFractionDigits: 1 });
  return currency ? `${formatted} ${currency}` : formatted;
}

export function formatShareCount(value: number | null, locale: string): string {
  if (value === null) return MISSING_VALUE_PLACEHOLDER;
  return value.toLocaleString(locale, { maximumFractionDigits: 0 });
}

export function formatEps(value: number | null, currency: string | null, locale: string): string {
  if (value === null) return MISSING_VALUE_PLACEHOLDER;
  const formatted = value.toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return currency ? `${formatted} ${currency}` : formatted;
}

interface FinancialsTableRow {
  labelKey: TranslationKey;
  values: (period: FinancialPeriodView) => string;
}

/** One row per metric, one column per fiscal period -- a dense,
 * analyst-file layout ("a table is acceptable and likely preferable").
 * Every cell is a direct, unevaluated read of `FinancialPeriodView`;
 * this table computes nothing itself. */
export function FinancialsTable({
  periods,
  t,
  locale,
}: {
  periods: FinancialPeriodView[];
  t: Translate;
  locale: string;
}) {
  // Newest period first, left to right -- matches how an analyst reads
  // a spreadsheet, and how the periods already arrive from the API
  // (oldest first) reversed once here rather than at the API layer.
  const newestFirst = periods.slice().reverse();

  const rows: FinancialsTableRow[] = [
    { labelKey: "investmentCase.analysis.financials.revenueLabel", values: (p) => formatFinancialValue(p.revenue, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.operatingIncomeLabel", values: (p) => formatFinancialValue(p.operatingIncome, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.netIncomeLabel", values: (p) => formatFinancialValue(p.netIncome, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.epsLabel", values: (p) => formatEps(p.eps, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.freeCashFlowLabel", values: (p) => formatFinancialValue(p.freeCashFlow, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.capitalExpenditureLabel", values: (p) => formatFinancialValue(p.capitalExpenditure, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.shareBuybacksLabel", values: (p) => formatFinancialValue(p.shareBuybacks, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.dividendsLabel", values: (p) => formatFinancialValue(p.dividends, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.cashLabel", values: (p) => formatFinancialValue(p.cash, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.totalDebtLabel", values: (p) => formatFinancialValue(p.totalDebt, p.currency, locale) },
    { labelKey: "investmentCase.analysis.financials.sharesOutstandingLabel", values: (p) => formatShareCount(p.sharesOutstanding, locale) },
  ];

  const cellStyle: CSSProperties = {
    padding: "var(--space-metadata) var(--space-row)",
    textAlign: "right",
    fontFamily: "var(--type-family-metadata)",
    fontVariantNumeric: "tabular-nums",
    whiteSpace: "nowrap",
    borderBottom: "var(--width-border-hairline) solid var(--color-border-hairline)",
  };
  const labelCellStyle: CSSProperties = {
    ...cellStyle,
    textAlign: "left",
    fontFamily: "var(--type-family-prose)",
    color: "var(--color-text-secondary)",
  };
  const headerCellStyle: CSSProperties = {
    ...cellStyle,
    fontFamily: "var(--type-family-prose)",
    fontWeight: 600,
    color: "var(--color-text-primary)",
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={{ ...headerCellStyle, textAlign: "left" }} />
            {newestFirst.map((period, index) => (
              <th key={period.periodEnd ?? index} style={headerCellStyle}>
                {period.periodEnd ?? t("investmentCase.analysis.financials.unknownPeriodLabel")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.labelKey}>
              <td style={labelCellStyle}>{t(row.labelKey)}</td>
              {newestFirst.map((period, index) => (
                <td key={period.periodEnd ?? index} style={cellStyle}>
                  {row.values(period)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

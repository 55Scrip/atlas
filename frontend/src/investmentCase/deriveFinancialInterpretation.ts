/**
 * Interpreted Financial Evidence (Figma-fidelity rebuild): pure
 * derivation turning `financialHistory[]` -- already fetched, already
 * real, previously shown only as a raw, uninterpreted table -- into the
 * metric/value/direction/interpretation rows the approved design
 * requires. No new backend call, no fabricated figure: every value here
 * is read straight from the two most recent real periods already on the
 * wire, and every direction is a plain comparison between them, never a
 * scored or weighted judgment (`DE-004` §5's categorical-not-numeric
 * discipline, applied to a new surface for the first time by direct
 * analogy).
 */

import type { FinancialPeriodView } from "./FinancialsTable";

export type FinancialMetricKey = "revenue" | "operatingMargin" | "freeCashFlow" | "totalDebt";
export type MetricDirection = "up" | "down" | "flat" | "unavailable";

export interface InterpretedFinancialRow {
  key: FinancialMetricKey;
  direction: MetricDirection;
  latestValue: number | null;
  currency: string | null;
  /** Operating margin only -- a computed percentage (operatingIncome /
   * revenue), never rendered as a raw currency value. */
  latestMarginPercent: number | null;
}

const DIRECTION_EPSILON = 0.005; // 0.5% relative change treated as "flat"

function compareDirection(latest: number | null, prior: number | null): MetricDirection {
  if (latest === null || prior === null) return "unavailable";
  if (prior === 0) return latest === 0 ? "flat" : latest > 0 ? "up" : "down";
  const relativeChange = (latest - prior) / Math.abs(prior);
  if (Math.abs(relativeChange) < DIRECTION_EPSILON) return "flat";
  return relativeChange > 0 ? "up" : "down";
}

function operatingMargin(period: FinancialPeriodView | undefined): number | null {
  if (!period || period.operatingIncome === null || period.revenue === null || period.revenue === 0) return null;
  return (period.operatingIncome / period.revenue) * 100;
}

/**
 * `financialHistory` arrives from the API **oldest-first** -- the same
 * ordering `FinancialsTable` itself reverses once, locally, before
 * rendering ("periods already arrive from the API (oldest first)
 * reversed once here"). This derivation reads directly from the raw,
 * oldest-first array, so the latest real period is the *last* element,
 * not the first. Requires at least two real periods to state a
 * direction; a single period, or two periods missing the specific
 * field, produces `"unavailable"` honestly rather than a guessed
 * direction.
 */
export function deriveInterpretedFinancialRows(financialHistory: FinancialPeriodView[]): InterpretedFinancialRow[] {
  const latest = financialHistory[financialHistory.length - 1];
  const prior = financialHistory[financialHistory.length - 2];
  const currency = latest?.currency ?? null;

  return [
    {
      key: "revenue",
      direction: compareDirection(latest?.revenue ?? null, prior?.revenue ?? null),
      latestValue: latest?.revenue ?? null,
      currency,
      latestMarginPercent: null,
    },
    {
      key: "operatingMargin",
      direction: compareDirection(operatingMargin(latest), operatingMargin(prior)),
      latestValue: null,
      currency: null,
      latestMarginPercent: operatingMargin(latest),
    },
    {
      key: "freeCashFlow",
      direction: compareDirection(latest?.freeCashFlow ?? null, prior?.freeCashFlow ?? null),
      latestValue: latest?.freeCashFlow ?? null,
      currency,
      latestMarginPercent: null,
    },
    {
      key: "totalDebt",
      direction: compareDirection(latest?.totalDebt ?? null, prior?.totalDebt ?? null),
      latestValue: latest?.totalDebt ?? null,
      currency,
      latestMarginPercent: null,
    },
  ];
}

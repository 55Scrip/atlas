import { KNOWN_COMPANY_TICKERS } from "./companyTickerMap";
import type { ParsedRow, ReconcileResult } from "./types";

const TICKER_SHAPE_PATTERN = /^[A-Za-z]{1,5}(\.[A-Za-z]{1,2})?$/;

/**
 * Deterministic name -> ticker resolution. Exactly two rules, checked in
 * order, nothing fuzzy:
 *
 * 1. Exact, case-insensitive lookup against the maintained dictionary in
 *    `companyTickerMap.ts` ("Microsoft" -> "MSFT").
 * 2. If that fails, and the pasted text already has the shape of a plain
 *    ticker (1-5 letters, optionally a "." and a one/two-letter share
 *    class suffix like "BRK.B") — accept it as-is. This is what keeps
 *    pasting a raw ticker ("AMD 40") working exactly as it did in v1.
 *    It never runs *before* the dictionary check, so a short company
 *    name that happens to look ticker-shaped ("Visa") still resolves to
 *    its real ticker ("V") instead of being misread as the literal
 *    string "VISA".
 *
 * Anything that clears neither rule is left unresolved — never guessed.
 */
export function resolveNameToTicker(
  name: string,
): { ticker: string; mappingStatus: "known" } | { ticker: null; mappingStatus: "unknown" } {
  const trimmed = name.trim();
  const dictionaryHit = KNOWN_COMPANY_TICKERS[trimmed.toLowerCase()];
  if (dictionaryHit) return { ticker: dictionaryHit, mappingStatus: "known" };
  if (TICKER_SHAPE_PATTERN.test(trimmed)) return { ticker: trimmed.toUpperCase(), mappingStatus: "known" };
  return { ticker: null, mappingStatus: "unknown" };
}

/**
 * Cross-row reconciliation: applies any manually-typed ticker
 * corrections, then (re-)runs duplicate-ticker detection across the
 * whole set — a manual correction can introduce a collision exactly as
 * an auto-resolved ticker can, so this always re-checks from scratch
 * rather than trusting a stale result. Pure function, safe to call on
 * every keystroke in the confirmation input.
 */
export function reconcileRows(rows: ParsedRow[], manualTickers: Record<number, string>): ReconcileResult {
  const withOverrides = rows.map((row) => {
    if (row.errorCode !== null || row.ticker !== null) return row;
    const manual = manualTickers[row.lineNumber]?.trim();
    if (!manual) return row;
    return { ...row, ticker: manual.toUpperCase(), mappingStatus: "known" as const };
  });

  const seenTickers = new Set<string>();
  const withDuplicates = withOverrides.map((row) => {
    if (row.errorCode !== null || row.ticker === null) return row;
    if (seenTickers.has(row.ticker)) {
      return { ...row, errorCode: "duplicate-ticker" as const, weightPercent: null };
    }
    seenTickers.add(row.ticker);
    return row;
  });

  const readyHoldings = withDuplicates
    .filter(
      (row): row is ParsedRow & { ticker: string; weightPercent: number } =>
        row.errorCode === null && row.ticker !== null && row.weightPercent !== null,
    )
    .map((row) => ({ ticker: row.ticker, weightPercent: row.weightPercent }));

  const errorCount = withDuplicates.filter((row) => row.errorCode !== null).length;
  const needsConfirmationCount = withDuplicates.filter(
    (row) => row.errorCode === null && row.ticker === null,
  ).length;

  const canImport =
    withDuplicates.length > 0 && errorCount === 0 && needsConfirmationCount === 0 && readyHoldings.length > 0;

  return { rows: withDuplicates, readyHoldings, errorCount, needsConfirmationCount, canImport };
}

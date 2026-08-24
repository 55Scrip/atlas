import { lookupInstrument, type InstrumentType } from "./instrumentRegistry";
import type { ParsedRow, ReconcileResult } from "./types";

const TICKER_SHAPE_PATTERN = /^[A-Za-z]{1,5}([.-][A-Za-z]{1,2})?$/;

/**
 * True only for text that has BOTH the shape of a ticker (short,
 * letters, optional one/two-letter share-class suffix like "BRK.B" or,
 * the Nordic exchange convention, "VOLV-B"/"ATCO-B"/"HM-B"/"INVE-B")
 * AND is written in the all-uppercase form a person uses when they
 * mean to paste a literal ticker symbol ("AMD", "MSFT", "NVDA",
 * "BRK.B", "VOLV-B"). Shape alone is not enough: "Volvo" (5 letters)
 * has the same shape as a ticker but is Title Case, exactly how it
 * appears on every broker statement — under a shape-only check it
 * would silently become the fabricated ticker "VOLVO", which is the
 * root cause this sprint exists to fix. Requiring the input to already
 * be uppercase is the smallest deterministic signal available (no
 * ticker database, no fuzzy logic) that distinguishes "the investor is
 * telling me this is a ticker" from "the investor pasted a company
 * name that happens to be short."
 *
 * Import Robustness (Internal Alpha Stabilization 1): the share-class
 * suffix originally only matched the US dot convention ("BRK.B"), so a
 * raw, correctly-formatted Swedish ticker pasted directly (e.g. from a
 * brokerage export) fell through to "needs confirmation" even though
 * it was already an unambiguous, literal ticker — real friction for
 * this app's actually Swedish-heavy real usage. Both suffix forms are
 * accepted now; nothing else about the two-rule resolution above
 * changes.
 */
function looksLikeExplicitTickerInput(trimmed: string): boolean {
  return TICKER_SHAPE_PATTERN.test(trimmed) && trimmed === trimmed.toUpperCase();
}

export type ResolvedIdentity =
  | { kind: "resolved"; ticker: string; instrumentType: InstrumentType }
  | { kind: "unsupported"; instrumentType: InstrumentType }
  | { kind: "unresolved" };

/**
 * Deterministic name -> instrument resolution. Exactly two rules,
 * checked in order, nothing fuzzy — no contains(), no substring
 * matching, no similarity scoring:
 *
 * 1. Exact, case-insensitive lookup against the maintained registry in
 *    `instrumentRegistry.ts`. A registry hit with a ticker resolves
 *    normally. A registry hit with `ticker: null` (a fund, ETP, or
 *    private company the current backend can't represent as an equity
 *    holding) comes back as "unsupported" — a known identity that
 *    still can't safely become a ticker, never a fabricated one.
 * 2. If that fails, and the pasted text is both ticker-shaped *and*
 *    already in the all-caps form a person uses to mean a literal
 *    ticker — accept it as-is, exactly as v1 did for "AMD 40". This
 *    never fires for a Title Case company name, mapped or not, so an
 *    unmapped short name is left unresolved instead of guessed at.
 *
 * Anything that clears neither rule is left unresolved.
 */
export function resolveInstrument(name: string): ResolvedIdentity {
  const trimmed = name.trim();

  const registryHit = lookupInstrument(trimmed);
  if (registryHit) {
    if (registryHit.ticker) {
      return { kind: "resolved", ticker: registryHit.ticker, instrumentType: registryHit.instrumentType };
    }
    return { kind: "unsupported", instrumentType: registryHit.instrumentType };
  }

  if (looksLikeExplicitTickerInput(trimmed)) {
    return { kind: "resolved", ticker: trimmed, instrumentType: "equity" };
  }

  return { kind: "unresolved" };
}

// ATLAS-015A: the manual-entry field applies on every keystroke (a
// controlled input, not a submit-on-blur/Enter one), so without a
// floor here, a person who starts typing "AAPL" and clicks "Import
// Portfolio" after only the first character is already, silently,
// "resolved" -- exactly how single-letter holdings ("A", "B", "C"...)
// reached persistence during Alpha testing (root cause: this line had
// no length check at all). Real single-character tickers do exist
// (Visa's "V", Ford's "F"), so this can't reject on shape -- it rejects
// on incompleteness instead: a one-character manual entry is far more
// likely to be typing-in-progress than a deliberately confirmed
// identity, so it's treated as not-yet-resolved (the row keeps showing
// "needs confirmation") rather than accepted. The same "a false
// automatic match is worse than an unresolved row" principle every
// other resolution rule in this module already follows -- this is a
// real, disclosed limitation (see PortfolioPage.tsx / the sprint
// report), not a silent gap: a genuine single-letter-ticker holding
// currently cannot be manually confirmed and stays "needs
// confirmation" until entered with a 2-plus character form.
const MIN_MANUAL_TICKER_LENGTH = 2;

/**
 * Cross-row reconciliation: applies any manually-typed ticker
 * corrections, then (re-)runs duplicate-ticker detection across the
 * whole set — after resolution, not before, so "Microsoft" and "MSFT"
 * (or "Meta Platforms A" and "META") collide correctly even though
 * they arrived through different resolution paths. A manual correction
 * can introduce a collision exactly as an auto-resolved ticker can, so
 * this always re-checks from scratch rather than trusting a stale
 * result. Pure function, safe to call on every keystroke in the
 * confirmation input.
 */
export function reconcileRows(rows: ParsedRow[], manualTickers: Record<number, string>): ReconcileResult {
  const withOverrides = rows.map((row) => {
    if (row.errorCode !== null || row.ticker !== null) return row;
    const manual = manualTickers[row.lineNumber]?.trim();
    if (!manual || manual.length < MIN_MANUAL_TICKER_LENGTH) return row;
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

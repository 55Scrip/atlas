import type { InstrumentType } from "./instrumentRegistry";

/**
 * Portfolio Import v1.2 — shared types for the deterministic parser and
 * name-to-instrument resolution.
 *
 * The backend's `AlphaHolding` still has only `weight_percent` (required)
 * and `value_absolute` (optional) — no `quantity`/`shares` field exists
 * anywhere in `atlas/alpha/portfolio/models.py`. Nothing about that
 * changed in this sprint, so the numeric value here is still always a
 * **weight percentage**, never a share count.
 *
 * v1.1 could resolve a name to a ticker or leave it unresolved. v1.2
 * adds a third outcome: a name can be a *recognized but unsupported*
 * instrument — identity known (via `instrumentRegistry.ts`), but not a
 * plain listed equity the current backend can honestly persist as
 * ticker + weight (a fund, an ETP, a private company). `ticker` stays
 * `null` for both "unknown" and "unsupported" — never a fabricated
 * ticker — while `mappingStatus` and `instrumentType` tell the review
 * screen which one it is and why.
 */

export type ImportRowErrorCode =
  | "missing-name"
  | "missing-value"
  | "invalid-value"
  | "non-positive-value"
  | "duplicate-ticker"
  | "too-many-columns";

/** How `ticker` came to be set — or, if it's still `null`, why not.
 *  Stays `null` while `errorCode` is set — a row with a parse error
 *  never reaches the resolution step. "unsupported" means the identity
 *  is known (see `instrumentType`) but isn't a plain equity. */
export type MappingStatus = "known" | "unknown" | "unsupported";

export interface ParsedRow {
  lineNumber: number;
  raw: string;
  originalName: string | null;
  ticker: string | null;
  mappingStatus: MappingStatus | null;
  /** Populated whenever an instrument was recognized — resolved or
   *  unsupported — `null` for "unknown" and for parse-error rows. */
  instrumentType: InstrumentType | null;
  weightPercent: number | null;
  errorCode: ImportRowErrorCode | null;
}

export interface ParseResult {
  /** Every non-blank input row, including the skipped header row if one
   * was detected. Duplicate detection has *not* run yet — see
   * `reconcileRows` in `resolution.ts`, which re-runs it every time a
   * manual ticker correction changes what's resolved. */
  rows: ParsedRow[];
  headerDetected: boolean;
}

export interface ReadyHolding {
  ticker: string;
  weightPercent: number;
}

export interface ReconcileResult {
  /** Same rows as `ParseResult.rows`, with manual ticker overrides
   * applied and duplicate tickers (re-)detected. */
  rows: ParsedRow[];
  /** Rows with no error and a resolved ticker — safe to send to the
   * import API, in original order. */
  readyHoldings: ReadyHolding[];
  errorCount: number;
  /** Rows that parsed cleanly but have no resolved ticker yet. Each one
   * blocks import until the investor types a ticker in for it. */
  needsConfirmationCount: number;
  canImport: boolean;
}

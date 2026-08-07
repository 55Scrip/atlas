/**
 * Portfolio Import v1.1 — shared types for the deterministic parser and
 * name-to-ticker resolution.
 *
 * The backend's `AlphaHolding` still has only `weight_percent` (required)
 * and `value_absolute` (optional) — no `quantity`/`shares` field exists
 * anywhere in `atlas/alpha/portfolio/models.py`. Nothing about that
 * changed in this sprint, so the numeric value here is still always a
 * **weight percentage**, never a share count.
 *
 * v1 could only accept a literal ticker in the first column. v1.1 accepts
 * either a ticker or a company name — `originalName` always holds exactly
 * what the investor pasted, verbatim; `ticker` holds the resolved ticker
 * once one is known (automatically, via the dictionary in
 * `companyTickerMap.ts`, or because a person typed it in after being
 * asked to confirm), or `null` while it's still unresolved.
 */

export type ImportRowErrorCode =
  | "missing-name"
  | "missing-value"
  | "invalid-value"
  | "non-positive-value"
  | "duplicate-ticker"
  | "too-many-columns";

/** How `ticker` came to be set. Stays `null` while `errorCode` is set —
 *  a row with a parse error never reaches the mapping step. */
export type MappingStatus = "known" | "unknown";

export interface ParsedRow {
  lineNumber: number;
  raw: string;
  originalName: string | null;
  ticker: string | null;
  mappingStatus: MappingStatus | null;
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

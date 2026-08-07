/**
 * Portfolio Import v1 — shared types for the deterministic parser.
 *
 * The backend's `AlphaHolding` has only `weight_percent` (required) and
 * `value_absolute` (optional) — no `quantity`/`shares` field exists
 * anywhere in `atlas/alpha/portfolio/models.py`, its request schemas,
 * or its persisted storage (confirmed by direct repository read before
 * writing this module). So the numeric value parsed here is always a
 * **weight percentage** — never a share count — and every type name
 * below says so explicitly, to make it structurally impossible for a
 * later screen to relabel it as something the backend cannot honestly
 * back.
 */

export type ImportRowErrorCode =
  | "missing-ticker"
  | "missing-value"
  | "invalid-value"
  | "non-positive-value"
  | "duplicate-ticker"
  | "too-many-columns";

export interface ParsedRow {
  lineNumber: number;
  raw: string;
  ticker: string | null;
  weightPercent: number | null;
  errorCode: ImportRowErrorCode | null;
}

export interface ParsedHolding {
  ticker: string;
  weightPercent: number;
}

export interface ParseResult {
  /** Every non-blank input row, including the skipped header row if
   * one was detected — the caller never has to guess what happened to
   * a line the user pasted. */
  rows: ParsedRow[];
  /** Only rows with no error, in original order, duplicates already
   * excluded — safe to send directly to the import API. */
  validHoldings: ParsedHolding[];
  /** Same length as `rows.filter(r => r.errorCode !== null)` — kept as
   * its own field so callers don't need to re-filter to gate
   * confirmation. */
  errorCount: number;
  headerDetected: boolean;
}

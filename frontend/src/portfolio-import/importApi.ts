/**
 * Zero-Effort Portfolio Onboarding -- the frontend client for the
 * unified backend import pipeline. Every entry method (paste, broker-
 * guided paste, CSV, manual) ends up calling `previewImport` with a
 * plain text blob; the backend owns all parsing, resolution, and
 * duplicate detection (`atlas.alpha.portfolio_import`). This module
 * never parses or resolves anything itself.
 */

export type RowStatus = "RESOLVED" | "AMBIGUOUS" | "UNRESOLVED" | "DUPLICATE" | "ERROR";

export interface ResolutionCandidate {
  ticker: string;
  displayName: string;
}

export interface ParsedHoldingRow {
  lineNumber: number;
  raw: string;
  originalName: string | null;
  ticker: string | null;
  quantity: number | null;
  price: number | null;
  valueAbsolute: number | null;
  weightPercent: number | null;
  currency: string | null;
  status: RowStatus;
  message: string | null;
  candidates: ResolutionCandidate[];
  alreadyHeld: boolean;
}

export interface ImportPreview {
  rows: ParsedHoldingRow[];
  headerDetected: boolean;
  holdingsFound: number;
  resolvedCount: number;
  needsReview: boolean;
  currencyConflict: boolean;
}

async function parseJsonOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Backend responded with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function previewImport(rawText: string): Promise<ImportPreview> {
  return fetch("/api/alpha-portfolio/import/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rawText }),
  }).then((response) => parseJsonOrThrow<ImportPreview>(response));
}

export interface ConfirmHolding {
  ticker: string;
  quantity: number | null;
  price: number | null;
  valueAbsolute: number | null;
  weightPercent: number | null;
  currency: string | null;
}

export interface ConfirmImportResult {
  batchId: string | null;
}

/** Row -> holding, applying any manual/candidate ticker override the
 * review screen collected. Rows with no resolvable ticker are excluded
 * by the caller before this ever runs. */
export function toConfirmHolding(row: ParsedHoldingRow, tickerOverride?: string): ConfirmHolding {
  return {
    ticker: tickerOverride ?? row.ticker ?? "",
    quantity: row.quantity,
    price: row.price,
    valueAbsolute: row.valueAbsolute,
    weightPercent: row.weightPercent,
    currency: row.currency,
  };
}

/** Confirms an import -- `/import` for a brand-new portfolio, `/reconcile`
 * (REPLACE_ALLOCATION) for an existing one, mirroring the exact routing
 * the old `PortfolioImportPage` already established. */
export function confirmImport(holdings: ConfirmHolding[], isReplace: boolean): Promise<ConfirmImportResult> {
  const body = isReplace
    ? { mode: "REPLACE_ALLOCATION", holdings, cashWeightPercent: null, cashValueAbsolute: null }
    : { holdings, cashWeightPercent: null, cashValueAbsolute: null, preferencesNotes: null };
  const endpoint = isReplace ? "/api/alpha-portfolio/reconcile" : "/api/alpha-portfolio/import";
  return fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((response) => parseJsonOrThrow<ConfirmImportResult>(response));
}

export interface EnrichmentProgress {
  exists: boolean;
  total: number;
  doneCount: number;
  currentlyAnalyzing: string | null;
  complete: boolean;
}

export function fetchEnrichmentProgress(batchId: string): Promise<EnrichmentProgress> {
  return fetch(`/api/enrichment-progress/${encodeURIComponent(batchId)}`).then((response) =>
    parseJsonOrThrow<EnrichmentProgress>(response),
  );
}

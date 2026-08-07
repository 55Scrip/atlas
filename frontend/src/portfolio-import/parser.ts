import type { ImportRowErrorCode, ParsedRow, ParseResult } from "./types";

/**
 * Portfolio Import v1 — deterministic parser.
 *
 * Pure function: raw pasted text in, a structured `ParseResult` out.
 * Never touches application state, never calls the network, never
 * silently drops a malformed row — every non-blank input line becomes
 * exactly one entry in `rows`, whether it parsed cleanly or not, so
 * the review screen can always show the user precisely what happened
 * to every line they pasted.
 *
 * Supported per-line delimiters, auto-detected independently per line
 * (comma takes priority, then semicolon, then any run of whitespace) —
 * covers "AMD 120", "AMD,120", and "AMD;120" with the same logic, no
 * per-format branching needed elsewhere.
 *
 * No fuzzy matching, no company-name resolution, no LLM: a ticker is
 * whatever token appears in the first column, trimmed and
 * uppercased — nothing is looked up or guessed.
 */

const NUMERIC_PATTERN = /^-?\d+(\.\d+)?$/;

function splitColumns(line: string): string[] {
  if (line.includes(",")) return line.split(",").map((part) => part.trim());
  if (line.includes(";")) return line.split(";").map((part) => part.trim());
  return line.trim().split(/\s+/);
}

/**
 * Explicit, deterministic header recognition — an allowlist, not a
 * "second column isn't a number" heuristic. That heuristic would treat
 * any malformed first data row (e.g. "AMD abc") as a silently-skipped
 * header instead of a reported error, which this sprint's own
 * hardening pass specifically forbids. A line is a header only when
 * BOTH columns, trimmed and case-insensitively compared, exactly match
 * one of these known label sets — a genuine data row's first column is
 * never one of these words, so this never misfires on real holdings.
 */
const HEADER_FIRST_COLUMN_LABELS = new Set(["ticker", "symbol"]);
const HEADER_SECOND_COLUMN_LABELS = new Set([
  "weight",
  "weight %",
  "allocation",
  "allocation %",
  "weightpercent",
]);

function looksLikeHeader(columns: string[]): boolean {
  if (columns.length !== 2) return false;
  const first = (columns[0] ?? "").trim().toLowerCase();
  const second = (columns[1] ?? "").trim().toLowerCase();
  return HEADER_FIRST_COLUMN_LABELS.has(first) && HEADER_SECOND_COLUMN_LABELS.has(second);
}

export function parsePortfolioText(raw: string): ParseResult {
  const lines = raw.split("\n");
  const rows: ParsedRow[] = [];
  let headerDetected = false;
  let sawFirstNonBlankLine = false;

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();
    if (trimmedLine === "") return; // blank rows ignored, never reported as errors

    const lineNumber = index + 1;
    const columns = splitColumns(trimmedLine);

    if (!sawFirstNonBlankLine) {
      sawFirstNonBlankLine = true;
      if (looksLikeHeader(columns)) {
        headerDetected = true;
        return; // header row is skipped entirely, not reported as a row
      }
    }

    rows.push(parseRow(lineNumber, trimmedLine, columns));
  });

  const seenTickers = new Set<string>();
  for (const row of rows) {
    if (row.errorCode !== null || row.ticker === null) continue;
    if (seenTickers.has(row.ticker)) {
      row.errorCode = "duplicate-ticker";
      row.weightPercent = null;
      continue;
    }
    seenTickers.add(row.ticker);
  }

  const validHoldings = rows
    .filter((row): row is ParsedRow & { ticker: string; weightPercent: number } =>
      row.errorCode === null && row.ticker !== null && row.weightPercent !== null,
    )
    .map((row) => ({ ticker: row.ticker, weightPercent: row.weightPercent }));

  const errorCount = rows.filter((row) => row.errorCode !== null).length;

  return { rows, validHoldings, errorCount, headerDetected };
}

function parseRow(lineNumber: number, raw: string, columns: string[]): ParsedRow {
  const base = { lineNumber, raw, ticker: null, weightPercent: null, errorCode: null } as ParsedRow;

  if (columns.length > 2) {
    return { ...base, errorCode: "too-many-columns" as ImportRowErrorCode };
  }
  if (columns.length === 1) {
    const ticker = (columns[0] ?? "").toUpperCase();
    return { ...base, ticker: ticker === "" ? null : ticker, errorCode: "missing-value" as ImportRowErrorCode };
  }

  const tickerColumn = columns[0] ?? "";
  const valueColumn = columns[1] ?? "";
  const ticker = tickerColumn.toUpperCase();

  if (ticker === "") {
    return { ...base, errorCode: "missing-ticker" as ImportRowErrorCode };
  }
  if (!NUMERIC_PATTERN.test(valueColumn)) {
    return { ...base, ticker, errorCode: "invalid-value" as ImportRowErrorCode };
  }

  const weightPercent = Number.parseFloat(valueColumn);
  if (weightPercent <= 0) {
    return { ...base, ticker, weightPercent, errorCode: "non-positive-value" as ImportRowErrorCode };
  }

  return { ...base, ticker, weightPercent, errorCode: null };
}

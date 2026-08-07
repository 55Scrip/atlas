import type { ImportRowErrorCode, ParsedRow, ParseResult } from "./types";
import { resolveInstrument } from "./resolution";

/**
 * Portfolio Import v1.2 — deterministic parser.
 *
 * Pure function: raw pasted text in, a structured `ParseResult` out.
 * Never touches application state, never calls the network, never
 * silently drops a malformed row — every non-blank input line becomes
 * exactly one entry in `rows`, whether it parsed cleanly or not, so the
 * review screen can always show the user precisely what happened to
 * every line they pasted.
 *
 * Per-line delimiters, checked in this order:
 *  1. Tab.
 *  2. A dash ("-", en dash "–", em dash "—") flanked by
 *     whitespace on both sides — covers "Microsoft – 6,14%" (the
 *     broker-copied form this sprint targets) without ever misreading
 *     punctuation *inside* a name ("Amazon.com" has no dash at all, so
 *     this rule never touches it).
 *  3. Semicolon — checked before comma because comma alone is
 *     ambiguous (it's also the decimal separator, "3,2%"), while
 *     semicolon never is.
 *  4. Comma.
 *  5. Any run of whitespace — and if that produces more than two
 *     tokens ("Meta Platforms 40"), the *last* token is the value and
 *     everything before it, rejoined with single spaces, is the name.
 *     That's a fixed column-parsing rule, not a guess about what the
 *     name refers to — it only applies when no other delimiter is
 *     present at all.
 *
 * The value column accepts a trailing "%" and either a decimal point or
 * a decimal comma ("6.14", "6,14", "6.14%", "6,14%") — both are
 * normalized to a plain float string before parsing; nothing else about
 * the text is touched.
 *
 * The name column is never uppercased or altered — `originalName` is
 * always exactly what was pasted, verbatim. Resolving it to an
 * instrument (or leaving it unresolved for manual confirmation) is
 * `resolveInstrument`'s job, not this parser's — see `resolution.ts`
 * and `instrumentRegistry.ts`. No fuzzy matching, no company-name
 * guessing, no LLM: every resolution is either an exact registry hit
 * or an explicitly all-caps, ticker-shaped token — never a short
 * company name accepted purely because it resembles one.
 */

const NUMERIC_PATTERN = /^-?\d+(\.\d+)?$/;
const DASH_DELIMITER_PATTERN = /\s[-–—]\s/;

function splitColumns(line: string): string[] {
  if (line.includes("\t")) return line.split("\t").map((part) => part.trim());
  if (DASH_DELIMITER_PATTERN.test(line)) return line.split(DASH_DELIMITER_PATTERN).map((part) => part.trim());
  // Semicolon is checked before comma: comma alone is ambiguous — it's
  // also the decimal separator ("3,2%") — while semicolon never is, so
  // a line that uses semicolon as its field delimiter must be split on
  // it even when a decimal comma also appears later in the line.
  if (line.includes(";")) return line.split(";").map((part) => part.trim());
  if (line.includes(",")) return line.split(",").map((part) => part.trim());
  const tokens = line.trim().split(/\s+/);
  if (tokens.length <= 2) return tokens;
  return [tokens.slice(0, -1).join(" "), tokens[tokens.length - 1] ?? ""];
}

function normalizeWeightText(raw: string): string {
  return raw.replace(/%/g, "").trim().replace(",", ".").trim();
}

/**
 * Explicit, deterministic header recognition — an allowlist, not a
 * heuristic. Unchanged from v1's own hardening pass: a line is a header
 * only when both columns, trimmed and case-insensitively compared,
 * exactly match one of these known label sets.
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

  return { rows, headerDetected };
}

function parseRow(lineNumber: number, raw: string, columns: string[]): ParsedRow {
  const base = {
    lineNumber,
    raw,
    originalName: null,
    ticker: null,
    mappingStatus: null,
    instrumentType: null,
    weightPercent: null,
    errorCode: null,
  } as ParsedRow;

  if (columns.length > 2) {
    return { ...base, errorCode: "too-many-columns" as ImportRowErrorCode };
  }
  if (columns.length === 1) {
    const name = columns[0] ?? "";
    return { ...base, originalName: name === "" ? null : name, errorCode: "missing-value" as ImportRowErrorCode };
  }

  const nameColumn = columns[0] ?? "";
  const valueColumn = columns[1] ?? "";

  if (nameColumn === "") {
    return { ...base, errorCode: "missing-name" as ImportRowErrorCode };
  }

  const normalizedValue = normalizeWeightText(valueColumn);
  if (!NUMERIC_PATTERN.test(normalizedValue)) {
    return { ...base, originalName: nameColumn, errorCode: "invalid-value" as ImportRowErrorCode };
  }

  const weightPercent = Number.parseFloat(normalizedValue);
  if (weightPercent <= 0) {
    return {
      ...base,
      originalName: nameColumn,
      weightPercent,
      errorCode: "non-positive-value" as ImportRowErrorCode,
    };
  }

  const resolution = resolveInstrument(nameColumn);
  const ticker = resolution.kind === "resolved" ? resolution.ticker : null;
  const mappingStatus =
    resolution.kind === "resolved" ? "known" : resolution.kind === "unsupported" ? "unsupported" : "unknown";
  const instrumentType = resolution.kind === "unresolved" ? null : resolution.instrumentType;

  return {
    ...base,
    originalName: nameColumn,
    ticker,
    mappingStatus,
    instrumentType,
    weightPercent,
    errorCode: null,
  };
}

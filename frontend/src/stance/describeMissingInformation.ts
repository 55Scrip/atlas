/**
 * Why Atlas is short of something, said where the investor reads the
 * conclusion -- not six thousand lines below it.
 *
 * The Case already carried both halves of this. `stance.missingInformation`
 * is a list of dimension names and is what the hero has always shown:
 * "Atlas is still missing: FCF Yield (Relative), Financial, Valuation".
 * `explanation.missingEvidence` is the same dimensions with a `reasoning`
 * array on each, and for ASSA-B that array says `industry_unknown` -- the
 * precise, already-translated fact that Financial Risk cannot conclude
 * because no source classifies a Stockholm listing. It was rendered, with
 * the right words, by `ExplanationPanel`, near the bottom of a page of
 * several thousand lines.
 *
 * The difference is not cosmetic. "Financial" reads as though Atlas is
 * missing financial statements or has a broken pipeline; Atlas has four
 * years of ASSA-B's audited accounts. "The company's industry is unknown"
 * says what is actually true and what would resolve it.
 *
 * This module only joins the two lists. No reason is written here, none is
 * inferred, and a dimension with nothing to say keeps exactly the copy it
 * had before.
 */

import { coverageDimensionLabel, coverageReasonLabel } from "../coverage/describeCoverage";
import type { Translate } from "../changeIntelligence/describeChange";

/** The shape `explanation.missingEvidence` already arrives in. */
export interface DimensionGap {
  dimension: string;
  reasoning: readonly string[];
}

export interface MissingInformationLine {
  /** Every dimension this one reason accounts for, in the order the
   * stance listed them. */
  dimensions: readonly string[];
  /** Already translated, or `null` when the Case offers no reason for
   * this dimension -- in which case the line is just the dimension, as
   * it always was. */
  reason: string | null;
}

/**
 * One line per distinct reason.
 *
 * Dimensions that share a reason share a line: three gaps all caused by an
 * unverified industry classification are one fact about the company, and
 * saying it three times makes a short summary look like a wall without
 * adding anything. Dimensions with genuinely different reasons stay apart,
 * because that difference is the whole point of showing reasons at all.
 *
 * `reasoning[0]` is the reason used -- the same choice `ExplanationPanel`
 * and `MaterialityPanel` already make, so the hero and the detail below it
 * cannot disagree.
 */
export function describeMissingInformation(
  dimensions: readonly string[],
  gaps: readonly DimensionGap[],
  t: Translate,
): MissingInformationLine[] {
  const reasonByDimension = new Map<string, string | null>();
  for (const gap of gaps) {
    reasonByDimension.set(gap.dimension, gap.reasoning[0] ?? null);
  }

  const lines: MissingInformationLine[] = [];
  const lineByReason = new Map<string, MissingInformationLine>();
  for (const dimension of dimensions) {
    const code = reasonByDimension.get(dimension) ?? null;
    // An unreasoned dimension never merges with another: there is no
    // shared fact to merge on, only a shared absence.
    if (code === null) {
      lines.push({ dimensions: [dimension], reason: null });
      continue;
    }
    const existing = lineByReason.get(code);
    if (existing) {
      (existing.dimensions as string[]).push(dimension);
      continue;
    }
    // `coverageReasonLabel` translates every gap kind Atlas defines and
    // humanises anything it does not recognise, so a reason code from a
    // later build degrades to readable words rather than to `snake_case`
    // or to a crash.
    const line: MissingInformationLine = { dimensions: [dimension], reason: coverageReasonLabel(dimension, code, t) };
    lineByReason.set(code, line);
    lines.push(line);
  }
  return lines;
}

/** "Financial risk, Valuation" -- the dimensions of one line. */
export function describeLineDimensions(line: MissingInformationLine, t: Translate): string {
  return line.dimensions.map((dimension) => coverageDimensionLabel(dimension, t)).join(", ");
}

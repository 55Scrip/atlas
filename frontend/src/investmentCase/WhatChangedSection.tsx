import { Stack, StatusText, Text, Label } from "../foundation";
import {
  CHANGE_DIRECTION_SYMBOL,
  describeChange,
  THESIS_IMPACT_KEY,
  type AnalysisChangeDirection,
  type AnalysisThesisImpact,
  type ChangeFindingView,
  type Translate,
} from "../changeIntelligence/describeChange";
import { isReadableFact, type ReasoningFacts } from "./AtlasReasoningSection";

/** Product Sprint 14 (Evidence & Explanation Quality, Deliverable 3 --
 * Explain Why Things Changed): a `ChangeFinding` only ever carries the
 * enum status transition (e.g. "moderate" -> "weak") plus a bare
 * dimension label -- confirmed by tracing `investment_case_change.py`'s
 * own construction code: `evidence_references` is hardcoded empty at
 * every call site, and no numeric delta is computed anywhere for these
 * categories. There is genuinely nothing more to say about *why* a
 * change happened without inventing it.
 *
 * What IS real and already on this same page: the CURRENT finding for
 * that same dimension (`analysis.businessAnalysis`/`.risk`/`.valuation`,
 * already fetched) carries its own real supporting/contradicting facts
 * -- the same ones `AtlasReasoningSection` above already resolves and
 * shows. Appending the current one here answers a different, honest
 * question than "why did it change": "what's the evidence behind where
 * it stands now" -- grounded, not fabricated, and only shown when a
 * real resolved fact exists (never a raw reference id, never invented). */
function currentEvidenceLine(change: ChangeFindingView, factsForDimension: (dimension: string) => ReasoningFacts): string | null {
  const dimension = change.details.dimension;
  if (!dimension) return null;
  const facts = factsForDimension(dimension);
  const fact = [...facts.supporting, ...facts.contradicting].filter(isReadableFact)[0];
  return fact ?? null;
}

/** Compact by design -- see this sprint's own "avoid another
 * Today's-Priorities-style block" instruction. Renders nothing when the
 * capability is unavailable (no snapshot repository wired); otherwise
 * always exactly one of: a baseline note, "no material change," or the
 * change list plus its Atlas Thesis impact line.
 *
 * Extracted from `InvestmentCasePage.tsx` (Company Workspace v1
 * implementation sprint) so `CompanyWorkspacePage.tsx` can render the
 * exact same real Change Intelligence feed and vocabulary without a
 * second, drifting copy.
 *
 * Product Sprint 7 (Investment Case Excellence, Deliverable 5) --
 * two presentation-only changes, both reusing fields the backend
 * already sends, never a new signal or a numeric score:
 * 1. The Atlas Thesis impact line now leads, not trails -- "what
 *    changed" is supporting detail for "does it matter," so the verdict
 *    reads first, matching this sprint's own "the first things shown
 *    should always be the things that matter most."
 * 2. Individual changes are grouped by their own real `direction`
 *    (negative first, then neutral, then positive) instead of raw
 *    backend array order -- the changes most likely to need review
 *    surface first, without inventing an importance score.
 */
const DIRECTION_ORDER: Record<AnalysisChangeDirection, number> = { negative: 0, neutral: 1, positive: 2 };

export function WhatChangedSection({
  changeIntelligenceAvailable,
  isBaselineCase,
  latestChanges,
  thesisChange,
  factsForDimension,
  t,
}: {
  changeIntelligenceAvailable: boolean;
  isBaselineCase: boolean;
  latestChanges: ChangeFindingView[];
  thesisChange: AnalysisThesisImpact;
  /** Product Sprint 14: resolves a change's `details.dimension` back to
   * that dimension's own current real facts, the same finding lookups
   * `InvestmentCasePage.tsx`/`CompanyWorkspacePage.tsx` already build
   * for `AtlasReasoningSection`/`InvestmentArgumentSection`. Optional
   * only so a caller with nothing to resolve yet can omit it cleanly;
   * every real call site passes one. */
  factsForDimension?: (dimension: string) => ReasoningFacts;
  t: Translate;
}) {
  if (!changeIntelligenceAvailable) {
    return null;
  }

  const orderedChanges = [...latestChanges].sort(
    (a, b) => DIRECTION_ORDER[a.direction] - DIRECTION_ORDER[b.direction],
  );

  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.whatChanged.heading")}</Label>
      {isBaselineCase && <StatusText label={t("investmentCase.whatChanged.baseline")} />}
      {!isBaselineCase && latestChanges.length === 0 && (
        <StatusText label={t("investmentCase.whatChanged.noChange")} />
      )}
      {!isBaselineCase && latestChanges.length > 0 && (
        <Stack gap="metadata">
          <Text as="p" style={{ fontWeight: 600 }}>
            {t(THESIS_IMPACT_KEY[thesisChange])}
          </Text>
          <Text color="secondary" as="p">
            {t("investmentCase.whatChanged.sincePrevious")}
          </Text>
          {orderedChanges.map((change) => {
            const evidenceLine = factsForDimension ? currentEvidenceLine(change, factsForDimension) : null;
            return (
              <Stack gap="metadata" key={change.id}>
                <Text as="p">
                  {CHANGE_DIRECTION_SYMBOL[change.direction]} {describeChange(change, t)}
                </Text>
                {evidenceLine && (
                  <Text as="p" color="tertiary">
                    {evidenceLine}
                  </Text>
                )}
              </Stack>
            );
          })}
        </Stack>
      )}
    </Stack>
  );
}

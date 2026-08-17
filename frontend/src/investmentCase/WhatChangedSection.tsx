import { Stack, StatusText, Text, Label } from "../foundation";
import {
  CHANGE_DIRECTION_SYMBOL,
  describeChange,
  THESIS_IMPACT_KEY,
  type AnalysisThesisImpact,
  type ChangeFindingView,
  type Translate,
} from "../changeIntelligence/describeChange";

/** Compact by design -- see this sprint's own "avoid another
 * Today's-Priorities-style block" instruction. Renders nothing when the
 * capability is unavailable (no snapshot repository wired); otherwise
 * always exactly one of: a baseline note, "no material change," or the
 * change list plus its Atlas Thesis impact line.
 *
 * Extracted from `InvestmentCasePage.tsx` (Company Workspace v1
 * implementation sprint) so `CompanyWorkspacePage.tsx` can render the
 * exact same real Change Intelligence feed and vocabulary without a
 * second, drifting copy -- behavior unchanged from the original.
 */
export function WhatChangedSection({
  changeIntelligenceAvailable,
  isBaselineCase,
  latestChanges,
  thesisChange,
  t,
}: {
  changeIntelligenceAvailable: boolean;
  isBaselineCase: boolean;
  latestChanges: ChangeFindingView[];
  thesisChange: AnalysisThesisImpact;
  t: Translate;
}) {
  if (!changeIntelligenceAvailable) {
    return null;
  }

  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.whatChanged.heading")}</Label>
      {isBaselineCase && <StatusText label={t("investmentCase.whatChanged.baseline")} />}
      {!isBaselineCase && latestChanges.length === 0 && (
        <StatusText label={t("investmentCase.whatChanged.noChange")} />
      )}
      {!isBaselineCase && latestChanges.length > 0 && (
        <Stack gap="metadata">
          <Text color="secondary" as="p">
            {t("investmentCase.whatChanged.sincePrevious")}
          </Text>
          {latestChanges.map((change) => (
            <Text as="p" key={change.id}>
              {CHANGE_DIRECTION_SYMBOL[change.direction]} {describeChange(change, t)}
            </Text>
          ))}
          <Text as="p" color="tertiary">
            {t(THESIS_IMPACT_KEY[thesisChange])}
          </Text>
        </Stack>
      )}
    </Stack>
  );
}

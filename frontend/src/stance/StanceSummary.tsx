import { Inline, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { STANCE_LEVEL_KEY, STANCE_LEVEL_TONE } from "../status/statusTone";
import { cautionaryStanceReason, primaryStanceReason, showsCautionarySentence, stanceReasonSentence } from "./describeStance";
import {
  describeLineDimensions,
  describeMissingInformation,
  type DimensionGap,
} from "./describeMissingInformation";
import { describeDimensions, partitionMissingInformation } from "./partitionMissingInformation";
import type { StanceView } from "./stanceApi";

/**
 * Atlas Intelligence Sprint 2 (Recommendation Quality & Actionability,
 * Deliverable 5). A compact block reusing Investment Case's existing
 * Hero/Executive Summary area -- not a new large section. Matches this
 * Sprint's own worked example exactly: a level badge, "because X,"
 * and, only when a real tension exists, "while remaining cautious
 * because Y." Never a trade-sizing instruction -- `level` is always
 * rendered through `STANCE_LEVEL_KEY`'s own present-tense, non-
 * imperative labels ("View strengthened," never "Buy more").
 */
export function StanceSummary({
  stance,
  t,
  gaps = [],
}: {
  stance: StanceView;
  t: Translate;
  /** `explanation.missingEvidence`. Optional so every existing caller
   * and test keeps the behaviour it had. */
  gaps?: readonly DimensionGap[];
}) {
  const primary = primaryStanceReason(stance);
  const cautionary = showsCautionarySentence(stance) ? cautionaryStanceReason(stance) : null;
  const { companySpecific: companyGaps, engineUnsupported: engineGaps } = partitionMissingInformation(
    stance.missingInformation,
  );

  return (
    <Stack gap="metadata">
      <Inline gap="row" align="center">
        <Text as="span" color="secondary" style={{ fontWeight: 600 }}>
          {t("stance.heading")}
        </Text>
        <StatusBadge label={t(STANCE_LEVEL_KEY[stance.level])} tone={STANCE_LEVEL_TONE[stance.level]} />
      </Inline>
      {primary && (
        <Text as="p">
          {t("stance.becauseLabel")}: {stanceReasonSentence(primary, t)}
        </Text>
      )}
      {cautionary && (
        <Text as="p" color="secondary">
          {t("stance.whileCautiousLabel")}: {stanceReasonSentence(cautionary, t)}
        </Text>
      )}
      {/* Data Coverage & Decision Honesty: what this company is short
          of, and what Atlas cannot evaluate for anyone, are different
          statements and are no longer said in one breath. */}
      {/* Gap Reason Surface: the dimension says where Atlas is short; the
          reason says why, and only the second is decision-useful.
          `explanation.missingEvidence` has always carried it -- this block
          stops it being readable only at the bottom of the page. Without
          reasons the copy is exactly what it was. */}
      {companyGaps.length > 0 && (
        <Stack gap="metadata">
          <Text as="p" color="tertiary">
            {t("stance.missingInformationLabel")}
            {gaps.length === 0 ? ` ${describeDimensions(companyGaps, t)}` : ""}
          </Text>
          {gaps.length > 0 &&
            describeMissingInformation(companyGaps, gaps, t).map((line) => (
              <Text as="p" color="tertiary" key={line.dimensions.join("|")}>
                {describeLineDimensions(line, t)}
                {line.reason ? ` — ${line.reason}` : ""}
              </Text>
            ))}
        </Stack>
      )}
      {engineGaps.length > 0 && (
        <Text as="p" color="tertiary">
          {t("stance.notYetEvaluatedByAtlasLabel")} {describeDimensions(engineGaps, t)}
        </Text>
      )}
    </Stack>
  );
}

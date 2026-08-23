import { Inline, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { STANCE_LEVEL_KEY, STANCE_LEVEL_TONE } from "../status/statusTone";
import { cautionaryStanceReason, primaryStanceReason, showsCautionarySentence, stanceReasonSentence } from "./describeStance";
import { coverageDimensionLabel } from "../coverage/describeCoverage";
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
export function StanceSummary({ stance, t }: { stance: StanceView; t: Translate }) {
  const primary = primaryStanceReason(stance);
  const cautionary = showsCautionarySentence(stance) ? cautionaryStanceReason(stance) : null;

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
      {stance.missingInformation.length > 0 && (
        <Text as="p" color="tertiary">
          {t("stance.missingInformationLabel")} {stance.missingInformation.map((d) => coverageDimensionLabel(d, t)).join(", ")}
        </Text>
      )}
    </Stack>
  );
}

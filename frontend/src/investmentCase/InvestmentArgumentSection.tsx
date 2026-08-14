import { Inline, Label, Stack, Text } from "../foundation";
import type { AnalysisHighlightKind, Translate } from "../changeIntelligence/describeChange";
import { CHALLENGE_SENTENCE_KEY, STRENGTH_SENTENCE_KEY } from "./HeroCard";

/**
 * Investment Argument (Figma-fidelity rebuild): the two-column Supports
 * the Case / Challenges the Case structure, built from `strengths[]`/
 * `risks[]` -- real, already-computed `CaseHighlightView` classifications
 * this codebase already fetches, previously shown only as bare category
 * words (`HIGHLIGHT_KIND_KEY[kind]`, e.g. "Growth") in the buried More
 * Details tab. `STRENGTH_SENTENCE_KEY`/`CHALLENGE_SENTENCE_KEY` (shared
 * with `HeroCard`'s Biggest Strength field, never redefined twice) turn
 * each real kind into the fuller, evidence-attributed sentence the
 * approved design shows -- the classification is real; only its sentence
 * form is new. The two banks are not interchangeable: `HighlightKind` is
 * directional (see `HeroCard`'s own comment), so Supports must read
 * `strengthKinds` through `STRENGTH_SENTENCE_KEY` and Challenges must
 * read `riskKinds` through `CHALLENGE_SENTENCE_KEY`, never the other way.
 */

export function InvestmentArgumentSection({
  strengthKinds,
  riskKinds,
  t,
}: {
  strengthKinds: AnalysisHighlightKind[];
  riskKinds: AnalysisHighlightKind[];
  t: Translate;
}) {
  return (
    <Stack gap="intra-section">
      <Label>{t("investmentCase.argument.heading")}</Label>
      <Inline gap="inter-section" wrap align="start">
        <Stack gap="metadata" style={{ flex: "1 1 320px", minWidth: 0 }}>
          <Text as="p" style={{ fontWeight: 600, color: "var(--color-semantic-green)" }}>
            {t("investmentCase.argument.supportsHeading")}
          </Text>
          {strengthKinds.length === 0 ? (
            <Text color="secondary">{t("investmentCase.argument.supportsEmpty")}</Text>
          ) : (
            strengthKinds.map((kind, index) => (
              <Text as="p" key={`${kind}-${index}`}>
                {t(STRENGTH_SENTENCE_KEY[kind])}
              </Text>
            ))
          )}
        </Stack>
        <Stack gap="metadata" style={{ flex: "1 1 320px", minWidth: 0 }}>
          <Text as="p" style={{ fontWeight: 600, color: "var(--color-semantic-amber)" }}>
            {t("investmentCase.argument.challengesHeading")}
          </Text>
          {riskKinds.length === 0 ? (
            <Text color="secondary">{t("investmentCase.argument.challengesEmpty")}</Text>
          ) : (
            riskKinds.map((kind, index) => (
              <Text as="p" key={`${kind}-${index}`}>
                {t(CHALLENGE_SENTENCE_KEY[kind])}
              </Text>
            ))
          )}
        </Stack>
      </Inline>
    </Stack>
  );
}

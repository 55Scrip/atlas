import { Inline, Label, Stack, Text } from "../foundation";
import {
  OPEN_QUESTION_ORIGIN_KEY,
  type AnalysisHighlightKind,
  type AnalysisOpenQuestionOrigin,
  type Translate,
} from "../changeIntelligence/describeChange";
import { CHALLENGE_SENTENCE_KEY, STRENGTH_SENTENCE_KEY } from "./HeroCard";
import { isReadableFact, type ReasoningFacts } from "./AtlasReasoningSection";

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
 *
 * Product Sprint 7 (Investment Case Excellence, Deliverable 4 -- Bull vs
 * Bear) -- a third column, Open Questions, was added so Bull Case / Bear
 * Case / Open Questions read together as one argument instead of Open
 * Questions being buried three clicks away in the "More Details" tab
 * (`keyOpenQuestions` was previously only rendered there). There is no
 * separate "Unknowns" concept anywhere in this codebase's analysis output
 * -- `keyOpenQuestions` (unresolved items Atlas flags as needing more
 * evidence) is what that word refers to here, so it is not duplicated
 * under a second heading.
 *
 * Product Sprint 13 (Company Intelligence Excellence, Deliverable 6 --
 * Bull/Bear Balance): the risk-derived Challenges sentences ("An
 * identified financial risk works against the case") were the thinnest
 * text on the whole page -- naming a category with zero specificity,
 * while the same finding's own `contradictingFacts` (real, already
 * fetched) sat unused. `factsForKind` resolves each kind back to its
 * real finding (the same lookup `AtlasReasoningSection`'s facts already
 * use) so both columns can show a real, company-specific fact under
 * the category sentence -- Supports shows `supporting`, Challenges
 * shows `contradicting`, matching each column's own direction. Every
 * fact is filtered through `isReadableFact` first -- live-testing found
 * these arrays sometimes hold raw internal evidence-reference ids
 * rather than resolved prose (a backend/data gap, out of this sprint's
 * scope; see `isReadableFact`'s own doc comment), so a kind with no
 * real prose fact simply shows no second line, never a raw id.
 */

export function InvestmentArgumentSection({
  strengthKinds,
  riskKinds,
  openQuestionOrigins,
  factsForKind,
  t,
}: {
  strengthKinds: AnalysisHighlightKind[];
  riskKinds: AnalysisHighlightKind[];
  openQuestionOrigins: AnalysisOpenQuestionOrigin[];
  factsForKind: (kind: AnalysisHighlightKind) => ReasoningFacts;
  t: Translate;
}) {
  return (
    <Stack gap="intra-section">
      <Label>{t("investmentCase.argument.heading")}</Label>
      <Inline gap="inter-section" wrap align="start">
        <Stack gap="metadata" style={{ flex: "1 1 280px", minWidth: 0 }}>
          <Text as="p" style={{ fontWeight: 600, color: "var(--color-semantic-green)" }}>
            {t("investmentCase.argument.supportsHeading")}
          </Text>
          {strengthKinds.length === 0 ? (
            <Text color="secondary">{t("investmentCase.argument.supportsEmpty")}</Text>
          ) : (
            strengthKinds.map((kind, index) => {
              const fact = factsForKind(kind).supporting.filter(isReadableFact)[0];
              return (
                <Stack gap="metadata" key={`${kind}-${index}`}>
                  <Text as="p">{t(STRENGTH_SENTENCE_KEY[kind])}</Text>
                  {fact && (
                    <Text as="p" color="tertiary">
                      {fact}
                    </Text>
                  )}
                </Stack>
              );
            })
          )}
        </Stack>
        <Stack gap="metadata" style={{ flex: "1 1 280px", minWidth: 0 }}>
          <Text as="p" style={{ fontWeight: 600, color: "var(--color-semantic-amber)" }}>
            {t("investmentCase.argument.challengesHeading")}
          </Text>
          {riskKinds.length === 0 ? (
            <Text color="secondary">{t("investmentCase.argument.challengesEmpty")}</Text>
          ) : (
            riskKinds.map((kind, index) => {
              const fact = factsForKind(kind).contradicting.filter(isReadableFact)[0];
              return (
                <Stack gap="metadata" key={`${kind}-${index}`}>
                  <Text as="p">{t(CHALLENGE_SENTENCE_KEY[kind])}</Text>
                  {fact && (
                    <Text as="p" color="tertiary">
                      {fact}
                    </Text>
                  )}
                </Stack>
              );
            })
          )}
        </Stack>
        <Stack gap="metadata" style={{ flex: "1 1 280px", minWidth: 0 }}>
          <Text as="p" style={{ fontWeight: 600, color: "var(--color-text-secondary)" }}>
            {t("investmentCase.atlasView.openQuestions.heading")}
          </Text>
          {openQuestionOrigins.length === 0 ? (
            <Text color="secondary">{t("investmentCase.atlasView.openQuestions.empty")}</Text>
          ) : (
            openQuestionOrigins.map((origin, index) => (
              <Text as="p" key={`${origin}-${index}`} color="secondary">
                {t(OPEN_QUESTION_ORIGIN_KEY[origin])}
              </Text>
            ))
          )}
        </Stack>
      </Inline>
    </Stack>
  );
}

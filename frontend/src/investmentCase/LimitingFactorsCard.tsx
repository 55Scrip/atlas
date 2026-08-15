import { Label, Stack, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { RISK_CATEGORY_KEY } from "../changeIntelligence/describeChange";
import { VALUATION_SUPPORT_GAP_COPY_KEY } from "../status/statusTone";
import { CONCERN_SENTENCE_KEY } from "./HeroCard";
import type { LimitingFactor } from "./deriveExecutiveSummary";

/**
 * Beta Recommendation Experience implementation sprint: the Figma's
 * "Limiting Factors" / "What limits this conclusion?" card, built from
 * `deriveLimitingFactors`'s own output only -- see that function's
 * docstring for the exact real-data selection rule. Each item's title
 * and sentence are both real, already-approved copy: risk items reuse
 * `RISK_CATEGORY_KEY` (title) + `CONCERN_SENTENCE_KEY` (sentence, the
 * same bank `HeroCard`'s own Biggest Concern field already uses);
 * the valuation-gap item reuses `VALUATION_SUPPORT_GAP_COPY_KEY`
 * (`UX-022` §9's own short gap-copy pattern). Renders nothing at all
 * when `factors` is empty -- never a placeholder ("no invented
 * taxonomy," per `UX-022` §3).
 */
export function LimitingFactorsCard({ factors, t }: { factors: LimitingFactor[]; t: Translate }) {
  if (factors.length === 0) return null;

  return (
    <Stack gap="intra-section">
      <Label>{t("investmentCase.limitingFactors.heading")}</Label>
      <Stack gap="metadata">
        {factors.map((factor, index) => {
          const title =
            factor.kind === "valuationGap"
              ? t("investmentCase.limitingFactors.valuationGapTitle")
              : t(RISK_CATEGORY_KEY[factor.category]);
          const sentence =
            factor.kind === "valuationGap"
              ? t(VALUATION_SUPPORT_GAP_COPY_KEY[factor.gap])
              : t(CONCERN_SENTENCE_KEY[factor.category]);
          return (
            <Stack gap="metadata" key={`${factor.kind}-${index}`}>
              <Text as="p" style={{ fontWeight: 600 }}>
                {title}
              </Text>
              <Text as="p" color="secondary">
                {sentence}
              </Text>
            </Stack>
          );
        })}
      </Stack>
    </Stack>
  );
}

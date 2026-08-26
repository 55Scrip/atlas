import { Stack, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { reliabilityReasonLabel } from "../decisionReliability/describeDecisionReliability";
import type { DecisionReliabilityView } from "../decisionReliability/decisionReliabilityApi";
import { stepLabel } from "../decisionPath/describeDecisionPath";
import type { DecisionPathView } from "../decisionPath/decisionPathApi";

/**
 * Information Compression (Productization Sprint P2, Phase 4 --
 * Decision-Layer Consolidation). Before this component, the same
 * underlying meaning ("evidence support is weak, here's the one thing
 * that would help") was restated across nine separately-fetched
 * Decision Layer sections (Decision Readiness, Investment Decision,
 * Recommendation Conviction, Decision Path, Opportunity Cost, Decision
 * Memory, Decision Explanation, Decision Reliability, Portfolio
 * Decision), each in its own vocabulary. This card answers the one
 * question they were all circling -- "why isn't Atlas more certain,
 * and what would change that" -- from the two views built specifically
 * to already hold a *single* authoritative answer: Decision
 * Reliability's own `primaryLimitingReason` (never a new synthesis --
 * the backend already ranks this) for the headline sentence and its
 * `limitingReasons` for supporting detail, and Decision Path's own
 * `nextAchievableImprovement` for what would change the view. No new
 * fetch, no new backend computation -- both views are already fetched
 * by `InvestmentCasePage` for the nine sections this card sits above.
 * Those nine sections are not deleted or changed in any way; they move
 * into a single `ExpandableDetail` immediately below this card, so
 * every reason, count, and source tag they show remains exactly as
 * reachable as before -- only the default reading path changes.
 */
export function AtlasDecisionSummary({
  reliability,
  path,
  t,
}: {
  reliability: DecisionReliabilityView | null;
  path: DecisionPathView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (!reliability) return null;

  const primary = reliability.primaryLimitingReason;
  /** Dedupe by meaning (source + the real reference id the backend
   * names), not object identity -- `primaryLimitingReason` and an
   * entry in `limitingReasons` can be distinct objects describing the
   * exact same underlying fact, which must never render as two
   * bullets saying the same thing (the precise duplication this
   * sprint exists to remove). */
  const isPrimary = (reason: DecisionReliabilityView["limitingReasons"][number]) =>
    primary !== null && reason.source === primary.source && reason.reference.id === primary.reference.id;
  const supportingLimits = reliability.limitingReasons.filter((reason) => !isPrimary(reason)).slice(0, 2);
  const nextImprovement = path?.nextAchievableImprovement ?? null;

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Text as="p" style={{ fontWeight: 600 }}>
          {t("investmentCase.decisionSummary.heading")}
        </Text>
        {primary ? (
          <Text as="p">
            {t("decisionReliability.section.primaryLimiting", { fact: reliabilityReasonLabel(primary, t) })}
          </Text>
        ) : (
          <Text as="p" color="tertiary">
            {t("decisionReliability.section.noLimiting")}
          </Text>
        )}
        {supportingLimits.length > 0 && (
          <Stack gap="row">
            {supportingLimits.map((reason, index) => (
              <Text as="p" color="secondary" key={`${reason.source}:${reason.reference.id}:${index}`}>
                {"• " + reliabilityReasonLabel(reason, t)}
              </Text>
            ))}
          </Stack>
        )}
        {nextImprovement && (
          <Text as="p" color="secondary">
            {t("decisionPath.section.nextAchievableImprovement")}: {stepLabel(nextImprovement, t)}
          </Text>
        )}
      </Stack>
    </Surface>
  );
}

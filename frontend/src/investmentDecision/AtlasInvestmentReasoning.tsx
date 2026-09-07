import { Stack, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ACTION_KEY } from "./describeInvestmentDecision";
import { CHANGE_TRIGGER_KEY, keyUnknownLabel, reasonKindLabel } from "./describeRecommendationReasoning";
import type { InvestmentDecisionView } from "./investmentDecisionApi";

/**
 * Recommendation Reasoning Convergence -- the one primary investment
 * explanation.
 *
 * Atlas has always computed a canonical rationale (drivers,
 * counter-drivers, key unknowns, change triggers) from the same engine
 * statuses Direction Selection reads. Two things kept it invisible: it
 * was discarded whenever a recommendation was withheld, and it was
 * never typed at the network boundary. Both are fixed; this card is
 * where the result is read.
 *
 * It renders the synthesis only -- the four questions an investor
 * actually asks -- and nothing else. Signal provenance, engine states
 * and magnitudes stay where they already are (Seven Categories,
 * Valuation Support, the Decision Layer disclosure); duplicating them
 * here is what made the page long in the first place.
 *
 * The directional/withheld distinction is preserved literally, never
 * cosmetically:
 *
 * - directional -- the recommendation is stated, and the drivers are
 *   presented as what supports *it*;
 * - withheld -- the card says plainly that Atlas does not yet support
 *   a directional recommendation, and the very same drivers are
 *   presented as what the evidence currently indicates. No "reason to
 *   buy", no "reason to sell", no implied action.
 *
 * Nothing here is ranked, scored, thresholded, or inferred locally:
 * every line is a translation lookup on a closed backend token, in the
 * backend's own order.
 */
export function AtlasInvestmentReasoning({
  decision,
  t,
}: {
  decision: InvestmentDecisionView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const reasoning = decision.reasoning;
  // Legitimately absent: a legacy row, or an outcome the analysis
  // engine never produced. Render nothing rather than an empty shell
  // that would read as "Atlas found nothing".
  if (!reasoning) return null;

  const supporting = reasoning.primaryDrivers ?? [];
  const opposing = reasoning.counterDrivers ?? [];
  const unknowns = (reasoning.keyUnknowns ?? [])
    .map((unknown) => keyUnknownLabel(unknown, t))
    .filter((label): label is string => label !== null);
  const triggers = reasoning.whatWouldChange ?? [];

  // `no_decision` is the action the backend emits when the
  // recommendation was withheld. It is read here for *wording* only --
  // the recommendation itself is `decision.action`, computed upstream,
  // and nothing in this card can change it.
  const isWithheld = decision.action === "no_decision";

  if (supporting.length === 0 && opposing.length === 0 && unknowns.length === 0 && triggers.length === 0) {
    return null;
  }

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Text as="p" style={{ fontWeight: 600 }}>
          {t("investmentReasoning.heading")}
        </Text>

        <Text as="p" color={isWithheld ? "secondary" : "primary"}>
          {isWithheld
            ? t("investmentReasoning.state.withheld")
            : t("investmentReasoning.state.directional", { action: t(ACTION_KEY[decision.action]) })}
        </Text>

        <ReasoningRow
          label={t(isWithheld ? "investmentReasoning.row.indicatesFor" : "investmentReasoning.row.supports")}
          items={supporting.map((reason) => reasonKindLabel(reason, t))}
          emptyLabel={t("investmentReasoning.empty.supports")}
        />
        <ReasoningRow
          label={t(isWithheld ? "investmentReasoning.row.indicatesAgainst" : "investmentReasoning.row.opposes")}
          items={opposing.map((reason) => reasonKindLabel(reason, t))}
          emptyLabel={t("investmentReasoning.empty.opposes")}
        />
        {unknowns.length > 0 && (
          <ReasoningRow label={t("investmentReasoning.row.unresolved")} items={unknowns} emptyLabel={null} />
        )}
        {triggers.length > 0 && (
          <ReasoningRow
            label={t(isWithheld ? "investmentReasoning.row.wouldStrengthen" : "investmentReasoning.row.wouldChange")}
            items={triggers.map((trigger) => t(CHANGE_TRIGGER_KEY[trigger]))}
            emptyLabel={null}
          />
        )}
      </Stack>
    </Surface>
  );
}

/** One label plus its already-ordered items, joined into a single
 * line. Deliberately one line per question rather than a bullet list
 * per question: this card sits in the first viewport, immediately
 * after Atlas's conclusion, and must stay readable at a glance. */
function ReasoningRow({
  label,
  items,
  emptyLabel,
}: {
  label: string;
  items: string[];
  emptyLabel: string | null;
}) {
  if (items.length === 0 && emptyLabel === null) return null;
  return (
    <Text as="p" color="secondary">
      <span style={{ color: "var(--color-text-primary)" }}>{label}: </span>
      {items.length > 0 ? items.join(" · ") : emptyLabel}
    </Text>
  );
}

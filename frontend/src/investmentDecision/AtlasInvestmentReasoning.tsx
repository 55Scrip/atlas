import { Stack, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import {
  CHANGE_TRIGGER_KEY,
  financialRiskNotApplicableLabel,
  forwardContextLabels,
  forwardUnknownLabels,
  keyUnknownLabel,
  reasonKindLabel,
  riskBasisLabel,
} from "./describeRecommendationReasoning";
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
  locale = "en-US",
}: {
  decision: InvestmentDecisionView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
  /** Number formatting for reported figures; the caller's own language. */
  locale?: string;
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
  // Forward context: verified forward evidence shown *alongside* the
  // reasoning. It is not a driver and has no side -- it gets its own row,
  // never the "in favour"/"against" ones.
  const forward = forwardContextLabels(reasoning.forwardContext, t);
  const forwardUnknowns = forwardUnknownLabels(reasoning.forwardContext, t);
  // Risk basis: why "elevated financial risk" is in the against-row, told
  // right beneath it. Only for that driver -- a low or moderate level
  // explains nothing that row claims, so it stays quiet.
  const riskBasis = opposing.some((reason) => reason.kind === "financial_risk_elevated")
    ? riskBasisLabel(reasoning.riskBasis, t, locale)
    : null;
  // A Financial Risk the measure does not apply to gets one quiet line --
  // never a row of its own, never read as "not elevated".
  const notApplicable = financialRiskNotApplicableLabel(reasoning.riskBasis, t);

  // `no_decision` is the action the backend emits when the
  // recommendation was withheld. It is read here for *wording* only --
  // the recommendation itself is `decision.action`, computed upstream,
  // and nothing in this card can change it.
  const isWithheld = decision.action === "no_decision";

  // What contracted volume does not establish always travels with it. On
  // a directional case that is exactly the "main uncertainty" row. On a
  // withheld case that row reads "what needs resolving" -- and an
  // unpriced contract is not what stands between Atlas and a position --
  // so there the limitation stays attached to the forward row instead.
  const unresolved = isWithheld ? unknowns : [...unknowns, ...forwardUnknowns];
  const forwardItems = isWithheld ? [...forward, ...forwardUnknowns] : forward;

  if (
    supporting.length === 0 &&
    opposing.length === 0 &&
    unresolved.length === 0 &&
    triggers.length === 0 &&
    forwardItems.length === 0 &&
    notApplicable === null
  ) {
    return null;
  }

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Text as="p" style={{ fontWeight: 600 }}>
          {t("investmentReasoning.heading")}
        </Text>

        {/* Canonical Reasoning Consolidation, Conflict 1. This line used
            to restate the recommendation for the directional case too
            ("Atlas slutsats: Behåll."), while the Hero -- reading the
            identical canonical `RecommendationDirection.HOLD` through
            `_DIRECTION_LEVEL` -- announced it as "Tesen kvarstår". One
            judgment, two vocabularies, stacked one above the other.
            The Hero owns the recommendation statement; this card owns
            the reasoning, and no longer names the direction at all.

            The withheld line stays, because it is not a restatement:
            the Hero's badge says "Vet inte än", which reports low
            evidence support without ever saying that Atlas is
            declining to take a direction. That is the one thing a
            withheld case most needs stated plainly, and it is stated
            once, here. */}
        {isWithheld && (
          <Text as="p" color="secondary">
            {t("investmentReasoning.state.withheld")}
          </Text>
        )}

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
        {riskBasis && (
          <Text as="p" color="tertiary">
            {riskBasis}
          </Text>
        )}
        {forwardItems.length > 0 && (
          <ReasoningRow
            label={t("investmentReasoning.row.forwardContext")}
            items={forwardItems}
            emptyLabel={null}
          />
        )}
        {/* Phase L. For a withheld outcome the investor's question is
            "what has to be resolved before Atlas can take a position",
            and the canonical field that answers it is `key_unknowns`
            -- not `what_would_change`. That is the engine's own
            division of labour, stated in `_derive_what_would_change`:
            an `INSUFFICIENT_INPUT` valuation support deliberately
            emits no change trigger, "a data gap, not an investment
            condition", precisely because `key_unknowns` already owns
            it. So the withheld case relabels this row to the blocker
            it already is. No new field, no new inference. */}
        {unresolved.length > 0 && (
          <ReasoningRow
            label={t(isWithheld ? "investmentReasoning.row.needsResolving" : "investmentReasoning.row.unresolved")}
            items={unresolved}
            emptyLabel={null}
          />
        )}
        {/* `what_would_change` means the same thing on both branches --
            "every condition that would materially change this picture",
            reversals and deteriorations alike. It is deliberately NOT
            relabelled as "what Atlas needs" for the withheld case:
            MU's triggers are "financial risk rises" and "valuation
            becomes expensive", neither of which would let Atlas reach a
            decision. Calling them that would be a false promise. */}
        {triggers.length > 0 && (
          <ReasoningRow
            label={t("investmentReasoning.row.wouldChange")}
            items={triggers.map((trigger) => t(CHANGE_TRIGGER_KEY[trigger]))}
            emptyLabel={null}
          />
        )}
        {notApplicable && (
          <Text as="p" color="tertiary">
            {notApplicable}
          </Text>
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

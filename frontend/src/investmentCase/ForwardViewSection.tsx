import { Divider, Label, Stack, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import {
  contractedVolumeLabel,
  forwardUnknownLabels,
  guidanceContextLabel,
} from "../investmentDecision/describeRecommendationReasoning";
import type {
  ContractedVolumeContextView,
  ForwardReasoningContextView,
} from "../investmentDecision/reasoningContract";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/**
 * Forward View -- what Atlas has that is genuinely about the future,
 * and nothing else.
 *
 * The source is `RecommendationReasoning.forwardContext`, the single
 * deliberate seam between Atlas's forward-evidence pipeline and its
 * recommendation (`atlas/analysis_engine/forward_context.py`). Every
 * item is a restatement of an interpretation that pipeline already
 * produced: the latest verified revision of each guided measure and
 * horizon, and each contracted-volume observation as it stands.
 *
 * Three rules this chapter does not bend:
 *
 * 1. **Evidence, not forecast.** Nothing here is extrapolated,
 *    projected, or consensus. Guidance is management's own figure, in
 *    management's own words, with `reaffirmed` meaning the numbers did
 *    not move -- never "supportive". Historical growth is not admitted
 *    to this chapter at all; a trend is not a forward claim.
 * 2. **Context, not driver.** `forward_context` is handed to the
 *    recommendation gate *after* the direction is chosen, and nothing
 *    that selects a direction, driver, trigger, unknown or conviction
 *    can read it -- both pinned by backend tests. Rendering it more
 *    prominently changes nothing about that, and this chapter states
 *    it in words so the reader is not left to infer a causal role.
 * 3. **What it does not establish travels with it.** A contracted
 *    volume is a quantity, not economics: price and the contribution
 *    to revenue, earnings and cash flow are named as unestablished
 *    wherever the evidence does not establish them.
 *
 * `null`/empty is the ordinary case, not a failure: most companies in
 * the portfolio have no verified forward evidence at all. It says so
 * quietly and stops.
 *
 * Deferred, deliberately, to the Forward Intelligence sprint:
 * `managementGuidanceIntelligence` on the analysis response carries a
 * broader raw guidance inventory (MA: 23 items, VST: 29) that this
 * verified pipeline does not admit. Surfacing it needs its own
 * enum vocabulary and its own honesty rules about what "guidance" a
 * commentary classifier found; it is not presentation work.
 */
/**
 * Product Convergence Sprint 1B (Investment Case Compression) -- what a
 * caller needs to render the chapter's title row without opening it.
 * Pure counting over the same structured context; no judgment, no
 * aggregation, and deliberately no "positive"/"negative" reading of
 * what management said.
 */
export function forwardViewSummary(
  context: ForwardReasoningContextView | null | undefined,
  t: Translate,
): { hasEvidence: boolean; status: string; headline: string | null } {
  const guidance = context?.guidance.length ?? 0;
  const volume = context?.contractedVolume.length ?? 0;
  if (guidance === 0 && volume === 0) {
    return { hasEvidence: false, status: t("investmentCase.forwardView.status.none"), headline: null };
  }
  const parts = [
    guidance > 0
      ? t(guidance === 1 ? "investmentCase.forwardView.count.guidanceOne" : "investmentCase.forwardView.count.guidanceOther", {
          count: guidance,
        })
      : null,
    volume > 0
      ? t(volume === 1 ? "investmentCase.forwardView.count.volumeOne" : "investmentCase.forwardView.count.volumeOther", {
          count: volume,
        })
      : null,
  ].filter((part): part is string => part !== null);
  return { hasEvidence: true, status: t("investmentCase.forwardView.status.present"), headline: parts.join(" · ") };
}

export function ForwardViewSection({
  context,
  t,
}: {
  /** `null` when the case carries no reasoning at all (a legacy row, or
   * a decision fetch that has not loaded) -- indistinguishable, from
   * here, from a company with no forward evidence, and treated the
   * same honest way. */
  context: ForwardReasoningContextView | null | undefined;
  t: Translate;
}) {
  const guidance = context?.guidance ?? [];
  const volume = context?.contractedVolume ?? [];
  const unknowns = forwardUnknownLabels(context, t);

  /* Sprint 1B: the "Atlas holds none" state is now the chapter's own
     status badge plus one tertiary line, rendered by the chapter rather
     than by a panel of its own -- an absent capability should not cost
     a card. This component renders only when there is something real to
     show, and the caller decides that with `forwardViewSummary`. */
  if (guidance.length === 0 && volume.length === 0 && unknowns.length === 0) {
    return null;
  }

  // `contractedVolumeLabel` summarises several observations into one
  // line for the conclusion strip. This chapter is the place that owes
  // the reader each observation, so the summary is used only when there
  // is genuinely one of them.
  const singleVolumeLine = volume.length === 1 && context ? contractedVolumeLabel(context, t) : null;

  return (
    <Stack gap="intra-section">
      <Text as="p" color="tertiary">
        {t("investmentCase.forwardView.caption")}
      </Text>

      {guidance.length > 0 && (
        <Stack gap="metadata">
          <Label>{t("investmentCase.forwardView.guidanceLabel")}</Label>
          {guidance.map((item) => (
            <Stack key={item.signalId} gap="metadata">
              <Text as="p">{guidanceContextLabel(item, t)}</Text>
              {item.sourcePeriod && (
                <Text as="p" color="tertiary">
                  {t("investmentCase.forwardView.statedIn", { period: item.sourcePeriod })}
                </Text>
              )}
            </Stack>
          ))}
        </Stack>
      )}

      {volume.length > 0 && (
        <>
          {guidance.length > 0 && <Divider tone="hairline" />}
          <Stack gap="metadata">
            <Label>{t("investmentCase.forwardView.contractedVolumeLabel")}</Label>
            {singleVolumeLine ? (
              <Text as="p">{singleVolumeLine}</Text>
            ) : (
              <>
                <Text as="p" color="tertiary">
                  {t("investmentCase.forwardView.observationsNote")}
                </Text>
                {volume.map((observation) => (
                  <ContractedVolumeObservation key={observation.signalId} observation={observation} t={t} />
                ))}
              </>
            )}
          </Stack>
        </>
      )}

      {unknowns.length > 0 && (
        <Stack gap="metadata">
          {unknowns.map((line) => (
            <Text as="p" color="tertiary" key={line}>
              {line}
            </Text>
          ))}
        </Stack>
      )}
    </Stack>
  );
}

/** One contracted-volume observation in its own stated terms. Quantities
 * are verbatim source text, so they are listed, never summed -- and the
 * same agreement may well appear in another observation, which is why
 * the note above says so rather than this line implying otherwise. */
function ContractedVolumeObservation({
  observation,
  t,
}: {
  observation: ContractedVolumeContextView;
  t: Translate;
}) {
  const parts = [
    observation.agreementText,
    ...observation.quantityTexts,
    observation.termYears !== null
      ? t("investmentReasoning.forward.volume.term", { years: observation.termYears }).replace(/^,\s*/, "")
      : null,
    observation.deliveryStartYears.length > 0
      ? t("investmentReasoning.forward.volume.deliveryFrom", {
          years: observation.deliveryStartYears.join(", "),
        }).replace(/^,\s*/, "")
      : null,
  ].filter((part): part is string => part !== null && part !== "");

  return (
    <Stack gap="metadata">
      <Text as="p">
        {observation.counterpartyText ?? t("investmentReasoning.forward.volume.unnamedCustomer")}
        {parts.length > 0 ? ` — ${parts.join(", ")}` : ""}
      </Text>
      {observation.sourcePeriod && (
        <Text as="p" color="tertiary">
          {t("investmentCase.forwardView.statedIn", { period: observation.sourcePeriod })}
        </Text>
      )}
    </Stack>
  );
}

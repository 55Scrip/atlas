import { useState } from "react";
import { Inline, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { EVIDENCE_TRANSITION_DIRECTION_TONE } from "../status/statusTone";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { materialTransitions, prominentSourceEvidence, sourceEvidenceSentence, transitionCategoryLabel, transitionSentence } from "./describeEvidenceTimeline";
import { fetchEvidenceTimelineForTicker, type EvidenceTimelineEntryPairView } from "./evidenceTimelineApi";

type FetchStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "unavailable" }
  | { kind: "loaded"; entries: EvidenceTimelineEntryPairView[] };

/**
 * Atlas Intelligence Sprint 5/6 (Evidence Timeline & Historical
 * Understanding, Deliverables 6/7/9/10). One reusable "how has the
 * evidence changed" disclosure -- used on Daily Brief/Portfolio agenda
 * rows and Discovery candidate cards alike, mirroring
 * `TickerExplanationDetail`/`TickerEvidenceQualityDetail`'s own exact
 * lazy-fetch shape: fetches only on first expand. Shows only the most
 * recent capture's *material* transitions (Sprint 6, Deliverable 7 --
 * an already-dense agenda row surfaces only what genuinely matters, not
 * every recorded transition) plus any new Source Evidence, or an honest
 * baseline/no-change note when neither exists -- the fuller,
 * unfiltered history already lives on the Investment Case page's own
 * `EvidenceTimelinePanel`, one click away.
 */
export function TickerEvidenceTimelineDetail({ ticker, summaryLabel, t }: { ticker: string; summaryLabel: string; t: Translate }) {
  const [status, setStatus] = useState<FetchStatus>({ kind: "idle" });

  function handleOpen(open: boolean) {
    if (!open || status.kind !== "idle") return;
    setStatus({ kind: "loading" });
    fetchEvidenceTimelineForTicker(ticker)
      .then((entries) => setStatus(entries === null ? { kind: "unavailable" } : { kind: "loaded", entries }))
      .catch(() => setStatus({ kind: "unavailable" }));
  }

  return (
    <ExpandableDetail summaryLabel={summaryLabel} onToggle={handleOpen}>
      {status.kind === "loading" && <Text color="tertiary">{t("common.loading")}</Text>}
      {status.kind === "unavailable" && <Text color="tertiary">{t("evidenceTimeline.panel.emptyHistory")}</Text>}
      {status.kind === "loaded" && (() => {
        const latest = status.entries[status.entries.length - 1];
        if (!latest) return <Text color="tertiary">{t("evidenceTimeline.panel.emptyHistory")}</Text>;
        if (latest.history.isBaseline) return <Text color="tertiary">{t("evidenceTimeline.panel.baselineNote")}</Text>;
        const prominentTransitions = materialTransitions(latest.history.transitions);
        if (prominentTransitions.length === 0 && latest.history.newSourceEvidence.length === 0) {
          return <Text color="tertiary">{t("evidenceTimeline.panel.noChangeNote")}</Text>;
        }
        const { shown: shownSourceEvidence, overflowCount: sourceEvidenceOverflow } = prominentSourceEvidence(latest.history.newSourceEvidence);
        return (
          <Stack gap="metadata">
            {shownSourceEvidence.map((event, index) => (
              <Text key={index} color="tertiary" as="p">
                {sourceEvidenceSentence(event, t)}
              </Text>
            ))}
            {sourceEvidenceOverflow > 0 && (
              <Text color="tertiary" as="p">{t("evidenceTimeline.sourceEvidence.overflowNote", { count: sourceEvidenceOverflow })}</Text>
            )}
            {prominentTransitions.map((transition) => (
              <Inline key={transition.id} gap="metadata" align="center">
                <StatusBadge label={transitionCategoryLabel(transition.category, t)} tone={EVIDENCE_TRANSITION_DIRECTION_TONE[transition.direction]} />
                <Text color="tertiary" as="span">
                  {transitionSentence(transition, t)}
                </Text>
              </Inline>
            ))}
          </Stack>
        );
      })()}
    </ExpandableDetail>
  );
}

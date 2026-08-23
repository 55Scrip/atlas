import { useState } from "react";
import { Inline, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { EVIDENCE_TRANSITION_DIRECTION_TONE } from "../status/statusTone";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { materialTransitions, prominentSourceEvidence, sourceEvidenceSentence, transitionCategoryLabel, transitionSentence } from "./describeEvidenceTimeline";
import { fetchEvidenceTimelineForCase, type EvidenceHistoryView, type EvidenceTimelineEntryPairView } from "./evidenceTimelineApi";

type FullHistoryStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "unavailable" }
  | { kind: "loaded"; entries: EvidenceTimelineEntryPairView[] };

/**
 * Atlas Intelligence Sprint 5/6 (Evidence Timeline & Historical
 * Understanding, Deliverables 5/8). Compact by default: only the most
 * recent capture's *material* transitions (Sprint 6, Deliverable 7 --
 * `isMaterial` is server-computed, this panel only filters on it) plus
 * any new Source Evidence (a factual "Atlas received newer X evidence"
 * line, deliberately distinct from the analysis transitions below it --
 * Deliverable 2) are shown prominently, or an honest "first recorded"/
 * "nothing changed" note when neither exists. The full, unfiltered,
 * potentially-long history sits behind one `ExpandableDetail`, fetched
 * lazily -- the same "never overwhelming" progressive-disclosure
 * discipline `ExplanationPanel`/`EvidenceQualityPanel` already
 * establish. The clarifying line under the heading exists because this
 * panel sits on the same page as "What Changed" (Change Intelligence)
 * -- Deliverable 8 requires the two are never mistaken for each other:
 * "What Changed" is an interpretation of the latest analysis delta,
 * this panel is the factual chronology of evidence and stored
 * analytical transitions.
 */
export function EvidenceTimelinePanel({ caseId, history, t }: { caseId: string; history: EvidenceHistoryView; t: Translate }) {
  const [fullHistory, setFullHistory] = useState<FullHistoryStatus>({ kind: "idle" });

  function handleOpen(open: boolean) {
    if (!open || fullHistory.kind !== "idle") return;
    setFullHistory({ kind: "loading" });
    fetchEvidenceTimelineForCase(caseId)
      .then((entries) => setFullHistory(entries === null ? { kind: "unavailable" } : { kind: "loaded", entries }))
      .catch(() => setFullHistory({ kind: "unavailable" }));
  }

  const noHistoricalChange = history.transitions.length === 0 && history.newSourceEvidence.length === 0;
  const prominentTransitions = materialTransitions(history.transitions);
  const hasNonMaterialTransitions = prominentTransitions.length < history.transitions.length;
  const { shown: shownSourceEvidence, overflowCount: sourceEvidenceOverflow } = prominentSourceEvidence(history.newSourceEvidence);

  return (
    <Stack gap="metadata">
      <Text color="secondary" style={{ fontWeight: 600 }}>
        {t("evidenceTimeline.panel.heading")}
      </Text>
      <Text color="tertiary" as="p">{t("evidenceTimeline.panel.whatChangedClarifier")}</Text>

      {history.isBaseline && <Text color="tertiary" as="p">{t("evidenceTimeline.panel.baselineNote")}</Text>}

      {!history.isBaseline && noHistoricalChange && (
        <Text color="tertiary" as="p">{t("evidenceTimeline.panel.noChangeNote")}</Text>
      )}

      {!history.isBaseline && !noHistoricalChange && (
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
          {hasNonMaterialTransitions && (
            <Text color="tertiary" as="p">{t("evidenceTimeline.panel.additionalNonMaterialNote")}</Text>
          )}
        </Stack>
      )}

      <ExpandableDetail summaryLabel={t("evidenceTimeline.panel.expandLabel")} onToggle={handleOpen}>
        {fullHistory.kind === "loading" && <Text color="tertiary">{t("common.loading")}</Text>}
        {fullHistory.kind === "unavailable" && <Text color="tertiary">{t("evidenceTimeline.panel.emptyHistory")}</Text>}
        {fullHistory.kind === "loaded" && (
          <Stack gap="inter-section">
            {fullHistory.entries.length === 0 && <Text color="tertiary">{t("evidenceTimeline.panel.emptyHistory")}</Text>}
            {[...fullHistory.entries].reverse().map((entry, index) => (
              <Stack key={index} gap="metadata">
                <Text color="tertiary" as="p" style={{ fontWeight: 600 }}>
                  {t("evidenceTimeline.panel.recordedAtLabel")} {new Date(entry.snapshot.capturedAt).toLocaleDateString()}
                </Text>
                {entry.history.isBaseline && <Text color="tertiary" as="p">{t("evidenceTimeline.panel.baselineNote")}</Text>}
                {!entry.history.isBaseline && entry.history.transitions.length === 0 && entry.history.newSourceEvidence.length === 0 && (
                  <Text color="tertiary" as="p">{t("evidenceTimeline.panel.noChangeNote")}</Text>
                )}
                {entry.history.newSourceEvidence.map((event, eventIndex) => (
                  <Text key={eventIndex} color="tertiary" as="p">
                    {sourceEvidenceSentence(event, t)}
                  </Text>
                ))}
                {entry.history.transitions.map((transition) => (
                  <Inline key={transition.id} gap="metadata" align="center">
                    <StatusBadge
                      label={transitionCategoryLabel(transition.category, t)}
                      tone={EVIDENCE_TRANSITION_DIRECTION_TONE[transition.direction]}
                    />
                    <Text color="tertiary" as="span">
                      {transitionSentence(transition, t)}
                    </Text>
                  </Inline>
                ))}
              </Stack>
            ))}
          </Stack>
        )}
      </ExpandableDetail>
    </Stack>
  );
}

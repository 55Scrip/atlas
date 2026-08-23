import { useState } from "react";
import { Stack, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { coverageDimensionLabel, coverageReasonLabel } from "../coverage/describeCoverage";
import { materialEvidenceSentence } from "../materiality/describeMateriality";
import { fetchMaterialityForTicker, type MaterialityAssessmentView } from "../materiality/materialityApi";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";

type MaterialityFetchStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "unavailable" }
  | { kind: "loaded"; assessment: MaterialityAssessmentView };

/**
 * Atlas Intelligence Sprint 3 (Decision Explainability & Evidence
 * Trace, Deliverables 5/6/8), upgraded by the Materiality & Priority
 * Engine (Deliverables 6/7/9). One reusable "why does this deserve
 * attention" disclosure -- used on Daily Brief/Portfolio agenda rows
 * and Discovery candidate cards alike, everywhere a real ticker is on
 * hand but a full Investment Case page is one click further away.
 * Fetches lazily, only on first expand -- never eagerly for every row
 * on a list.
 *
 * Originally showed Explainability's own unranked `limitingFactors`
 * plus the most-valuable-missing pick; now fetches the Materiality
 * Engine's own already-ranked assessment instead and shows the single
 * most material contradicting/limiting reason plus the top missing
 * evidence -- the same real facts, now led with whichever one actually
 * matters most (Materiality's own "explain priority, do not replace
 * it" instruction), never a fact removed, only reordered.
 */
export function TickerExplanationDetail({ ticker, summaryLabel, t }: { ticker: string; summaryLabel: string; t: Translate }) {
  const [status, setStatus] = useState<MaterialityFetchStatus>({ kind: "idle" });

  function handleOpen(open: boolean) {
    if (!open || status.kind !== "idle") return;
    setStatus({ kind: "loading" });
    fetchMaterialityForTicker(ticker)
      .then((assessment) => setStatus(assessment === null ? { kind: "unavailable" } : { kind: "loaded", assessment }))
      .catch(() => setStatus({ kind: "unavailable" }));
  }

  return (
    <ExpandableDetail summaryLabel={summaryLabel} onToggle={handleOpen}>
      {status.kind === "loading" && <Text color="tertiary">{t("common.loading")}</Text>}
      {status.kind === "unavailable" && <Text color="tertiary">{t("explainability.panel.mostValuableMissingNone")}</Text>}
      {status.kind === "loaded" && (
        <Stack gap="metadata">
          <Text as="p" color="tertiary">
            {status.assessment.topMissingEvidence
              ? `${coverageDimensionLabel(status.assessment.topMissingEvidence.dimension, t)}${
                  status.assessment.topMissingEvidence.reasoning[0]
                    ? ` — ${coverageReasonLabel(status.assessment.topMissingEvidence.dimension, status.assessment.topMissingEvidence.reasoning[0], t)}`
                    : ""
                }`
              : t("explainability.panel.mostValuableMissingNone")}
          </Text>
          {status.assessment.topLimitingFactor && (
            <Text color="tertiary" as="p">
              {materialEvidenceSentence(status.assessment.topLimitingFactor, t)}
            </Text>
          )}
          {status.assessment.topContradictingEvidence && (
            <Text color="tertiary" as="p">
              {materialEvidenceSentence(status.assessment.topContradictingEvidence, t)}
            </Text>
          )}
        </Stack>
      )}
    </ExpandableDetail>
  );
}

import { useState } from "react";
import { Inline, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { EVIDENCE_QUALITY_LEVEL_KEY, EVIDENCE_QUALITY_LEVEL_TONE } from "../status/statusTone";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { evidenceWarningSentence } from "./describeEvidenceQuality";
import { fetchEvidenceQualityForTicker, type EvidenceQualityReportView } from "./evidenceQualityApi";

type FetchStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "unavailable" }
  | { kind: "loaded"; report: EvidenceQualityReportView };

/**
 * Atlas Intelligence Sprint 4 (Evidence Quality & Conflict Resolution,
 * Deliverables 6/7/9). One reusable "how reliable is this evidence"
 * disclosure -- used on Daily Brief/Portfolio agenda rows and Discovery
 * candidate cards alike, mirroring `TickerExplanationDetail`'s own
 * exact lazy-fetch shape (Sprint 3): fetches only on first expand, so
 * the cost of a fresh evidence-quality assessment is paid only when an
 * investor actually asks, never eagerly for every row on a list.
 */
export function TickerEvidenceQualityDetail({ ticker, summaryLabel, t }: { ticker: string; summaryLabel: string; t: Translate }) {
  const [status, setStatus] = useState<FetchStatus>({ kind: "idle" });

  function handleOpen(open: boolean) {
    if (!open || status.kind !== "idle") return;
    setStatus({ kind: "loading" });
    fetchEvidenceQualityForTicker(ticker)
      .then((report) => setStatus(report === null ? { kind: "unavailable" } : { kind: "loaded", report }))
      .catch(() => setStatus({ kind: "unavailable" }));
  }

  return (
    <ExpandableDetail summaryLabel={summaryLabel} onToggle={handleOpen}>
      {status.kind === "loading" && <Text color="tertiary">{t("common.loading")}</Text>}
      {status.kind === "unavailable" && <Text color="tertiary">{t("evidenceQuality.warning.noEvidence")}</Text>}
      {status.kind === "loaded" && (
        <Stack gap="metadata">
          <Inline gap="metadata" align="center">
            <StatusBadge
              label={t(EVIDENCE_QUALITY_LEVEL_KEY[status.report.quality])}
              tone={EVIDENCE_QUALITY_LEVEL_TONE[status.report.quality]}
            />
          </Inline>
          {status.report.warnings.map((code, index) => (
            <Text key={index} color="tertiary" as="p">
              {evidenceWarningSentence(code, t)}
            </Text>
          ))}
        </Stack>
      )}
    </ExpandableDetail>
  );
}

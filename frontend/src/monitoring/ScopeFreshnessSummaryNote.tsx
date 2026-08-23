import { Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import type { ScopeFreshnessSummaryView } from "./monitoringApi";

/**
 * Atlas Intelligence Sprint 9 (Data Ingestion & Automatic Refresh,
 * Deliverable 8/9). One calm summary line for Portfolio's/Watchlist's
 * own "how many are waiting on new data" question, shared between the
 * two rather than written twice -- same convention as
 * `MonitoringFreshnessNote` (Sprint 8) being shared across Daily
 * Brief/Portfolio/Watchlist.
 */
export function ScopeFreshnessSummaryNote({ summary, t }: { summary: ScopeFreshnessSummaryView; t: Translate }) {
  const total = summary.waitingForAnalysis + summary.noNewData + summary.needsAttention;
  if (total === 0) return null;

  return (
    <Text color="tertiary">
      {t("monitoring.freshnessSummary.line", {
        waiting: summary.waitingForAnalysis,
        current: summary.noNewData,
        attention: summary.needsAttention,
      })}
    </Text>
  );
}

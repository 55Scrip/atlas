import { Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import type { TranslationKey } from "../i18n";
import type { ScopeFreshnessSummaryView } from "./monitoringApi";

/**
 * Atlas Intelligence Sprint 9 (Data Ingestion & Automatic Refresh,
 * Deliverable 8/9). One calm summary line for Portfolio's/Watchlist's
 * own "how many are waiting on new data" question, shared between the
 * two rather than written twice -- same convention as
 * `MonitoringFreshnessNote` (Sprint 8) being shared across Daily
 * Brief/Portfolio/Watchlist.
 *
 * RC-1 Phase 4 (Density Pass) -- confirmed live: this exact sentence
 * shape rendered on all three pages with three different real counts
 * and no indication they were different scopes, reading as though the
 * same number might be disagreeing with itself. `scopeKey` is a
 * required, page-supplied phrase ("in your portfolio," "in your
 * watchlist," "across your portfolio and watchlist") so the sentence
 * discloses its own scope instead of leaving the reader to guess.
 */
export function ScopeFreshnessSummaryNote({ summary, scopeKey, t }: { summary: ScopeFreshnessSummaryView; scopeKey: TranslationKey; t: Translate }) {
  const total = summary.waitingForAnalysis + summary.noNewData + summary.needsAttention;
  if (total === 0) return null;

  return (
    <Text color="tertiary">
      {t("monitoring.freshnessSummary.line", {
        waiting: summary.waitingForAnalysis,
        current: summary.noNewData,
        attention: summary.needsAttention,
        scope: t(scopeKey),
      })}
    </Text>
  );
}

import { Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import type { MonitoringOperationalStatusView } from "./monitoringApi";

/**
 * Atlas Intelligence Sprint 8 (Automated Monitoring Operations,
 * Deliverable 8/9/10/16). One subtle, calm line -- never a badge, never
 * a warning icon (Deliverable 23's own "professional, not alarming"
 * tone, reused from Sprint 7). Shared by Daily Brief/Portfolio/
 * Watchlist rather than three separate implementations, so the wording
 * for each operational state is written exactly once.
 */
export function MonitoringFreshnessNote({ status, t }: { status: MonitoringOperationalStatusView; t: Translate }) {
  const time = status.lastRunCompletedAt ? new Date(status.lastRunCompletedAt).toLocaleString() : null;

  if (status.status === "up_to_date" && time) {
    return <Text color="tertiary">{t("monitoring.freshness.upToDate", { time })}</Text>;
  }
  if (status.status === "pending" && time) {
    return <Text color="tertiary">{t("monitoring.freshness.pending", { time })}</Text>;
  }
  if (status.status === "running") {
    return <Text color="tertiary">{t("monitoring.freshness.running")}</Text>;
  }
  if (status.status === "failed") {
    return <Text color="tertiary">{t("monitoring.freshness.failed")}</Text>;
  }
  return <Text color="tertiary">{t("monitoring.freshness.unknown")}</Text>;
}

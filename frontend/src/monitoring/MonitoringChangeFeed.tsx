import { Divider, Inline, Link, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import type { TranslationKey } from "../i18n";
import { MONITORING_STATUS_KEY, MONITORING_STATUS_TONE, type MonitoringStatus } from "../status/statusTone";
import { describeMonitoringCategory } from "../dailyBriefAgenda/describeReasonFact";
import type { MonitoringChangeView, MonitoringResultView } from "./monitoringApi";

const SOURCE_CAPABILITY_KEY: Record<string, TranslationKey> = {
  evidence_timeline: "monitoring.changeFeed.sourceEvidenceTimeline",
  change_intelligence: "monitoring.changeFeed.sourceChangeIntelligence",
  case_condition: "monitoring.changeFeed.sourceCaseCondition",
};

const MATERIALITY_KEY: Record<string, TranslationKey> = {
  material: "monitoring.changeFeed.materialityMaterial",
  minor: "monitoring.changeFeed.materialityMinor",
};

/** Product Intelligence Sprint 3 (Monitoring Intelligence Activation).
 * Mirrors the precedence `atlas.alpha.monitoring.engine.derive_status`'s
 * own if/elif chain already encodes -- `CHANGED_HIGH_IMPORTANCE` is
 * checked first, then `CHANGED_REVIEW_SUGGESTED`, then
 * `WAITING_FOR_BETTER_EVIDENCE`, else `UP_TO_DATE` -- restated here as a
 * fixed display-order rank only, never a new severity judgment (same
 * discipline as Watchlist's own `PRIORITY_RANK` reuse). `UNAVAILABLE`
 * results carry no changes and never reach this list at all (see
 * `MonitoringChangeFeed` below). */
const STATUS_RANK: Record<MonitoringStatus, number> = {
  changed_high_importance: 3,
  changed_review_suggested: 2,
  waiting_for_better_evidence: 1,
  up_to_date: 0,
  unavailable: -1,
};

/**
 * Product Intelligence Sprint 3 (Monitoring Intelligence Activation).
 * The one, unified rendering of `GET /api/monitoring/results`
 * (`fetchMonitoringResults`, `atlas.alpha.monitoring`, Atlas
 * Intelligence Sprint 7/8) -- a complete, already-computed change feed
 * that had zero frontend callers before this sprint (only the
 * aggregate operational status half, `/api/monitoring/status`, was
 * ever read, via `MonitoringFreshnessNote`/`ScopeFreshnessSummaryNote`).
 *
 * Deliberately spans both Portfolio and Watchlist scope in one list,
 * never split into "Portfolio changes"/"Watchlist changes" sections --
 * that framing already belongs to Portfolio and Watchlist themselves;
 * Monitoring's own job is the cross-cutting change feed neither of
 * those pages provides. Every field rendered is a direct read of
 * `MonitoringResultView`/`MonitoringChangeView`; nothing here
 * reclassifies, re-scores, or recomputes anything.
 */
export function MonitoringChangeFeed({
  results,
  t,
  onOpenInvestmentCase,
}: {
  results: MonitoringResultView[];
  t: Translate;
  onOpenInvestmentCase: (caseId: string, ticker: string | null) => void;
}) {
  const withChanges = results
    .filter((result) => result.changes.length > 0)
    .sort((a, b) => STATUS_RANK[b.status as MonitoringStatus] - STATUS_RANK[a.status as MonitoringStatus]);
  const unavailableCount = results.filter((result) => result.status === "unavailable").length;

  if (withChanges.length === 0 && unavailableCount === 0) {
    return <Text color="secondary">{t("monitoring.changeFeed.empty")}</Text>;
  }

  return (
    <Stack gap="inter-section">
      {withChanges.length === 0 && <Text color="secondary">{t("monitoring.changeFeed.empty")}</Text>}
      {withChanges.map((result) => (
        <MonitoringResultCard key={result.caseId} result={result} t={t} onOpenInvestmentCase={onOpenInvestmentCase} />
      ))}
      {unavailableCount > 0 && (
        <Text color="tertiary">
          {t(
            unavailableCount === 1 ? "monitoring.changeFeed.unavailableCountOne" : "monitoring.changeFeed.unavailableCountOther",
            { count: unavailableCount },
          )}
        </Text>
      )}
    </Stack>
  );
}

function MonitoringResultCard({
  result,
  t,
  onOpenInvestmentCase,
}: {
  result: MonitoringResultView;
  t: Translate;
  onOpenInvestmentCase: (caseId: string, ticker: string | null) => void;
}) {
  const label = result.ticker ?? result.caseId;
  const status = result.status as MonitoringStatus;
  return (
    <Stack gap="metadata">
      <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
        <Inline gap="row" align="baseline" wrap>
          <Text as="span" style={{ fontWeight: 600 }}>
            {label}
          </Text>
          <StatusBadge label={t(MONITORING_STATUS_KEY[status])} tone={MONITORING_STATUS_TONE[status]} />
        </Inline>
        <Link
          href="#"
          onClick={(event) => {
            event.preventDefault();
            onOpenInvestmentCase(result.caseId, result.ticker);
          }}
        >
          {t("dailyBrief.entry.openInvestmentCase")} →
        </Link>
      </Inline>
      <Stack gap="metadata">
        {result.changes.map((change) => (
          <MonitoringChangeRow key={change.id} change={change} t={t} />
        ))}
      </Stack>
      <Divider tone="hairline" />
    </Stack>
  );
}

function MonitoringChangeRow({ change, t }: { change: MonitoringChangeView; t: Translate }) {
  const isMinor = change.materiality === "minor";
  const sourceKey = SOURCE_CAPABILITY_KEY[change.sourceCapability];
  return (
    <Stack gap="metadata">
      <Text color={isMinor ? "tertiary" : "secondary"} as="p">
        {describeMonitoringCategory(change.category, t) ?? change.reason}
      </Text>
      <Text color="tertiary">
        {t(MATERIALITY_KEY[change.materiality] ?? "monitoring.changeFeed.materialityMinor")}
        {sourceKey ? ` · ${t(sourceKey)}` : ""}
      </Text>
    </Stack>
  );
}

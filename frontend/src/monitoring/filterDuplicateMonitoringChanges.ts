/**
 * Daily Brief Consolidation -- pure, frontend-only deduplication
 * between the Daily Brief agenda (primary inbox) and the Monitoring
 * Change Feed (secondary history), both already rendered on the same
 * page from two separate endpoints that read the identical underlying
 * facts (`atlas.alpha.daily_brief_agenda.service.py`'s own source #7
 * reads `MonitoringService.read_model().results` -- the exact same
 * `MonitoringChangeView.reason` string is threaded through, unmodified,
 * into the agenda's own signal text via `engine.monitoring_signal`).
 *
 * This is not fuzzy matching: `change.reason` and an agenda item's own
 * `reason[]` entry are the *same string*, from the same source object,
 * for a MATERIAL monitoring change -- exact equality is the correct,
 * structurally-grounded identity key here, not an approximation.
 *
 * A MINOR monitoring change is never promoted into the agenda at all
 * (`monitoring_signal` returns `None` for `materiality !== "material"`)
 * -- so it can never collide with an agenda reason, and always survives
 * this filter untouched. No information is hidden that isn't already
 * shown elsewhere.
 */
import type { MonitoringChangeView, MonitoringResultView } from "./monitoringApi";

export function filterDuplicateMonitoringChanges(
  results: MonitoringResultView[],
  agendaReasonsByTicker: Map<string, Set<string>>,
): MonitoringResultView[] {
  return results
    .map((result) => {
      const ticker = result.ticker;
      const agendaReasons = ticker ? agendaReasonsByTicker.get(ticker) : undefined;
      if (!agendaReasons) return result;
      const changes = result.changes.filter((change: MonitoringChangeView) => !agendaReasons.has(change.reason));
      return changes.length === result.changes.length ? result : { ...result, changes };
    })
    .filter((result) => result.changes.length > 0 || result.status === "unavailable");
}

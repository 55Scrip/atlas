/**
 * Daily Brief Consolidation -- pure, frontend-only deduplication
 * between the Daily Brief agenda (primary inbox) and the Monitoring
 * Change Feed (secondary history), both already rendered on the same
 * page from two separate endpoints that read the identical underlying
 * facts (`atlas.alpha.daily_brief_agenda.service.py`'s own source #7
 * reads `MonitoringService.read_model().results` -- the same
 * `MonitoringChangeView.reason` string underlies the agenda's own
 * signal text via `engine.monitoring_signal`).
 *
 * Atlas UX Phase 7B, Phase 1 fix: exact string equality turned out to
 * under-match in practice -- confirmed live, NVDA's real capex signal
 * still appeared in both sections, because a case-condition-sourced
 * agenda reason arrives from the backend already wrapped in its own
 * ticker prefix and "(Satisfied)" suffix ("NVDA: Data center capex
 * growth decelerates below 10% YoY (Satisfied)"), while Monitoring's own
 * `change.reason` carries the bare fact only ("Data center capex growth
 * decelerates below 10% YoY"). Same underlying fact, two differently-
 * wrapped strings -- exact `Set.has` never caught it. Containment
 * (either string appearing inside the other) still requires the real,
 * specific sentence to match, so it stays a structurally-grounded
 * identity check, not a fuzzy heuristic that could coincidentally
 * suppress an unrelated real change.
 *
 * A MINOR monitoring change is never promoted into the agenda at all
 * (`monitoring_signal` returns `None` for `materiality !== "material"`)
 * -- so it can never collide with an agenda reason, and always survives
 * this filter untouched. No information is hidden that isn't already
 * shown elsewhere.
 */
import type { MonitoringChangeView, MonitoringResultView } from "./monitoringApi";

function isAlreadyShownInAgenda(reason: string, agendaReasons: Set<string>): boolean {
  for (const agendaReason of agendaReasons) {
    if (agendaReason.includes(reason) || reason.includes(agendaReason)) return true;
  }
  return false;
}

export function filterDuplicateMonitoringChanges(
  results: MonitoringResultView[],
  agendaReasonsByTicker: Map<string, Set<string>>,
): MonitoringResultView[] {
  return results
    .map((result) => {
      const ticker = result.ticker;
      const agendaReasons = ticker ? agendaReasonsByTicker.get(ticker) : undefined;
      if (!agendaReasons) return result;
      const changes = result.changes.filter((change: MonitoringChangeView) => !isAlreadyShownInAgenda(change.reason, agendaReasons));
      return changes.length === result.changes.length ? result : { ...result, changes };
    })
    .filter((result) => result.changes.length > 0 || result.status === "unavailable");
}

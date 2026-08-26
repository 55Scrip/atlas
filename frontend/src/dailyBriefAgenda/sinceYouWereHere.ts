/**
 * Since You Were Here -- pure, client-side comparison. The one new
 * backend concept this sprint introduces is `lastViewedAt`; everything
 * here reads only that value plus the Daily Brief agenda's own
 * already-real `since` field. No new judgment about what "meaningful"
 * means -- that is entirely the existing agenda's own, unmodified.
 *
 * Rule (no heuristics, no fuzzy logic):
 * - `lastViewedAt === null` (a genuine first visit): every agenda item
 *   is in scope -- there is no prior visit to compare against.
 * - Otherwise: an item counts only when it carries a real `since`
 *   timestamp *and* that timestamp is strictly after `lastViewedAt`.
 *   An item with `since === null` (most persistent conditions -- see
 *   this module's own test fixtures) can be neither proven new nor
 *   proven old, so it is never counted here -- it remains fully
 *   visible in the regular agenda above, just outside this specific,
 *   honest count.
 */
import type { AgendaItemView } from "./dailyBriefAgendaApi";

export function itemsSinceLastVisit(items: AgendaItemView[], lastViewedAt: string | null): AgendaItemView[] {
  if (lastViewedAt === null) return items;
  const lastViewedMs = new Date(lastViewedAt).getTime();
  return items.filter((item) => item.since !== null && new Date(item.since).getTime() > lastViewedMs);
}

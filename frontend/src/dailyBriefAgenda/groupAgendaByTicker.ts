/**
 * Daily Brief Compression (Trust Hardening follow-up) -- pure,
 * client-side grouping over the flat `AgendaItemView[]` the backend
 * already returns. No new backend field, no new endpoint: `ticker`,
 * `priority`, and `nature` are already real, already-present fields on
 * every item (`dailyBriefAgendaApi.ts`) -- this module only reorganizes
 * what already exists, per this sprint's own "presentation,
 * prioritization and communication only" scope.
 *
 * One ticker's items collapse into one `TickerAgendaGroup`; an item
 * with no ticker (a portfolio-wide/system item) stays its own
 * single-item group, since there is nothing real to group it with.
 */
import { PRIORITY_LEVEL_RANK } from "../status/statusTone";
import type { AgendaItemView, PriorityLevel } from "./dailyBriefAgendaApi";

export interface TickerAgendaGroup {
  /** `null` only for a portfolio-wide/system item with no ticker. */
  ticker: string | null;
  items: AgendaItemView[];
  /** The highest `PriorityLevel` among this group's own items -- never
   * recomputed from anything but the real per-item values already on
   * the wire. */
  topPriority: PriorityLevel;
  /** `true` when at least one item in this group is a genuine change
   * event (`nature === "change_event"`) rather than only persistent,
   * already-known conditions -- used to rank "something changed" above
   * "still true from before," never to hide the persistent items. */
  hasChangeEvent: boolean;
  /** Deduplicated, ordered reason lines across every item in the group
   * -- each item's own `headline` plus its own `reason` entries, with
   * exact-text duplicates collapsed (Deliverable 3's own "never repeat
   * the same reason twice"). Order preserved: highest-priority item's
   * lines first. */
  reasons: string[];
}

function reasonLinesFor(item: AgendaItemView): string[] {
  const lines = [item.headline, ...item.reason];
  return lines.filter((line, index) => lines.indexOf(line) === index);
}

/** Highest priority first; within equal priority, a group carrying a
 * genuine change event ranks above one that is only persistent
 * conditions -- "something changed" is more worth surfacing today than
 * "still true from yesterday," the same distinction `SignalNatureBadge`
 * already renders per-item, applied here at the group level. */
function compareGroups(a: TickerAgendaGroup, b: TickerAgendaGroup): number {
  const priorityDelta = PRIORITY_LEVEL_RANK[b.topPriority] - PRIORITY_LEVEL_RANK[a.topPriority];
  if (priorityDelta !== 0) return priorityDelta;
  if (a.hasChangeEvent !== b.hasChangeEvent) return a.hasChangeEvent ? -1 : 1;
  return 0;
}

export function groupAgendaByTicker(items: AgendaItemView[]): TickerAgendaGroup[] {
  const byTicker = new Map<string, AgendaItemView[]>();
  const standalone: AgendaItemView[] = [];

  for (const item of items) {
    if (item.ticker === null) {
      standalone.push(item);
      continue;
    }
    const existing = byTicker.get(item.ticker);
    if (existing) existing.push(item);
    else byTicker.set(item.ticker, [item]);
  }

  const groups: TickerAgendaGroup[] = [];
  for (const [ticker, groupItems] of byTicker) {
    // `groupItems` is never empty -- a Map entry only ever comes into
    // being seeded with its first real item, above.
    const topPriority = groupItems.reduce<PriorityLevel>(
      (best, item) => (PRIORITY_LEVEL_RANK[item.priority] > PRIORITY_LEVEL_RANK[best] ? item.priority : best),
      groupItems[0]!.priority,
    );
    const sortedItems = [...groupItems].sort(
      (a, b) => PRIORITY_LEVEL_RANK[b.priority] - PRIORITY_LEVEL_RANK[a.priority],
    );
    const reasons = sortedItems
      .flatMap((item) => reasonLinesFor(item))
      .filter((line, index, all) => all.indexOf(line) === index);
    groups.push({
      ticker,
      items: sortedItems,
      topPriority,
      hasChangeEvent: groupItems.some((item) => item.nature === "change_event"),
      reasons,
    });
  }

  for (const item of standalone) {
    groups.push({
      ticker: null,
      items: [item],
      topPriority: item.priority,
      hasChangeEvent: item.nature === "change_event",
      reasons: reasonLinesFor(item),
    });
  }

  return groups.sort(compareGroups);
}

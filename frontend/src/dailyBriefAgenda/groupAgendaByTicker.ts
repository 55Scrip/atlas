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
import type { AgendaItemView, PriorityLevel, ReasonFactView } from "./dailyBriefAgendaApi";

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
  /** Implementation Sprint B1.1 (Backend Language Cleanup) -- parallel
   * to `reasons`, same length, same order (built from the identical
   * dedup pass, never a second, independently-ordered one): the
   * semantic fact behind that reason line, when its source has been
   * converted; `null` otherwise. `reasons` itself stays raw text,
   * unchanged, since `DailyBriefPage.tsx` still compares it by exact
   * string against Monitoring's own, separately-sourced reason text
   * (`filterDuplicateMonitoringChanges`) -- rendering (`TickerAgendaCard
   * .tsx`) is the one place that owns turning a `{ text, fact }` pair
   * into the final, localized line. */
  reasonFacts: (ReasonFactView | null)[];
}

/** One dedup pass producing both parallel arrays together, so `reasons`
 * and `reasonFacts` can never drift out of alignment the way two
 * independently-deduplicated passes could. `item.headline` always
 * equals `item.reason[j]` for some `j` (the backend's own
 * `_item_for_ticker` builds `headline` from the winning signal's
 * `reason`, and `reason` always includes it) -- that same index's own
 * `reasonFacts[j]` is reused as the headline's fact rather than
 * treating the headline as a fact-less, separate line. */
function reasonLinesFor(item: AgendaItemView): { text: string; fact: ReasonFactView | null }[] {
  const reasonFacts = item.reasonFacts ?? [];
  const headlineIndex = item.reason.indexOf(item.headline);
  const headlineFact = headlineIndex >= 0 ? (reasonFacts[headlineIndex] ?? null) : null;
  const pairs = [
    { text: item.headline, fact: headlineFact },
    ...item.reason.map((text, index) => ({ text, fact: reasonFacts[index] ?? null })),
  ];
  return pairs.filter(({ text }, index) => pairs.findIndex((p) => p.text === text) === index);
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
    const pairs = sortedItems
      .flatMap((item) => reasonLinesFor(item))
      .filter((pair, index, all) => all.findIndex((p) => p.text === pair.text) === index);
    groups.push({
      ticker,
      items: sortedItems,
      topPriority,
      hasChangeEvent: groupItems.some((item) => item.nature === "change_event"),
      reasons: pairs.map((p) => p.text),
      reasonFacts: pairs.map((p) => p.fact),
    });
  }

  for (const item of standalone) {
    const pairs = reasonLinesFor(item);
    groups.push({
      ticker: null,
      items: [item],
      topPriority: item.priority,
      hasChangeEvent: item.nature === "change_event",
      reasons: pairs.map((p) => p.text),
      reasonFacts: pairs.map((p) => p.fact),
    });
  }

  return groups.sort(compareGroups);
}

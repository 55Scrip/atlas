import type { TranslationKey } from "../i18n";
import { describeReasonFact } from "./describeReasonFact";
import type { AgendaItemView } from "./dailyBriefAgendaApi";

/**
 * Localization fix (Portfolio live-verification follow-up), generalized
 * by Implementation Sprint B1.1 (Backend Language Cleanup): a
 * `headline` (`item.headline`) is a raw, backend-composed English
 * sentence by default -- bypassing this app's own `t()` localization
 * entirely, the one gap in an otherwise fully localized Swedish UI.
 * `item.headline` always equals `item.reason[j]` for some `j` (the
 * backend's own `_item_for_ticker` builds `headline` from the winning
 * signal's `reason`, which `reason` always includes) -- that same
 * index's own `reasonFacts[j]` is reused here, so any source Sprint
 * B1.1 converted gets a translated headline too, not only its
 * secondary reason lines. Every other item's `headline` (a source not
 * yet converted) falls straight through unchanged.
 */
export function agendaItemHeadline(
  item: AgendaItemView,
  t: (key: TranslationKey, params?: Record<string, string | number>) => string,
): string {
  const index = item.reason.indexOf(item.headline);
  const fact = index >= 0 ? ((item.reasonFacts ?? [])[index] ?? null) : null;
  if (!fact) return item.headline;
  const fragment = describeReasonFact(fact, t);
  if (fragment === null) return item.headline;
  if (fact.code === "large_unallocated_capital") return fragment;
  return item.ticker ? `${fact.entity}: ${fragment}` : fragment;
}

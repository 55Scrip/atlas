import type { TranslationKey } from "../i18n";
import { ATTENTION_CATEGORY_KEY } from "../status/statusTone";
import type { AgendaItemView } from "./dailyBriefAgendaApi";

/**
 * Localization fix (Portfolio live-verification follow-up): a
 * workflow-sourced item's `headline` (`atlas.alpha.daily_brief_agenda
 * .engine.workflow_signal`) is a raw, backend-composed English
 * sentence -- `f"{ticker}: {category.value.replace('_', ' ').lower()}
 * ({count} item(s))"` -- that bypassed this app's own `t()`
 * localization entirely, the one gap in an otherwise fully localized
 * Swedish UI. `attentionCategory`/`attentionCount` (populated only for
 * this one source) let this function compose and translate the same
 * sentence itself instead, matching the ticker-prefix shape the raw
 * string already had. Every other item's `headline` is untouched --
 * falls straight through unchanged.
 */
export function agendaItemHeadline(
  item: AgendaItemView,
  t: (key: TranslationKey, params?: Record<string, string | number>) => string,
): string {
  if (!item.attentionCategory || item.attentionCount == null) return item.headline;
  const phrase = t(ATTENTION_CATEGORY_KEY[item.attentionCategory], { count: item.attentionCount });
  return item.ticker ? `${item.ticker}: ${phrase}` : phrase;
}

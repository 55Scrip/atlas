import type { TranslationKey } from "../i18n";
import type { PriorityLevel } from "../status/statusTone";
import type { AgendaItemView, ReasonFactView } from "./dailyBriefAgendaApi";
import { groupAgendaByTicker, type TickerAgendaGroup } from "./groupAgendaByTicker";
import { agendaItemHeadline } from "./describeAgendaHeadline";
import { describeReasonLine } from "./describeReasonFact";

/**
 * Product Simplification Sprint 6E, Phase 1/3 (originally Portfolio-only,
 * extracted in Atlas UX Phase 7B, Phase 1 so Daily Brief shares the exact
 * same rule rather than a second, independently-maintained copy) --
 * Atlas's own internal decision-hygiene bookkeeping (a decision recorded
 * with no outcome yet, a decision missing its own note, an allocation
 * awaiting reconciliation, a stale Case, a candidate with no Case at all)
 * is process housekeeping, never an investment fact about the security --
 * an investor should never see it phrased as a red flag about the
 * company, and it must never be the reason a holding reads as Critical.
 * `no_evidence_recorded` is the one `missing_evidence` value that IS real
 * investment content ("Atlas has not evaluated this company yet") and is
 * deliberately kept real content, not bookkeeping.
 */
export function isBookkeepingFact(fact: ReasonFactView | null): boolean {
  if (!fact) return false;
  if (fact.code === "workflow_gap") return true;
  if (fact.code === "missing_evidence" && fact.value !== "no_evidence_recorded") return true;
  return false;
}

/** This item's own reason lines with the real investment content only --
 * Atlas's own bookkeeping lines excluded. A line with no structured fact
 * yet (`fact === null`, a source not yet converted to the semantic-
 * reason-code contract) is always kept: absent positive evidence it is
 * bookkeeping, it is treated as real. */
export function realReasonLines(item: AgendaItemView): { text: string; fact: ReasonFactView | null }[] {
  return item.reason
    .map((text, index) => ({ text, fact: item.reasonFacts?.[index] ?? null }))
    .filter(({ fact }) => !isBookkeepingFact(fact));
}

export function hasRealReason(item: AgendaItemView): boolean {
  return realReasonLines(item).length > 0;
}

/** The item's own priority is the backend's real, already-computed value
 * whenever at least one real reason exists for this ticker today --
 * trusted as-is, never recomputed. When literally every reason is
 * Atlas's own bookkeeping, this cannot honestly read as an investment
 * issue, regardless of which workflow priority the backend assigned the
 * underlying housekeeping signal. */
export function displayPriority(item: AgendaItemView): PriorityLevel {
  return hasRealReason(item) ? item.priority : "low";
}

/** The best real headline text for one holding/ticker's reason cell: the
 * item's own headline when it is itself real content, otherwise the
 * first remaining real reason line -- never Atlas's own bookkeeping
 * phrasing, and `null` only when nothing real exists at all for this
 * ticker today. */
export function realHeadlineText(
  item: AgendaItemView,
  t: (key: TranslationKey, params?: Record<string, string | number>) => string,
): string | null {
  const real = realReasonLines(item);
  if (real.length === 0) return null;
  const headlineIndex = item.reason.indexOf(item.headline);
  const headlineFact = headlineIndex >= 0 ? (item.reasonFacts?.[headlineIndex] ?? null) : null;
  if (!isBookkeepingFact(headlineFact)) return agendaItemHeadline(item, t);
  return describeReasonLine(real[0]!.text, real[0]!.fact, t);
}

/** The same group `groupAgendaByTicker` already builds, with Atlas's own
 * bookkeeping reason lines excluded from what's shown -- the group only
 * ever contains items with at least one real reason when the caller
 * pre-filters via `hasRealReason` before grouping, so `topPriority` is
 * always driven by a real signal; this only strips bookkeeping LINES a
 * surviving item's own `reason[]` still mixed in alongside a real one
 * (e.g. a real case-condition line bundled with a "decision without
 * outcome" line for the same ticker). */
export function sanitizeGroupReasons(group: TickerAgendaGroup): TickerAgendaGroup {
  const keptIndexes = group.reasonFacts
    .map((fact, index) => ({ fact, index }))
    .filter(({ fact }) => !isBookkeepingFact(fact))
    .map(({ index }) => index);
  return {
    ...group,
    reasons: keptIndexes.map((i) => group.reasons[i]!),
    reasonFacts: keptIndexes.map((i) => group.reasonFacts[i]!),
  };
}

/** The one grouping every page that shows the Agenda by ticker should
 * use (Portfolio's Attention Required, Daily Brief's own Today's
 * Agenda): items with nothing real to say are excluded before grouping
 * (so a ticker whose entire agenda is bookkeeping never gets a group,
 * and never counts toward a Critical/attention total), and any real
 * item's own remaining bookkeeping LINES are stripped after grouping.
 * Atlas UX Phase 7B, Phase 1 -- previously duplicated ad hoc at each
 * call site; now the one shared derivation both pages call. */
export function realAgendaGroups(items: AgendaItemView[]): TickerAgendaGroup[] {
  return groupAgendaByTicker(items.filter(hasRealReason)).map(sanitizeGroupReasons);
}

/**
 * Daily Brief 2.0's own sentence for one change-log entry -- reuses
 * `describeReasonFact.ts`'s existing, already-tested translation table
 * rather than inventing a second vocabulary for the same closed
 * `ReasonCode` enum (this codebase's own standing rule: "the same
 * reason must never appear differently depending on where it is
 * rendered"). `ChangeLogEntryView` carries the identical fields a
 * `ReasonFactView` does (`entity` here is always the entry's own
 * ticker, since the change log is already scoped per-company); this
 * module is the one place that reshapes one into the other.
 *
 * Falls back to the entry's own real, already-rendered `headline` --
 * never a blank line, and never invented causal language (e.g. "after
 * quarterly results") the backend did not itself compute.
 */
import type { ReasonFactView } from "./dailyBriefAgendaApi";
import type { ChangeLogEntryView } from "./dailyBriefChangeLogApi";
import { describeReasonFact } from "./describeReasonFact";

type Translate = (key: import("../i18n").TranslationKey, params?: Record<string, string | number>) => string;

export function describeChangeLogEntry(entry: ChangeLogEntryView, t: Translate): string {
  const fact: ReasonFactView = {
    code: entry.reasonCode,
    entity: entry.ticker,
    value: entry.value,
    secondaryValue: entry.secondaryValue,
    label: entry.label,
    count: null,
  };
  return describeReasonFact(fact, t) ?? entry.headline;
}

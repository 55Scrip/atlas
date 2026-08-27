/**
 * Thin typed client for Daily Brief 2.0's change log
 * (`atlas/alpha/daily_brief_change_log/api/`). This is the durable
 * "what changed since you last looked" source -- distinct from
 * `dailyBriefAgendaApi.ts`'s own `DailyBriefAgendaView`, which is
 * Atlas's *current* view, recomputed fresh on every call. Field names
 * mirror `TickerChangeGroupView`/`ChangeLogEntryView` exactly
 * (camelCase, via the backend's own `CamelModel`).
 */

import type { ReasonCode } from "./dailyBriefAgendaApi";

export interface ChangeLogEntryView {
  id: string;
  ticker: string;
  caseId: string | null;
  reasonCode: ReasonCode;
  value: string | null;
  secondaryValue: string | null;
  label: string | null;
  headline: string;
  detectedAt: string;
  seenAt: string | null;
}

/** One card's worth of material -- `primary` is the single fact this
 * ticker is represented by (Phase 10, "one company = one message");
 * `additionalCount` is how many other real, eligible facts exist for
 * the same ticker, never dropped, surfaced instead via a "view
 * remaining changes" disclosure the caller builds from the raw agenda
 * or the Investment Case itself. `isNew` reflects `primary`'s own
 * `seenAt` only -- never a lower-ranked fact's. */
export interface TickerChangeGroupView {
  ticker: string;
  primary: ChangeLogEntryView;
  additionalCount: number;
  isNew: boolean;
}

export async function fetchDailyBriefChangeLog(userId: string, signal?: AbortSignal): Promise<TickerChangeGroupView[]> {
  const response = await fetch(`/api/daily-brief-change-log?userId=${encodeURIComponent(userId)}`, {
    signal: signal ?? null,
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as TickerChangeGroupView[];
}

/** Marks the given change ids seen (Phase 8/9) -- deliberately not
 * "resolved" or "acknowledged"; the user is never required to act on
 * a recommendation, only to have looked at it. Returns the fresh, full
 * list post-mark, exactly like `fetchDailyBriefChangeLog`'s own shape,
 * so a caller can swap state in one step without a second fetch. */
export async function markDailyBriefChangesSeen(
  userId: string,
  changeIds: string[],
  signal?: AbortSignal,
): Promise<TickerChangeGroupView[]> {
  const response = await fetch(`/api/daily-brief-change-log/mark-seen?userId=${encodeURIComponent(userId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ changeIds }),
    signal: signal ?? null,
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as TickerChangeGroupView[];
}

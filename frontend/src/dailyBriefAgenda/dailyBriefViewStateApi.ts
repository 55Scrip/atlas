/**
 * Thin typed client for Since You Were Here's one piece of new state
 * (`atlas/alpha/daily_brief_view_state/api/`). Two calls, deliberately
 * kept separate -- see the backend router's own docstring for why
 * reading the previous value and marking a new one can never be
 * combined into a single request.
 */

export interface DailyBriefViewStateView {
  lastViewedAt: string | null;
}

export async function fetchDailyBriefViewState(userId: string, signal?: AbortSignal): Promise<DailyBriefViewStateView> {
  const response = await fetch(`/api/daily-brief/view-state?userId=${encodeURIComponent(userId)}`, {
    signal: signal ?? null,
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DailyBriefViewStateView;
}

export async function markDailyBriefViewed(userId: string, signal?: AbortSignal): Promise<DailyBriefViewStateView> {
  const response = await fetch(`/api/daily-brief/view-state/mark-viewed?userId=${encodeURIComponent(userId)}`, {
    method: "POST",
    signal: signal ?? null,
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DailyBriefViewStateView;
}

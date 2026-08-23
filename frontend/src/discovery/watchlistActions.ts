/**
 * Thin wrappers over the existing `/api/alpha-watchlist` endpoints
 * (`atlas/alpha/watchlist/api/router.py`), mirroring the exact request/
 * response shapes `WatchlistPage.tsx` already uses -- Discovery reuses
 * the same Watchlist persistence, never a second one (Deliverable 7).
 * `addTicker` always returns a real `caseId`: `AlphaWatchlistService
 * .add_ticker` ensures one server-side (creating it if none exists yet),
 * which is also how Discovery "opens/creates" a new candidate's
 * Investment Case (Deliverable 2) -- there is no separate case-creation
 * call for a non-Portfolio ticker.
 */

export interface WatchlistEntryView {
  ticker: string;
  caseId: string;
  addedAt: string;
}

export type AddToWatchlistResult =
  | { kind: "added"; entry: WatchlistEntryView }
  | { kind: "invalid" }
  | { kind: "error" };

export async function addTickerToWatchlist(ticker: string): Promise<AddToWatchlistResult> {
  const response = await fetch("/api/alpha-watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker: ticker.trim().toUpperCase() }),
  });
  if (response.status === 400) return { kind: "invalid" };
  if (!response.ok) return { kind: "error" };
  const entry = (await response.json()) as WatchlistEntryView;
  return { kind: "added", entry };
}

export async function removeTickerFromWatchlist(ticker: string): Promise<boolean> {
  const response = await fetch(`/api/alpha-watchlist/${encodeURIComponent(ticker)}`, { method: "DELETE" });
  return response.ok;
}

export async function fetchWatchlist(signal?: AbortSignal): Promise<WatchlistEntryView[]> {
  const response = await fetch("/api/alpha-watchlist", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as WatchlistEntryView[];
}

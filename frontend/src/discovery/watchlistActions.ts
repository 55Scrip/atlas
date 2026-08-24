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
 *
 * Internal Alpha Stabilization 1 (navigation/cache fix): also the
 * purpose-built, stale-while-revalidate shared data source for
 * `GET /api/alpha-watchlist` -- see `portfolio/alphaPortfolioData.ts`'s
 * own module docstring for the full rationale (the two are
 * deliberately independent, not a shared generic cache layer). Six
 * separate components previously ran this exact fetch on every mount
 * (three directly, three via `fetchWatchlist` below); `useAlphaWatchlist`
 * replaces all six with one shared, cached subscription.
 */
import { useEffect, useState } from "react";

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
  invalidateAlphaWatchlist();
  return { kind: "added", entry };
}

export async function removeTickerFromWatchlist(ticker: string): Promise<boolean> {
  const response = await fetch(`/api/alpha-watchlist/${encodeURIComponent(ticker)}`, { method: "DELETE" });
  if (response.ok) invalidateAlphaWatchlist();
  return response.ok;
}

export async function fetchWatchlist(signal?: AbortSignal): Promise<WatchlistEntryView[]> {
  const response = await fetch("/api/alpha-watchlist", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as WatchlistEntryView[];
}

export type AlphaWatchlistResource =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: WatchlistEntryView[] };

type Listener = (resource: AlphaWatchlistResource) => void;

let cached: AlphaWatchlistResource = { kind: "loading" };
let inFlight: Promise<void> | null = null;
const listeners = new Set<Listener>();

function publish(resource: AlphaWatchlistResource): void {
  cached = resource;
  listeners.forEach((listener) => listener(resource));
}

function revalidate(): Promise<void> {
  if (inFlight) return inFlight;
  inFlight = fetchWatchlist()
    .then((entries) => {
      publish({ kind: "loaded", entries });
    })
    .catch(() => {
      // Stale-while-revalidate: a failed background refresh must never
      // discard already-cached, still-useful data.
      if (cached.kind !== "loaded") publish({ kind: "error" });
    })
    .finally(() => {
      inFlight = null;
    });
  return inFlight;
}

/** Forces a background refetch -- called by `addTickerToWatchlist`/
 * `removeTickerFromWatchlist` above on success, and by any caller
 * (e.g. `WatchlistPage`'s own duplicated inline add/remove handlers)
 * whose mutation does not go through those two functions. */
export function invalidateAlphaWatchlist(): Promise<void> {
  return revalidate();
}

/** Seeds the cache directly -- for a caller (e.g. `DiscoveryPage`'s
 * "remove from watchlist" row action) that needs the removal to feel
 * instant rather than waiting for a real round trip, and to revert
 * cleanly if the backend call then fails. Read the current value first
 * via `getAlphaWatchlistSnapshot`, since it may have changed since this
 * component last rendered. */
export function setAlphaWatchlistData(entries: WatchlistEntryView[]): void {
  publish({ kind: "loaded", entries });
}

/** Current cached value, read synchronously (not a hook) -- for an
 * optimistic-update caller that needs the latest state at the moment
 * of a revert, not whatever it captured when the action started. */
export function getAlphaWatchlistSnapshot(): AlphaWatchlistResource {
  return cached;
}

export function useAlphaWatchlist(): AlphaWatchlistResource {
  const [resource, setResource] = useState<AlphaWatchlistResource>(cached);

  useEffect(() => {
    listeners.add(setResource);
    setResource(cached);
    void revalidate();
    return () => {
      listeners.delete(setResource);
    };
  }, []);

  return resource;
}

/** Test-only reset -- see `alphaPortfolioData.ts`'s own equivalent for
 * why this exists. */
export function __resetAlphaWatchlistCacheForTests(): void {
  cached = { kind: "loading" };
  inFlight = null;
  listeners.clear();
}

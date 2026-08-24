/**
 * Purpose-built, stale-while-revalidate shared data source for
 * `GET /api/alpha-portfolio` (Internal Alpha Stabilization 1,
 * navigation/cache fix). Before this module, 10 separate components
 * each ran their own independent `fetch("/api/alpha-portfolio", ...)`
 * on every mount, with zero reuse across navigation -- a routine
 * Portfolio -> Investment Case -> back-to-Portfolio flow re-downloaded
 * the full holdings list from scratch every single time, and every one
 * of those components rendered its own "loading" flash on every
 * revisit even though nothing had actually changed.
 *
 * Deliberately scoped to only this one endpoint -- see
 * `discovery/watchlistActions.ts` for the separate, independent
 * equivalent for `/api/alpha-watchlist`. This is not a general cache
 * layer for arbitrary future fetches; it does not generalize beyond
 * the two endpoints identified as genuinely, repeatedly duplicated.
 *
 * Every consumer immediately sees the last known-good response (no
 * "loading" flash on a revisit) and a background revalidation always
 * starts on mount -- the two halves of stale-while-revalidate.
 * Concurrent mounts share one in-flight request (`inFlight` below), so
 * several components mounting in the same tick never fire more than
 * one real network request.
 */
import { useEffect, useState } from "react";

export type AlphaPortfolioResource =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; data: unknown };

type Listener = (resource: AlphaPortfolioResource) => void;

let cached: AlphaPortfolioResource = { kind: "loading" };
let inFlight: Promise<void> | null = null;
const listeners = new Set<Listener>();

function publish(resource: AlphaPortfolioResource): void {
  cached = resource;
  listeners.forEach((listener) => listener(resource));
}

function revalidate(): Promise<void> {
  if (inFlight) return inFlight;
  inFlight = fetch("/api/alpha-portfolio")
    .then((response) => {
      if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
      return response.json();
    })
    .then((data: unknown) => {
      publish({ kind: "loaded", data });
    })
    .catch((error: unknown) => {
      // Stale-while-revalidate: a failed background refresh must never
      // discard already-cached, still-useful data -- surface the error
      // only when there was nothing to show yet.
      if (cached.kind !== "loaded") {
        publish({ kind: "error", message: error instanceof Error ? error.message : "Unknown error" });
      }
    })
    .finally(() => {
      inFlight = null;
    });
  return inFlight;
}

/**
 * Forces a background refetch. Call after a mutation whose response
 * does not already carry the full updated view (case-link, apply-
 * trade, import, from-scratch) -- see `setAlphaPortfolioData` for
 * mutations that do.
 */
export function invalidateAlphaPortfolio(): Promise<void> {
  return revalidate();
}

/**
 * Seeds the cache directly with an already-known-fresh value. Call
 * after a mutation whose response already *is* the updated view
 * (Portfolio's own `reconcile` endpoint), so every consumer sees the
 * new data immediately without a redundant extra GET.
 */
export function setAlphaPortfolioData(data: unknown): void {
  publish({ kind: "loaded", data });
}

export function useAlphaPortfolio(): AlphaPortfolioResource {
  const [resource, setResource] = useState<AlphaPortfolioResource>(cached);

  useEffect(() => {
    listeners.add(setResource);
    // The subscription above only catches updates from here on --
    // re-sync to whatever `cached` holds right now (it may have
    // changed between this component's render and this effect
    // running), then always kick off a background revalidation.
    setResource(cached);
    void revalidate();
    return () => {
      listeners.delete(setResource);
    };
  }, []);

  return resource;
}

/**
 * Test-only reset. This module is a real, intentional singleton at
 * runtime (that is the whole point), but each test needs a clean
 * slate -- call this in `beforeEach` rather than letting one test's
 * cached response leak into the next.
 */
export function __resetAlphaPortfolioCacheForTests(): void {
  cached = { kind: "loading" };
  inFlight = null;
  listeners.clear();
}

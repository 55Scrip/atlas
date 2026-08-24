import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import {
  __resetAlphaWatchlistCacheForTests,
  addTickerToWatchlist,
  getAlphaWatchlistSnapshot,
  invalidateAlphaWatchlist,
  removeTickerFromWatchlist,
  setAlphaWatchlistData,
  useAlphaWatchlist,
  type WatchlistEntryView,
} from "./watchlistActions";

const AAPL: WatchlistEntryView = { ticker: "AAPL", caseId: "case-aapl", addedAt: "2026-01-01T00:00:00Z" };
const TSLA: WatchlistEntryView = { ticker: "TSLA", caseId: "case-tsla", addedAt: "2026-01-02T00:00:00Z" };

function stubFetch(handler: (url: string, init?: RequestInit) => Promise<Response>) {
  const fetchMock = vi.fn(handler);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function jsonResponse(body: unknown, ok = true): Response {
  return { ok, json: () => Promise.resolve(body) } as Response;
}

beforeEach(() => {
  __resetAlphaWatchlistCacheForTests();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useAlphaWatchlist", () => {
  it("cache-reuse: a second mount after the cache is warm sees the cached entries immediately", async () => {
    let calls = 0;
    stubFetch(() => {
      calls += 1;
      return Promise.resolve(jsonResponse([AAPL]));
    });
    const first = renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(first.result.current.kind).toBe("loaded"));
    first.unmount();

    const second = renderHook(() => useAlphaWatchlist());
    expect(second.result.current).toEqual({ kind: "loaded", entries: [AAPL] });
    // The always-revalidate-on-mount half also fired again for this
    // second consumer -- immediate cached display and background
    // revalidation are not mutually exclusive.
    expect(calls).toBe(2);
  });

  it("background revalidation: a new mount on a warm cache refetches and every subscriber sees the update", async () => {
    let call = 0;
    stubFetch(() => {
      call += 1;
      return Promise.resolve(jsonResponse(call === 1 ? [AAPL] : [AAPL, TSLA]));
    });
    const first = renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(first.result.current).toEqual({ kind: "loaded", entries: [AAPL] }));

    renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(first.result.current).toEqual({ kind: "loaded", entries: [AAPL, TSLA] }));
  });

  it("dedup: two components mounting in the same tick share one in-flight request", async () => {
    const fetchMock = stubFetch(() => Promise.resolve(jsonResponse([AAPL])));
    let resultA: ReturnType<typeof renderHook<ReturnType<typeof useAlphaWatchlist>, unknown>>["result"];
    let resultB: ReturnType<typeof renderHook<ReturnType<typeof useAlphaWatchlist>, unknown>>["result"];

    act(() => {
      resultA = renderHook(() => useAlphaWatchlist()).result;
      resultB = renderHook(() => useAlphaWatchlist()).result;
    });

    await waitFor(() => expect(resultA.current.kind).toBe("loaded"));
    expect(resultB!.current.kind).toBe("loaded");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("a failed background revalidation never discards already-cached data", async () => {
    let call = 0;
    stubFetch(() => {
      call += 1;
      if (call === 1) return Promise.resolve(jsonResponse([AAPL]));
      return Promise.reject(new Error("network down"));
    });
    const first = renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(first.result.current).toEqual({ kind: "loaded", entries: [AAPL] }));

    renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(call).toBe(2));
    expect(first.result.current).toEqual({ kind: "loaded", entries: [AAPL] });
  });
});

describe("invalidation after mutation", () => {
  it("addTickerToWatchlist invalidates the shared cache on success -- a mounted consumer sees the new entry", async () => {
    let listCall = 0;
    stubFetch((url, init) => {
      if (init?.method === "POST") return Promise.resolve(jsonResponse(TSLA));
      listCall += 1;
      return Promise.resolve(jsonResponse(listCall === 1 ? [AAPL] : [AAPL, TSLA]));
    });
    const { result } = renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(result.current).toEqual({ kind: "loaded", entries: [AAPL] }));

    await act(async () => {
      await addTickerToWatchlist("TSLA");
    });

    await waitFor(() => expect(result.current).toEqual({ kind: "loaded", entries: [AAPL, TSLA] }));
  });

  it("addTickerToWatchlist does NOT invalidate on a rejected (validation) response", async () => {
    let listCall = 0;
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === "POST") {
        return Promise.resolve({ ok: false, status: 400, json: () => Promise.resolve({ detail: "invalid" }) } as Response);
      }
      listCall += 1;
      return Promise.resolve(jsonResponse([AAPL]));
    });
    const { result } = renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(result.current.kind).toBe("loaded"));
    const callsAfterMount = fetchMock.mock.calls.length;

    const outcome = await addTickerToWatchlist("BADTICKER");
    expect(outcome.kind).toBe("invalid");
    // No extra GET was triggered by a failed add.
    expect(fetchMock.mock.calls.length).toBe(callsAfterMount + 1); // +1 for the POST itself only
  });

  it("removeTickerFromWatchlist invalidates the shared cache on success", async () => {
    let listCall = 0;
    stubFetch((url, init) => {
      if (init?.method === "DELETE") return Promise.resolve(jsonResponse({}));
      listCall += 1;
      return Promise.resolve(jsonResponse(listCall === 1 ? [AAPL, TSLA] : [AAPL]));
    });
    const { result } = renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(result.current).toEqual({ kind: "loaded", entries: [AAPL, TSLA] }));

    await act(async () => {
      await removeTickerFromWatchlist("TSLA");
    });

    await waitFor(() => expect(result.current).toEqual({ kind: "loaded", entries: [AAPL] }));
  });

  it("removeTickerFromWatchlist does not invalidate when the backend call fails", async () => {
    stubFetch((url, init) => {
      if (init?.method === "DELETE") return Promise.resolve({ ok: false } as Response);
      return Promise.resolve(jsonResponse([AAPL]));
    });
    const { result } = renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(result.current).toEqual({ kind: "loaded", entries: [AAPL] }));

    const ok = await removeTickerFromWatchlist("AAPL");
    expect(ok).toBe(false);
    // The cache is untouched -- still shows AAPL, exactly as before.
    expect(result.current).toEqual({ kind: "loaded", entries: [AAPL] });
  });

  it("invalidateAlphaWatchlist forces a refetch directly", async () => {
    let call = 0;
    const fetchMock = stubFetch(() => {
      call += 1;
      return Promise.resolve(jsonResponse(call === 1 ? [AAPL] : [TSLA]));
    });
    const { result } = renderHook(() => useAlphaWatchlist());
    await waitFor(() => expect(result.current).toEqual({ kind: "loaded", entries: [AAPL] }));

    await act(async () => {
      await invalidateAlphaWatchlist();
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(result.current).toEqual({ kind: "loaded", entries: [TSLA] });
  });
});

describe("optimistic-update helpers (setAlphaWatchlistData / getAlphaWatchlistSnapshot)", () => {
  it("setAlphaWatchlistData seeds the cache synchronously, visible to every mounted subscriber", () => {
    stubFetch(() => Promise.resolve(jsonResponse([])));
    const { result } = renderHook(() => useAlphaWatchlist());

    act(() => {
      setAlphaWatchlistData([AAPL]);
    });

    expect(result.current).toEqual({ kind: "loaded", entries: [AAPL] });
  });

  it("getAlphaWatchlistSnapshot reads the current value synchronously, for a caller building an optimistic revert", () => {
    stubFetch(() => Promise.resolve(jsonResponse([])));
    act(() => {
      setAlphaWatchlistData([AAPL, TSLA]);
    });

    const snapshot = getAlphaWatchlistSnapshot();
    expect(snapshot).toEqual({ kind: "loaded", entries: [AAPL, TSLA] });
  });
});

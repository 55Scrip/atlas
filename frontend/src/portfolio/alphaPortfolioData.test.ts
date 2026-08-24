import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import {
  __resetAlphaPortfolioCacheForTests,
  invalidateAlphaPortfolio,
  setAlphaPortfolioData,
  useAlphaPortfolio,
} from "./alphaPortfolioData";

function mockFetch(responses: unknown[]) {
  const fetchMock = vi.fn(() => {
    const next = responses.length > 1 ? responses.shift() : responses[0];
    return Promise.resolve({ ok: true, json: () => Promise.resolve(next) } as Response);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  __resetAlphaPortfolioCacheForTests();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useAlphaPortfolio", () => {
  it("starts loading and resolves to the fetched data on a first, cold mount", async () => {
    mockFetch([{ exists: true, holdings: [{ ticker: "AAPL" }] }]);
    const { result } = renderHook(() => useAlphaPortfolio());

    expect(result.current.kind).toBe("loading");

    await waitFor(() => expect(result.current.kind).toBe("loaded"));
    expect(result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "AAPL" }] } });
  });

  it("cache-reuse: a second mount after the cache is warm sees the cached data immediately, never a loading flash", async () => {
    const fetchMock = mockFetch([{ exists: true, holdings: [{ ticker: "MSFT" }] }]);
    const first = renderHook(() => useAlphaPortfolio());
    await waitFor(() => expect(first.result.current.kind).toBe("loaded"));
    first.unmount();

    // A brand-new consumer -- simulating navigating back to a page that
    // uses this same hook -- must see the cached value synchronously,
    // on its very first render, not "loading" -- this is the core of
    // "cachead data visas direkt" and is true regardless of whether a
    // background revalidation is also kicked off (it always is; see
    // the "background revalidation" test below for that half).
    const second = renderHook(() => useAlphaPortfolio());
    expect(second.result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "MSFT" }] } });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("background revalidation: a fresh mount on a warm cache still triggers a real refetch and updates every subscriber when it resolves", async () => {
    const fetchMock = mockFetch([
      { exists: true, holdings: [{ ticker: "MSFT" }] },
      { exists: true, holdings: [{ ticker: "MSFT" }, { ticker: "AAPL" }] },
    ]);
    const first = renderHook(() => useAlphaPortfolio());
    await waitFor(() => expect(first.result.current.kind).toBe("loaded"));

    // Mounting again (e.g. a second consumer, or navigating back) must
    // start a second real background revalidation -- the "always
    // revalidate on mount" half of stale-while-revalidate.
    const second = renderHook(() => useAlphaPortfolio());
    // The cached value is shown immediately (still the first response)...
    expect(second.result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "MSFT" }] } });

    // ...and once the background revalidation resolves, both the
    // original and the new consumer see the fresh data.
    await waitFor(() =>
      expect(first.result.current).toEqual({
        kind: "loaded",
        data: { exists: true, holdings: [{ ticker: "MSFT" }, { ticker: "AAPL" }] },
      }),
    );
    expect(second.result.current).toEqual({
      kind: "loaded",
      data: { exists: true, holdings: [{ ticker: "MSFT" }, { ticker: "AAPL" }] },
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("dedup: two components mounting in the same tick share one in-flight request, never two real fetches", async () => {
    const fetchMock = mockFetch([{ exists: true, holdings: [] }]);
    let resultA: ReturnType<typeof renderHook<ReturnType<typeof useAlphaPortfolio>, unknown>>["result"];
    let resultB: ReturnType<typeof renderHook<ReturnType<typeof useAlphaPortfolio>, unknown>>["result"];

    act(() => {
      resultA = renderHook(() => useAlphaPortfolio()).result;
      resultB = renderHook(() => useAlphaPortfolio()).result;
    });

    await waitFor(() => expect(resultA.current.kind).toBe("loaded"));
    expect(resultB!.current.kind).toBe("loaded");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("invalidateAlphaPortfolio forces a real refetch and every mounted subscriber sees the new value", async () => {
    const fetchMock = mockFetch([
      { exists: true, holdings: [{ ticker: "MSFT" }] },
      { exists: true, holdings: [{ ticker: "NVDA" }] },
    ]);
    const { result } = renderHook(() => useAlphaPortfolio());
    await waitFor(() => expect(result.current.kind).toBe("loaded"));
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await invalidateAlphaPortfolio();
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "NVDA" }] } });
  });

  it("setAlphaPortfolioData seeds the cache directly, with no network call at all", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: true, holdings: [{ ticker: "SEEDED" }] }) } as Response),
    );
    vi.stubGlobal("fetch", fetchMock);

    act(() => {
      setAlphaPortfolioData({ exists: true, holdings: [{ ticker: "SEEDED" }] });
    });

    const { result } = renderHook(() => useAlphaPortfolio());
    // The seeded value is visible immediately, and the hook's own
    // always-revalidate-on-mount still fires a real request in the
    // background afterwards.
    expect(result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "SEEDED" }] } });
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  });

  it("a failed background revalidation never discards already-cached, still-useful data", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ exists: true, holdings: [{ ticker: "MSFT" }] }) })
      .mockRejectedValueOnce(new Error("network down"));
    vi.stubGlobal("fetch", fetchMock);

    const first = renderHook(() => useAlphaPortfolio());
    await waitFor(() => expect(first.result.current.kind).toBe("loaded"));

    const second = renderHook(() => useAlphaPortfolio());
    // Immediately visible: the last good data, not "loading" or "error".
    expect(second.result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "MSFT" }] } });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    // The failed background refetch must not have degraded either
    // subscriber's view -- the last good snapshot is still shown.
    expect(first.result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "MSFT" }] } });
    expect(second.result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "MSFT" }] } });
  });

  it("surfaces a real error only when there is nothing cached yet to show", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve(null) } as Response)),
    );
    const { result } = renderHook(() => useAlphaPortfolio());

    await waitFor(() => expect(result.current.kind).toBe("error"));
    expect(result.current).toMatchObject({ kind: "error" });
  });

  it("a component that unmounts no longer receives updates, but does not affect other still-mounted subscribers", async () => {
    const fetchMock = mockFetch([{ exists: true, holdings: [{ ticker: "MSFT" }] }, { exists: true, holdings: [{ ticker: "AAPL" }] }]);
    const first = renderHook(() => useAlphaPortfolio());
    await waitFor(() => expect(first.result.current.kind).toBe("loaded"));

    const second = renderHook(() => useAlphaPortfolio());
    first.unmount();

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    await waitFor(() =>
      expect(second.result.current).toEqual({ kind: "loaded", data: { exists: true, holdings: [{ ticker: "AAPL" }] } }),
    );
  });
});

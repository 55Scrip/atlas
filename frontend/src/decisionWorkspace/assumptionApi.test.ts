import { afterEach, describe, expect, it, vi } from "vitest";
import { challengeAssumption, createAssumption, retireAssumption, reviseAssumption } from "./assumptionApi";

function mockFetchOnce(body: unknown, ok = true, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(body),
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("assumptionApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("createAssumption POSTs to /api/decisions/{id}/assumptions with the given content", async () => {
    const fetchMock = mockFetchOnce({ assumptionId: "a1" });

    await createAssumption("decision-1", { statement: "GCP margin expansion", authorship: "atlas" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/decisions/decision-1/assumptions",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ statement: "GCP margin expansion", authorship: "atlas" }),
      }),
    );
  });

  it("reviseAssumption PATCHes to /api/assumptions/{id}", async () => {
    const fetchMock = mockFetchOnce({ assumptionId: "a1" });

    await reviseAssumption("a1", { statement: "revised text" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/assumptions/a1",
      expect.objectContaining({ method: "PATCH" }),
    );
  });

  it("challengeAssumption POSTs to /api/assumptions/{id}/challenge with severity", async () => {
    const fetchMock = mockFetchOnce({ assumptionId: "a1" });

    await challengeAssumption("a1", { note: "new evidence", severity: "invalidated" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/assumptions/a1/challenge",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ note: "new evidence", severity: "invalidated" }),
      }),
    );
  });

  it("retireAssumption POSTs to /api/assumptions/{id}/retire", async () => {
    const fetchMock = mockFetchOnce(null);

    await retireAssumption("a1");

    expect(fetchMock).toHaveBeenCalledWith("/api/assumptions/a1/retire", { method: "POST" });
  });

  it("throws when the backend responds with a non-ok status", async () => {
    mockFetchOnce({ detail: "not found" }, false, 404);

    await expect(reviseAssumption("unknown", {})).rejects.toThrow("404");
  });
});

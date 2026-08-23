import { afterEach, describe, expect, it, vi } from "vitest";
import { createCaseCondition, evaluateCaseCondition, retireCaseCondition, reviseCaseCondition } from "./caseConditionApi";

function mockFetchOnce(body: unknown, ok = true, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({ ok, status, json: () => Promise.resolve(body) });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("caseConditionApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("createCaseCondition POSTs to /api/cases/{id}/case-conditions with decisionId included", async () => {
    const fetchMock = mockFetchOnce({ conditionId: "c1" });

    await createCaseCondition("case-1", { predicateText: "China revenue trend", role: "monitoring", decisionId: "decision-1" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/cases/case-1/case-conditions",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ predicateText: "China revenue trend", role: "monitoring", decisionId: "decision-1" }),
      }),
    );
  });

  it("reviseCaseCondition PATCHes to /api/case-conditions/{id}", async () => {
    const fetchMock = mockFetchOnce({ conditionId: "c1" });

    await reviseCaseCondition("c1", { predicateText: "revised" });

    expect(fetchMock).toHaveBeenCalledWith("/api/case-conditions/c1", expect.objectContaining({ method: "PATCH" }));
  });

  it("evaluateCaseCondition POSTs to /api/case-conditions/{id}/evaluate", async () => {
    const fetchMock = mockFetchOnce({ satisfied: true, transitioned: true, condition: {} });

    const result = await evaluateCaseCondition("c1", { humanAssertedSatisfied: true });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/case-conditions/c1/evaluate",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ humanAssertedSatisfied: true }) }),
    );
    expect(result.satisfied).toBe(true);
  });

  it("retireCaseCondition POSTs to /api/case-conditions/{id}/retire", async () => {
    const fetchMock = mockFetchOnce(null);

    await retireCaseCondition("c1");

    expect(fetchMock).toHaveBeenCalledWith("/api/case-conditions/c1/retire", { method: "POST" });
  });

  it("throws when the backend responds with a non-ok status", async () => {
    mockFetchOnce({ detail: "conflict" }, false, 409);

    await expect(retireCaseCondition("c1")).rejects.toThrow("409");
  });
});

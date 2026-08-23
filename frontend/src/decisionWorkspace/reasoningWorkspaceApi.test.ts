import { afterEach, describe, expect, it, vi } from "vitest";
import {
  commitDraftWithReasoning,
  fetchActiveAssumptions,
  fetchActiveCaseConditions,
  fetchAssumptionEvents,
  fetchCaseConditionEvents,
  fetchDecisionDraftEvents,
  fetchDecisionReasoningWorkspace,
  fetchOpenDecisionDrafts,
} from "./reasoningWorkspaceApi";

function mockFetchOnce(body: unknown, ok = true, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({ ok, status, json: () => Promise.resolve(body) });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("reasoningWorkspaceApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetchDecisionReasoningWorkspace reads /api/decisions/{id}/reasoning-workspace", async () => {
    const fetchMock = mockFetchOnce({ decision: { id: "d1" } });

    const result = await fetchDecisionReasoningWorkspace("d1");

    expect(fetchMock).toHaveBeenCalledWith("/api/decisions/d1/reasoning-workspace", expect.anything());
    expect(result.decision.id).toBe("d1");
  });

  it("fetches per-aggregate event histories from their own existing endpoints", async () => {
    const fetchMock = mockFetchOnce([]);
    await fetchDecisionDraftEvents("draft-1");
    expect(fetchMock).toHaveBeenCalledWith("/api/decision-drafts/draft-1/events", expect.anything());

    mockFetchOnce([]);
    await fetchAssumptionEvents("assumption-1");
    expect(fetchMock).not.toBe(undefined); // sanity: mock swapped without throwing

    mockFetchOnce([]);
    await fetchCaseConditionEvents("condition-1");
  });

  it("fetchActiveAssumptions/fetchActiveCaseConditions read the Case-scoped read-model endpoints", async () => {
    const fetchMock = mockFetchOnce([]);
    await fetchActiveAssumptions("case-1");
    expect(fetchMock).toHaveBeenCalledWith("/api/cases/case-1/reasoning/active-assumptions", expect.anything());

    mockFetchOnce([]);
    await fetchActiveCaseConditions("case-1");
  });

  it("fetchOpenDecisionDrafts reads the user-scoped read-model endpoint with an encoded userId", async () => {
    const fetchMock = mockFetchOnce([]);

    await fetchOpenDecisionDrafts("user with space");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/reasoning/open-decision-drafts?userId=user%20with%20space",
      expect.anything(),
    );
  });

  it("commitDraftWithReasoning POSTs the assembled assumptions/standalone conditions payload", async () => {
    const fetchMock = mockFetchOnce({ decision: { id: "d1" }, draft: {}, assumptions: [], caseConditions: [] });

    await commitDraftWithReasoning("draft-1", {
      assumptions: [{ statement: "GCP margin expansion", linkedConditions: [{ predicateText: "China revenue trend" }] }],
      standaloneCaseConditions: [{ predicateText: "Review in 90 days" }],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/decision-drafts/draft-1/commit-with-reasoning",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          assumptions: [{ statement: "GCP margin expansion", linkedConditions: [{ predicateText: "China revenue trend" }] }],
          standaloneCaseConditions: [{ predicateText: "Review in 90 days" }],
        }),
      }),
    );
  });

  it("commitDraftWithReasoning defaults to empty arrays when no reasoning content is supplied", async () => {
    const fetchMock = mockFetchOnce({ decision: { id: "d1" }, draft: {}, assumptions: [], caseConditions: [] });

    await commitDraftWithReasoning("draft-1");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/decision-drafts/draft-1/commit-with-reasoning",
      expect.objectContaining({
        body: JSON.stringify({ assumptions: [], standaloneCaseConditions: [] }),
      }),
    );
  });

  it("throws a clear error when the backend responds with a non-ok status", async () => {
    mockFetchOnce({ detail: "not found" }, false, 404);

    await expect(fetchDecisionReasoningWorkspace("unknown")).rejects.toThrow("404");
  });
});

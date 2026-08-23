import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { DecisionWorkspacePage } from "./DecisionWorkspacePage";
import * as api from "./reasoningWorkspaceApi";
import type { DecisionReasoningWorkspace } from "./reasoningWorkspaceApi";

vi.mock("./reasoningWorkspaceApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./reasoningWorkspaceApi")>();
  return { ...actual, ...Object.fromEntries(Object.keys(actual).filter((k) => k.startsWith("fetch") || k === "commitDraftWithReasoning").map((k) => [k, vi.fn()])) };
});

function baseWorkspace(overrides: Partial<DecisionReasoningWorkspace> = {}): DecisionReasoningWorkspace {
  return {
    decision: {
      id: "d1",
      caseId: "case-1",
      userId: "user-1",
      decisionType: "BUY",
      subject: "ASML",
      reason: "Durable moat, undervalued relative to peers",
      confidence: 75,
      decidedAt: "2026-06-01T00:00:00Z",
      recordedAt: "2026-06-01T00:00:00Z",
      source: "Manual",
      observationId: null,
    },
    decisionContext: null,
    originatingDraft: null,
    activeCaseDrafts: [],
    assumptions: [],
    caseConditions: [],
    ...overrides,
  };
}

describe("DecisionWorkspacePage", () => {
  beforeEach(() => {
    vi.mocked(api.fetchDecisionReasoningWorkspace).mockResolvedValue(baseWorkspace());
    vi.mocked(api.fetchDecisionDraftEvents).mockResolvedValue([]);
    vi.mocked(api.fetchAssumptionEvents).mockResolvedValue([]);
    vi.mocked(api.fetchCaseConditionEvents).mockResolvedValue([]);
    vi.mocked(api.fetchActiveAssumptions).mockResolvedValue([]);
    vi.mocked(api.fetchActiveCaseConditions).mockResolvedValue([]);
    vi.mocked(api.fetchOpenDecisionDrafts).mockResolvedValue([]);
  });

  it("shows a loading state before data arrives", () => {
    renderWithProviders(<DecisionWorkspacePage />, { route: "/decisions/d1/workspace", path: "/decisions/:decisionId/workspace" });
    expect(screen.getByText(/Läser in/)).toBeInTheDocument();
  });

  it("renders the Decision's own subject and reason once loaded", async () => {
    renderWithProviders(<DecisionWorkspacePage />, { route: "/decisions/d1/workspace", path: "/decisions/:decisionId/workspace" });

    await waitFor(() => expect(screen.getByText("ASML")).toBeInTheDocument());
    expect(screen.getByText("Durable moat, undervalued relative to peers")).toBeInTheDocument();
  });

  it("fetches the workspace for the decisionId in the route", async () => {
    renderWithProviders(<DecisionWorkspacePage />, { route: "/decisions/d1/workspace", path: "/decisions/:decisionId/workspace" });

    await waitFor(() => expect(api.fetchDecisionReasoningWorkspace).toHaveBeenCalledWith("d1", expect.anything()));
  });

  it("shows the no-context message when DecisionContext is absent", async () => {
    renderWithProviders(<DecisionWorkspacePage />, { route: "/decisions/d1/workspace", path: "/decisions/:decisionId/workspace" });
    await waitFor(() => expect(screen.getByText(/Ingen kontext/)).toBeInTheDocument());
  });

  it("renders DecisionContext when present", async () => {
    vi.mocked(api.fetchDecisionReasoningWorkspace).mockResolvedValue(
      baseWorkspace({
        decisionContext: {
          contextId: "ctx1",
          decisionId: "d1",
          situation: "Large semiconductor exposure already",
          portfolioRelevance: null,
          capitalConsiderations: null,
          alternativesConsidered: [],
          uncertainties: [],
          capturedAt: "2026-06-01T00:00:00Z",
          recordedAt: "2026-06-01T00:00:00Z",
        },
      }),
    );

    renderWithProviders(<DecisionWorkspacePage />, { route: "/decisions/d1/workspace", path: "/decisions/:decisionId/workspace" });

    await waitFor(() => expect(screen.getByText("Large semiconductor exposure already")).toBeInTheDocument());
  });

  it("shows a resume/commit link for each other active draft on the same Case", async () => {
    vi.mocked(api.fetchDecisionReasoningWorkspace).mockResolvedValue(
      baseWorkspace({
        activeCaseDrafts: [
          {
            draftId: "draft-2",
            caseId: "case-1",
            userId: "user-1",
            status: "active",
            decisionType: null,
            subject: "MSFT",
            reason: null,
            confidence: null,
            decidedAt: null,
            source: null,
            situation: null,
            portfolioRelevance: null,
            capitalConsiderations: null,
            alternativesConsidered: [],
            uncertainties: [],
            committedDecisionId: null,
            latestEventId: "e1",
            createdAt: "2026-06-01T00:00:00Z",
            updatedAt: "2026-06-01T00:00:00Z",
          },
        ],
      }),
    );

    renderWithProviders(<DecisionWorkspacePage />, { route: "/decisions/d1/workspace", path: "/decisions/:decisionId/workspace" });

    await waitFor(() => expect(screen.getByText("MSFT")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Bekräfta ditt beslut" })).toHaveAttribute(
      "href",
      "/decision-drafts/draft-2/commit",
    );
  });

  it("links back to the real Investment Case this Decision belongs to (Product Sprint 10, Deliverable 3)", async () => {
    renderWithProviders(<DecisionWorkspacePage />, { route: "/decisions/d1/workspace", path: "/decisions/:decisionId/workspace" });
    await waitFor(() => expect(screen.getByText("ASML")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "← Tillbaka till investeringscaset" })).toHaveAttribute(
      "href",
      "/investment-case/case-1",
    );
  });

  it("shows an error message when the workspace fails to load", async () => {
    vi.mocked(api.fetchDecisionReasoningWorkspace).mockRejectedValue(new Error("404"));

    renderWithProviders(<DecisionWorkspacePage />, { route: "/decisions/unknown/workspace", path: "/decisions/:decisionId/workspace" });

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("404"));
  });
});

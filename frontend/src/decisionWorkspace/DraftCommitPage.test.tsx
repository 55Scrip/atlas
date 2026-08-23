import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { DraftCommitPage } from "./DraftCommitPage";
import * as decisionDraftApi from "./decisionDraftApi";
import type { DecisionDraftView } from "./decisionDraftApi";

vi.mock("./decisionDraftApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./decisionDraftApi")>();
  return { ...actual, fetchDecisionDraft: vi.fn() };
});

function baseDraft(overrides: Partial<DecisionDraftView> = {}): DecisionDraftView {
  return {
    draftId: "draft-1",
    caseId: "case-1",
    userId: "user-1",
    status: "active",
    decisionType: "BUY",
    subject: "ASML",
    reason: "Durable moat, undervalued relative to peers",
    confidence: 75,
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
    ...overrides,
  };
}

describe("DraftCommitPage", () => {
  it("links back to the real Investment Case this Draft belongs to (Product Sprint 10, Deliverable 3)", async () => {
    vi.mocked(decisionDraftApi.fetchDecisionDraft).mockResolvedValue(baseDraft());
    renderWithProviders(<DraftCommitPage />, { route: "/decision-drafts/draft-1/commit", path: "/decision-drafts/:draftId/commit" });

    await waitFor(() => expect(screen.getByText("ASML")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "← Tillbaka till investeringscaset" })).toHaveAttribute(
      "href",
      "/investment-case/case-1",
    );
  });
});

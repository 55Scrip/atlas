import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { StartDecisionSection } from "./StartDecisionSection";

function mockFetch({
  activeDrafts = [] as unknown[],
  createResponse,
}: {
  activeDrafts?: unknown[];
  createResponse?: unknown;
} = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/decision-drafts") && init?.method === "POST") {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(createResponse) } as Response);
      }
      if (url.includes("/decision-drafts")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(activeDrafts) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("StartDecisionSection (Product Sprint 12 -- Decision Workflow Consolidation)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the Start trigger when no draft is already in progress -- previously no entry point existed at all (Deliverable 3)", async () => {
    mockFetch();
    renderWithProviders(<StartDecisionSection caseId="case-1" ticker="NVDA" />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Starta ett beslut" })).toBeInTheDocument());
  });

  it("shows only a Resume link, never both, when a draft is already active for this case (Deliverable 3 -- never duplicated)", async () => {
    mockFetch({ activeDrafts: [{ draftId: "draft-1", caseId: "case-1", subject: "NVDA", createdAt: "2026-01-01T00:00:00Z" }] });
    renderWithProviders(<StartDecisionSection caseId="case-1" ticker="NVDA" />);
    await waitFor(() =>
      expect(screen.getByRole("link", { name: "Återuppta: NVDA →" })).toHaveAttribute("href", "/decision-drafts/draft-1/commit"),
    );
    expect(screen.queryByRole("button", { name: "Starta ett beslut" })).not.toBeInTheDocument();
  });

  it("requires a manual ticker before continuing when the resolved ticker is unknown (live-discovered: the backend rejects a decision with no subject)", async () => {
    mockFetch();
    const user = userEvent.setup();
    renderWithProviders(<StartDecisionSection caseId="case-1" ticker={null} />);
    await user.click(await screen.findByRole("button", { name: "Starta ett beslut" }));

    await user.type(screen.getByLabelText("Motivering"), "Some real reason");
    expect(screen.getByRole("button", { name: "Fortsätt →" })).toBeDisabled();

    await user.type(screen.getByLabelText("Bolag eller ticker"), "NVDA");
    expect(screen.getByRole("button", { name: "Fortsätt →" })).not.toBeDisabled();
  });

  it("creates a draft with the real ticker as subject and navigates to its commit page on submit", async () => {
    mockFetch({ createResponse: { draftId: "draft-2", caseId: "case-1", subject: "NVDA" } });
    const user = userEvent.setup();
    renderWithProviders(<StartDecisionSection caseId="case-1" ticker="NVDA" />, {
      route: "/investment-case/case-1",
      path: "/investment-case/:caseId",
    });
    await user.click(await screen.findByRole("button", { name: "Starta ett beslut" }));
    await user.type(screen.getByLabelText("Motivering"), "Durable growth, reasonable valuation");
    await user.click(screen.getByRole("button", { name: "Fortsätt →" }));

    await waitFor(() => {
      const calls = vi.mocked(fetch).mock.calls;
      const createCall = calls.find(([, init]) => init && (init as RequestInit).method === "POST");
      expect(createCall).toBeDefined();
      const body = JSON.parse(String((createCall![1] as RequestInit).body));
      expect(body.subject).toBe("NVDA");
      expect(body.decisionType).toBe("BUY");
    });
  });
});

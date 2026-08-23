import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { HoldingAttentionPage } from "./HoldingAttentionPage";

const HOLDING = {
  ticker: "AAPL",
  caseId: "case-aapl",
  weightPercent: 33,
  valueAbsolute: null,
  conviction: { level: "moderate" },
  decisionSupport: { level: "thesis_intact" },
  attention: { reasons: [] },
};

function mockFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/alpha-portfolio/cockpit")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: true, holdings: [HOLDING] }) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("HoldingAttentionPage (Product Sprint 10 -- Navigation & Workflow Excellence)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("offers a Compare entry point -- previously a dead end (Deliverable 1/4)", async () => {
    mockFetch();
    renderWithProviders(<HoldingAttentionPage />, { route: "/portfolio/holding/AAPL", path: "/portfolio/holding/:ticker" });
    await waitFor(() => expect(screen.getByRole("heading", { name: "AAPL" })).toBeInTheDocument());
    const link = screen.getByRole("link", { name: /Jämför med en annan kandidat/ });
    expect(link).toHaveAttribute("href", "/discovery/compare?a=AAPL");
  });

  it("styles every link with the same accent color other Tier-1 pages use (Deliverable 9)", async () => {
    mockFetch();
    renderWithProviders(<HoldingAttentionPage />, { route: "/portfolio/holding/AAPL", path: "/portfolio/holding/:ticker" });
    await waitFor(() => expect(screen.getByRole("heading", { name: "AAPL" })).toBeInTheDocument());
    const companyLink = screen.getByRole("link", { name: /bolagsvyn/ });
    expect(companyLink).toHaveStyle({ color: "var(--global-color-accent)" });
  });
});

import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LanguageProvider } from "../i18n";
import { renderWithProviders } from "../testUtils";
import { HoldingAttentionPage } from "./HoldingAttentionPage";
import type { AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";

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

  describe("Localization fix (Portfolio live-verification follow-up)", () => {
    function agendaItem(overrides: Partial<AgendaItemView> = {}): AgendaItemView {
      return {
        id: "review_portfolio_position:AAPL",
        priority: "critical",
        kind: "review_portfolio_position",
        group: "portfolio",
        source: "portfolio_status",
        headline: "AAPL: outcome without execution (3 item(s))",
        reason: ["AAPL: outcome without execution (3 item(s))"],
        nature: "persistent_condition",
        reasonNature: ["persistent_condition"],
        since: null,
        ticker: "AAPL",
        caseId: "case-aapl",
        portfolioContext: null,
        generatedAt: "2026-01-01T00:00:00Z",
        attentionCategory: null,
        attentionCount: null,
        reasonFacts: [null],
        ...overrides,
      };
    }

    it("shows the translated why-attention text for a real workflow item, never the raw backend headline", async () => {
      mockFetch();
      render(
        <MemoryRouter
          initialEntries={[
            {
              pathname: "/portfolio/holding/AAPL",
              state: {
                agendaItem: agendaItem({
                  reasonFacts: [
                    {
                      code: "workflow_gap",
                      entity: "AAPL",
                      value: "OUTCOME_WITHOUT_EXECUTION",
                      secondaryValue: null,
                      label: null,
                      count: 3,
                    },
                  ],
                }),
              },
            },
          ]}
        >
          <LanguageProvider>
            <Routes>
              <Route path="/portfolio/holding/:ticker" element={<HoldingAttentionPage />} />
            </Routes>
          </LanguageProvider>
        </MemoryRouter>,
      );
      await waitFor(() => expect(screen.getByRole("heading", { name: "AAPL" })).toBeInTheDocument());
      expect(screen.getByText(/affären ej bekräftad än \(3 st\)/)).toBeInTheDocument();
      expect(screen.queryByText(/outcome without execution/)).not.toBeInTheDocument();
    });
  });
});

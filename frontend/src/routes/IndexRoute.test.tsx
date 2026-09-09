import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LanguageProvider } from "../i18n";
import { IndexRoute } from "./IndexRoute";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

function renderIndex() {
  render(
    <MemoryRouter initialEntries={["/"]}>
      <LanguageProvider>
        <Routes>
          <Route path="/" element={<IndexRoute />} />
          <Route path="/daily-brief" element={<div>DAILY BRIEF SURFACE</div>} />
          <Route path="/portfolio" element={<div>PORTFOLIO SURFACE</div>} />
          <Route path="/welcome" element={<div>WELCOME SURFACE</div>} />
        </Routes>
      </LanguageProvider>
    </MemoryRouter>,
  );
}

/**
 * Final Pre-Alpha Convergence. Opening Atlas asks "what deserves my
 * attention today," which is Daily Brief's question. It used to land on
 * Portfolio -- the current-state control room, a different question the
 * investor gets to one click later.
 */
describe("start experience", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
  });

  it("opens Daily Brief once a portfolio is established", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: true, holdings: [] }) } as Response)));
    renderIndex();
    await waitFor(() => expect(screen.getByText("DAILY BRIEF SURFACE")).toBeInTheDocument());
    expect(screen.queryByText("PORTFOLIO SURFACE")).not.toBeInTheDocument();
  });

  /** First run is unchanged: with no portfolio there is nothing to
   * brief on, so onboarding still comes first. */
  it("still sends a first-run investor to onboarding, never to an empty brief", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: false, holdings: [] }) } as Response)));
    renderIndex();
    await waitFor(() => expect(screen.getByText("WELCOME SURFACE")).toBeInTheDocument());
  });

  it("says it is working rather than flashing a wrong surface while it resolves", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    renderIndex();
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.queryByText("DAILY BRIEF SURFACE")).not.toBeInTheDocument();
    expect(screen.queryByText("WELCOME SURFACE")).not.toBeInTheDocument();
  });
});

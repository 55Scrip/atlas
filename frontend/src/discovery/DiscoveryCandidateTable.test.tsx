import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LanguageProvider } from "../i18n";
import { DiscoveryCandidateTable } from "./DiscoveryCandidateTable";
import type { DiscoveryCandidateView } from "./discoveryCandidatesApi";

function candidate(overrides: Partial<DiscoveryCandidateView> = {}): DiscoveryCandidateView {
  return {
    ticker: "ASML",
    caseId: "case-asml",
    companyName: "ASML Holding NV ADR",
    decisionSupportLevel: "entry_supported",
    analysisCoverageLevel: "substantial_coverage",
    fitRating: "good",
    stanceLevel: "review",
    ...overrides,
  };
}

function renderTable(candidates: DiscoveryCandidateView[], onOpenCase = vi.fn()) {
  render(
    <LanguageProvider>
      <DiscoveryCandidateTable candidates={candidates} captionKey="discovery.worthReviewing.heading" onOpenCase={onOpenCase} />
    </LanguageProvider>,
  );
  return onOpenCase;
}

describe("DiscoveryCandidateTable (Convergence Sprint 4C -- dense candidate IA)", () => {
  it("renders one comparable column per canonical signal the candidate already carries", () => {
    renderTable([candidate()]);
    const headers = screen.getAllByRole("columnheader").map((cell) => cell.textContent);
    expect(headers).toEqual(["Bolag", "Beslutsstöd", "Nuvarande syn", "Analysdjup", "Passform"]);
  });

  it("renders every categorical value through the one shared vocabulary, never a Discovery-only wording", () => {
    renderTable([candidate()]);
    const row = screen.getByRole("button", { name: "Öppna investeringscaset för ASML" });
    expect(within(row).getByText("Nyinvestering stöds")).toBeInTheDocument();
    expect(within(row).getByText("Värt att se över")).toBeInTheDocument();
    expect(within(row).getByText("Utvärderat")).toBeInTheDocument();
    expect(within(row).getByText("Bra passform")).toBeInTheDocument();
    expect(within(row).getByText("ASML Holding NV ADR")).toBeInTheDocument();
  });

  /** A `null` Stance or Fit is a real answer -- "the engine could not
   * evaluate this company" -- never rendered as a middling value and
   * never left as an empty cell the reader has to interpret. */
  it("names an unevaluated signal instead of leaving the cell blank or inventing a neutral value", () => {
    renderTable([candidate({ ticker: "XOM", caseId: "case-xom", fitRating: null, stanceLevel: null })]);
    const row = screen.getByRole("button", { name: "Öppna investeringscaset för XOM" });
    expect(within(row).getAllByText("Ej bedömt")).toHaveLength(2);
    expect(within(row).queryByText("Neutral passform")).not.toBeInTheDocument();
  });

  it("preserves the order it was given, adding no ranking of its own", () => {
    renderTable([
      candidate({ ticker: "TSM", caseId: "case-tsm" }),
      candidate({ ticker: "AAPL", caseId: "case-aapl" }),
      candidate({ ticker: "CRM", caseId: "case-crm" }),
    ]);
    const order = screen.getAllByRole("button").map((row) => row.getAttribute("aria-label"));
    expect(order).toEqual([
      "Öppna investeringscaset för TSM",
      "Öppna investeringscaset för AAPL",
      "Öppna investeringscaset för CRM",
    ]);
  });

  it("opens the Investment Case when the row is clicked", async () => {
    const onOpenCase = renderTable([candidate()]);
    await userEvent.click(screen.getByRole("button", { name: "Öppna investeringscaset för ASML" }));
    expect(onOpenCase).toHaveBeenCalledWith("ASML");
  });

  /** The row is the action, so it has to answer the keyboard the way a
   * button does -- the same contract the Watchlist row already meets. */
  it("opens the Investment Case from the keyboard, with Enter and with Space", async () => {
    const onOpenCase = renderTable([candidate()]);
    const row = screen.getByRole("button", { name: "Öppna investeringscaset för ASML" });
    expect(row).toHaveAttribute("tabindex", "0");
    row.focus();
    await userEvent.keyboard("{Enter}");
    await userEvent.keyboard(" ");
    expect(onOpenCase).toHaveBeenCalledTimes(2);
    expect(onOpenCase).toHaveBeenCalledWith("ASML");
  });

  it("never renders a numeric score, an expected return or a conviction claim", () => {
    renderTable([candidate(), candidate({ ticker: "CRWD", caseId: "case-crwd" })]);
    const text = document.body.textContent ?? "";
    for (const invented of ["Övertygelse", "Förväntad avkastning", "Uppsida", "Nedsida", "Poäng"]) {
      expect(text).not.toContain(invented);
    }
    expect(text).not.toMatch(/\d+\s*\/\s*10/);
    expect(text).not.toMatch(/\d+\s*%/);
  });
});

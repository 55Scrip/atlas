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
      <DiscoveryCandidateTable candidates={candidates} captionKey="discovery.notConcluded.heading" onOpenCase={onOpenCase} />
    </LanguageProvider>,
  );
  return onOpenCase;
}

describe("DiscoveryCandidateTable (dense candidate IA, Sprints 4C/4D)", () => {
  /** Sprint 4D dropped the Stance column: `review` for 20 of 22 live
   * candidates, and the one signal here that folds Portfolio Fit into
   * itself, so beside the Fit column it stated the same
   * portfolio-relative fact twice. */
  it("renders one comparable column per canonical signal, and no column that repeats another", () => {
    renderTable([candidate()]);
    const headers = screen.getAllByRole("columnheader").map((cell) => cell.textContent);
    expect(headers).toEqual(["Bolag", "Beslutsstöd", "Analysdjup", "Passform"]);
  });

  it("renders every categorical value through the one shared vocabulary, never a Discovery-only wording", () => {
    renderTable([candidate()]);
    const row = screen.getByRole("row", { name: /ASML/ });
    expect(within(row).getByText("Nyinvestering stöds")).toBeInTheDocument();
    expect(within(row).getByText("Utvärderat")).toBeInTheDocument();
    expect(within(row).getByText("Bra passform")).toBeInTheDocument();
    expect(within(row).getByText("ASML Holding NV ADR")).toBeInTheDocument();
  });

  /** A `null` Stance or Fit is a real answer -- "the engine could not
   * evaluate this company" -- never rendered as a middling value and
   * never left as an empty cell the reader has to interpret. */
  it("names an unevaluated signal instead of leaving the cell blank or inventing a neutral value", () => {
    renderTable([candidate({ ticker: "XOM", caseId: "case-xom", fitRating: null, stanceLevel: null })]);
    const row = screen.getByRole("row", { name: /XOM/ });
    expect(within(row).getAllByText("Ej bedömt")).toHaveLength(1);
    expect(within(row).queryByText("Neutral passform")).not.toBeInTheDocument();
  });

  it("preserves the order it was given, adding no ranking of its own", () => {
    renderTable([
      candidate({ ticker: "TSM", caseId: "case-tsm" }),
      candidate({ ticker: "AAPL", caseId: "case-aapl" }),
      candidate({ ticker: "CRM", caseId: "case-crm" }),
    ]);
    const order = screen.getAllByRole("button").map((button) => button.getAttribute("aria-label"));
    expect(order).toEqual([
      "Öppna investeringscaset för TSM",
      "Öppna investeringscaset för AAPL",
      "Öppna investeringscaset för CRM",
    ]);
  });

  it("opens the Investment Case when the row is clicked", async () => {
    const onOpenCase = renderTable([candidate()]);
    await userEvent.click(screen.getByRole("row", { name: /ASML/ }));
    expect(onOpenCase).toHaveBeenCalledWith("ASML");
  });

  /** Sprint 4D: keep native table-row semantics and let a native button
   * own focus/keyboard activation instead of overriding `<tr>`'s role. */
  it("preserves table semantics and opens from a native keyboard control", async () => {
    const onOpenCase = renderTable([candidate()]);
    const row = screen.getByRole("row", { name: /ASML/ });
    expect(row).not.toHaveAttribute("role");
    expect(row).not.toHaveAttribute("tabindex");
    const button = within(row).getByRole("button", { name: "Öppna investeringscaset för ASML" });
    button.focus();
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

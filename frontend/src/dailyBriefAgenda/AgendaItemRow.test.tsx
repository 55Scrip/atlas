import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LanguageProvider } from "../i18n";
import { AgendaItemRow } from "./AgendaItemRow";
import type { AgendaItemView } from "./dailyBriefAgendaApi";

function item(overrides: Partial<AgendaItemView> = {}): AgendaItemView {
  return {
    id: "evaluate_case_condition:AAPL",
    priority: "critical",
    kind: "evaluate_case_condition",
    group: "portfolio",
    source: "case_condition",
    headline: "AAPL: China revenue declines (satisfied)",
    reason: ["AAPL: China revenue declines (satisfied)"],
    nature: "persistent_condition",
    reasonNature: ["persistent_condition"],
    since: null,
    ticker: "AAPL",
    caseId: "case-aapl",
    portfolioContext: null,
    generatedAt: "2026-01-01T00:00:00Z",
    attentionCategory: null,
    attentionCount: null,
    ...overrides,
  };
}

function renderRow(overrides: Partial<AgendaItemView> = {}, handlers: Partial<Parameters<typeof AgendaItemRow>[0]> = {}) {
  return render(
    <LanguageProvider>
      <AgendaItemRow
        item={item(overrides)}
        onOpenInvestmentCase={vi.fn()}
        onOpenCandidate={vi.fn()}
        onCompare={vi.fn()}
        onOpenHolding={vi.fn()}
        onGoToPortfolio={vi.fn()}
        {...handlers}
      />
    </LanguageProvider>,
  );
}

describe("AgendaItemRow", () => {
  it("renders the priority badge, group tag, ticker, and headline", () => {
    renderRow();
    expect(screen.getByText("Kritisk")).toBeInTheDocument();
    expect(screen.getByText("Portfölj")).toBeInTheDocument();
    expect(screen.getByText("China revenue declines (satisfied)", { exact: false })).toBeInTheDocument();
  });

  it("shows portfolioContext when present", () => {
    renderRow({ portfolioContext: "33% of portfolio" });
    expect(screen.getByText("33% of portfolio")).toBeInTheDocument();
  });

  it("offers Open Investment Case for an evaluate_case_condition item and calls the handler with the real caseId", async () => {
    const onOpen = vi.fn();
    const user = userEvent.setup();
    renderRow({}, { onOpenInvestmentCase: onOpen });
    await user.click(screen.getByRole("link", { name: /Öppna investeringscase/ }));
    expect(onOpen).toHaveBeenCalledWith("case-aapl", "AAPL");
  });

  it("offers Review Candidate, Compare, and Open Investment Case for a watchlist candidate item", () => {
    renderRow({ kind: "review_watchlist_candidate", group: "watchlist" });
    expect(screen.getByRole("link", { name: /Granska kandidat/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Jämför/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Öppna investeringscase/ })).toBeInTheDocument();
  });

  it("offers Go to Portfolio for a portfolio-level risk item with no ticker", () => {
    renderRow({ kind: "portfolio_risk", ticker: null, caseId: null });
    expect(screen.getByRole("link", { name: /Gå till portföljen/ })).toBeInTheDocument();
  });

  it("calls onCompare with the real ticker when Compare is clicked", async () => {
    const onCompare = vi.fn();
    const user = userEvent.setup();
    renderRow({ kind: "review_watchlist_candidate", group: "watchlist" }, { onCompare });
    await user.click(screen.getByRole("link", { name: /Jämför/ }));
    expect(onCompare).toHaveBeenCalledWith("AAPL");
  });

  it("offers Review Position for a review_portfolio_position item", () => {
    renderRow({ kind: "review_portfolio_position" });
    expect(screen.getByRole("link", { name: /Granska position/ })).toBeInTheDocument();
  });

  it("never renders a numeric score anywhere in the row", () => {
    renderRow();
    expect(screen.queryByText(/^\d+\/\d+$|^\d+%$/)).not.toBeInTheDocument();
  });

  describe("Localization fix (Portfolio live-verification follow-up)", () => {
    it("composes a translated headline instead of the raw backend headline when attentionCategory is present", () => {
      renderRow({
        kind: "review_portfolio_position",
        source: "portfolio_status",
        headline: "AAPL: outcome without execution (3 item(s))",
        reason: ["AAPL: outcome without execution (3 item(s))"],
        attentionCategory: "OUTCOME_WITHOUT_EXECUTION",
        attentionCount: 3,
      });
      expect(screen.getByText("utfall utan verkställande (3 st)", { exact: false })).toBeInTheDocument();
      expect(screen.queryByText(/outcome without execution/)).not.toBeInTheDocument();
    });

    it("falls back to the raw backend headline when attentionCategory is absent (every non-workflow source)", () => {
      renderRow({ headline: "AAPL: China revenue declines (satisfied)", attentionCategory: null, attentionCount: null });
      expect(screen.getByText("China revenue declines (satisfied)", { exact: false })).toBeInTheDocument();
    });
  });

  describe("Signal nature (Fix Sprint 4 -- Daily Brief Signal Quality)", () => {
    it("shows an 'Ongoing since ...' sentence for a persistent condition with a real since date", () => {
      renderRow({ nature: "persistent_condition", since: "2026-08-20T22:47:12.238114Z" });
      expect(screen.getByText(/Pågående sedan/)).toBeInTheDocument();
    });

    it("discloses the honest absence of a since date rather than fabricating one", () => {
      renderRow({ nature: "persistent_condition", since: null });
      expect(screen.getByText(/ingen uppgift om exakt när/)).toBeInTheDocument();
    });

    it("never shows the since sentence for a change event", () => {
      renderRow({ nature: "change_event", since: null });
      expect(screen.queryByText(/Pågående sedan/)).not.toBeInTheDocument();
      expect(screen.queryByText(/ingen uppgift om exakt när/)).not.toBeInTheDocument();
    });

    it("labels each folded-in reason with its own real nature, not the winning item's nature", () => {
      renderRow({
        headline: "AAPL: China revenue declines (satisfied)",
        reason: ["AAPL: China revenue declines (satisfied)", "AAPL: high concentration", "AAPL: thesis weakened"],
        reasonNature: ["persistent_condition", "persistent_condition", "change_event"],
      });
      expect(screen.getByText("Pågående:", { exact: false })).toBeInTheDocument();
      expect(screen.getByText("Nytt:", { exact: false })).toBeInTheDocument();
    });
  });

  describe("Stance (Atlas Intelligence Sprint 2, Deliverable 8)", () => {
    const stance = {
      level: "reduce" as const,
      reasoning: [{ code: "thesis_weakened" as const }],
      supportingSignals: [],
      limitingSignals: [{ code: "thesis_weakened" as const }],
      confidence: "high" as const,
      missingInformation: [],
    };

    it("shows the current Stance when the item's source is change_intelligence", () => {
      renderRow({ source: "change_intelligence" }, { stance });
      expect(screen.getByText("Atlas nuvarande syn:")).toBeInTheDocument();
      expect(screen.getByText("Synen har försvagats")).toBeInTheDocument();
    });

    it("never shows the current Stance when the item's source is something else, even with a real Stance in hand", () => {
      renderRow({ source: "portfolio_fit" }, { stance });
      expect(screen.queryByText("Atlas nuvarande syn:")).not.toBeInTheDocument();
    });

    it("shows nothing when no Stance is provided at all, never a placeholder", () => {
      renderRow({ source: "change_intelligence" }, { stance: null });
      expect(screen.queryByText("Atlas nuvarande syn:")).not.toBeInTheDocument();
    });
  });
});

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { MonitoringChangeFeed } from "./MonitoringChangeFeed";
import type { MonitoringChangeView, MonitoringResultView } from "./monitoringApi";

function change(overrides: Partial<MonitoringChangeView> = {}): MonitoringChangeView {
  return {
    id: "change-1",
    category: "stance_weakened",
    materiality: "material",
    direction: "negative",
    reason: "Atlas's view on AAPL weakened.",
    sourceCapability: "evidence_timeline",
    evidenceReference: "evidence-1",
    ...overrides,
  };
}

function result(overrides: Partial<MonitoringResultView> = {}): MonitoringResultView {
  return {
    caseId: "case-aapl",
    ticker: "AAPL",
    scope: "portfolio",
    status: "changed_high_importance",
    changes: [change()],
    stanceLevel: null,
    confidenceLevel: null,
    coverageLevel: null,
    latestMeaningfulEvidenceAt: null,
    recommendedAction: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function Wrapper({ results, onOpenInvestmentCase }: { results: MonitoringResultView[]; onOpenInvestmentCase: (caseId: string, ticker: string | null) => void }) {
  const { t } = useTranslation();
  return <MonitoringChangeFeed results={results} t={t} onOpenInvestmentCase={onOpenInvestmentCase} />;
}

function renderFeed(results: MonitoringResultView[], onOpenInvestmentCase = vi.fn()) {
  return render(
    <LanguageProvider>
      <Wrapper results={results} onOpenInvestmentCase={onOpenInvestmentCase} />
    </LanguageProvider>,
  );
}

describe("MonitoringChangeFeed (Product Intelligence Sprint 3 -- Monitoring Intelligence Activation)", () => {
  it("shows the honest empty state when no company has any change", () => {
    renderFeed([result({ changes: [], status: "up_to_date" })]);
    expect(screen.getByText("Atlas har inte hittat några förändringar att rapportera för dina bolag.")).toBeInTheDocument();
  });

  it("renders a real change's own reason text and status badge", () => {
    renderFeed([result()]);
    expect(screen.getByText("Atlas's view on AAPL weakened.")).toBeInTheDocument();
    expect(screen.getByText("AAPL")).toBeInTheDocument();
  });

  it("orders companies by the backend's own status severity, highest importance first", () => {
    const low = result({
      caseId: "case-msft",
      ticker: "MSFT",
      status: "changed_review_suggested",
      changes: [change({ id: "c-msft", reason: "MSFT review change." })],
    });
    const high = result({
      caseId: "case-nvda",
      ticker: "NVDA",
      status: "changed_high_importance",
      changes: [change({ id: "c-nvda", reason: "NVDA high-importance change." })],
    });
    renderFeed([low, high]);
    const tickers = screen.getAllByText(/^(MSFT|NVDA)$/).map((el) => el.textContent);
    expect(tickers).toEqual(["NVDA", "MSFT"]);
  });

  it("never surfaces a company with zero changes as if something changed", () => {
    renderFeed([result({ caseId: "case-msft", ticker: "MSFT", changes: [], status: "up_to_date" }), result()]);
    expect(screen.queryByText("MSFT")).not.toBeInTheDocument();
    expect(screen.getByText("AAPL")).toBeInTheDocument();
  });

  it("distinguishes a minor change from a material one, never hiding either", () => {
    renderFeed([
      result({
        changes: [
          change({ id: "c-material", materiality: "material", reason: "Material change." }),
          change({ id: "c-minor", materiality: "minor", reason: "Minor change." }),
        ],
      }),
    ]);
    expect(screen.getByText("Material change.")).toBeInTheDocument();
    expect(screen.getByText("Minor change.")).toBeInTheDocument();
    expect(screen.getByText(/^Väsentlig ·/)).toBeInTheDocument();
    expect(screen.getByText(/^Mindre ·/)).toBeInTheDocument();
  });

  it("discloses companies Monitoring has not evaluated yet, separately from 'nothing changed'", () => {
    renderFeed([result({ changes: [] as MonitoringChangeView[], status: "unavailable" }), result({ caseId: "case-nvda", ticker: "NVDA" })]);
    expect(screen.getByText("1 bolag har ännu inte utvärderats av Övervakning.")).toBeInTheDocument();
  });

  it("navigates to the real Investment Case when opened, never a dead end", () => {
    const onOpen = vi.fn();
    renderFeed([result()], onOpen);
    screen.getByText(/Öppna investeringscase/).click();
    expect(onOpen).toHaveBeenCalledWith("case-aapl", "AAPL");
  });
});

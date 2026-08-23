import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { TickerEvidenceQualityDetail } from "./TickerEvidenceQualityDetail";
import type { EvidenceQualityReportView } from "./evidenceQualityApi";

const REPORT: EvidenceQualityReportView = {
  quality: "conflicting",
  conflictStatus: "conflicting",
  freshness: "fresh",
  dominance: "single_source",
  warnings: ["conflicting_source_values"],
  facts: [],
  conflicts: [],
  unsupportedFindings: [],
};

function Harness({ ticker }: { ticker: string }) {
  const { t } = useTranslation();
  return <TickerEvidenceQualityDetail ticker={ticker} summaryLabel="Hur tillförlitligt är underlaget?" t={t} />;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("TickerEvidenceQualityDetail (Atlas Intelligence Sprint 4)", () => {
  it("does not fetch until the detail is actually opened", () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    render(
      <LanguageProvider>
        <Harness ticker="NVDA" />
      </LanguageProvider>,
    );
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("fetches and shows the real quality badge plus warning sentence once opened, never a raw code", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => REPORT } as Response));

    render(
      <LanguageProvider>
        <Harness ticker="NVDA" />
      </LanguageProvider>,
    );

    fireEvent.click(screen.getByText("Hur tillförlitligt är underlaget?"));

    await waitFor(() => expect(screen.getByText("Motstridigt")).toBeInTheDocument());
    expect(screen.getByText("Atlas hittade källor som motsäger varandra.")).toBeInTheDocument();
    expect(screen.queryByText("conflicting_source_values")).not.toBeInTheDocument();
  });

  it("shows the honest unavailable state when no Case exists for this ticker", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 404, json: async () => null } as Response));

    render(
      <LanguageProvider>
        <Harness ticker="ZZZZZ" />
      </LanguageProvider>,
    );

    fireEvent.click(screen.getByText("Hur tillförlitligt är underlaget?"));

    await waitFor(() => expect(screen.getByText("Atlas har inget bolagsunderlag att bedöma ännu.")).toBeInTheDocument());
  });
});

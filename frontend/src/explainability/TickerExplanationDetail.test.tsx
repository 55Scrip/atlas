import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { TickerExplanationDetail } from "./TickerExplanationDetail";
import type { MaterialityAssessmentView } from "../materiality/materialityApi";

const ASSESSMENT: MaterialityAssessmentView = {
  supportingEvidence: [],
  contradictingEvidence: [{ reason: { code: "high_risk_present" }, materiality: "critical" }],
  limitingFactors: [{ reason: { code: "confidence_limited" }, materiality: "medium" }],
  topSupportingEvidence: null,
  topContradictingEvidence: { reason: { code: "high_risk_present" }, materiality: "critical" },
  topLimitingFactor: { reason: { code: "confidence_limited" }, materiality: "medium" },
  topMissingEvidence: { dimension: "growth", level: "unavailable", reasoning: ["insufficient_historical_periods"] },
};

function Harness({ ticker }: { ticker: string }) {
  const { t } = useTranslation();
  return <TickerExplanationDetail ticker={ticker} summaryLabel="Varför?" t={t} />;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("TickerExplanationDetail (Materiality-powered, Atlas Intelligence)", () => {
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

  it("fetches and shows the top missing evidence, top limiting factor, and top contradicting evidence, never a raw enum token", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ASSESSMENT } as Response));

    render(
      <LanguageProvider>
        <Harness ticker="NVDA" />
      </LanguageProvider>,
    );

    fireEvent.click(screen.getByText("Varför?"));

    await waitFor(() => expect(screen.getByText(/Tillväxt/)).toBeInTheDocument());
    expect(screen.queryByText(/insufficient_historical_periods/)).not.toBeInTheDocument();
    expect(screen.getByText("Atlas egen tillförlitlighet i den här analysen är begränsad.")).toBeInTheDocument();
    expect(screen.getByText("En allvarlig risk föreligger för närvarande.")).toBeInTheDocument();
  });

  it("shows the honest unavailable state when no Case exists for this ticker", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 404, json: async () => null } as Response));

    render(
      <LanguageProvider>
        <Harness ticker="ZZZZZ" />
      </LanguageProvider>,
    );

    fireEvent.click(screen.getByText("Varför?"));

    await waitFor(() =>
      expect(
        screen.getByText("Atlas saknar inget underlag som väsentligt skulle förändra den här slutsatsen."),
      ).toBeInTheDocument(),
    );
  });
});

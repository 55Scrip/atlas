import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider } from "../i18n";
import { CaseDnaLine, SevenCategoriesSection, type SevenCategoriesInput } from "./SevenCategoriesSection";

const t = (key: string, params?: Record<string, string | number>) =>
  params ? `${key}(${JSON.stringify(params)})` : key;

function ratings(overrides: Partial<SevenCategoriesInput> = {}): SevenCategoriesInput {
  return {
    company: { score: 8, tier: "good" },
    investment: { score: 6, tier: "fair" },
    portfolio: { score: 9.5, tier: "excellent" },
    evidence: { score: 4, tier: "weak" },
    upside: { level: "high" },
    risk: { level: "moderate" },
    horizon: { bucket: "three_to_five_years", monthsLow: 36, monthsHigh: 60 },
    ...overrides,
  };
}

function renderBar(props: Partial<SevenCategoriesInput> = {}) {
  return render(
    <LanguageProvider>
      <SevenCategoriesSection ratings={ratings(props)} t={t as never} />
    </LanguageProvider>,
  );
}

describe("SevenCategoriesSection -- Atlas UX Phase 7A (Semantic Investment Model)", () => {
  it("shows the real score, to one decimal, for a rated pillar", () => {
    renderBar();
    expect(screen.getByText("8.0")).toBeInTheDocument();
    expect(screen.getByText("9.5")).toBeInTheDocument();
  });

  it("never renders a number for a missing rating -- 'Not rated yet' instead of a fabricated score", () => {
    renderBar({ evidence: { score: null, tier: "missing" } });
    expect(screen.getByText("investmentCase.ratings.missing")).toBeInTheDocument();
    // The other three rated pillars are unaffected by one being missing.
    expect(screen.getByText("8.0")).toBeInTheDocument();
  });

  it("renders 'Not applicable' distinctly from 'missing' for Portfolio Rating on a non-holding", () => {
    renderBar({ portfolio: { score: null, tier: "not_applicable" } });
    expect(screen.getByText("investmentCase.ratings.notApplicable")).toBeInTheDocument();
  });

  it("Upside and Risk render as independent qualitative levels, never a number", () => {
    renderBar({ upside: { level: "very_high" }, risk: { level: "very_high" } });
    const veryHighLabels = screen.getAllByText("investmentCase.ratings.qualitative.veryHigh");
    // A case can carry Very High Upside and Very High Risk at once -- both tiles render independently.
    expect(veryHighLabels).toHaveLength(2);
    expect(screen.queryByText(/^\d+\.\d\/10$/)).not.toBeInTheDocument();
  });

  it("shows 'Not rated yet' for a missing qualitative level, never a guessed one", () => {
    renderBar({ upside: { level: "missing" } });
    expect(screen.getAllByText("investmentCase.ratings.missing").length).toBeGreaterThan(0);
  });

  it("shows the real month range alongside the Horizon bucket label", () => {
    renderBar();
    expect(screen.getByText("investmentCase.ratings.horizon.threeToFiveYears")).toBeInTheDocument();
    expect(screen.getByText('investmentCase.ratings.horizon.monthRange({"low":36,"high":60})')).toBeInTheDocument();
  });

  it("shows no month range when Horizon itself is missing", () => {
    renderBar({ horizon: { bucket: "missing", monthsLow: null, monthsHigh: null } });
    expect(screen.queryByText(/investmentCase\.ratings\.horizon\.monthRange/)).not.toBeInTheDocument();
  });
});

describe("CaseDnaLine", () => {
  it("renders exactly the one sentence it's given, under the Case DNA label", () => {
    render(
      <LanguageProvider>
        <CaseDnaLine sentence="This case depends primarily on continued AI infrastructure demand." t={t as never} />
      </LanguageProvider>,
    );
    expect(screen.getByText("investmentCase.caseDna.label")).toBeInTheDocument();
    expect(screen.getByText("This case depends primarily on continued AI infrastructure demand.")).toBeInTheDocument();
  });
});

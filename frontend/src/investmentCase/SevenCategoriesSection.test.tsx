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
    risk: { level: "moderate" },
    horizon: { years: 4 },
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

  it("Risk renders as a qualitative level, never a number", () => {
    renderBar({ risk: { level: "very_high" } });
    expect(screen.getAllByText("investmentCase.ratings.qualitative.veryHigh")).toHaveLength(1);
    expect(screen.queryByText(/^\d+\.\d\/10$/)).not.toBeInTheDocument();
  });

  it("has no Upside tile: a sensitivity endpoint is never scored as upside", () => {
    const { container } = renderBar();
    expect(container.textContent ?? "").not.toMatch(/upside/i);
    const hidden = [...container.querySelectorAll("[aria-label],[title]")].map(
      (el) => `${el.getAttribute("aria-label") ?? ""} ${el.getAttribute("title") ?? ""}`,
    );
    for (const label of hidden) expect(label).not.toMatch(/upside|uppsida|expected|förväntad|forecast|prognos/i);
    // Six tiles: Company, Investment, Portfolio, Coverage, Risk, Horizon.
    expect(screen.getAllByText(/^investmentCase\.ratings\.[a-z]+\.label$/)).toHaveLength(6);
  });

  it("shows 'Not rated yet' for a missing qualitative level, never a guessed one", () => {
    renderBar({ risk: { level: "missing" } });
    expect(screen.getAllByText("investmentCase.ratings.missing").length).toBeGreaterThan(0);
  });

  it("shows the sensitivity's exact horizon in years, named as a sensitivity", () => {
    renderBar();
    expect(screen.getByText('investmentCase.ratings.horizon.years({"years":4})')).toBeInTheDocument();
    expect(screen.getByText("investmentCase.ratings.horizon.sensitivityCaption")).toBeInTheDocument();
  });

  it("shows 'Not rated yet' and no years when Horizon itself is missing", () => {
    renderBar({ horizon: { years: null } });
    expect(screen.queryByText(/investmentCase\.ratings\.horizon\.years/)).not.toBeInTheDocument();
    expect(screen.getAllByText("investmentCase.ratings.missing").length).toBeGreaterThan(0);
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

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider } from "../i18n";
import {
  AtlasOutlookSection,
  formatPercent,
  type HorizonOutlookView,
  type OutlookAssumptionView,
  type OutlookScenarioView,
  type OutlookView,
} from "./AtlasOutlookSection";

const t = (key: string, params?: Record<string, string | number>) =>
  params ? `${key}(${JSON.stringify(params)})` : key;

const yieldAssumption = (target: number): OutlookAssumptionView => ({
  kind: "historical_fcf_yield_reversion",
  currentFcfYield: 0.04,
  targetFcfYield: target,
  observationCount: 9,
  growthRate: null,
  horizonYears: null,
  growthObservationCount: null,
});

const growthAssumption = (growth: number): OutlookAssumptionView => ({
  kind: "historical_growth_with_terminal_reversion",
  currentFcfYield: 0.04,
  targetFcfYield: 0.05,
  observationCount: 9,
  growthRate: growth,
  horizonYears: 4,
  growthObservationCount: 5,
});

function scenario(overrides: Partial<OutlookScenarioView>): OutlookScenarioView {
  return {
    kind: "base",
    returnPercent: 0.1,
    assumption: yieldAssumption(0.036),
    driver: "valuation_rerating",
    withheldReason: null,
    anchorPeriods: ["2019-12-31"],
    ...overrides,
  };
}

const shortTerm: HorizonOutlookView = {
  horizon: "short_term",
  expectedReturn: {
    lowPercent: -0.2,
    highPercent: 0.1,
    basis: "cumulative",
    horizonMonthsLow: null,
    horizonMonthsHigh: null,
    assumption: yieldAssumption(0.036),
  },
  expectedReturnGap: null,
  scenarios: [
    scenario({
      kind: "bull",
      returnPercent: null,
      withheldReason: "near_zero_fcf_anchor",
      assumption: yieldAssumption(0.0008),
      anchorPeriods: ["2016-12-31"],
    }),
    scenario({ kind: "base" }),
    scenario({ kind: "bear", returnPercent: -0.2, assumption: yieldAssumption(0.05), anchorPeriods: ["2022-12-31"] }),
  ],
  scenariosGap: null,
  conviction: "moderate",
  momentum: "stable",
  keyDrivers: [],
};

const longTerm: HorizonOutlookView = {
  horizon: "long_term",
  expectedReturn: {
    lowPercent: 0.061,
    highPercent: 0.184,
    basis: "annualized",
    horizonMonthsLow: 48,
    horizonMonthsHigh: 48,
    assumption: growthAssumption(0.12),
  },
  expectedReturnGap: null,
  scenarios: [
    scenario({
      kind: "bull",
      returnPercent: 0.184,
      assumption: growthAssumption(0.2),
      driver: "fcf_growth_trend",
      anchorPeriods: ["2017-12-31", "2021-12-31"],
    }),
  ],
  scenariosGap: null,
  conviction: "moderate",
  momentum: "stable",
  keyDrivers: [],
};

function renderSection(outlook: Partial<OutlookView> = {}, locale = "en-US") {
  return render(
    <LanguageProvider>
      <AtlasOutlookSection
        outlook={{ role: "sensitivity", shortTerm, longTerm, ...outlook }}
        latestChanges={[]}
        t={t as never}
        locale={locale}
      />
    </LanguageProvider>,
  );
}

/** Intl's Swedish percent: U+2212 minus and a no-break space before "%". */
const SV = (text: string) => text.replace(/-/g, "\u2212").replace(/ %/g, "\u00a0%");
/** The same, as Testing Library reads rendered text: it folds the no-break
 * space into a plain one. */
const SV_TEXT = (text: string) => text.replace(/-/g, "\u2212");

describe("formatPercent -- display precision and locale, never a cap", () => {
  it("one decimal below 10%", () => {
    expect(formatPercent(0.0628, "en-US")).toBe("+6.3%");
    expect(formatPercent(-0.051, "en-US")).toBe("-5.1%");
  });
  it("whole percents from 10%", () => {
    expect(formatPercent(0.1679, "en-US")).toBe("+17%");
    expect(formatPercent(-0.4, "en-US")).toBe("-40%");
  });
  it("a value that rounds up to 10% reads as a whole percent", () => {
    expect(formatPercent(0.0996, "en-US")).toBe("+10%");
  });
  it("never caps a large magnitude", () => {
    expect(formatPercent(49.98, "en-US")).toBe("+4,998%");
    expect(formatPercent(12.94, "sv-SE")).toBe(SV("+1 294 %").replace(" 294", "\u00a0294"));
  });
  it("no sign on a zero, including a negative zero", () => {
    expect(formatPercent(-0.0001, "en-US")).toBe("0.0%");
    expect(formatPercent(0, "en-US")).toBe("0.0%");
  });
  it("Swedish uses a decimal comma, the Swedish minus and a spaced percent sign", () => {
    expect(formatPercent(0.043, "sv-SE")).toBe(SV("+4,3 %"));
    expect(formatPercent(-0.644, "sv-SE")).toBe(SV("-64 %"));
    expect(formatPercent(-0.051, "sv-SE")).toBe(SV("-5,1 %"));
  });
});

describe("AtlasOutlookSection -- a sensitivity, never a forecast", () => {
  it("is headed as a sensitivity and says it is not a forecast", () => {
    renderSection();
    expect(screen.getByText("investmentCase.outlook.heading")).toBeInTheDocument();
    expect(screen.getByText("investmentCase.outlook.caption")).toBeInTheDocument();
  });

  it("the re-rating shows no horizon; the 4-year sensitivity shows its four years", () => {
    renderSection();
    expect(screen.getByText("investmentCase.outlook.shortTermBasisNote")).toBeInTheDocument();
    expect(screen.getByText('investmentCase.outlook.longTermBasisNote({"years":"4"})')).toBeInTheDocument();
    expect(screen.queryByText(/months/)).not.toBeInTheDocument();
  });

  it("a Swedish page renders every sensitivity number with Swedish decimals", () => {
    renderSection({}, "sv-SE");
    expect(screen.getByText(SV_TEXT("-20 % → +10 %"))).toBeInTheDocument();
    expect(screen.getByText(SV_TEXT("+6,1 % → +18 %"))).toBeInTheDocument();
    expect(screen.getByText(SV_TEXT('investmentCase.outlook.scenarioAssumptionNote({"targetYield":"3,6 %"})'))).toBeInTheDocument();
    expect(screen.queryByText(/\d\.\d/)).not.toBeInTheDocument();
  });

  it("says a range leaves out its withheld endpoint, naming the anchor year", () => {
    renderSection();
    expect(screen.getByText('investmentCase.outlook.partialRangeNote({"periods":"2016"})')).toBeInTheDocument();
  });

  it("a range with every endpoint shown carries no partial-range note", () => {
    renderSection({ shortTerm: { ...shortTerm, scenarios: [scenario({ kind: "base" })] } });
    expect(screen.queryByText(/partialRangeNote/)).not.toBeInTheDocument();
  });

  it("renders a withheld endpoint as its reason and anchor year, never a number", () => {
    renderSection();
    expect(screen.getByText('investmentCase.outlook.withheld({"period":"2016"})')).toBeInTheDocument();
    expect(screen.queryByText("+0.0%")).not.toBeInTheDocument();
    // Nor its pathological assumption: a near-zero yield is no usable input.
    expect(screen.queryByText('investmentCase.outlook.scenarioAssumptionNote({"targetYield":"0.1%"})')).not.toBeInTheDocument();
  });

  it("lists a median's two anchor years oldest first", () => {
    renderSection({
      shortTerm: { ...shortTerm, scenarios: [scenario({ kind: "base", anchorPeriods: ["2020-12-31", "2011-12-31"] })] },
    });
    expect(screen.getByText('investmentCase.outlook.anchorYear({"periods":"2011, 2020"})')).toBeInTheDocument();
  });

  it("names each endpoint for its assumption, not Bull/Base/Bear", () => {
    renderSection();
    expect(screen.getByText("investmentCase.outlook.baseCaseLabel")).toBeInTheDocument();
    expect(screen.getByText("investmentCase.outlook.growthBullCaseLabel")).toBeInTheDocument();
  });

  it("discloses anchor provenance: the year, or the 4-year window", () => {
    renderSection();
    expect(screen.getByText('investmentCase.outlook.anchorYear({"periods":"2019"})')).toBeInTheDocument();
    expect(screen.getByText('investmentCase.outlook.anchorWindow({"periods":"2017–2021"})')).toBeInTheDocument();
  });

  it("shows no conviction badge beside a sensitivity", () => {
    renderSection();
    expect(screen.queryByText(/convictionLabel|convictionCaption|conviction\.level/)).not.toBeInTheDocument();
  });

  it("names not-applicable as its own final state, distinct from missing data", () => {
    const notApplicable = (horizon: HorizonOutlookView): HorizonOutlookView => ({
      ...horizon,
      expectedReturn: null,
      expectedReturnGap: "valuation_not_applicable",
      scenarios: [],
      scenariosGap: "valuation_not_applicable",
    });
    renderSection({ shortTerm: notApplicable(shortTerm), longTerm: notApplicable(longTerm) });
    expect(screen.getAllByText("investmentCase.outlook.gap.valuationNotApplicable").length).toBeGreaterThan(0);
    expect(screen.getAllByText("investmentCase.outlook.notApplicable").length).toBeGreaterThan(0);
    expect(screen.queryByText("investmentCase.outlook.notYetComputed")).not.toBeInTheDocument();
    expect(screen.queryByText("investmentCase.outlook.gap.valuationNotConclusive")).not.toBeInTheDocument();
  });

  it("missing data stays 'not yet computed', never 'not applicable'", () => {
    const missing = { ...shortTerm, expectedReturn: null, expectedReturnGap: "valuation_not_conclusive" as const, scenarios: [], scenariosGap: "valuation_not_conclusive" as const };
    renderSection({ shortTerm: missing });
    expect(screen.getAllByText("investmentCase.outlook.gap.valuationNotConclusive").length).toBeGreaterThan(0);
    expect(screen.queryByText("investmentCase.outlook.notApplicable")).not.toBeInTheDocument();
  });

  it("no hidden label -- aria-label or title -- words it as upside, expected return or forecast", () => {
    const { container } = renderSection();
    const hidden = [...container.querySelectorAll("[aria-label],[title]")].map(
      (el) => `${el.getAttribute("aria-label") ?? ""} ${el.getAttribute("title") ?? ""}`,
    );
    for (const label of hidden) expect(label).not.toMatch(/upside|uppsida|expected|förväntad|forecast|prognos/i);
  });

  it("renders nothing for a payload that does not claim the sensitivity role", () => {
    const { container } = renderSection({ role: "forecast" as never });
    expect(container.textContent).toBe("");
  });

  it("names the near-zero-anchor gap when a whole horizon is withheld", () => {
    renderSection({
      longTerm: {
        ...longTerm,
        expectedReturn: null,
        expectedReturnGap: "near_zero_fcf_anchor",
        scenarios: [],
        scenariosGap: "near_zero_fcf_anchor",
      },
    });
    expect(screen.getAllByText("investmentCase.outlook.gap.nearZeroFcfAnchor").length).toBeGreaterThan(0);
    expect(screen.getAllByText("investmentCase.outlook.withheldStatus").length).toBeGreaterThan(0);
  });
});

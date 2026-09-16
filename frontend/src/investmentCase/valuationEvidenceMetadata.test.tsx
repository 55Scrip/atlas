import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { en } from "../i18n/translations/en";
import { sv } from "../i18n/translations/sv";
import type { TranslationKey } from "../i18n";
import { AtlasReasoningSection, type AtlasReasoningInput } from "./AtlasReasoningSection";
import {
  MAX_CARD_CAVEATS,
  shareBasisKey,
  valuationEvidenceCaveats,
  valuationEvidenceDetails,
  type EdgeObservationView,
  type ValuationEvidenceMetadataView,
} from "./valuationEvidenceMetadata";

/**
 * (Valuation Evidence Communication) The descriptive metadata as the page
 * reads it. Two things are under test: that what is said is true of the
 * evidence given -- above all the share basis, which until this sprint
 * claimed every earlier market value used *today's* share count, a
 * retired `fiscal_epoch_v2` behaviour -- and that nothing is said when
 * the evidence gives no reason to say it.
 *
 * Every metadata object below is a shape, never a company: no assertion
 * here names a ticker, and no rule in the module under test may.
 */
function tWith(dictionary: Record<string, string>) {
  return (key: TranslationKey, params: Record<string, string | number> = {}): string =>
    Object.entries(params).reduce<string>((s, [k, v]) => s.split("{{" + k + "}}").join(String(v)), dictionary[key] ?? key);
}

/** The real dictionaries, interpolated exactly as the provider does. */
const T = tWith(en);
const TSv = tWith(sv);

/** Deep history, an ordinary cash-flow year, room to the boundary, an
 * exact share basis: the Case with nothing worth warning about. */
function healthy(): ValuationEvidenceMetadataView {
  return {
    history: {
      validPriorCount: 14,
      minimumPriorCount: 3,
      atMinimumDepth: false,
      spanYears: 14,
      firstPriorFiscalPeriod: "2010-12-31",
      latestPriorFiscalPeriod: "2024-12-31",
      missingFiscalYears: [],
      yieldMinimum: 0.02,
      yieldMedian: 0.05,
      yieldMaximum: 0.09,
      yieldDispersion: 0.07,
      typicalYearOverYearMove: 0.25,
    },
    boundary: {
      currentYield: 0.012,
      nearestClassification: "fairly_valued",
      boundaryYield: 0.02,
      distance: 0.008,
      distancePercent: 0.667,
      closerThanTypicalMove: false,
    },
    currentCashFlow: {
      currentFreeCashFlow: 100,
      priorYearFreeCashFlow: 95,
      recentMedianFreeCashFlow: 90,
      historicalMedianFreeCashFlow: 70,
      recentYearsCompared: 3,
      versusPriorYear: 1.05,
      versusRecentMedian: 1.11,
      versusHistoricalMedian: 1.43,
      recentRange: [80, 120],
      positionVersusRecent: "within_range",
    },
    capitalIntensity: {
      currentCapitalExpenditure: 20,
      currentRevenue: 200,
      currentIntensity: 0.1,
      priorIntensityMinimum: 0.08,
      priorIntensityMedian: 0.11,
      priorIntensityMaximum: 0.15,
      priorYearsCompared: 5,
      versusPriorMedian: 0.91,
      positionVersusPriorRange: "within_range",
      currentOperatingCashFlow: 120,
      operatingCashFlowVersusPriorYear: 1.04,
      capitalExpenditureVersusPriorYear: 1.02,
    },
    denominator: { currentTreatment: "issuer_exact", priorTreatments: ["issuer_exact", "issuer_exact"], allExact: true },
    rangeEdge: {
      lowEdge: edge(2011, 0.02), highEdge: edge(2024, 0.09),
      secondLowest: edge(2012, 0.03), secondHighest: edge(2023, 0.08),
      distanceToLowEdge: -0.4, distanceToHighEdge: -0.87,
      distanceToSecondLowest: -0.6, distanceToSecondHighest: -0.85,
      priorsAtOrBelowCurrent: 0, priorsAtOrAboveCurrent: 14,
      singleLowEdgeDependency: false, singleHighEdgeDependency: false,
      lowEdgeGap: 0.01, highEdgeGap: 0.01, medianHistoryGap: 0.005,
    },
  };
}

/** One range-edge observation, at the year and yield given. */
function edge(fiscalYear: number, fcfYield: number): EdgeObservationView {
  return {
    fiscalPeriod: `${fiscalYear}-12-31`,
    fiscalYear,
    fcfYield,
    denominatorQuality: "issuer_exact",
    ageYears: 2025 - fiscalYear,
    uniquelyOwned: true,
  };
}

describe("the share basis is named from the evidence, never assumed", () => {
  it("says each period's own reported count when every epoch is exact", () => {
    const key = shareBasisKey(healthy().denominator);
    expect(key).toBe("investmentCase.analysis.valuation.shareCountExact");
    expect(en[key!]).toBe("Each earlier market value uses that period's own reported share count.");
  });

  it("names filed equivalence when some epoch is equivalent", () => {
    const denominator = { currentTreatment: "issuer_exact", priorTreatments: ["issuer_equivalent"], allExact: false };
    expect(shareBasisKey(denominator)).toBe("investmentCase.analysis.valuation.shareCountEquivalent");
  });

  it("names the interval when any epoch is bounded, even alongside equivalent ones", () => {
    const denominator = {
      currentTreatment: "issuer_equivalent",
      priorTreatments: ["issuer_equivalent", "issuer_bounded"],
      allExact: false,
    };
    expect(shareBasisKey(denominator)).toBe("investmentCase.analysis.valuation.shareCountBounded");
  });

  it("says nothing at all when no epoch carries a treatment", () => {
    expect(shareBasisKey({ currentTreatment: null, priorTreatments: [], allExact: false })).toBeNull();
  });

  it("no longer claims today's share count, in English or Swedish", () => {
    const stale = [/today's share count/i, /dagens antal aktier/i];
    for (const dictionary of [en, sv]) {
      for (const value of Object.values(dictionary)) {
        for (const pattern of stale) expect(value).not.toMatch(pattern);
      }
    }
  });

  it("states the v3 basis in both languages", () => {
    expect(en["investmentReasoning.valuationBasis.shareBasis"]).toBe(
      "Earlier market values use each period's own share basis, not today's.",
    );
    expect(sv["investmentReasoning.valuationBasis.shareBasis"]).toBe(
      "Tidigare marknadsvärden bygger på varje periods egen aktiebas, inte dagens.",
    );
  });
});

describe("caveats appear only when the evidence makes them true", () => {
  it("a deep, ordinary, exact Case gets none", () => {
    expect(valuationEvidenceCaveats(healthy(), T)).toEqual([]);
  });

  it("no metadata at all gets none", () => {
    expect(valuationEvidenceCaveats(null, T)).toEqual([]);
    expect(valuationEvidenceCaveats(undefined, T)).toEqual([]);
  });

  it("minimum depth is named with the engine's own count, not an invented threshold", () => {
    const metadata = healthy();
    metadata.history = { ...metadata.history, validPriorCount: 3, atMinimumDepth: true };
    expect(valuationEvidenceCaveats(metadata, T)).toEqual(["Rests on the minimum of 3 prior fiscal years."]);
  });

  it("a cash-flow year outside its own recent range is named in both directions", () => {
    const low = healthy();
    low.currentCashFlow = { ...low.currentCashFlow, positionVersusRecent: "below_range" };
    expect(valuationEvidenceCaveats(low, T)).toEqual([
      "This period's free cash flow is below every one of the 3 most recent compared years.",
    ]);
    const high = healthy();
    high.currentCashFlow = { ...high.currentCashFlow, positionVersusRecent: "above_range" };
    expect(valuationEvidenceCaveats(high, T)).toEqual([
      "This period's free cash flow is above every one of the 3 most recent compared years.",
    ]);
  });

  it("a boundary nearer than this history's own typical move is named with the class it would become", () => {
    const metadata = healthy();
    metadata.boundary = { ...metadata.boundary, closerThanTypicalMove: true, nearestClassification: "expensive" };
    expect(valuationEvidenceCaveats(metadata, T)).toEqual([
      "Nearer the Expensive boundary than this history's typical year-to-year move.",
    ]);
  });

  it("an inexact share basis is named, an exact one is not", () => {
    const metadata = healthy();
    metadata.denominator = { currentTreatment: "issuer_exact", priorTreatments: ["issuer_bounded"], allExact: false };
    expect(valuationEvidenceCaveats(metadata, T)).toEqual([
      "Some earlier periods are priced on an equivalent or bounded share basis, not an exactly reported one.",
    ]);
  });

  it("capital intensity is named only above every compared year, never merely above the median", () => {
    const above = healthy();
    above.capitalIntensity = { ...above.capitalIntensity, positionVersusPriorRange: "above_range" };
    expect(valuationEvidenceCaveats(above, T)).toEqual([
      "Capital expenditure takes a larger share of revenue than in any compared year.",
    ]);
    const heavyButInRange = healthy();
    heavyButInRange.capitalIntensity = { ...heavyButInRange.capitalIntensity, versusPriorMedian: 1.4 };
    expect(valuationEvidenceCaveats(heavyButInRange, T)).toEqual([]);
  });

  it("a Case can genuinely warrant more caveats than the card shows", () => {
    const metadata = healthy();
    metadata.history = { ...metadata.history, validPriorCount: 3, atMinimumDepth: true };
    metadata.currentCashFlow = { ...metadata.currentCashFlow, positionVersusRecent: "above_range" };
    metadata.boundary = { ...metadata.boundary, closerThanTypicalMove: true, nearestClassification: "expensive" };
    metadata.denominator = { currentTreatment: "issuer_bounded", priorTreatments: ["issuer_bounded"], allExact: false };
    metadata.capitalIntensity = { ...metadata.capitalIntensity, positionVersusPriorRange: "above_range" };
    const all = valuationEvidenceCaveats(metadata, T);
    expect(all).toHaveLength(5);
    // The card takes the first few; the valuation disclosure lists them all,
    // so the cap defers rather than discards.
    expect(all.slice(0, MAX_CARD_CAVEATS)).toHaveLength(3);
    expect(all.slice(0, MAX_CARD_CAVEATS)[0]).toMatch(/minimum of 3 prior fiscal years/);
  });

  it("every caveat has real Swedish, not an English fallback", () => {
    const metadata = healthy();
    metadata.history = { ...metadata.history, validPriorCount: 3, atMinimumDepth: true };
    metadata.currentCashFlow = { ...metadata.currentCashFlow, positionVersusRecent: "below_range" };
    metadata.boundary = { ...metadata.boundary, closerThanTypicalMove: true, nearestClassification: "expensive" };
    metadata.denominator = { currentTreatment: "issuer_bounded", priorTreatments: ["issuer_bounded"], allExact: false };
    metadata.capitalIntensity = { ...metadata.capitalIntensity, positionVersusPriorRange: "above_range" };
    const swedish = valuationEvidenceCaveats(metadata, TSv);
    expect(swedish).toHaveLength(5);
    expect(swedish).toEqual([
      "Vilar på minimikravet 3 tidigare räkenskapsår.",
      "Periodens fria kassaflöde är lägre än vart och ett av de 3 senast jämförda åren.",
      "Närmare gränsen till Dyr än historikens typiska förändring mellan år.",
      "Vissa tidigare perioder prissätts på en likvärdig eller avgränsad aktiebas, inte en exakt rapporterad.",
      "Investeringarna tar en större andel av omsättningen än något jämfört år.",
    ]);
    expect(swedish).toEqual(expect.not.arrayContaining(valuationEvidenceCaveats(metadata, T)));
  });
});

describe("the detail figures are shown only where the statements carry them", () => {
  it("states dispersion, boundary distance, cash flow and capital intensity", () => {
    expect(valuationEvidenceDetails(healthy(), T, "en-US")).toEqual([
      "Range ends: FY2011 at 2.00% and FY2024 at 9.00%; next-lowest FY2012 at 3.00%.",
      "0 of 14 prior years sit at or below today's yield of 1.20%.",
      "Prior-year FCF yields ran 2.0% to 9.0%, median 5.0%.",
      "67% away from classifying as Fairly valued.",
      "This period's free cash flow is 105% of last year's and 111% of the median of the 3 most recent compared years.",
      "Capital expenditure is 10.0% of revenue, against a 11.0% median across 5 compared years (8.0% to 15.0%).",
    ]);
  });

  it("fabricates no capital line when the statements carry no capital expenditure", () => {
    const metadata = healthy();
    metadata.capitalIntensity = {
      currentCapitalExpenditure: null,
      currentRevenue: null,
      currentIntensity: null,
      priorIntensityMinimum: null,
      priorIntensityMedian: null,
      priorIntensityMaximum: null,
      priorYearsCompared: 0,
      versusPriorMedian: null,
      positionVersusPriorRange: null,
      currentOperatingCashFlow: null,
      operatingCashFlowVersusPriorYear: null,
      capitalExpenditureVersusPriorYear: null,
    };
    const lines = valuationEvidenceDetails(metadata, T, "en-US");
    expect(lines).toHaveLength(5);
    expect(lines.join(" ")).not.toMatch(/Capital expenditure/);
  });

  it("fabricates no capital line when only this period's figures are missing", () => {
    // The prior years are known, the current one is not: a partial shape
    // that must stay silent rather than render a 0.0% intensity.
    const metadata = healthy();
    metadata.capitalIntensity = {
      ...metadata.capitalIntensity,
      currentCapitalExpenditure: null,
      currentRevenue: null,
      currentIntensity: null,
      versusPriorMedian: null,
      positionVersusPriorRange: null,
    };
    const lines = valuationEvidenceDetails(metadata, T, "en-US");
    expect(lines.join(" ")).not.toMatch(/Capital expenditure/);
    expect(lines.join(" ")).not.toMatch(/0\.0%/);
    expect(valuationEvidenceCaveats(metadata, T)).toEqual([]);
  });

  it("fabricates no capital line when only the prior years are missing", () => {
    const metadata = healthy();
    metadata.capitalIntensity = {
      ...metadata.capitalIntensity,
      priorIntensityMinimum: null,
      priorIntensityMedian: null,
      priorIntensityMaximum: null,
      priorYearsCompared: 0,
      versusPriorMedian: null,
      positionVersusPriorRange: null,
    };
    expect(valuationEvidenceDetails(metadata, T, "en-US").join(" ")).not.toMatch(/Capital expenditure/);
  });

  it("says nothing without metadata", () => {
    expect(valuationEvidenceDetails(null, T, "en-US")).toEqual([]);
  });
});

function reasoningInput(caveats: string[] | undefined): AtlasReasoningInput {
  return {
    growthStatus: "moderate",
    growthFacts: { supporting: [], contradicting: [] },
    valuationStatus: "expensive",
    valuationFacts: { supporting: [], contradicting: [] },
    valuationEvidence: { eligibility: "eligible", priorEpochCount: 14, hasCurrentYield: true },
    valuationCaveats: caveats,
    financialHealthStatus: "low",
    financialHealthFacts: { supporting: [], contradicting: [] },
    businessQualityStatus: "strong",
    businessQualityFacts: { supporting: [], contradicting: [] },
  };
}

function Wrapper({ input }: { input: AtlasReasoningInput }) {
  const { t } = useTranslation();
  return <AtlasReasoningSection input={input} t={t} />;
}

function renderCards(input: AtlasReasoningInput): string {
  const { container } = render(
    <LanguageProvider>
      <Wrapper input={input} />
    </LanguageProvider>,
  );
  return container.textContent ?? "";
}

describe("the reasoning card explains the status without changing it", () => {
  it("renders a caveat beside the same status it would have shown anyway", () => {
    const withCaveat = renderCards(reasoningInput(["Rests on the minimum of 3 prior fiscal years."]));
    const without = renderCards(reasoningInput(undefined));
    expect(withCaveat).toContain("Rests on the minimum of 3 prior fiscal years.");
    expect(without).not.toContain("Rests on the minimum of 3 prior fiscal years.");
    // The status word the card shows is identical with and without it.
    expect(withCaveat).toContain(sv["portfolio.cockpit.valuation.expensive"]);
    expect(without).toContain(sv["portfolio.cockpit.valuation.expensive"]);
    expect(withCaveat).toContain(sv["investmentCase.reasoning.valuation.expensive"]);
    expect(without).toContain(sv["investmentCase.reasoning.valuation.expensive"]);
  });

  it("adds nothing to the card when there is nothing to add", () => {
    expect(renderCards(reasoningInput([]))).toBe(renderCards(reasoningInput(undefined)));
  });
});

describe("range edge disclosure names the year, never discredits it", () => {
  /** A FAIRLY_VALUED Case whose current yield is below every prior but the
   * single year owning the low edge -- the shape the corpus audit found. */
  function edgeDependent(): ValuationEvidenceMetadataView {
    const metadata = healthy();
    metadata.rangeEdge = {
      ...metadata.rangeEdge!,
      lowEdge: edge(2025, 0.0181),
      secondLowest: edge(2024, 0.0238),
      priorsAtOrBelowCurrent: 1,
      singleLowEdgeDependency: true,
    };
    return metadata;
  }

  it("leads the caveats with the edge year, in English", () => {
    const caveats = valuationEvidenceCaveats(edgeDependent(), T);
    expect(caveats[0]).toBe(
      "FY2025 alone forms the low end of the historical range; today's FCF yield is below every other prior year.",
    );
  });

  it("leads the caveats with the edge year, in Swedish", () => {
    expect(valuationEvidenceCaveats(edgeDependent(), TSv)[0]).toBe(
      "FY2025 utgör ensamt intervallets nedre ände; dagens FCF-avkastning ligger under alla övriga tidigare år.",
    );
  });

  it("never calls the edge year an outlier, stale or anomalous, in either language", () => {
    const forbidden = /outlier|anomal|stale|distort|mislead|unreliab|avvikande|föråldrad|missvisande|opålitlig/i;
    for (const translate of [T, TSv]) {
      for (const line of [...valuationEvidenceCaveats(edgeDependent(), translate),
                          ...valuationEvidenceDetails(edgeDependent(), translate, "en-US")]) {
        expect(line).not.toMatch(forbidden);
      }
    }
  });

  it("stays silent when several years corroborate the classification", () => {
    expect(valuationEvidenceCaveats(healthy(), T)).toEqual([]);
  });

  it("surfaces the symmetric high-edge case", () => {
    const metadata = healthy();
    metadata.rangeEdge = {
      ...metadata.rangeEdge!, highEdge: edge(2022, 0.09), secondHighest: edge(2021, 0.07),
      singleHighEdgeDependency: true,
    };
    expect(valuationEvidenceCaveats(metadata, T)[0]).toBe(
      "FY2022 alone forms the high end of the historical range; today's FCF yield is above every other prior year.",
    );
  });

  it("says nothing when the backend sent no range edge at all", () => {
    const metadata = healthy();
    metadata.rangeEdge = null;
    expect(valuationEvidenceCaveats(metadata, T)).toEqual([]);
    expect(valuationEvidenceDetails(metadata, T, "en-US").join(" ")).not.toMatch(/Range ends/);
  });

  it("puts the edge fact ahead of the other caveats on the compact card", () => {
    const metadata = edgeDependent();
    metadata.history = { ...metadata.history, validPriorCount: 3, atMinimumDepth: true };
    const caveats = valuationEvidenceCaveats(metadata, T);
    expect(caveats[0]).toMatch(/FY2025 alone forms the low end/);
    expect(caveats.slice(0, MAX_CARD_CAVEATS)).toHaveLength(2);
  });
});

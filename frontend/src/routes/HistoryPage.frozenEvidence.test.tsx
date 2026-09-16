import { describe, expect, it } from "vitest";
import { en } from "../i18n/translations/en";
import { sv } from "../i18n/translations/sv";
import type { TranslationKey } from "../i18n";

/**
 * (Frozen Evidence History) The copy contract for historical valuation
 * evidence.
 *
 * The one thing this surface must never do is let a reader mistake what
 * Atlas had *then* for what it believes *now*. Every figure is therefore
 * labelled at the analysis, in both languages, and the three states a
 * snapshot can be in -- never recorded, recorded but withheld, recorded with
 * a real comparison -- stay distinct rather than collapsing into one vague
 * "unavailable".
 */
function translate(dictionary: Record<string, string>) {
  return (key: TranslationKey, params: Record<string, string | number> = {}): string =>
    Object.entries(params).reduce<string>(
      (text, [name, value]) => text.split("{{" + name + "}}").join(String(value)),
      dictionary[key] ?? key,
    );
}

const T = translate(en);
const TSv = translate(sv);

const EVIDENCE_KEYS: TranslationKey[] = [
  "history.analytical.evidence.notStored",
  "history.analytical.evidence.yieldAtAnalysis",
  "history.analytical.evidence.comparedWith",
  "history.analytical.evidence.withheld",
  "history.analytical.evidence.singleLowEdge",
  "history.analytical.evidence.singleHighEdge",
  "history.analytical.evidence.showDetail",
  "history.analytical.evidence.range",
  "history.analytical.evidence.corroboration",
  "history.analytical.evidence.support",
  "history.analytical.evidence.methodology",
  "history.analytical.evidence.tableCaption",
  "history.analytical.evidence.columnYear",
  "history.analytical.evidence.columnYield",
  "history.analytical.evidence.columnBasis",
];

describe("historical evidence is spoken about in the past tense", () => {
  it("labels every figure as belonging to the analysis, in English", () => {
    const temporal = /at the analysis|compared at the analysis|recorded at the time|at the time|used:/i;
    const figureKeys: TranslationKey[] = [
      "history.analytical.evidence.yieldAtAnalysis",
      "history.analytical.evidence.comparedWith",
      "history.analytical.evidence.range",
      "history.analytical.evidence.corroboration",
      "history.analytical.evidence.support",
      "history.analytical.evidence.tableCaption",
    ];
    for (const key of figureKeys) expect(en[key]).toMatch(temporal);
  });

  it("labels every figure as belonging to the analysis, in Swedish", () => {
    const temporal = /vid analysen|registrerade d|som användes|jämfördes/i;
    const figureKeys: TranslationKey[] = [
      "history.analytical.evidence.yieldAtAnalysis",
      "history.analytical.evidence.comparedWith",
      "history.analytical.evidence.range",
      "history.analytical.evidence.corroboration",
      "history.analytical.evidence.support",
      "history.analytical.evidence.tableCaption",
    ];
    for (const key of figureKeys) expect(sv[key]).toMatch(temporal);
  });

  it("never calls a historical figure current", () => {
    for (const key of EVIDENCE_KEYS) {
      expect(en[key]).not.toMatch(/\bcurrent\b/i);
      expect(sv[key]).not.toMatch(/\bnuvarande\b|\bdagens\b/i);
    }
  });

  it("describes the edge year without discrediting it", () => {
    const forbidden = /outlier|stale|anomal|distort|mislead|unreliab|avvikande|föråldrad|missvisande|opålitlig/i;
    for (const key of EVIDENCE_KEYS) {
      expect(en[key]).not.toMatch(forbidden);
      expect(sv[key]).not.toMatch(forbidden);
    }
  });
});

describe("the three snapshot states stay distinct", () => {
  it("a snapshot that predates evidence persistence says exactly that", () => {
    expect(T("history.analytical.evidence.notStored")).toBe(
      "Detailed valuation evidence was not stored for this analysis.",
    );
    expect(TSv("history.analytical.evidence.notStored")).toBe(
      "Detaljerad värderingsevidens sparades inte för den här analysen.",
    );
  });

  it("never claims that Atlas had no evidence", () => {
    expect(en["history.analytical.evidence.notStored"]).toMatch(/not stored/i);
    expect(en["history.analytical.evidence.notStored"]).not.toMatch(/no evidence|none|missing/i);
  });

  it("a withheld valuation is worded differently from a never-recorded one", () => {
    const withheld = T("history.analytical.evidence.withheld", { support: "insufficient_input" });
    expect(withheld).not.toBe(T("history.analytical.evidence.notStored"));
    expect(withheld).toMatch(/no fiscal years qualified/i);
    expect(withheld).toMatch(/insufficient_input/);
  });

  it("a real comparison names how many fiscal years it rested on", () => {
    expect(T("history.analytical.evidence.comparedWith", { count: 16 })).toBe(
      "Compared with 16 earlier fiscal years recorded at the time.",
    );
  });
});

describe("range-edge history reuses the disclosure semantics, in the past tense", () => {
  it("names the low-edge year for an edge-dependent historical snapshot", () => {
    expect(T("history.analytical.evidence.singleLowEdge", { year: 2025 })).toBe(
      "FY2025 formed the low end of the range. At the analysis, the FCF yield was below every other stored prior year.",
    );
  });

  it("names the low-edge year in Swedish", () => {
    expect(TSv("history.analytical.evidence.singleLowEdge", { year: 2009 })).toBe(
      "FY2009 utgjorde intervallets nedre ände. Vid analysen låg FCF-avkastningen under alla övriga sparade tidigare år.",
    );
  });

  it("implements the symmetric high-edge sentence", () => {
    expect(T("history.analytical.evidence.singleHighEdge", { year: 2022 })).toMatch(/high end of the range/);
  });

  it("states the range ends and the corroboration count as figures of their time", () => {
    expect(T("history.analytical.evidence.range", { lowYear: 2009, low: "0.45%", highYear: 2011, high: "15.87%" })).toBe(
      "Range ends at the analysis: FY2009 at 0.45% and FY2011 at 15.87%.",
    );
    expect(T("history.analytical.evidence.corroboration", { below: 1, count: 16 })).toBe(
      "1 of 16 recorded prior years sat at or below the yield at the analysis.",
    );
  });
});

describe("both dictionaries carry every key", () => {
  it("has Swedish for every English evidence key and vice versa", () => {
    for (const key of EVIDENCE_KEYS) {
      expect(typeof en[key]).toBe("string");
      expect(typeof sv[key]).toBe("string");
      expect(sv[key]).not.toBe(en[key]);
    }
  });

  it("names the prior-epoch table columns for screen readers", () => {
    for (const key of ["history.analytical.evidence.columnYear",
                       "history.analytical.evidence.columnYield",
                       "history.analytical.evidence.columnBasis"] as TranslationKey[]) {
      expect(en[key].length).toBeGreaterThan(2);
      expect(sv[key].length).toBeGreaterThan(2);
    }
  });
});

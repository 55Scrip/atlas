import { describe, expect, it } from "vitest";
import { describeFitVerdict, describeFitVerdictCode } from "./describeFitVerdict";
import type { TranslationKey } from "../i18n";

function fakeTranslate(key: TranslationKey, params?: Record<string, string | number>): string {
  return params ? `${key}(${JSON.stringify(params)})` : key;
}

describe("describeFitVerdictCode", () => {
  it("returns null for a null code", () => {
    expect(describeFitVerdictCode(null, null, fakeTranslate)).toBeNull();
  });

  it("returns null for an unrecognized code", () => {
    expect(describeFitVerdictCode("not_a_real_code", null, fakeTranslate)).toBeNull();
  });

  it("translates a code with no count", () => {
    expect(describeFitVerdictCode("risk_gate", null, fakeTranslate)).toBe("portfolioFit.verdictReason.riskGate");
  });

  it("uses the singular multiplePoorOne key when the count is exactly 1", () => {
    expect(describeFitVerdictCode("multiple_poor", 1, fakeTranslate)).toBe(
      'portfolioFit.verdictReason.multiplePoorOne({"count":1})',
    );
  });

  it("uses the plural multiplePoorOther key for any other count", () => {
    expect(describeFitVerdictCode("multiple_poor", 3, fakeTranslate)).toBe(
      'portfolioFit.verdictReason.multiplePoorOther({"count":3})',
    );
  });

  it("interpolates the count for mostly_excellent", () => {
    expect(describeFitVerdictCode("mostly_excellent", 4, fakeTranslate)).toBe(
      'portfolioFit.verdictReason.mostlyExcellent({"count":4})',
    );
  });
});

describe("describeFitVerdict", () => {
  it("prefers the code-driven sentence over the raw English text", () => {
    const result = describeFitVerdict(
      { overallReasoning: ["raw english"], overallReasoningCode: "mixed", overallReasoningCount: null },
      fakeTranslate,
    );
    expect(result).toBe("portfolioFit.verdictReason.mixed");
  });

  it("falls back to the raw first reasoning line when no code is present", () => {
    const result = describeFitVerdict(
      { overallReasoning: ["raw english"], overallReasoningCode: null, overallReasoningCount: null },
      fakeTranslate,
    );
    expect(result).toBe("raw english");
  });

  it("returns null when there is neither a code nor any raw reasoning", () => {
    const result = describeFitVerdict(
      { overallReasoning: [], overallReasoningCode: null, overallReasoningCount: null },
      fakeTranslate,
    );
    expect(result).toBeNull();
  });
});

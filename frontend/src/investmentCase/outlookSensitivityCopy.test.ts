import { describe, expect, it } from "vitest";
import { en } from "../i18n/translations/en";
import { sv } from "../i18n/translations/sv";

/**
 * Outlook -> Sensitivity: the copy the sensitivity section, its Upside
 * and Horizon tiles and its reasoning label render. Pinned in both
 * languages because the wording *is* the fix -- a sensitivity worded as
 * a forecast is the defect this sprint removed.
 */
const SENSITIVITY_KEY = /^investmentCase\.(outlook\.|ratings\.(upside|horizon)\.)|^investmentReasoning\.engine\.expectedReturn$/;

function sensitivityCopy(dictionary: Record<string, string>): [string, string][] {
  return Object.entries(dictionary).filter(([key]) => SENSITIVITY_KEY.test(key));
}

const FORBIDDEN: Record<"en" | "sv", RegExp[]> = {
  en: [/expected return/i, /most likely/i, /\blikely\b/i, /\bbull\b/i, /\bbear\b/i, /\bbase\b/i, /6[–-]12/, /3[–-]5/, /price target/i, /\bmonths\b/i],
  sv: [/förväntad avkastning/i, /förväntat avkastning/i, /sannolik/i, /optimistisk/i, /pessimistisk/i, /\bbas\b/i, /6[–-]12/, /3[–-]5/, /kursmål/i, /månader/i],
};

describe("Outlook sensitivity copy -- never worded as a forecast", () => {
  for (const [language, dictionary] of [["en", en], ["sv", sv]] as const) {
    it(`${language}: no forecast, probability or horizon-range wording`, () => {
      for (const [key, value] of sensitivityCopy(dictionary)) {
        for (const pattern of FORBIDDEN[language]) {
          expect(value, `${key} = "${value}"`).not.toMatch(pattern);
        }
      }
    });
  }

  it("only the caption may say 'forecast' -- to say it is not one", () => {
    for (const [dictionary, word] of [[en, /forecast/i], [sv, /prognos/i]] as const) {
      const mentions = sensitivityCopy(dictionary).filter(([, value]) => word.test(value));
      expect(mentions.map(([key]) => key)).toEqual(["investmentCase.outlook.caption"]);
    }
    expect(en["investmentCase.outlook.caption"]).toMatch(/^Not a forecast\./);
    expect(sv["investmentCase.outlook.caption"]).toMatch(/^Inte en prognos\./);
  });

  it("names the section, the re-rating and the exact 4-year horizon", () => {
    expect(sv["investmentCase.outlook.heading"]).toBe("Värderingskänslighet");
    expect(en["investmentCase.outlook.heading"]).toBe("Valuation sensitivity");
    expect(sv["investmentCase.outlook.shortTerm.heading"]).toBe("Omvärdering");
    expect(sv["investmentCase.outlook.longTerm.heading"]).toBe("4 år");
    expect(sv["investmentCase.outlook.expectedReturnLabel.growth"]).toBe("4-årig känslighet");
    expect(sv["investmentCase.outlook.shortTermBasisNote"]).toMatch(/ingen tidshorisont/);
    expect(en["investmentCase.outlook.shortTermBasisNote"]).toMatch(/no time horizon/);
  });

  it("names the median endpoint as a median, never a base case", () => {
    expect(sv["investmentCase.outlook.baseCaseLabel"]).toBe("Vid medianvärdering");
    expect(sv["investmentCase.outlook.growthBaseCaseLabel"]).toBe("Vid mediantillväxt");
    expect(en["investmentCase.outlook.baseCaseLabel"]).toBe("At median valuation");
    expect(en["investmentCase.outlook.growthBaseCaseLabel"]).toBe("At median growth");
  });
});

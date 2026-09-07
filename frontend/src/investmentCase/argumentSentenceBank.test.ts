import { describe, expect, it } from "vitest";
import { CHALLENGE_SENTENCE_KEY, STRENGTH_SENTENCE_KEY } from "./HeroCard";
import { sv } from "../i18n/translations/sv";

/**
 * Canonical Reasoning Consolidation, Conflict 3 regression.
 *
 * `investment_case_synthesis._risk_highlights` puts a risk kind in
 * `strengths[]` when its finding is LOW and in `risks[]` when it is
 * HIGH. The frontend's Supports column pointed all three risk kinds at
 * the *challenge* sentences, so NVDA -- Financial Risk genuinely LOW --
 * rendered "En identifierad finansiell risk talar mot caset" under
 * "Talar för caset", contradicting canonical reasoning's
 * `financial_risk_not_elevated` on the same page.
 */
describe("investment argument sentence banks", () => {
  const RISK_KINDS = ["business_risk", "financial_risk", "valuation_risk"] as const;

  it("never prints a challenge sentence in the supports column", () => {
    for (const kind of RISK_KINDS) {
      expect(STRENGTH_SENTENCE_KEY[kind]).not.toBe(CHALLENGE_SENTENCE_KEY[kind]);
      expect(STRENGTH_SENTENCE_KEY[kind]).toContain(".supports.");
    }
  });

  it("gives every highlight kind a distinct sentence per direction", () => {
    for (const kind of Object.keys(STRENGTH_SENTENCE_KEY) as (keyof typeof STRENGTH_SENTENCE_KEY)[]) {
      expect(STRENGTH_SENTENCE_KEY[kind]).not.toBe(CHALLENGE_SENTENCE_KEY[kind]);
    }
  });

  it("states the positive meaning a LOW risk finding actually carries", () => {
    // The engine's own label for this strength is "a low-risk financial
    // position" -- the copy must agree with it, not invert it.
    const sentence = sv[STRENGTH_SENTENCE_KEY.financial_risk];
    expect(sentence).toMatch(/lågrisk/i);
    expect(sentence).not.toMatch(/talar mot/i);
  });

  it("keeps the thesis-risk category from reading as the investment thesis", () => {
    // Conflict 2 regression: `thesis_risk` is a risk category with no
    // evaluator (missing in 26/26 real cases). Labelled "Tes" it
    // collided with the THESIS_INTACT recommendation vocabulary --
    // "Atlas saknar fortfarande: Tes" beside "Den nuvarande tesen
    // kvarstår oförändrad."
    expect(sv["portfolio.cockpit.risk.category.thesis_risk"]).not.toBe("Tes");
    expect(sv["decisionSupport.badge.thesis_intact"]).toBe("Tesen kvarstår");
  });
});

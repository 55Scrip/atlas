import { describe, expect, it } from "vitest";
import { STANCE_LEVEL_KEY, STANCE_LEVEL_TONE } from "./statusTone";
import { en } from "../i18n/translations/en";
import { sv } from "../i18n/translations/sv";

describe("StanceLevel.avoid_decision -- Status/Explanation Language stabilization", () => {
  it("keeps the critical tone unchanged (only the label text was fixed, not the Stance engine's own severity)", () => {
    expect(STANCE_LEVEL_TONE.avoid_decision).toBe("critical");
  });

  it("stays distinct from wait's neutral tone -- the two levels must remain visually distinguishable, not just textually", () => {
    expect(STANCE_LEVEL_TONE.wait).toBe("neutral");
    expect(STANCE_LEVEL_TONE.avoid_decision).not.toBe(STANCE_LEVEL_TONE.wait);
  });

  it("still resolves to the same translation key (regression against an accidental key rename)", () => {
    expect(STANCE_LEVEL_KEY.avoid_decision).toBe("stance.level.avoidDecision");
  });

  it("no longer reads like 'insufficient evidence' in English -- avoid_decision means a genuine red flag, never merely 'not enough data yet' (see atlas.alpha.stance.models.StanceLevel.AVOID_DECISION's own docstring)", () => {
    const text = en["stance.level.avoidDecision"];
    expect(text.toLowerCase()).not.toMatch(/insufficient/);
    expect(text).not.toBe(en["stance.level.wait"]);
  });

  it("no longer reads like 'otillräckligt underlag' in Swedish, for the identical reason", () => {
    const text = sv["stance.level.avoidDecision"];
    expect(text.toLowerCase()).not.toMatch(/otillräck/);
    expect(text).not.toBe(sv["stance.level.wait"]);
  });

  it("wait's own 'not enough data yet' wording is unchanged -- this fix only touched avoid_decision", () => {
    expect(en["stance.level.wait"]).toBe("Wait for more evidence");
    expect(sv["stance.level.wait"]).toBe("Avvakta mer underlag");
  });
});

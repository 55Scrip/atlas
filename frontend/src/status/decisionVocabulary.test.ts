import { describe, expect, it } from "vitest";
import { DECISION_SUPPORT_BADGE_KEY } from "./statusTone";
import { ACTION_KEY } from "../investmentDecision/describeInvestmentDecision";
import { STANCE_LEVEL_KEY } from "./statusTone";
import { sv } from "../i18n/translations/sv";
import PORTFOLIO_SOURCE from "../routes/PortfolioPage.tsx?raw";
import WATCHLIST_SOURCE from "../routes/WatchlistPage.tsx?raw";
import HERO_SOURCE from "../investmentCase/HeroCard.tsx?raw";

/**
 * Convergence Sprint 3B, Phase R. One canonical state, one
 * investor-facing label.
 *
 * `ACTION_BY_DECISION_SUPPORT_LEVEL` (backend) maps `DecisionSupportLevel`
 * onto `DecisionAction` one-to-one, with no additional inputs -- so
 * rendering the action through its own translation bank gave the same
 * canonical value a second vocabulary. Watchlist did exactly that:
 * `thesis_intact` read "Tesen kvarstår" on Portfolio and the Investment
 * Case, and "Behåll" on Watchlist.
 */
describe("canonical decision-state vocabulary", () => {
  const SURFACES: Array<[string, string]> = [
    ["Portfolio", PORTFOLIO_SOURCE],
    ["Watchlist", WATCHLIST_SOURCE],
    ["Investment Case hero", HERO_SOURCE],
  ];

  it("renders DecisionSupportLevel through one shared bank on all three surfaces", () => {
    for (const [name, source] of SURFACES) {
      expect(source, `${name} should render the canonical bank`).toContain("DECISION_SUPPORT_BADGE_KEY");
    }
  });

  it("keeps the Investment Decision action bank off those surfaces", () => {
    for (const [name, source] of SURFACES) {
      expect(source, `${name} must not name the same state a second way`).not.toContain("ACTION_KEY");
    }
  });

  it("proves the two banks genuinely disagreed, so the guard above is not vacuous", () => {
    // Positive control. If these ever coincide the test above stops
    // meaning anything, and this will say so.
    expect(sv[DECISION_SUPPORT_BADGE_KEY.thesis_intact]).toBe("Tesen kvarstår");
    expect(sv[ACTION_KEY.hold]).toBe("Behåll");
    expect(sv[DECISION_SUPPORT_BADGE_KEY.thesis_intact]).not.toBe(sv[ACTION_KEY.hold]);
  });

  it("keeps Stance in its own vocabulary, never merged into the decision state", () => {
    const decisionLabels = new Set(Object.values(DECISION_SUPPORT_BADGE_KEY).map((key) => sv[key]));
    for (const key of Object.values(STANCE_LEVEL_KEY)) {
      expect(decisionLabels.has(sv[key]), `${sv[key]} must not double as a decision-state label`).toBe(false);
    }
  });

  it("gives every canonical level its own distinct label", () => {
    const labels = Object.values(DECISION_SUPPORT_BADGE_KEY).map((key) => sv[key]);
    expect(new Set(labels).size).toBe(labels.length);
  });

  it("never reconstructs a canonical value from a display string", () => {
    // The fix was to put the canonical enum on the wire, not to invert
    // the backend's lookup table in the frontend.
    // Indexing or importing it, not merely naming it in a comment --
    // WatchlistPage documents why it stopped using that bank.
    for (const [name, source] of SURFACES) {
      expect(source, `${name} must not index the action map`).not.toMatch(/ACTION_BY_DECISION_SUPPORT_LEVEL\s*\[/);
      expect(source, `${name} must not import the action map`).not.toMatch(/import[^;]*ACTION_BY_DECISION_SUPPORT_LEVEL/);
    }
    expect(WATCHLIST_SOURCE).toContain("decisionSupportLevel");
  });
});

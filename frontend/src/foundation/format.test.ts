import { describe, expect, it } from "vitest";
import { formatCurrency, formatPercentPoints } from "./format";

/**
 * An amount renders in the currency it is actually denominated in, or in no
 * currency at all.
 *
 * Sprint 69 found the Portfolio page showing `$2,543,747` for a portfolio
 * whose every holding is stored in SEK, because this module had a single
 * hardcoded USD formatter and no way to say otherwise. The figures were
 * right and the unit was wrong, which in an investment tool is worse than
 * showing nothing -- hence the deliberate absence of a default below.
 */
describe("formatCurrency", () => {
  it("labels SEK amounts as SEK", () => {
    expect(formatCurrency(2_543_747, "SEK")).toContain("SEK");
    expect(formatCurrency(2_543_747, "SEK")).not.toContain("$");
  });

  it("labels USD amounts as USD", () => {
    expect(formatCurrency(2_543_747, "USD")).toContain("$");
  });

  it("labels EUR amounts as EUR", () => {
    expect(formatCurrency(1_000, "EUR")).toContain("€");
  });

  it("normalises case and whitespace in the code", () => {
    expect(formatCurrency(1_000, " sek ")).toBe(formatCurrency(1_000, "SEK"));
  });

  it("renders no symbol at all when the currency is not established", () => {
    for (const unknown of [null, undefined, "", "   "]) {
      const rendered = formatCurrency(2_543_747, unknown);
      expect(rendered).not.toContain("$");
      expect(rendered).not.toContain("SEK");
      expect(rendered).not.toContain("€");
      expect(rendered).toBe("2,543,747");
    }
  });

  it("renders no symbol for a code Intl does not recognise, rather than guessing", () => {
    expect(formatCurrency(1_234, "NOTACURRENCY")).toBe("1,234");
  });

  it("keeps the number itself intact and never converts", () => {
    // The same figure under three labels must differ only in the label.
    const digits = (s: string) => s.replace(/[^0-9]/g, "");
    expect(digits(formatCurrency(2_543_747, "SEK"))).toBe("2543747");
    expect(digits(formatCurrency(2_543_747, "USD"))).toBe("2543747");
    expect(digits(formatCurrency(2_543_747, "EUR"))).toBe("2543747");
    expect(digits(formatCurrency(2_543_747, null))).toBe("2543747");
  });

  it("groups thousands and shows no fractional digits", () => {
    expect(formatCurrency(1_234_567, "SEK")).toMatch(/1[,\s ]234[,\s ]567/);
    expect(formatCurrency(1_234.56, "USD")).toBe("$1,235");
  });

  it("handles zero and negatives without losing the label", () => {
    expect(formatCurrency(0, "SEK")).toContain("SEK");
    expect(formatCurrency(-500, "SEK")).toContain("SEK");
    expect(formatCurrency(-500, "SEK")).toMatch(/-|−|\(/);
  });

  it("reuses one formatter per currency across calls", () => {
    // Same input, same output -- the cache must not leak state between codes.
    expect(formatCurrency(100, "SEK")).toBe(formatCurrency(100, "SEK"));
    expect(formatCurrency(100, "USD")).not.toBe(formatCurrency(100, "SEK"));
  });
});

describe("formatPercentPoints", () => {
  it("is unchanged by the currency work", () => {
    expect(formatPercentPoints(9.2)).toBe("9.2%");
    expect(formatPercentPoints(9.25, 2)).toBe("9.25%");
  });
});

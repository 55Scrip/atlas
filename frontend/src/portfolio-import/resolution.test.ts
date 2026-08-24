import { describe, expect, it } from "vitest";
import { resolveInstrument } from "./resolution";

describe("resolveInstrument -- ticker-shape recognition", () => {
  describe("US dot-suffix share classes (unchanged, regression)", () => {
    it("resolves a plain ticker", () => {
      expect(resolveInstrument("MSFT")).toEqual({ kind: "resolved", ticker: "MSFT", instrumentType: "equity" });
    });

    it("resolves BRK.B", () => {
      expect(resolveInstrument("BRK.B")).toEqual({ kind: "resolved", ticker: "BRK.B", instrumentType: "equity" });
    });
  });

  describe("Nordic hyphen-suffix share classes (Import Robustness, Internal Alpha Stabilization 1)", () => {
    it("resolves a raw, pasted VOLV-B ticker directly, not only via the registry's company-name lookup", () => {
      expect(resolveInstrument("VOLV-B")).toEqual({ kind: "resolved", ticker: "VOLV-B", instrumentType: "equity" });
    });

    it("resolves ATCO-B", () => {
      expect(resolveInstrument("ATCO-B")).toEqual({ kind: "resolved", ticker: "ATCO-B", instrumentType: "equity" });
    });

    it("resolves HM-B (no registry entry for this name -- must go through the ticker-shape rule, not the registry)", () => {
      expect(resolveInstrument("HM-B")).toEqual({ kind: "resolved", ticker: "HM-B", instrumentType: "equity" });
    });

    it("resolves INVE-B", () => {
      expect(resolveInstrument("INVE-B")).toEqual({ kind: "resolved", ticker: "INVE-B", instrumentType: "equity" });
    });

    it("still requires the input to already be uppercase -- a lowercase or mixed-case hyphenated string is left unresolved, never guessed", () => {
      expect(resolveInstrument("volv-b")).toEqual({ kind: "unresolved" });
      expect(resolveInstrument("Volv-B")).toEqual({ kind: "unresolved" });
    });

    it("still rejects a Title Case company name that happens to contain a hyphen -- shape alone is never enough", () => {
      expect(resolveInstrument("Volvo-Cars")).toEqual({ kind: "unresolved" });
    });

    it("still enforces the 1-2 letter suffix bound -- a longer hyphenated suffix is not a share class and stays unresolved", () => {
      expect(resolveInstrument("VOLV-BCD")).toEqual({ kind: "unresolved" });
    });

    it("the registry's own company-name lookup for the same instrument still resolves to the identical ticker (both paths agree)", () => {
      expect(resolveInstrument("Volvo B")).toEqual({ kind: "resolved", ticker: "VOLV-B", instrumentType: "equity" });
    });
  });

  describe("BTC/GOLD -- explicitly unchanged in this sprint", () => {
    /**
     * Import Robustness investigation (Internal Alpha Stabilization 1)
     * found this classification semantically questionable -- BTC/GOLD
     * are not equities -- but fixing it needs a real instrument-type
     * model and was explicitly scoped OUT of this sprint. This test
     * documents and pins the current, known, unchanged behavior rather
     * than silently letting it drift.
     */
    it("BTC still resolves as instrumentType 'equity' (known limitation, not fixed here)", () => {
      expect(resolveInstrument("BTC")).toEqual({ kind: "resolved", ticker: "BTC", instrumentType: "equity" });
    });

    it("GOLD still resolves as instrumentType 'equity' (known limitation, not fixed here)", () => {
      expect(resolveInstrument("GOLD")).toEqual({ kind: "resolved", ticker: "GOLD", instrumentType: "equity" });
    });
  });

  describe("registry-backed unsupported instruments (unchanged, regression)", () => {
    it("a fund/ETP/private registry hit with no ticker still comes back unsupported, never a guessed ticker", () => {
      expect(resolveInstrument("SpaceX")).toEqual({ kind: "unsupported", instrumentType: "private" });
    });
  });
});

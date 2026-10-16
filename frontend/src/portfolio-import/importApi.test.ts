import { describe, expect, it, vi, afterEach } from "vitest";
import { confirmImport, toConfirmHolding, type ParsedHoldingRow } from "./importApi";

/**
 * Portfolio Canonical Identity Retention — the confirm contract.
 *
 * Sprint 67 measured that this mapper was where an earned security identity
 * died: the preview response carried `canonicalSecurityId` and
 * `toConfirmHolding` mapped six fields, so pressing Confirm discarded it and
 * the Case binding stayed NULL. The fix is deliberately not "forward the
 * seventh field". This screen is not an authority on which company a Case is
 * about, so it forwards the row's own *source* identifiers and the backend
 * proves the identity again from them.
 */
const PREVIEW_ROW: ParsedHoldingRow = {
  lineNumber: 1,
  raw: "Volvo AB ser. B;VOLV-B;SE0000115446;Nasdaq Stockholm;10;100,00;SEK",
  originalName: "Volvo AB ser. B",
  ticker: "VOLV-B",
  quantity: 10,
  price: 100,
  valueAbsolute: 1000,
  weightPercent: null,
  currency: "SEK",
  status: "RESOLVED",
  message: null,
  instrumentType: null,
  candidates: [],
  alreadyHeld: false,
  isin: "SE0000115446",
  market: "Nasdaq Stockholm",
  identityStatus: "RESOLVED_EXISTING",
  identityReason: "ISIN SE0000115446 is already recorded against this security",
  canonicalSecurityId: "8075-0590-volvo",
  securityName: "Volvo AB",
  exchangeMic: "XSTO",
  strongIdentifierUsed: "ISIN",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("toConfirmHolding", () => {
  it("forwards the row's own hard identifier and venue", () => {
    const holding = toConfirmHolding(PREVIEW_ROW);

    expect(holding.isin).toBe("SE0000115446");
    expect(holding.market).toBe("Nasdaq Stockholm");
  });

  it("does not forward the canonical id the preview resolved", () => {
    const holding = toConfirmHolding(PREVIEW_ROW);

    expect(Object.keys(holding).sort()).toEqual([
      "currency",
      "isin",
      "market",
      "price",
      "quantity",
      "ticker",
      "valueAbsolute",
      "weightPercent",
    ]);
    expect(JSON.stringify(holding)).not.toContain("8075-0590-volvo");
  });

  it("leaves a row that carried no identifier without one", () => {
    const holding = toConfirmHolding({
      ...PREVIEW_ROW,
      isin: null,
      market: null,
      canonicalSecurityId: null,
      identityStatus: null,
    });

    expect(holding.isin).toBeNull();
    expect(holding.market).toBeNull();
    expect(holding.ticker).toBe("VOLV-B");
  });

  it("keeps a manual ticker override without touching the identifier", () => {
    const holding = toConfirmHolding(PREVIEW_ROW, "VOLVB");

    expect(holding.ticker).toBe("VOLVB");
    expect(holding.isin).toBe("SE0000115446");
  });
});

describe("confirmImport", () => {
  it("sends the identifier and no canonical id in the request body", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ batchId: "batch-1" }),
    } as Response);
    vi.stubGlobal("fetch", fetchMock);

    await confirmImport([toConfirmHolding(PREVIEW_ROW)], false);

    const call = fetchMock.mock.calls[0];
    expect(call).toBeDefined();
    const [endpoint, init] = call as [string, RequestInit];
    expect(endpoint).toBe("/api/alpha-portfolio/import");
    const body = JSON.parse(init.body as string);
    expect(body.holdings[0].isin).toBe("SE0000115446");
    expect(body.holdings[0].canonicalSecurityId).toBeUndefined();
  });

  it("sends the same identity contract on the replace path", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ batchId: null }),
    } as Response);
    vi.stubGlobal("fetch", fetchMock);

    await confirmImport([toConfirmHolding(PREVIEW_ROW)], true);

    const call = fetchMock.mock.calls[0];
    expect(call).toBeDefined();
    const [endpoint, init] = call as [string, RequestInit];
    expect(endpoint).toBe("/api/alpha-portfolio/reconcile");
    const body = JSON.parse(init.body as string);
    expect(body.mode).toBe("REPLACE_ALLOCATION");
    expect(body.holdings[0].market).toBe("Nasdaq Stockholm");
    expect(body.holdings[0].canonicalSecurityId).toBeUndefined();
  });
});

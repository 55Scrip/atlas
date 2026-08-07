/**
 * Portfolio Import v1.2 — bounded, explicit instrument registry.
 *
 * Replaces v1.1's flat name -> ticker dictionary. Still deterministic,
 * still a maintained lookup, not an attempt at universal coverage or a
 * general security master — the point is identity *safety* for this one
 * import flow: every entry represents one specific, verified instrument
 * identity, not a guess.
 *
 * Two safety rules this registry exists to enforce, both learned from a
 * real portfolio import (v1.2's hardening pass):
 *
 * 1. A company with more than one actively-traded public share class
 *    (Alphabet, Berkshire Hathaway) has NO bare/unqualified entry here.
 *    Only the fully-qualified name ("Alphabet Class C") resolves —
 *    defaulting an unqualified name to one class would be exactly the
 *    kind of guessed suffix this sprint forbids. An investor who pastes
 *    just "Alphabet" is left to confirm which class manually.
 * 2. An instrument whose identity is known but isn't a plain listed
 *    equity (a fund, an ETP, a private company) still gets an entry —
 *    with `ticker: null` — so the review screen can say "this is a
 *    recognized fund" instead of either fabricating a stock ticker for
 *    it or treating it as a blank unknown.
 *
 * Nordic-only local listings the real portfolio contained (Volvo B,
 * Alfa Laval, Trelleborg B, Sandvik, Assa Abloy B, Atlas Copco B,
 * SEB A, Schneider Electric) are deliberately left OUT of this
 * registry rather than mapped to a guessed Nasdaq Stockholm / Euronext
 * suffix convention Atlas has never verified — they fall through to
 * manual confirmation, per this sprint's own instruction to "verify
 * each mapping... or leave it unresolved."
 */

export type InstrumentType = "equity" | "fund" | "etp" | "private" | "other";

export interface InstrumentRegistryEntry {
  /** Names an investor would plausibly type or paste, lowercase-normalized
   *  for lookup. Not fuzzy aliases — exact known spellings only. */
  displayNames: string[];
  /** `null` when this instrument is recognized but isn't a plain listed
   *  equity the current Alpha backend can honestly persist as ticker +
   *  weight — see `resolution.ts`'s "unsupported" resolution kind. */
  ticker: string | null;
  instrumentType: InstrumentType;
  market?: string;
  shareClass?: string;
}

export const INSTRUMENT_REGISTRY: readonly InstrumentRegistryEntry[] = [
  // ---- unambiguous US/NASDAQ/NYSE equities, single public class ----
  { displayNames: ["microsoft"], ticker: "MSFT", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["apple"], ticker: "AAPL", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["amazon", "amazon.com"], ticker: "AMZN", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["nvidia"], ticker: "NVDA", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["tesla"], ticker: "TSLA", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["broadcom"], ticker: "AVGO", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["visa"], ticker: "V", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["mastercard"], ticker: "MA", instrumentType: "equity", market: "NYSE" },
  {
    displayNames: ["johnson & johnson", "johnson and johnson"],
    ticker: "JNJ",
    instrumentType: "equity",
    market: "NYSE",
  },
  {
    displayNames: ["procter & gamble", "procter and gamble"],
    ticker: "PG",
    instrumentType: "equity",
    market: "NYSE",
  },
  { displayNames: ["exxon mobil", "exxonmobil"], ticker: "XOM", instrumentType: "equity", market: "NYSE" },
  {
    displayNames: ["jpmorgan chase", "jpmorgan", "jp morgan"],
    ticker: "JPM",
    instrumentType: "equity",
    market: "NYSE",
  },
  { displayNames: ["walmart"], ticker: "WMT", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["eli lilly"], ticker: "LLY", instrumentType: "equity", market: "NYSE" },
  {
    displayNames: ["unitedhealth group", "unitedhealth"],
    ticker: "UNH",
    instrumentType: "equity",
    market: "NYSE",
  },
  { displayNames: ["home depot"], ticker: "HD", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["salesforce"], ticker: "CRM", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["adobe"], ticker: "ADBE", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["netflix"], ticker: "NFLX", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["coca-cola", "coca cola"], ticker: "KO", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["pepsico"], ticker: "PEP", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["costco"], ticker: "COST", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["oracle"], ticker: "ORCL", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["intel"], ticker: "INTC", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["cisco"], ticker: "CSCO", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["qualcomm"], ticker: "QCOM", instrumentType: "equity", market: "NASDAQ" },
  { displayNames: ["texas instruments"], ticker: "TXN", instrumentType: "equity", market: "NASDAQ" },
  {
    displayNames: ["thermo fisher scientific"],
    ticker: "TMO",
    instrumentType: "equity",
    market: "NYSE",
  },
  { displayNames: ["abbvie"], ticker: "ABBV", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["merck"], ticker: "MRK", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["pfizer"], ticker: "PFE", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["verizon"], ticker: "VZ", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["at&t"], ticker: "T", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["disney", "walt disney"], ticker: "DIS", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["nike"], ticker: "NKE", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["mcdonald's", "mcdonalds"], ticker: "MCD", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["starbucks"], ticker: "SBUX", instrumentType: "equity", market: "NASDAQ" },
  {
    displayNames: ["ibm", "international business machines"],
    ticker: "IBM",
    instrumentType: "equity",
    market: "NYSE",
  },
  { displayNames: ["paypal"], ticker: "PYPL", instrumentType: "equity", market: "NASDAQ" },
  {
    displayNames: ["booking holdings", "booking.com"],
    ticker: "BKNG",
    instrumentType: "equity",
    market: "NASDAQ",
  },
  { displayNames: ["uber"], ticker: "UBER", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["spotify"], ticker: "SPOT", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["shopify"], ticker: "SHOP", instrumentType: "equity", market: "NYSE" },
  {
    displayNames: ["meta platforms", "meta platforms a", "meta"],
    ticker: "META",
    instrumentType: "equity",
    market: "NASDAQ",
    shareClass: "A",
  },
  { displayNames: ["vistra"], ticker: "VST", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["vertiv"], ticker: "VRT", instrumentType: "equity", market: "NYSE" },
  { displayNames: ["applied materials"], ticker: "AMAT", instrumentType: "equity", market: "NASDAQ" },

  // ---- multi-class companies: only the fully-qualified name resolves;
  // the bare/unqualified name is deliberately absent from this registry
  // so it falls through to manual confirmation instead of defaulting
  // to a guessed class. ----
  {
    displayNames: ["alphabet class a"],
    ticker: "GOOGL",
    instrumentType: "equity",
    market: "NASDAQ",
    shareClass: "A",
  },
  {
    displayNames: ["alphabet class c"],
    ticker: "GOOG",
    instrumentType: "equity",
    market: "NASDAQ",
    shareClass: "C",
  },
  {
    displayNames: ["berkshire hathaway class a"],
    ticker: "BRK.A",
    instrumentType: "equity",
    market: "NYSE",
    shareClass: "A",
  },
  {
    displayNames: ["berkshire hathaway class b"],
    ticker: "BRK.B",
    instrumentType: "equity",
    market: "NYSE",
    shareClass: "B",
  },

  // ---- non-US primary listings represented by an unambiguous ADR ----
  { displayNames: ["taiwan semiconductor"], ticker: "TSM", instrumentType: "equity", market: "NYSE (ADR)" },
  { displayNames: ["astrazeneca"], ticker: "AZN", instrumentType: "equity", market: "NASDAQ (ADR)" },
  {
    displayNames: ["novo nordisk", "novo nordisk b"],
    ticker: "NVO",
    instrumentType: "equity",
    market: "NYSE (ADR)",
    shareClass: "B",
  },

  // ---- non-equity instruments: identity is known, but the current
  // Alpha backend can only persist ticker + weight and none of these
  // are a plain listed equity. `ticker` is deliberately `null` —
  // resolution.ts surfaces these as "unsupported", never a fabricated
  // stock ticker. ----
  {
    displayNames: ["coinshares xbt provider bitcoin tracker one", "coinshares xbt provider"],
    ticker: null,
    instrumentType: "etp",
  },
  {
    displayNames: ["länsförsäkringar global index", "lansforsakringar global index"],
    ticker: null,
    instrumentType: "fund",
  },
  { displayNames: ["avanza emerging markets"], ticker: null, instrumentType: "fund" },
  { displayNames: ["spacex"], ticker: null, instrumentType: "private" },
];

const LOOKUP: ReadonlyMap<string, InstrumentRegistryEntry> = new Map(
  INSTRUMENT_REGISTRY.flatMap((entry) => entry.displayNames.map((name) => [name, entry] as const)),
);

export function lookupInstrument(name: string): InstrumentRegistryEntry | null {
  return LOOKUP.get(name.trim().toLowerCase()) ?? null;
}

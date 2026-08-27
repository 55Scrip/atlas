"""Instrument Identity registry, ported from the frontend's own
`frontend/src/portfolio-import/instrumentRegistry.ts` -- the same
bounded, explicit, deterministic entries, not an attempt at universal
coverage. See that file's own module docstring for the full rationale
(no bare entry for a multi-share-class company, `ticker=None` for a
known-but-unsupported instrument type, only high-confidence Nordic
tickers). Kept as a second copy rather than a shared source for this
sprint -- the frontend's own copy is retired once the new unified
onboarding screen ships (see the Zero-Effort Onboarding Architecture's
Implementation Plan, Phase 5); consolidating the registry into one
place afterward is a natural, small follow-up, not blocking this one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

InstrumentType = str  # "equity" | "fund" | "etp" | "private" | "other"


@dataclass(frozen=True)
class InstrumentRegistryEntry:
    display_names: tuple[str, ...]
    ticker: str | None
    instrument_type: InstrumentType


INSTRUMENT_REGISTRY: tuple[InstrumentRegistryEntry, ...] = (
    InstrumentRegistryEntry(("microsoft", "microsoft corp", "microsoft corporation"), "MSFT", "equity"),
    InstrumentRegistryEntry(("apple",), "AAPL", "equity"),
    InstrumentRegistryEntry(("amazon", "amazon.com", "amazon.com inc"), "AMZN", "equity"),
    InstrumentRegistryEntry(("nvidia",), "NVDA", "equity"),
    InstrumentRegistryEntry(("tesla",), "TSLA", "equity"),
    InstrumentRegistryEntry(("broadcom",), "AVGO", "equity"),
    InstrumentRegistryEntry(("visa",), "V", "equity"),
    InstrumentRegistryEntry(("mastercard",), "MA", "equity"),
    InstrumentRegistryEntry(("johnson & johnson", "johnson and johnson"), "JNJ", "equity"),
    InstrumentRegistryEntry(("procter & gamble", "procter and gamble"), "PG", "equity"),
    InstrumentRegistryEntry(("exxon mobil", "exxonmobil"), "XOM", "equity"),
    InstrumentRegistryEntry(("jpmorgan chase", "jpmorgan", "jp morgan"), "JPM", "equity"),
    InstrumentRegistryEntry(("walmart",), "WMT", "equity"),
    InstrumentRegistryEntry(("eli lilly",), "LLY", "equity"),
    InstrumentRegistryEntry(("unitedhealth group", "unitedhealth"), "UNH", "equity"),
    InstrumentRegistryEntry(("home depot",), "HD", "equity"),
    InstrumentRegistryEntry(("salesforce",), "CRM", "equity"),
    InstrumentRegistryEntry(("adobe",), "ADBE", "equity"),
    InstrumentRegistryEntry(("netflix",), "NFLX", "equity"),
    InstrumentRegistryEntry(("coca-cola", "coca cola"), "KO", "equity"),
    InstrumentRegistryEntry(("pepsico",), "PEP", "equity"),
    InstrumentRegistryEntry(("costco",), "COST", "equity"),
    InstrumentRegistryEntry(("oracle",), "ORCL", "equity"),
    InstrumentRegistryEntry(("intel",), "INTC", "equity"),
    InstrumentRegistryEntry(("cisco",), "CSCO", "equity"),
    InstrumentRegistryEntry(("qualcomm",), "QCOM", "equity"),
    InstrumentRegistryEntry(("texas instruments",), "TXN", "equity"),
    InstrumentRegistryEntry(("thermo fisher scientific",), "TMO", "equity"),
    InstrumentRegistryEntry(("abbvie",), "ABBV", "equity"),
    InstrumentRegistryEntry(("merck",), "MRK", "equity"),
    InstrumentRegistryEntry(("pfizer",), "PFE", "equity"),
    InstrumentRegistryEntry(("verizon",), "VZ", "equity"),
    InstrumentRegistryEntry(("at&t",), "T", "equity"),
    InstrumentRegistryEntry(("disney", "walt disney"), "DIS", "equity"),
    InstrumentRegistryEntry(("nike",), "NKE", "equity"),
    InstrumentRegistryEntry(("mcdonald's", "mcdonalds"), "MCD", "equity"),
    InstrumentRegistryEntry(("starbucks",), "SBUX", "equity"),
    InstrumentRegistryEntry(("ibm", "international business machines"), "IBM", "equity"),
    InstrumentRegistryEntry(("paypal",), "PYPL", "equity"),
    InstrumentRegistryEntry(("booking holdings", "booking.com"), "BKNG", "equity"),
    InstrumentRegistryEntry(("uber",), "UBER", "equity"),
    InstrumentRegistryEntry(("spotify",), "SPOT", "equity"),
    InstrumentRegistryEntry(("shopify",), "SHOP", "equity"),
    InstrumentRegistryEntry(
        ("meta platforms", "meta platforms a", "meta platforms inc", "meta"), "META", "equity"
    ),
    InstrumentRegistryEntry(("vistra",), "VST", "equity"),
    InstrumentRegistryEntry(
        ("vertiv", "vertiv holdings", "vertiv holdings a", "vertiv holdings co"), "VRT", "equity"
    ),
    InstrumentRegistryEntry(("applied materials",), "AMAT", "equity"),
    # multi-class companies: only the fully-qualified name resolves.
    InstrumentRegistryEntry(("alphabet class a", "alphabet inc class a"), "GOOGL", "equity"),
    InstrumentRegistryEntry(("alphabet class c", "alphabet inc class c"), "GOOG", "equity"),
    InstrumentRegistryEntry(
        ("berkshire hathaway class a", "berkshire hathaway inc class a"), "BRK.A", "equity"
    ),
    InstrumentRegistryEntry(
        ("berkshire hathaway class b", "berkshire hathaway inc class b"), "BRK.B", "equity"
    ),
    # non-US primary listings represented by an unambiguous ADR.
    InstrumentRegistryEntry(
        (
            "taiwan semiconductor",
            "taiwan semiconductor mfg co",
            "taiwan semiconductor manufacturing",
            "tsmc",
        ),
        "TSM",
        "equity",
    ),
    InstrumentRegistryEntry(("astrazeneca",), "AZN", "equity"),
    InstrumentRegistryEntry(("novo nordisk", "novo nordisk b"), "NVO", "equity"),
    # Nasdaq Stockholm large caps -- only high-confidence local tickers.
    InstrumentRegistryEntry(("investor b", "investor ab b", "investor ab class b"), "INVE-B", "equity"),
    InstrumentRegistryEntry(("atlas copco b", "atlas copco ab b"), "ATCO-B", "equity"),
    InstrumentRegistryEntry(("volvo b", "volvo ab b"), "VOLV-B", "equity"),
    InstrumentRegistryEntry(("assa abloy b", "assa abloy ab b"), "ASSA-B", "equity"),
    InstrumentRegistryEntry(("seb a", "seb ab a"), "SEB-A", "equity"),
    InstrumentRegistryEntry(("alfa laval",), "ALFA", "equity"),
    InstrumentRegistryEntry(("sandvik",), "SAND", "equity"),
    InstrumentRegistryEntry(("trelleborg b", "trelleborg ab b"), "TREL-B", "equity"),
    InstrumentRegistryEntry(("abb", "abb ltd"), "ABB", "equity"),
    InstrumentRegistryEntry(("munters", "munters group", "munters group ab"), "MTRS", "equity"),
    InstrumentRegistryEntry(("castellum",), "CAST", "equity"),
    InstrumentRegistryEntry(("nordnet",), "SAVE", "equity"),
    # non-equity instruments: identity known, ticker deliberately None.
    InstrumentRegistryEntry(
        ("coinshares xbt provider bitcoin tracker one", "coinshares xbt provider"), None, "etp"
    ),
    InstrumentRegistryEntry(
        ("länsförsäkringar global index", "lansforsakringar global index"), None, "fund"
    ),
    InstrumentRegistryEntry(("avanza emerging markets",), None, "fund"),
    InstrumentRegistryEntry(("spacex",), None, "private"),
)

_DASH_VARIANT_PATTERN = re.compile("[‐‑‒–—−]")
_TRAILING_PERIOD_PATTERN = re.compile(r"\.(?=\s|$)")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_for_lookup(raw: str) -> str:
    """Punctuation/whitespace normalization only, never a matching
    strategy on its own -- ported verbatim from `instrumentRegistry.ts`'s
    identical function."""
    text = _DASH_VARIANT_PATTERN.sub("-", raw)
    text = text.replace(",", " ")
    text = _TRAILING_PERIOD_PATTERN.sub("", text)
    text = _WHITESPACE_PATTERN.sub(" ", text)
    return text.strip().lower()


_LOOKUP: dict[str, InstrumentRegistryEntry] = {
    normalize_for_lookup(name): entry
    for entry in INSTRUMENT_REGISTRY
    for name in entry.display_names
}


def lookup_instrument(name: str) -> InstrumentRegistryEntry | None:
    return _LOOKUP.get(normalize_for_lookup(name))

"""Real, network-calling `BusinessDataProvider` implementations (ATLAS-031).

Deliberately **not** inside `atlas.analysis_engine.business_data` --
that package's own boundary test
(`tests/unit/analysis_engine/business_data/test_boundaries.py`) forbids
any HTTP/network import anywhere in it, by design (ATLAS-022's own
"no external API integration this sprint" decision). A provider that
makes real calls has to live somewhere else and only *implement* the
`atlas.analysis_engine.business_data.providers.BusinessDataProvider`
Protocol from the outside, exactly the way `StaticBusinessDataProvider`
already demonstrates the extension point.

Two providers, chosen after a live Phase 1 audit (not from memory):

- `sec_edgar.SecEdgarFundamentalsProvider` -- fundamentals (Revenue,
  Free Cash Flow, Capital Expenditure, Buybacks, Issuance, Dividends,
  Debt Issuance/Repayment). Official, free, keyless, well-documented
  XBRL data -- but US SEC-registered filers only.
- `alpha_vantage.AlphaVantageMarketDataProvider` -- market data (share
  price, shares outstanding), combined into one
  `SourceKind.MARKET_DATA_SNAPSHOT` document. Official and documented,
  but requires the operator's own free API key (`ALPHA_VANTAGE_API_KEY`)
  and is rate-limited on the free tier.

Both return only `RawBusinessDocument` -- no score, no summary, no
conclusion, matching `atlas.analysis_engine.business_data.providers`'s
own contract exactly. Provider-specific parsing, error mapping, and
identity resolution live entirely in this package; nothing downstream
(`business_data`, `business_facts`, `valuation.facts`, any evaluator)
ever branches on which provider produced a record.
"""
from __future__ import annotations

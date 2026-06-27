# Atlas

Private investment research platform for AI infrastructure.

## Version
v0.1.0 — Foundation

## MVP commands

```bash
atlas init
atlas add-company TSM --name "Taiwan Semiconductor Manufacturing Company" --atlas-id AI-001 --exchange NYSE --country Taiwan --currency USD --sector Semiconductors --industry Foundry
atlas import-financials TSM data/tsm_financials.csv
atlas list-companies
atlas report NVDA
atlas portfolio analyze portfolio.json NVDA
atlas compare NVDA AMD MSFT
atlas watchlist analyze watchlist.json
atlas memory save NVDA memory.json
atlas memory show memory.json
atlas memory compare memory.json NVDA
```

## Financial import CSV

```csv
fiscal_year,revenue,gross_profit,operating_income,net_income,operating_cashflow,capex,free_cashflow,total_assets,equity,debt,cash,shares_outstanding
2024,120000,70000,45000,37000,50000,-13000,37000,560000,350000,85000,105000,1006
```

```bash
atlas import-financials TSM data/tsm_financials.csv
```

## Company analysis engine

```bash
atlas report NVDA
```

Sprint 1 introduces the first modular Atlas investment engine. It produces an
`InvestmentReport` from five score categories:

- quality
- growth
- valuation
- financial strength
- risk

Each category exposes a typed dataclass with a 0-100 score, reasoning, and
confidence. `AtlasInvestmentEngine` combines replaceable category scorers using
configurable weights and maps the final Atlas Score to an overall recommendation.
The Sprint 4 explanation engine then turns the deterministic `InvestmentReport`
into a bull case, bear case, key strengths, key risks, valuation concern, mind
changers, and confidence explanation. It does not make external AI calls.

Default recommendation bands:

- Strong Buy: 90+
- Buy: 75-89
- Hold: 60-74
- Sell: 40-59
- Strong Sell: below 40

The current CLI uses placeholder analysis signals for:

- NVDA
- AMD
- AAPL
- MSFT
- EVO

## Data provider architecture

Sprint 9 introduces `atlas.providers` as the data boundary for company analysis.
Engines depend on the `CompanyDataProvider` interface instead of concrete mock
data, so future live providers can be injected without changing business logic.

Available providers:

- `MockCompanyAnalysisProvider`: deterministic default provider used by the CLI
  and tests.
- `YahooFinanceProvider`: skeleton for future Yahoo Finance mapping. It exposes
  the same interface and raises `NotImplementedError` until live data mapping is
  implemented.

Provider methods:

- `get_company_analysis(ticker)` returns analysis signals for the investment,
  comparison, watchlist, and memory engines.
- `get_portfolio_profile(ticker)` returns portfolio context signals for the
  portfolio engine.

## Portfolio intelligence

```bash
atlas portfolio analyze portfolio.json NVDA
```

Sprint 5 adds deterministic portfolio intelligence. Atlas evaluates a target
company in the context of existing holdings and reports:

- Portfolio Recommendation
- Diversification Impact
- Portfolio Risk Impact
- Portfolio Quality Impact
- Overlap Analysis
- Final Reasoning

Portfolio JSON uses a `positions` list:

```json
{
  "positions": [
    {
      "ticker": "AAPL",
      "company": "Apple",
      "sector": "Consumer Electronics",
      "country": "United States",
      "market_cap": 3000000000000,
      "weight": 0.25,
      "quality_score": 86,
      "risk_score": 72
    }
  ]
}
```

## Company comparison

```bash
atlas compare NVDA AMD MSFT
```

Sprint 6 adds deterministic company comparison. Atlas evaluates each company
with the existing `AtlasInvestmentEngine`, compares Atlas Score, recommendation,
confidence, valuation, quality, growth, financial strength, and risk, then ranks:

- Best Overall
- Best Quality
- Best Valuation
- Best Growth
- Lowest Risk

The comparison report ends with a deterministic final conclusion beginning:
`If Atlas could choose only one...`

## Watchlist intelligence

```bash
atlas watchlist analyze watchlist.json
```

Sprint 7 adds deterministic watchlist intelligence. Atlas evaluates every ticker
with the existing `AtlasInvestmentEngine`, ranks current opportunities, and
identifies:

- strongest opportunity
- highest quality company
- cheapest valuation
- highest risk company
- companies to watch
- companies to avoid

Watchlist JSON uses a name and ticker list:

```json
{
  "name": "AI Watchlist",
  "tickers": ["NVDA", "AMD", "MSFT", "AAPL"]
}
```

## Memory engine

```bash
atlas memory save NVDA memory.json
atlas memory show memory.json
atlas memory compare memory.json NVDA
```

Sprint 8 adds JSON-backed memory. Atlas can save previous analyses, load saved
entries, and compare the two latest entries for a ticker. Memory entries store:

- ticker
- timestamp
- Atlas Score
- recommendation
- confidence
- category scores
- explanation summary

Memory comparison reports score change, recommendation change, confidence
change, strongest improving category, weakest category, and a deterministic
explanation of what changed.

## Install locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
atlas init
```

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
- AAPL
- MSFT
- EVO

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

## Install locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
atlas init
```

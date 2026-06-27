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
atlas analyze NVDA --provider yahoo
atlas ask "Analyze Nvidia"
atlas ask "How healthy is the market?"
atlas intelligence analyze NVDA
atlas intelligence analyze portfolio.json NVDA
atlas portfolio analyze portfolio.json NVDA
atlas compare NVDA AMD MSFT
atlas watchlist analyze watchlist.json
atlas memory save NVDA memory.json
atlas memory show memory.json
atlas memory compare memory.json NVDA
atlas market analyze market.json
atlas market health
atlas risk size risk_input.json
atlas theme analyze "AI infrastructure"
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
- `YahooFinanceProvider`: first real market-data provider. It retrieves Yahoo
  Finance quote-summary data and adapts it to the existing provider interface.

Provider methods:

- `get_company_analysis(ticker)` returns analysis signals for the investment,
  comparison, watchlist, and memory engines.
- `get_portfolio_profile(ticker)` returns portfolio context signals for the
  portfolio engine.
- `get_company(ticker)` returns raw company identity fields from Yahoo.
- `get_financials(ticker)` returns raw financial fields from Yahoo.
- `get_market_data(ticker)` returns raw price and market fields from Yahoo.

Provider selection:

```bash
atlas analyze NVDA --provider mock
atlas analyze NVDA --provider yahoo
atlas compare NVDA AMD MSFT --provider yahoo
atlas portfolio analyze portfolio.json NVDA --provider yahoo
atlas watchlist analyze watchlist.json --provider yahoo
```

The default is always `mock`, so tests and offline workflows remain
deterministic. Yahoo requires internet access and can fail when Yahoo Finance is
unavailable, rate limited, missing fields, or unable to resolve a ticker. Atlas
reports those provider failures as user-facing command errors instead of
crashing. No extra Python package is required for Yahoo support; Atlas uses the
standard library HTTP client.

Yahoo-supported fields:

- Company name
- Exchange
- Sector
- Industry
- Market Cap
- Current Price
- 52-week High
- 52-week Low
- P/E
- EPS
- Revenue
- Gross Margin
- Operating Margin
- Net Margin
- Free Cash Flow
- Shares Outstanding
- Beta
- Dividend Yield, when available

Limitations:

- Yahoo mapping is best-effort and depends on fields Yahoo returns for a ticker.
- Missing fields lower the quality of derived provider-side estimates.
- Yahoo-specific parsing remains isolated inside `atlas.providers`.
- Analysis, portfolio, comparison, watchlist, decision, and risk engines continue
  to depend only on the provider abstraction.

## Conversation engine

```bash
atlas ask "Analyze Nvidia"
atlas ask "Review my portfolio" --portfolio portfolio.json --ticker NVDA
atlas ask "What is the next bottleneck in AI?"
atlas ask "How healthy is the market?"
```

Sprint 16 adds `atlas.conversation`, a deterministic routing layer for natural
investment questions. It is not an LLM. The `IntentClassifier` maps questions to
known Atlas intents, and `ConversationEngine` calls the existing engines rather
than duplicating business logic.

Initial supported intents:

- Company Analysis
- Portfolio Review
- Watchlist Review
- Theme Research
- Market Health
- Market Regime
- Risk Assessment
- General Investment Guidance

Conversation responses include:

- Short Answer
- Supporting Reasoning
- Engines Used
- Confidence
- Suggested Follow-up Questions

The engine recognizes questions such as `Analyze Nvidia`, `Review my portfolio`,
`What is the next bottleneck in AI?`, `How healthy is the market?`, `What should
I monitor?`, `How risky is this company?`, and `What themes are attractive?`.
Outputs are deterministic research context, not personalized financial advice.
The architecture is intentionally ready for future GPT integration while keeping
the current router and reasoning layer testable offline.

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

## Market regime engine

```bash
atlas market analyze market.json
```

The Market Regime Engine classifies the current market environment so Atlas can
adapt future decision, portfolio, and watchlist reasoning to broader conditions.
It is deterministic, uses no external APIs, and currently accepts manually
provided or mock indicators.

Supported regimes:

- Bull
- Neutral
- Correction
- Bear
- Crisis

Market JSON can be flat or nested under `indicators`:

```json
{
  "as_of": "2026-06-27",
  "source": "manual",
  "indicators": {
    "sp500_drawdown": 12,
    "nasdaq_drawdown": 16,
    "vix": 26,
    "interest_rate_trend": "stable",
    "inflation_trend": "stable"
  }
}
```

The report includes the current market regime, confidence, key indicators,
opportunities, risks, and suggested investment behaviour. Crisis behaviour
emphasizes preserving liquidity, avoiding panic selling, investing slowly over
time, and focusing only on financially strong businesses.

## Market health

```bash
atlas market health
```

Sprint 14 adds deterministic Market Health analysis. Atlas evaluates multiple
signal groups to help users understand whether the market environment looks
healthy, fragile, stressed, or improving. This is market context, not investment
advice or a prediction engine.

Signal groups:

- Credit
- Liquidity
- Macro
- Volatility
- Market Breadth

Each group includes status, score, key signals, interpretation, what Atlas is
monitoring, what would improve the signal, and what would worsen the signal.
Credit conditions include deterministic placeholders for high yield spreads,
investment grade spreads, default rates, and bank lending standards.

The report includes overall market health, overall risk level, credit
conditions, liquidity conditions, macro conditions, volatility, market breadth,
Atlas' view, and what could change Atlas' view. The module is designed so future
providers such as FRED, Yahoo, Reuters, or other data sources can supply live
inputs later without changing the public analysis surface.

## Risk and position sizing

```bash
atlas risk size risk_input.json
```

Sprint 11 adds deterministic position sizing and capital deployment reasoning.
The Risk Engine evaluates cash reserves, investment horizon, risk profile, market
regime, existing positions, company score, confidence, and target risk score.

Risk profiles:

- Conservative
- Balanced
- Growth
- Aggressive

Example JSON:

```json
{
  "total_capital": 500000,
  "investable_capital": 200000,
  "existing_cash_reserve": 100000,
  "required_cash_reserve": 75000,
  "investment_horizon_years": 10,
  "risk_profile": "balanced",
  "market_regime": "correction",
  "current_positions": [
    {"ticker": "MSFT", "market_value": 80000},
    {"ticker": "NVDA", "market_value": 60000}
  ],
  "target_ticker": "TSMC",
  "target_company_score": 86,
  "target_confidence": 82,
  "target_risk_score": 35
}
```

The report includes risk profile, investable capital, cash reserve status,
suggested initial investment, suggested monthly deployment, deployment period,
maximum position size, concentration risk, liquidity risk, market regime
adjustment, final recommendation, and reasoning.

The engine never recommends investing money needed in the short term, never
deploys capital below the required cash reserve, favors gradual deployment in
Correction, Bear, and Crisis regimes, and caps single-position exposure by risk
profile. Lower confidence or a weaker target risk score reduces recommended
position size.

## Theme intelligence

```bash
atlas theme analyze "AI infrastructure"
```

Sprint 13 adds deterministic theme intelligence. Atlas analyzes investment
themes as research maps rather than stock-picking recommendations. The engine
identifies likely bottlenecks, affected industries, potential beneficiaries,
related equities, ETFs, commodities where relevant, second-order winners, risks,
monitoring items, confidence, and what would change Atlas' view.

Supported theme templates:

- AI infrastructure
- Energy transition
- Electrification
- Semiconductors
- Healthcare innovation

AI infrastructure explicitly tracks bottlenecks such as electricity supply, grid
capacity, data center construction, cooling, transformers, HBM memory, and
advanced packaging. Theme outputs are research directions only and are not
personalized financial recommendations or buy/sell advice.

## Atlas intelligence engine

```bash
atlas intelligence analyze NVDA
atlas intelligence analyze portfolio.json NVDA
```

Sprint 15 adds `atlas.intelligence`, the first deterministic orchestration layer
that combines multiple Atlas engines into one coherent reasoning process. It is
not an LLM and does not make trade instructions. It explains confidence,
uncertainty, structural context, market context, company positioning, portfolio
impact, and risks.

The Intelligence Engine can synthesize:

- Company Analysis
- Portfolio Analysis
- Watchlist Analysis
- Risk Engine output
- Decision Engine output
- Theme Engine output
- Market Regime
- Market Health

The report includes:

- Executive Summary
- Structural Tailwinds
- Current Market Environment
- Company Positioning
- Portfolio Impact
- Risk Assessment
- Atlas Conclusion
- What Atlas Is Monitoring
- What Could Change Atlas' View

The CLI uses deterministic defaults for theme, market regime, and market health
unless additional context is supplied. Portfolio-aware synthesis is available by
passing `portfolio.json` before the ticker. The engine is structured so future
LLM augmentation or live data providers can enrich specific report sections
without replacing the deterministic orchestration layer.

## Decision engine

Sprint 10 adds `atlas.decision`, the central deterministic reasoning layer that
orchestrates the existing Atlas subsystems without replacing them:

- Investment Engine
- Portfolio Engine
- Comparison Engine
- Watchlist Engine
- Memory Engine

`DecisionContext` captures market regime, optional portfolio, optional watchlist,
optional historical memory, investment horizon, risk profile, available capital,
cash reserve status, and optional comparison tickers.

`AtlasDecisionEngine` produces a `DecisionResult` with:

- Buy, Hold, Reduce, Avoid, Watch, or Learn More
- Decision Quality
- Portfolio Fit
- Capital Allocation Quality
- Confidence
- Reasoning
- Next Best Action
- What Could Change My Mind
- Uncertainty

The decision layer is deterministic, makes no external API calls, and uses no
LLM. It always explains uncertainty, blocks buy decisions when capital may be
needed in the short term, and explicitly discusses concentration risk when
portfolio context is available. It does not provide personal financial advice or
guarantee outcomes.

## Install locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
atlas init
```

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
atlas dashboard show
atlas daily brief
atlas report NVDA
atlas analyze NVDA --provider yahoo
atlas economics analyze
atlas ask "Analyze Nvidia"
atlas ask "How healthy is the market?"
atlas intelligence analyze NVDA
atlas intelligence analyze portfolio.json NVDA
atlas language explain
atlas monitor NVDA
atlas monitor portfolio.json
atlas monitor theme "AI infrastructure"
atlas profile create
atlas profile show
atlas profile update --risk-profile Growth
atlas principles check "text to check"
atlas reason analyze
atlas portfolio analyze portfolio.json NVDA
atlas portfolio review portfolio.json
atlas compare NVDA AMD MSFT
atlas watchlist analyze watchlist.json
atlas memory save NVDA memory.json
atlas memory show memory.json
atlas memory compare memory.json NVDA
atlas market analyze market.json
atlas market health
atlas risk size risk_input.json
atlas risk-drift analyze
atlas suitability analyze NVDA
atlas suitability analyze portfolio.json
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

## Atlas home dashboard

```bash
atlas dashboard show
atlas dashboard show --portfolio portfolio.json
atlas dashboard show --profile atlas_profile.json --portfolio portfolio.json
```

Sprint 24 adds `atlas.dashboard`, the first user-facing Atlas home briefing.
The dashboard is designed to feel like Atlas has already reviewed the current
context before the user asks a question. It is not a collection of disconnected
widgets and it does not create buy or sell recommendations.

The Home Dashboard aggregates existing engines only:

- Investor Profile Engine
- Portfolio and Monitoring engines
- Suitability Engine
- Risk Drift Engine
- Theme Engine
- Market Regime
- Market Health
- Economic Signals
- Principles Engine

Dashboard output includes:

- Welcome
- Portfolio Overview
- Market Overview
- Themes To Watch
- Today's Observations
- Atlas Is Monitoring
- Suggested Questions

The dashboard uses deterministic language such as `Worth monitoring`, `Worth
understanding`, `Appears stable`, and `May deserve attention`. CLI output is a
clean text briefing designed so future UI rendering can reuse the same structured
`DashboardSummary`, `DashboardSection`, and `DashboardCard` objects.

## Atlas Daily Brief

```bash
atlas daily brief
atlas daily brief --portfolio portfolio.json
atlas daily brief --profile atlas_profile.json --portfolio portfolio.json
```

Sprint 25 adds `atlas.daily`, a calm deterministic daily briefing experience.
Atlas Daily is not a news feed and does not provide buy or sell recommendations.
It summarizes what matters today for the investor using existing Atlas engines.

The Daily Brief aggregates:

- Dashboard Engine
- Investor Profile Engine
- Portfolio and Monitoring engines
- Suitability Engine
- Risk Drift Engine
- Theme Engine
- Market Health
- Market Regime
- Economic Signals
- Principles Engine

Daily Brief output includes:

- Opening Summary
- What Changed
- Portfolio Notes
- Market Notes
- Themes To Watch
- Risks To Watch
- Opportunities To Study
- Suggested Questions

The tone is calm, concise, analytical, and not promotional. Atlas Daily uses
language such as `worth monitoring`, `worth understanding`, `appears stable`,
`may deserve attention`, `not enough information`, and `depends on investor
profile`. Opportunities are presented as research directions only.

## Portfolio review engine

```bash
atlas portfolio review portfolio.json
atlas portfolio review portfolio.json --profile atlas_profile.json
atlas portfolio review portfolio.json --market market.json
```

Sprint 26 adds `atlas.portfolio_review`, a CIO-style portfolio review. This is
not a performance report and not a trade recommendation. It synthesizes investor
profile, portfolio structure, suitability, risk drift, market conditions,
economic signals, and long-term themes into a concise alignment review.

The review uses existing Atlas engines:

- Portfolio and Monitoring engines
- Investor Profile Engine
- Suitability Engine
- Risk Drift Engine
- Theme Engine
- Market Health
- Market Regime
- Economic Signals
- Principles Engine

Output sections:

- Bottom Line
- Atlas Rating
- Portfolio Strengths
- Main Risks
- Investor Alignment
- Theme Exposure
- Market Context
- What Atlas Is Monitoring
- What Could Change Atlas' View
- Missing Information
- Optional Follow-up Questions

Atlas Rating reflects alignment between the portfolio, investor profile, market
context, and risk profile. It is not a performance rating. Possible ratings are
Excellent Alignment, Strong Alignment, Balanced, Limited Alignment, and
Misaligned.

## Atlas language and rating system

```bash
atlas language explain
```

Sprint 27 adds `atlas.language`, a reusable language and rating layer for
standardizing how Atlas explains ratings, views, fit, confidence, thesis,
rationale, bottom lines, and what could change Atlas' view. It is not a trade
rating system and does not replace existing analysis engines.

The language layer defines:

- `AtlasRating` for explainable contextual assessments such as Strong Alignment,
  Balanced, Constructive, Cautious, or Unclear
- `AtlasView` for directional but non-instructional views such as Constructive,
  Balanced, Improving, Weakening, or Unclear
- `AtlasFit` for profile or portfolio compatibility such as Excellent Fit,
  Strong Fit, Moderate Fit, Limited Fit, or Poor Fit
- `AtlasConfidence` for confidence level, drivers, uncertainty, and missing
  information
- `AtlasThesis` for current thesis, evidence, counter arguments, monitoring
  items, and what could change Atlas' view
- `AtlasRationale` for bottom line, key reasons, main risk, and material
  follow-up questions
- `AtlasLanguageReport` for progressive transparency across Bottom Line,
  Reasoning, and Full Reasoning

Guardrails flag or avoid directive and absolute language such as `Strong Buy`,
`Strong Sell`, `Guaranteed`, `Risk-free`, `Can't lose`, and `Sure thing`.
Preferred language includes `appears aligned`, `worth monitoring`, `may deserve
attention`, `current evidence suggests`, and `not enough information for a
high-confidence assessment`.

Portfolio Review now attaches a structured `AtlasLanguageReport` as an example
integration point while keeping the existing review output unchanged.

The review uses language such as `appears aligned`, `worth monitoring`, `may
deserve attention`, and `current evidence suggests`. It avoids trade
instructions and absolute promises.

## Investor profile engine

```bash
atlas profile create
atlas profile show
atlas profile update --risk-profile Growth --time-horizon "10+ years"
```

Sprint 20 adds `atlas.profile`, a deterministic investor context layer. It does
not provide investment recommendations and is not a financial advisor. The
profile exists so future Atlas reasoning can account for the user's goals,
portfolio purpose, risk preferences, risk capacity, and time horizon before
evaluating portfolio fit.

The profile supports:

- investment goals: wealth accumulation, retirement, income, financial
  independence, capital preservation, learning, and experimental portfolio
- portfolio purpose: core portfolio, growth portfolio, income portfolio,
  exploration portfolio, and high conviction portfolio
- risk profile: conservative, balanced, growth, and aggressive
- risk capacity: low, medium, and high
- time horizon: `<3 years`, `3-10 years`, and `10+ years`

Profile commands read and write `atlas_profile.json` by default. Use `--path` to
store a profile elsewhere:

```bash
atlas profile create --path profiles/core.json --goal Retirement --risk-profile Balanced
atlas profile show --path profiles/core.json
atlas profile update --path profiles/core.json --risk-capacity High
```

`InvestorProfileEngine` produces an `InvestorContext` with capital safety
framing and deterministic reasoning context. The context is designed for future
onboarding UI and later integration into portfolio, risk, decision, and
intelligence workflows.

## Atlas principles engine

```bash
atlas principles check "This depends on the investor profile and risk context."
```

Sprint 23 adds `atlas.principles`, a deterministic validation layer for Atlas
communication and product philosophy. It is not an LLM, not a recommendation
engine, and does not replace existing engines. It checks whether text or rendered
reports follow Atlas' reasoning guardrails.

Initial principle categories:

- User First
- Context Before Conclusion
- Portfolio Before Position
- Risk Before Return
- Transparency
- Suitability
- Long-term Thinking
- Humility
- Educational Value
- Consistency

The engine outputs:

- Overall Principles Result: Pass, Warning, or Fail
- principles followed
- principles potentially missing
- guardrail warnings
- missing context
- suggested improvements
- confidence

Guardrails flag directive or absolute language such as `Buy`, `Sell`, `Strong
Buy`, `Strong Sell`, `Guaranteed`, `Can't lose`, `Risk-free`, and `Sure thing`
unless the phrase is clearly quoted as external text. Atlas should prefer
language such as `appears compatible`, `appears inconsistent`, `may be worth
studying`, `Atlas would monitor`, `there is not enough information`, and `this
depends on the investor profile`.

The package also exposes optional helper functions for validating conversation
responses, intelligence reports, suitability assessments, and reasoning reports
without changing those engines' business logic.

## Suitability engine

```bash
atlas suitability analyze NVDA
atlas suitability analyze portfolio.json
atlas suitability analyze NVDA --profile profiles/core.json
```

Sprint 21 adds `atlas.suitability`, a deterministic profile compatibility
engine. It is not a recommendation engine and does not decide whether an
investment is good or bad. It evaluates whether an investment or portfolio
appears compatible with the stated investor profile, objectives, risk context,
and portfolio purpose.

The engine evaluates investor context from `InvestorProfile`:

- investment goals
- portfolio purpose
- time horizon
- risk tolerance
- risk capacity
- preferred investment style, when explicitly supplied or inferred

It evaluates investment and portfolio characteristics:

- volatility
- business quality
- valuation sensitivity
- concentration impact
- cyclicality
- leverage
- sector exposure
- geographic exposure

Suitability output includes:

- Overall Suitability: Excellent Fit, Good Fit, Neutral, or Poor Fit
- why it fits
- why it may not fit
- main strengths
- main concerns
- assumptions
- missing information
- questions Atlas would ask before increasing confidence

The engine recognizes that higher-risk opportunities may be compatible with an
Exploration Portfolio or High Conviction Portfolio when the investor has high
risk capacity, a long time horizon, and accepts volatility. It also recognizes
that high-quality opportunities may still be unsuitable when they conflict with
the investor's time horizon, risk tolerance, or portfolio purpose.

The CLI uses `atlas_profile.json` by default when present and otherwise falls
back to Atlas' default deterministic profile. Use `--profile` to provide a
specific profile file. Ticker analysis combines company analysis, theme context,
and intelligence synthesis. Portfolio JSON analysis evaluates the portfolio's
own quality, risk, concentration, sector, and geographic exposure.

## Economic signals engine

```bash
atlas economics analyze
```

Sprint 18 adds `atlas.economics`, a deterministic macro and financial conditions
engine. It evaluates multiple economic signal groups rather than relying on a
single market classification. There are no live APIs yet, no forecasting, and no
buy/sell advice.

Signal groups:

- Credit Markets: high yield spreads, investment grade spreads, default rates,
  and bank lending standards
- Liquidity: central bank balance sheets, money supply, repo stress, and dollar
  liquidity
- Interest Rates: yield curve, real rates, and policy rate trend
- Volatility: VIX, MOVE Index, and cross-asset volatility
- Macro: PMI, unemployment trend, inflation trend, and GDP trend
- Market Breadth: advance/decline, new highs versus lows, and sector
  participation

Each signal includes name, current state, direction, importance, confidence, why
it matters, and a deterministic score. The report includes overall economic
health, overall risk score, strongest positive and negative signals, what Atlas
is watching most closely, and what would improve or worsen the outlook.

The module is structured so future FRED, ECB, Yahoo, or other macro data
providers can supply live inputs without changing the public analysis surface.

## Atlas reasoning engine

```bash
atlas reason analyze
atlas reason analyze --ticker NVDA --theme "AI infrastructure"
```

Sprint 19 adds `atlas.reasoning`, a deterministic thesis synthesis layer. It
does not call an LLM, does not use live APIs, does not invent missing facts, and
does not produce buy/sell recommendations. It only synthesizes outputs supplied
by existing Atlas engines.

Reasoning input can include:

- Company Analysis
- Portfolio Analysis
- Theme Analysis
- Monitoring Report
- Economic Signals
- Market Health
- Market Regime
- Risk Analysis

The report includes:

- Executive Summary
- Bullish Factors
- Bearish Factors
- Areas of Uncertainty
- Signals Atlas Trusts Most
- Signals Atlas Trusts Least
- Confidence
- Alternative Scenarios
- What Could Invalidate The Thesis
- What Atlas Will Monitor Next

The default CLI path builds a deterministic thesis from the mock company
provider, theme analysis, monitoring, economic signals, market health, and market
regime. Missing inputs are listed as uncertainty rather than inferred.

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

## Monitoring engine

```bash
atlas monitor NVDA
atlas monitor portfolio.json
atlas monitor theme "AI infrastructure"
atlas monitor watchlist watchlist.json
atlas monitor market-health
atlas monitor market-regime
```

Sprint 17 adds `atlas.monitoring`, a deterministic snapshot comparison layer.
Atlas creates typed monitoring snapshots, compares a previous snapshot with a
current snapshot, and explains what changed. There are no notifications, no
database requirements, and no live scheduling yet.

Atlas can monitor:

- Companies
- Themes
- Market Health
- Market Regime
- Credit indicators through Market Health
- Portfolio snapshots
- Watchlists

Monitoring output includes:

- Summary
- Signals that improved
- Signals that deteriorated
- New risks
- New opportunities
- Confidence
- Importance score
- Atlas recommends monitoring

The CLI currently generates a deterministic previous baseline so monitoring can
be tested offline without storage. The architecture keeps snapshots explicit so
future scheduled monitoring, persisted history, and notifications can be added
without changing the comparison model.

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

## Risk drift engine

```bash
atlas risk-drift analyze
atlas risk-drift analyze --portfolio portfolio.json
atlas risk-drift analyze --original-profile old_profile.json --current-profile atlas_profile.json
```

Sprint 22 adds `atlas.risk_drift`, a deterministic review engine that detects
when the current investor situation, portfolio, or market environment may have
drifted away from the assumptions in the original investor profile.

This is not a recommendation engine. It does not tell the user to buy or sell.
It identifies meaningful changes and asks whether the investor profile,
portfolio purpose, or risk assumptions should be reviewed.

The engine compares:

- original investor profile and current investor profile
- optional current portfolio context
- optional market regime
- optional market health
- optional economic signals
- optional suitability assessment

Risk drift signals include:

- risk tolerance drift
- risk capacity drift
- time horizon drift
- portfolio purpose drift
- portfolio size growth
- position concentration
- market regime stress
- market health stress
- economic risk environment
- volatility exposure

Output includes:

- Overall Drift Level: None, Low, Moderate, or High
- Drift Summary
- Signals Detected
- What Changed
- Why It Matters
- Triggers
- Questions Atlas Should Ask
- Suggested Profile Review Areas
- Confidence
- Missing Information

The engine recognizes that an aggressive portfolio may still show low drift when
the investor has high risk capacity, a long time horizon, and explicitly accepts
volatility. It also flags cases where a once-small exploration portfolio has
grown materially, concentration has risen, or the market backdrop has shifted
from calm conditions into correction or crisis.

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

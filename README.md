# Atlas

Private investment research platform for AI infrastructure.

## Version
v0.1.0 — Foundation

## Project Philosophy

Atlas is guided by a small set of permanent product documents:

- [Atlas Constitution](docs/ATLAS_CONSTITUTION.md)
- [Atlas Product](docs/ATLAS_PRODUCT.md)
- [Atlas Architecture](docs/ATLAS_ARCHITECTURE.md)
- [Atlas Roadmap](docs/ATLAS_ROADMAP.md)

Sprint 36 adds the Atlas foundation documents:

- [Architecture](docs/Architecture.md)
- [Project Structure](docs/ProjectStructure.md)
- [Decision Log](docs/DecisionLog.md)
- [Development Guide](docs/DevelopmentGuide.md)

## Atlas Foundation

The repository is organized around clear long-term boundaries:

- `atlas/shared/` contains canonical entities such as `Portfolio`, `Holding`,
  `Company`, `Watchlist`, `ResearchNote`, `JournalEntry`, `User`,
  `MarketEvent`, `Decision`, and `KnowledgeNode`.
- `atlas/domains/` defines ownership boundaries for portfolio, watchlist,
  research, decision journal, daily brief, knowledge, AI, and authentication.
- `atlas/ai/` defines replaceable AI service interfaces for future reasoning,
  knowledge, summary, discovery, and decision support services.
- `frontend/`, `backend/`, `shared/`, `ai_services/`, and `infrastructure/`
  reserve clear repository areas for future Atlas platform development.

The existing Python backend and CLI remain the working product. Sprint 36 adds
architecture, documentation, strict TypeScript configuration for future frontend
work, CI, and local hook configuration without changing user-facing behavior.

## Portfolio Domain

Sprint 37 adds the first real Atlas product domain:
`atlas.domains.portfolio`.

The Portfolio domain is documented in
[Portfolio Domain](docs/PortfolioDomain.md). It provides deterministic,
non-advisory portfolio understanding:

- total portfolio value
- holding market value
- holding portfolio weight
- sector allocation
- country allocation
- top holdings
- concentration level
- cash weight
- largest position
- number of holdings
- structured validation issues
- calm portfolio observations

This domain does not create trade recommendations, forecasts, external market
data integrations, persistence, UI, or AI-generated analysis.

## Decision Engine Foundation

Sprint 38 adds the Atlas Decision domain:
`atlas.domains.decision`.

The Decision domain is documented in
[Decision Engine Foundation](docs/DecisionEngine.md). It transforms structured
evidence into structured reasoning:

- evidence
- observations
- reasoning steps
- unknowns
- confidence
- decision result
- decision card

This foundation does not generate trade recommendations, predictions, external
market data, AI calls, or portfolio instructions. It exists to make future Atlas
reasoning explainable and traceable.

## Knowledge Domain

Sprint 39 adds the Atlas Knowledge domain:
`atlas.domains.knowledge`.

The Knowledge domain is documented in
[Knowledge Domain](docs/KnowledgeDomain.md). It provides deterministic,
provider-independent structures for:

- knowledge nodes
- knowledge edges
- attributed facts
- sources
- evidence references
- relationship creation
- simple deterministic queries

Knowledge stores facts and explicit relationships. It does not generate
opinions, use embeddings, call LLMs, or implement a graph database.

## Research Domain

Sprint 40 adds the Atlas Research domain:
`atlas.domains.research`.

The Research domain is documented in
[Research Domain](docs/ResearchDomain.md). It provides deterministic structures
for:

- research projects
- research notes
- research questions
- assumptions
- thesis fragments
- evidence references
- research summaries
- validation

Research organizes curiosity into structured understanding. It does not create
recommendations, forecasts, discovery feeds, market data integrations, or
AI-generated analysis.

## Company Analysis Capability

Sprint 41 adds the Atlas Company Analysis capability:
`atlas.capabilities.company_analysis`.

The capability is documented in
[Company Analysis Capability](docs/CompanyAnalysis.md). It consumes existing
domain structures from Knowledge, Research, and Decision to generate a calm,
deterministic, non-advisory company analysis report.

Reports include:

- Business Overview
- What Matters
- Supporting Evidence
- Key Risks
- Open Questions
- Research Context
- Knowledge Context
- Decision Context
- Confidence
- What Could Change the View

Company Analysis helps investors understand businesses. It does not create
trade recommendations, forecasts, price targets, external API calls, or
AI-generated analysis.

## MVP commands

```bash
atlas init
atlas add-company TSM --name "Taiwan Semiconductor Manufacturing Company" --atlas-id AI-001 --exchange NYSE --country Taiwan --currency USD --sector Semiconductors --industry Foundry
atlas import-financials TSM data/tsm_financials.csv
atlas list-companies
atlas home
atlas dashboard show
atlas daily brief
atlas journal create
atlas journal list
atlas journal review
atlas report NVDA
atlas analyze NVDA --provider yahoo
atlas economics analyze
atlas evidence assess
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
atlas compare
atlas watchlist analyze watchlist.json
atlas watchlist review watchlist.json
atlas watchlist review
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

## Atlas Home

```bash
atlas home
atlas home --portfolio portfolio.json --watchlist watchlist.json
atlas home --profile atlas_profile.json --journal .atlas/decision_journal.json
```

Sprint 32 adds `atlas.home`, the primary entry point to Atlas. Atlas Home is a
one-screen briefing designed to answer one question: what does the investor need
to understand right now?

It orchestrates existing engines rather than introducing new investment logic:

- Investor Profile Engine
- Portfolio Review Engine
- Watchlist Review Engine
- Market Health Engine
- Market Regime Engine
- Economic Signals Engine
- Decision Journal Engine
- Atlas Language Engine

The Home output includes a bottom line, Atlas Rating, up to three priorities,
portfolio health, market context, watchlist highlights, decision journal
reminders, up to five monitoring items, and meaningful changes since the last
review. If nothing meaningful changed, Atlas says so rather than inventing
updates.

This feature follows the [Atlas Constitution](docs/ATLAS_CONSTITUTION.md):
evidence before opinion, context before conclusion, calm before clever, and
progressive transparency.

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

Sprint 33 adds `atlas.daily_brief`, a reusable calm briefing layer for Atlas
Home, the CLI, and future UI surfaces. Atlas Daily is not a news feed, market
prediction, or recommendation engine. It summarizes what changed, why it
matters, and whether anything deserves attention.

The Daily Brief aggregates:

- Atlas Home Engine
- Investor Profile Engine
- Portfolio Review Engine
- Watchlist Review Engine
- Market Health
- Market Regime
- Economic Signals
- Evidence Quality Engine
- Atlas Language Engine
- Decision Journal Engine
- Monitoring Engine

Daily Brief output includes:

- Bottom Line
- What Changed
- Why It Matters
- Portfolio Context
- Watchlist Context
- Market Context
- Today's Priorities
- What Atlas Is Monitoring
- What Could Change This View
- Full Reasoning

Quiet days are handled explicitly. If nothing meaningful changed, Atlas says
`No meaningful changes since your last review.` and may show one informational
priority: `No immediate action appears necessary.`

The tone is calm, concise, analytical, and not promotional. Atlas Daily follows
the [Atlas Constitution](docs/ATLAS_CONSTITUTION.md) by using evidence before
opinion, context before conclusion, and progressive transparency.

## Decision journal engine

```bash
atlas journal create
atlas journal list
atlas journal review
```

Sprint 31 adds `atlas.decision_journal`, a deterministic decision reasoning
journal. The journal does not track trades and does not create recommendations.
Its purpose is to preserve the thesis, context, assumptions, risks, evidence
quality, Atlas assessment, and review triggers at the time a decision was being
considered.

Each `DecisionJournalEntry` captures:

- decision title
- asset or idea
- decision type: considering, entered, exited, reviewed, or passed
- decision date
- investor profile context
- portfolio context summary
- Atlas Rating, Atlas View, Atlas Fit, and Atlas Confidence at the time
- investment thesis
- supporting reasons
- main risks
- evidence quality
- assumptions
- what could change Atlas' view
- monitoring plan
- planned review date
- optional user notes
- lessons learned

The CLI uses a simple local JSON file by default:

```text
.atlas/decision_journal.json
```

Use `--path` to point the commands at another file during testing or local
experimentation. `atlas journal create` writes a deterministic example entry,
`atlas journal list` shows saved entries, and `atlas journal review` reviews the
latest saved entry or a deterministic demo entry when no file exists.

The review separates decision quality from outcome quality. A good decision can
have an unfavorable outcome, and a poor decision can have a favorable outcome.
Atlas preserves reasoning so the investor can learn without shame or hindsight
bias.

## Atlas Memory and Timeline

Sprint 34 adds `atlas.memory`, the historical reasoning foundation for future
Atlas engines.

This package is infrastructure only. It does not add CLI commands or
user-facing behavior.

The snapshot architecture provides immutable records for:

- `PortfolioSnapshot`
- `WatchlistSnapshot`
- `DailyBriefSnapshot`

Every snapshot contains:

- `timestamp`
- `source_version`
- `metadata`
- `payload`

The `MemoryStore` abstraction defines the storage contract:

- `save(snapshot)`
- `latest()`
- `get(timestamp)`
- `list()`
- `exists(timestamp)`

`InMemoryMemoryStore` is the first implementation and is intended for tests and
early orchestration. It has no persistence. Storage is abstracted so later
implementations can use SQLite, PostgreSQL, or another durable backend without
changing timeline consumers.

`Timeline` provides deterministic historical comparison:

- latest snapshot
- snapshot at a timestamp
- changes since the previous snapshot
- comparison between two snapshots

Initial comparisons report added, removed, and modified payload items. No AI
reasoning is included in this layer.

## Historical Change Engine

Sprint 35 adds `atlas.history`, the first reusable engine built on top of Atlas
Memory snapshots.

This package is infrastructure only. It does not add CLI commands or connect to
Atlas Home or Daily Brief yet.

The comparison pipeline is:

1. Store immutable snapshots in a `MemoryStore`.
2. Load the previous and latest snapshots.
3. Compare portfolio and watchlist structures.
4. Return deterministic `HistoricalChange` objects.

`HistoricalChangeEngine` exposes:

- `compare(previous, current)`
- `compare_latest()`

The engine currently detects:

- added portfolio positions
- removed portfolio positions
- portfolio weight changes
- watchlist additions
- watchlist removals
- significant quality score changes
- significant risk score changes

The output is structured and deterministic. It contains change type, subject,
previous value, current value, and severity. It does not generate explanations,
recommendations, or AI summaries.

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

## Evidence quality engine

```bash
atlas evidence assess
```

Sprint 28 adds `atlas.evidence`, a deterministic evidence quality layer. Atlas
should not treat all information equally: audited reports, regulatory filings,
exchange data, screenshots, social posts, forum claims, and user statements carry
different evidentiary weight.

The Evidence Quality Engine classifies structured inputs only. It does not
browse the web, call live APIs, use LLMs, or independently verify external
facts. Its job is to explain whether a claim is strong enough to affect Atlas
Confidence, Atlas View, missing information, what could change Atlas' view, or
the full reasoning trail.

Supported source categories include:

- audited annual report
- quarterly report
- company press release
- regulatory filing
- exchange data
- government / central bank data
- reputable financial news
- analyst report
- investor presentation
- social media post
- forum post
- TikTok / short-form video
- screenshot without source
- user statement
- unknown source

Evidence strength is classified as Very Strong, Strong, Moderate, Weak, Very
Weak, Unverified, or Insufficient. Atlas then chooses an evidence action such as
Update assessment, Reduce confidence, Add reservation, Monitor for confirmation,
Request source, Ignore for now, or Insufficient for assessment.

Example behavior:

- A regulatory filing that materially contradicts Atlas' current view can reduce
  confidence and trigger `Update assessment`.
- A screenshot or short-form video claim may be worth investigating, but Atlas
  asks for the original source, dataset, filing, or report before changing its
  view.
- Missing or unknown sources trigger a request for source material.

Every `EvidenceAssessment` includes the claim, source type, evidence strength,
evidence action, rationale, confidence impact, additional data needed, whether
Atlas' view should change, and a light `AtlasLanguageReport` integration.

## Watchlist review engine

```bash
atlas watchlist review watchlist.json
atlas watchlist review
```

Sprint 29 adds `atlas.watchlist_review`, a CIO-style watchlist review designed
to make a watchlist feel actively monitored. This is not a trade instruction
engine. It helps separate ideas that appear relevant from ideas that are noisy,
unclear, duplicated, or not yet supported by strong evidence.

The review uses existing Atlas engines where available:

- Watchlist Engine
- Atlas Language & Rating System
- Evidence Quality Engine
- Theme Engine
- Market Health
- Market Regime
- Economic Signals
- Monitoring Engine
- Suitability Engine
- Investor Profile Engine
- Principles Engine

Output sections include:

- Bottom Line
- Atlas Watchlist Rating
- Most Relevant Ideas
- Ideas Worth Monitoring
- Ideas Requiring Better Evidence
- Potential Noise
- Theme Exposure
- Fit With Investor Profile
- Market Context
- What Atlas Is Monitoring
- What Could Change Atlas' View
- Suggested Questions

Atlas Watchlist Rating reflects how useful, focused, evidence-supported, and
profile-aligned the watchlist appears. Possible ratings are High Quality
Watchlist, Focused Watchlist, Balanced Watchlist, Noisy Watchlist, and Unclear
Watchlist.

The CLI supports demo mode when no file is provided. Existing watchlist JSON
continues to work:

```json
{
  "name": "AI Watchlist",
  "tickers": ["NVDA", "AMD", "MSFT"]
}
```

The review also accepts optional broader research ideas and evidence metadata:

```json
{
  "name": "AI Watchlist",
  "tickers": ["NVDA", "AMD", "MSFT"],
  "ideas": ["AI power bottleneck"],
  "themes": ["AI infrastructure"],
  "evidence": {
    "AI power bottleneck": {
      "source": "social media post",
      "claim": "Social posts claim AI power constraints are worsening."
    }
  }
}
```

When evidence is weak, social-media-driven, or missing, Atlas asks for stronger
source material instead of elevating the idea. Preferred wording includes
`appears relevant`, `appears less supported`, `worth monitoring`, `worth
understanding`, `may deserve attention`, `current evidence suggests`, and `not
enough information for a high-confidence assessment`.

## Investment comparison engine

```bash
atlas compare NVDA MSFT
atlas compare NVDA MSFT "AI infrastructure"
atlas compare
```

Sprint 30 adds `atlas.comparison`, a deterministic Investment Comparison
Engine for comparing two or more companies, themes, ETFs, or investment ideas.
The goal is not to pick a universal winner. Atlas explains meaningful
differences, investor fit, evidence quality, portfolio role, and what could
change the view.

The engine uses existing Atlas layers where appropriate:

- Atlas Language & Rating System
- Evidence Quality Engine
- Investor Profile Engine
- Suitability Engine
- Theme Engine
- Market Health
- Market Regime
- Economic Signals
- Monitoring Engine
- Principles Engine

Output sections include:

- Bottom Line
- Comparison Rating
- Candidate Summaries
- Key Differences
- Investor Fit
- Evidence Quality
- Theme and Market Context
- Portfolio Role
- What Could Change Atlas' View
- Suggested Questions
- Full Reasoning

Comparison Rating is explainable and traceable. Possible ratings include Clearer
Fit, Similar Quality, Higher Uncertainty, Different Roles, Evidence Gap, and
Unclear.

Candidate summaries include Atlas Rating, Atlas View, Atlas Fit, Confidence, key
reasons, main risk, evidence strength, and what Atlas is monitoring. The CLI
also supports deterministic demo mode when no ideas are provided.

The comparison avoids trade instruction language and uses phrases such as
`appears better aligned`, `appears less aligned`, `worth monitoring`, `worth
understanding`, `current evidence suggests`, `not enough information for a
high-confidence assessment`, `depends on portfolio role`, and `serves a
different purpose`.

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

UX-007A — Portfolio Workspace Wireframe Specification

Status: Draft v1.0
Owner: Atlas Product
Depends on: UX-000 — The Atlas Experience, UX-006 — Portfolio Workspace Philosophy, UX-007 — Portfolio Workspace Screen Specification
Primary use: Figma wireframe refinement and interaction prototype
Visual fidelity: Low-fidelity, monochrome, structure-first


1. PURPOSE

This document defines the exact structural wireframe for the Atlas Portfolio Workspace.

It translates the behavioral and information requirements established in UX-007 into a precise layout, hierarchy, component structure, viewport model, interaction pattern, and Figma prototype.

This document specifies:

- section order,
- component placement,
- information density,
- default expansion states,
- viewport priorities,
- interaction behavior,
- links between portfolio-level and position-level reasoning,
- loading, empty, partial-data, and decision states,
- responsive structure,
- required Figma frames and prototype interactions.

This document does not define:

- final colors,
- final typography,
- decorative illustration,
- brand polish,
- final chart aesthetics,
- production animation timing,
- visual effects added only for presentation.

The wireframe must validate the Portfolio Workspace as a coherent reasoning environment before final visual polish begins.


2. GOVERNING QUESTION

The Portfolio Workspace exists to answer:

Is my portfolio positioned the way I want?

The first viewport must allow the user to understand:

- Atlas’ current portfolio conclusion,
- what materially changed,
- whether attention is required,
- whether a portfolio-level decision is required.

The user must not need to scroll before receiving the primary conclusion.

The complete Workspace must allow the user to understand:

- portfolio health,
- portfolio strengths,
- portfolio weaknesses,
- visible and hidden concentration,
- risk dependencies,
- scenario resilience,
- competing uses of capital,
- portfolio evolution,
- the appropriate next decision state.


3. RELATIONSHIP TO THE CURRENT IMPLEMENTATION

The current Portfolio Workspace implementation already establishes the correct core interaction model:

- it opens above the Dashboard,
- the Dashboard remains visible underneath a dimmed layer,
- the Workspace uses an internal vertical scroll,
- the header remains fixed,
- the content follows a conclusion-first hierarchy,
- deep sections use expandable rows and cards,
- individual positions can open related Investment Workspaces.

UX-007A should refine and formalize this implementation rather than replace its central interaction model.

The following existing qualities should be preserved:

- dark, restrained Atlas visual language,
- substantial elevated Workspace panel,
- persistent Dashboard context,
- full-width Atlas Portfolio Conclusion,
- What Changed immediately below the conclusion,
- portfolio health cards,
- dedicated Hidden Concentration section,
- explanatory Risk Dependencies,
- calibrated Scenario Analysis,
- Capital Allocation as a comparative reasoning section,
- Portfolio Evolution as a narrative rather than only a value chart.

The purpose of UX-007A is to improve hierarchy, consistency, density, component behavior, and completion states while preserving the established Atlas experience.


4. DESKTOP FRAME

Use the existing Atlas desktop Dashboard frame.

Reference viewport:

1440 × 1024 px

The Portfolio Workspace opens as an elevated panel above the existing Dashboard.

Structure:

┌──────────────────────────────────────────────────────────────┐
│ Dimmed Atlas Dashboard background                            │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐   │
│   │ Portfolio Workspace                                  │   │
│   │                                                      │   │
│   │ Internal scrollable content                          │   │
│   │                                                      │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Recommended Workspace dimensions:

- width: approximately 1120–1240 px,
- maximum height: viewport minus 32–48 px,
- minimum outer margin: 24 px,
- internal vertical scrolling,
- Dashboard fixed underneath,
- Workspace centered horizontally,
- Workspace should feel substantial without replacing the entire application shell.

Use the same general shell geometry as the Investment Workspace wherever possible.

The Portfolio Workspace and Investment Workspace should feel like members of the same Workspace system.


5. WORKSPACE SHELL

The Workspace contains three structural regions:

1. Pinned Workspace Header
2. Scrollable Workspace Content
3. Final Decision and Completion State inside the content flow

Structure:

┌──────────────────────────────────────────────────────────────┐
│ Pinned Workspace Header                                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Scrollable Workspace Content                                 │
│                                                              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Final Decision State                                         │
│ contained within the scrollable content                      │
└──────────────────────────────────────────────────────────────┘

Do not create a permanently fixed action bar at the bottom.

Portfolio reasoning must not feel like a transactional checkout flow.

Actions belong inside the relevant reasoning context.


6. PINNED HEADER

The header remains visible while the Workspace content scrolls.

Recommended structure:

┌──────────────────────────────────────────────────────────────┐
│ PORTFOLIO WORKSPACE | Is my portfolio positioned the way     │
│                       I want?              8 holdings | Close │
└──────────────────────────────────────────────────────────────┘

Left side:

- Workspace label: Portfolio Workspace
- governing question: Is my portfolio positioned the way I want?

Right side:

- number of holdings,
- optional review status,
- overflow menu if required,
- Close control.

The current governing-question treatment is strong and should be preserved.

The header should remain restrained.

Do not place the main portfolio judgment in the header.

The Atlas Portfolio Conclusion is the primary judgment.

Permitted restrained portfolio status labels:

- Stable
- Review Recommended
- Attention Required

These may appear near the portfolio identity but should not dominate the header.


7. CONTENT ORDER

The complete content order is:

1. Atlas Portfolio Conclusion
2. What Changed
3. Portfolio Health
4. Portfolio Drivers
5. Strengths
6. Weaknesses
7. Diversification
8. Hidden Concentration
9. Risk Dependencies
10. Scenario Analysis
11. Capital Allocation
12. Portfolio Evolution
13. Final Decision State
14. Related Actions

The order must remain stable.

Do not introduce tabs.

Do not create a secondary navigation rail.

Do not divide the Workspace into separate pages.

The Workspace should feel like one continuous reasoning document.


8. FIRST VIEWPORT

The first viewport must contain:

1. Pinned Header
2. Atlas Portfolio Conclusion
3. What Changed
4. beginning or summary of Portfolio Health

Target structure:

┌──────────────────────────────────────────────────────────────┐
│ Header                                                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ATLAS PORTFOLIO CONCLUSION                                   │
│                                                              │
│ The portfolio remains structurally sound across seven of     │
│ eight positions.                                             │
│                                                              │
│ One core assumption has broken in LVMH. Enterprise AI        │
│ exposure has increased and represents the most significant   │
│ concentration in the portfolio.                              │
│                                                              │
│ Two capital-allocation decisions deserve attention.          │
│                                                              │
│ [ Portfolio Review Recommended ]                             │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ WHAT CHANGED                                                 │
│                                                              │
│ LVMH core assumption broken                              →   │
│ Alphabet conviction increased                           →   │
│ Danaher entry range reached                            →   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ PORTFOLIO HEALTH                                             │
│ Expected Return | Business Quality | Conviction              │
└──────────────────────────────────────────────────────────────┘

The first viewport must not contain:

- full scenario analysis,
- full diversification tables,
- long charts,
- all portfolio drivers,
- complete risk-dependency detail,
- complete capital-allocation comparisons.

The first viewport communicates the conclusion and priority.

The rest of the Workspace supports deliberate exploration.


9. ATLAS PORTFOLIO CONCLUSION

The Atlas Portfolio Conclusion is the largest and most prominent content block.

It uses the full available content width.

Structure:

┌──────────────────────────────────────────────────────────────┐
│ ATLAS PORTFOLIO CONCLUSION                                   │
│                                                              │
│ Primary conclusion headline                                  │
│                                                              │
│ Supporting explanation, maximum three concise paragraphs.    │
│                                                              │
│ [Decision or review state]                                   │
│                                                              │
│ Reviewed today · 8 holdings · 5 watchlist                    │
│                                                              │
│ Why this conclusion?                                  ▾      │
└──────────────────────────────────────────────────────────────┘

Required content:

- section label,
- primary portfolio conclusion,
- short supporting reasoning,
- decision or review state,
- review metadata,
- optional expandable reasoning control.

Permitted primary states:

- No Structural Changes Required
- Portfolio Review Recommended
- Capital Allocation Opportunity
- Concentration Review Required
- Portfolio Decision Required

The primary state describes the current decision context.

It must not execute a transaction.

The conclusion should communicate:

- the overall structural state,
- the main material weakness,
- the main portfolio-level concentration,
- whether action is required,
- the number of decisions currently deserving attention.

The conclusion should not attempt to summarize every section in the Workspace.

Expanded reasoning may reveal:

- primary supporting changes,
- major dependencies,
- confidence,
- unresolved uncertainty,
- links to relevant sections.

Do not duplicate the entire Workspace inside the expanded conclusion.


10. WHAT CHANGED

What Changed appears directly below the conclusion.

It shows only material changes since the previous review.

Maximum visible items:

5

Each item includes:

- directional or status marker,
- concise headline,
- one-sentence explanation,
- Open or related action,
- optional link to an Investment Workspace.

Structure:

┌──────────────────────────────────────────────────────────────┐
│ WHAT CHANGED                                    Since May 12 │
│                                                              │
│ ↓ LVMH core assumption broken                         Open → │
│   Chinese luxury demand confirmed materially below thesis.   │
│                                                              │
│ ↑ Alphabet conviction increased                       Open → │
│   GCP margins turned positive for the first time.             │
│                                                              │
│ → Constellation Software above base case               Open →│
│   Expected return compressed. Do not add.                      │
│                                                              │
│ ◎ Danaher entry range reached                         Open → │
│   Start Position signal issued.                              │
│                                                              │
│ ↑ Brookfield FRE grew 28%                            Open →  │
│   Add signal maintained.                                     │
└──────────────────────────────────────────────────────────────┘

Interaction:

Selecting a change may:

- expand its explanation,
- open the relevant Investment Workspace,
- scroll to a related portfolio section,
- highlight affected positions.

The Portfolio Workspace state must remain preserved.

Empty state:

Nothing material has changed since the previous review.

The empty state should be calm and compact.

It should not appear like missing content.


11. PORTFOLIO HEALTH

Portfolio Health uses a six-card grid.

Recommended dimensions:

- wide desktop: 3 columns × 2 rows,
- narrower desktop: 2 columns × 3 rows,
- narrow Workspace: 1 column.

Recommended cards:

1. Expected Return
2. Business Quality
3. Conviction
4. Diversification
5. Liquidity
6. Risk Level or Risk Dependencies

Each card includes:

- label,
- current state,
- optional calibrated range,
- trend,
- one-sentence interpretation,
- optional View Reasoning control.

Structure:

┌──────────────────────────────┐
│ EXPECTED RETURN              │
│                              │
│ 16% p.a.                     │
│ ↑ Improving                  │
│                              │
│ Blended across all holdings. │
└──────────────────────────────┘

Cards must communicate states rather than decorative scores.

Avoid one composite portfolio-health score.

Avoid radial gauges.

Avoid presenting false precision.

Where a numeric range is used, it should be accompanied by interpretation.

Example:

12–15% estimated range
Attractive
Slightly declining

The card grid currently works well and should be retained.


12. PORTFOLIO DRIVERS

Portfolio Drivers explains what currently drives portfolio outcomes.

Default visible drivers:

3–5

Examples:

- Enterprise AI
- Semiconductor Capex
- Interest Rates
- Luxury Consumer Demand
- USD Strength

Default structure:

┌──────────────────────────────────────────────────────────────┐
│ PORTFOLIO DRIVERS                                            │
│                                                              │
│ Enterprise AI            Very High                      ↑    │
│ Semiconductor Capex      High                           →    │
│ Interest Rates           Moderate                       →    │
│ Luxury Consumer Demand   Moderate                       ↓    │
│ USD Strength             Low                            →    │
└──────────────────────────────────────────────────────────────┘

Each row or driver card contains:

- driver name,
- influence level,
- trend,
- optional visual influence bar,
- expandable explanation.

Expanded driver reveals:

- why the driver matters,
- affected positions,
- whether its influence is rising or declining,
- related portfolio strengths,
- related portfolio weaknesses,
- related risk dependencies.

Influence levels:

- Very High
- High
- Moderate
- Low

Do not imply exact scientific measurement unless the model supports it.

The current row-based implementation is appropriate and should remain visually restrained.


13. STRENGTHS

Strengths is an expandable insight section.

The section begins collapsed or partially summarized unless directly referenced by the Atlas Portfolio Conclusion.

Default structure:

┌──────────────────────────────────────────────────────────────┐
│ STRENGTHS                                               ▾    │
│                                                              │
│ • Durable competitive advantages across 7 of 8 positions     │
│ • High average business quality                              │
│ • Strong free cash flow generation                           │
│ • Attractive aggregate expected return                       │
│ • Long investment horizons support compounding               │
└──────────────────────────────────────────────────────────────┘

Each strength row contains:

- headline,
- one-line portfolio implication,
- optional number of supporting positions,
- expansion control.

Expanded row reveals:

- explanation,
- affected positions,
- supporting Investment Cases,
- relevant evidence,
- uncertainty or limitations,
- related Workspace link.

Strengths must not become generic praise.

Each strength must explain why the portfolio is resilient, attractive, or coherent.


14. WEAKNESSES

Weaknesses uses the same component structure as Strengths.

Default structure:

┌──────────────────────────────────────────────────────────────┐
│ WEAKNESSES                         LVMH REVIEW PENDING    ▾    │
│                                                              │
│ • Enterprise AI theme concentration                          │
│ • One broken assumption — LVMH                               │
│ • Limited inflation protection                               │
│ • Geographic and currency concentration                      │
└──────────────────────────────────────────────────────────────┘

Expanded weakness reveals:

- explanation,
- affected positions,
- portfolio consequence,
- whether action is required,
- related assumptions,
- uncertainty,
- related Investment Workspace.

Weaknesses should not use alarming red treatment by default.

The purpose is awareness and judgment, not urgency.

Use elevated warning treatment only where the Portfolio Conclusion already states that review or decision is required.


15. DIVERSIFICATION

Diversification is multi-dimensional.

It must not begin with a large sector pie chart.

Default summary dimensions:

- Sector
- Geography
- Currency
- Market Cap
- Business Model
- Themes

Optional future dimensions:

- Investment Style
- Cyclicality
- Duration
- Regulatory Exposure
- Customer Concentration

Default structure:

┌──────────────────────────────────────────────────────────────┐
│ DIVERSIFICATION                                              │
│ Multi-dimensional. Sector labels alone are insufficient.     │
│                                                              │
│ SECTOR                                                       │
│ Technology 36.9% · Luxury 13.4% · Financial 20.9%            │
│ Reasonably distributed by label. AI concentration is hidden. │
│                                                              │
│ GEOGRAPHY                                                    │
│ US 56% · Europe 35% · Canada 9%                              │
│ Limited emerging-market exposure.                            │
│                                                              │
│ CURRENCY                                                     │
│ USD 56% · EUR 24% · CAD 9% · Mixed 11%                      │
│ USD strength remains a mild headwind.                         │
│                                                              │
│ MARKET CAP                                                   │
│ Large-cap dominant                                           │
│                                                              │
│ BUSINESS MODEL                                               │
│ Software · Industrial · Consumer Brand · Insurance           │
│                                                              │
│ THEMES                                                       │
│ AI Infrastructure 36.9% · Luxury 13.4% · Asset Management    │
└──────────────────────────────────────────────────────────────┘

Each dimension includes:

- compact allocation summary,
- Atlas interpretation,
- optional state label,
- expandable detail.

Expanded state may use a dimension selector:

[Sector] [Geography] [Currency] [Market Cap] [Business Model] [Themes]

Only one detailed visualization should dominate at a time.

Below any visualization, show:

- Atlas interpretation,
- affected positions,
- whether concentration is intentional,
- whether it is compatible with investor intent.

No chart should appear without explanatory text.


16. HIDDEN CONCENTRATION

Hidden Concentration is a dedicated section.

It must not be merged with ordinary Diversification.

Structure:

┌──────────────────────────────────────────────────────────────┐
│ HIDDEN CONCENTRATION                         ATLAS INSIGHT    │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ ATLAS INSIGHT                                            │ │
│ │                                                          │ │
│ │ Technology exposure appears distributed across cloud     │ │
│ │ software, semiconductors, and asset management. However,  │ │
│ │ five holdings ultimately depend on continued enterprise  │ │
│ │ AI capital expenditure.                                  │ │
│ │                                                          │ │
│ │ UNDERLYING DEPENDENCY: Enterprise AI Capital Expenditure │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ AFFECTED                                                     │
│ [MSFT] [GOOGL] [ASML] [CSU] [BAM]                            │
│                                                              │
│ EXPOSURE                                                     │
│ Approximately 46% by underlying dependency                   │
│ 36.9% by visible sector label                                │
│                                                              │
│ Intentionality: Partly intentional                           │
│ Confidence: High                                             │
│                                                              │
│ Review dependency                                      →     │
└──────────────────────────────────────────────────────────────┘

The section must clearly distinguish:

- visible sector allocation,
- underlying dependency,
- affected positions,
- intentional versus accidental concentration,
- confidence.

If several hidden concentrations exist:

- show the most important insight in full,
- show remaining concentrations as compact rows beneath it.

The current Atlas Insight callout is a strong implementation and should be preserved.

Ensure the insight text remains readable and does not become too wide or dense.


17. RISK DEPENDENCIES

Risk Dependencies answers:

What must remain true for this portfolio to work as intended?

Use vertically stacked expandable rows.

Structure:

┌──────────────────────────────────────────────────────────────┐
│ RISK DEPENDENCIES                                            │
│ What must remain true for this portfolio to work as intended.│
│                                                              │
│ Enterprise AI Spending           Exposure: High              │
│                                  Confidence: High       ▾    │
│                                                              │
│ Chinese Luxury Demand            Exposure: Moderate          │
│                                  Confidence: Moderate   ▾    │
│                                                              │
│ Interest Rate Environment        Exposure: Low–Moderate      │
│                                  Confidence: High       ▾    │
│                                                              │
│ Semiconductor Capex Cycle        Exposure: High              │
│                                  Confidence: High       ▾    │
│                                                              │
│ Insurance Float Quality          Exposure: Low               │
│                                  Confidence: Very High  ▾    │
└──────────────────────────────────────────────────────────────┘

Expanded dependency content includes:

- dependency statement,
- affected positions,
- how the dependency enters each thesis,
- mitigating portfolio strengths,
- confidence,
- unknowns,
- what change would trigger review.

Do not use unexplained heatmaps.

Do not reduce all risk into one score.

Exposure and confidence must be visually separate concepts.


18. SCENARIO ANALYSIS

Scenario Analysis is a resilience test.

It must not present scenarios as forecasts.

Default layout:

- wide desktop: 2-column or 3-column card grid,
- standard desktop: 2-column grid,
- narrow Workspace: stacked cards.

Recommended scenarios:

- AI Investment Slowdown
- Recession
- Persistent High Interest Rates
- China Demand Weakness Persists
- Persistent Inflation
- Strong Equity Markets

Additional scenarios may be introduced only when supported by the portfolio context.

Card structure:

┌──────────────────────────────┐
│ AI INVESTMENT SLOWDOWN       │
│                              │
│ Materially Exposed           │
│                              │
│ View Reasoning          →    │
└──────────────────────────────┘

Permitted calibrated outcomes:

- Likely Resilient
- Moderately Exposed
- Materially Exposed
- Highly Dependent

Expanded scenario includes:

- portfolio-level assessment,
- most affected positions,
- resilient positions,
- relevant assumptions,
- mitigating strengths,
- confidence,
- what would require review.

Do not show probability percentages.

Do not show exact predicted losses unless supported by a separately validated model and clearly labeled as estimates.

The current scenario-card approach is appropriate.


19. CAPITAL ALLOCATION

Capital Allocation is one of the most important sections.

It should receive substantial vertical space.

It compares alternative uses of capital rather than optimizing automatically.

Primary structure:

┌──────────────────────────────────────────────────────────────┐
│ CAPITAL ALLOCATION                                           │
│                                                              │
│ LARGEST POSITIONS                  OPPORTUNITIES              │
│                                                              │
│ Microsoft        Hold     14.2%    Danaher             Open →│
│ Berkshire        Hold     12.2%    Start Position             │
│ Alphabet         Add      11.8%                              │
│ ASML             Hold     10.9%    Alphabet            Open →│
│ Constellation    Monitor   9.4%    Add on 5%+ weakness        │
│                                  Brookfield AM        Open → │
│                                  Add to 10% target            │
│                                  LVMH                 Open → │
│                                  Reduce — review pending      │
│                                                              │
│ CAPITAL COMPETITION                                          │
│                                                              │
│ Danaher currently offers a stronger expected return than     │
│ increasing Microsoft or Constellation Software. Reducing     │
│ LVMH from 7.1% to 3–4% could fund a Danaher initiation       │
│ without requiring new cash.                                  │
│                                                              │
│ [Compare Danaher vs LVMH] [Review Available Cash]            │
└──────────────────────────────────────────────────────────────┘

Required elements:

- largest positions,
- position actions or current states,
- available opportunities,
- watchlist candidates,
- capital-competition narrative,
- optional available cash,
- comparative next-step actions.

The primary interpretation must include trade-offs.

Example:

Danaher currently provides the stronger marginal use of capital, but adding it would increase healthcare exposure.

Rules:

- no auto-rebalance button,
- no one-click trade execution,
- no implied mathematically optimal portfolio,
- no recommendation without portfolio-context explanation,
- no transaction pressure.

Capital Allocation should open relevant Investment Workspaces or comparison views.


20. PORTFOLIO EVOLUTION

Portfolio Evolution shows how the portfolio has evolved as an investment system.

Default time selector:

[1Y] [3Y] [5Y] [All]

Default narrative dimensions:

- Concentration
- Diversification
- Expected Return
- Business Quality
- Conviction
- Liquidity
- Theme Exposure
- Risk Dependencies

Default structure:

┌──────────────────────────────────────────────────────────────┐
│ PORTFOLIO EVOLUTION                         [1Y][3Y][5Y][All] │
│                                                              │
│ Portfolio evolution as an investment system — not merely     │
│ as portfolio value.                                          │
│                                                              │
│ Jul 2026                                                     │
│ LVMH core assumption broken. GCP profitability confirmed.    │
│ AI theme exposure reached 37%.                               │
│                                                              │
│ Jun 2026                                                     │
│ Danaher entered target entry range. Start Position issued.   │
│                                                              │
│ Apr 2026                                                     │
│ BAM target weight increased from 8% to 10%.                  │
└──────────────────────────────────────────────────────────────┘

Expanded evolution may use a dimension selector:

[Quality] [Conviction] [Expected Return] [Concentration] [Themes]

The timeline should connect:

- meaningful portfolio changes,
- decisions,
- additions,
- reductions,
- changed assumptions,
- changed conviction,
- Atlas interpretation.

Portfolio market value may appear as supporting context.

It must not dominate the section.


21. FINAL DECISION STATE

The Workspace must end with a clear portfolio-level completion or decision state.

The current generic Actions row should be refined into a stronger final decision state followed by relevant actions.

There are two primary states.


21.1 NO ACTION REQUIRED

Structure:

┌──────────────────────────────────────────────────────────────┐
│ NO ACTION REQUIRED                                           │
│                                                              │
│ The portfolio remains aligned with your long-term strategy.  │
│ Current concentration is understood and does not require     │
│ immediate structural change.                                 │
│                                                              │
│ Review again when:                                           │
│ • Microsoft exceeds the preferred concentration range        │
│ • AI spending assumptions materially weaken                  │
│ • available cash exceeds the preferred range                 │
│                                                              │
│ [Record Portfolio Review Complete]                           │
└──────────────────────────────────────────────────────────────┘

This state should feel complete.

It should help the user leave the Workspace without feeling that more browsing is required.


21.2 PORTFOLIO DECISION REQUIRED

Structure:

┌──────────────────────────────────────────────────────────────┐
│ PORTFOLIO DECISION REQUIRED                                  │
│                                                              │
│ One portfolio-level decision remains unresolved.             │
│ LVMH contains a broken core assumption and may no longer      │
│ justify its current 7.1% allocation.                         │
│                                                              │
│ [Review LVMH] [Compare LVMH vs Danaher]                      │
└──────────────────────────────────────────────────────────────┘

The final decision state guides the next reasoning step.

It must not pressure the user into executing a trade.


22. RELATED ACTIONS

Relevant actions may appear beneath the final decision state.

Examples:

- Review LVMH
- Open Danaher
- Compare Danaher vs LVMH
- Open Alphabet
- Open Brookfield Asset Management
- Record No Action Required

Actions should open the relevant Workspace or comparison context.

The Portfolio Workspace does not execute trades.

Avoid presenting six equal buttons in one undifferentiated row.

Use hierarchy:

Primary action:
- the most important unresolved reasoning task.

Secondary actions:
- relevant supporting Workspaces.

Completion action:
- Record Review Complete or No Action Required.

The current Actions implementation should therefore be reorganized into:

1. final decision state,
2. one primary action,
3. limited secondary actions,
4. completion state.


23. DEFAULT EXPANSION STATES

Default expanded sections:

- Atlas Portfolio Conclusion
- What Changed
- Portfolio Health

Conditionally expanded:

- any section directly referenced by the Atlas Portfolio Conclusion,
- any section containing a required portfolio decision,
- any section containing newly material information.

Default collapsed sections:

- Portfolio Drivers
- Strengths
- Weaknesses
- Diversification
- Hidden Concentration
- Risk Dependencies
- Scenario Analysis
- Capital Allocation
- Portfolio Evolution

However, the implementation may show a compact summary inside a collapsed section.

Collapsed state includes:

- section title,
- one portfolio-level conclusion,
- one or two key signals,
- expand control.

Expanded state includes:

- explanation,
- affected positions,
- supporting data,
- uncertainty,
- related actions.

The current implementation already uses effective expandable sections and should retain this behavior.


24. SECTION HEADERS

All deep sections use a consistent header pattern:

┌──────────────────────────────────────────────────────────────┐
│ SECTION LABEL                            Optional State   ▾   │
└──────────────────────────────────────────────────────────────┘

Examples:

STRENGTHS
WEAKNESSES — LVMH REVIEW PENDING
HIDDEN CONCENTRATION — ATLAS INSIGHT
RISK DEPENDENCIES
SCENARIO ANALYSIS
CAPITAL ALLOCATION
PORTFOLIO EVOLUTION

Section headers should:

- use restrained hierarchy,
- make expanded or collapsed state obvious,
- support keyboard focus,
- use consistent padding,
- avoid competing with the Atlas Portfolio Conclusion.


25. LINKS TO INVESTMENT WORKSPACES

Position names and related actions should be interactive.

Selecting a position opens its Investment Workspace while preserving Portfolio Workspace context.

Preserved Portfolio Workspace state:

- scroll position,
- expanded sections,
- selected diversification dimension,
- selected scenario,
- selected time range,
- filters,
- sorting,
- currently highlighted position or dependency.

Closing the Investment Workspace returns the user to the exact previous Portfolio Workspace state.

Do not route the user back to the Dashboard between related reasoning tasks.

The user should experience:

Portfolio Workspace
→ Investment Workspace
→ return to the same Portfolio Workspace location


26. INTERACTION RULES

Hover:

- reveal additional explanation where appropriate,
- reveal subtle row affordance,
- never reveal essential information only on hover.

Click:

- expand section,
- open explanation,
- open related Workspace,
- select scenario or diversification dimension.

Double-click:

- no behavior.

Escape:

- close the topmost Workspace.

Close:

- return to the preserved Dashboard state.

Back:

- close the topmost nested Workspace,
- return to the exact previous context.

Keyboard:

- all interactive controls reachable,
- clear focus state,
- logical tab order,
- Enter or Space activates expandable controls.

No essential interaction may depend on pointer hover.


27. RESPONSIVE BEHAVIOR

Wide desktop:

- strengths and weaknesses may appear side by side if density remains readable,
- health cards in three columns,
- scenario cards in two or three columns,
- capital allocation uses two-column comparison,
- diversification detail may use split text and visualization layout.

Standard desktop:

- health cards in two or three columns,
- scenario cards in two columns,
- capital allocation remains side by side where possible,
- strengths and weaknesses may stack if readability improves.

Narrow Workspace or tablet:

- all content becomes one column,
- cards stack vertically,
- dimension selectors become horizontally scrollable,
- position chips wrap,
- header retains governing question and Close control,
- no essential content depends on hover.

Mobile is not the primary target for this version unless required by the wider Atlas product scope.


28. LOADING STATE

Loading sequence:

1. Workspace shell
2. pinned header
3. Atlas Portfolio Conclusion skeleton
4. What Changed skeleton
5. Portfolio Health skeleton
6. remaining sections progressively

Skeletons should resemble the final component structure.

Do not use one large central spinner.

If deep portfolio reasoning is still processing, show contextual messages such as:

Atlas is evaluating portfolio dependencies…

Atlas is comparing shared portfolio exposures…

Atlas is testing scenario resilience…

Available content should remain usable while deeper sections load.


29. EMPTY STATES

Required empty states:


29.1 NO PORTFOLIO

No portfolio has been created.

Primary action:

Create Portfolio


29.2 NO MATERIAL CHANGES

Nothing material has changed since your previous review.

The portfolio remains structurally unchanged.


29.3 NO HIDDEN CONCENTRATION IDENTIFIED

No significant hidden concentration has been identified with the currently available information.

Do not imply certainty beyond the available data.


29.4 NO CAPITAL ALLOCATION OPPORTUNITY

No current position or watchlist candidate clearly offers a superior marginal use of capital.


29.5 NO ACTION REQUIRED

The portfolio remains aligned with the investor’s declared long-term intent.

This is a successful completion state, not missing content.


30. PARTIAL-DATA STATES

A failure or missing input in one section must not block the entire Workspace.

Examples:

Scenario analysis is temporarily unavailable.
Your portfolio conclusion and other sections remain current.

Currency exposure cannot be fully evaluated because two holdings lack complete reporting data.

Hidden-concentration analysis has moderate confidence because one holding has incomplete segment disclosure.

Partial-data state must include:

- what is unavailable,
- why,
- whether the portfolio conclusion is affected,
- what remains current,
- whether the user needs to provide information.

Do not silently omit incomplete sections.


31. ERROR STATES

Use section-level errors whenever possible.

Structure:

┌──────────────────────────────────────────────────────────────┐
│ SCENARIO ANALYSIS                                            │
│                                                              │
│ Scenario analysis is temporarily unavailable.                │
│ Portfolio Health and Risk Dependencies remain current.       │
│                                                              │
│ [Retry]                                                      │
└──────────────────────────────────────────────────────────────┘

The entire Workspace should fail only if the portfolio itself cannot be loaded.

Errors should remain calm and factual.

Avoid technical error codes in the primary interface.


32. ACCESSIBILITY

The wireframe must support:

- keyboard navigation,
- logical heading hierarchy,
- screen-reader labels,
- visible focus states,
- large click targets,
- sufficient contrast,
- reduced motion,
- non-color status communication,
- expandable rows with clear state labels,
- scenario and risk states readable without color.

Icons and directional indicators must not carry meaning alone.

Status should always be available in text.


33. FIGMA COMPONENT REQUIREMENTS

Create reusable low-fidelity components for:

- Workspace shell
- pinned Workspace header
- Atlas Portfolio Conclusion card
- portfolio state badge
- What Changed item
- Portfolio Health card
- Portfolio Driver row
- expandable Insight row
- Strength row
- Weakness row
- position chip
- Diversification summary row
- dimension selector
- Hidden Concentration insight card
- Risk Dependency row
- Scenario card
- Capital Allocation comparison panel
- Portfolio Evolution timeline event
- Final Decision State card
- primary Workspace action
- secondary Workspace action
- empty state
- loading skeleton
- partial-data state
- section-level error state

Each applicable component should include:

- default,
- hover,
- keyboard focus,
- expanded,
- collapsed,
- loading,
- unavailable,
- selected,
- disabled states.


34. REQUIRED FIGMA FRAMES

Create at least the following frames:

1. Portfolio Workspace — Default First Viewport
2. Portfolio Workspace — Full Scrolled Workspace
3. Portfolio Workspace — Portfolio Health Expanded
4. Portfolio Workspace — Strengths Expanded
5. Portfolio Workspace — Weaknesses Expanded
6. Portfolio Workspace — Diversification Expanded
7. Portfolio Workspace — Hidden Concentration Expanded
8. Portfolio Workspace — Risk Dependency Expanded
9. Portfolio Workspace — Scenario Expanded
10. Portfolio Workspace — Capital Allocation
11. Portfolio Workspace — Portfolio Evolution Expanded
12. Portfolio Workspace — No Action Required
13. Portfolio Workspace — Portfolio Decision Required
14. Portfolio Workspace — No Material Changes
15. Portfolio Workspace — Partial Data
16. Portfolio Workspace — Loading
17. Portfolio Workspace — Section Error
18. Portfolio Workspace — Narrow Layout
19. Portfolio Workspace — Investment Workspace Opened Above Portfolio Context
20. Portfolio Workspace — Returned State After Closing Investment Workspace

The Default First Viewport frame is the primary prototype entry point.


35. REQUIRED PROTOTYPE INTERACTIONS

The Figma prototype must support:

- open Portfolio Workspace from All Positions,
- close Portfolio Workspace,
- expand and collapse sections,
- open Why This Conclusion,
- select a What Changed item,
- open an Investment Workspace from a position,
- return to preserved Portfolio Workspace state,
- select a Portfolio Health card,
- expand a Portfolio Driver,
- expand a Strength,
- expand a Weakness,
- switch Diversification dimension,
- open Hidden Concentration detail,
- expand a Risk Dependency,
- select and expand a Scenario,
- open Capital Allocation comparison,
- change Portfolio Evolution time range,
- record No Action Required,
- open a required portfolio decision,
- close the Workspace and return to the preserved Dashboard state.

Animations should be restrained and consistent with UX-000.

The prototype should communicate continuity, not page navigation.


36. VISUAL DENSITY RULES

The Portfolio Workspace is information-rich, but it must remain calm.

Rules:

- use generous separation between major sections,
- use compact spacing within related rows,
- keep conclusion text readable,
- avoid lines longer than a comfortable reading width,
- do not allow all sections to appear visually equally important,
- use cards only where grouping improves comprehension,
- avoid placing every row inside a boxed card,
- preserve flat document-like sections where appropriate,
- reserve stronger elevation for Atlas Conclusion, Atlas Insight, Capital Competition, and Final Decision State.

The current implementation succeeds in feeling analytical rather than decorative.

The next refinement should improve readability without making the Workspace visually heavier.


37. COPY AND LANGUAGE RULES

Portfolio copy should be:

- direct,
- calibrated,
- decision-relevant,
- specific,
- concise,
- non-alarmist.

Prefer:

The portfolio remains structurally sound across seven of eight positions.

Avoid:

Your portfolio is doing great.

Prefer:

Enterprise AI exposure is high and increasingly shared across five holdings.

Avoid:

Your tech allocation may be risky.

Prefer:

One core assumption has broken in LVMH and requires review.

Avoid:

LVMH is a bad investment.

Every conclusion should communicate:

- what Atlas currently believes,
- why,
- how confident the assessment is,
- whether a decision is required.


38. WIREFRAME VALIDATION CHECKLIST

Before visual design is considered complete, confirm:

- The governing question is visible in the header.
- The first viewport communicates Atlas’ portfolio conclusion.
- The user understands whether action is required.
- What Changed contains only material changes.
- Portfolio Health distinguishes portfolio quality from recent performance.
- Portfolio Drivers reveal current underlying influences.
- Strengths explain resilience rather than offer generic praise.
- Weaknesses explain trade-offs without manufacturing urgency.
- Diversification is explicitly multi-dimensional.
- Hidden Concentration remains separate from standard diversification.
- Risk is explained through dependencies.
- Scenario Analysis tests resilience rather than predicts outcomes.
- Capital Allocation compares competing uses of capital.
- Portfolio Evolution describes the investment system, not only portfolio value.
- The final state communicates completion or the next required decision.
- Related Investment Workspaces preserve Portfolio Workspace context.
- The Dashboard remains visible underneath.
- No chart is left without Atlas interpretation.
- No section uses false precision.
- No action executes a trade.
- No component encourages unnecessary activity.
- The Workspace can end with No Action Required.


39. COMPLETION STANDARD

UX-007A is successfully implemented when a user can navigate the monochrome prototype and answer:

- What is Atlas’ current conclusion about my portfolio?
- What materially changed?
- Is the portfolio structurally healthy?
- What currently drives portfolio outcomes?
- What are the portfolio’s strongest qualities?
- Where is the portfolio vulnerable?
- Is concentration visible or hidden?
- Which assumptions must remain true?
- How resilient is the portfolio under relevant scenarios?
- Where should available capital compete?
- How has the portfolio changed as an investment system?
- Is a decision required?
- What is the next appropriate reasoning step?
- Is doing nothing currently reasonable?

The user should answer the first three questions from the initial viewport.

The remaining questions should be answered through deliberate progressive disclosure.

The Workspace must provide clarity without requiring every section to be opened.


40. IMPLEMENTATION INSTRUCTION FOR FIGMA

Refine the existing Portfolio Workspace implementation into a complete low-fidelity structural prototype using this document as the exact wireframe specification.

Preserve the current successful interaction model:

- Portfolio Workspace opens above the Dashboard,
- Dashboard context remains visible,
- header stays pinned,
- content scrolls internally,
- Atlas Portfolio Conclusion appears first,
- What Changed appears immediately after,
- Portfolio Health uses a six-card grid,
- deeper reasoning uses expandable sections,
- Hidden Concentration remains a dedicated Atlas Insight,
- Risk Dependencies use exposure and confidence,
- Scenario Analysis uses calibrated language,
- Capital Allocation compares competing uses of capital,
- Portfolio Evolution is narrative,
- position links open related Investment Workspaces.

Apply the following refinements:

- improve the first-viewport hierarchy,
- formalize consistent section headers,
- standardize collapsed and expanded states,
- make the final portfolio decision state more prominent,
- reorganize the current Actions row into one primary decision path, limited secondary actions, and a completion state,
- preserve Portfolio Workspace state when Investment Workspaces are opened,
- add loading, empty, partial-data, and error states,
- add the required desktop and narrow-layout frames,
- build reusable components for every repeated pattern,
- keep the design monochrome and structure-first,
- do not introduce new navigation models,
- do not add unsupported scoring systems,
- do not add decorative charts,
- do not add automatic rebalancing,
- do not add trading execution,
- do not manufacture urgency.

Use UX-007 for behavioral requirements.

Use UX-006 for portfolio philosophy.

Use UX-000 as the governing Atlas experience standard.

The final result should feel like a calm, focused portfolio reasoning document above the Dashboard—not a portfolio analytics terminal, a trading interface, or a collection of unrelated widgets.
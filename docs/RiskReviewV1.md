# Risk Review V1

**Created:** 2026-07-08 (Sprint 284)
**Status:** DEFINED — architecture specification. No runtime implementation.
**Depends on:** [docs/AssumptionReviewV1.md](AssumptionReviewV1.md), [docs/EvidenceQualityReviewV1.md](EvidenceQualityReviewV1.md), [docs/EvidenceAssemblyV1.md](EvidenceAssemblyV1.md), [docs/InvestmentReviewPipelineV1.md](InvestmentReviewPipelineV1.md)
**Pipeline stage:** Stage 7 — Risk Review

---

## Purpose

This document defines the canonical Risk Review process for Atlas.

It answers:

> **What risks exist? Which assumptions does each risk depend on? What evidence supports the existence of the risk? What future events should cause this risk to be reviewed? What uncertainties remain unresolved?**

It does not answer:

> ~~Should the user invest? Should the user sell? Which investment is best?~~

Risk Review is not about predicting what will happen. It is about identifying what could invalidate the current investment thesis. Every material risk should be traceable to one or more assumptions. Every assumption reviewed in Stage 6 is a candidate risk source.

---

## Position in the Pipeline

```
Evidence Assembly  (Stage 4)
 ↓
Evidence Quality Review  (Stage 5)
 ↓
Assumption Review  (Stage 6)
 ↓
Risk Review  (Stage 7)  ←  defined in this document
 ↓
Value Scenario Review  (Stage 8)
 ↓
Weekly Review  (Stage 9)
```

Risk Review is the stage where explicit and implicit threats to the investment thesis are catalogued. It transforms the assumption register (Stage 6) and evidence quality outputs (Stage 5) into a structured risk register that informs every downstream stage.

---

## Risk Categories

### 1. Business Risk

**Purpose:** Risks arising from how the company operates, serves customers, and creates value.

**Examples:**
- Revenue growth decelerates materially below the base assumption
- Customer churn accelerates, reducing recurring revenue quality
- Unit economics deteriorate as the company scales
- Product-market fit weakens due to changing customer needs
- Key contracts are not renewed or are repriced downward

**Common evidence sources:** Earnings reports, customer metrics, product commentary, management guidance.

**Common assumption dependencies:** Business assumptions (revenue growth, customer retention, unit economics), Competitive assumptions (product-market fit durability).

---

### 2. Financial Risk

**Purpose:** Risks arising from revenue, profitability, cash generation, or capital structure.

**Examples:**
- Revenue misses guidance by a material margin
- Operating margins compress due to cost inflation or pricing pressure
- Free cash flow conversion deteriorates below the assumed range
- Debt levels increase beyond what earnings can service comfortably
- Working capital dynamics worsen, tightening near-term liquidity

**Common evidence sources:** Income statements, balance sheets, cash flow statements, earnings call commentary, credit facility disclosures.

**Common assumption dependencies:** Financial assumptions (margin expansion, cash conversion, debt management), Business assumptions (revenue trajectory).

---

### 3. Competitive Risk

**Purpose:** Risks arising from changes in the competitive landscape.

**Examples:**
- A well-funded new entrant addresses the core market with a differentiated approach
- An existing competitor achieves a meaningful product or pricing improvement
- The assumed competitive moat (switching costs, network effects, scale, IP) weakens
- Market share erodes faster than management commentary suggests
- Pricing power deteriorates due to competitive intensity

**Common evidence sources:** Competitor product announcements, customer commentary, market share data, management statements on competition.

**Common assumption dependencies:** Competitive assumptions (moat durability, pricing power, market share trajectory).

---

### 4. Management Risk

**Purpose:** Risks arising from leadership quality, strategic decisions, and capital allocation.

**Examples:**
- A key executive departs unexpectedly
- Management makes a large acquisition outside the assumed strategic plan
- Capital is allocated to low-return opportunities
- Management guidance proves persistently optimistic relative to outcomes
- Compensation structures create misaligned incentives

**Common evidence sources:** Leadership announcements, capital allocation history, acquisition track record, earnings call tone and accuracy.

**Common assumption dependencies:** Management assumptions (capital allocation quality, strategic continuity, leadership stability).

---

### 5. Industry Risk

**Purpose:** Risks arising from structural or cyclical changes to the industry.

**Examples:**
- Industry demand growth slows materially relative to the assumed trajectory
- Pricing rationalisation reverses due to oversupply or competitive entry
- Technology disruption accelerates obsolescence of the current business model
- The industry enters a cyclical downturn not anticipated in the base scenario
- Barriers to entry weaken, inviting new competition

**Common evidence sources:** Industry reports, competitor commentary, historical cycle data, technology development observations.

**Common assumption dependencies:** Industry assumptions (total addressable market growth, pricing rationality, structural stability).

---

### 6. Regulatory Risk

**Purpose:** Risks arising from changes in law, regulation, or enforcement.

**Examples:**
- New regulation increases compliance costs materially
- A regulatory decision restricts the company's ability to operate in a key market
- Antitrust scrutiny limits the company's ability to acquire or grow
- Data privacy regulation changes the economics of a core product
- Licences required for operation are not renewed or are challenged

**Common evidence sources:** Regulatory filings, government announcements, legal disclosures, industry association commentary.

**Common assumption dependencies:** Industry assumptions (regulatory stability), Business assumptions (operational continuity in existing markets).

---

### 7. Macro Risk

**Purpose:** Risks arising from the broader economic environment.

**Examples:**
- Interest rate increases compress valuation multiples materially beyond the assumed range
- A recessionary environment reduces demand or pricing power
- Currency movements affect international revenue beyond the assumed sensitivity
- Inflation increases input costs faster than pricing can absorb
- A credit market disruption affects the company's ability to refinance or grow

**Common evidence sources:** Central bank communications, macroeconomic indicators, management commentary on macro sensitivity, company disclosures on currency and rate exposure.

**Common assumption dependencies:** Macro assumptions (rate environment, currency stability, economic conditions), Valuation assumptions (multiple sustainability).

---

### 8. Valuation Risk

**Purpose:** Risks arising from how the market prices the company relative to its fundamentals.

**Examples:**
- The earnings multiple compresses materially due to a re-rating of growth expectations
- The peer group re-rates, pulling the company's implied valuation down
- Market sentiment shifts away from the company's sector or theme
- A premium assigned for expected future growth is reduced as growth slows
- The long-duration cash flow assumption is de-rated as rates rise

**Common evidence sources:** Historical multiple ranges, comparable company valuations, earnings growth versus multiple analysis, sector sentiment observations.

**Common assumption dependencies:** Valuation assumptions (multiple range, peer comparability), Financial assumptions (growth trajectory), Macro assumptions (rate sensitivity).

---

### 9. Portfolio Construction Risk

**Purpose:** Risks arising from how the holding interacts with the broader portfolio.

**Examples:**
- Concentration in a single holding, sector, or theme creates outsized downside exposure
- Correlation between holdings produces portfolio-level volatility beyond what individual analysis suggests
- A position grows disproportionately large through price appreciation without a corresponding evidence review
- Currency or geographic concentration creates systemic exposure beyond assumed limits
- Liquidity risk: a position is difficult to exit if conditions change

**Common evidence sources:** Current portfolio composition, position sizes, sector and geographic exposures, historical performance during stress periods.

**Common assumption dependencies:** Portfolio assumptions (concentration limits, correlation expectations, liquidity), User assumptions (investment horizon, risk tolerance).

---

### 10. Behavioural Risk

**Purpose:** Risks arising from how the user or market participants may act in ways that undermine the investment thesis.

**Examples:**
- The user sells a position during temporary volatility before the thesis has time to develop
- Recency bias causes an overweight to a recently performing theme or sector
- Loss aversion prevents timely recognition of a deteriorating thesis
- Market participants overshoot in either direction, creating temporary but disorienting price action
- Anchoring to a prior purchase price affects the objectivity of ongoing review

**Common evidence sources:** User's Decision Journal (prior behaviour), stated investor profile, market commentary on sentiment.

**Common assumption dependencies:** Behavioural assumptions (holding discipline, objectivity under volatility), User assumptions (horizon, risk tolerance).

---

## Canonical Risk Object

Every risk in the risk register carries the following fields. No scoring. No probability calculations. No ranking algorithm.

| Field | Description |
|---|---|
| `risk_id` | Unique identifier for this risk item |
| `category` | One of the ten canonical categories |
| `description` | Plain-language description of the risk |
| `linked_assumptions` | IDs of assumption register entries that this risk depends on |
| `supporting_evidence` | Evidence items that support the existence of this risk |
| `conflicting_evidence` | Evidence items that suggest the risk may be overstated |
| `evidence_quality` | Quality of the evidence supporting this risk (from Stage 5 vocabulary) |
| `uncertainty` | What is unknown about the nature, likelihood, or magnitude of this risk |
| `monitoring_triggers` | Events or data points that should prompt a review of this risk |
| `review_status` | Current state: `active`, `monitoring`, `resolved`, `obsolete` |
| `revision_history` | Prior versions of this risk entry with dates and reasons for change |

**Constraints:**
- No field accepts a numeric probability.
- No field accepts a severity score.
- The risk object makes risks visible and traceable — it does not rank them.

---

## Deterministic Risk Review Flow

The following flow is deterministic. No AI is required. Given the same evidence and assumption sets, it produces the same risk register.

```
Evidence Set  (from Stage 4)
 ↓
Evidence Quality Assessment  (from Stage 5)
 ↓
Assumption Register  (from Stage 6)
 ↓
Risk Identification
 (for each assumption: what could cause this assumption to fail?
  for each evidence gap: what risk does the absence of evidence represent?)
 ↓
Risk Classification
 (assign each identified risk to one of the ten canonical categories)
 ↓
Evidence Linking
 (link each risk to supporting and conflicting evidence items)
 ↓
Open Questions
 (generate questions for each risk with incomplete or missing evidence)
 ↓
Monitoring Triggers
 (identify events or data points that should prompt risk review)
 ↓
Risk Register
 (canonical collection of risk objects)
 ↓
Value Scenario Review  (Stage 8)
```

Each step produces structured output. No step generates a recommendation. The risk register is a first-class document that travels through every downstream stage.

---

## Monitoring Philosophy

Atlas monitors risks. It does not predict outcomes.

Monitoring is the practice of identifying, in advance, which events or observations should prompt a review of a risk. Monitoring is not surveillance. It does not require continuous data feeds. It is a structured list of conditions the user should watch for.

**Monitoring is observational, not predictive.** A monitoring trigger fires when an event occurs. Atlas then prompts a risk review. It does not predict whether the event will occur or assign a probability to it.

### Examples of monitoring triggers:

| Trigger type | Example |
|---|---|
| Quarterly earnings | Next earnings report will test the revenue growth assumption |
| Guidance revision | Any change to management's full-year guidance should prompt review |
| Regulatory decision | Outcome of the pending antitrust review expected Q3 2026 |
| Capital allocation change | Any acquisition above $1B in enterprise value warrants review |
| Customer concentration | Any customer representing more than 15% of revenue departing warrants review |
| Margin trend | Two consecutive quarters of margin contraction would prompt revision |
| Competitive development | A major product launch by the primary competitor warrants review |
| Macro event | A central bank rate decision outside the assumed range triggers review |
| Management change | Any C-suite departure should prompt a review of the management assumption |
| Analyst revision | A material downgrade from multiple analysts warrants evidence review |

### What monitoring produces:
- A list of events to watch
- A link from each event to the specific risk and assumption it would test
- A prompt to revisit the risk when the event occurs

### What monitoring does not produce:
- Predictions about whether the event will occur
- A recommended response to the event
- Automatic changes to the risk register
- Investment recommendations

---

## Examples

### Example 1 — Business execution risk

```
Risk: Revenue growth decelerates below the assumed 15% threshold.

Category: Business Risk

Description:
  The base assumption requires revenue growth above 15% annually. The company
  has delivered 17% and 19% in the last two quarters, but management has not
  reaffirmed full-year guidance and forward commentary on customer activity
  was cautious.

Linked assumptions:
  - Business: "Revenue growth remains above 15% annually"
  - Management: "Management provides reliable guidance"

Supporting evidence:
  - Q1 2026: revenue grew 19% (current, primary)
  - Q2 2026: revenue grew 17% (current, primary)
  - Management: guidance for full year is 16–20%

Conflicting evidence:
  - Research note: "customer expansion behaviour supports continued growth"

Evidence quality: Adequate
Uncertainty: Whether the growth deceleration in Q2 is temporary or structural

Monitoring triggers:
  - Next quarterly earnings report
  - Any mid-quarter update on customer activity or bookings
  - Any revision to full-year guidance

Review status: active
```

---

### Example 2 — Valuation risk

```
Risk: The earnings multiple compresses if revenue growth decelerates.

Category: Valuation Risk

Description:
  The current valuation implies a multiple of 35x forward earnings. This
  multiple is justified in the base scenario by assumed sustained revenue
  growth and margin expansion. If growth decelerates materially, the
  multiple may compress, reducing returns even if the business itself
  is healthy.

Linked assumptions:
  - Valuation: "Earnings multiple remains within 30–40x range"
  - Financial: "Revenue growth remains above 15% annually"

Supporting evidence:
  - Historical: multiple has ranged 28–42x over five years (stale)
  - No current evidence that the multiple is at risk

Conflicting evidence:
  - Macro: rates rising; high-multiple growth stocks have de-rated in similar periods

Evidence quality: Incomplete
Uncertainty: Whether the macro environment will trigger a sector-wide re-rating

Monitoring triggers:
  - Central bank rate decisions
  - Sector multiple movements among comparable companies
  - Any earnings miss that changes the growth narrative

Review status: active
```

---

### Example 3 — Customer concentration risk

```
Risk: Top customer represents an outsized share of revenue.

Category: Business Risk / Portfolio Construction Risk

Description:
  Available company facts indicate that the top customer represents
  approximately 22% of total revenue. No diversification trend has been
  documented. Loss of or material reduction in this relationship would
  have a direct impact on the revenue growth assumption.

Linked assumptions:
  - Business: "Revenue growth remains above 15% annually"
  - Business: "Customer retention rates remain stable"

Supporting evidence:
  - Company facts: customer concentration disclosure (adequate, current)

Conflicting evidence:
  - Research note: "management states customer cohort is expanding" (uncorroborated)

Evidence quality: Adequate
Uncertainty: Whether the concentration is declining, stable, or increasing

Monitoring triggers:
  - Any earnings commentary mentioning the top customer relationship
  - Any customer filing or public announcement from the top customer
  - Annual report revenue breakdown update

Review status: active
```

---

### Example 4 — Management succession risk

```
Risk: Departure of the founding CEO would create strategic uncertainty.

Category: Management Risk

Description:
  The investment thesis depends partly on the founding CEO's capital
  allocation track record and product vision. No succession plan has
  been described publicly. The thesis has not been tested under
  different leadership.

Linked assumptions:
  - Management: "Management continues to allocate capital to high-return opportunities"
  - Management: "The current leadership team remains in place"

Supporting evidence:
  - No evidence of succession planning found

Conflicting evidence:
  - None identified

Evidence quality: Weak (absence of evidence is itself a risk indicator)
Uncertainty: High — no public succession information available

Monitoring triggers:
  - Any board announcement regarding leadership or governance
  - Any earnings call or investor day discussion of succession planning
  - Any news of executive hiring at the senior level

Review status: active
```

---

### Example 5 — Portfolio concentration risk

```
Risk: A single holding now represents 28% of the portfolio.

Category: Portfolio Construction Risk

Description:
  Following recent price appreciation, a single holding has grown to
  represent 28% of the total portfolio. This concentration was not
  intended and exceeds the user's prior stated comfort level of 20%.
  The position has not been reviewed since it crossed this threshold.

Linked assumptions:
  - Portfolio: "Position size is appropriate given current evidence quality"
  - User: "Concentration within a single holding remains acceptable"

Supporting evidence:
  - Portfolio data: current weight 28% (current, user-provided)

Conflicting evidence:
  - Prior stated preference: "maximum single-position weight ~20%"

Evidence quality: Strong (for the concentration fact itself)
Uncertainty: Whether the user's preference has changed, and whether the evidence quality justifies the current weight

Monitoring triggers:
  - Any further price appreciation increasing concentration beyond 30%
  - Next scheduled weekly review
  - Any change to the investment thesis for this holding

Review status: active
```

---

## Canonical Principles

### Every material risk links to assumptions
A risk that cannot be traced to at least one assumption in the assumption register has not been fully understood. The link between risk and assumption makes the origin of the risk traceable and revisable.

### Every material risk links to evidence where available
Where evidence exists that supports or qualifies a risk, it is linked. Where no evidence exists, the absence is noted. Missing evidence may itself represent a risk (see below).

### Uncertainty is visible
Every risk entry carries an uncertainty field. Uncertainty is not hidden, averaged away, or replaced with a confidence estimate. If the nature, existence, or materiality of a risk is unclear, that is recorded as uncertainty.

### Risks evolve over time
A risk that was material twelve months ago may have been resolved by new evidence. A risk that appeared minor may have grown as assumptions have weakened. Risk Review is a recurring process. Each cycle reassesses the existing register against the current evidence and assumption state.

### Resolved risks remain in history
When a risk is resolved — because evidence has changed, an assumption has been revised, or an event has occurred that definitively addressed the risk — the entry is marked as resolved, not deleted. The revision history records why and when.

### New evidence may strengthen or weaken a risk
A new earnings report may provide evidence that a business risk is materialising — or that it was overstated. Either direction is valid. The risk register is updated when new evidence warrants, and the revision history records the change.

### Missing evidence may itself represent risk
If the evidence needed to assess a risk does not exist, that absence is not treated as evidence that the risk is low. An incomplete evidence set around a key assumption is itself a risk indicator. It is surfaced as a risk with evidence quality `incomplete` or `weak`.

### Monitoring supports revision, not prediction
The purpose of monitoring triggers is to identify when a risk review should be prompted — not to predict outcomes. Atlas does not forecast the probability of a monitoring trigger firing. It identifies what to watch and prompts review when conditions arise.

---

## Relationship Diagram

```
Evidence Assembly  (Stage 4)
 ↓
Evidence Quality Review  (Stage 5)
 ↓
Assumption Review  (Stage 6)
 ↓
Risk Review  (Stage 7)
 ↓
Value Scenario Review  (Stage 8)
 ↓
Weekly Review  (Stage 9)
```

The risk register produced by Stage 7 is a primary input to:
- **Value Scenario Review (Stage 8):** risks inform scenario case selection, range width, and uncertainty notes
- **Weekly Review (Stage 9):** active risks generate monitoring items, open questions, and reasons to wait

---

## Future Extension Points

When new evidence sources become available, they supply additional inputs to the risk identification and evidence linking steps without changing the Risk Review architecture.

| Future source | How it extends Risk Review |
|---|---|
| AI reasoning | May identify risks not visible from explicit evidence and assumptions; must be labelled AI-derived; subject to same evidence-linkage requirements |
| SEC filings | Provide primary evidence for business, financial, regulatory, and management risk assessment |
| Earnings transcripts | Provide management commentary evidence for monitoring trigger assessment |
| Broker imports | Provide current portfolio data for portfolio construction risk assessment |
| Market data | Provide evidence for valuation risk and macro risk assessments |
| OCR documents | Convert physical documents to evidence before risk assessment |
| Collaboration | Multiple users may contribute to the risk register; conflict detection applies across contributors |

**Principle:** No future source bypasses Risk Review. Future sources supply evidence and assumptions. Risk Review applies the same identification, classification, evidence-linking, and monitoring-trigger process regardless of evidence source.

---

## What This Document Is Not

- This is not a probability model.
- This is not a Value-at-Risk (VaR) calculation.
- This is not a Monte Carlo simulation.
- This is not a scoring system.
- This is not a recommendation framework.
- This is not a forecast.
- This is not a runtime implementation.

It is a definition of how Atlas identifies, organises, traces, and monitors risks before any Value Scenario Review or Weekly Review is produced.

---

## Sprint 285 Target

**Define Decision Review V1**

After Atlas has assembled evidence, evaluated its quality, surfaced assumptions, and identified risks, the next logical step is to define how those elements are synthesised into a structured decision review before any Weekly Review or Snapshot Draft is produced. The Decision Review should explain why Atlas reaches its structured judgment while remaining recommendation-free.

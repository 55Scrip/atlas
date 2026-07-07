# Assumption Review V1

**Created:** 2026-07-08 (Sprint 283)
**Status:** DEFINED — architecture specification. No runtime implementation.
**Depends on:** [docs/EvidenceAssemblyV1.md](EvidenceAssemblyV1.md), [docs/EvidenceQualityReviewV1.md](EvidenceQualityReviewV1.md), [docs/InvestmentReviewPipelineV1.md](InvestmentReviewPipelineV1.md)
**Pipeline stage:** Stage 6 — Assumption Review

---

## Purpose

This document defines the canonical Assumption Review process for Atlas.

It answers:

> **Which assumptions exist? Which evidence supports them? Which assumptions lack support? Which assumptions have changed?**

It does not answer:

> ~~Which investment should the user choose?~~

Evidence answers: **What do we know?**
Assumptions answer: **What must be true for the investment thesis to remain valid?**

Atlas must make assumptions visible. They must never remain hidden. A hidden assumption is an unexamined risk.

---

## Position in the Pipeline

```
Evidence Assembly  (Stage 4)
 ↓
Evidence Quality Review  (Stage 5)
 ↓
Assumption Review  (Stage 6)  ←  defined in this document
 ↓
Risk Review  (Stage 7)
 ↓
Value Scenario Review  (Stage 8)
 ↓
Weekly Review  (Stage 9)
```

Assumption Review is the stage where the gap between evidence and conclusion becomes explicit. It surfaces what must be believed — beyond what is known — for the investment thesis to hold.

---

## Explicit vs Implicit Assumptions

Assumptions fall into two categories that must be treated differently.

### Explicit Assumptions

Assumptions the user or source has directly stated.

**Examples:**
```
Revenue growth remains above 15% annually.

Operating margins expand to 25% over three years.

Management executes the capital allocation plan as described.

The competitive position in cloud infrastructure remains durable.
```

Explicit assumptions are identified by extraction — they are present in research notes, journal entries, or scenario descriptions and can be quoted directly.

### Implicit Assumptions

Assumptions embedded in the framing, comparisons, or projections that have not been stated directly.

**Examples:**
```
"The competitive position will remain unchanged."
(implied when a thesis uses historical market share without addressing competitive dynamics)

"The business model is scalable."
(implied when a thesis projects margin expansion without addressing operational constraints)

"Management will continue its current strategy."
(implied when future projections assume continuity without addressing leadership or succession risk)

"The regulatory environment remains stable."
(implied when a thesis does not address policy or compliance risk)
```

Implicit assumptions are identified by inference — they are not stated but must be true for the thesis to hold. Surfacing implicit assumptions is one of the most important functions of Assumption Review.

**Atlas's role:** Atlas surfaces implicit assumptions. It does not resolve them. It does not decide whether they are correct. It makes them visible so the user can evaluate them.

---

## Assumption Categories

### 1. Business Assumptions

**Purpose:** Assumptions about how the company operates, earns revenue, and creates value.

**Examples:**
- Revenue growth trajectory remains consistent with recent history
- The core product or service maintains its value proposition
- Customer retention rates remain stable
- Unit economics improve with scale

**Evidence required:** Company reports, earnings commentary, customer metrics, product announcements.

**Common failure modes:**
- Assuming growth rates are permanent when they reflect a cyclical or one-time tailwind
- Assuming product-market fit is durable when competitive alternatives are emerging
- Extrapolating recent quarters without accounting for compounding difficulty at scale

---

### 2. Financial Assumptions

**Purpose:** Assumptions about revenue, margins, cash generation, and capital structure.

**Examples:**
- Revenue grows at X% annually over the scenario horizon
- Operating margins expand from current levels to Y% over Z years
- Free cash flow conversion remains above 80% of net income
- Debt levels remain manageable relative to earnings

**Evidence required:** Historical income statements, management guidance, earnings transcripts, comparable company benchmarks.

**Common failure modes:**
- Projecting margin improvement without identifying the mechanism
- Assuming revenue growth without tracking customer cohort behaviour
- Ignoring the impact of capex cycles on free cash flow conversion

---

### 3. Competitive Assumptions

**Purpose:** Assumptions about the company's position relative to competitors.

**Examples:**
- Market share is stable or growing
- The competitive moat (network effect, switching cost, scale, IP) remains intact
- New entrants cannot replicate the core advantage within the scenario horizon
- Pricing power is maintained

**Evidence required:** Market share data, product launch observations, customer commentary, competitor announcements.

**Common failure modes:**
- Assuming a moat is durable when its basis has not been re-examined recently
- Ignoring well-funded new entrants because they have not yet caused observable damage
- Conflating revenue growth with competitive position strength

---

### 4. Management Assumptions

**Purpose:** Assumptions about leadership quality, strategic execution, and capital allocation.

**Examples:**
- Management continues to allocate capital to high-return opportunities
- The current leadership team remains in place
- Strategic priorities remain consistent with the stated long-term plan
- Shareholder alignment is maintained

**Evidence required:** Management track record, capital allocation history, earnings call commentary, compensation structure.

**Common failure modes:**
- Assuming management quality from a single good period
- Ignoring misaligned incentive structures
- Treating stated strategy as executed strategy without tracking delivery

---

### 5. Industry Assumptions

**Purpose:** Assumptions about the structure, growth, and dynamics of the industry.

**Examples:**
- The total addressable market continues to grow
- Industry pricing remains rational
- Regulatory barriers to entry remain in place
- The industry does not undergo structural disruption within the scenario horizon

**Evidence required:** Industry reports, regulatory filings, sector research, historical cycles.

**Common failure modes:**
- Assuming the industry will remain structurally stable without examining technological or regulatory trends
- Conflating near-term growth with long-term structural health
- Overlooking cyclical patterns by focusing only on recent conditions

---

### 6. Macro Assumptions

**Purpose:** Assumptions about the broader economic environment that affect the thesis.

**Examples:**
- Interest rates remain within a range that supports current valuations
- The currency basis for international revenue does not significantly shift
- Consumer spending conditions remain broadly stable
- No recessionary shock occurs within the scenario horizon

**Evidence required:** Central bank communications, macroeconomic indicators, prior cycle behaviour, company-specific macro sensitivity disclosures.

**Common failure modes:**
- Ignoring rate sensitivity when valuations depend on low discount rates
- Treating favourable macro conditions as a permanent baseline
- Not stress-testing against a plausible adverse macro scenario

---

### 7. Valuation Assumptions

**Purpose:** Assumptions about how the market prices the company relative to its fundamentals.

**Examples:**
- The earnings multiple remains within the current or historical range
- Multiple expansion occurs as growth accelerates
- The market assigns credit for long-duration cash flows
- Relative valuation to peers does not compress

**Evidence required:** Historical multiple ranges, comparable company valuations, earnings growth versus multiple analysis.

**Common failure modes:**
- Assuming multiple expansion will occur without identifying the catalyst
- Using a peer group that is not comparable on duration or quality
- Treating current valuation as the permanent baseline rather than as a point in a cycle

---

### 8. Portfolio Assumptions

**Purpose:** Assumptions about how a holding interacts with the rest of the portfolio.

**Examples:**
- The position size is appropriate given the current level of evidence quality
- Concentration within a sector or theme remains acceptable
- The holding's correlation to other positions does not create undue macro or sector exposure
- The position's contribution to overall portfolio risk is understood

**Evidence required:** Current portfolio composition, position sizes, sector exposures, historical behaviour during stress periods.

**Common failure modes:**
- Evaluating a holding in isolation without accounting for portfolio context
- Ignoring correlation risk between nominally different positions
- Allowing a position to grow beyond its evidence-justified size through price appreciation without review

---

### 9. Behavioural Assumptions

**Purpose:** Assumptions about how the user or market participants will behave.

**Examples:**
- The user will review the position at the next scheduled earnings event
- Market participants will price in new information within a reasonable time horizon
- The user will not change the position before the thesis has had time to develop
- Panic selling by other market participants creates a temporary opportunity

**Evidence required:** User's own investment history (from Decision Journal), market behaviour during comparable periods.

**Common failure modes:**
- Assuming the user will hold through volatility without examining their own past behaviour
- Assuming market mispricings will be corrected on a defined timeline
- Not accounting for how emotional states at time of review may differ from time of decision

---

### 10. User Assumptions

**Purpose:** Assumptions specific to the user's personal situation, goals, and constraints that affect the relevance of the thesis.

**Examples:**
- The investment horizon is consistent with the scenario timeframe
- The user's risk tolerance is appropriate for the scenario range presented
- The user has the liquidity to hold through volatility
- Tax or structural constraints do not change the effective return

**Evidence required:** User's investor profile, prior stated preferences, current financial situation as the user has described it.

**Common failure modes:**
- Applying a long-duration thesis to a user with a short practical horizon
- Presenting a high-volatility scenario without acknowledging the user's stated tolerance
- Ignoring structural constraints (tax, liquidity, account type) that affect outcomes

---

## Assumption Review Flow

The following flow is deterministic. No AI is required. Given the same evidence set, it produces the same assumption register.

```
Evidence Set  (from Stage 4 and Stage 5)
 ↓
Extract Assumptions
 (identify explicit assumptions from user material;
  identify implicit assumptions from framing and projections)
 ↓
Link Evidence
 (map each assumption to the evidence items that support or challenge it)
 ↓
Identify Unsupported Assumptions
 (flag assumptions with no supporting evidence)
 ↓
Identify Conflicting Assumptions
 (flag assumptions that contradict each other or contradict evidence)
 ↓
Surface Open Questions
 (generate questions for each unsupported or conflicting assumption)
 ↓
Identify Revision Candidates
 (flag assumptions that have changed or are due for re-examination)
 ↓
Risk Review  (Stage 7)
 (assumption register is a primary input to risk identification)
```

Each step produces a structured output. No step produces a recommendation. The assumption register — the output of Assumption Review — is a first-class document that travels through every downstream stage.

---

## Challenging Assumptions

Structured challenge of assumptions is not pessimism. It is how investment reasoning becomes more durable.

For every material assumption, Atlas surfaces the following questions:

**Evidence questions:**
- What evidence directly supports this assumption?
- What evidence contradicts or qualifies this assumption?
- What is the freshness of the supporting evidence?
- Is the supporting evidence primary or secondary?

**Invalidation questions:**
- What single event or change would invalidate this assumption?
- What would need to be true for this assumption to fail within the scenario horizon?
- Which assumptions depend on this assumption being true?

**Review trigger questions:**
- What new information should prompt a review of this assumption?
- How frequently should this assumption be re-examined?
- Has this assumption been challenged in a prior review? What changed?

**Dependency questions:**
- Which other assumptions does this assumption rely on?
- If this assumption fails, which downstream assumptions also fail?
- Are there assumption clusters where the failure of one makes others implausible?

These questions are not investment advice. They are structured thinking tools. They do not produce recommendations. They produce clarity.

---

## Relationship to Evidence

Every assumption in the register should be linked to evidence where possible.

| Assumption state | Meaning | Action |
|---|---|---|
| Evidence-supported | One or more evidence items directly support the assumption | Document the link; assess evidence quality |
| Partially supported | Some evidence exists but gaps remain | Flag the gap; generate follow-up question |
| Unsupported | No evidence found in the assembled set | Mark as unsupported; surface in open questions |
| Contradicted | Evidence exists that directly challenges the assumption | Flag as conflicting; surface in Conflict Review |
| Obsolete | The assumption was previously supported but evidence has been superseded | Flag as obsolete; recommend revision |

**Principle:** Unsupported assumptions do not disqualify a thesis — but they must remain visible. An unsupported assumption carried silently into a Value Scenario produces a scenario of unknown reliability.

---

## Downstream Relationships

### Risk Review (Stage 7)
The assumption register is the primary input to risk identification. Each unsupported, conflicting, or high-dependency assumption is a candidate for a risk item. The assumption-to-risk mapping makes the origin of each risk traceable.

### Value Scenario Review (Stage 8)
Every scenario assumption in a Value Scenario Review must correspond to an item in the assumption register. Scenario ranges are informed by assumption quality: unsupported assumptions produce wider ranges; well-supported assumptions allow narrower ranges.

### Weekly Review (Stage 9)
Unsupported assumptions generate follow-up questions. Conflicting assumptions generate open items. Revision candidates generate reasons to wait. The Weekly Review surfaces assumption health as a standing agenda item.

### Decision Journal (Stage 11)
When an assumption is revised, the prior version is preserved in the revision history. The Decision Journal records what changed, why, and what evidence prompted the change.

### Future revisions
Assumption health degrades over time. An assumption that was well-supported twelve months ago may be unsupported today if the evidence has become stale. Assumption Review is a recurring process, not a one-time classification.

---

## Examples

### Well-supported assumption

```
Assumption: "Revenue growth will remain above 15% annually."

Evidence:
  - Q1 2026 earnings: revenue grew 19% YoY (current, primary)
  - Q2 2026 earnings: revenue grew 17% YoY (current, primary)
  - Management guided full-year growth of 16–20% (current, primary)
  - User research note: "Customer expansion behaviour supports continued growth"

Evidence quality: Adequate
Assumption state: Evidence-supported
Open questions: None urgent. Review after next earnings.
```

---

### Unsupported assumption

```
Assumption: "The competitive moat in cloud infrastructure is durable."

Evidence:
  - No company facts entry for competitive analysis
  - Research notes mention competition but contain no specific assessment
  - No earnings commentary on competitive positioning found

Evidence quality: Incomplete
Assumption state: Unsupported
Open questions:
  - What specific advantages constitute the moat?
  - Have any major competitors entered the user's target segment in the last 12 months?
  - Has management addressed competitive dynamics in recent calls?
```

---

### Conflicting assumption

```
Assumption A: "Operating margins will expand to 25% over three years."
  Supporting evidence: Management guidance (Q2 2026 call)

Assumption B: "The business requires continued high infrastructure investment."
  Supporting evidence: User research note: "capex growing faster than revenue"

Status: Conflicting
  Margin expansion and accelerating capex are in tension.
  Both assumptions are present. Neither is discarded.
  Conflict is surfaced in Risk Review (Stage 7).
Open questions:
  - Has management explained how capex will moderate as the business scales?
  - Is the margin expansion timeline contingent on a capex reduction that has not been confirmed?
```

---

### Revised assumption

```
Original assumption (18 months ago):
  "Revenue growth remains above 20% annually."
  Evidence: Three quarters of 20–25% growth (strong, primary)

Current assumption:
  "Revenue growth remains above 15% annually."
  Evidence: Last two quarters: 16% and 17% growth (current, primary)
  Management revised guidance down from 20–24% to 16–20%

Revision history:
  2025-01-15: Set at >20% — supported by three consecutive quarters
  2026-07-08: Revised to >15% — management guidance reduced; growth decelerated

Status: Revised. Prior version preserved. Direction: downward revision.
```

---

### Obsolete assumption

```
Assumption: "The company operates primarily in North America."
  Evidence at time of assumption: 2022 annual report (North America: 78% of revenue)

Current state:
  2025 annual report: North America now 51% of revenue; EMEA 33%; APAC 16%
  Assumption no longer reflects the business.

Status: Obsolete
Action: Update assumption to reflect international diversification.
  Prior version preserved in revision history.
  Currency and regulatory assumptions must be revisited.
```

---

## Canonical Principles

### Assumptions are not facts
An assumption may be well-supported by evidence. It is still an assumption. Evidence gives it probability; it does not make it certain. This distinction is preserved throughout the pipeline.

### Assumptions should be revisited
An assumption that was valid twelve months ago may not be valid today. Assumption Review is a recurring process. Every review cycle re-examines material assumptions against the current evidence set.

### Assumptions may conflict
Two assumptions may be simultaneously present in the register and in direct tension. Atlas does not silently resolve conflicts. Both assumptions remain visible. The conflict is surfaced in Risk Review.

### Assumptions may become obsolete
When evidence changes materially, previously valid assumptions may no longer apply. Obsolete assumptions are flagged and preserved. The user decides whether to revise or retire them.

### Assumptions should be evidence-linked
Every assumption in the register should reference the evidence items that support or challenge it. Unlinked assumptions are not invalid — but their unsupported status must be visible.

### Uncertainty is acceptable
An assumption register with unsupported or conflicting assumptions is a valid and informative register. It accurately reflects what is unknown. An artificially clean assumption register is more dangerous than an honest incomplete one.

### Revisions preserve history
When an assumption is revised, the prior version is preserved with its date, evidence basis, and reason for revision. History is not overwritten. The revision trail supports learning.

### Challenged assumptions strengthen decisions
An assumption that has been explicitly challenged and survived the challenge is stronger than one that has never been questioned. Challenge is not adversarial — it is how assumptions develop into well-founded convictions or are correctly abandoned.

---

## Future Extension Points

When new evidence sources become available, they supply additional evidence to the assumption-linking step without changing the Assumption Review architecture.

| Future source | How it extends Assumption Review |
|---|---|
| AI reasoning | May surface implicit assumptions not visible to the user; must be labelled AI-derived; subject to same evidence-linkage requirements |
| SEC filings | Provide primary evidence for financial and business assumptions |
| Earnings transcripts | Provide management commentary evidence for strategy and guidance assumptions |
| Broker imports | Provide portfolio data evidence for portfolio assumptions |
| Market data | Provide evidence for valuation and macro assumptions |
| OCR documents | Convert physical documents to text evidence before assumption linking |
| Collaboration | Multiple users may contribute assumptions and evidence; conflict detection applies across contributors |

**Principle:** No future source bypasses Assumption Review. Future sources supply evidence. Assumption Review applies the same extraction, linking, and challenge process regardless of evidence source.

---

## What This Document Is Not

- This is not a scoring model for assumption quality.
- This is not an investment recommendation framework.
- This is not a forecast.
- This is not a valuation model.
- This is not a runtime implementation.

It is a definition of how Atlas identifies, documents, links, challenges, and revises assumptions before any risk review or value scenario is produced.

---

## Sprint 284 Target

**Define Risk Review V1**

After Atlas has assembled evidence, evaluated its quality, and made assumptions explicit, the next logical step is to define how risks are identified, categorised, linked back to assumptions, and carried forward into Value Scenario Review and Weekly Review — without introducing predictions or investment recommendations.

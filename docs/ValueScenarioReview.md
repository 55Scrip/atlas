# Value Scenario Review

**Created:** 2026-07-07 (Sprint 274)
**Status:** DEFINED — product specification complete. Data model specified in Sprint 275. Schema dataclasses implemented in Sprint 276. Example fixtures added in Sprint 277. Read-only validation CLI added in Sprint 278.
**Depends on:** [docs/AtlasProductPositioningV1.md](AtlasProductPositioningV1.md)
**Data model:** [docs/ValueScenarioDataModel.md](ValueScenarioDataModel.md) (Sprint 275)
**Schema implementation:** `atlas/value_scenario/schema.py` (Sprint 276)

---

## Purpose

Value Scenario Review defines how Atlas may eventually help users understand
possible value and return ranges for holdings and portfolios.

Users should be able to understand how much value potential, downside risk, and
scenario-dependent return range a holding or portfolio may have over different
time horizons.

Atlas should also explain what assumptions drive the range and what events or
evidence would cause the range to change.

This document defines the concept, principles, components, safe language,
prohibited language, and future implementation phases.

No valuation calculations, market data, scoring, forecasts, probability models,
or AI calls are implemented in this sprint.

---

## Product Principle

Atlas should help users understand possible value ranges, not pretend to know the future.

Atlas does not issue single-point price targets or action calls.

Atlas may estimate scenario-based value and return ranges when assumptions,
evidence quality, uncertainty, and change triggers are shown clearly.

The goal is structured judgment, not certainty.

Atlas must not become a prediction system, trading product, signal product, or
execution assistant by adding value scenario support.

---

## Non-Goals

The following are explicitly out of scope for Value Scenario Review:

- single-point price targets as primary output
- guaranteed return estimates
- execution instructions
- personalized financial advice
- trading signals
- momentum indicators
- AI-generated forecasts
- real-time market data
- news-driven alerts
- broker integration
- portfolio rebalancing recommendations
- urgency framing
- certainty framing
- prediction certainty

Atlas wins only if users feel calmer, clearer, and more in control after using
it. Urgency and certainty framing work against this.

---

## Relationship to Atlas Positioning

Value Scenario Review supports Atlas's role as a judgment system.

From `docs/AtlasProductPositioningV1.md`:

> Atlas is a private investment workspace for people who care about capital.
> It turns messy investment input into structured judgment.
> It helps users see what is missing, what needs more evidence, what should be
> revisited, and when no action is warranted.

Value Scenario Review extends this by allowing users to structure their thinking
about possible futures — not by predicting outcomes.

It should help users understand assumptions, ranges, risks, and change triggers.

It must not turn Atlas into a prediction system, trading product, or signal
product.

The emotional outcome remains the same: calm, clarity, and control — not
excitement, urgency, or certainty.

---

## Scenario-Based Value Ranges

Atlas may support scenario-based value and return ranges when:

1. The range is derived from user-provided or user-confirmed assumptions.
2. Evidence quality is displayed alongside the range.
3. Uncertainty is shown clearly.
4. Change triggers are identified.
5. No single-point target is presented as the primary output.
6. No action call accompanies the range.

A scenario range is not a prediction. It is a structured way to make
assumptions explicit and to show how different outcomes map to different
evidence states.

### Range types

- `bear_case_range` — range under adverse scenario assumptions
- `base_case_range` — range under current reasonable assumptions
- `bull_case_range` — range under favorable scenario assumptions
- `downside_range` — estimated downside from current level
- `upside_range` — estimated upside from current level
- `uncertainty_band` — additional width added when evidence quality is weak,
  incomplete, outdated, or conflicting

If an implied midpoint is discussed, it must be secondary to the range and
clearly derived from scenario assumptions. It must not be presented as a
price target.

---

## Holding-Level Review

For a single holding, Atlas may eventually show:

- current context (holding name, weight, current evidence summary)
- short-term scenario range
- medium-term scenario range
- long-term scenario range
- bear case
- base case
- bull case
- key drivers
- key risks
- evidence quality
- confidence level
- change triggers (what would change the range)
- last revision reason

Example safe holding-level statement:

> Given the current assumptions, the 12-month scenario range is approximately
> +8% to +18% in the base case, with wider downside and upside ranges
> depending on margin durability, revenue growth, valuation multiple, and
> market conditions.

This statement must not be presented as a promise, guarantee, or certainty.
It is a structured expression of scenario assumptions and their range
implications.

---

## Portfolio-Level Review

At portfolio level, Atlas may eventually show:

- portfolio scenario range (aggregate weighted contribution)
- weighted contribution by holding
- main upside drivers
- main downside drivers
- concentration sensitivity
- valuation sensitivity
- momentum exposure
- evidence gaps
- positions with most range impact
- positions requiring scenario revision

Example safe portfolio-level statement:

> The portfolio's scenario range is most sensitive to semiconductor exposure,
> valuation multiples, and earnings revision risk. Several positions have wide
> ranges because the available evidence is incomplete.

Portfolio-level scenarios inherit the same constraints as holding-level
scenarios. They must not imply predictive certainty or execution instructions.

---

## Time Horizons

Atlas defines three scenario time horizons:

| Horizon | Duration |
|---|---|
| Short term | 1–3 months |
| Medium term | 6–12 months |
| Long term | 3–5 years |

### Short-term range sensitivity

Short-term ranges are more sensitive to:

- sentiment
- positioning
- liquidity
- interest rates
- catalysts
- news flow
- earnings announcements

Short-term ranges will typically be wide because near-term outcomes depend
heavily on market dynamics outside the user's control or evidence base.

### Medium-term range sensitivity

Medium-term ranges are more sensitive to:

- earnings revisions
- valuation multiples
- company execution
- market regime
- competitive developments
- management quality
- margin trends

### Long-term range sensitivity

Long-term ranges are more sensitive to:

- business quality
- revenue growth
- margin durability
- capital allocation
- competitive position
- valuation discipline
- structural industry trends
- management track record

Long-term ranges are more anchored to fundamental assumptions and less driven
by near-term market dynamics.

---

## Scenario Components

Possible scenario components that may inform value and return ranges:

- revenue growth assumptions
- earnings growth assumptions
- margin assumptions
- valuation multiple assumptions
- balance sheet risk
- capital allocation quality
- competitive position
- business quality
- market sentiment
- momentum
- macro and rate sensitivity
- currency effect
- evidence quality
- uncertainty level

These components are not calculated automatically. They are inputs that the
user provides, confirms, or updates. Atlas structures and displays them.

---

## Assumptions

Atlas must make assumptions explicit.

A scenario range without explicit assumptions is not a scenario range. It is
an unchecked prediction.

Atlas should show:

- what assumptions drive the bear, base, and bull cases
- which assumptions have the most range impact
- which assumptions are supported by strong evidence
- which assumptions are speculative or unverified

The user should be able to challenge, revise, or reject any assumption. Atlas
tracks the assumption state, not a fixed forecast.

---

## Evidence Quality

Evidence quality describes how well the available evidence supports the current
scenario assumptions.

### Evidence quality labels

| Label | Meaning |
|---|---|
| `strong` | Evidence is current, consistent, and well-sourced |
| `adequate` | Evidence supports the assumptions but has some gaps |
| `incomplete` | Key evidence is missing; assumptions are partially unsupported |
| `weak` | Evidence is thin, indirect, or mostly speculative |
| `outdated` | Evidence exists but may no longer reflect current conditions |
| `conflicting` | Available evidence points in multiple directions |

Scenario ranges should become wider when evidence quality is weak, incomplete,
outdated, or conflicting.

A scenario with weak evidence is not invalid. It is a signal that the user
should seek more evidence before acting.

---

## Confidence

Confidence describes confidence in the scenario structure and evidence quality,
not certainty about future returns.

### Confidence labels

| Label | Meaning |
|---|---|
| `low` | Assumptions are speculative; evidence is weak or missing |
| `medium` | Assumptions are reasonable; evidence is adequate |
| `high` | Assumptions are well-supported; evidence is strong |
| `unknown` | Confidence cannot be assessed with available information |

Confidence must never be presented as certainty about investment outcomes.

A high-confidence scenario is a well-structured scenario with strong evidence.
It is not a guarantee.

---

## Uncertainty

Uncertainty should always be shown alongside scenario ranges.

Sources of uncertainty include:

- evidence quality
- macro and rate environment
- market sentiment
- company execution risk
- competitive disruption risk
- regulatory risk
- currency risk
- assumptions not yet tested by evidence
- time horizon length

Wide uncertainty bands are not failures. They are honest representations of
what is known and what is not.

Atlas should reward intellectual honesty. A wide, well-labeled range is better
than a narrow, overconfident range.

---

## Change Triggers

Change triggers are events or evidence updates that would cause a scenario
range to be revised.

### Defined change triggers

- earnings report
- guidance change
- revenue growth acceleration
- revenue growth deceleration
- margin surprise (positive or negative)
- valuation multiple expansion
- valuation multiple compression
- balance sheet deterioration
- balance sheet improvement
- major product or strategy update
- regulatory change
- macro or rate regime change
- currency movement
- thesis evidence improved
- thesis evidence weakened

Change triggers must be identified in advance. A scenario without change
triggers is a static prediction disguised as a range.

The purpose of change triggers is to define the conditions under which a
scenario should be revisited. They turn a scenario into a living thesis.

---

## Scenario Revision

Atlas should eventually track scenario revisions.

A revision records what changed, why it changed, and what the previous range
was.

Example revision:

```
Previous scenario range (12-month base case):
+15% to +25%

Updated scenario range (12-month base case):
+5% to +15%

Reason for revision:
- margin assumptions reduced following Q3 earnings miss
- evidence quality weakened: margin durability now conflicting
- valuation sensitivity increased: multiple has compressed

Revision date: 2026-07-07
```

Revision tracking serves the user, not the product.

The purpose is to create a living thesis that evolves with evidence — not a
static prediction that hardens into a commitment or a regret.

---

## Safe Language

The following language is allowed in Value Scenario Review outputs:

- scenario range
- value range
- return range
- possible upside range
- possible downside range
- base case range
- bear case range
- bull case range
- assumptions
- evidence quality
- uncertainty
- confidence in structure
- change trigger
- revision reason
- reason to revisit
- reason to wait
- no action warranted
- the range is approximately
- depending on assumptions
- if the assumptions hold
- subject to revision
- evidence is incomplete
- evidence is conflicting
- wide uncertainty band
- the scenario assumes
- what would change this

---

## Prohibited Language

The following language is not allowed in Value Scenario Review outputs:

- single-point target as primary output (e.g. "the target is 250")
- guaranteed return
- certain upside
- must act
- urgent action required
- buy now
- sell now
- execution instruction
- personalized financial advice
- prediction certainty
- will reach
- will return
- the stock will
- we expect the price to
- entry point
- exit point
- outperform
- price target
- strong buy

Also prohibited: any framing that implies Atlas knows the future or that the
user should act immediately based on the range.

---

## Example Outputs

The following examples are illustrative only. They do not reflect real-time
market data. They do not imply current factual accuracy for any real security.
Figures are hypothetical.

---

### Example 1 — Holding-Level 12-Month Scenario

**Holding:** Hypothetical Industrial Holdings Co. (ticker: HIHC)

**Scenario horizon:** 12 months (medium term)

**Evidence quality:** Adequate

**Confidence:** Medium

**Bear case range:** –12% to –5%
Assumptions: Revenue growth slows to 3%, margin pressure from input costs,
valuation multiple contracts from 18x to 15x.

**Base case range:** +8% to +18%
Assumptions: Revenue growth of 7–9%, stable margins at 22–24%, valuation
multiple holds at 17–19x.

**Bull case range:** +20% to +35%
Assumptions: Revenue growth accelerates to 12%+, margin expansion to 26%+,
multiple expands to 21–22x on improved execution.

**Key drivers:** Revenue growth, margin durability, valuation multiple

**Key risks:** Input cost pressure, customer concentration, rate sensitivity

**Uncertainty:** Moderate. Evidence on margin durability is adequate but not
strong. Forward guidance has not been reaffirmed.

**Change triggers:**
- Q3 earnings report and margin guidance
- Major customer contract renewal
- Rate environment shift affecting valuation multiples

> Given the current assumptions, the 12-month scenario range is approximately
> +8% to +18% in the base case, with wider downside and upside ranges
> depending on margin durability, revenue growth, valuation multiple, and
> market conditions. This is not a guarantee. Evidence quality is adequate
> but not strong. Revision is expected after the next earnings report.

---

### Example 2 — Long-Term Holding Scenario

**Holding:** Hypothetical Global Water Infrastructure Fund (ticker: GWIF)

**Scenario horizon:** 3–5 years (long term)

**Evidence quality:** Incomplete

**Confidence:** Low to medium

**Bear case range:** –20% to –5% (cumulative over 3–5 years)
Assumptions: Revenue growth stagnates, margin pressure persists, valuation
multiple compresses on weak execution.

**Base case range:** +30% to +65% (cumulative over 3–5 years)
Assumptions: Revenue grows at 6–8% annually, margins improve gradually to
28%+ as scale benefits emerge, valuation multiple holds or expands modestly.

**Bull case range:** +70% to +120% (cumulative over 3–5 years)
Assumptions: Thesis on water infrastructure demand proves well-founded, revenue
growth accelerates to 10%+, margins expand meaningfully, multiple re-rates.

**Business quality:** Adequate. Infrastructure assets provide defensible revenue
base. Capital allocation history is acceptable but not exceptional.

**Margin durability:** Uncertain. Evidence on long-term margin trends is
incomplete.

**Competitive position:** Moderate. No clear dominant market share in key
regions.

**Uncertainty:** Wide. Long-term ranges are more uncertain than medium-term
ranges because assumptions must hold over many years across multiple
business cycles.

**Change triggers:**
- New infrastructure contract announcements
- Margin trajectory through the next 2–3 earnings cycles
- Regulatory environment shifts in key markets
- Capital allocation decisions (M&A, buybacks, dividends)
- Evidence on competitive position in growth markets

> The 3–5 year scenario range is wide because the available evidence is
> incomplete. The water infrastructure thesis is plausible but not yet
> well-supported by a strong track record of execution. The range will
> narrow as margin durability evidence accumulates. This is a reason to
> revisit, not a reason to act immediately.

---

### Example 3 — Portfolio-Level Scenario

**Portfolio:** Hypothetical concentrated growth portfolio (7 positions)

**Scenario horizon:** 12 months (medium term)

**Portfolio scenario range (base case):** +5% to +16% (portfolio-level)

**Main upside drivers:**
1. Semiconductor position — highest portfolio weight; bull case could
   contribute +6–8% to portfolio return
2. Industrial automation position — margin expansion thesis has moderate
   evidence support
3. Global water infrastructure — improving evidence quality since last review

**Main downside drivers:**
1. Rate sensitivity — 3 of 7 positions have high valuation multiples sensitive
   to rate increases
2. Earnings revision risk — 2 positions have guidance that has not been
   reaffirmed for next quarter
3. Concentration — semiconductor exposure exceeds 30% of portfolio weight

**Evidence gaps:**
- Forward guidance reaffirmation outstanding for 2 positions
- Margin durability evidence is incomplete for 3 positions
- Competitive position evidence is weak for 1 position

**Positions requiring scenario revision:**
- Industrial automation position: last revision was 6 months ago; margin
  assumptions have not been updated following recent earnings
- Global water infrastructure: evidence quality has improved; base case range
  may be outdatable upward if next earnings support the thesis

> The portfolio's scenario range is most sensitive to semiconductor exposure,
> valuation multiples, and earnings revision risk. Several positions have wide
> ranges because the available evidence is incomplete. Three positions require
> scenario revision before this review should be considered current.

---

## Future Implementation Phases

Value Scenario Review will be implemented in phases.

No implementation is done in Sprint 274.

| Phase | Description |
|---|---|
| Phase 0 | Product specification (this sprint) |
| Phase 1 | Scenario data model specification |
| Phase 2 | Scenario schema dataclasses |
| Phase 3 | Manual scenario input fixtures |
| Phase 4 | Read-only scenario validation |
| Phase 5 | Read-only scenario summary renderer |
| Phase 6 | Portfolio-level scenario aggregation |
| Phase 7 | Revision tracking |
| Phase 8 | Optional market data integration, only if explicitly approved later |

Each phase builds on the previous. No phase should skip the documentation and
specification step.

Market data integration (Phase 8) is explicitly deferred and requires separate
approval. It should not be assumed or pre-built.

---

## Open Questions

1. **Scenario input format:** Should users enter scenario assumptions via CLI,
   structured JSON, or a future workspace card? How should assumptions be
   captured without an AI classifier?

2. **Range display format:** Should ranges be shown as percentages, absolute
   values, or both? What currency handling is needed for multi-currency
   portfolios?

3. **Revision cadence:** How frequently should users be prompted to revise
   scenarios? Should Atlas suggest revision when change triggers are detected
   from user input?

4. **Portfolio aggregation method:** What weighting method should Atlas use to
   aggregate holding-level ranges to portfolio level? How should Atlas handle
   positions with no scenario defined?

5. **Evidence quality assessment:** Who assesses evidence quality — the user,
   or Atlas from structured input? How does this connect to the existing
   uncertainty and missing field model in the Temporary Workspace schema?

6. **Relationship to Weekly Review:** Should Value Scenario Review integrate
   with the existing Weekly Review output sections, or be a separate review
   type?

7. **Safe midpoint display:** If a midpoint is implied by bear/base/bull ranges,
   should Atlas show it? If so, under what conditions and with what language?

---

## Recommended Next Sprint

**Sprint 275: Define Value Scenario data model**

After the Value Scenario Review concept is specified, Atlas should define the
data model for scenario ranges, assumptions, evidence quality, confidence,
change triggers, and revision history before any implementation.

This should remain a documentation and specification sprint. It should not
implement calculations, market data, scoring, or any runtime behavior.

This continues the pattern established by Sprint 268 (Temporary Workspace data
model) and Sprint 269 (card rendering contract): specify the architecture
before building it.

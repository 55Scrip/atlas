# Value Scenario Data Model

**Created:** 2026-07-07 (Sprint 275)
**Status:** DEFINED — data model specification only. No implementation in this sprint.
**Depends on:** [docs/ValueScenarioReview.md](ValueScenarioReview.md)
**Depends on:** [docs/AtlasProductPositioningV1.md](AtlasProductPositioningV1.md)

---

## Purpose

This document specifies the data model for Atlas Value Scenario Reviews.

It defines the objects, fields, canonical values, relationships, and validation
expectations that will guide future schema dataclass implementation.

No dataclasses, validators, calculations, or schemas are implemented in this
sprint.

---

## Non-Goals

- No dataclass implementation
- No JSON schema implementation
- No valuation calculations
- No forecasting or probability weighting
- No scoring
- No market data integration
- No portfolio return engine
- No AI or LLM calls
- No external API calls
- No CLI commands
- No runtime behavior changes

---

## Model Principles

The following principles govern the Value Scenario data model:

1. **Ranges, not predictions.** The model represents scenario-based ranges, not
   predictions. No object or field implies certainty about future returns.

2. **Ranges require grounding.** Every range must be connected to assumptions,
   evidence quality, uncertainty, and change triggers.

3. **No required single-point targets.** The model must not require
   single-point price targets. `lower_percent` and `upper_percent` may be
   equal only when representing a known realized value later — not for
   forward-looking scenario outputs.

4. **Confidence describes structure.** Confidence describes confidence in the
   scenario structure and supporting evidence, not certainty about future
   returns.

5. **Revisions explain change.** Revisions must explain what changed and why.
   They must not imply that prior uncertainty was avoidable or that the updated
   range is certain.

6. **Portfolio scenarios preserve uncertainty.** Portfolio-level scenarios
   should preserve holding-level uncertainty rather than hiding it behind
   an aggregate number.

7. **Canonical values remain English.** All enum-like fields use canonical
   English values. Display-layer localization is handled separately.

8. **Safety boundary is always on.** Safety fields must remain enforced in any
   future implementation.

---

## Model Overview

A Value Scenario Review contains:

- one top-level **Value Scenario Review** object per review session
- one or more **Holding Scenarios** (for `holding` or `mixed` review types)
- one optional **Portfolio Scenario** (for `portfolio` or `mixed` review types)
- a list of **Scenario Ranges** — bear, base, bull, downside, upside, and
  uncertainty band ranges per horizon per holding
- a list of **Assumptions** that ground the ranges
- a list of **Evidence Items** that support the assumptions
- a list of **Change Triggers** that define when to revise
- a list of **Scenario Revisions** that record what changed and why
- a **Safety Boundary** object that enforces Atlas's guardrails
- a **Subject** object that identifies the security or portfolio under review
- a list of **Portfolio Contributions** (portfolio scenario only)

---

## Value Scenario Review

The top-level object for a review session.

```
scenario_review_id   string         unique ID, prefix: vsr_
review_type          string         canonical: holding | portfolio | mixed
created_at           string         ISO 8601 datetime
subject              object         see Subject Model
time_horizons        array[string]  canonical horizon values included in this
                                   review
holding_scenarios    array[object]  holding-level scenarios; empty for
                                   portfolio-only reviews
portfolio_scenario   object|null    portfolio-level scenario; null for
                                   holding-only reviews
assumptions          array[object]  shared assumption list for this review
evidence_items       array[object]  shared evidence item list for this review
change_triggers      array[object]  change triggers for this review
revisions            array[object]  revision history for this review
safety_boundary      object         see Safety Boundary
```

### Review types

| Value | Meaning |
|---|---|
| `holding` | Review covers one or more individual holdings |
| `portfolio` | Review covers a portfolio as a whole |
| `mixed` | Review covers both holding-level and portfolio-level scenarios |

---

## Subject Model

Identifies what is being reviewed.

```
subject_id           string   unique ID for this subject
subject_type         string   canonical: holding | portfolio | watchlist_item
display_name         string   human-readable name
ticker               string   optional; ticker symbol if applicable
portfolio_id         string   optional; portfolio reference if applicable
source_reference     string   optional; reference to source input
```

### Subject types

| Value | Meaning |
|---|---|
| `holding` | A single security or position |
| `portfolio` | A collection of positions |
| `watchlist_item` | A security being monitored but not yet held |

---

## Time Horizon

Canonical time horizons from Sprint 274.

| Value | Display meaning |
|---|---|
| `short_term` | 1–3 months |
| `medium_term` | 6–12 months |
| `long_term` | 3–5 years |

Time horizons are referenced by field value throughout the model. They are not
objects — they are canonical string values.

---

## Scenario Range

A single range estimate within a defined case and horizon.

```
range_id             string         unique ID, prefix: rng_
horizon              string         canonical: short_term | medium_term |
                                   long_term
case_type            string         canonical: bear | base | bull | downside |
                                   upside | uncertainty_band
lower_percent        number         lower bound of the range (e.g. -12.0)
upper_percent        number         upper bound of the range (e.g. 8.0)
currency_basis       string         optional; ISO 4217 currency if relevant
assumption_ids       array[string]  IDs of assumptions that drive this range
evidence_item_ids    array[string]  IDs of evidence items supporting this range
confidence           string         canonical: low | medium | high | unknown
evidence_quality     string         canonical: strong | adequate | incomplete |
                                   weak | outdated | conflicting
uncertainty_note     string         optional; plain-language note on sources
                                   of uncertainty
```

### Case types

| Value | Meaning |
|---|---|
| `bear` | Adverse scenario: assumptions unfavorable |
| `base` | Central scenario: current reasonable assumptions |
| `bull` | Favorable scenario: assumptions favorable |
| `downside` | Estimated downside from current level |
| `upside` | Estimated upside from current level |
| `uncertainty_band` | Additional width reflecting weak or conflicting evidence |

### Range constraint

A scenario range must be a range, not a single-point target.

`lower_percent` and `upper_percent` may be equal only when representing a known
realized value later — not for forward-looking scenario outputs. In future
validation, this constraint will be enforced.

---

## Holding Scenario

Scenario review for a single holding.

```
holding_scenario_id  string         unique ID, prefix: hsc_
subject              object         Subject for this holding
ranges               array[object]  Scenario Ranges for this holding
key_drivers          array[string]  plain-language driver statements
key_risks            array[string]  plain-language risk statements
assumptions          array[string]  assumption_ids relevant to this holding
evidence_quality     string         canonical evidence quality for this holding
confidence           string         canonical confidence for this holding
change_triggers      array[string]  trigger_ids relevant to this holding
revision_ids         array[string]  IDs of revisions affecting this holding
notes                string         optional; additional context
```

---

## Portfolio Scenario

Scenario review at portfolio level. May aggregate multiple holding scenarios.

```
portfolio_scenario_id    string         unique ID, prefix: psc_
portfolio_id             string         reference to the portfolio
ranges                   array[object]  Scenario Ranges for the portfolio
weighted_contributions   array[object]  Portfolio Contributions
main_upside_drivers      array[string]  plain-language statements
main_downside_drivers    array[string]  plain-language statements
concentration_sensitivity  string       note on range sensitivity to
                                        concentration
valuation_sensitivity    string         note on range sensitivity to
                                        valuation multiples
evidence_gaps            array[string]  plain-language evidence gap statements
holdings_requiring_review  array[string]  holding IDs that need scenario
                                          revision
confidence               string         canonical confidence at portfolio level
evidence_quality         string         canonical evidence quality at portfolio
                                        level
```

---

## Portfolio Contribution

Describes a single holding's contribution to the portfolio scenario.

```
contribution_id      string   unique ID, prefix: ctb_
holding_id           string   reference to the holding
display_name         string   human-readable holding name
ticker               string   optional; ticker symbol
portfolio_weight     number   weight as decimal (e.g. 0.12 for 12%)
contribution_to_range  string optional; plain-language note on range
                               contribution
range_impact_level   string   canonical: low | medium | high | dominant
key_reason           string   plain-language explanation of the main driver
evidence_quality     string   canonical evidence quality for this contribution
```

### Range impact levels

| Value | Meaning |
|---|---|
| `low` | Small effect on the portfolio range |
| `medium` | Moderate effect |
| `high` | Significant effect |
| `dominant` | Primary driver of the portfolio range |

---

## Assumptions

Each assumption grounds one or more scenario ranges.

```
assumption_id        string         unique ID, prefix: asm_
assumption_type      string         canonical; see Assumption Types
description          string         plain-language statement of the assumption
direction            string         canonical: positive | negative | mixed |
                                   neutral | unknown
related_horizon      string         canonical time horizon this assumption
                                   applies to most; optional
related_range_ids    array[string]  range IDs this assumption feeds
evidence_item_ids    array[string]  evidence items that support this assumption
confidence           string         canonical confidence in this assumption
```

### Assumption types

| Value | What it captures |
|---|---|
| `revenue_growth` | Revenue growth rate assumptions |
| `earnings_growth` | Earnings growth rate assumptions |
| `margin` | Gross/operating/net margin assumptions |
| `valuation_multiple` | P/E, EV/EBITDA, or other multiple assumptions |
| `balance_sheet` | Debt, liquidity, and balance sheet risk assumptions |
| `capital_allocation` | Buyback, dividend, M&A, and reinvestment assumptions |
| `competitive_position` | Market share, competitive moat assumptions |
| `business_quality` | Durability, predictability, management quality |
| `market_sentiment` | Near-term sentiment and positioning assumptions |
| `momentum` | Short-term price and earnings momentum assumptions |
| `macro_rate_sensitivity` | Interest rate and macro exposure assumptions |
| `currency` | Currency and FX effect assumptions |

### Direction values

| Value | Meaning |
|---|---|
| `positive` | Assumption is favorable for the range |
| `negative` | Assumption is unfavorable for the range |
| `mixed` | Assumption has both favorable and unfavorable dimensions |
| `neutral` | Assumption does not clearly favor one direction |
| `unknown` | Direction is not yet assessable |

---

## Evidence Item

A piece of evidence that supports one or more assumptions.

```
evidence_item_id     string         unique ID, prefix: evi_
evidence_type        string         canonical; see Evidence Types
description          string         plain-language description of the evidence
source_reference     string         optional; source identifier or citation
evidence_quality     string         canonical evidence quality
freshness            string         canonical: current | recent | stale |
                                   unknown
related_assumption_ids  array[string]  assumption IDs this evidence supports
```

### Evidence types

| Value | Meaning |
|---|---|
| `company_report` | Annual or quarterly financial report |
| `earnings_call` | Earnings call transcript or summary |
| `guidance` | Forward guidance from management |
| `financial_history` | Historical financial performance data |
| `research_note` | User-provided research notes |
| `user_note` | Free-form notes entered by the user |
| `market_context` | Market regime or macro context |
| `unknown` | Source type not identified |

### Freshness values

| Value | Meaning |
|---|---|
| `current` | Evidence reflects the most recent available information |
| `recent` | Evidence is from the last quarter or reporting period |
| `stale` | Evidence is older and may not reflect current conditions |
| `unknown` | Freshness cannot be assessed |

---

## Evidence Quality

Evidence quality describes how well the available evidence supports assumptions.

| Value | Meaning |
|---|---|
| `strong` | Evidence is current, consistent, and well-sourced |
| `adequate` | Evidence supports the assumptions but has some gaps |
| `incomplete` | Key evidence is missing; assumptions are partially unsupported |
| `weak` | Evidence is thin, indirect, or mostly speculative |
| `outdated` | Evidence exists but may no longer reflect current conditions |
| `conflicting` | Available evidence points in multiple directions |

Scenario ranges should become wider when evidence quality is weak, incomplete,
outdated, or conflicting.

---

## Confidence

Confidence describes confidence in the scenario structure and supporting
evidence, not certainty about future returns.

| Value | Meaning |
|---|---|
| `low` | Assumptions are speculative; evidence is weak or missing |
| `medium` | Assumptions are reasonable; evidence is adequate |
| `high` | Assumptions are well-supported; evidence is strong |
| `unknown` | Confidence cannot be assessed |

A high-confidence scenario is a well-structured scenario with strong evidence.
It is not a guarantee.

---

## Change Trigger

An event or evidence update that would cause a scenario range to be revised.

```
trigger_id           string         unique ID, prefix: trg_
trigger_type         string         canonical; see Trigger Types
description          string         plain-language description of what to
                                   watch for
expected_effect      string         canonical; see Expected Effect Values
related_assumption_ids  array[string]  assumption IDs this trigger would affect
related_range_ids    array[string]  range IDs this trigger would affect
monitoring_note      string         optional; how to monitor this trigger
```

### Trigger types

| Value | Meaning |
|---|---|
| `earnings_report` | Scheduled earnings release |
| `guidance_change` | Management updates forward guidance |
| `revenue_growth_acceleration` | Revenue growth exceeds assumptions |
| `revenue_growth_deceleration` | Revenue growth falls short of assumptions |
| `margin_surprise` | Margins come in above or below assumptions |
| `valuation_multiple_expansion` | Multiple expands beyond base case |
| `valuation_multiple_compression` | Multiple contracts below base case |
| `balance_sheet_deterioration` | Debt, cash, or liquidity worsens |
| `balance_sheet_improvement` | Debt, cash, or liquidity improves |
| `product_or_strategy_update` | Major product launch or strategy shift |
| `regulatory_change` | Regulatory environment shifts |
| `macro_rate_regime_change` | Rate environment or macro regime changes |
| `currency_movement` | Significant currency movement affects returns |
| `thesis_evidence_improved` | New evidence strengthens the thesis |
| `thesis_evidence_weakened` | New evidence weakens the thesis |

### Expected effect values

| Value | Meaning |
|---|---|
| `range_may_expand` | The scenario range may widen |
| `range_may_compress` | The scenario range may narrow |
| `range_may_shift_up` | The range may shift upward |
| `range_may_shift_down` | The range may shift downward |
| `confidence_may_increase` | Confidence in the scenario may improve |
| `confidence_may_decrease` | Confidence in the scenario may decrease |
| `unknown` | Effect on the scenario is not yet known |

---

## Scenario Revision

A record of what changed in a scenario and why.

```
revision_id              string         unique ID, prefix: rev_
revised_at               string         ISO 8601 datetime of revision
previous_range_ids       array[string]  range IDs that were replaced
updated_range_ids        array[string]  range IDs that replaced them
reason                   string         plain-language summary of the revision
trigger_ids              array[string]  trigger IDs that prompted the revision
changed_assumption_ids   array[string]  assumption IDs that changed
evidence_item_ids        array[string]  evidence items that informed the revision
revision_note            string         optional; additional context
```

Revisions should explain what changed and why.

They must not imply that prior uncertainty was avoidable or that the updated
range is certain.

A revision record creates a living thesis. Each revision extends the thesis
history rather than replacing it.

---

## Safety Boundary

The safety boundary enforces Atlas's non-negotiable guardrails.

```
no_single_point_targets        boolean  true — ranges must not be single-point
                                        targets for forecast outputs
no_action_calls                boolean  true — no execution instructions
no_execution_instructions      boolean  true — no "buy" or "sell" instructions
no_prediction_certainty        boolean  true — no certainty framing
assumptions_required           boolean  true — assumptions must be present
evidence_quality_required      boolean  true — evidence quality must be stated
uncertainty_required           boolean  true — uncertainty must be acknowledged
change_triggers_required       boolean  true — change triggers must be present
```

All safety boundary fields must default to `true` in any future implementation.

None of these fields should ever be set to `false` in production scenarios.

---

## Canonical Values

The following values remain canonical English across all locales. Display-layer
localization is handled separately and does not change canonical field values.

| Field | Canonical values |
|---|---|
| `review_type` | holding, portfolio, mixed |
| `subject_type` | holding, portfolio, watchlist_item |
| `horizon` | short_term, medium_term, long_term |
| `case_type` | bear, base, bull, downside, upside, uncertainty_band |
| `assumption_type` | revenue_growth, earnings_growth, margin, valuation_multiple, balance_sheet, capital_allocation, competitive_position, business_quality, market_sentiment, momentum, macro_rate_sensitivity, currency |
| `direction` | positive, negative, mixed, neutral, unknown |
| `evidence_type` | company_report, earnings_call, guidance, financial_history, research_note, user_note, market_context, unknown |
| `freshness` | current, recent, stale, unknown |
| `evidence_quality` | strong, adequate, incomplete, weak, outdated, conflicting |
| `confidence` | low, medium, high, unknown |
| `trigger_type` | earnings_report, guidance_change, revenue_growth_acceleration, revenue_growth_deceleration, margin_surprise, valuation_multiple_expansion, valuation_multiple_compression, balance_sheet_deterioration, balance_sheet_improvement, product_or_strategy_update, regulatory_change, macro_rate_regime_change, currency_movement, thesis_evidence_improved, thesis_evidence_weakened |
| `expected_effect` | range_may_expand, range_may_compress, range_may_shift_up, range_may_shift_down, confidence_may_increase, confidence_may_decrease, unknown |
| `range_impact_level` | low, medium, high, dominant |
| Safety boundary fields | all boolean, default true |

---

## Example JSON

All examples use hypothetical data. They do not reflect real-time market data.
They do not imply factual accuracy for any real security. Figures are
illustrative only.

---

### Example 1 — Holding-Level Scenario

```json
{
  "scenario_review_id": "vsr_holding_001",
  "review_type": "holding",
  "created_at": "2026-07-07T12:00:00Z",
  "subject": {
    "subject_id": "subj_hihc_001",
    "subject_type": "holding",
    "display_name": "Hypothetical Industrial Holdings Co.",
    "ticker": "HIHC",
    "portfolio_id": null,
    "source_reference": "user_note_2026_07_07"
  },
  "time_horizons": ["medium_term"],
  "holding_scenarios": [
    {
      "holding_scenario_id": "hsc_hihc_001",
      "subject": {
        "subject_id": "subj_hihc_001",
        "subject_type": "holding",
        "display_name": "Hypothetical Industrial Holdings Co.",
        "ticker": "HIHC"
      },
      "ranges": [
        {
          "range_id": "rng_hihc_bear_mt",
          "horizon": "medium_term",
          "case_type": "bear",
          "lower_percent": -12.0,
          "upper_percent": -5.0,
          "currency_basis": null,
          "assumption_ids": ["asm_hihc_revenue", "asm_hihc_margin", "asm_hihc_multiple"],
          "evidence_item_ids": ["evi_hihc_q2report"],
          "confidence": "medium",
          "evidence_quality": "adequate",
          "uncertainty_note": "Margin durability under input cost pressure is the primary uncertainty."
        },
        {
          "range_id": "rng_hihc_base_mt",
          "horizon": "medium_term",
          "case_type": "base",
          "lower_percent": 8.0,
          "upper_percent": 18.0,
          "currency_basis": null,
          "assumption_ids": ["asm_hihc_revenue", "asm_hihc_margin", "asm_hihc_multiple"],
          "evidence_item_ids": ["evi_hihc_q2report", "evi_hihc_guidance"],
          "confidence": "medium",
          "evidence_quality": "adequate",
          "uncertainty_note": "Forward guidance has not been reaffirmed for Q3."
        },
        {
          "range_id": "rng_hihc_bull_mt",
          "horizon": "medium_term",
          "case_type": "bull",
          "lower_percent": 20.0,
          "upper_percent": 35.0,
          "currency_basis": null,
          "assumption_ids": ["asm_hihc_revenue", "asm_hihc_margin", "asm_hihc_multiple"],
          "evidence_item_ids": ["evi_hihc_q2report"],
          "confidence": "low",
          "evidence_quality": "incomplete",
          "uncertainty_note": "Bull case requires margin expansion above historical levels."
        }
      ],
      "key_drivers": [
        "Revenue growth trajectory",
        "Margin durability under input cost pressure",
        "Valuation multiple sensitivity to earnings"
      ],
      "key_risks": [
        "Input cost pressure reducing margins",
        "Customer concentration risk",
        "Rate sensitivity affecting valuation multiples"
      ],
      "assumptions": ["asm_hihc_revenue", "asm_hihc_margin", "asm_hihc_multiple"],
      "evidence_quality": "adequate",
      "confidence": "medium",
      "change_triggers": ["trg_hihc_earnings", "trg_hihc_guidance"],
      "revision_ids": [],
      "notes": "Review should be updated after Q3 earnings report."
    }
  ],
  "portfolio_scenario": null,
  "assumptions": [
    {
      "assumption_id": "asm_hihc_revenue",
      "assumption_type": "revenue_growth",
      "description": "Revenue grows at 7–9% in the base case; bear case 3%; bull case 12%+",
      "direction": "positive",
      "related_horizon": "medium_term",
      "related_range_ids": ["rng_hihc_bear_mt", "rng_hihc_base_mt", "rng_hihc_bull_mt"],
      "evidence_item_ids": ["evi_hihc_q2report", "evi_hihc_guidance"],
      "confidence": "medium"
    },
    {
      "assumption_id": "asm_hihc_margin",
      "assumption_type": "margin",
      "description": "Margins stable at 22–24% in base case; pressure to 18–20% in bear; expansion to 26%+ in bull",
      "direction": "mixed",
      "related_horizon": "medium_term",
      "related_range_ids": ["rng_hihc_bear_mt", "rng_hihc_base_mt", "rng_hihc_bull_mt"],
      "evidence_item_ids": ["evi_hihc_q2report"],
      "confidence": "medium"
    },
    {
      "assumption_id": "asm_hihc_multiple",
      "assumption_type": "valuation_multiple",
      "description": "P/E multiple holds at 17–19x in base; contracts to 15x in bear; expands to 21–22x in bull",
      "direction": "neutral",
      "related_horizon": "medium_term",
      "related_range_ids": ["rng_hihc_bear_mt", "rng_hihc_base_mt", "rng_hihc_bull_mt"],
      "evidence_item_ids": [],
      "confidence": "low"
    }
  ],
  "evidence_items": [
    {
      "evidence_item_id": "evi_hihc_q2report",
      "evidence_type": "company_report",
      "description": "Q2 2026 earnings report: revenue +8.1% YoY, margins at 22.8%",
      "source_reference": "Q2 2026 earnings release",
      "evidence_quality": "adequate",
      "freshness": "current",
      "related_assumption_ids": ["asm_hihc_revenue", "asm_hihc_margin"]
    },
    {
      "evidence_item_id": "evi_hihc_guidance",
      "evidence_type": "guidance",
      "description": "Management guided for full-year revenue growth of 7–9%; no margin guidance update",
      "source_reference": "Q2 2026 earnings call",
      "evidence_quality": "adequate",
      "freshness": "current",
      "related_assumption_ids": ["asm_hihc_revenue"]
    }
  ],
  "change_triggers": [
    {
      "trigger_id": "trg_hihc_earnings",
      "trigger_type": "earnings_report",
      "description": "Q3 2026 earnings report — will test margin durability and revenue growth assumptions",
      "expected_effect": "range_may_compress",
      "related_assumption_ids": ["asm_hihc_revenue", "asm_hihc_margin"],
      "related_range_ids": ["rng_hihc_bear_mt", "rng_hihc_base_mt", "rng_hihc_bull_mt"],
      "monitoring_note": "Watch gross margin trajectory and management commentary on input costs."
    },
    {
      "trigger_id": "trg_hihc_guidance",
      "trigger_type": "guidance_change",
      "description": "Any management update to revenue or margin guidance",
      "expected_effect": "range_may_shift_up",
      "related_assumption_ids": ["asm_hihc_revenue", "asm_hihc_margin"],
      "related_range_ids": ["rng_hihc_base_mt"],
      "monitoring_note": null
    }
  ],
  "revisions": [],
  "safety_boundary": {
    "no_single_point_targets": true,
    "no_action_calls": true,
    "no_execution_instructions": true,
    "no_prediction_certainty": true,
    "assumptions_required": true,
    "evidence_quality_required": true,
    "uncertainty_required": true,
    "change_triggers_required": true
  }
}
```

---

### Example 2 — Portfolio-Level Scenario

```json
{
  "scenario_review_id": "vsr_portfolio_001",
  "review_type": "portfolio",
  "created_at": "2026-07-07T12:00:00Z",
  "subject": {
    "subject_id": "subj_port_001",
    "subject_type": "portfolio",
    "display_name": "Hypothetical Growth Portfolio",
    "ticker": null,
    "portfolio_id": "port_growth_001",
    "source_reference": "portfolio_review_2026_07"
  },
  "time_horizons": ["medium_term"],
  "holding_scenarios": [],
  "portfolio_scenario": {
    "portfolio_scenario_id": "psc_port_001",
    "portfolio_id": "port_growth_001",
    "ranges": [
      {
        "range_id": "rng_port_bear_mt",
        "horizon": "medium_term",
        "case_type": "bear",
        "lower_percent": -18.0,
        "upper_percent": -6.0,
        "currency_basis": null,
        "assumption_ids": ["asm_port_semi", "asm_port_rate"],
        "evidence_item_ids": ["evi_port_macro"],
        "confidence": "low",
        "evidence_quality": "incomplete",
        "uncertainty_note": "Bear case highly sensitive to rate environment and semiconductor earnings revision."
      },
      {
        "range_id": "rng_port_base_mt",
        "horizon": "medium_term",
        "case_type": "base",
        "lower_percent": 5.0,
        "upper_percent": 16.0,
        "currency_basis": null,
        "assumption_ids": ["asm_port_semi", "asm_port_rate", "asm_port_margins"],
        "evidence_item_ids": ["evi_port_macro", "evi_port_earnings"],
        "confidence": "medium",
        "evidence_quality": "incomplete",
        "uncertainty_note": "Evidence gaps remain for 3 of 7 positions. Range will narrow as guidance is updated."
      }
    ],
    "weighted_contributions": [
      {
        "contribution_id": "ctb_semi_001",
        "holding_id": "hld_semi_001",
        "display_name": "Hypothetical Semiconductor Co.",
        "ticker": "HSMC",
        "portfolio_weight": 0.31,
        "contribution_to_range": "Largest single contributor to both upside and downside range.",
        "range_impact_level": "dominant",
        "key_reason": "High weight combined with wide scenario range driven by earnings revision risk.",
        "evidence_quality": "adequate"
      },
      {
        "contribution_id": "ctb_water_001",
        "holding_id": "hld_water_001",
        "display_name": "Hypothetical Water Infrastructure Fund",
        "ticker": "HWIF",
        "portfolio_weight": 0.14,
        "contribution_to_range": "Moderate upside contribution if thesis evidence improves.",
        "range_impact_level": "medium",
        "key_reason": "Thesis supported but evidence quality is incomplete.",
        "evidence_quality": "incomplete"
      }
    ],
    "main_upside_drivers": [
      "Semiconductor position — bull case could contribute +6–8% to portfolio return",
      "Industrial automation position — margin expansion thesis has moderate evidence support",
      "Water infrastructure — improving evidence quality could shift range upward"
    ],
    "main_downside_drivers": [
      "Rate sensitivity — 3 of 7 positions have high valuation multiples",
      "Earnings revision risk — 2 positions have guidance that has not been reaffirmed",
      "Concentration — semiconductor exposure exceeds 30% of portfolio weight"
    ],
    "concentration_sensitivity": "Portfolio scenario range is highly sensitive to the semiconductor position. A bear case for that single holding moves the portfolio range by approximately 5–7 percentage points.",
    "valuation_sensitivity": "Three positions have P/E multiples above 25x. A 10% multiple compression would reduce the base case range by approximately 3–4 percentage points.",
    "evidence_gaps": [
      "Forward guidance reaffirmation outstanding for 2 positions",
      "Margin durability evidence incomplete for 3 positions",
      "Competitive position evidence weak for 1 position"
    ],
    "holdings_requiring_review": ["hld_auto_001", "hld_water_001"],
    "confidence": "medium",
    "evidence_quality": "incomplete"
  },
  "assumptions": [
    {
      "assumption_id": "asm_port_semi",
      "assumption_type": "earnings_growth",
      "description": "Semiconductor position earnings grow 15–20% in base case, driven by AI infrastructure demand",
      "direction": "positive",
      "related_horizon": "medium_term",
      "related_range_ids": ["rng_port_base_mt", "rng_port_bear_mt"],
      "evidence_item_ids": ["evi_port_earnings"],
      "confidence": "medium"
    },
    {
      "assumption_id": "asm_port_rate",
      "assumption_type": "macro_rate_sensitivity",
      "description": "Rate environment holds roughly stable; significant rate increase would compress multiples for 3 positions",
      "direction": "mixed",
      "related_horizon": "medium_term",
      "related_range_ids": ["rng_port_bear_mt", "rng_port_base_mt"],
      "evidence_item_ids": ["evi_port_macro"],
      "confidence": "low"
    },
    {
      "assumption_id": "asm_port_margins",
      "assumption_type": "margin",
      "description": "Aggregate margin improvement of 0.5–1.5% across portfolio in base case",
      "direction": "positive",
      "related_horizon": "medium_term",
      "related_range_ids": ["rng_port_base_mt"],
      "evidence_item_ids": [],
      "confidence": "low"
    }
  ],
  "evidence_items": [
    {
      "evidence_item_id": "evi_port_macro",
      "evidence_type": "market_context",
      "description": "Current rate environment — central bank holding; market pricing 1–2 cuts in next 12 months",
      "source_reference": "User market context note, 2026-07-07",
      "evidence_quality": "adequate",
      "freshness": "current",
      "related_assumption_ids": ["asm_port_rate"]
    },
    {
      "evidence_item_id": "evi_port_earnings",
      "evidence_type": "financial_history",
      "description": "Semiconductor position Q2 earnings beat by 4%; guidance maintained",
      "source_reference": "Q2 2026 earnings",
      "evidence_quality": "adequate",
      "freshness": "current",
      "related_assumption_ids": ["asm_port_semi"]
    }
  ],
  "change_triggers": [
    {
      "trigger_id": "trg_port_earnings_season",
      "trigger_type": "earnings_report",
      "description": "Q3 earnings season — 5 of 7 portfolio positions report; key test for margin and growth assumptions",
      "expected_effect": "range_may_compress",
      "related_assumption_ids": ["asm_port_semi", "asm_port_margins"],
      "related_range_ids": ["rng_port_base_mt"],
      "monitoring_note": "Prioritize reviewing semiconductor and industrial automation positions first."
    },
    {
      "trigger_id": "trg_port_rate_change",
      "trigger_type": "macro_rate_regime_change",
      "description": "Central bank rate decision — any surprise above or below market pricing",
      "expected_effect": "range_may_shift_down",
      "related_assumption_ids": ["asm_port_rate"],
      "related_range_ids": ["rng_port_bear_mt", "rng_port_base_mt"],
      "monitoring_note": "Rate surprise upward would compress multiples for 3 high-multiple positions."
    }
  ],
  "revisions": [],
  "safety_boundary": {
    "no_single_point_targets": true,
    "no_action_calls": true,
    "no_execution_instructions": true,
    "no_prediction_certainty": true,
    "assumptions_required": true,
    "evidence_quality_required": true,
    "uncertainty_required": true,
    "change_triggers_required": true
  }
}
```

---

## Validation Expectations

Future schema validation should enforce the following:

| Expectation | Rule |
|---|---|
| Required IDs | `scenario_review_id`, `review_type`, `created_at`, `subject` must be present |
| Canonical `review_type` | Must be one of: holding, portfolio, mixed |
| Canonical `horizon` | Must be one of: short_term, medium_term, long_term |
| Canonical `case_type` | Must be one of: bear, base, bull, downside, upside, uncertainty_band |
| Range bounds present | `lower_percent` and `upper_percent` must be present on every Scenario Range |
| No single-point forecast | `lower_percent` must not equal `upper_percent` for forward-looking scenario outputs |
| Assumptions grounded | Scenario ranges should reference at least one assumption_id where possible |
| Evidence quality present | `evidence_quality` must be present on every Scenario Range |
| Confidence present | `confidence` must be present on every Scenario Range |
| Change triggers present | At least one change trigger must be present for scenario outputs |
| Safety boundary enforced | All safety boundary boolean fields must be `true` |
| Canonical values remain English | All enum-like fields must use canonical English values |
| IDs are non-empty strings | All `*_id` fields must be non-empty strings |

---

## Future Implementation Phases

| Phase | Description |
|---|---|
| Phase 0 | Data model specification (this sprint) |
| Phase 1 | Schema dataclasses for all model objects |
| Phase 2 | Example fixtures in valid JSON |
| Phase 3 | Read-only validation of scenario review JSON |
| Phase 4 | Read-only summary rendering |
| Phase 5 | Holding-level manual scenario input |
| Phase 6 | Portfolio-level manual scenario aggregation |
| Phase 7 | Revision tracking |
| Phase 8 | Optional market data integration, only if explicitly approved later |

No implementation is done in Sprint 275.

Market data integration (Phase 8) is explicitly deferred and requires separate
approval. It must not be pre-built or assumed.

---

## Open Questions

1. **ID format:** Should `vsr_`, `hsc_`, `rng_` etc. prefixes be enforced by
   the schema, or are they documentation conventions only?

2. **Revision linking:** When a range is revised, should the old range object
   be retained in full or only referenced by ID in the revision record?

3. **Portfolio aggregation method:** How should Atlas aggregate holding-level
   ranges to portfolio level without implementing a probability-weighted return
   model? Weighted average of midpoints is a possibility but requires
   documentation of its limitations.

4. **Horizon coverage requirement:** Should a complete scenario review require
   ranges for all three horizons, or is one horizon sufficient?

5. **Currency handling:** When holdings are in multiple currencies, how should
   portfolio-level percentage ranges be presented? Should currency effect be
   a separate scenario component?

6. **Safety boundary enforcement:** Should the safety boundary be a runtime
   check in future validation, or only a documentation guardrail?

7. **Integration with Temporary Workspace:** Should scenario review be a card
   type within the Temporary Workspace, or a separate review object? The
   existing `WorkspaceCard` model has 14 card types; a scenario card could
   be one of them.

---

## Recommended Next Sprint

**Sprint 276: Add Value Scenario schema dataclasses**

After the data model is specified, Atlas can add minimal schema dataclasses for
all Value Scenario model objects — `ValueScenarioReview`, `HoldingScenario`,
`PortfolioScenario`, `ScenarioRange`, `Assumption`, `EvidenceItem`,
`ChangeTrigger`, `ScenarioRevision`, `PortfolioContribution`, and
`SafetyBoundary` — with `from_dict()` and `from_json()` parse/validate methods.

This follows the pattern established by Sprint 270 (Temporary Workspace schema
dataclasses): no calculations, no market data, no forecasts, no CLI commands.
Pure data structure with parse and validate.

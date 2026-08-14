# UX-022 — Recommendation Experience Figma Correction Brief

**Sprint:** REI-001 (Atlas Beta — Recommendation Experience Implementation)
**Status:** Correction brief only. No production code, Core, or ADR changes made. Implementation remains paused pending a corrected Figma.

**Purpose:** UX-021 is the semantic source of truth. The Figma exports reviewed for this sprint are visually usable but contain ten categories of semantic drift — content, fields, and framing that Core does not compute and UX-021 did not approve. This brief lists every instance, the rule it breaks, and the minimum correction needed, while preserving as much of the approved visual design as possible. Confirmed against source this session: `atlas/alpha/decision_support.py`, `atlas/alpha/investment_case/api/schemas.py` (`FinancialPeriodView`, `MarketSnapshotView`, `CompanyProfileView`), `atlas/analysis_engine/direction_selector.py`, `atlas/analysis_engine/valuation/support.py`, `atlas/analysis_engine/outlook.py`.

---

## 1. Recommendation Labels

**Invalid Figma elements:** Badges reading "BUY," "ADD," "HOLD," "NO ACTION." Dev-mode spec's `RecommendationBadge` component table lists its states as `BUY (sage), ADD (sage), HOLD (gray), TRIM (ochre), NO_ACTION (gray), WITHHELD (warm-gray)` — the raw enum member names are the component's literal content model, not placeholder text.

**Governing rule:** `atlas/alpha/decision_support.py` docstring: *"The raw `RecommendationDirection` member names (`BUY`, `ADD`, `HOLD`, `TRIM`, `EXIT`) are never sent to the API or rendered anywhere in the product."* UX-021 Part 4's label table exists specifically to satisfy this.

**Correction:** Badge text becomes the existing `DecisionSupportLevel` badge label, unchanged from what's already live in `en.ts`:

| Figma shows | Correct badge | Correct one-line statement (already live copy) |
|---|---|---|
| BUY | **Entry supported** | "Current evidence supports initiating a position." |
| ADD | **Increase supported** | "Current evidence supports increasing exposure." |
| HOLD | **Thesis intact** | "Current thesis remains intact." |
| TRIM | **Reduction supported** | "Current evidence supports reducing exposure." |
| NO ACTION | **No action supported** | "Current evidence does not support initiating a position in this security." |
| WITHHELD | **Insufficient evidence** | See §4/§5 below — the Figma's own withheld headline needs separate correction, not just the badge. |

**Visual structure:** Unchanged. This is a text-content swap inside the existing badge component — same size, same muted/sage/gray/ochre/warm-gray tone-per-state system the dev spec already defines. The underlying principle to preserve regardless of exact wording: *Atlas states what current evidence supports, never an imperative command.*

**Data source:** `DecisionSupportLevel.badge_label` / `.statement`, already computed by `describe_recommendation()`. `RecommendationDirection` itself is not touched.

---

## 2. Fabricated Valuation Capabilities

**Invalid Figma elements:**
- "FAIR VALUE RANGE: $380–$440" bracketed directly against "CURRENT PRICE: $412" (MSFT BUY/ADD states)
- "EARNINGS GROWTH: +18% est." (all states)
- "DIVIDEND YIELD: 0.7%" (all states)
- "Price remains within the lower half of estimated fair value range" (ADD), "Current price sits within the estimated fair value range" (HOLD) — valuation-card body copy built entirely on the fair-value-range premise

**Governing rule:** None of these fields exist. Confirmed by direct source read this session:
- No "fair value range" or price-target concept exists anywhere in `valuation/support.py`, `valuation/models.py`, or `outlook.py`. `outlook.py`'s own docstring is explicit: Atlas's return ranges are *"never a forecast or a price target."* Bracketing a "Fair Value Range" around "Current Price" is structurally a price target, which Core has never computed and this sprint may not introduce (no Core changes).
- `FinancialPeriodView` has no earnings-growth-estimate field — only historical actuals (`revenue`, `netIncome`, `eps` per period). Atlas does not forecast forward earnings.
- `FinancialPeriodView.dividends` exists but is a **raw historical dollar amount per period** (a cash-flow line item), not a dividend-yield percentage. No yield ratio is computed anywhere.

**Correction:** Remove "Fair Value Range" and "Dividend Yield" and "Earnings Growth est." from the key-metrics strip entirely — do not invent replacement numbers, do not compute a yield or growth rate client-side. "Current Price" may stay **only** as a standalone fact (`MarketSnapshotView.sharePrice` is real), never positioned adjacent to or bracketed by anything implying a target or fair-value comparison. Replace the valuation card's body copy with the real DE-015 fields per UX-021 Part 8 (see §8 below).

**Visual structure:** The card shell, position, and "one-line explanation + expandable detail" pattern stay. The 5-metric horizontal strip shrinks to whatever subset of it is real (Current Price, and any other already-fetched `MarketSnapshotView`/`FinancialPeriodView` field the product wants to surface) — do not backfill the freed columns with new invented metrics to preserve a 5-item count.

**Data source:** `MarketSnapshotView.sharePrice` only, for the one legitimate figure. Everything else in this section has no data source and must not be rendered.

---

## 3. Invented Portfolio Intelligence

**Invalid Figma elements:**
- "Limited by: Portfolio concentration approaching threshold" (MSFT ADD hero)
- "Portfolio concentration: Adding would bring Technology sector weight above preferred range"
- "Timing uncertainty: Near-term earnings announcement may create temporary volatility"

**Governing rule:** `select_direction` (read in full this session) has no concentration-threshold, sector-weight, or earnings-calendar logic — `HoldingLinkage` is a binary PRESENT/ABSENT fact, nothing more. UX-021 Part 12 explicitly anticipated and forbade exactly this: *"avoid turning it into portfolio optimization given Portfolio Intelligence is still incomplete."*

**Correction:** Remove both bullets entirely — there is no real Core signal behind either. Holding context stays factual only: held/not held, share count, market value, portfolio weight (all real, already fetched today). If the real limiting factor for this ADD case is something else Core actually computed (e.g., a genuine risk finding or the ValuationSupport gap), substitute that instead — do not leave the Limiting Factor slot empty by habit; use §6's rule to pick the real highest-priority one.

**Visual structure:** Unchanged — "Limited by:" stays a single line in the hero, "What limits this conclusion?" stays a card below with 1–2 items. Only the content changes to whatever Core-real limiting factor(s) actually apply to that state (may be none, in which case the section is omitted, not filled with placeholder text).

**Data source:** `HoldingLinkage`, `RiskFinding`s tagged to real categories (business_risk/financial_risk/valuation_risk/thesis_risk), and `ValuationSupport.gap` — nothing else.

---

## 4. RecommendationWithheld Reasons

**Invalid Figma elements:**
- "Insufficient data reliability: Available financial data does not meet Atlas quality thresholds for recommendation."
- "Rapid change: Business fundamentals are shifting too quickly for stable analysis."

**Governing rule:** Neither "data reliability quality thresholds" nor "rapid business change" are real `RecommendationWithheld.reason` values. The real reasons trace to the DE-008 hard gate: `EvaluationState` (Business / Valuation / Portfolio Intelligence / Reasoning) not yet `EVALUATED`, or `EvidenceCoverageLevel` at `NONE`/`NOT_APPLICABLE`. UX-021 Part 5 already specifies translating the real `.reason`/`.missing_evaluations` into plain language — this Figma content invents a taxonomy that doesn't exist instead.

**Correction:** Replace both bullets with the real, named missing stage, in the same plain-language register UX-021 Part 5 already establishes, e.g.:

- "Atlas hasn't yet completed its business analysis for this company." (Business Evaluation not `EVALUATED`)
- "Atlas hasn't yet completed a valuation analysis for this company." (Valuation not `EVALUATED`)
- "There isn't enough evidence on record yet to support a conclusion." (`EvidenceCoverageLevel.NONE`/`.NOT_APPLICABLE`)

Show only the reason(s) actually present on `RecommendationWithheld` for that Case — never a fixed two-bullet template regardless of the real cause.

**Visual structure:** Unchanged — "Why is this recommendation withheld?" stays a card with 1–2 bulleted items in the same visual treatment as the "What limits this conclusion?" card elsewhere, which is a reasonable, consistent reuse of one component for both purposes.

**Data source:** `RecommendationWithheld.reason` / `.missing_evaluations`.

---

## 5. RecommendationWithheld Framing

**Invalid Figma elements:** Headline "Atlas has determined that providing a recommendation would not serve your interests at this time." Plus the CTA "Acknowledge and continue" gating further interaction.

**Governing rule:** This personifies Atlas as making an active, paternalistic judgment call about the investor's interests — a materially different, more editorializing claim than "the hard gate didn't clear." UX-021 Part 5's explicit framing: Withheld must read as "the correct, honest state," exactly as legible and intentional as every other state — not a decision Atlas is making *about* the investor. Nothing in UX-021 specifies an acknowledgment gate before the page can be used.

**Correction:** Replace the headline with something structurally equivalent to UX-021's own withheld pattern — a plain statement that a conclusion isn't available yet, e.g. "Atlas does not have enough evidence to support a directional conclusion yet." (the exact wording the sprint brief itself supplies as the safe baseline). Remove the "Acknowledge and continue" gate — the page should be usable immediately, the same as any other Direction state; a "Record my decision" CTA (§9) may still appear, just not behind an acknowledgment click.

**Visual structure:** Card shell, badge, and position in the hierarchy stay unchanged — only the headline sentence and the CTA's gating behavior change.

**Data source:** `RecommendationWithheld` itself (a `None` return, not an error) — no other field needed for the headline.

---

## 6. "Quality Guarantee" Card

**Invalid Figma elements:** The standalone card: *"Quality Guarantee — Atlas withholds recommendations when the quality of analysis cannot meet the standard required for responsible guidance. This is a protective measure, not a failure."*

**Governing rule:** This introduces a named product doctrine/promise ("Quality Guarantee") that exists nowhere in DE-008, UX-021, or any adopted ADR. It's marketing-register copy asserting a general policy about "responsible guidance" standards Atlas has never actually claimed to itself.

**Correction:** Remove this card entirely. If explanatory context is still wanted at this position in the layout, the only permitted content is the single sentence the sprint brief itself authorizes: *"Atlas does not have enough evidence to support a directional conclusion yet."* — no new heading, no "guarantee" framing, no "protective measure" characterization.

**Visual structure:** The card's position (between the hero and the reasons list) can be dropped, or repurposed to hold the one-sentence explanation above with the same visual weight — implementer's choice, since UX-021 doesn't mandate a card here at all.

**Data source:** None — this section, if kept at all, is fixed copy, not derived from any field.

---

## 7. Conviction Presentation

**Invalid Figma elements:** "ATLAS CONVICTION" as a metrics-strip field, taking values "Moderate" (BUY/ADD/HOLD), "Insufficient" (NO_ACTION), "Withheld" (RIVN withheld state) — implying one unified conviction scale spanning all states.

**Governing rule:** UX-021 Part 24 already deferred exposing `RecommendationConvictionLevel` in Beta as **NEEDS PRODUCT DECISION** — that decision has not been made, so it cannot appear at all. Separately, none of "Moderate"/"Insufficient"/"Withheld" as a single scale matches any real Core enum: `ConvictionAssessment` uses `very_high/high/moderate/low/insufficient_evidence`; `RecommendationConvictionLevel` uses `HIGH/MEDIUM/LOW`; neither has a "Withheld" value. UX-021 Part 7 also specifically renamed this field to "Analysis Depth" to stop it colliding with two other Core concepts already sharing the word "Conviction."

**Correction:** Remove "Atlas Conviction" as shown. Do not introduce it as a new label either. If a conviction-shaped field is wanted here at all, it must be the existing, already-approved presentation: label **"Analysis Depth"**, values drawn only from the real 5-level `ConvictionAssessment` scale already rendered elsewhere in the product today (not a new 3-value scale invented for this card).

**Visual structure:** The metrics-strip slot can stay (as a 4-item strip instead of 5, or backfilled with another real, already-fetched field) — only this field's label and value source change.

**Data source:** `ConvictionAssessment.level`, if shown at all — never `RecommendationConvictionLevel` (deferred) and never a value outside that enum's real 5 members.

---

## 8. "Why Atlas Thinks This" Content

**Invalid Figma elements:** "Cloud segment growing 28% YoY with expanding margins," "AI integration driving enterprise adoption across product suite," "Search advertising maintains dominant market position," etc. — specific, numeric, company-research-style claims.

**Governing rule:** Core's real Business Analysis output is categorical (Growth/Capital Allocation each `STRONG`/`MODERATE`/`WEAK`/`INSUFFICIENT_INPUT`), not narrative research prose with invented percentages. UX-021 Part 10 requires the evidence-compression rule to reflect only what Core actually ranks/states — inventing granular claims to "make the mockup look realistic" is exactly what that rule exists to prevent, and directly restates this sprint's own "no invented percentages" hard constraint.

**Correction:** The bullet-list structure (checkmark + short sentence, 3 items max) is fine to keep as a component shape. Content must come from real, already-computed Business Analysis / `CaseHighlightView` findings — reuse the sentence banks already live in `HeroCard.tsx`'s `STRENGTH_SENTENCE_KEY` (e.g., "Revenue growth trend supports the thesis," categorical and real) rather than fabricated company-specific research claims. If the design wants company-specific texture, that has to come from a real evidence reference already in `supportingEvidence`/evidence citations — never invented for visual polish.

**Visual structure:** Unchanged — checkmark-bulleted list, same card, same "Why Atlas thinks this" heading is fine as a Figma-native label distinct from (but not contradicting) the current live "Supports the Case" heading; that's a copy choice, not a semantic one, and can be resolved during implementation without another correction pass.

**Data source:** `CaseHighlightView` / `strengths[]`, via the existing `STRENGTH_SENTENCE_KEY` sentence bank — categorical, not free text.

---

## 9. Valuation Support Presentation

**Invalid Figma elements:** Covered mechanically in §2 (fair value range), but the labeling pattern itself also needs correction: section headlines like "VALUATION SUPPORTS THE RECOMMENDATION" / "VALUATION SUPPORTS ADDING TO POSITION" / "VALUATION IS NEUTRAL" / "VALUATION ASSESSMENT INCOMPLETE" imply a general valuation-attractiveness judgment, not DE-015's narrow downside-aware check.

**Governing rule:** DE-015 §6–8: `SUPPORTED` means only "the adverse end of the range still avoids a nominal loss" — never a claim that valuation broadly "supports" a recommendation, is "neutral," or is generally attractive. UX-021 Part 8 already defines the safe presentation-layer labels precisely to avoid this.

**Correction:** Replace the four section headlines with UX-021 Part 8's approved labels:

| ValuationSupportStatus | Correct label |
|---|---|
| `SUPPORTED` | **Downside support present** |
| `NOT_SUPPORTED` | **Downside support absent** |
| `INSUFFICIENT_INPUT` | **Valuation conclusion unresolved** |

Body copy must not claim fair value, price target, economic sufficiency, or risk-adjusted attractiveness (per UX-021 Part 6). Where the card needs one line of explanation, use UX-021 Part 9's real gap-kind copy (e.g., for `INSUFFICIENT_HISTORICAL_VALUATION_DATA`: "There isn't enough price history yet to complete this check.") rather than a fair-value-range sentence. Per UX-021 Part 8's placement rule, this card should only appear at all when Valuation Support is load-bearing for the Direction shown (BUY/ADD, or a case where it's the specific reason a stronger Direction wasn't reached) — not on every state unconditionally.

**Visual structure:** Card shell, "one-line explanation + expandable detail" pattern, and the `>` expand affordance all stay exactly as shown — only the headline and body copy source change.

**Data source:** `ValuationSupport.status` (for the label) and `.gap` (for the one-line explanation) only — never `.reasoning` verbatim, never a fair-value number.

---

## 10. What Should NOT Change

Per the correction instructions, the following aspects of the Figma are semantically valid or visual-only and should be preserved as-is:

- Overall page composition and card rhythm (identity header → Recommendation Hero → Valuation Support card → Why Atlas thinks this → Limiting Factors → metrics strip → Outlook/Risk cards → Decision Entry footer)
- Typography scale, spacing, and the calm, muted visual register (no saturated red/green, no urgency)
- Recommendation Hero proportions and the badge + headline + holding-context + freshness + limiting-factor layout inside it
- The Limiting Factor component concept itself (only its content source is wrong, not its existence or placement)
- Decision Entry placement and CTA copy — "Record my decision" already matches UX-021 Part 18/19 exactly; no correction needed here
- Progressive disclosure pattern (hero → expandable "Why Atlas thinks this" / "What limits this conclusion?" → metrics strip → deeper cards)
- Desktop/mobile structural approach (mobile condensing to the same hero-first hierarchy)
- The dev-mode "Migration Plan" table's REMOVE decisions (Charts/Graphs, Trading Actions, Price Alerts, News Feed) — all four correctly align with UX-021's explicit "no trading UI" constraint and should stay removed

---

## Corrected Component/State/Data-Source Summary

| Component | Correct states | Correct data source |
|---|---|---|
| `RecommendationBadge` | Entry supported / Increase supported / Thesis intact / Reduction supported / No action supported / Insufficient evidence | `DecisionSupportLevel.badge_label` |
| Recommendation Hero headline | Existing `decisionSupport.statement.*` copy (extend per UX-021 Part 6 for BUY/ADD full-chain attribution) | `DecisionSupportLevel.statement` |
| Limiting Factor | Only real Core-derived items: `RiskFinding` (4 real categories), `ValuationSupport.gap`, or nothing if none apply | Risk findings, `ValuationSupport.gap` |
| Valuation Support card | Downside support present/absent/unresolved + gap copy; shown only when load-bearing | `ValuationSupport.status`, `.gap` |
| Why Atlas thinks this | Categorical strength sentences, ≤3, no invented percentages | `CaseHighlightView`/`strengths[]` |
| Withheld reasons | Named missing evaluation stage(s), 1–2 items, only what's actually present | `RecommendationWithheld.reason`/`.missing_evaluations` |
| Withheld headline | "Atlas does not have enough evidence to support a directional conclusion yet." (or UX-021 Part 5's fuller version) | `RecommendationWithheld` |
| "Quality Guarantee" card | Removed | — |
| Key metrics strip | Current Price only (real) + any other already-fetched real field; no Fair Value Range, Earnings Growth, Dividend Yield | `MarketSnapshotView.sharePrice` |
| Atlas Conviction field | Removed, or replaced with "Analysis Depth" using real `ConvictionAssessment.level` | `ConvictionAssessment.level` |
| Decision Entry CTA | "Record my decision" (unchanged) | — |

---

## Verdict

**READY FOR FIGMA CORRECTION.**

Every invalid element in this brief has a direct, already-approved correction available from UX-021 or from Core fields already fetched today — none of the ten items requires a new product decision, a Core change, or an ADR change. (The one item that touches an existing open deferral — Conviction, §7 — is resolved by simply *not* introducing a new scale, consistent with UX-021 Part 24's standing NEEDS PRODUCT DECISION status; it does not require re-opening that decision now.) Once the Figma frames are corrected against this brief, implementation (REI-001) can resume.

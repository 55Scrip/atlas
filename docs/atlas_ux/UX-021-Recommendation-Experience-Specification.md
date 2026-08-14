# UX-021 — Recommendation Experience Specification

**Atlas Beta — Recommendation Experience Sprint 1: From Core Decision to Investor-Facing Product Experience**

Status: Product & implementation design. No code, no ADR, no schema, no commit produced by this document. Grounded in a fresh, direct re-read of the current frontend and backend as of 2026-08-14 (not inferred from prior-sprint memory).

---

## Part 1 — Current Product Audit

The audit was done by reading the live source, not by recalling what earlier sprints intended to build. Three findings from this fresh read change the shape of everything that follows, so they're stated first.

### Finding A: the product already has a faithful presentation layer for Recommendation — under different names

`atlas/alpha/decision_support.py` (`describe_recommendation`) is a deterministic, 1:1 wrapper around the real `RecommendationGateResult`. It reads `gate_result.recommendation` only, recomputes nothing, and maps:

| Core `RecommendationDirection` / `RecommendationWithheld` | Product `DecisionSupportLevel` | Current badge | Current statement |
|---|---|---|---|
| `BUY` | `entry_supported` | "Entry supported" | "Current evidence supports initiating a position." |
| `ADD` | `increase_supported` | "Increase supported" | "Current evidence supports increasing exposure." |
| `HOLD` | `thesis_intact` | "Thesis intact" | "Current thesis remains intact." |
| `TRIM` | `reduction_supported` | "Reduction supported" | "Current evidence supports reducing exposure." |
| `EXIT` | `exit_supported` | "Exit supported" | "Current evidence supports exiting the position." |
| `NO_ACTION` | `no_action_supported` | "No action supported" | "Current evidence does not support initiating a position in this security." |
| `RecommendationWithheld` (any reason) | `insufficient_evidence` | "Insufficient evidence" | "Current evidence is insufficient to support any portfolio action." |

The raw `RecommendationDirection` member names are never sent to the API or rendered — good, pre-existing discipline this sprint doesn't need to invent. This means Parts 4–6 are a **refinement of live copy**, not a greenfield design.

### Finding B: `ValuationSupport` is completely invisible in the product today

Grepped `atlas/alpha/investment_case/api/schemas.py`, `atlas/alpha/portfolio_cockpit/*.py`, and every frontend file: zero references to `valuation_support`/`ValuationSupport` anywhere outside `atlas/analysis_engine/`. DE-016 wired `ValuationSupport.status` into `select_direction` at the Core level, but nothing between Core and the investor knows it exists. Concretely: the moment a real company reaches `entry_supported`/`increase_supported` under DE-016's new reachability, the investor will see "Entry supported" / "Current evidence supports initiating a position" with **no indication that a valuation-support check was the gating factor**, and — for the far more common case — no explanation when it's the reason BUY/ADD *isn't* reached. This is the sprint's central gap; Parts 6, 8, and 9 exist to close it.

### Finding C: "Conviction" is already an overloaded label today, before this sprint adds a third meaning

`HeroCard`'s Key Metrics row shows a field labeled "Conviction" — but it renders `analysis.conviction.level`, the **5-level `ConvictionAssessment`** (`very_high/high/moderate/low/insufficient_evidence`), an evidence-quality signal computed in `atlas/analysis_engine/conviction.py`. It is *not* `RecommendationConvictionLevel` (DE-004 §3's 3-level `HIGH/MEDIUM/LOW` existence-gate concept) — that type is not exposed anywhere in the API or frontend at all; `RecommendationStateView.convictionGateMet` is defined on the wire type but never read in any JSX. Separately, `AtlasOutlookSection` gives **each Outlook horizon its own "Conviction" badge**, reusing the identical `ConvictionLevel` type/tone/label bank for a third, structurally different concept (Outlook's own bounded derivation, per `HorizonOutlook.conviction`'s docstring). Three different Core concepts, two of them already sharing one label and visual treatment, a third one not yet wired in at all. Part 7 has to resolve this now, before `RecommendationConvictionLevel` gets wired in and becomes a fourth thing competing for the same word.

### What the page actually looks like today

`InvestmentCasePage.tsx` (5,326 lines) composes, top to bottom:

1. **Identity header** — ticker, company name, current allocation if held, origin ribbon (dashboard/portfolio/history/daily-brief/discovery), reconciliation-status note.
2. **HeroCard** (`frontend/src/investmentCase/HeroCard.tsx`) — the only place Direction is stated as a sentence:
   - Withheld state: three-sentence opening/reason/closing narrative + one badge, no Key Metrics row, no Strength/Concern/Priority row.
   - Normal state: one Atlas sentence (Decision Support statement + a "tension" clause — `aligned_positive`/`aligned_negative`/`business_strong_valuation_weak`/`business_weak_valuation_strong`/`insufficient`, derived from Growth×Capital-Allocation×Valuation agreement) → Key Metrics row (Recommendation badge, Conviction badge, Expected Return range or gap reason, Upside/Downside) → Outlook-alignment tertiary line (only when not `unavailable`) → Biggest Strength / Biggest Concern / Current Priority three-column row → a risk flag line when the most severe risk is `moderate`/`high` → "Reflects Atlas's analysis as of {relative time}."
3. **InvestmentArgumentSection** — two-column Supports/Challenges, built from real `CaseHighlightView[]` (`strengths[]`/`risks[]`), one sentence per item, shared sentence banks with Hero's own Strength field.
4. **AtlasReasoningSection** — four terse, non-expandable cards: Growth, **Valuation** (this is `ValuationStatus` — undervalued/fairly_valued/expensive — *not* `ValuationSupport`), Financial Health, Business Quality.
5. **CompanyHealthAssessmentSection** — five expandable cards (Business Quality, Financial Strength, Management & Governance, Capital Allocation, Competitive Position), each with supporting/contradicting/missing evidence one click away.
6. **InterpretedFinancialEvidenceSection** + detailed **FinancialsTable** (expandable).
7. **AtlasOutlookSection** — dual horizon (Short-Term/Long-Term), each with Expected Return, Bull/Base/Bear scenarios, its own Conviction badge, Momentum, Key Drivers, graceful gap states.
8. **Tab bar** — Decision History / Timeline / Last Activity / Outstanding Work / Outcomes / More Details.
9. **Decision panel** (collapsed by default, header-anchored) — Add/Trim/Remove/Leave-as-is actions, opening a form that records a Decision (+ optional Outcome/Transaction) — never auto-executes anything.

`PortfolioPage.tsx`'s Holdings table Action column reuses the identical `DecisionSupportLevel` badge per row — cross-surface consistency already holds.

**No mobile-specific layout exists.** Zero `@media` queries in `InvestmentCasePage.tsx`; the same `Inline`/`Stack` flex-wrap layout is used at every width. On a narrow viewport, Hero's four-field Key Metrics row and three-column Strength/Concern/Priority row will each wrap to single-column stacks, pushing the "why" tension clause and the risk flag well below the fold — this is a real, current gap Part 17 has to address, not a hypothetical one.

**Deliverable 1:** Audit above. Two real, current defects carried forward as binding constraints on this design: (B) ValuationSupport must be surfaced wherever it's load-bearing for BUY/ADD, and (C) "Conviction" needs disambiguated labels before a third/fourth concept collides with it.

---

## Part 2 — Core-to-UX Mapping

For each Core concept: what it means, what it does *not* mean, and where it belongs.

| Concept | Means | Does NOT mean | Placement |
|---|---|---|---|
| `RecommendationDirection` (BUY/ADD/HOLD/TRIM/EXIT/NO_ACTION) | A terminal, categorical conclusion given today's evidence | An instruction, an order, a prediction | **Primary** — the headline |
| `RecommendationWithheld` | The hard gate didn't clear; no conclusion is being offered | An error, a bug, "no data" in the generic sense | **Primary** — its own first-class state, not a degraded Direction card |
| `ValuationSupport.status` | Narrow, downside-aware, nominal, non-risk-adjusted prerequisite for *new capital* (BUY/ADD only) | "Good value," "attractive," expected outperformance, risk-adjusted anything | **Secondary**, surfaced only when it is the actual reason BUY/ADD is or isn't reached |
| `ValuationSupport.reasoning` | Internal proof narrative (Core's own §18 boundary: Recommendation never reads it either) | — | **Hidden** — never rendered verbatim; only informs product-authored gap copy (Part 9) |
| `ValuationSupport.gap` | Which of 6 reasons the valuation check didn't resolve favorably | A defect or missing feature | **Secondary**, one interaction away, shown only alongside a non-`SUPPORTED` status that is actually gating something |
| Recommendation Conviction (3-level, existence-gate) | Whether a Recommendation could be formed at all — paired with `RecommendationWithheld` | A confidence percentage, a grade on the Direction itself | **Secondary**, low visual weight, relevant chiefly to explain *why withheld* |
| Business Analysis (Growth / Capital Allocation) | Evaluated company-quality findings that feed the Direction and the hard gate | A score to sum | **Primary supporting evidence** — already well-served by existing sections |
| Outlook | An independently computed, shared-ancestor sibling of Recommendation — correlated, never causal | A forecast that explains or justifies the Direction | **Secondary**, must stay visually and textually separate from Direction (current tertiary-line treatment is correct; keep it) |
| Risk | Categorical, per-category evaluated finding | A single aggregate risk score | **Secondary**, escalating to primary only when `moderate`/`high` (current Hero risk-flag behavior is correct) |
| Holding state (`HoldingLinkage`) | Structural fact partitioning which two Directions are even reachable | A recommendation to rebalance to a target weight | **Primary framing context** — must always be visible before the Direction sentence is read |
| `RecommendationWithheld.reason` / `.missing_evaluations` | Diagnostic detail on what specifically is missing | — | **Secondary**, one interaction away ("what's missing") |

**Deliverable 2:** Table above, grounded in DE-008 §6–8/§21, DE-015 §6–8/§18, DE-012, DE-014 — all re-confirmed from source this session, not recalled from memory of the ADR text.

---

## Part 3 — Recommendation Information Hierarchy

Ten elements, placed by the same three-tier model the existing page already uses (Hero / section / tab), because that model is sound and shouldn't be reinvented:

**Above the fold** (Hero):
1. Direction headline (badge + one-line statement)
2. Holding-state framing (already in the identity header — keep it directly above Hero, not below)
3. One-line rationale (today's "why" tension clause)
4. Risk flag, only when material

**One interaction away** (Hero's Key Metrics row / a single expand):
5. Conviction (existence-gate; relabeled per Part 7)
6. Valuation Support status — **only rendered here when it is load-bearing** (see Part 8)
7. Business Analysis summary (Biggest Strength / Biggest Concern — already exists)
8. Outlook corroboration line (already exists)
9. "What would change this" (new — Part 11)

**Deep detail** (sections below Hero / tabs):
10. Full reasoning chain: Business Analysis detail, Risk detail, evidence lists, full Outlook panel, ValuationSupport gap explanation, Decision/Outcome history

**Deliverable 3:** Hierarchy above. This is closer to a validation of the existing structure than a redesign — the real gap is items 6 and 9, which don't exist yet.

---

## Part 4 — Direction Presentation

For each reachable state, label + one-line statement (extending, not replacing, current copy) plus explicit non-goals:

| Direction | Label (badge) | Statement pattern | Tone (StatusBadge) |
|---|---|---|---|
| BUY | "Entry supported" | "Atlas's business analysis, [absence of a challenged thesis], and its valuation-support check together support initiating a position." | `positive`, desaturated — not the same saturated green as a "healthy" status elsewhere |
| ADD | "Increase supported" | Same chain, "increasing exposure." | `positive`, desaturated |
| HOLD | "Thesis intact" | Unchanged. | `neutral`/`positive` (current) |
| TRIM | "Reduction supported" | Unchanged. | `caution` |
| NO_ACTION | "No action supported" | Unchanged — already correctly distinct from Withheld. | `neutral` |
| `RecommendationWithheld` | "Insufficient evidence" | Part 5. | `neutral` |

Explicit non-goals, all absent from current copy and to stay absent: no oversized action buttons (Direction stays a badge + sentence, the same visual weight as every other status in the page); no numeric score or percentage attached to Direction; no urgency language ("act now," "time-sensitive"); no gamified affordances (streaks, progress bars toward a target); no brokerage register ("strong buy," "conviction buy," star ratings). The desaturation note for BUY/ADD is new and deliberate: today's `positive` tone is shared with, e.g., `undervalued` and `strong` — visually equating "entry supported" with a generic favorable status would overstate what a narrow, downside-aware valuation check actually claims.

**Deliverable 4:** Table above.

---

## Part 5 — RecommendationWithheld as a First-Class State

Hero already branches correctly (`isWithheld`) into its own narrative rather than a degraded Direction card — keep that structure, extend its content:

- Never render "insufficient data" as the entire message. Use `RecommendationWithheld.reason` to name the actual gap in plain language: which evaluation stage hasn't run (Business / Valuation / Portfolio Intelligence / Reasoning) or which evidence-coverage threshold isn't met — reusing the same plain-language mapping Part 9 builds for `ValuationSupport.gap`, so gap-communication copy has one consistent voice across the page rather than two.
- Never present it as disabled/greyed-out — it should look exactly as intentional and legible as every other state, because it *is* the correct, honest state for the majority of real companies in this environment today (only CRWD/NVDA clear `ValuationSupport.SUPPORTED`, and AAPL/MSFT/TSLA — the only tickers with real Cases today — are all withheld at the DE-008 hard gate).
- Always pair with a concrete next step: what evidence or analysis step would need to exist, phrased as "what's missing," not "try again later."

**Deliverable 5:** Above.

---

## Part 6 — BUY/ADD Safety Copy

Binding constraint restated: `SUPPORTED` means only "the adverse end of the range still avoids a nominal loss" — never expected outperformance, risk-adjusted attractiveness, superior opportunity cost, guaranteed upside, or high certainty.

**Attribution sentence (Direction statement, above the fold):** "Atlas's business analysis, [the absence of a challenged thesis / the intact thesis], and its valuation-support check for new capital — together — support [initiating a position / increasing exposure]." Never "Valuation Support says buy" and never a sentence that credits ValuationSupport alone.

**Expansion copy (one tap into item 6 from Part 3, shown only when ValuationSupport is actually load-bearing):** "Atlas checked whether today's price still avoids a nominal loss under a downside scenario — it does. This is not a claim about expected return, how attractive the price is relative to alternatives, or certainty. It is one narrow, downside-aware check among several that together support this Direction."

**Forbidden phrases** (none currently appear in `decisionSupport.*` copy — a scan of `en.ts` confirms today's six-state table is already clean; this list is a guardrail for the *new* copy this sprint adds): "expected to outperform," "attractive valuation," "better opportunity than," "guaranteed," "high certainty," "strong buy," any numeric confidence percentage.

**Deliverable 6:** Copy patterns above.

---

## Part 7 — Conviction vs Confidence

Resolving Finding C from Part 1 is the actual deliverable here, not a hypothetical design exercise.

- **Rename the presentation-layer label** for Hero's existing `ConvictionAssessment` field (currently "Conviction") to **"Analysis Depth"** — it is fundamentally an evidence-quality/coverage signal ("how much does Atlas actually know"), and that's what its own five values (`very_high`→`insufficient_evidence`) actually encode. This is a frontend copy change only — the Core `ConvictionAssessment` type and its `level` values are untouched.
- **Reserve "Conviction"** exclusively for `RecommendationConvictionLevel` once it is wired into the API (currently it is not — see Finding C). When it is added, it renders as its own field, distinct from Analysis Depth, with copy stating plainly: "Conviction reflects whether Atlas had enough to form a conclusion at all — not how likely that conclusion is to be right." Never a percentage, never a progress bar.
- **Outlook's per-horizon "Conviction" badge** stays scoped inside the Outlook section (it already is, visually) but its label should read **"Outlook Conviction"** rather than bare "Conviction," since it will otherwise be the third field on one page independently using the same bare word.
- General rule for all three: none of them is a probability. No field on this page should ever be phrased or styled (numeric, progress bar, star rating) in a way that invites reading it as "% chance Atlas is right."

**Deliverable 7:** Three-way relabeling above — a genuine, currently-live ambiguity resolved before it gets worse.

---

## Part 8 — Valuation Support UX Labels

Testing the literal Core value `SUPPORTED` directly in UI: unsafe alone — "Valuation: Supported" reads as "this is a good buy," collapsing exactly the distinction DE-015 exists to preserve. Adopting presentation-layer-only relabeling (Core enum untouched):

| `ValuationSupportStatus` | UI label |
|---|---|
| `SUPPORTED` | "Downside support present" |
| `NOT_SUPPORTED` | "Downside support absent" |
| `INSUFFICIENT_INPUT` | "Valuation conclusion unresolved" |

Placement rule (ties back to Part 2/3): **only shown when load-bearing.** Concretely — shown whenever Direction is BUY or ADD (as the explicit third leg of the attribution chain from Part 6); shown whenever the investor is looking at a not-held or held-undervalued position that *would* reach BUY/ADD except for this one gate (i.e., every other prerequisite is met but status isn't `SUPPORTED`) — this is the single most important case to get right, because it's the concrete answer to "what would change this." Not shown when Direction is HOLD/TRIM/NO_ACTION/Withheld for reasons unrelated to valuation support, to avoid cluttering states where it isn't the operative fact.

**Deliverable 8:** Label table + placement rule above.

---

## Part 9 — Gap Communication

`ValuationSupportGapKind` → plain copy, shown only alongside a non-`SUPPORTED` status that is actually gating BUY/ADD (per Part 8's placement rule):

| Gap | Plain copy |
|---|---|
| `MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT` | "Atlas hasn't yet run this specific check for this company." |
| `NO_DURABLE_GROWTH_BASIS` | "The business doesn't yet show a durable growth basis to check the valuation against." |
| `INSUFFICIENT_HISTORICAL_VALUATION_DATA` | "There isn't enough price history yet to complete this check." |
| `SCENARIO_ENVELOPE_INCONCLUSIVE` | "The downside and upside scenarios span both a gain and a loss — the check can't resolve either way yet." |
| `CONFLICTING_VALUATION_PROOFS` | "Two different ways of checking this gave conflicting answers." |
| `NO_SUFFICIENT_VALUATION_PROOF` | "None of Atlas's valuation checks reached a conclusive answer yet." |

Placement: card-level detail (item 6/9 from Part 3), one tap from Hero — never a tooltip (too easy to miss on the exact fact that matters most for "what would change this"), never surfaced when `SUPPORTED` (no gap to explain).

**Deliverable 9:** Table + placement above.

---

## Part 10 — Evidence Compression Rule

Core does **not** define a principled ranking across strengths or across risks in general. `CaseHighlightView`'s `strengths[]`/`risks[]` order is a fixed evaluation sequence (Growth → Capital Allocation → Valuation, each landing in one array or the other by direction of its own finding) — insertion order, not a severity ranking. Saying so explicitly matters: it would be easy to accidentally invent a "top 3" selection that implies importance where Core doesn't compute one.

**Deterministic rule:** render every item in `strengths[]`/`risks[]` in the Core's own fixed order; never truncate to a subset without a stated, Core-derived reason.

One partial exception already exists and is legitimate, not invented: Hero's "Biggest Concern" field uses `findMostSevereRisk`, which sorts by `RiskStatus` — itself a real, ordinal Core value (`low < moderate < high`), not a fabricated score. That selection is fine to keep because the ranking comes from a real ordinal already in the domain, not from product-side judgment.

**Deliverable 10:** Rule above — no scoring invented; one existing exception justified.

---

## Part 11 — "What Would Change My Mind?"

Only counterfactuals mechanically derivable from `select_direction`'s own branch logic — no invented reasoning:

| Current state | What would change it |
|---|---|
| HOLD (held, fairly valued) | "Would change if either the business assessment strengthens or the price becomes undervalued." |
| NO_ACTION (not held) | "Would change if the business assessment strengthens, the price becomes attractive by Atlas's valuation check, and Atlas's downside-aware valuation-support check resolves favorably." |
| Reachable-but-for-ValuationSupport (the case Part 8 flags as load-bearing) | "Would change if Atlas's downside-aware valuation check resolves favorably — see Downside Support above." |
| TRIM (held, expensive or weakening) | "Would change if the price becomes less expensive or the business assessment stabilizes." |
| Withheld | "Would change once [the specific missing evaluation from Part 5] is available." |

This section only ever restates a real branch of `select_direction`/the DE-008 hard gate — never a hypothetical the Core doesn't already encode.

**Deliverable 11:** Table above.

---

## Part 12 — Holding Context Treatment

BUY/NO_ACTION are unheld-only; ADD/HOLD/TRIM/EXIT are held-only (DE-008's position partition) — this is a hard structural fact, not a judgment call, and should be stated as plainly as the Direction itself: "You don't currently hold this" / "You hold {X}% via {allocation}" directly above the Direction sentence, exactly as the identity header already does. The distinction between BUY and ADD, or between TRIM and EXIT, must read as **what the evidence supports given your current position** — a fact about Direction, not a portfolio-optimization suggestion ("you're overweight," "rebalance to 5%"). Portfolio Intelligence is explicitly incomplete (per this sprint's own constraint) — nothing here should imply a sizing recommendation Atlas doesn't actually compute.

**Deliverable 12:** Above — current header treatment already correct; the constraint is "don't add more than this."

---

## Part 13 — Calmness Test

| Component | Informed | Oriented | Calm | Able to inspect |
|---|---|---|---|---|
| Direction badge + sentence | ✓ | ✓ | ✓ (desaturated tone, no icon urgency) | ✓ (tap for chain) |
| Downside Support label (Part 8) | ✓ | ✓ | ✓ (neutral phrasing, no red/green flashing) | ✓ (gap copy one tap away) |
| Analysis Depth / Conviction / Outlook Conviction (Part 7) | ✓ | ✓ (now disambiguated) | ✓ | ✓ |
| "What would change this" (Part 11) | ✓ | ✓ | ✓ — framed as information, not a countdown | ✓ |
| Decision capture form (Part 19) | ✓ | ✓ | ✓ — no "confirm" button styled as urgent | n/a |

No component in this design uses color to signal urgency beyond the existing `StatusTone` system (`positive`/`caution`/`critical`/`neutral`), no countdown, no "other investors are..." social proof, no red pulsing badge.

**Deliverable 13:** Table above.

---

## Part 14 — Transparency Test

Every visible claim in this design traces to a named Core field: Direction → `RecommendationDirection`/`RecommendationWithheld`; Downside Support → `ValuationSupport.status`/`.gap`; Analysis Depth → `ConvictionAssessment.level`; Conviction → `RecommendationConvictionLevel`; Outlook Conviction → `HorizonOutlook.conviction`; Biggest Strength/Concern → `CaseHighlightView`; "What would change this" → the literal branch of `select_direction` that would need to flip. Nothing in this design introduces a synthesized number, an inferred score, or a claim with no Core field behind it.

**Deliverable 14:** Traceability above.

---

## Part 15 — Progressive Disclosure Model

The suggested 4-layer model validates against, and mostly already matches, the live structure:

- **Layer 1** (glance, above fold): Direction, holding state, one-line why, risk flag if material.
- **Layer 2** (one tap, Key Metrics-equivalent): Conviction/Analysis Depth, Downside Support (when load-bearing), Outlook corroboration, Biggest Strength/Concern.
- **Layer 3** (section-level detail): full Business Analysis, Risk, evidence lists, full Outlook panel, "what would change this."
- **Layer 4** (deep/tab-level): raw evidence references, gap-kind detail, Decision/Outcome history, ValuationSupport-derived gap copy in full.

Adjustment vs. the current implementation: Downside Support and "what would change this" are new Layer-2 citizens; everything else is a relabeling or reordering of existing sections, not a new layer.

**Deliverable 15:** Validated 4-layer model above.

---

## Part 16 — Desktop Information Architecture (text wireframe)

```
┌─ Identity: Ticker · Company · Holding state (held X% / not held) ───────┐
│                                                                          │
│  DIRECTION BADGE   "Current evidence supports increasing exposure."     │
│  one-line why (business/valuation tension, if any)                     │
│                                                                          │
│  ── Key Metrics ─────────────────────────────────────────────────────  │
│  Conviction    Analysis Depth    Downside Support*    Expected Return   │
│  Outlook corroboration line (if available)                              │
│                                                                          │
│  Biggest Strength │ Biggest Concern │ Current Priority                  │
│  Risk flag (if material)                                                │
│  "What would change this" (if applicable)*                              │
│  As of {freshness}                                                      │
└──────────────────────────────────────────────────────────────────────┘
  Supports the Case │ Challenges the Case
  Growth · Valuation · Financial Health · Business Quality (terse cards)
  Business Quality · Financial Strength · Governance · Capital Allocation ·
    Competitive Position (expandable, evidence one click away)
  Financials (expandable)
  Atlas Outlook (Short-Term / Long-Term)
  ── tabs: Decision History · Timeline · Last Activity · Outstanding Work ·
     Outcomes · More Details ──
  [Decision capture panel — collapsed by default]
```
`*` = new in this design (Parts 7, 8, 11).

**Deliverable 16:** Wireframe above.

---

## Part 17 — Mobile Compression

Current gap: no responsive breakpoint exists; Hero's 4-field row and 3-column row both wrap to single columns on narrow viewports, pushing "why," Downside Support, and the risk flag well below first paint.

Design: at `<768px`, compress Hero to exactly what Part 16 calls Layer 1 — Direction badge, one-line why, holding state, risk flag if material — with Key Metrics and Strength/Concern/Priority collapsed behind a single "Details" disclosure directly beneath, not stacked as four/three separately-wrapping rows. This keeps the top of the page understandable without scrolling (the sprint's own explicit requirement) and avoids the horizontal-financial-dashboard pattern by never introducing a horizontally-scrolling metrics strip — the disclosure expands vertically in place.

**Deliverable 17:** Above.

---

## Part 18 — Recommendation → Decision Transition

The existing Add/Trim/Remove/Leave-as-is flow already does the right thing structurally: it opens a form, records a Decision (and optionally an Outcome/Transaction), and never executes anything automatically — no code path in `InvestmentCasePage.tsx` calls a brokerage or trading API. This design keeps that shape exactly. The transition from Recommendation to Decision is: investor reads Direction + reasoning → investor chooses one of accept / disagree-and-record-a-different-conclusion / wait (simply close the panel, no action forced) → if accepting or overriding, investor fills the minimum capture fields (Part 19) → a Decision is recorded, never a trade.

**Deliverable 18:** Above — validates existing flow, adds no trading affordance.

---

## Part 19 — Minimum Decision Capture

Five fields, matching the sprint's own instruction and mapping onto (mostly extending) the existing form:

1. **Chosen action** — existing `decisionType`/position-action selector, unchanged.
2. **Reasoning** — existing free-text reason field, unchanged.
3. **Expected outcome** — new: one short free-text field, distinct from "reasoning" (why vs. what-you-expect-to-happen).
4. **Invalidation condition** — new: one short free-text field ("what would tell you this was wrong").
5. **Time horizon** — new: a small closed set (e.g. short-term / long-term, mirroring Outlook's own two horizons rather than inventing a third scale).

The existing numeric `investorConfidence` (0–100) field is **kept, not flagged as a safety problem** — it is explicitly the investor's own self-reported confidence, never an Atlas-computed number, so it doesn't fall under "no invented confidence percentages" (that constraint governs what Atlas claims about itself). Recommend one copy fix: label it "Your confidence" explicitly, so it's never misread as adjacent to Atlas's own Conviction field.

**Deliverable 19:** Five fields above, one copy fix on an existing field.

---

## Part 20 — History / Learning-Loop Design

`HistoryPage.tsx` already renders an analytical timeline with `DecisionHistoryEntryView`/`OutcomeEntryView`. The natural bridge for Part 19's two new fields (expected outcome, invalidation condition) is to carry them into that same timeline so a past Decision can later be read alongside whether its stated expectation held — but today's Outcome recording is a freeform statement, not structured against an invalidation condition. Building that comparison (was the invalidation condition triggered, yes/no/unclear) is a real product decision with no existing data model to hang it on yet — flagged in Part 24 as **NEEDS PRODUCT DECISION**, not designed further here, since inventing that structure now would be exactly the kind of scope this sprint is told not to take on silently.

**Deliverable 20:** Bridge point identified; structural decision deferred and named explicitly.

---

## Part 21 — Real-State Walkthroughs

**A. BUY** (currently unreachable for any ticker with a real Case in this environment — CRWD/NVDA are the only `SUPPORTED` tickers and neither has a Case yet): First sees "Entry supported" badge + one-line chain sentence. Primary explanation: Biggest Strength + Downside Support present. Limiting factor: none — this is the fully-cleared state. Next action: review reasoning, optionally record a Decision.

**B. ADD**: First sees "Increase supported" + current holding %. Primary explanation: same chain, framed against existing position. Limiting factor: none. Next action: same as A, position-aware.

**C. HOLD**: First sees "Thesis intact." Primary explanation: fairly-valued + business assessment unchanged. Limiting factor: price would need to become undervalued, or business to strengthen, to move toward ADD (Part 11). Next action: no action required; investor may still record a "leave as is" Decision.

**D. TRIM**: First sees "Reduction supported." Primary explanation: business weakening or valuation expensive. Limiting factor: n/a (this is itself the conclusion). Next action: review reasoning, consider recording a Decision.

**E. RecommendationWithheld** (the actual current state for AAPL/MSFT/TSLA — the only tickers with real Cases today, all blocked at the DE-008 hard gate): First sees "Insufficient evidence," non-alarming tone. Primary explanation: named missing stage (Part 5). Limiting factor: the missing evaluation itself. Next action: none forced — informational; investor can still browse existing sections.

**F. ValuationSupport = INSUFFICIENT_INPUT** (the common, expected case per DE-015 §8 — includes every real Case in this environment that isn't NVDA/CRWD): No visible change vs. `NOT_SUPPORTED` at the Direction level (both behave identically per DE-016's proven invariant) — Downside Support reads "Valuation conclusion unresolved," gap copy from Part 9 explains why, "what would change this" names the same gap.

**G. Business WEAK but ValuationSupport SUPPORTED** (a real, reachable combination — DE-016 proved SUPPORTED alone never produces BUY/ADD when Business is weak): Direction shows NO_ACTION/TRIM, not BUY/ADD, precisely because Business gates first. Downside Support may still show "present" as a factual, secondary field, but the Direction sentence never credits it alone — this is exactly the scenario Part 6's full-chain-attribution copy exists to prevent from reading as a contradiction.

**H. Strong Business but unresolved ValuationSupport**: Direction shows HOLD or NO_ACTION depending on holding/valuation state, not BUY/ADD. Biggest Strength shows the strong business finding. Downside Support shows "unresolved" with gap copy — this is the single most instructive state for "what would change this," since every other prerequisite is met.

**Deliverable 21:** Eight walkthroughs above, each grounded in real, previously-validated backend behavior (the BUY/ADD reachability matrix and real-company runs from this session's earlier validation sprints) rather than hypothetical states.

---

## Part 22 — Copy Audit

Scanned `en.ts`'s existing `decisionSupport.*`/`investmentCase.hero.*`/`investmentCase.keyMetrics.*` keys: already clean — no enum member names, no "gate," "pipeline," "engine," or ADR IDs leak into user-facing strings today. The audit obligation for *this* sprint's new copy (Parts 6–9, 11) is to hold that same bar: no `ValuationSupportStatus`/`GapKind` member names, no "Core," "hard gate," "DE-015/DE-016," no fabricated certainty language. Every table in Parts 6–11 above is written to that standard already; no further rewrite is needed before Figma.

**Deliverable 22:** Confirmed clean baseline; new copy held to the same standard.

---

## Part 23 — Figma Handoff Specification

**Page:** Investment Case detail (existing route, no new page).

**New/changed components:**
- `HeroCard` — add two optional fields to its Key Metrics row (Downside Support, conditionally rendered per Part 8's placement rule) and a new "What would change this" block (Part 11), conditionally rendered. Rename existing "Conviction" field to "Analysis Depth" (Part 7).
- New small "gap explanation" inline-expandable block, reusable wherever Downside Support or Withheld reasons need one-tap detail (Parts 5, 9) — same interaction pattern `ExpandableDetail.tsx` already provides for Company Health cards; reuse that component rather than building a new one.
- `AtlasOutlookSection` — relabel its Conviction badge to "Outlook Conviction" (copy-only change).
- Decision capture form — add three fields (expected outcome, invalidation condition, time horizon) per Part 19; relabel existing confidence field to "Your confidence."
- Mobile: Hero collapses to Layer 1 + a single "Details" disclosure at `<768px` (Part 17) — no new component, a responsive variant of the existing Hero layout.

**States to design:** Direction × {BUY, ADD, HOLD, TRIM, NO_ACTION, Withheld} × {Downside Support shown/hidden} × {mobile/desktop} — the walkthroughs in Part 21 cover the representative combinations; Figma doesn't need every cross-product, just A–H plus the mobile collapse of any one of them.

**Content examples:** every copy string used above is real, final English copy — Figma can drop it in verbatim rather than using placeholder text.

**Interaction behavior:** all new disclosures use tap-to-expand (matching `ExpandableDetail`'s existing pattern), never hover-only (Part 9's explicit "never a tooltip" instruction), never a modal.

**Responsive behavior:** per Part 17 — no separate mobile page, one responsive Hero variant.

Not in scope for this handoff: colors, spacing, typography, iconography — this is component/content/state/interaction only, per the sprint's explicit "not a full visual redesign" instruction.

**Deliverable 23:** Handoff spec above.

---

## Part 24 — Implementation Boundary

| Item | Classification |
|---|---|
| Direction copy refinement (Part 4, 6) | READY TO IMPLEMENT — copy-only change to existing `decisionSupport.*` keys |
| Analysis Depth / Conviction / Outlook Conviction relabeling (Part 7) | READY TO IMPLEMENT — copy-only, no schema change |
| Downside Support field + gap copy (Parts 8, 9) | **NEEDS PRODUCT DECISION on API surface, then READY TO IMPLEMENT** — requires adding `valuation_support.status`/`.gap` to `InvestmentCaseAnalysisView`/schemas.py (additive field, same pattern every prior CanonicalAnalysis field addition has followed) before frontend work starts |
| "What would change this" (Part 11) | READY TO DESIGN IN FIGMA now; implementation needs the same additive API field as above once Downside Support exists, since several of its branches reference it |
| Mobile Hero collapse (Part 17) | READY TO IMPLEMENT — frontend-only, no backend dependency |
| Decision capture field additions (Part 19) | READY TO IMPLEMENT — additive form fields + additive persistence fields, same low-risk shape as existing Decision recording |
| History/invalidation-condition comparison (Part 20) | **NEEDS PRODUCT DECISION** — no data model decision made yet; do not build ahead of that decision |
| RecommendationConvictionLevel exposure (referenced in Part 7) | **NEEDS PRODUCT DECISION on whether to expose it at all in Beta**, then an additive API field — BLOCKED BY CORE only in the trivial sense that the field must be added to the wire schema; the Core object itself already exists and is correct |
| Figma visual design (Part 23) | READY TO DESIGN IN FIGMA — this document's component/state/copy list is sufficient to start without reopening product semantics |

Nothing here is BLOCKED BY CORE in the sense of requiring an ADR change or new domain logic — every item is either a copy/relabeling change, an additive API field surfacing an already-correct Core value, or an explicitly-deferred product decision with no invented interim behavior.

**Deliverable 24:** Table above.

---

## Final Verdict

**READY FOR FIGMA.**

Every component, state, and copy string in Parts 4–21 is either implementable today as a copy-only change or requires only an additive API field surfacing a Core value that already exists and is already correct — no ADR redesign, no new Recommendation/Valuation/Conviction semantics, no invented scoring. The two items marked NEEDS PRODUCT DECISION (Part 20's invalidation-condition comparison, and whether to expose `RecommendationConvictionLevel` in Beta at all) are named explicitly rather than buried, and neither blocks the rest of this design — Figma can proceed on everything else in parallel.

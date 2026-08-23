# Atlas Beta — Sprint 1 — Figma Implementation Review

**Stance:** implementation-readiness review, not a design review. Every field on every screen is traced to a real Core object or flagged as missing. No redesign is proposed anywhere in this document — where a Figma element has no Core owner, that is reported as a blocker with the smallest fix named, never resolved here.

**Screen model.** The Figma reviewed is one screen — **Investment Case / Recommendation Detail** — rendered across six Recommendation-direction states (BUY, ADD, HOLD, TRIM, NO_ACTION, RECOMMENDATION_WITHHELD) plus a compressed mobile layout. It is not six different screens; it is one template with six content variants. This matches the real, already-partially-built `InvestmentCasePage.tsx` + `HeroCard.tsx` architecture (built earlier this Beta program) — this sprint is substantially an alignment/completion pass on an existing screen, not a greenfield build.

**Prior finding this review does not repeat in full.** `UX-022` already performed a field-by-field validity audit of this exact Figma and found the same invalid elements this review independently re-confirms below under a stricter test (*"no UI field may exist without a corresponding Core object"*). Where this review's finding matches `UX-022`, it says so and points there for the corrected copy/labels, rather than re-deriving them.

---

## 1. Screen-by-Screen Analysis

### Screen: Investment Case / Recommendation Detail (states: BUY, ADD, HOLD, TRIM, NO_ACTION, WITHHELD; desktop + mobile)

**Figma page:** the single MSFT/JNJ/GOOGL/RIVN/TSLA flow shown in Flow 1 (desktop) and Flow 2 (mobile).

**User flow:** investor navigates from Portfolio (or Watchlist/Dashboard) into a specific company's Investment Case, reads Atlas's current Recommendation and its reasoning, optionally expands "Why Atlas thinks this" / "What limits this conclusion," optionally follows "View valuation detail," and ends at "Record my decision" (or, in the Withheld state, an acknowledgment before continuing).

**Major UI components (as drawn):** ticker/company header; Direction badge + one-line headline; holding-context line; "Limited by:" single-line summary; Valuation card (headline + one sentence + "View valuation detail" link); "Why Atlas thinks this" expandable (3 bullets); "What limits this conclusion?" card (1–2 items + "What would Atlas need to become more confident?" link); a 5-metric horizontal strip (Fair Value Range / Current Price / Earnings Growth / Dividend Yield / Atlas Conviction); an Outlook card (one paragraph); a Risk Assessment card (one paragraph); a footer CTA ("Record my decision" or, Withheld, "Acknowledge and continue").

**Information presented:** company identity, current Recommendation Direction and rationale, holding size, one dominant limiting factor, a compressed evidence list, a compressed risk list, five headline metrics, an Outlook summary, a Risk summary, and a path into Decision capture.

**Intended purpose:** let an investor understand, at a glance, what Atlas currently concludes and why, per `APP-000`'s explainability principle and `UX-021`'s own hierarchy design.

---

## 2. Core Mapping

| Figma element | Owning Core object | API source | ViewModel | Frontend component (existing) |
|---|---|---|---|---|
| Ticker, company name, sector/industry | `CompanyProfile` | `CompanyProfileView` | `InvestmentCaseAnalysisView.companyProfile` | header block, `InvestmentCasePage.tsx` |
| "Analysis current as of [date]" | `CanonicalAnalysis.generated_at` | `generatedAt` | same | header/Hero freshness line |
| Direction badge | `RecommendationDirection` (via `describe_recommendation`) | `RecommendationStateView.level`/`badgeLabel` | `DecisionSupportLevel` | `HeroCard.tsx` badge — **content must be "Entry supported"/"Increase supported"/"Thesis intact"/"Reduction supported"/"No action supported," never the raw word shown in this Figma** |
| One-line headline | `DecisionSupportLevel.statement` | `RecommendationStateView.statement` | same | `HeroCard.tsx` |
| Holding context (weight %, value) | `HoldingContextView` | already on `InvestmentCaseAnalysisView` | same | existing header block |
| Holding context (**share count**) | `AlphaHolding` (Portfolio domain) | **not currently on `HoldingContextView`** — needs verification against `AlphaHolding`'s own field set before assuming it's a one-line addition | — | — |
| "Limited by:" one-line summary | no single existing field — a synthesis of `ValuationSupport.gap` / highest-severity `RiskFinding` | none today | none today | **new**, per `UX-021` Part 3/11's evidence-compression rule (reuse Core's own fixed ordering, never a new ranking) |
| Valuation card headline + body | `ValuationSupport.status`/`.gap` | `ValuationSupportView` (added this Beta program) | already wired | **not yet rendered as a standalone card** — currently only a Key-Metrics badge in `HeroCard.tsx`; the Figma's card treatment (headline + explanation + "View valuation detail") is new composition over an already-real field |
| "Why Atlas thinks this" bullets | `CaseHighlightView` (`strengths[]`) | already on `InvestmentCaseAnalysisView` | `STRENGTH_SENTENCE_KEY` (already implemented) | `InvestmentArgumentSection.tsx` — **content must be the real categorical sentences this bank already defines, never the specific percentage claims this Figma shows** |
| "What limits this conclusion?" items | `RiskFinding` (`business_risk`/`financial_risk`/`valuation_risk`/`thesis_risk`) or `ValuationSupport.gap` | `risks[]` / `ValuationSupportView.gap` | `CHALLENGE_SENTENCE_KEY` (already implemented) / `UX-022`'s gap-copy table | `InvestmentArgumentSection.tsx`'s Challenges column — same caveat: real categories only |
| "What would Atlas need to become more confident?" | `RecommendationWithheld.reason`/`.missing_evaluations` (Withheld only) or the "What Would Change This View" derivation | partial — Withheld reason is real and available; the non-Withheld version is **not yet a built field** | none today (non-Withheld case) | **new for non-Withheld states**, per `UX-021` Part 11 (mechanical restatement of the real `select_direction` branch, not invented) |
| Current Price | `MarketSnapshotView.sharePrice` | already on `InvestmentCaseAnalysisView` | same | already fetched, not yet placed in this exact strip position |
| Atlas Conviction (label + value) | `ConvictionAssessment.level` (5-value) | `ConvictionAssessmentView` | already wired | `HeroCard.tsx` already renders this — **under the corrected label "Analysis Depth" per this Beta program's `M-1` correction, not "Atlas Conviction"** |
| Outlook card | `OutlookView.shortTerm`/`.longTerm` (expected-return range, momentum, key drivers) | already on `InvestmentCaseAnalysisView` | already wired | `AtlasOutlookSection.tsx` already exists — the Figma's one-paragraph "12–24 month" summary is a *different, unbacked* content shape from this real, already-built section |
| Risk Assessment card | `RiskAnalysisResult` (4 real categories) | `RiskAnalysisView` | already wired | `AtlasReasoningSection.tsx`/`CompanyHealthAssessmentSection.tsx` already render this per-category — the Figma's one-paragraph summary is again a different, unbacked shape |
| "Record my decision" CTA | Decision capture flow | existing `DecisionRecord`/`Decision` write path | existing form | already implemented, already copy-aligned with `UX-021` Part 18/19 — **this one element needs no correction** |
| Fair Value Range | *(none)* | — | — | **no Core owner — see Blocker B-1** |
| Earnings Growth (%, "est.") | *(none)* | — | — | **no Core owner — see Blocker B-2** |
| Dividend Yield (%) | *(none)* | — | — | **no Core owner — see Blocker B-3** |
| "Portfolio concentration approaching threshold" / "Adding would bring Technology sector weight above preferred range" (MSFT ADD) | *(none)* | — | — | **no Core owner — see Blocker B-4** |
| "Quality Guarantee" card (RIVN Withheld) | *(none — not a Core or doctrine concept)* | — | — | **no Core owner — see Blocker B-5** |
| RIVN Withheld reasons ("Insufficient data reliability," "Rapid change") | *(none — not real `RecommendationWithheld.reason` values)* | — | — | **no Core owner — see Blocker B-6** |
| "Acknowledge and continue" gate (Withheld) | *(none — no doctrine specifies an acknowledgment gate)* | — | — | **not a Core-backed interaction — see Blocker B-7** |

---

## 3. Missing Data

Every item below was independently re-checked against the real repository this session, not assumed from the earlier `UX-022` finding:

- **Fair Value Range.** No implemented Valuation capability produces a price-bracketed range. `DE-015`'s `ValuationSupport` is categorical only; `outlook.py`'s Expected Return is a percentage return over time, explicitly disclaimed as "never a price target" in its own module docstring. The master doctrine's §5 "range, never points" language is aspirational and was never built into a real, callable capability.
- **Earnings Growth (%, "est.").** No forward-earnings-estimate field exists anywhere in `FinancialPeriodView` or elsewhere — only historical actuals (`netIncome`, `eps` per period).
- **Dividend Yield (%).** `FinancialPeriodView.dividends` exists but is a raw historical dollar amount (a cash-flow line item), not a yield ratio. No yield computation exists anywhere.
- **Portfolio concentration threshold / "preferred sector weight range."** `DE-003`'s Allocation/Concentration factors are real and computed, but purely descriptive (what a position *is*), never prescriptive (what it *should* stay under). No investor-settable or system-defined threshold exists anywhere in `atlas/` — confirmed by direct grep this Beta program (zero `Constraint`/`InvestorPreference`/limit domain objects).
- **"Quality Guarantee" doctrine.** Not a concept in any adopted doctrine document. `RecommendationWithheld` (`DE-001` §2) is defined as the honest absence of a directional conclusion, never as an active, named "protective" policy Atlas asserts about itself.
- **RIVN's specific Withheld reasons.** `RecommendationWithheld.reason`/`.missing_evaluations` trace to the real DE-008 hard gate (Business/Valuation/Portfolio Intelligence/Reasoning `EvaluationState`, or `EvidenceCoverageLevel`). "Insufficient data reliability" and "Rapid change" are not members of that real taxonomy.
- **"Acknowledge and continue."** No doctrine document specifies a gated acknowledgment step before a Withheld case can be used; DE-001 §2 requires Withheld to read as a legitimate, immediately-usable conclusion state, not a dead end requiring confirmation.

None of these are proposed as future capabilities to build in this document — per the sprint's own instruction, they are named as gaps only.

---

## 4. Backend Requirements

**Already real, already exposed (no work required):**
- `RecommendationStateView` (direction badge label/statement)
- `HoldingContextView` (weight %, value)
- `ValuationSupportView` (status/gap — wired this Beta program)
- `ConvictionAssessmentView`
- `CaseHighlightView` (`strengths[]`/`risks[]`)
- `OutlookView` (both horizons)
- `RiskAnalysisView`
- `MarketSnapshotView.sharePrice`
- Decision-capture write endpoint

**New, but composed entirely from already-real data (additive, no new Core computation):**
- A `limitingFactor` field/endpoint addition: server-side selection of the single highest-priority real item (`ValuationSupport.gap` when load-bearing, else the highest-severity real `RiskFinding`, per `DE-003`'s/`RiskStatus`'s own real ordinal — no new ranking invented, reusing the exact rule `UX-021` Part 10 already specifies).
- A "what would change this" derivation for non-Withheld states: a mechanical restatement of the specific `select_direction` branch that would need to flip (`UX-021` Part 11 already specifies the exact mapping per Direction).
- Confirmation (or a small additive field) that `AlphaHolding` exposes share count through to `HoldingContextView`, if not already present.

**Cannot be built without new doctrine (out of scope for this sprint, named in Section 3):** Fair Value Range, Earnings Growth, Dividend Yield, portfolio concentration threshold, any RIVN-specific Withheld-reason taxonomy beyond the real one, any "Quality Guarantee" copy.

---

## 5. Frontend Requirements

- **Reuse, not rebuild:** `HeroCard.tsx`, `InvestmentArgumentSection.tsx`, `AtlasOutlookSection.tsx`, `AtlasReasoningSection.tsx`, `CompanyHealthAssessmentSection.tsx` already exist and already render the real underlying data this Figma is trying to show, in a different (already-approved, `UX-017`–`UX-020`) layout. This screen's job is primarily **re-composition of existing, working components into the new Figma layout**, not new data-fetching logic.
- **New, small components:** a "Limiting Factor" single-line summary component (consumes the new backend field above); a Valuation Support card wrapper (consumes the already-real `ValuationSupportView` under `UX-021`/`UX-022`'s safe labels, in the card shape this Figma proposes rather than the current Key-Metrics-row placement).
- **Copy layer:** every badge, headline, and card label must resolve through `en.ts`/`sv.ts` translation keys carrying the corrected copy (`decisionSupport.*`, `investmentCase.valuationSupport.*`, already committed this Beta program) — never the literal strings shown in the Figma's own Copy Specification table.
- **Mobile:** the existing responsive collapse pattern (`UX-021` Part 17) applies directly; no new mobile-specific data or component is required beyond what desktop already needs.
- **State/routing:** no change — this remains the existing `InvestmentCasePage.tsx` route and data-fetch pattern (`/api/cases/:id/analysis`), already proven working this Beta program (verified live against a real case during the `M-2` wiring work).

---

## 6. Integration Requirements

- **Backend → frontend mapping:** one request (`GET /api/cases/:id/analysis`) already returns everything needed except the two new derived fields (limiting factor, what-would-change-this) — both additive to the same response, no new endpoint required.
- **Loading flow:** unchanged from the existing page — a single fetch, existing loading/error states already implemented (`InvestmentCaseAnalysisFetchStatus`).
- **Error handling:** unchanged — existing pattern already covers `loading`/`error`/`loaded`.
- **Rendering order:** header → Hero (badge, headline, holding context, limiting factor) → Valuation Support card → Why Atlas thinks this → What limits this conclusion → Key Metrics (real subset only) → Outlook → Risk → Decision CTA — this order matches both the Figma's own layout and `UX-021`'s already-approved hierarchy (Part 3, Part 16), so no reconciliation is needed between the two.

---

## 7. Implementation Blockers

Each blocker below is genuine — a specific Figma element cannot be built as literally shown, not a preference for a different design.

**B-1 — Fair Value Range.** *Impact:* the 5-metric strip cannot show this field on any screen without fabricating a number. *Minimum viable resolution:* remove the field from the strip; `UX-022` already specifies this exact removal.

**B-2 — Earnings Growth.** Same impact/resolution shape as B-1; `UX-022` already specifies removal.

**B-3 — Dividend Yield.** Same; `UX-022` already specifies removal.

**B-4 — Portfolio concentration threshold (MSFT ADD's "Limited by" and "What limits this conclusion" content).** *Impact:* this exact limiting-factor content cannot be shown for ADD states without inventing a threshold Core doesn't compute. *Minimum viable resolution:* substitute the real, highest-priority limiting factor for that case (a real `RiskFinding` or `ValuationSupport.gap`) via the new backend field in Section 4 — never a concentration/sector-weight claim.

**B-5 — "Quality Guarantee" card.** *Impact:* the Withheld screen cannot ship this card without asserting a doctrine that doesn't exist. *Minimum viable resolution:* remove the card; `UX-022` already specifies the one permitted sentence in its place ("Atlas does not have enough evidence to support a directional conclusion yet").

**B-6 — RIVN's specific Withheld reasons.** *Impact:* cannot show "Insufficient data reliability"/"Rapid change" without inventing a reason taxonomy. *Minimum viable resolution:* render the real `RecommendationWithheld.reason`/`.missing_evaluations` for whichever case is actually being viewed — content is per-case and real, already available.

**B-7 — "Acknowledge and continue" gate.** *Impact:* no doctrine supports gating a Withheld screen behind acknowledgment before further use. *Minimum viable resolution:* remove the gate; the page should be immediately usable, exactly as every other Direction state already is.

**No blocker below Critical/structural severity was found** — every other element of this screen maps cleanly to an already-real, already-fetched Core field, and the majority of the actual React components already exist and are already wired to real data from earlier this Beta program.

---

## 8. Recommended Build Order

1. **Fix the copy/data layer first (B-1 through B-7), before any component work.** These are pure content corrections against already-real fields (or removals) — zero new backend logic, lowest risk, and prevents shipping fabricated data even transiently.
2. **Build the new small backend-derived fields** (limiting factor, what-would-change-this) — additive, small, testable in isolation against the existing test suite pattern.
3. **Re-compose the existing, already-working section components** (`HeroCard`, `InvestmentArgumentSection`, `AtlasOutlookSection`, `AtlasReasoningSection`) into the new Figma layout order — this is layout/composition work over already-correct data, the safest kind of frontend change.
4. **Build the two genuinely new small components** (Limiting Factor line, Valuation Support card wrapper) last, since they depend on step 2's new fields.
5. **Mobile pass** — apply the existing responsive collapse pattern once desktop is stable.

This order front-loads the correction work (cheap, high-confidence) and defers new composition (more design judgment, more visual QA) until the data underneath it is already trustworthy — minimizing the risk of re-doing layout work against data that later turns out to need correction.

---

## Final Output

**1. Overall implementation readiness assessment.** Mostly ready. The large majority of this screen — identity, Direction, holding context, evidence, Outlook, Risk, and Decision capture — is already real, already fetched, and in several cases already rendered by existing components from earlier this Beta program. The gap is narrow but real: seven specific Figma elements (B-1–B-7) have no Core owner and cannot ship as drawn, and two small new derived fields (limiting factor, what-would-change-this) need building before the Figma's own "Limited by" / "What would Atlas need to become more confident" affordances can be honest.

**2. Is Atlas Core sufficient to implement the approved Figma product?** Not as literally drawn — seven elements require either removal or substitution with real content, per Section 7. It **is** sufficient to implement the underlying product intent (a Recommendation, its reasoning, its limiting factor, its Outlook, and a path to Decision capture) — every one of the Figma's genuine information needs has a real Core answer; only a handful of specific fabricated numbers and one invented doctrine card do not.

**3. Prioritized Beta implementation roadmap.** (1) Copy/data corrections (B-1–B-7) — no new code, immediate. (2) Limiting-factor and what-would-change-this backend fields — small, additive. (3) Layout re-composition of existing components into the new Figma order. (4) New Valuation Support card + Limiting Factor line components. (5) Mobile. (6) Decision-capture screen already needs no work.

**4. Which single Figma screen should be implemented first, and why.** **The HOLD state (e.g., JNJ)** — not BUY, despite BUY being the most visually prominent state in the Figma. Reasoning: HOLD is the one state with the fewest blockers (its own "Limited by"/"What limits this conclusion" content — "Valuation fully reflects current business trajectory" — is close to something the real `ValuationSupport`/Valuation findings can actually support, unlike BUY's and ADD's fabricated fair-value and concentration-threshold content), it exercises the full component tree (Hero, Valuation card, Why/What-limits, Outlook, Risk, Decision CTA) without needing the not-yet-real "recommended quantity" content that BUY/ADD's own screens visually emphasize, and it is the direction most real Cases in the current environment are actually near (per this Beta program's own repeated live verification against AAPL/MSFT/TSLA). Building HOLD first proves the entire corrected data pipeline end to end on the lowest-blocker-count state, then BUY/ADD/TRIM/NO_ACTION/WITHHELD each become incremental variations on an already-proven template rather than five parallel first builds.

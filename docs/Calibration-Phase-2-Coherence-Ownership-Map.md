# Calibration Phase 2 — Investment Case Coherence Ownership Map

Investigation & design output from Calibration Phase 1 (Investment Case Coherence
& Recommendation Benchmark) found that the Investment Case page's core problem
was not missing analysis depth — it was that several independently-computed
backend signals were surfaced as if they each answered the same user-facing
question. This document names the one canonical, presentation-level owner for
each concept in the Product Rule's four questions, per Calibration Phase 2
Phase 1's own instruction: "no two independent engines should render separate
answers to the same user-facing question."

Every ownership decision below was verified against the real source (not
assumed) during Calibration Phase 1's investigation, and every fix in this
document has been implemented and live-verified against real Investment Cases
(MSFT, NVDA, AMZN) as of this sprint.

## What changed vs. what stays disclosed independently

Two different repair strategies apply, and this document is explicit about
which one each concept got:

- **Single canonical owner** — one engine's answer is now the only thing shown
  for that question; other engines that used to compete for the same UI slot
  either had their output relabeled to what it actually measures, or were
  removed from that slot because they had no real, ongoing use elsewhere.
- **Disclosed, distinguished signals** — two engines answer two genuinely
  different questions that happen to sound similar. Nothing was merged or
  hidden; only the *labels* changed so the difference reads as intentional
  rather than as a bug.

Deleting or silently discarding an underlying signal was never the fix
(Phase 1's own instruction) — every concept below still has its full
underlying data available somewhere on the page.

---

## 1. Recommendation

**Canonical owner: `Stance` (`atlas.alpha.stance.engine.determine_stance`).**

Stance is the superset judgment — it reads Conviction, Recommendation
(Decision Support), Risk, Coverage, Change Intelligence, *and* Portfolio Fit,
a strictly wider and later-computed input set than Decision Support's gate
alone (confirmed by reading `determine_stance`'s own source, not assumed from
its docstring). It is now the first thing `HeroCard` renders in the
non-withheld branch — before the narrower Decision Support statement, which
remains real, correctly computed, and visible immediately below it as
supporting detail, not a second headline.

**Disclosed, not replaced:** `DecisionSupportLevel`/`report.recommendation`
(`atlas.alpha.decision_support`) — the narrower, trade-evidence-support
question ("does current evidence support a position change") — still renders,
directly under Stance, in `HeroCard`'s own narrative paragraph and in the
Executive Summary Bar's "Recommendation" badge. Both are real, both are
independently useful; only their visual ranking changed.

**Removed as a competing verdict:** the page header's own "Status" badge
(`deriveCaseStatus`/`CaseStatusLevel`, values `healthy`/`needs_review`/
`high_priority`, rendered as "Healthy"/"Worth a look"/"Time-sensitive"). This
answered a workflow-triage question ("does this case need review"), not an
investment-direction question, but sat in the exact header position — right
beside the ticker — where a reader expects a directional verdict. Confirmed
live: NVDA showed "Status: Worth a look" beside "Reduction supported," a
severe, first-five-second contradiction. `deriveCaseStatus`/`CaseStatusLevel`
had no other consumer anywhere in the frontend, so removed entirely rather
than relabeled-and-kept-unused.

Files: `frontend/src/investmentCase/HeroCard.tsx`,
`frontend/src/routes/InvestmentCasePage.tsx`,
`frontend/src/investmentCase/deriveExecutiveSummary.ts`.

---

## 2. Open Questions

**Canonical owner: `analysis.keyOpenQuestions` (`atlas.analysis_engine.investment_case_synthesis`).**

This is the curated, business-analysis-specific open-question list — each
entry traceable to one real analytical condition (a Growth/Capital
Allocation/Valuation finding that did not reach a conclusive status). It is
now the sole source for both the Hero's compact "Open Question" card
(`primaryOpenQuestionKey`, resolved via `OPEN_QUESTION_ORIGIN_KEY`) and its
count (`openQuestionCount`), the same source `InvestmentArgumentSection`'s
full list already used.

**Disclosed, not merged:** `report.openQuestions`
(`atlas.decision_engine.stages.reasoning._open_questions`) is a genuinely
different concept — an evidence-*linkage* gap list (is a Decision linked to a
real Observation, is an Observation linked to real Evidence), not a business
open question. It remains real, computed, and available; it is no longer read
by the Hero or the header's case-status computation. Its natural home going
forward is inside the Evidence/Coverage detail, not under the "open
questions" label, since a reader conflates the two under the shared English
word.

**Confirmed bug, root cause:** the Hero's `primaryOpenQuestionKey` prop was
never passed by `InvestmentCasePage.tsx` at all (defaulted to `null`,
rendering "Open questions: None" unconditionally), while `openQuestionCount`
read the wrong (evidence-linkage) list — two independent bugs compounding
into the confirmed "Open questions: None" while three real questions were
listed below it.

Files: `frontend/src/routes/InvestmentCasePage.tsx` (HeroCard call site).

---

## 3. Conviction vs. Evidence

**Two real, distinct concepts — kept distinct, relabeled where they collided.**

- **Conviction** ("how strongly can Atlas support the recommendation") —
  `atlas.analysis_engine.conviction`/`RecommendationConviction`, gated by
  Decision Readiness, evidence coverage, contradiction presence, and stage
  completeness. Unchanged.
- **Evidence/Coverage** ("how strong and complete is the underlying
  information") — `atlas.alpha.coverage`, a per-dimension evaluation-state
  read. Unchanged in computation; the Atlas Rating Model's own numeric
  scorecard tile that re-expresses it (`deriveEvidenceRating`, a disclosed
  average of `overallCoverage`/`overallConfidence`) was labeled **"Evidence"**
  — the identical word Conviction's own `insufficient_evidence` reason uses
  for a different fact. Relabeled to **"Coverage"**
  (`investmentCase.ratings.evidence.label`) so the two no longer compete for
  the same word on the same page. The underlying computation is byte-for-byte
  unchanged; only the label moved.

Confirmed, not a contradiction (investigated during Phase 1, re-confirmed
here): Recommendation Conviction, Decision Reliability, and Evidence Quality's
own confidence-adjacent fields were checked against each other and found to
be genuinely non-duplicative by construction — each composes, never
independently recomputes, the others.

Files: `frontend/src/investmentCase/atlasRatingModel.ts`,
`frontend/src/i18n/translations/{en,sv}.ts`.

---

## 4. Recommendation Drivers

**Canonical owner: `report.strengths` + `report.risks` (`CaseHighlightView[]`, `atlas.analysis_engine.investment_case_synthesis`).**

No new selection logic was introduced. `strengths[]`/`risks[]` were already
the closed, decisive-only classification `InvestmentArgumentSection`'s own
"Supports the Case"/"Challenges the Case" columns read (STRONG business →
Strength, WEAK → Risk, MODERATE → neither; UNDERVALUED/EXPENSIVE valuation →
Strength/Risk, FAIRLY_VALUED → neither; LOW/HIGH risk → Strength/Risk,
MODERATE → neither — each category's own evaluator, unmodified). Combined
into one ranked, capped-at-5 list (`deriveRecommendationDrivers`) and
rendered under the Hero's new "Why Atlas thinks this" heading, reusing the
identical sentence bank (`STRENGTH_SENTENCE_KEY`/`CHALLENGE_SENTENCE_KEY`)
`InvestmentArgumentSection` already used — the same fact, worded identically,
in both places.

Files: `frontend/src/investmentCase/deriveExecutiveSummary.ts`,
`frontend/src/investmentCase/HeroCard.tsx`.

---

## 5. What Would Change

**Canonical owner: `RecommendationReasoning.what_would_change` (`atlas.analysis_engine.recommendation`), now genuinely populated.**

This field existed and was reserved for exactly this purpose but was never
populated by any code path. A new closed vocabulary
(`ChangeTriggerKind` — six members) and a pure selection function
(`_derive_what_would_change`) were added to `atlas/analysis_engine/recommendation.py`,
reading the same categorical facts `select_direction` already reads to pick
the Direction (Growth/Capital Allocation status, Valuation Support status,
Valuation status, the high-risk flag) — no new analysis, no new investment
model, only a fixed, disclosed priority order over already-computed
conclusions (risk > valuation support > growth > capital allocation >
valuation). `NO_CREDIBLE_TRIGGER_IDENTIFIED` is a real, distinct member —
returned, and shown, whenever nothing in that priority chain applies, per the
explicit "say so honestly" instruction, never silence standing in for "not
computed."

Live-verified as genuinely case-specific: MSFT (no weak dimension found)
returns "Atlas has not identified a specific condition that would change this
view."; NVDA and AMZN (both flagged `has_high_financial_or_valuation_risk`)
both return "A reduction in financial or valuation risk" — the same real fact
selected consistently, not a fixed string.

Files: `atlas/analysis_engine/recommendation.py`,
`atlas/alpha/investment_case/api/schemas.py` (wire field),
`frontend/src/status/statusTone.ts` (`ChangeTriggerKind`/`CHANGE_TRIGGER_KEY`),
`frontend/src/investmentCase/HeroCard.tsx`.

---

## 6. Risk / Upside / Horizon

**Canonical owner: `atlasRatingModel.ts`'s `deriveRisk`/`deriveUpside`/`deriveHorizon`, rendered once, in `SevenCategoriesSection`, directly adjacent to the Hero.**

No second computation of these three exists anywhere else on the page. They
were deliberately *not* duplicated into the Hero's own summary bar: since
`SevenCategoriesSection` renders immediately after `HeroCard` with no
intervening content, duplicating Risk/Horizon into the Hero bar would recreate
the redundancy problem Phase 1's audit flagged elsewhere (Atlas Reasoning vs.
Company Health Assessment's overlapping dimension cards), not solve it. The
two components are read together as one adjacent unit.

---

## 7. Valuation (header label)

**Two real, deliberately independent facts — the header now names which one it shows.**

`ValuationStatus.fcfYieldStatus` (vs.-own-trading-history comparison) and
`ValuationSupportStatus` (capital-deployment verdict, `ValuationSupportCard`)
are designed to diverge — `atlas.analysis_engine.valuation.support`'s own
docstring states the invariant explicitly (a company can be priced worse than
its own history has ever offered and still be a strong place to commit new
capital, and vice versa). This is not a bug; it is a real, disclosed tension.
The header line was relabeled from bare **"Valuation"** to **"Valuation vs.
own history"** so the two facts stop reading as one contradicting itself.

Files: `frontend/src/routes/InvestmentCasePage.tsx`,
`frontend/src/i18n/translations/{en,sv}.ts`.

---

## 8. Evidence Completeness / Missing Information (not yet consolidated)

Three independently-computed "what's missing" signals remain on the page,
each from a genuinely different taxonomy: Coverage's `missing_dimensions`
(business-analysis dimensions), Portfolio Fit's own `dataGaps` (six Fit
dimensions), and Evidence Quality's fact-kind-count warnings. Stance's own
`missingInformation` already correctly reuses Coverage's list verbatim — the
right pattern, not yet applied to the other two. **Not fixed this sprint** —
flagged in the Implementation Roadmap (Risk Assessment section of the sprint
report) as the natural next step once the Level 3/4 restructuring (Phase 8)
gives these three panels a real, shared home to be consolidated under.

---

## Reference: full contradiction-to-fix mapping

| Contradiction (Phase 1 ID) | Fixed this sprint | How |
|---|---|---|
| C1 — "Open questions: None" vs. 3 real questions | Yes | §2 above |
| C2 — Evidence completeness (Coverage vs. Evidence Quality) | No | Genuinely distinct, no single owner needed; flagged for future consolidation (§8) |
| C3 — Three "missing information" lists | No | §8 above |
| C4 — Header Valuation vs. Valuation Support | Yes | §7 above |
| C5 — Decision Support statement vs. Stance stacked | Yes | §1 above |
| C6 — Header "Status" badge vs. Recommendation | Yes | §1 above |
| C7 — "Evidence" word used for two concepts | Yes | §3 above |

# Calibration Phase 6 — Valuation & Expected Return Calibration

Phase 5 gave Atlas a real Business Quality signal. This document is Phase
1–2's required audit and Phase 5's required "document before implementing."

## Part A — Valuation Engine Audit (Phase 1)

**Only one real valuation method exists**: `ValuationMethodKind.FCF_YIELD_RELATIVE`
— current FCF yield (`FCF / market_cap`) vs. this same company's own historical
FCF-yield observations. `SCENARIO_BEAR`/`SCENARIO_BASE`/`SCENARIO_BULL` are the
other three `ValuationMethodKind` members and are permanently, honestly
`INSUFFICIENT_INPUT` — the identical "closed enum, some members structurally
locked" pattern `BusinessCategory` already established. The method's own module
docstring states the choice explicitly: *"Chosen over P/E, EV/EBITDA, or a full
DCF precisely because it needs the fewest unsupported assumptions."* Confirmed
by exhaustive grep: **no DCF, terminal multiple, peer, or comparable-company
logic exists anywhere in this codebase.** The rule table has no numeric
threshold at all — "cheap"/"expensive" are always relative to the company's own
recorded history, never a fixed yield percentage.

A separate, already-real system, `ValuationSupport` (`DE-015`, status
"ADOPTED — Alpha," genuinely implemented not stubbed), answers a narrower
question — *does today's price offer a **prospective positive return** under
historically-grounded scenarios* — via two independent, non-probability-weighted
proof paths (a scenario envelope built from the company's own historical growth
and yield range; a net-cash path). Its own doctrine's **Zero-Boundary Doctrine**
states zero is the *only* permitted threshold anywhere in it — no margin-of-safety
percentage, no hurdle rate, no risk-free spread. Its own **Rejected Alternatives**
list explicitly rejects `UNDERVALUED ≡ SUPPORTED`, probability-weighted synthesis,
and **Outlook-as-input** — Outlook and ValuationSupport are deliberately
independent, non-feeding siblings, not a pipeline.

## Part B — Expected Return Model Review (Phase 2)

`atlas/analysis_engine/outlook.py` (1189 lines) is already a mature, extensively
self-documented system — Short-Term (valuation re-rating only, no forward growth
assumption, cumulative, 6–12mo) and Long-Term (historical growth + terminal
reversion, annualized, 36–60mo via a disclosed 4-year compounding midpoint).
Every return figure reduces to a pure **yield ratio** — `(current_yield /
target_yield) - 1` for Short-Term, `((1+g)^years) * (current_yield/terminal_yield)`
annualized for Long-Term — deliberately constructed so `market_cap` (and
therefore share price and share count) algebraically cancels out.

**This is not an oversight — it is a disclosed, evidence-based exclusion.**
Real AAPL `SHARES_OUTSTANDING` history contains an undetected ~7x
consecutive-period jump (a real stock split with no split-adjustment marker in
the raw data) that would corrupt any share-count-based CAGR into a fabricated
"massive dilution" signal, with "no principled, non-arbitrary way to detect or
correct a split boundary." Margin is excluded from the arithmetic for the
identical reason — "no principled forward-expansion rule exists." A dedicated
test, `test_capital_allocation_never_enters_the_return_arithmetic`, proves this
by execution: real buyback/debt-reduction evidence changes the Capital
Allocation *driver's direction* but leaves `expected_return.low_percent`/
`high_percent` byte-for-byte identical. A second, structural guardrail test
asserts `OutlookAssumption` has no field with "margin" or "share" in its name at
all. **Any redesign that reintroduces share-count or margin into the numeric
arithmetic reopens a known, already-diagnosed data-corruption hazard and is out
of scope for this sprint.**

Growth, Risk, and Capital Allocation already interact with Outlook today —
**informationally, never arithmetically** — via `key_drivers`
(`OutlookDriverKind`: `VALUATION_RERATING`, `REVENUE_TREND`, `GROWTH`,
`CAPITAL_ALLOCATION`, `FINANCIAL_RISK`, `BUSINESS_RISK`, `VALUATION_RISK`,
`FCF_GROWTH_TREND`, `DEBT_TREND`, `MARGIN_TREND`), each a real `STRONG→POSITIVE
/ MODERATE→NEUTRAL / WEAK→NEGATIVE` mapping off an already-computed Finding's
own status — never a new computation. Conviction and Coverage already reach
Outlook too: `_outlook_conviction` is a *bounded derivation* of case-wide
Conviction (Calibration Phase 4's own redesign target, which already reads real
company-data coverage) — "never exceeds case-wide Conviction; forced to
`INSUFFICIENT_EVIDENCE` when this horizon's own data requirement is unmet." Long-
Term's own eligibility gate, `_business_trajectory_eligible`, already reads
Growth's full-history status and `TOTAL_DEBT`'s trend before a Long-Term Expected
Return is even attempted.

**The confirmed, real gap**: `atlas.alpha.business_quality_assessment`
(Calibration Phase 5) is never imported by `outlook.py` — confirmed by grep, zero
references. Business Quality (Moat, Management, Reinvestment) currently has
**zero interaction** with Expected Return or its Key Drivers. This is the one
genuine, evidence-confirmed gap this sprint addresses — not an invented one.

Two more disclosed, structural doctrine facts that bound this sprint's design:
`DE-009` (Outlook Ontology) explicitly tested and **rejected** representing
Outlook as a probability distribution — "the worst-fitting candidate tested,"
manufacturing false quantified certainty; scenarios are non-probability-weighted
by design, and probability-weighted synthesis is separately rejected because "it
reintroduces the already-forbidden Expected Return... through a side door."
`DE-014` (Outlook Composition) explicitly rejected collapsing Outlook's several
analytical dimensions into one composite label — "Outlook expresses the actual,
named state of each analytical dimension... never a single collapsed label."
**Neither doctrine is a gap. Both are constraints this sprint's redesign must
honor, not undo.**

## Part C — Valuation Benchmark (Phase 3)

Companies classified by real Business Quality (Phase 5's `overall_level`) ×
`ValuationStatus` (FCF Yield Relative). See the published report for the full
25-company table; 13 of 25 have zero real company data (both axes read
`Unknown`/`Insufficient Input`, unchanged from every prior calibration phase).

## Part D — Quality/Valuation Interaction (Phase 4): documented, not invented

Confirmed by reading the code, not assumed: **exceptional/strong quality
currently does not widen or raise Atlas's acceptable valuation range in any
way** — `FCF_YIELD_RELATIVE`'s classification is computed identically regardless
of Business Quality, exactly as it should be (a company's own historical yield
range is a fact about its trading history, not something Business Quality should
be allowed to override). **Reinvestment runway currently does not extend Long-
Term eligibility or widen its scenario range** — `_business_trajectory_eligible`
reads only Growth/debt-trend, never Reinvestment. **Moat currently has no
influence on long-term value** at all — confirmed absent. **Cyclicality has no
data source and cannot reduce valuation confidence** — Atlas has no cyclicality
signal anywhere in this codebase; this remains an honestly disclosed, unassessed
dimension, not something this sprint fabricates.

## Part E — Expected Return Redesign (Phase 5)

**The redesign is deliberately narrow, additive, and informational-only** —
matching every constraint documented in Parts B and D. Moat and Reinvestment
(not Management — its dominant real sub-signal, Capital Allocation, is already
a Long-Term driver; adding a second Management driver risks double-counting the
identical underlying evidence under two different labels, a disclosed scope
decision, not an oversight) become two new, informational `OutlookDriverKind`
members — `MOAT` and `REINVESTMENT_OPPORTUNITY` — mirroring the exact,
already-established pattern every other Long-Term driver uses:

```
Moat EXCEPTIONAL/STRONG              -> POSITIVE
Moat MODERATE                        -> NEUTRAL
Moat WEAK                            -> NEGATIVE
Moat UNKNOWN                         -> no driver constructed

Reinvestment EXCELLENT/GOOD          -> POSITIVE
Reinvestment MODERATE                -> NEUTRAL
Reinvestment LIMITED                 -> NEGATIVE
Reinvestment UNKNOWN                 -> no driver constructed
```

**Architecture boundary respected, not bent**: `outlook.py` (`analysis_engine`,
Core) cannot import `atlas.alpha.business_quality_assessment` — the same
one-way boundary Calibration Phase 4/5 already established and respected. The
two new `OutlookDriverKind` members are added to Core's closed vocabulary (a
pure data-model addition — `build_outlook` itself never constructs one, exactly
like a future capability could add a new closed-vocabulary member without every
existing producer needing to construct every member), and the *construction* of
`OutlookDriver` instances of these two kinds happens at the alpha layer, in a
new, pure function `derive_outlook_quality_drivers` in
`atlas.alpha.business_quality_assessment`. At the API view layer — the exact
place `businessQualityAssessment` was already wired in Phase 5 — these two
drivers are concatenated into the serialized `longTerm.keyDrivers` list
alongside Core's own. The Core `Outlook` domain object itself is never mutated;
only its *view* gains two more real, named, traceable entries.

**The return arithmetic itself — `_rerating_return`, `_annualized_return`,
every constant, every gap check — is completely unchanged.** No new threshold,
no probability weight, no collapsed score. This is deliberately the smallest
change that satisfies "Expected Return must reflect Business Quality... multiple
supporting signals should interact" without reopening the stock-split hazard or
violating `DE-009`/`DE-014`.

## Part F — Scenario Engine Review (Phase 6)

Bull/Base/Bear are already real, already non-probability-weighted by explicit,
adopted doctrine (`DE-009` §5), and already avoid false precision (ranges
derived from the company's own real historical observations, not an invented
distribution). **This sprint recommends no change to scenario generation
itself** — adding probability weights would violate `DE-009`'s own explicit
rejection ("reintroducing the already-forbidden Expected Return... through a
side door"), and no evidence from the benchmark replay (Part C) suggests the
existing ranges are unhelpfully wide or narrow. The one real, disclosed
improvement available without touching doctrine is exactly Part E's addition:
Long-Term's scenarios keep their existing growth/terminal-yield construction
unchanged, while the horizon's own `key_drivers` — which an investor reads
alongside the range to judge how much to trust it — now include the two
business-quality signals that were previously invisible there.

## Part G — What this sprint deliberately does not do

No change to `cash_flow.py`, `support.py`, `eligibility.py`, `scenario_proof.py`,
`net_cash_proof.py`, `synthesis.py`, or `proof.py` — the valuation/`ValuationSupport`
machinery is already correct, already doctrine-adopted, and no genuine defect
was found in it. No change to `_rerating_return`/`_annualized_return`/any
`ExpectedReturnRange`/`OutlookScenario` field. No new probability model. No
company-specific threshold or exception anywhere.

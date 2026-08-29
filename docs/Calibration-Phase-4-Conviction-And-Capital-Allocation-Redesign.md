# Calibration Phase 4 — Conviction & Capital Allocation Redesign

Calibration Phase 3 traced two systematic recommendation errors to exact source
lines: Conviction is capped at `insufficient_evidence` for every company
regardless of analysis quality, and Capital Allocation reads `weak` for
widely-regarded excellent allocators because it excludes dividends, lets one
stale historical event disqualify the whole category, and sums facts across a
company's entire available history with no recency weighting. This document
is Phase 1–4's required "document the complete model before implementing."

## Part A — Conviction

### A1. Input classification (Phase 1)

`atlas.analysis_engine.conviction.calculate_conviction` takes seven inputs.
Read against their real call site (`atlas.analysis_engine.pipeline
.assemble_analysis`), they split cleanly:

| Input | Real source | Classification |
|---|---|---|
| `business_state` / `valuation_state` | Decision Engine stage outcomes | Atlas's own knowledge — keep |
| `business_conclusive` / `valuation_conclusive` | Growth/Capital Allocation/FCF-Yield findings reaching a real conclusion | Atlas's own knowledge — keep |
| `has_high_financial_or_valuation_risk` | Risk Analysis's own `FINANCIAL_RISK`/`VALUATION_RISK` findings | Atlas's own knowledge — keep |
| `evidence_coverage` | `business_evaluation.evidence_quality.coverage` — literally defined as "how many investor-recorded Observations have linked Evidence" (`decision_engine/contracts.py`'s own `EvidenceCoverageLevel` docstring: "at least one Observation is recorded...") | **User-history — replace** |
| `has_contradicting_evidence` | `reasoning.contradicting_evidence.observation_classifications` — investor-recorded Observations flagged as challenged | **User-history — replace** |
| `has_open_questions` | `reasoning.open_questions` — `decision_engine`'s own evidence-*linkage* gap list (Calibration Phase 2's own ownership map already named this the wrong source for the identical reason) | **User-history — replace** |
| `is_thesis_stale` | 90-day-since-last-investor-Decision threshold (`pipeline.py`'s own docstring) | User-history — **out of scope this sprint**, see A4 |

A prior sprint (`atlas/analysis_engine/analysis_coverage.py`, "Internal Alpha
Fix Sprint 1, Part 2 -- confirmed root cause IA-003") already diagnosed this
almost verbatim: *"`PortfolioHoldingAnalysis.conviction` reads
`insufficient_evidence` for every holding that has no investor-recorded
Observations, even when the same holding has `confidence: full`... That is
not a bug in Conviction -- Conviction is answering exactly the question it
was built to answer."* That sprint's own resolution was to add a **second,
separate** signal (`AnalysisCoverageLevel`) alongside Conviction, deliberately
choosing not to touch Conviction's own definition. Calibration Phase 4's
brief explicitly overrides that prior decision: Conviction itself must stop
requiring investor notes. This document records that override rather than
silently discarding the prior team's reasoning — `AnalysisCoverageLevel`
itself is untouched and remains valid, additive, presentation-differentiated
context (`atlas.alpha.portfolio_cockpit` keeps showing both).

### A2. New model (Phase 2)

`ConvictionLevel` (5 members), `ConvictionReasonCode`, `ConvictionAssessment`,
and `calculate_conviction`'s decision-table *structure* (the branch order,
the five output tiers) are unchanged — only three inputs are re-sourced from
Atlas's own knowledge instead of investor history:

1. **`evidence_coverage: EvidenceCoverageLevel` → `analysis_coverage: AnalysisCoverageLevel`.**
   Reuses `atlas.analysis_engine.analysis_coverage.AnalysisCoverageLevel`
   verbatim (`NO_COVERAGE`/`PARTIAL_COVERAGE`/`SUBSTANTIAL_COVERAGE`) — the
   exact value `assemble_analysis` already computes on the line before
   Conviction's own call, previously unused there. No new type, no new
   computation: `NO_COVERAGE` → `INSUFFICIENT_EVIDENCE` (mirrors the old
   `NOT_APPLICABLE`/`NONE` branch), `PARTIAL_COVERAGE` → contributes to the
   `LOW` branch (mirrors the old `PARTIAL` branch), `SUBSTANTIAL_COVERAGE` →
   passes through (mirrors the old `FULL` branch).

2. **`has_contradicting_evidence` → Atlas's own finding-level contradiction.**
   A `BusinessFinding`/`RiskFinding`/`ValuationFinding` that has *both*
   non-empty `supporting_evidence` and non-empty `contradicting_evidence` at
   once is a genuine internal tension in Atlas's own analysis (e.g. Capital
   Allocation's own two independent signals — capital return and leverage —
   pointing opposite directions), not "one side lost" (which is normal and
   already reflected in `status`). This is a real, already-computed field on
   every finding; no new computation, just a new predicate over existing
   data: `any(f.supporting_evidence and f.contradicting_evidence for f in
   all_findings)`.

3. **`has_open_questions` → the curated, business-analysis-driven open
   questions, not the evidence-linkage gap list.**
   `atlas.analysis_engine.investment_case_synthesis._open_questions` already
   computes exactly this, from `business_analysis`/`valuation_engine` alone
   — both already available inside `assemble_analysis` *before* Conviction's
   own call, with no circular dependency. Promoted from a private function to
   a public one (`derive_case_open_questions`, added to `__all__`) so
   `pipeline.py` can call it without reaching into another module's private
   surface — the only structural change in this whole redesign, and it is a
   widening of an existing module's public API, not a new module.

### A3. Personalization boundary (explicit, per the brief)

Investor Decisions/Observations continue to exist, continue to be recorded,
and continue to feed **Stance** (`atlas.alpha.stance`, which legitimately
reads Change Intelligence — itself investor-decision-adjacent — as one of
six inputs to a *broader* judgment) and **Analysis Coverage**'s sibling
display. They are removed from **Conviction** specifically, per the brief's
own line: *"Past investor decisions may still influence personalization, but
never the analytical conviction itself."*

### A4. Explicitly out of scope

`is_thesis_stale` remains investor-Decision-based and is **not** changed
this sprint. Reclassifying it correctly would need a genuine Atlas-side data-
freshness signal (e.g. "time since last successful enrichment"), which lives
in `atlas.alpha` — a package `atlas.analysis_engine` structurally does not
read (the same boundary that already forces `is_thesis_stale` to be a
caller-supplied parameter today). Building and wiring that signal is real,
separate work, and its impact is far smaller than the other three inputs: it
only ever demotes `HIGH`/`VERY_HIGH` down to `MODERATE`, never gates
`INSUFFICIENT_EVIDENCE` or `LOW` — it was never the mechanism behind Phase
3's "every company reads insufficient evidence" finding. Flagged in the
Calibration Phase 4 report's own risk assessment as a disclosed follow-up,
not silently dropped.

---

## Part B — Capital Allocation

### B1. Confirmed weaknesses (Phase 3)

Read directly from `atlas/analysis_engine/capital_allocation.py`'s own
source and docstring:

1. **Dividends are informational only** — collected, never scored.
2. **A single negative signal disqualifies to `WEAK`, unconditionally** —
   never offset by the other signal being positive, regardless of magnitude
   or age.
3. **Facts are summed across the company's entire available history** — a
   debt-issuance fact from 2011 or 2015 counts exactly as much as one from
   last year.
4. **No cash-generation check** — a company covering its capital returns
   from strong free cash flow and one issuing debt to fund them read
   identically.
5. **No leverage *trend*** — only a static buyback-vs-issuance and
   repayment-vs-issuance comparison; a company actively deleveraging after a
   one-time acquisition-funded debt raise is indistinguishable from one with
   chronically worsening leverage.

### B2. New model (Phase 4)

Four independently-computed signals, each `POSITIVE`/`NEGATIVE`/
`INSUFFICIENT` (a true tie is `INSUFFICIENT` — no invented tie-break):

1. **`capital_return_signal`** — buybacks vs. issuance, unchanged
   comparison logic, but computed **only over each fact kind's most recent 3
   available periods** (a trailing window, not the full history) — a
   concrete, disclosed, general parameter, not a per-company tune. Facts are
   never treated as "zero" when the kind doesn't appear in the window;
   fewer than one fact on either side within the window is `INSUFFICIENT`,
   exactly like today.

2. **`leverage_trend_signal`** — reuses `atlas.analysis_engine.growth
   .classify_metric_trend` **verbatim**, over the full available `TOTAL_DEBT`
   history, the identical reuse `atlas.analysis_engine.risk.financial_risk
   ._debt_trend_signal` already established (never a second trend
   algorithm). Falling debt in every consecutive period → `POSITIVE`
   ("debt reduction should improve the score"); rising in every period →
   `NEGATIVE`; fewer than two periods or a mixed trend → `INSUFFICIENT`,
   never guessed. A trend check over the *direction* of debt, not its
   *level*, naturally stops one old acquisition-funded raise from
   permanently damning the category the way v1's static comparison could:
   a company whose *entire* available `TOTAL_DEBT` history has been falling
   reads `POSITIVE`, not `NEGATIVE`. **Caveat, confirmed by direct testing,
   not assumed:** because `classify_metric_trend` requires every
   consecutive period to agree, a raise still visible anywhere in the
   available history — even years back, with clean deleveraging every
   period since — reads `INSUFFICIENT`, not `POSITIVE`: the same
   already-shipped property `financial_risk._debt_trend_signal` has today,
   inherited by design ("never a second trend algorithm"), not a new
   limitation this evaluator introduces. `INSUFFICIENT` is still strictly
   better than v1's own behavior, which read that company `WEAK` forever
   with no path to recovery — the general, non-company-specific answer to
   "debt issued for a productive acquisition should not automatically
   equal poor allocation" is "no longer automatically negative," not "the
   trend algorithm can distinguish old-and-resolved debt from an ongoing
   worsening trend."

3. **`dividend_signal`** (new) — `POSITIVE` when the most recent available
   `DIVIDENDS` fact is greater than zero; `INSUFFICIENT` when no `DIVIDENDS`
   fact exists at all or the most recent one is zero. **Deliberately never
   `NEGATIVE`** — declining not to pay a dividend is a legitimate capital
   allocation strategy (reinvestment, buybacks-only), not a penalized one;
   this only ever rewards a real, current dividend, never punishes its
   absence.

4. **`cash_generation_signal`** (new) — mirrors `financial_risk
   ._cash_generation_signal`'s exact rule (not imported across the
   business/risk boundary — re-expressed locally in this business-side
   evaluator to avoid a new cross-evaluator dependency): most recent
   `FREE_CASH_FLOW` fact positive → `POSITIVE`; negative → `NEGATIVE`; no
   fact → `INSUFFICIENT`.

**Combination rule** — replaces "any negative disqualifies" with "negatives
must genuinely outweigh positives," and requires real multi-signal
corroboration for the top tier, directly answering "multiple signals should
outweigh isolated events":

```
positive_count = count of POSITIVE among the four signals
negative_count = count of NEGATIVE among the four signals
computable_count = positive_count + negative_count

if computable_count == 0:                       INSUFFICIENT_INPUT
elif negative_count > positive_count:            WEAK
elif positive_count >= 2 and negative_count == 0: STRONG
else:                                             MODERATE
```

A single negative signal against a single positive now reads `MODERATE`
(mixed, honest), not `WEAK` (disqualified). `STRONG` requires at least two
independently-corroborating positive signals and zero negatives — a higher,
more deliberate bar than the old model's own `STRONG`, which needed only two
signals to agree with nothing to disagree.

`CAPITAL_EXPENDITURE` and `SHARES_OUTSTANDING` remain informational-only, as
today — no principled scoring rule for them was designed this sprint, and
inventing one without evidence would violate this sprint's own core
principle.

### B3. What this does *not* do

No debt fact is ever tagged "acquisition" or "distress" — Atlas has no such
data and this sprint adds no new provider or classification. The leverage-
*trend* check is the general, honest substitute: it cannot tell *why* debt
was raised, but it can tell whether the company has been deleveraging since,
which is the closest a fact-only evaluator can honestly get without
fabricating intent.

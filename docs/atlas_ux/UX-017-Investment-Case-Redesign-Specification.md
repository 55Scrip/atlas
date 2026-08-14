# UX-017 — Investment Case Redesign Specification (Internal Alpha)

**Status:** Build-mode specification, not an ontology document. Governed by,
and grounded in, `docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` and `DE-001`
through `DE-014` — no new domain concept is introduced anywhere in this
document. Every interpretive label proposed below is either an existing
backend enum shown in plain language, or a new *narrative framing* of
already-computed, already-real data — never a new analytical judgment Atlas
does not already make. Where the brief that prompted this document asks for
something the current architecture cannot honestly produce, that gap is
named explicitly, not silently filled.

**Scope:** `frontend/src/routes/InvestmentCasePage.tsx` and its direct
supporting modules. No backend ontology change. One small, additive backend
derivation is proposed (§Part B, Financial Health) — a new pure function
over already-available raw data, not a new domain concept.

---

## Part 0 — Current State: What Exists, What's Wrong

### 0.1 What the current page actually is

Three stacked blocks before any tab: an identity header, a standalone
Decision Support badge+sentence, and an `ExecutiveSummaryCard` — not a
unified hero. Below that, a two-column "canonical sections" grid (Atlas
View 7-dot scorecard, Financials table, Valuation Scenarios stub, Business
findings, Company Overview, Evidence summary), then a six-tab bar (Decision
History, Timeline, Last Activity, Outstanding Work, Outcomes, More
Details) whose last tab contains a full narrative detail view **plus** the
legacy raw Core-Loop CRUD forms (Observation/Evidence/Knowledge
Reference/Reasoning Trace/Judgment).

### 0.2 Weaknesses, named specifically

1. **No unified hero.** The three above-the-fold blocks are separately
   composed, not one coherent above-the-fold summary — directly working
   against this brief's own "visible without scrolling" requirement.
2. **`FinancialsTable` is a bare spreadsheet.** Eleven raw metric rows ×
   N period columns, "computes nothing itself" by its own docstring — no
   YoY %, no trend, no interpretation. This is the single clearest
   violation of "Atlas should interpret data, never simply display data"
   anywhere on the page.
3. **Three permanently-empty slots render on every load**: the Expected
   Return dot in Atlas View (always `—`), the `ValuationScenariosSection`
   ("not yet available," sitting directly in the primary two-column
   layout, not tucked away), and `CompanyOverviewSection`'s Founded/CEO/
   Employees rows (hard-coded `—` — no backend field exists for them at
   all). A calm page does not show three guaranteed blanks before the
   investor scrolls.
4. **Valuation is shown three times at three altitudes** (header metadata
   word, Atlas View dot, full detail section) — defensible as progressive
   disclosure, but currently reads as repetition rather than escalation,
   since none of the three is framed as a narrative answer to "why does
   this matter."
5. **Risks are not ranked.** `RiskSection` shows the four risk categories
   in fixed category order, not by severity — directly contradicting this
   brief's explicit "Risks: ranked by importance" requirement.
6. **Recommendation is shown only as a collapsed 7-state badge.** The
   real, already-computed `direction`, `reasoning`, `alternatives`, and
   `portfolioFactors` never reach the wire (`decision_support.py`'s own
   documented Decision Log #1) — meaning "Why Atlas thinks this" cannot be
   built from Recommendation content directly; it has to be assembled from
   Business/Valuation/Risk/Change content instead (§Part A, §2).
7. **Timeline and "What Changed" are two overlapping views of the same
   underlying change data**, nested awkwardly inside one tab rather than
   unified.
8. **Legacy debugging CRUD forms sit inside an investor-facing tab.** The
   Observation/Evidence/Knowledge Reference/Reasoning Trace/Judgment forms
   in More Details are Core-Loop developer tooling, not Alpha investor
   content, and materially increase the page's perceived complexity.
9. **No per-metric interpretation exists anywhere in the codebase.**
   Neither `FinancialsTable` nor `deriveExecutiveSummary.ts` reads
   `financialHistory[]` to produce a Strong/Slowing/Accelerating-style
   framing — this is genuinely new work, not a relabeling exercise (§Part
   B).

### 0.3 What already works and should be preserved

`deriveExecutiveSummary.ts`'s existing discipline — priority is a "what
deserves attention" signal, explicitly never an instruction to
Buy/Hold/Reduce/Exit — is exactly right and should govern every new
interpretive label this redesign adds. The existing refusal to fabricate
Bull/Base/Bear or Expected Return is correct and should be preserved, not
worked around (§0.4). "Details on Demand" (three altitudes of the same
fact) is a sound pattern; this redesign tightens its execution, not its
premise.

### 0.4 The one decision this document cannot make silently

The brief asks the Hero to show, without scrolling: **Recommendation,
Conviction, Outlook, Short-term Expected Return, Long-term Expected Return,
Bull/Base/Bear, biggest opportunity, biggest risk.** Checked against the
actual backend (verified by direct grep, not assumption):

| Requested | Status | What's actually available |
|---|---|---|
| Recommendation | **Partially real** | The 7-state `DecisionSupportLevel` badge is real and on the wire. The raw `direction` (buy/add/hold/trim/exit/no_action) and the 3-level `RecommendationConvictionLevel` are computed server-side but deliberately never serialized (`decision_support.py` Decision Log #1). Only `hold`/`trim`/`no_action` are even reachable today — `buy`/`add`/`exit` are structurally unreachable (`direction_selector.py`, documented at length). |
| Conviction | **Real, at case-wide grain** | The 5-level, case-wide `ConvictionLevel` is real and on the wire. The 3-level, Recommendation-specific `RecommendationConvictionLevel` (`DE-004`/`DE-011`'s own subject) is computed but not exposed. |
| Outlook | **Does not exist.** Confirmed by full-repository grep: zero occurrences related to `DE-009`/`DE-010`'s Outlook anywhere in `atlas/`. | Adjacent, already-real signals exist: `growthAnalysis.recentTrend` (strong/weak/mixed metric), `thesisChange` (strengthened/weakened/mixed/unchanged), `latestChanges[].direction`. These are *not* Outlook — they are narrower, already-computed trend facts that can honestly stand in for "what's moving" without claiming an ontology that isn't implemented. |
| Short-term / Long-term Expected Return | **Explicitly, deliberately refused.** `expected_return` is named on the codebase's own list of values it refuses to fabricate (`decision_engine/contracts.py:365`). No numeric computation exists anywhere. | Nothing. Showing a number here would be fabrication, not interpretation — the single clearest thing this whole eleven-document doctrine corpus (`Doctrine` §5.1, `DE-004` §4, `DE-009` §4) exists to prevent. |
| Bull / Base / Bear | **Explicitly, deliberately refused**, with its own module-level doctrine comment explaining why (`analysis_engine/valuation/scenarios.py`): a real scenario needs a forward assumption this codebase does not have. | Nothing. Same fabrication risk as above. |
| Biggest opportunity | **Real, buildable today** | `strengths[]`, positive `latestChanges[]`, highest-severity favorable finding. |
| Biggest risk | **Real, buildable today** | `findMostSevereRisk` already exists; `risk.findings[]` + `riskProjection`. |

**Resolution adopted for this specification**: the Hero shows every
element that is honestly available, at the grain that is honestly
available, and states — once, calmly, in one place — that scenario-based
Expected Return and Bull/Base/Bear are not yet computed and why, exactly
following the precedent this codebase and this doctrine corpus already set
for Recommendation Withheld (`DE-004` §4: *"a complete, valid... outcome in
its own right, not an error state"*) and for the current page's own
already-correct treatment of the same two gaps (`—`, "not yet available").
**This document does not propose building Expected Return, Bull/Base/Bear,
or literal Outlook computation** — that would be new backend ontology and
analytical work, explicitly out of this session's scope ("do not introduce
new concepts... implement and refine the product using the existing
architecture"). It is named here as a **flagged decision**, not resolved
by silent omission, so the user can redirect if a different trade-off (e.g.
descoping the Hero's promise, or greenlighting the backend work to unlock
these fields) is preferred before implementation begins.

---

## Part A — Experience Specification

Each section below states its one governing question (per the brief), its
content in the honest-availability terms established in §0.4, its states,
and what is explicitly cut from today's page.

### A.1 Hero Summary

**Governing question:** *Should I continue reading?*

**Layout.** One unified card, full width, no internal tabs, entirely above
the fold at standard viewport height. Three zones, top to bottom:

1. **Identity strip** (single line): ticker · company name · exchange ·
   sector. (Case-id and origin badge move to a quiet, small top-corner
   element — not part of the reading flow.)
2. **Decision strip** (the card's visual center of gravity, largest type
   on the page): the `DecisionSupportLevel` badge + its evidence-
   attributed sentence (unchanged source, `recommendation.level` →
   `DECISION_SUPPORT_STATEMENT_KEY`), paired directly beside the
   case-wide Conviction level (`conviction.level`) as a plain-language
   label ("High conviction" / "Moderate conviction," never a number) —
   satisfying `DE-004` §6's "stated together, never collapsed" rule at the
   UI level, not just the data level.
3. **Two-up summary row**: *Biggest opportunity* (from `strengths[]` /
   most favorable material finding) and *Biggest risk* (from
   `findMostSevereRisk`), each one attributed sentence, not a label —
   directly answering the brief's two literal requirements with real data.

**The honest gap, stated once, calmly.** A single small line beneath the
decision strip: *"Atlas does not yet compute a scenario-based expected
return or Bull/Base/Bear range for this company — see Valuation for why."*
This replaces three scattered placeholders (Hero silence, Atlas View's
empty dot, the Scenarios stub) with one clear, honest disclosure, linked to
the one section (§A.3 Valuation) that explains it properly. This is a net
reduction in placeholder surface area, not an addition.

**What's cut from today's Hero-equivalent area:** the standalone Action
Flow Tier-1 buttons move below the fold (§A.2 boundary) — they are
workflow controls, not summary content, and their presence today is a
primary reason the current above-the-fold area does not read as a single
hero.

**States:** loading (skeleton matching the three-zone shape, never a spinner
replacing the whole card); `insufficient_evidence`/Recommendation
Withheld (Decision strip replaced by the existing honest-absence copy,
per `DE-004` §4 — never hidden, never defaulted to Hold).

---

### A.2 Why Atlas Thinks This

**Governing question:** *Why?*

**Content — maximum five cards**, each: **what changed** / **why it
matters** / **what could invalidate it**. The third field is not a new
concept — it is `DE-002` §2.7's "What Could Change This View" mechanism,
already adopted corpus-wide, applied here for the first time at card grain.

**Card source priority** (since Recommendation's own reasoning isn't on the
wire, per §0.4, cards are assembled from the strongest available signals,
ranked):

1. Highest-severity `latestChanges[]` entries (already carry `category`,
   `direction`, and a description — "what changed" is native to this data).
2. `businessAnalysis.findings[]` at `material`/`attention` severity, for
   categories with a real (non-`insufficient_input`) status.
3. `valuationContext` when `fcfYieldStatus` has moved materially since the
   prior snapshot.
4. `thesisChange` when `strengthened`/`weakened` (not `unchanged`/`mixed`).

**"What could invalidate it"** is sourced from the finding's own linked
`openQuestions[]` entry where one exists, or the change's own named
condition where `latestChanges[]` carries one — never a generic hedge,
matching `DE-002` §2.7's own prohibition on vague disclaimers.

**Cap enforcement:** exactly five slots, filled by the priority order
above; if fewer than five real, material-or-above signals exist, show
fewer cards rather than padding with `info`-severity content — consistent
with `DE-002` §2.3's "never populated for the appearance of completeness."

---

### A.3 Investment Drivers

**Governing question:** *Why?* (the supporting detail beneath A.2's headline
cards)

**Content.** `businessAnalysis.findings[]` and `valuation.findings[]`
filtered to `material`/`attention` severity only — `info`-severity findings
are explicitly excluded from this section (available in More Details,
never here). This is the concrete fix for "Atlas filters the noise": the
current `BusinessSection` shows all findings regardless of severity; this
redesign adds severity-based filtering as the section's defining rule.

**Presentation:** one line per driver — category label, current status
word, one-sentence basis — no dot-scorecard duplication of A.1/A.4/A.5's
own content (Atlas View's 7-dot scorecard is retired, its real dimensions
absorbed into the sections that already own them at full detail: Business
here, Valuation in §A.5, Risk in §A.6).

---

### A.4 Financial Health

**Governing question:** *Is the business healthy?*

**The one genuinely new piece of work in this specification.** No
interpretation of `financialHistory[]` exists anywhere today (§0.2, item
9). §Part B specifies the derivation precisely.

**Per-metric row shape** (revenue, operating margin, buybacks/capital
return, debt — the four metrics with enough historical depth to interpret;
other raw rows move to a "full history" disclosure, not deleted):

- **Current state** — the latest period's value, formatted as today.
- **Trend** — a short, named trajectory word (§Part B's exact rule set:
  e.g., Accelerating / Strong / Slowing / Contracting for revenue).
- **Interpretation** — one attributed sentence connecting the trend to
  what it means for the business, in `APP-002` §6's evidence-attributed
  register (never "Accelerating!" alone — always "Revenue growth
  accelerated to X%, up from Y% last period").
- **Investor impact** — one sentence connecting the metric to the
  Investment Case specifically (does this support or pressure the current
  thesis / Business Evaluation conclusion), sourced from the same
  `businessAnalysis.findings[]` content §A.3 already surfaces, not a new
  judgment.

**What's cut:** the eleven-row raw spreadsheet is not the primary view.
The four interpreted rows above are; the full raw table remains available
as an explicit "show full financial history" disclosure beneath them,
preserving every number the page shows today, just not as the first thing
an investor sees.

---

### A.5 Valuation

**Governing question:** *Why now?*

**Content.** One narrative paragraph, not a table: current FCF yield,
its own historical range, and what that comparison honestly means
(`fcfYieldStatus`, already real) — in prose, e.g. *"Current free-cash-flow
yield of X% sits [above/within/below] this company's own three-year range
of Y%–Z%, which Atlas reads as [undervalued/fairly valued/expensive] on a
historical-relative basis."* This is a direct application of `DE-008`
§10.1's already-adopted distinction (historically-relative Valuation
Evidence, never confused with an assumption-based fair-value judgment) —
stated honestly, in the same breath, rather than implied.

**The Expected Return / Bull-Base-Bear disclosure lives here, in full**
(not just the Hero's one-line pointer): *why* Atlas does not compute a
scenario range today (`DE-008` §10.1's own documented reason — no forward
assumption set exists) and what would need to be built before it could.
This consolidates what is currently three separate, under-explained
placeholders into one clear, complete, honest explanation — reducing
placeholder surface area is itself part of "reduce cognitive load."

---

### A.6 Risks

**Governing question:** *What worries Atlas?*

**Ranking, fixing the confirmed gap (§0.2, item 5).** Sort
`risk.findings[]` by `FindingSeverity` (`material` → `attention` → `info`,
`info` collapsed by default), never by fixed category order.

**Per-risk fields**, tested against what the current risk model can
honestly support:

- **Potential impact** — `RiskStatus` (low/moderate/high), in plain
  language, with the specific finding text.
- **Current trajectory** — sourced from `latestChanges[]` entries tagged
  to that risk category (`risk_added`/`risk_removed`, direction) — real,
  already-computed, not new.
- **Monitoring signal** — the specific named condition from that finding's
  linked open question or Counter-Evidence content — again `DE-002` §2.7's
  mechanism, applied at risk grain.
- **Likelihood** — **flagged, not silently included.** The current risk
  model carries one combined `RiskStatus` per category, not a separate
  likelihood axis. Presenting a distinct "Likelihood" field would require
  either inventing a second axis (new ontology, out of scope) or
  quietly relabeling `RiskStatus` as if it already measured likelihood
  (a category error `DE-013`'s own methodology exists to catch).
  **Recommendation: omit Likelihood as a separate field for Internal
  Alpha**, and fold any likelihood-relevant language the underlying
  evidence already supports into the risk's own attributed sentence,
  qualitatively — consistent with "no scoring systems unless logically
  unavoidable." If the user wants a real, separately-tracked Likelihood
  axis, that is new ontology and belongs in its own ADR, not this
  specification.

---

### A.7 Timeline

**Governing question:** *What changed?*

**Content, at honest scope** (§0.4 — Outlook and Expected Return have
nothing to show): Recommendation-level changes (`DecisionSupportLevel`
transitions), Conviction changes, and every `latestChanges[]` category
already covering Business/Valuation/Risk movement (growth, capital
allocation, business quality, business/financial/valuation risk changed,
strengths/risks added or removed) — unified into one chronological feed,
interleaved with Decision/Outcome/Trade history rather than shown as two
separate, overlapping views (fixing §0.2, item 7).

**What's cut:** the separate "Last Activity" and "Outstanding Work" tabs
fold into this one Timeline as filters/sections within it, rather than
remaining separate top-level tabs — this reduces the tab bar from six
entries toward three (Timeline, Outcomes, More Details), directly serving
"reduce cognitive load" at the navigation level, not just the content
level.

---

### A.8 More Details (retained, narrowed)

Everything not covered above that investors may still want on demand:
full financial history table, full risk vector, full evidence/confidence
detail, full narrative thesis text, Portfolio Context detail.

**One explicit removal, not a redesign of this tab's purpose**: the legacy
Core-Loop CRUD forms (Observation/Evidence/Knowledge Reference/Reasoning
Trace/Judgment) are developer/debugging tooling per the file's own
docstring and do not belong in an investor-facing tab under any framing.
Recommend relocating them behind a separate, explicitly-labeled internal/
debug route, not deleting the functionality — this is a page-scope
decision, not a data decision, and is flagged for confirmation before
implementation removes anything.

---

## Part B — Implementation Specification

### B.1 Component tree (proposed)

```
InvestmentCasePage
├── CaseIdentityStrip          (thin, top-corner: case-id, origin badge)
├── HeroCard                   (NEW — replaces header block + StatusBadge
│                                + ExecutiveSummaryCard's top portion)
│   ├── IdentityLine
│   ├── DecisionConvictionRow  (DecisionSupportLevel + ConvictionLevel, paired)
│   ├── OpportunityRiskRow     (two attributed sentences)
│   └── ScenarioGapNotice      (one line, links to ValuationSection)
├── ActionFlowSection          (existing Tier 1/2, moved below Hero)
├── WhyAtlasThinksThisSection  (NEW — max 5 cards, replaces most of
│                                ExecutiveSummaryCard's assessment points)
├── InvestmentDriversSection   (NEW — severity-filtered, replaces
│                                BusinessSection's unfiltered list)
├── FinancialHealthSection     (REBUILT — interpreted rows first,
│                                FinancialsTable retained as "full history"
│                                disclosure beneath)
├── ValuationSection           (REBUILT — narrative paragraph + full
│                                Expected-Return/Bull-Base-Bear disclosure,
│                                replaces ValuationScenariosSection stub +
│                                ValuationDetailSection's top-level split)
├── RisksSection                (REBUILT — severity-sorted, 4-field cards,
│                                replaces RiskSection's fixed-order vector)
├── TabBar                      (NARROWED — Timeline / Outcomes / More Details)
│   ├── TimelineTab              (UNIFIED — absorbs Last Activity,
│   │                             Outstanding Work, What Changed, Decision
│   │                             History into one chronological feed with
│   │                             in-tab filters)
│   ├── OutcomesTab              (unchanged)
│   └── MoreDetailsTab           (narrowed — CRUD forms relocated out,
│                                 everything else retained)
```

**Retired components**: `ExecutiveSummaryCard` (split across `HeroCard` and
`WhyAtlasThinksThisSection`), `AtlasViewSection` (its 7 dots absorbed into
the sections that already own each dimension at full detail — this removes
the 3-permanently-empty-dot problem by removing the component that produced
it, rather than patching around it), `ValuationScenariosSection` (folded
into `ValuationSection`'s single honest disclosure), `CompanyOverviewSection`'s
three dead fields (drop Founded/CEO/Employees rows entirely rather than
rendering guaranteed blanks — restore them only if/when the backend ever
carries real data for them).

### B.2 Data contract per section

| Section | Existing fields (no backend change) | New/changed backend need |
|---|---|---|
| Hero | `recommendation.level`, `conviction.level`, `strengths[]`, risk findings, `companyProfile` | None |
| Why Atlas Thinks This | `latestChanges[]`, `businessAnalysis.findings[]`, `valuationContext`, `thesisChange`, `openQuestions[]` | None |
| Investment Drivers | `businessAnalysis.findings[]`, `valuation.findings[]`, `.severity` | None — filtering is frontend-only |
| **Financial Health** | `financialHistory[]` (raw) | **New**: a small, pure backend derivation (see §B.3) producing per-metric trend + interpretation, mirroring `growthAnalysis.recentTrend`'s existing shape |
| Valuation | `valuationContext.fcfYieldStatus`, `currentYield` (assumed present per existing `ValuationDetailSection`) | None for the narrative; none for the disclosure (static copy) |
| Risks | `risk.findings[]`, `riskProjection`, `latestChanges[]` (risk categories), linked `openQuestions[]` | None |
| Timeline | `decisionHistory[]`, `outcomeHistory[]`, `tradeLog[]`, `latestChanges[]`, `thisChange` — all already fetched today across the existing tabs | None — pure frontend consolidation |

**Deliberately not requested**: raw `RecommendationDirection`, the 3-level
`RecommendationConvictionLevel`, any Outlook field, any Expected Return or
Bull/Base/Bear field. Each would require either new schema exposure of
already-computed-but-hidden data (the first two — a genuinely small,
low-risk backend change if the user wants finer-grained Recommendation
detail than `DecisionSupportLevel` provides) or wholly new analytical work
(the last three — explicitly out of this session's scope). Listed here so
the trade-off is visible, not because this specification asks for them.

### B.3 The Financial Health derivation (specified precisely, since it's the one new module)

A new, small, pure function — same architectural shape as the existing
`recentTrend` computation in `investment_case_synthesis.py`, extended to
four metrics instead of one:

- **Inputs**: `financialHistory[]` (already on the wire), unchanged.
- **Revenue trend**: compute YoY % for the two most recent periods with
  data. `Accelerating` — both YoY% positive and the latest exceeds the
  prior; `Strong` — both positive, roughly stable; `Slowing` — positive but
  the latest is materially below the prior; `Contracting` — latest YoY%
  negative. Four categorical outcomes, no numeric score exposed as the
  primary label (the underlying % appears in the attributed sentence, per
  `APP-002` §6, not as a standalone number).
- **Operating margin trend**: same four-state shape (Improving / Stable /
  Under pressure / Deteriorating), computed from margin % delta across the
  same two periods.
- **Capital return (buybacks + dividends) trend**: qualitative framing
  (Shareholder-friendly / Neutral / Potentially destructive) — "potentially
  destructive" is reserved for the specific, already-adoptable case of
  buybacks continuing while free cash flow is contracting or debt is
  rising (reusing the existing `TOTAL_DEBT` escalation signal already
  wired into Financial Risk, not a new data source).
- **Debt trend**: reuses the already-implemented `TOTAL_DEBT` trend signal
  (built for Financial Risk) directly — no new computation, only a new
  presentation of an existing one.
- **Every output is categorical, never a raw score** — consistent with
  `DE-004` §5's categorical-not-numeric discipline, applied here to a new
  surface for the first time by direct analogy, not by new reasoning.

This is additive to `investment_case_synthesis.py` (or a new sibling pure
module it calls), touches no `analysis_engine`/`decision_engine` ontology,
and introduces no new domain concept — it is a narrative framing of numbers
the API already returns.

### B.4 Translation keys

New `investmentCase.hero.*`, `investmentCase.whyAtlas.*`,
`investmentCase.drivers.*`, `investmentCase.financialHealth.*` (four
metrics × four fields), `investmentCase.valuation.narrative`,
`investmentCase.valuation.scenarioGap.*`, `investmentCase.risks.*` key
groups needed in both `en.ts` and `sv.ts`, parity-checked per this
project's existing localization discipline. Retired component keys
(`investmentCase.atlasView.*`, `investmentCase.valuationScenarios.*`,
`investmentCase.companyOverview.founded/ceo/employees`) should be removed,
not left orphaned.

### B.5 Phasing (suggested, not prescribed)

1. `HeroCard` + `ScenarioGapNotice` (unblocks the most visible change,
   zero backend work).
2. `WhyAtlasThinksThisSection` + `InvestmentDriversSection` (frontend-only,
   reads existing fields with new filtering/prioritization).
3. `ValuationSection` rewrite + `RisksSection` rewrite (frontend-only).
4. Financial Health derivation (the one backend addition, §B.3) +
   `FinancialHealthSection` frontend.
5. Timeline unification + tab-bar narrowing.
6. CRUD-form relocation (a decision item, §A.8 — confirm before removing).

---

## Part C — Decisions Needed Before Implementation

1. **§0.4** — confirm the Hero's honest-gap treatment for Expected Return /
   Bull-Base-Bear / Outlook is acceptable for Internal Alpha, versus
   descoping those three lines from the brief, versus greenlighting the
   (out-of-scope-here) backend work to unlock them.
2. **§A.6** — confirm dropping "Likelihood" as a separate risk field for
   Internal Alpha, rather than inventing a second risk axis.
3. **§A.8 / B.5 step 6** — confirm relocating (not deleting) the legacy
   Core-Loop CRUD forms out of the investor-facing tab.
4. **§B.2** — confirm no request, for this phase, to expose raw
   `RecommendationDirection` or the 3-level `RecommendationConvictionLevel`
   on the wire, even though both already exist server-side.

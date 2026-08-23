# Atlas Product Architecture — Tier 1 (Internal Alpha)

**Product Sprint 1.** This is a product architecture document, not an implementation plan and not code. It describes how Atlas should operate around the five Tier 1 capabilities — Portfolio, Investment Case, Daily Brief, Discovery, Portfolio Fit — using Atlas Core exactly as it already exists. No new domain object, no new ADR, no revisited architectural decision appears anywhere below; every mechanism this document relies on is either already real and cited by file, or is explicitly named as a genuine gap rather than quietly assumed solved.

This document was written against the actual current codebase, not from memory of what Atlas was designed to become. Where a capability already works, it is described as it works today, with citations. Where it doesn't, that is stated plainly, and the gap is scoped as ordinary product/integration work — connecting already-built Core capabilities to already-built product surfaces — never as new ontology.

---

## 0. What Is Already Real (Read This First)

Everything in this document is built from these existing pieces. Nothing below invents a domain concept; every gap this document closes is closed by *wiring together* things that already exist.

| Capability | Real today | Real gap |
|---|---|---|
| **Portfolio** | Holdings (ticker/weight/value/case), concentration (`atlas/domains/portfolio/calculations.py`), cash %, unallocated %, per-holding Conviction/Risk/Confidence/Decision-Support (`portfolio_cockpit`), "Needs Your Attention" (`derivePortfolioActions.ts`) | Sector/geographic diversification (explicitly disclosed as not tracked), performance/returns (not computed anywhere) |
| **Investment Case** | Hero, Atlas Reasoning, Atlas Outlook, Investment Argument, Company Health Assessment, Limiting Factors, Valuation Support, Interpreted Financial Evidence, What Changed, real Change Intelligence diff engine, real "Record Decision" POST | Not yet routed through the new Decision Draft/Assumption/CaseCondition flow (Sprints 9–13) — still posts a bare Decision |
| **Daily Brief** | One real analytical source (Investment Case Change Intelligence), explicitly and deliberately unranked | No unified prioritization; "Today's Priorities" is Portfolio's own Action Center, not Daily Brief's; CaseCondition/Assumption signals (Sprints 10–11) never reach it |
| **Discovery** | SEC ticker lookup (`security_discovery`), a real Case-link path for tickers already held | Cannot discover a genuinely new (not-yet-held) security into a candidate flow; no ranking; no Portfolio Fit |
| **Portfolio Fit** | A named, disclosed placeholder (`PortfolioFitStatus`, `PortfolioFitUnavailableReason.NOT_YET_IMPLEMENTED`, `portfolio_cockpit/models.py`) | The framework itself — this document defines it |
| **Decision Workspace** | Full DecisionDraft → Assumption/CaseCondition → commit-with-reasoning flow, Reasoning Timeline, live UI (Sprints 9–13) | Not yet reachable from Investment Case's own "Record Decision" |
| **Companion** | Persistent, cross-workspace AI chat, grounded in real portfolio/case context, with a real `create_or_open_investment_case` tool | — |

---

## 1. Overall Product Flow

Atlas is a loop, not a pipeline. The investor never "finishes" — every action returns them to a changed Portfolio.

```
Portfolio
  ↓
Portfolio Analysis        (concentration, cash, allocation, risk — already real)
  ↓
Investment Case           (deep, per-holding analysis — already the most mature capability)
  ↓
Daily Brief               (what changed, surfaced only when it matters)
  ↓
Discovery                 (what's new, ranked by fit)
  ↓
Portfolio Fit             (how would this candidate change my portfolio)
  ↓
Action                    (Decision Workspace: Draft → Assumptions/CaseConditions → Decision)
  ↓
Portfolio  (changed)  ──────────────────────────────────────────────┘
```

Two entry points into this loop matter equally for daily use:

- **Maintenance loop**: Portfolio → Investment Case (a specific holding) → Daily Brief (what changed since I last looked) → Action, when something demands it.
- **Growth loop**: Discovery → Portfolio Fit → Investment Case (full analysis of the candidate) → Action.

Both loops terminate at the same place: the Decision Workspace already built in Sprints 9–13. Nothing here proposes a second action surface.

---

## 2. Navigation

Primary navigation maps one-to-one onto the five Tier 1 capabilities, plus the two things that don't fit inside any single capability (a company detail view and account-level settings).

```
Portfolio
Daily Brief
Discovery
Watchlist
Companies (search)
—
Settings
```

**Not primary navigation, reached by drilling in:**
- **Investment Case** — reached from a specific Portfolio holding, Watchlist entry, or Discovery candidate. It is a detail view of a company, never a standalone top-level destination — this matches how it already behaves (`investment-case/:caseId`, `company/:ticker`).
- **Decision Workspace** — reached only from an Investment Case's own "Record Decision" action, or from a Daily Brief/Discovery entry that names a specific next step. It is never browsed to directly.
- **Portfolio Fit** — not a page. It is a panel/lens that appears *inside* Discovery (evaluating a candidate) and *inside* Portfolio (reviewing an existing holding's own contribution). Giving it a standalone nav destination would misrepresent what it is: a way of looking at something else, not a thing in itself.

**Explicitly removed from primary navigation for Internal Alpha:**
- **Dashboard** — no evidence it serves a purpose Portfolio + Daily Brief don't already cover together; Portfolio becomes the landing page, matching the mission's own stated order ("we should be able to manage a real portfolio inside Atlas" comes first).
- **History** — the underlying data (Decision Timeline, Change Intelligence history) is not deleted or disabled; it simply stops being a primary nav destination. Tier 3.
- **Platform Status** — kept, but as a utility link under Settings, not primary nav.

This is deliberately five items plus one utility link — the same count as the five Tier 1 capabilities, on purpose. Nothing is added that doesn't already have a Tier 1 justification.

---

## 3. Portfolio

Every field named below already exists in the running code (`atlas/alpha/portfolio/`, `atlas/domains/portfolio/calculations.py`, `atlas/alpha/portfolio_status/`, `atlas/alpha/portfolio_cockpit/`, `atlas/alpha/portfolio_intelligence/`). Nothing here is a new computation.

### Portfolio Overview
The landing view. Shows, precisely:
- Total portfolio value (sum of holdings' `value_absolute` + `cash_value_absolute`, where value is known — never fabricated for holdings with no entered value)
- Cash % and cash value (`cash_weight_percent`/`cash_value_absolute`, already real)
- Unallocated % (`100 − Σweight% − cash%`, already real)
- Number of holdings, number of Watchlist entries
- Portfolio-level concentration read (`concentration_level`: LOW/MODERATE/ELEVATED/HIGH — already real, never a numeric score)
- The three-tier "Needs Your Attention" summary (already real, from `derivePortfolioActions`) — count only here; detail lives in Holdings

### Holdings
One row per position. Shown per holding, all already computed today:
- Ticker, weight %, value (if entered)
- Conviction (qualitative level, already real — never shown as a number)
- Decision Support level (the non-imperative translation already established — `ENTRY_SUPPORTED`/`THESIS_INTACT`/`NO_ACTION_SUPPORTED`/etc., never the raw BUY/SELL direction, which is deliberately never surfaced)
- Attention flag, if any (reason drawn from the existing `AttentionCategory` vocabulary: missing case, decision without outcome, stale thesis, etc.)
- A link into that holding's Investment Case — the only way deeper detail is reached

### Allocation
Weight % per holding, cash %, and unallocated %, presented as a simple ordered breakdown (largest position first). This is arithmetic already computed; no new model.

### Risk
Two layers, both already real, never merged into one score:
- **Per-holding**: `risk_projection` and the full `risk_findings` vector already computed by Portfolio Cockpit
- **Portfolio-wide**: the existing `key_findings` vocabulary from Portfolio Intelligence — `HIGH_CONCENTRATION`, `ELEVATED_CONCENTRATION`, `LARGE_UNALLOCATED`, `MULTIPLE_MISSING_CASES`, `MULTIPLE_STALE_CASES`, `MULTIPLE_EVIDENCE_GAPS`

### Diversification and Exposure
**Honest gap, not filled here.** Sector and geographic exposure are not tracked anywhere in Atlas today — the existing Portfolio page already discloses this directly rather than inventing a placeholder chart ("Sector data isn't tracked for holdings yet"). This document keeps that discipline: diversification and exposure remain explicitly unavailable for Internal Alpha. The one diversification signal Atlas *can* honestly show today is position-level concentration (above), which is not the same claim and must never be presented as if it were.

### Concentration
Fully real, used directly: `largest_weight` and `top_five_weight` against the existing thresholds (`≥35%` → HIGH, `≥25%` → ELEVATED). No new threshold, no new computation.

### Performance
**Honest gap, not filled here.** No cost basis, return, or P&L calculation exists anywhere in Atlas. This is not accidental — it is consistent with Atlas's own already-established philosophy (UX-008: "The Decision Workspace evaluates the quality of the reasoning, not the performance of the stock"). Internal Alpha does not need a performance number to be useful; it needs the reasoning behind each holding to be visible and current, which Investment Case and Daily Brief already provide. Performance tracking is Tier 2 at the earliest, and only if a real, non-fabricated data source for cost basis is available.

### Cash
Fully real, used directly: `cash_weight_percent`, `cash_value_absolute`.

---

## 4. Investment Case

This is already Atlas's most complete capability. This section describes how the existing sections should be read together for Tier 1, and names the one real integration gap.

### What already exists, and stays exactly as it is
- **Hero** — recommendation (via Decision Support level, never raw direction), conviction, valuation support, price, expected return, biggest strength/concern/priority
- **Atlas Reasoning** — four cards: Growth, Valuation, Financial Health, Business Quality
- **Atlas Outlook** — Short-Term and Long-Term panels: expected return, scenarios, conviction, momentum, key drivers
- **Investment Argument** — Supports the Case / Challenges the Case, from real strength/risk findings
- **Company Health Assessment** — five expandable cards (Business Quality, Financial Strength, Management & Governance, Capital Allocation, Competitive Position), each with supporting/contradicting/missing evidence
- **Limiting Factors** — up to two real "what limits this conclusion" items
- **Valuation Support**, **Interpreted Financial Evidence** — real, unchanged

### What Atlas automatically generates
Everything above is generated automatically by `InvestmentCaseCompositionService.build()` on every load/recompute — the investor writes nothing to produce this view. The only investor-authored content anywhere on the page is the Decision itself (reason, confidence) and, going forward, DecisionContext/Assumptions captured through the Decision Workspace.

### What updates automatically, and how changes are highlighted
Change Intelligence already does exactly this, precisely:
- A new snapshot is captured on every recompute, but writes are content-hash-idempotent — reloading with no new underlying data never fabricates a change.
- Comparison produces named `ChangeFinding`s across business-category status, risk-category status, valuation status, and strength/risk highlights, plus one overall `ThesisImpact`: **strengthened / weakened / mixed / unchanged**.
- The existing "What Changed" section is where this surfaces on the page. Nothing new is proposed here — this same signal is the one Daily Brief (§5) needs to actually prioritize, and today does not consume with any structure.

### The one real integration gap
"Record Decision" today issues a bare `POST /decisions` — it bypasses the entire Decision Draft → Assumption/CaseCondition → commit-with-reasoning flow built in Sprints 9–13. For Tier 1, Investment Case's own "Record Decision" action should open the Decision Workspace (already fully built and live) instead of posting directly. This is wiring an existing entry point to an existing destination — no new capability on either side.

---

## 5. Daily Brief

**Philosophy.** Atlas should never show everything. The existing code already enforces this once, correctly, in one place — Daily Brief's own Change Intelligence entries are deliberately unranked today specifically *because* the team already rejected inventing an importance/urgency number. This document keeps that discipline and extends it: prioritization is achieved through **category and role**, never through a fabricated score. This is the same anti-false-precision pattern already governing Conviction, Risk, and Confidence everywhere else in Atlas — Daily Brief should not be the one place that breaks it.

### The real gap
Today, Daily Brief has exactly one analytical source (Change Intelligence). "Today's Priorities" is not Daily Brief's own — it's Portfolio's Action Center, reused. Meanwhile, two real signals built in Sprints 10–11 never reach Daily Brief at all: CaseCondition evaluation transitions (especially Invalidation-role conditions being satisfied) and Assumption challenges. This is the actual, closeable gap: Daily Brief should union these already-real sources, not invent a fourth one.

### Prioritization (categorical, not numeric)
Ordered groups, each internally alphabetical (matching the existing, deliberate non-ranking-within-group convention):

1. **Invalidation triggered** — a CaseCondition with `role: invalidation` has transitioned to satisfied. This is the single highest-urgency category that exists in Atlas today by ontological definition (ADR-CC-001 §4: an Invalidation Condition is "specifically designated to warrant re-entry into the Decision Workspace when met") — Daily Brief should treat it as such.
2. **Thesis weakened** — `ThesisImpact = weakened` from Change Intelligence, or an Assumption transitioned to `invalidated`.
3. **Needs attention** — a Monitoring-role CaseCondition satisfied, or an Assumption `challenged`, or an existing Portfolio "Needs Your Attention" item.
4. **Notable change** — `ThesisImpact = strengthened` or `mixed`.
5. **Routine** — `ThesisImpact = unchanged` updates and non-invalidation CaseCondition revisions. Collapsed by default.

### Grouping
Within each urgency tier, group by scope: Portfolio positions, Watchlist entries, Portfolio-wide (the existing Portfolio Intelligence `key_findings`, which belong to no single ticker).

### Recommended actions
Each entry names one plain, non-imperative next step, reusing language patterns already established elsewhere in Atlas (Decision Support's own "never imperative" discipline):
- Invalidation triggered → "Reconsider in the Decision Workspace"
- Thesis weakened / needs attention → "Review in Investment Case"
- Notable change → "Worth a look"
- Routine → no action named; visible only if expanded

---

## 6. Discovery

**Philosophy.** Discovery finds companies the investor doesn't yet hold, and tells them, honestly, how a new position would sit next to what they already own. Today it can do neither for a genuinely new ticker.

### Candidate sourcing
Reuse `security_discovery`'s existing SEC ticker lookup — already real, already correct, currently wired only into Decision-level `security_confirmation`. Discovery's own "Review a Company" should call the same lookup, removing the current restriction that only tickers already held can be reviewed. This is wiring, not new capability: the lookup already exists and already works.

### Ranking
No score. Every candidate is described the same way an existing holding is described in Portfolio — qualitatively, across the same dimensions Portfolio Fit (§7) already defines. "Ranking" means grouping candidates by qualitative Portfolio Fit read (e.g., candidates with no overlap and a positive diversification effect surface before candidates that would concentrate an already-large position), never a sorted numeric list.

### How Portfolio Fit affects ranking
Portfolio Fit (§7) is applied to every candidate the moment it's reviewed — this is the connective tissue between Discovery and Portfolio that does not exist today. A candidate that would significantly increase an already-elevated concentration level, or substantially overlaps an existing holding's own thesis, is flagged exactly the way Portfolio's own concentration signal already flags an existing holding — same vocabulary, same thresholds, applied one step earlier.

### What Discovery does not need
Its own chat surface. Companion already provides a persistent, cross-workspace conversational layer with a real `create_or_open_investment_case` tool, grounded in the same portfolio/case context Discovery itself would need. Building a second chat interface inside Discovery would duplicate an already-shipped capability — explicitly avoided.

---

## 7. Portfolio Fit

This section fills the placeholder Atlas's own code already named: `PortfolioFitStatus`, `PortfolioFitUnavailableReason.NOT_YET_IMPLEMENTED` (`portfolio_cockpit/models.py`). The product already anticipated this capability structurally; this is its definition — a framework, not a scoring model.

**Governing rule, stated once and applied everywhere below:** every dimension reports a qualitative read using vocabulary Atlas already has elsewhere (the same LOW/MODERATE/ELEVATED/HIGH scale Concentration already uses; the same qualitative levels Conviction and Decision Support already use). No dimension is ever combined into a single number. If two dimensions disagree, both are shown — Atlas does not resolve the tension into a false, tidy synthesis.

Portfolio Fit evaluates one candidate (existing holding or Discovery candidate) against the current Portfolio, across six dimensions:

1. **Overlap** — does this candidate's own thesis substantially duplicate an existing holding's? Read: None / Partial / High, naming the specific holding if any. Derived by comparing the candidate's Investment Case reasoning (Atlas Reasoning categories, already real) against existing holdings' own.
2. **Diversification impact** — the one dimension precisely computable today: would adding this position increase or decrease `concentration_level`, using `atlas/domains/portfolio/calculations.py` exactly as it already exists, unmodified, at the candidate's proposed weight.
3. **Valuation** — reuses Investment Case's own existing Valuation Support finding directly. No second valuation methodology.
4. **Quality** — reuses Company Health Assessment's own existing five categories directly, applied to the candidate.
5. **Portfolio impact** — the arithmetic effect of adding this position at a given size: resulting weight %, resulting cash/unallocated %. Pure existing math, no forecasting.
6. **Expected contribution** — reuses Investment Case's own existing "expected return" field from Atlas Outlook directly. Not a new return model — the same number Investment Case already shows for an existing holding, computed for the candidate instead.

**Output shape:** a short narrative summary (matching Hero's own existing "biggest strength/concern" pattern) plus the six qualitative reads. Never a "Fit Score."

---

## 8. Data Flow

```
External Data                     (business data providers — already real)
  ↓
Normalization                     (BusinessRecord versioning — already real)
  ↓
Company Knowledge                 (Observations, Evidence, Core Loop — already real)
  ↓
Investment Case                   (InvestmentCaseCompositionService.build() — already real)
  ↓
Portfolio Analysis                (Cockpit, Status, Intelligence — already real)
  ↓
Daily Brief                       (union of Change Intelligence + CaseCondition + Assumption signals — the §5 gap)
  ↓
Discovery / Portfolio Fit         (candidate sourcing + qualitative fit read — the §6/§7 gap)
  ↓
Decision Workspace                (Draft → Assumptions/CaseConditions → Decision — already real, Sprints 9–13)
  ↓
Portfolio  (changed)  ─────────────────────────────────────────────────────────┘
```

Every stage above the two named gaps is already real and unmodified by this document. The two gaps are integration work — new unions and new read-only comparisons over existing data — never a new write path, new table, or new event type.

---

## 9. Internal Alpha Definition

The minimum product the team would genuinely use every day instead of a spreadsheet and a notes app. Ruthless, per the sprint's own instruction.

**In:**
- **Portfolio**: Overview, Holdings, Allocation, Risk, Concentration, Cash — all real today, ship as-is.
- **Investment Case**: every section listed in §4, exactly as it exists today, with "Record Decision" rewired to open the Decision Workspace.
- **Daily Brief**: one list, five urgency groups, reusing Change Intelligence + CaseCondition + Assumption signals — the §5 integration, nothing else.
- **Discovery**: SEC-backed new-ticker search + a Portfolio Fit read on every candidate — the §6 integration.
- **Portfolio Fit**: the six-dimension qualitative framework in §7, surfaced inside Discovery and inside Portfolio.
- **Decision Workspace**: exactly what Sprints 9–13 already built — Draft, Assumptions, CaseConditions, commit-with-reasoning, Reasoning Timeline. No further feature added here.
- **Companion**: exactly as already built — the one chat surface, everywhere.
- **Watchlist**: exactly as it exists today.

**Deliberately cut, even though technically buildable this quarter:**
- Sector/geographic diversification (needs a real, non-fabricated data source that does not exist)
- Performance/returns tracking (no cost-basis data exists; not required by Atlas's own stated reasoning-over-performance philosophy)
- Any notification/alerting layer beyond Daily Brief itself
- Multi-draft comparison UI, draft-to-draft diffing
- A dedicated Portfolio Fit *page* (it is a lens, not a destination)
- Dashboard as a separate destination

## 10. Explicitly Out of Scope

Postponed, not rejected. None of the following blocks Internal Alpha, and none is touched by this document.

**Tier 2** (after Tier 1 works well): Smart notifications, Portfolio simulations, Scenario analysis, Rebalancing, AI monitoring improvements beyond the CaseCondition evaluation mechanics that already exist.

**Tier 3** (not required for Internal Alpha):
- **Decision Journal** — a dedicated authoring/browsing surface for Decision history
- **History / Timeline** — the existing History page and Decision Timeline data; the data is not deleted, it simply isn't primary navigation (§2)
- **Reflection** — ReflectionResponse's own dedicated surface
- **Personal Thesis** — a dedicated authoring/history page for thesis evolution. Note: this is distinct from `InvestmentCaseComposition.current_thesis`, which already exists as a real, derived field inside Investment Case (§4) and stays exactly where it is; what's deferred is a *separate* Personal Thesis page.
- **Decision Memory** — any dedicated surface for `DE-005`'s own thesis-strength synthesis
- **Complex collaboration** — multi-user Case access, shared annotation
- **Advanced social features** — anything beyond the single-investor product this already is

## Related

`docs/Atlas-Architecture-Conformance-Register.md` (the backend implementation baseline this document builds a product surface on top of, unmodified). `docs/ReasoningWorkspace-Implementation-Report.md`, `docs/DecisionWorkspace-UI-Implementation-Report.md` (Sprints 12–13, the Decision Workspace this document's own §1/§4/§9 route "Action" through). `docs/ADR-CC-001-CaseCondition.md`, `docs/ADR-AS-001-Assumption.md` (the Invalidation-role and challenge/support vocabulary §5's prioritization reuses directly, unmodified).

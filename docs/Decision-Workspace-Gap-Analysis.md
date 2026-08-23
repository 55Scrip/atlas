# Decision Workspace — Gap Analysis (Architecture Only)

**Status:** Architectural decision aid. Not a design specification, not an implementation plan, not a proposal for new domain models.

**Scope:** This document analyzes the gap between `docs/atlas_ux/UX-009-Decision-Workspace-Screen-Specification.md` (the 13-section, ADR-002-governed screen specification), the current implementation (the 4-field Add/Trim/Remove/Leave-as-is → Reason/Confidence → Record flow in `frontend/src/routes/InvestmentCasePage.tsx`'s Tier 2 panel), and the current domain model (`atlas/core/domain/*`, read directly from source for this analysis, plus `docs/atlas_decision_engine/DE-005-Decision-Memory.md` and `DE-006-Execution-Guidance.md` §4/§8 for doctrinal boundaries already on record).

**Method:** Every classification below is grounded in a specific file, field, or doctrine passage read for this analysis — not inference from the UX document alone. Where a doctrine document's claim did not match what the code actually does, that mismatch is stated explicitly rather than silently resolved in either direction.

---

## 1. What currently exists (baseline, for reference)

**Domain layer** (`atlas/core/domain/`), confirmed by direct read of each `entity.py`:

| Aggregate | Fields | Lifecycle |
|---|---|---|
| `Case` | `id`, `recorded_at` | Create-only. Pure ownership boundary — "no further lifecycle, status, title, description, or content is canonically forced" (own docstring). Alpha's Investment Case *is* one `Case` per ticker (`atlas/alpha/case_generation/__init__.py`: "Creates a Case, nothing else"). |
| `Decision` | `id`, `case_id`, `user_id`, `decision_type` (`BUY\|SELL\|HOLD\|WATCH\|PASS`), `subject`, `investment_case.reason` (free text), `confidence` (0–100 int), `decided_at`, `recorded_at`, `source`, `observation_id?` | **Immutable, capture-only.** "There is no update. A changed opinion is a new Decision" (own docstring). No versioning, amendment, or draft mechanism exists on this or any other aggregate below. |
| `Outcome` | `id`, `case_id`, `decision_id`, `statement`, `occurred_at`, `recorded_at`, `note?` | Capture-only. References `Decision` by id, read-only. |
| `DecisionContext` | `context_id`, `decision_id`, `situation`, `captured_at`, `recorded_at`, `portfolio_relevance?`, `capital_considerations?`, `alternatives_considered` (tuple of investor-authored strings), `uncertainties` (tuple of investor-authored strings) | Capture-only, insert-only, at most one per Decision. **Fully persisted** (`atlas/core/infrastructure/persistence/decision_context/`) and has a real application-layer use case (`atlas/core/application/decision_context/capture_decision_context.py`) — but is never called from anywhere in `atlas/alpha`. Confirmed by exhaustive grep across `atlas/alpha` and `atlas/core/api`: zero references. |
| `KnowledgeReference`, `ReasoningTrace`, `Judgment` | Each `case_id`-scoped, each fully persisted and has a real application layer | Same status as `DecisionContext`: real, tested, wired to nothing in Alpha. These are the general-purpose "Core Loop" epistemic primitives (`OE-002`); Alpha's Investment Case flow does not call any of them. |
| `reasoning_link` (four bridge types incl. `ConclusionDecisionLink`) | Explicitly marked **"PROVISIONAL STATUS"** in its own module docstring — "a temporary orchestration mechanism, not a permanent addition to the ubiquitous language" | Exists, persisted, unused by Alpha. |

**No domain object anywhere in the codebase represents:** a monitoring condition, an invalidation condition, a review trigger/schedule, a draft (pre-commit) Decision state, a challenge-acknowledgment record, an implementation type/status separate from `decision_type`, or a cross-Case "alternative investment" ranking. Confirmed by grep across `atlas/core/domain`, `atlas/decision_engine`, `atlas/analysis_engine` for each concept — no hits outside prose comments.

**Frontend layer**, current (post-revert) state of `InvestmentCasePage.tsx`'s Tier 2 panel: four buttons (Add / Trim / Remove / Leave as is) map to `decision_type` via `ACTION_DECISION_TYPE` → a form with `reason` (free text) and `confidence` (0–100) → submit calls the existing Decision-capture endpoint → on success, an Outcome/trade-reporting sub-flow becomes available. This is the entirety of the current implementation against UX-009's 13 sections.

**Analysis layer already fetched by this page** (`investmentCaseAnalysis.report`, from the existing `GET /api/cases/:id/analysis` endpoint): `atlasThesis` (posture + narrative), `conviction.level`, `recommendation.level`, `currentAnalysisAt`, `strengths[].kind`, `risks[].kind`, `risk.findings[]` (category, status, contradicting facts), `valuation.findings[].assumptions`, `keyOpenQuestions[]`, `holdingContext.weightPercent`. This is real, already-computed, already-transported data — not a gap.

**Doctrinal boundary already on record**, `DE-006-Execution-Guidance.md` §4/§8: Portfolio Simulation ("What would my portfolio look like if I did this?") is named explicitly as **"Not defined anywhere in this repository... not specified, not scoped, not designed here."** This is a standing architectural decision, not an oversight this analysis can resolve.

**A documentation/code mismatch worth flagging directly:** `DE-006` §4's table claims "UX-012B's Implementation Summary component (Implementation type: Reduce/Add/Initiate Position, No Action, Monitor; target allocation or quantity; states Pending, Partially Executed, Complete, Not Required)" **already exists**. Direct inspection of the current frontend found no such field — `tradeApplyStatus` is transient request-loading state (`idle | loading | success | error`), not a persisted implementation-type/status value. The same table also claims "Actual Execution... not defined anywhere in this repository," yet `TradeLogEntry` (`atlas/alpha/portfolio/trade_log_table.py`) already persists `executionPrice`, `quantity`, `fees`, `executedAt` — which is, on its face, exactly what "Actual Execution" describes. Both claims are stated here as observed, not resolved; DE-006 is documentation-only and appears to be stale relative to the actually-shipped code in at least these two places.

---

## 2. Section-by-section classification

For each UX-009 section: does it **already exist**, can it be built by **presenting existing data only**, does it need only **transient UI state**, does it need **new persistence**, does it need **new domain objects**, does it need a **new API endpoint**, and is it **blocked by the current ontology**? A section frequently splits across several of these — UX-009 sections are not atomic capabilities, and the table reflects that.

### Section 1 — Current Conclusion

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ✅ | ✅ | — | ❌ | ❌ | ❌ | ❌ |

**Why:** The conclusion narrative, confidence level, and as-of date are exactly `atlasThesis.narrative`, `conviction.level`, and `currentAnalysisAt` on the object this page already fetches from the existing analysis endpoint. The "View full analysis" link needs no new surface — the Decision Workspace and the originating analysis are the same page. Nothing here is a gap.

### Section 2 — Why a Decision Is Required

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ (1 of 8) | ⚠️ (1 of 8) | ✅ (1 of 8) | ✅ (7 of 8) | ✅ (7 of 8) | — | ✅ (7 of 8) |

**Why:** Of UX-009's eight named trigger values, only **User-initiated** is truthfully reachable today — every current entry point into the decision-recording panel is the investor's own click. That single value is static text; presenting it needs no data model at all. The other seven (Thesis change, Valuation change, Portfolio conflict, Opportunity cost, Scheduled review, Invalidation signal, New evidence) each presuppose a *trigger-detection and delivery mechanism* that does not exist: no invalidation-condition concept exists on any aggregate (confirmed in §1 above; also see Section 9 below), no scheduled-review re-entry exists, and Daily Brief does not currently push a "this decision is due" prompt into Investment Case (its own `investment_case_change` package computes deltas for *display*, but nothing consumes those deltas as a Decision Workspace entry trigger). This is a real, multi-part gap, not one gap.

### Section 3 — Proposed Decision

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ (decision-type half) | ⚠️ | — | ⚠️ | ⚠️ (open question) | — | — |

**Why:** The decision-type selector already exists in substance — the four action buttons (Add/Trim/Remove/Leave-as-is) already resolve to `decision_type` via `ACTION_DECISION_TYPE`, and the user already commits to a type before submitting. What does **not** exist is (a) Atlas stating its own proposed decision as a distinct, displayed starting point — `recommendation.level` carries a support *statement* (e.g. "Thesis intact"), not a literal proposed action sentence pre-populating a field — and (b) a "user's decision, in their own words" field UX-009 treats as *distinct from* the primary reason field of Section 4. Whether (b) is a real second field or whether `decision_type` + `reason` together already satisfy UX-009's intent is not decided by anything in the current code or doctrine — **this is an open architectural question, not a solved one or a confirmed gap**, and is listed again in §4 below.

### Section 4 — Decision Rationale

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ✅ (reason field) | ✅ (Atlas summary/risks) | — | ✅ (user-confirmed assumptions) | ⚠️ | — | — |

**Why:** The primary reason field already exists exactly as specified — `Decision.investment_case.reason`, free-text, already required by the current form. Atlas's supporting summary (recommendation statement) and material risks are both already-fetched fields (`recommendation.level`, `risk.findings`) — presentable with no backend change. What's missing is the "user-confirmable" half of Essential Assumptions: UX-009 wants the investor able to add/edit/remove Atlas-proposed assumptions and have that edited list preserved as part of the record. No field anywhere stores a user-edited assumption list against a Decision. Whether this becomes a new field on a `Decision`-adjacent object (following the `DecisionContext` precedent — captured after Decision, referencing `decision_id`, itself immutable) is exactly the kind of decision flagged in §4 of the executive summary below.

### Section 5 — Supporting Factors

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ | ✅ (supporting evidence) | — | — | ⚠️ (portfolio alignment) | ✅ (both sub-items) | — |

**Why:** Supporting evidence items are already-fetched (`strengths[].kind`) — presentable now. Two sub-items are not: **Portfolio alignment** ("consistent with the portfolio's established strategy and concentration limits") presupposes a stated, storable "portfolio strategy" — no such object exists; Portfolio Intelligence describes concentration *descriptively* ("Elevated") but against no investor-defined threshold. **Historical consistency** ("consistent with prior decisions on this investment") has its raw material already available — every prior `Decision` for a `case_id` is already fetchable — but the *comparison logic itself* does not exist. `DE-005` §5 states this almost verbatim: it explicitly leaves open, for "a future implementation phase," the algorithm for judging whether a thesis has "strengthened" or "weakened" from prior decision history. This is a documented, self-acknowledged gap, not merely an unbuilt feature.

### Section 6 — Challenges

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ | ✅ (most sub-items) | — | ✅ (acknowledgment) | ✅ (acknowledgment) | — | ✅ (acknowledgment) |

**Why:** Unresolved questions, conflicting evidence, and missing information are already-fetched (`keyOpenQuestions`, `risk.findings[].contradictingFacts`) — presentable now. **Behavioral context** ("12% price decline in 30 days," "held for four years") has no detection mechanism anywhere — this is `UX-008` §15's investor-behavioral-pattern memory, which `DE-005` §2 explicitly names as a *different, also-unbuilt* specification, not something this analysis can borrow from. **Acknowledgment** ("the item then appears with reduced emphasis... may be acknowledged but not deleted, the record must preserve that they were seen") is the clearest ontology conflict in this section: `Decision` has zero fields capable of holding a mutable, growing acknowledgment list, and adding one would contradict `Decision`'s own stated invariant — "There is no update." A per-challenge acknowledgment record is structurally a *new*, separate, append-only object referencing `decision_id` (the same shape `DecisionContext` already uses) — not an extension of `Decision` itself. Note: `DecisionContext.uncertainties` already persists investor-authored uncertainty text, but as free-form prose captured once, not as a per-item acknowledgment-of-an-Atlas-surfaced-challenge mechanism with individual timestamps — a related but not equivalent capability.

### Section 7 — Opportunity Cost

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ | ⚠️ | ✅ (no-reallocation fallback) | — | ⚠️ | ✅ (user's own note) | ⚠️ |

**Why:** The decision subject's own expected return/conviction summary is already-fetched — presentable now. The "no capital is being reallocated" fallback for Maintain/No Action decisions is static text — trivial. Ranking **alternatives** is where this section forks in two directions with different feasibility: alternatives drawn from *already-held positions* could in principle be built from already-batched data — `PortfolioCockpitService` already runs `build_many()` analysis across every holding for the Portfolio Cockpit view, so a ranking over that existing batch is not blocked by ontology, though it is genuinely new backend logic (a ranking/comparison service), not a presentation-only task. Alternatives *beyond* current holdings (UX-009's own example, "Danaher," is not necessarily held) would need on-demand analysis of an arbitrary ticker — technically possible via the existing case-generation + composition pipeline, but not wired to any "suggest an alternative" flow today. The investor's own "why I preferred this over the alternatives" note maps directly onto `DecisionContext.alternatives_considered`, which is already persisted and only needs an API endpoint to reach Alpha — the cleanest, lowest-cost item in this entire section.

### Section 8 — Portfolio Consequences

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ (current state only) | ⚠️ | — | — | ✅ (before/after math) | ✅ (qualitative note) | ✅ (before/after math) |

**Why:** This section's defining content — position size, theme exposure, sector balance, hidden concentration, and liquidity, each stated as a **before/after pair** — requires computing a hypothetical post-decision portfolio state. That computation is Portfolio Simulation, and `DE-006` §8 states plainly that Portfolio Simulation is "not defined anywhere in this repository... not specified, not scoped, not designed here." This is the single clearest, most explicit doctrinal exclusion found anywhere in this analysis — not an implementation gap so much as a standing architectural non-decision. Only the **current** (pre-decision) state — today's weight percent, today's concentration descriptor — is already computed and presentable; there is no "after" without Portfolio Simulation. Separately, the investor's own qualitative account (`DecisionContext.portfolio_relevance`, `.capital_considerations`) is already persisted and only needs an endpoint — but it answers a different question ("what did the investor think mattered") than what UX-009 Section 8 actually specifies ("what will Atlas compute changed").

### Section 9 — Assumptions, Monitoring and Invalidation

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ (assumptions, read-only) | ✅ | — | ✅ | ✅ | — | ✅ |

**Why:** Supporting Assumptions, read-only, are already-fetched (`valuation.findings[].assumptions`) — presentable now. Monitoring Conditions and Invalidation Conditions have no home anywhere in the ontology: confirmed by exhaustive grep across `atlas/core/domain`, `atlas/decision_engine`, and `atlas/analysis_engine` — no hits for either concept outside this UX document and prose comments. It is worth naming explicitly why the existing `Observation` aggregate (Core Loop: Question → Observation) is **not** a fit despite the name overlap: that `Observation` is retrospective — evidence gathered in answer to a Question, feeding forward into Interpretation/Hypothesis/Evidence — whereas UX-009's "Monitoring Condition" is prospective, a signal registered *after* a Decision to watch *going forward*. Reusing the existing `Observation` type for this would be a semantic misuse, not a genuine architectural fit. `DE-005` §5 independently confirms this is unresolved, listing the "review trigger" question among what it explicitly defers to "a future implementation phase."

### Section 10 — Implementation Plan

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ (post-hoc trade only) | ⚠️ | — | ✅ (type + status) | ⚠️ | — | ⚠️ |

**Why:** No implementation-type selector (Immediate/Gradual/Conditional/Deferred/No action) or trackable lifecycle status (Pending/In Progress/Completed/Conditional/Cancelled) exists anywhere as a persisted field — despite `DE-006`'s own table claiming otherwise (see the mismatch noted in §1). What *does* exist is the already-shipped Outcome/Trade-Log flow: once an investor reports a completed transaction, `TradeLogEntry` persists `quantity`, `executionPrice`, `fees`, `executedAt` — but this is deliberately, per `DE-006` §4's "Five Concepts" table, a different concept (Actual Execution, after the fact) from Implementation Plan (Intent, stated *before* any transaction, as a forward-looking type + target range + timeline). The existing flow can be presented as-is for a Decision that has *already* been implemented; it cannot substitute for the forward-looking planning content UX-009 Section 10 specifies before a decision is even recorded.

### Section 11 — Review Plan

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ❌ | ❌ | — | ✅ | ✅ | — | ✅ |

**Why:** Confirmed absent everywhere a review-trigger/schedule concept could live. This section is also **structurally downstream of Section 9**: UX-009 itself defines one of Review Plan's four trigger types as "Invalidation-triggered: automatically surfaced when an invalidation condition from Section 9 is reached" — meaning Section 11 cannot be meaningfully designed independently of Section 9's own unresolved Invalidation Conditions concept. This is one gap with two visible symptoms, not two separate gaps.

### Section 12 — Final Decision Card

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ⚠️ (inherits) | ⚠️ (inherits) | — | ⚠️ (inherits) | ⚠️ (inherits) | — | ⚠️ (inherits) |

**Why:** This section has no independent content of its own — it is defined by UX-009 as an assembled read-back of Sections 3, 4, 8, 10, and 11. Its Decision/Reason/Confidence sub-fields (from Sections 3–4) are real, already-captured fields once a Decision is recorded (`decision_type`, `investment_case.reason`, `confidence`) — fully presentable. Its Portfolio-impact/Implementation/Review-condition sub-fields are exactly as blocked as Sections 8, 10, and 11 respectively. This section's feasibility is entirely derivative; it resolves automatically once its sources do.

### Section 13 — Record Decision

| Already exists | Present existing data | Transient UI | New persistence | New domain objects | New API endpoint | Blocked by ontology |
|---|---|---|---|---|---|---|
| ✅ (universal minimum) | — | ⚠️ (unavailable-state UI) | ✅ (draft) | ✅ (draft) | — | ✅ (draft) |

**Why:** The universal-minimum recording gate (decision stated + primary reason authored) already exists in substance — the current form already requires both before its submit path succeeds. The conditionally-required gates (implementation type selected, review condition set, Portfolio Consequences acknowledged) cannot be implemented independently of Sections 10, 11, and 8 respectively — they inherit those sections' gaps rather than adding new ones. **Save as Draft** is a clean, independent gap: no draft/pending state exists on `Decision` or anywhere else, and `Decision`'s own immutability invariant ("There is no update") structurally excludes retrofitting a draft-to-committed transition onto the existing aggregate — a draft is, by definition, a record that gets updated (or discarded) later, which is precisely what `Decision` is designed never to permit. A draft, if built, is necessarily a new, separate object with its own (mutable, pre-commit) lifecycle, not a state of `Decision` itself. The post-decision "next steps" are mixed: return-to-origin already works (the existing origin-preserving ribbon system); "View decision in Atlas Memory" has no single named surface to point to — the existing Decision History tab is the closest analog, and whether that already *is* "Atlas Memory" in UX-009's sense, or whether UX-009 means something more specific, is unresolved; "Open [related] Workspace" depends on Section 7's alternatives existing first.

---

## 3. Executive Summary

### Can be implemented immediately

*No backend or ontology changes; the data is already computed, already fetched by this page, or is trivially static.*

- Section 1 (Current Conclusion) — conclusion narrative, confidence level, source date, link to full analysis.
- Section 2 — the single "User-initiated" trigger value (static text; the other seven trigger types are not in this bucket).
- Section 3 — the decision-type selection mechanism (already functionally present via the four action buttons).
- Section 4 — the primary reason field (already required by the current form); Atlas's supporting summary and material risks (already-fetched).
- Section 5 — supporting evidence items (already-fetched `strengths[].kind`).
- Section 6 — unresolved questions, conflicting evidence, missing information (already-fetched); the empty-state fallback text.
- Section 7 — the decision subject's own expected-return/conviction summary; the "no capital reallocated" fallback line for Maintain/No Action.
- Section 8 — the *current* (pre-decision) weight percent and concentration descriptor only — never a before/after pair.
- Section 9 — Supporting Assumptions, read-only (already-fetched `valuation.findings[].assumptions`).
- Section 12 — the Decision/Reason/Confidence sub-fields, once a Decision exists.
- Section 13 — the universal-minimum recording gate and its existing submit path; the return-to-origin next step.

### Requires frontend work only

*No domain or persistence changes — the data or mechanism already exists somewhere in the backend, but needs new frontend logic beyond simple pass-through, or needs an existing-but-unwired backend capability exposed.*

- Section 3 — mapping `recommendation.level` to a stated "Atlas proposes: …" sentence is frontend-derivable from already-exposed data, but is a real mapping/authoring task, not pass-through.
- Section 7 — ranking alternatives among *already-held* positions using the Portfolio Cockpit's own already-batched `build_many()` analysis output is new frontend (and light backend aggregation) logic over data that is already computed — see the "requires backend work" note below on where the line sits, since surfacing that batch to the Decision Workspace as a ranked comparison is arguably new backend composition, not pure frontend.
- Section 13 — pointing "View decision in Atlas Memory" at the existing Decision History tab is a frontend-only reinterpretation, contingent on confirming that tab is the intended target (see §4 below).

### Requires backend work

*Requires new backend services, new API endpoints, or new computed data — but does not require a new domain object; existing domain objects and persistence are sufficient once wired or extended with new computation.*

- Section 5 — Portfolio Alignment (needs a "portfolio strategy/concentration limit" computed comparison) and Historical Consistency (needs a decision-history comparison algorithm — `DE-005` §5 explicitly defers this).
- Section 6 — Behavioral context detection (price-move and holding-duration signals) has no existing computation.
- Section 7 — Wiring `DecisionContext.alternatives_considered`/`.uncertainties` to Alpha needs a new API endpoint over an already-persisted, already-application-layer-supported object — no new domain object required. A genuine cross-position alternatives-ranking service (beyond the note above) is new backend logic.
- Section 8 — Wiring `DecisionContext.portfolio_relevance`/`.capital_considerations` to Alpha, same as above: new endpoint only, no new domain object.
- Section 10 — Presenting the already-existing `TradeLogEntry` data for already-implemented decisions is a "requires frontend + possibly a thin new endpoint" item, not zero-backend.

### Requires new Domain Objects

*Cannot exist without extending the domain model — confirmed by exhaustive search finding no existing field, aggregate, or persisted concept that fits.*

- Section 6 — Challenge acknowledgment (a per-item, timestamped, append-only record referencing `decision_id`; cannot be added to `Decision` itself without violating its immutability invariant).
- Section 9 — Monitoring Conditions and Invalidation Conditions (no existing aggregate fits; the existing `Observation` aggregate is a different, retrospective concept and would be a semantic misuse if reused here).
- Section 11 — Review Plan / scheduling (structurally depends on Section 9's Invalidation Conditions existing first).
- Section 13 — Save as Draft (a pre-commit, mutable lifecycle state that `Decision`'s "there is no update" invariant structurally excludes from `Decision` itself).
- Section 4 (partially) — a user-confirmed/edited assumptions list, if it is to be preserved as part of the permanent record rather than discarded after submission.

### Requires architectural decisions before implementation

*Unresolved dependencies that must be decided — not merely built — before implementation can begin.*

- **Is Portfolio Simulation in scope at all?** Section 8's defining content (before/after portfolio consequences) and part of Section 7 (cross-position "capital competition" framing) both terminate at this single, already-documented boundary (`DE-006` §8: "not defined anywhere in this repository"). This is the largest single decision blocking implementation, and it is upstream of two sections, not one.
- **Does UX-009 Section 3's "user's decision field" require a new, distinct field**, or is it already satisfied by the existing `decision_type` + `reason` pair? Nothing in the current code or doctrine resolves this either way.
- **Should Monitoring, Invalidation, and Review Plan (Sections 9 and 11) be designed as one unified capability** rather than as separate gaps, given Review Plan is explicitly defined in terms of Invalidation Conditions? Designing them independently risks a second retrofit later.
- **Is a per-challenge acknowledgment record (Section 6) a new small aggregate of its own** (mirroring the `DecisionContext` precedent: captured after Decision, referencing `decision_id`, itself immutable), **or does it belong as an extension of `DecisionContext`** (which already has an adjacent, if not identical, `uncertainties` field)? Both are structurally possible; nothing in the current architecture favors one over the other.
- **Does "View decision in Atlas Memory" (Section 13) already mean the existing Decision History tab**, or does UX-009 intend a not-yet-built, more general "Atlas Memory" surface? UX-009 does not define what "Atlas Memory" is as a concrete surface; this document cannot resolve that without redesigning UX-009, which is out of scope here.
- **Is `TradeLogEntry` already "Actual Execution"** in `DE-006` §4's own terms, contradicting that document's claim that Actual Execution is undefined? This is a documentation-accuracy question that should be resolved (in `DE-006` itself, not here) before anyone relies on that table's "not defined anywhere" claim for planning purposes.
- **Should Section 10's forward-looking Implementation Plan be a new field on a `Decision`-adjacent object, or an extension of the existing Outcome/Trade-Log flow's timing** (i.e., letting an investor pre-declare intent that the existing trade-reporting flow later fulfills)? Both directions are architecturally plausible; this document takes no position.

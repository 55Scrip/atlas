# Decision Workspace — Architecture Resolution Sprint 1

**Status:** Architecture decisions only. No product code, UI, API, schema, or Domain Object changes accompany this document. Its purpose is to govern a later ADR and implementation-design phase, not to replace either.

**Method:** Every decision below is traced to a specific file, field, or governing document, read fresh for this sprint. Where evidence is insufficient, the decision is stated as `UNRESOLVED — REQUIRES ADR INVESTIGATION` rather than guessed.

---

## 0. Executive Conclusion

Atlas's domain model is substantially richer than UX-009's own text suggests when read in isolation, and substantially poorer than UX-008's philosophy assumes when read in isolation. Three findings drive every decision in this document:

1. **A large share of UX-009's apparent gaps are not gaps in Atlas — they are gaps in Alpha's wiring.** `DecisionContext`, `KnowledgeReference`, `ReasoningTrace`, `ReasoningLink`, `Judgment`, and the entire `ReflectionResponse`/`DecisionReflection`/Pattern-recognition "Understanding" lineage are real, persisted, tested Core capabilities that `atlas/alpha` calls nowhere. `docs/Atlas-Alpha-Baseline-v1.0.md` §4 confirms this is a **deliberate scope decision**, not an oversight: "Monitoring," "Reflection," and "Coach intelligence" are explicitly named as **Deferred**, not Included, in Alpha.

2. **A smaller, but structurally load-bearing, share of UX-009's content has no home anywhere in Atlas at all** — monitoring conditions, invalidation conditions, review scheduling, per-challenge acknowledgment, and forward-looking implementation intent (as distinct from `Decision`, `Outcome`, and Alpha's trade log). These are genuine, not merely unwired, gaps — several of them converge on the same underlying tension: **UX-008's own philosophy describes Decision as having an eleven-state mutable lifecycle (§12), while the actually-implemented `Decision` aggregate is frozen and capture-only ("There is no update. A changed opinion is a new Decision.").** This tension predates UX-009; it originates in UX-008 itself.

3. **UX-009's own governing correction record, `ADR-002-Critical-UX-Architecture-Resolutions.md` (C-03), summarizes Section 3's ownership as "User-owned (blank until authored)" — which does not match UX-009's own body text**, which describes Atlas proposing a decision that pre-populates an editable field. This is flagged, not resolved, below (§12).

None of this means UX-009 must be rewritten. It means implementation cannot resume against UX-009's text alone — several of its sections describe a product surface for a domain model Atlas does not yet have, and building that surface first would either silently fabricate data or quietly redefine the ontology through UI code, exactly what this sprint exists to prevent.

---

## 1. Baseline (Phase 1)

Confirmed directly, this sprint, before any analysis:

- `git status --short`: only pre-existing untracked files (`​.env`, `atlas/business_data_providers/alpha_vantage.py.save`, `docs/atlas_beta_sprint1_figma_implementation_review.md`) plus this document and the prior `Decision-Workspace-Gap-Analysis.md` — neither tracked yet.
- `git log --oneline -3`: `f32897f Revert "Add Decision Workspace v1..."` is `HEAD`, directly on top of `9a95448` (the reverted commit), on top of `60b42fc`. The revert is in `HEAD`.
- `docs/Decision-Workspace-Gap-Analysis.md` exists on disk (30.5 KB), produced in the prior sprint.
- No leftover Decision Workspace code: `find frontend/src -iname "*DecisionWorkspace*"` returns nothing; `grep -n "DecisionWorkspace" frontend/src/routes/InvestmentCasePage.tsx` returns nothing.
- Nothing pushed.

---

## 2. Decision Workspace Responsibility Boundary (Phase 2)

**Responsibility statement**, synthesized from `UX-008` §§1, 3, 4, 13 and its own "What the Decision Workspace Is / Is Not" list:

> The Decision Workspace is the surface where an investor converts an already-formed Atlas conclusion into an explicit, dated, reasoned commitment, and preserves that reasoning in a form that remains understandable without the surrounding context, years later. It owns the *moment of commitment* and the *record of why* — nothing upstream of the conclusion, and nothing downstream of the commitment.

**What it explicitly does not own**, each grounded in UX-008's own text or existing architecture:

- **Analysis** — belongs to the Investment Workspace / Investment Case (`UX-008` §1: "should not repeat the complete analysis from previous Workspaces"). The Decision Workspace *reads* Atlas's conclusion; it does not compute one.
- **Portfolio-wide review** — belongs to the Portfolio Workspace (`UX-008` §1's own sequence: Dashboard → Investment Workspace → Portfolio Workspace → Decision Workspace).
- **Execution** — belongs to a brokerage integration that does not exist and that UX-008 §13 and `DE-006` §4 both explicitly disclaim: "Atlas should track whether implementation occurred without becoming the execution venue."
- **Ongoing monitoring after recording** — belongs to `atlas/monitoring` (a real, separate package: `MonitoringEngine`, `MonitoringSignal`, `MonitoringAlert`), explicitly **Deferred** from Alpha per `Atlas-Alpha-Baseline-v1.0.md` §4. The Decision Workspace may *set* a monitoring condition; it does not *watch* it.
- **Pattern recognition across decisions** — belongs to the `ReflectionResponse`/`DecisionReflection`/Pattern-recognition lineage (ATLAS-007/009–013), explicitly **Deferred** from Alpha per the same Baseline section. UX-008 §15 itself names this as a *downstream consumer* of Decision Workspace records, not a Decision Workspace responsibility.
- **Daily Brief surfacing** — a downstream consumer (`UX-008` §1), not something the Decision Workspace itself renders.

**Why this matters:** four of UX-009's thirteen sections (Monitoring, Invalidation-as-review-trigger, Review Plan, and post-decision pattern surfacing) sit exactly on this boundary — the Decision Workspace's job is to *state* these things once, at commitment time; a separate, currently out-of-Alpha-scope system is responsible for *acting* on them afterward. Conflating "stating a condition" with "having a system that watches it" is the single most common way this kind of specification quietly expands into an implementation of monitoring/automation it never intended to own. This distinction governs §§7–8 below.

---

## 3. Decision vs. DecisionContext (Phase 3)

**Verdict: `PARTIAL_REUSE`.**

`Decision` (`atlas/core/domain/decision/entity.py`) is minimal and immutable by design: `id`, `case_id`, `user_id`, `decision_type`, `subject`, `investment_case.reason`, `confidence`, `decided_at`, `recorded_at`, `source`, `observation_id?`. `DecisionContext` (`atlas/core/domain/decision_context/entity.py`) is a separate, real, fully-persisted aggregate (`atlas/core/infrastructure/persistence/decision_context/`, application layer at `atlas/core/application/decision_context/capture_decision_context.py`), insert-only, at most one per Decision, with exactly the fields UX-009 wants for several sections: `situation`, `portfolio_relevance?`, `capital_considerations?`, `alternatives_considered` (tuple of strings), `uncertainties` (tuple of strings).

1. **Is `DecisionContext` already the intended companion object for richer decision-time context?** Yes, by its own docstring: "a point-in-time record of the circumstances surrounding an existing Decision... Decision remains stable and minimal, context may be captured later." This is exactly UX-009's own split between the "universal minimum" (Section 3–4) and the richer surrounding reasoning (Sections 5–9).
2. **Is its current scope sufficient for any UX-009 sections?** Yes, for the **investor-authored** half of three sections: Section 6's "uncertain assumptions" reads naturally against `uncertainties`; Section 7's "user may add a note explaining why the stated alternatives were rejected" reads naturally against `alternatives_considered`; Section 8's "user may add a note" half reads against `portfolio_relevance`/`capital_considerations`.
3. **Does exposing it to Alpha preserve its existing ontology?** Yes — no field would need to change meaning. `situation`, `alternatives_considered`, and `uncertainties` are already free-text, investor-authored, captured-once fields; exposing them through a new Alpha API endpoint does not distort what they already mean.
4. **Would using it require ontology change, or only API/application wiring?** Only wiring — `capture_decision_context.py` already exists as a callable use case; Alpha would need a new endpoint and a frontend call, not a new field or a new aggregate.
5. **Which UX-009 fields can map to it without semantic distortion?** Only the investor's-own-account halves named in (2) above. It does **not** fit: Atlas-*generated* content (Sections 5, 7's alternative comparisons, 8's before/after math — `DecisionContext` records what the investor thought, never what Atlas computed); per-item, timestamped acknowledgment (Section 6's Challenges — `DecisionContext.uncertainties` is a single free-text list captured once, not an itemized, individually-acknowledged record); or anything with a lifecycle after Decision is recorded (Sections 9's Monitoring/Invalidation, 11's Review Plan — `DecisionContext` is captured once, at or shortly after Decision, and never revisited; Monitoring/Invalidation/Review are explicitly forward-looking and post-recording).

**Consequence:** `DecisionContext` should be treated as the natural home for investor-authored *context*, never for Atlas-*computed* content or anything requiring a *post-recording lifecycle*. Reusing it beyond that boundary would be exactly the kind of silent ontology distortion this sprint exists to prevent.

---

## 4. Immutability Analysis (Phase 4)

`Decision`'s own docstring is unambiguous: **"There is no update. A changed opinion is a new Decision."** No aggregate read for this sprint — `Decision`, `Outcome`, `DecisionContext`, `Case`, `Observation`, `Question`, `Conclusion`, `KnowledgeReference`, `ReasoningTrace`, `Judgment`, `ReflectionResponse` — has an update or delete method on its repository interface. Every one is capture/insert-only.

| UX-009 requirement | Compatible with immutable `Decision`? | Why |
|---|---|---|
| Editable draft decisions | **No** — but not because of `Decision`'s immutability per se; a draft, by definition, does not yet satisfy `Decision`'s own required invariants (a fully-formed `decision_type`, `confidence`, `decided_at`, non-empty `reason`) until the moment it is submitted. A draft is naturally a *separate*, pre-`Decision` concept, not a mutable `Decision`. See §5. |
| Challenge acknowledgments | **Naturally a separate object.** Cannot be a mutable list *on* `Decision` without violating "no update." Fits the same shape `DecisionContext` and `ReflectionResponse` already use: a small, separate, immutable record referencing `decision_id`, captured after the fact. See §6. |
| Assumption confirmation | **Naturally a separate object**, for the same reason — "the user may confirm, edit, add, or remove" an assumption list implies a value that changes over time, which cannot live directly on `Decision`. |
| Monitoring-condition edits | **Naturally a separate, and explicitly out-of-Alpha-scope, system.** `atlas/monitoring`'s `MonitoringEngine`/`MonitoringSignal` already model *watching* as its own, separate concern — editing a monitoring condition after the fact is squarely that system's responsibility, not `Decision`'s. |
| Implementation-status updates | **Naturally a separate object** — UX-008 §13 and `DE-006` §4 both already insist Decision/Implementation-Intent and Actual Execution are distinct concepts; a status that changes from Pending → Partially Executed → Complete is, by definition, mutable state that cannot live on an immutable `Decision`. |
| Review-plan edits | **Naturally a separate object**, structurally identical to the Monitoring case. |

**Where UX-009 (and UX-008 §12, more explicitly) assumes mutable Decision state:** UX-008 §12's own eleven-state lifecycle (Draft, Under Review, Ready to Record, Recorded, Implementation Pending, Implemented, Partially Implemented, Superseded, Cancelled, Due for Review, Reviewed) reads, on its surface, as a single object moving through states over time — which the actually-implemented `Decision` cannot do. Read more carefully, UX-008 §14 itself resolves most of this tension without requiring mutation: **"Later edits must not silently overwrite the historical record. When the user's view changes, Atlas should record a new review, an amendment, or a superseding decision — not alter the original."** States like Superseded and Cancelled are consistent with immutability if they are *computed* (e.g., "superseded" = a later `Decision` exists for the same `case_id` and subject) rather than *stored* as a mutated field. States like Implementation Pending/Implemented/Partially Implemented remain a genuine, unresolved tension: they describe a single, continuously-updated status, and no existing pattern in this codebase (not even `DecisionContext`, which is insert-once) models a status that changes more than once after the anchor object is recorded.

---

## 5. Save as Draft (Phase 5)

- **Is an uncommitted draft a Decision?** No — a draft, by its nature, may be missing `decision_type`, `confidence`, or `reason`, all of which `Decision.__post_init__`/`register()` require. A draft cannot satisfy `Decision`'s own invariants.
- **Can a draft legally have a `DecisionId`?** Only if `DecisionId()` is generated before the object is otherwise valid — technically possible (`DecisionId` is just a UUID wrapper), but doing so would let an incomplete, mutable object carry the identity type of a supposedly-immutable aggregate, which is a modeling smell, not a clean fit.
- **Does turning a draft into a Decision violate immutability?** Not if the draft is a *different* object that, on submission, is used to *construct* a brand-new, fully-formed `Decision` via `Decision.register()` — exactly the existing pattern. It *would* violate immutability if the "draft" were itself a partially-populated `Decision` row later updated in place.
- **Is transient client state sufficient for Alpha?** Only if UX-009's own "Drafts are surfaced in the Daily Brief as unresolved decisions" requirement is dropped for Alpha. Daily Brief is a separate page/session; a purely client-side, in-memory or `sessionStorage`-scoped draft cannot be surfaced there.
- **Does UX-009 require cross-session persistence?** Yes, as written — the Daily Brief requirement is explicit in UX-009's own Section 13 text, not incidental.
- **Does Daily Brief depend on persisted drafts?** Only if this specific requirement is kept; Daily Brief today (`atlas/alpha/daily_brief/`) has no concept of a draft decision at all.

**Verdict: `REQUIRES_SEPARATE_PERSISTED_CONCEPT`** — conditional on keeping UX-009's own Daily-Brief-surfacing requirement. If that one requirement were dropped for Alpha, the honest verdict would instead be `TRANSIENT_UI_ONLY`. This is exactly the kind of product-scope decision this document surfaces rather than resolves — see the Architecture Decisions register (§18).

---

## 6. Challenges and Acknowledgment (Phase 6)

**Displaying challenges** and **recording acknowledgment** are genuinely separate questions with genuinely different answers.

**Displaying:** already substantially covered by existing data. `keyOpenQuestions`, `risk.findings[].contradictingFacts`, and valuation gaps are already fetched by the Investment Case analysis endpoint (confirmed directly in the prior Gap Analysis sprint's live verification against real MSFT data). This is presentation-only.

**Recording acknowledgment:** investigated against every plausible existing home:

- **`DecisionContext`** — adjacent (its `uncertainties` field is investor-authored text about what they were unsure of) but not equivalent: it is one free-text list captured once, not a per-item, individually-timestamped acknowledgment of specific Atlas-surfaced items.
- **`Judgment`** — a Case-scoped "settled characterization" object; its `characterization` is a single field, and it is not anchored to `decision_id` at all, only `case_id`. Not a fit for a per-Decision acknowledgment.
- **`ReflectionResponse`** — the closest structural precedent: "the investor's own preserved words," anchored to `decision_id`, capturing a `ProvenanceSnapshot` of what prompted it — but its own docstring scopes it to the "Understanding lineage" (Pattern/Strategy Signature/Decision Reflection/Coaching Question), which `Atlas-Alpha-Baseline-v1.0.md` §4 explicitly **Defers** from Alpha. Reusing its *shape* (small, separate, `decision_id`-anchored, immutable, captured-once) for acknowledgment would not be reusing the *object*, and would not pull Reflection itself into Alpha scope.
- **`KnowledgeReference` / `ReasoningTrace`** — both are Case-scoped, generic "this Case relies on that object" primitives with no acknowledgment semantics of any kind. Not a fit.

**Answer to the governing question** ("Is acknowledgment part of the investment decision itself, or a separate record about how the investor processed a challenge?"): the latter. UX-009 Section 13's own completion rule confirms this independently — acknowledgment is explicitly named as **soft friction that never blocks recording** (per `ADR-002` C-04), meaning it cannot be part of `Decision`'s own required-field invariant set; it is a parallel, optional record about the investor's engagement with the material, not a component of the commitment itself.

**Classification: `NEW ONTOLOGY REQUIRED`** — but small, and shaped identically to two already-accepted precedents (`DecisionContext`, `ReflectionResponse`): a minimal, separate, `decision_id`-referencing, immutable, captured-once-per-item aggregate. Not an extension of `Decision`. Not a repurposing of an existing object outside its own documented scope.

---

## 7. Assumptions, Monitoring and Invalidation (Phase 7)

Investigated independently, as instructed — they are not one gap.

### Assumptions

Already exist as **analysis findings**: `valuation.findings[].assumptions` is already fetched by the current Investment Case endpoint. Investor *confirmation* of an assumption, however, changes its ontology exactly the way acknowledgment does in §6 — confirmation is a fact about the investor's engagement with an Atlas-generated item, not a re-derivable computation, and nothing on `Decision` can hold a growing, editable confirmation list. **Reading: existing (Atlas-proposed half) + new ontology required (confirmation/edit-preservation half), same shape as §6.**

### Monitoring Conditions

No Domain Object represents "something Atlas should watch after a Decision." `atlas/monitoring`'s `MonitoringEngine`/`MonitoringSignal`/`MonitoringAlert`/`MonitoringChange` is real, separate infrastructure — but it is explicitly named **Deferred** in `Atlas-Alpha-Baseline-v1.0.md` §4, alongside Reflection and Coach intelligence. `Observation` was investigated specifically and rejected as a fit: its own docstring — "something the investor noticed... immutable, and introduces no relationship to Decision" — describes a **retrospective** record of a past noticing, temporally and semantically the opposite of a **prospective** watch condition registered for the future. Reusing `Observation` for Monitoring would misuse an existing, narrowly-scoped aggregate to mean something its own invariants were never designed to hold.

**Reading: `atlas/monitoring` may already be the intended eventual home, but it is out of Alpha's current scope by product decision, not by omission.** Setting a monitoring condition from the Decision Workspace (writing the intent) and watching it (`atlas/monitoring`'s own job) are two different capabilities; the first could plausibly live in Alpha before the second does, but nothing today lets the Decision Workspace hand a condition to `atlas/monitoring` even if it wanted to — no integration point exists.

### Invalidation Conditions

Confirmed absent everywhere by exhaustive grep across `atlas/core/domain`, `atlas/decision_engine`, `atlas/analysis_engine`. No field on `Decision`, no separate aggregate, no doctrine document defines what an invalidation condition *is* as a stored object (`DE-005` §5 explicitly defers the underlying algorithm question — "the exact algorithm for judging 'strengthened' versus 'weakened'" — to "a future implementation phase"). **This is a genuine, undocumented-as-solved gap, distinct from Monitoring's "exists but deferred" status.**

**Three independent conclusions:**

- Assumptions: existing (read-only) + new ontology required (confirmation).
- Monitoring: exists as separate infrastructure, explicitly deferred from Alpha — not a gap to close in this scope, a scope boundary to respect.
- Invalidation: genuinely does not exist anywhere; would require new ontology if built, and is presently un-designed even at the doctrine level.

---

## 8. Review Plan (Phase 8)

Time-based, condition-based, event-based, and invalidation-based review triggers, an expected review date, and review depth: none of these are Decision metadata (no field on `Decision` fits), none are computed anywhere, and — per UX-009's own text — the "Invalidation-triggered" review type is explicitly defined as "automatically surfaced when an invalidation condition from Section 9 is reached." **Review Plan cannot be meaningfully designed independently of Section 9's Invalidation Conditions, which §7 above already found does not exist.** Checked against Daily Brief (`atlas/alpha/daily_brief/`): no review-scheduling concept exists there either — Daily Brief today surfaces already-computed change intelligence, not scheduled future check-ins.

**Answer to the governing question:** neither purely Decision metadata nor purely workflow scheduling — it is a **scheduling/monitoring capability that a Decision-time interaction would set the initial conditions for**, structurally identical to Monitoring Conditions in §7: the Decision Workspace's job is to *state* the trigger; a separate system (which does not yet exist, and would sit adjacent to or inside `atlas/monitoring`) would be responsible for *watching* for it and *surfacing* it. This section is not an independent gap — it is downstream of, and secondary to, the Monitoring/Invalidation resolution in §7.

---

## 9. Implementation Plan vs. Outcome vs. Trade (Phase 9)

`DE-006` §4's "Five Concepts" table draws exactly the distinction this phase asks for: **Recommendation** (what should I do, Atlas), **Execution Guidance** (how might it be carried out, Atlas), **Decision/Implementation Intent** (what do I intend to do, the Investor — "Already exists," per that table, citing the live `BUY|SELL|HOLD|WATCH|PASS` field), **Actual Execution** (what factually happened, undefined in this repository, per the table), **Portfolio Simulation** (hypothetical, undefined). Two doctrine-vs-code mismatches were confirmed by direct inspection, both already noted in the prior Gap Analysis and re-verified here:

- `DE-006`'s claim that a richer "Implementation Summary" component (Immediate/Gradual/Conditional/Deferred/No-action type; Pending/Partially-Executed/Complete/Not-Required status) **already exists** does not match the current frontend — `tradeApplyStatus` is transient request-loading state (`idle | loading | success | error`) only.
- `DE-006`'s claim that "Actual Execution... is not defined anywhere in this repository" does not match `atlas/alpha/portfolio/trade_log_table.py`, which persists `outcome_id`, `decision_id`, `security`, `transaction_type`, `quantity`, `execution_price`, `fees`, `executed_at` — precisely what "Actual Execution" names. This table itself confirms its own boundary in its own docstring: "it never causes Outcome to be written to or modified... 'Outcome must never reference Alpha.'"

**Answers:**

1. **Does an Implementation Plan currently have an ontology?** No — `decision_type` (BUY/SELL/HOLD/WATCH/PASS) captures *what* was decided, not *how* or *when* it will be carried out.
2. **Can Outcome represent it without semantic distortion?** No — `Outcome` is explicitly "what actually happened after a Decision" (its own docstring), a backward-looking fact, not a forward-looking plan.
3. **Can Trade represent it without semantic distortion?** No, for the identical reason — the Alpha trade log records an *already-confirmed execution*, keyed by `outcome_id`; it has no concept of a plan that precedes and may never become a trade.
4. **Is implementation intent distinct from both?** Yes — UX-008 §13 states this directly: "A recorded decision and an executed transaction are not the same thing... [the investor] may decide to initiate a position gradually over three months," which the existing single-shot `decision_type` cannot express, and which neither `Outcome` nor the trade log can express before a transaction exists.
5. **Should UX-009's implementation status exist in Alpha before this is resolved?** No — building any part of Section 10 today would either bolt an incompatible forward-looking field onto `Decision` (violating §4's immutability finding) or silently conflate it with the already-shipped, backward-looking Outcome/Trade flow (repeating exactly the conflation `DE-006` §4 and `UX-008` §13 both warn against).

---

## 10. Opportunity Cost (Phase 10)

**Investor-authored alternatives:** `DecisionContext.alternatives_considered` already covers this semantic requirement exactly — a tuple of investor-authored strings, in the order considered, already persisted, already application-layer-supported, unwired to Alpha only for lack of an endpoint. No gap in the domain model here.

**Atlas-generated alternative ranking**, split as instructed:

- **Data availability:** partial. `PortfolioCockpitService` (`atlas/alpha/portfolio_cockpit/service.py`) already runs `build_many()` analysis across every currently-held position for the Cockpit view — conviction and expected-return data for every *existing holding* already exists in one already-computed batch. Data for tickers *not* currently held (UX-009's own example, "Danaher," is not necessarily a holding) does not exist in any batch and would require on-demand analysis of an arbitrary ticker — technically possible via the existing case-generation + composition pipeline, but not wired to any comparison flow.
- **Comparison computation:** does not exist for either case. No service ranks holdings against each other by conviction/expected return today; Portfolio Cockpit presents them side by side for human reading, not as a ranked recommendation.
- **Product semantics:** ranking existing holdings against each other is a *comparison of already-computed, independent analyses* — not a hypothetical "what would my portfolio look like" question, and therefore **not** Portfolio Simulation as `DE-006` §8 scopes that term. Ranking against a not-yet-held candidate is likewise a comparison of two independently-computed analyses, not a portfolio-level hypothetical.

**Conclusion:** Atlas-generated Opportunity Cost among *already-held* positions is **backend computation over existing ontology** (a new ranking/comparison service consuming already-computed Cockpit data — no new domain object, no Portfolio Simulation dependency). Extending it to *not-held* candidates is the same classification, with an added dependency on wiring on-demand single-ticker analysis into that same comparison. Neither is `dependent on Portfolio Simulation` or `blocked by unresolved architecture` — this is a genuine, positive finding that narrows what the earlier Gap Analysis treated as more uniformly uncertain.

---

## 11. Portfolio Consequences (Phase 11)

**Current-state portfolio facts** (current weight, current concentration descriptor, current sector-exposure characterization) are already computed by Portfolio Intelligence and already fetched (`holdingContext.weightPercent`, concentration descriptors already rendered elsewhere on the Investment Case page).

**Hypothetical post-decision state** (projected weight, projected concentration, projected sector/geographic exposure, projected risk-dependency change, liquidity impact after the action) requires computing what the portfolio would look like *after* a decision that has not yet been executed — a genuinely different computation from anything currently built, and precisely the capability `DE-006` §8 names and excludes: **"Portfolio Simulation... Not defined anywhere in this repository... not specified, not scoped, not designed here."**

**Verdict: `PORTFOLIO_SIMULATION_REQUIRED`** for the section's defining before/after content. **`CURRENT_STATE_ONLY_IN_ALPHA`** is what is actually achievable without it — and that current-state-only content, while real and presentable, is not what UX-009 Section 8 specifies (a before/after pair, explicitly). Presenting only the "before" half under this section's own heading risks silently implying the "after" half was computed when it was not — an honesty concern this document flags for whatever design phase follows, without prescribing its resolution.

---

## 12. Proposed Decision Vocabulary Analysis (Phase 12)

**A governance discrepancy, found and not silently resolved:** UX-009's own body text (Section 3) describes Atlas proposing a decision first — "Atlas's proposed decision, stated in one clear sentence... An editable field where the user states their own decision — initially populated with Atlas's proposal but fully modifiable." `ADR-002` (C-03)'s own summary table, by contrast, describes Section 3's ownership as **"User-owned (blank until authored)"** and its purpose as "The user's own stated intention, in their own words, as a working position" — with no mention of Atlas pre-populating anything. `ADR-002` claims UX-009, UX-009A, UX-010, and UX-011 are "four documents that already agree with each other exactly" on this point; the text actually found in UX-009 does not obviously agree with the ownership column in `ADR-002`'s own table. This document takes no position on which is correct — only that they conflict, and that this conflict was not visible from reading either document alone. See the Architecture Decisions register (§18).

**Vocabulary compatibility table**, comparing every decision-type vocabulary found in this codebase or its governing documents:

| Vocabulary | Source | Values |
|---|---|---|
| `DecisionType` (persisted enum) | `atlas/core/domain/decision/value_objects.py` | `BUY \| SELL \| HOLD \| WATCH \| PASS` |
| `PositionAction` (Alpha UI-only) | `frontend/src/routes/InvestmentCasePage.tsx` | `ADD \| TRIM \| REMOVE \| LEAVE_AS_IS`, mapped 1:1 onto `DecisionType` via `ACTION_DECISION_TYPE` (`ADD→BUY`, `TRIM→SELL`, `REMOVE→SELL`, `LEAVE_AS_IS→HOLD`) |
| `RecommendationStateView.recommendation.level` | Investment Case analysis endpoint | Support-level statements (e.g. `entry_supported`, `increase_supported`, `thesis_intact`) — describes Atlas's *support strength* for a direction, not a decision-type label itself |
| Investment-level decision vocabulary | `UX-008` §3 | `Initiate \| Add \| Maintain \| Reduce \| Exit \| Avoid \| Defer` |
| Portfolio-level decision vocabulary | `UX-008` §3 | `Reallocate capital \| Reduce concentration \| Increase theme exposure \| Reduce a macro dependency \| Preserve liquidity \| Rebalance conviction \| Accept a known concentration \| Maintain portfolio structure` |
| Review decision vocabulary | `UX-008` §3 | `Thesis remains valid \| Thesis requires revision \| Evidence is insufficient \| Decision postponed conditionally` |
| Decision-type label vocabulary (Section 3 body text) | `UX-009` | `Initiate / Add / Maintain / Reduce / Exit / Avoid / Defer` (investment-level, matching UX-008) plus separate portfolio-level and review-type lists, essentially restating UX-008 §3 |

**Existing collapse already performed, and already disclosed as such:** `ACTION_DECISION_TYPE`'s own comment in the current frontend states plainly that "Trim" and "Remove" both record `SELL`, and that "the difference between reducing and exiting a position is captured later, honestly, in the Outcome's own recorded quantity — not invented here as a Decision-level concept that doesn't exist." This is a real precedent for how this codebase has already chosen to handle vocabulary mismatch once: collapse at the `Decision` layer, preserve the distinction downstream, and say so explicitly rather than silently. UX-008/UX-009's own seven-to-eight-value investment-level vocabulary is considerably richer than the five-value `DecisionType` enum it would need to collapse onto (`Initiate` and `Add` both plausibly map to `BUY`; `Reduce` and `Exit` both plausibly map to `SELL`, mirroring the existing Trim/Remove collapse; `Avoid` has no existing `DecisionType` counterpart at all — the current enum has nothing for "reject an opportunity and record the reason" absent an existing position).

**Is "Proposed Decision" a presentation of Recommendation, a distinct object, a mapping layer, or unresolved?** Given the ownership conflict above is itself unresolved, this question cannot be answered independently of resolving it. If UX-009's body text governs (Atlas proposes, pre-populated): "Proposed Decision" would be a **mapping layer** from `recommendation.level` to one of the richer UX-008 vocabulary values, itself requiring the `Avoid` gap above to be separately resolved. If `ADR-002`'s table governs (user-owned, blank until authored): no mapping is needed at all — Section 3 would simply be a free-text field, and this vocabulary question would not arise for Section 3, only for the existing `decision_type` selector already captured via the four-button flow. **This is not decided here.**

---

## 13. Final Decision Card Boundary (Phase 13)

Traced field-by-field to its authoritative source:

| Final Decision Card field | Source | Classification |
|---|---|---|
| Decision | `Decision.decision_type` (+ whatever Section 3 resolves to, per §12) | Existing persisted data, pending §12 |
| Reason | `Decision.investment_case.reason` | Existing persisted data |
| Confidence | `Decision.confidence` | Existing persisted data |
| Portfolio impact | Section 8's before/after computation | Blocked upstream dependency (§11) |
| Implementation | Section 10's implementation type/status | Blocked upstream dependency (§9) |
| Review condition | Section 11's review trigger | Blocked upstream dependency (§8, itself downstream of §7) |

No field in this section originates independently of its own numbered source section. **This section must not become a second source of truth** — the finding here is simply that it cannot, structurally: it has no field of its own to distort, only read-throughs of Sections 3–11 whose own resolution this section inherits automatically.

---

## 14. Recording-Gate Boundary (Phase 14)

The existing Decision-creation contract (`Decision.register()`, requiring `decision_type`, `subject`, `investment_case.reason`, `confidence`, `decided_at`) already is, and per this document's own findings should remain, the canonical persistence gate — nothing in this sprint proposes changing it.

- **Universal minimum** (decision stated + primary reason authored, per `ADR-002` C-04): already effectively enforced by the current form, which requires a decision-type selection and a non-empty reason before submission succeeds. **Can remain frontend validation, backed by the existing, unchanged application-layer requirement.**
- **Conditionally-required gates** (implementation type per decision type, review condition, Portfolio Consequences acknowledgment): cannot be implemented as gates today, because the fields they would gate on (§§7–9, 11) do not yet exist. Adding a "you must select an implementation type" gate before an implementation-type field exists is not meaningful. **These gates are blocked upstream, not independently unbuildable.**
- **Soft friction** (unacknowledged Challenges, per `ADR-002` C-04): explicitly, by that ADR's own text, never hard-blocking — "Atlas never blocks recording because the user's own judgment differs from Atlas's own surfaced concern." This can exist as **application-level validation only in the sense of tracking whether acknowledgment occurred**, never as a submit-blocking condition, once §6's acknowledgment object exists.

**Clear boundary:** the existing gate is sufficient and correct for what Alpha can build today (Sections 1–7 partially, plus the existing decision-type/reason/confidence flow); no new persisted "completeness" semantics are needed until the sections that would populate the conditional gates themselves exist.

---

## 15. Atlas Memory Mapping (Phase 15)

UX-009's "preserved in Atlas Memory" and UX-008's "The Decision Workspace is part of Atlas Memory" are mapped, term for term, onto real objects already read for this sprint:

| "Atlas Memory" component (UX-008/UX-009 language) | Existing object | Alpha-wired? |
|---|---|---|
| The decision itself | `Decision` | Yes |
| What actually happened | `Outcome` | Yes |
| Circumstances at decision time | `DecisionContext` | **No** — real, persisted, unwired |
| The Case-scoped "relies on this" fact | `KnowledgeReference` | **No** — real, persisted, unwired |
| Epistemic support for a reasoning step | `ReasoningTrace` | **No** — real, persisted, unwired |
| Bridge between Conclusion and Decision | `reasoning_link.ConclusionDecisionLink` | **No** — real, persisted, unwired, and explicitly self-described as "PROVISIONAL STATUS... not a permanent addition to the ubiquitous language" |
| Case-relative settled characterization | `Judgment` | **No** — real, persisted, unwired |
| The investor's own preserved words about a decision, later | `ReflectionResponse` | **No** — real, persisted, explicitly Deferred from Alpha by product scope |
| Recognized behavioral patterns across decisions | `RecognizedPattern` / `RecognizedStrategySignature` / `DecisionReflection` (ATLAS-005–007) | **No** — real, computed on demand, explicitly Deferred from Alpha by product scope |
| Monitoring/watching after recording | `atlas/monitoring` (`MonitoringEngine` et al.) | **No** — real, separate package, explicitly Deferred from Alpha by product scope |
| Invalidation condition | *(nothing)* | Genuinely does not exist anywhere |
| Review scheduling | *(nothing)* | Genuinely does not exist anywhere |

**Answer to the governing question:** for the large majority of what "Atlas Memory" would need to mean, **yes — Atlas already possesses the required ontology, and Alpha simply fails to expose it**, in most cases by explicit, documented product-scope decision rather than by accident. Only Invalidation Conditions and Review Scheduling are genuine ontology absences, not merely unwired presences — and both, per §§7–8, are themselves downstream of the deliberately-deferred Monitoring capability.

---

## 16. Architecture Conflict Register (Phase 16)

| UX-009 (or UX-008) assumption | Current Atlas ontology | Conflict | Why it matters | ADR required? |
|---|---|---|---|---|
| Mutable, acknowledgeable Challenges | `Decision` is immutable, capture-only | Cannot add a mutable list to `Decision` | Blocks any literal reading of Section 6's acknowledgment mechanism | Yes |
| Draft decisions, editable pre-commit | `Decision` requires all invariants at construction | A "draft" cannot be a `Decision` instance | Blocks Section 13's Save-as-Draft without a new, separate concept | Yes |
| Review scheduling as part of the permanent decision record | No scheduling concept exists on any aggregate; nearest infrastructure (`atlas/monitoring`) is explicitly deferred from Alpha | Section 11 has no ontology to persist against, and the nearest candidate infrastructure is out of current scope by product decision | Blocks Section 11 and the Invalidation-triggered half of it | Yes |
| Monitoring conditions "registered as active Atlas observations" (UX-009's own Recording Behaviour text) | `Observation` is retrospective (something noticed), not prospective (something to watch); the actual watching infrastructure (`atlas/monitoring`) is separate and deferred | UX-009's own wording invites confusing `Observation` with monitoring; they are unrelated concepts that happen to share a common-language word | Risks a semantic misuse if implemented literally from UX-009's own phrasing | Yes |
| Implementation intent (Section 10) as forward-looking plan | `Outcome`/Alpha's trade log are backward-looking, post-execution facts; `DE-006` §4 explicitly separates Decision/Implementation-Intent from Actual Execution | No forward-looking implementation-plan object exists; conflating it with Outcome/Trade would violate an already-stated doctrinal boundary | Blocks Section 10 as specified, though the existing `decision_type` field is not nothing | Yes |
| Portfolio Consequences (Section 8) as computed before/after | Portfolio Simulation is explicitly named and explicitly excluded (`DE-006` §8: "not defined anywhere in this repository") | Direct, pre-existing, already-documented doctrinal exclusion | Blocks Section 8's defining content entirely | Yes (already effectively an open ADR-level question per `DE-006` itself) |
| `recommendation`/`decision_type`/UX-008 decision-type vocabularies are freely interchangeable | Three genuinely different vocabularies exist (`DecisionType`, `PositionAction`, UX-008's seven-to-eight-value lists), only partially and asymmetrically collapsible (the existing Trim/Remove→SELL precedent shows collapse is accepted in this codebase, but `Avoid` has no target at all) | Silent mapping would either lose real distinctions or fabricate a `DecisionType` value that doesn't exist | Blocks a faithful Section 3 decision-type selector as UX-008/UX-009 describe it | Yes |
| UX-009 body text (Atlas proposes, pre-populated) vs. `ADR-002` C-03's summary table (user-owned, blank until authored) for Section 3 | Two governing documents, both nominally authoritative, describe different ownership models for the same section | Neither this document nor any document read for this sprint resolves which governs | Blocks any implementation of Section 3 until resolved — implementing either reading risks contradicting the other's stated authority | Yes |

---

## 17. Alpha Scope Classification (Phase 17)

Per `Atlas-Alpha-Baseline-v1.0.md` §4, cross-referenced against every finding above:

| UX-009 capability | Classification | Basis |
|---|---|---|
| Section 1 — Current Conclusion | `ALPHA_EXISTING` | Already fetched, already computed |
| Section 2 — Why a Decision Is Required (User-initiated only) | `ALPHA_EXISTING` | Trivially true today; all other trigger types are `ALPHA_ARCHITECTURE_DECISION_REQUIRED` |
| Section 3 — Proposed Decision | `ALPHA_ARCHITECTURE_DECISION_REQUIRED` | Ownership-model conflict (§12) must resolve before any wiring or frontend work |
| Section 4 — Decision Rationale (Atlas-generated half) | `ALPHA_FRONTEND_GAP` | Data already fetched; needs only presentation |
| Section 4 — Decision Rationale (user-confirmed-assumptions half) | `ALPHA_ARCHITECTURE_DECISION_REQUIRED` | Same shape question as §6 (small new object vs. `DecisionContext` extension) |
| Section 5 — Supporting Factors (evidence) | `ALPHA_FRONTEND_GAP` | Already fetched |
| Section 5 — Supporting Factors (portfolio alignment, historical consistency) | `ALPHA_WIRING_GAP` / `DEFER_TO_BETA_OR_LATER` | Raw decision history is fetchable now (wiring gap); the comparison *algorithm* is explicitly undecided per `DE-005` §5 (defer) |
| Section 6 — Challenges (display) | `ALPHA_FRONTEND_GAP` | Already fetched |
| Section 6 — Challenges (behavioral context) | `DEFER_TO_BETA_OR_LATER` | Real infrastructure exists (Pattern/StrategySignature/DecisionReflection) but is explicitly Deferred from Alpha by `Atlas-Alpha-Baseline-v1.0.md` §4 |
| Section 6 — Challenges (acknowledgment) | `ALPHA_ARCHITECTURE_DECISION_REQUIRED` | New small object needed (§6); shape is clear, decision to build it is not made here |
| Section 7 — Opportunity Cost (investor's own alternatives) | `ALPHA_WIRING_GAP` | `DecisionContext.alternatives_considered` already exists |
| Section 7 — Opportunity Cost (Atlas-generated ranking, held positions) | `ALPHA_WIRING_GAP` | Existing Cockpit batch data, new comparison service only (§10) |
| Section 7 — Opportunity Cost (Atlas-generated ranking, unheld candidates) | `ALPHA_ARCHITECTURE_DECISION_REQUIRED` | Needs on-demand analysis wiring not yet designed for this purpose |
| Section 8 — Portfolio Consequences (current-state facts) | `ALPHA_FRONTEND_GAP` | Already computed |
| Section 8 — Portfolio Consequences (before/after) | `DEFER_TO_BETA_OR_LATER` | Portfolio Simulation, explicitly and doctrinally out of scope (`DE-006` §8) |
| Section 9 — Assumptions (read-only) | `ALPHA_FRONTEND_GAP` | Already fetched |
| Section 9 — Assumptions (confirmation) | `ALPHA_ARCHITECTURE_DECISION_REQUIRED` | Same as Section 4's assumption-confirmation half |
| Section 9 — Monitoring Conditions | `DEFER_TO_BETA_OR_LATER` | Explicitly named Deferred in the Baseline |
| Section 9 — Invalidation Conditions | `ALPHA_ARCHITECTURE_DECISION_REQUIRED` | Genuinely undesigned; not merely deferred, actually absent |
| Section 10 — Implementation Plan | `ALPHA_ARCHITECTURE_DECISION_REQUIRED` | §9's finding: needs a genuinely new, forward-looking object, distinct from Outcome/Trade |
| Section 11 — Review Plan | `DEFER_TO_BETA_OR_LATER` | Downstream of Monitoring (Deferred) and Invalidation (undesigned) |
| Section 12 — Final Decision Card | *(inherits each source section's classification — no independent classification)* | §13 |
| Section 13 — Record Decision (universal minimum) | `ALPHA_EXISTING` | Already enforced |
| Section 13 — Record Decision (conditional gates) | *(inherits Sections 8/10/11)* | §14 |
| Section 13 — Save as Draft | `ALPHA_ARCHITECTURE_DECISION_REQUIRED` | Conditional on the Daily-Brief-surfacing scope question (§5) |

**Every deferral explained:** Monitoring, Reflection/behavioral-pattern detection, and Portfolio Simulation are deferred because `Atlas-Alpha-Baseline-v1.0.md` §4 says so explicitly and by name (the first two verbatim; Portfolio Simulation via `DE-006` §8's own, separately-documented exclusion, consistent with but not restated by the Baseline). Review Plan is deferred because it structurally depends on Monitoring and on Invalidation Conditions, the latter of which is not merely deferred but genuinely undesigned.

---

## 18. Architecture Decisions

| # | Question | Evidence | Decision | Consequence | Requires ADR? |
|---|---|---|---|---|---|
| 1 | Should `DecisionContext` be the home for investor-authored qualitative context (uncertainties, alternatives considered, portfolio relevance, capital considerations)? | §3 | **`PARTIAL_REUSE`** — yes for investor-authored content; no for Atlas-generated content, per-item acknowledgment, or anything with a post-recording lifecycle | Alpha may add an API endpoint over the existing, already-persisted `DecisionContext` without any domain change, for exactly this bounded content | **No** — this is wiring, not a new architectural commitment |
| 2 | Is `Decision`'s immutability compatible with UX-009's draft/acknowledgment/monitoring/implementation-status requirements? | §4 | **No, not directly** — each requires a separate object; none should be modeled as mutable state on `Decision` itself | Any future implementation design must treat `Decision` as permanently append-only and design every stateful concept as its own small, `decision_id`-referencing object | **Yes** — this is a foundational modeling commitment, not a detail |
| 3 | Does Save as Draft belong in Alpha as specified? | §5 | **`UNRESOLVED — REQUIRES ADR INVESTIGATION`** — contingent on whether UX-009's Daily-Brief-surfacing requirement for drafts is kept for Alpha | If kept, requires a new persisted concept; if dropped, `TRANSIENT_UI_ONLY` suffices | **Yes** |
| 4 | Does Challenge acknowledgment require a new Domain Object? | §6 | **Yes**, but small and shaped identically to `DecisionContext`/`ReflectionResponse` — a minimal, separate, `decision_id`-referencing, immutable, per-item record | Not an extension of `Decision`; not a repurposing of `ReflectionResponse` outside its Deferred scope | **Yes** |
| 5 | Is Monitoring in scope for this Decision Workspace work? | §7, §17 | **No** — explicitly Deferred by `Atlas-Alpha-Baseline-v1.0.md` §4 | Section 9's Monitoring Conditions and Section 11's Review Plan should not be designed as part of this track | **No** — already a settled product-scope decision, not an open architecture question |
| 6 | Is Invalidation in scope? | §7, §17 | **`UNRESOLVED — REQUIRES ADR INVESTIGATION`** — not covered by the Baseline's Monitoring/Reflection deferral (it is a different concept), and not designed anywhere | If pursued, requires new ontology from first principles — no existing pattern to reuse | **Yes** |
| 7 | Can Implementation Plan reuse Outcome or Trade? | §9 | **No** — both are backward-looking; Implementation Plan is forward-looking, per `DE-006` §4's and `UX-008` §13's own already-stated distinction | A new, forward-looking, `decision_id`-anchored concept would be required if built | **Yes** |
| 8 | Is Atlas-generated Opportunity Cost among held positions blocked by Portfolio Simulation? | §10 | **No** — it is backend computation over already-batched, already-computed Cockpit data, not a hypothetical portfolio state | Narrower and more achievable than the earlier Gap Analysis's more uniform treatment suggested | **No** — implementation-design question, not an architecture question |
| 9 | Is Portfolio Consequences' before/after content blocked by Portfolio Simulation? | §11 | **Yes** — `PORTFOLIO_SIMULATION_REQUIRED`, per `DE-006` §8's own explicit exclusion | Section 8 cannot be built as specified until a separate, currently-unscoped Portfolio Simulation decision is made | **Yes** (already effectively open per `DE-006` itself) |
| 10 | Does Section 3's ownership model (Atlas-proposed vs. user-owned) govern implementation? | §12 | **`UNRESOLVED — REQUIRES ADR INVESTIGATION`** — UX-009 body text and `ADR-002` C-03's summary table disagree | No implementation of Section 3 should proceed until this is resolved by whoever owns UX governance | **Yes** |
| 11 | Which decision-type vocabulary governs Section 3's decision-type selector? | §12 | **`UNRESOLVED — REQUIRES ADR INVESTIGATION`** — three incompatible vocabularies exist, only partially collapsible, with at least one confirmed gap (`Avoid`) | Any Section 3 implementation must either adopt the existing five-value `DecisionType` with disclosed collapse (the existing Trim/Remove precedent) or trigger a genuine ontology extension | **Yes** |

---

## 19. UX-009 Status

**`MIXES_MULTIPLE_DOMAIN_CONCERNS_AND_REQUIRES_REVISION`**

UX-009 is not wrong about what a Decision Workspace should feel like or what questions it should answer — UX-008's philosophy is coherent, and UX-009's section-by-section elaboration of it is careful and internally well-reasoned. But UX-009, read as a single flat specification, presents thirteen sections as though they were thirteen instances of the same kind of problem — "surface this content in this order" — when in fact, per this sprint's own findings, they span at least four structurally different situations: content Alpha already has and merely fails to present (Sections 1, most of 4–5, 6's display half, 8's current-state half, 9's assumptions half); content Atlas has built but has deliberately deferred from Alpha by product decision (Section 6's behavioral-context half, Section 9's Monitoring, most of Section 11); content that doctrinally cannot exist without a separate, currently-unscoped capability (Section 8's before/after content, dependent on Portfolio Simulation); and content that genuinely does not exist anywhere and has no designed replacement (Invalidation Conditions, forward-looking Implementation Plan, per-item Challenge acknowledgment, Save-as-Draft's persistence). A single document that does not distinguish these categories will read, to an implementer, as a uniform backlog — exactly the failure mode this sprint exists to prevent. This is not a case of `VALID_BUT_REQUIRES_NEW_ARCHITECTURE` (which would imply one coherent new capability closes the gap) or `PARTIALLY_SUPERSEDED` (nothing here contradicts UX-009; it is simply more architecturally heterogeneous than its own flat section list discloses).

---

## 20. Questions Requiring Future ADRs

Restated from §18, plus two additional items surfaced only by cross-referencing multiple documents together:

1. Formal modeling commitment: every stateful UX-009 concept (draft, acknowledgment, assumption-confirmation, monitoring, invalidation, implementation status, review plan) is a *separate object referencing `decision_id`*, never mutable state on `Decision` itself. (Decision 2, §18)
2. Whether Save as Draft, as specified (including Daily Brief surfacing), is in scope for Alpha, and if so, its persistence design. (Decision 3, §18)
3. Whether Invalidation Conditions are in scope for Alpha at all, independent of Monitoring's already-settled deferral, and if so, their first-principles design — no existing pattern to extend. (Decision 6, §18)
4. Whether a forward-looking Implementation Plan concept is in scope for Alpha, and its relationship (if any) to the existing `decision_type` field. (Decision 7, §18)
5. Whether, and how, Portfolio Simulation itself should ever be scoped — this document does not decide it, only confirms it is the single largest capability multiple UX-009 sections silently assume exists. (Decision 9, §18)
6. **Resolving the Section 3 ownership conflict between UX-009's own body text and `ADR-002` C-03's summary table** — this is UX-governance work, not Alpha-implementation work, but blocks both. (Decision 10, §18)
7. **Resolving the three-way decision-type vocabulary mismatch** (`DecisionType` vs. `PositionAction` vs. UX-008's richer investment/portfolio/review vocabularies), including the confirmed `Avoid` gap with no existing target value. (Decision 11, §18)
8. *(New, found only by cross-referencing `ADR-002` against UX-009 directly, not surfaced by either document alone.)* **What mechanism will verify that any future UX-009 correction — if one is undertaken to resolve #6 or #7 — does not silently reintroduce a conflict with `ADR-002`'s own Cross-Resolution Dependencies** (§"Cross-Resolution Dependencies" in `ADR-002` already requires this discipline for its own six resolutions; UX-009 is not itself one of the seven documents `ADR-002` names as requiring correction, meaning any correction to UX-009 arising from this sprint's findings would be new work, not previously scoped work).
9. *(New.)* **Whether `atlas/monitoring`'s existing `MonitoringEngine`/`MonitoringSignal` infrastructure is the intended eventual target for Section 9's Monitoring Conditions and Section 11's Review Plan**, or whether a Decision-Workspace-specific mechanism is intended instead — this document confirms the infrastructure exists and is deferred, but does not confirm it is the same thing UX-009 is describing.

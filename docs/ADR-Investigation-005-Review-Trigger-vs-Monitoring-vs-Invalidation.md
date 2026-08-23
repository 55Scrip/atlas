# ADR Investigation 5 — Review Trigger vs. Monitoring vs. Invalidation

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Central question:** What is a future-oriented condition attached to an investment decision? Do not assume Review Trigger, Monitoring Condition, and Invalidation Condition are the same thing — test that proposition.

**Method:** Read fresh — the four prior ADR investigations, `Decision-Workspace-Architecture-Resolution-Sprint-1.md`, `DE-005`, `DE-006`, `UX-008`, `UX-009`, `ADR-002`, the `Decision`/`DecisionContext`/`Outcome`/`Evaluation`/`Learning`/`Observation`/`Question`/`Conclusion`/`Judgment`/`ReflectionResponse` entities, and — the decisive new evidence for this investigation — the entire `atlas/monitoring` package (`engine.py`, `__init__.py`, its one test file) read in full, plus a fresh grep for existing staleness/reminder logic in Alpha, which surfaced `atlas/alpha/investment_case/service.py`'s already-wired `_is_thesis_stale` computation.

**Headline finding, stated up front:** `atlas/monitoring` is not a deferred-but-working system Alpha simply hasn't turned on. It is a stateless, deterministic scoring utility with **zero persistence, zero relationship to `Decision` or `Case`, and a "previous baseline" comparison that is synthetically fabricated rather than read from real history.** This is a material correction to how this document series has characterized it — `Architecture-Resolution-Sprint-1.md` described it as "real, separate infrastructure... explicitly deferred," which, now read fully, is more accurate as "a real, tested, but architecturally disconnected module that would need substantial redesign, not merely activation, to serve UX-009's purpose." This correction, and the discovery of `_is_thesis_stale` as an already-working, uniform, time-based staleness signal, shape most of what follows.

---

## Phase 1 — Semantic Vocabulary, Established Independently

- **Review Trigger:** whatever makes a `Decision` worthy of reconsideration — a condition that, when met, should prompt the investor back into the Decision Workspace. Per `Investigation-004`'s own finding, the review *act* itself already resolves into a new `Decision` — so Review Trigger concerns only the *signal preceding* that act, not the act itself.
- **Monitoring Condition:** per `UX-008` §10, "what Atlas should continue observing after the decision is recorded — the signals that indicate whether the decision remains valid." A passive, ongoing watch, not itself a demand to act.
- **Invalidation Condition:** per the same section, "the thresholds at which the decision should be revisited or reversed." Narrower and stronger than Monitoring — the subset of watched facts that, if true, delegitimize the existing reasoning.
- **Observation (Core):** re-confirmed fresh — "something the investor noticed... not an interpretation, not evidence, not a decision... immutable," standalone, no relationship to `Decision`/`DecisionContext`/`Hypothesis`/`Evidence`. Past tense, retrospective, investor-authored.
- **Alert (`MonitoringAlert`):** re-confirmed fresh in this investigation — a stateless, computed-on-demand comparison of two snapshots, never persisted, never anchored to `Decision` or `Case`. Its own "previous" baseline is fabricated via hard-coded per-object-type score deltas (`_previous_baseline()`), not read from stored history — categorically different from what UX-009's own use of "alert" implicitly assumes.
- **Reconsideration:** per `Investigation-004`, a workflow, not a stored fact — resolving into a new `Decision`, optionally via a `Draft`.

**These are not synonyms, even where casual usage conflates them.** This is tested directly, not assumed, across the phases below.

---

## Phase 2 — Existing Monitoring Ontology

`atlas/monitoring` is exactly two source files (`engine.py`, `__init__.py`) plus one test file — confirmed by direct directory listing. No persistence directory, no application-service directory, no API directory, and zero references from anywhere in `atlas/alpha` (confirmed by grep).

| Object | Meaning | Owner | Scope | Persistence | Lifecycle | Mutability | Trigger semantics | Relation to Case | Relation to Decision | Relation to Portfolio | Relation to Watchlist | Relation to Daily Brief |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `MonitoringSnapshot` | A deterministic, scored point-in-time summary | Atlas/system only | Company (by ticker), Theme, Market Health, Market Regime, an *older* `Portfolio` type, an *older* `Watchlist` type | **None** | None — recomputed fresh on every call | N/A (frozen dataclass, nothing persists to mutate) | None | **None — no `case_id` anywhere** | **None — no `decision_id` anywhere** | Uses `atlas.adapters.portfolio.Portfolio`, not Alpha's own holdings model | Uses `atlas.capabilities.watchlist_intelligence`, not `atlas/alpha/watchlist` | None |
| `MonitoringSignal` | One named score + status + summary within a snapshot | Atlas/system only | Same as above | None | None | N/A | None | None | None | None | None | None |
| `MonitoringChange` | The delta between two signals across two snapshots | Atlas/system only | Same | None | None | N/A | None | None | None | None | None | None |
| `MonitoringAlert` | An aggregated comparison of two snapshots | Atlas/system only | Same | None | None | N/A | **None — nothing fires or notifies; `monitor_x()` simply returns an object to its caller** | None | None | None | None | None |

**A load-bearing detail:** `_previous_baseline()` does not read any stored prior state. It *synthesizes* a fake "previous" snapshot by applying hard-coded score deltas (e.g., `previous_score = signal.score - 3` for a generic Company signal). Even `MonitoringAlert`'s own comparison mechanism is not comparing real historical states — it is a synthetic demonstration of what a comparison would look like. `render_monitoring_alert()` self-describes accordingly: "This is deterministic monitoring context, not a notification or investment advice."

**Is the current monitoring package already the ontology UX-009 needs?**

**NO.** Not `PARTIALLY` — the gaps are structural, not a matter of degree:

1. Zero persistence means it cannot support "watch this going forward" semantics at all — there is nothing to accumulate into over time.
2. Zero relationship to `Decision`/`Case` means it cannot anchor a condition to a specific Decision's own reasoning, which UX-009 requires explicitly ("depends on the originating analysis").
3. It operates on entirely different, older `Portfolio`/`Watchlist` type hierarchies than Alpha uses — wiring it in would first require translating between two incompatible domain models.
4. Its own comparison mechanism is admittedly synthetic, not a genuine longitudinal signal — using it as-is would silently present fabricated "changes" as if they were real.

---

## Phase 3 — Observation vs. Monitoring

`Observation`'s own docstring and `capture()` method, re-read fresh: "something the investor noticed... immutable... ObservedAt is preserved exactly as given... the investor's own account of when they noticed something." This is unambiguously past-tense and retrospective.

**Could a Monitoring Condition be represented as an `Observation`? No — a direct temporal/directional contradiction.** A Monitoring Condition is inherently prospective ("watch for X in the future"); `Observation` is inherently retrospective ("I noticed X, in the past"). Forcing the fit would require either fabricating a false past-tense record for something that has not happened ("I noticed X" is not honestly claimable for something one is only proposing to watch *for*), or redefining `Observation`'s own semantics — both forbidden by this investigation's scope.

This is the **third** independent occasion this exact temporal mismatch has been found in this document series — first in `Architecture-Resolution-Sprint-1.md` §7 (Observation vs. Monitoring), again in `ADR-Investigation-003` Phase 9 (Observation vs. Drafts), and now here. Each time against a different candidate use, each time the same underlying reason. This is not a coincidence worth re-litigating each time — it is a stable, load-bearing architectural fact about what `Observation` is and is not.

---

## Phase 4 — Condition vs. Event

"Revenue growth falls below 5%" (a predicate — a rule that can evaluate true or false at any future point) and "Revenue growth has fallen below 5%" (a detected event — a specific, dated fact that the predicate evaluated true at some particular moment) are **not the same ontology.**

| Stage | What it is | Object needed? |
|---|---|---|
| Condition definition | A predicate/rule, authored once (plausibly at Decision-recording time), persisting unevaluated until checked | A real, structured or free-text predicate record — does not exist anywhere today (confirmed: `atlas/monitoring` has no threshold/predicate concept, only computed scores) |
| Condition evaluation | The act of checking the predicate against current data | A computation, not a stored object |
| Detected event | The moment a condition evaluates true — a dated occurrence | A dated, Atlas-authored fact — structurally similar to, but authorship-distinct from, `Observation` (Atlas-detected vs. investor-noticed) |
| Notification | Telling the investor a detected event occurred | Delivery/UI concern, not ontology of its own |
| Investor action | What the investor does in response | Reconsideration — already fully resolved by `Investigation-004` |

Separating these five stages cleanly prevents the single most common failure mode this investigation is testing for: conflating "the rule" with "the rule being met" with "someone being told about it."

---

## Phase 5 — Review Trigger Ontology

Testing whether one ontology can honestly represent all six named examples:

| Example | Mechanism |
|---|---|
| Scheduled review date reached | Time-based — pure calendar comparison, needs only a stored date |
| Thesis assumption invalidated | State-based — needs a stored predicate plus real detection against live data |
| Material new evidence appears | Event-based, sourced from the upstream Core Loop's own Evidence/Observation/Conclusion chain — a different trigger *source* entirely |
| Valuation crosses threshold | State-based, numeric — similar to the second, different data type |
| Portfolio concentration exceeds limit | State-based, **but Portfolio-scoped, not Decision-scoped at all** |
| User manually chooses to review | No stored condition or detection needed whatsoever — already fully covered by UX-009 §2's own "User-initiated" trigger |

**Can one ontology honestly represent all six? No — decisively.** These six span at least four structurally different mechanisms: calendar comparison, threshold-predicate evaluation requiring real monitoring, upstream-Core-Loop-triggered, and Portfolio-wide-scoped computation unrelated to any single Decision. **"Review Trigger" is not itself a single domain object — it is a product-level label for "any of several structurally different things that can lead the investor back into the Decision Workspace."** Forcing all six into one object would either become a meaningless bag of unrelated fields, or silently misrepresent at least one of them (most obviously the fifth, which is not Decision-scoped at all).

---

## Phase 6 — Monitoring Condition Ontology

- **Authorship:** UX-009's own text — "Atlas-proposed, user-adjustable" — both, collaboratively. The identical authorship shape UX-009 already uses for Section 4's "Essential assumptions" ("Atlas-identified, user-confirmable"), a precedent within the same document, not a new pattern invented here.
- **Scope:** UX-009's own text scopes it to "what Atlas should watch *after the decision is recorded*" — Decision-scoped by construction, for the primary case UX-009 describes. Phase 5 (item 5) already found this cannot be the *only* scope that exists; the narrower claim here is that Monitoring Conditions specifically, as UX-009 describes them, are Decision-scoped — other, differently-scoped siblings exist alongside them (Phase 13).
- **Can it exist without a Decision?** No, per UX-009's own text — created after a Decision is recorded.
- **Can one condition belong to many Decisions?** Not evidenced anywhere; UX-009 always describes conditions as belonging to the one Decision they accompanied.
- **Can a Decision have many conditions?** Yes — UX-009: "Two to three items."
- **Predicate, task, or expectation?** A predicate, most precisely — "a specific observable signal" (UX-009's own phrase) — not a task (nothing to *do*), and more precise than "expectation," consistent with Phase 4's condition-definition/detected-event split.

---

## Phase 7 — Invalidation Condition Ontology

**Is it simply `Monitoring Condition + severity`? Close, but not exact.** UX-009's own text draws the line functionally, not by severity label: "Monitoring is passive observation. Invalidation is the threshold that triggers re-entry into the Decision Workspace." The more precise reduction is `Monitoring Condition + a designated trigger-role`, which severity-like language often correlates with but is not identical to.

- **Does invalidation invalidate the Decision?** No — per `Investigation-004`'s own Phases 1/10, nothing can un-make a Decision's historical truth. Invalidation means the *current reasoning* is no longer sound, not that the past commitment was false when made.
- **The thesis?** Yes, most directly — `UX-008` §1's own definition of Investment Thesis as "the specific, named claim... that justifies holding, adding to, reducing, or exiting a position."
- **An assumption?** Yes, as the mechanism — UX-009's own Section 9 frames Invalidation Conditions as thresholds on the Supporting Assumptions the thesis depends on.
- **A Conclusion?** Only indirectly — a Conclusion (Core Loop) feeds a Decision via `ConclusionDecisionLink`; invalidation could undermine the *continued relevance* of a prior Conclusion, never its own historical truth (Conclusion, like Decision, is immutable and permanently true as recorded).
- **The current Recommendation?** Derivatively, not identically — `Investigation-004`'s own Phase 11 already established "current recommendation" as Atlas's own, independently-recomputed output, architecturally separate from any investor-stated invalidation condition. The two often correlate; they can, in principle, diverge.
- **Only the investor's prior reasoning?** The most precise, defensible answer: invalidation is a claim about whether the *specific reasoning recorded in a past Decision* remains sound — not a claim about objective truth, not a mutation of the Decision, not automatically identical to Atlas's own recommendation.

**Can an invalidation condition be satisfied without forcing a new Decision?** Yes — `ADR-002` C-04's own completion-gate model ("unacknowledged Challenges... never blocks recording") and `Investigation-004`'s own "Atlas never blocks... the investor's own judgment governs" finding both apply directly: Atlas may surface that a condition was met without forcing action.

**Can Atlas disagree with the investor about whether invalidation occurred?** Yes, and precisely: the condition itself is investor-confirmed at Decision time (Phase 6); its *evaluation* against later data is Atlas's own computation. Atlas could compute a stored predicate as true while the investor, reading the same data, disagrees it constitutes genuine invalidation — structurally identical to the existing Challenges-acknowledgment model ("I have seen and considered this," never "I agree with this," `ADR-002` C-04, reused directly).

---

## Phase 8 — Assumption Relationship

Testing `Assumption → Monitoring Condition → Invalidation Condition` as a formal dependency chain, not assuming it:

- **Could a Monitoring Condition exist without a named assumption?** Yes, plausibly — UX-009's own example ("Next quarterly earnings for enterprise AI infrastructure spending") is a general informational watch-point, not obviously tied to one specific named assumption.
- **Could an assumption exist without monitoring?** Yes, trivially — UX-009's own Section 4 "Essential assumptions" appear without any accompanying monitoring/invalidation apparatus at all; only Section 9 re-surfaces them alongside Monitoring/Invalidation.
- **Could one invalidation condition relate to several assumptions?** Plausibly — a compound condition could reference more than one assumption's threshold, though UX-009 gives no explicit compound example.

**Conclusion: the grouping is not a strict formal dependency chain.** It is UX-009's own *presentational* grouping of three related-but-independent concepts under one section, because all three are "conditions the current reasoning depends on and Atlas should track" — not because one formally derives from or requires another. A future implementation should model Assumptions, Monitoring Conditions, and Invalidation Conditions as loosely-related, similarly-shaped siblings, informally cross-referenced where an investor happens to relate them — not a rigid, structurally-enforced hierarchy.

---

## Phase 9 — Decision Relationship

- **Part of Decision?** No — the same immutability argument as every prior investigation: a growing list of conditions is mutable state `Decision` structurally cannot hold.
- **References from Decision?** Possible, not required — could follow the `observation_id` optional-additive-field precedent, but nothing in the evidence requires `Decision` itself to reference conditions; the reverse (condition → `decision_id`) is simpler and matches every comparable object's own established shape (`DecisionContext`, `ReflectionResponse`, `SecurityConfirmationEvent`).
- **Case-level objects created during Decision capture?** Per Phase 6, no — UX-009 frames Monitoring/Invalidation as Decision-scoped specifically, not Case-wide (though Phase 13 finds a genuinely Case-scoped sibling is separately needed).
- **Draft-level objects promoted at recording time?** Plausible and consistent — `Investigation-003`'s own Phase 5 ownership table already identified "implementation intent" and "review intent" as draft content with no post-Decision home; Monitoring/Invalidation conditions plausibly belong in the same category, drafted alongside the rest of the reasoning, then captured as their own Decision-anchored objects at commit time — mirroring exactly how `DecisionContext` itself would be captured from draft content per `Investigation-003` Phase 11.

**Can conditions be edited after Decision recording?** UX-009's own text says yes, explicitly: "After recording, items are locked and versioned. Changes to monitoring or invalidation conditions after recording create a visible amendment in the decision history." This directly matches `Investigation-004`'s own Phase 3 finding — Amendment is a property a Decision-*adjacent* companion object needs, never a property of `Decision` itself — and `Investigation-003`'s own Model B/C.

**Does this create post-hoc rationalization risk?** Only under a naive Model A (mutable row). Under Model B/C (append-only revision, current-state-as-derived-projection), every prior version remains permanently inspectable — "amendment" and "post-hoc rationalization" are not the same thing as long as the old condition text stays visible. UX-009's own phrase "amendments versioned" already signals this exact non-mutating model. This is the **third** independent convergence in this session on the identical architectural shape — Security Confirmation (built), `Investigation-003`'s Draft (proposed), and now this — reinforcing it as an established, reusable template, not a fresh invention each time.

---

## Phase 10 — Temporal Lifecycle

Testing the proposed chain arrow by arrow, not assuming it:

```
Draft → Decision → Monitoring Condition active → Condition evaluated repeatedly
  → Signal detected → Alert → Review Trigger → Reconsideration → New Decision
```

| Arrow | Verdict |
|---|---|
| `Draft → Decision` | Persisted objects, already fully resolved (`Investigation-003`/`004`) |
| `Decision → Monitoring Condition active` | A persisted object (Phase 6/9), created alongside or shortly after Decision |
| `Monitoring Condition active → Condition evaluated repeatedly` | **Not an object** — a process/workflow (periodic computation), needs a scheduler mechanism, not a domain concept (explicitly out of this investigation's ontology-only scope) |
| `Condition evaluated repeatedly → Signal detected` | Potentially a persisted, dated fact — a "detected event" (Phase 4) |
| `Signal detected → Alert` | **Not a separate object** — presentation/delivery of the underlying detected-event record (Phase 4) |
| `Alert → Review Trigger` | **This arrow is mislabeled.** Per Phase 5, Review Trigger isn't one object; a detected Invalidation-Condition-met event simply *is* one instance of UX-009 §2's own existing "Invalidation signal" trigger type, once surfaced |
| `Review Trigger → Reconsideration` | **This arrow collapses** — per Phase 5/7, the surfaced event either prompts reconsideration or doesn't; nothing forces it |
| `Reconsideration → New Decision` | Already fully resolved by `Investigation-004` |

**Corrected picture:** only two nodes in the proposed chain are genuinely persisted objects that do not exist today — the Condition itself, and, optionally, the Detected Event. Everything else is either an already-resolved existing mechanism (Draft, Decision, Reconsideration) or a process/UI concern requiring no new domain object at all.

---

## Phase 11 — Scheduling

Testing whether "review in 90 days" needs the same ontology as "review if debt/EBITDA exceeds 3×":

A **time-based** condition needs only a stored date and a trivial `today >= date` comparison — no market data, no threshold-predicate evaluation, no dependency on Atlas's own analysis pipeline. A **state-based** condition needs a stored predicate *and* ongoing, real evaluation against live financial data.

**Direct existing precedent found:** `atlas/alpha/investment_case/service.py`'s `_is_thesis_stale` already implements a time-based staleness signal today — a fixed, uniform `VERY_OLD_CASE_THRESHOLD_DAYS = 90` (reused from `PortfolioStatusService`), computed fresh from `min(decided_at, observed_at)` timestamps, never investor-configurable, never persisted as its own object. Coincidentally the same round number ("90 days") UX-009's own example text uses — worth noting, not over-reading. This is *already-shipped, real code* demonstrating exactly that time-based and state-based conditions in this codebase use completely different mechanisms even where the same number appears: a plain datetime comparison here, versus a live-scoring-engine comparison for anything state-based.

**Recommendation from this evidence:** a single, unified *object shape* for Condition (both are, at bottom, "a predicate defined at Decision/Case time, evaluated later") — but explicitly **not** a single, unified *evaluation mechanism*. Time-based evaluation is trivial and needs no monitoring infrastructure at all; state-based evaluation genuinely needs real, currently-nonexistent, live-data-watching infrastructure that `atlas/monitoring`, per Phase 2, does not provide in any Decision-anchored, persisted form.

---

## Phase 12 — Daily Brief

Distinguishing what Daily Brief needs to *know* from what it needs to *display*:

| Candidate | Know? | Display? |
|---|---|---|
| Active Monitoring Conditions | Yes (to check them) | **No** — too granular; per `Architecture-Resolution-Sprint-1.md` §14's own "narrow projection, not raw content" principle, reused directly |
| Triggered conditions only | Yes | **Yes** — matches UX-009's own "surfaced as unresolved" language, mirroring `Investigation-003`'s own Draft-surfacing finding |
| Alerts | N/A today (Phase 2: nothing real to know) | If a real, Decision-anchored alert mechanism is ever built, only a narrow summary |
| Review Triggers | Yes, as a **union** of several sources | Yes — the union itself, not each source separately |
| Overdue reviews | Yes | Yes — derived from a stored date, no new object beyond it (Phase 11) |
| Invalidations | Yes | Yes, at higher priority than plain Monitoring — invalidation's whole purpose (UX-009) is triggering surfacing |
| Unresolved reconsiderations | Yes | Existence + subject + resume link only, per `Investigation-003`'s own Phase 14 finding, reused directly — never full draft content |

**Architectural boundary, not UI design:** Daily Brief's real requirement is a narrow, computed projection that unions several underlying sources (unresolved Drafts, met Invalidation Conditions, overdue time-based conditions, sufficiently-important met Monitoring Conditions) — never direct access to full condition definitions, full draft content, or raw monitoring data. This extends, rather than restates, the identical principle `Investigation-003` already established for Drafts specifically.

---

## Phase 13 — Watchlist and Portfolio

Testing whether Decision-scoping alone is sufficient:

Phase 5's own item 5 (Portfolio concentration) already provides a real, evidenced counterexample: a Portfolio-wide concentration limit has no single originating Decision at all — it is a property of the whole portfolio, computed across many holdings. **Decision-scoping alone is too narrow, confirmed directly, not speculatively.**

Watchlist securities are a starker case: by definition, a Watchlist security has no recorded Decision at all (nothing has been committed to yet), so a condition like "watch AAPL's valuation before considering initiating" cannot be Decision-anchored even in principle.

**This confirms a layered structure, not one flat scope:**

1. **Decision-scoped** conditions — Monitoring/Invalidation set alongside a specific recorded Decision (UX-009's own primary case).
2. **Case-scoped** conditions — relevant to a specific security/Case regardless of whether any Decision exists yet. Covers Watchlist securities directly, since `Investigation-001` already established Watchlist securities map 1:1 onto real `Case` objects even before any Decision exists.
3. **Portfolio-scoped** conditions — relevant to the whole portfolio, not any single security. Not covered by either of the above.

"Securities with no Case at all" (the phrase's own explicit example) needs either a fourth scope or, more simply, a `Case` created for them first — trivial per `Investigation-001`'s own finding that `Case.create()` is content-free ("creates a Case, nothing else"). This phase is explicitly flagged as critical for future international/provider-driven monitoring, and the evidence supports that concern directly: a Decision-only-scoped design would need a disruptive redesign the moment Portfolio-wide or pre-Decision conditions are wanted — which UX-009/UX-008 already, implicitly, want.

---

## Phase 14 — Recommendation and Atlas Analysis

Testing whether Recommendation changes (BUY→HOLD, confidence collapse, valuation support becoming unavailable, a new contradiction appearing) should automatically create Review Triggers:

**Is this monitoring?** No — Monitoring Conditions (Phase 6) are investor-Decision-anchored predicates agreed to at Decision time; a Recommendation change is Atlas's own, independently-recomputed output changing, unprompted by any specific stored condition.

**Derived change intelligence? Yes — and this already exists, is already wired, and does not need to be invented.** This session's own prior work confirmed the Investment Case page's own Change Intelligence package ("What Changed" sections) already computes and displays exactly these kinds of deltas. This is not a gap.

**A trigger?** Only in UX-009 §2's own loose taxonomy sense — "Thesis change" and "Valuation change" are two of its eight named trigger types — but per Phase 5, this needs no new object; it is another instance of the same union-of-sources category, sourced from already-existing Change Intelligence rather than any investor-set condition.

**Merely new evidence?** In one real sense yes — a Recommendation shift is itself downstream of new Evidence/Conclusions entering the Core Loop, matching UX-009 §2's separately-named "New evidence" trigger type.

**Conclusion:** automatic Review Triggers from Recommendation changes should **reuse the already-existing Change Intelligence computation**, surfaced through Daily Brief (Phase 12) as one more source feeding the same union-projection — not a new, separate object. This phase's own instruction ("do not create automatic semantics without evidence") is honored precisely by finding that the needed semantics already exist and simply need surfacing, not invention.

---

## Phase 15 — User Authorship vs. Atlas Authorship

| Concept | Owner |
|---|---|
| Condition definition (predicate text/structure) | **Shared** — "Atlas-proposed, user-adjustable" (UX-009's own text) |
| Threshold | **Shared**, same reasoning |
| Review date | **Shared** — investor-set primarily, though UX-009 §11 explicitly allows Atlas to propose one based on Monitoring Conditions, confirmed or adjusted by the investor |
| Invalidation meaning | Investor-anchored, ultimately (Phase 7's "only the investor's prior reasoning" finding), though Atlas proposes candidates |
| Triggered signal | **System-derived** — pure Atlas computation, no investor authorship |
| Alert | **System-derived**, presentation-only |
| Decision to reconsider | **Investor, exclusively** — per Phase 7's "Atlas never blocks... the investor's own judgment governs" |

**What Atlas may safely generate automatically:** proposed condition text/thresholds as a starting point, always investor-adjustable and never silently finalized without confirmation — the same authorship-transfer discipline `ADR-002` C-02 already established for Atlas-suggested content generally, reused rather than reinvented; triggered-signal detection; alert/change-intelligence computation and surfacing. **What must remain investor-authored:** final confirmation of an invalidation condition's meaning; the decision to actually reconsider; agreement that a triggered signal constitutes genuine invalidation (Phase 7's disagreement-is-possible finding).

---

## Phase 16 — Persistence and Immutability

| Model | Semantic integrity | Auditability | Complexity | Post-hoc rationalization risk | Consistency with Decision | Consistency with Security Confirmation | Suitability for future automation | Suitability for Alpha |
|---|---|---|---|---|---|---|---|---|
| **A — Mutable rows** | Weakest — first mutable-row precedent break in this codebase | None | Lowest | Real | Breaks the uniform convention | **Contradicts it directly** — the exact pattern Security Confirmation deliberately moved away from | Poor | Sets a bad precedent already once abandoned |
| **B — Immutable condition + superseding revisions** | Strong | Excellent | Moderate | Essentially none | Excellent | Close match | Good | Good |
| **C — Append-only lifecycle events (definition immutable; activate/deactivate/supersede as events)** | Strong | Excellent | Moderate, but solved | Essentially none | Excellent | **This is the `SecurityConfirmationEvent` pattern, directly** — proven and shipped | Best fit — an event stream is naturally extensible to automated evaluation output | Best of the four |
| **D — Purely derived (nothing persisted but original Decision text)** | Adequate, minimal | None beyond re-reading raw text | Lowest of all | None — nothing to rationalize post-hoc since nothing structured exists | Trivially consistent (nothing added) | Not applicable | **None — forecloses any automated detection entirely** | A real, viable minimal-footprint option for an early phase, with a disclosed, permanent cost |

**Model C is, for the third time in this document series, the winning shape** — the same already-proven `SecurityConfirmationEvent`/derived-current-state pattern `Investigation-003` already selected for Drafts. This is now an established, reusable architectural template for this entire family of "editable-over-time but historically-honest" concepts, not a fresh invention each time it recurs.

---

## Phase 17 — Existing Monitoring Package Reuse

**Kept separate.** Not reused unchanged (Phase 2's decisive NO — wiring it in as-is would propagate a fabricated comparison baseline as if real). Not extended (extending a stateless, Decision-unaware, differently-typed legacy module into a persistent, Decision-anchored condition system would be a near-total rewrite in disguise, not an extension). Not wrapped (wrapping a fabricated baseline behind a thin interface would just make the fabrication harder to see). Not replaced (nothing in this investigation evaluated, or found wrong with, whatever legitimate current callers `atlas/monitoring` may have for deterministic scoring snapshots — replacing it is out of this investigation's scope and unjustified by anything found here).

**What it already owns:** deterministic, stateless, on-demand scoring and snapshot comparison for Company/Theme/Market Health/Market Regime/an older Portfolio type/an older Watchlist type — a display/summary utility, not a condition-tracking system.

**What it does not own:** any persistence; any `Decision`/`Case` anchoring; any investor-authored predicate concept; any real longitudinal comparison (its own baseline is synthetic); any trigger/notification delivery mechanism; any relationship whatsoever to Alpha's actual domain model.

---

## Phase 18 — Alternative Architectures

| Option | Semantic fit | Overlap with current ontology | New objects required | Migration impact | Daily Brief compatibility | Decision immutability compatibility | Future automation | Failure modes |
|---|---|---|---|---|---|---|---|---|
| **A — Monitoring owns everything** | Poor — the existing package cannot "own" this without first becoming an entirely different, persistent, anchored system. Really means "build something new and call it Monitoring" | None genuine | Effectively all of them, mislabeled | Same as building fresh, plus confusing legacy naming | N/A until rebuilt | N/A | N/A | Misleading labeling; hides the true scope of work |
| **B — DecisionCondition aggregate** | Good for Phase 8's loosely-related-siblings finding (one object, `kind: monitoring \| invalidation` discriminator) | Low, additive | One new object family | None to existing objects | Good, via projection | Compatible (references only) | Good | **Fails Phase 13** if scoped only to `decision_id` — too narrow |
| **C — Separate MonitoringCondition + ReviewSchedule, Review Trigger derived** | Partial — closer to Phase 5's union finding, but introduces a structural split Phase 8 found unnecessary (time/state conditions can share one object shape per Phase 11) | Low, additive | Two new objects where one suffices | None to existing | Good, via projection | Compatible | Good | Unjustified structural split |
| **D — CaseCondition (Case-scoped, optional Decision provenance)** | **Best fit** — matches Phase 13 directly (Decision-scoping too narrow; Watchlist has Cases, not Decisions) and Phase 9 (optional `decision_id`, mirroring the `observation_id` precedent) | Low, additive, follows existing `case_id`-referencing pattern already used by `Decision` itself | One new object family | None to existing | Good, via projection | Compatible | Good, especially under Model C | Does not, by itself, cover Portfolio-wide conditions (Phase 13/19) |
| **E — Generic Watch Condition (Security/Case/Portfolio, one shape)** | Tempting given Phase 13's Portfolio example, but a Portfolio-wide condition (no single subject, spans all holdings) is structurally coarser than a Case-scoped one — collapsing them risks the same "vague dumping ground" failure `Investigation-003`'s own Option E was rejected for | Moderate, but blurs distinct scopes | One new, maximally generic object | None to existing | Workable, but harder to build a clean narrow projection from a loosely-typed generic bag | Compatible | Workable | Under-differentiates genuinely different-shaped concerns |
| **F — No new ontology (derive everything transiently)** | Matches Model D (Phase 16) — a real, viable, minimal-footprint reading for an early phase | None | None | None | Minimal — only "you said you'd review this, go re-read your notes" | Trivially compatible | **None — forecloses automated detection** | Permanently limits the product to manual re-reading unless later revisited |

---

## Phase 19 — Consistency Test

Challenging Option D (`CaseCondition`, built on Model C), documenting rather than resolving:

- **vs. Decision:** no contradiction — untouched; only optionally referenced.
- **vs. DecisionDraft:** no contradiction, and a positive integration point — condition content plausibly originates as draft content, captured as a real `CaseCondition` only at commit time (Phase 9), mirroring how `DecisionContext` itself would be captured from draft content per `Investigation-003`.
- **vs. DecisionContext:** no contradiction — genuinely distinct shapes (free-text circumstantial narrative, captured once, vs. a structured, evaluable predicate with an ongoing lifecycle).
- **vs. ReflectionResponse:** no contradiction — no relationship; ReflectionResponse remains occasioned by Pattern/Coaching, entirely separate.
- **vs. Evaluation:** a loose, disclosed, non-forced possible future connection — an `Evaluation`'s own content could plausibly prompt setting a new `CaseCondition`, but nothing requires this relationship.
- **vs. Learning:** no contradiction — unrelated, different roles in the Core Loop.
- **vs. Case:** directly consistent, not merely non-contradictory — `Case`'s own explicit minimalism doctrine (re-confirmed via `Investigation-003` Phase 8) is respected precisely because `CaseCondition` is a *separate* object merely referencing `case_id`, the identical non-violating shape `Decision` itself already uses.
- **vs. Observation:** no contradiction, but the temporal-directional distinction (Phase 3) must be maintained precisely by any future implementation — a real, disclosed naming/implementation-discipline risk, not an ontology-level conflict.
- **vs. KnowledgeReference / ReasoningTrace:** no contradiction — confirmed disjoint shape across every prior investigation.
- **vs. Recommendation:** no contradiction — Recommendation-driven triggers reuse existing Change Intelligence (Phase 14), entirely separate from investor-set `CaseCondition`s; the two sources union only at the Daily Brief presentation layer, never merge at the domain layer.
- **vs. Portfolio:** **a genuine, disclosed gap, not resolved.** Portfolio-scoped conditions (concentration limits) do not fit `CaseCondition`'s own Case-anchored shape at all (Phase 13). Option D explicitly does not solve Portfolio-scoped conditions and is not claimed to.
- **vs. Watchlist:** consistent — Watchlist securities already map onto real `Case` objects (`Investigation-001`), so `CaseCondition` covers them without special-casing.
- **vs. Daily Brief:** consistent, given the narrow-projection/union-of-sources boundary (Phase 12) is respected — a design-discipline requirement, not an ontology conflict.
- **vs. Security identity:** no contradiction — no relationship exists or is proposed beyond reusing Security Confirmation's own *persistence pattern* (Model C), never its objects or scope.
- **vs. imported Decisions:** no contradiction — the optional `decision_id` reference accommodates `IMPORT`/`API`/`BROKER_SYNC` Decisions with zero special-casing, exactly as `observation_id` already does (`Investigation-003`/`004`, reused).
- **vs. future automation:** consistent — Model C's event-sourced shape is well-suited to future automated evaluation output, though building that automation is itself future, unauthorized work.
- **vs. future collaboration:** the same disclosed, inherited limitation already named in `Investigation-003` and `Investigation-004` — a Case-scoped-only model becomes ambiguous ("whose condition is this") once multi-user access to a shared Case exists, which nothing today supports.

**Two genuine gaps found and documented, not resolved, per instruction:** (1) Portfolio-scoped conditions are explicitly not covered by the preferred architecture — a real, acknowledged limitation, not a silent omission; (2) the Observation temporal-naming discipline risk, now confirmed for a third time, carried forward rather than re-argued.

---

## Phase 20 — Final Decision

**`CASE_CONDITION`**

**Is new ontology required?** Yes. Tested exhaustively across Phases 2, 3, 6, 7, and 9, no existing object — `atlas/monitoring`, `Observation`, `DecisionContext`, `ReflectionResponse`, `Evaluation`, `Judgment`, `KnowledgeReference`, `ReasoningTrace` — can represent a forward-looking, evaluable, Case-or-Decision-anchored predicate. `atlas/monitoring` in particular is decisively not it, for structural reasons (no persistence, no `Decision`/`Case` awareness, a fabricated comparison baseline), not a matter of styling or activation.

**Does current Monitoring survive?** Yes, unchanged, kept fully separate (Phase 17). Nothing in this investigation invalidates its own narrow, legitimate current use; it was simply never the ontology this investigation needed it to be.

**What is Review Trigger?** Not a single domain object — a product-level label for the union of several structurally different sources: time-based `CaseCondition`s past due, state-based `CaseCondition`s evaluated true, upstream Change-Intelligence-detected recommendation shifts (already built, Phase 14), and plain user-initiated entry. Resolved entirely as a Daily-Brief-layer projection (Phase 12), never a standalone aggregate.

**What is Invalidation?** A `CaseCondition` whose evaluation outcome is specifically designated (Phase 7) to warrant re-entry into the Decision Workspace — the same underlying object shape as Monitoring, distinguished by trigger-role, not a separate aggregate.

**Where does Reconsideration begin?** At the workflow boundary `Investigation-004` already established. A `CaseCondition`'s detected/met state (or plain user-initiated entry) surfaces the *reason* per UX-009 §2's own existing taxonomy; Reconsideration itself remains exactly what `Investigation-004` concluded — a workflow resolving into a new Draft or Decision, not a new object of its own.

**What remains unresolved:** Portfolio-scoped conditions (Phase 13/19 — a real, acknowledged gap `CASE_CONDITION` does not close); the exact evaluation/scheduling mechanism (explicitly out of this investigation's ontology-only scope); whether `CaseCondition` content is always captured via Draft or sometimes directly at Decision-commit time; the future-collaboration Case-scoping ambiguity, inherited and restated, not newly created.

---

## ADR Candidate (Outline Only)

**Problem:** UX-009 requires Monitoring Conditions, Invalidation Conditions, and a Review Plan. No existing object can represent any of them, and the existing `atlas/monitoring` package, despite its name, is architecturally unrelated to Alpha's Case/Decision ontology.

**Context:** `Decision` is immutable and cannot hold mutable condition lists (Phases 6, 9). `atlas/monitoring` is stateless, Decision/Case-unaware, and its own historical comparison is fabricated (Phase 2). A real, already-shipped precedent for exactly this shape of problem exists — `SecurityConfirmationEvent`'s append-only-events-plus-derived-current-state pattern (Phase 16, 17), reused for a third time in this document series. Decision-scoping alone is too narrow: Watchlist securities have Cases but no Decisions, and Portfolio-wide conditions have neither (Phase 13).

**Decision:** Adopt a new, minimal, illustratively-named `CaseCondition` concept — Case-scoped by default, with an optional `decision_id` back-reference for the common case where a condition originates from a specific Decision Workspace recording. Built on the append-only-events-plus-derived-current-state pattern already proven by Security Confirmation.

**Invariants (illustrative, not binding — no schema decided here):**
- References `case_id` always; `decision_id` optionally, following the `observation_id` precedent.
- A condition's *definition* is captured once; its lifecycle (active → met → dismissed/amended → superseded) is a sequence of immutable events, never a mutated row.
- Authorship is shared: Atlas may propose text/thresholds; the investor confirms or adjusts, following `ADR-002` C-02's own authorship-transfer discipline.
- Time-based and state-based conditions share one object shape but never one evaluation mechanism.
- No field anywhere marks a Decision "monitored" or "invalidated" — that state lives entirely on `CaseCondition`, never on `Decision` itself.

**Consequences:** `Decision`'s immutability remains completely untouched. `atlas/monitoring` requires no change and is not implicated. Daily Brief gains one more source to union into its existing narrow-projection boundary (Phase 12), not a new content type to design from scratch. Portfolio-scoped conditions remain explicitly unsolved and out of scope for this ADR.

**Rejected Alternatives:** A (Monitoring owns everything — really means building something new under a misleading name); C (a structural MonitoringCondition/ReviewSchedule split — unjustified given Phase 8's siblings finding); E (a fully generic Watch Condition — under-differentiates genuinely different-shaped scopes); F (no new ontology — a real, viable minimal option, but permanently forecloses automated detection, a disclosed and significant cost).

**Migration/Compatibility:** None required to any existing object. Fully additive.

**Open Questions** (carried forward, not resolved here):

1. How should Portfolio-scoped conditions (concentration limits, sector exposure) be represented, given they explicitly do not fit `CaseCondition`'s own Case-anchored shape? (Phase 13, 19)
2. Should `CaseCondition` content always be captured via a Draft first, or is direct Decision-time capture also legitimate? (Phase 9)
3. What is the actual scheduling/evaluation mechanism for state-based conditions, given `atlas/monitoring` cannot currently serve this role? Explicitly out of this investigation's ontology-only scope, but a real, unavoidable next question. (Phase 11, 17)
4. Should Daily Brief's union-of-sources projection (Phase 12) be its own read-model service, or computed ad hoc per request? An implementation question, not decided here.
5. Does the future-collaboration Case-scoping ambiguity, now named a third time across three investigations, warrant its own dedicated investigation before any of these objects are actually built? (Phase 19)

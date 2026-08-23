# ADR Investigation 6 — CaseCondition: Definition, Predicate, Lifecycle & Evaluation

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Starting premise, not reopened:** `Investigation-005` already established that a new `CaseCondition` ontology is required. This document does not re-litigate that conclusion — it determines precisely what `CaseCondition` *is*.

**Method:** This investigation builds tightly on the evidence already gathered across `Investigation-001` through `Investigation-005`, all still fresh in this session, refined rather than rediscovered. One new check was performed fresh: a corpus-wide search for any existing predicate/threshold/expression domain concept (`class.*Predicate`, `class.*Threshold`, `class.*Expression`) — none found, confirming Phase 2 must be answered from first principles.

**Headline finding, stated up front:** the investigation converges, independently across four separate phases (3, 4, 10, 12), on a single, economical shape: **exactly two objects** — a stable `CaseCondition` identity (the definition) and one unified `CaseConditionEvent` stream anchored to it (covering both revisions *and* meaningful evaluation transitions as different event types). This is materially leaner than the eight-item lifecycle and multi-object shape the investigation's own phase list might suggest — finding that economy is itself the ontological work this investigation was asked to do.

---

## Phase 1 — What Is a CaseCondition?

Testing each candidate framing to contradiction:

| Candidate | Verdict | Why |
|---|---|---|
| Expectation | Fails | Too passive — implies nothing is actively tracked. Also collides with what `Decision.investment_case.reason`/UX-009 Section 4 already cover (what the investor expects to happen) — a different concept a CaseCondition must stay distinct from. |
| Prediction | Fails | Implies Atlas forecasting a probability — directly contradicts `UX-008`'s own anti-false-precision doctrine (already cited repeatedly this series, `DE-004` §5). A condition is a threshold, not a forecast. |
| Reminder | Fails | Too shallow — a reminder is a *consequence* of a condition being met (Phase 4's Alert/Notification stage), not the condition's own definitional content. |
| Task | Fails | Reconfirms `Investigation-005` Phase 6 directly: a condition represents a predicate, not something to *do*. |
| Watch instruction | Fails | Conflates two things `Investigation-005` Phase 4 already found must stay separate — the definition of what to watch for, and the process of watching (evaluation). An "instruction" bundles both. |
| **Predicate** | **Survives** | Matches `Investigation-005` Phase 6 directly: "a specific observable signal." Consistent with everything already established. |
| Future fact | Fails | Epistemically wrong — a condition is not itself a fact; it is a *rule* that, evaluated against a future fact, produces a truth value. Confusing the two is exactly the Condition/Event conflation `Investigation-005` Phase 4 already dismantled. |
| Hypothesis | Fails | The Core Loop's own `Hypothesis` explains a current observation, feeding toward a `Conclusion` — a different direction (explains the past/present) than a condition (screens the future), and anchors to `Evidence`, not `Decision`/`Case`. |
| Decision dependency | Partial, incomplete alone | Captures *why* a condition matters (what the reasoning depends on) but not the evaluation/trigger mechanism — a dependency could be a static fact with no tracking lifecycle at all. |

**Conclusion:** a `CaseCondition` fundamentally represents **a predicate about a future or ongoing fact, defined once, that Atlas can (or will eventually be able to) evaluate against real data over time, whose evaluation outcome informs whether the reasoning behind a Decision remains sound.** This synthesizes Predicate (the logical shape) with Decision-dependency (the semantic anchor) without collapsing into either alone.

---

## Phase 2 — Predicate Ontology

- **Always boolean?** Only at the *evaluation* level — a condition ultimately "is met" or "is not met" at a given check. The underlying comparison is not uniformly boolean: it can be a threshold crossing (numeric), a qualitative judgment, a date comparison, or an event occurrence.
- **Qualitative conditions?** Yes — UX-009's own examples ("China revenue trend," "capital-allocation policy changes against expectations") are narrative, not reducible to a formula, though they still resolve to true/false at evaluation time.
- **Dates?** Yes — `Investigation-005` Phase 11 already established time-based conditions (a stored date, `today >= date`).
- **Events?** Yes — "if management changes capital-allocation policy" resolves true the moment a discrete event occurs, distinct from a continuously-checkable threshold.
- **Combinations?** Plausible, not confirmed as required — `Investigation-005` Phase 7 flagged this as possible without a confirmed example; neither `UX-008` nor `UX-009` gives a compound-predicate example. Not designed here.

**What does the stored object actually contain?** Given qualitative, date, event, and numeric-threshold conditions all coexist and share no single formal schema, the honest answer is: the stored content is fundamentally **free-text, investor/Atlas-authored natural language** (matching every UX-009 example verbatim: "Next quarterly earnings for enterprise AI infrastructure spending"), with an *optional* structured sub-shape for the subset of conditions mechanically evaluable today (a specific date; a metric+operator+threshold triple). This mirrors this codebase's own established pattern — `Decision.investment_case.reason` and `DecisionContext.situation`/`alternatives_considered` are also free text — natural language first, structure only where mechanically necessary, never a rigid schema forced on day one. **The predicate is not "always boolean" as a storage type — it is always free-text as stored content, and boolean only as an evaluation outcome, once (if) an evaluation mechanism exists for that specific condition.**

---

## Phase 3 — Condition vs. Evaluation

| Category | What it is |
|---|---|
| **Permanently stored** | The `CaseCondition`'s own definition — text/structure, authored once, immutable (amendments produce new revisions, per Phase 11, never in-place edits) |
| **Repeatedly computed** | The evaluation act itself — checking the condition against current data |
| **Historical** | Only *meaningful* evaluation outcomes — specifically, transitions (was not-met, now met) |
| **Transient** | Every non-transition check ("still not met, checked again today") — no permanent trace needed |

Storing every single evaluation check (e.g., a daily "not yet" for a 90-day time condition, 89 times before it finally becomes true) would be enormous, valueless noise. **Only the delta matters** — the same underlying philosophy `atlas/monitoring`'s own `compare()` function already expresses (`Investigation-005` Phase 2: "report signals that changed"), even though that specific module's own data is fabricated. The *pattern* — report only what changed — is sound and reusable independent of that module's own defects.

---

## Phase 4 — Condition vs. Event vs. Alert vs. Notification vs. Review Trigger vs. Reconsideration

Directly testing whether any of these should be the *same* object:

| Concept | Persisted object? | Same as another? |
|---|---|---|
| Condition | Yes — the definition (Phase 3) | — |
| Evaluation | No — transient computation (Phase 3) | Not the same as Condition (one permanent, one usually transient) |
| Satisfied condition | Yes, as a meaningful transition | **Same object as "Detected event"** — both describe "the moment the predicate became true," from two angles. No reason found to keep them separate. |
| Detected event | Yes | Same as "Satisfied condition," above |
| Alert | No | Presentation/delivery only (`Investigation-005` Phase 4/12, reconfirmed) |
| Notification | No | Same as Alert |
| Review Trigger | No | A derived union across sources (`Investigation-005` Phase 5/20, reconfirmed, not re-derived) |
| Reconsideration | No | A workflow (`Investigation-004`, reconfirmed) |

**Only two new persisted objects survive this test:** the `CaseCondition` definition, and a single, unified evaluation-transition record (merging "Satisfied condition" and "Detected event," which this phase finds are the same fact described two ways). Everything else in the chain remains process, presentation, or workflow — sharpening, not merely restating, `Investigation-005`'s own conclusion.

---

## Phase 5 — Monitoring vs. Invalidation

Testing the five offered framings directly:

- **Same ontology?** No, too strong a claim of identity in meaning.
- **Different ontology?** No, too strong the other way — they share every structural property (definition shape, evaluation mechanism, scope, authorship).
- **Different roles?** **Yes — the precise answer**, matching `Investigation-005` Phase 7 exactly: Monitoring is passive watch with no inherent consequence; Invalidation is a watch specifically *designated* to warrant re-entry into the Decision Workspace when met. The difference is a role/purpose tag on an otherwise-identical object.
- **Different severity?** Close but imprecise — `Investigation-005` already flagged this nuance ("more precise reduction is `+ a designated trigger-role`"), reconfirmed here rather than accepted at face value.
- **Different lifecycle?** Not evidenced — nothing suggests a different state-machine shape (Phase 10 finds both share the identical shape).

**Exact relationship: Invalidation Condition = Monitoring Condition + a role designation.** Same object type, differentiated by a field, not a separate aggregate.

---

## Phase 6 — Time Conditions

Directly reconfirming and sharpening `Investigation-005` Phase 11: one object shape (`CaseCondition`, whose stored content is free text per Phase 2, optionally with a structured date sub-field), but **not** one evaluation mechanism — calendar comparison (trivial, no live data) and live-data threshold comparison (genuinely needs infrastructure `atlas/monitoring` does not currently provide, per `Investigation-005` Phase 2) remain different processes. `_is_thesis_stale`'s own already-shipped, fixed 90-day threshold (found fresh in `Investigation-005`) remains the concrete, working precedent that these two mechanisms already coexist distinctly in this codebase.

---

## Phase 7 — Assumptions

Directly reconfirming `Investigation-005` Phase 8: the grouping is presentational, not a formal dependency chain. A `CaseCondition` can exist without a named assumption (UX-009's own example is a general informational watch-point); an assumption can exist without a `CaseCondition` (UX-009 Section 4 presents assumptions with no monitoring apparatus at all).

**One refinement this investigation adds:** since Phase 1 established a `CaseCondition` is partly "a decision dependency" in nature, an assumption is really *one particular kind of thing a CaseCondition can be about* — "this assumption remaining true" is itself expressible as a `CaseCondition`'s own free-text content. This raises a real possible future economy: if Assumption confirmation (the still-unresolved gap named in `Architecture-Resolution-Sprint-1.md` §7 and `Investigation-003`/`004`) is ever built, it could plausibly be modeled as a specific *kind* of `CaseCondition` rather than a wholly separate object — fewer total concepts. **This is named as an implication, not decided** — deciding it would reopen a question this investigation series has consistently left open, and doing so here would exceed this investigation's own scope.

---

## Phase 8 — Ownership

| Part | Owner |
|---|---|
| Condition definition | Shared — Atlas-proposed, investor-adjustable (`Investigation-005` Phase 6/15) |
| Threshold | Shared, same |
| Review date | Shared — Atlas may propose (UX-009 §11), investor confirms/adjusts |
| Meaning (what it implies for the thesis) | Investor-anchored, ultimately (`Investigation-005` Phase 7) |
| Evaluation (the act of checking) | System/Atlas — pure computation |
| Detected event | System-derived |
| Alert | System-derived, presentation-only |
| Investor response | Investor, exclusively |
| Atlas proposal | Atlas-originated |
| Investor confirmation | Investor — and precisely: an **unedited acceptance** of Atlas's proposed condition text should be labeled "Atlas Suggested / User Accepted," per `ADR-002` C-02's own already-established model, never silently relabeled "User Authored." This directly reuses C-02's own authorship-transfer discipline rather than inventing a new rule for this object — a sharper application than `Investigation-005` Phase 15 spelled out. |

---

## Phase 9 — Scope

Testing which scope survives contradiction, reapplying `Investigation-005` Phase 13 precisely:

| Scope | Survives? | Why |
|---|---|---|
| Decision | As an **optional** reference only | Decision-only scoping already found too narrow (`Investigation-005` Phase 9/13); `decision_id` survives as an optional back-reference, following the `observation_id` precedent |
| **Case** | **Yes — the primary scope** | Watchlist securities have Cases, not Decisions (`Investigation-005` Phase 13's decisive finding) |
| Portfolio | **No** | `Investigation-005` Phase 19 explicitly, honestly left Portfolio-scoped conditions unresolved — `CaseCondition` does not cover them. This investigation's own instruction not to introduce architecture beyond what's unavoidable means this gap is preserved, not silently closed here. |
| Security | Only via Case | A Security is already represented by a real `Case` (`Investigation-001`) — not a distinct scope of its own |
| Watchlist | Only via Case | Same reasoning — a Watchlist security already has a real Case |

---

## Phase 10 — Lifecycle

Testing the offered eight-item list against the event-sourced shape already converging across this investigation:

| Item | Actually is | Why |
|---|---|---|
| Draft | **Not a state of `CaseCondition` at all** | If a condition originates from `Investigation-003`'s own Draft object, "Draft" is a state of *that different, upstream object* — `CaseCondition` itself only comes into being already-Confirmed, by the same "a draft isn't a Decision" logic `Investigation-003` Phase 1 established, reapplied by direct analogy |
| Confirmed | The **creation event**, not a separate state | The first, definitional entry in the event stream |
| Active | A **projection**, not a stored state | Derived: "is there any later terminal event for this condition?" — computed, never persisted |
| Satisfied | An **event** (Phase 4's unified transition record) | Not a mutated flag on the condition itself |
| Invalidated | **Not a distinct state — a naming collision to disambiguate** | UX-009 never uses "invalidated" as a lifecycle state; it names the *role* (Invalidation Condition) and describes the outcome as being "reached." "Invalidated" is simply "Satisfied," specifically on a condition carrying the Invalidation role (Phase 5) — not a fourth concept |
| Superseded | An **event** | The investor (or Atlas, proposing) replaces the condition's own text/threshold — a new revision event, per Phase 11 |
| Retired | An **event**, distinct from Superseded | "Stop watching this, no replacement" — a real, separate terminal event |
| Deleted | **Unresolved, genuinely** | Per this session's uniform immutability principle, nothing is physically deleted from an append-only stream; a "Deleted" entry, if it exists, is itself just another event ("investor requested removal from view"). This is the *same* open question `Investigation-003` Phase 12 already left unresolved for Drafts (edit vs. abandon vs. delete) — recurring, not newly resolved here either. |

**Conclusion:** only two-to-three of the eight listed items are genuinely distinct events worth persisting (Superseded, Retired, possibly Deleted); Satisfied/Invalidated collapse into one event type tagged by role; Confirmed is simply the creation event; Active is a pure projection; Draft does not belong to `CaseCondition`'s own lifecycle at all. **This is materially leaner than an eight-state model.**

---

## Phase 11 — Versioning

**When the investor changes a condition: edit, new version, new object, or new event?**

Not "edit" — a first mutable-row precedent break, the same objection raised in every prior investigation. Not strictly "new object" — a fully disconnected replacement would lose the continuity UX-009's own "amendments versioned... visible in the decision history" explicitly requires (the *same* condition's own history must remain traceable). **A new, immutable revision event, referencing the same, stable `CaseCondition` identity** — directly matching `SecurityConfirmationEvent`'s own proven shape (a stable anchor identity, multiple event rows over time, "current state" always the latest event) — this is the precise answer, not "new version" loosely construed, but specifically an event within the same condition's own stream.

---

## Phase 12 — Evaluation History

**Belongs to:** an event stream — specifically **the same stream already established in Phase 11**, as a different event type, not a separate mechanism. A `CaseConditionEvent` with `event_type: "revised" | "evaluated_satisfied" | "superseded" | "retired"`, all referencing the same stable `condition_id`, directly generalizes `SecurityConfirmationEvent`'s own `event_type: "confirmed" | "revoked"` shape. **Evaluation history and revision history are the same mechanism, not two** — a real economy this phase's own analysis surfaces, since the investigation's own phase structure (10, 11, 12 as separate questions) might otherwise suggest they need separate treatment.

---

## Phase 13 — Atlas Memory

| Surface | Relationship |
|---|---|
| Decision | `CaseCondition` optionally references `decision_id` — a sibling, not a component |
| Decision Timeline (ATLAS-004) | **Not currently included** — ATLAS-004's own dependency list names only Decision/Outcome/Evaluation/Learning repositories; extending it to include `CaseCondition` is a real, disclosed future integration point, not something to assume already works |
| Decision Memory (`DE-005`'s term) | `CaseCondition`'s own Satisfied/Invalidated events are plausible new input to that synthesis, but `DE-005` §3's own grounding section names only DecisionRecord/OutcomeRecord/TradeLogEntry today — a disclosed future extension, not current fact |
| Knowledge (`KnowledgeReference`) | No relationship — disjoint shape, confirmed repeatedly |
| Reasoning (`ReasoningTrace`) | No relationship, same reasoning |
| **Evaluation (Core Loop)** | **A genuine naming collision, flagged explicitly:** "Condition Evaluation" (this investigation's own term) and the Core Loop's `Evaluation` aggregate ("the investor's assessment of an Outcome") are different concepts sharing one English word — the same category of naming-overload risk `Investigation-002` already flagged for "Reflection." Any future implementation must not let these two collapse into one casually-shortened term. |
| Learning | No relationship — a different, terminal Core Loop node |
| Reflection | No relationship — `ReflectionResponse` is occasioned by Pattern/Coaching; `CaseCondition` is occasioned by nothing (Phase 1's "unoccasioned" framing) — disjoint origin stories |
| Outcome | No relationship — backward-looking (what happened) vs. `CaseCondition`'s forward-looking nature, the same directional distinction established repeatedly for `Observation` |

---

## Phase 14 — Daily Brief

| Candidate | Consume? | Why |
|---|---|---|
| Conditions (definitions) | Know, not display | Too granular — matches the narrow-projection principle, reused |
| Evaluations (transient checks) | **Never** | Explicitly transient/non-persisted per Phase 3 — nothing exists to consume |
| Detected Events (unified Satisfied/Detected, Phase 4) | **Yes, directly** | The actual, real signal worth surfacing |
| Alerts | No | Not a persisted object (Phase 4) — Daily Brief's own presentation of a Detected Event *is* the alert |
| Review Triggers | No, computed not consumed | A union Daily Brief itself computes from Detected Events + overdue conditions + Change Intelligence, not a stored object |
| **Projections** | **Yes — this is the correct boundary** | A computed "current state" summary, the same current-state half of Model D (Phase 16), never raw event-stream data |

**Correct boundary, precisely: Daily Brief consumes a narrow, derived projection over Detected Events — never raw Condition definitions, never raw per-check Evaluations, never a separately-stored Alert or Review Trigger object, since none of those exist as anything but presentation or derivation over the first two.**

---

## Phase 15 — Existing Architecture

| Object | Satisfies the ontology? | Why not |
|---|---|---|
| `Decision` | No | Immutable, no predicate/evaluation shape |
| `DecisionContext` | No | Free-text, captured once, no ongoing evaluation lifecycle |
| `ReflectionResponse` | No | Occasioned by Pattern/Coaching, not by a predicate |
| `DecisionDraft` (proposed) | No, but adjacent | May seed a `CaseCondition`'s initial content (Phase 9/10); has no predicate/evaluation shape of its own |
| Security Confirmation | No, but this is the **direct structural template**, not a reusable object | Its own domain content (security identity) is unrelated; its event-sourcing mechanism is exactly what `CaseConditionEvent` should copy — the third reuse of this pattern in this series |
| `Evaluation` (Core Loop) | No | Outcome-anchored, backward-looking — wrong direction (Phase 13's naming-collision finding) |
| `Learning` | No | Terminal Core Loop node, unrelated |
| `Observation` | No | Retrospective — wrong temporal direction, confirmed for a **fourth** time across this series |
| `KnowledgeReference` / `ReasoningTrace` | No | Reference-based, not predicate-based, confirmed repeatedly |
| `Judgment` | No | Case-scoped settled characterization, no `decision_id` anchor, no evaluation lifecycle |
| `Outcome` | No | Backward-looking fact of what happened |

**No existing object satisfies the ontology** — confirming, not reopening, `Investigation-005`'s own settled premise.

---

## Phase 16 — Alternative Models

| Model | Verdict |
|---|---|
| **A — Mutable Condition** | Rejected — first mutable-row precedent break; contradicts Security Confirmation's own deliberate move away from this; real post-hoc rationalization risk |
| **B — Immutable Condition + revisions** | Strong, but incomplete alone — matches Phase 11 for revisions, but doesn't by itself specify how evaluation history (Phase 12) is handled without a separate mechanism |
| **C — Event sourced** | Correct philosophy (matches Model C from `Investigation-003`/`005`), but as named doesn't specify *what* the events represent — the general pattern, not the specific design |
| **D — Condition + Event stream** | **The precise, complete answer** — one stable `CaseCondition` identity + one unified `CaseConditionEvent` stream covering both revisions and evaluation transitions as different `event_type` values, exactly matching `SecurityConfirmationEvent`'s own shape generalized. Synthesizes B and C's partial answers into what Phases 3/4/10/11/12 already converged on independently. |
| **E — Fully derived** | A real, viable minimal option, tested honestly — conditions live only as free text inside `Decision.reason`/`DecisionContext`, no structured tracking, no evaluation, Daily Brief can only say "go re-read your own notes." Costs nothing, adds no ontology, but forecloses everything Phases 4/12/14 found valuable. A genuine trade-off, not a strawman. |
| **F — Separate Monitoring aggregate** | Rejected — fails for the same reason `Investigation-005` Phase 18's own Option C failed: Phase 5 already found Monitoring and Invalidation are the *same object*, differentiated by role, not by a structural split |

---

## Phase 17 — Consistency Test

Challenging Option D, documenting rather than resolving:

- **vs. Decision:** no contradiction — untouched, only optionally referenced (Phase 9).
- **vs. Draft:** no contradiction, a positive integration point — Draft content may seed a `CaseCondition`'s initial definition at commit time.
- **vs. Evaluation (Core Loop):** a real, disclosed **naming** risk, not a structural contradiction — the same word used for two unrelated concepts (Phase 13); must be disambiguated in any future implementation's own naming.
- **vs. Learning:** no contradiction — unrelated.
- **vs. Reflection:** no contradiction — disjoint origin stories (Phase 13).
- **vs. Knowledge:** no contradiction — disjoint shape, confirmed repeatedly.
- **vs. Portfolio:** **a genuine, disclosed gap, restated from `Investigation-005` and deliberately not resolved here**, per this investigation's own scope discipline (Phase 9).
- **vs. Watchlist:** consistent — covered via Case.
- **vs. Daily Brief:** consistent, given the Phase 14 projection boundary is respected.
- **vs. Atlas Memory:** consistent, but with two disclosed, not-yet-realized integration points (Decision Timeline extension; Decision Memory synthesis extension, Phase 13) — compatible with eventually feeding both, doesn't do so today, and this investigation does not design that integration.
- **vs. future collaboration:** the same inherited, disclosed Case-scoping ambiguity, now named a **fourth** time across this series (`Investigation-003`, `004`, `005`, now `006`) — not a new finding, the same limitation recurring from the same root cause (the single-investor assumption) every time a Case-scoped object is proposed.
- **vs. imported Decisions:** no contradiction — the optional `decision_id` reference accommodates every `DecisionSource` value with zero special-casing, per the repeatedly-reused `observation_id` precedent.
- **vs. provider synchronization:** **a genuinely new question, not previously tested in this series.** If a future automated evaluation mechanism is ever driven by an external data provider feed, does a provider-triggered evaluation event carry a different authorship/trust shape than an Atlas-computed one? No evidence was gathered for this investigation to answer it — flagged as unresolved, not glossed over.

---

## Phase 18 — Final Decision

**`CASE_CONDITION_WITH_EVENT_STREAM`**

Justified purely from this investigation's own findings: Phases 3, 4, 10, 11, and 12 independently converged on the identical shape — a stable `CaseCondition` definition plus one unified `CaseConditionEvent` stream — without this investigation assuming that answer in advance. Phase 15 confirms no existing object satisfies the ontology, consistent with `Investigation-005`'s premise. Phase 16 shows the alternative models either fail on immutability grounds (A), are incomplete on their own (B, C), or trade away real, evidenced value for minimalism (E, a legitimate but not preferred option) or introduce an unjustified structural split (F).

---

## Phase 19 — ADR Candidate (Outline Only)

**Problem:** `CaseCondition` is established as necessary (`Investigation-005`), but its precise shape, lifecycle, and persistence model were undefined.

**Context:** No existing object (`Decision`, `DecisionContext`, `ReflectionResponse`, `Evaluation`, `Observation`, `Judgment`, `KnowledgeReference`, `ReasoningTrace`, `Outcome`) satisfies the ontology (Phase 15). `SecurityConfirmationEvent` provides a proven, already-shipped structural template for exactly this shape of problem, reused for a third time in this document series.

**Decision:** `CaseCondition` is a stable, Case-scoped identity (optionally referencing `decision_id`) representing a single predicate's definition — free-text by default, with optional structured sub-fields for mechanically-evaluable date/threshold conditions. Its lifecycle is expressed entirely through a single, unified `CaseConditionEvent` stream, never through mutation. Monitoring and Invalidation are the same object, distinguished by a role field, not separate aggregates.

**Invariants (illustrative, not binding — no schema decided here):**
- `CaseCondition` itself is created once and never mutated; every subsequent change is a new `CaseConditionEvent`.
- One event stream, one condition identity, multiple event types (`revised`, `evaluated_satisfied`, `superseded`, `retired`), directly generalizing `SecurityConfirmationEvent`'s own `confirmed`/`revoked` shape.
- Only meaningful evaluation transitions are persisted as events; routine "still not met" checks are never stored (Phase 3).
- Scope is Case-first, never Portfolio (a distinct, unsolved sibling concept, Phase 9).
- Unedited acceptance of an Atlas-proposed condition follows `ADR-002` C-02's own authorship model exactly (Phase 8) — never silently relabeled as user-authored.

**Consequences:** No existing object requires modification. Daily Brief gains one clean, narrow projection source (Phase 14). Decision Timeline and Decision Memory each gain a disclosed, but not yet designed, future integration point (Phase 13). The naming collision between "Condition Evaluation" and the Core Loop's own `Evaluation` must be actively managed in any future implementation's naming choices (Phase 13/17).

**Rejected Alternatives:** A (mutable — breaks immutability, the precedent already abandoned once by Security Confirmation); B and C alone (each correct but incomplete without the other — synthesized into D); E (fully derived — a real, legitimate minimal option, not chosen because it forecloses meaningful-transition detection and real Daily Brief signal, an evidenced cost, not a hypothetical one); F (separate Monitoring aggregate — an unjustified structural split given Phase 5's role-not-kind finding).

**Migration/Compatibility:** None required to any existing object. Fully additive.

**Open Questions** (carried forward, not resolved here):

1. Should `Assumption` confirmation ultimately be modeled as a specific kind of `CaseCondition`, given the structural overlap Phase 7 surfaces? Not decided — would reopen a question left open in `Architecture-Resolution-Sprint-1.md` and `Investigation-003`/`004`.
2. What happens to a "Deleted" `CaseCondition` — is it a genuine event type, or does "Retired" already cover this case? Genuinely unresolved (Phase 10), the same open question `Investigation-003` Phase 12 already left open for Drafts, recurring rather than newly resolved.
3. How, precisely, should Decision Timeline (ATLAS-004) and Decision Memory (`DE-005`) be extended to consume `CaseCondition` events, given neither currently does? (Phase 13)
4. Does provider-synchronized automated evaluation need a distinct authorship/trust model from Atlas-computed evaluation? No evidence gathered this investigation to answer it (Phase 17) — a real gap for a future investigation.
5. Portfolio-scoped conditions remain entirely unaddressed by `CaseCondition` — restated, not resolved, consistent with `Investigation-005`'s own disclosed limitation (Phase 9/17).

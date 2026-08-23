# ADR Investigation 1 — Decision vs. DecisionContext

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Scope:** Exactly one question — *what is `DecisionContext`?* — answered from the current implementation and governing documents, read fresh for this investigation: `Decision-Workspace-Architecture-Resolution-Sprint-1.md`, `Decision-Workspace-Gap-Analysis.md`, `DE-005`, `DE-006`, `UX-008`, `UX-009`, `UX-012`, `ADR-002`, the `Decision`/`DecisionContext`/`Outcome`/`Case` domain entities, `capture_decision.py`, `capture_decision_context.py`, both repositories, and both persistence tables.

---

## Phase 1 — Decision Ontology

**What is a Decision?** Per its own docstring: "the smallest meaningful learning unit in Atlas: a single investment decision, preserved exactly as it was reasoned at the time it was made." It is not a plan, not a trade, not a belief in progress — it is a completed, dated act of commitment.

**Essential information** (every field on the frozen `Decision` dataclass, all required except `source` and `observation_id`): `id`, `case_id`, `user_id`, `decision_type` (`BUY|SELL|HOLD|WATCH|PASS`), `subject` (the ticker/company the decision concerns), `investment_case.reason` (free text — the primary, investor-stated justification), `confidence` (the investor's own 0–100 self-report — "Atlas stores this. It does not interpret it."), `decided_at` (when the investor says it happened, normalized to UTC), `recorded_at` (when Atlas captured it, always Atlas's own clock), `source` (`Manual|Import|BrokerSync|API`), `observation_id` (optional, same-Case anchor).

**What is intentionally excluded:** anything with a lifecycle or status; anything Atlas-computed or interpretive (Confidence is stored, never interpreted); assumptions; monitoring or invalidation conditions; an implementation plan; a review plan; alternatives considered; challenge acknowledgment; any circumstantial detail beyond the single `reason` field. `Decision` is deliberately the *minimum* that makes a commitment legible, not the *maximum* that could be said about it.

**Why immutable:** "There is no update. A changed opinion is a new Decision." This is a stated epistemic-integrity choice, not an implementation convenience — it directly serves `UX-008` §14's "Preventing Post-Hoc Rationalization": a Decision that could be edited later could be quietly rewritten to match a since-known outcome, destroying the very record the Decision Workspace exists to preserve.

**Invariants:** `id`, `case_id`, `decision_type`, `subject`, `investment_case`, `confidence`, `decided_at`, `recorded_at` are all non-nullable; `decided_at` must be timezone-aware; `Subject.value` and `InvestmentCase.reason` must be non-empty (self-validating value objects); `Confidence.value` must be an integer in `[0, 100]`. No repository method updates or deletes a `Decision` — `capture_decision.py` only ever calls `.add()`.

---

## Phase 2 — DecisionContext Ontology

**What belongs inside it:** `situation` (required — "the relevant circumstances the investor believed mattered at decision time"), `portfolio_relevance` (optional, free text), `capital_considerations` (optional, free text), `alternatives_considered` (a tuple of investor-authored strings, may be empty), `uncertainties` (a tuple of investor-authored strings, may be empty), `captured_at` (investor-supplied, preserved exactly as given — unlike `Decision.decided_at`, this is *not* renormalized to UTC), `recorded_at` (Atlas's own clock), `context_id`, `decision_id` (the sole reference out of this aggregate).

**Why separate from Decision**, in its own words: "DecisionContext is a point-in-time record of the circumstances surrounding an existing Decision — not a live view of the current portfolio, not market data, not a later reflection... Decision remains stable and minimal, context may be captured later, and neither aggregate can rewrite the other's history." This is a deliberate minimalism-versus-richness split: `Decision` stays valid and complete for every source (a broker-synced or imported decision has no narrative at all), while `DecisionContext` is where the optional, richer narrative goes for investors who choose to supply it.

**Invariants:** at most one `DecisionContext` per `Decision`, enforced twice — at the application layer (`DuplicateDecisionContextError`) and at the SQL layer (`decision_id` column has `unique=True`); the referenced `Decision` must already exist (`DecisionNotFoundError`) before a `DecisionContext` can be captured; `situation` must be non-empty; each item inside `alternatives_considered`/`uncertainties`, if present, must itself be non-empty. No repository method updates a `DecisionContext` — only `.add()` and `.get_by_decision_id()` exist.

**Does it describe the investor?** Yes, exclusively — every field is explicitly the investor's own account ("what the investor believed mattered," "the other options the investor weighed," "what the investor was unsure about"). Atlas contributes no content to `DecisionContext`, the identical pattern `ReflectionResponse` uses ("Atlas contributes no content to it, only the provenance snapshot of what the investor saw").

**Does it describe the situation?** Yes, literally — `situation: Situation` is its one required field.

**Does it describe the reasoning?** Partially, and only the *supplementary* half. `capital_considerations` and `portfolio_relevance` touch on why the decision made sense, but the *primary* reason already lives on `Decision.investment_case.reason`. `DecisionContext` never restates or replaces that field.

**Does it describe the decision?** No. It never touches `decision_type`, `confidence`, or the primary `reason`. It surrounds the decision without ever restating it.

---

## Phase 3 — Relationship

- **Part of Decision?** No — separate dataclass, separate table (`decision_contexts`, distinct `MetaData` from `decisions`), separate repository interface.
- **Attached to Decision?** Yes — its only foreign reference is `decision_id`, enforced unique (0..1 cardinality, never more).
- **Attached to Case?** No — confirmed directly from the table schema: `decision_contexts_table` has no `case_id` column at all. It reaches `Case` only transitively, through the `Decision` it belongs to.
- **Independent?** Only in the sense of being a separate, separately-persisted aggregate. Not independent in existence: it cannot be created before, or orphaned from, its `Decision` (enforced by the application service's own existence check).
- **Historical?** Yes — `captured_at` is preserved exactly as given, the same treatment this codebase already gives `Observation.observed_at` and `Question.raised_at`; it is a permanent record of a past moment, not a live view of anything.
- **Optional?** Yes — a `Decision` may have zero `DecisionContext` records; nothing requires every Decision to receive one.
- **Mandatory?** No.

**Conceptual relationship:**

```
Case
 └── owns ──▶ Decision  (required minimum: commitment, reason, confidence, timing)
                 └── (0..1) ──▶ DecisionContext  (optional: surrounding circumstance, investor-authored only)
```

`DecisionContext` is a satellite aggregate attached one level below `Case`, at the `Decision` it belongs to — never attached to `Case` directly, and never required.

---

## Phase 4 — Ownership

| Field | Owns the truth |
|---|---|
| `situation` | **Investor** — their own account of relevant circumstances |
| `portfolio_relevance` | **Investor** — their own qualitative read at the time, *not* Atlas's computed Portfolio Intelligence output, despite the field's name (flagged as a naming-clarity risk in Phase 9) |
| `capital_considerations` | **Investor** |
| `alternatives_considered` | **Investor** — what *they* weighed, not an Atlas-generated ranking |
| `uncertainties` | **Investor** — what *they* were unsure of, distinct from Atlas's own computed Risk findings elsewhere in the system |
| `captured_at` | **Investor** — their own account of timing, preserved exactly, unlike `Decision.decided_at` |
| `recorded_at` | **Atlas** — system clock |
| `context_id` | **Atlas** — generated identity |
| `decision_id` | **Decision** — a reference to an identity `DecisionContext` does not itself own |

No field is owned by **Case** or by **Portfolio**, despite one field's name. This is worth stating plainly: `portfolio_relevance` is investor-authored prose about what the investor thought mattered for the portfolio — never a computed value from Portfolio Intelligence, and never a live or derived fact.

---

## Phase 5 — Temporal Analysis

- **When is it created?** Strictly after its `Decision` — `CaptureDecisionContextService.capture()` raises `DecisionNotFoundError` if the referenced `Decision` does not already exist.
- **Can it exist before a Decision?** No — structurally prevented.
- **After?** Yes — this is the expected case, per its own docstring: "context may be captured later."
- **Without one?** A `Decision` can exist with zero `DecisionContext` records (0..1, not 1..1) — but a `DecisionContext` can never exist without exactly one `Decision`, since `decision_id` is required and validated.
- **Can it change?** No — no update method exists on `DecisionContextRepository`; only `add()` and `get_by_decision_id()`.
- **Should it?** No. Mutating `DecisionContext` would reintroduce exactly the post-hoc-rationalization risk `UX-008` §14 names for `Decision` itself, and would contradict `DecisionContext`'s own stated character — "a point-in-time record... not a later reflection" is definitionally not something that can be edited without becoming a different kind of object.
- **Does mutability violate anything?** Yes, two things: (1) it would break the uniform immutable-aggregate pattern this investigation confirmed across every one of the ten domain objects read for it (`Decision`, `Outcome`, `Case`, `Observation`, `Question`, `Conclusion`, `KnowledgeReference`, `ReasoningTrace`, `Judgment`, `ReflectionResponse` — none has an update path); (2) it would directly contradict `DecisionContext`'s own docstring characterization of itself.

---

## Phase 6 — Comparison Against UX-009

Every UX-009 section, classified as `Decision`, `DecisionContext`, `Neither`, `Both`, or `Unknown` (no redesign proposed — classification only):

| UX-009 section (item) | Classification | Why |
|---|---|---|
| 1. Current Conclusion | **Neither** | Sourced from Investment Case analysis, not from either aggregate |
| 2. Why a Decision Is Required | **Neither** | A detection/trigger fact, not stored on either |
| 3. Proposed Decision — decision type | **Decision** | `decision_type` is a `Decision` field |
| 3. Proposed Decision — user's stated decision text | **Decision** | Part of the commitment itself, not surrounding circumstance (subject to the Section-3 ownership conflict already flagged in `Architecture-Resolution-Sprint-1.md` §12, which this investigation does not reopen) |
| 4. Decision Rationale — primary reason | **Decision** | `investment_case.reason`, directly |
| 4. Decision Rationale — Atlas-generated summary | **Neither** | From analysis, not stored on either |
| 4. Decision Rationale — user-confirmed assumptions | **Unknown** | No field on either object today; `DecisionContext` is the more natural extension point *if* one were ever added, but none exists now |
| 4. Decision Rationale — material risks | **Neither** | From analysis |
| 5. Supporting Factors (all items) | **Neither** | From analysis; "portfolio alignment"/"historical consistency" would require new computation belonging to neither object |
| 6. Challenges — unresolved questions / conflicting evidence / missing info | **Neither** | From analysis |
| 6. Challenges — uncertain assumptions | **DecisionContext** | Matches `uncertainties` directly |
| 6. Challenges — behavioral context | **Neither** | Belongs to the separate, explicitly-deferred Reflection/Pattern lineage |
| 6. Challenges — per-item acknowledgment | **Unknown** | No field on either; shape-incompatible with `DecisionContext` (single free-text list, not a per-item timestamped record) — needs a new, small, separate object per `Architecture-Resolution-Sprint-1.md` §6 |
| 7. Opportunity Cost — subject's own summary | **Neither** | From analysis |
| 7. Opportunity Cost — Atlas-generated ranking | **Neither** | New computation, belongs to neither object |
| 7. Opportunity Cost — "no capital reallocated" fallback | **Neither** | Static text |
| 7. Opportunity Cost — investor's own alternatives considered | **DecisionContext** | Matches `alternatives_considered` directly |
| 8. Portfolio Consequences — current-state facts | **Neither** | From Portfolio Intelligence |
| 8. Portfolio Consequences — computed before/after | **Neither** | Portfolio Simulation, undefined anywhere, and not a fit for either object even if it existed (a computed projection, not a captured circumstance) |
| 8. Portfolio Consequences — investor's own qualitative note | **DecisionContext** | Matches `portfolio_relevance`/`capital_considerations` directly |
| 9. Assumptions (read-only) | **Neither** | From analysis |
| 9. Assumptions (user-confirmed) | **Unknown** | Same as Section 4's assumption sub-item |
| 9. Monitoring Conditions | **Neither** | Belongs to the separate `atlas/monitoring` system; wrong temporal shape for `DecisionContext` (point-in-time capture vs. ongoing watch) |
| 9. Invalidation Conditions | **Unknown, and specifically not DecisionContext** | Genuinely undesigned anywhere, and `DecisionContext`'s captured-once character is a poor fit regardless — an invalidation condition is a standing, forward-referenced threshold, not a snapshot of past circumstance |
| 10. Implementation Plan | **Neither** | Forward-looking intent; `DecisionContext` is backward/point-in-time, not a fit |
| 11. Review Plan | **Neither** | Same forward-looking-schedule shape mismatch as Monitoring |
| 12. Final Decision Card | **Both** (derivative) | Decision/Reason/Confidence sub-fields from `Decision`; Portfolio-impact's qualitative half from `DecisionContext`, if wired; Implementation/Review sub-fields remain `Neither`, inherited from Sections 10–11 |
| 13. Record Decision | **Both** | The recording event itself is `Decision`; a UI could additionally submit `DecisionContext` at the same moment, though the two are not required to be simultaneous (`DecisionContext` may be captured later) |

**Pattern:** every item this investigation classified `DecisionContext` is an investor-authored, captured-once, backward-or-present-tense account. Every item classified `Unknown` or `Neither` that involves user-supplied *ongoing* or *future-referenced* content (acknowledgment, confirmation, monitoring, invalidation, implementation, review) is `DecisionContext`-incompatible by its own captured-once nature, not merely unimplemented.

---

## Phase 7 — Comparison Against the Decision-Memory Family

| Object | Scope | Authorship | Shape | Overlap with DecisionContext |
|---|---|---|---|---|
| `ReasoningTrace` | `case_id` (Case-wide, not Decision-specific) | System-mediated (records that N accepted objects support the trace) | A `frozenset` of *typed references* to other Domain Objects | **None** — reference-based, not narrative; Case-scoped, not Decision-scoped |
| `KnowledgeReference` | `case_id` | System-mediated | Exactly one typed reference | **None** — same reasons |
| `Judgment` | `case_id`, with an *optional* reference to a subject object | Investor/Case-level characterization | A single `characterization` field, no `decision_id` at all | **Adjacent, not overlapping** — both can hold investor belief-content, but `Judgment` has no way to anchor to a specific `Decision`; it is a Case-wide settled characterization, not a per-decision circumstantial record |
| `ReflectionResponse` | `decision_id` (Decision-specific, like `DecisionContext`) | Investor-only, Atlas contributes no content | A single `response_text` plus a `ProvenanceSnapshot` of what prompted it | **Closest structural sibling, but not duplicative** — see below |

**`DecisionContext` vs. `ReflectionResponse`, specifically:** both are `decision_id`-anchored, investor-authored-only, immutable, and captured once. They differ in *when* and *why*: `DecisionContext` is captured at-or-near the moment of the `Decision` itself, unprompted by anything except the Decision Workspace flow. `ReflectionResponse` is explicitly "occasion-originated" from a later, separate Reflection session — its `ProvenanceSnapshot` exists specifically to record what pattern or coaching question prompted it, something `DecisionContext` has no equivalent of and does not need, since it isn't a response to anything — it *is* the original circumstance.

**No duplicated responsibility found.** `ReasoningTrace`/`KnowledgeReference` are generic, Case-wide, reference-based epistemic primitives with no shape or scope overlap with `DecisionContext`'s Decision-specific free narrative. `Judgment` is adjacent but structurally unable to anchor to a specific Decision. `ReflectionResponse` shares `DecisionContext`'s shape but not its temporal purpose.

---

## Phase 8 — Alternatives

### Option A — DecisionContext remains separate

- **Advantages:** matches an already-built, already-tested, internally-consistent pattern; preserves `Decision`'s required minimalism (works for imported/broker-synced decisions with no narrative at all); clean, doubly-enforced 0..1 invariant; zero migration cost.
- **Disadvantages:** currently unwired to Alpha (a wiring problem, not an architecture problem); its scope, as it exists today, does not cover Monitoring/Invalidation/Acknowledgment/Implementation Plan — those need something else regardless of what happens to `DecisionContext`.
- **Ontology consequences:** none — status quo, already internally coherent.
- **Migration consequences:** none.
- **Future extensibility:** good — new *optional* fields could be added without breaking existing rows, following the same additive pattern this codebase already used for `Decision.observation_id`.

### Option B — Merge into Decision

- **Advantages:** one object instead of two to read.
- **Disadvantages:** forces every `Decision` — including imported and broker-synced ones with no narrative — to either populate meaningless-empty rich fields or accept a permanently bloated schema; directly contradicts `DecisionContext`'s own stated design rationale ("Decision remains stable and minimal, context may be captured later"); breaks the SQL-enforced 1:1-optional cardinality; reverses a pattern this codebase applies consistently across all eleven domain objects read for this investigation and the prior sprint (none of them merge a required-minimum aggregate with an optional-rich companion).
- **Ontology consequences:** severe — collapses "the commitment" and "the circumstances surrounding the commitment" into one concept, the exact distinction `DecisionContext`'s docstring exists to preserve.
- **Migration consequences:** a real schema migration (merging two tables, or adding nullable columns to `decisions`), plus every consumer of the currently-separate repository interface would need updating.
- **Future extensibility:** worse — a single wide table accretes fields faster and makes future "is this about the decision or the context around it" questions harder to answer.

### Option C — Split DecisionContext further

- **Advantages:** could isolate sub-concerns (`alternatives_considered` vs. `uncertainties` vs. `portfolio_relevance`/`capital_considerations`) if they ever needed independent lifecycles or query patterns.
- **Disadvantages:** no evidence found, anywhere in this investigation, that they currently need this — all four are captured together, by the same use case, at the same moment, with identical cardinality and identical (investor-only) authorship.
- **Ontology consequences:** neutral-to-negative — more objects without a corresponding gain in clarity.
- **Migration consequences:** a real schema migration, and the one existing call site would need updating.
- **Future extensibility:** marginally better for a hypothetical future need, at a real, unjustified present cost.

### Option D — DecisionContext should disappear

- **Advantages:** none identified.
- **Disadvantages:** deletes a working, tested, precisely-scoped capability that already solves the investor-authored half of three UX-009 sections (6, 7, 8); Alpha would then have to invent a replacement of an identical shape — strictly worse than reusing what exists.
- **Ontology consequences:** none positive — removing a correctly-scoped object does not simplify anything; it deletes a distinction both `UX-008` §14 and `DecisionContext`'s own docstring independently justify keeping.
- **Migration consequences:** dropping a table and its application/persistence layers for no offsetting benefit.
- **Future extensibility:** worse — nothing gained, a working capability lost.

---

## Phase 9 — Consistency Test

Actively attempting to break Option A (keep `DecisionContext` unchanged), against every named neighbor:

- **vs. `Decision`:** a real, disclosed risk — `Decision.investment_case.reason` (required) and `DecisionContext.situation`/`capital_considerations` (optional, richer) both hold investor free text about *why*. Nothing in the ontology stops an investor from putting their actual primary reasoning into `DecisionContext` instead of `Decision.reason`, which would silently defeat `Decision`'s own "universal minimum, required for every decision" design intent, since `DecisionContext` is optional and could simply never be checked. **This is a UI/copy-discipline risk, not an architecture flaw** — the objects themselves are correctly distinct — but it is real and worth carrying forward.
- **vs. `Outcome`:** no contradiction — disjoint fields, disjoint purpose (what happened vs. what surrounded the decision), no shared table.
- **vs. `Case`:** no contradiction — `DecisionContext` deliberately has no `case_id` column, avoiding any dual-ownership ambiguity; it reaches `Case` only transitively through `Decision`.
- **vs. Reflection (`ReflectionResponse`):** a real, disclosed risk — once Reflection is un-deferred, an investor could plausibly encounter both `DecisionContext.uncertainties` (at decision time) and a later `ReflectionResponse` touching similar uncertainty-adjacent content, without a UI that clearly distinguishes "what you weren't sure of when you decided" from "your later reflection on a recognized pattern." **Again a labeling/sequencing risk for a future implementation, not a present ontology conflict**, since the two objects' actual temporal scope is genuinely different.
- **vs. Knowledge/Reasoning:** no contradiction — confirmed disjoint shape and scope in Phase 7.
- **vs. Trade:** no contradiction — entirely separate table, entirely separate purpose, no shared fields.
- **vs. Daily Brief:** no contradiction found — Daily Brief does not reference `DecisionContext` today; no conflicting assumption exists to surface.
- **vs. Atlas Memory (the general concept):** no contradiction — `DecisionContext` is already named as one component of "Atlas Memory" in `Architecture-Resolution-Sprint-1.md` §15.
- **vs. Portfolio:** a real, disclosed risk — the field name `portfolio_relevance` itself invites a future implementer to assume it holds Atlas-computed Portfolio Intelligence data. It does not, and never has — it holds the investor's own account. This is a naming-clarity risk, not a data-model error.

**Three risks found, none fatal, all documented rather than hidden:** (1) `Decision.reason` vs. `DecisionContext.situation`/`capital_considerations` boundary discipline; (2) `DecisionContext.uncertainties` vs. future `ReflectionResponse` content, once Reflection is un-deferred; (3) `portfolio_relevance`'s name inviting a false assumption of Atlas authorship. All three are implementation- and copy-discipline risks for whichever design phase follows this one — none of them is a reason to change the architecture itself.

---

## Phase 10 — Final Decision

### Executive Summary

`DecisionContext` is not a duplicate, not a redundant object, and not an architecturally incorrect model. It is a correctly-scoped, deliberately minimal companion aggregate: the home for investor-authored circumstantial narrative that `Decision`'s own required-minimalism was explicitly designed to exclude. It is unwired to Alpha, not incorrectly designed — a wiring problem, addressed by the prior sprint's own §3 finding, not an ontology problem, which is what this investigation was asked to check. It is not, and should not become, a home for Atlas-computed content, per-item acknowledgment, or anything with a forward-looking or ongoing lifecycle (Monitoring, Invalidation, Review, Implementation Plan) — its point-in-time, captured-once character is structurally incompatible with those, independent of anything about Alpha's current scope.

### Evidence

- `DecisionContext`'s own docstring states its separation rationale directly and specifically: minimal-stable `Decision` vs. optional-rich context, neither able to rewrite the other's history.
- Both the application layer (`DuplicateDecisionContextError`, `DecisionNotFoundError`) and the SQL schema (`unique=True` on `decision_id`) independently enforce the same 0..1, Decision-must-precede-Context invariant — a doubly-confirmed, deliberate design, not an accident of one layer.
- Every field is investor-authored; none is Atlas-computed — confirmed field-by-field in Phase 4.
- Every UX-009 item this investigation could place inside `DecisionContext` (Phase 6) shares the same shape: investor-authored, backward-or-present-tense, captured once. Every item that needed acknowledgment, confirmation, monitoring, invalidation, implementation, or review semantics was independently found `DecisionContext`-incompatible, for the same underlying reason each time (Phase 6), not five different reasons.
- No overlap or duplicated responsibility was found against `ReasoningTrace`, `KnowledgeReference`, `Judgment`, or `ReflectionResponse` (Phase 7) — `DecisionContext` occupies a genuinely distinct niche even among its closest siblings.
- The consistency test (Phase 9) found three real risks, none of which are architectural — all three are UI/copy-discipline questions for a later implementation phase.

### Alternatives Considered

| Option | Verdict |
|---|---|
| A — Keep separate | Selected |
| B — Merge into Decision | Rejected — contradicts `DecisionContext`'s own stated rationale, forces schema bloat on every Decision, reverses this codebase's consistent small-aggregate pattern |
| C — Split further | Rejected — no evidence of a present need; real migration cost for a hypothetical future benefit |
| D — Remove | Rejected — deletes a working, correctly-scoped, already-tested capability for no offsetting benefit |

### Decision

**`KEEP_DECISION_CONTEXT`**

Its current scope — `situation`, `portfolio_relevance`, `capital_considerations`, `alternatives_considered`, `uncertainties` — is correct and sufficient for what it should own. Nothing found in this investigation warrants adding or removing a field. The gaps this investigation confirmed `DecisionContext` cannot close (per-item acknowledgment, assumption confirmation, monitoring, invalidation, implementation plan, review plan) require new, separate objects, exactly as `Architecture-Resolution-Sprint-1.md` §§6–9 already concluded — this investigation independently arrives at the same boundary from first-principles ontology analysis, which corroborates rather than merely repeats that prior finding.

---

## ADR Candidate (Outline Only)

**Problem:** UX-009 assumes richer decision-time context than the minimal `Decision` aggregate alone holds. Is `DecisionContext` the architecturally correct home for that richer context, or does the domain model need to change?

**Context:** `DecisionContext` already exists, fully persisted and application-layer-supported, but is called from nowhere in `atlas/alpha` — it was built, correctly scoped, and never wired to the one product surface (Alpha's Investment Case) that would use it.

**Decision:** Keep `DecisionContext` unchanged in scope and shape. Treat it as the sole correct home for investor-authored, decision-time, captured-once circumstantial narrative — never for Atlas-computed content, never for anything with a post-recording lifecycle. Any future wiring work should expose it via a new API endpoint over the existing, unmodified `capture_decision_context.py`/`DecisionContextRepository` — an implementation-design question explicitly out of scope for this investigation.

**Consequences:** No migration required. No field changes required. Three implementation-discipline risks must be carried into whatever design phase follows: (1) clear separation, in any future UI copy, between `Decision.reason` and `DecisionContext.situation`/`capital_considerations`; (2) clear separation, once Reflection is un-deferred, between `DecisionContext.uncertainties` and any later `ReflectionResponse` content; (3) a naming-clarity concern with `portfolio_relevance`, which could be misread as Atlas-computed — worth a future, separate, small documentation (or possibly renaming) decision, not decided here.

**Open Questions** (carried forward, not resolved here):

1. Should `portfolio_relevance` eventually be renamed, or is a documentation clarification sufficient? Not decided — out of scope for an ontology-only investigation.
2. Where should assumption-confirmation (UX-009 Sections 4 and 9) ultimately live — a `DecisionContext` field extension, or its own object? This investigation found `DecisionContext` the more *natural* extension point but did not find enough evidence to commit to extending it versus building something new; both remain open.
3. Per-item Challenge acknowledgment (UX-009 Section 6) needs a new, small, `decision_id`-anchored object, structurally similar to `DecisionContext` and `ReflectionResponse` but distinct from both — not designed here, per this investigation's own no-new-ontology constraint.
4. Monitoring, Invalidation, Implementation Plan, and Review Plan (UX-009 Sections 9–11) all remain confirmed `DecisionContext`-incompatible by temporal shape, independent of Alpha's separate scope decision to defer Monitoring — their eventual homes are not addressed by this investigation.


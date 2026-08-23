# ADR Investigation 2 — DecisionContext vs. ReflectionResponse

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Central question:** Why does Atlas have both `DecisionContext` and `ReflectionResponse`? Could they be one object? Should they? Or are they fundamentally different concepts?

**Method:** Read fresh for this investigation — `ADR-Investigation-001-Decision-vs-DecisionContext.md`, `Decision-Workspace-Architecture-Resolution-Sprint-1.md`, `Decision-Workspace-Gap-Analysis.md`, `DE-005`, `DE-006`, `UX-008`, `UX-009`, the `ReflectionResponse`/`DecisionContext`/`Decision`/`Outcome` entities and value objects, `docs/ReflectionResponseATLAS009.md`, `docs/DecisionReflectionATLAS007.md`, `docs/ReflectionHistoryATLAS010.md`, and `docs/DecisionTimelineATLAS004.md`. Conclusions are traced to specific evidence, not carried over from Investigation 1's prior conclusions about `DecisionContext` — its ontology is re-derived here independently and cross-checked for consistency, not assumed.

---

## Phase 1 — ReflectionResponse Ontology

**What does it capture?** The investor's own verbatim response to exactly one Decision Coach question — nothing else. Per its governing document: "Lets an investor explicitly, voluntarily preserve their verbatim response to one Decision Coach question." It exists specifically because Decision Coach's default behavior is to let responses be *ephemeral* (discarded) — `ReflectionResponse` is the investor's explicit override of that default, "not because Atlas needs them, but because the investor decided something they said was worth having on record."

**Who authors it?** The investor, exclusively, and unusually strictly: `ResponseText` is "the one value object in this codebase where validation must not become transformation" — every other free-text value object in the codebase (`Subject`, `InvestmentCase.reason`, `Statement`, `DecisionContext.situation`) strips and normalizes the stored value; `ResponseText` checks only that the input isn't empty/whitespace-only, then stores it byte-for-byte, whitespace and punctuation and all. Atlas contributes nothing to the field's content — only the `ProvenanceSnapshot` alongside it, which records what Atlas showed the investor, never what the investor said.

**Why is it immutable?** For the same reason every other aggregate read in this and the prior investigation is immutable — to prevent a later, hindsight-informed edit from quietly rewriting what the investor actually said in the moment. This applies with particular force here, since the entire object exists to preserve a *reaction*, and a reaction that could be edited after the fact stops being evidence of anything.

**Why is it attached to Decision?** Because, per its own docstring, "a Decision, once recorded, never changes" — `Decision`'s own immutability is exactly what makes it a safe, permanent anchor for a second object to reference. `decision_id` is described as "the only durable-identity reference this aggregate holds" — every other field is a plain-value snapshot, never a reference to another object.

**What belongs inside it:** `response_text` (verbatim, unmodified) and a `ProvenanceSnapshot` — `reflection_description` (the exact sentence the investor read, captured verbatim, "immune to any future change in how those fields' own description templates are worded"), `coaching_question_text`, `grounding_pattern` (a `PatternMembershipSnapshot`: `strategy_name` + the specific prior `member_decision_ids` that formed the pattern), `strategy_signature_patterns` (a tuple of the same), and a snapshot of the in-progress `ReasoningContext` (`subject`, `decision_type`, `confidence` at the moment of reflection).

**What is intentionally excluded:** any live reference to `RecognizedPattern`, `RecognizedStrategySignature`, `DecisionReflection`, or `CoachingQuestion` themselves — all four are explicitly ephemeral and "may never be recomputed identically again," so only their plain-value content is snapshotted, never the objects. Also excluded: automatic capture (an explicit, separate, mechanical save/discard question is always asked — never inferred from whether the investor typed something); atomicity with Decision capture (deliberately two separate, non-atomic writes, with a disclosed, honestly-reported failure window between them); and any retrieval capability in its own original scope (ATLAS-009 was capture-only by explicit design; retrieval was a later, separate increment — see Phase 8).

---

## Phase 2 — DecisionContext Ontology (Read Fresh)

**Purpose:** Per its own docstring, "a point-in-time record of the circumstances surrounding an existing Decision — not a live view of the current portfolio, not market data, not a later reflection." It is a separate aggregate specifically so that `Decision` can "remain stable and minimal" while richer, optional narrative is captured elsewhere, for investors who choose to supply it.

**Invariants:** at most one `DecisionContext` per `Decision`, enforced twice — at the application layer (`DuplicateDecisionContextError`) and at the SQL schema layer (`decision_id` carries `unique=True`); the referenced `Decision` must already exist (`DecisionNotFoundError`) before capture is permitted; `situation` is required and non-empty; individual items inside `alternatives_considered`/`uncertainties`, if present, must themselves be non-empty, though the tuples as a whole may be empty.

**Ownership:** every field — `situation`, `portfolio_relevance`, `capital_considerations`, `alternatives_considered`, `uncertainties` — is exclusively investor-authored. Atlas contributes no content to any of them.

**Temporal meaning:** `captured_at` is preserved exactly as the investor gave it, unlike `Decision.decided_at`, which is normalized to UTC — `DecisionContext` treats the investor's own account of *when* the circumstances applied as itself part of the historical record, not something to be silently corrected. `recorded_at` is Atlas's own clock, marking when the record entered the system, separately from `captured_at`.

This independently reconfirms Investigation 1's own conclusion about `DecisionContext`'s ontology — arrived at again here from a fresh read, not carried forward by assertion.

---

## Phase 3 — Temporal Difference

**When each exists, relative to Decision:** both require an already-existing `Decision` — neither entity's own construction path permits otherwise (`DecisionNotFoundError` for `DecisionContext`; `ReflectionResponse.register()`'s own docstring: "anchored to an already-recorded Decision... the caller is responsible for calling this only once Decision capture has already succeeded"). In this narrow sense, both are strictly *after*, never *before* or *concurrent with*, their Decision.

**Can one exist without the other?** Yes, completely — nothing in either entity references the other. A `Decision` may have a `DecisionContext` and no `ReflectionResponse`, a `ReflectionResponse` and no `DecisionContext`, both, or neither. They are siblings under the same `Decision`, mutually invisible to each other.

**Must one precede the other?** No ordering is imposed or implied between them anywhere in the domain model — only that both, independently, must follow their shared `Decision`.

**Can there be several?** `DecisionContext` is capped at exactly one per `Decision`, doubly enforced (Phase 2). `ReflectionResponse` carries **no equivalent constraint anywhere found** — no `DuplicateReflectionResponseError`, no `unique=True` on `decision_id` in its own table. This is a genuine, confirmed asymmetry: the domain model does not itself prevent more than one `ReflectionResponse` per `Decision`. (In the one currently-built conversational flow, only one coaching question is ever asked per Decision, so only one is ever produced today — but that is a fact about the current process, not a constraint the entity itself enforces.)

**Can they occur years apart?** Ontologically, yes, for both — neither entity's own invariants place any bound on the gap between `Decision.recorded_at` and the companion object's own `recorded_at`. This must be stated carefully, separating ontology from implementation, exactly as instructed: the domain model places no such constraint on either object. Separately, and only as a process observation, not an ontological one: the one currently-built conversational flow captures a `ReflectionResponse` "immediately after [Decision capture] succeeds, in the same loop iteration" — a same-session process choice, not a rule the `ReflectionResponse` entity itself expresses or enforces. `DecisionContext`'s own docstring, by contrast, explicitly anticipates a gap ("context may be captured later"), though it likewise states no ontological bound on how large that gap may be.

**Can ReflectionResponse exist before DecisionContext? Can DecisionContext exist after ReflectionResponse?** Both are ontologically unconstrained and therefore both are possible — since neither object references the other, their relative order is determined by nothing in the domain model at all, only by whatever a future process chooses.

---

## Phase 4 — Semantic Difference

Neither "circumstances" nor "interpretation" alone is precise enough. The exact boundary, derived from Phases 1–2:

**`DecisionContext` is investor-*initiated* situational narrative.** Its existence requires no prior Atlas computation of any kind — an investor may supply it purely because the Decision Workspace offers the fields, unprompted by any pattern Atlas detected. Its content is *about the investment situation itself*: what the investor believed, what alternatives they weighed, what they were unsure of, how it related to their portfolio.

**`ReflectionResponse` is investor-*authored but Atlas-occasioned* response.** Its existence structurally depends on Atlas having first computed something specific worth reacting to — a `DecisionReflection` (itself grounded in a real correspondence between the investor's current, in-progress reasoning and their own already-recorded decision history) and a `CoachingQuestion` posed in response to it. Its content is not about the current investment situation at all — it is *about the investor's own reaction to being shown a pattern from their own past behavior*, a self-referential, meta-level content that `DecisionContext` has no equivalent of.

**Neither is Atlas's own interpretation** — Atlas authors no content in either object, only (in `ReflectionResponse`'s case) the occasion the investor is responding to. The precise, load-bearing distinction is *origin of the occasion*: `DecisionContext` has none; `ReflectionResponse`'s entire existence is downstream of one.

---

## Phase 5 — Field Comparison

| | `DecisionContext` | `ReflectionResponse` |
|---|---|---|
| **Purpose** | Investor's own account of the circumstances surrounding a specific Decision | Investor's own preserved reaction to an Atlas-surfaced pattern from their own decision history |
| **Author** | Investor, exclusively | Investor, exclusively, and preserved with stricter fidelity than any other free-text field in the codebase (no normalization at all) |
| **Meaning of content** | About the investment situation | About the investor's own behavioral pattern |
| **Occasioned by Atlas?** | No — investor-initiated | Yes — requires a prior `DecisionReflection`/`CoachingQuestion` |
| **Core fields** | `situation`, `portfolio_relevance?`, `capital_considerations?`, `alternatives_considered`, `uncertainties` | `response_text`, `provenance` (reflection description, coaching question text, grounding pattern/signature membership, reasoning-context snapshot) |
| **Cardinality per Decision** | 0..1, doubly enforced (application + SQL) | 0..N in the domain model — no constraint found anywhere; 0..1 only as a fact of the current process |
| **Lifetime** | Point-in-time capture, insert-only | Point-in-time capture, insert-only |
| **Mutability** | None — no update path exists | None — no update path exists |
| **Temporal scope relative to Decision** | Ontologically unbounded gap permitted; explicitly anticipated to occur "later" | Ontologically unbounded gap permitted (nothing in the entity forbids it); in practice, built to occur in the same session as Decision capture |
| **`case_id` present?** | No — reaches Case only transitively through Decision | No — same transitive-only relationship |
| **Retrieval surface today** | None — repository offers only `add`/`get_by_decision_id` | Yes, as of ATLAS-010 — `list_all_for_owner(user_id)`, scoped by transitive ownership through `decisions.user_id` |

---

## Phase 6 — Overlap Analysis

An actual merge attempt, not an assumption:

Could `ReflectionResponse.response_text`/`provenance` become an optional field group on `DecisionContext`? Tried directly against the evidence: `DecisionContext`'s own four content fields (`situation`, `alternatives_considered`, `uncertainties`, `portfolio_relevance`/`capital_considerations`) are never responses to anything — there is no occasion to snapshot provenance *from*. Adding a `provenance` field to `DecisionContext` would leave it permanently null for every genuinely `DecisionContext`-shaped row (the investor-initiated case) and populated only for the merged-in `ReflectionResponse`-shaped rows — a null-heavy discriminator field is the specific, recognizable shape of two aggregates artificially forced into one, not a genuine unification.

Could `DecisionContext`'s fields become part of `ReflectionResponse`? Tried in the opposite direction: `ReflectionResponse`'s entire shape is built around `provenance` — reflection description, coaching question text, grounding pattern. Forcing `DecisionContext`'s spontaneous, unoccasioned content into that shape would require *fabricating* a `ProvenanceSnapshot` for content that was never prompted by any coaching question — inventing a `reflection_description`/`coaching_question_text` that does not exist. This would be actual fabrication, the exact failure mode every architecture document in this sequence has been built to prevent.

**The merge fails in both directions, for a concrete, evidenced reason each time — not a preference, a structural incompatibility.** The two objects also carry different, independently-verified cardinality models (Phase 3/5): `DecisionContext` is doubly enforced at 0..1; `ReflectionResponse` has no such constraint anywhere found. Merging them would also require reconciling two different cardinality rules under one schema, a second, independent reason the merge does not hold.

---

## Phase 7 — Alternative Architectures

### Option A — Keep both

- **Advantages:** matches the structural incompatibility found in Phase 6; each object's shape is already fully explained by its own distinct purpose; zero cost, since both already exist, work, and are independently tested.
- **Disadvantages:** two names, two API surfaces to eventually wire into Alpha, rather than one.
- **Ontology:** none — status quo, already coherent per Phases 1–6.
- **Complexity:** lowest of any option — no change.
- **Future extensibility:** good — each object can be extended independently along its own axis (more `DecisionContext` fields for richer situational capture; more `ReflectionResponse` provenance detail as the coaching lineage grows) without either constraining the other.
- **Migration impact:** none.

### Option B — Merge

- **Advantages:** one object instead of two.
- **Disadvantages:** fails on direct attempt (Phase 6) in both directions — forces either a permanently-null discriminator or fabricated provenance; reconciles two incompatible cardinality models under one schema.
- **Ontology:** collapses "unoccasioned investor narrative" and "occasioned investor reaction" into one concept, destroying a real, evidenced distinction (Phase 4).
- **Complexity:** higher, not lower — every consumer would need to branch on which "kind" of merged row it received, reintroducing the discriminator problem at the call site instead of the schema.
- **Future extensibility:** worse — a merged object accretes both aggregates' fields, most of them irrelevant to any given row.
- **Migration impact:** a real schema/table merge, touching two independently-tested existing capabilities.

### Option C — Reflection becomes part of DecisionContext

- **Advantages:** none beyond a smaller Option B — same failure mode, narrower in scope (only `ReflectionResponse` absorbed, not the reverse).
- **Disadvantages:** identical to Option B's core objection — `DecisionContext` rows would carry a permanently-null provenance field for every unoccasioned entry.
- **Ontology:** same collapse as Option B, one direction only.
- **Complexity:** higher for the same reason as Option B.
- **Future extensibility:** worse, same reason as Option B.
- **Migration impact:** real, though narrower than a full bidirectional merge.

### Option D — DecisionContext becomes Reflection

- **Advantages:** none identified.
- **Disadvantages:** the more severe of the two one-directional merges — it would force every genuinely spontaneous, investor-initiated `DecisionContext` entry to fabricate a `reflection_description` and `coaching_question_text` that never existed, a direct fabrication of provenance, not merely an awkward null field.
- **Ontology:** the worst option evaluated — actively invents a false occasion for content that had none.
- **Complexity:** higher, and additionally dishonest in a way Option C is not.
- **Future extensibility:** worse.
- **Migration impact:** real, and additionally risky — any future consumer reading a fabricated `ProvenanceSnapshot` on a former `DecisionContext` row would be reading manufactured data.

### Option E — Introduce a common parent

- **Advantages:** would acknowledge the real structural kinship both objects share (`decision_id`-anchored, immutable, investor-authored-content, captured-once) without forcing their *content* together; could plausibly extend later to the still-undesigned per-item Challenge-acknowledgment object identified as an open question in Investigation 1.
- **Disadvantages:** no such parent, or any shared-base-class pattern, exists anywhere among the eleven-plus domain objects read across this investigation and the prior one — every one (`Decision`, `Outcome`, `DecisionContext`, `Case`, `Observation`, `Question`, `Conclusion`, `KnowledgeReference`, `ReasoningTrace`, `Judgment`, `ReflectionResponse`) is an independent frozen dataclass with no shared domain base beyond the language's own `object`. Introducing one here would be a genuine new ontological concept — explicitly outside this investigation's own constraint ("only ontology... no new domain models" is this whole sprint sequence's own standing rule, restated at the top of this investigation's own governing prompt).
- **Ontology:** would introduce a new abstract concept ("the family of Decision-anchored investor annotations") that does not exist today and was not asked for here.
- **Complexity:** adds an abstraction layer for a benefit not yet evidenced by any present need.
- **Future extensibility:** the one genuine, plausible advantage of this option — but speculative, not evidenced by anything found in this investigation.
- **Migration impact:** would require touching both existing entities to introduce or reference the new parent, for no present benefit.

**This investigation's own scope explicitly forbids introducing new ontology — Option E is therefore not adoptable here even where it has a plausible future case; it is recorded as a genuine idea for a *future*, separately-scoped investigation, not as this investigation's answer.**

---

## Phase 8 — Placement in Atlas Memory

| Concept | DecisionContext | ReflectionResponse |
|---|---|---|
| **Decision Timeline** (ATLAS-004 — Decision + nested Outcome→Evaluation→Learning chain) | Not included — ATLAS-004's own dependency list names only `DecisionRepository`, `OutcomeRepository`, `EvaluationRepository`, `LearningRepository` | Not included, for the same reason |
| **Reflection retrieval surface** (ATLAS-010, titled **"Reflection History"** — see naming note below) | No equivalent surface exists — `DecisionContextRepository` offers only `add`/`get_by_decision_id`, no owner-scoped listing | Belongs here directly — ATLAS-010 is a dedicated, read-only, investor-identity-scoped retrieval surface built specifically for `ReflectionResponse` |
| **Case Memory** (the Case-scoped `KnowledgeReference`/`ReasoningTrace`/`Judgment` layer) | Does not belong here — `DecisionContext` is strictly Decision-scoped, one level more specific, with no `case_id` at all | Does not belong here, for the same reason |
| **Decision Memory** (`DE-005`'s own term — per-position thesis history synthesized from `reason` fields) | Not currently wired in — `DE-005` §3's own grounding section names only `DecisionRecord`/`OutcomeRecord`/`TradeLogEntry`; `DecisionContext` is absent from it | Not currently wired in, for the same reason — also absent from `DE-005` §3 |
| **Knowledge** (`KnowledgeReference`) | Does not belong — reference-shaped, Case-scoped, no overlap (confirmed in Investigation 1) | Does not belong, for the same reason |
| **Learning** (the Core Loop's own Evaluation→Learning chain) | Does not belong — no field or reference overlap | Does not belong, for the same reason |
| **Pattern Recognition / Strategy Signature** | No relationship at all — entirely independent of this computational lineage | Direct downstream consequence — `ReflectionResponse`'s entire `provenance.grounding_pattern`/`strategy_signature_patterns` content is a snapshot of this lineage's own output |
| **Coaching** (`CoachingQuestion`, ATLAS-008) | No relationship | Direct, immediate upstream trigger — `ReflectionResponse` exists specifically to preserve a response to a `CoachingQuestion` |

**Naming note, disclosed rather than silently resolved:** this investigation's own governing prompt refers to "Reflection Timeline" as a placement target. The actual governing document found is titled **`ATLAS-010 — Reflection History`**, not "Reflection Timeline." This may be informal paraphrase in the prompt, or a genuine naming inconsistency somewhere in the corpus; this investigation did not find a document titled "Reflection Timeline" anywhere and does not assume the two names refer to confirmed-identical things beyond what ATLAS-010's own text describes.

**Structural finding:** `ReflectionResponse` sits inside one tight, self-consistent lineage — Pattern Recognition → Strategy Signature → Decision Reflection → Coaching Question → Reflection Response → Reflection History — each step named in ATLAS-007's and ATLAS-009's own docstrings as "the Understanding lineage." `DecisionContext` sits entirely outside that lineage, an independent, self-contained, chronologically and numerically earlier capability (API-002) with no relationship to any of it.

---

## Phase 9 — Consistency Test

Challenging the emerging conclusion (that both are correctly kept, structurally distinct) against every named neighbor. Contradictions are documented, not resolved, per instruction.

- **vs. `Decision`:** a weaker version of a risk already found in Investigation 1 for `DecisionContext` alone — could `ReflectionResponse.response_text` and `Decision.investment_case.reason` be confused? Less so than the `DecisionContext` case, because `ResponseText` answers a structurally different question (a reaction to a coaching prompt about the investor's own pattern) than `reason` (why this decision). Noted as a weaker, but not zero, instance of the same general risk category.
- **vs. `Outcome`:** no contradiction — unrelated content, no shared fields.
- **vs. `KnowledgeReference` / `ReasoningTrace`:** no contradiction — confirmed disjoint shape and scope in Investigation 1, unaffected by this investigation's findings.
- **vs. `Judgment`:** no current contradiction, but a genuine, disclosed open question: `Judgment`'s "Case's settled characterization" could, in principle, eventually be *informed by* a pattern of `ReflectionResponse` entries (an investor's own repeated reactions forming a settled self-characterization) — nothing in the current code performs or implies this synthesis, but nothing forbids it either. Documented as a possible future convergence point, not a present contradiction.
- **vs. `Case`:** no contradiction — both `DecisionContext` and `ReflectionResponse` confirmed to have no `case_id`, reaching `Case` only transitively through `Decision`, consistently.
- **vs. "Reflection" as a broader term:** a real, documented naming-overload contradiction — "Reflection" is used in this codebase for at least three distinct things: (1) `DecisionReflection`, an ephemeral, never-persisted correspondence object; (2) `ReflectionResponse`, the persisted investor reaction; (3) "Reflection" as a colloquial umbrella term for the whole feature area, as used in `Atlas-Alpha-Baseline-v1.0.md`'s own "Deferred: Reflection" scope bullet. Someone reading that Baseline's deferral in isolation cannot tell, from the word alone, whether it defers the ephemeral object, the persisted object, or both (in practice, it must defer both, since neither has any Alpha wiring — but the *document itself* does not disambiguate). Documented, not resolved.
- **vs. Portfolio:** no contradiction beyond the already-disclosed `portfolio_relevance` naming-clarity risk carried over from Investigation 1, restated here for completeness — unaffected by anything new found in this investigation.
- **vs. Daily Brief:** no contradiction — neither object is referenced by Daily Brief today; no new conflicting assumption found.
- **vs. `Learning`:** no contradiction — confirmed disjoint in Phase 8, no field or reference overlap.

**One genuine contradiction found and documented, not resolved:** the overloaded use of "Reflection" across an ephemeral object, a persisted object, and a colloquial feature-area name, most visibly in `Atlas-Alpha-Baseline-v1.0.md`'s own scope language. Two lesser, already-known risks (the `Decision.reason`-adjacent boundary risk, restated in weaker form; the `portfolio_relevance` naming risk, restated unchanged) are carried forward rather than re-litigated.

---

## Phase 10 — Final Decision

### Executive Summary

`DecisionContext` and `ReflectionResponse` are not duplicates, not competing designs, and not evidence of an inconsistent ontology. They are structurally distinct along the one axis that matters most for both: whether an Atlas-side computation occasioned the content. `DecisionContext` holds investor-*initiated* narrative about the investment situation, requiring no prior Atlas computation. `ReflectionResponse` holds investor-*authored but Atlas-occasioned* reaction to a specific, computed pattern from the investor's own decision history. A direct merge attempt fails in both directions for concrete, evidenced reasons — a permanently-null discriminator in one direction, fabricated provenance in the other — and the two objects additionally carry different, independently-confirmed cardinality models. The distinction between them, however, was not previously stated anywhere as a first-class architectural boundary; this investigation derives and states it explicitly for the first time.

### Evidence

- Both objects independently confirmed `decision_id`-anchored, immutable, investor-authored-only, captured-once (Phases 1–2, 5).
- Neither references the other, and neither imposes any ordering or temporal bound relative to the other beyond both following their shared `Decision` (Phase 3).
- `ReflectionResponse`'s entire content structure is organized around a `ProvenanceSnapshot` that has no equivalent, and no purpose, for `DecisionContext`'s unoccasioned content (Phases 1, 4, 6).
- `ReflectionResponse` carries no confirmed multiplicity cap; `DecisionContext` is doubly enforced at 0..1 — a genuine, previously undocumented asymmetry (Phases 3, 5).
- `ReflectionResponse` sits inside one tight, self-named "Understanding lineage" (Pattern Recognition → Strategy Signature → Decision Reflection → Coaching Question → Reflection Response → Reflection History); `DecisionContext` sits entirely outside it, with no relationship to any part of that lineage (Phase 8).
- A genuine naming-overload contradiction in how "Reflection" is used across the corpus was found and disclosed, not resolved (Phase 9).

### Alternatives Considered

| Option | Verdict |
|---|---|
| A — Keep both | Selected, with the boundary made explicit |
| B — Merge | Rejected — fails a direct merge attempt in both directions |
| C — Reflection into DecisionContext | Rejected — same failure mode as B, one direction |
| D — DecisionContext into Reflection | Rejected, more severely than C — requires fabricating provenance that never existed |
| E — Common parent | Not adopted here — a genuine idea, but introducing new ontology is outside this investigation's own scope; recorded as a future question, not a present answer |

### Decision

**`KEEP_WITH_CLEARER_BOUNDARY`**

Neither object requires any change — no field, schema, or code. What this investigation adds is the boundary itself, not previously stated as a single, explicit rule anywhere read for it: **`DecisionContext` is for content that required no Atlas occasion to exist; `ReflectionResponse` is for content that exists only because Atlas first computed something specific to react to.** Any future field, object, or UX-009 section content should be routed by this test, not by surface-level similarity in "sounds like investor narrative about a decision."

---

## ADR Candidate (Outline Only)

**Problem:** Atlas has two structurally similar, `decision_id`-anchored, investor-authored objects — `DecisionContext` and `ReflectionResponse`. Is this duplication, or two genuinely distinct concepts, and if distinct, what precisely separates them?

**Context:** Both objects are real, persisted, independently tested, and both are currently unwired to Alpha (a wiring gap, not an ontology gap, consistent with Investigation 1's own finding about `DecisionContext`). `ReflectionResponse` additionally sits inside a larger, six-step "Understanding lineage" that `Atlas-Alpha-Baseline-v1.0.md` explicitly defers from Alpha as a whole ("Reflection"); `DecisionContext` is independent of that lineage and was not named in that same deferral.

**Decision:** Keep both objects unchanged in scope and shape. Adopt the Atlas-occasioned/unoccasioned distinction (Phase 10) as the governing test for where future Decision-Workspace content belongs, in place of any looser "sounds like investor narrative" heuristic.

**Consequences:** No migration required. No field changes required. Future UX-009 implementation work (per Investigation 1's own open question 2, on where assumption-confirmation should live) should be evaluated against this same occasioned/unoccasioned test rather than being routed to whichever of the two objects merely seems structurally closest. The multiplicity asymmetry found in Phase 3/5 (no cap on `ReflectionResponse` per `Decision`) should be verified as intentional or accidental before any future retrieval or presentation surface assumes at-most-one.

**Open Questions** (carried forward, not resolved here):

1. Is the absence of a multiplicity cap on `ReflectionResponse` per `Decision` an intentional design choice (room for multiple future coaching occasions per Decision) or an oversight not yet exercised because only one coaching flow exists today? Not decided here.
2. Should the corpus disambiguate "Reflection" as used in `Atlas-Alpha-Baseline-v1.0.md`'s scope language from the specific `DecisionReflection` and `ReflectionResponse` objects it presumably covers? Not decided here.
3. Is "Reflection Timeline," as referenced in this investigation's own governing prompt, intended to name `ATLAS-010 — Reflection History`, or does it refer to something not found in this investigation's search? Not decided here.
4. Does `DecisionContext` need an owner-scoped retrieval surface analogous to `ReflectionResponse`'s `list_all_for_owner` (added in ATLAS-010), given none exists today? Not decided here — a capability gap, not an ontology question, and therefore adjacent to but outside this investigation's own scope.
5. Option E's common-parent idea (Phase 7) — worth a dedicated future investigation once (or if) a third `decision_id`-anchored, investor-authored, occasion-or-spontaneous object is designed (e.g., the per-item Challenge-acknowledgment object identified as an open question in Investigation 1), at which point a real, evidenced pattern (not a speculative one) would exist to generalize from.

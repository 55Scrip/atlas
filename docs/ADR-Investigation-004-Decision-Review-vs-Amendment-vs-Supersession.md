# ADR Investigation 4 — Decision Review vs. Amendment vs. Supersession

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Central question:** What is the ontology of changing your mind — not implementation, not editing, not UI?

**Method:** Read fresh for this investigation — the three prior ADR investigations, `Decision-Workspace-Architecture-Resolution-Sprint-1.md`, `DE-005`, `DE-006`, `UX-008`, `UX-009`, `ADR-002`, and the `Decision`/`Outcome`/`DecisionContext`/`ReflectionResponse`/`Evaluation`/`Learning` entities and value objects, plus a corpus-wide search for any existing "supersede"/"amend"/"amendment" domain concept (none found outside prose).

**Headline finding, stated up front:** `Evaluation` — an existing, already-built Core Loop object — already *is* a real review mechanism, sitting directly between `Outcome` and `Learning`, previously untested against this exact question in any prior investigation this session. Combined with UX-009's own explicit text ("the user completes the review by recording a new decision"), the evidence converges on a genuinely economical conclusion: **none of Review, Amendment, or Supersession requires new ontology.** Reconsideration is a workflow, not a stored fact. This is a different shape of answer than Investigation 3 reached for Drafts, and the difference is itself evidence-driven, not a default.

---

## Phase 1 — Decision, Re-Established

**What recording makes permanently true:** that at `recorded_at`, the investor committed to `decision_type` for `subject`, with `reason` and self-reported `confidence`, as of `decided_at`. This is a historical *fact about a moment* — not a standing claim about the present.

**What cannot ever change:** the content of that fact — `decision_type`, `subject`, `investment_case.reason`, `confidence`, `decided_at`, `recorded_at` — once set, per the constructor argument already established in `Investigation-003` Phase 1 and not re-derived here.

**What may legitimately change later:** nothing on the `Decision` object itself. What changes is the *investor's current belief*, which exists independently of any one past `Decision`. Atlas represents that change **extensionally** — by adding a new, separate, later `Decision` — never **intensionally**, by editing the old one. This distinction is the spine of this entire investigation.

**Why:** the same post-hoc-rationalization concern `UX-008` §14 names directly, re-cited rather than re-argued.

---

## Phase 2 — Define Review

**A major finding, not previously surfaced in this session:** `Evaluation` (`atlas/core/domain/evaluation/entity.py`) is already, precisely, one real shape of "Review." Its own docstring: "the investor's assessment of an Outcome: did it confirm or contradict what was expected, and why?" — immutable, referencing `Outcome` only, capturing a free-text `Statement` at `evaluated_at`.

Testing the candidate framings directly against it: is Review "looking again"? Partially — `Evaluation` looks at an `Outcome` once, not necessarily repeatedly. "Recording a judgment"? Yes, exactly — `Evaluation.statement` is precisely that. "Comparing reality"? Yes — comparing what happened (`Outcome`) against what was expected. "Evaluating quality"? Only if the investor chooses to write about reasoning quality in that free text — `Evaluation`'s structural anchor is `Outcome`, not `Decision` or reasoning directly.

**Must Review create persistence, or can it be transient?** Re-reading UX-009 fresh surfaces that "Review" is not one concept in that document — it is at least three, conflated under one word:

1. **The review *trigger*/schedule** — a forward-looking intent set at Decision-recording time ("Review after Q3 earnings"), which `Architecture-Resolution-Sprint-1.md` §8 already found has no persisted home anywhere. This must persist to be useful; nothing new is concluded about it here beyond reconfirming the gap already on record.
2. **The review *act*** — re-entering the Decision Workspace later. UX-009's own Navigation Behaviour text, re-read directly: "the user completes the review by recording a new decision: Thesis Valid / Revised / Superseded." **UX-009 itself already resolves the review act into the existing Decision-recording mechanism — no separate object.**
3. **`Evaluation`-as-review** — Outcome-confirmation assessment, already built, already persisted, structurally distinct from (2) because it requires an `Outcome` to exist, which a Maintain/Hold decision that never trades may never produce.

These three senses are genuinely different things wearing one English word, and conflating them would be the single easiest way to over-build here.

---

## Phase 3 — Define Amendment

**Can an immutable Decision ever be amended?** No — same constructor argument as Phase 1, restated once: there is no partial or in-place update path on `Decision` anywhere in this codebase.

**Why does UX language sometimes imply otherwise?** Traced to its exact source: `UX-009`'s own Section 9 interaction-ownership note — "After recording, items are locked and versioned. Changes to monitoring or invalidation conditions after recording create a visible amendment in the decision history." This is the *only* place "amendment" is used with any specificity in either governing UX document. Critically, it is describing amendments to **Monitoring and Invalidation Conditions** — and `Architecture-Resolution-Sprint-1.md` §7 and `ADR-Investigation-003`'s own Phase 9 both already, independently, found that Monitoring and Invalidation Conditions have **no persisted home anywhere in this codebase, on Decision or off it.**

**Conclusion:** "Amendment," as UX-009 actually uses the word, is not a property of `Decision`. It is a property a *future, currently-nonexistent* companion object (whatever eventually holds Monitoring/Invalidation Conditions) would need — specifically, the append-only-revision property `ADR-Investigation-003`'s own Phase 10 already worked out in detail for Drafts (Model B/C, the same shape already proven by `SecurityConfirmationEvent`). **Amendment is not a gap in Decision's ontology; it is a not-yet-relevant property of an object that does not yet exist.** Separating ordinary in-progress editing (covered entirely by `Investigation-003`'s own Draft concept, pre-commit) from historical amendment (a versioned revision to an *already-recorded* companion object) is exactly this distinction.

---

## Phase 4 — Define Supersession

Testing "a newer Decision replaces an older Decision" against the four dimensions named:

| Dimension | Does the old Decision remain true? |
|---|---|
| **Historical truth** | Yes, unconditionally, forever — "I decided X, on date D, for reason R" is permanently true regardless of any later Decision. Supersession never erases or falsifies history. |
| **Current recommendation** | No — the newer Decision supplants the older as the operative, currently-governing statement of committed intent for that subject going forward. |
| **Investor intention** | Both are true, indexed to different moments — the newer reflects *current* intention; the older reflects what intention *was*, at an earlier moment. This directly anticipates Phase 10 below. |
| **Portfolio state** | Not directly affected either way — `DE-006` §4's own "Five Concepts" table already, independently, separates Decision/Implementation-Intent from Actual Execution; superseding a Decision changes neither by itself. |

**"Replace" therefore does not mean "invalidate."** It means "supplant as the currently-governing statement," a relationship that holds between two already-immutable records, computable directly from `case_id`/`subject`/`decided_at` ordering. Nothing needs to be written down to know Decision B supersedes Decision A. This directly confirms, from first principles and independent of it, the conclusion `Architecture-Resolution-Sprint-1.md` §4 already reached about `Decision`'s own `Superseded` state being "consistent with immutability if computed rather than stored."

---

## Phase 5 — Define Reconsideration

Testing the five candidate framings directly:

- **A persisted event?** No — nothing needs to record "the investor started reconsidering" as a standing fact of its own.
- **A workflow?** Yes, functionally — UX-009's own "review mode" description, re-read: "the original decision is displayed read-only... current analysis is surfaced... allowing side-by-side comparison."
- **A state?** No — `Decision` carries no state field (confirmed repeatedly across this session), and nothing about "reconsidering" needs a status flag on anything either; it is an activity, not a condition something is *in*.
- **A Review?** Overlapping, not identical. UX-009's own Section 2 taxonomy names "Scheduled review" as *one of eight possible triggers* (alongside Thesis change, New evidence, User-initiated, etc.) that can lead into reconsideration — Reconsideration is the broader activity; a scheduled Review is one specific route into it.
- **Simply beginning a brand-new Decision?** Yes, precisely — per Phase 2's own UX-009 line-565 finding, reconsideration, whatever prompted it, resolves into recording a new `Decision` via the same existing mechanism. Reconsideration names *the Decision Workspace flow, entered again, informed by prior context* — a workflow framing over an already-existing mechanism, not a new domain concept.

---

## Phase 6 — Timeline

```
Case → Decision → Outcome → Evaluation → Learning → Reflection → New Decision
```

- **Review** does not occupy one place — it splits three ways: the review *trigger* would sit as a (currently unbuilt) forward-looking annotation set at Decision-recording time; the review *act* sits at the "New Decision" node — it is simply a Decision, arrived at via a review-flavored path; `Evaluation`-as-review sits exactly where the Core Loop already places it, between `Outcome` and `Learning`.
- **Amendment** has no place on this timeline at all, per Phase 3 — it belongs, if it ever exists, on a parallel, not-yet-built revision-timeline of a Monitoring/Invalidation companion object, not on the Decision→Outcome sequence.
- **Supersession** is not a node — it is a *relationship* between two points already on the timeline (two `Decision` instances for the same subject), derived by comparing their positions, never itself a step in the sequence.
- **Reconsideration** is the arrow, not a node — specifically the loop-back arrow from "Reflection" (or any other trigger point) back to "New Decision." It names the mechanism of the loop itself, not a new stop on it.

---

## Phase 7 — Existing Objects

| Object | Represents Review? | Represents Amendment? | Represents Supersession? | Represents Reconsideration? |
|---|---|---|---|---|
| `Decision` | The *result* of review/reconsideration, not the act itself | No | No — but participates as one of the two records the relationship holds between | The *result* |
| `Outcome` | No — represents what happened, not a review of it | No | No | No |
| `Evaluation` | **Yes, for the Outcome-confirmation sense specifically** (Phase 2) | No | No | No |
| `Learning` | No — the distilled lesson *from* an Evaluation, downstream of review, not review itself | No | No | No — a Learning could motivate a later Reconsideration, but is not itself the act |
| `ReflectionResponse` | No — an investor's preserved reaction to a behavioral *pattern*, not a review of a specific decision's outcome | No | No | No |
| `DecisionReflection` | No — explicitly, per its own docstring, "occasion-bound... never persisted, never compared across occasions" (ATLAS-007). Cannot represent any of the four target concepts, each of which requires *some* persistence to be useful, which `DecisionReflection` deliberately lacks by design | No | No | No |
| `DecisionContext` | No | No | No | No |
| `Question`/`Conclusion`/`Judgment`/`KnowledgeReference`/`ReasoningTrace` | No, for each | No, for each | No, for each | No, for each — each already tested and rejected against a comparable requirement battery in `Investigation-003` Phase 9, for the same underlying reasons (immutable, wrong shape/direction), re-confirmed here rather than re-derived |

**A reinforcing, cross-cutting observation surfaced by this comparison:** `Judgment` — "Case's settled characterization" — has exactly the same immutability and no explicit versioning mechanism `Decision` has. If an investor's Case-level characterization changes, the only available path, by the same logic as Phase 4, is capturing a *new* `Judgment`, with the old one remaining historically true. **The "supersession = new immutable record, old one stays true" pattern that answers this investigation's Phase 4 for `Decision` is not special to `Decision` — it is how this codebase already, uniformly, handles change for every immutable Core Loop object.** This is a broader architectural principle this investigation surfaces, not merely a fact about one aggregate.

---

## Phase 8 — Alternative Models

### Model A — Review only; no amendment; new Decision handles everything

Matches Phases 2, 5, and 7 directly: review resolves to a new `Decision` (or, for outcome-confirmation, the already-existing `Evaluation`); reconsideration resolves to a new `Decision`; supersession is derived, not stored. Does not itself solve the still-open review-*trigger* gap (Phase 2, item 1) — it does not claim to, since that gap is a separate, already-disclosed question (`Architecture-Resolution-Sprint-1.md` §8), not part of what happens *after* a Decision is recorded.

### Model B — Mutable Decision

Rejected on the identical grounds `Investigation-003`'s own Option B was rejected: directly breaks `Decision`'s core invariant and everything downstream that explicitly relies on it not changing (`ReflectionResponse`'s own stated safety claim: "valid because a Decision, once recorded, never changes"). The most severe failure mode of any option considered in this or the prior investigation.

### Model C — Review object; Supersession derived

A genuine, considered alternative: a new, explicit "Review" object distinct from both `Evaluation` and a plain new `Decision`, capturing a lighter-weight "I looked again and nothing changed" acknowledgment without necessarily producing a full new `Decision` each time. Not preferred: UX-009's own text (Phase 2, item 2) explicitly resolves review completion into recording a new Decision, not a separate object, and no governing document read for this investigation asks for a no-new-Decision acknowledgment path. Recorded as a real alternative, not a straw man — just not the one the evidence supports.

### Model D — Separate Amendment object

Per Phase 3: "Amendment" does not currently apply to `Decision` at all — it would only ever apply to a future Monitoring/Invalidation companion object that does not yet exist. Building a general-purpose Amendment object now, before the thing it would amend has been designed, is solving an unposed problem — the precise case this investigation's own governing instruction (do not add new ontology unless the evidence concludes one is required) exists to prevent.

### Model E — Decision lifecycle object

Would track superseded-by/amended-by/reviewed-by pointers explicitly. Interesting for query convenience, but Phase 4 already established supersession is fully derivable from `decided_at`/`recorded_at` ordering — a lifecycle object would be a materialized-view optimization, not an ontological necessity. Not preferred, for the same "storing something freely derivable" caution `Investigation-001`'s own Option C/E reasoning already applied to a comparable question.

### Model F — Entirely event-sourced

Nothing in this investigation's evidence shows `Decision` itself needs to become a formal event stream — it already behaves like the "final, committed event" in an implicit one (each new Decision for a subject *is* the next event, in effect), and the existing table-of-immutable-rows, queried by ordering, already achieves what a formal event-sourcing layer would add, without the additional machinery. Not preferred, for the same "solving an unposed problem" reasoning as Model D.

---

## Phase 9 — Immutability Test

| Concept | Achievable without mutation? | How |
|---|---|---|
| Review | **Yes** | Resolves to a brand-new immutable `Decision` (Model A) or, for outcome-confirmation, a brand-new immutable `Evaluation` |
| Supersession | **Yes, trivially** | A derived relationship between two already-immutable records, never itself written anywhere |
| Amendment | **Yes** | Per the already-proven append-only-revision pattern (`Investigation-003`'s own Model B/C, and the real, shipped `SecurityConfirmationEvent` precedent) — a new immutable revision of a companion object, not an edit to any existing row, *if and when that companion object is ever built* |
| Reconsideration | **Yes** | A workflow/activity, not a stored fact — nothing about "the investor is reconsidering" needs its own row; the *result* (a new Decision) is, as always, itself immutable |

**All four concepts are achievable without ever mutating anything.** None of Review, Amendment, Supersession, or Reconsideration actually requires breaking `Decision`'s immutability — a clean, evidence-grounded finding that runs contrary to what a naive reading of "changing your mind" might suggest.

---

## Phase 10 — Historical Truth

Testing whether "I believed X," "I later rejected X," and "I still once believed X" can be simultaneously true, and which concepts preserve which:

- **"I believed X" (at T1):** preserved permanently by Decision #1 itself — its own `reason`/`decision_type`, as of `decided_at = T1`. Never erased.
- **"I later rejected X" (at T2):** preserved by Decision #2 — a new, later `Decision` with a different `decision_type`/`reason`. Its existence, dated after Decision #1, *is* the record of rejection. Nothing needs to be written onto Decision #1 for this to be true.
- **"I still once believed X":** not a third fact requiring a third record — it is simply Decision #1, read again, later, with its own timestamp intact. The fact that Decision #1 is never deleted or mutated automatically preserves this statement for as long as the historical record exists at all.

**All three are simultaneously true, and Atlas already preserves all three automatically, as a direct consequence of Decision's own immutability plus Decision #2's own separate existence — with zero additional mechanism.** This may be the single most load-bearing finding in this investigation: the very feature (immutability) that looks, on first impression, like an obstacle to representing a changed mind is exactly what makes all three historical statements simultaneously and automatically true, at no extra cost.

---

## Phase 11 — Current Truth

Five distinct concepts, deliberately not identical, with distinct ownership:

| Concept | Owner |
|---|---|
| Historical truth | The full, ordered set of `Decision` records for a subject, collectively, unconditionally |
| Current belief | Whichever `Decision` is chronologically latest for that subject — a derived pointer (Phase 4), not a separately stored fact |
| Portfolio state | Actual holdings data (Portfolio Intelligence), never `Decision` — `DE-006` §4's own Decision/Actual-Execution boundary applies directly, reused rather than re-derived |
| Current recommendation | Atlas's own, freshly computed analysis (`recommendation.level`) — entirely independent of `Decision`; it changes moment to moment as new evidence arrives, with no `Decision` required to change it |
| Latest decision | A derived pointer, identical mechanism to "current belief" above — the `Decision` with the greatest `decided_at`/`recorded_at` for the subject |

**These five are not identical, and conflating any two would be a real modeling error.** Current recommendation and latest decision, specifically, are *often and legitimately different* — this is not an edge case; it is the entire reason UX-009's own "Thesis change" trigger (Section 2) exists at all. Atlas's recommendation moves continuously; the investor's last recorded Decision does not move until they act again. UX-009's whole "Why a Decision Is Required" section exists precisely because these two are architecturally distinct and can drift apart.

---

## Phase 12 — Decision Memory (Compared Against DE-005)

`DE-005`, re-read fresh, §4: "What Atlas SHALL Remember, Per Position" lists exactly — why initiated (earliest BUY reason), why increased/reduced (later Add/Trim reasons, in order), reported Outcomes (linked via `decision_id`), and "Thesis Synthesis" — explicitly: *"a synthesis, not a new recorded field... produced fresh each time it is needed from the underlying records — it is never itself stored as a separate, possibly-stale verdict."*

**Can Decision Memory work using only immutable Decisions? Yes — per DE-005's own explicit text, not merely this investigation's inference.** §3 states directly: "a position's thesis is not a separately recorded object; it is the accumulated set of `reason` statements across that position's own Decision history... read together in order." **DE-005 already reached, independently and before this investigation began, the identical "derive, don't store" conclusion Phases 4, 9, and 10 above reach from first principles** — for exactly the same underlying reason (avoiding a second, possibly-stale source of truth). This is strong, direct, pre-existing corroboration, not a new argument invented for this document.

Decision Memory does **not** require Review, Supersession, or Amendment as separate stored objects. It requires only reading the already-immutable, ordered set of Decisions (plus Outcomes) and computing a synthesis over them — exactly what this investigation independently concludes is sufficient.

---

## Phase 13 — Reflection Relationship

**Can reflection (`DecisionReflection`/`ReflectionResponse`) change a Decision?** No — neither object has any write path to `Decision` anywhere in this codebase; every application service touching either (`capture_decision_context.py`, `capture_reflection_response.py`, and the security-confirmation services examined in `Investigation-003`) only ever *reads* from `DecisionRepository`.

**Can reflection motivate a later Decision?** Yes, precisely — this is its designed role. `DecisionReflection` surfaces a pattern *during* an in-progress, not-yet-recorded conversation, motivating the *current* in-progress decision; `ReflectionResponse` preserves the investor's reaction, which could plausibly motivate a *future* Reconsideration (Phase 5). In neither case does reflection ever reach back and alter an existing `Decision`. This directly reuses and reconfirms `Investigation-002`'s own finding — Reflection is occasioned by, and downstream of, existing decision history, never upstream-mutating of it.

---

## Phase 14 — Outcome Relationship

**Does an Outcome ever supersede a Decision?** No. `Outcome`'s own docstring: "what actually happened after a Decision... it never modifies Decision." Outcome answers a different *kind* of question (what happened) than supersession answers (what does the investor currently intend). An `Outcome` could *prompt* a later Decision (a disappointing result triggering reconsideration) — but prompting is not superseding, exactly the same distinction Phase 13 draws for Reflection. Outcome and Decision remain permanently, structurally separate, per `DE-006` §4's own boundary, reused rather than re-derived. **Outcome merely evaluates a Decision (via the Outcome→Evaluation chain, Phase 2/7) — it never replaces or governs it.**

---

## Phase 15 — Atlas Memory

| Surface | Placement |
|---|---|
| Decision Timeline (ATLAS-004) | Already includes the full `Decision`→`Outcome`→`Evaluation`→`Learning` chain directly, natively, today — Review-as-new-Decision, Evaluation-as-outcome-review, and Learning-as-distillation all already belong here with zero new work |
| Reflection History (ATLAS-010) | `ReflectionResponse` only, unchanged from `Investigation-002`'s own Phase 8 finding |
| Decision Memory (`DE-005`'s own term) | The synthesized, always-freshly-computed thesis-strength narrative over the *same* Decision Timeline data — not a separate storage location, a computed view over it (Phase 12) |
| Learning | Its own terminal Core Loop node, downstream of `Evaluation`, already correctly placed by the existing ontology |
| Case Memory | None of Review/Amendment/Supersession/Reconsideration belong here — all four are Decision-subject-scoped, one level more specific than the Case-wide epistemic primitives (`KnowledgeReference`/`ReasoningTrace`/`Judgment`), consistent with every other Decision-adjacent object tested this session |
| Portfolio Memory | **Not a concept found anywhere in the material read for this investigation.** No governing document across all four investigations names a distinct "Portfolio Memory" object — flagged honestly as a naming gap this investigation cannot resolve, not silently mapped onto Portfolio Intelligence's own current-state computation, which is explicitly live, recomputed state, not memory (per `DE-006` §8's Portfolio Simulation exclusion discussion) |
| Atlas Memory (the umbrella term) | Per `UX-008`'s own definition, the umbrella under which `Decision`/`Outcome`/`Evaluation`/`Learning`/`DecisionContext`(once wired)/`ReflectionResponse`(once wired) collectively sit. Review/Supersession/Reconsideration are *activities or relationships over* that memory, not separate citizens *within* it. Amendment, per Phase 3, does not currently apply to anything inside Atlas Memory today. |

---

## Phase 16 — Consistency Test

Challenging Model A (the emerging preferred architecture) against every named neighbor, documenting rather than resolving:

- **vs. Decision / Outcome / Learning:** no contradiction — Model A adds nothing to any of them; every review/reconsideration resolves through the same, already-existing mechanisms.
- **vs. Reflection:** no contradiction — Phase 13's finding (reflection motivates, never mutates) is fully compatible with "new Decision handles everything."
- **vs. DecisionContext:** a real point worth naming precisely, not assumed away — if a Decision is superseded, does its own `DecisionContext` (once wired) remain "accurate"? Examined: `DecisionContext`'s own docstring already frames itself as "a point-in-time record... not a live view," meaning it was never meant to track present accuracy — it is explicitly historical, exactly like the Decision it belongs to. No contradiction, but the framing must be stated correctly rather than assumed.
- **vs. Draft (`Investigation-003`):** a genuine, positive integration point, not a contradiction — Reconsideration (Phase 5) could plausibly *begin* as a new Draft, reusing the object `Investigation-003` already designed, before eventually producing a new Decision. Worth naming explicitly as a place where this investigation's findings compose cleanly with the immediately preceding one.
- **vs. Portfolio:** no contradiction — Decision/Reconsideration/Supersession never touch portfolio state directly (Phase 11's own ownership finding).
- **vs. Daily Brief:** **a genuine, disclosed, unresolved tension, not merely a minor detail.** If Decision Timeline already shows the full ordered history (Phase 15), does Daily Brief need its own explicit "this decision has been superseded" or "this looks stale" computed flag, or does the ordered timeline alone suffice? UX-009's own Section 2 triggers ("Scheduled review," "Invalidation signal") implicitly assume *some* surface knows a Decision is due for reconsideration — which needs either the still-missing review-trigger (Phase 2, item 1; `Architecture-Resolution-Sprint-1.md` §8) or a staleness signal neither this nor any prior investigation has designed. Documented, not resolved.
- **vs. Imports:** no contradiction — imported/API/BrokerSync Decisions (`Investigation-003`'s own Phase 16 finding, reused) participate in supersession/history exactly as manually-recorded ones do, since supersession is purely a function of `case_id`/`subject`/`decided_at` ordering, indifferent to `source`.
- **vs. Historical migrations:** no contradiction — ATLAS-009B's own retroactive `user_id` reconciliation (`Investigation-002`'s own finding, reused) already proves this codebase can safely backfill metadata onto historical Decisions without disturbing their immutable content; the same reasoning would extend to any future supersession-adjacent read model.
- **vs. Future collaboration:** a genuine, disclosed open question, inherited rather than newly discovered — if multiple investors could ever act on a shared Case (nothing today supports this), "whose latest Decision governs" (Phase 11's "current belief" ownership) becomes ambiguous, in exactly the way `Investigation-003` already flagged for Drafts. Not a contradiction specific to Model A; a shared limitation with the same root cause (the single-investor assumption) already named in the immediately preceding investigation.

---

## Phase 17 — Final Decision

**`REVIEW_ONLY`**

Not `REVIEW_PLUS_SUPERSESSION` — Phases 4, 9, and 16 all converge on supersession being entirely computable at zero storage cost; nothing in this investigation's evidence requires it to be explicitly represented as an object, flag, or event anywhere. Naming it as a co-equal second thing that "must exist" alongside Review would overstate what the evidence actually shows.

**This does not require new ontology** — a direct, notable contrast with `Investigation-003`'s conclusion for Drafts, and the contrast is itself evidence-driven: reviewing and reconsidering resolve into `Decision.register()` (optionally routed through `Investigation-003`'s own already-scoped Draft concept) or, for outcome-confirmation specifically, the already-existing, already-persisted `Evaluation`. Amendment does not apply to `Decision` at all (Phase 3) and is deferred, not solved, until — if ever — the companion object it would actually apply to (Monitoring/Invalidation Conditions) is itself designed; building it now would be solving a problem that does not yet exist, directly against this investigation's own governing instruction.

**What this investigation does *not* resolve, and does not claim to:** the review-*trigger* (the forward-looking schedule set at recording time) still has no persisted home — `Architecture-Resolution-Sprint-1.md` §8 already found this, and this investigation reconfirms rather than closes it, since that gap concerns what happens *before* a future review, not what happens *after* the Decision already recorded — a different question than the one this investigation was asked.

---

## Phase 18 — ADR Candidate (Outline Only)

**Problem:** Does Atlas need separate persisted concepts for Review, Amendment, Supersession, and Reconsideration once a Decision has been recorded, or do these collapse into mechanisms that already exist?

**Context:** `Decision` is immutable by explicit design (Phase 1). `Evaluation` already exists as a real, if Outcome-scoped, review mechanism (Phase 2). UX-009's own text already resolves review completion into recording a new Decision (Phase 2), not a separate object. `DE-005` independently, and prior to this investigation, already concluded Decision Memory requires no separately-stored thesis-strength verdict (Phase 12). No existing object represents Amendment or Supersession as first-class concepts (Phase 7), and neither needs to — Amendment applies only to a not-yet-built companion object (Phase 3), and Supersession is fully derivable from existing timestamps (Phase 4).

**Decision:** Adopt `REVIEW_ONLY`. Review and Reconsideration resolve into the existing `Decision.register()` mechanism (optionally via `Investigation-003`'s own Draft concept) or, for outcome-confirmation specifically, the existing `Evaluation` object. Supersession is never stored — always computed by comparing `decided_at`/`recorded_at` across Decisions sharing a subject. Amendment is deferred entirely, pending the separate, not-yet-authorized design of whatever eventually holds Monitoring/Invalidation Conditions.

**Invariants:**
- No field or flag on `Decision`, or anywhere else, ever marks a Decision "superseded," "reviewed," or "amended" — these are always computed, never persisted as status.
- A `Decision`'s own immutability is never weakened to accommodate any of the four target concepts.
- Amendment-shaped behavior (append-only revisions), if and when it is ever needed for a future companion object, follows the already-proven `Investigation-003`/Security-Confirmation pattern — not invented fresh at that time.

**Consequences:** Decision Timeline (ATLAS-004) already supports everything this ADR concludes, today, with zero new work. `DE-005`'s own Decision Memory synthesis is independently validated, not contradicted, by this investigation. The review-*trigger* gap remains open and is explicitly out of this ADR's scope.

**Rejected Alternatives:** B (mutable Decision — breaks the core invariant and everything downstream that relies on it, the most severe failure considered); C (a dedicated Review object — not supported by UX-009's own explicit text); D (a general Amendment object — premature, nothing yet exists for it to amend); E (a Decision lifecycle object — an unrequired materialized view of a freely-derivable relationship); F (full event sourcing — solves a problem the existing immutable-row-plus-ordering model already solves).

**Open Questions** (carried forward, not resolved here):

1. Does Daily Brief need its own explicit "superseded/stale" computed signal, or does surfacing the ordered Decision Timeline suffice? (Phase 16)
2. How, in product terms — not architecturally, which is already clean — should Reconsideration compose with `Investigation-003`'s own Draft concept? (Phase 16)
3. Should `Evaluation` ever be extended to cover reasoning-quality review for decisions that never produce an `Outcome` (e.g., a Maintain/Hold decision), given its current anchor is strictly Outcome-scoped? (Phase 2)
4. When (if ever) Monitoring/Invalidation Conditions are designed, should their own amendment mechanism be a direct reuse of the Security-Confirmation event pattern, or does that companion object's own shape argue for something else? (Phase 3, deferred from `Architecture-Resolution-Sprint-1.md` §7)
5. Is the still-missing review-*trigger* home (distinct from the review act resolved here) the next investigation this lineage should undertake? (Phase 2, 17)

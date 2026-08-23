# ADR Investigation 7 — The Nature of Assumptions

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Starting premise, not reopened:** `Decision`, `DecisionContext`, `ReflectionResponse`, `Decision Draft`, Review/Supersession, and `CaseCondition` are all already settled by prior investigations in this series. This document determines only: what is an Assumption?

**Method:** Built on the full evidence base of `Investigation-001` through `Investigation-006`, all still fresh in this session. Two fresh checks were performed: `atlas/core/domain/hypothesis/entity.py`, read in full (never previously read in this series), and a corpus-wide search for any existing `class.*Assumption` — which surfaced a genuinely important, previously-undiscovered finding.

**Headline finding, stated up front:** "Assumption" **already exists in this codebase** — but as `OutlookAssumption` (`atlas/analysis_engine/outlook.py`), a fully-structured, fully-numeric disclosure of Atlas's own valuation-model inputs ("the range assumes the market re-rates this company's FCF yield..."), explicitly with "no free-text 'why' field," owned entirely by Atlas. **This is a different concept from UX-008/UX-009's investor-belief Assumption, sharing only a name.** This is the **third** instance of naming overload this document series has now found (after "Reflection" in `Investigation-002` and "Evaluation" in `Investigation-006`) — a real, recurring vocabulary risk in this codebase, not a one-off coincidence, and it must be disambiguated explicitly wherever it recurs.

---

## Phase 1 — What Is an Assumption?

Testing each candidate to contradiction:

| Candidate | Verdict | Why |
|---|---|---|
| Belief | Fails | Too broad — a belief could be about anything; doesn't capture the specific structural role of something *reasoning depends on* |
| Expectation | Fails | Too passive — UX-009 presents assumptions as things "the decision currently depends on," a structural dependency, not a passive anticipation |
| Prediction | **Fails, directly and explicitly** | UX-009's own text rejects this framing by name: "stated as a condition, not a prediction: 'GCP margin expansion continues' rather than 'GCP margins will expand.'" Direct textual confirmation, not inference. |
| Dependency | Survives, partially | UX-009's own language: "what the decision currently relies upon" — captures the structural role but not the epistemic content |
| Hypothesis | Fails as identity, tested fully in Phase 2 | Different epistemic stance — see below |
| Accepted uncertainty | Fails | Backwards — an assumption is a deliberately-accepted *certainty* (provisionally), not uncertainty itself. This more precisely describes UX-009's own separate "Uncertainties" concept (`DecisionContext.uncertainties`) — a genuinely different, near-opposite epistemic stance that happens to sit nearby in UX-009's own document structure |
| Accepted proposition | Survives | Captures the "provisionally treated as true" stance correctly |
| **Premise** | **Survives, most precisely** | The exact logical role: a proposition accepted as true for the purpose of an argument/reasoning chain — precisely what UX-009 assigns Assumptions relative to the Decision's own reasoning |
| Condition | Fails as the fundamental nature (though related) | Per `Investigation-006` Phase 7, an assumption *can* be watched via a `CaseCondition`, but is not inherently condition-shaped — it is a statement the reasoning depends on, whether or not anyone is watching it. Tested fully in Phase 6, not assumed here. |
| Claim | Fails | Too generic — doesn't capture the "reasoning's own foundation" role |

**Conclusion:** an Assumption fundamentally is **a proposition the investor's (or Atlas's) reasoning treats as true, without independently re-proving it each time, such that the reasoning's own soundness depends on the proposition remaining true.** Synthesizes "premise" (the logical role) with "dependency" (why it matters) — directly matching UX-009's own "what the decision currently relies upon."

---

## Phase 2 — Assumption vs. Hypothesis

`Hypothesis`, read fresh: "the investor's provisional belief about what something may mean... Atlas assigns no truth value, confidence, or conviction to a Hypothesis." Explicitly unresolved — a candidate explanation still being tested, standalone, immutable, no relationship to `Observation`/`Decision`/`DecisionContext`/`Evidence`.

An Assumption, by contrast, per UX-009, is treated as a foundation the *current* reasoning already stands on — provisionally *accepted*, not merely floated as a candidate. The difference is epistemic stance, not content: Hypothesis says "this might explain X, unresolved"; Assumption says "we are treating this as true for now, and the decision depends on it remaining so."

- **Can a Hypothesis become an Assumption?** Functionally, plausibly — once a `Hypothesis` is sufficiently supported by Evidence (the Core Loop's own Interpretation→Hypothesis→Evidence→Conclusion chain), an investor might stop treating it as merely provisional and rely on it as a foundation. Nothing in the current domain model represents this transition explicitly; consistent with every object tested across this series, "becoming" means *capturing a new record*, informed by the old one, never mutating the `Hypothesis` itself.
- **Can an Assumption become a Hypothesis?** Conceivable in reverse — if new Evidence contradicts an assumption, the investor might "downgrade" it back to merely provisional. Same mechanism: a new capture, not a mutation.
- **Can both exist simultaneously?** Yes — an investor may hold several already-accepted Assumptions while exploring entirely separate, still-unresolved Hypotheses about other aspects of the same Case.
- **Are they mutually exclusive?** No, but they are different epistemic *statuses* for similar kinds of content — the same statement text could plausibly appear as a Hypothesis at one point and, later, as an Assumption once accepted, without contradiction, since they would never be the same object, only semantically-adjacent content at different epistemic stages.

---

## Phase 3 — Assumption vs. Investment Thesis vs. Reason vs. Decision

`DE-005` §1, re-cited directly: "Investment Thesis. The specific, named claim about a business and its valuation that justifies holding, adding to, reducing, or exiting a position — captured in the Investor's or Atlas's own words at the time a Decision was made... a position's thesis is not a separately recorded object; it is the accumulated set of `reason` statements across that position's own Decision history."

**Dependency graph:**

```
Decision --requires--> Reason (Decision.investment_case.reason, structurally required)
Reason, accumulated across a position's Decision history --constitutes--> Thesis (derived, per DE-005, never stored separately)
Reason/Thesis --implicitly rests on--> Assumption(s) (0..N, extractable and individually nameable)
```

Assumptions are narrower and more structured than Reason: Reason is the investor's own free-text justification ("why I'm doing this"); Assumptions are the specific, enumerated propositions embedded in or implied by that reasoning that must remain true for the reasoning to hold ("GCP margin expansion continues"). UX-009's own Section 4 ordering confirms this exactly: "Primary reason field... Essential assumptions: the two to three assumptions that the decision currently depends on" — assumptions are named *as a consequence of, and in support of*, the primary reason, never prior to or independent of it.

**Which depends on which:** Decision depends structurally on Reason; Reason (aggregated over time) constitutes Thesis (derived, not stored); Reason/Thesis implicitly rests on Assumptions, which depend on nothing else themselves, but whose continued truth the Reason's own soundness depends on.

---

## Phase 4 — Assumption vs. Evidence

| Question | Answer | Why |
|---|---|---|
| Does evidence *prove* assumptions? | No | Nothing in this codebase's own epistemic humility doctrine (`UX-008`'s anti-false-precision, `DE-004`'s own no-false-precision commitment) treats anything as "proven" absolutely |
| *Support* assumptions? | **Yes** | The calibrated, correct verb — matches this codebase's own established Evidence/Counter-Evidence structure (`DE-002`, already cited in `DE-005` §1) |
| *Challenge* assumptions? | **Yes, symmetrically** | Matches UX-009's own Section 6 text directly: "Uncertain assumptions: assumptions in the decision rationale that Atlas has low confidence in" — evidence raises or lowers confidence *in* an assumption, never proves or disproves it outright |
| *Replace* assumptions? | No | Evidence doesn't edit an assumption's own wording; if an assumption is shown unsound, the investor records new reasoning that no longer depends on it — the same new-record-not-mutation pattern reused throughout this series |
| *Destroy* assumptions? | No, not literally | Per this whole series' immutability principle, an assumption, once stated as part of a Decision's own recorded reasoning, remains permanently true that it *was* held, even after later evidence undermines it — directly paralleling `Investigation-004` Phase 10's own "I still once believed X" finding |

---

## Phase 5 — Assumption vs. Existing Knowledge Objects

| Object | Fit? | Why not |
|---|---|---|
| `KnowledgeReference` | No | Reference-shaped (points *at* another object), never a free-standing proposition itself. An Assumption *is* a proposition, not a pointer to one — confirmed disjoint, consistent with every prior investigation |
| `ReasoningTrace` | No | Same reference-collection shape, same disjoint finding |
| `Judgment` | No | Closer in spirit (both are investor beliefs about a subject), but `Judgment` is explicitly "settled" — permanently concluded — whereas an Assumption is explicitly provisional and expected to potentially be revisited (UX-009's entire Section 9 framing). A real epistemic-stance mismatch. |
| `Observation` | No | Retrospective ("something noticed"); an Assumption is a *standing belief currently relied upon*, not a record of a past noticing — though an `Observation` could be evidentiary *input* to forming one |
| `Question` | No | The inverse of an Assumption in a real sense — a `Question` is explicitly unresolved/open; an Assumption is explicitly (provisionally) accepted, at least for now |
| `Conclusion` | No | Atlas/reasoning-authored, anchored to a single `Evidence` record, the *output* of an evidence-weighing process — an Assumption is closer to an *input* the reasoning starts from or stands on, a different direction in the reasoning chain |
| **`OutlookAssumption`** (`atlas/analysis_engine/outlook.py`) | **No — a genuine naming collision, not a fit** | Fully structured, fully numeric, no free-text "why" field, describing Atlas's own valuation-model inputs — owned entirely by Atlas, no investor-belief content at all. Shares only a name with what UX-008/UX-009 mean. |

**Does Assumption already exist? Not as the object UX-008/UX-009 need — but the word "Assumption" already exists in this codebase, meaning something unrelated.** This must be disambiguated explicitly in any future naming, exactly the same caution already raised for "Reflection" and "Evaluation."

---

## Phase 6 — Assumption vs. CaseCondition (Central Question)

Testing all four framings directly, not assuming any:

- **CaseCondition watches Assumptions?** Plausible and partially confirmed — `Investigation-006` Phase 7 already found assumption-confirmation "could plausibly be modeled as a specific kind of CaseCondition." A `CaseCondition`'s own predicate text *can* be defined about an assumption ("watch whether GCP margin expansion continues"). But `Investigation-006` Phase 7 also found the reverse: "an assumption can exist without a CaseCondition" — so watching is a possible, optional *relationship*, not Assumption's defining nature.
- **Assumptions create CaseConditions?** Only as a product workflow (a UI convenience — "turn this assumption into something I track"), never as an ontological requirement. Nothing in the evidence shows an Assumption's own statement structurally requires or automatically spawns a `CaseCondition`.
- **CaseConditions ARE Assumptions?** No — tested directly and rejected. A `CaseCondition` (`Investigation-006` Phase 1) is fundamentally "a predicate... that Atlas can evaluate against real data over time," with its own evaluation lifecycle (Confirmed → Active → Satisfied/Superseded/Retired). Not every Assumption is watched or evaluated; forcing all of them into `CaseCondition`'s own evaluation-lifecycle shape would be architecturally wasteful and semantically imprecise for the (likely majority of) assumptions no one is actively tracking.
- **Assumptions and CaseConditions are unrelated?** Too strong — a real, evidenced relationship exists (the first bullet above).

**Surviving ontology: Assumption and CaseCondition are related but distinct.** An Assumption is the statement — the premise itself, existing independent of any tracking mechanism. A `CaseCondition` is an optional, separate tracking/evaluation apparatus that *may* be set up to watch whether a specific Assumption (or any other future fact) continues to hold. Every Assumption can, but need not, have zero-or-more `CaseCondition`s referencing it; not every `CaseCondition` need reference an Assumption either. A loose, optional cross-reference — never an is-a or contains relationship.

---

## Phase 7 — Ownership

| Part | Owner |
|---|---|
| Assumption text | Shared — Atlas proposes (from analysis, matching UX-009's own "Atlas-identified, user-confirmable"), investor may edit |
| Atlas proposal | Atlas-originated |
| Investor modification | Investor — follows `ADR-002` C-02's own authorship-transfer model exactly (an edit transfers to "User Authored"; unedited acceptance stays "Atlas Suggested / User Accepted"), directly reused from `Investigation-006` Phase 8 |
| Investor confirmation | Investor |
| Atlas interpretation (Atlas's own assessment of how well-supported the assumption currently is) | Atlas — a separate, derived layer on top of the investor-owned statement text, the same separation already established between `Decision.reason` (investor-owned) and `recommendation.level` (Atlas-owned) |
| Historical revisions | The same event-stream mechanism established for `CaseCondition` (`Investigation-006` Phase 11) — a change is a new immutable revision event, not a mutation |
| Meaning (what remaining-true implies for the thesis) | Investor-anchored, ultimately — the same reasoning `Investigation-005` Phase 7 already established for Invalidation Conditions' own "meaning" ownership, applied here by direct analogy |
| Truth | Deliberately not resolved in this table — Phase 8's own dedicated question |

---

## Phase 8 — Truth

- **Can assumptions be true? False? Unknown?** Yes to all three, ordinarily — a proposition can correspond to reality, fail to, or (most commonly, at the time it's made) have genuinely uncertain truth value. Uncertainty at formation time is the *normal, expected* state, not a defect.
- **Useful despite being false?** Yes, and precisely so — this is `UX-008`'s own core distinction ("A decision can be correct even if the outcome is negative... The Decision Workspace evaluates the quality of the reasoning, not the performance of the stock"), applied here specifically to Assumptions: an assumption's usefulness as a sound basis for reasoning *at the time* is separate from its eventual truth value, discovered later.

**Is truth even the correct property? No.** Precisely because of the finding above, truth is not the primary property worth tracking. The more precise, useful properties are: whether the assumption was *reasonable to hold at the time* (a quality-of-reasoning judgment, made once, historically fixed); whether it *currently remains supported* by evidence (a live, re-evaluatable status, per Phase 4); whether it has been *specifically challenged/contradicted* (Phase 4, potentially escalating to invalidation if also tracked via a role-tagged `CaseCondition`, per `Investigation-006` Phase 5). **"Currently supported" vs. "currently challenged" — a calibrated, evidence-relative status — is the correct property, not a binary true/false verdict**, directly consistent with this codebase's own anti-false-precision doctrine.

---

## Phase 9 — Time

- **Does an Assumption change, or only our relationship to it? Only our relationship to it.** The statement, once captured, is immutable, same as every object in this series; what changes is the ongoing assessment of whether it remains supported (Phase 8). Directly parallels `Investigation-004` Phase 1's finding about `Decision` itself: the historical fact never changes; only the current relationship to it evolves.
- **Can an Assumption become obsolete?** Yes — if the reasoning that depended on it is itself superseded (`Investigation-004`'s own derived-supersession finding), the old assumption becomes obsolete not because it changed, but because the Decision it supported is no longer operative.
- **Invalid?** Only in the "no longer supported by current evidence" sense (Phase 8) — never in the sense of the historical record being erased.
- **Superseded?** Yes, in the same derived sense `Investigation-004` established for `Decision` itself — a newer Decision's own assumptions supersede an older Decision's as the currently-operative set, without erasing the old ones' historical truth (that they *were* assumed, at the time).

---

## Phase 10 — Lifecycle

Testing the eight-item list, directly reapplying `Investigation-006` Phase 10's methodology:

| Item | Actually is | Why |
|---|---|---|
| Draft | Not a state of Assumption itself | If it originates from Draft content (`Investigation-003`), "Draft" belongs to that separate, upstream object |
| Accepted | The creation event, not a separate state | Same as `CaseCondition`'s own "Confirmed" |
| Rejected | A candidate that never became a real Assumption at all | An investor could reject an Atlas-proposed candidate without ever accepting it — arguably outside Assumption's own lifecycle entirely, the same "a draft that's abandoned never becomes a Decision" logic |
| Supported | **A projection, not a stored state** | The default, ongoing relationship absent any challenge event (Phase 8) — derived, not persisted |
| Challenged | **An event** | Evidence emerges that weakens the assumption (Phase 4) — directly analogous to `CaseCondition`'s own "evaluated_satisfied" event type, generalized here to "evidence-relationship changed" |
| Invalidated | Really just "sufficiently and specifically Challenged" | Possibly the same event type as Challenged, differentiated by degree, not a truth-verdict (consistent with Phase 8's rejection of truth as the tracked property) |
| Retired | An event, distinct from Challenged/Invalidated | The reasoning that depended on it moved on (Phase 9), independent of whether the evidence relationship changed |
| Deleted | **Genuinely unresolved** | The same open question `Investigation-003` Phase 12 and `Investigation-006` Phase 10 already left open, recurring rather than newly resolved here |

**Conclusion, mirroring `Investigation-006`'s own economy:** Draft doesn't belong to Assumption's own lifecycle; Accepted is just the creation event; Supported is a projection, not a stored state; Challenged/Invalidated collapse toward one event type differentiated by degree; Retired and Superseded are real, distinct terminal events; Rejected describes a candidate outside the lifecycle entirely; Deleted remains genuinely unresolved.

---

## Phase 11 — Versioning

Direct reuse of `Investigation-006` Phase 11's settled answer — nothing in this investigation's evidence suggests Assumption needs different treatment: **a new, immutable revision event, referencing the same, stable Assumption identity.** Not an edit, not a wholly disconnected new object.

---

## Phase 12 — Evaluation

What actually gets evaluated?

| Candidate | Verdict |
|---|---|
| The wording | No — per this series' own "validation must not become transformation" principle, wording is stored text, not itself evaluated for truth |
| **The underlying claim** | **Yes — the correct answer** — whether the proposition the assumption's wording expresses continues to be supported by available evidence: the semantic content, not the phrasing |
| The evidence | No — evidence is the *input* to evaluation (Phase 4), not the object being evaluated |
| The prediction | No — per Phase 1's own finding, UX-009 itself rejects framing assumptions as predictions; there is no forecast component to evaluate |

**Conclusion:** Atlas evaluates the underlying claim, via available Evidence/Observations/Conclusions bearing on it — never the wording, never a prediction.

---

## Phase 13 — Atlas Memory

| Surface | Relationship |
|---|---|
| Decision | Assumptions are extracted from / stated alongside a Decision's own reason — a derivative sibling, never stored on `Decision` itself (Phase 3) |
| **Decision Memory (`DE-005`)** | **Directly and explicitly the right home, per DE-005's own existing text** — DE-005 already frames Thesis (which Assumptions decompose) as "the accumulated set of `reason` statements... read together in order," and explicitly states thesis-strength synthesis is "produced fresh each time it is needed... never itself stored as a separate, possibly-stale verdict." A future formally-captured Assumption should feed directly into this *same, already-established* DE-005 synthesis mechanism — a stronger, more precisely-anticipated integration point than `Investigation-006` found for `CaseCondition` (which only identified a disclosed *future* extension, not something DE-005's own text already anticipates the shape of) |
| Knowledge (`KnowledgeReference`) | No relationship — disjoint shape (Phase 5) |
| Reasoning (`ReasoningTrace`) | No direct relationship, but a plausible, loose future one — `ReasoningTrace`'s own target is a generic typed reference, so a future `ReasoningTrace` could reference an Assumption as supporting content, without the two being the same object |
| Evaluation (Core Loop) | No direct relationship — but a real structural *parallel* worth naming without conflating: evaluating an assumption's claim (Phase 12) conceptually echoes what Core Loop `Evaluation` does for an `Outcome` ("did it confirm or contradict expectation"). An echo, not a shared object — naming it precisely avoids exactly the naming-collision risk already flagged for "Evaluation" in `Investigation-006` |
| Learning | No relationship — a different, terminal Core Loop node |
| Reflection | No relationship — occasioned by Pattern/Coaching, unrelated to Assumption's origin |
| Case Memory | Assumptions are Decision/Case-scoped, not part of the Case-wide `KnowledgeReference`/`ReasoningTrace`/`Judgment` layer — one level more specific, consistent with every comparable object tested this series |
| Outcome | No relationship — backward-looking fact of what happened, unrelated to Assumption's forward-standing role |

---

## Phase 14 — Daily Brief

| Candidate | Consume? |
|---|---|
| Assumptions (raw text) | Know, not display — too granular, same narrow-projection principle reused from `Investigation-005`/`006` |
| Changes (Challenged/Invalidated events) | **Yes — the real, meaningful signal** |
| Challenges | Same as Changes — this *is* the event worth surfacing |
| Invalidations | Same, at higher priority — mirroring `CaseCondition`'s own Invalidation-role priority |
| Review Triggers | No — a computed union, not a stored object (`Investigation-005`'s settled finding, reused) |
| **Projections** | **Yes — the correct boundary**, same as `Investigation-006` Phase 14's own conclusion |

---

## Phase 15 — Existing Objects

Reapplying Phase 5's own comparisons as the complete answer to this phase: no existing Core Loop object — `Decision`, `Outcome`, `DecisionContext`, `ReflectionResponse`, `Evaluation`, `Learning`, `Observation`, `Question`, `Conclusion`, `Judgment`, `KnowledgeReference`, `ReasoningTrace`, `Hypothesis` — satisfies the ontology established in Phases 1–12. `OutlookAssumption` shares only a name, not the ontology. **Assumption does not already exist as the object this document needs.**

---

## Phase 16 — Alternative Models

| Model | Verdict |
|---|---|
| **A — Assumption as text on Decision** | Fails — `Decision`'s own immutability cannot hold a growing/editable list; Phase 10's own lifecycle (challenge/retire events) needs something `Decision` structurally cannot support; per Phase 3, assumptions need individual identity to be tracked/confirmed/challenged separately, which cramming them into the same free-text `reason` field loses entirely |
| **B — Assumption as CaseCondition** | Fails — tested directly in Phase 6 and rejected: not every assumption needs an evaluation lifecycle; forcing all into `CaseCondition`'s predicate-evaluation shape is wasteful and imprecise for the likely-majority never actively tracked |
| **C — Separate Assumption object** | **Matches everything found** — a distinct proposition/premise (Phase 1), related-but-distinct from `CaseCondition` (Phase 6), its own leaner-than-eight-item lifecycle (Phase 10), and a uniquely strong, already-anticipated DE-005 integration point (Phase 13) |
| D — Derived only (unparsed text inside `Decision.reason`) | A real, honest, minimal option — costs nothing, adds no ontology, but forecloses individual tracking, challenge history, and the DE-005 integration Phase 13 found genuinely available |
| E — Event sourced | The correct *persistence pattern* (Phase 11, the now four-times-proven template), but as a standalone model doesn't answer the scope/relationship questions Phases 1–9 already resolved — Model C, built using this pattern, is the complete answer |
| F — Knowledge object (reuse `KnowledgeReference`) | Fails — tested and rejected in Phase 5: `KnowledgeReference` is reference-shaped, not proposition-shaped; an Assumption *is* the proposition, not a pointer to one |

---

## Phase 17 — Consistency Test

Challenging Option C, documenting rather than resolving:

- **vs. Decision:** no contradiction — untouched, referenced only.
- **vs. Draft:** no contradiction, a positive integration point — assumption content plausibly originates as draft content (Phase 10).
- **vs. DecisionContext:** no contradiction, and a clean division of labor worth naming — `DecisionContext` currently has no "assumptions" field of its own, so a separate Assumption object doesn't compete with or duplicate anything it already holds.
- **vs. Reflection:** no contradiction — unrelated origin stories.
- **vs. Knowledge:** no contradiction — disjoint shape (Phase 5).
- **vs. CaseCondition:** **the most important check, tested carefully.** Per Phase 6, the relationship is a loose, optional cross-reference. A real, disclosed integration-discipline risk exists: could an Assumption be retired while a `CaseCondition` still watching it is never told, letting the two drift out of sync? Flagged, not resolved — resolving it would mean designing the actual cross-reference mechanism, outside this investigation's ontology-only scope.
- **vs. Outcome:** no contradiction — unrelated, backward vs. forward-looking.
- **vs. Evaluation (Core Loop):** **the naming-collision risk, reconfirmed from a second angle.** "Evaluating an assumption's underlying claim" (Phase 12) must never be casually conflated with the Core Loop's own `Evaluation` aggregate in any future implementation's naming — the *fourth* instance of this pattern across the series (Reflection, Evaluation/`CaseCondition`, Assumption/`OutlookAssumption`, and now this cross-cutting "evaluate" verb ambiguity specifically). Worth naming as a genuinely systemic vocabulary risk this document series keeps surfacing, not a one-off.
- **vs. Learning:** no contradiction — unrelated.
- **vs. Daily Brief:** consistent, given the Phase 14 projection boundary is respected.
- **vs. Atlas Memory:** directly consistent, and more concretely so than any prior investigation's finding — per Phase 13, `DE-005`'s own existing text already anticipates exactly this kind of decomposed reasoning content, a stronger integration story than `CaseCondition`'s own merely-disclosed-future-extension.
- **vs. future collaboration:** the same inherited, disclosed Case-scoping ambiguity, now named a **fifth** time across this series (`Investigation-003`, `004`, `005`, `006`, now `007`) — a recurrence, not a new finding.
- **vs. imported Decisions:** no contradiction — imported/API/BrokerSync Decisions simply have no stated Assumptions at all, which is fine; nothing requires a Decision to have any (Phase 3's dependency graph treats Assumptions as optional decomposed content, not a required invariant).
- **vs. provider synchronization:** the same genuinely open question `Investigation-006` first surfaced — if evidence bearing on an assumption's claim is ever provider-synchronized, does it carry a different trust shape than Atlas-computed evidence? Not resolved here either, restated as still open.

**Two tensions worth flagging distinctly, per instruction:** (1) the `CaseCondition`/Assumption sync-discipline risk — a real, newly-specific instance of integration risk; (2) the "evaluate" naming collision, now confirmed across three separate objects (Core Loop `Evaluation`, `CaseCondition`'s own evaluation process, Assumption's own claim-evaluation) — a systemic vocabulary risk, not merely a one-off.

---

## Phase 18 — Final Decision

**`SEPARATE_ASSUMPTION`**

Justified purely from findings: Phase 1 established Assumption as a distinct premise/dependency, surviving contradiction against nine alternative framings. Phase 2 cleanly distinguished it from `Hypothesis` on epistemic stance (provisional-candidate vs. accepted-foundation). Phase 5 confirmed no existing object — including the confusingly-named but unrelated `OutlookAssumption` — satisfies it. Phase 6 confirmed `CaseCondition` is a related-but-non-identical, optional tracking mechanism, not Assumption's own defining nature. Phase 13 found a uniquely strong, already-anticipated integration point in `DE-005`'s own existing Decision Memory synthesis text. Phase 16 showed every alternative (text-on-Decision, CaseCondition-is-Assumption, Knowledge-object, derived-only) fails a specific, evidenced test.

---

## Phase 19 — ADR Candidate (Outline Only)

**Problem:** UX-009 requires Assumptions to be individually named, confirmed, and tracked for challenge/support over time. No existing object satisfies this, and the codebase already, confusingly, uses the word "Assumption" for an unrelated Atlas-methodology-disclosure concept.

**Context:** `Decision` cannot hold this content (immutable, no lifecycle). `CaseCondition` is a related but non-identical, optional watching mechanism, not a substitute (Phase 6). `DE-005`'s own text already anticipates exactly this kind of decomposed, per-position reasoning content feeding its Decision Memory synthesis (Phase 13) — a stronger existing hook than any prior investigation in this series has found.

**Decision:** `Assumption` is a stable, Decision-anchored identity (with `case_id` reachable transitively, per every comparable object in this series) representing a single premise's statement — free text, Atlas-proposable, investor-confirmable/editable. Its lifecycle is expressed entirely through the same unified event-stream pattern already established for `CaseCondition` (`Investigation-006`), never through mutation. It is loosely, optionally cross-referenced by `CaseCondition`s that choose to watch it — never contained by or identical to one.

**Invariants (illustrative, not binding — no schema decided here):**
- `Assumption` itself is created once and never mutated; every subsequent change is a new event in its own stream (`revised`, `challenged`, `retired`, `superseded`).
- "Supported" is a derived projection (absence of a challenge event), never a stored state.
- Truth is never tracked as a binary verdict — only "currently supported" vs. "currently challenged," consistent with this codebase's anti-false-precision doctrine.
- The name `Assumption` (this concept) and `OutlookAssumption` (the existing, unrelated Atlas-methodology object) must never be conflated in code, comments, or product copy.
- Unedited acceptance of an Atlas-proposed assumption follows `ADR-002` C-02's authorship model exactly — never silently relabeled as user-authored.

**Consequences:** No existing object requires modification. `DE-005`'s own Decision Memory synthesis gains a natural, already-anticipated future input. Daily Brief gains one more narrow-projection source, consistent with `CaseCondition`'s own boundary. The `CaseCondition`/Assumption sync-discipline risk (Phase 17) must be actively managed by any future implementation.

**Rejected Alternatives:** A (text on Decision — breaks immutability, loses individual trackability); B (Assumption as CaseCondition — forces an evaluation lifecycle onto content that doesn't inherently need one); D (derived only — a legitimate minimal option, not chosen because it forecloses the DE-005 integration Phase 13 found genuinely available); F (Knowledge object — wrong shape, reference-based not proposition-based).

**Migration/Compatibility:** None required to any existing object. Fully additive.

**Open Questions** (carried forward, not resolved here):

1. Should the `CaseCondition`/Assumption cross-reference be enforced (a `CaseCondition` watching a retired Assumption is flagged) or left entirely loose? (Phase 17)
2. Is "Rejected" (an Atlas-proposed candidate the investor never accepted) worth its own event type, or does it fall entirely outside Assumption's own lifecycle as this investigation's Phase 10 suggests? (Phase 10)
3. Should `OutlookAssumption` be renamed to close the naming collision, now that it has been found and documented three times over (Reflection, Evaluation, Assumption)? Not decided — a documentation/naming question for a future, separate task, not this investigation's to resolve.
4. What is the precise mechanism by which a future `Assumption` feeds `DE-005`'s own thesis-strength synthesis? Genuinely promising (Phase 13) but not designed here.
5. Same open questions on provider synchronization and future collaboration inherited unchanged from `Investigation-006` (Phase 17) — not newly resolved here either.

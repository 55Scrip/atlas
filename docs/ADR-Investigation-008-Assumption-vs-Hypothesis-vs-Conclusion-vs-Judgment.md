# ADR Investigation 8 — Assumption vs. Hypothesis vs. Conclusion vs. Judgment

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Starting premise, not reopened unless contradicted:** `Investigation-007` established Assumption as a separate concept representing a premise reasoning currently relies upon. This investigation tests that conclusion genuinely (Phase 17) rather than protecting it by assumption, and it survives.

**A major discovery made in the course of gathering fresh evidence, disclosed before any phase begins:** `docs/atlas_domain_object_architecture/OE-002-Domain-Object-Model.md` is a **normative, closed** Domain Object Set of exactly six objects — Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome. **Hypothesis, Evidence, Conclusion, and Question are not part of it.** Reading further, `docs/ADR-005-Atlas-Reasoning-Foundations-Naming-and-Authority.md` (Accepted) resolves what could otherwise look like a contradiction: it establishes that the implemented `atlas/core/` package (the ten-step Question→Learning Foundation Core Loop this entire investigation series has been analyzing) and the separate, pre-implementation "Atlas Reasoning Foundations" ontology track (where OE-002 and a differently-worded, Final-status `ADR-002-The-Nature-of-Judgment.md` both live) are **explicitly declared not to govern, supersede, reinterpret, or imply convergence with one another** — a decision "not authorized" to be inferred by anyone short of "its own explicit decision." This investigation therefore treats the **implemented** `atlas/core/domain/*` entities as primary authority throughout (consistent with every prior investigation in this series, which has always grounded itself in running code), while explicitly disclosing every place the parallel ontology track's own definitions diverge, rather than silently picking one or attempting to reconcile them — reconciliation is explicitly not this investigation's to perform.

**Method:** Fresh reads this investigation: `atlas/core/domain/hypothesis/entity.py`, `atlas/core/domain/evidence/entity.py`, `OE-002-Domain-Object-Model.md` (in full), `ADR-005-Atlas-Reasoning-Foundations-Naming-and-Authority.md` (in full), and the "Current Best Definition" section of `atlas_reasoning_foundations/ADR-002-The-Nature-of-Judgment.md`. `Conclusion` and `Judgment` (implemented) were read fresh in `Investigation-006`/`001` respectively and remain unsummarized in this session. A grep for `class.*Judgment\b|class.*Conclusion\b` outside the Core Loop found no additional naming collisions; `Evidence`'s own docstring self-discloses a **fourth** naming collision found across this series ("`atlas.domains.decision.models.Evidence` and the `atlas.evidence` package already use the word 'Evidence' for an unrelated, automated evidence-quality-assessment concept... a known legacy naming collision, left untouched") — notably, this is the first collision in the series the codebase's own authors had already found and documented themselves, rather than one this investigation series discovered independently.

---

## Phase 1 — Re-Establish Assumption

Restated only as necessary, from `Investigation-007`: an Assumption is a proposition the reasoning treats as true, without independently re-proving it, such that the reasoning's own soundness depends on it remaining true. Atlas does not treat it as true (it tracks "supported" vs. "challenged," never a verdict — `Investigation-007` Phase 8). The investor treats it as *provisionally* true — that is what "accepted as premise" means. It is provisional by definition, expected to potentially be revisited. It differs from a fact (what `Observation` records — something noticed) precisely in role: a fact is what was noticed; an Assumption is what reasoning is *built on top of*, independent of whether it was itself independently verified.

---

## Phase 2 — Re-Establish Hypothesis

`Hypothesis`, read fresh: "the investor's provisional belief about what something may mean — not an Observation, not Evidence, not a Decision, not an Outcome, not a truth claim, and not an Atlas-generated conclusion... Atlas assigns no truth value, confidence, or conviction to a Hypothesis." Standalone — "introduces no relationship to Observation, Decision, DecisionContext, or Evidence."

- **What exactly is unresolved?** Whether the candidate explanation is correct at all — a Hypothesis is explicitly a *candidate*, not yet weighed against anything.
- **Does Atlas believe it?** No — explicitly, structurally, Atlas assigns it nothing (no truth value, confidence, or conviction field exists on the entity at all).
- **Does the investor believe it?** The investor *formulated* it (`formulated_at`), but nothing in the entity requires or implies belief — it is a candidate explanation the investor may or may not currently favor.
- **Explain something? Predict something? Propose something?** Explain, primarily — "provisional belief about what something *may mean*" is interpretive, not predictive. It proposes a candidate meaning, open to testing, not a forecast of future values.
- **Epistemic status:** the weakest commitment of any object tested in this series — weaker even than Assumption (which is at least provisionally *relied upon*). A `Hypothesis` is floated, not relied upon.

---

## Phase 3 — Assumption vs. Hypothesis, Tested Against Examples

| Statement | Classification | Why |
|---|---|---|
| "Margins are declining because competition is increasing." | **Hypothesis** | A causal explanation for an observed fact — proposes what something means, doesn't commit to it |
| "Margins will normalize next year." | **Neither, as stated** | Fails Assumption (a forecast, directly the framing UX-009 rejects — `Investigation-007` Phase 1) and fails Hypothesis (Hypothesis explains meaning, doesn't predict future values). It would need reframing to fit either shape: "margin normalization is assumed" (Assumption) or as a `CaseCondition` predicate ("if margins normalize by...") |
| "The current valuation assumes margins recover." | **Assumption** | Self-labeled (the word "assumes" appears in the statement itself) and structurally correct — a premise the valuation reasoning depends on |
| "Management can maintain pricing power." | **Both, depending on epistemic stance, not content** | As a candidate explanation currently being investigated, it is Hypothesis-shaped. As a premise the current thesis already relies on without further investigation, it is Assumption-shaped. |

The fourth example is the decisive one: **the same statement text can be either object, depending entirely on whether the investor is currently *testing* it (Hypothesis) or currently *relying* on it (Assumption)** — confirming and concretely sharpening `Investigation-007` Phase 2's "different epistemic status for similar content" finding with a worked example.

---

## Phase 4 — Evidence

Read fresh. Key structural fact: `direction: Direction` (`SUPPORTS` or `CHALLENGES`) is a **required** field.

| Question | Answer |
|---|---|
| Truth? | No — explicit: "It does not represent objective truth: Atlas preserves that the investor regarded this information as evidence, not that the information proves or disproves anything." |
| Reliability? Authority? | Not asserted by the core object — no such field exists. (A *separate*, legacy, unrelated "automated evidence-quality-assessment concept" under the same word does exist elsewhere — the fourth naming collision, self-disclosed by `Evidence`'s own docstring, not conflated with here.) |
| Support direction? | **Yes — the clearest, most direct confirmation in this whole investigation of how Evidence relates to claims.** It doesn't prove; it structurally, mandatorily `SUPPORTS` or `CHALLENGES`. |
| Prove things? | No, explicit. |
| Merely participate in reasoning? | Yes, precisely. |
| Support both a Hypothesis and an Assumption? | **Structurally, neither directly** — `Evidence`'s own entity has *no* reference to `Hypothesis` or `Assumption` at all, only `observation_id` (confirmed by its own docstring: "Evidence still introduces no relationship to Hypothesis, Decision, or DecisionContext"). Any support relationship would have to run through `ReasoningTrace` (which can reference arbitrary same-Case objects) or remain informal/presentational. |
| Challenge both? | Same answer — no direct field-level link either way. |

---

## Phase 5 — Conclusion

Already read fully in `Investigation-006`, reapplied precisely here.

- **What makes it "derived"?** Anchored to exactly one `Evidence` record — an explicit implementation simplification ("a future increment extending this to multiple Evidence records... is expected, not merely possible").
- **What must exist first?** One `Evidence` record — `evidence_id` is required, non-optional.
- **Does it assert truth?** No, by family pattern, though notably its own docstring does *not* carry the same explicit truth-disclaimer language `Evidence`/`Hypothesis` each state separately — a real, disclosed stylistic inconsistency in how directly each object disclaims truth-assertion, not a substantive gap.
- **Atlas owns it, or the investor?** **Genuinely underspecified** — unlike `Evidence`'s clear "the investor regarded," `Conclusion`'s own docstring does not state authorship explicitly. Flagged as a real gap, not filled in by assumption.
- **Can a Conclusion exist without Evidence?** No — structurally required.
- **Can it contradict an Assumption? Conclude an Assumption is no longer reasonable?** Yes, at the content level — nothing prevents this. But structurally, `Conclusion` has no reference to `Assumption` at all, the same "no direct field-level link, only informal or via a future `ReasoningTrace`" pattern found in Phase 4.

---

## Phase 6 — Judgment

Already read fully in `Investigation-001`. **Now tested against the newly-discovered second and third definitions** (OE-002 §5.4; the Reasoning Foundations track's own Final-status `ADR-002-The-Nature-of-Judgment.md`).

| Trait | Implemented entity | OE-002 §5.4 | Reasoning Foundations ADR-002 |
|---|---|---|---|
| Core phrasing | "the Case's settled, Case-relative characterization of an identified subject" | "records the Case's settled, Case-relative characterization of an identified subject" — near-identical wording | "the ontological object produced by a completed Reasoning Act: the specific, complete determination that Act reaches" |
| Ties to an upstream "Act"? | No | No | **Yes, tightly** — Judgment cannot exist without one |
| Requires Reasoning Trace? | No — no such field | Explicit: "does not require prior epistemic support from a Reasoning Trace" | Not addressed in the excerpt read |

The implemented entity and OE-002 read as **the same concept described at two levels of formality** (near-identical core phrasing). The Reasoning Foundations track's own definition is **materially different in emphasis** — it makes Judgment's existence depend on a "Reasoning Act" concept that exists in *neither* the implemented codebase nor OE-002. **Per ADR-005, none of the three governs the others.** This investigation treats the implemented entity as authoritative for what follows, and states this divergence rather than silently resolving it.

Testing the phase's own questions against the **implemented** entity:

- More settled? **Yes, explicitly** — "settled" appears in both the implemented docstring and OE-002; `Conclusion`'s own docstring uses no comparable word.
- More subjective? Not more or less — both are equally non-truth-asserting.
- Investor-authored or Atlas-authored? Underspecified, the same disclosed gap as `Conclusion`.
- Case-level? **Yes, confirmed** — `case_id`, subject optional, no narrower anchor by default.
- A characterization rather than a proposition? Yes, precisely — the field is literally named `characterization`, distinct from `Conclusion.statement`.
- Downstream of Conclusion? Not structurally required — no such reference exists on the entity.
- Independent from formal reasoning? Yes — "does not require prior epistemic support from a Reasoning Trace," matching OE-002 verbatim.

---

## Phase 7 — Conclusion vs. Judgment

| Dimension | Conclusion | Judgment |
|---|---|---|
| Authorship | Underspecified | Underspecified |
| Scope | Anchored to exactly one `Evidence` record — narrow | Case-wide, subject optional — broad |
| Truth semantics | Non-truth-asserting by family pattern | Explicitly non-truth-asserting, explicitly "settled" |
| Reasoning dependency | Requires the reasoning that produced the anchoring Evidence | Requires nothing |
| Evidence dependency | Mandatory, 1:1 | None |
| Mutability | Immutable | Immutable |
| Persistence | Real, tested, three-layer pattern | Same |
| Temporal role | Mid-chain (Evidence → Conclusion → Decision, via the provisional `ConclusionDecisionLink`) | Unconstrained — no chain position, per OE-002 §6 |
| Downstream consumers | The named `ConclusionDecisionLink` bridge | No equivalent named bridge to anything |
| Relationship to Decision | Explicit, if "PROVISIONAL STATUS," link | None |

**Attempting the merge, directly:** it fails on two independent structural grounds. First, the mandatory-vs-optional Evidence anchor — `Conclusion` structurally requires `evidence_id`; `Judgment` structurally has none — merging would force either a fabricated anchor onto `Judgment` or the loss of `Conclusion`'s own enforced requirement. Second, narrow-vs-broad scope — `Conclusion` is inherently about one evidentiary chain; `Judgment` is inherently Case-wide. Merging would either narrow `Judgment`'s genuinely useful breadth or loosen `Conclusion`'s tight anchor beyond what its own docstring commits to. **The merge fails precisely where the objects' own ownership boundaries diverge in kind, not degree.**

---

## Phase 8 — Assumption vs. Judgment, Tested Against Examples

| Statement | Classification | Why |
|---|---|---|
| "Management quality is strong." | **Judgment** | A standing characterization, Case-wide, independent of any specific Decision's own reasoning — equally true/relevant whether or not any Decision currently depends on it |
| "Management will successfully execute the restructuring." | **Neither, as stated** | Predictive framing — fails both, mirroring Phase 3's second example |
| "The thesis assumes management executes successfully." | **Assumption, unambiguously** | Self-labeled, and defined entirely by its dependency relationship to a specific line of reasoning |

**Is the distinction semantic or merely linguistic? Semantic.** The decisive test, comparing the first and third examples: remove the Decision/reasoning that "management executes successfully" supports, and there is no longer any reason to track it *as an Assumption* — it would simply become a general belief, structurally closer to a Judgment. "Management quality is strong," by contrast, needs no supporting Decision to remain relevant. **The distinguishing test: does the proposition's own relevance depend on a specific, active piece of reasoning (Assumption), or does it stand as a general characterization regardless of any specific reasoning (Judgment)?** A real, evidence-grounded distinction, not a wording accident.

---

## Phase 9 — Assumption vs. Conclusion — Reuse as Premise

Can something concluded earlier become a later premise? Plausibly, functionally, yes — an investor might draw a Conclusion in one review ("FCF margins have structurally improved") and, in a later Decision, rely on that same content as a premise ("assumes structural margin improvement persists"). **Does the ontology change?** No — per this series' immutability principle, the original `Conclusion` remains exactly what it was; it does not transform into an `Assumption`. **Does reuse require a new object, or a reference to the prior Conclusion?** A new `Assumption` object is created (new statement, new identity); it *could*, but need not, informally reference the prior Conclusion. Nothing found in this investigation makes such a cross-reference unavoidable, so per the phase's own instruction, none is designed here — the relationship remains purely presentational, exactly as most cross-references in this object family already are (Phase 4, Phase 5).

---

## Phase 10 — Hypothesis → Conclusion: Is There a Formal Transition?

Structurally: `Conclusion.evidence_id` requires an `Evidence` record; `Evidence` has no reference to `Hypothesis` at all (Phase 4). **There is no structural, enforced chain from Hypothesis through Evidence to Conclusion.** `Hypothesis` sits entirely outside this chain at the object level, exactly matching its own docstring: "immutable, and introduces no relationship to Observation, Decision, DecisionContext, or Evidence: this aggregate is deliberately standalone."

**Is "Hypothesis becomes Conclusion" semantically valid? No** — for the same reason established throughout this series: an existing `Hypothesis` cannot mutate. "Becoming" always means a new object is captured, informed by but not identical to the old one. A `Conclusion` might happen to validate or reject a prior `Hypothesis`'s content, but this is a content relationship, informal and textual, never a structural transformation.

**Conclusion: Atlas does not have a formal, enforced Hypothesis→Evidence→Conclusion pipeline at the domain-object level.** This directly matches OE-002 §6's own explicit statement about its own six-object subset: "This document does NOT establish a mandatory sequence, chain, or required ordering... Any apparent workflow association between Domain Objects reflects common usage, not an architectural requirement of this model." Tested here directly against the actual entity code for the *four* objects outside OE-002's own set, the same finding holds independently.

---

## Phase 11 — Conclusion → Judgment: Testing the Four Models

| Model | Verdict |
|---|---|
| A — Conclusion mechanically produces Judgment | **Fails** — no code path anywhere converts a `Conclusion` into a `Judgment`; `Judgment.capture()` takes a `characterization` and an optional `subject` reference, never a `Conclusion` as input |
| **B — Judgment can reference Conclusion but is independently authored** | **Survives** — `Judgment.subject` could, in principle, reference a `Conclusion` (target type unrestricted, per OE-002 §5.2/§5.4), but nothing requires this, and `Judgment` is fully valid with `subject=None` |
| C — Judgment is unrelated to Conclusion | Too strong — B shows a real, optional, possible reference |
| D — Judgment is a special kind of Conclusion | **Fails** — the direct merge test in Phase 7 already found two independent structural blockers |

---

## Phase 12 — Assumption → CaseCondition (Not Reopening CaseCondition Itself)

Testing whether Atlas can meaningfully monitor each object, against `CaseCondition`'s own already-settled defining purpose (`Investigation-006` Phase 1: "informing whether the reasoning behind a Decision remains sound"):

- **Hypothesis?** Structurally possible (nothing forbids a free-text `CaseCondition` about a hypothesis's content), but not well-motivated — a `Hypothesis` is explicitly not yet relied upon by anything (Phase 2); monitoring something nobody depends on doesn't fit the purpose.
- **Conclusion?** Same weak fit — a `Conclusion` is a past, immutable inference; what's worth watching is whether the *conditions that produced it* still hold, which reduces to watching the underlying Assumption or Evidence, not the Conclusion object itself.
- **Judgment?** Same reasoning — "watching a Judgment" really means watching whether the conditions that made the characterization reasonable still hold, again reducing to an Assumption- or Evidence-shaped underlying fact.

**Should CaseCondition only attach to Assumption?** As the *primary, well-motivated* case, yes — `CaseCondition`'s defining purpose most directly targets Assumptions, since Assumptions are by definition the things current reasoning depends on. Monitoring the other three is not forbidden by either ontology, but lacks the same tight fit. This confirms and sharpens, without reopening, both `Investigation-006`'s and `Investigation-007`'s own findings.

---

## Phase 13 — Reasoning Graph

**A correction, tested rather than assumed:** the candidate shape given in this investigation's own governing material states "Observation → Question → Hypothesis..." — this reverses the order every entity docstring read across this session actually states. `Question`'s own docstring: "the root of the Core Loop... the one node in the cycle with nothing upstream of it," and every other entity consistently names the sequence Question → Observation → Interpretation → Hypothesis → Evidence → Conclusion → Decision → Outcome → Evaluation → Learning. Correcting the ordering rather than silently reasoning from the wrong one.

Testing the corrected chain:

- **Is every arrow mandatory?** No — confirmed decisively. `Evidence` has no reference to `Hypothesis`; `Question` and `Observation` each explicitly reference nothing upstream or downstream. The named sequence is a workflow convention, not an enforced dependency graph — the same finding as Phase 10, now generalized to the whole chain.
- **Are arrows directional?** Only by naming/usage convention — not enforced by reference direction in code, since most adjacent pairs have no reference at all.
- **Can objects bypass stages?** Yes, trivially — nothing requires a prior stage to exist.
- **Does Assumption belong upstream or alongside?** **Alongside**, not upstream or downstream of any specific stage — per Phases 1, 3, and 9, an Assumption's defining trait is its relationship to *current reasoning-dependency*, not its position in an evidentiary pipeline. It sits alongside Decision's own reason/thesis, not as a node in the Observation→Learning chain.
- **Does Judgment belong downstream or orthogonal?** **Orthogonal**, confirmed by OE-002 §6 directly ("Judgment... MAY be roots of this structure or MAY reference another Domain Object") and by Phase 11's own Model B finding.

**Conclusion:** the "Core Loop" name describes a common usage pattern, not a structurally-enforced graph. This is independently confirmed both by testing the actual entity code (most adjacent pairs share zero cross-references) and by OE-002's own explicit disclaimer about its own, narrower six-object subset.

---

## Phase 14 — Truth and Confidence

| Object | Legitimate language |
|---|---|
| Assumption | Not true/false. Supported / challenged / uncertain (default). Never "settled," never flatly "rejected" — a challenged assumption remains historically true that it *was* held (`Investigation-007` Phase 8) |
| Hypothesis | Not true/false, not even structurally "supported/challenged" (no direction field, no evidence link). Only "uncertain" / "proposed" / "unresolved" apply — the weakest legitimate vocabulary in the family |
| Evidence | Not true/false — but *does* legitimately carry a structural "supports/challenges" direction relative to whatever it bears on — the only object in this family with a required, first-class directional field |
| Conclusion | Not true/false. "Concluded" / "drawn" — a fact about the reasoning process's own output, not a truth claim about the world |
| Judgment | Not objectively true/false — but uniquely entitled to "settled" among this family, per both the implemented docstring and OE-002's near-identical language, describing the Case's own stance, not objective truth |

**Does the ontology deliberately refuse a truth judgment? Yes, without exception, across all five.** This is not an oversight — each object's own docstring states this disclaimer *separately*, not inherited from a shared base class. A genuinely notable, deliberate, cross-cutting architectural discipline, confirmed to hold across the entire epistemic family, not merely asserted by this investigation.

---

## Phase 15 — Authorship

| Object | Creates the record | Owns the claim | ADR-002 C-02 integrated? |
|---|---|---|---|
| Assumption | Shared (Atlas proposes, investor confirms/edits) | Per C-02's model precisely | **Yes** — `Investigation-007` Phase 7 |
| Hypothesis | Investor exclusively | Investor | **No** — no authorship-transfer field exists |
| Evidence | Investor exclusively | Investor | **No** |
| Conclusion | Underspecified (Phase 5) | Underspecified | **No** |
| Judgment | Underspecified (Phase 6) | Underspecified | **No** |

**Testing ADR-002's authorship-transfer principles directly, as instructed:** C-02's own model (Atlas Suggested / User Accepted / Mixed / User Authored) was built specifically for Decision Workspace content, per `Investigation-006` Phase 8's own citation. **It has not been extended to, and does not naturally fit, the older Core Loop objects** — `Hypothesis`, `Evidence`, `Conclusion`, `Judgment` each predate it and describe a simpler, single-party authorship model with no Atlas-suggestion/acceptance mechanic at all. This is a real, disclosed authorship-model inconsistency: `Assumption` (new, per `Investigation-007`) explicitly adopts C-02; the four older objects were never designed to and do not today.

---

## Phase 16 — Atlas Memory Placement

| Object | Stored primitive | Reasoning input | Reasoning output | Read model | Presentation-only |
|---|---|---|---|---|---|
| Assumption | Yes (once built) | Yes — feeds `DE-005`'s thesis synthesis | — | — | — |
| Hypothesis | Yes | Yes | — | — | — |
| Evidence | Yes | Yes — to `Conclusion`, structurally | — | — | — |
| Conclusion | Yes | Yes, informally (Phase 9) | Yes — of Evidence-weighing | — | — |
| Judgment | Yes | — | Sometimes, or standalone (OE-002: nothing required) | — | — |

- **Case Memory:** `Judgment` fits most naturally (explicitly Case-scoped); the other four are narrower (Decision- or Evidence-anchored).
- **Decision Memory (`DE-005`):** `Assumption` fits directly, per `Investigation-007` Phase 13's own strong finding — none of the other four have an established `DE-005` hook.
- **Knowledge / Reasoning (`KnowledgeReference`/`ReasoningTrace`):** none of the five *are* either — but any of the five could be the *target* one of those references, since both have unrestricted target types per OE-002.
- **Learning:** unrelated — downstream of `Evaluation`→`Outcome` only.
- **Reflection:** unrelated — occasioned by Pattern/Coaching, per `Investigation-002`.
- **Daily Brief:** only meaningful transitions (e.g., an Assumption Challenged event) would ever surface here, per the narrow-projection boundary already established across `Investigation-005`/`006`/`007` — never raw Hypothesis/Evidence/Conclusion/Judgment content.
- **Investment Case:** the current product surface already displays *derived, presentation-only* content (strengths, risks, valuation assumptions as plain text) that draws on this family conceptually, but none of these five domain objects is today wired into what it actually displays — consistent with every prior investigation's repeated finding that the Core Loop remains unwired to Alpha.

---

## Phase 17 — Existing Ontology Duplication Test

Genuinely testing, not defending, whether Assumption is unnecessary:

| Candidate replacement | Fails because |
|---|---|
| Hypothesis | Phase 2/3's real epistemic-stance difference — forcing Assumption content into Hypothesis means Atlas assigns "no truth value, confidence, or conviction" to something reasoning *actively depends on*, contradicting Assumption's own defining role |
| Conclusion | Phase 5/7 — Conclusion structurally requires an Evidence anchor; many real Assumptions (UX-009's own examples) are stated premises, not conclusions drawn from one specific evidentiary record |
| Judgment | Phase 8's decisive test — Judgment is reasoning-independent; Assumption is reasoning-dependent by definition. Forcing the fit loses the "actively depended upon by *this* reasoning" relationship entirely |
| KnowledgeReference | Reference-shaped, not proposition-shaped (`Investigation-007` Phase 5, reconfirmed) |
| ReasoningTrace | Same reference-collection shape mismatch |
| DecisionContext | Currently has no assumptions field, captured once with no lifecycle, differently-shaped fields (`Investigation-007` Phase 5) |
| CaseCondition | Not every Assumption needs an evaluation lifecycle — wasteful for the majority never actively tracked (`Investigation-007` Phase 6) |
| Free text on `Decision.reason` | Loses individual identity, trackability, and challenge history entirely (`Investigation-007` Phase 16, Model A) |

**No existing object satisfies Assumption without semantic distortion. `Investigation-007`'s conclusion is not merely left alone — it is independently reconfirmed** by genuine testing against every plausible substitute, differently angled from `Investigation-007`'s own testing.

---

## Phase 18 — Alternative Epistemic Models

| Model | Verdict |
|---|---|
| A — Linear pipeline, Assumption before Hypothesis | **Fails** — Phase 10/13 already found no enforced linear pipeline exists; ranking Assumption "before" Hypothesis misrepresents Phase 13's own finding that Assumption sits alongside, not upstream of, the chain |
| **B — Reasoning graph, independent typed nodes with optional relationships** | **Matches everything found** — not a new model, a description of what Phase 10/13's own testing already confirms is how the implementation actually behaves |
| C — Assumption as accepted Hypothesis, no distinction after acceptance | **Fails** — Phases 2, 3, and 8 collectively show the epistemic-stance difference (reasoning-dependency vs. candidate-testing) persists and matters even after "acceptance" |
| D — Judgment as accepted Conclusion, one lifecycle | **Fails** — Phase 7's direct merge test found two independent structural blockers |
| E — Minimal ontology (Hypothesis+Evidence+Conclusion only; Assumption/Judgment presentation-only) | **Fails for Assumption** — cannot support the Challenged/Retired lifecycle or the `DE-005` integration Phase 16 confirms is genuinely available. **Fails for Judgment too** — OE-002 formally adopts Judgment as one of exactly six permanent, normative Domain Objects; demoting it to presentation-only would directly contradict OE-002's own Final-status classification, a real, disclosed tension worth naming rather than smoothing over |
| **F — Existing ontology plus separate Assumption, unchanged otherwise** | **Matches every finding across all 17 prior phases** — no existing object needs modification, no merge succeeds, Assumption survives independently, Model B already describes current reality accurately |

---

## Phase 19 — Consistency Test

Challenging Models B/F together, documenting rather than resolving:

- **vs. Decision:** no contradiction — untouched.
- **vs. Draft:** no contradiction, a positive integration point — assumption/hypothesis/evidence content could originate as draft content.
- **vs. DecisionContext:** no contradiction — clean division of labor (`Investigation-007`).
- **vs. Reflection:** no contradiction — unrelated origin story.
- **vs. CaseCondition:** no contradiction — the same loose, optional cross-reference already established, now confirmed as primarily well-motivated for Assumption specifically (Phase 12), not equally so for the other three.
- **vs. Outcome:** no contradiction — unrelated, backward-looking.
- **vs. Evaluation (Core Loop):** **the same naming-collision risk, now confirmed for a fifth angle** — the generic English verb "evaluate" could informally describe assessing any of these five objects, while Core Loop's own `Evaluation` object is narrowly Outcome-anchored. A systemic vocabulary risk across the whole epistemic family, not an Assumption-specific one.
- **vs. Learning:** no contradiction — unrelated, terminal node.
- **vs. Observation / Question:** no contradiction — both independently confirmed standalone by their own docstrings, extending the "deliberate non-linkage between adjacent Core Loop objects" pattern found now to be the *rule*, not the exception, across the whole family.
- **vs. KnowledgeReference / ReasoningTrace:** no contradiction — disjoint shape, reconfirmed.
- **vs. Recommendation:** no contradiction — architecturally separate; none of these five feed it structurally today, since all are unwired to Alpha (every prior investigation's repeated finding).
- **vs. Daily Brief:** consistent, given the narrow-projection boundary is respected.
- **vs. imported Decisions:** no contradiction — none of these five is required by any Decision, per OE-002 §6's own explicit "no mandatory sequence" finding, generalized from Assumption alone (`Investigation-007`) to the whole family here.
- **vs. provider-derived evidence:** **a genuinely sharpened, new question.** If `Evidence` is ever provider-synchronized (automatically ingesting a data provider's own reported figures), does provider-sourced Evidence carry the same `direction` semantics investor-entered Evidence does — and does "the investor regarded this as evidence" (`Evidence`'s own defining phrase) remain honestly claimable when no investor personally reviewed it? More precise than `Investigation-006`'s general framing of this question, not resolved here either.
- **vs. future collaboration:** the same inherited Case-scoping ambiguity, now named a **sixth** time across this series.
- **vs. future automated reasoning:** **a genuinely new question for this investigation.** If Atlas itself, not the investor, someday formulates a `Hypothesis` or draws a `Conclusion` fully automatically, does the family's uniform "the investor's own account of when..." framing (used verbatim or near-verbatim in `Hypothesis.formulated_at`, `Evidence.observed_at`, `Observation.observed_at`, `DecisionContext.captured_at`) remain valid, or does it silently assume a human author a future automated-reasoning capability would violate? Genuinely unresolved, surfaced here for the first time in this series.

**Three tensions worth flagging as genuinely new, beyond restated/inherited ones:** (1) provider-synchronized Evidence's authorship-honesty question; (2) automated reasoning's challenge to the whole family's "investor's own account" framing; (3) the authorship-model inconsistency between C-02-integrated Assumption and the four older, C-02-unaware objects (Phase 15).

---

## Phase 20 — Final Decision

**`KEEP_ALL_DISTINCT`**

- **Assumption:** a reasoning-dependent premise, provisionally accepted, tracked for support/challenge, never truth-verdicted.
- **Hypothesis:** a reasoning-independent, unresolved candidate explanation — no truth, confidence, or conviction assigned at all, the weakest epistemic commitment in the family.
- **Evidence:** investor-regarded informational content bearing a required direction (supports/challenges) relative to a line of reasoning, never proof.
- **Conclusion:** an investor-drawn inference, mandatorily anchored to exactly one Evidence record, the output of evidence-weighing, never a truth claim.
- **Judgment:** a settled, Case-wide characterization, independent of any specific reasoning chain, optionally referencing anything or nothing.
- **Epistemic ordering — mandatory or merely possible?** Merely possible. Confirmed decisively (Phase 10, 13): the only structurally *enforced* link found anywhere in this entire five-object family is `Conclusion`'s mandatory `Evidence` anchor. Everything else — including the named "Core Loop" sequence itself — is a usage convention, not an architectural requirement, directly matching OE-002 §6's own explicit disclaimer about its own, narrower subset.
- **Does `Investigation-007` survive unchanged?** **Yes — independently reconfirmed**, via Phase 17's genuine, non-defensive testing against every plausible substitute, not merely left standing by default.

---

## ADR Candidate (Outline Only)

**Problem:** Atlas contains several epistemic objects — Assumption, Hypothesis, Evidence, Conclusion, Judgment — whose ordinary-English meanings overlap, risking accidental duplication or conflation.

**Context:** The implemented `atlas/core/` Core Loop and the separate, pre-implementation "Atlas Reasoning Foundations" ontology track (home to OE-002's closed six-object set and a differently-emphasized Final-status Judgment definition) are explicitly, per `ADR-005`, not governing or converged with one another — this ADR's own scope is the implemented objects only, and it does not attempt or authorize reconciling the two tracks. Within the implemented objects, testing every pairwise relationship found a coherent, if loosely-coupled, structure: each object plays a genuinely distinct epistemic role, none merges cleanly with any other, and the "sequence" implied by the Core Loop's own name is a naming/usage convention, not an enforced graph.

**Decision:** Keep Assumption, Hypothesis, Evidence, Conclusion, and Judgment as five distinct objects. Model their relationships as a loosely-coupled reasoning graph (Model B/F), never a mandatory pipeline. `CaseCondition` primarily, though not exclusively, targets Assumption. `Assumption` is the only member of this family integrated with `ADR-002` C-02's authorship-transfer model; this gap for the other four is disclosed, not closed, by this decision.

**Invariants (illustrative, not binding — no schema decided here):**
- No object silently changes type — a Hypothesis "becoming" an Assumption, or a Conclusion "becoming" a Judgment, is always a new capture, never a mutation.
- Historical claims remain immutable across all five, without exception.
- Provisional (Hypothesis, Assumption) ≠ accepted-as-settled (Judgment) — a real, tested epistemic-stance distinction, not a wording accident (Phase 3, 8).
- Derived (Conclusion, from Evidence) ≠ assumed (Assumption, a premise reasoning starts from or stands on) — different directions in the reasoning process.
- Settled characterization (Judgment) ≠ derived conclusion (Conclusion) unless a future, explicit design proves otherwise — the Phase 7 merge attempt failed on two independent structural grounds and is not resolved by this ADR.
- Evidence does not automatically prove a claim — it carries a direction (supports/challenges), never a verdict, across every object it might inform.

**Consequences:**
- **Reasoning:** the graph shape (Model B) should govern how any future implementation connects these objects — optional, typed references, never an enforced sequence.
- **Decision Workspace:** `Assumption`'s content maps directly onto UX-009's own Section 4/9 fields; the other four remain unwired to Alpha today, consistent with every prior investigation's finding.
- **Atlas Memory:** `Assumption` has a genuinely strong, already-anticipated `DE-005` integration point; `Judgment` fits Case Memory; the other three remain narrower, less-integrated primitives.
- **CaseCondition:** primarily, not exclusively, watches Assumptions — a refinement, not a reopening, of `Investigation-006`.
- **Daily Brief:** only meaningful transitions across any of these five objects should ever surface there, never raw content.
- **Future AI reasoning:** the whole family's "investor's own account" authorship framing does not yet anticipate Atlas itself as an author — a real, disclosed gap for any future automated-reasoning capability.

**Rejected Alternatives:** A (linear pipeline — no such enforcement exists); C (Assumption as accepted Hypothesis — the epistemic-stance distinction persists after acceptance); D (Judgment as accepted Conclusion — fails on two independent structural grounds); E (minimal ontology, Assumption/Judgment presentation-only — contradicts both the DE-005 integration evidence and OE-002's own normative Judgment classification).

**Migration/Compatibility:** None required to any existing object. Fully additive, if and when `Assumption` is actually implemented per `Investigation-007`.

**Open Questions** (carried forward, not resolved here):

1. Should the authorship-model gap between C-02-integrated Assumption and the four older, C-02-unaware objects (Hypothesis, Evidence, Conclusion, Judgment) ever be closed, and if so, how? (Phase 15)
2. Does provider-synchronized Evidence honestly satisfy "the investor regarded this as evidence"? (Phase 4, 19)
3. What happens to this whole family's "investor's own account" authorship framing if Atlas itself ever originates a Hypothesis or Conclusion? (Phase 19)
4. Should the OE-002/Reasoning-Foundations track and the implemented `atlas/core/` objects ever be reconciled — and if so, whose definition of Judgment governs? Explicitly not decided by `ADR-005`, not decided here either, and not this investigation's to resolve.
5. Should a future `ReasoningTrace` formally connect Assumption, Hypothesis, Evidence, Conclusion, and Judgment where an investor chooses to relate them, given all four pairwise "no direct link" findings (Phase 4, 5, 9)? Not designed here, per this investigation's own "do not design cross-references unless unavoidable" instruction — nothing found made one unavoidable.

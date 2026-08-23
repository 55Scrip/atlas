# ADR Investigation 10 — Ontology Reconciliation Process

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document. This investigation does not reconcile any ontology — it determines the *process* by which Atlas should reach legitimate architectural authority when tracks disagree.

**Central question:** How should Atlas decide which architectural truth becomes authoritative whenever multiple architectural tracks disagree?

**Method:** Read fresh — `docs/atlas_domain_object_architecture/Doctrine.md`, in full for the first time in this series (previously only grepped in `Investigation-009`). This single document turns out to already contain a remarkably complete, internally rigorous answer to nearly every phase of this investigation — sections on normative authority (§9), publication/amendment/supersession (§10, §14), historical integrity (§11), architecture/implementation separation (§12), the Change Protocol (§13), and forcing functions for reopening (§8). `ADR-005`, `OE-002`, `atlas_reasoning_foundations/Doctrine.md`, `CoreLoopATLAS001.md`, and `ADR-001`/`ADR-002` (Reasoning Foundations) remain as read fresh in `Investigation-008`/`009` and are cited, not re-read line by line, where their content is unchanged. Every prior investigation's conclusion is treated as established unless directly contradicted; none was found to be.

**A distinction that governs this entire document, stated up front:** `Investigation-009` found that Track 3's *content* claim (OE-002's closed six-object set binds implementation) has not been accepted anywhere. This investigation asks a different question: independent of whether that specific content claim is accepted, is Track 3's own governing *method* — its process for investigating, deciding, superseding, and preserving history — nonetheless the best available answer to "how should Atlas reconcile disagreement," adoptable as a cross-track process without thereby also adopting OE-002's specific conclusions as binding? **Testing this directly across the phases below, the answer is yes** — the method and the content are separable, and only the method is recommended here.

---

## Phase 1 — What Does "Architectural Authority" Mean?

| Kind | What it governs | Where claimed |
|---|---|---|
| Philosophical | What a thing fundamentally *is*, argued from first principles | Track 2 (Reasoning Foundations) exclusively |
| Ontological | Which categories/objects genuinely, distinctly exist | Tracks 2 and 3, by different methods |
| Architectural | How components relate, their responsibilities | Track 3, explicitly separated from implementation (§12: "architecture determines what must be represented") |
| Implementation | How something is represented operationally | Track 1 exclusively — and, per Track 3's own §12, implementation is *never* claimed as an ontological authority even by the track that most engages with it |
| Operational | Whether something actually runs, is tested, is used | Track 1 only — no doctrine track addresses this directly |
| Historical | What was decided, when, on what grounds | Track 3, precisely defined (§11): authority "extends only to the fact that a decision occurred... never to what the architecture currently states" |
| Documentary | The mere existence of a document describing something | **Explicitly insufficient on its own**, per Track 3 §3: a category is not accepted merely because "it appears in a workflow or process description" |

**Must exactly one authority always exist?** No, not across independent chains. Track 3's own §9 states every fact must have exactly one authoritative home "among the normative documents" — this is a rule *within* one coherent dependency chain, not a claim that only one chain may exist. `Investigation-009` already established three independent chains exist; each may (and, within itself, per §9, should) have a single internal authority, without there being one authority across all three until an explicit reconciliation merges them.

---

## Phase 2 — What Constitutes an Authoritative Source?

Testing each candidate against Track 3's own explicit rules (the only track that states this precisely) and Track 2's parallel discipline:

| Candidate | Legitimate on its own? |
|---|---|
| Implementation | No, for ontology — explicit, repeated (§2, §12). Yes, definitionally, for *runtime behavior specifically*, since Track 1 has no other candidate. |
| ADR (Draft/Final, either track's discipline) | Yes, once genuinely tested — Track 2's falsification method or Track 3's Decision Standard (§6) |
| Doctrine | Yes — the highest authority within its own chain |
| Architecture/OE document | Yes, subordinate to its own Doctrine |
| Design document / implementation design | **No, explicitly** — `Investigation-009`'s own citation of `Decision-Implementation-Design.md`'s self-disclaimer ("not a normative document") applies directly |
| Migration document | **No, explicitly** — same self-disclaiming pattern found for the Reconciliation Plan |

**Which documents may legitimately establish architecture?** Only documents belonging to a defined, Doctrine-governed chain, carrying an explicit status (Draft/Final, or equivalent), produced through that chain's own required investigative discipline. Engineering artifacts — however numerous and however carefully written, and Track 3's own ecosystem contains dozens — explicitly do not qualify, by their own stated terms.

---

## Phase 3 — Should Implementation Ever Establish Ontology?

Testing Track 3's own flat "no" (§2, §12) against the evidence, rather than accepting it by default:

Tested directly against `Investigation-009` Phase 11: every object in Track 1 — Decision, Observation, Hypothesis, Evidence, DecisionContext, ReflectionResponse, KnowledgeReference, ReasoningTrace, Judgment — was built and shipped either before either doctrine track existed in its current form, or independently of it. **If "implementation must never establish ontology" is read as an absolute, retroactively-applied rule, it invalidates the legitimacy of the entire Track 1 object set as it stands today** — a conclusion `Investigation-009` Phase 14 already found untenable when testing the same claim from the authority-conflict angle.

**The candidate that survives:** implementation *may* establish a working, provisional ontology in the absence of any doctrine-governed alternative — but such a provisional ontology does not thereby become immune to later, doctrine-governed reconsideration, and must not be mistaken for having passed through either track's own falsification or justification discipline. This explains how Track 1 legitimately reached its current state (nothing else existed to consult) without claiming implementation is a rigorous ontology-generating authority in the sense Tracks 2 and 3 claim for themselves.

---

## Phase 4 — Can Ontology Invalidate Implementation?

Two different senses must be separated:

- **Can ontology declare the implementation's past existence illegitimate?** No — directly contradicted by Track 3's own §11: "A historical record MUST NOT become a competing source of current normative truth... A later amendment MUST NOT rewrite the historical fact that the prior norm was once adopted." Nothing in any track's own treatment of *its own* history tolerates retroactive erasure; applying a harsher standard to Track 1's history than any track applies to itself would be inconsistent.
- **Can ontology require implementation to change going forward?** Yes, in principle — but only through the full Change Protocol (§13: investigation → decision → amend upstream → amend dependents → historical record → navigational alignment → repository inspection → migration planning → implementation), never by unilateral doctrinal assertion. **Ontology can eventually require implementation to change, but only through a completed reconciliation process — never by mere claim of authority.**

---

## Phase 5 — What Should Happen When Implementation and Ontology Disagree?

| Alternative | Verdict |
|---|---|
| Implementation wins unconditionally | Too strong — permanently devalues real, rigorous work in Tracks 2/3, contradicted by `Investigation-009`'s own finding that Track 2's rigor "may become more relevant, not less" for future automated reasoning |
| Ontology wins unconditionally | Too strong — would retroactively invalidate ten real, running, load-bearing objects with no reconciliation ever having occurred, violating Track 3's own §11/§12 |
| Newest wins | Fails directly — Track 3 §9 explicitly rejects date-based authority |
| Repository wins | Same failure as "implementation wins" |
| **Explicit reconciliation required** | Matches Track 3's own Change Protocol almost exactly, and matches `Investigation-009`'s own recommendation of an `ADR-005`-equivalent for Track 1 ↔ Track 3 |
| **Temporary divergence permitted** | Not mutually exclusive with the above — Track 3's own §7 (settled-in-one-respect, open-in-another) and §14 (Draft status: "not yet a stable basis for dependent work") already build in exactly this tolerance |

**The surviving, combined answer:** explicit reconciliation is the required *eventual* step before a disagreement can be considered resolved — but honestly-disclosed, temporary divergence is legitimate in the meantime, exactly as this entire investigation series has already, repeatedly, practiced (documenting contradictions "without resolving them" in every prior investigation's own Consistency Test phase).

---

## Phase 6 — What Evidence Is Legitimate During Reconciliation?

| Candidate | Status |
|---|---|
| Running code | Legitimate for fact-finding ("Repository inspection MAY be performed earlier... for fact-finding purposes," §13); **not** legitimate as the ground for an ontological conclusion (§13: "Its findings MUST NOT determine the ontological conclusion") |
| Tests | Same status as running code |
| ADRs | Legitimate, if genuinely tested by falsification (Track 2) or reasoned per the Decision Standard (Track 3 §6) |
| Doctrines | Legitimate — the highest authority within their own chain |
| Implementation/commit history | Same status as running code — informs, does not decide |
| User behaviour | **Not addressed by either doctrine.** Reasoned here: further from ontological evidence than implementation itself, since it reflects product usage, not conceptual necessity — legitimate only for informing *which* reconciliation to prioritize, never as ontological evidence itself |
| Architecture principles (a track's own Doctrine-level reasoning) | The most legitimate category — precisely what both tracks' own methods treat as dispositive |

---

## Phase 7 — What Is a Contradiction?

Not directly answered verbatim by either Doctrine, though Track 3's own status vocabulary (§14) gets close. Reasoned here, tested against real examples already found in this series:

- **Contradiction:** two claims, both currently claiming settled status *within their own scope*, that cannot both be true of the same fact. The clearest example found across this whole series: OE-002 §4's explicit closure claim ("No other Domain Object is part of this model") directly, textually conflicts with Track 1's ten additional objects' continued, successful existence. This is a genuine contradiction because OE-002 makes an *explicit closure claim* — most other cross-track differences do not.
- **Omission:** a track simply never having addressed a concept (Tracks 2/3 saying nothing about Hypothesis, Evidence, Conclusion) — not a contradiction, since nothing asserted conflicts; a gap, not a conflict.
- **Alternative model:** two tracks address the *same* question with different, non-merged, internally coherent accounts, neither shown false (Track 2's Reasoning-as-capability vs. Track 1/3's silence on the concept) — closer to omission from one side, a genuine competing account from the other.
- **Incomplete work:** a Draft-status document — explicitly not yet binding, explicitly permitted open questions (§7) — not a contradiction by definition, since its own status discloses provisionality.
- **Implementation lag:** a Final ontological decision exists, implementation hasn't caught up — explicitly anticipated and permitted (§12: "a settled architectural decision MAY be published before any corresponding implementation exists") — an ordinary, expected state, not a contradiction.
- **Experimental work:** exploratory investigation (this series' own documents, or Track 3's own numerous Discrepancy/Reconciliation investigations) — disclaims normative status of its own accord, never a contradiction, since it makes no competing authority claim.

**A sharpened, load-bearing finding:** most of what looks like disagreement across Atlas's three tracks is actually omission or alternative-model territory, not true contradiction — precisely because Track 1 asserts no closure claim of its own (it simply *has* objects, without claiming "and no others may exist"). Judgment's three definitions (`Investigation-008`/`009`) remain genuinely ambiguous under this test — Track 2's Act-dependency could be read as either a contradicting claim or a compatible refinement, and this investigation does not force a resolution either way, per its own governing instruction to disclose rather than paper over.

---

## Phase 8 — What Constitutes Reconciliation?

Tested against Track 3's own Change Protocol (§13) and, critically, against `ADR-005` as a **real, already-completed example** of reconciliation:

Reconciliation's minimum required output, per §13 step 5, is always at least a documented decision (a historical decision record). Beyond that minimum, reconciliation *may*, but need not, change ontology, implementation, or both. **`ADR-005` is direct, real evidence that reconciliation does not require either side's content to change at all** — it concluded with a formal, mutual "neither governs the other" declaration, changing *only the declared authority relationship*, leaving both tracks' actual content fully intact. This is an important, evidence-grounded finding: reconciliation's minimum viable output is a declared-authority document, not necessarily a content merge.

---

## Phase 9 — Can Reconciliation Occur Incrementally?

Yes, both by explicit doctrinal permission and by demonstrated practice. Track 3's own §7 explicitly permits partial settlement ("MAY be settled in one respect while retaining... open questions in another respect... MUST NOT... block publication of the settled core"), and §8 requires any reopening to use "the narrowest scope of reconsideration required" — a direct rejection of any implied global-consistency mandate. `ADR-005` itself is a further, working example: it reconciled exactly one pairwise relationship (Track 1 ↔ Track 2) without attempting to also address Track 3, which it does not even mention. **Incremental, pairwise reconciliation is not merely theoretically permitted — it is the only kind that has actually happened.**

---

## Phase 10 — How Should Supersession Work?

Precisely answered by Track 3's own §14: **Superseded** is a formal status ("no longer the current norm, replaced by an *identified* later decision... A superseded norm remains a true historical record of what was once adopted"). Supersession requires an identified replacing decision — not merely "this feels outdated" — and the former document's status changes explicitly to Superseded; it is never silently deleted or left ambiguously Final. Retirement (**Historical** status) applies whenever content is "preserved as a record of a past decision; not currently normative" — worth reading, never worth citing as current architecture. **The precise rule: a document transitions to Superseded the moment a later, genuinely-reconciled decision replaces its specific claim — never merely because a newer document exists** (§9 explicitly rejects recency as an authority criterion) — and the superseded text itself must never be edited or erased, only its status flag changed.

---

## Phase 11 — What Historical Record Must Always Be Preserved?

Directly answered, Track 3 §11: what was decided; when; the alternatives considered; the grounds for rejecting each; the normative consequences produced; the decision-specific reopening condition. "A historical record MUST NOT become a competing source of current normative truth," but must remain permanently recoverable.

**Applied directly to this investigation series itself:** every one of `Investigation-001` through `009`, and this one, should remain permanently readable — even if a future, more authoritative reconciliation someday supersedes some of their specific conclusions, none should ever be deleted, only marked Superseded with the superseding document named explicitly, exactly as `Investigation-006`/`007`'s own carried-forward open questions already anticipate.

---

## Phase 12 — Can Architecture Legitimately Fork?

**Yes — this has already, legitimately happened.** `Investigation-009` found three independent, non-converged tracks, one of which (Track 1 ↔ Track 2) carries explicit, mutual, documented permission to remain forked indefinitely (`ADR-005`).

**Conditions for legitimacy, tested against the evidence:** (1) each fork maintains its own internal consistency (both Tracks 2 and 3 do, per their own respective Doctrines); (2) the fork is *named and disclosed*, not hidden — exactly what `ADR-005` did for Tracks 1/2, and what `Investigation-009` did, for the first time, for Tracks 1/3; (3) neither side silently treats the other as superseded without the actual Change Protocol having run (satisfied — no track claims to have superseded another).

**Illegitimate forking, by contrast, is disagreement without disclosure**, or one side silently acting as though it had already won. This was precisely Track 1 ↔ Track 3's condition *before* `Investigation-009` named it. Naming an undisclosed fork is itself a step toward making it legitimate.

---

## Phase 13 — Should Atlas Eventually Have Exactly One Governing Ontology?

**For "yes":** Track 3's own §9 (one authoritative home per fact) is compelling for long-term simplicity, and becomes materially more valuable if Atlas ever builds automated reasoning — `Investigation-009` Phase 18 already found Track 2's philosophical rigor "may become more relevant, not less" in exactly that scenario, and an automated reasoner would benefit enormously from one unambiguous ontology to reason from rather than three.

**For "no":** `ADR-005`'s own wording frames Track 1 ↔ Track 2's non-convergence as genuinely open-ended, not a temporary state awaiting resolution — "Whether any relationship between them will exist in the future is explicitly undecided... and is not to be inferred." Different tracks may legitimately serve different purposes (Track 2's depth for a different audience than Track 1's ship-fast discipline) that do not need merging, and forcing premature convergence risks damaging both — consistent with the same anti-premature-complexity spirit found throughout both Doctrines ("Complexity Must Be Discovered, Never Introduced," Track 2; §3's burden-of-justification, Track 3).

**Conclusion, surviving both tests, stated as a conditional, not a flat answer:** not immediately, and not by mandate — but likely yes, eventually, for the specific, narrow purpose of any future automated-reasoning capability that needs a single ontology to operate against — while plurality remains legitimate and low-cost for everything else in the meantime, until a genuine forcing function (§8's own vocabulary) arises.

---

## Phase 14 — Governance Models

| Model | Verdict |
|---|---|
| A — Implementation-first | Matches `Investigation-009`'s own conclusion. Strength: zero disruption, matches current practice. Weakness: permanently undervalues Tracks 2/3's real work; doesn't build toward Phase 13's own eventual automation need |
| B — Ontology-first | Matches Track 3's own self-claim. Strength: rigorous, prevents drift. Weakness: retroactively delegitimizes ten real objects if read as retroactive — but the *correct* reading of "ontology-first," per Track 3's own §12, is prospective (govern what's built next), never retroactive (invalidate what already exists) — a nuance worth stating precisely rather than rejecting the whole model |
| C — Documentation-first | Fails immediately — directly contradicted by §9 ("not by which document is more recent, where a document is located") |
| D — Explicit reconciliation authority | Matches Phase 5/8's converging finding — a dedicated, ongoing *process* for producing `ADR-005`-style pairwise resolutions, modeled on Track 3's own already-well-designed Change Protocol, applied across tracks rather than only within Track 3's own chain |
| E — Living architecture | Closest to Track 1's own actual historical behavior (`Investigation-009` Phase 11) — but alone, with no reconciliation discipline, it is exactly the condition that let the Track 1 ↔ Track 3 fork go unnoticed until `Investigation-009`. Living architecture without a reconciliation practice risks the silent drift both Doctrines exist to prevent |
| F — Independent parallel tracks | Matches the current, actual state — legitimate per Phase 12, if disclosed; illegitimate if silent |
| **G — Disclosed Pluralism with an Explicit Reconciliation Process** | **A synthesis of D + F + a narrow, prospective-only reading of B**, detailed below |

**Model G, in full:** tracks remain independently governed (F) unless and until a specific, demonstrated forcing function (Track 3's own §8 vocabulary) makes reconciliation necessary, at which point a dedicated, `ADR-005`-style process (D) is invoked, using Track 3's own Change Protocol (§13) as the *method template* — borrowing the discipline without pre-committing to Track 3's own *content* winning. Newly-authored, forward-looking ontological work (this series' own future continuations) should increasingly consult, and where practical align with, whichever track's reasoning is most rigorous for the specific question at hand — a narrow, practice-level echo of B, applied only prospectively, never retroactively.

---

## Phase 15 — Consistency Test Against Existing Atlas Architecture

Testing Model G against each named item — does it correctly accommodate the item's current status without requiring immediate, disruptive change?

- **Core Loop:** accommodated — Track 1, informally governed (Model A/F), unchanged.
- **Domain Objects (OE-002's six + Track 1's ten extra):** accommodated — the extras remain valid under Track 1's informal governance; OE-002's six remain valid under Track 3; the genuine contradiction (OE-002's closure claim, Phase 7) is named, not hidden — Model G does not resolve it, only correctly classifies it as pending explicit reconciliation.
- **Reasoning Foundations:** accommodated — `ADR-005` is itself a worked example of Model G already in successful, real operation.
- **Domain Object Architecture:** accommodated — its own authority claim is now explicitly named (`Investigation-009`) rather than silently unexercised; Model G neither retracts nor accepts the claim, consistent with Phase 5's finding.
- **ADR process / OE process:** both preserved unchanged, each governing its own track.
- **Decision, Case:** consistent, closely-matching definitions across all three tracks — no tension to accommodate.
- **Draft, CaseCondition, Assumption:** none produced by either formal Doctrine track — produced instead by *this investigation series itself*, using a method (systematic, evidence-cited, falsification-adjacent) closer to Track 3's rigor than Track 1's ad hoc engineering, but formally under neither Doctrine. **This surfaces an honest, important, previously-unstated fact: this ten-investigation series is itself a fourth, unacknowledged quasi-track**, not yet reconciled with any of the other three — Model G must account for its own series' status, not only the three tracks it started by naming.
- **Security Confirmation:** Alpha-only, engineering-sprint-governed exactly like Track 1's other objects — same treatment, no new tension.
- **Atlas Memory, Daily Brief, Change Intelligence:** none formally defined by any of the three tracks (`Investigation-009` Phase 15, reused) — trivially accommodated, since no track claims authority over them to begin with.

---

## Phase 16 — Unresolved Tensions, Disclosed Honestly

1. **OE-002's own closure claim directly, textually contradicts Track 1's ten extra objects' continued existence** — the clearest true contradiction found across this whole series, per Phase 7's own sharpened test, still fully unresolved by this investigation.
2. **This investigation series itself (`Investigation-001`–`010`) is an unacknowledged fourth quasi-track**, methodologically novel, not reconciled with any of the other three, its own future authority status undetermined.
3. **Judgment's three definitions remain genuinely ambiguous** — contradiction or compatible refinement — not resolved here, consistent with `Investigation-008`/`009`'s own disclosure rather than forced resolution.
4. **Phase 13's "eventually, for automation" conclusion is speculative**, untested against any concrete automation proposal — a real uncertainty, not a settled forecast.
5. **No owner has been identified anywhere in any document read across this series for actually initiating the recommended Track 1 ↔ Track 3 reconciliation** — a real, practical, unresolved gap: who does this work, and when?

---

## Phase 17 — Preferred Governance Model

**Model G — Disclosed Pluralism with an Explicit Reconciliation Process.**

Justified from the cumulative findings above: it is the only model tested that (a) matches the one already-completed, real-world reconciliation this repository has actually performed (`ADR-005`, Phase 8); (b) is consistent with the most rigorous governing document found in this entire investigation (`atlas_domain_object_architecture/Doctrine.md`) without requiring that document's specific content claims to be accepted as binding (the Phase-0 distinction stated at the top of this document); (c) survives the incrementalism test (Phase 9) and the legitimate-forking test (Phase 12); and (d) does not force a premature, undemonstrated convergence Phase 13 found unjustified by any current forcing function.

---

## ADR Candidate (Outline Only)

**Problem:** Atlas contains at least three, and arguably four, independently-governed architectural tracks, with no general-purpose process for reconciling them when they disagree — only one completed, narrowly-scoped precedent (`ADR-005`, covering exactly one pairwise relationship).

**Context:** `Investigation-009` found three tracks and one asymmetric, unreconciled authority claim (Domain Object Architecture over implementation). This investigation, reading `atlas_domain_object_architecture/Doctrine.md` in full for the first time, found that document already contains a remarkably complete governance method — normative authority (§9), publication/amendment (§10), historical integrity (§11), architecture/implementation separation (§12), and a nine-step Change Protocol (§13) — separable from, and adoptable independent of, whether its own specific ontological content (OE-002) is accepted as binding.

**Decision:** Adopt Model G. Tracks remain independently governed by default. A specific, demonstrated forcing function (per §8's own vocabulary: a newly identified domain fact, an unavoidable contradiction, a downstream task exposing a real expressive gap) is required before reconciliation between any two tracks is undertaken. When undertaken, reconciliation follows the Change Protocol's own method (adapted, not copied verbatim, since it was written for one track's internal use) and produces, at minimum, a historical decision record — an `ADR-005`-style document is a complete, sufficient outcome even where it changes no content at all, only the declared authority relationship.

**Invariants:**
- Every ontology track has exactly one authority boundary: itself, unless and until an explicit reconciliation document states otherwise (reused directly from `Investigation-009`'s own invariant, now generalized as the standing rule this investigation confirms).
- Implementation follows the implemented model by default; it does not silently inherit either doctrine track's authority claim.
- Doctrine never silently overrides implementation — any future work treating a doctrine track as binding on implementation must say so as its own explicit decision.
- A contradiction (Phase 7's precise sense — competing settled claims about the same fact) must be named the moment it is found; an omission or alternative model must not be inflated into a contradiction requiring urgent resolution.
- Supersession requires an identified replacing decision and an explicit status change — never silent deletion, never mere recency.
- Historical records, including every document in this investigation series, remain permanently recoverable regardless of any future reconciliation's outcome.

**Consequences:**
- **Implementation:** unaffected — no code changes follow from this investigation.
- **Documentation:** this document is the first to state a general reconciliation process rather than resolve one specific case; future reconciliations (Track 1 ↔ Track 3 chief among them) may cite it as their method.
- **Future ADRs:** may continue this series' own established practice — implementation-grounded, doctrine-informed, evidence-cited — now with an explicit process to invoke if a genuine forcing function is ever found.
- **Atlas Memory:** unaffected, already fragmented by subsystem before this investigation (`Investigation-009` Phase 15), unresolved by it.
- **Decision Workspace:** unaffected — every finding across `Investigation-001`–`009` remains valid.
- **Future architecture:** this investigation series' own status as a fourth, unacknowledged quasi-track (Phase 15/16) is now named and should be addressed by whoever eventually undertakes Track 1 ↔ Track 3 reconciliation.

**Rejected Alternatives:** A (implementation-first alone — undervalues real doctrinal work, no path to Phase 13's eventual need); B (ontology-first alone — correct only prospectively, wrong if read retroactively, as Track 3's own crude application would imply); C (documentation-first — fails directly against §9); E (living architecture alone — no reconciliation discipline, the exact condition that let the Track 1 ↔ Track 3 fork go unnamed for nine investigations); F (independent parallel tracks alone — legitimate only if disclosed, which requires the reconciliation process Model G adds).

**Migration/Compatibility:** None required by this decision itself. Any future Track 1 ↔ Track 3 reconciliation, if undertaken, is its own, separately-scoped body of work — not designed, authorized, or begun here.

**Open Questions** (carried forward, not resolved here):

1. Who owns and initiates the recommended Track 1 ↔ Track 3 reconciliation, and on what timeline? (Phase 16, item 5 — the single most concrete, actionable gap this investigation leaves open)
2. Should this investigation series itself formally register as a fourth track, with its own stated scope and status vocabulary, or remain informal? (Phase 15, 16)
3. Is Judgment's three-way definitional difference a contradiction requiring reconciliation, or a compatible refinement that can remain as is? (Phase 7, 16)
4. What concrete forcing function, if any, would justify pursuing Phase 13's "eventually, for automation" convergence now rather than later?
5. Should `atlas_domain_object_architecture/Doctrine.md`'s own excellent Change Protocol be formally adapted into a cross-track version, or does each future reconciliation design its own method as `ADR-005` did?

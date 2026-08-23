# ADR Investigation 9 — Ontology Authority and Reconciliation

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Central question:** Which ontology is authoritative for Atlas?

**Headline finding, stated up front — this investigation found not two ontology tracks but THREE, and their relationships to each other are not symmetric.** `Investigation-008`'s framing ("the implemented Core Loop domain, OE-002 Domain Object Model, Atlas Reasoning Foundations") undercounts by one: **`OE-002` does not live inside "Atlas Reasoning Foundations."** It lives under `docs/atlas_domain_object_architecture/`, which has **its own, separate `Doctrine.md`** — a different governing document from `docs/atlas_reasoning_foundations/Doctrine.md`, never mentioned in `ADR-005`, never renamed from `docs/atlas_core/`, and structurally different (OE-002 does not follow the Reasoning Foundations Doctrine's own mandated ADR structure — no Question/Motivation/Falsification Attempts sections). This is a third, independently-governed track. And its relationship to the implemented codebase is **not** the peaceful non-convergence `ADR-005` established between Reasoning Foundations and implementation — its own Doctrine **explicitly, assertively claims authority over implementation**: "Repository facts MUST NOT be used to establish, confirm, or deny an ontological claim... implementation planning MUST NOT silently introduce new ontology." No document analogous to `ADR-005` exists reconciling this claim with the actual running codebase this entire investigation series has treated as ground truth.

**Method:** Fresh reads this investigation — `OE-002-Domain-Object-Model.md` (re-confirmed from `Investigation-008`), `ADR-005-Atlas-Reasoning-Foundations-Naming-and-Authority.md` (re-confirmed), `docs/atlas_reasoning_foundations/Doctrine.md` (in full), `docs/CoreLoopATLAS001.md` (in full), `docs/atlas_reasoning_foundations/ADR-001-The-Nature-of-Reasoning.md` (§1–4), `docs/atlas_domain_object_architecture/Doctrine.md` (targeted grep across governance/authority language), and `docs/atlas_domain_object_architecture/Domain-Object-Type-Set-Discrepancy-Investigation.md` (§1–7) — a document that turns out to be an internal precedent for exactly this investigation's own method, and whose own quoted Doctrine §9 principle is load-bearing evidence throughout what follows.

---

## Phase 1 — Identify Every Ontology Track

| # | Track | Location | Governing document |
|---|---|---|---|
| 1 | **Implemented Core Loop** | `atlas/core/domain/*`, `atlas/alpha/*` | No formal doctrine — sprint-by-sprint engineering documents (`CoreLoopATLAS001.md`, `EvidenceCaptureAPI005.md`, `HypothesisCaptureAPI004.md`, etc.), each describing what was built, not what ought to exist |
| 2 | **Atlas Reasoning Foundations** | `docs/atlas_reasoning_foundations/` | `docs/atlas_reasoning_foundations/Doctrine.md` — "Normative. Governs *how* Atlas Reasoning Foundations is developed." Draft/Final ADR discipline, first-principles falsification method |
| 3 | **Domain Object Architecture** | `docs/atlas_domain_object_architecture/` | `docs/atlas_domain_object_architecture/Doctrine.md` — a **separate** document, explicitly claiming to "govern the relationship between architecture and implementation" |

Additional material found within track 3, not previously known to this series: `OE-003` (Domain Event Model), `OE-004` (Domain Invariants), `OE-005` (Domain Validation Model), `OE-006` (Domain Acceptance Model) — all Final, per the Discrepancy Investigation's own citation table — plus roughly two dozen "Implementation Design," "Pre-Commit Architecture Review," and "Reconciliation Investigation" documents, several explicitly named around reconciling this track against the "Legacy Core Loop" (`Legacy-Core-Loop-Canonical-Reconciliation-Investigation.md`, `Core-Loop-Case-Context-Reconciliation-Investigation.md`, `Domain-Object-Implementation-Reconciliation-Plan.md`, `Domain-Object-Type-Set-Discrepancy-Investigation.md`). **No document within this series' own prior investigations identified track 3 as separate from track 2 before now.** No additional, fourth track was found.

---

## Phase 2 — Each Track's Purpose

| Track | Why created | Problem solved | Abstraction level | In scope | Out of scope |
|---|---|---|---|---|---|
| 1 — Implemented Core Loop | `CoreLoopATLAS001.md`'s own stated scope: "Prove that one complete Atlas Core Loop reasoning cycle can be executed through the existing architecture" | Connecting four independently-built aggregates (API-001/003/004/005: Decision, Observation, Hypothesis, Evidence) into one walkable cycle | Working code — entities, application services, persistence, tests | Making the ten named steps runnable and tested | Any first-principles justification of *why* those ten steps are the right ontology — none is offered or attempted |
| 2 — Reasoning Foundations | `Doctrine.md`'s own Purpose: "establishing what things *are* before deciding how they are structured... so that Atlas Reasoning Foundations' own foundations remain sound" | The risk of building architecture atop unexamined concepts | Pure ontology — philosophical first principles, argued from scratch | What Reasoning, Judgment, Knowledge fundamentally are, tested by deliberate falsification | Implementation, architecture, "how Atlas Core's `atlas/core/` package is meant" (explicitly out of scope per its own §16 naming rule) |
| 3 — Domain Object Architecture | Doctrine.md §7 (own line 7): "governs the method by which Atlas Core's architecture is investigated, decided, published, amended, removed, reopened, and historically preserved. It governs the relationship between architecture and implementation." | Establishing a closed, normative object set and an explicit change protocol, with implementation treated as strictly downstream | Normative specification, closer to architecture than pure philosophy — OE-002's own definitions read as formalized, doctrinal restatements, not first-principles arguments the way Reasoning Foundations' ADRs are | The Domain Object Set (OE-002), Domain Events (OE-003), Invariants (OE-004), Validation (OE-005), Acceptance (OE-006), and the explicit governance of how implementation relates to all of them | "Ordinary product planning, engineering process, or repository operations, except to the extent required to preserve the boundary between architecture and implementation" (its own §-20 exclusion) |

**No inference was required for any of these three rows — each is quoted or closely paraphrased from the governing document's own stated purpose.**

---

## Phase 3 — Object Inventory

| | Track 1 (Implemented) | Track 2 (Reasoning Foundations) | Track 3 (Domain Object Architecture / OE-002) |
|---|---|---|---|
| Objects | Question, Observation, Interpretation, Hypothesis, Evidence, Conclusion, Decision, Outcome, Evaluation, Learning, `reasoning_link` (4 bridge entities, explicitly provisional), plus — from later sprints across this session — DecisionContext, ReflectionResponse, KnowledgeReference, ReasoningTrace, Judgment, Security Confirmation (Alpha-only), and the proposed-not-implemented CaseCondition, Assumption, Draft (`Investigation-003`/`006`/`007`) | Reasoning (a capability), Reasoning Act (a bounded exercise), Judgment (an Act's own distinct output object), Knowledge (referenced, own identity criterion "explicitly open" per `ADR-002`'s own text) | Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome — **exactly six, closed** |
| Relationships | Mostly informal/no structural link (confirmed repeatedly in `Investigation-008`: most adjacent Core Loop pairs share zero cross-references); four explicit provisional Link bridges; later objects (`DecisionContext`, `ReflectionResponse`) reference `decision_id` directly | Reasoning Act individuated by numerical distinctness alone; Judgment produced by exactly one Act; Judgment's equivalence to another Judgment is content-based, never identity-based | Case-membership (ownership) vs. semantic relationship, explicitly separated (§3); no mandatory sequence among the six (§6) |
| Reasoning primitives | `ReasoningTrace` (a reference-collection object) | **Reasoning itself** — a full first-principles account (capability/act distinction, conservatism principle) | `ReasoningTrace`, same definition as OE-002 §5.3 |
| Decision primitives | `Decision` (immutable, capture-only, five required fields) | Not directly addressed in the material read — Decision is not one of `ADR-001`'s own named concepts | `Decision` (§5.5) — "records the Case's settled practical commitment... without itself executing behaviour," internal-or-referenced form |
| Memory primitives | None named "memory" as such — `DE-005`'s own "Decision Memory" is a derived-synthesis concept over Decision history, not a stored object | `Knowledge`, referenced but its own identity criterion is an acknowledged open dependency | None named "memory" |

**Shared concepts:** Observation, Judgment, Decision, Outcome, Knowledge Reference/Reasoning (in some form) appear in at least two of the three tracks. **Unique to Track 1:** Question, Interpretation, Hypothesis, Evidence, Conclusion, Evaluation, Learning — none of these seven appear in OE-002's closed set, and none has a counterpart named in the `ADR-001`/`ADR-002` material read. **Unique to Track 2:** Reasoning-as-capability and Reasoning Act — genuinely novel concepts with no counterpart in either other track; Track 1 has no object representing "reasoning" as a thing in itself, only `ReasoningTrace`, a reference list. **Missing across all three:** a formally adopted concept matching what `Investigation-007`/`008` call Assumption, and what `Investigation-006` calls CaseCondition — neither track defines either.

---

## Phase 4 — Authority Claims

| Track | Claims to be | Evidence |
|---|---|---|
| 1 — Implemented | Descriptive of itself; **implicitly normative for runtime behavior** by virtue of being the only track that actually runs | `CoreLoopATLAS001.md` never claims philosophical authority — it documents what was built and why, in engineering terms ("a direct consequence of Decision's own existing required fields," "not scope creep") |
| 2 — Reasoning Foundations | Explicitly normative, but narrowly — **"Normative. This document governs *how* Atlas Reasoning Foundations is developed."** Not a claim over implementation. | `Doctrine.md` line 3 (quoted verbatim); `ADR-005` independently confirms no governance claim over `atlas/core/` |
| 3 — Domain Object Architecture | **Explicitly, assertively normative over implementation.** | `Doctrine.md` line 7: "It governs the relationship between architecture and implementation." Line 41: "Repository facts MUST NOT be used to establish, confirm, or deny an ontological claim." Lines 193–198: "implementation determines how it is represented operationally... the existence of an implementation MUST NOT be treated as retroactive proof of an ontological claim... implementation planning MUST NOT silently introduce new ontology." |

None of the three tracks describes itself as merely historical or experimental. Track 1 is closest to "implementation guidance" in character (it explains engineering choices, not ontological ones). Track 3 is the only one of the three whose own words claim authority *over* another track's domain (implementation) — Track 2 explicitly disclaims any such reach, per `ADR-005`.

---

## Phase 5 — Governance

- **Does OE-002 govern Core Loop?** OE-002's own Doctrine (Track 3) claims it should — but no document was found where Track 1 (or anyone acting on its behalf) accepts this claim. The claim exists; acceptance was not found.
- **Does Core Loop govern OE-002?** No — nothing in Track 1's own documentation asserts authority over Track 3, or over any ontology document at all.
- **Does Reasoning Foundations govern implementation?** No — `ADR-005` explicitly, mutually rules this out: "Neither track currently governs, supersedes, reinterprets, or implies future convergence with the other."
- **Does implementation govern doctrine?** Track 3's own Doctrine explicitly, repeatedly forbids this in its own direction ("Repository facts MUST NOT be used to establish, confirm, or deny an ontological claim"). Track 2's Doctrine does not address this question directly (it never claims jurisdiction over implementation to begin with, so the question of implementation "governing" it does not arise in the same way). Track 1 makes no claim over anything.
- **Does ADR-005 explicitly answer these questions?** **Only for Tracks 1 and 2.** `ADR-005` was written specifically to resolve the "Atlas Core" naming collision between `atlas/core/` and the *original* `docs/atlas_core/` (now `docs/atlas_reasoning_foundations/`). It says nothing about `docs/atlas_domain_object_architecture/`, which is not named anywhere in it. **The Track 1 ↔ Track 3 relationship has no analogous, explicit resolution anywhere found in this investigation.**

---

## Phase 6 — Contradiction Table

| Pair | Compatible | Incompatible | Duplicated | Competing definitions | Authority conflict |
|---|---|---|---|---|---|
| Track 1 vs. Track 2 | Both treat immutability as foundational | Track 1 has no "Reasoning" object at all; Track 2's central concept (Reasoning as capability/Act) has no implemented counterpart | Judgment (name only) | Judgment: Track 1's docstring ("settled, Case-relative characterization") vs. Track 2's ADR-002 ("the ontological object produced by a completed Reasoning Act") — materially different emphasis | **None, by explicit mutual agreement** (`ADR-005`) |
| Track 1 vs. Track 3 | Judgment's core phrasing is near-identical between Track 1's docstring and OE-002 §5.4 | Track 1 has Question, Interpretation, Hypothesis, Evidence, Conclusion, Evaluation, Learning — none in OE-002's closed six; Track 3's Doctrine explicitly forbids treating this as evidence of anything | Observation, Judgment, Decision, Outcome, Knowledge Reference (as `KnowledgeReference`), Reasoning Trace (as `ReasoningTrace`) — same names, and (for Observation/Judgment/Decision/Outcome) closely matching definitions | None found to be materially divergent for the five shared, matching objects | **Yes, real and unresolved** — Track 3 claims governing authority over implementation; no document accepts, rejects, or reconciles that claim against Track 1's actual, larger object set |
| Track 2 vs. Track 3 | Both are ontology-first, Doctrine-governed, pre/post-implementation-agnostic in stated intent | Different governing Doctrine documents; different structural templates (Track 2's mandated Question/Motivation/Falsification/Current-Best-Definition structure vs. Track 3's flat normative-spec structure); Track 2's Judgment (`ADR-001`/`002`, tied to "Reasoning Act") vs. Track 3's Judgment (OE-002 §5.4, no "Act" concept at all) | Judgment (name), Knowledge/Knowledge Reference (adjacent but not identical — Track 2's Knowledge is an unresolved-identity referent of Reasoning; Track 3's Knowledge Reference is a Case-scoped pointer object) | **Yes — Judgment, materially** (Phase 4/7) | **No document found reconciles or even acknowledges the other's existence** — neither `ADR-005` nor anything in Track 3's own material names Track 2, and vice versa |

**Documented, not resolved, per instruction.**

---

## Phase 7 — Judgment, Special Investigation

**How many definitions exist? Three**, confirmed by direct comparison in `Investigation-008` Phase 6, restated precisely here with governance now attached:

| Definition | Track | Implemented? | Governs runtime? | Governs doctrine? |
|---|---|---|---|---|
| "the Case's settled, Case-relative characterization of an identified subject, without asserting that the characterization is objectively true" | 1 (docstring) / 3 (OE-002 §5.4, near-identical wording) | **Yes** — `atlas/core/domain/judgment/entity.py` is real, tested, persisted code | **Yes** | Track 3 claims this doctrine governs the implemented object; no acceptance found |
| "the ontological object produced by a completed Reasoning Act: the specific, complete determination that Act reaches concerning the Knowledge it operated over" | 2 (`ADR-002`, Final status) | No — no "Reasoning Act" concept exists anywhere in implemented code | No | Yes, within Track 2's own scope, which explicitly does not extend to implementation |

**Which governs runtime behavior?** Only the implemented entity's own definition — trivially, since it is the only one with running code. **Which govern doctrine?** Both Track 2's ADR-002 (Final, within its own track) and Track 3's OE-002 §5.4 (Final, within its own track) are doctrine within their respective, separately-governed tracks. Neither is doctrine for the other track, and neither has been formally reconciled with the implemented object, though Track 3's own wording is close enough to the implementation that a reconciliation, if attempted, would likely be far less disruptive than reconciling Track 2's Act-dependent definition would be.

---

## Phase 8 — Reasoning Itself

**Does every ontology define Reasoning?** No — only Track 2. Track 1 has no "Reasoning" object; the closest artifact is `ReasoningTrace`, which Track 3 (OE-002 §5.3) defines as "one or more already-accepted Domain Objects... providing epistemic support" — a reference-collection object, nothing like Track 2's capability/act pair. Track 3 itself has no standalone "Reasoning" concept either, only `ReasoningTrace` — meaning **Track 2 is the only track that treats Reasoning as a first-class ontological subject at all.**

Per `ADR-001` §1 (read fresh): Reasoning is **a standing capability** — "an enduring, always-available power to engage in disciplined evaluative operation, exercisable on any number of separate, bounded occasions." A Reasoning Act is one bounded exercise of it, individuated by numerical distinctness alone (§2). Reasoning is explicitly **not** an object, a process, an event, or a relation — each was tested and rejected in the document's own falsification method.

**Role Reasoning plays where it is *not* formally defined (Tracks 1 and 3):** an informal, unexamined background assumption — every entity's own docstring ("the investor's provisional belief," "the Case's settled characterization") presupposes that *some* reasoning activity produced the content, without either track ever naming or examining that activity as its own thing. Track 2 exists specifically to close this gap for itself; it has not been extended to close it for Tracks 1 or 3.

---

## Phase 9 — Workflow vs. Ontology

Directly reusing and citing `Investigation-008` Phase 10/13's own decisive finding, now cross-checked against the freshly-read `CoreLoopATLAS001.md` for corroboration: **the Core Loop represents workflow/common usage, not enforced ontology.**

New corroborating evidence from the fresh read: the ten-step sequence was **not designed as a sequence at all** — it was assembled from four aggregates "already built" independently in prior sprints (API-001 = Decision, API-003 = Observation, API-004 = Hypothesis, API-005 = Evidence — note the sprint numbering does not even match the eventual ten-step order), with `reasoning_link`'s own four bridge entities built specifically, and only, "to prove that one complete Atlas Core Loop reasoning cycle can be executed" after the fact. `reasoning_link`'s own docstring states this status directly: "explicitly not a permanent addition to the ubiquitous language... a structural workaround for one specific constraint... not a modeling decision about what 'linking' means in Atlas's domain." **The sequence is illustrative, retrofitted, and explicitly provisional at its own connective tissue — not mandatory**, confirmed now from the implementation side as well as the ontology side (OE-002 §6's own disclaimer, already found in `Investigation-008`).

---

## Phase 10 — Implementation Reality (Doctrine Ignored)

Reading only the code: `atlas/core/domain/` contains sixteen real, tested, persisted aggregates as of this session's own cumulative findings — Case, Observation, Question, Interpretation, Hypothesis, Evidence, Conclusion, Decision, Outcome, Evaluation, Learning, DecisionContext, ReflectionResponse, KnowledgeReference, ReasoningTrace, Judgment — plus four provisional `reasoning_link` bridge entities and (Alpha-only) Security Confirmation's event-sourced pair. **This set does not match any of the three documented ontologies exactly.** It is a strict superset of OE-002's closed six (confirmed: all six of OE-002's named objects exist and match closely in the code; ten more implemented objects exist beyond them). It has no counterpart anywhere for Track 2's Reasoning/Reasoning Act. It follows no doctrine's own change-protocol or falsification discipline in its own commit history — each object's own sprint document (API-00X, ATLAS-00X) argues from engineering necessity and prior precedent within the codebase, not from first principles or normative closure.

**The ontology the actual code follows is its own, fourth thing: an accreted, sprint-by-sprint engineering ontology, historically informed by but never formally derived from either doctrine track.**

---

## Phase 11 — Historical Evolution

Reconstructed from what each document states about itself, without speculation:

1. `atlas/core/` (Track 1) began with independent aggregates (API-001 Decision, API-002 DecisionContext, API-003 Observation, API-004 Hypothesis, API-005 Evidence), each built and documented on its own terms.
2. `CoreLoopATLAS001` (2026, per this session's own git history context) retroactively connected four of those five into a named ten-step sequence, adding six new aggregates and four provisional bridge links — explicitly framed as proving connectivity, not establishing ontology.
3. A separate ontology-first track began under `docs/atlas_core/` (the *original* name, per `ADR-005`'s own account) — later renamed to `docs/atlas_reasoning_foundations/` after a naming collision with the `atlas/core/` package was identified and investigated (`ENG-001`, `ARC-001`).
4. `ADR-005` (Accepted) formally resolved that naming collision and explicitly declared no governance relationship between Track 1 and Track 2, in either direction.
5. **Separately, and not mentioned anywhere in `ADR-005`,** `docs/atlas_domain_object_architecture/` (Track 3) was established, with its own Doctrine, culminating in OE-002 through OE-006 (Final status) and an extensive, ongoing body of implementation-design and reconciliation-investigation documents that treat the *existing* implementation as something to be examined and reconciled against, one document at a time (`Domain-Object-Type-Set-Discrepancy-Investigation.md` is itself dated to a specific implementation increment, "DO-IMP-002," and explicitly reasons about a **discrepancy** between OE-002's closed set and a later engineering brief that substituted Case for Observation — evidence that this track is actively aware of, and actively working to resolve, gaps against real engineering work).

**Do later documents intentionally supersede earlier ones?** Within Track 3, yes, explicitly and procedurally (OE-002 §3: "A later Domain Object MAY supersede or reinterpret an earlier one; it MUST NOT erase or overwrite it" — a rule about objects, applied by the track's own Doctrine to documents as well, per its 9-step Change Protocol). **Across tracks, no** — nothing found supersedes Track 1 or Track 2 from Track 3, or vice versa; each track's own supersession discipline operates only within itself.

---

## Phase 12 — Layer Analysis

Testing the candidate hierarchy (Reasoning Foundations → Domain Object Model → Implemented Core Loop) against the evidence gathered:

- **If this were the real structure**, Track 3 (Domain Object Model) would sit *between* Track 2 and Track 1 — deriving its own content from Track 2's first-principles work, and Track 1 would in turn implement Track 3's own closed set.
- **Testing the first link (Reasoning Foundations → Domain Object Model):** fails directly. Track 3's own material never cites `ADR-001`, `ADR-002`, or `ADR-003`, and Track 3's own definition of Judgment (OE-002 §5.4) is independently, differently worded from Track 2's (Phase 7) — if Track 3 derived from Track 2, the definitions would either match or explicitly note a refinement; neither is found.
- **Testing the second link (Domain Object Model → Implemented Core Loop):** partially holds in *content* (five of OE-002's six objects match the implementation closely) but fails in *governance* — Track 3's own Doctrine claims authority the implementation has never been shown to accept, and the implementation contains ten objects (Question, Interpretation, Hypothesis, Evidence, Conclusion, Evaluation, Learning, plus the four provisional links) with no place in Track 3's closed set at all. A true "lower layer implements the upper layer's closed set" relationship would not tolerate an unreconciled surplus this large.

**The candidate three-layer hierarchy does not survive contradiction.** The tracks are not stacked; they are three, largely independent efforts, two of which happen to share several object names and approximate definitions, and one of which (Track 3) has made an authority claim over the third (Track 1, the implementation) that has not been tested or accepted anywhere found.

---

## Phase 13 — Can They Coexist?

Attempting to prove coexistence directly, across each named dimension:

- **Terminology:** Yes, with disclosed friction — "Judgment," "Reasoning," and "Evidence" (the latter already self-disclosed as collision-prone in its own docstring, per `Investigation-008`) carry different senses across tracks, but nothing prevents each track from using its own vocabulary internally consistently.
- **Authority:** **This is where coexistence strains.** Track 2 coexists peacefully with Track 1 by explicit mutual agreement (`ADR-005`). Track 3 does not have an equivalent agreement with Track 1 — it has made a unilateral claim. Coexistence *without* authority conflict requires either Track 1 accepting Track 3's claim (not found) or Track 3's claim being understood as aspirational/future-facing rather than currently binding (plausible, but not stated anywhere found).
- **Implementation:** Coexists today only because Track 3's own Doctrine explicitly declines to let implementation facts count as ontological evidence either way (line 41) — a deliberate stance that *permits* the ten extra Track-1 objects to exist without formally contradicting Track 3, at the cost of Track 3 never having to explain them.
- **Memory:** No conflict found — none of the three tracks defines a "memory" concept with enough specificity to conflict (Phase 15, below).
- **Reasoning:** Genuine gap, not conflict — Track 1 and Track 3 simply have nothing to say about Reasoning-as-such; Track 2 says a great deal. A gap is not a contradiction.
- **Decision flow:** No conflict — all three tracks' treatments of Decision (where they address it at all) converge on immutability and non-execution.
- **Ownership:** No conflict — Case-as-ownership-boundary (Track 3 §3.1) is compatible with, though more formally stated than, how Track 1's `Decision`/`DecisionContext`/etc. already use `case_id`.
- **Doctrine:** Two separate, non-cross-referencing Doctrine documents (Tracks 2 and 3) is unusual but not, by itself, a logical impossibility — each can simply govern its own track.

**Coexistence is achievable, but only by treating Track 3's own authority claim as currently unexercised rather than currently binding** — a real, load-bearing qualification, not a clean "yes."

---

## Phase 14 — Must One Win?

Attempting the opposite: is coexistence actually impossible?

**Not logically impossible**, but genuinely unstable in one specific respect: Track 3's Doctrine (line 198) states "implementation planning MUST NOT silently introduce new ontology," while Track 1's own actual history (Phase 11) shows exactly this happening repeatedly and successfully — ten objects beyond OE-002's closed six, each introduced by ordinary sprint engineering, none passing through Track 3's own 9-step Change Protocol. **If Track 3's authority claim is taken literally and applied retroactively, every one of those ten objects is, by Track 3's own rule, an ontological violation already committed.** Coexistence survives today only because Track 3's own Doctrine (Phase 13) declines to treat implementation facts as ontological evidence in *either* direction — meaning it also declines to treat this pattern of "silent ontology introduction" as something requiring correction, so long as no one asks the question directly. **This investigation is the first document found, across this entire nine-investigation series, to ask it directly.**

One does not have to "win" for the system to keep functioning — Track 1 will keep running regardless of what either doctrine track claims. But if Track 3's own stated authority is ever *exercised* (e.g., a future engineer treats OE-002's closed set as a hard constraint and attempts to reconcile Track 1 to it), the resulting conflict is real, not hypothetical, and would require either revising OE-002's own closed set (a Track-3-internal, Doctrine-governed act) or treating ten already-shipped, tested, load-bearing objects as non-conformant.

---

## Phase 15 — Atlas Memory

- **Case Memory:** Not formally defined by any of the three tracks under that exact name. Closest: Track 3's Case (§3.1, "the normative ownership boundary") plus Track 1's actual `case_id`-scoped objects. Governance: Track 3, in name only (the boundary concept); Track 1, in practice (every object's own `case_id` usage).
- **Decision Memory:** Defined only by `DE-005` (a doctrine document outside all three tracks named in this investigation, part of the Alpha/Decision-Engine documentation lineage) — explicitly a *derived synthesis* over Track 1's own Decision history, never a stored object in any track. No conflict, because only one source defines it at all.
- **Knowledge:** Track 2 (`ADR-003-The-Nature-of-Knowledge.md`, not read in full this investigation but referenced in `ADR-002`'s own dependency graph) and Track 3 (`KnowledgeReference`, OE-002 §5.2) both use the word, for related but not confirmed-identical concepts — Track 2's Knowledge is what Reasoning operates over; Track 3's `KnowledgeReference` is a Case-scoped pointer *to* something treated as knowledge. Not tested to resolution here — a genuine, disclosed open question this investigation surfaces but does not chase further, since `ADR-002` itself already states Knowledge's own identity criterion is "an explicit external dependency, owned by a future ADR."
- **Reasoning:** Track 2 only (Phase 8) — the others have no comparable concept.
- **Reflection:** None of the three tracks defines this — it belongs entirely to Track 1's later "Understanding lineage" (`Investigation-002`), outside all three ontologies examined here.
- **Learning:** Track 1 only (`Learning`, the Core Loop's terminal node) — absent from both Track 2 and Track 3.

**Governance differs by subsystem, stated explicitly:** no single track governs all six of these. Case Memory splits between Track 3 (the boundary concept) and Track 1 (the practice); Decision Memory and Reflection and Learning belong to Track 1 alone (or, for Decision Memory, to `DE-005` specifically); Reasoning belongs to Track 2 alone; Knowledge is contested, unresolved, between Tracks 2 and 3.

---

## Phase 16 — Future ADRs

**Which documents should new ADRs build upon?** For this document series specifically (`Investigation-001` through `009`), the answer already given implicitly, and now made explicit: **the implemented `atlas/core/domain/*` entities**, because every one of the eight prior investigations grounded its findings in running code, cross-checked against whichever doctrine document was directly relevant to the specific question at hand — never adopting either doctrine track's *closed set* or *authority claim* as binding on the series' own conclusions.

**Which documents are informative only?** For this series: OE-002 through OE-006, and `ADR-001`/`002`/`003` under Reasoning Foundations — genuinely valuable comparative and philosophical material (as this investigation's own Phase 7 use of them demonstrates), but neither has been shown to be binding on Track 1, and this investigation does not change that.

**Which documents require explicit reconciliation first?** Any future ADR that wants to treat Track 3's closed six-object set as a hard constraint on Track 1's implementation would need exactly the kind of reconciliation `ADR-005` performed for Track 2 — and none currently exists for Track 3. This is the single most concrete, actionable gap this investigation identifies.

---

## Phase 17 — Alternative Governance Models

| Model | Consistency | Implementation impact | Documentation impact | Migration impact | Future ADR stability | Conceptual clarity |
|---|---|---|---|---|---|---|
| **A — Implemented Core Loop is normative; everything else supporting theory** | High — matches what this whole series has already, implicitly, been doing | None — nothing changes | Requires an explicit statement (this investigation) that neither doctrine track is currently binding | None | High — this series' own eight prior investigations remain valid without qualification | High — one clear, already-operative rule |
| **B — OE-002 is normative; implementation must converge** | Low today — ten implemented objects have no home in OE-002's closed set | Severe if taken literally — would require justifying or removing Question/Interpretation/Hypothesis/Evidence/Conclusion/Evaluation/Learning/`reasoning_link` | Requires OE-002 itself to be reopened (its own closed-set status revisited) or an explicit, formal exception granted to Track 1 | Severe, hypothetically | Unstable until reconciliation completes | Low today, potentially high after reconciliation |
| **C — Reasoning Foundations governs all ontology** | Low — Track 2 has no counterpart for seven of Track 1's ten "extra" objects, and explicitly disclaims governing implementation at all (`ADR-005`) | Severe and, per `ADR-005`, currently unauthorized | Would require reopening `ADR-005` itself | Severe, hypothetically | Unstable | Low — Track 2 was never designed for this role |
| **D — Three-layer architecture, each track owning a different abstraction level** | **Fails** — tested directly in Phase 12 and does not survive contradiction | N/A, since the model itself fails | N/A | N/A | N/A | Attractive in principle, false in practice |
| **E — Competing ontologies, explicit reconciliation required** | Honest, but unresolved by definition | None immediately, but commits to future work | Requires a dedicated reconciliation document, analogous to `ADR-005`, for Track 1 ↔ Track 3 | Deferred, not avoided | Stable once reconciliation lands; unstable until then | Medium — accurate but incomplete until the reconciliation is done |
| **F — Current state remains acceptable; no authority change required** | Matches Track 3's own Doctrine's *de facto* current posture (declining to treat implementation facts as evidence either way) | None | None required, though this investigation itself is new documentation of the situation | None | Stable only as long as no one exercises Track 3's dormant claim (Phase 14's own risk) | Low — leaves a live contradiction unacknowledged if adopted silently |

---

## Phase 18 — Consistency Test

Challenging Model A (the emerging preference) directly:

- **vs. all previous ADR investigations:** no contradiction — every one of `Investigation-001` through `008` already, implicitly, treated implementation as primary, exactly what Model A makes explicit. This investigation's own finding *validates* rather than revises the series' prior methodology.
- **vs. implemented entities:** no contradiction, definitionally.
- **vs. Core Loop:** no contradiction — Model A treats it as the (informal, engineering-derived) actual ontology, consistent with Phase 9/10's findings.
- **vs. OE-002:** a real, disclosed tension, not hidden — under Model A, OE-002 becomes "supporting theory," which is a real demotion from what its own Doctrine (Track 3) claims for it. This is not resolved by Model A; it is simply the choice Model A makes, stated plainly rather than smoothed over.
- **vs. Reasoning Foundations:** no contradiction — `ADR-005` already, independently, reached the same non-governance conclusion for this track.
- **vs. Atlas Memory:** no contradiction — Phase 15's own subsystem-by-subsystem findings are unaffected by which track is declared primary, since governance already differs by subsystem regardless.
- **vs. Decision Workspace:** no contradiction — every finding across `Investigation-001` through `007` (all Decision-Workspace-focused) was already grounded in the implemented objects; Model A changes nothing about them.
- **vs. future automation:** a genuine, disclosed open question — if Atlas ever builds automated reasoning (per `Investigation-008`'s own Phase 19 finding), should that automation be designed against Track 1's own accreted ontology, or is this the moment to finally reconcile with Track 2's more rigorous Reasoning/Act account, which was arguably built with exactly this kind of future capability in mind? Not resolved here.
- **vs. future AI reasoning:** the same question, restated — Track 2's own philosophical rigor (falsification, first principles, explicit uncertainty-as-legitimate-outcome) may become *more*, not less, relevant once Atlas's own reasoning is no longer exclusively human-authored. Model A's demotion of Track 2 to "supporting theory" is a present-tense, not permanent, choice — worth flagging as a real, live tension this investigation does not resolve.

**Two contradictions/tensions found and documented, not resolved:** (1) OE-002's own self-claimed normative status is directly demoted under Model A, a real cost, not a hidden one; (2) Track 2's own philosophical rigor may become more valuable, not less, as automated reasoning capability grows — Model A's present-tense pragmatism could look premature in hindsight.

---

## Phase 19 — Final Decision

**`IMPLEMENTED_CORE_LOOP_IS_NORMATIVE`**

- **Which ontology governs implementation?** The implemented `atlas/core/domain/*` objects themselves — not by any doctrine's own declared authority, but because nothing else has been shown, anywhere in this investigation, to actually bind them, and because this is the practice this entire nine-investigation series has already, correctly, followed.
- **Which governs architecture?** For any future work in *this specific document series* (Decision Workspace architecture, `Investigation-001`–`008`), the implemented objects, cross-referenced against whichever doctrine track's specific document is most directly relevant to the question at hand (as every prior investigation has already done) — never a blanket adoption of either track's closed set or authority claim.
- **Which governs doctrine?** Each doctrine track governs itself. Track 2 governs Track 2's own Draft/Final ADR discipline. Track 3 governs Track 3's own OE-series and its own Change Protocol. Neither governs the other, and (per this investigation's own finding) neither has been shown to govern Track 1.
- **Which governs future ADRs?** This series' own established practice (implementation-grounded, doctrine-informed) should continue, now explicitly justified rather than merely habitual.
- **Is reconciliation work now mandatory?** **Not mandatory for this series to continue producing valid work** — Model A is stable for that purpose. But **a genuine, concrete gap now exists and is named**: no `ADR-005`-equivalent reconciliation exists between Track 1 and Track 3, and Track 3's own Doctrine's dormant authority claim (Phase 14) remains a live, if currently unexercised, risk. This investigation recommends, without mandating, that such a reconciliation document eventually be produced — explicitly modeled on `ADR-005`'s own precedent.

---

## ADR Candidate (Outline Only)

**Problem:** Atlas currently contains three ontology tracks — an implemented Core Loop, a Reasoning-Foundations doctrine track, and a separately-doctrined Domain Object Architecture track — with overlapping concepts, one asymmetric and unreconciled authority claim, and no single document (before this one) that named all three or tested their relationships directly.

**Context:** `ADR-005` resolved the naming collision and authority question between the implemented package and Reasoning Foundations, explicitly and mutually. No equivalent document exists for Domain Object Architecture, whose own Doctrine explicitly claims authority the implementation has never been shown to accept, and whose own closed six-object set (OE-002) excludes ten objects the implementation actually, successfully, currently runs.

**Decision:** For all purposes within this document series and its own future continuations, the implemented `atlas/core/domain/*` objects are treated as normative. Reasoning Foundations and Domain Object Architecture are both treated as informative, doctrinally rigorous, but not currently binding — consistent with `ADR-005`'s own explicit ruling for the former, and, in the absence of any equivalent ruling, extended by this investigation's own reasoning to the latter.

**Invariants:**
- Every ontology track has exactly one authority boundary: itself, unless and until an explicit reconciliation document (an `ADR-005` analog) states otherwise.
- Implementation follows the implemented model; it does not silently adopt either doctrine track's closed set or authority claim by default.
- Doctrine never silently overrides implementation in this series' own future work — any future investigation that wishes to treat a doctrine track as binding must say so explicitly, as its own decision, not by inheritance from this one.
- Ontology tracks must not drift indefinitely without at least being named and compared, as this investigation now does for the first time across all three.

**Consequences:**
- **Implementation:** unaffected — no code changes follow from this investigation.
- **Documentation:** this document itself is the first to name and compare all three tracks; future investigations in this series may cite it rather than re-deriving the comparison.
- **Future ADRs:** may continue grounding themselves in implementation, now with explicit justification rather than habit.
- **Atlas Memory:** governance-by-subsystem (Phase 15) is unaffected — already fragmented before this investigation, unresolved by it.
- **Decision Workspace:** no change — every finding across `Investigation-001`–`008` remains valid.
- **Future architecture:** the dormant Track 1/Track 3 authority tension (Phase 14) remains a real, if currently low-probability, risk that a future, dedicated investigation should address.

**Rejected Alternatives:** B (OE-002 normative — implementation impact too severe, ten objects unaccounted for); C (Reasoning Foundations governs all — explicitly unauthorized by `ADR-005`, and Track 2 has no counterpart for most of Track 1's objects); D (three-layer architecture — tested directly in Phase 12 and does not survive contradiction); F (current state remains acceptable with no change — leaves a live, named contradiction unacknowledged, which this investigation exists specifically not to do).

**Migration/Compatibility:** No migration required for this decision itself. A future, separate reconciliation between Track 1 and Track 3 — if undertaken — would be its own, larger body of work, explicitly not scoped or designed here.

**Open Questions** (carried forward, not resolved here):

1. Should a formal `ADR-005`-equivalent reconciliation between the implemented Core Loop and Domain Object Architecture be produced, and by whom? (Phase 14, 16)
2. Does Track 3's own dormant authority claim need to be explicitly revised or withdrawn by its own Doctrine's Change Protocol, or is indefinite non-exercise an acceptable steady state? (Phase 14)
3. Should Track 2's Reasoning/Reasoning Act account be integrated into Track 1 before, rather than after, Atlas builds any automated-reasoning capability, given Phase 18's own finding that its rigor may become more relevant, not less, over time? (Phase 8, 18)
4. Is Knowledge (Track 2) the same concept as Knowledge Reference's own target (Track 3), and does this matter before either concept is exercised further? (Phase 15)
5. Should this investigation's own three-track inventory (Phase 1) be kept up to date as a standing reference, given how easily a fourth track could be discovered exactly the way this investigation discovered the third?

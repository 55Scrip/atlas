# Reasoning Trace — Implementation Design

This document is an implementation-design artifact, not a normative document. It carries no Doctrine status (Draft/Final/Superseded/Historical) because those statuses apply to normative documents, and this is not one. Where anything here appears to conflict with the Architecture Doctrine, OE-002 through OE-006, or the Historical Decision Record, those documents govern and this one is wrong and must be corrected.

## 1. Executive Finding

**Corrected twice: first by the Relation Completeness Review, then by the Self-Support Coherence Review (both appended at the end of this document) — this Executive Finding reflects both corrections.**

**A Reasoning Trace is a permanent, independently-identified Domain Object that records, as its entire settled semantic content, that one or more specified, already-accepted, same-Case Domain Objects satisfy the adopted, stipulated admission criteria for standing in OE-002's "epistemic support" relation directed at the Reasoning Trace's own existence as that accepted record — without asserting any stepwise process, chronology, narrative rationale, the truth or validity of that support, or that the Reasoning Trace itself embodies any independent, truth-apt proposition beyond this. "Epistemic support" is retained as canonical wording, but is treated as a primitive, architecture-internal relation (per Doctrine §14) rather than a richly decomposed philosophical one — nothing beyond the relation's own admission and exclusion criteria (INV-004, INV-005, INV-013, and the stated exclusions) is asserted. Whether a further, distinct supported claim exists beyond the Trace itself remains exactly as open as OE-002 leaves it, and is not resolved here.**

The prior version of this Executive Finding described the relation as one in which the supporting objects "stand in a support relationship" without ever identifying what receives that support, leaving the relation's second endpoint apparently unstated. The Relation Completeness Review found that OE-002 §5.3's own "Relationships" clause already answers this for the base case — "Reasoning Trace MAY be supported by one or more other Domain Objects" identifies the Trace itself, grammatically and textually, as the entity receiving support. This was a real gap in the prior prose, not merely a stylistic one, and is corrected here; it did not require any change to the accepted field set (Section 15), because the resolved endpoint is the Trace's own `id`, already present.

The minimal accepted fields remain exactly: `id`, `case_id`, a non-empty set of supporting-object references (each a typed `target_type`/`target_id` pair), and `recorded_at`. No field for a *further, distinct* supported claim is included, because OE-002 itself leaves the representation of any such claim explicitly, deliberately open — this design does not resolve that narrower question and is not required to. No agent, model, prompt, tool, confidence, explanation, ordering, or status field is included; each was tested and rejected or deferred with a stated reason. The supporting-object collection is a set, not a sequence — order is not adopted as semantic content. Self-reference and cycles are structurally impossible, not merely prohibited. No database foreign key is used; no separate Domain Event artifact is required. **A significant repository correction is recorded in Section 3 and Section 24: two of the named canonical sources this task asked to be inspected — "BETA-001" and "DFS-001" — do not exist anywhere in this repository, and the "open-edge/ontology-edge records" and "mechanics observations and foundation reviews" referenced in the task brief could not be located either. This design proceeds without them rather than fabricating their content.**

## 2. Scope

This document designs the implementation of Reasoning Trace, the Domain Object adopted by OE-002 §5.3 within the `docs/atlas_domain_object_architecture/` ontology (the Atlas Core Domain Object Architecture). It does not redesign Case, identity, validation/acceptance, or Knowledge Reference — each is treated as an already-settled input, reused where genuinely applicable. It does not design Judgment. It does not resolve OE-002's own deliberately open "supported claim" representation question; it identifies precisely what that question is and confirms the minimal design does not require resolving it. No code, schema, migration, or existing document was modified in the course of this work.

## 3. Canonical Sources Reviewed

**Authoritative for this design** (the `docs/atlas_domain_object_architecture/` track): Doctrine.md; OE-002-Domain-Object-Model.md (§5.3 Reasoning Trace; §6 Overall Relationship Topology); OE-003-Domain-Event-Model.md (§4.3 ReasoningTraceAccepted; §3 Definition of a Domain Event); OE-004-Domain-Invariants.md (INV-002 through INV-015, with particular attention to INV-004, INV-005, INV-007, INV-008, INV-009, INV-011, INV-013, INV-015); OE-005-Domain-Validation-Model.md (§4, §9, §15's own worked Knowledge-Reference/INV-014 example, reused by direct analogy for INV-013); OE-006-Domain-Acceptance-Model.md; Historical-Decision-Record-Domain-Object-Architecture-Foundation.md (historical, non-normative — consulted only for provenance, not treated as a source of current ontology, per its own stated authority limits).

**Treated as prior, non-normative implementation-design evidence, within the same track**: the completed Knowledge Reference Implementation Design — reused directly wherever its underlying mechanism (typed polymorphic references, no foreign key, generic validation pipeline, Case-assignment discipline) applies to Reasoning Trace without alteration, and diverged from precisely where Reasoning Trace's own adopted cardinality (INV-013's "one or more") differs from Knowledge Reference's (INV-014's "exactly one"). This document was directly re-verified against the current, post-"Reference Validation Availability" state of `atlas/core/domain/knowledge_reference/` and `atlas/core/application/knowledge_reference/capture_knowledge_reference.py` during this audit, not merely cited from memory.

**Correction made by this audit — citation provenance**: this section previously also cited, as "completed" prior authorities, a "Repository & Conformance Baseline," a "Legacy CoreLoop Semantic Correspondence & Reducibility Investigation," a "Decision/Outcome Reference Semantics Investigation," a "Case Representation Strategy," an "Investor Identity and Accepted-State Permanence Resolution," and a "Complete Validation and Acceptance Redesign." A repository-wide directory listing and grep, performed independently during this audit and separately corroborated by `Core-Loop-Case-Context-Reconciliation-Investigation.md`'s own Section 5 finding, confirms **none of these six documents exists anywhere in this repository** under any name. This is the same category of defect Section 3 already disclosed for "BETA-001"/"DFS-001" (below), and is corrected the same way: named plainly, not silently worked around. This does not change any conclusion in this document — every substantive finding that these six phantom citations were invoked to support (the typed-reference pattern, the no-foreign-key policy, the Candidate/accepted-object distinction, INV-013's cardinality reading, the deterministic-validation conclusion in Section 28) is independently re-derived in this document directly from OE-002 through OE-006, the Architecture Doctrine, and the Historical Decision Record's own decision-history entries — each re-verified against live document text during this audit, not taken on the phantom citations' word. **This disclosure governs every other reference to these six names appearing later in this document** (e.g., Section 9's "Case Representation Strategy," Section 10's and Section 22's "Complete Validation and Acceptance Redesign," Section 17's same, Section 18 by omission, Section 11's "Investor Identity investigation," Sections 5/9/22's "Legacy Correspondence investigation"): each such mention is an informal, descriptive label for a conclusion this document itself independently re-derives from live OE-002–OE-006/Doctrine text or from direct repository inspection, not a citation to a separate file that could be opened and checked. No individual body sentence was rewritten to remove these labels, since doing so would not change any conclusion; this single disclosure is the correction.

**Inspected and found not to define or govern Reasoning Trace**: `docs/atlas_reasoning_foundations/` — its own README.md and Doctrine.md were read in full. This is a separate, self-contained ontology-development track (ADR-001 "The Nature of Reasoning," Final; ADR-002 "The Nature of Judgment," Final; ADR-003 "The Nature of Knowledge," Final) that explicitly states, in its own words: "Nothing outside `docs/atlas_reasoning_foundations/` is part of Atlas Reasoning Foundations," and "No work currently exists at the Architecture or Implementation layers." Its own primitives are Reasoning, the Reasoning Act, Judgment, and Knowledge — it does **not** define a "Reasoning Trace" primitive anywhere. Per the Architecture Doctrine's own §9 (single source of truth; a document outside the normative dependency chain has no authority to establish or alter current ontology), and consistent with this repository's own prior ADR-005 naming-collision precedent between these two tracks, this design treats `atlas_reasoning_foundations` as non-authoritative background only, and does not rely on it for any binding conclusion below.

**Named in the task brief but not found anywhere in this repository, confirmed by a repository-wide search**: "BETA-001," "DFS-001." No file, filename fragment, or textual reference to either exists. No "open-edge" or "ontology-edge" record format, and no "mechanics observations" or "foundation reviews" documents distinct from the six prior investigations already listed above, were found either. This is stated plainly rather than silently working around it, per the same discipline this entire investigation series has applied throughout: repository evidence is verified before being relied upon, never assumed from a prompt's own framing.

**Existing code**: a repository-wide search for `ReasoningTrace`, `Reasoning Trace`, and `reasoning_trace` across `atlas/` and `tests/` returned **zero matches**. No provisional schema, model, migration, API, test, or fixture anywhere currently encodes any Reasoning Trace assumption. The nearest *mechanically* similar existing structures are the `reasoning_link` package's `InterpretationHypothesisLink` and `HypothesisEvidenceLink` tables, addressed in Section 23.

## 4. Explicit Canonical Claims

Quoted or closely paraphrased, each with its source:

- "Reasoning Trace is a permanent Domain Object that represents one or more already-accepted Domain Objects as providing epistemic support." (OE-002 §5.3, Definition)
- "Reasoning Trace has stable identity independent of its content and independent of the identity of the Domain Objects it represents as supporting." (OE-002 §5.3, Identity)
- "Reasoning Trace is responsible for recording that specified, already-accepted Domain Objects stand in a support relationship, without itself asserting a stepwise process, chronology, or narrative rationale." (OE-002 §5.3, Responsibility)
- "Every supporting Domain Object MUST belong to the same Case as the Reasoning Trace and MUST already exist as an accepted Domain Object. Reasoning Trace requires at least one supporting Domain Object. Reasoning Trace is not root-eligible." (OE-002 §5.3, Ownership boundary)
- "Reasoning Trace MAY be supported by one or more other Domain Objects defined in this document, drawn from the same Case. Whether Reasoning Trace additionally contains, or instead references, a distinct supported claim is not settled by this document." (OE-002 §5.3, Relationships)
- "Knowledge Reference and Reasoning Trace each require at least one reference to another Domain Object and are therefore never roots of this structure." (OE-002 §6)
- "Not established: any stepwise process, chronology, or narrative rationale by which the support was determined; the exact representation of any supported claim, which remains an open matter at the object level under OE-002." (OE-003 §4.3)
- INV-013: "A Reasoning Trace MUST be accepted with at least one supporting Domain Object already accepted in the same Case." "Does not require: Any specific Domain Object type as a supporter, any upper bound on the number of supporters, or any resolution of how a supported claim, if separately represented, is itself constrained." (OE-004)
- "INV-013 does not resolve how a Reasoning Trace's supported claim is represented." (OE-004 §17; reaffirmed identically in OE-005 §19 and OE-006 §19)

## 5. Required Distinctions

- **Reasoning** — not a primitive of `atlas_domain_object_architecture`; the term is used only within the separate, non-authoritative `atlas_reasoning_foundations` track.
- **A Reasoning Act** — likewise not a primitive of this ontology. No document within `docs/atlas_domain_object_architecture/` uses this term. This design does not assume Reasoning Trace corresponds to, records, or represents any "Reasoning Act."
- **Reasoning Trace** — as defined in Section 4: a support-relation record, nothing more.
- **Judgment** (OE-002 §5.4) — a settled, Case-relative characterization of a subject. Distinct: Judgment characterizes something; Reasoning Trace records support for something (possibly for a characterization), but does not itself characterize anything.
- **Knowledge** — not a directly named OE-002 primitive; the nearest analog is Knowledge Reference (OE-002 §5.2), which records reliance on a target as knowledge. Distinct from Reasoning Trace's support relation, which is a different kind of relational fact.
- **Evidence** — an unresolved legacy concept (per the Legacy Correspondence investigation), not an adopted Domain Object type. Not conflated with Reasoning Trace here.
- **Decision** (OE-002 §5.5) — a settled practical commitment. Distinct.
- **Evaluation, Learning** — legacy CoreLoop concepts, both found reducible to Judgment (per the Legacy Correspondence investigation). Not Reasoning Trace.
- **Technical execution telemetry** (prompts, model calls, tool invocations, latency) — explicitly not part of Reasoning Trace's ontology; see Section 11 and Section 14.

## 6. Candidate Designs

**Candidate A — Trace as Reasoning Act Record.** Strongest argument: matches an intuitive "trace of a reasoning act" reading. Canonical evidence: none — "Reasoning Act" is not a term this ontology defines. Contradiction: OE-002 explicitly states Reasoning Trace's responsibility excludes asserting "a stepwise process," which a record of an "act" (an occurrence) would import. Unsupported assumption: that a foreign concept from an unrelated, non-authoritative track applies here. **Disposition: Rejected** — imports an undefined concept and contradicts OE-002's own text.

**Candidate B — Trace as Ordered Step Sequence.** Strongest argument: matches "chain of thought" intuitions. Canonical evidence: none. Contradiction: direct and explicit — OE-002 states Reasoning Trace does not assert "a stepwise process, chronology, or narrative rationale." **Disposition: Rejected outright**, directly contradicted by adopted text.

**Candidate C — Trace as Relation Set.** Strongest argument: matches OE-002's own text almost verbatim once stripped of the phrase "one reasoning occurrence" (which is not itself a defined term here). Canonical evidence: OE-002 §5.3's Definition and Responsibility clauses describe exactly a retained relation between the Trace and its supporting objects, with no intermediate "occurrence" object anywhere in the text. Contradictions: none found. Unsupported assumptions: none, once refined to remove the undefined "occurrence" language. **Disposition: Selected**, in refined form — see Section 8.

**Candidate D — Trace as Documentary Explanation.** Contradiction: OE-002 explicitly disclaims "narrative rationale." **Disposition: Rejected.**

**Candidate E — Trace as Execution Telemetry.** Canonical evidence: none anywhere in OE-002 through OE-006 for models, prompts, tools, or execution details. This is exactly the category of content the Decision Standard explicitly excludes ("useful for AI observability" is not a forcing function). **Disposition: Rejected.**

**Candidate F — Trace as Generic Container.** Contradiction: directly opposes Doctrine's burden-of-justification and minimality discipline; "flexible container for any reasoning-related objects" is precisely the kind of unforced, open-ended design Doctrine warns against. **Disposition: Rejected.**

**Candidate G — No Distinct Domain Object.** Contradiction: OE-002 has already, as Final, adopted Reasoning Trace as one of the six closed-set Domain Object types (per the Historical Decision Record's own account of that decision). Eliminating it would require reopening OE-002 itself under a genuine forcing function; none was found in six prior investigations spanning this exact question area, and none is found here. **Disposition: Rejected** — the ontology has already settled this candidate's own question in the opposite direction.

No additional candidate was found necessary; Candidate C, refined, is fully supported by the canonical text without requiring an eighth alternative.

## 7. Contradiction Analysis

No contradiction exists within OE-002 through OE-006 concerning Reasoning Trace. The one genuine, internally-acknowledged open question — the "supported claim" representation — is not a contradiction; it is an explicitly, repeatedly (OE-002, OE-004 §17, OE-005 §19, OE-006 §19) disclosed and deliberately preserved open question, permitted under Doctrine §7 because it does not block Reasoning Trace's own minimum semantic contract from being stated. This design does not attempt to resolve it (Section 19, Section 24).

## 8. Selected Ontological Meaning

**Corrected twice: by the Relation Completeness Review, then by the Self-Support Coherence Review (see the end of this document).** A Reasoning Trace is a permanent Domain Object whose entire settled semantic content is the retained fact that one or more specified, already-accepted, same-Case Domain Objects satisfy the admission criteria for OE-002's "epistemic support" relation, directed at **the Reasoning Trace's own existence as that accepted record** — the Trace is the relation's second, already-identified endpoint, by its own `id`, not an unstated one, and the Trace is not itself claimed to embody any further, independent, truth-apt proposition. This is Candidate C, refined and now precisely closed: the relation is direct, binary in structure (a supporting-object set on one side, the Trace's own identity on the other), primitive rather than richly decomposed (its content is exhausted by admission/exclusion criteria, not by an independently articulated claim), with no intermediate "reasoning occurrence" concept, no stepwise process, and no narrative content. Whether a *further*, distinct supported claim exists beyond the Trace itself — e.g., a Judgment the Trace is understood to inform — remains exactly as open as OE-002 states, and is a separate, narrower, non-blocking question (Section 24), not a gap in the base relation's own completeness.

## 9. Identity and Ownership

**Identity**: every Reasoning Trace is independently identified (OE-002 §5.3), stable and content-independent, and — critically — independent of the identity of the objects it supports. Two distinct Traces may cite the same supporting object(s); nothing reduces a Trace's identity to any external "occurrence," because no such concept exists in this ontology. Identity is immutable, permanent, append-only, exactly like every other adopted type (INV-009/011), and survives any change in presentation or serialization, since it is a stable fact independent of both content and display.

**Ownership**: Case ownership is semantic and structural, per INV-002, identical in kind to every other Domain Object — not inherited from, or derived through, any supporting object (this follows the Case Representation Strategy's own general rule that referenced objects never supply the referencing candidate's Case). Cross-Case supporting-object references are forbidden by INV-004, stated explicitly for Reasoning Trace in OE-002 §5.3's own text ("Every supporting Domain Object MUST belong to the same Case as the Reasoning Trace").

## 10. Cardinality

- Supporting objects per Trace: at least one (INV-013), no upper bound (INV-013's own "Does not require" clause).
- Traces per supporting object: unbounded — nothing limits how many distinct Traces may cite the same object.
- Judgments among the supporting objects: unbounded; Judgment is one eligible supporting-object type among six, with no special cardinality rule of its own.
- "Exactly one terminal output": not established — this imports a process/input-output framing OE-002 neither requires nor forbids, but does not demonstrate either; not adopted.
- An empty trace (zero supporting objects): **Invalid under INV-013**, not Incomplete — this is a logically derived conclusion (Section 16), reached by direct analogy to OE-005 §15's own explicit worked resolution of the parallel Knowledge-Reference/INV-014 case, applied to INV-013's structurally identical "at least one" requirement.
- An incomplete trace: not a distinct property of the accepted object — completeness is a pre-acceptance gating concept (per the Complete Validation and Acceptance Redesign), not a state a Reasoning Trace itself can occupy once accepted.
- Multiple traces referencing the same Domain Objects: permitted, as stated above.

## 11. Internal Structure

| Candidate member | Classification | Basis |
|---|---|---|
| Reasoning inputs (as a name distinct from supporting-object references) | Unsupported, as a separate field | Redundant with supporting_object_refs; no separate concept demonstrated |
| Knowledge References | Permitted, not required | One eligible supporting-object type among six (OE-002 §5.3, no type restriction) |
| Evidence | Unsupported | Not an adopted Domain Object type; unresolved legacy concept |
| Observations | Permitted, not required | Eligible supporting-object type |
| Hypotheses | Unsupported | Not an adopted type; reduces to Judgment upon migration |
| Candidates (pre-acceptance) | Explicitly forbidden | INV-005 requires supporting objects to be already accepted; a Candidate is not yet accepted |
| Judgments | Permitted, not required | Eligible supporting-object type; also the most plausible future target form of a referential "supported claim," if that question is ever resolved that way |
| Decisions | Permitted, not required | Eligible supporting-object type |
| Intermediate states | Unsupported | No such concept in OE-002; contradicted by "without asserting a stepwise process" |
| Ordered reasoning steps | Explicitly forbidden | Direct contradiction of "without asserting... chronology" |
| Relationships between steps | Explicitly forbidden | Same reason |
| Timestamps (beyond recorded_at) | Unsupported | No second demonstrated meaning; see Section 18 |
| Agents | Explicitly forbidden | Direct extension of the Investor Identity investigation's own conclusion: no Domain Object carries actor identity as accepted content |
| Models | Explicitly forbidden | Platform execution telemetry, Candidate E's rejected content |
| Prompts | Explicitly forbidden | Same |
| Tools | Explicitly forbidden | Same |
| Confidence values | Unsupported | No basis in OE-002; would assert a reliability judgment OE-002 does not require and arguably conflicts with the "without asserting... validity" reading |
| Explanations | Explicitly forbidden | Directly the disclaimed "narrative rationale" |
| Outcomes | Permitted, not required | Eligible supporting-object type, no special role |
| Evaluations | Unsupported as a distinct concept | Reduces to Judgment (Legacy Correspondence investigation); a migrated instance falls under the Judgment row above |
| Learnings | Unsupported as a distinct concept | Same reasoning |
| Parent/child traces | Unsupported as a distinct mechanism | A Reasoning Trace may cite another Reasoning Trace as an ordinary supporting object (no type restriction excludes it), but no distinct "parent/child" field or relationship category is established or needed |

## 12. Ordering Semantics

**Ordering is not adopted as part of Reasoning Trace's semantic content.** OE-002 explicitly disclaims "chronology" as asserted content, and nothing in its text treats the supporting-object collection as anything other than an unordered set — consistent with OE-005 §9's own treatment of violation sets as true sets, not sequences. Any array-like representation in a future implementation is presentation-only; semantic ordering is not inferred from serialization shape, per this investigation's own governing method.

## 13. Completeness and Lifecycle

A Reasoning Trace cannot be open, in-progress, or abandoned as an accepted object — per OE-006, an object either is accepted (complete, permanent, immutable) or does not yet exist as a Domain Object at all; there is no intermediate state (INV-008). "Abandoned" candidates simply never become objects — nothing exists to represent their abandonment. Supersession (INV-011) is a relational fact about a later, separately-accepted Trace, never a status field on an earlier one. Finality belongs entirely to the acceptance moment (OE-006), not to any field inside Reasoning Trace itself. **No status field is introduced** — no genuine ontological distinction requires one, consistent with every other adopted type's own status-field-free design.

## 14. Truth and Authority Boundaries

The existence of a Reasoning Trace asserts only: that the Case, at acceptance time, recorded that the specified, already-accepted, same-Case objects provide epistemic support **for the Reasoning Trace itself** (Section 8; corrected by the Relation Completeness Review). It does **not** assert: that any reasoning process occurred or was valid (no process is asserted at all); that the support is complete or exhaustive; that the referenced objects' own content is true (each retains whatever truth-status it independently carries; Reasoning Trace adds nothing); that any resulting Judgment is correct; that the system endorses the recorded relation beyond the bare fact of its existence; or that the Trace constitutes an authoritative explanation (explicitly excluded, per the disclaimed "narrative rationale"). This mirrors, structurally, Knowledge Reference's own truth-disclaimer (OE-002 §5.2), applied here to a support relation rather than a reliance relation.

## 15. Minimal Accepted Fields

| Field | Type | Nullable | Meaning | Necessity | Semantic/Technical | Source |
|---|---|---|---|---|---|---|
| `id` | `ReasoningTraceId` (UUID) | No | Identity | OE-002 §5.3 Identity clause | Semantic | OE-002 §5.3; INV-003/006 |
| `case_id` | `CaseId` | No | Ownership boundary | INV-002; OE-002 §5.3 Ownership boundary | Semantic | INV-002; Case Representation Strategy |
| supporting-object references | non-empty set of (`target_type`, `target_id`) pairs | No (must be non-empty) | The support relation itself — Reasoning Trace's entire semantic content | OE-002 §5.3 Definition/Responsibility; INV-013 | Semantic | OE-002 §5.3; INV-013 |
| `recorded_at` | `datetime` | No | Acceptance/event time | INV-015; uniform acceptance-time discipline across every adopted type | Technical (acceptance-time fixation) | INV-015; established codebase pattern |

No field for a "supported claim" is included — see Section 19. **Note, corrected by the Relation Completeness Review**: the relation's second endpoint (what is supported) is not missing from this table — it is the Trace's own `id`, already listed above, per Section 8. No separate "supported entity" field is needed for the base relation; only a *further, distinct* supported claim (e.g., a specific downstream Judgment) remains unrepresented, and remains so because OE-002 itself leaves that narrower question open, not because this table is incomplete.

## 16. Rejected or Deferred Fields

| Candidate field | Disposition | Reason |
|---|---|---|
| A separate "reasoning inputs" field | Rejected | Redundant with the supporting-object reference set |
| Special fields for Knowledge Reference / Evidence / Hypothesis as distinct member types | Rejected | Ordinary instances of the generic supporting-object reference; no special field needed |
| A Candidate-holding field | Forbidden | INV-005 requires already-accepted targets only |
| Intermediate-state / step / step-relationship fields | Forbidden | Contradicts "without asserting a stepwise process" |
| A second timestamp | Rejected | No demonstrated distinct meaning beyond `recorded_at` (Section 18) |
| Agent / model / prompt / tool fields | Forbidden | Platform telemetry and actor-identity content, both explicitly excluded |
| Confidence field | Rejected | No basis in OE-002; would assert a reliability claim OE-002 does not require |
| Explanation field | Forbidden | Directly the disclaimed "narrative rationale" |
| Special Outcome/Evaluation/Learning fields | Rejected | Ordinary supporting-object instances; no special field needed |
| Parent/child trace fields | Rejected | No basis; ordinary supporting-object citation suffices if a Trace ever cites another Trace |
| Any field "for future flexibility" | Rejected across the board | Explicitly excluded by the governing Decision Standard |

## 17. Reference Semantics

Reused directly from the Knowledge Reference design, because the underlying situation is textually confirmed to match: OE-002 places **no type restriction** on either Knowledge Reference's target or Reasoning Trace's supporting objects. References are **typed** (a `target_type`/`target_id` discriminator pair per supporting object, exactly as designed for Knowledge Reference), because both designs face the identical polymorphic-target problem. Any adopted Domain Object type may be referenced, including another Reasoning Trace or a Knowledge Reference — no category restriction exists. A reference does not require its own Domain Object; it is a technical relation record. **Duplicate references within one Trace** (the same target cited twice in one Trace's own support set) are absorbed by set semantics (Section 12) — a set does not contain the same element twice, so this is not a distinct violation category, mirroring OE-005 §9's own set-semantics treatment of violation sets. **Duplicate references across distinct Traces** are permitted, exactly as for Knowledge Reference — each Trace is an independently accepted fact. **Self-reference** is structurally impossible: at validation time a candidate Trace is not yet accepted, so it cannot serve as its own already-accepted supporting object (INV-005). **Cycles** are structurally impossible for the identical reason established for Knowledge Reference: prior-acceptance ordering plus permanence together make the reference graph an inherent DAG — no additional acyclicity invariant is needed. References must remain within one Case (INV-004, explicit in OE-002 §5.3's own text). Referential integrity is required at acceptance time, via the same transactional, authoritative re-validation already established by the Complete Validation and Acceptance Redesign — reused without modification, since that mechanism is type-agnostic by design.

## 18. Temporal Semantics

Only `recorded_at` has demonstrated meaning: system-generated at acceptance, playing the role of acceptance/event time (INV-015), using the same injectable-clock pattern established throughout the codebase. **No second timestamp is justified.** Unlike Observation, Decision, or Outcome — each of which describes some external happening at a specific, investor-known moment, and therefore carries its own investor-supplied timestamp (`observed_at`, `decided_at`, `occurred_at`) — Reasoning Trace describes no external happening with its own independent timing; it records a purely relational fact whose only meaningful time is the moment of acceptance. This is the identical conclusion reached for Knowledge Reference, for the identical underlying reason.

## 19. Persistence Design

Two tables, reflecting the genuine structural difference from Knowledge Reference (a one-or-more cardinality rather than exactly-one):

- `reasoning_traces`: `id` (PK, `String`), `case_id` (indexed `String`), `recorded_at` (`String`). No foreign key.
- `reasoning_trace_supports`: `reasoning_trace_id` (indexed `String`, no FK), `target_type` (indexed `String`, CHECK-constrained to the six adopted type names), `target_id` (indexed `String`, no FK), with a **composite uniqueness constraint on (`reasoning_trace_id`, `target_type`, `target_id`)** — this constraint is not invented arbitrarily; it directly enforces the set-semantics conclusion of Section 12 and Section 17 at the schema level, a genuinely forced constraint rather than a speculative one.

No deletion, no update, append-only, exactly like every other table in this codebase. No ordering column, per Section 12. No foreign key across the polymorphic target, for the identical reasons given in the Knowledge Reference design: the current schema uses none anywhere, permanence eliminates the dangling-reference risk foreign keys primarily guard against, and the acceptance flow's own transactional, authoritative re-validation is sufficient. camelCase API serialization follows the existing shared `CamelModel` convention.

## 20. API Consequences

**Create/capture**: required — accepts (or resolves) a `case_id` and a non-empty set of target descriptors. **Read**: required — get by `case_id` + `id`. **Update**: not meaningful — permanence forbids it. **Append** (adding a supporting object to an already-accepted Trace): **not required and not permitted** — per OE-006 §4's "no candidate element may be replaced," a different supporting-object set is a different candidate requiring its own, separate acceptance; there is no "append" operation on an accepted Reasoning Trace. **Completion/finalization**: not meaningful — acceptance itself is finalization (Section 13). **Validation**: governed by OE-005's own actual, verified text, not by a prior citation — see Section 28 for the corrected, precise conclusion this audit reached (this section previously cited a "Complete Validation and Acceptance Redesign" worked example claiming three invalid supporting references must produce three separately attributable findings; that document does not exist in this repository, per Section 3's corrected citation-provenance finding, and the claim is not adopted — Section 28 replaces it with a conclusion grounded directly in OE-005 §8–§9). **Error conditions**: zero supporting objects at capture time is Invalid under INV-013 (Section 10, Section 16). **Response representation**: `id`, `case_id`, the complete supporting-object set, `recorded_at`.

**API inclusion, finalized by this audit**: the API layer (schemas, dependencies, router, error handlers) **is included in this same implementation package**, not deferred to a later one. This document's original Section 23 language ("eventually API/CLI surfaces") is corrected as genuinely ambiguous and is resolved definitively here, by direct precedent: the two most recently built *from-scratch* Domain Objects in this codebase — Knowledge Reference (DO-IMP-003) and Judgment (DO-IMP-004) — both shipped domain, persistence, application, and API layers together in one package, not in separate retrofit packages (unlike Decision/Observation/Outcome, which pre-dated this project's own current API convention for genuinely different reasons that do not apply to a brand-new type). Reasoning Trace should follow the same, now-established convention. See Section 31 for the finalized API surface.

## 21. Invariants

**Adopted** (directly stated): INV-002 (single Case ownership); INV-003/INV-006 (distinct identity); INV-004 (same-Case reference, applied to every supporting object individually); INV-005 (prior acceptance of every supporting object individually); INV-007 (exactly one `ReasoningTraceAccepted` event per instance, structurally trivial); INV-008 (atomic acceptance); INV-009/010/011 (permanence, non-erasure); INV-013 (at least one supporting object, no upper bound, no type restriction); INV-015 (`recorded_at` is acceptance time).

**Logically derived** (not literally quoted, but following directly from adopted text applied by the same reasoning already used for Knowledge Reference): zero supporting objects yields Invalid under INV-013, not Incomplete, by direct analogy to OE-005 §15's explicit Knowledge-Reference/INV-014 resolution; the supporting-object collection is a set (no duplicates, no order); self-reference and cycles are structurally impossible under prior-acceptance ordering plus permanence; no separate Domain Event artifact is required, per OE-003 §3 and INV-007's own "does not require... event payload" clause.

**Proposed implementation constraints** (engineering choices, not normative invariants): a composite uniqueness constraint on (`reasoning_trace_id`, `target_type`, `target_id`); no foreign key across the polymorphic target; no `update`/`delete` repository method; no "append" operation.

**Unresolved candidates** (Section 24): whether a distinct "supported claim" exists at all, and if so its representation; whether a cardinality bound applies to it if adopted referentially; the architectural significance, if any, of a Reasoning Trace citing another Reasoning Trace.

## 22. Edge-Case Analysis

1. **Two traces citing the same supporting object(s)** — permitted; each is an independent accepted fact.
2. **A trace with no Judgment among its supporters** — permitted; Judgment is one eligible type among six, never required.
3. **A trace with multiple Judgments** — permitted; no cardinality bound on any specific type.
4. **A trace referencing an unresolved (never-accepted) or "later-deleted" object** — "later-deleted" is impossible under permanence; "unresolved" targets are rejected at validation as INV-005 violations and never accepted.
5. **Duplicate referenced objects within one Trace** — absorbed by set semantics; not a distinct violation category.
6. **Self-reference** — structurally impossible.
7. **Cyclic trace relationships** — structurally impossible.
8. **A trace created "after" some external reasoning event** — moot; no such external-occurrence concept is asserted by this ontology.
9. **An imported historical trace** — permitted, subject to the same completeness/validation/Case-assignment rules as any other; no special import mechanism is introduced, and no actor/origin information is fabricated where unknown, since Reasoning Trace carries no such field regardless.
10. **A partially captured trace** — not a distinct object state; either a complete, Valid candidate is accepted, or nothing is accepted at all.
11. **A trace whose presentation changes without semantic change** — fully compatible; identity and content are independent of presentation.
12. **A failed or abandoned reasoning attempt** — not represented; an unaccepted candidate simply never becomes an object.
13. **A trace generated by a non-human agent** — fully compatible; agent identity is excluded from Reasoning Trace's content entirely (Section 11), so nothing distinguishes or requires knowing the proposer's nature.

## 23. Existing-Code Impact

A repository-wide search confirms **zero existing files** reference `ReasoningTrace`, "Reasoning Trace," or `reasoning_trace` anywhere in `atlas/` or `tests/`. No provisional schema, model, API, or test currently encodes any Reasoning Trace assumption, and none needs to change to introduce it — this is a purely additive design, like Knowledge Reference before it.

The nearest mechanically similar existing structures are `atlas/core/domain/reasoning_link/`'s `InterpretationHypothesisLink` and `HypothesisEvidenceLink` tables. Per their own module docstring ("PROVISIONAL STATUS... a temporary orchestration mechanism, not a permanent addition to the ubiquitous language") and per the Legacy Correspondence investigation's own finding, these are **not** an existing implementation of Reasoning Trace — they carry no independent content, no Case concept, and are explicitly disclosed as provisional. They are, at most, potential migration seed data for a future Reasoning Trace migration (their `link_id`/two-reference/`linked_at` shape is structurally compatible with becoming rows in a future `reasoning_trace_supports`-like table), never something to be silently treated as already satisfying this design. **This design does not touch, migrate, or retire `reasoning_link`** — that remains a separate, later task.

Future work (not performed here) would add: `atlas/core/domain/reasoning_trace/` (entity, value objects, exceptions, repository); a matching persistence module; a capture/acceptance application service; and — per Section 20's finalized API-inclusion decision, correcting this sentence's prior "eventually" hedge — a REST API surface in the same package, following exactly the Knowledge Reference/Judgment precedent. No CLI is added (none exists for Knowledge Reference or Judgment either). All of this is additive; none of it requires modification of any existing file. See Sections 27–39 for the exact, finalized inventory and mechanics.

## 24. Unresolved Questions

**Q1 — Does a Reasoning Trace additionally carry or reference a *further*, distinct supported claim beyond the Trace itself (e.g., a specific Judgment it is understood to inform), and if so, is it internal content or a reference?** *(Narrowed by the Relation Completeness Review: the base question — what receives the recorded support — is resolved; the Trace itself is the base endpoint, per Section 8. This question concerns only whether something further, beyond the Trace, is also supported.)* Competing interpretations: (a) no further distinct claim exists — the Trace's own being-supported is the entirety of the relation, and any downstream use (e.g., a Judgment citing the Trace) is established by that other object's own reference to the Trace, not by anything additional stored here; (b) internal content — the Trace additionally carries its own statement of a further claim; (c) referential — the Trace additionally references another same-Case Domain Object (most plausibly a Judgment) as a further, distinct thing supported. OE-002 itself states this is unresolved, and OE-004 §17, OE-005 §19, and OE-006 §19 each independently reaffirm that none of their own invariants, validation rules, or acceptance rules require it to be resolved. No canonical source in this repository forces a choice among (a)/(b)/(c). Implementation consequence of choosing prematurely: committing now would silently narrow deliberately preserved flexibility and could require a breaking migration if the wrong form were later found necessary. Smallest safe placeholder: **none is needed** — the minimal design in Section 15 is fully complete and self-sufficient without this field, per Doctrine §7's own permission for a settled minimum contract to coexist with an explicitly retained open question. Forcing function to resolve: per Doctrine §8 — a newly identified domain fact inexpressible without it, an unavoidable contradiction, a downstream normative document exposing a real expressive gap, or evidence the original OE-002 investigation missed a distinct candidate. None currently exists.

**Q2 — If the supported claim is ever adopted as a reference, does a cardinality bound apply?** OE-002 uses singular language ("a supported claim") but states no explicit "exactly one" invariant comparable to INV-014's for Knowledge Reference. Genuinely open; deferred alongside Q1, for the same reason.

**Q3 — Does the separate `atlas_reasoning_foundations` track bear on this design?** Resolved, not merely deferred: no. That track disclaims authority outside its own directory, has not reached its own Architecture layer, and does not define a "Reasoning Trace" primitive at all. It remains adjacent background material only (Section 3).

**Q4 — The task brief's references to "BETA-001," "DFS-001," "open-edge/ontology-edge records," and "mechanics observations and foundation reviews."** These do not exist in this repository, confirmed by direct search. This is recorded as a factual correction to the task brief, not an unresolved design question — no placeholder or fabricated content was substituted for them, and no design conclusion in this document depends on them.

## 25. Reopening Conditions

Governed entirely by the Architecture Doctrine's own §8 forcing-function standard, applied identically to every open item above: a genuine forcing function exists only if a newly identified domain fact cannot be represented by the currently adopted architecture, an unavoidable contradiction is discovered, a downstream normative task exposes a real, demonstrated expressive gap, or evidence emerges that the original OE-002 investigation omitted a materially distinct candidate or misapplied the Doctrine's method. Documentary convenience, implementation inconvenience, naming preference, familiarity, symmetry, speculative future usefulness, or the existence of legacy code (including `reasoning_link`) do **not**, by themselves, qualify — consistent with every prior investigation in this series.

## 26. Final Implementation Recommendation

Adopt the four-element minimal design of Section 15: `id`, `case_id`, a non-empty set of typed supporting-object references, and `recorded_at`. Persist as two tables (Section 19, finalized by Section 30), reusing Knowledge Reference's typed-reference and no-foreign-key pattern directly, diverging only where INV-013's "one or more" cardinality genuinely differs from INV-014's "exactly one." Enforce set-semantics via a composite uniqueness constraint, not through application logic alone. Introduce no status, ordering, agent, model, confidence, explanation, or "supported claim" field. Leave the "supported claim" representation question exactly as open as OE-002 itself leaves it, per Section 24. Touch no existing file, including `reasoning_link`, `capture_knowledge_reference.py`, or `capture_judgment.py`, in the course of implementing this design (Section 34). This recommendation is completed and made exact by Sections 27–39 below, added by this audit to close every mechanical ambiguity a direct implementation would otherwise have had to resolve unilaterally. Section 39 states the exact implementation-authorization boundary this recommendation is subject to.

## 27. Exception Ownership and Layering

Following the Knowledge Reference and Judgment precedent exactly (both packages define their own exception classes locally rather than importing another package's): `atlas/core/domain/reasoning_trace/exceptions.py` defines, in the **domain** layer:

- `ReasoningTraceError` — base class for all Reasoning Trace domain errors.
- `ReasoningTraceNotFoundError` — raised when a requested Reasoning Trace does not exist (read-path use, mirroring `KnowledgeReferenceNotFoundError`).
- `EmptySupportError` — raised when a candidate support collection is empty, violating INV-013's "at least one" requirement. Raised primarily by the domain entity's own construction path (`ReasoningTrace.__post_init__`, invoked by both `.capture()` and ordinary reconstruction — Section 30), so that non-emptiness is enforced structurally regardless of which path constructs an instance; the application layer also checks this first, before any repository call (Section 28), and raises the same class directly rather than duplicating it.
- `TargetNotFoundError` — raised when a supporting reference of any of the six adopted types does not exist, or has not yet been accepted, in that type's own repository (INV-005). Unlike Knowledge Reference's own same-named exception, Reasoning Trace's version has **no excluded type** — all six adopted `DomainObjectType` members, including `REASONING_TRACE` itself, are eligible supporting-object types with a working repository by the time this package exists (Section 29).
- `CrossCaseTargetError` — raised when a supporting reference is verified to belong to a different Case than the capturing Reasoning Trace (INV-004), for any of the six adopted types.

**No `TargetTypeUnavailableError`-equivalent is defined.** Knowledge Reference's own such exception exists solely because, at the time Knowledge Reference was implemented, some canonical target types (Observation, Decision, Outcome, and originally Judgment) lacked a working repository or `case_id`. By the time Reasoning Trace is implemented, all six types already have both (Reasoning Trace's own repository is created as part of this same package), so there is no type for such a gate to exclude. Inventing one regardless, for taxonomic symmetry with Knowledge Reference, would be exactly the kind of unforced, speculative addition the Architecture Doctrine's own minimality discipline (Section 25) prohibits.

`ReasoningTraceRepository` (`atlas/core/domain/reasoning_trace/repository.py`) is a two-method `Protocol`, identical in shape to `KnowledgeReferenceRepository`/`JudgmentRepository`:

```python
class ReasoningTraceRepository(Protocol):
    def add(self, reasoning_trace: ReasoningTrace) -> None: ...
    def get(self, reasoning_trace_id: ReasoningTraceId) -> ReasoningTrace | None: ...
```

No `update`, `delete`, or `list_all` — insert-only, matching every other repository Protocol in this codebase without exception.

`atlas/core/application/reasoning_trace/` has **no `exceptions.py` of its own**, matching Knowledge Reference's and Judgment's own precedent exactly: the application service imports and raises the domain-layer exceptions above; it does not define new ones.

## 28. Application Validation Sequence and Determinism

**Corrects Section 20's prior citation.** OE-005 §8–§9 (verified directly against the live document during this audit) defines the violation set as a set of **invariant identifiers** (INV-001 through INV-015), not a set of per-element findings: "The violation set contains each violated invariant's identifier exactly once; duplicate identifiers are not permitted, since the violation set is a set, not a sequence" (OE-005 §9). This means OE-005 does not, on its own actual text, require — for a Reasoning Trace with several invalid supporting references — a separate, individually attributable finding per bad reference; it requires only that the applicable invariant (INV-004 or INV-005) appear once in the violation set if violated by any supporting reference at all. The Section 20 citation this audit found and removed ("a Reasoning Trace with three invalid supporting references should... produce three separately attributable findings") therefore overstated OE-005's actual requirement, in addition to citing a document confirmed not to exist (Section 3).

Consequently, Reasoning Trace's application service uses the **same fail-fast validation pattern already implemented for Knowledge Reference's `_verify_target` and Judgment's `_verify_subject`**, generalized over a collection instead of a scalar — not a new multi-finding-collection mechanism. Exact sequence, implemented by `ReasoningTraceService.capture()`:

1. Receive `case_id` and a collection of `(target_type, target_id)` descriptors.
2. Collapse the descriptors into a `frozenset[TypedDomainObjectReference]` — exact-duplicate collapsing happens here, structurally, via set construction (Section 12, Section 17); this is not a distinct validation step, it is what "a set" already means.
3. If the resulting set is empty, raise `EmptySupportError` immediately — **before any repository is consulted**. This is the literal application of the task's own required ordering ("reject an empty collection before repository lookup") and matches Knowledge Reference's/Judgment's own "cheapest check first" discipline.
4. **Deterministic validation order**: sort the distinct typed references by `(target_type.value, str(target_id))` before iterating. This sort is a **presentation-irrelevant, purely technical device for reproducible error selection** — it does not make support order semantic (Section 12 is unaffected: the persisted and reconstructed representation remains an unordered set) — it exists solely so that, given the same invalid input, the same violation is always the one reported, satisfying the Historical Decision Record's own stated reason for the wider architecture's determinism ("given that validation is deterministic," Decision History: OE-005). No existing package needed this rule before, because Knowledge Reference and Judgment each validate exactly one reference; Reasoning Trace's "one or more" cardinality is the first case in this codebase where a stable multi-element validation order is actually load-bearing.
5. Iterate the sorted, deduplicated references in order; for each, dispatch by `target_type` to the matching repository's `.get(...)` (Section 29) exactly as `_verify_target`/`_verify_subject` already do.
6. On the first reference for which `existing is None`: raise `TargetNotFoundError`, naming that specific type and id, and stop — no further references are checked.
7. On the first reference (in sorted order) for which `existing.case_id != case_id`: raise `CrossCaseTargetError`, naming that specific type and id, and stop.
8. If, and only if, every reference in the set passes both checks: construct nothing until this point, then call `ReasoningTrace.capture(case_id=case_id, supports=the_frozenset)` exactly once.
9. Persist the constructed instance via `self._reasoning_traces.add(reasoning_trace)`, which performs the atomic parent+child insert described in Section 30.

Self-support to a *different*, already-accepted Reasoning Trace is not a distinct case in this sequence — it is handled by the ordinary `REASONING_TRACE` branch of the dispatch in step 5, resolved through `self._reasoning_traces.get(...)` (the service's own repository), exactly as Knowledge Reference resolves a `KNOWLEDGE_REFERENCE`-typed target through itself. Literal self-reference (a candidate citing its own not-yet-assigned id) cannot arise as an input at all, since the candidate has no id until step 8.

## 29. Support-Type Dispatch and Availability

`ReasoningTraceService.__init__` takes six repository dependencies — its own, plus one per eligible external type:

```python
def __init__(
    self,
    repository: ReasoningTraceRepository,
    observation_repository: ObservationRepository,
    knowledge_reference_repository: KnowledgeReferenceRepository,
    judgment_repository: JudgmentRepository,
    decision_repository: DecisionRepository,
    outcome_repository: OutcomeRepository,
) -> None: ...
```

Dispatch in the validation loop (Section 28, step 5) is a six-way `if/elif` exactly mirroring Knowledge Reference's five-way dispatch, with `REASONING_TRACE` resolved via `self._reasoning_traces` (the service's own repository) rather than a separate constructor parameter — identical in kind to how Knowledge Reference resolves its own type via `self._knowledge_references` in its `else` branch. All five external types (Observation, Knowledge Reference, Judgment, Decision, Outcome) are confirmed, by direct inspection during this audit and the immediately preceding readiness audit, to already have a working repository and a required `case_id` — none needs the kind of availability gate Knowledge Reference and Judgment originally needed and later widened (Reference Validation Availability). This is why Section 27 states no `TargetTypeUnavailableError`-equivalent is needed: **the gate that pattern exists to express has no work to do here**, since Reasoning Trace is implemented last among the six adopted types.

## 30. Persistence Mechanics (Finalized)

This finalizes Section 19's "two tables" statement into exact, implementable mechanics. No existing package in this codebase persists a one-to-many typed-reference set for a single aggregate (Section 19's own claim is reconfirmed here: Knowledge Reference and Judgment are strictly single-target, single-row-per-`add()`; `reasoning_link`'s four tables are four independent fixed-pair link tables, not a parent+child shape for one aggregate). This is therefore the first instance of this pattern in the codebase, and every mechanical choice below is stated explicitly rather than left to whoever implements it.

**Parent table** `reasoning_traces` (own private `MetaData()`, mirroring every other persistence package — no shared declarative base exists in this codebase, per direct verification):
- `reasoning_trace_id` — `String`, primary key.
- `case_id` — `String`, indexed, not nullable.
- `recorded_at` — `String`, not nullable.
- No foreign key (matching codebase-wide convention: no `ForeignKey` is used anywhere in `atlas/core/infrastructure/persistence/`).

**Child table** `reasoning_trace_supports`, same `MetaData()`:
- `reasoning_trace_support_id` — `String`, primary key, a freshly generated UUID per row. This mirrors `reasoning_link`'s own established precedent of a synthetic per-row primary key (its four tables each use a `link_id` PK) rather than inventing a composite primary key, which has no precedent anywhere in this codebase.
- `reasoning_trace_id` — `String`, indexed, not nullable, no foreign key (same no-FK convention; permanence and the transactional insert below eliminate the dangling-reference risk a FK would otherwise guard against).
- `target_type` — `String`, indexed, not nullable, `CheckConstraint` restricted to the six adopted `DomainObjectType` values, built the same way Knowledge Reference's own `table.py` builds its check constraint (`tuple(member.value for member in DomainObjectType)`).
- `target_id` — `String`, indexed, not nullable.
- `UniqueConstraint` on (`reasoning_trace_id`, `target_type`, `target_id`) — **this is the first use of `UniqueConstraint` anywhere in this codebase** (confirmed by a repository-wide grep during this audit: zero prior uses). It is not introduced casually: it is the direct, schema-level enforcement of the set-semantics conclusion already reached in Section 12 and Section 17, and is exactly as forced as Knowledge Reference's own `CheckConstraint` was when that package was implemented.

**Table creation**: `create_reasoning_trace_tables(engine: Engine) -> None` (plural, since it creates two tables — deliberately distinguished from Knowledge Reference's singular `create_knowledge_reference_table` precisely because Reasoning Trace, unlike Knowledge Reference, genuinely has two tables), calling `metadata.create_all(engine, tables=[reasoning_traces_table, reasoning_trace_supports_table])`. No table is created by merely importing the module — this codebase has no ambient registration mechanism (verified: every existing package requires its own `create_X_table(engine)` to be explicitly invoked from its own `dependencies.py`, and there is no `Base.metadata.create_all` call anywhere in the API startup path). `reasoning_trace/dependencies.py`'s own repository-provider function calls `create_reasoning_trace_tables(engine)` on every resolution, exactly like every other package's provider (idempotent no-op once the tables exist).

**Atomic insert**: `SqlAlchemyReasoningTraceRepository.add()` opens exactly one `with self._engine.begin() as connection:` block (matching every existing repository's transaction pattern) and, within it, issues one `insert(reasoning_traces_table).values(...)` for the parent row followed by one multi-row `insert(reasoning_trace_supports_table).values([... one dict per support ...])` for the child rows. A failure at either insert (e.g., a uniqueness violation, which cannot occur on a fresh `id` but is defensively still inside the same transaction) rolls back both, so a Reasoning Trace is never persisted with a partial support set.

**Reconstruction** (`get()`): two `SELECT`s within one connection — the parent row by `reasoning_trace_id`, then all child rows matching that `reasoning_trace_id`. If the parent row does not exist, return `None` (ordinary "not found," matching every other repository). If the parent row exists, the child rows are collected into a `frozenset[TypedDomainObjectReference]` and the entity is reconstructed via its **ordinary constructor** — not a separate, unchecked path — so `ReasoningTrace.__post_init__`'s non-empty check (Section 27, Section 35) runs on reconstruction exactly as it does on capture.

**Corrupt-state handling, stated explicitly rather than left implicit**: a parent row with **zero** matching child rows can only arise from direct database manipulation outside this repository's own `add()` (which is atomic and always inserts at least one child row, since `ReasoningTrace.capture()` itself refuses to construct an empty-support instance). If it ever occurs, `get()`'s reconstruction step raises `EmptySupportError` from the entity's own `__post_init__` rather than silently returning an entity with an empty `frozenset` — a loud failure on tampered or corrupted data, consistent with this codebase's general stance of trusting its own transactional invariants and not defensively coding around states its own write path cannot produce. **Orphan child rows** (rows whose `reasoning_trace_id` matches no parent row) are unreachable by any read path (they are simply never joined against), and — like every other no-FK table in this codebase — are accepted as an out-of-scope tampering concern, not specifically guarded against, matching the codebase's stated general rationale for omitting foreign keys.

**Deletion is irrelevant**: no `delete` method exists on the repository Protocol (Section 27), so there is no code path that could produce an orphan in ordinary operation.

## 31. API Inclusion Decision (Finalized)

Per Section 20's finalized decision: the API layer ships in this same package. Surface, mirroring Knowledge Reference's own router/schema/dependency/error-handler shape exactly:

- `atlas/core/infrastructure/api/reasoning_trace/schemas.py`:
```python
class CreateReasoningTraceRequest(CamelModel):
    case_id: uuid.UUID
    supports: list[TypedDomainObjectReferenceSchema]  # non-empty; enforced by the service, not by a Pydantic length constraint alone (Section 28 step 3 remains the authoritative check; a Pydantic min_length=1 may additionally be applied at the schema boundary as a cheap first-pass rejection with a 422, but does not replace the service-level EmptySupportError path other clients of the service must also go through)

class ReasoningTraceResponse(CamelModel):
    reasoning_trace_id: uuid.UUID
    case_id: uuid.UUID
    supports: list[TypedDomainObjectReferenceSchema]
    recorded_at: datetime
```
Reuses the existing shared `TypedDomainObjectReferenceSchema` (`atlas/core/infrastructure/api/shared/typed_reference_schemas.py`) unmodified for each set member, exactly as Knowledge Reference already does for its own single target. **JSON array ordering in both the request and the response is presentation-only and carries no semantic meaning** (Section 12) — the domain and persistence layers treat `supports` as a set throughout; the array shape exists only because JSON has no native set literal.

- `atlas/core/infrastructure/api/reasoning_trace/router.py`:
```python
router = APIRouter(prefix="/reasoning-traces", tags=["reasoning-traces"])

@router.post("", response_model=ReasoningTraceResponse, status_code=201)
def create_reasoning_trace(...) -> ReasoningTraceResponse: ...

@router.get("/{reasoning_trace_id}", response_model=ReasoningTraceResponse)
def get_reasoning_trace(...) -> ReasoningTraceResponse: ...
```
No `PATCH`/`PUT`/`DELETE`/list/search route — matching Knowledge Reference's and Judgment's own explicitly-stated exclusion of all of these.

- `atlas/core/infrastructure/api/reasoning_trace/errors.py` — exception-to-status mapping, mirroring Knowledge Reference's table exactly in structure:

| Exception | Status |
|---|---|
| `ReasoningTraceNotFoundError` | 404 |
| `EmptySupportError` | 400 |
| `TargetNotFoundError` | 400 |
| `CrossCaseTargetError` | 400 |
| `UnknownDomainObjectTypeError` (shared) | 400 |
| `InvalidTypedDomainObjectReferenceError` (shared) | 400 |

Pydantic-level shape errors (a missing field, an unrecognized `targetType` string, an empty array if a `min_length=1` schema constraint is used) fall through untouched to FastAPI's default 422, exactly as Knowledge Reference's own `errors.py` already documents.

## 32. Dependency Wiring and Import Graph

`atlas/core/infrastructure/api/reasoning_trace/dependencies.py` needs all five external repositories plus its own. Verified import graph (traced directly against the current, post-"Reference Validation Availability" state of every relevant `dependencies.py` file during this audit):

```python
from atlas.core.infrastructure.api.decision.dependencies import (
    get_decision_engine,
    get_decision_repository,
)
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import (
    get_knowledge_reference_repository,
    get_outcome_repository,
)
from atlas.core.infrastructure.api.judgment.dependencies import get_judgment_repository
```

**No private helper duplication is needed anywhere in this file** — unlike `knowledge_reference/dependencies.py`'s own private `_get_judgment_repository` (needed there specifically because `judgment/dependencies.py` already imports from `knowledge_reference/dependencies.py`, so the reverse import would cycle). `reasoning_trace/dependencies.py` is a brand-new leaf module: nothing in the existing import graph (`decision`, `observation`, `knowledge_reference`, `judgment`) imports from it, in either direction, because it does not exist yet and nothing existing has any reason to depend on it. All four public imports above are therefore safe, direct, and require no private re-implementation. `get_judgment_repository` (public, confirmed by direct inspection of `judgment/dependencies.py`) and `get_outcome_repository`/`get_knowledge_reference_repository` (public, confirmed in `knowledge_reference/dependencies.py`) are reused as-is.

```python
def get_reasoning_trace_repository(
    engine: Engine = Depends(get_decision_engine),
) -> ReasoningTraceRepository:
    create_reasoning_trace_tables(engine)
    return SqlAlchemyReasoningTraceRepository(engine)


def get_reasoning_trace_service(
    repository: ReasoningTraceRepository = Depends(get_reasoning_trace_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    knowledge_reference_repository: KnowledgeReferenceRepository = Depends(get_knowledge_reference_repository),
    judgment_repository: JudgmentRepository = Depends(get_judgment_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
) -> ReasoningTraceService:
    return ReasoningTraceService(
        repository,
        observation_repository,
        knowledge_reference_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
    )
```
Reuses the shared engine from `decision`'s dependencies module (same physical `atlas.db` file), exactly like every other package.

## 33. Composition Boundary

Exactly one existing file requires a change to complete this package: `atlas/core/infrastructure/api/app.py`, gaining one `include_router` call and one `register_..._error_handlers` call, in the same two-line-per-package pattern every existing router already follows:
```python
app.include_router(reasoning_trace_router)
...
register_reasoning_trace_error_handlers(app)
```
No other integration is required or added: not conversation orchestration, not decision commitment, not outcome capture, not `reasoning_link` (Section 23 — untouched, its disposition remains the separate, disclosed-open DO-REC-019 question), not a composite application service, not a Domain Object registry (none exists), not background processing, not a CLI (none exists for Knowledge Reference or Judgment either, so none is added here for symmetry).

## 34. Relationship to Knowledge Reference and Judgment Availability

Knowledge Reference and Judgment remain **entirely unmodified** by this package. `capture_knowledge_reference.py`'s `_CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES` and `capture_judgment.py`'s `_CURRENTLY_CAPTURE_ENABLED_SUBJECT_TARGET_TYPES` continue to exclude `REASONING_TRACE`, exactly as today, because Reasoning Trace's own package does not touch either file.

Once Reasoning Trace has an entity, repository, persistence, Case ownership, and an accepted-instance mechanism (i.e., once this package is complete), widening those two services to accept `REASONING_TRACE` becomes technically possible for the first time — but this document classifies that widening as a **required, immediate, separate follow-on package**, not part of this one, by direct precedent: exactly the same sequencing was already used for Observation, Decision, and Outcome, each of which gained `case_id` in its own separate package, with the widening of Knowledge Reference/Judgment to reference them deferred to the later, dedicated "Reference Validation Availability" package rather than bundled into any one of the three. Implementation of this design must not widen Knowledge Reference or Judgment opportunistically merely because it becomes possible to do so.

## 35. Exact Production Inventory

**New files (15, precisely counted below):**
- `atlas/core/domain/reasoning_trace/__init__.py`
- `atlas/core/domain/reasoning_trace/entity.py` — `ReasoningTrace` (`@dataclass(frozen=True)`, fields `id`, `case_id`, `supports: frozenset[TypedDomainObjectReference]`, `recorded_at`; `__post_init__` rejects an empty `supports` via `EmptySupportError`; `.capture(*, case_id, supports, clock=_utc_now)` classmethod, mirroring `KnowledgeReference.capture`'s exact shape)
- `atlas/core/domain/reasoning_trace/value_objects.py` — `ReasoningTraceId`, structurally identical to `KnowledgeReferenceId`
- `atlas/core/domain/reasoning_trace/exceptions.py` — Section 27
- `atlas/core/domain/reasoning_trace/repository.py` — Section 27
- `atlas/core/application/reasoning_trace/__init__.py`
- `atlas/core/application/reasoning_trace/capture_reasoning_trace.py` — `CaptureReasoningTraceRequest`, `ReasoningTraceService` — Section 28, Section 29
- `atlas/core/infrastructure/persistence/reasoning_trace/__init__.py`
- `atlas/core/infrastructure/persistence/reasoning_trace/table.py` — Section 30
- `atlas/core/infrastructure/persistence/reasoning_trace/sqlalchemy_repository.py` — Section 30
- `atlas/core/infrastructure/api/reasoning_trace/__init__.py`
- `atlas/core/infrastructure/api/reasoning_trace/schemas.py` — Section 31
- `atlas/core/infrastructure/api/reasoning_trace/dependencies.py` — Section 32
- `atlas/core/infrastructure/api/reasoning_trace/router.py` — Section 31
- `atlas/core/infrastructure/api/reasoning_trace/errors.py` — Section 31

**Count by layer**: domain — 5 files. Application — 2 files. Persistence — 3 files. API — 5 files. **Total: 15 new production files.**

**Existing files modified (1):** `atlas/core/infrastructure/api/app.py` (Section 33 — two added lines).

**Existing files NOT modified, confirmed by this audit**: every Knowledge Reference file, every Judgment file, `reasoning_link`'s three files, and every other existing production file — none was found, during exhaustive repository search, to require any change for this package specifically.

## 36. Exact Test Inventory

- `tests/unit/domain/reasoning_trace/__init__.py`
- `tests/unit/domain/reasoning_trace/test_entity.py`
- `tests/unit/domain/reasoning_trace/test_value_objects.py`
- `tests/unit/application/reasoning_trace/__init__.py`
- `tests/unit/application/reasoning_trace/test_capture_reasoning_trace.py`
- `tests/unit/infrastructure/persistence/reasoning_trace/__init__.py`
- `tests/unit/infrastructure/persistence/reasoning_trace/test_sqlalchemy_repository.py`
- `tests/unit/infrastructure/api/reasoning_trace/__init__.py`
- `tests/unit/infrastructure/api/reasoning_trace/test_router.py`

**No existing test file requires modification.** This was explicitly re-checked during this audit (as it was during the immediately preceding readiness audit): Knowledge Reference's and Judgment's own test suites reference `REASONING_TRACE` only inside their own "currently unavailable target types" fixtures, which remain correct and unchanged, since Section 34 keeps that exclusion in place for this package.

## 37. Behavioral Test Matrix

**Domain** (`test_entity.py`): valid construction with one support; valid construction with multiple supports across different types; empty-support construction raises `EmptySupportError`; duplicate typed references in the constructor input collapse via `frozenset` (verified by constructing from a list containing a repeated tuple and checking the resulting `len(supports)`); required `case_id` (omitting it is a `TypeError`, matching every other frozen dataclass in this codebase); independent identity (two instances built from identical arguments, including identical support sets, have distinct `id`s and are unequal, since `ReasoningTrace` uses default dataclass equality exactly like `KnowledgeReference` — no `eq=False` is introduced, since nothing in OE-002 requires content-based equality here, unlike the unrelated `FormationAct` precedent from a different module); `recorded_at` is acceptance time via an injectable clock; immutability (attribute assignment raises `FrozenInstanceError`); support ordering has no observable effect on equality or persistence (two instances built from the same set presented in different input orders are identical in stored/reconstructed form).

**Application** (`test_capture_reasoning_trace.py`), for every one of the six supported target types (Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome) where feasible:
- successful capture referencing an existing, same-Case, already-accepted object of that type;
- missing target of that type → `TargetNotFoundError`;
- cross-Case target of that type → `CrossCaseTargetError`;
- multiple valid supports spanning several different types in one capture;
- one invalid support among several otherwise-valid supports → the correct exception is raised, deterministically, per the sorted order defined in Section 28 (a dedicated test constructs the same invalid input twice and asserts the same exception and message both times, and a second test with two different invalid supports asserts specifically which one is reported, per the stable sort);
- no partial persistence on rejection (the repository remains empty/unaffected after any rejected capture attempt);
- empty support collection rejected via `EmptySupportError` before any repository is queried (verified with a spy/counting fake repository asserting zero `.get()` calls occurred);
- duplicate input references collapse rather than erroring;
- the first Reasoning Trace in a brand-new Case, supported by a non-Trace object, succeeds (confirming non-root-eligibility is naturally satisfied rather than specially handled — INV-012);
- a later Reasoning Trace successfully citing a previously-accepted Reasoning Trace as one of its supports;
- literal self-reference cannot be expressed as a test at all, since a candidate has no `id` prior to construction (Section 28) — this absence-of-a-test-case is itself the correct demonstration, not an oversight, and the design states so explicitly rather than fabricating a vacuous test.

**Persistence** (`test_sqlalchemy_repository.py`): one-support round-trip; multi-support round-trip; type preservation across all six target types; Case preservation; the composite `UniqueConstraint` rejects a direct duplicate-row insert at the SQL level; parent+child insertion is atomic (a forced failure on the child insert, e.g. via a duplicate-row conflict, leaves no parent row behind — verified by attempting the same `add()` twice with an artificially repeated child tuple and confirming the parent table remains empty); a corrupted parent-row-with-zero-child-rows scenario (constructed directly via raw SQL in the test, bypassing the repository's own `add()`) causes `get()` to raise `EmptySupportError`, not return a malformed entity; the `target_type` `CheckConstraint` rejects an unrecognized value at the SQL level; retrieval of a nonexistent id returns `None`; no `update`/`delete` method exists on the repository class at all (a structural/`hasattr`-style test, matching how this property is verified for Knowledge Reference).

**API** (`test_router.py`): `POST` success with one support; `POST` success with multiple supports across different types; `GET` success; `GET` for a missing id → 404; empty `supports` array → 400 (`EmptySupportError`, via the service; a `min_length=1` schema-level 422 is a distinct, separately tested path if that constraint is added per Section 31); missing target → 400; cross-Case target → 400; representative coverage of all six target types where the underlying fixture already provides an accepted instance to reference; camelCase alias round-trip (`caseId`, `reasoningTraceId`, `targetType`, `targetId`, `recordedAt`); response serialization matches the domain entity exactly; JSON array ordering of `supports` in the request has no effect on the resulting stored/returned set; test fixtures use one shared in-memory `StaticPool` engine with every needed table created and every needed repository-provider dependency overridden, mirroring exactly the pattern established for Knowledge Reference's and Judgment's own widened test fixtures in "Implement Reference Validation Availability."

## 38. Explicit Package Exclusions

This package, and its implementation, must not include: widening Knowledge Reference or Judgment to accept `REASONING_TRACE` targets (Section 34 — separate, immediate follow-on); any `reasoning_link` reinterpretation, migration, or retirement (Section 23, Section 33); conversation orchestration, decision orchestration, or outcome-capture integration; a CLI; `PATCH`/`PUT`/`DELETE`/list/search endpoints; any change to the `ReasoningTraceRepository` Protocol beyond `add`/`get`; a generic polymorphic repository abstraction; any new ontology, additional semantic field, narrative/reasoning content, or sequence/chronology semantics (Section 11, Section 16 — unchanged by this audit); any migration script (no existing data needs migrating into these new tables; `reasoning_link`'s rows remain, at most, potential future seed data per Section 23, not something this package converts); and any opportunistic cleanup unrelated to Reasoning Trace itself.

## 39. Implementation Authorization Boundary

This document, including the corrections and additions made by this audit, does not itself authorize implementation. It is a design artifact; implementation requires its own, separate, explicitly scoped task, exactly as every prior Domain Object in this series (Case, Knowledge Reference, Judgment) was implemented only after its own design received exactly this kind of audit-and-commit pass first. That future implementation task must follow Sections 27–38 exactly — no additional capability may be included merely because it would be convenient or symmetrical to add while the files are already open, and the Knowledge Reference/Judgment widening described in Section 34 remains a separate task, not something to fold in "while already in the area."

---

## Relation Completeness Review

*Appended after initial completion, as a focused corrective review. This section re-examines the finding above rather than assuming it was correct merely because it was already written. Sections 1, 8, 14, 15, and 24 above were edited in place to reflect the correction reached here; all other sections are unchanged, since nothing else in the original design depended on the error identified below.*

### Review Question

Can a Reasoning Trace faithfully assert a support relationship when its representation identifies only the purported supporters and does not identify what is supported?

### Re-Examination of the Exact Canonical Text

OE-002 §5.3, in full, quoted again here because this review's conclusion turns on a precise reading of it:

> **Definition.** Reasoning Trace is a permanent Domain Object that represents one or more already-accepted Domain Objects as providing epistemic support.
>
> **Identity.** Reasoning Trace has stable identity independent of its content and independent of the identity of the Domain Objects it represents as supporting.
>
> **Responsibility.** Reasoning Trace is responsible for recording that specified, already-accepted Domain Objects stand in a support relationship, without itself asserting a stepwise process, chronology, or narrative rationale.
>
> **Ownership boundary.** Every supporting Domain Object MUST belong to the same Case as the Reasoning Trace and MUST already exist as an accepted Domain Object. Reasoning Trace requires at least one supporting Domain Object. Reasoning Trace is not root-eligible.
>
> **Relationships.** Reasoning Trace MAY be supported by one or more other Domain Objects defined in this document, drawn from the same Case. Whether Reasoning Trace additionally contains, or instead references, a distinct supported claim is not settled by this document; where a supported claim is represented as a reference, it MUST be to another same-Case Domain Object. Additional constraints on which Domain Objects MAY occupy the supporting role are governed by Domain Invariants and are not stated in this document.

The original design (Sections 1 and 8, before correction) read the Definition clause's "providing epistemic support" as support directed at an unspecified external target, and treated the Relationships clause's "distinct supported claim" sentence as the *entirety* of the "what is supported" question, concluding that the whole question was open. Re-reading the Relationships clause's first sentence on its own — **"Reasoning Trace MAY be supported by one or more other Domain Objects"** — its grammatical subject is the Reasoning Trace itself, and "supported by" identifies it as the recipient of the support, exactly parallel to how OE-002 phrases every other object's own Relationships section (e.g., Observation §5.1: "Observation MAY be referenced by other Domain Objects," where Observation is unambiguously the target of the reference). Applying that same, consistently-used construction here: the Trace itself is already, textually, the base-case recipient of the support its supporting objects provide. The *second* sentence — about a "distinct supported claim" — then introduces a **separate, additional, optional** question: whether something *further*, beyond the Trace's own being-supported, is also identified as supported (most plausibly a specific Judgment). That second question is genuinely open; the first is not. The original design conflated the two, and concluded the whole relation was open when only the narrower, second part is.

### Question 1 — Arity of the Relationship

The relationship is **binary**: one side is the (one-or-more) supporting-object set; the other side is the Reasoning Trace itself, identified by its own `id`. It is **directed** (support flows from the supporting objects toward the Trace) and is **not** internal-only, since the supporting-object side references external, independently-accepted objects. It is not unary (it relates two things, not one), not undirected (support has a stated direction — objects provide support *for* the Trace, not the reverse), and not merely a set of participants with no defined relation — OE-002's own Relationships clause supplies the second relatum directly. The n-ary reading (with multiple simultaneous roles) does not apply here; every supporting object occupies the same single role (supporter), and the Trace occupies the single, fixed role of recipient.

### Question 2 — What Is Supported

At the base, settled level: **the Reasoning Trace itself**. Nothing further is identified by canonical material as also, necessarily, supported. A further, distinct supported claim (a Judgment, a conclusion, a Decision) is explicitly left open by OE-002's own text and is not recoverable by logical necessity from anything else in OE-002 through OE-006 — it is recoverable, if at all, only from a *future* object's own reference *to* the Trace (e.g., a Judgment that cites this Trace as informing it), which is external to the Trace and not part of its own stored content.

### Question 3 — What "Supporting Object" Means

A supporting object is one the Case treats as providing epistemic grounding for the Trace's own existence as a recorded fact — not bare association, inclusion, or provenance. What distinguishes this from generic association is addressed directly in Question 6 below.

### Question 4 — Can the Trace Be Its Own Relation Endpoint?

Tested directly, per the review's own required test: is this circular or empty? It is not. There is no infinite regress — the Trace's own identity is assigned independently (a freshly generated id, exactly like every other Domain Object), and does not depend on first evaluating whether its supporting objects support it; the relation is a single, flat, well-founded fact: "these already-accepted objects provide support, and this Trace is the record of that fact, identified by its own id." This is structurally ordinary, not paradoxical — comparable to an ordinary accepted record whose own identity is simply assigned, with the record's content being *about* its relation to other things, not about itself in a way that requires resolving itself first. It is not empty: it excludes candidates that fail INV-004/INV-005 (cross-Case or unaccepted objects cannot occupy the supporting role), so the relation has real, falsifiable content, not a tautology. **Test 4 (Section "Required Contradiction Tests" below) is answered explicitly using this reading.**

### Question 5 — Can Ownership Supply the Missing Endpoint?

Not needed under the corrected reading, since no endpoint is missing — but tested anyway, for completeness. Case ownership does not and cannot supply a supported-claim endpoint: a Case is a boundary containing many objects, not itself a single proposition capable of being "supported." A mandatory Judgment association is not established anywhere in OE-002 — Judgment's own text (§5.4) states it "does not require... prior epistemic support from a Reasoning Trace," which is phrased as optional, not mandatory, and in the *opposite* direction (Judgment optionally depending on a Trace, not a Trace being mandatorily owned by a Judgment). No Decision-flow position or external aggregate root is named anywhere as determining a Trace's supported endpoint. This interpretation is rejected as an account of how the endpoint is resolved — it is resolved by Section 8's finding, not by ownership.

### Question 6 — Is the Current Set Representation Merely a Container?

This is the review's most serious remaining tension, and it is not fully dissolved by Question 4's answer. Applying **Test 6** directly: if the field `supporting-object references` were renamed `related-object references`, the stored structure — an id, a case_id, a set of typed references, a timestamp — would not change at all. This means the *storage shape alone* does not distinguish "support" from generic grouping; nothing about the shape itself would be lost by that renaming. What does distinguish it is that this shape is being accepted **as an instance of the specific, adopted `Reasoning Trace` type**, whose institutional meaning is fixed by OE-002 §5.3's own text: accepting a candidate as a `ReasoningTrace` (as opposed to some undefined generic `RelatedObjectGroup`) is itself the act that asserts "the Case treats these objects as epistemically supporting this record," precisely because that is what OE-002 says accepting a Reasoning Trace *means*. The same reasoning was already, correctly, relied upon for Knowledge Reference (whose own field shape — an id, a case_id, one typed target reference, a timestamp — is likewise indistinguishable, in raw shape, from a generic link record; what supplies its "reliance-as-knowledge" meaning is exactly the same thing: the specific, adopted type being instantiated, not the field names). This is a legitimate, non-circular way for an architecture to carry meaning — the type tag is doing semantic work, not the column names — but it is a real, disclosed limit: nothing about the *persisted data alone*, read without knowledge of which OE-002-defined type produced it, would recover the word "support." This is stated honestly rather than concealed, per the review's own decision standard.

### Question 7 — Does OE-002 Permit Deferral?

Yes, and the corrected reading shows precisely why: OE-002's own open question is narrower than "the relation is incomplete" — it is exactly "whether a *further* distinct claim exists beyond the Trace's own being-supported." The *base* relation (supporting objects → the Trace) is not deferred; it is already settled by the Relationships clause's own text, and can be fully implemented today without resolving the narrower question. This matches the "yes, because the endpoint is already determined elsewhere" branch of the required answer set, with the correction that "elsewhere" is not an external object but the Trace's own identity.

### Question 8 — Does Final Adoption Force Immediate Implementability?

Final adoption settles that Reasoning Trace exists as one of the six Domain Object types and settles its base semantic contract (support directed at the Trace itself, per the corrected reading). It does not settle, and does not need to settle, whether a further distinct claim is ever added — that remains a genuinely open internal edge, permitted to stay open under Doctrine §7, without blocking today's implementation of the base object. Final adoption is not used here to manufacture the missing semantics; the base semantics were already present in the adopted text, and this review's contribution is a corrected reading of already-adopted material, not a new invention.

### Candidate Outcomes — Disposition

- **Outcome A (current design is complete)** — **Adopted, with a corrected sentence.** Direct, precise canonical support: OE-002 §5.3's own "Reasoning Trace MAY be supported by..." construction, read with the same grammatical convention OE-002 uses consistently elsewhere in the same section for every other Domain Object's Relationships clause.
- **Outcome B (externally determined endpoint)** — Rejected as an account of the mechanism (Question 5): no external owning object supplies the endpoint; it is the Trace's own identity, not an external one.
- **Outcome C (endpoint must be added as a new field)** — Rejected: no new field is required, since the endpoint is the Trace's own already-present `id`.
- **Outcome D (internal supported-claim content required)** — Rejected: not required for the base relation; remains an open, deferred, *further* question (Section 24, Q1), not a requirement.
- **Outcome E (meaning must be weakened)** — Rejected as the principal outcome, but Question 6's finding is retained precisely as a disclosed limit: the *type tag*, not the field shape, is what carries the "support" meaning beyond bare association. This is not a weakening of the claim, but an honest account of *how* the claim is carried.
- **Outcome F (implementation must be deferred)** — Rejected for the base object: the base relation is fully expressible today. The narrower "further distinct claim" question remains genuinely deferred, exactly as OE-002 itself defers it (Section 24, Q1) — this is not a blocking deferral of the whole design.
- **Outcome G (identity shell only)** — Rejected as insufficient: it understates what is actually established; the design is not an empty shell, it is a complete base relation.

### Required Contradiction Tests

**Test 1 — Two different intended conclusions from the same three supporting objects.** Each Reasoning Trace is its own, independently-identified accepted fact: "X, Y, Z support Trace A" and, separately, "X, Y, Z support Trace B." If Judgment-1 later references Trace A and Judgment-2 later references Trace B (via whatever mechanism eventually links Judgment to Reasoning Trace, a question left to the Judgment implementation design), the two conclusions are correctly distinguished — but that distinguishing fact lives in the *later* Judgments' own references to the Traces, not in the Traces themselves. Looked at in isolation, with identical supporting-object sets, Trace A and Trace B are semantically identical apart from being two numerically distinct tokens of the same base fact. This is disclosed, not concealed: it is analogous to, and no more troubling than, the already-accepted conclusion that two Knowledge References may duplicate the same target as two distinct facts.

**Test 2 — Same supporters, opposite conclusions.** Handled identically to Test 1: two distinct Traces, each independently accepted, each later citable by a different, opposite-concluding Judgment. The Trace does not itself distinguish the conclusions — consistent with, and required by, its own Responsibility clause explicitly disclaiming any assertion about a resulting conclusion.

**Test 3 — One object in multiple roles (supports one conclusion, undermines another).** Reasoning Trace, as adopted, has **no "undermine" or "challenge" role at all** — OE-002 §5.3 speaks only of objects "providing epistemic support," never opposition. This is a genuine, disclosed scope boundary of the adopted type, not a defect introduced by this design: the same object may appear as a supporter in one Trace and simply be *absent* from another, but there is currently no adopted mechanism, anywhere in OE-002 through OE-006, for representing that an object undermines something. This is consistent with the Legacy Correspondence investigation's own finding that Evidence's `direction` (SUPPORTS/CHALLENGES) annotation is an unresolved legacy concept, not yet part of the adopted Reasoning Trace ontology.

**Test 4 — Singleton trace.** With exactly one supporting reference to object X, the complete proposition asserted, without inserting any unstored endpoint, is: **"Within Case C, object X is treated as providing epistemic support for this Reasoning Trace."** No unstored endpoint is inserted — "this Reasoning Trace" is the object's own identity, already present.

**Test 5 — Duplicate trace.** Two Traces with identical `case_id` and identical reference sets, differing only in `id` and `recorded_at`, represent **two independent, numerically distinct assertions of the same underlying fact** — not an error, not forbidden, and not required to be deduplicated, for the same reason duplicate Knowledge Reference targets are permitted. The ontology does not explain *why* one would want two such duplicates, but it does not need to; nothing in OE-002 through OE-006 prohibits it, and Doctrine's own minimality discipline counsels against inventing a prohibition unsupported by any invariant.

**Test 6 — Removal of the word "support."** Addressed fully in Question 6 above: no stored structure changes; the word's semantic weight is carried by the adopted type itself (`ReasoningTrace`, with its own `ReasoningTraceAccepted` correspondence), not by the field names. This is disclosed as a genuine, non-trivial limit of the design, not concealed.

### Corrected Executive Finding

*(Restated here for clarity; the authoritative copy is in Section 1, corrected above.)* A Reasoning Trace is a permanent, independently-identified Domain Object that records, as its entire settled semantic content, that one or more specified, already-accepted, same-Case Domain Objects provide epistemic support for the Reasoning Trace itself, without asserting any stepwise process, chronology, narrative rationale, or the truth or validity of that support. Whether a further, distinct supported claim exists beyond the Trace remains exactly as open as OE-002 leaves it.

### Corrected Accepted Fields

**Unchanged**: `id`, `case_id`, a non-empty set of typed supporting-object references, `recorded_at`. No field was added or removed by this review. What changed is the stated meaning of the relation these fields express, not the fields themselves.

### Final Determination on This Review

The previous design was **not fully semantically complete as written**, though its field set was, by correct derivation, already adequate. Its prose asserted a "support relationship" without identifying a recipient, which is precisely the incompleteness the review's central question was testing for. The correction is textual and interpretive, not structural: OE-002 §5.3 already, textually, supplies the missing endpoint (the Trace itself), and no new field, table, or invariant is required. Reasoning Trace, under the corrected reading, **is implementation-ready** for its base relation; the further "distinct supported claim" question remains open and non-blocking, exactly as OE-002 itself leaves it. Section 6 of this review records, honestly, that the "support" meaning is carried by type identity rather than by field shape alone — a real property of this design, not a defect requiring further correction.

*(A further, deeper coherence question — whether identifying the Trace as the grammatical recipient of support actually supplies determinate semantic content, given the Trace has no independent content of its own — is addressed by the Self-Support Coherence Review immediately below, appended after this Relation Completeness Review was itself completed.)*

---

## Self-Support Coherence Review

*Appended after the Relation Completeness Review, as one further, focused review. This section does not reopen the full investigation; it tests the specific coherence question the prior review's own resolution invited but did not fully answer. Sections 1 and 8 above were edited in place to reflect this review's correction. The accepted field set (Section 15) is unchanged — this review's correction is entirely interpretive.*

### Exact Question

Is "Reasoning Trace MAY be supported by one or more other Domain Objects" sufficient to establish a non-circular, implementation-ready semantic meaning when the Trace contains no independently specified claim, conclusion, proposition, or output beyond the support relation itself? What exactly is being epistemically supported when the Trace's entire stored content is the fact that specified objects support it?

### 1. The Exact Proposition Represented by One Trace Instance

Let `RT-1` be a Reasoning Trace in Case `C`, with supporting objects `A` and `B`. The complete proposition, stated without hidden content and without inserting anything beyond what is stored, is:

> Within Case `C`, `A` and `B` are each an already-accepted, same-Case Domain Object, and `RT-1` is the accepted record of the fact that `A` and `B` jointly satisfy OE-002's adopted admission criteria for standing in the "epistemic support" relation whose recipient is `RT-1`'s own existence as this specific accepted record.

Nothing more is asserted. In particular, this proposition does **not** assert that `A` or `B` are true; does not assert that `RT-1` embodies any further claim, conclusion, or output distinct from this fact; and does not assert that "epistemic support" here decomposes into ordinary evidential, logical, or justificatory support. The only semantic property of `RT-1` being supported is `RT-1`'s own existence as this particular accepted record — not an independent proposition `RT-1` is alleged to embody, because `RT-1` embodies no further proposition.

### 2. Circularity Determination

Restated plainly: `RT-1` records that `A` and `B` support `RT-1`, and `RT-1` has no semantic content beyond recording that fact. Tested against the offered classifications, this is: **a valid primitive self-referential relation with a fixed, stipulated semantic interpretation — not an empty semantic loop, and not an underdefined ontology.**

It is not an empty semantic loop, because the relation is not vacuously true of everything: a candidate fails to be a valid `RT-1` unless every supporting object is already accepted (INV-005), belongs to the same Case (INV-004), and the set is non-empty (INV-013). These admission criteria give the relation real, falsifiable content — many candidate object-sets are *excluded*, which is precisely what distinguishes a non-vacuous relation from a tautology. It is not merely "a circular but coherent identity condition" either, because the circularity here is not about *identity* (`RT-1`'s own identity is assigned independently, exactly like every other Domain Object's, and does not depend on evaluating the support relation first) — it is about *content*: the relation's target has no content beyond the relation itself. This is best classified as a primitive relation whose entire meaning is exhausted by its own admission and exclusion criteria, not by an independently articulated truth-apt target — a legitimate architectural pattern, not a logical defect, provided it is explicitly acknowledged as primitive rather than described as though it carried richer content. This document now does so.

### 3. Truth-Aptness Determination

Tested directly against the required candidates:

- **Candidate A (the Trace is truth-apt; identify the proposition)** — **Rejected.** No canonical text identifies any proposition `RT-1` embodies beyond the bare fact of Section 1 above. Inventing one would add unstated content, which this review's own governing instruction ("do not add a supported claim merely to avoid philosophical discomfort") forbids.
- **Candidate B (not truth-apt; support does not require truth-aptness; a primitive relation)** — **Adopted.** Canonical basis: Architecture Doctrine §14 — "Architectural terms MUST be defined by their normative contracts as stated in the governing document. Architectural terms MUST NOT be interpreted by ordinary-language association where a normative contract exists." OE-002 §5.3 is that normative contract for "epistemic support" as applied to Reasoning Trace, and its full content is exhausted by: which objects may occupy the supporting role (any accepted, same-Case object, at least one, per INV-013 and OE-002's own "no specific Domain Object type is required" clause) and what is explicitly excluded (a stepwise process, chronology, or narrative rationale). Nothing in that contract requires the recipient to be independently truth-apt; requiring that would be importing an external, ordinary-language philosophical expectation Doctrine §14 explicitly tells this design to resist.
- **Candidate C (support targets the Trace's existence or acceptance)** — **Adopted as the closest available paraphrase of Candidate B**, not as a distinct, competing reading. Once "support" is understood as a primitive relation rather than a decomposed evidential one, the least-loaded available description of its target is exactly the Trace's own existence as an accepted record — Candidate B supplies the formal classification (primitive, not decomposed), and Candidate C supplies the plainest available paraphrase of what that primitive amounts to.
- **Candidate D (implicit, unfielded semantic content recoverable identically by every implementation)** — **Rejected.** No canonical text supplies a mechanism by which any implementation could recover further content beyond the bare relation; nothing is presumed here that is not stated.
- **Candidate E ("underdefined," structural implementation may proceed regardless)** — **Rejected as stated, though its practical conclusion is retained.** This design does not treat the relation as merely "underdefined" (which would suggest an incomplete specification awaiting future completion); rather, per Candidate B, it is *completely* defined *as a primitive* — nothing is missing, because a primitive relation's definition is exhausted by its admission/exclusion criteria, not left short of one. The practical upshot — implementation may proceed without further philosophical interpretation — is retained, but the word "underdefined" is not, since it would misdescribe a complete-as-primitive relation as an incomplete one.
- **Candidate F (circular, not implementation-ready)** — **Rejected**, per the Circularity Determination above.

### 4. Is "Epistemic Support" Canonical, or Overstated?

**Canonical, not overstated — but retained as a primitive term, not a richly interpreted one.** OE-002 §5.3's Definition clause literally states the phrase: "represents one or more already-accepted Domain Objects **as providing epistemic support**." This is not a term this design introduced; it is quoted directly from the governing document. The relation is classified as exactly one of the offered options: **an uninterpreted primitive relation** — not logical support, evidential support, justificatory support, or generic support in any further-decomposed sense, because none of those richer classifications is established by canonical text, and adopting one would add content beyond what OE-002 states. The word "epistemic" is retained because it is literally canonical; what changes is that this design no longer implies the word carries the full weight ordinary epistemology would assign it.

### 5. Does the Type Tag Carry Defined Semantics, or Merely a Label?

**Type-discriminated semantics, not mere type-label substitution — but bounded, and the boundary is stated honestly.** Canonical material defines, precisely, which candidates may be admitted as a `ReasoningTrace` (INV-001's closed-type-set membership, combined with INV-013's specific "at least one, no upper bound, no type restriction" cardinality, as distinct from, say, INV-014's "exactly one" for Knowledge Reference) and what is excluded (process, chronology, narrative). This is real, machine-checkable, type-discriminated content — accepting a candidate as a `ReasoningTrace` specifically routes it to INV-013's check rather than some other invariant, which is a substantive, not merely nominal, distinction. What the type tag does **not** do is redeem the full ordinary-English connotation of "epistemic support" (evidential weight, justification, warrant) — that richer connotation is not established by canonical text and is not claimed here. The type name is evocative of more than the ontology currently commits to; this design does not rely on that evocation to do work the ontology itself has not done, and states so explicitly rather than letting the name imply otherwise.

### 6. Comparison With Other Relationship Clauses

The same grammatical pattern ("X MAY be Y-ed by Z") does **not** prove equivalent semantic completeness across different relation verbs, and this design does not assume otherwise. Reference relations (Observation "MAY be referenced by other Domain Objects"; Knowledge Reference "MAY reference any other Domain Object") are semantically self-sufficient with a bare pointer target — "reference," in ordinary usage, never presupposed truth-aptness of its target, so identifying the target fully completes the relation. "Support," in ordinary usage, typically does presuppose a truth-apt or evaluable target (one supports a *claim*), which is exactly why this review's challenge had real force where an equivalent challenge against Knowledge Reference's reference relation would not. The resolution here is not that support and reference are the same kind of relation reaching the same kind of completeness by the same mechanism; it is that OE-002 uses "support," for Reasoning Trace specifically, in a narrower, stipulated, technical sense that deliberately does not carry the ordinary-language presupposition — a distinct and more demanding semantic repair than reference relations ever required, made explicit here rather than assumed.

### 7. Ontology Completeness, Contract Completeness, Explanatory Completeness

- **Ontology completeness**: achieved, for the base primitive relation — OE-002, together with INV-004, INV-005, and INV-013, fully specifies who may be a supporter, how many are required, and what is excluded. The narrower, further "distinct supported claim" question remains open, exactly as already documented, and this does not block the base relation's own completeness.
- **Contract completeness**: achieved — a faithful persistence and validation contract (Section 15, Section 19, Section 21) can represent the adopted relation exactly, using INV-013 as the concrete, testable admission rule, without needing to resolve any richer philosophical interpretation.
- **Explanatory completeness**: **not achieved, and not required.** No richer reasoning narrative explaining *why* this counts as epistemic support in a fully philosophically satisfying sense is established or attempted here, consistent with the governing instruction that this level of completeness is not needed for implementation.

### 8. Where the Implementation Semantics Reside

Precisely: in **OE-002 §5.3's admission and exclusion criteria as enforced by INV-004, INV-005, and INV-013 at validation time**, combined with **the closed-type discriminator (INV-001) that routes a candidate specifically to INV-013's cardinality rule rather than any other invariant's**. They do not reside in the scalar column shape alone (Empty-Payload Test, below), and they do not reside in any richer, undocumented interpretation of "epistemic."

### Duplicate-Instance Test

Two Traces with identical `case_id` and identical supporting-object sets, differing only in `id` and `recorded_at`, are **distinct accepted Domain Objects with identical semantic content** — not "two reasoning occurrences" (an undefined concept, not introduced here), and not merely "no canonical distinction beyond identity" in a dismissive sense. Independent identity alone is sufficient for this to be coherent: OE-002 §5.3's own Identity clause and INV-006 require only numerical distinctness, never content-distinctness, and this is the same, already-accepted conclusion reached for Knowledge Reference's own duplicate-target case.

### Empty-Payload Test

Stripped of type name, field labels, and prose, the retained shape — one identifier, one Case identifier, a set of typed references, one timestamp — is not distinguishable from any other typed-reference container **by its scalar shape alone**. The distinction lives entirely in **the validation/acceptance contract**: specifically, which invariant is checked against the claimed type's reference count and content at acceptance time (INV-013's "at least one, no upper bound" for a claimed `ReasoningTrace`, as opposed to INV-014's "exactly one" for a claimed `KnowledgeReference`, or no cardinality requirement at all for a claimed root-eligible `Observation`), routed there by the closed-type discriminator (INV-001). A database column diff alone would not reveal this; the implementation contract's own validation logic is where the semantics are determinable.

### Final Outcome Selection

**Outcome 2 — Structurally Ready, Semantically Primitive.** The repository requires a typed support relation directed at the Reasoning Trace, adopts a precise admission/exclusion criterion for it (INV-013, INV-004, INV-005), but does not further define the philosophical nature of "support" beyond that primitive. Implementation may proceed on exactly this basis. Outcome 1 is not selected because it would overstate matters by implying full richness without acknowledging the relation's primitive, stipulated character. Outcome 3 is not selected because it would require dropping "epistemic" entirely, understating what canonical text literally states. Outcome 4 is not selected because the relation *can* be named and given a precise (if primitive) interpretation — it is not left uninterpretable. Outcome 5 is not selected because the relation is not circular or empty, per the Circularity Determination above.

### Corrections Made

The Executive Finding (Section 1) and Selected Ontological Meaning (Section 8) were both revised to state explicitly that "epistemic support" is retained as canonical wording but treated as a primitive, stipulated relation under Doctrine §14, and that the Reasoning Trace is not claimed to be truth-apt or to embody any independent proposition. **No field was added, removed, or renamed** — Section 15's accepted-field list is unchanged, since nothing in this review's finding forces a structural change; the correction is entirely in how the relation is described, not in what is stored.

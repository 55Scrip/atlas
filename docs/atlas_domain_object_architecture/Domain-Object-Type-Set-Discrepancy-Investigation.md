# Domain Object Type-Set Discrepancy Investigation

## 1. Title

Atlas Core — Domain Object Type-Set Discrepancy Investigation.

## 2. Status

Engineering investigation artifact. Not a normative document; carries no Doctrine status (Draft/Final/Superseded/Historical) — those statuses apply only to documents amending the architecture itself (Doctrine §14), and this document does not amend anything. Where anything here appears to conflict with OE-002 or the Architecture Doctrine, those documents govern and this one is wrong and must be corrected. This document's own authority is limited to stating, precisely and with full citation, what the existing normative sources already say — it does not, and under Doctrine §13's Change Protocol cannot, itself add, remove, or redefine any Domain Object type.

## 3. Exact Question

What is the canonically adopted closed set of Domain Object types that may serve as typed-reference targets? Specifically: (1) is Case a member of the adopted Domain Object Set; (2) may Case be the target of a typed Domain Object reference; (3) does Observation remain an adopted Domain Object; (4) may Observation be the target of a typed Domain Object reference; (5) are "Domain Object Set" and "valid reference-target set" necessarily identical; (6) has any later accepted source explicitly amended or superseded OE-002 §4; (7) does the substitution of Case for Observation in later briefs carry any formal architectural authority.

## 4. Scope

Limited strictly to the Case/Observation type-set discrepancy identified during DO-IMP-002. Does not reopen any other settled question from the Knowledge Reference, Reasoning Trace, Judgment, Decision, or Outcome Implementation Designs, and does not revisit the internal-versus-referential coexistence question already settled (as an explicitly open, non-blocking question) for Judgment, Decision, and Outcome.

## 5. Non-Goals

Does not amend OE-002. Does not create a new normative document. Does not modify the uncommitted DO-IMP-002 implementation, DO-IMP-001, the Domain Object Implementation Reconciliation Plan, or any other file. Does not resolve unrelated ontology. Does not manufacture an architectural decision this document has no authority to make (Doctrine §13's Change Protocol requires a distinct investigation → decision → upstream-document-amendment sequence that this document does not, and cannot by itself, complete).

## 6. Sources Reviewed

Read directly, in full or by targeted section, not by summary:

| Document | Path | Status |
|---|---|---|
| Architecture Doctrine | `docs/atlas_domain_object_architecture/Doctrine.md` | Final |
| OE-002 — Domain Object Model | `docs/atlas_domain_object_architecture/OE-002-Domain-Object-Model.md` | Final |
| OE-003 — Domain Event Model | `docs/atlas_domain_object_architecture/OE-003-Domain-Event-Model.md` | Final |
| OE-004 — Domain Invariants | `docs/atlas_domain_object_architecture/OE-004-Domain-Invariants.md` | Final |
| OE-005 — Domain Validation Model | `docs/atlas_domain_object_architecture/OE-005-Domain-Validation-Model.md` | Final |
| OE-006 — Domain Acceptance Model | `docs/atlas_domain_object_architecture/OE-006-Domain-Acceptance-Model.md` | Final |
| Historical Decision Record | `docs/atlas_domain_object_architecture/Historical-Decision-Record-Domain-Object-Architecture-Foundation.md` | Historical |
| Knowledge Reference Implementation Design | — | **Absent.** Confirmed absent under this or any name in a prior investigation (Outcome-Implementation-Design.md §3, §43 Q5) and reconfirmed here; not fabricated. |
| Reasoning Trace Implementation Design | `docs/atlas_domain_object_architecture/Reasoning-Trace-Implementation-Design.md` | Engineering design artifact, no Doctrine status |
| Judgment Implementation Design | `docs/atlas_domain_object_architecture/Judgment-Implementation-Design.md` | Engineering design artifact, no Doctrine status |
| Decision Implementation Design | `docs/atlas_domain_object_architecture/Decision-Implementation-Design.md` | Engineering design artifact, no Doctrine status |
| Outcome Implementation Design | `docs/atlas_domain_object_architecture/Outcome-Implementation-Design.md` | Engineering design artifact, no Doctrine status |
| Domain Object Implementation Reconciliation Plan | `docs/atlas_domain_object_architecture/Domain-Object-Implementation-Reconciliation-Plan.md` | Engineering planning artifact, no Doctrine status (states this of itself, §2) |
| Uncommitted DO-IMP-002 implementation | `atlas/core/domain/shared/domain_object_type.py`, `typed_reference.py`, `exceptions.py`; `atlas/core/infrastructure/api/shared/typed_reference_schemas.py` | Untracked, uncommitted code |
| Committed DO-IMP-001 implementation | `atlas/core/domain/case/entity.py` and siblings (commit `f8048a7a112d7846185736482309376b7eb01144`) | Committed code |
| Existing Observation implementation | `atlas/core/domain/observation/`, `atlas/core/infrastructure/persistence/observation/`, `atlas/core/infrastructure/api/observation/` | Committed, pre-existing code (predates this governance track) |

**Confirmed absent** (searched, not found, per the already-established findings this investigation reuses without re-deriving): OE-001; an "Architecture Baseline" document under that exact name; an "Architecture Review Summary" document under that exact name; any OE-007 (the Historical Decision Record confirms OE-007 — a proposed "Domain Rejection Model," unrelated to this question — was investigated but never published, and no file exists for it).

## 7. Source Authority and Precedence

Doctrine §9, quoted directly: *"Every architectural fact MUST have exactly one authoritative home among the normative documents... Navigational documents, historical records, and engineering guidance have no authority to establish, alter, or contradict current ontology. Where any document appears to conflict with a normative document, authority is determined by the established normative dependency chain, not by which document is more recent, where a document is located, or the current state of any implementation."*

Applying this directly:

- OE-002 is a normative document with Final status and is the sole authoritative home for the Domain Object Set (its own §2: *"Its content is authoritative for the facts listed in Section 1 and for no others"*; §4: *"No other Domain Object is part of this model"*).
- The Domain Object Implementation Reconciliation Plan **explicitly and correctly disclaims normative authority of its own accord**, in its own §2: *"Engineering planning artifact. Not a normative document; carries no Doctrine status... Where anything here conflicts with the Architecture Doctrine, OE-002 through OE-006, the Historical Decision Record, or a completed Implementation Design, those documents govern and this plan is wrong and must be corrected."* By its own stated terms, this plan cannot be the source that changed the Domain Object Set — and it never claimed to be.
- The five completed Implementation Design documents (Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome) likewise carry no Doctrine status (each states this directly in its own §1/§2, e.g. Decision-Implementation-Design.md's opening line: *"This document is an implementation-design artifact, not a normative document... this is not one"*). None of them purports to amend OE-002 §4, and none discusses Case as a Domain Object type at all.
- The reconciliation-plan task brief and the DO-IMP-002 task brief are **task-execution instructions**, not documents at all in the Doctrine's own sense of "normative document" — they were never published, carry no stable identifier, and were never subjected to the Change Protocol (Doctrine §13). Per Doctrine §9, they have no authority to establish, alter, or contradict current ontology, however explicit or repeated their own six-item list is.
- No document in this repository claims Doctrine-amendment authority for itself except OE-002 through OE-006 and the Doctrine itself.

**Doctrine §13, Change Protocol, quoted directly**: *"Adding, removing, or materially redefining an architectural category MUST follow this sequence: 1. investigation... 2. an architectural decision closing that investigation; 3. amendment of the authoritative upstream normative document; 4. review and, where necessary, amendment of every dependent normative document; 5. creation of a historical decision record; 6. alignment of navigational documentation; 7. repository inspection; 8. migration planning; 9. implementation."* No step of this sequence occurred for a Case-for-Observation substitution: no investigation record exists; no architectural decision closing such an investigation exists; OE-002 §4 itself is textually unchanged (it still reads "Observation" as item 1, and does not mention Case); the Historical Decision Record contains no entry describing removal of Observation or addition of Case (its own "Decision History: OE-002" section names only Evaluation and Learning Event as considered-and-rejected alternatives — never Case, never a proposal to remove Observation).

**Doctrine §12, quoted directly**: *"implementation planning MUST NOT silently introduce new ontology... Where implementation work discovers an apparent expressive gap, that gap MUST be returned to the architectural investigation process described in Sections 4 through 6. It MUST NOT be resolved by introducing an undocumented type, field, event, or rule at the implementation layer."* The reconciliation-plan task brief's and DO-IMP-002 task brief's six-item lists did exactly what this section forbids: they introduced a materially different closed type-set at the planning/implementation layer, without returning to the OE-002 investigation process.

**Conclusion on precedence**: OE-002 §4 has never been amended, superseded, or reviewed for amendment under Doctrine §13. It remains the sole controlling, Final, normative statement of the Domain Object Set. No later source — task brief, reconciliation plan, or implementation — carries authority to change this, regardless of how recently written, how often repeated, or how much implementation now assumes otherwise (Doctrine §12: *"the existence of an implementation MUST NOT be treated as retroactive proof of an ontological claim"*).

## 8. Exact Conflicting Propositions

| # | Proposition | Source | Section | Status |
|---|---|---|---|---|
| 1 | "The Domain Object Set consists of exactly the following six Domain Objects: 1. Observation 2. Knowledge Reference 3. Reasoning Trace 4. Judgment 5. Decision 6. Outcome. No other Domain Object is part of this model." | OE-002 | §4 | Final, normative |
| 2 | "A Case is the normative ownership boundary within which Domain Objects exist and relate to one another... This document defines only the role of Case as the ownership boundary of the Domain Object Model." | OE-002 | §3.1 | Final, normative — defines Case's role, deliberately outside §4's enumerated set |
| 3 | "Observation MAY be referenced by other Domain Objects defined in this document; nothing in Observation's own definition requires this." | OE-002 | §5.1 Relationships | Final, normative |
| 4 | "Knowledge Reference and Reasoning Trace each require at least one reference to another Domain Object and are therefore never roots of this structure; Judgment, Decision, and Outcome each MAY be roots of this structure or MAY reference another Domain Object" | OE-002 | §6 | Final, normative — Observation is the implied root/referenceable node these three MAY instead reference |
| 5 | "The adopted Domain Object set is closed and consists of: Case, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome." | Domain-Object-Implementation-Reconciliation-Plan.md (reflecting its own originating task brief) | §8 (Canonical Target Model table) | Task-local/planning; no Doctrine status; self-disclaims normative authority (§2) |
| 6 | "It must reject non-adopted types, including: ... Observation ... Do not silently include legacy aggregates merely because they exist in code." | DO-IMP-002 task brief (this conversation, not a repository file) | §3 | Task-execution instruction; not a repository document; no Doctrine status |
| 7 | `DomainObjectType` enum admits `CASE` and has no `OBSERVATION` member; a corresponding test asserts `"Observation"` is rejected. | `atlas/core/domain/shared/domain_object_type.py`; `tests/unit/domain/shared/test_domain_object_type.py` | — | Uncommitted, untracked code — implements proposition 6, not proposition 1 |

Propositions 1–4 are mutually consistent, Final, normative, and directly on point. Propositions 5–7 are mutually consistent with each other but directly contradict propositions 1 and 3, and carry no authority capable of overriding them (§7 above).

## 9. Required Conceptual Distinctions

Applying the six distinctions named in the task brief directly to the two concepts at issue:

| | Case | Observation |
|---|---|---|
| **A. Ontological membership** — is it an adopted Domain Object per OE-002 §4? | **No.** OE-002 §3.1 defines it separately from, and prior to, the §4 enumeration; §4 itself does not name it. | **Yes.** Named explicitly as item 1 of exactly six (§4). |
| **B. Ownership role** — is it the ownership boundary for other Domain Objects? | **Yes**, exclusively (§3.1: "the normative ownership boundary within which Domain Objects exist"). | **No.** Observation belongs to a Case like every other Domain Object (§3: "Every Domain Object: belongs to exactly one Case"); it does not itself serve as an ownership boundary for anything. |
| **C. Reference eligibility** — may another Domain Object contain a typed reference to it? | **No**, under current text (Section 11, Section 13 below). | **Yes**, explicitly stated (§5.1 Relationships; §6). |
| **D. Implementation existence** — does code exist? | **Yes** (`atlas/core/domain/case/`, committed in DO-IMP-001). | **Yes** (`atlas/core/domain/observation/`, pre-existing, predates this governance track). |
| **E. Acceptance status** — may instances be admitted/accepted under the current architecture? | Case instances are created via `Case.create()` (DO-IMP-001); OE-002 does not define a Case-specific acceptance/validation contract at all (§3.1 explicitly limits its own scope to the ownership-boundary role), so Case's own creation sits outside the OE-005/OE-006 Valid/Invalid/acceptance model that governs the six Domain Objects specifically. | Governed fully by the general OE-005/OE-006 model, like every other Domain Object; `ObservationAccepted` is one of the six adopted Domain Events (OE-003 §4.1). |
| **F. Closed-set membership** — included in the explicitly closed set? | **No** — excluded from OE-002 §4's own closed enumeration. | **Yes** — one of exactly six named members. |

No inference beyond what is explicitly stated was drawn: Case is not treated as reference-ineligible merely because it is newly implemented, nor is Observation treated as no longer adopted merely because later task briefs omitted it (Doctrine §9's own precedence rule forecloses inferring an ontological change from a planning document's omission).

## 10. Candidate Analysis

**Candidate A — Observation is the reference-eligible target; Case remains the ownership boundary, not a target type.** Directly and fully supported by OE-002 §3.1, §4, §5.1, and §6, with no contradiction found anywhere in OE-003 through OE-006 or any completed Implementation Design. **Selected** (Section 20).

**Candidate B — Case included, Observation excluded, via formal supersession.** Requires an accepted source with formal amendment authority over OE-002 §4. None exists: no OE-002 amendment, no Doctrine-sanctioned architectural decision, no Historical Decision Record entry describing this change (Section 7). **Rejected for lack of authority, not preference** — this is precisely the distinction Doctrine §9 requires: a later, more detailed, more repeated statement is still not a superseding statement absent the Change Protocol's own required steps.

**Candidate C — Both Case and Observation adopted as Domain Objects, but only a specifically governed subset is reference-eligible.** This presupposes Case has been adopted as an OE-002 §4 Domain-Object-Set member in the first place — no accepted source does this (Section 8, Section 9 distinction A). **Rejected**: the premise itself lacks authority, independent of whatever reference-eligibility subset one might then propose.

**Candidate D — Both Case and Observation are reference-eligible (seven types).** Same rejection as Candidate C (Case was never adopted as a Domain Object at all), compounded by the same-Case paradox a Case-as-target would create (Section 14). **Rejected.**

**Candidate E — Domain Object Set and reference-target set are two independently defined closed sets.** Tested directly against OE-002's own text: §3 states "A Domain Object MAY reference another Domain Object only if that other Domain Object belongs to the same Case" — the reference rule is stated generically in terms of "Domain Object," with no separate, independently-scoped "reference-target set" ever defined anywhere in OE-002 through OE-006. INV-001 (OE-004) closes both the Domain Object type set and the Domain Event type set to the same six-and-six correspondence, again with no third, independently-scoped set introduced. **Rejected as a description of the currently adopted architecture** — no source establishes two distinct sets today. (A future, formally adopted amendment *could* choose to split these concepts apart; nothing here forecloses that as a future possibility, but it is not the current state and this document does not manufacture it, per Doctrine §13.)

**Candidate F — Canonical contradiction blocks implementation; no precedence exists.** Tested against Doctrine §9's own explicit precedence rule (normative dependency chain governs, not recency, not implementation state) — precedence is in fact fully decidable here: OE-002 is Final and normative; the conflicting sources are self-declared non-normative or task-local. **Rejected** — this is not a case of two equally-authoritative sources genuinely disagreeing; it is a case of one normative source and several non-normative sources that silently diverged from it without ever claiming amendment authority.

## 11. Case Analysis

Case is not, and has never been, adopted as a member of OE-002 §4's closed Domain Object Set. OE-002 §3.1 defines Case's role with deliberate scope-limiting language: *"This document defines only the role of Case as the ownership boundary of the Domain Object Model. It does not define the complete semantics, lifecycle, or implementation of Case beyond what is required by this model."* This is a considered, textually explicit choice to keep Case's definition narrow and structurally prior to the enumerated set, not an oversight later corrected by omission. DO-IMP-001's own implementation is fully consistent with this narrower role: it built Case solely as an ownership-boundary aggregate (`id`, `recorded_at`) and never asserted, tested, or relied upon Case being reference-eligible (its own `entity.py` docstring: *"Case is foundational... other Domain Objects will depend on Case later, not the reverse"* — a one-directional dependency claim, not a reference-target claim). Case's existence as a committed aggregate is therefore unaffected by, and does not itself argue for, reference-eligibility (Doctrine §12: implementation existence is not retroactive ontological proof).

## 12. Observation Analysis

Observation remains, without qualification, one of OE-002 §4's exactly six adopted Domain Objects. Nothing in OE-002, OE-003, OE-004, OE-005, OE-006, the Historical Decision Record, or any of the five completed Implementation Designs states or implies that Observation's status changed. The Historical Decision Record's own "Decision History: OE-002" section names the only two candidates ever considered-and-rejected relative to the adopted six: Evaluation and Learning Event, both "found reducible to Judgment." Observation is not mentioned in that rejected-candidates list — it is, and has only ever been, an adopted member. Observation's existing implementation (`atlas/core/domain/observation/`) is untouched by DO-IMP-001 or DO-IMP-002 and remains fully valid; the only inconsistency is that the currently uncommitted `DomainObjectType` enum fails to admit it as a reference target, which is an implementation gap relative to OE-002 §5.1's explicit reference-eligibility statement, not a fact about Observation's own status.

## 13. Reference-Eligibility Analysis

Per OE-002 §3: *"A Domain Object MAY reference another Domain Object only if that other Domain Object belongs to the same Case."* Reference eligibility, as OE-002 states it, is a property of being "a Domain Object" — i.e., of falling within the closed six-type set INV-001 (OE-004) enforces. Since Case is not one of the six, it is not, under the current text, eligible to be a reference target: not by an arbitrary policy choice, but because the reference rule's own scope ("another Domain Object") categorically excludes it. Observation, being explicitly one of the six and explicitly named as referenceable (§5.1, §6), is eligible without qualification. This directly answers Section 3's Question 5: under the architecture as it stands today, the Domain Object Set and the valid reference-target set are the same set — OE-002 supplies no independent definition of the latter that could diverge from the former.

## 14. Same-Case Consequences

Forcing Case into the reference-target set would create a structural paradox the task brief itself anticipated (Section 7 of the task): INV-004 (OE-004) requires *"Every semantic reference from one Domain Object to another MUST connect Domain Objects belonging to the same Case."* Applying this to a Case-as-target would require asking whether the target Case "belongs to the same Case" as the referencing object — but Case is the ownership boundary itself, not a thing that belongs to a Case (OE-002 §3: "Every Domain Object... belongs to exactly one Case" is a statement about Domain Objects, and Case, per Section 11, is not one). There is no adopted concept of nested or self-referential Case containment anywhere in this repository. Admitting Case as a target would therefore require either inventing such a concept (forbidden by Doctrine §12 at the implementation-planning layer) or applying INV-004 in an undefined, ad hoc way — precisely what the task brief instructed this investigation not to do. This is an independent, positive architectural argument against Candidates B/D, not merely an absence of textual support.

## 15. Impact on Existing Architecture

No existing normative document (OE-002 through OE-006) requires any change. No completed Implementation Design (Knowledge Reference — absent as a document; Reasoning Trace; Judgment; Decision; Outcome) requires any change: none of them discusses Case as a candidate reference target, and each already correctly treats its own committed-to-matter/subject/support reference as targeting "any of the six adopted types" in the sense OE-002 §4 actually defines (Observation included). No invariant (OE-004) requires any change. Existing Observation implementation code requires no change — it was never touched by this discrepancy.

## 16. Impact on DO-IMP-001

**None.** DO-IMP-001's Case aggregate (`atlas/core/domain/case/`, committed at `f8048a7a112d7846185736482309376b7eb01144`) implements only Case's ownership-boundary role and never asserted or depended on Case being reference-eligible. It remains fully valid and requires no correction, no re-opening, and no re-commit under any candidate examined here, including the selected Candidate A.

## 17. Impact on Uncommitted DO-IMP-002

**Classification: structurally correct but requiring enum-value correction** (per the task's own Section 8 classification options). The architecture of the package — a closed `(str, Enum)` `DomainObjectType`, an immutable, hashable `TypedDomainObjectReference` value object carrying only `target_type`/`target_id`, a `parse()` classmethod raising a dedicated exception for unrecognized values, strict domain-layer construction with no implicit coercion, a `uuid.UUID`-only `target_id` with no shared identifier-wrapper class, dependency-direction discipline (no import of any concrete aggregate or infrastructure technology), and a thin `CamelModel`-based API schema wrapper — is sound and requires no redesign. The defect is narrow and confined to the enum's own six literal values and their corresponding tests:

- `DomainObjectType` must admit `OBSERVATION = "Observation"` and must not admit `CASE`.
- `tests/unit/domain/shared/test_domain_object_type.py`'s `_ADOPTED` mapping and `_REJECTED_LEGACY_OR_NON_ADOPTED` list must be swapped accordingly (Observation moves from rejected to adopted; Case moves from adopted to rejected).
- The module's own disclosed-discrepancy docstring in `domain_object_type.py` must be updated to state the resolution reached here (citing this document) rather than continuing to describe the substitution as an unresolved, task-confirmed choice.
- No other file requires structural change; `typed_reference.py`, `exceptions.py`, and `typed_reference_schemas.py` reference `DomainObjectType` only generically and require no edits beyond what naturally follows from the enum's own corrected values.

This correction is **not performed by this document**, per its own explicit restriction against modifying the current DO-IMP-002 files during this investigation.

## 18. Required Corrections to the Reconciliation Plan

The Domain-Object-Implementation-Reconciliation-Plan.md requires a correction to its own §8 "Canonical Target Model" table (currently lists the closed set as "Case, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome"; should read "Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome," with Case's ownership-boundary role stated separately, as OE-002 §3.1 itself does) and to every reconciliation-register item (DO-REC-*) that inherited this same six-item framing. This correction is **not performed by this document**, per its own scope restriction against modifying any file other than itself.

## 19. Open Questions

**Q1 — Should a future, formally adopted amendment introduce Case-referencing as a genuinely new capability (Candidate E's split-set model)?** No canonical source currently requires this, and no demonstrated expressive gap has been identified (Doctrine §8's forcing-function test is not met: no downstream normative task has yet exposed a real need to reference a Case from another Domain Object). Not resolved here; would require its own investigation under Doctrine §§4–6 if a genuine need ever arises.

**Q2 — How did the Case-for-Observation substitution originate?** Not authoritatively determinable from the repository alone; plausibly, later task briefs were framing "the six types requiring engineering attention in this convergence phase" and inadvertently conflated that framing with OE-002 §4's own closed set, substituting the newly salient Case (just then being built) for the already-implemented, seemingly "done" Observation. This is offered only as a disclosed hypothesis about provenance, not as a finding with evidentiary weight, and does not affect the conclusion in Section 20.

**Q3 — Does Observation's practical absence from the Engineering Convergence series (no DO-REC/DO-IMP item currently addresses it) require its own reconciliation item?** Yes, plausibly — the Reconciliation Register (Section 18) will need a corrected item once its own §8 table is fixed, since Observation, being genuinely reference-eligible, may need the same generic-reference-role verification the five other reference-bearing types received. Not resolved here.

## 20. Decision or Blocking Finding

**Outcome 1 — OE-002 remains controlling.** Observation is included in, and Case is excluded from, the closed Domain Object Set and the (currently identical) valid reference-target set, because no accepted source has established a separate reference-target rule and no accepted source has amended OE-002 §4 under Doctrine §13's Change Protocol.

## 21. Recommended Next Action

Correct `atlas/core/domain/shared/domain_object_type.py` (and its corresponding tests and docstring) to admit `Observation` and exclude `Case`, as a narrowly-scoped, disclosed fix to the still-uncommitted DO-IMP-002 package — not as a new architectural decision, since none is being made here, only an existing one (OE-002 §4) being correctly applied. Separately, correct the Domain Object Implementation Reconciliation Plan's §8 table and affected DO-REC items to match. Both corrections are recommended as immediate follow-up work, not performed by this investigation itself.

## 22. Final Conclusion

The discrepancy is real, and it resolves cleanly in OE-002's favor: Observation is, and has remained throughout, one of OE-002 §4's six adopted, reference-eligible Domain Objects; Case is, and has remained throughout, the ownership boundary defined separately in OE-002 §3.1, outside that enumerated set and not reference-eligible under the architecture as currently adopted. The later task briefs' and reconciliation plan's substitution of Case for Observation carries no formal architectural authority — it was assumed, not decided, and Doctrine §9's own precedence rule resolves the conflict without requiring any new amendment. DO-IMP-001 is unaffected. DO-IMP-002 requires a narrow, mechanical enum-value correction, not a redesign, before it may be committed.

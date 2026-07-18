# OE-004 — Domain Invariants

**Status:** Final.

## 1. Purpose and Scope

This document is the authoritative normative definition of the Domain Invariants for Atlas Core's architecture. It states:

- the complete normative set of Domain Invariants;
- the precise meaning of each invariant;
- the architectural state each invariant constrains;
- whether each invariant applies to Domain Objects, Domain Events, semantic relationships, Case ownership, acceptance ordering, or historical permanence;
- consequences directly implied by preservation or violation of an invariant.

This document does not define Domain Objects, Domain Events, validation procedures, validation levels, or any implementation, persistence, transport, or engineering mechanism. This document is governed by, and MUST be read together with, the Architecture Doctrine, OE-002 — Domain Object Model, and OE-003 — Domain Event Model. It does not restate the content of any of these three documents beyond what is necessary to state an invariant precisely.

## 2. Normative Status

This document is normative only for the facts listed in Section 1. It has no authority over the Domain Object Set, Domain Object definitions, the Domain Event set, or any Domain Event definition.

This document depends on the Architecture Doctrine for its investigation, decision, publication, amendment, removal, and reopening procedures; on OE-002 for the Domain Object Set and structural rules governing Domain Objects; and on OE-003 for the Domain Event set and structural rules governing Domain Events. This document MUST NOT redefine any fact stated in any of the three upstream documents.

## 3. Definition of a Domain Invariant

A Domain Invariant is a condition that MUST hold in every valid architectural state.

An invariant applies to accepted architectural state — the state constituted by the Domain Objects and Domain Events that have already occurred. An invariant is not itself an event and is not itself a procedure; it does not act, occur, or execute. An invariant is not temporarily violable within the normative model: there is no valid state in which an invariant is suspended, deferred, or partially satisfied.

Determining, procedurally, whether a given state satisfies an invariant is a validation concern and belongs to OE-005, not to this document. This document states only what MUST be true; it does not state how that truth is checked.

An invariant MAY constrain a single Domain Object, a single Domain Event, or a relationship among several Domain Objects, Domain Events, or Cases.

## 4. Complete Adopted Invariant Set

The invariant set consists of exactly the following fifteen invariants. No other invariant is part of this model.

### INV-001 — Closed Architectural Type Sets

**Statement.** Every accepted Domain Object MUST be an instance of exactly one of the six Domain Object types adopted in OE-002. Every Domain Event MUST be an instance of exactly one of the six Domain Event types adopted in OE-003.

**Elements constrained.** Domain Objects; Domain Events.

**Source.** OE-002, Sections 2 and 4; OE-003, Sections 4 and 5.

**Does not require.** Any ordering, preference, or frequency among the adopted Domain Object or Domain Event types.

### INV-002 — Single Case Ownership

**Statement.** Every Domain Object MUST belong to exactly one Case.

**Elements constrained.** Domain Objects; Case ownership.

**Source.** OE-002, Section 3.

**Does not require.** Any definition of what a Case is beyond its role as ownership boundary, which is stated in OE-002 alone.

### INV-003 — Event-Object Case Correspondence

**Statement.** Every Domain Event MUST belong to the same Case as the Domain Object it concerns.

**Elements constrained.** Domain Events; Case ownership.

**Source.** OE-003, Section 3.

**Does not require.** Any Domain Event to exist independent of a Case.

### INV-004 — Same-Case Reference

**Statement.** Every semantic reference from one Domain Object to another MUST connect Domain Objects belonging to the same Case.

**Elements constrained.** Semantic relationships.

**Source.** OE-002, Section 3.

**Does not require.** Any particular Domain Object to reference another; reference is optional except where INV-013 or INV-014 applies.

### INV-005 — Prior Acceptance of Referenced Targets

**Statement.** A Domain Object MUST NOT reference another Domain Object that has not already been accepted.

**Elements constrained.** Semantic relationships; acceptance ordering.

**Source.** OE-002, Sections 3 and 6; OE-003, Section 7.

**Does not require.** Any specific Domain Object type as the target; the target's type is unconstrained by this invariant.

### INV-006 — Distinct Identity

**Statement.** Two distinct Domain Objects MUST NOT share the same identity.

**Elements constrained.** Domain Objects.

**Source.** OE-002, Section 3.

**Does not require.** Any specific identity mechanism or criterion beyond distinctness; OE-002 does not establish one, and this invariant does not introduce one.

### INV-007 — Exactly One Acceptance Event Per Object

**Statement.** Every accepted Domain Object MUST correspond to exactly one Domain Event of the event type assigned to its Domain Object type by OE-003. Every Domain Event MUST correspond to exactly one accepted Domain Object of its assigned Domain Object type.

**Elements constrained.** Domain Objects; Domain Events.

**Source.** OE-003, Sections 3 and 5.

**Does not require.** Any implementation identifier, event payload, or storage representation.

### INV-008 — Atomic Acceptance and Event Occurrence

**Statement.** A Domain Object's acceptance and the occurrence of its corresponding Domain Event MUST be the same architectural moment. There MUST be no intermediate normative state between non-acceptance and acceptance.

**Elements constrained.** Domain Objects; Domain Events; acceptance.

**Source.** OE-003, Sections 3 and 6.

**Does not require.** Any implementation transaction, execution sequence, processing duration, or mechanism by which acceptance is determined.

### INV-009 — Permanence of Domain Objects

**Statement.** An accepted Domain Object MUST NOT be mutated.

**Elements constrained.** Domain Objects.

**Source.** OE-002, Section 3.

**Does not require.** That a Domain Object remain practically relevant; only that it remain unaltered as a historical record.

### INV-010 — Permanence of Domain Events

**Statement.** A Domain Event MUST NOT be mutated.

**Elements constrained.** Domain Events.

**Source.** OE-003, Sections 3 and 6.

**Does not require.** Any statement about how a Domain Event is stored or retained; that is an implementation concern.

### INV-011 — Non-Erasure Under Supersession

**Statement.** A later Domain Object MAY supersede or reinterpret an earlier Domain Object but MUST NOT erase or overwrite it. No Domain Event exists whose function is to delete, revise, or retract a Domain Object or another Domain Event.

**Elements constrained.** Domain Objects; Domain Events; historical permanence.

**Source.** OE-002, Section 3; OE-003, Section 8.

**Does not require.** That supersession or reinterpretation be represented by any Domain Event beyond the later Domain Object's own ordinary acceptance event.

### INV-012 — Root Eligibility Boundaries

**Statement.** Observation MAY be the first accepted Domain Object in a Case. Knowledge Reference and Reasoning Trace MUST NOT be the first accepted Domain Object in a Case. Judgment, Decision, and Outcome MAY be the first accepted Domain Object in a Case only when their respective subject, committed-to matter, or realized matter is internal content rather than a reference.

**Elements constrained.** Domain Objects; acceptance ordering.

**Source.** OE-002, Sections 5 and 6; OE-003, Section 7.

**Does not require.** Any Domain Object type to be first, any mandatory starting object, or any universal workflow sequence.

### INV-013 — Reasoning Trace Minimum Support

**Statement.** A Reasoning Trace MUST be accepted with at least one supporting Domain Object already accepted in the same Case.

**Elements constrained.** Domain Objects; semantic relationships.

**Source.** OE-002, Section 5.3; OE-003, Section 4.3.

**Does not require.** Any specific Domain Object type as a supporter, any upper bound on the number of supporters, or any resolution of how a supported claim, if separately represented, is itself constrained.

### INV-014 — Knowledge Reference Single Target

**Statement.** A Knowledge Reference MUST identify exactly one other Domain Object already accepted in the same Case.

**Elements constrained.** Domain Objects; semantic relationships.

**Source.** OE-002, Section 5.2; OE-003, Section 4.2.

**Does not require.** Any specific Domain Object type as the identified target.

### INV-015 — Acceptance Time as Event Time

**Statement.** A Domain Event's time MUST always be understood as the acceptance time of the Domain Object it concerns. It MUST NOT be replaced by, or conflated with, any time represented by that Domain Object's own content.

**Elements constrained.** Domain Events; acceptance ordering.

**Source.** OE-003, Section 9.

**Does not require.** That represented time, where an object's content concerns it, coincide with, precede, or follow acceptance time in any particular way beyond what OE-002 and OE-003 already permit for Outcome.

## 5. Case Ownership Invariants

INV-002, INV-003, and INV-004 together state everything this document establishes about Case ownership: exactly one Case per Domain Object, matching Case ownership between a Domain Event and the Domain Object it concerns, and same-Case scope for every semantic reference. This document does not define Case lifecycle, Case creation, or any Case semantics beyond its role as ownership boundary, which remains solely defined in OE-002.

## 6. Identity and Uniqueness Invariants

INV-006 and INV-007 together state everything this document establishes about identity and uniqueness: two distinct Domain Objects MUST NOT share identity, and every accepted Domain Object corresponds to exactly one Domain Event of the event type OE-003 assigns to its Domain Object type, with no Domain Event corresponding to more than one Domain Object of any type. This document does not introduce any implementation-level identifier scheme, event payload, or storage representation; identity and correspondence here are architectural, not technical, concepts.

## 7. Acceptance and Existence Invariants

INV-007 and INV-008 together state everything this document establishes about acceptance and existence: every accepted Domain Object corresponds, in both directions, to exactly one Domain Event matching its OE-003-assigned type; a Domain Object's acceptance and its corresponding Domain Event's occurrence are the same architectural moment; and no intermediate normative state exists between non-acceptance and acceptance. This document does not describe how acceptance is determined; that is a validation concern belonging to OE-005.

## 8. Reference Integrity Invariants

INV-004, INV-005, INV-013, and INV-014 together state everything this document establishes about reference integrity: references are same-Case only, a referenced target MUST already be accepted, Knowledge Reference requires exactly one identified target, and Reasoning Trace requires at least one supporting Domain Object. Where Judgment, Decision, or Outcome use a referential form, INV-004 and INV-005 apply to that reference in the same manner; this document does not settle, and does not need to settle, OE-002's open question as to whether the internal or referential form is used in a given instance.

## 9. Root Eligibility Invariants

INV-012 states everything this document establishes about root eligibility: Observation MAY be the first accepted Domain Object in a Case; Knowledge Reference and Reasoning Trace MUST NOT be the first accepted Domain Object in a Case; Judgment, Decision, and Outcome MAY be the first accepted Domain Object in a Case only when using internal content. No invariant in this document establishes a mandatory first Domain Object or a required starting point for any Case.

## 10. Permanence and Immutability Invariants

INV-009, INV-010, and INV-011 together state everything this document establishes about permanence: accepted Domain Objects and Domain Events MUST NOT be mutated, a later Domain Object MAY supersede or reinterpret an earlier one without erasing or overwriting it, and no deletion event exists for any Domain Object or Domain Event. This document does not define storage retention, archival policy, or physical deletion mechanics; those are implementation concerns.

## 11. Event-Time Invariants

INV-015 states everything this document establishes about event time: a Domain Event's time is always its Domain Object's acceptance time, never the time represented by that object's own content. Retrospective content, as OE-002 permits for Outcome, does not backdate the acceptance event; the event's time remains the time of acceptance regardless of what the object's content states about represented time. Event ordering, per INV-005, follows reference dependency among Domain Objects, not represented chronology.

## 12. Absence of Global Workflow Invariant

No invariant in this document imposes a universal sequence among the six Domain Object types, such as Observation → Knowledge Reference → Reasoning Trace → Judgment → Decision → Outcome. No such sequence is part of this model. Where such a sequence appears in usage, it reflects common practice, not an architectural requirement stated by this document or by any upstream document.

## 13. Invariant Interaction and Consistency

Every invariant in Section 4 MUST hold simultaneously in every valid architectural state. Satisfying one invariant does not waive, relax, or substitute for another.

The fifteen invariants constrain distinct architectural dimensions — architectural type-set closure, Case ownership, reference integrity, identity, acceptance, permanence, root eligibility, and event time — and none contradicts another. This document does not define a precedence order among invariants, because no genuine contradiction exists that would require one.

## 14. Violation Semantics

An architectural state that fails to satisfy any invariant in Section 4 is not a valid state under this normative model.

This document does not define error handling, recovery procedures, severity levels, validation result structures, rejection workflows, or repair procedures. Those belong to OE-005 or to implementation, and are excluded under Section 15.

## 15. Explicit Exclusions

This document does not define:

- validation procedures or levels;
- error handling or recovery;
- severity classification;
- validation result or violation structures;
- rejection workflows;
- repair procedures;
- implementation mechanics of any kind;
- persistence or storage mechanisms;
- event transport or messaging infrastructure;
- API definitions;
- database schema;
- serialization formats;
- migration procedures;
- engineering guidance.

Any of the above, where relevant, is defined in a separate, dependent normative document.

## 16. Dependency and Authority

The normative dependency chain governing this document is:

```
Architecture Doctrine
   →  OE-002 — Domain Object Model
   →  OE-003 — Domain Event Model
   →  OE-004 — Domain Invariants
```

This document MUST NOT redefine any fact whose authoritative home is OE-002 or OE-003, including the Domain Object Set, any object's definition, the Domain Event set, any event's definition, or any relationship, ownership boundary, or ordering fact already stated by either document. This document MUST NOT redefine any fact whose authoritative home is the Architecture Doctrine.

## 17. Open Questions

This document retains no open question.

OE-002's unresolved questions do not create an unresolved invariant distinction in this document. INV-004 and INV-005 apply whenever a permitted referential form is used. INV-012 states the root-eligibility consequence conditionally for the internal and referential forms already permitted by OE-002, without deciding whether those forms may coexist within one undifferentiated instance. INV-013 does not resolve how a Reasoning Trace's supported claim is represented. No invariant in this document requires those upstream questions to be resolved.

## 18. Definition of Done for OE-004

This document satisfies the Architecture Doctrine's definition of a normative publication when:

- its content is consistent with the Architecture Doctrine, OE-002, and OE-003, its upstream documents;
- every fact it states has exactly one authoritative home within this document, per the Doctrine's single-source-of-truth principle;
- its status is explicitly stated;
- no open question is retained, per Section 17;
- a historical decision record exists for the decision the publication enacts, or the publication is explicitly part of an incomplete change package that MUST NOT be considered closed until that record exists.

This document's completion does not require the existence of validation rules, validation levels, or any implementation.

---

## Self-Audit

- **No Domain Object or Domain Event added or redefined.** This document names only the six Domain Objects and six Domain Events already adopted in OE-002 and OE-003, and states no new fact about their definitions — only the conditions that MUST hold across them.
- **The invariant set is complete and minimal, with count unchanged at fifteen.** Each invariant is derived directly from an already-adopted OE-002 or OE-003 fact and cited to its source; no invariant was introduced merely because an implementation could enforce it, and no universal invariant was stated where the upstream model permits multiple valid forms (see INV-012's explicit conditional framing).
- **INV-001 covers both closed type sets.** The closed Domain Object set and the closed Domain Event set share one invariant home, citing both OE-002 and OE-003.
- **INV-006 modal wording corrected.** Reads "Two distinct Domain Objects MUST NOT share the same identity," stating the prohibition directly.
- **INV-007 completed and implementation-neutral.** States that correspondence matches each Domain Object's type to its OE-003-assigned event type in both directions, with its "Does not require" field excluding implementation identifiers, event payloads, and storage representation.
- **INV-008 now covers both same-moment occurrence and atomicity.** The fact that a Domain Object's acceptance and its corresponding Domain Event's occurrence are the same architectural moment now shares one invariant home with the absence of any intermediate normative state; both facts are stated in INV-008's own text, and Section 7 has been updated to attribute both explicitly to INV-008 rather than leaving the same-moment fact as unattributed narrative.
- **INV-012 duplication removed.** States root eligibility purely in terms of first-in-Case status, with no restatement of Reasoning Trace's minimum-support or Knowledge Reference's single-target facts; those remain exclusively stated in INV-013 and INV-014.
- **Section 17 addresses each affected invariant individually.** INV-004, INV-005, INV-012, and INV-013 are each stated to hold without resolving OE-002's open questions.
- **No validation procedure introduced.** Section 3 explicitly excludes procedural determination of invariant satisfaction from this document's scope; Section 14 states only the architectural meaning of violation; Section 15 excludes all validation content explicitly.
- **Upstream open questions were not silently resolved.** Section 8, INV-012, and Section 17 each explicitly preserve OE-002's unresolved internal-versus-referential form questions without assuming a resolution.
- **No global workflow imposed.** Section 12 explicitly states that no invariant establishes a sequence among the six Domain Object types.
- **Architecture and implementation remain separated.** No invariant references storage, persistence, identifiers, schema, transport, or any implementation mechanic; INV-008's "Does not require" field explicitly excludes transaction, execution-sequence, and processing-duration concepts.
- **Doctrine, OE-002, and OE-003 authority preserved.** Section 16 states the full dependency chain and explicitly prohibits redefinition of any upstream fact.

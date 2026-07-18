# OE-002 — Domain Object Model

**Status:** Final.

## 1. Purpose and Scope

This document is the authoritative normative definition of the Domain Object Model for Atlas Core's architecture. It states:

- the normative Domain Object Set;
- the definition of each retained Domain Object;
- each object's identity;
- each object's responsibility;
- the relationships that may exist between Domain Objects;
- ownership boundaries;
- architectural consequences directly implied by the object model.

This document is governed by, and MUST be read together with, the published Architecture Doctrine. It does not restate the Doctrine's content.

## 2. Normative Status

This document is normative. Its content is authoritative for the facts listed in Section 1 and for no others.

The Domain Object Set stated in Section 4 is closed. No Domain Object beyond those listed exists under this model. A Domain Object MAY be added, removed, or materially redefined only through the change protocol defined by the Architecture Doctrine.

## 3. Definition of the Domain Object Model

A Domain Object is a permanent element of Atlas Core's architecture. Every Domain Object:

- belongs to exactly one Case;
- has stable identity, independent of its content;
- MAY participate in explicit semantic relationships with other Domain Objects;
- MAY be referenced by Domain Events;
- is governed by Domain Invariants;
- does not execute behaviour.

A Domain Object, once accepted, is permanent. It MUST NOT be mutated. A later Domain Object MAY supersede or reinterpret an earlier one; it MUST NOT erase or overwrite it.

A Domain Object MAY reference another Domain Object only if that other Domain Object belongs to the same Case. A reference from one Domain Object to another is a semantic relationship, distinct from Case membership: Case membership establishes ownership; a semantic relationship expresses that one object depends upon, characterizes, or points to another.

Some Domain Objects defined in this document permit two structurally different forms: content held internally by the object itself, or a reference to another same-Case Domain Object. Where both forms are independently valid for a given object, this document states so explicitly and does not assert that the two forms may be combined within a single, undifferentiated instance of that object unless stated. Where this remains unresolved, it is stated as an open question under Section 7 of the Architecture Doctrine, not as a defect in this document's completeness.

No Domain Object defined in this document requires an Agent, requires multiple alternatives, asserts objective or externally verified truth, or asserts causal attribution, except where explicitly stated otherwise below.

### 3.1 Case

A Case is the normative ownership boundary within which Domain Objects exist and relate to one another.

Every Domain Object belongs to exactly one Case.

This document defines only the role of Case as the ownership boundary of the Domain Object Model. It does not define the complete semantics, lifecycle, or implementation of Case beyond what is required by this model.

## 4. The Complete Adopted Domain Object Set

The Domain Object Set consists of exactly the following six Domain Objects:

1. Observation
2. Knowledge Reference
3. Reasoning Trace
4. Judgment
5. Decision
6. Outcome

No other Domain Object is part of this model.

## 5. Domain Object Definitions

### 5.1 Observation

**Definition.** Observation is a permanent Domain Object that preserves informational content without asserting that the content is true.

**Identity.** Observation has stable identity independent of its content. Its identity does not depend on any indication of origin.

**Responsibility.** Observation is responsible for preserving informational content as it stands, without commitment to its truth, verification, reliability, or authority.

**Ownership boundary.** Observation is origin-neutral: its own definition neither requires nor prohibits any particular origin for its content. Where an indication of origin is present, it is optional, non-defining content, not part of what makes an Observation valid.

**Relationships.** Observation requires no other Domain Object to exist validly. Observation is root-eligible: it MAY be the first Domain Object accepted into a Case. Observation MAY be referenced by other Domain Objects defined in this document; nothing in Observation's own definition requires this.

### 5.2 Knowledge Reference

**Definition.** Knowledge Reference is a permanent Domain Object that identifies another permanent Domain Object within the same Case, which the Case treats as knowledge for its own purposes, without asserting that the referenced content is true, verified, reliable, or externally authoritative.

**Identity.** Knowledge Reference has stable identity independent of its content and independent of the identity of the Domain Object it references.

**Responsibility.** Knowledge Reference is responsible for recording that the Case relies upon another Domain Object's content as knowledge, without itself vouching for that content's accuracy or standing.

**Ownership boundary.** Knowledge Reference's target MUST belong to the same Case and MUST already exist as an accepted Domain Object. Knowledge Reference is not root-eligible.

**Relationships.** Knowledge Reference MAY reference any other Domain Object defined in this document that belongs to the same Case. No specific Domain Object type is required as its target; the target's type is unrestricted by this document.

### 5.3 Reasoning Trace

**Definition.** Reasoning Trace is a permanent Domain Object that represents one or more already-accepted Domain Objects as providing epistemic support.

**Identity.** Reasoning Trace has stable identity independent of its content and independent of the identity of the Domain Objects it represents as supporting.

**Responsibility.** Reasoning Trace is responsible for recording that specified, already-accepted Domain Objects stand in a support relationship, without itself asserting a stepwise process, chronology, or narrative rationale.

**Ownership boundary.** Every supporting Domain Object MUST belong to the same Case as the Reasoning Trace and MUST already exist as an accepted Domain Object. Reasoning Trace requires at least one supporting Domain Object. Reasoning Trace is not root-eligible.

**Relationships.** Reasoning Trace MAY be supported by one or more other Domain Objects defined in this document, drawn from the same Case. Whether Reasoning Trace additionally contains, or instead references, a distinct supported claim is not settled by this document; where a supported claim is represented as a reference, it MUST be to another same-Case Domain Object. Additional constraints on which Domain Objects MAY occupy the supporting role are governed by Domain Invariants and are not stated in this document.

### 5.4 Judgment

**Definition.** Judgment is a permanent Domain Object that records the Case's settled, Case-relative characterization of an identified subject, without asserting that the characterization is objectively true.

**Identity.** Judgment has stable identity independent of its content and independent of the identity of any subject it references.

**Responsibility.** Judgment is responsible for recording a settled assessment, status, or position that the Case holds regarding its subject. Judgment does not require multiple alternatives, does not assign a mandatory discrete status vocabulary, and does not require prior epistemic support from a Reasoning Trace.

**Ownership boundary.** Judgment's subject MAY be content held internally by the Judgment itself, or a reference to another Domain Object belonging to the same Case. Both forms are independently valid. This document does not establish that both forms may coexist within one undifferentiated Judgment; this is an open question under Section 7 of the Architecture Doctrine. Judgment's root-eligibility depends on which form a given instance uses: an instance whose subject is internal content MAY be the first Domain Object accepted into a Case; an instance whose subject references another Domain Object is not root-eligible.

**Relationships.** Where Judgment's subject is a reference, it MUST be to another same-Case Domain Object; no specific Domain Object type is required. Judgment does not require a Reasoning Trace, a Decision, an Observation, or a Knowledge Reference. Judgment MAY be referenced by other Domain Objects defined in this document; nothing in Judgment's own definition requires this.

### 5.5 Decision

**Definition.** Decision is a permanent Domain Object that records the Case's settled practical commitment regarding what is to be done, without itself executing behaviour.

**Identity.** Decision has stable identity independent of its content and independent of the identity of any object it references.

**Responsibility.** Decision is responsible for recording that the Case has settled on a determinate practical commitment. Decision does not require multiple alternatives, does not require an Agent, and does not itself constitute or perform execution of any kind.

**Ownership boundary.** Decision's committed-to matter MAY be content held internally by the Decision itself, or a reference to another Domain Object belonging to the same Case. Both forms are independently valid. This document does not establish that both forms may coexist within one undifferentiated Decision; this is an open question under Section 7 of the Architecture Doctrine. Decision's root-eligibility depends on which form a given instance uses, following the same pattern as Judgment.

**Relationships.** Where Decision's committed-to matter is a reference, it MUST be to another same-Case Domain Object. No specific Domain Object type is required; a Judgment, a Reasoning Trace, or an Outcome MAY each serve as this reference, but none is required. Decision does not require a prior Judgment, Reasoning Trace, or Outcome. Decision remains a valid record regardless of whether it is later executed, remains executable, produces a recorded Outcome, or is superseded by a later Decision.

### 5.6 Outcome

**Definition.** Outcome is a permanent Domain Object that records a determinate state of affairs which the Case treats as having become actual, without asserting objective truth or attributing that realization to a specific cause.

**Identity.** Outcome has stable identity independent of its content and independent of the identity of any object it references.

**Responsibility.** Outcome is responsible for recording that a state of affairs is treated as realized, as distinct from intended, possible, or proposed matter. Outcome does not assert causality, success, failure, or measurement.

**Ownership boundary.** Outcome's realized matter MAY be content held internally by the Outcome itself, or a reference to another Domain Object belonging to the same Case. Both forms are independently valid. This document does not establish that both forms may coexist within one undifferentiated Outcome; this is an open question under Section 7 of the Architecture Doctrine. Outcome's root-eligibility depends on which form a given instance uses, following the same pattern as Judgment and Decision.

**Relationships.** Where Outcome's realized matter is a reference, it MUST be to another same-Case Domain Object. No specific Domain Object type is required. Outcome does not require a Decision, a Judgment, or a Reasoning Trace. Outcome MAY be referenced by a Decision or by a Reasoning Trace as one permissible target among others; this document does not establish Outcome as the required or exclusively endorsed target of either. Outcome may be recorded retrospectively: the time at which the realized matter is treated as having become actual need not equal the time of Outcome's own acceptance. A later Outcome does not erase or invalidate an earlier one.

## 6. Overall Relationship Topology

Ownership among Domain Objects is established solely by Case membership: every Domain Object belongs to exactly one Case, and this membership is independent of any semantic relationship.

Semantic relationships between Domain Objects form a structure separate from Case ownership. This document establishes the following about that structure:

- every semantic relationship MUST connect Domain Objects belonging to the same Case;
- a Domain Object MAY only reference another Domain Object that already exists as accepted;
- Observation requires no relationship to any other Domain Object and MAY be a root of this structure;
- Knowledge Reference and Reasoning Trace each require at least one reference to another Domain Object and are therefore never roots of this structure;
- Judgment, Decision, and Outcome each MAY be roots of this structure or MAY reference another Domain Object, depending on which internally valid form a given instance uses.

This document does NOT establish a mandatory sequence, chain, or required ordering among the six Domain Objects. No Domain Object defined in this document requires any other specific Domain Object type as a precondition of its own validity, except where explicitly stated in Section 5. Any apparent workflow association between Domain Objects reflects common usage, not an architectural requirement of this model.

## 7. Architectural Consequences

The following consequences follow directly from the model stated above:

- root-eligibility is not a uniform property of the Domain Object Set; it varies by object and, for three objects, by which internally valid form a given instance uses;
- a Domain Object that references another Domain Object depends on that target already having been accepted within the same Case;
- every Domain Object, once accepted, is a permanent historical record; later Domain Objects MAY supersede its practical relevance but MUST NOT alter or erase it;
- no Domain Object's validity depends on any subsequent Domain Object being created, executed, or evaluated;
- the unresolved internal-versus-referenced form of Judgment, Decision, and Outcome does not prevent any of the three from being normatively adopted, since each object's minimum semantic contract is fully stated independent of that resolution.

## 8. Explicit Exclusions

This document does not define:

- Domain Events, including which events exist or how they relate to Domain Objects;
- Domain Invariants, including any rule constraining which Domain Objects may occupy a given relational role beyond what is stated in Section 5;
- validation rules, levels, or procedures;
- implementation structures of any kind;
- persistence mechanisms;
- API definitions;
- database schema;
- serialization formats;
- engineering guidance.

Any of the above, where relevant, is defined in a separate, dependent normative document.

## 9. Dependency on the Architecture Doctrine

This document is created and MAY be amended only under the method established by the Architecture Doctrine. The Doctrine is the sole authority for the investigation, decision, publication, amendment, removal, and reopening procedures that apply to this document. This document does not restate that method and defers to the Doctrine wherever a procedural question arises.

## 10. Definition of Done for OE-002

This document satisfies the Architecture Doctrine's definition of a normative publication when:

- its content is consistent with the Architecture Doctrine, its sole upstream document;
- every fact it states has exactly one authoritative home within this document, per the Doctrine's single-source-of-truth principle;
- its status is explicitly stated;
- every open question it retains — the internal-versus-referenced form of Judgment, Decision, and Outcome — is stated explicitly and does not block the minimum semantic contract of any object;
- a historical decision record exists for the decision the publication enacts, or the publication is explicitly part of an incomplete change package that MUST NOT be considered closed until that record exists.

This document's completion does not require the resolution of the open questions stated above, nor does it require the existence of Domain Events, Domain Invariants, validation rules, or any implementation.

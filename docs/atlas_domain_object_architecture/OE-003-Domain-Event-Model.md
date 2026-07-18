# OE-003 — Domain Event Model

**Status:** Final.

## 1. Purpose and Scope

This document is the authoritative normative definition of the Domain Event Model for Atlas Core's architecture. It states:

- the normative Domain Event set;
- the meaning of each retained Domain Event;
- which Domain Object each event concerns;
- the architectural fact each event establishes;
- the relationship between Domain Events, Domain Objects, Case ownership, and historical permanence;
- event ordering consequences directly implied by the adopted Domain Object Model.

This document does not define Domain Objects, Domain Invariants, validation rules, or any implementation, persistence, transport, or engineering mechanism. This document is governed by, and MUST be read together with, the Architecture Doctrine and OE-002 — Domain Object Model. It does not restate either document's content.

## 2. Normative Status

This document is normative only for the facts listed in Section 1. It has no authority over the Domain Object Set, Domain Object definitions, or any fact whose authoritative home is OE-002.

This document depends on the Architecture Doctrine for its investigation, decision, publication, amendment, removal, and reopening procedures, and on OE-002 for the Domain Object Set and the structural rules governing Domain Objects. This document MUST NOT redefine any fact stated in either upstream document.

## 3. Definition of a Domain Event

A Domain Event is the architectural representation that a specific Domain Object has been accepted.

A Domain Event records acceptance. It does not record occurrence in the sense of an external, real-world happening, and it does not record a process or transition beyond the single fact that acceptance took place.

A Domain Event has identity only by reference to the specific Domain Object acceptance it represents. A Domain Event MUST NOT be understood as an independent entity with its own content separate from that acceptance.

A Domain Event cannot exist without the Domain Object it concerns. A Domain Event represents that object's acceptance and therefore presupposes that the object exists as accepted; it has no standing prior to, or independent of, that acceptance.

A Domain Event is permanent. Once a Domain Object's acceptance has occurred, the corresponding Domain Event is a stable historical fact. A Domain Event MUST NOT be mutated, for the same reason the Domain Object it concerns MUST NOT be mutated: mutating either would misrepresent what was accepted and when.

A Domain Event belongs to the same Case as the Domain Object it concerns. No Domain Event exists independent of a Case.

The time a Domain Event records — the time of acceptance — is distinct from any time represented by the content of the Domain Object it concerns. Section 9 states this distinction in full.

This document does not define any event-envelope structure, payload, identifier scheme, or transport mechanism. Those are implementation concerns and are excluded under Section 10.

## 4. Complete Adopted Domain Event Set

The Domain Event set consists of exactly the following six Domain Events, corresponding to the six Domain Objects defined in OE-002:

### 4.1 ObservationAccepted

**Object type concerned:** Observation.

**Preconditions implied by OE-002:** none. Observation is root-eligible and requires no other Domain Object.

**Fact established:** that a specific Observation has been accepted as a permanent Domain Object within its Case.

**Not established:** the truth, accuracy, or origin of the preserved content; any relationship to any other Domain Object.

### 4.2 KnowledgeReferenceAccepted

**Object type concerned:** Knowledge Reference.

**Preconditions implied by OE-002:** the Domain Object identified by the Knowledge Reference MUST already be accepted, within the same Case.

**Fact established:** that a specific Knowledge Reference has been accepted, and that the Case now treats the identified Domain Object as knowledge for its own purposes.

**Not established:** the truth, reliability, or authority of the identified Domain Object's content; which Domain Object type was identified.

### 4.3 ReasoningTraceAccepted

**Object type concerned:** Reasoning Trace.

**Preconditions implied by OE-002:** at least one supporting Domain Object MUST already be accepted, within the same Case.

**Fact established:** that a specific Reasoning Trace has been accepted, representing the specified Domain Objects as providing epistemic support.

**Not established:** any stepwise process, chronology, or narrative rationale by which the support was determined; the exact representation of any supported claim, which remains an open matter at the object level under OE-002.

### 4.4 JudgmentAccepted

**Object type concerned:** Judgment.

**Preconditions implied by OE-002:** if Judgment's subject is a reference to another Domain Object, that Domain Object MUST already be accepted, within the same Case; if Judgment's subject is internal content, no such precondition applies.

**Fact established:** that a specific Judgment has been accepted, recording the Case's settled characterization of its subject.

**Not established:** that the characterization is objectively true; anything about which of the two subject-forms was used beyond what OE-002 itself permits.

### 4.5 DecisionAccepted

**Object type concerned:** Decision.

**Preconditions implied by OE-002:** if Decision's committed-to matter is a reference to another Domain Object, that Domain Object MUST already be accepted, within the same Case; if the committed-to matter is internal content, no such precondition applies.

**Fact established:** that a specific Decision has been accepted, recording the Case's settled practical commitment.

**Not established:** that the Decision has been, will be, or can be executed; any consequence of the commitment.

### 4.6 OutcomeAccepted

**Object type concerned:** Outcome.

**Preconditions implied by OE-002:** if Outcome's realized matter is a reference to another Domain Object, that Domain Object MUST already be accepted, within the same Case; if the realized matter is internal content, no such precondition applies.

**Fact established:** that a specific Outcome has been accepted, recording that a state of affairs is treated by the Case as having become actual.

**Not established:** the objective truth of the realized matter; any cause of the realization; that the event's own acceptance time coincides with the time the realized matter is treated as having occurred.

No other Domain Event is part of this model.

## 5. Event-to-Object Correspondence

Each of the six Domain Object types corresponds to exactly one Domain Event type. This correspondence is uniform: no Domain Object type has more than one corresponding event, and no Domain Event type corresponds to more than one Domain Object type.

This correspondence holds regardless of which internally valid form a Judgment, Decision, or Outcome instance uses for its subject, committed-to matter, or realized matter, respectively, and regardless of how Reasoning Trace's supported claim is eventually represented. A Domain Object's acceptance corresponds to exactly one event whether its content is internal or a reference; this document does not introduce a distinct event for either form.

No asymmetry exists in this model beyond the differing preconditions stated in Section 4, which follow directly from each object's own definition in OE-002.

## 6. Acceptance and Permanence

Event occurrence and Domain Object acceptance are the same architectural moment. A Domain Event does not follow acceptance as a separate, later step; it is the representation that acceptance occurred.

From this model's perspective, acceptance is atomic: there is no intermediate state between a Domain Object not yet existing as accepted and its existing as accepted. A Domain Event represents this single transition and no finer-grained process within it.

Because a Domain Object has stable identity independent of its content, per OE-002, the corresponding Domain Event's reference to that identity is likewise stable. Because an accepted Domain Object is permanent and MUST NOT be mutated, per OE-002, the corresponding Domain Event is permanent and MUST NOT be mutated. Historical preservation of a Domain Object, per OE-002, therefore entails historical preservation of the Domain Event that represents its acceptance.

## 7. Event Ordering

The following ordering rules follow directly from OE-002 and from no additional source:

- a Domain Event whose Domain Object references another Domain Object MUST NOT occur before the referenced Domain Object's own event has occurred;
- a Domain Event concerns exactly one Case; ordering constraints between events apply only within the same Case;
- Knowledge Reference's and Reasoning Trace's events are never first in a Case, since both object types require at least one prior reference;
- Observation's event, and the events of any Judgment, Decision, or Outcome instance using the internal-content form, MAY be first in a Case;
- an Outcome's event MAY occur at any time relative to the time its own content treats the realized matter as having become actual; retrospective recording does not violate any ordering rule stated here, because ordering rules in this model govern acceptance dependencies between Domain Objects, not the relationship between acceptance time and represented time;
- no mandatory global sequence exists among the six Domain Event types. This document does not require, and MUST NOT be read to imply, that the six Domain Objects are accepted in any particular overall order.

This document does not state any further ordering rule. Any additional constraint on which Domain Objects may occupy a given relational role is governed by Domain Invariants and is not addressed here.

## 8. Supersession and Reinterpretation

OE-002 permits a later Domain Object to supersede or reinterpret an earlier one without erasing or overwriting it.

This document defines no separate Domain Event for supersession or reinterpretation.

Where supersession or reinterpretation is represented under the Domain Object Model, the later Domain Object is accepted through its ordinary corresponding acceptance event. That event establishes only that the later Domain Object was accepted. The semantic relationship of supersession or reinterpretation is established, if at all, by the Domain Object Model rather than by the event itself.

This document defines no update, supersession, reinterpretation, revision, or deletion events.

## 9. Event Time and Represented Time

Event time is the time at which a Domain Object's acceptance occurred. Represented time, where an object's content concerns any temporal matter, is a property of that content, not of the event.

These two times are distinct and MUST NOT be conflated. A Domain Event's own time is always the acceptance time. Where a Domain Object's content treats some matter as having occurred at an earlier point — as Outcome's own definition in OE-002 permits — the event representing that object's acceptance MUST still be understood as timed at acceptance, not at the represented time.

This distinction is what allows retrospective recording, as permitted for Outcome under OE-002, without contradiction: an Outcome's event occurring after the time its content treats the realized matter as having become actual is fully compatible with this model, not an exception to it.

## 10. Explicit Exclusions

This document does not define:

- Domain Invariants;
- validation rules, levels, or procedures;
- implementation mechanics of any kind;
- event transport or messaging infrastructure;
- replay systems;
- persistence or storage mechanisms;
- API definitions;
- database schema;
- serialization formats;
- engineering operations or guidance.

Any of the above, where relevant, is defined in a separate, dependent normative document.

## 11. Dependency and Authority

The normative dependency chain governing this document is:

```
Architecture Doctrine
   →  OE-002 — Domain Object Model
   →  OE-003 — Domain Event Model
```

This document MUST NOT redefine any fact whose authoritative home is OE-002, including the Domain Object Set, any object's definition, identity, responsibility, ownership boundary, or relationships. This document MUST NOT redefine any fact whose authoritative home is the Architecture Doctrine.

## 12. Open Questions

This document retains no open question.

The unresolved object-form questions preserved by OE-002 do not alter the event correspondence established here. Each accepted Domain Object corresponds to the acceptance event for its Domain Object type regardless of whether the object's permitted content is internal or referential.

Any future architectural change introducing a genuinely distinct acceptance fact would require amendment under the Architecture Doctrine and MUST NOT be inferred from OE-002's current open questions alone.

## 13. Definition of Done for OE-003

This document satisfies the Architecture Doctrine's definition of a normative publication when:

- its content is consistent with the Architecture Doctrine and with OE-002, its upstream documents;
- every fact it states has exactly one authoritative home within this document, per the Doctrine's single-source-of-truth principle;
- its status is explicitly stated;
- no open question is retained, per Section 12;
- a historical decision record exists for the decision the publication enacts, or the publication is explicitly part of an incomplete change package that MUST NOT be considered closed until that record exists.

This document's completion does not require the existence of Domain Invariants, validation rules, or any implementation.

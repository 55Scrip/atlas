# OE-006 — Domain Acceptance Model

**Status:** Final.

## 1. Purpose and Scope

This document is the authoritative normative definition of the Domain Acceptance Model for Atlas Core's architecture. It states:

- what acceptance means;
- what is accepted;
- the relationship between successful validation and acceptance;
- the architectural state before and after acceptance;
- the relationship between Domain Object acceptance and Domain Event occurrence;
- the atomicity of object admission and event occurrence;
- the permanence of accepted state;
- whether acceptance is deterministic at the architectural level;
- whether acceptance may partially occur;
- what acceptance establishes and does not establish;
- what happens when a candidate transition that yielded Valid is not accepted;
- what authority or initiation is excluded from this model;
- the boundary between normative acceptance and implementation-specific persistence or transaction mechanisms.

This document does not define Domain Objects, Domain Events, Domain Invariants, the validation subject, or the Valid or Invalid outcome definitions. This document is governed by, and MUST be read together with, the Architecture Doctrine, OE-002 — Domain Object Model, OE-003 — Domain Event Model, OE-004 — Domain Invariants, and OE-005 — Domain Validation Model. It does not restate the content of any of these five documents beyond what is necessary to state the acceptance model precisely.

## 2. Normative Status

This document is normative only for the Domain Acceptance Model. It has no authority over the Domain Object Set, the Domain Event set, the Domain Invariant set, the validation subject, or the Valid or Invalid outcome definitions.

This document depends on the Architecture Doctrine for its investigation, decision, publication, amendment, removal, and reopening procedures; on OE-002 for the Domain Object Set; on OE-003 for the Domain Event set; on OE-004 for the invariant set; and on OE-005 for the validation subject and the Valid outcome that is this document's own precondition. This document MUST NOT redefine any fact stated in any of the five upstream documents.

## 3. Definition of Acceptance

Acceptance is the actual admission of the candidate Domain Object belonging to a candidate state transition that yielded Valid under OE-005, together with the occurrence of that transition's corresponding candidate Domain Event.

Acceptance is not validation. Acceptance is not a validation outcome. Acceptance is not a Domain Object. Acceptance is not a separate Domain Event. Acceptance is not persistence. Acceptance is not serialization. Acceptance is not transport. Acceptance is not user approval. Acceptance is not business approval. Acceptance is not a recommendation. Acceptance is not a repair procedure. Acceptance is not implementation execution.

## 4. Acceptance Subject

The acceptance subject is the same complete candidate state transition that yielded Valid under OE-005:

```
prior accepted architectural state
   + candidate Domain Object
   + its corresponding candidate Domain Event
   →  resulting accepted architectural state
```

Valid is a result of the complete candidate state transition. Valid is not a separate status assigned independently to the candidate Domain Object. Valid is not a separate status assigned independently to the candidate Domain Event. Acceptance admits the object and causes the event to occur only as the two elements of the same transition that yielded Valid.

The prior accepted architectural state is the same prior state used in the Valid determination. The candidate Domain Object is the same candidate object included in that determination. The corresponding candidate Domain Event is the same candidate event included in that determination. No candidate element may be replaced, altered, re-specified, or substituted between validation and acceptance. Any change to the prior state, the candidate Domain Object, or the candidate Domain Event means the transition is no longer the same transition that yielded Valid, and therefore requires validation of the changed transition under OE-005.

No second or altered candidate is created between validation and acceptance. Acceptance applies only to a complete candidate state transition that has already yielded Valid under OE-005; this document does not define a separate act of re-specifying, re-forming, or re-describing the candidate between validation and acceptance.

## 5. Validation as Necessary Precondition

Valid is necessary for acceptance. A candidate MUST NOT be accepted unless its state transition has yielded Valid under OE-005.

Invalid absolutely prohibits acceptance. Validation does not itself perform acceptance; a Valid outcome establishes eligibility, not inevitability. A transition that yielded Valid MAY remain unaccepted.

This document does not define who or what initiates acceptance. No authorization, command, workflow, actor, policy, or orchestration mechanism is defined here.

## 6. Atomic Acceptance Transition

Acceptance of the candidate Domain Object and occurrence of its corresponding Domain Event are one indivisible architectural transition, consistent with OE-004's INV-008.

There is no normative state in which the object has been accepted but its event has not occurred, in which the event has occurred but the object has not been accepted, or in which only part of either has entered accepted state. Acceptance either occurs completely or does not occur.

This document does not define database transactions, locks, commit protocols, rollback mechanisms, or distributed systems behavior.

## 7. Resulting Accepted State

The resulting accepted architectural state is:

- the complete prior accepted architectural state;
- plus exactly the accepted candidate Domain Object;
- plus exactly its corresponding occurred Domain Event;
- with every applicable upstream invariant continuing to hold.

Acceptance MUST NOT mutate or replace any prior accepted Domain Object or Domain Event. Acceptance MUST NOT erase, rewrite, repair, supersede, or reinterpret prior accepted history. No deletion, amendment, correction, invalidation, retraction, replacement, supersession, or reversal mechanism is defined by OE-006; any future normative change to the architecture would require the Architecture Doctrine's amendment or reopening procedures and is not part of the acceptance transition defined here.

## 8. Permanence

Once acceptance has occurred:

- the Domain Object is accepted permanently;
- the corresponding Domain Event has occurred permanently;
- neither is returned to candidate status;
- neither is made "unaccepted" by this model;
- acceptance is not provisional;
- acceptance is not pending;
- acceptance is not reversible within this document.

This document does not infer or introduce deletion, amendment, correction, invalidation, retraction, replacement, or supersession mechanisms. No such mechanism is defined by OE-006; any future normative change to the architecture would require the Architecture Doctrine's amendment or reopening procedures and is not part of the acceptance transition defined here.

## 9. Acceptance Outcome

OE-006 defines acceptance by whether the complete architectural transition occurred. It does not define a separate set of acceptance outcomes.

"Accepted" is not a new Domain Object, a new Domain Event, or a result type. Non-occurrence of acceptance is not Rejected, Failed, Pending, Deferred, Cancelled, Unknown, or Partially Accepted. A transition that yielded Valid MAY remain unaccepted without producing a new result.

This document does not introduce AcceptedResult, Rejected, Failed, Pending, Deferred, Cancelled, Partially Accepted, Unknown, or any warning state. A separate outcome concept is not forced by the adopted architecture and is explicitly rejected as unnecessary.

## 10. Determinism

Given one specific prior accepted architectural state, one specific candidate Domain Object, one specific corresponding candidate Domain Event forming a transition that yielded Valid under OE-005, and the fact that acceptance occurs, the resulting accepted architectural state is determinate.

This document does not claim that a transition which yielded Valid must necessarily be accepted, and does not claim that the initiation decision is deterministic. This document defines the architectural consequence of acceptance, not the cause or authority that triggers it.

## 11. Architectural Effects

Acceptance is state-changing by definition. Unlike validation, acceptance is not side-effect-free at the architectural level.

Its complete normative architectural effect is limited to:

- admitting exactly one candidate Domain Object;
- causing exactly its corresponding Domain Event to occur;
- producing the resulting accepted architectural state.

No other architectural side effect exists. This document does not define any implementation side effect.

## 12. Exactly-One Admission

One acceptance transition concerns exactly one candidate Domain Object and exactly one corresponding candidate Domain Event.

This document does not introduce batch acceptance, and does not claim that several Domain Objects can be accepted within one normative acceptance transition. Whether an implementation may process multiple independent transitions together is outside the scope of this document.

## 13. Prior-State Correspondence

Acceptance MUST preserve INV-006 and every other applicable invariant. A Valid determination is based on a specific prior accepted architectural state.

Acceptance is normatively justified only relative to the same prior accepted architectural state against which the candidate transition was determined Valid, unless the candidate transition is validated again against a newer state. A candidate transition previously determined Valid is not silently assumed to remain Valid once the accepted state against which it was determined has changed.

This is an architectural consistency requirement, not an implementation concurrency protocol. This document does not define version numbers, optimistic locking, revision tokens, timestamps for concurrency control, database isolation, compare-and-swap mechanisms, or retries.

## 14. No Partial Acceptance

No partial acceptance exists. Satisfying only part of the acceptance transition is not acceptance. Object admission without event occurrence is prohibited. Event occurrence without object admission is prohibited. No intermediate architectural state exists between non-acceptance and acceptance.

## 15. Implementation Failure

A particular implementation may fail to realize an acceptance transition. Such implementation failure does not create a new architectural outcome, does not mean partial acceptance occurred normatively, and does not alter the definition of acceptance stated in this document. A candidate MUST NOT be represented as accepted state unless the complete normative transition, per Section 6, actually occurred.

This document does not define exceptions, retries, compensation, recovery, rollback, persistence guarantees, or error handling. This document does not define what causes an implementation to attempt acceptance; no request, command, initiator, actor, or authorization concept is introduced here.

## 16. Acceptance Result Semantics

Acceptance establishes exactly:

- that the candidate Domain Object is now part of accepted architectural state;
- that its corresponding Domain Event has occurred;
- that the resulting state is the prior accepted state plus exactly those two elements;
- that the accepted transition satisfies every applicable upstream invariant.

Acceptance MUST NOT establish:

- persistence success;
- transport success;
- authorization;
- business desirability;
- correctness of future outcomes;
- recommendation quality;
- practical relevance;
- user agreement;
- implementation durability beyond the normative architectural meaning stated here;
- any later evaluation or learning.

This section defines the normative meaning of acceptance itself. It does not create a separate acceptance result object, an acceptance response, an acceptance record, an acknowledgement, a receipt, or an implementation return value.

## 17. Non-Acceptance

When a candidate transition that yielded Valid is not accepted:

- the prior accepted architectural state remains unchanged;
- the candidate Domain Object remains unaccepted;
- the candidate Domain Event remains not occurred;
- no rejection Domain Event occurs;
- no cancellation Domain Event occurs;
- no normative reason for non-acceptance is implied;
- no new outcome is produced by this document.

When a candidate transition is Invalid, acceptance is prohibited under OE-005, the prior accepted state remains unchanged, and the candidate event does not occur. Non-acceptance of a transition that yielded Valid and the prohibition applying to an Invalid transition MUST NOT be merged or conflated; they are distinct conditions with distinct upstream grounds.

## 18. Explicit Exclusions

This document does not define:

- initiators;
- actors;
- agents;
- permissions;
- authorization;
- commands;
- workflows;
- orchestration;
- transaction boundaries;
- persistence;
- storage;
- database commits;
- concurrency mechanisms;
- locking;
- APIs;
- schemas;
- serialization;
- transport;
- retries;
- rollback;
- compensation;
- exception handling;
- user messaging;
- telemetry;
- monitoring;
- implementation algorithms;
- engineering guidance.

## 19. Open Questions

This document retains no open question.

Who initiates acceptance, what authorizes it, how it is persisted, how transactions are implemented, how concurrency is controlled, and whether a transition that yielded Valid is eventually accepted are excluded from this model, per Section 18, not left unresolved within it.

OE-002's unresolved representation questions concerning Judgment, Decision, Outcome, and Reasoning Trace do not create an unresolved acceptance-model distinction. Acceptance applies to any complete candidate state transition that yielded Valid under OE-005, without OE-006 determining which representation permitted by OE-002 the candidate Domain Object uses. Those representation questions remain upstream and unresolved; this document does not resolve them, they create no OE-006-level open question, and no representation is independently endorsed or rejected by OE-006.

## 20. Definition of Done for OE-006

This document satisfies the Architecture Doctrine's definition of a normative publication when:

- its content is consistent with the Architecture Doctrine, OE-002, OE-003, OE-004, and OE-005, its upstream documents;
- every fact it states has exactly one authoritative home within this document, per the Doctrine's single-source-of-truth principle;
- its status is explicitly stated;
- no open question is retained, per Section 19;
- a historical decision record exists for the decision the publication enacts, or the publication is explicitly part of an incomplete change package that MUST NOT be considered closed until that record exists.

This document's completion does not require the existence of any implementation, persistence mechanism, or engineering guidance.

---

## Self-Audit

1. **Valid is attributed only to the complete candidate state transition.** Section 4 states this directly; no passage anywhere in the document describes the candidate Domain Object or candidate Domain Event as independently Valid.
2. **No independently Valid candidate Domain Object was introduced.** Section 3 and Section 4 describe the object as "belonging to" a transition that yielded Valid, never as itself carrying a Valid status.
3. **No independently Valid candidate Domain Event was introduced.** Section 3, Section 4, and Section 10 describe the event the same way — as the transition's corresponding event, never as independently Valid.
4. **Acceptance concerns the exact same prior state, candidate object, and candidate event that formed the transition yielding Valid.** Section 4 states this for all three elements explicitly, prohibiting replacement, alteration, re-specification, or substitution of any one of them.
5. **Any alteration to any of those three elements produces a different transition requiring validation under OE-005.** Stated directly in Section 4's closing sentence.
6. **Acceptance establishes exactly the normative facts listed in Section 16.** Section 16 now opens with "Acceptance establishes exactly," stating these as the necessary normative meaning of acceptance rather than optional facts.
7. **No separate acceptance result, record, response, acknowledgement, or receipt was introduced.** Section 16's closing sentence excludes all of these explicitly.
8. **No request or command concept remains in Section 15.** Section 15 now reads "an acceptance transition" rather than "a requested acceptance transition," and explicitly excludes request, command, initiator, actor, and authorization concepts.
9. **Implementation failure remains outside the normative outcome model.** Section 15 states that implementation failure creates no new architectural outcome and does not constitute partial acceptance.
10. **Permanence remains fully normative under OE-006.** Section 8 states acceptance is permanent, not provisional, not pending, and not reversible within this document, without qualification.
11. **No deletion, correction, reversal, replacement, or supersession mechanism was introduced.** Sections 7 and 8 both state this directly.
12. **OE-006 does not claim authority over future doctrinal amendment procedures.** Sections 7 and 8 now state that any future normative change would require the Architecture Doctrine's own amendment or reopening procedures, rather than asserting that no such mechanism exists anywhere, present or future.
13. **No separate binary acceptance-outcome model was introduced.** Section 9 states that acceptance is defined by whether the complete transition occurred, not by a second outcome model parallel to OE-005's Valid/Invalid.
14. **Non-occurrence of acceptance remains merely absence of the acceptance transition.** Section 9 and Section 17 both state this without introducing Rejected, Failed, Pending, Deferred, Cancelled, Unknown, or Partially Accepted.
15. **OE-002 representation questions remain unresolved and upstream.** Section 19 states this directly, without OE-006 determining which OE-002-permitted representation the candidate Domain Object uses.
16. **No component-level validity status was introduced.** Confirmed throughout Sections 3, 4, 5, 10, 13, and 17, each of which ties Valid or Invalid only to the transition, never to the object or event individually.
17. **All previously required Self-Audit confirmations remain present:** no Domain Object, Domain Event, or Domain Invariant was added or redefined; acceptance is distinct from validation; Invalid prohibits acceptance; object acceptance and event occurrence are atomic; no partial acceptance exists; exactly one object and one event are admitted per transition; prior accepted state is preserved unchanged except for the exact addition; accepted state is permanent under this model; a transition that yielded Valid remaining unaccepted changes no accepted state; acceptance is architecturally state-changing and not side-effect-free; the resulting state is determinate once acceptance occurs; initiation and authorization remain outside scope; a transition previously determined Valid is not silently assumed valid after accepted state changes; no implementation concurrency mechanism was introduced; no workflow, persistence, API, schema, serialization, or engineering mechanism was introduced; no OE-006-level open question remains; all upstream authority is preserved.

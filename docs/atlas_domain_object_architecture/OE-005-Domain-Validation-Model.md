# OE-005 — Domain Validation Model

**Status:** Final.

## 1. Purpose and Scope

This document is the authoritative normative definition of the Domain Validation Model for Atlas Core's architecture. It states:

- what validation means in this architecture;
- what is validated;
- the relationship between candidate state, accepted state, and invariant satisfaction;
- the complete normative validation outcome model;
- the meaning of success and failure;
- the relationship between validation and acceptance;
- whether validation is total, deterministic, and side-effect-free at the architectural level;
- what a validation result MUST and MUST NOT establish;
- the boundary between normative validation and implementation-specific checking.

This document does not define Domain Objects, Domain Events, Domain Invariants, or any implementation, persistence, transport, API, schema, serialization, or engineering mechanism. This document is governed by, and MUST be read together with, the Architecture Doctrine, OE-002 — Domain Object Model, OE-003 — Domain Event Model, and OE-004 — Domain Invariants. It does not restate the content of any of these four documents beyond what is necessary to state the validation model precisely.

## 2. Normative Status

This document is normative only for the Domain Validation Model. It has no authority over the Domain Object Set, the Domain Event set, or the Domain Invariant set.

This document depends on the Architecture Doctrine for its investigation, decision, publication, amendment, removal, and reopening procedures; on OE-002 for the Domain Object Set; on OE-003 for the Domain Event set; and on OE-004 for the complete invariant set against which validation is performed. This document MUST NOT redefine any fact stated in any of the four upstream documents.

## 3. Definition of Validation

Validation is the determination of whether admitting a candidate Domain Object, together with its corresponding Domain Event, would produce a resulting architectural state that satisfies every applicable Domain Invariant.

Validation concerns a proposed addition to accepted state. Validation does not mutate accepted state. Validation does not itself accept anything; it determines only whether acceptance would be architecturally valid if it occurred. Validation is not a Domain Event. Validation is not a Domain Invariant. Validation is not a repair procedure.

## 4. Validation Subject

The complete validation subject is:

```
prior accepted architectural state
   + candidate Domain Object
   + its corresponding candidate Domain Event
   →  resulting candidate architectural state
```

**Prior accepted architectural state** is the complete set of all Domain Objects and Domain Events already accepted at the point validation is performed. This set is not limited in advance to the candidate's own Case. Some invariants evaluate only relationships bounded by the candidate's Case — for example, INV-004's same-Case reference requirement. Other invariants evaluate the complete accepted state without such a limit — for example, INV-006's distinct-identity requirement, which must be checked against every accepted Domain Object, not only those in the candidate's Case. Each invariant's own stated scope, per OE-004, determines which portion of the complete accepted state is relevant to it; this document does not alter the adopted Case ownership model in stating this.

**Candidate Domain Object** is a proposed, not-yet-accepted object that makes a determinate claim about its Domain Object type. It MUST be sufficiently specified for every applicable invariant to yield a determinate result, but it is not required, before validation, to claim one of the six adopted Domain Object types or to satisfy any other invariant. Validation determines whether its claimed type and all other relevant characteristics conform to OE-004. A claimed type outside the closed Domain Object Set adopted in OE-002 yields Invalid under INV-001; this document does not thereby recognize or create any new Domain Object type, and a candidate with a non-adopted claimed type never becomes an accepted Domain Object.

**Its corresponding candidate Domain Event** is a proposed, not-yet-occurred event that would concern the candidate Domain Object if acceptance occurred. It makes a determinate claim about its Domain Event type. It MUST be sufficiently specified for every applicable invariant to yield a determinate result, but it is not required, before validation, to claim an adopted Domain Event type, to claim the event type assigned to the candidate object's claimed type, or to satisfy any other invariant.

The candidate event remains a required element of the complete validation subject. Validation determines whether its claimed event type belongs to the closed Domain Event set under INV-001, and whether its event type correctly corresponds to the candidate object's claimed type under INV-007. Validation evaluates its Case correspondence under INV-003, atomic acceptance and event occurrence under INV-008, and event-time semantics under INV-015. An Invalid candidate event never becomes an occurred Domain Event.

**Resulting candidate architectural state** is the prior accepted state as it would be if the candidate Domain Object and its corresponding Domain Event were accepted and occurred.

Validation is applied to this candidate state transition — the relationship between the prior accepted state and the resulting state that would follow from admitting the candidate. Validation is not applied to an isolated Domain Object, because relational invariants such as same-Case reference and prior acceptance of referenced targets cannot be evaluated without the prior accepted state as context. Validation is not applied to an isolated Domain Event, because a Domain Event cannot exist without the Domain Object it concerns, and its occurrence is the same architectural moment as that object's acceptance, per OE-004's INV-008; the candidate event is a required element of the complete subject, not an independent subject on its own.

## 5. Validation Basis

Validation is performed against the complete invariant set adopted in OE-004.

Every applicable invariant MUST be considered. An invariant is applicable whenever the architectural elements it constrains, per OE-004's own statement of that invariant, are present in the candidate state transition. No implementation may treat architectural validity as satisfied while omitting an applicable invariant.

This document does not restate the content of any invariant. Where an invariant is referenced below, it is referenced by identifier only.

## 6. Validation Outcome Model

The complete normative outcome set consists of exactly two outcomes: **Valid** and **Invalid**.

No third outcome exists. Warning, Unknown, Deferred, Partial, and Recoverable are not part of this model; nothing in the adopted architecture forces their existence, and none is introduced here.

## 7. Valid Outcome

A candidate state transition is **Valid** if and only if the resulting candidate architectural state satisfies every applicable invariant from OE-004. No invariant violation exists.

Valid means the candidate is architecturally eligible for acceptance. Valid does not itself perform acceptance. A Valid determination does not require that acceptance actually occur; a Valid candidate MAY remain unaccepted.

## 8. Invalid Outcome

A candidate state transition is **Invalid** if and only if the resulting candidate architectural state would violate at least one applicable invariant from OE-004.

An Invalid candidate MUST NOT be accepted under the normative model. No Domain Event occurs for a rejected candidate: the candidate Domain Event named in Section 4 is a required element of the validation subject under consideration, but it does not become an occurred Domain Event when validation yields Invalid. The prior accepted state remains exactly as it was; nothing is added, and nothing is altered. Invalidity does not prescribe repair, correction, or any other subsequent action.

## 9. Violation Set

An Invalid result MUST identify the complete set of invariants violated by the candidate state transition, by invariant identifier (INV-001 through INV-015).

This is the strongest minimal contract available: because validation is deterministic (Section 10), which invariants a given candidate violates is itself a determinate fact, not merely a convenience of any particular evaluation order. Stating only "at least one" violated invariant would discard determinate information; stating only the bare fact of invalidity would discard it entirely. Neither is adopted.

The violation set contains each violated invariant's identifier exactly once; duplicate identifiers are not permitted, since the violation set is a set, not a sequence. No ordering among its members is normative. No explanatory text is normative; this document does not require or define any accompanying explanation. An empty violation set is not permitted for an Invalid result: a result is Invalid only because at least one invariant is violated, so the violation set MUST be non-empty whenever the outcome is Invalid, and MUST be empty whenever the outcome is Valid.

This document does not define any implementation data structure for the violation set; it defines only its normative membership and properties.

## 10. Totality and Determinism

Validation is **total**: every complete validation subject, per Section 4, yields exactly one outcome — Valid or Invalid — never zero and never more than one.

Validation is **deterministic**: the same complete validation subject yields the same normative outcome on every determination, always.

Validation is **side-effect-free**: performing validation changes no accepted architectural state. No Domain Object or Domain Event is created, mutated, or removed by the act of validating.

These are architectural properties of the normative model, not claims about implementation reliability or execution. A particular implementation's failure to correctly compute the outcome of a complete subject is an implementation defect; it does not make the normative model itself partial, non-deterministic, or stateful.

## 11. Relationship to Acceptance

Successful validation — a Valid outcome — is necessary for acceptance. A candidate MUST NOT be accepted unless validation of its state transition yields Valid.

Successful validation is not itself acceptance. Validation and acceptance are conceptually distinct: validation is a determination; acceptance is the actual admission of the candidate into permanent architectural state, which, per OE-004's INV-008, coincides with the corresponding Domain Event's occurrence as the same architectural moment.

Validation failure prohibits acceptance absolutely: no candidate Domain Object or Domain Event enters accepted state when validation yields Invalid. There is no intermediate accepted state between a candidate not being accepted and its being accepted, consistent with OE-004's INV-008.

Any act, condition, or authority that initiates acceptance after a Valid outcome is outside the Domain Validation Model. Its exclusion does not create an unresolved OE-005 question. This document defines only that Valid is necessary for acceptance, that validation does not itself perform acceptance, and that a Valid candidate MAY remain unaccepted.

## 12. Prior State Preservation

Validation failure and non-acceptance leave the prior accepted architectural state exactly as it was.

Validation does not mutate any prior accepted Domain Object or Domain Event. Validation does not erase history. Validation does not create a rejection Domain Event; no such event exists in the adopted Domain Event set. Validation does not create a validation Domain Object; no such object exists in the adopted Domain Object Set. Validation does not create a repair record of any kind.

## 13. Validation of References and Ordering

Validation evaluates same-Case reference (INV-004), prior acceptance of referenced targets (INV-005), root eligibility (INV-012), Reasoning Trace minimum support (INV-013), Knowledge Reference single target (INV-014), and acceptance time as event time (INV-015) as applicable invariants, exactly as OE-004 states them. This document does not reproduce their content.

No invariant in this model is evaluated before or after any other as a matter of normative requirement. All applicable invariants are considered as a single, conjunctive whole; this document does not introduce a validation order, sequence, or precedence among them.

## 14. No Partial Validity

A candidate that satisfies some applicable invariants while violating another is Invalid. There is no architecturally valid partial-success state. Every applicable invariant is conjunctive: all MUST be satisfied for the outcome to be Valid, and any single violation is sufficient for the outcome to be Invalid, consistent with OE-004's own statement that satisfying one invariant does not waive another.

No warning outcome exists for a candidate that violates some invariants while satisfying others; such a candidate is Invalid, in full, without qualification.

## 15. Indeterminacy and Unavailable Information

A complete validation subject cannot yield an indeterminate normative outcome. Per Section 10, every complete subject yields exactly one of Valid or Invalid.

A validation subject is incomplete only when the available architectural specification is insufficient to determine the complete applicable violation set. This includes: the prior accepted architectural state is absent; the candidate Domain Object is absent; the corresponding candidate Domain Event is absent; or a required main element is present but specified insufficiently, such that at least one applicable invariant cannot yield a determinate result.

Incompleteness MUST NOT be used to avoid a determinable invariant violation. Whenever missing, malformed, or non-conforming candidate content itself determines an invariant violation, the complete validation subject yields Invalid rather than being classified as incomplete.

For example: if no candidate Domain Event is provided at all, the validation subject is incomplete. If a candidate Domain Event is present but belongs to the wrong Case, the candidate is Invalid under INV-003. If a proposed Knowledge Reference is present but identifies no target, the candidate is Invalid under INV-014; it is not an indeterminate result and not merely an absent validation subject. If the candidate is so insufficiently specified that its claimed Case cannot be determined and no complete applicable violation set can be established, the validation subject is incomplete — unless the missing information itself directly determines a specific invariant violation, in which case the candidate is Invalid under that invariant instead. A candidate object with a determinate claimed type outside the closed Domain Object Set is Invalid under INV-001. A candidate event with a determinate claimed type outside the closed Domain Event Set is Invalid under INV-001. A candidate event with an adopted but incorrectly assigned event type is Invalid under INV-007. A candidate whose claimed object or event type cannot be determined may constitute an incomplete validation subject when that prevents determination of the complete applicable violation set; incompleteness MUST NOT be used to avoid a determinate INV-001 or INV-007 violation where the claimed type is in fact determinate.

Three distinct matters must not be conflated:

- **Incomplete validation subject** — the available architectural specification is insufficient to determine the complete applicable violation set, whether because a required main element (prior accepted state, candidate Domain Object, or candidate Domain Event) is entirely absent, or because one is present but insufficiently specified for at least one applicable invariant to yield a determinate result.
- **Determinate normative invalidity** — the candidate Domain Object and its corresponding Domain Event are present and sufficiently specified for every applicable invariant to yield a determinate result, and at least one applicable invariant is violated. This is Invalid, in full.
- **Implementation inability to evaluate a complete subject** — a particular implementation's failure to compute an outcome for an otherwise-complete subject is an implementation concern, not a normative one; the normative model asserts that a correct determination exists and is unique for any complete subject, regardless of any implementation's ability to compute it.

Incomplete validation subject is not a third validation outcome; it means validation has not occurred on a complete subject. The outcome set remains exactly Valid and Invalid, per Section 6. This document does not introduce Unknown, Deferred, Partial, Warning, or Recoverable as outcomes, and does not define syntactic validation stages, parsing rules, deserialization rules, construction procedures, or pre-validation pipelines. Those distinctions belong to implementation, not to this document.

## 16. Validation Result Semantics

A normative validation result MAY establish only:

- Valid or Invalid;
- the complete violated-invariant identifier set, where the result is Invalid, per Section 9.

A normative validation result MUST NOT establish:

- acceptance;
- persistence success;
- transport success;
- user authorization;
- business desirability;
- practical relevance;
- recommendation quality;
- any future outcome;
- repair instructions.

## 17. Explicit Exclusions

This document does not define:

- implementation algorithms;
- evaluation sequence;
- caching;
- concurrency;
- persistence;
- transport;
- APIs;
- schema;
- serialization;
- exceptions;
- retries;
- repair;
- user messaging;
- monitoring;
- telemetry;
- engineering guidance.

Any of the above, where relevant, belongs to implementation, not to this document.

## 18. Dependency and Authority

The normative dependency chain governing this document is:

```
Architecture Doctrine
   →  OE-002 — Domain Object Model
   →  OE-003 — Domain Event Model
   →  OE-004 — Domain Invariants
   →  OE-005 — Domain Validation Model
```

This document MUST NOT redefine any fact whose authoritative home is OE-002, OE-003, or OE-004, including the Domain Object Set, the Domain Event set, the invariant set, or any relationship, ownership boundary, ordering fact, or invariant statement already established by those documents. This document MUST NOT redefine any fact whose authoritative home is the Architecture Doctrine.

## 19. Open Questions

This document retains no open question.

Valid is necessary for acceptance; Valid does not itself perform acceptance; a Valid candidate MAY remain unaccepted; whether acceptance is initiated is outside the Domain Validation Model. This distinction is already complete and is not treated as an unresolved validation question.

OE-002's unresolved representation questions do not create an unresolved validation-outcome distinction. INV-004 and INV-005 apply whenever a permitted referential form is used. INV-012 applies conditionally according to whether the permitted internal or referential form is used, without deciding whether those forms may coexist within one undifferentiated instance. INV-013 does not resolve how a Reasoning Trace's supported claim is represented. Validation evaluates these invariants exactly as OE-004 states them and requires no upstream representation question to be resolved.

## 20. Definition of Done for OE-005

This document satisfies the Architecture Doctrine's definition of a normative publication when:

- its content is consistent with the Architecture Doctrine, OE-002, OE-003, and OE-004, its upstream documents;
- every fact it states has exactly one authoritative home within this document, per the Doctrine's single-source-of-truth principle;
- its status is explicitly stated;
- no open question is retained, per Section 19;
- a historical decision record exists for the decision the publication enacts, or the publication is explicitly part of an incomplete change package that MUST NOT be considered closed until that record exists.

This document's completion does not require the existence of any implementation, persistence mechanism, or engineering guidance.

---

## Self-Audit

- **No Domain Object, Domain Event, or Domain Invariant added or redefined.** This document names only the six Domain Objects, six Domain Events, and fifteen invariants already adopted upstream, and states no new fact about their definitions — only how they are collectively evaluated.
- **Section 4 no longer pre-assumes INV-001 compliance.** The candidate Domain Object and candidate Domain Event are now defined as making a determinate *claim* about their respective types, not as already being instances of an adopted type; whether that claim falls within the closed sets is something validation itself determines.
- **Section 4 no longer pre-assumes type-correct INV-007 correspondence.** The candidate event's definition no longer states that its type is simply "the type assigned to the candidate object's type"; it states only that the candidate event makes a determinate claim about its own type, with INV-007 determining whether that claim correctly corresponds to the candidate object's claimed type.
- **Candidate object and event type claims may be determinately non-conforming.** Both definitions state explicitly that the candidate is not required, before validation, to claim an adopted type or the correctly corresponding type; validation determines conformance rather than assuming it.
- **Non-adopted claimed types yield Invalid under INV-001.** Stated directly in Section 4 for the candidate object, and in Section 4 and Section 15 for the candidate event, with concrete examples in Section 15.
- **An adopted but incorrectly assigned event type yields Invalid under INV-007.** Stated directly in Section 4 and illustrated with a concrete example in Section 15.
- **Indeterminate type specification produces incomplete subject only where the complete applicable violation set cannot be determined.** Section 15 states this explicitly and distinguishes it from a determinate INV-001 or INV-007 violation, which is never reclassified as incompleteness merely because the type claim happens to be wrong.
- **No new Domain Object type or Domain Event type was added or recognized.** Section 4 states explicitly that a non-adopted claimed type is never thereby created or recognized as a new type, and a candidate with such a claim never becomes an accepted Domain Object.
- **The closed upstream type sets remain unchanged.** OE-002's six Domain Objects and OE-003's six Domain Events are named exactly as before; only how a candidate's claim about its own type is evaluated has changed.
- **The outcome set remains exactly Valid and Invalid.** No third outcome is introduced anywhere in this revision; incomplete validation subject continues to mean that validation has not occurred on a complete subject, not a third result.
- **No implementation or construction model was introduced.** Section 4 and Section 15 continue to exclude event payloads, identifiers, schemas, serialization, constructors, and parsing; Section 17 excludes all remaining implementation-level concerns.
- **Validation and acceptance remain distinct, with no open question remaining.** Section 11 and Section 19 are unchanged by this correction and continue to state that successful validation is necessary but does not itself cause acceptance, that a Valid candidate MAY remain unaccepted, and that no OE-005-level open question remains.
- **Doctrine, OE-002, OE-003, and OE-004 authority preserved.** Section 18 states the full dependency chain and explicitly prohibits redefinition of any upstream fact; Section 13 references invariants by identifier only, without reproducing their content.

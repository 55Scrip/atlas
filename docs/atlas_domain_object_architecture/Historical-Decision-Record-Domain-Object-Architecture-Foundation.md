# Historical Decision Record — Domain Object Architecture Foundation

This historical record explains why the adopted decisions covered below were made. It does not redefine them. Where this record and a normative document appear to differ, the normative document governs.

## Purpose

This record documents the decisions that established Atlas Core's Domain Object Architecture: the Architecture Doctrine and OE-002 through OE-006, together with the investigation and non-publication of a proposed OE-007 — Domain Rejection Model. It exists to satisfy the historical-record condition stated in each of those documents' own Definition of Done sections. It is not itself a source of normative architecture.

## Change-Package Scope

This record covers, in the order each document was published:

1. Architecture Doctrine — `docs/atlas_domain_object_architecture/Doctrine.md`
2. OE-002 — Domain Object Model — `docs/atlas_domain_object_architecture/OE-002-Domain-Object-Model.md`
3. OE-003 — Domain Event Model — `docs/atlas_domain_object_architecture/OE-003-Domain-Event-Model.md`
4. OE-004 — Domain Invariants — `docs/atlas_domain_object_architecture/OE-004-Domain-Invariants.md`
5. OE-005 — Domain Validation Model — `docs/atlas_domain_object_architecture/OE-005-Domain-Validation-Model.md`
6. OE-006 — Domain Acceptance Model — `docs/atlas_domain_object_architecture/OE-006-Domain-Acceptance-Model.md`

and the closed, non-published proposal:

7. Proposed OE-007 — Domain Rejection Model (investigated, not published; no corresponding file exists).

Each of OE-003 through OE-006 explicitly states, in its own Normative Status section, that it depends on every document published before it in this list, not merely the one immediately preceding it. This record restates that fact; it does not itself establish a stronger or different dependency relationship than each document already states of itself.

## Investigation Origin

The Domain Object Architecture was developed to establish a minimal, non-redundant ontology for Atlas Core's permanent domain facts, governed by a fixed method rather than by inherited terminology or ad hoc convention. The investigation began from a broader candidate set of permanent domain concepts and subjected each to dimension-by-dimension distinctness testing — identity conditions, semantic operation, validity conditions, relationship topology, and Historical Integrity behaviour — before treating any concept as an independent architectural category. This method was applied uniformly to every candidate, including candidates that were ultimately not adopted.

## Decision History: Architecture Doctrine

The Doctrine was published first and establishes only method: how architectural investigation, decision, publication, amendment, removal, and reopening are conducted, and how architecture is separated from implementation. It names no specific Domain Object, Domain Event, or invariant, so that it could govern adoption of the Domain Object Set that followed without being coupled to that set's outcome.

## Decision History: OE-002 — Domain Object Model

**Adopted Domain Object Set:** Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome — six types, defined in full in OE-002 itself.

**Major alternative considered:** An earlier candidate set of eight Domain Object types, additionally including Evaluation and Learning Event. Each candidate was tested independently for a genuinely distinct semantic operation, identity condition, validity condition, and relationship topology. Evaluation and Learning Event were each found reducible to Judgment: neither demonstrated a semantic operation, identity condition, validity condition, or relationship topology distinct from Judgment's own established characterization function. No forcing function was found for retaining either despite this finding.

**Basis for adoption:** The six retained types each demonstrated a semantic operation not derivable from any other retained type: preservation of content (Observation), reference to knowledge (Knowledge Reference), epistemic support (Reasoning Trace), characterization (Judgment), practical commitment (Decision), and realization (Outcome), as OE-002 itself states for each.

**Unresolved representation question:** Whether the subject-matter of Judgment, Decision, and Outcome, and the supported claim of Reasoning Trace, may take the form of content contained within the object itself, a reference to another same-Case Domain Object, or — unresolved — both simultaneously within one undifferentiated type. Both forms were independently tested and found viable for each of these objects; no textual basis was found in the adopted architecture for a mechanism permitting both forms within a single type.

**Why deferred:** Each object's minimum semantic contract is fully statable without resolving this question, satisfying the Doctrine's own permission (§7) for a settled document to retain an explicitly identified open question that does not block its minimum contract.

**Reopening condition:** Per the Doctrine's general reopening standard (§8): a demonstrated architectural fact requiring both forms to coexist within one type, or a downstream document that cannot state its own contract without this question first being resolved.

## Decision History: OE-003 — Domain Event Model

**Adopted Domain Event Set:** ObservationAccepted, KnowledgeReferenceAccepted, ReasoningTraceAccepted, JudgmentAccepted, DecisionAccepted, OutcomeAccepted — one event per adopted Domain Object type, in a fixed one-to-one correspondence, as OE-003 itself states.

**Rejected event types without independent semantics:** Separate events for supersession, reinterpretation, revision, or deletion were considered and rejected, since a later Domain Object may supersede or reinterpret an earlier one through its own ordinary acceptance event, requiring no additional event type.

**Naming revision:** The event names as originally supplied used process-, production-, or completion-oriented verbs. During drafting, review found these names semantically inconsistent with OE-003's own definition of a Domain Event as representing acceptance specifically, and the names were revised to consistently end in "Accepted."

**Why sufficient:** No downstream document, including the OE-007 investigation, required an additional event type or a different correspondence model.

## Decision History: OE-004 — Domain Invariants

**Why a closed invariant set was required:** An open-ended or implementation-discoverable invariant set would allow architectural validity to be redefined ad hoc, contrary to the Doctrine's single-source-of-truth principle.

**Role of invariants:** Each invariant states a condition that MUST hold in every valid architectural state, distinct from the validation procedure (OE-005) that determines whether a state satisfies them.

**Major dimensions covered:** closed architectural type sets; Case ownership; reference integrity; distinct identity; acceptance and existence; permanence; root eligibility; and event time as acceptance time — fifteen invariants in total.

**Corrections made during drafting:** An earlier formulation of the closed-type-set invariant covered only the Domain Object Set; it was corrected to cover both the closed Domain Object Set and the closed Domain Event Set together, since both are the same kind of closure fact. A separate earlier formulation of the root-eligibility invariant duplicated Reasoning Trace's minimum-support requirement and Knowledge Reference's single-target requirement; it was corrected to state only first-in-Case status, leaving those two requirements exclusively to their own invariants.

**Adopted closure boundary:** The fifteen-invariant set does not include validation procedure, severity, or repair content; those remain OE-005's and implementation's respective domains.

## Decision History: OE-005 — Domain Validation Model

**Why validation applies to the complete transition:** Isolated-object and isolated-event framings were tested and found incomplete, since relational invariants cannot be evaluated without the prior accepted state, and an event cannot exist without the object it concerns. The validation subject was adopted as the complete transition: prior accepted state, candidate Domain Object, and its corresponding candidate Domain Event together.

**Why Valid and Invalid are exhaustive:** Warning, Unknown, Deferred, Partial, and Recoverable outcomes were each considered and found not required by the adopted architecture.

**Why Invalid carries a complete violation set:** A model requiring only "at least one" violated invariant, or only the bare fact of invalidity, was considered and rejected as discarding determinate information, given that validation is deterministic.

**Why incomplete subjects are not Invalid:** A subject missing a required main element, or insufficiently specified for a given invariant to yield a determinate result, is incomplete, not Invalid; incompleteness was explicitly barred from being used to avoid a determinable violation.

**Why validation does not itself perform acceptance:** Validation was adopted as a determination, side-effect-free with respect to accepted state; acceptance was deferred to a separate document.

**Correction made during drafting:** An earlier formulation described the candidate Domain Object and candidate Domain Event as already claiming an adopted or correctly corresponding type, which would have made it impossible for validation to determine a type violation. This was corrected so that a candidate makes only a determinate claim about its type, with conformance determined by validation itself.

## Decision History: OE-006 — Domain Acceptance Model

**Why acceptance is distinct from validation:** Acceptance was adopted as the actual admission of a candidate into permanent state following a transition that yielded Valid, distinguished from validation's determination of eligibility alone.

**Why Valid is necessary but not sufficient:** A model in which a Valid outcome automatically caused acceptance was considered and rejected; a transition that yielded Valid may remain unaccepted without contradiction.

**Why Invalid absolutely prohibits acceptance:** No discretion was found or adopted.

**Why acceptance changes accepted state:** Acceptance was adopted as state-changing by definition, limited to admitting exactly one candidate Domain Object and causing exactly its corresponding Domain Event to occur.

**Why no separate acceptance-outcome model was adopted:** AcceptedResult, Rejected, Failed, Pending, Deferred, Cancelled, Partially Accepted, Unknown, and Warning outcomes were each considered and found unforced.

**Corrections made during drafting:** An earlier formulation attributed the Valid outcome independently to the candidate Domain Object and candidate Domain Event; this was corrected so that Valid and Invalid are attributed only to the complete transition. A separate earlier formulation stated that no correction, deletion, or reversal mechanism "exists" in absolute terms; this was corrected to state instead that any future normative change would require the Doctrine's own amendment or reopening procedures.

## Investigation Closure: Proposed OE-007 — Domain Rejection Model

A Domain Rejection Model was investigated as a candidate seventh normative document. A full draft was produced and reviewed claim by claim against OE-005 and OE-006's own already-published authority. Every proposed fact — that Invalid grounds rejection, that rejection prohibits acceptance, that a rejected transition remains unaccepted, that prior accepted state is preserved, that the candidate event does not occur, and that no separate rejection object, event, record, or outcome exists — was found already owned by OE-005 or OE-006, or a direct corollary of combining facts each already owned by one of them. No independent subject, operation, state, event, object, result, outcome, authority, actor, or workflow was found, and no forcing function was identified.

**Disposition: Do Not Publish.** Publishing the proposal would have duplicated normative authority already held by OE-005 and OE-006.

"Rejection" may be used only as non-normative shorthand for "a transition that yielded Invalid, whose acceptance is therefore prohibited." No normative OE-007 document was published or created. This record makes no decision about future OE identifier allocation.

**Reopening condition:** a newly discovered forcing function — an inexpressible adopted fact concerning Invalid, an unavoidable contradiction between OE-005 and OE-006, a downstream model unable to refer precisely to the existing terms, a genuine new-consequence lifecycle distinction, or a required absent state, event, object, relation, invariant, or outcome. Ordinary-language familiarity, documentary convenience, numbering symmetry, workflow familiarity, a desire to name the consequence of Invalid, and implementation preference do not satisfy this condition.

## Single-Source-of-Truth Allocation

The Domain Object Set and object definitions belong exclusively to OE-002; the Domain Event set and event definitions to OE-003; the invariant set to OE-004; the validation subject and Valid/Invalid outcomes to OE-005; the acceptance transition to OE-006. No fact was found to require synchronization across more than one of these documents.

## Separation of Ontology from Implementation

No persistence, API, schema, serialization, transport, or engineering mechanism was adopted in any of these six documents; each explicitly excludes implementation concerns from its own scope.

## Architectural Consequences

- Every normative fact adopted in this change package has exactly one authoritative home.
- Any future work concerning Domain Objects, Domain Events, invariants, validation, or acceptance must conform to OE-002 through OE-006 respectively, or amend them through the Doctrine's own change protocol.
- The internal-versus-referential representation question for Judgment, Decision, Outcome, and Reasoning Trace's supported claim remains open and deferred, without blocking any adopted document's own contract.
- Implementation remains a separate, later concern, not addressed by this change package.
- No Domain Rejection Model currently exists in this architecture.

## Reopening Conditions

**For the change package generally:** per the Architecture Doctrine's own general standard (§8), only a newly identified domain fact inexpressible by the adopted architecture, an unavoidable contradiction within it, a downstream normative task exposing a real expressive gap, or evidence that this investigation omitted a materially distinct candidate or misapplied the Doctrine's method.

**For the OE-002 representation question specifically:** stated above, under its own decision history.

**For the non-adoption of a Domain Rejection Model specifically:** stated above, under its own investigation closure.

None of these reopening conditions is satisfied by convenience, symmetry, familiarity, or preference.

## Repository Provenance

The documents covered by this record were published in the following order, each as its own commit to `docs/atlas_domain_object_architecture/`:

1. `9cdf6e20bdc65d3c293ac35a9a11031eda061a52` — Architecture Doctrine
2. `1bfa2245a57fecada2c6ed6b10ee3805726b649d` — OE-002 — Domain Object Model
3. `cc72cb31cec1d94daf4069c3fefe93b6ad2196a4` — OE-003 — Domain Event Model
4. `858835f2bba497e5f20b50791cdb348d72b56ca2` — OE-004 — Domain Invariants
5. `372e3bf592dac39f389ea36acd4d2cd96483dd74` — OE-005 — Domain Validation Model
6. `b123153f4a674f07aa96720939932a4602ad8dc8` — OE-006 — Domain Acceptance Model

The proposed OE-007 — Domain Rejection Model was investigated and closed without a corresponding commit, consistent with its non-publication.

This commit metadata records publication history; it does not itself constitute or replace the architectural reasoning recorded above, which remains the authoritative explanation of why each decision was made.

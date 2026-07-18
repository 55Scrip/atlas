# Atlas Core — Architecture Doctrine

**Status:** Final.

## 1. Purpose and Scope

This Doctrine governs the method by which Atlas Core's architecture is investigated, decided, published, amended, removed, reopened, and historically preserved. It governs the relationship between architecture and implementation.

This Doctrine governs:

- architectural investigation;
- ontological decision-making;
- normative publication;
- amendment of normative documents;
- removal of architectural categories;
- reopening of closed architectural decisions;
- historical preservation of architectural decisions;
- the separation between architecture and implementation.

This Doctrine does not govern ordinary product planning, engineering process, or repository operations, except to the extent required to preserve the boundary between architecture and implementation described in Section 12.

This Doctrine applies to every document subordinate to it in the normative dependency chain. It does not itself define any domain fact.

## 2. Ontology-First Principle

Architecture MUST begin with an inquiry into the domain fact or candidate domain distinction being represented.

A domain fact is a distinction established as belonging to the subject matter the architecture describes. A candidate domain distinction is a proposed distinction whose existence and architectural relevance have not yet been established.

Architecture MUST NOT begin with, and MUST NOT be justified by:

- existing code;
- database schema;
- API shape;
- naming familiarity;
- workflow convenience;
- user-interface needs;
- the existence of a prior document;
- migration cost.

Repository facts MAY inform implementation and migration planning. Repository facts MUST NOT be used to establish, confirm, or deny an ontological claim.

## 3. Burden of Justification

Inclusion of a category in the architecture requires positive justification. A candidate category MUST NOT be accepted on the grounds that:

- it already exists, in the repository or elsewhere;
- it has a familiar or established name;
- it appears in a workflow or process description;
- it seems useful;
- it may be needed at some future time;
- no one has disproved it.

Absence of a demonstrated contradiction is not sufficient to establish that a candidate is a distinct architectural category. The burden of showing a candidate is distinct falls on whoever proposes it, not on whoever would leave the existing architecture unchanged.

## 4. Candidate Investigation Method

An investigation into a proposed architectural category MUST address, at minimum:

- a precise statement of the question under investigation;
- multiple plausible candidate models, stated as genuine alternatives rather than a single preferred account;
- the exact semantic commitment each candidate makes;
- the identity conditions each candidate implies;
- the validation implications of each candidate;
- the relationship-topology and dependency implications of each candidate;
- the Historical Integrity implications of each candidate;
- an explicit test of each candidate against every established constraint and every already-retained category;
- a reducibility test, per Section 5;
- a record of every rejected candidate and the specific ground for its rejection.

Preference, elegance, symmetry, familiarity, and implementation convenience MUST NOT be treated as sufficient grounds for accepting or rejecting a candidate.

## 5. Distinctness and Reducibility

A candidate category is not distinct merely because it has:

- a different name than an existing category;
- a different position in a workflow;
- a different subject matter than an existing category, where that existing category's own definition already permits such subject matter;
- a different moment of creation;
- a different presentation in a user interface;
- a different associated event name.

A candidate category is genuinely distinct only if it preserves a domain fact that cannot be represented, without loss, contradiction, or semantic distortion, through an already-retained category.

If no such fact is demonstrated, the candidate is reducible to the already-retained category. A reducible candidate MUST NOT be adopted as an independent normative category, regardless of its name, prior usage, or apparent usefulness.

## 6. Decision Standard

An architectural investigation MAY be closed only when all of the following hold:

- the question investigated is stated explicitly;
- the viable alternative candidates have been tested against this Doctrine's method;
- the ground for rejecting each rejected alternative is stated;
- the surviving conclusion is positively justified, not merely the last candidate remaining;
- any unresolved question is stated separately from, and does not contaminate, the settled conclusion;
- implementation facts have not been used as evidence of an ontological claim;
- historical claims and current normative claims are distinguished from one another;
- the result states its normative consequences for dependent documents;
- the result states the decision-specific reopening condition under which it may later be revisited.

A legitimate outcome of an investigation is that no new category is justified. This outcome MUST be treated as a complete, positive result, not as an incomplete investigation.

## 7. Open Questions Inside Settled Decisions

An architectural category, or a normative document, MAY be settled in one respect while retaining one or more explicitly identified open questions in another respect.

A status such as Final, or any equivalent adopted status, MUST NOT be read to imply that every question about the category or document has been resolved. It MUST be read to mean only that the category or document is normatively adopted within its stated scope.

An open question retained alongside a settled status MUST:

- be stated precisely, not left implicit;
- not contradict the settled core of the decision;
- not silently expand the scope of the category beyond what was settled;
- not block publication of the settled core, unless the open question prevents the category's minimum semantic contract from being stated at all.

## 8. Forcing Functions and Reopening

A closed architectural decision MAY be reopened only upon a genuine forcing function. A genuine forcing function is one of:

- a newly identified domain fact that cannot be represented by the currently adopted architecture;
- an unavoidable contradiction discovered within the adopted model;
- a downstream normative task that exposes a real, demonstrated expressive gap;
- evidence that the original investigation omitted a materially distinct candidate, or misapplied this Doctrine's method.

The following MUST NOT, by themselves, qualify as a forcing function:

- documentary convenience;
- implementation inconvenience;
- naming preference;
- ordinary-language familiarity;
- a desire for structural symmetry;
- speculative future usefulness;
- the mere existence of legacy code;
- disagreement unaccompanied by new evidence.

A proposal to reopen a decision MUST identify:

- the prior decision being reopened;
- the specific forcing function invoked;
- the exact settled claim being challenged;
- why the applicable reopening condition is satisfied;
- the narrowest scope of reconsideration required to address the forcing function.

Reopening one decision MUST NOT automatically reopen any other settled decision. Each decision's own reopening condition governs that decision alone.

## 9. Normative Authority and Single Source of Truth

Every architectural fact MUST have exactly one authoritative home among the normative documents.

A normative document MAY reference an upstream document by stable identifier. A normative document MUST NOT duplicate an upstream document's content beyond what is necessary for that reference.

A downstream document MAY refine the scope of its own responsibility. A downstream document MUST NOT redefine a fact whose authoritative home is an upstream document.

Navigational documents, historical records, and engineering guidance have no authority to establish, alter, or contradict current ontology. Where any document appears to conflict with a normative document, authority is determined by the established normative dependency chain, not by which document is more recent, where a document is located, or the current state of any implementation.

## 10. Publication and Amendment Discipline

Creation and amendment of normative documents MUST follow these rules:

- an upstream document MUST be established, or amended, before any dependent downstream document that relies on the change;
- every downstream document that depends on a changed upstream document MUST be reviewed following that change;
- changes MUST be minimal and MUST follow dependency order;
- every amendment MUST state what changed and why;
- silent semantic overwriting of a prior normative statement is prohibited; a change MUST be visible as a change;
- a stable identifier, once assigned to a document or category, MUST NOT be reused for a different architectural responsibility, even if the original is later found unnecessary;
- a historical decision MUST remain recoverable after any later amendment.

An amendment to this Doctrine is a higher-order amendment, because it alters the method governing every downstream document. A Doctrine amendment MUST be justified independently of any single downstream decision and MUST NOT be adopted merely to accommodate the outcome of one investigation.

## 11. Historical Integrity

The current normative state of the architecture and the historical trail of decisions that produced it MUST both remain recoverable at all times.

A historical record MUST preserve:

- what was decided;
- when it was decided;
- the alternatives that were considered;
- the grounds on which each rejected alternative was rejected;
- the normative consequences the decision produced;
- the decision-specific reopening condition established for that decision.

A historical record MUST NOT become a competing source of current normative truth. Its authority extends only to the fact that a decision occurred, when, and on what stated grounds — never to what the architecture currently states.

A later amendment MAY supersede a prior norm. A later amendment MUST NOT rewrite the historical fact that the prior norm was once adopted, or erase the record of the decision that adopted it.

## 12. Architecture and Implementation Separation

The following separations MUST be maintained:

- architecture determines what must be represented;
- implementation determines how it is represented operationally;
- repository inspection informs implementation and migration planning;
- the existence of an implementation MUST NOT be treated as retroactive proof of an ontological claim;
- the cost of migration MUST NOT be treated as grounds to invalidate a settled domain fact;
- a settled architectural decision MAY be published before any corresponding implementation exists;
- implementation planning MUST NOT silently introduce new ontology.

Where implementation work discovers an apparent expressive gap, that gap MUST be returned to the architectural investigation process described in Sections 4 through 6. It MUST NOT be resolved by introducing an undocumented type, field, event, or rule at the implementation layer.

## 13. Change Protocol

Adding, removing, or materially redefining an architectural category MUST follow this sequence:

1. investigation, per Sections 4 through 6;
2. an architectural decision closing that investigation;
3. amendment of the authoritative upstream normative document;
4. review and, where necessary, amendment of every dependent normative document;
5. creation of a historical decision record;
6. alignment of navigational documentation;
7. repository inspection;
8. migration planning;
9. implementation.

Repository inspection MAY be performed earlier than this sequence for fact-finding purposes. Its findings MUST NOT determine the ontological conclusion, the architectural decision, or the normative content of any document. Repository findings MAY determine implementation scope, migration requirements, compatibility measures, and other operational consequences downstream of the normative decision.

## 14. Status and Terminology Discipline

Every normative document, and every category defined within one, MUST carry one of the following statuses, or an equivalent status defined by amendment to this Doctrine:

- **Draft** — under active investigation or revision; not yet a stable basis for dependent work.
- **Final** — normatively adopted within the document's or category's stated scope.
- **Superseded** — no longer the current norm, replaced by an identified later decision.
- **Historical** — preserved as a record of a past decision; not currently normative.

These statuses MUST be understood as follows:

- Final means normatively adopted within the stated scope. Final does not mean every internal question about the category or document has been resolved.
- Superseded does not mean erased or historically false. A superseded norm remains a true historical record of what was once adopted.
- Historical does not mean currently normative. A historical record's content MUST NOT be cited as a statement of the current architecture.

Architectural terms MUST be defined by their normative contracts as stated in the governing document. Architectural terms MUST NOT be interpreted by ordinary-language association where a normative contract exists.

## 15. Definition of Done

An architectural decision is done when it satisfies the Decision Standard in Section 6 in full.

A normative publication is done when:

- its content is consistent with every upstream document in the normative dependency chain;
- every fact it states has exactly one authoritative home, per Section 9;
- its status is explicitly stated, per Section 14;
- any open question it retains is stated explicitly and does not block its minimum semantic contract, per Section 7;
- a historical decision record exists for the decision the publication enacts, or the publication is explicitly part of an incomplete change package that MUST NOT be considered closed until that record exists.

An individual normative document MAY reach Final status before the complete change package is closed, provided its governing decision is already recoverable. The architectural change package is done only when the required historical decision record exists.

This definition of done MUST NOT be read to require implementation, repository migration, or the resolution of every internal open question before a normative publication is considered done.

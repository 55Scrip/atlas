# APS-001 — Decision Context

**Status:** Draft, v0.1. This is the first Atlas Product Specification, subordinate to APP-000 — Atlas Product Doctrine and APP-001 — Atlas Product Concept Taxonomy. It states the complete normative product behavior of Decision Context. It does not describe screens, workflows, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique.

---

## 1. Document Status and Authority

This specification is subordinate to APP-000 (Draft v0.4) and APP-001 (Draft v0.3), per APP-000 §2 and §9. It SHALL derive its behavior, priorities, and constraints from those two documents; it SHALL NOT contradict either; it SHALL NOT redefine any term either already defines.

Where this specification appears to conflict with APP-000, APP-001, or any Atlas Core normative document (the Architecture Doctrine, OE-002 through OE-006), those documents govern and this specification is wrong and must be corrected.

While Draft, this specification is a candidate governing document for Decision Context's product behavior, not yet binding on any implementation. Promotion to Final status requires deliberate review and adoption, consistent with the status discipline APP-000 §11.4 establishes across the Product Architecture.

## 2. Purpose

This specification states the complete normative product behavior of Decision Context: what it is, how it begins, what it supports while open, how it closes, what persists after closure, and the boundaries within which it operates relative to Atlas Core. It operationalizes the Decision Context concept APP-001 §3.10 accepts into behavior sufficiently complete for a future UX specification, an implementation design, engineering, QA, and any AI agent working on Atlas to build from without inventing new product rules of their own.

## 3. Scope

In scope: Decision Context's identity, ownership, lifetime, closure, persistence, concurrency, its relationship to Evidence and Investor Reasoning, its relationship to exactly one Core Case, and the responsibilities Atlas and the Investor each carry regarding it.

Out of scope, per APP-000 §1 and §10: screens, workflows, navigation, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique. Also out of scope: capital-allocation arbitration among concurrent Decision Contexts (a Portfolio-level concern APP-000 §5 defers to a future specification); relation types between historically related Decision Contexts (Section 25); and any resolution of cross-Case Decision Context requirements (Section 18), which is Atlas Core's authority, not this specification's.

## 4. Governing References

- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative, superior to this specification.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.3.** Normative, superior to this specification; defines Decision Context as an accepted concept (§3.10).
- **OE-002 — Domain Object Model, Final.** Normative for Atlas Core; defines Case (§3.1) and the closed six-object Domain Object Set (§4), which excludes Case.
- **OE-004 — Domain Invariants, Final.** Normative for Atlas Core; INV-002 (single Case ownership), INV-004 (same-Case reference), and INV-005 (prior acceptance of referenced targets) apply to any Core Domain Object a Decision Context's own material involves.
- **Atlas Core Architecture Doctrine, Final.** Normative for Atlas Core's own investigation, decision, and amendment method; governs how any future cross-Case question would have to be resolved (§8, forcing functions and reopening).
- **The Case-Context reconciliation investigation and adopted implementation designs** (`Core-Loop-Case-Context-Reconciliation-Investigation.md` and the committed Observation/Decision/Outcome Case-Context Implementation Designs). **Non-normative** — each explicitly disclaims Doctrine status in its own text. Cited here only as adopted engineering precedent establishing that a Case has no closure mechanism and is designed to persist across multiple engagements, not as a source of Core ontology.
- **The Decision Context / Case Mapping Investigation** (this conversation's own prior turn). **Non-normative** — a product-side architectural investigation, cited as the basis for this specification's accepted premise (Section 6), not as an independent authority in its own right.

## 5. Definitions

Only concepts not already defined by APP-000 or APP-001 are defined here.

**Enclosing Case.** The single Atlas Core Case (OE-002 §3.1) within which every Core Domain Object a Decision Context's material involves must belong, per DCINV-003. This is a product-layer relationship, not an instance of OE-002's own "belongs to a Case" relation: OE-002 §3 defines that relation only for Domain Objects, and a Decision Context, per DC-R-004, is not one. A Decision Context's own relationship to its Enclosing Case is this specification's statement of which Case's Domain Objects its material may draw from, not a claim of Domain Object Case membership.

**Investment Decision.** As used throughout this specification, denotes the Decision defined by APP-000 §5 — no term distinct from APP-000's own Decision is introduced or intended. APP-001 §4 already declined to adopt "Investment Decision" as a separate concept, on the grounds that APP-000's Decision is already scoped to "a course of action regarding capital"; this specification's use of the longer phrase is a stylistic convenience only, carrying no independent meaning.

**Commitment.** The event by which the Investor's Investor Judgment resolves a Decision Context's one prospective Investment Decision into an actual, recorded Decision, per APP-000 §5's own definition of Decision. Commitment is a closure event of a Decision Context (Section 11); its content beyond that role is governed entirely by APP-000 and, at the Core layer, by OE-002 §5.5 — this definition adds nothing further to either.

**Abandonment.** The event by which the Investor explicitly closes a Decision Context without Commitment. Abandonment is a legitimate closure (Section 12), not a failure state and not an implicit or inferred condition.

**Dormancy.** The state of an open Decision Context that is not currently receiving Attention. Dormancy is not a distinct lifecycle state (Section 9); it is the ordinary condition of any open Decision Context the Investor is not, at a given moment, engaged with.

**Historical Record.** The permanent, inspectable state a Decision Context occupies after closure, by either Commitment or Abandonment (Section 13).

**Objective Lineage.** A descriptive, product-layer-only relationship one Decision Context MAY carry toward another Decision Context that shares a thematically related origin (Section 16, Section 17). Objective Lineage is not a Core relationship, confers no reference eligibility, and creates no merge, supersession, or reopening of either context's own closed identity.

## 6. Architectural Position

**DC-R-001.** A Decision Context SHALL be subordinate to APP-000 and APP-001, per APP-000 §2 and §9; it SHALL NOT contradict either or redefine any term either defines.

**DC-R-002.** A Decision Context SHALL be a product-level sub-boundary that exists within exactly one Core Case; it SHALL NOT be treated as identical to a Case.

**DC-R-003.** This specification SHALL NOT redefine Case (OE-002 §3.1) or any of the six Core Domain Objects (OE-002 §4); it treats Core ontology as given and unmodified.

**DC-R-004.** A Decision Context SHALL NOT itself become a Core Domain Object and SHALL NOT be, or be treated as, reference-eligible within Atlas Core — no Core Domain Object may hold a typed reference to a Decision Context, consistent with Case's own exclusion from the closed Domain Object Set (OE-002 §4) and the Decision Context / Case Mapping Investigation's finding that Decision Context requires no new Core ontology.

**DC-R-005.** A Decision Context SHALL NOT be treated as a time-bounded interaction session, a UI workspace, or an implementation runtime object; APP-001 §4 already rejects Session as a first-class product concept, and this specification does not reintroduce it under any name.

## 7. Core Properties

**DC-R-006.** A Decision Context SHALL be owned by the Investor, for the same reason a Decision is Investor-owned (APP-000 §5; APP-001 §3.10).

**DC-R-007.** A Decision Context SHALL scope exactly one objective.

**DC-R-008.** A Decision Context SHALL be directed at exactly one prospective Investment Decision throughout its open lifetime.

**DC-R-009.** A Decision Context SHALL exist within exactly one enclosing Case for its entire lifetime.

**DC-R-010.** A Decision Context SHALL begin open and MAY remain open without a time limit and without continuous Attention.

**DC-R-011.** A Decision Context SHALL close only through Commitment or Abandonment (Sections 11, 12); no other event SHALL close it.

**DC-R-012.** A closed Decision Context SHALL persist permanently as a Historical Record (Section 13); closure SHALL NOT destroy or dissolve it.

**DC-R-013.** An Investor MAY hold multiple Decision Contexts open concurrently (Section 15).

**DC-R-014.** A Decision Context SHALL NOT own Attention or Learning; both remain Investor-owned and independent of any single Decision Context, per APP-001 §3.7 and §3.6.

**DC-R-015.** A Decision Context SHALL NOT own Evidence exclusively; it draws upon, and MAY originate, Evidence that MAY also be relevant to another Decision Context (Section 14).

**DC-R-016.** Every Core Domain Object a Decision Context's material involves SHALL belong to the same Case as every other Core Domain Object that material semantically references, per OE-004 INV-002 and INV-004; a Decision Context SHALL NOT be used in a manner that would require a Core Domain Object it involves to reference another Core Domain Object outside its enclosing Case.

## 8. Creation

**DC-R-017.** A Decision Context SHALL be created only upon an explicit, Investor-originated objective sufficient to direct exactly one prospective Investment Decision.

**DC-R-018.** A Decision Context SHALL NOT be created with zero objectives.

**DC-R-019.** A Decision Context SHALL NOT be created with more than one objective; where an Investor's stated intention resolves into more than one objective, Section 16 governs.

**DC-R-020.** A Decision Context SHALL be created only within, or together with, an identified enclosing Case; a Decision Context SHALL NOT be created without an enclosing Case.

**DC-R-021.** A Decision Context SHALL NOT be created merely because the product was opened or a runtime interaction began; creation SHALL require an actual, Investor-originated objective, not an incidental consequence of engagement.

No screen or interaction flow is defined by this section, or by any other section of this specification.

## 9. Open Behavior

**DC-R-022.** An open Decision Context SHALL support the gathering of material relevant to its one objective, including material that precedes any explicit Investor Reasoning chain, per APP-001 §3.10's own Purpose.

**DC-R-023.** An open Decision Context SHALL support drawing upon Evidence belonging to its enclosing Case, per DC-R-016.

**DC-R-024.** An open Decision Context SHALL support the forming, revising, or withholding of explicit Investor Reasoning; Investor Reasoning is not required for a Decision Context to remain meaningfully open, per APP-001 §3.10's Boundary with Investor Reasoning.

**DC-R-025.** An open Decision Context SHALL support representing Uncertainty that has not been resolved, consistent with APP-000 §5's definition of Uncertainty as a permanent, legitimate condition, not a defect.

**DC-R-026.** An open Decision Context MAY remain dormant, per Section 5, without this constituting or requiring closure.

**DC-R-027.** An open Decision Context MAY receive or lose the Investor's current Attention at any time without any change to its own identity, objective, or lifecycle state.

**DC-R-028.** An open Decision Context SHALL remain open for as long as the Investor is not ready to commit or has not explicitly abandoned it; readiness to decide SHALL NOT be inferred or imposed by Atlas.

## 10. Objective Integrity

**DC-R-029.** A Decision Context's objective SHALL be identity-bearing: the objective is what a given Decision Context is a Decision Context of.

**DC-R-030.** A clarification of the objective's own expression that does not change what the objective concerns SHALL be treated as the same objective and SHALL NOT require a new Decision Context.

**DC-R-031.** A genuine change to the objective — one that concerns a materially different course of action or subject matter than the Decision Context was created to address — SHALL require a new Decision Context; it SHALL NOT be represented as a continuation of the original.

**DC-R-032.** A Decision Context SHALL NOT be silently mutated into carrying a different objective than the one it was created for.

The operative test for distinguishing a clarification (DC-R-030) from a genuine change (DC-R-031) is, consistent with the ambiguity test for Abandonment (DC-F-007), deferred to a future UX specification; this specification states only the governing principle and the fail-closed consequence (DC-F-005).

## 11. Decision Relationship

**DC-R-033.** A Decision Context SHALL be directed at exactly one prospective Investment Decision throughout its open lifetime.

**DC-R-034.** Commitment SHALL be a closure event of a Decision Context, per DC-R-011.

**DC-R-035.** The Decision produced by Commitment SHALL remain owned by the Investor, per APP-000 §5, §8.2, and PP-005.

**DC-R-036.** Atlas SHALL NOT create Commitment autonomously; no Decision Context SHALL close by Commitment absent an identifiable act of Investor Judgment, per APP-000 §4 and PP-003/PP-005.

**DC-R-037.** Closure by Commitment SHALL NOT erase, overwrite, or obscure the pre-decision material and Investor Reasoning the Decision Context held, per PP-006.

**DC-R-038.** This specification SHALL NOT redefine the canonical Core Decision Domain Object (OE-002 §5.5); the relationship between a committed Decision and its originating Decision Context is a product-layer fact this specification states, not a Core-layer redefinition.

## 12. Abandonment

**DC-R-039.** Abandonment SHALL be available to the Investor as an explicit act closing a Decision Context without Commitment.

**DC-R-040.** Abandonment SHALL be treated as a legitimate closure, not a failure state, defect, or incomplete outcome.

**DC-R-041.** All material and Investor Reasoning accumulated within an abandoned Decision Context SHALL be preserved and remain inspectable, per APP-001 §3.10's Lifetime clause.

**DC-R-042.** An abandoned Decision Context SHALL remain available to Learning, including learning about rejected opportunities, unresolved Uncertainty, and repeated patterns of not deciding, per APP-001 §3.6.

**DC-R-043.** Atlas SHALL NOT silently delete any material, Investor Reasoning, or record belonging to an abandoned Decision Context.

## 13. Historical Persistence

**DC-R-044.** A closed Decision Context — whether closed by Commitment or by Abandonment — SHALL persist permanently and SHALL remain distinguishable as its own historical record.

**DC-R-045.** A Decision Context closed by Commitment and a Decision Context closed by Abandonment SHALL remain separately identifiable as such; closure type SHALL NOT be lost or conflated.

**DC-R-046.** Closure SHALL NOT dissolve a Decision Context into the Decision it produced; the Decision Context SHALL remain its own historically identifiable record, distinct from, though related to, the Decision.

**DC-R-047.** A subsequent Decision Context SHALL NOT overwrite, supersede in place, or alter an earlier Decision Context's own historical record, regardless of any Objective Lineage between them (Section 16, Section 17).

## 14. Evidence Relationship

**DC-R-048.** Evidence SHALL NOT be exclusively owned by a Decision Context, per APP-001 §3.10.

**DC-R-049.** A Decision Context MAY gather, originate, draw upon, or relate Evidence relevant to its one objective.

**DC-R-050.** The same Evidence MAY support more than one Decision Context only where doing so complies with accepted Core same-Case rules (OE-004 INV-002, INV-004) — that is, only where every Decision Context involved shares the same enclosing Case.

**DC-R-051.** This specification SHALL NOT authorize a cross-Case reference of any kind; Evidence shared across Decision Contexts belonging to different Cases is not represented, permitted, or addressed by this document (Section 18).

**DC-R-052.** Real-world material MAY be relevant to more than one Decision Context regardless of Case boundaries; its Core-layer representation SHALL nonetheless comply with Case boundaries at all times, since relevance in the world does not itself alter Core ownership.

This specification does not define data-reference mechanics; how Evidence sharing is technically achieved is reserved for a future implementation design.

## 15. Concurrent Decision Contexts

**DC-R-053.** Multiple Decision Contexts MAY be open concurrently for one Investor.

**DC-R-054.** Each concurrently open Decision Context SHALL remain independently identifiable, with its own objective, material, and lifecycle state.

**DC-R-055.** Attention MAY move between concurrently open Decision Contexts at any time, per PP-001, without altering any Decision Context's own identity.

**DC-R-056.** Concurrency SHALL NOT merge the objectives or identities of two or more Decision Contexts; each remains exactly one objective, exactly one prospective Decision.

**DC-R-057.** Arbitration among concurrent Decision Contexts competing for the same capital is outside this specification's scope and is deferred to a future, Portfolio-level specification, per APP-000 §5 and APP-001 §3.10's own Cardinality clause.

## 16. Multi-Decision Objectives

This section resolves the open question the Decision Context Architecture Review identified — one objective producing several related Decisions — which the Decision Context / Case Mapping Investigation classified as a required APS decision, not a blocker.

**DC-R-058.** One Decision Context SHALL produce no more than one Investment Decision.

**DC-R-059.** Where a broader investment intention gives rise to more than one separate commitment, each separate commitment SHALL require its own Decision Context.

**DC-R-060.** Related Decision Contexts arising from one broader intention MAY share descriptive Objective Lineage at the product layer (Section 5); Objective Lineage carries no Core representation and does not affect DC-R-058 or DC-R-059.

**DC-R-061.** This specification SHALL NOT define a new Core relationship or a merge mechanism for related Decision Contexts.

**DC-R-062.** Relation types among Objective-Lineage-related Decision Contexts, their orchestration, and their presentation are deferred to a future subordinate specification (Section 25).

No conflict was found between this rule and any governing source. APP-001 §3.10's own "combined objective" clause addresses the reverse direction — several existing contexts merging into one newly formulated objective — and does not contradict this section's rule that one intention splitting into several commitments requires several Decision Contexts. Both rules share the same underlying principle: an objective, once genuinely distinct, requires its own Decision Context, in either direction.

## 17. Merge, Split, Supersession, and Reopening

**DC-R-063.** Decision Contexts SHALL NOT merge by mutating either context's own identity; no operation SHALL cause two Decision Contexts to become one Decision Context in place.

**DC-R-064.** Where several existing Decision Contexts contribute to a newly formulated, combined objective, that combined objective SHALL belong to a new Decision Context, per APP-001 §3.10; the contributing contexts SHALL remain separately closed and historically identifiable.

**DC-R-065.** Where one objective splits into genuinely separate objectives, each SHALL be represented by its own new Decision Context, per Section 16.

**DC-R-066.** Earlier Decision Contexts involved in a merge or split SHALL remain historically identifiable, per Section 13, regardless of any later Objective Lineage.

**DC-R-067.** An abandoned Decision Context SHALL NOT be reopened by changing its closed state; a similar later objective SHALL be represented by a new Decision Context.

**DC-R-068.** A new Decision Context arising from a similar later objective MAY be related to an earlier, closed Decision Context through Objective Lineage, as defined by a future subordinate specification; this specification does not itself define relation types.

## 18. Cross-Case Boundary

**DC-R-069.** A Decision Context SHALL exist within exactly one Core Case (DC-R-009); it SHALL NOT contain or semantically reference Core Domain Objects belonging to a different Case, per OE-004 INV-002 and INV-004.

**DC-R-070.** Where a prospective Investment Decision genuinely requires material belonging to more than one Core Case, this specification treats that requirement as an unresolved architectural limitation, not as a case this specification resolves.

**DC-R-071.** This specification SHALL NOT weaken, bypass, or reinterpret Core same-Case invariants to accommodate a cross-Case requirement.

**DC-R-072.** A demonstrated cross-Case requirement SHALL be escalated through a dedicated Core architecture investigation, per Architecture Doctrine §8's forcing-function and reopening standard; it SHALL NOT be resolved at the product-specification layer.

## 19. Atlas Responsibilities

**DC-R-073.** Atlas SHALL preserve all material and Investor Reasoning within an open or closed Decision Context, regardless of closure type, per PP-006.

**DC-R-074.** Atlas SHALL preserve objective integrity: it SHALL NOT represent a genuinely changed objective as a continuation of the same Decision Context, per PP-002 and Section 10.

**DC-R-075.** Atlas SHALL disclose Uncertainty represented within a Decision Context rather than concealing or resolving it by assertion, per PP-007.

**DC-R-076.** Atlas SHALL attribute the origin of any Atlas-originated content contributed to a Decision Context, per PP-008.

**DC-R-077.** Atlas SHALL NOT create Commitment autonomously and SHALL NOT present a Decision Context as though it were closing by Commitment absent an identifiable act of Investor Judgment, per PP-003 and PP-005.

**DC-R-078.** Atlas SHALL keep every closed Decision Context inspectable by the Investor at a later time, per PP-006 and Section 13.

## 20. Investor Responsibilities

**DC-R-079.** The Investor owns the objective of each Decision Context the Investor creates.

**DC-R-080.** The Investor owns the Decision produced by any Commitment, including a Decision reached with Atlas's assistance, per APP-000 §8.2.

**DC-R-081.** Abandonment, where chosen, SHALL be an explicit Investor act; it is not inferred, imposed, or assumed on the Investor's behalf.

**DC-R-082.** The Investor remains responsible for the exercise of Investor Judgment within any Decision Context, per APP-000 §5 and §8.2; Atlas's contribution, however extensive, does not transfer this responsibility.

**DC-R-083.** The Investor remains accountable for any Commitment reached, in the same manner APP-000 §8.2 states for any Decision.

## 21. Invariants

**DCINV-001 — Exactly One Objective.** A Decision Context SHALL have exactly one objective at every point in its lifetime.

**DCINV-002 — Exactly One Prospective Decision.** A Decision Context SHALL be directed at exactly one prospective Investment Decision at every point in its open lifetime. Once closed, per Section 13, the Decision Context's associated Decision — if Commitment occurred — is no longer prospective; this invariant does not apply to, and is not violated by, that closed state.

**DCINV-003 — Exactly One Enclosing Case.** A Decision Context SHALL belong to exactly one Core Case for its entire lifetime; this SHALL NOT change once established.

**DCINV-004 — No Cross-Case Core Reference.** No Core Domain Object a Decision Context involves SHALL semantically reference a Core Domain Object belonging to a different Case.

**DCINV-005 — Investor Ownership.** A Decision Context SHALL be owned by the Investor; ownership SHALL NOT transfer to Atlas or to any other party.

**DCINV-006 — No Autonomous Atlas Commitment.** Atlas SHALL NOT cause a Decision Context to close by Commitment absent an identifiable act of Investor Judgment.

**DCINV-007 — Permanent Preservation After Closure.** A closed Decision Context SHALL persist permanently and SHALL NOT be deleted, destroyed, or dissolved.

**DCINV-008 — Abandoned Material Retained.** Material and Investor Reasoning within an abandoned Decision Context SHALL be preserved identically to material within a committed one.

**DCINV-009 — Concurrent Identity Independence.** Each concurrently open Decision Context SHALL retain independent identity; concurrency SHALL NOT merge objectives or identities.

**DCINV-010 — No Silent Objective Mutation.** A Decision Context's objective SHALL NOT change without constituting the creation of a new Decision Context.

**DCINV-011 — Attention and Learning Non-Ownership.** A Decision Context SHALL NOT own Attention or Learning.

**DCINV-012 — Non-Exclusive Evidence Ownership.** A Decision Context SHALL NOT hold Evidence exclusively; other Decision Contexts within the same Case MAY draw upon the same Evidence.

**DCINV-013 — Closure Type Distinctness.** A Decision Context's closure type (Commitment or Abandonment) SHALL remain distinguishable for as long as the Decision Context's historical record exists.

**DCINV-014 — One Decision Per Context.** A Decision Context SHALL produce no more than one committed Decision.

**DCINV-015 — No New Core Relationship.** This specification, and any Decision Context governed by it, SHALL NOT introduce or rely upon a Core relationship, Core Domain Object, or Core invariant beyond those already adopted in OE-002 and OE-004. Unlike DCINV-001 through DCINV-014, this invariant constrains this specification's own scope and future evolution; it does not describe a runtime property of any individual Decision Context instance.

**DCINV-016 — Atomic Closure.** Closure by Commitment or Abandonment SHALL be atomic; no intermediate state SHALL exist between open and closed. This invariant governs the transition itself; it does not introduce any lifecycle state beyond the three stated in DC-AC-003.

## 22. Failure and Refusal Behavior

Atlas SHALL fail closed: where continuing would violate this specification, APP-000, APP-001, or a Core invariant, Atlas SHALL refuse or halt the action rather than proceed on an assumed or inferred basis. No UI error message is prescribed by this section or by this specification.

**DC-F-001 — No valid objective exists.** Atlas SHALL NOT create a Decision Context (DC-R-017, DC-R-018).

**DC-F-002 — More than one objective is supplied.** Atlas SHALL NOT create a single Decision Context spanning them; Section 16 governs — each genuinely distinct objective requires its own Decision Context.

**DC-F-003 — The enclosing Case is absent or ambiguous.** Atlas SHALL NOT create a Decision Context until exactly one enclosing Case is established (DC-R-020).

**DC-F-004 — Required material lies in more than one Case.** Atlas SHALL NOT represent the Decision Context as containing or referencing that cross-Case material; Section 18 governs, and the limitation SHALL be surfaced as unresolved rather than silently worked around.

**DC-F-005 — Atlas cannot determine whether the objective materially changed.** Atlas SHALL NOT treat continuation as settled; it SHALL treat the question as unresolved rather than assuming either continuation or a new objective, until the Investor's own act resolves it, per the same discipline DC-R-036 applies against assuming Investor Judgment on the Investor's behalf.

**DC-F-006 — Commitment cannot be attributed to the Investor.** Atlas SHALL NOT close the Decision Context by Commitment (DCINV-006).

**DC-F-007 — Abandonment is ambiguous.** Atlas SHALL NOT close the Decision Context; an ambiguous signal SHALL NOT be treated as an explicit Investor act (DC-R-081).

**DC-F-008 — Persistence cannot be guaranteed.** Atlas SHALL NOT proceed with an action that would leave a Decision Context's material, Investor Reasoning, or closure record unpreserved; the action SHALL be refused rather than completed with a known preservation gap (DCINV-007, DCINV-008).

## 23. Acceptance Criteria

**DC-AC-001 (Creation).** A Decision Context is never observed to exist with zero or more than one objective, and never without exactly one enclosing Case, per DCINV-001, DCINV-002, DCINV-003.

**DC-AC-002 (Objective Integrity).** Every recorded objective change is accompanied by the creation of a new Decision Context; no Decision Context's own recorded objective differs between two points in its lifetime, per DCINV-010.

**DC-AC-003 (Lifecycle).** Every Decision Context is observed in exactly one of: open, closed-by-Commitment, closed-by-Abandonment; no fourth state is observed, and no intermediate state between open and closed is ever observed, per DCINV-016.

**DC-AC-004 (Closure).** Every closure is attributable to either an identifiable act of Investor Judgment (Commitment) or an explicit Investor act (Abandonment); no closure lacks either attribution, per DCINV-006 and DC-R-081.

**DC-AC-005 (Persistence).** Every closed Decision Context remains retrievable, with its material and Investor Reasoning intact and its closure type distinguishable, indefinitely after closure, per DCINV-007, DCINV-008, DCINV-013.

**DC-AC-006 (Concurrency).** Two or more concurrently open Decision Contexts for one Investor are each independently retrievable with independent objectives and material; no concurrency-induced merge is observed, per DCINV-009.

**DC-AC-007 (Evidence Relationship).** Evidence referenced by more than one Decision Context is observed only where every referencing Decision Context shares the same enclosing Case; no cross-Case Evidence reference is observed, per DCINV-004 and DCINV-012.

**DC-AC-008 (Case Containment).** Every Decision Context's enclosing Case is fixed at creation and unchanged for its entire lifetime, per DCINV-003.

**DC-AC-009 (Human Ownership).** Every Decision Context and every Decision it produces is attributable to exactly one Investor as owner, per DCINV-005 and DC-R-080.

**DC-AC-010 (Abandonment).** Every abandoned Decision Context's material remains present and inspectable after abandonment, identical in completeness to a committed Decision Context's material, per DCINV-008.

**DC-AC-011 (Traceability).** Every requirement in Sections 6 through 20 is traceable, by citation, to at least one of: an APP-000 Product Principle, an APP-001 Decision Context provision, or a Core Case/same-Case requirement, per Section 24.

## 24. Traceability

This section distinguishes, for every requirement and invariant group, which basis is a normative Core requirement, which is adopted engineering precedent (non-normative), and which is a product decision made by this specification itself.

| Requirement / Invariant | APP-000 basis | APP-001 basis | Core basis | Core basis status |
|---|---|---|---|---|
| DC-R-001, DC-R-005 | §2 Document Authority; §9 Relationship to Subordinate Specifications | §1 Governing Authority and Method; §4 rejected Session | — | — |
| DC-R-002–004 | §1 (Core boundary respected) | §3.10 Core relationship | OE-002 §3.1 Case; §4 closed Domain Object Set | Normative (Core) |
| DC-R-017–021 | PP-002 (Thinking Before Action) | §3.10 Purpose, Responsibility | — | — |
| DC-R-006, DCINV-005 | §5 Decision; PP-005 | §3.10 Ownership | — | — |
| DC-R-007, DCINV-001 | — | §3.10 Responsibility | — | — |
| DC-R-008, DCINV-002, DCINV-014 | §5 Decision | §3.10 Purpose/Responsibility | OE-002 §5.5 Decision | Normative (Core) |
| DC-R-009, DCINV-003 | — | §3.10 Core relationship | OE-002 §3.1 Case; OE-004 INV-002 | Normative (Core) |
| DC-R-016, DC-R-051, DC-R-069, DCINV-004 | — | §3.10, §6 | OE-004 INV-004 | Normative (Core) |
| DC-R-010, DC-R-026 | §6.3 Uncertainty | §3.10 Lifetime | Case has no closure mechanism | Adopted engineering precedent, non-normative |
| DC-R-011, DC-R-012, DC-R-044 | PP-006 | §3.10 Lifetime | Domain Objects are permanent (OE-002 §3), by analogy only | APS product decision, informed by adopted Core pattern |
| DC-R-013, DC-R-053–056, DCINV-009 | PP-001 | §3.10 Cardinality | "continue an existing Case" model | Adopted engineering precedent, non-normative |
| DC-R-014, DCINV-011 | — | §3.6, §3.7 | — | — |
| DC-R-015, DC-R-048–052, DCINV-012 | PP-008 | §3.10 Responsibility (non-exclusive Evidence) | OE-004 INV-002, INV-004 | Normative (Core) for Case-boundedness of sharing; APS product decision for non-exclusivity itself |
| DC-R-022–028 | §6.3, §6.4, §6.5 | §3.10 Purpose; Boundary with Investor Reasoning | — | — |
| DC-R-029–032, DCINV-010 | PP-002 | §3.10 Changing an objective | — | — |
| DC-R-033–038, DCINV-006 | §5 Decision; PP-003, PP-005, PP-006 | §3.10 | OE-002 §5.5 Decision | Normative (Core), cited not redefined |
| DC-R-039–043, DCINV-008 | PP-006 | §3.10 Lifetime; §3.6 Learning | — | — |
| DC-R-044–047, DCINV-007, DCINV-013, DCINV-016 | PP-006 | §3.10 Lifetime | — | APS product decision |
| DC-R-057 | §5 Definitions (Portfolio deferral) | §3.10 Cardinality | — | — |
| DC-R-058–062, DCINV-014, DCINV-015 | PP-002 | §3.10 (gap identified by the Decision Context Architecture Review; resolved here) | — | APS product decision |
| DC-R-063–068 | PP-006 | §3.10 Changing an objective; §4 rejected Objective/Session | — | APS product decision |
| DC-R-069–072, DCINV-004 | §1 (Core boundary respected) | §3.10 Core relationship; §6 | OE-002 §3, §3.1; OE-004 INV-002, INV-004; Architecture Doctrine §8 | Normative (Core) |
| DC-R-073–078 | PP-001 through PP-009, as cited per line in Section 19 | §3.10 | — | — |
| DC-R-079–083 | §8.2 Responsibilities of the Investor | §3.10 Ownership | — | — |

## 25. Open Questions and Deferred Work

- **Cross-Case Decision Context requirements** (Section 18). Whether and how a prospective Decision genuinely requiring multi-Case material could ever be supported is not resolved here; it requires a dedicated Core architecture investigation, not a product-specification workaround.
- **Future relation types among contexts** (Objective Lineage, Sections 5, 16, 17). What relation types exist, how they are represented, and how they are surfaced is deferred to a future subordinate specification.
- **Capital-allocation arbitration across concurrent Decision Contexts** (Section 15). Deferred to a future, Portfolio-level specification, per APP-000 §5.
- **Presentation and interaction behavior.** Deferred entirely to future UX specifications; this document defines no screen, workflow, or interaction of any kind.
- **Relationship to the existing `docs/atlas_ux` governance track.** Remains undetermined, as already flagged by APP-001 §7 Observation 3 and §8 Risks; unresolved here. Any future APS work touching AI-originated content presentation SHALL NOT proceed until that relationship is resolved, per APP-001 §9 and §10.
- **Case selection or creation basis for a new Decision Context.** DC-R-020 requires an identified enclosing Case before a Decision Context may be created, but whether and how an Investor selects an existing Case or triggers creation of a new one is not addressed here and is deferred to a future specification.

Nothing necessary for Decision Context's own core behavior — creation, objective integrity, lifecycle, closure, persistence, concurrency, Evidence relationship, Case containment, or the Atlas/Investor responsibility split — has been deferred; each of these is fully specified in Sections 6 through 21 above.

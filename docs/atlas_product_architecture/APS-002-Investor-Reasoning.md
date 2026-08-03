# APS-002 — Investor Reasoning

**Status:** Draft, v0.1. This is the second Atlas Product Specification, subordinate to APP-000 — Atlas Product Doctrine, APP-001 — Atlas Product Concept Taxonomy, and APS-001 — Decision Context. It states the complete normative product behavior of Investor Reasoning. It does not describe screens, workflows, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique, and it does not redefine Core ontology.

---

## 1. Document Status and Authority

This specification is subordinate to APP-000 (Draft v0.4), APP-001 (Draft v0.3), and APS-001 (Draft v0.1), per APP-000 §2 and §9. It SHALL derive its behavior, priorities, and constraints from those three documents; it SHALL NOT contradict any of them; it SHALL NOT redefine a term any of them already defines.

Where this specification appears to conflict with APP-000, APP-001, APS-001, or any Atlas Core normative document (the Architecture Doctrine, OE-002 through OE-006), those documents govern and this specification is wrong and must be corrected.

While Draft, this specification is a candidate governing document for Investor Reasoning's product behavior, not yet binding on any implementation. Promotion to Final status requires deliberate review and adoption, consistent with the status discipline APP-000 §11.4 establishes across the Product Architecture.

## 2. Purpose

This specification states the complete normative product behavior of Investor Reasoning: what it is, how it begins, how it evolves and may be revised, how it may hold competing branches or unresolved contradiction, how it relates to Evidence, Investor Judgment, Decision Context, and Decision, how it closes, and what persists after closure. It operationalizes the Reasoning concept APP-000 §5 already defines and APP-001 §3.3 already accepts, under the disambiguated name APP-001 §7 Observation 1 recommends, into behavior sufficiently complete for a future UX specification, an implementation design, engineering, QA, and any AI agent working on Atlas to build from without inventing new product rules of their own. This specification is the direct product of the completed Investor Reasoning Investigation and adopts that investigation's findings as its accepted architecture; it does not reopen the questions that investigation already settled.

## 3. Scope

In scope: Investor Reasoning's identity, ownership, evolution, revision, branching, its relationship to Evidence, Investor Judgment, Decision Context, and Decision, its behavior under Commitment and Abandonment, historical persistence, contradictory reasoning, restart, merge, and split.

Out of scope, per APP-000 §1 and §10: screens, workflows, navigation, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique. Also out of scope: Evidence's own sourcing, reliability, and lifecycle (a future Evidence APS); Learning's own synthesis mechanics across many closed Investor Reasonings (a future Learning APS); Uncertainty's own general characterization beyond APP-000 §5 (a future Uncertainty APS, if any); Decision Context's own lifecycle, objective scoping, and Case containment (APS-001's own territory, not restated here except by citation); and any mechanism for copying or referencing Investor Reasoning content across a merge or split (Section 29).

## 4. Governing References

- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative, superior to this specification.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.3.** Normative, superior to this specification; organizes Reasoning as an accepted concept (§3.3) and flags the Core naming collision this specification's own terminology resolves informally (§7 Observation 1).
- **APS-001 — Decision Context, Draft v0.1.** Normative, superior to this specification; governs the enclosing boundary within which Investor Reasoning exists, and already defines "Investment Decision" as denoting APP-000's Decision (§5) — reused here without redefinition.
- **OE-002 — Domain Object Model, Final.** Normative for Atlas Core; defines Reasoning Trace (§5.3), the leading, unconfirmed hypothesis for a future Core mapping of Investor Reasoning's relational content.
- **OE-004 — Domain Invariants, Final.** Normative for Atlas Core; INV-002 (single Case ownership) and INV-004 (same-Case reference) bound any Core material Investor Reasoning cites, via its enclosing Decision Context's own Case.
- **Atlas Core Architecture Doctrine, Final.** Normative for Atlas Core's own investigation, decision, and amendment method; governs how any future Core-mapping question would have to be resolved (§8).
- **ADR-001 — The Nature of Reasoning, Final.** Normative for Atlas Core; establishes Core Reasoning as a standing capability, not an object — the basis for Investor Reasoning's non-correspondence to it.
- **ADR-002 — The Nature of Judgment, Final.** Normative for Atlas Core; establishes Core Judgment as a settled object produced by a completed Reasoning Act — the basis for Investor Judgment's, and by extension Investor Reasoning's, non-correspondence to it.
- **The Investor Reasoning Investigation** (this conversation's prior turn). **Non-normative** — a product-side architectural investigation, adopted here as this specification's accepted basis, not cited as independent authority in its own right.

## 5. Definitions

Only concepts not already defined by APP-000, APP-001, or APS-001 are defined here.

**Investor Reasoning.** As used throughout this specification, denotes the Reasoning defined by APP-000 §5, under the disambiguated name APP-001 §7 Observation 1 recommends for a future APP-000 amendment. No term distinct from APP-000's own Reasoning is introduced; this specification operationalizes that existing definition without redefining it.

**Premise.** An individual constituent link within Investor Reasoning's chain, connecting Evidence, a prior premise, or the residue of an act of Investor Judgment to what it supports.

**Branch.** A competing, unresolved line of Investor Reasoning existing concurrently with one or more other lines within one Investor Reasoning, per Section 11.

**Superseded Content.** Content within Investor Reasoning that a Restart, a Branch's resolution, or a Contradiction's resolution has ceased to advance, but which remains preserved and inspectable rather than removed.

**Contradiction.** A state in which two or more premises within Investor Reasoning cannot both be true as stated, per Section 19.

**Restart.** The Investor's explicit act of ceasing to advance Investor Reasoning's current active content while its enclosing Decision Context remains open. Restart does not close the Decision Context and does not create a new Investor Reasoning; see Section 20.

## 6. Architectural Position

**IR-R-001.** Investor Reasoning SHALL be subordinate to APP-000, APP-001, and APS-001; it SHALL NOT contradict any of the three or redefine a term any of them defines.

**IR-R-002.** Investor Reasoning SHALL NOT itself be a Core Domain Object and SHALL NOT be, or be treated as, reference-eligible within Atlas Core.

**IR-R-003.** This specification SHALL NOT redefine Core Reasoning, Reasoning Act, Reasoning Trace, or Judgment (ADR-001, ADR-002, OE-002 §5.3–§5.4); it treats Core ontology as given and unmodified.

**IR-R-004.** Investor Reasoning SHALL NOT be treated as identical to Core Reasoning, Core Reasoning Trace, or Investor Judgment.

**IR-R-005.** The correspondence between Investor Reasoning and Core Reasoning Trace SHALL NOT be asserted as settled; it remains an unconfirmed hypothesis pending a dedicated future Core compatibility investigation, per the Investor Reasoning Investigation.

**IR-R-006.** Investor Reasoning SHALL NOT be treated as a time-bounded interaction session, a UI workspace, or an implementation runtime object; no Session concept is introduced or reintroduced by this specification.

## 7. Core Properties

**IR-R-007.** Investor Reasoning SHALL be owned by the Investor.

**IR-R-008.** Investor Reasoning SHALL exist within exactly one Decision Context for its entire lifetime.

**IR-R-009.** Investor Reasoning SHALL be an evolving structure while its Decision Context remains open, and SHALL become a permanent record upon its Decision Context's closure, whether by Commitment or by Abandonment.

**IR-R-010.** Investor Reasoning SHALL NOT be, or be treated as, identical to Core Reasoning, Core Reasoning Trace, or Investor Judgment.

**IR-R-011.** Investor Reasoning SHALL incorporate Evidence by reference or citation; it SHALL NOT own Evidence.

**IR-R-012.** Investor Reasoning SHALL support exactly one prospective Investment Decision throughout its open lifetime.

**IR-R-013.** Investor Reasoning MAY internally contain competing Branches without thereby becoming more than one Investor Reasoning.

## 8. Creation

**IR-R-014.** Investor Reasoning SHALL begin only upon the first act connecting Evidence or a premise to another premise, or to the prospective Investment Decision, within an already-open Decision Context.

**IR-R-015.** Investor Reasoning SHALL NOT exist before its Decision Context exists; it SHALL NOT be created independent of a Decision Context.

**IR-R-016.** The existence of gathered Evidence, unresolved Uncertainty, or preliminary Investor Judgment within a Decision Context SHALL NOT, by itself, constitute the creation of Investor Reasoning; per APS-001 §3.10, this pre-Reasoning material is distinct from Investor Reasoning.

**IR-R-017.** Investor Reasoning SHALL NOT be created merely because a Decision Context was created; creation requires an actual connecting act.

## 9. Evolution

**IR-R-018.** Investor Reasoning MAY be extended by the Investor at any time while its Decision Context remains open.

**IR-R-019.** Investor Reasoning's evolution SHALL pause whenever its Decision Context is dormant and SHALL resume without requiring any separate act, per APS-001's own Dormancy definition; no separate paused state is introduced.

**IR-R-020.** Extension of Investor Reasoning SHALL NOT require prior resolution of any existing Branch or Contradiction.

**IR-R-021.** Investor Reasoning's evolution SHALL cease upon its Decision Context's closure, by either Commitment or Abandonment.

## 10. Revision

**IR-R-022.** The Investor MAY revise a premise within Investor Reasoning while its Decision Context remains open.

**IR-R-023.** A revision that alters a premise's content, but not the objective Investor Reasoning serves, SHALL be treated as evolution of the same Investor Reasoning, not the creation of a new one, consistent with APS-001 DC-R-030's treatment of objective clarification.

**IR-R-024.** Ordinary revision MAY replace a premise's prior content directly; this specification does not require continuous preservation of every intermediate edit. Restart (Section 20) and Branch or Contradiction resolution (Sections 11, 19) are the specific events at which superseded content SHALL be preserved as Superseded Content, per IR-R-027, IR-R-055, and IR-R-059.

## 11. Branches and Alternatives

**IR-R-025.** Investor Reasoning MAY contain more than one Branch concurrently, each representing a competing, unresolved line of consideration toward the same one prospective Investment Decision.

**IR-R-026.** A Branch SHALL NOT constitute a separate Investor Reasoning; all Branches within one Decision Context belong to that Decision Context's one Investor Reasoning, per IR-R-013.

**IR-R-027.** Resolution of competing Branches SHALL retain exactly the Branch or Branches the Investor's own Investor Judgment selects; every other Branch SHALL become Superseded Content, not be deleted.

**IR-R-028.** An accepted Branch SHALL remain part of Investor Reasoning's active content going forward; a discarded Branch SHALL remain preserved and inspectable as Superseded Content.

**IR-R-029.** Branch resolution SHALL NOT be required before Investor Reasoning may continue to evolve elsewhere within the same structure.

## 12. Relationship to Evidence

**IR-R-030.** Investor Reasoning SHALL reference or incorporate Evidence relevant to its premises; it SHALL NOT own Evidence, per APS-001 DC-R-015 and DC-R-048.

**IR-R-031.** The same Evidence MAY be referenced by more than one Investor Reasoning only where doing so complies with the same-Case rules already governing Decision Context (APS-001 DC-R-050); this specification does not loosen or extend that rule.

**IR-R-032.** Investor Reasoning SHALL NOT be considered to have incorporated Evidence it does not explicitly reference within a premise.

This specification does not define the mechanism of citation or reference between a premise and Evidence; that is implementation-level.

## 13. Relationship to Investor Judgment

**IR-R-033.** Investor Judgment SHALL contribute to Investor Reasoning by resolving a premise, a Branch, a Contradiction, or the eventual Commitment; it SHALL NOT be identical to Investor Reasoning.

**IR-R-034.** Investor Reasoning SHALL persist as a structure independent of any single act of Investor Judgment; no act of Investor Judgment, once exercised, SHALL itself persist as part of Investor Reasoning — only its settled contribution to a premise persists.

**IR-R-035.** Atlas SHALL NOT exercise Investor Judgment on the Investor's behalf within Investor Reasoning, per APP-000 PP-003.

## 14. Relationship to Decision Context

**IR-R-036.** Investor Reasoning SHALL be held within, not owned by, its Decision Context, per APS-001 §3.10 and IR-R-007.

**IR-R-037.** Investor Reasoning's enclosing Decision Context SHALL NOT change during Investor Reasoning's lifetime, consistent with APS-001 DCINV-003.

**IR-R-038.** Where a Decision Context's objective changes (per APS-001 DC-R-031), the Investor Reasoning developed under the original objective SHALL remain with the original, now-closing, Decision Context; a new Decision Context begins with no inherited Investor Reasoning of its own.

## 15. Relationship to Decision

**IR-R-039.** Investor Reasoning SHALL support exactly one prospective Investment Decision while its Decision Context remains open.

**IR-R-040.** Investor Reasoning SHALL NOT itself constitute Commitment; Commitment remains an act of Investor Judgment, per APS-001 DC-R-034 and DC-R-036.

**IR-R-041.** After Commitment, Investor Reasoning SHALL remain historical — associated with, but not merged into or dissolved into, the Decision it supported, mirroring APS-001 DC-R-046's treatment of Decision Context itself.

## 16. Commitment

**IR-R-042.** Upon Commitment, Investor Reasoning's evolution SHALL cease.

**IR-R-043.** Upon Commitment, Investor Reasoning SHALL become permanent and SHALL NOT be discarded, overwritten, or obscured thereafter, per APP-000 PP-006.

**IR-R-044.** Every Branch's disposition — accepted or Superseded — at the moment of Commitment SHALL remain distinguishable thereafter.

**IR-R-045.** Commitment SHALL NOT require Investor Reasoning to be free of Superseded Content or unresolved Contradiction; only the state of Investor Reasoning at Commitment is what PP-006 protects going forward.

## 17. Abandonment

**IR-R-046.** Upon Abandonment, Investor Reasoning's evolution SHALL cease.

**IR-R-047.** Upon Abandonment, Investor Reasoning SHALL be preserved and remain inspectable, identically in completeness to Investor Reasoning that reaches Commitment, per APS-001 DCINV-008.

**IR-R-048.** Abandonment SHALL NOT authorize silent deletion of any premise, Branch, or Superseded Content within Investor Reasoning.

## 18. Historical Persistence

**IR-R-049.** Closed Investor Reasoning — by either Commitment or Abandonment — SHALL persist permanently and SHALL remain distinguishable as its own historical record, per APS-001 Section 13's treatment of Decision Context.

**IR-R-050.** Investor Reasoning SHALL NOT silently disappear at any point in its lifetime, open or closed.

**IR-R-051.** A later Decision Context's Investor Reasoning SHALL NOT overwrite, supersede in place, or alter an earlier, closed Investor Reasoning's own historical record.

## 19. Contradictory Reasoning

**IR-R-052.** Investor Reasoning MAY contain an unresolved Contradiction while its Decision Context remains open; a Contradiction SHALL NOT, by itself, prevent Investor Reasoning from continuing to evolve.

**IR-R-053.** Atlas SHALL NOT silently resolve or conceal a Contradiction on the Investor's behalf.

**IR-R-054.** Where Atlas is aware of a Contradiction, Atlas SHALL make it available for the Investor's own examination, consistent with PP-007's disclosure requirement for Uncertainty.

**IR-R-055.** A Contradiction, once resolved by the Investor, SHALL follow the same preservation rule as Branch resolution (Section 11): the superseded side of the Contradiction SHALL become Superseded Content, not be deleted.

**IR-R-056.** Investor Reasoning SHALL NOT be required to be contradiction-free at Commitment; an unresolved Contradiction present at Commitment SHALL remain part of the permanent historical record, not be silently dropped.

## 20. Restart

**IR-R-057.** Restart SHALL NOT create a new Investor Reasoning; the Investor Reasoning that existed before Restart and the Investor Reasoning that continues after it SHALL be the same Investor Reasoning.

**IR-R-058.** Restart SHALL NOT create a new Decision Context; the enclosing Decision Context SHALL remain the same, per IR-R-037.

**IR-R-059.** Restart SHALL NOT replace Investor Reasoning in a manner that erases its prior content; the content the Investor ceases to advance at Restart SHALL become Superseded Content, preserved and inspectable, per IR-R-050.

**IR-R-060.** Restart SHALL be available to the Investor as an explicit act while a Decision Context remains open; it SHALL NOT close the Decision Context and SHALL NOT constitute Abandonment.

## 21. Merge

**IR-R-061.** Where several Decision Contexts contribute to a newly formulated, combined objective per APS-001 DC-R-064, the new Decision Context's Investor Reasoning SHALL begin with no inherited premises from the contributing Decision Contexts' own Investor Reasoning.

**IR-R-062.** The contributing Decision Contexts' own Investor Reasoning SHALL remain with their original, now-closed Decision Contexts, preserved per Section 18.

**IR-R-063.** This specification does not define a mechanism for copying, importing, or referencing prior Investor Reasoning content into a new Decision Context's Investor Reasoning; that is deferred to a future specification (Section 29).

**IR-R-064.** The same Evidence referenced by a contributing Decision Context's Investor Reasoning MAY be referenced again by the new Decision Context's Investor Reasoning, subject to IR-R-031's same-Case limitation; this is Evidence re-reference, not Investor Reasoning inheritance.

## 22. Split

**IR-R-065.** Where one objective splits into genuinely separate objectives per APS-001 DC-R-065, each resulting new Decision Context's Investor Reasoning SHALL begin with no inherited premises from the original Decision Context's Investor Reasoning.

**IR-R-066.** The original Decision Context's Investor Reasoning SHALL remain with the original, now-closed Decision Context, preserved per Section 18.

**IR-R-067.** The same Evidence referenced by the original Decision Context's Investor Reasoning MAY be referenced again by any resulting Decision Context's Investor Reasoning, subject to IR-R-031's same-Case limitation.

## 23. Atlas Responsibilities

**IR-R-068.** Atlas SHALL preserve Investor Reasoning's content — active and Superseded — for as long as its enclosing Decision Context exists, open or closed, per PP-006.

**IR-R-069.** Atlas SHALL NOT resolve a Branch, a Contradiction, or a premise on the Investor's behalf, per PP-003.

**IR-R-070.** Atlas SHALL disclose an unresolved Contradiction it is aware of, per PP-007.

**IR-R-071.** Atlas SHALL attribute the origin of any Atlas-originated content contributed to a premise, per PP-008.

**IR-R-072.** Atlas SHALL NOT cause Commitment by resolving Investor Reasoning autonomously, per PP-003, PP-005, and APS-001 DCINV-006.

**IR-R-073.** Atlas SHALL keep closed Investor Reasoning inspectable by the Investor at a later time, per PP-006.

## 24. Investor Responsibilities

**IR-R-074.** The Investor owns the content of Investor Reasoning created within any Decision Context the Investor owns.

**IR-R-075.** The Investor is responsible for resolving Branches and Contradictions the Investor chooses to resolve; Atlas's contribution does not transfer this responsibility, per APP-000 §8.2.

**IR-R-076.** Restart, where chosen, SHALL be an explicit Investor act.

**IR-R-077.** The Investor remains accountable for any Decision reached, including where Investor Reasoning contained unresolved Contradiction or Superseded Content at Commitment, in the same manner APP-000 §8.2 already states.

## 25. Invariants

**IRINV-001 — Single Enclosing Decision Context.** Investor Reasoning SHALL exist within exactly one Decision Context for its entire lifetime.

**IRINV-002 — Investor Ownership.** Investor Reasoning SHALL be owned by the Investor; ownership SHALL NOT transfer to Atlas or to any other party.

**IRINV-003 — Non-Identity with Core Reasoning, Reasoning Trace, and Investor Judgment.** Investor Reasoning SHALL NOT be treated as identical to any of the three.

**IRINV-004 — Non-Ownership of Evidence.** Investor Reasoning SHALL NOT own Evidence; it references or incorporates Evidence only, subject to the same-Case limitation.

**IRINV-005 — One Prospective Decision While Open.** Investor Reasoning SHALL support exactly one prospective Investment Decision throughout its open lifetime.

**IRINV-006 — Single Structure Despite Branches.** Investor Reasoning SHALL remain one Investor Reasoning regardless of how many Branches it concurrently contains.

**IRINV-007 — No Autonomous Atlas Resolution.** Atlas SHALL NOT resolve a Branch, Contradiction, or premise, or cause Commitment, on the Investor's behalf.

**IRINV-008 — Permanent Preservation After Closure.** Closed Investor Reasoning SHALL persist permanently and SHALL NOT be deleted, destroyed, or dissolved.

**IRINV-009 — Superseded Content Retained.** Content superseded by Restart, or by Branch or Contradiction resolution, SHALL be preserved and inspectable, not deleted.

**IRINV-010 — Contradiction Permitted While Open.** An unresolved Contradiction SHALL NOT, by itself, block Investor Reasoning's continued evolution or its Decision Context's Commitment.

**IRINV-011 — Restart Preserves Identity.** Restart SHALL NOT create a new Investor Reasoning or a new Decision Context.

**IRINV-012 — No Inheritance Across Merge or Split.** A new Decision Context arising from a merge or split SHALL NOT inherit premises from a contributing or originating Decision Context's Investor Reasoning.

**IRINV-013 — No New Core Relationship.** This specification, and any Investor Reasoning governed by it, SHALL NOT introduce or rely upon a Core relationship, Core Domain Object, or Core invariant beyond those already adopted in OE-002 and OE-004. Unlike IRINV-001 through IRINV-012, this invariant constrains this specification's own scope and future evolution; it does not describe a runtime property of any individual Investor Reasoning instance.

## 26. Failure and Refusal Behavior

Atlas SHALL fail closed: where continuing would violate this specification, APP-000, APP-001, APS-001, or a Core invariant, Atlas SHALL refuse or halt the action rather than proceed on an assumed or inferred basis. No UI error message is prescribed by this section or by this specification.

**IR-F-001 — No Decision Context exists.** Atlas SHALL NOT create or record Investor Reasoning without an already-open, identified Decision Context.

**IR-F-002 — No connecting act has occurred.** Atlas SHALL NOT treat gathered Evidence or preliminary Investor Judgment alone as Investor Reasoning (IR-R-016).

**IR-F-003 — Attempted creation of a second Investor Reasoning within one Decision Context.** Atlas SHALL NOT create a second, independent Investor Reasoning for a Decision Context that already has one; further content SHALL be represented as evolution, a Branch, or Superseded Content of the existing Investor Reasoning.

**IR-F-004 — Commitment cannot be attributed to the Investor.** Atlas SHALL NOT treat Investor Reasoning as closed by Commitment absent an identifiable act of Investor Judgment, per APS-001 DCINV-006.

**IR-F-005 — Attempted deletion of Superseded Content or closed Investor Reasoning.** Atlas SHALL refuse the action; deletion is not authorized by this specification.

**IR-F-006 — Attempted Evidence reference across Cases.** Atlas SHALL NOT represent Investor Reasoning as referencing Evidence belonging to a different Case than its enclosing Decision Context's own Case, per APS-001 DC-R-016 and DC-R-069, and IR-R-031.

**IR-F-007 — Ambiguous Restart versus Abandonment signal.** Atlas SHALL NOT treat an ambiguous signal as either Restart or Abandonment; it SHALL treat the question as unresolved until the Investor's own explicit act resolves it, mirroring APS-001 DC-F-007.

**IR-F-008 — Persistence of Investor Reasoning cannot be guaranteed.** Atlas SHALL refuse to proceed with an action that would leave Investor Reasoning's content unpreserved, mirroring APS-001 DC-F-008.

## 27. Acceptance Criteria

**IR-AC-001 (Creation).** Investor Reasoning is never observed to exist without an already-open, identified enclosing Decision Context, per IRINV-001.

**IR-AC-002 (Singularity).** No Decision Context is ever observed with more than one independent Investor Reasoning; all content is observed as one evolving structure, per IRINV-006.

**IR-AC-003 (Evolution).** Investor Reasoning's content changes only while its Decision Context is open; no change is observed after closure.

**IR-AC-004 (Ownership).** Every Investor Reasoning is attributable to exactly one Investor as owner, per IRINV-002.

**IR-AC-005 (Evidence).** Every Evidence reference within Investor Reasoning is observed to belong to the same Case as its enclosing Decision Context; no cross-Case reference is observed, per IRINV-004 and IR-R-031.

**IR-AC-006 (Branch Resolution).** Every resolved Branch is observed as either retained active content or Superseded Content; no resolved Branch is observed deleted, per IRINV-009.

**IR-AC-007 (Contradiction).** Every unresolved Contradiction present at Commitment or Abandonment is observed to remain part of the permanent record, per IRINV-010.

**IR-AC-008 (Restart).** Every Restart is observed to preserve the discarded content as Superseded Content within the same Investor Reasoning and the same Decision Context; no Restart is observed to produce a second Investor Reasoning or a new Decision Context, per IRINV-011.

**IR-AC-009 (Merge/Split).** Every Decision Context arising from a merge or split is observed to begin with no inherited premises; the contributing or originating Decision Context's own Investor Reasoning remains separately, historically identifiable, per IRINV-012.

**IR-AC-010 (Persistence).** Every closed Investor Reasoning remains retrievable and inspectable indefinitely after closure, per IRINV-008.

**IR-AC-011 (Traceability).** Every requirement in Sections 6 through 24 is traceable, by citation, to at least one of: an APP-000 Product Principle, an APP-001 or APS-001 provision, or a Core Case/same-Case requirement, per Section 28.

## 28. Traceability

This section distinguishes, for every requirement and invariant group, which basis is a normative Core requirement, which is adopted engineering precedent or an established APS-001 pattern, and which is a product decision made by this specification itself.

| Requirement / Invariant | APP-000 basis | APP-001 / APS-001 basis | Core basis | Core basis status |
|---|---|---|---|---|
| IR-R-001, IR-R-006 | §2 Document Authority; §9 | APP-001 §1; §4 rejected Session | — | — |
| IR-R-002, IR-R-004, IR-R-010, IRINV-003 (Reasoning Trace clause) | §1 (Core boundary respected) | APS-001 DC-R-004 (pattern) | OE-002 §4 closed Domain Object Set | Normative (Core) |
| IR-R-003 | §1 boundary paragraph | APP-001 §3.3, §3.5 Core relationship | ADR-001; ADR-002; OE-002 §5.3–§5.4 | Normative (Core), cited not redefined |
| IR-R-005 | — | APS-001 §18 (Cross-Case/unconfirmed-mapping pattern) | OE-002 §5.3 Reasoning Trace | Unconfirmed hypothesis, non-normative |
| IR-R-007, IRINV-002 | §5 Reasoning; §6.5 "a fact about the investor's own mind"; §8.2 | APP-001 §3.3 Ownership | — | — |
| IR-R-008, IRINV-001, IR-R-036–038 | — | APS-001 §3.10; DCINV-003 (pattern) | — | — |
| IR-R-009 | PP-006; §6.5 | APP-001 §3.3 Lifetime | — | — |
| IR-R-011, IR-R-030–032, IRINV-004 | PP-008 | APP-001 §3.4 "feeds into Reasoning"; APS-001 DC-R-015, DC-R-048, DC-R-050 | OE-004 INV-002, INV-004 | Normative (Core) for Case-boundedness only |
| IR-R-012, IR-R-039, IRINV-005 | §5 Reasoning "connects... to a Decision" | APS-001 DCINV-002 (pattern) | OE-002 §5.5 Decision | Normative (Core) |
| IR-R-013, IR-R-025–029, IRINV-006 | §6.3 Uncertainty; PP-007 | APP-001 §3.10 (gap identified by the Investor Reasoning Investigation; resolved here) | — | APS product decision |
| IR-R-014–017 | PP-002 | APS-001 §3.10 Purpose (pre-Reasoning material distinction) | — | — |
| IR-R-018–021 | §6.3, §6.5 | APS-001 DC-R-026 Dormancy (pattern) | — | — |
| IR-R-022–024 | PP-002 | APS-001 DC-R-030 (clarification-as-evolution pattern) | — | APS product decision |
| IR-R-033–035, IRINV-003 (Investor Judgment clause) | §5 Investor Judgment; PP-003 | APP-001 §3.5 | ADR-002 (non-correspondence) | Normative (Core), cited not redefined |
| IR-R-040–041 | §5 Decision | APS-001 DC-R-034, DC-R-036, DC-R-046 | OE-002 §5.5 Decision | Normative (Core), cited not redefined |
| IR-R-042–045 | PP-003, PP-005, PP-006 | APS-001 §11 Decision Relationship (pattern) | OE-002 §5.5 | Normative (Core), cited not redefined |
| IR-R-046–048 | PP-006 | APS-001 §12; DCINV-008 | — | — |
| IR-R-049–051, IRINV-008 | PP-006 | APS-001 §13 Historical Persistence (pattern) | — | APS product decision |
| IR-R-052–056, IRINV-010 | §6.3 Uncertainty; PP-007 | — (new resolution; no prior APP-001/APS-001 provision) | — | APS product decision |
| IR-R-057–060, IRINV-011 | PP-006 | APS-001 DC-R-030 (revision-as-evolution pattern) | — | APS product decision |
| IR-R-061–064, IR-R-065–067, IRINV-012 | PP-006 | APS-001 DC-R-064, DC-R-065 (§17 Merge, Split) | — | APS product decision |
| IR-R-068, IR-R-073 | PP-006 | APS-001 §19 pattern | — | — |
| IR-R-069, IRINV-007 | PP-003, PP-005 | APS-001 DCINV-006 (pattern) | — | — |
| IR-R-070 | PP-007 | APS-001 §19 pattern | — | — |
| IR-R-071 | PP-008 | APS-001 §19 pattern | — | — |
| IR-R-072 | PP-003, PP-005 | APS-001 DCINV-006 | — | — |
| IR-R-074–077 | §8.2 Responsibilities of the Investor | APS-001 §20 pattern | — | — |
| IRINV-009 | PP-006 | — (new resolution) | — | APS product decision |
| IRINV-013 | §1 boundary | APS-001 DCINV-015 (pattern) | OE-002; OE-004 (scope-only) | Normative (Core) scope constraint |

## 29. Open Questions

- **Mechanism for copying or referencing prior Investor Reasoning content across a merge or split** (IR-R-063). Not addressed here; deferred to a future specification.
- **How Atlas becomes aware of a Contradiction** (IR-R-054, IR-R-070). An algorithmic/AI-capability question, explicitly out of scope; deferred to a future specification concerned with AI-assisted reasoning support.
- **Evidence's own sourcing, reliability, and lifecycle.** Deferred to a future Evidence APS.
- **Learning's own synthesis mechanics across many closed Investor Reasonings.** Deferred to a future Learning APS.
- **Presentation and interaction behavior**, including how the Investor is prompted to distinguish ordinary revision, Restart, and Abandonment from one another. Deferred entirely to future UX specifications; IR-F-007's fail-closed treatment of ambiguity governs until such a UX design exists.
- **Relationship to the existing `docs/atlas_ux` governance track.** Remains undetermined, as already flagged by APP-001 §7 Observation 3 and carried forward by APS-001 §25; unresolved here.
- **The Investor Reasoning ↔ Core Reasoning Trace mapping** (IR-R-005). Remains an unconfirmed hypothesis; a dedicated Core compatibility investigation, following the same discipline already used for Decision Context and Case, is required before any future specification may assert a mapping.

Nothing necessary for Investor Reasoning's own core behavior — creation, evolution, revision, branching, its relationships to Evidence, Investor Judgment, Decision Context, and Decision, its behavior under Commitment and Abandonment, historical persistence, contradictory reasoning, restart, merge, and split — has been deferred; each of these is fully specified in Sections 6 through 25 above.

# APS-003 — Evidence

**Status:** Draft, v0.2. This is the third Atlas Product Specification, subordinate to APP-000 — Atlas Product Doctrine and APP-001 — Atlas Product Concept Taxonomy, and depending on APS-001 — Decision Context and APS-002 — Investor Reasoning. It states the complete normative product behavior of Evidence. It does not describe screens, workflows, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique, and it does not redefine Core ontology.

---

## 1. Document Status and Authority

This specification is subordinate to APP-000 (Draft v0.4) and APP-001 (Draft v0.3), and depends on APS-001 (Draft v0.1) and APS-002 (Draft v0.1), per APP-000 §2 and §9. It SHALL derive its behavior, priorities, and constraints from those four documents; it SHALL NOT contradict any of them; it SHALL NOT redefine a term any of them defines.

Where this specification appears to conflict with APP-000, APP-001, APS-001, APS-002, or any Atlas Core normative document, those documents govern and this specification is wrong and must be corrected.

While Draft, this specification is a candidate governing document for Evidence's product behavior, not yet binding on any implementation. Promotion to Final status requires deliberate review and adoption, consistent with the status discipline APP-000 §11.4 establishes across the Product Architecture.

## 2. Purpose

Evidence requires its own specification because APP-000 §5 defines it in a single paragraph, while APS-001 and APS-002 already presuppose behavior — non-exclusive sharing, cross-context citation, permanence — that neither document specifies in full. This specification closes that gap: it states Evidence's own identity, capture, equivalence, provenance, and reliability behavior, and the placement of evidential direction at the Evidence-to-Premise Citation rather than on Evidence itself, so that a future UX specification, an implementation design, engineering, QA, and any AI agent working on Atlas can build from it without inventing new Evidence product rules of their own. This specification is the direct product of three completed investigations (Evidence Pre-Design, Evidence Direction, and Evidence Identity/Source/Reliability) and adopts their findings as its accepted architecture; it does not reopen what those investigations already settled.

## 3. Scope

In scope: Evidence's identity, capture, equivalence, duplicate recognition, provenance and Source, Descriptive Reliability, the Evidence-to-Premise Citation, direction placement, relationships to Decision Context, Investor Reasoning, Investor Judgment, Decision, and Outcome, correction and supersession, contradictory and conflicting Evidence, obsolescence, the same-Case boundary, and ownership and attribution.

Out of scope, per APP-000 §1 and §10: screens, workflows, navigation, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique. Also out of scope: Decision Context's own lifecycle (APS-001's own territory); Investor Reasoning's own lifecycle, branching, and Superseded Content mechanics beyond what Evidence Citation requires (APS-002's own territory); a future Learning APS's own synthesis mechanics; a future Uncertainty APS's own general characterization; cross-Investor Evidence sharing (Section 31); formal correction or supersession relationship types (Section 20); and any assertion of a Core mapping for Evidence (Section 31).

## 4. Governing References

- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative, superior to this specification.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.3.** Normative, superior to this specification; organizes Evidence as an accepted concept (§3.4).
- **APS-001 — Decision Context, Draft v0.1.** Normative, superior to this specification; governs Decision Context's own non-exclusive relationship to Evidence (DC-R-015, DC-R-048–052).
- **APS-002 — Investor Reasoning, Draft v0.1.** Normative, superior to this specification; governs Investor Reasoning's own relationship to Evidence and defines Premise (IR-R-011, IR-R-030–032).
- **OE-002 — Domain Object Model, Final.** Normative for Atlas Core; defines Observation (§5.1) and Reasoning Trace (§5.3), neither of which this specification maps Evidence onto as settled fact.
- **OE-004 — Domain Invariants, Final.** Normative for Atlas Core; INV-002, INV-004, INV-005, INV-006 bound same-Case Citation behavior and inform, by analogy, this specification's own identity discipline.
- **Atlas Core Architecture Doctrine, Final.** Normative for Atlas Core's own method; governs how any future cross-Case or Core-mapping question would have to be resolved (§8).
- **ADR-001, ADR-002, ADR-003, Final.** Normative for Atlas Core; ADR-002's Identity Criterion and Equivalence Criterion for Judgment is the directly reused analogical template for this specification's own Evidence Equivalence (Section 11) — reused as pattern, not as binding authority over Evidence.
- **Hypothesis-Evidence-API-Lifecycle-Decision.md, Legacy-Core-Loop-Canonical-Reconciliation-Investigation.md, Reasoning-Trace-Implementation-Design.md.** Non-normative engineering precedent, each explicitly disclaiming Doctrine status in its own text. Cited only in Section 30's traceability table, where the completed investigations' own Core-compatibility findings are carried forward; never as a source of Core ontology.
- **The Evidence Pre-Design Investigation, the Evidence Direction Investigation, and the Evidence Identity, Source, and Reliability Investigation** (this conversation's prior turns). Non-normative — adopted here as this specification's own accepted architectural basis (the twenty-four accepted-architecture items governing this document), not cited as independent authority in their own right.

## 5. Definitions

Only Evidence-specific behavioral terms not already canonical are defined here.

**Capture.** The affirmative act of preserving qualifying informational content, together with its Provenance Category and Source state — specific or explicitly unknown — as a new, numerically distinct record.

**Evidence Instance.** The numerically distinct product record produced by one Capture, per EVINV-001.

**Content.** The informational substance an Evidence Instance preserves — what the Evidence Instance actually states or shows — independent of its wording, format, medium, or storage representation. Content is distinct from Source, Provenance Category, Citation direction, and any Citation Assessment. Two Evidence Instances share Content only where they preserve the same informational substance, not merely similar or related information.

**Evidence Equivalence.** The relation under which two numerically distinct Evidence Instances preserve the same Content and the same Source, per EVINV-002. Equivalence never merges the Evidence Instances it relates.

**Provenance Category.** One of exactly three mandatory classifications an Evidence Instance's content belongs to: Investor-originated, Atlas-originated, or externally originated.

**Source.** The specific originator of an Evidence Instance's content within its Provenance Category, where known.

**Unknown Source.** The explicit, disclosed state of an Evidence Instance whose specific Source is not known. Unknown Source is distinct from Provenance Category, which remains mandatory regardless.

**Descriptive Reliability.** A context-independent characterization of an Evidence Instance's trustworthiness, associated with its content and Source, distinct from any Investor's contextual weighting of it within a Citation.

**Citation Assessment.** The Investor's own contextual judgment applied to an Evidence Instance within one specific Citation; never a property of the Evidence Instance itself. This specification governs direction (Section 15) as a currently operative Citation Assessment facet. Weight, relevance, confidence, and materiality are named as facets Citation Assessment MAY eventually carry, per EV-R-052; this specification does not itself authorize or define their form.

**Evidence-to-Premise Citation.** The relationship, carried by APS-002's own Premise, through which exactly one Evidence Instance is incorporated into exactly one Premise, carrying that incorporation's own direction and any Citation Assessment.

## 6. Architectural Position

**EV-R-001.** Evidence SHALL be a Product Architecture concept, subordinate to APP-000 and APP-001, depending on APS-001 and APS-002; it SHALL NOT contradict any of the four or redefine a term any of them defines.

**EV-R-002.** Evidence SHALL NOT be treated as a canonical Core Domain Object; this specification does not define, and SHALL NOT be read to define, a Core Evidence ontology.

**EV-R-003.** Evidence SHALL be direction-neutral; no property of Evidence itself SHALL carry SUPPORTS, CHALLENGES, or an equivalent stance.

**EV-R-004.** Contextual evidential direction SHALL belong exclusively to the Evidence-to-Premise Citation.

**EV-R-005.** An Evidence Instance SHALL remain independently identifiable from every Citation, Premise, Investor Reasoning, or Decision Context that uses it.

## 7. Core Properties

**EV-R-006.** Every Capture SHALL produce exactly one numerically distinct Evidence Instance.

**EV-R-007.** An Evidence Instance SHALL persist permanently once captured.

**EV-R-008.** Evidence content, Source, and Provenance Category SHALL NOT be silently mutated.

**EV-R-009.** Two Evidence Instances MAY be equivalent without being identical; equivalence SHALL NOT merge their separate identities.

**EV-R-010.** An Evidence Instance MAY be cited by more than one Premise, Investor Reasoning, or Decision Context, subject to same-Case compliance (Section 23).

**EV-R-011.** An Evidence Instance SHALL NOT be exclusively owned by any single Premise, Investor Reasoning, or Decision Context that cites it.

**EV-R-012.** An Evidence Instance SHALL carry an explicit Provenance Category.

**EV-R-013.** An Evidence Instance's specific Source MAY be explicitly unknown.

**EV-R-014.** Every Citation of an Evidence Instance SHALL comply with the same-Case limitation governing the citing Investor Reasoning's own enclosing Decision Context.

**EV-R-015.** An Evidence Instance's own identity SHALL be independent of the identity of any Decision Context, Investor Reasoning, Decision, or Outcome that cites or relates to it.

## 8. Qualification as Evidence

**EV-R-016.** Content SHALL qualify as Evidence only where it preserves identifiable informational content.

**EV-R-017.** Content SHALL qualify as Evidence only where it is capable of bearing on a Premise, whether or not it has yet been cited.

**EV-R-018.** Content SHALL qualify as Evidence only where it carries a mandatory Provenance Category (Section 12).

**EV-R-019.** Content SHALL qualify as Evidence only where it carries either a specific Source or an explicit Unknown Source.

**EV-R-020.** Content SHALL preserve Descriptive Reliability where known at Capture; Descriptive Reliability's absence SHALL be explicit, not silent.

**EV-R-021.** Content SHALL remain direction-neutral to qualify as Evidence; content carrying an intrinsic stance does not qualify as Evidence until that stance is separated into a Citation.

**EV-R-022.** Evidence SHALL NOT be required to already be cited, true, accepted, conclusive, or currently relevant to qualify.

## 9. Capture

**EV-R-023.** Every Capture SHALL create one numerically distinct Evidence Instance, per EV-R-006.

**EV-R-024.** Capture SHALL NOT occur merely by an Investor or Atlas viewing or encountering information; Capture requires the affirmative act of preserving it as an Evidence Instance.

**EV-R-025.** Repeated Capture of content equivalent to an existing Evidence Instance MAY occur and SHALL produce its own, separate, equivalent Evidence Instance, not a reuse of the existing one.

**EV-R-026.** Capture SHALL NOT silently reuse an existing Evidence Instance's identity for materially different content.

**EV-R-027.** Capture SHALL preserve the Provenance Category and Source — specific or explicitly unknown — as understood at the moment of Capture; this record SHALL NOT later be altered by subsequent discoveries (Section 12).

**EV-R-115.** Citing or reusing an already-captured Evidence Instance SHALL NOT itself create a new Capture. Reproducing or displaying the same Content elsewhere SHALL NOT itself create a new Capture. A new Capture occurs only where qualifying informational content is affirmatively preserved as a new, numerically distinct Evidence Instance; where that newly preserved content is equivalent to an existing Evidence Instance, it produces its own, separate, equivalent Evidence Instance, per EV-R-025.

**EV-R-116.** Capture MAY be performed for Investor-originated content, for Atlas-originated content, or for externally originated content captured by either the Investor or Atlas, consistent with the Provenance Category the captured content carries.

## 10. Identity

**EV-R-028.** Two Evidence Instances SHALL be numerically identical if and only if they were produced by the same Capture.

**EV-R-029.** Numerical identity SHALL NOT be confused with Evidence Equivalence (Section 11); two numerically distinct Evidence Instances MAY be equivalent.

**EV-R-030.** Use of an Evidence Instance in different Premises, Branches, Investor Reasonings, or Decision Contexts SHALL NOT alter its identity.

**EV-R-031.** Use of an Evidence Instance by different citing contexts SHALL NOT create a new Evidence Instance.

**EV-R-032.** Correction of an Evidence Instance's content SHALL NOT mutate its identity; it SHALL instead produce a new, non-equivalent Evidence Instance (Section 20).

**EV-R-117.** Capture time SHALL be preserved as historical information. Capture time SHALL NOT determine numerical identity, per EV-R-028. Capture time SHALL NOT determine Evidence Equivalence, per EV-R-033.

## 11. Equivalence and Duplicate Recognition

**EV-R-033.** Two Evidence Instances SHALL be equivalent if and only if they preserve the same Content and the same Source.

**EV-R-034.** Two Evidence Instances carrying the same Content but different Sources SHALL NOT be equivalent.

**EV-R-035.** Equivalent Evidence Instances SHALL remain numerically distinct and independently identifiable.

**EV-R-036.** Recognition of equivalence SHALL NOT authorize merging equivalent Evidence Instances into one.

**EV-R-037.** Repeated Citation of one Evidence Instance SHALL NOT be treated as duplicate Capture.

**EV-R-038.** Independently captured Evidence Instances that corroborate one another through different Sources SHALL NOT be treated as duplicates of each other.

**EV-R-118.** Equivalent Evidence Instances SHALL NOT be presented as independent corroboration merely because they are numerically distinct.

## 12. Source and Provenance

**EV-R-039.** Every Evidence Instance SHALL carry a Provenance Category of exactly one of: Investor-originated, Atlas-originated, or externally originated.

**EV-R-040.** Provenance Category SHALL be mandatory without exception.

**EV-R-041.** Source SHALL be a distinct fact from Provenance Category; an Evidence Instance's Provenance Category SHALL be known even where its specific Source is not.

**EV-R-042.** Where a specific Source is not known at Capture, the Evidence Instance SHALL record Unknown Source explicitly.

**EV-R-043.** Unknown Source SHALL NOT be concealed, omitted, or replaced with a fabricated attribution.

**EV-R-044.** A Source becoming known after Capture SHALL NOT mutate the original Evidence Instance's own historical record; it SHALL be reflected in a new Evidence Instance or in still-open Investor Reasoning, per EV-R-008.

**EV-R-045.** A Source later disputed or shown incorrect SHALL NOT erase or alter the original Evidence Instance's historical record of what was understood at the time of Capture.

## 13. Descriptive Reliability

**EV-R-046.** Descriptive Reliability SHALL characterize an Evidence Instance's content and Source, independent of any specific Citation.

**EV-R-047.** Descriptive Reliability SHALL NOT be conflated with an Investor's contextual weighting of an Evidence Instance within a specific Citation (Section 14).

**EV-R-048.** Where Descriptive Reliability is unknown or uncertain, that state SHALL be explicit, not silent.

**EV-R-049.** Later information bearing on a Source's credibility SHALL NOT alter an existing Evidence Instance's own Descriptive Reliability record as it stood at Capture, whether silently or explicitly; that record SHALL remain preserved. Reliability-relevant information arising after Capture SHALL be represented through a new Evidence Instance, per EV-R-080, or through later Citation Assessment for still-open Investor Reasoning, per EV-R-092, never through in-place mutation of the original.

## 14. Evidence-to-Premise Citation

**EV-R-050.** A Citation SHALL relate exactly one Evidence Instance to exactly one Premise.

**EV-R-051.** A Citation SHALL carry the contextual evidential direction of that specific relation, per EV-R-004.

**EV-R-052.** A Citation MAY carry a Citation Assessment of contextual reliability weighting where a future specification authorizes it; this specification does not itself define that weighting's form.

**EV-R-053.** Citation meaning SHALL belong to the Investor Reasoning context in which it occurs.

**EV-R-054.** A Citation SHALL NOT mutate the Evidence Instance's own content, Source, Provenance Category, or Descriptive Reliability.

**EV-R-055.** An Evidence Instance MAY participate in zero, one, or many Citations.

**EV-R-056.** A Premise MAY cite one or many Evidence Instances.

## 15. Direction

**EV-R-057.** Evidence SHALL NOT carry an intrinsic SUPPORTS, CHALLENGES, or equivalent stance.

**EV-R-058.** Direction SHALL be scoped to exactly one Citation.

**EV-R-059.** The same Evidence Instance MAY support one Premise and challenge another through separate Citations.

**EV-R-060.** Opposite directions carried by separate Citations of the same Evidence Instance SHALL NOT constitute a contradiction within the Evidence Instance itself.

**EV-R-061.** A change in direction over time SHALL be represented as new or superseding Citation-level meaning; it SHALL NOT be represented as a mutation of the Evidence Instance.

## 16. Relationship to Decision Context

**EV-R-062.** A Decision Context MAY draw upon Evidence non-exclusively, per APS-001 DC-R-015 and DC-R-048–052.

**EV-R-063.** Evidence MAY exist before Investor Reasoning has formed within a Decision Context.

**EV-R-064.** Evidence SHALL NOT be owned by any Decision Context that draws upon it.

**EV-R-065.** Several Decision Contexts MAY cite equivalent or identical Evidence Instances, subject to same-Case compliance (Section 23).

**EV-R-066.** Closure of a Decision Context, by Commitment or Abandonment, SHALL NOT destroy any Evidence Instance it drew upon.

## 17. Relationship to Investor Reasoning

**EV-R-067.** Investor Reasoning SHALL incorporate Evidence only through Premise Citations, per APS-002 IR-R-011 and IR-R-030–032.

**EV-R-068.** Evidence SHALL NOT be treated as identical to Investor Reasoning.

**EV-R-069.** An Evidence Instance MAY remain uncited by any Premise.

**EV-R-070.** Contradictory Branches within one Investor Reasoning MAY cite the same Evidence Instance with different direction, per Section 15.

**EV-R-071.** Restart, revision, or Superseded Content within Investor Reasoning SHALL NOT erase a cited Evidence Instance or the historical Citation meaning it carried at the time.

## 18. Relationship to Investor Judgment

**EV-R-072.** Investor Judgment SHALL weigh Evidence and its Citation Assessments, per APP-000 §5.

**EV-R-073.** Evidence SHALL NOT own or replace Investor Judgment.

**EV-R-074.** An Investor's contextual assessment of reliability, relevance, direction, confidence, or materiality SHALL NOT be silently frozen into the Evidence Instance's own identity.

## 19. Relationship to Decision and Outcome

**EV-R-075.** Evidence SHALL NOT itself constitute a Decision.

**EV-R-076.** Evidence SHALL NOT itself constitute an Outcome.

**EV-R-077.** Evidence used before Commitment SHALL remain historically linked to the Decision it informed through the permanent Investor Reasoning that cited it.

**EV-R-078.** Information about a later Outcome MAY become a new Evidence Instance cited within a later, separate Decision Context, subject to the same-Case requirements of Section 23; this SHALL NOT authorize a cross-Case semantic reference and SHALL NOT retroactively alter any closed Investor Reasoning.

**EV-R-079.** Evidence discovered after Commitment SHALL NOT be inserted retroactively into a closed Investor Reasoning, per APS-002 IR-R-043.

## 20. Correction and Supersession

**EV-R-080.** Corrected informational content SHALL create a new, non-equivalent Evidence Instance, per EV-R-032.

**EV-R-081.** The original Evidence Instance SHALL persist unmutated.

**EV-R-082.** This specification does not define a mandatory correction or supersession relationship type between Evidence Instances.

**EV-R-083.** A future specification MAY define such a relationship without altering any Evidence Instance's own identity.

## 21. Contradictory and Conflicting Evidence

**EV-R-084.** Conflicting Evidence Instances MAY coexist.

**EV-R-085.** Atlas SHALL NOT suppress conflicting Evidence merely to present a single conclusion.

**EV-R-086.** Conflict between Evidence Instances SHALL remain inspectable.

**EV-R-087.** Conflict between two Evidence Instances SHALL be treated as distinct from contradictory direction assigned to one Evidence Instance across different Citations (Section 15).

**EV-R-088.** Resolution of conflicting Evidence SHALL belong to Investor Reasoning and Investor Judgment, not to Evidence itself.

## 22. Obsolescence, Relevance, and Credibility Change

**EV-R-089.** An Evidence Instance MAY become obsolete or irrelevant without being deleted.

**EV-R-090.** A change in assessed credibility SHALL NOT retroactively alter a prior Citation's own historical record.

**EV-R-091.** Historical Investor Reasoning SHALL preserve the Evidence Instance and the assessment applied to it as they stood at the time.

**EV-R-092.** The same Evidence Instance MAY later be cited with a different contextual assessment than it received previously.

## 23. Same-Case Boundary

**EV-R-093.** Every Citation of an Evidence Instance SHALL comply with the same-Case requirements governing the citing Investor Reasoning's enclosing Decision Context, per OE-004 INV-002 and INV-004.

**EV-R-094.** This specification SHALL NOT authorize a cross-Case semantic reference of any kind.

**EV-R-095.** Evidence reuse across Decision Contexts SHALL be limited to Decision Contexts sharing the same enclosing Case.

**EV-R-096.** A demonstrated requirement for cross-Case Evidence use SHALL be escalated through a dedicated Core architecture investigation; it SHALL NOT be resolved at the product-specification layer.

## 24. Ownership and Attribution

**EV-R-097.** An Evidence Instance itself SHALL NOT be owned by any Decision Context or Investor Reasoning that cites it.

**EV-R-098.** The Investor SHALL own the act of incorporating and weighing Evidence within Investor Reasoning.

**EV-R-099.** Provenance SHALL remain attributable at all times, per PP-008.

**EV-R-100.** Atlas SHALL distinguish Atlas-originated Evidence from Investor-originated and externally originated Evidence.

## 25. Atlas Responsibilities

**EV-R-101.** Atlas SHALL preserve the integrity of every Capture, recording content, Provenance Category, and Source — specific or explicitly unknown — as understood at that moment, per PP-006.

**EV-R-102.** Atlas SHALL disclose Provenance Category and Source, including Unknown Source, per PP-008.

**EV-R-103.** Atlas SHALL disclose uncertainty in Descriptive Reliability rather than presenting it as settled, per PP-007.

**EV-R-104.** Atlas MAY surface recognized Evidence Equivalence to the Investor but SHALL NOT merge equivalent Evidence Instances, per EV-R-036.

**EV-R-105.** Atlas SHALL preserve every Evidence Instance permanently, per EV-R-007.

**EV-R-106.** Atlas SHALL NOT present Evidence as carrying an intrinsic direction, per EV-R-057.

**EV-R-107.** Atlas SHALL NOT suppress or conceal conflicting Evidence, per EV-R-085.

**EV-R-108.** Atlas SHALL keep every Evidence Instance and its Citation history inspectable by the Investor at a later time, per PP-006.

**EV-R-109.** Atlas SHALL enforce same-Case compliance for every Citation, per Section 23.

**EV-R-110.** Atlas SHALL keep Descriptive Reliability and Citation Assessments distinct in every disclosure, per PP-007 and PP-008.

## 26. Investor Responsibilities

**EV-R-111.** The Investor is responsible for determining whether an Evidence Instance is relevant to the Investor's own Reasoning.

**EV-R-112.** The Investor remains responsible for the exercise of Investor Judgment in weighing Evidence, per APP-000 §8.2.

**EV-R-113.** The Investor is accountable for the direction and Citation Assessment applied through any Citation the Investor makes.

**EV-R-114.** The Investor is responsible for choosing to correct, restart, or abandon Reasoning that relied on an Evidence Instance later found mistaken, where the Investor elects to do so.

## 27. Invariants

**EVINV-001 — Numerical Identity Per Capture.** Two Evidence Instances SHALL be numerically identical if and only if produced by the same Capture.

**EVINV-002 — Equivalence Without Merger.** Evidence Equivalence SHALL NOT merge the identities of the Evidence Instances it relates.

**EVINV-003 — Direction Neutrality.** No Evidence Instance SHALL carry an intrinsic directional property.

**EVINV-004 — Citation-Level Direction.** Direction SHALL exist only within a Citation.

**EVINV-005 — Mandatory Provenance Category.** Every Evidence Instance SHALL carry exactly one Provenance Category.

**EVINV-006 — Explicit Unknown Source.** An unknown Source SHALL be recorded explicitly, never omitted or fabricated.

**EVINV-007 — No Mutation.** Evidence content, Source, Provenance Category, and Descriptive Reliability SHALL NOT be altered, silently or explicitly, once captured. A change SHALL be represented only through a new Evidence Instance or, for Descriptive Reliability specifically, through later Citation Assessment where applicable.

**EVINV-008 — Correction Creates New Evidence.** A correction SHALL produce a new, non-equivalent Evidence Instance, never an alteration of the original.

**EVINV-009 — Permanent Preservation.** Every Evidence Instance SHALL persist permanently once captured. It SHALL NOT be deleted. It SHALL NOT be destroyed.

**EVINV-010 — Non-Exclusive Citation.** An Evidence Instance SHALL NOT be exclusively owned by any single citing Premise, Investor Reasoning, or Decision Context.

**EVINV-011 — Same-Case Compliance.** Every Citation SHALL comply with the same-Case requirements of its Investor Reasoning's enclosing Decision Context.

**EVINV-012 — Distinctness from Premise and Investor Reasoning.** An Evidence Instance SHALL NOT be treated as identical to any Premise or Investor Reasoning that cites it.

**EVINV-013 — Contextual Assessment Non-Mutation.** A Citation's own Citation Assessment SHALL NOT alter the Evidence Instance it cites.

**EVINV-014 — Coexistence of Conflicting Evidence.** Conflicting Evidence Instances SHALL be permitted to coexist without forced resolution.

**EVINV-015 — Survival of Decision Context Closure.** Closure of a Decision Context SHALL NOT destroy any Evidence Instance it drew upon.

**EVINV-016 — Descriptive Reliability / Citation Assessment Separation.** Descriptive Reliability SHALL belong to the Evidence Instance; contextual assessment or weight SHALL belong to the Evidence-to-Premise Citation. Neither SHALL be represented as the other. A change in contextual assessment SHALL NOT mutate the Evidence Instance it cites.

**EVINV-017 — No New Core Relationship.** This specification SHALL NOT create, redefine, or imply a canonical Core Domain Object or Core reference relationship for Evidence or for the Evidence-to-Premise Citation.

## 28. Failure and Refusal Behavior

Atlas SHALL fail closed: where continuing would violate this specification, APP-000, APP-001, APS-001, APS-002, or a Core invariant, Atlas SHALL refuse or halt the action rather than proceed on an assumed or inferred basis. No error message is prescribed by this section or by this specification.

**EV-F-001 — Content cannot be distinguished sufficiently to Capture.** Atlas SHALL NOT create an Evidence Instance from content that cannot be identified as distinct informational content, per EV-R-016.

**EV-F-002 — Provenance Category is unknown.** Atlas SHALL NOT create an Evidence Instance without an identified Provenance Category, per EV-R-018 and EVINV-005.

**EV-F-003 — Specific Source is unknown.** Atlas SHALL NOT fabricate a Source; it SHALL record Unknown Source explicitly, per EV-R-042 and EVINV-006.

**EV-F-004 — Source is disputed.** Atlas SHALL NOT alter the original Evidence Instance's record; it SHALL preserve the dispute as a fact for Investor Reasoning to weigh, per EV-R-045.

**EV-F-005 — Duplicate equivalence is uncertain.** Atlas SHALL NOT assume equivalence where content or Source match is uncertain; it SHALL treat the Evidence Instances as non-equivalent until the Investor's own act establishes otherwise.

**EV-F-006 — An attempted correction would mutate existing Evidence.** Atlas SHALL refuse the mutation and SHALL instead create a new Evidence Instance, per EV-R-080 and EVINV-008.

**EV-F-007 — Direction is being assigned intrinsically to Evidence.** Atlas SHALL refuse the assignment; direction SHALL be recorded only at the Citation, per EVINV-003 and EVINV-004.

**EV-F-008 — A Citation would cross Case boundaries.** Atlas SHALL refuse the Citation, per EV-R-094 and EVINV-011.

**EV-F-009 — Preservation of prior Evidence cannot be guaranteed.** Atlas SHALL refuse to proceed with an action that would leave an Evidence Instance, or the historical Citation meaning and assessment already attached to it, unpreserved, per EVINV-009 and EV-R-091.

**EV-F-010 — Descriptive Reliability cannot be distinguished from a Citation's own direction.** Atlas SHALL NOT record an undifferentiated reliability value; it SHALL record Descriptive Reliability at the Evidence Instance or direction at the Citation, never conflated, per EV-R-047. This specification does not require Atlas to distinguish Descriptive Reliability from a contextual reliability weighting no future specification has yet authorized, per EV-R-052.

**EV-F-011 — Attempted merge of equivalent Evidence Instances.** Atlas SHALL refuse the merge; equivalent Evidence Instances SHALL remain separately identifiable, per EV-R-036 and EVINV-002.

## 29. Acceptance Criteria

**EV-AC-001 (Capture).** Every Evidence Instance is observed to originate from exactly one Capture, per EVINV-001.

**EV-AC-002 (Identity).** No two Evidence Instances produced by different Captures are ever observed to share numerical identity.

**EV-AC-003 (Equivalence).** Every pair of Evidence Instances marked equivalent is observed to share content and Source, and each remains separately retrievable, per EVINV-002.

**EV-AC-004 (Duplicate Recognition).** No two equivalent Evidence Instances are ever observed merged into one record.

**EV-AC-005 (Source and Provenance).** Every Evidence Instance carries exactly one Provenance Category; every Evidence Instance without a specific Source carries an explicit Unknown Source marker, never an absent or fabricated one.

**EV-AC-006 (Reliability Separation).** Descriptive Reliability and a Citation's own direction are never observed recorded as the same fact. This criterion does not extend to a contextual reliability weighting not yet authorized by any specification, per EV-R-052.

**EV-AC-007 (Direction Neutrality).** No Evidence Instance is ever observed carrying its own direction; every observed direction is attached to exactly one Citation.

**EV-AC-008 (Citation Direction).** Every Citation relates exactly one Evidence Instance to exactly one Premise and carries its own independent direction.

**EV-AC-009 (Correction).** Every correction is observed to produce a new, non-equivalent Evidence Instance; the original remains retrievable, unaltered.

**EV-AC-010 (Permanence).** Every Evidence Instance remains retrievable indefinitely after Capture, including after the closure of every Decision Context that cited it.

**EV-AC-011 (Reuse).** An Evidence Instance cited by more than one Premise, Investor Reasoning, or Decision Context is observed unchanged by each additional citation.

**EV-AC-012 (Contradictory Evidence).** Conflicting Evidence Instances are observed to coexist without either being suppressed or forcibly reconciled.

**EV-AC-013 (Same-Case Compliance).** No Citation is ever observed relating an Evidence Instance to a Premise whose Investor Reasoning's Decision Context lies in a different Case.

**EV-AC-014 (Historical Review).** Every closed Investor Reasoning's Citations remain inspectable with the Evidence Instance, direction, and assessment each carried at the time.

**EV-AC-015 (Traceability).** Every requirement in Sections 6 through 26 is traceable, by citation, to at least one of: an APP-000 Product Principle, an APP-001 Evidence provision, an APS-001 or APS-002 provision, or a Core same-Case requirement, per Section 30.

## 30. Traceability

This section distinguishes normative Core authority, adopted engineering precedent, and this specification's own product decisions for every requirement and invariant group.

| Requirement / Invariant | APP-000 basis | APP-001 / APS-001 / APS-002 basis | Core basis | Core basis status |
|---|---|---|---|---|
| EV-R-001, EV-R-002, EVINV-017 | §2, §9 | APP-001 §1 | OE-002 §4 (closed Domain Object Set excludes Evidence) | Normative (Core) |
| EV-R-003, EV-R-004, EVINV-003, EVINV-004 | — | (Evidence Direction Investigation, adopted) | — | APS product decision |
| EV-R-005, EV-R-015, EVINV-012 | — | APS-001 §3.10; APS-002 §5 Premise | — | — |
| EV-R-006, EV-R-023, EVINV-001 | — | (Evidence Identity Investigation, adopted) | ADR-002 Identity Criterion (Judgment) | Precedent pattern, not binding |
| EV-R-007, EVINV-009 | PP-006 | — | — | APS product decision |
| EV-R-008, EVINV-007 | PP-006 | Accepted Architecture item 6 | — | — |
| EV-R-009, EVINV-002 | — | (Evidence Identity Investigation, adopted) | ADR-002 Equivalence Criterion (Judgment) | Precedent pattern, not binding |
| EV-R-010, EV-R-011, EVINV-010 | — | APS-001 DC-R-015, DC-R-048–052; APS-002 IR-R-030–031 | — | — |
| EV-R-012, EV-R-039, EV-R-040, EVINV-005 | PP-008 | — | — | APS product decision |
| EV-R-013, EV-R-042, EVINV-006 | PP-008 | — | — | APS product decision |
| EV-R-014, EV-R-093, EVINV-011 | — | APS-001 DC-R-016, DC-R-069; APS-002 IRINV-004 | OE-004 INV-002, INV-004 | Normative (Core) |
| EV-R-016–022 | §5 Evidence | — | — | — |
| EV-R-024–027, EV-R-115, EV-R-116 | — | (Evidence Pre-Design / Identity Investigations, adopted) | — | APS product decision |
| EV-R-028–032, EV-R-117 | — | (Evidence Identity Investigation, adopted); ADR-002 Identity Criterion (pattern) | ADR-002 | Precedent pattern, not binding |
| EV-R-033–038, EV-R-118 | — | (Evidence Identity Investigation, adopted) | ADR-002 Equivalence Criterion (pattern) | Precedent pattern, not binding |
| EV-R-041, EV-R-043–045 | PP-008 | — | — | APS product decision |
| EV-R-046–049, EVINV-016 | §5 Evidence "degree of reliability" | — | — | APS product decision |
| EV-R-050–056 | — | APS-002 §5 Premise definition | — | — |
| EV-R-057–061, EVINV-003, EVINV-004 | — | (Evidence Direction Investigation, adopted) | Reasoning-Trace-Implementation-Design.md Test 2/Test 3 | Engineering precedent only |
| EV-R-062–066, EVINV-015 | — | APS-001 DC-R-015, DC-R-048–052, DC-R-012 | — | — |
| EV-R-067–071 | — | APS-002 IR-R-011, IR-R-025–029, IR-R-030–032, IR-R-057–059 | — | — |
| EV-R-072–074, EVINV-013 | §5 Investor Judgment | APS-002 §13 | — | — |
| EV-R-075–079 | §5 Decision | APS-001 §11; APS-002 §19 | OE-002 §5.5, §5.6 | Normative (Core), cited not redefined |
| EV-R-080–083, EVINV-008 | PP-006 | (Evidence Identity Investigation, adopted) | — | APS product decision |
| EV-R-084–088, EVINV-014 | PP-007 | (Evidence Pre-Design Investigation, adopted) | — | APS product decision |
| EV-R-089–092 | §6.3 Uncertainty | (Evidence Pre-Design Investigation, adopted) | — | — |
| EV-R-094–096 | §1 (Core boundary respected) | APS-001 §18 (pattern) | OE-004 INV-002, INV-004; Architecture Doctrine §8 | Normative (Core) |
| EV-R-097–100 | PP-008 | (Evidence Identity Investigation, adopted) | — | — |
| EV-R-101–110 | PP-001 through PP-009, as cited per line | APS-001 §19 pattern | — | — |
| EV-R-111–114 | §8.2 Responsibilities of the Investor | APS-001 §20 pattern | — | — |

## 31. Open Questions and Deferred Work

- **Product Evidence correspondence to Core Observation, Reasoning Trace, Knowledge, or any future Core Evidence primitive.** Explicitly unconfirmed, per Accepted Architecture item 23. Requires its own dedicated future Core compatibility investigation before any mapping may be asserted.
- **Cross-Investor Evidence sharing.** Undetermined, per Accepted Architecture item 24; recorded as deferred, not assumed.
- **Formal correction or supersession relationship types between Evidence Instances.** Not defined here (Section 20); a future specification may define one without altering Evidence identity.
- **Presentation and interaction behavior.** Deferred entirely to future UX specifications; this document defines no screen, workflow, or interaction of any kind.
- **Duplicate-recognition mechanisms** (how equivalence is actually detected in practice). Deferred — algorithmic and implementation-level, explicitly out of this specification's scope.
- **Scales or representations for Descriptive Reliability and Citation Assessments.** Not defined here; this specification deliberately avoids any scoring system.
- **Relationship to the existing `docs/atlas_ux` governance track.** Remains undetermined, as already flagged by APP-001 §7 Observation 3 and carried forward by APS-001 §25 and APS-002 §29; unresolved here.

Nothing necessary for Evidence's own core product behavior — capture, identity, equivalence, provenance, Descriptive Reliability, Citation and direction placement, relationships to Decision Context, Investor Reasoning, Investor Judgment, Decision, and Outcome, correction, contradictory Evidence, obsolescence, the same-Case boundary, and the Atlas/Investor responsibility split — has been deferred; each of these is fully specified in Sections 6 through 27 above.

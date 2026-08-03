# APS-004 — Learning

**Status:** Draft, v0.2. This is the fourth Atlas Product Specification, subordinate to APP-000 — Atlas Product Doctrine and APP-001 — Atlas Product Concept Taxonomy, and depending on APS-001 — Decision Context, APS-002 — Investor Reasoning, and APS-003 — Evidence. It states the complete normative product behavior of Learning. It does not describe screens, workflows, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique, and it does not redefine Core ontology.

---

## 1. Document Status and Authority

This specification is subordinate to APP-000 (Draft v0.4) and APP-001 (Draft v0.3), and depends on APS-001 (Draft v0.1), APS-002 (Draft v0.1), and APS-003 (Draft v0.2), per APP-000 §2 and §9. It SHALL derive its behavior, priorities, and constraints from those five documents; it SHALL NOT contradict any of them; it SHALL NOT redefine a term any of them defines.

Where this specification appears to conflict with APP-000, APP-001, APS-001, APS-002, APS-003, or any Atlas Core normative document (the Architecture Doctrine, OE-002 through OE-006), those documents govern and this specification is wrong and must be corrected.

While Draft, this specification is a candidate governing document for Learning's product behavior, not yet binding on any implementation. Promotion to Final status requires deliberate review and adoption, consistent with the status discipline APP-000 §11.4 establishes across the Product Architecture.

## 2. Purpose

Learning requires its own specification because APP-000 §5 and §6.6 define and motivate it in two short passages, while APP-001 §3.6 organizes it as an accepted concept without operationalizing its own behavior. This specification closes that gap: it states Learning's own nature as a standing capability distinct from its bounded Acts and their permanent Results, the closure preconditions its source material must satisfy, its cross-Context and cross-Case examination behavior, its relationship to Investor Reasoning, Evidence, Decision, Outcome, Pattern Recognition, and Decision Quality, and its revision, contradiction, and completion behavior — so that a future UX specification, an implementation design, engineering, QA, and any AI agent working on Atlas can build from it without inventing new Learning product rules of their own. This specification is the direct product of two completed investigations (the Learning Pre-Design Investigation and the Learning Cross-Case Examination Investigation) and adopts their findings as its accepted architecture; it does not reopen what those investigations already settled.

## 3. Scope

In scope: Learning's own nature as a Capability/Act/Result/History structure, source material and its closure preconditions, cross-Context and cross-Case examination, Learning Provenance, relationships to Investor Reasoning, Evidence, Decision, Outcome, Decision Quality, Pattern Recognition, and Review/Reflection, learning about Learning, revision and obsolescence, contradictory Learning Results, completion behavior, and the boundary against Restart/Merge/Split as separately named concepts.

Out of scope, per APP-000 §1 and §10: screens, workflows, navigation, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique. Also out of scope: Decision Context's own lifecycle (APS-001's own territory); Investor Reasoning's own lifecycle, branching, and Superseded Content mechanics (APS-002's own territory); Evidence's own capture, identity, and Citation mechanics (APS-003's own territory); Pattern Recognition's own internal detection behavior; Review and Reflection's own workflows; a formal, mandatory supersession relationship type between Learning Results (Section 24); and any assertion of a Core mapping for Learning (Section 34).

## 4. Governing References

- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative, superior to this specification.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.3.** Normative, superior to this specification; organizes Learning as an accepted concept (§3.6).
- **APS-001 — Decision Context, Draft v0.1.** Normative, superior to this specification; governs closure by Commitment or Abandonment (Sections 11–13), and Decision Context's own status as the unit Learning revisits (§3.10 Relationships).
- **APS-002 — Investor Reasoning, Draft v0.1.** Normative, superior to this specification; governs Investor Reasoning's own evolution, Branches, Superseded Content, Contradiction, and Restart, which a Learning Act may examine but SHALL NOT mutate.
- **APS-003 — Evidence, Draft v0.2.** Normative, superior to this specification; governs Evidence's own direction-neutrality (EVINV-003), Citation Assessment (Section 14), and the anti-corroboration rule (EV-R-118) a Learning Act SHALL respect when examining Evidence.
- **OE-002 — Domain Object Model, Final.** Normative for Atlas Core; defines Case (§3.1) and the closed six-object Domain Object Set (§4), which excludes Learning; defines Decision (§5.5) and Outcome (§5.6).
- **OE-004 — Domain Invariants, Final.** Normative for Atlas Core; INV-002 (single Case ownership) and INV-004 (same-Case reference) bound this specification's own cross-Case examination behavior (Section 15).
- **Atlas Core Architecture Doctrine, Final.** Normative for Atlas Core's own method; §3 states the burden-of-justification principle this specification applies against introducing new Core ontology for Learning; §8 governs how any future cross-Case requirement would have to be resolved.
- **ADR-001 — The Nature of Reasoning, Final.** Normative for Atlas Core; establishes the standing-capability/bounded-act distinction this specification's own Capability/Act/Result structure (Section 7 onward) reuses as pattern, not as binding authority over Learning.
- **ADR-002 — The Nature of Judgment, Final.** Normative for Atlas Core; its Identity Criterion/Equivalence Criterion two-tier pattern is reused as analogical template only, as APS-003 §11 already reused it for Evidence; not binding authority over Learning.
- **`Evaluation-to-Judgment-Reduction-Design.md`.** Non-normative engineering precedent, explicitly disclaiming Doctrine status in its own text. Its own L3 disposition ("Learning's own content is explicitly general and cross-Case-transferable, not a settled fact about one specific, identified, same-Case Domain Object... Learning remains outside Core") is the single most load-bearing precedent this specification relies on for Section 6's architectural position.
- **`Core-Loop-Case-Context-Reconciliation-Investigation.md`.** Non-normative engineering precedent. Cited only as adopted precedent establishing that a Case has no closure mechanism, informing this specification's treatment of Learning as independent of any single Decision Context's closure.
- **`PatternRecognitionATLAS005.md`.** Non-normative engineering precedent, read fresh in full. Its own domain distinction — "a Pattern is a recurring structure that exists in an investor's recorded history whether or not Atlas has found it; Pattern Recognition is the separate act that discovers a Pattern already there — it never creates one" — is directly reused in Section 21's relationship boundary; its read-only, cross-Decision `RecognizedPattern` model is cited as precedent that product-layer synthesis across many Decisions requires no new Core ontology.
- **`DecisionTimelineATLAS004.md`.** Non-normative engineering precedent, read fresh in full. Its own `DecisionTimelineQuery`, assembled by `DecisionRepository.list_all()` with no Case-scoping filter of its own, is cited as precedent that a product-layer read model may already synthesize material across an investor's full Decision history without a Core same-Case restriction being imposed on the read model itself, informing Section 15's cross-Case examination behavior.
- **`DecisionReviewATLAS003.md`.** Non-normative engineering precedent, read fresh in full. Its own legacy Core Loop `Learning` entity — captured once per Decision Review as a free-text, generalized, forward-looking statement ("the terminal node of the Core Loop"), explicitly not a canonical Core Domain Object (no `case_id`, absent from OE-002 §4's closed set) — is cited in Section 5 as a concrete, already-implemented precedent for the shape of a single, narrowly-scoped Learning Result, not as an authority defining this specification's own, broader standing Learning capability.
- **`DecisionCoachATLAS008.md`.** Non-normative engineering precedent, read fresh in full. Its own bounded, question-only engagement with a Decision Reflection is cited in Section 22 to state the boundary between Learning and Review/Reflection/Coach.
- **`ReflectionHistoryATLAS010.md`.** Non-normative engineering precedent, read fresh in full. Its own owner-scoped, read-only retrieval of preserved Reflection Responses is cited in Section 22 as further precedent for the boundary between Learning and Reflection.
- **The Learning Pre-Design Investigation** (this conversation's prior turn). Non-normative — adopted here as this specification's own accepted architectural basis for Learning's Capability/Act/Result/History nature (Section 7 onward), not cited as independent authority in its own right.
- **The Learning Cross-Case Examination Investigation** (this conversation's prior turn). Non-normative — adopted here as this specification's own accepted architectural basis for Section 15's cross-Case examination behavior, not cited as independent authority in its own right.

## 5. Definitions

Only concepts not already defined by APP-000, APP-001, APS-001, APS-002, or APS-003 are defined here.

**Learning Act.** One bounded exercise of Learning, examining specific Contributing Material at a point in time, per Section 9.

**Learning Result.** The permanent, generalized conclusion one completed Learning Act produces, applicable beyond the specific historical material it was drawn from, per Section 10.

**Learning History.** The accumulated body of an Investor's own permanent Learning Results over time; not itself a single Learning Result, and not identical to the raw Decision history it was drawn from, per Section 11.

**Contributing Material.** The closed Decision Contexts, their Investor Reasoning, Evidence, Decisions, Outcomes, Premises, Branches, Superseded Content, Contradictions, Restart history, and prior Learning Results a given Learning Act examines, per Section 12.

**Learning Provenance.** The record, carried by a Learning Result, of which Contributing Material was Materially Contributing to it, per Section 16.

**Materially Contributing.** Said of Contributing Material whose presence, absence, or interpreted meaning affected the generalized conclusion a Learning Result expresses, as distinct from Contributing Material merely examined, available, displayed, or accessed without such effect, per Section 16.

**Revised Learning Result.** A new Learning Result produced by a later Learning Act that reconsiders an earlier Result's own conclusion; does not alter or replace the earlier Result, which remains permanent, per Section 24.

**Cross-Case Examination.** A Learning Act's examination of Contributing Material originating from more than one Core Case, conducted entirely at the product layer without creating any Core semantic reference between the underlying Domain Objects, per Section 15.

A note on a distinct, non-colliding legacy term: the existing Core Loop implementation's own `Learning` entity (`DecisionReviewATLAS003.md` §5) is captured once per Decision Review as a free-text, generalized statement, and is not itself a canonical Core Domain Object. It is not a competing or conflicting ontology this specification must disambiguate against, in the manner APP-000 §5 disambiguates Investor Judgment from Core's own Judgment Domain Object; rather, it is a concrete, already-implemented precedent for the general shape a single Learning Result may take — narrowly scoped, in that implementation, to one Decision Review occasion. This specification's own Learning Result is not confined to that narrow scope, and this specification does not assert that the legacy entity and a Learning Result under this specification are the same thing; it cites the legacy entity only as informative precedent, per Section 4.

## 6. Architectural Position

**LR-R-001.** Learning SHALL be a Product Architecture capability, subordinate to APP-000 and APP-001, depending on APS-001, APS-002, and APS-003; it SHALL NOT contradict any of the five or redefine a term any of them defines.

**LR-R-002.** Learning SHALL be owned by the Investor.

**LR-R-003.** Learning SHALL NOT be treated as a canonical Core Domain Object; this specification does not define, and SHALL NOT be read to define, a Core Learning ontology.

**LR-R-004.** A Learning Result SHALL NOT acquire Core Case membership.

**LR-R-005.** Cross-Case examination SHALL remain product-layer only; it SHALL NOT create a Core semantic reference between Domain Objects belonging to different Cases.

**LR-R-006.** Atlas MAY support Learning; Atlas SHALL NOT own or exercise Learning on the Investor's behalf.

## 7. Core Properties

**LR-R-007.** There SHALL be exactly one standing Learning capability per Investor.

**LR-R-008.** An Investor MAY exercise Learning through many Learning Acts over time.

**LR-R-009.** A completed Learning Act SHALL produce no more than one new Learning Result.

**LR-R-010.** Many permanent Learning Results MAY exist per Investor.

**LR-R-011.** Learning History SHALL consist of the accumulated body of an Investor's own permanent Learning Results.

**LR-R-012.** Learning, every Learning Act, and every Learning Result SHALL be owned by the Investor.

**LR-R-013.** A Learning Result SHALL persist permanently once produced.

**LR-R-014.** A Learning Result SHALL NOT be mutated.

**LR-R-015.** A Learning Act MAY examine Contributing Material across multiple closed Decision Contexts and, subject to Section 15, across multiple Cases.

**LR-R-016.** A Learning Result SHALL carry Learning Provenance identifying the Contributing Material that is Materially Contributing to it.

**LR-R-017.** Learning SHALL NOT retroactively rewrite Decision Quality.

## 8. Learning Capability

**LR-R-018.** Learning SHALL be standing and continuously exercisable.

**LR-R-019.** Learning SHALL NOT be treated as completed or exhausted by any number of Learning Acts.

**LR-R-020.** Learning SHALL exist independent of any one Decision Context.

**LR-R-021.** Learning itself SHALL NOT be treated as a record; only a Learning Result is a record.

**LR-R-022.** Learning SHALL be exercised only through Learning Acts.

## 9. Learning Act

**LR-R-023.** A Learning Act SHALL be a bounded exercise of Learning.

**LR-R-024.** A Learning Act SHALL be owned by the Investor.

**LR-R-025.** A Learning Act MAY examine one or many closed Decision Contexts.

**LR-R-026.** A Learning Act MAY examine one or many prior Learning Results.

**LR-R-027.** A Learning Act MAY end without producing a Learning Result.

**LR-R-028.** A Learning Act SHALL produce no more than one new Learning Result upon completion.

**LR-R-029.** A Learning Act SHALL NOT mutate any Contributing Material it examines.

**LR-R-147.** A Learning Act SHALL begin only through an explicit, Investor-initiated act to examine Contributing Material for the purpose of deriving a generalized lesson.

**LR-R-148.** Casual browsing, passive viewing, automated surfacing, or the mere availability of history SHALL NOT, by itself, begin a Learning Act.

**LR-R-149.** A Learning Act SHALL be in exactly one of the following states at any point in its lifetime: active; completed-with-Result; completed-without-Result.

## 10. Learning Result

**LR-R-030.** A Learning Result SHALL be a generalized conclusion applicable beyond the one historical Decision Context it may have been drawn from.

**LR-R-031.** A Learning Result SHALL be produced by exactly one Learning Act.

**LR-R-032.** A Learning Result SHALL be owned by the Investor.

**LR-R-033.** A Learning Result SHALL persist permanently.

**LR-R-034.** A Learning Result SHALL remain independently identifiable from every other Learning Result.

**LR-R-035.** A Learning Result SHALL NOT be mutated.

**LR-R-036.** A Learning Result MAY later be challenged, contradicted, revised, or rendered obsolete without being deleted.

**LR-R-037.** A Learning Result SHALL NOT be treated as a Decision, a Recommendation, a Pattern, an Outcome, or a Core Judgment.

**LR-R-150.** Two Learning Results SHALL be numerically identical if and only if they were produced by the same Learning Act.

**LR-R-151.** Two distinct Learning Acts SHALL always produce numerically distinct Learning Results, even where the Results' generalized conclusions are identical.

**LR-R-152.** Two numerically distinct Learning Results SHALL be equivalent where they preserve the same generalized conclusion; equivalence SHALL NOT merge their separate numerical identity.

**LR-R-153.** Equivalent Learning Results SHALL remain independently identifiable and historically inspectable.

**LR-R-154.** Wording alone SHALL NOT determine equivalence: matching wording SHALL NOT establish equivalence where the preserved conclusion differs, and differing wording SHALL NOT preclude equivalence where the preserved conclusion is the same.

**LR-R-155.** A revised or corrected understanding SHALL produce a new Learning Result, numerically distinct from the earlier Result under LR-R-150; the earlier Result SHALL NOT be mutated, per LR-R-109 through LR-R-112.

## 11. Learning History

**LR-R-038.** Learning History SHALL consist of the accumulated body of an Investor's own permanent Learning Results.

**LR-R-039.** Learning History SHALL NOT be treated as identical to the raw Decision history it may draw upon.

**LR-R-040.** Learning History SHALL NOT itself be treated as a single Learning Result.

**LR-R-041.** Learning History MAY grow as further Learning Acts complete.

**LR-R-042.** Every Learning Result within Learning History SHALL remain independently identifiable.

**LR-R-043.** No Learning Result within Learning History SHALL be silently overwritten.

## 12. Source Material

**LR-R-044.** A Learning Act MAY examine, as Contributing Material: closed Decision Contexts; committed and abandoned contexts alike; Investor Reasoning; Evidence; historical Citations; Decisions; Outcomes; Premises; Branches; Superseded Content; Contradictions; Restart history; and prior Learning Results.

**LR-R-045.** Contributing Material SHALL remain governed by its own governing specification.

**LR-R-046.** Learning SHALL NOT own Contributing Material.

**LR-R-047.** Learning SHALL NOT mutate Contributing Material.

## 13. Closure Preconditions of Source Contexts

**LR-R-048.** A Decision Context SHALL be closed before its material may be treated as completed historical Learning input.

**LR-R-049.** A Decision Context closed by Commitment SHALL qualify as Contributing Material.

**LR-R-050.** A Decision Context closed by Abandonment SHALL qualify as Contributing Material.

**LR-R-051.** An open Decision Context SHALL NOT be treated as completed historical Learning input.

**LR-R-052.** This SHALL NOT prevent current, still-open Investor Reasoning from consulting prior Learning Results.

**LR-R-156.** The closure requirement of this section SHALL govern the historical eligibility of a Decision Context's own Investor Reasoning, Premises, Branches, Superseded Content, Contradictions, and Restart history; material from an open Decision Context SHALL NOT become completed historical Learning input merely because one such sub-component exists independently.

## 14. Cross-Context Examination

**LR-R-053.** A Learning Act MAY compare Contributing Material from many closed Decision Contexts.

**LR-R-054.** Source Decision Contexts SHALL remain independently identifiable after examination.

**LR-R-055.** Learning SHALL NOT merge or rewrite the identity of any source Decision Context.

**LR-R-056.** One Learning Result MAY be derived from many Decision Contexts.

**LR-R-057.** One Decision Context MAY contribute to many Learning Results.

## 15. Cross-Case Examination

This section resolves the question the Learning Cross-Case Examination Investigation examined — whether a Learning Act may examine material from more than one Core Case — and adopts that investigation's Model B verdict as accepted architecture.

**LR-R-058.** A Learning Act MAY examine Contributing Material originating from any number of Cases.

**LR-R-059.** Cross-Case examination SHALL NOT create a Core semantic reference between Domain Objects belonging to different Cases.

**LR-R-060.** Contributing Domain Objects SHALL remain within their own original Cases.

**LR-R-061.** A Learning Result SHALL have no Core Case membership.

**LR-R-062.** Learning Provenance MAY identify contributing Decision Contexts regardless of the Cases they belong to.

**LR-R-063.** This specification SHALL NOT weaken OE-004 INV-002 or INV-004.

**LR-R-064.** An attempted cross-Case Core reference in service of a Learning Act SHALL be refused.

## 16. Learning Provenance

**LR-R-065.** Every Learning Result SHALL preserve which Contributing Material is Materially Contributing to it.

**LR-R-066.** Learning Provenance SHALL distinguish source Decision Contexts from prior Learning Results it examined.

**LR-R-067.** Where provenance is incomplete but the Contributing Material that is Materially Contributing to the Learning Result remains identifiable, that incompleteness SHALL be disclosed, not silently omitted.

**LR-R-068.** Learning Provenance SHALL be understood as product-layer traceability; it SHALL NOT be treated as Core reference eligibility.

**LR-R-069.** A Learning Result derived from another Learning Result SHALL preserve provenance sufficient to reconstruct the chain back through each immediate predecessor.

**LR-R-157.** A Learning Result MAY be produced with disclosed provenance incompleteness only where the Materially Contributing Contributing Material remains identifiable, per LR-R-067; where Learning Provenance cannot identify the Materially Contributing Contributing Material sufficiently to preserve inspectability and reconstructability, Atlas SHALL refuse to produce the Learning Result, per LR-F-003.

**LR-R-158.** Learning Provenance SHALL identify Contributing Material that is Materially Contributing to the Learning Result's conclusion; Contributing Material examined but not Materially Contributing need not be included in Learning Provenance.

This specification does not define provenance's own storage or presentation mechanics; that is implementation-level.

## 17. Relationship to Investor Reasoning

**LR-R-070.** A Learning Act MAY examine preserved Investor Reasoning.

**LR-R-071.** Learning SHALL NOT mutate Investor Reasoning.

**LR-R-072.** A Learning Act MAY identify recurring strengths, weaknesses, assumptions, contradictions, or omissions within examined Investor Reasoning.

**LR-R-073.** A Learning Result MAY inform future Investor Reasoning only through the Investor's own Investor Judgment.

**LR-R-074.** Future Investor Reasoning's use of a Learning Result SHALL NOT alter that Learning Result.

**LR-R-159.** A Learning Result SHALL NOT be treated as Evidence, and SHALL NOT be directly connected into a Premise as an Evidence substitute or as an additional Premise-input category under APS-002 §5.

**LR-R-160.** Reasoning informed by a Learning Result remains, in every case, the Investor's own Investor Reasoning and Investor Judgment.

## 18. Relationship to Evidence

**LR-R-075.** A Learning Act MAY examine Evidence and historical Citation meaning.

**LR-R-076.** Evidence examined by a Learning Act SHALL remain direction-neutral, per APS-003 EVINV-003.

**LR-R-077.** Learning SHALL NOT change an Evidence Instance's identity, Source, Provenance Category, Descriptive Reliability, or any historical Citation Assessment.

**LR-R-078.** Equivalent Evidence examined across different Contributing Material SHALL NOT automatically be treated as independent corroboration, per APS-003 EV-R-118.

**LR-R-079.** Evidence quality MAY be a subject a Learning Result addresses without creating a new Evidence rule.

## 19. Relationship to Decision and Outcome

**LR-R-080.** A Learning Act MAY examine Decisions and Outcomes together with the Reasoning that produced them.

**LR-R-081.** Outcome examined by a Learning Act SHALL be treated as informative about the world, not as a verdict on past Decision Quality, per APP-000 §6.1.

**LR-R-082.** Learning SHALL NOT infer Decision Quality from a favorable or unfavorable Outcome alone.

**LR-R-083.** Later Outcome information MAY support a new Learning Act.

**LR-R-084.** A prior Learning Result SHALL remain historically fixed regardless of later Outcome information.

## 20. Decision Quality Boundary

**LR-R-085.** Learning SHALL NOT retroactively re-score Decision Quality.

**LR-R-086.** Learning SHALL NOT characterize general Decision Quality through aggregate Outcome performance.

**LR-R-087.** A cross-Case Learning Act SHALL derive its conclusion from the Reasoning behind each contributing Decision, not from aggregate Outcome favorability alone.

**LR-R-088.** A favorable Outcome SHALL NOT retroactively validate Reasoning that was unsound at the time it was exercised.

**LR-R-089.** An unfavorable Outcome SHALL NOT retroactively invalidate Reasoning that was sound at the time it was exercised.

**LR-R-090.** A Learning Result MAY identify an improvement to future Reasoning without rewriting the historical record of any past Decision's own Quality.

## 21. Relationship to Pattern Recognition

**LR-R-091.** Pattern Recognition SHALL be understood as the discovery of recurring structure, distinct from Learning, per `PatternRecognitionATLAS005.md` §1's own domain distinction.

**LR-R-092.** Learning SHALL begin only where the Investor interprets material and derives a generalized conclusion.

**LR-R-093.** A structure Atlas discovers via Pattern Recognition SHALL be attributable as Atlas-originated input to any Learning Act it informs, per PP-008.

**LR-R-094.** The Investor SHALL be the one who exercises Learning; Atlas discovering a pattern SHALL NOT itself constitute an act of Learning.

**LR-R-095.** Learning MAY occur without any Pattern Recognition input.

**LR-R-096.** This specification does not define Pattern Recognition's own internal detection behavior.

## 22. Relationship to Review and Reflection

**LR-R-097.** A Decision Review MAY provide the occasion on which a Learning Act occurs.

**LR-R-098.** Decision Review SHALL NOT be treated as identical to Learning itself.

**LR-R-099.** Reflection MAY contribute material or prompt an Investor's own interpretation relevant to a Learning Act.

**LR-R-100.** Reflection content SHALL NOT be automatically treated as a Learning Result.

**LR-R-101.** This specification does not define Review or Reflection workflows.

## 23. Learning About Learning

**LR-R-102.** A Learning Act MAY examine one or more earlier Learning Results.

**LR-R-103.** A later Learning Result SHALL NOT mutate any earlier Learning Result it examined.

**LR-R-104.** Contradictory Learning Results MAY coexist.

**LR-R-105.** A revised understanding of an earlier Learning Result SHALL produce a new Learning Result, per Section 24.

**LR-R-106.** A Learning Result's own provenance chain SHALL remain reconstructable, per Section 16.

**LR-R-107.** A Learning Result SHALL NOT depend, directly or indirectly, upon a Learning Result that does not yet exist.

**LR-R-108.** A Learning Result MAY depend only on Contributing Material already in existence at the time its own Learning Act occurs.

## 24. Revision, Correction, and Obsolescence

**LR-R-109.** Learning Results SHALL be immutable.

**LR-R-110.** A revised or corrected understanding SHALL create a new Learning Result.

**LR-R-111.** The original Learning Result SHALL remain permanent.

**LR-R-112.** No Learning Result SHALL be silently replaced.

**LR-R-113.** An obsolete Learning Result SHALL remain inspectable.

**LR-R-114.** This specification does not define a mandatory supersession relationship type between Learning Results.

**LR-R-115.** A future specification MAY define such a relationship without altering any Learning Result's own identity.

## 25. Contradictory Learning Results

**LR-R-116.** Contradictory Learning Results MAY coexist.

**LR-R-117.** A contradiction between Learning Results SHALL NOT cause either to be deleted.

**LR-R-118.** Atlas SHALL disclose a contradiction between Learning Results where both are materially relevant to the Investor's own present Reasoning.

**LR-R-119.** Resolution of a contradiction between Learning Results SHALL belong to a later Learning Act and the Investor's own Judgment.

**LR-R-120.** A Learning Result SHALL NOT be treated as superior to another solely because it is more recent.

## 26. Learning Act Completion

**LR-R-121.** A Learning Act MAY complete having produced one Learning Result or none.

**LR-R-122.** The absence of a Learning Result upon completion SHALL be a legitimate outcome.

**LR-R-123.** Atlas SHALL NOT fabricate a Learning Result merely to complete a Learning Act.

**LR-R-124.** A completed Learning Result SHALL satisfy the identity, provenance, and ownership requirements this specification states.

**LR-R-125.** Unresolved interpretation MAY remain without being forced into a Learning Result.

**LR-R-161.** The transition from active to completed-with-Result or to completed-without-Result SHALL be atomic; no intermediate state SHALL exist between them.

**LR-R-162.** A completed Learning Act SHALL NOT return to the active state; a revised understanding after completion SHALL require a new Learning Act, per LR-R-128.

## 27. Learning Restart, Merge, and Split

**LR-R-126.** This specification does not introduce a separate Learning Restart concept.

**LR-R-127.** In-progress reconsideration within a Learning Act that has not yet produced a Learning Result SHALL remain part of that same Learning Act.

**LR-R-128.** Once a Learning Result exists, a revised understanding SHALL require a new Learning Act and a new Learning Result, per Section 24.

**LR-R-129.** A merge of prior understanding SHALL be represented as a new Learning Act examining prior Learning Results, per Section 23.

**LR-R-130.** A split of prior understanding SHALL be represented as separate, later Learning Acts each producing its own Learning Result.

**LR-R-131.** Prior Learning Results SHALL remain unchanged by any merge or split.

## 28. Atlas Responsibilities

**LR-R-132.** Atlas SHALL preserve Contributing Material without mutation, per PP-006.

**LR-R-133.** Atlas SHALL preserve Learning Provenance, per PP-006 and PP-008.

**LR-R-134.** Atlas SHALL surface relevant historical material to support a Learning Act, per PP-001.

**LR-R-135.** Atlas SHALL distinguish Outcome from Decision Quality in any disclosure touching Learning, per PP-007 and PP-009.

**LR-R-136.** Atlas SHALL enforce the cross-Case limits stated in Section 15.

**LR-R-137.** Atlas SHALL attribute Pattern-Recognition-originated input to a Learning Act as Atlas-originated, per PP-008.

**LR-R-138.** Atlas SHALL disclose contradictory Learning Results where both are materially relevant, per PP-007.

**LR-R-139.** Atlas SHALL keep every Learning Result historically inspectable, per PP-006.

**LR-R-140.** Atlas SHALL NOT fabricate a Learning Result, per PP-007.

**LR-R-141.** Atlas SHALL NOT exercise Learning autonomously on the Investor's behalf, per PP-003.

## 29. Investor Responsibilities

**LR-R-142.** The Investor owns every Learning Act the Investor undertakes.

**LR-R-143.** The Investor owns every Learning Result produced from the Investor's own Learning Acts.

**LR-R-144.** The Investor is responsible for the interpretation a Learning Act produces.

**LR-R-145.** The Investor is responsible for accepting, rejecting, or revising a Learning Result, where the Investor elects to do so.

**LR-R-146.** The Investor remains accountable for any future use made of a Learning Result, in the same manner APP-000 §8.2 states for Decisions.

## 30. Invariants

**LRINV-001 — One Standing Capability Per Investor.** Learning SHALL exist as exactly one standing capability per Investor.

**LRINV-002 — Bounded Learning Acts.** Every Learning Act SHALL be a bounded exercise of Learning.

**LRINV-003 — At Most One Result Per Act.** A completed Learning Act SHALL produce no more than one new Learning Result.

**LRINV-004 — Investor Ownership.** Learning, every Learning Act, and every Learning Result SHALL be owned by the Investor.

**LRINV-005 — Permanent Results.** Every Learning Result SHALL persist permanently once produced.

**LRINV-006 — Immutable Results.** No Learning Result SHALL be mutated.

**LRINV-007 — Closed Source Contexts.** A Decision Context SHALL be closed before its material qualifies as Contributing Material.

**LRINV-008 — Commitment and Abandonment Both Qualify.** A Decision Context closed by either Commitment or Abandonment SHALL qualify as Contributing Material.

**LRINV-009 — Independent Preservation of Source Material.** Contributing Material SHALL remain governed and preserved by its own governing specification, independent of Learning.

**LRINV-010 — No Cross-Case Core Reference.** Cross-Case examination SHALL NOT create a Core semantic reference between Domain Objects belonging to different Cases.

**LRINV-011 — No Core Case Membership for Results.** A Learning Result SHALL have no Core Case membership.

**LRINV-012 — Provenance Preserved.** Every Learning Result SHALL preserve Learning Provenance identifying the Contributing Material that is Materially Contributing to it.

**LRINV-013 — No Retroactive Decision Quality Rescoring.** Learning SHALL NOT retroactively re-score Decision Quality.

**LRINV-014 — No Aggregate-Outcome Decision Quality Proxy.** Learning SHALL NOT characterize Decision Quality through aggregate Outcome favorability.

**LRINV-015 — Pattern Recognition Distinctness.** Pattern Recognition SHALL NOT be treated as identical to Learning.

**LRINV-016 — No Circular Result Dependency.** A Learning Result SHALL NOT depend, directly or indirectly, on a Learning Result that does not yet exist at the time of its own Learning Act.

**LRINV-017 — Coexistence of Contradictory Results.** Contradictory Learning Results SHALL be permitted to coexist without forced resolution.

**LRINV-018 — No Autonomous Atlas Learning.** Atlas SHALL NOT exercise Learning autonomously on the Investor's behalf.

**LRINV-019 — No New Core Relationship.** This specification SHALL NOT create, redefine, or imply a canonical Core Domain Object or Core reference relationship for Learning. Unlike every other invariant in this section, this invariant constrains this specification's own scope and future evolution; it does not describe a runtime property of any individual Learning Act or Learning Result instance.

**LRINV-020 — Numerical Identity.** Two Learning Results SHALL be numerically identical if and only if they were produced by the same Learning Act; distinct Learning Acts SHALL always produce numerically distinct Learning Results.

**LRINV-021 — Equivalence Without Merger.** Learning Result equivalence SHALL NOT merge numerical identity; equivalent Learning Results SHALL remain independently identifiable and historically inspectable.

**LRINV-022 — Learning Act Lifecycle Closure.** A Learning Act SHALL occupy exactly one of: active, completed-with-Result, completed-without-Result; the transition to either completed state SHALL be atomic and SHALL NOT reverse.

## 31. Failure and Refusal Behavior

Atlas SHALL fail closed: where continuing would violate this specification, APP-000, APP-001, APS-001, APS-002, APS-003, or a Core invariant, Atlas SHALL refuse or halt the action rather than proceed on an assumed or inferred basis. No UI error message is prescribed by this section or by this specification.

**LR-F-001 — No closed source material exists.** Atlas SHALL NOT treat a Learning Act as examining historical material where no closed Decision Context or prior Learning Result exists to examine.

**LR-F-002 — Source material includes an open Decision Context.** Atlas SHALL NOT treat an open Decision Context's material as completed historical Learning input, per LR-R-051.

**LR-F-003 — Provenance cannot identify the Materially Contributing Contributing Material.** Atlas SHALL refuse to produce a Learning Result whose Learning Provenance cannot identify, sufficiently to preserve inspectability and reconstructability, the Contributing Material that is Materially Contributing to it, per LR-R-157.

**LR-F-004 — A cross-Case Core reference would be created.** Atlas SHALL refuse the action, per LR-R-059 and LRINV-010.

**LR-F-005 — Outcome-only analysis is being used to characterize Decision Quality.** Atlas SHALL refuse to characterize Decision Quality on that basis, per LR-R-082 and LRINV-014.

**LR-F-006 — Atlas cannot distinguish Pattern-Recognition input from Investor interpretation.** Atlas SHALL disclose the ambiguity rather than attribute the resulting Learning Result to the Investor's own interpretation alone.

**LR-F-007 — A Result would overwrite an earlier Result.** Atlas SHALL refuse the overwrite and SHALL instead produce a new, separate Learning Result, per LR-R-112.

**LR-F-008 — Circular Learning-Result dependency is attempted.** Atlas SHALL refuse to create the dependency, per LR-R-107 and LRINV-016.

**LR-F-009 — Atlas cannot attribute the origin of contributing material.** Atlas SHALL disclose the unattributed state rather than silently omit it, per PP-008.

**LR-F-010 — Atlas cannot establish Investor ownership of the Result.** Atlas SHALL refuse to record the Learning Result.

**LR-F-011 — A system attempts to force a Result where interpretation remains unresolved.** Atlas SHALL refuse to fabricate a Learning Result and SHALL permit the Learning Act to complete without one, per LR-R-121 through LR-R-123.

**LR-F-012 — Atlas attempts to exercise Learning autonomously, or to record a Learning Result without a genuine act of Investor interpretation.** Atlas SHALL refuse to record the Learning Result; nominal Investor attribution, complete provenance, or formal correctness SHALL NOT cure the absence of genuine Investor interpretation, per LR-R-141 and LRINV-018.

## 32. Acceptance Criteria

**LR-AC-001 (Learning Capability).** Learning is observed to exist as exactly one standing, continuously exercisable capability per Investor, never exhausted by any number of Learning Acts, per LRINV-001.

**LR-AC-002 (Learning Act).** Every Learning Act is observed as a bounded occurrence, owned by the Investor, per LRINV-002 and LRINV-004.

**LR-AC-003 (Result Creation).** Every Learning Result is observed to originate from exactly one Learning Act, per LRINV-003.

**LR-AC-004 (No-Result Completion).** At least some Learning Acts are observed to complete without producing a Learning Result, with no fabricated Result substituted, per LR-R-121 through LR-R-123.

**LR-AC-005 (Ownership).** Every Learning Act and every Learning Result is attributable to exactly one Investor as owner, per LRINV-004.

**LR-AC-006 (Permanence).** Every Learning Result remains retrievable indefinitely after being produced, per LRINV-005.

**LR-AC-007 (Immutability).** No Learning Result is ever observed altered after its own production, per LRINV-006.

**LR-AC-008 (Committed and Abandoned Source Contexts).** Contributing Material is observed to include Decision Contexts closed by both Commitment and Abandonment, never an open Decision Context, per LRINV-007 and LRINV-008.

**LR-AC-009 (Cross-Context Examination).** A Learning Result is observed capable of citing more than one closed Decision Context as Contributing Material, each remaining independently identifiable, per LR-R-054 and LR-R-056.

**LR-AC-010 (Cross-Case Examination).** A Learning Result's Contributing Material is observed capable of spanning more than one Case, with no Core semantic reference ever created between Domain Objects in different Cases, per LRINV-010 and LRINV-011.

**LR-AC-011 (Provenance).** Every Learning Result's Learning Provenance is observed sufficient to identify and reconstruct the Contributing Material that is Materially Contributing to it, per LRINV-012.

**LR-AC-012 (Decision Quality Boundary).** No Learning Result is ever observed characterizing Decision Quality by aggregate Outcome favorability alone, per LRINV-013 and LRINV-014.

**LR-AC-013 (Pattern Recognition Boundary).** Every Learning Result attributing Atlas-discovered structure is observed to mark that structure as Atlas-originated input, distinct from the Investor's own interpretation, per LRINV-015 and LR-R-093.

**LR-AC-014 (Learning-about-Learning).** A Learning Result is observed capable of citing an earlier Learning Result as Contributing Material, with no circular dependency ever observed, per LRINV-016.

**LR-AC-015 (Contradiction).** Contradictory Learning Results are observed to coexist without either being deleted or forcibly reconciled, per LRINV-017.

**LR-AC-016 (Correction).** Every revision to an earlier Learning Result is observed to produce a new, separate Learning Result, with the original unaltered, per LR-R-109 through LR-R-112.

**LR-AC-017 (Historical Review).** Every closed Learning Act's Result, or its absence, remains inspectable together with the Contributing Material examined, per LR-R-113 and LR-R-139.

**LR-AC-018 (Failure/Refusal Behavior).** Every condition named in Section 31 is observed to produce the stated refusal or disclosure, never a silent proceed.

**LR-AC-019 (Traceability).** Every requirement in Sections 6 through 29 is traceable, by citation, to at least one of: an APP-000 Product Principle, an APP-001 Learning provision, an APS-001/002/003 provision, or a Core same-Case requirement, per Section 33.

**LR-AC-020 (Learning Act Lifecycle).** Every Learning Act is observed in exactly one of: active, completed-with-Result, completed-without-Result; no Learning Act is ever observed returning to active after completion, per LRINV-022.

**LR-AC-021 (Result Identity).** No two Learning Results produced by different Learning Acts are ever observed to share numerical identity, even where their generalized conclusions are identical, per LRINV-020.

**LR-AC-022 (Result Equivalence).** Every pair of Learning Results marked equivalent is observed to preserve the same generalized conclusion, and each remains separately retrievable and inspectable, per LRINV-021.

## 33. Traceability

This section distinguishes, for every requirement and invariant group, which basis is a normative Core requirement, which is adopted engineering precedent, and which is a product decision made by this specification itself.

| Requirement / Invariant | APP-000 basis | APP-001 / APS-001 / APS-002 / APS-003 basis | Core basis | Core basis status |
|---|---|---|---|---|
| LR-R-001–003, LRINV-019 | §2, §9 | APP-001 §1; §3.6 | OE-002 §4 (closed Domain Object Set excludes Learning) | Normative (Core) |
| LR-R-004, LR-R-005, LR-R-058–064, LRINV-010, LRINV-011 | — | (Learning Cross-Case Examination Investigation, adopted) | OE-004 INV-002, INV-004 | Normative (Core) for same-Case boundary; APS product decision for the examination permission itself |
| LR-R-006, LR-R-141, LRINV-018 | PP-003 | APS-001 DCINV-006 (pattern) | — | — |
| LR-R-007, LR-R-018–022, LRINV-001 | §5 Learning; §6.6 | APP-001 §3.6 Lifetime ("standing capacity... never itself completed or exhausted") | ADR-001 (standing-capability pattern) | Precedent pattern, not binding |
| LR-R-008, LR-R-023–029, LRINV-002 | §6.5 | (Learning Pre-Design Investigation, adopted — Capability/Act/Result/History structure) | ADR-001 (Reasoning/Reasoning Act pattern) | Precedent pattern, not binding |
| LR-R-009, LR-R-028, LR-R-030–037, LRINV-003, LRINV-005, LRINV-006 | PP-006 | (Learning Pre-Design Investigation, adopted) | `Evaluation-to-Judgment-Reduction-Design.md` L3 (Learning's own content is general and non-canonical) | Engineering precedent only |
| LR-R-010, LR-R-011, LR-R-038–043 | §6.6 "Learning as the Purpose of Memory" | APP-001 §3.6 Purpose | — | — |
| LR-R-012, LR-R-032, LRINV-004 | §5 Learning "The Investor's capacity"; §8.2 | APP-001 §3.6 Ownership | — | — |
| LR-R-013, LR-R-014, LR-R-033, LR-R-035 | PP-006 | (Learning Pre-Design Investigation, adopted) | — | APS product decision |
| LR-R-015, LR-R-025, LR-R-044, LR-R-053–057 | §6.6 "what was reasoned... together" | APP-001 §3.6 Relationships ("operates across multiple closed Decision Contexts") | — | — |
| LR-R-016, LR-R-065–069, LRINV-012 | PP-006, PP-008 | (Learning Cross-Case Examination Investigation, adopted) | — | APS product decision |
| LR-R-017, LR-R-085–090, LRINV-013, LRINV-014 | §6.1 Decision Quality Over Outcome; PP-009 | (Learning Cross-Case Examination Investigation, adopted) | — | APS product decision |
| LR-R-026, LR-R-102–108, LRINV-016 | §6.5 | (Learning Pre-Design Investigation, adopted) | OE-004 INV-005 (prior-acceptance pattern) | Precedent pattern, not binding |
| LR-R-027, LR-R-121–125 | PP-007 | (Learning Pre-Design Investigation, adopted) | — | APS product decision |
| LR-R-045–047 | PP-006 | APS-001 §3.10; APS-002 §5; APS-003 §5 (each governs its own material) | — | — |
| LR-R-048–052, LRINV-007, LRINV-008, LRINV-009 | §6.6 "learning requires that Reasoning be preserved" | APS-001 DC-R-011, DC-R-041, DC-R-042 | — | — |
| LR-R-070–074, LR-R-159, LR-R-160 | §5 Reasoning; §6.5; PP-003 | APS-002 §18 Historical Persistence; §17 Abandonment; §5 Premise (closed enumeration) | — | — |
| LR-R-075–079 | §5 Evidence | APS-003 EVINV-003, EV-R-118, EVINV-007 | — | — |
| LR-R-080–084 | §5 Decision, Outcome; §6.1 | APS-001 §11, §12; APP-001 §3.11 Outcome | OE-002 §5.5, §5.6 | Normative (Core), cited not redefined |
| LR-R-091–096, LRINV-015 | PP-008 | `PatternRecognitionATLAS005.md` §1 (Pattern/Pattern Recognition distinction, adopted as precedent) | — | Engineering precedent only |
| LR-R-097–101 | — | `DecisionReviewATLAS003.md`, `DecisionCoachATLAS008.md`, `ReflectionHistoryATLAS010.md` (adopted as precedent for the boundary) | — | Engineering precedent only |
| LR-R-109–115 | PP-006 | (Learning Pre-Design Investigation, adopted); APS-003 §20 Correction and Supersession (pattern) | — | APS product decision |
| LR-R-116–120, LRINV-017 | PP-007 | APS-002 §19 Contradictory Reasoning (pattern); APS-003 §21 Contradictory Evidence (pattern) | — | APS product decision |
| LR-R-126–131 | PP-006 | APS-001 §17 Merge, Split (pattern); APS-002 §20 Restart (pattern) | — | APS product decision |
| LR-R-132–140 | PP-001 through PP-009, as cited per line | APS-001 §19; APS-002 §23; APS-003 §25 pattern | — | — |
| LR-R-142–146 | §8.2 Responsibilities of the Investor | APS-001 §20; APS-002 §24; APS-003 §26 pattern | — | — |
| LR-R-147–149, LRINV-022 | PP-002 | APS-001 DC-R-017 (pattern); APS-002 IR-R-014 (pattern) | — | — |
| LR-R-150–155, LRINV-020, LRINV-021 | — | (this correction, adopted) | ADR-002 Identity Criterion/Equivalence Criterion (pattern); APS-003 EV-R-028, EV-R-033 (pattern) | Precedent pattern, not binding |
| LR-R-156 | PP-006 | APS-001 §13 (pattern) | — | APS product decision |
| LR-R-157, LR-R-158 | PP-006, PP-008 | (this correction, adopted) | — | APS product decision |
| LR-R-161, LR-R-162 | PP-006 | (this correction, adopted) | — | APS product decision |

## 34. Open Questions and Deferred Work

- **Product Learning correspondence to any future Core primitive.** Explicitly unconfirmed. `Evaluation-to-Judgment-Reduction-Design.md`'s own L3 disposition states Learning remains outside Core with no forcing function requiring otherwise; this specification does not reopen that finding and does not assert any Core mapping.
- **Relationship between this specification's standing Learning capability and the legacy Core Loop's per-Decision-Review `Learning` entity.** Cited in Section 5 as informative precedent only; this specification does not require, authorize, or assume any particular implementation mapping between the two.
- **Formal supersession relationship types between Learning Results.** Not defined here (Section 24); a future specification may define one without altering Learning Result identity.
- **Presentation and interaction behavior.** Deferred entirely to future UX specifications; this document defines no screen, workflow, or interaction of any kind.
- **Pattern Recognition's own internal detection behavior**, and any future strategy beyond what `PatternRecognitionATLAS005.md` already implements. Deferred — algorithmic and implementation-level, out of this specification's scope.
- **Review and Reflection workflows.** Not defined here (Section 22); deferred to any future specification addressing those capabilities directly.
- **How Atlas becomes aware of a contradiction between Learning Results** (LR-R-118, LR-R-138). An algorithmic/AI-capability question, explicitly out of scope, mirroring APS-002's own identical deferral (§29) for Investor Reasoning Contradiction.
- **Relationship to the existing `docs/atlas_ux` governance track.** Remains undetermined, as already flagged by APP-001 §7 Observation 3 and carried forward by APS-001 §25, APS-002 §29, and APS-003 §31; unresolved here.

Nothing necessary for Learning's own core product behavior — its Capability/Act/Result/History nature, source material and closure preconditions, cross-Context and cross-Case examination, Learning Provenance, its relationships to Investor Reasoning, Evidence, Decision, Outcome, Decision Quality, Pattern Recognition, and Review/Reflection, learning about Learning, revision and obsolescence, contradictory Learning Results, completion behavior, and the Atlas/Investor responsibility split — has been deferred; each of these is fully specified in Sections 6 through 29 above.

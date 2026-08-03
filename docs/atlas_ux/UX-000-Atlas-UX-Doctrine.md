# UX-000 — Atlas UX Doctrine

**Status:** Release Candidate, RC v1.0. Established on the basis of Draft v0.2, having completed drafting, Internal Consistency Review, Targeted Consistency Corrections, and Final Verification (Verdict A). This is the highest governing document within the Atlas UX Architecture and the governing UX doctrine baseline for the operational migration program. It establishes the authority, responsibility, and prohibitions that govern every future UX specification, screen, workspace, and component document. It does not itself describe any screen, page, navigation map, component, visual token, or implementation technique. Final status is not yet claimed.

**Governance Refresh Notice (Atlas UX Governance Resolution Sprint, 2026-08-03):** This is a later, additive clarification; it does not revise, replace, or reopen any content below, and it changes no doctrine rule, UX responsibility, prohibition, or Principle. Following the completed Atlas Product Architecture Reconciliation and the ATLAS UX CORRESPONDENCE INVESTIGATION (2026-08-03), which found this Doctrine's own Product-layer authority citations (Section 1, Section 4) stale, and its Section 26 Open Question concerning Investment Case and Portfolio resolved by intervening work, three narrow factual updates are made: (1) Section 1's and Section 4's citations of `APP-001 — Draft v0.3` and `APS-001 through APS-005` are updated to `APP-001 — Draft v0.4` and `APS-001 through APS-009`, reflecting the completed APP-001 v0.4 amendment and the APS-006 (Portfolio), APS-007 (Watchlist), APS-008 (Daily Brief), and APS-009 (Discover) additions; (2) UXD-R-071 item 5 is annotated, not rewritten, to record that Investment Case and Portfolio now possess the future Product Architecture treatment it anticipated; (3) Section 26's corresponding Open Question is marked RESOLVED, with its original text preserved in quotation, and a further bullet records that Watchlist, Daily Brief, and Discover — none named in this Doctrine's own original Open Questions, since none existed when this Doctrine reached Release Candidate — now possess formal Product Architecture treatment as well. No doctrine rule is altered by this notice.

---

## 1. Document Status and Authority

This Doctrine is subordinate to the Atlas Core Architecture Doctrine, OE-002, and OE-004 (Normative Core); to APP-000 (Draft v0.4), APP-001 (Draft v0.4), and APS-001 through APS-009 (Normative Product). It SHALL derive its authority, responsibility, and prohibitions from those documents; it SHALL NOT contradict any of them; it SHALL NOT redefine a term any of them already defines. *(Citation refreshed per the Atlas UX Governance Resolution Sprint, 2026-08-03: prior text read "APP-001 (Draft v0.3), and APS-001 through APS-005," reflecting APP-001's status before its own v0.4 amendment and before APS-006 through APS-009 existed.)*

This Doctrine formally supersedes `UX-000-The-Atlas-Experience.md` as the governing UX doctrine, per Section 23. The superseded document remains part of the historical record; it is not erased, and its Correction Notice is not rewritten.

As Release Candidate, this Doctrine is the governing UX doctrine baseline for the operational migration program, having completed the full drafting and review cycle described above; it is not yet binding on any implementation and not yet Final. Promotion to Final status requires deliberate review and adoption, consistent with the status discipline APP-000 §11.4 establishes across the Atlas documentation corpus, which this Doctrine adopts as its own status discipline. Future substantive amendment of this Doctrine remains governed exclusively by UXD-R-007 and UXD-R-110, unaffected by this status change.

## 2. Purpose

Atlas Core determines what exists. Atlas Product Architecture determines what those accepted concepts mean and how they behave. Neither document may describe a screen, a workspace, a visual treatment, or an interaction — both explicitly exclude this content from their own scope. This Doctrine exists to close that gap: to govern how an already-accepted Product Concept's already-fixed normative behavior is perceived, understood, and acted on by a human Investor, without altering what that behavior means.

This Doctrine is required, not optional, and is not discharged by any existing document. This finding, and the evidence supporting it, is the accepted architectural basis of the completed **UX-000 Pre-Design Investigation** (Section 3, Necessity), adopted here without reopening it. That investigation found, and this Doctrine treats as settled: APP-000 §1 explicitly excludes screens, workspaces, interaction design, and visual design from its own governance; every APS specification's own Scope section independently confirms the same exclusion; and the pre-existing UX governance corpus's own documented history (`ADR-001` through `ADR-004`) demonstrates that, absent a governing UX doctrine, real, values-bearing contradictions occur — not hypothetically, but as committed fact, later corrected only through expensive, ad hoc architecture review.

## 3. Scope

In scope: UX's own authority and responsibility (Sections 7–8); the representation of already-accepted Product Concepts without altering their meaning (Section 9); Human Ownership, AI presentation, and attribution (Sections 10–11); Attention and information hierarchy (Section 12); Uncertainty and Confidence presentation (Section 13); the presentation of Reasoning, Evidence, and Conclusion (Section 14); Decision and Commitment presentation (Section 15); Outcome and Decision Quality presentation (Section 16); Learning, Review, and Reflection presentation (Section 17); implementation-independent interaction semantics (Section 18); accessibility as a correctness property (Section 19); terminology discipline for UX-exclusive vocabulary (Section 20); UX governance and ADR authority (Section 21); extensibility (Section 22); and the formal supersession of the prior UX-000 (Section 23).

Out of scope: screens, page layouts, component anatomy, visual tokens, typography, color, animation, navigation maps, detailed workflows, API behavior, schemas, storage, implementation technology, algorithms, AI-generation logic, and scoring models. This Doctrine does not design, and SHALL NOT be read to design, any of the above; those subjects belong to subordinate UX specifications, governed by, and consistent with, this Doctrine.

## 4. Governing Authority

- **Atlas Core Architecture Doctrine, OE-002, OE-004 — Final.** Normative Core, superior to every document in the Atlas UX Architecture. This Doctrine does not, and SHALL NOT, govern Core ontology directly.
- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative Product, superior to this Doctrine.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.4.** Normative Product, superior to this Doctrine; the sole authority for which concepts are accepted, rejected, or merged. *(Citation refreshed per the Atlas UX Governance Resolution Sprint, 2026-08-03; prior text read "Draft v0.3.")*
- **APS-001 through APS-009 — Decision Context, Investor Reasoning, Evidence, Learning, Outcome, Portfolio, Watchlist, Daily Brief, Discover.** Normative Product, superior to this Doctrine; the sole authority for each accepted concept's own normative behavior. *(Citation refreshed per the Atlas UX Governance Resolution Sprint, 2026-08-03; prior text read "APS-001 through APS-005 — Decision Context, Investor Reasoning, Evidence, Learning, Outcome.")*
- **`ADR-002-Critical-UX-Architecture-Resolutions.md`, `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`, `ADR-004-Scenario-Analysis-Comparison-and-Sequence-Authority-Resolution.md` — Accepted.** Normative UX, subordinate to this Doctrine, authoritative within their own stated scope (Section 21).
- **`ADR-001-Missing-Source-Volume-Governance.md` — Status: Accepted**, per its own formal ratification (2026-08-01), resolving the prior mismatch between its file status and its actual downstream reliance. Its historical Proposed period, and the fact that `ADR-002`, `ADR-003`, and `ADR-004` already relied on it as binding before this ratification, remain disclosed in its own ratification note. `UXD-R-102`, below, was itself subsequently corrected to state this directly, per Section 26.
- **`UX-000-The-Atlas-Experience.md` — Historical, superseded by this document.** See Section 23. Cited here only as the source of the doctrine-level content this document absorbs and re-grounds; it is no longer active governing authority once this Doctrine is accepted.
- **The completed UX-000 Pre-Design Investigation, UX Governance Relationship & Terminology Reconciliation Investigation, and "Conclusion" Status Investigation** (this conversation's prior turns). Non-normative — adopted here in full as this Doctrine's own accepted architectural basis; their conclusions are incorporated directly into this document's normative text and are not reopened.

## 5. The Role of UX in Atlas

UX translates an already-accepted Product Concept's already-fixed normative behavior into a form a human Investor can perceive, understand, and act on, without altering what that behavior means. UX does not decide what a Decision is, what Decision Quality means, or what Learning requires — Product Architecture has already, exclusively, decided these. UX decides how the Investor sees them, in what order, with what emphasis, through what interaction, and with what disclosure.

Product Architecture already, structurally, depends on UX to resolve specific, bounded interpretive questions it deliberately leaves open — for example, APS-001 DC-R-030's own text defers the operative test for distinguishing an objective clarification from a genuine change "to a future UX specification." UX's own authority includes resolving exactly these named, bounded deferrals; it does not include resolving any question Product Architecture has not deferred.

## 6. Core → Product → UX → Implementation Boundary

**UXD-R-001.** The governing chain SHALL be: Core determines what exists; Product determines what accepted concepts mean and how they behave; UX determines how already-accepted Product behavior is perceived, understood, and acted on; Implementation determines how the UX specification is built.

**UXD-R-002.** UX SHALL NOT directly govern Core ontology. No UX document SHALL assert, redefine, or imply a Core Domain Object, Core invariant, or Core reference relationship.

**UXD-R-003.** UX SHALL NOT redefine Product Architecture. No UX document SHALL contradict a Product Principle, redefine a term APP-000 or APP-001 already defines, or alter an accepted concept's own normative behavior as stated by its governing APS.

**UXD-R-004.** UX SHALL NOT infer authority from implementation. The existence of an implementation, a technical constraint, or an engineering convenience SHALL NOT be treated as grounds for a UX rule, and SHALL NOT be treated as evidence that a UX rule is correct.

**UXD-R-005.** Where conflict exists between layers: Core authority SHALL prevail over Product; Product authority SHALL prevail over UX; UX authority SHALL prevail over Implementation.

**UXD-R-006.** A subordinate UX specification SHALL NOT override this Doctrine.

**UXD-R-007.** An accepted UX ADR MAY amend or clarify a subordinate UX specification within its own stated scope, per Section 21. An accepted UX ADR SHALL NOT amend this Doctrine merely through the ordinary subordinate-specification correction process; amending this Doctrine itself requires the higher-order process stated in UXD-R-110.

**UXD-R-008.** A statement belongs at the UX layer only if it concerns what a human perceives or does, not what fact Atlas's data model asserts or what rule governs a Concept's own behavior, and only if it would remain true regardless of the specific screen, framework, or visual design used to express it while changing if Product Architecture's own normative behavior changed. This test governs every subordinate UX specification's own scope discipline, mirroring APP-000 §1's own test for the Product layer.

## 7. UX Responsibilities

**UXD-R-009.** UX SHALL own visual representation — how an already-established Product-layer fact is rendered.

**UXD-R-010.** UX SHALL own information hierarchy — what receives attention first, second, and last.

**UXD-R-011.** UX SHALL own interaction semantics — what a click, an Accept, a focus event, or a keyboard action means and does.

**UXD-R-012.** UX SHALL own disclosure mechanics — how and when Uncertainty, confidence, attribution, and Challenges become visible, collapsed, or expanded.

**UXD-R-013.** UX SHALL own attribution presentation — how PP-008's own attribution requirement is made genuinely visible, not merely technically present in a data field.

**UXD-R-014.** UX SHALL own uncertainty presentation — how PP-007's own disclosure requirement is expressed to the Investor.

**UXD-R-015.** UX SHALL own accessibility behavior — ensuring the interaction contract UX itself specifies is genuinely perceivable and operable through supported accessibility mechanisms.

**UXD-R-016.** UX SHALL own the human-readable organization of accepted Product Concepts into screens, workspaces, and components.

**UXD-R-017.** UX SHALL own the presentation-layer allocation of Attention, operationalizing PP-001 at the interaction layer.

**UXD-R-018.** UX SHALL own implementation-independent interaction contracts — what an interaction guarantees, independent of the specific platform or framework realizing it.

**UXD-R-019.** UX MAY resolve an interpretive ambiguity a Product Architecture document explicitly and namedly defers to a future UX specification. UX SHALL NOT resolve an ambiguity Product Architecture has not explicitly deferred.

## 8. UX Prohibitions

**UXD-R-020.** UX SHALL NOT decide or redefine a business or product rule — what constitutes a Decision, what Decision Quality means, what closes a Decision Context, or what makes two Product records equivalent.

**UXD-R-021.** UX SHALL NOT decide or redefine a Product Principle (PP-001 through PP-009). UX MAY operationalize a Product Principle at the presentation layer, per Section 24; it SHALL NOT restate it as though UX itself were the principle's own authority.

**UXD-R-022.** UX SHALL NOT introduce a new Product Concept. Every UX construct SHALL either (1) represent an already-accepted Product Concept, per APP-001 §3.x, or (2) be a pure presentation, navigation, or interaction artifact carrying no independent Product identity, ownership, lifecycle, or semantic authority.

**UXD-R-023.** Where a UX construct begins to acquire independent identity, ownership, lifecycle, or responsibility of its own — beyond pure presentation or interaction — it SHALL be referred back to Product Architecture for formal admission under APP-001's own concept-acceptance method. It SHALL NOT be resolved unilaterally at the UX layer.

**UXD-R-024.** UX SHALL NOT decide or redefine a Product relationship — what Pattern Recognition may or may not do to Learning, or Outcome's own Decision Quality boundary. UX MAY present these relationships; it SHALL NOT define, narrow, or extend them.

**UXD-R-025.** UX SHALL NOT decide or redefine ownership of a Product Concept.

**UXD-R-026.** UX SHALL NOT decide or redefine the lifecycle of a Product Concept — its open/closed states, its active/completed states, or its permanence.

**UXD-R-027.** UX SHALL NOT decide or redefine the identity of a Product Concept — what makes two instances numerically identical.

**UXD-R-028.** UX SHALL NOT decide or redefine the equivalence of a Product Concept — what makes two numerically distinct instances equivalent. UX SHALL NOT merge equivalent-but-distinct instances for presentation convenience.

**UXD-R-029.** UX SHALL NOT decide or redefine a Product invariant.

**UXD-R-030.** UX SHALL NOT decide or adjudicate Reasoning validity — whether a premise is sound, or how a Contradiction is resolved.

**UXD-R-031.** UX SHALL NOT decide or redefine Decision logic — what constitutes a valid, complete, or recordable Decision beyond what Product Architecture already requires.

**UXD-R-032.** UX SHALL NOT decide or redefine Learning logic — what constitutes a Learning Act, or when Learning may occur.

**UXD-R-033.** UX SHALL NOT decide or redefine Outcome meaning — what an Outcome asserts, or does not assert.

**UXD-R-034.** UX SHALL NOT decide, score, or characterize Decision Quality.

**UXD-R-035.** UX SHALL NOT decide or extend AI autonomy — what Atlas is permitted to do without an identifiable Investor act.

**UXD-R-036.** UX SHALL NOT decide or redefine Recommendation logic — how Atlas decides what to advise, or what confidence to assign.

**UXD-R-037.** UX SHALL NOT assert a Core correspondence. No UX document SHALL claim that a UX-layer artifact literally is a specific Core Domain Object.

**UXD-R-038.** UX SHALL NOT assert Core reference eligibility for any UX-layer artifact.

**UXD-R-039 — Product sequencing rule.** UX SHALL NOT operationalize the normative behavior of an accepted Product Concept before that concept's own normative behavior is governed with sufficient Product Architecture authority to support the UX behavior being specified. This does not require a dedicated APS for every accepted concept; it requires only that the relevant Product-layer behavior already be governed, by whatever document currently governs it.

## 9. Product Concept Representation

**UXD-R-040.** No UI element SHALL be designed such that accepting, using, or being exposed to Atlas-originated content is itself sufficient to constitute a Decision, per PP-003 and PP-005.

**UXD-R-041.** Evidence SHALL be presented direction-neutral by default; no rendering SHALL imply an intrinsic SUPPORTS or CHALLENGES stance for an Evidence Instance outside a specific Citation context, per APS-003 EVINV-003.

**UXD-R-042.** Two equivalent-but-numerically-distinct Learning Results, Evidence Instances, or Outcomes SHALL be rendered as separate, independently inspectable records. UX SHALL NOT merge them for display convenience, per APS-003 EVINV-002, APS-004 LRINV-021, and APS-005 ORINV-010.

**UXD-R-043.** Outcome SHALL NOT be presented with greater visual priority, more prominent placement, or more assertive framing than the Reasoning and Decision Quality context needed to interpret it, per PP-009 and APS-005 OR-R-072 through OR-R-080.

**UXD-R-044.** No interaction SHALL be designed such that using or accepting Atlas-originated content substitutes for the Investor's own exercise of Investor Judgment, per PP-003.

**UXD-R-045.** UX SHALL NOT define, derive, calculate, or assign a Decision Quality score. Any presentation of Decision Quality SHALL remain qualitative and grounded in the Reasoning it characterizes; it SHALL NOT appear as a standalone metric, rank, rating, badge, or performance indicator. Outcome SHALL NOT be used to derive Decision Quality, per UXD-R-034 and PP-009.

**UXD-R-046.** Attention allocation choices SHALL be justified by relevance to the Investor's own investment objectives, active Reasoning, or a prospective or recorded Decision, per PP-001; UX SHALL NOT justify a proactive presentation solely on the grounds that the underlying information exists or is available.

**UXD-R-047.** Uncertainty SHALL be disclosed wherever it materially bears on the Reasoning being presented; UX SHALL NOT conceal, minimize, or obscure it, per PP-007.

## 10. Human Ownership

Grounded directly in PP-003 and PP-005.

**UXD-R-048.** Atlas MAY support, suggest, summarize, organize, and surface. Atlas SHALL NOT perform the Investor's own act of Judgment, Commitment, or Learning.

**UXD-R-049.** No interaction with Atlas-originated content SHALL silently transfer authorship to the Investor.

**UXD-R-050.** Accepting Atlas-originated content without a genuine Investor edit SHALL preserve Atlas-origin attribution.

**UXD-R-051.** Only a genuine Investor act MAY create Investor-authored content from Atlas-originated content.

**UXD-R-052.** No irreversible Investor-owned action SHALL be triggered autonomously by Atlas.

**UXD-R-053.** The Record Decision action, or any equivalent future commitment action, SHALL require an identifiable Investor act. It SHALL NOT be triggerable by Atlas under any circumstance.

## 11. AI Presentation and Attribution

Grounded directly in PP-008.

**UXD-R-054.** Visible, understandable attribution SHALL be required for Atlas-originated content, Investor-originated content, externally-sourced content, and transformed or edited Atlas-originated content.

**UXD-R-055.** Attribution SHALL survive acceptance, editing, historicization, later presentation, and review. The underlying historical provenance SHALL NOT become thinner than the actual sequence of acts that occurred.

**UXD-R-056.** Atlas SHALL NOT be framed as independently knowing, believing, deciding, judging, learning, committing, or being certain — including as an independent believer, the owner of a Decision, the source of certainty, the final authority, an autonomous learner, or an autonomous judge. This does not prohibit accurate source attribution, such as "Atlas has identified...", where clearly framed as system output rather than as independent truth authority.

**UXD-R-057.** Atlas-generated analytical content SHALL NOT use first-person belief framing. Prohibited framing includes language equivalent to "I believe...", "I have decided...", or "I think this investment is correct...". Required framing uses clearly attributed, third-person language such as "Atlas's current synthesis...", "The current analysis indicates...", or "Atlas has identified...". This is a doctrine-level language rule governing every subordinate UX specification's own copy; it does not itself specify final component copy.

## 12. Attention and Information Hierarchy

Grounded directly in PP-001.

**UXD-R-058.** Meaning SHALL be presented before volume; a Conclusion SHALL be presented before the detail that supports it, per the Conclusion rule in Section 14.

**UXD-R-059.** Complexity SHALL be disclosed progressively, per PP-004, and withheld until it is materially relevant to the Investor's current objective or explicitly requested.

**UXD-R-060.** The Investor's Attention SHALL be treated as scarce; a proactive presentation SHALL justify the Attention it requests.

**UXD-R-061.** Visual priority SHALL express architectural importance as Product Architecture states it, and SHALL NOT contradict Product Architecture. Visual hierarchy MAY violate Product Architecture even where no individual sentence in the interface does; a UX specification SHALL be checked for this failure mode explicitly, not only for textual contradiction.

## 13. Uncertainty and Confidence

Grounded directly in PP-007.

**UXD-R-062.** UX SHALL NOT present uncertainty as certainty.

**UXD-R-063.** Confidence presentation SHALL NOT imply precision unsupported by the underlying Evidence and Reasoning.

**UXD-R-064.** This Doctrine SHALL NOT define a numeric or categorical confidence scale. Any future scale requires its own subordinate specification.

**UXD-R-065.** Confidence is presentation terminology, not a Product Concept. It SHALL remain subordinate to the Product Concept of Uncertainty and to the Evidence and Reasoning support it characterizes.

## 14. Reasoning, Evidence, and Conclusion Presentation

**UXD-R-066.** UX SHALL make Investor Reasoning inspectable; it SHALL NOT decide what Reasoning is sufficient or valid.

**UXD-R-067.** The visibility of supporting and challenging material SHALL be preserved; UX SHALL NOT default to presenting one side as inherently more legitimate merely because it supports the current Proposed Decision.

**UXD-R-068.** Contradiction, Uncertainty, and Superseded Content SHALL be preserved in presentation wherever Product Architecture requires them to be preserved in substance; UX SHALL NOT hide them by default.

**UXD-R-069.** Equivalent Evidence examined across different material SHALL NOT be visually presented as independent corroboration, per APS-003 EV-R-118.

**UXD-R-070 — Challenges and Supporting Factors.** These are UX presentation categories over already-governed Reasoning and Evidence relationships. They are not Product Concepts. They SHALL NOT be assigned different default credibility solely because one supports and one challenges the current view.

**UXD-R-071 — Conclusion rule.** Conclusion is a UX presentation artifact, not an independent Product Concept, per the completed "Conclusion" Status Investigation, adopted here in full and not reopened. Its Product-layer correspondence depends on its variant and lifecycle stage:

1. **Initial, unengaged Current Conclusion** — Atlas-originated, PP-008-attributable, pre-Reasoning material within an open Decision Context, per APP-001 §3.10. It SHALL NOT be presented as Investor-authored or Investor-endorsed.
2. **Investor-engaged Current Conclusion** — the underlying Product content is an ordinary Premise, or a compact presentation of Premise content, within Investor Reasoning, per APS-002; this Doctrine creates no special Premise subtype, identity, authority, or Product status. Any prominence, anchoring role, or hierarchy Current Conclusion carries is solely a UX presentation fact, not a Product-layer distinction. Initial, Atlas-authored content remains pre-Reasoning material, per item 1, until the Investor performs a genuine act connecting it into their own reasoning, satisfying APS-002 IR-R-014; passive viewing does not create Investor Reasoning, and acceptance without substantive editing does not, by itself, transfer authorship or constitute this connecting act, per ADR-002 C-02's own authorship rule and Section 10. A genuine Investor edit, an explicit incorporation of the content into another Premise, or another deliberate act connecting it into the Investor's own reasoning MAY create Premise status. The exact interaction mechanics by which a subordinate UX specification detects or presents this transition are not defined here; no subordinate specification SHALL weaken this Product-layer threshold. Once Premise status exists, it is governed by Investor Reasoning's own mutability while open (IR-R-018): a genuine edit SHALL preserve superseded content as Superseded Content, per APS-002 IR-R-027 and IR-R-059.
3. **Historical Conclusion** — the preserved presentation of Conclusion content after its governing Product-layer lifecycle closes. It SHALL be immutable in presentation wherever the underlying Product content is immutable. This Doctrine SHALL NOT independently decide whether Commitment and Abandonment historicize Conclusion differently; a subordinate specification SHALL follow APS-001 and APS-002 on this question.
4. **Review Conclusion** — corresponds to a Learning Result, per APS-004 LR-R-030's own "generalized conclusion" definition and LR-R-097's own Decision-Review-as-occasion rule. It MAY arise only through a genuine, Investor-initiated Learning Act, per APS-004 LR-R-147 and LRINV-018. Atlas MAY support or surface material toward it; Atlas SHALL NOT autonomously produce it.
5. **Primary and Portfolio Conclusion** — their complete Product-layer correspondence remains open until the relevant Investment Case or Portfolio concept receives its own Product Architecture treatment. A subordinate UX specification SHALL NOT overclaim their Product status before then. *(Annotated per the Atlas UX Governance Resolution Sprint, 2026-08-03: this treatment now exists — Investment Case at `APP-001` §3.13, Portfolio at `APS-006`. This annotation records the fact; it does not itself grant Product status to Primary or Portfolio Conclusion, which remains, per this item's own rule, a matter for the subordinate UX specification presenting them to state correctly.)*

**UXD-R-072.** Conclusion SHALL NOT be treated as Decision, Recommendation, Proposed Decision Candidate Content, Outcome, Decision Quality, Pattern Recognition, or autonomous Investor Judgment.

**UXD-R-073.** Atlas-generated Conclusion content SHALL NOT use first-person belief framing, per Section 11's own general rule, applied here to the single most visually prominent presentation surface this Doctrine governs.

## 15. Decision and Commitment

**UXD-R-074.** A Decision SHALL be attributable to the Investor as its owner in every presentation, per PP-005.

**UXD-R-075.** No UX specification SHALL design a capability under which a Decision is recorded without an identifiable act of Investor commitment.

**UXD-R-076 — Recommendation terminology.** Recommendation remains rejected as an independent Product Concept by APP-001 §4. Atlas Recommendation and Proposed Decision Candidate Content MAY exist only as UX presentation or interaction artifacts, under `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`, adopted here unchanged. Neither is a Decision. Neither is Investor Judgment. Neither creates Commitment. UX SHALL NOT introduce an additional recommendation-like term without a dedicated terminology decision, following the process ADR-003 itself already used.

## 16. Outcome and Decision Quality

Grounded directly in PP-009 and APS-005.

**UXD-R-077.** Outcome SHALL NOT be presented as proof of Decision Quality.

**UXD-R-078.** A favorable Outcome SHALL NOT be visually framed as proof of good Reasoning.

**UXD-R-079.** An unfavorable Outcome SHALL NOT be visually framed as proof of bad Reasoning.

**UXD-R-080.** Learning and review presentation SHALL preserve the distinction between what became actual and whether the original Reasoning process was sound.

**UXD-R-081.** Outcome SHALL NOT automatically receive greater visual emphasis than the Reasoning and Decision Quality context needed to interpret it.

**UXD-R-082.** Aggregate Outcome favorability SHALL NOT be presented as a proxy for Decision Quality, per APS-004 LRINV-014.

## 17. Learning, Review, and Reflection

**UXD-R-083.** Learning is the accepted Product Concept, per APP-000 §5/§6.6 and APP-001 §3.6.

**UXD-R-084.** Review is an occasion or workflow that MAY provide the occasion on which a Learning Act occurs, per APS-004 LR-R-097. Review is not itself Learning and SHALL NOT be presented as identical to it.

**UXD-R-085.** Reflection is ordinary-language activity, not an independent Product Concept, per APP-001 §4. Before preservation, Reflection is an occasion or act already governed by Learning, per APS-004 LR-R-092, or by Investor Judgment, per APP-001 §3.5. After preservation, its content is Investor-originated Evidence, per APP-001 §4's own Reflection rejection. No separate Reflection lifecycle is created by this rule.

**UXD-R-086.** No review or reflection workflow SHALL be presented as constituting Learning unless a genuine, Investor-initiated Learning Act has occurred, per APS-004 LR-R-147 and LRINV-018.

**UXD-R-087.** Pattern Recognition MAY provide attributable input to Learning, per APS-004 LR-R-091 through LR-R-096. It SHALL NOT be presented as constituting Learning itself, per APS-004 LRINV-015.

## 18. Interaction Semantics

**UXD-R-088.** UX owns interaction semantics as an implementation-independent contract, per Section 7; this Doctrine does not itself define any specific screen, component, or interaction detail.

**UXD-R-089 — Scenario Analysis and Comparison.** These are UX presentation/interaction artifacts, per `ADR-004-Scenario-Analysis-Comparison-and-Sequence-Authority-Resolution.md`, adopted here unchanged. Hypothetical "outcomes" produced within Scenario Analysis SHALL NOT be confused with, or presented using terminology identical to, the Product Concept Outcome. A subordinate UX specification SHALL use disambiguating terminology wherever both senses could otherwise be read as the same word.

**UXD-R-090.** A UX-layer dependency, flow, or sequence diagram describes interface information flow only. It SHALL NOT be read to assert a Product-layer causal or derivational rule, regardless of the language it uses.

## 19. Accessibility

**UXD-R-091.** Accessibility is part of the correctness of an interaction contract, not optional polish.

**UXD-R-092.** Any action, disclosure, attribution state, hierarchy, refusal state, or historical state governed by UX SHALL remain perceivable and operable through supported accessibility mechanisms.

This Doctrine does not define platform-specific accessibility implementation; that is a subordinate UX specification's own responsibility, consistent with UXD-R-091 and UXD-R-092.

## 20. Terminology Discipline

**UXD-R-093 — Session.** Session SHALL NOT be reintroduced as a Product Concept, per APP-001 §4's own rejection. The ordinary-language term MAY be used only to describe a temporary interaction period, with no independent identity, persistence, ownership, or lifecycle. A doctrine-level organizing structure named "Session" SHALL NOT be retained without this qualification stated explicitly alongside it.

**UXD-R-094 — Memory.** Memory SHALL NOT be used as a Product Concept. A subordinate UX specification SHALL distinguish clearly among historical persistence (APS-001 §13, APS-002 §18, APS-003 EVINV-009), Learning (APS-004), Evidence (APS-003), and Decision history. Memory MAY remain ordinary UX language only where it implies no independent Product semantics.

**UXD-R-095 — Workspace and Dashboard.** Workspace and Dashboard are UX organizational artifacts. They are not Product Concepts. They carry no independent Product identity, ownership, or lifecycle. A Decision Workspace MAY represent one Decision Context; the two terms are not ontologically identical, and a subordinate UX specification SHALL NOT treat them as interchangeable. Any future independent Workspace state — persistence, ownership, or lifecycle beyond pure screen organization — SHALL be referred to Product Architecture, per UXD-R-023.

**UXD-R-096.** A term used at the UX layer that shares a word with an accepted Product Concept but carries a different meaning SHALL be disambiguated explicitly in the subordinate specification that introduces it, following the precedent already established for Knowledge (APP-001 §4) and for Reasoning (APP-001 §7 Observation 1).

**UXD-R-111 — Proposed Decision.** Proposed Decision is a UX presentation/workflow artifact. It is not a Decision. It is not Commitment. It MAY present in-progress Investor Reasoning directed toward a prospective Decision, per APS-002. Proposed Decision Candidate Content remains governed by `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`, adopted here unchanged, per UXD-R-076. Neither Proposed Decision nor Proposed Decision Candidate Content SHALL be treated as a Product Concept.

## 21. UX Governance and ADR Authority

**UXD-R-097.** This Doctrine governs every UX specification.

**UXD-R-098.** `ADR-002`, `ADR-003`, and `ADR-004` remain authoritative within their own stated scope, per Section 4.

**UXD-R-099.** An ADR is an amendment and resolution mechanism operating on this Doctrine or on a subordinate UX specification; it is not a separate architectural layer between them.

**UXD-R-100.** A future ADR SHALL identify exactly what governing text it amends or clarifies.

**UXD-R-101.** Historical ADR reasoning SHALL NOT be silently deleted; a superseding decision SHALL state what changed and why, per the Atlas Core Architecture Doctrine §10's own publication and amendment discipline, adopted here as UX's own standard.

**UXD-R-102.** `ADR-001` is Accepted. Its ratification resolved the historical mismatch between its formal status and its actual downstream reliance by `ADR-002`, `ADR-003`, and `ADR-004`; its historical Proposed period remains part of its own preserved decision record, per its own Ratification Note. Its scope remains limited to documentary-source and missing-source governance; ratification grants it no authority to amend this Doctrine through the ordinary ADR mechanism, per UXD-R-007 and UXD-R-110. `ADR-002`, `ADR-003`, and `ADR-004` remain authoritative only within their own stated scope, per Section 4.

**UXD-R-110 — Doctrine-level amendment process.** Amendment of this Doctrine itself is a higher-order act, distinct from an ordinary ADR's correction of a subordinate UX specification, per UXD-R-007. This Doctrine adopts the same discipline the Atlas Core Architecture Doctrine §10 and §11 require for Core-level amendment as its own standard — not because the Core Architecture Doctrine itself governs UX amendment, but because this Doctrine holds itself to the same rigor. A proposed amendment to this Doctrine SHALL identify: the forcing function requiring it; every doctrine rule it affects; the authority basis for the change; the migration consequence for every subordinate UX specification and accepted ADR depending on the affected rule; and a historical decision record preserving what was decided, when, the alternatives considered, and the grounds on which each was rejected, per the historical-integrity discipline this Doctrine already applies to the prior UX-000 in Section 23. An accepted UX ADR MAY document a doctrine amendment only after this higher-order process has independently justified it; the ordinary ADR mechanism SHALL NOT itself be the vehicle by which the amendment is decided.

## 22. Extensibility

**UXD-R-103.** Every new UX construct SHALL be tested against UXD-R-022 and UXD-R-023 before being adopted; this Doctrine states no separate admission test here.

**UXD-R-104.** UX SHALL NOT get ahead of Product Architecture's own sequencing. A Product Concept accepted by APP-001 but not yet operationalized by its own governing APS — for example, Pattern Recognition, accepted at APP-001 §3.12 with no governing APS yet — SHALL NOT have its normative behavior represented by any UX specification until that governing APS exists, per UXD-R-039.

## 23. Supersession and Historical Integrity

This Doctrine formally supersedes `UX-000-The-Atlas-Experience.md`, per the completed UX Governance Relationship & Terminology Reconciliation Investigation's own Section 10 (Migration Models, Model C selected: absorption with explicit historical marking) and Section 5 (section-by-section classification), adopted here in full and not reopened.

**UXD-R-105.** The prior `UX-000-The-Atlas-Experience.md` remains part of the historical record. It is not erased.

**UXD-R-106.** Its Correction Notice SHALL NOT be removed or rewritten by any future action taken under this Doctrine's own authority.

**UXD-R-107.** Its valid doctrine-level content has been absorbed and re-grounded into this document, per the table below. Where this document and the prior document conflict, this document governs.

**UXD-R-108.** The prior document SHALL NO LONGER serve as active governing authority once this Doctrine is accepted.

**UXD-R-109.** `UX-000-The-Atlas-Experience.md` now carries an explicit Historical / Superseded notice, per its own Supersession Notice (2026-08-01). The file remains preserved as historical evidence; its original Correction Notice and all substantive sections remain intact and unrewritten. It is no longer current UX doctrine. This Doctrine, at Release Candidate RC v1.0, is the current governing UX doctrine baseline. No historical content was silently erased or rewritten by the addition of that notice, per the non-erasure discipline UXD-R-105 and UXD-R-106 already require.

**Absorption table**, per the completed Pre-Design Investigation's own Section 5 classification, adopted unchanged:

| Old §, `UX-000-The-Atlas-Experience.md` | Disposition | New location |
|---|---|---|
| Correction Notice | Preserved verbatim in the historical record; not migrated as active text | N/A — remains only in the superseded document |
| §1 Purpose | Duplicative of APP-000 §3–4; collapses to a cross-reference | Section 2 |
| §2 Experience Philosophy | Valid, UX-exclusive; no re-grounding required | Not restated verbatim in this Doctrine, which is a governance document rather than an experiential-philosophy one; reserved for a subordinate UX specification to carry forward |
| §3 Emotional Goals | Valid, UX-exclusive | As above |
| §4 The Atlas Session | Required reframing (Session collision risk) | Section 20, UXD-R-093 |
| §5 Attention | Duplicative of PP-001; re-grounded | Section 12 |
| §6 Conclusions Before Details | Required the Conclusion investigation before migration | Section 14, UXD-R-071 through UXD-R-073 |
| §7 Memory | Required disambiguation from Learning | Section 20, UXD-R-094 |
| §8 Respect for Uncertainty | Duplicative of PP-007; re-grounded | Section 13 |
| §9 Workspace Philosophy | Valid, UX-exclusive | Section 20, UXD-R-095 (terminology discipline); experiential content reserved for a subordinate specification |
| §10 Simplicity | Duplicative of PP-004; re-grounded | Section 12, UXD-R-059 |
| §11 The Role of AI | Required rewording ("invisible" framing risk) | Section 11, UXD-R-056/057 |
| §12 Interaction Principles | Valid, UX-exclusive | Section 18 (implementation-independent contracts framing); experiential content reserved for a subordinate specification |
| §13 Success | Duplicative of PP-009; the single most important alignment | Section 16 |
| §14 The Atlas Test | Valid, UX-exclusive design heuristic | Reserved for a subordinate specification; informed Section 24's own UX Principles |
| §15 The Atlas Promise | Duplicative of §1's own content | Collapses with §1's treatment, Section 2 |

## 24. UX Principles

Each UX Principle operationalizes one or more Product Principles, or another explicit Product Architecture boundary, at the presentation/interaction layer. UX Principles do not restate or own PP-001 through PP-009; PP-001 through PP-009 remain exclusively Product Architecture's own authority. Where a UX Principle is not derived from a specific Product Principle, its own citation states this explicitly rather than overclaiming one.

**UXP-001 — Meaning Before Volume** *(APP-000 §6.5, Reasoning as the Durable Artifact; APP-000 §6.6, Learning as the Purpose of Memory; PP-001 only where attention allocation is genuinely relevant).* A synthesis or conclusion is presented before the detail that supports it; the interface never requires the Investor to assemble meaning from volume before any meaning is offered.

**UXP-002 — Investor Attention Is Scarce** *(PP-001).* Every proactive presentation justifies the Attention it requests before requesting it.

**UXP-003 — Attribution Must Be Visible** *(PP-008).* Attribution is genuinely visible to the Investor, not merely present in an underlying data field.

**UXP-004 — Uncertainty Must Remain Visible** *(PP-007).* Uncertainty is disclosed wherever it materially bears on what is presented; it is never resolved by assertion or hidden by omission.

**UXP-005 — Atlas Supports, Never Owns** *(PP-003, PP-005).* Every interaction with Atlas-originated content is designed so that the Investor's own act of Judgment, Commitment, or Learning remains the operative act.

**UXP-006 — Irreversible Acts Require Investor Action** *(PP-003, PP-005).* No irreversible, Investor-owned action is ever presented as available to Atlas alone.

**UXP-007 — Historical Meaning Is Never Silently Rewritten** *(PP-006).* A historical presentation reflects what was actually recorded at the time it was recorded; a later correction is additive, never a silent rewrite.

**UXP-008 — Visual Hierarchy Must Preserve Product Meaning** *(PP-007, PP-009).* Relative visual emphasis never contradicts what Product Architecture requires — even where no individual sentence in the interface does.

**UXP-009 — UX Artifacts Do Not Become Product Concepts** *(APP-001 §1's own admission method, applied at the UX layer).* A UX-layer construct that begins to acquire independent identity, ownership, or lifecycle is referred back to Product Architecture, never resolved unilaterally.

**UXP-010 — Outcome Does Not Define Decision Quality** *(PP-009).* A realized state of affairs is never presented as proof of the reasoning that preceded it.

**UXP-011 — Accessibility Is Part of Correctness** *(a standing UX-layer commitment established by this Doctrine, not derived from a specific Product Principle).* An interaction contract that is not perceivable and operable through supported accessibility mechanisms is not a correct interaction contract. This commitment is consistent with, and necessary for, governed UX meaning to remain perceivable and operable by every Investor; it does not modify Product meaning and does not introduce any implementation-specific requirement.

**UXP-012 — Presentation Must Not Imply Unowned Certainty or Judgment** *(PP-003, PP-007).* No presentation implies a degree of certainty, belief, or autonomous judgment that Atlas does not, and must not, actually hold.

## 25. Traceability

This section distinguishes Normative Core, Normative Product, Normative UX (Accepted ADR), historical UX source, and investigation findings adopted by this Doctrine, for every substantive area this document governs.

| Doctrine area | Normative Core basis | Normative Product basis | Normative UX (ADR) basis | Historical UX source | Investigation basis |
|---|---|---|---|---|---|
| §6 Boundary (UXD-R-001–008) | Architecture Doctrine §1, §12 | APP-000 §1, §2, §9 | — | — | Pre-Design Investigation §3, §6 |
| §7 Responsibilities (UXD-R-009–019) | — | APP-000 §7 PP-001, PP-007, PP-008; APS-001 DC-R-030 | — | old §5, §8 | Pre-Design Investigation §4 |
| §8 Prohibitions (UXD-R-020–039) | Architecture Doctrine §2–5 | APP-000 §2; APP-001 §1 | — | — | Pre-Design Investigation §5, §7 |
| §9 Product Concept Representation (UXD-R-040–047) | — | PP-001, PP-003, PP-005, PP-007, PP-009; APS-003 EVINV-002/003; APS-004 LRINV-021; APS-005 OR-R-072–080, ORINV-010 | — | — | Pre-Design Investigation §9, §10 |
| §10 Human Ownership (UXD-R-048–053) | — | PP-003, PP-005 | ADR-002 C-02 | old (n/a) | Terminology Investigation §7; Pre-Design Investigation §9 |
| §11 AI Presentation (UXD-R-054–057) | — | PP-008 | ADR-002 C-02 and addendum | old §11 | Pre-Design Investigation §11; "Conclusion" Investigation §8 |
| §12 Attention/Hierarchy (UXD-R-058–061) | — | PP-001, PP-004; APP-000 §6.4, §6.8 | ADR-002 C-01 | old §5, §6, §10 | Pre-Design Investigation §12; Terminology Investigation §5 |
| §13 Uncertainty/Confidence (UXD-R-062–065) | — | PP-007; APP-001 §3.8 | — | old §8 | Pre-Design Investigation §11; Terminology Investigation §7 |
| §14 Reasoning/Evidence/Conclusion (UXD-R-066–073) | — | APS-002 IR-R-014–018, IR-R-027, IR-R-059; APS-003 EV-R-118; APP-001 §3.10; APS-004 LR-R-030, LR-R-097, LR-R-147, LRINV-018 | ADR-002 C-02 | old §6 | "Conclusion" Status Investigation, in full |
| §15 Decision/Commitment (UXD-R-074–076) | — | PP-005; APP-000 §5 | ADR-003, all | — | Terminology Investigation §4, §7 |
| §16 Outcome/Decision Quality (UXD-R-077–082) | — | PP-009; APS-005 OR-R-072–080; APS-004 LRINV-014 | ADR-002 C-01 | — | Pre-Design Investigation §10 |
| §17 Learning/Review/Reflection (UXD-R-083–087) | — | APP-000 §5/§6.6; APP-001 §3.5, §3.6, §4; APS-004 LR-R-091–097, LR-R-147, LRINV-015, LRINV-018 | — | — | Terminology Investigation §7 |
| §18 Interaction Semantics (UXD-R-088–090) | — | — | ADR-004, all (interface information flow/sequence); ADR-003 R-06 (presentation derivation creates no Product identity or causality) | — | Terminology Investigation §4, §6 |
| §19 Accessibility (UXD-R-091–092) | — | — | ADR-002 C-06 | — | Pre-Design Investigation §4 |
| §20 Terminology (UXD-R-093–096, UXD-R-111) | — | APP-001 §4, §7 Observation 1; APS-002 (Proposed Decision correspondence) | ADR-003 (Proposed Decision Candidate Content) | old §4, §7, §9 | Terminology Investigation §7, §8 |
| §21 ADR Authority (UXD-R-097–102, UXD-R-110) | Architecture Doctrine §10, §11 | — | ADR-001, ADR-002, ADR-003, ADR-004 | — | Terminology Investigation §6, §11 |
| §22 Extensibility (UXD-R-103–104) | Architecture Doctrine §3, §8 | APP-001 §9 | — | — | Pre-Design Investigation §12 |
| §23 Supersession (UXD-R-105–109) | Architecture Doctrine §10, §11 | — | — | old UX-000, in full | Terminology Investigation §5, §10 |
| §24 UX Principles (UXP-001–012) | — | PP-001, PP-003, PP-005, PP-006, PP-007, PP-008, PP-009; APP-000 §6.5, §6.6 (UXP-001 specifically) | — | old §14 (informing, not sourcing) | Pre-Design Investigation §14 |

UXP-011 is a standing UX-layer commitment established by this Doctrine directly, not derived from PP-001, PP-008, or any other specific Product Principle; this is stated explicitly in UXP-011's own citation and is not overclaimed here.

No UX precedent, ADR, or historical source is treated as Product authority anywhere in this table; every row's Product-layer citation traces exclusively to APP-000, APP-001, or an APS.

## 26. Open Questions and Deferred Work

- **RESOLVED — ADR-001's formal ratification to Accepted status**, per the Atlas UX Architecture Governance Phase 0 Closure task (2026-08-01) and this subsequent Post-Ratification Consistency Correction (2026-08-02), which updated `UXD-R-102`'s own text to state the current governance status directly. `ADR-001`'s own header states Accepted, with its historical Proposed period disclosed in its own ratification note; `UXD-R-102`'s own prior text, stating the earlier Proposed status, remains recoverable in this document's own revision history, per the Atlas Core Architecture Doctrine §10's non-erasure discipline.
- **RESOLVED — a formal supersession notice added to `UX-000-The-Atlas-Experience.md` itself**, per the same Phase 0 Closure task (2026-08-01) and the same subsequent correction (2026-08-02), which updated `UXD-R-109`'s own text to state the current status directly, on the identical basis.
- **RESOLVED — Primary and Portfolio Conclusion's Product-layer correspondence precondition.** Per the Atlas UX Governance Resolution Sprint (2026-08-03), following the completed Atlas Product Architecture Reconciliation and the ATLAS UX CORRESPONDENCE INVESTIGATION: Investment Case now has formal Product Architecture treatment (`APP-001` §3.13) and Portfolio now has formal Product Architecture treatment (`APS-006`), per UXD-R-071 item 5's own annotation, above. This resolves the precondition item 5 named; it does not itself determine each subordinate UX specification's own correct presentation of Primary or Portfolio Conclusion, which remains that specification's own responsibility under item 5's unchanged rule. Prior text: "Primary and Portfolio Conclusion's complete Product-layer correspondence remains open pending Investment Case and Portfolio's own future Product Architecture treatment, per UXD-R-071 item 5. Not resolved here; not resolvable here."
- **RECORDED — Watchlist, Daily Brief, and Discover now possess formal Product Architecture treatment.** Per the same sprint: Watchlist (`APS-007`), Daily Brief (`APS-008`), and Discover (`APS-009`) — none named in this Doctrine's own original Open Questions, since none had received architectural treatment when this Doctrine reached Release Candidate — now have governing Product Architecture specifications. No UX-layer rule in this Doctrine depended on their prior absence; this bullet is recorded for completeness, consistent with the Investment Case/Portfolio resolution above.
- **The exact future Confidence representation scale** is not defined by this Doctrine, per UXD-R-064, and requires its own subordinate specification.
- **Migration of the existing operational UX documents** (UX-004 through UX-013F) against this Doctrine has not been performed and is out of this task's own scope; per the Terminology Reconciliation Investigation's own Section 13 migration strategy, that migration is deferred until after this Doctrine itself is reviewed and accepted.
- **Whether Review Conclusion's own current generation mechanism already requires a genuine Investor-initiated Learning Act**, as UXD-R-086/087 require, has not been confirmed against the operational component specification and remains an open verification item, per the "Conclusion" Status Investigation's own Section 17.
- **Any terminology alignment not already settled by the three completed investigations this Doctrine adopts** remains open by default; this Doctrine does not assert completeness beyond what those investigations themselves established.

## 27. Verdict

This Doctrine is Release Candidate, RC v1.0, established on the basis of Draft v0.2's own completed Internal Consistency Review, Targeted Consistency Correction cycle, and Final Verification (Verdict A) — the same five-phase discipline this session's own Product Architecture program applied to every APS specification, culminating in the same Release Candidate milestone that program itself reached. It is not yet Final and SHALL NOT be cited as such. Future substantive amendment remains governed by UXD-R-007 and UXD-R-110.

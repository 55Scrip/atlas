# Atlas Core — ADR Adoption Program · Sprint 1

## Recommendation Register

**Status:** Inventory and classification only. No ADR, OE document, doctrine, or implementation is created, modified, or authorized by this document. Every entry below is a *recommendation* in `Investigation-011`'s own precise sense — research-grade, non-binding, requiring a separate act of conversion by an authorized track before it has any normative force.

**Scope:** `docs/ADR-Investigation-001` through `docs/ADR-Investigation-011`, read in full. `Decision-Workspace-Gap-Analysis.md` and `Decision-Workspace-Architecture-Resolution-Sprint-1.md` (the two pre-series documents) are out of scope, per the sprint's own instruction to inventory "Investigations 001–011" specifically.

**Method note on what counts as a "recommendation":** each investigation's own Final Decision/verdict and every distinct, independently-actionable sub-finding that carries its own recommendation force (e.g., "Daily Brief should consume only a narrow projection," not merely "Daily Brief was discussed") is recorded as its own entry. Rejected alternatives are recorded as supporting evidence attached to the recommendation they support, not as independent entries — a rejection is not itself something Atlas is being told to do. Open Questions are compiled separately (Section 6), by investigation, rather than as inventory cards, since they are explicitly *not* recommendations — every source investigation labels them "not resolved," "carried forward," or "unresolved" precisely to distinguish them from a recommendation.

---

## 1. Executive Summary

Eleven investigations produced **61 discrete recommendations**, spanning eight of the fourteen preliminary categories (no recommendation was found to fit Lifecycle, Memory, Monitoring, or Other as a *primary* category, though several touch those concerns secondarily). Three structural facts dominate the register:

1. **A genuine dependency order exists, and it runs opposite to the investigations' own numbering.** `Investigation-009`, `010`, and `011` — the last three produced — settle *how* any of the other fifty-eight recommendations could ever legitimately become architecture. Adopting any content recommendation (Draft, CaseCondition, Assumption, and their many sub-findings) before the governance question is settled would itself violate `Investigation-011`'s own finding that conversion requires an authorized track's own process.
2. **Several recommendations are refinements of earlier ones within the same sub-lineage, not independent proposals.** `Investigation-006` refines `Investigation-005`'s CaseCondition proposal into a leaner, two-object shape; `Investigation-008` reconfirms and sharpens `Investigation-007`'s Assumption proposal. Both relationships are noted explicitly per entry, not silently merged.
3. **One architectural pattern — the append-only-event-stream-plus-derived-current-state model, first proven by the already-shipped `SecurityConfirmationEvent`/`ConfirmedSecuritySelection` pair — is independently reused as the preferred persistence shape in three separate recommendations** (`Investigation-003`'s Draft, `Investigation-005`/`006`'s CaseCondition, `Investigation-007`'s Assumption). This is the single most load-bearing recurring architectural decision in the register and is flagged wherever it appears.

**Recommendation density is highest in Governance (16) and Ontology/Domain Object (22 combined)** — see Section 4.

---

## 2. Recommendation Inventory

### Investigation 001 — Decision vs. DecisionContext

#### INV1-R1
- **Recommendation:** `DecisionContext` is correctly scoped as-is; its current fields (`situation`, `portfolio_relevance`, `capital_considerations`, `alternatives_considered`, `uncertainties`) require no addition or removal.
- **Architectural area:** Domain Object
- **Supporting evidence:** `Investigation-001` Phase 10, "Final Decision" — `KEEP_DECISION_CONTEXT`, evidenced by field-by-field ownership analysis (Phase 4) and the object's own docstring rationale.
- **Dependencies:** None.
- **Related documents:** Referenced and reconfirmed in `Investigation-002` (Phase 2), `Investigation-003` (Phase 6).
- **Current implementation impact:** None — `DecisionContext` already exists, unmodified, in `atlas/core/domain/decision_context/`.
- **Depended on by another recommendation:** Yes — INV2-R1, INV3-R6 (as a rejected-merge test case).
- **Suggested adoption priority:** Low (confirms existing state; no action required).

#### INV1-R2
- **Recommendation:** `DecisionContext` should be exposed to Alpha via a new API endpoint over the existing, unmodified `capture_decision_context.py`/`DecisionContextRepository` — wiring only, no domain or persistence change.
- **Architectural area:** Implementation Guidance
- **Supporting evidence:** `Investigation-001` Phase 3 ("PARTIAL_REUSE" finding) and Phase 10.
- **Dependencies:** None architecturally; practically gated by Sprint 2 prioritization.
- **Related documents:** `Decision-Workspace-Architecture-Resolution-Sprint-1.md` §3 (prior, non-series finding, cited for continuity).
- **Current implementation impact:** None yet — no endpoint exists.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV1-R3
- **Recommendation:** `DecisionContext` must never absorb Atlas-generated content, per-item acknowledgment records, or anything with a lifecycle after Decision recording — these belong to separate, not-yet-built objects.
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-001` Phase 6 (merge-attempt tests against Section 6/9's own UX-009 content), Phase 8 (Option B/C rejection).
- **Dependencies:** None.
- **Related documents:** Directly informs `Investigation-006` (CaseCondition) and the acknowledgment-object question in `Investigation-006`'s own Open Question 1.
- **Current implementation impact:** None — a negative constraint, not a build item.
- **Depended on by another recommendation:** Yes — constrains INV5-R1/INV6-R1's own scope.
- **Suggested adoption priority:** Medium (a design constraint future work must respect).

#### INV1-R4 through INV1-R6 (naming/discipline risks, compacted)
- **Recommendation:** (a) `portfolio_relevance`'s field name risks being misread as Atlas-computed data and should eventually be clarified or renamed; (b) future UI copy must keep `Decision.reason` and `DecisionContext.situation`/`capital_considerations` visibly distinct; (c) future UI copy must keep `DecisionContext.uncertainties` distinct from any later `ReflectionResponse` surface.
- **Architectural area:** Implementation Guidance
- **Supporting evidence:** `Investigation-001` Phase 9 (Consistency Test, three named risks).
- **Dependencies:** (c) depends on Reflection ever being un-deferred from Alpha scope.
- **Related documents:** `Investigation-002` (Reflection/DecisionContext boundary).
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

---

### Investigation 002 — DecisionContext vs. ReflectionResponse

#### INV2-R1
- **Recommendation:** Adopt the "occasioned vs. unoccasioned" test as the governing rule for where future Decision-Workspace content is routed: `DecisionContext` holds content requiring no prior Atlas computation; `ReflectionResponse` holds content that exists only because Atlas first computed something specific to react to.
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-002` Phase 4 (semantic difference), Phase 10 (Final Decision — `KEEP_WITH_CLEARER_BOUNDARY`).
- **Dependencies:** Builds on INV1-R1/R3.
- **Related documents:** Directly reused in `Investigation-006` Phase 5/6 and `Investigation-007` Phase 6 as the template for testing further object pairs.
- **Current implementation impact:** None — a classification rule, not a build item.
- **Depended on by another recommendation:** Yes — the reasoning method is reused explicitly in `Investigation-006`/`007`.
- **Suggested adoption priority:** Medium.

#### INV2-R2
- **Recommendation:** Do not merge `DecisionContext` and `ReflectionResponse` in either direction (rejects Options B, C, D — merge, Reflection-into-Context, Context-into-Reflection).
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-002` Phase 6 (direct merge attempt, fails both directions — null-discriminator vs. fabricated-provenance).
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low (negative constraint, already effectively followed).

#### INV2-R3
- **Recommendation:** A common-parent object unifying `DecisionContext`/`ReflectionResponse`/future similarly-shaped objects (Option E) should not be adopted now, but is recorded as a legitimate future idea, worth revisiting once a third occasioned-or-spontaneous object is actually designed.
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-002` Phase 7 (Option E evaluation).
- **Dependencies:** Contingent on `Investigation-006`'s CaseCondition and `Investigation-007`'s Assumption actually being adopted first (they are the "third object" this recommendation anticipates).
- **Related documents:** `Investigation-006` Open Question 1 (Challenge-acknowledgment shape) implicitly revives this.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low (explicitly deferred by its own source).

---

### Investigation 003 — Decision Drafts vs. Immutable Decision

#### INV3-R1
- **Recommendation:** Adopt a new `DecisionDraft` concept — Case-scoped (via `case_id`, following `Decision`'s own direct precedent, not `DecisionContext`'s narrower one), referencing investor identity, never `decision_id` directly.
- **Architectural area:** Domain Object
- **Supporting evidence:** `Investigation-003` Phase 19 (`SEPARATE_DECISION_DRAFT`), Phases 6–9 (exhaustive rejection of every existing object as a substitute).
- **Dependencies:** None architecturally; is itself a dependency for INV4-R2 (Reconsideration may begin as a Draft), INV5/6's CaseCondition content origination, INV7's Assumption content origination.
- **Related documents:** Directly cited and reused in `Investigation-004`, `005`, `006`, `007`.
- **Current implementation impact:** None — no object exists yet.
- **Depended on by another recommendation:** Yes — heavily; the register's most-cited single recommendation.
- **Suggested adoption priority:** **Critical** (a structural dependency for multiple later recommendations).

#### INV3-R2
- **Recommendation:** Build `DecisionDraft` on the append-only-events-plus-derived-current-state pattern already proven by `SecurityConfirmationEvent`/`ConfirmedSecuritySelection` (Model C) — not a novel persistence philosophy.
- **Architectural area:** Lifecycle
- **Supporting evidence:** `Investigation-003` Phase 10 (Model A/B/C comparison), citing the shipped Security Confirmation package directly.
- **Dependencies:** Depends on INV3-R1 (the object this pattern is applied to).
- **Related documents:** Reused identically in `Investigation-005`/`006` (CaseCondition) and `Investigation-007` (Assumption) — the register's most-reused architectural pattern.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — the pattern itself is the dependency for INV6-R1 and INV7-R2.
- **Suggested adoption priority:** **Critical.**

#### INV3-R3
- **Recommendation:** The commit boundary for a Draft becoming real must remain the existing, unmodified `Decision.register()`/`DecisionContext.capture()` calls; `DecisionDraft` itself never becomes a `Decision`.
- **Architectural area:** Lifecycle
- **Supporting evidence:** `Investigation-003` Phase 11.
- **Dependencies:** Depends on INV3-R1.
- **Related documents:** None.
- **Current implementation impact:** None — preserves existing mechanism unchanged.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High (a hard constraint on any future implementation).

#### INV3-R4
- **Recommendation:** Daily Brief should consume only a narrow summary projection of drafts (existence, subject, resume link) — never full draft content (rationale, confidence).
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-003` Phase 14.
- **Dependencies:** Depends on INV3-R1.
- **Related documents:** The identical principle is reused in `Investigation-005` Phase 12/14 and `Investigation-006` Phase 14.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — cited as precedent in INV5-R8 and INV6-R7.
- **Suggested adoption priority:** Medium.

#### INV3-R5
- **Recommendation:** Any future `draft_id`-style provenance field on `Decision` must be optional and additive, following the `observation_id` precedent — never required, since imported/API/broker-synced Decisions never pass through a draft.
- **Architectural area:** Domain Object
- **Supporting evidence:** `Investigation-003` Phase 16 (hard constraint from the `DecisionSource` taxonomy).
- **Dependencies:** Depends on INV3-R1.
- **Related documents:** The identical constraint pattern is reused in `Investigation-005` Phase 9/16 for `CaseCondition.decision_id`.
- **Current implementation impact:** None — no such field exists yet.
- **Depended on by another recommendation:** Yes — the same reasoning is directly reapplied in INV5-R2.
- **Suggested adoption priority:** Medium.

#### INV3-R6
- **Recommendation:** Reject Options A (transient UI state only — fails Daily Brief requirement), B (Decision gains DRAFT status — destroys core invariant), D (`DecisionContext` doubles as draft — fails on temporal precedence and immutability), E (generic Case Workspace State — collapses into a mislabeled Option C), F (event-only, no current-state projection — dominated by Model C).
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-003` Phase 17.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low (negative constraints, already reflected in INV3-R1's own shape).

---

### Investigation 004 — Decision Review vs. Amendment vs. Supersession

#### INV4-R1
- **Recommendation:** No new ontology is required for Review, Amendment, or Supersession. Review and Reconsideration resolve into the existing `Decision.register()` mechanism (optionally via Draft) or, for outcome-confirmation specifically, the existing `Evaluation` object.
- **Architectural area:** Epistemology
- **Supporting evidence:** `Investigation-004` Phase 17 (`REVIEW_ONLY`), Phases 2, 5, 7.
- **Dependencies:** None architecturally; optionally composes with INV3-R1 (Draft).
- **Related documents:** Directly informs `Investigation-005`'s own Review Trigger analysis.
- **Current implementation impact:** None — confirms existing mechanisms are sufficient.
- **Depended on by another recommendation:** Yes — `Investigation-005` builds its own Review Trigger finding directly on this one.
- **Suggested adoption priority:** High (a confirmed constraint that shapes how later recommendations are scoped).

#### INV4-R2
- **Recommendation:** Supersession must never be stored as a field or flag on `Decision` — always computed by comparing `decided_at`/`recorded_at` across Decisions sharing a subject.
- **Architectural area:** Lifecycle
- **Supporting evidence:** `Investigation-004` Phase 4, 9, 16.
- **Dependencies:** None.
- **Related documents:** Directly reconfirmed and extended by `Investigation-005` Phase 4 for `CaseCondition` supersession.
- **Current implementation impact:** None — a negative constraint.
- **Depended on by another recommendation:** Yes — INV6-R4 reuses the identical derive-don't-store logic.
- **Suggested adoption priority:** High.

#### INV4-R3
- **Recommendation:** Amendment (as UX-009 uses the word) should be deferred entirely, pending the separate design of whatever eventually holds Monitoring/Invalidation Conditions — it is not a property of `Decision` and nothing currently exists for it to amend.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-004` Phase 3.
- **Dependencies:** Blocks on `Investigation-005`/`006`'s CaseCondition work being adopted first.
- **Related documents:** Directly resolved (the "amendment" concept is realized as `CaseConditionEvent` revisions) in `Investigation-006` Phase 11.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — `Investigation-006`'s own versioning recommendation (INV6-R2) is the eventual resolution of this deferral.
- **Suggested adoption priority:** Medium.

#### INV4-R4
- **Recommendation:** Reject Model B (mutable `Decision` status — the most severe failure of any option considered in the series), Model C (dedicated Review object — not supported by UX-009's own text), Model D (general Amendment object — premature), Model E (Decision lifecycle object — an unrequired materialized view of a freely-derivable relationship), Model F (full event sourcing for Decision itself — solves an already-solved problem).
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-004` Phase 18.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

---

### Investigation 005 — Review Trigger vs. Monitoring vs. Invalidation

#### INV5-R1
- **Recommendation:** Adopt a new `CaseCondition` concept, Case-scoped by default, with an optional `decision_id` back-reference. *(Superseded in shape, not in substance, by `Investigation-006`'s own leaner two-object refinement — INV6-R1 — see relationship note.)*
- **Architectural area:** Domain Object
- **Supporting evidence:** `Investigation-005` Phase 20 (`CASE_CONDITION`).
- **Dependencies:** Builds on INV3-R1/R2 (Draft, event-sourcing pattern) and INV4-R1 (Review resolves via existing mechanisms).
- **Related documents:** Directly refined by `Investigation-006`; this entry is the *unrefined* original — retained per the sprint's own "keep both, note the relationship" instruction.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — INV6-R1 is its direct refinement; INV7's Assumption/CaseCondition relationship (INV7-R3) depends on this concept existing.
- **Suggested adoption priority:** **Critical** (superseded in detail by INV6-R1, but the underlying concept is load-bearing for INV6 and INV7).

#### INV5-R2
- **Recommendation:** `atlas/monitoring` should be kept fully separate — not reused, not extended, not wrapped, not replaced. It is a stateless, Decision/Case-unaware legacy scoring utility whose own comparison baseline is synthetically fabricated, not a working-but-dormant system.
- **Architectural area:** Architecture
- **Supporting evidence:** `Investigation-005` Phase 2, 17 (full read of `atlas/monitoring/engine.py`).
- **Dependencies:** None.
- **Related documents:** Corrects a characterization made in `Decision-Workspace-Architecture-Resolution-Sprint-1.md` (pre-series).
- **Current implementation impact:** None — a negative constraint on future work.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High (prevents a likely future implementation mistake if not disclosed).

#### INV5-R3
- **Recommendation:** "Review Trigger" should not be modeled as a single object — resolve it as a Daily-Brief-layer projection unioning several sources: time-based `CaseCondition`s past due, state-based `CaseCondition`s evaluated true, Change-Intelligence-detected recommendation shifts, and plain user-initiated entry.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-005` Phase 5, 10, 12.
- **Dependencies:** Depends on INV5-R1/INV6-R1 (CaseCondition existing) and the already-shipped Change Intelligence package.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV5-R4
- **Recommendation:** Automatic Review Triggers from Atlas Recommendation changes should reuse the already-existing, already-shipped Change Intelligence computation — no new ontology is needed for this.
- **Architectural area:** Implementation Guidance
- **Supporting evidence:** `Investigation-005` Phase 14.
- **Dependencies:** None — the dependency (Change Intelligence) already exists in production.
- **Related documents:** None.
- **Current implementation impact:** None — a reuse recommendation, not a new build.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium (low-cost, high-leverage — already-built capability, just needs wiring).

#### INV5-R5
- **Recommendation:** Time-based and state-based conditions should share one object shape (`CaseCondition`) but never one evaluation mechanism — calendar comparison and live-data threshold comparison remain structurally distinct processes.
- **Architectural area:** Lifecycle
- **Supporting evidence:** `Investigation-005` Phase 11, citing the already-shipped `_is_thesis_stale` fixed 90-day threshold as existing precedent for this exact split.
- **Dependencies:** Depends on INV5-R1/INV6-R1.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV5-R6
- **Recommendation:** Portfolio-scoped conditions (e.g., concentration limits) are explicitly not covered by `CaseCondition` — a real, disclosed gap, not silently claimed as solved.
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-005` Phase 13, 19.
- **Dependencies:** None — a disclosed limitation, not a build item.
- **Related documents:** Restated, unresolved, in `Investigation-006` Phase 9/19.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low (explicitly out of scope for current recommendations; flagged for future work).

#### INV5-R7
- **Recommendation:** Reject Option A (Monitoring owns everything — a misleading relabeling of building something new), Option C (separate `MonitoringCondition` + `ReviewSchedule` — an unjustified structural split), Option E (fully generic Watch Condition across Security/Case/Portfolio — under-differentiates genuinely different scopes), Option F (no new ontology, fully derived — forecloses automated detection, a real and significant cost).
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-005` Phase 18.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

---

### Investigation 006 — CaseCondition: Definition, Predicate, Lifecycle & Evaluation

#### INV6-R1
- **Recommendation:** Refine `CaseCondition` to exactly two objects — a stable `CaseCondition` identity (the definition) plus one unified `CaseConditionEvent` stream, covering both revisions and evaluation transitions as different event types. This is the adopted shape; **it directly supersedes INV5-R1's own less-specified proposal**, without contradicting its underlying concept.
- **Architectural area:** Domain Object
- **Supporting evidence:** `Investigation-006` Phase 18 (`CASE_CONDITION_WITH_EVENT_STREAM`), Phases 3, 4, 10, 11, 12 (four independent phases converging on the same shape).
- **Dependencies:** Depends on INV3-R2 (event-sourcing pattern), INV5-R1 (the concept being refined).
- **Related documents:** Supersedes INV5-R1 in detail. Cited as precedent by `Investigation-007` (Assumption's own identical shape, INV7-R2).
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — INV7-R2 directly reuses this shape.
- **Suggested adoption priority:** **Critical.**

#### INV6-R2
- **Recommendation:** "Satisfied condition" and "Detected event" should be modeled as the same underlying event, not two — both describe the same transition from two angles.
- **Architectural area:** Lifecycle
- **Supporting evidence:** `Investigation-006` Phase 4.
- **Dependencies:** Depends on INV6-R1.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV6-R3
- **Recommendation:** Monitoring and Invalidation Conditions are the same object type, differentiated by a role field — never separate aggregates. *(Reconfirms `Investigation-005`'s own finding independently.)*
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-006` Phase 5.
- **Dependencies:** Depends on INV6-R1.
- **Related documents:** Reconfirms `Investigation-005` Phase 7's identical finding — recorded as two independent confirmations, not merged, per the sprint's own instruction.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV6-R4
- **Recommendation:** Only meaningful evaluation transitions should ever be persisted as events — routine "still not met" re-checks must never be stored.
- **Architectural area:** Lifecycle
- **Supporting evidence:** `Investigation-006` Phase 3.
- **Dependencies:** Depends on INV6-R1.
- **Related documents:** Reuses the "derive, don't store" principle from INV4-R2.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV6-R5
- **Recommendation:** `CaseCondition` scope must remain Case-first, never Portfolio — Portfolio-scoped conditions remain a distinct, unsolved sibling concept. *(Restates INV5-R6, kept as a separate confirmation per instruction.)*
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-006` Phase 9, 19.
- **Dependencies:** None.
- **Related documents:** Restates `Investigation-005` Phase 13/19.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

#### INV6-R6
- **Recommendation:** Unedited acceptance of an Atlas-proposed condition must follow `ADR-002` C-02's own authorship model exactly (labeled "Atlas Suggested / User Accepted") — never silently relabeled "User Authored."
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-006` Phase 8.
- **Dependencies:** Depends on `ADR-002` C-02 (already-accepted, pre-series governance).
- **Related documents:** The identical rule is recommended again, independently, for Assumption in `Investigation-007` (INV7-R6) and its gap for the other four epistemic objects is disclosed in `Investigation-008` (INV8-R4).
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV6-R7
- **Recommendation:** Daily Brief should consume only a narrow, derived projection over Detected Events — never raw condition definitions or raw per-check evaluations. *(Extends INV3-R4's identical principle to CaseCondition.)*
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-006` Phase 14.
- **Dependencies:** Depends on INV6-R1/R2; restates INV3-R4's principle.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV6-R8
- **Recommendation:** Reject Model A (mutable condition rows), Model E (fully derived — legitimate as a minimal option, not chosen, since it forecloses meaningful-transition detection), Model F (separate Monitoring aggregate — an unjustified structural split given the role-not-kind finding in INV6-R3).
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-006` Phase 16.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

---

### Investigation 007 — The Nature of Assumptions

#### INV7-R1
- **Recommendation:** Adopt a new, separate `Assumption` concept — Decision-anchored identity, free text, Atlas-proposable, investor-confirmable/editable.
- **Architectural area:** Domain Object
- **Supporting evidence:** `Investigation-007` Phase 18 (`SEPARATE_ASSUMPTION`), Phase 17 (exhaustive rejection of every existing object as a substitute).
- **Dependencies:** Builds on INV3-R2 (event-sourcing pattern) and the "occasioned/unoccasioned" method from INV2-R1.
- **Related documents:** Reconfirmed and sharpened by `Investigation-008`.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — `Investigation-008`'s entire analysis is built on this recommendation surviving genuine re-testing.
- **Suggested adoption priority:** **Critical.**

#### INV7-R2
- **Recommendation:** `Assumption`'s lifecycle should use the identical event-stream pattern established for `CaseCondition` (INV6-R1) — a stable identity plus append-only revision/challenge/retire events.
- **Architectural area:** Lifecycle
- **Supporting evidence:** `Investigation-007` Phase 10, 11.
- **Dependencies:** Depends on INV7-R1 and INV6-R1 (the pattern being reused).
- **Related documents:** Third reuse in the series of the Security-Confirmation-derived event pattern.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High.

#### INV7-R3
- **Recommendation:** `Assumption` and `CaseCondition` should remain a loose, optional cross-reference — never merged, never one contained by the other.
- **Architectural area:** Relationship
- **Supporting evidence:** `Investigation-007` Phase 6.
- **Dependencies:** Depends on INV6-R1 and INV7-R1 both existing.
- **Related documents:** Reconfirmed in `Investigation-008` Phase 12.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV7-R4
- **Recommendation:** `CaseCondition` should primarily, though not exclusively, target `Assumption` rather than `Hypothesis`, `Conclusion`, or `Judgment`.
- **Architectural area:** Relationship
- **Supporting evidence:** `Investigation-007` Phase 6, citing `Investigation-006` Phase 7.
- **Dependencies:** Depends on INV6-R1, INV7-R1.
- **Related documents:** Reconfirmed and generalized in `Investigation-008` Phase 12.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — INV8-R3 restates and confirms this.
- **Suggested adoption priority:** Medium.

#### INV7-R5
- **Recommendation:** Truth should never be tracked as a binary verdict for `Assumption` — only "currently supported" vs. "currently challenged," never true/false/settled/rejected.
- **Architectural area:** Epistemology
- **Supporting evidence:** `Investigation-007` Phase 8.
- **Dependencies:** Depends on INV7-R1.
- **Related documents:** The same discipline is confirmed to hold, without exception, across the whole five-object epistemic family in `Investigation-008` Phase 14.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High (a core semantic invariant, not a detail).

#### INV7-R6
- **Recommendation:** Unedited acceptance of an Atlas-proposed `Assumption` should follow `ADR-002` C-02's authorship model precisely. *(Parallels INV6-R6 for CaseCondition.)*
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-007` Phase 7.
- **Dependencies:** Depends on INV7-R1; depends on pre-series `ADR-002` C-02.
- **Related documents:** `Investigation-008` Phase 15 discloses this is the *only* member of the five-object epistemic family integrated with C-02 this way.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV7-R7
- **Recommendation:** A future `Assumption` object should feed `DE-005`'s own existing thesis-strength synthesis directly — a genuinely strong, already-anticipated integration point, stronger than any comparable Atlas Memory hook found elsewhere in the series.
- **Architectural area:** Memory
- **Supporting evidence:** `Investigation-007` Phase 13, citing `DE-005` §3's own pre-existing text.
- **Dependencies:** Depends on INV7-R1.
- **Related documents:** `Investigation-006`'s own comparable finding for `CaseCondition` (Phase 13) is explicitly weaker — only a "disclosed future extension," not an already-anticipated one.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High (a rare case where the integration path is unusually low-risk and well-evidenced).

#### INV7-R8
- **Recommendation:** The existing `OutlookAssumption` (`atlas/analysis_engine/outlook.py`) naming collision should never be conflated with the new `Assumption` concept in any future naming, documentation, or code.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-007` Phase 5 (headline finding), a self-disclosed-by-neither-side naming collision found independently by this investigation.
- **Dependencies:** None.
- **Related documents:** The third instance of a naming-overload pattern in the series (after "Reflection" and "Evaluation").
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium (real risk of a future implementation mistake if undisclosed).

#### INV7-R9
- **Recommendation:** Reject Model A (Assumption as free text on `Decision.reason` — loses individual trackability), Model B (Assumption as `CaseCondition` — forces an unneeded evaluation lifecycle onto content that doesn't inherently need one), Model F (Assumption as a `KnowledgeReference`/Knowledge object — wrong shape, reference-based not proposition-based).
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-007` Phase 16.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

---

### Investigation 008 — Assumption vs. Hypothesis vs. Conclusion vs. Judgment

#### INV8-R1
- **Recommendation:** Keep `Assumption`, `Hypothesis`, `Evidence`, `Conclusion`, and `Judgment` as five fully distinct objects — no merge is justified for any pair.
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-008` Phase 20 (`KEEP_ALL_DISTINCT`), Phase 17 (exhaustive substitution testing).
- **Dependencies:** Depends on INV7-R1 surviving re-testing (it does).
- **Related documents:** Independently reconfirms `Investigation-007`'s own conclusion via differently-angled testing, not by assumption.
- **Current implementation impact:** None — `Hypothesis`, `Evidence`, `Conclusion`, `Judgment` already exist unchanged; `Assumption` remains proposed only (INV7-R1).
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High (settles a question that would otherwise recur).

#### INV8-R2
- **Recommendation:** Model the relationships among these five objects as a loosely-coupled reasoning graph (optional, typed references) — never a mandatory pipeline, and never assume the "Core Loop" naming implies an enforced sequence.
- **Architectural area:** Relationship
- **Supporting evidence:** `Investigation-008` Phase 10, 13, 18 (Model B/F).
- **Dependencies:** None.
- **Related documents:** Directly reconfirmed from the implementation side in `Investigation-009` Phase 9.
- **Current implementation impact:** None — describes existing behavior accurately, requires no change.
- **Depended on by another recommendation:** Yes — `Investigation-009`'s own Phase 9 finding builds on this.
- **Suggested adoption priority:** Medium.

#### INV8-R3
- **Recommendation:** `CaseCondition` should primarily, though not exclusively, watch `Assumption`s among this five-object family. *(Restates and generalizes INV7-R4.)*
- **Architectural area:** Relationship
- **Supporting evidence:** `Investigation-008` Phase 12 (Assumption → CaseCondition, "not reopening CaseCondition itself").
- **Dependencies:** Depends on INV6-R1, INV7-R1.
- **Related documents:** Restates `Investigation-007` Phase 6/INV7-R4.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low (a confirmation, not new guidance).

#### INV8-R4
- **Recommendation:** The `ADR-002` C-02 authorship-transfer model should eventually be extended to `Hypothesis`, `Evidence`, `Conclusion`, and `Judgment` — currently only `Assumption` is integrated with it, a disclosed, real inconsistency across the epistemic family.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-008` Phase 15.
- **Dependencies:** Depends on `ADR-002` C-02 (pre-series) and INV7-R6.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low (disclosed gap, no urgency established).

#### INV8-R5
- **Recommendation:** No object in this family should ever silently change type — a `Hypothesis` "becoming" an `Assumption`, or a `Conclusion` "becoming" a `Judgment," is always a new capture, never a mutation.
- **Architectural area:** Lifecycle
- **Supporting evidence:** `Investigation-008` Phase 9, 10 (Hypothesis→Conclusion, Conclusion→Judgment transition tests), Invariants section.
- **Dependencies:** None — a restated core immutability invariant, applied to this family specifically.
- **Related documents:** Consistent with every prior investigation's own immutability findings.
- **Current implementation impact:** None — already true of every implemented object in the family.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High (a core semantic invariant).

#### INV8-R6
- **Recommendation:** `Evidence` must never be treated as automatically proving a claim — it carries a required direction (`SUPPORTS`/`CHALLENGES`) relative to whatever it bears on, never a verdict.
- **Architectural area:** Epistemology
- **Supporting evidence:** `Investigation-008` Phase 4, Invariants section.
- **Dependencies:** None — describes the already-implemented `Evidence.direction` field accurately.
- **Related documents:** None.
- **Current implementation impact:** None — already true of the implemented object.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium (worth stating explicitly even though already true, since it governs how future features may use Evidence).

#### INV8-R7
- **Recommendation:** Reject Model A (linear pipeline with Assumption "before" Hypothesis — no such enforcement exists), Model C (Assumption as accepted Hypothesis — the epistemic-stance distinction persists after acceptance), Model D (Judgment as accepted Conclusion — fails on two independent structural grounds), Model E (minimal ontology, Assumption/Judgment presentation-only — contradicts both the DE-005 integration evidence and OE-002's own normative Judgment classification).
- **Architectural area:** Ontology
- **Supporting evidence:** `Investigation-008` Phase 18.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

---

### Investigation 009 — Ontology Authority and Reconciliation

#### INV9-R1
- **Recommendation:** For this document series and its own future continuations, treat the implemented `atlas/core/domain/*` objects as primary/normative authority. Treat Reasoning Foundations and Domain Object Architecture as informative but not currently binding.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-009` Phase 19 (`IMPLEMENTED_CORE_LOOP_IS_NORMATIVE`), Phases 1–14 (full three-track comparison).
- **Dependencies:** Retroactively governs how every prior investigation's own conclusions should be read (all were already, in practice, grounded this way).
- **Related documents:** Refined into a general process by `Investigation-010`; the series' own status is further resolved by `Investigation-011`.
- **Current implementation impact:** None — a governing-posture recommendation, not a build item.
- **Depended on by another recommendation:** Yes — foundational to INV10-R1 and INV11-R1.
- **Suggested adoption priority:** **Critical.**

#### INV9-R2
- **Recommendation:** A formal, `ADR-005`-equivalent reconciliation between the implemented Core Loop and Domain Object Architecture should eventually be produced — recommended, not mandated, and not designed by this investigation.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-009` Phase 16, 19.
- **Dependencies:** Depends on INV9-R1's own three-track finding.
- **Related documents:** Directly taken up as the central subject of `Investigation-010`.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — `Investigation-010`'s entire scope is built on this recommendation.
- **Suggested adoption priority:** High.

#### INV9-R3
- **Recommendation:** Reject the candidate three-layer hierarchy model (Reasoning Foundations → Domain Object Model → Implementation) — it does not survive contradiction and should not be adopted as a description of how the tracks relate.
- **Architectural area:** Architecture
- **Supporting evidence:** `Investigation-009` Phase 12.
- **Dependencies:** None.
- **Related documents:** Directly informs `Investigation-010`'s own rejection of the equivalent Model D there.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — INV10-R6 (rejecting Model D) reuses this finding.
- **Suggested adoption priority:** Medium.

#### INV9-R4
- **Recommendation:** Reject treating OE-002 as unilaterally normative over implementation (Model B), treating Reasoning Foundations as governing all ontology (Model C), or treating the current, undisclosed state as acceptable with no change (Model F).
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-009` Phase 17.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

---

### Investigation 010 — Ontology Reconciliation Process

#### INV10-R1
- **Recommendation:** Adopt "Disclosed Pluralism with an Explicit Reconciliation Process" (Model G): tracks remain independently governed by default; a genuine, demonstrated forcing function is required before reconciliation between any two tracks is undertaken; when undertaken, reconciliation follows the Domain Object Architecture Change Protocol as a *method template* only, never as a content mandate.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-010` Phase 17, Phases 1–14.
- **Dependencies:** Depends on INV9-R1, INV9-R2.
- **Related documents:** Directly extended by `Investigation-011`'s own treatment of the investigation series' own status.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — `Investigation-011` builds its entire own governance model on this one.
- **Suggested adoption priority:** **Critical.**

#### INV10-R2
- **Recommendation:** Reconciliation's minimum required output is always at least a documented decision (a historical decision record) — it need not change either track's actual content; `ADR-005` is direct proof a "we remain separate, by mutual declaration" outcome is a complete, sufficient act of reconciliation.
- **Architectural area:** Process
- **Supporting evidence:** `Investigation-010` Phase 8.
- **Dependencies:** Depends on INV10-R1.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV10-R3
- **Recommendation:** Supersession, wherever it eventually applies (to any track, or to this investigation series itself), requires an identified replacing decision and an explicit status change — never silent deletion, never mere recency.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-010` Phase 10, citing `atlas_domain_object_architecture/Doctrine.md` §14 directly.
- **Dependencies:** None.
- **Related documents:** Directly reused, reflexively, by `Investigation-011` Phase 11 for the investigation series itself.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — INV11-R5 applies this rule to the series itself.
- **Suggested adoption priority:** High.

#### INV10-R4
- **Recommendation:** Historical records, including every document in this investigation series, must remain permanently recoverable regardless of any future reconciliation's outcome — never deleted, only marked superseded with the superseding document named explicitly.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-010` Phase 11.
- **Dependencies:** None.
- **Related documents:** Directly reused by `Investigation-011` Phase 11.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — INV11-R5.
- **Suggested adoption priority:** High.

#### INV10-R5
- **Recommendation:** A contradiction (Phase 7's precise sense — two claims both currently claiming settled status about the same fact) must be named the moment it is found; an omission or alternative model must not be inflated into a contradiction requiring urgent resolution.
- **Architectural area:** Process
- **Supporting evidence:** `Investigation-010` Phase 7.
- **Dependencies:** None.
- **Related documents:** Directly reused as the precise test in `Investigation-011` Phase 12.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes.
- **Suggested adoption priority:** Medium.

#### INV10-R6
- **Recommendation:** Reject Model A (implementation-first alone — undervalues real doctrinal work), Model B (ontology-first alone, read retroactively — would invalidate ten real, running objects with no reconciliation ever performed), Model C (documentation-first — fails directly against normative-authority §9), Model E (living architecture alone — no reconciliation discipline, the exact condition that let the Track 1↔3 fork go unnamed for nine investigations), Model F (independent parallel tracks alone — legitimate only if disclosed, which Model G's own process adds).
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-010` Phase 18.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

#### INV10-R7
- **Recommendation:** This investigation series itself should be recognized as a fourth, previously-unacknowledged quasi-track and its own authority status formally addressed — not left implicit.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-010` Phase 15, 16 (Open Question 2).
- **Dependencies:** None.
- **Related documents:** **Directly answered by `Investigation-011`** — see INV11-R8's relationship note (the answer is "advisory ADR-precursor input," not "peer-authority fourth track").
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — this is precisely the open question `Investigation-011` exists to resolve.
- **Suggested adoption priority:** High.

---

### Investigation 011 — Authority of the ADR Investigation Series

#### INV11-R1
- **Recommendation:** Adopt "Permanent ADR-Precursor Record" (Model G) as the investigation series' own governance model: the series observes and advises; it never governs, replaces, or self-converts into architecture.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-011` Phase 17, Phases 1–13, grounded in empirical verification (grep) of all ten prior documents' own actual behavior.
- **Dependencies:** Depends on INV10-R1 and INV10-R7.
- **Related documents:** Governs how every recommendation in this register itself should be treated (see Section 1, point 1).
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — this recommendation governs the standing of every other entry in this register.
- **Suggested adoption priority:** **Critical.**

#### INV11-R2
- **Recommendation:** Investigation documents should borrow, without formally subordinating themselves to, the existing status/supersession/historical-integrity vocabulary already defined in `atlas_domain_object_architecture/Doctrine.md` §8, §11, §14 — no new, bespoke doctrine for the series is justified.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-011` Phase 13.
- **Dependencies:** Depends on INV11-R1.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Medium.

#### INV11-R3
- **Recommendation:** No investigation document may claim Final, binding, or normative status for itself, now or in any future document in the series.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-011` Phase 3, 9, Invariants section.
- **Dependencies:** Depends on INV11-R1.
- **Related documents:** None.
- **Current implementation impact:** None — already the uniform practice, confirmed empirically.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High (a binding constraint on this very sprint's own future work).

#### INV11-R4
- **Recommendation:** Every ADR Candidate section a future investigation produces must remain explicitly labeled an outline, never presented as the ADR itself.
- **Architectural area:** Process
- **Supporting evidence:** `Investigation-011` Phase 2, Invariants section.
- **Dependencies:** Depends on INV11-R1.
- **Related documents:** None.
- **Current implementation impact:** None — already the uniform practice, confirmed empirically (4/4 occurrences checked).
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High.

#### INV11-R5
- **Recommendation:** No investigation is ever deleted; a later investigation or formal ADR that reaches a different conclusion on the same narrow question supersedes the earlier one explicitly, leaving it fully readable. *(Applies INV10-R3/R4 reflexively to the series itself.)*
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-011` Phase 11, Invariants section.
- **Dependencies:** Depends on INV10-R3, INV10-R4, INV11-R1.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High.

#### INV11-R6
- **Recommendation:** Conversion of any investigation's findings into architecture always requires a separate, later act performed by an appropriately authorized track's own process — never accomplished by the investigation itself, and never by mere continued existence as a committed file.
- **Architectural area:** Process
- **Supporting evidence:** `Investigation-011` Phase 3, 9.
- **Dependencies:** Depends on INV11-R1.
- **Related documents:** Directly governs how every recommendation in *this* register should eventually be actioned — see Section 7.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** Yes — this is the rule the entire ADR Adoption Program's own future sprints must satisfy.
- **Suggested adoption priority:** **Critical.**

#### INV11-R7
- **Recommendation:** If a genuine contradiction between two future investigations is found, the correct resolution process is a third, later investigation that directly re-tests the disputed claim using the same evidence-based method — not an ad hoc adjudication by either original document.
- **Architectural area:** Process
- **Supporting evidence:** `Investigation-011` Phase 12.
- **Dependencies:** Depends on INV11-R1, INV10-R5.
- **Related documents:** None.
- **Current implementation impact:** None — untested in practice, per the investigation's own Open Question 3.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low (a contingency rule, not yet exercised).

#### INV11-R8
- **Recommendation:** Answers `Investigation-010`'s own Open Question 2: the series should be treated as advisory ADR-precursor input, not as a peer-authority fourth track alongside the other three.
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-011` Phase 16, item 2 (explicit statement that this answers, rather than reverses, a genuinely open prior question).
- **Dependencies:** Depends on INV10-R7, INV11-R1.
- **Related documents:** Directly resolves INV10-R7.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** High.

#### INV11-R9
- **Recommendation:** Reject Model A (research only — undersells the decisive, verdict-producing structure actually observed), Model C (architecture authority — directly falsified by the empirical grep record), Model D (independent reconciliation track — overstates what investigations have ever actually completed), Model E (living archive alone — correct on permanence, incomplete on function), Model F (temporary working documents — directly contradicted by the series' own practice of never deleting anything).
- **Architectural area:** Governance
- **Supporting evidence:** `Investigation-011` Phase 14.
- **Dependencies:** None.
- **Related documents:** None.
- **Current implementation impact:** None.
- **Depended on by another recommendation:** No.
- **Suggested adoption priority:** Low.

---

## 3. Dependency Overview

**Critical-path chain, as evidenced by the "Depended on by another recommendation" field above:**

```
INV9-R1 (implementation-first posture, this series)
   └─→ INV10-R1 (Disclosed Pluralism + Explicit Reconciliation)
          └─→ INV11-R1 (series is a Permanent ADR-Precursor Record)
                 └─→ INV11-R6 (conversion always requires an authorized track's own process)
                        └─→ governs how every other recommendation in this register may ever be adopted

INV3-R1 (DecisionDraft) + INV3-R2 (event-sourcing pattern, from Security Confirmation)
   ├─→ INV5-R1 → INV6-R1 (CaseCondition, refined shape)
   │       └─→ INV7-R3/R4, INV8-R3 (Assumption↔CaseCondition relationship)
   └─→ INV7-R1 → INV7-R2 (Assumption, same event-sourcing pattern)
          └─→ INV8-R1 (KEEP_ALL_DISTINCT, independently reconfirms INV7-R1)

INV4-R1 (Review resolves via existing mechanisms, no new ontology)
   └─→ informs INV5's own Review Trigger analysis (INV5-R3)
```

**Two independent root dependencies exist, and neither strictly precedes the other in this register's own numbering:** the *governance* chain (INV9→10→11) determines whether *any* content recommendation can ever legitimately become architecture; the *content* chain (INV3→5/6→7/8) determines *what* that architecture should say if and when it is adopted. Per `Investigation-011`'s own INV11-R6, the governance chain's conclusion (conversion requires an authorized track) applies to the content chain's own conclusions regardless of which was produced first — meaning **Sprint 2 cannot adopt any content recommendation without also, first or concurrently, addressing how conversion is actually supposed to happen.**

---

## 4. Areas With High Recommendation Density

| Architectural area | Count | Notable concentration |
|---|---|---|
| Governance | 16 | Dominant in INV9–011 (13 of 16), reflecting the series' own late pivot to self-examination |
| Domain Object | 6 | INV1-R1, INV3-R1, INV5-R1, INV6-R1, INV7-R1, INV8-R1 — one per investigation that proposes or confirms an object's shape |
| Ontology | 10 | Concentrated in the "reject the alternatives" entries (INV3-R6, INV4-R4, INV5-R7, INV6-R8, INV7-R9, INV8-R7) plus core distinctness findings |
| Process | 4 | Exclusively in INV10/011 — a category that essentially did not exist before the series turned self-referential |
| Relationship | 4 | INV7/008's Assumption↔CaseCondition and Assumption↔Hypothesis/Judgment findings |
| Lifecycle | 5 | INV3-R2/R3, INV6-R2/R4, INV8-R5 |
| Epistemology | 3 | INV4-R1, INV7-R5, INV8-R6 |
| Architecture | 2 | INV5-R2, INV9-R3 |
| Memory | 1 | INV7-R7 |
| Implementation Guidance | 3 | INV1-R2, INV5-R4, INV1-R4–R6 (grouped) |
| Case, Decision, Monitoring, Other | 0 each | No recommendation was found to fit these as a *primary* category — Case and Decision concerns are consistently secondary to a Domain Object or Ontology classification; Monitoring concerns route through Governance (Daily Brief projection rules) or Ontology (CaseCondition scope) instead |

**Governance's dominance is itself a finding worth surfacing, not just a tally:** more than a quarter of all recommendations in the register concern *how Atlas should decide things* rather than *what Atlas should contain* — a direct, quantitative confirmation of `Investigation-010`/`011`'s own qualitative conclusion that the series' center of gravity shifted partway through.

---

## 5. Candidate Adoption Waves

Grouped by dependency order (Section 3), not by investigation number or subjective importance, per the sprint's own instruction.

**Wave 0 — Governance posture (must be addressed before any other wave can legitimately proceed, per INV11-R6):** INV9-R1, INV10-R1, INV11-R1, INV11-R2, INV11-R3, INV11-R4, INV11-R5, INV11-R6, INV11-R8.

**Wave 1 — Foundational, no-new-ontology confirmations (low risk, reuse existing objects only):** INV1-R1, INV1-R2, INV1-R3, INV2-R1, INV2-R2, INV4-R1, INV4-R2.

**Wave 2 — The Draft/event-sourcing pattern (a genuine new-object dependency for Waves 3–4):** INV3-R1, INV3-R2, INV3-R3, INV3-R5.

**Wave 3 — CaseCondition (depends on Wave 2):** INV6-R1 (adopt this shape; treat INV5-R1 as superseded-in-detail), INV6-R2 through INV6-R7.

**Wave 4 — Assumption (depends on Wave 2 and, per INV7-R3/R4, benefits from Wave 3 existing first though does not strictly require it):** INV7-R1, INV7-R2, INV7-R5, INV7-R6, INV7-R7, INV8-R1, INV8-R2, INV8-R5, INV8-R6.

**Wave 5 — Presentation/integration guidance (depends on Waves 2–4 existing):** INV3-R4, INV5-R3, INV5-R4, INV5-R5, INV6-R7.

**Not yet wave-assignable — disclosed gaps, not adoption candidates:** INV5-R6/INV6-R5 (Portfolio-scoped conditions), INV1-R4–R6 (naming/discipline risks), INV8-R4 (C-02 extension to the older epistemic objects), INV9-R2 (Track 1↔3 reconciliation itself).

---

## 6. Open Questions

Compiled by investigation, exactly as each source document stated them — not recommendations, and not resolved here.

- **Investigation 001:** Should `portfolio_relevance` be renamed? Where should assumption-confirmation live? Where should per-item Challenge acknowledgment live?
- **Investigation 002:** Should "Reflection" naming be disambiguated in `Atlas-Alpha-Baseline-v1.0.md`? Is "Reflection Timeline" the same as `ATLAS-010 — Reflection History`? Does `DecisionContext` need an owner-scoped retrieval surface? Is `ReflectionResponse`'s unbounded multiplicity intentional?
- **Investigation 003:** Is a superseded draft retained as provenance or discarded? Are "abandon" and "delete" the same action? Should drafts expire? Should multiple simultaneous drafts per Case be permitted? Should Case-only scoping be revisited before multi-user support? Should abandoned-draft events be retained indefinitely at the storage layer? Does offline/mobile editing need its own design? Should `Decision` gain an optional `draft_id`?
- **Investigation 004:** Should Daily Brief have its own explicit "superseded/stale" signal? How should Reconsideration compose with Draft in product terms? Should `Evaluation` cover reasoning-quality review for Outcome-less decisions? Should Monitoring/Invalidation amendment reuse the Security Confirmation pattern? Is the still-missing review-trigger home the next investigation needed?
- **Investigation 005:** How should Portfolio-scoped conditions be represented? Should `CaseCondition` content always originate via Draft? What is the actual scheduling/evaluation mechanism for state-based conditions? Should Daily Brief's projection be its own service? Does the collaboration Case-scoping ambiguity need its own investigation?
- **Investigation 006:** Should Assumption confirmation be modeled as a kind of `CaseCondition`? Is "Deleted" a real event type or does "Retired" cover it? How should Decision Timeline/Memory be extended to consume `CaseCondition` events? Does provider-synchronized evaluation need a distinct trust model?
- **Investigation 007:** Should the `CaseCondition`↔Assumption cross-reference be enforced? Is "Rejected" its own event type? Should `OutlookAssumption` be renamed? What is the precise DE-005 feed mechanism?
- **Investigation 008:** Should the C-02 authorship gap for the four older objects be closed? Does provider-synchronized Evidence honestly satisfy "the investor regarded this as evidence"? What happens to the family's authorship framing under future automated reasoning? Should OE-002/Reasoning-Foundations and implementation ever be reconciled — whose Judgment wins? Should a future `ReasoningTrace` formally connect all five objects?
- **Investigation 009:** Who owns the Track 1↔3 reconciliation, and when? Should Track 3's dormant authority claim be formally revised or withdrawn? Should Track 2's Reasoning/Act account be integrated before automated reasoning is built? Is Track 2's Knowledge the same as Track 3's `KnowledgeReference` target? Should the three-track inventory be kept current?
- **Investigation 010:** Who owns the Track 1↔3 reconciliation (restated)? Should the series formally register as a track — **now answered by `Investigation-011` (INV11-R8): no, advisory input instead.** Is Judgment's three-way definitional difference a contradiction or a refinement? What forcing function would justify convergence now? Should the Change Protocol be formally cross-track-adapted?
- **Investigation 011:** Who owns actual ADR conversion of any given investigation's findings? How should the production/conversion backlog be managed? Is "write a third, testing investigation" adequate, untested in practice? Should this document itself be treated as authoritative about the series' status, or does it remain non-binding about itself too?

---

## 7. Suggested Sprint 2 Scope

Per `Investigation-011`'s own INV11-R6 (conversion always requires a separately-authorized track's own process, never self-conversion), Sprint 2 cannot itself adopt any recommendation — that would violate the very governance model Wave 0 exists to establish. The recommended scope for Sprint 2 is therefore:

1. **Formally address Wave 0** — determine, as its own explicit decision (not inherited from this register), whether Atlas accepts `Investigation-009`/`010`/`011`'s own governance recommendations (INV9-R1, INV10-R1, INV11-R1 through R8) as the operating model for everything that follows. This is a precondition for every other wave, per Section 3's own dependency finding.
2. **Assign a real owner and timeline to INV9-R2 / INV10-R7's own open reconciliation question**, since no document in the register names one, and `Investigation-011` Phase 16 independently confirms this same gap recurs at the single-recommendation level.
3. **Deduplicate and formally merge INV5-R1 into INV6-R1** (and, on the same pattern, confirm whether any other "refined by a later investigation" pairs exist beyond the two explicitly noted in this register) — the sprint's own instruction not to deduplicate yet means this remains Sprint 2's first real content task once Wave 0 is settled.
4. **Begin drafting the first real ADR** — following whichever track Wave 0 designates as authorized to do so — for the single recommendation with the strongest, most self-contained evidentiary basis in the register: **INV6-R1 (CaseCondition, refined shape)**, on the grounds that it is Critical priority, has a fully worked ontology (`Investigation-006`, twelve phases), reuses an already-proven persistence pattern (Security Confirmation), and its own dependency chain (INV3-R1/R2) is itself already well-evidenced.
5. **Do not begin implementation work of any kind** — Sprint 2, like Sprint 1, remains within the investigation/inventory/decision-preparation phase until Wave 0's own governance question is actually, formally settled.

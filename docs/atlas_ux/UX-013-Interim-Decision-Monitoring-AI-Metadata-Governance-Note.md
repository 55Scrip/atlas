# UX-013 — Interim Decision, Monitoring & AI-Metadata Governance Note

Status: Interim — Provenance Classified, Not Canonical

---

## Governing Introduction

This document implements the documentary trust-boundary correction required by `ADR-002-Critical-UX-Architecture-Resolutions.md` C-05 (adopting `ADR-001-Missing-Source-Volume-Governance.md`'s Option F governance model). It holds the Decision, Monitoring, AI-Collaboration, and domain-specific Metadata content previously assembled in `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md`, restructured under mandatory, per-claim, three-tier provenance classification.

**This document is not a fabricated missing source volume.** `UX-013C — Atlas Component Specification: Decision & Monitoring Components` and `UX-013D — Atlas Component Specification: AI Collaboration, Metadata & System Components` — the two source volumes UX-013E's own text names — do not exist anywhere in the committed repository. This document does not reconstruct them, does not present itself as either of them, and does not claim they ever existed. It is assembled on 2026-07-28 from content previously held in `UX-013E`, itself dated to its own original authorship; it does not claim any earlier origin.

**This document is not a canonical substitute for genuine future authorship.** It is an interim governance boundary: every substantive claim below is classified individually as (1) **Independently Confirmed** — corroborated by another committed document, cited by name; (2) **Unconfirmed** — traceable only to UX-013E's own secondhand account, with no independent corroboration; or (3) **To Be Authored** — explicitly awaiting genuine future specification work, not an indefinite deferral. This tagging is applied per claim or per closely-related claim group, per `ADR-001`'s own "per claim or per section" requirement — never as one blanket document-level status.

This document is **provisional and non-canonical**. Genuine future authorship of UX-013C and UX-013D, following the identical process UX-013A and UX-013B themselves used — citing only documents that exist and are checkable at the time of writing — may supersede corresponding portions of this document in whole or in part, exactly as UX-012 superseded UX-012A–D.

## Relationship to Predecessor and Peer Documents

**Relationship to UX-013E.** This document supersedes UX-013E **only for interim Decision, Monitoring, AI-Collaboration, and domain-specific Metadata governance authority**, and only provisionally — pending the genuine authorship named as this document's own commissioning trigger (below). It does not supersede UX-013E's Foundation or Reasoning content, or the cross-cutting infrastructure content — that operative authority belongs to `UX-013F-Foundation-Reasoning-Component-Library-Assembly.md`. UX-013E remains, unedited in body, as the historical record of the original assembly attempt.

**Relationship to UX-013F.** This document and UX-013F are peers describing the same library from two different, explicitly bounded trust positions. UX-013F is canonical because its content is genuinely traceable to committed UX-013A and UX-013B. This document is provisional because its Decision/Monitoring/AI-specific content traces only to UX-013E's own secondhand account of the never-authored UX-013C and UX-013D. This document references UX-013F for every shared infrastructure primitive (StatusBadge, MetadataBlock, ProgressIndicator, EmptyState, Dialog, and the cross-cutting property/state/composition/dependency models) rather than restating their canonical definitions.

**Relationship to ADR-002 C-05.** This document is one of the two operative outputs C-05 requires; the other is UX-013F.

## Non-Goals

This document does not: introduce any new component, variant, action, state, or pattern; introduce any new API, runtime behavior, persistence model, routing model, or token; claim final component architecture, completed UX-013C/UX-013D authorship, settled APIs, settled persistence, settled runtime behavior, settled state machines, or settled test contracts beyond what is explicitly classified Independently Confirmed below; reopen ADR-002 C-05 or any other accepted decision; or take a position on Open Questions Q1, Q2, or Finding F-2 of the Atlas UX Source Correction Plan, all of which remain outside this document's scope, exactly as unresolved as before.

---

# 1. Source Specification Reconciliation — Decision, Monitoring, AI Collaboration, and Metadata

**Provenance classification for this entire section: Unconfirmed**, unless a specific claim is separately marked otherwise. UX-013C and UX-013D do not exist in the committed repository. UX-013B itself states, in its own committed text (cited by `ADR-001`), "Do not produce UX-013C yet. The completed UX-013B is the prerequisite" — establishing that UX-013C did not exist at the time UX-013B was written. Whether it was later written and never captured, or never written at all, cannot be determined from anything in this repository. Everything below is UX-013E's own secondhand account of what it claims UX-013C and UX-013D once established — preserved here as a historical claim being carried forward under explicit provenance classification, **not** restated as settled fact.

## UX-013C — "Decision & Monitoring Components" (claimed source; does not exist in this repository)

**UX-013E's own claimed contribution (Unconfirmed):** ~27 Decision and Monitoring component types across 12 families — Decision Proposal, Decision Card (7 lifecycle variants, normalized to one component), Decision Summary, Final Decision, Recorded Decision, Decision Rationale Summary, Decision Outcome (5 variants), Decision History, Decision Amendment, Decision Supersession, Monitoring Condition (6 lifecycle variants), Monitoring Trigger, Review Trigger, Invalidation Condition, Scheduled Review, Review Summary, Review Outcome, Follow-up (5 variant types), Implementation Plan (5 variants), Implementation Status, Outcome Tracking, Timeline Entry (10 types), Decision Timeline, historical variants, and a Current-to-Historical Transition pattern.

**Independently Confirmed, per ADR-002 C-05's own worked example:** the broad existence and purpose of **Monitoring Condition** — named in `UX-012` itself, per ADR-002 C-05's explicit citation.

**Independently Confirmed via UX-013B (a real, committed, accepted document, distinct from UX-013E):** the broad existence of a **Monitoring Condition** concept referenced by ID from Reasoning's own AssumptionItem component (`monitoringConditionId`); the general expectation that Decision-tier and Reasoning-tier content relate via typed ID references, not component nesting.

**Unconfirmed (traceable only to UX-013E's own account, no independent corroboration found):** exact component counts (27, 12 families); exact names (DecisionProposal, DecisionSummary, RecordedDecision, DecisionRationaleRef, DecisionHistory, DecisionAmendment, DecisionSupersession, DecisionOutcome, MonitoringTrigger, ReviewTrigger, InvalidationCondition, ScheduledReview, ReviewSummary, ReviewOutcome, FollowUp, ImplementationPlan, ImplementationStatus, OutcomeTracking, TimelineEntry); exact variant counts (7 DecisionCard lifecycle variants, 6 MonitoringCondition lifecycle variants, 5 DecisionOutcome variants, 5 FollowUp types, 5 ImplementationPlan variants, 10 TimelineEntry types); exact merge/normalization decisions (Historical Decision → DecisionCard state; Historical Monitoring Record → MonitoringCondition state; Historical Review → ReviewSummary state; Decision Rationale Summary → DecisionSummary variant); the specific overlap-resolution narratives below.

**Overlaps and resolutions claimed by UX-013E (Unconfirmed as a body of prior reasoning; preserved as UX-013E's own account, not independently re-derived here):**
- Decision Card variants (Current, Draft, Final, Recorded, Historical, Superseded, Under-review) claimed as one canonical Composite Component, differentiated by `lifecycleState` and `isHistorical`.
- Historical Decision, Historical Monitoring Record, Historical Review each claimed as a state on an existing component, not a separate component.
- Decision History (catalog) vs. Decision Timeline (event narrative) claimed as architecturally distinct — Composite Component vs. Composed Pattern respectively.
- Decision Summary claimed distinct from a Decision Card's own internal summary region.
- Decision Rationale Summary claimed as a `DecisionSummary` variant, not a separate component.
- Follow-up claimed distinct from Implementation Plan (different structural content, independent lifecycle rules).

**Unresolved implementation questions UX-013E carries forward from its own account of UX-013C (preserved unchanged, To Be Authored where genuine specification work is named):**
- One-to-many decision-to-monitoring relationship cardinality — **To Be Authored**; requires product and engineering confirmation.
- Monitoring Condition data integration contracts with external sources — **To Be Authored**; not yet specified anywhere.
- Scheduled Review calendar integration model — **To Be Authored**; requires product architecture decision.
- Invalidation Condition automated-detection scope — **To Be Authored**; requires AI capability confirmation.
- Review Outcome "Further information required" next-step flow — **To Be Authored**; requires product flow definition.

## UX-013D — "AI Collaboration, Metadata & System Components" (claimed source; does not exist in this repository)

**UX-013E's own claimed contribution (Unconfirmed):** ~35 AI, Metadata, and System component types across 10 families — AtlasSuggestion (6 variant types), AtlasInsight (6 variant types), AtlasQuestion (6 categories), AtlasClarification, AtlasWarning (6 variant types), AIGeneratedSummary (6 types), AIAuthorshipIndicator, seven suggestion actions, SourceReference (5 variant types), SourceGroup, MetadataBlock, Timestamp (8 types), Author (7 categories), Version, RelationshipReference (4 variant types), ConfidencePresentation, PermissionState (6 categories), UnavailableDataState, OfflineConnectionState, SystemNotification, plus various normalized items.

**Independently Confirmed, per ADR-002 C-05's own worked example:** the broad existence and purpose of **Atlas Warning** — named in `UX-012` itself, per ADR-002 C-05's explicit citation.

**Independently Confirmed via ADR-002 C-02 and its Mixed-Origin Single-Field Content addendum (both accepted, committed sources independent of UX-013E):** the general existence of an authorship/attribution model distinguishing Atlas-generated, user-accepted, user-edited, and mixed-origin content; the general principle that acceptance of AI-suggested content is never itself genuine editing.

**Unconfirmed (traceable only to UX-013E's own account):** exact component counts (~35, 10 families); exact names and variant counts for AtlasSuggestion, AtlasInsight, AtlasQuestion, AtlasClarification, AtlasWarning, AIGeneratedSummary; the specific claim that `MetadataBlock`, `SourceReference`, `SourceGroup`, `Timestamp`, `Author`, `Version`, `RelationshipReference`, `ConfidencePresentation` originated in UX-013D specifically (as opposed to being independently developed design-system infrastructure — this document takes no position on their true origin; their present operative specification lives in UX-013F regardless of origin); the merge/normalization decisions below.

**Overlaps and resolutions claimed by UX-013E (Unconfirmed as a body of prior reasoning):**
- AtlasWarning (analytical) confirmed distinct from WarningMessage (system) and ValidationMessage (input) — full comparison table is UX-013F's own (Section 5), cross-referenced here since AtlasWarning's own operative specification is this document's.
- Notification Center claimed deferred, no approved product requirement.
- AI Working State and Skeleton State claimed as behavior/variant, not standalone components — both build on UX-013F's own ProgressIndicator.
- Atlas Recommendation Presentation claimed as an authorship configuration of Reasoning's own Recommendation component (UX-013F), not a second component.

**Unresolved implementation questions UX-013E carries forward from its own account of UX-013D (preserved unchanged):**
- Suggestion-targeting precision at item level — **To Be Authored**; requires AI orchestration architecture confirmation (shared with UX-013F's own carried-forward question from UX-013B).
- Restore Dismissed Suggestion cross-device persistence model — **To Be Authored**; requires persistence architecture decision.
- Partial-acceptance structural safety bounds — **To Be Authored**; requires AI content model specification.
- AI explanation faithfulness guarantee — **To Be Authored**; requires AI architecture specification.
- Offline sync conflict resolution strategy — **To Be Authored**; requires persistence architecture decision.

## Reconciliation Summary (Decision, Monitoring, AI Collaboration — Unconfirmed counts, preserved from UX-013E)

| Claimed Source | Component Types Contributed (Unconfirmed) | Actions Established (Unconfirmed) | Patterns Established (Unconfirmed) |
|---|---|---|---|
| UX-013C | ~27 Decision/Monitoring types | Finalize, Record, Amend, Supersede, StartReview, CompleteReview | DecisionTimeline, HistoricalInspection, ReviewFlow, DecisionFinalization, CurrentToHistoricalTransition |
| UX-013D | ~35 AI/Metadata/System types | AcceptSuggestion, PartiallyAcceptSuggestion, RejectSuggestion, DismissSuggestion, RestoreSuggestion, ExplainSuggestion, CompareSuggestion | SuggestionComparison, ErrorRecovery, OfflineRecovery, ConfirmationFlow |

---

# 2. Canonical Classification Model — Reference

The ten classification types (Primitive, Component, Composite Component, Action, Behavior, State, Variant, Composed Pattern, Semantic Concept, Deferred Item) are cross-cutting and defined in full in `UX-013F`, Section 2. This document applies them, unchanged, to the Decision/Monitoring/AI-tier items below — it does not redefine any classification type.

---

# 3. Canonical Component Taxonomy — Decision, Monitoring, Historical, AI Collaboration

**Decision** *(Tier 2 — Content, Domain-Specific)* — the components through which investment decisions are proposed, examined, finalized, recorded, amended, superseded, and displayed. Figma: `Decision/`. Engineering: `@atlas/decision`. Owner: Product Design + Domain. Dependencies: Foundation, Reasoning (via ID references, per `UX-013F`), Metadata & Provenance (`UX-013F`), Historical.

**Monitoring** *(Tier 2)* — components tracking, triggering, reviewing, and resolving conditions relevant to recorded decisions. Figma: `Monitoring/`. Engineering: `@atlas/monitoring`. Owner: Product Design + Domain. Dependencies: Foundation, Decision (via ID references), Metadata & Provenance, Historical.

**Historical** *(Tier 2)* — components displaying past states, chronological event sequences, and completed lifecycle records. Scope: TimelineEntry, DecisionOutcome (in a historical context). Historical variants of Decision, Monitoring, and Reasoning components are not separate components — they are those components with `isHistorical={true}`, per `UX-013F`'s own naming and property rules. Figma: `Historical/`. Engineering: `@atlas/historical`. Owner: Product Design. Dependencies: Foundation, Decision, Monitoring, Metadata & Provenance.

**AI Collaboration** *(Tier 3 — System, Cross-Domain)* — components through which Atlas AI suggestions, insights, questions, clarifications, warnings, and summaries are presented, evaluated, and actioned. Scope: AtlasSuggestion, AtlasInsight, AtlasQuestion, AtlasClarification, AtlasWarning (analytical — distinct from WarningMessage, per `UX-013F` Section 5), AIGeneratedSummary, AIAuthorshipIndicator. Figma: `AI/`. Engineering: `@atlas/ai`. Owner: AI Product + Design System. Dependencies: Foundation (`UX-013F`), Metadata & Provenance (`UX-013F`), Status & Feedback (`UX-013F`).

**Provenance note:** the taxonomy structure itself (tiers, dependency direction, namespace convention) is cross-cutting and defined once, canonically, in `UX-013F` Section 3 — **Independently Confirmed** as a structural convention, since it applies uniformly and is not itself a claim about UX-013C/UX-013D's content. The specific component lists assigned to each category above remain **Unconfirmed**, per Section 1.

---

# 4. Canonical Naming System — Application to This Document's Tiers

The naming rules themselves are cross-cutting and defined in full in `UX-013F` Section 4 (Independently Confirmed as a structural convention). Applied here:

## Naming Audit — Decision/Monitoring/AI Items Renamed from the Claimed Source Volumes (Unconfirmed provenance; the renaming logic itself is a documentary consistency decision, not a new claim)

| Previous Name (Claimed Source) | Canonical Name | Change Type | Reason |
|---|---|---|---|
| `HistoricalDecision` (UX-013C) | `DecisionCard` with `isHistorical={true}` | Component → State on existing component | Same semantic responsibility; historical is a state |
| `HistoricalMonitoringRecord` (UX-013C) | `MonitoringCondition` with `isHistorical={true}` | Component → State | Same semantic responsibility |
| `HistoricalReview` (UX-013C) | `ReviewSummary` with `isHistorical={true}` | Component → State | Same semantic responsibility |
| `DecisionRationaleSummary` (UX-013C) | `DecisionSummary` with `variant="rationale"` | Component → Variant | Both summarize decision content |
| `AtlasRecommendationPresentation` (UX-013D) | `Recommendation` (`UX-013F`) with `isAtlasGenerated={true}` | Component → Props on an existing UX-013F component | Atlas recommendation authorship is expressed through existing Recommendation props |
| `SkeletonState` (UX-013D) | `ProgressIndicator` (`UX-013F`) with `variant="skeleton"` | Component → Variant | Skeleton is a loading presentation mode |
| `AIWorkingState` (UX-013D) | Behavior: LoadingBehavior + `ProgressIndicator` (`UX-013F`) | Component → Behavior pattern | Not a standalone component |
| `StatusPresentation` (UX-013D) | Architecture document (no Figma/engineering equivalent) | Component → Architecture document | Mapping specification, not a component |
| `NotificationCenter` (UX-013D) | Deferred | Component → Deferred | Not yet justified by approved product requirements |
| `AIUnavailableState` (UX-013D) | `UnavailableDataState` with `reason="ai-unavailable"` | Component → Variant/prop | Same component; reason is a prop |
| `DecisionCard` (Current variant, UX-013C) | `DecisionCard` with `lifecycleState="draft"`/`"proposed"` | Clarified; not a rename | No separate "Current" component; current state is the default |
| `FinalDecision` (UX-013C) | `DecisionCard` with `lifecycleState="final"` | Component → Variant | All lifecycle states are variants of one DecisionCard |
| `RecordedDecision` (as separate component, UX-013C) | `DecisionCard` (`lifecycleState="recorded"`) for editing contexts + standalone `RecordedDecision` for immutable display | Clarified | Distinguishes editing context from cross-Workspace immutable display |

Every row above is **Unconfirmed** — the "previous name" side traces only to UX-013E's own account of UX-013C/UX-013D; the "canonical name" side is this document's own current, internally consistent naming, applying `UX-013F`'s cross-cutting naming rules.

---

# 5. Duplicate, Variant, and Pattern Audits — Decision, Monitoring, AI Collaboration

*(These audit entries concern components whose own operative specification is this document's; where an entry spans a UX-013F-owned component, UX-013F Section 5 carries the full comparison and this document cross-references it. All resolutions below are Unconfirmed provenance — UX-013E's own account — restated for internal consistency, not independently re-derived.)*

## DecisionHistory vs. Decision Timeline

DecisionHistory is a queryable, filterable, paginated catalog of Recorded Decisions (catalog lookup). Decision Timeline is a chronological sequence of Timeline Entries for one decision's lifecycle (narrative review). Different data requirements, different filtering behaviors, different user goals. **Resolution: DecisionHistory is a Composite Component; Decision Timeline is a Composed Pattern.**

## MonitoringTrigger vs. ReviewTrigger

| Dimension | MonitoringTrigger | ReviewTrigger |
|---|---|---|
| Semantic responsibility | Event notification: a Monitoring Condition produced a state change | Review initiation: formal re-examination is warranted |
| Originating cause | A MonitoringCondition crossing a threshold | A MonitoringTrigger, InvalidationCondition, or external event |
| Lifecycle | Acknowledged → Resolved | Pending → InProgress → Completed |

**Resolution: both retained as separate Components with distinct semantic responsibilities and independent lifecycle management.**

## Decision Card variants → one component (Component-versus-Variant)

Decision Proposal, Draft, Final, Recorded, Historical, Superseded, Under-review Decision are all lifecycle states/variants of the canonical `DecisionCard`. Engineering: `lifecycleState` typed enum + `isHistorical` boolean. Figma: one component set with a `Lifecycle State` variant property.

## AI Suggestion variants → one component (Component-versus-Variant)

Inline, section, replacement, insertion, structured-field, multi-part suggestion: variants of `AtlasSuggestion` (`type` enum). One component.

## Permission-State variants → one component (Component-versus-Variant)

View/Edit/Action/Source/Workspace/AI-feature restricted: variants of `PermissionState` (`reason` enum). One component.

## Component-versus-Pattern Resolutions (Decision/Monitoring/AI-relevant)

- Decision Timeline → Composed Pattern (multiple components orchestrated; no single owner).
- Decision History → Composite Component (owns its full composition).
- Decision Card → Composite Component (owns header, statement, status, rationale summary, implementation summary, monitoring summary, review conditions, metadata, actions, relationship links).
- Source Group, Implementation Plan, Outcome Tracking, Review Summary → Composite Components (each owns its own complete composition; the underlying primitives — SourceReference, MetadataBlock — are `UX-013F`'s own).
- Decision Finalization Flow → Application-Level Composed Pattern (completion gate → pause → conversion → monitoring activation → historical record creation; components used — WorkspaceFooter, Dialog, ProgressIndicator [all `UX-013F`], DecisionCard — are independent).
- Current-to-Historical Transition → Application-Level Composed Pattern.
- Suggestion Comparison → Composed Pattern, using `UX-013F`'s own Comparison component configured for suggestion comparison.
- Notification Center → Deferred.

---

# 6. Canonical Component Inventory — Decision, Monitoring, AI Collaboration Categories

**Provenance tag legend:** **[IC]** Independently Confirmed · **[U]** Unconfirmed · **[TBA]** To Be Authored. The broad existence of each category and its general purpose is tagged once at the category heading; individual rows carry their own tag only where it differs from the category default.

## Decision Category — [U] (exact roster, props, and classifications trace only to UX-013E's own account)

| Canonical Name | Classification | Semantic Purpose | Core Properties | Historical | Maturity | Provenance |
|---|---|---|---|---|---|---|
| DecisionProposal | Component | Candidate decision not yet finalized | statement, authorship, source, isAtlasGenerated | No | Candidate | [U] |
| DecisionCard | Composite | Structural representation of a decision | decisionId, lifecycleState, statement, rationale, implementation, monitoring, review, metadata | Yes | Candidate | [U] |
| DecisionSummary | Component | Portable condensed decision representation | decisionId, statement, date, status | Yes | Candidate | [U] |
| RecordedDecision | Component | Finalized committed decision | decisionId, recordedAt, author, version, immutable | Yes | Candidate | [U] |
| DecisionRationaleRef | Component | Reference to full reasoning from decision | decisionId, summaryText, expandsTo | Yes | Candidate | [U] |
| DecisionHistory | Composite | Queryable catalog of recorded decisions | decisions[], filter, sort | Yes | Candidate | [U] |
| DecisionAmendment | Component | Formal partial modification to a recorded decision | decisionId, reason, affectedScope, effectiveAt, author | Yes | Candidate | [U] |
| DecisionSupersession | Component | Formal replacement of a recorded decision | predecessorDecisionId, successorDecisionId, reason, effectiveAt | Yes | Candidate | [U] |
| DecisionOutcome | Component | Observed result after decision was recorded | decisionId, outcomeType, observedResult, observationDate, uncertainty | Yes | Candidate | [U] |

## Monitoring Category — category default **[IC]** for "Monitoring Condition" broad existence/purpose only (per ADR-002 C-05's own worked example); all other rows and all prop/variant detail **[U]**

| Canonical Name | Classification | Semantic Purpose | Core Properties | Historical | Maturity | Provenance |
|---|---|---|---|---|---|---|
| MonitoringCondition | Composite | Defined trackable condition post-decision | conditionId, decisionId, subject, threshold, frequency, lifecycleState | Yes | Candidate | [IC] broad existence/purpose; [U] exact props/classification |
| MonitoringTrigger | Component | Event notification from a monitoring condition | conditionId, triggerTime, severity, acknowledgementState | Yes | Candidate | [U] |
| ReviewTrigger | Component | Communication that review is warranted | decisionId, reason, materiality, reviewScope, reviewPriority, state | Yes | Candidate | [U] |
| InvalidationCondition | Component | Named condition that would change the decision's basis | decisionId, conditionExpression, observationState | Yes | Candidate | [U] |
| ScheduledReview | Component | Time-based review commitment | reviewId, decisionId, reviewDate, scope, state, recurrence | Yes | Candidate | [U] |
| ReviewSummary | Composite | Complete record of a formal review | reviewId, decisionId, scope, findings, conclusion, outcome | Yes | Candidate | [U] |
| ReviewOutcome | Component | Result of a completed review | reviewId, outcomeType, consequence | Yes | Candidate | [U] |
| FollowUp | Component | Named obligation or next step | followUpId, type, description, owner, dueState, completionCriteria | No | Candidate | [U] |
| ImplementationPlan | Composite | Structured implementation strategy for a decision | decisionId, variant, steps[], dependencies[], timing, owner | No | Candidate | [U] |
| ImplementationStatus | Component | Current implementation progress | decisionId, statusModel, progress, blockingInfo, owner | No | Candidate | [U] |
| OutcomeTracking | Composite | Observation history for a decision | decisionId, observations[], baseline, expectedResult, timeHorizon | Yes | Candidate | [U] |
| TimelineEntry | Component | Single chronological event in a decision's history | entryId, entryType, timestamp, actor, eventStatement, relatedObjectId | Yes | Candidate | [U] |

## AI Collaboration Category — category default **[IC]** for "Atlas Warning" broad existence/purpose only (per ADR-002 C-05's own worked example); all other rows and all prop/variant detail **[U]**

| Canonical Name | Classification | Semantic Purpose | Core Properties | Maturity | Provenance |
|---|---|---|---|---|---|
| AtlasSuggestion | Component | Optional AI-generated content proposal | type, suggestedContent, reason, affectedContentId, authorship, state | Candidate | [U] |
| AtlasInsight | Component | AI analytical observation | insightType, statement, evidence[], uncertainty, state | Candidate | [U] |
| AtlasQuestion | Component | AI request for reasoning or clarification | questionType, question, reason, answerMechanism, state | Candidate | [U] |
| AtlasClarification | Component | AI explanatory clarification | clarificationType, content, isExpanded, state | Candidate | [U] |
| AtlasWarning | Component | AI-surfaced material analytical concern | severity, concern, affectedContext, reason, state, isAcknowledged | Candidate | [IC] broad existence/purpose; [U] exact props/classification |
| AIGeneratedSummary | Component | AI-generated content summary | summaryType, content, scope, generatedAt, state, isUserConfirmed | Candidate | [U] |
| AIAuthorshipIndicator | Component | Attribution display for AI-originated content | authorshipType, label, isCondensed | Candidate | [IC] broad existence/purpose, via ADR-002 C-02's own authorship model; [U] exact props |

*(Foundation, Reasoning, Metadata & Provenance, Status & Feedback, Loading & Availability, Overlay & Dialog, and Notification category inventories are `UX-013F`'s own operative content.)*

**Total canonical components in this document's own scope: Decision 9, Monitoring 12, AI Collaboration 7 = 28, with no component appearing in more than one of these three categories — all Unconfirmed except where individually tagged [IC] above.** Combined with `UX-013F`'s own deduplicated total of 56 unique components (Foundation's 16 — which already includes LayoutContainer, NavigationBar, Breadcrumb, StatusBadge, ProgressIndicator, and EmptyState as members, not as additions — plus Reasoning's 19, plus 21 further unique components across Metadata & Provenance, Status & Feedback, Loading & Availability, Overlay & Dialog, and Notification once StatusBadge, ProgressIndicator, and EmptyState are not recounted), the two documents together account for **84 unique canonical components**. **This does not match UX-013E's own stated "Total canonical components: 87"** — that figure is the raw sum of UX-013E's own ten category-row counts (16+19+9+12+7+8+6+5+4+1=87), which counts StatusBadge, ProgressIndicator, and EmptyState twice each (once in Foundation, once in Status & Feedback or Loading & Availability respectively), despite UX-013E's own parenthetical claiming to exclude such duplicates and naming only two of the three. This 3-component discrepancy is pre-existing in UX-013E's own original counting method, not introduced by this migration: this document and `UX-013F` do not add, remove, or recount any component relative to UX-013E's own account — they only correct how the total is arithmetically reconciled, and reclassify the provenance of each count.

---

# 7. Action, Pattern, and Semantic Concept Inventories — Decision, Monitoring, AI Collaboration

## Actions — [U] (per ADR-002 C-02's own already-accepted authorship model, the Accept/Reject/Dismiss/Restore mechanics for AI-suggested content are [IC]; the exact action roster and event-contract detail below remain [U])

| Canonical Name | Purpose | Eligible Components | Confirmation Required | Undo Window | Provenance |
|---|---|---|---|---|---|
| AcceptSuggestion | Accept Atlas-generated content in full | AtlasSuggestion | No (5s undo) | 5 seconds | [IC] mechanic (ADR-002 C-02); [U] exact contract |
| PartiallyAcceptSuggestion | Accept selected portion of suggestion | AtlasSuggestion (multi-part) | No | 5 seconds | [U] |
| RejectSuggestion | Formally reject a suggestion | AtlasSuggestion | No | Session restore | [U] |
| DismissSuggestion | Temporarily remove suggestion from view | AtlasSuggestion | No | Session (restore) | [U] |
| RestoreSuggestion | Return a dismissed suggestion to view | AtlasSuggestion (dismissed) | No | N/A | [U] |
| ExplainSuggestion | Request Atlas explanation of a suggestion | AtlasSuggestion | No | N/A | [U] |
| CompareSuggestion | Open Suggestion Comparison pattern | AtlasSuggestion | No | N/A | [U] |
| FinalizeDecision | Advance decision from proposal to final state | DecisionCard, WorkspaceFooter (`UX-013F`) | Yes (Confirmation Dialog) | No | [U] |
| RecordDecision | Commit a final decision to the historical record | DecisionCard, WorkspaceFooter | Yes | No | [U] |
| AmendDecision | Formally modify a recorded decision's scope | RecordedDecision | Yes | No | [U] |
| SupersedeDecision | Replace a recorded decision with a new decision | RecordedDecision | Yes | No | [U] |
| StartReview | Initiate a formal review of a decision | ReviewTrigger, ScheduledReview | No | N/A | [U] |
| CompleteReview | Finalize and record a completed review | ReviewSummary | Yes | No | [U] |

## Patterns — [U]

| Pattern Name | Purpose | Participating Components | Provenance |
|---|---|---|---|
| ReasoningToDecisionFlow | Full flow from reasoning to recorded decision | ReasoningHierarchy (`UX-013F`) + DecisionProposal + DecisionCard + WorkspaceFooter (`UX-013F`) | [U] |
| DecisionFinalization | Finalization and recording sequence | WorkspaceFooter, DialogContainer, Dialog (Confirmation), ProgressIndicator (all `UX-013F`), DecisionCard | [U] |
| DecisionRecording | Commit to historical record | DecisionCard, WorkspaceFooter, ProgressIndicator | [U] |
| DecisionMonitoring | Post-decision monitoring setup and display | MonitoringCondition × n, AssumptionItem links (`UX-013F`) | [U] |
| TriggeredReview | Review initiated by monitoring or invalidation trigger | MonitoringTrigger or ReviewTrigger → ReviewSummary → ReviewOutcome | [U] |
| ScheduledReviewFlow | Time-based review execution | ScheduledReview → ReviewSummary → ReviewOutcome | [U] |
| DecisionTimeline | Chronological event sequence for a decision | TimelineEntry × n, SectionContainer (`UX-013F`), filtering | [U] |
| HistoricalInspection | Viewing historical Workspace content | DecisionCard (isHistorical), Reasoning components (isHistorical, `UX-013F`), MetadataBlock (`UX-013F`) | [U] |
| SuggestionReview | Evaluating an Atlas Suggestion | AtlasSuggestion, AIAuthorshipIndicator, Accept/Reject/Dismiss actions | [U] |
| SuggestionComparison | Side-by-side original vs. suggested content | Comparison (`UX-013F`, configured for suggestion comparison), AtlasSuggestion actions | [U] |

## Semantic Concepts — [U] unless tagged

| Concept | Semantic Meaning | Primary Component Carriers | Provenance |
|---|---|---|---|
| Decision | A user-committed choice to act on or in response to an investment situation | DecisionCard, RecordedDecision | [U] |
| Implementation | The execution of what a Decision commits to | ImplementationPlan, ImplementationStatus | [U] |
| Monitoring | Ongoing observation of conditions relevant to a Decision or Assumption | MonitoringCondition, MonitoringTrigger | [IC] broad concept, per ADR-002 C-05; [U] component detail |
| Review | Formal re-examination of a Decision in light of new information or a monitoring trigger | ReviewSummary, ReviewOutcome, ReviewTrigger | [U] |
| Outcome | What actually happened after a Decision was recorded | DecisionOutcome, OutcomeTracking | [U] |

---

# 8. Shared Cross-Cutting Models — Reference Only

The Property Model, State Model, State Composition Rules, Variant Model, Composition Model, and complete Component Dependency Graph are canonical, cross-cutting, and defined once in `UX-013F` (Sections 8–11). This document does not restate them. This document's own position within the shared Dependency Graph:

```
… → Metadata & Provenance (UX-013F) → Status & Feedback (UX-013F) →
AI Collaboration (this document) →
Reasoning (UX-013F) →
Decision (this document) →
Monitoring (this document) →
Historical (this document) →
Patterns and Templates
```

**Explicitly disclosed cross-tier dependencies (mirrored from `UX-013F` Section 11 for this document's own tiers):** AtlasSuggestion → multiple Reasoning components (`UX-013F`), as target of suggestions, via typed `targetComponent` ID, not a direct import. DecisionCard → MonitoringCondition, ReviewTrigger, ImplementationStatus, all within this document, via ID reference. AssumptionItem (`UX-013F`) → MonitoringCondition (this document), via ID reference — the reciprocal of the same disclosed edge.

**No circular dependencies** — this property is established for the complete graph in `UX-013F` Section 11 and holds identically for this document's own tiers within it.

AI Content States (`generated`, `presented`, `viewed`, `partiallyAccepted`, `accepted`, `rejected`, `dismissed`, `restored`, `outdated`, `superseded`) are this document's own full semantic elaboration of the state class `UX-013F` Section 9 names once, cross-cuttingly, for consistency with the rest of the State Dictionary — **[U]** as applied to AtlasSuggestion/AtlasInsight specifically, since the exact state-transition rules trace only to UX-013E's own account; the state-class structure itself is **[IC]**, being a documentary-consistency convention, not a UX-013C/D content claim.

---

# 9. Workspace Coverage — This Document's Rows

The complete Workspace Coverage Matrix is `UX-013F`'s own (Section 12), spanning every Workspace and category. This document's own rows within it: DecisionCard (Required, summary form on Dashboard; Optional on Investment; Required on Portfolio and Decision), MonitoringCondition (Required summary on Dashboard; Optional on Investment; Required on Portfolio and Decision), AtlasSuggestion and AtlasWarning (Optional on Dashboard/Portfolio; Required on Investment and Decision), DecisionTimeline and TimelineEntry (Optional on Investment/Portfolio/Decision; Not used on Dashboard), ReviewSummary and ImplementationPlan (Not used on Dashboard/Investment; Optional on Portfolio; Required on Decision) — all **[U]**.

**Coverage gaps carried forward unchanged, To Be Authored:** Dashboard has no dedicated Monitoring summary component; a condensed MonitoringCondition variant for Dashboard display is not yet specified — **[TBA]**. Portfolio Workspace's Review and Implementation coverage is partial (reference forms only); the reference representation is not yet specified for all cases — **[TBA]**.

---

# 10. Responsive, Accessibility, and Token Coverage — This Document's Tiers

Responsive and Accessibility policy are cross-cutting and defined once in `UX-013F` (Sections 13–14); this document's components conform to them without restatement. This document's own tier-specific responsive notes, preserved from UX-013E (**[U]**): on mobile, Decision Card becomes full-width with metadata collapsing to compact MetadataBlock (`UX-013F`); Timeline becomes full-width entries with no side-by-side actor/date layout.

**Token groups required for this document's tiers, preserved unchanged from UX-013E's own backlog — all To Be Authored [TBA]:** AI authorship tokens (`authorship.atlas.*`, `.user.*`, `.mixed.*`); Decision state tokens (`decision.state.*`); Monitoring state tokens (`monitoring.state.*`); AI content-state tokens (`ai.state.*`). None of these tokens currently exist; none is deprecated from the existing UX-012 vocabulary.

---

# 11. Figma and Engineering Architecture — This Document's Pages and Layers

The complete Figma file structure and engineering layer stack are single, coherent, cross-tier structures, reproduced in full in `UX-013F` (Sections 16, 18) for the reasons stated there (the ordering itself is one dependency chain that cannot be fragmented without duplicating or breaking it). This document's own operative pages and layers within that shared structure:

**Figma pages (this document's own content, within the shared file `UX-013F` Section 16 structures):** Decision page (DecisionProposal, DecisionCard, DecisionSummary, DecisionHistory); Monitoring page (MonitoringCondition, MonitoringTrigger, ReviewTrigger, InvalidationCondition, ScheduledReview, ReviewSummary, ReviewOutcome, FollowUp, ImplementationPlan, ImplementationStatus, OutcomeTracking); Historical page (TimelineEntry, DecisionOutcome; other historical variants documented inline on Decision/Monitoring pages); AI Collaboration page (AtlasSuggestion, AtlasInsight, AtlasQuestion, AtlasClarification, AtlasWarning, AIGeneratedSummary, AIAuthorshipIndicator).

**Engineering layers (this document's own content, within `UX-013F` Section 18's shared stack):** Layer 7 — AI Collaboration Components (`@atlas/ai`), Layer 9 — Decision Components (`@atlas/decision`), Layer 10 — Monitoring Components (`@atlas/monitoring`).

**Representative API example (AI Collaboration — AtlasSuggestion), Unconfirmed detail applying UX-013F's own [IC] API principles:**
```typescript
interface AtlasSuggestionProps {
  suggestionId: string;
  type: AtlasSuggestionType;
  suggestedContent: SuggestionContent;
  reason: string;
  affectedContentId?: string;
  authorship: 'atlas-generated';
  state: AtlasSuggestionState;
  onAccept?: () => void;
  onPartialAccept?: (selectedParts: string[]) => void;
  onReject?: (reason?: string) => void;
  onDismiss?: () => void;
  onExplain?: () => void;
  onCompare?: () => void;
  isLoading?: boolean;
  'data-testid'?: string;
}
```

**Representative API example (Decision — DecisionCard):**
```typescript
interface DecisionCardProps {
  decisionId: string;
  lifecycleState: DecisionLifecycleState;
  statement: string;
  status: DecisionStatus;
  authorship: AuthorshipRecord;
  rationaleRegion?: React.ReactNode;
  implementationRegion?: React.ReactNode;
  monitoringRegion?: React.ReactNode;
  actionsRegion?: React.ReactNode;
  isHistorical?: boolean;
  historicalDate?: Date;
  metadata?: MetadataConfig;
  isLoading?: boolean;
  error?: Error | null;
  'data-testid'?: string;
}
```

Both interfaces above apply `UX-013F` Section 19's own cross-cutting API principles (semantic props only, typed state enums, explicit historical props, slot-based composition) — the principles are [IC] as a documentary convention; the exact prop lists are [U].

---

# 12. Cross-Cutting Architecture References — This Document's Tier-Specific Content

Validation, Feedback/Interruption, Historical-State transition rules, Authorship/Provenance categories, Status classes, Loading/Progress representations, Permission/Availability/Connection state selection, Notification components, Icon roles, Content rules, Localization, Performance, Security, Analytics, Testing, and Documentation architectures are all cross-cutting and defined once, canonically, in `UX-013F` (Sections 20–21). This document's own tier-specific elaborations, all **[U]** unless noted:

- **Historical-State:** DecisionCard, MonitoringCondition, ReviewSummary, FollowUp (review-related), OutcomeTracking, TimelineEntry, AIGeneratedSummary each require the `isHistorical` prop, per `UX-013F`'s own cross-cutting transition rules (which are [IC] as a documentary convention).
- **Feedback:** AtlasWarning's own row in `UX-013F` Section 5's comparison table (Reasoning/Decision-context scope, acknowledgement-with-note dismissal, `aria-live="polite"` with "Atlas warning" prefix) is this document's own operative specification, cross-referenced from `UX-013F`.
- **Performance:** DecisionHistory and DecisionTimeline require virtualization beyond 50/entries respectively (per `UX-013F`'s own cross-cutting performance-budget policy).
- **AI Working State pattern:** ProgressIndicator (`UX-013F`, indeterminate) + a contextual activity label (e.g., "Atlas is analyzing your reasoning") + optional cancel — this document's own AI-specific application of `UX-013F`'s own cross-cutting Loading/Progress architecture.
- **Analytics:** `suggestion.accepted`, `suggestion.rejected`, `suggestion.dismissed`, `decision.finalized`, `decision.recorded`, `review.started` are this document's own permitted event names, fired via `UX-013F`'s own cross-cutting `onAnalyticsEvent` hook convention.

---

# 13. Ownership, Lifecycle, Change, Versioning, and Deprecation Governance — This Document's Rows

The governance models themselves are cross-cutting and defined once, canonically, in `UX-013F` (Section 22) — **[IC]** as documentary/process convention. This document's own ownership rows, **[U]** as specific role-to-domain assignments carried from UX-013E's own account: Decision Components (design: Product Designer — Decision Workspace; engineering: Feature Engineer); Monitoring Components (same); AI Collaboration Components (design: AI Product Designer; engineering: AI Integration Engineer).

---

# 14. Existing Workspace Migration Audit — This Document's Bullets

The complete per-Workspace migration audit is `UX-013F`'s own (Section 23), since it mixes Foundation/Reasoning bullets with Decision/Monitoring bullets in UX-013E's own original text. This document's own bullets, **[U]**, cross-referenced from that same per-Workspace structure:

- **Dashboard:** replace bespoke Decision-summary elements → `DecisionSummary`; replace bespoke monitoring badges → `StatusBadge` (`UX-013F`, Monitoring:Active/Approaching/Triggered types).
- **Portfolio Workspace:** portfolio position cards → `DecisionCard` (`variant="portfolio"`); portfolio monitoring summary → `MonitoringCondition` (condensed — see the To Be Authored note, Section 9 above).
- **Decision Workspace:** Decision Proposal area → `DecisionProposal`; decision recording sequence → `DecisionFinalization` and `DecisionRecording` patterns; monitoring conditions setup → `MonitoringCondition` creation flow. Risk: High overall for this Workspace (per `UX-013F`'s own risk statement) — the most Workspace-specific behavior and the most consequence if semantic changes are introduced incorrectly.

---

# 15. Migration Plan, Sequencing, Risk Register, and Readiness Gates — This Document's Phases, Waves, and Rows

The complete 7-phase Migration Plan and 9-wave Figma/Engineering sequences are single, ordered, cross-tier sequences, stated in full in `UX-013F` Section 24. This document's own operative phases/waves within that same sequence:

**Phase 5 — Decision & Monitoring Component Migration.** Scope: migrate Decision Workspace decision formation and Decision/Portfolio Workspace monitoring. Risk: High — the Decision recording sequence and monitoring lifecycle are the most consequential migrations; full regression testing required before release.

**Phase 6 — AI Collaboration Migration.** Scope: migrate all Atlas AI suggestion, insight, and warning surfaces. Risk: Medium — AI components have complex lifecycle states; all AI content lifecycle transitions must be tested.

**Figma Wave 7 — Decision, Monitoring, Historical** (depends on Waves 3–6, `UX-013F`): all Decision, Monitoring, and Historical components including TimelineEntry. Completion criteria: full Decision Workspace composable; Decision Timeline pattern composable.

**Figma Wave 8 — AI Collaboration** (depends on Waves 4–7): AtlasSuggestion, AtlasInsight, AtlasQuestion, AtlasClarification, AtlasWarning, AIGeneratedSummary. Completion criteria: all AI collaboration contexts in Reasoning and Decision Workspaces composable.

**Engineering Wave 5 — `@atlas/ai`** (depends on `@atlas/metadata`, `@atlas/feedback`, both `UX-013F`).
**Engineering Wave 7 — `@atlas/decision`** (depends on `@atlas/reasoning`, `@atlas/metadata`, `UX-013F`).
**Engineering Wave 8 — `@atlas/monitoring`** (depends on `@atlas/decision`, `@atlas/metadata`).

## Implementation Risk Register — This Document's Rows

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| AI suggestion targeting precision (unresolved — [TBA]) | High | Medium | Implement Section-level suggestions first; defer item-level until AI team confirms capability | AI Product |
| Historical content migration complexity | Medium | High | Historical rendering is additive (new `isHistorical` prop); no destructive migration | Engineering Lead |
| Performance regression in Decision Timeline (large histories) | Medium | Medium | Virtualization required before production release; performance test in Wave 9 | Engineering Lead |

## Readiness Gates — This Document's Rows

| Gate | Required Evidence | Approver | Blocking |
|---|---|---|---|
| Domain readiness | Domain model confirmed for all cross-category dependencies | Domain Lead | Yes — blocks Decision and Monitoring waves |
| AI integration readiness | Atlas Suggestion targeting model confirmed | AI Product + Engineering | No — can proceed with Section-level suggestions |
| Persistence readiness | Server persistence model confirmed for all Recorded Decisions | Engineering Lead, Backend Lead | Yes — blocks Decision Recording pattern |
| Workspace migration readiness (Decision-tier) | Per-Workspace semantic audit complete | Product Designer (per Workspace) | Yes — blocks Phase 5+ migration |

---

# 16. Final Consistency Notes — This Document's Scope

This document does not claim structural completeness independent of `UX-013F` — the two documents together, not this document alone, describe the whole Atlas Component Library. Within its own scope:

✓ Every Decision/Monitoring/AI-Collaboration component named above is classified per `UX-013F` Section 2's cross-cutting classification model.
✓ No unjustified duplicate components remain within this document's own scope (Section 5).
✓ Dependencies from this document's tiers to `UX-013F`'s tiers are explicitly disclosed, never silently assumed (Section 8).

**Remaining inconsistencies, preserved unchanged and honestly disclosed, none silently resolved:**
1. AI Suggestion targeting precision (Section-level vs. item-level) — **To Be Authored**; safe default established (Section-level).
2. Dashboard MonitoringCondition condensed form — **To Be Authored**; not yet specified.
3. Portfolio Workspace's partial Review/Implementation coverage — **To Be Authored**; reference representation not yet specified for all cases.
4. Every "unresolved implementation question" listed in Section 1 above, for both the claimed UX-013C and UX-013D contributions — **all remain exactly as unresolved as UX-013E's own account left them.**

**This document does not claim any of the above is resolved by its own existence.** Its purpose is honest classification, not resolution.

---

# Commissioning Trigger — Future Genuine UX-013C and UX-013D Authorship

Genuine, newly-authored, honestly-dated `UX-013C — Decision & Monitoring Components` and `UX-013D — AI Collaboration, Metadata & System Components` specifications are the scheduled replacement for this interim document, following the identical authorship process `UX-013A` and `UX-013B` themselves used — citing only UX-012 (corrected) and other approved specifications that exist and are checkable at the time of writing, never presenting themselves as recovered or reconstructed history.

This document's own front matter states plainly: it was assembled on 2026-07-28, from content previously held in UX-013E (itself dated to its own original authorship); it does not claim UX-013C or UX-013D ever existed prior to this point. Once genuinely authored, each new volume supersedes the corresponding portion of this document exactly as UX-012 superseded UX-012A–D: this document's own status line is then updated to "Superseded — see UX-013C / UX-013D," its body left unedited, per the same non-erasure principle applied throughout the Atlas UX Source Correction Plan.

Until that authorship occurs, every Unconfirmed and To Be Authored claim in this document remains exactly that — unconfirmed and to be authored — regardless of how completely or coherently it is described above. Coherent restatement is not confirmation.

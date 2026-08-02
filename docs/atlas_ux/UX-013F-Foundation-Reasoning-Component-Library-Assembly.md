# UX-013F — Atlas Foundation & Reasoning Component Library Assembly

Status: Canonical

---

## Governing Introduction

This document is the canonical, operative assembly of the Foundation and Reasoning tiers of the Atlas Component Library, together with the cross-cutting infrastructure every tier of the library depends on (Metadata & Provenance, Status & Feedback, Loading & Availability, Overlay & Dialog, Notification, and the shared property/state/composition/dependency models).

This document implements the documentary trust-boundary correction required by `ADR-002-Critical-UX-Architecture-Resolutions.md` C-05 (adopting `ADR-001-Missing-Source-Volume-Governance.md`'s Option F governance model). It draws on content previously assembled in `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md`, restated here for the Foundation and Reasoning tiers specifically, with the C-01 and C-02 corrections already required elsewhere in the Atlas UX Source Correction Plan (Sections 6–7) folded in.

Its authority is genuinely traceable: Foundation content is grounded in the committed `UX-013A-Atlas-Component-Specification-Foundation-Components.md`; Reasoning content is grounded in the committed `UX-013B-Atlas-Component-Specification-Reasoning-Components.md`; token, hierarchy, and Workspace Shell grounding comes from the committed `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md`, `UX-012A-Atlas-Design-System-Foundations.md`, and `UX-012B-Atlas-Design-System-Components-Reusable-Patterns.md`.

**This document does not claim that UX-013C or UX-013D exist.** Decision, Monitoring, AI Collaboration, and domain-specific Metadata claims are the operative, non-canonical authority of `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`, not of this document. Where this document must reference a Decision- or Monitoring-tier concept (for example, the ID-based reference from a Reasoning component to a Monitoring component), it names the concept and points to the interim note — it does not restate or redefine Decision/Monitoring/AI semantics here.

This document does not redesign components, introduce new product functionality, or redefine the Atlas reasoning model. It reconciles and formalizes what UX-013A, UX-013B, and their cross-cutting infrastructure counterparts already established, exactly as UX-013E did for these same tiers, minus UX-013E's own unsupported four-volume framing.

**Correction Notice (Phase 6D, governed by `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` — 2026-07-30):** This document's own "Recommendation" component name, used throughout to name ADR-003 Concept B, is corrected to **Proposed Decision Candidate Content** (short form, once established in context: "Candidate Content"), consistent with `UX-013B`'s own Phase 3D-1 correction of the same component. ADR-003 reserves "Atlas Recommendation" exclusively for Concept A — the general, Atlas-origin directional advisory artifact defined in `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §28 — which is unrelated to this document and unaffected by this correction. This document's own "Recommendation" always represented Concept B, not Concept A; only its own naming has changed, not its behavior, inputs, outputs, authorship model, or hierarchy position. Prior text, quoted verbatim at each corrected passage: "the difference between a Conclusion and a Recommendation" (line ~51); "...and Recommendation to Decision" (line ~65); "...ScenarioAnalysis, ScenarioItem, Recommendation, ReasoningBlock..." (line ~132); "*Recommendation ↔ Atlas Recommendation Presentation.* Recommendation is the canonical Reasoning component. ...on Recommendation itself, not a second component." (line ~137); "Examples: Reasoning, Conclusion, Recommendation, Decision, Monitoring..." (line ~184); "Recommendation with `isAtlasGenerated={true}`" (line ~208, right column only); "...Comparison, Scenario Analysis, Recommendation, Reasoning Block, Context Panel" (line ~230); "Correct: `Recommendation` with `isAtlasGenerated={true}`." (line ~274, "Correct:" reference only); "## Recommendation vs. Atlas Recommendation Presentation" (line ~335, component-name portion only); "Recommendation is the canonical Reasoning Component. ...alongside Recommendation to present..." (line ~337); "| Recommendation | Component | Suggested direction from reasoning | ... |" (line ~409); "Do not conflate with Decision or Recommendation" (line ~482); "| Recommendation | A suggested direction that follows from reasoning; not a decision | Recommendation component | ... |" (line ~483); "...Comparison, ScenarioAnalysis, Recommendation, ReasoningBlock, ContextPanel" (line ~788).

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, above. No new component, variant, state, interaction, API, runtime behavior, persistence model, routing model, or Domain Object is introduced by this correction; Concept B's own semantics, inputs, outputs, authorship behavior, and hierarchy position are unchanged. This correction does not rewrite the historical chronology of when this document was assembled (Phase 4, 2026-07-28), and does not claim `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md` — the document this terminology was originally drawn from — was inaccurate or improperly reasoned at the time UX-013E itself was written; UX-013E remains governed exclusively by its own existing correction notice and ADR-003 R-09's own characterization of it as non-governing historical evidence, and its entire body remains byte-identical and unedited by this correction. The `AtlasRecommendationPresentation` label (lines ~137, ~208, ~297) is not Concept B's own component name — it is a distinct authorship-configuration label whose own provenance this document already, explicitly attributes to the currently-unconfirmed UX-013C/UX-013D account (line ~297); it is unrenamed and unaffected by this correction, as is line ~297's surrounding prose in full. `UX-012` §28's own "Atlas Recommendation" (Concept A) is not referenced anywhere in this document and requires no change. Line ~274's illustrative "Incorrect: `AtlasRecommendation` as a separate component" anti-pattern is left as a literal illustration, unrenamed, per this Plan's own express latitude on that point — it teaches a general naming rule (no "Atlas"-prefixed component names) and does not itself assert Concept B's current name. All content outside the corrected passages named above is unchanged.

**Correction Notice (Atlas UX Architecture Foundation & Collaboration Token Alignment task — 2026-08-02):** This is a later, additive correction; it does not revise, replace, or reopen the notice above. This document's own Accessibility System Assembly (§14, "Focus Visibility") cited `focus.ring.color`, the pre-Phase-1 focus-ring naming order superseded by `UX-012D` §3's own canonical `color.focus.ring` / `width.focus.ring` / `radius.focus.ring` ordering (Reasoning Token Architecture Phase 1: UX-012D Foundations, 2026-08-02). Prior text: "`outline: 2px solid [focus.ring.color]; outline-offset: 2px`." Corrected to `color.focus.ring` and `width.focus.ring`. This correction changes no classification, inventory, dependency, or component architecture anywhere in this document — only this one token citation.

## Relationship to Predecessor and Peer Documents

**Relationship to UX-013E.** This document supersedes UX-013E **only for Foundation and Reasoning component-library assembly authority, and for the cross-cutting infrastructure categories assigned to this document below.** It does not supersede UX-013E's Decision, Monitoring, AI-Collaboration, or domain-specific Metadata content — that authority belongs to the interim note. UX-013E remains, unedited in body, as the historical record of the original assembly attempt; its own status line names both this document and the interim note as its successors.

**Relationship to UX-013A and UX-013B.** Both remain the detailed, component-by-component specifications. This document is the first-consult source for canonical identity, classification, and cross-cutting architecture; UX-013A and UX-013B remain the source for exhaustive anatomy, property, and interaction detail for each Foundation and Reasoning component respectively.

**Relationship to the interim note.** This document and the interim note are peers describing the same library from two different, explicitly bounded trust positions: this document is canonical because its content is genuinely traceable to committed sources; the interim note is provisional because its content traces only to UX-013E's own secondhand, currently-unconfirmed account of UX-013C and UX-013D. Neither document claims authority over the other's tier. The interim note references this document for shared infrastructure; this document references the interim note for the small number of ID-based cross-tier links Reasoning components carry.

**Relationship to ADR-002 C-05.** This document is one of the two operative outputs C-05 requires; the other is the interim note.

## Non-Goals

This document does not: introduce any new component, variant, action, state, or pattern; introduce any new API, runtime behavior, persistence model, routing model, or token; govern Decision, Monitoring, or AI-Collaboration claims except through narrow, named references to shared infrastructure; resolve any unresolved provenance question (those questions, where they exist for Foundation/Reasoning content, are preserved unchanged below, exactly as UX-013E stated them); reopen ADR-002 C-05 or any other accepted decision; or take a position on Open Questions Q1, Q2, or Finding F-2 of the Atlas UX Source Correction Plan, all of which remain outside this document's scope.

---

## Overall Objective

This document assembles the Foundation and Reasoning tiers of the Atlas Component Library, plus their shared cross-cutting infrastructure, into one production-ready specification with the following deliverables, exactly as UX-013E's own Overall Objective stated for the library as a whole: reconciliation (removing duplication within these tiers), canonical taxonomy, canonical inventory, canonical models (State Dictionary, Property Model, Composition Rules, Naming System, Variant Dimensions), architecture (Figma and engineering, for these tiers), coverage validation (for the Workspaces these tiers serve), and governance (versioning, deprecation, documentation standards, shared across the whole library).

This document does not produce wireframes, visual designs, or Workspace screen specifications, and does not redesign any component whose specification was settled in UX-013A or UX-013B.

---

# Final Assembly Philosophy

*(Cross-cutting; applies to the whole Atlas Component Library, both this document's tiers and the interim note's tiers. Retained once here, per the Atlas UX Source Correction Plan's own duplication-avoidance rule for cross-cutting content; the interim note references this section rather than restating it.)*

## Why a Component Library Is a Semantic System

A component library is not a collection of visual building blocks. It is a system of named meanings. Every component carries a semantic responsibility — a specific claim about what a piece of the interface means and what it does. When that semantic responsibility is clear, components can be reused reliably, tested predictably, documented accurately, and evolved without breakage.

Atlas's component library serves an investment reasoning platform. Its semantics are unusually precise: the difference between a Conclusion and Proposed Decision Candidate Content, between a Monitoring Trigger and a Review Trigger, between a Recorded Decision and a historical Decision Card variant, is not incidental. These distinctions protect the integrity of the reasoning Atlas supports.

## Why Component Identity Is Determined by Meaning, Not Appearance

Two components that look similar are not the same component if their semantic responsibilities differ. A Warning Message (system feedback about a technical condition) and an Atlas Warning (an analytical concern surfaced by Atlas reasoning) share visual language but have different authorship models, different dismissal rules, different persistence requirements, and different accessibility announcements.

The inverse is also true: two components that look different may be the same component in different states or variants. The current-state Decision Card and the historical Decision Card share the same semantic responsibility — they differ in state, not identity.

## Why Atlas Prefers a Smaller Coherent Library

A large fragmented library of similar components creates decision paralysis for designers, inconsistent implementations from engineers, and an unstable API surface. Atlas prefers fewer canonical components with well-defined variant dimensions over a larger collection of slightly different components with overlapping purposes.

## Why Composition Is Essential to Reasoning Hierarchy

Atlas's reasoning hierarchy — from Conclusion through Supporting Factors, Challenges, Assumptions, Evidence, Opportunity, and Proposed Decision Candidate Content to Decision — is expressed through component composition, not through monolithic components. This composition preserves the hierarchy visually and semantically and allows each level to be independently accessible, testable, historicized, and governed.

## Why Component APIs Must Not Expose Accidental Visual Details

A component's API defines its semantic contract. Atlas component APIs expose semantic props (`severity`, `authorship`, `isHistorical`, `lifecycleState`, `variant`); visual presentation is resolved entirely from tokens. No `style` prop, no raw color values, no spacing overrides.

## Why Shared State Terminology Must Be Canonical

UX-013A and UX-013B each name states per-component-family, in their own committed text; the interim note carries, under explicit Unconfirmed classification, UX-013E's own further claim that UX-013C and UX-013D once did the same. The canonical State Dictionary (below) reconciles all of this into five classes: Interaction States, Lifecycle States, Availability States, Validation States, and AI Content States. Components draw from this canonical vocabulary; they do not invent new state names.

## Why Figma and Engineering Architectures Must Correspond Without Being Identical

Figma represents components visually; engineering implements them as executable code. Their architectures correspond at the semantic level (same names, same variant dimensions, same property names) but diverge at the implementation level, through the Canonical Property Model and Canonical State Model both consume without exception.

## Why Historical Integrity Governs a Distinct Component Contract

Atlas's historical model — the preservation of reasoning, decisions, and monitoring records as immutable records of what was true at a prior point — creates a distinct engineering and design requirement enforced through the `isHistorical` prop, which propagates top-down and disables editing, removes action affordances, relabels accessibility announcements to include the historical date, and prevents any user action that would alter the historical record.

## Why AI Authorship Must Remain Permanently Distinguishable

The Atlas product model places the user in permanent responsibility for investment decisions. AI-authored content must remain permanently distinguishable from user-confirmed content throughout its lifecycle, including after acceptance and editing. The canonical authorship model records the initial author and whether the user has subsequently modified AI content. No design or engineering decision may produce a state in which AI-originated content presents itself as user-authored without an explicit user confirmation action.

## Governing Principles of the Final Component Library

1. One primary semantic responsibility per component.
2. Visual similarity does not imply semantic equivalence.
3. Semantic equivalence must not produce duplicate components.
4. A variant may change presentation or controlled behavior without changing the component's primary meaning.
5. A composed pattern coordinates multiple components but must not become a hidden domain model.
6. Actions are not automatically components.
7. States are not automatically variants.
8. Metadata is composed rather than embedded inconsistently.
9. Historical behavior, authorship visibility, accessibility, responsive behavior, and token usage are part of the component contract, not optional enhancements.
10. Domain meaning must not be invented in presentation components.
11. The `isHistorical` prop propagates top-down from the application layer.
12. AI authorship must never be silently cleared.

---

# 1. Source Specification Reconciliation — Foundation and Reasoning

*(The interim note holds its own, separately classified account of UX-013C's and UX-013D's own claimed contributions; see that document. This section covers only UX-013A and UX-013B, both committed, existing documents.)*

## Purpose of This Section

This section documents the normalization decisions made when assembling UX-013A and UX-013B into this document's canonical Foundation and Reasoning tiers. For each source volume it records: the components and specifications contributed, the overlaps detected, the resolution applied, and unresolved implementation questions carried forward unchanged.

## UX-013A — Foundation Components

**Contribution:** 16 Foundation Components establishing the structural shell of every Atlas Workspace: WorkspaceFrame, WorkspaceHeader, WorkspaceToolbar, WorkspaceFooter, NavigationBar, Breadcrumb, SectionContainer, SectionHeader, Divider, Surface, LayoutContainer, EmptyState, StatusBadge, ProgressIndicator, ScrollContainer, DialogContainer — plus shared Foundation Accessibility Rules, Token Mapping, and Engineering Mapping.

**Overlaps detected and resolutions applied** (all traceable to UX-013A's own committed text, cross-checked against the shared infrastructure this document also carries):

- *StatusBadge ↔ Status Presentation.* StatusBadge is the canonical rendering component. Status Presentation is the architecture mapping semantic states to StatusBadge configurations, not a separate component. No visual component named "Status Presentation" exists in this library.
- *EmptyState ↔ system-specific Empty-State variants.* One canonical EmptyState component with a `subtype` enum prop covering all 12 subtypes.
- *ProgressIndicator ↔ Loading State ↔ AI Working State.* ProgressIndicator is the canonical rendering component. Loading State is a documented behavior pattern. AI Working State is a composed presentation (ProgressIndicator indeterminate + a contextual activity label + optional cancel action) — its own AI-specific labeling convention is documented in the interim note, which references this document's ProgressIndicator and Loading Threshold behavior.
- *DialogContainer ↔ Dialog ↔ Confirmation Dialog.* Three distinct classifications: Component, Composite Component, and Composed Pattern respectively.

**Unresolved implementation questions from UX-013A, preserved unchanged:**
- Section Header stickiness threshold not yet defined; safe default: no stickiness.
- Breadcrumb ellipsis-on-touch behavior requires usability validation.
- Workspace Toolbar presence criteria not fully enumerated.
- Dialog vs. simpler inline confirmation boundary requires product decision.
- Scroll restoration session boundary requires architectural confirmation.

## UX-013B — Reasoning Components

**Contribution:** 19 Reasoning component types across 13 families: Conclusion, SupportingFactorsContainer, FactorItem, FactorGroup, ChallengesContainer, ChallengeItem, AssumptionsContainer, AssumptionItem, EvidenceSummary, EvidenceItem, OpportunitySummary, OpportunityCost, AlternativeItem, Comparison, ScenarioAnalysis, ScenarioItem, Proposed Decision Candidate Content, ReasoningBlock, ContextPanel — plus Reasoning Relationships, States, Accessibility, Token Mapping, and Engineering Mapping.

**Overlaps detected and resolutions applied:**

- *Supporting Metadata ↔ MetadataBlock.* Supporting Metadata is normalized as a configured instance of MetadataBlock (`context="reasoning"`). No component named `SupportingMetadata` exists in this library.
- *Proposed Decision Candidate Content ↔ Atlas Recommendation Presentation.* Candidate Content is the canonical Reasoning component. Atlas-generated authorship is expressed through `isAtlasGenerated={true}` and `authorship="atlas-generated"` on Candidate Content itself, not a second component.
- *ReasoningBlock ↔ ContextPanel.* Confirmed as separate components — distinct structural placement (`<section>` vs. `<aside>`), distinct semantic purposes.
- *EvidenceSummary source display ↔ SourceReference.* EvidenceSummary uses SourceReference instances for each evidence item; no bespoke source display exists in the Reasoning namespace.

**Unresolved implementation questions from UX-013B, preserved unchanged:**
- Atlas Suggestion targeting precision at item level requires AI orchestration architecture confirmation (interim note carries the AI-side resolution of this same open question).
- Contradiction detection scope for ChallengeItem's Contradiction variant requires domain model specification.
- Scenario Analysis vs. a future Scenario Workspace relationship requires product roadmap decision. **This is the same open question `UX-013E`'s own text names at its line ~199; it remains unresolved and is not narrowed by this document.**
- Evidence recency threshold requires product policy definition.

## Reconciliation Summary (Foundation and Reasoning)

| Source Volume | Component Types Contributed | Actions Established | Patterns Established | Items Normalized Away |
|---|---|---|---|---|
| UX-013A | 16 Foundation | 0 | 0 | 0 |
| UX-013B | 19 Reasoning types across 13 families | 0 | 0 | SupportingMetadata → MetadataBlock configuration; EvidenceSummary source → SourceReference |

*(UX-013C's and UX-013D's own reconciliation rows are carried, under explicit unconfirmed/to-be-authored classification, in the interim note — not restated here, since this document does not treat UX-013C or UX-013D as existing sources.)*

---

# 2. Canonical Classification Model

*(Cross-cutting — governs every item in the whole Atlas Component Library, including the interim note's tiers. Retained once here; the interim note references this section.)*

## Purpose of Classifications

The canonical classification model assigns every item in the Atlas Component Library to one of ten classification types, determining how it is built in Figma, implemented in engineering, documented, tested, and versioned. No item may be classified in two ways simultaneously.

## Classification Types

**Primitive** — an atomic visual or behavioral unit with no internal semantic state, rendered by the token system. Figma: base component, no variants. Engineering: a styled element or atomic styled component; no domain props. Testing: visual regression only. Versioning: patch for token changes. Examples: IconPrimitive, TextPrimitive, DividerPrimitive.

**Component** — a reusable unit with one primary semantic responsibility, defined behavior, a stable accessibility contract, and a documented API. Figma: one component set per the Figma Property Standard. Engineering: a typed React component; no `style` prop. Testing: full suite. Versioning: semantic versioning. Examples: Conclusion, StatusBadge, SourceReference, FollowUp.

**Composite Component** — a component whose primary responsibility requires composing multiple sub-components in a defined structure; owns the composition. Examples: DecisionCard, WorkspaceHeader, MetadataBlock, ReviewSummary, ImplementationPlan.

**Action** — a discrete user-initiated operation with a defined trigger, consequence, optional confirmation, and undo window; not a standalone component. Examples: AcceptSuggestion, RecordDecision, DismissFeedback, AmendDecision, StartReview.

**Behavior** — a shared runtime behavior implemented once and consumed by multiple components through a shared hook, utility, or service; not a visual artifact. Examples: FocusManagement, DismissRestore, UndoWindow, AutosaveIndication, ScrollRestoration, LoadingThreshold.

**State** — a discrete condition with defined visual treatment, interaction rules, and accessibility announcements; not user-selectable. Examples: loading, saving, historical, dismissed, triggered, breached, partiallyAccepted.

**Variant** — a controlled presentation or behavioral difference that does not change primary semantic responsibility; user-selectable. Examples: `compact` vs. `expanded` (MetadataBlock); `inline` vs. `section` vs. `workspace` (ValidationMessage); `horizontal` vs. `vertical` (Divider).

**Composed Pattern** — a documented strategy for composing multiple canonical components for a defined multi-component task; the pattern does not own state. Examples: DecisionTimeline, ReasoningToDecisionFlow, SuggestionComparison, ErrorRecovery, ConfirmationFlow, CurrentToHistoricalTransition.

**Semantic Concept** — an important Atlas domain concept represented through components but not itself a component. Examples: Reasoning, Conclusion, Proposed Decision Candidate Content, Decision, Monitoring, Historical State, Authorship, Confidence.

**Deferred Item** — a component, variant, action, or pattern acknowledged but not yet justified by approved product requirements. Example: Notification Center.

## Ambiguous Case Resolutions

| Item | Canonical Classification | Reasoning |
|---|---|---|
| StatusBadge | Component | Owns its semantic rendering contract; used across all categories |
| Status Presentation | Architecture document (not a component) | Maps semantic states to StatusBadge configurations; no visual form |
| AcceptSuggestion | Action | No independent visual form; appears as a button within AtlasSuggestion |
| Decision Timeline | Composed Pattern | Coordinates TimelineEntry × n, SectionContainer, filtering; no single owning component |
| WorkspaceFrame | Component | Owns the structural shell of every Workspace |
| Dialog | Composite Component | Content system inside the DialogContainer structural shell |
| HistoricalDecision | State + Variant of DecisionCard | Same semantic responsibility as DecisionCard |
| AI Working State | Behavior + Composed Pattern | ProgressIndicator + contextual label; not a standalone component |
| ConfidencePresentation | Component (variant-driven) | Distinct rendering contract for epistemic qualification |
| RelationshipReference | Component | Distinct rendering contract for cross-entity navigation |
| Responsive Grid | Variant of LayoutContainer | Responsive behavior is a variant dimension, not a separate component |
| Scroll Restoration | Behavior | Implemented once as a shared hook |
| EmptyState | Component | 12 subtypes expressed through `subtype` prop, not separate components |
| SupportingMetadata | MetadataBlock configuration (not a component) | Normalized with `context="reasoning"` |
| SkeletonState | Variant of ProgressIndicator | Presentation mode, not a separate component family |
| ConfirmationDialog | Composed Pattern | DialogContainer + Dialog (Confirmation type) + content rules |
| AtlasRecommendationPresentation | Authorship configuration (not a component) | Proposed Decision Candidate Content with `isAtlasGenerated={true}` |
| Notification Center | Deferred | No approved product requirements establish this |
| AIUnavailableState | UnavailableDataState (reason="ai-unavailable") | Same component; reason is a prop value |

---

# 3. Canonical Component Taxonomy

The taxonomy uses **three tiers** and **14 canonical categories**. This document is the operative, canonical home for Tier 1 in full, for Reasoning within Tier 2, and for the cross-cutting Tier 3 infrastructure categories (their content is genuinely universal — used by every tier, owned by no single domain — per the Atlas UX Source Correction Plan's own instruction that such content have one canonical owner). Decision, Monitoring, Historical, and AI Collaboration are named here only to complete the taxonomy; their own operative content lives in the interim note.

## Tier 1 — Structural (Foundation)

Tier 1 components establish the structural environment every Atlas Workspace requires. They depend only on Design Tokens. All other tiers depend on Tier 1.

**Foundation** — structural shell of every Workspace. Figma: `Foundation/`. Engineering: `@atlas/foundation`. Owner: Design System. Dependencies: Tokens only. Primary components: WorkspaceFrame, WorkspaceHeader, WorkspaceToolbar, WorkspaceFooter, SectionContainer, SectionHeader, Surface, Divider, StatusBadge, ProgressIndicator, EmptyState, ScrollContainer, DialogContainer.

**Layout** — spatial organization. Figma: `Foundation/Layout/`. Engineering: `@atlas/foundation` (`layout`). Dependencies: Foundation. Primary components: LayoutContainer (Column, Stack, Row, Split, Grid, Adaptive variants).

**Navigation** — location communication and movement. Figma: `Foundation/Navigation/`. Engineering: `@atlas/foundation` (`navigation`). Dependencies: Foundation. Primary components: NavigationBar, Breadcrumb.

## Tier 2 — Content (Domain-Specific): Reasoning

**Reasoning** — components through which investment reasoning is structured, displayed, examined, and preserved. Scope: Conclusion, Supporting Factors, Challenges, Assumptions, Evidence, Opportunity, Opportunity Cost, Comparison, Scenario Analysis, Proposed Decision Candidate Content, Reasoning Block, Context Panel. Does not include Decision or Monitoring components. Figma: `Reasoning/`. Engineering: `@atlas/reasoning`. Owner: Product Design + Domain. Dependencies: Foundation, Metadata & Provenance. **Cross-category references:** Reasoning components reference Decision-tier components via typed IDs only (e.g., AssumptionItem references a MonitoringCondition via `monitoringConditionId`) — this document does not import or redefine the Decision/Monitoring implementation those IDs point to; see the interim note for that content.

*(Decision, Monitoring, and Historical — the remaining Tier 2 categories — are the interim note's own operative content; named here only for taxonomy completeness: Decision governs the decision lifecycle from proposal through recorded history; Monitoring governs post-decision condition tracking, triggers, and reviews; Historical governs chronological event display and completed lifecycle records.)*

## Tier 3 — System (Cross-Domain): Infrastructure Categories Owned by This Document

**Metadata & Provenance** — authorship, timestamps, versions, sources, relationships, and epistemic qualifications, displayed consistently across every Workspace and category. Scope: MetadataBlock, Author, Timestamp, Version, SourceReference, SourceGroup, RelationshipReference, ConfidencePresentation, AIAuthorshipIndicator (shared with AI Collaboration; primary ownership here). Figma: `Metadata/`. Engineering: `@atlas/metadata`. Owner: Design System. Dependencies: Foundation only.

**Status & Feedback** — communicating system conditions, validation results, and informational states. Scope: StatusBadge (shared with Foundation; primary specification there), ValidationMessage, InformationalMessage, WarningMessage (system), ErrorMessage, SuccessConfirmation. Not AtlasWarning (analytical) — that belongs to AI Collaboration, in the interim note. Figma: `Feedback/`. Engineering: `@atlas/feedback`. Owner: Design System. Dependencies: Foundation.

**Loading & Availability** — loading progress, data availability, permission restrictions, and connection state. Scope: ProgressIndicator (shared with Foundation), EmptyState (shared with Foundation), PermissionState, UnavailableDataState, OfflineConnectionState. Figma: `Feedback/Loading/`, `Feedback/Availability/`. Engineering: `@atlas/feedback` (`loading`, `availability`). Owner: Design System. Dependencies: Foundation.

**Overlay & Dialog** — content requiring focused attention or a required response, above the primary surface. Scope: Dialog (content system, used inside DialogContainer), Toast, InlineNotice, Banner. ConfirmationDialog is a Composed Pattern, not a category component. Figma: `Overlay/`. Engineering: `@atlas/overlay`. Owner: Design System. Dependencies: Foundation.

**Notification** — background system events and state changes outside the current user action. Scope: SystemNotification. Notification Center: Deferred. Figma: `Notification/`. Engineering: `@atlas/notification`. Owner: Design System. Dependencies: Foundation, Status & Feedback.

*(AI Collaboration — the remaining Tier 3 category — is the interim note's own operative content: components through which Atlas AI suggestions, insights, questions, clarifications, warnings, and summaries are presented, evaluated, and actioned.)*

**Design rationale for this split, stated explicitly:** the Atlas UX Source Correction Plan's own Section 10 instructs that cross-cutting content be "retained once in the canonical assembly and referenced (not duplicated) by the interim document" wherever the Plan supports that outcome. Every infrastructure category assigned to this document here (Metadata & Provenance, Status & Feedback, Loading & Availability, Overlay & Dialog, Notification) depends only on Foundation and Tokens — none of them is owned by, or requires, Decision, Monitoring, or AI-Collaboration semantics to be specified. AI Collaboration is the one Tier 3 category retained in the interim note because its own semantic ownership is inherently AI-specific and its content traces to UX-013D, not to a committed, confirmed source.

---

# 4. Canonical Naming System

*(Cross-cutting; the interim note references this section rather than restating it.)*

## Naming Rules

**Semantic names** (preferred for components) reflect what the component means, not how it looks or where it sits. Correct: `Conclusion`, `SupportingFactors`, `ChallengeItem`, `MonitoringCondition`, `DecisionCard`. Incorrect: `ReasoningCard`, `YellowWarningBox`, `BigHeaderArea`, `LeftPanel`.

**Structural names** are used when structural role is precisely the semantic responsibility. Correct: `WorkspaceFrame`, `SectionContainer`, `SectionHeader`, `LayoutContainer`, `DialogContainer`.

**Behavioral names** are used for behavior-driven structural components. Correct: `ScrollContainer`, `DialogContainer`.

**Action names:** Verb + Noun, PascalCase. Correct: `AcceptSuggestion`, `RecordDecision`, `DismissFeedback`, `StartReview`.

**State names:** descriptive adjective or past-tense verb; camelCase in engineering, Title Case in Figma. Correct: `historical`, `loading`, `dismissed`, `proposed`, `partiallyAccepted`.

**Variant names:** descriptive of the variant dimension, not the component; PascalCase in Figma, camelCase string literal in engineering. Correct: `compact`, `inline`, `historical`, `blocking`, `determinate`.

**Property names:** semantic, not visual; camelCase in engineering, Title Case in Figma. Correct: `isHistorical`, `authorship`, `lifecycleState`, `severity`, `subtype`. Incorrect: `style`, `color`, `borderWidth`, `fontSizeMultiplier`.

**Historical content:** expressed through `isHistorical`, not a separate "Historical" component name. Correct: `DecisionCard` with `isHistorical={true}`. Incorrect: `HistoricalDecisionCard` as a separate component.

**AI-authored content:** expressed through `authorship` and `isAtlasGenerated`, not a separate "AI"/"Atlas" prefix on the parent component. Correct: `Proposed Decision Candidate Content` with `isAtlasGenerated={true}`. Incorrect: `AtlasRecommendation` as a separate component.

**Namespace prefixes** are used only for components whose semantic responsibility is inherently AI-originated (AtlasSuggestion, AtlasInsight, AtlasQuestion, AtlasClarification, AtlasWarning, AIGeneratedSummary, AIAuthorshipIndicator) — those components' own detailed specification lives in the interim note; this naming rule itself is cross-cutting and applies to them exactly as it applies to Foundation and Reasoning names.

## Prohibited Visual Names

| Prohibited Name | Reason | Canonical Replacement |
|---|---|---|
| `Panel` (generic) | Describes visual form | `ContextPanel` or `SectionContainer` |
| `Card` (generic) | Describes visual form | `DecisionCard` or `ReasoningBlock` depending on content |
| `Modal` | Describes visual presentation layer | `Dialog` |
| `Chip` | Describes visual form | `StatusBadge` |
| `Box` | Structural, not semantic | `SectionContainer` or `Surface` |
| `Container` (generic) | Overloaded; no stable meaning | `SectionContainer`, `LayoutContainer`, `ScrollContainer`, `DialogContainer` |
| `Wrapper` | Implementation detail | The structurally appropriate component |
| `Widget` | Vague, not semantic | The specific component for the semantic purpose |

## Naming Audit — Foundation and Reasoning Items Renamed from Source Volumes

| Previous Name (Source Volume) | Canonical Name | Change Type | Reason |
|---|---|---|---|
| `SupportingMetadata` (UX-013B) | `MetadataBlock` with `context="reasoning"` | Component → Configuration of existing component | Reasoning-specific metadata is a configuration of the general MetadataBlock |

*(Decision-, Monitoring-, and AI-tier renamed items — HistoricalDecision, HistoricalMonitoringRecord, HistoricalReview, DecisionRationaleSummary, AtlasRecommendationPresentation, SkeletonState, AIWorkingState, StatusPresentation, NotificationCenter, AIUnavailableState, and the Decision Card lifecycle-variant clarifications — are carried, under explicit classification, in the interim note, since their own provenance traces to the currently-unconfirmed UX-013C/UX-013D account.)*

---

# 5. Duplicate, Variant, and Pattern Audits — Foundation and Reasoning

## StatusBadge vs. Status Presentation

StatusBadge is the canonical rendering component, accepting a semantic `type` enum. Status Presentation is the mapping layer between domain state and StatusBadge configuration — an architecture document, not a component; it has no Figma or engineering component equivalent.

## EmptyState vs. System-Specific Empty-State Variants

One canonical EmptyState component with a `subtype` enum covering all 12 subtypes (`no-content-yet`, `no-results`, `no-changes`, `no-monitoring-events`, `no-historical-records`, `no-sources`, `no-permissions`, `no-available-data`, `ai-unavailable`, `filtered-empty`, `search-empty`, `completed-empty`). Figma: one component set with a `Subtype` property; Engineering: one `EmptyState` component with `subtype: EmptyStateSubtype` and an optional `contentOverride`.

## DialogContainer vs. Dialog vs. Confirmation Dialog

DialogContainer owns the structural shell (focus trap, scrim, sizing, Escape-close, `role="dialog"`, portal rendering). Dialog owns the content system inside it (7 categories: Informational, Task, Review, Comparison, Error Recovery, Permission, Confirmation). Confirmation Dialog is a specific composed use of Dialog inside DialogContainer. Three distinct classifications: Foundation Component, Overlay Composite Component, Overlay Composed Pattern respectively — no standalone `ConfirmationDialog` Figma set or engineering export exists.

## ProgressIndicator vs. Loading State vs. AI Working State

ProgressIndicator owns all loading/progress rendering (determinate, indeterminate, skeleton, completion, saving, review progress). Loading State is the behavior governing when it appears (300ms threshold) and how it transitions. AI Working State is a composed presentation (ProgressIndicator indeterminate + contextual label + optional cancel) documented, in its own AI-specific labeling convention, in the interim note, which references this document's ProgressIndicator and LoadingThreshold behavior.

## AtlasWarning vs. WarningMessage vs. ValidationMessage

| Dimension | AtlasWarning (interim note) | WarningMessage | ValidationMessage |
|---|---|---|---|
| Semantic ownership | Atlas AI reasoning analysis | System operations | User input validation |
| Authorship model | AI-generated; acknowledgement transfers record | System-generated; no authorship model | User-triggered; no authorship model |
| Dismissal rule | Acknowledged with a note; contributes to Challenges | Generic dismissal | Persists until input corrected |
| Accessibility | `aria-live="polite"`, "Atlas warning" prefix; acknowledgement required | `aria-live="polite"`, standard announcement | `role="alert"` at blocking severity |
| API surface | `severity`, `concern`, `affectedContext`, `reason`, `isAcknowledged`, `authorship` | `severity`, `message`, `isDismissed` | `severity`, `message`, `affectedFieldId`, `placement` |

Three separate canonical Components. Merging any two would produce an API with no stable meaning. WarningMessage and ValidationMessage are this document's own operative Status & Feedback components; AtlasWarning's own full specification is the interim note's, cross-referenced here for the comparison's completeness.

## MetadataBlock vs. Supporting Metadata

MetadataBlock is the canonical Composite Component; Supporting Metadata is a configured instance (`context="reasoning"`). No component named `SupportingMetadata` exists.

## Proposed Decision Candidate Content vs. Atlas Recommendation Presentation

Proposed Decision Candidate Content is the canonical Reasoning Component. Atlas-generated authorship is `isAtlasGenerated={true}`, `authorship="atlas-generated"`, with AIAuthorshipIndicator (interim note) shown — not a second component. AtlasSuggestion may be displayed alongside Candidate Content to present an "Accept as draft" action; this is a composition, not a third component.

## SourceReference vs. Evidence Summary Source Representation

SourceReference is the canonical Component (Metadata & Provenance, this document). EvidenceSummary's `evidence[]` items each carry a `source: SourceRef` object rendered through a SourceReference instance. No bespoke source display exists in the Reasoning namespace.

## Component-versus-Variant Resolutions (Foundation/Reasoning-relevant)

- Feedback severity forms (Informational/Warning/Error Message, Success Confirmation): retained as four distinct Components (Status & Feedback), not merged — their accessibility, persistence, and placement rules differ materially. Shared visual language via tokens only.
- Inline Notice / Banner severity forms: variants (`severity` prop) of one component each.
- Source Reference compact/expanded forms: variants (`display` prop).
- Metadata Block compact/expanded forms: variants (`display` prop).
- Empty-State subtypes: variants (`subtype` prop).
- Loading-state variants (Determinate, Indeterminate, Completion, Saving, Skeleton, Review Progress): variants (`variant` prop) of ProgressIndicator.
- Permission-state variants: variants (`reason` prop) of PermissionState (interim note's own component; naming rule stated here for completeness).
- Historical Reasoning Blocks: all Reasoning components support the `isHistorical` prop; no separate historical component class.

## Component-versus-Pattern Resolutions (Foundation/Reasoning-relevant)

- Comparison View → Composite Component (owns its full presentation, 4 variants: Before/After, Alternative, Allocation, Historical).
- Suggestion Comparison → Composed Pattern (Comparison configured for suggestion comparison, per the interim note's AtlasSuggestion Compare action).
- Workspace Header with Actions and Status → Composite Component (owns its complete composition).
- Reasoning Block → Component, not a pattern (single component with defined anatomy).
- Decision Card, Source Group, Implementation Plan, Outcome Tracking, Review Summary, Decision History, Decision Timeline, Decision Finalization Flow, Current-to-Historical Transition: Decision/Monitoring-tier classifications, carried in the interim note.

---

# 6. Canonical Component Inventory — Foundation and Reasoning Categories

*(Full property/state/variant/dependency detail per component is unchanged from UX-013E's own Section 8; restated here in full for these two categories.)*

## Foundation Category

| Canonical Name | Classification | Semantic Purpose | Primary Workspace | Dependencies | Core Properties | Eligible States | Primary Variants | Persistence | Historical | Authorship | Figma Priority | Eng Priority | Owner | Maturity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WorkspaceFrame | Component | Structural shell of every Workspace | All | Tokens | workspaceId, variant, hasFooter, isLoading | loading, error | Standard, Dashboard, Historical | None | Via children | Via children | P0 | P0 | Design System | Candidate |
| WorkspaceHeader | Composite | Workspace identity and status display | All | WorkspaceFrame | workspaceTypeLabel, subjectTitle, status indicators | loading, historical | Standard, Dashboard, Historical | None | isHistorical | None | P0 | P0 | Design System | Candidate |
| WorkspaceToolbar | Component | Secondary Workspace actions | All | WorkspaceFrame | actions[], maxVisible | — | Standard | None | No | No | P1 | P1 | Design System | Candidate |
| WorkspaceFooter | Component | Primary action and completion control | Decision, Portfolio | WorkspaceFrame | primaryAction, completionState | completion-ready, completion-blocked, post-completion | Standard, Completion-ready, Completion-blocked | None | No | No | P0 | P0 | Design System | Candidate |
| NavigationBar | Component | Atlas contextual path display | All | WorkspaceFrame | breadcrumb, relatedLinks | — | Standard | None | No | No | P1 | P1 | Design System | Candidate |
| Breadcrumb | Component | Hierarchical location display | All | NavigationBar | items[], currentLabel | collapsed, expanded | Standard | Session | No | No | P1 | P1 | Design System | Candidate |
| SectionContainer | Component | Named, expandable content region | All | WorkspaceFrame | sectionId, isExpanded, variant | expanded, collapsed, loading, updated, draft, historical, empty, error | Standard, Fixed, Read-Only, Historical, Empty | Session (expansion) | isHistorical | No | P0 | P0 | Design System | Candidate |
| SectionHeader | Component | Section identity and expansion control | All | SectionContainer | title, isExpanded, hasActions | expanded, collapsed | Standard, Fixed, With Actions, Compact | None | Via parent | No | P0 | P0 | Design System | Candidate |
| Divider | Component | Semantic content boundary | All | None | orientation, variant | — | Horizontal, Vertical, Inset | None | No | No | P1 | P1 | Design System | Stable |
| Surface | Component | Tonal background region | All | Tokens | tier, variant | — | Tier 0–3, Historical, Monitoring | None | Via isHistorical | No | P1 | P1 | Design System | Candidate |
| LayoutContainer | Component | Spatial organization | All | None | type, gap, maxWidth | — | Column, Stack, Row, Split, Adaptive, Grid | None | No | No | P0 | P0 | Design System | Candidate |
| EmptyState | Component | Meaningful absence communication | All | None | subtype, headline, action | — | 12 subtypes via `subtype` prop | None | No | No | P0 | P0 | Design System | Candidate |
| StatusBadge | Component | Labeled status indicator | All | Tokens | type, label | — | 9 types | None | Via type | No | P0 | P0 | Design System | Candidate |
| ProgressIndicator | Component | Progress and loading representation | All | None | variant, value, max, label | loading, saving, completed | Determinate, Indeterminate, Skeleton, Completion, Saving, Review Progress | None | No | No | P1 | P1 | Design System | Candidate |
| ScrollContainer | Component | Scroll behavior management | All | WorkspaceFrame | workspaceId, hasNestedScroll | — | Standard | Session (position) | No | No | P1 | P1 | Design System | Candidate |
| DialogContainer | Component | Dialog structural shell | All | None | size, isDismissible | open, closed | Small, Medium, Full-width | None | No | No | P0 | P0 | Design System | Candidate |

## Reasoning Category

| Canonical Name | Classification | Semantic Purpose | Primary Workspace | Core Properties | Historical | Authorship | Eng Priority |
|---|---|---|---|---|---|---|---|
| Conclusion | Component | Primary output of a reasoning session | Investment, Portfolio, Decision | statement, variant, isAtlasGenerated, isEditable | Yes | Yes | P0 |
| SupportingFactorsContainer | Composite | Section for named supporting reasons | Investment, Decision | factors[], isEditable, groupingEnabled | Yes | Yes | P0 |
| FactorItem | Component | Single named supporting reason | Investment, Decision | id, name, explanation, weight, evidence[], dependedOnByAssumptionId | Yes | Yes | P0 |
| FactorGroup | Component | Named category of related factors | Investment, Decision | groupId, label, factors[] | Yes | No | P1 |
| ChallengesContainer | Composite | Section for named concerns | Investment, Decision | challenges[], isEditable | Yes | Yes | P0 |
| ChallengeItem | Component | Single named challenge | Investment, Decision | id, name, severity, isAcknowledged, contradictsId, isAtlasSurfaced | Yes | Yes | P0 |
| AssumptionsContainer | Composite | Section for explicit conditions | Investment, Decision | assumptions[], isEditable | Yes | Yes | P1 |
| AssumptionItem | Component | Single named assumption | Investment, Decision | id, name, status, dependedOnBy[], monitoringConditionId | Yes | Yes | P1 |
| EvidenceSummary | Composite | Section for reasoning evidence base | Investment | evidence[], isEditable | Yes | Yes | P2 |
| EvidenceItem | Component | Single evidence reference | Investment | id, sourceLabel, date, relevanceNote, linkedFactorId | Yes | Yes | P2 |
| OpportunitySummary | Component | Investment opportunity thesis | Investment | opportunityStatement, whyItExists, windowStatement, isEditable | Yes | Yes | P1 |
| OpportunityCost | Composite | Explicit foregone alternatives | Decision | chosenPath, foregoneAlternatives[] | Yes | Yes | P1 |
| AlternativeItem | Component | Single foregone alternative | Decision | id, alternativeName, whatItOffered, whyNotChosen | Yes | Yes | P1 |
| Comparison | Composite | Side-by-side structured comparison | Decision, Portfolio | type, columns[], rows[] | Yes | No | P1 |
| ScenarioAnalysis | Composite | Structured scenario examination | Decision, Investment | scenarios[] | Yes | Yes | P2 |
| ScenarioItem | Component | Single named scenario | Decision, Investment | id, scenarioType, name, probability, conditions, implications | Yes | Yes | P2 |
| Proposed Decision Candidate Content | Component | Suggested direction from reasoning | Investment, Decision | source, statement, primaryReason, isEditable | Yes | Yes | P1 |
| ReasoningBlock | Component | Named container for unclassified reasoning | All | id, blockName, isExpanded, isEditable | Yes | Yes | P2 |
| ContextPanel | Component | Supplementary contextual information | Investment, Decision | variant, panelName, crossReferences[] | Yes | No | P2 |

## Cross-Cutting Infrastructure Categories (Operative Here)

| Canonical Name | Classification | Semantic Purpose | Core Properties | Maturity |
|---|---|---|---|---|
| MetadataBlock | Composite | Provenance information composition | display, author, timestamp, version, source, relationship, confidence | Stable |
| Author | Component | Authorship display | authorshipCategory, displayName, role | Stable |
| Timestamp | Component | Point-in-time display | timestampType, value, display, precision | Stable |
| Version | Component | Version identifier display | identifier, createdAt, author, changeSummary | Candidate |
| SourceReference | Component | Source display with navigation | sourceTitle, sourceType, date, availability, display | Candidate |
| SourceGroup | Composite | Multiple source references composed | sources[], grouping, deduplication, isExpanded | Candidate |
| RelationshipReference | Component | Cross-entity relationship link | sourceObject, targetObject, relationshipLabel, direction, display | Candidate |
| ConfidencePresentation | Component | Epistemic qualification display | confidenceType, qualitativeLabel, context | Candidate |
| StatusBadge | Component | Labeled status indicator (shared with Foundation) | 9 canonical types | Stable |
| ValidationMessage | Component | Field/section/workspace validation feedback | Informational, Recommended, Blocking, Historical-integrity | Candidate |
| InformationalMessage | Component | Non-urgent system information | — | Candidate |
| WarningMessage | Component | System-level concern | Standard | Candidate |
| ErrorMessage | Component | System failure feedback | 8 categories | Candidate |
| SuccessConfirmation | Component | Calm completion confirmation | — | Candidate |
| ProgressIndicator | Component | Progress and loading representation (shared with Foundation) | all variants | Candidate |
| EmptyState | Component | Meaningful absence (shared with Foundation) | all 12 subtypes | Candidate |
| PermissionState | Component | Permission limitation display | Candidate |
| UnavailableDataState | Component | Data unavailability communication | Candidate |
| OfflineConnectionState | Component | Connection state display | Candidate |
| Dialog | Composite | Content system inside DialogContainer | Candidate |
| Toast | Component | Transient action-result feedback | Candidate |
| InlineNotice | Component | Contextual inline feedback | Candidate |
| Banner | Component | Workspace or system-level notice | Candidate |
| SystemNotification | Component | Background system event communication | Candidate |

*(Decision, Monitoring, AI Collaboration category inventories are the interim note's own operative content.)*

---

# 7. Action, Pattern, and Semantic Concept Inventories — Foundation/Reasoning/Infrastructure-Relevant Entries

## Actions (infrastructure- and Reasoning-relevant)

| Canonical Name | Purpose | Eligible Components | Confirmation Required | Undo Window | Accessibility Contract |
|---|---|---|---|---|---|
| RetryOperation | Retry a failed operation | ErrorMessage | No | N/A | Focus returns to retry; error re-announced if it fails again |
| UndoAction | Reverse the most recent action within undo window | Any supporting component | No | 5s (structural); 30s (autosave) | `aria-live="polite"`: "Action undone" |
| DismissFeedback | Remove dismissible feedback from view | Toast, InlineNotice, Banner, AtlasSuggestion | No | Session restore (suggestion only) | `aria-live="polite"`: "Dismissed" |
| RequestAccess | Initiate a permission request | PermissionState | No | N/A | Focus to request form |
| CancelOperation | Abort an in-progress operation | ProgressIndicator (when cancellable) | No | N/A | `aria-live="polite"`: "Operation cancelled" |

*(AcceptSuggestion, PartiallyAcceptSuggestion, RejectSuggestion, DismissSuggestion, RestoreSuggestion, ExplainSuggestion, CompareSuggestion — AI Collaboration actions — and FinalizeDecision, RecordDecision, AmendDecision, SupersedeDecision, StartReview, CompleteReview — Decision/Monitoring actions — are the interim note's own.)*

## Patterns (Foundation/Reasoning/infrastructure-relevant)

| Pattern Name | Purpose | Participating Components | State Ownership | Accessibility Focus |
|---|---|---|---|---|
| WorkspaceShell | Complete Workspace assembly | WorkspaceFrame, WorkspaceHeader, WorkspaceToolbar, WorkspaceFooter, NavigationBar, ScrollContainer | WorkspaceFrame | Single `<h1>` in Header; `<main>` landmark |
| ReasoningHierarchy | Ordered reasoning structure in a Workspace | SectionContainer × n, Conclusion, SupportingFactorsContainer, ChallengesContainer, AssumptionsContainer | Each Section owns its expansion state | Headings nest correctly; Tab order follows visual order |
| ValidationRecovery | Responding to validation failures | ValidationMessage + affected field/section | Application layer | Focus moved to first error |
| ErrorRecovery | Responding to system errors | ErrorMessage, RetryOperation, alternative path | Application layer | Error announced; retry offered |
| OfflineRecovery | Handling connection loss and restoration | OfflineConnectionState, ProgressIndicator (sync), queued actions | Application layer | Connection state announced |
| PermissionRecovery | Responding to permission limitations | PermissionState, RequestAccess | Application layer | Permission restriction announced |
| ResponsiveCondensation | Adapting dense content for smaller viewports | All components | Component-local | Condensed content remains accessible |
| ConfirmationFlow | User-required confirmation before consequential action | DialogContainer, Dialog (Confirmation), primary + cancel actions | Application layer | Focus to confirmation dialog; Escape to cancel |
| SourceInspection | Viewing and navigating source references | SourceGroup, SourceReference, RelationshipReference | No state | External link warning |
| MetadataExpansion | Progressive disclosure of metadata | MetadataBlock (compact → expanded), Timestamp, Author, Version | Component-local | Expanded content announced |

*(ReasoningToDecisionFlow, DecisionFinalization, DecisionRecording, DecisionMonitoring, TriggeredReview, ScheduledReviewFlow, DecisionTimeline, HistoricalInspection, SuggestionReview, SuggestionComparison — patterns whose primary participant components are Decision-, Monitoring-, or AI-tier — are the interim note's own; where a pattern above cross-references one of these by name, the reference is to the interim note.)*

## Semantic Concepts (Foundation/Reasoning-relevant)

| Concept | Semantic Meaning | Primary Component Carriers | Direct Component? | Misuse to Prevent |
|---|---|---|---|---|
| Reasoning | The structured process of working through evidence, factors, and challenges to reach a conclusion | Conclusion, SupportingFactors, Challenges, Assumptions, ReasoningBlock | No | Do not use "reasoning" as a generic label for any analytical display |
| Conclusion | The current state of what the reasoning indicates to be true | Conclusion component | Yes | Do not conflate with Decision or Proposed Decision Candidate Content |
| Proposed Decision Candidate Content | A suggested direction that follows from reasoning; not a decision | Candidate Content component | Yes | Do not present as binding or equivalent to a Decision |
| Evidence | The factual grounding from which reasoning is derived | EvidenceSummary, EvidenceItem, SourceReference | Yes | Do not conflate evidence with reasoning conclusions |
| Source | The origin of a piece of information | SourceReference, SourceGroup | Yes | Do not imply reliability merely through visual presentation |
| Reference | A navigable pointer to a related object | RelationshipReference | Yes | Do not invent domain relationships in the presentation layer |
| Authority | The epistemic weight of a source — communicated qualitatively, not visually | ConfidencePresentation, SourceReference | No | Do not use visual hierarchy to imply source authority |
| Confidence | The degree to which a claim is supported by evidence | ConfidencePresentation | Yes | Do not use numeric percentages without justified basis; qualitative only |
| Uncertainty | Acknowledged gaps, limitations, or ambiguity | ConfidencePresentation (uncertainty variant) | Yes | Do not suppress uncertainty to appear more authoritative |
| Historical State | The immutable record of what was true at a prior point in time | `isHistorical` prop on all supporting components | No | Do not allow historical content to appear editable |
| Authorship | The traceable attribution of who or what created or modified content | Author component, AIAuthorshipIndicator, `authorship` prop | Yes | Do not allow AI authorship to silently become user authorship |
| Status | The current lifecycle or operational state of an object | StatusBadge, Status Presentation | Yes | Do not conflate lifecycle status with interaction state |
| Progress | Measurable advancement toward a defined completion state | ProgressIndicator | Yes | Do not fabricate percentages |
| Completion | The state of having reached a defined end state | StatusBadge, ProgressIndicator, WorkspaceFooter | Yes | Do not celebrate completion; treat it as calm and documentary |
| Availability | Whether content or functionality is currently accessible | EmptyState, UnavailableDataState, PermissionState, OfflineConnectionState | Yes | Do not conflate unavailability with error |
| Permission | Authorization to view or act | PermissionState | Yes | Do not reveal protected information through permission state error detail |
| Validation | Confirmation or challenge of input correctness | ValidationMessage | Yes | Do not use validation to punish the user; guide recovery |

*(Decision, Implementation, Monitoring, Review, Outcome — Decision/Monitoring-tier concepts — are the interim note's own.)*

---

# 8. Canonical Property Model

*(Cross-cutting; identical to UX-013E's own Section 12 in full — every property below applies library-wide, to both this document's tiers and the interim note's. Retained once here; the interim note references this section.)*

| Property | Semantic Meaning | Type | Default | Eligible Categories | Accessibility | Persistence | Anti-pattern |
|---|---|---|---|---|---|---|---|
| `id` | Stable unique identifier | `string` | Required | All | `aria-labelledby`/`describedby` targets | Server | Do not use as display label |
| `label` | Human-readable name | `string` | Required where applicable | All | `aria-label` | Content | Do not use generic labels like "Item" |
| `title` | Primary heading or name | `string` | Required where applicable | Foundation, Decision, Monitoring | Rendered as heading element | Content | Do not use as tooltip |
| `description` | Supporting explanatory text | `string` | Optional | Most | `aria-describedby` | Content | Do not use for primary purpose |
| `status` | Lifecycle or operational state | Per-category typed enum | Component default | Decision, Monitoring, Review, AI, Source | Via StatusBadge text | Server | Do not use generic `status` across incompatible domains |
| `lifecycleState` | Decision-specific lifecycle position | `DecisionLifecycleState` enum | `'draft'` | Decision | Announced on change | Server | Do not use for non-Decision components |
| `variant` | Controlled presentation/behavioral difference | Per-component enum | Component default | All | Variant-specific rules apply | None | Do not use as an escape hatch |
| `severity` | Importance/urgency classification | `'informational' \| 'material' \| 'blocking'` | `'informational'` | Challenges, ValidationMessage, WarningMessage, AtlasWarning | Via StatusBadge text; not color alone | None | Do not assign Blocking without justification |
| `isHistorical` | Content is from a prior immutable session | `boolean` | `false` | All supporting components | All labels include historical date; editing disabled | Server | Do not allow historical content to appear editable |
| `isEditable` | Content may be modified | `boolean` | `false` | Reasoning, Decision, AI | Editing controls shown | None | Do not default to `true` in historical contexts |
| `isAtlasGenerated` | Content was created by Atlas AI | `boolean` | `false` | All AI-capable | Attribution indicator shown | Server | Do not silently clear on user edit |
| `isUserModified` | User has modified AI-generated content | `boolean` | `false` | Reasoning, Decision | Attribution updates | Server | Do not conflate with full user authorship |
| `authorship` | Categorized origin of content | `AuthorshipType` enum | `'user'` | AI, Metadata, Reasoning, Decision | Via AIAuthorshipIndicator | Server | Do not allow AI authorship to silently become user authorship |
| `historicalDate` | Date of the historical session | `Date` | — | All with `isHistorical` | Required in all ARIA labels when historical | Server | Required when `isHistorical={true}` |
| `confidence` | Qualitative epistemic qualification | `ConfidenceQualifier` enum | — | Reasoning, AI | Via ConfidencePresentation | None | Do not use numeric percentage without justified basis |
| `source` | Single source reference | `SourceRef` object | — | Evidence, AI | Source navigable as a link | None | Do not imply source authority through visual hierarchy |
| `sources` | Multiple source references | `SourceRef[]` | `[]` | Evidence, AI, Decision | Source Group renders them | None | Do not deduplicate silently |
| `timestamp` | Generic point-in-time reference | `Date` | — | Metadata | `<time>` element with `datetime` | Server | Do not show relative timestamps in historical contexts |
| `createdAt` | Creation time | `Date` | — | Decision, Monitoring, Review | `<time>` | Server | Required for all Recorded Decisions |
| `updatedAt` | Last modification time | `Date` | — | Reasoning, Decision | Updated indicator shown | Server | Do not show in historical contexts |
| `recordedAt` | Time of formal recording | `Date` | — | Decision | Required in historical record | Server | Must not be mutable |
| `version` | Semantic version identifier | `string` | — | Decision, Monitoring | Version component renders it | Server | Do not use as display sequence number |
| `owner` | Responsible person or team | `string` | — | Follow-up, ImplementationPlan, ScheduledReview | Owner label rendered | Content | Do not require for read-only contexts |
| `isLoading` | Component is loading its content | `boolean` | `false` | All | `aria-busy="true"` | None | Do not show for <300ms |
| `error` | Error condition with message | `Error \| null` | `null` | All | ErrorMessage rendered; announced | None | Do not embed error-handling logic in presentational components |
| `dismissible` | Whether the user can dismiss this component | `boolean` | Varies | AtlasSuggestion, AtlasInsight, Toast, Banner, InlineNotice | Dismiss button shown | Session | Do not make critical blocking components dismissible |
| `dismissed` | Whether the user has dismissed this component | `boolean` | `false` | Same | Component hidden | Session | Do not permanently suppress without restore path |
| `required` | Whether a field or item is required | `boolean` | `false` | ValidationMessage, form fields | `aria-required="true"` | None | Do not mark non-required fields as required |
| `metadata` | Metadata block configuration | `MetadataConfig` object | — | Most | MetadataBlock renders it | None | Do not embed raw metadata in component anatomy |

**Properties that must not be globally shared:** `type` (overloaded — use `variant`, `severity`, `lifecycleState`, or domain-specific enums); `mode` (ambiguous); `status` (must be typed per domain enum); `data` (never pass raw domain objects to presentational components).

---

# 9. Canonical State Model

*(Cross-cutting; identical to UX-013E's own Section 13 in full.)*

### Interaction States (transient; component-local; not persisted)

| State | Semantic Meaning | Eligible Components | Visual Obligation | Accessibility |
|---|---|---|---|---|
| `default` | No interaction in progress | All | Resting visual treatment | No announcement |
| `hover` | Pointer over the component | Interactive components | Subtle background/border change | No announcement |
| `focused` | Keyboard focus | All interactive | `:focus-visible` ring | No announcement (implicit) |
| `pressed` | Active press/click | Interactive | Brief pressed treatment | No announcement |
| `selected` | Item is selected | List items, filters | Selected background/border | `aria-selected="true"` |
| `expanded` | Disclosure region is open | SectionContainer, Breadcrumb, MetadataBlock, ContextPanel | Body visible | `aria-expanded="true"` |
| `collapsed` | Disclosure region is closed | Same | Body hidden | `aria-expanded="false"` |

### Lifecycle States (semantic; domain or application-layer; may be persisted)

| State | Semantic Meaning | Eligible Components | Permitted Transitions |
|---|---|---|---|
| `draft` | Content exists but not formally committed | Reasoning, Decision, Review, MonitoringCondition | → proposed, final, recorded |
| `proposed` | Candidate for formalization | DecisionProposal, AtlasSuggestion | → final, rejected, dismissed |
| `final` | Formally designated as ready | DecisionCard | → recorded |
| `recorded` | Permanently committed to the historical record | RecordedDecision, ReviewSummary | → amended, superseded |
| `active` | Currently in operation | MonitoringCondition | → paused, satisfied, breached, ended |
| `paused` | Temporarily suspended | MonitoringCondition | → active, ended |
| `scheduled` | Planned for a future time | ScheduledReview, MonitoringCondition | → active, cancelled |
| `triggered` | Condition produced an event requiring attention | MonitoringCondition, MonitoringTrigger | → acknowledged, resolved |
| `pending` | Awaiting action | ReviewTrigger, FollowUp | → acknowledged, started, resolved, dismissed |
| `inProgress` | Actively being worked on | ImplementationStatus, ScheduledReview | → completed, blocked, cancelled |
| `completed` | Successfully reached end state | ScheduledReview, ImplementationStatus, FollowUp | terminal |
| `satisfied` | Monitoring condition met as expected | MonitoringCondition | → ended |
| `breached` | Monitoring condition violated | MonitoringCondition | → triggered |
| `resolved` | Issue or trigger addressed | MonitoringTrigger, ReviewTrigger, InvalidationCondition | terminal |
| `amended` | Recorded decision formally modified | DecisionCard | may coexist with recorded |
| `superseded` | Item formally replaced | DecisionCard, MonitoringCondition | terminal for original |
| `historical` | From a prior immutable session | All supporting components | terminal |

### Availability States, Validation States, AI Content States

Availability: `loading`, `saving`, `saved`, `updated`, `unavailable`, `offline`, `error`.
Validation: `valid`, `informational`, `recommendedCorrection`, `blocking`, `historicalIntegrityViolation`.
AI Content: `generated`, `presented`, `viewed`, `partiallyAccepted`, `accepted`, `rejected`, `dismissed`, `restored`, `outdated`, `superseded` (full semantics per state carried in the interim note, since this class exists for AI Collaboration content — the class itself is defined once, here, for cross-cutting consistency).

### State Coexistence Rules

**May coexist:** `historical` + `superseded`; `recorded` + `amended`; monitoring `active` + review `pending`; `loading` + existing content visible; `expanded` + `updated`; `dismissed` + restorable.

**Mutually exclusive:** `historical` and any editing-enabled state; `loading` and `error`; `satisfied` and `breached` (same condition); `recorded` and `draft` (same decision); `accepted` and `rejected` (same suggestion).

---

# 10. State Composition Rules, Variant Model, and Composition Model

*(Cross-cutting; identical to UX-013E's own Sections 14–16 in full.)*

## Valid State Combinations

`historical` + read-only (implied); `loading` + existing content (show overlay, do not blank); `error` + retry available; AI-generated + user-edited (`isAtlasGenerated={true}` + `isUserModified={true}`); `recorded` + `superseded`; monitoring active + review pending; `offline` + sync pending; `dismissed` + restorable; `unavailable` + `historical` (show historical version if available).

## Invalid Combinations

`historical` + editing; `loading` + `error`; `satisfied` + `breached` (same condition); `draft` + `recorded`; `accepted` + `rejected`.

## Precedence

1. `historical` (highest) 2. `error` 3. `loading` 4. `unavailable` 5. `offline`.

## Canonical Variant Dimensions

| Dimension | Meaning | Eligible Components | Implementation |
|---|---|---|---|
| `display` | Compact vs. detailed | MetadataBlock, SourceReference, RelationshipReference, Toast | `'compact' \| 'expanded' \| 'inline'` |
| `severity` | Importance classification | ChallengeItem, ValidationMessage, AtlasWarning, InlineNotice, Banner | `'informational' \| 'material' \| 'blocking'` |
| `orientation` | Horizontal vs. vertical | Divider, LayoutContainer (Row) | `'horizontal' \| 'vertical'` |
| `size` | Relative scale | StatusBadge, Dialog, ProgressIndicator | `'small' \| 'medium' \| 'large'` |
| `subtype` | Semantic subtype within a category | EmptyState, AtlasSuggestion, AtlasInsight, AtlasQuestion, AIGeneratedSummary | specific per component |
| `lifecycleState` | Decision lifecycle position | DecisionCard | typed enum |
| `isEditable` | Editing permitted | Conclusion, Reasoning components | boolean |
| `isHistorical` | Historical vs. current | All supporting components | boolean |
| `isAtlasGenerated` | AI vs. user authored | Reasoning, Decision, AI | boolean |

**Not variants:** Loading (state), Error (state), Expanded/Collapsed (interaction state), Historical (state + property), Responsive (behavior, not user-selectable).

## Composition Model — Parent-Child, Slot, and Ownership Rules

**WorkspaceFrame** may contain: WorkspaceHeader, NavigationBar, WorkspaceToolbar, ScrollContainer, WorkspaceFooter. May not contain: Dialog.
**SectionContainer** may contain: SectionHeader, any Reasoning component, any Decision component (interim note), MetadataBlock, EmptyState, ProgressIndicator, ContextPanel, ReasoningBlock. May not contain: WorkspaceFrame, WorkspaceHeader, WorkspaceFooter, Dialog.
**DecisionCard** composition rules are the interim note's own.
**LayoutContainer** may contain any component (layout wrapper only).
**DialogContainer** may contain one Dialog instance. May not contain WorkspaceFrame or another DialogContainer.
**Maximum recommended nesting depth:** 4 levels.

**Slot Model:** WorkspaceHeader (`statusArea`); SectionContainer (`header`, `body`); Dialog (`title`, `body`, `primaryAction`, `secondaryAction`); MetadataBlock (`author`, `timestamp`, `version`, `source`, `relationship`, `confidence`); EmptyState/Toast/InlineNotice/Banner (`action`). *(DecisionCard's own slot set is the interim note's.)*

**Ownership rules:** Spacing owned by the parent; surface ownership by the outermost surface at each nesting level; border ownership by Section Containers; focus ownership by DialogContainer when a Dialog is open, otherwise by the Workspace; historical ownership propagates top-down from Workspace/Section level via `isHistorical`.

---

# 11. Component Dependency Graph

**This is the single, complete, canonical dependency graph for the entire Atlas Component Library** — Foundation, Reasoning, and infrastructure tiers operative in this document, and Decision, Monitoring, Historical, and AI Collaboration tiers operative in the interim note. It is retained whole, here, because the graph's own "no circular dependencies" claim is a property of the complete chain, not of either tier alone; fragmenting it into two partial graphs would either duplicate the shared portion or make neither document's graph provably complete. The interim note references this graph and states only its own tier's position within it; it does not reproduce a competing or partial graph.

## High-Level Dependency Graph

```
Design Tokens
    ↓
Primitives (IconPrimitive, TextPrimitive, DividerPrimitive)
    ↓
Foundation (WorkspaceFrame, SectionContainer, StatusBadge, ProgressIndicator, EmptyState, DialogContainer…)
    ↓
Metadata & Provenance (MetadataBlock, Author, Timestamp, SourceReference…)
    ↓
Status & Feedback (ValidationMessage, ErrorMessage, WarningMessage, Toast, InlineNotice, Banner…)
    ↓
AI Collaboration (AtlasSuggestion, AtlasInsight, AtlasWarning, AIAuthorshipIndicator…) — interim note's own tier
    ↓
Reasoning (Conclusion, SupportingFactors, ChallengesContainer, AssumptionsContainer…)
    ↓
Decision (DecisionCard, RecordedDecision, DecisionHistory…) — interim note's own tier
    ↓
Monitoring (MonitoringCondition, ReviewSummary, ImplementationPlan…) — interim note's own tier
    ↓
Historical (TimelineEntry, DecisionTimeline, OutcomeTracking…) — interim note's own tier
    ↓
Patterns and Templates
```

## Detailed Dependency Table (Foundation/Reasoning/infrastructure rows)

| Component | Hard Dependencies | Optional Dependencies | Notes |
|---|---|---|---|
| WorkspaceFrame | Tokens | StatusBadge, ProgressIndicator | Structural root |
| SectionContainer | WorkspaceFrame, Tokens | StatusBadge, EmptyState, ProgressIndicator | Foundation |
| StatusBadge | Tokens, IconPrimitive | — | Leaf component |
| ProgressIndicator | Tokens | IconPrimitive | Leaf component |
| MetadataBlock | Tokens, Author, Timestamp | SourceReference, Version, RelationshipReference, ConfidencePresentation | Foundation for all provenance |
| Conclusion | SectionContainer, MetadataBlock | AIAuthorshipIndicator (interim), StatusBadge | Reasoning |
| ChallengeItem | Tokens, StatusBadge, MetadataBlock | RelationshipReference | Reasoning |
| AssumptionItem | Tokens, StatusBadge | MetadataBlock, RelationshipReference (to MonitoringCondition, interim note) | **Cross-tier dependency, explicitly disclosed:** this Reasoning component references a Monitoring-tier component by typed ID only; it does not import or redefine MonitoringCondition |

*(AtlasSuggestion, DecisionCard, MonitoringCondition, TimelineEntry rows are the interim note's own; reproduced there with the identical cross-tier disclosure convention used above.)*

## Critical Shared Primitives

StatusBadge, MetadataBlock, Timestamp, Author, SourceReference are used across every component category, including the interim note's own tiers. Changes to these components have the highest blast radius; breaking changes require a major version bump and coordinated migration support across all consuming categories, canonical and interim alike.

## Explicitly Disclosed Cross-Tier Dependencies

- **AssumptionItem → MonitoringCondition** (via ID reference, not component nesting).
- **AtlasSuggestion → multiple Reasoning components** (as target of suggestions, via typed `targetComponent` ID; interim note's own dependency, disclosed here for graph completeness).
- **DecisionCard → MonitoringCondition, ReviewTrigger, ImplementationStatus** (via ID reference; interim note's own dependency, disclosed here for graph completeness).

## No Circular Dependencies Found

Foundation does not depend on Reasoning, Decision, or Monitoring. Reasoning does not depend on Decision or Monitoring. Decision does not depend on Monitoring (holds ID references only). Monitoring does not depend on Historical (transitions to historical via the application layer). This property holds across the complete graph above, spanning both this document's tiers and the interim note's.

---

# 12. Workspace Coverage Matrix

*(Cross-cutting; retained whole here since it spans every Workspace and every category. The interim note references this table for its own tier's rows rather than reproducing a partial or competing matrix.)*

| Component | Dashboard | Investment Workspace | Portfolio Workspace | Decision Workspace |
|---|---|---|---|---|
| WorkspaceFrame | Required | Required | Required | Required |
| WorkspaceHeader | Required | Required | Required | Required |
| WorkspaceToolbar | Optional | Optional | Optional | Optional |
| WorkspaceFooter | Optional (read-only) | Optional | Optional | Required |
| NavigationBar | Required | Required | Required | Required |
| Breadcrumb | Required | Required | Required | Required |
| SectionContainer | Required | Required | Required | Required |
| StatusBadge | Required | Required | Required | Required |
| MetadataBlock | Optional | Required | Required | Required |
| Conclusion | Not used (shows DecisionSummary) | Required | Required | Required |
| SupportingFactorsContainer | Not used | Required | Optional | Required |
| ChallengesContainer | Not used | Required | Optional | Required |
| AssumptionsContainer | Not used | Required | Optional | Required |
| DecisionCard *(interim note)* | Required (summary form) | Optional | Required | Required |
| MonitoringCondition *(interim note)* | Required (summary) | Optional | Required | Required |
| AtlasSuggestion *(interim note)* | Optional | Required | Optional | Required |
| AtlasWarning *(interim note)* | Optional | Required | Optional | Required |
| DecisionTimeline *(interim note)* | Not used | Optional | Optional | Optional |
| TimelineEntry *(interim note)* | Not used | Optional | Optional | Optional |
| ReviewSummary *(interim note)* | Not used | Not used | Optional | Required |
| ImplementationPlan *(interim note)* | Not used | Not used | Optional | Required |

**Coverage gaps identified (preserved unchanged from UX-013E):** Dashboard has no dedicated Monitoring summary component — it shows MonitoringCondition (interim note) in a condensed form requiring a defined variant, not yet specified. Portfolio Workspace coverage for Review and Implementation components (interim note) is partial — "Optional," reference-only, not full components.

---

# 13. Responsive System Assembly

*(Cross-cutting; identical to UX-013E's own Section 19, applies library-wide.)*

**Desktop:** Full layout, 48px side padding, 1200px max content width, all components in standard form.
**Tablet:** 32px side padding; split layouts stack at narrower widths; companion panels move below associated content; toolbar overflow collapses sooner.
**Mobile:** 16px side padding; side-by-side layouts stack vertically; Comparison columns stack sequentially; Decision Card (interim note) full-width with collapsed metadata; Timeline (interim note) full-width entries; Dialogs become bottom sheets; Toasts appear at bottom.

**What may condense:** MetadataBlock, SourceGroup, Breadcrumb, WorkspaceToolbar, SectionHeader actions.
**What must remain visible:** Conclusion statement, Decision Card statement (interim note), all StatusBadge text labels, ValidationMessage/ErrorMessage content, AuthorshipIndicator labels, historical date labels, Recovery actions.
**What must never be hidden:** Authorship attribution, historical date labels, blocking validation messages, error recovery actions, the current user's undo window.

---

# 14. Accessibility System Assembly

*(Cross-cutting; identical to UX-013E's own Section 20, applies library-wide.)*

**Keyboard:** All interactive elements reachable by Tab in visual reading order; arrow-key navigation within lists; Escape closes Dialogs/dismissible overlays; Space/Enter activates controls; focus never trapped outside DialogContainer when no Dialog is open.
**Focus Visibility:** `:focus-visible` only; `outline: [width.focus.ring] solid [color.focus.ring]; outline-offset: 2px`; no `box-shadow` for focus in High Contrast Mode.
**Focus Order:** Matches visual reading order; Dialogs move focus to first interactive element on open and return it on close.
**Screen Reader Naming:** Every interactive element has an accessible name; icon-only buttons have `aria-label`; decorative elements have `aria-hidden="true"`.
**Landmark Regions:** One `<main>`; `<header>`/`<footer>`/`<nav>` for their Foundation components; `role="dialog"` for Dialog; `<aside>` for ContextPanel.
**Heading Hierarchy:** One `<h1>` per Workspace; SectionHeader headings `<h2>`; factor names `<h3>`/`<h4>` as appropriate; no skipped levels.
**Dynamic Announcements:** `aria-live="polite"` for updated content, saved state, suggestion appearance/acceptance/dismissal (interim note's own components), monitoring status changes (interim note); `aria-live="assertive"` for blocking errors, triggered monitoring conditions, record/finalize transitions (interim note), offline state change.
**Non-color Status, Touch Targets (44×44px min), Zoom (200%/400% reflow), High Contrast, Reduced Motion:** all as specified once, here, for the whole library.

---

# 15. Token Coverage Audit

*(Cross-cutting; identical to UX-013E's own Section 21. The missing token backlog spans both this document's tiers and the interim note's — retained whole here since the token dictionary itself is a single, canonical artifact.)*

Typography, Spacing, and Surface tokens are fully covered (UX-013A/UX-012A). Border tokens are covered, with new tokens required for challenge severity, factor status, comparison columns (Reasoning-tier). New token groups required, spanning both tiers: AI authorship (`authorship.atlas.*`, `.user.*`, `.mixed.*` — interim-note-relevant); Decision states (`decision.state.*` — interim-note-relevant); Monitoring states (`monitoring.state.*` — interim-note-relevant); AI content states (`ai.state.*` — interim-note-relevant); Confidence/Uncertainty (`confidence.level.*` — this document's Reasoning tier); Assumption status tokens (holding, under-review, weakening, broken — this document); Opportunity Cost tokens (this document); Scenario probability tokens (this document).

**No existing tokens are deprecated.** The UX-012 token vocabulary is extended, not replaced.

---

# 16. Figma Library Architecture (Foundation, Reasoning, and Infrastructure Pages)

The complete Figma file structure is a single library file; this document specifies the pages operative here. The interim note specifies its own pages (Decision, Monitoring, Historical, AI Collaboration) within the same file, cross-referencing this document's `_Tokens` page and shared conventions rather than restating them.

```
Atlas Component Library [Figma File]
├── _Cover [page — file metadata, version, owners] — this document
├── _Changelog [page — version history] — this document
├── _Tokens [page — variable collections and token reference] — this document
├── Foundation [page] — this document
│   ├── Workspace Shell, Navigation, Layout, Surfaces, Containers, Structural, Indicators
├── Metadata & Provenance [page] — this document
│   ├── MetadataBlock, Author, Timestamp, Version, SourceReference, SourceGroup, RelationshipReference, ConfidencePresentation
├── Reasoning [page] — this document
│   ├── Conclusion, SupportingFactors, Challenges, Assumptions, Evidence, Opportunity, OpportunityCost, Comparison, ScenarioAnalysis, Proposed Decision Candidate Content, ReasoningBlock, ContextPanel
├── Decision [page] — interim note
├── Monitoring [page] — interim note
├── Historical [page] — interim note
├── AI Collaboration [page] — interim note
├── Feedback [page] — this document
│   ├── ValidationMessage, InformationalMessage, WarningMessage, ErrorMessage, SuccessConfirmation
├── Loading & Availability [page] — this document
│   ├── ProgressIndicator (all variants), EmptyState (all subtypes), PermissionState, UnavailableDataState, OfflineConnectionState
├── Overlay & Dialog [page] — this document
│   ├── DialogContainer, Dialog, Toast, InlineNotice, Banner
├── Notification [page] — this document
│   └── SystemNotification
├── Patterns [page] — shared; entries cross-reference their own owning document
│   ├── WorkspaceShell, ReasoningHierarchy (this document); DecisionTimeline, SuggestionComparison (interim note); ConfirmationFlow (this document)
└── Workspace Templates [page] — shared; templates themselves are Workspace-level assemblies drawing on both documents
    ├── DashboardTemplate, InvestmentWorkspaceTemplate, PortfolioWorkspaceTemplate, DecisionWorkspaceTemplate
```

**Component Set Rules:** one component set per canonical component; variants as component set properties; non-selectable states as boolean properties; historical state always `Historical: True/False`; maximum 48 variants per set, decompose if exceeded.

**Naming Conventions:** component sets PascalCase; properties Title Case (enum) or `Has/Is/Show [Thing]` (boolean); variant values Title Case; nested instances PascalCase matching the component name.

---

# 17. Figma Component Property Standard and Documentation Standard

*(Cross-cutting; identical to UX-013E's own Sections 23–24.)*

**Boolean properties:** `Has [Element]`, `Is [State]`, `Show [Element]`.
**Enum properties:** `Variant`, `Severity`, `Lifecycle State`, `Authorship`, `Display`.
**Text properties:** `Title`, `Label`, `Statement`, `Description`, `Supporting Text`.
**Instance swap properties:** `Icon`, `Action`.
**Protected properties** (must not be overridden): token assignments, focus ring presentation, `Is Historical` visual treatment, AI authorship indicator appearance.

**Every published Figma component page must contain** (17 items): component name and status label; purpose; when used/when not used; anatomy diagram; properties table; variants showcase; states showcase; composition examples; responsive examples; accessibility notes; content rules; token roles; do/don't examples; engineering mapping; owner and version; deprecation notice (if applicable); migration guidance (if superseding a prior component).

**Definition of Done (Figma):** component set published; all variants/properties documented; all states tested in context; documentation page complete; accessibility annotations added; Design System and Accessibility owner review; engineering name confirmed; token roles confirmed.

---

# 18. Engineering Component Architecture

**This is the single, complete, canonical engineering layer architecture for the entire library** — reproduced whole here for the same reason as the Dependency Graph (Section 11): the layer stack is one coherent, ordered structure whose correctness depends on the full chain. The interim note references this architecture and names only the layers/packages operative to its own tier.

```
Layer 0 — Design Tokens (@atlas/tokens)
Layer 1 — Primitives (@atlas/primitives)
Layer 2 — Foundation Components (@atlas/foundation) — this document
Layer 3 — Metadata & Provenance Components (@atlas/metadata) — this document
Layer 4 — Status & Feedback Components (@atlas/feedback) — this document
Layer 5 — Loading & Availability Components (@atlas/feedback, sub-modules) — this document
Layer 6 — Overlay & Dialog Components (@atlas/overlay) — this document
Layer 7 — AI Collaboration Components (@atlas/ai) — interim note
Layer 8 — Reasoning Components (@atlas/reasoning) — this document
Layer 9 — Decision Components (@atlas/decision) — interim note
Layer 10 — Monitoring Components (@atlas/monitoring) — interim note
Layer 11 — Pattern Orchestration (Workspace-specific; not published to the component library)
```

**What Belongs Where:** the component library (Layers 0–10) holds all reusable presentational components, shared behaviors, tokens, accessibility contracts, and typed interfaces — both this document's and the interim note's. Workspace code (Layer 11) holds layout composition, route-level state, pattern orchestration, and Workspace-specific data fetching. Application services (outside the library) hold domain state, persistence logic, AI request orchestration, and permission resolution. Presentational components never infer domain model cardinality, initiate AI requests, run database queries, check permissions, or validate business rules.

---

# 19. Engineering Component API Standard, Data/Presentation Boundary, and Shared Behavior Architecture

*(Cross-cutting; identical to UX-013E's own Sections 26–28 in principle and structure, with representative examples limited to this document's own tiers; the interim note carries its own representative examples for Decision and AI Collaboration components using the identical API principles below.)*

## API Principles

Semantic props only (no `style`, no `className` for visual customization, no raw color values); typed state enums (`lifecycleState: DecisionLifecycleState`, not `status: string`); explicit historical props (`isHistorical` + `historicalDate`); slot-based composition (named slot props, not arbitrary `children`); controlled async state (`isLoading`, `error`, `onRetry` explicit); accessibility as contract (`aria-label`, `id`, `data-testid` standard on all components).

**Representative API example (Foundation — SectionContainer):**
```typescript
interface SectionContainerProps {
  sectionId: string;
  variant?: 'standard' | 'fixed' | 'read-only' | 'historical' | 'empty';
  isExpanded?: boolean;
  onExpandChange?: (isExpanded: boolean) => void;
  isHistorical?: boolean;
  historicalDate?: Date;
  isLoading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  'data-testid'?: string;
  children: React.ReactNode;
}
```

**Representative API example (Reasoning — ChallengeItem):**
```typescript
interface ChallengeItemProps {
  id: string;
  name: string;
  severity: 'informational' | 'material' | 'blocking';
  explanation: string;
  isAcknowledged?: boolean;
  acknowledgementNote?: string;
  contradictsId?: string;
  isAtlasSurfaced?: boolean;
  isEditable?: boolean;
  isHistorical?: boolean;
  historicalDate?: Date;
  onAcknowledge?: (note: string) => void;
  onEdit?: () => void;
  onRemove?: () => void;
  onReclassify?: (severity: ChallengeSeverity) => void;
  'data-testid'?: string;
}
```

## Data and Presentation Boundary

Presentation components may infer: which variant/elements to render from typed/boolean props; which tokens to apply from state/variant; focus management from component state. They must receive explicitly: all domain entity IDs, lifecycle states (typed enums), authorship information, historical flags/dates, loading/error states, available actions (callbacks), metadata. They must never invent: domain cardinality, permission rules, business logic, or AI request initiation.

## Shared Behavior Architecture

| Behavior | Implementation | Used By |
|---|---|---|
| Focus Management | `useFocusManagement` hook | All interactive components |
| Disclosure | `useDisclosure` hook | SectionContainer, MetadataBlock, SourceGroup, ContextPanel, Breadcrumb |
| Dismissal/Restoration | `useDismissible` hook | Toast, InlineNotice, Banner (and AtlasSuggestion/AtlasInsight, interim note) |
| Undo | `useUndoWindow(5000)` hook | RecordDecision (interim note) and any action with undo |
| Autosave Indication | `useAutosaveIndicator` hook | All editable Reasoning components (and Decision, interim note) |
| Loading Threshold | `useLoadingDelay(300)` hook | All components with `isLoading` |
| Retry | `useRetry` hook | ErrorMessage, all `onRetry` components |
| Scroll Restoration | `useScrollRestoration(workspaceId)` hook | WorkspaceFrame, ScrollContainer |
| Sticky Positioning | CSS `position: sticky` | WorkspaceHeader, WorkspaceFooter, SectionHeader |
| Historical Read-only | `useHistoricalReadOnly(isHistorical)` hook | All components with `isHistorical` |
| Relationship Navigation | `useRelationshipNavigation` hook | RelationshipReference, ChallengeItem, AssumptionItem |
| Confirmation | `useConfirmation` hook + DialogContainer | All actions requiring confirmation (including interim-note actions) |

---

# 20. Validation, Feedback, Historical-State, Authorship, and Status Architectures

*(Cross-cutting; identical in structure to UX-013E's own Sections 29–33. Reproduced whole here; the interim note references this section for its own Decision/Monitoring/AI examples rather than restating the shared architecture.)*

## Validation Architecture

Field validation: owned by the component/form container, inline below the field. Section validation: owned by SectionContainer/consuming Workspace, shown in SectionHeader (StatusBadge) and a top-of-body ValidationMessage. Workspace validation: owned by WorkspaceFooter (completion gate). Domain validation: owned by the application service layer.

Severity model: `informational` (none); `recommendedCorrection` (none, dismissible "Consider" framing); `blocking` (hard completion-gate block); `historicalIntegrityViolation` (no edit possible; `aria-live="assertive"`).

## Feedback and Interruption Architecture

The full feedback-selection decision tree from UX-013E is preserved unchanged (system failure → ErrorMessage; validation issue → ValidationMessage; AI analytical concern → AtlasWarning, interim note; system-level concern → WarningMessage; informational → Dialog/Banner/InlineNotice/InformationalMessage by scope; success → Dialog/Toast/SuccessConfirmation; background system event → SystemNotification), together with the full Feedback Component Comparison table (scope, persistence, dismissibility, focus interrupt, action required, accessibility) for every component named above.

## Historical-State Architecture

Components requiring explicit `isHistorical` variants, this document's tier: all Reasoning Components, MetadataBlock, SourceReference, RelationshipReference. *(DecisionCard, MonitoringCondition, ReviewSummary, FollowUp, OutcomeTracking, TimelineEntry, AIGeneratedSummary are the interim note's own — the transition rules below apply identically to both.)*

Components that never appear historically: WorkspaceToolbar, ValidationMessage, Toast, ProgressIndicator, PermissionState, OfflineConnectionState.

Transition rules (unchanged): on `isHistorical` becoming true — editing controls hidden (not disabled); action buttons removed; `historicalDate` shown in headers and ARIA labels; historical text opacity applied; historical lock indicator appears; the component becomes permanently non-interactive for the session.

## Authorship and Provenance Architecture

The full Authorship Categories table (User-authored, Atlas-generated, User-confirmed AI, User-edited AI, System-generated, Mixed, Unknown — with visual requirement, metadata requirement, and historical preservation columns) is preserved unchanged, cross-cutting both tiers.

## Status Architecture

Lifecycle Status (StatusBadge), Interaction State (CSS/ARIA), Availability Status, Validation Status, Persistence Status, AI Content Status (interim note's own full semantics) — all as canonical status classes. A generic `status: string` prop is prohibited everywhere.

---

# 21. Loading, Permission, Notification, Icon, Content, Localization, Performance, Security, Analytics, Testing, and Documentation Architectures

*(Cross-cutting; identical in structure and substance to UX-013E's own Sections 34–45. Reproduced whole here; the interim note references this section.)*

**Loading/Progress/Async:** canonical loading representations table (ProgressIndicator variants, thresholds); AI Working State pattern documented once, here, though its own contextual labeling is AI-specific (interim note references it).

**Permission/Availability/Connection:** canonical state-selection table (PermissionState, UnavailableDataState, OfflineConnectionState, EmptyState, ProgressIndicator, ErrorMessage) with the key rule that AI unavailability must never block user-controlled functionality.

**Notification:** Toast and SystemNotification retained as specified; Notification Center remains Deferred; MonitoringTrigger/ReviewTrigger (interim note) are domain-specific, not generic notifications.

**Icon Architecture:** semantic/action/status/AI/historical icon roles and rules (never sole carrier of meaning, `aria-label` on icon-only buttons, 44×44px minimum touch targets, consistent stroke weight, no per-Workspace variation).

**Content Architecture:** canonical content rules for Conclusions, Supporting Factor/Challenge names, Action labels, Error messages, Empty-state headlines, AI attribution labels, and the full Prohibited Content list (brokerage urgency, celebratory language, vague AI claims, blame-oriented errors, decorative metadata, ambiguous action labels).

**Localization Readiness:** all text via props; ±40% length tolerance; Timestamp component delegates to a localization-aware formatter; RTL readiness via Flexbox/Grid start/end; components at particular localization risk named (Breadcrumb, WorkspaceToolbar, ValidationMessage, ConfidencePresentation).

**Performance Considerations:** virtualization requirements for Decision History and Decision Timeline (interim note's own components, cross-referenced here for the shared performance-budget policy), Source Group lazy-rendering, OutcomeTracking pagination, skeleton layout-shift avoidance, Comparison's 3-column/20-row cap, motion-token performance rules, passive scroll listeners.

**Security and Privacy Considerations:** PermissionState non-disclosure rules; ErrorMessage's prohibition on exposing internals; SourceReference's `rel="noopener noreferrer"` rule; AIGeneratedSummary attribution rule; the Analytics exclusion list (no reasoning/decision content, source excerpts, or investment rationale captured).

**Analytics Boundaries:** the permitted component-level events table, fired via `onAnalyticsEvent` hooks only — the component fires the hook; the application layer decides tracking.

**Component and Pattern Testing Standards:** minimum test requirements by classification (Primitive through Composed Pattern); the full Production Readiness Definition of Done checklist; the full Pattern Testing Standard checklist.

**Documentation Architecture:** the canonical documentation-sources table (component semantic spec, Figma page, engineering API reference, usage site, token reference, pattern library, migration guides, changelog, accessibility notes, content guidelines) — one source of truth per information type, no divergent documentation permitted anywhere in the library.

---

# 22. Ownership, Lifecycle, Change, Versioning, and Deprecation Governance

*(Cross-cutting; identical in structure to UX-013E's own Sections 46–50. Reproduced whole here; the interim note references this section for its own tier's rows.)*

## Ownership Model

| Responsibility | Owner |
|---|---|
| Design System overall | Design System Lead |
| Foundation Components (design/engineering) | Design System Designer / Engineer |
| Reasoning Components (design/engineering) | Product Designer — Investment Workspace / Feature Engineer |
| Decision Components (design/engineering) *(interim note)* | Product Designer — Decision Workspace / Feature Engineer |
| Monitoring Components (design/engineering) *(interim note)* | Product Designer — Decision Workspace / Feature Engineer |
| AI Collaboration Components (design/engineering) *(interim note)* | AI Product Designer / AI Integration Engineer |
| Metadata & Provenance Components | Design System |
| Status & Feedback Components | Design System |
| Accessibility compliance | Accessibility Lead |
| Content guidelines | Content Designer |
| Domain model alignment | Domain Lead / Product |
| Token dictionary | Design System Lead |
| Figma/Engineering package publishing | Design System Designer / Engineer |
| Workspace consumer coordination | Product Designer (per Workspace) + Feature Engineer |

## Component Lifecycle Governance

Stages (Proposed → Under Review → Approved → Ready for Implementation → Implemented → Adopted → Stable → Deprecated → Removed → Deferred), each with entry criteria, required evidence, Figma status, and engineering status — reproduced unchanged from UX-013E's own table, applying identically to both this document's and the interim note's components.

## Change Governance

Change-type table (New component, New variant, New property, State model change, Token change, Accessibility change, Responsive change, Bug fix, Breaking change, Deprecation, Emergency correction) with required rationale, reviewers, versioning impact, and communication — reproduced unchanged, cross-cutting.

## Versioning Strategy

Design Tokens, Figma Library, Engineering Package (per package), and Documentation versioning models — reproduced unchanged, cross-cutting; Figma and engineering versions tracked together but not required to match numerically.

## Deprecation and Migration Strategy

The six-step deprecation process (replacement available and documented → marked deprecated → migration guide published → minimum 2-sprint window → consumers notified → removal with Figma archival, not deletion) and the historical-reference handling rule (deprecated component instances in historical Workspace documents are never migrated) — reproduced unchanged, cross-cutting.

---

# 23. Existing Workspace Migration Audit — Foundation and Reasoning Bullets

*(This audit is inherently per-Workspace and mixes Foundation/Reasoning bullets with Decision/Monitoring bullets in UX-013E's own text; retained whole here, with the interim note referencing this section for its own tier's bullets rather than reproducing a competing per-Workspace audit.)*

## Dashboard

Dashboard currently represents decisions via Decision-Summary-equivalent UI elements (interim note), monitoring status via badge-like components (interim note), and navigation via a custom breadcrumb. Migration actions: replace custom breadcrumb → `Breadcrumb`; replace custom empty states → `EmptyState` (subtypes "no-monitoring-events," "no-historical-records"). *(Decision-summary and monitoring-badge replacement is the interim note's own.)* Risk: Low — primarily visual and structural.

## Investment Workspace

The primary consumer of Reasoning Components. Migration actions: existing reasoning sections → `SectionContainer` + canonical Reasoning Components; existing source displays → `SourceReference`/`SourceGroup`; existing metadata displays → `MetadataBlock`; existing Atlas suggestion areas → `AtlasSuggestion` (interim note). Risk: Medium — reasoning component migration requires careful mapping of existing free-form reasoning content to structured components.

## Portfolio Workspace

Uses aggregated views of Decisions and Monitoring (interim note's own migration bullets: position cards, monitoring summary). This document's own relevant action: Portfolio comparison → `Comparison` (`type="allocation"`). Risk: Medium — Portfolio-specific layouts may require new Layout Container configurations.

## Decision Workspace

The most complex Workspace; this document's own relevant action: all reasoning sections → canonical Reasoning Components. *(Decision Proposal area, decision recording sequence, and monitoring conditions setup are the interim note's own bullets for this same Workspace.)* Risk: High overall — the Decision Workspace has the most Workspace-specific behavior and the most consequence if semantic changes are introduced incorrectly.

**Migration principle (unchanged):** translate existing designs into the canonical library; do not redesign during migration; identify semantic mismatches as open questions rather than silently resolving them.

---

# 24. Migration Plan, Implementation Sequencing, Delivery Model, Risk Register, and Readiness Gates — Foundation and Reasoning Scope

*(The full 7-phase Migration Plan, 9-wave Figma sequence, and 9-wave Engineering sequence are single, ordered, cross-tier sequences in UX-013E's own text — Phases/Waves 1–3 and 6 are this document's operative scope; Phases/Waves 4–5, 7–8 are the interim note's. Both documents state the complete sequence, since the ordering itself is one coherent dependency chain, and each names which of its own phases/waves fall in its own operative scope.)*

## Migration Plan (complete 7-phase sequence; Phases 1–2 and 4 operative here)

**Phase 1 — Token Implementation** (prerequisite for all else): implement all missing token groups (Section 15 above), spanning both tiers.
**Phase 2 — Foundation Component Migration:** replace bespoke Workspace shell elements across all Workspaces. Risk: Low.
**Phase 3 — Metadata & Feedback Migration:** replace bespoke metadata/feedback components. Risk: Low-Medium.
**Phase 4 — Reasoning Component Migration:** migrate Investment/Decision Workspace reasoning sections. Risk: Medium.
*(Phase 5 — Decision & Monitoring Component Migration and Phase 6 — AI Collaboration Migration are the interim note's own operative scope.)*
**Phase 7 — Pattern Implementation & Template Creation:** implement Workspace Templates; document all Composed Patterns. Risk: Low.

## Figma Implementation Sequence (complete 9-wave sequence; Waves 1–4, 6 operative here)

Wave 1 (Tokens/Primitives) → Wave 2 (Foundation/Layout/Navigation) → Wave 3 (Containers/Indicators/Empty States) → Wave 4 (Metadata & Provenance Primitives) → Wave 5 (Feedback/Loading/Availability) → Wave 6 (Reasoning) → *(Wave 7 Decision/Monitoring/Historical and Wave 8 AI Collaboration — interim note)* → Wave 9 (Patterns/Templates/Migration QA, shared).

## Engineering Implementation Sequence (complete 9-wave package sequence; Waves 1–4, 6 operative here)

`@atlas/tokens` → `@atlas/primitives` + `@atlas/foundation` → `@atlas/metadata` → `@atlas/feedback` (incl. Loading/Availability/Overlay/Notification) → *(`@atlas/ai` — interim note)* → `@atlas/reasoning` → *(`@atlas/decision`, `@atlas/monitoring` — interim note)* → Workspace integration (shared, Wave 9).

## Cross-Discipline Delivery Model

The eight delivery checkpoints (Specification, Figma build, Engineering build, Design review, Accessibility review, Content review, Workspace integration, Release) apply identically to every component in both this document and the interim note; no checkpoint may be skipped without Design System Lead approval for emergency hotfixes.

## Implementation Risk Register — Foundation/Reasoning/Infrastructure Rows

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Variant explosion in a component set | Medium | High | Hard cap: 48 variants per set; decompose if exceeded | Design System Lead |
| MetadataBlock token requirement expansion | Medium | Medium | Complete token implementation before Wave 4 | Design System Lead |
| Reasoning content migration — semantic mismatch | High | High | Per-Workspace semantic audit before Phase 4 migration begins | Product Designer per Workspace |
| Figma-engineering drift | Medium | High | Design review checkpoint mandatory; shared property dictionary | Design System Lead |
| AssumptionItem → MonitoringCondition cross-category dependency | Low | Medium | ID-based reference model; enforced in package boundaries | Engineering Lead |
| Documentation drift | High | Medium | Mandatory documentation checkpoint before Stable status | Design System Lead |
| Accessibility regression during migration | Medium | High | Accessibility test suite on every PR; checkpoint before each Wave | Accessibility Lead |

*(AI suggestion targeting precision, historical content migration complexity, and Decision Timeline performance regression rows are the interim note's own.)*

## Readiness Gates — Foundation/Reasoning/Infrastructure-Relevant Rows

| Gate | Required Evidence | Approver | Blocking |
|---|---|---|---|
| Token readiness | All missing token groups implemented; dictionary published | Design System Lead | Yes — blocks all component work |
| Component specification readiness | This document and the interim note both approved | Design System Lead, Product Lead | Yes — blocks Figma and engineering |
| Figma readiness (per wave) | All Wave N components published; Definition of Done met | Design System Lead, Accessibility Lead | Yes — blocks next wave |
| Engineering readiness (per wave) | All Wave N packages published; tests passing; Storybook complete | Engineering Lead, Accessibility Lead | Yes — blocks next wave |
| Accessibility readiness (per component) | Manual accessibility review completed | Accessibility Lead | Yes — blocks Stable status |
| Testing readiness (per component) | All required tests passing | Engineering Lead | Yes — blocks production release |

*(Domain readiness [blocking Decision/Monitoring waves], AI integration readiness, Persistence readiness, and Workspace migration readiness for Decision-tier content are the interim note's own.)*

---

# 25. Final Consistency Audit — Foundation, Reasoning, and Infrastructure Scope

✓ Every canonical component in this document's scope has one primary semantic responsibility.
✓ Every component is classified per Section 2.
✓ Every component is named canonically per Section 4.
✓ No unjustified duplicate components remain in this document's scope (Section 5).
✓ Variant and pattern boundaries are clear (Sections 5, 10).
✓ Shared properties and states are canonical (Sections 8–10).
✓ Dependencies are coherent; no circular dependencies found in the complete graph (Section 11).
✓ Workspace coverage for this document's own components is complete, with acknowledged gaps (Section 12).
✓ Responsive and accessibility behavior is complete (Sections 13–14).
✓ Token coverage is complete, with a shared missing-token backlog (Section 15).
✓ Figma and engineering architecture for this document's tiers is coherent (Sections 16–19).
✓ Testing, documentation, ownership, and governance requirements are complete (Sections 21–22).
✓ Migration for this document's phases/waves is feasible, with identified risk areas (Section 24).
✓ This document's content aligns with UX-012 (all canonical terminology preserved).
✓ This document's content preserves the meaning established in UX-013A and UX-013B (confirmed by the reconciliation summary in Section 1 and the naming audit in Section 4).

**This document does not claim the whole Atlas Component Library is production-ready** — that overall claim depends jointly on this document and the interim note, and the interim note's own claims remain explicitly provisional per its three-tier claim classification.

**Remaining open items in this document's own scope, preserved unchanged from UX-013E:** missing Reasoning/infrastructure-relevant token groups (Confidence, Opportunity Cost, Scenario probability, Assumption status — Section 15); Scenario Analysis's relationship to a future Scenario Workspace (Section 1, UX-013B carried-forward question); Atlas Suggestion targeting precision at item level (Section 1, shared with the interim note's own AI-side resolution).

---

# Canonical Atlas Component Taxonomy (Consolidated Reference)

| # | Category | Purpose | Operative Document |
|---|---|---|---|
| 1 | Foundation | Structural Workspace shell | This document |
| 2 | Layout | Spatial organization | This document |
| 3 | Navigation | Location and movement | This document |
| 4 | Reasoning | Structured investment reasoning | This document |
| 5 | Decision | Investment decision lifecycle | Interim note |
| 6 | Monitoring | Post-decision conditions and reviews | Interim note |
| 7 | Historical | Immutable past records | Interim note |
| 8 | AI Collaboration | Atlas AI presentation | Interim note |
| 9 | Metadata & Provenance | Authorship, timestamps, sources | This document |
| 10 | Status & Feedback | System and validation feedback | This document |
| 11 | Loading & Availability | Loading, empty, permission, connection | This document |
| 12 | Overlay & Dialog | Dialogs, Toasts, Banners | This document |
| 13 | Notification | Background system events | This document |
| 14 | Utility | Shared behaviors and services | This document |

# Canonical Component Inventory (Consolidated Reference — This Document's Scope)

**Foundation (16 components), Layout (1 composite), Navigation (2 components), Reasoning (19 canonical items), Metadata & Provenance (8), Status & Feedback (6, including the shared StatusBadge), Loading & Availability (5, including the shared ProgressIndicator/EmptyState), Overlay & Dialog (4), Notification (1).** Full property, state, variant, and dependency specifications for every item above are in Sections 6–11. *(Decision (9), Monitoring (12), and AI Collaboration (7) canonical items are the interim note's own; the full-library total of 87 canonical components is confirmed by summing both documents' own inventories, with StatusBadge, ProgressIndicator, and EmptyState counted once each, per UX-013E's own original accounting.)*

---

# Requirements for UX-014

## UX-014 — Atlas Figma Design System Implementation Specification

UX-014 translates the canonical component library established by this document and the interim note into a complete, buildable Figma implementation specification. UX-014 does not redesign components; it implements the already-canonical decisions of both documents in Figma.

**UX-014 must specify at minimum:** Figma file architecture; library structure; variable collections; typography/effect/grid-and-layout styles; component property standards; component variant standards; nested-component standards; Auto Layout standards; responsive resizing; slot patterns; prototype behavior; accessibility annotations; documentation page standards; usage examples; do-and-don't examples; component maturity labels; experimental/deprecation/migration treatment; publishing and review workflow; versioning; release notes; branching/change workflow; permissions; ownership; QA checklist; Figma-to-engineering mapping; Workspace template construction; implementation waves (matching Section 24 above and the interim note's own Section 53-equivalent); Definition of Done.

**UX-014 must not:** redesign any component specified in this document or the interim note; introduce new component functionality; resolve unresolved product or domain questions through Figma implementation choices; create visual tokens contradicting the Atlas semantic token system.

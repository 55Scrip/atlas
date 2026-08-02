# UX-013C — Atlas Component Specification: Decision Components

**Phase 1 — Canonical Decision Architecture.** Governing references: `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md`; `UX-012B-Atlas-Design-System-Components-Reusable-Patterns.md`; `UX-000-Atlas-UX-Doctrine.md` (RC v1.0); `ADR-002-Critical-UX-Architecture-Resolutions.md`; `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`.

**Status: Canonical (Phase 1 — Decision Components only).** This document specifies, in production-ready detail, only the Decision-tier components already fully supported by committed, canonical documentary evidence — `UX-012` and `UX-012B` directly. It is genuinely, honestly authored on 2026-08-02, citing only documents that exist and are checkable at the time of writing, following the identical process `UX-013A` and `UX-013B` themselves used, per `ADR-001-Missing-Source-Volume-Governance.md`'s own Governance Rule 4 and Option B. It does not reconstruct, does not claim descent from, and is not a replacement for `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own account of an absent `UX-013C` — that account remains its own document's own separate, `[U]` Unconfirmed record. Where this document's own Decision-tier scope overlaps that account, this document supersedes it for every component specified below, exactly as `ADR-001`'s own Future Work section anticipates ("Genuine `UX-013C`... may later be authored... following the same process `UX-013A` and `UX-013B` themselves used"); it does not supersede the interim note's own Monitoring or AI Collaboration content, which remains entirely outside this document's own Phase 1 scope.

**Provenance convention used in this document.** This document uses **[C]** (Canonical — traced directly to `UX-012`, `UX-012B`, `UX-000`, an Accepted UX ADR, or a directly-cited Product Architecture document's own committed text) and **[IR]** (Implementation Refinement — anatomy, property, or token detail newly authored here, required to make a canonical purpose production-ready, and not itself asserting new meaning). This is a different, and stronger, convention than the interim note's own **[IC]**/**[U]**/**[TBA]** scheme, used deliberately: that scheme exists to disclose varying confidence in a *secondhand, unconfirmed* account; this document's own claims are traced directly to committed, canonical sources, per `ADR-001` Governance Rule 7 ("A document is not eligible to be treated as canonical... if adopting it requires accepting an unverifiable or fabricated claim about its own provenance"). No claim in this document is tagged **[U]** — anything that would require such a tag is instead moved to Section 9, Deferred.

---

## 1. Purpose

This document specifies every Atlas Decision-tier component whose architecture is already settled by `UX-012` and `UX-012B`, in the same production-ready detail — anatomy, properties, states, interaction, accessibility, responsive behavior, and token mapping — that `UX-013A` and `UX-013B` already provide for the Foundation and Reasoning tiers. It closes part of the documentary gap `ADR-001` and `ADR-002` C-05 identified, for the Decision tier specifically, through genuine new authorship rather than reconstruction. Figma components can be built directly from these specifications. Engineering can implement without inventing behavior.

This document does not specify Monitoring, AI Collaboration, or domain-specific Metadata components — those remain entirely outside this Phase 1 scope, and this document takes no position on the interim note's own account of them.

## 2. Authority Chain

Atlas Core Architecture Doctrine (Final) → Atlas Product Doctrine and Product Concept Taxonomy, `APP-000`/`APP-001` (Normative Product) → `APS-001` through `APS-005` (Normative Product, the sole authority for each accepted concept's own normative behavior) → `UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0 (governing UX doctrine, per its own `UXD-R-097`) → `ADR-002`, `ADR-003` (Accepted, Normative UX, subordinate to `UX-000`, authoritative within their own stated scope) → `UX-012`/`UX-012B` (Normative UX, the Design System's own semantic authority) → this document (subordinate component-level realization).

This document does not amend `UX-000`. It does not amend `ADR-001` through `ADR-004`. It does not redefine, narrow, or extend any Product Concept, Product Principle, or Core Domain Object. It does not introduce new terminology — every component name, state name, and property concept below is traced to `UX-012` or `UX-012B`'s own committed text.

## 3. Relationship to UX-012

`UX-012` (and `UX-012B`, its own companion component specification) remain the semantic authority for every component this document specifies. This document adds implementation-ready anatomy, properties, states, interaction, accessibility, and token detail; it does not redefine any component's purpose or meaning. Where this document's own detail and `UX-012`/`UX-012B`'s own text could be read to diverge, `UX-012`/`UX-012B` govern — the identical relationship `UX-013B` already states for its own dependence on `UX-012` ("Governing references: UX-012"). This document does not silently absorb or replace `UX-012`; `UX-012` §25 and `UX-012B` §8/§10 remain fully valid, unedited, and authoritative in their own right.

## 4. Relationship to UX-013F

`UX-013F-Foundation-Reasoning-Component-Library-Assembly.md` is this document's peer, canonical for the Foundation and Reasoning tiers and for the cross-cutting infrastructure every tier depends on (Metadata & Provenance, Status & Feedback, Loading & Availability, Overlay & Dialog, Notification, and the shared property/state/composition/dependency/classification models). This document does not restate any of that cross-cutting content; it references it by name — `SectionContainer`, `MetadataBlock`, `StatusBadge`, `ProgressIndicator`, `WorkspaceFooter`, `Dialog`, `Long-Form Editor` — exactly as `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md` already does for its own tiers. This document adopts `UX-013F`'s own ten-type classification model (Section 2 of that document: Primitive, Component, Composite Component, Action, Behavior, State, Variant, Composed Pattern, Semantic Concept, Deferred Item) to classify each component below, without redefining any classification type.

## 5. Decision Architecture Overview

The Decision tier renders the Product Concept Decision (per `APP-000` §5, `APS-001`) across its lifecycle: formation (Proposed Decision), commitment (Final Decision Card, and the Record Decision action governed within it), historical presentation (Historical Decision, Decision Summary, Decision History, Decision Amendment), and formal review (Decision Review). Seven components are canonical and fully specified below, all traced directly to `UX-012` §25 and `UX-012B` §8/§10.

**Decision Review's own addition (Atlas UX Architecture UX-013C Decision Review Canonical Extension task, 2026-08-02).** This component was added following a dedicated architecture reconciliation investigation (Decision Review / Review Summary / Review Outcome Architecture Reconciliation) that determined Decision Review has complete, documentary-supported anatomy in `UX-012` §25 and `UX-012B` §8, while `Review Summary` and `Review Outcome` — two adjacent names referenced only in `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own **[U]** account — remain unsupported and are deferred, per Section 9, below. This addition does not reopen that investigation's own conclusions.

Several further Decision-adjacent constructs referenced elsewhere in the corpus — a unified `DecisionCard` spanning multiple lifecycle states, `Decision Outcome`, `Decision Supersession` as an independent component, and `Decision Rationale Reference` — are not specified in this document. Each traces only to `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own **[U]** Unconfirmed account, and, for `DecisionCard` specifically, carries a documented, unreconciled divergence from this document's own canonical Final Decision Card. Per this task's own governing instruction, they are not authored here; see Section 9, Deferred.

**Proposed Decision Candidate Content** — the Reasoning-tier component (`UX-013B` §10, `ADR-003`-governed) that feeds Proposed Decision — is explicitly out of this document's own scope. It is owned by `UX-013B`, cross-referenced here where relevant, never redefined.

## 6. Canonical Component Inventory

| Component | Classification | Status | Source |
|---|---|---|---|
| Proposed Decision | Component | **[C]** Canonical | `UX-012` §25 |
| Final Decision Card | Composite Component | **[C]** Canonical | `UX-012` §25, `UX-012B` §8 |
| Historical Decision | Component | **[C]** Canonical | `UX-012B` §10 |
| Decision Summary | Component | **[C]** Canonical | `UX-012B` §8 |
| Decision History | Composite Component | **[C]** Canonical | `UX-012B` §8 |
| Decision Amendment | Component | **[C]** Canonical | `UX-012B` §8 |
| Decision Review | Composite Component | **[C]** Canonical | `UX-012` §25, `UX-012B` §8 |

Not specified in this document — see Section 9: `DecisionCard` (unified lifecycle model), `Decision Outcome`, `Decision Supersession` (as an independent component), `Decision Rationale Reference`, `Decision Required` and `Decision Rationale` (Workspace-section-level content, not yet component-level). Out of this document's own scope entirely (owned by `UX-013B`): `Proposed Decision Candidate Content`.

---

## 7. Component Specifications

### 7.1 Proposed Decision

**Purpose [C].** The user's stated intention, written in their own words, before it is formalized in the Final Decision Card. Per `UX-012` §25: *"The user's stated intention, written in their own words before it is formalized in the Final Decision Card."* Canonical Decision Workspace sequence position 3 (`ADR-002` C-03).

**Semantic Meaning [C].** Character: free-form, authored, the user's own language. Not a form. Not a template. Per `UX-000-Atlas-UX-Doctrine.md` UXD-R-111: *"Proposed Decision is a UX presentation/workflow artifact. It is not a Decision. It is not Commitment. It MAY present in-progress Investor Reasoning directed toward a prospective Decision, per APS-002."*

**Product Correspondence [C].** Governed directly by `UX-000` UXD-R-111. **[IR]** — by implementation inference, not itself directly stated by UXD-R-071 (which is scoped explicitly to Current Conclusion): the same genuine-connecting-act reasoning UXD-R-071 item 2 applies to Current Conclusion plausibly extends to Proposed Decision's own content, since both concern the same Investor-Reasoning-connecting-act threshold. Proposed Decision Candidate Content, where it originates the statement, remains governed by `ADR-003`; accepting candidate content into Proposed Decision does not itself constitute Investor Judgment or a Decision (`ADR-003` R-04, R-05).

**Ownership [C].** User-owned; blank until authored. Per `ADR-003` R-04: *"A user may author Proposed Decision without any candidate content ever existing."*

**Composition [IR].** Standalone Component, per `UX-013F`'s own classification model (Section 2) — it does not compose sub-components of its own.

**States [C].** empty, drafting, authored, atlas-suggested, user-modified (`UX-012` §25).

**Properties [IR]** (named here for the first time, following `UX-012D`'s own `category.role.variant` naming convention, Section 4):

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `statement` | string | — | No (required only for the Final Decision Card's own completion gate) | The user's own stated intention |
| `source` | `'user' \| 'atlas-suggested'` | `'user'` | No | Set when content originates from an accepted Proposed Decision Candidate Content |
| `isEditable` | boolean | `true` | No | Always true — Proposed Decision has no read-only variant while its Decision Context remains open |
| `lastModified` | timestamp | — | No | Autosave timestamp |

**Interaction [C].** Its content flows into the Final Decision Card (`UX-012` §25: *"Its content flows into the Final Decision Card"*). Content MAY originate from Proposed Decision Candidate Content (`UX-013B` §10, out of this document's own scope) via that component's own Accept/Modify/Decline actions, per `ADR-003` R-03/Flow B — this document does not redefine that flow, only names the destination field it terminates in. Editing uses Long-Form Editor behavior, per `UX-012` §29 (cross-referenced, not restated, consistent with `UX-013B` §1's own citation pattern for the identical dependency).

**Accessibility [C].** Consistent with Long-Form Editor (`UX-012` §29): `aria-label="Proposed Decision"`, `aria-multiline="true"` while editing.

**Responsive Behaviour [C].** Full-screen editing mode on mobile, per `UX-012` §12/§45's own editing-component convention (Decision Field and Long-Form Editor).

**Token Mapping [IR]** (leaf tokens newly named here, following `UX-012D` §3's own established `Decision` semantic token group — no existing token name for this specific component was found in `UX-012D`, so the following extend that group's own convention):

| Visual Property | Token |
|---|---|
| Statement text (user-authored) | `type.body.user` (existing, `UX-012D` §3) |
| Statement text (atlas-suggested, unedited) | `type.body.atlas` (existing, `UX-012D` §3) |
| Field container | `space.decision.card.internal` (existing, `UX-012D` §3, reused for consistency with the field this content later occupies) |

**Engineering Notes [IR].** Implement as a rich text field consistent with Long-Form Editor's own eight-state model (`UX-013B` §1's own citation pattern for Current Conclusion applies identically here, since both editable fields share the same underlying editing primitive per `UX-012` §29).

**Anti-Patterns [C].** Do not require Proposed Decision to be populated before candidate content exists — `ADR-003` R-04 requires it to remain authorable independently. Do not treat acceptance of candidate content as itself constituting a Decision — `ADR-003` R-05.

---

### 7.2 Final Decision Card

**Purpose [C].** The structured, permanent record of a Decision with full reasoning provenance. Per `UX-012` §25: *"The structured, permanent record of a Decision with full reasoning provenance."*

**Semantic Meaning [C].** Six required fields (`UX-012` §25, `UX-012B` §8): Decision (the core commitment in the user's own words), Primary Reason, Confidence (a qualitative statement, never a gauge or percentage), Invalidation Condition, Implementation Intent, Review Condition.

**Product Correspondence [C].** Confidence remains subordinate presentation terminology, not a Product Concept, per `UX-000` UXD-R-065, and SHALL NOT define a numeric or categorical scale, per UXD-R-064. The Decision field itself corresponds to the Product Concept Decision, owned exclusively by the Investor, per `APP-000` PP-005 and `UX-000` UXD-R-074: *"A Decision SHALL be attributable to the Investor as its owner in every presentation."* Recording requires an identifiable Investor act, per `UX-000` UXD-R-075; per UXD-R-053, it SHALL NOT be triggerable by Atlas under any circumstance.

**Ownership [C].** User-owned; locks on recording (`UX-012` §25).

**Composition [C].** Composite Component (per `UX-013F`'s own classification model — it owns a defined composition of six named fields, unlike a Composed Pattern, which owns no state of its own). Per `UX-012B` §8: *"Signature status: The Final Decision Card is one of the six signature Atlas UI moments."*

**States [C].** Two: **Draft/Live-Updating** ("fields are editable; content flows from the Proposed Decision and reasoning sections") and **Completed/Recorded** ("all fields are locked and converted to Historical content. The card is permanently labeled with the recording timestamp and is immutable") — `UX-012` §25.

**Properties [IR]** (fields named here for the first time as typed properties, following the six fields `UX-012`/`UX-012B` already name in prose):

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `decisionId` | string | — | Yes (on Recorded) | Assigned on first recording |
| `statement` | string | — | Yes, at completion gate | The core commitment |
| `primaryReason` | string | — | Yes, at completion gate | The single most important reason |
| `confidence` | string (qualitative label only) | — | No | Never numeric, per `UX-000` UXD-R-063–065 |
| `invalidationCondition` | string | — | Conditionally required, per `ADR-002` C-04's own completion matrix | |
| `implementationIntent` | string | — | Conditionally required, per `ADR-002` C-04 | |
| `reviewCondition` | string | — | Conditionally required (or explicit override), per `ADR-002` C-04 | |
| `lifecycleState` | `'draft' \| 'recorded'` | `'draft'` | Yes | Exactly the two states `UX-012` §25 names — no third value |
| `recordedAt` | timestamp \| null | `null` | No | Set only on transition to `recorded` |

**Interaction [C].** Draft state: non-interactive live preview (`UX-012B` §8: *"In draft state — non-interactive (the card updates as a live preview while the user edits above)"*). Recorded state: read-only within the Decision Workspace; may link to a full Decision Record view. The Record Decision action (`ADR-002` C-03 canonical position 13) is user-driven only; per `ADR-002` C-06, it uses `aria-disabled="true"`, never the native `disabled` attribute, while any `ADR-002` C-04 required-field condition is unmet, and remains permanently focusable and in the tab order.

**Accessibility [C].** Per `ADR-002` C-06: blocked activation moves focus to the first unmet required field and announces the current reason recording is unavailable; state changes (unavailable → available) are announced; keyboard, pointer, mobile, and touch behavior are equivalent.

**Responsive Behaviour [C].** Full six-field layout on desktop and tablet; fields stack vertically on mobile, full-screen editing per field (`UX-012` §73).

**Token Mapping [C]**, using `UX-012D` §3's own already-named `Decision` semantic token group directly:

| Visual Property | Token |
|---|---|
| Card container (elevated) | `surface.decision.card` |
| Decision statement text | `type.decision.statement` |
| Internal card padding | `space.decision.card.internal` |

**Engineering Notes [C].** Per `UX-012B` §8: recorded state "acquires its permanent visual authority" through "the completeness of its settled form," not a different surface treatment from draft (`UX-012D` §3's own Semantic Token Model applies the identical principle: *"Completed: tokens for the post-recording state... no visual change from the draft state — the authority comes from the populated content."*).

**Anti-Patterns [C].** Do not present Confidence as a gauge, percentage, or numeric score (`UX-012` §25, `UX-000` UXD-R-063–065). Do not permit the native `disabled` attribute on the Record Decision control (`ADR-002` C-06). Do not permit any interaction path by which Atlas triggers recording (`UX-000` UXD-R-053).

---

### 7.3 Historical Decision

**Purpose [C].** The embedded representation of a prior decision in historical context. Per `UX-012B` §10: *"Extends Historical Record and Decision Summary. The embedded representation of a prior decision in historical context."*

**Semantic Meaning [C].** Presents a finalized, immutable Decision for cross-context, cross-Workspace inspection — distinct from the in-Workspace, just-recorded state of Final Decision Card. Corresponds to `UX-012`'s own Canonical Glossary term "Recorded Decision": *"A Decision that has been formally submitted and converted to immutable historical content. Not a saved draft or completed form."*

**Documentary note [IR].** `UX-012` itself also names a "Historical Decision" component, at §27: *"A Historical Record of a Recorded Decision in full — all six Final Decision Card fields, recorded timestamp, and full reasoning provenance."* This is a broader required-content claim than `UX-012B` §10's own *"All Decision Summary fields. The recording date. The decision's current status"* — fewer, more condensed fields than all six Final Decision Card fields in full. This document follows `UX-012B` §10 as its primary source for this component, consistent with its own practice for every other component specified here (Decision Summary, Decision History, and Decision Amendment are likewise drawn from `UX-012B` §8, the component-level specification, not `UX-012`'s own compact §20–29 summaries). The discrepancy between `UX-012` §27's own broader claim and `UX-012B` §10's own narrower one is disclosed here, not resolved; reconciling it is a future `UX-012`-family correction, outside this document's own authority.

**Product Correspondence [C].** Historical immutability is governed at the Product layer by `APS-002` IR-R-027/IR-R-059 (Superseded Content preservation) and restated at the UX layer by `UX-000` UXP-007 (*"Historical Meaning Is Never Silently Rewritten... a later correction is additive, never a silent rewrite"*). This component asserts no independent Product meaning beyond presenting that already-governed immutability.

**Ownership [C].** None asserted independently — presents content the Investor already owns as the recorded Decision's own author.

**Composition [C].** Component, extending Historical Record and Decision Summary (`UX-012B` §10) — a composition of an already-specified base (Historical Record) plus the Decision Summary field set.

**States [C].** All Decision Summary fields, per `UX-012B` §10: *"Required content: All Decision Summary fields. The recording date. The decision's current status (Superseded, Closed, Active — though in Historical context, Active indicates this is the most recent record)."*

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `decisionId` | string | — | Yes | References the recorded Final Decision Card |
| `recordedAt` | timestamp | — | Yes | |
| `status` | `'Active' \| 'Superseded' \| 'Closed'` | — | Yes | Per `UX-012B` §10 |
| `isHistorical` | boolean | `true` | Yes | Always true for this component |

**Interaction [C].** *"Expand to show the full prior decision. 'Compare with current decision →' when a current active decision exists"* (`UX-012B` §10). All editing controls disabled; historical locking is absolute, per `UX-012B` §51: *"No override is possible."*

**Accessibility [C].** Per `UX-012A` §15's own accessible-authorship pattern, historical status is identifiable through both visual means and ARIA labeling — consistent with `UX-013F`'s own cross-cutting `isHistorical` transition rules.

**Responsive Behaviour [C].** Overlay presentation on desktop and tablet, full-screen on mobile, per `UX-012` §73's own Historical Record responsive rule.

**Token Mapping [C]**, using `UX-012D` §3's own already-named `Historical Content` semantic token group:

| Visual Property | Token |
|---|---|
| Historical text color | `color.text.historical` |
| Historical surface | `surface.historical` |
| Timestamp | `type.metadata.timestamp` |

**Engineering Notes [IR].** Implement historical locking at the system level, not merely the interaction level — no edit affordance may appear on hover, and no field may activate on click, consistent with `UX-012B` §51's own "absolute" framing.

**Anti-Patterns [C].** Do not permit any edit path for Historical Decision content, under any circumstance (`UX-012B` §51). Do not present a Historical Decision as if it were current.

---

### 7.4 Decision Summary

**Purpose [C].** A portable, condensed representation of a recorded decision. Per `UX-012B` §8: *"A portable, condensed representation of a recorded decision — suitable for embedding in Dashboard briefings, Investment Workspace prior decisions sections, and Portfolio Workspace context panels."*

**Semantic Meaning [C].** Condensed, read-only. Not the full record — a pointer to it with enough content to orient the reader before they navigate to the full Historical Record.

**Product Correspondence [C].** None asserted independently; presents already-governed Decision content in condensed form.

**Ownership [C].** None asserted independently.

**Composition [C].** Component (not composite — it does not own sub-components with independent state, per `UX-013F`'s own classification test).

**States [C].** Active (the decision is the current governing commitment), Due for Review (the review condition has been triggered), Historical (the decision has been superseded or closed out) — `UX-012B` §8.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `decisionId` | string | — | Yes | |
| `statement` | string | — | Yes | Truncated per `UX-012B` §8 |
| `subjectName` | string | — | Yes | |
| `recordedAt` | timestamp | — | Yes | |
| `implementationState` | string | — | Yes | |
| `primaryReason` | string | — | No | Secondary, truncated if necessary |
| `reviewCondition` | string | — | No | Metadata scale |
| `confidence` | string | — | No | Metadata scale; qualitative only |

**Interaction [C].** *"Tapping/clicking the Decision Summary opens the full Decision Record view (read-only). In active state, an 'Open Decision →' link is visible"* (`UX-012B` §8).

**Accessibility [C].** Read-only link semantics; `<a>` with descriptive `aria-label` naming the decision subject and status.

**Responsive Behaviour [IR].** Consistent with the general condensed-component responsive rule already stated for Decision History (`UX-012B` §8's own Reuse rules place both in identical contexts — Dashboard, Investment Workspace, Portfolio Workspace).

**Token Mapping [IR]:**

| Visual Property | Token |
|---|---|
| Decision statement (condensed) | `type.decision.statement` (existing, `UX-012D` §3, reused at reduced scale) |
| Status label | `type.metadata.timestamp` category (existing), status-specific variant |

**Engineering Notes [C].** *"One of the most widely reused decision components"* (`UX-012B` §8) — Dashboard, Investment Workspace, Portfolio Workspace, Decision Workspace, and Historical timeline all reuse it.

**Anti-Patterns [C].** Do not expand Decision Summary into a full editable record inline — it is read-only by definition; navigation to the full Historical Record is the only path to detail.

---

### 7.5 Decision History

**Purpose [C].** A chronological list of Recorded Decisions related to the current Workspace subject. Per `UX-012B` §8: *"A chronological list of Recorded Decisions related to the current Workspace subject."*

**Semantic Meaning [C].** A subject-scoped catalog — decisions concerning one investment or Workspace subject, not a system-wide catalog. Per this session's own completed Decision History Terminology Reconciliation Investigation (Model A — same construct as the interim note's own `DecisionHistory`, at a different documentary vintage; re-derived here directly from `UX-012B`'s own text, not cited as authority): the "filter" capacity attributed elsewhere to a broader, system-wide catalog is a legitimate configuration of this same component, not a competing construct.

**Product Correspondence [C].** None asserted independently.

**Ownership [C].** None asserted independently.

**Composition [C].** Composite Component, per `UX-013F`'s own classification model — it owns a composition of Decision Summary entries.

**States [IR].** `UX-012B` §8's own Decision History definition does not itself specify a states list. Applied here by analogy to `UX-012` §27's own general Historical Record state pattern: *"States: default, selected, expanded, compared."*

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `subjectId` | string | — | Yes | The Workspace subject this catalog is scoped to |
| `decisions` | array of Decision Summary references | `[]` | Yes | |
| `filter` | object \| null | `null` | No | Consistent with `UX-012B` §8's own reading-order/status filtering behavior |
| `sort` | `'recent-first'` | `'recent-first'` | No | Per `UX-012B` §8: *"Reading order: Most recent first"* |

**Interaction [C].** *"Each entry expands to show the Decision Summary component; the expanded view may contain a 'Compare with current →' link"* (`UX-012B` §8).

**Accessibility [C].** List semantics (`<ul>`/`<li>` or ARIA `list`/`listitem`); each entry individually reachable by Tab, per `UX-012B` §19's own general keyboard-behavior requirement for section-level components.

**Responsive Behaviour [IR].** Consistent with `UX-012` §73's own general list/catalog responsive rule (full-width entries on mobile, no side-by-side layout).

**Token Mapping [IR]:**

| Visual Property | Token |
|---|---|
| Entry row | `space.row` category (general, `UX-012D` §3) |
| Entry text | `type.decision.statement` (existing, `UX-012D` §3, condensed variant) |

**Engineering Notes [C].** Per `UX-012B` §8: *"Reuse rules: Investment Workspace (historical decisions section). Decision Workspace (in review mode). Future Decision Review Workspace."*

**Anti-Patterns [C].** Do not present Decision History as a system-wide catalog spanning subjects it is not scoped to — its own canonical purpose is subject-scoped, per `UX-012B` §8's own text.

---

### 7.6 Decision Amendment

**Purpose [C].** Formally links a new Decision to a prior one, with explicit documentation of what changed and why. Per `UX-012B` §8: *"Formally links a new Decision to a prior one, with explicit documentation of what changed and why."*

**Semantic Meaning [C].** Additive only. Per `UX-012B` §8: *"Character: amendments do not modify the original Decision. They are additive historical records."* This document explicitly preserves this framing rather than any alternative "modification" framing found elsewhere in the corpus's own **[U]** Unconfirmed material, consistent with `UX-000` UXP-007 ("Historical Meaning Is Never Silently Rewritten... a later correction is additive, never a silent rewrite") and `APS-002` IR-R-027/059's own Superseded Content model.

**Product Correspondence [C].** Governed by the same historical-immutability principles as Historical Decision, above; introduces no new Product meaning.

**Ownership [C].** User-owned, consistent with the original Decision's own ownership.

**Composition [C].** Component, referencing the original Decision by identifier — it does not compose the original Decision's own content, only a reference to it plus the amendment's own fields.

**States [C].** Current (this is the most recent amendment), Superseded (a later amendment has been made) — `UX-012B` §8.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `originalDecisionId` | string | — | Yes | The Decision being amended |
| `amendmentReason` | string | — | Yes | Per `UX-012B` §8: *"the reason for the amendment"* |
| `changedField` | string | — | Yes | The specific field changed |
| `beforeValue` | string | — | Yes | Historical treatment (tertiary text) |
| `afterValue` | string | — | Yes | Primary treatment |
| `recordedAt` | timestamp | — | Yes | |
| `status` | `'current' \| 'superseded'` | `'current'` | Yes | |

**Interaction [C].** Read-only, presented as a before/after comparison row within the amended Decision's own historical context (`UX-012B` §8's own visual-treatment description).

**Accessibility [C].** Before/after values individually announced, consistent with `UX-012A` §15's own non-color-communication requirement for amended-content states.

**Responsive Behaviour [IR].** Stacked before/after presentation on mobile, side-by-side on desktop and tablet, consistent with `UX-012` §73's own general Before/After component responsive rule.

**Token Mapping [C]**, reusing `UX-012D` §3's own already-named `Historical Content` group for the before value and `Decision` group for the after value:

| Visual Property | Token |
|---|---|
| Before value (historical) | `color.text.historical` |
| After value (current, amended) | `type.decision.statement` |

**Engineering Notes [C].** Per `UX-012B` §8: *"Reuse rules: Decision History component. Decision Workspace (version history panel)."*

**Anti-Patterns [C].** Do not present an amendment as modifying the original Decision's own recorded content — it is a new, additive record only (`UX-012B` §8; `UX-000` UXP-007).

---

### 7.7 Decision Review

**Purpose [C].** Two compatible framings, both preserved rather than collapsed into a single Product-layer lifecycle claim. Per `UX-012` §25: *"The formal re-examination of a prior Decision in light of new information."* Per `UX-012B` §8: *"Represents a completed review of a prior decision — the verdict, the key finding, and any resulting changes."* The first names the workflow event; the second names the settled record that event produces. Both are UX/workflow-layer statements about the same underlying occasion, not two competing definitions — the identical relationship this document already applies to Final Decision Card's own dual framing in `UX-012` §25 and `UX-012B` §8.

**Semantic Meaning [C].** Decision Review is a UX/workflow artifact, not a Product Concept. `APP-001` §3.6 formally considered and rejected "Review" as an independent Product Concept: *"The candidate concept 'Review' was considered and rejected as a separate entry: it names the act of exercising Learning, not a distinct thing Learning does not already fully cover. Accepting it would duplicate an already-accepted concept, which the Architectural Rules explicitly forbid."* (`APP-001` §4: *"Review. Rejected — see Section 3.6. Fully absorbed by Learning."*) `UX-000` UXD-R-084 restates this at the UX layer: *"Review is an occasion or workflow that MAY provide the occasion on which a Learning Act occurs, per APS-004 LR-R-097. Review is not itself Learning and SHALL NOT be presented as identical to it."*

**Product Correspondence [C].** Six statements, each directly sourced, none inferred beyond its citation:
- Review is rejected as an independent Product Concept by `APP-001` §3.6/§4, as quoted above.
- Decision Review is not Learning, per `APS-004` LR-R-098: *"Decision Review SHALL NOT be treated as identical to Learning itself."*
- Decision Review MAY provide the occasion for a Learning Act, per `APS-004` LR-R-097: *"A Decision Review MAY provide the occasion on which a Learning Act occurs."*
- Decision Review MAY provide the occasion for an Outcome-recording act, per `APS-005` OR-R-085: *"A Decision Review MAY provide the occasion on which an Outcome is recorded."*
- Decision Review does not own or contain a Learning Result or an Outcome as Product objects, per `APS-005` OR-R-086: *"Decision Review SHALL NOT be treated as identical to Outcome, nor as an architectural container of Outcome"* — and, by the identical reasoning `APS-004` LR-R-098 already establishes for Learning, Decision Review is not an architectural container of a Learning Result either.
- Decision Review never evaluates Decision Quality from Outcome, per `APS-005` OR-R-016/OR-R-072/OR-R-093 and ORINV-008/ORINV-016 (Outcome SHALL NOT characterize Decision Quality, in whole or in part, under any capability), restated at the UX layer by `UX-000` UXD-R-077–082.

**Ownership [C].** Human Ownership discipline, per `UX-000` §10 (UXD-R-048–053), preserved without modification:
- The Investor initiates or performs the review.
- The Investor owns any genuine interpretation that occurs during it.
- The Investor owns any resulting Learning Act, per `APS-004` LR-R-147 (*"A Learning Act SHALL begin only through an explicit, Investor-initiated act"*) and LRINV-018 (*"No Autonomous Atlas Learning. Atlas SHALL NOT exercise Learning autonomously on the Investor's behalf"*).
- The Investor owns any resulting Decision change (amendment or supersession), consistent with Decision Amendment's own ownership, above.
- The Investor owns the act of recording any resulting Outcome, per `APS-005` OR-R-098: *"The Investor owns the act of recording an Investor-originated Outcome"* — while the Outcome itself remains owned by neither party, per OR-R-006/OR-R-042 (*"Outcome itself SHALL be owned by neither the Investor nor Atlas; it is a fact about the world, not a possession"*).

Atlas MAY surface due reviews, organize the material for comparison, summarize already-existing information, assist the comparison between prior and current reasoning, and present attributable suggestions. Atlas MAY NOT perform the Review itself, create a Learning Result autonomously (`APS-004` LR-F-012: *"Atlas attempts to exercise Learning autonomously... Atlas SHALL refuse to record the Learning Result"*), decide the verdict, record an Outcome autonomously (`APS-005` OR-R-097: *"Atlas SHALL NOT fabricate an Outcome where none has been recorded"*), or supersede a Decision autonomously (`UX-000` UXD-R-053, applied identically to the Record Decision action).

**Composition [IR].** Composite Component, per `UX-013F`'s own classification model, following the identical reasoning already applied to Final Decision Card, above — it owns a defined composition of its own named fields (verdict, key finding, review date, what changed, next review condition), not merely a reference to another record. Two further facts MAY be associated with a completed Decision Review, and both are modeled as optional, external, provenance-preserving **references**, never as owned or embedded sub-objects: a Review Conclusion (`UX-013B` §1's own Review Conclusion variant, already canonical), present only where its own Learning-Act precondition is independently satisfied; and a recorded Outcome (`APS-005`-governed), present only where independently recorded per OR-R-085. Neither reference makes Decision Review an architectural container of the thing it references, per OR-R-086 and the identical reasoning for Learning.

**States [C].** Complete, Superseded — per `UX-012B` §8: *"States: Complete, Superseded."* **Documentary note [IR].** `UX-012` §25 does not itself enumerate a states list for Decision Review (it states only Purpose, Output, and Reuse) — this is silence, not disagreement, so no Documentary Note disclosing a source conflict is required; `UX-012B` §8 is the sole and uncontested source for this component's own state model. No pre-completion "in progress" state is specified by either source, and none is invented here, per this task's own governing instruction.

**Properties [IR]** (named here for the first time as typed properties, following the fields `UX-012B` §8 already names in prose; enum values for `verdict` are drawn from `UX-012B` §5's own Review Conclusion entry, which enumerates the identical underlying verdict this component's own "Review verdict" field names without itself re-listing the four values — a bounded, disclosed cross-reference, not an invention):

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `reviewId` | string | — | Yes | Assigned on completion |
| `originalDecisionId` | string | — | Yes | The Decision being reviewed |
| `verdict` | `'THESIS_VALID' \| 'THESIS_WEAKENED' \| 'ASSUMPTION_BROKEN' \| 'DECISION_SUPERSEDED'` | — | Yes | Per `UX-012B` §8 ("Review verdict") and §5 (the four enumerated values) |
| `keyFinding` | string | — | Yes | Per `UX-012B` §8: "Key finding sentence" |
| `reviewDate` | timestamp | — | Yes | |
| `whatChanged` | string | — | No | Per `UX-012B` §8: "What changed since the original decision" |
| `nextReviewCondition` | string | — | No | Per `UX-012B` §8: "Next review condition" |
| `status` | `'complete' \| 'superseded'` | `'complete'` | Yes | The two states `UX-012B` §8 names |
| `reviewConclusionId` | string \| null | `null` | No | External reference only, per Composition, above. Populated only if the Learning-Act precondition (`UX-000` UXD-R-071 item 4) is independently satisfied — never inferred from this component's own existence |
| `outcomeId` | string \| null | `null` | No | External reference only, per Composition, above. Populated only if independently recorded, per `APS-005` OR-R-085 — never inferred from this component's own existence |

**Interaction [C].** Inspect the original Decision (navigates via `originalDecisionId`, consistent with Decision Amendment's own reference pattern, above). Compare prior and current reasoning, using the Historical Comparison component per `UX-012B` §7 (*"Reuse rules: Decision Workspace (historical decision panel in review mode)"*) — this document does not restate Historical Comparison's own specification. Record the Investor-authored verdict and key finding — this is a genuine Investor act, consistent with `UX-000` UXD-R-048's own general Human Ownership rule, applied identically to every other Investor-owned recording act in this document. Inspect resulting changes (`whatChanged`). Open the resulting Decision History entry, per `UX-012B` §8: *"Reuse rules: Decision History component."* Inspect the linked Review Conclusion only where `reviewConclusionId` is populated. Inspect the linked Outcome only where `outcomeId` is populated. **Record Decision, Decision Amendment, Decision supersession, Outcome recording, and any resulting Learning Act each remain separate, independently Investor-owned acts** — completing a Decision Review does not itself perform, trigger, or imply any of them.

**Accessibility [C].** Verdict and historical/superseded status are communicated through both text label and color, never color alone, per `UX-012A` §15's own non-color-communication requirement, applied identically to Decision Amendment's before/after states, above. Review state (`status`) and provenance (`reviewConclusionId`/`outcomeId` presence) are programmatically available via ARIA attributes, not conveyed by visual treatment alone. The prior/current comparison follows linear reading order, consistent with `UX-012B` §7's own Historical Comparison reading order ("Current state first, prior state below").

**Responsive Behaviour [IR].** Stacked prior/current presentation on mobile, side-by-side on desktop and tablet — consistent with Decision Amendment's own before/after responsive rule, above, and `UX-012` §73's own general comparison-component responsive rule. No interaction specified above (inspect original Decision, compare reasoning, inspect changes, open Decision History entry, inspect Review Conclusion, inspect Outcome) becomes unavailable on smaller viewports; each degrades to full-screen sequential presentation, per `UX-012` §73's own general rule already applied to every other component in this document.

**Token Mapping [C]/[IR]**, reusing `UX-012D` §3's own already-named `Decision` and `Historical Content` semantic token groups directly — no new token is introduced:

| Visual Property | Token |
|---|---|
| Card container | `surface.decision.card` (existing, `UX-012D` §3) |
| Verdict and key finding text | `type.decision.statement` (existing, `UX-012D` §3, reused) |
| Internal card padding | `space.decision.card.internal` (existing, `UX-012D` §3) |
| Superseded-state text | `color.text.historical` (existing, `UX-012D` §3, `Historical Content` group — reused per the identical pattern already applied to Decision Amendment's own before-value, above) |

**Engineering Notes [C].** Decision Review is not Product Learning — it is, at most, the occasion on which a genuine Investor-initiated Learning Act may occur, per `APS-004` LR-R-097/LR-R-098. Its own `reviewConclusionId` reference remains conditional on that Learning Act's genuineness, per `UX-000` UXD-R-071 item 4 and UXD-R-086 — this precondition is not restated in full here; it is the already-settled rule governing `UX-013B`'s own Review Conclusion variant and is not reopened by this component's own addition. Its own `outcomeId` reference remains external to this component in every sense — Decision Review never owns, contains, computes, or derives the Outcome it may reference, per `APS-005` OR-R-086. `Review Summary` and `Review Outcome` remain Deferred, per Section 9, below — this component's own anatomy already covers every fact either name was claimed to add. No interaction path in this component permits autonomous Atlas review, verdict determination, Learning Result creation, or Outcome recording.

**Anti-Patterns [C].** Do not present Decision Review, or any workflow that produces it, as itself constituting Learning (`UX-000` UXD-R-084/086; `APS-004` LR-R-098). Do not populate `reviewConclusionId` without an independently verified, genuine Investor-initiated Learning Act (`UX-000` UXD-R-071 item 4). Do not embed Outcome content as an owned or nested field of Decision Review — it is a reference only (`APS-005` OR-R-086). Do not use a linked Outcome, or Outcome favorability, as a Decision Quality verdict on the original Decision (`APS-005` OR-R-016/072/093, ORINV-008/016; `UX-000` UXD-R-077–082). Do not silently convert an Atlas-surfaced comparison or summary into an Investor-attributed verdict without a genuine Investor act (`UX-000` UXD-R-048, applied identically to every other recording act in this document). Do not implement `Review Summary` or `Review Outcome` as separate, independently canonical components — neither has documentary-supported anatomy beyond what Decision Review, Review Conclusion, and Decision Summary already jointly cover, per Section 9, below.

---

## 8. Historical Behavior Summary (Cross-Component)

All seven components above share the identical historical-immutability discipline, traced consistently to `UX-012` §27 (Historical Components), `UX-000` UXP-007, and `APS-002` IR-R-027/059: reduced opacity (`color.text.historical`), permanently locked (no editing controls, no hover state, no cursor change), timestamp always visible. No component specified in this document permits an exception to this rule. Once Complete or Superseded, Decision Review becomes eligible for presentation via the Historical Review component `UX-012B` §10 separately names — that component's own anatomy is out of this document's own scope, per this task's own governing instruction, and remains a candidate for a future Historical-tier authoring phase.

## 9. Deferred

The following constructs are explicitly **not** specified in this document. Each is named here, with the exact reason for deferral, so that a future phase of `UX-013C` authorship — or a dedicated architectural decision, where noted — has a clear, honest starting point, per `ADR-001` Governance Rule 5 ("Interim documents must disclose their own confidence level").

- **`DecisionCard`** — a unified, multi-lifecycle-state component spanning proposed/draft/final/recorded/historical/superseded/under-review, referenced in `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md` §5–6. Traces only to that document's own **[U]** Unconfirmed account. This session's own completed Final Decision Card ↔ DecisionCard investigation found a genuine, unreconciled divergence from this document's own canonical Final Decision Card (different compositional model; missing Confidence and Invalidation Condition properties; overlapping, uncoordinated lifecycle span with Proposed Decision) — re-verified, not merely cited, against `UX-012`/`UX-012B`'s own text during this document's own authorship. Not adopted here. A future, dedicated resolution is required before any unified lifecycle-state Decision component may be treated as canonical.
- **`Decision Outcome`** — traces only to the interim note's own **[U]** account (`decisionId, outcomeType, observedResult, observationDate, uncertainty`). No `UX-012`/`UX-012B` component by this name exists. Renders the already-accepted Product Concept Outcome (`APP-001` §3.11) but has no documentary-supported anatomy of its own yet.
- **`Decision Supersession`** — traces only to the interim note's own **[U]** account. No `UX-012`/`UX-012B` component by this exact name exists, though the general "Superseded" status value is already used within Decision Summary and Decision Amendment, above, per `UX-012B` §8. A dedicated component for cross-decision supersession (as opposed to the status value already specified) is not yet documentary-supported.
- **`Decision Rationale Reference`** — traces only to the interim note's own **[U]** account (`decisionId, summaryText, expandsTo`). No `UX-012`/`UX-012B` equivalent found.
- **`Decision Required` and `Decision Rationale`** — named as canonical Decision Workspace sequence positions 2 and 4 (`ADR-002` C-03), but not specified as standalone components anywhere in `UX-012`/`UX-012B`. Their content is a Workspace-section-level concern, feeding Final Decision Card's own Primary Reason field (Decision Rationale specifically); component-level specification is deferred to a future phase, once such a component is genuinely documentary-supported.
- **`Review Summary`** — traces only to `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own **[U]** account, and to the unrelated, pre-existing `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md`'s own uncorroborated claim of a "Review Summary" Composite Component. Neither has independent canonical anatomy in `UX-012`/`UX-012B` — no component by this name appears in either source. Decision Review (§7.7, above), Review Conclusion (`UX-013B` §1), and Decision Summary (§7.4, above) already jointly cover every fact either account claims for it (scope, original decision reference, findings, conclusion). Not adopted here. Confirmed by the completed Decision Review / Review Summary / Review Outcome Architecture Reconciliation investigation; not reopened by this document's own addition of Decision Review.
- **`Review Outcome`** — traces only to the same two unsupported sources as `Review Summary`, above. No `UX-012`/`UX-012B` component by this name exists. Beyond lacking documentary anatomy, this name is structurally disfavored: modeling a "Review Outcome" as a Review-owned construct that embeds Outcome content risks treating Decision Review as an architectural container of Outcome, which `APS-005` OR-R-086 directly forbids (*"Decision Review SHALL NOT be treated as identical to Outcome, nor as an architectural container of Outcome"*). Where an Outcome is genuinely recorded in connection with a Decision Review, per `APS-005` OR-R-085, Decision Review's own `outcomeId` property (§7.7, above) already models it correctly — as an optional, external, provenance-preserving reference, never an owned field. Not adopted here.

## 10. Out of Scope

**Proposed Decision Candidate Content** — fully specified, canonical, `ADR-003`-governed, in `UX-013B` §10. This document cross-references it (Section 7.1, Interaction) as the input to Proposed Decision; it does not restate or redefine it. Its own operative specification remains `UX-013B`'s.

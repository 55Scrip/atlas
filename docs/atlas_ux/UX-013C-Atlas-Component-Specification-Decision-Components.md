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

The Decision tier renders the Product Concept Decision (per `APP-000` §5, `APS-001`) across its lifecycle: formation (Proposed Decision), commitment (Final Decision Card, and the Record Decision action governed within it), and historical presentation (Historical Decision, Decision Summary, Decision History, Decision Amendment). Six components are canonical and fully specified below, all traced directly to `UX-012` §25 and `UX-012B` §8/§10.

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

**Product Correspondence [C].** Historical immutability is governed at the Product layer by `APS-002` IR-R-027/IR-R-059 (Superseded Content preservation) and reflected in `UX-000` UXD-R-105/UXD-R-106's own non-erasure discipline. This component asserts no independent Product meaning beyond presenting that already-governed immutability.

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

## 8. Historical Behavior Summary (Cross-Component)

All six components above share the identical historical-immutability discipline, traced consistently to `UX-012` §27 (Historical Components), `UX-000` UXD-R-105/UXD-R-106, and `APS-002` IR-R-027/059: reduced opacity (`color.text.historical`), permanently locked (no editing controls, no hover state, no cursor change), timestamp always visible. No component specified in this document permits an exception to this rule.

## 9. Deferred

The following constructs are explicitly **not** specified in this document. Each is named here, with the exact reason for deferral, so that a future phase of `UX-013C` authorship — or a dedicated architectural decision, where noted — has a clear, honest starting point, per `ADR-001` Governance Rule 5 ("Interim documents must disclose their own confidence level").

- **`DecisionCard`** — a unified, multi-lifecycle-state component spanning proposed/draft/final/recorded/historical/superseded/under-review, referenced in `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md` §5–6. Traces only to that document's own **[U]** Unconfirmed account. This session's own completed Final Decision Card ↔ DecisionCard investigation found a genuine, unreconciled divergence from this document's own canonical Final Decision Card (different compositional model; missing Confidence and Invalidation Condition properties; overlapping, uncoordinated lifecycle span with Proposed Decision) — re-verified, not merely cited, against `UX-012`/`UX-012B`'s own text during this document's own authorship. Not adopted here. A future, dedicated resolution is required before any unified lifecycle-state Decision component may be treated as canonical.
- **`Decision Outcome`** — traces only to the interim note's own **[U]** account (`decisionId, outcomeType, observedResult, observationDate, uncertainty`). No `UX-012`/`UX-012B` component by this name exists. Renders the already-accepted Product Concept Outcome (`APP-001` §3.11) but has no documentary-supported anatomy of its own yet.
- **`Decision Supersession`** — traces only to the interim note's own **[U]** account. No `UX-012`/`UX-012B` component by this exact name exists, though the general "Superseded" status value is already used within Decision Summary and Decision Amendment, above, per `UX-012B` §8. A dedicated component for cross-decision supersession (as opposed to the status value already specified) is not yet documentary-supported.
- **`Decision Rationale Reference`** — traces only to the interim note's own **[U]** account (`decisionId, summaryText, expandsTo`). No `UX-012`/`UX-012B` equivalent found.
- **`Decision Required` and `Decision Rationale`** — named as canonical Decision Workspace sequence positions 2 and 4 (`ADR-002` C-03), but not specified as standalone components anywhere in `UX-012`/`UX-012B`. Their content is a Workspace-section-level concern, feeding Final Decision Card's own Primary Reason field (Decision Rationale specifically); component-level specification is deferred to a future phase, once such a component is genuinely documentary-supported.

## 10. Out of Scope

**Proposed Decision Candidate Content** — fully specified, canonical, `ADR-003`-governed, in `UX-013B` §10. This document cross-references it (Section 7.1, Interaction) as the input to Proposed Decision; it does not restate or redefine it. Its own operative specification remains `UX-013B`'s.

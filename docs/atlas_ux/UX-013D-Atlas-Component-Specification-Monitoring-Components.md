# UX-013D — Atlas Component Specification: Monitoring Components

**Phase 1 — Canonical Monitoring Architecture.** Governing references: `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md`; `UX-012B-Atlas-Design-System-Components-Reusable-Patterns.md`; `UX-000-Atlas-UX-Doctrine.md` (RC v1.0); `ADR-002-Critical-UX-Architecture-Resolutions.md`; `UX-013C-Atlas-Component-Specification-Decision-Components.md`.

**Status: Canonical (Phase 1 — Monitoring Components only).** This document specifies, in production-ready detail, only the Monitoring-tier components already fully supported by committed, canonical documentary evidence — `UX-012` and `UX-012B` directly. It is genuinely, honestly authored on 2026-08-02, citing only documents that exist and are checkable at the time of writing, following the identical process `UX-013A`, `UX-013B`, and `UX-013C` themselves used, per `ADR-001-Missing-Source-Volume-Governance.md`'s own Governance Rule 4 and Option B. It does not reconstruct, does not claim descent from, and is not a replacement for `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own account of an absent `UX-013D` — that account remains its own document's own separate, `[U]` Unconfirmed record. Where this document's own Monitoring-tier scope overlaps that account, this document supersedes it for every component specified below; it does not supersede the interim note's own Decision, AI Collaboration, or domain-specific Metadata content, which remains entirely outside this document's own Phase 1 scope.

**Provenance convention used in this document**, identical to `UX-013C`'s own: **[C]** (Canonical — traced directly to `UX-012`, `UX-012B`, `UX-000`, an Accepted UX ADR, or a directly-cited Product Architecture document's own committed text) and **[IR]** (Implementation Refinement — anatomy, property, or token detail newly authored here, required to make a canonical purpose production-ready, and not itself asserting new meaning). No claim in this document is tagged **[U]** — anything that would require such a tag is moved to Section 9, Deferred.

---

## 1. Purpose

This document specifies every Atlas Monitoring-tier component whose architecture is already settled by `UX-012` and `UX-012B`, in the same production-ready detail `UX-013C` already provides for the Decision tier. It closes part of the documentary gap `ADR-001` and `ADR-002` C-05 identified, for the Monitoring tier specifically, through genuine new authorship rather than reconstruction.

This document does not specify Decision (see `UX-013C`), AI Collaboration, or domain-specific Metadata components. Those remain entirely outside this Phase 1 scope.

## 2. Authority Chain

Atlas Core Architecture Doctrine (Final) → `APP-000`/`APP-001` (Normative Product) → `APS-001` through `APS-005` (Normative Product, the sole authority for each accepted concept's own normative behavior) → `UX-000-Atlas-UX-Doctrine.md`, RC v1.0 (governing UX doctrine, per `UXD-R-097`) → `ADR-002` (Accepted, Normative UX, subordinate to `UX-000`, authoritative within its own stated scope) → `UX-012`/`UX-012B`/`UX-012C`/`UX-012D` (Normative UX, the Design System's own semantic authority) → `UX-013C` (peer, Decision-tier realization) → this document (subordinate, Monitoring-tier realization).

This authority order is never reversed. This document does not amend `UX-000`. It does not amend `ADR-001` through `ADR-004`. It does not redefine, narrow, or extend any Product Concept, Product Principle, or Core Domain Object. It does not introduce new terminology — every component name, state name, and property concept below is traced to `UX-012` or `UX-012B`'s own committed text. Where `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own Monitoring-category account names a construct or property not independently supported by `UX-012`/`UX-012B`, it is not adopted here; per the authority order above, the Interim Note's own account never overrides `UX-012`/`UX-012B`, and is used only where explicitly marked unconfirmed.

## 3. Relationship to UX-012

`UX-012` (and `UX-012B`, its own companion component specification) remain the semantic authority for every component this document specifies. This document adds implementation-ready anatomy, properties, states, interaction, accessibility, and token detail; it does not redefine any component's purpose or meaning. Where this document's own detail and `UX-012`/`UX-012B`'s own text could be read to diverge, `UX-012`/`UX-012B` govern. This document does not silently absorb or replace `UX-012`; `UX-012` §26 and `UX-012B` §9 remain fully valid, unedited, and authoritative in their own right. **Two components below (Review Trigger, Implementation Follow-up) carry a genuine, disclosed state-list discrepancy between `UX-012` §26's own account and `UX-012B` §9's own account** — see each component's own Documentary note; this document does not silently resolve either discrepancy.

## 4. Relationship to UX-013F

`UX-013F-Foundation-Reasoning-Component-Library-Assembly.md` is this document's peer, canonical for the Foundation and Reasoning tiers and for the cross-cutting infrastructure every tier depends on. This document does not restate that content; it references it by name (`StatusBadge`, `SectionContainer`, `MetadataBlock`) exactly as `UX-013C` already does. This document adopts `UX-013F`'s own ten-type classification model to classify each component below, without redefining any classification type.

## 5. Monitoring Architecture Overview

The Monitoring tier renders ongoing, post-Decision observation — conditions Atlas watches on the Investor's behalf, and the triggers that surface when those conditions warrant the Investor's attention. **Monitoring itself has no direct correspondence to any `APP-001` §3.x accepted Product Concept** — a targeted search of `APP-001-Atlas-Product-Concept-Taxonomy.md` found no entry named "Monitoring." What Monitoring renders is a UX-layer operationalization of already-governed Product content: the Review Condition and Invalidation Condition fields `UX-013C`'s own Final Decision Card already specifies (§7.2), and, where a Review Trigger leads to a formal Decision Review, the resulting occasion connects to the already-accepted Product Concept Learning, per `APS-004` LR-R-097: *"A Decision Review MAY provide the occasion on which a Learning Act occurs."* This document asserts no independent Product meaning for Monitoring beyond this already-governed correspondence.

Five components are canonical and fully specified below, all traced directly to `UX-012` §26 and `UX-012B` §9: Monitoring Condition, Review Trigger, Invalidation Trigger, Implementation Follow-up, Scheduled Review.

Several further Monitoring-adjacent constructs referenced in `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own account — a separate `MonitoringTrigger` distinct from Review Trigger, `Review Summary`, `Review Outcome`, `Implementation Plan`, `Implementation Status`, `Outcome Tracking`, and `Timeline Entry` — are not specified in this document. Each traces only to that account's own **[U]** Unconfirmed status, and none is independently justified by `UX-012`/`UX-012B`'s own text. Per this task's own governing instruction, they are not authored here; see Section 9, Deferred.

## 6. Canonical Component Inventory

| Component | Classification | Status | Source |
|---|---|---|---|
| Monitoring Condition | Composite Component | **[C]** Canonical | `UX-012` §26, `UX-012B` §9 |
| Review Trigger | Component | **[C]** Canonical | `UX-012` §26, `UX-012B` §9 |
| Invalidation Trigger | Component | **[C]** Canonical | `UX-012` §26, `UX-012B` §9 |
| Implementation Follow-up | Component | **[C]** Canonical | `UX-012` §26, `UX-012B` §9 |
| Scheduled Review | Component | **[C]** Canonical | `UX-012` §26, `UX-012B` §9 |

Not specified in this document — see Section 9: `MonitoringTrigger` (as a construct independent of Review Trigger), `Review Summary`, `Review Outcome`, `Implementation Plan`, `Implementation Status`, `Outcome Tracking`, `Timeline Entry`.

---

## 7. Component Specifications

### 7.1 Monitoring Condition

**Purpose [C].** A single trackable condition that determines whether a Decision remains valid. Per `UX-012` §26: *"A single trackable condition that determines whether a Decision remains valid."*

**Semantic Meaning [C].** Per `UX-012B` §9: *"A single trackable condition that Atlas is actively observing — linked to a prior decision, assumption, or thesis element."*

**Product Correspondence [C].** No direct `APP-001` §3.x correspondence (Section 5, above). Monitoring Condition presents ongoing observation of already-governed Decision, Assumption, or thesis content; it does not itself decide or redefine a Product rule, per `UX-000` UXD-R-020, and does not decide or extend AI autonomy, per `UX-000` UXD-R-035.

**Ownership [C].** Established at Decision-recording time (`UX-012` §26: *"Reuse: Decision Workspace (establishment)"*), by the Investor or Atlas-suggested and Investor-confirmed, consistent with the general Atlas Suggestion model. The ongoing observation itself is Atlas-performed surfacing, not an independent act of Investor Judgment, Commitment, or Learning, per `UX-000` UXD-R-048.

**Composition [C].** Composite Component, per `UX-013F`'s own classification model (it owns a defined composition: condition statement, threshold, current status, optional linked decision/assumption, per `UX-012B` §9).

**States [C].** `UX-012B` §9's own fuller list is used as this document's primary source, consistent with `UX-013C`'s own established practice of preferring the component-level specification: *"Active (observation ongoing, condition not approaching trigger), Approaching (condition is moving toward the trigger threshold — amber treatment), Triggered (the condition has met the trigger — the item auto-surfaces in Dashboard and expands in its containing section), Resolved (the trigger was met and has been acknowledged and addressed), Expired (the decision the condition was linked to has been superseded or closed)."* `UX-012` §26's own shorter lifecycle statement — *"Established → Active → Approaching (threshold near) → Triggered (threshold crossed) → Acknowledged → Resolved"* — is consistent with, not contradicted by, this fuller list; it does not separately name "Expired," which `UX-012B` adds without contradicting anything `UX-012` itself states.

**Properties [IR]** (named here for the first time, following the fields both sources already name in prose):

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `conditionId` | string | — | Yes | |
| `linkedDecisionId` | string | — | No | Linked decision or assumption, per `UX-012B` §9 |
| `conditionStatement` | string | — | Yes | |
| `threshold` | string | — | Yes | The trigger threshold definition |
| `status` | `'active' \| 'approaching' \| 'triggered' \| 'resolved' \| 'expired'` | `'active'` | Yes | Per `UX-012B` §9 |
| `establishedAt` | timestamp | — | Yes | Monitoring start date, per `UX-012` §26 |
| `observationCadence` | string | — | No | Optional, per `UX-012B` §9 |

**Interaction [C].** Per `UX-012B` §9: *"Active: expand to view the full condition and current status. Approaching: expand automatically. Triggered: expand automatically; shows an acknowledgment control and a link to the associated decision or Workspace."* Approaching and Triggered states surface to the Dashboard and may generate Atlas Warnings, per `UX-012` §26.

**Accessibility [IR].** Consistent with `UX-012A` §15's own non-color-communication requirement: status is communicated through text label (Active/Approaching/Triggered/Resolved/Expired) in addition to amber/red visual treatment, never by color alone.

**Responsive Behaviour [IR].** Consistent with `UX-012` §73's own general condensed-component responsive rule (full-width entries on mobile).

**Token Mapping [C]**, using `UX-012D` §3's own already-named `Monitoring` semantic token group: *"tokens for monitoring condition presentations. Values: `color.semantic.amber` (for Approaching state), `color.border.monitoring-rule` (the left-border rule on monitoring items), `type.status.monitoring`."*

| Visual Property | Token |
|---|---|
| Approaching state border/text | `color.semantic.amber` |
| Left-border rule | `color.border.monitoring-rule` |
| Status label | `type.status.monitoring` |

**Engineering Notes [C].** Per `UX-012B` §9: *"Reuse rules: Decision Workspace (Section 9). Dashboard (monitoring signal). Future Monitoring Workspace. Investment Workspace (linked to thesis assumptions)."*

**Anti-Patterns [C].** Do not permit Atlas to autonomously resolve or dismiss a Monitoring Condition without an identifiable Investor act — acknowledgment requires the Investor, per `UX-000` UXD-R-048's own general rule applied here.

---

### 7.2 Review Trigger

**Purpose [C].** Communicates that a Review Condition has been met and a formal Review is required. Per `UX-012` §26: *"Communicates that a Review Condition has been met and a formal Review is required."*

**Semantic Meaning [C].** Per `UX-012B` §9: *"Extends Monitoring Condition. A monitoring condition whose activation reopens a specific prior decision for review."*

**Product Correspondence [C].** The Review Condition it watches is the already-governed field `UX-013C` §7.2 specifies within Final Decision Card. Where this trigger's own activation leads to a formal Decision Review, `APS-004` LR-R-097 governs the resulting occasion's relationship to Learning: *"A Decision Review MAY provide the occasion on which a Learning Act occurs"* — this component itself does not perform or constitute that Learning Act, per `UX-000` UXD-R-032 and UXD-R-086.

**Ownership [C].** The underlying Review Condition is Investor-owned (established as part of the Final Decision Card, `UX-013C` §7.2). The trigger's own firing is Atlas-performed surfacing, not an Investor act.

**Composition [C].** Component extending Monitoring Condition (`UX-012B` §9) — it does not compose independent sub-components beyond what Monitoring Condition already provides, plus its own additional required content.

**Documentary note [IR].** `UX-012` §26 states Review Trigger's own states as *"pending, acknowledged, resolved."* `UX-012B` §9 instead frames it as extending Monitoring Condition's own state set, with *"State addition: Due for Review (triggered state for a review trigger — the associated decision transitions to Due for Review state and appears prominently in Dashboard)."* These are not identical vocabularies. This document follows `UX-012B` §9 as its primary source, consistent with its own practice throughout (Section 3, above), while disclosing `UX-012` §26's own distinct three-state list rather than silently discarding it. Reconciling the two is a future `UX-012`-family correction, outside this document's own authority.

**States [C/IR]** — per the Documentary note above: Monitoring Condition's own inherited states (Active, Approaching, Triggered, Resolved, Expired) plus **Due for Review**, per `UX-012B` §9. `UX-012` §26's own alternative list (pending, acknowledged, resolved) is disclosed, not adopted, per the note above.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `linkedDecisionId` | string | — | Yes | The decision being monitored |
| `reviewCondition` | string | — | Yes | References the Final Decision Card's own `reviewCondition` field, `UX-013C` §7.2 |
| `status` | inherited from Monitoring Condition, plus `'due-for-review'` | — | Yes | |

**Interaction [C].** Per `UX-012` §26: *"Behavior: navigates to Decision Review mode in the relevant Workspace."* Per `UX-012B` §9: *"Additional required content: The linked decision (a Decision Summary component showing the decision being monitored). The review action ('Atlas will open a Decision Workspace for this decision when this trigger is met')."*

**Accessibility [IR].** Consistent with Monitoring Condition's own accessibility rules (§7.1, above); the "Due for Review" state is announced via the same non-color-communication requirement.

**Responsive Behaviour [IR].** Consistent with Monitoring Condition's own responsive rule (§7.1, above).

**Token Mapping [C]**, reusing `UX-012D` §3's own `Monitoring` token group (§7.1, above); no additional token was found named specifically for Review Trigger.

**Engineering Notes [C].** Per `UX-012B` §9: *"Reuse rules: Decision Workspace (review plan, Section 11). Dashboard (due-for-review signal)."*

**Anti-Patterns [C].** Do not permit Review Trigger's own activation to itself constitute a Decision Review or a Learning Act — per `APS-004` LR-R-147, a Learning Act begins only through an explicit, Investor-initiated act.

---

### 7.3 Invalidation Trigger

**Purpose [C].** Communicates that an Invalidation Condition has been met. Per `UX-012` §26: *"Communicates that an Invalidation Condition has been met."*

**Semantic Meaning [C].** Per `UX-012B` §9: *"Extends Monitoring Condition. A monitoring condition linked to an Invalidation Condition — one that, when triggered, signals that the fundamental basis of the decision may no longer hold."*

**Product Correspondence [C].** The Invalidation Condition it watches is the already-governed field `UX-013C` §7.2 specifies within Final Decision Card. This component asserts no independent Product meaning beyond surfacing that field's own already-governed threshold having been met.

**Ownership [C].** The underlying Invalidation Condition is Investor-owned (`UX-013C` §7.2). The trigger's own firing is Atlas-performed surfacing.

**Composition [C].** Component extending Monitoring Condition (`UX-012B` §9).

**States [C].** Per `UX-012` §26: *"States: triggered, acknowledged."* Not contradicted by `UX-012B` §9, which describes visual treatment ("amber treatment transitions to restrained red") without restating a separate state list — no documentary tension found for this component.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `linkedDecisionId` | string | — | Yes | |
| `invalidationCondition` | string | — | Yes | References the Final Decision Card's own `invalidationCondition` field, `UX-013C` §7.2 |
| `status` | `'triggered' \| 'acknowledged'` | — | Yes | Per `UX-012` §26 |

**Interaction [C].** Per `UX-012` §26: *"Behavior: requires the user to explicitly acknowledge the Invalidation and initiate a new reasoning process."* Severity higher than Review Trigger, per the same source.

**Accessibility [IR].** Higher-severity visual treatment (amber → restrained red, per `UX-012B` §9) is accompanied by an explicit text label, never by color alone, consistent with `UX-012A` §15.

**Responsive Behaviour [IR].** Consistent with Monitoring Condition's own responsive rule (§7.1, above).

**Token Mapping [IR]**, extending `UX-012D` §3's own `Monitoring` token group toward its own already-named restrained-red semantic accent (the general `color` token category, `UX-012D` §2, includes red among the "semantic accent colors (amber, green, red, blue) in their restrained Atlas forms"):

| Visual Property | Token |
|---|---|
| Triggered state (escalated) | Restrained red variant of the general semantic accent color group |
| Acknowledged state | `color.semantic.amber` (as inherited from Monitoring Condition) |

**Engineering Notes [C].** Per `UX-012B` §9: *"Reuse rules: Decision Workspace (invalidation conditions, Section 9). Dashboard (invalidation signal)."*

**Anti-Patterns [C].** Do not permit Atlas to initiate the "new reasoning process" `UX-012` §26 requires on the Investor's behalf — that act remains the Investor's own, per `UX-000` UXD-R-048.

---

### 7.4 Implementation Follow-up

**Purpose [C].** Tracks whether the Implementation Intent from a Recorded Decision was executed. Per `UX-012` §26: *"Tracks whether the Implementation Intent from a Recorded Decision was executed."*

**Semantic Meaning [C].** Per `UX-012B` §9: *"Represents an outstanding implementation action linked to a recorded decision — a reminder that execution is pending."*

**Product Correspondence [C].** Tracks execution of the already-governed `implementationIntent` field `UX-013C` §7.2 specifies within Final Decision Card. Asserts no independent Product meaning.

**Ownership [C].** The underlying Implementation Intent is Investor-owned. Follow-up itself is Atlas-performed surfacing; per `UX-012B` §9, the Investor acknowledges or completes it.

**Composition [C].** Component (not composite — does not own sub-components with independent state).

**Documentary note [IR].** `UX-012` §26 states Implementation Follow-up's own states as *"pending, confirmed, modified, cancelled."* `UX-012B` §9 instead states *"Status (Pending, In Progress, Complete)."* These are not identical vocabularies (four states vs. three; "confirmed"/"modified"/"cancelled" do not map one-to-one onto "In Progress"/"Complete"). This document follows `UX-012B` §9 as its primary source, consistent with its own practice throughout, while disclosing `UX-012` §26's own distinct four-state list rather than silently discarding it. Reconciling the two is a future `UX-012`-family correction, outside this document's own authority.

**States [C/IR]** — per the Documentary note above: Pending, In Progress, Complete (`UX-012B` §9, primary). `UX-012` §26's own alternative list (pending, confirmed, modified, cancelled) is disclosed, not adopted.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `linkedDecisionId` | string | — | Yes | |
| `actionDescription` | string | — | Yes | Implementation action description, per `UX-012B` §9 |
| `status` | `'pending' \| 'in-progress' \| 'complete'` | `'pending'` | Yes | Per `UX-012B` §9's own primary list |

**Interaction [C].** Per `UX-012B` §9: *"Acknowledging the follow-up marks it as seen. Completing it transitions the linked decision's implementation state to Complete."*

**Accessibility [IR].** Status communicated by text label, consistent with `UX-012A` §15.

**Responsive Behaviour [IR].** Consistent with Monitoring Condition's own responsive rule (§7.1, above).

**Token Mapping [IR]**, reusing `UX-012D` §3's own `Decision` token group for the linked implementation-state text, since no dedicated Implementation Follow-up token was found named in `UX-012D`:

| Visual Property | Token |
|---|---|
| Action description text | `type.decision.statement` (existing, `UX-012D` §3, reused) |

**Engineering Notes [C].** Per `UX-012B` §9: *"Reuse rules: Dashboard (implementation follow-up signal). Decision Workspace (implementation section state)."*

**Anti-Patterns [C].** Do not permit Implementation Follow-up's own "Complete" transition to occur without an Investor act, per `UX-012B` §9's own "Completing it transitions..." framing, which names the action as something the user does, not Atlas.

---

### 7.5 Scheduled Review

**Purpose [C].** A time-based review trigger defined at Decision time. Per `UX-012` §26: *"A time-based review trigger defined at Decision time."*

**Semantic Meaning [C].** Per `UX-012B` §9: *"A time-based review trigger — a future date at which Atlas will surface the associated decision for review regardless of condition-based triggers."*

**Product Correspondence [C].** Surfaces the already-governed Review Condition field (`UX-013C` §7.2) on a time basis rather than a threshold basis. Where it leads to a formal Decision Review, the same `APS-004` LR-R-097 correspondence stated for Review Trigger (§7.2, above) applies identically.

**Ownership [C].** Investor-established at Decision time (`UX-012` §26: *"Reuse: Decision Workspace (establishment)"*); Atlas-performed surfacing at the scheduled time.

**Composition [C].** Component (not composite).

**States [C].** `UX-012B` §9's own explicit list is used, since `UX-012` §26 does not independently specify states for this component (no contradiction, only differing detail): *"Upcoming (more than two weeks away — quiet), Due Soon (within two weeks — amber treatment), Overdue (past the scheduled date without completion — red treatment)."*

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `linkedDecisionId` | string | — | Yes | |
| `reviewDate` | timestamp | — | Yes | The scheduled review date |
| `reviewType` | string | — | Yes | e.g. "Annual review," "Six-month check-in," per `UX-012B` §9 |
| `status` | `'upcoming' \| 'due-soon' \| 'overdue'` | `'upcoming'` | Yes | Per `UX-012B` §9 |

**Interaction [C].** Per `UX-012` §26: *"Behavior: surfaces in the Dashboard at the scheduled time as a Review Trigger."*

**Accessibility [IR].** Status (Upcoming/Due Soon/Overdue) communicated by text label in addition to amber/red visual treatment, never by color alone, consistent with `UX-012A` §15.

**Responsive Behaviour [IR].** Consistent with Monitoring Condition's own responsive rule (§7.1, above).

**Token Mapping [C]**, reusing `UX-012D` §3's own `Monitoring` token group (§7.1, above) for Due Soon (amber) and extending toward the general semantic red accent for Overdue, consistent with Invalidation Trigger's own token treatment (§7.3, above):

| Visual Property | Token |
|---|---|
| Due Soon state | `color.semantic.amber` |
| Overdue state | Restrained red variant of the general semantic accent color group |

**Engineering Notes [C].** Per `UX-012B` §9: *"Reuse rules: Decision Workspace (review plan). Dashboard (upcoming review signal)."*

**Anti-Patterns [C].** Do not permit Scheduled Review to silently resolve or dismiss itself without surfacing to the Investor at the scheduled time — its own defining purpose is that Atlas surfaces it *"regardless of condition-based triggers"* (`UX-012B` §9).

---

## 8. Cross-Component Monitoring Behaviour

All five components above share a common pattern, traced consistently across `UX-012` §26 and `UX-012B` §9: each is Investor-established (directly, or Atlas-suggested and Investor-confirmed) at or after Decision-recording time; each is Atlas-operated for ongoing observation and surfacing; and none is permitted, anywhere in either source, to autonomously resolve, dismiss, acknowledge, or initiate a subsequent Investor act (acknowledgment, initiating a new reasoning process, completing a follow-up) on the Investor's own behalf — consistent with `UX-000` UXD-R-048's own general rule, applied identically to all five. Two components (Review Trigger, Implementation Follow-up) carry a disclosed, unresolved state-vocabulary discrepancy between `UX-012` §26 and `UX-012B` §9; no other cross-component inconsistency was found.

## 9. Deferred

The following constructs, named in `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own Monitoring-category account, are explicitly **not** specified in this document. Each is named here, with the exact reason for deferral, per `ADR-001` Governance Rule 5.

- **`MonitoringTrigger`** (as a construct independent of Review Trigger) — the interim note's own account lists `MonitoringTrigger` ("Event notification: a Monitoring Condition produced a state change") and `ReviewTrigger` ("Review initiation: formal re-examination is warranted") as two separate components. `UX-012`/`UX-012B` name only one component for this purpose — Review Trigger (§7.2, above), which already covers threshold-crossing notification as part of its own Monitoring-Condition-extension model. The interim note's own two-component split is not independently supported by `UX-012`/`UX-012B` and is not adopted here.
- **`Review Summary`** and **`Review Outcome`** — trace only to the interim note's own **[U]** account. No `UX-012`/`UX-012B` Monitoring-tier component by either name exists. The closest existing correspondence is `UX-012B` §8's own **Decision Review** component ("The formal re-examination of a prior Decision... Output: Review Conclusion"), which that document places under its own Decision Components, not Monitoring Components — and which was not itself authored in `UX-013C`. This cross-tier gap is disclosed here, not resolved; it is a candidate for `UX-013C`'s own future extension, not for this document.
- **`Implementation Plan`** — traces only to the interim note's own **[U]** account (`steps[], dependencies[], timing, owner`). No `UX-012`/`UX-012B` component by this name exists; its own declared anatomy goes materially beyond the already-canonical Implementation Summary/Implementation Intent (a brief description, per `UX-012` §23 and `UX-013C` §7.2's own `implementationIntent` field).
- **`Implementation Status`** — traces only to the interim note's own **[U]** account. Its own stated purpose ("Current implementation progress") substantially overlaps the already-canonical Implementation Follow-up (§7.4, above). No `UX-012`/`UX-012B` component separately named "Implementation Status" exists; adopting it as a distinct component here would risk an unjustified duplication.
- **`Outcome Tracking`** — traces only to the interim note's own **[U]** account. Overlaps `Decision Outcome`, already deferred from `UX-013C` (`UX-013C` §9) for the identical reason: no `UX-012`/`UX-012B` component by this name exists.
- **`Timeline Entry`** — the interim note's own taxonomy places this construct under its **Historical**, not Monitoring, tier. `UX-012B` §10 already defines a canonical **Historical Timeline Entry** component ("A single entry in a chronological timeline of historical events for a subject"), which is Historical-tier, not Monitoring-tier, and was not authored in `UX-013C` either. It is out of this document's own scope; a future Historical-tier authoring phase is the correct place for it.

## 10. Out of Scope

Decision-tier components (Final Decision Card, Proposed Decision, Historical Decision, Decision Summary, Decision History, Decision Amendment) — fully specified in `UX-013C`. This document cross-references Final Decision Card's own `reviewCondition` and `invalidationCondition` fields (§7.2, §7.3, §7.5, above) as the content each relevant Monitoring component watches; it does not restate or redefine them.

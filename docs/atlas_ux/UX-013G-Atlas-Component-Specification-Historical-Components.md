# UX-013G — Atlas Component Specification: Historical Components

**Phase 1 — Canonical Historical Architecture.** Governing references: `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md`; `UX-012B-Atlas-Design-System-Components-Reusable-Patterns.md`; `UX-000-Atlas-UX-Doctrine.md` (RC v1.0); `ADR-002-Critical-UX-Architecture-Resolutions.md`; `UX-013C-Atlas-Component-Specification-Decision-Components.md` (Decision Review, Historical Decision cross-reference).

**Status: Canonical (Phase 1 — Historical Components only).** This document specifies, in production-ready detail, four of the five Historical-tier components already fully supported by committed, canonical documentary evidence — `UX-012` §27 and `UX-012B` §10 directly. **The fifth, Historical Decision, is classified and placed within this tier (§6, §7.2) but is not independently re-specified here — its controlling implementation contract remains solely `UX-013C` §7.3**, per the corrected Atlas UX Architecture Historical Tier Targeted Consistency Corrections task (2026-08-02), which removed an earlier, duplicated full restatement to eliminate a dual-maintenance risk. This document is genuinely, honestly authored on 2026-08-02, citing only documents that exist and are checkable at the time of writing, following the identical process `UX-013A` through `UX-013D` themselves used, per `ADR-001-Missing-Source-Volume-Governance.md`'s own Governance Rule 4 and Option B. It does not reconstruct, does not claim descent from, and is not a replacement for `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own account of an absent Historical-tier volume — that account remains its own document's own separate, `[U]` Unconfirmed record. Where this document's own Historical-tier scope overlaps that account, this document supersedes it for every component specified below; it does not supersede the interim note's own Decision, Monitoring, AI Collaboration, or domain-specific Metadata content, which remains entirely outside this document's own Phase 1 scope.

**Provenance convention used in this document**, identical to `UX-013C`'s and `UX-013D`'s own: **[C]** (Canonical — traced directly to `UX-012`, `UX-012B`, `UX-000`, an Accepted UX ADR, or a directly-cited Product Architecture document's own committed text) and **[IR]** (Implementation Refinement — anatomy, property, or token detail newly authored here, required to make a canonical purpose production-ready, and not itself asserting new meaning). No claim in this document is tagged **[U]** — anything that would require such a tag is moved to Section 9, Deferred.

---

## 1. Purpose

This document specifies every Atlas Historical-tier component whose architecture is already settled by `UX-012` §27 and `UX-012B` §10, in the same production-ready detail `UX-013A` through `UX-013D` already provide for their own tiers — with one disclosed exception: Historical Decision (§7.2) is classified and placed within this tier but is not independently re-specified, since its controlling implementation contract already exists, fully audited, at `UX-013C` §7.3. It closes part of the documentary gap `ADR-001` and `ADR-002` C-05 identified, for the Historical tier specifically, through genuine new authorship rather than reconstruction.

This document does not specify `Review Summary`, `Review Outcome`, `Decision Outcome`, `DecisionCard`, `Decision Supersession`, or `Decision Rationale Reference` — each remains Deferred exactly where `UX-013C` §9 and `UX-013D` §9 already left it; this document does not reopen, adopt, or reconcile any of them, and cross-references those sections rather than restating their own reasoning. It does not specify Historical Comparison (`UX-012B` §7, a Comparison-tier component) or Historical Indicator (`UX-013A`, a Foundation-tier component) — both are named where relevant, never restated. See Section 9, Deferred, and Section 10, Out of Scope.

## 2. Authority Chain

Atlas Core Architecture Doctrine (Final) → Atlas Product Doctrine and Product Concept Taxonomy, `APP-000`/`APP-001` (Normative Product) → `APS-001` through `APS-005` (Normative Product, the sole authority for each accepted concept's own normative behavior) → `UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0 (governing UX doctrine, per its own `UXD-R-097`) → `ADR-002`, `ADR-003` (Accepted, Normative UX, subordinate to `UX-000`, authoritative within their own stated scope) → `UX-012`/`UX-012B`/`UX-012D` (Normative UX, the Design System's own semantic authority) → `UX-013C` (peer, Decision-tier realization; the operative source for Historical Decision's own architecture) → `UX-013B` (peer, Reasoning-tier realization; the operative source for Review Conclusion, presented — never restated — within Historical Review) → this document (subordinate component-level realization for the Historical tier).

This document does not amend `UX-000`. It does not amend `ADR-001` through `ADR-004`. It does not redefine, narrow, or extend any Product Concept, Product Principle, or Core Domain Object. It does not introduce new terminology — every component name, state name, and property concept below is traced to `UX-012` or `UX-012B`'s own committed text.

## 3. Relationship to UX-012

`UX-012` (and `UX-012B`, its own companion component specification) remain the semantic authority for every component this document specifies. This document adds implementation-ready anatomy, properties, states, interaction, accessibility, and token detail; it does not redefine any component's purpose or meaning. Where this document's own detail and `UX-012`/`UX-012B`'s own text could be read to diverge, `UX-012`/`UX-012B` govern. This document does not silently absorb or replace `UX-012`; `UX-012` §27 and `UX-012B` §10 remain fully valid, unedited, and authoritative in their own right.

**One component named below (Historical Decision) is governed by the `UX-012` §27-vs-`UX-012B` §10 documentary note `UX-013C` §7.3 already states — inherited here by reference, not restated.** `UX-012` §27's own required-content claim for Historical Decision ("all six Final Decision Card fields, recorded timestamp, and full reasoning provenance") is broader than `UX-012B` §10's own narrower claim ("All Decision Summary fields. The recording date. The decision's current status"). `UX-013C` §7.3 already discloses this discrepancy and follows `UX-012B` §10 as its primary source; this document does not restate that disclosure a second time, per Section 5's own single-source correction, below — it points to `UX-013C` §7.3 as the place that disclosure lives.

## 4. Relationship to UX-013F

`UX-013F-Foundation-Reasoning-Component-Library-Assembly.md` is this document's peer, canonical for the Foundation and Reasoning tiers and for the cross-cutting infrastructure every tier depends on (Metadata & Provenance, Status & Feedback, Loading & Availability, Overlay & Dialog, Notification, and the shared property/state/composition/dependency/classification models). This document does not restate any of that cross-cutting content; it references it by name — `StatusBadge`, `MetadataBlock` — exactly as `UX-013C` and `UX-013D` already do. This document adopts `UX-013F`'s own ten-type classification model (`UX-013F` § 2, Canonical Classification Model: Primitive, Component, Composite Component, Action, Behavior, State, Variant, Composed Pattern, Semantic Concept, Deferred Item) to classify each component below, without redefining any classification type.

**Documentary note [IR].** `UX-013F`'s own Ambiguous Case Resolutions table (§2) contains one entry — "HistoricalDecision | State + Variant of DecisionCard" — that reflects the same unconfirmed `DecisionCard` unification model `UX-013C` §9 already found genuinely divergent from `UX-013C`'s own canonical Final Decision Card and declined to adopt. This document follows `UX-013C` §7.3's own, already-settled classification (Historical Decision as its own Component, not a state/variant of an unadopted `DecisionCard`) and does not reopen that finding.

## 5. Historical Architecture Overview

The Historical tier renders permanently immutable presentations of already-governed content originating in every other tier — Decision (Historical Decision), formal review (Historical Review), Reasoning (Historical Assumption) — anchored by one shared base, Historical Record, and indexed by one chronological pointer component, Historical Timeline Entry. Five components are canonical and fully specified below, all traced directly to `UX-012` §27 and `UX-012B` §10.

**Historical Decision's own single-source correction, applied here.** `UX-013C` §7.3 already specifies Historical Decision as a fully canonical, independently verified component, and `UX-013D` §10 already cross-references it there ("Decision-tier components... fully specified in `UX-013C`"). An earlier draft of this document duplicated that specification in full at Section 7.2, below, creating a genuine dual-maintenance risk — two independently-editable copies of the identical architecture that could silently drift apart. That duplication has been removed, per the Atlas UX Architecture Historical Tier Targeted Consistency Corrections task (2026-08-02). **`UX-013C` §7.3 is, and remains, the sole controlling specification** for Historical Decision's own purpose, semantic meaning, product correspondence, ownership, composition, states, properties, interaction, accessibility, responsive behaviour, token mapping, engineering notes, and anti-patterns. This document's own Section 7.2, below, is now a thin cross-reference — not a specification — that classifies Historical Decision within the Historical tier and points to `UX-013C` §7.3, without restating its contract. This is a genuinely different relationship from Decision Review (`UX-013C` §7.7) and Review Conclusion (`UX-013B` §1), which remain two independently-specified components that happen to present overlapping underlying facts from different tier perspectives — Historical Decision has only one specification, located at `UX-013C` §7.3, and this document does not offer a second one.

Several further Historical-adjacent constructs referenced elsewhere in the corpus — `Review Summary`, `Review Outcome`, `Decision Outcome`, `DecisionCard`, `Decision Supersession`, `Decision Rationale Reference`, Historical Comparison, `Historical Monitoring Record` — are not specified in this document. Each is named, with its own exact reason, in Section 9, Deferred, or Section 10, Out of Scope.

## 6. Canonical Component Inventory

| Component | Classification | Status | Source |
|---|---|---|---|
| Historical Record | Component | **[C]** Canonical | `UX-012` §27, `UX-012B` §10 |
| Historical Decision | Component | **[C]** Canonical — cross-reference only | `UX-013C` §7.3 (sole controlling specification) |
| Historical Review | Component | **[C]** Canonical | `UX-012` §27, `UX-012B` §10 |
| Historical Assumption | Component | **[C]** Canonical | `UX-012B` §10 |
| Historical Timeline Entry | Component | **[C]** Canonical | `UX-012` §27, `UX-012B` §10 |

Not specified in this document — see Section 9: `Review Summary`, `Review Outcome`, `Decision Outcome`, `DecisionCard`, `Decision Supersession`, `Decision Rationale Reference`, `Historical Monitoring Record`. Out of this document's own scope entirely — see Section 10: Historical Comparison (owned by a future Comparison-tier document, `UX-012B` §7), Historical Indicator (owned by `UX-013A`).

---

## 7. Component Specifications

### 7.1 Historical Record

**Purpose [C].** The base component for any immutable recorded content. Per `UX-012` §27: *"The base component for any immutable recorded content."* Per `UX-012B` §10: *"The base component for any prior state presented within a current context — the visual treatment that distinguishes past from present."*

**Semantic Meaning [C].** Every other Historical component in this document extends Historical Record — it is the shared foundation, not an independent presentation in its own right. Per `UX-012B` §10: *"Visual treatment: Tertiary text color. Reduced opacity surface (subtle background distinction from surrounding current content). Timestamp and version indicator in metadata scale at the top. All content is read-only."*

**Product Correspondence [C].** No independent Product meaning. Historical immutability is governed at the Product layer by `APS-002` IR-R-027/IR-R-059 (Superseded Content preservation) and restated at the UX layer by `UX-000` UXP-007: *"Historical Meaning Is Never Silently Rewritten... A historical presentation reflects what was actually recorded at the time it was recorded; a later correction is additive, never a silent rewrite."* This component asserts no independent Product meaning beyond presenting that already-governed immutability.

**Ownership [C].** None asserted independently — the base component presents whatever content the underlying record's own author already owns; Historical Record itself performs no act.

**Composition [C].** Component (per `UX-013F`'s own classification model) — the shared base every other component in this document extends; it does not itself compose other components.

**States [C].** default, selected, expanded, compared — per `UX-012` §27: *"States: default, selected, expanded, compared."*

**Properties [IR]** (named here for the first time as typed properties, following the fields `UX-012B` §10 already names in prose):

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `recordId` | string | — | Yes | |
| `recordType` | string | — | Yes | Free-text label, per `UX-012B` §10 examples: "PRIOR DECISION," "PRIOR CONCLUSION" |
| `timestamp` | timestamp | — | Yes | |
| `content` | object | — | Yes | The prior content at its original level of detail, per `UX-012B` §10; shape is defined by the extending component |
| `state` | `'default' \| 'selected' \| 'expanded' \| 'compared'` | `'default'` | Yes | Per `UX-012` §27 |
| `isImmutable` | boolean | `true` | Yes | Always true |

**Interaction [C].** *"Expand/collapse only. 'Compare with current →' link when comparison is relevant"* (`UX-012B` §10). All editing controls disabled; historical locking is absolute.

**Accessibility [C].** Per `UX-012A` §15's own non-color-communication requirement: historical status is identifiable through both a text label and a visual/opacity treatment, never opacity alone. Per `UX-012A` §15's own accessible-authorship identification: historical content is identifiable through both visual means (label, typographic weight, position) and non-visual means (ARIA label or role) — the screen-reader experience distinguishes historical from current content without relying on visual rendering alone.

**Responsive Behaviour [C].** Per `UX-012` §73: *"Historical Records: Overlay on desktop and tablet. Full-screen on mobile."*

**Token Mapping [C]**, using `UX-012D` §3's own already-named `Historical Content` semantic token group directly:

| Visual Property | Token |
|---|---|
| Historical text color | `color.text.historical` |
| Historical surface | `surface.historical` |
| Timestamp | `type.metadata.timestamp` |

**Engineering Notes [C].** All four extending components below (Historical Decision, Historical Review, Historical Assumption) inherit this base's own immutability, token treatment, and state model; none introduces an exception. Historical Timeline Entry does not extend Historical Record directly — it is a compact pointer to one of the other four — and is specified independently, below.

**Anti-Patterns [C].** Do not permit any edit path for Historical Record content, under any circumstance. Do not present Historical Record content as if it were current.

---

### 7.2 Historical Decision

**Cross-reference entry — not a component specification.** This entry intentionally does not follow the thirteen-subsection format used for the other four components in this document (§7.1, §7.3–§7.5). Historical Decision is a canonical Historical-tier component, per `UX-012B` §10: *"Extends Historical Record and Decision Summary. The embedded representation of a prior decision in historical context."* **Its controlling, sole implementation contract — Purpose, Semantic Meaning, Product Correspondence, Ownership, Composition, States, Properties, Interaction, Accessibility, Responsive Behaviour, Token Mapping, Engineering Notes, and Anti-Patterns — is `UX-013C` §7.3.** This document does not restate that contract and does not maintain a second, independently-editable copy of it.

**Why it is listed here.** Historical Decision is genuinely a Historical-tier component under `UX-012` §27's and `UX-012B` §10's own taxonomy, and belongs in this document's own Canonical Component Inventory (§6) and Historical Architecture Overview (§5) for that reason — omitting it entirely would leave this document's own inventory incomplete. `UX-013C` §7.3 remains its operative home because that is where it was first specified and independently audited; `UX-013D` §10 already cross-references it there on the identical basis (*"Decision-tier components... — fully specified in `UX-013C`"*).

**Governing rule.** Any future change to Historical Decision's own anatomy, properties, states, interaction, accessibility, responsive behaviour, token mapping, or engineering guidance MUST be made in `UX-013C` §7.3. This entry is updated only if Historical Decision's own tier placement itself changes — never to reintroduce a duplicated implementation contract.

---

### 7.3 Historical Review

**Purpose [C].** The prior review record shown in historical context. Per `UX-012B` §10: *"Extends Historical Record. The prior review record shown in historical context."* Per `UX-012` §27: *"A Historical Record of a completed Review — Review Conclusion, comparison with original Decision, reviewer notes."*

**Semantic Meaning [C].** Historical Review is the historicized presentation of a completed Decision Review (`UX-013C` §7.7), once that component reaches its own `Complete` or `Superseded` state — restated from `UX-013C` §8's own Cross-Component note: *"Once Complete or Superseded, Decision Review becomes eligible for presentation via the Historical Review component `UX-012B` §10 separately names."* Historical Review references Decision Review; it does not reference, and never presents, `Review Summary` or `Review Outcome` — neither has independent canonical anatomy in `UX-012`/`UX-012B`, per `UX-013C` §9 and `UX-013D` §9, both carried forward here, not reopened.

**Documentary note [IR].** `UX-012` §27's own required-content claim ("Review Conclusion, comparison with original Decision, reviewer notes") and `UX-012B` §10's own claim ("Review verdict. Key finding. Review date. The previous state of the decision at review time") are compatible but not identically worded — the same pattern already disclosed for Historical Decision, above. This document follows `UX-012B` §10 as its primary source, for the identical consistency reason already stated in Section 3. The discrepancy is disclosed here, not resolved.

**Product Correspondence [C].** Historical Review presents the already-settled facts of a Decision Review (`UX-013C` §7.7) — itself a UX/workflow artifact, not a Product Concept, per `APP-001` §3.6's own rejection of "Review" as independent Product Concept. Historical Review MAY present a linked Review Conclusion only where the underlying Decision Review's own `reviewConclusionId` was genuinely populated — meaning a genuine, Investor-initiated Learning Act occurred, per `UX-000` UXD-R-071 item 4, UXD-R-086, and `APS-004` LR-R-147/LRINV-018. Historical Review MAY present a linked Outcome only where the underlying Decision Review's own `outcomeId` was genuinely populated, per `APS-005` OR-R-085. **Neither presentation is mandatory** — a Historical Review presenting neither is not defective; it accurately reflects that no Learning Act or Outcome-recording act occurred in connection with that review. Historical Review does not own, contain, or compute either — per `APS-005` OR-R-086 (*"Decision Review SHALL NOT be treated as identical to Outcome, nor as an architectural container of Outcome"*), applied identically to Historical Review as its own historicized presentation, and by the identical reasoning `APS-004` LR-R-098 already establishes for Learning. Historical Review never characterizes Decision Quality from any presented Outcome, per `APS-005` OR-R-016/OR-R-072/OR-R-093 and ORINV-008/ORINV-016, restated at the UX layer by `UX-000` UXD-R-077–082.

**Ownership [C].** None asserted independently. Historical Review presents Decision Review (`UX-013C` §7.7), which the Investor owns per that component's own Ownership section. Where present, a linked Review Conclusion presents a Learning Result the Investor owns via a genuine Learning Act, per `APS-004` LR-R-147. Where present, a linked Outcome presents a fact whose *recording act* the Investor owns, per `APS-005` OR-R-098, while the Outcome itself remains owned by neither party, per OR-R-006/OR-R-042. Historical Review itself performs no act, decides nothing, records nothing, approves nothing, learns nothing, concludes nothing, and supersedes nothing — it is a permanently locked, read-only presentation of facts already settled elsewhere.

**Composition [C].** Component, extending Historical Record (`UX-012B` §10) — a composition of the already-specified base (§7.1, above) plus Historical Review's own named fields (review verdict, key finding, review date, prior decision state). Two further facts MAY be associated, and both are modeled as optional, external references, never as owned or embedded sub-objects, mirroring `UX-013C` §7.7's own Composition section exactly: a linked Review Conclusion (`UX-013B` §1), present only where the underlying Decision Review's own precondition was independently satisfied; and a linked Outcome (`APS-005`-governed), present only where independently recorded per OR-R-085.

**States [IR].** `UX-012B` §10 does not itself enumerate a distinct states list for Historical Review beyond the shared Historical Record state model (§7.1, above: default, selected, expanded, compared). Applied here by direct inheritance from Historical Record, per `UX-012B` §10's own "Extends Historical Record" framing — no new state is invented. The underlying Decision Review's own `status` (`'complete' \| 'superseded'`, `UX-013C` §7.7) is presented as read-only content within Historical Review, not as an independent state of Historical Review itself.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `reviewId` | string | — | Yes | References the underlying, completed Decision Review (`UX-013C` §7.7) |
| `originalDecisionId` | string | — | Yes | The Decision that was reviewed |
| `verdict` | `'THESIS_VALID' \| 'THESIS_WEAKENED' \| 'ASSUMPTION_BROKEN' \| 'DECISION_SUPERSEDED'` | — | Yes | Per `UX-012B` §10: "Review verdict," carried forward from `UX-013C` §7.7's own identical property |
| `keyFinding` | string | — | Yes | Per `UX-012B` §10: "Key finding" |
| `reviewDate` | timestamp | — | Yes | |
| `priorDecisionState` | object | — | Yes | Per `UX-012B` §10: "The previous state of the decision at review time" |
| `reviewConclusionId` | string \| null | `null` | No | External reference only, per Composition, above. Populated only if genuinely present on the underlying Decision Review |
| `outcomeId` | string \| null | `null` | No | External reference only, per Composition, above. Populated only if genuinely present on the underlying Decision Review |
| `resultingChangeRef` | string \| null | `null` | No | Per `UX-012B` §10: "when the review produced an amendment or superseding decision" |

**Interaction [C].** *"Expand to show the full review record. 'View resulting changes →' when the review produced an amendment or superseding decision"* (`UX-012B` §10). Where `reviewConclusionId` is populated, the linked Review Conclusion (`UX-013B` §1) is inspectable; where absent, no Review Conclusion affordance appears — its absence is not an error state. Where `outcomeId` is populated, the linked Outcome is inspectable; where absent, no Outcome affordance appears. All editing controls disabled; historical locking is absolute, per Historical Record's own inherited discipline.

**Accessibility [C].** Verdict and historical status are communicated through both text label and color, never color alone, per `UX-012A` §15's own non-color-communication requirement, applied identically to Decision Review's own analogous rule (`UX-013C` §7.7). The presence or absence of a linked Review Conclusion or Outcome is programmatically available via ARIA attributes, not conveyed by visual treatment alone, consistent with `UX-012A` §15's own accessible-authorship identification pattern.

**Responsive Behaviour [C].** Per `UX-012` §73: *"Historical Records: Overlay on desktop and tablet. Full-screen on mobile."*

**Token Mapping [C]**, using `UX-012D` §3's own already-named `Historical Content` semantic token group:

| Visual Property | Token |
|---|---|
| Historical text color | `color.text.historical` |
| Historical surface | `surface.historical` |
| Timestamp | `type.metadata.timestamp` |

**Engineering Notes [C].** Historical Review is not Product Learning, and its presentation of a linked Review Conclusion does not itself constitute or re-perform the underlying Learning Act — it is a read-only reflection of a fact already settled at Decision Review's own completion time, per `UX-000` UXD-R-084/086. Historical Review never fabricates a Review Conclusion or Outcome presentation where the underlying Decision Review carries none, per `APS-004` LR-F-012 and `APS-005` OR-R-097 (*"Atlas SHALL NOT fabricate an Outcome where none has been recorded"*), applied identically here. `Review Summary` and `Review Outcome` remain Deferred, per Section 9, below — Historical Review's own anatomy already covers every fact either name was claimed to add for the historical case.

**Anti-Patterns [C].** Do not permit any edit path for Historical Review content, under any circumstance. Do not present a Historical Review as if it were a live, in-progress Decision Review. Do not populate `reviewConclusionId` on a Historical Review that does not accurately reflect the underlying Decision Review's own genuinely-satisfied Learning-Act precondition (`UX-000` UXD-R-071 item 4). Do not embed Outcome content as an owned or nested field — it is a reference only (`APS-005` OR-R-086). Do not use a presented Outcome, or its favorability, as a Decision Quality verdict on the original Decision (`APS-005` OR-R-016/072/093, ORINV-008/016). Do not treat the absence of a linked Review Conclusion or Outcome as an error, omission, or incomplete state — both are genuinely optional, per this document's own governing instruction. Do not implement `Review Summary` or `Review Outcome` as separate, independently canonical components, or as an alternate name for this component.

---

### 7.4 Historical Assumption

**Purpose [C].** A prior assumption state shown in historical context. Per `UX-012B` §10: *"Extends Historical Record. A prior assumption state shown in historical context — when an assumption has been updated or broken and the user wants to understand the original state."* Per `UX-012` §27: *"A Historical Record of an Assumption as it existed at a prior point in time — used for comparison during a Review."*

**Semantic Meaning [C].** Presents an immutable snapshot of an Assumption (`UX-012` §23, `UX-012B` §6) at a prior point in time — distinct from the live, currently-editable Assumption it may be compared against.

**Product Correspondence [C].** Assumption is a UX presentation category over already-governed Investor Reasoning content (`APS-002`) — per `UX-012` §23's own definition, *"the conditions on which the current reasoning depends."* This component asserts no independent Product Concept for Assumption; it presents already-governed Investor Reasoning content in its historically preserved form, governed by `APS-002` IR-R-027/IR-R-059 (Superseded Content preservation) and `UX-000` UXP-007.

**Ownership [C].** None asserted independently — presents an assumption statement the Investor already owns as part of their own Investor Reasoning.

**Composition [C].** Component, extending Historical Record (`UX-012B` §10) — a composition of the already-specified base (§7.1, above) plus this component's own two named fields.

**States [IR].** No distinct states list beyond the shared Historical Record state model (§7.1, above), per `UX-012B` §10's own "Extends Historical Record" framing — no new state is invented. The `statusAtRecording` property, below, presents the Assumption's own status value at the time of recording as read-only content, not as an independent state of Historical Assumption itself.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `assumptionId` | string | — | Yes | |
| `statement` | string | — | Yes | Per `UX-012B` §10: "The original assumption statement" |
| `statusAtRecording` | `'Holding' \| 'Under Review' \| 'Weakening' \| 'Broken'` | — | Yes | Per `UX-012B` §10: "The status at the time of recording"; enum values per `UX-012` §23's own Assumption status model |
| `lastConfirmedDate` | timestamp | — | Yes | Per `UX-012B` §10: "The date the assumption was last confirmed" |

**Interaction [C].** Expand/collapse, per the inherited Historical Record interaction model (§7.1, above). *"Used for comparison during a Review"* (`UX-012` §27) — MAY appear alongside the corresponding live Assumption within Historical Comparison (`UX-012B` §7, out of this document's own scope, cross-referenced only). All editing controls disabled.

**Accessibility [C].** Status at recording is communicated through both text label and color, never color alone, per `UX-012A` §15's own non-color-communication requirement, consistent with the live Assumption component's own identical rule (`UX-012B` §6).

**Responsive Behaviour [C].** Per `UX-012` §73: *"Historical Records: Overlay on desktop and tablet. Full-screen on mobile."*

**Token Mapping [C]**, using `UX-012D` §3's own already-named `Historical Content` semantic token group:

| Visual Property | Token |
|---|---|
| Historical text color | `color.text.historical` |
| Historical surface | `surface.historical` |
| Timestamp | `type.metadata.timestamp` |

**Engineering Notes [C].** Historical Assumption's own purpose is explicitly comparative (`UX-012` §27: "used for comparison during a Review") — it is expected to be rendered alongside its live counterpart via Historical Comparison, not in isolation, though isolated presentation (e.g., within Historical Timeline Entry's own expansion target) is not prohibited.

**Anti-Patterns [C].** Do not permit any edit path for Historical Assumption content, under any circumstance. Do not present a Historical Assumption as if it were the current, live Assumption.

---

### 7.5 Historical Timeline Entry

**Purpose [C].** A compact representation of one event in a decision's history. Per `UX-012B` §10: *"A compact representation of one event in a decision's history — suitable for display in a chronological timeline or version history panel."* Per `UX-012` §27: *"A single entry in a chronological timeline of historical events for a subject."*

**Semantic Meaning [C].** Unlike the other four components in this document, Historical Timeline Entry does not itself extend Historical Record — `UX-012B` §10 states no "Extends" relationship for it. It is a compact pointer that, on interaction, opens the relevant Historical component; it does not itself present the full historical content.

**Product Correspondence [C].** No independent Product meaning — a pure navigational and chronological presentation artifact over already-governed content presented elsewhere.

**Ownership [C].** None asserted independently — presents a pointer to content already owned elsewhere, per the owning component's own Ownership section.

**Composition [C].** Component (per `UX-013F`'s own classification model) — standalone, referencing another Historical component by identifier; it does not compose that component's own content.

**States [IR].** No states list is given by either source. None is invented here, consistent with this document's own governing instruction not to invent lifecycle content beyond what `UX-012`/`UX-012B` state.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `entryId` | string | — | Yes | |
| `eventType` | `'Decision Recorded' \| 'Amended' \| 'Review Completed' \| 'Superseded' \| 'Monitoring Triggered'` | — | Yes | Per `UX-012B` §10's own exact event-type list |
| `timestamp` | timestamp | — | Yes | |
| `summary` | string | — | Yes | Per `UX-012B` §10: "A one-line summary of the event" |
| `linkedRecordId` | string | — | Yes | Per `UX-012` §27: "link to full Historical Record" |

**Interaction [C].** *"Tapping/clicking expands to the relevant Historical component (Historical Decision, Historical Review, etc.)"* (`UX-012B` §10). Non-interactive beyond this single navigation affordance.

**Accessibility [C].** Event type and date are conveyed through text, never through icon or color alone, per `UX-012A` §15's own non-color-communication requirement. The navigation affordance uses standard link/button semantics with an `aria-label` naming the event type and date.

**Responsive Behaviour [IR].** Full-width entries on mobile, no side-by-side layout, consistent with `UX-012` §73's own general list/catalog responsive rule already applied to Decision History (`UX-013C` §7.5).

**Token Mapping [IR]:**

| Visual Property | Token |
|---|---|
| Entry text | `type.metadata.timestamp` (existing, `UX-012D` §3) |
| Entry row surface | `surface.historical` (existing, `UX-012D` §3, reused since every entry points to historical content) |

**Engineering Notes [C].** Per `UX-012B` §10: *"Reuse rules: Decision History component. Version history panel in Decision Workspace."* Historical Timeline Entry is the shared pointer type Decision History (`UX-013C` §7.5) and a future Decision Workspace version-history panel both compose; this document does not restate Decision History's own specification.

**Anti-Patterns [C].** Do not embed the full content of the target Historical component within Historical Timeline Entry itself — it is a pointer, not a duplicate presentation. Do not permit any edit path.

---

## 8. Cross-Component Historical Behaviour

All five components above share the identical historical-immutability discipline stated in full at §7.1 (Historical Record) and inherited by the other four: reduced opacity (approximately 70% of standard text opacity, per `UX-012` §27), permanently locked (no editing controls, no hover state, no cursor change), timestamp always visible. No component specified in this document permits an exception to this rule. This discipline is governed at the Product layer by `APS-002` IR-R-027/IR-R-059 and restated at the UX layer by `UX-000` UXP-007 — *"a later correction is additive, never a silent rewrite."*

Every Historical presentation reachable from a live Workspace surface is accompanied by the Historical Indicator, per `UX-012` §27: *"Always accompanied by: the Historical Indicator in the Workspace Header."* Historical Indicator is fully specified in `UX-013A` (Foundation tier); this document cross-references it and does not restate it.

Historical Decision, Historical Review, and Historical Assumption each extend Historical Record with their own named fields — Historical Decision's own field set is specified solely at `UX-013C` §7.3, not restated in this document, per §7.2's own cross-reference entry, above. Historical Timeline Entry alone does not extend Historical Record and instead references the other four by identifier. No component in this document owns, contains, or mutates a Learning Result or an Outcome — where either is presented (Historical Review only), it is presented strictly as an optional, external, provenance-preserving reference, per `APS-004` LR-R-098 and `APS-005` OR-R-086, applied identically to their historicized presentation as to their live presentation in `UX-013C` §7.7.

## 9. Deferred

The following constructs are explicitly **not** specified in this document. Each is named here, with the exact reason for deferral, per `ADR-001` Governance Rule 5.

- **`Review Summary`** — remains Deferred, exactly as `UX-013C` §9 and `UX-013D` §9 already establish. Traces only to `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own **[U]** account and the unrelated `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md`'s own uncorroborated claim. No `UX-012`/`UX-012B` component by this name exists, in any tier — including Historical, where the interim note's own taxonomy does not even place it (it places `Review Summary` under Monitoring, not Historical). Historical Review (§7.3, above) already covers every historical-presentation fact either account claims for it. Not adopted here.
- **`Review Outcome`** — remains Deferred, for the identical reason. Beyond lacking anatomy, this name remains structurally disfavored: presenting it as a Review-owned Outcome container would risk exactly what `APS-005` OR-R-086 forbids. Historical Review's own `outcomeId` property (§7.3, above) already models the historical case correctly — an optional, external, provenance-preserving reference, never an owned field. Not adopted here.
- **`Decision Outcome`** — remains Deferred, exactly as `UX-013C` §9 already establishes. Traces only to the interim note's own **[U]** account. No `UX-012`/`UX-012B` component by this name exists in any tier. This document does not reopen `UX-013C` §9's own finding.
- **`DecisionCard`** — remains Deferred, exactly as `UX-013C` §9 already establishes, including its own genuine, unreconciled divergence finding against Final Decision Card. This document's own §4 Documentary note, above, confirms `UX-013F`'s own related "HistoricalDecision as a state/variant of `DecisionCard`" claim is not adopted here either, for the identical reason.
- **`Decision Supersession`** — remains Deferred, exactly as `UX-013C` §9 already establishes. The general "Superseded" status value already appears within Decision Summary, Decision Amendment, and — in this document — Historical Decision's own `status` property; a dedicated cross-decision supersession component remains undocumented.
- **`Decision Rationale Reference`** — remains Deferred, exactly as `UX-013C` §9 already establishes. Traces only to the interim note's own **[U]** account.
- **`Historical Monitoring Record`** — traces only to the unrelated `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md`'s own account ("normalized to `MonitoringCondition` state"). No `UX-012`/`UX-012B` component by this name exists anywhere — confirmed by direct search of both documents' own Historical Components sections (`UX-012` §27, `UX-012B` §10), neither of which names it. Not adopted here.

## 10. Out of Scope

**Historical Comparison** — genuinely documentary-supported (`UX-012B` §7: *"A composed component that presents a Historical Record alongside its current equivalent for direct comparison. See Section 7 — Comparison Components."*), but owned by the Comparison tier, not the Historical tier. No UX-013 document yet specifies the Comparison tier in full; this document cross-references Historical Comparison (§7.4, above) as the mechanism through which Historical Assumption is presented alongside its live counterpart, without restating or redefining it. A future, dedicated Comparison-tier authoring phase is the correct place for it.

**Historical Indicator** — fully specified in `UX-013A` (Foundation tier). This document cross-references it (§8, above) as the Workspace-Header-level signal that accompanies every Historical presentation in this document; it does not restate or redefine it.

**Historical Decision's own full specification** — the sole, controlling specification is `UX-013C` §7.3. This document's own §7.2 is a thin cross-reference, not a restatement, per Section 5, above; it does not supersede, amend, duplicate, or compete with `UX-013C` §7.3.

**`Review Summary`, `Review Outcome`, `Decision Outcome`, `DecisionCard`, `Decision Supersession`, `Decision Rationale Reference`** — each owned by `UX-013C` §9's or `UX-013D` §9's own Deferred disposition, cross-referenced in Section 9, above, not restated or redefined here.

# UX-013E — Atlas Component Specification: AI Collaboration Components

**Phase 1 — Canonical AI Collaboration Architecture.** Governing references: `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md`; `UX-012B-Atlas-Design-System-Components-Reusable-Patterns.md`; `UX-000-Atlas-UX-Doctrine.md` (RC v1.0); `ADR-002-Critical-UX-Architecture-Resolutions.md`; `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`; `UX-013C-Atlas-Component-Specification-Decision-Components.md`; `UX-013D-Atlas-Component-Specification-Monitoring-Components.md`.

**Naming note.** This document's own filename uses "UX-013E" per this task's explicit instruction. This is a distinct, newly-authored, genuinely canonical document, unrelated to and not superseding `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md` — a differently-scoped, pre-existing historical document already superseded, for its own tiers, by `UX-013F` and `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`, per those documents' own Correction Notices. This document does not touch, edit, or alter that pre-existing document in any way, and does not claim its filename.

**Status: Canonical (Phase 1 — AI Collaboration Components only).** This document specifies, in production-ready detail, only the AI Collaboration-tier components already fully supported by committed, canonical documentary evidence — `UX-012` and `UX-012B` directly. It is genuinely, honestly authored on 2026-08-02, citing only documents that exist and are checkable at the time of writing, following the identical process `UX-013B`, `UX-013C`, and `UX-013D` themselves used, per `ADR-001-Missing-Source-Volume-Governance.md`'s own Governance Rule 4 and Option B. It does not reconstruct, does not claim descent from, and is not a replacement for `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own account of an absent `UX-013D` (that document's own AI Collaboration content). That account remains its own document's own separate, `[U]` Unconfirmed record. Where this document's own AI Collaboration-tier scope overlaps that account, this document supersedes it for every component specified below; it does not supersede the interim note's own Decision, Monitoring, or domain-specific Metadata content.

**Provenance convention used in this document**, identical to `UX-013C`'s and `UX-013D`'s own: **[C]** (Canonical — traced directly to `UX-012`, `UX-012B`, `UX-000`, an Accepted UX ADR, or a directly-cited Product Architecture document's own committed text) and **[IR]** (Implementation Refinement — anatomy, property, or token detail newly authored here, required to make a canonical purpose production-ready, and not itself asserting new meaning). No claim in this document is tagged **[U]** — anything that would require such a tag is moved to Section 9, Deferred.

**Correction Notice (Atlas UX Architecture Foundation & Collaboration Token Alignment task — 2026-08-02):** This is a later, additive correction; it does not revise, replace, or reopen the identity or scope stated above. The completed Reasoning Token Architecture Phase 3C: Attribution & Action Text task (2026-08-02) established the canonical Attribution Text mapping — attribution labels use `color.text.secondary`, per `UX-012D` §3's own Canonical Attribution & Action Text Mapping contract — and retired `text.attribution.atlas` as an unsupported name. This document, authored before Phase 3C completed, retained three live references to it. They are now aligned to `color.text.secondary`. Authorship identity (Atlas-origin vs. user-origin) remains communicated by the component's own explicit label and provenance property, not by color alone — this correction changes no AI ownership, authority, or authorship semantics, and no component anatomy, property, state, or accessibility behavior. No new token is introduced.

---

## 1. Purpose

This document specifies every Atlas AI Collaboration-tier component whose architecture is already settled by `UX-012` and `UX-012B`, in the same production-ready detail `UX-013C` and `UX-013D` already provide for the Decision and Monitoring tiers. It closes part of the documentary gap `ADR-001` and `ADR-002` C-05 identified, for the AI Collaboration tier specifically, through genuine new authorship rather than reconstruction.

This document does not specify Decision (see `UX-013C`), Monitoring (see `UX-013D`), or domain-specific Metadata components. Those remain entirely outside this Phase 1 scope.

## 2. Authority Chain

Atlas Core Architecture Doctrine (Final) → `APP-000`/`APP-001` (Normative Product) → `APS-001` through `APS-005` (Normative Product, the sole authority for each accepted concept's own normative behavior) → `UX-000-Atlas-UX-Doctrine.md`, RC v1.0 (governing UX doctrine, per `UXD-R-097`) → `ADR-002`, `ADR-003` (Accepted, Normative UX, subordinate to `UX-000`, authoritative within their own stated scope) → `UX-012`/`UX-012B`/`UX-012C`/`UX-012D` (Normative UX, the Design System's own semantic authority) → `UX-013C`, `UX-013D` (peers, Decision- and Monitoring-tier realization) → this document (subordinate, AI Collaboration-tier realization).

This authority order is never reversed. This document does not amend `UX-000`. It does not amend `ADR-001` through `ADR-004`. It does not redefine, narrow, or extend any Product Concept, Product Principle, or Core Domain Object — specifically, it does not redefine Decision, Reasoning, Learning, Evidence, or Confidence, and it does not introduce any form of AI autonomy beyond what `UX-000` already permits. It does not introduce new terminology — every component name, state name, and property concept below is traced to `UX-012` or `UX-012B`'s own committed text. Where `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own AI Collaboration-category account names a construct or property not independently supported by `UX-012`/`UX-012B`, it is not adopted here.

## 3. Relationship to UX-012

`UX-012` (and `UX-012B`, its own companion component specification) remain the semantic authority for every component this document specifies. This document adds implementation-ready anatomy, properties, states, interaction, accessibility, and token detail; it does not redefine any component's purpose or meaning. Where this document's own detail and `UX-012`/`UX-012B`'s own text could be read to diverge, `UX-012`/`UX-012B` govern, and where `UX-012`/`UX-012B` themselves diverge from each other, this document applies the authority hierarchy Section 2 states — an Accepted ADR's own already-corrected terminology governs over an uncorrected `UX-012`-family passage. **One component below (Atlas Warning) carries exactly this situation** — see its own Documentary note.

## 4. Relationship to UX-013F

`UX-013F-Foundation-Reasoning-Component-Library-Assembly.md` is this document's peer, canonical for the Foundation and Reasoning tiers and for the cross-cutting infrastructure every tier depends on (including `AIAuthorshipIndicator`, which that document's own Metadata & Provenance category already owns, jointly with AI Collaboration, per its own text: *"AIAuthorshipIndicator (shared with AI Collaboration; primary ownership here)"* — meaning `UX-013F` itself, not this document). This document does not restate that content; it references it by name (`SectionContainer`, `MetadataBlock`, `StatusBadge`, `ProgressIndicator`) exactly as `UX-013C` and `UX-013D` already do. This document adopts `UX-013F`'s own ten-type classification model to classify each component below, without redefining any classification type.

## 5. AI Collaboration Architecture Overview

The AI Collaboration tier renders Atlas's own contribution to the Investor's reasoning: suggestions, observations, warnings, advisory direction, clarifying questions, and reasoning-state summaries. Every component in this tier is bounded by the same, unqualified ownership constraint, stated once here and never varied per component: **Atlas MAY suggest, summarize, clarify, warn, explain, and ask. Atlas MAY NEVER decide, conclude on behalf of the Investor, learn autonomously, commit, record, approve, or perform Review, Learning, or Decision.** This is not a new rule — it is `UX-000` UXD-R-048 (*"Atlas MAY support, suggest, summarize, organize, and surface. Atlas SHALL NOT perform the Investor's own act of Judgment, Commitment, or Learning"*), UXD-R-035 (*"UX SHALL NOT decide or extend AI autonomy"*), UXD-R-056, and UXD-R-057, applied identically across all six components below, per this task's own explicit instruction that every component reinforce, not weaken, Human Ownership.

Six components are canonical and fully specified below, all traced directly to `UX-012` §28 and `UX-012B` §11: Atlas Suggestion, Atlas Insight, Atlas Warning, Atlas Recommendation, Atlas Clarification, Atlas Summary.

Several further AI-Collaboration-adjacent constructs referenced in `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own account — a separate `AtlasQuestion` distinct from Atlas Clarification, and a standalone `AIAuthorshipIndicator` — are not specified in this document. Neither is independently justified by `UX-012`/`UX-012B`'s own text as a distinct AI-Collaboration-tier component. Per this task's own governing instruction, they are not authored here; see Section 9, Deferred.

## 6. Canonical Component Inventory

| Component | Classification | Status | Source |
|---|---|---|---|
| Atlas Suggestion | Component | **[C]** Canonical | `UX-012` §28, `UX-012B` §11 |
| Atlas Insight | Component | **[C]** Canonical | `UX-012` §28, `UX-012B` §11 |
| Atlas Warning | Component | **[C]** Canonical | `UX-012` §28, `UX-012B` §11 |
| Atlas Recommendation | Component | **[C]** Canonical | `UX-012` §28, `ADR-003` R-01.A |
| Atlas Clarification | Component | **[C]** Canonical | `UX-012` §28, `UX-012B` §11 |
| Atlas Summary | Component | **[C]** Canonical | `UX-012` §28, `UX-012B` §11 |

Not specified in this document — see Section 9: `AtlasQuestion` (as a construct independent of Atlas Clarification), `AIAuthorshipIndicator` (as a standalone AI Collaboration-tier component, as distinct from the Metadata & Provenance-tier `Author`/`AIAuthorshipIndicator` construct `UX-013F` already owns).

---

## 7. Component Specifications

### 7.1 Atlas Suggestion

**Purpose [C].** AI-generated content offered as optional input to user reasoning. Per `UX-012` §28: *"AI-generated content offered as optional input to user reasoning. Never mandatory. Never primary."*

**Semantic Meaning [C].** Per `UX-012B` §11: *"Presents a specific Atlas-generated improvement proposal for a user-authored or user-editable field — a concrete alternative wording, a missing element, a precision improvement."*

**Product Correspondence [C].** Governed directly by `ADR-002` C-02 (AI Authorship and Provenance) and its Mixed-Origin addendum, adopted here unchanged: acceptance alone does not transfer authorship; the accepted, unedited state is labeled "Atlas Suggested / User Accepted"; only a subsequent genuine edit transitions the field to "User Authored." Per `UX-000` UXD-R-056/UXD-R-057, Atlas Suggestion content is never framed with first-person belief language.

**Ownership [C].** The field it addresses remains the user's own field throughout. Per `ADR-002` C-02: *"Recording never itself transfers authorship."* Per `UX-000` UXD-R-051: *"Only a genuine Investor act MAY create Investor-authored content from Atlas-originated content."*

**Composition [C].** Component (not composite — does not own sub-components with independent state, though it addresses a field owned by another component).

**States [C].** Per `UX-012B` §11 and `ADR-002` C-02: pending (offered, not yet responded to), accepted ("Atlas Suggested / User Accepted"), user-modified-from-atlas (after a genuine subsequent edit), dismissed (session-scoped).

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `targetFieldId` | string | — | Yes | The field this suggestion addresses |
| `suggestedContent` | string | — | Yes | |
| `reason` | string | — | Yes | Metadata-scale explanation, per `UX-012B` §11 |
| `state` | `'pending' \| 'accepted' \| 'user-modified-from-atlas' \| 'dismissed'` | `'pending'` | Yes | |
| `offeredAt` | timestamp | — | Yes | |
| `acceptedAt` | timestamp \| null | `null` | No | Per the already-adopted C-02 provenance model |

**Interaction [C].** Per `UX-012` §28: *"Trigger: surfaces after a 1.5-second pause in user editing — never interrupts active typing."* Three responses, per `UX-012` §28 and `UX-012B` §11: Accept (content populates the field; five-second structural undo window), Partial Accept (selectable segments, user confirms individual portions), Dismiss (removed for the current session, does not reappear). Per `UX-012B` §11: appears at most once per editing session per field; if the user edits the field without responding, the panel dims and disappears.

**Accessibility [C].** Per `ADR-002` C-02's own model, the attribution label ("Atlas Suggested / User Accepted") is announced via `aria-live="polite"`, consistent with the identical requirement already specified for Conclusion (`UX-013B` §1).

**Responsive Behaviour [IR].** Consistent with `UX-012` §73's own general AI Suggestion responsive rule (below the relevant field on all breakpoints).

**Token Mapping [IR].** No dedicated Atlas Suggestion token group was found named in `UX-012D` §3; this component reuses `type.body.atlas` (existing, `UX-012D` §3) for the suggestion text and `color.text.secondary` — the canonical Attribution Text mapping, per `UX-012D` §3's own Canonical Attribution & Action Text Mapping contract, Phase 3C — for the general attribution color already used for Conclusion's own Atlas-attribution indicator (per `UX-013B` §1's own Token Mapping).

| Visual Property | Token |
|---|---|
| Suggestion text | `type.body.atlas` |
| Attribution label | `color.text.secondary` |

**Engineering Notes [C].** Per `UX-012B` §11: *"Historical behavior: Suggestions are not preserved in the decision record. Only the final content of the field — whatever the user authored or confirmed — is recorded."*

**Anti-Patterns [C].** Do not transition a field to "user-modified-from-atlas" on Accept alone — `ADR-002` C-02 explicitly rejects this. Do not require the user to confirm they have just edited something they visibly just edited, per `ADR-002` C-02's own "no confirmation prompt" rule.

---

### 7.2 Atlas Insight

**Purpose [C].** A contextual observation from Atlas that does not require user action. Per `UX-012` §28: *"A contextual observation from Atlas that does not require user action. Informational."*

**Semantic Meaning [C].** Per `UX-012B` §11: *"Presents a broader interpretive observation from Atlas — not a suggestion for specific field content, but a contextual interpretation relevant to the user's current reasoning."*

**Product Correspondence [C].** `UX-012B` §11 names *"RELATED PATTERN"* as one of Atlas Insight's own illustrative label types. **Boundary note [IR].** Per `UX-000` UXD-R-104, Pattern Recognition is accepted at `APP-001` §3.12 but has no governing APS yet, and *"SHALL NOT have its normative behavior represented by any UX specification until that governing APS exists."* This document does not represent Pattern Recognition's own normative behavior; Atlas Insight remains a pure UX presentation artifact for an observation, whatever its own underlying source, and a "RELATED PATTERN" label is descriptive labeling only, not an operationalization of Pattern Recognition's own Product-layer behavior.

**Ownership [C].** Atlas-originated, informational, per `UX-000` UXD-R-054/UXD-R-056. The user's own Investor Judgment is not engaged merely by an Insight's presence.

**Composition [C].** Component.

**States [C].** default, acknowledged (`UX-012` §28).

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `insightType` | string | — | Yes | e.g. "RELATED PATTERN," "HISTORICAL PARALLEL," "PORTFOLIO CONTEXT," per `UX-012B` §11 |
| `statement` | string | — | Yes | |
| `sourceReference` | string | — | No | Per `UX-012B` §11 |
| `state` | `'default' \| 'acknowledged'` | `'default'` | Yes | |

**Interaction [C].** Per `UX-012B` §11: *"Expand/collapse. A 'View analysis →' link when the Insight refers to specific underlying content."* Does not require the user to accept or dismiss; informational only.

**Accessibility [IR].** Consistent with `UX-012A` §15's own non-color-communication requirement; the insight-type label is always accompanied by text, never color alone.

**Responsive Behaviour [IR].** Consistent with `UX-012` §73's own Section-level component responsive rule.

**Token Mapping [IR].** No dedicated token group was found named in `UX-012D` §3 for Atlas Insight; this component reuses `type.body.atlas` for its statement text, consistent with Atlas Suggestion (§7.1, above).

**Engineering Notes [C].** Per `UX-012B` §11: *"Historical behavior: An Insight surfaced during a decision session may be noted in the session context but is not preserved in the decision record."*

**Anti-Patterns [C].** Do not present an Insight's own "RELATED PATTERN" label as an assertion of Pattern Recognition's own governed normative behavior (Product Correspondence, above). Do not require user response to an Insight — it is informational by definition.

---

### 7.3 Atlas Warning

**Purpose [C].** A concern identified by Atlas that warrants user attention. Per `UX-012` §28: *"A concern identified by Atlas that warrants user attention."*

**Semantic Meaning [C].** Per `UX-012B` §11: *"Presents a conflict, inconsistency, or concern that Atlas has identified in the user's current reasoning — the AI Collaboration form of a challenge or contradiction."*

**Documentary note [IR].** `UX-012` §28 states Atlas Warning's own three severity levels as *"Informational, Material, Blocking,"* explicitly *"matching Challenges."* `UX-012B` §11 instead states *"Informational, Material, Unresolved."* Fresh verification found `UX-012B`'s own Challenges component (§6, the very component Atlas Warning's own severity model is stated to match) **also** uses *"Informational, Material, Unresolved"* — internally consistent with itself, but inconsistent with `UX-012` §23's own Challenges definition, which uses *"Informational, Material, Blocking"* and carries its own explicit Correction Notice: *"Corrected per ADR-002/C-04: this line previously stated a Blocking challenge 'must be resolved or explicitly overridden'... Challenges acknowledgment, at any severity, is soft friction and is never a hard block on recording."* Per the authority hierarchy (Section 2, above), an Accepted ADR's own already-reflected correction governs over an uncorrected `UX-012`-family passage. This document therefore uses **Blocking** as the canonical third severity tier, per `UX-012` §23/`ADR-002` C-04, and discloses that `UX-012B` §6 and §11 both retain the uncorrected "Unresolved" term, apparently not yet updated when `ADR-002`/C-04's correction was applied to `UX-012`'s own main-document text. This document does not edit `UX-012B` to correct this; that remains a future `UX-012`-family correction, outside this document's own authority.

**Product Correspondence [C].** Atlas Warning presents already-governed Challenge/contradiction content in AI-collaboration form; it decides nothing about Reasoning validity itself, per `UX-000` UXD-R-030.

**Ownership [C].** Atlas-identified; the user acknowledges or addresses it, per `UX-012B` §11. Acknowledgment means the concern has been seen and considered, never that the user agrees with it, per `ADR-002` C-04's own general Challenges rule, applied identically here.

**Composition [C].** Component.

**States [C/IR]** — per the Documentary note, above: Informational, Material, Blocking (`UX-012` §23/`ADR-002` C-04, this document's own canonical choice); `UX-012B`'s own "Unresolved" label is disclosed as the uncorrected equivalent, not adopted.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `warningType` | string | — | Yes | e.g. "CONTRADICTS PRIOR REASONING," per `UX-012B` §11 |
| `statement` | string | — | Yes | |
| `explanation` | string | — | Yes | Why this matters, per `UX-012B` §11 |
| `severity` | `'informational' \| 'material' \| 'blocking'` | — | Yes | Per this document's own Documentary note, above |
| `acknowledgedAt` | timestamp \| null | `null` | No | |

**Interaction [C].** Per `UX-012` §28: *"Blocking Warnings create a soft gate on the completion action."* Per `UX-012B` §11: *"May be acknowledged... or addressed... The warning is never blocking except in the specific case of [Blocking] status affecting the completion gate"* (term corrected per the Documentary note, above; the underlying soft-gate-only behavior, consistent with `ADR-002` C-04's own "soft friction, never hard blocking," is unaffected by this correction).

**Accessibility [C].** Consistent with `UX-012A` §15's own non-color-communication requirement, already applied identically to Challenges.

**Responsive Behaviour [IR].** Consistent with Atlas Insight's own responsive rule (§7.2, above).

**Token Mapping [C]**, reusing `UX-012D` §3's own already-named `Contradiction`/`Warning` semantic token groups: *"Warning: synonym for Material Contradiction and above. The Warning semantic group maps to the same amber tokens — the distinction between Contradiction and Warning is semantic (Contradiction is content-identified; Warning is Atlas-identified) not visual."*

| Visual Property | Token |
|---|---|
| Informational/Material/Blocking severity border | `color.border.contradiction.[informational\|material\|unresolved]` (existing, `UX-012D` §3, Contradiction group — the underlying token retains its own "unresolved" suffix; only the user-facing severity label reads "Blocking," per the Documentary note above) |

**Engineering Notes [C].** Per `UX-012B` §11: *"Historical behavior: Material and [Blocking] warnings that were acknowledged but not addressed are noted in the decision record's session context."*

**Anti-Patterns [C].** Do not allow a Blocking Atlas Warning to require resolution rather than acknowledgment — `ADR-002` C-04 governs this identically to Challenges. Do not let Atlas Warning silently gate recording without an explicit, visible reason, per `ADR-002` C-06's own general explanation requirement.

---

### 7.4 Atlas Recommendation

**Purpose [C].** A specific action or direction recommended by Atlas, with explicit reasoning. Per `UX-012` §28: *"A specific action or direction recommended by Atlas, with explicit reasoning."*

**Semantic Meaning [C].** Per `ADR-003` R-01.A (Concept A, the sole canonical Atlas Recommendation, adopted here unchanged): *"A general, Atlas-origin directional advisory artifact that suggests what action or direction should be considered. It is not defined by transferring content into a specific field."* Distinguished from Atlas Suggestion per `UX-012` §28: *"a Recommendation suggests what to do; a Suggestion contributes content."*

**Product Correspondence [C].** Per `ADR-003` R-05: neither Atlas Recommendation nor accepting it constitutes a Decision. This document does not redefine Atlas Recommendation — its identity, naming, and boundary are fully settled by `ADR-003` and are adopted here unchanged, exactly as `UX-013C` §7.1 already adopts `ADR-003`'s own treatment of Proposed Decision Candidate Content without redefinition.

**Ownership [C].** Atlas-originated advisory content; per `ADR-003` R-05, the Investor's own separate commitment-and-recording flow (governed in `UX-013C`) is the only path to a Decision.

**Composition [C].** Component.

**States [C].** pending, accepted, dismissed, acted-upon (`UX-012` §28). Per `ADR-003` R-01.A: acceptance and action are decoupled events; UX-012 §28 does not describe a field-population mechanism for this component, unlike Atlas Suggestion.

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `statement` | string | — | Yes | The recommended direction |
| `reasoning` | string | — | Yes | |
| `state` | `'pending' \| 'accepted' \| 'dismissed' \| 'acted-upon'` | `'pending'` | Yes | Per `UX-012` §28 |

**Interaction [C].** Per `UX-012` §28: *"Position: within a relevant Conclusion component or as a standalone Atlas component."* Per `ADR-003` R-01.A: acceptance does not itself populate any field.

**Accessibility [IR].** Consistent with Atlas Insight's own accessibility rule (§7.2, above); state changes announced via `aria-live="polite"`.

**Responsive Behaviour [IR].** Consistent with Atlas Insight's own responsive rule (§7.2, above).

**Token Mapping [IR].** No dedicated token group was found named in `UX-012D` §3 for Atlas Recommendation specifically; reuses `type.body.atlas` for its statement text, consistent with Atlas Suggestion and Atlas Insight, above.

**Engineering Notes [C].** Per `UX-012` §28: *"Reuse: Dashboard, Investment Workspace, Decision Workspace."*

**Anti-Patterns [C].** Per `ADR-003` R-02: the term "Recommendation" or "Atlas Recommendation" must not be used, in any future correction, for Concept B (Proposed Decision Candidate Content, `UX-013B` §10) — the two remain fully distinguished. Do not treat acceptance of this component as populating Proposed Decision — that is Atlas Suggestion's/Candidate Content's own, separate mechanism (`UX-013C` §7.1).

---

### 7.5 Atlas Clarification

**Purpose [C].** A question Atlas poses to the user. Per `UX-012` §28: *"A question Atlas poses to the user — used when the user's input is ambiguous and clarification would improve the quality of Atlas's assistance."*

**Semantic Meaning [C].** Per `UX-012` §28: *"Character: optional, lightweight, easily dismissed. Never blocks reasoning."*

**Product Correspondence [C].** Presents a request for input, not a decision or judgment; asserts no independent Product meaning.

**Ownership [C].** The user's own response is the only source of the clarifying content; Atlas poses the question but does not supply or infer the answer on the user's behalf, per `UX-000` UXD-R-048.

**Composition [C].** Component.

**States [C].** pending, answered, dismissed (`UX-012` §28).

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `question` | string | — | Yes | |
| `state` | `'pending' \| 'answered' \| 'dismissed'` | `'pending'` | Yes | |
| `response` | string \| null | `null` | No | The user's own answer |

**Interaction [C].** Optional, lightweight, easily dismissed; never blocks reasoning (`UX-012` §28). Reuse: Decision Workspace (primary), per `UX-012` §28.

**Accessibility [IR].** Consistent with Atlas Insight's own accessibility rule (§7.2, above).

**Responsive Behaviour [IR].** Consistent with Atlas Insight's own responsive rule (§7.2, above).

**Token Mapping [IR].** No dedicated token group was found named in `UX-012D` §3 for Atlas Clarification; reuses `type.body.atlas` for the question text, consistent with the pattern established above.

**Engineering Notes [IR].** No historical-persistence behavior is stated in either `UX-012` §28 or `UX-012B` for this component; per Atlas Insight's own precedent (§7.2, above), this document does not invent one, and treats it as session-scoped only, consistent with Atlas Clarification's own stated "easily dismissed" character.

**Anti-Patterns [C].** Do not allow an unanswered Atlas Clarification to block reasoning or recording — `UX-012` §28's own "never blocks reasoning" is unconditional.

---

### 7.6 Atlas Summary

**Purpose [C].** A structured summary of the current reasoning state, generated by Atlas to help the user orient. Per `UX-012` §28: *"A structured summary of the current reasoning state, generated by Atlas to help the user orient."*

**Semantic Meaning [C].** Naming note: this component corresponds to `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own `AIGeneratedSummary`; this document uses `UX-012`/`UX-012B`'s own canonical name, "Atlas Summary," consistent with its own established practice of preferring `UX-012`-family naming over the Interim Note's own (`UX-013C` §7.1's identical treatment of "Proposed Decision" over "Decision Proposal").

**Product Correspondence [C].** Summarizes already-governed reasoning content; asserts no independent Product meaning of its own.

**Ownership [C].** Per `UX-012` §28: *"Behavior: the user can replace any part of the Atlas Summary with their own authored content."* The summary itself remains Atlas-attributed until a genuine Investor edit occurs, per the identical C-02 provenance model already governing Atlas Suggestion (§7.1, above).

**Composition [C].** Component.

**States [IR].** Not explicitly enumerated in `UX-012`/`UX-012B`; by direct analogy to Atlas Suggestion's own attribution model (§7.1, above, `ADR-002` C-02), this document specifies: atlas-generated (default), user-modified (after a genuine edit to any part).

**Properties [IR]:**

| Property | Type | Default | Required | Notes |
|---|---|---|---|---|
| `summaryText` | string | — | Yes | |
| `isUserModified` | boolean | `false` | No | Per the C-02 provenance model, applied by analogy |

**Interaction [C].** Per `UX-012` §28: *"Position: top of the Workspace or within a designated Summary area."* Per `UX-012B` §11's own general Editable Section model, applied here: the user can replace any part with their own authored content.

**Accessibility [IR].** Consistent with Atlas Suggestion's own accessibility rule (§7.1, above), applied by analogy since no dedicated rule is stated in either source for this component.

**Responsive Behaviour [IR].** Consistent with Atlas Insight's own responsive rule (§7.2, above).

**Token Mapping [IR].** Reuses `type.body.atlas` for atlas-generated content and `type.body.user` for user-modified portions, consistent with the Conclusion component's own identical attribution-weight distinction (`UX-013B` §1).

**Engineering Notes [C].** Per `UX-012` §28: *"Reuse: Investment Workspace, Decision Workspace."*

**Anti-Patterns [IR].** Do not present Atlas Summary content with first-person belief framing — `UX-000` UXD-R-057 applies identically to this component as to every other Atlas-generated analytical content in this document.

---

## 8. Cross-Component AI Behaviour

All six components above share the identical ownership boundary stated once in Section 5, above, and reinforced here: none of the six permits Atlas to decide, conclude on behalf of the Investor, learn autonomously, commit, record, approve, or perform Review, Learning, or Decision. Every component's own Interaction section describes only: offering content or observation (Atlas Suggestion, Atlas Insight, Atlas Recommendation), surfacing a concern (Atlas Warning), posing a question (Atlas Clarification), or summarizing already-authored content (Atlas Summary) — the six permitted verbs this task itself names (suggest, summarize, clarify, warn, explain, ask), and no others. Every component that presents Atlas-generated text is governed by the identical `UX-000` UXD-R-056/UXD-R-057 first-person-belief-framing prohibition and the identical `ADR-002` C-02 acceptance-does-not-transfer-authorship model, applied consistently, not varied per component. One component (Atlas Warning) carries a disclosed, unresolved terminology discrepancy between `UX-012` and `UX-012B` (Section 7.3); no other cross-component inconsistency was found.

## 9. Deferred

The following constructs, named in `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`'s own AI Collaboration-category account, are explicitly **not** specified in this document. Each is named here, with the exact reason for deferral, per `ADR-001` Governance Rule 5.

- **`AtlasQuestion`** (as a construct independent of Atlas Clarification) — the interim note's own account lists `AtlasQuestion` and `AtlasClarification` as two separate components. `UX-012`/`UX-012B` name only one component for this purpose — Atlas Clarification (§7.5, above), which already covers "a question Atlas poses to the user." The interim note's own two-component split is not independently supported by `UX-012`/`UX-012B` and is not adopted here.
- **`AIAuthorshipIndicator`** (as a standalone AI Collaboration-tier component) — `UX-013F` itself already states this construct is *"shared with AI Collaboration; primary ownership here,"* i.e., owned by `UX-013F`'s own Metadata & Provenance category, not by this document's own tier. No `UX-012`/`UX-012B` component separately named "AI Authorship Indicator," distinct from the general `Author` metadata component and each individual component's own attribution properties (already specified throughout this document — e.g., Atlas Suggestion's own `color.text.secondary` attribution token, §7.1), was found. Authoring a competing, AI-Collaboration-tier version here would duplicate `UX-013F`'s own already-stated ownership.

## 10. Out of Scope

Decision-tier components (`UX-013C`) and Monitoring-tier components (`UX-013D`) — this document cross-references Atlas Suggestion's own relationship to Proposed Decision Candidate Content (`UX-013B` §10) and does not restate or redefine any Decision- or Monitoring-tier construct. Foundation, Reasoning, and Metadata & Provenance components — fully specified in `UX-013F`; this document references `AIAuthorshipIndicator`, `StatusBadge`, `SectionContainer`, and `MetadataBlock` by name only, per Section 9, above.

# ADR-003 — Recommendation Identity and Terminology Resolution

## Status

Accepted

**Date:** 2026-07-25

## Context

`UX-Architecture-Review-001.md` identified, as its own **Finding 5.3** (severity Medium-High, listed in the findings summary as **H-2**), that the term "Recommendation" is used for what reads as two different components: `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §28 ("AI Collaboration Components") defines **"Atlas Recommendation"** — *"a specific action or direction recommended by Atlas, with explicit reasoning... Distinction from Atlas Suggestion: a Recommendation suggests what to do; a Suggestion contributes content"* — while `UX-013B-Atlas-Component-Specification-Reasoning-Components.md` independently defines a plain **"Recommendation"** Reasoning component, with an Atlas-generated and a user-authored variant, positioned in its own Reasoning dependency chain, whose accepted content *"flows into the Proposed Decision field."* Finding 5.3 states explicitly: *"Only UX-013E notices and reconciles the two."*

This finding was **not** among the six Critical findings (C-01 through C-06) resolved by `ADR-002-Critical-UX-Architecture-Resolutions.md`. It is absent from ADR-002's Context, Decision, and Supersession sections in their entirety. It therefore remains, as of this ADR, an identified but ungoverned architectural question.

The question resurfaced during execution of the Atlas UX Source Correction Plan's **Phase 3D** (held, not authorized for source editing — see the Plan, Section 14), specifically during a dedicated, read-only **"UX-013B Sequence Reconciliation Assessment"** performed to determine how UX-013B's finer-grained Reasoning components (Scenario Analysis, Comparison, Recommendation) relate to the canonical 13-item Decision Workspace sequence adopted by ADR-002 C-03. That assessment found Recommendation's status could not be resolved without first resolving its underlying identity question, and recommended a dedicated architectural decision task — the read-only **"Recommendation Identity"** assessment — as the smallest safe next step. This ADR is the formal adoption of that assessment's findings.

**On UX-013E specifically:** `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md`'s own attempted reconciliation (its "Recommendation vs. Atlas Recommendation Presentation" section) was independently checked against the actual UX-012 §28 definition during the Recommendation Identity assessment and found **not to address it at all** — UX-013E's reconciliation is entirely against a differently-named concept, "Atlas Recommendation Presentation," which UX-013E itself attributes to the absent, unconfirmed **UX-013D** volume (per `ADR-001-Missing-Source-Volume-Governance.md`'s three-tier classification and ADR-002 C-05). UX-013E's reconciliation therefore carries no governing weight for the question this ADR resolves; it is retained below only as historical design evidence, not as authority.

## Problem Statement

Before any Phase 3D source correction touching UX-013B's Recommendation component or its Decision Workspace sequence listing can be authorized, the repository requires a settled answer to: what is Recommendation, how does it relate to Atlas Suggestion, Proposed Decision, and Decision, and does the corpus's overlapping use of "Recommendation" / "Atlas Recommendation" name one concept or two?

## Scope

This ADR resolves Recommendation's semantic identity, ownership, provenance relationship, and canonical-sequence status. It does **not** resolve Scenario Analysis's or Comparison's canonical-sequence status (both remain separately held, per the UX-013B Sequence Reconciliation Assessment), does not itself edit any UX source document, does not amend the Source Correction Plan, and does not adopt a Domain Object.

## Authority and Dependencies

- Depends on `ADR-002-Critical-UX-Architecture-Resolutions.md` C-02 (AI Authorship and Provenance) and its 2026-07-25 addendum ("Mixed-Origin Single-Field Content") — this ADR does not reopen, revise, or reinterpret either; it applies them unchanged to a case (Recommendation-derived content) they were not previously known to cover.
- Depends on ADR-002 C-03 (Decision Workspace Sequence) — this ADR does not reopen the canonical 13-item table; it clarifies that Recommendation is not, and was never intended to be, a member of it.
- Depends on `ADR-001-Missing-Source-Volume-Governance.md`'s three-tier classification for its treatment of UX-013E (see Context, above).
- Supersedes no prior ADR. Extends no prior ADR's own text (unlike the ADR-002 mixed-origin addendum, which extended C-02's own already-adopted enumeration, this ADR resolves a finding ADR-002 never took up at all).

## Definitions

**Atlas Suggestion** — the already-governed, already-corrected (Source Correction Plan Phases 2, 2B, 3, 3C) content-presentation-and-acceptance interaction pattern: Atlas-generated content offered as optional input, surfaced after a pause in editing, with Accept / Partial Accept / Dismiss responses and a structural undo window. Governed by ADR-002 C-02 and its addendum.

**Proposed Decision** — the canonical Decision Workspace sequence item at position 3 (ADR-002 C-03): *"The user's own stated intention, in their own words, as a working position... User-owned (blank until authored)... Feeds Final Decision Card."*

**Decision** — the user's committed, recorded choice, produced only by the canonical Record Decision action (position 13). Never constituted by content acceptance alone (ADR-002 C-02: *"Recording never itself transfers authorship... Accept alone... does not itself convert any field to 'User Authored.'"*).

**Concept A / Atlas Recommendation** — see Decision R-01.A, below.

**Concept B / Proposed Decision Candidate Content** — see Decision R-01.B and R-02, below.

## Considered Alternatives

**A — One Recommendation concept with two renderings.** This is the reading UX-013E's own text superficially suggests. **Rejected** — UX-013E's reconciliation is against a UX-013D-attributed concept, not UX-012 §28's real, committed definition; independently comparing UX-012 §28 against UX-013B directly shows a genuine behavioral mismatch (UX-012's four-state pending/accepted/dismissed/**acted-upon** lifecycle, with acceptance and action as distinct events and no field-population mechanism at all, versus UX-013B's Accept-synchronously-transfers-content model) that this alternative cannot explain away.

**B — Recommendation equals Proposed Decision.** **Rejected** — a user must be able to author Proposed Decision without any Recommendation ever existing (Proposed Decision's own canonical definition: "blank until authored"); collapsing the two would make UX-013B's separate component definition meaningless and contradicts its own explicit framing of Recommendation as "input to the Decision," not the Decision-Workspace field itself.

**C — Recommendation as an independent Domain Object.** **Rejected as unauthorized by current evidence** — UX-013B's own text states Recommendation "does not appear as a standalone Historical component — its content is absorbed into the Decision," i.e., no independent identifier, persistence, or durable reference is specified anywhere in the corpus for either concept. Adopting Domain Object status would invent, not merely recognize, architecture.

**D — Recommendation as a separate canonical Decision Workspace sequence stage.** **Rejected** — ADR-002 C-03's own evidence base (the Resolution Design's C-03 section, re-verified) draws its adopted order from UX-009/UX-009A/UX-010/UX-011 versus UX-012. UX-013B is mentioned there once, but only regarding its own separate top-level 1–19 component numbering, which C-03 explicitly considered and rejected as a competing full-sequence claim ("not rejected as wrong, since UX-013B's own scope is intentionally Reasoning-components-only... but noted as not itself a competing full-sequence claim"). UX-013B's *separately-labeled* §14 "Decision Workspace sequence" — the list that actually lists Recommendation as item 11 — was never examined by C-03 at all; it was discovered later, during the Source Correction Plan's own Phase 3 Scope Reassessment. Recommendation's item-11 placement was therefore never resolved, one way or the other, by ADR-002 C-03, and no governing document names Recommendation as a 14th (or replacement) sequence item. Adopting this alternative would expand the already-fixed 13-item canonical table.

**E — Recommendation as generic Atlas advice only (no field-population role).** **Rejected** — this describes Concept A (Atlas Recommendation) accurately but is directly contradicted by UX-013B's own explicit "flows into the Proposed Decision field" text for Concept B; the two cannot be merged into one advice-only definition without discarding real, specified UX-013B behavior.

**F — Two distinct concepts with disambiguated names.** **Accepted** — see Decision, below. This is the only alternative that preserves every specified behavior in UX-012, UX-013B, UX-012B, and UX-012C without inventing new architecture, expanding the canonical sequence, or silently dropping functionality.

**G — Leaving terminology unresolved.** **Rejected** — this is the status quo that has already blocked Phase 3D's own governance since the UX-013B Sequence Reconciliation Assessment; per that assessment, the corpus does contain sufficient, if previously unexamined, evidence to resolve this specific question (unlike Scenario Analysis/Comparison, which remain genuinely unresolved and are correctly left held).

## Decision

The following ten resolutions are adopted together, as one coordinated decision.

### R-01 — Two Distinct Concepts

The term "Recommendation" currently refers to two distinct concepts in the committed corpus.

**A. Atlas Recommendation.** Canonical source: `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §28. A general, Atlas-origin directional advisory artifact that suggests what action or direction should be considered. It is not defined by transferring content into a specific field. It may be displayed across multiple surfaces (Dashboard, Investment Workspace, Decision Workspace). UX-012 §28 defines `accepted` and `acted-upon` as distinct states and states no field-population behavior anywhere in its definition of Atlas Recommendation — unlike its own immediately-preceding Atlas Suggestion entry in the same section, which explicitly states its content "populates the relevant field." This supports treating acceptance and action as decoupled events, neither of which is described as populating a field; the source does not, however, explicitly define the exact interaction between the `accepted` and `acted-upon` states beyond naming them separately.

**B. Proposed Decision Candidate Content.** Current specifying source: `UX-013B-Atlas-Component-Specification-Reasoning-Components.md`'s Recommendation component. Transient candidate wording representing a possible Proposed Decision. It may be Atlas-originated or user-originated. Its semantic destination is the canonical Proposed Decision field. It does not constitute a separate canonical Decision Workspace stage.

### R-02 — Canonical Naming

The term **"Atlas Recommendation" is reserved exclusively for Concept A**, as already defined in UX-012 §28.

Concept B receives the canonical name **"Proposed Decision Candidate Content"** (short form, once the canonical term is established in context: "candidate content").

**Naming analysis** (candidates evaluated): *Decision Proposal* — rejected; near-transposition of "Proposed Decision" and collides with UX-012B's already-established "Atlas proposal block" UI element, high misreading risk. *Proposed Decision Draft* — rejected; "Draft" already has an established, unrelated meaning in this corpus (session/autosave draft state — "Draft Indicator," "Discard draft," "Compare with recorded"), and reusing it here would collide with that meaning. *Recommendation Content* — rejected; retains "Recommendation" as a substring, failing to disambiguate from Concept A. *Decision Direction Candidate* — rejected as suboptimal; "Direction" pulls back toward Concept A's own vocabulary ("a Recommendation suggests what to do... **direction**"), risking re-blending the two concepts it exists to separate. *Proposed Decision Candidate* — considered strong, but "Candidate" alone, as a bare noun, carries a mild risk of being read as naming a persisted entity ("the Candidate"), in tension with R-07's requirement that no Domain Object identity be implied. **Proposed Decision Candidate Content** — **selected**: it names the destination field unambiguously (reuses "Proposed Decision" directly), conveys non-committal, possibly-plural, not-yet-accepted status via "Candidate," and the trailing "Content" firmly anchors the term as data, not an object — directly serving R-07's own requirement. It reads coherently as content in prose, correction notices, and accessibility language; its use in a component prop name or state label may reasonably be abbreviated in context (e.g., `candidateContent` within a Proposed-Decision-scoped component) — this abbreviation choice is left to future implementation, not dictated here (see Non-Decisions).

**Prohibited/deprecated terminology, going forward:** "Recommendation" and "Atlas Recommendation" must not be used, in any future correction, to name Concept B. UX-013B's own internal reuse of "Atlas Recommendation" as one of its two Recommendation-component *variant names* (distinct from UX-012's component of the same name) is a confirmed instance of exactly this collision and must be renamed in any future UX-013B correction — this ADR does not perform that rename itself (see Source-Correction Implications).

### R-03 — Relationship to Atlas Suggestion

Concept B is not a second content-acceptance architecture. When Atlas originates Concept B, it is presented and accepted through the already-governed Atlas Suggestion interaction pattern (ADR-002 C-02, its addendum, and the already-corrected UX-012B/UX-012C mechanics). Therefore: Atlas Suggestion describes the presentation-and-acceptance *mechanism*; Concept B describes the semantic *role* of the resulting content. Atlas origin is provenance, not the content's semantic identity. Accept transfers content into Proposed Decision. Accept does not make Atlas the decision-maker. Replace and Append retain their existing, already-governed meanings exactly. Acceptance and genuine editing remain distinct. Existing mixed-origin and `user-modified-from-atlas` rules apply unchanged. **This ADR does not redefine Atlas Suggestion and does not reopen ADR-002 C-02.**

### R-04 — Relationship to Proposed Decision

Concept B and Proposed Decision are not identical. Concept B is candidate input; Proposed Decision is the canonical, user-owned Decision Workspace field. A user may author Proposed Decision without any candidate content ever existing. A user may reject or ignore candidate content. Once candidate content is accepted into Proposed Decision, the content is governed as Proposed Decision content under the already-adopted C-02 model; the candidate content itself has no separate continuing identity (no committed source requires one — see R-07); the later Decision lifecycle remains entirely separate.

### R-05 — Relationship to Decision

Neither Concept A nor Concept B constitutes a Decision. Acceptance of advice (Concept A) or wording (Concept B) does not itself record commitment. The user must separately complete the canonical commitment-and-recording flow (Proposed Decision → ... → Final Decision Card → Record Decision). Four events remain distinct throughout: (1) Atlas generating or presenting content; (2) the user accepting wording into Proposed Decision; (3) the user forming or committing to a Decision; (4) the system recording the Decision.

### R-06 — Relationship to Reasoning

Concept B may be derived from, or informed by, Reasoning — UX-013B's own Dependency Chain (§14) is retained as an accurate description of derivation: *Scenario Analysis + Comparison → (synthesized into) → Recommendation [renamed under this ADR to Proposed Decision Candidate Content] → (formalized as) → Decision.* This derivational relationship does **not** grant Concept B independent Domain Object identity, independent persistence, or canonical sequence membership. Concept B may be the output or presentation of reasoning without itself being a reasoning process. **This ADR does not decide Scenario Analysis's or Comparison's own placement or status** — both remain held exactly as the UX-013B Sequence Reconciliation Assessment left them.

### R-07 — Component and Ontology

Neither Concept A nor Concept B is adopted as an independently identified Domain Object by this ADR. This ADR governs semantic role, component responsibility, workflow relationship, naming, and provenance interaction only. It does **not** establish identifiers, persistence schemas, history retention, backend entities, or Core/domain ontology for either concept. Any future adoption of Concept B as a Domain Object requires its own, separate architectural decision, with its own explicit justification.

### R-08 — Canonical Sequence

Concept B is not, and never was validly, an independent canonical Decision Workspace sequence item. The canonical 13-item sequence continues unchanged, with Proposed Decision at position 3 (ADR-002 C-03, unmodified). This ADR does not itself edit `UX-013B-Atlas-Component-Specification-Reasoning-Components.md`. It creates the authority a later Source Correction Plan governance amendment needs to remove or replace UX-013B's own §14 listing of "Recommendation" as Decision Workspace sequence item 11. Concept A (Atlas Recommendation) may continue to appear visually within relevant Workspaces (per its own UX-012 §28 definition) without becoming a canonical sequence stage — this was never in question and is unaffected by this ADR.

### R-09 — UX-013E Treatment

UX-013E's own "Recommendation vs. Atlas Recommendation Presentation" reconciliation may be cited only as historical design evidence of intent to eventually reconcile *some* Recommendation-adjacent naming question. It is not, and must not be treated as, the governing basis for this decision, because its claims rest on "Atlas Recommendation Presentation" as attributed to the absent, unconfirmed UX-013D volume (ADR-001's three-tier classification; ADR-002 C-05) — a different pairing than the one this ADR resolves (UX-012 §28's real, committed Atlas Recommendation versus UX-013B's Recommendation). This ADR stands entirely on currently committed, accepted evidence: UX-012 §28, UX-013B's Recommendation component and Reasoning Relationships sections, ADR-002 (C-02, its addendum, and C-03), and `UX-Architecture-Review-001.md`'s own Finding 5.3/H-2.

### R-10 — Non-Decisions

This ADR explicitly leaves unresolved: Scenario Analysis's canonical-sequence placement; Comparison's canonical-sequence placement; Concept B's exact visual layout; the number of candidate contents Atlas may generate at once; candidate regeneration behavior; any candidate-ranking algorithm; underlying model behavior; explanation-depth requirements; placement animation and timing; default expanded/collapsed presentation state; whether candidate content persists for any duration prior to acceptance and, if so, how long; historical retention policy; backend/database representation; exact multiplicity (whether more than one live candidate can coexist); the exact implementation-level property or state-label name used for "candidate content" in future component code; and whether Concept B should ever become a Domain Object (R-07 above declines to adopt one now, but does not foreclose a future, separately-justified decision to do so). None of these is decided by implication anywhere above.

## Canonical Terminology

| Term | Refers to | Status |
|---|---|---|
| Atlas Recommendation | Concept A (UX-012 §28) | Canonical, unchanged |
| Proposed Decision Candidate Content | Concept B (currently specified in UX-013B as "Recommendation") | Canonical, newly adopted by this ADR |
| Atlas Suggestion | The existing content-acceptance interaction pattern | Canonical, unchanged (ADR-002 C-02) |
| Proposed Decision | Canonical Decision Workspace sequence item 3 | Canonical, unchanged (ADR-002 C-03) |
| "Recommendation" (bare) | — | **Deprecated for Concept B**; must not be used for Concept B in any future correction |
| "Atlas Recommendation" (as a UX-013B component *variant* name) | — | **Deprecated**; collides with Concept A's real name; requires renaming in a future UX-013B correction |

## Lifecycle Governed

**Flow A — Atlas Recommendation (Concept A, unchanged, for completeness):** Atlas produces directional advice → the user accepts it as advice, dismisses it, or later acts upon it through a separate, distinct action. Acceptance does not by itself populate Proposed Decision unless a separate, explicit Atlas Suggestion interaction is independently invoked.

**Flow B — Proposed Decision Candidate Content (Concept B, newly clarified):**
1. Candidate content exists, Atlas-originated or user-originated, before insertion into Proposed Decision.
2. For Atlas-originated candidate content: Atlas presents it through the already-governed Atlas Suggestion interaction.
3. The user responds via whichever of Replace, Append, Partial Accept, or Dismiss the *governing source document for that specific field* already supports — this ADR invents no new response type and does not harmonize response sets across documents; any inconsistency in which responses a given source currently offers remains a separate, future source-correction question. For UX-013B's own Recommendation component specifically, this generic list corresponds to its own Accept / Modify / Decline vocabulary as follows: Accept corresponds to acceptance into Proposed Decision; Modify is a genuine subsequent edit of the already-accepted content, not Partial Accept (UX-013B's own text: Modify "enters Long-Form Editor mode... attribution updates to 'User modified'" — a post-acceptance edit, distinct in kind from selecting segments of not-yet-placed suggestion text); Decline corresponds to dismissal for the current session. This mapping does not redefine Partial Accept, Replace, or Append, and does not claim UX-013B supports response types it does not itself name — each source's own vocabulary remains governed by that source.
4. Accepted content enters Proposed Decision.
5. Provenance follows ADR-002 C-02 and its addendum exactly (Accepted/`atlas-accepted` state on Accept; `user-modified-from-atlas` only after a genuine subsequent edit; mixed-origin rules apply if append is the mechanism used).
6. Acceptance alone does not constitute a Decision (R-05).
7. The candidate content does not persist as a separate historical object once absorbed (R-07, R-10).

## Acceptance Semantics

Accepting Proposed Decision Candidate Content means: the candidate text is transferred into Proposed Decision via the existing Atlas Suggestion acceptance mechanism; the field transitions to `atlas-accepted` / "Atlas Suggested / User Accepted"; authorship is not transferred; only a subsequent genuine edit produces `user-modified-from-atlas`. This is identical in every respect to the already-governed Atlas-Suggestion-into-Proposed-Decision model (UX-012B's Decision Section, UX-012C's AI Interaction) — not a new acceptance model.

## Provenance Implications

None beyond what ADR-002 C-02 and its addendum already establish. This ADR applies that already-adopted model to a case (content originating from a component previously named "Recommendation") it was not previously known to cover; it does not alter the model itself.

## Domain-Object Implications

Neither concept is adopted as a Domain Object (R-07). No identifier, persistence schema, or backend representation is established by this ADR for either concept.

## Canonical-Sequence Implications

Concept B is confirmed not to be a canonical Decision Workspace sequence item (R-08). The canonical 13-item table (ADR-002 C-03) is unchanged. UX-013B's own §14 listing of "Recommendation" as item 11 is now understood to be an error requiring future correction, not a competing architectural claim.

## Consequences

### Positive

- Finding 5.3/H-2 — open since the original Architecture Review, never absorbed into ADR-002 — is now resolved.
- Phase 3D's Recommendation-related blocker is substantially narrowed: the identity question is settled; only the mechanical rename/removal correction and its governance amendment remain.
- The naming collision between UX-012's real "Atlas Recommendation" and UX-013B's reuse of that same term is identified and given a resolution path.
- No new Domain Object, no new provenance model, and no expansion of the canonical 13-item sequence was required — the resolution reuses existing, already-governed architecture in full.

### Negative

- UX-013B's Recommendation component, its "Atlas Recommendation" variant name, and its §14 sequence listing all now require a future source correction to align with this ADR — none of that correction is performed here.
- Until that correction lands, an authority split exists: this ADR states the correct terminology and relationships, while UX-013B's committed text still reads "Recommendation" and lists it as a sequence item, mirroring the same kind of temporary split ADR-002 itself already accepted as a trade-off for its own six resolutions.

### Accepted Trade-offs

- This ADR accepts leaving Scenario Analysis and Comparison unresolved rather than delaying the (separable, evidence-supported) Recommendation question until every Phase 3D component is settled.
- This ADR accepts that "Proposed Decision Candidate Content" is a longer canonical term than the single word it replaces, in exchange for eliminating the naming collision and avoiding any implication of object identity.

## Non-Decisions

See R-10, above (this ADR's authoritative non-decisions list).

## Source-Correction Implications

A future, separately-authorized Source Correction Plan governance amendment is required before any UX-013B source edit may occur, to: (1) rename UX-013B's Recommendation component and its "Atlas Recommendation" variant per this ADR's canonical terminology; (2) remove "Recommendation" from UX-013B's §14 Decision Workspace sequence listing (item 11), with a correction notice disclosing the removal and citing this ADR; (3) add or adjust any cross-reference in UX-013B (e.g., its Dependency Chain diagram) to reflect the corrected terminology, preserving the diagram's own derivation logic unchanged. This ADR does not perform, and does not itself authorize, any of these three edits.

## Validation Criteria

A future correction implementing this ADR must be checked against: the canonical 13-item sequence remains unchanged; Proposed Decision remains at position 3, unchanged; Atlas Suggestion mechanics remain unchanged; ADR-002's mixed-origin rules remain unchanged; user ownership of Proposed Decision (authorable without any candidate content) remains unchanged; the Decision boundary (acceptance ≠ commitment) remains unchanged; no Domain Object is introduced; Scenario Analysis's and Comparison's status remain untouched; no UX source specification is edited by this ADR itself; UX-013E is not cited as governing authority for this specific question; the naming collision is resolved (no future document uses "Recommendation" or "Atlas Recommendation" for Concept B); both concepts are clearly, separately defined wherever cited; and sufficient authority now exists for the Phase 3D governance amendment named above.

## Supersession

This ADR supersedes no prior ADR. It does not reopen, revise, or reinterpret any part of ADR-001 or ADR-002 — it applies both, unchanged, to a question neither previously resolved. It resolves `UX-Architecture-Review-001.md`'s Finding 5.3, listed there as H-2 — a finding never included among ADR-002's six Critical (C-01–C-06) resolutions.

## Open Questions

- **Should Scenario Analysis's and Comparison's canonical-sequence status be resolved by a similarly-scoped, dedicated ADR, or folded into a single future "Phase 3D architectural decisions" document alongside this one's own implementation?** Not decided here; either approach is compatible with this ADR.
- **What is the exact future property/state-label name for Concept B in implementation code?** Left to the future source-correction and, eventually, engineering-implementation tasks (R-10).
- **Does any other committed document, beyond those examined, use "Recommendation" or "Atlas Recommendation" in a way this ADR's terminology now conflicts with?** Not exhaustively re-verified beyond the documents this ADR's own evidence base covers (UX-012, UX-012B, UX-012C, UX-013B, UX-013E, ADR-002, both review documents); a future Phase 5-style cross-reference sweep, mirroring the Source Correction Plan's own established pattern, would be the appropriate mechanism to check.

## Next Required Task

**A Source Correction Plan governance amendment authorizing a Phase 3D (or newly-split sub-phase) source correction to UX-013B**, implementing this ADR's R-02 (renaming) and R-08 (sequence-item removal), following the same amendment-then-implementation-then-independent-review pattern already used for Phase 2B in this same program. This ADR does not itself perform or authorize that amendment.

## Working Tree Verification

**Branch:** main
**HEAD at time of this ADR:** `c0a122d14b77fbead63e6464f8f971a724217db6` ("docs(ux): correct Phase 2B C-02 source specifications") — unchanged throughout this task.
**Files created:** `docs/atlas_ux/governance/ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` (this document). No new directory was required.
**Files modified:** none. No UX source document under `docs/atlas_ux/*.md` was changed. `ADR-001-Missing-Source-Volume-Governance.md` and `ADR-002-Critical-UX-Architecture-Resolutions.md` were not modified. `Atlas-UX-Source-Correction-Plan.md` was not modified. Neither `UX-Architecture-Review-001.md` nor `UX-Critical-Findings-Resolution-Design-001.md` was modified.
**Staged files:** none.
**Untracked files:** `docs/atlas_ux/governance/ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`.

No commit was made.

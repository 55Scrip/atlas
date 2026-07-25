# ADR-002 — Critical UX Architecture Resolutions

## Status

Accepted

## Context

`UX-Architecture-Review-001.md` reviewed the full eighteen-document Atlas UX baseline imported at commit `f2d5adbb7cd260853f56197e35fcc776caf85a78` and identified six Critical findings — contradictions serious enough that two conformant implementers, each following a different one of the committed governing documents, would build genuinely different, incompatible versions of Atlas's Decision Workspace and component library. The six findings were: an information-hierarchy conflict between UX-012 and UX-012A over where Challenges/contradiction content ranks; an AI-authorship-transfer contradiction across UX-012, UX-012B, and UX-013B over when Atlas-originated content becomes attributed to the user; a three-way disagreement between UX-009A, UX-012, and UX-013B over the Decision Workspace's own canonical section order; a contradiction between UX-009A and UX-012/UX-012C over how many fields must be complete before a Decision can be recorded; the discovery that UX-013E — the intended final assembly of the component library — cites UX-013C and UX-013D as governing source volumes that do not exist anywhere in the committed repository; and an accessibility contradiction in which the Decision Workspace's own specifying documents (UX-009A, UX-010) describe a "disabled" Record Decision button in terms that would violate their own focus-announcement requirement if implemented with the native HTML `disabled` attribute.

`UX-Critical-Findings-Resolution-Design-001.md` was produced specifically to resolve each of these six findings as one explicit, evidence-traced, canonical decision — before any source document is corrected and before any component implementation begins — using only the eighteen committed documents, the Architecture Review itself, and ten stated governing decision principles, and explicitly without inferring the content of the two absent volumes anywhere in its reasoning.

`ADR-001-Missing-Source-Volume-Governance.md` separately formalized the general governance principle this project applies whenever an assembling document cites a source volume that does not exist — adopting, as a permanent rule and not a one-time fix, that missing sources are never fabricated, that provenance gaps are closed only through honest new authorship, and that unsupported and partially-corroborated claims must remain explicitly, and separately, distinguished from settled fact.

This ADR is the formal acceptance record for the six specific resolutions the Resolution Design produced, and it is the specific application of ADR-001's general rule to the one concrete case (UX-013E's citation of UX-013C/UX-013D) that prompted ADR-001 in the first place.

**The six resolutions are approved together, as one coordinated decision set, and must not be applied selectively.** The Resolution Design's own Section 9 (Cross-Finding Consistency Check) establishes real, load-bearing dependencies between them: C-06's "navigate to the first unmet required field" behavior is only meaningful once C-04's completion matrix defines what "unmet" means; C-01's Challenges-at-Level-4 ranking is what justifies C-03's placement of the Challenges section as always-present and never conditional; and C-05's own long-term resolution — any future, genuinely-authored UX-013C/UX-013D-equivalent specification — depends on C-01, C-02, C-03, C-04, and C-06 already being settled, since that future work would otherwise have to reference an information hierarchy, authorship model, section order, completion gate, and disabled-control contract that were still in dispute. Adopting some of the six now and deferring others would reintroduce exactly the contradictions this decision set exists to close — for example, adopting C-03's section order without C-01's hierarchy resolution would leave the Challenges section's own visual priority undefined even as its position in the flow became settled.

## Decision

The following six resolutions, as fully specified in `UX-Critical-Findings-Resolution-Design-001.md`, are formally adopted.

### C-01 — Information Hierarchy

UX-012A's content-importance hierarchy is adopted as canonical, in place of UX-012's own Level 2 and Level 4 definitions, which are corrected; UX-012's Levels 1, 3, 5, and 6 are retained unchanged, since both documents already substantively agree on those four.

**The canonical hierarchy:**

| Level | Name | Semantic meaning | Typographic role |
|---|---|---|---|
| 1 | Primary Conclusion or Decision | The single most important statement in the current Workspace or Section scope — the decision statement in the Decision Workspace, the thesis or portfolio assessment in Investment/Portfolio Workspace, the most urgent signal on the Dashboard. | Largest type, greatest surrounding space, first in reading order. |
| 2 | Material Implication | Why the Level 1 statement matters — its consequence or significance for the user's situation. Not supporting evidence; the stakes. | Medium-emphasis type, clearly subordinate to Level 1, placed immediately below it. |
| 3 | Supporting Reasoning | The strongest factors, evidence, or logic that make the Level 1 statement credible. | Standard body text, comfortable reading scale. |
| 4 | Challenges, Uncertainty, and Contradiction | What weakens, complicates, or contradicts the Level 1 statement. Receives deliberate design attention: must be visible and readable, never buried, suppressed, or defaulted to collapsed-and-hidden, though it does not compete with Level 1 for primary emphasis. | Standard body text, distinguished by semantic border/color treatment and structural position, not by size alone. Explicitly acknowledged by the user when severity is Material or Blocking. |
| 5 | Reference Detail | Evidence, source material, historical records, granular assumptions, collapsed previews, and other content reached when seeking depth, not encountered first. | Reduced-emphasis, frequently behind expand/collapse, never in the primary reading path. |
| 6 | System Metadata | Timestamps, version numbers, identifiers, save state, system-generated labels. | Smallest text in the system, visible only when needed. |

**Challenges and contradiction content is fixed permanently at Level 4** and must never be reduced to, or treated as equivalent to, Level 6 generic system metadata. This is not a stylistic preference: Atlas's own stated product identity depends on counter-evidence remaining genuinely visible, and this resolution exists specifically to prevent an implementation that would, under UX-012's uncorrected Level 4 definition, have left Challenges content with no defined hierarchy level at all.

UX-012's former "Structural Element" concept (Level 2 in UX-012's own, now-superseded text) becomes a **cross-cutting typographic convention, not a competing hierarchy level**: a section heading, category label, or named Workspace area is not itself a rank in the hierarchy — it labels whatever content follows it and inherits that content's own level for visual weight. A heading over Level 1 content renders with Level-1-appropriate prominence; a heading over Level 5 reference detail renders correspondingly quieter. No content is ever "Level 2" merely because it happens to be a heading.

**Recursion rule:** the hierarchy applies at both Workspace and Section scope. A Workspace has exactly one Level-1 statement overall; a major Section within it may independently have its own local Level 1 (its own most-important statement), which is itself Level-2-through-5 content relative to the Workspace's own Level 1. A Section's internal hierarchy never competes with the Workspace's own top-level Conclusion for the single Level-1 slot.

### C-02 — AI Authorship and Provenance

The canonical model:

- **Acceptance alone does not transfer authorship.** When a user accepts an Atlas Suggestion with no further edit, the field is attributed as Atlas-originated and user-accepted — not as user-authored.
- **Accepted, unedited Atlas content is represented with the display label "Atlas Suggested / User Accepted."**
- **Any subsequent user edit to the field's content, however small, transfers current authorship to the user**, updating the display label to "User Authored."
- **No confirmation prompt is required for that transfer.** The label updates automatically on the edit itself; the user is never interrupted to confirm they have just edited something they visibly just edited.
- **Provenance is retained permanently, regardless of the currently-displayed label.** The original Atlas-generated text, the moment it was offered, and the moment it was accepted are never deleted from the record. "Silently cleared" — which this model forbids — refers specifically to destroying this underlying provenance record; it does not mean the currently-displayed summary label can never change.
- **Recording never itself transfers authorship.** Record Decision locks whatever attribution state each field already holds at that moment into permanent Historical Record status; it does not itself convert any field to "User Authored," and a field left as "Atlas Suggested / User Accepted" at the moment of recording is recorded permanently with exactly that attribution.
- **Historical records preserve both the current (frozen) attribution label and the original provenance** (the original Atlas text, acceptance timestamp, and edit timestamp, where applicable) — an amendment made after recording is itself a new, additively-recorded event with its own independent attribution; it never alters the original recorded field's attribution.

Canonical API properties supporting this model: `authorship: 'atlas' | 'user' | 'mixed'` (the currently-displayed label); `hasAtlasOrigin: boolean` (permanently true once any Atlas-generated content ever touched the field, regardless of the current label); `originalAtlasText: string | null`; `acceptedAt: timestamp | null`; `editedAt: timestamp | null`.

This resolution rejects, specifically, UX-012B's rule that Accept alone (with zero edits) transitions a field to "user-modified-from-atlas" — that rule is not adopted and directly contradicts the model above.

### C-03 — Decision Workspace Sequence

The canonical thirteen-section sequence, adopted from the mutually-consistent Decision Workspace lineage (UX-009, UX-009A, UX-010, UX-011 — four documents that already agree with each other exactly), in preference to UX-012's own single, differently-ordered "reasoning sequence," which additionally imports a section ("What Changed") that appears nowhere in the Decision Workspace's own dedicated documents and is, instead, the Investment Workspace's own third section.

**Proposed Decision remains early in the flow, at position 3, as a testable working hypothesis** — explicitly, per UX-009's own framing, "a starting point, not a conclusion," stated before Supporting Factors, Challenges, Opportunity Cost, Portfolio Consequences, Assumptions/Monitoring/Invalidation, Implementation, and Review Plan test it, and only formalized afterward, at position 12, into the Final Decision Card. **"What Changed" is not adopted as a standalone Decision Workspace section** — its appearance in UX-012's sequence is treated as a templating artifact carried over from the Investment Workspace, not as an independent design decision for the Decision Workspace.

**The full canonical ordered section list:**

| # | Canonical name | Purpose | Presence | Default expansion | Ownership | Produces recorded content? | Relationship to neighbors |
|---|---|---|---|---|---|---|---|
| 1 | Current Conclusion | Establish shared understanding before the decision begins | Always | Expanded | Atlas-generated, read-only | No | Grounds everything that follows |
| 2 | Why a Decision Is Required | State the specific trigger for this decision moment | Always | Expanded | Atlas-generated, read-only | No | Follows from Current Conclusion |
| 3 | Proposed Decision | The user's own stated intention, in their own words, as a working position | Always | Expanded | User-owned (blank until authored) | Feeds Final Decision Card | Tested, not finalized, by Sections 4–11 |
| 4 | Decision Rationale | The user's own reasoning for the Proposed Decision | Always | Expanded | User-owned | Feeds Final Decision Card (Primary Reason) | Elaborates Section 3 |
| 5 | Supporting Factors | What supports the Proposed Decision | Always | Expanded | Mixed (Atlas-surfaced, user-editable) | No | Precedes Challenges by design |
| 6 | Challenges | What challenges the Proposed Decision — Level 4 content, never defaulted to hidden | Always | Expanded | Mixed | No, but severity acknowledgment may be recorded | Directly follows Supporting Factors |
| 7 | Opportunity Cost | What is foregone by the Proposed Decision | Always | Expanded | Mixed | No | Follows Challenges — cost is assessed after both sides of the case are seen |
| 8 | Portfolio Consequences | What this decision means for the portfolio | Conditional (portfolio-level) | Expanded for portfolio-level, collapsed otherwise | Mixed | Conditionally, via required acknowledgment | Follows Opportunity Cost |
| 9 | Assumptions, Monitoring and Invalidation | The conditions this reasoning depends on, what Atlas will watch, what would invalidate the decision | Always (subsections may collapse) | Expanded | Mixed | Yes — Monitoring and Invalidation Condition | Precedes Implementation |
| 10 | Implementation Plan | How the decision would be executed | Conditional (per C-04) | Expanded when present | User-owned | Yes, when present | Precedes Review Plan |
| 11 | Review Plan | What should trigger re-examination | Always, unless explicitly overridden (per C-04) | Expanded | User-owned | Yes — Review Condition | Precedes Final Decision Card |
| 12 | Final Decision Card | The six-field structured, permanent record | Always | N/A (form) | User-owned, locks on recording | Yes — the canonical recorded object | Assembles content from Sections 3–11 |
| 13 | Record Decision | The submission action | Always | N/A | User-driven only; cannot be triggered by Atlas | Triggers recording of Section 12 | Terminal |

**Shorter component names from later design-system documents are retained where semantically equivalent**, since naming and sequencing are independent questions: "Supporting Factors" and "Challenges" (UX-012/UX-013B naming) are adopted over "What Supports This Decision"/"What Challenges This Decision" (UX-009/UX-009A naming), and "Final Decision Card" (UX-012/UX-012B naming) is adopted over "Final Decision Summary" (UX-009/UX-009A naming) — in both cases because the shorter names already match the actual named components (UX-013B) that populate these sections.

### C-04 — Record Decision Completion Gate

The canonical completion model, stated fully here so this ADR is independently understandable without cross-referencing the Resolution Design's own Section 6:

**Universal hard-blocking minimum, no exceptions:** Decision Statement and Primary Reason. A Recorded Decision without a stated reason cannot support future review under any circumstance; this is a floor, not a ceiling, and is required for every Decision Workspace exit via Record Decision regardless of decision type.

**Conditionally hard-blocking, by decision type:**

| Decision type | Implementation Plan required? | Review Condition required? | Portfolio Consequences acknowledgment required? |
|---|---|---|---|
| Action decision (Increase / Reduce / Exit / Initiate) | Yes | Yes, unless explicitly overridden | Yes if portfolio-level; no if single-position |
| No-action / Hold decision | No — nothing to implement | Yes, unless explicitly overridden | As above |
| Deferred decision | No — deferral is itself the implementation | Yes — this is the one field a deferred decision cannot omit | As above |
| Review outcome | Conditional — only if the review concludes with a new or amended action | Yes, unless explicitly overridden | As above |
| Portfolio-level decision | Per action/no-action rule above | Yes, unless explicitly overridden | Yes, always |
| Conditional implementation decision | Yes — the condition itself is the implementation plan | Yes, unless explicitly overridden | As above |

**The explicit override path:** Review Condition is treated as effectively universal, since Atlas's own philosophy of ongoing monitoring argues against treating future review as optional — but a small number of decisions (a full, final exit with no remaining stake to monitor) genuinely have nothing left to review. Rather than making the field always-required or silently optional, an explicit, single-click, logged override ("No further review is needed for this decision because ___") stands in place of a populated Review Condition, and the override text itself becomes the recorded content — the record is never silently thinner than a genuine review requirement would produce.

**Soft friction, never hard blocking:** unacknowledged Challenges. A Material or Blocking-severity Challenge must be shown, and for Blocking severity must be explicitly acknowledged before recording — but acknowledgment means "I have seen and considered this," never "I agree with this." Atlas never blocks recording because the user's own judgment differs from Atlas's own surfaced concern.

**Semantic completeness and interface validation are distinct concerns.** This section defines *what* must be true of a Decision record for it to be complete. *How* that requirement is presented and enforced in the interface — field markers, the Record Decision button's own state — is governed separately by C-06, which depends on this section's completion matrix to know what "unmet" means.

### C-05 — Missing Source Governance

ADR-001's Option F governance model is adopted as the governing application to UX-013E specifically:

- **Structural separation along the trust boundary.** UX-013E's Foundation- and Reasoning-tier reconciling content (its classification, naming, and dependency decisions for material independently traceable to the present UX-013A and UX-013B) remains canonical. Its Decision-, Monitoring-, AI-Collaboration-, and Metadata/System-tier content — the material attributed to the absent UX-013C and UX-013D — is separated out and redesignated, pending genuine specification.
- **Three-tier claim classification**, not a single blanket status: (1) content independently confirmed by other committed documents (e.g., the broad existence and purpose of Monitoring Condition or Atlas Warning, as named in UX-012 itself) may be cited with that confidence; (2) content unconfirmed anywhere outside UX-013E's own secondhand account (exact component counts, exact prop names, exact variant structures, exact merge decisions) is explicitly marked unconfirmed and is not implemented as canonical; (3) content is marked to-be-authored, naming the eventual, genuinely new specification work as its own scheduled completion, not an indefinite deferral.
- **No fabricated source history.** UX-013C and UX-013D are never reconstructed, back-filled, or presented as having existed prior to this point.
- **No silent deletion of provenance warnings.** The disclosure that this content's grounding is unconfirmed is preserved exactly as long as the content remains unconfirmed; it is never edited away to make the finding appear resolved.
- **Genuine new UX-013C and UX-013D work, when undertaken, must be honestly authored and dated** — citing only documents that exist and are checkable at the time of writing, following the identical process UX-013A and UX-013B themselves used, never claiming retroactive authorship or presenting itself as recovered history.
- **Current unconfirmed granular claims cannot be implemented as canonical specifications.** Decision, Monitoring, and AI-Collaboration/Metadata component implementation remains correctly withheld until genuinely grounded, exactly as the Architecture Review's own implementation-readiness assessment already concluded.

ADR-001 remains the general rule, applicable to any future assembling document in any part of the Atlas documentation corpus that cites a source volume that does not exist; this ADR (ADR-002) applies that general rule to the one concrete instance — UX-013E's citation of UX-013C and UX-013D — that prompted ADR-001's adoption.

### C-06 — Unavailable Primary Action Accessibility

The canonical interaction contract for the Record Decision action, and any future primary action following the same "unavailable but explained" pattern:

- **`aria-disabled="true"` is used, never the native HTML `disabled` attribute**, for the Record Decision control while any C-04 required-field condition is unmet.
- **The control remains permanently focusable and permanently in the natural tab order**, at every point in the flow, including while incomplete — this is a deliberate decision, not an oversight, given the consequence of this specific action.
- **Blocked activation moves focus to the first unmet required field** (per C-04's completion matrix) and re-announces the specific, current reason recording is unavailable, rather than producing no response at all.
- **The reason for unavailability is exposed visually** (reduced-emphasis styling, unchanged from existing visual specification) **and to assistive technology** via `aria-describedby` pointing to the specific, current explanation.
- **State changes are announced** — when the control transitions from unavailable to available, or when the specific blocking reason changes because a field was completed — via the same announcement mechanism already specified for this interaction, unchanged in behavior; only the underlying markup mechanism changes.
- **Keyboard, pointer, mobile, and touch behavior are equivalent**: the same `aria-disabled` state, the same navigate-to-first-incomplete-field response to activation, and the same visual treatment apply across all input modalities, with no special-casing for touch.
- **No inaccessible focus-announcement contradiction remains.** The native `disabled` attribute — which would remove the control from the tab order and make it impossible to satisfy the existing requirement that its explanation be announced on focus — is never used for this control under any circumstance.

## Cross-Resolution Dependencies

- **C-01 affects C-03's visual and semantic hierarchy.** C-03's placement of the Challenges section as always-present and never conditional is justified by, and depends on, C-01's fixing of Challenges at Level 4 as content that must never be buried.
- **C-02 affects historical integrity and component state.** C-02's provenance-retention rule is a direct application of the additive-only historical model; any future historical-integrity or component-state work must preserve C-02's distinction between the currently-displayed attribution label and the permanently-retained provenance record.
- **C-04 governs C-06's unavailable-action behavior.** C-06's "navigate to the first unmet required field" response has no defined target without C-04's completion matrix; a future correction to C-04's matrix automatically changes what C-06 navigates to, with no change required to C-06's own contract.
- **C-05 constrains which Decision, Monitoring, AI, and Metadata specifications may be treated as canonical.** No claim in these tiers may be implemented as settled fact merely because it appears inside UX-013E; only content independently corroborated elsewhere, or genuinely newly authored per ADR-001's model, qualifies.
- **Source correction must preserve all six simultaneously.** No future correction to any one of UX-012, UX-012A, UX-012B, UX-009A, UX-010, UX-013B, or UX-013E may resolve its own local contradiction in a way that reintroduces a conflict with any of the other five resolutions adopted here.

## Authority

- **ADR-002 is the authoritative decision record for the six resolutions** described above.
- **`UX-Critical-Findings-Resolution-Design-001.md` remains the detailed rationale and implementation reference** — the evidence quotations, rejected alternatives, and downstream-change identification behind each resolution live there and are incorporated by this ADR's Decision section, not restated in full.
- **`UX-Architecture-Review-001.md` remains the evidence record** — the original discovery, quotation, and severity grading of all six findings, and of every other finding in the broader review, continues to be authoritative for that evidentiary record.
- **ADR-001 remains the general governance authority for missing-source cases** generally, beyond this one instance.
- **Existing UX source documents remain historically unchanged until separately corrected.** No document under `docs/atlas_ux/*.md` is altered by this ADR's adoption.
- **Where an existing UX source document conflicts with this ADR, this ADR governs future correction and implementation** — the source document is not retroactively "wrong" in a historical sense (it remains an accurate record of what it said, when), but it is no longer the operative authority on the specific point this ADR resolves, pending the correction described in the Resolution Design's own Source Correction Plan.

## Consequences

### Positive

- Implementation can proceed on Foundation- and Reasoning-tier work today with one settled, internally-consistent set of rules, rather than a choice between conflicting source documents.
- The single highest-risk ambiguity in the entire review (Challenges' hierarchy placement) is closed.
- The Decision Workspace's own core information architecture and its most irreversible action's validation logic are both now unambiguous.
- The specific accessibility defect that would have made the Record Decision button's own stated requirement impossible to satisfy is closed.
- The missing-source problem is handled by a durable, honest, general rule rather than a one-off patch.

### Negative

- Six source documents (UX-012, UX-012A, UX-012B, UX-009A, UX-010, UX-013B) and one assembled document (UX-013E) now require a correction pass before they are internally consistent with the resolutions adopted here — none of that correction work is performed by this ADR.
- Until that correction lands, a genuine authority split exists: this ADR and its supporting Resolution Design state the correct semantics, while the affected source documents still contain the superseded, contradictory text.
- Decision, Monitoring, and AI-Collaboration/Metadata component implementation remains delayed pending genuinely new UX-013C/UX-013D-equivalent authorship, which is real, unavoidable future work, not yet begun.

### Accepted Trade-offs

- This ADR accepts the temporary inconvenience of an authority split (accepted decision vs. as-yet-uncorrected source text) as preferable to either delaying this decision until every source document is corrected, or silently treating the uncorrected source text as still-authoritative.
- This ADR accepts that closing C-05 fully requires real authorship labor with no defined timeline yet, in preference to lowering the evidentiary bar to make Decision/Monitoring/AI-Collaboration implementation appear unblocked before it genuinely is.

## Source Correction Requirement

Acceptance of this ADR authorizes **planning** for source correction. It does not itself authorize **performing** any source correction — no document under `docs/atlas_ux/*.md` is modified by this ADR, and none should be modified as a direct consequence of this ADR's adoption alone.

A separate Atlas UX Source Correction Plan is required before any correction is performed, and must define:

- the exact files to change (at minimum: UX-012, UX-012A, UX-012B, UX-009A, UX-010, UX-013B, and UX-013E);
- the exact conflict each correction resolves, traced to its specific C-0N resolution above;
- the correction order (the Resolution Design's own Section 11 already establishes that UX-012 — as the already-authoritative assembled document — is corrected first, followed by UX-012A's supersession marking, UX-012B, UX-009A/UX-010, UX-013B, and only then UX-013E, since UX-013E's own eventual re-reconciliation depends on every other correction landing first);
- how supersession and changelog notes are handled for each correction, consistent with this ADR's own requirement that no document's body text be silently rewritten to erase the fact that a contradiction once existed;
- the UX-013E migration sequence specifically (the structural split and three-tier classification required by C-05), sequenced last among the source corrections for the reason given above;
- how each correction is validated afterward — at minimum, confirming the corrected document no longer contradicts any of the other five resolutions, per the Cross-Resolution Dependencies above.

## Implementation Constraint

**Implementation may not treat conflicting source text as authoritative merely because it remains unchanged in Git.** The fact that UX-012's uncorrected Level 4 definition, or UX-009A's uncorrected four-field completion rule, or any other superseded passage identified in the Resolution Design still exists, unedited, in its committed file is not evidence that it still governs. It does not.

Until source correction is complete:

- **This ADR (ADR-002) governs resolved semantics** — the six decisions stated above are the operative rules for Foundation- and Reasoning-tier implementation, and for any Decision-tier work not itself blocked by C-05.
- **ADR-001 governs provenance gaps** — any claim touching Decision, Monitoring, or AI-Collaboration/Metadata content must be checked against ADR-001's three-tier classification before being treated as implementable.
- **The Resolution Design provides detailed operational interpretation** — where this ADR's own summary leaves an implementation question open, `UX-Critical-Findings-Resolution-Design-001.md` is the next-level authority, before falling back to the original, uncorrected source documents.
- **Unsupported granular UX-013E claims remain non-canonical**, exactly as C-05 and ADR-001 establish, regardless of how complete or authoritative UX-013E otherwise appears.

## Supersession

- **This ADR supersedes no prior ADR.**
- **It depends on ADR-001**, applying that ADR's general governance model to the specific case of UX-013E's citation of UX-013C and UX-013D.
- **It resolves the six Critical findings identified in `UX-Architecture-Review-001.md`** — C-1 through C-6 as numbered there, referred to as C-01 through C-06 in the Resolution Design and in this ADR.

## Open Questions

- **What mechanism will verify, going forward, that source corrections performed under the future Source Correction Plan actually match the six resolutions adopted here**, rather than introducing a new, unreviewed variation during the editing process itself? This ADR requires validation after each correction (see Source Correction Requirement above) but does not itself specify the review mechanism for that validation.
- **What is the ownership and timeline for the Source Correction Plan and the eventual genuine UX-013C/UX-013D authorship?** Neither this ADR nor ADR-001 assigns an owner or a deadline; both establish that the work must happen and must be honest when it does.
- **Does any other Atlas document, beyond the seven identified here, contain text that conflicts with one of the six resolutions and was not surfaced by the original Architecture Review's scope?** The Architecture Review was scoped to the eighteen committed UX documents as a set; whether any conflicting text exists in documentation outside that scope was not checked and remains open.

## Next Required Task

**Create the Atlas UX Source Correction Plan.**

No source correction is begun within this ADR. The next task is to produce the Source Correction Plan described under "Source Correction Requirement" above — defining exact files, exact conflicts, correction order, supersession/changelog treatment, the UX-013E migration sequence, and post-correction validation — as its own, separately-authorized document. Only once that plan itself is produced and reviewed should any actual correction to a UX source document be performed.

## Working Tree Verification

**Branch:** main
**HEAD:** `3f06e0375b8ae14ec9e34bb2e1ab60e711a8ac85` ("docs: review and govern Atlas UX architecture") — unchanged throughout this task.
**Files created:** `docs/atlas_ux/governance/ADR-002-Critical-UX-Architecture-Resolutions.md` (this document). No new directory was required — `docs/atlas_ux/governance/` already existed.
**Files modified:** none. No UX source document under `docs/atlas_ux/*.md` was changed. `ADR-001-Missing-Source-Volume-Governance.md` was not modified. Neither `UX-Architecture-Review-001.md` nor `UX-Critical-Findings-Resolution-Design-001.md` was modified.
**Staged files:** none.
**Untracked files:** `docs/atlas_ux/governance/ADR-002-Critical-UX-Architecture-Resolutions.md`.

No commit was made.

## Addendum — C-02 Mixed-Origin Single-Field Content (2026-07-25)

### Status

Accepted, as an addendum to C-02. This addendum does not reopen, revise, or supersede any text under "C-02 — AI Authorship and Provenance" above, which remains unchanged and remains the governing rule for the case it already resolved. This addendum resolves a narrower, previously-undefined case that C-02's own canonical API property list named but never operationally defined.

### Context

A read-only scope reassessment of `UX-010-Decision-Workspace-Interaction-Microinteraction-Specification.md` (Section 4, "Atlas Suggestion Model," the passage "Accept: Atlas text replaces or appends to the user's text. A modification indicator appears: 'Modified with Atlas suggestion.'") and a matching passage in `UX-011-Decision-Workspace-Visual-Design-Polish-Specification.md` (Section 10, "AI Suggestion Presentation," line 311) found that both documents describe two distinct outcomes of accepting an Atlas suggestion — the suggestion **replacing** the field's content, and the suggestion being **appended** to pre-existing user-authored content in the same field — without distinguishing the two, and describe the "modification indicator" as firing on Accept alone in both cases.

The replace case is already governed by C-02 above, and the wording describing it as producing "modification"/authorship transfer on Accept alone is a straightforward instance of the pattern C-02 already rejects (matching the defect already corrected in `UX-012B-Atlas-Design-System-Components-Reusable-Patterns.md` and `UX-012C-Atlas-Design-System-Interaction-Navigation-Responsive-Behavior.md`, whose own Accept passages, for the identical feature, were corrected under Phase 3 and Phase 3C of the Atlas UX Source Correction Plan).

The append case is not resolved by the existing C-02 text. C-02's own canonical API properties (above) already name `authorship: 'atlas' | 'user' | 'mixed'` — the `'mixed'` value is present in that enumeration but its trigger, lifecycle, display label, and provenance requirements were never separately defined anywhere in this ADR, the Resolution Design, or any corrected UX source document. A dedicated architectural decision task, informed by a fresh reading of this ADR, the Atlas UX Source Correction Plan, both review documents, UX-010, UX-011, UX-012B, UX-012C, UX-013B, and UX-013E, and a corpus-wide search for every relevant term, concluded that existing authority plus first-principles reasoning is sufficient to define this case without inventing new architecture, and that the result should take the form of an addendum to C-02 rather than a new ADR, since every element of the decision below is inherited directly from C-02's own already-accepted model.

This addendum exists because `mixed` was already named but not yet defined for this specific, single-field append case — not because C-02 as originally written was wrong about anything it actually decided.

### Decision

#### Semantic definition of `mixed`

Authorship and provenance remain **field-level**, exactly as in the unamended C-02 model above. This addendum does not adopt token-level, character-level, span-level, or fragment-level provenance of any kind.

A field may nonetheless contain content contributed by more than one origin. The field-level authorship value `mixed` means: **the field's current value contains both a user-authored component that existed before the current Atlas suggestion was accepted, and an Atlas-suggested component that was appended through Accept and has not subsequently been genuinely edited.** The exact textual boundary between the two components is not retained and is not claimed by this value.

`mixed` does **not** mean: uncertain authorship; collaborative or real-time joint editing; wholly user-authored content; wholly Atlas-authored content; or `user-modified-from-atlas`.

#### Replace behavior (unchanged)

When Accept causes Atlas text to **replace** the field's current content, the resulting state is unchanged from the existing C-02 model above: Atlas-originated content, accepted by the user, not subsequently edited. **Canonical user-facing label: "Atlas Suggested / User Accepted."** This addendum makes no change to this case.

#### Append behavior (newly defined)

When Accept causes Atlas-suggested text to be **appended** to pre-existing user-authored text already present in the same field, the resulting state is `mixed`, accepted, unedited. The field contains two known origins — the pre-existing user-authored content and the accepted Atlas-suggested content. The field must not be labeled as wholly Atlas-originated. The field must not be labeled as wholly user-authored. The field must not be labeled `user-modified-from-atlas` merely because Accept occurred.

**Canonical user-facing label for this state: "User Authored / Atlas Suggestion Accepted."** This label means: some current field content originated with the user; some current field content originated with Atlas; the Atlas portion was accepted; no genuine subsequent edit has yet occurred. This exact wording is adopted following the corpus's own established convention for disclosing dual-origin content (`UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md`'s own state-composition rule for "AI-generated + user-edited" content: "Atlas generated / User modified") and directly reuses the vocabulary of the already-canonical "Atlas Suggested / User Accepted" label. A corpus-wide search performed as part of the decision that produced this addendum found no existing, already-adopted canonical label for this exact case; the following are explicitly rejected as the canonical label, and must not be used in its place: "Modified with Atlas suggestion" (overstates editing — this is precisely the wording this addendum exists to correct); "User edited from Atlas" (overstates editing); "Atlas-assisted" (under-specifies which content originated where and omits acceptance state); "User + Atlas" (under-specifies acceptance versus editing); "Mixed Origin" (accurate but does not, by itself, distinguish acceptance from editing or match the corpus's own compound-label convention).

#### Accept-versus-edit distinction

Accept is consent to adopt Atlas-suggested content. **Accept alone does not constitute genuine editing.** This applies identically whether Atlas text replaces the field content or is appended to existing user-authored content — append is a strictly gentler transformation of the field's prior content than replace (it preserves rather than discards the user's own prior text), and since Accept-by-replacement already does not transfer authorship under the unamended C-02 model above, there is no principled basis for Accept-by-append to be treated differently. Accept alone, by either mechanism, must never produce "User Authored," `user-modified-from-atlas`, or any label implying genuine user editing occurred.

#### State transitions

| Path | Sequence |
|---|---|
| Replace | Atlas suggestion offered → Accept with replacement → **Atlas Suggested / User Accepted** → genuine later edit → `user-modified-from-atlas` |
| Append | Atlas suggestion offered → Accept with append into pre-existing user-authored content → **mixed ("User Authored / Atlas Suggestion Accepted")** → genuine later edit → `user-modified-from-atlas` |

Any genuine user edit occurring while a field is in the `mixed` state transitions it to `user-modified-from-atlas`, regardless of whether the edit touches the pre-existing user-authored portion, the appended Atlas portion, both, or the field as a whole without regard to which portion is which. This reuses the existing edit-triggered transition rule from the unamended C-02 model above without modification — that rule was never scoped to require the pre-edit state to be purely Atlas-originated, and no new, fragment-aware transition logic is introduced or required.

Both accepted states (`Atlas Suggested / User Accepted` and `mixed`) may later transition through the existing Recorded → Historical lifecycle (per the unamended C-02 model above) without loss of provenance, exactly as already governed for the replace case.

#### Minimum provenance requirements

For the `mixed` state, the minimum provenance record must semantically preserve: the field value immediately before Accept; the field's authorship/provenance state immediately before that same Accept action; the Atlas suggestion text that was accepted; the resulting field value after append; the acceptance timestamp; an edit timestamp, initially unset until a genuine edit occurs; and the field's current authorship/provenance state. No token ranges, character offsets, text fragments, or per-segment ownership metadata are required or introduced.

The property names below are illustrative, following the naming convention already used for the replace case's `originalAtlasText` / `acceptedAt` / `editedAt` properties (established in `UX-013B-Atlas-Component-Specification-Reasoning-Components.md` and referenced in the canonical API properties above) — they are not themselves a binding database schema; as with the rest of this ADR, they express the semantic requirement that a future implementation must satisfy, not a mandated field name or storage layout:

- a record of the field's user-authored content immediately prior to Accept (the pre-Accept snapshot),
- a record of the field's own authorship/provenance state immediately prior to Accept, associated with that same pre-Accept snapshot (for example, `priorAuthorship`) — so that Undo can restore the exact prior state rather than one that must be re-inferred, including in the case where that prior state was itself already `user-modified-from-atlas` from an earlier interaction cycle,
- `originalAtlasText` (the Atlas suggestion text offered and accepted),
- `acceptedAt`,
- `editedAt` (`null` until a genuine subsequent edit occurs),
- `authorship: 'mixed'` (the currently-displayed state, per the enumeration already established in the unamended C-02 model above).

#### Attribution behavior

The indicator associated with the `mixed` state is an **attribution indicator** — it discloses provenance and acceptance state; it is not evidence that modification occurred. This addendum does not redesign, and takes no position on, the indicator's placement, interaction behavior, animation, timing, or visual styling — those remain governed by existing and future UX specifications, unchanged by this addendum.

#### Undo requirements

Undo must atomically restore the previous field value, the previous authorship/provenance state, and the previous attribution display state together, as one operation. Undo must never restore the field's prior text while leaving the field's authorship state incorrectly marked as `mixed` or `Atlas Suggested / User Accepted`. The existing undo-window mechanics already specified elsewhere in the corpus (the five-second structural undo window) are unchanged by this addendum; this addendum only requires that whatever snapshot mechanism already backs that undo window restore provenance state, not merely displayed text.

#### Forbidden transitions

Extending the forbidden-transition principles already stated under the unamended C-02 model above, the following are also forbidden:

- Accept-by-append producing `user-modified-from-atlas`.
- `mixed` content displaying as though wholly Atlas-originated.
- `mixed` content displaying as though wholly user-authored.
- Any transition that erases, from the provenance record, either the user-authored pre-Accept contribution or the accepted Atlas contribution.
- Undo restoring field content without also restoring the field's provenance/authorship state.
- A display label claiming fragment-level or positional precision about the boundary between contributions when no fragment-level data is retained.

### Explicit Non-Decisions

This addendum does not decide, and takes no position on: when the product chooses replace versus append; whether the user selects the insertion mode; whether append occurs at the cursor position or at the end of the field; exact concatenation, whitespace, or punctuation rules; or whether append remains available in every context a suggestion can appear. These are interaction- and product-behavior questions, separate from the provenance semantics this addendum governs. This addendum governs only what authorship/provenance state results **if** append occurs — it does not establish when append occurs, including not establishing that append occurs whenever the field is non-empty; that inference arose during the analysis that produced this addendum as one plausible product reading, but it is not adopted here as settled authority and remains open for a future, separate product decision.

This addendum does not introduce token-level provenance, arbitrary collaborative or multi-user authorship semantics, paragraph-level attribution, rich-text range ownership, a new general-purpose provenance engine, new UI components, exact visual styling, implementation code, or database migrations. It does not amend the Atlas UX Source Correction Plan, does not authorize any correction to UX-010 or UX-011, and does not begin or affect Phase 3D of that Plan.

### Downstream Governance Consequence

Implementation in `UX-010-Decision-Workspace-Interaction-Microinteraction-Specification.md` and `UX-011-Decision-Workspace-Visual-Design-Polish-Specification.md` remains unauthorized until: (1) this addendum is independently reviewed and accepted; (2) the Atlas UX Source Correction Plan is separately amended to reflect it; (3) UX-010 and UX-011 are added to that Plan as authorized C-02 correction targets for this specific finding; and (4) a separate source-correction implementation task is approved. This addendum, by itself, authorizes none of those four steps.

### Working Tree Verification (Addendum)

**Branch:** main
**HEAD at time of this addendum:** `d382fdb285a1888ab3d5dbb1bc59d14d6bb6367b` ("docs(ux): correct Phase 3C source specifications") — unchanged throughout this task.
**Files modified:** `docs/atlas_ux/governance/ADR-002-Critical-UX-Architecture-Resolutions.md` (this addendum, appended). All text preceding this addendum, including the original "C-02 — AI Authorship and Provenance" section, is unchanged.
**Files created:** none.
**Other files modified:** none. `docs/atlas_ux/governance/Atlas-UX-Source-Correction-Plan.md` was not modified. `UX-010-Decision-Workspace-Interaction-Microinteraction-Specification.md` and `UX-011-Decision-Workspace-Visual-Design-Polish-Specification.md` were not modified.
**Staged files:** none.
**Untracked files:** none.

No commit was made.

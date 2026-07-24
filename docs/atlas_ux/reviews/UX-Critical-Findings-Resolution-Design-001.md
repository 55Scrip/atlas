# UX Critical Findings Resolution Design 001

## 1. Purpose

`UX-Architecture-Review-001.md` identified six Critical findings (C-1 through C-6, renumbered here C-01 through C-06 for consistency with this document's own section numbering) that, left unresolved, would let two conformant implementers build genuinely different, contradictory versions of Atlas from the same committed document set. This document resolves each of the six as one explicit, traceable, canonical decision, before any source document is corrected and before any component implementation begins. It is a design artifact, not a normative document, and it changes nothing by itself: no existing UX source document is modified here, no missing document is reconstructed here, and nothing is staged or committed. Its output is a decision record that later, separate tasks will use to correct specific source documents, once all six resolutions below are approved together (Governing Decision Principle 10).

## 2. Resolution Method

Every resolution below was reached using only: the 18 committed UX source documents, `UX-Architecture-Review-001.md`, and the ten governing decision principles supplied for this task. UX-013C and UX-013D were not used as evidence and their contents were not inferred, guessed, or reconstructed anywhere in this document — where a finding touches territory those documents would have covered, this document says so explicitly rather than filling the gap by inference.

**Decision criteria, applied in this priority order when they conflict:**
1. **Product philosophy alignment** — does the candidate rule serve Atlas's own stated identity (honest reasoning under uncertainty, user decision ownership, calm non-bureaucratic interaction, permanent and truthful historical record)?
2. **Semantic coherence** — does the candidate rule make the underlying concept clearer, or does it just relocate the ambiguity?
3. **Source support** — is the candidate rule the one multiple independent committed documents already converge on, or is it a minority position held by only one document?
4. **Implementation safety** — does the candidate rule prevent a concrete, describable failure mode (a misattributed record, an inaccessible control, a validation gate that can be satisfied without real content)?
5. **Accessibility** — does the candidate rule conform to standard, non-inventive HTML/ARIA behavior?
6. **Historical integrity** — does the candidate rule preserve the immutable, additive-only historical record model established everywhere else in the set?
7. **Minimum blast radius** — of the coherent candidates remaining after 1–6, which requires correcting the fewest documents, or reuses the most already-existing, already-approved language?

**For every finding, the structure below is fixed:** *Evidence* (direct quotations, freshly re-verified against the committed files, not merely re-cited from the Architecture Review's own paraphrase); *Interpretation* (what the evidence establishes and where it stops); *Selected resolution* (the canonical rule, stated completely enough to implement without further interpretation); *Rejected alternatives* (named, with the specific principle each one fails); *Downstream changes* (which documents this resolution implies must later be corrected, per Governing Decision Principle 9 — no correction is performed here, per Governing Decision Principle 10).

## 3. Critical Finding C-01 — Information Hierarchy Conflict

**Evidence.**

UX-012, §5 ("The Six-Level Information Hierarchy"):
> "Level 1 — Primary Conclusion / The single most important piece of information in a Workspace or Section... One per Workspace or major Section.
> Level 2 — Structural Element / Section headings, Category labels, Named areas of a Workspace. Communicate what a region is for.
> Level 3 — Supporting Narrative / Primary body text...
> Level 4 — Contextual Information / Secondary text — timestamps, sources, metadata, annotations. Present but not dominant.
> Level 5 — Reference Content / Tertiary text — historical content labels, collapsed section previews, supporting references...
> Level 6 — System Metadata / Version numbers, identifiers, system-generated labels."

UX-012A, §7 ("Atlas Information Hierarchy") — the document UX-012 explicitly supersedes, but which is nonetheless committed unflagged as an alternative:
> "Level 1 — Primary conclusion or decision... In the Decision Workspace, it is the decision statement.
> Level 2 — Material implication / Why the primary conclusion matters... This is not the supporting evidence — it is the consequence or significance of the Level 1 statement.
> Level 3 — Supporting reasoning...
> Level 4 — Challenges, uncertainty, or contradiction / What weakens, complicates, or contradicts the primary conclusion. This level receives significant design attention — it must be visible and readable, not buried or suppressed, but it does not compete with the conclusion for primary emphasis.
> Level 5 — Reference detail / The evidence, source material, historical records, granular assumptions, and notes...
> Level 6 — System metadata..."

Product-philosophy evidence bearing on which reading to prefer: UX-000, principle 9 ("Uncertainty is honest, not hidden... Atlas does not manufacture false confidence to appear more useful"); UX-009's own dedicated, always-present Section 6 "What Challenges This Decision"; UX-013B's Challenges component carrying a `blocking` severity level capable of gating the Record Decision action (established independently of UX-012A, in UX-013B's own text).

**Interpretation.** UX-012's Level 2 and UX-012A's Level 2 are not actually describing the same kind of thing: UX-012's "Structural Element" is a **typographic role** (is this text a heading, or is it body copy?) with no stated importance ranking of its own. UX-012A's "Material implication" is a **content-importance tier** (how much does this specific piece of reasoning matter?) with no stated typographic role of its own. These are two different, compatible axes that were both filed under "Level 2" of "the six-level hierarchy" by name, which is the actual defect — not that one is right and one is wrong, but that naming them as competing entries in a single ordered list hides that they answer different questions. Level 4 is the more serious conflict: UX-012's Level 4 never mentions Challenges, uncertainty, or contradiction at all, and under a literal reading of UX-012 alone, Challenges content has **no stated hierarchy level whatsoever** — this is not a defensible design position for a product whose own philosophy repeatedly names honest confrontation with counter-evidence as central to its value, and it is contradicted by the same document series' own Reasoning component (UX-013B's Challenges, with a `blocking` severity) treating Challenges as capable of gating the product's most consequential action.

**Selected resolution.** Adopt a merged six-level **content-importance** hierarchy (UX-012A's axis, since it is the one that actually answers "how important is this"), and demote UX-012's "Structural Element" concept from a competing hierarchy level to a **cross-cutting typographic convention** that applies at every level, not a rank of its own.

**Canonical hierarchy table:**

| Level | Name | Semantic meaning | Typographic role at this level |
|---|---|---|---|
| 1 | **Primary Conclusion or Decision** | The single most important statement in the current Workspace or Section scope. In the Decision Workspace, this is the decision statement; in the Investment/Portfolio Workspace, the thesis or portfolio assessment; in the Dashboard, the most urgent signal. | Largest type, greatest surrounding space, first in reading order. A structural heading labeling Level 1 content uses this same visual weight; it is not a separate level. |
| 2 | **Material Implication** | Why the Level 1 statement matters — its consequence or significance for the user's situation. Not supporting evidence; the stakes. | Medium-emphasis type, clearly subordinate to Level 1, placed immediately below it. |
| 3 | **Supporting Reasoning** | The strongest factors, evidence, or logic that make the Level 1 statement credible. | Standard body text, comfortable reading scale. |
| 4 | **Challenges, Uncertainty, and Contradiction** | What weakens, complicates, or contradicts the Level 1 statement. This level receives deliberate design attention: it must be visible and readable, never buried, suppressed, or defaulted to collapsed-and-hidden, though it does not compete with Level 1 for primary emphasis. | Standard body text, distinguished by semantic border/color treatment (not size alone) and by structural position (after supporting reasoning, before consequences). Explicitly acknowledged by the user when severity is Material or Blocking (per UX-013B's own Challenges model, adopted here unchanged). |
| 5 | **Reference Detail** | Evidence, source material, historical records, granular assumptions, collapsed previews, and other content the user reaches when seeking depth, not content encountered first. | Reduced-emphasis (secondary/tertiary scale), frequently behind expand/collapse, never in the primary reading path. |
| 6 | **System Metadata** | Timestamps, version numbers, identifiers, save state, system-generated labels. | Smallest text in the system, metadata scale, visible only when needed. |

**Cross-cutting rule (replacing UX-012's former Level 2):** "Structural Element" — section headings, category labels, named Workspace areas — is a **typographic treatment**, not a hierarchy level. A heading labels whatever content follows it and inherits that content's own level for weight purposes: a heading over Level 1 content is rendered with Level-1-appropriate prominence; a heading over Level 5 reference detail is rendered with correspondingly lower prominence. No content is ever "Level 2" merely because it is a heading.

**Workspace-level vs. Section-level relationship.** The hierarchy applies recursively, per UX-012's own already-correct instinct ("One per Workspace or major Section"): a Workspace has exactly one Level-1 statement overall, and a major Section within that Workspace may independently have its own local Level 1 (its own most-important statement), which is itself Level-2-through-5 content relative to the Workspace's own Level 1. A Section's internal hierarchy is scoped to that Section; it does not compete with the Workspace's own top-level Conclusion for the single Level-1 slot.

**Rejected alternatives:** UX-012's Level 4 ("Contextual Information," timestamps/metadata) as the definition of Level 4 — rejected because it leaves Challenges undefined and contradicts the product's own stated values (Decision Principle 1). UX-012's Level 2 ("Structural Element") as a genuine hierarchy level — rejected not because it is false, but because treating a typographic role as a peer of a content-importance tier is a category error that this resolution corrects rather than preserves (Decision Principle 2). Wholesale adoption of UX-012A in place of UX-012 — rejected because UX-012's Levels 1, 3, 5, and 6 are substantively sound and already reflected in downstream documents (UX-013B); replacing the whole document would be a larger change than the conflict requires (Decision Principle 3/7).

**Downstream changes required later (not performed here):** UX-012 §5 needs its Level 2 and Level 4 text corrected to match the table above; its former Level 4 content ("timestamps, sources, metadata, annotations") is preserved without loss, redistributed to Levels 5–6 above. UX-012A §7 should be marked formally Superseded (its Level 1/3/5/6 content is absorbed into the corrected UX-012; its Level 2/4 language is the one that prevailed and should be credited, not silently dropped, in UX-012's own amendment note). UX-013B's own stated alignment claim ("All Reasoning Components use the six-level Information Hierarchy consistently... Metadata, labels, contextual text: Level 4–5") needs its Level 4 reference corrected once UX-012's Level 4 changes meaning — Metadata content moves fully to Level 5–6 under the corrected table, and Level 4 becomes exclusively Challenges/contradiction content.

## 4. Critical Finding C-02 — AI Authorship Transfer Conflict

**Evidence.**

UX-012, line 1171 (the strictest, two-step model):
> "AI content attribution: when Atlas Suggestion content is accepted, the field is labeled 'Atlas suggested / User accepted.' When the user subsequently modifies it, the label updates to 'User authored.'"

UX-012B, lines 243, 245, 490, 660 (Accept alone flips the label, no subsequent edit required):
> "user-modified-from-atlas (user has edited the Atlas proposal)."
> "If accepted, the content copies into the user decision field and becomes user-modified-from-atlas state."
> "Accept copies the proposal into the user decision field (user-modified-from-atlas state)."
> "Accept behavior: Accepting replaces the field content with the suggestion. The field transitions to user-modified-from-atlas state."

UX-013B, line 245 (Conclusion component; corrected citation — this quotation belongs to UX-013B, not UX-013A as an earlier extraction pass mis-cited; independently re-verified here):
> "When `isAtlasGenerated` transitions to `isUserModified` (user edits Atlas-generated content), update the attribution silently. Do not prompt the user to confirm they have modified it."

UX-013E's own governing principle (this is UX-013E's own stated text, not attributed to any absent volume, and is therefore usable as direct evidence):
> "AI authorship must never be silently cleared. The `authorship` prop and its rendered indicator persist through user edits unless the user explicitly performs a confirmation action that transfers authorship."

**Interpretation.** Three documents specify three different thresholds for the same underlying event, and UX-012B's threshold (Accept alone, zero edits, flips the label to "user-modified") directly contradicts UX-012's own stricter model for the identical action. UX-013E's own governing principle — not a claim about missing documents, its own directly-stated rule — gives the clearest statement of what the *product* actually needs: authorship must never be silently cleared absent an explicit user act. Read strictly, this principle would seem to require an explicit confirmation dialog for every edit, which would reintroduce exactly the kind of bureaucratic friction Atlas's own philosophy (UX-000: calm, not interruptive) argues against. The correct resolution distinguishes two different things that "authorship" currently conflates: the **currently-displayed attribution label** (which may update automatically, without friction, as soon as genuine editing occurs) and the **underlying provenance record** (which must never be deleted, regardless of what the current label says).

**Selected resolution.** A two-part rule that keeps UX-012's stricter threshold for the *label* and keeps UX-013E's stricter guarantee for the *record*:

1. **Accept, with no subsequent edit:** the field displays "Atlas suggested / User accepted." This is UX-012's rule, adopted as canonical; UX-012B's "Accept alone becomes user-modified-from-atlas" is rejected.
2. **Any subsequent user edit to the field's content, however small:** the displayed label updates immediately to "User authored," with no separate confirmation step required. This adopts UX-013B's no-friction instinct (do not prompt the user to confirm an edit they just made), but reframes what "silently" is permitted to mean.
3. **What "silently" is not permitted to mean:** the original Atlas Suggestion text, the moment it was offered, and the moment it was accepted are never deleted from the record — they are preserved permanently as the field's provenance history, visible in the field's historical/audit trail even after the display label has moved on to "User authored." This satisfies UX-013E's "must never be silently cleared" principle by scoping "cleared" to mean *the provenance record is destroyed* (which never happens), not *the currently-displayed summary label never changes* (which would be both impractical and inconsistent with UX-013B's own no-friction design).
4. **Recording does not itself transfer authorship.** Recording a Decision (Section 13, Record Decision) converts whatever attribution state each field currently holds into permanent Historical Record status — it locks the existing attribution, it does not change it. A field that was never edited and still reads "Atlas suggested / User accepted" at the moment of recording is permanently recorded with exactly that attribution; recording is not itself an implicit "accept everything" or "author everything" act.

**Canonical authorship state table:**

| State | Meaning | Reachable from | Display label |
|---|---|---|---|
| Atlas-generated | Content originated from Atlas with no user action yet | (initial) | "Atlas Suggested" |
| Atlas-suggested, unaccepted | Same as above, offered but not yet acted on | Atlas-generated | "Atlas Suggested" |
| Accepted, unedited | User clicked Accept; content unchanged since | Atlas-suggested | "Atlas Suggested / User Accepted" |
| User-authored (post-edit) | User has edited content that originated with Atlas, or written original content from a blank field | Accepted, unedited; or blank field | "User Authored" |
| Recorded | Any of the above, locked at the moment of Record Decision | Any state above | Same label as at moment of recording, plus a permanent, non-editable "Recorded [date]" marker |
| Historical | A Recorded field displayed in a later review/comparison context | Recorded | Same label, plus "Historical" treatment (Section 11 of the Architecture Review) |

**Allowed transitions:** Atlas-generated → Atlas-suggested → Accepted (unedited) → User-authored (on edit) → Recorded (on Record Decision, from any prior state) → Historical (on later display). **Forbidden transitions:** any transition that discards the original Atlas-generated text from the provenance record; any transition that displays "User Authored" without at least one genuine user edit having occurred; Accept alone producing "User-authored" or "user-modified" (this is precisely UX-012B's rejected rule).

**Rendering consequence:** the visible label reflects the table above exactly; the underlying provenance (original Atlas text, acceptance timestamp, edit history) is always retrievable but not necessarily always visible — it is Level 5 (Reference Detail, per Section 3 above) content, consulted on demand, not surfaced in the primary reading path.

**Persistence consequence:** every field's full attribution history (Atlas-generated text, if any; accepted timestamp, if any; edited timestamp, if any) is stored, never overwritten, mirroring the additive-only historical model established in Section 11 of the Architecture Review.

**Historical consequence:** a Recorded field's attribution label is frozen at whatever it was at the moment of recording; it does not retroactively become "User Authored" if, hypothetically, an amendment later changes the same content (an amendment is itself a new, additively-recorded event with its own independent attribution, per UX-012's Decision Amendment model — the original recorded field is never altered).

**Canonical API properties (for Figma/engineering):** `authorship: 'atlas' | 'user' | 'mixed'` (the currently-displayed label, per the table above); `hasAtlasOrigin: boolean` (permanently true once any Atlas-generated content ever touched this field, regardless of current label); `originalAtlasText: string | null` (the provenance record, never cleared); `acceptedAt: timestamp | null`; `editedAt: timestamp | null`. This is a minimal, additive refinement of UX-013E's own `isAtlasGenerated`/`isUserModified`/`authorship` model — it does not replace that model, it resolves the one behavioral ambiguity (the Accept-alone threshold) that the model as stated did not settle.

**Rejected alternatives:** UX-012B's "Accept alone transfers authorship" — fails Decision Principle 1 (contradicts the product's own promise that the user, not a single click, decides) and Principle 4 (only one document supports this reading; UX-012 and UX-013E's own principle both point the other way). A strict reading of UX-013E's principle requiring explicit confirmation on every edit — fails Decision Principle 1 differently (violates the calm, non-bureaucratic interaction principle) and is explicitly rejected by UX-013B's own "do not prompt" instruction, which this resolution honors by distinguishing label from record.

**Downstream changes required later (not performed here):** UX-012B's three "Accept... becomes user-modified-from-atlas" passages (lines 243, 245, 490, 660) need correction to match the two-step model. UX-013B's Conclusion component note (line 245) needs no change to its *behavior* (silent label update on edit is correct) but should have a clarifying note added that the provenance record is separately preserved. UX-013E's authorship table (Section 32 of that document, per the Architecture Review's citation) should have the `originalAtlasText`/`acceptedAt`/`editedAt` fields added explicitly.

## 5. Critical Finding C-03 — Decision Workspace Section Order Conflict

**Evidence — the two competing numbered sequences, freshly re-verified directly against source, not merely re-cited:**

UX-009 (lines 71–385) and UX-009A (lines 74–603) — mutually identical, thirteen sections:
> "Section 1 — Current Conclusion / Section 2 — Why a Decision Is Required / Section 3 — Proposed Decision / Section 4 — Decision Rationale / Section 5 — What Supports This Decision / Section 6 — What Challenges This Decision / Section 7 — Opportunity Cost / Section 8 — Portfolio Consequences / Section 9 — Assumptions, Monitoring and Invalidation / Section 10 — Implementation Plan / Section 11 — Review Plan / Section 12 — Final Decision Summary / Section 13 — Record Decision."

UX-010 and UX-011 both cite this identical numbering throughout (e.g., UX-010's keyboard shortcuts map Cmd+6 to Section 6 "Challenges," per the Architecture Review's own citation) — **four documents (UX-009, UX-009A, UX-010, UX-011) agree with each other exactly.**

UX-012, §17 (lines 437–450), a different order under different names:
> "1. Current Conclusion / 2. Decision Required / 3. What Changed / 4. Supporting Factors / 5. Challenges / 6. Assumptions / 7. Portfolio Consequences / 8. Opportunity Cost / 9. Implementation / 10. Review Conditions / 11. Proposed Decision / 12. Final Decision Card / 13. Record Decision."

**Interpretation.** Four independent, mutually-consistent documents (the entire dedicated Decision Workspace lineage, UX-008 through UX-011) place Proposed Decision at position 3, immediately following the statement of why a decision is required, and framed explicitly by UX-009 itself as "a starting point, not a conclusion" — i.e., a working hypothesis stated early and then tested by the sections that follow (Rationale, Supporting Factors, Challenges, Opportunity Cost, Portfolio Consequences, Assumptions/Monitoring/Invalidation, Implementation, Review), before being formalized into the Final Decision Card near the end. This is a coherent and defensible design pattern (state the working position, then interrogate it) and is the pattern four documents actually build from. UX-012's single-document alternative moves Proposed Decision to position 11, effectively collapsing it into the same moment as the Final Decision Card, **and introduces a section, "What Changed," that does not appear anywhere in the Decision Workspace's own dedicated lineage** — notably, "What Changed" is the *Investment Workspace's* own third section (UX-005's 11-section order also places "What Changed" at position 3). This is strong evidence that UX-012 §17's sequence is a generic, templated compression that absorbed a pattern from a different Workspace, rather than an independent, deliberate re-ordering of the Decision Workspace specifically. Per Decision Principle 4 (prefer rules supported by multiple documents) and Principle 5 (do not preserve a contradiction merely because one side is detailed — UX-012 is a large document, but size is not the same as being right on this specific point), the four-document lineage governs.

**Selected resolution — the canonical ordered section table**, adopting UX-009/UX-009A/UX-010/UX-011's *order*, and adopting UX-012's component *names* where UX-012's naming is the one already reflected in the component-library documents (UX-012B, UX-013B), since naming and ordering are independent questions and each source is stronger on a different one:

| # | Canonical name | Purpose | Always/Conditional | Default expansion | Ownership | Produces recorded content? | Relationship to neighbors |
|---|---|---|---|---|---|---|---|
| 1 | Current Conclusion | Establish shared understanding before the decision begins | Always | Expanded | Atlas-generated, read-only | No (consumed, not authored, here) | Grounds everything that follows |
| 2 | Why a Decision Is Required | State the specific trigger for this decision moment | Always | Expanded | Atlas-generated, read-only | No | Follows from Current Conclusion |
| 3 | **Proposed Decision** | The user's own stated intention, in their own words, as a working position — "a starting point, not a conclusion" | Always | Expanded | User-owned (blank until authored) | Feeds Final Decision Card | Tested, not finalized, by Sections 4–11 |
| 4 | Decision Rationale | The user's own reasoning for the Proposed Decision | Always | Expanded | User-owned | Feeds Final Decision Card (Primary Reason) | Elaborates Section 3 |
| 5 | **Supporting Factors** | What supports the Proposed Decision | Always | Expanded | Mixed (Atlas-surfaced, user-editable) | No | Precedes Challenges by design (support before contest) |
| 6 | **Challenges** | What challenges the Proposed Decision — Level 4 content per Section 3 above, never defaulted to hidden | Always | Expanded | Mixed | No, but severity acknowledgment may be recorded | Directly follows Supporting Factors |
| 7 | Opportunity Cost | What is foregone by the Proposed Decision | Always | Expanded | Mixed | No | Follows Challenges — cost is assessed after both sides of the case are seen |
| 8 | Portfolio Consequences | What this decision means for the portfolio | Conditional (portfolio-level decisions; may collapse for single-position decisions) | Expanded for portfolio-level, collapsed otherwise | Mixed | Conditionally, via required acknowledgment (Section 6 below) | Follows Opportunity Cost |
| 9 | Assumptions, Monitoring and Invalidation | The conditions this reasoning depends on, what Atlas will watch, and what would invalidate the decision | Always (subsections may collapse) | Expanded | Mixed | Yes — Monitoring Condition and Invalidation Condition | Precedes Implementation |
| 10 | Implementation Plan | How the decision would be executed | Conditional (only for decisions that entail an action; see Section 6 below) | Expanded when present | User-owned | Yes, when present | Precedes Review Plan |
| 11 | Review Plan | What should trigger re-examination | Always (unless explicitly overridden; see Section 6) | Expanded | User-owned | Yes — Review Condition | Precedes Final Decision Card |
| 12 | **Final Decision Card** | The six-field structured, permanent record | Always | N/A (form, not a reading section) | User-owned, locks on recording | Yes — the canonical recorded object | Assembles content from Sections 3–11 |
| 13 | Record Decision | The submission action | Always | N/A | User-driven only; "cannot be triggered by Atlas" (UX-009) | Triggers recording of Section 12 | Terminal |

**Rejected sequences:** UX-012 §17's order — rejected specifically for relocating Proposed Decision to position 11 (contradicted by four documents placing it at position 3) and for introducing "What Changed" as a Decision Workspace section (contradicted by its absence from all four dedicated Decision Workspace documents, and its apparent origin as an Investment-Workspace import). UX-013B's own numbered Reasoning-component sequence, which stops at Review Conditions and appends Decision-tier content separately — not rejected as wrong, since UX-013B's own scope is intentionally Reasoning-components-only (it does not claim to specify the full Workspace section order), but noted as not itself a competing full-sequence claim.

**Naming reconciliation, stated explicitly:** "Supporting Factors" and "Challenges" (UX-012/UX-013B naming) are adopted over "What Supports This Decision"/"What Challenges This Decision" (UX-009/UX-009A naming) because the shorter names are already the ones used by the actual Reasoning components (UX-013B) that populate these sections — using the component's own name for its containing section avoids a needless naming mismatch. "Final Decision Card" (UX-012/UX-012B naming) is adopted over "Final Decision Summary" (UX-009/UX-009A naming) for the identical reason.

**Philosophy check, per the task's own required principles:** *Reasoning before action* — preserved: the Proposed Decision at position 3 is explicitly a hypothesis, not a commitment; the commitment is Record Decision at position 13, unchanged, and everything between tests the hypothesis. *User decision ownership* — preserved and strengthened by Section 3's ownership column (Record Decision remains exclusively user-driven). *Opportunity cost visibility* — preserved at position 7, always present, never made conditional. *Historical durability* — preserved via Section 9's Monitoring/Invalidation Condition and the Final Decision Card's permanent-record role. *Calm completion* — preserved via the conditional (not universally mandatory) treatment of Sections 8 and 10, resolved fully in Section 6 below.

**Downstream changes required later (not performed here):** UX-012 §17 needs its "Reasoning sequence" list corrected to match the table above (this is the single highest-value source correction identified anywhere in this design, since it currently misstates the order of the product's most safety-critical screen). UX-013B should have any of its own section-sequence references checked against the corrected table for consistency (none currently contradict it, since UX-013B's own numbering is scoped to Reasoning components only, as noted above).

## 6. Critical Finding C-04 — Record Decision Completion Gate Conflict

**Evidence.**

UX-009A, line 1091 (the stricter, four-field rule):
> "Validation rules: four required fields before recording (decision text, primary reason, implementation type, review trigger). Soft friction for unacknowledged challenges. All other fields optional."

UX-012, line 874 (the looser, two-field rule):
> "Two fields are required for completion: the Decision statement and the Primary Reason."

UX-012's own unresolved question, lines 1910–1914 (previewing, in its own words, the direction this resolution adopts):
> "Question 2: Completion Gate Threshold / Why unresolved: Two fields are specified as required for Completion... Whether these two fields are sufficient to warrant the gravity of a Recorded Decision — or whether additional required acknowledgments are needed for specific Decision types — requires evidence... Implementation impact: May require conditional required fields based on Decision type... Priority: High."

UX-009A, line 888 (the governing principle for how blocking should work at all):
> "The general principle: Atlas explains the concern clearly and then permits the user to proceed. Blocking is reserved for genuinely incomplete records (missing required fields), not for disagreements about judgment."

**Interpretation.** UX-012's own text does not merely conflict with UX-009A — it explicitly flags the conflict as an open, high-priority question and gestures toward exactly the resolution direction this design adopts: a conditional, decision-type-sensitive completion model rather than one flat threshold. Neither a universal four-field rule nor a universal two-field rule, applied without exception, is correct: a flat four-field rule would force an Implementation Plan onto a decision that entails no implementation (e.g., a Hold decision), which is bureaucratic in exactly the way UX-009A's own governing principle warns against; a flat two-field rule risks producing a Recorded Decision too thin to support a future review, which is the concern UX-012's own Question 2 raises.

**Selected resolution — the canonical completion matrix.**

**Universal hard-blocking minimum, no exceptions, for every Decision Workspace exit via Record Decision:** Decision Statement (Section 3/12) and Primary Reason (Section 4/12). This is UX-012's rule, retained unconditionally, because a Recorded Decision without a stated reason cannot support future review under any circumstance — this is a floor, not a ceiling.

**Conditionally hard-blocking, by decision type:**

| Decision type | Implementation Plan required? | Review Condition required? | Portfolio Consequences acknowledgment required? |
|---|---|---|---|
| Action decision (Increase / Reduce / Exit / Initiate a position) | **Yes** — an action decision with no stated implementation is incomplete | Yes, unless explicitly overridden (see below) | Yes, if portfolio-level; no, if single-position |
| No-action / Hold decision | **No** — there is nothing to implement | Yes, unless explicitly overridden | As above |
| Deferred decision | No — deferral is itself the implementation | **Yes** — the review condition is what ends the deferral; this is the one field a deferred decision cannot omit | As above |
| Review outcome (re-entry via a prior decision's own review trigger) | Conditional — required only if the review concludes with a new or amended action | Yes, unless explicitly overridden | As above |
| Portfolio-level decision | Per action/no-action rule above | Yes, unless explicitly overridden | **Yes**, always |
| Conditional implementation decision (e.g., "increase only if price falls below X") | **Yes** — the condition itself is the implementation plan | Yes, unless explicitly overridden | As above |

**The Review Condition's "unless explicitly overridden" clause, stated precisely:** Atlas's own philosophy (ongoing monitoring, honest confrontation with future uncertainty) argues for treating a Review Condition as effectively universal rather than optional — but a small number of decisions (e.g., a full and final exit of a position with no remaining stake to monitor) genuinely have nothing left to review. Rather than making Review Condition either always-required (bureaucratic in the one case where it doesn't apply) or optional (under-specified everywhere else), the gate requires an explicit, single-click, logged override ("No further review is needed for this decision because ___") in place of a populated Review Condition field — the override itself becomes the recorded content, so the record is never silently thinner than a real review requirement would be.

**Soft-friction, never hard-blocking (per UX-009A's own governing principle, adopted unchanged):** unacknowledged Challenges. A Material or Blocking Challenge must be shown and, for Blocking severity, explicitly acknowledged before recording — but acknowledgment is "I have seen and considered this," not "I agree with this" — Atlas never blocks recording merely because the user's judgment differs from Atlas's own surfaced concern.

**Recommended, non-blocking:** Assumptions detail beyond what Monitoring/Invalidation strictly requires; elaboration of Opportunity Cost beyond the single required comparison; Portfolio Consequences detail beyond the required acknowledgment for non-portfolio-level decisions.

**Semantic completeness vs. interface validation, distinguished explicitly:** the matrix above states *semantic completeness* (what must be true of the Decision record for it to mean something). *Interface validation* is the mechanical implementation of that same rule (field-level required markers, submit-button availability) — Section 8's disabled-control resolution (C-06) governs how that mechanical layer behaves, not what it enforces; this section governs what.

**Accessibility, error messaging, and historical implications** are addressed jointly with C-06 in Section 8, since they are the same interaction surface; this section defines the rule, Section 8 defines its accessible presentation.

**Rejected alternatives:** a flat four-field rule for every decision type — rejected under Decision Principle 1 (bureaucratic friction contradicts Atlas's calm-interaction philosophy for decision types where a field is inapplicable). A flat two-field rule for every decision type — rejected under Decision Principle 4 (Implementation Safety) and is exactly the concern UX-012's own Question 2 raises about itself. Making Review Condition unconditionally required with no override — rejected as needlessly bureaucratic for the genuine edge case of a final, no-remaining-stake exit.

**Downstream changes required later (not performed here):** UX-009A's flat four-field statement (line 1091) needs correction to the conditional matrix above. UX-012's two-field statement (line 874) needs the conditional additions layered on top of its correct universal minimum; its own Question 2 (lines 1910–1914) should be marked resolved, citing this design.

## 7. Critical Finding C-05 — Missing UX-013C and UX-013D Source Problem

**Evidence, re-confirmed directly, not merely re-cited from the Architecture Review:** UX-013E's opening "Governing References" section attributes specific, granular claims (~27 Decision/Monitoring component types across 12 families; ~35 AI/Metadata/System types across 10 families; exact variant counts; exact prop names) to UX-013C and UX-013D, neither of which exists in the committed set. UX-013B's own closing instruction ("Do not produce UX-013C yet. The completed UX-013B is the prerequisite") establishes that, at the time UX-013B was written, UX-013C did not yet exist — meaning UX-013E's later treatment of it as a completed prior volume cannot be confirmed as accurate even in principle from anything else in this repository.

**Option analysis:**

| Option | Truthfulness | Traceability | Implementation safety | Documentation burden | Historical integrity | Future governance | Risk of fabricating provenance |
|---|---|---|---|---|---|---|---|
| A — Reconstruct UX-013C/013D as historical sources, back-filled from UX-013E | Low — would create documents that look independently authored but are not | None gained — circular | Low — no new independent verification occurs | Low effort, but low value | Poor — creates a false paper trail | Poor — normalizes fabricating "history" | **High** — explicitly the failure mode this task instructs against |
| B — Author genuinely new UX-013C/013D specifications from committed governing documents | High — honest new work, same process every other UX-013 volume followed | High, once written — every claim traces to UX-012/UX-008–011 | High, once complete — components get real, checkable specification | High — substantial new design work | Preserved — no existing document is touched | Strong — establishes real provenance going forward | None |
| C — Keep UX-013E's content, strip its unverifiable provenance claims only | Improved, but incomplete — stops mis-attributing, doesn't verify the content itself | Improved for the citation, unchanged for the underlying claims | Unchanged — the same ungrounded component specifications remain in place | Low — a citation-only edit | Neutral | Weak — leaves the actual grounding gap open | None, but doesn't solve the problem C-05 exists to flag |
| **D — Split UX-013E: keep Foundation/Reasoning portions canonical (independently traceable to present UX-013A/013B); demote Decision/Monitoring/AI/Metadata portions to Draft, pending proper specification** | High — states exactly what is and isn't currently grounded | High for the retained portion; explicitly and honestly "not yet" for the demoted portion | High — implementation on the demoted tiers is correctly withheld until grounded | Moderate — a scoping edit now, real authorship work later | Preserved — nothing is deleted, the sound work is kept | Strong — creates the correct entry point for Option B's future work | None |
| E — other | — | — | — | — | — | — | — |

**Selected approach: D**, with Option B as D's own necessary completion path, not a competing second selection (Decision Principle 7 — this distinguishes the canonical decision, D, from its migration consequence, which happens to have the shape described in B).

D is selected because it is the only option that is fully honest about the current state (unlike A and, partially, C) without discarding UX-013E's genuinely sound work (unlike a hypothetical full rejection of UX-013E). It precisely scopes the "not yet safe to build from" boundary to exactly the tiers the Architecture Review already identified as ungrounded (Decision, Monitoring, AI Collaboration, Metadata & System components), leaving Foundation and Reasoning implementation fully unblocked.

**Future authority chain:** UX-012 (corrected per Sections 3–6 above) remains the sole Design System authority. UX-013A and UX-013B remain source volumes, individually authoritative for their own component families, both independently traceable and unaffected by this finding. UX-013E remains canonical **only** for the portions of its content that reconcile UX-013A and UX-013B (its Foundation- and Reasoning-tier classification, naming, and dependency decisions) — this portion's authority is unchanged. UX-013E's Decision-, Monitoring-, AI-Collaboration-, and Metadata/System-tier content is redesignated **Draft — Provenance Unconfirmed**, not deleted, not treated as false, simply not yet promotable to governing status.

**Should UX-013C and UX-013D be created?** Yes — as genuinely new authorship (Option B's shape), not reconstruction. They should be newly written, citing UX-012 (corrected) and all other previously-approved specifications as their governing references, following the identical process UX-013A and UX-013B themselves already followed. They are not "reconstructed" (implying they once existed and are being recovered) and not "intentionally omitted" (the product needs real Decision/Monitoring/AI-Collaboration component specifications; omitting them permanently is not a real option) — they are newly authored.

**What provenance language must change:** every claim in UX-013E of the form "UX-013C establishes..." or "~27 Decision and Monitoring types" must be either (a) removed, if the claim cannot be independently re-derived from committed documents, or (b) re-attributed to whatever new document eventually establishes it, once that document exists. Until then, UX-013E's own text should read "pending UX-013C" rather than asserting UX-013C's content as settled fact.

**What implementation may safely begin before this work is complete:** Foundation-tier (UX-013A) and Reasoning-tier (UX-013B) component implementation — both independently grounded, both unaffected by this finding — may begin now, per Section 12 below.

## 8. Critical Finding C-06 — Disabled Action and Accessibility Conflict

**Evidence.**

UX-009A, line 622 (the earlier, ambiguous language):
> "Disabled state: — Reduced emphasis, cursor: not-allowed"

UX-010, line 611 (a requirement the plain reading of "disabled" above cannot satisfy):
> "Completion gate explanations (the text adjacent to the disabled Record Decision button) are announced when the button is focused and when its state changes (from disabled to available, or when a new explanation appears)."

UX-013A, lines 457, 482 (the correct, later clarification):
> "Disabled actions are accessible: they carry `aria-disabled=\"true\"` (not the HTML `disabled` attribute, which removes them from tab order). A tooltip or visually-hidden text explains why the action is unavailable."
> "Disabled actions: `aria-disabled=\"true\"`, `tabindex=\"0\"` (keyboard reachable), tooltip explaining why."

UX-012C, line 588:
> "Completion-blocked state: `aria-disabled=\"true\"` on the Primary Action with an `aria-describedby` pointing to the gate status message."

**Interpretation.** The native HTML `disabled` attribute removes an element from the tab order and prevents it from ever receiving focus. UX-009A and UX-010, read literally and without the later clarification, describe a button whose focus-announcement requirement (UX-010) is structurally impossible to satisfy if implemented with native `disabled` (UX-009A's plain "Disabled state" language, unqualified). UX-013A and UX-012C already state the correct fix — `aria-disabled`, not `disabled` — but that fix currently lives only in the later, engineering-facing documents, not in the two documents (UX-009A, UX-010) that actually specify this button's behavior in the Decision Workspace.

**Selected resolution — the canonical interaction contract for the Record Decision action (and any primary action following the same "unavailable but explained" pattern):**

- **Markup:** the control is a real, natively-focusable element (e.g., `<button>`), never removed from the DOM or given `display: none` while unavailable. It carries `aria-disabled="true"` while any Section 6 (C-04) required-field condition is unmet, and `aria-describedby` pointing to the specific, current explanation of what remains incomplete. The native `disabled` attribute is never used for this control.
- **Keyboard contract:** the control remains in the natural tab order (`tabindex="0"` or its default natural value) at all times. Pressing Enter/Space while `aria-disabled="true"` does not submit the Decision, but does move focus to the first unmet required field (per the C-04 completion matrix) and re-announces the specific reason recording is currently unavailable. This is the standard, robust WAI-ARIA "operable but blocked" pattern for a primary action, preferred over true disablement precisely because it keeps the control discoverable, explainable, and — per Atlas's own calm, helpful character — actively guides the user to what remains, rather than presenting a dead end.
- **Screen-reader contract:** on focus, the control announces its label and its current reason for unavailability (via `aria-describedby`), per UX-013A's own already-correct language. On any state change (from unavailable to available, or when the specific blocking reason changes because a field was completed), the change is announced via the same mechanism UX-010 already specifies (line 611), which this resolution preserves unchanged — only the underlying mechanism (`aria-disabled` in place of `disabled`) changes, not the announcement behavior itself.
- **Visual contract:** reduced-emphasis styling (UX-011's existing "reduced opacity, approximately 40–45%; cursor not-allowed on pointer devices") is retained exactly as specified — this resolution changes the underlying accessibility mechanism, not the visual design.
- **Pointer/mouse behavior:** clicking while `aria-disabled="true"` produces the identical result as the keyboard contract above — focus (or scroll-and-focus) moves to the first unmet required field, with the reason surfaced inline at that field, not only in a tooltip on the button itself.
- **Tab order:** the control is always in the tab order; this is a direct, explicit decision (not an oversight) precisely because a primary action this consequential must remain discoverable to keyboard and screen-reader users at every point in the flow, including while incomplete.
- **Mobile/touch:** identical contract — `aria-disabled`, tap-to-navigate-to-first-incomplete-field, same visual treatment, no special-casing. Consistency across input modalities is preferred over inventing a touch-specific variant.

**Failure cases explicitly addressed:** a screen-reader user who tabs to the Record Decision control while incomplete hears the label and the specific reason, not silence (which native `disabled` would produce by excluding the control from the tab order entirely). A sighted keyboard user who presses Enter on the visually-dimmed button is taken somewhere useful (the first incomplete field) rather than experiencing an inert control with no feedback.

**Rejected alternatives:** native HTML `disabled` — rejected outright, fails Decision Principle 5 (conflicts with standard, well-established ARIA guidance and with UX-010's own stated requirement). A no-op click/Enter response (control announces the reason but does not move focus anywhere) — considered and not selected as the primary rule, since navigating to the first incomplete field is more consistent with Atlas's stated helpful, calm character (Decision Principle 1), though this alternative is not unsafe and is noted in Section 13 as a question that would benefit from real usability evidence.

**Downstream changes required later (not performed here):** UX-009A line 622 and UX-010's surrounding "Disabled state" language need the `aria-disabled`-not-`disabled` instruction added directly, pulling forward UX-013A's and UX-012C's already-correct text into the documents that actually specify this button's behavior. No change is needed to UX-013A or UX-012C themselves — they were already correct; they simply were not the documents a Decision-Workspace-focused reader would necessarily reach.

## 9. Cross-Finding Consistency Check

**Information hierarchy (C-01) vs. Decision Workspace section order (C-03):** Consistent, and mutually reinforcing. C-01's Level 4 (Challenges, uncertainty, contradiction — never buried) directly justifies C-03's placement of the Challenges section as always-present, never conditional, immediately following Supporting Factors. No conflict.

**Authorship model (C-02) vs. historical immutability (Architecture Review, Section 11):** Consistent. C-02's rule that the provenance record (original Atlas text, acceptance/edit timestamps) is never deleted is a direct application of the additive-only historical model; C-02 introduces no new mutation of recorded content, only a rule for what gets recorded and when.

**Completion gate (C-04) vs. unavailable-action behavior (C-06):** Consistent, with an explicit dependency: C-06's "navigate to the first unmet required field" behavior is only implementable once C-04's completion matrix defines which fields are required for the current decision type. **C-06 depends on C-04**, not the reverse — any future correction to the completion matrix (C-04) automatically changes what C-06's navigation targets, with no change needed to C-06's own contract.

**Decision Workspace sequence (C-03) vs. component architecture (Architecture Review, Section 8):** Consistent. C-03's naming choices (Supporting Factors, Challenges, Final Decision Card) match the component names already established in UX-012B and UX-013B, introducing no new naming conflict.

**UX-013E authority resolution (C-05) vs. future source correction:** A genuine, important sequencing dependency. New UX-013C/UX-013D-equivalent authorship (C-05's migration consequence) should itself be written using the corrected hierarchy (C-01), authorship model (C-02), section-order/naming conventions (C-03), completion-gate pattern (C-04), and disabled-control pattern (C-06) — meaning **C-05's long-term resolution depends on C-01, C-02, C-03, C-04, and C-06 being settled first**, not the other way around. This is the single most important sequencing fact in this design and governs Section 11's ordering.

**No contradictions were found between any of the six resolutions.** The dependency C-06→C-04 and the dependency C-05→{C-01, C-02, C-03, C-04, C-06} are the only load-bearing relationships; every other pair is independent.

## 10. Canonical Decisions Summary

| Finding ID | Canonical Decision | Governing Reason | Documents to Correct Later | Blocks Implementation? | Implementation Scope Affected |
|---|---|---|---|---|---|
| C-01 | Merge UX-012A's content-importance levels with UX-012's typographic-role concept demoted to a cross-cutting convention; Challenges is Level 4, universally, never buried. | Decision Principle 1 (product philosophy: honest confrontation with uncertainty) and Principle 2 (semantic coherence: "heading" and "importance" are different axes). | UX-012 §5, UX-012A §7 (mark Superseded), UX-013B (Level 4 reference). | Yes, for any Reasoning-tier or cross-Workspace visual-hierarchy work. | Reasoning components, Workspace composition, Figma visual tokens. |
| C-02 | Accept-alone → "Atlas suggested / User accepted"; any subsequent edit → "User authored," no confirmation prompt; provenance record never deleted regardless of label; recording locks, never transfers, attribution. | Decision Principle 1 (user agency, no silent misattribution) reconciled with Principle 1's calm-interaction requirement via the label/record distinction. | UX-012B (four passages), UX-013E (authorship table, add provenance fields). | Yes, for any component displaying or persisting authorship state. | Reasoning and Decision components, Metadata/Provenance components. |
| C-03 | Canonical 13-section order = UX-009/UX-009A/UX-010/UX-011's sequence (Proposed Decision at position 3), with UX-012/UX-013B's shorter component names adopted for Sections 5, 6, 12. | Decision Principle 3 (Source Support: four mutually-consistent documents vs. one outlier) and Principle 5 (UX-012's detail does not make its outlier order correct). | UX-012 §17 (correct the sequence). | Yes — this is the Decision Workspace's entire information architecture. | Decision Workspace composition and layout. |
| C-04 | Universal minimum: Decision Statement + Primary Reason. Conditional by decision type: Implementation Plan (action decisions only), Review Condition (all, unless explicitly overridden), Portfolio Consequences acknowledgment (portfolio-level only). Challenges acknowledgment stays soft-friction. | Decision Principle 1 (avoid bureaucratic friction) balanced against Principle 4 (Implementation Safety: a Decision record must support future review). | UX-009A (line 1091), UX-012 (line 874, resolve Question 2). | Yes — gates the product's single most irreversible action. | Decision components, validation logic. |
| C-05 | Option D: retain UX-013E's Foundation/Reasoning-reconciling content as canonical; redesignate its Decision/Monitoring/AI-Collaboration/Metadata content as Draft — Provenance Unconfirmed, pending genuinely new UX-013C/UX-013D authorship (not reconstruction). | Decision Principle 1 (truthfulness) and Principle 7 (minimum blast radius — preserves UX-013E's sound work rather than discarding it). | UX-013E (provenance-language correction); future new UX-013C, UX-013D. | Yes, for Decision, Monitoring, and AI Collaboration/Metadata component tiers specifically; no, for Foundation/Reasoning. | Decision, Monitoring, AI Collaboration, Metadata & System component tiers. |
| C-06 | `aria-disabled="true"` (never native `disabled`), always in tab order, activation navigates focus to first unmet required field and re-announces the reason; identical contract on mobile. | Decision Principle 5 (Accessibility: standard ARIA behavior, not invented interaction) and Principle 1 (helpful, calm character). | UX-009A (line 622 area), UX-010 (surrounding "Disabled state" language). | Yes, for the Record Decision button and any component following the same pattern. | Foundation (WorkspaceFooter/primary action), Decision components. |

## 11. Source Correction Plan

**This section defines order only. No correction is performed here, per Governing Decision Principle 10 — nothing below is executed until all six resolutions above are approved together.**

1. **Correct UX-012 first.** UX-012 is already the sole, currently-authoritative assembled Design System document (having already and correctly superseded UX-012A–D per the existing, unchallenged supersession chain documented in the Architecture Review, Section 4). Three of the six findings (C-01, C-03, C-04) require correcting UX-012 directly. Because UX-012 already holds sole authority, the assembled document is corrected directly — there is no reason to "un-supersede" back to UX-012A first. This directly answers the task's own question of whether assembled or source documents go first: **for UX-012, the assembled document goes first**, precisely because it is already the sole authority.
2. **Mark UX-012A formally Superseded**, immediately after step 1 lands, with an explicit amendment note crediting UX-012A's Level 2/4 language as the basis for UX-012's corrected Level 2/4 (per C-01's resolution) — this avoids silently erasing the fact that UX-012A's specific wording is what prevailed on this point. UX-012A's body text is not edited; only its Status line changes.
3. **Correct UX-012B**, for C-02 (the four "Accept alone becomes user-modified-from-atlas" passages).
4. **Correct UX-009A and UX-010**, for C-06 (pull forward the `aria-disabled` clarification) and for C-04 (replace the flat four-field rule with the conditional matrix).
5. **Correct UX-013B**, for C-01 (Level 4 cross-reference) — a small, localized change, not a rewrite.
6. **Only after steps 1–5 land**, address UX-013E per C-05: apply the provenance-language correction (remove or defer claims attributed to UX-013C/UX-013D), and formally redesignate its Decision/Monitoring/AI-Collaboration/Metadata sections as Draft. This step is ordered last because UX-013E's eventual re-reconciliation will need to reference the now-corrected hierarchy, authorship model, section order, completion gate, and disabled-control contract — doing this step first would mean redoing it once steps 1–5 land.
7. **Only after step 6**, begin genuinely new authorship of UX-013C- and UX-013D-equivalent specifications, using the corrected UX-012 (and the now-Draft-scoped UX-013E boundary) as governing references, following the same process UX-013A and UX-013B themselves used.

**Changelog and supersession-note handling:** every corrected document should carry an explicit, dated amendment note ("Amended [date]: Corrected per UX-Critical-Findings-Resolution-Design-001, Finding C-0N") rather than silently rewriting the disputed passage — this preserves the historical fact that a prior version existed and stated something different, consistent with the immutable-history discipline this same review found Atlas's own product philosophy already requires of its data model; the documentation should hold itself to the standard it sets for the product. **No source document's body text is rewritten to erase the fact that a contradiction once existed** — the correction adds the new canonical rule and dates it; it does not pretend the old text was never there.

## 12. Implementation Unblocking Map

| Area | Status |
|---|---|
| Foundation Components | **Unblocked by resolution design alone.** None of the six findings changes Foundation component existence or API; C-01's corrected token application is a later, non-blocking visual-weight refinement. |
| Reasoning Components | **Unblocked by resolution design alone.** This document's C-01/C-02 rules are sufficient authority to build against immediately, even before UX-012B/UX-013B's own text is physically corrected. |
| Decision Components | **Requires missing-document work** (C-05) before full build-out; the C-03/C-04 rules in this document may be used as interim authority for whatever Decision-tier work is not blocked on C-05 specifically (e.g., the Final Decision Card's basic six-field shape, already independently established in UX-012). |
| Monitoring Components | **Requires missing-document work** (C-05) — no independently-grounded specification exists for this tier beyond the one-paragraph component definitions in UX-012 itself. |
| AI Collaboration Components | **Requires missing-document work** (C-05), and additionally gated on this document's C-02 resolution being adopted, since this is exactly the tier where the authorship-transfer rule applies most directly. |
| Metadata and System Components | **Requires missing-document work** (C-05). |
| Workspace composition (Dashboard, Investment) | **Unblocked by resolution design alone.** |
| Workspace composition (Decision Workspace specifically) | **Requires source correction** in the sense that this document's C-03 table should be treated as the authority now, with UX-012 §17 corrected to match later — implementation may proceed against this document directly. |
| Figma library architecture | **Unblocked by resolution design alone** for Foundation/Reasoning pages; **still blocked by another unresolved finding** (C-05) for Decision/Monitoring/AI Collaboration pages specifically. |
| Engineering package architecture | **Unblocked by resolution design alone** for the layered package model itself (Foundation → Reasoning); **requires missing-document work** for the Decision/Monitoring/AI Collaboration packages specifically. |

## 13. Remaining Questions

**Q1 — The exact typographic values (font sizes, weights, spacing units) that operationalize the corrected six-level hierarchy.** *Why unresolved:* this is a visual-design execution question, not an architectural one; the corrected hierarchy in Section 3 states the semantic model completely, but translating "Level 2 is clearly subordinate to Level 1 but not subtle" into an actual point size requires visual design work this document is not positioned to do. *Evidence/decision required:* a visual-design pass, analogous to what UX-011 did for the Decision Workspace specifically, now applied to the corrected universal hierarchy. *Blocks implementation:* No — Foundation and Reasoning component behavior does not depend on the exact point sizes; final visual polish sign-off does.

**Q2 — Whether "Review Condition required unless explicitly overridden" (C-04) is the right default in practice.** *Why unresolved:* this mirrors UX-012's own Question 2 disposition almost exactly — it is a product-policy default that reasonably could be set as designed here, but its correctness is ultimately an empirical question about real Decision-recording sessions, not one resolvable from documents and philosophy alone. *Evidence/decision required:* qualitative research on recorded-Decision quality and user confidence at the completion moment, per UX-012's own stated evidence requirement. *Blocks implementation:* No — the default in Section 6 is a reasonable, principled starting position; it can be adjusted later without re-architecting the completion gate's structure.

**Q3 — Whether "navigate to the first incomplete field" (C-06) is better for Atlas's specific users than a simpler "re-announce the reason, do not navigate" pattern.** *Why unresolved:* both are ARIA-conformant; which is actually better for Atlas's audience (long-term investors, not necessarily power users of complex forms) is a usability question. *Evidence/decision required:* usability testing of the Record Decision completion flow, per the Architecture Review's own Section 24 ("safe to defer to implementation evidence") disposition for closely related questions. *Blocks implementation:* No — Section 8 selects the navigate-to-field behavior as the initial, principled default; it is a low-cost change to simplify later if evidence warrants.

**Q4 — The actual content of UX-006 and UX-007 (Portfolio Workspace Philosophy and Screen Specification).** *Why unresolved:* this task's scope is the six Critical findings from the Architecture Review, none of which concerns Portfolio Workspace directly; UX-006/UX-007 remain absent and this design does not reconstruct them, consistent with this task's own explicit instruction. *Evidence/decision required:* the same missing-document work path described for UX-013C/UX-013D in Section 7, applied instead to Portfolio Workspace's own foundational documents — a separate, not-yet-scoped future task. *Blocks implementation:* Not for anything this design addresses; yes, for any future Portfolio Workspace-specific implementation, per the Architecture Review's own Section 18 finding.

**Q5 — How the future new UX-013C/UX-013D-equivalent specifications should be scoped** (mirroring the original four-way Foundation/Reasoning/Decision/AI split, or reorganized differently, given what this review learned about how that four-way split produced an unverifiable dependency the first time). *Why unresolved:* this is a documentation-architecture decision for whoever undertakes that future authorship work, informed by, but not settled by, this design. *Evidence/decision required:* a scoping decision at the start of that future task, informed by Section 19 of the Architecture Review (documentation scalability). *Blocks implementation:* No — it affects how the future work is organized, not whether Foundation/Reasoning work can proceed now.

## 14. Recommended Next Task

**Approve resolutions.**

Governing Decision Principle 10 states plainly that no source document should be changed until all six resolutions are approved together. This design has produced exactly the six approvable resolutions that principle anticipates, plus their dependency order (Section 9) and correction sequence (Section 11). The only task that can correctly come next, in dependency order, is an explicit approval step for this document as a whole — not a partial approval of some findings and not a start on source correction, missing-document authorship, or implementation, any of which would violate Principle 10 by acting on an unapproved subset. Once approved, Section 11's correction plan and Section 12's unblocking map become directly actionable in the order stated.

## 15. Working Tree Verification

**Branch:** main
**HEAD:** `f2d5adbb7cd260853f56197e35fcc776caf85a78` ("docs: import verified Atlas UX source specifications") — unchanged throughout this task.
**Files created:** `docs/atlas_ux/reviews/UX-Critical-Findings-Resolution-Design-001.md` (this document). No new directory was required — `docs/atlas_ux/reviews/` already existed from the prior task.
**Files modified:** none. No UX source document under `docs/atlas_ux/*.md` was altered. `UX-Architecture-Review-001.md` was not modified.
**Staged files:** none.
**Untracked files:** `docs/atlas_ux/reviews/UX-Critical-Findings-Resolution-Design-001.md`, alongside the previously-untracked `docs/atlas_ux/reviews/UX-Architecture-Review-001.md`.

No commit was made. This document does not stage, commit, tag, or push anything, and does not modify any existing UX source document, reconstruct any missing document, or implement any component, per its own instructions.

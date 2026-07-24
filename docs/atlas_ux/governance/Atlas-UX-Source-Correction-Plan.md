# Atlas UX Source Correction Plan

## 1. Purpose

This document plans the controlled correction of the committed Atlas UX source corpus (`docs/atlas_ux/*.md`) so that it becomes textually consistent with `ADR-001-Missing-Source-Volume-Governance.md` and `ADR-002-Critical-UX-Architecture-Resolutions.md`.

This is **not** a new architecture review. It does not re-examine whether the six resolutions in ADR-002 are correct, and it does not introduce new findings of its own weight equal to those six. This is **not** a redesign. No Workspace, component, or interaction model is changed in substance anywhere in this plan; every correction described below states an already-decided rule more consistently than the current text does. **The six decisions (C-01 through C-06) are already accepted** by ADR-002 and are treated here as fixed inputs, not open questions. **This plan must not reopen them** — where this planning pass surfaces a source passage not previously named in the Resolution Design's own "Downstream changes" lists (this happened twice; see Sections 6 and 9 below), the correct response is to add that file to the *same, already-decided* correction, not to re-litigate the decision itself. **Historical source content must not be silently rewritten without traceability** — every correction described below is paired with an explicit, dated amendment note requirement (Section 17), so that a reader who encounters a corrected document can see both the corrected rule and the fact that a prior, different statement once existed there.

## 2. Governing Authority

1. **ADR-001** governs missing-source and provenance handling in general, for any current or future assembling document in this corpus.
2. **ADR-002** governs the six accepted UX architecture resolutions (C-01 through C-06) specifically.
3. **`UX-Critical-Findings-Resolution-Design-001.md`** provides the detailed rationale, evidence quotations, rejected alternatives, and operational interpretation behind each of the six resolutions — this plan defers to it wherever this plan's own summary is incomplete.
4. **`UX-Architecture-Review-001.md`** remains the evidence record — the original discovery, quotation, and severity grading of all findings, not only the six Critical ones.
5. **Existing UX source documents remain historical source artifacts** — accurate records of what they said, when — **until corrected** by a separate, future execution task.
6. **Where existing source text conflicts with ADR-001 or ADR-002, the ADRs govern the future corrected state.** The source text is not retroactively false; it is simply no longer the operative authority on the point the ADRs resolve.

**Handling the temporary authority split during migration.** Between now (ADR-002 accepted, no source corrected) and the completion of this plan's execution, two authorities coexist over the same subject matter: the accepted ADRs (stating the correct rule) and the uncorrected source documents (still stating the old, superseded rule in their own committed text). ADR-002's own "Implementation Constraint" section already resolves how to act during this window: implementation treats the ADRs, the Resolution Design, and (for provenance questions) ADR-001 as governing, and does not treat conflicting, uncorrected source text as authoritative merely because it is unchanged in Git. This plan does not alter that constraint; it exists to close the split, not to manage it indefinitely.

## 3. Correction Principles

- **Minimal necessary change.** Each correction states the accepted rule; it does not rewrite surrounding, unaffected material.
- **Preserve unaffected content.** A document corrected for one finding is not opportunistically edited for unrelated matters.
- **No silent semantic drift.** A corrected passage must mean exactly what ADR-002 says it means — not a rephrasing that shifts nuance.
- **No fabricated provenance.** No correction implies that a document said something, at some past date, that it did not actually say.
- **No retroactive dating.** A correction is dated to when it is actually made; it is never back-dated to make it appear original to the document's first authorship.
- **No claim that missing documents previously existed.** UX-013C and UX-013D are never described, in any corrected document, as having existed before this program addresses them.
- **Explicit changelog or correction notes where semantics change** — required for every correction in this plan; see Section 17 for the exact mechanism.
- **Assembled documents are corrected after their governing source decisions are stabilized.** UX-012 (an assembled document) is the one exception this plan treats as "already the sole authority" and therefore correctable directly and first (Section 15); UX-013E (the other assembled document) is corrected last, specifically because its own correction (the trust-boundary migration) depends on every other correction's content being final.
- **Deterministic validation after each phase** — defined fully in Section 18, applied at every phase boundary in Section 14.
- **One concern per commit where practical** — defined fully in Section 16.
- **No implementation dependency on uncorrected contradictory text** — restated from ADR-002's own Implementation Constraint; this plan's existence does not loosen it.
- **(Added, required by ADR-001 specifically) No fabricated historical source document is created, and no provenance claim is silently removed** — applies specifically to the UX-013E migration (Section 10) and to any future UX-013C/UX-013D authorship, which this plan schedules but does not perform.
- **(Added, required by ADR-002's Cross-Resolution Dependencies) A correction to any one of the six findings must not reintroduce a conflict with any of the other five** — validated explicitly per correction, not only at the end (Section 18).

## 4. Source Corpus Inventory

All 18 committed files, classified. "Finding IDs" lists only C-01–C-06 relevance; broader (Medium/Low) Architecture Review findings are out of scope per Section 21.

| File | Current role | Finding IDs | Correction status | Reason | Dependency |
|---|---|---|---|---|---|
| UX-000-The-Atlas-Experience.md | Foundational product philosophy | none | No correction required | Contains no hierarchy, authorship, section-order, completion-gate, provenance, or disabled-control text; cited only as philosophy evidence in the Resolution Design | none |
| UX-004-Investment-Workspace-Philosophy.md | Investment Workspace philosophy | none | No correction required | Investment-Workspace-scoped; not implicated by any of the six | none |
| UX-005-Investment-Workspace-Screen-Specification.md | Investment Workspace screen spec | C-03 (reference only) | No correction required | Its own "What Changed" (its legitimate Section 3) is correct for the *Investment* Workspace; the finding is that UX-012 wrongly imported this into the *Decision* Workspace sequence — UX-005 itself is not wrong and is not touched | none |
| UX-007A-Portfolio-Workspace-Wireframe-Specification.md | Portfolio Workspace wireframe | none | No correction required | Portfolio-Workspace-scoped; not implicated | none |
| UX-007P-Portfolio-Workspace-Final-Polish.md | Portfolio Workspace polish | none | No correction required | Portfolio-Workspace-scoped; not implicated | none |
| UX-008-Decision-Workspace-Philosophy.md | Decision Workspace philosophy | C-04 (supporting evidence only) | No correction required — later validation only | Its own anti-bureaucracy principle ("excessive required fields" named as an anti-pattern, line 594) *supports* C-04's conditional model; contains no field-count, hierarchy, authorship, or disabled-control text of its own | Validate corrected UX-009/UX-009A/UX-010/UX-012 against this principle after Phase 2 |
| UX-009-Decision-Workspace-Screen-Specification.md | Decision Workspace information architecture | C-03, C-04 | Direct correction required | (a) Uses non-canonical section names ("What Supports This Decision," "What Challenges This Decision," "Final Decision Summary") for Sections 5/6/12, now superseded by "Supporting Factors"/"Challenges"/"Final Decision Card"; (b) states its own four-condition completion rule (lines 578–586) that **hard-blocks on unacknowledged critical Challenges** — this directly contradicts ADR-002's "Challenges acknowledgment stays soft-friction, never hard-blocking" and was not named in the Resolution Design's own downstream-changes list — newly confirmed during this planning pass and added here without reopening the C-04 decision itself | After UX-012 (Phase 1) |
| UX-009A-Decision-Workspace-Wireframe-Specification.md | Decision Workspace wireframe | C-03, C-04, C-06 | Direct correction required | Same Sections 5/6/12 naming as UX-009; its own flat four-field rule (line 1091) superseded by the conditional matrix; its own ambiguous "Disabled state" language (line 622) needs the `aria-disabled` clarification | After UX-012 (Phase 1) |
| UX-010-Decision-Workspace-Interaction-Microinteraction-Specification.md | Decision Workspace interaction/microinteraction | C-03 (naming, minor), C-04, C-06 | Direct correction required | Uses "Final Decision Summary" in multiple places (Sections 5/6/12 style references); independently restates "Record Decision reaches availability when four required fields are complete" (line 751) — a bare restatement of the superseded flat rule, newly confirmed during this planning pass; its own focus-announcement requirement (line 611) needs the `aria-disabled` clarification added alongside it | After UX-012 (Phase 1) |
| UX-011-Decision-Workspace-Visual-Design-Polish-Specification.md | Decision Workspace visual design | none | No correction required | Its 3-tier local "Reading Hierarchy" and 4-layer authorship-visual-weight model are compatible with, not contradicted by, any of the six resolutions; contains no field-count or ARIA-mechanism text; verified directly — no authorship *label* text, no completion-count text | none |
| UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md | Assembled Design System authority | C-01, C-03, C-04 | Direct correction required | §5 Level 2/4 definitions; §17 "Reasoning sequence" (wrong order, spurious "What Changed"); line 874 two-field rule needs conditional additions layered on; its own Question 2 (lines 1910–1914) marked resolved | First (already sole authority; Section 15) |
| UX-012A-Atlas-Design-System-Foundations.md | Superseded Design System part (Foundations) | C-01 | Authority/supersession correction required | Its own Level 2/4 wording is the one that prevailed in UX-012's correction and must be credited, not silently dropped; its `Status:` line updates to Superseded; body text is not edited | After UX-012 (step 1) |
| UX-012B-Atlas-Design-System-Components-Reusable-Patterns.md | Superseded Design System part (Components) | C-02 | Direct correction required | Four passages (lines 243, 245, 490, 660) state "Accept alone → user-modified-from-atlas," directly contradicting the accepted two-step authorship model | After UX-012A's status update |
| UX-012C-Atlas-Design-System-Interaction-Navigation-Responsive-Behavior.md | Superseded Design System part (Interaction) | C-06 (reference only) | No correction required | Already compatible: line 336 states primary actions in disabled state remain in tab order; line 544 already describes an auto-scroll-to-missing-field completion-gate check consistent with the accepted C-06 model. Serves as corroborating reference, not a document requiring edits | none |
| UX-012D-Atlas-Design-System-Governance-Tokens-Evolution.md | Superseded Design System part (Governance/Tokens) | none | No correction required | Not implicated by any of the six; its token-naming mismatch with UX-013A/013B (Architecture Review Finding 15.1, High severity) is explicitly out of scope per Section 21 | none |
| UX-013A-Atlas-Component-Specification-Foundation-Components.md | Foundation component library (source volume) | C-06 (reference only), C-01 (reference only) | No correction required | Already contains the correct `aria-disabled` language (lines 457, 482, 588) — this is the source the C-06 correction pulls forward into UX-009A/UX-010; its sole hierarchy reference ("Conclusion occupies Level 1") is unaffected since Level 1 is unchanged by C-01. Remains fully canonical and untouched by the C-05 migration | none |
| UX-013B-Atlas-Component-Specification-Reasoning-Components.md | Reasoning component library (source volume) | C-01, C-02, C-03 (validation only) | Direct correction required (C-01, C-02); later validation only (C-03) | Its own "Metadata, labels, contextual text: Level 4–5" claim needs correction once UX-012's Level 4 changes meaning; its Conclusion-component note (line 245) needs a clarifying addition (not a behavior change) that provenance is separately, permanently preserved; its own Reasoning-only numbered sequence does not compete with, and is not contradicted by, the corrected Section order | After UX-012B |
| UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md | Final component-library assembly | C-01 (reference check), C-02, C-05 | Direct correction required (C-02); UX-013 trust-boundary migration required (C-05) | Its own authorship table needs `originalAtlasText`/`acceptedAt`/`editedAt` added; its Decision/Monitoring/AI-Collaboration/Metadata content and provenance claims about UX-013C/UX-013D require the full Option F migration (Section 10) | Last — after every other correction (Phase 4) |

**11 of 18 files require no correction. 7 files require direct or authority correction**, matching ADR-002's own "at minimum" list exactly, with two additions (UX-009's hard-blocking Challenge rule; UX-010's bare four-field restatement) surfaced by this planning pass's own full read and folded into the already-accepted C-04 decision without reopening it.

## 5. Conflict-to-Document Matrix

| Finding | Governing decision (ADR-002) | Conflicting text found in | Already-compatible text in | Direct edits required in | Cross-reference/status only in | Assembled documents affected | Validation required |
|---|---|---|---|---|---|---|---|
| C-01 | Merged content-importance hierarchy; Challenges fixed at Level 4 | UX-012 (§5), UX-012A (§7, superseded original) | UX-013A (Level 1 reference only) | UX-012, UX-013B | UX-012A (status line) | UX-012 | No document states a six-level hierarchy other than the corrected one; UX-012A carries a Superseded status crediting its own wording |
| C-02 | Two-step authorship model; permanent provenance | UX-012B (4 passages) | UX-012 (line 1171, already correct), UX-011 (visual weight, unaffected) | UX-012B, UX-013B (clarifying note), UX-013E (authorship table) | none | UX-013E | No document states "Accept alone transfers authorship"; every authorship-label passage matches the two-step model |
| C-03 | Canonical 13-section order, adopted names | UX-012 (§17 order + naming) | UX-009, UX-009A, UX-010 (order only — matches exactly) | UX-012 (order), UX-009/UX-009A/UX-010 (naming only) | UX-013B (validation only) | UX-012 | Exactly one section order appears anywhere in the corpus; Sections 5/6/12 use identical canonical names everywhere |
| C-04 | Universal minimum + conditional matrix + soft-friction Challenges | UX-009A (flat 4-field), UX-012 (flat 2-field, self-flagged), UX-009 (hard-blocks Challenges), UX-010 (bare 4-field restatement) | UX-008 (anti-bureaucracy principle, supports the resolution) | UX-009, UX-009A, UX-010, UX-012 | none | UX-012 | No document states a flat field count with no decision-type conditionality; no document hard-blocks on Challenge acknowledgment |
| C-05 | Option F trust-boundary migration | UX-013E (Governing References; provenance claims) | UX-013A, UX-013B (fully independent, untouched) | UX-013E (split into two new documents, per Section 10) | UX-013E (existing file, marked Superseded once split) | UX-013E | No document asserts UX-013C/UX-013D content as settled fact; the interim document's three-tier classification is internally consistent |
| C-06 | `aria-disabled`, permanent focusability, navigate-to-first-incomplete-field | UX-009A (line 622), UX-010 (line 611, paired requirement) | UX-013A (lines 457, 482, 588), UX-012C (lines 336, 544) | UX-009A, UX-010 | none | none | No document describes the Record Decision control using the bare word "disabled" without the `aria-disabled` qualification |

## 6. C-01 Correction Plan — Information Hierarchy

| File | Exact section/concept | Current conflicting rule | Target canonical rule | Semantic text changes? | Examples/diagrams change? | Token/typography references change? | Historical note preserved? |
|---|---|---|---|---|---|---|---|
| UX-012, §5 "The Six-Level Information Hierarchy" | Level 2 and Level 4 definitions | Level 2 = "Structural Element" (headings/labels); Level 4 = "Contextual Information" (timestamps/metadata, no mention of Challenges) | Level 2 = "Material Implication" (why Level 1 matters); Level 4 = "Challenges, Uncertainty, and Contradiction" (per ADR-002's canonical table, Section on C-01) | Yes — both level definitions replaced | No diagrams present in this section | No — this section states semantic meaning only; typography values are a separate, later, non-blocking design pass (Resolution Design's own Remaining Question Q1) | Yes — amendment note crediting UX-012A's original Level 2/4 wording as the basis (Section 17) |
| UX-012, §5 | New cross-cutting rule | Not present | Add explicit statement: "Structural Element" (headings, labels) is a typographic convention applied at every level, not a separate level | Yes — new sentence(s) added | No | No | Not applicable — this is a clarifying addition, not a correction of prior wrong text |
| UX-012A, §7 "Atlas Information Hierarchy" | Entire section | Currently the "live," uncredited alternative | No body text change — `Status:` line updated to "Superseded — see UX-012 §5 (corrected); this section's Level 2/4 wording is the basis for that correction, per ADR-002 C-01" | No — body preserved verbatim | No | No | Yes — this is the supersession note itself |
| UX-013B (Reasoning Accessibility/alignment section) | "All Reasoning Components use the six-level Information Hierarchy consistently... Metadata, labels, contextual text: Level 4–5" | States metadata sits partly at Level 4 | Correct to: metadata sits at Levels 5–6 only; Level 4 is exclusively Challenges/contradiction content | Yes — one clause corrected | No | No | Yes — dated correction note |

**This plan preserves:** UX-012A's six-level content-importance hierarchy (adopted, not UX-012's original); Challenges fixed permanently at Level 4; "Structural Element" repositioned as cross-cutting typography, never a competing level — exactly as ADR-002 states, with no further interpretation introduced here.

**Order of correction:** UX-012 first (it is already the sole authority — see Section 15's rationale), then UX-012A's status update, then UX-013B's Level 4 reference. UX-012 must be corrected before UX-012A's status note is written, since the note credits UX-012's *corrected* text, not its original.

## 7. C-02 Correction Plan — AI Authorship and Provenance

| File | Current rule | Target rule | Terminology correction | State/API implications | Rendering implications | Historical implications | Migration note required |
|---|---|---|---|---|---|---|---|
| UX-012B, lines 243, 245, 490, 660 | "Accept... becomes user-modified-from-atlas" (authorship transfers on Accept alone) | Accept alone → "Atlas suggested / User accepted"; only a subsequent edit → "User authored" | Retire "user-modified-from-atlas" as an Accept-triggered state name; retain it only as the name for the state reached after a genuine subsequent edit | The state model gains an intermediate state ("Accepted, unedited") not previously named in UX-012B | Accepted-but-unedited content now displays "Atlas Suggested / User Accepted," not "user-modified" | None — no historical/recorded content is affected, only the pre-recording live-editing label | Yes, at each of the four passages |
| UX-013B, line 245 (Conclusion component) | "update the attribution silently. Do not prompt the user to confirm" | Behavior unchanged (silent label update on genuine edit remains correct); add: the original Atlas text and acceptance/edit timestamps are separately, permanently preserved in the provenance record regardless of the current label | No terminology change — this passage's own instruction is retained; only a clarifying addition | Add `originalAtlasText`/`acceptedAt`/`editedAt` to this component's own property notes if not already present | No visual change | Clarify explicitly that "silently" governs the label only, never the underlying record | Yes — additive clarification, not a correction of wrong behavior |
| UX-013E, authorship table (per Architecture Review's citation) | `isAtlasGenerated`/`isUserModified`/`authorship` only | Add `originalAtlasText: string | null`, `acceptedAt: timestamp | null`, `editedAt: timestamp | null` | None | Additive properties only — no existing property removed or renamed | No visual change | Establishes the permanent-provenance guarantee at the canonical property-model level | Yes |

**Canonicalization of terms:** "user-authored" is retained as the canonical label for the post-edit state (matches UX-009A's own "User Owned"/"User Authored" tier naming, unaffected). "user-modified" is retained only as the *general* concept name (a field that was Atlas-original and is now user-edited); "user-modified-from-atlas" as a state reached by Accept-alone is retired specifically in UX-012B. "accepted Atlas content" is canonicalized to mean exactly the "Atlas Suggested / User Accepted" state in the table above — this phrase should not, after correction, appear anywhere describing content that has actually been edited.

**This plan preserves:** acceptance does not transfer authorship; a subsequent edit does transfer current authorship, without a confirmation prompt; the provenance record (original text, acceptance timestamp, edit timestamp) remains permanent regardless of the current label; recording locks, never transfers, whatever attribution already exists — exactly as ADR-002 states.

**Order of correction:** UX-012B first (it contains the actual contradiction), UX-013B second (an additive clarification, not urgent relative to UX-012B), UX-013E's authorship-table addition folded into the Phase 4 migration since it lives inside UX-013E's retained-canonical (Reasoning-adjacent) portion.

## 8. C-03 Correction Plan — Decision Workspace Sequence

**Section sequence as currently stated, mapped:**

| File | States a sequence? | Order (positions of Proposed Decision / Supporting / Challenges / Opportunity Cost / Portfolio Consequences) | Compatible with canonical order? |
|---|---|---|---|
| UX-009 | Yes, 13 sections | 3 / 5 / 6 / 7 / 8 | Yes — order already canonical; only 3 of 13 names differ |
| UX-009A | Yes, 13 sections | 3 / 5 / 6 / 7 / 8 | Yes — identical to UX-009; same 3-name naming gap |
| UX-010 | References sections by number and by name throughout | Consistent with UX-009/UX-009A's numbering | Yes — order compatible; uses "Final Decision Summary" naming in several places |
| UX-011 | References sections by number ("Section 1," "Section 3," "Section 12") | Consistent with UX-009/UX-009A's numbering | Yes — no naming or order correction needed; no non-canonical section names found in a direct check |
| UX-012, §17 | Yes, its own 13-item "Reasoning sequence" | 11 / 4 / 5 / 8 / 7 (Proposed Decision moved to 11; Supporting/Challenges shifted to 4/5; Opportunity Cost and Portfolio Consequences swapped to 8/7; spurious "What Changed" inserted at position 3) | **No — this is the outlier requiring correction** |
| UX-013B | States its own Reasoning-component sequence, ending at "Review Conditions," not covering Decision-tier sections | N/A — intentionally scoped to Reasoning components only | Yes, by scope — not a competing claim; validation only |

**For each file:**

- **UX-009**: exact sections to rename — Section 5 "What Supports This Decision" → "Supporting Factors"; Section 6 "What Challenges This Decision" → "Challenges"; Section 12 "Final Decision Summary" → "Final Decision Card." No sections moved, added, or removed. All cross-references within UX-009 to these three names (e.g., "Position: Below What Supports This Decision," line 183) must be updated to match.
- **UX-009A**: identical renaming (Sections 5, 6, 12), plus its own internal cross-references (e.g., "see What Challenges This Decision," line 251) updated to match.
- **UX-010**: every occurrence of "Final Decision Summary" (at least 11 distinct locations, including Section 12 references, the four high-emphasis-moments list, and the post-recording behavior description) becomes "Final Decision Card"; "Section 6 (What Challenges This Decision)" and "Section 5 (What Supports This Decision)" become "Section 6 (Challenges)" and "Section 5 (Supporting Factors)."
- **UX-011**: no correction required — a direct check found no non-canonical section names in this document; only numeric section references, already compatible.
- **UX-012, §17**: replace the entire 13-item "Reasoning sequence" list with the canonical order from ADR-002 (Current Conclusion / Why a Decision Is Required / Proposed Decision / Decision Rationale / Supporting Factors / Challenges / Opportunity Cost / Portfolio Consequences / Assumptions, Monitoring and Invalidation / Implementation Plan / Review Plan / Final Decision Card / Record Decision). The spurious "What Changed" entry is removed entirely, not relocated. UX-012's own Section 17 prose describing "Primary output," "Cognitive mode," etc. is otherwise unaffected.
- **UX-013B**: no direct edit required; add one validation note (not a correction) confirming its own Reasoning-scoped sequence remains non-contradictory after UX-012's §17 is corrected.

**This plan preserves:** Proposed Decision remaining early (position 3) as a testable working hypothesis; no standalone "What Changed" section anywhere in the Decision Workspace sequence; the canonical 13-section sequence exactly as UX-009/UX-009A/UX-010/UX-011 already state it; shorter component names retained only where semantically equivalent (Sections 5, 6, 12) — the sequence itself is not redesigned anywhere in this plan, only renamed in three places and corrected in the one outlier document (UX-012).

## 9. C-04 Correction Plan — Record Decision Completion Gate

| File | Current requirement | Target requirement | Direct semantic edit | Interaction update | Accessibility dependency | Historical-record impact |
|---|---|---|---|---|---|---|
| UX-009, lines 578–586 | Four hard-blocking conditions: decision stated, primary reason authored, **all unacknowledged critical Challenges acknowledged**, implementation type selected | Universal minimum (decision statement + primary reason) hard-blocking; Challenges acknowledgment moves to soft-friction (never hard-blocking); Implementation Plan becomes conditional by decision type; Review Condition becomes required-unless-overridden | Yes — the Challenges bullet is removed from the hard-blocking list and restated as the separate soft-friction rule; Implementation and Review Condition bullets become conditional, per the canonical matrix | The "Record Decision action is disabled until" list is replaced with the canonical matrix's plain-language restatement | Feeds directly into C-06's "unmet required field" definition | None — this is a live-editing rule, not recorded content |
| UX-009A, line 1091 | "four required fields... (decision text, primary reason, implementation type, review trigger)" | Same as above | Yes — full replacement with the canonical matrix | Same | Same | None |
| UX-010, line 751 | "Record Decision reaches availability when four required fields are complete" | Restated to reference the canonical matrix, not a flat count | Yes — minimal, one-sentence correction | Minor — this line is a summary restatement, not the primary rule definition | Same | None |
| UX-012, line 874 and lines 1910–1914 | "Two fields are required for completion" (Question 2 left open) | Universal minimum retained unchanged (Decision Statement + Primary Reason); conditional matrix layered on top; Question 2 marked resolved, citing this correction | Yes — the two-field statement is retained as the *universal minimum* framing (not replaced), with the conditional matrix added as new text; Question 2's own text is updated to state it is resolved | N/A (this document is information-architecture level, not wireframe) | Feeds into C-06 | None |

**Canonical completion matrix** (restated in full here, per ADR-002, for a self-contained correction reference):

*Universal hard-blocking minimum, all decision types:* Decision Statement, Primary Reason.

| Decision type | Implementation Plan required? | Review Condition required? | Portfolio Consequences acknowledgment required? |
|---|---|---|---|
| Action decision (Increase/Reduce/Exit/Initiate) | Yes | Yes, unless explicitly overridden | Yes if portfolio-level; no if single-position |
| No-action/Hold | No | Yes, unless explicitly overridden | As above |
| Deferred | No | Yes — the one field it cannot omit | As above |
| Review outcome | Conditional | Yes, unless explicitly overridden | As above |
| Portfolio-level | Per action/no-action rule | Yes, unless explicitly overridden | Yes, always |
| Conditional implementation | Yes | Yes, unless explicitly overridden | As above |

*Soft friction, never hard-blocking:* unacknowledged Challenges (acknowledgment means "seen and considered," never "agreed with").

*Override path:* an explicit, single-click, logged override statement stands in place of a populated Review Condition where genuinely applicable (e.g., a final exit with no remaining stake).

**Primary source designation:** **UX-012** becomes the primary source for completion-gate semantics generally (it already holds the universal-minimum framing and is the document Question 2 lives in), with **UX-009A** remaining the primary source for the wireframe-level presentation of the gate (field markers, disabled-state visual treatment) — the two are complementary, not competing, once both are corrected to state the identical matrix.

**This plan preserves:** semantic completeness (what must be true) as distinct from interface validation (how it is enforced) as distinct from soft friction (Challenges) as distinct from hard blocking (the universal minimum and conditional fields) as distinct from optional reasoning depth (Assumptions/Opportunity Cost elaboration, Portfolio Consequences detail beyond acknowledgment) — exactly the four-way distinction ADR-002 draws, none of it re-derived or altered here.

## 10. C-05 Correction Plan — UX-013 Trust-Boundary Migration (Plan Only — Not Executed)

**Migration architecture:**

- **The future canonical Foundation & Reasoning assembly document** — new file, new name (see naming strategy below) — retains, verbatim except for the C-01/C-02 corrections already specified in Sections 6–7 above, everything in current UX-013E that reconciles UX-013A and UX-013B: the canonical component taxonomy and classification model, the Foundation- and Reasoning-tier naming/duplicate-component audit, the Figma library architecture for Foundation and Reasoning pages, and the engineering package architecture for the Foundation→Reasoning layers. Status: **Canonical.**
- **The future interim governance document** — new file, deliberately and visibly *not* part of the lettered A/B/C/D/E series (see naming strategy below) — receives everything in current UX-013E concerning Decision, Monitoring, AI Collaboration, and Metadata & System components, restructured under the three-tier classification ADR-001/ADR-002 require. Status: **Interim — Provenance Classified, Not Canonical.**

**Which sections of current UX-013E move to each:** Sections covering the canonical classification model, the Foundation/Reasoning component inventories, the Foundation/Reasoning duplicate-audit and naming-reconciliation tables, and the Figma/engineering architecture for those two tiers move to the canonical assembly. Sections covering Decision, Monitoring, AI Collaboration, and Metadata & System component inventories, their duplicate-audit tables, and their Figma/engineering architecture move to the interim document. Cross-cutting sections that apply to the whole library (e.g., general governance, general testing standards, general versioning rules) are duplicated into both documents only where genuinely needed by each, or — preferably — retained once in the canonical assembly and referenced (not duplicated) by the interim document, to avoid the two documents drifting apart over time.

**Which sections remain (in the original UX-013E file):** none are edited in place. The original file is preserved verbatim; only its `Status:`/governing-description text at the top changes (see below).

**How internal links and governing references change:** every place in the corpus that currently cites "UX-013E" as the authority for a Decision, Monitoring, AI-Collaboration, or Metadata claim must, after migration, cite the new interim document by its new name, with the three-tier classification noted at the point of citation (e.g., "per the interim governance note, independently confirmed" vs. "...currently unconfirmed"). Citations to Foundation/Reasoning content continue to resolve to the new canonical assembly document.

**How claim-level three-tier classification is represented:** within the interim document, every claim inherited from current UX-013E's Decision/Monitoring/AI-Collaboration/Metadata content is tagged as exactly one of: **(1) Independently Confirmed** — the broad concept is corroborated by UX-012 or another present document, cited by name; **(2) Unconfirmed** — the claim traces only to the absent UX-013C/UX-013D and has no independent corroboration; **(3) To Be Authored** — an explicit statement that this content awaits genuine specification work, naming that work as the commissioning trigger (below), not an indefinite deferral.

**How independently confirmed claims are distinguished from unconfirmed granular claims:** by the tag in (2) above, applied per claim or per closely-related group of claims (per ADR-001's "per claim or per section" requirement) — never one blanket status for the whole document.

**How the commissioning trigger for genuine UX-013C and UX-013D is recorded:** the interim document's own closing section states, explicitly, that genuine, newly-authored, honestly-dated UX-013C ("Decision & Monitoring Components") and UX-013D ("AI Collaboration, Metadata & System Components") specifications are the scheduled replacement for this interim document, following the same authorship process UX-013A and UX-013B themselves used, citing UX-012 (corrected) and all other approved specifications as governing references — this is recorded as a commitment with a named next step (Section 23 of this plan), not as an open-ended aspiration.

**How future UX-013C and UX-013D will supersede the interim note:** once genuinely authored, each new volume supersedes the corresponding portion of the interim document exactly as UX-012 superseded UX-012A–D — the interim document's own `Status:` line is then updated to "Superseded — see UX-013C / UX-013D," its body left unedited, per the same non-erasure principle applied throughout this plan.

**How no fictional historical lineage is created:** the interim document's own front matter states plainly that it was assembled on the date of migration, from content previously held in UX-013E (itself dated to its own original authorship), and that it does not claim UX-013C or UX-013D ever existed prior to this point. This is the same disclosure ADR-001 requires of any future genuinely-authored UX-013C/UX-013D.

**Naming strategy — evaluated and selected.** Two strategies were considered:

- *Strategy 1 — rename the existing UX-013E file in place* to reflect its narrower, post-split scope. Rejected: this would silently change what "UX-013E" means to any existing reference or citation, in place, which is a subtler but real form of the same non-traceability risk ADR-001 warns against — a filename that used to mean "the full final assembly" would come to mean something narrower with no visible signal of the change.
- *Strategy 2 — preserve the existing UX-013E file exactly as committed (mark its `Status:` line Superseded, per the identical precedent already applied to UX-012A), and create two genuinely new files with new names.* **Selected.** This mirrors the UX-012A precedent exactly (Section 6), is lower-risk (no existing citation to "UX-013E" silently changes meaning), and lets the two new documents' names themselves carry the trust-boundary signal.

**Selected names:** `UX-013F-Foundation-Reasoning-Component-Library-Assembly.md` for the canonical assembly — continuing the established A/B/C/D/E lettering convention with the next available letter, signaling that this is a genuine peer volume of equivalent standing to its predecessors. `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md` for the interim document — deliberately **not** given a letter in the A–F sequence, specifically so its provisional, non-canonical status is visible in its filename alone, not only in its internal content, consistent with Option F's own philosophy of making the trust boundary structural, not merely textual.

**How Git history preserves traceability through the split:** the original `UX-013E-...md` file is not deleted, renamed, or `git mv`-ed — it remains, unedited in body, with only its status line updated, so its full commit history remains attached to its own, unchanged path. The two new files are added as new files in a single, dedicated commit (Section 16, Commit 6) whose message states explicitly that their content originates from `UX-013E-...md` as of the commit that last touched it, providing a textual (not merely structural) pointer a future `git blame`/`git log --follow` investigation can corroborate.

## 11. C-06 Correction Plan — Unavailable Primary Action Accessibility

| File | Current language | Target interaction contract | Native `disabled` removed/qualified? | Keyboard behavior | Pointer behavior | Screen-reader behavior | Mobile behavior | Error/help text behavior |
|---|---|---|---|---|---|---|---|---|
| UX-009A, line 622 | "Disabled state: — Reduced emphasis, cursor: not-allowed" (unqualified) | `aria-disabled="true"`, never native `disabled`; permanently focusable; activation navigates to first unmet field | Qualified — add the `aria-disabled`-not-`disabled` instruction directly at this line | Remains in tab order; Enter/Space navigates to first unmet field | Click navigates to first unmet field | Announces label + reason via `aria-describedby` | Identical contract, no special-casing | Unaffected — existing adjacent-explanation behavior retained |
| UX-010, line 611 (and surrounding "Disabled state" language) | States the focus-announcement requirement without stating the underlying mechanism | Same target contract | Qualified — add the mechanism note alongside the existing, correct announcement requirement | Same | Same | Same, made explicit at the mechanism level | Same | Unaffected |

**Primary accessibility authority designation:** **UX-013A** becomes the primary accessibility authority for this specific interaction pattern going forward (it already states the correct, complete contract at lines 457, 482, and 588), with UX-009A and UX-010 corrected to match it rather than UX-013A being altered to match them.

**This plan preserves:** the exact canonical interaction contract from ADR-002 — `aria-disabled="true"` always; permanent focusability and tab-order membership; blocked activation navigating to the first unmet required field (feeding directly from Section 9's completion matrix) and re-announcing the reason; visible and screen-reader-accessible explanation; equivalent keyboard/pointer/mobile/touch behavior — none of it re-derived here.

## 12. Authority and Supersession Corrections

| File | Current claim | Target claim | Future document status | Correction note/changelog entry required? |
|---|---|---|---|---|
| UX-012 | "Final Governing Document... assembled from UX-012A–D... all prior part documents (012A–D) are superseded" | Unchanged claim, now backed by an actually-corrected §5 and §17 | Canonical (unchanged) | Yes — amendment note for the §5/§17 corrections specifically |
| UX-012A | `Status: Foundation Specification Complete` | `Status: Superseded — see UX-012 §5 (Level 2/4, corrected per ADR-002 C-01)` | Superseded (newly and explicitly marked, though already implied by UX-012's own existing text) | Yes |
| UX-013E | Opening: "It supersedes UX-013A through UX-013D... assembled from" UX-013C/UX-013D as if settled fact | Corrected, at time of migration (Phase 4), to: superseded by `UX-013F` for Foundation/Reasoning authority, and by the new interim document for Decision/Monitoring/AI/Metadata content, with UX-013C/UX-013D provenance explicitly marked unconfirmed pending genuine authorship | Superseded (both successors named) | Yes — this is the single largest authority correction in this plan |

**UX-012 versus UX-012A–D:** already a clean supersession chain per the Architecture Review's own Section 4 finding; this plan's only correction is UX-012A's own status line, for the reason given in Section 6 — UX-012B, UX-012C, and UX-012D's own status lines are **not** touched by this plan, since none of their content is directly implicated by any of the six decisions, and touching them merely for tidiness would be scope creep beyond what ADR-002 requires (Section 21).

**UX-013E versus UX-013A/013B and absent UX-013C/013D:** the one authority relationship in this entire corpus resting on unverifiable provenance; fully addressed by Section 10's migration plan, not by a simple status-line edit, since the underlying content (not just the claim) must be reorganized.

**No document elsewhere in the corpus was found, during this planning pass, to claim final authority while containing text superseded by ADR-002**, beyond the three rows above.

## 13. Terminology Canonicalization Required by the Six Decisions

Only terminology changes required to implement ADR-002 — no broader terminology normalization (Architecture Review Section 5's Medium/Low findings, e.g. "Blocking" vs. "Unresolved" Challenge-severity naming, or "Read-only" vs. "Locked," are explicitly **not** included here; see Section 21).

| Current variant(s) | Canonical term | Documents affected | Semantic reason | Aliases permitted in historical quotations/examples? |
|---|---|---|---|---|
| "What Supports This Decision" | Supporting Factors | UX-009, UX-009A, UX-010 | Matches the actual named Reasoning component (UX-013B) that populates this section | Yes — a corrected document's own amendment note may quote the original name verbatim as historical record |
| "What Challenges This Decision" | Challenges | UX-009, UX-009A, UX-010 | Same reason | Yes, same basis |
| "Final Decision Summary" | Final Decision Card | UX-009, UX-009A, UX-010 | Matches UX-012/UX-012B's already-established component name | Yes, same basis |
| "user-modified-from-atlas" (as an Accept-triggered state) | Retired in that specific usage; retained only for the genuine post-edit state | UX-012B | Accept alone must not read as authorship transfer | Yes, in the amendment note quoting the original passage |
| "Structural Element" (as a hierarchy level) | Retired as a level name; retained as "typographic convention" | UX-012 | No longer a competing rank in the hierarchy | Yes, in the amendment note |
| "Contextual Information" (as Level 4) | Retired at Level 4; redistributed to Levels 5–6 | UX-012 | Level 4 is now exclusively Challenges/contradiction | Yes, in the amendment note |

## 14. Correction Phases

### Phase 0 — Baseline and Safety Verification
**Files changed:** none. **Dependencies:** none. **Entry criteria:** ADR-002 accepted (already true, per this plan's own premise). **Exit criteria:** confirmed clean working tree, confirmed HEAD, confirmed byte-for-byte baseline snapshot (checksums) of all 18 source files recorded for later diff verification. **Implementation status:** remains fully blocked wherever it already was (this phase changes nothing). **Recommended commit boundary:** none — no commit in this phase.

### Phase 1 — Primary Governing Semantics
**Files changed:** UX-012 (§5 for C-01, §17 for C-03, line 874/Question 2 for C-04). **Dependencies:** Phase 0 complete. **Entry criteria:** Phase 0 exit criteria met. **Exit criteria:** UX-012 alone, read in isolation, states the corrected hierarchy, the corrected section sequence, and the corrected completion-gate framing, with no internal contradiction. **Implementation status:** Reasoning-tier and Decision-Workspace-composition work may now cite UX-012 directly, per ADR-002's own "Unblocked by resolution design alone" findings — this phase does not newly unblock anything ADR-002/the Resolution Design did not already unblock; it simply makes UX-012's own text match what was already the operative rule. **Recommended commit boundary:** one commit, UX-012 only (Section 16, Commit 1).

### Phase 2 — Dependent Workspace Documents
**Files changed:** UX-009, UX-009A, UX-010 (naming per C-03; field-count/hard-block correction per C-04; `aria-disabled` clarification per C-06). **Dependencies:** Phase 1 complete (these corrections reference the now-corrected UX-012 naming and matrix, so they should read consistently with it, though none of them structurally depend on UX-012's own file content to be edited). **Entry criteria:** Phase 1 exit criteria met. **Exit criteria:** UX-009, UX-009A, and UX-010, read together, state one section order with one set of names, one completion matrix, and one accessibility contract, with no internal contradiction among the three. **Implementation status:** unchanged from Phase 1 in terms of what's unblocked — this phase closes wording, not scope. **Recommended commit boundary:** one commit for the three files together, since all three corrections in this phase are small, mechanically similar (naming/field-count/ARIA), and closely coupled (Section 16, Commit 2) — or, if narrower review is preferred, up to three commits split by finding (C-03 naming; C-04 field-count; C-06 ARIA) rather than by file, since the same finding's correction touches multiple files identically.

### Phase 3 — Design-System and Component Documents
**Files changed:** UX-012A (status line only), UX-012B (four passages), UX-013B (Level 4 reference + Conclusion-component clarifying note). **Dependencies:** Phase 1 complete (UX-012A's note credits UX-012's corrected text; UX-012B's correction should be consistent with UX-012's already-correct line 1171). **Entry criteria:** Phase 1 exit criteria met (Phase 2 need not be complete first, since Phase 3's files are independent of Phase 2's). **Exit criteria:** UX-012A carries an accurate Superseded status; UX-012B no longer contradicts the two-step authorship model; UX-013B's Level 4 reference and Conclusion note match the corrected hierarchy and authorship model. **Implementation status:** Reasoning-tier implementation, already unblocked, now has fully consistent source text to build from with no remaining internal contradiction. **Recommended commit boundary:** one commit (Section 16, Commit 3), since all three files here serve the same underlying purpose (bringing the Design-System/Reasoning tier into agreement with Phase 1's corrected hub document).

### Phase 4 — UX-013E Trust-Boundary Migration
**Files changed:** UX-013E (status line only, body unedited); two new files created (`UX-013F-...md`, `UX-013-Interim-...md`). **Dependencies:** Phases 1–3 complete — this is a hard dependency, not a preference, since the new documents must reference the already-corrected hierarchy, authorship model, section order, completion gate, and disabled-control contract, per the Resolution Design's own Section 9 sequencing rule. **Entry criteria:** Phases 1–3 exit criteria all met and validated (Section 18). **Exit criteria:** the split is structurally complete; the interim document's three-tier classification is internally consistent and cites no fabricated history; UX-013E's own status line accurately points to both successors. **Implementation status:** Foundation/Reasoning-tier Figma and engineering package architecture may now cite `UX-013F` directly; Decision/Monitoring/AI-Collaboration/Metadata implementation remains blocked, exactly as before, pending the genuine authorship named as this phase's own commissioning trigger. **Recommended commit boundary:** one commit (Section 16, Commit 4).

### Phase 5 — Cross-Reference, Authority, and Changelog Corrections
**Files changed:** none new — this phase is a corpus-wide sweep confirming every changelog/amendment note required by Sections 6–12 above is present and correctly dated, and that no file outside the seven already corrected contains a stale cross-reference to a pre-correction name or claim (e.g., a document citing "UX-013E" for Decision-tier content that should now cite the interim document). **Dependencies:** Phase 4 complete. **Entry criteria:** Phase 4 exit criteria met. **Exit criteria:** zero stale cross-references found corpus-wide (Section 18's search patterns). **Implementation status:** unchanged. **Recommended commit boundary:** a small cleanup commit only if any stale cross-reference is actually found (Section 16, Commit 5) — otherwise this phase may close with no commit at all.

### Phase 6 — Corpus Validation
**Files changed:** none. **Dependencies:** Phase 5 complete. **Entry criteria:** Phase 5 exit criteria met. **Exit criteria:** the full validation plan (Section 18) passes in its entirety. **Implementation status:** this phase is the formal close-out confirming the correction program's own success criteria; it does not itself change what is or isn't implementation-blocked. **Recommended commit boundary:** none — this is a verification pass, not a content change; its result (pass/fail) is reported, not committed.

**No phase combines unrelated semantic corrections merely to reduce commit count** — Phase 2's grouping of C-03/C-04/C-06 corrections across three files is justified because all three corrections are small, mechanically similar, and mutually reinforcing within the same three closely-related documents, not because grouping them is convenient; Phase 4 is kept entirely separate from Phases 1–3 specifically because it is structurally different work (a document split, not a text correction) with a hard sequencing dependency on everything before it.

## 15. Exact File Change Order

1. **UX-012** — changed first because it is already the sole, currently-authoritative assembled Design System document (its own text already declares 012A–D superseded); three of the six findings (C-01, C-03, C-04) require correcting it directly, and every other correction in this plan is written to be consistent with UX-012's *corrected* state, not its original. Nothing must be stable before this step; everything after it depends on it.
2. **UX-012A** (status line only) — depends on step 1, because its amendment note explicitly credits UX-012's now-corrected Level 2/4 wording; performing this step before step 1 would credit text that did not yet exist.
3. **UX-012B** — depends on step 1 only loosely (its own correction is independent content, but should be written consistent with UX-012's already-correct line 1171, unaffected by step 1 in any case); no later file depends on UX-012B specifically, other than the general corpus-consistency check in Phase 5.
4. **UX-009, UX-009A, UX-010** (as one grouped step, or three sequential steps) — depend on step 1 for naming consistency (Sections 5/6/12) and for the completion-gate matrix's exact wording; no file later in this order depends on these three specifically, other than Phase 5's cross-reference sweep.
5. **UX-013B** — depends on step 1 (Level 4 reference) and is independent of steps 2–4; later depended on by step 6.
6. **UX-013E status line, plus creation of `UX-013F-...md` and `UX-013-Interim-...md`** — depends on steps 1–5 all being complete and stable, since the new documents' own content must reference the corrected hierarchy, authorship model, section order, completion gate, and disabled-control contract established by every step before this one. This is the last content-bearing step.
7. **Corpus-wide cross-reference sweep** (Phase 5) — depends on step 6, since it specifically checks for stale references to pre-migration UX-013E claims.

This order prevents exactly the failure mode ADR-002's own Resolution Design warned against: correcting a dependent or assembled document before its own governing semantics (in UX-012, and later in the corrected Sections 6–13 of this plan) are stable.

## 16. Proposed Commit Plan

No commit is performed by this planning task. The following sequence is proposed for the future execution task.

**Commit 1 — Correct UX-012 (C-01, C-03, C-04).**
Files: `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md`.
Findings resolved: C-01 (§5), C-03 (§17), C-04 (line 874, Question 2).
Validation required: UX-012 alone is internally consistent (no remaining Level-4/Challenges omission; §17 matches the canonical 13-section order; Question 2 marked resolved).
Suggested commit message: `docs(ux): correct UX-012 hierarchy, sequence, and completion gate per ADR-002`

**Commit 2 — Correct Decision Workspace dependent documents (C-03 naming, C-04, C-06).**
Files: `UX-009-Decision-Workspace-Screen-Specification.md`, `UX-009A-Decision-Workspace-Wireframe-Specification.md`, `UX-010-Decision-Workspace-Interaction-Microinteraction-Specification.md`.
Findings resolved: C-03 (naming only), C-04 (field-count/hard-block correction), C-06 (`aria-disabled` clarification).
Validation required: the three files, read together, state one section-naming convention, one completion matrix, one accessibility contract.
Suggested commit message: `docs(ux): align UX-009/009A/010 naming, completion gate, and accessibility with ADR-002`

**Commit 3 — Correct Design-System and Reasoning documents (C-01, C-02).**
Files: `UX-012A-Atlas-Design-System-Foundations.md` (status only), `UX-012B-Atlas-Design-System-Components-Reusable-Patterns.md`, `UX-013B-Atlas-Component-Specification-Reasoning-Components.md`.
Findings resolved: C-01 (UX-012A status, UX-013B Level 4), C-02 (UX-012B, UX-013B).
Validation required: UX-012A's status line accurately reflects supersession; UX-012B no longer states an Accept-alone authorship transfer; UX-013B's Level 4 and provenance notes match the corrected models.
Suggested commit message: `docs(ux): mark UX-012A superseded; correct UX-012B authorship rule and UX-013B references`

**Commit 4 — UX-013E trust-boundary migration.**
Files: `UX-013E-...md` (status line only), new `UX-013F-Foundation-Reasoning-Component-Library-Assembly.md`, new `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md`.
Findings resolved: C-02 (authorship-table addition, folded in), C-05 (full migration).
Validation required: UX-013E's own status line names both successors; the new canonical assembly and interim documents are each internally consistent; the interim document's three-tier classification is complete and cites no fabricated history.
Suggested commit message: `docs(ux): split UX-013E into UX-013F (canonical) and an interim Decision/Monitoring/AI governance note per ADR-001/ADR-002`

**Commit 5 — Cross-reference sweep (conditional).**
Files: any file found, during Phase 5, to contain a stale reference.
Findings resolved: none new — cleanup only.
Validation required: zero remaining stale references corpus-wide.
Suggested commit message: `docs(ux): correct remaining cross-references to superseded UX-013E claims`
*(Omitted entirely if Phase 5 finds nothing to correct.)*

Each commit is scoped to one phase's worth of closely-related findings, is independently reviewable, and is independently revertible without affecting the others, since no commit's own file set overlaps another's.

## 17. Changelog and Historical Traceability Strategy

**Selected strategy: a combination — a short, standardized correction-notice block added near each corrected document's own existing title/metadata block, plus reliance on ordinary Git history for the full diff record.** Document-local changelog *sections* (a running list at the bottom of each file) were considered and rejected as the sole mechanism, since they would grow indefinitely and duplicate what Git already records faithfully; Git history alone was considered and rejected as insufficient by itself, since a reader opening the document directly (not its Git log) would have no in-document signal that a correction occurred at all.

**The standardized notice**, placed immediately after each corrected document's existing metadata block (Status/Owner/Depends-on lines), reads:

> **Corrected [date]:** [one-sentence description of what changed], per ADR-002 (Finding C-0N) / ADR-001, as planned in the Atlas UX Source Correction Plan. Prior text: "[short verbatim excerpt of the superseded passage]." See `git log` for the full diff.

Every corrected document records: its original status (unchanged, stated as it always was); the correction date (the actual date of the future execution task, never back-dated); the governing ADR and finding ID; a one-sentence description of the semantic change; a short verbatim quotation of the original, now-superseded text (so the historical fact that a different statement once existed is visible without requiring a Git-log lookup); and, where relevant, an explicit note that unchanged surrounding content remains historical context, not itself corrected.

**Original authorship dates are never altered.** A document's own original `Status:`/date framing is left exactly as it was; the correction notice is additive, clearly dated to the correction itself, and never merged into or mistaken for the document's original authorship record.

## 18. Validation Plan

Deterministic checks to run after Phase 6 (and, where noted, after each earlier phase):

- **All six ADR decisions reflected consistently:** grep every corrected file for the exact canonical terms (Level names, section names, completion-matrix language, authorship labels, `aria-disabled`) and confirm no corrected file still contains its own pre-correction wording outside a quoted correction notice.
- **No remaining contradictory hierarchy definitions:** search corpus-wide for `Level 1` through `Level 6` (or `Level 1 —` style headers); confirm exactly one six-level definition exists (in UX-012, post-correction) and that UX-012A's own body text is unedited but its status line is Superseded.
- **One Decision Workspace sequence:** search corpus-wide for `Section 1 —` through `Section 13 —` style headers or equivalent numbered lists in UX-009, UX-009A, UX-010, UX-011, UX-012; confirm all agree on both order and the Section 5/6/12 canonical names.
- **One completion matrix:** search for `required field`, `four required`, `two field`, `Two fields are required` corpus-wide; confirm no remaining flat-count statement exists anywhere outside a quoted correction notice.
- **One authorship/provenance model:** search for `user-modified-from-atlas`, `Atlas suggested`, `User accepted`, `User authored`, `isAtlasGenerated`, `isUserModified` corpus-wide; confirm UX-012B no longer states an Accept-alone transfer outside a quoted correction notice.
- **One unavailable-action accessibility contract:** search for `disabled` (bare) and `aria-disabled` corpus-wide; confirm every occurrence of "disabled" applied to the Record Decision control is paired with, or superseded by, the `aria-disabled` qualification.
- **Truthful UX-013 authority chain:** confirm UX-013E's status line names both successors; confirm the interim document's own front matter states its assembly date and disclaims any prior existence of UX-013C/UX-013D; confirm no document anywhere claims UX-013C or UX-013D as an existing, consulted source.
- **No references to nonexistent governing sources:** re-run the same corpus-wide citation check the original Architecture Review performed (grep for `UX-013C`, `UX-013D`, `UX-006`, `UX-007` as bare document citations) and confirm every remaining citation is to the interim document or is explicitly marked unconfirmed/to-be-authored, never to a document presented as settled.
- **No accidental semantic changes outside scope:** `git diff` review (below) confirms every changed line traces to one of the six findings; any unexplained line change is treated as a defect in the correction, not accepted.
- **Valid Markdown and UTF-8:** re-run the same `file -I` encoding check and a Markdown lint pass used during the original import, on every corrected and newly-created file.
- **Internal link validation:** if any document uses relative links to another document in this corpus, confirm every link target still exists post-migration (relevant specifically to the UX-013E split).
- **Filename/title consistency:** confirm every corrected or new file's own first-heading title still matches its filename's UX identifier, exactly as verified during the original import (Section 3a of the import task).
- **Duplicate-content check:** `md5`/checksum comparison across all files post-correction, confirming no accidental byte-identical duplicate was introduced (mirroring the original import's own duplicate check).
- **Git diff review:** a full, human review of `git diff` for every commit in Section 16, confirming the diff contains only the described correction and nothing else.
- **Targeted term searches**, as exact patterns to run: `grep -rn "Structural Element" docs/atlas_ux/*.md`, `grep -rn "Contextual Information" docs/atlas_ux/*.md`, `grep -rn "user-modified-from-atlas" docs/atlas_ux/*.md`, `grep -rn "What Supports This Decision\|What Challenges This Decision\|Final Decision Summary" docs/atlas_ux/*.md`, `grep -rn "four required\|Two fields are required" docs/atlas_ux/*.md`, `grep -rn "\bdisabled\b" docs/atlas_ux/UX-009A*.md docs/atlas_ux/UX-010*.md` — each should return zero matches outside a quoted correction notice once Phase 6 is complete.

## 19. Implementation Unblocking Criteria

| Area | Unblocked after |
|---|---|
| Foundation Components | Already unblocked (ADR-002/Resolution Design); this correction program does not change that — no phase is a precondition |
| Reasoning Components | Already unblocked in principle; **fully, textually consistent** only after Phase 3 |
| Decision Components | Partially unblocked already (basic Final Decision Card shape); **fully unblocked only after genuine UX-013C-equivalent authorship** (later implementation evidence/future task, not this program) |
| Monitoring Components | Blocked until genuine UX-013C-equivalent authorship — this program (through Phase 4) only makes the block honest and structurally clear; it does not remove it |
| AI Collaboration Components | Blocked until genuine UX-013D-equivalent authorship, for the same reason, and additionally gated on Phase 3's C-02 correction being consistently reflected |
| Metadata and System Components | Blocked until genuine UX-013D-equivalent authorship |
| Decision Workspace composition | Already usable against this plan/ADR-002 directly; **textually consistent in the source documents themselves only after Phase 2** |
| Figma library architecture | Foundation/Reasoning pages: unblocked already, fully consistent after Phase 4 (once `UX-013F` exists); Decision/Monitoring/AI-Collaboration pages: blocked until genuine authorship, same as the components above |
| Engineering package architecture | Foundation→Reasoning layers: unblocked already; Decision/Monitoring/AI-Collaboration layers: blocked until genuine authorship |

**No area in this table becomes unblocked, in a way it was not already, merely by this correction program's completion** — the program closes a documentation-consistency gap, not an implementation-readiness gap; the two genuinely new implementation-readiness gates (Decision/Monitoring/AI-Collaboration/Metadata component tiers) remain gated on the same future authorship work ADR-002 already named, not on anything in this plan.

## 20. Risks and Rollback

| Risk | Prevention | Detection | Rollback |
|---|---|---|---|
| Accidental redesign (a correction drifts into a new design decision) | Every correction in Sections 6–13 is stated as a direct restatement of an already-quoted ADR-002 rule, with no new judgment introduced | `git diff` review (Section 18) checking every changed line traces to a named finding | Revert the specific commit (Section 16 commits are narrow and independently revertible) |
| Historical erasure (a correction silently deletes the record that different text once existed) | Section 17's mandatory correction-notice-with-verbatim-quotation requirement | Spot-check corrected files for the presence of a correction notice wherever a `git diff` shows a semantic change | Revert and re-apply with the missing notice added |
| Over-correction (fixing Medium/Low findings not required by the six decisions) | Section 4's explicit "no correction required" classification for 11 of 18 files, and Section 21's explicit non-goals | `git diff` review confirming no changed file lies outside the seven named in Section 4 | Revert the specific over-scoped change |
| Authority loops (a corrected document ends up citing another document that itself still contains the pre-correction claim) | Section 15's strict file-change order, and Phase 5's dedicated cross-reference sweep | Phase 5's own validation pass | Correct the missed cross-reference as a small, additional Phase 5 commit |
| Broken links (a relative link inside a document breaks after the UX-013E split) | Section 10's explicit "how internal links... change" requirement, checked in Phase 4's exit criteria | Section 18's internal-link validation step | Fix the specific link; low-risk, isolated correction |
| Renaming ambiguity (a future reader confuses `UX-013E` with `UX-013F`) | The deliberate naming-strategy choice in Section 10 (keep UX-013E as-is, clearly Superseded; give the new canonical document a new, sequential letter) | Manual review of UX-013E's own corrected status line for clarity | Strengthen the status-line wording; does not require reverting file structure |
| UX-013 split losing Git traceability | Section 10's explicit requirement that the original file is never `git mv`-ed, only status-edited, plus the new files' own commit message pointing back to it | `git log --follow` on the original UX-013E path, confirmed still intact post-migration | Not applicable — this risk is prevented structurally, not merely detected |
| Implementation beginning against mixed authority (a team builds against a half-corrected corpus) | ADR-002's own Implementation Constraint (already in force, unaffected by this plan) plus this plan's own phase-by-phase exit criteria | Any implementation task should cite this plan's own Section 19 unblocking table before beginning Decision/Monitoring/AI-Collaboration work specifically | Not a rollback scenario — the constraint is preventative, not corrective |

## 21. Explicit Non-Goals

This correction program does not:

- resolve Medium or Low findings from the Architecture Review unless directly required by one of the six accepted decisions (e.g., the "Blocking" vs. "Unresolved" Challenge-severity naming conflict, the UX-012D/UX-013A token-identity mismatch, and the zoom 200%/400% discrepancy all remain untouched, since none is one of C-01 through C-06);
- redesign any Workspace;
- invent missing product behavior;
- reconstruct missing historical documents (UX-006, UX-007, UX-013C, UX-013D remain unaddressed by this program beyond the interim classification and commissioning-trigger language required by C-05);
- create UX-013C or UX-013D as part of this source-correction program — that is separate, future, genuinely-new authorship work, only scheduled and named here, never performed here;
- begin implementation of any kind;
- normalize unrelated terminology beyond the specific canonicalizations Section 13 lists as required by the six decisions.

## 22. Open Questions

**Q1 — Who owns and schedules the actual execution of this plan's phases, and on what timeline?** *Why unresolved:* neither ADR-001 nor ADR-002 assigns ownership or a deadline for source correction, and this plan, being planning-only, cannot assign one either. *Decision owner:* not established by any prior document. *Blocks a phase:* blocks the start of Phase 1 specifically (execution cannot begin without an owner), though it does not affect this plan's own completeness. *Latest phase by which it must be answered:* before Phase 0 begins.

**Q2 — Should the Phase 5 cross-reference sweep be automated (a script checking every citation pattern) or performed as a manual review?** *Why unresolved:* this is a tooling/process decision outside the scope of either ADR; the six accepted decisions say nothing about correction-program tooling. *Decision owner:* whoever executes Phase 5. *Blocks a phase:* does not block any phase's entry criteria — either approach satisfies Phase 5's exit criteria — but affects how much confidence the exit criteria check carries. *Latest phase by which it must be answered:* before Phase 5 begins.

**Q3 — Should the new interim governance document (Section 10) be reviewed by the same process that produced ADR-001/ADR-002 before Phase 4 is executed, or is this plan's own specification of its structure sufficient authorization?** *Why unresolved:* this plan specifies the interim document's required structure in full (Section 10) but does not itself constitute a review of a drafted instance of that document — a draft has not yet been written. *Decision owner:* whoever authorizes Phase 4's execution. *Blocks a phase:* potentially blocks Phase 4 specifically, if a review step is deemed necessary before the split is executed rather than after. *Latest phase by which it must be answered:* before Phase 4 begins.

None of these three questions reopens any of the six accepted decisions; each concerns only the *process* of executing corrections already fully specified above.

## 23. Recommended Execution Task

**Execute Phase 0 and Phase 1 of the Atlas UX Source Correction Plan.**

This is the correct first execution slice, not performed within this planning task, for three reasons. First, Phase 0 (baseline/safety verification) and Phase 1 (correcting UX-012 alone) together resolve the single highest-leverage item in the entire program: UX-012 is named in three of the six decisions (C-01, C-03, C-04) and, per Section 15, is the one document every other correction in this plan is written to be consistent with — correcting it first, and only it, produces the largest reduction in corpus contradiction for the smallest, most independently-reviewable change (one file, one commit). Second, Phase 1 has no dependency on any other phase, so it can begin immediately upon this plan's approval, without waiting on any open question in Section 22. Third, treating Phase 0+1 as one bounded execution task (rather than authorizing the full six-phase program at once) preserves this program's own stated discipline of narrow, reviewable, independently-revertible units of work — exactly the posture Section 3's "minimal necessary change" and Section 16's "one concern per commit" principles require, applied at the level of task authorization itself, not only at the level of individual commits.

## 24. Working Tree Verification

**Branch:** main
**HEAD:** `3f06e0375b8ae14ec9e34bb2e1ab60e711a8ac85` ("docs: review and govern Atlas UX architecture") — unchanged throughout this task.
**Files created:** `docs/atlas_ux/governance/Atlas-UX-Source-Correction-Plan.md` (this document). No new directory was required — `docs/atlas_ux/governance/` already existed.
**Files modified:** none. No UX source document under `docs/atlas_ux/*.md` was changed. `ADR-001-Missing-Source-Volume-Governance.md` and `ADR-002-Critical-UX-Architecture-Resolutions.md` were not modified. Neither `UX-Architecture-Review-001.md` nor `UX-Critical-Findings-Resolution-Design-001.md` was modified.
**Staged files:** none.
**Untracked files:** `docs/atlas_ux/governance/Atlas-UX-Source-Correction-Plan.md`.

No commit was made.

# ADR-004 — Scenario Analysis, Comparison, and UX-013B Sequence Authority Resolution

## Status

Accepted

## Date

2026-07-26

## Decision Owners / Authority

Formulated following the same process that produced `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`: a dedicated, read-only architectural investigation (the "Scenario Analysis / Comparison Architectural Investigation," performed against HEAD `867a0338e8ce8eed5c6c70cd6407ec68b32bcd94`), followed by this formal decision document. This ADR is **Accepted governance following independent review**. Its authority is limited to the architectural decisions stated here; downstream source correction remains subject to the separately authorized governance steps identified by this ADR.

## Context

`UX-Architecture-Review-001.md` identified, as its own **Finding 8.3** (severity Medium, listed in the findings summary as **M-6**), that Scenario Analysis (a standalone Reasoning component specified in `UX-013B-Atlas-Component-Specification-Reasoning-Components.md`) and "Scenario Comparison" (one of five types named in UX-013B's own Comparison component prose) both structure "potential outcomes under different conditions" and were never fully reconciled by the document whose job is reconciliation (`UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md`). Finding 8.6 (same review) cautions against reflexively merging components in this family of findings, observing that the pattern across the review is usually naming/classification drift rather than true redundancy, and that "the correct fix in every case is a single naming/classification decision, not a merge."

This question was separately, explicitly held open by `ADR-002-Critical-UX-Architecture-Resolutions.md` C-03 (which adopted the canonical thirteen-item Decision Workspace sequence but does not mention Scenario Analysis or Comparison anywhere in it) and by `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` (which resolved a structurally adjacent question — Recommendation's identity and canonical status — while explicitly declining to resolve this one: "This ADR does not decide Scenario Analysis's or Comparison's own placement or status," R-06). The Atlas UX Source Correction Plan's Phase 3D-2a (governed by ADR-002, implemented at commit `867a0338e8ce8eed5c6c70cd6407ec68b32bcd94`) performed two narrow, mechanical corrections to UX-013B's §14 "Decision Workspace sequence" list and explicitly left Scenario Analysis (position 9) and Comparison (position 10) untouched, held for exactly the dedicated architectural decision this document now provides, as Phase 3D-2b's own named blocker.

A dedicated, read-only architectural investigation was performed prior to this ADR to reconstruct the problem precisely, without assuming an answer. That investigation found:

- Scenario Analysis and Comparison are both fully specified, independently anatomized Reasoning-tier components in UX-013B (§9 and §8 respectively) and in UX-013E's own component taxonomy (line 481).
- Neither appears anywhere in ADR-002's own canonical thirteen-item table (lines 68–82), nor in the four-document Decision Workspace lineage (UX-009, UX-009A, UX-010, UX-011) that table was drawn from.
- ADR-003's own Alternative D contains a direct, load-bearing observation not previously surfaced anywhere else in the corpus: UX-013B's *separately-labeled* §14 "Decision Workspace sequence" — the specific numbered list that currently places Scenario Analysis at 9 and Comparison at 10 — **"was never examined by C-03 at all."** C-03 examined only UX-013B's *other*, separate top-level `# 1.`–`# 19.` component-heading numbering, and explicitly declined to treat *that* numbering as a competing full-sequence claim, "since UX-013B's own scope is intentionally Reasoning-components-only." The §14 list is a third, distinct thing, discovered later by the Source Correction Plan's own Phase 3 Scope Reassessment, and no adopted ADR has ever examined *its* claim to canonical authority.
- The Atlas UX Source Correction Plan (Section 5's C-03 row, Section 8, Section 69) nonetheless characterizes this same §14 list as stating "a materially different, competing normative order" — a characterization in real, unresolved tension with ADR-003's own Alternative D text. This is Contradiction K-1, below, and is the central, structural question this ADR must resolve before either component's placement can be meaningfully decided.
- ADR-003 R-06 already establishes, as adopted authority (quoting UX-013B's own §14 Dependency Chain as an accurate description): *"Scenario Analysis + Comparison → (synthesized into) → Recommendation [renamed Proposed Decision Candidate Content] → (formalized as) → Decision."* This derivational relationship is preserved unchanged by this ADR.
- UX-013B's own Comparison prose (§8, "Comparison Types") names five types, including "Scenario Comparison." UX-013B's own authoritative Component Inventory table and UX-013E's own "Comparison View → Composite Component" classification (line 906) both independently enumerate only **four** variants (Before/After, Alternative, Allocation, Historical), silently omitting Scenario Comparison. This is Contradiction K-3, below, and bears directly on Finding 8.3/M-6.
- UX-013B's own §14 contains an internal tension: §9's own component-level prose states Scenario Analysis's Upside/Downside cases "should inform the Opportunity Cost and the Challenges," while §14's own explicit "Dependencies" list states only "Opportunity Cost ← Conclusion + Candidate Content" and the Dependency Chain diagram places Opportunity Cost's own stage *before* "Scenario Analysis + Comparison." This is Contradiction K-2, below.
- Both components are labeled "(conditional)" in UX-013B's §14 list with no governing source anywhere defining what triggers that conditionality.

## Authority and Dependencies

- Depends on `ADR-002-Critical-UX-Architecture-Resolutions.md` C-03 (Decision Workspace Sequence) — this ADR does not reopen the canonical thirteen-item table; it clarifies whether Scenario Analysis and Comparison were ever intended to be members of it, exactly as ADR-003 did for Recommendation.
- Depends on `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` R-06, R-08, and Alternative D — this ADR does not reopen, revise, or reinterpret any part of ADR-003; it extends the same reasoning ADR-003 already applied to a structurally adjacent case, and relies on Alternative D's own factual finding about C-03's examination scope as direct evidence. **Clarification on the use of Alternative D:** ADR-003's Alternative D itself proposed, and ADR-003 itself rejected, treating Recommendation as a separate canonical Decision Workspace sequence stage — this ADR does not adopt that rejected proposal, does not extend it to Scenario Analysis or Comparison, and does not treat any rejected alternative as binding governance. What this ADR relies on is narrower: the factual observation, recorded within Alternative D's own rejection rationale, that UX-013B's §14 list was never examined by C-03 and was never established anywhere as a competing full-sequence claim. That observation is evidence about what C-03 did and did not consider — a historical fact independent of whether Alternative D's own proposed conclusion was accepted or rejected — and it is this fact alone, not Alternative D's rejected proposal, that this ADR treats as authoritative.
- Depends on `ADR-001-Missing-Source-Volume-Governance.md`'s three-tier classification for its treatment of UX-013E's own inventory claims (see R-05, below) and for its general non-fabrication/non-silent-deletion rules, which this ADR applies to the Scenario Comparison variant-count discrepancy. **Disclosure:** ADR-001's own document header still reads Status: Proposed, not Accepted; ADR-002 and ADR-003 nevertheless already rely on its governance rules as binding, and this ADR follows that same existing dependency chain rather than introducing a new one. Correcting ADR-001's own status header is outside this ADR's scope and is not attempted here; this ADR does not itself validate, formalize, or otherwise change ADR-001's adoption status.
- Supersedes no prior ADR. Extends no prior ADR's own adopted text. It resolves a question ADR-002 and ADR-003 both explicitly, deliberately left open.

## Exact Question

**Does UX-013B's §14 "Decision Workspace sequence" carry canonical Decision Workspace sequence authority — such that Scenario Analysis and Comparison must receive canonical numbered positions within, or an expansion of, ADR-002's thirteen-item table — or should that list instead be explicitly reclassified as a local Reasoning-component dependency/synthesis-order model with no claim to canonical-sequence authority? Independently of that structural question: does "Scenario Comparison" remain an active, semantically distinct variant of the Comparison component, or is scenario-based analytical structure exclusively owned by the standalone Scenario Analysis component?**

This is stated as two questions rather than expanded into a single, unreadable compound sentence. This ADR also resolves several necessary secondary dimensions — conditionality, the Opportunity Cost relationship, Scenario Workspace's status, and Phase 3D-2b's own authorization boundary — addressed separately, in Scope below and in R-07, R-08, R-10, and R-12, rather than folded into the question above.

## Scope

This ADR resolves: UX-013B's §14 list's own authority classification; Scenario Analysis's and Comparison's canonical Decision Workspace sequence membership (or lack thereof); the semantic boundary between Scenario Analysis and Comparison, specifically including the Scenario Comparison variant question; conditionality's meaning for both components; the minimum necessary statement of Scenario Analysis's/Comparison's relationship to Opportunity Cost sufficient to resolve Contradiction K-2 without reopening Opportunity Cost's own canonical position; and confirmation of Scenario Workspace's deferred status.

## Non-Scope

This ADR does not resolve, decide, or take a position on: Portfolio Recommendation's identity; Recommendation/Proposed Decision Candidate Content's identity (both remain exactly as ADR-003 settled them); Proposed Decision's or Decision Rationale's own identity or canonical position (both remain exactly as ADR-002 settled them); Final Decision Card's or Record Decision's own identity or canonical position; the exact full Decision Workspace implementation; exact UX copy, visual layout, charts, spacing, or animation; backend schema, persistence implementation, or provenance implementation for either component; Domain Object adoption for either component; scenario-generation algorithms, forecasting methodology, or financial methodology; model provider selection; scenario accuracy; maximum scenario count; Scenario Workspace's own design, navigation architecture, or ownership; product-tier rules; mobile layout; or detailed accessibility implementation. None of these is decided by implication anywhere below.

## Definitions

**UX-013B §14 "Decision Workspace sequence"** — the specific numbered list at UX-013B lines ~1739–1750 (post-Phase-3D-2a), distinct from UX-013B's own separate `# 1.`–`# 19.` top-level component-heading numbering. This is the list ADR-003 Alternative D confirms was never examined by ADR-002 C-03.

**Canonical Decision Workspace sequence** — ADR-002 C-03's own thirteen-item table (lines 68–82), the sole document-wide authority for Decision Workspace section order and membership.

**Scenario Analysis** — the standalone Reasoning component specified in UX-013B §9: structures a set of potential outcomes (Base/Upside/Downside/Alternative cases) under different conditions, each with qualitative probability, explicitly not a numerical sensitivity-analysis mechanism.

**Comparison** — the reusable Composite Component specified in UX-013B §8: presents two or more options, states, or scenarios side by side in a structured, parallel format, reused across Investment, Portfolio, Decision, and Historical contexts.

**Scenario Comparison** — the fifth type named in UX-013B §8's "Comparison Types" prose ("two or more potential outcome scenarios... each column is one scenario"), absent from UX-013B's own Component Inventory table and from UX-013E's own Composite-Component classification, both of which enumerate only four Comparison types.

**Local Reasoning-component ordering model** — a descriptive list of the sequence in which UX-013B's own specified Reasoning components are read, making no claim to represent, compete with, or require reconciliation against ADR-002's canonical Decision Workspace section order.

## Governing Facts (Preserved)

1. Scenario Analysis is a named Reasoning component (UX-013B §9). Unchanged by this ADR.
2. Scenario Analysis structures potential outcomes under different conditions. Unchanged.
3. Scenario Analysis is not numerical sensitivity analysis (UX-013B §9, "When Not Used"). Unchanged.
4. Comparison is a named Composite Component (UX-013E line 906: "It is not a pattern — it is a single Composite Component"). Unchanged.
5. Comparison is reusable across multiple workspace contexts (Investment, Portfolio, Decision, Historical — UX-013B §8 "When Used"; UX-013E line 992). Unchanged.
6. Comparison supports side-by-side presentation (UX-013B §8 Anatomy). Unchanged.
7. Comparison is not merely a pattern (UX-013E line 906, direct quotation). Unchanged.
8. Scenario Analysis and Comparison both feed Proposed Decision Candidate Content (ADR-003 R-06, UX-013B §14 Dependency Chain). Unchanged.
9. Proposed Decision Candidate Content is not a canonical Decision Workspace sequence member (ADR-003 R-08). Unchanged.
10. Proposed Decision is governed by ADR-002 at canonical position 3. Unchanged.
11. Decision Rationale is governed by ADR-002 at canonical position 4. Unchanged.
12. Opportunity Cost is governed by ADR-002 at canonical position 7. Unchanged, and **not reopened by this ADR**.
13. Portfolio Consequences is governed by ADR-002 at canonical position 8. Unchanged, and **not reopened by this ADR**.
14. Final Decision Card is governed by ADR-002 at canonical position 12. Unchanged.
15. Record Decision is governed by ADR-002 at canonical position 13. Unchanged.
16. Scenario Workspace is not currently designed or adopted (UX-012 §69, UX-013B "Remaining Reasoning Questions" Q4, UX-013E line 199 — all three mutually consistent). Unchanged.
17. Portfolio Recommendation remains outside this ADR, exactly as it has remained outside every phase of this program to date.
18. UX-013C and UX-013D do not currently exist in the repository (confirmed by direct directory listing; governed by ADR-001, ADR-002 C-05). Unchanged.
19. Data contracts, persistence, and provenance for both Scenario Analysis and Comparison remain outside this ADR — correctly withheld pending genuine UX-013C/UX-013D authorship, per ADR-001/ADR-002 C-05.

No fresh reading performed for this ADR contradicted any of the nineteen facts above; all are preserved as stated.

## Contradictions

### K-1 — Sequence Authority

**Source A** (Atlas UX Source Correction Plan, Section 5 C-03 row): UX-013B's §14 list "states a materially different, competing normative order... the one place in the corpus where the 'exactly one order' claim does not yet hold."

**Source B** (ADR-003, Alternative D, adopted): "UX-013B's *separately-labeled* §14 'Decision Workspace sequence' — the list that actually lists Recommendation as item 11 — was never examined by C-03 at all... Recommendation's item-11 placement was therefore never resolved, one way or the other, by ADR-002 C-03."

**Resolution.** Source B is authoritative — it is adopted ADR text (Class A), while Source A is planning-document characterization (Class D) that was never itself independently reviewed against ADR-002/ADR-003's own text for this specific claim. The two are not, on inspection, actually incompatible once precisely stated: the Plan is correct that UX-013B's §14 list *differs* from the canonical order (it does — it contains entries the canonical table does not, and omits entries the canonical table has); ADR-003 is correct that this list was never *examined and rejected as a rival claim* by C-03 (it wasn't — C-03's own evidence base is the four-document lineage, and the Resolution Design explicitly declined to treat *any* UX-013B list as competing). The Plan's language ("competing normative order") overstates what was actually established: difference is not the same as competition for the same authority. **This ADR resolves K-1**: UX-013B's §14 list is not, and has never been, a canonical Decision Workspace sequence, complete or partial. It differs from ADR-002's table because it was never built to track it — it is UX-013B's own local Reasoning-component reading order, describing a real dependency/synthesis relationship among the components UX-013B itself specifies, not a rival claim to the same authority ADR-002 C-03 settled.

### K-2 — Opportunity Cost Relationship

**Source A** (UX-013B §9, "Relationship to Conclusions"): "The Upside and Downside cases bound the space of outcomes the user is considering — they should inform the Opportunity Cost and the Challenges."

**Source B** (UX-013B §14, explicit "Dependencies" list and Dependency Chain diagram): "Opportunity Cost ← Conclusion + Candidate Content" (only); diagram places Opportunity Cost's own stage before "Scenario Analysis + Comparison."

**Resolution.** Both are Class E (descriptive component text), neither adopted governance — this is an internal UX-013B inconsistency, not a conflict between governing authorities, and does not, by itself, require reopening anything ADR-002 settled. **This ADR resolves K-2 as follows**: Scenario Analysis may semantically inform Opportunity Cost's content (Source A is not rejected — a user's Downside Case reasoning is legitimate input to what they judge is foregone). Opportunity Cost remains an independent canonical Decision Workspace section at position 7, unconditionally, regardless of whether Scenario Analysis exists, is populated, or precedes or follows it in any given reading flow. The two do not have a strict, required one-way dependency — Source B's own linear diagram overstates strict sequential ordering where the actual relationship is informational, not compositional (Opportunity Cost does not require Scenario Analysis's content to be complete or even present). §14's own diagram and Dependencies list are identified as needing a future, narrow correction to state this relationship accurately (see Required Downstream Corrections) — this ADR does not perform that correction itself, and does not require it to be resolved before Phase 3D-2b may proceed with the corrections this ADR does authorize.

### K-3 — Comparison Variant Count

**Source A** (UX-013B §8, "Comparison Types" prose): five types, including "Scenario Comparison."

**Source B** (UX-013B's own Component Inventory table; UX-013E line 906): four variants (Before/After, Alternative, Allocation, Historical), Scenario Comparison absent from both.

**Resolution.** Per Architectural Principle 10 (silent omission from an inventory is not an adopted retirement decision) and Principle 11 (silent inclusion in prose is not an adopted variant if authoritative enumeration differs), **neither Source A nor Source B alone settles this by default** — the discrepancy is exactly the kind of undisclosed drift ADR-001 exists to prevent, and this ADR is the first document with the authority to resolve it rather than merely note it. **This ADR resolves K-3**: Scenario Comparison is retired as a named Comparison type, formally, by this decision (not merely confirmed as already-silently-retired) — see R-05, below. The Component Inventory table and UX-013E's own classification, which already reflect four variants, are correct and require no further correction on this specific point; UX-013B §8's own prose, which still names five, is the text requiring a future, disclosed correction (see Required Downstream Corrections). This resolves Finding 8.3/M-6 for its canonical-inventory dimension; see also R-04/R-05 for the underlying semantic-boundary reasoning.

### K-4 — Canonical Membership

**Source A** (ADR-002 C-03's canonical table): neither Scenario Analysis nor Comparison appears anywhere in it.

**Source B** (UX-013B §14): both numbered as items 9 and 10.

**Resolution.** Directly settled by K-1's own resolution above: this is not a real architectural conflict requiring ADR-002 to be reopened or expanded — it is a scope-labeling problem. UX-013B's §14 list was never a canonical sequence to begin with (K-1), so its numbering Scenario Analysis and Comparison as 9/10 was never a claim requiring reconciliation against ADR-002's own table; it is local-list numbering, not canonical-position numbering, and it may continue, be reframed, or be removed, per Phase 3D-2b's own future implementation, without amending ADR-002 in any respect.

## Candidate Architectures

### Candidate A — Canonical Decision Workspace Members

**Definition.** UX-013B §14 is treated as a partial canonical sequence; Scenario Analysis and Comparison are granted canonical Decision Workspace membership; their exact positions are adopted; ADR-002 is amended or extended.

**Supporting evidence.** UX-013B's own current list places them at 9/10; both are fully-specified, mature components.

**Contradicting evidence.** K-1's resolution (this list carries no canonical authority to begin with); ADR-003 Alternative D's own precedent — Recommendation was denied canonical membership on structurally identical grounds (absence from the four-document lineage, absence from ADR-002's own table); neither component appears in UX-009/UX-009A/UX-010/UX-011.

**Required assumptions.** That UX-013B's §14 list, despite K-1's finding, should nonetheless be elevated to canonical status now, retroactively, for these two components specifically — an assumption this ADR finds unsupported.

**Semantic model / component identities.** Unchanged from current spec, but reframed as canonical sections rather than local-list entries.

**Workspace ownership.** Decision Workspace, exclusively, by definition of this candidate.

**Canonical-sequence consequences.** Requires expanding ADR-002's thirteen-item table to fifteen (or renumbering existing entries), directly reopening C-03.

**Conditionality consequences.** Would require canonical-level conditionality rules (like C-04's completion matrix), a new governance burden not currently justified by any evidence.

**Comparison-variant consequences.** Does not by itself resolve K-3.

**Opportunity Cost consequences.** Risks re-litigating K-2 at canonical-authority level rather than descriptive level, raising the stakes of an already-identified internal inconsistency.

**Candidate Content consequences.** Unchanged — ADR-003 R-06 is preserved regardless.

**ADR-002 consequences.** Requires amendment. **ADR-003 consequences.** None directly, but sits in tension with its own Alternative D precedent.

**Source Correction Plan consequences.** Would require a new phase authorizing table expansion — heavier than anything Phase 3D-2b currently anticipates.

**UX-013B / UX-013E consequences.** Would require renumbering §14 and updating UX-013E's own category tables to reflect new canonical status.

**Phase 3D-2b consequences.** Would exceed Phase 3D-2b's own current scope (a source correction, not an ADR-002 amendment).

**Implementation blast radius.** High — touches Decision Workspace's own core information architecture, the single highest-risk surface in the whole corpus per ADR-002's own Context section.

**Domain-model / persistence implications.** None directly, but a heavier canonical-sequence footprint invites future pressure to persist Scenario Analysis/Comparison content as recorded, canonical fields, which is explicitly out of scope.

**Strengths.** Would give UX-013B's list full internal coherence as a genuinely canonical, complete document.

**Weaknesses.** Requires justifying an ADR-002 expansion this ADR finds no evidentiary basis for; directly contradicts the precedent ADR-003 itself set for a structurally identical case (Recommendation) and offers no principled reason Scenario Analysis/Comparison deserve different treatment.

**Contradictions introduced.** Reopens K-1 in the opposite direction from this ADR's own resolution; invites a K-4-style conflict at the canonical level rather than resolving it.

**Contradictions resolved.** None beyond what any candidate resolves trivially.

**Verdict: rejected by contradiction** (contradicts K-1's resolution and Architectural Principle 12: existing ADR-002 positions must not be reopened without necessity — no necessity is shown here).

### Candidate B — Local Reasoning Order, No Canonical Membership

**Definition.** UX-013B §14 is explicitly reclassified as a local Reasoning-component dependency/synthesis-order model, not a canonical Decision Workspace sequence; Scenario Analysis and Comparison remain valid components; neither receives canonical numbered membership; ADR-002 remains unchanged.

**Supporting evidence.** Directly matches ADR-003 Alternative D's own finding that this list "was never examined by C-03... not itself a competing full-sequence claim." Matches Architectural Principles 3 (a numbered list is not automatically canonical merely because it is numbered) and 4 (component existence does not imply canonical sequence membership).

**Contradicting evidence.** None found in this investigation or in any fresh re-read performed for this ADR.

**Required assumptions.** That the Plan's own "competing normative order" characterization (Source A of K-1) was an overstatement rather than an independently-derived, separately-authoritative finding — this ADR finds this assumption justified, since the Plan's characterization cites no evidence of its own beyond the observation that the lists differ, which K-1's resolution already accounts for without requiring competition.

**Semantic model.** UX-013B §14 becomes descriptive: it documents the order in which UX-013B's own specified components are read and how they depend on one another, exactly as its own "Dependency Chain" sub-heading already states, without asserting Workspace-section-order authority.

**Component identities.** Unchanged — Scenario Analysis and Comparison remain exactly as specified in §9 and §8.

**Workspace ownership.** Both remain usable within the Decision Workspace (as they are today), with Comparison's existing cross-workspace reuse (Investment, Portfolio, Historical) fully preserved, since this candidate makes no exclusivity claim.

**Canonical-sequence consequences.** None — ADR-002's thirteen-item table is untouched, unexpanded, unreopened.

**Conditionality consequences.** Still requires definition (this ADR provides it — see R-07), independent of this candidate's own selection.

**Comparison-variant consequences.** Compatible with, and does not itself resolve, K-3 — resolved separately by R-04/R-05.

**Opportunity Cost consequences.** Consistent with K-2's resolution above — Opportunity Cost remains canonical and independent regardless of §14's own reclassified status.

**Candidate Content consequences.** Fully preserves ADR-003 R-06 unchanged.

**ADR-002 consequences.** None — no amendment required.

**ADR-003 consequences.** None — no amendment required; this candidate is the direct extension of ADR-003's own reasoning to a parallel case.

**Source Correction Plan consequences.** The Plan's own C-03 row (Section 5) and Section 8/69 characterization of UX-013B's §14 list as "competing" will need a future, narrow correction to align with this ADR's K-1 resolution — flagged under Required Downstream Corrections, not performed here.

**UX-013B consequences.** §14's own heading and framing will need a future correction disclosing this reclassification — not performed here.

**UX-013E consequences.** None required beyond what K-3/R-05 already separately requires.

**Phase 3D-2b consequences.** This is exactly the kind of bounded, mechanical correction Phase 3D-2b already anticipates performing once its own blocking architectural decision (this ADR) is adopted.

**Implementation blast radius.** Low — a framing/disclosure correction to one document section, not a change to any canonical architecture.

**Domain-model / persistence implications.** None.

**Strengths.** Resolves K-1 and K-4 directly and simultaneously; requires no ADR-002 amendment; matches the single strongest piece of directly on-point governing-authority evidence in the entire corpus (ADR-003 Alternative D); minimizes new assumptions (Architectural Principle per Decision Standard item 3).

**Weaknesses.** Represents a real, if narrow, shift in how Phase 3D-1 and Phase 3D-2a's own corrections are best understood — though neither phase's own individual correctness depended on §14 being canonical (What Changed's removal and the Opportunity Cost/Portfolio Consequences reorder are independently justified by ADR-002 C-03's own canonical content regardless of what authority §14 itself carries), so this candidate does not retroactively invalidate either prior phase.

**Contradictions introduced.** None identified.

**Contradictions resolved.** K-1, K-4, and (in combination with R-08) removes the pressure that was driving K-2 toward a canonical-level dispute.

**Verdict: selected.**

### Candidate C — Scenario Analysis Semantic Owner, Comparison as Generic Renderer

**Definition.** Scenario Analysis owns scenario-specific semantic structure (Base/Upside/Downside/Alternatives, conditions, implications, qualitative likelihood); Comparison remains generic and reusable; Scenario Comparison is not a separate semantic Comparison variant; Comparison may render or display multiple Scenario Analysis outputs side by side without owning their meaning; neither gains canonical sequence membership merely through this relationship.

**Supporting evidence.** Scenario Analysis's own anatomy (§9) is already fully self-contained and does not reference Comparison's own anatomy; Comparison's own anatomy (§8) is generic (ColumnHeader/RowLabel/Value, not scenario-specific fields); this directly and cleanly resolves Finding 8.3/M-6 and K-3 by giving each component an exclusive, non-overlapping semantic role while preserving Comparison's own presentation capability.

**Contradicting evidence.** None found — this candidate is fully consistent with every governing fact preserved above.

**Required assumptions.** That "rendering scenario content" (a presentation act) can be cleanly separated from "owning scenario semantics" (an analytical-structure act) — supported directly by the existing anatomy evidence (Comparison's own anatomy has no Base/Upside/Downside/probability fields; those live exclusively in Scenario Analysis's own ScenarioItem).

**Semantic model.** Scenario Analysis produces structured scenario content (with its own full anatomy); if that content is ever displayed two-or-more-at-a-time in a side-by-side format, Comparison is the presentation vehicle used to do so, via its existing generic variant model (its Before/After and Alternative Comparison types are illustrative examples of configurations that could support this, not a mandated mapping) — analogous to how UX-013E's own "Suggestion Comparison" pattern already configures the generic Comparison component for a specific comparison use case (line 908-910) without Comparison itself needing to define a "Suggestion Comparison" variant. The exact configuration is an implementation-level choice, not decided by this ADR (see R-04).

**Component identities.** Both remain fully distinct, named components; Comparison's identity is strengthened (a single, coherent, generic presentation capability) rather than fragmented across a growing list of domain-specific named types.

**Workspace ownership.** Unchanged from current descriptive text for both.

**Canonical-sequence consequences.** None — consistent with Candidate B's own resolution of K-1/K-4; this candidate operates entirely within Candidate B's own framing.

**Conditionality consequences.** Directly supports a clean definition (R-07): Scenario Analysis's own conditionality concerns whether multiple plausible future conditions materially exist for the current decision; Comparison's own conditionality concerns whether two or more comparable entities exist and side-by-side evaluation is useful — these are two independent, component-specific preconditions, not one shared one.

**Comparison-variant consequences.** Directly resolves K-3: Scenario Comparison is retired as a named type; scenario content, when compared side by side, may be rendered through Comparison's existing generic variant model — its "Alternative Comparison" type (already defined for "two or more mutually exclusive options... rows are shared evaluation criteria") is one variant whose existing description already covers comparing scenario outputs without requiring its own named sub-variant, but this ADR does not mandate that specific type as the exclusive mechanism (see R-04).

**Opportunity Cost consequences.** Fully consistent with K-2's resolution — no change required.

**Candidate Content consequences.** Fully preserves ADR-003 R-06 — both components remain upstream, non-canonical contributors to Candidate Content's own synthesis.

**ADR-002 / ADR-003 consequences.** None — no amendment to either.

**Source Correction Plan consequences.** Adds one further downstream correction target (§8's "Comparison Types" prose) beyond what Candidate B alone would require.

**UX-013B consequences.** §8's "Comparison Types" prose requires a future, disclosed correction removing "Scenario Comparison" as a named type (with a note that scenario comparison may be achieved through Comparison's existing generic variant model, without this ADR specifying which existing type performs it) — not performed here.

**UX-013E consequences.** None required — its own four-variant classification is already correct under this candidate and requires no further change.

**Phase 3D-2b consequences.** This is the specific semantic-boundary content Phase 3D-2b's own future correction should implement, alongside Candidate B's own §14-reframing correction.

**Implementation blast radius.** Low — confined to one prose section's own type list and its accompanying disclosure.

**Domain-model / persistence implications.** None.

**Strengths.** Resolves Finding 8.3/M-6 completely and precisely; gives both components a clean, stable, non-overlapping semantic boundary; requires the fewest new assumptions of any candidate that actually resolves K-3 (as opposed to Candidate B alone, which is silent on K-3); consistent with every architectural principle in this decision, including Principle 7 (a generic rendering capability must not absorb domain-specific semantic responsibility merely because it can display that content) and Principle 8 (a domain-specific semantic component must not duplicate a generic presentation component unnecessarily) — this candidate is precisely the resolution those two principles were framed to test for.

**Weaknesses.** Requires one additional future source correction (§8's prose) beyond Candidate B alone.

**Contradictions introduced.** None identified.

**Contradictions resolved.** K-3 (directly); reinforces K-1/K-4's resolution (indirectly, by removing any residual argument that Scenario Analysis and Comparison "must" both be independently canonical because they're semantically distinct — they remain semantically distinct without needing canonical status).

**Verdict: selected**, in combination with Candidate B.

### Candidate D — Scenario Comparison Remains an Active Comparison Variant

**Definition.** Scenario Analysis structures/generates scenario content, exactly as under every other candidate; Scenario Comparison remains a named, distinct Comparison variant whose own job is comparing two or more already-produced scenario outputs; Scenario Comparison is formally restored to UX-013B's Component Inventory and to UX-013E's own classification (both of which currently enumerate only four Comparison variants); the ADR would define the boundary between Scenario Analysis (produces scenario content) and Scenario Comparison (compares scenario content) precisely enough to prevent the overlap Finding 8.3/M-6 describes.

**Supporting evidence.** UX-013B §8's own "Comparison Types" prose still names it, unedited, alongside the other four types, in the same list, with the same descriptive format ("Two or more potential outcome scenarios. Each column is one scenario. Rows are outcome dimensions."); restoring it would require the least textual change to §8 itself (no deletion needed, only a possible clarifying note); it preserves, without correction, one more piece of UX-013B's own committed text than Candidate C does.

**Contradicting evidence.** Requires reinstating a type that UX-013B's own authoritative Component Inventory and UX-013E's own classification have *already*, independently, and consistently dropped (Contradiction K-3) — going against, not resolving, the convergent silent evidence of two independent sources; would leave Finding 8.3/M-6 exactly as unreconciled as it is today, since a restored, distinctly-named "Scenario Comparison" variant sitting alongside a fully independent Scenario Analysis component, both structuring "potential outcomes under different conditions," is the precise overlap Finding 8.3 describes, not a resolution of it — merely re-affirming the status quo ante does not, by itself, supply the "single naming/classification decision" Finding 8.6 says this family of findings requires.

**Required assumptions.** That the four-variant inventory and UX-013E's classification are themselves the error, rather than §8's prose — an assumption this ADR finds less supported than the reverse (Principle 10/11 cuts against treating either silent state as automatically authoritative, but between the two, the *convergence* of two independently-authored sources on the same four-variant count is stronger evidence than one prose passage that was never updated). This candidate also requires assuming that a stable, non-overlapping boundary between "Scenario Analysis produces scenario content" and "Scenario Comparison compares scenario content" can be maintained in practice — an assumption not tested anywhere in the corpus, since no committed source anywhere describes Scenario Comparison's own anatomy, properties, or behavior independently of the general Comparison anatomy (§8's own Anatomy section is generic across all five originally-listed types; no scenario-specific fields are specified for the Scenario Comparison type specifically, unlike Allocation Comparison, which at least references "Allocation Comparison layout").

**Semantic model.** Under this candidate, two adjacent but formally separate components would exist: Scenario Analysis (generates/structures Base/Upside/Downside/Alternative content) and Scenario Comparison (a Comparison variant that arranges two or more already-generated scenario outputs into columns). The two would need to interoperate — Scenario Comparison would need to consume Scenario Analysis's own output as its input — without either owning the other, similar in shape to Candidate C's own rendering relationship, but with the receiving component given its own distinct name and semantic status rather than being absorbed into Comparison's already-generic variant set.

**Scenario Analysis identity.** Unchanged from R-02 under every candidate — Scenario Analysis remains the exclusive owner of scenario generation and structuring even here; this candidate does not touch that identity.

**Comparison identity.** Comparison's own identity would be complicated, not simplified, by this candidate: it would carry four purely generic, structural variants (Before/After, Alternative, Allocation, Historical) plus one, Scenario Comparison, whose entire reason for existing is to consume another specific component's (Scenario Analysis's) domain-specific output — an asymmetry among Comparison's own five variants that does not exist under Candidate C, where all of Comparison's variants remain uniformly generic.

**Scenario Comparison identity.** Would need to be defined, for the first time with any rigor, as a component distinct from both Scenario Analysis and from Comparison's other four variants — no committed source currently gives it this level of definition; it exists today only as a one-sentence description under §8's "Comparison Types" prose, with no anatomy, properties, states, or interaction model of its own beyond what it inherits generically from Comparison.

**Workspace ownership.** Unchanged from Candidate C — both remain usable within, and are not exclusively owned by, the Decision Workspace.

**Canonical-sequence consequences.** None beyond what Candidate B already establishes — this candidate, like Candidate C, operates entirely within Candidate B's own K-1/K-4 resolution and does not itself reopen canonical membership.

**Conditionality consequences.** Would require *three* conditionality definitions instead of two — one for Scenario Analysis (per R-07, unchanged), one for Comparison generally (per R-07, unchanged), and a *third*, narrower one for Scenario Comparison specifically (available when two or more Scenario Analysis outputs exist and are to be compared) — an additional definitional burden Candidate C does not require, since under Candidate C this third case is simply an instance of Comparison's own existing, general conditionality.

**Comparison-variant consequences.** Directly the inverse of R-05: rather than retiring Scenario Comparison, this candidate restores and formally strengthens it, requiring UX-013B's Component Inventory and UX-013E's own classification both to be corrected in the opposite direction (adding a fifth row/variant back) from what R-05 requires (confirming the existing four-row count).

**Opportunity Cost consequences.** No material difference from Candidate C/R-08 — Scenario Analysis's own informational relationship to Opportunity Cost is unaffected by whether Scenario Comparison exists as a separate named variant.

**Candidate Content consequences.** No material difference — ADR-003 R-06's own chain ("Scenario Analysis + Comparison → synthesized into → Candidate Content") is preserved identically regardless of whether Comparison's own internal variant set includes a named Scenario Comparison entry.

**ADR-002 consequences.** None — like every candidate except A, this does not touch ADR-002's own table.

**ADR-003 consequences.** None — Candidate Content's own identity (ADR-003 R-04, R-06, R-07) is unaffected either way.

**Source Correction Plan consequences.** Would require the Plan's own future downstream-correction list to add a restoration task (adding Scenario Comparison back to the Component Inventory and to UX-013E) rather than Candidate C's retirement/removal task — a symmetrically-sized, but directionally opposite, correction burden.

**UX-013B consequences.** §8's own prose would require no deletion (a strength), but the Component Inventory table would require a new row, and a new definitional passage would likely be needed to give Scenario Comparison its own anatomy distinct from Comparison's other four variants, since none currently exists.

**UX-013E consequences.** Line 906's own "4 variants" classification would require correction to "5 variants," reversing rather than confirming UX-013E's own current, already-converged position — a correction this candidate requires that no other candidate does.

**Phase 3D-2b consequences.** Would still leave Phase 3D-2b with a bounded, describable correction task, but a larger and more novel one than Candidate C's (new anatomy authorship for Scenario Comparison, rather than a disclosed removal of an already-underspecified type).

**Implementation blast radius.** Low-to-moderate — confined to Comparison's own variant list and its accompanying UX-013E classification, but larger than Candidate C's, since it requires *authoring new component definition*, not merely disclosing a removal.

**Domain Object implications.** None directly required by this candidate itself, consistent with every other candidate — no committed source anywhere suggests Scenario Comparison would need independent persistence merely by existing as a named variant.

**Persistence implications.** None directly required, though maintaining two separate scenario-related concepts (Scenario Analysis's own content, and Scenario Comparison's own comparison configuration) creates a mild future risk of persistence-model duplication if either concept is later given real storage — a risk Candidate C's single-owner model does not carry.

**Provenance implications.** None directly required; unaffected by whichever candidate is chosen, since neither this ADR nor any prior one defines provenance for either component's content.

**Strengths.** Requires the least textual deletion from UX-013B's own current committed prose; preserves a name ("Scenario Comparison") that already exists in the corpus rather than retiring it; could be argued to give scenario-to-scenario comparison its own explicit, discoverable identity in a component inventory, rather than requiring an implementer to infer that Comparison's generic "Alternative Comparison" type is the intended vehicle.

**Weaknesses.** Leaves Finding 8.3/M-6 exactly as unreconciled as it is today, since the overlap the finding describes — two components ("Scenario Analysis" and "Scenario Comparison") both structuring potential-outcome content — is precisely what this candidate preserves rather than resolves; runs directly against the convergent, independently-authored evidence of both UX-013B's own Component Inventory and UX-013E's own classification, both of which already, consistently, without coordination, omit it; requires new component-definition authorship (anatomy, properties, states) for Scenario Comparison that exists nowhere in the corpus today, which is a heavier documentary burden than Candidate C's disclosed-removal approach; introduces an asymmetry into Comparison's own variant set (four generic variants plus one variant whose entire purpose is consuming another specific component's domain output) that Candidate C avoids entirely by keeping all of Comparison's variants uniformly generic; requires three conditionality definitions instead of two.

**Contradictions introduced.** Directly reintroduces Contradiction K-3 in its original, unresolved form — restoring Scenario Comparison without addressing why two independent sources already, convergently, dropped it would leave exactly the same undisclosed-drift risk ADR-001's own governing principles exist to prevent, unless this candidate is paired with its own fresh, disclosed justification for why the four-variant convergence should itself be treated as the error — which no evidence gathered anywhere in this investigation supports.

**Contradictions resolved.** None beyond what Candidate B already resolves (K-1/K-4, by the same reasoning as every candidate operating within Candidate B's framing).

**Finding 8.3 resolution assessment.** Not resolved — this candidate preserves, rather than closes, the exact overlap Finding 8.3 identifies. A future implementer would still lack the "single naming/classification decision" the finding's own companion diagnosis (Finding 8.6) says is required.

**M-6 resolution assessment.** Same as Finding 8.3 — unresolved under this candidate, since M-6 is the findings-summary listing of the identical Finding 8.3.

**Whether it preserves the generic Comparison boundary.** No — it introduces exactly the asymmetry (one variant that is not generic, unlike the other four) that Architectural Principle 8 (a domain-specific semantic component must not duplicate a generic presentation component unnecessarily) is framed to guard against.

**Whether it duplicates Scenario Analysis semantics.** Partially — Scenario Comparison's own one-sentence description ("Two or more potential outcome scenarios... rows are outcome dimensions") already substantially overlaps with Scenario Analysis's own stated purpose ("structures a set of potential outcomes... under different conditions"), which is the original substance of Finding 8.3's own diagnosis, unresolved by this candidate.

**Whether restoration can be kept purely presentational.** Not on the evidence available — no committed source distinguishes a "purely presentational" Scenario Comparison from a semantically-substantive one; §8's own one-sentence description does not draw that line, and drawing it now would require new architecture this candidate's own definition does not supply.

**Whether a named variant is necessary for rendering.** No — Candidate C's own edge-case analysis (elsewhere in this ADR) demonstrates that Comparison's existing generic variant model is sufficient to render Scenario Analysis's output without requiring a dedicated named variant; necessity is not established anywhere in the corpus for a separate Scenario Comparison identity beyond the fact that it was once named.

**Verdict: viable but rejected** — internally coherent as a candidate, fairly evaluated across all of the above dimensions, but it fails to resolve the very finding (8.3/M-6) this ADR exists to close, runs against convergent evidence from two independent sources, introduces a structural asymmetry into Comparison's own variant set that the selected architecture avoids, and requires new component-definition authorship unsupported by any existing anatomy. This verdict is unchanged from this ADR's original analysis; the expanded treatment above confirms, rather than merely asserts, the original conclusion.

### Candidate E — Scenario Analysis as a Comparison Variant

**Definition.** The standalone Scenario Analysis component is retired or reduced; Scenario Analysis becomes one Comparison mode or variant.

**Contradicting evidence.** Directly contradicted by Scenario Analysis's own complete, independent component specification (full anatomy, states, token mapping, historical behavior distinct from Comparison's own) — retiring it would discard real, specified, mature behavior with no textual basis; directly contradicted by Finding 8.6's own explicit caution against reflexive merging in this exact family of findings; UX-013E's own category treatment (line 481) lists ScenarioAnalysis as its own named item within the Reasoning category, not as a Comparison sub-type.

**Verdict: rejected by contradiction.**

### Candidate F — Comparison as Subcomponent of Scenario Analysis

**Definition.** Scenario Analysis remains the semantic component; Comparison becomes an internal subcomponent or mode used only when multiple scenarios are viewed side by side.

**Contradicting evidence.** Directly contradicted by Comparison's own extensive, specified cross-workspace reuse (Investment, Portfolio, Decision, Historical, and the Suggestion-Comparison composed pattern) — subordinating it to Scenario Analysis would either fork Comparison into two implementations (one generic, one Scenario-Analysis-owned) or improperly narrow its already-established, broader role; violates Architectural Principle 6 (cross-workspace reuse does not imply workspace ownership) in the opposite direction it's meant to guard against — here it would impose a *component-ownership* subordination based on one use case among many.

**Verdict: rejected by contradiction.**

### Candidate G — Separate Scenario Workspace

**Definition.** Scenario Analysis and possibly Comparison move into a future Scenario Workspace; Decision Workspace contains only an entry point or summary.

**Contradicting evidence.** UX-012 §69 explicitly lists Scenario Workspace as "not designed here; identified for future governance" — designing or adopting it now would violate Architectural Principle 15 (no Scenario Workspace may be created merely to simplify the current component-boundary question) and would exceed this ADR's own authority, which is scoped to Scenario Analysis and Comparison's *existing* status, not to authorizing a new Workspace; depends on a product-roadmap decision (UX-013B's own Remaining Reasoning Question 4) this ADR is not positioned to make.

**Verdict: rejected** — not by internal contradiction, but by scope: adopting it would exceed this ADR's own authority and prematurely resolve a distinct, deferred, lower-priority question. Explicitly deferred, per R-10, below.

### Candidate H

No additional candidate was found necessary. The fresh evidence gathered for this ADR (Contradictions K-1 through K-4, the Component Inventory/UX-013E convergence) is fully accounted for by Candidates B and C in combination; no repository evidence was found requiring a ninth model.

## Selected Architecture

**Candidate B (Local Reasoning Order, No Canonical Membership) combined with Candidate C (Scenario Analysis Semantic Owner, Comparison as Generic Renderer).** Together, these: (1) resolve K-1 and K-4 by correctly classifying UX-013B's §14 list as carrying no canonical authority, requiring no ADR-002 amendment; (2) resolve K-3 (and thereby Finding 8.3/M-6) by retiring Scenario Comparison as a named Comparison type and giving each component an exclusive, non-overlapping semantic role; (3) resolve K-2 by stating the minimum necessary, non-canonical-reopening relationship between Scenario Analysis and Opportunity Cost; (4) introduce zero new assumptions beyond what the existing anatomy of both components already directly supports; (5) require no ADR-002 or ADR-003 amendment; (6) leave a fully bounded, mechanical Phase 3D-2b source correction path open.

## Rejected Alternatives

Candidate A (rejected by contradiction — reopens K-1, contradicts ADR-003's own Recommendation precedent, no necessity shown for an ADR-002 expansion). Candidate D (viable but rejected — fails to actually resolve Finding 8.3/M-6, runs against convergent two-source evidence, introduces a variant-set asymmetry into Comparison and requires new, currently-unsupported component-definition authorship for Scenario Comparison). Candidate E (rejected by contradiction — discards specified Scenario Analysis behavior, contradicts Finding 8.6). Candidate F (rejected by contradiction — improperly subordinates Comparison's own established cross-workspace role). Candidate G (rejected on scope grounds — exceeds this ADR's authority, prematurely resolves a distinct, deferred product-roadmap question).

## Decision

The following twelve resolutions are adopted together, as one coordinated decision.

### R-01 — UX-013B §14 Authority Classification

UX-013B's §14 "Decision Workspace sequence" is **not**, and has never been, a canonical Decision Workspace sequence, complete or partial. It is a **local Reasoning-component dependency/synthesis-order model**: a description of the order and derivation relationships among the Reasoning components UX-013B itself specifies. It was never examined by ADR-002 C-03 (ADR-003 Alternative D, confirmed) and carries no claim to represent, compete with, or require reconciliation against ADR-002's own thirteen-item table. The Atlas UX Source Correction Plan's own characterization of this list as "a materially different, competing normative order" (Section 5) is corrected by this ADR to: a differently-scoped, non-competing, local ordering model that happens to also contain content (What Changed; the pre-Phase-3D-2a Opportunity-Cost/Portfolio-Consequences order) that has already been separately, correctly brought into consistency with canonical naming and ordering where ADR-002's own content overlaps with this list's content — a narrower, more precise claim than "competing."

### R-02 — Scenario Analysis Identity

Scenario Analysis remains a fully valid, independently specified Reasoning component (UX-013B §9), unchanged in purpose, anatomy, properties, states, interaction, or accessibility by this ADR. It is the exclusive semantic owner of scenario-specific analytical structure: Base/Upside/Downside/Alternative case framing, scenario conditions, scenario implications, and qualitative probability estimation.

### R-03 — Comparison Identity

Comparison remains a fully valid, independently specified, reusable Composite Component (UX-013B §8), unchanged in purpose, anatomy, properties, states, interaction, or accessibility by this ADR, except as R-04/R-05 narrow its variant list. It remains a generic, cross-workspace side-by-side presentation capability, not scoped exclusively to any one domain's semantics.

### R-04 — Scenario Analysis / Comparison Boundary

The semantic boundary between the two is: **Scenario Analysis owns the generation and structuring of scenario content; Comparison owns the generic, side-by-side presentation of any comparable content, including scenario content when two or more scenarios are displayed together.** Comparison may render Scenario Analysis's output without owning, duplicating, or redefining its scenario-specific semantics — this is a rendering/presentation relationship, not a composition-of-ownership or subcomponent relationship, and neither component contains the other in any structural sense. When scenario content is compared side by side, Comparison's existing, generic variant model may support that rendering without any new, named "Scenario Comparison" variant being required — analogous to UX-013E's own already-established "Suggestion Comparison" pattern, which configures the generic Comparison component for a specific use case without Comparison itself requiring a dedicated named variant for it. **Comparison's "Alternative Comparison" type (already defined for "two or more mutually exclusive options... rows are shared evaluation criteria") is one illustrative example of how this could be configured — it is cited here to show the boundary is implementable with Comparison's existing anatomy, not as a mandate.** This ADR does not mandate Alternative Comparison, any other specific existing type, a new Scenario Comparison variant, a specific prop value, or a specific layout as the required mechanism; it establishes only that Comparison's generic capability is sufficient to render Scenario Analysis's output without Comparison acquiring scenario-specific semantic ownership. The exact variant mapping — which existing type, if any, is actually used, and how it is configured — is an implementation-level decision left to later source correction or implementation design, provided that decision preserves R-02 through R-05 (Scenario Analysis's exclusive semantic ownership; Comparison's generic, non-owning role; and Scenario Comparison's retirement as a distinct named variant).

### R-05 — Scenario Comparison Variant Status

"Scenario Comparison" is **retired, formally, by this decision**, as a named Comparison type. UX-013B's own Component Inventory table and UX-013E's own "Comparison View → Composite Component" classification — both of which already, independently, enumerate only four Comparison variants (Before/After, Alternative, Allocation, Historical) — are **confirmed correct** and require no further correction on this point. UX-013B §8's own "Comparison Types" prose, which still names a fifth type ("Scenario Comparison"), is identified as containing superseded text requiring a future, disclosed correction (see Required Downstream Corrections) — this ADR does not perform that correction itself, consistent with every prior ADR in this program (ADR-002, ADR-003) never performing its own downstream source correction. This resolves Finding 8.3/M-6 (`UX-Architecture-Review-001.md`) and Contradiction K-3.

### R-06 — Canonical Sequence Membership

Neither Scenario Analysis nor Comparison is, or has ever validly been, a canonical Decision Workspace sequence member. ADR-002's thirteen-item table (C-03) remains unchanged, unexpanded, and is **not reopened** by this ADR. UX-013B §14's current numbering of Scenario Analysis as "9" and Comparison as "10" is **local-list documentary numbering**, not canonical positional authority (per R-01) — it may be retained, renumbered, converted to an unnumbered dependency-chain-style presentation, or otherwise reframed by a future Phase 3D-2b correction, without that correction constituting, requiring, or implying any ADR-002 amendment.

**Explicit disambiguation of the numeral coincidence.** ADR-002's own canonical positions 9 and 10 (C-03 table, lines 78–79) are, respectively: **9 — Assumptions, Monitoring and Invalidation** ("the conditions this reasoning depends on, what Atlas will watch, what would invalidate the decision") and **10 — Implementation Plan** ("how the decision would be executed"). These are entirely different content from UX-013B's local-list items numbered 9 and 10 (Scenario Analysis and Comparison, respectively). The shared numerals are a coincidence of two independent numbering systems, not evidence of shared identity, replacement, or canonical correspondence — UX-013B's local "9" does not mean, imply, displace, or reinterpret ADR-002's canonical "9" (Assumptions, Monitoring and Invalidation), and UX-013B's local "10" does not mean, imply, displace, or reinterpret ADR-002's canonical "10" (Implementation Plan). ADR-002's canonical Assumptions/Monitoring/Invalidation and Implementation Plan sections are unaffected by, and unmentioned elsewhere in, this ADR precisely because they are not the subject of it. Any future Phase 3D-2b correction implementing this ADR must preserve this distinction explicitly — for example, by not describing UX-013B's own local list using language ("position 9," "position 10") that could be read as a claim about ADR-002's canonical sequence — so that a reader is never left to guess which of the two numbering systems a given reference to "9" or "10" belongs to.

### R-07 — Conditionality

For **Scenario Analysis**: conditional means the component is available/rendered when the current decision materially depends on multiple plausible future conditions or outcome paths — i.e., when the reasoning genuinely requires acknowledging more than one plausible way the relevant future could unfold. For **Comparison**: conditional means the component is available/rendered when two or more comparable entities, states, alternatives, or outputs exist for which side-by-side evaluation would be useful. In both cases, "conditional" means the component is not always rendered — its presence is gated by whether its own stated semantic precondition currently holds for the specific reasoning session — not that it is permanently hidden, not that it requires special user permission to invoke, and not that it is gated by any product-tier, model-confidence, or numerical threshold (none of which any committed source supports and none of which this ADR introduces). No backend evaluation rule, numerical threshold, or model-confidence requirement is defined or implied by this resolution — the semantic precondition itself is stated in ordinary language, consistent with every other qualitative judgment already established elsewhere in UX-013B (e.g., Scenario Analysis's own Likely/Possible/Unlikely scale).

### R-08 — Opportunity Cost Relationship

Scenario Analysis may semantically inform Opportunity Cost's content — a user's Upside/Downside Case reasoning is legitimate, permitted input to their own judgment of what is foregone. Opportunity Cost remains an independent, unconditional canonical Decision Workspace section at position 7 (ADR-002 C-03, **not reopened**), regardless of whether Scenario Analysis exists, is populated, or logically precedes or follows it in any specific reading flow. No strict, required, one-directional dependency exists between them. UX-013B §14's own current linear Dependency Chain diagram, which places Opportunity Cost's stage before "Scenario Analysis + Comparison," and its own explicit Dependencies list, which omits Scenario Analysis as a named Opportunity Cost input despite §9's own prose stating it "should inform" Opportunity Cost, together **overstate strict sequential ordering** where the actual relationship is informational only. A future source correction should distinguish semantic influence (which may exist) from canonical section order (which is fixed, per ADR-002, independent of any component's own semantic-influence claims) — not performed here, and not a precondition for Phase 3D-2b's other corrections.

### R-09 — Candidate Content Relationship

ADR-003 R-06 is preserved unchanged: Scenario Analysis and Comparison both remain upstream analytical capabilities whose relevant output is synthesized into Proposed Decision Candidate Content. This derivational role does not, and under this ADR still does not, grant either component canonical Decision Workspace sequence membership, independent Domain Object identity, or independent persistence. Candidate Content remains distinct from Proposed Decision, exactly as ADR-003 R-04 established. Candidate Content's own identity is **not reopened** by this ADR.

### R-10 — Scenario Workspace Status

Scenario Workspace is **not required** by this decision, is **explicitly and safely deferred**, and remains exactly the anticipated-but-undesigned future Workspace type UX-012 §69 already describes. This ADR does not design it, does not assign it navigation, layout, persistence, or ownership, and does not treat its eventual existence as a precondition for, or a consequence of, any resolution adopted above. Whether it is ever created, and whether it would replace or supplement inline Scenario Analysis, remains a distinct, low-priority, product-roadmap decision (UX-013B's own Remaining Reasoning Question 4), unaffected by this ADR in either direction.

### R-11 — Domain Object / Persistence Non-Decision

Neither Scenario Analysis nor Comparison is adopted as an independently identified Domain Object by this ADR. No identifier, persistence schema, backend representation, or provenance model is established for either concept. Any future adoption of either as a Domain Object requires its own, separate, explicitly-justified architectural decision, exactly as ADR-003 R-07 required for Candidate Content.

### R-12 — Phase 3D-2b Authorization Boundary

This ADR resolves the architectural blocker Phase 3D-2b's own "component 1" (Scenario Analysis's and Comparison's canonical-sequence status and placement) named as its prerequisite. It creates the authority a future, separately-authorized Source Correction Plan governance amendment needs to perform Phase 3D-2b's own remaining scope. Phase 3D-2b **may**, once such a governance amendment is adopted: reframe UX-013B §14's own heading and introductory text to disclose its local, non-canonical status (R-01); remove or replace "Scenario Comparison" from UX-013B §8's prose, with a disclosed correction notice (R-05); define conditionality inline in UX-013B (R-07); correct the Dependency Chain diagram/Dependencies list to state Scenario Analysis's informational (not strictly sequential) relationship to Opportunity Cost (R-08); and, as its own separate, already-anticipated component-2 scope, restore Proposed Decision and Decision Rationale to UX-013B's §14 list in the correct full-sequence context, resolving the numbering gaps left by Phase 3D-1 and Phase 3D-2a. Phase 3D-2b **must not**: reopen Opportunity Cost's or Portfolio Consequences's own canonical positions (7, 8); reopen Recommendation/Proposed Decision Candidate Content's own settled identity (ADR-003); reopen Portfolio Recommendation's own identity; adopt a Domain Object for either Scenario Analysis or Comparison; design or adopt a Scenario Workspace; or claim, in any correction notice, that UX-013B's §14 list is now a complete, canonical, fully-reconciled Decision Workspace sequence — R-01 already establishes it never was one and does not become one through this correction.

## Consequences

### Positive

- Finding 8.3/M-6 — open since the original Architecture Review, diagnosed but never resolved — is now closed.
- Contradictions K-1 through K-4 are all resolved without reopening ADR-002 or ADR-003.
- Phase 3D-2b's own architectural blocker (component 1) is closed, unblocking its future governance amendment and source-correction work.
- Scenario Analysis and Comparison each retain a clean, stable, non-overlapping semantic identity.
- No new Domain Object, no new persistence model, and no expansion of the canonical thirteen-item sequence was required.

### Negative

- UX-013B's §14 heading/framing, its §8 "Comparison Types" prose, its Dependency Chain diagram, and its Dependencies list all now require a future source correction to align with this ADR — none of that correction is performed here.
- Until that correction lands, an authority split exists: this ADR states the correct classification and boundary, while UX-013B's committed text still frames §14 as if reconciliation-pending and still names a fifth Comparison type, mirroring the same kind of temporary split ADR-002 and ADR-003 each already accepted as their own trade-off.
- The Atlas UX Source Correction Plan's own Section 5/8 characterization of UX-013B's §14 list requires a future, narrow correction to match R-01 — not performed here.

### Accepted Trade-offs

- This ADR accepts that "local Reasoning-component ordering model" is a less tidy characterization than "canonical sequence," in exchange for not reopening ADR-002 and not inventing new canonical architecture unsupported by the four-document lineage.
- This ADR accepts retiring "Scenario Comparison" outright (R-05) rather than the lighter-touch option of leaving it formally ambiguous, because Architectural Principle 17 (the selected model must minimize contradiction, not maximize documentary convenience) favors a clean, disclosed resolution over indefinitely preserving Finding 8.3/M-6's own diagnosed ambiguity.

## Non-Decisions

See Non-Scope, above, for the authoritative list. In addition, explicitly not decided here: the exact future property/state-label name for either component in implementation code; whether Comparison's "Alternative Comparison" type needs its own prop-level accommodation for scenario-specific fields (an implementation-level question, not architectural); the precise wording of any future UX-013B correction notice implementing this ADR (left to that future task, per this program's own established pattern).

## Required Downstream Corrections

**Required** (directly implements a resolution adopted above):
1. UX-013B §8 "Comparison Types" prose — remove "Scenario Comparison" as a named type, with a disclosed correction notice citing this ADR (implements R-05).
2. UX-013B §14 heading/introductory text — disclose that this list is a local Reasoning-component ordering model, not a canonical Decision Workspace sequence (implements R-01).
3. Review-resolution status for Finding 8.3/M-6 (`UX-Architecture-Review-001.md`) — should be annotated as resolved by this ADR, once accepted (a disclosure/status update, not a rewrite of the original finding's own historical text).

**Likely** (probable consequence, not strictly compelled by any single resolution above):
4. Atlas-UX-Source-Correction-Plan.md — Section 5's C-03 row and Section 8/69's "competing normative order" characterization likely require a narrow future correction to match R-01; Phase 3D-2b's own entry likely requires updating to reflect this ADR's adoption and to scope its own future implementation task per R-12.
5. UX-013B §14 Dependency Chain diagram and Dependencies list — likely require correction to state Scenario Analysis's informational (not strictly sequential) relationship to Opportunity Cost (per R-08), and to reflect R-04's rendering/ownership boundary.
6. UX-013B Component Inventory — no correction likely required (already reflects the correct four-variant count, per R-05), but should be explicitly re-confirmed, not silently assumed, during that future implementation task.

**No correction required:**
7. UX-013E — its own four-variant Comparison classification (line 906) and its own Reasoning-category placement of both components (line 481) are already correct under this ADR and require no change.
8. ADR-002, ADR-003 — neither requires amendment.

## Explicit Non-Decisions

Restated for clarity, per this ADR's own Non-Scope section: Portfolio Recommendation identity; Recommendation/Proposed Decision Candidate Content identity; Proposed Decision identity; Decision Rationale identity; Final Decision Card identity; Record Decision identity; exact Decision Workspace implementation; UX copy, visual layout, charts, spacing, animation; backend schema, persistence, provenance implementation; Domain Object adoption for either component; scenario-generation algorithms; forecasting/financial methodology; model provider; scenario accuracy; maximum scenario count; Scenario Workspace design, navigation, or ownership; product-tier rules; mobile layout; detailed accessibility implementation. None of these is decided by implication anywhere above.

## Relationship to ADR-001

This ADR applies ADR-001's general non-fabrication and non-silent-deletion principles to resolve Contradiction K-3: it does not silently delete the disclosure that Scenario Comparison was once named (R-05 explicitly states what is being retired and why, per ADR-001's own requirement that provenance/classification changes be disclosed, not erased). Does not amend ADR-001.

## Relationship to ADR-002

Depends on ADR-002 C-03's own canonical table, unchanged and unexpanded (R-06). Does not amend ADR-002.

## Relationship to ADR-003

Extends ADR-003's own reasoning (Alternative D's precedent; R-06's derivational-relationship framing) to a structurally adjacent case. Does not amend, reopen, or reinterpret ADR-003.

## Relationship to UX-012

Preserves UX-012 §17's canonical sequence and §69's "not designed here" characterization of Scenario Workspace unchanged. Does not amend UX-012.

## Relationship to UX-013B

Identifies four future correction targets (§8 prose, §14 heading, §14 Dependency Chain/Dependencies) per Required Downstream Corrections, above. Does not itself edit UX-013B.

## Relationship to UX-013E

Confirms UX-013E's own four-variant Comparison classification and Reasoning-category placement are already correct and require no change. Does not edit UX-013E.

## Relationship to the Source Correction Plan

Identifies the Plan's own Section 5/8/69 characterization of UX-013B's §14 list as requiring a likely future, narrow correction (R-01). Does not itself amend the Plan — a future governance amendment, following this program's own established pattern, is required before any such correction is performed.

## Relationship to Phase 3D-2b

Resolves Phase 3D-2b's own named architectural blocker (component 1). Defines, per R-12, exactly what Phase 3D-2b's future governance amendment and source correction may and may not do. Does not itself perform, or authorize performing, any Phase 3D-2b source correction — that remains separate, later, and requires its own governance amendment, independent review, and commit gate, per this program's own established pattern.

## Supersession and Precedence

This ADR supersedes no prior ADR. It does not reopen, revise, or reinterpret any part of ADR-001, ADR-002, or ADR-003 — it applies all three, unchanged, to a question none of them previously resolved. It resolves `UX-Architecture-Review-001.md`'s Finding 8.3, listed there as M-6.

## Validation Criteria

A future correction implementing this ADR must be checked against: ADR-002's thirteen-item table remains unchanged and unexpanded; Proposed Decision remains at position 3, Decision Rationale at position 4, Opportunity Cost at position 7, Portfolio Consequences at position 8, Final Decision Card at position 12, Record Decision at position 13 — all unchanged; ADR-002's own canonical positions 9 (Assumptions, Monitoring and Invalidation) and 10 (Implementation Plan) remain unchanged and are never described using language that could be confused with UX-013B's local-list items of the same numerals; ADR-003's ten resolutions remain unchanged; no Domain Object is introduced for either Scenario Analysis or Comparison; Scenario Workspace is not designed or adopted; Portfolio Recommendation remains untouched; UX-013B §14 is reframed as a local ordering model, not renumbered into a claimed-canonical shape; Scenario Comparison is removed from §8's prose with a disclosed notice, not silently deleted; the Component Inventory and UX-013E remain unedited on this point (already correct); conditionality is defined per R-07 wherever it is implemented; Opportunity Cost's informational (not strictly sequential) relationship to Scenario Analysis is stated without altering Opportunity Cost's own canonical position; no correction implementing this ADR mandates a specific Comparison variant (e.g., Alternative Comparison) as the exclusive mechanism for rendering compared scenario content.

## Open Questions

- **Should the future Phase 3D-2b governance amendment implement R-01/R-05/R-07/R-08 as one combined correction, or split them into further sub-phases**, mirroring this program's own established practice of splitting corrections along independently-separable lines (as Phase 3D-2 was split into 3D-2a/3D-2b)? Not decided here; either approach is compatible with this ADR.
- **Does UX-012 itself (as distinct from UX-013B) contain any text that needs correction as a consequence of R-05's retirement of Scenario Comparison?** Not exhaustively checked beyond UX-012 §17, §18, §69, which contain no reference to Scenario Comparison; a future, narrow search is the appropriate mechanism to confirm this fully before Phase 3D-2b's own implementation.
- **Should Finding 8.3/M-6's own review-document status line be updated as its own tiny, separate correction, or bundled into Phase 3D-2b's future work?** Not decided here.

## Definition of Done

This ADR is Done, for the purpose of this task, when: it exists as a complete, self-contained, internally consistent document; every required decision dimension (Required Decision Dimensions 1–24 of the originating task) is addressed by an explicit resolution or an explicit non-decision; every candidate architecture is tested and given a verdict; every contradiction (K-1–K-4) is resolved or explicitly, safely deferred; no existing file is modified; and the document is staged for independent review, not adopted. Adoption (Status: Accepted) requires a separate, future independent-review task, following this program's own established pattern for ADR-003.

## Working Tree Verification

**Branch:** main
**HEAD at time of this ADR:** `867a0338e8ce8eed5c6c70cd6407ec68b32bcd94` ("docs(ux): reconcile UX-013B sequence with ADR-002") — unchanged throughout this task.
**Files created:** `docs/atlas_ux/governance/ADR-004-Scenario-Analysis-Comparison-and-Sequence-Authority-Resolution.md` (this document). No new directory was required.
**Files modified:** none. No UX source document under `docs/atlas_ux/*.md` was changed. `ADR-001-Missing-Source-Volume-Governance.md`, `ADR-002-Critical-UX-Architecture-Resolutions.md`, and `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` were not modified. `Atlas-UX-Source-Correction-Plan.md` was not modified. Neither `UX-Architecture-Review-001.md` nor `UX-Critical-Findings-Resolution-Design-001.md` was modified.
**Staged files:** none.
**Untracked files:** `docs/atlas_ux/governance/ADR-004-Scenario-Analysis-Comparison-and-Sequence-Authority-Resolution.md`.

No commit was made.

# UX-013B — Atlas Component Specification: Reasoning Components

Governing references: UX-012 — Atlas Design System & Workspace Consistency Specification; UX-013A — Atlas Component Specification: Foundation Components; all previously approved Atlas UX specifications.

Volume 2 of the Atlas Component Library. This document specifies every Atlas Reasoning Component in production-ready detail. Figma components can be built directly from these specifications. Engineering can implement without inventing behavior. Future designers can extend Atlas without reinterpretation.

**Correction Notice (Phase 3, governed by ADR-002 — 2026-07-25):** This document's original identity (title, governing references, and original date, as above) is preserved unchanged. Two semantic areas were corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan, Phase 3:
- **C-01 (Information Hierarchy):** the Reasoning Audit's "Metadata, labels, contextual text: Level 4–5" clause was corrected to "Levels 5–6," and the Context Panel's own hierarchy classification was corrected from "Level 4 or Level 5" to "Level 5," since Level 4 is now reserved exclusively for Challenges, Uncertainty, and Contradiction (per UX-012 §5, corrected), and the Context Panel's own declared purpose — background, definitional, and reference content — never includes Challenge or contradiction content.
- **C-02 (AI Authorship and Provenance):** the Conclusion component's Engineering Notes were clarified, without changing the existing silent-label-update behavior, to state that the original Atlas text and acceptance/edit timestamps are separately, permanently preserved in the provenance record regardless of the current attribution label.

**This correction does not resolve, and does not claim to resolve, this document's own separately labeled "Decision Workspace sequence"** (§14, Reasoning Relationships, below), which remains unchanged and is held for a dedicated future reconciliation with the canonical Decision Workspace sequence (Phase 3D of the Atlas UX Source Correction Plan) — this document is not fully C-03-consistent as a result, and no claim of complete C-03 consistency is made here.

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, above. All content outside these two corrected areas, including every Reasoning Component's own specification, is unchanged.

**Correction Notice (Phase 3D-1, governed by `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` — 2026-07-25):** This document's own former "Recommendation" component (previously `# 10. Recommendation`) has been renamed **Proposed Decision Candidate Content** (short form, once established in context: "candidate content"). ADR-003 distinguishes two previously conflated concepts: **Atlas Recommendation** — a general, Atlas-origin directional advisory artifact defined in `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §28, unrelated to this document and not touched by this correction — and **Proposed Decision Candidate Content** — the transient, Atlas- or user-originated candidate wording this document's own component specifies, destined for the Proposed Decision field. This document's former "Recommendation" component always represented the latter; only its own naming has changed, not its behavior, relationships, or interaction model. Prior text (component heading): "`# 10. Recommendation`." Prior text (variant names): "`**Atlas Recommendation**`" and "`**User Recommendation**`," now "Atlas-Generated Candidate Content" and "User-Authored Candidate Content" respectively — the former "Atlas Recommendation" variant name is retired specifically because it collided with UX-012 §28's own, unrelated "Atlas Recommendation" artifact (ADR-003 R-02). This document's own separately labeled "Decision Workspace sequence" (§14, Reasoning Relationships) previously listed this component as item 11; per ADR-003 R-08, that item has been **removed outright, not renamed and not relocated** — this component was never a valid, independent canonical Decision Workspace sequence member. The remaining items in that list (1–10, 12–13) are unchanged in content, order, and numbering by this correction — item 11's own number is not reused, and no replacement item has been added. **This correction does not resolve, and does not narrow, Scenario Analysis's or Comparison's own canonical-sequence placement, the retained "What Changed" entry, or the Portfolio Consequences/Opportunity Cost ordering** — all remain exactly as unresolved as the Phase 3 notice above states them, now tracked as Phase 3D-2 of the Atlas UX Source Correction Plan. The "Portfolio Recommendation" variant is unaffected by this correction — ADR-003 does not examine it, and it is not renamed, reclassified, or otherwise altered here.

**Correction Notice (Phase 3D-2a, governed by `ADR-002-Critical-UX-Architecture-Resolutions.md` C-03 — 2026-07-26):** ADR-002 governs the canonical Decision Workspace sequence (`UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §17). Two mechanical corrections are made to this document's own separately labeled "Decision Workspace sequence" (§14, Reasoning Relationships, below), both dictated directly by that canonical order and independently separable from every other entry in the list. First, the former item "3. What Changed" has been **removed outright, not renamed and not relocated** — ADR-002/UX-012 §17 explicitly states "'What Changed' is a templating artifact carried over from the Investment Workspace and is not adopted as a standalone Decision Workspace section." No replacement item occupies the vacated position; position 3 is left an explicit, visible gap, alongside the existing gap at position 11 (from the Phase 3D-1 correction above). Second, "Portfolio Consequences" and "Opportunity Cost" — previously ordered 7/8 in reverse of the canonical sequence — are restored to their canonical order: Opportunity Cost at position 7, Portfolio Consequences at position 8; only their relative order changed, not their content, definitions, or the existing UX-013C cross-reference on Portfolio Consequences.

**Proposed Decision and Decision Rationale remain omitted from this list.** ADR-002/UX-012 §17 already, unambiguously governs both — Proposed Decision at canonical position 3, Decision Rationale at canonical position 4 — and this correction does not reopen or question that governance. Their omission from this document's own list is a **confirmed discrepancy, not an open or architecturally unresolved question**: their restoration is structurally deferred to a future, complete sequence reconstruction (Phase 3D-2b of the Atlas UX Source Correction Plan), because inserting either at its canonical position, inside this document's own structurally divergent numbering, cascades into a collision with Supporting Factors, Challenges, and Assumptions that this narrowly-bounded correction does not attempt to resolve.

**Scenario Analysis and Comparison remain unresolved** — genuinely, architecturally unresolved, unlike Proposed Decision and Decision Rationale above. Neither is renamed, renumbered, or reclassified by this correction; their own canonical-sequence status remains blocked on a dedicated architectural decision, held as Phase 3D-2b, which this correction does not create, perform, or propose.

**This correction does not claim the UX-013B sequence is now fully reconciled with ADR-002.** Positions 3 and 11 remain visible gaps; Scenario Analysis and Comparison remain unresolved at positions 9 and 10; Proposed Decision and Decision Rationale remain absent, pending Phase 3D-2b. Phase 3D-1 (above) remains complete and unchanged by this correction. The "Portfolio Recommendation" variant remains unaffected — this correction does not classify, rename, or otherwise touch it. No Domain Object, persistence, provenance, backend, interaction, or visual-layout decision is introduced by this correction.

---

# Reasoning Component Philosophy

## Why Reasoning Is Atlas's Primary Product

Atlas exists to improve the quality of investment decisions. Not to surface more data. Not to accelerate execution. Not to automate conclusions. To improve the quality of the reasoning that precedes a decision.

Reasoning Components are the primary expression of that purpose. They are not decorative. They are not organizational. They are the atoms of the reasoning process made visible and navigable — the components that allow a user's thinking to be structured, examined, challenged, and recorded.

A Workspace without Reasoning Components is a blank document. A Workspace with well-specified Reasoning Components is a thinking environment.

## Why Reasoning Components Exist Independently of Decisions

A Decision is the output of reasoning. Reasoning Components exist before the Decision, during it, and persist after it in the Historical Record. They are not scaffolding for a Decision form — they are the substance of thinking in progress.

This independence means:
- Reasoning Components appear in Investment Workspaces (where no Decision is being made) as the primary content.
- Reasoning Components within a Decision Workspace are fully valid even if no Decision is ever recorded.
- Historical Reasoning Components — preserved from prior reasoning sessions — retain meaning independently of whether the reasoning led to a recorded Decision.

The reasoning is the work. The Decision records its conclusion.

## How Reasoning Should Remain Structured Rather Than Narrative

The risk in a reasoning environment is drift toward free-form narrative — long paragraphs that mix conclusion, evidence, challenge, and assumption without distinction. Structured Reasoning Components prevent this drift.

Each Reasoning Component has a defined semantic purpose. Supporting Factors name and weigh reasons. Challenges name and classify concerns. Assumptions state conditions explicitly. Opportunity Cost makes the foregone explicit. These components enforce structure not by constraining what the user can write, but by giving each distinct type of reasoning a distinct location.

Structure does not mean brevity. A Supporting Factor may have a lengthy explanation. An Assumption may have extensive conditions. But each occupies its designated component, making the reasoning legible to the user themselves on return, and to reviewers examining the historical record.

## Why Reasoning Components Should Communicate Relationships Rather Than Persuasion

Investment platforms often present reasoning as a case for action — an argument that the conclusion is correct. Atlas explicitly rejects this posture.

Reasoning Components present relationships: how does this factor relate to the conclusion? How does this challenge relate to the assumption it contradicts? How does the opportunity cost relate to the proposed action?

Relationships are honest. They allow contradictory information to coexist without suppression. They allow the user to see the full structure of their reasoning rather than just the direction it points. A Reasoning Component that presents a challenge is not undermining the conclusion — it is completing the picture.

## How Reasoning Components Reduce Cognitive Load While Preserving Analytical Depth

Cognitive load in reasoning comes from holding multiple things simultaneously: what do I know, what concerns me, what am I assuming, what am I giving up? Reasoning Components externalize each of these into a defined location. The user does not have to hold the structure in their head — Atlas holds it.

This externalization does not reduce the depth of analysis. It enables greater depth by freeing cognitive resources from structural maintenance. A user who does not need to remember "where did I put my concern about valuation?" can spend more attention on the concern itself.

The result is that a well-structured set of Reasoning Components should represent more analytical work, not less, than the same information held in unstructured notes.

## Governing Principles for All Reasoning Components

**1. One semantic purpose per component.** A Reasoning Component does one thing — names a factor, states an assumption, describes an opportunity, identifies a challenge. It does not mix reasoning types.

**2. Structure without constraint.** Reasoning Components provide a defined location for each type of reasoning. They do not constrain what can be written within that location.

**3. Relationships are explicit.** Connections between Reasoning Components (a Challenge that contradicts an Assumption; an Opportunity Cost that relates to a Conclusion) are represented structurally, not implied by proximity.

**4. Authorship is visible.** User-authored content within a Reasoning Component is visually distinguished from Atlas-generated content. The user's voice is primary.

**5. Historical content is permanent and accessible.** Reasoning Components that were part of a completed reasoning session are preserved as Historical Records. Their structure is maintained. They cannot be modified.

**6. State is always communicated.** Every Reasoning Component communicates its current state (draft, validated, historical, monitoring, updated) through consistent visual treatment. The user never needs to guess.

**7. Components are independently meaningful.** A Supporting Factor is comprehensible without reading the Challenges section. An Assumption is legible without reading the Supporting Factors. Components designed to be legible in isolation are also legible when the user reads them in sequence.

---

# 1. Conclusion

## Purpose

The Conclusion is the primary output of a reasoning session or Workspace. It states, in clear terms, what the reasoning currently indicates — the answer to the question the Workspace is organized around. Every Atlas Workspace has a Conclusion. It is the first piece of reasoning content the user encounters.

## Semantic Meaning

The Conclusion communicates: given everything I know and have examined, this is what I currently believe to be true. It is not candidate content (that is the Proposed Decision Candidate Content component). It is not a decision (that is the Decision component). It is the current state of the reasoning — a synthesis rather than an action.

## When Used

- At the top of every reasoning Workspace (Investment, Portfolio, Decision)
- As the primary content of a Section designated as a conclusion area
- In the Decision Workspace: the "Current Conclusion" that updates as reasoning evolves
- In Historical Records: as the preserved conclusion from a prior reasoning session
- In the Decision Summary component (a condensed form for display in other Workspaces)

## When Not Used

- As a sub-element within a Supporting Factor or Challenge. A Conclusion is Workspace-level or Section-level, not nested within another Reasoning Component.
- As the label for an action. The Conclusion is a statement of reasoning, not a call to action.
- In the Dashboard. The Dashboard shows the Decision Summary (a derived read-only condensed form) — not the full Conclusion component.

## Hierarchy

The Conclusion occupies the **Level 1 Information Hierarchy** position. It is the single most prominent piece of content in the Workspace. Its typography uses Role 1 (Primary Conclusion): the heaviest weight, largest size, and most prominent position.

Within the Decision Workspace, there are two Conclusion positions:
1. **Current Conclusion** — at the top of the reasoning body, updated dynamically as the user reasons.
2. **Proposed Decision** — at the bottom of the reasoning body, the user's authored commitment before formalization.

These are distinct components. The Conclusion component specifies the Current Conclusion. The Proposed Decision is specified in UX-013C.

## Variants

**Primary Conclusion**
The settled Workspace-level conclusion. Used at the top of Investment Workspace and Portfolio Workspace.
Visual: Role 1 typography. Fully visible, never collapsed. No expansion control.

**Current Conclusion**
A live-updating conclusion within the Decision Workspace. Updates as the user reasons, as Atlas analysis changes, or when key assumptions shift.
Visual: Role 1 typography with a subtle "Updated" status indicator when content has changed since the user's last session.
Behavior: Editable by the user. Atlas may suggest updates; user accepts or modifies.

**Portfolio Conclusion**
The integration-level conclusion for the Portfolio Workspace — synthesizes multiple investment positions into a portfolio-level view.
Visual: Same as Primary Conclusion. Contains a secondary sub-conclusion area for individual position summaries.

**Review Conclusion**
The conclusion produced by a formal Decision Review — what the review determined about the continued validity of a prior Decision.
Visual: Same as Primary Conclusion, with a "Review Conclusion" label and the review date.

**Historical Conclusion**
The preserved conclusion from a prior reasoning session. Displayed in Historical mode.
Visual: Role 1 typography at reduced opacity (`text.historical.opacity`). Permanently labeled "Historical" with the session date. Immutable.

## Anatomy

```
Conclusion
├── Variant Label [Role 4, optional — "Current Conclusion", "Review Conclusion"]
├── Statement [Role 1 typography — the conclusion itself]
├── [Conditional] Sub-statement [Role 3 — one clarifying sentence]
├── [Conditional] Last-updated indicator [Role 5 — "Updated [date]" or "Updated during this session"]
└── [Conditional] Atlas-authored indicator [Role 5 — "Atlas generated / User accepted"]
```

## Properties

| Property | Type | Default | Required | Notes |
|----------|------|---------|----------|-------|
| `variant` | `'primary' \| 'current' \| 'portfolio' \| 'review' \| 'historical'` | `'primary'` | Yes | |
| `statement` | string | — | Yes | The conclusion text |
| `subStatement` | string | — | No | One clarifying sentence |
| `isAtlasGenerated` | boolean | `false` | No | Shows attribution indicator |
| `isUserModified` | boolean | `false` | No | Shows "User authored" when true even if atlas-originated |
| `lastUpdated` | Date | — | No | Shows update indicator if set |
| `isEditable` | boolean | `false` | No | True for Current Conclusion in Decision Workspace |
| `historicalDate` | Date | — | No | Required when `variant === 'historical'` |
| `originalAtlasText` | `string \| null` | `null` | No | The original Atlas-generated text, permanently preserved regardless of the current attribution label |
| `acceptedAt` | `timestamp \| null` | `null` | No | When Atlas-generated content was accepted, if applicable |
| `editedAt` | `timestamp \| null` | `null` | No | When the user genuinely edited the content, if applicable — distinct from acceptance |

## States

| State | Description |
|-------|-------------|
| Default | Statement displayed in Role 1 typography |
| Atlas-generated | Statement has Atlas origin; attribution indicator shown |
| User-authored | User wrote or modified the statement; no indicator (user authorship is the default) |
| Updated | Content changed since last session; Update token fires once then settles |
| Editing | User is editing the statement (Current Conclusion variant only) |
| Saved | Brief Saved indicator after autosave |
| Historical | Reduced opacity; locked; Historical label and date prominent |
| Loading | Skeleton placeholder at Role 1 scale |

## Interaction

**Read-only variants (Primary, Portfolio, Review):**
No editing interaction. Hover has no effect. The Conclusion is not a tap target for expansion (it is always fully visible).

**Current Conclusion (editable):**
- Hover: subtle edit invitation (cursor changes, background lightens slightly)
- Click/tap: enters editing state, cursor placed in the statement text
- Editing: Long-Form Editor behavior applies (see UX-013D)
- Blur: exits editing state, triggers autosave
- Atlas Suggestion: appears after 1.5s pause during editing inactivity

**Historical variant:**
No interaction. No hover effect. No cursor change.

## Historical Behavior

When displayed as a Historical Conclusion:
- Statement text at `text.historical.opacity` (approximately 70% opacity)
- "Historical Record — [date]" label above the statement, in Role 5 typography
- No editing controls, no hover state, no focus ring on the statement
- Included in the Historical Section's accessible content — screen reader announces historical status

The Historical Conclusion is presented alongside the current reasoning for comparison (Historical Comparison pattern). It is never presented as if it is current.

## Accessibility

- Statement: `<h2>` or `<h1>` depending on position in Workspace hierarchy. The Current Conclusion in the Decision Workspace is `<h2>` (Workspace Header title is `<h1>`).
- Variant Label (if present): preceding text in the ARIA label — `aria-label="Current Conclusion: [statement]"`.
- Editable Current Conclusion: the editing target is a text area or content-editable element with `aria-label="Current Conclusion"` and `aria-multiline="true"`.
- Atlas-generated indicator: visually visible and screen-reader accessible ("Atlas generated, user accepted").
- Updated indicator: `aria-live="polite"` region — announces when the conclusion updates.
- Historical variant: `aria-label` includes "Historical Record from [date]: [statement]".

## Responsive Behavior

**Desktop:** Full typography at Role 1 scale. Sub-statement below. Attribution indicator right-aligned or below.
**Tablet:** Same as desktop. Statement may wrap to additional lines; line height maintained.
**Mobile:** Role 1 typography is reduced slightly for mobile (responsive token). Statement is full-width. Sub-statement below. Attribution indicator below the sub-statement.

## Spacing Rules

- Above the Conclusion (from Workspace Header or preceding component): `spacing.level5`
- Below the Conclusion (before first Reasoning Block or Section): Pause Point 1 spacing (`spacing.pause1`)
- Between Statement and Sub-statement: `spacing.level1`
- Between Sub-statement and metadata: `spacing.level2`

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Statement color | `conclusion.text.primary` |
| Sub-statement color | `conclusion.text.secondary` |
| Variant label color | `text.label.secondary` |
| Historical opacity | `text.historical.opacity` |
| Historical label color | `status.historical.text` |
| Updated indicator color | `status.updated.text` |
| Atlas attribution color | `text.attribution.atlas` |
| Editing background | `editing.field.background` |
| Editing focus ring | `focus.ring.color` |

## Figma Structure

```
Conclusion [Frame, Auto Layout, vertical]
├── VariantLabel [Text, Role 4, conditional]
├── Statement [Text, Role 1]
├── SubStatement [Text, Role 3, conditional]
└── MetadataRow [Frame, Auto Layout, horizontal, conditional]
    ├── UpdatedIndicator [StatusBadge, conditional]
    └── AtlasAttribution [Text, Role 5, conditional]
```

Figma Properties: `variant` (enum), `isEditable` (boolean), `hasSubStatement` (boolean), `hasAttribution` (boolean), `isHistorical` (boolean).

## Engineering Notes

- For the Current Conclusion (editable): implement as a rich text field, not a plain `<textarea>`. The statement supports basic formatting (bold for emphasis within the statement). Maximum recommended length: 3 sentences.
- The Conclusion component is always server-persisted — it is never stored locally only. Draft state is handled by the Draft Indicator in the Workspace Header, not by the Conclusion component itself.
- When `isAtlasGenerated` transitions to `isUserModified` (user edits Atlas-generated content), update the attribution silently. Do not prompt the user to confirm they have modified it. The original Atlas text and the acceptance/edit timestamps are, regardless of the current attribution label, separately and permanently preserved in the provenance record — "silently" governs only the displayed label, never the underlying record.

## Anti-Patterns

- **Do not use the Conclusion for action calls.** "Buy Acme Corp" is a Decision, not a Conclusion. "Acme Corp represents a compelling risk-adjusted opportunity at current valuations" is a Conclusion.
- **Do not place more than one Primary Conclusion in a Workspace.** One conclusion per Workspace-level context.
- **Do not abbreviate the Conclusion for brevity's sake.** The Conclusion is a complete statement. Truncation (ellipsis) is not applied to the Conclusion statement.
- **Do not use the Conclusion component to display data.** The Conclusion is narrative prose, not a data point.

---

# 2. Supporting Factors

## Purpose

Supporting Factors are named, discrete reasons that support the current reasoning direction or Conclusion. They make the evidence behind the Conclusion explicit and individually examable. Each Supporting Factor is a distinct claim about why the reasoning is well-founded.

## Semantic Meaning

A Supporting Factor communicates: here is one specific reason the Conclusion appears to be correct. Multiple Supporting Factors together build the case for the Conclusion — but each stands independently and can be challenged, updated, or invalidated separately.

## When Used

- In every reasoning Workspace where the Conclusion requires substantiation
- In the Decision Workspace: as the explicit rationale for the Proposed Decision
- In the Investment Workspace: as the investment case
- In the Historical Record: as the preserved rationale from a prior session

## When Not Used

- As a location for general observations not connected to the Conclusion
- As a substitute for the Conclusion itself
- For concerns or counter-arguments (those belong in Challenges)

## Relationship to Conclusion

Supporting Factors are directionally subordinate to the Conclusion. They support a specific Conclusion. If the Conclusion changes significantly, the Supporting Factors should be reviewed — they may no longer be relevant to the new direction.

This relationship is not enforced programmatically but is communicated through the component's position in the reading flow (below the Conclusion) and its documentation.

## Ordering

Supporting Factors are ordered by the user. No automatic ordering. The user places the most important factor first (a convention, not an enforcement).

The user may reorder factors at any time during the reasoning session. On reorder, factors animate with the Insert and Remove motion tokens to communicate the change.

## Grouping

Supporting Factors may be grouped by the user into named categories (e.g., "Financial" / "Strategic" / "Market"). Grouping is optional. When ungrouped, factors appear as a flat list.

**Group Header:** Role 4 typography, above the group's factors. Subordinate to the Supporting Factors section heading.

## Evidence Association

Each Supporting Factor may reference one or more pieces of evidence (data points, source documents, prior reasoning). Evidence is displayed as a Supporting Metadata component attached to the factor.

Evidence association is optional. A factor without evidence is valid — the user may be drawing on general knowledge or experience that cannot be cited.

## Strength Indication

Supporting Factors do not use numerical strength scores or visual gauges (no stars, no bars, no percentages). Strength is communicated through the user's written explanation of the factor's significance.

If a factor is particularly significant, the user may indicate this through a user-authored "Weight" label (Strong / Moderate / Supporting) — a qualitative classification, not a metric.

## Variants

**Simple Factor**
A named factor with a brief explanation. No grouping, no evidence, no weight label.
Anatomy: Factor Name + Explanation text.

**Evidenced Factor**
A factor with attached Supporting Metadata (source, data point, reference).
Anatomy: Factor Name + Explanation text + Supporting Metadata.

**Grouped Factors**
Multiple factors under a shared Group Header.
Anatomy: Group Header + [Simple or Evidenced Factors].

**Historical Factor**
A factor from a prior reasoning session, preserved in Historical mode.
Anatomy: Same as Simple or Evidenced, with historical visual treatment.

## Anatomy

```
SupportingFactors [Section using SectionContainer]
├── SectionHeader ("Supporting Factors")
└── SectionBody
    ├── [Conditional] Group [Auto Layout, vertical]
    │   ├── GroupHeader [Role 4]
    │   └── [FactorItem × n]
    └── [FactorItem × n] (ungrouped)

FactorItem
├── FactorName [Role 3, medium weight]
├── Explanation [Role 3, regular weight — the narrative support]
├── [Conditional] WeightLabel [Role 5 — "Strong" / "Moderate" / "Supporting"]
├── [Conditional] SupportingMetadata [metadata component]
└── FactorActions [Section Action: Edit, Remove — right-aligned, visible on hover]
```

## Properties

**SupportingFactors (container):**
| Property | Type | Default | Required |
|----------|------|---------|----------|
| `factors` | `Factor[]` | `[]` | Yes |
| `isEditable` | boolean | `false` | No |
| `isHistorical` | boolean | `false` | No |
| `groupingEnabled` | boolean | `false` | No |

**Factor (item):**
| Property | Type | Default | Required |
|----------|------|---------|----------|
| `id` | string | — | Yes |
| `name` | string | — | Yes |
| `explanation` | string | — | Yes |
| `weight` | `'strong' \| 'moderate' \| 'supporting' \| null` | `null` | No |
| `evidence` | `Evidence[]` | `[]` | No |
| `isAtlasGenerated` | boolean | `false` | No |
| `groupId` | string | — | No |
| `historicalDate` | Date | — | No |

## States

| State | Description |
|-------|-------------|
| Default | Factors displayed in reading order |
| Editable | Edit and Remove controls visible on hover |
| Editing (factor) | Individual factor in Long-Form Editor mode |
| Atlas-generated | Factor has Atlas origin; attribution shown |
| Weakening | Factor's relevance is challenged by an Assumption in "Weakening" status |
| Invalidated | Factor is directly contradicted by a Broken Assumption or identified Contradiction |
| Historical | Full section in historical visual treatment |
| Empty | No factors yet; Action-Required Empty State |
| Loading | Skeleton placeholders for expected factors |

**Weakening and Invalidated states:** visually distinguished with a left-border treatment (same visual language as Challenges severity levels — a consistent system across components). Weakening: `border.factor.weakening` (amber). Invalidated: `border.factor.invalidated` (red). The label "Weakening" or "Invalidated" appears as a Status Badge adjacent to the Factor Name.

## Interaction

**Reading:** No interaction. Factor items are not tappable unless editable mode is active.

**Editing:**
- Add Factor: Section Action in Section Header ("+Add factor"). Opens an empty FactorItem in editing state.
- Edit Factor: hover reveals Edit action (pencil icon) on the FactorItem. Clicking enters Long-Form Editor mode for that factor.
- Remove Factor: hover reveals Remove action. Confirmation required ("Remove this factor?"). Uses Remove motion token.
- Reorder: drag handle (visible on hover, accessible via keyboard with Arrow key reorder). Uses Insert and Remove motion tokens.
- Group: when `groupingEnabled`, a "Group by" Section Action allows the user to add Group Headers and assign factors.

**Atlas Suggestion:** After 1.5s pause, Atlas may suggest additional factors. Suggestions appear as draft FactorItems at the end of the list with Atlas attribution. Accept: factor added to the list. Dismiss: factor removed for the session.

## Accessibility

- Section: `<section aria-labelledby="supporting-factors-heading">`.
- Section Heading: `<h3>` (or appropriate level within the Section header hierarchy).
- Factors list: `<ol>` (ordered — order matters and is user-determined).
- FactorItem: `<li>`.
- Factor Name: `<h4>` (or equivalent heading within the list item).
- Reorder: keyboard-accessible with instructions ("Press Space to select, arrow keys to move, Space to drop"). `aria-grabbed`, `aria-dropeffect` on drag handles.
- Weakening/Invalidated status: communicated via `aria-label` on the Status Badge ("This factor is weakening due to a related assumption").
- Edit and Remove actions: labeled buttons within the FactorItem, visible on focus (not only on hover).

## Responsive Behavior

**Desktop:** Full anatomy. Hover controls. Drag reorder.
**Tablet:** Full anatomy. Touch-accessible reorder (tap to select, tap target to drop). Hover controls replaced with persistent icons.
**Mobile:** Single-column. Reorder via a dedicated reorder mode (tap "Reorder" to enter, tap arrows to move, tap "Done"). Edit and Remove via long-press or visible icon buttons.

## Spacing Rules

- Between FactorItems: `spacing.level3`
- Between GroupHeader and first FactorItem: `spacing.level2`
- Between groups: `spacing.level4`
- Factor Name to Explanation: `spacing.level1`
- Explanation to Metadata: `spacing.level2`

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Factor Name color | `reasoning.factor.name` |
| Explanation color | `text.body.primary` |
| Weight label color | `text.label.secondary` |
| Group header color | `text.label.primary` |
| Weakening border | `border.factor.weakening` |
| Invalidated border | `border.factor.invalidated` |
| Historical opacity | `text.historical.opacity` |
| Atlas attribution | `text.attribution.atlas` |
| Edit action color | `text.action.secondary` |

## Anti-Patterns

- **Do not include challenges or concerns in Supporting Factors.** Concerns belong in the Challenges component.
- **Do not use Supporting Factors as a data table.** They are narrative reasoning, not structured data.
- **Do not require evidence for every factor.** Requiring evidence creates false rigor — not all valid reasoning is citable.
- **Do not use numerical weighting (1–5, percentages).** Qualitative weight labels are the Atlas approach.

---

# 3. Challenges

## Purpose

Challenges are named, discrete concerns, risks, or counter-arguments that complicate the reasoning direction. They make the tensions in the reasoning explicit. Each Challenge is a distinct claim about why the Conclusion may be wrong, incomplete, or more complex than it appears.

## Semantic Meaning

A Challenge communicates: here is one specific reason the reasoning may not be correct, or a risk that must be acknowledged. Challenges do not refute the Conclusion — they complicate it honestly. They are the intellectual integrity of the reasoning process.

## When Used

- In every reasoning Workspace where the reasoning direction has complications, risks, or counter-arguments
- In the Decision Workspace as the counterweight to Supporting Factors
- As the location for detected Contradictions (automatically surfaced by Atlas or manually flagged)
- In Historical Records as preserved concerns from prior sessions

## When Not Used

- For observations that support the Conclusion (those belong in Supporting Factors)
- As a location for monitoring conditions (those are the Monitoring Condition component, specified in UX-013C)

## Relationship to Supporting Factors

Challenges and Supporting Factors are counterweights. Together they constitute the honest case for and against the reasoning direction. Neither should be suppressed. A reasoning session with only Supporting Factors and no Challenges is an incomplete analysis.

Atlas may surface Challenges automatically (as Atlas Warnings) when it detects inconsistencies, but the primary source of Challenges is user reasoning.

## Priority

Challenges have three severity levels, governing their visual treatment and their effect on the completion gate:

**Informational**
A relevant concern that the user should be aware of but that does not require resolution before proceeding.
Visual: left border in `border.challenge.informational` (a subtle neutral tone). No blocking effect.

**Material**
A significant concern that requires explicit acknowledgment in the reasoning. The user must address it (not necessarily resolve it — they may accept the risk and document that acceptance).
Visual: left border in `border.challenge.material` (amber). Subtle amber tint to the FactorItem background. A "Material" Status Badge.
Completion gate effect: Acknowledged Challenges (user has marked them as reviewed) do not block. Unacknowledged Material Challenges create a soft gate — a warning before proceeding, not a hard block.

**Blocking**
A concern that must be resolved or explicitly overridden with documented rationale before the Decision can be recorded.
Visual: left border in `border.challenge.blocking` (red). Red-tinted background. "Blocking" Status Badge.
Completion gate effect: Blocking Challenges that are unresolved or unacknowledged prevent the completion action from proceeding. The user must either resolve the challenge, dismiss it with explicit justification, or reclassify it.

## Grouping

Same model as Supporting Factors. Challenges may be grouped by the user (e.g., "Market Risk" / "Execution Risk" / "Valuation Risk"). Grouping is optional.

## Variants

**Simple Challenge**
Named challenge with explanation. No Atlas association.

**Atlas-surfaced Challenge**
A challenge identified by Atlas analysis (e.g., a detected logical inconsistency, an assumption contradiction). Displayed with Atlas attribution. The user may accept (challenge is added to their list), modify the classification, or dismiss.

**Contradiction**
A Challenge that directly contradicts a stated Supporting Factor or Assumption. Displayed with a "Contradiction" label and a relationship indicator linking to the conflicting element.

**Historical Challenge**
Preserved challenge from a prior session. Historical visual treatment. Immutable.

## Anatomy

```
Challenges [Section using SectionContainer]
├── SectionHeader ("Challenges")
└── SectionBody
    ├── [Conditional] Group [Auto Layout, vertical]
    │   ├── GroupHeader [Role 4]
    │   └── [ChallengeItem × n]
    └── [ChallengeItem × n] (ungrouped)

ChallengeItem
├── SeverityBorder [left border, 3px, color by severity]
├── ChallengeContent
│   ├── ChallengeName [Role 3, medium weight]
│   ├── SeverityBadge [StatusBadge — "Material" or "Blocking", conditional]
│   ├── AcknowledgementState [Role 5 — "Acknowledged" / "Requires acknowledgement"]
│   ├── Explanation [Role 3, regular weight]
│   ├── [Conditional] RelationshipIndicator [links to contradicted Factor or Assumption]
│   └── [Conditional] SupportingMetadata
└── ChallengeActions [right-aligned: Edit, Reclassify, Acknowledge, Remove]
```

## Properties

**Challenge (item):**
| Property | Type | Default | Required |
|----------|------|---------|----------|
| `id` | string | — | Yes |
| `name` | string | — | Yes |
| `severity` | `'informational' \| 'material' \| 'blocking'` | `'informational'` | Yes |
| `explanation` | string | — | Yes |
| `isAcknowledged` | boolean | `false` | No |
| `acknowledgementNote` | string | — | No |
| `contradictsId` | string | — | No | ID of contradicted Factor or Assumption |
| `isAtlasSurfaced` | boolean | `false` | No |
| `isHistorical` | boolean | `false` | No |
| `historicalDate` | Date | — | No |

## States

| State | Description |
|-------|-------------|
| Informational | Left border, no badge, no gate effect |
| Material-unacknowledged | Amber border, amber tint, Material badge, soft gate |
| Material-acknowledged | Amber border, "Acknowledged" label, no gate effect |
| Blocking-unresolved | Red border, red tint, Blocking badge, hard gate |
| Blocking-acknowledged | Red border, amber acknowledgement note, gate cleared |
| Contradiction | Informational/Material/Blocking + Contradiction label + relationship link |
| Historical | All states at historical opacity, immutable |
| Atlas-surfaced | Attribution indicator, pending acceptance |

## Interaction

**Acknowledge:** A "Mark as acknowledged" action on Material and Blocking Challenges. On activation: the user is prompted to enter an acknowledgement note (why this challenge does not block the Decision). Note is required for Blocking; optional for Material.

**Reclassify:** The user may reclassify a Challenge's severity (e.g., from Blocking to Material with justification). Reclassification is recorded in the challenge's history.

**Add Challenge:** Section Action "+Add challenge". Opens a new ChallengeItem in editing state with severity selection.

**Atlas-surfaced Challenges:** Accept or dismiss. Accept adds the challenge to the list. Dismiss removes it for the session.

**Contradiction relationship:** If a Challenge has `contradictsId`, the RelationshipIndicator is a tappable link that navigates (smooth scroll) to the contradicted component.

## Historical Behavior

Historical Challenges are immutable. Their severity, acknowledgement state, and notes are preserved exactly as they were at the time of recording. Historical Blocking Challenges that were acknowledged are shown with their acknowledgement notes intact — providing a complete record of how the user resolved the concern at the time.

## Accessibility

- Section: `<section aria-labelledby="challenges-heading">`.
- ChallengeItem: `<li>` within an `<ul>`. (Unordered — user ordering, but severity determines visual priority, not list order.)
- Severity communicated via Status Badge text label (not color alone).
- SeverityBorder: supplementary to the Badge — color alone is not the only communicator.
- Acknowledge action: `<button aria-label="Acknowledge [ChallengeName]">`.
- Blocking gate announcement: `aria-live="assertive"` — screen reader announces when a Blocking Challenge is cleared.

## Responsive Behavior

**Desktop:** Full anatomy. Hover controls. Left severity border visible.
**Tablet:** Same. Touch targets on acknowledgement and action buttons.
**Mobile:** Single-column. Severity border remains. Actions surface via long-press or persistent icons.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Informational border | `border.challenge.informational` |
| Material border | `border.challenge.material` |
| Material background tint | `surface.challenge.material` |
| Blocking border | `border.challenge.blocking` |
| Blocking background tint | `surface.challenge.blocking` |
| Challenge Name color | `reasoning.challenge.name` |
| Explanation color | `text.body.primary` |
| Acknowledged state color | `status.acknowledged.text` |
| Historical opacity | `text.historical.opacity` |

## Anti-Patterns

- **Do not auto-resolve Blocking Challenges.** The user must explicitly acknowledge or resolve each one.
- **Do not suppress Challenges when the conclusion is positive.** An honest Challenges list is required regardless of the conclusion direction.
- **Do not use Challenges as the location for monitoring conditions.** Monitoring Conditions have their own component.
- **Do not apply the Blocking severity without user or Atlas justification.** Blocking is a serious classification; it should not be the default.

---

# 4. Assumptions

## Purpose

Assumptions are the explicit conditions on which the current reasoning depends. By naming assumptions, the user makes their reasoning honest — they acknowledge what must be true for the reasoning to hold. Each Assumption is a distinct condition that could, if invalidated, change the Conclusion.

## Semantic Meaning

An Assumption communicates: my reasoning depends on this being true. I am not certain it is true — but I believe it is sufficiently likely to proceed. If it turns out to be false, my reasoning should be revisited.

## When Used

- In any reasoning Workspace where the reasoning rests on conditions that are assumed but not certain
- In the Decision Workspace as part of the structured reasoning that accompanies the Decision
- In the Historical Record as the preserved assumptions from a prior session (their status at the time of recording)

## When Not Used

- For facts that are known and certain (those are Evidence, not Assumptions)
- For monitoring conditions (those are the Monitoring Condition component)
- For action items or implementation notes

## Explicit Assumption Recording

The act of writing an Assumption is significant. Many reasoning errors arise from implicit assumptions that are never examined. The Assumptions component forces assumptions into the open — from implicit to explicit, from unexamined to named and tracked.

Once named, an Assumption can be monitored. Once monitored, it can trigger a review when its status changes.

## Dependencies

An Assumption may be marked as depended on by a specific Supporting Factor or the Conclusion itself. This dependency relationship is optional but valuable — it enables the automated detection of when a Broken Assumption invalidates supporting reasoning.

**Dependency model:** An Assumption with `dependedOnBy: ['factor-id-1']` is displayed with a relationship indicator linking to the dependent Factor. When the Assumption status changes to "Broken", the dependent Factor automatically enters the "Invalidated" state and a Contradiction is surfaced in the Challenges section.

## Monitoring Relationships

An Assumption may have an associated Monitoring Condition — a specific, trackable external condition that will provide evidence about whether the Assumption continues to hold.

**Example:** Assumption: "Revenue growth will remain above 8% through the holding period." Associated Monitoring Condition: triggers a review if quarterly revenue growth falls below 8%.

When an Assumption has an associated Monitoring Condition, the Assumption displays the Monitoring Condition's current status (Established / Active / Approaching / Triggered). A Triggered Monitoring Condition on an Assumption transitions the Assumption status to "Weakening."

## Historical Persistence

Assumptions in Historical Records are preserved with their status at the time of recording. A "Holding" Assumption at record time is preserved as "Holding" in the historical record — even if the assumption has since been broken. This ensures the historical record accurately reflects what the user believed to be true at the time of the Decision.

The current status of each assumption (post-recording) is visible in the current Workspace. The historical status is visible in the Historical Record. These are distinct views of the same assumption.

## Variants

**Simple Assumption**
A named assumption with an explanation and a status.

**Monitored Assumption**
A Simple Assumption with an associated Monitoring Condition showing current monitoring status.

**Dependent Assumption**
A Simple or Monitored Assumption with one or more dependency relationships to Supporting Factors or the Conclusion.

**Historical Assumption**
An Assumption as it was at the time of a recorded Decision. Immutable. Displayed with status-at-time-of-recording.

## Anatomy

```
Assumptions [Section using SectionContainer]
├── SectionHeader ("Assumptions")
└── SectionBody
    └── [AssumptionItem × n]

AssumptionItem
├── AssumptionName [Role 3, medium weight]
├── StatusBadge [Holding / Under Review / Weakening / Broken]
├── Explanation [Role 3, regular weight]
├── [Conditional] DependencyIndicators [Role 5 — "Supporting [Factor Name]"]
├── [Conditional] MonitoringStatus [compact MonitoringCondition reference]
└── AssumptionActions [Edit, Change Status, Add Monitoring, Remove — hover]
```

## Properties

| Property | Type | Default | Required |
|----------|------|---------|----------|
| `id` | string | — | Yes |
| `name` | string | — | Yes |
| `status` | `'holding' \| 'underReview' \| 'weakening' \| 'broken'` | `'holding'` | Yes |
| `explanation` | string | — | Yes |
| `dependedOnBy` | `string[]` | `[]` | No | IDs of dependent Factors/Conclusion |
| `monitoringConditionId` | string | — | No | |
| `isHistorical` | boolean | `false` | No |
| `historicalStatus` | same as `status` | — | No | Status at time of recording |
| `historicalDate` | Date | — | No |

## States

| State | Visual Treatment |
|-------|-----------------|
| Holding | Status Badge in neutral tone. Normal opacity and weight. |
| Under Review | Status Badge in amber. Subtle amber tint to item. Indicates the assumption is being examined. |
| Weakening | Status Badge in amber (stronger). Associated Monitoring Condition is in Approaching state. Dependent Factors enter Weakening state. |
| Broken | Status Badge in red. Dependent Factors enter Invalidated state. A Contradiction is surfaced in the Challenges section. |
| Historical | Full historical visual treatment. Status reflects status-at-time-of-recording. |

## Interaction

**Change Status:** A direct status selector on the AssumptionItem (a compact inline control: Holding / Under Review / Weakening / Broken). Changing status to "Broken" triggers the downstream Contradiction flow: affected Factors enter Invalidated state, Challenges section surfaces a Contradiction. A confirmation dialog precedes the Broken transition ("Marking this assumption as Broken will surface a Contradiction in your Challenges. Continue?").

**Add Monitoring:** A Section Action on each AssumptionItem. Opens a Monitoring Condition creation flow (specified in UX-013C).

**Dependency:** Set during factor creation or via an association control on the Assumption item.

## Accessibility

- AssumptionItem: `<li>` in an `<ul>`.
- Status: communicated via Status Badge text (not color alone). `aria-label` on the badge includes the meaning ("Status: Weakening — this assumption is being challenged by recent information").
- Status selector: an accessible control (e.g., `<select>` or a radio group) with all four options labeled.
- "Broken" transition confirmation: uses Dialog Container with explicit confirmation action.
- Dependency links: `<a>` elements with `aria-label="This assumption supports: [Factor Name]"`.

## Responsive Behavior

**Desktop:** Full anatomy. Status selector inline. Monitoring status compact reference.
**Tablet:** Same. Touch-accessible status selector.
**Mobile:** Status selector presented as a bottom-sheet picker on tap.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Assumption Name color | `reasoning.assumption.name` |
| Holding badge | `status.assumption.holding.*` |
| Under Review badge | `status.assumption.underReview.*` |
| Weakening badge | `status.assumption.weakening.*` |
| Weakening background | `surface.assumption.weakening` |
| Broken badge | `status.assumption.broken.*` |
| Broken background | `surface.assumption.broken` |
| Historical opacity | `text.historical.opacity` |

---

# 5. Evidence Summary

## Purpose

The Evidence Summary presents the data, sources, and references that support the reasoning. It is not the reasoning itself — it is the evidence that the reasoning draws from. It allows the user (and future reviewers) to trace where the reasoning comes from.

## Semantic Meaning

Evidence Summary communicates: here is what the reasoning is grounded in. These are the facts, sources, and data points from which the Supporting Factors and Conclusion are derived. Without this grounding, reasoning is assertion. With it, reasoning is traceable.

## When Used

- As a Section in Investment Workspace (the evidence base for the investment analysis)
- Attached to individual Supporting Factors as Supporting Metadata (inline evidence)
- Within the Decision Workspace when the Decision is evidence-driven
- In Historical Records to show what evidence supported the reasoning at the time

## When Not Used

- As a data dashboard (it is not a table of financial metrics — it is a curated summary of relevant evidence)
- As a primary Conclusion area
- As a replacement for narrative reasoning in Supporting Factors

## Relationship to Reasoning

Evidence provides the factual grounding for Supporting Factors and Challenges. The relationship is:
- A Supporting Factor may cite one or more Evidence items
- Evidence does not stand alone — it is always in service of a named piece of reasoning
- Evidence that does not connect to any Factor or Challenge should be reviewed for relevance

## Evidence Grouping

Evidence items may be grouped by:
- **Type:** Quantitative (data, metrics), Qualitative (analysis, reports, expert views), Historical (prior performance)
- **Source category:** Internal analysis, External research, Market data, Company filings

Grouping is optional. Default is ungrouped, presented in recency order.

## Source Representation

Each evidence item includes:
- **Source label:** Where the evidence comes from (source name, not a full URL)
- **Date:** When the evidence was recorded or published
- **Relevance note:** A brief statement of why this evidence is relevant to the reasoning

## Confidence Presentation

Evidence items do not carry confidence scores (no numbers, no gauges). Confidence in the evidence quality is communicated qualitatively through:
- Source type (primary source vs. secondary analysis)
- Recency (date shown prominently)
- User notation (a brief relevance note that may include a confidence qualifier: "Strong signal from primary source" or "Directional guidance only")

## Variants

**Inline Evidence** — A single evidence item attached to a Supporting Factor or Challenge. Displayed as a Supporting Metadata component (compact form).

**Evidence Section** — A full Section containing the complete evidence base for the Workspace. Multiple evidence items, optionally grouped.

**Historical Evidence** — Evidence as preserved in a Historical Record. Immutable, dated.

## Anatomy

```
EvidenceItem
├── SourceLabel [Role 5, medium weight]
├── Date [Role 5]
├── RelevanceNote [Role 5]
└── [Conditional] LinkedFactor [Role 5 — "Supports: [Factor Name]"]
```

## States

| State | Description |
|-------|-------------|
| Default | Evidence displayed in recency order |
| Outdated | Evidence date is older than a threshold (configurable); subtle label "Older reference" |
| Historical | Historical visual treatment; immutable |
| Loading | Skeleton placeholders |

## Interaction

**Add Evidence:** "+Add evidence" Section Action. Opens an evidence creation form: source label, date, relevance note, optional factor association.

**Link to Factor:** Each evidence item may be linked to one or more Supporting Factors or Challenges via the `LinkedFactor` field. The link is navigational — tapping it navigates to the associated Factor.

**No editing once historical.** Historical evidence items are immutable.

## Accessibility

- Evidence items: `<li>` in an `<ul>`.
- LinkedFactor: `<a>` with descriptive `aria-label`.
- Outdated label: `aria-label` includes the age message.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Source label color | `text.label.secondary` |
| Date color | `text.contextual` |
| Relevance note color | `text.body.secondary` |
| Historical opacity | `text.historical.opacity` |
| Outdated label color | `status.outdated.text` |

---

# 6. Opportunity Summary

## Purpose

The Opportunity Summary presents the specific investment opportunity that the current reasoning is examining. It frames the core thesis: what is the opportunity, why does it exist, and what makes it available now.

## Semantic Meaning

The Opportunity Summary communicates: here is the specific opportunity. Not the company background — the opportunity. The gap between current conditions and a more favorable future state that this investment is positioned to capture.

## When Used

- As a Section in Investment Workspace, positioned after context and before detailed Supporting Factors
- In the Decision Workspace, as the compressed opportunity statement that motivates the proposed action
- In the Historical Record as the opportunity as it was framed at the time of the Decision

## When Not Used

- As the Conclusion (the Conclusion is what the reasoning indicates; the Opportunity Summary is the investment thesis)
- As a Supporting Factor (the Opportunity Summary is the framing; Supporting Factors explain why the opportunity is real)

## Placement

In the Investment Workspace reading flow:
1. Primary Conclusion
2. What Changed
3. Investment Context (background)
4. **Opportunity Summary** ← here
5. Supporting Factors
6. Challenges

The Opportunity Summary is placed after context and before the detailed reasoning — it is the thesis statement that organizes the subsequent analysis.

## Relationship to Investment Reasoning

The Opportunity Summary motivates the following reasoning. Supporting Factors should explain why the opportunity is real and accessible. Challenges should address risks to capturing the opportunity. Assumptions should name the conditions on which the opportunity depends.

## Variants

**Standard Opportunity Summary**
A structured narrative: opportunity statement, why it exists, what window exists.

**Compressed Opportunity Summary**
A one-sentence version for display in Decision Workspace or Dashboard context. Derived from the Standard.

**Historical Opportunity Summary**
As preserved in a Historical Record. Immutable.

## Anatomy

```
OpportunitySummary [Section using SectionContainer]
├── SectionHeader ("Opportunity")
└── SectionBody
    ├── OpportunityStatement [Role 1 or Role 2 — compressed thesis]
    ├── WhyItExists [Role 3 — the conditions creating the opportunity]
    └── WindowStatement [Role 3 — why now / for how long]
```

## Interaction

The Opportunity Summary is editable in Investment Workspace and Decision Workspace. The same editing model as other reasoning sections — Long-Form Editor on focus, Atlas Suggestion after 1.5s pause. Historical variants are immutable.

## Historical Handling

Historical Opportunity Summaries preserve the opportunity framing as it was at the time — including the window statement ("why now"), which may be outdated. A "Historical Record — [date]" label above the statement makes the temporal context clear.

Reviewers can compare the historical opportunity framing with current conditions to evaluate whether the opportunity has been captured, is still available, or has closed.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Opportunity Statement color | `reasoning.opportunity.statement` |
| Why/Window text color | `text.body.primary` |
| Historical opacity | `text.historical.opacity` |

---

# 7. Opportunity Cost

## Purpose

The Opportunity Cost component makes explicit what is foregone by pursuing the current reasoning direction. It presents the chosen path and the alternatives not taken side by side, with an honest assessment of what the choice costs.

## Semantic Meaning

Opportunity Cost communicates: choosing this means not choosing that. What is given up has value. By naming it explicitly, the user is forced to confirm that the chosen path is worth its cost — not just good in isolation, but better than the foregone alternatives.

## When Used

- In the Decision Workspace, as a required component of the reasoning structure
- In the Portfolio Workspace, when the Decision has portfolio-level resource implications
- In Historical Records, as the preserved opportunity cost analysis from the time of the Decision

## When Not Used

- As a Comparison component (Comparison is for evaluating alternatives; Opportunity Cost is for naming what is foregone after a direction is chosen)
- For operational cost analysis (this is not a budget component)

## Comparison Philosophy

The Opportunity Cost is not a neutral comparison — it is a directed analysis. The "chosen path" is defined. The "alternatives foregone" are in relation to the chosen path. The component does not present the alternatives as equally valid; it presents them as the cost of the choice.

This is distinct from the Comparison component (Section 8), which presents options without a predetermined preferred choice.

## Alternative Representation

Each foregone alternative is represented with:
- **Alternative label:** What the alternative was
- **What it offered:** The primary value the alternative would have provided
- **Why not chosen:** A brief statement of why this alternative was not selected

The analysis does not need to be exhaustive. One to three key foregone alternatives is the expected range.

## Relationship to Conclusions

The Opportunity Cost reinforces the Conclusion by naming its price. A Conclusion that seems attractive in isolation may look different when the Opportunity Cost is named. If the Opportunity Cost appears very high relative to the Conclusion's projected value, that tension should surface as a Challenge.

## Variants

**Standard Opportunity Cost**
Chosen path (brief statement) + one to three foregone alternatives with explanations.

**Simple Opportunity Cost**
A single foregone alternative — the most important one — without the full structured comparison. Used in Decision Workspace when the opportunity cost is straightforward.

**Historical Opportunity Cost**
Preserved from a prior reasoning session. Immutable.

## Anatomy

```
OpportunityCost [SectionContainer]
├── SectionHeader ("Opportunity Cost")
└── SectionBody
    ├── ChosenPath [Frame]
    │   ├── Label [Role 4 — "Pursuing"]
    │   └── PathStatement [Role 3]
    ├── Divider (vertical or horizontal depending on layout)
    └── ForegoneAlternatives [Stack]
        └── [AlternativeItem × 1–3]

AlternativeItem
├── Label [Role 4 — "Instead of"]
├── AlternativeName [Role 3, medium weight]
├── WhatItOffered [Role 3]
└── WhyNotChosen [Role 5]
```

## Interaction

Editable in Decision Workspace and Portfolio Workspace. The ChosenPath is derived from the Proposed Decision but can be manually specified. AlternativeItems are user-authored.

**Add Alternative:** "+Add alternative" action. Maximum 3 alternatives.
**Remove Alternative:** Remove action on each AlternativeItem (with confirmation).

Historical Opportunity Cost is immutable.

## Historical Behavior

Historical Opportunity Cost shows what was foregone at the time of the Decision. In retrospect, some alternatives may have performed differently than expected. The Historical Opportunity Cost is not updated retrospectively — it preserves the reasoning as it was, providing an accurate record of the decision context.

## Accessibility

- ChosenPath and ForegoneAlternatives: structurally labeled (`aria-label`).
- AlternativeItem: `<li>` in a `<ul>`.
- Vertical Divider between sections: `aria-hidden="true"`.
- Screen reader reads: "Pursuing: [path statement]. Instead of: [alternative 1], [alternative 2]."

## Responsive Behavior

**Desktop:** Split Layout — ChosenPath left, ForegoneAlternatives right, vertical Divider between.
**Tablet:** Same split if width allows; stacked at narrower tablet widths.
**Mobile:** Stacked — ChosenPath above, ForegoneAlternatives below. Horizontal Divider.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Chosen path label | `reasoning.opportunityCost.chosen.label` |
| Chosen path statement | `reasoning.opportunityCost.chosen.statement` |
| Alternative label | `reasoning.opportunityCost.alternative.label` |
| Alternative name | `reasoning.opportunityCost.alternative.name` |
| What it offered | `text.body.secondary` |
| Why not chosen | `text.contextual` |
| Historical opacity | `text.historical.opacity` |

---

# 8. Comparison

## Purpose

The Comparison component presents two or more investment options, scenarios, or states side by side in a structured, parallel format. It enables direct, visual comparison without requiring the user to hold multiple information sets simultaneously.

## Semantic Meaning

Comparison communicates: these things are being evaluated against each other on defined criteria. Neither is predetermined as the preferred choice (contrast with Opportunity Cost, where a choice has been made). The Comparison is the evaluation before the choice.

## When Used

- In Investment Workspace for comparing an investment to alternatives or historical periods
- In Portfolio Workspace for comparing allocation states (current vs. proposed)
- In Decision Workspace for comparing before/after states or evaluating alternatives
- In Historical Records for comparing current and historical reasoning

## When Not Used

- For post-decision analysis of what was foregone (that is Opportunity Cost)
- For presenting a single option's attributes (that is a standard Reasoning Section)

## Comparison Types

**Before/After**
Current state versus proposed state. Two columns with shared row labels.
Row labels represent the dimensions of comparison (e.g., "Allocation", "Expected Return", "Risk Profile").

**Alternative Comparison**
Two or more mutually exclusive options. Each column is one option. Rows are shared evaluation criteria.

**Allocation Comparison**
Portfolio allocation before and after a Decision. Visual representations of each allocation state (via Allocation Comparison layout).

**Historical Comparison**
Current reasoning alongside Historical Record reasoning. Historical column uses historical visual treatment.

**Scenario Comparison**
Two or more potential outcome scenarios. Each column is one scenario. Rows are outcome dimensions.

## Ordering

For Before/After and Historical: the current or proposed state appears on the right. The prior or baseline state appears on the left. This is consistent with reading direction — from old to new.

For Alternative Comparison: the preferred option (if one is emerging from the reasoning) appears on the left. If no preference is established, ordering is user-determined.

## Relationship Visualization

When two comparison items have a specific relationship (e.g., "Option A is 40% cheaper but 30% less effective"), that relationship is expressed in a comparison note below the relevant row — a brief contextual statement that names the tradeoff.

## Variants

**Two-Column Comparison**
The standard form. Two options or states.

**Three-Column Comparison**
Three options or states. Used when a third alternative is genuinely distinct. Maximum three columns to preserve readability.

**Stacked Comparison (mobile)**
All comparison columns stack vertically. Row labels above each column's values.

## Anatomy

```
Comparison [SectionContainer]
├── SectionHeader ("Comparison" or specific label)
└── SectionBody [Split Layout]
    ├── ComparisonColumn [left]
    │   ├── ColumnHeader [Role 2 — option/state name]
    │   └── [ComparisonRow × n]
    ├── [ColumnDivider]
    └── ComparisonColumn [right]
        ├── ColumnHeader [Role 2]
        └── [ComparisonRow × n]

ComparisonRow
├── RowLabel [Role 5, left-aligned]
├── LeftValue [Role 3]
├── RightValue [Role 3]
└── [Conditional] ComparisonNote [Role 5 — relationship/tradeoff]
```

## Interaction

**Editing (in editable Workspaces):**
- ColumnHeaders are editable (user can rename the options)
- ComparisonRow values are editable
- Add Row: "+Add row" at the bottom
- Remove Row: Row-level remove action (hover)

**Historical Comparison interaction:** The historical column has no editing controls. Historical visual treatment. A "View full historical record" link navigates to the complete Historical Record.

## Accessibility

- Implemented as an `<table>` when the comparison is truly tabular (row/column data).
- ColumnHeaders: `<th scope="col">`.
- RowLabels: `<th scope="row">`.
- ComparisonNotes: additional row below the data row, spanning both columns, with `aria-label` describing the relationship.
- Historical column: `aria-label` on the `<th>` includes "Historical Record from [date]".
- On mobile (stacked): columns become sequential sections with headings; no table structure (tables do not stack semantically).

## Responsive Behavior

**Desktop and Tablet:** Side-by-side columns. Full anatomy.
**Mobile:** Stacked — each column becomes a subsection. First column (left/current) appears first; second column appears below.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Column header color | `text.heading.primary` |
| Row label color | `text.label.secondary` |
| Value color | `text.body.primary` |
| Comparison note color | `text.contextual` |
| Column divider | `border.comparison.column` |
| Historical column overlay | `surface.historical.background` |
| Historical opacity | `text.historical.opacity` |

---

# 9. Scenario Analysis

## Purpose

The Scenario Analysis component structures a set of potential outcomes under different conditions. It allows the user to reason about uncertainty explicitly — naming the scenarios, defining the conditions, and assessing the implications of each.

## Semantic Meaning

Scenario Analysis communicates: here are the plausible futures I am considering. Each scenario is a named, defined alternative to the base case. By analyzing them explicitly, I acknowledge that the future is uncertain and that my reasoning must account for multiple possibilities.

## When Used

- In the Decision Workspace when a decision must be evaluated against multiple possible outcomes
- In the Investment Workspace when the investment thesis depends on conditions that could go several ways
- In Historical Records when the prior reasoning included scenario analysis

## When Not Used

- As a substitute for the Conclusion (the Conclusion reflects the most probable scenario; Scenario Analysis supports it by making uncertainty explicit)
- For sensitivity analysis on numerical models (that is a data visualization, not a Reasoning Component)

## Scenario Grouping

Scenarios are organized in a defined structure:
- **Base Case:** The most probable scenario — the one the reasoning is primarily built on
- **Upside Case:** A more favorable scenario than the base
- **Downside Case:** A less favorable scenario than the base
- **Alternative Case(s):** Additional scenarios that are genuinely distinct from the above (optional, maximum 2)

Each scenario has:
- **Scenario Name:** The label for this potential future
- **Conditions:** The specific conditions that define this scenario
- **Implications:** What this scenario means for the investment/decision
- **Probability Estimate:** A qualitative probability (Likely / Possible / Unlikely) — not a numerical percentage

## Scenario Ordering

Base Case first, Upside second, Downside third, Alternative cases last. This ordering is fixed — it prevents the interface from leading with extreme cases that anchor reasoning inappropriately.

## Relationship to Conclusions

The Base Case should be consistent with the Conclusion. If the Base Case and the Conclusion diverge, that is a Contradiction worth surfacing.

The Upside and Downside cases bound the space of outcomes the user is considering — they should inform the Opportunity Cost and the Challenges (e.g., "Downside Case: revenue decline materially affects valuation" should appear as a Challenge if not already addressed).

## Variants

**Standard Scenario Analysis**
Base + Upside + Downside + optional alternatives. Full anatomy.

**Simple Scenario Analysis**
Base + one alternative. Two scenarios. Used when uncertainty can be expressed as a binary.

**Historical Scenario Analysis**
Preserved scenarios from a prior reasoning session. Immutable.

## Anatomy

```
ScenarioAnalysis [SectionContainer]
├── SectionHeader ("Scenario Analysis")
└── SectionBody
    └── [ScenarioItem × 2–5]

ScenarioItem
├── ScenarioType [Role 4 — "Base Case" / "Upside" / "Downside" / "Alternative"]
├── ScenarioName [Role 3, medium weight]
├── ProbabilityLabel [StatusBadge — "Likely" / "Possible" / "Unlikely"]
├── Conditions [Role 3 — the specific conditions]
└── Implications [Role 3 — what this means]
```

## Interaction

**Adding scenarios:** The Base, Upside, and Downside cases are always present (empty state until authored). Alternative cases are added via "+Add alternative scenario" (maximum 2 additional).

**Probability:** Selected from a compact inline control (three options: Likely / Possible / Unlikely). Not a free-text field.

**Historical:** Immutable. Probability labels preserved from time of recording.

## Historical Behavior

Historical Scenario Analysis preserves the scenarios as they were framed at the time. In hindsight, which scenario played out becomes clear — but the historical record shows the uncertainty as it existed at decision time. This is valuable for reviewing decision quality.

## Accessibility

- ScenarioItems: `<section>` elements within the Section Body, labeled by ScenarioType.
- ProbabilityLabel: StatusBadge with text communicating the probability qualitatively.
- Probability selector: an accessible inline control (e.g., radio group).

## Responsive Behavior

**Desktop and Tablet:** Scenarios stacked vertically. Full anatomy for each.
**Mobile:** Same vertical stack. Conditions and Implications may be expandable (collapsed by default) to reduce initial screen length.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Scenario type label | `text.label.secondary` |
| Scenario name color | `reasoning.scenario.name` |
| Conditions color | `text.body.primary` |
| Implications color | `text.body.secondary` |
| Likely badge | `status.scenario.likely.*` |
| Possible badge | `status.scenario.possible.*` |
| Unlikely badge | `status.scenario.unlikely.*` |
| Historical opacity | `text.historical.opacity` |

---

# 10. Proposed Decision Candidate Content

## Purpose

Proposed Decision Candidate Content is an Atlas-generated or user-authored statement of what action or direction the reasoning suggests. It bridges the Conclusion (what the reasoning indicates) and the Decision (the user's commitment). Candidate content is not a Decision — it is a suggestion that the user evaluates and either adopts, modifies, or rejects.

## Semantic Meaning

Candidate content communicates: based on this reasoning, the suggested course of action is X. It is directional, not binding. The user may accept, modify, or decline candidate content. The Decision is always the user's own.

## When Used

- As an Atlas-generated component that surfaces when analysis supports a specific direction
- As a user-authored statement of their current intent before formalizing the Decision
- In the Investment Workspace to capture the investment candidate content before a Decision is formally initiated

## When Not Used

- As a Conclusion substitute. The Conclusion is the current state of the reasoning; candidate content is the suggested action that follows from it.
- As a Decision. Candidate content has no permanence — it is a working suggestion.
- In Historical Records as an independent component (candidate content at decision time is captured in the Decision itself).

## Relationship to Reasoning

Candidate content should follow logically from the Conclusion and the weighted balance of Supporting Factors and Challenges. If candidate content appears to contradict the Challenges, Atlas surfaces this as a Contradiction.

## Relationship to Conclusions

Candidate content is directionally derived from the Conclusion. The Conclusion is what is believed; candidate content is what that belief implies for action. They should be consistent — a Conclusion that an investment represents a strong opportunity should produce candidate content to invest, not to pass.

## Relationship to Decisions

Candidate content is the input to the Decision. When the user is ready to formalize a Decision, the candidate content flows into the Proposed Decision field. The user may accept the candidate content as-is or modify it.

## Variants

**Atlas-Generated Candidate Content**
Atlas-generated. Appears with Atlas attribution. The user can accept (flows to Proposed Decision), modify (user edits, attribution updates), or decline (dismissed for session).

**User-Authored Candidate Content**
User-authored. The user has decided their working intent before formalizing. Used in Investment Workspace when the user wants to capture a working intent.

**Portfolio Recommendation**
A portfolio-level recommendation from the Portfolio Workspace — what the portfolio analysis recommends for the composition.

## Anatomy

```
CandidateContent
├── SourceLabel [Role 4 — "Atlas suggested" or "Working intent"]
├── RecommendationStatement [Role 2 — the candidate action]
├── PrimaryReason [Role 3 — the key reason for this candidate content]
└── RecommendationActions
    ├── AcceptAction [→ flows to Proposed Decision]
    ├── ModifyAction [→ enters editing state]
    └── DeclineAction [→ dismissed for session]
```

## Properties

| Property | Type | Default | Required |
|----------|------|---------|----------|
| `source` | `'atlas' \| 'user'` | `'atlas'` | Yes |
| `statement` | string | — | Yes |
| `primaryReason` | string | — | Yes |
| `isEditable` | boolean | `true` | No |
| `isDismissed` | boolean | `false` | No |

## Interaction

**Atlas-Generated Candidate Content:**
- Accept: `RecommendationStatement` and `PrimaryReason` flow to the Proposed Decision Section. The candidate content transitions to "Accepted" state (soft success state with "Moved to Proposed Decision" label).
- Modify: Statement enters Long-Form Editor mode. On save, attribution updates to "User modified".
- Decline: Dismissed for the session. Not shown again in the current session.
- Structural Undo: 5-second window after Accept to undo the acceptance.

**User-Authored Candidate Content:**
Editing model — same as other editable Reasoning Components. No Accept/Decline actions.

## Historical Persistence

Candidate content that leads to a recorded Decision is preserved in the Decision's Historical Record as the attribution context. The candidate content itself does not appear as a standalone Historical component — its content is absorbed into the Decision.

## Accessibility

- SourceLabel: `aria-label` on the component: "Candidate content from Atlas" or "Your working intent".
- Statement: `<h4>` or appropriate heading level.
- Accept/Modify/Decline: explicit `<button>` labels ("Accept candidate content", "Modify candidate content", "Decline candidate content").
- Dismissed state: announced via `aria-live="polite"` ("Candidate content dismissed").
- Accepted state: announced via `aria-live="polite"` ("Candidate content moved to Proposed Decision").

## Responsive Behavior

**Desktop and Tablet:** Full anatomy. Actions right-aligned or below the statement.
**Mobile:** Statement full-width. Actions stacked below. Full-width buttons.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Source label (Atlas) | `text.attribution.atlas` |
| Source label (User) | `text.label.secondary` |
| Recommendation statement | `reasoning.recommendation.statement` |
| Primary reason | `text.body.primary` |
| Accept action | `action.primary.*` |
| Modify action | `action.secondary.*` |
| Decline action | `text.action.dismiss` |

---

# 11. Reasoning Block

## Purpose

The Reasoning Block is a reusable structural unit for containing a discrete piece of reasoning that does not fit one of the named Reasoning Components (Conclusion, Supporting Factors, etc.). It provides consistent structure — a named header, content body, and optional metadata — for reasoning content that is context-specific to a particular Workspace.

## Semantic Meaning

A Reasoning Block communicates: here is a named piece of reasoning. It is structured (it has a name and a body) but its content is not constrained to one of the predefined reasoning types.

## When Used

- For reasoning content that is specific to a Workspace's requirements but does not have a dedicated component
- For grouping related reasoning content that should be navigable as a unit
- As an extensibility point: new Workspaces that require new reasoning structures can use Reasoning Blocks until the pattern justifies a dedicated component

## When Not Used

- As a substitute for a named Reasoning Component. If Supporting Factors, Challenges, Assumptions, or another named component fits the content, use the named component.
- As a generic container for layout. Use Layout Containers for spatial organization; Reasoning Blocks are for named reasoning content.

## Hierarchy

Reasoning Blocks occupy a secondary position in the reasoning hierarchy — below the Conclusion and named Reasoning Components, but above metadata and supporting references.

## Composition

A Reasoning Block may contain:
- Narrative text (Long-Form Editor or read-only)
- Supporting Metadata
- Nested Reasoning Blocks (maximum one level of nesting)
- Other named Reasoning Components as sub-elements (e.g., a Reasoning Block containing a compact Comparison)

## Nested Reasoning

A Reasoning Block may contain another Reasoning Block (maximum one level of nesting). This allows for a two-level reasoning structure: a named topic area containing named sub-areas.

Example: A "Valuation Context" Reasoning Block containing a "Historical Multiples" sub-block and a "Peer Comparison" sub-block.

## Expandable Behavior

Same as Section Container — the full Reasoning Block heading row is the expansion target. Collapsed state shows the block name and a one-line summary.

## Variants

**Standard Reasoning Block**
Named header, narrative content body. Expandable.

**Compact Reasoning Block**
A non-expandable Reasoning Block. Always visible, less vertical space. Used for brief supporting observations.

**Historical Reasoning Block**
Historical visual treatment. Immutable.

## Anatomy

```
ReasoningBlock [SectionContainer (reduced visual weight)]
├── SectionHeader [with expansion control]
│   ├── BlockName [Role 3, medium weight — less prominent than Section Header]
│   └── [Conditional] BlockSummary [Role 5, visible when collapsed]
└── BlockBody
    └── [Content]
```

## States

Same as Section Container: Expanded, Collapsed, Updated, Draft, Historical, Empty, Loading.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Block name color | `reasoning.block.name` |
| Block summary color | `text.contextual` |
| Block background | `surface.primary.background` |
| Block border | `border.reasoning.block` |
| Historical opacity | `text.historical.opacity` |

---

# 12. Context Panel

## Purpose

The Context Panel presents supporting contextual information that is relevant to the current reasoning but is not itself part of the reasoning chain. It is supplementary — it provides the user with background, definitions, or references without cluttering the primary reasoning flow.

## Semantic Meaning

A Context Panel communicates: here is relevant context that supports your reasoning. It is not a conclusion, a factor, or an assumption. It is background.

## When Used

- For investment background information (company history, market context) in the Investment Workspace
- For portfolio context in the Portfolio Workspace
- For definition panels (what is this investment type?) when a concept requires clarification
- For cross-references to related Workspaces or records

## When Not Used

- For reasoning content that belongs in Supporting Factors, Conclusions, or other named components
- As a persistent sidebar (the Context Panel is contextual — it appears when relevant and can be collapsed)

## Context Hierarchy

Context Panels are Level 5 in the information hierarchy — subordinate to the reasoning content they support. Their typography is Role 5 (Contextual Text), never Role 1–2.

## Associated Reasoning

A Context Panel may be explicitly associated with a specific Reasoning Component (e.g., a Context Panel providing company background associated with the Opportunity Summary). This association is represented through positioning (the Context Panel appears near the associated component) and an optional relationship indicator.

## Cross References

A Context Panel may contain links to:
- Related Workspaces (e.g., the Portfolio Workspace for the current holding)
- Historical Records (prior reasoning sessions for this investment)
- External references (source documents)

Cross-reference links use Role 5 typography in `text.action.navigation` color. They do not open in new tabs — they navigate within Atlas.

## Historical Context

When a Context Panel is displayed within a Historical Record, it shows the contextual information as it was at the time of the session. Historical cross-references link to historical versions of referenced records.

## Variants

**Inline Context Panel**
Appears within the Workspace body flow, collapsible. Used for investment background and market context.

**Companion Context Panel**
Appears adjacent to a specific Reasoning Component (positioned to the right on desktop, or below on mobile). Not part of the main reading flow.

**Reference Panel**
A compact list of cross-references. No narrative content — links only.

## Anatomy

```
ContextPanel
├── PanelHeader [Role 4 — panel name]
├── PanelBody [Role 5 — narrative context]
└── [Conditional] CrossReferences [list of reference links]
```

## Interaction

**Inline Context Panel:** Collapsible (same model as Section Container). Collapsed by default in Decision Workspace (where reasoning depth is more important than context). Expanded by default in Investment Workspace.

**Companion Context Panel:** Fixed beside the associated component. Dismissed with a close control. Does not collapse — it appears or is dismissed.

**Reference Panel:** Non-collapsible. Always visible when present.

## Accessibility

- Panel: `<aside aria-label="[Panel Name]">`. The `<aside>` landmark communicates that this is supplementary content.
- Cross-reference links: `<a>` elements with descriptive labels.
- Associated reasoning: `aria-describedby` on the associated Reasoning Component pointing to the Context Panel `id`.

## Responsive Behavior

**Desktop:** Inline panels in the reading flow; Companion panels may appear to the right.
**Tablet:** Companion panels move to below the associated component.
**Mobile:** All Context Panels appear in the main reading flow. Companion panels become Inline panels.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Panel header | `text.label.secondary` |
| Panel body | `text.contextual` |
| Cross-reference links | `text.action.navigation` |
| Panel background | `surface.elevated.background` |
| Panel border | `border.contextPanel` |

---

# 13. Supporting Metadata

## Purpose

Supporting Metadata presents the reference information that accompanies a Reasoning Component — sources, timestamps, authorship, confidence qualifiers, and version information. It is subordinate to the reasoning content it supports and is always presented in a visually quiet form.

## Semantic Meaning

Supporting Metadata communicates: here is the provenance of this reasoning. Where did it come from, when was it created or modified, and by whom? Metadata gives the reasoning a traceable history without dominating its presentation.

## When Used

- Attached to Evidence Items (source and date)
- Attached to Supporting Factors and Challenges (source of the claim)
- As the attribution line on Atlas-generated content
- As the timestamp and lock indicator on Historical content
- Within the Final Decision Card (see UX-013C) as the provenance record

## When Not Used

- As primary content. Metadata is always secondary to the reasoning it supports.
- For content that belongs in a Conclusion or Reasoning Component (don't demote reasoning to metadata).

## Displayed Metadata

The following metadata types may appear in a Supporting Metadata component:

**Source** — Where this information comes from (source name, abbreviated).
**Date** — When this information was recorded or published. Always shown for Historical content.
**Author** — Who authored this content. "You" for user-authored, "Atlas" for Atlas-generated.
**Confidence** — A qualitative confidence qualifier ("Strong signal from primary source" / "Directional guidance" / "Speculative"). Never a number or gauge.
**Version** — For components that have been amended (e.g., "Amended 2024-03-15"). Shows the amendment count if more than one.
**Relationship** — A named relationship to another record ("Amends decision from [date]" / "Related to [investment]").

## Ordering

When multiple metadata items appear together: Date → Author → Source → Confidence → Version → Relationship. This ordering reflects the most frequently needed information first.

## Visibility

Supporting Metadata is always visually quiet — Role 5 typography, `text.contextual` color. It is present but not dominant. It does not compete with the reasoning content it supports.

On compact or collapsed views, metadata may be reduced to a single line (the single most important item — typically Date for historical content, Author for attribution).

## Historical Handling

Historical Supporting Metadata has one additional required field: the Historical lock indicator (a lock icon or "Historical" label). This communicates that the metadata — and the content it supports — cannot be modified.

All Historical content's Supporting Metadata is displayed with the `text.historical.opacity` treatment.

## Variants

**Inline Metadata**
One to three metadata items on a single line, separated by "·" or equivalent light separator. Used adjacent to FactorItems, Conclusions, and other reasoning components.

**Expanded Metadata**
All relevant metadata items in a stacked block. Used at the bottom of completed Section Containers or Historical Records.

**Historical Metadata**
Same as Inline or Expanded, with historical visual treatment and the lock indicator.

## Anatomy

```
SupportingMetadata [Frame, Auto Layout, horizontal or vertical]
├── [Conditional] LockIndicator [icon, aria-label="Historical — cannot be edited"]
├── DateLabel [Role 5 — "[date]"]
├── AuthorLabel [Role 5 — "You" / "Atlas"]
├── SourceLabel [Role 5 — source name]
├── ConfidenceLabel [Role 5 — qualifier]
├── VersionLabel [Role 5 — "v[n]" or "Amended [date]"]
└── RelationshipLabel [Role 5, link — "Amends [reference]"]
```

## Responsive Behavior

**Desktop and Tablet:** Inline form when space allows. Expanded form below Sections.
**Mobile:** Single most important item inline. "More" link to expanded form.

## Accessibility

- Metadata is `<footer>` within its parent component (for a long reasoning block).
- Or `<p>` with `role="note"` for inline metadata.
- Lock indicator: `aria-label="Historical — this content cannot be edited"`.
- RelationshipLabel: `<a>` with descriptive `aria-label`.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| All metadata text | `text.contextual` |
| Historical metadata text | `text.contextual` at `text.historical.opacity` |
| Lock indicator color | `status.historical.text` |
| Separator color | `text.muted` |
| Relationship link | `text.action.navigation` |

## Engineering Mapping

Supporting Metadata is typically implemented as a composable group of atomic metadata elements (DateLabel, AuthorLabel, etc.) rather than a single component that receives all metadata as props. This allows consumers to include only the metadata types relevant to their context.

---

# 14. Reasoning Relationships

## Overview

Reasoning Components do not exist in isolation. They form a structured dependency graph in which each component's content is informed by, and may affect, other components. This section defines those relationships explicitly.

## The Reasoning Dependency Chain

```
Conclusion
  ↓ (informed by)
Supporting Factors + Challenges + Assumptions
  ↓ (grounded in)
Evidence Summary
  ↓ (frames context for)
Opportunity Summary
  ↓ (made explicit by)
Opportunity Cost
  ↓ (considered alongside)
Scenario Analysis + Comparison
  ↓ (synthesized into)
Candidate Content
  ↓ (formalized as)
Decision [UX-013C]
```

## Dependencies

**Conclusion ← Supporting Factors, Challenges, Assumptions**
The Conclusion should be consistent with the balance of Supporting Factors and Challenges. If Challenges materially outweigh Supporting Factors, or if a key Assumption breaks, the Conclusion may need revision. This dependency is logical (not enforced programmatically) but is surfaced by Atlas analysis as a Contradiction when a significant inconsistency is detected.

**Supporting Factors ← Assumptions**
A Supporting Factor may be dependent on one or more Assumptions. When an Assumption's status changes to Broken, dependent Factors automatically enter the Invalidated state, and the dependency relationship surfaces a Contradiction in the Challenges section.

**Challenges ← Assumptions**
A Broken Assumption automatically generates a Challenge of severity determined by the Assumption's monitored significance. The Challenge references the Broken Assumption.

**Opportunity Cost ← Conclusion + Candidate Content**
The Opportunity Cost names what is foregone by the chosen direction. It is directionally informed by the Conclusion and the candidate content — the chosen path in the Opportunity Cost should match the direction indicated by those components.

**Scenario Analysis ← Supporting Factors + Challenges**
Each scenario in the Scenario Analysis should be grounded in the Supporting Factors and Challenges. The Base Case should reflect the balance of Supporting and Challenge evidence. Upside and Downside cases should be derivable from specific Supporting Factors or Challenges.

**Candidate Content ← Conclusion + Supporting Factors + Challenges**
The candidate content follows from the Conclusion. It should be challenged if it is inconsistent with the Challenges or if the Supporting Factors do not appear to support the direction indicated by the candidate content.

## Ordering

The Reasoning Components appear in a defined sequence within each Workspace. The sequence is not arbitrary — it reflects the reading order that produces the most coherent reasoning arc:

**Decision Workspace sequence:**
1. Current Conclusion
2. Decision Required (UX-013C)
4. Supporting Factors
5. Challenges
6. Assumptions
7. Opportunity Cost
8. Portfolio Consequences (UX-013C)
9. Scenario Analysis (conditional)
10. Comparison (conditional)
12. Implementation (UX-013C)
13. Review Conditions (UX-013C)

**Investment Workspace sequence:**
1. Primary Conclusion
2. What Changed
3. Investment Context (Reasoning Block)
4. Opportunity Summary
5. Supporting Factors
6. Challenges
7. Assumptions
8. Evidence Summary
9. Candidate Content (conditional)

## Composition

Reasoning Components are composed within Section Containers. Each named component is its own Section. The Section Container's expansion behavior is governed by the component's states (Contradictions expand the Section; Atlas Warnings at Material/Blocking severity expand the Section).

## Inheritance

Reasoning Components do not inherit from each other in the component architecture sense. They share the visual language (typography roles, spacing levels, token references) defined in the Atlas Design System.

What propagates between components is state, not structure. A Broken Assumption propagates its effect to dependent Factors (Invalidated state) and the Challenges section (new Contradiction). This propagation is application-layer logic, not component-layer inheritance.

## Navigation

Cross-component navigation is provided by RelationshipIndicators within components that reference other components. These are inline links that scroll the referenced component into view and briefly apply the Highlight motion token to it (one pulse, then settled).

Screen reader navigation: users navigating by heading can move through Reasoning Components by their Section headings. Users navigating by ARIA landmark can reach the entire reasoning body through the `<main>` landmark.

---

# 15. Reasoning States

## Shared States Across All Reasoning Components

These states apply to every Reasoning Component. Their visual treatments are defined here and applied consistently.

| State | Semantic Meaning | Visual Treatment | Interaction | Accessibility |
|-------|-----------------|-----------------|-------------|--------------|
| **Draft** | Content exists but has not been saved in the current session | Draft Indicator in Section Header; content in Unsaved token state | Editable | `aria-label` includes "Draft" |
| **Accepted** | Atlas-suggested content has been accepted by the user | Attribution label updates to "Atlas generated / User accepted"; editing enabled | Editable | Attribution announced via `aria-live` |
| **Updated** | Content has changed since the user's last session | Update motion token fires once on render; StatusBadge "Updated" in Section Header settles after interaction | Normal editing | StatusBadge announced via `aria-live="polite"` |
| **Historical** | Content is from a prior recorded session | `text.historical.opacity` applied to all text; lock indicator present; all editing disabled; Historical label + date | No interaction | All ARIA labels include "Historical Record from [date]" |
| **Monitoring** | An Assumption with this content has an active Monitoring Condition | Compact monitoring status indicator attached to the component | Links to Monitoring Condition | `aria-label` includes "Monitored" and current monitoring status |
| **Superseded** | This reasoning has been explicitly replaced by newer reasoning | "Superseded" Status Badge; reduced opacity (not as low as Historical); link to successor reasoning | Read-only, not immutable | `aria-label` includes "Superseded by: [successor]" |
| **Collapsed** | Section is collapsed; only header and summary visible | Section Header with summary; SectionBody `display: none` | Full header row is expand target | `aria-expanded="false"` on header |
| **Expanded** | Section is fully visible | Full Section Body shown; collapse control visible | Full header row is collapse target | `aria-expanded="true"` on header |
| **Focused** | Component has keyboard focus for navigation | Focus ring (`:focus-visible`) on the focused interactive element | Standard keyboard navigation | Focus ring communicates focus |
| **Loading** | Content is being fetched | Skeleton placeholders at component scale; Loading motion token | No interaction while loading | `aria-busy="true"` on Section; skeleton has `aria-hidden="true"` |

## State Precedence

When multiple states apply to the same component:
1. Historical (highest — overrides all editing and most visual states)
2. Loading (no content visible; skeleton shown)
3. Superseded
4. Monitoring + Updated (both may be shown simultaneously)
5. Draft + Accepted (mutually exclusive)
6. Expanded / Collapsed (always present, independent of other states)
7. Focused (layered on top of any other state)

## State Transitions

**Draft → Saved:** On autosave (30s interval or on blur from editing). Draft Indicator transitions from "Draft" to brief "Saved" label, then reverts to invisible (no indicator when content is current).

**Atlas-suggested → Accepted:** On user accepting an Atlas Suggestion. Attribution updates. Content enters editable state.

**Assumption Holding → Broken:** User-initiated via status selector, or triggered by a Monitoring Condition. Propagates to Invalidated state on dependent Factors, surfaces Contradiction in Challenges.

**Current → Historical:** On Workspace completion (Decision recording). Entire Workspace converts. All components simultaneously enter Historical state.

---

# 16. Reasoning Accessibility

This specification applies to all Reasoning Components. Individual component accessibility rules are defined in their respective sections above. This section establishes the shared accessibility model.

## Keyboard Navigation

**Tab order within the Reasoning body:** Follows the reasoning sequence (Section 14). Each Section Container's heading is a tab stop. Interactive elements within each Section are reachable by Tab after entering the Section.

**Within a collapsed Section:** Tab reaches the Section Header (as a single tab stop). Tab does not enter the Section Body when collapsed.

**Within an expanded Section:** Tab moves through all interactive elements in reading order: Section Header (expansion control), then each interactive element in the Section Body, then the Section's Section Actions.

**Between components within a Section:** Tab moves through all interactive elements. Arrow keys are used for list navigation within Supporting Factors, Challenges, and Assumptions lists.

**Cross-component links (RelationshipIndicators):** Tab reaches each RelationshipIndicator link. Activation scrolls and highlights the target component.

## Focus Behavior

**Never lose focus.** If a Reasoning Component is removed from the DOM (e.g., a Factor is deleted), focus moves to the next interactive element — typically the "Add factor" action or the Section Header.

**Automatic expansion on focus:** When keyboard focus reaches a collapsed Section that contains the user's current editing context (returned from navigation), the Section expands and focus moves to the previously focused element within it.

**Atlas Suggestion appearance:** When an Atlas Suggestion appears (1.5s pause), it does not steal focus. Focus remains on the editing field. The Suggestion is announced via `aria-live="polite"`.

## Reading Order

The reading order for screen readers follows the visual reading flow:
1. Workspace Header (`<header>`)
2. Navigation Bar (`<nav>`)
3. Main content (`<main>`) — Reasoning Components in sequence
4. Workspace Footer (`<footer>`)

Within the main content, Reasoning Components appear in the sequence defined in Section 14. Each Section is a `<section>` with `aria-labelledby` pointing to its heading.

## Screen Readers

**State announcements:**
- Draft state: "Section name: Draft" — announced when the Section enters Draft state.
- Updated state: "Section name has been updated since your last session" — announced on render.
- Historical state: "Historical Record from [date]: Section name" — part of the Section's ARIA label.
- Monitoring state: "Monitored — [condition name] is [status]" — announced on status change.
- Atlas Suggestion: "Atlas has a suggestion for [Section name]" — announced via `aria-live="polite"`.
- Blocking Challenge acknowledged: "Blocking challenge acknowledged. Completion is now available." — `aria-live="assertive"`.

**Relationship indicators:** Read as "[Component name] is related to [target component name]" and are navigational links.

## Touch Interaction

**All minimum touch targets:** 44×44px.
**List reorder:** Tap to select, tap arrow buttons to move, tap "Done" to confirm. No drag required.
**Expansion:** Entire Section Header row is the touch target.
**Inline editing:** Long tap (long-press) on read-only content opens the edit option on touch devices. A persistent edit icon is also present.

## Reduced Motion

All Reasoning Component animations use the twelve defined motion tokens, each with a reduced-motion fallback:
- Expand/Collapse: instant height change
- Insert/Remove (list items): instant appear/disappear
- Highlight (cross-component navigation): no pulse; instead, a persistent "focused" background state that clears after 2 seconds
- Update: no animation; state change is immediate
- Loading skeleton: static (no shimmer)

## High Contrast

All Reasoning Components:
- Status communicates via text labels, not color alone
- Borders use `border` CSS property (respected in Windows High Contrast Mode)
- Focus rings use `outline` (respected in High Contrast Mode), not `box-shadow`

## Zoom Behavior

At 200% browser zoom:
- All Reasoning Component text reflows within the available width
- No content is clipped
- Section Headers remain functional (expansion target remains accessible)
- Inline Metadata wraps gracefully (may require multiple lines)

---

# 17. Reasoning Token Mapping

A consolidated mapping of all Reasoning Components to the Atlas semantic token system.

## Typography Tokens

| Token | Applies To |
|-------|-----------|
| `typography.role1.*` | Conclusion Statement, Opportunity Statement (primary), Recommendation Statement |
| `typography.role2.*` | Comparison Column Headers, Scenario Names, Supporting Factors / Challenges Group Headers |
| `typography.role3.*` | Factor/Challenge/Assumption explanations; Opportunity/Scenario/Candidate-Content narrative text |
| `typography.role4.*` | Section variant labels, Group Headers, Opportunity Panel labels |
| `typography.role5.*` | Supporting Metadata, Evidence dates/sources, Relationship links, Summary text |

## Spacing Tokens

| Token | Applies To |
|-------|-----------|
| `spacing.pause1` | After Conclusion, before first Reasoning Section |
| `spacing.level1` | Between component name and explanation (Factor Name → Explanation) |
| `spacing.level2` | Between explanation and metadata |
| `spacing.level3` | Between items within a Reasoning list |
| `spacing.level4` | Between Sections (already defined in Foundation) |

## Semantic Color Tokens

| Token Group | Applies To |
|-------------|-----------|
| `conclusion.text.*` | Conclusion Statement, sub-statement |
| `reasoning.factor.name` | Supporting Factor name |
| `reasoning.challenge.name` | Challenge name |
| `reasoning.assumption.name` | Assumption name |
| `reasoning.opportunity.statement` | Opportunity Summary statement |
| `reasoning.opportunityCost.*` | Opportunity Cost chosen/alternative labels and text |
| `reasoning.scenario.name` | Scenario Analysis scenario names |
| `reasoning.recommendation.statement` | Recommendation statement |
| `reasoning.block.name` | Reasoning Block name |
| `text.attribution.atlas` | Atlas attribution labels |
| `text.body.primary` | Primary narrative body text in reasoning |
| `text.body.secondary` | Secondary/supporting body text |
| `text.contextual` | Supporting Metadata, Evidence, context text |

## Surface Tokens

| Token | Applies To |
|-------|-----------|
| `surface.challenge.material` | Material Challenge background tint |
| `surface.challenge.blocking` | Blocking Challenge background tint |
| `surface.assumption.weakening` | Weakening Assumption background tint |
| `surface.assumption.broken` | Broken Assumption background tint |
| `surface.elevated.background` | Context Panel, candidate content panel |
| `surface.historical.background` | Historical variants of all Reasoning Components |

## Border Tokens

| Token | Applies To |
|-------|-----------|
| `border.challenge.informational` | Informational Challenge left border |
| `border.challenge.material` | Material Challenge left border |
| `border.challenge.blocking` | Blocking Challenge left border |
| `border.factor.weakening` | Weakening Supporting Factor left border |
| `border.factor.invalidated` | Invalidated Supporting Factor left border |
| `border.comparison.column` | Divider between comparison columns |
| `border.reasoning.block` | Reasoning Block border |
| `border.contextPanel` | Context Panel border |

## State Tokens

| Token Group | Applies To |
|-------------|-----------|
| `status.assumption.*` | All four Assumption status states |
| `status.scenario.*` | Likely/Possible/Unlikely probability labels |
| `status.updated.*` | Updated state across all components |
| `status.acknowledged.*` | Acknowledged state on Material/Blocking Challenges |
| `status.historical.*` | Historical state across all components |
| `status.outdated.*` | Outdated Evidence label |

## Motion Tokens

| Token | Applied By |
|-------|-----------|
| `motion.highlight` | Cross-component navigation target highlight |
| `motion.insert` | New Factor/Challenge/Assumption item addition |
| `motion.remove` | Factor/Challenge/Assumption removal |
| `motion.update` | Content updated since last session |
| `motion.expand` / `motion.collapse` | Section expansion/collapse |
| `motion.fade` | Dismissed Atlas Suggestion fade-out |
| `motion.loading` | Skeleton loading states |

## Interaction Tokens

| Token | Applies To |
|-------|-----------|
| `interaction.hover.background` | Hoverable Reasoning Component areas |
| `text.action.secondary` | Edit/Remove/Acknowledge actions within components |
| `text.action.navigation` | Cross-reference and relationship links |
| `text.action.dismiss` | Dismiss actions on Atlas Suggestions |

---

# 18. Reasoning Engineering Mapping

## Recommended Component Hierarchy

```
Reasoning/
├── Core/
│   ├── Conclusion
│   ├── SupportingFactors
│   │   ├── SupportingFactorsContainer
│   │   ├── FactorItem
│   │   └── FactorGroup
│   ├── Challenges
│   │   ├── ChallengesContainer
│   │   ├── ChallengeItem
│   │   └── ChallengeGroup
│   └── Assumptions
│       ├── AssumptionsContainer
│       ├── AssumptionItem
│       └── AssumptionStatusSelector
├── Analysis/
│   ├── EvidenceSummary
│   │   └── EvidenceItem
│   ├── OpportunitySummary
│   ├── OpportunityCost
│   │   └── AlternativeItem
│   ├── Comparison
│   │   ├── ComparisonContainer
│   │   ├── ComparisonColumn
│   │   └── ComparisonRow
│   └── ScenarioAnalysis
│       └── ScenarioItem
├── Synthesis/
│   └── CandidateContent
├── Structure/
│   ├── ReasoningBlock
│   └── ContextPanel
└── Metadata/
    └── SupportingMetadata
        ├── DateLabel
        ├── AuthorLabel
        ├── SourceLabel
        ├── ConfidenceLabel
        ├── VersionLabel
        └── RelationshipLabel
```

## Naming Conventions

Component names: PascalCase, matching specification names.
Props: camelCase.
State: `data-state="[state-name]"` attribute (e.g., `data-state="material-unacknowledged"`).
Status: passed as props (e.g., `severity="blocking"`, `status="broken"`).

## Props

**Universal Reasoning Component props:**
- `isEditable?: boolean` — Whether this component allows editing in the current context.
- `isHistorical?: boolean` — Whether this component is in Historical mode.
- `historicalDate?: Date` — Required when `isHistorical` is true.
- `isAtlasGenerated?: boolean` — Whether the primary content was Atlas-generated.
- `isUserModified?: boolean` — Whether the user has modified Atlas-generated content.
- `onEdit?: () => void` — Callback when editing is initiated.
- `onSave?: (content: ContentType) => Promise<void>` — Autosave callback.
- `data-testid?: string` — Testing selector.

## Composition

Reasoning Components are composed within Foundation Component Section Containers. The application layer composes the full Workspace by nesting Reasoning Components within Section Containers in the defined sequence.

Reasoning Components do not compose each other directly (a FactorItem does not contain a ChallengeItem). Cross-component relationships are expressed through IDs (`contradictsId`, `dependedOnBy`) and are resolved at the application layer.

## Inheritance

Reasoning Components share a base component interface (`ReasoningComponentBase`) that provides:
- `isEditable`, `isHistorical`, `historicalDate`, `isAtlasGenerated`, `isUserModified`
- Standard editing lifecycle callbacks (`onEdit`, `onSave`)
- Standard ARIA props (`aria-label`, `id`)

Individual components extend this base interface with their specific props.

## State Handling

**Application-owned state:** Content values (factor names, explanations, assumption statuses, scenario definitions). These are persisted to the server.

**Component-owned state:** Editing state (whether a specific item is in editing mode), collapse/expand state (session-persistent), Atlas Suggestion visibility.

**Derived state:** Weakening/Invalidated Factor states (derived from Assumption status changes). Contradiction entries in Challenges (derived from Assumption status and dependency relationships). These are computed at the application layer and passed as props to the affected components.

## Serialization Expectations

Reasoning Component content is serialized as structured JSON, not as HTML or Markdown. This enables:
- Re-rendering with consistent visual treatment
- Querying specific reasoning elements (e.g., "all Assumptions with status Broken")
- Historical preservation with structured data (not just rendered HTML)
- Atlas analysis of structured reasoning content

**Factor serialization example:**
```json
{
  "id": "factor-001",
  "name": "Strong recurring revenue base",
  "explanation": "...",
  "weight": "strong",
  "isAtlasGenerated": false,
  "evidence": [...],
  "dependedOnByAssumptionId": null
}
```

## Testing Expectations

Every Reasoning Component must have:
- **Structural tests:** Correct HTML elements, ARIA attributes, landmark roles.
- **State tests:** Every state variant renders correctly. State transitions are covered (e.g., Assumption Holding → Broken triggers correct downstream state changes).
- **Interaction tests:** Keyboard navigation, expansion/collapse, editing initiation/save/cancel, Atlas Suggestion accept/dismiss.
- **Relationship tests:** Dependency propagation (Broken Assumption → Invalidated Factor → Contradiction in Challenges).
- **Accessibility tests:** axe-core passes on every component state. Focus management verified programmatically.
- **Visual regression tests:** Screenshot per state per variant.
- **Responsive tests:** At 1280px (desktop), 768px (tablet), 375px (mobile).

## Documentation Expectations

Each Reasoning Component is documented with:
1. Purpose and semantic meaning
2. Relationship to other Reasoning Components
3. All props (types, defaults, required/optional, descriptions)
4. All states (visual description and semantic meaning)
5. Interaction model (keyboard, mouse, touch)
6. Atlas Collaboration behavior (where applicable)
7. Historical behavior
8. Accessibility notes
9. Token mapping reference
10. Serialization format
11. Examples (correct use) and anti-patterns (incorrect use)
12. Changelog

## Versioning

Same semantic versioning as Foundation Components (major.minor.patch). Reasoning Component breaking changes (major bumps) that affect serialization format also require a data migration plan — the old serialization format must continue to be readable for historical records.

---

# 19. Reasoning Audit

## No Duplicated Reasoning Components

Review confirms:
- Conclusion and Proposed Decision Candidate Content are semantically distinct (what is believed vs. what is suggested).
- Supporting Factors and Evidence Summary are semantically distinct (reasoning claims vs. evidence grounding).
- Challenges and Assumptions are semantically distinct (current concerns vs. conditions depended on).
- Opportunity Summary and Opportunity Cost are semantically distinct (what the opportunity is vs. what is foregone to pursue it).
- Comparison and Scenario Analysis are semantically distinct (evaluation of options vs. exploration of uncertain futures).
- Reasoning Block and Context Panel are semantically distinct (named reasoning of unclassified type vs. supplementary background context).
- No duplicate component found.

## Clear Semantic Ownership

Each Reasoning Component has:
- A defined semantic purpose.
- A defined "When Not Used" condition that distinguishes it from adjacent components.
- A clear position in the reasoning dependency chain (Section 14).

## Consistent Hierarchy

All Reasoning Components use the six-level Information Hierarchy consistently:
- Conclusions, Opportunity Statements, Recommendation Statements: Level 1 typography
- Component and Group names: Level 2–3 typography
- Narrative explanations: Level 3 typography
- Metadata, labels, contextual text: Levels 5–6 typography

## Consistent Terminology

All components use the canonical terminology from the UX-012 glossary:
- "Historical" (not "archive", "past", or "prior") for historical content
- "Assumption" (not "hypothesis" or "premise") for assumption-type content
- "Challenge" (not "risk", "concern", or "issue") for challenge-type content
- "Conclusion" (not "summary" or "finding") for conclusion-type content
- "Atlas Suggestion" (not "AI recommendation" or "suggestion") for Atlas-generated proposals

## Accessibility Completeness

All thirteen Reasoning Components specify:
- ARIA roles and labels.
- Keyboard navigation.
- Focus management.
- Screen reader announcements for all states.
- Reduced-motion fallbacks.
- Touch targets.
- High Contrast Mode compatibility.

## Engineering Readiness

The Reasoning Engineering Mapping (Section 18) provides component hierarchy, universal props, composition model, state management boundary, serialization expectations, testing requirements, and documentation requirements. Engineering can begin implementation from these specifications.

## Alignment with UX-012

All Reasoning Components are present in the UX-012 Initial Atlas Component Inventory. No Reasoning Component specified in UX-013B conflicts with a UX-012 design decision. All token references use token names from the UX-012 Semantic Token Model. All state definitions align with the fourteen Interaction Tokens defined in UX-012 Section 44.

---

# What UX-013B Establishes

## Core Reasoning

The Conclusion component is fully specified in five variants (Primary, Current, Portfolio, Review, Historical). The complete anatomy, editing behavior, Historical behavior, Atlas attribution model, and accessibility requirements for the primary reasoning output are established.

Supporting Factors are fully specified: FactorItem anatomy, ordering and reordering model, grouping, evidence association, qualitative weight labels, Weakening and Invalidated states, and the relationship between Assumption status and Factor state.

Challenges are fully specified: three severity levels (Informational, Material, Blocking) with distinct visual treatments (left-border system), the acknowledgement model and completion gate behavior for Material and Blocking challenges, the Contradiction variant, and the Atlas-surfaced Challenge model.

Assumptions are fully specified: four status states (Holding, Under Review, Weakening, Broken), the dependency model linking Assumptions to Supporting Factors, the Monitoring Condition association, the automated propagation of Broken Assumption status to Invalidated Factors and Contradiction surfacing in Challenges, and Historical status preservation.

## Supporting Analysis

Evidence Summary is fully specified: inline and Section variants, source representation, confidence presentation (qualitative only), linking to dependent Factors and Challenges.

Opportunity Summary is fully specified: standard and compressed variants, placement in the reasoning sequence, relationship to the reasoning chain, Historical handling.

## Comparisons

Comparison is fully specified: four comparison types (Before/After, Alternative, Allocation, Historical), column ordering rules, relationship visualization, tabular accessibility model, and responsive stacking behavior.

## Scenarios

Scenario Analysis is fully specified: Base/Upside/Downside/Alternative structure, fixed ordering rule, qualitative probability (Likely/Possible/Unlikely), relationship to the reasoning chain, Historical behavior, and conditional expandability on mobile.

## Candidate Content

Proposed Decision Candidate Content is fully specified: Atlas-Generated Candidate Content and User-Authored Candidate Content variants, the three-response model (Accept/Modify/Decline), flow to Proposed Decision on acceptance, 5-second structural undo, and Historical persistence within the Decision.

## Context

Reasoning Block is fully specified: Standard and Compact variants, one-level nesting model, expandable behavior identical to Section Container.

Context Panel is fully specified: Inline, Companion, and Reference variants, the `<aside>` landmark, Historical context model, and cross-reference link behavior.

## Metadata

Supporting Metadata is fully specified: six metadata types (Source, Date, Author, Confidence, Version, Relationship), ordering rule, visibility rules, Historical lock indicator, Inline and Expanded variants, and the composable atomic implementation model.

## Relationships

The reasoning dependency chain (Conclusion → Factors + Challenges + Assumptions → Evidence → Opportunity → Cost → Scenarios + Comparison → Candidate Content → Decision) is fully specified. Dependencies between components (Assumption → Factor → Challenge), ordering within each Workspace, and cross-component navigation (RelationshipIndicators, Highlight motion token, smooth scroll) are established.

## Accessibility

The shared Reasoning Accessibility specification establishes: keyboard tab order within the reasoning body, focus behavior on component removal, reading order for screen readers, state announcements for all thirteen Reasoning Component states, touch reorder model, reduced-motion fallbacks for all Reasoning Component animations, and High Contrast compatibility.

## Engineering Mapping

The Reasoning Engineering Mapping establishes: component hierarchy across five categories (Core, Analysis, Synthesis, Structure, Metadata), naming conventions, universal props interface (`ReasoningComponentBase`), composition model, application-owned vs. component-owned state boundary, serialization format (structured JSON), testing requirements (six test types), and documentation requirements (twelve mandatory sections).

---

# Remaining Reasoning Questions

**Question 1: Atlas Suggestion Targeting Precision**
Reason: The specification states that Atlas Suggestions appear in the relevant Section after 1.5s of editing inactivity. For Reasoning Components with multiple items (a list of Supporting Factors), the precision of targeting — whether Atlas suggests a specific new factor, a modification to an existing factor, or a reordering — has not been specified at the component level.
Required Evidence: Atlas AI team input on what types of suggestions are feasible to generate at the item level (individual factor, challenge, assumption) vs. the section level. User research on whether item-level suggestions are perceived as more or less helpful than section-level suggestions.
Implementation Impact: Determines whether the Atlas Suggestion component appears at the Section level (one suggestion per Section) or the Item level (a suggestion attached to a specific Factor or Challenge). Item-level suggestions require a more complex suggestion component anatomy.
Priority: High. Resolving this before implementing the Atlas Suggestion model within Reasoning Components prevents rework.

**Question 2: Contradiction Detection Scope**
Reason: The specification states that Atlas detects Contradictions between Reasoning Components (e.g., a Conclusion inconsistent with Challenges). The scope of automated detection — which types of contradictions are within Atlas's detection capability — has not been specified.
Required Evidence: Atlas AI team definition of which contradiction types Atlas can reliably detect: (a) Assumption Broken → Factor Invalidated (specified), (b) Conclusion direction vs. balance of Factors/Challenges, (c) Opportunity Cost inconsistency with Conclusion, (d) candidate content inconsistency with Challenges.
Implementation Impact: Determines the trigger conditions for automatically surfacing Contradictions in the Challenges section. Over-triggering false contradictions would create noise; under-triggering misses the value of Atlas analysis.
Priority: High. The Contradiction model is central to Atlas's value proposition.

**Question 3: Assumption Monitoring Condition Creation Flow**
Reason: The Assumption component specifies that an Assumption may have an associated Monitoring Condition, and that the creation is triggered by "+Add Monitoring" on the AssumptionItem. The creation flow (fields, validation, lifecycle initiation) will be fully specified in UX-013C (Decision & Monitoring Components). This creates a dependency: the Assumption component is specified, but the action within it (creating a Monitoring Condition) is specified in the next document.
Required Evidence: No new evidence required — this is a sequencing dependency that will be resolved in UX-013C.
Implementation Impact: The Assumption component's "+Add Monitoring" action should be implemented as a deferred interaction (opens a flow to be specified in UX-013C) rather than a self-contained flow. Engineering should plan for this dependency.
Priority: Medium. The Assumption component can be implemented before UX-013C if the "+Add Monitoring" action is stubbed with a placeholder.

**Question 4: Scenario Analysis vs. Formal Scenario Workspace**
Reason: The Scenario Analysis component as specified handles scenario analysis within the Decision Workspace inline. UX-012 identifies a potential future "Scenario Workspace" as a dedicated Workspace for structured scenario analysis. The relationship between the inline Scenario Analysis component and the future Scenario Workspace has not been specified — in particular, whether the Scenario Analysis component will remain as an inline component when the Scenario Workspace exists.
Required Evidence: Product decision on whether Scenario Workspace, if created, replaces inline Scenario Analysis or supplements it.
Implementation Impact: Low for current implementation (specify and build the inline component as specified). Medium for future Workspace planning — if Scenario Workspace will replace inline Scenario Analysis, the component should be designed for extraction.
Priority: Low. The inline Scenario Analysis component can proceed to implementation as specified.

**Question 5: Evidence Recency Threshold**
Reason: The Evidence Summary specification states that evidence items with dates older than a threshold display an "Older reference" label. The threshold has not been defined.
Required Evidence: Investment domain expertise — what constitutes "old" evidence depends on the investment type (public equities: months; private equity: years; macro: quarters). A single threshold may not be appropriate for all Atlas contexts.
Implementation Impact: May require a configurable threshold (set at the Workspace or investment-type level) rather than a global constant. Or a simpler heuristic (e.g., "> 12 months" for all types) that is acknowledged as approximate.
Priority: Low. The label is a UI hint, not a validation requirement. The implementation can use a reasonable default (12 months) until evidence-based refinement is possible.

---

# Reasoning Component Inventory

The official Atlas Reasoning Component Inventory for UX-013B. Maturity is Candidate unless noted.

| Category | Component Name | Semantic Purpose | Primary Workspace | Secondary Reuse | Engineering Priority | Figma Priority | Maturity | Future Owner |
|----------|---------------|-----------------|-------------------|-----------------|---------------------|----------------|----------|--------------|
| Core | Conclusion (Primary) | Settled Workspace-level conclusion | Investment, Portfolio | Decision | Immediate | Immediate | Candidate | Design System |
| Core | Conclusion (Current) | Live-updating reasoning direction | Decision | Investment | Immediate | Immediate | Candidate | Design System |
| Core | Conclusion (Portfolio) | Portfolio-level integration conclusion | Portfolio | — | High | High | Candidate | Design System |
| Core | Conclusion (Review) | Formal review outcome conclusion | Decision (review) | Future Review | Medium | Medium | Experimental | Design System |
| Core | Conclusion (Historical) | Preserved prior conclusion | All | All | High | High | Candidate | Design System |
| Core | SupportingFactors Container | Section for named reasoning factors | Investment, Decision | Portfolio | Immediate | Immediate | Candidate | Design System |
| Core | FactorItem | Single named supporting reason | Investment, Decision | Portfolio | Immediate | Immediate | Candidate | Design System |
| Core | FactorGroup | Grouped category of related factors | Investment, Decision | All | Medium | Medium | Candidate | Design System |
| Core | Challenges Container | Section for named concerns and risks | Investment, Decision | Portfolio | Immediate | Immediate | Candidate | Design System |
| Core | ChallengeItem (Informational) | Relevant concern, no gate effect | Investment, Decision | All | Immediate | Immediate | Candidate | Design System |
| Core | ChallengeItem (Material) | Significant concern, soft gate | Decision | Investment | Immediate | Immediate | Candidate | Design System |
| Core | ChallengeItem (Blocking) | Must-resolve concern, hard gate | Decision | — | Immediate | Immediate | Candidate | Design System |
| Core | ChallengeItem (Contradiction) | Logic conflict between reasoning elements | Decision | Investment | High | High | Candidate | Design System |
| Core | Assumptions Container | Section for explicit conditions | Investment, Decision | Portfolio | High | High | Candidate | Design System |
| Core | AssumptionItem (Holding) | Active assumption in good standing | Investment, Decision | All | High | High | Candidate | Design System |
| Core | AssumptionItem (Under Review) | Assumption being re-examined | Investment, Decision | All | High | High | Candidate | Design System |
| Core | AssumptionItem (Weakening) | Assumption reliability declining | Investment, Decision | All | High | High | Candidate | Design System |
| Core | AssumptionItem (Broken) | Invalidated assumption | Investment, Decision | All | High | High | Candidate | Design System |
| Analysis | EvidenceSummary | Section for reasoning evidence base | Investment | Decision | Medium | Medium | Candidate | Design System |
| Analysis | EvidenceItem | Single evidence reference | Investment | Decision | Medium | Medium | Candidate | Design System |
| Analysis | OpportunitySummary | Investment opportunity thesis | Investment | Decision | High | High | Candidate | Design System |
| Analysis | OpportunityCost | Explicit foregone alternatives | Decision | Portfolio | High | High | Candidate | Design System |
| Analysis | AlternativeItem | Single foregone alternative | Decision | Portfolio | High | High | Candidate | Design System |
| Analysis | Comparison (Before/After) | Current vs. proposed state | Decision | Portfolio | High | High | Candidate | Design System |
| Analysis | Comparison (Alternative) | Side-by-side option evaluation | Decision | Investment | High | High | Candidate | Design System |
| Analysis | Comparison (Allocation) | Portfolio allocation comparison | Portfolio | Decision | High | High | Candidate | Design System |
| Analysis | Comparison (Historical) | Current vs. historical reasoning | Decision | Investment | Medium | Medium | Candidate | Design System |
| Analysis | ScenarioAnalysis Container | Section for scenario structure | Decision | Investment | Medium | Medium | Candidate | Design System |
| Analysis | ScenarioItem | Single named scenario | Decision | Investment | Medium | Medium | Candidate | Design System |
| Synthesis | Candidate Content (Atlas) | Atlas-generated directional suggestion | Decision | Investment | High | High | Candidate | Design System |
| Synthesis | Candidate Content (User) | User-authored working intent | Investment | Decision | Medium | Medium | Candidate | Design System |
| Structure | ReasoningBlock | Named container for unclassified reasoning | All | All | Medium | Medium | Candidate | Design System |
| Structure | ContextPanel (Inline) | Supplementary background in reading flow | Investment | All | Medium | Medium | Candidate | Design System |
| Structure | ContextPanel (Companion) | Supplementary context adjacent to component | Investment | Decision | Low | Low | Experimental | Design System |
| Structure | ContextPanel (Reference) | Cross-reference link panel | All | All | Medium | Medium | Candidate | Design System |
| Metadata | SupportingMetadata | Provenance information for reasoning content | All | All | Immediate | Immediate | Candidate | Design System |
| Metadata | DateLabel | Timestamp display | All | All | Immediate | Immediate | Stable | Design System |
| Metadata | AuthorLabel | Attribution display | All | All | Immediate | Immediate | Stable | Design System |
| Metadata | SourceLabel | Source reference display | Investment | All | High | High | Candidate | Design System |
| Metadata | ConfidenceLabel | Qualitative confidence indicator | Investment, Decision | All | Medium | Medium | Candidate | Design System |
| Metadata | RelationshipLabel | Cross-record relationship link | Decision | All | High | High | Candidate | Design System |

---

# Implementation Readiness Assessment

## Design Completeness — Ready

All thirteen Reasoning Components are specified with: purpose, semantic meaning, when used, when not used, variants, anatomy, properties, states, interaction, historical behavior, accessibility, responsive behavior, composition rules, content rules, spacing rules, token mapping, Figma architecture, and engineering guidance. The Reasoning Relationships section establishes the full dependency graph. No Reasoning Component requires additional design philosophy work.

## Engineering Readiness — Ready

The Reasoning Engineering Mapping provides: component hierarchy, naming conventions, universal props (`ReasoningComponentBase`), composition model, application-owned vs. component-owned state boundary, serialization format (structured JSON), testing requirements, and documentation requirements. Engineering can begin implementation from this specification.

**Recommended implementation sequence:**
1. SupportingMetadata (atomic metadata components)
2. Conclusion (Primary and Current variants)
3. FactorItem and SupportingFactors Container
4. ChallengeItem (all severity levels) and Challenges Container
5. AssumptionItem (all status states) and Assumptions Container
6. Dependency propagation logic (Assumption → Factor → Challenge)
7. OpportunitySummary
8. OpportunityCost and AlternativeItem
9. Comparison (all four types)
10. EvidenceSummary and EvidenceItem
11. ScenarioAnalysis Container and ScenarioItem
12. Candidate Content (Atlas and User variants)
13. ReasoningBlock
14. ContextPanel (all three variants)
15. Historical variants of all components

## Accessibility Readiness — Ready

The shared Reasoning Accessibility specification covers all thirteen components. Every component specifies ARIA, keyboard, focus, screen reader, touch, reduced motion, High Contrast, and zoom requirements.

## Responsive Readiness — Ready

All Reasoning Components specify behavior at Desktop, Tablet, and Mobile. The primary responsive adaptations — Comparison stacking on mobile, Scenario expandability on mobile, full-screen editing for Long-Form Editor fields — are specified.

## Token Readiness — Ready

Section 17 provides the complete Reasoning Token Mapping. New token groups introduced in UX-013B (reasoning.factor.*, reasoning.challenge.*, reasoning.assumption.*, reasoning.opportunity.*, reasoning.scenario.*, reasoning.recommendation.*, border.factor.*, border.challenge.*, surface.challenge.*, surface.assumption.*) must be added to the token dictionary before Reasoning Component implementation begins.

## Documentation Quality — Ready

All specifications meet the twelve-section documentation standard established in the Reasoning Engineering Mapping. Serialization examples are provided for key components (FactorItem).

## Testing Readiness — Ready

Testing requirements (six test types: structural, state, interaction, relationship, accessibility, visual regression, responsive) are defined for all Reasoning Components.

## Overall Implementation Readiness

**The Reasoning Component Library is ready for production implementation.**

Two prerequisites before beginning implementation:
1. Token dictionary must be extended with the new Reasoning Component token groups defined in Section 17.
2. Question 1 (Atlas Suggestion targeting precision) should be resolved in consultation with the Atlas AI team before implementing the Atlas Suggestion integration within Reasoning Components. The components themselves can proceed; the Atlas Suggestion attachment can be implemented after resolution.

UX-013C (Decision & Monitoring Components) can be produced in parallel with Reasoning Component implementation. The Assumption "+Add Monitoring" action should be stubbed until UX-013C is complete.

---

# Requirements for UX-013C

## UX-013C — Atlas Component Specification: Decision & Monitoring Components

UX-013C specifies every Atlas Decision and Monitoring Component in the same production-ready depth as UX-013A (Foundation) and UX-013B (Reasoning). Every component must be documented in sufficient detail that Figma components can be built directly and engineering can implement without inventing behavior.

**Scope:** All Decision and Monitoring Components from the UX-012 Component Inventory.

**Decision Components to specify:**
- Proposed Decision (the user's authored intent before formalization)
- Final Decision Card (signature component — six fields, two states: Draft and Recorded)
- Decision Field (signature editing component for Final Decision Card fields)
- Decision Summary (condensed portable version for display in other Workspaces)
- Decision History (chronological list of Recorded Decisions)
- Decision Amendment (formal link from a new Decision to a prior one)
- Decision Review (formal re-examination of a prior Decision)
- Decision Required (the specific choice framing in the Decision Workspace)
- What Changed (recent developments triggering the current reasoning session)
- Portfolio Consequences (portfolio-level implications of the Decision)
- Implementation Summary (how and when the Decision will be executed)
- Review Condition (the trigger for future Decision Review)

**Monitoring Components to specify:**
- Monitoring Condition (single trackable condition with full lifecycle: Established → Active → Approaching → Triggered → Acknowledged → Resolved)
- Review Trigger (communication that Review Condition has been met)
- Invalidation Trigger (communication that Invalidation Condition has been met)
- Implementation Follow-up (tracks whether Implementation Intent was executed)
- Scheduled Review (time-based review trigger established at Decision time)
- Monitoring State Label (current lifecycle stage indicator)

**History Components to specify:**
- Historical Record (base immutable content container)
- Historical Decision (full Recorded Decision as Historical Record)
- Historical Review (completed Review as Historical Record)
- Historical Assumption (Assumption at a prior point in time, for review comparison)
- Historical Timeline Entry (single entry in chronological event timeline)
- Decision Outcome (what actually happened after the Decision was recorded)

**For each Decision & Monitoring Component, UX-013C must specify:**

- Purpose and Semantic Meaning
- When Used / When Not Used
- All Variants (with semantic justification)
- Complete Anatomy (every sub-element named and described)
- Properties (all configurable, with types, defaults, required/optional)
- All States (with visual and behavioral description)
- Interaction Behavior (keyboard, mouse, touch; editing for Decision Fields)
- Completion Gate Behavior (for components that affect or are affected by the completion gate)
- Historical Behavior (how the component transforms on recording)
- Monitoring Lifecycle (for Monitoring Components — all lifecycle stage transitions)
- Accessibility Behavior (ARIA, keyboard, focus management, screen reader announcements)
- Responsive Behavior (Desktop, Tablet, Mobile — especially for the Final Decision Card on mobile)
- Composition Rules (what contains it, what it contains, nesting)
- Content Rules (required fields, maximum lengths, validation)
- Validation Rules (when validation appears, what it communicates, severity)
- Token Mapping (every visual property mapped to semantic token)
- Figma Component Architecture
- Engineering Naming and Guidance
- Serialization Format (especially important for the Final Decision Card — the structure that becomes the permanent historical record)
- Examples and Anti-Patterns
- Future Extensibility

**The Final Decision Card specification must be treated as the highest-priority component in UX-013C.** It is the signature Atlas component and the culmination of the entire reasoning process. Its six fields, two states (Draft/Live-Updating and Completed/Recorded), completion gate, 400ms pause, historical conversion, and permanent immutability are the most consequential specification in the Atlas Component Library.

**The Monitoring Condition lifecycle specification must be fully detailed**, including all six stages (Established, Active, Approaching, Triggered, Acknowledged, Resolved), the trigger conditions for each transition, how transitions are communicated to users, and how transitions relate to the broader Monitoring surface in the Dashboard and Investment Workspace.

**UX-013C should also specify the completion sequence end-to-end:** from the user activating the Record Decision action, through the completion gate check, the 400ms pause, the Workspace conversion to Historical state, the activation of Monitoring Conditions, the creation of the Historical Record, and the post-completion Workspace state.

Do not produce UX-013C yet. The completed UX-013B is the prerequisite.

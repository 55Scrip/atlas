UX-012B — Atlas Design System Components & Reusable Patterns

Status: Component Specification Complete
Owner: Atlas Product
Governs: Reusable component library, component taxonomy, component states, accessibility behavior, component relationships
Depends on: UX-012A — Atlas Design System Foundations; UX-008 through UX-011
Part B of: UX-012 — Atlas Design System & Workspace Consistency Specification

**Correction Notice (Phase 3, governed by ADR-002 — 2026-07-25):** This document's original identity (Status, Owner, Governs, Depends on, Part B of, as above) and original date are preserved unchanged. Two semantic areas were corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan, Phase 3:
- **C-02 (AI Authorship and Provenance):** the Decision Section, Proposed Decision, and Atlas Suggestion components previously stated that accepting an Atlas proposal, by itself, transitioned the field directly to "user-modified-from-atlas" state — this read as authorship transferring on acceptance alone. These passages were corrected so that acceptance alone produces an Accepted state ("Atlas Suggested / User Accepted"), with authorship not yet transferred; "user-modified-from-atlas" is now reached only after a genuine, subsequent edit to the accepted content. The Long-form Editor's own "User-modified-from-atlas" states-list entry already described this correctly (a genuine-edit state, not an acceptance-triggered one) and is unchanged.
- **C-03 (Decision Workspace Sequence terminology):** two "Reuse rules" cross-references to the Decision Workspace's own section names were corrected — "Section 5 — What Supports This Decision" to "Section 5 — Supporting Factors," and "Section 6 — Challenge Review" to "Section 6 — Challenges."

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, above. All content outside these two areas, including every other component's own reusable definitions, is unchanged.

**Correction Notice (Phase 3E, governed by `ADR-004-Scenario-Analysis-Comparison-and-Sequence-Authority-Resolution.md`'s own committed Corpus-Wide Scenario Comparison Extension addendum — 2026-07-27):** This document previously presented "Scenario Comparison" as a fully specified Comparison component — with Purpose, Structure (a card-per-scenario grid: scenario name, outcome label with semantic color, consequence line, optional expandable detail), Interaction, Visual treatment, and Reuse rules — listed alongside its five sibling Comparison components in this document's own component-taxonomy list, and the subject of its own "Remaining Component Questions" item 4 concerning mobile layout. **This correction does not delete that design material.** It is retained below, relabeled, as historical experimental design evidence, on the following evidentiary basis, per the ADR-004 addendum:
- This document's own companion, `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md`, marked the same-named entry Maturity: **Experimental** in its own Component Inventory table (since corrected — see that document's own Phase 3E notice) — under `UX-012D-Atlas-Design-System-Governance-Tokens-Evolution.md`'s own governing maturity definition, an idea that had not completed the approval process and "may not be considered a shared system component until it has."
- `UX-013B-Atlas-Component-Specification-Reasoning-Components.md`'s own later, independently-authored Reasoning Component Inventory table promoted two of this same entry's Experimental-maturity Comparison siblings (Allocation Comparison, Historical Comparison) to "Candidate" but did not carry this entry forward at all.
- No test, token, prop, route, persisted field, or other downstream implementation artifact referencing "Scenario Comparison" as a distinct, adopted rendering artifact was found anywhere in the repository.
- This entry's own card-per-scenario anatomy materially overlaps `UX-013B-...md` §9's own `ScenarioItem` anatomy (`ScenarioType`, `ScenarioName`, `ProbabilityLabel`, `Conditions`, `Implications`) — scenario-specific content that ADR-004 R-02 assigns exclusively to Scenario Analysis.
- `UX-005-Investment-Workspace-Screen-Specification.md`'s own earlier "Scenario Cards"/"Scenario Card" wireframe-level element listings offer a plausible, documented lineage for this card-based concept, predating Scenario Analysis's own later, more authoritative specification — offered as observed evidence of a documented lineage only, not as proof of this document's own original authors' intent, which the repository cannot establish.

On this basis, the entry below is retained as historical experimental evidence, not as an adopted Comparison component or a required named Comparison variant; its own scenario-specific content is owned by Scenario Analysis, not by Comparison, per ADR-004 R-02/R-04. Its component-taxonomy list entry has been removed accordingly, and its "Remaining Component Questions" item 4 has been marked moot. This correction introduces no new component, variant, state, interaction, rendering primitive, persistence, route, API, or token, and does not amend ADR-002, ADR-003, or ADR-004. Finding F-2 and any other unrelated matter remain untouched.

**Correction Notice (Phase 6C, governed by ADR-002 C-06 — 2026-07-29):** This is a later, additive correction, discovered after the Phase 3 and Phase 3E corrections above had already closed; it does not revise, replace, or reopen either notice, both of which remain historically accurate for the areas they corrected. One active occurrence of unqualified "disabled" wording applied to the Record Decision control was corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` C-06 and the Atlas UX Source Correction Plan, Phase 6C:
- The "Blocking Issue" feedback-pattern definition's "Behavior:" line previously stated "The primary action (Record Decision) remains disabled" — corrected to "remains unavailable (`aria-disabled=\"true\"`, never native `disabled`)."

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, at the corrected passage. No described interaction behavior (the blocking-condition explanation, the auto-scroll-to-field behavior) is changed by this correction — only the terminology naming the control's unavailable state. The immediately adjacent "Visual treatment:" line, and the separate "Required content"/"Interaction:" passage at this document's own Primary Action definition (reviewed and excluded per the governance amendment's own classification, since it describes a generic, cross-Workspace, cross-action pattern rather than the Record Decision C-06 contract specifically), remain byte-identical and unaffected. The Completion Section and Completion Action definitions elsewhere in this document, and this document's own Universal state model and Interaction-token lists, are likewise unaffected. All content outside the one corrected passage above, including this document's own already-corrected Phase 3 and Phase 3E passages, is unchanged.

**Clarification Notice (Atlas UX Architecture UX-012 Authority Migration task — 2026-08-02):** This is a later, additive clarification; it does not revise, replace, or reopen any notice above. This document is subordinate to `UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0, per that Doctrine's own UXD-R-097. One clarification is added, without changing any specified component behavior: the Review Conclusion component (Section 5) is annotated with its governing Product-layer precondition, per `UX-000-Atlas-UX-Doctrine.md` UXD-R-071 item 4 and UXD-R-086.

⸻

1. Component Philosophy

Atlas components are not visual primitives. They are not buttons, cards, or inputs in the generic sense. An Atlas component is the visual and interactive form of a recurring product meaning — a reasoning relationship, a decision state, a monitoring condition, an authorship distinction that must be communicated consistently across every surface.

A component earns its place in the Atlas Design System when the same product meaning recurs across two or more surfaces, and when inconsistent presentation of that meaning would confuse or mislead a user. The challenge item in the Decision Workspace and the contradiction signal in the Investment Workspace represent the same product concept — reasoning that conflicts with a conclusion. They are the same component because the meaning is the same, even though the surface context differs.

A component does not earn its place because it would be convenient to reuse its visual appearance. A box with a label in the upper-left corner is not a component. A monitoring condition — an observable state linked to a prior decision, with a defined trigger, a current status, and a relationship to future Atlas behavior — is a component.

Every Atlas component shares five characteristics:

Clarity: The component communicates one product meaning with precision. The user who encounters it anywhere in Atlas should immediately understand what it represents, what state it is in, and what interaction is available.

Restraint: The component uses only the visual and interactive elements required to communicate its meaning. No decorative borders, no gratuitous icons, no surplus states. The visual treatment is as minimal as the meaning allows.

Predictability: The component behaves identically in structurally equivalent contexts. If expanding an assumption row in the Decision Workspace reveals the supporting reasoning and a comment field, expanding an assumption row in a future Review Workspace reveals the same elements in the same order.

Editorial quality: The component's typography, spacing, and containment follow the Atlas visual hierarchy established in UX-012A. No component introduces typography, spacing, or containers that contradict the foundation.

Accessibility: Every component is fully operable by keyboard, correctly labeled for screen readers, and communicates all states through non-color means. Accessibility is designed into the component, not added afterward.

When does a new component deserve to exist? Three conditions must all be true: (1) the product meaning it represents recurs across at least two Atlas surfaces; (2) inconsistent presentation of that meaning would harm the user's understanding or trust; (3) no existing component can be extended or composed to represent the meaning correctly. Meeting only one or two conditions does not justify a new component — it justifies an extension or a usage variant of an existing one.

⸻

2. Component Taxonomy

Atlas components are organized into twelve categories. Each category represents a class of product meaning, not a class of visual form.

Workspace: Components that constitute the structural frame of any Atlas Workspace — the identity, header, footer, and navigation controls. These components are present on every overlay Workspace surface.

Section: Components that represent the collapsible reasoning units within a Workspace body — their anatomy, their collapsed and expanded states, and their behavioral variants by content type.

Conclusion: Components that present Atlas's primary interpretive statements — the settled analysis that anchors a Workspace or section. These are among the highest-emphasis components in the system.

Reasoning: Components that present the supporting, challenging, or analytical content beneath a conclusion — the evidence, assumptions, challenges, consequences, and conditions that explain and qualify it.

Comparison: Components that structure explicitly comparative content — alternatives, before/after states, scenario contrasts, historical versus current.

Decision: Components that exist at the Decision Workspace level — the user's authored commitment, the proposed form, the final recorded card, and its downstream representations.

Monitoring: Components that represent ongoing observation — conditions Atlas watches, triggers that may reopen a decision, and the lifecycle of a monitoring item from establishment through resolution.

History: Components that represent prior records — prior decisions, prior conclusions, prior assumptions — in their immutable, timestamp-attributed form.

AI Collaboration: Components that represent Atlas's active assistance — suggestions, insights, warnings, clarifications, and the interaction patterns for accepting, modifying, or dismissing them.

Editing: Components that represent the user's authoring experience — the field states, editing controls, autosave indicators, and undo behavior for every type of editable content in Atlas.

States and Feedback: Components that communicate current system or content state — draft indicators, loading states, empty states, validation messages, and completion confirmations.

Actions: Components that represent user-initiated actions — primary, secondary, inline, and destructive action controls at all levels of the action hierarchy.

Metadata: Components that present supplementary system information — timestamps, source references, confidence labels, version indicators, authorship attributions.

⸻

3. Workspace Components

Workspace Frame

Purpose: The non-scrolling outer shell of any Atlas Workspace overlay. Contains the fixed header, the scrolling body zone, and the fixed footer. Defines the proportional relationship between these three areas.
Required content: Fixed header (Workspace Header component), scrolling body zone, fixed footer (Workspace Footer component).
Optional content: Historical mode indicator when the Workspace is displaying a prior record.
Interaction: Opens with the defined entry transition. Closes via the return/close control. The underlying surface dims on open and restores on close. The underlying surface's scroll position, expanded sections, and filter state are preserved.
Responsive behavior: On desktop — overlay proportioned to approximately 94vw × 93vh, centered. On tablet — full-screen overlay. On mobile — full-screen overlay with safe-area-aware footer.
Appropriate use: Every Investment Workspace, Portfolio Workspace, and Decision Workspace. Future analytical and review Workspaces.
Misuse to avoid: Do not use the Workspace Frame as a persistent panel or sidebar. It is an overlay — it implies a focused, temporary departure from the underlying context.

⸻

Workspace Header

Purpose: The fixed top bar of a Workspace. Orients the user to the Workspace subject, type, and status before they read any body content.
Required content: Workspace Identity (the subject name — investment name, "Portfolio Review," or equivalent). Workspace type and decision type on a secondary line (smaller, lighter weight). Return/close control (right-aligned).
Optional content: Status indicator (Draft, Recorded, Under Review — present only when the state is non-default). Draft indicator (very low emphasis; last-saved timestamp or unsaved-changes signal). Related source link (compact reference to the originating Workspace).
Interaction: The return/close control closes the Workspace and restores the underlying surface. The related source link opens the originating Workspace in a new overlay layer or navigates to it depending on context. The header is not a toolbar — no other controls belong here.
Responsive behavior: Header height is minimal — sufficient to hold two text lines and the control. The secondary line may collapse to a label only (without decision type) on narrow viewports if space is constrained.
Appropriate use: Every Workspace Frame.
Misuse to avoid: Do not add search, filtering, settings, or supplementary controls to the Workspace Header. Do not use the header to display body-level information.

⸻

Workspace Identity

Purpose: The primary text element within the Workspace Header. Names the subject and type of the current Workspace.
Required content: Subject name (investment name, "Portfolio Review," etc.) at the largest header text size. Workspace type on a secondary line at a clearly smaller weight and size.
Optional content: Decision type (for Decision Workspace only — "Reduce Position," "Initiate Position," etc.) on the secondary line adjacent to or below the Workspace type label.
Interaction: Non-interactive. Read-only identity anchor.
Responsive: Subject name may truncate with ellipsis on narrow viewports if the string exceeds available width. The secondary line is preserved.
Appropriate use: Inside every Workspace Header.
Misuse: Do not use Workspace Identity outside of the header context. Do not make it tappable as a navigation element.

⸻

Workspace Status

Purpose: Communicates the current lifecycle state of the Workspace or its primary object (decision, review, analysis). Present only when the state is non-default.
Required content: A single state label from the defined status vocabulary (Draft, Recorded, Under Review, Monitoring, Superseded, Historical).
Optional content: Brief contextual note in metadata scale (e.g., "Last reviewed: [date]").
Interaction: Non-interactive in most states. In Recorded or Monitoring state, may expand on tap to show the recorded date and a link to the Final Decision Record.
Responsive: Compact on all viewports. May reduce to an icon-only treatment on mobile if text cannot be accommodated alongside the Workspace Identity.
Appropriate use: Workspace Header when the state is non-default. May appear in condensed form within the Workspace Footer.
Misuse: Do not use Workspace Status for content-level states (assumption status, contradiction severity) — those have their own state components.

⸻

Workspace Footer

Purpose: The fixed bottom bar of a Workspace. Contains the primary action for the current stage and any supporting secondary actions. The completion region.
Required content: Primary action control (Record Decision, Complete Review, or equivalent). The primary action's disabled explanation when the action is not yet available.
Optional content: Secondary actions (Save Draft, Return to Analysis, Compare Alternatives). Tertiary contextual links (View History).
Interaction: Primary action is the terminal point of the Workspace reasoning flow. In disabled state: rendered at reduced opacity (~40–45%), cursor not-allowed, adjacent explanation text visible. Secondary actions are clearly subordinate in visual weight. On mobile, the primary action is within thumb reach at the bottom of safe area.
Responsive: On desktop and tablet, footer contains the full action group. On mobile, secondary actions may move to a collapsed "More options" disclosure if space is insufficient.
Appropriate use: Every Workspace Frame, always fixed at the bottom.
Misuse: Do not add navigation, settings, or supplementary content to the footer. There should never be more than one primary action in the footer at any time.

⸻

Return Navigation

Purpose: The control that closes the Workspace and returns the user to the underlying surface.
Required content: A close or back label ("Close" or "←" with surface name). Single control.
Interaction: On activation, the Workspace closes with the reverse of the entry transition. The underlying surface restores to its exact prior state (scroll position, expanded sections, filter state). No confirmation is required unless there are unsaved changes exceeding the autosave interval.
Responsive: Always present in the Workspace Header. On mobile, may be the sole header control on the left.
Appropriate use: Every Workspace Header.
Misuse: Do not use Return Navigation as a breadcrumb or navigation trail. It returns to one specific prior surface — not to an arbitrary destination.

⸻

Historical Indicator

Purpose: Communicates that the Workspace is currently displaying a prior record, prior decision, or prior state rather than the current active version.
Required content: A clear label identifying the historical mode: "Reviewing prior decision · [date]" or "Historical analysis · [date]."
Optional content: A link to the current active version ("View current →").
Interaction: Non-interactive label. The link to the current version opens the current state.
Responsive: Compact. Displayed below the Workspace Identity in the header, or as a banner at the very top of the scrolling body.
Appropriate use: Any Workspace in review or historical mode.
Misuse: Do not use Historical Indicator when the Workspace is displaying current content. Do not apply it at section level — the Historical Container handles section-level history.

⸻

Draft Indicator

Purpose: Communicates unsaved changes or draft state in real time.
Required content: A subtle indicator showing unsaved-changes state or last-autosaved timestamp.
Interaction: Non-interactive unless the user can manually trigger a save — in which case a "Save now" link appears adjacent to the indicator during unsaved state.
Responsive: Metadata scale. Always present but never prominent. On mobile, may appear only during active editing.
Appropriate use: Workspace Header during active editing sessions.
Misuse: Do not use Draft Indicator as a primary status indicator. It is supplementary — the user should never feel anxious about losing work because of the absence or presence of this indicator.

⸻

4. Section Components

All section components share the anatomy defined in UX-012A Section 12. This section specifies the behavioral variants.

Standard Section

Anatomy: Section label (required) → Collapsed summary (required when collapsible, two-line maximum) → Expansion affordance → Expanded: headline + body + optional elements.
States: collapsed, expanded, collapsed-with-attention (when the section contains an unresolved state that requires the user's awareness even while collapsed).
Collapse behavior: The collapsed state always shows a meaningful two-line summary. Line 1 is the section's primary conclusion or most important single fact. Line 2 is the material implication or the most important supporting detail. The expansion affordance is a quiet directional indicator at the right edge.
Expansion behavior: Content reveals downward from the section header. The header remains fixed at the top of the expanded content. Surrounding sections reflow to accommodate.
Interaction: The entire collapsed header row is tappable/clickable as an expand trigger. Within the expanded body, individual elements have their own interaction.
Spacing: Inter-section spacing above and below. Intra-section spacing between content groups within the expanded body.
Hierarchy: The section label is Level 6. The headline is Level 2 (material implication) or Level 3 (supporting reasoning) depending on the section's position in the Workspace reading order. Body content varies by section type.

⸻

Reasoning Section

Extends Standard Section. Used for sections presenting Atlas-generated analytical content that the user reads but does not primarily author — thesis assessment, portfolio conclusions, supporting factors.
Additional anatomy: Source reference (optional, metadata scale). Confidence indicator (optional, metadata scale adjacent to or below the headline).
State additions: updated (when Atlas analysis has changed since last user visit — a small "Updated" label appears in metadata scale at the section label level).
Collapse behavior: The collapsed summary reflects the current Atlas conclusion, not a generic label. "The thesis remains intact — enterprise AI thesis and quality moat both holding" is a valid collapsed summary. "Investment analysis" is not.
Interaction: Read-only at the section level. Individual assumptions, evidence items, and supporting factors within the body may have their own interaction.

⸻

Read-Only Section

Extends Reasoning Section. Used for sections that contain no user-editable content and no interactive elements beyond expand/collapse — historical sections, locked conclusions, inherited context.
State additions: locked (when the content cannot be changed because it is a historical record or an inherited conclusion from another Workspace).
Visual distinction from Reasoning Section: Slightly reduced emphasis on the headline — secondary text color rather than primary. This signals "informational, not actionable."
Interaction: Expand/collapse only. No edit affordances.

⸻

Editable Section

Extends Standard Section. Used for sections where the user authors or modifies content — the decision statement, primary reason, assumptions, review conditions.
Additional anatomy: Edit affordance (appears on hover in desktop; persistent low-emphasis in mobile/tablet). AI suggestion indicator (appears after editing pause). Validation state (appears when content is materially unclear or incomplete).
States: inactive, editing, saved, AI-suggested (when the field contains Atlas-proposed content not yet confirmed by the user), user-modified (when Atlas content has been edited by the user).
Collapse behavior: The collapsed summary reflects the user's authored content when present — the first line of the decision statement, for example. When unpopulated, the collapsed summary shows the Atlas proposal summary if one exists, labeled as such.
Interaction: Tapping/clicking the body area or the edit affordance enters editing mode. The field expands to full-screen editing on mobile. Autosaves every 30 seconds. Five-second structural undo window for significant changes.

⸻

Comparison Section

Extends Standard Section. Used for sections that structure explicitly comparative content — Opportunity Cost, capital allocation alternatives, historical versus current.
Additional anatomy: Comparison rows (two or more parallel content blocks — the decision subject and its alternatives, or before/after states). Conclusion line (the synthesis statement at the bottom of the comparison — the most prominent text within the section).
Collapse behavior: The collapsed summary reflects the conclusion line — the synthesis, not a list of the alternatives. "Reducing LVMH and initiating Danaher is the most clearly supported reallocation" is a valid collapsed summary.
Layout: Two-column on desktop (decision subject and alternatives side by side). Sequential single-column on tablet and mobile (decision subject first, alternatives in order below, conclusion line at the end).
Interaction: Each alternative row may expand to show additional reasoning. The conclusion line is non-interactive.

⸻

Monitoring Section

Extends Standard Section. Used for sections that present ongoing observation conditions — monitoring conditions, review triggers, invalidation conditions.
Additional anatomy: Lifecycle state for each monitoring item (Active, Triggered, Resolved, Expired). Current condition indicator for each item (status of the monitored variable relative to the trigger threshold). Atlas reminder note (what Atlas will do when a trigger is met).
States: active (monitoring in progress), triggered (condition has been met — the section auto-expands and the triggered item is prominently displayed), all-resolved (no active monitoring — treated as a positive empty state).
Collapse behavior: Collapsed summary shows the count of active monitoring conditions and the most recently changed item. "2 conditions active · Enterprise AI capex: holding" is a valid collapsed summary.
Interaction: Each monitoring item expands to show its full definition and current condition. Triggered items show an acknowledgment control. Items may be edited in Editable variant of Monitoring Section.

⸻

Historical Section

Extends Read-Only Section. Used for prior records displayed within a current Workspace — prior decisions, prior conclusions, prior assumptions.
Visual treatment: All content in tertiary text color at reduced emphasis. The section surface has a subtle background distinction from surrounding content. A timestamp and version indicator appear in metadata scale at the top of the section.
States: historical-current (this is the most recent prior record), historical-superseded (this record has been superseded by a later record), historical-amended (this record has been modified by an amendment).
Collapse behavior: The collapsed summary shows the prior conclusion and the date. "Prior thesis: Intact · January 2025" is a valid collapsed summary.
Interaction: Expand/collapse only. The section may contain a "Compare with current →" link that opens a Historical Comparison component.
Immutability: No editing is possible within a Historical Section. The content is permanently locked at the time of recording.

⸻

Decision Section

Extends Editable Section. Used for the sections in the Decision Workspace that contain the user's primary authored commitment — the decision statement, primary reason, confidence assessment.
Additional anatomy: Atlas proposal block (the Atlas-proposed version of the content — distinct surface, "ATLAS SUGGESTS" label, secondary text weight). User decision field (the user's authored version — primary text weight, no label). Accept/modify controls for the Atlas proposal (appear in the proposal block's hover/focused state).
States: all standard Editable Section states, plus: atlas-proposed (content is Atlas-suggested, not yet user-confirmed), atlas-accepted (content is Atlas-suggested and has been accepted by the user, unedited — displayed as "Atlas Suggested / User Accepted"; authorship is not yet transferred), user-authored (user has written original content), user-modified-from-atlas (user has genuinely edited the Atlas proposal after acceptance).
Collapse behavior: The collapsed summary reflects the user's authored content when present. When only the Atlas proposal exists, the summary reflects the proposal with a subtle "Atlas proposed" qualifier.
Interaction: The user decision field is the primary authoring target. The Atlas proposal block is secondary — it can be accepted, modified, or ignored. If accepted, the content copies into the user decision field and becomes atlas-accepted state ("Atlas Suggested / User Accepted") — authorship is not yet transferred. Only a subsequent genuine edit to the copied content transitions it to user-modified-from-atlas state.

⸻

Completion Section

Used only at the bottom of the Workspace body, immediately above the footer. Contains the Final Decision Card (or equivalent final record), the completion gate explanation if the primary action is disabled, and contextual next steps in post-recording state.
States: pre-completion (primary action available or disabled), post-completion (decision recorded; body has cleared; Final Decision Card is the primary visible element).
Interaction: Contains no section-level expand/collapse. The Final Decision Card within it has its own interaction states. The completion gate explanation is non-interactive text.
Visual weight: This section receives more surrounding space than any other section in the Workspace — the inter-section spacing above it is increased to create a visual descent into the commitment moment.

⸻

5. Conclusion Components

Primary Conclusion

Purpose: Presents Atlas's most important interpretive statement for any Workspace or section — the single statement the user must not miss.
Required content: The conclusion statement (Level 1 typography — the largest body text in the Workspace). A source label in section-label scale ("ATLAS PORTFOLIO CONCLUSION," "ATLAS THESIS ASSESSMENT").
Optional content: A material implication line (Level 2 typography — immediately below the conclusion, in secondary text weight). Confidence indicator in metadata scale.
Priority: Always the first content in the scrolling body, or the first content in a section where it appears. No other content precedes it within its scope.
Placement: Full editorial column width. Strong container (elevated surface) when it is the anchor conclusion of a Workspace (Current Conclusion card in Decision Workspace, for example). Subtle or no container when it appears as the headline of a subordinate section.
Interaction: Non-interactive in its primary form. May contain an inline link to supporting analysis ("Based on Investment Workspace analysis →").
Historical behavior: When a prior version of the conclusion exists, a Historical Section shows the prior conclusion below the current one. The current conclusion is always shown first; history follows.
*(Boundary clarification per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02: this is a UX presentation artifact, not an independent Product Concept; no new Product meaning is established by this entry.)*

⸻

Current Conclusion

Extends Primary Conclusion. Specific to the Decision Workspace. The settled Atlas analysis that opens the Workspace body and grounds the decision.
Required content: The conclusion statement. The "ATLAS PORTFOLIO CONCLUSION" or equivalent label.
Visual treatment: Strong container (elevated surface, clear boundary, generous internal padding). The most visually significant element at the top of the scrolling body.
Interaction: Non-interactive as a block. May contain a "View full analysis →" link that opens the related Investment or Portfolio Workspace.
State: Always current — it reflects Atlas's most recent settled analysis. It updates between Workspace visits if Atlas has new analysis. When it updates, the Updated state of the Reasoning Section applies, with a note showing what changed.

⸻

Decision Required

Purpose: Communicates why a decision is being prompted — the trigger that makes this moment the appropriate time to decide.
Required content: A trigger type label ("THESIS CHANGE," "ASSUMPTION BROKEN," "PLANNED REVIEW," "MARKET CONDITION," etc.) in section-label scale. A trigger statement in secondary body text explaining the specific condition.
Optional content: An elaboration sentence explaining the implication of the trigger for the current investment or portfolio.
Priority: Level 2 in the Workspace reading order — always follows the Current Conclusion.
Placement: Inline in the scrolling body, full editorial column. Subtle visual distinction — a left-border rule in the appropriate semantic color (amber for thesis changes or broken assumptions; neutral for planned reviews).
Interaction: Non-interactive. The trigger statement may contain a link to the source of the trigger (the Investment Workspace section where the assumption broke, for example).
Historical behavior: The trigger is preserved as part of the decision record. When the decision is reviewed, the original trigger is shown alongside the original decision.

⸻

What Changed

Purpose: Presents material changes since the last analysis, decision, or review — a structured changelog of the most important recent developments.
Required content: A prioritized list of change items, each with a direction indicator (↑ increased, ↓ declined, → maintained, ◎ newly relevant), a headline, and a brief explanation.
Optional content: An expand control for additional lower-priority changes.
Priority: High — this component appears early in the Workspace reading order because understanding what has changed is prerequisite to forming a current judgment.
Placement: Full editorial column. Structured list layout.
Interaction: Primary changes (typically three) are always visible. Additional changes are behind an expand control ("View N additional changes"). Individual change items may expand to show additional reasoning.
Historical behavior: When the decision is recorded, the What Changed state at the time of recording is preserved in the decision record.

⸻

Portfolio Conclusion

Extends Primary Conclusion. Specific to the Portfolio Workspace. Presents the Atlas synthesis of the portfolio's current state.
Required content: The portfolio conclusion statement ("The portfolio remains structurally sound across seven of eight positions"). Source label ("ATLAS PORTFOLIO CONCLUSION").
Optional content: Primary issue and implication in a structured two-column label-and-statement layout (as specified in UX-007P).
Interaction: Non-interactive as a block. May link to the underlying analysis sections.
*(Boundary clarification per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02: per `UX-000-Atlas-UX-Doctrine.md` UXD-R-071 item 5, this remains a UX presentation artifact whose complete Product-layer correspondence is open pending future Investment Case / Portfolio Product Architecture treatment. This entry SHALL NOT be read as establishing Portfolio as an independent Product Concept.)*

⸻

Review Conclusion

Extends Primary Conclusion. Appears at the top of a Review Workspace or within the completion region of a Workspace being reviewed.
Required content: The review verdict ("THESIS VALID," "THESIS WEAKENED," "ASSUMPTION BROKEN," "DECISION SUPERSEDED"). The most important finding from the review.
Optional content: Comparison with the original conclusion ("Original thesis: Intact · January 2025 → Current assessment: Weakening").
States: Valid, Weakened, Broken, Superseded — each with the appropriate semantic color treatment (green, amber, red, neutral).
*(Clarified per the Atlas UX Architecture UX-012 Authority Migration task, 2026-08-02: per `UX-000-Atlas-UX-Doctrine.md` UXD-R-071 item 4 and UXD-R-086, this component MAY be populated only following a genuine, Investor-initiated Learning Act; a Review workflow or occasion, by itself, does not constitute or produce a Review Conclusion.)*

⸻

6. Reasoning Components

Supporting Factors

Purpose: Presents the evidence, conditions, intact assumptions, and portfolio alignment factors that support the primary conclusion.
Required content: A list of supporting items, each with a brief headline and optional expansion to supporting reasoning.
Optional content: A grouping of items by type (evidence, assumptions, alignment, historical consistency — the four supporting factor groups defined in UX-009A).
Priority: Level 3 in the information hierarchy. Presented after the conclusion and implication, before challenges.
Visual emphasis: Subtle — supporting factors do not compete with the conclusion for the user's primary attention. They are available for the user who wants to understand why the conclusion holds.
Interaction: Each item may expand to show additional reasoning or a link to the source.
Reuse rules: Used in Investment Workspace (thesis support), Portfolio Workspace (portfolio strengths), Decision Workspace (Section 5 — Supporting Factors). Not used in Dashboard.

⸻

Challenges

Purpose: Presents the conditions, assumptions, contradictions, or external factors that weaken, complicate, or challenge the primary conclusion.
Required content: A list of challenge items, each with a severity level (Informational, Material, Unresolved), a challenge statement, and an acknowledgment control when the severity is Material or Unresolved.
Optional content: An Atlas reasoning line beneath Material and Unresolved challenge items explaining why the challenge is significant. A link to the source of the challenge.
Priority: Level 4 in the information hierarchy. Presented after supporting factors — the user builds understanding of what is working before encountering what is not.
Visual treatment: Left-border rule in amber at three opacity levels corresponding to the three severity tiers. See Section 14 (Feedback Components) for the severity model.
Interaction: Informational challenges: expand/collapse. Material challenges: expand/collapse plus visible acknowledgment control. Unresolved challenges: expand/collapse plus acknowledgment control that requires deliberate interaction (not a one-tap dismiss).
Reuse rules: Used in Investment Workspace (thesis challenges), Portfolio Workspace (portfolio weaknesses), Decision Workspace (Section 6 — Challenges). One of the most widely reused components in the system.

⸻

Assumptions

Purpose: Presents the specific conditions that must remain true for the conclusion or decision to hold. Each assumption has a status, a definition, and optionally a linked monitoring condition.
Required content: Assumption statement. Status indicator (Holding, Under Review, Weakening, Broken). Left-border rule in the semantic color of the status.
Optional content: Supporting reasoning (expanded). Linked monitoring condition. Comment field. Last-reviewed timestamp.
States: Holding (green border), Under Review (amber border, reduced opacity), Weakening (amber border, full opacity), Broken (restrained red border). Each state is communicated by both the border color and a text label in metadata scale.
Lifecycle: An assumption begins as Holding when established. It moves to Under Review when new information warrants attention. It moves to Weakening when evidence suggests the condition is deteriorating. It moves to Broken when the condition has definitively failed — this state auto-expands the containing section and marks the assumption as requiring acknowledgment.
Interaction: Expand/collapse. Editable when in an Editable Section. Linkable to a Monitoring Condition. When Broken, the acknowledgment control becomes prominent.
Reuse rules: Used in Decision Workspace (Section 9), Investment Workspace (thesis assumptions), future Review Workspace. One of the highest-reuse components in the system.

⸻

Invalidation Condition

Purpose: Presents the specific, observable conditions that would render the decision or thesis invalid and require revisiting. Distinct from assumptions (which may weaken gradually) and monitoring conditions (which Atlas observes). Invalidation conditions are authored by the user and represent their own stated decision rules.
Required content: The invalidation condition statement — observable, specific, and verifiable. A status indicator (Not Met, Approaching, Met).
Optional content: A monitoring link ("Atlas will alert you if this approaches"). A review date.
Visual treatment: Slightly more prominent than assumption rows — a slightly heavier left-border rule and a marginally larger statement size. These are the conditions that govern the decision's future validity.
Interaction: Editable when first established. Read-only once the decision is recorded (the condition is locked as part of the record). The status updates through monitoring, not through user editing.
States: Not Met (default), Approaching (amber — Atlas has detected movement toward the condition), Met (red — the condition has been triggered; the decision requires review).
Reuse rules: Decision Workspace (Section 9). Future Review Workspace. May appear in a monitoring summary in the Dashboard.

⸻

Portfolio Consequences

Purpose: Presents the structural changes to the portfolio that would result from the proposed decision — position sizing, concentration effects, dependency changes.
Required content: A set of before/after consequence rows. Each row: a consequence subject (position name or portfolio dimension), a before value, a directional indicator (→), an after value.
Optional content: A dependency-affected note (when the consequence changes a shared portfolio risk dependency). A summary line (the most important consequence synthesized into one sentence).
Priority: Level 3 within the Decision Workspace. Presented as an analytical section, not as a dashboard.
Visual treatment: No charts. No visualization. Typographic before/after comparison — the before value in secondary text, the after value in primary text. The user reads the change through text, not through a graphic that implies precision.
Interaction: Each consequence row may expand to show a brief explanation of why the change matters. The summary line is non-interactive.
Reuse rules: Decision Workspace (Section 8). Portfolio Workspace (capital allocation section). May appear in condensed form in a decision summary component.

⸻

Opportunity Summary

Purpose: Presents the comparative reasoning between the proposed decision and its most relevant alternatives — a qualitative synthesis of why one path is preferred over others.
Required content: The decision subject row (proposed decision, Atlas conviction summary). Alternative rows (each with an Atlas comparison line). The conclusion line (the synthesis of the comparison — the most prominent text within the section).
Optional content: User note field within each alternative row. "Explore →" link on each alternative row.
Visual treatment: See UX-011 Section 12. Qualitative prose comparison — no numeric scores, no rankings, no green/red treatment. The conclusion line is the highest-emphasis text within the section.
Interaction: Each alternative row may expand to show deeper comparison reasoning. The "Explore →" control on each alternative opens the relevant Investment Workspace or portfolio section. The conclusion line is non-interactive.
Reuse rules: Decision Workspace (Section 7 — Opportunity Cost). Portfolio Workspace (capital allocation alternatives). One of the signature Atlas components.

⸻

Implementation Summary

Purpose: Presents the implementation intent associated with a decision — what the user intends to do, when, and under what conditions — as a secondary, visually subordinate record.
Required content: Implementation type (Reduce Position, Add to Position, Initiate Position, No Action, Monitor). Target allocation or quantity when applicable.
Optional content: Timeline. Conditions for execution. Contingency. Linked order management reference.
Visual treatment: Visually subordinate to the decision record. Secondary text scale for labels; primary text scale for user-entered values. No prominent containers.
States: Pending (implementation not yet executed), Partially Executed, Complete, Not Required (for No Action type).
Interaction: Editable throughout the implementation lifecycle — the implementation state evolves without modifying the recorded decision reasoning. Implementation history is tracked separately.
Reuse rules: Decision Workspace (Section 10). Dashboard (implementation follow-up signal). Future Implementation Tracking Workspace.

⸻

Review Condition

Purpose: Presents the plan for when and why this decision will be reconsidered — the trigger condition and the expected review date.
Required content: Review trigger type. Review trigger statement.
Optional content: Expected review date. Linked monitoring condition ("Atlas will surface this when [condition]"). Atlas reminder note.
States: Active, Triggered (the condition has been met — the review is due), Completed.
Interaction: Editable when first established. The trigger links to a Monitoring Condition when applicable. When Triggered, the component becomes more prominent and displays an "Open Review →" control.
Reuse rules: Decision Workspace (Section 11). Decision Summary component (embedded). Dashboard (monitoring signal when triggered).

⸻

7. Comparison Components

Before / After

Purpose: Presents a structural change as a two-state comparison — the prior state and the resulting state.
Structure: A subject label. A before value in secondary text weight. A directional arrow (→) in tertiary text. An after value in primary text weight. An optional significance note in metadata scale.
Interaction: Non-interactive by default. May expand to show a brief explanation of the change.
Reading order: Subject → before → arrow → after. Always left-to-right on desktop; stacked (subject, then before → after on one line) on mobile.
Expansion behavior: Expanding reveals the significance explanation. The before/after line remains visible above the explanation.
Reuse rules: Portfolio Consequences component (Section 8 — Decision Workspace). Portfolio Workspace capital allocation section. Historical Comparison component.

⸻

Alternative Comparison

Purpose: Presents a structured comparison between the proposed action and one or more alternatives, emphasizing reasoning over scoring.
Structure: Decision subject row (slightly elevated treatment). One or more alternative rows (each with: alternative label, Atlas comparison line in secondary text, user note field). Conclusion line (synthesis — the highest-emphasis text in the component).
Interaction: Each alternative row may expand. Conclusion line is non-interactive. Desktop: two-column layout (subject and alternatives side by side). Tablet and mobile: sequential single-column.
Reading order: Decision subject first, alternatives in order of Atlas-assessed relevance, conclusion line last.
Expansion behavior: Alternative rows expand to reveal deeper reasoning. The surrounding alternatives remain visible (the expansion is within the row, not a takeover).
Reuse rules: Opportunity Cost section (Decision Workspace). Capital allocation alternatives (Portfolio Workspace).

⸻

Opportunity Cost

Extends Alternative Comparison. The full Opportunity Cost section of the Decision Workspace — includes the decision subject, all identified alternatives, the conclusion line, and the user note fields.
Specific requirements: No numeric scoring. No ranking symbols. No color treatment for "better" or "worse" alternatives — the Atlas comparison line communicates reasoning, not verdict. The conclusion line uses the second-largest body text in the section.
Signature status: One of the six signature Atlas visual moments (per UX-011 Section 30). Its qualitative, reasoning-first presentation is a defining characteristic of Atlas.

⸻

Scenario Comparison (Historical Experimental Concept — Not an Adopted Comparison Component; see Correction Notice, Phase 3E, above)

The following describes a card-grid presentation concept explored at this document's original Experimental maturity stage and never promoted into adopted shared architecture. It is retained here as historical design evidence, not as a live Comparison component; its own scenario-specific content (scenario naming, outcome framing, detail) is owned by Scenario Analysis (`UX-013B-Atlas-Component-Specification-Reasoning-Components.md` §9), not by Comparison.

Purpose: Presents multiple scenarios (economic, thesis, or market) as a structured comparison of outcomes and portfolio impacts.
Structure: Each scenario card: scenario name, outcome label (with semantic color), consequence line, optional detail (behind expand). Cards arranged in a consistent grid (typically two or three columns on desktop, single column on mobile).
Interaction: Each card may expand to show additional scenario detail and the specific portfolio consequence.
Visual treatment: The outcome label (the most important line on each card) receives the highest emphasis within the card. The consequence line is secondary. Scenario name is tertiary.
Reuse rules (historical): Portfolio Workspace (scenario analysis section). Investment Workspace (scenario section). Decision Workspace (scenario context when relevant to the decision).

⸻

Allocation Comparison

Purpose: Presents portfolio allocation data as a comparative structured view — current allocation versus proposed or target allocation.
Structure: A set of rows, each with: a position label, current allocation percentage, directional indicator, proposed allocation percentage, and optionally a note.
Interaction: Rows may expand to show reasoning. Non-interactive by default.
Visual treatment: Typographic table — no bar charts, no pie segments. The numbers are in body text scale; the directional indicator is in tertiary text.
Reuse rules: Portfolio Workspace (capital allocation section). Decision Workspace (portfolio consequences when showing allocation changes).

⸻

Historical Comparison

Purpose: Presents a comparison between a prior state and the current state — prior conclusion alongside current conclusion, prior decision alongside amended decision.
Structure: Prior state block (tertiary text color, reduced opacity, timestamp label). Current state block (primary text color, full opacity). A separator between them (hairline rule or clear spatial gap).
Interaction: Expand/collapse. A "What changed" link may appear in metadata scale.
Reading order: Current state first, prior state below — the user's primary reference is the present.
Reuse rules: Decision Workspace (historical decision panel in review mode). Investment Workspace (thesis evolution section). Portfolio Workspace (historical portfolio assessment).

⸻

8. Decision Components

Proposed Decision

Purpose: Presents the Atlas-proposed version of the user's decision — the suggestion derived from Atlas's analysis of the investment and portfolio context.
Required content: "ATLAS SUGGESTS" label in section-label scale. The proposed decision statement in secondary text weight on a subtle panel surface. The primary reason for the proposal in secondary body text.
Optional content: A condensed opportunity cost note ("Over maintaining current position or initiating Danaher"). Accept, Modify, and Ignore controls.
States: Pending (user has not yet interacted with the proposal), Accepted (user has confirmed the proposal as their decision), Modified (user has edited the proposal), Ignored (user has written a different decision).
Interaction: Accept copies the proposal into the user decision field, entering Accepted state ("Atlas Suggested / User Accepted" — authorship is not yet transferred). Modify opens the user decision field with the proposal pre-populated for editing; a genuine edit to the field transitions it to user-modified-from-atlas state. Ignore keeps the proposal visible but moves focus to the empty user decision field.
Visual treatment: Clearly subordinate to the user decision field above it. Contained within a panel-surface block with the "ATLAS SUGGESTS" label. Not as visually prominent as the user's authored decision.
Reuse rules: Decision Workspace (Section 3 — Proposed Decision). Must not appear outside this context — the proposal is specific to the moment of decision formation.

⸻

Final Decision Card

Purpose: The permanent visual record of the user's completed decision — the six-field summary (decision, primary reason, confidence, invalidation condition, implementation intent, review condition) assembled into one settled document card.
Required content: The decision statement (primary text weight, body text scale). The primary reason (secondary text weight). The confidence assessment (metadata scale). The key invalidation condition (secondary text). The implementation intent (secondary text, subordinate). The review condition (secondary text).
Optional content: A timestamp and recording date. A source attribution ("Based on [Workspace name] analysis").
States: Draft/live-updating (fields show placeholder text for unpopulated items; values update in real time as the user works through the Workspace above); Completed/recorded (all six fields populated in full primary text weight and color; the card acquires its permanent visual authority).
Visual treatment: Strong container — elevated surface, generous internal padding, clear boundary. One of the most visually significant elements in the system. In post-recording state, the card is the primary visible element in the cleared Workspace body.
Interaction: In draft state — non-interactive (the card updates as a live preview while the user edits above). In recorded state — read-only within the Decision Workspace; may link to a full Decision Record view.
Signature status: The Final Decision Card is one of the six signature Atlas UI moments. Its visual authority is achieved through simplicity, space, and the completeness of its settled form.
Reuse rules: Decision Workspace (Section 12 and post-recording state). Decision Summary component (condensed variant). Dashboard (compact variant in briefing). Investment and Portfolio Workspace (when displaying prior decisions).

⸻

Decision Summary

Purpose: A portable, condensed representation of a recorded decision — suitable for embedding in Dashboard briefings, Investment Workspace prior decisions sections, and Portfolio Workspace context panels.
Required content: Decision statement (primary text weight, slightly reduced scale from the full Final Decision Card). Subject name. Recording date. Implementation state indicator.
Optional content: Primary reason (secondary text weight, truncated if necessary). Review condition (metadata scale). Confidence label (metadata scale).
States: Active (the decision is the current governing commitment), Due for Review (the review condition has been triggered), Historical (the decision has been superseded or closed out).
Interaction: Tapping/clicking the Decision Summary opens the full Decision Record view (read-only). In active state, an "Open Decision →" link is visible.
Reuse rules: Dashboard (daily briefing signal). Investment Workspace (prior decisions section). Portfolio Workspace (capital allocation context). Decision Workspace (related decisions section). This is one of the most widely reused decision components.

⸻

Decision History

Purpose: Presents the complete sequence of decisions related to one subject — initial decision, amendments, reviews, superseding decisions — in chronological order.
Required content: Each entry: decision type label, recording date, decision statement (truncated), current status (Active, Superseded, Closed).
Optional content: Expand each entry to show the full Decision Summary. A visual timeline indicator showing the chronological relationship.
Interaction: Each entry expands to show the Decision Summary component. The expanded view may contain a "Compare with current →" link.
Reading order: Most recent first.
Reuse rules: Investment Workspace (historical decisions section). Decision Workspace (in review mode). Future Decision Review Workspace.

⸻

Decision Amendment

Purpose: Represents a modification to a recorded decision — a change to the primary reason, confidence, or implementation intent — without superseding the core decision.
Required content: Amendment type label ("AMENDMENT"). The field that was changed, shown as a before/after comparison. The reason for the amendment. Recording date.
Visual treatment: Historical treatment for the prior state (tertiary text); primary treatment for the amended state. A clear relationship to the original decision.
States: Current (this is the most recent amendment), Superseded (a later amendment has been made).
Reuse rules: Decision History component. Decision Workspace (version history panel).

⸻

Decision Review

Purpose: Represents a completed review of a prior decision — the verdict, the key finding, and any resulting changes.
Required content: Review verdict (THESIS VALID, THESIS WEAKENED, ASSUMPTION BROKEN, DECISION SUPERSEDED). Key finding sentence. Review date.
Optional content: What changed since the original decision. Next review condition.
States: Complete, Superseded.
Reuse rules: Decision History component. Dashboard (past reviews in briefing context). Future Review Workspace.

⸻

9. Monitoring Components

Monitoring Condition

Purpose: Represents a specific, defined state that Atlas is actively observing — linked to a prior decision, assumption, or thesis element.
Required content: The condition statement (what Atlas is observing). The trigger threshold (the specific value or event that would activate the trigger). Current condition status (the current observed state relative to the trigger).
Optional content: Linked decision or assumption. Expected observation cadence. History of prior condition states.
States: Active (observation ongoing, condition not approaching trigger), Approaching (condition is moving toward the trigger threshold — amber treatment), Triggered (the condition has met the trigger — the item auto-surfaces in Dashboard and expands in its containing section), Resolved (the trigger was met and has been acknowledged and addressed), Expired (the decision the condition was linked to has been superseded or closed).
Lifecycle: Established → Active → (Approaching) → Triggered → Acknowledged → Resolved.
Interaction: Active: expand to view the full condition and current status. Approaching: expand automatically. Triggered: expand automatically; shows an acknowledgment control and a link to the associated decision or Workspace.
Reuse rules: Decision Workspace (Section 9). Dashboard (monitoring signal). Future Monitoring Workspace. Investment Workspace (linked to thesis assumptions).

⸻

Review Trigger

Extends Monitoring Condition. A monitoring condition whose activation reopens a specific prior decision for review.
Additional required content: The linked decision (a Decision Summary component showing the decision being monitored). The review action ("Atlas will open a Decision Workspace for this decision when this trigger is met").
State addition: Due for Review (triggered state for a review trigger — the associated decision transitions to Due for Review state and appears prominently in Dashboard).
Reuse rules: Decision Workspace (review plan, Section 11). Dashboard (due-for-review signal).

⸻

Invalidation Trigger

Extends Monitoring Condition. A monitoring condition linked to an Invalidation Condition — one that, when triggered, signals that the fundamental basis of the decision may no longer hold.
Additional treatment: Higher visual prominence than standard Monitoring Condition in triggered state — amber treatment transitions to restrained red. The trigger announcement in Dashboard uses stronger language: "A condition you identified as potentially invalidating this decision has been met."
Reuse rules: Decision Workspace (invalidation conditions, Section 9). Dashboard (invalidation signal).

⸻

Implementation Follow-up

Purpose: Represents an outstanding implementation action linked to a recorded decision — a reminder that execution is pending.
Required content: Implementation action description. Linked decision (Decision Summary). Status (Pending, In Progress, Complete).
Interaction: Acknowledging the follow-up marks it as seen. Completing it transitions the linked decision's implementation state to Complete.
Reuse rules: Dashboard (implementation follow-up signal). Decision Workspace (implementation section state).

⸻

Scheduled Review

Purpose: A time-based review trigger — a future date at which Atlas will surface the associated decision for review regardless of condition-based triggers.
Required content: The scheduled review date. The review type ("Annual review," "Six-month check-in," etc.). The linked decision.
State: Upcoming (more than two weeks away — quiet), Due Soon (within two weeks — amber treatment), Overdue (past the scheduled date without completion — red treatment).
Reuse rules: Decision Workspace (review plan). Dashboard (upcoming review signal).

⸻

10. Historical Components

Historical Record

Purpose: The base component for any prior state presented within a current context — the visual treatment that distinguishes past from present.
Visual treatment: Tertiary text color. Reduced opacity surface (subtle background distinction from surrounding current content). Timestamp and version indicator in metadata scale at the top. All content is read-only.
Required content: Timestamp. Record type label ("PRIOR DECISION," "PRIOR CONCLUSION," etc.). The content of the prior record at its original level of detail.
Interaction: Expand/collapse only. "Compare with current →" link when comparison is relevant.
Immutability: The content of a Historical Record is permanently locked. No editing is possible. The original wording, confidence, and metadata are preserved exactly as recorded.

⸻

Historical Decision

Extends Historical Record and Decision Summary. The embedded representation of a prior decision in historical context.
Required content: All Decision Summary fields. The recording date. The decision's current status (Superseded, Closed, Active — though in Historical context, Active indicates this is the most recent record).
Interaction: Expand to show the full prior decision. "Compare with current decision →" when a current active decision exists.

⸻

Historical Review

Extends Historical Record. The prior review record shown in historical context.
Required content: Review verdict. Key finding. Review date. The previous state of the decision at review time.
Interaction: Expand to show the full review record. "View resulting changes →" when the review produced an amendment or superseding decision.

⸻

Historical Assumption

Extends Historical Record. A prior assumption state shown in historical context — when an assumption has been updated or broken and the user wants to understand the original state.
Required content: The original assumption statement. The status at the time of recording. The date the assumption was last confirmed.

⸻

Historical Comparison

A composed component that presents a Historical Record alongside its current equivalent for direct comparison. See Section 7 — Comparison Components.

⸻

Historical Timeline Entry

Purpose: A compact representation of one event in a decision's history — suitable for display in a chronological timeline or version history panel.
Required content: Event type label (Decision Recorded, Amended, Review Completed, Superseded, Monitoring Triggered). Date. A one-line summary of the event.
Interaction: Tapping/clicking expands to the relevant Historical component (Historical Decision, Historical Review, etc.).
Reuse rules: Decision History component. Version history panel in Decision Workspace.

⸻

11. AI Collaboration Components

Atlas Suggestion

Purpose: Presents a specific Atlas-generated improvement proposal for a user-authored or user-editable field — a concrete alternative wording, a missing element, a precision improvement.
Required content: "ATLAS SUGGESTS" label in section-label scale. The suggested content in secondary text weight. The reason for the suggestion in metadata scale ("This adds a specific observable condition to the review trigger").
Optional content: A "View difference →" control that shows a before/after comparison of the current content versus the suggestion. Accept, Partial Accept, Dismiss controls.
Trigger: Appears after a defined editing pause (approximately 1.5 seconds of inactivity following the user's most recent edit). Never appears while the user is actively typing. Appears at most once per editing session per field.
Placement: Below the field it addresses, on a panel-surface block. Not as an overlay or modal.
Dismiss behavior: Dismissing removes the suggestion immediately. The suggestion does not reappear during the current editing session.
Accept behavior: Accepting replaces the field content with the suggestion. The field transitions to Accepted state ("Atlas Suggested / User Accepted") — authorship is not yet transferred; only a subsequent genuine edit transitions it to user-modified-from-atlas state. A five-second undo control appears.
Partial accept behavior: A partial accept mode shows the suggestion with selectable segments. The user confirms individual sentences or clauses. The confirmed selections assemble in the field.
Editing behavior: If the user edits the field after the suggestion appears without accepting or dismissing, the suggestion panel dims and then disappears after a short delay.
Historical behavior: Suggestions are not preserved in the decision record. Only the final content of the field — whatever the user authored or confirmed — is recorded.

⸻

Atlas Insight

Purpose: Presents a broader interpretive observation from Atlas — not a suggestion for specific field content, but a contextual interpretation relevant to the user's current reasoning.
Required content: A brief label identifying the insight type ("RELATED PATTERN," "HISTORICAL PARALLEL," "PORTFOLIO CONTEXT"). The insight statement in secondary body text. A source reference or link to underlying analysis.
Placement: At the section level — at the bottom of a section's expanded content, or as a section-level indicator that collapses into the section label.
Priority: Lower than Atlas Suggestion — an Insight does not require the user to accept or dismiss; it is informational.
Interaction: Expand/collapse. A "View analysis →" link when the Insight refers to specific underlying content.
Historical behavior: An Insight surfaced during a decision session may be noted in the session context but is not preserved in the decision record.

⸻

Atlas Warning

Purpose: Presents a conflict, inconsistency, or concern that Atlas has identified in the user's current reasoning — the AI Collaboration form of a challenge or contradiction.
Required content: A warning type label ("CONTRADICTS PRIOR REASONING," "INCREASES CONCENTRATION," "VAGUE REVIEW CONDITION"). The warning statement in secondary body text. An explanation of why this matters.
Severity: Follows the three-level contradiction model — Informational, Material, Unresolved. Visual treatment matches the Challenges component severity tiers.
Interaction: May be acknowledged (the user has seen it and is proceeding deliberately) or addressed (the user modifies their reasoning in response). The warning is never blocking except in the specific case of Unresolved status affecting the completion gate.
Historical behavior: Material and Unresolved warnings that were acknowledged but not addressed are noted in the decision record's session context.

⸻

Atlas Recommendation

Purpose: Presents a broader Atlas suggestion at the decision or portfolio level — not a field-specific suggestion but a strategic recommendation ("Consider completing the LVMH review before recording this decision").
Required content: Recommendation statement. The reasoning behind the recommendation.
Priority: Higher than an Insight; lower than a Warning. A Recommendation draws attention but does not interrupt.
Placement: At the section level within the relevant section, or within the footer area as a pre-completion note.
Interaction: Accept, Defer, or Dismiss.

⸻

Atlas Clarification

Purpose: A question Atlas poses to the user — used when the user's input is ambiguous and clarification would improve the quality of Atlas's assistance.
Required content: The clarifying question. Two to three suggested response paths (not required answers — the user may always type a different response).
Placement: Inline, immediately below the field or element that prompted the question. Not as a modal or popup.
Interaction: The user selects a response path or types a custom response. Atlas updates its analysis accordingly. The clarification is not recorded in the decision record.

⸻

Atlas Summary

Purpose: A system-generated summary of the user's current decision state — useful when a long editing session has produced complex content and the user wants to see the assembled picture.
Required content: A concise synthesis of the current state of the key decision fields. Source attribution ("Based on your current inputs").
Placement: At the top of the Completion Section, above the Final Decision Card, during complex editing sessions.
Interaction: Accept and proceed, or return to edit a specific field (the field link opens the field in editing mode).

⸻

12. Editing Components

Long-form Editor

Purpose: The editing surface for extended prose content — the decision statement, primary reason, thesis statement, and other multi-sentence authored fields.
States: Inactive (placeholder text in tertiary color, no border, no background — field is invisible in the document until focused); Hover (edit control appears adjacent to the field; no background change); Focused (subtle underline or left-border rule activates; surrounding document dims at 5–8% opacity; cursor is a text cursor); Editing (user is actively writing; the field expands to accommodate content; autosave indicator is active); Saved (content is in primary text weight and color, indistinguishable from static document text when not focused); Atlas-generated (secondary text weight; "ATLAS SUGGESTS" label above the content); User-modified-from-atlas (primary text weight; a "Modified from Atlas suggestion" note in metadata scale below the field); Read-only (primary text weight and color; no edit control on hover; locked treatment in historical context).
Validation: Does not use error states for incomplete content. Uses soft friction — the completion gate explanation in the footer references the field, and an "Add primary reason →" link navigates to the field. The field itself does not turn red.
AI collaboration: The Atlas Suggestion component may appear below the field. The Atlas Clarification component may appear below the field.
Autosave: Every 30 seconds during active editing. Unsaved changes are indicated by the Draft Indicator in the Workspace Header.
History: Prior versions of the field content are accessible in the version history panel. The field does not show version history inline.
Undo: A five-second undo window for significant structural changes (deleting a paragraph, accepting an Atlas suggestion). Standard OS undo for character-level editing.
Read-only mode: In recorded/historical state, the field renders as static document text. No editing is possible.

⸻

Short Statement

Extends Long-form Editor. For concise, single-sentence inputs — assumption statements, invalidation condition statements, review trigger descriptions.
Behavioral differences: Does not expand to full-screen on mobile. Remains single-line unless the content wraps. Autosave on field blur rather than on interval. Atlas Suggestion may offer a complete replacement of the short statement rather than a partial suggestion.

⸻

Decision Field

Extends Long-form Editor. The primary decision statement field in the Decision Workspace — the single most important authored element in the entire system.
Specific treatment: The largest editable field in any Atlas surface. When focused, the surrounding document dims more noticeably than standard Long-form Editor fields — the field is the center of the document. In inactive state with Atlas-generated content, the field shows the proposed decision in secondary weight with "ATLAS SUGGESTS" above it and the user decision field (empty with placeholder) above the proposal block. The visual hierarchy (user field first, Atlas proposal below) is maintained regardless of which has content.
Signature status: The moment the user begins writing in the Decision Field is one of the six signature Atlas visual moments.

⸻

Structured Comparison Editor

Purpose: For editing structured rows within a comparison — opportunity cost alternative rows, assumption rows, portfolio consequence rows.
States: Inactive (the row is read-only in its standard collapsed state), Editing (the row expands to show editable fields within the comparison structure), Saved.
Interaction: The edit affordance (on hover) opens the row in editing mode. Individual fields within the row use Short Statement or Long-form Editor as appropriate.

⸻

Assumption Editor

Extends Structured Comparison Editor. For editing assumption statements and their associated fields.
Specific fields: Assumption statement (Short Statement). Status selector (qualitative choice — Holding, Under Review, Weakening, Broken). Supporting reasoning (Long-form Editor, optional). Comment (Long-form Editor, optional). Monitoring condition link (select from existing monitoring conditions or create new).

⸻

Implementation Editor

Extends Structured Comparison Editor. For editing implementation intent fields.
Specific fields: Implementation type selector. Target allocation (Short Statement). Timeline (Short Statement, optional). Conditions (Long-form Editor, optional). Note: Implementation fields are editable after the decision is recorded — they represent execution state, not the decision record itself.

⸻

13. State Components

The following states apply to Atlas objects (decisions, assumptions, monitoring conditions, Workspaces) and to interface components. States are communicated through text labels, typographic treatment, and semantic color — never through color alone.

Draft: The object or content is in active preparation and has not been recorded or submitted. Visual treatment: Draft Indicator in the Workspace Header; the primary action is available but secondary to the completion flow.

Saved: The draft state has been explicitly saved. Visual treatment: Draft Indicator shows last-saved timestamp.

Unsaved: Changes exist that have not been saved. Visual treatment: Draft Indicator shows unsaved-changes indicator.

Under Review: The object is actively being examined — an assumption is being assessed, a decision is being reviewed. Visual treatment: Amber treatment at metadata scale.

Monitoring: Atlas is actively observing conditions linked to this object. Visual treatment: A small "MONITORING" label in metadata scale; the Monitoring Condition component linked to the object.

Completed: The reasoning or review process has reached its conclusion and been recorded. Visual treatment: The completion state — the Final Decision Card in its recorded form.

Recorded: A decision has been formally recorded and is now permanent. Visual treatment: The full recorded state — Final Decision Card, read-only fields, historical treatment applied to prior states.

Historical: The object is a prior record, not the current active state. Visual treatment: Tertiary text color, reduced opacity, timestamp label.

Updated: Atlas has new analysis or the object's state has changed since the user's last visit. Visual treatment: A small "UPDATED" label in metadata scale at the section label level.

Requires Attention: The object has an unresolved state that warrants the user's awareness — a broken assumption, a triggered monitoring condition, a material contradiction. Visual treatment: Amber treatment at the section label level; the containing section has the collapsed-with-attention state.

Deferred: The user has deliberately postponed a decision or action. Visual treatment: Neutral, slightly reduced emphasis — this is an intentional state, not a failure.

Superseded: The object has been replaced by a later version. Visual treatment: Historical treatment with a "SUPERSEDED" label and a link to the current active version.

⸻

14. Feedback Components

Feedback components communicate information to the user about system state, content state, or reasoning quality. They follow the Atlas tone — calm, direct, honest about uncertainty, proportional in urgency.

Informational:
Used for: low-priority observations, system activity notes, Atlas insights that do not require action.
Behavior: Appears inline or at the section level. Does not interrupt reading. May be dismissed or ignored without consequence.
Timing: Present for the duration of relevance. Dismissed on user action or when the condition resolves.
Visual treatment: No special color treatment. Secondary text scale.

Reminder:
Used for: upcoming reviews, incomplete optional fields, Atlas clarifications.
Behavior: Inline, non-interrupting. A gentle note rather than a warning. May be acknowledged without completing the action.
Visual treatment: Neutral. No semantic color. The tone is "when you're ready" rather than "you must act."

Warning:
Used for: material contradictions, broken assumptions affecting the current decision, concentration increases that conflict with portfolio strategy.
Behavior: The containing section auto-expands. The warning item is visually prominent within the section. An acknowledgment control is present. Does not block progress.
Visual treatment: Amber left-border rule at medium opacity. Amber label in metadata scale. Secondary text for the warning statement.
Timing: Persistent until acknowledged. Acknowledgment is recorded in the session context.

Material Concern:
Used for: unresolved contradictions, decisions that would break a defined portfolio strategy, missing required fields that affect decision quality.
Behavior: The containing section auto-expands. The concern is prominently displayed. The acknowledgment control requires deliberate interaction. May produce a completion gate note (the primary action explanation references the concern) without blocking recording.
Visual treatment: Amber left-border rule at full opacity. Amber label at medium emphasis. The acknowledgment control is larger than for a standard Warning.

Blocking Issue:
Used for: conditions that prevent the primary action from becoming available — incomplete required fields, unresolved states that make the decision incoherent.
Behavior: The primary action (Record Decision) remains unavailable (`aria-disabled="true"`, never native `disabled`). The footer explanation references the specific blocking condition. An "Auto-scroll to [field] →" link navigates the user to the specific element that must be addressed. *(Corrected per ADR-002/C-06, Phase 6C — 2026-07-29: this line previously used "disabled" without qualification.)*
Visual treatment: The footer explanation uses secondary body text, not error styling. The tone is "this is what's still needed" not "you made an error."

Validation:
Used for: field-level content that is too vague to serve as a review trigger or invalidation condition.
Behavior: A soft, inline note below the field — "This condition may be difficult for Atlas to monitor objectively. Consider adding a specific observable threshold." Not an error state. The field does not change color.
Visual treatment: Secondary text scale, tertiary color. A subtle improvement suggestion, not a failure indicator.

Loading:
Used for: Atlas analysis updating, portfolio recalculation in progress, source comparison loading, decision record saving.
Behavior: A minimal loading indicator at the element level — not a full-page spinner. The element shows its last-known state while loading; a small loading indicator appears adjacent to the element. If loading takes more than three seconds, a brief text note appears ("Updating analysis...") at secondary text scale.
Visual treatment: No theatrical animation. No skeleton screens with shimmer. The loading state is honest and minimal.

Empty State:
Used for: sections with no current content — no contradictions identified, no monitoring conditions active, no historical decisions.
Behavior: A complete, intentional statement in secondary text ("No conflicts identified for this decision."). Optional explanatory note in tertiary text. The section has the same structural presence as a populated section.
Types: Positive absence ("No contradictions identified"), unavailable result ("Analysis not yet available for this investment"), incomplete data ("Some portfolio data is incomplete — results may be approximate"), user action required ("Add a review condition to enable this section").
Visual treatment: Never looks like an error. Never has a placeholder illustration. The statement is the content.

⸻

15. Action Components

Primary Action

Purpose: The single dominant action available at the current stage of the Workspace — the terminal point of the current reasoning flow.
Placement: Fixed footer, right-aligned (or full-width on mobile). One per footer region at any time.
Emphasis: Clearly the highest-emphasis action control — defined surface or clear outline at primary text color. Not a filled bright button. The visual weight communicates "this is the conclusion of a process" rather than "click me."
States: Available (the user may proceed), Disabled (conditions not yet met — rendered at 40–45% opacity, not-allowed cursor, adjacent explanation text).
Naming convention: Verb + Noun, specific to the action. "Record Decision" not "Submit." "Complete Review" not "Done." "Open Workspace" not "Go."
Keyboard: Activated by Enter when focus is in the footer region.
Mobile: Full-width. Within thumb reach at the bottom safe area.
Misuse: Do not create multiple Primary Actions in one footer. Do not use the Primary Action style for secondary actions.

⸻

Secondary Action

Purpose: A useful but non-dominant action available alongside the primary action.
Placement: Fixed footer, adjacent to or below the Primary Action. Never positioned to compete visually.
Emphasis: Clearly lower visual weight than the Primary Action — a link-style treatment or a minimal outline at secondary text weight.
Examples: "Save Draft," "Return to Analysis," "Compare Alternatives."
States: Available, disabled (rare — secondary actions are usually always available).
Naming convention: Same convention as Primary Action — Verb + Noun.
Keyboard: Accessible via Tab from the Primary Action.

⸻

Inline Action

Purpose: A low-emphasis action embedded within body content — triggering expansion, editing, dismissal, or navigation within a section or component.
Placement: Adjacent to the element it acts on. Not in the footer. Not in the header.
Emphasis: Tertiary — visible on hover or as a persistent low-emphasis element. Does not draw the eye during primary reading.
Examples: "Edit," "View source →," "Dismiss," "View difference →," "Explore →."
States: Default (visible), hover (slightly more prominent), activated (action in progress).
Naming convention: Single verb or Verb + context. "Edit" or "Edit assumption." "Dismiss" or "Dismiss suggestion."
Mobile: Persistent (not hover-dependent) at minimum 44×44px touch target.
Keyboard: Accessible via Tab. Activated by Enter or Space.

⸻

Section Action

Purpose: An action available at the section level — applies to the section as a whole rather than to a specific element within it.
Placement: At the section label level (right-aligned) or at the bottom of the expanded section body.
Emphasis: Tertiary — present but not competing with section content.
Examples: "Refresh analysis," "View full history," "Export section."
Misuse: Do not put Primary Actions at the section level. Section actions are always tertiary.

⸻

Completion Action

Extends Primary Action. Specific to the terminal action of the Workspace — the Record Decision, Complete Review, or equivalent action. Distinguished from a generic Primary Action by the gravity of its consequence: it produces a permanent record.
Additional requirements: Always accompanied by an explanation when disabled (the blocking condition is always named, not generic). The enabled state is only available when all completion gate conditions are met. In post-recording state, transitions to "Close Workspace" only.

⸻

Destructive or History-Altering Action

Purpose: Actions with permanent or difficult-to-reverse consequences — discarding a draft, superseding a decision, removing a monitoring condition.
Placement: Not in the primary action position. Usually a Tertiary Action or an action within a specific section context.
Emphasis: Low emphasis at rest. On activation, a confirmation step is required before the action completes.
Confirmation: A brief inline confirmation ("Are you sure you want to discard this draft? This cannot be undone.") with explicit confirm and cancel. Not a modal dialog.
Keyboard: Requires explicit confirmation Enter — cannot be activated accidentally.
Examples: "Discard draft," "Supersede decision," "Remove monitoring condition."

⸻

16. Metadata Components

All metadata components use the metadata typographic scale — the smallest text in the system, with wide letter-spacing and optionally a technical variant. All are secondary to the primary reading experience. All are clearly readable at deliberate reading distance while receding at normal reading distance.

Timestamp: A date or date-and-time indicator. Format: natural language for recent dates ("Yesterday," "3 days ago"), explicit date for older records ("January 14, 2025"). Used for recording dates, last-reviewed dates, last-updated dates. Non-interactive unless tapping reveals the full timestamp with time zone.

Source: A reference to the Workspace or analysis that produced the adjacent content. Format: "Based on Investment Workspace · [date]" or "From Portfolio Analysis." A link when the source is navigable. Non-interactive when the source is not available for navigation.

Confidence: The qualitative confidence label adjacent to the decision statement or conclusion. One of five values (High Confidence, Moderate Confidence, Low Confidence, Evidence Incomplete, Dependent on Uncertain Assumptions). Non-interactive at metadata scale — tapping/clicking opens the full Confidence component (with explanation and contributing factors). Never numeric, never a gauge, never a percentage.

Status: The current lifecycle state of an object. Uses the state vocabulary defined in Section 13. Always accompanied by a text label — never color alone. The semantic color reinforces the text label.

Author: Identifies who authored a piece of content — Atlas or the user. Present as a small label ("ATLAS" or the user identifier) when the authorship would otherwise be ambiguous in context. In practice, authorship is more often communicated through layout, typography, and the section structure (per UX-012A Section 14) rather than through an explicit Author label.

Version: Indicates which version of a decision or record is being displayed. "Version 2 of 3" or "Amended · January 2025." Non-interactive unless a version selector is available.

Relationship: A reference to a related object — a linked monitoring condition, a related decision, a connected assumption. "Linked to: LVMH monitoring condition." A link when the related object is navigable.

Monitoring State: The current state of an active monitoring condition associated with this object. "MONITORING ACTIVE" or "TRIGGERED · 3 days ago." A link to the Monitoring Condition component when navigable.

⸻

17. Component Relationships

Components exist within a compositional structure. Understanding how components relate is as important as understanding each component individually.

The primary compositional sequence in Atlas:

Primary Conclusion → Supporting Factors → Challenges → Decision → Monitoring → History

This sequence represents the reasoning arc from established analysis through user commitment to ongoing observation to preserved memory. Every major Atlas surface follows a variant of this arc.

Dependencies:

The Final Decision Card depends on: the Decision Field (decision statement), the Long-form Editor for primary reason, the Confidence component (via editing interaction), at least one Assumption or Invalidation Condition, the Implementation Summary, and the Review Condition. The card cannot be in completed state unless all six fields are populated.

The Monitoring Condition depends on: a linked prior decision or assumption (it cannot exist without an object it is monitoring). When the linked object is superseded, the Monitoring Condition transitions to Expired.

The Atlas Suggestion depends on: the Long-form Editor or Short Statement it addresses. It cannot appear independently of a field context.

The Challenge component is generated by Atlas in response to: the current decision content, the prior decision record (if one exists), the current portfolio state, and the current assumption status. Challenges are not user-authored — they are Atlas-surfaced. The user acknowledges them; they do not create them.

Nesting rules:

Components may be nested when they are conceptually contained — an Atlas Suggestion is contained within a Long-form Editor context; a Historical Record may contain a Decision Summary. Components should not be nested when the nesting would obscure the hierarchy — a Final Decision Card should not appear inside a Comparison Section.

Composition rules:

A section is always composed from a Section component (which provides the collapse/expand structure) containing one or more reasoning, comparison, decision, monitoring, or history components. The Section component is the container; it does not contain other Section components.

The Workspace Frame contains Section components, not the individual reasoning components directly. Reasoning components appear within sections.

A Dashboard signal may contain a condensed Decision Summary, a condensed Monitoring Condition, or a condensed Conclusion component — but not a full Final Decision Card or a full Comparison Section. The Dashboard uses compact variants of components, not the full Workspace variants.

⸻

18. Component States

Every Atlas component supports a consistent state model. State is communicated through text labels, typographic treatment, and semantic color — consistently and without color dependency.

Collapsed: The component shows only its summary or headline. The expansion affordance is visible.
Expanded: The component shows its full content. The section header remains visible at the top.
Focused: The component or one of its interactive elements is the current keyboard focus. Focus ring visible.
Selected: A specific item within the component has been selected by the user — a monitoring condition is chosen for linking, an assumption is chosen for editing.
Hover: The component is being hovered by a pointer. Edit controls or expand affordances become visible. No background change for non-interactive components.
Editing: The component contains an active Long-form Editor or Short Statement in focused/editing state. The surrounding document dims slightly.
Read-only: The component contains content that cannot be edited — recorded decisions, locked historical content, inherited context.
Historical: The component is presenting a prior record. Tertiary text color, reduced opacity, timestamp visible.
Disabled: An action within the component is not currently available. Reduced opacity, not-allowed cursor, no color change.
Loading: The component is waiting for Atlas analysis or system data. Minimal loading indicator; last-known state shown.
Empty: The component has no current content. An intentional empty state is shown — never a blank space.
Invalid: The component's content does not meet a specific requirement — a review trigger that cannot be monitored, an assumption without a specific observable condition. A soft inline validation note appears.
Updated: The component's content has changed since the user's last visit. A small "UPDATED" label in metadata scale appears at the section label level.

State transitions are always communicated through: (1) a visible label change (the text of the state label changes), (2) a typographic or opacity change (the content becomes more or less prominent), and (3) optionally a semantic color change (the border or label color changes). No state is communicated through color alone.

⸻

19. Component Accessibility

Every Atlas component is designed to be fully operable without a pointer device and fully communicable to assistive technology.

Keyboard behavior:
— All section headers are reachable via Tab.
— Expand/collapse is triggered by Enter or Space when the section header is focused.
— All action controls are reachable via Tab and activated by Enter or Space.
— Long-form editors and Short Statement fields are reachable via Tab and entered via focus.
— The Atlas Suggestion panel appears in the Tab order after the field it addresses.
— Destructive actions require a separate Tab focus and explicit Enter confirmation.
— The Workspace can be navigated entirely from header to footer using Tab, with clear focus indicators throughout.

Focus behavior:
— The focus ring (minimum 2px, sufficient contrast — per UX-012A Section 15) appears on all interactive elements during keyboard navigation.
— The focus ring is suppressed on pointer interaction (`:focus-visible`).
— When a section expands, focus moves to the first interactive element within the expanded body.
— When a section collapses, focus returns to the section header.
— When the Atlas Suggestion appears, focus does not move to the suggestion automatically — the user navigates to it when ready.

Screen reader expectations:
— Section headers are marked with an appropriate ARIA role (`button` with `aria-expanded` attribute).
— Expanded state changes are announced (`aria-live` region or equivalent).
— All status labels and state changes are announced without requiring navigation.
— The authorship of every content block is identifiable — Atlas-generated content has an ARIA label identifying its source.
— The Final Decision Card is identified as a landmark region in the post-recording state.
— All action controls have accessible labels that describe their effect ("Record this decision permanently" rather than "Record Decision" when additional context is needed for screen reader users).

Non-color communication:
— Every semantic state is communicated through text label first, typographic treatment second, semantic color third.
— A user who cannot perceive color differences can determine: the status of every assumption, the severity of every challenge, the state of every monitoring condition, the authorship of every content block, and the availability of every action.

Touch interaction:
— All interactive elements have a minimum 44×44px touch target.
— Touch targets that appear smaller visually have transparent padding extending to the minimum size.
— Swipe behavior is reserved for system-level navigation (back gesture). Atlas components do not use swipe interactions for core functions.

Reduced motion:
— All transitions are instantaneous when the OS prefers reduced motion.
— No functional information is conveyed through motion alone.
— The 400ms post-recording behavioral pause is preserved — it is not a visual animation.

⸻

20. Component Audit

Reviewing the complete component library against the five characteristics defined in Section 1:

Clarity: Every component defined above represents one product meaning — a monitoring condition, a challenge item, an Atlas suggestion, a historical record. No component has an ambiguous purpose. Components with overlapping purposes (Challenge and Atlas Warning) are distinguished by their trigger and authorship context.

Restraint: No component has been defined that exists for visual convenience rather than semantic necessity. The Before/After, Alternative Comparison, Opportunity Cost, and Allocation Comparison components might appear to overlap — they are distinct because the product meaning in each context is distinct: a structural portfolio change, a qualitative reasoning comparison, the specific cross-investment opportunity analysis, and a quantitative allocation view.

Clear ownership: Every component belongs to one category and one primary purpose. Cross-category composition is defined through explicit composition rules (Section 17), not through components that belong to multiple categories.

High reuse potential: The highest-reuse components are: Section (all Workspaces), Assumptions (Decision, Investment, future Review), Challenges (Decision, Investment, Portfolio, future Review), Monitoring Condition (Decision, Dashboard, future Monitoring), Decision Summary (Dashboard, Investment, Portfolio, future surfaces), and Final Decision Card (Decision Workspace, Dashboard, Investment and Portfolio context).

Minimal overlap: The most similar component pairs — Atlas Warning and Challenges; Monitoring Condition and Review Trigger; Historical Record and Historical Decision — are distinguished by authorship context (Atlas Warning is AI-generated; Challenges is a section component that may surface warnings), by specificity (Monitoring Condition is the base; Review Trigger is a specific type), and by content scope (Historical Record is the base; Historical Decision is a specifically typed variant).

Future extensibility: The component taxonomy supports future Workspaces — a Review Workspace would primarily compose Section, Conclusion (Review Conclusion), Historical (Historical Decision, Historical Comparison), Decision (Decision Summary, Decision Amendment), and Monitoring components. A Monitoring Workspace would primarily compose Section, Monitoring (all variants), and Decision Summary components. No new component categories would be required for these two likely future surfaces.

⸻

What UX-012B Establishes

The following component and pattern decisions are now fixed.

Component philosophy: Atlas components are recurring product meanings, not visual primitives. A component earns its place when the same product meaning recurs across two or more surfaces and inconsistent presentation would harm user understanding. Three conditions must all be true for a new component.

Component taxonomy: Twelve categories — Workspace, Section, Conclusion, Reasoning, Comparison, Decision, Monitoring, History, AI Collaboration, Editing, States and Feedback, Actions, Metadata — each representing a class of product meaning.

Workspace components: Workspace Frame, Workspace Header, Workspace Identity, Workspace Status, Workspace Footer, Return Navigation, Historical Indicator, Draft Indicator — all fully specified with required content, optional content, interaction, responsive behavior, appropriate use, and misuse to avoid.

Section component variants: Standard Section, Reasoning Section, Read-only Section, Editable Section, Comparison Section, Monitoring Section, Historical Section, Decision Section, Completion Section — all sharing the Section template anatomy from UX-012A with behavioral specializations.

Conclusion components: Primary Conclusion, Current Conclusion, Decision Required, What Changed, Portfolio Conclusion, Review Conclusion — all with required content, priority, placement, and historical behavior.

Reasoning components: Supporting Factors, Challenges, Assumptions, Invalidation Condition, Portfolio Consequences, Opportunity Summary, Implementation Summary, Review Condition — all with purpose, content, hierarchy, interaction, visual emphasis, and reuse rules.

Comparison components: Before/After, Alternative Comparison, Opportunity Cost, Allocation Comparison, Historical Comparison — all with structure, interaction, responsive layout, reading order, and expansion behavior. (A previously explored "Scenario Comparison" concept remains documented earlier in this document as historical experimental evidence, not as an adopted Comparison component; see Correction Notice, Phase 3E, above.)

Decision components: Proposed Decision, Final Decision Card, Decision Summary, Decision History, Decision Amendment, Decision Review — all with required and optional content, states, interaction, and historical behavior. The Final Decision Card is established as a signature Atlas component.

Monitoring components: Monitoring Condition (base), Review Trigger, Invalidation Trigger, Implementation Follow-up, Scheduled Review — all with purpose, lifecycle, states, and interaction.

Historical components: Historical Record (base), Historical Decision, Historical Review, Historical Assumption, Historical Timeline Entry — all with presentation, hierarchy, immutability rules, and navigation.

AI Collaboration components: Atlas Suggestion, Atlas Insight, Atlas Warning, Atlas Recommendation, Atlas Clarification, Atlas Summary — all with purpose, trigger, priority, placement, dismiss/accept/partial-accept behavior, editing behavior, and historical behavior.

Editing components: Long-form Editor, Short Statement, Decision Field, Structured Comparison Editor, Assumption Editor, Implementation Editor — all with full state models (inactive, hover, focused, editing, saved, atlas-generated, user-modified, read-only), validation behavior, AI collaboration integration, autosave, history, and undo.

State vocabulary: Thirteen states (Draft, Saved, Unsaved, Under Review, Monitoring, Completed, Recorded, Historical, Updated, Requires Attention, Deferred, Superseded) — each with semantic meaning, visual treatment, interaction, and relationships.

Feedback components: Seven feedback patterns (Informational, Reminder, Warning, Material Concern, Blocking Issue, Validation, Loading, Empty State) — each with severity, behavior, timing, dismissal, visual treatment, and relationship to reasoning. Empty State defined as four distinct types (positive absence, unavailable result, incomplete data, user action required).

Action components: Primary Action, Secondary Action, Inline Action, Section Action, Completion Action, Destructive/History-Altering Action — all with placement, emphasis, states, naming convention, keyboard behavior, and mobile behavior.

Metadata components: Timestamp, Source, Confidence, Status, Author, Version, Relationship, Monitoring State — all with hierarchy, placement, visibility, and responsive behavior.

Component relationships: Primary compositional sequence (Conclusion → Supporting Factors → Challenges → Decision → Monitoring → History); dependency rules; nesting rules; composition rules; Dashboard compact variant rules.

Universal state model: Fourteen states (collapsed, expanded, focused, selected, hover, editing, read-only, historical, disabled, loading, empty, invalid, updated) — all communicated through text label + typographic treatment + optional semantic color. No state communicated through color alone.

Component accessibility: Keyboard behavior, focus behavior, screen reader expectations, non-color communication, touch target requirements, and reduced motion behavior — all specified for the component system as a whole and applicable to every individual component.

⸻

Remaining Component Questions

1. The exact form of the Atlas Suggestion partial-accept interaction:
The specification establishes that highlighted segments in the suggestion are selectable. The visual form of the selection state — how a selected versus unselected sentence segment is rendered — has not been specified at the pixel level. This requires a design prototype to validate that the interaction is legible without feeling mechanical.
Evidence needed: Prototype testing with representative suggestion content. Does not block UX-012C.

2. The Dashboard compact variant of the Final Decision Card:
The Decision Summary component is defined as the portable version of the Final Decision Card, but the specific truncation rules — which fields appear, which are omitted, how the card adapts to the Dashboard's signal density context — have not been fully specified.
Evidence needed: Dashboard design context from a Dashboard specification update. Does not block Decision Workspace implementation.

3. Whether a future version history panel deserves its own component:
The Historical Timeline Entry component is defined, but the container panel within which it appears — the version history panel in the Decision Workspace — is referenced but not given its own full specification. It may warrant its own component definition.
Evidence needed: Decision Workspace implementation experience. Does not block UX-012C.

4. The historical Scenario Comparison concept's mobile layout (moot — not an adopted component):
This question, as originally posed, concerned the mobile responsive treatment of the Scenario Comparison card grid described earlier in this document. Per the ADR-004 corpus-wide addendum (see Correction Notice, Phase 3E, above), that concept was never adopted as a shared Comparison component; this question is accordingly moot and requires no further resolution. Scenario-specific content and its own responsive presentation remain governed by Scenario Analysis (UX-013B §9), not by this document.
Evidence needed: none — moot. Does not block UX-012C.

⸻

Requirements for UX-012C

UX-012C — Atlas Design System Interaction, Motion & System Behaviors — will cover the behavioral layer of the Atlas Design System: the rules governing how the system moves, responds, transitions, and handles edge cases consistently across all components and Workspaces.

Navigation patterns:
— The full navigation model for Atlas Workspaces: open, close, return, move to related Workspace, follow a monitoring trigger, revisit a historical decision
— Context preservation rules: what is preserved when a Workspace is opened (the underlying surface state), what is preserved when a Workspace is closed (the scroll position, expanded sections, filter state)
— How navigation between Workspaces passes context forward (the inherited content model — what the Decision Workspace receives from the Portfolio Workspace)
— The overlay layer model: when two Workspaces are open simultaneously (Decision Workspace opened from Portfolio Workspace) — how layers are managed and dismissed

Interaction tokens:
— Hover: surface change rules, affordance appearance rules, pointer behavior rules — by component type
— Focus: focus ring specification (pixel width, color, radius behavior), `:focus-visible` implementation, focus movement on expand/collapse
— Pressed: the visual state of an action control between pointer-down and pointer-up — brief, non-theatrical
— Selected: the visual state of a selected item within a comparison or history list
— Expanded/collapsed: the behavioral rules governing the transition between these states — which elements persist, which reveal, which reflow
— Editable: the transition from read/hover to focused/editing — the specific moment when the document becomes a writing surface
— Read-only: the visual rules for locked content — historical records, recorded decisions, inherited context
— Loading: the inline loading indicator — its appearance, its position relative to the loading element, its minimum display duration
— Saved/Unsaved: the Draft Indicator's state transition rules
— Acknowledged: the visual result of user acknowledgment for a challenge, warning, or monitoring trigger
— Disabled: opacity, cursor, and explanation text rules for disabled states
— Historical: the full visual treatment specification (opacity level, color token, surface distinction)
— System-updated: the "UPDATED" label appearance and disappearance rules

Motion principles:
— Duration categories: immediate (0ms, for reduced-motion contexts), brief (100–150ms, for state changes and affordance appearances), standard (200–250ms, for expand/collapse transitions), deliberate (350–400ms, for the post-recording transition)
— Easing: ease-out for elements entering, ease-in for elements leaving, ease-in-out for elements moving
— Six motion categories (Orientation, Disclosure, State-change, Suggestion, Comparison, Focus) — each with defined duration category and easing
— The post-recording behavioral pause: 400ms with no visual animation, followed by the body clearing
— Scroll deceleration at visual pause points: the specific velocity reduction rule
— Motion reduction: the instantaneous fallback for all transitions; which behaviors survive reduced-motion preference

Responsive behaviors:
— The full stacking and adaptation rules for each component at each breakpoint — beyond the high-level philosophy in UX-012A
— The comparison layout collapse rules: when the two-column layout becomes sequential, how the reading order is preserved
— The footer adaptation on mobile: when secondary actions move to a collapsed group, how the primary action retains full-width treatment
— The long-form editor full-screen mode on mobile: entry, editing, and exit behavior
— The Dashboard signal density adaptation from desktop to mobile

Accessibility implementation:
— The complete ARIA role assignment for every component type defined in UX-012B
— The screen reader announcement model for state changes, expansion events, and Atlas assistance appearances
— The focus movement model on section expansion and collapse
— The keyboard shortcut specification (full shortcut table extending UX-010's Decision Workspace shortcuts to the full Atlas system)
— The accessible comparison model for Historical Comparison and Alternative Comparison on screen readers
— The reduced-motion token implementation

Loading states:
— The minimum display duration for loading indicators (prevents flash-of-loading for fast responses)
— The maximum wait time before a system-activity note appears ("Updating analysis...")
— The skeleton state rules — when, if ever, skeleton content is shown versus the last-known state
— The error state for failed Atlas analysis (Atlas cannot generate a conclusion — the section shows the unavailable empty state, not an error message)

Validation and errors:
— The complete validation model for all required fields in the Decision Workspace completion gate
— Soft validation (the inline field note for vague review triggers or assumptions) versus hard validation (the completion gate)
— The error model for technical failures — network errors, analysis unavailability, save failures
— The unsaved-work protection model — what happens when the user closes the Workspace with unsaved changes

Empty states:
— The full empty state specification for every component defined in UX-012B that may be in an empty state
— The four empty state types (positive absence, unavailable result, incomplete data, user action required) specified for each component
— The empty Workspace state (when a Decision Workspace is first opened with no prior content)

Cross-workspace interaction consistency:
— The consistency audit method for verifying that interaction behaviors are identical across Workspaces
— The behavioral token system — a shared vocabulary of interaction rules that components reference rather than defining independently
— The rules for new Workspaces: which interaction behaviors are required, which are optional, which must be explicitly justified if they deviate

Do not produce UX-012C yet.

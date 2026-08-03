UX-012C — Atlas Design System Interaction, Navigation & Responsive Behavior

Status: Interaction Specification Complete
Owner: Atlas Product
Governs: Interaction language, navigation model, motion principles, interaction tokens, responsive behavior, editing behavior, AI interaction, loading, validation, errors, empty states, completion, history, monitoring, accessibility
Depends on: UX-012A — Foundations; UX-012B — Components & Reusable Patterns; UX-008 through UX-011
Part C of: UX-012 — Atlas Design System & Workspace Consistency Specification

**Correction Notice (Phase 3C, governed by ADR-002 — 2026-07-25):** This document's original identity (Status, Owner, Governs, Depends on, Part C of, as above) and original date are preserved unchanged. Two semantic areas were corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan, Phase 3C:
- **C-02 (AI Authorship and Provenance):** the AI Interaction section's Accept behavior previously stated that accepting an Atlas suggestion, by itself, transitioned the field directly to "user-modified-from-atlas" state — this read as authorship transferring on acceptance alone. This was corrected so that acceptance alone produces an Accepted state ("Atlas Suggested / User Accepted"), with authorship not yet transferred; "user-modified-from-atlas" is now reached only after a genuine, subsequent edit — the same model already corrected in UX-012B. The adjacent label was also corrected, from "modification indicator" to "attribution indicator," because acceptance alone has not modified the content — the indicator's placement and interaction behavior are unchanged; only what it represents was corrected.
- **C-03 (Decision Workspace Sequence terminology):** one stale illustrative naming example — "Section names describe their content role ('What Supports This Decision,' not 'Supporting Section')" — was corrected to use the canonical name "Supporting Factors."

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, above. All content outside these two areas, including all interaction, navigation, responsive, and accessibility content, is unchanged.

**Correction Notice (Phase 6C, governed by ADR-002 C-06 — 2026-07-29):** This is a later, additive correction, discovered after the Phase 3C correction above had already closed; it does not revise, replace, or reopen that notice, which remains historically accurate for the areas it corrected. Three active occurrences of unqualified "disabled" wording applied to the Record Decision control were corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` C-06 and the Atlas UX Source Correction Plan, Phase 6C:
- §21 ("Completion Behavior"), pre-completion state: "If the button is disabled" was corrected to "is unavailable (`aria-disabled=\"true\"`)."
- §21 ("Completion Behavior"), completion gate check: "the button remains in the disabled state" was corrected to "remains in the unavailable state (`aria-disabled=\"true\"`)."
- §24 ("Cross-Workspace Interaction Consistency," permitted cross-workspace variation): "the primary action may be disabled based on content conditions" was corrected to "may become unavailable (`aria-disabled=\"true\"`, never native `disabled`) based on content conditions."

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, at each corrected passage. No described interaction behavior (the completion-gate evaluation, the missing-content explanation, the auto-scroll-to-field behavior, the cross-Workspace-variation reasoning) is changed by this correction — only the terminology naming the control's unavailable state. This document's own hover-treatment line ("Primary action in disabled state: no change on hover"), its foundational Interaction-tokens "disabled:" definition, and its Interaction-tokens summary list are presentation-only or generic-vocabulary content, reviewed and outside the scope of this correction, and remain byte-identical. All content outside the three corrected passages above, including this document's own already-corrected Phase 3C passage, is unchanged.

**Authority Notice (Atlas UX Architecture UX-012 Authority Migration task — 2026-08-02):** `UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0, is the governing UX doctrine, per its own UXD-R-097. This document is a subordinate operational specification governing interaction, navigation, and responsive behavior only, within the scope stated in its own header. Product meaning remains governed exclusively by APP-000, APP-001, and the applicable APS documents; nothing in this document amends `UX-000`, Product Architecture, Core Architecture, or any ADR.

**Correction Notice (Atlas UX Architecture Token Architecture Release Polish (Final Sprint) task — 2026-08-02):** This is a later, additive correction; it does not revise, replace, or reopen any notice above. This document's own token-naming-convention worked example (§9, "Token naming convention") mixed a canonical form (`surface.elevated`) with a retired, pre-Phase-1 bare form (`text.primary`) in the same illustrative sentence. Prior text: "e.g., `surface.elevated`, `text.primary`, `space.inter-section`, `motion.expand.duration`." Corrected to `color.text.primary`, matching `UX-012D` §3's own Text Hierarchy (Phase 1). This is an illustrative-example correction only — no architecture, interaction behavior, motion behavior, or accessibility content changes anywhere in this document.

**Terminology Notice (Atlas UX Governance Resolution Sprint, 2026-08-03):** Per the completed ATLAS UX CORRESPONDENCE INVESTIGATION, which found this document's three "Daily Briefing" references and `APS-008`'s formal "Daily Brief" to name the same product surface at every point tested, with no contextual difference, "Daily Briefing" is corrected to "Daily Brief" at each of the three occurrences (the deep-link-behavior source list; the open-historical-record source list; the monitoring-trigger signal description). This is a naming correction only; no deep-link, history-access, or monitoring-trigger behavior is changed.

⸻

1. Interaction Philosophy

Atlas interactions exist to support one purpose: helping the user think more clearly about a decision. Every interaction is evaluated against this test. If an interaction does not help the user think more clearly, it should not exist.

This produces a governing principle for the entire interaction model: interactions reduce uncertainty, never increase it. When a user completes an action in Atlas, they should be more oriented than before — they should understand where they are, what changed, what is available next, and what the system did on their behalf.

Atlas interaction differs from other product categories in four specific ways:

Different from consumer apps: Consumer apps are optimized for engagement, habit formation, and return visits. Atlas is optimized for reasoning quality. Consumer apps reward frequent interaction; Atlas should reward careful, infrequent interaction. An investor who opens Atlas once a week and records one well-considered decision is using it correctly. The interaction model should never suggest that more engagement is better.

Different from brokerage platforms: Brokerage platforms communicate market state and trading opportunity in real time — they are designed for speed, pattern recognition, and immediate action. Atlas is designed for the opposite: slowing down, examining reasoning, and forming a considered position. Atlas interaction never creates urgency. Nothing in Atlas should feel like a live ticker.

Different from enterprise software: Enterprise software is typically form-driven — users complete workflows by filling in required fields and proceeding through defined steps. Atlas is document-driven — users read, reflect, and author. The interaction model must feel like working within a document, not completing a workflow. Validation in Atlas is soft and informational, not gate-driven. The user is never trapped in a step.

Different from AI chat interfaces: AI chat interfaces structure reasoning as a dialogue — a sequence of turns where the AI responds to each user input. Atlas structures reasoning as a document — the user is the author, and Atlas is a collaborator who has already done significant preparatory work. Atlas assistance appears in context, within the document, without requiring the user to initiate a conversation. The user should never feel they are talking to Atlas; they should feel they are working on a document that Atlas has prepared for them.

Five governing principles for every interaction:

1. Support reasoning. Every interaction should make the user's thinking clearer, more structured, or more complete. Interactions that merely satisfy system requirements without improving the user's understanding should be removed.

2. Clarify hierarchy. When the user acts — expands a section, accepts a suggestion, navigates to a related Workspace — the result should confirm the hierarchy they expected. Nothing should land somewhere surprising.

3. Reduce cognitive load. The interaction should require less mental effort after it than before. This means interactions should be discoverable from structure (not from tooltips or documentation), reversible where possible, and consistent across all contexts.

4. Preserve context. An interaction that causes the user to lose their place, their draft, or their understanding of where they are has failed. Context is the user's reasoning state — it must be preserved across navigation, across editing, and across surface transitions.

5. Avoid unnecessary activity. The interaction model should not generate activity for its own sake. Notifications, badges, confirmations, and animations that do not carry information should be removed. The user's attention is the most scarce resource in Atlas.

⸻

2. Navigation Philosophy

Atlas navigation is not page navigation. The user is not moving between pages; they are moving through a continuous reasoning process. Navigation in Atlas carries the user deeper into their analysis or returns them to a prior point in the reasoning arc — it does not take them somewhere unrelated.

The user's orientation is built from three questions, which the design must always answer:

Where am I? The Workspace Frame (identity, type, subject) answers this continuously. The user should always know which investment, which Workspace type, and which reasoning stage they are in without reading the URL or breadcrumb trail.

Where did I come from? The underlying surface is visible at the edges of any Workspace overlay. The return control navigates back to the exact prior surface state. This is the primary "back" mechanism in Atlas — not a browser back button.

Where can I go? The links and action controls within each Workspace provide the available next steps — the related Workspace, the source analysis, the historical record, the monitoring condition. These are inline and contextual, not in a navigation menu.

What navigation must preserve:

Scroll position of the underlying surface: When a Workspace is closed, the underlying surface returns to the exact scroll position it was in when the Workspace was opened.

Expanded section states of the underlying surface: Sections that were expanded before the Workspace was opened remain expanded on return.

Workspace draft state: Any unsaved changes in the current Workspace are preserved while the user navigates to a related Workspace or source reference. Opening a second Workspace does not discard the draft in the first.

Selected investment or portfolio context: The current subject of the user's reasoning — the investment they are analyzing, the portfolio review in progress — is maintained across navigation. The user does not need to re-select their context when returning.

Filters and sorting on the underlying surface: If the user has applied filters on the Dashboard or Portfolio Workspace, those filters are restored on return from a Workspace overlay.

Decision editing context: If the user is mid-decision in the Decision Workspace and follows a source link to the Investment Workspace, their Decision Workspace state is preserved and the Investment Workspace opens as an additional overlay layer above it.

Navigation as continuous reasoning: The ideal navigation experience in Atlas is that the user feels they are moving deeper into the same reasoning thread, not leaving it and starting over. A well-designed navigation transition carries the relevant context forward — the Investment Workspace that opens from a Dashboard signal shows why it was opened. The Decision Workspace that opens from the Portfolio Workspace already contains the conclusion and supporting context from the portfolio analysis.

⸻

3. Workspace Navigation

Open Workspace

Entry behavior: A Workspace opens as an overlay above the current surface. The underlying surface dims to approximately 30–40% opacity — enough to recede without disappearing. The Workspace entry transition follows the motion token for Open (see Section 10). The overlay settles into its final position before any body content is interactive — the transition completes before the user can interact with the content.
Context passing: The opening Workspace receives the context from the originating surface — the subject (investment name, portfolio review period), the reason for opening (the signal, the Atlas recommendation, the user's deliberate navigation), and any relevant prior decisions or analysis that should be pre-loaded into the Workspace.
Focus on entry: On opening, focus moves to the first interactive element within the fixed header (the return/close control). The user may Tab forward into the scrolling body from there.
Appropriate use: Any transition from Dashboard to an Investment Workspace, from an Investment or Portfolio Workspace to the Decision Workspace, or from any surface to a historical record view.

Close Workspace

Exit behavior: The Workspace closes with the motion token for Close. The underlying surface restores to full opacity. The user's position, expanded sections, and filter state are exactly as they were before the Workspace opened.
Unsaved changes: If the Workspace contains a draft with unsaved changes beyond what autosave has captured, a brief inline confirmation appears before close: "Close and save draft?" with Save draft and Discard options. Not a modal — an inline panel within the footer area. If there are no meaningful unsaved changes, the Workspace closes without confirmation.
Focus on exit: Focus returns to the element that triggered the Workspace opening — the Dashboard signal that was tapped, the "Open Decision Workspace →" link that was activated.

Return to Dashboard

Behavior: Closes all open Workspace overlays in sequence (outermost first) and returns to the Dashboard. Each overlay closes with the motion token for Close. The Dashboard restores to its pre-Workspace state.
Context: The user's Dashboard state (scroll position, any expanded briefing items, filter state) is preserved.
Appropriate use: The Return Navigation control in any Workspace header that was opened directly from the Dashboard.

Return to Source

Behavior: Closes the current Workspace and returns to the Workspace from which this one was opened. Distinct from Return to Dashboard when the user has navigated through multiple Workspace layers.
Context: The source Workspace restores to its pre-overlay state — the user's scroll position within the Portfolio Workspace, for example, is exactly where they left it.
Appropriate use: The Return Navigation control in the Decision Workspace when it was opened from a Portfolio or Investment Workspace.

Open Related Workspace

Behavior: Opens a second Workspace overlay above the current one. The current Workspace dims (to the same overlay-dimming opacity as the underlying surface beneath the first Workspace). The related Workspace opens with the motion token for Open.
Layer management: Atlas supports a maximum of two overlapping Workspace layers. If a third overlay is requested, it replaces the second layer rather than adding a third.
Context preservation: The first Workspace's draft state is fully preserved while the second overlay is open.
Appropriate use: Opening the Investment Workspace from within the Decision Workspace to review source analysis. Opening the Portfolio Workspace from within the Decision Workspace to review portfolio consequences.

Open Historical Record

Behavior: Opens the historical view of the current Workspace or a specific prior record. The current content does not close — the Historical Indicator appears in the header, and the body transitions to the historical view using the motion token for Replace.
Alternative behavior: If the historical record is for a different investment or a different decision entirely, it opens as a separate overlay.
Context: The current draft state is preserved.
Appropriate use: Reviewing a prior decision while forming a new one. Comparing prior thesis conclusions with current analysis.

Open Monitoring

Behavior: Navigates to the relevant monitoring condition — either within the current Workspace (expands and scrolls to the monitoring section) or opens a related Workspace that contains the monitoring context.
Context: If within the current Workspace, the page scrolls smoothly to the monitoring section and the relevant item auto-expands. No overlay opens.
Appropriate use: Following a monitoring trigger link from a Dashboard signal or from the review condition section.

Deep-link behavior: A Workspace may be opened to a specific section via a deep link — from a Decision Timeline entry, from a Daily Brief item, from a monitoring trigger. When a deep link is followed, the Workspace opens normally, then auto-scrolls to the targeted section and auto-expands it. The scroll and expansion happen after the Workspace opening transition completes, not simultaneously. *(Corrected per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02. Prior text: "from an Atlas Memory reference." Per the completed Atlas Memory Status Investigation, "Atlas Memory" is not a canonical UX term; a deep link to a specific point in one Decision's own history is a Decision Timeline reference.)*

Browser history behavior: Workspace overlay navigation is not reflected in browser history. Opening and closing Workspace overlays does not create new browser history entries. Only navigation between distinct Atlas surfaces (Dashboard, a specific investment context, the portfolio context) creates history entries. The user's browser back button returns them to the prior Atlas surface, not to a prior Workspace overlay state.

⸻

4. Reading Flow

The Workspace reading flow is the interaction experience of a user who is not actively editing or navigating — simply reading through the document from top to bottom. This is the primary mode for the Investment Workspace and the early stages of the Decision Workspace.

Natural progression: The Workspace is designed to be read sequentially. Each section builds on the previous. The user who reads linearly — conclusion → implication → supporting reasoning → challenges → opportunity cost → decision — arrives at the completion region with the full reasoning context assembled. The interaction model should not interrupt this progression.

Scroll behavior: The body scrolls continuously. There are no hard scroll stops or snap points. The scroll behavior is modified at four visual pause points — the high-emphasis moments defined in UX-012A — by a subtle velocity deceleration: the scroll slows as the primary conclusion, the decision field, the opportunity cost synthesis, or the Final Decision Card enters the center of the viewport. This deceleration is brief and gentle — it draws the user's attention without interrupting their agency. It is achieved through a scroll event listener that applies a temporary friction when these elements cross a defined viewport threshold.

Visual pauses: The four pause points are structural, not interactive. The user's scroll is not stopped; it is slowed. If the user scrolls quickly through the deceleration zone, the behavior does not reassert — it fires once per scroll event crossing the threshold.

Reading progression across sessions: Atlas preserves the user's scroll position within a Workspace between sessions. If a user closes the Decision Workspace at the portfolio consequences section and returns the next day, the Workspace opens at the position it was closed. The user does not restart from the top.

Section transitions: The visual transition between sections is spacing — the inter-section space is the transition. No graphical separators, no motion effects between sections. The user's awareness that they have arrived in a new section comes from the section label, the change in content type, and the surrounding space.

Auto-scroll to incomplete field: When the user activates the primary action while a required field is incomplete, the Workspace auto-scrolls to the field, expanding the containing section if necessary, and places focus within the field. This auto-scroll uses the motion token for Focus — a smooth, moderately paced scroll that makes the destination visible before the scroll completes, so the user follows the movement and arrives oriented.

⸻

5. Expansion and Collapse

The expansion and collapse system is one of the highest-frequency interactions in Atlas. It must be perfectly consistent across every section in every Workspace.

What collapsed sections communicate:
— Purpose: the section label identifies what the section contains
— Summary: the two-line collapsed summary (line 1: primary conclusion for this section; line 2: material implication or most important supporting detail) communicates the section's current state
— Importance: the collapsed-with-attention state (when an unresolved issue exists within the section) communicates that the section warrants the user's attention
— State: a status label in metadata scale (when the section has a non-default state — a broken assumption, a triggered monitoring condition) communicates the current condition

What expanded sections communicate:
— Full reasoning: all content is visible and readable
— Structure: internal groupings, subsections, and row-level hierarchy are apparent
— Interaction: edit affordances, AI suggestion indicators, and acknowledgment controls become visible
— Relationships: links to related sections, source Workspaces, and monitoring conditions are accessible

Manual expansion: The user taps or clicks anywhere on the collapsed section header row. The entire row is the interactive target — including the section label, the summary text, and the expansion affordance. There is no small hit-target — the full row width and the full row height are interactive.

Automatic expansion: A section may be auto-expanded by Atlas in specific conditions:
— A material contradiction has been detected (the Challenges or Contradiction section expands)
— A monitoring condition has been triggered (the Monitoring section expands and scrolls into view)
— A required field is incomplete at the point of completion gate evaluation (the containing section expands and focus moves to the field)
— A deep-link target is within the section (the section expands as part of the deep-link arrival)

Auto-expansion behavior: Auto-expansion always includes an explanation of why the section has opened. This explanation appears either as a label within the section header ("Expanded: material contradiction detected") or as an Atlas Warning component at the top of the expanded body. The user is never confused about why something opened without their action.

Persistent state: A section's expanded or collapsed state persists within the current session. If the user expands the Assumptions section and then scrolls away, the section remains expanded when they scroll back. Expanded states do not persist between sessions by default — the Workspace returns to its default expansion state on each session, except for the scroll position preservation described in Section 4.

Cross-device behavior: The expansion state is not synchronized across devices. The Desktop session and the mobile session maintain independent expansion states. Each device starts from the Workspace's default expansion state.

Animation principles: Section expansion uses the motion token for Expand — content reveals downward from beneath the header. The header remains stationary. Surrounding sections reflow smoothly to accommodate the new height. Section collapse uses the motion token for Collapse — content compresses upward. The summary line replaces it. Neither transition uses spring-based overshoot. Neither transition uses bounce or elastic easing. The easing is functional — ease-out for the reveal (content enters), ease-in for the collapse (content exits).

⸻

6. Focus Management

Focus management defines how the user's active focus point moves through the interface — by keyboard, by pointer, by programmatic control, and across interaction boundaries.

Keyboard focus: All interactive elements are in the tab order. Tab order follows the visual reading order — top to bottom, left to right within rows. The focus ring (per UX-012A Section 15) is visible on all focused elements during keyboard navigation. Tab order within a collapsed section: the section header row is in the tab order; the content within the section is not accessible by tab until the section is expanded.

Mouse focus: Pointer interactions do not move keyboard focus except when the user activates a field (click into a Long-form Editor or Short Statement activates that field and places focus within it). Pointer clicks on non-interactive elements do not move focus. The focus ring is suppressed on pointer interaction using `:focus-visible`.

Touch focus: On touch devices, the focus model follows pointer focus rules — touch activation of a field places focus within it. The focus ring may be suppressed on touch following the `:focus-visible` convention, or may be shown on touch if it aids orientation.

Workspace transition focus: When a Workspace opens, focus moves to the first interactive element in the fixed header (the return/close control). The user may Tab into the scrolling body from there. When a Workspace closes, focus returns to the element that triggered the opening.

Section expansion focus: When a section is manually expanded by keyboard (Enter or Space on the section header), focus moves to the first interactive element within the expanded body — the first edit affordance, the first expand control within the section, or the section headline if there are no interactive elements. When a section is collapsed, focus returns to the section header.

Auto-expansion focus: When a section is auto-expanded by Atlas (contradictions detected, monitoring triggered, deep-link arrival), focus moves to the relevant item within the expanded section — the triggered monitoring item, the contradiction item, the required field. A screen reader announcement accompanies the focus movement.

Dialog focus: Atlas does not use modal dialogs for reasoning content. The one exception is the unsaved-changes confirmation on Workspace close — a brief inline panel, not a modal. When this panel appears, focus moves to the primary action within it (Save draft). Escape dismisses the panel without action and returns focus to the close control.

Editing focus: When the user activates a Long-form Editor or Short Statement (by clicking, tapping, or tabbing into it), focus enters the field. The focus state changes (subtle left-border rule or underline activates). The surrounding document dims at low opacity. Tab within the field inserts a tab character (in long-form fields) or moves to the next field (in short statement sequences). Escape returns focus to the field's parent section header without saving (the autosave has preserved the content regardless).

Validation focus: When a completion gate check identifies an incomplete required field, the system auto-scrolls to that field and places focus within it. This is the only case where Atlas programmatically moves focus without direct user initiation.

Error focus: When a technical error occurs (network failure, analysis unavailability), focus does not move. The error indicator appears in place within the relevant section. The user discovers the error by reading — not by focus movement.

Users should never lose orientation. This is the absolute governing rule for focus management. A user who is navigating entirely by keyboard should always be able to answer: "Where is my focus right now? What will happen if I press Enter? What will happen if I press Tab?"

⸻

7. Hover Behavior

Hover reveals interactive affordances without requiring prior knowledge of what is interactive. It is the secondary discovery layer — the primary layer is structure (section headers are clearly section headers; action controls have labels). The user who has never hovered should still understand the Workspace structure.

Section headers (collapsed): The entire row receives a very subtle surface treatment on hover — a slight lightening or darkening that signals interactivity. The expansion affordance shifts from tertiary to secondary emphasis. The cursor is a pointer.

Section headers (expanded): Same hover treatment. The expansion affordance shifts emphasis — this time indicating collapse is available.

Long-form editor fields (user-authored): On hover, an edit control (a small "Edit" label or pencil icon at secondary emphasis) appears adjacent to the field text. The cursor within the text area is a text cursor. The cursor over the edit control is a pointer. No background change on the field itself — document space does not acquire a hover background.

Atlas-suggested content: On hover over Atlas-suggested content (the Atlas proposal block, Atlas-generated body text in an editable section), the "View original →" or "Modify →" control becomes visible. The cursor is a pointer over the control, default over the text.

Assumption rows and comparison rows: On hover, the row receives a subtle surface change. The expand affordance (if collapsed) shifts emphasis. Any inline action controls (Edit, Link) become visible.

Alternative rows in the Opportunity Cost section: On hover, the "Explore →" control becomes visible. The row receives a very subtle surface change. The cursor is a pointer over the control, default elsewhere.

Links ("View full analysis →", "View original →", "Return to Workspace"): On hover, text shifts to primary emphasis and an underline appears. Cursor is a pointer.

Action controls (buttons): Primary action in available state: a very subtle surface lightening on hover. Primary action in disabled state: no change on hover; cursor is not-allowed. Secondary actions: link hover treatment (text emphasis shift + underline).

Non-interactive content: No hover treatment. The cursor is the default cursor. If a piece of content has no hover treatment, it is read-only and non-interactive.

Touch devices: No hover state exists on touch. All content that relies on hover to reveal interactive affordances must also have a persistent low-emphasis alternative that is visible without hover. On mobile and tablet, edit controls are persistently visible (at low emphasis) rather than hover-revealed.

Hover must never be the only way to discover an interaction. Every interactive element in Atlas is structured to communicate its interactivity through its label, its position, or its section context — hover enhances this but does not create it.

⸻

8. Selection Model

Selection in Atlas communicates which item within a group is the current focus of the user's attention — the investment they are analyzing, the assumption they are editing, the alternative they are exploring.

Selected investment (Dashboard and Investment Workspace): The current investment being analyzed is visually indicated by a persistent selection state — a left-border rule or subtle background treatment at the Dashboard list item level. The Investment Workspace identity communicates the selected investment through its Workspace Identity component. No explicit "selected" visual within the Investment Workspace body itself — the Workspace is already scoped to one subject.

Selected section: There is no persistent selected section state in Atlas. Sections are expanded or collapsed; the user's focus within a section is communicated by keyboard focus. A section does not acquire a "selected" visual treatment merely because the user has scrolled past it.

Selected comparison item: Within a comparison layout (Opportunity Cost, Historical Comparison), the item the user has tapped or focused receives a subtle selection treatment — a slightly more elevated surface treatment or a left-border rule at full opacity. This selection is cleared when the user navigates away from the comparison section.

Selected decision: The active decision in any Decision Workspace is the entire Workspace — there is no need for a selection treatment at the decision level. In a list of historical decisions (the Decision History component), the currently relevant item (the most recent, or the one the user has expanded) receives a subtle selection treatment — distinct from the historical treatment applied to all items in the list.

Selected monitoring item: Within the Monitoring Section, a triggered monitoring condition that the user has tapped or focused receives the full triggered treatment — expanded, amber border, acknowledgment control prominent. Untriggered items in the same section have no selection treatment.

Selected historical record: When the user has opened a historical record for reading (within a Historical Section or a Historical Comparison), the expanded record acquires a slightly more defined surface treatment — a clear but not dramatic distinction from the surrounding historical content that communicates "this is the one I am reading."

Visual consistency: Selection is always communicated by a left-border rule, a subtle background elevation change, or a combination of both. Never by color alone. Never by a checkbox or toggle. Atlas selection is contextual and spatial — the user's position in the document communicates their current focus.

⸻

9. Motion Philosophy

Motion in Atlas has one purpose: to clarify what happened. When something changes in Atlas, motion communicates the nature of the change — what moved, where it came from, where it went. Motion never communicates excitement, urgency, achievement, or delight.

Motion should:
— Orient: show the user where something came from and where it went, so they maintain a mental model of the interface
— Clarify: make the cause of a change legible (the section expanded because the user tapped it; the content appeared because Atlas generated it)
— Connect: show the relationship between an action and its result by animating the transition between the before and after state
— Reduce confusion: eliminate the jarring visual jump that would occur if content changed instantaneously in a way that requires spatial adjustment

Motion should never:
— Celebrate: no particle effects, confetti, success animations, or positive-reinforcement motion for recording a decision
— Gamify: no bouncing, spring overshoot, elastic easing, or playful physics
— Create urgency: no rapid-fire transitions, no attention-demanding animations, no blinking or pulsing elements
— Distract: no idle animations, no breathing effects, no continuous motion on any element

The guiding test for any motion: if the motion were removed, would the user be confused about what happened? If yes, the motion serves a purpose. If no, remove it.

Motion categories and their governing qualities:

Workspace transition: Expansive and directional. The Workspace opens from a direction (below or with a fade) that communicates "this is a layer above." The Workspace closes in the reverse direction. Duration: standard (200–250ms).

Section expansion: Directional and contained. Content reveals downward from beneath the header. The header remains stationary. Surrounding sections shift downward to accommodate. Duration: standard.

Section collapse: Directional and contained. Content compresses upward. The summary replaces it. Surrounding sections shift upward. Duration: standard.

State transition: Immediate to brief. A status label changing (Holding → Broken), an acknowledgment being confirmed, a draft being saved. These are small, contained changes. Duration: brief (100–150ms).

Completion: Deliberate and quiet. The post-recording transition — the 400ms behavioral pause, then the body clearing. This is the longest motion event in Atlas and the one most charged with meaning. The clearing of the body uses the motion token for Fade (the editing content fades out). The Final Decision Card's entry uses the motion token for Insert (it appears from below, settling into the center of the cleared space). Duration: deliberate (350–400ms).

Suggestion appearance: Quiet entry from below. The Atlas Suggestion panel enters from below the field it addresses, using the motion token for Insert. Dismissal uses the motion token for Remove (fade and compress upward). Duration: brief.

Comparison: Spatial and comprehensible. When the user switches between alternatives in a comparison or navigates between historical versions, the transition communicates directionality — newer content comes from the right, older content goes to the left (or equivalent). Duration: standard.

Navigation: Purposeful and oriented. The auto-scroll to an incomplete field or a deep-link target uses the motion token for Navigate — a smooth scroll that decelerates as the target enters view. Duration: depends on scroll distance; brief for short scrolls, standard for long scrolls.

Focus motion: Immediate. The focus ring appears instantly on Tab focus. It does not animate in — its sudden appearance is itself an orientation signal.

⸻

10. Motion Tokens

Motion tokens are the reusable building blocks of the Atlas motion system. They define the nature of a transition, not its specific duration. Duration is contextually determined by the component and content scale.

Open: Used when content comes into existence where there was none, or when a Workspace overlay appears. Character: directional — the content enters from a consistent direction (below for overlays, downward for expansion). Easing: ease-out (fast initial movement, settling deceleration). Applied to: Workspace opening, Atlas Suggestion appearance, bottom-sheet panels on mobile.

Close: Used when content exits completely, or when a Workspace overlay dismisses. Character: directional in reverse. Easing: ease-in (gradual acceleration to exit). Applied to: Workspace closing, Atlas Suggestion dismissal, unsaved-changes panel closing.

Expand: Used when an existing element grows to reveal more content beneath it. Character: the header remains stationary; content grows downward. Easing: ease-out. Applied to: section expansion, alternative row expansion, assumption row expansion.

Collapse: Used when an element shrinks, concealing expanded content. Character: content shrinks upward to the summary. Easing: ease-in. Applied to: section collapse, row collapse.

Highlight: Used to draw attention to a specific element — a newly triggered monitoring condition, an auto-expanded section. Character: a brief emphasis pulse (increased visual weight for one cycle, returning to normal). Easing: ease-in-out. Applied to: auto-expanded section items, newly surfaced contradictions, triggered monitoring conditions. Duration: brief.

Fade: Used when content exits without implying a spatial direction. Character: opacity transitions from full to zero. Easing: ease-in. Applied to: the body clearing after recording, the dimming of the underlying surface when a Workspace opens.

Replace: Used when one piece of content is substituted for another in the same position. Character: the outgoing content fades and compresses slightly; the incoming content fades in and expands from slightly smaller. Easing: ease-in-out for the outgoing; ease-out for the incoming. Applied to: the transition to historical view within a Workspace, content updating after Atlas analysis.

Insert: Used when new content arrives in an existing layout — a new suggestion appears, the Final Decision Card settles into place after recording. Character: the content enters from slightly below its final position, decelerating to rest. Easing: ease-out. Applied to: Final Decision Card post-recording entry, Atlas Suggestion initial appearance.

Remove: Used when content exits an existing layout without the space closing. Character: the content fades and compresses. Easing: ease-in. Applied to: Atlas Suggestion after dismissal (before the space closes), acknowledgment controls after acknowledgment.

Navigate: Used for scroll transitions — auto-scroll to an incomplete field, a deep-link target, or a newly highlighted section. Character: smooth scroll with deceleration as the target approaches the viewport center. Easing: ease-in-out for the scroll curve. Applied to: all programmatic scroll events.

Update: Used when content changes in place — a status label transitions from one state to another, the Final Decision Card field updates as the user edits above. Character: a very brief cross-fade between the old and new value. Easing: ease-in-out. Duration: immediate to brief. Applied to: status changes, live-updating Final Decision Card fields.

Loading: Used when content is waiting for Atlas analysis. Character: a minimal opacity pulse on the loading indicator (not on the content itself — the content shows its last-known state). Easing: ease-in-out, looping. Duration: continues until loading completes. Applied to: the inline loading indicator adjacent to updating elements.

Reduced-motion fallback: All motion tokens have a reduced-motion variant — instantaneous transition with no animation. When the OS prefers reduced motion, all motion tokens produce their reduced-motion variant. The Highlight token produces no visual pulse. The Expand and Collapse tokens produce an instantaneous height change. The Navigate token produces an instantaneous scroll (the target appears immediately without animated travel). The 400ms post-recording behavioral pause is preserved — it is not a motion token and therefore not subject to motion reduction.

⸻

11. Interaction Tokens

Interaction tokens define the behavioral state of any interactive element — independent of the element's visual appearance. The visual treatment of each token is specified in UX-012B (Section 18) and UX-011 (visual layer). Here, the semantic meaning and behavioral rules are defined.

hover: The element is being pointed at by a pointer device. Interaction tokens for hover: edit affordances become visible, expand affordances shift emphasis, inline action controls appear. The hover token never creates interactive affordances that do not exist on touch — all hover-revealed content must have a persistent touch equivalent.

pressed: The element is being actively held down — between pointer-down and pointer-up, or during a touch activation. Character: a brief visual acknowledgment that the element has been activated. Not a sustained state — it resolves to the next state (activated, focused) within one interaction cycle.

focused: The element is the current keyboard focus. Focus ring is visible. Tab will move to the next focusable element. Enter or Space will activate the element.

selected: The element has been chosen from a set of options — a monitoring item, a historical record in a list, a comparison alternative. Selection persists until the user explicitly selects something else or exits the context.

disabled: The element exists but cannot currently be activated. Rendered at reduced opacity. Cursor is not-allowed on pointer devices. Tab order may skip disabled elements in most cases, but primary actions in disabled state remain in the tab order (the user should be able to reach them and understand why they are disabled).

editing: The element contains an active editing session. For Long-form Editor and Short Statement: text cursor is visible, the autosave interval is active, the undo history is active. For the surrounding document: the low-opacity dimming is active.

expanded: The element is in its full-content state. The collapse affordance is available. The content within is in the tab order.

collapsed: The element is in its summary state. The expand affordance is available. The content within is not in the tab order (it is not rendered or is hidden from assistive technology).

loading: The element is waiting for system data or Atlas analysis. The loading indicator is active. The last-known state is shown in the element's content area. The element is non-interactive while loading.

saved: The most recent edit has been committed to the autosave. The Draft Indicator reflects the saved state.

unsaved: Edits exist that exceed the autosave interval without being saved. The Draft Indicator reflects the unsaved state. The Workspace close protection activates.

updated: The element's content has changed since the user's last session. The "UPDATED" label is visible in metadata scale at the section label level.

historical: The element is presenting a prior record. All content is read-only. The historical visual treatment is active (tertiary text color, reduced opacity, timestamp visible). No editing is possible.

acknowledged: The user has explicitly confirmed awareness of a challenge, contradiction, or triggered monitoring condition. The acknowledgment control disappears. The item remains visible but at reduced emphasis. The acknowledged state is recorded in the session context.

⸻

12. Responsive Philosophy

Atlas's responsive strategy preserves the reasoning experience across form factors. It does not merely reflow a desktop layout. At each breakpoint, the specific cognitive demands of the user's context inform what is shown, what is collapsed by default, and what is adapted for the interaction model of the device.

The governing principle: the user must be able to complete the same reasoning at the same quality on any device. A decision that is well-considered on desktop must be equally well-considered on mobile. The difference is not the quality of reasoning available — it is the pace and the surface area of presentation.

Desktop reasoning mode: The user is seated, focused, with sustained attention available. They may have multiple windows or tabs open. They are comparing, writing, and reviewing in an extended session. Atlas on desktop optimizes for: deep reading (full editorial column width, maximum line length), sustained writing (the Long-form Editor at full desktop scale), multi-section awareness (multiple sections expanded simultaneously), and comparison (two-column comparison layouts available).

Tablet reasoning mode: The user has focused attention but may be in a less structured environment. They are reading and making decisions, possibly annotating. The session may be shorter. Atlas on tablet optimizes for: full reasoning flow (all sections accessible, all decision tasks completable), comfortable touch interaction (full-row tap targets, bottom-sheet panels), and preserved reading quality (editorial column narrows, spacing reduces proportionally).

Mobile reasoning mode: The user has focused but potentially brief attention. They may be checking a monitoring trigger, reviewing a prior decision, or completing a specific section. Atlas on mobile optimizes for: efficient scanning (collapse defaults more aggressively), focused section reading (the expanded section fills most of the visible viewport), and lightweight editing (short statements and decision selectors are well-adapted; long-form writing opens in a full-screen mode).

The question for every responsive adaptation: Does this adaptation preserve the user's ability to reason clearly? If collapsing an element on mobile means the user cannot understand the section's current state, the element must not be collapsed — the section summary must include its substance.

⸻

13. Responsive Navigation

Workspace opening: Desktop — overlay at 94vw × 93vh, centered, with underlying surface visible at the edges. Tablet — full-screen overlay, underlying surface not visible. Mobile — full-screen overlay, safe-area-aware header and footer.

Section navigation: Desktop — all sections accessible by scrolling; no section-jump navigation needed for typical Workspace lengths. Tablet — same as desktop. Mobile — a section-jump control may appear at the top of the scrolling body for very long Workspaces (Decision Workspace with all sections expanded) — a compact horizontal list of section labels that scrolls to the tapped section. This control appears only on mobile and only for Workspaces with more than eight sections.

Return behavior: Desktop and tablet — the return/close control in the fixed header. Mobile — same, plus the device's native back gesture (where supported) triggers the Workspace close behavior (with the same unsaved-changes check as the explicit close).

Sticky controls: Desktop — fixed header and footer only. No content within the scrolling body is sticky. Tablet — same. Mobile — the fixed header and footer. On very long expanded sections (an assumption list with many items), the section label may become sticky at the top of the viewport as an orientation anchor while the user scrolls through the section's content.

Scrolling: Desktop and tablet — standard scroll within the fixed-header/fixed-footer overlay. Mobile — standard scroll. The scroll velocity deceleration at visual pause points applies on all devices.

Action placement: Desktop — primary action in the footer, right-aligned. Secondary actions adjacent to it. Tablet — same. Mobile — primary action full-width at the bottom of the footer safe area. Secondary actions stacked above the primary action if space allows; moved to a "More options" disclosure if the footer height would exceed a defined maximum.

History: Desktop and tablet — the version history panel opens as an inline panel within the body (right-aligned alongside the content). Mobile — the version history panel opens as a bottom sheet.

Draft recovery: On any device, if the user opens a Workspace where a draft exists from a prior session, the draft is automatically restored. A brief Draft Indicator message appears at the top of the scrolling body: "Draft restored from [relative date]." This message auto-dismisses after five seconds.

⸻

14. Responsive Components

Workspace Frame: Desktop — overlay proportions as defined. Tablet — full-screen. Mobile — full-screen with safe-area insets applied to header and footer. In all cases, the proportional relationship between header height, body, and footer height is preserved — the header and footer remain minimal.

Section: Desktop — full editorial column within the overlay body. Tablet — editorial column narrows to approximately 90% of desktop width. Mobile — full content width minus margins. Collapse behavior is identical across all devices. Expand behavior is identical. The collapsed summary is always the full two-line summary regardless of device.

Decision Card (Final Decision Card): Desktop — full editorial column, elevated surface, generous internal padding, all six fields visible. Tablet — same, slightly narrower. Mobile — full content width, internal padding reduced slightly. All six fields visible — the card is never truncated on mobile. The card's visual authority is preserved across all devices.

Monitoring Condition: Desktop — full-width row within the Monitoring Section. Tablet — same. Mobile — same; lifecycle state label may move to a second line below the condition statement if the row width cannot accommodate both on one line.

Comparison (Alternative Comparison, Opportunity Cost): Desktop — two-column layout (decision subject and alternatives side by side, with the conclusion line spanning full width below). Tablet — two-column layout preserved if viewport width permits; collapses to sequential single-column if not. Mobile — sequential single-column: decision subject first, alternatives in order, conclusion line last. The reading order is preserved; only the spatial relationship changes.

Historical Record: Desktop — the historical surface treatment with timestamp. Tablet and mobile — same; the timestamp may move to a compact label format on smaller viewports.

AI Suggestion: Desktop — the suggestion panel appears below the field it addresses, within the body column. Tablet — same. Mobile — the suggestion panel appears as a bottom sheet, floating above the keyboard if the field is focused.

Completion: Desktop — the Completion Section at the bottom of the body, above the footer. Tablet — same. Mobile — same; the Record Decision button in the footer is full-width, at the safe-area bottom.

⸻

15. Editing Behavior

The editing model is unified across all editable fields in Atlas. Whether the user is writing their decision statement, updating an assumption, or editing a review condition, the behavioral rules are the same.

Focus and entry: Clicking or tapping a field activates it — the field enters the editing token state. On mobile, activating a Long-form Editor opens the full-screen editing mode. The keyboard appears and the field is scrolled into view above it.

Autosave: Every 30 seconds during an active editing session, the current state of all edited fields is saved to a draft. Autosave is transparent — the Draft Indicator updates to show the timestamp; there is no visual interruption or confirmation. If the user closes the Workspace between autosave intervals, the close protection activates if the time since last autosave contains meaningful new content.

Undo: Character-level undo is handled by the OS/browser native undo behavior within the field. Structural undo — accepting an Atlas Suggestion, deleting a complete field's content — is handled by a five-second undo window specific to Atlas. Within this window, a small "Undo" control appears adjacent to the affected field. Activating it reverses the structural change. After five seconds, the structural undo expires and standard character-level undo resumes.

Redo: Standard OS/browser redo for character-level editing. No structural redo is provided — the five-second undo window is the only structural reversal mechanism.

Validation: Editing validation in Atlas is soft and deferred. Fields do not show error states while the user is actively editing. Soft validation (the inline improvement suggestion — "Consider adding a specific observable threshold") appears after the user has left the field (on blur), not while they are typing. Completion gate validation appears only when the user activates the primary action, not during editing.

Draft management: The draft is the current state of all edited fields in the Workspace. It is identified by Workspace, investment subject, and session. On opening a Workspace where a draft exists, the draft is automatically restored. The user can compare the draft with the last recorded version (for amendment sessions) using the "Compare with recorded →" link in the version history panel. Discarding the draft is a deliberate action — it requires the explicit "Discard" option in the close protection panel or in the version history panel.

Versioning: When the user edits a recorded decision (creating an amendment), the existing recorded content is preserved as a Historical Record. The editing session creates a new draft that, when recorded, becomes the new active record. The prior record is linked from the Historical Timeline Entry component. The user can view both the prior and current content in a Historical Comparison component.

AI collaboration during editing: The Atlas Suggestion panel may appear after an editing pause. The user may also explicitly request Atlas assistance through an inline "Ask Atlas" control that appears at the bottom of the Long-form Editor when the field is focused. Either mechanism produces an Atlas Suggestion, Atlas Clarification, or Atlas Warning component adjacent to the field.

Read-only transitions: When the Decision Workspace transitions to post-recording state, all editable fields transition to read-only. The field's editing chrome disappears — no border, no edit affordance. The field text renders in primary weight and color as static document text. This transition uses the motion token for Update — a brief cross-fade from the editing state to the document state.

Historical locking: Historical records are permanently locked. No field within a Historical Section can be focused, edited, or activated (except for expand/collapse controls and navigation links). The historical lock is a system-level state that cannot be overridden by any user action. This is the primary mechanism by which historical integrity is preserved.

⸻

16. AI Interaction

Atlas AI assistance is contextual, secondary, and always explicitly attributed. The user never encounters AI-generated content without knowing it is AI-generated. The user never feels they are in a conversation with a chatbot — they are working on a document, and Atlas has prepared parts of it and may offer improvements.

Suggestion appearance: The Atlas Suggestion panel appears after a 1.5-second pause in the user's editing — enough time to complete a thought but brief enough that the suggestion feels timely. The panel uses the motion token for Insert. On first appearance, the user's attention is not forced to it — it appears in the peripheral content area below the field. The user may continue editing and the suggestion remains available until they interact with it or navigate away.

Accept: The user accepts the Atlas suggestion by activating the "Accept" control. The field content replaces with the suggestion text. The field transitions to Accepted state ("Atlas Suggested / User Accepted") — authorship is not yet transferred; only a subsequent genuine edit transitions it to user-modified-from-atlas state. The attribution indicator appears in metadata scale below the field. A five-second structural undo window activates.

Partial accept: The user activates "Partial accept." The suggestion text appears with segment boundaries visible — individual sentences or clauses are selectable. The user taps or clicks segments to confirm them. Confirmed segments render at primary text weight; unconfirmed segments render at tertiary. When the user completes their selection, the confirmed segments assemble in the field. The five-second undo window activates.

Dismiss: The user dismisses the suggestion by activating "Dismiss" or by pressing Escape while the suggestion panel is focused. The panel exits using the motion token for Remove. The suggestion does not reappear during the current editing session for this field.

Undo: After accepting a suggestion (full or partial), the five-second structural undo window allows the user to reverse the acceptance. After the window expires, the change is part of the standard undo history.

History: Atlas suggestions are not recorded in the decision record. The decision record contains only the final content of the field — what the user authored or confirmed. A session log (accessible from the version history panel for the session) may show the suggestions that were offered and how the user responded, but this is implementation-level detail and not required in the primary Atlas experience.

Comparison: When an Atlas Suggestion is present, a "View difference →" control appears within the suggestion panel. Activating it shows a before/after view — the current field content on the left, the suggestion on the right (on desktop). On mobile, the comparison is sequential: current content above, suggestion below. The comparison view has its own Accept and Dismiss controls, which behave identically to the standard suggestion controls.

The governing rule for all AI interaction: Atlas suggests; the user decides. No AI suggestion is accepted without explicit user confirmation. Atlas never silently modifies field content. The user's authored content is never overwritten without a visible action, a visible transition, and a reversal mechanism.

⸻

17. Loading Behavior

Atlas communicates loading states honestly and minimally. The user should always understand whether Atlas is working and what it is working on.

Inline loading indicator: When a section's Atlas-generated content is being updated (analysis has changed, a monitoring condition is being evaluated), a small loading indicator appears adjacent to the section label — not within the content area. The content area shows the last-known state while loading. The loading indicator uses the motion token for Loading. On loading completion, the indicator disappears (motion token: Remove) and if the content has changed, the section acquires the Updated state.

Minimum display duration: The loading indicator is shown for a minimum of 300ms even if the loading resolves faster. This prevents a visual flash that would be more disorienting than informative.

Maximum wait time: If loading exceeds three seconds, a brief text note appears adjacent to the loading indicator: "Updating analysis..." at secondary text scale. This note communicates that Atlas is working and has not stalled. After ten seconds, if loading has not resolved: "Taking longer than usual — continuing in the background." The user may continue reading and editing; the update will apply when it arrives.

Failed loading: If Atlas cannot complete an analysis update (network failure, service unavailability), the section remains at its last-known state. A quiet note in metadata scale appears below the section: "Analysis could not be updated · [date of last update]." A "Retry →" link is available. The user's work and reasoning are unaffected — only the Atlas-generated analysis content is stale. The user is never blocked from reading or completing their decision because Atlas analysis failed to load.

Decision record saving: When the user records a decision, the system saves the record. The saving state uses the motion token for Loading on the primary action control — the button text does not change, but a subtle loading indicator appears within it. On save completion, the 400ms behavioral pause begins. If saving fails, the body does not clear. An error note appears in the footer: "Recording failed — your draft is preserved. Try again →" The user is never left uncertain about whether their decision was saved.

Atlas analysis generation: When Atlas is generating a new conclusion (after a portfolio rebalance, after a thesis change), the Workspace may show a loading state for the Primary Conclusion component while generation completes. A note within the conclusion container: "Atlas is preparing the updated conclusion..." at secondary text scale. The previous conclusion remains visible below this note until the new one is ready. When ready, the Replace motion token is used to substitute the new conclusion.

The governing rule: loading states are truthful. Atlas does not show fake progress. Atlas does not simulate "thinking" with theatrical animation. Loading states communicate the actual system state — processing, complete, or failed.

⸻

18. Validation Behavior

Validation in Atlas is proportional to the risk. Soft validation identifies opportunities to improve — it does not block. Hard validation (the completion gate) identifies conditions that make the decision incoherent — it prevents recording but does not interrupt editing.

Incomplete reasoning (soft): When a field contains content that could be more precise — a review trigger that is vague, an assumption without a specific threshold, a decision statement that does not specify a position — a soft validation note appears below the field on blur. The note uses the Atlas Warning component at Informational severity. It explains the specific improvement and why it matters. The user may ignore it. The Workspace's completion gate is not affected.

Missing information (soft to hard depending on field): Some fields are required for the completion gate (at least one invalidation condition, a review condition, the decision statement, the primary reason). If these fields are empty when the user activates the primary action, the completion gate activates. The footer explanation names the specific missing field. An auto-scroll navigates to the field. The required fields are never marked with a red asterisk or an inline error state — they are identified only when the user attempts to record without them.

Contradiction (informational to material): A contradiction between the user's current reasoning and prior decisions or portfolio strategy is communicated through the Atlas Warning component. Informational severity: the warning is inline and does not affect the completion gate. Material severity: the warning is prominent within the Challenges section and produces a footer explanation note ("Consider addressing the identified contradiction before recording"). Unresolved severity: the warning includes a mandatory acknowledgment step. Acknowledged-but-unresolved: the completion gate allows recording but the acknowledgment is recorded in the session context.

Blocking issue: The only conditions that fully disable the Record Decision button are: the decision statement field is empty, and the primary reason field is empty. All other missing content produces soft validation. The reasoning: a decision without a statement and a reason is not a decision. A decision without an invalidation condition is incomplete but still represents the user's considered judgment.

Historical conflict: If the user's draft decision conflicts with a prior recorded decision in a way that would make the history incoherent (recording a decision that contradicts itself within the same investment context), Atlas surfaces this as a Material Warning. The warning names the prior decision, shows the conflict, and offers three options: "View prior decision," "Create superseding decision instead," and "Acknowledge and continue." Blocking is not applied — the user may record the decision regardless. The acknowledgment is recorded.

Recovery from validation: All validation in Atlas is recoverable. The user can return to any field from any point in the Workspace, correct or update it, and the validation state clears. Validation is never sticky beyond its natural resolution.

⸻

19. Error Behavior

Errors in Atlas communicate clearly what is wrong, why it matters, whether the user's work is preserved, and what they can do next.

Technical error: A failure in the Atlas system or network connection that prevents content from loading or being saved. Presentation: a quiet note in metadata scale within the affected element ("Unable to load this section — check your connection and retry →"). The user's draft is preserved. Other sections that loaded successfully are not affected. The error note is self-contained — it does not propagate to the Workspace footer or header.

Unavailable data: Atlas cannot generate analysis for a specific section because source data is unavailable (the investment has no recent filings, a portfolio calculation is pending). Presentation: the section shows the unavailable empty state: "Analysis is not currently available for this section. [Reason if known] — this section will update when data becomes available." The user may continue working on all other sections. The decision may be recorded without this section's content if the user chooses.

Connection loss: The user has lost network connectivity during an active editing session. Presentation: a Draft Indicator change to "Working offline — your changes are saved locally." The autosave continues to local storage. On reconnection, the local draft is synced. No interruption to the user's editing experience is necessary.

Permission error: The user attempts to access a Workspace or record they do not have permission to view. Presentation: the Workspace frame opens (to confirm the navigation arrived) but the body shows: "You do not have access to this record. [If applicable: Request access →]." The user can close the Workspace and return to their prior surface.

Missing source: A link to a source Workspace or analysis reference resolves to a record that no longer exists (has been deleted or is unavailable). Presentation: a quiet note in metadata scale adjacent to the link: "Source no longer available." The link is non-interactive. The decision or analysis that referenced the source is not affected.

Incomplete calculation: A portfolio consequence or concentration calculation cannot be completed because position data is partially missing. Presentation: the affected component shows the calculation with a note: "Based on partial portfolio data — [N] positions could not be included." The calculation result is shown with the caveat, not withheld entirely.

Preservation of work: In all error conditions, the user's draft is preserved. This is non-negotiable. No error state in Atlas may result in the loss of user-authored content. If a save operation fails, the content remains in the local draft. If the Workspace closes unexpectedly, the draft is recoverable on next open. The Draft Indicator always reflects the true save state so the user can make an informed decision about whether to close.

Recovery behavior: Every error state includes a specific recovery action. "Retry →" for transient failures. "Check connection" for network errors. "Request access →" for permission errors. No error leaves the user without a clear next step.

⸻

20. Empty-State Interaction

Empty states in Atlas communicate four distinct meanings, each with different interaction implications:

Positive absence: The system has evaluated a condition and found nothing of concern. This is a good outcome, not a failure. Presentation: "No contradictions identified for this decision." — secondary text, no icon, no placeholder. The section has the same structural presence as a populated section. Interaction: the section remains collapsible. Its collapsed summary reflects the positive absence ("CHALLENGES · None identified"). No action is required or available.

Unavailable result: The system cannot complete an evaluation because data is insufficient or the analysis has not been run. Presentation: "Analysis is not currently available — this section will update when data is ready." — secondary text. Interaction: no action is available to the user to force the result. The section exists and is collapsible, showing its empty state in both collapsed and expanded forms.

Incomplete data: The system has partial data and the result may be inaccurate. Presentation: "Some data is incomplete — results may be approximate." — secondary text with a qualification note. Interaction: the section shows its partial result (not withheld) with the qualification. No action is required.

User action required: The section is empty because the user has not yet provided the necessary input. Presentation: the section shows the empty state with an instruction. "No invalidation conditions set. Add a condition to help Atlas monitor this decision →" — secondary text, a link to the relevant editing affordance. Interaction: the link activates the editing mode for the first item in the section. This is the only empty state where an action is prompted.

Empty Workspace: When the Decision Workspace is first opened with no prior analysis and no user input, each section shows its empty state according to the above categories. Sections that Atlas has pre-populated (the Current Conclusion, the Proposed Decision) show their Atlas-generated content. Sections that await user input (the decision statement, the primary reason) show the user-action-required empty state.

⸻

21. Completion Behavior

Recording a decision is the most significant action in Atlas. The interaction model at this moment must communicate finality without pressure, and calm without dismissiveness.

Pre-completion state: The Completion Section is visible at the bottom of the Workspace body. The Final Decision Card shows the live-updating draft state — all six fields reflecting the current content of the Workspace above. The footer shows the Record Decision button. If the button is unavailable (`aria-disabled="true"`), the footer explanation names the specific missing content. The user may return to any section above to complete missing content. *(Corrected per ADR-002/C-06, Phase 6C — 2026-07-29: this line previously used "disabled" without qualification.)*

Completion gate check: When the user activates the Record Decision button, the system evaluates the completion gate conditions. If all conditions are met, the recording proceeds. If a required field is missing, the button remains in the unavailable state (`aria-disabled="true"`), the footer explanation updates to name the specific missing content, and the Workspace auto-scrolls to the missing field. *(Corrected per ADR-002/C-06, Phase 6C — 2026-07-29: this line previously used "the disabled state" without qualification.)*

Recording transition: On successful activation, the button enters the loading state. The system saves the record. On save confirmation (from the server), the 400ms behavioral pause begins. During this pause, the Workspace is fully visible and non-interactive — a deliberate moment before the transition.

Body clearing: After the 400ms pause, the scrolling body content above the Completion Section fades out using the motion token for Fade. The process is clean and immediate — the analytical content that led to the decision exits without ceremony.

Final Decision Card entry: As the body clears, the Final Decision Card transitions from the Completion Section to a centered position in the now-cleared body using the motion token for Insert. The card settles into place in its completed/recorded state — all six fields in full primary text weight, the elevated surface treatment at full visual authority.

Post-recording content: Below the Final Decision Card, three elements appear using Insert: the confirmation line ("Decision recorded · [date] · [investment name]") in metadata scale; three contextual next steps as primary body text links ("Return to [Workspace name]", "Set up monitoring →", "View implementation →"); and the footer simplifies to "Close Workspace."

Saving a draft: The secondary action "Save Draft" saves the current Workspace state without recording. The Workspace remains open. The Draft Indicator updates. No transition occurs in the body. This action is always available, always reversible, and never confused with Recording.

Acknowledging a challenge: When the user acknowledges a challenge or contradiction using the acknowledgment control, the control's visual state changes to the acknowledged token — it dims and the "Acknowledged" label appears. The challenge item remains visible but at reduced emphasis. The acknowledgment is silent — no confirmation, no animation beyond the token state change.

Finishing a review: When the user completes a review (in a Review Workspace or review mode Decision Workspace), the completion behavior is the same as recording — a deliberate pause, a body transition, a settled review record. The Review Conclusion component is the analogue of the Final Decision Card in this context.

Monitoring activation: After a decision is recorded, monitoring conditions that were established in Section 9 of the Decision Workspace become active. The post-recording next steps include "Set up monitoring →" to confirm the monitoring conditions and their Atlas observation settings. Monitoring activation is not automatic — it requires the user's explicit confirmation, which may be done immediately or deferred.

Historical creation: Recording a decision creates a permanent historical record. This record is immediately accessible in the Decision History component and in the decision's own Decision Timeline. The creation of the historical record is not surfaced as a separate event — it is a consequence of recording that the user understands from the product philosophy, not from a system notification. *(Corrected per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02. Prior text: "...and in Atlas Memory." Per the completed Atlas Memory Status Investigation, "Atlas Memory" is not a canonical UX term; this decision's own chronological narrative is its Decision Timeline. The record's creation, not either successor term, is what creates permanence.)*

⸻

22. History Interaction

Open historical record: The user accesses historical content through: a link within the current Workspace ("View prior decision →"), a Historical Timeline Entry in the version history panel, or a deep link from a Decision Timeline entry or a Daily Brief item. Opening a historical record within the current Workspace uses the motion token for Replace — the body transitions to the historical view while the header updates with the Historical Indicator. Opening a historical record from an external link opens the Decision Workspace in historical mode directly. *(Corrected per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02. Prior text: "...or a deep link from Atlas Memory or a Daily Briefing item." Per the completed Atlas Memory Status Investigation, "Atlas Memory" is not a canonical UX term; this passage's own adjacent Historical Timeline Entry component already names the accepted UX-layer artifact for exactly this concept.)*

Compare: When a historical record is open, the "Compare with current →" link initiates the Historical Comparison view. The prior record appears on one side (or above on mobile), the current record on the other. Both use their respective visual treatments (historical: tertiary/reduced opacity; current: primary/full opacity). The comparison layout uses the same structure as the Alternative Comparison component — sequential on mobile, spatial on desktop.

Return from historical: A "Return to current →" link or the return/close control exits the historical view. The motion token for Replace returns the body to the current Workspace content.

Timeline: The version history panel (accessible via the "View history →" link in the Workspace or from a dedicated history control) shows Historical Timeline Entries in reverse chronological order. The user scrolls through the timeline and taps entries to expand them into their respective historical components. The version history panel opens as an inline panel on desktop (right-aligned), a bottom sheet on mobile.

Version navigation: Within the version history panel, the user may navigate forward and backward through versions. Each version is the full state of the Workspace content at the time of recording. The navigation uses the motion token for Replace within the panel — versions slide in from left (newer) or right (older) as the user navigates.

Relationship navigation: Some historical records are related to others — an amendment references the decision it amends; a superseding decision references the decision it replaces; a review record references the decision being reviewed. These relationships are visible as links within each historical component. Activating a relationship link opens the related historical record (within the panel, or navigates to it if it is in a different context).

Historical editing restrictions: No historical record content can be edited, copied to a new field using an in-place mechanism, or modified in any way. The Historical Section's interaction model is expand/collapse and navigate — nothing else. This is enforced at the interaction level (no edit affordances appear on hover; no field activates on click) and at the system level (the historical lock state prevents any write operation).

⸻

23. Monitoring Interaction

Open trigger: A monitoring trigger surfaces in the Dashboard as a Daily Brief signal. The signal shows the monitoring condition, the investment subject, and the trigger event. Tapping the signal opens the relevant Workspace (Investment Workspace or Decision Workspace) directly to the monitoring section with the triggered item auto-expanded. The auto-expansion uses the motion token for Highlight.

View status: Within any Workspace that contains Monitoring Conditions, the user may view the current status of each condition by expanding the Monitoring Section. Each condition shows its lifecycle state (Active, Approaching, Triggered, Resolved, Expired) and its current observed value relative to the trigger threshold. Approaching conditions show an amber treatment; Triggered conditions are prominently displayed with an acknowledgment control.

Review: When a Review Trigger fires, the Dashboard signal links to a review-mode opening of the Decision Workspace. The Workspace opens in review mode — the prior decision is displayed with the Historical Indicator, and the review sections are available for the user to complete. The review workflow follows the same section-by-section reading and editing model as the initial decision, adapted for the review context.

Dismiss: A monitoring item may be dismissed (removed from active monitoring) by the user from within the Monitoring Section. Dismissal is a Destructive or History-Altering Action — it requires the confirmation step. Dismissed monitoring conditions are preserved in the monitoring history (they transition to the Expired lifecycle state with a "Dismissed by user" note).

Resolve: When the user has addressed the underlying condition that triggered a monitoring item (the assumption has been confirmed, the review has been completed), they may mark the monitoring item as Resolved. Resolving requires a brief note from the user ("What action addressed this condition?") — a Short Statement field that appears when the user activates the Resolve control. The monitoring item transitions to Resolved state and is preserved in the monitoring history.

Follow decision: From a triggered monitoring item, a "View linked decision →" link opens the Full Decision Record for the decision the monitoring condition is linked to. This may open in a Historical view if the decision has been superseded, or in the current active Decision Workspace if the decision is still active.

Historical monitoring: Expired and Resolved monitoring conditions are visible in the monitoring history — accessible from the Monitoring Section via a "View history →" link. The monitoring history shows each condition in the Historical Record treatment, with its lifecycle events (Established, Approaching, Triggered, Acknowledged, Resolved/Expired) in timeline order.

⸻

24. Cross-Workspace Interaction Consistency

The user must never need to relearn an interaction pattern when moving between Atlas surfaces. The following elements are identical across all Workspaces and the Dashboard:

Section expand/collapse: The interaction — tap or click the full header row — is identical everywhere. The expansion affordance is identical. The transition is identical. A user who has used any Atlas Workspace can expand and collapse sections in any other Workspace without learning anything new.

Atlas Suggestion: The appearance, the accept/partial-accept/dismiss controls, the five-second undo window, and the non-interrupting placement below the field are identical wherever Atlas suggestions appear — Investment Workspace thesis editing, Decision Workspace reason editing, future Workspace field editing.

Monitoring condition interaction: The lifecycle states, the triggered behavior, the acknowledgment control, and the resolve action are identical whether the monitoring condition is encountered in the Dashboard signal, the Decision Workspace monitoring section, or a future Monitoring Workspace.

Historical content: The visual treatment (tertiary text, reduced opacity, timestamp) and the interaction (expand/collapse only, no editing, compare link) are identical wherever historical content appears.

Action hierarchy: Primary actions are always in the footer. Inline actions are always adjacent to the elements they act on. Tertiary actions are always low-emphasis. Destructive actions always require confirmation. This is identical across all surfaces.

Focus ring: Identical visual treatment across all surfaces, all components.

Keyboard shortcuts: The same shortcut for expanding a section works in the Investment Workspace and the Decision Workspace. The same shortcut for navigating to the footer works everywhere.

The governing rule: if a user who has only used the Investment Workspace opens the Decision Workspace for the first time, they should feel immediately competent — the structure, the interactions, and the patterns should feel familiar even though the content is different. This is the test for cross-workspace interaction consistency.

Permitted cross-workspace variation (variations that are justified by the distinct reasoning task):

The Dashboard uses signal density — the interaction model is lower-depth (tap to navigate, no in-place editing, no complex expansion). This is a justified variation because the cognitive task is scanning, not reading.

The Decision Workspace has a completion gate — the primary action may become unavailable (`aria-disabled="true"`, never native `disabled`) based on content conditions. This is a justified variation because no other Workspace has the consequence of creating a permanent, immutable record. *(Corrected per ADR-002/C-06, Phase 6C — 2026-07-29: this line previously used "disabled" without qualification.)*

The full-screen editing mode on mobile is specific to the Decision Workspace and Investment Workspace long-form fields — not appropriate for the Dashboard's compact signals.

⸻

25. Accessibility Interaction

Keyboard navigation: The full Atlas interaction model is available without a pointer device. Tab order follows the visual reading order in all Workspaces. Every interactive element — section headers, action controls, field edit controls, AI suggestion controls, monitoring acknowledgment controls, historical navigation links — is reachable by Tab and activatable by Enter or Space.

Focus order: The focus order is predictable and follows the spatial layout. In any section: section header → expanded content items (top to bottom) → section-level actions. In the Workspace: header controls → body (section by section) → footer controls.

Announcements: State changes that are not visually obvious must be announced to screen readers:
— When a section expands: "Section [name] expanded" or equivalent announcement.
— When a section collapses: "Section [name] collapsed."
— When a monitoring condition transitions to Triggered: the section auto-expands and the screen reader announces: "Alert: [condition name] has been triggered."
— When the Atlas Suggestion panel appears: "Atlas has a suggestion for [field name]. Navigate to review it."
— When the Record Decision action becomes available: "Record Decision is now available."
— When the post-recording transition completes: "Decision recorded. [Decision summary read aloud]."
— When a completion gate blocks recording: "Recording is not available: [specific reason]."

Touch interaction: All interactive elements have minimum 44×44px touch targets. Swipe gestures are not used for Atlas-specific interactions — they are reserved for native device navigation. Long-press is not used for Atlas-specific interactions. All interactions are single-tap or double-tap (for text selection within fields).

Screen readers: All structural elements have appropriate ARIA roles and labels. Section headers use the `button` role with `aria-expanded` attribute. The Final Decision Card is a landmark region with an appropriate label. Authorship is communicated through ARIA labels — Atlas-generated content has an `aria-label` or `aria-describedby` that identifies its source. Historical content is identified as such.

Reduced motion: All motion tokens produce their instantaneous variant when the OS `prefers-reduced-motion` media query is active. The 400ms behavioral pause (post-recording) is preserved — it is behavioral, not visual, and is not subject to motion reduction. The Loading token continues to show the loading indicator (opacity change is removed under reduced motion; a text indicator replaces the animation).

Error recovery via keyboard: Error states and validation notes are in the focus order — a keyboard user who reaches an error state can Tab to the error note, read it, and follow any available recovery link (Retry, navigate to missing field) using keyboard alone.

Expansion accessibility: When a section auto-expands due to Atlas behavior, the expansion announcement includes the reason: "Section [name] expanded: [reason — monitoring triggered, material contradiction detected, required field incomplete]." The focus moves to the relevant item within the expanded section, with a subsequent announcement of that item's state.

Dialogs: The one inline confirmation panel (unsaved-changes on close) follows the standard dialog accessibility model — focus moves to the panel's primary action on appearance; Tab is trapped within the panel; Escape dismisses the panel and returns focus to the close control; the panel has an ARIA role and accessible label.

⸻

26. Interaction Audit

Reviewing the entire interaction system against the governing principles defined in Section 1:

Consistent behavior: Every interaction defined in this document applies the same motion token, the same focus management, the same hover behavior, and the same state model wherever it appears in Atlas. Section expand/collapse is identical in the Investment Workspace, the Portfolio Workspace, the Decision Workspace, and the Dashboard (with signal-density adaptations). Atlas Suggestions appear and behave identically in every editing context. Historical content is treated identically everywhere.

Predictability: No interaction produces a surprising result. Every action has a visible affordance (the section header is tappable; the edit control appears on hover; the Record Decision button is in the footer). Every transition communicates what happened (the section expanded downward from the header; the Workspace opened as an overlay above the previous surface; the suggestion appeared below the field it addresses). Every state change is announced.

Minimal surprises: The only unexpected interaction in the system is auto-expansion — sections that open without the user tapping them. Every instance of auto-expansion is explained: a label within the expanded section or a screen reader announcement communicates why the section opened.

Clear navigation: The user's current location (Workspace identity in the header), their origin (return/close control, underlying surface visible), and their available destinations (inline links, action controls) are always visible or accessible.

Strong accessibility: Every interaction is fully keyboard-operable. Every state change is announced to screen readers. Every interactive element has a 44×44px minimum touch target. No interaction relies on color alone. The focus order is predictable and follows the visual layout.

Future extensibility: The interaction tokens (Section 11), motion tokens (Section 10), and interaction principles (Section 1) are defined at the system level — not tied to specific components or Workspaces. A future Review Workspace, Monitoring Workspace, or Comparative Workspace can use the same tokens without defining new interaction patterns. The cross-workspace consistency rules (Section 24) provide the governance framework for ensuring new surfaces remain consistent.

Alignment with Atlas philosophy: Every interaction supports reasoning rather than activity. The system does not create urgency (no auto-escalating timers, no aggressive loading feedback). The system does not reward activity (no badges, no streaks, no activity counts). The system preserves context across all transitions. Historical content is immutable and fully accessible. The user's judgment is always the final authority.

⸻

What UX-012C Establishes

The following interaction, navigation, and responsive behavior decisions are now fixed.

Interaction philosophy: Five governing principles (support reasoning, clarify hierarchy, reduce cognitive load, preserve context, avoid unnecessary activity) and four distinctions from other product categories (consumer apps, brokerage platforms, enterprise software, AI chat interfaces). These principles govern the evaluation of every interaction in Atlas.

Navigation philosophy: Three orientation questions (where am I, where did I come from, where can I go) always answered by the design. Nine elements preserved across all navigation (scroll position, expanded states, draft state, selected context, filters, decision context, portfolio context, source context, session context). Navigation as continuous reasoning — not page transitions.

Workspace navigation model: Open, Close, Return to Dashboard, Return to Source, Open Related Workspace, Open Historical Record, Open Monitoring, Deep-link behavior, and Browser history behavior — all fully specified with entry behavior, exit behavior, context preservation, and focus management.

Reading flow: Natural sequential progression from conclusion to completion. Scroll velocity deceleration at four visual pause points. Reading position preserved between sessions. Auto-scroll to incomplete fields using the Navigate motion token.

Expansion and collapse: Manual expansion (full header row is the tap target), auto-expansion (four triggering conditions, each with an explanation), persistent session state, cross-device independence, and animation using Expand and Collapse motion tokens.

Focus management: Keyboard, mouse, and touch focus models. Workspace transition focus. Section expansion/collapse focus. Auto-expansion focus with screen reader announcements. Dialog focus trapping. Editing focus with document dimming. Validation focus auto-scroll. The absolute rule: users never lose orientation.

Hover behavior: Section headers, long-form editor fields, Atlas-suggested content, comparison rows, links, and action controls — all with defined hover treatments. Touch devices must have persistent affordances replacing hover-revealed controls.

Selection model: Selected investment, selected section (none), selected comparison item, selected decision, selected monitoring item, selected historical record — all with defined visual consistency and behavior.

Motion philosophy: Seven governing qualities (orient, clarify, connect, reduce confusion) and four prohibitions (celebrate, gamify, create urgency, distract).

Motion tokens: Twelve tokens — Open, Close, Expand, Collapse, Highlight, Fade, Replace, Insert, Remove, Navigate, Update, Loading — each with character, easing, applied-to contexts, and reduced-motion fallback.

Interaction tokens: Fourteen tokens — hover, pressed, focused, selected, disabled, editing, expanded, collapsed, loading, saved, unsaved, updated, historical, acknowledged — each with semantic meaning and behavioral rules.

Responsive philosophy: Desktop for deep reading and sustained writing. Tablet for full reasoning flow. Mobile for scanning, review, and focused reasoning. All three must support equivalent reasoning quality.

Responsive navigation: Device-specific section jump controls on mobile for long Workspaces. Native back gesture support on mobile. Bottom-sheet history panel on mobile. Full-width primary action on mobile. Draft recovery on all devices with a auto-dismissing restoration note.

Responsive component adaptations: All twelve component types adapted for all three breakpoints — without losing reasoning content on any device.

Editing behavior: Autosave at 30-second intervals. Five-second structural undo window. Soft deferred validation (on blur, not on input). Historical locking at the system level. AI collaboration integration through the Atlas Suggestion panel and the "Ask Atlas" inline control. Full-screen editing mode for Long-form Editor on mobile.

AI interaction: Suggestion appearance after 1.5-second pause. Accept, partial accept, and dismiss — all with five-second structural undo. Dismiss is session-scoped (does not reappear for the current editing session). History is not recorded in the decision record. The governing rule: Atlas suggests, the user decides.

Loading behavior: Inline loading indicator at the section label level. 300ms minimum display duration. Three-second threshold for the extended wait note. Ten-second threshold for the background processing note. Failed loading leaves the last-known state visible. Decision record save failure preserves the draft with a retry option.

Validation behavior: Soft validation on blur for precision improvements. Completion gate for the two truly required fields (decision statement, primary reason). Contradiction acknowledgment with three severity levels. Historical conflict with three response options. No sticky validation — all validation resolves when the content resolves.

Error behavior: Technical, unavailable data, connection loss, permission, missing source, incomplete calculation — all with specific recovery actions. Preservation of work is non-negotiable in all error conditions.

Empty-state interaction: Four distinct empty state types (positive absence, unavailable result, incomplete data, user action required) — each with different presentation and different interaction implications.

Completion behavior: Pre-completion state, completion gate check, recording transition, 400ms behavioral pause, body clearing, Final Decision Card entry, post-recording content. Saving a draft, acknowledging challenges, monitoring activation, and historical record creation — all specified.

History interaction: Open, compare, return, timeline, version navigation, relationship navigation, and historical editing restrictions. Historical records are permanently locked at the interaction level.

Monitoring interaction: Open trigger (Dashboard signal to Workspace), view status, review, dismiss (with confirmation), resolve (with user note), follow decision, and historical monitoring access.

Cross-workspace consistency: Fourteen elements that are identical across all surfaces. Three justified variations (Dashboard signal density, Decision Workspace completion gate, full-screen editing). The governing test: a user who knows one Workspace should feel immediately competent in any other.

Accessibility: Keyboard navigation, focus order, screen reader announcements for all state changes, touch targets (44×44px minimum), reduced-motion fallback (all tokens instantaneous), error recovery by keyboard, expansion announcements with reason, dialog focus trapping.

⸻

Remaining Interaction Questions

1. The specific scroll deceleration implementation:
The behavioral rule (subtle velocity reduction at visual pause points) is defined. The specific implementation — whether this is achieved through CSS scroll-snap with a loose snap type, through a JavaScript scroll event listener, or through a native scroll behavior API — has not been specified. Different implementations produce subtly different felt experiences and have different performance characteristics.
Evidence needed: Cross-browser prototype testing. Does not block UX-012D.

2. The maximum number of simultaneously open Workspace overlay layers:
UX-012C specifies a maximum of two overlay layers (the originating Workspace and one related Workspace). This rule may need to be reconsidered if user research reveals workflows that require deeper navigation chains. The two-layer rule is a design judgment, not a fundamental constraint.
Evidence needed: User session observation from Investment Workspace to Portfolio Workspace to Decision Workspace workflows. Does not block UX-012D.

3. The section-jump control threshold on mobile:
The specification establishes that the section-jump control appears on mobile for Workspaces with more than eight sections. This threshold is an estimate — the exact threshold should be calibrated against the typical mobile viewport height and the typical collapsed section height.
Evidence needed: Mobile rendering tests with the Decision Workspace (nine sections) and the Portfolio Workspace. Does not block UX-012D.

4. The precise form of the partial accept interaction on mobile:
Desktop partial accept uses highlight-and-tap for segment selection. On mobile, where precision tapping on text segments may be less reliable, an alternative interaction model may be needed — perhaps a swipe-through or a word-selection metaphor. The current specification describes the desktop model and notes that mobile adaptation is required.
Evidence needed: Mobile usability testing for the partial accept flow. Does not block UX-012D.

5. The version history panel on desktop — inline or bottom sheet:
The specification says the version history panel opens as an inline panel on desktop (right-aligned alongside the content). This assumes the Workspace overlay is wide enough to accommodate a side panel without compressing the editorial column below minimum reading width. If the overlay at 94vw does not provide sufficient width for both column and panel, the panel may need to be a bottom sheet on desktop as well.
Evidence needed: Layout calculation at the confirmed overlay dimensions, editorial column width, and minimum panel width. Does not block UX-012D.

⸻

Requirements for UX-012D

UX-012D — Atlas Design System Tokens, Governance & Extensibility — will cover the implementation governance layer of the Atlas Design System: the token system, naming conventions, component governance, documentation structure, migration strategy, anti-patterns, consistency audits, and the rules for extending the system to future Workspaces.

Design tokens:
— The complete token taxonomy for Atlas: typography tokens (scale, weight, line height, letter-spacing by role), spacing tokens (the six spacing levels by name), layout tokens (column widths, overlay dimensions, reading widths), semantic color tokens (the full set established in UX-011 and referenced in UX-012B, specified as named tokens), surface tokens (the four surface levels — primary, elevated, panel, hairline), border tokens (the three border/divider weights), elevation tokens (the shadow or surface-distinction model for strong containers), radius tokens (corner radius for containers and controls), motion tokens (the twelve tokens from UX-012C, specified with duration ranges and easing functions), focus tokens (focus ring width, color, radius), state tokens (the fourteen interaction tokens from UX-012C, specified as composable visual properties), responsive tokens (breakpoint definitions, spacing scale reduction ratios for each breakpoint), accessibility tokens (minimum contrast ratios, minimum touch target size, minimum text size).
— Token naming convention: a two or three-part semantic name structure (category.role.variant — e.g., `surface.elevated`, `color.text.primary`, `space.inter-section`, `motion.expand.duration`). No raw values exposed directly — all implementation references a named token.
— Token hierarchy: global tokens (the underlying values — hex colors, pixel sizes, millisecond durations) → semantic tokens (named by meaning, referencing global tokens — `color.text.primary` references the global warm near-white value) → component tokens (component-specific overrides, referencing semantic tokens).

Component governance:
— Component ownership: each component in the Atlas Design System has a named owner (product role, not person) — the owner is responsible for the component's specification, its documentation, its versioning, and its deprecation. No component exists without an owner.
— Contribution requirements: a new component requires (1) a documented recurring product meaning, (2) evidence of recurrence across at least two surfaces, (3) a specification meeting the UX-012B component specification format, (4) an accessibility review, (5) a cross-platform review, (6) owner approval. Components that meet only visual reusability criteria are rejected.
— Naming conventions: component names describe meaning, not appearance ("Final Decision Card," not "Large Bordered Card"). Component names are consistent between the design specification, the code implementation, and the documentation. Renaming a component requires a deprecation period for the old name.
— Versioning: components use semantic versioning — major versions for breaking changes (changed required content, changed accessibility model, changed interaction model), minor versions for additions, patch versions for fixes. The version history for each component is documented.
— Deprecation: when a component is deprecated, a replacement is always specified. The deprecation notice includes a migration path and a sunset date. Deprecated components remain available for two release cycles before removal.
— Experimental variants: components may have experimental variants, clearly labeled as such, that have not yet met the full contribution requirements. Experimental variants may be used in one surface at a time while being validated. An experimental variant that proves durable is promoted through the contribution process.

Naming conventions (full system):
— Workspace names describe their reasoning purpose ("Decision Workspace," not "Decision Panel" or "Decision View")
— Section names describe their content role ("Supporting Factors," not "Supporting Section")
— Action names use Verb + Noun ("Record Decision," "Complete Review," "Dismiss Suggestion")
— State names use consistent vocabulary from the state vocabulary defined in UX-012B Section 13
— Color token names describe semantic meaning ("color.semantic.amber" not "color.warning-orange")
— Spacing token names describe relationship ("space.inter-section" not "space-32")

Documentation structure:
— Foundations layer: philosophy, typography, spacing, color, layout, motion, accessibility, language. One document per foundation area. Each document: governing principle, rules, constraints, examples of correct and incorrect application.
— Components layer: one document per component. Each document: anatomy, variants, states, interaction behavior, responsive behavior, accessibility behavior, composition rules, usage examples, anti-patterns.
— Patterns layer: one document per reusable pattern (conclusion presentation, comparison, monitoring, completion, etc.). Each document: when to use, component composition, content requirements, responsive adaptation.
— Templates layer: one document per Workspace template. Each document: entry context, section hierarchy, default expansion, editability, completion behavior, history behavior.
— Governance layer: contribution guidelines, versioning, deprecation, migration, audit procedures.

Migration strategy (staged approach):
— Stage 1 — Inventory: catalogue all current components, patterns, and token values used across existing Atlas surfaces. Identify divergences from the UX-012 system.
— Stage 2 — Semantic mapping: map current patterns to the named components in UX-012B. Identify which current implementations are correct applications of the system, which are justified variations, and which are divergences requiring correction.
— Stage 3 — Token adoption: introduce the token system into the implementation. Replace raw values with semantic tokens. This is a non-visual change and should produce no visual regression.
— Stage 4 — High-impact alignment: correct the most visible cross-workspace inconsistencies — section collapse summaries that do not follow the two-line model, hover behaviors that differ between surfaces, historical content that does not use the standard treatment.
— Stage 5 — Component implementation: create shared component implementations for the highest-reuse components (Section, Assumption, Challenge, Monitoring Condition, Decision Summary, Final Decision Card).
— Stage 6 — Surface migration: update each Workspace surface to use the shared components. One Workspace at a time. The Decision Workspace is the reference implementation — it was designed to the system.
— Stage 7 — Governance activation: apply the contribution and review processes to all future work. Audit new design and implementation work against the system before release.

Anti-patterns (a defined set that UX-012D must enumerate and explain):
— Dashboarding reasoning content (showing conclusions as metrics, charts, or statistics rather than as prose reasoning)
— Excessive card grids (arranging reasoning content in equal-emphasis tiles rather than hierarchical flow)
— Overuse of borders (drawing boxes around content that spatial organization already separates)
— Traffic-light investment judgments (using red/amber/green to imply buy/hold/sell)
— Numeric confidence (expressing confidence as a percentage or score rather than as a qualitative label)
— Persistent chat panels (providing AI assistance as a conversation sidebar rather than as in-context suggestions)
— Hidden historical edits (allowing content to change without preserving the prior state)
— Artificial urgency (using motion, color, or language to suggest that faster action is better action)
— Celebratory completion states (using success animations or positive reinforcement for recording a decision)
— Color-dependent meaning (requiring color perception to understand any semantic state)
— Opening all sections by default (removing the user's ability to prioritize which reasoning they read first)
— Turning reasoning into forms (treating the decision authoring experience as a multi-step form with required fields and progress indicators)

Consistency audit method:
— A defined checklist applied to each Atlas surface at each design review: purpose clarity, hierarchy correctness, typography compliance, spacing compliance, container usage, section anatomy, collapse behavior, authorship distinction, confidence language, state labeling, historical treatment, AI assistance placement, completion behavior, language compliance, accessibility compliance, responsive compliance.
— A distinction between true inconsistency (a pattern that diverges from the system without justification), justified contextual variation (a pattern that differs because the reasoning task requires it, explicitly justified), and obsolete patterns (patterns from prior to UX-012 that have not yet been migrated).

Future Workspace extension rules:
— Before a new Workspace is designed, ten questions must be answered: what user question does it resolve; where does it sit in the Atlas reasoning flow; what context does it inherit; what conclusion does it produce; is a new Workspace genuinely required; which existing template applies; which existing components can be reused; what new pattern, if any, is necessary; how will its output become future context; how will it preserve historical integrity.
— A new Workspace may not introduce new interaction patterns without demonstrating that the existing patterns are insufficient for the reasoning task.
— A new component required by a new Workspace must pass the full contribution process before it is used in the new Workspace's specification.

Do not produce UX-012D yet.

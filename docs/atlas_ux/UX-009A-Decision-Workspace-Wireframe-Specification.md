UX-009A — Decision Workspace Wireframe Specification

Status: Wireframe Specification Complete
Owner: Atlas Product
Governs: Decision Workspace — component hierarchy, section behavior, editing model, interaction rules
Depends on: UX-008 — Decision Workspace Philosophy, UX-009 — Decision Workspace Screen Specification
Defers to: UX-010 — Decision Workspace Visual Design

**Correction Notice (Phase 2, governed by ADR-002 — 2026-07-24):** This document's original identity (Status, Owner, Governs, Depends on, Defers to, as above) and original date are preserved unchanged. Three semantic areas were corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan, Phase 2:
- **C-03 (Decision Workspace Sequence):** Sections 5, 6, and 12 renamed to "Supporting Factors," "Challenges," and "Final Decision Card" — this document previously named them "What Supports This Decision," "What Challenges This Decision," and "Final Decision Summary" — no change to section order, count, or content.
- **C-04 (Record Decision Completion Gate):** the Validation Rules section, the "What UX-009A Establishes" summary, and the review-trigger empty states were corrected from a flat four-field rule (with Review Condition unconditionally required and no override path) to the universal minimum (Decision Statement, Primary Reason), a decision-type-conditional matrix, and an explicit override path for Review Condition.
- **C-06 (Unavailable Primary Action Accessibility):** the Fixed Footer and Section 13 unavailable-state descriptions were corrected to specify `aria-disabled="true"` (never native `disabled`), permanent focusability, and that activation while unavailable navigates focus to the first unmet required field.

This notice does not claim any of the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, at each corrected passage. All content outside these three areas is unchanged.

⸻

Overall Layout

The Decision Workspace opens as a fixed overlay above the originating Workspace, consistent with the Investment Case and Portfolio Workspace overlay pattern. The originating Workspace remains visible underneath as a passive layer, preserving context without requiring navigation back.

The overlay occupies approximately 94% of the viewport width and 93% of the viewport height. It is centered horizontally and vertically. The originating Workspace is dimmed but visible at the edges.

The layout has three persistent zones:

Fixed Header
— Spans the full width of the overlay
— Contains: decision subject label, decision type label, Atlas badge, and a close / return control
— Does not scroll
— Always visible regardless of scroll position

Scrolling Body
— The full content area between the header and footer
— Contains all thirteen sections in order
— Scrolls vertically only
— Content is constrained to a maximum reading width (approximately 760px) and centered within the body
— Sections are separated by thin horizontal dividers

Fixed Footer
— Spans the full width of the overlay
— Contains: primary Record Decision action, secondary actions (Save as Draft, Return to Workspace), and the completion gate explanation when the primary action is unavailable (`aria-disabled`, never native `disabled`)
— Does not scroll
— Always visible

The user always knows where they are: the decision subject and type are in the header, the current position in the narrative is visible by scroll position, and the Record Decision action is always reachable at the footer without scrolling to the bottom.

⸻

Fixed Header — Component Specification

Left side:
— Decision subject: the investment name (for investment-level decisions) or "Portfolio" (for portfolio-level decisions), rendered as the primary label
— Decision type label: the current decision type from the controlled vocabulary (Initiate / Add / Maintain / Reduce / Exit / Avoid / Defer / Reallocate / etc.), rendered as a secondary label immediately below or adjacent to the subject

Right side:
— Atlas badge: a subtle indicator that this is an Atlas Decision Workspace (distinguishes the overlay from the Investment Workspace behind it)
— Return to [Workspace name] control: labeled precisely — "Return to LVMH Workspace" not a generic back arrow. Tapping or clicking this returns the user to the originating Workspace without recording.
— Close control: closes and dismisses the overlay entirely. If a draft exists, prompts once before dismissing.

The header does not contain progress indicators, step counts, or completion percentages. The Workspace is a document, not a wizard.

⸻

Fixed Footer — Component Specification

Primary action:
— Label: "Record Decision"
— Occupies the right portion of the footer
— Two states: Available (full emphasis) and Unavailable (reduced emphasis, not-allowed cursor). The unavailable state carries `aria-disabled="true"` — never the native HTML `disabled` attribute — and the control remains focusable and in the natural tab order throughout. *(Corrected per ADR-002/C-06: this line previously named the state "Disabled" without qualification, which could be read as native `disabled` semantics that would remove the control from the tab order.)*
— When unavailable: a single-line explanation sits adjacent to the button, and is also exposed via `aria-describedby`, naming the specific incomplete requirement. Not a generic error. Example: "State a primary reason before recording." This text updates as requirements are met. Activating the action while unavailable does not record the decision — it moves focus to the first unmet required field and re-announces the explanation there.
— The primary action does not animate, pulse, or draw unnecessary attention

Secondary actions (left side of footer):
— "Save as Draft" — saves current state without committing. Available at any time.
— "Return to Workspace" — navigates back without saving. If a draft exists, prompts once.

The footer does not contain progress indicators or section navigation controls.

⸻

Section 1 — Current Conclusion

Position: Top of the scrolling body. Always visible. Never collapsible.
Width: Full reading width.

Components:

Conclusion card — a contained surface, visually distinct from the sections below it

  Top area of card:
  — Section label: "CURRENT CONCLUSION" — rendered as a small uppercase label
  — Source reference: "[Investment Workspace / Portfolio Workspace] · Reviewed [date]" — rendered as a secondary label

  Body of card:
  — Conclusion statement: the essential conclusion in one to three sentences. This is the most prominent text element at the top of the Workspace.
  — Confidence indicator: a small labeled badge showing the conclusion's confidence level. Four states: High Confidence / Moderate Confidence / Low Confidence / Evidence Incomplete. The label is text-only — no traffic-light colors at this specification level.

  Bottom of card:
  — "View full analysis →" link: opens the originating Workspace as a nested context without navigating away from the Decision Workspace. The originating Workspace slides in from the side or appears as a secondary overlay, allowing the user to read the supporting analysis and return to the same scroll position in the Decision Workspace.

Interaction ownership: Atlas-generated. Read-only. The conclusion cannot be edited in the Decision Workspace — if it is wrong, the user returns to the originating Workspace.

Collapsed state: none. This section is always fully visible.

⸻

Section 2 — Why a Decision Is Required

Position: Immediately below Section 1. Always visible. Never collapsible.
Width: Full reading width.

Components:

Section label: "WHY A DECISION IS REQUIRED" — small uppercase label

Primary trigger block:
  — Trigger label: one of the eight defined trigger types rendered as a short label:
    THESIS CHANGE / VALUATION CHANGE / PORTFOLIO CONFLICT / OPPORTUNITY COST / SCHEDULED REVIEW / INVALIDATION SIGNAL / NEW EVIDENCE / USER-INITIATED
  — Trigger elaboration: one sentence of Atlas-generated explanation immediately below the label. Example: "The core thesis assumption about Chinese luxury demand has been reclassified as Broken."

Supporting triggers block (when more than one trigger applies):
  — Rendered as a compact secondary list below the primary trigger block
  — Each supporting trigger: trigger label + one-line elaboration
  — Maximum two supporting triggers shown without expansion

User note field:
  — A lightly prompted optional text field: "Add context for this decision →"
  — Collapses to a single line until the user taps to add text
  — If left empty: shows nothing in the saved record (not "No note added")

Interaction ownership: Primary trigger and elaboration are Atlas-generated, read-only. User note field is user-owned, optional, unlocked until recording.

Collapsed state: none.

⸻

Section 3 — Proposed Decision

Position: Below Section 2. Always visible. Never collapsible.
Width: Full reading width.

This section contains the most prominent user-editable element in the entire Workspace. Its visual weight must be higher than any other interactive element.

Components:

Section label: "PROPOSED DECISION" — small uppercase label

Atlas proposal block:
  — Clearly labeled: "Atlas suggests" — rendered as a small secondary label, visually distinct from user-owned elements
  — Atlas's proposed decision: stated in one clear sentence
  — Decision type indicator: the suggested decision type from the controlled vocabulary, shown as a small label

User decision field:
  — Rendered as a text area, not a standard input field — it is a statement, not a form value
  — Initially pre-populated with Atlas's proposed decision text, but fully user-editable
  — The field must feel like authoring — the cursor is a text cursor, not a pointer
  — Placeholder text (when cleared): "State your decision."
  — No character limit displayed unless the user approaches a practical maximum

Decision type selector:
  — A compact grouped selector below the user decision field
  — Shows the full decision vocabulary organized into two groups:
    Investment: Initiate · Add · Maintain · Reduce · Exit · Avoid · Defer
    Portfolio: Reallocate · Reduce Concentration · Accept Concentration · Maintain Structure · Preserve Liquidity · Rebalance Conviction
    Review: Thesis Valid · Thesis Requires Revision · Evidence Insufficient · Postponed
  — Currently selected type is visually indicated. The user may change the type at any time before recording.

Modification indicator:
  — If the user has changed the decision text from Atlas's proposal: a small inline note appears: "Modified from Atlas proposal" — this is preserved in the decision record to support future pattern analysis
  — If the user has restored the original text: the indicator disappears

Interaction ownership: Atlas proposal block is read-only. User decision field and decision type selector are fully user-editable until recording. Both are locked after recording.

Validation: the user decision field must contain text before Record Decision is available. An empty field disables recording with the explanation: "State your decision before recording."

Collapsed state: none. This section is always fully expanded.

⸻

Section 4 — Decision Rationale

Position: Below Section 3. Expanded by default for major decisions. Collapsed by default for Maintain, No Action, and Scheduled Review decisions.
Width: Full reading width.

Components:

Section header (always visible when section exists):
  — Section label: "DECISION RATIONALE"
  — Collapse / expand control: right-aligned chevron
  — Collapsed summary (when collapsed): the first sentence of the primary reason field, truncated at approximately 80 characters, followed by an ellipsis

Expanded state:

Primary reason field:
  — Labeled: "Primary reason"
  — A text area — the user's own first-person explanation of why they are making this decision
  — Placeholder: "Why are you making this decision?"
  — Required. The Record Decision action remains unavailable (`aria-disabled`) until this field contains text.
  — Atlas does not pre-populate this field. The user authors it from scratch.

Atlas supporting conclusions:
  — Labeled: "Key conclusions from your analysis" — rendered as a secondary label
  — Two to four Atlas-generated conclusions from the originating Workspace, each presented as a short statement with a source indicator (e.g., "From LVMH Investment Workspace · July 2026")
  — Each conclusion has a small toggle: "Relevant to this decision" (checked by default) / "Not relevant" (allows the user to exclude it from the record without deleting it)

Essential assumptions:
  — Labeled: "Assumptions this decision depends on"
  — Two to three Atlas-proposed assumptions, each as a short statement
  — Each assumption has an "Accept" control (accepted by default) and an "Edit" control
  — The user may add additional assumptions via an "Add assumption" control at the end of the list
  — Empty state: "No assumptions identified. Add one if the decision depends on a specific condition remaining true."

Material risks:
  — Labeled: "Material risks"
  — One to two Atlas-proposed risks, each as a short statement
  — Same Accept / Edit / Add model as assumptions
  — Empty state: "No material risks identified."

Interaction ownership: Primary reason is user-authored, required, unlocked until recording. Supporting conclusions are Atlas-generated, toggleable, locked after recording. Assumptions and risks are Atlas-proposed and user-confirmable, editable, locked after recording.

Collapsed state:
  — Shows the primary reason truncated
  — Does not show conclusions, assumptions, or risks

⸻

Section 5 — Supporting Factors

Position: Below Section 4. Collapsed by default for minor decisions (Maintain, No Action, Defer). Expanded by default for allocation-change decisions.
Width: Full reading width.

Components:

Section header (always visible when section exists):
  — Section label: "SUPPORTING FACTORS"
  — Collapse / expand control
  — Collapsed summary: a single count. "4 supporting factors." If all are from Atlas: "4 Atlas-identified factors."

Expanded state — four groups, each labeled:

Supporting evidence:
  — Two to four items from the originating analysis, each as a one-to-two line statement
  — Source indicator for each item
  — Each item has a "Flag as particularly important" control — flagged items are highlighted in the Final Decision Card

Intact assumptions:
  — Assumptions from the originating analysis that remain unbroken
  — Each shown as: "[Assumption statement] — confirmed intact as of [date]"
  — If no intact assumptions: empty state — "No assumptions confirmed intact. Check originating analysis."

Portfolio alignment:
  — One to three statements about how the decision aligns with the established portfolio strategy, concentration limits, and return objectives
  — Atlas-generated
  — If fully aligned: "This decision is consistent with the portfolio's stated strategy and current concentration limits."
  — If partially aligned: specific statements about the areas of alignment and the areas of tension (tension items appear in Section 6)

Historical consistency:
  — If a prior decision exists on this investment: "Consistent with [date] decision to [prior decision type]" or "Departs from [date] decision to [prior decision type] — see Challenges."
  — If no prior decision: "No prior recorded decision for this investment."

Interaction ownership: All items Atlas-generated. Read-only. The Flag control is user-owned, persists to the Final Decision Card.

Empty states:
  — No supporting evidence: "No supporting evidence identified in the originating analysis. Proceed with caution or return to the analysis."
  — No intact assumptions: stated as above.
  — No portfolio alignment: "This decision has not been evaluated for portfolio alignment. Consider reviewing the Portfolio Workspace."

⸻

Section 6 — Challenges

Position: Below Section 5. Collapsed by default for Maintain and No Action. Expanded by default for any allocation-change, initiation, or exit decision.
Width: Full reading width.

Components:

Section header:
  — Section label: "CHALLENGES"
  — Collapse / expand control
  — Collapsed summary: "[N] unresolved challenges · [M] acknowledged" — this count updates as the user acknowledges items
  — If all challenges are acknowledged: "All challenges acknowledged."

Expanded state:

Challenge items — each rendered as a contained row:
  — Challenge text: one to two sentences, Atlas-generated
  — Challenge type label: one of — UNRESOLVED QUESTION / CONFLICTING EVIDENCE / UNCERTAIN ASSUMPTION / CONTRADICTORY SIGNAL / MISSING INFORMATION
  — Action required indicator: "Requires awareness" (the majority) or "Consider addressing before recording" (for high-severity conflicts)
  — Acknowledgment control: "Acknowledge" button. When tapped, the item's visual prominence reduces and the button changes to "Acknowledged ✓". The item remains visible and in the record — it is not hidden.
  — If a challenge has been acknowledged: the acknowledgment is preserved in the decision record. The user cannot un-acknowledge without creating a version note.

Behavioral context items (when present):
  — Visually distinguished from analytical challenge items — a different section label: "BEHAVIORAL CONTEXT"
  — Shown only when Atlas has identified a specific behavioral signal. Never shown by default.
  — Example: "This decision follows a 12% price decline over 30 days. The core thesis has not changed in the same period. Confirm this is a thesis-driven decision."
  — The user may dismiss a behavioral context item with "This is a thesis-driven decision" — the dismissal and its timestamp are preserved in the record.

Severity escalation:
  — If two or more challenges remain unacknowledged at the time the user attempts to record, a gentle friction prompt appears adjacent to the Record Decision button: "2 challenges have not been acknowledged. Review before recording." This does not disable the button — it adds one deliberate friction step.
  — If one or more challenges is marked "Consider addressing before recording" and remains unacknowledged, the Record Decision button is softly disabled (reduced emphasis only, not fully blocked) with the explanation: "Consider acknowledging the open conflict with prior reasoning."

Interaction ownership: All challenge items Atlas-generated, read-only. Acknowledgment controls are user-owned. Behavioral context dismissal is user-owned. All states preserved in the record.

Empty state: "No conflicts identified for this decision." This should feel intentional — a clean challenge section means the decision is internally consistent.

⸻

Section 7 — Opportunity Cost

Position: Below Section 6. Visible for all decisions involving capital allocation. Hidden for Maintain, No Action, and Scheduled Review decisions with no allocation change.
Width: Full reading width.

This section is one of the defining Atlas experiences. Its components should be read as a comparative reasoning surface, not a table of data.

Components:

Section header:
  — Section label: "OPPORTUNITY COST"
  — Collapse / expand control
  — Collapsed summary: "Why [decision subject] over [primary alternative]."

Expanded state:

Decision subject summary row:
  — Label: "This decision"
  — Name and decision type
  — Atlas conviction or expected return indicator: a short qualitative label — "High conviction · ~11% p.a. expected return" or "Moderate conviction · expected return compressed after recent appreciation"
  — Current allocation (for existing positions) or proposed allocation (for new positions)

Alternative rows (one to three):
  Each alternative row:
  — Alternative name and type (investment, cash, portfolio adjustment)
  — Atlas conviction or expected return indicator, in the same format as the decision subject
  — Relevant portfolio context: current allocation, available capacity, any overlap with existing exposure
  — Comparison line: a one-sentence qualitative comparison with the decision subject. This is the critical element of each row. It must be specific, not generic. Example: "Danaher currently offers a higher expected return at a lower current allocation, with no additional AI theme overlap." Not: "Danaher may be a good alternative."
  — User note field: "Add reasoning →" — an optional inline field for the user to add why this alternative was considered and rejected

Conclusion line:
  — Labeled: "Why this decision"
  — A single statement, Atlas-generated, summarizing why the proposed decision is preferred over the alternatives shown
  — User-editable: the user may overwrite or append to this statement
  — Required for decisions with alternatives: if the conclusion line is empty and alternatives are present, the Record Decision action explanation notes: "State why this decision is preferred over the alternatives."

Interaction ownership: Atlas-generated throughout. User note fields and conclusion line are user-editable. Conclusion line is locked after recording.

Empty state (no alternatives identified): "No competing capital uses have been identified for this decision. If you are aware of alternatives, consider reviewing the Portfolio Workspace before recording." This is shown as a calm informational note, not an error.

⸻

Section 8 — Portfolio Consequences

Position: Below Section 7. Collapsed by default for minor decisions. Expanded by default for decisions with meaningful allocation impact.
Width: Full reading width.

Components:

Section header:
  — Section label: "PORTFOLIO CONSEQUENCES"
  — Collapse / expand control
  — Collapsed summary: the single-line summary from below — "This decision reduces LVMH from 7.1% to 4.0% and releases 3.1% of portfolio capital."

Expanded state:

Consequence rows — each shown only when relevant to this specific decision:

Position size change:
  — "[Investment name]: [before]% → [after]%"
  — For reductions: "Releases approximately [X]% of portfolio capital."
  — For additions: "Increases allocation by approximately [X]%."

Theme exposure change:
  — Shown when the decision materially changes a theme exposure
  — "[Theme name]: [direction] — [brief explanation]"
  — Example: "Enterprise AI dependency: unchanged — LVMH has no AI exposure."

Sector or geographic change:
  — Shown when material
  — Brief before/after statement

Hidden concentration change:
  — Shown when the decision changes an underlying shared dependency
  — "This decision [increases / reduces / does not change] the portfolio's shared enterprise AI dependency."

Risk dependency change:
  — Shown when material
  — "[Dependency name]: exposure [increases / decreases / unchanged]."

Liquidity impact:
  — Shown only when the position is illiquid or the decision has a meaningful liquidity effect

Summary line:
  — Always present at the bottom of the expanded section
  — A single sentence synthesizing the most important portfolio consequence
  — Atlas-generated, read-only

Interaction ownership: Atlas-generated. Read-only.

Empty state (no material consequences): "This decision has no material impact on portfolio allocation, concentration, or risk dependencies." This should feel complete — zero-consequence decisions are valid.

⸻

Section 9 — Assumptions, Monitoring and Invalidation

Position: Below Section 8. Collapsed by default for minor decisions. Expanded by default for allocation-change, initiation, and exit decisions.
Width: Full reading width.

This section contains three distinct, clearly labeled subsections.

Section header:
  — Section label: "ASSUMPTIONS · MONITORING · INVALIDATION"
  — Collapse / expand control
  — Collapsed summary: "[N] assumptions · [M] monitoring conditions · [P] invalidation conditions"

Expanded state — three subsections:

— SUPPORTING ASSUMPTIONS

Each assumption rendered as a row:
  — Assumption statement: a conditional sentence. "GCP margin expansion at scale continues." Not: "GCP margins will expand."
  — Status indicator: Holding / Under Review / Weakening / Broken — four states, Atlas-assessed
  — Supporting reasoning: a short one-line explanation of why Atlas has assessed this status
  — Accept control: default accepted. The user may mark an assumption as "I disagree with this assessment" — this flag is preserved in the record and surfaces in Section 6 as a challenge item.
  — Edit control: allows the user to reword an assumption without changing its status
  — Add control: at the bottom of the list — "Add an assumption"

— MONITORING CONDITIONS

Each condition rendered as a row:
  — Condition statement: a specific observable signal. "LVMH China revenue trend over two consecutive quarters."
  — Why it matters: one line. "This is the primary evidence source for the core luxury demand assumption."
  — Monitoring status: Active / Triggered / Paused — status visible in the record and in Atlas Memory
  — Automatically generates review: a small indicator — "Review triggered if this condition changes" — shown when the condition is linked to an invalidation condition
  — Add control: "Add a monitoring condition"

— INVALIDATION CONDITIONS

Each condition rendered as a row:
  — Condition statement: specific and thesis-grounded. "If LVMH China revenue decline exceeds 20% over two consecutive fiscal years." Not: "If the stock falls 15%."
  — Why this matters: one line explaining the reasoning link. "This would confirm the core thesis assumption is structurally broken rather than cyclically weak."
  — Review trigger: a small indicator — "Triggers Decision Workspace review" — confirming Atlas will surface this decision when the condition is reached
  — Edit control
  — Add control: "Add an invalidation condition"

Interaction ownership: All Atlas-proposed. The user may accept, edit, add, or flag disagreement. After recording: locked. Subsequent changes to monitoring or invalidation conditions create a visible amendment entry in the decision record's version history.

Empty states:
  — No assumptions: "No assumptions identified. Add one if this decision depends on a specific condition remaining true."
  — No monitoring conditions: "No monitoring conditions set. Atlas will not proactively surface this decision for review."
  — No invalidation conditions: "No invalidation conditions set. This decision will only be reviewed when the user initiates a review."

The empty states for monitoring and invalidation conditions are informational warnings, not errors. A Maintain or No Action decision may legitimately have minimal monitoring conditions.

⸻

Section 10 — Implementation Plan

Position: Below Section 9. Expanded for all decision types. Complexity adapts.
Width: Full reading width.

Components:

Section header:
  — Section label: "IMPLEMENTATION PLAN"
  — Not collapsible for decisions involving allocation change
  — Collapsible for No Action and Maintain decisions, with collapsed summary: "No action required."

Implementation type selector:
  — Five options displayed as a compact grouped selector:
    Immediate / Gradual / Conditional / Deferred / No Action
  — Selected by default based on the decision type (Atlas-proposed, user-adjustable)

Conditional fields — each appears only when the relevant implementation type is selected:

Immediate:
  — Target allocation or change, stated as a range: "Reduce to approximately 3–4%"
  — A brief intended timeline: "As soon as practicable" or a specific horizon

Gradual:
  — Target allocation or change
  — Number of portions and approximate timeline: "Three equal portions over 60 days"
  — Note field: optional explanation of the gradual approach

Conditional:
  — Condition that must be met: "If the valuation falls below 20x forward FCF"
  — Action once condition is met: "Initiate a 3–4% position"
  — Expiry: "Review condition if not met within 12 months"

Deferred:
  — Deferral trigger: "Following the next LVMH earnings release"
  — Interim status: "No action until trigger is reached"
  — Optional partial action: "Consider a small initial position while awaiting full evidence"

No Action:
  — A single required acknowledgment: "This is a deliberate decision to take no action." The user must actively confirm this — it cannot be the default for a blank implementation section.

Implementation status field (appears after recording):
  — Separate from the implementation plan itself
  — Updated by the user outside the Decision Workspace, from the decision record
  — States: Pending / In Progress / Completed / Conditional (Awaiting Trigger) / Cancelled
  — Not editable within the Decision Workspace itself

Interaction ownership: Implementation type and all conditional fields are collaborative — Atlas proposes, user confirms and adjusts. All fields locked after recording. Implementation status is user-updated externally.

Validation: an implementation type must be selected before recording. If no type is selected, the completion gate explanation reads: "Select an implementation approach before recording."

⸻

Section 11 — Review Plan

Position: Below Section 10. Expanded for all decision types.
Width: Full reading width.

Components:

Section header:
  — Section label: "REVIEW PLAN"
  — Not collapsible

Review trigger selector:
  — Four trigger types shown as a compact grouped selector:
    Time-Based / Condition-Based / Event-Based / Invalidation-Triggered
  — Atlas proposes a trigger type based on the monitoring conditions in Section 9. User may change.

Trigger detail field (adapts to selected type):

Time-Based:
  — "Review after: [free text — next Q3 earnings, six months, December 2026]"
  — Approximate date field (optional)

Condition-Based:
  — "Review if: [free text — valuation exceeds 35x FCF, revenue growth falls below 8%]"
  — Link to monitoring condition: a small selector — "Linked to: [condition from Section 9]"

Event-Based:
  — "Review following: [free text — next LVMH earnings release, management strategy update]"

Invalidation-Triggered:
  — Read-only: "Atlas will surface this decision for review when any invalidation condition in Section 9 is reached."
  — Shows the linked invalidation conditions as a brief list

Review depth note:
  — A short optional field: "What should the review examine?"
  — Placeholder: "What to look at when this decision comes up for review."
  — Pre-populated by Atlas when a natural review focus is identifiable. User-editable.

Atlas reminder behavior:
  — A small informational note: "Atlas will surface this decision in your Daily Briefing when the review condition is reached."
  — For invalidation-triggered reviews: "Atlas will monitor the conditions you defined and surface this decision when any of them changes."

Interaction ownership: All fields collaborative. Atlas proposes, user confirms. Locked after recording.

Empty state: if no review trigger is set, the footer explanation reads: "Set a review condition before recording." A Review Condition is required unless explicitly overridden with a logged reason (a full, final exit with no remaining stake to monitor) — the override text itself becomes the recorded content. A Maintain decision may use: "Next scheduled portfolio review or earlier if thesis changes." *(Corrected per ADR-002/C-04: this line previously stated Review Conditions are "required for all decision types" with no override path.)*

⸻

Section 12 — Final Decision Card

Position: Below Section 11. Always visible. Never collapsible.
Width: Full reading width.

This is the most prominent section in the lower half of the Workspace. It is a read-back — assembled from the user's inputs above — that converges the entire reasoning sequence into one readable record.

Components:

Section label: "FINAL DECISION CARD"

The summary is rendered as a contained card — visually distinct from the sections above it.

Six labeled fields within the card, each sourced from a specific section:

Decision
— Source: Section 3, user decision field
— Updates in real time as the user edits Section 3

Reason
— Source: Section 4, primary reason field
— Updates in real time as the user edits Section 4

Confidence
— Source: Section 4, derived from the state of the Assumptions section
— Five states: High Confidence / Moderate Confidence / Low Confidence / Evidence Incomplete / Intentionally Deferred
— User may override the Atlas-assessed confidence level

Portfolio impact
— Source: Section 8, summary line
— One sentence, Atlas-generated

Implementation
— Source: Section 10, implementation type and key detail
— Example: "Gradual reduction — three portions over 60 days · Target 3–4%"

Review condition
— Source: Section 11, trigger and detail
— Example: "Review after Q3 earnings · Confirm China revenue trend"

Live update behavior:
— All six fields update in real time as the user edits the corresponding sections above
— If a required field is empty, the card shows a placeholder: "Awaiting your decision." / "Awaiting your primary reason." etc.
— The user can see exactly what will be recorded before committing

Flagged items:
— If the user flagged items as "particularly important" in Section 5, a seventh field appears in the card: "Key supporting factors" — listing the flagged items as a brief compact list

Interaction ownership: Atlas-assembled from user inputs. Read-only. All fields lock after recording.

After recording: this card becomes the permanent decision record shown in Atlas Memory, in Investment Workspace reviews, in Portfolio Workspace reviews, and in the Daily Briefing.

⸻

Section 13 — Record Decision

Position: Bottom of the scrolling body. The primary action is also in the fixed footer.
Width: Full reading width.

The Record Decision section in the body provides the final context statement before the primary action. The primary action itself lives in the footer.

Body content (immediately above the footer):
— "Recording this decision will preserve it in Atlas Memory, link it to your [originating Workspace], and begin monitoring the conditions you defined."
— This is shown as a single calm statement — not a warning, not a checklist.
— If any challenges remain unacknowledged: "[N] challenges have not been acknowledged." shown as a secondary note, not an error.

Primary action — Record Decision:
Available state:
— Full emphasis
— Label: "Record Decision"
— Selecting this action triggers the recording behavior described in UX-009

Unavailable state: *(Corrected per ADR-002/C-06: this state was previously named "Disabled" without qualification. It carries `aria-disabled="true"` — never the native HTML `disabled` attribute — and remains focusable and in the natural tab order.)*
— Reduced emphasis, cursor: not-allowed (visual treatment unchanged)
— Label: "Record Decision" — label unchanged
— Adjacent explanation, also exposed via `aria-describedby`: a single sentence naming the specific incomplete element. Examples:
  "State your decision before recording."
  "Add a primary reason before recording."
  "Select an implementation approach before recording."
  "Set a review condition before recording."
— The explanation updates as requirements are met. When all requirements are met, it disappears and the button becomes available. Activating the action while unavailable does not record the decision — it moves focus to the first unmet required field and re-announces the explanation there.

Secondary actions (always available):
— Save as Draft: saves the current state to Atlas as an in-progress decision. Available at any time. Drafts appear in the Daily Briefing as unresolved.
— Return to Workspace: closes the Decision Workspace and returns to the originating Workspace. If an unsaved draft exists, prompts: "Exit without saving? Your progress will be lost." Two options: "Save draft and exit" / "Exit without saving."

Completion behavior — after selecting Record Decision:
— A brief transition to the post-decision state
— The scrolling body shows: the Final Decision Card (full reading width, elevated visual prominence) surrounded by clear space
— Below the card: a single calm confirmation line — "Decision recorded · [date] · [investment name or portfolio scope]"
— Below the confirmation: three contextual next steps (rendered as clearly labeled links, not buttons):
  "Return to [originating Workspace name]" — the most prominent of the three
  "View decision in Atlas Memory"
  "[Next step]" — present when a clear next step exists, e.g., "Open Danaher Workspace to begin capital comparison"

The footer in the post-decision state:
— The Record Decision button is replaced with "Close Workspace"
— Save as Draft and Return to Workspace are removed

⸻

Editing Model

Every field in the Decision Workspace has a defined ownership classification.

Atlas Generated — Read-Only:
Produced entirely by Atlas from originating analysis. The user cannot edit these fields within the Decision Workspace. Returning to the originating Workspace is the path for changing the underlying conclusions.
— Current Conclusion (Section 1)
— Trigger label and elaboration (Section 2)
— Atlas proposal text (Section 3)
— Supporting conclusions (Section 4)
— All items in Section 5 (Supporting Factors)
— Challenge items (Section 6)
— Behavioral context items (Section 6)
— Alternative comparisons (Section 7)
— Portfolio consequence rows (Section 8)
— Implementation type proposal (Section 10)

Atlas Suggested — User Confirmable and Editable:
Atlas proposes content; the user may accept, edit, or add. These fields appear pre-populated and editable.
— Assumptions (Section 4 and Section 9)
— Material risks (Section 4)
— Monitoring conditions (Section 9)
— Invalidation conditions (Section 9)
— Review trigger and detail (Section 11)
— Confidence level (Section 12)
— Opportunity cost conclusion line (Section 7)
— Decision type selection (Section 3)

User Owned — Authored by the User:
These fields are not pre-populated by Atlas. They are blank until the user writes in them.
— Primary reason (Section 4)
— User decision field (Section 3)
— User note in Section 2
— User notes on alternatives in Section 7

Locked After Recording:
All fields — Atlas-generated and user-authored — lock after Record Decision is selected. The fields are readable but not editable in the recorded state.

Versioned After Post-Recording Changes:
Any changes to monitoring conditions or invalidation conditions after recording create a visible amendment entry in the version history. The original content is preserved. The amendment shows: changed field, original content, new content, timestamp.

History Preserved:
The modification indicator on the user decision field (whether the user changed Atlas's proposal) is preserved permanently in the record. The original Atlas proposal is stored alongside the user's final decision.

⸻

Adaptive Behaviour

The following defines which sections are expanded, collapsed, or hidden for each decision type. The thirteen-section structure is constant. Only the depth varies.

Maintain:
Expanded: 1, 2, 3, 10, 11, 12, 13
Collapsed: 4 (shows brief reason only), 9 (one assumption, one review trigger only)
Hidden: 7 (Opportunity Cost)
Section 5 and 6 present but collapsed. Section 8 collapsed.
Expected duration: under three minutes.

Add (minor — under 2% change):
Expanded: 1, 2, 3, 4, 6, 10, 11, 12, 13
Collapsed: 5, 8, 9
Section 7: brief — one alternative row only.
Expected duration: four to eight minutes.

Add (major — over 2% change) / Initiate:
All sections expanded.
Section 7: two to three alternatives.
Expected duration: ten to fifteen minutes.

Reduce (minor):
Expanded: 1, 2, 3, 4, 6, 7, 10, 11, 12, 13
Collapsed: 5, 8, 9
Expected duration: four to eight minutes.

Reduce (major) / Exit:
All sections expanded.
Section 6 given additional prominence: "This decision reduces or exits a position. Confirm the thesis has changed or the opportunity cost is clearly superior."
Section 9: full depth — all three subsections.
For Exit only: Section 9 includes an additional field: "What would cause you to consider re-entering this investment?"
Expected duration: twelve to twenty minutes.

Avoid / Reject:
Expanded: 1, 2, 3, 4, 7, 9 (assumptions only), 11, 12, 13
Collapsed: 5, 6, 8
Section 7: shows why the investment was evaluated and why it was rejected — one to two alternatives to the investment (including "deploy capital elsewhere" or "hold cash")
Expected duration: five to eight minutes.

Portfolio Reallocation:
Sections 1 and 2 draw from the Portfolio Workspace rather than an Investment Workspace.
Section 8 — Portfolio Consequences — becomes the primary analytical section and is rendered at full expanded depth.
Section 7 shows capital competition across multiple positions.
All other sections at standard depth.
Expected duration: fifteen to thirty minutes.

Defer:
Expanded: 1, 2, 3, 10 (Deferred type), 11, 12, 13
Collapsed: 4 (reason required but brief acceptable), 9 (monitoring conditions only — no invalidation)
Hidden: 5, 6, 7, 8
Section 12 reflects the deferral explicitly: "Deferred — [deferral trigger]"
Expected duration: under five minutes.

No Action:
Expanded: 1, 2, 3, 10 (No Action type, requires deliberate acknowledgment), 11, 12, 13
Collapsed: 4 (reason required — even "no material change" is a valid reason), 9
Hidden: 7, 8
Sections 5 and 6 collapsed.
Expected duration: under three minutes.

⸻

Validation Rules

*(Corrected per ADR-002/C-04: this section previously listed a flat four-field "Required" rule — user decision field, primary reason field, implementation type, review trigger — applied identically regardless of decision type. The corrected model below distinguishes the universal minimum from decision-type-conditional requirements.)*

The following must be complete before Record Decision is available:

Universal minimum, required for every decision type, no exceptions:
1. Section 3 — user decision field: must contain text
2. Section 4 — primary reason field: must contain text

Conditionally required, by decision type:
3. Section 10 — implementation type: must be selected for decisions that entail an action; selecting "No Action" or "Deferred" itself satisfies this requirement for decisions where no action is entailed
4. Section 11 — review trigger: must be set, unless explicitly overridden with a logged reason (a full, final exit with no remaining stake to monitor)
5. Section 8 — Portfolio Consequences acknowledgment: required for portfolio-level decisions; not required for single-position decisions

Soft friction (reduces emphasis, adds explanation, does not fully block — never a hard block regardless of severity):
— One or more "Consider addressing before recording" challenges in Section 6 remain unacknowledged
— Two or more total challenges remain unacknowledged

Does not block recording:
— Any Atlas-suggested fields left at default (assumptions, monitoring conditions, etc.)
— User note fields left empty
— Flagging controls unused
— Supporting conclusions all left at default

The Record Decision explanation text updates dynamically as requirements are met. When the last requirement is satisfied, the text disappears and the button reaches full availability.

A Deferred decision satisfies all requirements with a brief primary reason ("Insufficient evidence to decide now") and a deferral trigger. Deferral is a first-class outcome, not a workaround.

⸻

Navigation

Entering the Decision Workspace:
The overlay animates in from below, consistent with the Investment Case overlay behavior. The originating Workspace is dimmed but spatially present.

Moving through sections:
Continuous vertical scroll. No pagination, no step controls, no next/previous navigation. The user scrolls freely in both directions at any point.

Returning to originating Workspace:
The "Return to [Workspace name]" control in the header dismisses the overlay and restores the originating Workspace to its exact scroll position and expanded section state. No context is lost.

"View full analysis" link (Section 1):
Opens the originating analysis as a secondary context surface — a slide-in panel or nested overlay — without losing the Decision Workspace state. Closing the analysis panel returns the user to the same scroll position in the Decision Workspace.

Draft restoration:
When the user re-enters the Decision Workspace for the same decision subject after saving a draft, the draft state is fully restored — all fields, all selections, all scroll position.

History access:
A "View prior decisions →" control is accessible from the header (secondary, low-emphasis). Opens the Atlas Memory record for this investment or portfolio scope — prior recorded decisions shown in chronological order. Read-only. Closing returns to the Decision Workspace.

Escape key:
Dismisses the overlay. If an unsaved draft exists, prompts once: "Save draft and exit / Exit without saving." If no draft exists, dismisses immediately.

⸻

Versioning

When a user revisits a recorded decision, they enter the Decision Workspace in Review Mode.

Review Mode layout:
— The recorded decision appears in a left panel or collapsed header region: the Final Decision Card from the original decision, with its date and recorded state
— The current analysis appears in the right panel or main body in the same thirteen-section structure, but populated with current data
— The user can scroll both panels or collapse the original to focus on current conditions
— Section 6 (Challenges) in Review Mode includes a comparison: "How has this changed since the original decision?"

Version types — when the user records in Review Mode, they select one of:

New Review:
The original decision remains unchanged. A new review record is created: current analysis, new Section 12 summary, outcome assessment (was the thesis still intact? did the invalidation conditions hold?). The review links to the original decision.

Revision:
The original decision is amended. The specific fields changed, their original values, and a reason for the change are preserved in the version history. The revised decision replaces the original in active use but the original remains accessible.

Superseding Decision:
A new full decision is recorded that explicitly replaces the prior decision. The prior decision's status changes to "Superseded." Both records are preserved in Atlas Memory.

Implementation Update:
The implementation status field is updated (Pending → In Progress → Completed). Does not require re-entering the full Decision Workspace. Available from the decision record in Atlas Memory.

Review Completion:
The review is closed with a summary outcome and the review trigger is updated to the next cycle. Available as a streamlined action from the review surface.

In all cases: the original reasoning is never silently overwritten. Every change creates a visible entry in the version history with a timestamp and the nature of the change.

⸻

Empty States

No conflicting evidence (Section 6):
"No conflicts identified for this decision."
Presented as a single calm statement occupying the section content area. Not greyed out, not marked as incomplete. A clean challenge section means the decision is internally consistent. This is a positive state.

No opportunity cost identified (Section 7):
"No competing capital uses have been identified. If you are aware of alternatives, consider reviewing the Portfolio Workspace before recording."
Shown as an informational note. The section remains present but minimal. The Record Decision action is not blocked by an empty opportunity cost section — for small or maintenance decisions, no alternatives may genuinely exist.

No monitoring conditions (Section 9):
"No monitoring conditions set. Atlas will not proactively surface this decision for review."
This is a warning, not an error. The user is informed that Atlas will not be watching unless conditions are defined. Recordable.

No implementation required (Section 10):
For No Action decisions: the section shows the deliberate acknowledgment — "This is a deliberate decision to take no action" — once confirmed. No further fields appear.

No review scheduled (Section 11):
The Record Decision completion gate requires a review trigger unless explicitly overridden with a logged reason. If no trigger is set and no override has been given, the gate explanation reads: "Set a review condition before recording." *(Corrected per ADR-002/C-04: this line previously stated the review-trigger requirement had no override path.)*

⸻

Error Prevention

Atlas surfaces the following concerns without blocking thoughtful decisions unnecessarily.

Decision contradicts earlier reasoning:
Appears in Section 6 as a challenge item: "This decision departs from your [date] decision to [prior decision]. Prior reasoning: [one-sentence summary]."
Interaction: the user acknowledges or adds a note explaining the change. Not blocked.

Decision increases hidden concentration:
Appears in Section 8 and in Section 6 as a challenge: "This decision increases the portfolio's enterprise AI dependency from approximately 42% to 48% of underlying exposure."
Interaction: acknowledged. Not blocked.

Implementation conflicts with portfolio strategy:
Appears in Section 6 as a challenge: "This implementation would bring the position above the portfolio's stated concentration limit of 10%."
Interaction: acknowledged. Not blocked.

Primary reason field left empty:
The Record Decision action remains unavailable (`aria-disabled`) with the explanation: "Add a primary reason before recording." No inline error shown on the field itself — the explanation in the footer is sufficient.

Critical assumption unresolved:
If an assumption in Section 9 has status "Broken" and has not been acknowledged, a soft friction item appears in Section 6: "A supporting assumption for this decision has been classified as Broken." The user acknowledges. Not blocked.

Behavioral context (price-reaction decision):
Appears in Section 6 as a behavioral context item: specific, calm, non-judgmental. The user dismisses with "This is a thesis-driven decision." The dismissal is recorded. Not blocked.

The general principle: Atlas explains the concern clearly and then permits the user to proceed. Blocking is reserved for genuinely incomplete records (missing required fields), not for disagreements about judgment.

⸻

Completion Experience

After selecting Record Decision, the Workspace transitions to the post-decision state.

The scrolling body clears all sections. The Final Decision Card is displayed centered in the body, at full reading width, with generous space above and below it. The card is in its completed form — all six fields populated with the recorded values.

Immediately below the card, a single line:
"Decision recorded · [date] · [investment name or portfolio scope]"

This line is the entirety of the completion messaging. No celebratory language. No summary of what Atlas learned. No call to action about market timing. The meaning is in the record, not the confirmation.

Below the confirmation line, three contextual next steps — rendered as plain labeled links, left-aligned, in order of natural flow:
1. Return to [originating Workspace name]
2. View decision in Atlas Memory
3. [Next step, when relevant] — "Open Danaher Workspace to begin capital comparison" or "Return to Portfolio Workspace to complete the pending review"

The fixed footer changes: Record Decision is replaced with "Close Workspace." Save as Draft and Return to Workspace are removed.

The header remains, with the same decision subject and type, and the same close control.

The user should feel, at this moment, that they have preserved exactly what they decided, why they decided it, what they are watching, and that the record will be understandable to their future self.

⸻

Final Wireframe Hierarchy

Fixed Header
— Decision subject label (investment name or "Portfolio")
— Decision type label
— Atlas badge
— Return to [Workspace name] control
— Close control

Scrolling Body — maximum reading width, centered

[1] CURRENT CONCLUSION
  — Section label
  — Conclusion card
    — Source reference + date
    — Conclusion statement (primary text)
    — Confidence indicator label
  — "View full analysis →" link

[2] WHY A DECISION IS REQUIRED
  — Section label
  — Primary trigger block
    — Trigger label
    — Trigger elaboration
  — Supporting triggers (when present)
  — User note field (optional)

[3] PROPOSED DECISION
  — Section label
  — Atlas proposal block
    — "Atlas suggests" label
    — Proposed decision text
    — Suggested decision type
  — User decision field (primary text area)
  — Decision type selector (grouped)
  — Modification indicator (when user has changed from proposal)

[4] DECISION RATIONALE
  — Section header + collapse control
  — Collapsed summary: primary reason excerpt
  — [Expanded]
    — Primary reason field (user-authored text area)
    — Atlas supporting conclusions (labeled, toggleable)
    — Essential assumptions (Atlas-proposed, Accept / Edit)
    — Material risks (Atlas-proposed, Accept / Edit)
    — "Add assumption" / "Add risk" controls

[5] SUPPORTING FACTORS
  — Section header + collapse control
  — Collapsed summary: item count
  — [Expanded]
    — Supporting evidence items (with Flag control)
    — Intact assumptions
    — Portfolio alignment statements
    — Historical consistency statement

[6] CHALLENGES
  — Section header + collapse control
  — Collapsed summary: challenge count + acknowledged count
  — [Expanded]
    — Challenge items (challenge text + type label + action indicator + Acknowledge control)
    — Behavioral context items (when present, with dismiss control)

[7] OPPORTUNITY COST
  — Section header + collapse control
  — Collapsed summary: "Why [subject] over [primary alternative]"
  — [Expanded]
    — Decision subject summary row
    — Alternative rows (with user note field per row)
    — Conclusion line (Atlas-generated, user-editable)

[8] PORTFOLIO CONSEQUENCES
  — Section header + collapse control
  — Collapsed summary: summary line
  — [Expanded]
    — Consequence rows (relevant only)
    — Summary line

[9] ASSUMPTIONS · MONITORING · INVALIDATION
  — Section header + collapse control
  — Collapsed summary: counts
  — [Expanded]
    — SUPPORTING ASSUMPTIONS subsection
      — Assumption rows (statement + status + reasoning + Accept / Edit / Flag)
      — "Add assumption" control
    — MONITORING CONDITIONS subsection
      — Condition rows (statement + why + monitoring status + review trigger indicator)
      — "Add condition" control
    — INVALIDATION CONDITIONS subsection
      — Condition rows (statement + reasoning + review trigger indicator + Edit)
      — "Add invalidation condition" control
      — [Exit decisions only] "Re-entry consideration" field

[10] IMPLEMENTATION PLAN
  — Section label
  — Implementation type selector (Immediate / Gradual / Conditional / Deferred / No Action)
  — Conditional detail fields (adapts to selected type)

[11] REVIEW PLAN
  — Section label
  — Review trigger selector (Time-Based / Condition-Based / Event-Based / Invalidation-Triggered)
  — Trigger detail field (adapts to selected type)
  — Review depth note field
  — Atlas reminder behavior note

[12] FINAL DECISION CARD
  — Section label
  — Summary card (live-updating)
    — Decision
    — Reason
    — Confidence
    — Portfolio impact
    — Implementation
    — Review condition
    — Key supporting factors (when flagged items exist)

[13] RECORD DECISION — body area
  — Context statement
  — Unacknowledged challenge note (when present)

Fixed Footer
  — Save as Draft (secondary)
  — Return to Workspace (secondary)
  — Record Decision (primary — available or unavailable via `aria-disabled="true"`, never native `disabled`, remaining focusable; unavailable activation navigates to the first unmet required field)

Post-Decision State (replaces body after recording)
  — Final Decision Card (full emphasis)
  — Confirmation line
  — Three contextual next steps

Fixed Footer (post-decision)
  — Close Workspace

⸻

What UX-009A Establishes

The following component-level decisions are now fixed:

— Layout: fixed header, scrolling body at maximum reading width, fixed footer. The overlay sits above the originating Workspace, which remains visible and restorable.

— Fixed Header components: decision subject, decision type label, Atlas badge, "Return to [Workspace name]" control, close control.

— Fixed Footer components: primary Record Decision action (available, or unavailable via `aria-disabled="true"` with named explanation — never native `disabled`, remains focusable), Save as Draft, Return to Workspace. Post-decision: Close Workspace only.

— Section 1 — Current Conclusion: conclusion card with source reference, conclusion statement, confidence indicator, and "View full analysis →" link. Atlas-generated, read-only.

— Section 2 — Why a Decision Is Required: primary trigger block (trigger label + elaboration), supporting triggers, optional user note. Atlas-generated with optional user note.

— Section 3 — Proposed Decision: Atlas proposal block (clearly labeled), user decision text area (primary interactive element), decision type grouped selector, modification indicator. The distinction between Atlas's proposal and the user's decision is structurally enforced.

— Section 4 — Decision Rationale: primary reason text area (user-authored, required), Atlas supporting conclusions (toggleable), assumptions (Atlas-proposed, Accept/Edit), risks (Atlas-proposed, Accept/Edit).

— Section 5 — Supporting Factors: four groups — evidence, intact assumptions, portfolio alignment, historical consistency. Flag control on evidence items. Atlas-generated.

— Section 6 — Challenges: challenge rows with type labels, action indicators, and Acknowledge controls (preserved in record, not deletable). Behavioral context items separately labeled with dismiss control. Unacknowledged challenges create soft friction at the footer.

— Section 7 — Opportunity Cost: decision subject summary row, alternative rows (with user note fields per row), Atlas-generated comparison lines, user-editable conclusion line. Required for allocation decisions; hidden for No Action and Maintain.

— Section 8 — Portfolio Consequences: relevant consequence rows only, summary line. Atlas-generated, read-only.

— Section 9 — Assumptions, Monitoring and Invalidation: three distinct subsections, each with individual rows, status indicators, Accept/Edit/Add controls. Assumptions carry status (Holding / Under Review / Weakening / Broken). Monitoring conditions carry active/triggered/paused state. Invalidation conditions link to future review triggers. Exit decisions include a re-entry consideration field.

— Section 10 — Implementation Plan: five-type selector, conditional detail fields per type. No Action requires deliberate acknowledgment. Implementation status tracked externally after recording.

— Section 11 — Review Plan (the section): four-type trigger selector, conditional detail fields, review depth note, Atlas reminder behavior note. The Review Condition it produces (the completion-gate content) is required only where the decision-type matrix requires it, and an explicit logged override may stand in place of it.

— Section 12 — Final Decision Card: live-updating summary card assembled from user inputs across six fields (Decision, Reason, Confidence, Portfolio impact, Implementation, Review condition). Becomes the permanent Atlas Memory record.

— Section 13 — Record Decision: context statement, challenge count note, primary action available or unavailable via `aria-disabled="true"` (never native `disabled`, remains focusable; unavailable activation navigates to the first unmet required field) with named explanation per incomplete requirement.

— Editing model: four ownership classifications (Atlas Generated, Atlas Suggested, User Owned, Collaborative) with consistent application across all fields. All fields lock after recording. Post-recording amendments create version history entries.

— Adaptive depth: nine decision types with defined expansion patterns (Maintain, Add minor, Add major / Initiate, Reduce minor, Reduce major / Exit, Avoid / Reject, Portfolio Reallocation, Defer, No Action).

— Validation rules: universal minimum before recording is decision text and primary reason; implementation type, review trigger, and Portfolio Consequences acknowledgment are conditionally required by decision type. Soft friction, never a hard block, for unacknowledged challenges. All other fields optional. *(Corrected per ADR-002/C-04; this line previously stated a flat four-field rule with no decision-type conditionality.)*

— Navigation: continuous scroll, context-preserving overlay, "View full analysis" as nested context, draft restoration, history access from header, escape-key behavior.

— Versioning: five post-recording change types (New Review, Revision, Superseding Decision, Implementation Update, Review Completion). Original reasoning always preserved.

— Empty states: defined for all six possible empty conditions, with intentional rather than error-suggesting presentation.

— Error prevention: six identified concern types, each surfaced through Section 6 as challenge items or footer friction. None block recording except genuinely incomplete required fields.

— Completion experience: Final Decision Card displayed at full emphasis, single confirmation line, three contextual next steps. No celebratory language.

⸻

What Should Be Deferred to UX-010

The following are intentionally deferred to the visual design specification:

— Visual design: all color decisions, elevation, surface treatment, shadow, and depth
— Typography: font families, weights, sizes, line heights, and letter spacing for every text element
— Spacing: all padding, margin, gap, and section separation values
— Component sizing: exact dimensions of the user decision field, summary card, footer, header, and all other elements
— Icons: any iconographic treatment of controls, indicators, status states, and trigger types
— Animations: all transition and motion behavior — overlay entry, section collapse/expand, post-decision transition
— Hover states: visual behavior of all interactive elements on hover
— Focus states: keyboard focus ring treatment and tab order
— Microinteractions: real-time Summary card update behavior, Acknowledge control animation, modification indicator appearance
— Visual distinction between Atlas-generated and user-authored content: the exact visual language (border style, background treatment, label form) that communicates content ownership
— Mobile and tablet layout: responsive breakpoints and layout adaptations
— The visual form of the disabled Record Decision state beyond "reduced emphasis"
— The visual treatment of the behavioral context items as distinct from analytical challenge items
— The visual form of the post-decision confirmation state

Do not produce UX-010 yet.

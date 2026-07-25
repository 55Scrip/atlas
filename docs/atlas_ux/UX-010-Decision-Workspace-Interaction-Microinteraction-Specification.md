UX-010 — Decision Workspace Interaction & Microinteraction Specification

Status: Interaction Specification Complete
Owner: Atlas Product
Governs: Decision Workspace — all behavioral and interaction patterns, microinteractions, editing model, AI collaboration, accessibility
Depends on: UX-008 — Decision Workspace Philosophy, UX-009 — Screen Specification, UX-009A — Wireframe Specification
Defers to: UX-011 — Decision Workspace Visual Design & Polish Specification

**Correction Notice (Phase 2, governed by ADR-002 — 2026-07-24):** This document's original identity (Status, Owner, Governs, Depends on, Defers to, as above) and original date are preserved unchanged. Two semantic areas were corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan, Phase 2:
- **C-04 (Record Decision Completion Gate):** the completion-progression and "What UX-010 Establishes" summary lines were corrected from a flat "four required fields" restatement to the universal minimum plus decision-type-conditional requirements, with unacknowledged Challenges never affecting availability.
- **C-06 (Unavailable Primary Action Accessibility):** the touch-deliberateness, screen-reader-announcement, and error-announcement passages were corrected to specify `aria-disabled="true"` (never native `disabled`), and to state explicitly that the control remains tappable and focusable while unavailable.

This notice does not claim any of the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, at each corrected passage. All content outside these two areas is unchanged. Section naming (Section 5, 6, 12 references) already matched the canonical "Supporting Factors," "Challenges," and "Final Decision Card" names used by the corrected UX-012 and its own C-03-corrected sibling documents, except for "Final Decision Summary," which this correction also updated to "Final Decision Card" for consistency.

**Correction Notice (Phase 2B, governed by ADR-002 — 2026-07-25):** This is a later, additive correction, discovered after the Phase 2 correction above had already closed; it does not revise, replace, or reopen that notice, which remains historically accurate for the two areas it corrected. One further semantic area was corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md`'s C-02 finding and its 2026-07-25 "Addendum — C-02 Mixed-Origin Single-Field Content," as authorized by the Atlas UX Source Correction Plan, Phase 2B:
- **C-02 (AI Authorship and Provenance):** the Atlas Suggestion Model's Accept behavior (Section 4) previously stated that accepting an Atlas suggestion — whether the suggestion replaced the field's content or was appended to the user's own pre-existing text — produced a "modification indicator" reading "Modified with Atlas suggestion" immediately on Accept, conflating acceptance with genuine editing and, in the append case, with mixed-origin authorship. This was corrected so that Accept alone, by either mechanism, never constitutes genuine editing: when the suggestion replaces the field's content, the result reads "Atlas Suggested / User Accepted"; when it is appended to pre-existing user-authored content, the field's authorship becomes field-level `mixed`, displayed as "User Authored / Atlas Suggestion Accepted." In both cases, "user-modified-from-atlas" is reached only after a genuine, subsequent edit — the same model already corrected in UX-012B and UX-012C for this identical feature.

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, above. The three other "modification indicator" occurrences in this document (the restore-to-original passage in Section 5, the Opportunity Cost conclusion-overwrite passage in Section 8, and the color-treatment reference in Requirements for UX-011) were reviewed as part of this same correction and confirmed to already describe genuine subsequent editing, not Accept alone — they are unaffected and unchanged. All content outside this one area is unchanged.

⸻

Governing Intent

Every interaction in the Decision Workspace must answer one question before it is included:

Does this help the user think more clearly?

If not, remove it.

The user must never feel they are filling out a form. They must feel they are gradually arriving at a better decision. Atlas is a reasoning partner — calm, patient, and precise. It surfaces what matters, withholds what doesn't, and never mistakes activity for progress.

⸻

1. Interaction Philosophy

The Decision Workspace is optimized for decision quality, not decision speed. Every interaction pattern reflects this.

Atlas's behavioral stance:
— Encourage thinking by surfacing relevant context at the right moment, not all at once
— Reduce unnecessary typing by pre-populating Atlas-generated content that the user confirms or modifies rather than authors from scratch
— Progressively clarify reasoning by expanding complexity only when the decision or evidence warrants it
— Surface contradictions naturally, as part of the flow, without interrupting the user's reasoning thread
— Preserve user ownership at every step — no interaction implies that Atlas made the decision
— Make complexity appear manageable by collapsing depth that is not yet needed and expanding it when it becomes relevant
— Slow impulsive decisions without bureaucracy — friction arises from the substance of the decision, not from mandatory fields or confirmation dialogs

Atlas is never passive. It actively reads what the user is building and adjusts its behavior. But it is also never controlling. It proposes, surfaces, and suggests. The user accepts, modifies, or disregards.

The interaction model has three behavioral modes:

Ambient — Atlas is quietly present, saving state, observing what is being built, ready to respond
Responsive — Atlas reacts to what the user is doing: expanding a section because the evidence warrants it, surfacing a suggestion because a field is weak, flagging a contradiction because one has appeared
Collaborative — the user explicitly invites Atlas into the reasoning: asking for suggestions, requesting challenges to their own reasoning, comparing with prior decisions

The transition between these modes should be imperceptible. The Workspace should simply feel intelligent.

⸻

2. Reading and Scroll Behavior

The Workspace reads as a document, not software. Scroll behavior reinforces this.

Scroll pause points:
The four high-emphasis moments from UX-009A create natural reading pauses. When the user scrolls to one of these points, the scroll velocity decelerates slightly — not a hard snap, but a gentle deceleration that invites the user to stop and read before continuing:

— Section 1: Current Conclusion
— Section 3: Proposed Decision (specifically the user decision field)
— Section 7: Opportunity Cost conclusion line
— Section 12: Final Decision Card

The deceleration is subtle — it should feel like gravity, not a lock. The user can scroll through without stopping if they choose.

Smooth scroll throughout. No abrupt jumps. When the Workspace auto-scrolls in response to an action (such as expanding a section that was just collapsed, or navigating to a required field when the Record Decision button is tapped while incomplete), the scroll is animated — the user can follow where they are going.

When the Record Decision footer button is tapped while requirements are unmet, the Workspace scrolls to the first incomplete required field and gently highlights it. It does not jump — it travels. The first incomplete field receives focus.

⸻

3. Progressive Disclosure

Sections expand and collapse based on decision significance, not user choice alone. Atlas determines initial expansion state at entry and updates it in response to signals it detects.

Automatic expansion triggers — Atlas expands a section without user action when:

A material contradiction is detected:
Section 6 (Challenges) expands automatically. A brief ambient note appears at the top of the section: "Atlas has identified a conflict with prior reasoning." The section does not flash or animate aggressively — it opens, and the relevant challenge item is briefly highlighted.

Confidence is assessed as low:
Section 6 expands. The uncertainty items are presented first. Section 9 (Assumptions, Monitoring and Invalidation) expands to the Assumptions subsection.

Portfolio impact is significant (position change exceeds 2% of portfolio or a shared dependency materially changes):
Section 8 (Portfolio Consequences) expands. The summary line is shown at the top of the section before the user scrolls to it.

A prior decision exists on the same investment with an opposing decision type:
Section 5 (Supporting Factors) — historical consistency row — is expanded and the conflict is presented with a link to the prior decision.

The implementation type is set to "Conditional" or "Deferred":
Section 9 (Monitoring Conditions subsection) expands automatically, because deferred and conditional decisions require monitoring conditions to be meaningful.

The user sets an invalidation condition that references a price threshold rather than a thesis condition:
Section 9 (Invalidation subsection) presents an Atlas suggestion: "This condition references price movement. Consider whether a thesis-related condition would be more durable." (See Section 14, Invalidation Behavior, for the full suggestion model.)

Automatic collapse triggers — Atlas collapses a section when:

The decision type is changed to Maintain or No Action: Sections 7 (Opportunity Cost) and 8 (Portfolio Consequences) collapse. The collapse is animated. A brief ambient note appears: "Opportunity Cost and Portfolio Consequences are not shown for maintenance decisions. Expand if needed."

All challenge items in Section 6 are acknowledged: the section collapses to its summary state ("All challenges acknowledged") after a brief pause. It does not collapse immediately — it waits approximately two seconds, allowing the user to see their progress.

The decision type is changed to Defer: Sections 5, 6, 7, and 8 collapse. Sections 9 and 10 adapt to the deferred format.

User-controlled collapse:
The user may collapse or expand any collapsible section at any time. User-initiated collapse overrides Atlas's expansion logic for that section during the current session. If the user collapses Section 6 after Atlas expanded it due to a contradiction, the section stays collapsed unless a new, more severe contradiction appears.

⸻

4. Atlas Suggestion Model

Atlas suggestions appear when the user's input could be more precise, complete, or consistent — not simply because a field exists and is brief.

When Atlas generates a suggestion:

A small inline affordance appears adjacent to the relevant field: a subtle indicator that Atlas has something to offer. It does not interrupt the user's typing. It appears when the user pauses (approximately 1.5 seconds of inactivity after completing a thought — not mid-keystroke).

The suggestion is presented as an offer, not an instruction:

— "Would you like to make this more specific? →"
— "This condition may be difficult to monitor. Suggest a more observable alternative?"
— "This assumption overlaps with one you've marked as uncertain. Consider linking them."
— "This reasoning mirrors your [date] decision on [investment]. Consider noting the connection."

The user may:
— Accept: Atlas text replaces the user's text, or is appended to it. When it replaces, the field transitions to Accepted state ("Atlas Suggested / User Accepted") — Atlas remains the recorded author of the accepted text; accepting it is not itself an edit. When it is appended to pre-existing user-authored text, the field becomes field-level mixed ("User Authored / Atlas Suggestion Accepted") — both origins remain legible at the field level, with no fragment-level attribution. In either case, the attribution indicator reflects the resulting state, and "user-modified-from-atlas" is reached only after a genuine, subsequent edit. Undo is immediately available.
— Dismiss: the suggestion disappears. It does not reappear for the same field unless the content changes materially.
— Engage: the user selects "Show reasoning →" and Atlas explains why it made the suggestion in one or two sentences. The user can then accept, dismiss, or modify.

Atlas never suggests in a tone that implies the user is wrong. The framing is always additive: "Here is a way to make this more durable" rather than "This is incorrect."

Suggestions Atlas generates across specific fields:

Section 3 — User Decision Field:
If the decision text is vague (fewer than eight words, or contains language like "maybe" or "consider"):
"This decision could be more specific. Would you like to sharpen the wording?"
Atlas offers one or two alternative phrasings. The user may adopt one, reject all, or use them as a starting point.

Section 4 — Primary Reason Field:
If the reason references price movement without a thesis change:
"This reason references price movement. Would you like to add a thesis-based reason?"
If the reason is very brief and the decision is a major allocation change:
"This is a significant decision. Consider expanding the reasoning to capture what changed."

Section 9 — Invalidation Conditions:
If a condition references a price percentage:
"Invalidation conditions tied to price movement can trigger reviews during normal volatility. Consider whether a thesis-related condition would be more durable."
If no invalidation conditions are set for a major allocation decision:
"Decisions of this scale typically benefit from defined invalidation conditions. Would you like Atlas to suggest some based on the assumptions above?"

Section 11 — Review Plan:
If the review trigger is very broad ("whenever I feel like it" or left as default text):
"This review condition may be difficult to schedule. Would you like to link it to a specific event or monitoring condition?"

⸻

5. Editing Behavior

The Decision Workspace has two categories of editable content: Atlas-generated content that the user may modify, and user-authored content that Atlas never touches without permission.

Atlas-generated content (Atlas Suggested):
Pre-populated. The user may edit any part of it. When the user begins editing an Atlas-generated field:
— The field opens into full editing mode
— Atlas's original text remains accessible via "View original →" at the field edge
— If the user edits and then wants to restore: "Restore Atlas text" replaces the field contents with the original. A modification indicator disappears.
— Atlas remembers all user edits to suggested fields. Future suggestions for the same field respect the user's wording choices — if the user consistently prefers shorter assumptions, Atlas suggests shorter assumptions.

User-authored content (User Owned):
Atlas never pre-populates these fields. It never silently modifies them. If Atlas has a suggestion for a user-authored field, it always presents the suggestion as a separate offer — it does not appear in the field itself.

The Primary Reason field (Section 4) and the User Decision field (Section 3) are the most protected. Atlas may suggest alternative wording, but the suggestion is always shown side-by-side with the user's text, never as a replacement. The user selects whether to adopt any part of it.

Partial accept model:
When Atlas proposes changes to any multi-sentence field, the user may accept individual sentences or phrases rather than the whole suggestion. The proposed text is shown with selectable segments. The user confirms each segment or rejects it. This applies to:
— Section 4: primary reason suggestions
— Section 7: opportunity cost conclusion line suggestions
— Section 9: assumption and invalidation condition suggestions

The partial accept model is available only when Atlas proposes changes to existing user text. For accept/reject on Atlas-generated suggestions into empty fields, a simple accept/dismiss model is sufficient.

Undo behavior:
Standard text-field undo (Cmd/Ctrl+Z) works within any editing session for text changes. For structural actions — accepting an Atlas suggestion, acknowledging a challenge, toggling a supporting conclusion — a dedicated undo control appears adjacent to the action for approximately five seconds after the action is taken. After that window, undoing requires the explicit "Restore original" or "Undo acknowledgment" controls in the field or item. Acknowledged challenge items can be un-acknowledged via their item menu before recording. After recording, all fields are locked.

Auto-save:
The Workspace auto-saves draft state every 30 seconds and immediately after any structural action (acknowledging a challenge, recording an assumption, selecting an implementation type). The auto-save is silent — no toast, no indicator. An unsaved changes indicator in the header (a small dot adjacent to the decision subject label) shows when the current state differs from the last auto-save. When the state is current, the indicator disappears.

⸻

6. AI Collaboration

The user may explicitly invoke Atlas as a collaborator at any point. This is distinct from the ambient suggestion model — the user is actively asking Atlas to engage.

Collaboration entry points:

Every major text field has a secondary control: a small "Ask Atlas →" affordance. Tapping this opens a compact inline collaboration panel adjacent to the field.

Available collaboration actions, varying by field:

Shorten — Atlas rewrites the current text more concisely, preserving meaning. Shown as a side-by-side comparison. User accepts, rejects, or modifies.

Clarify — Atlas identifies the least precise phrase in the current text and suggests a more specific alternative. Shown with the imprecise phrase highlighted and an alternative offered.

Strengthen reasoning — Atlas identifies the weakest claim in the current text and suggests what evidence or argument would make it more durable. Does not rewrite — presents as a question: "What supports [the weak claim]?"

Challenge reasoning — Atlas argues against the current decision or reasoning from the perspective of a skeptical but informed observer. Presented as a single paragraph. The user may add the challenge to Section 6 as an acknowledged challenge item, or dismiss it.

Find contradictions — Atlas compares the current field content with prior decisions, current assumptions, and portfolio strategy. Surfaces any detected contradictions as challenge items in Section 6.

Compare with previous decisions — Atlas retrieves the decision reasoning for prior decisions on the same investment, presented in a side panel. The user can read the prior reasoning and return to the current field. Atlas does not apply any comparison automatically — it shows and lets the user draw their own conclusion.

Suggest assumptions — Atlas proposes two to three assumptions derived from the current decision and supporting conclusions. Presented as a list with Accept / Dismiss per item.

Suggest invalidation conditions — Atlas proposes two to three invalidation conditions derived from the current assumptions and risks. Presented with Accept / Edit / Dismiss per item.

Suggest review plan — Atlas proposes a review trigger based on monitoring conditions and the investment's next known event. Presented as a suggestion with accept / modify controls.

For every collaboration action, Atlas explains why it made the suggestion in one sentence. The explanation is shown below the suggestion, in a secondary text style. The user may collapse it.

Atlas never chains collaboration actions without user initiation. Completing one action (e.g., Shorten) does not automatically trigger another (e.g., Clarify). Each action is a discrete request.

⸻

7. Contradiction Handling

When Atlas detects a contradiction between the user's current reasoning and prior recorded decisions, stated portfolio strategy, or within the decision itself, it surfaces the contradiction as a challenge item in Section 6.

The contradiction appears calmly. It does not interrupt the user's editing. It does not produce a modal or alert. Section 6 expands (if collapsed) and the new item appears at the top of the list with a brief ambient highlight that fades within two seconds.

Contradiction framing:
— Always factual and specific: "This proposal differs from your [date] decision to maintain a maximum 7% allocation to individual positions."
— Never editorial: not "This seems like a bad idea" or "You should reconsider."
— Never urgent: no warning iconography at this specification level, no red states.

The contradiction item shows:
— The contradiction statement (one sentence)
— The source of the prior reasoning (link to the prior decision record or portfolio strategy document)
— A secondary explanation: why Atlas considers this a contradiction (one sentence)

The user may respond in four ways, each mapped to a specific control on the contradiction item:

Acknowledge — "I've seen this. Proceeding." The item moves to acknowledged state. Preserved in record. Not hidden.

Explain — "Here is why this is different." Opens a short text field attached to the item. The user's explanation is preserved in the record alongside the contradiction item. The item shows as acknowledged with explanation.

Modify decision — "I want to change my decision or reasoning in response to this." The item expands a shortcut: "Return to [relevant section]." Tapping navigates the user directly to the relevant field. After editing, the user returns to Section 6.

Review source reasoning — "Show me the prior decision." Opens the prior decision record in a nested side panel without leaving the Decision Workspace. The user reads the prior reasoning and closes the panel. No action is required.

Atlas does not trap the user at any contradiction. A user who acknowledges a contradiction and proceeds is making a deliberate choice. That choice is preserved in the record. The Decision Workspace does not prevent it.

⸻

8. Opportunity Cost Interaction

The Opportunity Cost section (Section 7) is one of the defining Atlas experiences. Its interactions should feel like comparative reasoning, not data browsing.

Initial state:
The section shows the decision subject row and the first alternative. Additional alternatives are revealed progressively as the user scrolls within the section.

Exploring alternatives:
Each alternative row has an "Explore →" control. Tapping it expands the row into a fuller comparative view:
— The decision subject summary on the left
— The alternative in full detail on the right
— The Atlas comparison sentence highlighted between them
— A user note field for the user to record their reasoning about this specific alternative

The expanded comparison is not a new page — it is an in-place expansion within the section. The user closes it and returns to the standard section view.

Switching between alternatives:
If multiple alternatives are present, the user navigates between expanded alternatives via previous/next controls within the expanded view. Each alternative is explored sequentially if the user chooses, or the user may collapse back to the list view.

Conclusion line interaction:
The opportunity cost conclusion line (Atlas-generated, user-editable) updates when the user has explored an alternative and added a note. Atlas may revise its generated conclusion based on what the user wrote in the note: "Based on your note, would you like to update the conclusion?" The user accepts or dismisses.

If the user explicitly reaches a different conclusion from Atlas's:
The user overwrites the Atlas-generated conclusion line. A modification indicator appears. The user's conclusion is preserved. Atlas does not re-propose unless the alternatives themselves change.

Cash alternative:
If no investment alternatives are identified, the section shows a single alternative row: "Hold cash — no deployment." The comparison line reads: "Keeping this capital available preserves optionality but foregoes the expected return of the current decision." The user may dismiss this row if it is not relevant.

⸻

9. Review Mode Behavior

When the user enters the Decision Workspace from a prior decision record (review mode), the behavioral model shifts.

On entry:
The Workspace opens with the prior decision displayed in a collapsed reference panel at the top of the scrolling body, above Section 1. The panel shows: the prior decision type, the prior decision text, the prior confidence level, the date, and an "Expand original record →" control.

The current analysis occupies the main body — the same thirteen-section structure, populated with current data from the originating Workspace.

Reading sequence for review mode:
Atlas surfaces the original reasoning first — the user sees what they believed before seeing what has changed. The section order is:

1. Prior Decision (collapsed reference panel — expandable)
2. What Has Changed Since Recording (an additional section, only present in review mode, positioned above Section 1)
3. Current Conclusion (Section 1)
4. All remaining sections in standard order

The "What Has Changed Since Recording" section contains:
— Monitoring conditions that have changed status (Holding → Weakening, Weakening → Broken)
— Assumptions that have changed
— New evidence that postdates the original decision
— Time elapsed since the decision was recorded

After the user has reviewed the current analysis, they record a review outcome using one of the five version types defined in UX-009A. The version type selector appears adjacent to Section 13 (Record Decision) in review mode.

History is shown. Original reasoning is never rewritten. The prior decision record is read-only throughout the review.

⸻

10. Draft Behavior

Auto-save:
Continuous silent auto-save every 30 seconds and on all structural actions. No confirmation toasts. The unsaved changes indicator (a small dot in the header) communicates current state without demanding attention.

Draft restoration:
When the user returns to the Decision Workspace for the same subject after leaving with unsaved changes:
— The Workspace opens to the draft state — all fields, all section expansions, all scroll position restored
— An ambient note appears below the header: "Restored from draft — [time]. You left [N] required fields incomplete."
— A "Discard draft and start fresh" control is available in the header area, low-emphasis

Comparing draft with recorded version:
When a draft exists alongside a recorded version (the user is amending a prior decision), a "Compare with recorded" control appears at the top of the scrolling body. Tapping it shows a side-by-side view of the draft and the recorded version for any fields that differ. Changed fields are indicated. The user closes the comparison and returns to the draft.

Discarding a draft:
The user selects "Discard draft" and confirms once: "Discard this draft? Your progress will be lost." Two options: "Discard" / "Keep draft." No further confirmation. The discard action does not delete recorded decisions — it discards only unsaved work in the current session.

⸻

11. Confidence Interaction

The confidence indicator in Section 12 (Final Decision Card) is tappable/clickable.

When the user taps the confidence indicator:
A compact explanation panel expands adjacent to the indicator. It shows:

— Why Atlas assessed this confidence level: a list of the factors that lowered confidence (broken assumptions, unacknowledged challenges, missing evidence) or raised it (intact assumptions, strong supporting evidence, historical consistency)
— Which specific assumptions reduce confidence: links to the relevant assumption rows in Section 9
— What evidence is missing that would increase confidence: one or two sentences from Atlas, specific rather than generic

The user may override the Atlas-assessed confidence level by selecting from the five options directly in this panel. An override indicator appears: "Confidence set by user — [level]." The override is preserved in the record.

The confidence panel closes when the user taps outside it or presses Escape.

Confidence is never expressed numerically. The five qualitative states (High Confidence / Moderate Confidence / Low Confidence / Evidence Incomplete / Intentionally Deferred) are the only options, both for Atlas-assessed and user-overridden states.

⸻

12. Assumption Behavior

Each assumption row in Section 9 (Supporting Assumptions subsection) supports the following interactions:

Expand / collapse:
The row shows the assumption statement and status indicator in collapsed state. Tapping the row expands it to show the supporting reasoning and any linked evidence.

Edit:
Tapping the edit control opens the assumption statement as an inline text field. The user may reword it. Atlas's original wording is accessible via "View original →". Saving the edit updates the assumption in the Final Decision Card if the assumption appears there.

Comment:
A comment field opens below the assumption. The user adds a note — for example, "This assumes Q3 data confirms the trend. Revisit after September earnings." The comment is preserved in the record.

Mark uncertain:
A "Mark uncertain" toggle changes the assumption status to "Under Review." This is reflected in the confidence assessment — marking an assumption as uncertain may lower the Atlas-assessed confidence level. An ambient note appears: "Marking this assumption as uncertain has been reflected in the confidence assessment."

Mark resolved:
If an assumption was previously marked "Weakening" or "Under Review" by Atlas, the user may mark it as "Resolved" if new evidence has addressed it. A short text field for the resolution evidence is required: "What resolved this?" The resolution is preserved in the record.

Link to reasoning:
A "Link to analysis →" control opens the relevant section of the originating Investment Workspace or Portfolio Workspace in a nested side panel — without leaving the Decision Workspace.

Link to evidence:
If the assumption has a linked monitoring condition in the Monitoring subsection, a "See monitoring condition →" control navigates (smooth scroll) to the relevant row in the Monitoring subsection.

⸻

13. Monitoring Condition Behavior

Each monitoring condition row supports:

Preview of future Atlas behavior:
A small informational note below each condition: "If this condition changes, Atlas will surface this decision for review in your Daily Briefing." For conditions linked to an invalidation trigger: "If this condition reaches the invalidation threshold, Atlas will reopen this decision."

This preview is always visible when the row is expanded. It should feel like Atlas describing its own behavior in plain language — making its future actions understandable and predictable.

Status updates (post-recording):
Monitoring conditions show one of three statuses — Active / Triggered / Paused — visible in the decision record in Atlas Memory. Status changes do not require re-entering the Decision Workspace.

Pausing a monitoring condition:
The user may pause a monitoring condition from the decision record in Atlas Memory. A pause reason is required (one brief field). Paused conditions do not trigger reviews. The Workspace notes when a condition is paused during a review.

⸻

14. Invalidation Condition Behavior

Specificity guidance:
When the user writes or edits an invalidation condition, Atlas evaluates the wording for specificity and observability. If the wording is vague or references price movement rather than thesis conditions, Atlas presents a non-blocking suggestion:

"Invalidation conditions tied to price movement can trigger reviews during normal volatility. Here is a more thesis-grounded alternative: [specific alternative]."

The user accepts, dismisses, or modifies. The suggestion does not appear again for the same condition unless the content changes materially.

For Exit decisions only — re-entry consideration field:
Below the invalidation conditions, an additional optional field appears: "What would cause you to consider re-entering this investment?" This field is user-authored, not Atlas-proposed. It is preserved in the record. It becomes visible in Atlas Memory as a signal if the investment appears in future Portfolio Workspace or Investment Workspace reviews.

Future review triggers:
Each invalidation condition row shows: "Triggers Decision Workspace review if reached." This label is always visible in expanded state. The user should always understand which conditions are actively linked to future reviews.

⸻

15. Implementation Behavior

The implementation type selector (Section 10) and its conditional fields behave as a lightweight adaptive form — each implementation type reveals only the fields relevant to it. Changing the implementation type collapses irrelevant fields and expands relevant ones with a smooth transition.

The No Action implementation type requires a deliberate acknowledgment step:
After selecting No Action, a single confirmation prompt appears within the section (not a modal): "Confirm this is a deliberate decision to take no action." A single control: "Confirmed." Until the user confirms, the implementation section is not marked complete and the Record Decision gate explains: "Confirm the no-action decision before recording."

Implementation status (post-recording):
Implementation status is updated from the decision record in Atlas Memory — not from within the Decision Workspace. This separation reinforces the principle that decision and execution are distinct. Implementation updates do not modify the recorded reasoning. They are tracked as a separate evolving state linked to the decision record.

If the implementation type is Conditional, Atlas creates a monitoring condition for the named condition in Section 9 automatically: "Implementation condition: [condition from Section 10]." The user may edit this condition in Section 9.

⸻

16. Version Behavior

When the user opens a recorded decision for amendment, Atlas presents the version type selector before any editing begins. The user must select a version type before they can edit:

— New Review: "I am reviewing this decision against current conditions. The original decision remains."
— Revision: "I am amending specific fields. The change will be versioned."
— Superseding Decision: "I am replacing this decision with a new one."
— Implementation Update: "I am updating the implementation status only." (Redirects to the decision record in Atlas Memory — no editing of reasoning.)
— Review Completion: "I am closing this review cycle." (Presents a streamlined completion form — current conditions, outcome assessment, next review trigger.)

After selecting a version type, the relevant sections are editable. Sections not relevant to the version type remain locked and read-only during this session.

Version history panel:
A "View history →" control is accessible from the decision record header at low emphasis. It opens a chronological list of all versions: each entry shows version type, date, changed fields (for revisions), and a link to view that version's full record. Version history is read-only.

Atlas never overwrites. Every change creates a new version entry. The original reasoning is always retrievable.

⸻

17. Completion Behavior

As the user approaches completion, the Workspace reduces its interactive surface. This is a deliberate editorial choice — the final section should feel quiet and focused.

Progression signal:
When the universal minimum (user decision text, primary reason) and any decision-type-conditional requirements (implementation type, review trigger unless overridden, Portfolio Consequences acknowledgment where applicable) are complete, the Record Decision button reaches full availability. Unacknowledged Challenges never affect this availability. No fanfare. No progress percentage. The button simply becomes available. The completion gate explanation disappears. *(Corrected per ADR-002/C-04: this line previously stated a flat "four required fields" rule with no decision-type conditionality.)*

The Final Decision Card (Section 12) has been live-updating throughout. By the time the user reaches it, it reflects their completed work. Reading it in full before recording is the natural last step.

The body content immediately above the footer (Section 13) shows the context statement: "Recording this decision will preserve it in Atlas Memory." If any challenges remain unacknowledged, the count note appears. No other elements compete for attention at this point.

The scroll position at this stage should already be near the bottom. The user should not need to scroll to reach the Record Decision footer — they have arrived at it by reading through the document.

⸻

18. Post-Recording Behavior

After the user selects Record Decision:

Transition:
The scrolling body transitions to the post-decision state. The transition is not instantaneous — a brief pause (approximately 400ms) follows the action before the body clears. This pause is the moment of recording. It should feel like something meaningful just happened, without requiring any visual celebration to communicate it.

Post-decision state content:
The Final Decision Card appears at full reading width, centered in the body, with generous surrounding space. It is the only content in the body. The card is in completed form — all six fields, all user-authored and Atlas-assembled content, rendered as a read-only document.

Confirmation line:
A single line immediately below the card: "Decision recorded · [date] · [investment name or portfolio scope]."
Nothing else. No summary of what Atlas learned. No encouragement. No calls to action beyond the three contextual next steps.

Three contextual next steps — plain labeled links, left-aligned:
1. Return to [originating Workspace name] — the most prominent of the three
2. View decision in Atlas Memory
3. [Next step when a clear one exists] — e.g., "Open Danaher Workspace to begin capital comparison"

If no clear next step exists, only two links appear.

Atlas does not celebrate. Recording a decision is the completion of a reasoning process, not a transaction success. The user's feeling of completion should come from the quality of their recorded reasoning, not from any system affirmation.

⸻

19. Error Prevention

Atlas surfaces the following concerns without blocking the user unnecessarily. The general principle: explain the concern clearly, then permit the user to proceed.

Reasoning appears weak (primary reason is very brief for a major decision):
An ambient note appears below the primary reason field after a pause: "This is a significant decision. Consider expanding the reasoning." Not a validation error. Dismissible.

Decision contradicts earlier reasoning:
A contradiction item appears in Section 6. Section 6 expands if collapsed. (See Section 7, Contradiction Handling.)

Review trigger appears unmonitorable:
An Atlas suggestion appears in Section 11: "This review condition may be difficult to schedule. Consider linking it to a specific event." (See Section 4, Atlas Suggestion Model.)

Implementation conflicts with portfolio strategy:
A challenge item appears in Section 6. (See Section 7, Contradiction Handling.)

Primary reason field left empty:
The Record Decision button is disabled. The adjacent explanation: "Add a primary reason before recording." No inline error on the field. The user navigates to the field via the scroll behavior described in Section 2.

Critical assumption has Broken status:
A challenge item appears in Section 6: "A supporting assumption for this decision is classified as Broken." The user acknowledges. Not blocked.

All error prevention interactions share one tone: collaborative, factual, calm. Atlas does not diagnose, alarm, or moralize. It states the concern and trusts the user to decide.

⸻

20. Undo Behavior

In-session text undo:
Standard Cmd/Ctrl+Z within any text field undoes character-by-character edits, as expected. This applies to all text fields regardless of ownership classification.

Structural action undo:
For actions that change the state of a section or item — accepting an Atlas suggestion, acknowledging a challenge item, toggling a supporting conclusion, selecting an implementation type — a brief undo affordance appears adjacent to the action for five seconds after it is taken. The affordance reads: "Undo." Tapping it reverses the structural action. After five seconds, the affordance disappears.

After the five-second window:
— For text field edits: "Restore Atlas text" or "View original →" are available in the field controls
— For acknowledged challenge items: an "Undo acknowledgment" control is available in the item menu before recording
— For Atlas suggestion acceptance: "Remove suggestion" in the field area restores the pre-suggestion content
— After recording: all fields are locked. Undo is no longer available. Changes require a version action.

The undo model ensures that no user action within the Decision Workspace causes irreversible loss of content before recording. The only irreversible action is recording itself — and recording is deliberate, gated, and preceded by a visible summary of everything being committed.

⸻

21. Keyboard Behavior

The Decision Workspace is fully operable without a mouse or pointer.

Tab order:
Tab navigates through interactive elements in document order — top to bottom, left to right within rows. The tab order follows the reading order: Header controls → Section 1 link → Section 2 note field → Section 3 decision field → Section 3 type selector → Section 4 fields → ... → Footer actions.

Focused elements receive a visible focus ring at all times. The focus ring style is defined in UX-011.

Section expansion:
Collapsible section headers are focusable. Enter or Space toggles expand/collapse. The expanded content receives focus immediately after expansion.

Quick navigation — keyboard shortcuts:

Cmd/Ctrl+1 through Cmd/Ctrl+9: navigate to Sections 1 through 9 directly. Sections 10–13 are reached via Cmd/Ctrl+0, Cmd/Ctrl+Shift+1, Cmd/Ctrl+Shift+2, Cmd/Ctrl+Shift+3.

Cmd/Ctrl+Enter (when the Record Decision button is available): records the decision. Does not function when the button is disabled — prevents accidental recording.

Cmd/Ctrl+S: saves draft. Functions at any point.

Escape: when a collaboration panel, side panel, or expanded comparison view is open, Escape closes it and returns focus to the triggering element. When no panel is open, Escape triggers the "Exit without saving?" prompt.

AI Collaboration via keyboard:
From any major text field, Shift+Cmd/Ctrl+A opens the Atlas collaboration panel for that field. The available actions are navigable by keyboard. Enter selects an action. Escape closes the panel.

Challenge item acknowledgment via keyboard:
Tab to the challenge item. Enter acknowledges. The focus moves to the next unacknowledged item.

⸻

22. Mobile Interaction Adaptations

On mobile, the interaction model adapts for touch without changing the information architecture or section order.

Editing:
Text fields expand to full screen when focused on mobile — the keyboard and the field occupy the full viewport, with the field label visible above and a "Done" control to close the keyboard. The remainder of the Decision Workspace is accessible after closing the keyboard.

Section expansion:
Section headers have a minimum tap target of 44px height. Expand/collapse is triggered by tapping anywhere on the header row, not only on the chevron. Expanded sections may be swiped up to collapse (a swipe-up gesture on the section header area collapses it) — the standard tap on the header also works.

Opportunity cost comparison:
On mobile, the expanded comparison view (Section 7) is fullscreen rather than an in-place expansion. The user navigates to it from the section, views the comparison, and returns to the section via a "Back to decision" control.

Long reasoning fields:
The primary reason field (Section 4) and user decision field (Section 3) expand to multiline on mobile as the user types. The field does not have a maximum visible height on mobile — it grows with the content, and the surrounding sections scroll away below it.

AI Collaboration on mobile:
The "Ask Atlas →" affordance opens a bottom sheet rather than an inline panel. The available actions are shown as a list. Tapping an action shows the suggestion in the same bottom sheet. Accept / dismiss controls are at the bottom of the sheet, reachable without scrolling.

Record Decision on mobile:
The footer is always visible. On mobile, the footer occupies the bottom of the viewport — the primary action, secondary actions, and (when relevant) the completion gate explanation are all within thumb reach. The Record Decision button has a minimum tap target of 48px height.

Touch deliberateness:
Touch interactions are designed to be deliberate, not accidental. The Record Decision action requires a single deliberate tap — no double-tap, no swipe, no hold. Its unavailable state carries no visual feedback suggesting it is active, but the control remains tappable: a single deliberate tap while unavailable behaves identically to the keyboard contract described in Section 2 — it does not record the decision, but moves focus to the first unmet required field and re-announces the explanation there. *(Corrected per ADR-002/C-06: this line previously stated the disabled state "makes it untappable," which would contradict the requirement that the control remain focusable and reachable on tap.)*

⸻

23. Accessibility Behavior

Screen reader announcements:
All section headers are announced when the user navigates to them, including their current state (expanded / collapsed) and the summary content when collapsed.

Challenge item acknowledgment: announced as "[Challenge text] — acknowledged." The change in state is communicated immediately.

Atlas suggestions: announced as "Atlas suggestion available for [field name]. [First sentence of suggestion]." The suggestion controls are announced as "Accept suggestion," "Dismiss suggestion," "Show reasoning."

Record Decision button: announced as "Record Decision — [available / unavailable: reason]." The reason for the unavailable state is included in the announcement. The button carries `aria-disabled="true"` — never the native HTML `disabled` attribute — so it remains in the accessibility tree and reachable by screen reader navigation at all times. *(Corrected per ADR-002/C-06: this line previously used "disabled" without qualification.)*

Confidence indicator: announced as "Decision confidence: [level]. Tap to inspect." When expanded: the explanation content is announced in full.

Auto-save: the unsaved changes indicator is not announced — it is a visual-only ambient state indicator. Auto-save itself produces no announcement.

Post-recording: announced as "Decision recorded. [Decision summary card content]." The three next steps are announced in order.

Focus management:
When a section expands automatically (Atlas-triggered), focus moves to the first new content item within the expanded section if the user was not already within that section. If the user was in the section when Atlas expanded additional content, focus does not move — the new content appears below their current position.

When the Record Decision button is tapped while disabled, focus moves to the first incomplete required field. A screen reader announcement names the incomplete field: "Primary reason required — navigating to the primary reason field."

When a collaboration panel opens, focus moves to the first action in the panel. When the panel closes, focus returns to the triggering field.

Motion reduction:
When the user has enabled reduced motion at the OS level, all transitions are instantaneous — no scroll animation, no section expand animation, no post-decision body transition pause. Structural changes happen immediately. The content is the same; only the motion is removed.

Interaction timing:
No time limits on any interaction. No auto-dismissing tooltips or suggestions that require the user to respond within a window. The Atlas suggestion affordance appears after a pause but remains available until the user acts. Drafts are saved continuously — there is no session timeout that would lose work.

Error announcements:
Completion gate explanations (the text adjacent to the unavailable Record Decision button, exposed via `aria-describedby`) are announced when the button is focused and when its state changes (from unavailable to available, or when a new explanation appears). This is reachable because the button carries `aria-disabled="true"` rather than the native `disabled` attribute, and therefore remains focusable throughout. *(Corrected per ADR-002/C-06: this line previously assumed the button could be "focused" while "disabled" without stating the mechanism — native `disabled` would remove the button from the tab order and make this requirement unsatisfiable.)*

⸻

24. Interaction Hierarchy

Every interaction in the Decision Workspace belongs to one of three tiers. The Workspace surfaces only the tier appropriate to the current moment.

Immediate — interactions the user needs now, accessible with a single tap or click:
— Section expand / collapse
— Text field editing
— Accept Atlas suggestion (single-tap)
— Acknowledge challenge item (single-tap)
— Toggle supporting conclusion (single-tap)
— Select implementation type (single-tap)
— Select review trigger (single-tap)
— Save as Draft (always in footer)
— Return to Workspace (always in footer)
— Record Decision (when available, footer)

Secondary — interactions available but not foregrounded:
— Ask Atlas → (available in every major text field)
— Compare with recorded version (draft mode)
— View original → (within edited Atlas-suggested fields)
— View full analysis → (Section 1)
— Explore alternative → (Section 7, per alternative row)
— Inspect confidence (Section 12)
— Expand assumption detail / comment / link (Section 9)
— View prior decisions (header control)
— View history (decision record header)

Rare — interactions for infrequent or advanced use:
— Supersede recorded decision
— Merge draft with recorded version
— View implementation history
— Pause a monitoring condition
— Mark assumption as resolved
— Override Atlas-assessed confidence
— Partial accept of Atlas suggestion (multi-sentence fields)

The Workspace does not display Rare interactions in the primary flow. They are accessible from item menus, the decision record in Atlas Memory, or the version history panel — not from the main Workspace surface.

⸻

25. Emotional Tone

Every interaction must communicate the following:

Clarity — the user always knows what Atlas is saying, why, and what they can do with it. No ambiguity in suggestion language, contradiction framing, or completion state.

Respect — Atlas never implies the user is making a mistake. It surfaces information. The user interprets. Suggestions are offers, not corrections. Contradictions are facts, not judgments.

Patience — no interaction rushes the user. No progress bars, no completion percentages, no "You're 70% done" messaging. The user moves at their own pace.

Thoughtfulness — Atlas's suggestions, contradiction items, and review prompts reflect genuine engagement with this specific decision — not generic templates. The suggestion for a specific assumption references that assumption's content. The contradiction cites the specific prior decision it conflicts with.

Confidence without certainty — Atlas presents its assessments and suggestions with appropriate conviction while acknowledging the limits of its confidence. It says "appears to conflict" rather than "contradicts." It says "may be difficult to monitor" rather than "is unmonitorable."

The Workspace must never feel:
— Sales-like: no language that nudges toward more activity or more changes
— Urgent: urgency appears only when genuinely justified (a defined invalidation condition has been reached)
— Robotic: Atlas sounds like a thoughtful analyst, not a validation engine
— Bureaucratic: no unnecessary confirmation dialogs, no required fields for decisions that don't need them
— Chatbot-driven: Atlas does not respond in conversational back-and-forth within the Workspace. Its collaboration model is precise and structured, not conversational.
— Transactional: the Record Decision action feels like preservation, not submission

⸻

26. Governing Interaction Principles

These principles apply to every interaction, microinteraction, and behavioral pattern in the Decision Workspace.

1. Every interaction should improve reasoning.
No interaction exists to generate engagement, measure completion, or encourage activity. If an interaction does not help the user think more clearly, it does not belong here.

2. Atlas suggests. The user decides.
No interaction implies that Atlas made a decision. No interaction prevents the user from making a decision Atlas would not recommend. Atlas proposes, surfaces, and explains. The user accepts, modifies, and commits.

3. Nothing is rewritten silently.
Atlas never overwrites user content without showing a comparison and receiving explicit acceptance. Every change — structural or textual — is visible, reversible within the session, and preserved in the version history.

4. Complexity appears only when needed.
Sections expand when the evidence warrants it. Suggestions appear when the field can be improved. Contradictions surface when they exist. The Workspace does not surface depth that is not relevant to this decision at this moment.

5. History remains trustworthy.
No interaction enables silent modification of recorded reasoning. Post-recording changes create versioned entries. The original record is always retrievable. The user can trust that what they recorded is what was preserved.

6. Interactions create confidence — not activity.
The measure of a successful interaction is whether the user feels more certain about their decision — or more certain that deferral is right — not whether they completed more fields or made more changes.

7. Reasoning always precedes commitment.
The reading flow is not optional. The user moves through the reasoning sequence before reaching the record action. The Workspace does not offer a shortcut to the Record Decision action that skips the reasoning sections.

8. No interaction rewards impulsiveness.
The Workspace creates deliberate friction where friction is appropriate — not bureaucratic friction, but reasoning friction. The friction comes from seeing a contradiction, from reading a challenge, from recognizing an opportunity cost. It is intellectual, not procedural.

9. Uncertainty must remain explicit.
No interaction resolves uncertainty by hiding it. If an assumption is uncertain, it is labeled uncertain. If the confidence is moderate, it is shown as moderate. The user records the decision with full visibility of what is not yet known.

10. The user's ownership of the decision is never ambiguous.
The user decision field is the most prominent editable element. Atlas's proposals are always labeled. The Record Decision action is user-initiated only. At no point should the user be unsure whether they or Atlas made a choice.

⸻

What UX-010 Establishes

The following interaction behaviors are now fixed:

— Interaction philosophy: three behavioral modes (Ambient, Responsive, Collaborative) with clear transition logic. The governing test for every interaction: "Does this help the user think more clearly?"

— Scroll behavior: gentle deceleration at the four high-emphasis moments (Current Conclusion, Proposed Decision, Opportunity Cost conclusion, Final Decision Card). Smooth animated scrolling for all auto-scroll events. Tapping Record Decision while incomplete scrolls to the first incomplete field.

— Progressive disclosure triggers: seven automatic expansion conditions (material contradiction, low confidence, significant portfolio impact, prior opposing decision, conditional/deferred implementation type, price-based invalidation condition, major decision entry). Four automatic collapse conditions (decision type changed to Maintain/No Action, all challenges acknowledged, decision type changed to Defer, major type change).

— Atlas suggestion model: suggestions appear after a 1.5-second typing pause. Presented as offers. Accept / Dismiss / Engage model. Partial accept available for multi-sentence suggestions. Suggestions do not repeat for unchanged content. Atlas always explains why it suggested.

— Editing behavior: Atlas-suggested content is pre-populated and user-editable. User-authored content is never pre-populated by Atlas. "View original →" is always available for edited Atlas content. Five-second structural undo window. Standard text undo in fields. Auto-save every 30 seconds and on structural actions.

— AI Collaboration: "Ask Atlas →" available from all major text fields. Eight explicit collaboration actions (Shorten, Clarify, Strengthen, Challenge, Find Contradictions, Compare with prior, Suggest Assumptions, Suggest Invalidation, Suggest Review Plan). Atlas explains every suggestion. No chaining without user initiation.

— Contradiction handling: contradictions appear as challenge items in Section 6 without interruption. Section 6 expands automatically. Contradiction items show: statement, source link, reasoning. Four user responses: Acknowledge, Explain, Modify Decision, Review Source. No blocking.

— Opportunity Cost interaction: in-place expanded comparison per alternative row. Previous/next navigation between alternatives. Conclusion line updates based on user notes. Cash alternative row when no investments are identified.

— Review mode: prior decision in collapsed reference panel above Section 1. "What Has Changed Since Recording" section added. Version type selector required before editing. Original reasoning read-only throughout.

— Draft behavior: auto-save every 30 seconds and on structural actions. Silent — no toast. Unsaved changes indicator in header. Draft restoration on re-entry with ambient note. "Compare with recorded" comparison view for amendments.

— Confidence interaction: tappable confidence indicator opens explanation panel. Shows contributing factors, links to specific assumptions, identifies missing evidence. User may override Atlas-assessed confidence. Five qualitative states only — no numerical confidence.

— Assumption behavior: expand/collapse, edit, comment, mark uncertain, mark resolved with evidence field, link to reasoning, link to monitoring condition. Status changes reflected in confidence assessment.

— Monitoring condition behavior: preview of future Atlas behavior visible per row ("If this condition changes, Atlas will surface this decision"). Status updates post-recording from Atlas Memory, not from within the Workspace.

— Invalidation condition behavior: specificity guidance when price-based conditions are written. Non-blocking suggestion with specific alternative. Exit-only re-entry consideration field (user-authored, optional).

— Implementation behavior: five-type selector with adaptive conditional fields. No Action requires deliberate in-section acknowledgment. Conditional implementation auto-creates a monitoring condition in Section 9. Status tracked externally post-recording.

— Version behavior: version type must be selected before editing begins. Five version types with defined scopes. Version history panel (read-only) accessible from decision record. Original reasoning never overwritten.

— Completion behavior: Record Decision reaches availability when the universal minimum and any decision-type-conditional requirements are complete; unacknowledged Challenges never affect availability. No fanfare. Live-updating Final Decision Card throughout. 400ms transition pause before post-decision state. *(Corrected per ADR-002/C-04; this line previously stated a flat "four required fields" rule.)*

— Post-recording behavior: Final Decision Card at full emphasis. Single confirmation line. No celebration. Maximum three contextual next steps. Footer changes to "Close Workspace" only.

— Error prevention: nine defined concern types, each surfaced through ambient notes, challenge items, or completion gate explanations. No blocking except missing required fields. All error prevention language is collaborative and specific.

— Undo behavior: standard text undo in fields. Five-second structural undo window. Field-level restoration controls after the window. Acknowledged challenge items un-acknowledgeable before recording via item menu.

— Keyboard behavior: full keyboard operability. Tab order follows document order. Section headers focusable with Enter/Space toggle. Cmd/Ctrl+1–9 section navigation. Cmd/Ctrl+Enter for Record Decision (when available). Cmd/Ctrl+S for draft save. Shift+Cmd/Ctrl+A for Atlas collaboration panel.

— Mobile interaction adaptations: fields expand to full screen when focused. Section headers full-row tap target. Opportunity cost comparison is fullscreen modal on mobile. Collaboration via bottom sheet. Footer always accessible at thumb height.

— Accessibility behavior: screen reader announcements for all section state changes, Atlas suggestions, challenge acknowledgments, button states, post-recording content. Focus management on auto-expansion and on activation of the Record Decision button while unavailable (`aria-disabled="true"`, never native `disabled`) — focus moves to the first unmet required field. Motion reduction removes all transitions. No time limits on any interaction.

— Interaction hierarchy: three tiers (Immediate, Secondary, Rare) with defined membership. Rare interactions not surfaced in the primary flow.

— Emotional tone: clarity, respect, patience, thoughtfulness, confidence without certainty. Ten specific anti-patterns excluded.

— Ten governing interaction principles.

⸻

Remaining Questions

The following are genuine unresolved interaction questions that require decisions before implementation:

1. Collaboration panel form factor on tablet: should the collaboration panel appear as an inline panel (as on desktop) or as a bottom sheet (as on mobile)? The breakpoint between these behaviors has not been defined.

2. The five-second structural undo window: is five seconds the right duration? For users reading carefully through a long decision, five seconds after acknowledging a challenge item may pass before they notice. A longer window (ten to fifteen seconds) may be more appropriate for a Workspace where the user is expected to read, not scan.

3. Partial accept granularity: the partial accept model specifies "selectable segments" for multi-sentence suggestions, but the exact segmentation unit has not been defined. Should it be sentence-level, clause-level, or paragraph-level? Sentence-level is recommended but not finalized.

4. Behavioral context dismissal: when the user dismisses a behavioral context item with "This is a thesis-driven decision," is the item completely hidden from the record or preserved in a reduced-emphasis state? The spec requires the record to show it was seen — but the exact visual form of the preserved state is not yet defined.

5. Auto-scroll conflict: if the user is actively editing a field when Atlas detects a contradiction and expands Section 6, does the auto-expansion interrupt the user's editing context? The spec specifies that Section 6 expands without interruption — but the exact behavior when the user is mid-type in another section needs implementation guidance.

⸻

Requirements for UX-011

The Visual Design & Polish Specification must establish:

Typography hierarchy:
— The visual distinction between the conclusion statement (highest weight), supporting reasoning (medium weight), and secondary labels (lowest weight)
— The typographic form of Atlas-generated versus user-authored content — these must be visually distinguishable without relying on color alone
— The exact typographic treatment of the user decision field — it must feel like authoring a document, not filling a form input
— The font family, weight, and size for the section label convention (small uppercase)
— The typographic form of Atlas suggestion offers and contradiction statements

Spacing system:
— The rhythm between sections — how much space separates them, and how the section boundary divider behaves
— The internal rhythm within sections — between labeled groups, between rows, between the section label and the first content item
— The spacing within the Final Decision Card

Visual emphasis:
— How the four high-emphasis moments (Current Conclusion, Proposed Decision, Opportunity Cost conclusion, Final Decision Card) are visually distinguished from the surrounding sections
— How the user decision field is visually elevated above all other text fields

Color semantics:
— The color treatment of the five confidence levels (High / Moderate / Low / Evidence Incomplete / Intentionally Deferred)
— The color treatment of assumption statuses (Holding / Under Review / Weakening / Broken)
— The color treatment of challenge item types (and how behavioral context items are visually distinguished from analytical challenge items)
— The color treatment of the modification indicator (user has changed Atlas's proposal)
— How Atlas-generated and user-authored content are color-distinguished

Card treatments:
— The visual form of the Current Conclusion card (Section 1)
— The visual form of the Final Decision Card (Section 12) — both in live-updating and completed states
— The visual form of the Atlas proposal block (Section 3)
— Whether individual challenge items, assumption rows, and alternative rows use card-level containment or divider-level separation

Iconography:
— Whether any iconographic treatment is used for decision types, assumption statuses, or challenge item types
— The visual form of the "Ask Atlas →" affordance
— The visual form of the expand/collapse chevron and whether it is uniform across all sections

Dividers:
— The visual treatment of section boundary dividers
— Whether section boundaries within Section 9 (between Assumptions, Monitoring, and Invalidation subsections) are visually distinct from inter-section dividers

Elevation:
— Whether the fixed header and footer use elevation (shadow, surface distinction) to communicate their fixed nature
— Whether the Final Decision Card uses elevation in its completed form

Motion design:
— The duration and easing of section expand/collapse animations
— The duration and easing of the auto-scroll behavior at high-emphasis scroll pause points
— The 400ms post-recording transition — what exactly animates, and how
— How Atlas suggestion affordances appear and disappear
— How the unsaved changes indicator appears and disappears

Hover states:
— The hover state for all interactive elements: section headers, text field controls, challenge acknowledgment controls, Atlas suggestion affordances, alternative row expand controls, and footer actions

Focus states:
— The focus ring design — consistent across all interactive elements
— Whether focus rings differ between keyboard and pointer-driven focus (pointer-initiated focus may suppress the ring per modern convention)

Transitions:
— The enter transition for the Decision Workspace overlay
— The dismiss transition (Return to Workspace, Close after recording)
— The transition between the draft state and the post-decision state
— The transition for collaboration panels and side panels opening and closing

Empty-state visuals:
— The visual design of all six defined empty states — how they communicate "intentional" rather than "incomplete"
— The empty state for the user decision field (placeholder text style)
— The empty state for the primary reason field

Completion visuals:
— The exact visual form of the post-decision state — the Final Decision Card at full emphasis, the confirmation line, and the three contextual next steps
— Whether the 400ms recording pause includes any visual feedback (a momentary surface change, a text change on the button before the transition, or simply a pause with no change)

Overall premium feel:
— The visual character that makes the Decision Workspace feel like a serious reasoning environment — not a form, not a chat interface, not a brokerage terminal
— How the Workspace communicates calm and deliberateness through visual design choices that reinforce the interaction model defined in UX-010

Do not produce UX-011 yet.

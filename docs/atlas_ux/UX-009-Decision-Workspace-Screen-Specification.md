UX-009 — Decision Workspace Screen Specification

Status: Screen Specification Complete
Owner: Atlas Product
Governs: Decision Workspace — information architecture, reading flow, section hierarchy, interaction model
Depends on: UX-008 — Decision Workspace Philosophy
Defers to: UX-009A — Decision Workspace Wireframe Specification

**Correction Notice (Phase 2, governed by ADR-002 — 2026-07-24):** This document's original identity (Status, Owner, Governs, Depends on, Defers to, as above) and original date are preserved unchanged. Three semantic areas were corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan, Phase 2:
- **C-03 (Decision Workspace Sequence):** Sections 5, 6, and 12 renamed to "Supporting Factors," "Challenges," and "Final Decision Card" — this document previously named them "What Supports This Decision," "What Challenges This Decision," and "Final Decision Summary" — no change to section order, count, or content.
- **C-04 (Record Decision Completion Gate):** the "Preventing Incomplete Records" section and the Section 13 available/unavailable states were corrected from a flat four-condition rule (with Challenges acknowledgment hard-blocking) to the universal minimum (Decision Statement, Primary Reason), a decision-type-conditional matrix, and Challenges acknowledgment as soft friction that never blocks recording.
- **C-06 (Unavailable Primary Action Accessibility):** the Section 13 unavailable-state description was corrected to specify `aria-disabled="true"` (never native `disabled`), permanent focusability, and that activation while unavailable navigates focus to the first unmet required field.

This notice does not claim any of the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, at each corrected passage. All content outside these three areas is unchanged.

⸻

Purpose of This Document

UX-009 translates the philosophy established in UX-008 into a complete screen specification. It defines what the Decision Workspace contains, in what order, and why. It determines which sections are always present, which adapt to decision type, and how the user moves from received analysis to recorded commitment.

No wireframe is produced here. No visual styling is specified. The purpose is to fix the information architecture and interaction model before any layout work begins.

⸻

Entry Points

The Decision Workspace is not a standalone destination. It is entered from within an existing reasoning context.

Primary entry points:

From the Investment Workspace — when an individual investment decision is required. The Investment Workspace surfaces the "Record Decision" call-to-action when the review has reached a clear conclusion or when a decision is overdue.

From the Portfolio Workspace — when a portfolio-level decision is required. The Portfolio Workspace surfaces the Decision Workspace when unresolved allocation decisions remain open at the end of a portfolio review.

From the Dashboard — when a flagged item has an unresolved decision state. The Daily Briefing may surface a prompt: "The LVMH decision recorded last month is due for review."

From a prior decision record — when a recorded decision reaches a defined review condition, Atlas may re-enter the Decision Workspace in review mode, presenting the original decision alongside current conditions.

User-initiated: the user may open the Decision Workspace directly from any Investment Workspace at any time, not only when Atlas has surfaced a trigger.

Entry carries context. When the Decision Workspace opens, it inherits the current conclusion, the originating Workspace, and the decision trigger. The user does not restate what they have already reasoned through.

⸻

Surface Structure

The Decision Workspace opens as a focused overlay above the originating Workspace, consistent with the Investment Workspace overlay pattern established in earlier Atlas Workspaces.

The originating Workspace — Investment or Portfolio — remains visible underneath. This preserves context without requiring the user to navigate back and forth.

The Decision Workspace has a fixed header, an internally scrolling body, and a fixed footer containing the primary action.

The header shows: the decision subject (investment name or portfolio-level scope), the decision type, and a close or return control.

The footer shows: the primary Record Decision action, its current state (available, or unavailable via `aria-disabled`, never native `disabled`), and a brief explanation when unavailable.

The body is the complete reasoning sequence.

⸻

Reading Flow

The Decision Workspace is a continuous narrative, not a form. The user moves progressively through:

Current understanding → Need for a decision → Decision formation → Supporting reasoning → Challenges → Consequences → Commitment → Future review

Each section flows into the next. The user should not feel that they are filling out separate fields. They should feel that the decision becomes progressively clearer as they move through the Workspace.

By the time the user reaches the Record Decision action, the decision should feel like the natural conclusion of the reasoning — earned, not abrupt.

⸻

Section Hierarchy

⸻

Section 1 — Current Conclusion

Position: Top of the body. Always visible. Never collapsible.

Purpose: Establish shared understanding before the decision begins. The user and Atlas must agree on what is currently believed before deciding what to do.

Content:
— The essential conclusion from the originating Workspace, stated in one to three sentences
— The confidence level of that conclusion (high / moderate / low / evidence incomplete)
— The source: Investment Workspace review or Portfolio Workspace review, with date
— A "View full analysis" link that surfaces the originating Workspace in context without navigating away

This section must not repeat the full analysis. It distills. One conclusion, its confidence, its source.

Interaction ownership: Atlas-generated. Read-only. Cannot be edited in the Decision Workspace.

Rationale: The user needs to see the conclusion before forming a decision. If the conclusion is wrong or incomplete, the user should return to the originating Workspace rather than form a decision against flawed premises. Making the conclusion visible and prominent enforces this.

⸻

Section 2 — Why a Decision Is Required

Position: Immediately below Current Conclusion. Always visible. Never collapsible.

Purpose: Answer the user's first question: Why am I here? The user should immediately understand the trigger without having to infer it.

Content:
— A single labeled trigger, drawn from the following taxonomy:

  Thesis change — a core investment assumption has materially changed
  Valuation change — the expected return has moved beyond an accepted threshold
  Portfolio conflict — the position has created an unintended concentration or dependency
  Opportunity cost — a competing use of capital has become clearly superior
  Scheduled review — a review condition set in a prior decision has been reached
  Invalidation signal — a named invalidation condition has been triggered
  New evidence — material new information has emerged that the prior decision did not reflect
  User-initiated — the user has opened the Decision Workspace without a system-generated trigger

— A brief one-sentence elaboration of the trigger. For example: "The core thesis assumption about Chinese luxury demand has been reclassified as Broken."

Interaction ownership: Atlas-generated. Read-only. The trigger label is set by Atlas. The elaboration is Atlas-generated but the user may add a note.

Rationale: Knowing why a decision is required is the second most important thing the user needs to understand. It prevents the user from treating all decisions as equivalent in urgency. It also prevents post-hoc rationalization by anchoring the stated reason in the system before the decision is formed.

⸻

Section 3 — Proposed Decision

Position: Below Why a Decision Is Required. Always visible. Never collapsible.

Purpose: Present the decision that Atlas believes follows from the reasoning — as a starting point, not a conclusion.

Content:
— Atlas's proposed decision, stated in one clear sentence
— The decision type label, drawn from the vocabulary established in UX-008:
  Investment-level: Initiate / Add / Maintain / Reduce / Exit / Avoid / Defer
  Portfolio-level: Reallocate / Reduce Concentration / Accept Concentration / Maintain Structure / Preserve Liquidity / Rebalance Conviction
  Review: Thesis Valid / Thesis Requires Revision / Evidence Insufficient / Postponed
— A clear visual distinction that marks this as Atlas's proposal, not the user's decision
— An editable field where the user states their own decision — initially populated with Atlas's proposal but fully modifiable
— The user's decision field is the central element of this section and must have the highest visual emphasis of any user-editable element in the Workspace

The edit field must feel like a deliberate authoring environment, not a form field. The user is stating a commitment, not completing a checkbox.

Interaction ownership: Proposed content is Atlas-generated. The user's decision field is fully user-editable. After recording, the field is locked and versioned.

Rationale: Atlas may propose, but the user decides. The section must make this distinction unmistakable. The proposal is a starting point. The user's edited or confirmed decision is the actual commitment. Having Atlas propose also accelerates the process — the user can confirm, modify, or replace rather than starting from a blank field.

⸻

Section 4 — Decision Rationale

Position: Below Proposed Decision. Expanded by default for major decisions. Collapsed by default for minor review confirmations.

Purpose: Capture the primary reason for the decision in the user's own terms, supported by the key conclusions and assumptions that justify it.

Content:
— Primary reason field: a free-form or semi-structured field where the user states the most important reason for the decision
— Atlas-generated supporting summary: the two to four key conclusions from the originating analysis most relevant to this decision, presented as a concise structured list
— Essential assumptions: the two to three assumptions that the decision currently depends on — Atlas-identified, user-confirmable
— Material risks: the one or two risks that most directly threaten the decision's validity

The rationale section should feel like authoring, not filling in fields. The primary reason field must feel like a first-person statement.

Interaction ownership: Primary reason is user-authored. Atlas-generated supporting summary is read-only. Assumptions and risks are Atlas-proposed and user-confirmable — the user may add, edit, or remove.

Rationale: This section creates the core intellectual record of the decision. The primary reason, stated in the user's own words, is the single most important element for preventing post-hoc rationalization. If the user cannot state a clear reason, the decision is not ready to record.

⸻

Section 5 — Supporting Factors

Position: Below Decision Rationale. Collapsed by default for minor decisions. Expanded by default for major reallocations and exits.

Purpose: Reinforce the user's confidence by surfacing the strongest evidence that the decision is well-founded.

Content:
— The strongest supporting evidence, drawn from the originating analysis — Atlas-generated, two to four items
— Assumptions that remain intact and have not deteriorated
— Portfolio alignment — whether the decision is consistent with the portfolio's established strategy and concentration limits
— Historical consistency — whether the proposed decision is consistent with prior decisions on this investment or similar situations

Each item should be brief — one or two lines. The section is not a detailed evidence review. It is a summary of what makes the decision reasonable.

Interaction ownership: Atlas-generated. Read-only. The user may add a note or flag an item as particularly important.

Rationale: Impulsive decisions are often made by ignoring what supports the current position. Forcing the user to see the supporting case before committing ensures that the decision is being made with full information, not only the information that supports the desired action.

⸻

Section 6 — Challenges

Position: Below Supporting Factors. Collapsed by default for maintenance and minor review decisions. Expanded by default for any decision involving allocation change.

Purpose: Surface the strongest counterarguments and unresolved questions. This is the section that creates deliberate friction where friction is most valuable.

Content:
— Unresolved questions: things that would ideally be known before making this decision but are currently uncertain
— Conflicting evidence: data or observations that point in a direction contrary to the proposed decision
— Uncertain assumptions: assumptions in the decision rationale that Atlas has low confidence in
— Contradictory signals: places where the current decision appears to contradict prior reasoning or stated portfolio strategy
— Missing information: evidence that was not available during the prior analysis but would materially affect the decision

Atlas may also surface behavioral context here, when appropriate:

— "This decision follows a 12% price decline in the past 30 days. The thesis has not changed. Confirm this is a thesis-driven decision."
— "This position has been held for over four years. Review whether attachment to the holding period is influencing the decision."

Behavioral context should appear only when it is specific and material. It must be presented calmly, without judgment.

The user may dismiss a challenge item by selecting "Acknowledged" — the item then appears with reduced emphasis, confirming the user saw it rather than hiding it from the record.

Interaction ownership: Atlas-generated. Challenges may be acknowledged but not deleted. The record must preserve that they were seen.

Rationale: This section is the most important mechanism for preventing impulsive decisions. It does not require the user to change the decision. It requires the user to see the counterarguments and confirm the decision anyway. That confirmation — combined with the preserved record — is the source of decision quality.

⸻

Section 7 — Opportunity Cost

Position: Below Challenges. Always visible for significant allocation decisions. Hidden for maintenance, minor review confirmations, and no-action decisions.

Purpose: Answer the question: Why this use of capital rather than the alternatives? This section ensures that every allocation decision is made with visible awareness of what it costs in terms of foregone alternatives.

Content:
— The decision subject's expected return or conviction summary
— One to three alternatives, each showing:
  — Name
  — Current Atlas conviction or expected return indicator
  — Relevant portfolio context (current allocation, available capacity, overlap with existing exposure)
  — One-line comparison: "Danaher currently offers a higher expected return at a lower current allocation."
— A conclusion line: the reason this decision is preferred over the alternatives, stated explicitly

For decisions that involve no allocation change (Maintain, No Action), this section may show "No capital is being reallocated — opportunity cost is the continued commitment of existing capital to this investment" as a brief statement, without the full alternative comparison.

For Defer decisions, this section should note that deferral also has an opportunity cost — capital remains committed during the deferral period.

Interaction ownership: Atlas-generated. Read-only. The user may add a note explaining why the stated alternatives were rejected.

Rationale: Opportunity cost is often the least visible element of an investment decision. Making it explicit — even briefly — prevents the user from evaluating a decision in isolation from the alternatives that capital could serve. Over time, this section also feeds the pattern recognition in Atlas Memory: does the user systematically underweight strong alternatives?

⸻

Section 8 — Portfolio Consequences

Position: Below Opportunity Cost. Collapsed by default for minor decisions. Expanded by default for decisions with meaningful allocation impact.

Purpose: Show only the portfolio-level consequences that are directly relevant to this decision. This section connects the individual decision to the portfolio as a system.

Content:
— Relevant consequences only, drawn from:
  — Position size change (before and after, as a percentage of portfolio)
  — Theme exposure change (if relevant — e.g., enterprise AI dependency changes)
  — Sector or geographic balance change
  — Hidden concentration change (does this increase or decrease an underlying shared dependency?)
  — Risk dependency change (does this reduce or increase exposure to a named portfolio-level driver?)
  — Liquidity impact (if relevant)
— Each item presented as a before/after pair or a directional indicator, not as a full portfolio dashboard
— A one-line summary: "This decision reduces LVMH from 7.1% to 4% and releases approximately 3% of capital without materially changing sector exposure."

This section must not reproduce the full Portfolio Workspace. It shows only what changes, and only what changes meaningfully.

Interaction ownership: Atlas-generated. Read-only.

Rationale: Individual investment decisions create portfolio-level effects that are easy to overlook in the moment. Surfacing the consequences within the Decision Workspace means the user does not have to switch contexts to understand them. It also prevents decisions that would create unintended concentrations or dependencies that would only be visible in the Portfolio Workspace later.

⸻

Section 9 — Assumptions, Monitoring and Invalidation

Position: Below Portfolio Consequences. Collapsed by default for minor review and maintenance decisions. Expanded by default for any decision involving allocation change, initiation, or exit.

Purpose: Preserve the conditions that make the decision reasonable, the signals Atlas will watch after recording, and the thresholds that would make the decision no longer valid.

This section contains three distinct and clearly labeled subsections:

Supporting Assumptions
What the decision currently relies upon — the conditions that must remain true for the decision to remain reasonable.
— Two to four items, Atlas-proposed from the originating analysis, user-confirmable
— Each assumption stated as a condition, not a prediction: "GCP margin expansion continues" rather than "GCP margins will expand."

Monitoring Conditions
What Atlas should watch after the decision is recorded — the signals that indicate whether the decision remains valid.
— Two to three items, Atlas-proposed, user-adjustable
— Each condition stated as a specific observable signal: "Next quarterly earnings for enterprise AI infrastructure spending" or "LVMH China revenue trend over two consecutive quarters."

Invalidation Conditions
What specific changes would make the original decision no longer reasonable — not arbitrary price movement, but thesis, evidence, valuation, or portfolio-level changes.
— Two to three items, Atlas-proposed, user-adjustable
— Each condition stated specifically: "If LVMH China revenue decline exceeds 20% in the following fiscal year" rather than "if the stock falls further."

The distinction between Monitoring and Invalidation must be clear. Monitoring is passive observation. Invalidation is the threshold that triggers re-entry into the Decision Workspace.

Interaction ownership: Atlas-proposed throughout. User may confirm, edit, add, or remove individual items. After recording, items are locked and versioned. Changes to monitoring or invalidation conditions after recording create a visible amendment in the decision history.

Rationale: This is the section that makes future decision reviews possible. Without defined invalidation conditions, Atlas cannot distinguish a decision that is still valid from one that has become obsolete. Without monitoring conditions, Atlas cannot proactively surface the decision for review when circumstances change.

⸻

Section 10 — Implementation Plan

Position: Below Assumptions, Monitoring and Invalidation. Visible for all decisions. Complexity adapts to decision type.

Purpose: Record what action is required, if any, and on what timeline. Establish clearly that the decision and its implementation are separate — Atlas records intent, not execution.

Content:
— Implementation type, drawn from:
  Immediate — act as soon as possible
  Gradual — execute in portions over a defined period
  Conditional — act only if a named condition is met
  Deferred — implementation postponed until a future trigger
  No action — no transaction required; the decision is to maintain or record a review outcome

— For Immediate and Gradual:
  — Target allocation or position change, stated as a range rather than a precise number where appropriate
  — Time frame or approximate sequence

— For Conditional:
  — The named condition that must be met before acting
  — What the action will be once the condition is met

— For Deferred:
  — The event or condition that will trigger the implementation decision
  — Whether a partial action should be taken immediately while the full decision is deferred

— For No Action:
  — A brief statement confirming that the decision to take no action was deliberate, not accidental

Implementation status indicator: after the decision is recorded, the implementation status becomes trackable (Pending / In Progress / Completed / Conditional / Cancelled). Status updates do not require re-entering the full Decision Workspace — they can be updated from the decision record directly.

Interaction ownership: Collaborative. Atlas may propose an implementation type based on the decision, but the user sets or confirms all implementation details. After recording, status updates are user-driven.

Rationale: Separating decision from implementation prevents two failure modes: (1) treating every decision as requiring immediate execution, and (2) recording a decision and never implementing it without any tracking of that gap. The Decision Workspace records the intention. Implementation is the user's responsibility, tracked as a separate state.

⸻

Section 11 — Review Plan

Position: Below Implementation Plan. Visible for all decisions. Complexity adapts.

Purpose: Establish when and under what conditions Atlas should re-surface this decision for review.

Content:
— Primary review trigger, one of:
  — Time-based: "Review after Q3 earnings, expected September 2026"
  — Condition-based: "Review if valuation rises above 35x FCF"
  — Event-based: "Review following the next LVMH China revenue announcement"
  — Invalidation-triggered: automatically surfaced when an invalidation condition from Section 9 is reached

— Expected review date (optional, if the trigger has a natural timeline)
— Review depth: a brief indication of what the review should examine. For example: "Confirm whether China revenue trend has stabilized."

For maintenance and no-action decisions, a simpler prompt: "Next review: scheduled portfolio review or earlier if thesis changes."

Interaction ownership: Atlas may propose a review trigger based on the monitoring conditions in Section 9. The user confirms or adjusts. After recording, the review plan is locked and creates a scheduled item in Atlas Memory.

Rationale: A decision without a review plan is incomplete. It assumes the decision remains valid indefinitely. The review plan is the mechanism by which Atlas Memory generates future engagement — not as a general alert, but as a precise return to this specific decision in this specific context.

⸻

Section 12 — Final Decision Card

Position: Below Review Plan. Always visible. Never collapsible. The most prominent section in the lower half of the Workspace.

Purpose: Converge everything above into a single, explicit, readable decision statement. This is the element that the user and Atlas will refer to when this decision is reviewed months or years later.

Content — assembled from the sections above:

Decision
The exact decision as stated by the user in Section 3 — unchanged.

Reason
The primary reason from Section 4 — the user's own words.

Confidence
The confidence level: High / Moderate / Low / Evidence Incomplete / Intentionally Deferred.

Portfolio impact
A single-line summary of the most relevant portfolio consequence from Section 8.

Implementation
The implementation type and intent from Section 10.

Review condition
The primary review trigger from Section 11.

This section does not contain any editable fields. It is a read-back of the decisions made above. If any element is wrong, the user scrolls up to the relevant section and corrects it there. The Final Decision Card updates in real time as the user edits above.

Interaction ownership: Atlas-assembled from user inputs. Read-only. Locked on recording.

Rationale: Seeing the full decision assembled in one place, before recording, serves two purposes. First, it allows the user to confirm that the decision is coherent as a whole rather than reviewing each section in isolation. Second, it establishes the canonical decision record — the format in which the decision will be preserved in Atlas Memory.

⸻

Section 13 — Record Decision

Position: Bottom of the Workspace, with the primary action in the fixed footer and supporting context immediately above.

Purpose: Complete the Decision Workspace and preserve the decision in Atlas Memory.

Content:

Available state (universal minimum and any decision-type-conditional fields complete — see "Preventing Incomplete Records" below; unacknowledged Challenges never block this state):
— Primary action: Record Decision — full emphasis, clearly the terminal action
— Secondary actions: Save as Draft / Return to Workspace
— Confirmation context, one line: "This decision will be preserved in Atlas Memory and linked to your LVMH Investment Workspace."

Unavailable state (universal minimum or a required conditional field incomplete): *(Corrected per ADR-002/C-04: this state was previously also triggered by "critical challenges unacknowledged" — unacknowledged Challenges never make this action unavailable; see "Preventing Incomplete Records" below.)*
— Primary action: Record Decision — carries `aria-disabled="true"` (never the native HTML `disabled` attribute), remains focusable and in the natural tab order, reduced-emphasis visual treatment, cursor not-allowed. *(Corrected per ADR-002/C-06: this state was previously described only as "visually disabled," which could be read as native `disabled` semantics that would remove the control from the tab order.)*
— Explanation, one line, adjacent to the action, and also exposed via `aria-describedby`: states specifically what must be completed. Not a generic error. For example: "State a primary reason for this decision before recording." Activating the action while unavailable does not record the decision — it moves focus to the first unmet required field and re-announces the explanation there.

The Record Decision action must feel meaningful without being dramatic. It is a record-keeping action, not a celebration trigger. No animation, no confetti, no congratulatory message. A quiet confirmation: "Decision recorded — [date], [investment name]."

After recording:
— A brief post-decision state appears: the Final Decision Card becomes the primary visible element, surrounded by space
— Three contextual next steps are offered:
  — Return to [Investment / Portfolio] Workspace
  — View decision in Atlas Memory
  — Open [related investment] Workspace (if opportunity cost alternatives were surfaced in Section 7)

Secondary actions:

Save as Draft — preserves the Workspace in its current state without committing to the record. Drafts are surfaced in the Daily Briefing as unresolved decisions. Available at any time from the footer.

Return to Workspace — closes the Decision Workspace and returns to the originating Workspace without recording or saving. The user is prompted once: "Exit without saving?" No data is lost unless the user confirms exit.

Interaction ownership: All actions are user-driven. The Record Decision action cannot be triggered by Atlas.

⸻

Collapse Strategy

The Decision Workspace uses progressive disclosure to adapt its depth to the significance of the decision.

Always expanded, never collapsible:
— Section 1 — Current Conclusion
— Section 2 — Why a Decision Is Required
— Section 3 — Proposed Decision
— Section 12 — Final Decision Card

Expanded by default for major allocation decisions (Add, Reduce, Exit, Initiate, Reallocate):
— Section 4 — Decision Rationale
— Section 5 — Supporting Factors
— Section 6 — Challenges
— Section 7 — Opportunity Cost
— Section 8 — Portfolio Consequences
— Section 9 — Assumptions, Monitoring and Invalidation
— Section 10 — Implementation Plan
— Section 11 — Review Plan

Collapsed by default for minor decisions (Maintain, No Action, Scheduled Review, Defer):
— Section 5 — Supporting Factors
— Section 6 — Challenges
— Section 7 — Opportunity Cost (hidden entirely for no-action decisions)
— Section 8 — Portfolio Consequences
— Section 9 — Assumptions, Monitoring and Invalidation

Sections 4, 10, 11 remain expanded in all decision types — rationale, implementation, and review are always required, even if brief.

After recording:
— All sections collapse to their summary states
— Section 12 — Final Decision Card expands to full width and becomes the primary visible content
— The Workspace enters read-only mode
— A "View full decision record" control expands all sections for review

⸻

Reading Hierarchy

Three levels of visual emphasis govern the eye's natural path through the Workspace.

Highest emphasis — the user's eye should pause here:
— Section 1: the conclusion statement (the most prominent text element in the Workspace header area)
— Section 3: the user's decision field (the most prominent interactive element in the body)
— Section 7: the opportunity cost conclusion line
— Section 12: the full Final Decision Card

Medium emphasis — the reasoning scaffold:
— Section 2: the trigger label and elaboration
— Section 4: the primary reason field and key conclusions
— Section 6: challenge items and behavioral context
— Section 9: invalidation conditions
— Section 10: implementation type and intent

Low emphasis — supporting and contextual:
— Section 5: supporting evidence items
— Section 8: portfolio consequence detail
— Section 11: review plan
— Source links, acknowledgment controls, secondary actions

⸻

Adaptive Behaviour by Decision Type

Maintain / No Action
Sections 5, 7, 8 collapsed. Section 9 simplified: one assumption and one review trigger. Section 10 shows "No action" confirmation only. Overall depth: minimal. Duration: under two minutes.

Minor Addition or Reduction (under 2% allocation change)
Sections 5, 8 collapsed. Section 6 present. Section 7 brief — one alternative. Section 9 standard. Duration: four to six minutes.

Major Addition, Reduction, or Initiation (over 2% allocation change)
All sections expanded. Section 7 shows two to three alternatives. Section 8 shows full consequence summary. Section 9 shows all three subsections fully. Duration: eight to fifteen minutes.

Full Exit
All sections expanded. Section 6 — Challenges — given particular emphasis. Additional prompt from Atlas: "This is a full exit. Confirm that the thesis has changed or the opportunity cost is clearly superior." Section 9 includes a specific question: "What would cause you to consider re-entering this investment?" Duration: ten to twenty minutes.

Portfolio-Level Reallocation
Sections 1 and 2 draw from the Portfolio Workspace rather than Investment Workspace. Section 8 — Portfolio Consequences — becomes the primary analytical section. Section 7 shows capital competition across multiple positions. All other sections adapt to the portfolio scope. Duration: fifteen to thirty minutes.

Deferred Decision
Section 3 shows decision type as Defer with the deferral condition stated. Sections 5, 6, 7, 8 collapsed. Section 9 reduced to monitoring conditions only — invalidation is replaced by the trigger that will end the deferral. Section 10 shows "Action pending condition." Section 12 reflects the deferral explicitly. Duration: under five minutes.

⸻

Interaction Ownership Table

Section 1 — Current Conclusion
Atlas-generated. Read-only. User may link to full analysis.

Section 2 — Why a Decision Is Required
Atlas-generated. Read-only. User may add a note.

Section 3 — Proposed Decision
Proposed by Atlas. Decision field is fully user-editable. Locked after recording.

Section 4 — Decision Rationale
Primary reason is user-authored (required). Supporting conclusions and assumptions are Atlas-proposed and user-confirmable. Locked after recording.

Section 5 — Supporting Factors
Atlas-generated. Read-only. User may flag items as particularly important.

Section 6 — Challenges
Atlas-generated. Challenges may be acknowledged but not deleted. Acknowledgment status preserved in record.

Section 7 — Opportunity Cost
Atlas-generated. Read-only. User may add a note explaining preference over stated alternatives.

Section 8 — Portfolio Consequences
Atlas-generated. Read-only.

Section 9 — Assumptions, Monitoring and Invalidation
Atlas-proposed. User-confirmable and editable. User may add items. Locked after recording; amendments versioned.

Section 10 — Implementation Plan
Collaborative. Atlas proposes type; user sets details. Implementation status updated by user post-recording.

Section 11 — Review Plan
Atlas may propose based on monitoring conditions. User confirms or adjusts. Locked after recording.

Section 12 — Final Decision Card
Atlas-assembled from user inputs. Read-only. Updates in real time as user edits other sections.

Section 13 — Record Decision
User-driven only. Record action cannot be triggered by Atlas.

⸻

Navigation Behaviour

Entering the Decision Workspace: the overlay opens with a transition that preserves the originating Workspace behind it. The user can see that context has been preserved without navigating back.

Moving through sections: continuous scrolling. No next/previous step controls. No wizard navigation. The sections flow as a document, not a guided form sequence.

Returning to the originating Workspace: the close control or "Return to Workspace" action dismisses the overlay and returns the user to the same scroll position and expanded state in the originating Workspace.

Opening the Decision Workspace from a prior decision for review: the Workspace opens in review mode. The original decision is displayed read-only on the left (or in the header region on smaller layouts). The current analysis is surfaced in the same section structure, allowing side-by-side comparison. The user completes the review by recording a new decision: Thesis Valid / Revised / Superseded.

Escape key: dismisses the Workspace with a single "Exit without saving?" prompt if a draft exists. If no draft exists, dismisses immediately.

⸻

Recording Behaviour

When the user selects Record Decision:

— All entered data is committed to Atlas Memory as a complete, immutable decision record
— The record is linked to the originating Investment Workspace or Portfolio Workspace
— Monitoring conditions from Section 9 are registered as active Atlas observations
— Review conditions from Section 11 are scheduled
— The decision appears in the Daily Briefing history
— The implementation status becomes trackable from the decision record
— A quiet confirmation is displayed: "Decision recorded — [date] · [investment name or portfolio scope]"

The Workspace then transitions to the post-decision state: Final Decision Card becomes the primary visible element with clear space around it. Three contextual next steps are offered as described in Section 13.

Nothing is sent, executed, or transmitted to any brokerage or third-party system.

⸻

Preventing Incomplete Records

*(Corrected per ADR-002/C-04: this section previously stated a flat four-condition rule — decision stated, primary reason authored, all unacknowledged critical Challenges acknowledged, and an implementation type selected — with Challenges acknowledgment treated as hard-blocking. The corrected model below replaces it: a universal minimum, decision-type-conditional requirements, and Challenges acknowledgment as soft friction that never blocks recording.)*

**Universal minimum, required for every decision type, no exceptions:**
— The user has stated a decision in Section 3
— The user has authored a primary reason in Section 4

**Conditionally required, by decision type:**
— An implementation type has been selected in Section 10 — required for decisions that entail an action; not required for No Action or Deferred decisions, where selecting "No Action" or "Deferred" itself satisfies this requirement
— A Review Condition has been set in Section 11 (Review Plan) — required unless explicitly overridden with a logged reason (a full, final exit with no remaining stake to monitor)
— Portfolio Consequences (Section 8) acknowledgment — required for portfolio-level decisions; not required for single-position decisions

**Never blocks recording:** unacknowledged Challenges in Section 6, at any severity. A Blocking-severity Challenge requires the user to explicitly acknowledge it — "I have seen and considered this," never "I agree with this" — before recording, but this acknowledgment is soft friction, not a hard block; Atlas never prevents recording because the user's own judgment differs from a surfaced concern.

The explanation adjacent to the unavailable action names the specific incomplete item. It is never a generic error message.

The user may save a draft at any time without meeting these requirements. Drafts do not enter Atlas Memory.

⸻

Post-Decision State

After recording:

The Workspace transitions to a calm confirmation state. The Final Decision Card is the primary visible element. The decision is now part of Atlas Memory.

The post-decision state communicates:

"This decision is now part of your investment history. Atlas will monitor the conditions you defined and surface this decision for review when appropriate."

This is stated once, briefly, in a single line beneath the Final Decision Card. No repeated affirmation. No celebratory language. The meaning of the moment is in the decision itself, not in any system response to it.

Three contextual actions are available:

Return to [originating Workspace] — the most prominent of the three
View decision in Atlas Memory — opens the stored record
Open [next related Workspace] — present when a clear next step exists (e.g., "Open Danaher Workspace to begin capital comparison")

⸻

Final Screen Structure

The complete ordered hierarchy:

Fixed Header
— Decision subject (investment name or portfolio scope)
— Decision type label
— Return / close control

Body (internally scrolling)

1. Current Conclusion
   — Conclusion statement
   — Confidence level
   — Source and date
   — Link to full analysis

2. Why a Decision Is Required
   — Trigger label
   — Trigger elaboration
   — Optional user note

3. Proposed Decision
   — Atlas's proposed decision (labeled as proposal)
   — User's decision field (primary interactive element)
   — Decision type selector

4. Decision Rationale
   — Primary reason (user-authored)
   — Key supporting conclusions (Atlas-generated)
   — Essential assumptions (Atlas-proposed, user-confirmable)
   — Material risks (Atlas-proposed, user-confirmable)

5. Supporting Factors
   — Supporting evidence items
   — Intact assumptions
   — Portfolio alignment
   — Historical consistency

6. Challenges
   — Unresolved questions
   — Conflicting evidence
   — Uncertain assumptions
   — Behavioral context (when relevant)
   — Acknowledgment controls

7. Opportunity Cost
   — Decision subject summary
   — Alternative comparisons
   — Conclusion line

8. Portfolio Consequences
   — Relevant consequence items (before/after)
   — Single-line summary

9. Assumptions, Monitoring and Invalidation
   — Supporting assumptions
   — Monitoring conditions
   — Invalidation conditions

10. Implementation Plan
    — Implementation type
    — Implementation details
    — Timeline or condition

11. Review Plan
    — Primary review trigger
    — Expected date (if applicable)
    — Review depth summary

12. Final Decision Card
    — Decision
    — Reason
    — Confidence
    — Portfolio impact
    — Implementation
    — Review condition

Fixed Footer
— Record Decision (primary action, available or unavailable via `aria-disabled="true"` — never native `disabled` — remaining focusable; unavailable activation navigates to the first unmet required field)
— Save as Draft (secondary)
— Return to Workspace (secondary)

Post-Decision State (replaces body after recording)
— Final Decision Card (full emphasis)
— Confirmation line
— Three contextual next steps

⸻

What UX-009 Establishes

The following screen-level decisions are now fixed:

— Entry points: the Decision Workspace is entered from the Investment Workspace, Portfolio Workspace, Daily Briefing, or directly from a prior decision record. It inherits context from the originating surface.

— Surface structure: a focused overlay above the originating Workspace, consistent with the existing Atlas overlay pattern, with a fixed header, fixed footer, and internally scrolling body.

— Section count and order: thirteen sections in a fixed sequence, from Current Conclusion through Record Decision.

— Reading flow: continuous narrative scroll — not a wizard, not a tabbed form, not a multi-page flow.

— Which sections are always visible: Sections 1, 2, 3, and 12 are never collapsible.

— Collapse strategy: sections expand or collapse based on decision type — major allocation decisions expand all sections; maintenance and review decisions collapse the analytical depth sections.

— Adaptive depth by decision type: the seven decision types — Maintain, Minor Add/Reduce, Major Add/Reduce/Initiate, Full Exit, Portfolio Reallocation, Deferred, and No Action — each have a defined expansion pattern and expected duration.

— Interaction ownership: each section's content source (Atlas-generated, user-authored, collaborative) and edit rights (read-only, user-editable, locked after recording) are fully specified.

— The distinction between Atlas's proposed decision and the user's decision: Atlas proposes; the user decides. The proposal is clearly labeled as Atlas's. The user's decision field is the primary interactive element of the Workspace.

— Reading hierarchy: the four high-emphasis moments (Current Conclusion, User's Decision Field, Opportunity Cost conclusion, Final Decision Card) and the two lower tiers of emphasis are defined.

— Navigation behaviour: continuous scroll, context-preserving overlay, escape-key dismissal, review-mode entry from prior decision records.

— What must be complete before recording: decision statement and primary reason as the universal minimum; implementation type, review trigger, and Portfolio Consequences acknowledgment as conditional requirements by decision type; Challenges acknowledgment as soft friction that never blocks recording. *(Corrected per ADR-002/C-04; this line previously listed a flat four-condition rule including hard-blocking Challenges acknowledgment.)*

— Recording behaviour: immutable commitment to Atlas Memory, linked to originating Workspaces, monitoring and review conditions scheduled, implementation status trackable, no brokerage action.

— Post-decision state: calm confirmation, Final Decision Card as primary element, three contextual next steps.

— Secondary actions: Save as Draft preserves without committing; Return to Workspace dismisses with a single prompt.

⸻

What UX-009 Defers to UX-009A

The following are intentionally deferred to the wireframe specification:

— Wireframes and layout diagrams
— Column structure, panel proportions, and responsive breakpoints
— Component sizing and density
— Spacing values, padding, and margin systems
— Visual styling — typography, color, elevation, border treatment
— Exact field dimensions and input affordances
— The visual form of Atlas's proposal label
— How the user's decision field is typographically distinguished from form inputs
— The visual treatment of the disabled Record Decision state
— Animation and transition behavior
— Microinteraction design — acknowledgment controls, confidence selectors, real-time Summary updates
— Mobile and tablet behavior
— The visual structure of the review-mode overlay (original decision alongside current analysis)
— How behavioral context items are visually distinguished from analytical challenge items
— The exact visual form of the post-decision confirmation state

Do not produce UX-009A yet.

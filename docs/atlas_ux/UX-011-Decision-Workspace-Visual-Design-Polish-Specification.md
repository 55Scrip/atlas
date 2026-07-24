UX-011 — Decision Workspace Visual Design & Polish Specification

Status: Visual Design Specification Complete
Owner: Atlas Product
Governs: Decision Workspace — visual philosophy, hierarchy, typography, spacing, color semantics, card system, motion, accessibility
Depends on: UX-008, UX-009, UX-009A, UX-010
Defers to: UX-012 — Atlas Design System & Workspace Consistency Specification

**Correction Notice (Phase 2A, governed by ADR-002 — 2026-07-24):** This document's original identity (Status, Owner, Governs, Depends on, Defers to, as above) and original date are preserved unchanged. One semantic area was corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan:
- **C-03 (Decision Workspace Sequence):** the superseded terms "Final Decision Summary" (including "Final Decision Summary card") and "What Supports This Decision" were corrected to "Final Decision Card" and "Supporting Factors" throughout — this document previously used the superseded names in its Section 12 and Section 5 references, component descriptions, and narrative passages, including its own Section 18 heading, which already read "Final Decision Card" while the body beneath it read "Final Decision Summary." No section order, count, or unaffected visual-design content (typography, spacing, color, motion, layout values) was changed.

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, above. All content outside this one terminology correction is unchanged.

⸻

Visual Design Philosophy

The Decision Workspace is a place for careful thinking. Its visual language must communicate this without asserting it.

The experience should feel closer to a considered editorial publication than to enterprise software. The user is reasoning through a significant decision — the visual environment should treat that with appropriate gravity and restraint. Nothing should compete with the user's thinking. The visual language should disappear behind the reasoning.

The Workspace achieves this through four foundational commitments:

Restraint over decoration. Every visual element must earn its presence. If removing something does not cause confusion, remove it. The instinct to add — more borders, more labels, more color — must be consistently resisted. What remains should be purposeful.

Structure over borders. Spatial organization communicates hierarchy more elegantly than drawn boundaries. Consistent left alignment, generous spacing between sections, and deliberate reading width create order without enclosing every element in a box.

Typography over color. The visual hierarchy is primarily typographic — weight, size, and spatial rhythm guide the eye. Color confirms and reinforces semantic meaning, but it is never the primary signal. A user with no color perception should experience the same hierarchy as any other user.

Permanence over novelty. The visual language should be timeless. It should feel appropriate not only during the moment of decision but when the user returns to the same decision record years later. Nothing should feel like a product feature. Everything should feel like a document.

The Workspace must not feel like any of these: a high-frequency trading terminal, a consumer fintech app, a sales dashboard, an analytics platform, a gaming interface, a social product, or an AI chat window. These visual references are all associated with either speed, entertainment, or transactional completion — none of which belong in the Decision Workspace.

⸻

1. Visual Hierarchy

The Workspace operates on three levels of visual emphasis. Every element belongs to exactly one level. No element should claim higher emphasis than its level permits.

Highest emphasis — the eye pauses here without instruction:

— Current Conclusion (Section 1): the conclusion statement is the largest, most prominent text in the upper body. It sets the intellectual context for everything that follows.
— User Decision Field (Section 3): the most prominent user-editable element in the Workspace. When the user is in this field, it should feel like the center of the document.
— Final Decision Card (Section 12): as the document approaches completion, this card becomes the visual center of gravity in the lower body.
— Record Decision action: the terminal action of the Workspace. Its visual weight communicates finality without urgency.

Medium emphasis — the reasoning scaffold, read attentively but not involuntarily:

— Why a Decision Is Required (Section 2): the trigger label and elaboration are medium-emphasis — clearly readable but not as large as the conclusion.
— Opportunity Cost conclusion line (Section 7): the comparative reasoning line that synthesizes the alternatives.
— Portfolio Consequences summary line (Section 8): the single-sentence synthesis.
— Challenge items (Section 6): each challenge statement receives medium emphasis — the user must read them without being commanded to.
— Invalidation conditions (Section 9): these are the durable conditions that govern the decision's future — they deserve medium emphasis in their section.

Lower emphasis — supporting and contextual, read when relevant:

— Supporting evidence items (Section 5)
— Individual assumption rows (Section 9)
— Monitoring conditions (Section 9)
— Implementation detail fields (Section 10)
— Review plan detail (Section 11)
— Historical references and source citations
— Metadata: dates, sources, version indicators
— Behavioral context items (Section 6)
— Section labels (the small uppercase labels that name each section)

The hierarchy must be distinguishable without relying on color. A grayscale rendering of the Workspace must show the same three-tier structure as a full-color rendering.

⸻

2. Typography System

The typography system governs reading rhythm, hierarchy, and editorial character. The following defines each conceptual role — the specific font family, sizes, and weights are specified in UX-012's design token system. UX-011 defines the roles and their relationships.

Typography roles and their relationships:

Workspace subject line (Fixed Header — decision name + type):
The investment name is the largest text in the fixed header. The decision type label is a secondary line — smaller, lighter weight. Together they orient the user without demanding attention. The header typography should feel more like a document title line than a navigation bar.

Section labels:
Small, wide-spaced uppercase. These are the lowest-emphasis typographic element in the Workspace. They identify the section but do not anchor the reading experience — the content beneath them does that. Their restrained size and letter-spacing signal "document structure" rather than "software feature."

Conclusion statement (Section 1):
The most prominent prose in the Workspace. It is read first and remembered longest. It uses the largest body text size in the Workspace — larger than any other non-interactive text element. Its weight should be moderate rather than heavy: the emphasis comes from size and placement, not from thickness. The prose should feel authoritative but not formal.

Decision statement (Section 3, user decision field):
The primary authored text in the Workspace. When the user writes in it, the typography must feel like writing in a document — not filling a form. The field's inactive state shows the text at the same scale as the conclusion statement but in a subtly distinct weight or style that signals editability without resembling a conventional input. When focused, the field is rendered in full editorial weight.

Atlas proposal text (Section 3):
Clearly subordinate to the user decision field. The same general type family but rendered at a slightly smaller size and in a reduced weight. The "Atlas suggests" label above it is in section-label scale — small and uppercase. The spatial distance between the Atlas proposal block and the user decision field reinforces their different natures.

Primary reason field (Section 4):
The user's authored explanation. Typographically similar to the decision statement — it is user-owned, important, and should feel like prose writing. When populated, it reads as natural first-person reasoning. Its scale is slightly smaller than the decision statement — it is important but not the singular focal point.

Supporting explanations (Atlas-generated content throughout):
The majority of Atlas-generated text — conclusions, challenge items, consequence statements — uses a consistent body text scale below the decision statement. It reads comfortably at moderate line length. Its weight is slightly lighter than user-authored content — a consistent, subtle distinction that reinforces authorship without relying on color.

Metadata (dates, source references, confidence labels, status indicators):
The smallest text in the Workspace. Wide letter-spacing, moderate weight, optionally in a monospaced or narrow variant that distinguishes it from body text. Metadata should be clearly readable but should not draw the eye unless the user deliberately looks for it.

Confidence label:
Typographically, the confidence label sits between metadata and body text. It is a qualitative state description — larger and more prominent than a timestamp but smaller than a reasoning statement. The label itself is less important than its explanation, so when the confidence panel is open, the label reduces and the explanation text takes over.

Long-form reasoning (primary reason, user decision, detailed assumption explanations):
Long-form text uses generous line height — approximately 1.65–1.7 relative to font size — and a comfortable line length of approximately 65–70 characters. This is editorial line length, not data-table line length. The reading experience for long-form content must be pleasant. The user is expected to read carefully, not scan.

⸻

3. Reading Rhythm

The Workspace reads as a single continuous document. Visual rhythm guides the user through it without interrupting the reasoning thread.

Section separation creates pace. The space between sections is the primary pacing mechanism — generous enough that the user feels they have arrived somewhere new, not so large that the document feels disconnected. The space between sections is larger than the space within sections. The space within sections is larger than the space between individual rows.

The four scroll-pause moments (Section 1, Section 3 decision field, Section 7 opportunity cost conclusion, Section 12 Final Decision Card) are visually distinct from their surroundings. Each one creates a slight visual weight that causes the eye to slow — this is achieved through larger type size, greater surrounding space, or a contained surface — not through color, animation, or graphic treatment.

No section visually interrupts the narrative. Section dividers, where used, are hairline — thin enough to mark a boundary without asserting one. The goal is that the sections feel like paragraphs in a long document, not like panels in an application.

Section labels (the small uppercase identifiers) appear consistently at the same vertical position relative to their first content element. Their spatial rhythm is uniform. The user should feel the section label as punctuation, not as a header.

⸻

4. Card System

The Workspace uses three levels of visual containment. The choice of containment for each section is a design decision, not a default.

Strong containers — a surface with clear boundaries, used for the most significant moments:

Current Conclusion card (Section 1): the opening statement of the Workspace deserves a clearly defined surface. It is the foundational context for every section that follows. The card should feel settled and authoritative — like the opening paragraph of a considered document. Subtle elevation or a distinct background surface achieves this. No decorative border treatment.

Final Decision Card (Section 12): this is the permanent record — the element that will be referenced in Atlas Memory, in future reviews, and in daily briefings. It should feel more substantial than any other element in the body. A clearly defined surface, slightly elevated from the body background, with generous internal spacing. The card should communicate permanence.

Atlas proposal block (Section 3): a subtly contained surface that distinguishes the Atlas proposal from the surrounding body. Smaller than the above two — contained enough to be clearly set apart, not so prominent that it competes with the user decision field above it.

Subtle containers — a light background or a single-side border rule, used for secondary groupings:

Opportunity cost alternative rows (Section 7): each alternative benefits from a subtle surface distinction that helps the user understand the comparative structure. Not a full card — a background treatment that reads as a row.

Challenge items (Section 6): a subtle left-border rule or a minimal background treatment that groups each challenge item and its acknowledgment control into a legible unit. Not boxed — but readable as a discrete item.

Assumption rows (Section 9): similarly — a subtle left-border rule that groups each assumption with its status indicator and controls.

Dividers only — a hairline rule, used where content needs separation without containment:

Between section groups within Section 9 (Assumptions / Monitoring / Invalidation): hairline rules separate the three subsections without the overhead of full containers.

Within Section 5 (Supporting Factors): the four groups (evidence, intact assumptions, portfolio alignment, historical consistency) are separated by hairlines.

Within Section 8 (Portfolio Consequences): consequence rows separated by hairlines.

Open layout — no visual separation, content floats in the body space:

Section labels and their immediate content: the section label is typographically distinct — no container needed.
Section 2 (Why a Decision Is Required): the trigger label and elaboration float in the body space. Their visual weight comes from typography and the section label, not from containment.
Section 10 (Implementation Plan): the implementation type selector floats in the body. The conditional fields it reveals use field-level visual treatment, not containers.
Section 11 (Review Plan): similarly open.

The card system should not result in a Workspace that feels like a series of boxes. The strong containers are used sparingly — two to three times in the full Workspace, for the moments that genuinely deserve them.

⸻

5. Spacing System

Spacing is the primary tool for communicating hierarchy. It should be applied with discipline.

Inter-section spacing (the gap between one section and the next):
The largest spacing unit in the Workspace. It signals a significant shift in topic. This space must be large enough that the user feels they have moved to a new conceptual territory. Approximately three to four times the line height of body text.

Intra-section spacing (between content groups within a section):
Approximately half of inter-section spacing. Sufficient to distinguish groups without suggesting a complete break in topic.

Row spacing (between individual items in a list or table):
Approximately one to one-and-a-half line heights. Enough to make each row individually readable without padding the list unnecessarily.

Label-to-content spacing (between a section label and its first content element):
Small — approximately half a line height. The label is punctuation, not a heading. It does not need substantial breathing room of its own.

Paragraph spacing within long-form fields:
Standard editorial paragraph spacing — approximately the same as the line height. The user's authored text reads as flowing prose.

The Workspace must never feel dense. If any part of the Workspace feels compressed, the correct response is to remove content before reducing spacing. Density is a product failure in this context.

The maximum reading width applies to all content in the scrolling body. Content does not span the full overlay width. A comfortable editorial line length — approximately 65–70 characters for prose, up to 90 for structured data rows — defines the content container. This container is centered within the body. The surrounding space on either side reinforces the document-like character.

⸻

6. Color Semantics

The Decision Workspace uses color sparingly. Color reinforces meaning — it never creates it. Every semantic state must be communicated through text, structure, or iconography first. Color is the confirmation, not the signal.

The Workspace operates on a warm dark editorial background consistent with the Atlas design language established across the Dashboard, Investment Workspace, and Portfolio Workspace. The following semantic colors are defined at the conceptual level:

Primary surface: the overlay background — the base on which all content rests. Warm dark.

Elevated surface: used for strong containers (Current Conclusion card, Final Decision Card). Slightly lighter than the primary surface. Subtle, not dramatic.

Panel surface: used for the Atlas proposal block and subtle row backgrounds. Between primary and elevated.

Text primary: the highest-emphasis text — conclusion statements, decision statements, primary user-authored content. Near-white, slightly warm.

Text secondary: Atlas-generated body text, supporting explanations. Moderately warm gray — clearly readable but visually subordinate to primary text.

Text tertiary: section labels, metadata, timestamps, status indicators. Quiet warm gray. Clearly readable at close range; recedes at normal reading distance.

Semantic accents:

Amber (restrained): used for active review states, pending decisions, monitoring indicators that require attention. Not used for decorative purposes. Restrained amber — not bright orange. Applied to the trigger label in Section 2 when the trigger is a thesis change or invalidation signal. Applied to assumption status "Under Review."

Green (restrained): used for intact states, high-confidence indicators, resolved assumptions, and "Thesis Valid" review outcomes. Not used for completion celebration. Applied to assumption status "Holding."

Red (restrained, rare): used for genuinely broken or deteriorated states. Not for warnings. Applied to assumption status "Broken." Applied to challenge items classified as "Consider addressing before recording." Not applied broadly.

Blue (restrained): used for Atlas-sourced indicators — the Atlas badge, the "Atlas suggests" label, links that navigate to Atlas-generated analysis. Signals that something originates from Atlas without claiming more prominence than it deserves.

Muted (dim): used for read-only states, historical content, locked fields, and the disabled Record Decision button. Clearly indicates unavailability without harshness.

Color must not be the only indicator of any state. Every colored semantic state must also have a textual label, a typographic distinction, or a structural indicator that communicates the same meaning.

⸻

7. Authorship Visual Model

Distinguishing Atlas-generated content from user-authored content is one of the most important visual challenges in the Workspace. The distinction must be clear, consistent, and never reliant on color alone.

The authorship model uses four layers of distinction, applied consistently across all content:

Layer 1 — Label:
All Atlas-generated content has a small label identifying its source. "ATLAS CONCLUSION" / "ATLAS SUGGESTS" / "ATLAS ANALYSIS." This label uses section-label typography — small, uppercase, spaced. It appears above the content, not inline.
User-authored content has no source label — its absence is itself the signal. The user does not need to be reminded that their own words are theirs.

Layer 2 — Typography:
Atlas-generated body text (supporting conclusions, challenge items, consequence statements) uses a slightly lighter weight than user-authored prose. The weight difference is deliberate but subtle — a trained eye would identify it; a casual reader would feel it as a slightly different authority without knowing why.
User-authored text (primary reason, decision statement) uses the primary text weight — the weight the eye associates with the most important content.

Layer 3 — Layout position:
Atlas-generated content consistently appears before user-authored content within each section. The Atlas proposal (Section 3) appears above the user decision field. Atlas-generated supporting conclusions (Section 4) appear below the user's primary reason. This consistent layout rule means the user always knows where to expect each voice.

Layer 4 — Surface (for Atlas suggestions only):
When Atlas presents a suggestion (as distinct from settled Atlas-generated content), the suggestion appears on a slightly distinct surface — a subtle background or a contained region that signals "this is an offer, not a fact." The surface is quieter than the Atlas proposal block and disappears when the suggestion is dismissed or accepted.

Historical content (prior decision records shown in review mode):
Historical content uses the tertiary text color and a reduced opacity surface. A timestamp and version indicator appear in metadata scale. The visual treatment communicates "this is the past" without making it hard to read.

Recorded / locked content:
When the Workspace transitions to post-recording state, all content — Atlas-generated and user-authored alike — renders in primary text color on the elevated Final Decision Card. The authorship distinction becomes irrelevant in the recorded record; what matters is what was decided.

⸻

8. Expand / Collapse Presentation

Section expansion and collapse are structural, not decorative.

Collapsed state:
The section header is the entire visible element. It contains: the section label (small uppercase), a summary statement in secondary text (the collapsed summary defined in UX-009A), and the expand affordance (a subtle directional indicator — right-aligned, low-emphasis). The collapsed state is visually complete — it communicates the section's current state without requiring expansion.

The expand affordance should not be a prominent button. It should be a quiet directional signal — an indicator that more exists below. A chevron at tertiary text emphasis works correctly. It should not draw the eye when the user is reading the summary.

Expanded state:
The section opens downward. The transition is smooth — the content reveals from beneath the header, not from a separate location. The section header remains in place at the top. The content renders beneath it.

The expanded content has clear internal structure — if it contains multiple groups, they are separated by hairlines or intra-section spacing. The reading width is consistent with the rest of the document.

Expanded sections do not acquire a border or elevated surface merely because they are expanded. Only sections that deserve strong containers receive them (per Section 4 above). Expansion does not change containment level.

The transition between collapsed and expanded should feel like a document page revealing more text — not like a panel sliding open. The expansion is structural, not theatrical.

Avoid accordion-heavy interfaces. In practice, several sections may be expanded simultaneously. The user should not feel that opening one section requires closing another. The document metaphor allows multiple open passages.

⸻

9. Editable Field Treatment

Editable fields in the Decision Workspace must feel like writing inside a document, not filling out a form. This distinction is visual as well as behavioral.

Inactive state (user-authored field, not yet populated):
A placeholder text in tertiary color, at body text scale. No border. No background. The field occupies space in the document flow and its placeholder text communicates what belongs there. The absence of a border is the primary signal that this is a document, not a form.

Focused state (user is actively editing):
A subtle underline rule or a very light left-border rule activates — the minimum visual signal required to indicate the active field. No box, no background change, no shadow. The cursor is a text cursor. The surrounding document dims very slightly, drawing focus to the active field without creating a harsh overlay.

Edited state (user has authored content, field is not focused):
The user's text renders in primary text color, primary text weight. No border, no background. Indistinguishable from static document text in everything except the presence of the edit control when the field is hovered.

Atlas-suggested content (pre-populated, not yet confirmed):
Rendered in secondary text weight — slightly lighter than user-authored text. A subtle "Atlas suggests" label appears above the content. The "View original →" control is visible in the field's hover state. The distinction between suggested content and authored content must be perceptible without examining the label.

User-modified Atlas content (user has edited an Atlas-suggested field):
Renders in primary text weight — the same as user-authored content. A modification indicator appears in metadata scale below or adjacent to the field: "Modified from Atlas suggestion." This indicator is small and low-emphasis — it should inform without distracting.

Read-only state (post-recording):
The field text renders at full primary weight and color. There is no visual indication that the field was once editable — it reads purely as document text. The transition from editable to read-only should feel like the document closing, not like a field locking.

Historical state (prior decision record in review mode):
Rendered at tertiary text color with reduced opacity. Clearly readable at deliberate reading distance. A timestamp marker in metadata scale indicates when the content was recorded.

⸻

10. AI Suggestion Presentation

Atlas suggestions must feel secondary to the Workspace. They are offers, not assertions.

Suggestion affordance (the initial signal that Atlas has a suggestion):
A small inline indicator adjacent to the relevant field — at tertiary emphasis, in the Atlas blue semantic color. Not a button. Not a label. A quiet signal that something is available. The affordance appears after a typing pause (per UX-010) — it should not appear while the user is actively writing.

Suggestion panel (when the user engages with the affordance):
A compact surface — either inline adjacent to the field or as a nearby panel — at panel surface elevation. The suggestion text is in secondary weight. The "Atlas suggests" label is in metadata scale. Accept / Dismiss / Engage controls are in metadata-to-secondary scale.

The suggestion panel does not interrupt reading flow. It appears at the field level, not at the document level. It occupies space proportional to its content — compact for short suggestions, slightly taller for longer ones, but never dominating the surrounding document.

When dismissed: the panel and affordance disappear without animation.
When accepted: the field updates with a smooth text replacement, the modification indicator appears, and the panel closes.
When the partial accept model is active: the suggestion text shows highlighted segments. Selected segments render at primary weight; unselected segments render at tertiary. The user's confirmed selection assembles in the field.

The visual language of suggestions must consistently communicate: "This is Atlas offering. You remain in control." The suggestion surface is never darker, brighter, or larger than the surrounding document.

⸻

11. Contradiction Presentation

Contradictions must feel important without feeling alarming. The visual language distinguishes between information, concern, and material conflict — without using red warning states for anything short of a genuinely broken condition.

Three contradiction states, each with a distinct visual treatment:

Information — an inconsistency worth noting but not urgently resolving:
Challenge item rendered at standard body text. Left-border rule in amber at reduced opacity. The item reads as secondary — the user can acknowledge it without urgency. The acknowledgment control is in metadata scale.

Concern — a conflict with prior reasoning, portfolio strategy, or a weakening assumption:
Challenge item rendered at medium-emphasis body text. Left-border rule in amber at fuller opacity. The challenge type label ("CONTRADICTORY SIGNAL" / "UNCERTAIN ASSUMPTION") appears in metadata scale above the item. The item reads as more prominent — the user's eye is more likely to pause.

Material conflict — an opposing decision from the recent past, a broken assumption that the decision depends on, or a decision that increases a known portfolio risk:
Challenge item rendered at medium-emphasis body text with the "Consider addressing before recording" indicator visible. Left-border rule in amber, full opacity, slightly thicker. A brief Atlas reasoning line appears below the challenge statement. The acknowledgment control is larger — deliberately requiring a tap rather than an accidental hover.

What the contradiction presentation must not do:
— Use red for any challenge item unless the underlying condition is itself classified as "Broken" (an assumption or thesis condition that has definitively failed)
— Use modal alerts or interruptions
— Prevent the user from scrolling past
— Add warning icons that suggest alarm at information scale

The user must feel: "I should think about this" — not "I am blocked."

⸻

12. Opportunity Cost Presentation

The Opportunity Cost section is a signature Atlas visual experience. It must feel analytical and editorial — never like a product comparison table or a scoring matrix.

Section structure:
The section reads as a narrative comparison, not a data table. Each row (decision subject + alternatives) uses a consistent layout but with prose-style content rather than numeric cells.

Decision subject row:
Visually the anchor of the section. Slightly elevated treatment — a subtle background distinction from the alternative rows. The decision name renders at medium-emphasis body text. The Atlas conviction summary renders at secondary text.

Alternative rows:
Each alternative at slightly lower emphasis than the decision subject row — a subtle but perceptible hierarchy. The Atlas comparison line — the most important text in each row — renders at secondary body text, slightly italicized or in a distinct weight that signals "this is an interpretive statement." The user note field, when empty, is invisible. When populated, it renders in primary text weight below the comparison line.

Conclusion line:
The most prominent text within the section. It synthesizes the comparison into one statement. It renders at the transition between secondary and medium emphasis — larger than the comparison lines in each row, but not as large as the decision statement above. This is the text the user's eye should reach after reading the alternatives.

The section must never resemble a scorecard. No numeric ratings, no percentage returns in primary display, no green-for-winner / red-for-loser treatment. The comparison is qualitative. Its visual language must reflect this.

⸻

13. Portfolio Consequences Presentation

This section presents structural change to the portfolio — not a live portfolio dashboard.

The before/after structure:
Each consequence row uses a simple before → after pattern: "[position] 7.1% → 4.0%." The arrow between them is typographic — not an icon. The before value renders at secondary text, the after value at primary text. The direction of change (reduction vs. increase) is communicated by the values themselves, not by color.

The summary line:
The one-sentence synthesis of the section's most important consequence. Rendered at medium-emphasis body text, separated from the detail rows by intra-section spacing. This is the element the user reads if they do not read the individual rows.

What this section must not look like:
A portfolio dashboard, a pie chart, a bar chart, or a heat map. Structural consequences are expressed as prose and structured text — not visualizations. The reasoning is primary; numbers support the reasoning.

⸻

14. Confidence Presentation

Confidence is nuanced and qualitative. Its presentation must reflect this.

The confidence indicator in the Final Decision Card:
A small label — one of five qualitative states — in metadata scale. Adjacent to the decision statement. Not more prominent than the decision itself. The label's visual weight communicates: "this is context for the decision, not the decision."

When the confidence panel is open (the user has tapped the indicator):
The indicator text reduces in size. The explanation content appears in secondary body text — larger, more prominent, and more important than the label. The factors that contributed to the assessment are listed in metadata-to-secondary scale. Links to specific assumptions are rendered as inline text links, not buttons.

What confidence must not look like:
A gauge, a dial, a speedometer, a percentage, a star rating, a traffic light, or any visual metaphor that implies measurement precision. The five qualitative states are conceptual, not ordinal. "Moderate Confidence" is not a measured value between High and Low — it is an editorial assessment.

⸻

15. Assumptions and Invalidation Presentation

These sections communicate permanence and durability. Their visual design should reflect this.

Assumptions — each row:
The assumption statement in secondary body text. The status indicator in metadata scale — a small label (Holding / Under Review / Weakening / Broken) in the appropriate semantic color. The left-border rule in the semantic color of the status: green for Holding, amber for Under Review or Weakening, restrained red for Broken. The status color is the only color signal — the label provides the same information in text.

Expanded assumption (user has opened the detail):
The supporting reasoning appears in tertiary text below the statement — smaller, quieter. The link controls (to reasoning, to evidence) appear in metadata scale. The comment field uses the inactive field visual treatment.

Invalidation conditions:
More prominent than assumptions — slightly larger text, slightly more internal spacing. These are the conditions that govern the decision's future validity. They should feel like rules, not notes. A subtle but distinct visual treatment — perhaps a slightly heavier left-border rule — distinguishes them from assumption rows above.

The visual treatment of both sections should communicate: "these conditions are durable and will be referenced again." This is achieved through the permanence of the presentation — clean structure, no decorative elements, consistent alignment, the feeling that this content has been considered and placed with intent.

⸻

16. Implementation Presentation

Implementation is visually secondary to the recorded decision. This must be communicated clearly.

The implementation type selector:
A compact control — smaller scale than the decision type selector in Section 3. The selected type renders in secondary body text. Unselected types are in tertiary text. No prominent button treatment — the selector should feel like a document-level choice, not a software control.

The conditional detail fields (target allocation, timeline, conditions):
Use the standard inactive/focused/edited field treatment — but in a slightly reduced scale compared to the primary reason and decision fields. Secondary body text scale for labels, primary body text for user-entered values. The visual subordination reinforces that implementation details are consequential but not primary.

The No Action acknowledgment:
A single confirmation statement in secondary body text. An "Acknowledged" control in metadata scale. When confirmed, the control disappears and the confirmed statement renders at primary text, indicating that the deliberate choice has been made.

⸻

17. Review Plan Presentation

The review plan communicates continuity. The decision is entering observation, not ending.

The review trigger:
The primary trigger statement renders in secondary body text. Its label (the trigger type) renders in metadata scale. This creates a gentle rhythm: label → trigger → detail — the same rhythm used across the Workspace for structured content.

The linked monitoring conditions:
When a review trigger is linked to a monitoring condition in Section 9, a small "Linked to monitoring: [condition name]" note appears in metadata scale below the trigger detail. This is a cross-reference, not a primary statement. Its scale reflects that.

The Atlas reminder note ("Atlas will surface this decision in your Daily Briefing..."):
Tertiary text scale. Quiet. It is a description of future system behavior, not a primary element of the decision. It should be readable but invisible unless the user is looking for it.

⸻

18. Final Decision Card

The Final Decision Card is one of Atlas's signature UI components. Its visual design should be determined by three qualities: simplicity, durability, and authority.

The card in live-updating state (during editing):
A clearly defined surface at elevated background level. The six fields render in a consistent left-aligned layout. Labels are in metadata scale (small, uppercase, spaced). Values are in primary body text. Fields not yet populated show placeholder text in tertiary color.

The live-updating behavior is visually subtle — values update in place without animation. The user sees the card filling in as they work through the Workspace above. This is the document assembling itself.

The card in completed state (after recording):
The same surface and layout, but with all six fields populated in primary text weight and color. The card now communicates authority — it is the settled record. Its visual weight should be slightly heavier than in the draft state — achieved through more generous internal spacing or a subtle increase in the surface's visual distinction from the body background.

The Final Decision Card must not resemble a data card, a dashboard tile, or a notification card. It is a document artifact. It should feel like the kind of card that would sit inside a private investment journal.

⸻

19. Record Decision Area and Completion Presentation

The bottom of the Workspace closes a chapter. The visual language at this moment must communicate finality without heaviness.

The pre-recording state:
The body's final element — the context statement and challenge note — is in secondary body text. It is informational, not commanding. The footer below it contains the primary and secondary actions.

The Record Decision button in available state:
Medium emphasis — clearly the primary action, clearly the terminal point. Not a filled bright button. A defined outline or a slightly elevated surface in a restrained treatment. The label "Record Decision" is in body text scale, primary color. It should feel like a document-closing action, not a submit button.

The Record Decision button in disabled state:
The label remains "Record Decision." The button renders at reduced opacity — approximately 40–45%. The cursor is not-allowed on pointer devices. The adjacent explanation text renders in secondary body text scale. The explanation should feel like a calm note, not an error message.

After recording — the 400ms transition:
The body clears. This transition is the one moment in the Workspace where a slight pause is appropriate — not a celebration, but a breath. The Final Decision Card is the first element to appear in the cleared body, fading or sliding into place. The confirmation line appears below it. Three contextual next steps appear below the confirmation line.

The confirmation line ("Decision recorded · [date] · [investment name]"):
Tertiary text scale. Small and quiet. The meaning of the moment is in the card above it, not in the confirmation itself. The line should almost disappear behind the card — it is a timestamp, not an announcement.

The three contextual next steps:
Primary body text links, left-aligned. The first — "Return to [Workspace name]" — is the most visually prominent of the three, but still not as prominent as the Final Decision Card above it.

The footer in post-decision state:
The footer simplifies to "Close Workspace" only — same visual treatment as the secondary actions in the pre-recording footer.

⸻

20. Empty State Visual Design

Empty states must feel intentional — like a document that has been considered and found complete, not like a screen that failed to load content.

No contradictions (Section 6):
A single quiet statement in secondary text: "No conflicts identified for this decision." No icon. No placeholder illustration. No greyed-out row. The statement fills the space where challenge items would appear. The section has the same structural presence as a populated section — it is not visually compressed.

No opportunity cost identified (Section 7):
"No competing capital uses have been identified." In secondary text. Followed by a soft note in tertiary text: "If you are aware of alternatives, consider reviewing the Portfolio Workspace before recording." The section is present and has visual weight — it is not missing.

No monitoring conditions (Section 9, monitoring subsection):
"No monitoring conditions set. Atlas will not proactively surface this decision for review." Secondary text for the first sentence, tertiary for the second. The visual treatment communicates: "this is a deliberate absence."

No implementation required (Section 10, No Action):
After the deliberate acknowledgment is confirmed: "No action — deliberate decision recorded." Primary text weight for the statement, to signal that the acknowledgment was active, not passive.

No review scheduled (the only blocking empty state):
The completion gate explanation in the footer handles this — the section itself does not show an error state. The section body shows the unpopulated trigger selectors in their inactive state. This is not presented as an empty state — it is an incomplete section that the user must complete.

⸻

21. Historical Content Visual Design

Historical decisions, shown in review mode, must be immediately distinguishable from current reasoning without creating visual clutter.

The prior decision reference panel (top of scrolling body in review mode):
Collapsed by default. Header: "Prior Decision · [date] · [decision type]" in metadata scale. The collapsed panel has a subtly distinct surface — slightly reduced opacity or a left-border rule in a historical color (a quieter variant of a neutral) — that signals "this is the past." Expanding the panel reveals the prior Final Decision Card, rendered in tertiary text color at slightly reduced opacity. The layout is identical to the current Final Decision Card, ensuring the comparison is structural, not just textual.

Superseded decisions (visible in the version history panel):
Each superseded decision listed in chronological order. Decision type, date, and first line of the decision statement in metadata-to-secondary scale. Superseded status indicated by a small label — "Superseded" in tertiary text, not in a color. The visual treatment communicates that the record exists and is readable, without claiming current relevance.

Amendments and reviews:
In the version history panel, each amendment shows: the changed field name, the original value (in tertiary text), the new value (in secondary text), and a timestamp. The visual hierarchy within each entry reads: new value first, original value second. The user's current understanding takes precedence in the visual presentation.

⸻

22. Motion Philosophy

Motion in the Decision Workspace must support orientation, clarify transitions, and reduce cognitive load. It must never entertain, distract, or signal completion through visual spectacle.

Motion principles:

Duration: brief. The longest transitions in the Workspace — section expand/collapse, the post-recording transition — should complete in 250–400ms. Shorter for small state changes (suggestion affordance appearing, acknowledgment control disappearing) — 100–150ms. The 400ms post-recording pause is the only moment where duration carries meaning.

Easing: use ease-out for elements entering the screen (content revealing on expansion, panels opening, the Final Decision Card entering post-decision). Use ease-in for elements leaving (suggestions dismissing, the body clearing on recording). Ease-in-out for movements (smooth scroll, elements repositioning).

What motion clarifies:
— Section expansion: content reveals from beneath the section header, downward. The surrounding sections shift to accommodate the new height. The user follows where the content came from.
— Section collapse: content compresses upward. The summary line replaces it. The user understands that the content is preserved, not deleted.
— Scroll pause behavior at high-emphasis moments: a very subtle velocity deceleration — not a snap, not a lock. Motion communicates "this is worth reading."
— Auto-scroll to incomplete field: an animated travel from the footer to the field. The user follows the movement and arrives oriented.
— Post-recording body transition: the editing content dissolves (400ms pause, then a clean surface). The Final Decision Card appears. This is the most significant motion event in the Workspace.

What motion must not do:
— Celebrate the Record Decision action with particle effects, confetti, or success animations
— Use spring-based overshoot for any expansion or entry — this feels playful, not deliberate
— Chain multiple animations simultaneously in a way that creates visual busyness
— Animate content that is not changing state — no idle animations, no breathing effects, no subtle loops

Motion reduction:
When the OS prefers reduced motion, all transitions become instantaneous. The 400ms recording pause is preserved — it is a behavioral pause, not an animation. The document order of content is unchanged; the motion simply does not occur.

⸻

23. Hover States

Hover communicates interactive affordance. It is the secondary layer of interactivity discovery — the primary layer must be structural.

Hover behavior by element type:

Collapsible section headers:
The entire header row receives a very subtle background change — a slight surface lightening or darkening that indicates the row is interactive. The expand affordance (chevron) shifts to primary text emphasis from tertiary. The cursor is a pointer.

Editable text fields (user-authored and Atlas-suggested):
The field area receives no background change — it is document space. Instead, the edit control (a small icon or "Edit" link) appears adjacent to the field. The cursor is a text cursor within the text area, a pointer over the edit control.

Atlas suggestion affordance:
On hover, the affordance label ("Would you like to...") becomes fully visible — it may be partially visible or dimmed in its resting state. The cursor is a pointer.

Challenge acknowledgment controls:
The control receives a subtle background treatment that communicates it is a clickable element. No color change — only surface.

Alternative rows in Section 7:
The "Explore →" control becomes visible (it is not visible in the unhovered state). The row receives a very subtle surface change. The cursor is a pointer on the control, default elsewhere.

Links ("View full analysis →", "View original →", "Return to Workspace"):
The link text shifts from its resting state to primary text emphasis. An underline appears on hover. Cursor is a pointer.

Footer actions:
The Record Decision button receives a very subtle surface lightening on hover (in available state) and no change (in disabled state — cursor is not-allowed). Secondary actions receive the standard link hover treatment.

The universal rule: hover must never be the primary discovery mechanism. Every interactive element must be discoverable without hover — through its label, its position, or its structural context.

⸻

24. Focus States

Focus states serve two purposes: orienting keyboard users within the Workspace, and communicating the active editing context.

Keyboard focus ring:
A consistent outline — fixed pixel width, rounded to match the element's corner radius — visible on all interactive elements when navigated by keyboard. The ring should be clearly visible against both light and dark surfaces. It must not be subtle — keyboard users depend on it for orientation. The focus ring color is a single value used consistently across the Workspace, defined in UX-012.

The focus ring only appears on keyboard navigation. On pointer-driven interaction, the focus ring is suppressed (using `:focus-visible`). This prevents the ring from appearing after mouse clicks, where it would be distracting.

Active editing field (text cursor present):
The subtle underline or left-border rule described in the editable field treatment activates. The surrounding document dims very slightly — this is achieved through a transparent overlay on the non-focused regions at very low opacity (approximately 5–8%). The user's eye is drawn to the field without a harsh dimming effect.

Focused section header (keyboard):
The focus ring appears. The section label and summary text remain visible. The expand affordance shifts to medium emphasis. Pressing Enter or Space expands or collapses the section.

Active section context:
There is no persistent "active section" indicator beyond the standard focus ring. The user's scroll position and the expanded state of sections communicate context. No section border thickens or highlights based on scroll proximity.

⸻

25. Accessibility Visual Principles

All visual decisions must support accessibility without compromise.

Contrast:
All text — including tertiary metadata and the disabled Record Decision explanation — meets WCAG AA contrast requirements against its background. This is the minimum; primary and secondary text should meet AAA. The constraint applies to all semantic color treatments.

Non-color indicators:
Every state communicated by color is also communicated by text label, structural indicator, or typographic distinction. The assumption status "Broken" is communicated by the label "BROKEN" in metadata scale and by the left-border rule color — either alone is sufficient. A monochrome rendering of the Workspace must communicate the same hierarchy as the full-color rendering.

Typography readability:
Long-form text (primary reason, decision statement, challenge explanations) uses a minimum body text size of 15–16px at 1x scale, line height of 1.65–1.7, maximum line length of 65–70 characters. These values are specified as minimum requirements — implementations may exceed them.

Motion reduction:
As specified in Section 22 — all animations are instantaneous when the OS prefers reduced motion. No functional information is conveyed through motion alone.

Focus visibility:
The keyboard focus ring meets WCAG 2.1 Level AA for focus visibility — a perimeter of at least 2px, in a color with sufficient contrast against both the element background and the surrounding surface.

Touch targets:
All interactive elements — section headers, acknowledge controls, suggestion affordances, footer actions, field edit controls — have a minimum touch target of 44×44px. Touch targets may extend beyond the visible element boundary using padding.

Reading order:
The visual presentation order must match the DOM order and reading order. No CSS positioning that causes a screen reader to encounter content in a different order than a sighted user.

⸻

26. Desktop Experience

On desktop, the Decision Workspace should feel like reading, thinking, writing, and reviewing — in that order, as a progression through the document.

The overlay sits centered on the viewport. The originating Workspace is visible at the edges — a reminder that context is preserved. The reading width is constrained to an editorial column. The surrounding space within the overlay — between the content column and the overlay edges — is generous. The user does not feel confined within a window. They feel they are working at a desk with clear space around them.

The fixed header is low-height — sufficient to hold the decision subject, type label, and controls, but not so tall that it compresses the scrolling body. The fixed footer similarly — present but not dominant.

The desktop experience should never resemble operating software. The user should not be managing windows, panels, or navigation. They are in one document, moving through it from top to bottom.

⸻

27. Tablet Experience

Tablet preserves the editorial quality of desktop with appropriate simplifications.

The content column narrows slightly — the maximum reading width may need to reduce to approximately 55–60 characters per line. Inter-section spacing may reduce by approximately 20% to accommodate the shorter viewport height. These reductions are structural, not conceptual — the hierarchy remains identical.

The collaboration panel opens as a bottom sheet rather than an inline panel (per UX-010). The touch target sizes are at their specified minimums. Section headers are fully tappable as rows.

No functional content is hidden or moved on tablet. The Workspace contains the same sections in the same order with the same behavior. The adaptation is purely spatial.

⸻

28. Mobile Experience

Mobile does not compress reasoning into cards. It preserves the reading flow at reduced width.

At mobile width, the content column fills the screen horizontally. Inter-section spacing reduces to approximately 60% of desktop spacing — enough to maintain rhythm without requiring excessive scrolling.

The fixed footer on mobile occupies the bottom of the viewport at native safe area height. The primary action is within thumb reach. The explanation text adjacent to the disabled button may wrap to two lines — this must be accounted for in the footer height.

Sections that are collapsed on mobile must still communicate their summary content legibly. The collapsed section header — section label, summary statement, and expand affordance — is all the user sees. The summary text must be comprehensive enough to be meaningful without expansion.

Long-form text fields expand to full screen on mobile when focused (per UX-010). The expanded full-screen editing mode uses the same typographic treatment as the document — the user writes in the same style, just with more available space and an uncluttered context.

Mobile must not feel like a degraded version of desktop. The experience is simpler in scope but not lesser in quality. The user makes the same decision with the same care.

⸻

29. Emotional Journey

The visual design must support the following emotional arc from the user's first arrival to their post-recording state:

Arrival:
The overlay opens. The originating Workspace is visible beneath. The header orients the user: "[Investment name] · Reduce." The body shows Section 1 — the Current Conclusion card, fully formed, with the conclusion statement at full emphasis. The user feels: "I am in the right place. I know what this is about."

Orientation:
The user reads the conclusion, the decision trigger. The Proposed Decision section below shows what Atlas thinks follows from the analysis. The user decision field waits — a gentle invitation, not a demand. The user feels: "I understand the situation. Now I need to decide what I think."

Understanding:
The user reads the supporting and challenging sections. They see what works in their favor and what complicates the decision. The Opportunity Cost section surfaces the alternatives. The user feels: "I can see the full picture now. This decision has real context."

Reflection:
The user authors their primary reason. They adjust Atlas's proposed assumptions. They review the invalidation conditions. They set a review trigger. The Workspace does not rush them. The Final Decision Card begins to fill in as they work. The user feels: "I'm building this decision carefully. I understand what I'm committing to."

Decision:
The Final Decision Card is complete. The user reads it in full — seeing their decision, their reason, their confidence level, their review condition assembled in one place. The Record Decision button is available. The user feels: "This decision is clear. I'm ready."

Commitment:
The user selects Record Decision. The 400ms pause. The body clears. The Final Decision Card occupies the cleared space, settled and permanent. The user feels: "That is exactly what I decided. It's recorded correctly."

Calm completion:
The confirmation line appears below the card. Three contextual next steps. The footer shows "Close Workspace." Nothing celebrates. Nothing demands further action. The user feels: "I've done something meaningful and careful. I can return to my work."

The visual design is responsible for enabling this arc. The emotional journey is not narrated — it is structured.

⸻

30. Signature Atlas Moments

Six visual moments should be designed with particular care. These are the moments that will define the Decision Workspace's identity and make the Atlas experience recognizable across the product.

1. The Current Conclusion Card
The opening moment. The first thing the user sees below the header. It must communicate authority and clarity simultaneously. The card's visual weight, its typography, and its contained surface must immediately communicate: "This is the foundation for your decision."

2. The User Decision Field
The most important interactive element in the Workspace. The moment the user begins writing in this field — when the document waits for their commitment — must feel significant. The typographic treatment of the text as it appears, the subtle activation of the field, and the live updating of the Final Decision Card in the distance must work together to create a sense of authoring, not form-filling.

3. The Opportunity Cost Section
The comparative reasoning moment. The presentation of decision subject versus alternatives in a qualitative, reasoning-first layout — without scores, without rankings — is one of the visual ideas that most clearly separates Atlas from conventional investment tools. This section should feel like reading a considered analysis, not looking at a comparison table.

4. A Contradiction Item Appearing
The moment Atlas surfaces a conflict with prior reasoning. Section 6 expands quietly. The new item highlights briefly. The acknowledgment control appears. This interaction — calm, non-interrupting, serious — should feel like being shown something important by a thoughtful colleague. Not a warning system activating.

5. The Final Decision Card
The document assembling itself into a permanent record. The live-updating card, filling in as the user works through the Workspace, arriving at its completed form before the user records. The visual moment when the card is complete and the user reads it in full before committing.

6. The Post-Recording Moment
The 400ms pause. The body clearing. The Final Decision Card settling into the center of the cleared space. This is the closest the Workspace comes to ceremony — achieved entirely through space, timing, and the visual authority of the card. No animation, no icon, no celebratory element. The record speaks for itself.

⸻

31. Holistic Design Audit Principles

The following questions must be applied to every visual element in the final implementation:

Can anything be removed without causing confusion?
If yes: remove it. Every element that does not carry meaning creates noise.

Does the spacing between elements communicate their relationship?
Adjacent elements that are conceptually related should be closer than elements that are not. Spacing should communicate structure before typography does.

Can typography replace a visual treatment?
If a border, background, or icon is being used to communicate something that well-chosen typography could communicate instead: use typography.

Can structure replace a border?
If a border is being used to separate elements that consistent alignment would already separate: remove the border.

Can hierarchy replace color?
If color is being used to establish hierarchy that size, weight, and spacing would already establish: confirm the color is adding semantic meaning, not visual interest.

Does every element feel like it belongs in this document?
The Workspace should feel like a single, coherent document. If any element feels like it was imported from a different product category — a dashboard widget, a chat bubble, a form field from a different era — redesign it to fit the document.

Would this Workspace feel appropriate to look at five years from now?
The visual language must be timeless. Nothing should feel like a design trend. The deliberate constraints of the system — restrained color, typographic hierarchy, generous space, contained surfaces used sparingly — should produce a visual result that ages well.

⸻

What UX-011 Establishes

The following visual decisions are now fixed:

— Visual philosophy: editorial, restrained, calm, typographic, premium. The Workspace references a considered document publication — not enterprise software, consumer fintech, or a brokerage terminal.

— Four foundational commitments: restraint over decoration, structure over borders, typography over color, permanence over novelty.

— Three-tier visual hierarchy: highest (Conclusion, Decision, Final Decision Card, Record Decision), medium (Trigger, Opportunity Cost, Challenges, Consequences, Invalidation), lower (Supporting factors, Assumptions, Monitoring, Implementation, Metadata).

— Typography system: seven conceptual roles (Workspace subject, section labels, conclusion statement, decision statement, supporting explanations, metadata, confidence labels) with defined relationships. Long-form text at editorial line length (65–70 characters) and line height (1.65–1.7).

— Reading rhythm: inter-section spacing as the primary pacing mechanism. Four visual pause points (Sections 1, 3, 7, 12). No section interrupts the narrative.

— Card system: three containment levels. Strong containers for Section 1 and Section 12 only (plus the Atlas proposal block). Subtle containers for alternative rows, challenge items, assumption rows. Dividers for intra-section separation. Open layout for sections that do not require containment.

— Spacing system: four spacing tiers (inter-section, intra-section, row, label-to-content). Maximum reading width of approximately 65–70 characters. Workspace must never feel dense.

— Color semantics: warm dark editorial base. Restrained amber for review/pending states. Restrained green for intact/valid states. Restrained red for broken/deteriorated states only. Atlas blue for Atlas-sourced indicators. Muted treatment for disabled and read-only states.

— Authorship model: four-layer distinction (label, typography weight, layout position, surface treatment for suggestions). Atlas-generated content consistently labeled in metadata scale. User-authored content in primary weight with no source label.

— Editable field treatment: no borders in inactive state. Subtle underline or left-border on focus. User-authored content visually indistinguishable from static document text when not focused. Atlas-suggested content in secondary weight with "Atlas suggests" label.

— Suggestion presentation: small inline affordance, compact panel at panel-surface elevation, secondary-weight text, partial accept with highlighted segments. Never dominates the surrounding document.

— Contradiction presentation: three visual states (information, concern, material conflict) using left-border rule and opacity variation in amber. No red for challenge items unless the underlying condition is Broken. No modals or interruptions.

— Opportunity cost: prose-comparison layout with narrative comparison lines. No numeric scores, no ranking treatment. Conclusion line as the most prominent text in the section.

— Portfolio consequences: before/after typographic structure. No charts. Summary line at medium emphasis.

— Confidence: small metadata-scale label, never numeric, never gauged. Explanation content more prominent than the label. Five qualitative states only.

— Assumptions and invalidation: left-border rule in semantic status color. Status label in metadata scale. Invalidation conditions slightly more prominent than assumption rows.

— Implementation: visually subordinate to the decision. Secondary scale for the type selector. Reduced-scale field treatment for detail fields.

— Final Decision Card: elevated surface, two visual states (live-updating with placeholder text, completed with primary weight text). Becomes the sole body content in post-recording state.

— Record Decision: medium emphasis in available state, 40–45% opacity in disabled state. Adjacent explanation in secondary text, not error styling. 400ms post-recording pause before body clears.

— Empty states: present as complete, intentional document states. Same structural presence as populated sections. No placeholder illustrations.

— Historical content: tertiary color, reduced opacity, expanded layout identical to current layout for structural comparison.

— Motion philosophy: brief (100–400ms), directional, functional. No overshoot, no celebration, no idle animations. 400ms post-recording pause is behavioral, not decorative. Instantaneous under reduced-motion preference.

— Hover states: surface-level treatments only. Edit controls appear on hover for text fields. Focus ring suppressed on pointer interaction.

— Focus states: consistent focus ring (2px+, sufficient contrast) visible on all keyboard-navigated elements. Active field receives subtle underline rule. Surrounding document dims at 5–8% opacity.

— Accessibility: WCAG AA minimum contrast for all text. Non-color indicators for all semantic states. Minimum 15–16px body text, 65–70 character line length. Minimum 44×44px touch targets. Reading order matches DOM order.

— Desktop: editorial document experience, constrained reading column, generous surrounding space.

— Tablet: same hierarchy, reduced spacing, bottom-sheet panels, same functional content.

— Mobile: full-width content column, footer at thumb height, full-screen editing mode for long-form fields, same decision quality.

— Emotional journey: seven stages (Arrival, Orientation, Understanding, Reflection, Decision, Commitment, Calm completion) each structurally supported by the visual design.

— Six signature Atlas moments: Current Conclusion card, User Decision field, Opportunity Cost section, Contradiction appearance, Final Decision card live-update, Post-recording moment.

— Holistic design audit: seven questions applied to every visual element.

⸻

Remaining Visual Questions

The following are genuine unresolved visual questions that require decisions before implementation:

1. Overlay entry animation: the specific form of the overlay's entry transition has not been defined at the motion-parameter level. Should the overlay slide up from the bottom (consistent with the Investment Case and Portfolio Workspace overlay pattern), fade in, or use a different entry? The entry motion sets the first emotional tone of the Workspace.

2. The partial accept visual form: the specification describes "highlighted segments" for partial acceptance of Atlas suggestions, but the exact visual treatment of selected versus unselected segments requires a visual design decision — highlight color, selection affordance, confirmed state appearance.

3. The "Atlas suggests" label precise form: the specification establishes that this label exists at metadata scale and uses the Atlas blue semantic color, but whether it is accompanied by any iconographic element — a small symbol that becomes recognizable as the "Atlas voice" — is not yet resolved.

4. The post-recording transition specifics: the 400ms pause and body-clearing behavior are specified, but the exact transition form — does the existing content fade, compress, or simply disappear — has not been defined. Each option creates a different emotional quality.

5. The reading width for the specific overlay dimensions: the specification establishes approximately 65–70 characters per line as the target line length, but the exact column width in pixels — derived from the overlay width, content padding, and font size — must be calculated and specified in UX-012.

⸻

Requirements for UX-012

The Atlas Design System & Workspace Consistency Specification must establish:

Cross-workspace consistency:
— A shared visual language that applies coherently across the Dashboard, Investment Workspace, Portfolio Workspace, and Decision Workspace — allowing users to move between Workspaces without any feeling of context switch at the visual layer
— The shared overlay behavior: entry animation, background dimming, overlay proportions, fixed header and footer treatment — consistent across all Workspace overlays
— A shared section anatomy: the relationship between section labels, content, dividers, and spacing must follow the same rules across all Workspaces

Reusable components:
— The Final Decision Card as a component: its states (draft, live-updating, completed, historical), its data model, and its behavior when embedded in Atlas Memory, Daily Briefing, and future Workspace surfaces
— The Challenge Item component: its three visual states, its acknowledgment control, and its behavioral context variant
— The Assumption Row component: its status variants, its expand/collapse behavior, its links to monitoring conditions
— The Atlas Suggestion Panel: its form factor on desktop, tablet, and mobile; its accept/dismiss/partial-accept states
— The Contradiction Item component: its three severity states and their visual distinctions

Shared typography scale:
— A formal type scale defining all roles specified in UX-011 as named tokens: `--type-workspace-subject`, `--type-section-label`, `--type-conclusion`, `--type-decision`, `--type-body-primary`, `--type-body-secondary`, `--type-metadata`
— Font family decisions for each role (whether the system uses one family or two — a sans-serif for reasoning text and a monospace or narrow variant for metadata and labels)
— Minimum sizes for each role across the three breakpoints (desktop, tablet, mobile)

Spacing scale:
— A formal spacing scale as named tokens: `--space-inter-section`, `--space-intra-section`, `--space-row`, `--space-label-content`
— How the spacing scale reduces at tablet and mobile breakpoints
— The maximum content width token and its behavior at different viewport widths

Card variants:
— Strong container: the definitive specification for the Current Conclusion card and Final Decision Card — their surface treatment, internal padding, corner radius, and elevation treatment
— Subtle container: the definitive specification for challenge item and alternative row backgrounds
— The Atlas proposal block as a named card variant

Interaction tokens:
— Duration values for all transitions: expand/collapse (section), expand/collapse (row), suggestion panel open/close, post-recording transition, scroll behavior
— Easing curves for each transition type: ease-out for entry, ease-in for exit, ease-in-out for positional movement
— The scroll deceleration behavior at pause points — defined as a named interaction token

Motion tokens:
— A reduced-motion fallback token that governs all transitions globally
— Duration multipliers for different transition categories (structural transitions vs. state transitions vs. the post-recording pause)

Icon system:
— Whether iconographic elements are used alongside the Atlas suggestion label
— The expand/collapse affordance — chevron specifications (size, weight, orientation)
— Any additional iconographic elements in the Workspace (challenge item type indicators, assumption status indicators, implementation type indicators)
— The Atlas badge in the fixed header

Semantic color tokens:
— Formal token names for all semantic colors established in UX-011: `--color-surface-primary`, `--color-surface-elevated`, `--color-surface-panel`, `--color-text-primary`, `--color-text-secondary`, `--color-text-tertiary`, `--color-accent-amber`, `--color-accent-green`, `--color-accent-red`, `--color-accent-blue`, `--color-disabled`
— The precise warm dark values for each token, specified as HSL or equivalent
— Dark-mode-only variants (the Decision Workspace is dark by default; confirm whether a light mode variant is required)
— Contrast ratios for all text-on-surface combinations

Workspace templates:
— A canonical layout template for Workspace overlays: the header zone, scrolling body zone, and footer zone proportions
— The content column specification: width, horizontal centering, padding
— The section anatomy template: section label position, content start, divider style

Accessibility tokens:
— The focus ring specification: pixel width, color token, corner radius behavior
— Minimum contrast ratios as tokens that all implementations must pass
— Minimum touch target size tokens
— Reduced-motion flag handling

Future Workspace extensibility:
— A component inventory that documents which components from the Decision Workspace are candidates for reuse in future Atlas Workspaces (e.g., the Challenge Item, the Final Decision Card, the Assumption Row, the Atlas Suggestion Panel)
— Design principles for extending the visual system to new Workspace types — ensuring that future Workspaces maintain the same editorial character without requiring case-by-case design decisions

Do not produce UX-012 yet.

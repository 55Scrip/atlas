UX-012A — Atlas Design System Foundations

Status: Superseded — see UX-012 §5 (Level 2/4 hierarchy, corrected per ADR-002 C-01)
Owner: Atlas Product
Governs: Design system philosophy, cross-workspace principles, information hierarchy, typography, spacing, layout, Workspace frame, section template, reading rhythm, responsive philosophy, accessibility
Depends on: UX-008, UX-009, UX-009A, UX-010, UX-011
Part A of: UX-012 — Atlas Design System & Workspace Consistency Specification

**Correction Notice (Phase 3, governed by ADR-002 — 2026-07-25):** This document's original identity (Owner, Governs, Depends on, Part A of, as above) and original date are preserved unchanged. Two semantic areas were corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan, Phase 3:
- **C-01 (Information Hierarchy authority):** the `Status:` line above is updated to record that this document's own Level 2/4 hierarchy wording — originally "Foundation Specification Complete" — is superseded specifically for hierarchy authority by UX-012 §5, which was corrected to adopt this document's own original Level 2/4 wording (Material Implication / Challenges, Uncertainty, and Contradiction). This supersession is scoped to hierarchy authority only; the remaining Foundation content below (product philosophy, typography, spacing, layout, Workspace frame, accessibility, and all other sections) is not superseded and remains part of this document.
- **C-03 (Decision Workspace Sequence terminology):** one stale component reference — "The Final Decision Summary card" — was corrected to "The Final Decision Card" in the card-emphasis discussion, matching the ten other, already-correct occurrences of the canonical name elsewhere in this document.

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, above. All content outside these two areas is unchanged.

**Correction Notice (Atlas UX Architecture UX-012 Authority Migration task — 2026-08-02):** This is a later, additive correction; it does not revise, replace, or reopen the Phase 3 notice above, which remains historically accurate for the areas it corrected. This document is subordinate to `UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0, per that Doctrine's own UXD-R-097. Its own Status line above already marks it Superseded — see UX-012 §5 — for hierarchy-authority purposes only; the remainder of its content, including the two passages corrected below, remains part of the active record cited by UX-012B, UX-012C, and UX-012D. Two semantic areas are corrected:
- **Atlas Memory terminology (Section 4):** two passages attributed the creation of permanence to "Atlas Memory" itself rather than to the act of recording. Per `UX-000-Atlas-UX-Doctrine.md` UXD-R-094, Memory is UX-layer language only and MAY NOT be used as a Product Concept; the accepted successor terms, per the completed Atlas Memory Status Investigation, are DecisionHistory (catalog lookup across recorded Decisions) and Decision Timeline (one Decision's own chronological narrative), applied below according to each passage's own meaning, alongside the pre-existing Historical Record component defined in this document's own companion `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §27 (Decision History itself is defined at §25).
- **AI-belief framing (Section 5, Principle 5):** "Atlas concludes" risked framing Atlas as an independent authority that concludes truth, contrary to `UX-000-Atlas-UX-Doctrine.md` UXD-R-056.

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, at each corrected passage below. All content outside these two areas is unchanged.

**Terminology Notice (Atlas UX Governance Resolution Sprint, 2026-08-03):** Per the completed ATLAS UX CORRESPONDENCE INVESTIGATION, which found this document's "Daily Briefing" reference and `APS-008`'s formal "Daily Brief" to name the same product surface, with no contextual difference, "Daily Briefing" is corrected to "Daily Brief" in Section 1's list of Atlas surfaces (previously: "the Daily Briefing, the Investment Workspace, the Portfolio Workspace, or the Decision Workspace"). This is a naming correction only; the surrounding governing-language statement is unchanged.

⸻

1. The Atlas Design System Defined

The Atlas Design System is not a UI kit, a component library, a visual theme, or a style guide. Those things may eventually be produced as outputs of the system, but they are not the system itself.

The Atlas Design System is the governing language for how Atlas thinks, communicates, and behaves. It is the set of decisions that ensures Atlas always reasons in the same way regardless of which surface the user is currently using — the Daily Brief, the Investment Workspace, the Portfolio Workspace, or the Decision Workspace.

It governs five things:

Reasoning structure. The order in which information is revealed, the hierarchy of conclusions over detail, and the consistent logic by which complexity is disclosed or withheld.

Communication. The language Atlas uses — the words it chooses for states, confidence levels, contradictions, decisions, and monitoring. This language is shared across all surfaces. A user who learns what "High Confidence" means in the Decision Workspace knows what it means in the Investment Workspace.

Hierarchy. The visual and typographic relationships that tell the user which information is most important without requiring them to read everything. The system establishes that hierarchy and ensures it is applied consistently.

Interaction. The behavioral patterns by which users expand, edit, acknowledge, record, and navigate. Patterns established in one Workspace are recognized in others because they follow the same underlying grammar.

Continuity. The rules that ensure context survives movement between Workspaces. When a user moves from the Portfolio Workspace to the Decision Workspace, they do not restart their understanding. The Design System defines what is carried forward and how it is presented when it arrives.

What the Design System does not solve:

It does not define which investments a user should consider. It does not replace product judgment in defining which sections belong in which Workspace. It does not specify production-ready code or Figma component implementations — those are outputs of UX-013 and beyond. It does not make every Workspace look identical. Identical appearance across contextually different surfaces would be a failure of the system, not a success.

The governing principle: Atlas should be consistent in how it thinks, not merely in how it looks.

⸻

2. Atlas Product Philosophy

Atlas improves investment decision quality. It does not replace the investor's judgment. It does not generate trading signals. It does not optimize for activity, engagement, or transaction volume. It is not a portfolio performance dashboard. It is not a financial news aggregator. It is not a research terminal.

Its central commitment is this: Atlas helps users make better decisions by improving the quality of their reasoning, not by making more decisions easier to reach.

This produces four product principles that the Design System must reinforce everywhere:

Decision quality over decision speed. Atlas is designed for the investor who wants to think carefully, not act quickly. The Design System must not create urgency, promote action, or reward high-frequency interaction.

Transparency over confidence. Atlas surfaces uncertainty, challenges, and contradictions alongside its conclusions. The Design System must make uncertainty visible, not hide it behind optimistic summaries.

User judgment as the final authority. Atlas proposes, suggests, and concludes — but the user decides. The Design System must make this authorship relationship clear in every field, every suggestion, and every recorded output. The user's voice must be visually distinguishable from Atlas's voice at all times.

Depth without complexity. Atlas deals with intellectually demanding subject matter. The Design System must make this material feel manageable and readable — not by simplifying it, but by structuring it so clearly that the complexity reveals itself at the right pace.

How the Design System reinforces these:
— By establishing conclusion-first information hierarchy, Atlas shows the user what matters before asking them to read why.
— By making authorship legible through typography and layout rather than color alone, Atlas reminds the user that they are the decision-maker.
— By defining generous spacing and editorial reading widths, Atlas signals that the user is expected to think, not scan.
— By defining restrained color semantics that separate signal from emphasis, Atlas avoids creating the sense of urgency that financial information interfaces are prone to produce.

⸻

3. Cross-Workspace Roles

The four Atlas surfaces have distinct purposes, user mindsets, and interaction depths. The Design System must preserve these differences. Treating all surfaces identically would erase the reasoning arc that makes Atlas coherent as a product.

Dashboard

Primary purpose: Surface what deserves the user's attention today.
User mindset: Scanning. The user arrives without a specific investment in mind. They are asking: what has changed? What needs my attention?
Interaction style: Minimal. The user reads, follows a signal, or dismisses. Editing is rare. Decision-making does not happen here.
Reading depth: Shallow. Each item is compact. Supporting detail is available but not default.
Editing depth: None. The Dashboard is observational.
Decision responsibility: Attention allocation only — the user decides which signal to investigate further.

The Dashboard should feel observant and selective. It surfaces the most important signals and withholds everything else. A well-functioning Dashboard presents very little — because what it presents has already been filtered.

Investment Workspace

Primary purpose: Examine whether the user's thesis for a specific investment still holds.
User mindset: Investigative. The user has arrived with a specific company or investment in mind and wants to understand whether their prior judgment remains valid.
Interaction style: Reading-primary, with occasional editing of assumptions, confidence assessments, and notes.
Reading depth: Deep. The user reads structured analysis — thesis, evidence, assumptions, challenges, valuation, scenario — in a coherent sequence.
Editing depth: Moderate. The user may edit their thesis statement, update assumption status, adjust conviction, and add notes. They do not author analysis from scratch.
Decision responsibility: Reaches a conclusion about the state of the investment — but the decision to act is deferred to the Decision Workspace.

The Investment Workspace should feel investigative and focused. It narrows attention to one subject and examines it from multiple angles without losing the thread.

Portfolio Workspace

Primary purpose: Examine whether the portfolio as a whole is positioned in accordance with the user's objectives, convictions, and risk tolerances.
User mindset: Strategic and integrative. The user has stepped back from individual investments to see the whole — concentration, dependencies, capital competition, structural alignment.
Interaction style: Reading-primary, with occasional editing of allocation context and prioritization notes.
Reading depth: Deep across the portfolio structure, moderate on individual positions.
Editing depth: Moderate. The user may annotate sections, adjust priority, and set review focus. They do not rewrite the underlying analysis.
Decision responsibility: Identifies which decisions deserve attention and prepares the context for them — but does not record decisions itself.

The Portfolio Workspace should feel integrative and strategic. It synthesizes across all holdings and reveals structural relationships that are invisible when looking at investments one at a time.

Decision Workspace

Primary purpose: Help the user form, examine, document, and preserve an investment decision.
User mindset: Deliberate and conclusive. The user has arrived with a position and wants to work through it carefully — examining its reasoning, its assumptions, its opportunity cost — before committing.
Interaction style: Writing-primary. The user authors their decision statement, their primary reason, their confidence assessment, their assumptions, and their review conditions. Atlas provides the analytical context; the user supplies the commitment.
Reading depth: Deep. The user reads both Atlas-generated context and their own prior writing.
Editing depth: High. The user owns the most important fields in this Workspace.
Decision responsibility: The user records a durable decision — the reason, the assumptions it depends on, the conditions that would change it, and the plan for reviewing it.

The Decision Workspace should feel deliberate and conclusive. It is the only surface where the user makes a permanent commitment. The visual weight of the final decision should reflect this.

How these surfaces differ while remaining one reasoning flow:

The user moves through these surfaces in a reasoning arc: attention → investigation → portfolio interpretation → decision. The Design System ensures that each step in this arc feels like a continuation of the previous one. The same visual grammar, the same terminology, the same authorship conventions, and the same information hierarchy apply everywhere — even as the density, editability, and decision weight differ across surfaces.

⸻

4. Atlas Reasoning Flow

Every piece of information in Atlas, and every interaction, belongs somewhere in the following reasoning sequence:

Signal: Something has changed, or a condition has been met, that deserves the user's attention. The Dashboard is the primary surface for signals.

Context: The background needed to understand why the signal matters — the investment's thesis, its current assumptions, its prior decisions. The Investment Workspace is the primary source of context.

Understanding: A structured examination of the investment, the portfolio, or the decision at hand. The Investment Workspace and Portfolio Workspace are the primary surfaces for understanding.

Analysis: Deeper reasoning — opportunity cost, scenario implications, concentration effects, historical comparison. Both the Portfolio Workspace and the Decision Workspace contain analysis.

Decision: The user's explicit commitment — what they have decided, why, what they expect to remain true, and when they will review it. The Decision Workspace is the primary surface for decisions.

Monitoring: The conditions Atlas will observe after the decision is recorded — the triggers that will surface the decision for review. Monitoring appears in the Decision Workspace's review plan and in the Dashboard's ongoing signals.

Memory: The permanent record of the decision — created by the act of recording, and accessible across all surfaces for future reference, review, and comparison through the Historical Record and the decision's own Decision Timeline. *(Corrected per the Atlas UX Architecture UX-012 Authority Migration task, 2026-08-02 — see the Correction Notice above. Prior text: "preserved in Atlas Memory and available across all surfaces for future reference, review, and comparison," which risked attributing the creation of permanence to Atlas Memory itself rather than to the act of recording. Refined per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02: per the completed Atlas Memory Status Investigation, one decision's own chronological narrative is its Decision Timeline, distinct from DecisionHistory's catalog-wide scope.)*

How each Workspace participates:

Dashboard → Signal. It initiates the flow by identifying what matters.
Investment Workspace → Context + Understanding. It examines whether the thesis behind the signal remains valid.
Portfolio Workspace → Understanding + Analysis. It examines what the signal means for the whole portfolio.
Decision Workspace → Analysis + Decision + Monitoring. It closes the loop by producing a durable, reviewable commitment.
DecisionHistory and Historical Record → Memory. Recording creates the permanent record; these components make it accessible for future signals. *(Corrected per the Atlas UX Architecture UX-012 Authority Migration task, 2026-08-02 — see the Correction Notice above. Prior text: "Atlas Memory → Memory. It preserves the output and makes it available for future signals," which named an undefined "Atlas Memory" surface as the actor performing preservation. Refined per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02: per the completed Atlas Memory Status Investigation, the catalog-wide, cross-decision lookup this stage of the reasoning flow describes is DecisionHistory; Historical Record is the base immutable component each catalogued record is presented through, per this document's own companion `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §27 (Decision History itself is defined at §25).)*

The Design System ensures that movement through this flow feels continuous. When the user arrives in the Decision Workspace from the Portfolio Workspace, the context they built in both prior surfaces is present and legible. Nothing requires the user to re-explain their situation. The Workspace knows where they came from and begins from there.

⸻

5. Universal Design Principles

The following principles govern every Atlas surface without exception. They are not stylistic guidelines. They are structural commitments — rules against which every design decision in the system should be tested.

1. Conclusion before detail.
The most important statement on any screen appears at the top, before its supporting reasoning. The user should not have to read to the end to understand the point. This principle applies at every level: Workspace, section, card, and paragraph.

2. Signal before explanation.
When something has changed or requires attention, the change itself is visible before the explanation of why. The user can decide whether the explanation is worth reading.

3. Reasoning before action.
The reasoning that supports a decision or recommendation is always visible before the action control that acts on it. Atlas never presents a "Do this" button without first showing the reasoning behind the recommendation.

4. Important information before complete information.
Atlas prioritizes the most material items within any list, section, or Workspace. Completeness is not an Atlas value. Relevance is.

5. The user owns judgment and decisions.
Atlas synthesizes, suggests, and proposes — but the user decides. *(Corrected per the Atlas UX Architecture UX-012 Authority Migration task, 2026-08-02 — see the Correction Notice above. Prior text: "Atlas concludes, suggests, and proposes," which risked framing Atlas as an independent authority that concludes truth, contrary to `UX-000-Atlas-UX-Doctrine.md` UXD-R-056.)* Every recorded decision is the user's. The user's authored content is always visually distinguishable from Atlas's generated content. The user may override, reject, or edit any Atlas-generated content without justification.

6. Uncertainty remains visible.
Atlas does not smooth over uncertainty with confident-sounding summaries. Confidence levels, incomplete assumptions, unresolved contradictions, and genuinely unknown outcomes are all surfaced. The user makes their decision with the uncertainty in view.

7. Historical reasoning remains intact.
No prior decision, assumption, or conclusion is silently overwritten or hidden. When Atlas updates its analysis, the prior state is preserved. When the user amends a decision, the original remains accessible. History is additive.

8. AI remains contextual and secondary.
Atlas's reasoning, suggestions, and proposals are always clearly identified as such. Atlas assistance appears in response to the user's work — not ahead of it. Atlas does not control the interface or interrupt the user's reasoning process.

9. Context survives navigation.
When the user moves between Workspaces, the relevant context from their previous surface travels with them. The user does not re-explain their situation when arriving in the Decision Workspace from the Portfolio Workspace. The Workspace they left is preserved and accessible upon return.

10. Complexity appears only when relevant.
Advanced sections, detailed assumptions, historical comparisons, and implementation specifics are revealed progressively. The default state of any Workspace shows the user what they need to begin reasoning — not everything that exists.

11. Typography communicates hierarchy before color does.
The visual priority of any element — its relative importance on the screen — is established primarily through typographic scale, weight, and spatial position. Color confirms semantic meaning but is never the sole indicator of importance.

12. Spacing communicates structure before borders do.
The relationship between elements — which items belong together, which are distinct — is established primarily through spatial proximity and separation. Explicit borders, dividers, and containers are used sparingly and only when spatial organization alone is insufficient.

13. Every visual element must improve comprehension.
No element is present for decoration. If removing an element does not cause confusion, it should be removed. Visual restraint is not an aesthetic preference — it is a precision requirement.

14. Atlas should know when to remain quiet.
When nothing material has changed, Atlas says so briefly and without apology. When the user's reasoning is already complete, Atlas does not add suggestions. Silence is sometimes the most appropriate response.

15. The product should reward thought, not activity.
No interaction should create urgency. No visual state should suggest that acting quickly is better than acting carefully. The product's tone at every layer — copy, motion, color, hierarchy — should support deliberation.

⸻

6. Consistency versus Context

Not every decision in Atlas should look identical. The Dashboard and the Decision Workspace serve different cognitive purposes, and designing them identically would undermine both. The Design System's task is not uniformity — it is coherence.

The following must remain consistent everywhere:

Terminology: The words used for states, confidence levels, contradictions, authorship, and decisions are identical across all surfaces. "High Confidence" means the same thing in the Investment Workspace and the Decision Workspace. "Material Contradiction" is labelled the same way everywhere it appears.

Confidence language: The five qualitative confidence states (High Confidence, Moderate Confidence, Low Confidence, Evidence Incomplete, Dependent on Uncertain Assumptions) are used with identical meaning and labelling across all surfaces.

Authorship distinction: The visual convention for distinguishing Atlas-generated content from user-authored content is identical across all surfaces. A user who learns this convention in one Workspace does not need to relearn it in another.

Section collapse logic: A collapsed section always shows a meaningful summary of its current state. The structure of that summary — section label, one-line headline, one-line implication, status indicator if relevant — is consistent across all surfaces.

Expansion affordance: The control that expands a collapsed section is visually identical across all surfaces. Its position, scale, and behavior do not vary.

Spacing relationships: The ratios between spacing levels — the relationship between inter-section spacing and intra-section spacing, between label-to-content spacing and row spacing — are consistent. Absolute values may scale responsively, but the relationships are fixed.

Semantic color meanings: A given semantic color carries the same meaning everywhere it appears in Atlas. Amber is not used for positive conditions in one Workspace and warning conditions in another. Green does not mean "buy" in any context.

Keyboard behavior: Tab order, expansion shortcuts, and action shortcuts follow the same conventions across Workspaces.

Historical treatment: Prior decisions, prior conclusions, prior assumptions — wherever they appear — use the same visual treatment: tertiary text color, reduced emphasis surface, timestamp in metadata scale.

The following may vary by context:

Density: The Dashboard uses compact signal density. The Decision Workspace uses editorial reading density. These are different because the cognitive task is different. A dense Dashboard is efficient; a dense Decision Workspace would be stressful.

Default expansion: The Dashboard defaults most content to collapsed. The Decision Workspace opens its most important sections by default. This reflects the different reading modes: scanning versus linear reading.

Card emphasis: The Final Decision Card is one of the most prominently contained elements in Atlas — it deserves strong visual framing because it is a permanent record. Supporting factor cards in the Investment Workspace require only subtle separation. Containment strength is proportional to the significance and permanence of the content.

Editing presence: The Dashboard has essentially no editing. The Investment Workspace has moderate editing. The Decision Workspace has extensive editing. The editing affordances are present or absent based on the surface's purpose.

Comparison layouts: Multi-column comparison layouts are appropriate in the Opportunity Cost section of the Decision Workspace and in certain Portfolio Workspace sections. They are inappropriate in the Dashboard, where they would compete with the scanning model.

Section count and order: Each Workspace has a different section architecture determined by its purpose. The shared template governs the anatomy of each section, not the number or ordering of sections.

The governing rule behind all contextual variation: A difference between Workspaces is justified only when the reasoning task genuinely requires it. A variation that exists merely for visual variety, to distinguish one Workspace from another, or to make a Workspace feel more technically sophisticated is not justified.

⸻

7. Atlas Information Hierarchy

Every piece of content in Atlas belongs to exactly one level of the following hierarchy. Every design decision — typography, spacing, containment, layout, responsive behavior — flows from understanding which level a piece of content occupies.

Level 1 — Primary conclusion or decision:
The most important statement on the screen. The single thing the user must not miss. In the Dashboard, this is the most urgent signal. In the Investment Workspace, it is the thesis conclusion. In the Portfolio Workspace, it is the portfolio assessment. In the Decision Workspace, it is the decision statement.
→ Largest type on the screen. Greatest surrounding space. Strong visual containment for permanent records (Final Decision Card). Placed first in the reading order.

Level 2 — Material implication:
Why the primary conclusion matters. What it means for the user's situation. This is not the supporting evidence — it is the consequence or significance of the Level 1 statement.
→ Medium-emphasis type, clearly subordinate to Level 1 but not subtle. Placed immediately below Level 1 with a clear but not dramatic spatial separation.

Level 3 — Supporting reasoning:
The strongest factors that explain or support the primary conclusion. The evidence, conditions, or logic that make Level 1 credible.
→ Standard body text. Comfortable reading scale. Not competing with Levels 1 and 2 for the eye's first attention.

Level 4 — Challenges, uncertainty, or contradiction:
What weakens, complicates, or contradicts the primary conclusion. This level receives significant design attention — it must be visible and readable, not buried or suppressed, but it does not compete with the conclusion for primary emphasis.
→ Standard body text. Distinguished by semantic color (amber left-border rule for contradictions) or structural position (placed after supporting reasoning). Acknowledged explicitly by the user when material.

Level 5 — Reference detail:
The evidence, source material, historical records, granular assumptions, and notes that support or elaborate on higher levels. This is the content the user reaches when they want depth, not the content they encounter first.
→ Reduced-emphasis type (secondary or tertiary scale depending on how rarely it is consulted). Often behind expand/collapse. Never in the primary reading path.

Level 6 — System metadata:
Dates, source references, save state, version indicators, system-generated timestamps, confidence labels in their compact form. This content is present and readable but does not draw the eye in any reading context.
→ Smallest text in the system. Metadata scale. Wide letter-spacing, optionally in a distinct technical type variant. Recedes at normal reading distance.

How hierarchy influences each design dimension:

Typography: Each level has a distinct conceptual typographic role. The scale difference between adjacent levels is perceptible but not dramatic — the visual hierarchy reads as a gradient, not a step function.

Spacing: The space between elements at different levels is always greater than the space between elements at the same level. Moving from Level 1 to Level 2 feels like a step down within the same train of thought. Moving from Level 3 to Level 4 feels like a shift in perspective. These transitions are communicated through spacing before any other signal.

Containers: Level 1 permanent records (the Final Decision Card) and Level 1 conclusions that anchor a Workspace (the Current Conclusion card in the Decision Workspace) receive strong containers. Most other content uses subtle separation or no container.

Layout: Level 1 content is full-column, centered in the editorial reading column. Level 5 reference material may be narrower or indented to signal its subordinate nature.

Reading order: The hierarchy defines reading order. The user who reads only Level 1 and Level 2 content understands the essential structure of any Atlas surface. Levels 3, 4, and 5 reward deeper reading.

Responsive behavior: On smaller screens, Level 5 and Level 6 content is more aggressively collapsed or deprioritized. Levels 1 and 2 are always fully visible. Level 4 (contradictions) is never hidden even on mobile — material challenges must remain visible regardless of screen size.

⸻

8. Shared Typography Philosophy

Typography is the primary medium of hierarchy in Atlas. Color and containment are secondary. Spacing is the structure that makes typography legible. The typography system should be expressive through hierarchy — through the relationships between levels — not through variety of styles.

Conceptual typographic roles:

Workspace title (fixed header — investment name or portfolio review):
The identity anchor of the current Workspace. Clearly the largest text in the fixed header. Moderate weight — presence comes from size and position, not from heaviness. Paired with a secondary line (Workspace type, decision type) in a clearly smaller and lighter weight.

Primary conclusion (Level 1 — Workspace body):
The largest body text in the Workspace. This is the statement the user encounters first in the scrolling body. Its weight is moderate, not heavy — authority comes from scale and space, not from typographic mass. Line length is editorial: approximately 65–70 characters.

Section title (section label):
The smallest text in the system in most contexts. Small, uppercase, wide letter-spacing. Reads as punctuation — identifying the section without claiming its prominence. Never dominates the content below it.

Reasoning and long-form body (Levels 2 and 3 — standard Workspace body text):
The primary reading scale. Comfortable size for sustained reading. Line height approximately 1.65–1.7 relative to font size. Line length 65–70 characters. This is the scale at which most Workspace content is read.

Supporting explanation (Atlas-generated body text):
Same scale as reasoning, but in a slightly lighter weight — the perceptible but subtle signal that this content was authored by Atlas, not the user. The weight difference is consistent everywhere Atlas-generated body text appears.

User-authored text (decision fields, primary reason, user-edited content):
Primary text weight — the weight the eye associates with the most important authored content. When a user writes in the decision field, their text is visually dominant over surrounding Atlas-generated context. This is intentional.

Reference detail (Level 5 — supporting assumptions, evidence notes, historical annotation):
Below the standard body scale. Comfortable for deliberate reading but clearly not in the primary reading path. Line height maintained for readability even at reduced scale.

Metadata (Level 6 — timestamps, source labels, confidence labels, version indicators, status labels):
The smallest text in the system. Distinct from body text — either through weight (very light), tracking (wide letter-spacing), or in appropriate contexts a technical typeface variant. Clearly readable at close range; recedes at reading distance.

Status indicators and labels:
Rendered in metadata scale. The label is always accompanied by a textual description — status is never conveyed by the label styling alone.

Historical records:
Same typographic roles as their current equivalents, but rendered in tertiary text color with reduced opacity. The structure of a historical record mirrors the structure of the current equivalent — enabling easy comparison without introducing a new typographic grammar.

Action labels (buttons and link controls):
In body or secondary body scale depending on action hierarchy. Primary action labels are in the same scale as secondary body text — clearly readable, not demanding special typographic treatment of their own. The action hierarchy is communicated through placement and visual weight, not through outsized typography.

Line length: Approximately 65–70 characters for all long-form reading. This applies to body text, reasoning fields, decision statements, and supporting explanations. It is enforced by the content column width. Shorter line lengths (for metadata rows, structured comparisons) are appropriate for tabular content.

Reading rhythm: The typographic hierarchy creates pace. Level 1 (largest scale, most space) causes the eye to pause. Level 2 flows naturally from it. Levels 3 and 4 reward sustained reading. Level 5 rewards deliberate investigation. The user moves through these levels in a natural editorial rhythm — not because they are instructed to, but because the typography guides them.

Weight hierarchy: One primary weight for user-authored content. One slightly lighter weight for Atlas-authored content. One heavier weight (or primary weight at a larger scale) for Level 1 conclusions. One noticeably lighter weight for metadata. Four conceptual weights — more than four would begin to compete rather than clarify.

Capitalization: Section labels use uppercase with wide letter-spacing. All other text uses sentence case. Uppercase is reserved for labels that function as structural markers — never for emphasis within prose.

Typographic restraint: The system uses hierarchy rather than variety. A designer reaching for a new text style should first ask whether an existing style at a different scale or weight would serve the purpose. The number of distinct text styles should be as small as possible while still communicating the full six-level hierarchy.

When a technical typeface is appropriate: Metadata, timestamps, and compact numerical data may use a narrow or monospaced variant — a visual signal that the content is system-generated rather than editorially authored. This distinction reinforces the authorship model without relying on color.

Typography across Dashboard and Workspaces: The Dashboard uses the same typographic roles but applies them at the compact signal density — body text is present but tighter; metadata is proportionally more prominent. The Workspaces use the same roles at the editorial reading density — body text is given room to breathe; metadata recedes further. The roles do not change; the proportional emphasis of each role adjusts for context.

⸻

9. Shared Spacing Philosophy

Spacing in Atlas communicates structure. It is more important than borders, dividers, or containers as a grouping mechanism. The goal is that a user could understand the hierarchy of any Atlas screen in a low-fidelity grayscale rendering, purely from the spatial relationships.

Spacing levels and their purposes:

Workspace margins (outermost padding):
The space between the viewport or overlay edge and the first content element. Large enough to frame the content as a document within a defined space — not cramped against the edges. The margin signals "this is a reading environment."

Inter-section spacing (between one section and the next):
The largest spacing unit within the content body. Its size communicates that the user has arrived somewhere conceptually new. Approximately three to four times the body text line height. When this space is correctly calibrated, sections feel like chapters in a document — distinct enough to be oriented to, connected enough to remain in the same thread.

Intra-section spacing (between content groups within one section):
Approximately half of inter-section spacing. Sufficient to distinguish groups of content without breaking the user's sense of being within one topic. A collapsed section summary, an expanded reasoning block, and a reference link might each be separated by intra-section spacing within their section.

Card padding (internal space within a contained element):
Generous within strong containers (Final Decision Card, Primary Conclusion card) — the space within these cards reinforces their significance and permanence. More compact within subtle containers (assumption rows, alternative rows) — enough to make each row individually readable without padding the list.

Paragraph spacing (between prose paragraphs):
Standard editorial paragraph spacing — approximately one line height. The user's authored text reads as flowing prose, not as a series of discrete entries.

Label-to-content spacing (between a section label and its first content element):
Small — approximately half a line height. The section label is punctuation, not a heading. It identifies the section without requiring breathing room of its own.

Field spacing (between adjacent editable fields):
Sufficient to distinguish fields without creating the sense of a form. If two adjacent fields feel like a form row, the spacing has failed — each field should feel like a distinct authoring moment.

Row spacing (between rows in a list or structured comparison):
Approximately one to one-and-a-half line heights. Each row is individually readable at a glance. Not so loose that the list feels disconnected; not so tight that it feels dense.

Metadata spacing (between metadata items and adjacent body content):
Clear enough that metadata never reads as primary text. The spatial distance between a timestamp and the body text above it signals that the timestamp is annotation, not content.

Action spacing (between an action control and the content it acts on):
Sufficient to prevent accidental activation and to distinguish the action as a control rather than continuation of the text. Primary actions in the footer are spatially separated from body content by the header/footer structure itself.

Where Atlas should feel dense: Signal density (Dashboard). Compact row spacing, minimal card padding, metadata visible but tight. The user can scan many items quickly.

Where Atlas should feel comfortable: Reading density (analytical Workspaces). Standard body spacing, generous intra-section spacing, editorial line length and line height. The user reads at a natural pace.

Where Atlas should feel spacious: Decision density (Final Decision Card vicinity, pre-recording region). Generous card padding, increased inter-section spacing, surrounding whitespace that draws the eye to the commitment moment. The user's focus narrows.

Where Atlas should feel quiet: Historical density (prior records, version history). Reduced emphasis, slightly tighter spacing than reading density — signaling that this content is reference material, not primary reasoning.

⸻

10. Layout Foundations

The shared layout language governs how content is positioned within any Atlas surface. It answers: which content gets a narrow editorial column, which content expands to a wider analytical view, and when structured comparison layouts are appropriate.

Editorial column (default for all long-form content):
The primary content layout for all Workspace reasoning. A single column, horizontally centered within the content area, with a maximum width determined by the reading line-length target (approximately 65–70 characters). Body text, decision statements, primary reasoning, and Atlas-generated conclusions all use the editorial column. This layout signals "this is a document."

Analytical column (for structured data, summaries, and comparison rows):
A slightly wider column — up to approximately 90 characters for data rows — used where structured comparisons, side-by-side labels and values, or multi-field structured rows are appropriate. Assumption rows, before/after consequence rows, and portfolio allocation rows use this layout. The analytical column does not break the document feel — it is an adaptation within the same reading space.

Comparison layout (two-column, for explicit alternatives):
Used only where the content is genuinely comparative — the Opportunity Cost section (decision subject alongside alternatives), the Portfolio Workspace's capital allocation comparison. The two-column layout is not a grid; it is a deliberate side-by-side presentation of content that gains meaning from adjacency. Never used for information that merely exists in parallel — only for content whose meaning depends on comparison.

Full-width structural view:
Used rarely, and only in the Dashboard — where signal items benefit from the full available width for scanability. Not used in reasoning Workspaces, where a full-width layout would disrupt the editorial reading experience.

Overlay Workspace model:
Investment Workspace, Portfolio Workspace, and Decision Workspace all open as overlays above the originating surface. The underlying surface remains visible at the edges. This preserves context — the user knows where they came from — and signals that the Workspace is a focused reasoning environment layered above their existing state. The overlay has a fixed header (Workspace identity and controls), a fixed footer (primary and secondary actions), and a scrolling body (the document content).

Sticky regions:
The fixed header and footer of any Workspace overlay are always visible. Within the scrolling body, no additional elements are made sticky — the user should not feel that controls are following them through the document. The exceptions: the section label may remain briefly visible as the user scrolls through a very long expanded section, as an orientation anchor.

Side reference area:
Not used as a permanent panel. Source references, related assumptions, and linked prior decisions are accessible through inline links and expand/collapse — not through a persistent sidebar. A persistent sidebar would compete with the document reading experience and would present poorly on smaller screens.

Responsive stacking:
On tablet and mobile, the comparison layout collapses to a sequential single-column layout. Each alternative is presented in full before the next begins — the comparison becomes sequential rather than spatial. This preserves the reasoning; only the simultaneous visual comparison is unavailable on smaller screens.

Long-form content behavior:
Long reasoning text flows naturally within the editorial column. No pagination, no read-more truncation for primary content. Expand/collapse is used for sections and for reference detail, not for primary body text.

When each layout is used:
— A single investment thesis → editorial column
— A list of assumptions → analytical column
— Opportunity cost comparison → comparison layout (desktop only)
— Dashboard signals → full-width structural view
— Opening a Workspace → overlay model
— Reviewing prior decisions → editorial column with historical treatment

⸻

11. Workspace Frame

Every Atlas Workspace overlay shares a common structural frame. The frame is the non-scrolling shell within which the document content lives. It should be restrained — minimal enough that the content dominates, present enough that the user is always oriented.

Required areas:

Workspace identity (fixed header, left):
The name of the investment, portfolio entity, or decision subject — the largest text in the header. Adjacent to it, on a secondary line: the Workspace type and decision type if applicable. These two lines orient the user completely. Nothing more is required in this position.

Return or close control (fixed header, right):
A clearly accessible control to close the Workspace or return to the originating surface. Single control. No navigation breadcrumb in the header — the overlay model preserves orientation through the visible underlying surface.

Primary body (scrolling):
The document content — all sections, the full reasoning sequence. This is the dominant area of every Workspace. The frame should occupy as little vertical space as possible at top and bottom to maximize the document area.

Completion region (fixed footer):
The primary action for the Workspace — Record Decision, Complete Review, or the equivalent. The footer contains primary and secondary actions only. It does not contain navigation, settings, or supplementary content.

Optional areas:

Status indicator (fixed header, secondary line):
The current state of the Workspace — Draft, Under Review, Recorded, Monitoring. Present when the state is not the default. Absent when the Workspace is in its normal active state.

Draft or save state (fixed header, very low emphasis):
A quiet unsaved-changes indicator or last-saved timestamp. Visible at metadata scale. Never dominates the header.

Related source link (fixed header or top of body):
A link to the Investment Workspace or Portfolio Workspace from which the Decision Workspace was opened. Present as a compact reference, not as a navigation element.

Historical state indicator (below Workspace identity):
When the Workspace is displaying a prior record or a prior-plus-current comparison, a clear label indicates this. "Reviewing prior decision · [date]." This indicator is in the header, not the body — the user should know the Workspace mode before they begin reading.

Shared behavior across all Workspaces:

The Workspace opens with a smooth entry transition. The underlying surface dims slightly. The overlay settles into place.

Closing the Workspace returns the underlying surface to its previous state — the user's position, any expanded sections, and filters are preserved.

The header does not become a toolbar. It identifies and provides the return control. Everything else lives in the body or footer.

⸻

12. Section Template

Every section in every Atlas Workspace shares a common anatomy. The elements are consistent — what varies is which elements are present in any given section.

Standard section anatomy:

Section label (required):
Small, uppercase, wide-spaced. Identifies the section. Appears at the top of the section, above all other content. This is Level 6 metadata in the information hierarchy — it punctuates the structure, it does not anchor it.

Collapsed summary (required for all collapsible sections):
A two-line maximum summary of the section's current state. Line 1: the headline or primary conclusion for this section. Line 2: the material implication, status, or most important supporting detail. The collapsed summary must communicate meaningfully — a section whose collapsed state says only "SUPPORTING FACTORS · 5 items" has failed this requirement.

Expansion affordance (required for all collapsible sections):
A quiet directional indicator at the right edge of the collapsed header. Its scale is tertiary — it should not draw the eye away from the summary content.

Headline (expanded state):
The primary statement of the section — preserved from the collapsed state and shown at the top of the expanded content. The user does not lose orientation when the section opens.

Body (expanded state):
The full content of the section — reasoning, evidence, comparison, structured rows, or whatever the section type requires. The body uses the appropriate density and layout for its content type.

State or status indicator (optional):
For sections with a meaningful status — an assumption that is "Broken," a contradiction that is "Unresolved," a monitoring condition that has "Triggered" — a small label adjacent to or within the section header. Present only when the state is non-default. Absent in the default state.

Source reference (optional):
A small link or attribution indicating where Atlas's analysis in this section originated. At metadata scale. Present when the source is materially relevant to the user's assessment of the content.

Action or edit affordance (optional):
Where the user may edit, acknowledge, or act within a section, the edit control appears on hover or as a persistent low-emphasis element. It does not occupy space in the primary reading path.

AI suggestion indicator (optional):
A small indicator that Atlas has a suggestion related to this section's content. At tertiary emphasis — visible but not demanding. Appears only after the user has interacted with the section, not on first arrival.

Completion or acknowledgment state (optional):
For sections that require user acknowledgment — a material contradiction, a missing review condition — a small acknowledgment control or status indicator. Present when the section is in an unresolved state. Absent once resolved.

Historical note (optional):
When a section contains content that has changed since a prior decision or prior Atlas analysis, a small indicator notes the change. At metadata scale. Linking to the prior state if the user wants to compare.

Required in all sections: section label, collapsed summary (if collapsible), expansion affordance (if collapsible).
Required in expanded state: headline, body.
All others are optional and context-dependent.

⸻

13. Reading Rhythm

A well-designed Atlas Workspace should be readable from top to bottom without instruction, without a tutorial, and without confusion about what to read next. Reading rhythm is the system property that makes this possible.

The pace of a Workspace:

The Workspace opens and the user's eye lands on the fixed header — Workspace identity, subject. Immediate orientation. Then the scrolling body begins.

The first section of the scrolling body is always the highest-emphasis content in the document — the Current Conclusion, the Thesis Assessment, the Atlas Portfolio Conclusion. This section is visually distinct from everything below it. The user pauses here. They have the essential context before reading anything else.

The sections that follow are read in order — each one moving from conclusion to supporting reasoning to challenges and context. Within each section, the collapsed state provides the headline and implication; the user decides whether to expand. Most users, on most visits, will read the collapsed summaries sequentially before expanding the sections that are most relevant to their current question.

Visual pause points:

There are typically four moments in a full Workspace reading where the document weight naturally causes the eye to slow — these are the high-emphasis moments (equivalent to the Level 1 conclusions listed in the information hierarchy). They are:

1. The opening conclusion — the founding statement of the Workspace.
2. The user decision or proposed decision — the core commitment being formed.
3. The opportunity cost or portfolio consequence synthesis — the moment of comparative understanding.
4. The Final Decision Card — the settled record.

These pauses are not created by animation or forced interaction. They are created by typographic scale, surrounding space, and the visual weight of the content itself. The user experiences them as natural moments of comprehension, not as designed speed bumps.

Section transitions:

The space between sections is the primary transition mechanism. It is large enough that arriving at a new section feels like turning a page — a small but perceptible shift in focus. It is not so large that the document feels disconnected.

Sections do not interrupt each other. A section that is expanded does not push subsequent content out of view in a jarring way — the document reflows smoothly, and the user can continue reading below the expanded content.

The progression toward action:

As the user moves toward the bottom of the Workspace, the document becomes progressively more focused. Earlier sections are analytical and exploratory — the user is building understanding. Later sections are more conclusive — the user is confirming and committing. The final visible content before the footer is the most focused: the Final Decision Card, the recording explanation, and the primary action. At this point, nothing should compete for the user's attention except the decision they are about to record.

⸻

14. Responsive Philosophy

The Atlas responsive strategy preserves reasoning quality across form factors. It does not merely compress the desktop layout onto smaller screens. Different form factors support different reasoning modes, and the design should reflect this.

Desktop:

The primary form factor for all reasoning-intensive activity. Desktop optimizes for deep reading, sustained writing, multi-section comparison, and deliberate reviewing. The editorial column is at its full intended width. Inter-section spacing is at its maximum. The user can work through a full Workspace at a natural pace without accommodation.

Desktop should feel like working at a desk with a well-organized document in front of you. The tools are present but quiet. The writing space is generous. There is room to think.

Tablet:

The primary form factor for full reasoning flow in a portable context. The user can complete every reasoning task — reading, editing, acknowledging, recording — on a tablet. The editorial column narrows to accommodate the reduced screen width. Inter-section spacing reduces by approximately 20% from desktop. The comparison layout collapses to sequential presentation.

Tablet interactions adapt for touch: section headers are fully tappable as rows. Long-form editing fields expand to give the writing context more room. Bottom-sheet panels replace inline panels for collaborative content.

Tablet should feel like reading and annotating a well-structured document on a device that fits in one hand. Not cramped; not inefficient.

Mobile:

The primary form factor for scanning, reviewing, and focused attention on individual sections. The user can complete decision review, monitoring acknowledgment, and lightweight editing on mobile. Complex multi-section reasoning and initial decision recording are better suited to desktop or tablet, but mobile must not block these tasks — it accommodates them with appropriate adaptation.

On mobile, the content column fills the full width minus margins. Section collapsed states are the default — the user expands what they need. Long-form editing opens as a full-screen editing mode so the user writes with the full available screen rather than a cramped field.

Mobile should feel like reading the most important page of a document — clear, focused, and readable without zooming or scrolling horizontally.

Mobile must not become: a compressed desktop dashboard, a data-dense analytics view, or a notification-list experience. The Atlas reasoning quality must be preserved even when the surface is smaller.

⸻

15. Accessibility Foundations

Accessibility in Atlas is a core design property, not an afterthought. Every foundational decision — typography scale, color system, spacing, interactive element sizing — must support accessibility from the moment it is specified.

Typography:
All body text meets a minimum of 15–16px at 1x display scale. Line height of 1.65–1.7 for long-form reading ensures that text with any level of visual accommodation remains legible. No content-carrying text relies on a size below 11px.

Contrast:
All text meets WCAG AA minimum contrast against its background. Primary and secondary text should target WCAG AAA where possible. This applies to all semantic color treatments — an assumption labeled "Broken" in amber must meet contrast requirements against both the primary surface and the elevated container surface. The disabled Record Decision button explanation text, despite its reduced emphasis, must still meet WCAG AA.

Non-color communication:
Every semantic state communicated by color is also communicated by text label, typographic distinction, structural indicator, or position. A monochrome rendering of any Atlas surface must convey the same hierarchy and the same semantic states as the full-color rendering. The assumption status "Broken" is communicated by the label "BROKEN" in metadata scale and by the left-border rule color — either alone is sufficient to understand the state.

Focus visibility:
A consistent focus ring — minimum 2px perimeter in a color with sufficient contrast against both the element and the surrounding surface — appears on all interactive elements during keyboard navigation. The focus ring is suppressed on pointer interaction using `:focus-visible`. No interactive element may be reached by keyboard without a visible focus indicator.

Keyboard navigation:
Every interaction in Atlas must be completeable without a pointer device. Tab order follows the DOM reading order. Expand/collapse operates on Enter or Space. Primary actions are reachable without leaving the tab flow. Keyboard shortcuts are available for the most frequent operations. The full keyboard interaction model is specified in UX-010 for the Decision Workspace and must be extended consistently to all Workspaces.

Screen reader compatibility:
All structural elements — sections, headings, status indicators, expansion states — have appropriate ARIA roles and labels. When a section expands, a screen reader announces the expansion and the new content becomes navigable. When a state changes (assumption marked as Broken, contradiction acknowledged), the change is announced without requiring the user to navigate away and back.

Motion reduction:
When the user's OS is set to prefer reduced motion, all transitions are instantaneous. The only exception is the 400ms post-recording pause in the Decision Workspace — this is a behavioral pause, not a visual animation, and it is preserved. No functional information is conveyed through motion alone.

Touch target sizing:
All interactive elements — section headers, row controls, suggestion affordances, footer actions, assumption acknowledgment controls — have a minimum touch target of 44×44px. Touch targets may extend beyond the visible element boundary through transparent padding. This applies at all breakpoints, not only on mobile.

Reading comfort:
Maximum line length of approximately 65–70 characters for long-form prose. This applies universally — enforced by the content column width, not left to the rendering context.

Accessible authorship identification:
Every piece of Atlas-generated content is identifiable through both visual means (label, typographic weight, position) and non-visual means (ARIA label or role that communicates the content source to screen readers). The user who cannot see should be able to understand "this is Atlas's suggestion" versus "this is my authored text" through the screen reader experience alone.

⸻

16. Foundation Audit

Before this document is considered complete, the following questions should be answered affirmatively for every principle, system, and template it contains:

Does every principle support Atlas's core philosophy (improve decision quality, not decision frequency)?
Yes. Each principle directs the design toward deliberation, transparency, and user judgment. None of the fifteen universal principles rewards activity, urgency, or superficial action.

Does any principle contradict another?
No material contradiction exists. The nearest tension is between Principle 1 (conclusion before detail) and Principle 6 (uncertainty remains visible) — but these operate at different levels: the conclusion is presented first, and the uncertainty that qualifies it appears within the same reading unit rather than being suppressed. The two principles reinforce, rather than oppose, each other.

Do Dashboard and Workspaces feel related?
Yes. The information hierarchy, the typographic role system, the spacing relationships, the semantic color system, and the authorship conventions are identical across both. What differs is density and editability — both of which are explicitly justified by the different cognitive tasks each surface supports.

Can future Workspaces reuse the system without modification?
Yes. The Workspace frame template, section template, information hierarchy, typographic roles, spacing levels, and layout foundations are all defined at the conceptual level — not tied to the specific content of any existing Workspace. A future Review Workspace, Monitoring Workspace, or Comparative Workspace can use these foundations directly.

Does the system remain timeless rather than trend-driven?
The design foundations in this document make no reference to visual trends, current UI fashions, or platform-specific aesthetic conventions. The principles of editorial typography, conclusion-first hierarchy, restrained color, and structure-over-decoration have been foundational to high-quality document design for decades and are likely to remain appropriate for Atlas's use case indefinitely.

⸻

What UX-012A Establishes

The following foundational decisions are now fixed. They govern all current Atlas surfaces and all future Workspace extensions.

Definition of the Atlas Design System: The Design System is the governing language for reasoning structure, communication, hierarchy, interaction, and continuity across Atlas. It is not a UI kit, component library, visual theme, or style guide.

Atlas product philosophy as a design constraint: Improving decision quality (not speed or frequency) is the foundational constraint behind every design principle in the system. The system actively prevents design drift toward urgency, activity optimization, or transaction-oriented aesthetics.

Cross-workspace roles and their governing experiential qualities: Dashboard (observant, selective, scanning); Investment Workspace (investigative, focused); Portfolio Workspace (integrative, strategic); Decision Workspace (deliberate, conclusive). Each role defines the appropriate density, editability, reading depth, and decision weight for that surface.

The Atlas reasoning flow as a product architecture: Signal → Context → Understanding → Analysis → Decision → Monitoring → Memory. Every Workspace occupies a defined position in this flow. Every design decision in each Workspace should serve that position.

Fifteen universal design principles: These govern every Atlas interface. No surface is exempt from any principle. The principles establish: conclusion-first hierarchy, uncertainty visibility, historical immutability, user decision authority, AI as contextual and secondary, context continuity across navigation, visual restraint, and deliberation as the product's defining cognitive mode.

Consistency-versus-variation rules: What is always consistent (terminology, confidence language, authorship distinction, section collapse logic, expansion affordance, spacing relationships, semantic color meanings, keyboard behavior, historical treatment); what may vary by context (density, default expansion, card emphasis, editing presence, comparison layouts, section count and order).

The six-level information hierarchy: Level 1 (primary conclusion), Level 2 (material implication), Level 3 (supporting reasoning), Level 4 (challenges and contradiction), Level 5 (reference detail), Level 6 (metadata). Each level's influence on typography, spacing, containment, layout, reading order, and responsive behavior is fixed.

Shared typography philosophy: Seven conceptual roles (Workspace title, primary conclusion, section label, reasoning/body, supporting explanation, reference detail, metadata); editorial line length (65–70 characters); reading line height (1.65–1.7); four conceptual weight tiers; capitalization convention (uppercase for section labels only); typographic restraint as a governing principle.

Shared spacing philosophy: Six spacing levels (Workspace margins, inter-section, intra-section, card padding, row spacing, metadata spacing); the rule that spacing communicates structure before borders or containers do; density levels (signal, reading, decision, historical) mapped to Workspace contexts.

Layout foundations: Editorial column as the default for all long-form content; analytical column for structured data; comparison layout for genuine two-column alternatives; full-width only for Dashboard signals; overlay Workspace model; no persistent side panels; editorial reading width (65–70 characters) enforced by column constraints.

Workspace frame template: Required areas (Workspace identity, return/close control, scrolling body, completion region footer); optional areas (status indicator, draft/save state, related source link, historical mode indicator); behavioral rules (entry transition, context preservation on close, header restraint).

Section template anatomy: Required elements (section label, collapsed summary for collapsible sections, expansion affordance, headline and body in expanded state); optional elements (status indicator, source reference, edit affordance, AI suggestion indicator, completion/acknowledgment state, historical note).

Reading rhythm principles: Four natural visual pause points per full Workspace; section transitions communicated through spacing rather than animation; progressive narrowing of focus toward the commitment moment; no section should interrupt the reading narrative.

Responsive philosophy: Desktop optimized for deep reading and sustained writing; tablet for full reasoning flow in portable context; mobile for scanning, review, and focused section-by-section reasoning. Mobile preserves decision quality without becoming a compressed dashboard.

Accessibility as a core design property: WCAG AA contrast minimum for all text; non-color communication for all semantic states; 15–16px minimum body text at 1x; 44×44px minimum touch targets; visible focus ring on all keyboard-navigated elements (`:focus-visible`); screen reader labels for authorship, state changes, and expansion events; instantaneous transitions under reduced-motion preference.

⸻

Remaining Foundation Questions

1. Exact type scale values:
This document establishes the typographic roles and their relationships — but the specific pixel values (body text at 15px or 16px? conclusion at 19px or 21px?) depend on the final font family choice and screen rendering context. The font family is established (DM Sans and DM Mono, from UX-011 implementation), but the final size table requires specification under UX-012B or UX-013. This does not block the implementation of UX-012A's principles.
Evidence needed: Type-setting tests at target sizes with the confirmed font family. Does not block implementation.

2. Exact spacing scale values:
The spacing relationships are defined conceptually (inter-section ≈ 3–4× body line height, etc.), but the specific pixel values require calibration against the confirmed type scale. A slight adjustment to the body text size ripples through the whole spacing system.
Evidence needed: Rendered spacing tests at all density levels. Does not block principle adoption; would block detailed component specification in UX-013.

3. Maximum editorial column width in pixels:
The 65–70 character line length target is conceptually fixed. The pixel value depends on the specific font family at the specific body text size. At the confirmed font family (DM Sans) and an approximate body text size of 15–16px, the editorial column width is approximately 560–640px — but this should be confirmed through rendering.
Evidence needed: Rendered column tests. Does not block UX-012B.

4. Whether a light-mode variant of Atlas is a product requirement:
UX-011 establishes Atlas as a dark-mode-first (warm dark) product. This document preserves that position. If a light-mode variant is required, the semantic color system would require a second token tier. This question is a product decision, not a design decision, and it cannot be resolved by this document.
Evidence needed: Product direction decision. Blocks the semantic color token specification if light mode is required.

5. The precise form of the Workspace entry transition:
The overlay Workspace entry is defined as a smooth transition that preserves underlying context. Whether it slides up, fades in, or uses a scale-from-origin approach is not resolved here. This choice affects the emotional first impression of the Workspace and warrants a design decision.
Evidence needed: Motion prototype testing. Does not block UX-012B; should be resolved before UX-013.

⸻

Requirements for UX-012B

UX-012B will cover the reusable component and pattern layer of the Atlas Design System — the second part of the full UX-012 specification. It must establish the following:

Reusable components:
For each component below, UX-012B must define: purpose, required content, optional content, visual emphasis level, interaction behavior, responsive behavior, allowed Workspaces, and prohibited misuse.

— Atlas Conclusion component (the primary conclusion presentation in any Workspace)
— Section Header component (the collapsed state for any collapsible section, including the two-line summary model)
— Challenge Item component (three severity states: informational, material, unresolved — with left-border rule, acknowledgment control, and auto-expansion behavior)
— Assumption Row component (status variants: Holding, Under Review, Weakening, Broken; expand/collapse; linked monitoring condition; comment field)
— Monitoring Condition component (passive monitoring, review trigger, invalidation condition, scheduled review — each as a distinct variant)
— Invalidation Condition component (distinguished from assumption and monitoring; communicates durability and permanence)
— Atlas Suggestion Panel component (trigger, suggestion label, content, reason, accept/partial accept/dismiss controls; inline and below-field variants)
— Final Decision Card component (draft/live-updating state and completed/recorded state; adaptation for embedding in Dashboard and other surfaces)
— Opportunity Cost Comparison component (decision subject row, alternative rows, conclusion line; no-scoring qualitative comparison; desktop full-column and tablet sequential variants)
— Contradiction Item component (three visual states aligned with Challenge Item severity model)
— Historical Decision Record component (tertiary treatment; original wording preservation; timestamp and authorship; amendment relationship)

Card and container variants:
— Primary Conclusion Container (strong framing for the anchor conclusion of any Workspace)
— Final Decision Container (elevated, permanent-record treatment — one of the most visually significant elements in the system)
— Standard Reasoning Container (default treatment for normal analytical sections — often no container at all, relying on spacing)
— Subtle Supporting Container (light background or single left-border rule for lower-emphasis grouped content)
— Comparison Container (the row-level treatment within the Opportunity Cost comparison)
— Contradiction Container (amber left-border rule in three weights, corresponding to severity levels)
— Monitoring Container (the visual treatment that communicates ongoing observation)
— Historical Container (reduced-emphasis treatment for prior records)
— Completion Container (the visual environment around the Record Decision region and Final Decision Card)

Section variants:
Each of the following section types requires a defined anatomy combining the elements from the Section Template (UX-012A Section 12) with the appropriate optional elements:
— Read-only reasoning section (Investment Workspace thesis assessment, portfolio conclusion)
— Editable reasoning section (Decision Workspace primary reason, assumption record)
— Comparison section (Opportunity Cost, capital allocation alternatives)
— Warning or contradiction section (Challenge Items, Contradiction Check)
— Monitoring section (monitoring conditions, review triggers, invalidation conditions)
— Historical section (prior decision display, amendment record, prior conclusion reference)
— Decision section (the decision statement field with Atlas proposal, the primary reason field, the confidence field)
— Completion section (Final Decision Card, Record Decision region, post-recording state)

AI collaboration patterns:
— The Atlas suggestion pattern (one canonical pattern, with inline and below-field variants)
— The partial-accept model (highlighted segments, selection affordance, confirmation state)
— The "Atlas suggests" label system (consistent form, scale, and placement across all surfaces)
— The collaboration panel (the expanded AI collaboration context for complex refinement requests; bottom-sheet on tablet/mobile)

Editing patterns:
— Inactive, hover, focused, edited, and read-only states for all field types
— Atlas-generated, Atlas-suggested, user-modified, and locked-historical states
— Short statement fields, long-form reasoning fields, selector fields, qualitative choice fields

State and status system:
— The full state vocabulary for Atlas objects (decisions, assumptions, monitoring conditions, evidence, Workspaces)
— Visual and textual treatment for each state
— Rules for which states are mutually exclusive

Monitoring and trigger system:
— The anatomy of a monitoring condition across all Workspaces
— The visual distinction between passive monitoring, review triggers, invalidation conditions, and scheduled reviews
— How monitoring transitions to a Dashboard signal

History and version system:
— The visual treatment of prior records, amendments, superseded decisions, and current active records
— The version history panel anatomy
— Rules for historical content that is never silently modified

Completion patterns:
— The completion gate model (what prevents recording; how blocking conditions are communicated)
— The post-recording state (Final Decision Card prominence, confirmation line, next steps)
— The completion experience in review mode (closing a review versus closing an initial decision)

Reusable Workspace patterns:
— Six template types: Monitoring Workspace, Analytical Workspace, Comparative Workspace, Portfolio Workspace, Decision Workspace, Review Workspace
— For each: entry context, conclusion placement, section hierarchy, editability, expansion behavior, completion behavior, history behavior

Do not produce UX-012B yet.

# UX-012 — Atlas Design System & Workspace Consistency Specification

Version 1.0 — Final Governing Document
Assembled from UX-012A (Foundations), UX-012B (Components & Reusable Patterns), UX-012C (Interaction, Navigation & Responsive Behavior), UX-012D (Governance, Tokens & Evolution), and all previously approved Atlas UX specifications.

This is the single authoritative reference for every future Atlas interface, component, interaction, visual pattern, and governance decision. Every future Workspace, component, interaction, and visual pattern derives from this specification. All prior part documents (012A–D) are superseded by this assembled version.

---

# Canonical Glossary

Before any specification, one vocabulary. The following terms are established once and used consistently throughout.

**Workspace** — A full-screen Atlas surface dedicated to a specific reasoning purpose. Not a screen, page, or view. Examples: Dashboard, Investment Workspace, Portfolio Workspace, Decision Workspace.

**Section** — A named content area within a Workspace, representing one discrete step in the reasoning structure. Not a card, block, panel, or module.

**Component** — A reusable UI element with a defined semantic purpose, states, and interaction behavior. Not a widget, element, or control.

**Pattern** — A reusable combination of components, sections, or behaviors that together represent a recurring reasoning structure. Not a template or layout.

**Token** — A named design variable representing a semantic value in typography, spacing, color, motion, or interaction. Not a style, variable, or setting.

**Conclusion** — The primary output of a reasoning step or Workspace: the thing Atlas or the user concludes is true, required, or recommended. Not a summary, result, or outcome.

**Decision** — A specific user-authored commitment to a course of action, recorded permanently. Not a conclusion, recommendation, or outcome.

**Recorded Decision** — A Decision that has been formally submitted and converted to immutable historical content. Not a saved draft or completed form.

**Historical Record** — Immutable content from any prior event (decision, review, reasoning session) preserved for permanent reference. Not an archive, log, or version.

**Monitoring** — Active tracking of conditions that could affect a prior Decision, triggering review when thresholds are crossed. Not alerts, notifications, or reminders.

**Monitoring Condition** — A specific trackable condition established at Decision time that has a defined threshold and lifecycle. Not a flag or alert.

**Review** — A scheduled or triggered re-examination of a prior Decision in light of new information. Not monitoring, checking, or revisiting.

**AI Collaboration** — The relationship between Atlas AI suggestions and user reasoning. Atlas suggests; the user decides. Not AI assistance, AI features, or AI automation.

**Atlas Suggestion** — AI-generated content offered as optional input to user reasoning. Not a recommendation, answer, or output.

**Authorship** — The visible, meaningful contribution of a user to their reasoning and decisions. Typography, layout, and surface together communicate that the user has authored something.

**Contradiction** — A logical inconsistency between two or more reasoning elements, detected automatically or manually flagged.

**Opportunity Cost** — The explicit representation of what is foregone by pursuing a chosen course of action.

**Workspace Transition** — Movement between Workspaces, preserving context and reasoning continuity.

**Draft** — User-authored content that has not been recorded. Recoverable, autosaved, and persistently labeled.

**Immutable** — Content that cannot be edited, deleted, or modified under any circumstances.

**Semantic Token** — A token named for its meaning rather than its visual value (e.g., `conclusion.text` not `off-white`).

**Maturity** — The governance stage of a component, pattern, or token: experimental → candidate → stable → deprecated → retired.

---

# Part I: Philosophy & Foundations

## 1. What Atlas Is

Atlas is a reasoning environment for high-stakes financial decisions. It supports the full arc of investment thinking: observing signals, building context, analyzing opportunity, weighing consequences, committing to decisions, monitoring outcomes, and learning from history.

Atlas is not a dashboard product. It is not a trading platform. It is not a financial news reader. It is not a portfolio tracker. It is a deliberate reasoning environment whose primary output is a Recorded Decision and whose primary resource is the quality of the user's thinking.

Every interface choice in Atlas should support reasoning quality over speed, depth over density, and authorship over automation.

## 2. Atlas Product Philosophy as Design Constraint

The Atlas product philosophy is not an aspiration. It is a constraint on every design decision.

**Reasoning over action.** Atlas does not optimize for speed of execution. It optimizes for quality of reasoning. An interface that helps a user think more clearly is always preferred over one that helps them act more quickly.

**Conclusion precedes detail.** Every Workspace and Section presents its conclusion first. Supporting evidence, reasoning, and detail follow. Users should never need to read to the bottom to understand what something means.

**History is permanent.** No recorded content is ever modified, overwritten, or deleted. Atlas treats historical content as the user's most valuable asset.

**Users own decisions.** Atlas AI supports reasoning. It never makes decisions. The Recorded Decision is always user-authored, even when Atlas suggested content that the user accepted.

**Context is preserved.** Atlas never loses the user's place, draft, or reasoning context. Navigation preserves everything.

**Accessibility is fundamental.** Atlas is designed for all users at all times. Accessibility is not an accommodation. It is a design requirement.

## 3. The Atlas Reasoning Flow

Atlas supports a structured reasoning arc. This arc is not a rigid workflow; it is the natural sequence of investor thinking that Atlas makes visible and navigable.

**Signal** — An observation, data point, or trigger that warrants attention. (Primary surface: Dashboard)

**Context** — The background, history, and conditions that give a Signal meaning. (Primary surface: Investment Workspace)

**Understanding** — The synthesis of Context into a coherent picture of an investment situation. (Primary surface: Investment Workspace)

**Analysis** — The structured examination of opportunity, risk, comparison, and consequence. (Primary surface: Investment Workspace, Portfolio Workspace)

**Decision** — The deliberate commitment to a course of action, with full reasoning recorded. (Primary surface: Decision Workspace)

**Monitoring** — Active tracking of conditions that validate or challenge the Decision. (Primary surface: Decision Workspace, Dashboard)

**Memory** — The permanent historical record of decisions, reviews, and reasoning, accessible for future reference. (Primary surface: Historical Record, Dashboard)

This flow governs the navigation structure, the component hierarchy, and the information architecture of every Atlas Workspace.

## 4. The Four Atlas Workspaces

**Dashboard**
Role: observant, selective, scanning.
Purpose: surface actionable Signals, provide portfolio status, enable navigation to all Workspaces.
Primary output: identification of what requires attention.
Cognitive mode: monitoring, filtering.

**Investment Workspace**
Role: investigative, focused, analytical.
Purpose: develop deep understanding of a single investment — its history, position, reasoning, challenges, and opportunity.
Primary output: understanding sufficient to justify a decision.
Cognitive mode: reading, analyzing, comparing.

**Portfolio Workspace**
Role: integrative, strategic, comparative.
Purpose: examine relationships between holdings, assess allocation consequences, evaluate portfolio-level opportunity and risk.
Primary output: portfolio-level understanding that informs decision priorities.
Cognitive mode: comparing, weighing, integrating.

**Decision Workspace**
Role: deliberate, conclusive, authoritative.
Purpose: structure the full reasoning chain for a specific decision, surface contradictions and consequences, record the final decision with full provenance.
Primary output: a Recorded Decision with complete reasoning.
Cognitive mode: deliberating, committing, recording.

## 5. The Six-Level Information Hierarchy

All Atlas content occupies one of six levels. This hierarchy governs typography weight, position, size, and visual emphasis. It applies universally across all Workspaces and all contexts.

**Level 1 — Primary Conclusion**
The single most important piece of information in a Workspace or Section. Presented at the top, in the largest weight. One per Workspace or major Section.

**Level 2 — Structural Element**
Section headings, Category labels, Named areas of a Workspace. Communicate what a region is for.

**Level 3 — Supporting Narrative**
Primary body text. The substance of reasoning, context, and analysis. Comfortable reading weight and line height.

**Level 4 — Contextual Information**
Secondary text — timestamps, sources, metadata, annotations. Present but not dominant.

**Level 5 — Reference Content**
Tertiary text — historical content labels, collapsed section previews, supporting references. Visually quiet.

**Level 6 — System Metadata**
Version numbers, identifiers, system-generated labels. Visible only when needed.

## 6. The Fifteen Universal Design Principles

These principles govern every Atlas design decision without exception.

1. **Reasoning first.** Every interface element exists to support the user's reasoning process. If it does not support reasoning, it does not belong.

2. **Conclusion before detail.** Primary conclusions appear before supporting evidence. Users orient before they investigate.

3. **Authorship is visible.** The user's contribution to reasoning is typographically and spatially distinguished. Atlas content and user content are never visually equivalent.

4. **AI remains secondary.** Atlas suggestions appear below the user's primary reasoning, in a visually distinct and dismissible form. They never occupy structural positions.

5. **History is immutable.** Nothing recorded is changed. Historical content is permanently locked, permanently accessible, and permanently labeled as historical.

6. **Context is preserved.** Navigation never destroys state. Drafts, scroll positions, expanded sections, and reasoning context are recovered on return.

7. **Hierarchy is honest.** Visual hierarchy reflects information importance. Nothing is styled to appear more important than it is.

8. **Motion serves meaning.** Animation clarifies transitions and state changes. It never celebrates, entertains, or creates urgency.

9. **Consistency begins with meaning.** Two elements look the same because they mean the same thing. They look different because they mean different things.

10. **Accessibility is structural.** Contrast, focus management, screen reader support, and reduced motion are designed into the system, not retrofitted.

11. **Restraint over novelty.** A familiar pattern that works is preferred over a novel pattern that might. New visual treatments require semantic justification.

12. **Editing is authorship.** Text input feels like writing, not form completion. Long-form fields use editorial typography and proportions.

13. **Completion is calm.** Recording a Decision is a significant moment. It is communicated with quiet precision, not celebration or fanfare.

14. **Every new component requires justification.** A component is introduced only when it represents a genuinely recurring semantic pattern that no existing component can serve.

15. **Future Workspaces inherit before inventing.** New Workspaces extend existing templates, patterns, and components. They introduce new concepts only when existing vocabulary is demonstrably insufficient.

## 7. Consistency Versus Variation

Some Atlas elements must be absolutely consistent across every context. Others vary by Workspace or context with justification.

**Always consistent across all Workspaces:**
- Information hierarchy levels and their visual representation
- Typography roles, weights, and line heights
- Color semantics (what each color communicates)
- Motion token behaviors and easing characteristics
- Interaction token states and their visual treatments
- Focus indicator appearance and behavior
- Historical content treatment (locked, labeled, reduced opacity)
- Accessibility requirements (contrast, touch targets, focus order)
- AI Suggestion appearance and interaction model
- Draft indicator appearance and behavior
- Navigation return patterns
- Completion interaction pattern
- Empty state communication model

**Varies by Workspace (with justification):**
- Section content and sequence (each Workspace has a different reasoning structure)
- Primary Conclusion framing (each Workspace produces a different type of conclusion)
- Editing availability (Decision Workspace has extensive authoring; Dashboard has none)
- Comparison layouts (Portfolio and Decision Workspaces present comparisons differently)
- Monitoring visibility (not present in all Workspaces at the same level)
- Section density (Dashboard is higher density than Decision Workspace)

---

# Part II: Typography, Spacing & Layout

## 8. Typography System

Atlas typography communicates hierarchy and meaning through weight, size, and spacing — not through color or decoration.

**Seven Typographic Roles:**

**Role 1 — Primary Conclusion**
Used for: the central conclusion of a Workspace or Section.
Character: authoritative, settled, readable at a glance.
Weight: heavy. Line height: 1.2–1.3. Size: large.

**Role 2 — Section Heading**
Used for: named Sections within a Workspace.
Character: clear, structural, directional.
Weight: medium-heavy. Line height: 1.3. Size: medium-large.

**Role 3 — Body Narrative**
Used for: primary reasoning text, context, analysis, and explanation.
Character: readable, editorial, unhurried.
Weight: regular. Line height: 1.65–1.7. Size: medium.
Line length: 65–70 characters per line in reading columns.

**Role 4 — Supporting Label**
Used for: field labels, category names, section sub-labels, metadata headings.
Character: quiet, structural, not primary.
Weight: medium. Line height: 1.4. Size: small-medium.
Letter-spacing: slightly open.

**Role 5 — Contextual Text**
Used for: timestamps, source references, metadata values, annotation text.
Character: present but subordinate.
Weight: regular. Line height: 1.5. Size: small.

**Role 6 — Historical Text**
Used for: all content within Historical Records.
Character: readable but visually receded.
Weight: regular. Opacity: reduced (approximately 70%). Size: small-medium.
Permanently accompanied by the Historical label.

**Role 7 — System Text**
Used for: identifiers, version labels, system status, technical metadata.
Character: functional, mechanical.
Weight: regular. Family: monospace. Size: small.

**Four Weight Tiers:**
Heavy — Primary Conclusions, significant labels.
Medium-Heavy — Section Headings, named areas.
Medium — Supporting Labels, category names.
Regular — Body Narrative, Contextual Text, Historical Text.

**Capitalization Rules:**
Section headings: Title Case.
Body text: Sentence case.
Labels: Sentence case (never ALL CAPS in primary content).
System metadata: lowercase acceptable.
Decision field labels: Sentence case, consistent with body.

**Typeface:**
Primary: DM Sans or equivalent humanist sans-serif. Used for all non-monospace content.
Secondary: DM Mono or equivalent monospace. Used for System Text, identifiers, and technical values.

## 9. Spacing System

Atlas spacing communicates structure. Consistent spacing makes hierarchy legible without requiring visual separators.

**Six Spacing Levels:**
Level 1 — Minimal: between closely related inline elements.
Level 2 — Tight: between a label and its value; within a compact component.
Level 3 — Component: between sections of a component; default internal padding.
Level 4 — Section: between Sections within a Workspace. The primary structural separator.
Level 5 — Region: between major areas of a Workspace (e.g., header from body).
Level 6 — Workspace: external padding of a Workspace from the viewport edge.

**Four Density Contexts:**
Dense — Dashboard, monitoring feeds, metadata rows.
Standard — Investment Workspace, Portfolio Workspace body.
Generous — Decision Workspace reading sections.
Editorial — Long-form editing fields, narrative body text.

Spacing does not change to indicate importance. It changes to indicate relationship. Closer elements are more closely related.

## 10. Layout Foundations

**Editorial Column**
Used when: reading and writing narrative. A column sized for comfortable reading (65–70 characters). The primary layout for Decision Workspace body sections, Investment Workspace context sections, and all long-form editing.

**Analytical Column**
Used when: displaying structured data, comparisons, or side-by-side reasoning. A wider column with internal grid for structured alignment. The primary layout for comparison sections and data-heavy Investment Workspace sections.

**Comparison Layout**
Two or more columns of equivalent width presenting parallel information. Used for Before/After, Opportunity Cost, Alternative Comparison, and Scenario Comparison.

**Overlay Model**
Historical Records, Monitoring detail, and related Workspace context are presented in overlays that preserve the underlying Workspace. Overlays do not navigate away from the primary Workspace.

## 11. Workspace Frame Template

Every Atlas Workspace is built on this template. Required elements must appear in every Workspace. Optional elements appear when the Workspace requires them.

**Required:**
- Workspace identity area (name of the Workspace and its subject)
- Return navigation (path back to Dashboard or source)
- Primary Conclusion or Workspace status
- Body (the Workspace-specific section sequence)
- Footer area (primary action, completion indicator, or monitoring status)

**Optional:**
- Draft indicator (present whenever unsaved user content exists)
- Historical indicator (present when viewing or comparing historical content)
- Progress indicator (present in completion-oriented Workspaces)
- Monitoring status (present when active Monitoring Conditions exist)
- Related Workspace links (contextual navigation to related reasoning)

## 12. Section Template Anatomy

Every Atlas Section uses this structure. Required elements appear in every Section. Optional elements appear when the Section requires them.

**Required:**
- Section heading (Role 2 typography)
- Primary content (the conclusion, reasoning, or interactive area)

**Optional:**
- Section summary (visible when collapsed; communicates the Section's current state)
- Expansion control (for Sections that can be expanded or collapsed)
- Section status indicator (draft, updated, historical, monitoring-triggered)
- AI Suggestion area (when Atlas has relevant input)
- Section actions (inline actions relevant to this Section)
- Timestamps and source attribution
- Section footnote or assumption disclosure

## 13. Reading Rhythm

Reading flow in Atlas follows a natural editorial progression. Four structural pause points mark transitions between phases of reasoning.

**Pause Point 1 — After Primary Conclusion**
Before beginning supporting reasoning. Space and weight differential communicate: this is the conclusion; what follows explains it.

**Pause Point 2 — Between Reasoning Regions**
Between distinct phases (e.g., between Supporting Factors and Challenges). Section-level spacing creates a legible boundary.

**Pause Point 3 — Before User Decision Area**
The transition from read-dominated to write-dominated space. Increased vertical space and a subtle visual signal communicate: authorship begins here.

**Pause Point 4 — Before Completion**
The boundary between reasoning and commitment. The completion area is visually separated from the reasoning body to signal the gravity of recording a Decision.

Section transitions use subtle horizontal rules or increased vertical spacing, never color fills or graphic dividers. Reading progression is natural and sequential. Sections are designed to be read top to bottom; users who have reviewed a Workspace before may navigate directly to areas of interest.

---

# Part III: The Four Workspaces

## 14. Dashboard

**Purpose:** Surface Signals requiring attention, show portfolio status, enable navigation to active reasoning.
**Cognitive mode:** scanning, monitoring, filtering.
**Primary output:** identification of what requires attention and navigation to the appropriate Workspace.

**Structure:**
The Dashboard presents a scanning surface, not an investigative one. Information density is higher here than in reasoning Workspaces. Conclusions are compressed to single lines or short labels. Expanded reasoning belongs in a Workspace, not the Dashboard.

**Required areas:**
- Portfolio status summary (Level 1 conclusion: overall state)
- Active Monitoring Conditions (any triggered or approaching thresholds)
- Recent Decisions summary (accessible, not dominant)
- Signals list (items requiring attention, ordered by relevance or recency)
- Navigation to all active Workspaces

**Interaction character:**
Primarily navigational. The Dashboard is a launching point. Actions are minimal — primarily "open" and "dismiss." Editing is not available on the Dashboard.

**Spacing and density:** Dense. Dashboard sections use tight spacing, compact components, and compressed conclusions.

## 15. Investment Workspace

**Purpose:** Develop deep understanding of a single investment — its history, position, reasoning, challenges, and opportunity.
**Cognitive mode:** reading, analyzing, comparing.
**Primary output:** understanding sufficient to justify a decision.

**Reasoning sequence:**
1. Current Conclusion (what Atlas understands about the investment now)
2. What Changed (recent developments worth reviewing)
3. Investment Context (background, history, position)
4. Supporting Factors (reasons the investment may perform as expected)
5. Challenges (reasons it may not)
6. Assumptions (conditions on which the reasoning depends)
7. Opportunity (specific opportunity the investment represents)
8. Monitoring (active conditions)
9. Related Decisions (Decisions made about this investment)

**Primary authorship:** User can annotate and edit narrative fields. Investment Workspace supports lighter authorship than Decision Workspace.

**Spacing and density:** Standard. Reading sections use editorial line lengths. Analysis sections use analytical column.

## 16. Portfolio Workspace

**Purpose:** Examine relationships between holdings, assess allocation consequences, evaluate portfolio-level opportunity and risk.
**Cognitive mode:** comparing, weighing, integrating.
**Primary output:** portfolio-level understanding that informs decision priorities.

**Reasoning sequence:**
1. Portfolio Conclusion (overall portfolio state)
2. Allocation Overview (current allocation versus targets)
3. Holdings Comparison (comparative view of current positions)
4. Opportunity Assessment (portfolio-level opportunity and risk)
5. Consequences (what changes to individual positions mean for the whole)
6. Portfolio Monitoring (portfolio-level conditions)

**Comparison layouts:** Portfolio Workspace uses Comparison layouts extensively. Before/After, Allocation Comparison, and Scenario Comparison components are used here more than in any other Workspace.

**Spacing and density:** Standard to Generous. Comparison sections use wider layouts; narrative sections use editorial column.

## 17. Decision Workspace

**Purpose:** Structure the full reasoning chain for a specific decision, surface contradictions and consequences, record the final Decision with full provenance.
**Cognitive mode:** deliberating, committing, recording.
**Primary output:** a Recorded Decision with complete reasoning.

**Reasoning sequence:**
1. Current Conclusion (what the reasoning currently points to)
2. Decision Required (the specific choice that must be made)
3. What Changed (what triggered this decision moment)
4. Supporting Factors (reasons for the proposed action)
5. Challenges (reasons against; contradictions surfaced here)
6. Assumptions (the conditions this reasoning depends on)
7. Portfolio Consequences (what this decision means for the portfolio)
8. Opportunity Cost (what is foregone by this decision)
9. Implementation (how the decision would be executed)
10. Review Conditions (what should trigger re-examination)
11. Proposed Decision (the structured statement of intent)
12. Final Decision Card (the completion form; appears after Proposed Decision is authored)
13. Record Decision (the submission action)

**Primary authorship:** Decision Workspace is the primary authoring environment in Atlas. Every Section with a user-editable field uses editorial typography, document-like proportions, and authorship visual treatments.

**Spacing and density:** Generous. Reading sections use full editorial column and line heights. The Final Decision Card uses the most deliberate spacing in the system.

**Completion behavior:** Recording a Decision is the primary completion act. It is communicated with a calm 400ms transition, conversion of all content to Historical Record status, and persistent confirmation. Not with animation, celebration, or fanfare.

## 18. Future Workspace Governance

Every new Atlas Workspace must answer seven questions before design begins:

1. What question does it solve that no existing Workspace can answer?
2. What reasoning role does it serve in the Atlas reasoning flow (Signal/Context/Understanding/Analysis/Decision/Monitoring/Memory)?
3. What context does it inherit from other Workspaces?
4. What conclusion does it produce?
5. How does its conclusion feed future reasoning?
6. Which existing components does it use?
7. Which new patterns, if any, does it require — and why can no existing pattern serve?

New Workspaces extend existing templates, patterns, and components. They do not reinvent the visual language, interaction model, or information hierarchy.

---

# Part IV: Components & Reusable Patterns

## 19. Component Philosophy

An Atlas component is not a visual element. It is a recurring semantic pattern — a UI element whose purpose, meaning, states, and behavior are defined once and applied consistently wherever that meaning occurs.

A component is justified only when:
- It represents a recurring reasoning structure (not just a repeated visual)
- Its purpose cannot be served by an existing component
- Its purpose will recur in at least two Workspaces or contexts
- It can be fully specified with states, relationships, and content rules

Five required characteristics of every Atlas component:
**Clarity** — Its purpose is immediately apparent from its content and position.
**Restraint** — It contains only what is necessary for its semantic purpose.
**Predictability** — It behaves identically in every context where it appears.
**Editorial quality** — Its typography, spacing, and proportion meet Atlas standards.
**Accessibility** — It meets WCAG AA requirements in every state.

## 20. Workspace Components

**Workspace Frame**
Purpose: The outer container of every Atlas Workspace. Establishes identity, navigation, and layout structure.
Required elements: identity area, return navigation, body, footer.
Optional elements: draft indicator, historical indicator, progress indicator, monitoring status, related Workspace links.
States: default, draft-present, historical-viewing, monitoring-triggered, loading.
Reuse: all Workspaces.

**Workspace Header**
Purpose: Identifies the Workspace and its subject; provides primary navigation controls.
Required elements: Workspace name, subject identity (investment name, portfolio name, decision topic), return navigation control.
Optional elements: status indicator, timestamp, monitoring badge.
States: default, monitoring-active, draft-present, historical-mode.
Reuse: all Workspaces.

**Return Navigation**
Purpose: Provides clear path back to Dashboard or source context.
Required elements: destination label, navigation control.
Behavior: appears consistently in the same position in every Workspace. Preserves context on return (scroll position, draft, expanded state).
States: default, hover, focused.
Reuse: all Workspaces.

**Draft Indicator**
Purpose: Communicates that unsaved user content exists. Persistent until content is saved or discarded.
Required elements: label ("Draft"), timestamp of last autosave.
Position: in the Workspace Header, adjacent to identity.
States: draft-present, autosaving, save-failed.
Reuse: all Workspaces with editable content (Investment Workspace, Decision Workspace).

**Historical Indicator**
Purpose: Communicates that the user is viewing historical content. Persistent in the Header throughout the historical viewing session.
Required elements: label ("Historical Record"), date of historical record.
Behavior: all editable controls are disabled while Historical Indicator is present. Editing historical content is not permitted.
Reuse: all Workspaces with historical content.

## 21. Section Components

All Section components share the Section Template Anatomy (heading, content, optional elements). Each specialization adds behavioral constraints.

**Standard Section**
The baseline Section type. Used when no specialized behavior is required.
Heading, body content, optional expansion, optional Atlas Suggestion area.
Reuse: all Workspaces.

**Reasoning Section**
Used for narrative reasoning content: Supporting Factors, Challenges, Assumptions, Context, Analysis.
Characteristics: editorial line length (65–70 chars), generous line height, no inline data tables.
Always: includes heading, allows expansion, shows summary when collapsed.
Reuse: Investment Workspace, Decision Workspace.

**Read-Only Section**
Used for Atlas-generated or historical content that the user cannot edit.
Visual indicator: no editing controls, subtle read-only treatment, no cursor change on hover.
Reuse: all Workspaces.

**Editable Section**
Used for user-authored content. Uses Long-form Editor or Decision Field components internally.
Visual indicator: field area shows document-like edit invitation (not form-like border boxes) on hover.
States: inactive, hover, focused, editing, saved, atlas-generated, user-modified.
Reuse: Investment Workspace (light authorship), Decision Workspace (primary authorship).

**Comparison Section**
Used for side-by-side reasoning, Before/After, and alternative evaluation.
Layout: Comparison Layout (parallel columns).
Must contain: at least two parallel content areas with equivalent structure.
Reuse: Portfolio Workspace, Decision Workspace.

**Decision Section**
Used for the Proposed Decision and Final Decision Card areas.
Characteristics: most generous spacing in the system, strongest typographic weight for the user's Decision statement, visible completion gate behavior.
Reuse: Decision Workspace (primary), Review Workspace (future).

**Historical Section**
Used for displaying content from a Historical Record within a current Workspace context.
Characteristics: reduced opacity, Historical label, all editing disabled, timestamp prominent.
Always: wrapped in or adjacent to the Historical Indicator.
Reuse: all Workspaces.

**Completion Section**
Used for the Record Decision area and post-completion state.
Characteristics: maximum visual separation from body sections (Pause Point 4), deliberate spacing, primary action prominently placed.
Reuse: Decision Workspace, Review Workspace (future).

## 22. Conclusion Components

**Primary Conclusion**
Purpose: The single most important conclusion in a Workspace or the result of a completed reasoning process.
Position: top of the Workspace body, immediately below the Header.
Typography: Level 1.
Behavior: always visible; does not collapse.
Reuse: all Workspaces.

**Current Conclusion**
Purpose: Atlas's current understanding of the investment or situation — a live, updated summary that reflects the current state of reasoning.
Distinction from Primary Conclusion: the Current Conclusion updates as the user reasons; the Primary Conclusion is the settled output.
Position: within the reasoning sequence, before supporting detail.
States: initial, updated (subtle Update token), atlas-generated, user-modified.
Reuse: Investment Workspace, Decision Workspace.

**Decision Required**
Purpose: Frames the specific choice the user must make. Sets the decision question.
Position: immediately after or alongside Current Conclusion in Decision Workspace.
Characteristic: the decision question is stated clearly and specifically. Not vague or open-ended.
Reuse: Decision Workspace (primary).

**What Changed**
Purpose: Surfaces recent developments relevant to the current reasoning session.
Position: after the Current Conclusion, before the full reasoning body.
Behavior: optional; present only when there are relevant recent changes.
States: present, empty (with informative empty state label).
Reuse: Investment Workspace, Decision Workspace.

**Portfolio Conclusion**
Purpose: The integration of individual investment reasoning into a portfolio-level understanding.
Position: top of Portfolio Workspace body.
Reuse: Portfolio Workspace (primary).

**Review Conclusion**
Purpose: The conclusion produced by a Review — what the review determined about the continued validity of a prior Decision.
Position: top of Historical Review, displayed alongside the original Decision.
Reuse: Historical Review (future Workspace), Decision Workspace review mode.

## 23. Reasoning Components

**Supporting Factors**
Purpose: Reasons that support the reasoning direction or proposed Decision.
Structure: a list of named factors, each with a brief explanation. Not bullet points — named, weighed elements.
States: default, atlas-suggested, user-authored, weakening (when contradicted), removed.
Reuse: Investment Workspace, Decision Workspace.

**Challenges**
Purpose: Reasons that complicate, contradict, or argue against the reasoning direction.
Three severity levels, communicated with a left-border visual treatment:
- Informational challenge: a relevant concern that does not invalidate the reasoning.
- Material challenge: a concern that requires explicit acknowledgment in the Decision.
- Blocking challenge: a concern that must be resolved or explicitly overridden before the Decision can be recorded.
Reuse: Investment Workspace, Decision Workspace.

**Assumptions**
Purpose: The conditions on which the current reasoning depends. Making assumptions explicit forces honest reasoning.
Four status states:
- Holding: assumption is considered valid.
- Under Review: assumption is being re-examined.
- Weakening: assumption has become less reliable.
- Broken: assumption is no longer valid; reasoning that depended on it requires revision.
Behavior: a Broken Assumption triggers a Contradiction in the Decision Workspace.
Reuse: Investment Workspace, Decision Workspace.

**Invalidation Condition**
Purpose: A specific future condition that, if true, would invalidate the current reasoning or Decision.
Character: stated precisely and specifically. Not "if the market changes" but "if revenue growth falls below 8% in two consecutive quarters."
Reuse: Decision Workspace (required field in Final Decision Card), Investment Workspace (optional).

**Portfolio Consequences**
Purpose: What the Decision means for the portfolio — allocation changes, risk exposure changes, relationship to other holdings.
Position: within Decision Workspace reasoning sequence; after individual-investment analysis.
Reuse: Decision Workspace (primary), Portfolio Workspace (contextual).

**Opportunity Cost**
Purpose: An explicit representation of what is foregone by pursuing the chosen course of action.
This is a signature Atlas component. It makes the cost of a Decision visible. It prevents the user from evaluating an opportunity in isolation.
Structure: what is pursued, what is given up, explicit comparison of the two.
Reuse: Decision Workspace (primary), Portfolio Workspace (contextual).

**Implementation Summary**
Purpose: A brief description of how the Decision would be executed.
Required: the record, not the plan — what will be done, not how it will be managed operationally.
Reuse: Decision Workspace (required in Final Decision Card).

**Review Condition**
Purpose: The specific condition under which the Decision should be formally reviewed. Establishes the schedule and trigger for the Monitoring phase.
Required in Final Decision Card.
Reuse: Decision Workspace.

## 24. Comparison Components

**Before/After**
Purpose: Explicit comparison of the current state and the proposed state.
Layout: parallel columns with equal visual weight.
Reuse: Decision Workspace, Portfolio Workspace.

**Alternative Comparison**
Purpose: Structured comparison between two or more investment options.
Layout: parallel columns; consistent row structure for each compared attribute.
Reuse: Decision Workspace, Investment Workspace.

**Opportunity Cost Component** (distinct from Opportunity Cost section)
Purpose: The structured visual representation of the opportunity cost calculation.
Layout: what is chosen versus what is foregone, with explicit comparison framing.
This is a signature visual element. It should be visually distinct and clearly labeled.
Reuse: Decision Workspace (required).

**Scenario Comparison**
Purpose: Comparison of potential outcomes under different conditions or assumptions.
Layout: parallel columns; row-per-scenario structure.
Reuse: Investment Workspace, Decision Workspace.

**Allocation Comparison**
Purpose: Visual representation of portfolio allocation before and after a proposed Decision.
Layout: parallel representations of portfolio composition.
Reuse: Portfolio Workspace (primary).

**Historical Comparison**
Purpose: Side-by-side view of current reasoning and a Historical Record.
Behavior: Historical content is always displayed with the Historical Indicator. Current content is in the standard editable state.
Reuse: Decision Workspace (review mode), Investment Workspace.

## 25. Decision Components

**Proposed Decision**
Purpose: The user's stated intention, written in their own words before it is formalized in the Final Decision Card.
Character: free-form, authored, the user's own language. Not a form. Not a template.
Behavior: the Proposed Decision is the primary authorship moment before completion. Its content flows into the Final Decision Card.
States: empty, drafting, authored, atlas-suggested, user-modified.
Reuse: Decision Workspace.

**Final Decision Card** *(signature component)*
Purpose: The structured, permanent record of a Decision with full reasoning provenance.
Six required fields:
1. Decision — the core commitment in the user's words.
2. Primary Reason — the single most important reason for this Decision.
3. Confidence — the user's stated confidence level (not a gauge or percentage; a qualitative statement).
4. Invalidation Condition — the specific condition that would invalidate this Decision.
5. Implementation Intent — how and when the Decision will be acted upon.
6. Review Condition — when and under what conditions the Decision should be reviewed.

Two states:
- Draft/Live-Updating: fields are editable; content flows from the Proposed Decision and reasoning sections.
- Completed/Recorded: all fields are locked and converted to Historical content. The card is permanently labeled with the recording timestamp and is immutable.

Reuse: Decision Workspace (primary); Review Workspace (historical reference).

**Decision Summary**
Purpose: A condensed, portable version of a Recorded Decision for display in other contexts (Dashboard, Investment Workspace, Portfolio Workspace).
Contains: decision statement, primary reason, recording date, confidence level.
Behavior: read-only; clicking navigates to the full Historical Record.
Reuse: Dashboard, Investment Workspace, Portfolio Workspace, Historical timeline.

**Decision History**
Purpose: A chronological list of Recorded Decisions related to the current Workspace subject.
Behavior: each entry is a Decision Summary; clicking expands to the full Historical Record.
States: default, expanded, selected.
Reuse: Investment Workspace, Portfolio Workspace.

**Decision Amendment**
Purpose: Formally links a new Decision to a prior one, with explicit documentation of what changed and why.
Character: amendments do not modify the original Decision. They are additive historical records.
Reuse: Decision Workspace (for amendment-type decisions).

**Decision Review**
Purpose: The formal re-examination of a prior Decision in light of new information.
Output: Review Conclusion — the determination of whether the original Decision remains valid.
Reuse: Decision Workspace (review mode), future Review Workspace.

## 26. Monitoring Components

**Monitoring Condition**
Purpose: A single trackable condition that determines whether a Decision remains valid.
Lifecycle: Established → Active → Approaching (threshold near) → Triggered (threshold crossed) → Acknowledged → Resolved.
Required elements: condition name, threshold definition, current status, monitoring start date.
Behavior: Approaching and Triggered states surface to the Dashboard and may generate Atlas Warnings.
Reuse: Decision Workspace (establishment), Dashboard (status), Investment Workspace (contextual display).

**Review Trigger**
Purpose: Communicates that a Review Condition has been met and a formal Review is required.
Position: prominently placed in the Dashboard and Investment Workspace.
Behavior: navigates to Decision Review mode in the relevant Workspace.
States: pending, acknowledged, resolved.

**Invalidation Trigger**
Purpose: Communicates that an Invalidation Condition has been met.
Severity: higher than Review Trigger. Requires immediate acknowledgment.
Behavior: requires the user to explicitly acknowledge the Invalidation and initiate a new reasoning process.
States: triggered, acknowledged.

**Implementation Follow-up**
Purpose: Tracks whether the Implementation Intent from a Recorded Decision was executed.
States: pending, confirmed, modified, cancelled.
Reuse: Dashboard (monitoring), Decision Workspace (historical reference).

**Scheduled Review**
Purpose: A time-based review trigger defined at Decision time.
Behavior: surfaces in the Dashboard at the scheduled time as a Review Trigger.
Reuse: Decision Workspace (establishment), Dashboard (surfacing).

## 27. Historical Components

All Historical components share three permanent characteristics:
- Reduced opacity (approximately 70% of standard text opacity)
- Permanently locked (no editing controls appear; no cursor change on hover)
- Timestamp always visible

**Historical Record**
Purpose: The base component for any immutable recorded content.
Always accompanied by: the Historical Indicator in the Workspace Header.
States: default, selected, expanded, compared.
Reuse: all Workspaces with historical content.

**Historical Decision**
Purpose: A Historical Record of a Recorded Decision in full — all six Final Decision Card fields, recorded timestamp, and full reasoning provenance.
Reuse: Investment Workspace, Decision Workspace, Dashboard.

**Historical Review**
Purpose: A Historical Record of a completed Review — Review Conclusion, comparison with original Decision, reviewer notes.
Reuse: Investment Workspace, Decision Workspace.

**Historical Assumption**
Purpose: A Historical Record of an Assumption as it existed at a prior point in time — used for comparison during a Review.
Reuse: Decision Workspace (review mode), Investment Workspace.

**Historical Timeline Entry**
Purpose: A single entry in a chronological timeline of historical events for a subject.
Content: event type, timestamp, brief summary, link to full Historical Record.
Reuse: Investment Workspace, Portfolio Workspace, Decision Workspace.

## 28. AI Collaboration Components

**Atlas Suggestion**
Purpose: AI-generated content offered as optional input to user reasoning. Never mandatory. Never primary.
Appearance: visually distinct from user content (different surface treatment, labeled as Atlas Suggestion). Always positioned secondary to or below the relevant user-authored area.
Trigger: surfaces after a 1.5-second pause in user editing — never interrupts active typing.
Three responses:
- Accept: the Suggestion's content populates the relevant field. User is credited as author. Atlas is credited as source.
- Partial Accept: the Suggestion appears in an editable state; user modifies before accepting.
- Dismiss: the Suggestion is removed for the session. Dismissed Suggestions are not shown again in the current session.
Structural Undo: 5-second window to undo the structural effect of an accepted Suggestion.
Reuse: all Workspaces where user authorship occurs.

**Atlas Insight**
Purpose: A contextual observation from Atlas that does not require user action. Informational.
Position: within the relevant Section, below primary content.
States: default, acknowledged.
Reuse: Investment Workspace, Decision Workspace.

**Atlas Warning**
Purpose: A concern identified by Atlas that warrants user attention.
Three severity levels matching Challenges: Informational, Material, Blocking.
Position: within the relevant Section (Informational, Material) or at the Section boundary (Blocking).
Behavior: Blocking Warnings create a soft gate on the completion action.
Reuse: Decision Workspace (primary), Investment Workspace.

**Atlas Recommendation**
Purpose: A specific action or direction recommended by Atlas, with explicit reasoning.
Distinction from Atlas Suggestion: a Recommendation suggests what to do; a Suggestion contributes content.
Position: within a relevant Conclusion component or as a standalone Atlas component.
States: pending, accepted, dismissed, acted-upon.
Reuse: Dashboard, Investment Workspace, Decision Workspace.

**Atlas Clarification**
Purpose: A question from Atlas seeking additional context that would improve the quality of its Suggestions and Insights.
Character: optional, lightweight, easily dismissed. Never blocks reasoning.
States: pending, answered, dismissed.
Reuse: Decision Workspace (primary).

**Atlas Summary**
Purpose: A structured summary of the current reasoning state, generated by Atlas to help the user orient.
Position: top of the Workspace or within a designated Summary area.
Behavior: the user can replace any part of the Atlas Summary with their own authored content.
Reuse: Investment Workspace, Decision Workspace.

## 29. Editing Components

**Long-Form Editor**
Purpose: Primary text editing environment for narrative reasoning content.
Character: document-like, not form-like. Full-width within the editorial column. Proportions suggest writing, not data entry.
Eight states: inactive (displays content, no edit controls), hover (subtle edit invitation), focused (cursor placed, content highlighted), editing (user actively typing), saved (content autosaved, brief confirmation), atlas-generated (content has Atlas origin, labeled), user-modified (previously Atlas-generated, now user-edited — label updates), read-only (no editing possible; used in Historical Sections and read-only Workspaces).
Autosave: every 30 seconds. Draft Indicator updates on each autosave.
Reuse: Decision Workspace (primary), Investment Workspace (secondary).

**Short Statement**
Purpose: A brief, single-line or two-line text field for concise user statements.
Used for: decision titles, assumption statements, condition names.
Character: same document-like visual language as Long-Form Editor, compressed.
States: same eight states as Long-Form Editor.
Reuse: all Workspaces with authoring.

**Decision Field** *(signature component)*
Purpose: The primary editing component for the six Final Decision Card fields.
Character: the most deliberate editing experience in Atlas. Generous padding. Strong typography. Clear label. The field communicates the weight of what is being authored.
States: empty (with instructive placeholder), drafting, authored, validated, invalid, locked (once Recorded).
Validation: soft, deferred. Appears on blur, not while typing. Two fields are required for completion: the Decision statement and the Primary Reason.
Reuse: Decision Workspace (Final Decision Card).

**Structured Comparison Editor**
Purpose: Editing interface for Comparison Section content — allows the user to author both sides of a comparison.
Structure: parallel editing areas with consistent label rows.
Reuse: Decision Workspace, Portfolio Workspace.

**Assumption Editor**
Purpose: Specialized editing interface for Assumptions — includes the assumption statement, status control, and invalidation condition.
States: inherited from Assumptions component (Holding, Under Review, Weakening, Broken).
Reuse: Investment Workspace, Decision Workspace.

**Implementation Editor**
Purpose: Editing interface for the Implementation Intent field.
Character: free-form, authored, document-like. Not a structured form.
Reuse: Decision Workspace.

## 30. State Components

All Atlas states are semantic — they communicate meaning, not appearance. These thirteen states are named consistently and their visual treatments are defined in the Semantic Token Model.

| State | Semantic Meaning |
|-------|-----------------|
| Hover | Interactive; the element can be engaged |
| Pressed | The element is being activated |
| Focused | The element has keyboard or programmatic focus |
| Selected | The element is chosen within a selection context |
| Disabled | The element cannot be interacted with in the current context |
| Editing | The element is in an active authoring state |
| Expanded | The Section or element is fully revealed |
| Collapsed | The Section or element is summarized |
| Loading | Data or content is being fetched or processed |
| Saved | Content has been autosaved successfully |
| Unsaved | Content has been modified since last save |
| Updated | Content has changed since last user review |
| Historical | Content is from a Historical Record; immutable |
| Acknowledged | A trigger, warning, or insight has been seen |

## 31. Feedback Components

**Informational** — Neutral information that does not require action.
**Reminder** — A gentle prompt to return to something.
**Warning** — A concern that warrants attention but does not block.
**Material Concern** — A significant concern requiring explicit acknowledgment.
**Blocking Issue** — A condition that must be resolved before proceeding.
**Validation** — Confirmation that content meets requirements.
**Loading** — Communication of background processing.
**Empty State** — Communication when a Section or area has no content.

Four empty state subtypes:
- Expected empty (No contradictions found — positive)
- Informational empty (No monitoring conditions established yet)
- Action-required empty (Decision not yet authored)
- Error empty (Data unavailable)

## 32. Action Components

**Primary Action** — The single most important action available in the current context. One per Workspace at a time. Completion trigger, submission, or navigation.

**Secondary Action** — Supporting action that does not advance the primary workflow. Typically: preview, compare, export, share.

**Inline Action** — Action available within a Section or component. Does not navigate away.

**Section Action** — Action that applies to an entire Section. Positioned within the Section, not the global Footer.

**Completion Action** — The specific action that records a Decision or completes a significant step. Visually the most prominent action. Preceded by the completion gate check.

**Destructive/History-Altering Action** — Any action that modifies or removes content. Requires explicit confirmation. Never ambiguous. Always labeled with what it does ("Delete this draft" not "Delete").

## 33. Metadata Components

**Timestamp** — When something was created, modified, or recorded. Present on all Historical content.
**Source** — The origin of information (data source, Atlas, user, imported).
**Confidence** — A qualitative statement of reasoning confidence. Never a percentage or gauge.
**Status** — The current lifecycle stage of a component or record.
**Author** — User attribution on authored content.
**Version** — Document or component version identifier.
**Relationship** — A named link between two Atlas records (e.g., "Amends Decision from 2024-03-15").
**Monitoring State** — The current lifecycle stage of a Monitoring Condition.

---

# Part V: Interaction & Navigation

## 34. Interaction Philosophy

Atlas interaction serves reasoning. Every interaction decision is evaluated against one question: does this help the user think more clearly?

Five governing principles:
1. Interaction reduces uncertainty. It never creates it.
2. Context is never lost. Navigation preserves every dimension of user state.
3. Behavior is predictable. The same gesture in the same type of element always produces the same result.
4. The interface is calm. Motion, feedback, and state changes are measured and purposeful.
5. Users stay oriented. At all times, users know where they are, where they came from, and what they can do next.

Atlas interaction differs from comparable software in specific ways:
- Unlike consumer apps: no notifications, no engagement mechanics, no streak indicators, no activity feeds.
- Unlike brokerage platforms: no real-time price animation, no urgency indicators, no trade-now calls to action.
- Unlike enterprise software: no complex permission flows, no toolbar overload, no modal dialog chains.
- Unlike AI chat: AI content is supplementary and secondary, not primary. The user speaks first.

## 35. Navigation Philosophy

Navigation in Atlas supports continuous reasoning. The user's journey across Workspaces is part of their thinking process, not an interruption.

Three questions users always know the answer to:
1. Where am I?
2. Where did I come from?
3. Where can I go from here?

Nine elements preserved across every navigation event:
- Scroll position (restored on return)
- Expanded Section state (restored on return)
- Draft content (autosaved and recovered)
- Workspace context (investment, portfolio, decision subject)
- Selected investment or holding
- Portfolio context
- Decision context and reasoning state
- Active filters and selection criteria
- History viewing state

Navigation never destroys reasoning. A user who navigates to a related Workspace and returns finds their work exactly as they left it.

## 36. Workspace Navigation

**Open Workspace** — Navigates to the specified Workspace, initializing it with the relevant subject context. Scroll position begins at the top. Expanded state uses session defaults.

**Close Workspace** — Returns to the Dashboard or the last Dashboard state. Preserves draft content with autosave.

**Return to Dashboard** — Available from every Workspace, always in the same position. Returns to Dashboard maintaining last Dashboard state.

**Return to Source** — Returns to the Workspace that originated the current navigation. Scroll position and state restored.

**Open Related Workspace** — Opens a related Workspace (e.g., Portfolio Workspace from Investment Workspace) in the same window. Current Workspace state preserved for return.

**Open Historical Record** — Opens the Historical Record in an overlay. The underlying Workspace is visible and preserved. Historical Indicator appears in the Header.

**Open Monitoring** — Opens monitoring detail for a specific Monitoring Condition. Available from Dashboard and Investment Workspace.

**Deep-link Behavior** — Deep-linked Workspaces initialize fully, loading the required subject context. Return navigation goes to the Dashboard (no source Workspace available from external link).

**Browser History** — Forward and back navigation in the browser are honored for Workspace-level navigation. Sub-Workspace navigation (expansion, scroll, selection) is not recorded in browser history.

## 37. Reading Flow

Atlas content is designed to be read top to bottom. Section sequence within each Workspace follows the reasoning flow from conclusion to supporting detail to decision.

Scroll behavior: continuous vertical scroll. No pagination within a Workspace. Scroll velocity naturally decelerates as the user approaches the four Pause Points.

Scroll position is restored precisely on return to a Workspace. Users are not returned to the top; they resume where they were.

Auto-scroll behavior (for Completion and Atlas events) uses the Navigate motion token — orientation-preserving, not disruptive.

## 38. Expansion and Collapse

Collapsed Sections communicate: purpose (heading), summary (one-line state), and status (draft/updated/historical indicator).

Expanded Sections reveal: full reasoning, structure, editing controls, and relationships.

The entire Section heading row is the tap/click target for expansion. Section content is never the tap target for expansion.

Four automatic expansion triggers:
- Newly added content (the Section containing new content expands)
- Atlas Warning at Material or Blocking severity (the relevant Section expands)
- Returning to a Workspace with a section the user was editing (that Section expands)
- Contradiction detected involving a Section (that Section expands)

All expansion decisions are explained. Users are not surprised by automatic expansion.

State is persistent within a session. If the user collapses a Section and navigates away, the Section is collapsed on return. Default states are defined per Workspace; user overrides persist per session.

Expansion and collapse use the Expand and Collapse motion tokens.

## 39. Focus Management

Focus is never lost. The governing rule for every focus decision.

**Keyboard focus:** Full keyboard navigation. Tab moves through interactive elements in reading order. Shift+Tab reverses. Arrow keys navigate within components (lists, comparisons, options).

**Mouse focus:** Click or tap activates and focuses the target element. Focus indicator appears for keyboard users (`:focus-visible`, not `:focus`).

**Touch focus:** Touch targets are a minimum of 44×44px. Touch devices require persistent alternatives to hover-only interactions.

**Programmatic focus:** When content changes, focus moves to the most relevant new element. When a Section expands automatically, focus does not move (the user did not initiate it). When the user completes an action, focus moves to the next logical element.

**Workspace transitions:** Focus moves to the Workspace Header on navigation. On return, focus is restored to the last focused element if recoverable; otherwise to the Workspace Header.

**Editing:** Focus moves to the editing field on edit initiation. On save or completion, focus returns to the parent component.

**Validation:** When validation messages appear, focus moves to the first invalid field.

## 40. Hover Behavior

Hover communicates interactive, editable, expandable, or linked.

Never rely on hover alone. Every interaction available on hover must also be available without hover.

Element-specific hover behavior:
- Sections: subtle background change, expansion control becomes visible.
- Editing fields: edit invitation appears (document-like, not form-like border).
- Actions: standard pressed-ready state.
- Historical content: no hover effect (immutable).
- Disabled elements: no hover effect.

Touch devices: hover equivalents are achieved through persistent controls, tap-to-reveal, or long-press.

## 41. Selection Model

Six selection contexts, each with distinct visual treatment:

**Selected Investment** — The investment whose Workspace is currently open. Shown in Dashboard investment list.
**Selected Section** — The Section currently receiving keyboard focus for navigation.
**Selected Comparison** — The comparison column or row currently selected for detail.
**Selected Decision** — The Decision whose historical record is currently being viewed.
**Selected Monitoring Item** — The Monitoring Condition currently expanded in a monitoring list.
**Selected Historical Record** — The Historical Record currently open in overlay.

Selection is never implied. The selected state is visually clear in every context.

## 42. Motion Philosophy

Motion in Atlas orients, clarifies, connects, and reduces confusion. It never celebrates, gamifies, or creates urgency.

Three motion contexts where animation is used:
1. **Workspace transitions** — to communicate movement between contexts.
2. **State transitions** — to communicate that something changed and what the new state is.
3. **Structural changes** — to communicate expansion, collapse, insertion, and removal of content.

Motion is never used for:
- Attracting attention to something the user has not initiated.
- Celebrating completion (no confetti, no particle effects, no bouncing).
- Indicating urgency or time pressure.
- Adding character, personality, or delight at the expense of clarity.

**Reduced Motion:** All motion behavior respects the user's operating system reduced-motion preference. Every motion token has a reduced-motion fallback (instant state change or a simple opacity crossfade).

## 43. The Twelve Motion Tokens

| Token | Character | Applied To |
|-------|-----------|------------|
| Open | Gentle reveal from slightly smaller | Workspace entrance, overlay appearance |
| Close | Fade-and-compress | Workspace exit, overlay dismissal |
| Expand | Smooth height increase, content fades in | Section expansion |
| Collapse | Content fades out, height decreases | Section collapse |
| Highlight | Subtle background pulse, one cycle | Updated content, Atlas-flagged item |
| Fade | Opacity to/from zero | Secondary transitions, dismissal |
| Replace | Crossfade between two states | State changes within a component |
| Insert | Slides into position, companion content shifts | New item added to a list |
| Remove | Fades and contracts, companion content fills | Item removed from a list |
| Navigate | Directional movement | Auto-scroll, position changes |
| Update | Brief visual marker, then settles | Content that has changed |
| Loading | Steady, subtle skeleton or placeholder | Loading states |

## 44. The Fourteen Interaction Tokens

| Token | Semantic Meaning | Visual Treatment |
|-------|-----------------|-----------------|
| hover | Interactive; ready for engagement | Subtle background shift |
| pressed | Being activated | Slightly compressed or darkened |
| focused | Has keyboard focus | Focus ring (`:focus-visible`) |
| selected | Chosen within selection context | Clear selected background |
| disabled | Not available in current context | Reduced opacity; no cursor change |
| editing | Active authoring state | Cursor visible; editing indicator |
| expanded | Fully revealed | Collapse control visible |
| collapsed | Summarized | Expand control visible; summary shown |
| loading | Data being fetched | Loading token animation |
| saved | Autosave successful | Brief confirmation label |
| unsaved | Modified since last save | Draft Indicator active |
| updated | Changed since last user review | Update token, then settled |
| historical | From a Historical Record; immutable | Reduced opacity; timestamp; locked |
| acknowledged | Trigger or insight has been seen | Acknowledged visual marker |

## 45. Editing Behavior

Autosave: every 30 seconds while editing. Draft Indicator updates on each save cycle.

Structural Undo: a 5-second undo window is available after any structural change (Atlas Suggestion accepted, comparison added, assumption deleted). The undo window does not apply to routine typing.

Validation: soft, deferred. Appears on blur from a field, not while typing. Required field validation surfaces only at the completion gate, not before.

Historical locking: all editing controls are disabled while the Historical Indicator is present. Users cannot edit historical content under any circumstances.

Mobile editing: full-screen editing mode on mobile — the Workspace body is replaced with the editing surface; done/save returns to the Workspace.

## 46. AI Interaction

The governing principle: Atlas suggests; the user decides.

AI Suggestions surface after a 1.5-second pause in user editing. They never interrupt active typing. They never appear unsolicited in areas the user has not engaged with.

Three responses are always available: Accept, Partial Accept, Dismiss. These three controls are always visible when an Atlas Suggestion is present.

Session-scoped Dismiss: a dismissed Suggestion does not reappear in the current session. Atlas does not re-suggest the same content after explicit dismissal.

Structural Undo: 5-second window after Accept. The user can undo the acceptance and return to their prior authored state.

AI content attribution: when Atlas Suggestion content is accepted, the field is labeled "Atlas suggested / User accepted." When the user subsequently modifies it, the label updates to "User authored."

## 47. Loading Behavior

All loading states use the Loading motion token — a steady, non-theatrical placeholder that communicates processing without urgency.

300ms minimum: loading states that resolve in under 300ms do not show the loading animation (prevents flash).

Extended loading (beyond 3 seconds): a brief explanatory label appears ("Loading investment history").

Background processing (beyond 10 seconds): a persistent indicator in the Workspace Header communicates ongoing background work. The rest of the Workspace remains usable.

Failed loading: the last known state of the content is preserved. An error empty state communicates what could not be loaded and provides a retry action.

## 48. Validation Behavior

Validation in Atlas is soft and deferred. It does not interrupt reasoning. It appears at the right moment.

Soft validation: field-level validation appears on blur (when the user leaves the field). Not while typing.

Completion gate: two fields are required before a Decision can be recorded — the Decision statement and the Primary Reason. The completion action communicates this requirement clearly before the user attempts to submit.

Contradiction severity:
- Informational: a highlighted note within the relevant Section. Does not block.
- Material: a Warning component in the relevant Section. Requires acknowledgment (not resolution) to proceed.
- Blocking: prevents the completion action until resolved or explicitly overridden with documented reason.

## 49. Error Behavior

Six error types, each with distinct communication:

**Technical error** — System failure unrelated to user content. Communication: brief inline message, retry action. Work is preserved.

**Unavailable data** — A data source is temporarily inaccessible. Communication: empty state in the affected area with explanation. Rest of Workspace functions normally.

**Connection error** — Network unavailability. Communication: persistent indicator in Header. Autosave attempts are queued.

**Permission error** — User lacks access to requested content. Communication: clear explanation of why the content is unavailable. No broken states.

**Missing source** — A referenced record or investment no longer exists. Communication: the reference is preserved with a "Source unavailable" label. Historical content that cited the source is not altered.

**Incomplete calculation** — Atlas cannot complete an analysis due to missing inputs. Communication: partial results shown with a clear indication of what is missing and why.

Preservation of work is non-negotiable across all error types. No error condition results in loss of user-authored content.

## 50. Completion Behavior

Completion is the most deliberate moment in Atlas. It is not celebrated. It is confirmed.

Completion gate check: before the Record Decision action is activated, the system verifies that the two required fields are complete. Any Blocking Issues are surfaced. If requirements are unmet, the completion action communicates what is needed — it does not silently fail.

400ms pause: when all requirements are met and the user activates the Record Decision action, a 400ms pause precedes the transition to the recorded state. This pause is not theatrical; it gives the interface time to settle into the transition.

Workspace conversion: after recording, the entire Decision Workspace body converts to Historical content. The Draft Indicator is removed. The Historical Indicator appears. All editing controls are removed.

Post-completion state: the Workspace remains visible as a Historical Record. The user can navigate away naturally. The Dashboard will reflect the new Monitoring Conditions. The Historical Record is immediately accessible.

## 51. History Interaction

Historical Records are opened in overlays that preserve the underlying Workspace.

Timeline navigation: Historical Records can be navigated chronologically (earlier/later) within the overlay.

Comparison: the current Workspace state can be compared with a Historical Record using the Historical Comparison component. Both states are visible simultaneously.

Return: closing the Historical overlay returns to the exact state of the underlying Workspace.

Historical locking: all editing is disabled in Historical mode. This is absolute. No override is possible.

Version navigation: within a Historical Record, the full provenance of each field is accessible — each change is attributed and timestamped.

Relationship navigation: Historical Records that reference other records (amendments, reviews) provide navigation to those records.

## 52. Monitoring Interaction

Monitoring Conditions are established as part of the Decision recording process. They are not added separately after recording.

**Trigger surface:** Dashboard (primary for Approaching and Triggered states), Investment Workspace (contextual).

**Status review:** each Monitoring Condition's current lifecycle stage is visible in its component.

**Review:** when a Review Condition is met (Triggered state), the Review Trigger component appears in the Dashboard and Investment Workspace. The user navigates to Decision Review mode.

**Dismiss:** a Monitoring Condition can be dismissed from the Approaching or Triggered state. Dismissal requires explicit confirmation and documentation ("Why are you dismissing this condition?"). Dismissed Conditions move to the Acknowledged state and are recorded in the Historical timeline.

**Resolve:** Monitoring Conditions are resolved through a formal Review or by explicit resolution with documentation. Resolution is permanent and recorded historically.

## 53. Cross-Workspace Consistency

Fourteen interaction behaviors are identical across all Workspaces:

1. Return navigation position and behavior
2. Draft Indicator appearance and behavior
3. Historical Indicator appearance and behavior
4. Autosave timing and Draft Indicator update
5. Expansion and collapse gesture (full heading row)
6. Focus ring appearance (`:focus-visible`)
7. Minimum touch target (44×44px)
8. Atlas Suggestion appearance, timing (1.5s), and three-response model
9. Loading token behavior and timing thresholds
10. Historical content treatment (reduced opacity, locked, timestamped)
11. Empty state communication model (four subtypes)
12. Completion action visual treatment (most prominent action)
13. Structural Undo (5-second window)
14. Reduced motion compliance

Three justified variations across Workspaces:
- Section sequence and content (each Workspace has a different reasoning structure)
- Editing availability and depth (Decision Workspace has deepest authoring)
- Monitoring prominence (most prominent in Decision Workspace and Dashboard)

---

# Part VI: Design Tokens

## 54. Design Token Philosophy

Atlas uses semantic design tokens — named variables whose names describe meaning, not appearance.

Semantic tokens decouple meaning from implementation. When the visual implementation changes (a color is adjusted, a typeface is updated), the semantic token name remains stable. Code that references `conclusion.text` continues to express the right meaning even if the specific color value changes.

Fifteen token categories govern the Atlas visual and interaction language:

**Typography** — font families, weights, sizes, line heights, letter spacing, editorial column width.
**Spacing** — six spacing levels, four density contexts.
**Layout** — column widths, grid parameters, overlay dimensions.
**Semantic Colors** — colors named by meaning, not by value.
**Surface** — background colors for each surface tier.
**Borders** — border colors, widths, and radius values.
**Elevation** — shadow values for elevation tiers.
**Radius** — border radius values for components.
**Icons** — icon size tiers, stroke weights.
**Motion** — the twelve motion tokens (easing, timing range, reduced-motion fallback).
**Focus** — focus ring thickness, offset, color.
**Interaction** — the fourteen interaction state tokens.
**Accessibility** — minimum contrast ratios, minimum touch target sizes, focus indicator specifications.
**Responsive** — breakpoint definitions, density transitions.
**State** — the thirteen semantic state tokens and their visual representations.

## 55. Semantic Token Model

Semantic tokens are organized by meaning group. Each group represents a distinct reasoning concept in Atlas.

**Primary Conclusion** — Tokens for the central conclusion of a Workspace or Section. Text, background, border.

**Supporting Reasoning** — Tokens for supporting narrative, analysis, and context. Text, secondary text.

**User Authored** — Tokens for content the user has written. Text, field background, editing state.

**Historical Content** — Tokens for all Historical Records. Text opacity, background, lock indicator, timestamp.

**Monitoring** — Tokens for Monitoring Condition states. Text for each lifecycle stage (Established, Active, Approaching, Triggered, Acknowledged, Resolved).

**Decision** — Tokens for Decision-specific content. Proposed Decision text, Final Decision Card field, Recorded state.

**Opportunity** — Tokens for Opportunity and Opportunity Cost components. Opportunity text, foregone text, comparison framing.

**Contradiction** — Tokens for Contradictions and Challenges at three severity levels. Informational, Material, Blocking — each with border, text, and background tokens.

**Warning** — Tokens for Atlas Warnings at three severity levels. Matches Contradiction severity naming.

**Completed** — Tokens for the post-recording state. Visual treatment of completed Decisions.

**Disabled** — Tokens for disabled states. Opacity, cursor, interaction indicators.

**Loading** — Tokens for loading states. Skeleton background, animation timing.

**Focus** — Tokens for focus indicators. Ring color, width, offset.

## 56. Naming Conventions

All Atlas design artifacts follow meaning-based naming. Names describe what something is, not what it looks like.

**Components:** 2–3 words describing the product object. Examples: `FinalDecisionCard`, `MonitoringCondition`, `AtlasSuggestion`, `OpportunityCost`.

**Tokens:** `category.role.variant`. Examples: `conclusion.text.primary`, `contradiction.border.blocking`, `motion.expand.duration`.

**Actions:** `Verb + Noun`. Examples: `RecordDecision`, `DismissSuggestion`, `AcknowledgeTrigger`, `OpenWorkspace`.

**Sections:** Named by reasoning purpose. Examples: `SupportingFactors`, `Assumptions`, `OpportunityCost`, `ReviewCondition`.

**States:** Named by condition. Examples: `draft-present`, `monitoring-triggered`, `historically-locked`.

Twelve prohibited naming styles:
1. Color-based names (`red-warning`, `green-success`)
2. Position-based names (`top-card`, `left-panel`)
3. Size-based names (`big-text`, `small-button`)
4. Generic names (`card`, `box`, `container`, `item`)
5. Abbreviations without expansion (`sec`, `comp`, `hist`)
6. Numbered variants without semantic distinction (`Card1`, `Card2`)
7. Platform-specific names (`mobile-view`, `desktop-layout`)
8. Appearance-based names (`rounded-card`, `bordered-section`)
9. Action-receiver names (`clickable`, `tappable`)
10. Status codes (`status200`, `errorState3`)
11. Component-implementation names (`flex-container`, `grid-row`)
12. Temporary names (`temp-card`, `new-component`)

---

# Part VII: Governance & Evolution

## 57. Governance Philosophy

Design System governance exists to prevent coherent design from fragmenting as a product grows. Atlas's governance model is built on three beliefs:

**Coherence is product quality.** When Atlas behaves consistently, users reason more confidently. Every inconsistency is a tax on reasoning quality.

**Semantic consistency matters more than visual consistency.** Two components that look similar but mean different things create confusion. Two components that look different but mean the same thing create redundancy. Naming and meaning must be consistent first; visual consistency follows.

**Governance is not implementation.** The Design System defines what Atlas is and how it behaves. It does not specify how components are built in code. Implementation governance (naming, token mapping, documentation) is defined; build strategy is not.

## 58. Component Governance

**Ownership:** Every component has a named owner — the person or team responsible for its specification, documentation, and evolution.

**Approval process:**
1. Semantic proposal: what does this component mean? Why doesn't an existing component serve this meaning?
2. Usage evidence: in which Workspaces or contexts will this recur?
3. Specification draft: full component specification including states, relationships, content rules, accessibility behavior.
4. Design review: review against the five component characteristics (clarity, restraint, predictability, editorial quality, accessibility).
5. Approval and documentation: the component is added to the Atlas Component Inventory at experimental maturity.

**Maturity stages:** experimental → candidate → stable → deprecated → retired.
- Experimental: in active design and testing. May change significantly.
- Candidate: specification is stable; implementation is being evaluated.
- Stable: approved for use in all new and existing Workspaces.
- Deprecated: to be replaced; use is discouraged for new work.
- Retired: removed; replacement is documented and available.

**Versioning:** semantic versioning (major.minor.patch).
- Major: breaking change to component behavior, states, or required content.
- Minor: backward-compatible addition (new optional element, new state).
- Patch: documentation update, clarification, accessibility improvement.

**Deprecation sequence:** Deprecated status announced with replacement documented → Stable replacement promoted → Migration guidance provided → Deprecated component marked "do not use for new work" → Retired after migration completion verified.

## 59. Pattern Governance

A pattern is approved only when:
- It represents a recurring combination of components that serves a recurring reasoning need.
- The combination occurs in at least two Workspaces or contexts.
- No existing pattern can serve the need.
- The pattern has clear ownership and full documentation.

Seven pattern categories (each governed separately): Reasoning, Comparison, Decision, Monitoring, Historical, AI Collaboration, Completion.

Maturity stages: draft → candidate → stable → deprecated → retired (same definitions as components).

## 60. Workspace Governance

Every new Atlas Workspace is approved through the seven-question review process (Section 18). This review is mandatory. No new Workspace begins design without completing it.

The Workspace review confirms:
- The new Workspace serves a reasoning need not met by existing Workspaces.
- The Workspace uses existing components and patterns where available.
- Any new components or patterns required by the Workspace go through their own approval processes.
- The Workspace is consistent with Atlas philosophy, hierarchy, interaction language, and accessibility requirements.

## 61. Documentation Standards

Every reusable Atlas artifact (component, pattern, token, Workspace template) is documented to a consistent standard. Documentation explains why the artifact exists, not only what it is.

Ten mandatory documentation sections:
1. **Purpose** — What reasoning need does this serve?
2. **Meaning** — What does this communicate to users?
3. **Usage** — In which contexts does this appear, and why?
4. **Required content** — What must always be present?
5. **Optional content** — What appears conditionally?
6. **States** — Every state with visual and behavioral description.
7. **Variants** — Every justified variant with the reason for its existence.
8. **Composition** — How this artifact combines with others.
9. **Accessibility** — Keyboard behavior, screen reader labels, focus management.
10. **Responsive behavior** — How this artifact adapts across desktop, tablet, mobile.

Plus: examples (correct use), anti-patterns (incorrect use), history (version log).

## 62. Design Review Process

Six review criteria:
1. **Semantic necessity** — Does this serve a distinct reasoning purpose?
2. **Reuse potential** — Will this recur in at least two Workspaces or contexts?
3. **Clarity** — Is its purpose immediately clear to users?
4. **Accessibility** — Does it meet WCAG AA in all states?
5. **Consistency** — Is it compatible with existing components, patterns, and tokens?
6. **Future impact** — Does this introduce complexity that will compound over time?

## 63. Migration Strategy

Eight stages for migrating existing Atlas interfaces into the Design System:

**Stage 1 — Inventory.** Document all existing components, patterns, interactions, and visual elements across all Workspaces.

**Stage 2 — Semantic Mapping.** For each existing element, identify its semantic purpose. Map it to the closest Atlas component or pattern. Identify unmapped elements requiring new specifications.

**Stage 3 — Consolidation.** Merge duplicate elements. Retire elements that have no semantic justification. Resolve terminology conflicts.

**Stage 4 — Token Adoption.** Replace hardcoded visual values with semantic tokens across all existing work.

**Stage 5 — High-Impact Alignment.** Apply the Design System to the highest-visibility Workspaces first (Decision Workspace, Dashboard).

**Stage 6 — Component Implementation.** Build stable components in the implementation environment, aligned with specifications.

**Stage 7 — Surface Migration.** Systematically migrate each Workspace surface to use Design System components, patterns, and tokens.

**Stage 8 — Audit and Governance.** Conduct a post-migration consistency audit. Activate ongoing governance processes.

## 64. Consistency Audit

The Atlas consistency audit is a structured review process run at defined intervals (after major Workspace releases, quarterly for the full system).

Fourteen audit dimensions:

| Dimension | What is verified |
|-----------|-----------------|
| Information hierarchy | Levels 1–6 applied correctly throughout |
| Typography | All seven roles applied consistently |
| Spacing | Correct level for each context |
| Color semantics | No color used outside its semantic meaning |
| Component usage | No component used outside its defined purpose |
| State consistency | All fourteen interaction tokens applied correctly |
| Interaction behavior | Navigation, editing, completion consistent |
| Motion | Twelve tokens applied correctly; reduced motion respected |
| Accessibility | Contrast, focus, touch targets, announcements |
| Responsive behavior | Reasoning quality preserved across all breakpoints |
| AI Collaboration | Suggestion model consistent; user is always primary |
| Historical treatment | All historical content locked, labeled, reduced |
| Naming conventions | All artifacts named by meaning |
| Documentation | All components and patterns fully documented |

Three audit output classifications:
- **Compliant** — Meets all relevant requirements.
- **Acceptable variation** — Differs from the standard with documented justification.
- **True inconsistency** — Differs from the standard without justification; requires remediation.

## 65. The Thirteen Anti-Patterns

Each of the following represents a recurring design failure that conflicts with Atlas philosophy. Every new design is evaluated against this list.

**1. Visual Novelty Without Meaning**
What it is: A new visual treatment introduced because it looks different, not because it means something different.
Violated principle: Consistency begins with meaning.
Correct alternative: Use the existing visual treatment. If the meaning is genuinely different, document the new semantic need and propose a new token.

**2. Duplicate Components**
What it is: Two components that serve the same semantic purpose with different visual treatments.
Violated principle: One meaning, one component.
Correct alternative: Consolidate to a single component. Justify any visual variants by semantic difference.

**3. Duplicate Terminology**
What it is: Two different names used for the same concept across the system (e.g., "Summary" and "Conclusion" used interchangeably).
Violated principle: Canonical glossary.
Correct alternative: Standardize to the canonical term. Update all documentation.

**4. Overloaded Components**
What it is: A single component used to communicate too many different meanings by adding visual indicators, states, or content beyond its defined scope.
Violated principle: Clarity; restraint.
Correct alternative: Split into distinct components, each with one clear purpose.

**5. Dashboard Thinking in Reasoning Workspaces**
What it is: Applying the compact, high-density, scanning-oriented presentation of the Dashboard to Workspaces designed for reading and deliberating.
Violated principle: Reasoning first; context is specific to Workspace role.
Correct alternative: Apply the correct density and spacing for the Workspace's cognitive mode.

**6. AI Content Dominating the Interface**
What it is: Atlas Suggestions, Insights, or Recommendations occupying primary structural positions — appearing before user content, in the Level 1 position, or as the primary voice of a Section.
Violated principle: AI remains secondary; users own decisions.
Correct alternative: AI content is always secondary — positioned below user content, visually distinct, and dismissible.

**7. Traffic-Light Investment Logic**
What it is: Using simple red/green/yellow color-coding to represent investment quality, performance, or recommendation strength.
Violated principle: Reasoning over action; color semantics.
Correct alternative: Present reasoning, not signals. Use color only within its defined semantic role.

**8. Hidden History**
What it is: Historical content that is inaccessible, difficult to find, or not linked from the current context.
Violated principle: History is permanent and accessible.
Correct alternative: Historical content is consistently navigable from the relevant current Workspace.

**9. Unnecessary Animation**
What it is: Motion that entertains, decorates, or marks time without communicating a state change or structural transition.
Violated principle: Motion serves meaning.
Correct alternative: Use only the twelve defined motion tokens for defined purposes. Remove animation that serves no navigational or communicative function.

**10. Component Proliferation**
What it is: A growing inventory of components that serve overlapping or redundant purposes, making the system harder to learn and maintain.
Violated principle: Every new component requires justification.
Correct alternative: Reuse existing components. Propose new ones only through the approval process.

**11. Token Duplication**
What it is: Multiple tokens that represent the same semantic value, leading to inconsistency when one is updated but others are not.
Violated principle: Semantic consistency.
Correct alternative: One semantic meaning, one token. Audit token usage regularly.

**12. Completion Celebration**
What it is: Marking the recording of a Decision with celebratory animation, congratulatory messaging, or theatrical visual effects.
Violated principle: Completion is calm.
Correct alternative: Record the Decision with the 400ms pause and quiet conversion to Historical state. The significance is communicated through restraint, not spectacle.

**13. Premature Abstraction**
What it is: Creating a reusable component or pattern for a design element that has only appeared once, in anticipation of future reuse that has not been evidenced.
Violated principle: Every new component requires justification; future Workspaces inherit before inventing.
Correct alternative: Build for the known need. Propose a reusable component only when reuse has been evidenced in at least two contexts.

## 66. Accessibility Governance

Accessibility is governed at every stage of the design process. It is not reviewed at the end.

Mandatory accessibility reviews at four stages:
1. **Component proposal** — Keyboard behavior and screen reader labels are specified in the proposal, not added later.
2. **Specification approval** — Accessibility behavior is reviewed as a required criterion (not a nice-to-have).
3. **Implementation handoff** — Engineering receives explicit accessibility requirements per component.
4. **Consistency audit** — Accessibility is one of the fourteen audit dimensions.

Token requirements: every color token must meet WCAG AA contrast requirements against its expected background. Every new semantic color token is evaluated for contrast at specification time.

Component requirements: every component must specify keyboard navigation, focus management, and screen reader label in its documentation.

Interaction requirements: every interaction behavior must be achievable without a mouse. Touch targets are at minimum 44×44px.

## 67. Versioning Strategy

**System versioning** — The Atlas Design System as a whole uses semantic versioning (major.minor.patch).
- Major: a change that requires all Workspaces to update.
- Minor: a backward-compatible addition of new components, patterns, or tokens.
- Patch: documentation updates, accessibility improvements, clarifications.

**Document versioning** — Each specification document (UX-012, UX-013, and successors) is versioned independently, with change history.

**Component versioning** — Each component is versioned independently (Section 58).

All version changes are communicated through the governance documentation before they take effect in implementation. No breaking changes without a documented migration path.

## 68. Cross-Team Collaboration

Five disciplines share responsibility for the Atlas Design System. Each has distinct responsibilities.

**Product** — Define the reasoning problems each Workspace must solve. Own the reasoning flow (Signal → Memory). Set priorities for component and Workspace development. Review governance against product strategy.

**UX** — Own the Design System specification. Author and maintain all component, pattern, and token documentation. Conduct consistency audits. Review new proposals against Atlas philosophy and principles.

**Engineering** — Implement components against specification. Maintain the token implementation. Report implementation constraints that require specification adjustment. Maintain implementation-side naming and hierarchy documentation.

**AI (Atlas AI team)** — Define the behavior of all Atlas Collaboration components. Specify trigger timing, suggestion model, and attribution behavior. Ensure AI behavior is consistent with the "Atlas suggests; user decides" principle throughout.

**Content** — Define the editorial voice of all Atlas system text (labels, empty states, confirmations, error messages). Ensure language consistency with the canonical glossary. Own the documentation voice.

Research contributes evidence for unresolved questions (see Remaining System Questions) and validates design decisions against user behavior. Research does not govern the Design System directly; it informs it.

## 69. Future Extensibility

The preference ordering for extending Atlas:

1. **Existing templates** — Use the Workspace Frame template and Section template as-is.
2. **Existing patterns** — Use an approved reasoning, comparison, decision, monitoring, or history pattern.
3. **Existing components** — Use approved components in new configurations.
4. **Existing tokens** — Use existing semantic tokens.
5. **New concept** — Only when none of the above can serve the need, with documented semantic justification.

Three anticipated future Workspace types (not designed here; identified for future governance):
- **Review Workspace** — A dedicated surface for formal Decision Review, producing a Review Conclusion.
- **Research Workspace** — A surface for structured investment research, producing an Understanding sufficient to initiate a Decision.
- **Scenario Workspace** — A surface for structured scenario analysis across multiple possible futures.

Each future Workspace will begin its design process with the seven-question Workspace governance review (Section 18) and will reuse the maximum available set of existing components, patterns, and tokens before proposing new ones.

---

# Part VIII: Accessibility

## 70. Accessibility Foundations

Accessibility in Atlas is structural. It is built into the system's foundations — hierarchy, typography, spacing, color, focus, and interaction — not added afterward.

WCAG AA compliance is the minimum standard throughout. Every component, every state, every Workspace, and every interaction must meet WCAG AA.

Non-color communication: every state change, severity level, and status indicator communicates meaning through at least one non-color channel (shape, label, position, pattern, or typography).

Minimum touch target: 44×44px for all interactive elements on touch devices.

Focus management: `:focus-visible` is used for keyboard focus indicators. Focus is never removed programmatically without being moved to a logical destination.

Screen reader support: all components have defined ARIA labels, roles, and live region behavior. Section expansion/collapse is announced. State changes (saved, updated, loading) are announced. Historical and disabled states are communicated in labels.

Reduced motion: every motion token has a defined reduced-motion fallback. The operating system `prefers-reduced-motion` setting is respected throughout.

Contrast: text contrast meets WCAG AA minimums. Focus indicators meet minimum contrast requirements. Historical content at reduced opacity still meets contrast requirements.

---

# Part IX: Responsive Behavior

## 71. Responsive Philosophy

Responsive behavior in Atlas preserves reasoning quality across devices. It is not a layout rearrangement exercise.

The governing question at every responsive breakpoint: does this adaptation preserve the user's ability to reason?

Three device contexts:

**Desktop** — Primary reasoning environment. Full editorial column, full Comparison layouts, full Section sequences, all editing controls visible.

**Tablet** — Secondary reasoning environment. Most features available. Some Comparison layouts collapse to stacked. Editing controls visible. Navigation adapts to touch.

**Mobile** — Tertiary reasoning environment. Reading and reviewing primary decisions. Full-screen editing mode for authoring. Comparison layouts are stacked. Navigation is touch-primary.

## 72. Responsive Navigation

**Desktop:** All navigation controls persistent. Return navigation always visible. Full Workspace Header.

**Tablet:** Navigation controls persistent but adapted for touch (minimum 44×44px targets). Workspace Header maintained. Overlay model for Historical Records.

**Mobile:** Navigation controls adapted to bottom navigation or persistent top bar. Workspace transitions use full-screen navigation model. Return navigation always visible. Deep-link entry supported.

Scroll behavior: continuous vertical scroll on all devices. Position preserved on return on all devices.

## 73. Responsive Component Adaptations

**Workspace Frame:** Full layout on desktop. Adapted padding on tablet. Single column on mobile.

**Section:** Stacks vertically on all devices. Expansion behavior identical. Section heading row remains full-width tap target.

**Final Decision Card:** Full six-field layout on desktop and tablet. Fields stack vertically on mobile. Full-screen editing for each field on mobile.

**Comparison Layouts:** Side-by-side on desktop. Side-by-side on tablet (narrower columns). Stacked with swipe navigation on mobile.

**Historical Records:** Overlay on desktop and tablet. Full-screen on mobile.

**Atlas Suggestion:** Below relevant field on desktop and tablet. Below relevant field on mobile (may require scroll to see; scroll is not gated).

**Completion Action:** Full-width button on mobile. Standard button in Footer on desktop and tablet.

---

# Cross-Workspace Continuity

## 74. The Complete Atlas User Journey

The full Atlas reasoning journey, from Signal to Future Decision, is continuous. No interaction discontinuity, terminology drift, or hierarchy conflict should occur at any transition.

```
Dashboard
  ↓ (user identifies Signal requiring investigation)
Investment Workspace
  ↓ (user develops understanding; may consult Portfolio Workspace)
Portfolio Workspace
  ↓ (user understands portfolio consequences)
Decision Workspace
  ↓ (user records Decision; Monitoring Conditions established)
Monitoring
  ↓ (conditions approached or triggered)
Historical Review
  ↓ (prior Decision reviewed; Review Conclusion produced)
Future Decision
  ↓ (new reasoning cycle begins)
```

**No interaction discontinuity:** The same gesture (full heading row to expand, same position for return navigation, same Draft Indicator, same Historical Indicator) appears identically at every transition.

**No terminology drift:** The canonical glossary (Part I) governs all content. The same concept is named identically in every Workspace.

**No hierarchy conflicts:** The six-level information hierarchy applies identically in every Workspace. Level 1 is always the most prominent. Level 6 is always the quietest.

---

# 75. Final Governing Principles

These are the permanent governing principles of the Atlas Design System. They supersede all local design preferences and apply without exception.

**1. Consistency begins with meaning.**
Two elements look the same because they mean the same thing. They look different because they mean different things. Never the reverse.

**2. Atlas should look like it thinks.**
The visual language of Atlas expresses the deliberate, structured reasoning it supports. It is calm, editorial, hierarchical, and honest. Not playful, promotional, or theatrical.

**3. Reasoning precedes action.**
Atlas does not optimize for speed. It optimizes for clarity of thought. An interface that helps a user reason well is always preferred over one that helps them act quickly.

**4. Conclusion precedes detail.**
Every Workspace and Section presents its conclusion first. Users orient before they investigate.

**5. Users own decisions.**
The Recorded Decision is always user-authored. Atlas may have suggested content; the decision belongs to the user. This ownership is preserved in attribution, typography, and historical provenance.

**6. History remains immutable.**
Nothing recorded is ever modified, overwritten, or deleted. The immutability of historical content is not a technical constraint — it is a product value.

**7. Typography communicates hierarchy.**
Weight, size, and line height carry the full burden of information hierarchy. Color and decoration do not substitute for typographic clarity.

**8. Spacing communicates structure.**
Closer elements are more closely related. Wider spacing signals a conceptual boundary. Spacing is not decoration — it is architecture.

**9. AI remains secondary.**
Atlas AI supports reasoning. It never leads it. AI content is always visually secondary, always dismissible, and always attributed. The user's voice is always primary.

**10. Accessibility is fundamental.**
WCAG AA compliance is the floor, not the ceiling. Every component, state, and interaction is designed to be accessible from the beginning.

**11. Every new component requires semantic justification.**
A component is introduced only when it represents a genuinely recurring semantic pattern that no existing component can serve. Visual difference is not semantic justification.

**12. Future Workspaces inherit before inventing.**
New Workspaces extend existing templates, patterns, components, and tokens. They introduce new concepts only when existing vocabulary is demonstrably insufficient, and only through the governed approval process.

**13. Context is never destroyed.**
Navigation preserves scroll position, drafts, expansion state, and reasoning context. A user who navigates away and returns finds their work exactly as they left it.

**14. Completion is calm.**
Recording a Decision is a significant moment. It is communicated with measured precision, not celebration. The gravity is in the restraint.

**15. Governance prevents fragmentation.**
The Design System's value compounds over time only if it remains coherent. Every addition, change, and deprecation passes through the governance process. No exceptions.

---

# What UX-012 Establishes

UX-012 establishes the following as permanently decided. These decisions require no further philosophy work. They are the governing specification for all future Atlas design.

**Foundations**
- Atlas is a reasoning environment, not a dashboard product, trading platform, or AI chat interface.
- The Atlas product philosophy (reasoning over action, conclusion before detail, history is permanent, users own decisions) is established as a design constraint, not an aspiration.
- The Atlas reasoning flow (Signal → Context → Understanding → Analysis → Decision → Monitoring → Memory) is the governing information architecture for all Workspaces.
- The six-level information hierarchy is established and applies universally.
- The fifteen universal design principles govern every design decision.
- The canonical glossary establishes single authoritative terms for all Atlas concepts.

**Typography**
- Seven typographic roles are defined with weight, line height, and size characteristics.
- Four weight tiers are established.
- Editorial line length (65–70 characters) is established for narrative reading contexts.
- Line height for body text is established (1.65–1.7).
- Capitalization rules for each typographic role are fixed.
- DM Sans (or equivalent humanist sans-serif) and DM Mono (or equivalent monospace) are the designated typefaces.

**Spacing**
- Six spacing levels are defined.
- Four density contexts (Dense, Standard, Generous, Editorial) are defined and assigned to Workspaces.
- Spacing communicates relationship, not importance.

**Layout**
- Four layout types are established: Editorial Column, Analytical Column, Comparison Layout, Overlay Model.
- Workspace Frame template with required and optional elements is established.
- Section template anatomy with required and optional elements is established.
- Four reading rhythm pause points are defined.

**Components**
- Five characteristics required of every component are established.
- Three conditions required for component justification are established.
- Every component in twelve categories is fully specified: Workspace, Section, Conclusion, Reasoning, Comparison, Decision, Monitoring, Historical, AI Collaboration, Editing, State, Feedback, Action, Metadata.
- The Final Decision Card is established as a signature component with six required fields and two states.
- The Atlas Suggestion interaction model (1.5s pause, three responses, session-scoped dismiss, structural undo) is established.
- The Long-Form Editor eight-state model is established.
- The thirteen state semantic meanings are established.

**Patterns**
- Eleven reusable reasoning patterns are established and inventoried.
- Pattern governance (approval, maturity stages, documentation) is established.

**Interaction**
- Five governing principles for all Atlas interaction are established.
- Navigation philosophy (three orientation questions, nine preserved elements) is established.
- Workspace navigation behaviors for nine navigation types are fully specified.
- Reading flow and scroll behavior are established.
- Expansion and collapse model (full heading row as target, four auto-expansion triggers, session-persistent state) is established.
- Focus management governing rule ("users never lose orientation") and all focus contexts are established.
- Hover behavior for all element types is established.
- Fourteen interaction tokens with semantic meanings are established.
- Editing behavior (30s autosave, 5s structural undo, soft deferred validation, historical locking) is established.
- AI Collaboration interaction (1.5s pause, three responses, structural undo, session-scoped dismiss) is established.
- Loading behavior (300ms minimum, timing thresholds, failed loading handling) is established.
- Validation behavior (soft on blur, completion gate, three contradiction severity levels) is established.
- Error behavior (six error types, work preservation) is established.
- Completion behavior (completion gate check, 400ms pause, calm conversion) is established.
- History interaction (overlay model, locking, comparison, version navigation) is established.
- Monitoring interaction (lifecycle, trigger, review, dismiss with confirmation, resolve) is established.
- Fourteen cross-Workspace consistent interaction behaviors are established.

**Navigation**
- Return navigation position and behavior is fixed and identical across all Workspaces.
- Draft Indicator and Historical Indicator behavior is fixed.
- Browser history behavior for Workspace-level navigation is established.
- Deep-link behavior is established.
- Mobile navigation model is established.

**Responsive Behavior**
- Three device contexts (Desktop, Tablet, Mobile) are defined.
- Responsive philosophy (preserve reasoning quality, not just rearrange layout) is established.
- Component adaptations for all eleven major component types are specified across all device contexts.

**Accessibility**
- WCAG AA compliance is established as the minimum standard throughout.
- Non-color communication requirement is established.
- 44×44px minimum touch target is established.
- `:focus-visible` focus indicator requirement is established.
- Reduced motion compliance with all twelve motion tokens is established.
- Accessibility governance (mandatory reviews at four stages) is established.

**Tokens**
- Fifteen token categories are defined.
- Thirteen semantic token groups are defined with token names and governing meanings.
- Naming conventions for all token categories are established.
- Twelve prohibited naming styles are established.
- Twelve motion tokens with character, easing, applied-to contexts, and reduced-motion fallbacks are established.
- Fourteen interaction tokens with semantic meanings are established.

**Governance**
- Component governance (ownership, five-step approval, ten-section documentation, semantic versioning, deprecation sequence, maturity stages) is established.
- Pattern governance (seven categories, maturity stages) is established.
- Workspace governance (seven-question review) is established.
- Design review criteria (six criteria) are established.
- Eight-stage migration strategy is established.
- Fourteen-dimension consistency audit is established.
- Thirteen anti-patterns are catalogued.
- Versioning strategy (system, document, component) is established.
- Cross-team collaboration responsibilities (five disciplines) are established.
- Future extensibility preference ordering is established.

**Workspace Templates**
- All four current Atlas Workspaces (Dashboard, Investment Workspace, Portfolio Workspace, Decision Workspace) are fully specified.
- Seven governance questions for future Workspaces are established.
- Three anticipated future Workspace types are identified.

**Future Extensibility**
- Preference ordering for extending Atlas (templates → patterns → components → tokens → new concepts) is established.
- New concept introduction requires documented semantic justification and governed approval.

---

# Remaining System Questions

The following questions are genuinely unresolved. They remain open because they require implementation evidence, user research, performance testing, or accessibility testing that has not yet been conducted. No settled design decision is reopened here.

**Question 1: Atlas Suggestion Pause Timing**
Why unresolved: The 1.5-second pause before an Atlas Suggestion surfaces was specified as a design intent. Whether 1.5 seconds feels appropriately non-interruptive under real editing conditions (varying typing speed, varying content length, varying Workspace context) requires observation of users editing in live conditions.
Required evidence: User research observing editing sessions across the four Workspaces. Specific focus on moments when Suggestions surface and whether users perceive them as interruptive.
Implementation impact: The pause timing may need to be context-sensitive (longer in intensive editing phases, shorter in review phases). This would add a behavioral variant to the Atlas Suggestion component.
Priority: Medium. The 1.5s default is a reasonable starting point; this question validates or adjusts it.

**Question 2: Completion Gate Threshold**
Why unresolved: Two fields are specified as required for Completion (Decision statement, Primary Reason). Whether these two fields are sufficient to warrant the gravity of a Recorded Decision — or whether additional required acknowledgments are needed for specific Decision types — requires evidence from Decision recording sessions.
Required evidence: Analysis of the quality and completeness of recorded Decisions in early implementation. Qualitative research on user confidence at the completion moment.
Implementation impact: May require conditional required fields based on Decision type (e.g., a Decision that contradicts a prior Decision may require explicit acknowledgment of the contradiction before recording).
Priority: High. This directly affects Decision quality — the primary Atlas output.

**Question 3: Mobile Long-Form Editing Experience**
Why unresolved: The full-screen editing mode for mobile is specified as the approach. The precise interaction — how the user enters and exits full-screen editing, how they navigate between the six Final Decision Card fields while in full-screen mode, whether the Workspace body remains visible in any form — requires usability testing on actual mobile devices.
Required evidence: Usability testing of the Decision Workspace editing flow on mobile devices. Minimum: five users completing a full Decision cycle (from empty to Recorded) on mobile.
Implementation impact: May require a dedicated mobile editing model that differs more significantly from the desktop model than currently specified.
Priority: Medium. Decision Workspace is primarily a desktop experience; mobile editing is secondary but must be functional.

**Question 4: Monitoring Condition Density at Scale**
Why unresolved: The Monitoring Condition component and Dashboard monitoring surface are specified for a manageable number of active conditions. The behavior of the Dashboard and Investment Workspace when a user has a large number of active Monitoring Conditions (e.g., 20+, across 10+ investments) has not been specified.
Required evidence: Information architecture testing with high-condition scenarios. User research on how experienced Atlas users expect to navigate large monitoring surfaces.
Implementation impact: May require filtering, grouping, or priority-ordering controls for the monitoring surface that are not currently specified.
Priority: Medium. Low priority for initial implementation; becomes critical as user adoption grows.

**Question 5: Historical Record Navigation at Scale**
Why unresolved: The Historical Timeline Entry and Decision History components are specified for a normal number of historical records. The navigation model for a user with extensive decision history (5+ years of recorded decisions across dozens of investments) has not been specified.
Required evidence: Information architecture work with realistic historical data volumes. User research on how users expect to navigate, search, and filter historical content at scale.
Implementation impact: May require search, filtering, and tagging capabilities in the Historical Record navigation model.
Priority: Low for initial implementation. Important for long-term product planning.

---

# Initial Atlas Component Inventory

The first official Atlas Component Inventory. All components are at experimental maturity unless otherwise noted. Future Owner is the design system team unless otherwise noted.

## Foundations

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Information Hierarchy (Levels 1–6) | Governs typographic emphasis throughout | All | Universal | Immediate | Stable |
| Semantic Token Model | Named design variables for all visual values | All | Universal | Immediate | Stable |
| Canonical Glossary | Single vocabulary for all Atlas concepts | All | Universal | Immediate | Stable |

## Navigation & Frame

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Workspace Frame | Outer container establishing identity and structure | All | Universal | Immediate | Candidate |
| Workspace Header | Identity area with navigation controls | All | Universal | Immediate | Candidate |
| Return Navigation | Consistent return path to Dashboard or source | All | Universal | Immediate | Candidate |
| Draft Indicator | Persistent communication of unsaved content | Investment, Decision | All authoring Workspaces | Immediate | Candidate |
| Historical Indicator | Persistent communication of historical viewing mode | All | All Workspaces with history | Immediate | Candidate |
| Workspace Footer | Primary action area | All | Universal | High | Candidate |

## Workspace-Specific

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Dashboard Signal List | Prioritized list of items requiring attention | Dashboard | Dashboard-like surfaces | High | Experimental |
| Dashboard Portfolio Status | Compact portfolio-level status summary | Dashboard | Dashboard | High | Experimental |
| Portfolio Allocation Overview | Current vs. target allocation representation | Portfolio | Portfolio Workspace | High | Experimental |

## Section

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Standard Section | Baseline section with heading, content, expansion | All | Universal | Immediate | Candidate |
| Reasoning Section | Section for editorial narrative reasoning | Investment, Decision | All reasoning Workspaces | Immediate | Candidate |
| Read-Only Section | Section for non-editable content | All | Universal | High | Candidate |
| Editable Section | Section with authoring capability | Investment, Decision | All authoring Workspaces | Immediate | Candidate |
| Comparison Section | Section with parallel column layout | Portfolio, Decision | Portfolio, Decision | High | Candidate |
| Decision Section | Section with completion gate and deliberate spacing | Decision | Decision, future Review | Immediate | Candidate |
| Historical Section | Section for displaying immutable historical content | All | Universal | High | Candidate |
| Completion Section | Record Decision area and post-completion state | Decision | Decision, future Review | Immediate | Candidate |

## Conclusion

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Primary Conclusion | Central conclusion of a Workspace | All | Universal | Immediate | Candidate |
| Current Conclusion | Live-updating Atlas understanding | Investment, Decision | Reasoning Workspaces | High | Candidate |
| Decision Required | Frames the specific choice to be made | Decision | Decision-oriented surfaces | High | Candidate |
| What Changed | Recent developments relevant to current reasoning | Investment, Decision | Reasoning Workspaces | Medium | Experimental |
| Portfolio Conclusion | Portfolio-level integration conclusion | Portfolio | Portfolio Workspace | High | Experimental |
| Review Conclusion | Conclusion produced by a formal Review | Decision (review mode) | Future Review Workspace | Medium | Experimental |
| Decision Summary | Condensed portable record of a Recorded Decision | Dashboard, Investment, Portfolio | Universal | High | Candidate |

## Reasoning

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Supporting Factors | Named reasons supporting reasoning direction | Investment, Decision | Reasoning Workspaces | Immediate | Candidate |
| Challenges | Named concerns against reasoning direction (3 severity) | Investment, Decision | Reasoning Workspaces | Immediate | Candidate |
| Assumptions | Explicit conditions reasoning depends on (4 statuses) | Investment, Decision | Reasoning Workspaces | High | Candidate |
| Invalidation Condition | Specific condition that would invalidate reasoning | Decision | Decision, Investment | High | Candidate |
| Portfolio Consequences | What the Decision means for the portfolio | Decision | Decision, Portfolio | High | Candidate |
| Opportunity Cost | Explicit representation of what is foregone | Decision | Decision, Portfolio | High | Candidate |
| Implementation Summary | How the Decision will be executed | Decision | Decision | High | Candidate |
| Review Condition | When and why the Decision should be reviewed | Decision | Decision, Investment | High | Candidate |

## Comparison

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Before/After | Explicit comparison of current and proposed state | Decision, Portfolio | Decision, Portfolio | High | Candidate |
| Alternative Comparison | Structured comparison of two or more options | Decision, Investment | Reasoning Workspaces | High | Candidate |
| Opportunity Cost Component | Structured visual of opportunity cost | Decision | Decision, Portfolio | High | Candidate |
| Scenario Comparison | Comparison of potential outcomes | Investment, Decision | Reasoning Workspaces | Medium | Experimental |
| Allocation Comparison | Before/after portfolio allocation representation | Portfolio | Portfolio | High | Experimental |
| Historical Comparison | Current state alongside Historical Record | Decision, Investment | All Workspaces with history | Medium | Experimental |

## Decision

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Proposed Decision | User's authored intent before formalization | Decision | Decision | Immediate | Candidate |
| Final Decision Card | Six-field structured permanent record (signature) | Decision | Decision, future Review | Immediate | Candidate |
| Decision Summary | Condensed portable Recorded Decision | All | Universal | High | Candidate |
| Decision History | Chronological list of Recorded Decisions | Investment, Portfolio | Reasoning Workspaces | High | Candidate |
| Decision Amendment | Links new Decision to prior; additive only | Decision | Decision | Medium | Experimental |
| Decision Review | Formal re-examination of prior Decision | Decision (review mode) | Future Review Workspace | Medium | Experimental |

## Monitoring

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Monitoring Condition | Single trackable condition with full lifecycle | Decision, Dashboard, Investment | All Workspaces | High | Candidate |
| Review Trigger | Communication that Review Condition is met | Dashboard, Investment | All Workspaces | High | Candidate |
| Invalidation Trigger | Communication that Invalidation Condition is met | Dashboard | All Workspaces | High | Candidate |
| Implementation Follow-up | Tracks whether Implementation Intent was executed | Dashboard, Decision | Dashboard, Decision | Medium | Experimental |
| Scheduled Review | Time-based review trigger from Decision | Decision, Dashboard | Decision, Dashboard | Medium | Experimental |

## History

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Historical Record | Base immutable content container | All | Universal | Immediate | Candidate |
| Historical Decision | Full Recorded Decision as Historical Record | Investment, Decision, Dashboard | Universal | High | Candidate |
| Historical Review | Completed Review as Historical Record | Investment, Decision | Reasoning Workspaces | High | Experimental |
| Historical Assumption | Assumption at a prior point in time | Decision (review mode) | Decision, Investment | Medium | Experimental |
| Historical Timeline Entry | Single entry in chronological event timeline | Investment, Portfolio, Decision | All Workspaces | High | Candidate |

## AI Collaboration

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Atlas Suggestion | Optional AI content for user reasoning | All authoring Workspaces | All authoring Workspaces | High | Candidate |
| Atlas Insight | Contextual AI observation; no action required | Investment, Decision | Reasoning Workspaces | Medium | Experimental |
| Atlas Warning | AI-identified concern (3 severity levels) | Decision | Reasoning Workspaces | High | Candidate |
| Atlas Recommendation | Specific AI-suggested action with reasoning | Dashboard, Investment, Decision | All Workspaces | Medium | Experimental |
| Atlas Clarification | AI question seeking additional context | Decision | Reasoning Workspaces | Low | Experimental |
| Atlas Summary | Structured AI-generated reasoning state summary | Investment, Decision | Reasoning Workspaces | Medium | Experimental |

## Actions

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Primary Action | Single most important action in current context | All | Universal | Immediate | Candidate |
| Secondary Action | Supporting non-primary action | All | Universal | Immediate | Candidate |
| Inline Action | Section or component-level action | All | Universal | High | Candidate |
| Section Action | Action applying to an entire Section | All | Universal | High | Candidate |
| Completion Action | Deliberate final action (Record Decision) | Decision | Decision, future Workspaces | Immediate | Candidate |
| Destructive Action | Action that removes or modifies; requires confirmation | All | Universal | High | Candidate |

## Feedback

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Informational Feedback | Neutral non-action-required information | All | Universal | High | Candidate |
| Reminder | Gentle prompt to return to something | All | Universal | Medium | Experimental |
| Warning Feedback | Concern requiring attention; does not block | All | Universal | High | Candidate |
| Material Concern | Significant concern requiring acknowledgment | Decision, Investment | Reasoning Workspaces | High | Candidate |
| Blocking Issue | Condition that must be resolved before proceeding | Decision | Decision | Immediate | Candidate |
| Validation Feedback | Confirmation that content meets requirements | All authoring | All authoring | High | Candidate |
| Loading State | Communication of background processing | All | Universal | Immediate | Candidate |
| Empty State | Communication when no content exists (4 subtypes) | All | Universal | Immediate | Candidate |

## Completion

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Completion Gate | Pre-submission requirement verification | Decision | Decision, future Workspaces | Immediate | Candidate |
| Post-Completion State | Workspace state after recording | Decision | Decision | Immediate | Candidate |
| Monitoring Activation | Visual communication of newly active Monitoring | Decision, Dashboard | Decision | High | Experimental |

## Editing

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Long-Form Editor | Primary narrative editing environment (8 states) | Decision | Investment, Decision | Immediate | Candidate |
| Short Statement | Brief single/two-line authored statement | All authoring | All authoring | Immediate | Candidate |
| Decision Field | Deliberate editing for Final Decision Card fields | Decision | Decision | Immediate | Candidate |
| Structured Comparison Editor | Parallel editing for Comparison content | Decision, Portfolio | Comparison contexts | High | Experimental |
| Assumption Editor | Specialized editing with status control | Investment, Decision | Reasoning Workspaces | High | Experimental |
| Implementation Editor | Free-form editing for Implementation Intent | Decision | Decision | High | Experimental |

## Metadata

| Name | Purpose | Primary Workspace | Reuse Potential | Implementation Priority | Maturity |
|------|---------|------------------|-----------------|------------------------|---------|
| Timestamp | When content was created, modified, or recorded | All | Universal | Immediate | Candidate |
| Source Attribution | Origin of information | All | Universal | High | Candidate |
| Confidence Statement | Qualitative confidence level (never a gauge) | Decision | Decision, Investment | High | Candidate |
| Status Label | Lifecycle stage of a component or record | All | Universal | High | Candidate |
| Author Attribution | User attribution on authored content | All authoring | All authoring | High | Candidate |
| Version Identifier | Document or component version | Governance | System | Medium | Candidate |
| Relationship Link | Named link between two Atlas records | Decision, Investment | All Workspaces | Medium | Experimental |
| Monitoring State Label | Current lifecycle stage of Monitoring Condition | Decision, Dashboard | All Workspaces | High | Candidate |

---

# Initial Atlas Pattern Inventory

The first official Atlas Pattern Inventory. Each pattern represents a recurring combination of components and behaviors that together serve a specific reasoning purpose.

| Pattern | Purpose | Primary Workspace | Reuse Scope | Priority |
|---------|---------|------------------|-------------|----------|
| **Conclusion** | Presents the primary conclusion of a reasoning session at the top of a Workspace, before supporting detail | Investment, Decision, Portfolio | All Workspaces | Immediate |
| **Reasoning** | Structures the full reasoning body: conclusion → supporting factors → challenges → assumptions → opportunity | Investment, Decision | Reasoning Workspaces | Immediate |
| **Comparison** | Presents two or more options, states, or outcomes in parallel with consistent structure | Portfolio, Decision | Portfolio, Decision | High |
| **Opportunity Cost** | Makes explicit what is foregone by a Decision; always presented alongside the proposed action | Decision | Decision, Portfolio | High |
| **Contradiction** | Surfaces logical conflicts between reasoning elements; classifies by severity; gates completion for Blocking severity | Decision | Decision, Investment | High |
| **Decision** | Sequences Proposed Decision → Final Decision Card → Record Decision with deliberate spacing and completion gate | Decision | Decision | Immediate |
| **Monitoring Establishment** | The process by which Monitoring Conditions and Review Conditions are defined at Decision time and activated upon recording | Decision | Decision | High |
| **Historical Review** | Presents a prior Recorded Decision alongside current reasoning for formal review; produces a Review Conclusion | Decision (review mode) | Future Review Workspace | Medium |
| **AI Suggestion** | Consistent model for surfacing, presenting, and responding to Atlas AI suggestions: 1.5s pause, three responses, attribution, undo | All authoring | All authoring Workspaces | High |
| **Completion** | The full completion sequence: completion gate → 400ms pause → historical conversion → post-completion state | Decision | Decision | Immediate |
| **Workspace Transition** | Consistent navigation between Workspaces preserving full context: draft, scroll position, expansion state, subject context | All | Universal | Immediate |
| **Assumption Invalidation** | The process by which a Broken Assumption surfaces as a Contradiction in the Decision Workspace | Investment, Decision | Reasoning Workspaces | High |
| **Monitoring Trigger** | The process by which an Approaching or Triggered Monitoring Condition surfaces in the Dashboard and Investment Workspace | Dashboard, Investment | All Workspaces | High |

---

# Atlas Design System Readiness Assessment

## Design Readiness — Ready

Philosophy, principles, hierarchy, typography, spacing, layout, Workspace templates, all four current Workspaces, all components, all patterns, interaction language, motion tokens, interaction tokens, accessibility foundations, responsive philosophy, governance model, token model, naming conventions, documentation standards, migration strategy, anti-patterns, and future extensibility are all specified.

No design decisions require additional philosophy work. No design questions have been left deliberately unanswered. Remaining System Questions (listed above) require implementation evidence or user research, not design work.

## Engineering Readiness — Partially Ready

**Ready for specification:** Component definitions, state models, token categories, semantic token groups, naming conventions, and implementation governance are sufficient to begin component-level specification (UX-013).

**Requires before implementation begins:** UX-013 (Component Specification) must be produced before engineering implementation starts in earnest. UX-013 will provide: component anatomy, variants, properties, design-token mapping, Figma component architecture, engineering naming, and implementation guidance for each component.

**Can begin immediately:** Token implementation (semantic token dictionary, color values, typography scales, spacing scales) can begin in parallel with UX-013 production. Workspace Frame and Navigation components can begin implementation against current specifications.

## Documentation Readiness — Partially Ready

**Complete at the system level:** This document (UX-012) provides complete system-level documentation. The canonical glossary, governing principles, component inventory, pattern inventory, and governance model are complete.

**Requires UX-013:** Component-level documentation (anatomy, variants, properties, design-token mapping, implementation guidance, testing expectations) is not yet produced. UX-013 is the vehicle for this documentation.

## Migration Readiness — Ready to Begin

The eight-stage migration strategy is fully specified. The Initial Atlas Component Inventory provides the basis for Stage 1 (Inventory) and Stage 2 (Semantic Mapping). Migration can begin immediately, working from the Inventory.

Recommendation: begin Stage 1 (Inventory of existing elements) in parallel with UX-013 production.

## Governance Readiness — Ready

Component governance, pattern governance, Workspace governance, naming conventions, documentation standards, design review process, versioning strategy, accessibility governance, and cross-team collaboration responsibilities are all established. The governance model can be activated immediately.

## Accessibility Readiness — Ready

Accessibility requirements are specified at the system level, component level, token level, and interaction level. WCAG AA is established as the minimum standard. Governance requires mandatory accessibility review at four stages. Remaining System Question 3 (mobile editing) has an accessibility component that will be addressed through usability testing.

## Future Extensibility — Ready

The preference ordering for extensions (templates → patterns → components → tokens → new concepts), the seven-question Workspace governance review, and the three anticipated future Workspace types are established. The system is designed to scale without fragmentation.

## Conclusion

**Atlas is ready to begin component-level specification.**

UX-012 is sufficient to initiate UX-013 (Component Specification). Engineering can begin token implementation and Workspace Frame implementation in parallel. Migration Stage 1 can begin immediately. Governance can be activated immediately.

The only remaining design work is UX-013. No philosophy work, no system-level decisions, and no governance questions require resolution before UX-013 begins.

---

# Requirements for UX-013

## UX-013 — Atlas Design System Component Specification

UX-013 specifies every reusable Atlas component individually. It takes the component definitions in UX-012 and produces complete implementation-ready specifications for each.

**Scope:** Every component in the Initial Atlas Component Inventory at Candidate or Experimental maturity. Components should be specified in implementation priority order: Immediate first, then High, then Medium, then Low.

**Required for each component:**

**Anatomy** — The complete structural breakdown of every element within the component: required, optional, conditional. Named. Hierarchical. Every element has a name that follows Atlas naming conventions.

**Variants** — Every justified variant with the semantic reason for its existence. No variant is introduced because it looks different; every variant exists because it means something different.

**Semantic purpose** — What does this component communicate to users? Why does it exist? What reasoning need does it serve?

**Properties** — Every configurable property: type, allowed values, default value, required or optional.

**States** — Every state from the thirteen interaction tokens, plus component-specific states. Visual and behavioral description of each.

**Interaction behavior** — Full interaction specification: keyboard, mouse, touch. Focus management. Tab order within the component. Activation behavior.

**Accessibility behavior** — ARIA role, label, and live region specifications. Screen reader announcements for all state changes. Reduced motion behavior. Contrast requirements.

**Responsive behavior** — Explicit adaptation at Desktop, Tablet, and Mobile breakpoints. What stacks, what collapses, what remains visible.

**Composition rules** — Which components this component can contain. Which components can contain this one. Nesting restrictions.

**Content rules** — Maximum and minimum content lengths. Required content. Prohibited content. Truncation behavior.

**Validation rules** — What constitutes valid content. When and how validation is communicated.

**Authorship behavior** — If the component is editable: the complete editing model for this specific component. How editing is initiated. How content is saved. How Atlas-generated content is attributed.

**Historical behavior** — How this component appears and behaves when it contains or displays historical content.

**Design-token mapping** — Every visual property mapped to a specific semantic token. No hardcoded values.

**Figma component architecture** — How the component is structured in Figma: frames, auto-layout, variants, properties, slots.

**Engineering naming** — The exact component name in code, consistent with Atlas naming conventions.

**Implementation guidance** — Notes for engineering on anything that may not be obvious from the visual specification.

**Documentation template** — A completed version of the ten-section documentation standard for this component.

**Testing expectations** — What should be verified in visual regression testing, interaction testing, and accessibility testing.

**Deprecation rules** — What conditions would warrant deprecation of this component. What would replace it.

UX-013 does not introduce new philosophy, new principles, or new governance. It applies the decisions made in UX-012 to individual components with precision. Where UX-012 describes what a component is, UX-013 describes everything needed to build it.

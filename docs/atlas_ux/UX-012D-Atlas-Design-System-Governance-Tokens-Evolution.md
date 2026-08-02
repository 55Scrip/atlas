UX-012D — Atlas Design System Governance, Tokens & Evolution

Status: Governance Specification Complete
Owner: Atlas Product
Governs: Design token philosophy and taxonomy, naming conventions, component governance, pattern governance, Workspace governance, documentation standards, design review process, migration strategy, consistency audit, anti-patterns, evolution model, accessibility governance, implementation governance, cross-team collaboration, versioning, future extensibility, governance checklist
Depends on: UX-012A — Foundations; UX-012B — Components & Reusable Patterns; UX-012C — Interaction, Navigation & Responsive Behavior; UX-008 through UX-011
Part D of: UX-012 — Atlas Design System & Workspace Consistency Specification

**Correction Notice (Phase 3C, governed by ADR-002 — 2026-07-25):** This document's original identity (Status, Owner, Governs, Depends on, Part D of, as above) and original date are preserved unchanged. One semantic area was corrected per `ADR-002-Critical-UX-Architecture-Resolutions.md` and the Atlas UX Source Correction Plan, Phase 3C:
- **C-03 (Decision Workspace Sequence terminology):** the Naming Conventions section's "Sections" example bullet mixed two already-canonical terms with two superseded ones in the same sentence. "What Supports This Decision" was corrected to "Supporting Factors," and "Challenge Review" was corrected to "Challenges." The bullet's other two examples — "Why a Decision Is Required" and "Portfolio Consequences" — were already canonical and are unchanged.

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, above. All content outside this one example bullet, including all governance, token, and evolution content, is unchanged.

**Correction Notice (Atlas UX Architecture UX-012 Authority Migration task — 2026-08-02):** This is a later, additive correction; it does not revise, replace, or reopen the Phase 3C notice above, which remains historically accurate for the area it corrected. This document is subordinate to `UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0, per that Doctrine's own UXD-R-097. Two semantic areas are corrected:
- **Atlas Memory terminology (Section 7, Workspace Governance questions 4 and 5):** two passages named "Atlas Memory" as the destination of Workspace-produced analysis. Per `UX-000-Atlas-UX-Doctrine.md` UXD-R-094, Memory is UX-layer language only and MAY NOT be used as a Product Concept; the accepted successor terms, per the completed Atlas Memory Status Investigation, are DecisionHistory (catalog lookup across recorded Decisions) and Decision Timeline (one Decision's own chronological narrative), applied below according to each passage's own meaning.
- **AI-belief framing (Section 16, Cross-Team Collaboration):** "what Atlas concludes" risked framing Atlas as an independent authority that concludes truth, contrary to `UX-000-Atlas-UX-Doctrine.md` UXD-R-056.

This notice does not claim the corrected wording existed in this document's original, historical version — the prior wording is preserved verbatim, in quotation, at each corrected passage below. All content outside these two areas is unchanged.

⸻

1. Governance Philosophy

The Atlas Design System exists because coherence is a product quality, not a stylistic preference. When every Atlas surface communicates hierarchy the same way, uses the same terms for the same states, and behaves consistently on the same interactions, the user develops a reliable mental model of how Atlas thinks. That mental model is a form of trust — the user knows that what they learn in the Investment Workspace will work in the Decision Workspace. Governance is the mechanism that preserves that trust as Atlas grows.

Without governance, design systems drift. New contributors make locally sensible decisions that diverge from established patterns. New Workspaces introduce new components that solve problems already solved elsewhere. New terminology enters the product that means nearly the same thing as existing terminology — and the user encounters two words where one would have served. Visual novelty gets introduced because a new surface wants to feel distinct, rather than because its reasoning task genuinely requires a different treatment. Over two or three years, Atlas stops feeling like one product and starts feeling like several products that share a color palette.

Governance prevents this by making the cost of divergence explicit. Every new pattern requires a justification that the existing system cannot satisfy the need. Every new component requires evidence of a recurring semantic problem. Every new term requires confirmation that no existing term already covers the meaning. The cost of introducing something new is higher than the cost of adapting something existing — and this asymmetry is the mechanism that keeps the system coherent.

Governance is not implementation. This document does not specify pixels, code, or tooling. It specifies the decision-making framework that determines what is built — and the process by which future additions are evaluated against the system. Implementation is UX-013's responsibility.

Why consistency supports better reasoning: A user making a decision does not want to spend cognitive resources learning the interface. Every moment spent re-orienting to a new pattern — why does this confidence label look different here? what does this amber treatment mean in this context? — is a moment not spent on the investment reasoning itself. Interaction consistency is not an aesthetic goal; it is a cognitive load reduction. The Design System governs consistency so the product can deliver on its core promise: Atlas improves reasoning.

Why every new pattern requires justification: The justification burden is asymmetric by design. Adding a pattern is easy; discovering that two similar patterns exist and removing one is hard. Every new pattern that enters the system permanently increases the surface area that future contributors must understand before they can work coherently. The correct stance is conservative: if an existing pattern can serve a new need with a justified variant, the variant is preferred over a new pattern.

Why semantic consistency is more important than visual novelty: A surface that looks slightly different from other Atlas surfaces but behaves consistently and uses the same terms will feel like Atlas. A surface that uses different terms for the same states — calling what every other Workspace labels "Under Review" something else in this new Workspace — will not feel like Atlas, regardless of how visually consistent it appears. Semantic consistency is the deeper layer. Visual consistency is its expression.

⸻

2. Design Token Philosophy

Design tokens are the boundary between design decisions and implementation values. A token is a named semantic relationship: `space.inter-section` means "the space between major sections in a Workspace" — regardless of whether the underlying pixel value is 48px or 56px or changes in a future release. The token preserves the meaning; the implementation may change.

Atlas uses semantic tokens rather than hardcoded visual values for three reasons:

Stability of meaning: The token `color.semantic.amber` means "a condition that warrants attention but is not urgent" everywhere it appears in Atlas. If the Atlas visual identity evolves and the amber hue shifts slightly, only the global token value changes — every component that uses `color.semantic.amber` updates automatically, with no risk of some components updating and others not.

Reviewability: A design or code review can evaluate whether `color.semantic.amber` is the correct token for a given context by asking whether the content represents a condition that warrants attention. This semantic question is far more useful than asking whether `#D2A95E` is the right color — the latter requires knowing what `#D2A95E` means.

Documentation: Token names document themselves. `motion.expand.duration` communicates its purpose to any reader. `var(--atlas-motion-expand)` communicates slightly less. `250` communicates nothing.

Token categories and what each governs:

Typography tokens: Font family (by role — prose and metadata), font size (by the six information hierarchy levels), font weight (by authorship and emphasis role), line height (by content type — editorial body vs. compact metadata), letter spacing (standard body, wide for uppercase labels), and text transform (none for body; uppercase for section labels). Typography tokens do not specify absolute px values directly — they specify roles, and the role-to-value mapping is defined in the global token tier.

Spacing tokens: The six spacing levels (workspace margins, inter-section, intra-section, card padding, row spacing, metadata spacing), plus the density multipliers for each density level (signal: 0.65×, reading: 1.0×, decision: 1.2×, historical: 0.8×) applied to the base reading-density values. Responsive reduction ratios (tablet: 0.85×, mobile: 0.70× for inter-section and intra-section).

Layout tokens: Maximum editorial column width (the character-count target translated to a pixel-equivalent at the confirmed type size), maximum analytical column width, overlay proportions (94vw × 93vh for desktop), safe area inset references for mobile, maximum comparison column width.

Semantic color tokens: The complete set established in UX-011 — surface levels (primary, elevated, panel, hairline), text levels (primary, secondary, tertiary, dim), and semantic accent colors (amber, green, red, blue) in their restrained Atlas forms. Plus: disabled opacity level, historical opacity level, overlay background dimming opacity.

Surface tokens: The four background surface levels (background, surface, elevated, panel) with their warm-dark values, plus the hairline and border values. Surface tokens are referenced by container components to ensure that the visual distinction between surface levels remains consistent.

Border tokens: Three border weights — hairline (1px, used for subtle section dividers), standard (1px at higher opacity, used for container boundaries), semantic-rule (the left-border rule used by challenge items and assumption rows, with three opacity levels for the three severity tiers). Plus border-radius values (consistent corner radius for all Atlas containers, a slightly larger radius for the overlay Workspace frame itself).

Elevation tokens: The visual elevation model for Atlas's three container types. Strong containers (Final Decision Card, Current Conclusion card) use a distinct surface color and optionally a very subtle shadow. Subtle containers (assumption rows, alternative rows) use a background color change only. Open layout uses neither. The elevation tokens define these three levels as semantic references.

Icon tokens: The icon family reference, icon size by context (body-adjacent, metadata-adjacent, standalone), icon weight (consistent stroke width), and the rule that icons at metadata scale must have a text label companion.

Motion tokens: The twelve tokens from UX-012C (Open, Close, Expand, Collapse, Highlight, Fade, Replace, Insert, Remove, Navigate, Update, Loading), each with a duration range expressed as a named duration category (immediate: 0ms, brief: 100–150ms, standard: 200–250ms, deliberate: 350–400ms) and an easing function reference (ease-out, ease-in, ease-in-out). The reduced-motion flag that converts all motion to instantaneous.

Focus tokens: Focus ring pixel width (minimum 2px), focus ring color (a specific token distinct from the semantic accent colors, with sufficient contrast against both light and dark surfaces in Atlas's warm-dark palette), focus ring border-radius behavior (matches the focused element's border-radius).

Interaction tokens: The fourteen interaction states from UX-012C mapped to composable visual properties: hover (surface lightening delta), pressed (brief additional lightening or darkening), focused (focus ring application), selected (left-border rule at full opacity or elevated surface), disabled (opacity multiplier: 0.40–0.45), editing (document dimming overlay opacity: 0.05–0.08), expanded/collapsed (no additional visual property — communicated by affordance position), loading (loading indicator opacity animation), saved/unsaved (Draft Indicator text content — not a visual token), updated ("UPDATED" label visibility), historical (text opacity multiplier + surface opacity multiplier), acknowledged (challenge item opacity reduction after acknowledgment).

Accessibility tokens: Minimum contrast ratio for body text (WCAG AA: 4.5:1 for normal text, 3:1 for large text), minimum contrast ratio for metadata text (WCAG AA: 4.5:1 — metadata must meet AA even at its small scale), minimum touch target size (44×44px), minimum body text size at 1x display scale (15px), focus ring minimum width (2px), focus ring minimum contrast ratio (3:1 against adjacent surface — WCAG 2.1 Level AA for focus visibility).

Responsive tokens: Three breakpoint definitions (desktop, tablet, mobile) expressed as minimum viewport widths. Spacing scale multipliers for each breakpoint. Overlay behavior by breakpoint (94vw × 93vh at desktop, full-screen at tablet and mobile). Comparison layout breakpoint (the viewport width below which two-column comparison collapses to sequential single-column).

State tokens: The visual properties associated with each semantic state — not repeating the interaction tokens, but the content-level state indicators: the "UPDATED" label typography, the "MONITORING ACTIVE" label typography, the assumption status label typography and its left-border rule color (mapped from semantic color tokens).

⸻

3. Semantic Token Model

Semantic tokens describe meaning — they are not named after their visual properties. A semantic token named `color.semantic.amber` communicates what the color means (a condition requiring attention that is not urgent) rather than what it looks like. This distinction is the foundation of the token model.

Semantic token groups and their governing meanings:

Primary Conclusion: tokens governing the visual presentation of the highest-emphasis Atlas conclusion on any surface — the conclusion statement, its container, its surrounding space. Values: `type.conclusion`, `space.conclusion.vertical`, `surface.conclusion.container`.

Supporting Reasoning: tokens for Atlas-generated body content that supports a primary conclusion. Values: `type.body.atlas`, `space.reasoning.intra`. The weight difference from user-authored content is encoded as a separate token.

User Authored: tokens for user-written content — decision statements, primary reasons, assumption edits. Values: `type.body.user`. Distinguished from `type.body.atlas` by weight.

Historical Content: tokens for all prior-record presentations. Values: `color.text.historical` (maps to tertiary text at reduced opacity), `surface.historical` (maps to primary surface at reduced opacity), `type.metadata.timestamp`.

Monitoring: tokens for monitoring condition presentations. Values: `color.semantic.amber` (for Approaching state), `color.border.monitoring-rule` (the left-border rule on monitoring items), `type.status.monitoring`.

Decision: tokens for the decision record and its components — the Final Decision Card, the decision statement, the review condition, the implementation state. Values: `surface.decision.card` (the elevated container for the Final Decision Card), `type.decision.statement`, `space.decision.card.internal`.

Opportunity: tokens for the Opportunity Cost section's conclusion line and the comparative row structure. Values: `type.opportunity.conclusion` (the highest-emphasis text within the section, slightly larger than standard body).

Contradiction: tokens for the three severity tiers of the Challenge component. Values: `color.border.contradiction.informational` (amber, reduced opacity), `color.border.contradiction.material` (amber, medium opacity), `color.border.contradiction.unresolved` (amber, full opacity, slightly thicker).

Warning: synonym for Material Contradiction and above. The Warning semantic group maps to the same amber tokens — the distinction between Contradiction and Warning is semantic (Contradiction is content-identified; Warning is Atlas-identified) not visual.

Completed: tokens for the post-recording state — the completed Final Decision Card, the cleared body, the recorded state. Values: `surface.decision.card` at its full recorded visual authority (no visual change from the draft state — the authority comes from the populated content, not a different surface treatment).

Disabled: tokens for unavailable actions and incomplete required fields. Values: `opacity.disabled` (0.40–0.45), `cursor.disabled` (not-allowed).

Loading: tokens for loading indicator presentations. Values: `opacity.loading.pulse.min`, `opacity.loading.pulse.max` (the range of the opacity animation in the loading indicator, suppressed under reduced motion).

Focus: `color.focus.ring`, `width.focus.ring`, `radius.focus.ring` — the three parameters of the focus ring, constant across all surfaces.

Why semantic meaning must remain stable even if visual implementation changes:

If Atlas's visual identity evolves — a slightly adjusted amber hue, a warmer surface background, a refined typography scale — the semantic token names should not change. `color.semantic.amber` continues to mean "a condition requiring attention" before and after the visual update. The global token value it maps to changes; the semantic token name does not. This stability ensures that every component referencing `color.semantic.amber` is automatically updated by the global change, and that documentation, design reviews, and code reviews continue to use the same vocabulary regardless of the current visual implementation.

⸻

4. Naming Conventions

Names in Atlas describe product meaning. They do not describe appearance, position, size, or technical implementation. A name that could only be understood by looking at a screenshot is not a valid Atlas name.

Components:
— Names are two or three words: a noun describing the product object, optionally preceded by a descriptor. "Final Decision Card." "Monitoring Condition." "Historical Record." "Atlas Suggestion."
— The noun describes what the object is in the Atlas product, not what it looks like. Not "Large Bordered Card." Not "Amber Left Panel."
— The descriptor, when present, is semantic — "Final" describes the permanence of the record, not its position. "Historical" describes its temporal status, not its visual treatment.
— Component names are the same in design documentation, design tooling, code, and product copy where the component is named. No separate "design names" and "code names."

Patterns:
— Pattern names describe the reasoning relationship they serve. "Opportunity Cost Comparison." "Assumption Status Review." "Contradiction Acknowledgment." "Completion Gate."
— Not: "Two-Column Card Layout." Not: "Amber Warning Flow." Not: "Bottom Button Pattern."

States:
— State names use the vocabulary defined in UX-012B Section 13. "Draft," "Recorded," "Under Review," "Monitoring," "Superseded," "Historical." These names are used identically in design documentation, code, and any user-facing labels that name the state.
— Not: "Pending," "Locked," "Inactive" (these are valid states in generic systems but have undefined meaning in Atlas — use the Atlas vocabulary).

Workspaces:
— Workspace names describe the reasoning question they answer. "Decision Workspace" — the place where decisions are formed and recorded. "Investment Workspace" — the place where investment judgments are examined.
— Not: "Decision Panel." Not: "Decision View." Not: "Decision Screen." The word "Workspace" is intentional — it communicates that this is a sustained reasoning environment, not a page or a modal.

Tokens:
— Token names follow the structure: `category.role.variant` where applicable.
— `space.inter-section` — category: space; role: inter-section. No variant needed.
— `color.text.primary` — category: color; subcategory: text; role: primary.
— `color.semantic.amber` — category: color; subcategory: semantic; role: amber.
— `motion.expand.duration` — category: motion; role: expand; property: duration.
— `type.body.atlas` — category: type; role: body; variant: atlas-authored.
— Token names never include px values, hex codes, or implementation-specific identifiers. Never: `color-d2a95e`. Never: `space-48px`. Never: `font-15-regular`.

Templates:
— Template names describe the Workspace type they support. "Analytical Workspace Template." "Decision Workspace Template." "Monitoring Workspace Template."
— A template name should make it immediately clear which future Workspace type would use it.

Actions:
— Action names follow Verb + Noun. "Record Decision." "Complete Review." "Dismiss Suggestion." "Acknowledge Contradiction." "Compare Alternatives."
— The verb is specific to the action's consequence, not generic. Not "Submit." Not "Confirm." Not "OK."
— Destructive actions name the consequence. "Discard Draft." "Supersede Decision." "Remove Monitoring Condition." Not "Delete." Not "Cancel."

Sections:
— Section names describe their content role in the reasoning arc. "Supporting Factors." "Why a Decision Is Required." "Challenges." "Portfolio Consequences."
— Not: "Section 1." Not: "Top Card." Not: "Analysis Area."

AI behaviors:
— Atlas AI behaviors are named by their conversational role, not by their technical form. "Atlas Suggestion" (a specific field-level improvement proposal). "Atlas Insight" (a broader interpretive observation). "Atlas Warning" (a detected conflict). "Atlas Recommendation" (a strategic suggestion at the decision level).
— Not: "AI Output." Not: "Model Response." Not: "Generated Content."

History and monitoring:
— Historical components add the prefix "Historical" to the base component name. "Historical Decision." "Historical Record." "Historical Comparison."
— Monitoring components use a descriptive noun. "Monitoring Condition." "Review Trigger." "Invalidation Trigger." "Scheduled Review."

Prohibited naming styles:
— Appearance-based names: "Big Card," "Dark Panel," "Amber Box," "Thin Divider."
— Position-based names: "Top Section," "Right Panel," "Bottom Bar," "Left Rail."
— Generic interaction names: "Popup," "Modal," "Dropdown," "Toggle."
— Technology-specific names: "React Component," "CSS Module," "SVG Icon."
— Abbreviations that are not universally understood within Atlas: "DW" for "Decision Workspace," "MC" for "Monitoring Condition."
— Names that describe implementation before meaning: "CardWithBorder," "CollapsibleRow," "ExpandableSection."

⸻

5. Component Governance

A component enters the Atlas Design System when — and only when — it represents a product meaning that recurs across at least two surfaces and would cause user confusion if presented inconsistently.

Ownership: Every component has one named owner — a product role (not a person) responsible for the component's current specification, its documentation, its versioning decisions, and its deprecation when the time comes. Ownership is assigned at the time of introduction and transferred explicitly if the responsible role changes. A component without a named owner is not a production component — it is experimental.

Approval process: Introducing a new component requires five verifiable steps:
1. Problem statement: a written description of the recurring product meaning the component addresses, with references to the specific Atlas surfaces where the problem appears.
2. Existing system check: a documented review of all existing components confirming that none can satisfy the need through a variant or composition.
3. Component specification: a complete specification in the format established by UX-012B — purpose, required content, optional content, interaction behavior, responsive behavior, accessibility behavior, composition rules, usage examples, anti-patterns.
4. Accessibility review: a review confirming that the component specification meets all accessibility token requirements — contrast, touch target, keyboard navigation, screen reader labels, non-color state communication.
5. Owner approval: explicit sign-off from the component's designated owner.

Documentation requirements: Every production component must have documentation that covers — in this order — why the component exists (the product meaning it represents), what it contains (anatomy), how it behaves (states and interaction), how it adapts (responsive behavior), how it combines with other components (composition), and what it must not be used for (anti-patterns). Documentation must include at least one usage example and at least one anti-pattern example. Documentation that only explains what a component looks like, without explaining why it exists, is insufficient.

Versioning: Components use three-part semantic versioning.
— Major version: a breaking change — required content changes, accessibility model changes, interaction model changes that would require existing implementations to be updated. Major version changes require a migration note documenting what changed and how existing uses should be updated.
— Minor version: a non-breaking addition — a new optional content element, a new state, a new responsive variant. Existing implementations are unaffected.
— Patch version: a fix — correcting a specification error, clarifying ambiguous language, adding a missing example. No behavioral change.

Deprecation: A component is deprecated when a superior replacement exists or when the product meaning it represents has been consolidated into an existing component. Deprecation follows this sequence:
1. Deprecation notice: the component is marked as deprecated in documentation. The replacement is named. The sunset date is set to two release cycles from the deprecation notice.
2. Migration period: existing implementations that use the deprecated component are updated to the replacement during the migration period.
3. Retirement: at the sunset date, the deprecated component is retired — removed from the active component library. Its documentation is preserved in an archive for reference but is no longer actively maintained.

Experimental status: A component idea that has not yet completed the approval process may be designated experimental. Experimental components may be used in one surface at a time while the specification is developed and validated. An experimental component may not be considered a shared system component until it has completed the full approval process. Experimental components are labeled clearly in documentation and tooling.

Reuse expectations: A component that is introduced as a shared component is expected to be used wherever its product meaning appears. If a designer or engineer implements the product meaning without using the shared component — creating a local one-off instead — this is a governance failure that should be caught in design review. The consistency audit (Section 11) specifically checks for unintentional divergence of this type.

⸻

6. Pattern Governance

A pattern is a composition of components that serves a recurring product need — a conclusion followed by its supporting reasoning and a set of challenge items, or a decision field preceded by an Atlas proposal block. Patterns are larger than components and smaller than sections.

When is a new pattern justified? A new pattern is justified when the same component composition recurs in more than one context, and when specifying the composition in one place reduces the risk of inconsistent implementation. A pattern is not justified merely because a layout is visually distinctive or because it appears complex.

How are duplicate patterns prevented? Before proposing a new pattern, the designer must review the pattern library and confirm that no existing pattern serves the same compositional need. If a pattern serves a similar need but with a different component set, the difference must be semantically justified — not visually different, but representing a different product meaning. The design review process (Section 9) includes a duplicate-pattern check.

How patterns mature:
— Draft pattern: a proposed composition that has been identified in a specific Workspace context but has not yet been validated across surfaces.
— Candidate pattern: a composition that recurs in at least two contexts and has been proposed for the pattern library, with a complete specification.
— Stable pattern: a candidate pattern that has completed the pattern review process, is documented in the pattern library, and is the expected implementation for its product meaning.
— Deprecated pattern: a stable pattern that has been superseded by a refined composition. Deprecated patterns follow the same two-cycle retirement process as components.

Pattern categories and governance notes:

Reasoning patterns: Compositions that present Atlas analysis — the primary conclusion followed by its implication and supporting factors. These patterns are the most fundamental in the system. New reasoning patterns require strong justification that the existing composition does not serve the new context.

Comparison patterns: Compositions that structure parallel content for the user to evaluate. The comparison pattern library is deliberately small — most comparisons in Atlas follow one of the three defined layouts (Before/After, Alternative Comparison, or Allocation Comparison). A new comparison layout requires demonstrating that the existing three do not serve the new content structure.

Decision patterns: Compositions specific to decision formation and recording — the Proposed Decision block, the decision field with Atlas proposal, the Final Decision Card, the post-recording state. These patterns are tightly coupled to the Decision Workspace and are less likely to require new additions.

Monitoring patterns: Compositions for monitoring condition presentations — the monitoring item row, the triggered state, the resolve flow. These patterns may require extension as Atlas adds new monitoring capabilities, but extensions should build on the existing monitoring component set.

Historical patterns: Compositions for prior-record presentations — the historical comparison, the timeline, the version panel. These are stable and unlikely to require new patterns unless a new type of historical record is introduced (a new decision type, a new record category).

AI collaboration patterns: Compositions for Atlas assistance — the suggestion panel, the partial-accept flow, the Atlas Warning within a challenge section. These may evolve as Atlas's AI capabilities develop, but each new AI collaboration pattern must demonstrate that the existing patterns cannot be extended to serve the new capability.

Completion patterns: Compositions for the terminal moment of any Workspace — the completion gate explanation, the post-recording transition, the settled record. These are deliberately stable — consistency at the moment of completion is critical to the user's sense of trust in the system.

⸻

7. Workspace Governance

A new Workspace is a significant product decision, not a design decision. Before a new Workspace is designed, seven questions must be answered and documented:

1. What reasoning question does it solve? The question must be precise and distinct from the questions answered by existing Workspaces. "How do I track the performance of my decisions over time?" is a distinct question from anything the current Workspace set answers. "How do I see my portfolio?" is not distinct from the Portfolio Workspace.

2. Why can't an existing Workspace solve it? This question must be answered honestly. If the need can be served by adding a section to an existing Workspace, a new Workspace is not justified. A new Workspace is justified only when the reasoning mode — the user's mindset, depth of editing, reading style, and decision responsibility — is genuinely different from all existing Workspaces.

3. What context does it inherit? Every Workspace receives context from another surface. The new Workspace must specify what it receives (from which surface, what information, in what form) and how that context is displayed when the Workspace opens.

4. What conclusion does it produce? A Workspace that does not produce a conclusion or a recorded output cannot feed the reasoning arc. The new Workspace must specify its output — the decision it records, the analysis it contributes to the decision's own Decision Timeline, the monitoring conditions it establishes. *(Corrected per the Atlas UX Architecture UX-012 Authority Migration task, 2026-08-02 — see the Correction Notice above. Prior text: "the analysis it adds to Atlas Memory." Refined per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02: per the completed Atlas Memory Status Investigation, analysis contributed to one decision's own record is its Decision Timeline, distinct from DecisionHistory's catalog-wide scope.)*

5. How does it feed future reasoning? The output of the Workspace must connect to the Atlas reasoning arc — appearing in future Dashboard signals, informing future Investment or Portfolio Workspace analysis, or contributing to DecisionHistory. A Workspace that produces output with no downstream use is isolated from the product's core function. *(Corrected per the same task and notice. Prior text: "contributing to Atlas Memory." Refined per the Atlas UX Architecture UX-012 Authority Migration Targeted Correction, 2026-08-02: this item describes output feeding future, cross-decision reasoning across the corpus, which is DecisionHistory's catalog-wide scope, per the completed Atlas Memory Status Investigation.)*

6. What existing components and patterns does it use? A new Workspace specification must begin with a map of existing components from UX-012B and patterns from the pattern library that it will use. Only after establishing this map should new component or pattern needs be identified.

7. What new patterns or components, if any, are required? If the new Workspace requires components or patterns that do not exist in the system, each must go through the full component or pattern governance process before the Workspace specification is finalized. A Workspace specification that relies on undefined components is not complete.

The review process for a new Workspace follows the design review process defined in Section 9, with the additional requirement that the seven questions above are documented and approved before design work begins.

⸻

8. Documentation Standards

Every reusable artifact in the Atlas Design System — every component, pattern, template, token category, and governance rule — must be documented. Documentation is not optional; an artifact without documentation is experimental regardless of its maturity.

The documentation standard for every artifact:

Purpose (required first): Why does this artifact exist? What product problem does it solve? What would go wrong if it did not exist? This section is written before any other — it is the artifact's justification.

Meaning (required): What does this artifact communicate to the user? What understanding should the user arrive at when they encounter it? For components, this is the semantic meaning. For tokens, this is the product role the value governs.

Usage (required): Where and when should this artifact be used? Which Workspaces, which contexts, which content types? This section includes at least one positive example ("Use this when...") and at least one negative example ("Do not use this when...").

States (required for components): Every state the component supports, with a description of the visual treatment, the user's expected understanding, and the interaction available in each state.

Variants (required for components with variants): Each variant, its distinguishing characteristics, and the product meaning or context that justifies the variant's existence.

Composition (required for components): Which components may contain this component. Which components this component may contain. Nesting rules. What must not be nested.

Accessibility (required): Keyboard behavior, focus behavior, screen reader labels and announcements, touch target requirements, contrast requirements, non-color state communication. This section must be written as requirements, not as guidelines.

Responsive behavior (required): How the artifact adapts at each breakpoint. What changes and what does not. What must remain visible on all devices.

Examples (required): At least one correct usage example demonstrating the artifact in its intended context. For complex components, at least two examples showing different states or variants.

Anti-patterns (required): At least one documented misuse — a specific way the artifact might be used incorrectly, why this is a problem, and what the correct approach is. Anti-patterns that appear in practice should be added to this section.

History (required): When the artifact was introduced, which UX specification governed its introduction, major version changes and their reasons, deprecation status if applicable.

Version (required): The current version number in major.minor.patch format.

Documentation should explain why the artifact exists before explaining what it is. A reader who understands the why will apply the artifact correctly in novel contexts. A reader who only understands the what will apply it only in the exact contexts shown in examples.

⸻

9. Design Review Process

Every new addition to the Atlas Design System — a component, a pattern, a token category, a Workspace template, a new interaction behavior, a new term in the vocabulary — requires a design review before it is incorporated into the system.

The design review is not a visual critique. It is a semantic and consistency review. The questions it asks are: Does this addition represent a real and recurring product need? Is it consistent with the system it joins? Does it introduce terminology or behavior that could be confused with existing terms or behaviors? Will it remain useful as the product evolves?

Review criteria applied to every addition:

Semantic necessity: Does this addition address a product meaning that is not already addressed by the existing system? If the existing system can serve the need with a variant or composition, the addition is not semantically necessary.

Reuse potential: Will this addition be used across at least two Atlas surfaces, or is it so specific to one surface that it functions as a local one-off? An addition used in only one place is not a system component — it is a surface-specific implementation detail.

Clarity: Is the addition clearly distinguishable from all existing artifacts that serve similar purposes? If a designer or engineer might confuse the new addition with an existing one, the differentiation must be sharpened before approval.

Accessibility: Does the addition meet all accessibility token requirements? Accessibility review is not a separate later step — it is a criterion for design review approval.

Consistency: Does the addition behave consistently with all existing system artifacts? Does it use the same interaction tokens, the same motion tokens, the same naming conventions? Where it deviates, is the deviation semantically justified?

Future impact: Will this addition remain useful and coherent as the product grows? Does it introduce a dependency that might become a problem when new Workspaces or capabilities are added? Does it foreclose options that the system might need later?

Review process by artifact type:

New component: Requires the full five-step approval process from Section 5 (problem statement, existing system check, complete specification, accessibility review, owner approval) before review. The design review then evaluates the specification against the six criteria above.

New pattern: Requires a draft pattern specification and evidence of recurrence in at least two surface contexts. The design review confirms that no existing pattern can serve the need and that the new pattern composes existing components correctly.

New token: Requires a token specification naming the semantic meaning, the token name, the tier (global, semantic, or component), and the relationship to existing tokens. The design review confirms that the token name follows naming conventions, that no existing token covers the same semantic role, and that the token can be implemented consistently across all surfaces.

New Workspace: Requires completed answers to the seven Workspace governance questions from Section 7 before review. The design review evaluates whether the Workspace is genuinely necessary, whether it fits in the Atlas reasoning arc, and whether its component and pattern requirements are fully specified.

New interaction or motion behavior: Requires specification as an extension or variant of an existing interaction token or motion token. The design review confirms that the existing token system cannot serve the need and that the new behavior is consistent with the motion philosophy established in UX-012C.

New terminology: Requires a glossary entry with the new term, its definition, its intended usage contexts, and a comparison with the most similar existing terms. The design review confirms that the term does not conflict with or shadow existing Atlas vocabulary.

New visual style (typography treatment, container variant, color treatment): Requires a semantic justification — the visual difference must correspond to a semantic difference in the product meaning. A new visual style that exists to make a new surface look distinct is not accepted. A new visual style that distinguishes a new semantic state that the existing system does not represent is reviewed on its merits.

⸻

10. Migration Strategy

The Atlas Design System applies to all Atlas surfaces — including those that existed before the system was fully specified. Migration from pre-system implementations to the system is a staged process that minimizes disruption while maintaining forward momentum.

Stage 1 — Inventory:
Document every current component, pattern, color value, type style, spacing value, and interaction behavior in use across all existing Atlas surfaces. The inventory is not a redesign — it is a factual record. The output is a catalogue organized by surface (Dashboard, Investment Workspace, Portfolio Workspace, Decision Workspace) and by category (typography, spacing, containers, states, interactions). The inventory includes honest notation of divergences between surfaces — places where the same product meaning is currently presented differently.

Stage 2 — Semantic Mapping:
For each item in the inventory, identify the corresponding element in the UX-012 system. Three classifications apply:
— Aligned: the current implementation correctly matches the system specification. No change required.
— Justified variation: the current implementation differs from the system but the difference is legitimately explained by the surface's specific reasoning task. Document the justification; no change required unless the justification is reviewed and found insufficient.
— Divergence: the current implementation differs from the system without justification. Flag for correction. Prioritize by visibility (differences the user encounters in every session are higher priority than differences in rarely-accessed sections).

Stage 3 — Consolidation:
Before correcting divergences, consolidate duplicate implementations. Where the same product meaning is implemented in three slightly different ways across three surfaces, choose the system-compliant version and establish it as the reference implementation. The other two implementations become candidates for the Stage 6 migration.

Stage 4 — Token Adoption:
Introduce the token system into the implementation. Replace hardcoded values (raw color values, pixel sizes, duration values) with semantic token references. This stage produces no visual changes — it is a pure implementation refactor. It must be completed before any visual migrations in Stage 5 and 6, because subsequent stages depend on the token system to propagate correctly.

Stage 5 — High-Impact Alignment:
Correct the most visible divergences identified in Stage 2. Prioritize: section collapse summaries that do not follow the two-line model (high frequency, high user impact), hover behaviors that differ between surfaces (visible in every interaction session), historical content treatments that do not use the standard visual treatment (visible whenever prior decisions are accessed), and terminology that deviates from the established vocabulary (visible in every text element that names a state or action). High-impact alignment changes should be bundled by surface — correcting all divergences in the Investment Workspace together rather than correcting one type of divergence across all surfaces at once.

Stage 6 — Component Implementation:
Create shared implementation components for the highest-reuse system components. Priority order based on reuse frequency: Section (all Workspaces), Assumption (Decision, Investment, future Review), Challenge (Decision, Investment, Portfolio, future Review), Monitoring Condition (Decision, Dashboard, future Monitoring), Decision Summary (Dashboard, Investment, Portfolio, Decision), Final Decision Card (Decision, Dashboard).

Stage 7 — Surface Migration:
Update each Workspace surface to use the shared component implementations. The Decision Workspace is the reference implementation — it was designed to the system and is the most recently specified surface. Migration order for other surfaces: Investment Workspace (highest reasoning depth, most component overlap with Decision Workspace), Portfolio Workspace, Dashboard. One surface at a time. Each surface migration is validated before the next begins.

Stage 8 — Audit and Governance:
Once all surfaces are migrated, activate the consistency audit process (Section 11) as a regular practice. Apply the design review process (Section 9) to all new work. The system is now actively governed rather than being established.

How migration minimizes disruption:
— No stage requires a complete visual redesign of any surface. Each stage addresses a defined subset of changes.
— Stage 4 (token adoption) is invisible to users — it produces no visual change.
— Stages 5, 6, and 7 produce visual changes only in the elements being migrated, not in surrounding elements.
— User-facing text changes (terminology corrections) are coordinated with content review to ensure the new terms are clear and do not introduce confusion.
— Migration is validated by the audit process at each stage before proceeding to the next.

⸻

11. Consistency Audit

The consistency audit is a repeatable evaluation process applied to Atlas surfaces at regular intervals (at minimum, before each major release) and to any surface after a significant design change.

The audit evaluates each surface against the Atlas Design System across fourteen dimensions:

Hierarchy: Does the surface correctly apply the six-level information hierarchy? Is the primary conclusion the highest-emphasis element? Do challenges and contradictions appear at Level 4 (after supporting reasoning)? Is metadata at Level 6?

Spacing: Does the surface use the correct spacing token for each relationship? Is inter-section spacing consistently the largest spacing unit? Does the surface feel appropriately dense for its reasoning task?

Typography: Does the surface apply the correct typographic roles? Is Atlas-authored content in the slightly lighter weight? Is user-authored content in primary weight? Are section labels in the correct scale and capitalization?

Interaction: Does the surface apply the correct motion tokens for its transitions? Is the expand/collapse animation consistent with the system? Do Atlas Suggestions appear after the 1.5-second pause? Is the focus ring visible and consistent?

Components: Does the surface use the shared system components for all recurring product meanings? Are there any locally implemented alternatives to system components?

Patterns: Does the surface use the established pattern compositions? Are there any locally composed patterns that duplicate existing stable patterns?

States: Does the surface use the correct state vocabulary from UX-012B Section 13? Are all states communicated through text labels as well as visual treatment?

Tokens: Does the surface reference semantic tokens rather than hardcoded values? Are there any raw color values, pixel sizes, or duration values not routed through the token system?

Language: Does the surface use the established Atlas vocabulary? Are action labels in Verb + Noun form? Are state labels from the defined vocabulary? Is the confidence language using the five qualitative states?

Responsiveness: Does the surface adapt correctly at all three breakpoints? Are all reasoning content and required actions accessible on mobile? Does the comparison layout collapse to sequential single-column below the defined breakpoint?

Accessibility: Does the surface meet all accessibility token requirements? Does it pass WCAG AA contrast checks? Are all interactive elements in the tab order? Do state changes produce the required screen reader announcements?

History: Does the surface present all historical content with the standard treatment? Is all historical content fully immutable? Does the historical comparison follow the established layout?

AI collaboration: Does the surface present Atlas Suggestions consistently with the system pattern? Does the partial-accept flow follow the established model? Is Atlas assistance clearly secondary to the user's authored content?

Completion: Does the surface follow the established completion behavior? Is the Final Decision Card (or its equivalent) presented with the correct visual authority? Does the post-recording transition follow the 400ms pause and body-clearing sequence?

Audit output: The audit produces three classifications for each finding:
— Aligned: the surface correctly implements the system specification in this dimension.
— Justified variation: the surface differs from the specification, and the justification is documented and accepted. No correction needed.
— Divergence: the surface differs from the specification without justification. A specific correction is recommended and tracked to completion.

Audit cadence: Full audit before each major release. Targeted audit (covering only the dimensions affected) after any significant design change to a surface. New Workspace audit before any new surface is released.

⸻

12. Anti-Patterns

Atlas anti-patterns are specific design decisions that contradict the Atlas Design System's governing principles. Each is defined with its description, the principle it violates, and the correct alternative.

Visual novelty without meaning: Introducing a new visual treatment — a new container style, a new color treatment, a new typographic emphasis — because the designer wants the new surface to feel distinct, not because the product meaning requires a new visual signal. Violates: typography and spacing do more work than decoration; every visual element must improve comprehension. Correct alternative: apply the existing visual system. If the reasoning task genuinely requires a new semantic state, introduce a new semantic token through the governance process.

Duplicate components: Implementing a component locally that solves a problem already solved by a system component. Most commonly occurs when a designer is unaware of the existing component or finds it inconvenient to use. Violates: the consistency audit requirement; the component governance principle that shared components must be used wherever their product meaning appears. Correct alternative: use the system component; if it does not serve the need, propose an extension through the governance process.

Duplicate terminology: Using a different word for a state, action, or concept that already has an established Atlas name. "Pending" used in one surface where other surfaces use "Draft." "Locked" where other surfaces use "Historical." Violates: semantic consistency. Correct alternative: use the established vocabulary; if the existing term does not accurately describe the new concept, propose a vocabulary addition through the terminology review process.

Overloaded cards: Adding content to a strong container (the Final Decision Card, the Primary Conclusion card) that does not belong to the primary record being presented. Making the Final Decision Card contain secondary and tertiary information because it is visually prominent and thus attracts content. Violates: the card system's purpose — strong containers are used sparingly for specific high-significance content. Correct alternative: the additional content belongs in a subordinate section or in a subtle container adjacent to the strong container.

Dashboard thinking inside reasoning Workspaces: Organizing reasoning content as a grid of equal-emphasis tiles or metrics rather than as a hierarchical document. Occurs when a designer defaults to the layout conventions of analytics tools or portfolio dashboards when designing a new Workspace. Violates: structure over borders; conclusion before detail; typography communicates hierarchy. Correct alternative: the editorial column with the six-level information hierarchy applied — conclusions first, reasoning beneath, challenges after reasoning, reference material last.

AI dominating the interface: Presenting Atlas-generated content at higher visual emphasis than user-authored content, or designing a Workspace where the primary content is Atlas's analysis rather than the user's reasoning and decision. Occurs when the Atlas AI capability feels like the product's selling point and designers give it undue prominence. Violates: the user owns judgment and decisions; AI remains contextual and secondary. Correct alternative: Atlas-generated content is secondary to user-authored content in visual weight. The user's decision statement, primary reason, and confidence assessment are always the highest-emphasis content in any decision context.

Traffic-light investment logic: Using red, amber, and green to communicate buy, hold, and sell judgments — or any system that implies Atlas is making investment recommendations rather than improving the user's reasoning. Violates: color never carries meaning alone; green should not imply guaranteed positive outcomes; red should not create trading urgency. Correct alternative: semantic colors communicate structural conditions (amber: a condition requiring attention; green: an intact or valid condition; red: a broken or deteriorated condition) — never investment verdicts.

Hidden history: Updating Atlas-generated analysis without preserving the prior state in a way that is accessible to the user; or allowing a recorded decision to be edited without creating an explicit version record. Violates: historical reasoning remains intact; no historical reasoning is silently rewritten. Correct alternative: every change to a prior record creates an explicit version; the prior state is accessible through the Historical Record component.

Unnecessary animations: Adding motion to transitions that do not require it to clarify what happened — a subtle card hover animation, a loading spinner that runs even when the content loads in under 100ms, a fade-in on static text that has not changed. Violates: motion should clarify; motion should never entertain or distract. Correct alternative: apply motion tokens only to transitions that would otherwise cause disorientation — apply the test "would removing this motion cause the user to be confused about what happened?"

Component proliferation: Introducing a new component for each visual variation of a product pattern rather than using variants and states of existing components. Results in a component library that is difficult to maintain and that produces visual inconsistency as each variant evolves independently. Violates: component governance — a component earns its place by representing a recurring semantic pattern, not a recurring visual arrangement. Correct alternative: extend existing components through variants and states; introduce a new component only when the product meaning is genuinely distinct.

Token duplication: Defining multiple tokens that map to the same global value for conceptually different purposes — effectively creating the same token twice with different names. Results in a token system that is difficult to maintain and that breaks when the global value is updated (because only one token reflects the update). Violates: the token naming convention — each token represents one semantic role. Correct alternative: if two semantic roles consistently share the same global value, that is a coincidence of current visual design — they should remain as two distinct tokens so they can diverge independently if the visual design evolves.

Inconsistent empty states: Designing empty states that look like errors rather than intentional absences, or that imply Atlas failed rather than that there is genuinely nothing to show. Violates: empty states should reassure, not look unfinished. Correct alternative: apply the four empty state types from UX-012C and design each to communicate its specific type (positive absence, unavailable result, incomplete data, user action required).

Complexity escalation: Adding features, states, or behaviors to a component or pattern to address edge cases that could instead be handled by a simpler, separate component. Results in components that are difficult to document, difficult to test, and inconsistent in practice. Violates: restraint over decoration; every element must earn its presence. Correct alternative: serve common cases cleanly with the primary component; handle edge cases with a separate, clearly distinct component if the edge case genuinely represents a different product meaning.

⸻

13. Design System Evolution

The Atlas Design System is a living specification. It is not a fixed artifact that was completed at one point in time. It will evolve as Atlas's product evolves — as new Workspaces are added, as user research reveals reasoning needs that the current system does not address, as Atlas's AI capabilities develop, and as the visual identity matures.

How components mature:
— Components begin as experimental — used in one context, not yet reviewed through the governance process.
— Candidates are proposed for the system after demonstrating recurrence in at least two contexts and completing the specification.
— Stable components have completed the review process and are the expected implementation for their product meaning.
— Deprecated components have been superseded and are in the sunset period.
— Retired components are preserved in an archive but no longer active.

Components do not regress — a stable component does not become experimental because a new surface doesn't use it. A stable component may be deprecated when a superior replacement is identified, but it remains in the system until the retirement process is complete.

How patterns mature: Patterns follow the same maturity stages as components (draft, candidate, stable, deprecated, retired) with the same governance requirements at each transition.

How tokens evolve: Global tokens (the underlying values) may change as the Atlas visual identity evolves — a hue adjustment, a scale refinement, a new breakpoint definition. When a global token value changes, every semantic token that references it inherits the change automatically. Semantic token names do not change when their underlying values change — the meaning remains stable. New semantic tokens are added through the design review process when new product meanings emerge that the existing token set does not cover.

How Workspaces evolve: Workspaces evolve by adding sections, refining components within existing sections, and updating Atlas-generated content. Adding a section to an existing Workspace follows a lighter governance process than creating a new Workspace — but the section must be specified using existing components and patterns, and must go through the design review process to confirm it does not introduce new product concepts that conflict with the Workspace's established reasoning role.

How obsolete artifacts are retired: An artifact is considered for retirement when: it has been deprecated for two release cycles; all known implementations have been migrated to the replacement; the archive record of its specification and history has been completed. Retirement is a formal decision — it is not automatic at the sunset date. The decision is made by the artifact's owner with confirmation that no remaining implementation depends on it.

How compatibility is maintained: The token system is the primary compatibility mechanism. When components are updated (major version), the token references within them are preserved — implementations that reference the token continue to receive the correct visual treatment even as the underlying component evolves. Implementations that depend on specific token values will need to be reviewed on major token changes.

The Design System does not aim to be unchanging. It aims to evolve with intention — every change is deliberate, documented, communicated, and migrated. The opposite of a well-governed system is not a static system; it is an ungoverned one.

⸻

14. Accessibility Governance

Accessibility is governed from the moment of specification, not inspected at the end of implementation. Every component, pattern, and token introduced to the Atlas Design System must meet accessibility requirements before it is accepted.

Mandatory accessibility reviews:

At component specification: the component specification must include a complete accessibility section covering keyboard behavior, focus behavior, screen reader labels and announcements, touch target requirements, contrast requirements, and non-color state communication. A specification missing any of these is incomplete and cannot proceed to design review.

At design review: the accessibility section of every specification is reviewed as a design review criterion — not as a separate accessibility audit. A specification that fails to meet accessibility token requirements does not pass design review.

At implementation: implementation of any system component includes an accessibility implementation check — verifying that the coded component matches the specified keyboard behavior, focus behavior, and screen reader model. This check occurs before the implementation is accepted into shared component libraries.

At consistency audit: the accessibility dimension of the consistency audit (Section 11) verifies that existing implementations continue to meet requirements. Accessibility regressions discovered in a consistency audit are treated as high-priority divergences.

Token requirements:
— All text must reference contrast tokens (`accessibility.contrast.body` — WCAG AA 4.5:1, `accessibility.contrast.large` — WCAG AA 3:1, `accessibility.contrast.ui` — WCAG AA 3:1 for interface components) and must pass the specified ratios against the surface they appear on.
— All interactive elements must reference the touch target token (`accessibility.touch-target.minimum` — 44×44px).
— All text must meet the minimum size token (`accessibility.text.minimum` — 15px at 1x).
— The focus ring must reference focus tokens (`focus.ring.width`, `focus.ring.color`, `focus.ring.radius`).
— All motion must reference the reduced-motion flag and produce the instantaneous variant when the flag is active.

Component requirements:
— Every component in the system has a defined ARIA role and label model in its specification.
— State changes that are not visually obvious produce screen reader announcements — expansion, triggered monitoring conditions, Atlas Suggestion appearance, completion gate activation.
— All semantic states are communicated through at least two non-color channels (text label + typographic treatment, or text label + structural indicator).

Interaction requirements:
— The full interaction model of every component is achievable by keyboard alone, following the interaction behaviors specified in UX-012C.
— No interaction relies on hover as the sole discovery mechanism — all interactive affordances have a persistent or structurally implied alternative.
— Focus order is predictable and follows the visual reading order in all components.

Responsive requirements:
— Touch targets remain at minimum 44×44px at all breakpoints. Components that reduce in size on mobile must have transparent padding that maintains the minimum touch target.
— Line length targets (65–70 characters for prose) are maintained through column width constraints at all breakpoints — on mobile, this may result in full-width content with horizontal margins, but the constraint is maintained.
— Reduced motion applies at all breakpoints — the `prefers-reduced-motion` check is not device-specific.

Documentation expectations:
— The accessibility section of every component's documentation is written as requirements ("The focus ring must appear...") not as guidelines ("The focus ring should appear...").
— Accessibility anti-patterns are documented alongside usage anti-patterns — specific ways the component might be implemented incorrectly that would break accessibility.
— ARIA role and label specifications are precise and testable — not vague ("provide appropriate labels") but specific ("the section header button has `aria-expanded` set to `true` when expanded and `false` when collapsed; `aria-controls` references the ID of the expanded content region").

⸻

15. Implementation Governance

The Atlas Design System is a design specification. Its translation into production code is the responsibility of engineering, guided by the component specifications, token definitions, and interaction behavior documented in UX-012. Implementation governance defines the conventions that ensure the specification is translated accurately and remains maintainable.

Implementation naming: Component names in code match the system names exactly. "FinalDecisionCard" in code, not "BigCard" or "DecisionSummaryCard." Token names in code match the system token names in category.role.variant structure, adapted to the target language's naming convention (CSS custom properties use `--atlas-space-inter-section`; JavaScript/TypeScript token objects use `space.interSection`). The mapping between design names and code names is documented explicitly.

Component hierarchy: The code component hierarchy mirrors the compositional structure defined in UX-012B Section 17. A Section component contains Conclusion, Reasoning, Comparison, Monitoring, or History components — not the reverse. The hierarchy is enforced through the component API (a parent component accepts a defined set of child component types; it does not accept arbitrary children).

Token mapping: Every visual property in every component implementation references a token — no hardcoded values. Token reference is verified as part of the implementation check (the accessibility review at implementation, Section 14). A component implementation that contains raw hex values, raw pixel sizes, or raw duration values does not pass the implementation check.

Documentation ownership: Every component in the system has a documentation owner (the same role as the component owner from Section 5) who is responsible for keeping the documentation current as the implementation evolves. When a component receives a minor or major version update, the documentation is updated before the version is released. No version ships without corresponding documentation.

Version compatibility: The system uses semantic versioning. Major version changes to shared components are announced to engineering teams with a defined migration timeline before release. The migration timeline is set to two sprint cycles — sufficient time for affected surface implementations to update without blocking other work. Minor and patch versions are non-breaking and do not require migration timelines.

Design-to-code expectations: The design specification produced by UX-012A through UX-012D is the authoritative source for component behavior, states, and semantic meaning. Engineering implementation details (choice of framework, component API design, state management approach) are engineering decisions — they are not specified by UX-012. The test of a correct implementation is that it matches the behavioral specification, not that it matches a specific technical approach.

Future maintenance: As the product evolves, component specifications are the first document to be updated — before implementation begins. Engineering implements against the updated specification. Design and engineering review together confirm that the specification changes are accurately translated. The token system is maintained as a shared artifact — design tokens and implementation token values are kept in sync through a defined process (the specific tooling for this synchronization is an implementation detail outside the scope of UX-012).

⸻

16. Cross-Team Collaboration

The Atlas Design System spans multiple disciplines. Each discipline has distinct responsibilities — and each discipline's work depends on other disciplines working correctly within the system.

Product:
— Owns the product philosophy that governs what belongs in Atlas and what does not.
— Approves new Workspaces by answering the seven Workspace governance questions.
— Resolves conflicts between business requirements and system constraints — when a business requirement would require an anti-pattern, Product decides whether the constraint holds or whether the requirement must be served differently.
— Owns the product vocabulary — the terminology that Atlas uses to describe reasoning states, decision types, and monitoring conditions.

UX:
— Authors component specifications, pattern specifications, and Workspace specifications.
— Conducts design reviews for all new system additions.
— Owns the design documentation within the system, including anti-patterns and usage examples.
— Conducts the consistency audit at each release cycle.
— Maintains the token system at the design layer — defining token names, semantic meanings, and the mapping to global values.

Engineering:
— Translates component specifications into production implementations.
— Maintains the code component library, ensuring implementations match specifications.
— Maintains the implementation token values, keeping them synchronized with the design token system.
— Conducts the implementation accessibility check for each new or updated component.
— Surfaces implementation constraints that may require specification adjustments — when a specified behavior is not achievable in the target environment, Engineering proposes an alternative and UX reviews whether the alternative meets the semantic requirement.

AI (Atlas intelligence team):
— Defines the content of Atlas-generated outputs — what Atlas synthesizes, suggests, proposes, and warns — within the interaction and presentation conventions established by UX-012. *(Corrected per the Atlas UX Architecture UX-012 Authority Migration task, 2026-08-02 — see the Correction Notice above. Prior text: "what Atlas concludes," which risked framing Atlas as an independent authority that concludes truth, contrary to `UX-000-Atlas-UX-Doctrine.md` UXD-R-056.)*
— Ensures that Atlas-generated content follows the language conventions established in UX-012 (calm, direct, honest about uncertainty).
— Coordinates with UX when AI capability changes require new interaction patterns (a new type of Atlas suggestion, a new category of monitoring condition) to ensure the new patterns go through the design review process.

Content:
— Owns the language layer of the Atlas Design System — the specific words used in labels, action names, state names, empty states, validation messages, and AI-generated templates.
— Ensures that all product language follows the Atlas voice established across UX-008 through UX-012 (calm, direct, honest, non-judgmental, precise).
— Reviews all new terminology proposals in the design review process.
— Maintains the Atlas vocabulary — the list of established terms and their definitions.

Research:
— Provides the user evidence that governs system decisions — when a component or pattern needs revision, user research provides the evidence that the current approach is not serving users well.
— Validates that new components and patterns solve real user problems, not hypothetical ones.
— Contributes findings to the governance record — when research reveals that a specific pattern is consistently misunderstood, this finding is documented as evidence for a revision proposal.

The shared obligation across all disciplines: every team member who touches Atlas is responsible for flagging divergences from the system when they observe them — in design reviews, in implementation reviews, in user research sessions. The governance system only works if divergences are caught when they are created, not after they have proliferated across multiple surfaces.

⸻

17. Versioning Strategy

The Atlas Design System uses semantic versioning at three levels: the system level (UX-012 as a whole), the document level (UX-012A, B, C, D, and the assembled UX-012), and the artifact level (individual components, patterns, and tokens).

System-level versioning:
— Major version: a change to the governing philosophy (UX-012A Section 5), the information hierarchy (UX-012A Section 7), or the core semantic color system that affects every surface and requires coordinated migration.
— Minor version: a new component category, a new Workspace template, or a new section of the system specification that does not conflict with existing decisions.
— Patch version: a clarification, correction, or addition that does not change existing decisions.

Document-level versioning:
— Each part document (A, B, C, D) is versioned independently. A change to UX-012B (adding a new component) does not require a new version of UX-012A.
— When a part document reaches a major version, the assembled UX-012 receives a corresponding major version increment.

Artifact-level versioning:
— Components, patterns, and token categories each carry their own version.
— Major version: breaking change — requires migration.
— Minor version: non-breaking addition — no migration required.
— Patch version: fix or clarification — no migration required.
— Experimental: not versioned. Experimental artifacts may change without notice.
— Deprecated: version is frozen at the last stable version. A deprecation notice replaces the changelog.
— Retired: version history is preserved in the archive.

How changes are communicated:
— Patch and minor version changes are communicated through documentation updates and a changelog entry.
— Major version changes are communicated through a migration guide — a document that describes what changed, why it changed, which implementations are affected, and how affected implementations should be updated.
— Deprecation notices are communicated at the time of deprecation, with the replacement identified and the sunset date set. A reminder is issued at the midpoint of the sunset period (one release cycle before retirement).
— All version changes are timestamped and attributed to the change's initiator and approver.

⸻

18. Future Extensibility

The Atlas Design System must remain extensible as Atlas grows — new Workspaces, new AI capabilities, new reasoning contexts that do not yet exist. Extensibility is designed into the system through its structure: a foundation layer (UX-012A) that governs meaning before appearance; a component layer (UX-012B) that builds from recurring semantic patterns; an interaction layer (UX-012C) that defines behavioral tokens rather than specific component behaviors; and a governance layer (UX-012D) that specifies how new additions enter the system.

Every extension should prefer in this order:
1. Existing templates: if a new Workspace fits the Analytical, Monitoring, Comparative, Portfolio, Decision, or Review template defined in UX-012B, the template is used without modification.
2. Existing patterns: if the new Workspace requires a comparison, a conclusion presentation, a monitoring summary, or another recurring composition, the stable pattern from the pattern library is used.
3. Existing components: if the new Workspace requires an assumption record, a challenge item, a monitoring condition, or another established component, the system component is used — not a locally re-implemented variant.
4. Existing tokens: the new Workspace applies existing semantic tokens for all visual properties. New token values are introduced only when a new semantic state genuinely requires them.

New concepts require clear semantic justification: A concept that does not exist in the current system may emerge as Atlas evolves — a new type of decision record, a new category of monitoring condition, a new form of AI assistance. Each new concept must be introduced through the governance process:
— Defined in the vocabulary (what is it, what is it not, how does it differ from the most similar existing concept).
— Specified as a new component or pattern if it requires a new recurring presentation.
— Reviewed through the design review process.
— Documented before implementation.

The extension test: when a new Workspace or feature is proposed, the appropriate question is not "what new design system elements does this need?" but "what existing design system elements does this use?" The new elements — if any — are the residual after maximizing reuse. A new Workspace that requires many new components and patterns is a signal that either the Workspace's reasoning task is not genuinely distinct from existing Workspaces, or that the system needs to evolve to serve a new class of product need that was not anticipated.

Future Workspace types that the system anticipates and is prepared to serve:
— Review Workspace (reviewing a prior decision against current analysis): uses Section, Historical Record, Historical Comparison, Conclusion (Review Conclusion variant), Reasoning, Decision (Decision Review component), and Monitoring components. No new components required.
— Monitoring Workspace (observing a portfolio of active monitoring conditions): uses Section, Monitoring (all variants), Conclusion, and Decision Summary components. Likely requires one new pattern (a monitoring portfolio overview that does not exist as a pattern currently) but no new components.
— Outcome Workspace (reflecting on a completed or superseded decision — what happened, what the decision produced): would require the most new system development of any anticipated Workspace type. Historical components form the basis, but the outcome analysis framing may require a new pattern category. This Workspace should be governed carefully to ensure it does not introduce a reflection-and-blame dynamic that conflicts with the Atlas tone.

⸻

19. Governance Checklist

This checklist is applied to every proposed addition to the Atlas Design System before design review. A proposal that cannot answer every question with a clear, specific answer is not ready for review.

Does this solve a recurring problem?
Name at least two specific Atlas surfaces or contexts where this problem currently exists or will exist. If the problem occurs in only one context, it is a surface-specific implementation detail, not a system addition.

Can an existing pattern, component, or token be reused?
Name the existing system element most similar to the proposed addition and explain precisely why it cannot serve the need. "It looks different" is not an answer. "It represents a different product meaning because..." is an answer.

Does it improve reasoning?
Describe specifically how this addition makes the user's reasoning clearer, more structured, or less cognitively demanding. If the addition improves visual polish without improving reasoning, it belongs in a surface-specific design refinement, not in the system.

Does it preserve accessibility?
Confirm that the addition meets every accessibility token requirement: contrast ratios, touch targets, keyboard navigation, screen reader labels, non-color state communication, and reduced-motion behavior. If any requirement is not met, the proposal is not ready for review.

Does it preserve historical integrity?
If the addition involves any content that was authored or recorded in the past, confirm that the addition cannot overwrite, hide, or modify that content. If the addition changes how historical content is displayed, confirm that the underlying data is unchanged.

Does it increase cognitive load?
Describe any new vocabulary, new interaction pattern, or new visual treatment introduced by this addition that the user must learn. Justify why this learning cost is acceptable given the benefit. A zero-learning-cost addition (reusing existing patterns and terms) is always preferred.

Does it introduce terminology drift?
Confirm that every term used in the addition is from the established Atlas vocabulary, or name the new term and provide its vocabulary entry (definition, usage contexts, comparison with most similar existing terms).

Is it future-proof?
Describe one likely future Atlas evolution (a new Workspace, a new AI capability, a new decision type) and explain how this addition would interact with that evolution. Confirm that the addition does not foreclose a likely future option or create a dependency that would be difficult to change.

Does it follow naming conventions?
Confirm that the component, pattern, token, or template name follows the naming conventions from Section 4. Read the proposed name aloud — does it describe product meaning or visual appearance?

Is the documentation complete?
Confirm that the documentation includes purpose, meaning, usage, states (if applicable), variants (if applicable), composition, accessibility, responsive behavior, at least one positive example, at least one anti-pattern, and version.

⸻

20. Governance Audit

Reviewing the complete governance model against its stated objectives:

Long-term maintainability: The system defines ownership (every artifact has an owner), versioning (changes are tracked at three levels), documentation standards (every artifact is documented before release), and a retirement process (deprecated artifacts are removed after a defined sunset period). A system maintained under these rules can remain coherent as contributors change and as the product evolves over years.

Consistency: The consistency audit process (Section 11) provides a repeatable, fourteen-dimension evaluation framework. The anti-patterns catalogue (Section 12) makes the most common failure modes explicit before they occur. The naming conventions (Section 4) prevent the terminology drift that is typically the first sign of a fragmenting system.

Clarity: The governance checklist (Section 19) provides a clear entry point for any new addition — the questions are specific, answerable, and sufficient to determine whether a proposal is ready for review. The component governance process (Section 5) is staged — experimental, candidate, stable — with defined criteria for each transition. There is no ambiguity about what is required at each stage.

Future extensibility: The extensibility framework (Section 18) establishes a preference ordering (templates → patterns → components → tokens) that defaults to reuse before creation. The extension test ("what existing elements does this use?" before "what new elements does this need?") operationalizes this preference in practice. The three anticipated future Workspace types demonstrate that the system is prepared for likely growth without requiring new infrastructure.

Engineering readiness: The implementation governance section (Section 15) defines the naming conventions, component hierarchy, token mapping, documentation ownership, and version compatibility requirements that engineering needs to translate the specification into production. The accessibility governance section (Section 14) defines the implementation accessibility check as a mandatory step, ensuring that accessibility is verified in code, not just in the specification.

Alignment with Atlas philosophy: Every governance rule in this document can be traced back to one of the fifteen universal design principles from UX-012A Section 5. The anti-patterns catalogue maps each failure mode to the principle it violates. The component philosophy (Section 1 of UX-012B) — components exist for recurring product meanings, not for visual reusability — is the direct application of the principle that every visual element must improve comprehension. Governance is not a bureaucratic addition to Atlas; it is the mechanism by which Atlas's principles are enforced as the product grows.

⸻

What UX-012D Establishes

The following governance, token, naming, migration, documentation, and evolution decisions are now fixed.

Governance philosophy: Three governing reasons for the system (coherence is a product quality; design systems drift without governance; semantic consistency is more important than visual novelty). The governing principle: every new pattern requires a justification that the existing system cannot satisfy the need. Governance is not implementation.

Design token philosophy: Why Atlas uses semantic tokens (stability of meaning, reviewability, documentation). Fifteen token categories fully described: Typography, Spacing, Layout, Semantic Colors, Surface, Borders, Elevation, Radius, Icons, Motion, Focus, Interaction, Accessibility, Responsive, State.

Semantic token model: Thirteen semantic token groups — Primary Conclusion, Supporting Reasoning, User Authored, Historical Content, Monitoring, Decision, Opportunity, Contradiction, Warning, Completed, Disabled, Loading, Focus — each with governing meaning and representative token names. The principle that semantic token names do not change when underlying values change.

Naming conventions: Rules for components (two or three words, noun describes product object), patterns (reasoning relationship), states (Atlas vocabulary from UX-012B), Workspaces (reasoning question), tokens (category.role.variant), templates (Workspace type), actions (Verb + Noun), sections (content role), AI behaviors (conversational role), history and monitoring (standardized prefixes). Twelve prohibited naming styles.

Component governance: Ownership (one named role per component), five-step approval process (problem statement, existing system check, specification, accessibility review, owner approval), documentation requirements (ten mandatory sections), three-part semantic versioning, deprecation sequence (notice → migration period → retirement), experimental status, retirement process.

Pattern governance: Seven pattern categories with governance notes. Draft → candidate → stable → deprecated → retired maturity stages. Rules for when new patterns are justified and how duplicates are prevented.

Workspace governance: Seven mandatory questions before any new Workspace design begins. Review process requirement.

Documentation standards: Ten mandatory documentation sections for every artifact, in defined order: purpose, meaning, usage, states, variants, composition, accessibility, responsive behavior, examples, anti-patterns, history, version. The principle: documentation explains why before what.

Design review process: Six review criteria (semantic necessity, reuse potential, clarity, accessibility, consistency, future impact). Review process specified for seven artifact types (component, pattern, token, Workspace, interaction/motion, terminology, visual style).

Migration strategy: Eight stages (Inventory, Semantic Mapping, Consolidation, Token Adoption, High-Impact Alignment, Component Implementation, Surface Migration, Audit and Governance). Three semantic mapping classifications (aligned, justified variation, divergence). Surface migration order: Decision Workspace as reference, then Investment, Portfolio, Dashboard.

Consistency audit: Fourteen dimensions (hierarchy, spacing, typography, interaction, components, patterns, states, tokens, language, responsiveness, accessibility, history, AI collaboration, completion). Three audit output classifications (aligned, justified variation, divergence). Audit cadence (full audit before major release, targeted audit after significant changes, new Workspace audit before release).

Anti-patterns: Thirteen named anti-patterns — visual novelty without meaning, duplicate components, duplicate terminology, overloaded cards, dashboard thinking, AI domination, traffic-light investment logic, hidden history, unnecessary animations, component proliferation, token duplication, inconsistent empty states, complexity escalation — each with description, violated principle, and correct alternative.

Design system evolution: Component and pattern maturity model (experimental → candidate → stable → deprecated → retired). Token evolution (global values change; semantic names stay stable). Workspace evolution (adding sections through lighter governance than creating new Workspaces). Obsolete artifact retirement process. Compatibility through the token system.

Accessibility governance: Mandatory reviews at four stages (specification, design review, implementation, consistency audit). Token requirements for contrast, touch targets, minimum text size, focus ring, reduced motion. Component, interaction, and responsive requirements. Documentation expectations written as requirements, not guidelines.

Implementation governance: Implementation naming conventions (matches system names), component hierarchy (mirrors UX-012B compositional structure), token mapping (all properties reference tokens, no hardcoded values), documentation ownership, version compatibility (two-sprint migration timeline for major versions), design-to-code expectations (specification governs behavior; engineering decides technical approach).

Cross-team collaboration: Five disciplines defined (Product, UX, Engineering, AI, Content, Research) with distinct responsibilities. Shared obligation: all team members flag divergences when observed.

Versioning strategy: Three levels (system, document, artifact) with semantic versioning at each. Change communication: patch/minor through changelog, major through migration guide, deprecation through advance notice with sunset reminder.

Future extensibility: Preference ordering for extensions (templates → patterns → components → tokens). Extension test (what existing elements does this use?). New concept introduction process. Three anticipated future Workspace types and their component needs.

Governance checklist: Ten questions applied to every proposed system addition before design review, covering: recurring problem evidence, existing system review, reasoning improvement, accessibility compliance, historical integrity, cognitive load assessment, terminology drift check, future-proof assessment, naming convention compliance, documentation completeness.

⸻

Remaining Governance Questions

1. The tooling for design token synchronization between design and code:
UX-012D defines the token system at the semantic level — the names, the categories, the relationships. The specific tooling (design tokens plugin in Figma, style-dictionary, custom build step, or other mechanism) that synchronizes token values between the design specification and the production codebase has not been specified. This is an implementation decision, but the choice of tooling affects how feasible it is to maintain token synchronization as the system evolves.
Evidence needed: Engineering feasibility assessment of token synchronization options in the Atlas technical stack. Does not block UX-012E.

2. The specific atlas vocabulary document:
UX-012D defines the naming conventions and the requirement for a maintained Atlas vocabulary — the list of established terms and their definitions. The vocabulary document itself has not been produced as part of UX-012. It should be a living document, updated through the terminology review process at each design review cycle.
Evidence needed: A dedicated vocabulary document produced as a companion to UX-012. Does not block UX-012E.

3. The governance ownership structure at launch:
UX-012D defines "a named product role" as the owner for each component, pattern, and document. At Atlas's current stage, the specific ownership assignments have not been made. Ownership assignment is a product team decision — UX-012D establishes the requirement and the framework, not the specific assignments.
Evidence needed: Product team ownership assignment meeting. Does not block UX-012E.

4. The migration timeline and prioritization:
The migration strategy defines eight stages in sequence. The specific timeline — how long each stage will take, which divergences are highest priority within Stage 5, what constitutes "significant design change" for targeted audit purposes — depends on the current state of each surface implementation and the product team's release calendar.
Evidence needed: Stage 1 inventory completion. Does not block UX-012E.

5. Whether the Outcome Workspace is a product commitment:
UX-012D names the Outcome Workspace as an anticipated future Workspace and notes it would require new system development. Whether this Workspace is actually on the product roadmap — and therefore whether the system should proactively prepare for it — is a product decision. If it is on the roadmap, the system should conduct an early specification pass for the new pattern category it would require.
Evidence needed: Product roadmap review. Does not block UX-012E.

⸻

Requirements for UX-012E

UX-012E is the final document in the UX-012 series. Its purpose is to assemble UX-012A, UX-012B, UX-012C, and UX-012D into one coherent, complete specification — the full Atlas Design System & Workspace Consistency Specification — and to produce the synthesis outputs that can only be created after all four parts are complete.

UX-012E must accomplish the following:

Cross-document consistency audit:
Review all four part documents for: conflicting statements about the same artifact or behavior; terminology that varies between documents for the same concept; component specifications in UX-012B that conflict with interaction specifications in UX-012C; token names defined in UX-012D that conflict with references in UX-012A or UX-012B; governance rules in UX-012D that are inconsistent with the component and pattern governance described in UX-012B. Resolve every conflict — either by choosing one version and correcting the other, or by clarifying that the two statements address different aspects of the same question.

Duplication removal:
Identify content that is substantially repeated across documents — definitions of principles that appear in multiple parts, descriptions of the same component behavior in UX-012B and UX-012C, accessibility requirements stated in UX-012A, UX-012B, and UX-012C. Consolidate duplicated content into its most appropriate location and replace other instances with cross-references. The assembled UX-012 should not require the reader to reconcile conflicting or redundant versions of the same specification.

Terminology conflict resolution:
Produce a complete glossary of all terms used across UX-012A through UX-012D. Identify any terms used differently between documents. Resolve all conflicts and produce a single canonical definition for each term. The assembled UX-012 uses one vocabulary.

Component validation:
For each component defined in UX-012B, confirm that: its interaction behavior is fully specified in UX-012C; its token references are fully defined in UX-012D; its governance requirements are satisfied by the component governance model in UX-012D; its accessibility specification meets all accessibility token requirements from UX-012D. Identify and fill any gaps.

Pattern validation:
For each pattern identified in UX-012B and UX-012C, confirm that: the component composition is consistent across both documents; the interaction behavior specified in UX-012C is consistent with the component behaviors in UX-012B; the governance model from UX-012D applies correctly to each pattern's maturity stage.

Workspace consistency validation:
For each existing Atlas Workspace (Dashboard, Investment Workspace, Portfolio Workspace, Decision Workspace), produce a validation summary confirming that the workspace's current specification is consistent with the assembled UX-012. Identify specific areas where the Workspace specification should be updated to align with the system (these are inputs to the Stage 1 migration inventory).

Initial Atlas Component Inventory:
Produce the structured inventory of reusable components and patterns that should enter the Atlas Design System first — organized by category (foundations, navigation and Workspace frame, reasoning, comparison, decision, monitoring, history, AI collaboration, states and feedback, completion), with for each component: current source Workspace, expected reuse across surfaces, maturity level (experimental/candidate/stable), whether consolidation is needed across surfaces, and priority for implementation.

Final Governing Principles:
Distill the governing principles from all four part documents into one complete, non-redundant set — the principles that govern every Atlas design decision, now and in the future. These should be more specific than the fifteen principles in UX-012A (which are the universal principles) and should reflect everything learned across the full specification process. The Final Governing Principles should be sufficiently precise that a designer who reads only this list can make correct decisions about novel situations not explicitly covered in the specification.

Assembled UX-012 document:
Produce the complete, assembled UX-012 — the Atlas Design System & Workspace Consistency Specification — incorporating: the full content of UX-012A through UX-012D, revised to remove conflicts and duplications; the Initial Atlas Component Inventory; the Final Governing Principles; a complete glossary; an index of all defined components, patterns, tokens, and templates. The assembled document should be self-contained — a reader who has not read the part documents should be able to understand the full system from UX-012 alone.

The assembled UX-012 is the governing document for all future Atlas design and implementation work. It supersedes UX-012A, UX-012B, UX-012C, and UX-012D as individual documents — those remain as version-controlled references, but UX-012 is the authoritative source.

Do not produce UX-012E yet.

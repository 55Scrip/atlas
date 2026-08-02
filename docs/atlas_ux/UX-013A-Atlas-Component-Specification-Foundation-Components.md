# UX-013A — Atlas Component Specification: Foundation Components

Governing references: UX-012 — Atlas Design System & Workspace Consistency Specification, and all previously approved Atlas UX specifications.

Volume 1 of the Atlas Component Library. This document specifies every Foundation Component in production-ready detail. Figma components can be built directly from these specifications. Engineering can implement without inventing behavior. Future designers can extend Atlas without reinterpretation.

**Correction Notice (Phase 3E, governed by `ADR-004-Scenario-Analysis-Comparison-and-Sequence-Authority-Resolution.md`'s own committed Corpus-Wide Scenario Comparison Extension addendum — 2026-07-27):** This document's "Requirements for UX-013B" section previously named "Scenario Comparison" among the Comparison Components UX-013B was expected to specify. Per the ADR-004 addendum, "Scenario Comparison" is not, and was never validly, an independently adopted Comparison component or a required named Comparison variant — Scenario Analysis (`UX-013B-Atlas-Component-Specification-Reasoning-Components.md` §9) exclusively owns scenario-specific analytical content, and Comparison (UX-013B §8) is a generic, non-owning renderer. This correction removes "Scenario Comparison" from that scope-list mention; the remaining five Comparison Components (Before/After, Alternative Comparison, Opportunity Cost Component, Allocation Comparison, Historical Comparison) are unaffected. This is this document's first correction under this program; all content outside this single mention is unchanged. This correction is documentary only — it introduces no new component, variant, state, interaction, or architecture, and does not amend ADR-002, ADR-003, or ADR-004. Finding F-2 and any other unrelated matter remain untouched.

**Correction Notice (Phase 5, governed by the Atlas UX Source Correction Plan's own Section 22 Q2-resolved corpus-wide cross-reference sweep — 2026-07-28):** A corpus-wide mechanical inventory, followed by human semantic disposition per Section 22's Q2 resolution, found this document's Responsive Behavior section (Mobile) citing "Long-Form Editor spec in UX-013D" as the governing source for full-screen mobile editing mode. Per ADR-002 C-05, `UX-013D` does not exist anywhere in the committed repository. The citation was also substantively wrong, independent of UX-013D's absence: Long-Form Editor's own identity, states, and autosave behavior are, and always were, specified in `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §29 ("Editing Components"), not in any UX-013-series document; the specific full-screen mobile editing rule this passage describes is separately stated in UX-012 §45 ("Editing Behavior": "Mobile editing: full-screen editing mode on mobile — the Workspace body is replaced with the editing surface; done/save returns to the Workspace"). This correction replaces the stale citation with the accurate one, naming both supporting sections. Prior text: "Full-screen editing mode for authoring components (see Long-Form Editor spec in UX-013D)." No behavior, state, or interaction is changed by this correction — only the citation. This correction does not resolve, reopen, or take any position on Q1, Finding F-2, ADR-002 C-05, or any canonical-authorship question.

**Correction Notice (Atlas UX Architecture Foundation Motion/Interaction Consistency Correction task — 2026-08-02):** This is a later, additive correction; it does not revise, replace, or reopen any notice above. The completed Reasoning Token Architecture Phase 3B: Motion & Interaction Foundations task (2026-08-02) established `opacity.interaction.hover` and `opacity.loading.pulse.min`/`.max` as the canonical `UX-012D` §3 tokens for hover-opacity treatment and loading-opacity treatment, respectively, and retired `interaction.hover.background` and `motion.loading` as unsupported names. This document still contained legacy references to both. This correction aligns this document's own token references to the now-canonical names. No component behavior, interaction, accessibility, loading, or animation timing is changed by this correction.

**Correction Notice (Atlas UX Architecture Foundation & Collaboration Token Alignment task — 2026-08-02):** This is a later, additive correction; it does not revise, replace, or reopen any notice above. The completed Cross-Document Token Consistency Audit (2026-08-02) found that this document retained numerous legacy token references — bare `text.*`, bare `border.*`, bare `status.*`, bare `action.*`, superseded `focus.ring.*` ordering, bare `motion.<event>`, and undocumented `progress.*`/`loading.skeleton.*` references — after the canonical `UX-012D` architecture had evolved through the completed Reasoning Token Architecture program (Phases 1 through 3C, 2026-08-02). This correction aligns Foundation Components with `UX-012D` and those completed mappings, following the identical semantic-role analysis already applied to Reasoning Components. **This correction is presentation-token-only.** No component identity, anatomy, state, interaction, accessibility behavior, responsive behavior, ownership, or Product meaning changes anywhere in this document. No new top-level token namespace is introduced — every replacement below reuses a token `UX-012D` already defines. A small number of items have no canonical `UX-012D` equivalent (a focus-ring offset value, three Motion events never formalized beyond Reasoning-tier usage, and a progress-bar/skeleton fill treatment) — these are not guessed into a plausible-looking token; they are disclosed as missing foundations, in prose, exactly where they occur, and in the traceability record at Section 18, below. The full traceability record — every prior token, its replacement or disclosed non-replacement, and its rationale — appears in the new Phase 4: Foundation Token Alignment subsection, Section 18, below.

**Correction Notice (Atlas UX Architecture Foundation Token Alignment (UX-013A Final Alignment) task — 2026-08-02):** This is a later, additive correction; it does not revise, replace, or reopen any notice above. The completed Missing Foundation Resolution Phase 1: UX-012D Canonical Foundation Additions task (2026-08-02) established five of the nine foundations the notice above disclosed as missing: `color.border.hairline` and `color.border.standard` (`UX-012D` §3, new Border group), and `motion.open.duration`/`.easing`, `motion.close.duration`/`.easing`, `motion.navigate.duration`/`.easing` (`UX-012D` §3, Motion Architecture group, extended). This correction replaces the temporary implementation-prose treatment those five items previously required — written only because no canonical token yet existed — with the now-canonical token references, throughout this document and in Section 18's own consolidated tables. **No component behavior, anatomy, interaction, accessibility behavior, or Product meaning changes anywhere in this document. No component is redesigned. No new token is introduced — every replacement below cites a token `UX-012D` already defines.** Four items remain exactly as disclosed by the notice above and are unaffected by this correction: focus-ring offset, `progress.fill`, `progress.track`, and `loading.skeleton.base` — none of these was added by the governing `UX-012D` task, and none is touched here. The full traceability record for this correction appears in the new Phase 5: Foundation Foundation-Extension Alignment subsection, Section 18, below.

---

# Foundation Component Philosophy

## Why Foundation Components Are Structural Rather Than Functional

Foundation Components are the load-bearing architecture of every Atlas Workspace. They do not communicate reasoning content. They do not hold investment data. They do not express decisions. They create the structural conditions under which reasoning components can do their work.

A Workspace Frame is not a card. A Section Header is not a navigation element. A Divider is not a decoration. Each Foundation Component exists to establish spatial, hierarchical, and behavioral structure — the surface on which all reasoning content appears.

Because Foundation Components are structural, they must be visually restrained. They should recede. The user's attention should never rest on the frame; it should move through the frame to the content within it.

## How Foundation Components Create Consistency

Every Atlas Workspace is built from the same Foundation Components in the same configuration. A user who has navigated one Workspace can navigate all others without learning a new structure. They already know where the header is, where the footer is, how sections expand, how navigation returns them to their origin.

This structural consistency is not aesthetic uniformity. Different Workspaces have different content, different Section sequences, different density. But the structural skeleton — Frame, Header, Toolbar, Footer, Section Containers, Navigation — is identical. Users carry their mental model of the Workspace architecture from context to context.

## Why Foundation Components Must Remain Visually Restrained

Reasoning is cognitively expensive. Every pixel of decorative structure competes for the same attentional budget as the reasoning content the user is trying to absorb. Foundation Components should create invisible scaffolding — present enough to establish clarity, quiet enough to disappear when the user is reading.

This restraint is expressed in:
- Surface colors that differ from content only enough to establish hierarchy
- Borders that establish edges without drawing attention
- Typography that is present but subordinate
- Motion that occurs only on user-initiated structural changes

## How Foundation Components Support Reasoning Before Interaction

Before a user reads a single sentence of reasoning content, Foundation Components have already communicated:
- Where they are (Workspace Header)
- Where they can go (Navigation Bar, Return control)
- What state their work is in (Draft Indicator, Status Badge in Header)
- How the Workspace is structured (Section Containers, Section Headers)
- What action is available when they are ready (Footer, Completion Action)

This pre-reasoning orientation reduces cognitive overhead. The user arrives at the content already oriented. They do not need to explore the interface to understand it.

## Governing Principles for All Foundation Components

**1. Structure before content.** Foundation Components establish spatial and hierarchical context. They must be rendered and stable before reasoning content loads.

**2. One structural purpose per component.** Each Foundation Component has a single, non-overlapping structural role. The Frame contains. The Header identifies. The Footer completes. No component inherits another's role.

**3. Invisible when working correctly.** A Foundation Component that the user notices is competing with content. Restrained color, weight, and motion keep Foundation Components structurally present but perceptually quiet.

**4. Consistent position, every Workspace.** The Workspace Frame always contains the same structural hierarchy. The Header is always at the top. The Footer is always at the bottom. Return navigation is always in the same position. Users never search for structure.

**5. Accessible by default.** Foundation Components are the first layer of the accessibility model. Keyboard navigation, focus order, landmark roles, and screen reader regions are defined at the Foundation Component level, before reasoning content is considered.

**6. Token-mapped throughout.** No Foundation Component contains a hardcoded visual value. Every color, spacing, radius, border, and typography value is a semantic token reference.

---

# 1. Workspace Frame

## Purpose

The Workspace Frame is the outermost structural container of every Atlas Workspace. It establishes the maximum width, horizontal centering, vertical scroll context, safe areas, and the stacking order of the Header, body, and Footer. Every other component in a Workspace lives inside the Workspace Frame.

## Semantic Meaning

The Frame communicates containment without enclosure. It is not a card, a panel, or a modal. It is the Workspace itself — the surface on which all reasoning occurs. Its visual restraint communicates that the content within it is primary and the frame is secondary.

## When Used

In every Atlas Workspace. There is exactly one Workspace Frame per Workspace view.

## When Not Used

Inside an overlay, dialog, or Historical Record overlay. Overlays have their own contained structure that does not inherit the Workspace Frame.

## Responsibilities

- Establishes the maximum content width
- Centers the content horizontally in the viewport
- Maintains safe padding at all breakpoints
- Creates the vertical scroll context for the Workspace body
- Stacks Header (sticky), scrollable body, and Footer (sticky) in correct order
- Provides the containing block for sticky elements

## Boundaries

The Frame is responsible for horizontal centering and maximum width only. It does not control the content width of individual Sections (those are governed by Layout Containers within the body). It does not control vertical spacing between Sections (governed by Section Containers).

## Variants

**Standard** — For Dashboard, Investment Workspace, Portfolio Workspace, Decision Workspace. Centered, maximum-width constrained, full-viewport-height.

**Overlay** — Not a Workspace Frame variant. Overlays (Historical Records, Dialogs) use their own container. Do not extend the Workspace Frame for overlay content.

## Anatomy

```
WorkspaceFrame
├── Header (sticky, always rendered)
├── Body (scrollable)
│   └── [Section Containers, content components]
└── Footer (sticky, conditional)
```

## Properties

| Property | Type | Default | Required | Notes |
|----------|------|---------|----------|-------|
| `workspaceId` | string | — | Yes | Unique identifier for the Workspace instance |
| `variant` | `'standard'` | `'standard'` | No | Only standard in v1 |
| `hasFooter` | boolean | `true` | No | False on Dashboard |
| `isLoading` | boolean | `false` | No | Triggers loading state |
| `className` | string | — | No | Engineering extension point only |

## States

**Default** — Header, scrollable body, and Footer rendered. Content populates normally.

**Loading** — Skeleton placeholders in the body. Header and Footer remain rendered (preventing layout shift). Loading token animation applies.

**Draft-present** — Draft Indicator visible in the Header. Body content in Unsaved state where applicable. No structural change to the Frame itself.

**Historical-mode** — Historical Indicator visible in the Header. All editable controls within the body are disabled. The Frame itself does not change visually; it hosts the Historical Indicator passively.

**Error** — Connection or critical load failure. Header remains rendered. Body shows the Error empty state. Footer remains rendered if it was previously visible.

## Layout Specifications

**Maximum content width:** 1200px. Above this viewport width, the content is centered with equal horizontal margins.

**Minimum width:** 320px. Below this width, the layout is not specified and not supported.

**Horizontal padding:**
- Desktop (≥1024px): 48px on each side within the maximum-width container
- Tablet (768px–1023px): 32px on each side
- Mobile (<768px): 16px on each side

**Vertical structure:**
- Header: sticky to the top of the viewport. Height is determined by its content (see Workspace Header specification).
- Body: `flex: 1; overflow-y: auto`. Fills remaining height between Header and Footer.
- Footer: sticky to the bottom of the viewport when present. Height is determined by its content.

**Safe areas:** On mobile devices, the Frame respects `env(safe-area-inset-*)` values. Footer bottom padding is augmented by `env(safe-area-inset-bottom)`.

## Scrolling

Vertical scrolling occurs on the Body region only. The Header and Footer remain fixed relative to the viewport. No horizontal scroll at any breakpoint (content adapts to viewport width).

Scroll position is stored per `workspaceId` and restored when the user returns to a Workspace. Restoration is exact (scrollTop to the stored value), with a brief Layout token applied if the scroll distance is greater than one viewport height.

## Sticky Behavior

**Header:** `position: sticky; top: 0; z-index: [frame.header.zIndex]`. Sticky throughout scroll. Does not collapse or compress on scroll.

**Footer:** `position: sticky; bottom: 0; z-index: [frame.footer.zIndex]`. Sticky throughout scroll. Visible when `hasFooter` is true.

**Section-level sticky headers:** Individual Section Headers may be sticky within the Body scroll context. Their z-index must be below the Workspace Header z-index. See Section Header specification.

## Responsive Behavior

**Desktop (≥1024px):** Full layout. Maximum-width container centered. 48px side padding. Header, scrollable body, sticky Footer.

**Tablet (768px–1023px):** Same structural model. 32px side padding. Some nested layout containers stack (governed by their own specs). Touch targets meet 44×44px minimum.

**Mobile (<768px):** 16px side padding. Single-column layout throughout. Full-screen editing mode for authoring components (see Long-Form Editor, `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` §29 for component identity, and §45 for the specific full-screen mobile editing rule). Footer action is full-width.

## Accessibility

- The Workspace Frame root element is the `<main>` landmark. One per page.
- `aria-label` on `<main>`: the Workspace title (e.g., `"Investment Workspace — Acme Corp"`).
- The Header region uses `<header>` element (implicit `banner` landmark).
- The Footer region uses `<footer>` element (implicit `contentinfo` landmark).
- When the Frame enters loading state, `aria-busy="true"` is applied to the `<main>` element.
- When historical mode is active, `aria-label` updates to include "Historical Record — [date]".

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Body background | `surface.background` |
| Maximum width | `layout.workspace.maxWidth` |
| Side padding (desktop) | `space.workspace.horizontal.desktop` |
| Side padding (tablet) | `space.workspace.horizontal.tablet` |
| Side padding (mobile) | `space.workspace.horizontal.mobile` |
| Header z-index | `elevation.header.zIndex` |
| Footer z-index | `elevation.footer.zIndex` |

## Composition Rules

- **Contains:** Workspace Header (required), Body (required), Workspace Footer (conditional).
- **Cannot contain:** Another Workspace Frame. Dialogs or overlays (those use Dialog Container).
- **Is contained by:** Nothing. The Workspace Frame is the root layout component.

## Engineering Notes

- Implement as a full-height flex column: `display: flex; flex-direction: column; min-height: 100dvh`.
- Body region: `flex: 1; overflow-y: auto; overscroll-behavior: contain`.
- Scroll position management: store and restore using the `workspaceId` as the storage key. Restoration happens on mount, before first paint (use layout effect, not effect).
- The Frame must render synchronously. No lazy-loading the structural shell.
- Do not use `position: fixed` for Header or Footer — use sticky within a defined scroll container.

## Figma Structure

```
WorkspaceFrame [Frame, Auto Layout, vertical]
├── WorkspaceHeader [Frame, Auto Layout, horizontal] — fixed height
├── Body [Frame, Fill, vertical scroll] — Fills remaining space
└── WorkspaceFooter [Frame, Auto Layout, horizontal] — fixed height, conditional
```

Constraints: Frame fills viewport (use 100% width, 100dvh height in prototype context). Use Figma's "Clip content" on Body region.

## Anti-Patterns

- **Do not nest Workspace Frames.** One per Workspace, always.
- **Do not add decorative borders or shadows to the Frame.** The Frame surface should be the background; decoration belongs in content components.
- **Do not make the Header collapsible or auto-hide on scroll.** The Header must remain visible at all times for orientation.
- **Do not add animated entrance transitions to the Frame itself.** The Frame should appear instantly; the Open motion token applies to content regions, not the structural container.

---

# 2. Workspace Header

## Purpose

The Workspace Header identifies the Workspace, its subject, and its current state. It provides return navigation and hosts persistent status indicators. It is the primary orientation element — the first thing a user reads when entering a Workspace.

## Semantic Meaning

The Header communicates: you are here, looking at this, in this state. It answers three questions before the user reads a word of reasoning content: What Workspace am I in? What is it about? What state is my work in?

## When Used

In every Atlas Workspace. There is exactly one Workspace Header per Workspace Frame.

## When Not Used

In Dialog containers or Historical Record overlays. Those have their own header structures.

## Anatomy

```
WorkspaceHeader
├── Left: Return Navigation
├── Center: Identity
│   ├── Workspace Type Label (e.g., "Investment Workspace")
│   ├── Subject Title (e.g., "Acme Corp")
│   └── [Optional] Subject Subtitle (e.g., "Series B — $4.2M position")
└── Right: Status Area
    ├── [Conditional] Draft Indicator
    ├── [Conditional] Historical Indicator
    ├── [Conditional] Monitoring Badge
    └── [Conditional] Background Processing Indicator
```

## Properties

| Property | Type | Default | Required | Notes |
|----------|------|---------|----------|-------|
| `workspaceTypeLabel` | string | — | Yes | e.g., "Decision Workspace" |
| `subjectTitle` | string | — | Yes | Primary identity of the Workspace subject |
| `subjectSubtitle` | string | — | No | Secondary identifier |
| `returnDestination` | `'dashboard' \| 'source'` | `'dashboard'` | No | Controls return navigation label |
| `returnLabel` | string | auto | No | Overrides derived return label |
| `hasDraftIndicator` | boolean | `false` | No | |
| `hasHistoricalIndicator` | boolean | `false` | No | |
| `historicalDate` | Date | — | No | Required when `hasHistoricalIndicator` is true |
| `monitoringBadgeCount` | number | 0 | No | 0 = badge not shown |
| `isBackgroundProcessing` | boolean | `false` | No | |

## Variants

**Standard** — Subject title + optional subtitle. Used in Investment Workspace, Portfolio Workspace, Decision Workspace.

**Dashboard** — No subject identity (the Dashboard is not about a specific subject). Shows portfolio name or account name as the title. No subject subtitle.

**Historical** — Historical Indicator is present. All editing controls in the body are disabled. Historical Indicator is visually prominent (not dismissible within this state).

## Identity Hierarchy

1. **Workspace Type Label** — Role 4 typography (Supporting Label). Positioned above the Subject Title. All-caps not used; Sentence case. Examples: "Investment Workspace", "Decision Workspace", "Portfolio Workspace".

2. **Subject Title** — Role 2 typography (Section Heading weight). The name of the investment, portfolio, or decision topic. Maximum one line; truncates with ellipsis. Full content available on hover (tooltip) and in the ARIA label.

3. **Subject Subtitle** — Role 5 typography (Contextual Text). Secondary identifier: position size, date, or context. Optional. Maximum one line.

## Return Navigation

- Positioned at the left edge of the Header.
- Label: "Dashboard" (default) or the source Workspace name when navigated from a specific Workspace.
- Includes a left-pointing chevron or equivalent directional indicator.
- On click/tap: navigates to the return destination, preserving current Workspace state (scroll, draft, expansion).
- Minimum touch target: 44×44px.
- Focus: included in the Workspace Header tab order, before the identity area.

## Status Area

**Draft Indicator:** Text label "Draft" in Role 5 typography. Accompanied by last-autosave timestamp. Presentation: neutral — no distinct semantic color, per `UX-012B` §13 and the Status Badge Token Architecture Correction (2026-08-02, §13, above); communicated by the text label alone. Appears when any unsaved user content exists in the Workspace. Disappears on save completion.

**Historical Indicator:** Text label "Historical Record" in Role 4 typography. Accompanied by the historical record date. Color: `color.text.historical`. Appears when the user is viewing historical content. Persists for the duration of the historical viewing session.

**Monitoring Badge:** A numeric badge indicating the count of active Monitoring Conditions in Triggered or Approaching state. Positioned on or near a monitoring icon. Clicking navigates to the monitoring surface. Present only when `monitoringBadgeCount > 0`.

**Background Processing Indicator:** A subtle inline animation (Loading token) with a brief label (e.g., "Updating"). Present only during background operations longer than 3 seconds. Disappears automatically on completion.

## States

**Default** — Standard layout, no status indicators active.
**Draft-present** — Draft Indicator visible in status area.
**Historical-mode** — Historical Indicator visible. Subject title updates to include historical context.
**Monitoring-active** — Monitoring Badge present with count.
**Background-processing** — Processing indicator present.
**Loading** — Header renders immediately with subject identity (no skeleton). Content below may be loading but the Header is never in a loading state itself.

## Responsive Behavior

**Desktop:** Full anatomy as specified. Identity centered or left-aligned depending on Workspace type. Status area right-aligned.

**Tablet:** Same layout. Touch targets padded to 44×44px. Subtitle may be suppressed on narrower tablet widths (below 900px) if it would cause overflow.

**Mobile:** Return navigation becomes an icon-only control (left chevron, labeled with `aria-label`). Workspace Type Label is suppressed. Subject Title only. Status indicators reduced to icon form with accessible labels.

## Spacing

- Header height (desktop): determined by content, minimum 56px, typical 64–72px.
- Internal horizontal padding: matches Workspace Frame side padding.
- Vertical padding: `space.header.vertical` (top and bottom).
- Identity stack: `space.level2` between Workspace Type Label and Subject Title.

## Accessibility

- Implemented as `<header>` element (ARIA `banner` landmark).
- Subject Title: `<h1>`. One `<h1>` per page.
- Return Navigation: `<a>` or `<button>` with `aria-label="Return to [destination]"`.
- Draft Indicator: `aria-live="polite"` region. Announces on state change.
- Historical Indicator: Included in `<h1>` via visually hidden text.
- Monitoring Badge: `aria-label="[count] monitoring conditions require attention"`.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Header background | `surface.header` |
| Header border-bottom | `color.border.standard` |
| Workspace Type Label color | `color.text.secondary` |
| Subject Title color | `color.text.primary` |
| Subject Subtitle color | `color.text.tertiary` |
| Return control color | `color.text.tertiary` |
| Draft Indicator color | None — neutral default text, no color distinction (per Status Badge Token Architecture Correction, §13, above) |
| Historical Indicator color | `color.text.historical` |
| Monitoring Badge background | `surface.elevated` — a neutral, distinguished surface; not a warning or contradiction color (see §18 traceability for the Monitoring Badge severity-ambiguity rationale) |
| Monitoring Badge text | `color.text.primary` |

## Figma Architecture

```
WorkspaceHeader [Frame, Auto Layout, horizontal, 100% width]
├── ReturnNavigation [Frame, Auto Layout, horizontal] — left aligned
│   ├── ChevronLeft [Icon, 16px]
│   └── ReturnLabel [Text, Role 4]
├── Identity [Frame, Auto Layout, vertical] — center or fill
│   ├── WorkspaceTypeLabel [Text, Role 4]
│   ├── SubjectTitle [Text, Role 2]
│   └── SubjectSubtitle [Text, Role 5, conditional]
└── StatusArea [Frame, Auto Layout, horizontal] — right aligned
    ├── DraftIndicator [Frame, conditional]
    ├── HistoricalIndicator [Frame, conditional]
    ├── MonitoringBadge [Frame, conditional]
    └── ProcessingIndicator [Frame, conditional]
```

Figma Variants: Standard, Dashboard, Historical. Properties: `hasDraft` (boolean), `hasHistorical` (boolean), `monitoringCount` (number 0–9+), `isProcessing` (boolean).

## Engineering Notes

- The Header must render synchronously. Never lazy-load.
- Subject Title truncation: CSS `text-overflow: ellipsis` with `overflow: hidden; white-space: nowrap`. Full text in `title` attribute and ARIA label.
- Status indicators are conditionally rendered (not hidden with `display: none` when absent — they should be removed from the DOM to avoid ARIA live region noise).
- Return navigation should use the router's `<Link>` component (not `<a href>`) for SPA navigation.

## Anti-Patterns

- **Do not add action buttons to the Workspace Header.** Actions belong in the Toolbar or Footer.
- **Do not use the Header for navigation beyond the Return control.** Complex navigation belongs in the Navigation Bar.
- **Do not animate the Header on scroll.** It must remain visually stable.
- **Do not place reasoning content in the Header.** The Header is structural identity, not content.

---

# 3. Workspace Toolbar

## Purpose

The Workspace Toolbar provides contextual actions and secondary controls that apply to the entire Workspace or to the current Workspace state. It is not a navigation element. It is not a primary action area. It hosts actions that modify the Workspace view, trigger secondary operations, or provide access to controls that do not belong in the content body or Footer.

## Semantic Meaning

The Toolbar communicates: here are the operations available for this Workspace as a whole, beyond reading and primary completion.

## When Used

When a Workspace requires secondary actions or view controls that operate at the Workspace level (not the Section level). Not every Workspace requires a Toolbar. It is optional.

## When Not Used

- When all available actions fit in the Footer.
- On the Dashboard, where actions are minimal and contextual.
- When the only available action is the primary completion action (that belongs in the Footer).

## Position

The Toolbar is positioned immediately below the Workspace Header, above the body content. It is sticky on Desktop and Tablet. On Mobile, it may collapse into a bottom sheet trigger or be omitted.

## Anatomy

```
WorkspaceToolbar
├── Primary Action Group (left)
│   └── [0–3 actions, labeled or icon+label]
├── [Spacer]
└── Secondary Action Group (right)
    └── [0–3 actions, labeled or icon+label]
    └── [Overflow menu trigger, if >3 actions total]
```

## Action Priority Rules

1. Actions that change what the user is looking at (compare, view history, toggle section) are highest priority and appear directly in the Toolbar.
2. Actions that create or export content are secondary.
3. Destructive actions are never in the Toolbar. They appear contextually within Sections or require confirmation dialogs.

**Maximum visible actions:** 3 per group, 6 total. Beyond 6, overflow into a menu triggered by a "More" control.

## Overflow Behavior

When Toolbar actions exceed 6, or when the viewport width cannot accommodate all labeled actions, overflow into a dropdown menu. The overflow menu trigger is labeled "More" with a down-chevron icon. The menu contains the overflowed actions in full label form.

**Overflow threshold by breakpoint:**
- Desktop: up to 6 labeled actions before overflow.
- Tablet: up to 4 labeled actions, remaining overflow.
- Mobile: Toolbar collapses entirely; primary contextual actions surface in a bottom sheet or are promoted to Section-level controls.

## Sticky Rules

**Desktop and Tablet:** The Toolbar is sticky immediately below the Workspace Header. When content scrolls, the Toolbar remains visible. Its z-index is below the Workspace Header and above body content.

**Mobile:** The Toolbar is not sticky. It scrolls with the body, or is omitted in favor of Section-level actions.

## Disabled Behavior

Actions that are unavailable in the current Workspace state are rendered in the `disabled` interaction token state. They remain visible and in-position (they do not disappear). They are not removed from the DOM.

Disabled actions are accessible: they carry `aria-disabled="true"` (not the HTML `disabled` attribute, which removes them from tab order). A tooltip or visually-hidden text explains why the action is unavailable.

## Keyboard Interaction

- The Toolbar is a single tab stop. Within the Toolbar, arrow keys navigate between actions.
- Home/End keys navigate to the first/last action.
- Enter or Space activates the focused action.
- Escape moves focus to the body (first interactive element).

## States

**Default** — Actions rendered based on current Workspace state.
**Scrolled** — Sticky toolbar is visually separated from the content below by a subtle shadow or border (not present when at the top).
**Historical-mode** — Actions that modify content are disabled. View-only actions remain active.

## Responsive Behavior

**Desktop:** Full labeled actions. Sticky. Overflow at >6 actions.
**Tablet:** May use icon-only actions for secondary group. Sticky. Overflow at >4 actions.
**Mobile:** Toolbar collapses. Essential actions are promoted to Section-level or the Footer. A "More" control may surface the full action list in a bottom sheet.

## Accessibility

- Implemented as `<nav aria-label="Workspace actions">` or `<div role="toolbar" aria-label="Workspace actions">`.
- Individual actions: `<button>` or `<a>` as appropriate.
- Disabled actions: `aria-disabled="true"`, `tabindex="0"` (keyboard reachable), tooltip explaining why.
- Overflow menu: `aria-haspopup="menu"` on trigger, `role="menu"` on menu, `role="menuitem"` on items.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Toolbar background | `surface.toolbar` |
| Toolbar border-bottom | `color.border.standard` |
| Action text color | `color.text.tertiary` (Inline Action, per `UX-012B` §15 — visible on interaction, does not compete with primary content) |
| Action hover background | `opacity.interaction.hover` |
| Disabled action text | `color.text.tertiary` at `opacity.disabled` — the same Inline Action color, dimmed; not a separate disabled-text color token |
| Overflow shadow (scrolled) | `elevation.toolbar.shadow` |
| Toolbar z-index | `elevation.toolbar.zIndex` |

## Anti-Patterns

- **Do not place the primary completion action in the Toolbar.** That belongs in the Footer.
- **Do not use the Toolbar as a secondary navigation bar.** Navigation belongs in the Navigation Bar.
- **Do not hide disabled actions.** They communicate available functionality in the current context.
- **Do not add decorative icons to Toolbar labels without semantic purpose.** Icons add scanning value only when they are meaningful and consistent.

---

# 4. Workspace Footer

## Purpose

The Workspace Footer anchors the primary completion action and provides persistent status communication at the bottom of the Workspace. It communicates: this is how you move forward, and this is the current state of your progress.

## Semantic Meaning

The Footer represents the threshold between reasoning and action. Its visual position — at the bottom of the Workspace, always visible — communicates that completion is available when the user is ready, without demanding it.

## When Used

In every Workspace where a primary action or completion state is relevant. Present in Decision Workspace (Record Decision), Investment Workspace (Save, Open Decision), Portfolio Workspace (Open Decision). Not present on the Dashboard.

## When Not Used

On the Dashboard. On Historical Record overlays (those have their own action model).

## Anatomy

```
WorkspaceFooter
├── Left: Status / Metadata
│   ├── [Conditional] Progress Indicator
│   ├── [Conditional] Completion Gate Status
│   └── [Conditional] Last-saved timestamp
└── Right: Actions
    ├── [Conditional] Secondary Action
    └── Primary Action (always present)
```

## Variants

**Standard** — Status left, actions right. Used in Decision Workspace and Investment Workspace.

**Completion-ready** — Primary Action is the Completion Action. Gate status shows requirements met. Visual treatment of the Primary Action is the most prominent in the system.

**Completion-blocked** — Primary Action is present but in a soft-disabled state (visually present, not fully activated). Gate status communicates what is missing.

**Post-completion** — After a Decision is Recorded. Primary Action is replaced with a "View Historical Record" or "Return to Dashboard" action. Status area shows "Decision recorded on [date]".

## Completion

When the Workspace Footer hosts the Completion Action:
- The Primary Action label reflects the specific completion act: "Record Decision", not a generic label.
- The completion gate check (verifying required fields are complete) occurs on activation, before the 400ms completion pause.
- If requirements are unmet: the Completion Action does not proceed; the Footer status area displays what is required (e.g., "Decision statement required").
- If requirements are met: the 400ms pause begins, then the Workspace converts to the post-completion state.

## Navigation (in Footer context)

Footer navigation links (e.g., "View Portfolio Context", "Open Comparison") are secondary to the primary action. They appear to the left or below the primary action. They are styled as Secondary Actions.

## Status Area

**Progress Indicator:** When a Workspace has a defined completion sequence (e.g., filling the six Final Decision Card fields), a progress indicator shows how many required areas are complete. Displayed as a text label ("3 of 6 fields complete") rather than a visual gauge.

**Completion Gate Status:** When the Completion Action is blocked, a text explanation appears in the status area ("Decision statement required to record").

**Last-saved timestamp:** Small, Role 5 typography. "Saved [time]" or "Draft — not yet saved". Always present when the Workspace contains user-authored content.

## Spacing

- Footer height: determined by content, minimum 56px, typical 64px.
- Internal horizontal padding: matches Workspace Frame side padding.
- Vertical padding: `space.footer.vertical`.
- Between status and actions: space distributed to push actions to the right.

## Responsive Behavior

**Desktop and Tablet:** Full anatomy. Status left, actions right.

**Mobile:** Actions are full-width, stacked vertically if both Primary and Secondary are present. Status text appears above the actions. Safe area bottom padding applied.

## Visibility Rules

The Footer is sticky and always visible when present. It does not hide or collapse. If content scrolls behind it, the Footer casts a subtle top shadow to communicate the overlap (using `elevation.footer.shadow` token).

## Accessibility

- Implemented as `<footer>` element (ARIA `contentinfo` landmark).
- Primary Action: `<button>` with explicit label. Never a generic label.
- Completion-blocked state: `aria-disabled="true"` on the Primary Action with an `aria-describedby` pointing to the gate status message.
- Status text: `aria-live="polite"` region. Announces changes to gate status and save confirmation.
- On mobile: actions are minimum 44×44px touch targets.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Footer background | `surface.footer` |
| Footer border-top | `color.border.standard` |
| Footer top shadow (scrolled) | `elevation.footer.shadow` |
| Status text color | `color.text.tertiary` |
| Primary Action background | No dedicated background token — `UX-012B` §15's own Primary Action definition states "defined surface or clear outline at primary text color. Not a filled bright button." The Primary Action renders on the Footer's own existing neutral surface (`surface.footer`, above), distinguished by `color.text.primary` and an outline treatment, not by a separate background color |
| Primary Action text | `color.text.primary` (Primary Action, per `UX-012B` §15) |
| Secondary Action text | `color.text.secondary` (Secondary Action, per `UX-012B` §15 — footer-level, alongside the Primary Action; distinct from Inline/Section Action placement elsewhere in this document) |
| Completion-blocked Action background | `opacity.disabled` applied to the Primary Action's own base treatment, above — not a separate disabled-background token; behavior is `aria-disabled="true"`, never native `disabled`, per `ADR-002` C-06, already correctly stated in this component's own Accessibility section |
| Progress text color | `color.text.secondary` |

## Composition Rules

- **Contains:** Status area (optional), Secondary Action (optional), Primary Action (required when Footer is present).
- **Is contained by:** Workspace Frame.
- **Does not contain:** Section content, reasoning components, navigation elements.

## Anti-Patterns

- **Do not use the Footer as a navigation bar.** Navigation belongs in the Navigation Bar or Workspace Header.
- **Do not place destructive actions in the Footer.** Destructive actions require contextual placement and explicit confirmation.
- **Do not hide the Footer when completion is blocked.** The Footer should always be visible, communicating the current state.
- **Do not place more than two actions in the Footer.** Additional actions belong in the Toolbar.

---

# 5. Navigation Bar

## Purpose

The Navigation Bar provides the structural navigation context within and between Workspaces. It communicates where the user is, where they came from, and offers explicit controls for Workspace transitions.

## Semantic Meaning

The Navigation Bar makes continuous reasoning visible. Moving between Workspaces is part of the reasoning process. The Navigation Bar communicates that progression rather than treating it as incidental.

## When Used

When a Workspace exists within a navigation hierarchy deeper than Dashboard → one Workspace. Used to show the path from Dashboard through related Workspaces when the user has navigated through multiple contexts.

## When Not Used

When the user is at the Dashboard (top of the hierarchy). When the Workspace is accessed via a direct deep-link (Navigation Bar shows Dashboard as the only ancestor).

## Anatomy

```
NavigationBar
├── Breadcrumb (path from Dashboard to current Workspace)
└── [Conditional] Related Workspace Links
    └── [0–2 sibling or related Workspace links]
```

## Current Location

The current Workspace is always the rightmost (final) element in the Breadcrumb. It is not a link — it communicates "you are here."

## History and Back Behavior

The Navigation Bar does not replicate browser back/forward. It shows the contextual Atlas navigation path (Dashboard → Investment Workspace → Decision Workspace), not the browser history. Browser back/forward is supported separately.

On clicking a Breadcrumb ancestor: navigates to that Workspace, restoring the context state (scroll, draft, expansion) from when the user last left it.

## Workspace Transitions

Navigation within the Navigation Bar uses the Navigate motion token. The body content transitions; the Header and Navigation Bar remain in place.

## Deep Links

When the user arrives via a deep link with no navigation history, the Navigation Bar shows "Dashboard" as the sole ancestor. No fabricated intermediate steps.

## States

**Default** — Breadcrumb with 1–4 levels.
**Collapsed** — On tablet or mobile, the Breadcrumb collapses per the Breadcrumb component specification.
**Deep-link entry** — Only "Dashboard" is shown as the ancestor.

## Responsive Behavior

**Desktop:** Full breadcrumb visible. Related Workspace links visible.
**Tablet:** Breadcrumb collapses beyond 3 levels. Related Workspace links may collapse to icon-only.
**Mobile:** Navigation Bar may be suppressed entirely; Return Navigation in the Workspace Header provides the primary back control.

## Accessibility

- `<nav aria-label="Workspace navigation">` wrapping element.
- Breadcrumb implemented as `<ol>` with `aria-current="page"` on the final item.
- Related Workspace links: `<a>` elements with descriptive labels.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Navigation Bar background | `surface.navigation` |
| Navigation Bar border-bottom | `color.border.standard` |
| Breadcrumb ancestor color | `color.text.tertiary` (shares `type.role5`/`type.breadcrumb` typography with Supporting Metadata, already mapped to `color.text.tertiary` throughout this corpus) |
| Breadcrumb separator color | `color.text.tertiary` |
| Current location color | `color.text.secondary` |

---

# 6. Breadcrumb

## Purpose

The Breadcrumb communicates the user's position within the Atlas Workspace hierarchy. It provides direct navigation to any ancestor Workspace.

## Semantic Meaning

The Breadcrumb answers "where did I come from?" It is not decorative. It is not branding. It is a live map of the user's navigation path that doubles as a navigation tool.

## When Used

Within the Navigation Bar, when the user has navigated more than one level from the Dashboard.

## When Not Used

On the Dashboard itself. When the user is exactly one level from the Dashboard and the Workspace Header Return Navigation is sufficient.

## Anatomy

```
Breadcrumb
├── Ancestor 1 (link) → Separator
├── Ancestor 2 (link) → Separator
├── [Collapsed ancestors, if >3 levels] → Separator
└── Current (not a link, aria-current="page")
```

## Hierarchy

Breadcrumb levels follow the Atlas reasoning flow:
1. Dashboard (always the root)
2. Investment Workspace (if visited)
3. Portfolio Workspace (if visited)
4. Decision Workspace (current)

The Breadcrumb is not constructed from the browser history — it reflects the Atlas contextual navigation path.

## Collapsing Rules

**Maximum visible ancestors (Desktop):** 3 before collapsing.
**Collapsed representation:** An ellipsis (`…`) replaces the middle ancestors. Clicking the ellipsis expands to show all ancestors.

## Overflow

If the total Breadcrumb width exceeds its container, ancestors truncate with ellipsis from left to right. The current location (rightmost) is never truncated.

## Interaction

- Ancestor links: navigate to the corresponding Workspace on click, restoring that Workspace's preserved state.
- Current location: not interactive (not a link, no hover state).
- Collapsed ellipsis: expands inline to show hidden ancestors on click.
- Separator: not interactive.

## Keyboard

- Tab: reaches each ancestor link and the ellipsis trigger.
- Enter/Space: activates the link or expands the ellipsis.
- The current location is not in the tab order (it is not a link).

## Touch

- Minimum touch target per ancestor: 44×44px (padding extends the tap area beyond the visible text).
- Collapsed ellipsis: minimum 44×44px touch target.

## Responsive Behavior

**Desktop:** Up to 3 visible ancestors + current. Collapses beyond 3.
**Tablet:** Up to 2 visible ancestors + current. Collapses beyond 2.
**Mobile:** Navigation Bar may be suppressed. If shown, maximum 1 visible ancestor + current.

## Accessibility

- `<nav aria-label="Breadcrumb">` wrapper.
- `<ol>` list with `<li>` items.
- `<a>` for each ancestor link.
- Current location: `<li>` with `aria-current="page"`, no link element.
- Separator: implemented with CSS `::before` or an aria-hidden decorative element. Not in ARIA content.
- Collapsed ellipsis: `<button aria-label="Show navigation path">`.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Ancestor text color | `color.text.tertiary` |
| Ancestor hover state | `opacity.interaction.hover` applied atop the ancestor text color, above — not a separate hover color token |
| Separator color | `color.text.tertiary` |
| Current location color | `color.text.secondary` |
| Collapsed ellipsis color | `color.text.tertiary` (Inline Action, per `UX-012B` §15) |
| Font | `type.breadcrumb` (Role 5) |

## Examples

**3-level path (Desktop, fully visible):**
Dashboard → Investment Workspace: Acme Corp → Decision Workspace

**5-level path (Desktop, collapsed):**
Dashboard → … → Decision Workspace

**Deep-link entry:**
Dashboard → Decision Workspace

## Anti-Patterns

- **Do not make the current location a link.** The user is already there.
- **Do not use the Breadcrumb for filtering or state selection.** It navigates, it does not filter.
- **Do not invent breadcrumb hierarchy.** Only reflect actual Atlas navigation paths.
- **Do not use the Breadcrumb as the only navigation affordance on mobile.** The Header Return control is the primary mobile back control.

---

# 7. Section Container

## Purpose

The Section Container is the structural wrapper for each discrete content section within a Workspace body. It establishes the visual boundary, internal spacing, and expansion behavior for a single Section of reasoning content.

## Semantic Meaning

A Section Container communicates: this is a bounded, discrete piece of reasoning with its own identity and state. The container is not decorative — it defines where one reasoning topic ends and another begins.

## When Used

For every named Section within a Workspace body. Every Section has exactly one Section Container.

## When Not Used

For inline content within a Section (that uses Layout Containers). For the Workspace-level structure (that uses the Workspace Frame). For dialogs and overlays.

## Anatomy

```
SectionContainer
├── SectionHeader (always present)
│   ├── Title
│   ├── [Conditional] Status indicator
│   ├── [Conditional] Summary (visible when collapsed)
│   └── [Conditional] Expansion control
└── SectionBody (conditionally visible based on expansion state)
    └── [Content components]
```

## Visual Hierarchy

Section Containers establish visual separation through spacing, not through heavy borders or backgrounds. The internal surface is a slight variation from the Workspace background — enough to define the Section as a contained unit without visually enclosing it like a card.

The container's visual role: separate sections with space, not with walls.

## Spacing

**Between Section Containers:** `space.level4` (Section-level spacing). This is the primary structural separator between reasoning topics.

**Internal top padding:** `space.section.top` (distance from Section Container top to the Section Header).

**Internal bottom padding:** `space.section.bottom` (distance from last content element to Section Container bottom).

**Internal horizontal padding:** None at the Section Container level. Internal horizontal padding is governed by the Layout Container within the Section Body.

## Variants

**Standard** — The default. Expansion control present. Summary visible when collapsed. Used for: Supporting Factors, Challenges, Assumptions, Portfolio Consequences, Opportunity Cost, Implementation, Review Conditions.

**Fixed** — Cannot be collapsed. No expansion control. Full content always visible. Used for: Primary Conclusion, Proposed Decision area, Final Decision Card.

**Read-Only** — Content is visible but no editing controls appear. Used for: Atlas-generated sections, monitoring summaries.

**Historical** — All content is in the Historical state (reduced opacity, locked, timestamped). No editing controls. Used for any Section displaying historical content.

**Empty** — Section has no content yet. Section Body shows the appropriate Empty State component.

## States

| State | Description |
|-------|-------------|
| Expanded (default) | Full Section Body is visible |
| Collapsed | Section Body is hidden; Summary visible in header |
| Loading | Section Body shows skeleton (Loading token animation) |
| Updated | Recent content change; subtle Update token on the Section Header area; settles after a moment |
| Draft | Section has unsaved user content; Draft status visible in Section Header |
| Historical | Entire Section in historical presentation |
| Empty | No content; Empty State shown in Section Body |
| Error | Data unavailable; Error Empty State shown |

## Interaction

**Expansion/Collapse:**
- The entire Section Header row is the tap/click target for expansion and collapse.
- Not just the expansion control icon — the entire header row.
- Expansion uses the Expand motion token. Collapse uses the Collapse motion token.
- State persists within the session.
- Screen reader: `aria-expanded` on the header element.

**Auto-expansion triggers (four):**
1. Section contains newly added content (expands to show it).
2. Atlas Warning of Material or Blocking severity targets this Section (expands to surface the warning).
3. User was editing this Section before navigating away (expands on return).
4. A Contradiction involves reasoning within this Section (expands to surface it).

## Accessibility

- Section Container: `<section>` element with `aria-labelledby` pointing to the Section Header's title element.
- When collapsible: `<button aria-expanded="true|false">` as the header row activation target.
- Section Body: `id` referenced by `aria-controls` on the header button.
- Section Body: `hidden` attribute (or `display: none`) when collapsed (not just visually hidden).
- Screen reader announces expansion state changes automatically via `aria-expanded`.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Container background | `surface.primary` |
| Container border | `color.border.standard` |
| Container border-radius | `radius.section` |
| Internal top padding | `space.section.top` |
| Internal bottom padding | `space.section.bottom` |
| Between-section spacing | `space.level4` |
| Updated indicator color | None — neutral default text, no color distinction (per Status Badge Token Architecture Correction, §13, above) |
| Draft indicator color | None — neutral default text, no color distinction (per Status Badge Token Architecture Correction, §13, above) |

## Composition Rules

- **Contains:** Section Header (required), Section Body (conditionally visible), Layout Containers, content components.
- **Is contained by:** Workspace Frame body region.
- **Does not contain:** Other Section Containers at the same level. Sections do not nest within one another.
- **May reference:** Related Sections through Relationship Metadata components.

## Engineering Notes

- Use `<section>` with `aria-labelledby` for each Section Container.
- The Section Header click handler must be on the full-width header row, not just the expansion icon.
- Section Body visibility: use `hidden` attribute for collapsed state (accessible hiding). CSS transitions for smooth height animation.
- For height animation, use the Expand/Collapse motion tokens. Avoid animating `height` from 0 to `auto` with CSS alone — use JS-measured heights or the Web Animations API.

## Anti-Patterns

- **Do not use Section Containers for inline grouping within a Section.** That is the role of Layout Containers.
- **Do not make the border or background visually heavy.** The Section Container defines boundaries through spacing, not visual enclosure.
- **Do not collapse the Section Header to just the expansion icon.** The entire row is the tap target.
- **Do not nest Section Containers.** Sections are flat within the Workspace body.

---

# 8. Section Header

## Purpose

The Section Header identifies a Section, communicates its current state, and provides the expansion control. It is the first element a user sees when scanning the Workspace body. Every Section has exactly one Section Header.

## Semantic Meaning

The Section Header answers: what is this section, and what is its current state? When collapsed, the Section Header is all the user sees of that section. It must communicate enough for the user to decide whether to expand.

## When Used

As the first child of every Section Container. Always present, whether the Section is expanded or collapsed.

## When Not Used

Outside of a Section Container. For Workspace-level identity (that is the Workspace Header's role).

## Anatomy

```
SectionHeader
├── Expansion Control (if Section is collapsible)
├── Title [Role 2 typography]
├── [Conditional] Status Indicator
├── [Conditional] Summary [Role 5 typography, visible when collapsed]
└── [Conditional] Section Action
```

## Title

Role 2 typography (Section Heading weight). The name of the reasoning Section. Examples: "Supporting Factors", "Challenges", "Assumptions", "Opportunity Cost", "Final Decision Card".

Title Case. Never truncated (if the title wraps, it wraps). Maximum recommended title length: 4 words.

The title is the `<h2>` (or appropriate heading level based on document hierarchy) referenced by the Section Container's `aria-labelledby`.

## Subtitle

Optional. Role 5 typography. One line. Provides contextual clarification of the Section's current focus. Example: below "Assumptions", a subtitle might read "4 holding, 1 under review".

## Description

Optional, rare. Role 5 typography. A brief clarification of what the Section is for — used only when the Section title alone may be ambiguous to a first-time user. Maximum one line.

## Actions

Section-level actions appear in the Section Header, right-aligned. Maximum 2. Examples: "Add assumption", "Compare", "View history".

Section actions are smaller than Toolbar actions. Icon-only on mobile, icon+label on desktop. Minimum touch target: 44×44px.

## Metadata

Timestamps, counts, or status values may appear in the Section Header as secondary information. Role 5 typography. Always subordinate to the Title.

## Expansion

**Collapsible Sections:** The expansion control is a chevron icon (rotates from right-facing when collapsed to down-facing when expanded). The entire Section Header row is the tap target — not just the chevron.

**Fixed Sections:** No expansion control. The Section is always fully open.

**Expansion control visual:** `icon.chevron` at the appropriate icon size. Color: `color.text.tertiary`. Rotates 90° on expansion (Expand token animation).

## Collapse

When collapsed, the Section Header shows the Summary text below or adjacent to the Title. The Summary communicates the Section's current state in one line (e.g., "3 factors identified" or "1 challenge flagged as material").

The Summary is not shown when the Section is expanded.

## Alignment

Title and expansion control: left-aligned. Section actions: right-aligned.

## Spacing

- Section Header height: minimum 44px (for tap target compliance). Typical 48–56px.
- Horizontal padding: inherited from Section Container's internal padding.
- Vertical padding: `space.section.header.vertical` above and below.
- Between Title and Summary: `space.level1`.

## Variants

**Standard** — Title, expansion control, conditional summary and status.
**Fixed** — Title only (no expansion control, no summary). Used in Sections that are always open.
**With Actions** — Standard with section-level actions right-aligned.
**Compact** — Reduced vertical padding for dense Workspaces (Dashboard-level density).

## Responsive Behavior

**Desktop:** Full anatomy. Labels on section actions.
**Tablet:** Section actions may become icon-only.
**Mobile:** Section actions become icon-only or move to a tap-to-reveal overflow. Summary truncates to one line if necessary.

## Accessibility

- Title: appropriate heading level (`<h2>` in standard Workspace body context).
- When collapsible: `<button>` wrapping the entire header row (or the header row as a button with `role="button"`). `aria-expanded="true|false"`. `aria-controls="[section-body-id]"`.
- Summary: `aria-hidden="true"` when Section is expanded (the Summary is not needed when the content is visible). Visible when collapsed.
- Status Indicator: `aria-label` communicating the meaning.
- Section actions: labeled buttons or links with descriptive `aria-label`.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Title color | `color.text.primary` |
| Subtitle color | `color.text.secondary` |
| Summary color | `color.text.tertiary` |
| Expansion chevron color | `color.text.tertiary` |
| Section action color | `color.text.tertiary` (Section Action, per `UX-012B` §15 — explicitly Tertiary emphasis) |
| Section Header background (hover) | `opacity.interaction.hover` |
| Status indicator (draft) | None — neutral default text, no color distinction (per Status Badge Token Architecture Correction, §13, above) |
| Status indicator (updated) | None — neutral default text, no color distinction (per Status Badge Token Architecture Correction, §13, above) |

## Anti-Patterns

- **Do not use the Section Header as a navigation element.** It expands and collapses the Section it belongs to.
- **Do not put reasoning content in the Section Header.** Content belongs in the Section Body.
- **Do not make the expansion icon the only tap target.** The entire header row must be tappable.
- **Do not truncate the Section title.** Titles are short by design and should never need truncation.

---

# 9. Divider

## Purpose

The Divider creates a visual boundary between content areas that share a surface but represent different logical groupings. It is a spatial separator, not a structural container.

## Semantic Meaning

A Divider communicates: what is above and what is below are related but distinct. It is the lightest possible boundary signal. It does not communicate hierarchy, importance, or interactivity.

## When Used

- Between subsections within a Section Body (less significant than a Section-to-Section boundary).
- Between a primary content area and a metadata area within the same Section.
- Between the Section Body and the Section-level action area.

## When Not Used

- Between Section Containers. Section-to-Section separation is achieved with spacing (`space.level4`), not Dividers.
- As decoration.
- To create visual interest in an otherwise empty area.
- Between every element — Dividers used too frequently lose meaning.

## Semantic Purpose

Before adding a Divider, ask: would spacing alone communicate this boundary? If yes, use spacing. A Divider is warranted only when two content areas share the same surface and the proximity would cause ambiguity without a visual separator.

## Anatomy

```
Divider
└── [A horizontal or vertical rule]
```

No text, no icons, no interactive elements.

## Spacing

A Divider is accompanied by equal spacing on both sides. The spacing on each side is at minimum `space.level2` (Tight). The Divider itself has no margin of its own — the surrounding components provide spacing.

## Thickness

1px. No thicker Dividers in Atlas. Thickness does not communicate hierarchy.

## Variants

**Horizontal** — A full-width horizontal rule. The standard Divider.
**Vertical** — Used within horizontal layouts to separate parallel columns. Used within Comparison layouts.
**Inset** — A horizontal Divider that does not extend to the full width of its container. Used within list items to separate adjacent list entries without creating heavy visual weight.

## Visibility

The Divider is visible but subtle. Its color is `color.border.hairline` — a step above the surface color, a step below text colors.

Dividers may be omitted (visibility: hidden; preserved in layout to maintain spacing) in historical Sections where visual density is already reduced.

## Responsive Rules

**Desktop and Tablet:** Dividers appear as specified.
**Mobile:** Vertical Dividers within Comparison layouts become horizontal Dividers (when columns stack). The Divider reorients to match the layout.

## Accessibility

- `<hr>` element for horizontal Dividers. `role="separator"` for vertical Dividers implemented with `<div>`.
- `aria-hidden="true"` when the Divider is purely decorative and the boundary is communicated through content structure.
- `aria-hidden="false"` when the Divider communicates a meaningful boundary that screen readers should be aware of (rare).

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Divider color | `color.border.hairline` |
| Divider thickness | 1px, stated directly — no dedicated width token exists for this value; `width.focus.ring` is the only literalized `width.*` token in `UX-012D` §3 *(missing foundation, see §18 traceability)* |

## Misuse

The most common Divider misuse is overuse — using Dividers as a default separator between all content, regardless of whether the spacing alone would communicate the boundary. The result is a visually heavy, grid-like interface that contradicts Atlas's restrained, editorial aesthetic.

Rule: if spacing provides the separation, remove the Divider.

---

# 10. Surface

## Purpose

Surface components define the background layer of each distinct area in the Atlas interface. Surfaces create visual hierarchy through subtle tonal variation — lighter or darker than the surrounding surface — without using borders or shadows as primary differentiators.

## Semantic Meaning

A Surface communicates: this area belongs to a specific layer of the interface hierarchy. Surfaces do not communicate information content — they organize space by role.

## Surface Tier Model

Atlas uses five surface tiers. Each tier is a distinct tonal step within the warm dark palette. Adjacent tiers must have sufficient contrast for the boundary to be perceptible.

**Tier 0 — Workspace Background**
The base of the Workspace body. Everything else sits on top of this.
Token: `surface.background`
Use: Workspace Frame body region.

**Tier 1 — Primary Surface**
The standard surface for Section Containers and primary content areas.
Token: `surface.primary`
Use: Standard, Reasoning, Editable, and Comparison Sections.

**Tier 2 — Elevated Surface**
A slightly lighter surface for components that appear above Tier 1. Used to create depth within a Section without a card-like enclosure.
Token: `surface.elevated`
Use: Atlas Suggestion components, inline metadata areas, compact information panels.

**Tier 3 — Panel Surface**
Used for persistent side panels, overlays, or secondary information panels. Higher tonal contrast against the Workspace background.
Token: `surface.panel`
Use: Historical Record overlays, Dialog containers, comparison side panels.

**Historical Surface**
A surface specifically for Historical content. Distinguishable from Tier 1 by a slight desaturation or opacity adjustment, reinforcing the "past" quality of historical content.
Token: `surface.historical`
Use: Historical Sections, Historical Records.

**Monitoring Surface**
A surface for Monitoring condition components when they are in an Approaching or Triggered state. A subtle warm variation that communicates attention without urgency.
Token: `surface.monitoring`
Use: Monitoring Condition components in Approaching or Triggered state.

## Properties

| Property | Type | Notes |
|----------|------|-------|
| `tier` | `'workspace' \| 'primary' \| 'elevated' \| 'panel' \| 'historical' \| 'monitoring'` | Required |
| `hasBorder` | boolean | Adds `color.border.standard` on all sides |
| `borderRadius` | `'none' \| 'default' \| 'large'` | Default for standard; large for Dialog; none for full-bleed |

## Elevation

Atlas surfaces do not use drop shadows as their primary differentiation mechanism. Elevation is communicated through tonal variation. Shadows are reserved for overlays (Dialog, Historical Record) where the floating nature of the container must be communicated.

**Shadow tokens:**
- `elevation.none` — no shadow (Section Containers, inline components)
- `elevation.overlay` — subtle shadow for Dialog and Historical Record overlays
- `elevation.sticky` — subtle bottom shadow for sticky Headers and Toolbars when content scrolls beneath them

## Contrast

Adjacent surfaces must provide sufficient visual differentiation. Minimum perceptible contrast between adjacent surface tiers: sufficient for a user to identify the boundary without a border (approximately 3:1 luminance contrast between adjacent surfaces).

Borders (`color.border.standard`) supplement tonal contrast when two surfaces of close tonal value are adjacent.

## Composition

Surfaces are not standalone components — they are applied as background and border properties to structural container components. A Section Container uses `surface.primary`. An Atlas Suggestion component uses `surface.elevated`. A Dialog uses `surface.panel`.

The Surface component in engineering is typically implemented as a design token mapping, not a separate React component — applied through CSS custom properties on the relevant structural component.

## Token Mapping

| Surface | Token |
|---------|-------|
| Workspace background | `surface.background` |
| Primary surface | `surface.primary` |
| Elevated surface | `surface.elevated` |
| Panel surface | `surface.panel` |
| Historical surface | `surface.historical` |
| Monitoring surface | `surface.monitoring` |
| Surface border | `color.border.standard` |
| Overlay shadow | `elevation.overlay` |

---

# 11. Layout Container

## Purpose

Layout Containers organize content within Section Bodies and other content areas. They govern how child components are arranged spatially: as a column, row, stack, split, grid, or adaptive arrangement.

## Semantic Meaning

A Layout Container has no semantic meaning of its own. It is purely structural. It arranges its children according to a specified layout model.

## When Used

Wherever content within a Section Body, Dialog, or overlay needs to be arranged. Layout Containers are the internal organization layer. They are not the Section-level structural layer (that is the Section Container).

## Column

A single vertical column. Children stack vertically. Width is governed by its container.

**Editorial Column:** `max-width: 680px` (approximately 65–70 characters of body text). Content within the Editorial Column is centered within the Section Body. Used for all long-form narrative reading and writing.

**Analytical Column:** Full width of the Section Body. Used for structured data, tables, and analysis grids.

## Row

Children are arranged horizontally. Wraps to the next line at the breakpoint specified. Default: wraps at tablet breakpoint.

## Stack

Children are stacked vertically with consistent spacing between them. The Stack is the most commonly used Layout Container within Section Bodies.

**Properties:**
- `spacing`: `space.level1` through `space.level6` (between children)
- `align`: `'start' | 'center' | 'end' | 'stretch'`

## Split Layout

Two columns of specified relative widths. Used for Comparison content.

**Properties:**
- `split`: `'50/50' | '60/40' | '40/60'`
- `gap`: spacing between columns
- `stacks-at`: breakpoint at which columns stack vertically

**At the stacking breakpoint:** columns become a Stack. The left column appears first; the right column appears below.

## Adaptive Layout

A Layout Container that responds to its available width rather than the viewport breakpoints. Switches between a defined multi-column layout and a single-column stack based on measured container width (CSS container queries).

## Responsive Grid

A multi-column grid for dashboard-style content (Dashboard Section bodies only). Columns collapse progressively: 4-column on desktop, 2-column on tablet, 1-column on mobile.

**Properties:**
- `columns`: `2 | 3 | 4`
- `gap`: spacing between cells

## Maximum Widths

| Layout Type | Max Width | Context |
|------------|-----------|---------|
| Editorial Column | 680px | Narrative reading/writing |
| Analytical Column | 100% of Section Body | Data analysis |
| Split Layout (each column) | `(Section Body width - gap) / 2` | Comparison |
| Responsive Grid | 100% of Section Body | Dashboard |

## Spacing

Layout Container spacing is governed by the spacing tier appropriate to the context:
- Within a reasoning Section: `space.level3` between components.
- Within a dense Section (Dashboard): `space.level2` between components.
- Within a comparison layout: `space.level3` between columns.

## Alignment

**Horizontal:** Center by default for Editorial Column; left-align for Analytical Column and Stack.
**Vertical:** Stretch by default for Row and Split; top-align for Column and Stack.

## Engineering Implementation

Layout Containers map to CSS layout primitives:
- **Column/Stack:** `display: flex; flex-direction: column; gap: [spacing-token]`.
- **Row:** `display: flex; flex-direction: row; flex-wrap: wrap; gap: [spacing-token]`.
- **Split Layout:** `display: grid; grid-template-columns: [split] [split]; gap: [spacing-token]`.
- **Adaptive Layout:** `display: grid; grid-template-columns: repeat(auto-fill, minmax([min-width], 1fr))` or CSS container queries.
- **Responsive Grid:** `display: grid; grid-template-columns: repeat([columns], 1fr); gap: [spacing-token]`.

Engineering should implement Layout Containers as composable primitive components: `<Column>`, `<Row>`, `<Stack>`, `<Split>`, `<Grid>`. They accept children, spacing, alignment, and breakpoint props.

---

# 12. Empty State

## Purpose

The Empty State communicates the condition of a Section or area that has no content yet — and explains why, and what it means. Empty States are informative, not decorative.

## Semantic Meaning

An Empty State communicates: this area has no content right now. The reason matters and is always provided. The implication (positive, neutral, or action-required) is communicated in the tone and content.

## When Used

When a Section has no content to display. When a list has no items. When a data source returns no results. When the user has not yet authored content in a required area.

## When Not Used

When content is loading (use Progress Indicator / Loading state, not Empty State). When content exists but is filtered to zero results (show the filter state, not an Empty State).

## Illustration Policy

No illustrations in Atlas Empty States. No characters, no icons beyond a single functional status icon, no decorative graphics. The emptiness is communicated through text alone, with appropriate tonal variation.

The exception: a single, simple, semantically relevant icon (e.g., a clock icon for "No monitoring conditions established yet") may appear above the headline. Icon size: `icon.large`. Color: `color.text.tertiary`.

## Anatomy

```
EmptyState
├── [Conditional] Icon (single, semantic, muted)
├── Headline [Role 3 typography, medium weight]
├── Supporting Text [Role 5 typography]
└── [Conditional] Action [Secondary Action component]
```

## Headline

Communicates what is absent and why it matters. Not the generic "Nothing here yet." Four subtypes have distinct headline approaches:

**Expected Empty** — What is absent, stated neutrally. Example: "No contradictions identified."
**Informational Empty** — What has not been set up yet, stated informatively. Example: "Monitoring conditions not yet established."
**Action-Required Empty** — What needs to be done, stated directly. Example: "Record your Decision to complete this Workspace."
**Error Empty** — What could not be loaded, stated clearly. Example: "Supporting factors could not be loaded."

## Supporting Text

One to two sentences. Explains the implication of the empty state. Tone is calibrated to subtype:
- Expected: reassuring ("The reasoning does not surface any conflicting information.")
- Informational: instructive ("Monitoring conditions are established after recording a Decision.")
- Action-Required: direct ("The Decision field is required to proceed.")
- Error: honest and actionable ("Check your connection and try again, or continue with available information.")

## Actions

**Expected Empty:** No action. The empty state is the message.
**Informational Empty:** No action (or a link to documentation/help if warranted).
**Action-Required Empty:** A Secondary Action pointing to the relevant area or Section.
**Error Empty:** A retry action ("Try again") as a Secondary Action.

## Tone

Atlas Empty States are calm. They do not apologize, over-explain, or use marketing language. They do not say "Looks like there's nothing here!" — they say what is absent and why.

## Variants

Four variants correspond to the four subtypes (Expected, Informational, Action-Required, Error). Each variant has the same anatomy but different default icon (if used), headline approach, and action availability.

## Sizing

Empty States fill the Section Body they inhabit. They are vertically centered within the available height. They are not full-screen elements.

## Accessibility

- Implemented as a text region; no complex ARIA required.
- Icon: `aria-hidden="true"` (decorative).
- Headline: the most prominent text; styled with Role 3 weight.
- Action: `<button>` or `<a>` with descriptive label.
- When the Empty State is dynamically inserted (e.g., after a failed load), `aria-live="polite"` on the container announces the change.

## Responsive Behavior

**Desktop and Tablet:** Centered within available space. Editorial Column width for text.
**Mobile:** Full-width text. Action is full-width button.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Icon color | `color.text.tertiary` |
| Headline color | `color.text.secondary` |
| Supporting text color | `color.text.tertiary` |
| Background | inherited from Section |

## Anti-Patterns

- **Do not use illustrations.** They add visual weight without informational value.
- **Do not use "Nothing here yet" or equivalents.** Always state what is absent and why.
- **Do not add an action to Expected Empty states.** The user does not need to do anything — the state is correct.
- **Do not apply an Empty State when content is loading.** The Loading state handles in-progress data fetches.

---

# 13. Status Badge

**Correction Notice (Atlas UX Architecture Status Badge Token Architecture Correction task — 2026-08-02):** This component's own purpose, semantic meaning, nine canonical badge types, priority ordering, sizing, placement, states, and accessibility rules are unchanged by this notice. What changed: every badge type's own color reference previously used an unsupported `status.*` token namespace that does not exist anywhere in `UX-012D-Atlas-Design-System-Governance-Tokens-Evolution.md` — confirmed by the completed Status Badge Token Family Architecture Investigation (2026-08-02). That namespace is rejected in full; no `status.*` token is used anywhere below. Historical, Warning, and Monitoring: Approaching are corrected to cite the existing `UX-012D` tokens that already governed their own meaning. Monitoring: Triggered and Completed/Recorded are corrected to cite the two small, bounded additions made to `UX-012D` §3 for this same correction (`color.semantic.red`, `type.badge.completed`) — the only new tokens introduced by this correction, and the only two Status Badge types that needed one. Draft, Saved, Monitoring: Active, and Updated are corrected to the neutral, label-only presentation `UX-012B` §13 already specifies for them — their prior `status.*` references implied a color distinction that was never source-supported. This notice preserves the fact that the prior `status.*` references existed; the corrected values replace them below, not silently.

## Purpose

The Status Badge communicates the current semantic state of a component, record, or Section in a compact, labeled form. It is a persistent status indicator, not a notification or alert.

## Semantic Meaning

A Status Badge answers: what is the current state of this thing? It is not interactive by default. It is informational. Its color and label together communicate the state.

## Status Presentation

Status Badge renders a semantic `type` value; it does not itself define what any underlying state means. Per `UX-013F`'s own established classification: *"Status Presentation is the mapping layer between domain state and StatusBadge configuration — an architecture document, not a component."* The mapping below — from an already-known domain fact (a Decision is recorded, a Monitoring Condition has crossed its threshold, content is historical) to a specific badge presentation — is that mapping, stated here for Status Badge's own nine canonical types; it is not a new Product Concept, and it does not make Status Presentation an independently stateful component of its own.

Different badge types intentionally draw on different `UX-012D` semantic token groups, because they represent genuinely different kinds of facts — workflow state (Draft, Saved), monitoring urgency (Monitoring: Active, Approaching, Triggered), content immutability (Historical), completion (Completed/Recorded), and change feedback (Updated). Neutral states (Draft, Saved, Monitoring: Active, Updated) do not receive an artificially distinct color merely for visual variety — per `UX-012B` §13's own literal description, each is communicated by its text label alone. Text and programmatic labels are always authoritative; color, where a badge type has one, is supplementary only, per this component's own Accessibility section, below, and `UX-012A` §15. No `status.*` token namespace exists anywhere in `UX-012D`, and none is used below.

## When Used

In Workspace Headers (Draft Indicator, Historical Indicator), Section Headers (Section status), Monitoring Condition components (lifecycle stage), Decision records (Recorded state).

## When Not Used

As an interactive button. As a notification count (use the Monitoring Badge in the Workspace Header instead). For states that are communicated adequately by typography or spacing alone.

## Anatomy

```
StatusBadge
├── [Conditional] Icon (12px, preceding label)
└── Label [Role 5 or Role 4 typography]
```

No colored dot alone — always include a text label. Color supplements the label; it does not replace it.

## Badge Types and Their Meanings

**Draft**
Label: "Draft"
Meaning: Unsaved user content exists.
Presentation: Neutral — no distinct semantic color, per `UX-012B` §13 ("Draft: The object or content is in active preparation and has not been recorded or submitted"; no color is specified beyond the Draft Indicator itself). Communicated by the text label alone.
Accompanies: Last-autosave timestamp.

**Saved**
Label: "Saved"
Meaning: Content was recently autosaved. Transient (appears briefly after save, then disappears).
Duration: 3 seconds, then fades out.
Presentation: Neutral — no distinct semantic color, per `UX-012B` §13 ("Saved: The draft state has been explicitly saved. Visual treatment: Draft Indicator shows last-saved timestamp"; no distinct color is specified).

**Completed / Recorded**
Label: "Recorded"
Meaning: A Decision has been formally recorded and is now a Historical Record.
Presentation: `type.badge.completed` (`UX-012D` §3, Completed semantic group). No dedicated background token — renders on the Status Badge's own neutral default surface, consistent with the Completed group's own stated principle that "the authority comes from the populated content, not a different surface treatment." Communicates recording status textually only; does not imply Decision Quality or a positive Outcome.
Persistent: never disappears once shown.

**Monitoring: Active**
Label: "Monitoring"
Meaning: Active Monitoring Conditions are established.
Presentation: Neutral — no distinct semantic color, per `UX-012B` §13 ("Monitoring: Atlas is actively observing conditions linked to this object. Visual treatment: A small 'MONITORING' label in metadata scale"; no distinct color is specified).

**Monitoring: Approaching**
Label: "Approaching"
Meaning: A Monitoring Condition threshold is near.
Presentation: `color.semantic.amber` (`UX-012D` §3, Monitoring semantic group — explicitly named for this state).

**Monitoring: Triggered**
Label: "Triggered"
Meaning: A Monitoring Condition threshold has been crossed. Requires attention.
Presentation: `color.semantic.red` (`UX-012D` §3, Monitoring semantic group, added per the Status Badge Token Architecture Correction task, 2026-08-02). Communicates only that the underlying Monitoring Condition has crossed its own threshold, per `UX-012` §26; it does not itself imply autonomous Atlas action or assert that the associated Decision is invalid — that determination remains the Investor's own, consistent with the Invalidation Trigger's own established boundary (`UX-012B` §9).

**Historical**
Label: "Historical Record"
Meaning: The content is from a Historical Record and is immutable.
Presentation: `color.text.historical` (`UX-012D` §3, Historical Content semantic group).
Always persistent. Cannot be dismissed.

**Updated**
Label: "Updated"
Meaning: Content in this Section or component has changed since the user last reviewed it.
Presentation: Neutral — no distinct semantic color, per `UX-012B` §13 ("Updated: Atlas has new analysis or the object's state has changed since the user's last visit. Visual treatment: A small 'UPDATED' label in metadata scale"; no distinct color is specified).
Transient: fades after the user interacts with the Section.

**Warning**
Label: "Warning" or the specific warning type.
Meaning: An Atlas Warning is present in this Section. Used in Section Header status area.
Presentation: `color.semantic.amber` (`UX-012D` §3 — Warning is stated to be "a synonym for Material Contradiction and above... maps to the same amber tokens" as the Contradiction semantic group).

## Priority

When multiple Status Badges compete for the same slot (e.g., a Section is both Draft and Updated):
Priority order (highest first): Warning > Triggered > Draft > Updated > Saved > Active > Historical > Completed

Only the highest-priority badge is shown in the Section Header. Full status detail is available in the Section Body.

## Sizing

Two sizes:
- **Standard:** Used in Section Headers and component-level status.
- **Compact:** Used in dense contexts (Dashboard, Monitoring lists, Breadcrumb adjacency).

## Placement

Status Badges appear in the Section Header (right of title), in the Workspace Header Status Area, or within a component as a state indicator. They never appear as free-floating elements.

## States

Status Badges themselves have no interactive states. They are informational. If a Status Badge needs to be interactive (e.g., clicking "Triggered" to navigate to the Monitoring surface), it should be implemented as a Secondary Action or link, not a Badge.

## Accessibility

- Implemented as `<span>` with `role="status"` for transient badges (Saved, Updated) — announces changes.
- Implemented as `<span>` without `role="status"` for persistent badges — static informational content.
- Color alone does not communicate status — always a text label.
- For screen readers: badge text is read as part of surrounding context.

## Token Mapping

| Badge | Background Token | Text/Icon Token | Source |
|-------|-------------------|------------------|--------|
| Draft | None — neutral default surface, no color distinction | None — text label only, no color distinction | `UX-012B` §13 |
| Saved | None — neutral default surface, no color distinction | None — text label only, no color distinction | `UX-012B` §13 |
| Completed | None — neutral default surface | `type.badge.completed` | `UX-012D` §3, Completed group (added this correction) |
| Monitoring: Active | None — neutral default surface, no color distinction | None — text label only, no color distinction | `UX-012B` §13 |
| Monitoring: Approaching | None defined in `UX-012D` | `color.semantic.amber` | `UX-012D` §3, Monitoring group |
| Monitoring: Triggered | None defined in `UX-012D` | `color.semantic.red` | `UX-012D` §3, Monitoring group (added this correction) |
| Historical | `surface.historical` | `color.text.historical` | `UX-012D` §3, Historical Content group |
| Updated | None — neutral default surface, no color distinction | None — text label only, no color distinction | `UX-012B` §13 |
| Warning | None defined in `UX-012D` | `color.semantic.amber` | `UX-012D` §3, Warning/Contradiction group |

No `status.*` token is used above. `color.semantic.red` and `type.badge.completed` are the only two tokens newly added anywhere in this correction, both to their own already-established `UX-012D` §3 semantic group (Monitoring and Completed, respectively) — no new token category or top-level namespace was introduced.

## Anti-Patterns

- **Do not use color alone to communicate status.** Always include the text label.
- **Do not make Status Badges interactive.** They are informational. Use Action components for navigation or triggers.
- **Do not stack multiple Status Badges in the same slot.** Show only the highest priority.
- **Do not use Status Badges as decorative tags.** Every badge communicates a specific semantic state.
- **Do not invent a component-specific token family for a new badge type.** Extend an existing `UX-012D` §3 semantic group, or raise a bounded token-governance request per `UX-012D` §5 — never introduce a parallel namespace like the rejected `status.*` family.

---

# 14. Progress Indicator

## Purpose

The Progress Indicator communicates whether a process is underway, how far it has progressed (when determinable), or that the system is working. It prevents uncertainty during loading, saving, processing, and completion sequences.

## Semantic Meaning

A Progress Indicator communicates: something is happening. When determinate: how much has happened. When indeterminate: that the system is active, not stalled.

## When Used

- Loading Workspace content (indeterminate)
- Autosaving (indeterminate, brief)
- Completing the Decision recording sequence (determinate: completion gate progress)
- Background processing longer than 3 seconds (indeterminate, persistent)

## When Not Used

- For processes shorter than 300ms (no visual indicator; prevents flash)
- For failed states (use Error Empty State instead)
- As decoration

## Variants

**Determinate**
A linear progress bar that fills from left to right as progress is made. Used when the total number of steps is known.
Example use: "3 of 6 Decision fields complete."
Implementation: `<progress value="3" max="6">` element.
Visual: a filled bar within a track. Fill/track color treatment has no canonical `UX-012D` foundation *(missing foundation, see §18 traceability)*.

**Indeterminate**
A looping animation that communicates ongoing work without implying a known endpoint. Used when the duration is unknown.
Animation: the Loading motion token (steady, non-theatrical).
Visual: a pulsing bar or skeleton, not a spinner. Atlas does not use circular spinners.

**Completion**
A specific Progress Indicator for the Decision recording completion gate. Displays as text rather than a visual bar: "3 of 6 fields complete" in Role 5 typography. When all 6 are complete: "Ready to record."
Placement: Workspace Footer status area.

**Saving**
A transient indicator that autosave is in progress. Appears in the Workspace Header or Section Header area. Text: "Saving…" fading to "Saved" (Status Badge). Duration: as long as the save operation takes, minimum 300ms for the "Saved" confirmation.

**Loading (Skeleton)**
Content placeholders that match the expected layout of the loading content. Used in Section Bodies during initial data load. The Loading motion token applies: a gentle shimmer animation across the skeleton shapes.

**Review Progress**
For Historical Review Workspaces: indicates progress through the review sequence. Text-based ("Step 2 of 4: Reviewing Assumptions").

## Interaction

Progress Indicators are not interactive. They communicate; they do not enable actions.

**Exception:** The Completion Progress ("3 of 6 fields complete") is paired with the Completion Action in the Footer. The Completion Action becomes active when the required count is reached.

## Accessibility

**Determinate:** `<progress value="[current]" max="[total]">`. Screen readers announce the percentage or fraction.
**Indeterminate:** `<div role="progressbar" aria-valuenow="indeterminate" aria-label="[description of what is loading]">`.
**Saving indicator:** `aria-live="polite"` region. Announces "Saving" and "Saved" to screen readers.
**Skeleton loading:** `aria-busy="true"` on the containing Section. Screen reader waits for content.
**Reduced motion:** The shimmer animation is removed. Skeleton shapes remain static.

## Animation Rules

- Shimmer animation: the Loading motion token. Duration: continuous. Reduced-motion fallback: no animation (static skeleton).
- Determinate fill: transitions from old value to new value using the Update motion token.
- Saving/Saved transition: Fade token between "Saving…" and "Saved" label.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Progress bar fill | No canonical `UX-012D` foundation exists *(missing foundation, see §18 traceability)* |
| Progress bar track | No canonical `UX-012D` foundation exists *(missing foundation, see §18 traceability)* |
| Skeleton base | No canonical `UX-012D` foundation exists — a neutral placeholder shape color, distinct from the shimmer animation below *(missing foundation, see §18 traceability)* |
| Skeleton shimmer | `opacity.loading.pulse.min` / `opacity.loading.pulse.max` — the same tokens already governing the Loading animation row, below; `loading.skeleton.shimmer` was a redundant second name for the identical effect, not a distinct token |
| Loading animation | `opacity.loading.pulse.min` / `opacity.loading.pulse.max` |

---

# 15. Scroll Container

## Purpose

The Scroll Container defines a specific scrollable region within the Atlas interface. It governs overflow behavior, scroll restoration, sticky element behavior, and nested scrolling context.

## Semantic Meaning

A Scroll Container communicates: the content within this boundary can be navigated vertically (or horizontally). The container itself is a viewport into potentially longer content.

## When Used

- The Workspace Frame body region (primary Workspace scroll context)
- Horizontal scroll within a Comparison layout on mobile (when columns cannot stack)
- Tall content within a Dialog or overlay
- Historical timeline navigation

## Vertical Scrolling

**Primary Workspace scroll:** The Workspace Frame body is the primary vertical scroll context. Scrolling is smooth, continuous, without pagination.

**Scroll behavior:** `scroll-behavior: smooth` for programmatic scroll changes (Navigate token). `scroll-behavior: auto` for user-initiated scroll (do not apply smooth scroll to user drag — only to programmatic repositioning).

**Overscroll behavior:** `overscroll-behavior: contain`. Prevents scroll chaining from the Workspace body to the viewport when the user reaches the top or bottom of the body scroll region.

## Horizontal Scrolling

Atlas avoids horizontal scroll at the page level. Within specific components (Comparison on mobile), controlled horizontal scroll is permitted.

**Horizontal scroll rules:**
- Never full-page horizontal scroll.
- Always accompanied by a visible scroll indicator (native or custom) so the user knows there is more content.
- Content within a horizontally scrolled container adapts to at least one column width at 320px.

## Nested Scrolling

Nested scroll contexts (a scrollable area within a scrollable Workspace body) require careful management.

**Rule:** Nested scroll should be avoided where possible. When necessary:
- The nested scroll container must have a defined `height` or `max-height`.
- `overscroll-behavior: contain` on the nested container.
- The nested container must be visually distinguishable from the parent scroll context (through surface differentiation or a persistent scroll indicator).

## Sticky Elements

Within the Workspace scroll context, the following elements are sticky:
- **Workspace Header:** sticky to `top: 0` of the viewport.
- **Workspace Footer:** sticky to `bottom: 0` of the viewport.
- **Workspace Toolbar:** sticky to `top: [header-height]` of the viewport.
- **Section Headers** (optional): may be sticky within the Workspace body scroll context, at `top: [header-height + toolbar-height]`. z-index below the Workspace Header.

Sticky Section Headers are used only when the Section is very long (e.g., a lengthy Final Decision Card). They are not applied by default to every Section.

## Overflow

**Text overflow:** `overflow: hidden; text-overflow: ellipsis` on single-line truncated text. Full content in tooltip or ARIA label.
**Content overflow:** Section content never clips; Section Container grows to contain its content.
**Comparison layout overflow (mobile):** horizontal scroll with scroll snap.

## Scroll Restoration

Scroll position in the Workspace Frame body is stored per `workspaceId` and restored on mount. Restoration is exact and synchronous (before first paint).

For Dialog overlays: scroll position starts at 0 on open. Not restored between open/close cycles (the user is starting a new dialog session each time).

## Performance Considerations

- Use `will-change: transform` sparingly — only for elements that will animate (sticky headers, overlays). Remove `will-change` after animation completes.
- Long Section bodies with many child components should use windowing or virtualization only when there is evidence of performance problems. Do not over-optimize prematurely.
- Scroll event listeners on the Workspace body should be passive: `{ passive: true }`.

---

# 16. Dialog Container

## Purpose

The Dialog Container provides a focused overlay context for interactions that require user attention but do not warrant navigating away from the current Workspace. It overlays the Workspace without destroying it.

## Semantic Meaning

A Dialog communicates: an action or confirmation is required before you can continue. The current Workspace context is preserved beneath the Dialog.

## When Used

- Confirmation of destructive actions ("Delete this draft?")
- Disambiguation of ambiguous choices
- Brief supplementary information that does not fit in the Workspace body
- Confirmation before the completion action in exceptional cases (not standard — the Footer completion gate handles most completion scenarios)

## When Not Used

- For Historical Record viewing (those use a full-width overlay, not a Dialog)
- For Section content that belongs in the Workspace body
- For primary Workspace navigation
- As a substitute for designing content that belongs in the Workspace itself

Atlas uses Dialogs sparingly. The preference is always to surface information within the Workspace body rather than behind a Dialog.

## Overlay

The Dialog appears above the Workspace, centered. The Workspace beneath is visible but inactive — a scrim (semi-transparent overlay) covers it.

**Scrim:**
- Color: `surface.scrim` (semi-transparent dark)
- Opacity: sufficient to distinguish the Dialog from the background without fully obscuring the Workspace context
- The scrim communicates: you are in a focused interaction; the Workspace is paused
- Clicking the scrim dismisses the Dialog (if it is dismissible)

## Focus Trap

When a Dialog is open, focus is trapped within it. Tab and Shift+Tab cycle only through interactive elements within the Dialog. Focus cannot reach elements beneath the scrim.

On Dialog open: focus moves to the first interactive element within the Dialog (or the Dialog's heading, if no interactive elements precede it).

On Dialog close: focus returns to the element that triggered the Dialog.

## Dismissal

**Dismissible Dialogs:** Closed by clicking the scrim, pressing Escape, or activating a close control within the Dialog. Used for informational and low-stakes Dialogs.

**Non-dismissible Dialogs:** Can only be closed by taking an explicit action within the Dialog (confirm or cancel). Used for destructive-action confirmations. Pressing Escape activates the "Cancel" action, not dismissal.

## Sizing

**Small:** Used for simple confirmations (one action, short text). Maximum width: 400px.
**Medium:** Used for more complex interactions with additional explanation. Maximum width: 560px.
**Full-width (Overlay):** Used for Historical Records and comparisons. Covers most of the Workspace width. Maximum width: 1000px. This is not a Dialog in the strict sense — it is an overlay. Specified separately from the Dialog Container.

## Anatomy

```
DialogContainer
├── Scrim (covers Workspace)
└── DialogPanel [Panel Surface]
    ├── DialogHeader
    │   ├── Title [Role 2 typography]
    │   └── [Conditional] Close control
    ├── DialogBody
    │   └── [Content components]
    └── DialogFooter
        ├── [Conditional] Secondary Action (Cancel)
        └── Primary Action (Confirm, Proceed, or specific label)
```

## Responsive Behavior

**Desktop and Tablet:** Dialog appears centered. Maximum widths as specified. Scrim covers full viewport.

**Mobile:** Dialog occupies full width. For small and medium Dialogs: the Dialog slides up from the bottom (bottom sheet pattern). Full-width Overlay: full-screen on mobile.

## Accessibility

- Dialog: `role="dialog"` with `aria-modal="true"` and `aria-labelledby="[dialog-title-id]"`.
- Focus trap: implemented with a focus-trap utility. All focus management is explicit.
- On open: `aria-hidden="true"` applied to the Workspace body behind the scrim. Removed on close.
- Escape key: closes dismissible Dialogs; activates Cancel in non-dismissible Dialogs.
- Screen reader: Dialog appears immediately in the reading order; content beneath is hidden.
- Motion: Dialog uses the Open/Close motion tokens on enter/exit. Reduced motion: instant appear/disappear.

## Composition Rules

- **Contains:** Dialog Header (required), Dialog Body (required), Dialog Footer (required when actions are needed).
- **Is contained by:** The Workspace root, above the scrim z-index layer.
- **Does not contain:** Workspace Frames, Navigation Bars, or other modal overlays.

## Token Mapping

| Visual Property | Token |
|-----------------|-------|
| Dialog background | `surface.panel` |
| Dialog border | `color.border.standard` |
| Dialog border-radius | `radius.dialog` |
| Dialog shadow | `elevation.overlay` |
| Scrim color | `surface.scrim` |
| Dialog z-index | `elevation.dialog.zIndex` |
| Title color | `color.text.primary` |
| Open motion | `motion.open.duration` / `motion.open.easing` |
| Close motion | `motion.close.duration` / `motion.close.easing` |

## Future Extensibility

The Dialog Container is the base for all future Atlas overlay interactions. Future extensions:
- Sheet Dialog (bottom sheet): already specified for mobile. Can be promoted to tablet if use cases emerge.
- Multi-step Dialog: a Dialog with internal navigation between steps. Governed by the same focus trap and accessibility rules.
- Confirmation Dialog template: a standard configuration for destructive action confirmations (specific label, destructive action styled distinctly from the cancel action).

---

# 17. Foundation Accessibility Rules

This specification applies to all Foundation Components. Individual component accessibility rules are defined in their respective sections above. This section establishes the shared rules that govern all Foundation Components.

## Keyboard Navigation

**Tab order:** The tab order within a Workspace follows the visual reading order — top to bottom, left to right. Foundation Components define the macro tab order; reasoning components define the micro tab order within them.

**Focus never disappears.** If an action removes the focused element (e.g., dismissing a Dialog), focus moves to a logical successor. If a Section collapses (user did not initiate it), focus does not move.

**Tab stops:** Every interactive Foundation Component element is a tab stop. Purely structural elements (Workspace Frame, Layout Containers) are not tab stops.

**Arrow key navigation:** Within compound components (Toolbar, Navigation Bar), arrow keys navigate between child elements. Tab moves to the next component-level tab stop.

## Focus

**Focus indicator:** `:focus-visible` only. Never `:focus` (which would show focus rings on mouse clicks). Focus ring: `outline: [width.focus.ring] solid [color.focus.ring]; outline-offset: 2px`. Color: `color.focus.ring`. Width: `width.focus.ring`. The 2px offset value has no canonical `UX-012D` token — `radius.focus.ring` governs the ring's own corner radius, not its separation from the focused element, and no separate offset token exists; the 2px value is stated directly as implementation prose *(missing foundation, see §18 traceability)*.

**Minimum focus indicator size:** The focus ring must be large enough to encompass the entire interactive element with 2px offset on all sides.

**Focus in scrolled contexts:** When programmatic focus moves to an element not in the visible scroll region, the browser scrolls the element into view. Use `scrollIntoView({ behavior: 'smooth', block: 'nearest' })` where manual scroll management is needed.

## Touch

**Minimum touch target:** 44×44px for all interactive elements. This applies to the tappable hit area, not necessarily the visual size of the element.

**Touch target extension:** Small visual elements (chevrons, small icons) have their touch target extended through padding or a transparent hit area.

**Hover equivalents:** Every interaction available only on hover has a touch-accessible equivalent: a persistent control, a tap-to-reveal pattern, or a long-press alternative.

**Touch feedback:** Interactive elements provide visual feedback on press (the `pressed` interaction token). This applies to all touch-interactive Foundation Components.

## Screen Readers

**Landmark regions:** Every Foundation Component that constitutes a landmark provides the correct HTML element or ARIA role:
- Workspace Frame body: `<main>`
- Workspace Header: `<header>`
- Workspace Footer: `<footer>`
- Navigation Bar: `<nav aria-label="Workspace navigation">`
- Toolbar: `<nav aria-label="Workspace actions">` or `role="toolbar"`
- Dialogs: `role="dialog" aria-modal="true"`

**Headings:** One `<h1>` per page (the Workspace Subject Title in the Header). Section Titles are `<h2>`. Sub-section titles within a Section Body are `<h3>`. No heading levels are skipped.

**Live regions:** State changes that are not visually obvious to screen reader users are announced through `aria-live` regions:
- `aria-live="polite"`: Draft Indicator changes, Save confirmations, Loading completion.
- `aria-live="assertive"`: Error states that block the user's intended action. Used sparingly.

**Hidden structural elements:** Separators, decorative icons, and purely visual elements carry `aria-hidden="true"`.

## Reduced Motion

All Foundation Component animations respect `@media (prefers-reduced-motion: reduce)`.

Reduced-motion fallbacks for all twelve motion tokens:
- Open, Close: instant appear/disappear (no duration)
- Expand, Collapse: instant height change (no duration)
- Highlight, Fade, Replace: instant state change
- Insert, Remove: instant appear/disappear
- Navigate: instant position change (no smooth scroll)
- Update: no animation (state changes instantly)
- Loading: static skeleton (no shimmer animation)

The reduced-motion preference is applied at the CSS level via `@media` query, not conditionally in JavaScript.

## Zoom

Atlas must function at browser zoom levels from 100% to 200%. At 200% zoom:
- No content is clipped.
- No horizontal scroll is introduced (text reflows).
- Minimum touch targets remain sufficient.
- Focus indicators remain visible.

## High Contrast

Foundation Components must function in Windows High Contrast Mode. This means:
- Focus indicators are visible (they use `outline` which is respected in High Contrast mode, not `box-shadow` which is not).
- Borders are defined with `border` properties (not `background-color` alone, which may be overridden).
- Status indicators include text labels (not color alone).

## Error Prevention

Foundation Components prevent errors through:
- Confirmation Dialogs before destructive actions (never immediate destruction)
- Autosave with Draft Indicator (work is never silently lost)
- Focus management after validation failures (focus moves to the first invalid field)
- Non-destructive interaction defaults (collapse, navigate, and view actions never destroy content)

---

# 18. Foundation Token Mapping

A consolidated mapping of all Foundation Components to the Atlas semantic token system. This serves as the implementation reference. All values are token references — no hardcoded values.

## Phase 4: Foundation Token Alignment

*(Added per the Atlas UX Architecture Foundation & Collaboration Token Alignment task, 2026-08-02.)* This document previously referenced numerous unsupported bare `text.*`, `border.*`, `status.*`, and `action.*` tokens, superseded `focus.ring.*` ordering, bare `motion.<event>` references, and undocumented `progress.*`/`loading.skeleton.*` references, none of which `UX-012D` defines. Each occurrence throughout this document and this section's own consolidated tables has been individually corrected or disclosed in place, following the identical semantic-role analysis the completed Reasoning Token Architecture program (Phases 1–3C) already applied to `UX-013B`. This table summarizes every prior unsupported reference, its occurrence count at the time of this correction, and its resolution.

**Traceability — every prior unsupported reference, accounted for exactly once:**

| Previous token | Occurrences | Resolution | Rationale | Status |
|---|---|---|---|---|
| `text.label.secondary` | 4 | `color.text.secondary` | Supporting/subordinate label text | Reuse |
| `text.heading.primary` | 4 | `color.text.primary` | Highest-tier heading text (Role 2 typography) | Reuse |
| `text.heading.secondary` | 4 | `color.text.secondary` | Second-tier heading text (Role 3 typography) | Reuse |
| `text.contextual` | 5 | `color.text.tertiary` | Quiet, contextual, or supporting text | Reuse |
| `text.action.secondary` | 5 | `color.text.tertiary` | Inline/Section Action, per `UX-012B` §15 — explicitly Tertiary, regardless of the local name's own use of "secondary" | Reuse |
| `text.action.navigation` | 3 | `color.text.tertiary` | Shares Role 5/`type.breadcrumb` typography with already-tertiary-mapped Supporting Metadata | Reuse |
| `text.action.navigation.hover` | 1 | `opacity.interaction.hover` applied atop the base color | A delta on an existing color, not a separate hover-color token | Reuse |
| `text.muted` | 7 | `color.text.tertiary` | Quiet, de-emphasized text | Reuse |
| `text.disabled` | 2 | `color.text.tertiary` at `opacity.disabled` | The enabled action's own color, dimmed — not a distinct token | Reuse |
| `border.header.bottom` | 2 | Neutral structural border, prose only | No literal `UX-012D` token for the "standard" border weight | Missing foundation |
| `border.footer.top` | 2 | Neutral structural border, prose only | Same | Missing foundation |
| `border.toolbar.bottom` | 2 | Neutral structural border, prose only | Same | Missing foundation |
| `border.navigation.bottom` | 2 | Neutral structural border, prose only | Same | Missing foundation |
| `border.section` | 2 | Neutral structural border, prose only | Same | Missing foundation |
| `border.surface` | 5 | Neutral structural border, prose only | Same | Missing foundation |
| `border.divider` | 3 | Neutral hairline treatment, prose only | No literal `UX-012D` token for the "hairline" border weight | Missing foundation |
| `border.divider.width` | 2 | 1px, stated directly | No `width.*` token exists beyond `width.focus.ring` | Missing foundation |
| `status.monitoring.badge.background` | 1 | `surface.elevated` | Aggregate count spans two severities (Approaching + Triggered) — no single semantic color is accurate; resolved neutrally, per Option A | Reuse |
| `status.monitoring.badge.text` | 1 | `color.text.primary` | Numeric count requires high legibility | Reuse |
| `action.primary.background` | 1 | No dedicated token — existing neutral surface + outline | `UX-012B` §15: Primary Action is "defined surface or clear outline... Not a filled bright button" | Reuse (no token needed) |
| `action.primary.text` | 1 | `color.text.primary` | `UX-012B` §15: Primary Action uses "primary text color" | Reuse |
| `action.secondary.text` | 1 | `color.text.secondary` | Genuine footer-level Secondary Action per `UX-012B` §15 (placement matches exactly — unlike `UX-013B`'s locally-named "secondary" actions, which are Inline Actions) | Reuse |
| `action.primary.disabled.background` | 1 | `opacity.disabled` applied to the Primary Action's own base treatment | `ADR-002` C-06: `aria-disabled="true"`, never native `disabled`, already correctly stated in this component's own Accessibility section | Reuse |
| `focus.ring.color` | 3 | `color.focus.ring` | Canonical ordering, `UX-012D` §3 | Reuse |
| `focus.ring.width` | 1 | `width.focus.ring` | Canonical ordering, `UX-012D` §3 | Reuse |
| `focus.ring.offset` | 1 | 2px, stated directly | `UX-012D` §2's Focus tokens description names exactly three properties (width, color, radius) — no offset property exists, conceptually or literally | Missing foundation |
| `motion.expand` | 1 | `motion.expand.duration` / `.easing` | Already formalized, Phase 3B | Reuse |
| `motion.collapse` | 1 | `motion.collapse.duration` / `.easing` | Already formalized, Phase 3B | Reuse |
| `motion.update` | 1 | `motion.update.duration` / `.easing` | Already formalized, Phase 3B | Reuse |
| `motion.fade` | 1 | `motion.fade.duration` / `.easing` | Already formalized, Phase 3B | Reuse |
| `motion.open` | 2 | Not formalized in `UX-012D` — disclosed, not invented | Phase 3B excluded it for lack of a consuming reference; `UX-013A` is one, not previously accounted for | Missing foundation |
| `motion.close` | 2 | Not formalized in `UX-012D` — disclosed, not invented | Same | Missing foundation |
| `motion.navigate` | 1 | Not formalized in `UX-012D` — disclosed, not invented | Same | Missing foundation |
| `progress.fill` | 2 | No canonical foundation | No governing source maps a progress-bar fill to any existing token; not guessed | Missing foundation |
| `progress.track` | 1 | No canonical foundation | Same | Missing foundation |
| `loading.skeleton.base` | 1 | No canonical foundation | A neutral placeholder shape color, distinct from the shimmer animation; no governing source maps it to a specific surface tier | Missing foundation |
| `loading.skeleton.shimmer` | 1 | `opacity.loading.pulse.min` / `.max` | Redundant second name for the identical effect already-governed by these tokens (same pattern as `motion.loading`, Phase 3B) | Reuse |

Nine items remain disclosed as missing `UX-012D` foundations — not invented, not silently presented as canonical. They are each individually flagged, in place, throughout this document, and summarized in Remaining Findings in the governing task's own final report. Every other item reuses a token `UX-012D` already defines; zero new tokens were added in this phase.

## Phase 5: Foundation Foundation-Extension Alignment

*(Added per the Atlas UX Architecture Foundation Token Alignment (UX-013A Final Alignment) task, 2026-08-02.)* The completed Missing Foundation Resolution Phase 1: UX-012D Canonical Foundation Additions task (2026-08-02) formalized five of the nine items the Phase 4 table, above, disclosed as missing foundations: `color.border.hairline`, `color.border.standard` (`UX-012D` §3, new Border group), and `motion.open.duration`/`.easing`, `motion.close.duration`/`.easing`, `motion.navigate.duration`/`.easing` (`UX-012D` §3, Motion Architecture group, extended). This correction replaces the temporary implementation-prose treatment those five items required — written only because no canonical token yet existed — with the now-canonical token references, throughout this document. The Phase 4 table, above, is preserved unchanged as the historically accurate record of what was disclosed at that time; it is not rewritten.

**Traceability — every item resolved by this phase, accounted for exactly once:**

| Previous treatment | Occurrences | Resolution | Rationale | Status |
|---|---|---|---|---|
| Neutral structural border, prose only (`border.header.bottom`) | 2 | `color.border.standard` | Container boundary, per `UX-012D` §2/§3 | Reuse |
| Neutral structural border, prose only (`border.footer.top`) | 2 | `color.border.standard` | Same | Reuse |
| Neutral structural border, prose only (`border.toolbar.bottom`) | 2 | `color.border.standard` | Same | Reuse |
| Neutral structural border, prose only (`border.navigation.bottom`) | 2 | `color.border.standard` | Same | Reuse |
| Neutral structural border, prose only (`border.section`) | 2 | `color.border.standard` | Same | Reuse |
| Neutral structural border, prose only (`border.surface`) | 5 | `color.border.standard` | Same | Reuse |
| Neutral hairline treatment, prose only (`border.divider`) | 3 | `color.border.hairline` | Explicitly named "subtle section dividers," per `UX-012D` §2/§3 | Reuse |
| Not formalized in `UX-012D`, disclosed (`motion.open`) | 2 | `motion.open.duration` / `motion.open.easing` | Live Dialog consuming reference, per `UX-012D` §3 extension | Reuse |
| Not formalized in `UX-012D`, disclosed (`motion.close`) | 2 | `motion.close.duration` / `motion.close.easing` | Same | Reuse |
| Not formalized in `UX-012D`, disclosed (`motion.navigate`) | 1 | `motion.navigate.duration` (context-dependent) / `motion.navigate.easing` | Live Navigation Bar/Scroll Container consuming reference; duration genuinely two-valued per `UX-012D` §3 | Reuse |

Four items remain exactly as Phase 4 disclosed them, unaffected by this correction: `border.divider.width` (no `width.*` foundation beyond `width.focus.ring`), `focus.ring.offset`, `progress.fill`/`progress.track`, and `loading.skeleton.base`. None of these was added by the governing `UX-012D` task, and none is guessed here. Every replacement above reuses a token `UX-012D` already defines; zero new tokens were added in this phase.

## Phase 6: Surface Naming Consistency (Release Polish)

*(Added per the Atlas UX Architecture Token Architecture Release Polish (Final Sprint) task, 2026-08-02.)* The completed Final Corpus Verification (Release Candidate Audit) found this document used a non-canonical `surface.<role>.background` naming pattern throughout — inconsistent with `UX-012D` §3's own Surface Hierarchy (Phase 1), which names its four neutral tiers `surface.background`, `surface.primary`, `surface.elevated`, `surface.panel` (no `.background` suffix), and with the already-canonical, pre-existing `surface.historical`. Some rows had already been corrected to the canonical bare form by intervening work (the Monitoring Badge and Status Badge corrections); the remainder had not, leaving the document in a mixed state. Every occurrence is now resolved, traced directly to `UX-012D` §3:

- **`surface.workspace.background` → `surface.background`** — direct textual match: `UX-012D` §3 names `surface.background` as "the base Workspace surface"; this document's own Tier 0 is named "Workspace Background... Workspace Frame body region."
- **`surface.section.background` → `surface.primary`** — direct textual match: this document's own Composition prose already states "A Section Container uses `surface.primary[.background]`," and `UX-012D`'s Tier 1 ("Primary Surface") is independently confirmed by this document's own "Use: Standard, Reasoning, Editable, and Comparison Sections."
- **`surface.primary.background` → `surface.primary`**, **`surface.elevated.background` → `surface.elevated`**, **`surface.panel.background` → `surface.panel`** — the Surface component's own Tier 1/2/3 definitions; direct 1:1 name correspondence to `UX-012D` §3.
- **`surface.historical.background` → `surface.historical`** — `UX-012D` §3 already names `surface.historical` explicitly as an existing, unchanged, component-scoped exception; only the erroneous suffix is removed.
- **`surface.monitoring.background` → `surface.monitoring`** — no `UX-012D` §3 tier or named exception covers Monitoring Surface (its own "subtle warm variation" description is semantically distinct from the four neutral tiers); kept component-specific, per `UX-012D` §3's own explicit allowance for genuinely-needed component-scoped surfaces, mirroring the already-established `surface.decision.card` pattern. No tier reassignment is guessed.
- **`surface.header.background` → `surface.header`**, **`surface.toolbar.background` → `surface.toolbar`**, **`surface.footer.background` → `surface.footer`**, **`surface.navigation.background` → `surface.navigation`** — no `UX-012D` §3 tier's own "Use" description names Header, Toolbar, Footer, or Navigation Bar; kept component-specific, on the same basis as Monitoring Surface, rather than guessed into one of the four neutral tiers without direct evidence.

This correction changes no component behavior, anatomy, or Product meaning — only token spelling, in both component-level tables and the Section 18 appendix, which now agree throughout. No new token is introduced; every replacement above is either the exact canonical `UX-012D` §3 form or an already-permitted component-scoped name, mechanically corrected to remove the erroneous `.background` suffix.

## Typography Tokens

| Token | Applies To |
|-------|-----------|
| `type.role1.size`, `type.role1.weight`, `type.role1.lineHeight` | Workspace Primary Conclusion (not a Foundation Component — reference for context) |
| `type.role2.size`, `type.role2.weight`, `type.role2.lineHeight` | Section Header titles, Workspace Subject Title |
| `type.role4.size`, `type.role4.weight`, `type.role4.lineHeight`, `type.role4.letterSpacing` | Workspace Type Label, Section action labels, Status Badge labels |
| `type.role5.size`, `type.role5.weight`, `type.role5.lineHeight` | Breadcrumb labels, Contextual text, Summary text, Timestamps, Empty State supporting text |
| `type.breadcrumb` | Breadcrumb-specific composite typography token |
| `type.sans` | All non-monospace Foundation Components |
| `type.mono` | System text, identifiers (not common in Foundation Components) |

## Spacing Tokens

| Token | Applies To |
|-------|-----------|
| `space.level1` | Between closely related inline elements (icon + label in badges) |
| `space.level2` | Between label and subtitle in Section Header; compact Divider surroundings |
| `space.level3` | Between components within a Section Body |
| `space.level4` | Between Section Containers |
| `space.level5` | Between major Workspace regions |
| `space.level6` | Workspace outer padding (supplemented by breakpoint-specific tokens) |
| `space.workspace.horizontal.desktop` | Workspace Frame side padding, desktop |
| `space.workspace.horizontal.tablet` | Workspace Frame side padding, tablet |
| `space.workspace.horizontal.mobile` | Workspace Frame side padding, mobile |
| `space.section.top` | Section Container internal top padding |
| `space.section.bottom` | Section Container internal bottom padding |
| `space.section.header.vertical` | Section Header internal top and bottom padding |
| `space.header.vertical` | Workspace Header internal padding |
| `space.footer.vertical` | Workspace Footer internal padding |

## Layout Tokens

| Token | Applies To |
|-------|-----------|
| `layout.workspace.maxWidth` | Workspace Frame maximum content width (1200px) |
| `layout.editorialColumn.maxWidth` | Editorial Column maximum width (680px) |
| `layout.split.gap` | Split Layout gap between columns |
| `layout.grid.gap` | Responsive Grid gap |

## Surface Tokens

| Token | Applies To |
|-------|-----------|
| `surface.background` | Workspace Frame body |
| `surface.header` | Workspace Header |
| `surface.footer` | Workspace Footer |
| `surface.toolbar` | Workspace Toolbar |
| `surface.navigation` | Navigation Bar |
| `surface.primary` | Section Container |
| `surface.primary` | Primary Surface (Tier 1) |
| `surface.elevated` | Elevated Surface (Tier 2) |
| `surface.panel` | Panel Surface (Tier 3, Dialog) |
| `surface.historical` | Historical Surface |
| `surface.monitoring` | Monitoring Surface |
| `surface.scrim` | Dialog scrim overlay |

## Border Tokens

*(Corrected per the Atlas UX Architecture Foundation & Collaboration Token Alignment task, 2026-08-02: every row below previously named a bare `border.*` token — `border.header.bottom`, `border.footer.top`, `border.toolbar.bottom`, `border.navigation.bottom`, `border.section`, `border.surface`, `border.divider`, `border.divider.width` — none of which exists in `UX-012D`. `UX-012D` §2 conceptually describes two neutral border weights ("hairline," "standard") that would cover these roles, but neither has ever been literalized as a named token in `UX-012D` §3. This is a genuinely missing foundation, not a naming error this document alone can fix; no token is invented here. The rows below now use precise implementation prose in place of a token name, and each is individually disclosed as a missing foundation in the traceability record, below.)*

*(Further corrected per the Atlas UX Architecture Foundation Token Alignment (UX-013A Final Alignment) task, 2026-08-02: the completed Missing Foundation Resolution Phase 1 task subsequently formalized both weights — `color.border.hairline` and `color.border.standard` — in `UX-012D` §3. All rows below except Divider thickness, which remains a disclosed missing foundation (no `width.*` token covers it), now cite the canonical tokens.)*

| Visual Property | Token |
|-----------------|-----------|
| Workspace Header bottom edge | `color.border.standard` |
| Workspace Footer top edge | `color.border.standard` |
| Workspace Toolbar bottom edge | `color.border.standard` |
| Navigation Bar bottom edge | `color.border.standard` |
| Section Container border | `color.border.standard` |
| Standard surface border | `color.border.standard` |
| Divider color | `color.border.hairline` |
| Divider thickness (1px) | Stated directly; no dedicated width token *(missing foundation)* |

## Elevation Tokens

| Token | Applies To |
|-------|-----------|
| `elevation.header.zIndex` | Workspace Header z-index |
| `elevation.toolbar.zIndex` | Workspace Toolbar z-index |
| `elevation.footer.zIndex` | Workspace Footer z-index |
| `elevation.dialog.zIndex` | Dialog Container z-index |
| `elevation.toolbar.shadow` | Toolbar shadow when content scrolls beneath |
| `elevation.footer.shadow` | Footer shadow when content scrolls beneath |
| `elevation.overlay` | Dialog/overlay drop shadow |
| `elevation.none` | No shadow |

## Radius Tokens

| Token | Applies To |
|-------|-----------|
| `radius.section` | Section Container border-radius |
| `radius.dialog` | Dialog Container border-radius |
| `radius.badge` | Status Badge border-radius |
| `radius.button` | Action component border-radius |

## State Tokens (Foundation-relevant)

*(Corrected per the Status Badge Token Architecture Correction task, 2026-08-02: this table previously listed a `status.*` token for every row below. That namespace does not exist in `UX-012D` and is rejected in full; see §13, above, for the full correction and its own sourcing. The corrected mapping is restated here for this table's own consolidated-reference purpose, not restated as a second, independently-maintained specification.)*

| Token | Applies To |
|-------|-----------|
| None — neutral, no color distinction | Draft Status Badge |
| None — neutral, no color distinction | Saved Status Badge |
| `type.badge.completed` | Completed Status Badge |
| `color.text.historical`, `surface.historical` | Historical Status Badge |
| None — neutral, no color distinction | Updated Status Badge |
| `color.semantic.amber` | Warning Status Badge |
| None — neutral, no color distinction (Active); `color.semantic.amber` (Approaching); `color.semantic.red` (Triggered) | Monitoring Status Badges |

## Focus Tokens

*(Corrected per the Atlas UX Architecture Foundation & Collaboration Token Alignment task, 2026-08-02: `focus.ring.color` and `focus.ring.width` used the pre-Phase-1 naming order, superseded by `UX-012D` §3's own canonical `color.focus.ring` / `width.focus.ring` / `radius.focus.ring` ordering. `focus.ring.offset` is not corrected to any token — `UX-012D` §2's own Focus tokens description names exactly three properties (pixel width, color, border-radius behavior); no offset property is described, conceptually or literally, anywhere in `UX-012D`. This is a missing foundation, not a naming error; no token is invented here.)*

| Token | Applies To |
|-------|-----------|
| `color.focus.ring` | All focus indicators |
| `width.focus.ring` | Focus ring width (2px) |
| 2px offset, stated directly — no dedicated token exists | Focus ring offset *(missing foundation)* |

## Text Tokens (Foundation-relevant)

*(Corrected per the same task: every row below previously named a bare `text.*` token, none of which exists in `UX-012D`. Each is remapped to the canonical Text Hierarchy — `color.text.primary`, `color.text.secondary`, `color.text.tertiary` — established in `UX-012D` §3, Phase 1, per the same semantic-role analysis already applied throughout `UX-013B`.)*

| Token | Applies To |
|-------|-----------|
| `color.text.tertiary` at `opacity.disabled` | Disabled action text — the enabled action's own color, dimmed; not a distinct disabled-text token |
| `color.text.tertiary` | Inline/Section action text color (Toolbar, Section Header, Breadcrumb ellipsis) |
| `color.text.tertiary` | Navigation link color (Breadcrumb ancestors) |
| `color.text.tertiary` | De-emphasized text (separators, expansion chevrons, Empty State icon) |
| `color.text.tertiary` | Supporting contextual information (Subject Subtitle, Footer status text, Section Summary, Empty State supporting text) |
| `color.text.primary` | Section titles, Workspace Subject Title, Dialog Title |
| `color.text.secondary` | Secondary headings, current breadcrumb location, Empty State headline |
| `color.text.secondary` | Supporting labels (Workspace Type Label, Progress text) |

## Interaction Tokens (Foundation-relevant)

| Token | Applies To |
|-------|-----------|
| `opacity.interaction.hover` | Interactive element hover state (including Breadcrumb ancestor hover — a delta on the base text color, not a separate hover color) |

## Motion Tokens (Foundation-relevant)

*(Corrected per the same task: `motion.expand`, `motion.collapse`, `motion.update`, and `motion.fade` were bare event references; each now cites the canonical `motion.<event>.duration` / `motion.<event>.easing` pair `UX-012D` §3's own Motion Architecture group (Phase 3B) already defines. `motion.open`, `motion.close`, and `motion.navigate` are not corrected to a canonical form — `UX-012D`'s own Motion Architecture group explicitly instantiated only the seven events `UX-013B` consumes; Open, Close, and Navigate were left unformalized on the stated basis that "no current consuming reference" existed. `UX-013A` is exactly such a reference, not previously accounted for. This is disclosed as a missing foundation, not silently presented as canonical.)*

*(Further corrected per the Atlas UX Architecture Foundation Token Alignment (UX-013A Final Alignment) task, 2026-08-02: the completed Missing Foundation Resolution Phase 1 task subsequently formalized Open, Close, and Navigate in `UX-012D` §3's own Motion Architecture group, extending Phase 3B. All three rows below now cite the canonical tokens. Navigate's own duration is context-dependent between `motion.duration.brief` (short scrolls) and `motion.duration.standard` (long scrolls), per `UX-012D`'s own explicit definition — not a single fixed value; this document does not state a scroll-distance threshold, consistent with `UX-012D` itself not stating one.)*

| Token | Applied By |
|-------|-----------|
| `motion.open.duration` / `motion.open.easing` | Dialog open, Workspace entry |
| `motion.close.duration` / `motion.close.easing` | Dialog close, Workspace exit |
| `motion.expand.duration` / `motion.expand.easing` | Section Container expansion |
| `motion.collapse.duration` / `motion.collapse.easing` | Section Container collapse |
| `motion.navigate.duration` (context-dependent: brief or standard) / `motion.navigate.easing` | Scroll restoration, auto-scroll |
| `opacity.loading.pulse.min` / `opacity.loading.pulse.max` | Skeleton shimmer, Progress Indicator (indeterminate) |
| `motion.update.duration` / `motion.update.easing` | Status Badge changes, content updates |
| `motion.fade.duration` / `motion.fade.easing` | Status Badge transient transitions (Saved → hidden) |

## Accessibility Tokens

| Token | Applies To |
|-------|-----------|
| `accessibility.minTouchTarget` | Minimum touch target (44px) |
| `accessibility.contrastMinimum` | WCAG AA minimum contrast ratio (4.5:1) |
| `accessibility.focusRingMinSize` | Minimum focus indicator dimension |

---

# 19. Foundation Engineering Mapping

## Recommended Component Hierarchy

```
Foundation/
├── Layout/
│   ├── WorkspaceFrame
│   ├── Column
│   ├── Row
│   ├── Stack
│   ├── Split
│   └── Grid
├── Navigation/
│   ├── WorkspaceHeader
│   ├── WorkspaceToolbar
│   ├── WorkspaceFooter
│   ├── NavigationBar
│   └── Breadcrumb
├── Containers/
│   ├── SectionContainer
│   ├── SectionHeader
│   ├── DialogContainer
│   └── ScrollContainer
├── Surface/
│   └── Surface (token-application utility)
├── Structural/
│   ├── Divider
│   └── EmptyState
└── Indicators/
    ├── StatusBadge
    └── ProgressIndicator
```

## Naming Conventions

- Component names: PascalCase, matching the specification name exactly.
- Props: camelCase.
- Token references in code: use the token name as a CSS custom property (e.g., `var(--surface-workspace-background)`).
- State class names (if CSS-based): `data-state="[state-name]"` attribute pattern.

## Props

All Foundation Components follow a consistent prop pattern:

**Universal props (all Foundation Components):**
- `className?: string` — Extension point for consumer-side overrides. Not for design system customization.
- `data-testid?: string` — Testing selector. Not an ID for accessibility; use ARIA.
- `children: ReactNode` — Where the component is a container.

**No `style` prop** on Foundation Components. Inline styles bypass the token system. Engineering enforces this at the component boundary.

## Composition

Foundation Components are composed declaratively. The Workspace Frame is the root; all other Foundation Components are composed within it.

Example composition:
```jsx
<WorkspaceFrame workspaceId="decision-acme-2024" hasFooter>
  <WorkspaceHeader
    workspaceTypeLabel="Decision Workspace"
    subjectTitle="Acme Corp"
    hasDraftIndicator={hasDraft}
  />
  <WorkspaceToolbar actions={toolbarActions} />
  <NavigationBar breadcrumbs={breadcrumbs} />
  {/* Section Containers go here */}
  <WorkspaceFooter primaryAction={recordAction} status={footerStatus} />
</WorkspaceFrame>
```

## Inheritance

Foundation Components do not inherit from one another. They are composed. The Section Container does not extend the Workspace Frame; it is placed within it.

Token inheritance is through CSS custom property cascades — tokens defined on a parent element are available to all children.

## State Handling

State that belongs to the Design System is managed within the component (expansion state, focus state). State that belongs to the application (workspace content, draft status, user identity) is passed as props.

The boundary: if the state changes the component's visual presentation but is governed by Atlas design rules, the component manages it. If the state reflects application data, the consumer provides it.

## Testing Expectations

Every Foundation Component must have:
- **Structural tests:** Verifies the correct HTML elements and ARIA attributes are rendered.
- **Interaction tests:** Verifies keyboard navigation, expansion/collapse, and focus management.
- **Accessibility tests:** Automated ARIA checks (using axe-core or equivalent). Every component passes without violations.
- **Visual regression tests:** Screenshot comparison for each state and variant.
- **Responsive tests:** At three viewport widths (desktop: 1280px, tablet: 768px, mobile: 375px).

## Documentation Expectations

Each Foundation Component is documented with:
1. Purpose and semantic meaning
2. Usage examples (correct and incorrect)
3. All props with types, defaults, and descriptions
4. All states with visual descriptions
5. Accessibility notes (ARIA, keyboard, focus)
6. Token mapping reference
7. Changelog (version history)

## Versioning

Foundation Components follow semantic versioning (major.minor.patch):
- Major: breaking change to props, ARIA structure, or DOM structure.
- Minor: new optional prop, new state, new variant.
- Patch: documentation update, accessibility improvement, performance fix.

Breaking changes require a documented migration path and a minimum 2-sprint deprecation period before removal.

---

# 20. Foundation Audit

## No Duplicated Components

Review confirms:
- WorkspaceFrame and SectionContainer have distinct, non-overlapping roles.
- WorkspaceHeader and SectionHeader have distinct, non-overlapping roles.
- WorkspaceToolbar and WorkspaceFooter have distinct, non-overlapping roles.
- NavigationBar and Breadcrumb are appropriately separated (one provides the context, one provides the trail).
- Surface is a token-application utility, not a standalone visual component competing with Section Container.
- StatusBadge and ProgressIndicator serve distinct information needs (state vs. progress).
- No duplicate component found.

## Clear Ownership

Each Foundation Component has a defined owner in the Design System team. Foundation Components are the highest-priority components for ownership clarity — they underlie all Workspace content.

## Consistent Semantics

All sixteen Foundation Components have:
- A defined semantic meaning.
- A defined "When Not Used" condition.
- No semantic overlap with adjacent Foundation Components.

The semantic boundaries are confirmed clean.

## Responsive Consistency

All sixteen Foundation Components specify behavior at Desktop (≥1024px), Tablet (768px–1023px), and Mobile (<768px). No component specifies desktop behavior only.

## Accessibility Completeness

Each Foundation Component specifies:
- HTML element or ARIA role.
- Keyboard interaction.
- Focus behavior.
- Screen reader content.
- Reduced-motion behavior.
- Touch target compliance (where interactive).

## Engineering Readiness

Foundation Components are specified with:
- Component hierarchy.
- Prop interfaces.
- Composition model.
- State management boundary.
- Testing expectations.
- Documentation requirements.
- Versioning rules.

Engineering can begin implementation from these specifications without inventing behavior.

## Alignment with UX-012

All sixteen Foundation Components are present in the UX-012 Component Inventory or are derived from UX-012 Workspace and Section specifications. No Foundation Component introduced in UX-013A conflicts with a UX-012 design decision. All token mappings reference token categories defined in UX-012 Section 54–55.

---

# What UX-013A Establishes

## Workspace Structure

The Workspace Frame is fully specified: maximum width (1200px), side padding per breakpoint, sticky Header and Footer model, scroll position management, scrollable Body region, and the composition hierarchy of Header → Body → Footer. Every future Workspace is built on this specification.

## Navigation

The Workspace Header is fully specified: identity hierarchy (Workspace Type Label, Subject Title, Subject Subtitle), Return Navigation position and behavior, Status Area contents and priority, and all state variants. The Workspace Toolbar is fully specified: action priority, overflow behavior, sticky rules, and disabled behavior. The Navigation Bar and Breadcrumb are fully specified: hierarchy representation, collapsing rules, keyboard interaction, and all responsive adaptations.

## Layout

The Layout Container family is fully specified: Column (Editorial and Analytical), Row, Stack, Split Layout, Adaptive Layout, and Responsive Grid. Each has defined maximum widths, spacing rules, alignment defaults, and responsive behavior. The Editorial Column (680px maximum width, 65–70 character line length) is established as the standard for all narrative reading and writing contexts.

## Containers

The Section Container and Section Header are fully specified: anatomy, states, expansion model, auto-expansion triggers, session persistence, and composition rules. The Dialog Container is fully specified: focus trap, dismissal behavior, sizing, animation, and responsive adaptation. The Scroll Container is fully specified: vertical and horizontal scrolling rules, nested scrolling constraints, sticky element behavior, and scroll restoration.

## Surfaces

Five surface tiers are specified: Workspace Background (Tier 0), Primary (Tier 1), Elevated (Tier 2), Panel (Tier 3), plus Historical and Monitoring surfaces. All are token-mapped. Elevation model (tonal variation, not shadows) is established for all non-overlay surfaces. Overlay elevation (shadows) is established for Dialog and Historical Record overlays.

## Structural Components

The Divider is specified with semantic justification requirements, usage rules, misuse prevention, and responsive adaptation. The Empty State is specified with four subtypes (Expected, Informational, Action-Required, Error), illustration policy (no illustrations), tone guidelines, and anti-patterns.

## Shared Behaviors

The Status Badge system is fully specified: nine named badge types, priority ordering, sizing, placement rules, and transient versus persistent behavior. The Progress Indicator is fully specified: Determinate, Indeterminate, Completion gate text, Saving, Skeleton Loading, and Review Progress variants.

## Accessibility

The Foundation Accessibility Rules establish the shared accessibility model for all Foundation Components: keyboard tab order and arrow key navigation, focus indicator specification (`:focus-visible`, `color.focus.ring`, `width.focus.ring`, 2px offset), 44×44px minimum touch targets, landmark region requirements, heading hierarchy (`<h1>` → `<h2>` → `<h3>`), `aria-live` region usage, reduced motion fallbacks for all twelve motion tokens, 200% zoom compliance, and Windows High Contrast Mode support.

## Engineering Mapping

The Foundation Component hierarchy, naming conventions, universal prop patterns, composition model, state management boundary, testing requirements (structural, interaction, accessibility, visual regression, responsive), documentation requirements (seven mandatory sections), and versioning rules (semantic versioning with 2-sprint deprecation minimum) are all established.

---

# Remaining Foundation Questions

**Question 1: Section Header Stickiness Threshold**
Reason: The specification states that Section Headers may be sticky within the Workspace body for very long Sections. The threshold at which a Section is considered "long enough" to warrant a sticky header has not been specified quantitatively.
Required Evidence: Implementation observation — at what Section body height does the absence of a sticky Section Header cause measurable orientation loss during scroll?
Implementation Impact: Determines whether sticky Section Headers are opt-in per Section or applied via a length heuristic. May require a new `stickyHeader` prop on Section Container.
Priority: Low. The specification correctly defers this to implementation evidence. The opt-in prop is a safe starting point.

**Question 2: Breadcrumb Ellipsis Interaction on Touch**
Reason: The specification describes the collapsed ellipsis as expanding inline on click. On touch devices, the expand interaction and the follow-through tap into an ancestor link may be difficult to separate cleanly.
Required Evidence: Usability testing of Breadcrumb navigation on tablet and mobile, specifically the collapsed ellipsis expand interaction.
Implementation Impact: May require a distinct pattern for the collapsed breadcrumb on touch — e.g., a bottom sheet listing all ancestors rather than inline expansion.
Priority: Low. The Breadcrumb is suppressed on mobile and simplified on tablet; this primarily affects tablet users who have collapsed ancestors.

**Question 3: Workspace Toolbar Presence Criteria**
Reason: The specification defines the Workspace Toolbar as optional, appearing only when secondary Workspace-level actions are needed. The specific criteria for which actions belong in the Toolbar versus the Footer versus Section-level actions are defined in principle but will require validation against real Workspace content.
Required Evidence: Content audit of the four current Workspaces — which actions appear, at what frequency, and whether they are Workspace-level or Section-level in practice.
Implementation Impact: May result in the Toolbar being absent from certain Workspaces entirely (e.g., the Dashboard or Portfolio Workspace may not require a Toolbar at all), or in promoting some currently Section-level actions to the Toolbar.
Priority: Medium. This affects the structural configuration of each Workspace. Should be resolved before Workspace-specific implementation begins.

**Question 4: Dialog vs. Overlay Boundary**
Reason: The specification distinguishes Dialogs (focused overlays for confirmations and supplementary information) from Overlays (full-width overlays for Historical Records and comparisons). The boundary between these two types — specifically when to use a Dialog versus a wide Overlay for contextual information — requires a decision rule that is currently stated only as a principle.
Required Evidence: Enumeration of all current and anticipated Atlas use cases that require an overlay interaction. Classification of each against the Dialog/Overlay boundary criteria.
Implementation Impact: If the boundary is not clear, designers and engineers will inconsistently choose between Dialog and Overlay, creating interaction inconsistency across Workspaces.
Priority: Medium. Should be resolved in UX-013B (which will encounter overlay contexts in Reasoning Components) or in a follow-up Foundation amendment.

**Question 5: Scroll Restoration and Session Boundary**
Reason: Scroll restoration is specified as per-session (cleared between sessions). The definition of "session" in the Atlas product context — whether a session ends when the browser closes, when the user logs out, or after a defined period of inactivity — has not been specified.
Required Evidence: Product decision on session definition. Engineering input on what storage mechanism is appropriate (sessionStorage vs. localStorage vs. server-side persistence).
Implementation Impact: Determines the implementation of the scroll restoration storage mechanism. Server-side persistence would allow restoration across devices, which may be desirable for Decision Workspace users who switch between desktop and tablet.
Priority: Low for initial implementation (session storage is a reasonable default); Medium for long-term product planning.

---

# Foundation Component Inventory

The official Foundation Component Inventory for UX-013A. All components at Candidate maturity unless noted.

| Category | Component Name | Semantic Purpose | Primary Workspace | Secondary Reuse | Engineering Priority | Figma Priority | Maturity | Future Owner |
|----------|---------------|-----------------|-------------------|-----------------|---------------------|----------------|----------|--------------|
| Layout | WorkspaceFrame | Outermost structural container | All | All | Immediate | Immediate | Candidate | Design System |
| Layout | Column (Editorial) | Narrative reading/writing column | Investment, Decision | All | Immediate | Immediate | Candidate | Design System |
| Layout | Column (Analytical) | Data analysis full-width column | Investment, Portfolio | All | High | High | Candidate | Design System |
| Layout | Stack | Vertical arrangement with consistent spacing | All | All | Immediate | Immediate | Stable | Design System |
| Layout | Row | Horizontal arrangement with wrapping | All | All | High | High | Candidate | Design System |
| Layout | Split Layout | Parallel column comparison layout | Portfolio, Decision | Comparison contexts | High | High | Candidate | Design System |
| Layout | Adaptive Layout | Container-query responsive layout | Decision | All | Medium | Medium | Experimental | Design System |
| Layout | Responsive Grid | Multi-column grid for scanning | Dashboard | Dashboard-like | High | High | Candidate | Design System |
| Navigation | WorkspaceHeader | Workspace identity and orientation | All | All | Immediate | Immediate | Candidate | Design System |
| Navigation | WorkspaceToolbar | Secondary workspace-level actions | Investment, Decision | Portfolio | High | High | Candidate | Design System |
| Navigation | WorkspaceFooter | Primary action and completion status | Decision | Investment, Portfolio | Immediate | Immediate | Candidate | Design System |
| Navigation | NavigationBar | Navigation context and path | Investment, Decision | Portfolio | High | High | Candidate | Design System |
| Navigation | Breadcrumb | Hierarchical path with navigation | Investment, Decision | Portfolio | High | High | Candidate | Design System |
| Containers | SectionContainer | Structural wrapper for reasoning sections | All | All | Immediate | Immediate | Candidate | Design System |
| Containers | SectionHeader | Section identity and expansion control | All | All | Immediate | Immediate | Candidate | Design System |
| Containers | DialogContainer | Focused overlay for confirmations | All | All | High | High | Candidate | Design System |
| Containers | ScrollContainer | Defined scrollable region | All | All | High | Medium | Candidate | Design System |
| Surface | Surface (Primary) | Tier 1 content background | All | All | Immediate | Immediate | Candidate | Design System |
| Surface | Surface (Elevated) | Tier 2 secondary content background | Decision | All | High | High | Candidate | Design System |
| Surface | Surface (Panel) | Tier 3 overlay background | All | All | High | High | Candidate | Design System |
| Surface | Surface (Historical) | Immutable content background | All | All | High | High | Candidate | Design System |
| Surface | Surface (Monitoring) | Active monitoring surface | Dashboard, Decision | Investment | High | Medium | Candidate | Design System |
| Structural | Divider (Horizontal) | Visual boundary between content groupings | All | All | Immediate | Immediate | Stable | Design System |
| Structural | Divider (Vertical) | Boundary between parallel columns | Portfolio, Decision | Comparison | High | High | Candidate | Design System |
| Structural | EmptyState (Expected) | Communication of correct empty condition | All | All | High | High | Candidate | Design System |
| Structural | EmptyState (Informational) | Communication of not-yet-established state | Decision | All | High | High | Candidate | Design System |
| Structural | EmptyState (Action-Required) | Communication of required authorship | Decision | Investment | High | High | Candidate | Design System |
| Structural | EmptyState (Error) | Communication of data unavailability | All | All | High | High | Candidate | Design System |
| Indicators | StatusBadge (Draft) | Unsaved content communication | Investment, Decision | All authoring | Immediate | Immediate | Candidate | Design System |
| Indicators | StatusBadge (Historical) | Immutable content communication | All | All | Immediate | Immediate | Candidate | Design System |
| Indicators | StatusBadge (Monitoring states) | Monitoring lifecycle communication | Dashboard, Decision | Investment | High | High | Candidate | Design System |
| Indicators | StatusBadge (Saved, Updated, Completed, Warning) | Transient and state status | All | All | High | High | Candidate | Design System |
| Indicators | ProgressIndicator (Skeleton) | Loading content placeholder | All | All | Immediate | Immediate | Candidate | Design System |
| Indicators | ProgressIndicator (Determinate) | Known-endpoint progress communication | Decision | All | High | High | Candidate | Design System |
| Indicators | ProgressIndicator (Indeterminate) | Open-ended process communication | All | All | High | High | Candidate | Design System |

---

# Implementation Readiness Assessment

## Design Completeness — Ready

All sixteen Foundation Components are specified with: purpose, semantic meaning, when used, when not used, variants, anatomy, properties, states, interaction, accessibility, responsive behavior, composition rules, spacing rules, token mapping, Figma architecture, and engineering guidance. No Foundation Component requires additional design philosophy work.

## Engineering Readiness — Ready

The Foundation Engineering Mapping (Section 19) provides: component hierarchy, naming conventions, prop patterns, composition model, state management boundary, testing requirements, documentation requirements, and versioning rules. Engineering can begin implementation from this specification.

**Recommended implementation sequence:**
1. Design Token implementation (token dictionary, CSS custom properties)
2. Layout Containers (Stack, Column, Row — used by all other components)
3. WorkspaceFrame
4. WorkspaceHeader
5. WorkspaceFooter
6. SectionContainer + SectionHeader
7. Divider, Surface utilities
8. StatusBadge, ProgressIndicator
9. EmptyState
10. NavigationBar, Breadcrumb
11. WorkspaceToolbar
12. DialogContainer, ScrollContainer

## Accessibility Readiness — Ready

Every Foundation Component specifies ARIA roles, keyboard interaction, focus management, screen reader behavior, and reduced-motion fallbacks. The Foundation Accessibility Rules (Section 17) provide the shared model. No Foundation Component requires additional accessibility design work.

## Responsive Readiness — Ready

All Foundation Components specify behavior at Desktop (≥1024px), Tablet (768px–1023px), and Mobile (<768px). Responsive token mappings (breakpoint-specific spacing, maximum-width adaptation) are defined.

## Token Readiness — Ready, with disclosed exceptions

*(Corrected per the Atlas UX Architecture Foundation & Collaboration Token Alignment task, 2026-08-02: this section previously read "Ready" without qualification. Section 18's own Phase 4: Foundation Token Alignment subsection, above, resolved the great majority of this document's prior unsupported token references by reuse of already-canonical `UX-012D` tokens, but nine items — three neutral structural border weights (used at eight distinct locations), a focus-ring offset value, three unformalized Motion events (Open, Close, Navigate), and a progress-bar/skeleton-base fill treatment — have no canonical `UX-012D` foundation and are disclosed as missing, not invented. Implementation of the affected properties requires those foundations to be established first.)*

Section 18 provides a complete Foundation Token Mapping across all twelve token categories. Before engineering implementation of Foundation Components, the token dictionary (all semantic token names and their values) must be finalized. Every token name is either already canonical in `UX-012D`, or explicitly disclosed as a missing foundation requiring its own future, separately-authorized addition — none is presented as canonical without being one. The values of already-canonical token names are Atlas design decisions to be confirmed in the token implementation document.

## Documentation Quality — Ready

Each Foundation Component has documentation sufficient to build from. The Documentation Standards from UX-012 Section 61 (ten mandatory sections) are satisfied for each component.

## Testing Readiness — Ready

Testing expectations are defined for each Foundation Component: structural tests, interaction tests, accessibility tests (axe-core), visual regression tests, and responsive tests at three breakpoints.

## Overall Implementation Readiness

**The Foundation Component Library is ready for production implementation.**

Token dictionary finalization is the only prerequisite. Once tokens have confirmed values, Foundation Component implementation can begin in the sequence above. UX-013B (Reasoning Components) should not block Foundation Component implementation — Foundation Components are independent of reasoning content and can be built in parallel with UX-013B production.

---

# Requirements for UX-013B

## UX-013B — Atlas Component Specification: Reasoning Components

UX-013B specifies every Reasoning Component in the same production-ready depth as UX-013A specified Foundation Components. Every component should be documented in sufficient detail that Figma components can be built directly and engineering can implement without inventing behavior.

**Scope:** All Reasoning Components from the UX-012 Component Inventory. This includes:

**Conclusion Components:** Primary Conclusion, Current Conclusion, Decision Required, What Changed, Portfolio Conclusion, Review Conclusion, Decision Summary.

**Reasoning Narrative Components:** Supporting Factors, Challenges (all three severity levels), Assumptions (all four status states), Invalidation Condition, Implementation Summary, Review Condition.

**Evidence and Opportunity Components:** Opportunity Summary, Opportunity Cost (as a Reasoning component — the standalone visual is a Comparison Component), Evidence Summary.

**Comparison Components:** Before/After, Alternative Comparison, Opportunity Cost Component (the structured visual), Allocation Comparison, Historical Comparison.

**Reasoning Block Components:** Context Panel, Relationship display, Supporting Metadata within Reasoning.

**For each Reasoning Component, UX-013B must specify:**

- Purpose and Semantic Meaning (what reasoning purpose does this serve?)
- When Used / When Not Used
- All Variants (justified by semantic difference)
- Complete Anatomy (every sub-element named and described)
- Properties (all configurable properties with types, defaults, required/optional)
- All States (from the fourteen interaction tokens, plus component-specific states)
- Interaction Behavior (keyboard, mouse, touch; expansion; editing if applicable)
- Atlas Collaboration Behavior (how Atlas Suggestions relate to this component)
- Accessibility Behavior (ARIA, keyboard, screen reader, reduced motion)
- Responsive Behavior (Desktop, Tablet, Mobile)
- Composition Rules (what this contains, what contains it, nesting restrictions)
- Content Rules (length limits, required content, prohibited content)
- Spacing Rules (internal padding, relationship to adjacent components)
- Authorship Behavior (where applicable — how user-authored content is presented and attributed)
- Historical Behavior (how this component appears when it is or contains historical content)
- Token Mapping (every visual property mapped to a semantic token)
- Figma Component Architecture (frames, auto-layout, variants, properties, slots)
- Engineering Naming and Guidance
- Examples and Anti-Patterns
- Future Extensibility

**Relationships between Reasoning Components must be specified:**
- How Supporting Factors and Challenges relate to the Assumption component
- How Assumptions feed Contradictions in the Decision Workspace
- How the Opportunity Summary and Opportunity Cost relate
- How Comparison Components share structure with Reasoning Narrative Components
- How Historical Behavior propagates through a Reasoning Component hierarchy

**The Reasoning Component specification should make explicit:**
- The visual distinction between Atlas-generated and user-authored content within each component
- The visual distinction between current reasoning and historical reasoning
- How each component changes when its parent Section is collapsed versus expanded
- How each component participates in the completion gate (if it hosts required content)

Do not produce UX-013B yet. The completed UX-013A is the prerequisite.

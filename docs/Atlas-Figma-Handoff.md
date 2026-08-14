# Atlas Alpha — Figma Implementation Handoff

**Purpose of this document.** This is a factual snapshot of the current Atlas Alpha implementation for four pages — Daily Brief, Discovery, Portfolio, Investment Case. It exists so a designer can redesign the visual presentation of these pages in Figma **without changing what the product does**. Nothing here is a proposal, a critique, or a recommendation. Every section describes code that exists today, as of this writing.

**How to read this document.** Each page has nine sections: Purpose, Current Information Hierarchy, Components, Interactions, Data, Business Rules, Preserve, Technical Notes, Screenshot Map. Wherever this document names a translation key (e.g. `portfolio.summary.heading`), that is the literal key in `frontend/src/i18n/translations/en.ts` / `sv.ts` — the designer can look up the exact current English/Swedish copy there.

**Wire format convention (applies to every endpoint below).** All JSON request/response bodies use camelCase keys (`ADR-004`, `atlas/core/infrastructure/api/serialization.py`'s `CamelModel`). Enum-valued fields (e.g. `conviction.level`, `reconciliationStatus`) are sent as raw English string values and translated only at render time by the frontend — the wire value itself is never localized.

**Foundation component library (used identically across all four pages).** `Container` (page-width wrapper), `Stack` (vertical layout, `gap` prop: `"inter-section"` | `"intra-section"` | `"metadata"` | `"row"`), `Inline` (horizontal layout, same gap scale, optional `wrap`), `Surface` (card container, `tier="primary"` throughout these four pages), `Heading` (`level={1|2|3}`), `Text` (`as="p"|"span"|"label"`, `color="primary"|"secondary"|"tertiary"`), `Button` (`variant="primary"|"tertiary"`), `Divider` (`tone="hairline"` for a lighter rule inside a card, unset for a full-width section break), `Link` (React Router `<Link>`, styled). No component library beyond this Foundation set is used on these four pages — no modal/dialog component, no toast, no tooltip component, no chart library, no date picker.

---

## Table of Contents
1. [Daily Brief](#1-daily-brief)
2. [Discovery](#2-discovery)
3. [Portfolio](#3-portfolio)
4. [Investment Case](#4-investment-case)

---

# 1. Daily Brief

Route: `/daily-brief`. File: `frontend/src/routes/DailyBriefPage.tsx` (130 lines — the simplest of the four pages).

## 1.1 Purpose

Answer exactly one question for the investor: **"what changed today that deserves my attention?"** Daily Brief is a pure read-only distribution layer over Investment Case Change Intelligence — it computes nothing itself, ranks nothing by invented importance, and never fabricates activity when nothing changed. If nothing changed, the page says so plainly and shows no entries.

## 1.2 Current Information Hierarchy

```
Daily Brief
├── Page Title ("Daily Brief")
├── Divider
├── Summary Card
│   └── One sentence: loading / error / summary text
└── (if entries exist) Entry List
    ├── Divider
    └── One Card per company, each containing:
        ├── Ticker (or "Unknown company")
        ├── Headline (one line)
        ├── Change Summary (one paragraph per changed dimension)
        ├── Why It Matters (one sentence)
        └── "Open Investment Case" button
```

There is no header/hero beyond the plain page title. There is no visual distinction between the summary card and the entry cards beyond their content — both use the same `Surface tier="primary"`.

## 1.3 Components

| Component | Where | Notes |
|---|---|---|
| Page title (`Heading level={1}`) | Top | `dailyBrief.title` |
| Summary `Surface` card | Below title | Contains one `Text` node whose content depends on load state |
| Entry `Surface` card | One per company, repeated | Contains: `Heading level={2}` (ticker), 1 headline `Text`, N change-summary `Text` lines (split on `\n`), 1 "why it matters" `Text`, 1 `Button variant="tertiary"` |
| Loading indicator | Inside summary card | `Text role="status" aria-live="polite"` reading `common.loading` |
| Error text | Inside summary card | `Text color="secondary"` with the raw error message |

No badges, no status pills, no icons, no tables, no charts anywhere on this page.

## 1.4 Interactions

- **"Open Investment Case" button** (one per entry card): navigates to `/investment-case/{caseId}` with router state `{ origin: "daily-brief" }` (this state is what makes the Investment Case page show a "← Back to Daily Brief" link).
- No other buttons, no expandable sections, no inputs, no hover-revealed content. The page is purely a display + one navigation action per entry.

## 1.5 Data

| Section | Source | Endpoint | ViewModel | Loading | Error | Empty |
|---|---|---|---|---|---|---|
| Summary + Entries | `atlas/analysis_engine/daily_brief.py` (`DailyBrief`) via `atlas/alpha/daily_brief/service.py` | `GET /api/daily-brief` (single call, on mount) | `DailyBriefView { generatedAt, summary, entries: DailyBriefEntryView[] }`; entry = `{ caseId, ticker, headline, changeSummary, whyItMatters, thesisImpact, changes: ChangeFindingView[] }` | `Text role="status"` with `common.loading` | `Text color="secondary"` with the caught error's message (or `common.unknownError`) | Not a distinct UI state — when `entries` is empty, the summary sentence itself says `"No material analytical changes since your previous review."` and the entry list section renders nothing (conditionally not rendered at all) |

Single `useEffect` on mount, `AbortController`-cancelled on unmount. No polling, no refetch trigger, no client-side caching beyond component state.

## 1.6 Business Rules

All rules live in `atlas/analysis_engine/daily_brief.py` (backend, pure), not in the frontend:

1. **Eligibility**: a company appears only if its Change Intelligence is not a "baseline" (i.e. not the very first analysis ever run for that Case) **and** has at least one real `ChangeFinding`. A Case with nothing changed produces no entry — never a placeholder entry.
2. **Headline selection**: a fixed lookup table keyed by change category + direction (e.g. "Growth strengthened.", "New risk identified.", "Valuation became more attractive."). If a company has more than one change, the headline instead reflects the overall thesis impact ("Mixed signals.", "Thesis strengthened.", etc.).
3. **Ordering**: entries are sorted **alphabetically by ticker** (case-insensitive; entries with no ticker sort last). There is explicitly no importance/urgency/priority ranking — the backend module's own docstring states this is a deliberate constraint.
4. **Summary sentence**: `"No material analytical changes..."` (0 entries) / `"1 company has a meaningful analytical change to review."` (1 entry) / `"{n} companies have meaningful analytical changes to review."` (n>1). No other summary phrasing exists.
5. Companies come from the union of current Portfolio holdings and Watchlist entries (`known_cases()`), each mapped to its own Investment Case's Change Intelligence.

## 1.7 Preserve

- The page must remain a pure read-only summary — no editing, no data entry.
- The "no material change" state must remain a first-class, non-alarming, non-empty-looking state — it is correct behavior, not an error.
- The one-sentence summary count and the alphabetical, non-ranked entry order.
- "Open Investment Case" as the only navigation action per entry, preserving `{ origin: "daily-brief" }` router state so the Investment Case page can offer a return link.
- The distinction between headline / change summary / why-it-matters as three separate pieces of text (they map to three different backend fields and should not be merged into one paragraph).

## 1.8 Technical Notes

- Single fetch, single loading/error/loaded state machine (`DailyBriefStatus` union type) — no per-entry loading states.
- `changeSummary` may contain embedded `\n` characters representing multiple change lines within one entry; the current implementation splits on `\n` and renders each as its own `Text` node.
- No pagination — all eligible entries render in one list, unbounded.
- No polling / auto-refresh; the brief is only as fresh as the last page load.

## 1.9 Screenshot Map

```
Daily Brief
Header (page title)
↓
Summary Card
↓
Entry Card (ticker 1)
↓
Entry Card (ticker 2)
↓
...
↓
Entry Card (ticker n)
```

---

# 2. Discovery

Route: `/discovery`. File: `frontend/src/routes/DiscoveryPage.tsx` (374 lines).

## 2.1 Purpose

The conversational entry point into Atlas: a free-text chat with an AI backend (bounded by real portfolio/case tools, never fabricating outcomes), a bounded "review a specific company" shortcut that resolves a ticker against real Portfolio holdings, and an honest placeholder for a not-yet-built "opportunities" capability.

## 2.2 Current Information Hierarchy

```
Discovery
├── Page Title ("Discovery")
├── Divider
├── Primary Prompt Card
│   ├── Heading + "(i)" info toggle button
│   ├── Supporting text
│   ├── (if toggled) Info disclosure body + "learn more" note
│   ├── (if portfolio exists) "Portfolio context available" note
│   ├── Divider (hairline)
│   ├── Conversation transcript (user + Atlas messages, if any)
│   ├── "Sending…" / "unavailable" status text
│   ├── Multi-line text input
│   ├── Submit button
│   └── Row of 5 suggested-prompt buttons
├── Divider
├── Review a Company Card
│   ├── Heading
│   ├── Ticker text input
│   ├── (conditional) "not in portfolio" note + link to Portfolio
│   ├── (conditional) error text
│   └── "Open/Create Case" button
├── Divider
└── Opportunities Card
    ├── Heading
    └── "Not yet available" note
```

## 2.3 Components

| Component | Where | Notes |
|---|---|---|
| Info toggle | Prompt card | `Button variant="tertiary"` showing literal text `"(i)"`, `aria-expanded` reflects open/closed state |
| Conversation transcript | Prompt card | List of `Text` nodes, one per message; `color="secondary"` for Atlas replies, `color="primary"` for the user's own messages — no chat-bubble styling, no avatars |
| Multi-line input | Prompt card | Native `<textarea rows={3}>`, full width |
| Suggested-prompt buttons | Prompt card | 5 `Button variant="tertiary"`, each pre-filled question text (`discovery.suggestions.*`) |
| Ticker input | Review-a-company card | Native `<input>`, plain text, no ticker validation/autocomplete |
| Review/Create button | Review-a-company card | Label changes dynamically between "Open case" and "Create case" depending on whether the entered ticker already has a linked Case |

No tables, no charts, no badges, no icons beyond the literal "(i)" glyph, no dialogs.

## 2.4 Interactions

- **Info toggle**: click toggles a `showInfo` boolean; shows/hides the info disclosure text. No animation.
- **Send question**: typing in the textarea + clicking Submit (or the Enter-key shortcut is **not** wired — only the explicit button) posts the full conversation so far to the backend. Input disabled while a request is in flight (`sendStatus.kind === "sending"`).
- **Suggested-prompt buttons**: clicking one replaces the textarea's current content with that prompt's fixed text — it does **not** submit automatically.
- **Ticker input + Review button**: typing resets any prior error/not-found state. Clicking the button:
  - If the ticker matches an existing Portfolio holding **with** a linked Case → navigates directly to that Case.
  - If it matches a holding **without** a Case yet → creates a Case, links it, then navigates.
  - If the ticker does not match any current holding → shows an inline "not in portfolio" note with a link to `/portfolio`. No new holding is created.
- Row-level `onKeyDown` handling exists for the ticker input? — **no**, only the Ask input in the primary prompt reacts to Enter (`handleAsk`/`submitQuestion` on Enter). The ticker field is button-only.

## 2.5 Data

| Section | Source | Endpoint | ViewModel | Loading | Error | Empty |
|---|---|---|---|---|---|---|
| Portfolio context (used for "review a company" ticker matching) | `atlas/alpha/portfolio` | `GET /api/alpha-portfolio` (on mount) | `PortfolioView { exists, holdings: [{ ticker, caseId }] }` | Not shown to user (silently pending) | Silently sets `portfolioStatus.kind = "error"`; no visible error text on page | N/A |
| Chat reply | `atlas/ai/api/router.py` (Discovery Intelligence v1) | `POST /api/discovery/chat` — body `{ messages: [{role, content}], language }` | Response `{ message, mode: "generated"\|"not_configured"\|"provider_error"\|"tool_call", toolResult }` | `discovery.chat.sending` text shown | `discovery.chat.unavailable` text on network failure (a distinct inline notice, never appended to the transcript as something "Atlas said") | Empty transcript = no messages rendered yet |
| Case creation (ticker review path) | `atlas/core/.../case` | `POST /api/cases` then `POST /api/alpha-portfolio/holdings/{ticker}/case-link` | `{ caseId }` | Button label becomes `common.submitting` | `discovery.reviewCompany.error` inline text | N/A |

## 2.6 Business Rules

1. **No entity recognition.** The "review a company" ticker match is exact, case-insensitive string equality against the investor's own real holdings — never parsed out of free-text conversation.
2. **Tool-call replies are never model-authored text.** When the backend's chat response has `mode: "tool_call"`, the rendered Atlas message is one of four fixed, translated, deterministic sentences chosen by the real `outcome` value (`opened` / `created` / `unresolved` / `failed`) — the frontend cannot display a false "success" unless the backend tool genuinely succeeded.
3. **Degraded-provider modes are shown honestly, not hidden.** `not_configured` and `provider_error` both render as a real (if generic) Atlas transcript message — still a truthful statement, just not model-generated text. A genuine network failure (`unavailable`) is deliberately **not** added to the transcript at all (since Atlas never actually replied) — it's a separate small inline notice.
4. **No opportunities/candidate generator exists.** The Opportunities card is a permanent, honest "not yet available" disclosure, not a stub for content that will silently appear later without this document being updated.
5. Only Portfolio holdings are ever matched by the review-a-company shortcut — Watchlist is explicitly out of scope for this page today.

## 2.7 Preserve

- The three-way mode split (`generated` / `not_configured or provider_error` / `unavailable`) and the rule that only genuine model output can ever appear as an Atlas transcript message.
- The tool-call outcome → fixed sentence mapping — never let a redesign imply the AI is "describing" the outcome in its own words.
- Exact, case-insensitive ticker matching for the review shortcut (no fuzzy matching, no autocomplete that could resolve to the wrong company).
- The "create case if not linked yet" vs. "open existing case" branching and its dynamic button label.
- The honest "not yet available" Opportunities disclosure as a real, permanent UI state — not a loading placeholder.

## 2.8 Technical Notes

- Conversation history is **entirely in-memory** (component state) — refreshing the page loses the transcript. No persistence, no conversation ID.
- The full message history is re-sent on every new question (`sessionSoFar`), not just the new message — the backend has no server-side session state for this page.
- `language` (the investor's active UI language) is sent with every chat request so Atlas replies in the same language.
- No `AbortController` is used for the chat POST itself (unlike the portfolio-context GET), so an in-flight chat request cannot be cancelled by unmounting.

## 2.9 Screenshot Map

```
Discovery
Header (page title)
↓
Primary Prompt Card
  ├─ Prompt heading + info toggle
  ├─ Conversation transcript
  ├─ Text input + submit
  └─ Suggested prompts row
↓
Review a Company Card
↓
Opportunities Card
```

---

# 3. Portfolio

Route: `/portfolio`. File: `frontend/src/routes/PortfolioPage.tsx` (1620 lines — "Portfolio Workspace v3").

## 3.1 Purpose

The investor's single working view of their real portfolio: a compact summary, a short, severity-ranked list of what to work on next (Action Center), a dense per-holding table (weight, Atlas's analytical coverage, investor conviction, evidence, review priority, thesis freshness), and a small set of Atlas-initiated discussion starters. Portfolio is explicitly the **overview** layer — depth (full Business/Valuation/Risk analysis) lives one click away on each holding's own Investment Case page.

## 3.2 Current Information Hierarchy

```
Portfolio
├── Page Title ("Portfolio")
├── "Import Portfolio" link
├── (state-dependent: loading / error / not-established / empty / loaded)
└── (when loaded, has holdings) —
    ├── Portfolio Summary (compact bar: Holdings, Cash, Needs attention, Health)
    ├── Action Center ("Today's Priorities")
    │   ├── 🔴 Highest Priority (0–2 items)
    │   ├── 🟠 High Priority (0–2 items)
    │   └── 🟡 Medium Priority (0–2 items)
    ├── (conditional) Awaiting-reconciliation banner
    ├── (conditional) Replace Allocation form
    ├── Holdings Table (one row per holding, 8 columns)
    │   └── Unallocated % / Concentration level (below table)
    │   └── "Open a new Investment Case" button
    └── Today's Discussions
        ├── Atlas-derived discussion prompts (0–3)
        └── Free-text "Ask" input (placeholder feature)
```

## 3.3 Components

| Component | Where | Notes |
|---|---|---|
| Portfolio Summary bar | Top card | 4 inline stats: Holdings count, Cash %, "Needs attention" count, Health coverage fraction (`n of m holdings have a Case`); conditional 5th line for data-quality warning (unrecognized ticker formats) |
| Action Center card | 2nd card | 3 severity tiers, each a `Heading level={3}` with an emoji (🔴/🟠/🟡) + up to 2 action rows; each row = title, reason text, optional item count, optional CTA button, hairline divider |
| Awaiting-reconciliation banner | Conditional | Plain `Surface` with explanatory text + a "Replace Allocation" button |
| Replace Allocation form | Conditional, toggled | Repeating rows of Ticker / Weight% / Value(optional) text inputs, plus portfolio-level Cash% / Cash value inputs, Save / Cancel buttons |
| Holdings table | 3rd card | HTML `<table>`, horizontally scrollable (`overflowX: auto`) on narrow viewports. Columns: Status (emoji), Ticker, Weight, Analysis Coverage, Conviction, Evidence, Priority, Thesis |
| Holdings table row | Repeating | Entire `<tr>` is a keyboard-operable button (`role="button"`, `tabIndex`, Enter/Space activates) that navigates to the holding's Investment Case. Ticker cell additionally shows: "opening…" while a Case is being created, "updated automatically" tag, "unresolved" tag (Case link broken), inline open-case error, and (only when reconciliation is pending) a Reconcile-toggle button |
| Reconcile inline row | Expandable, one at a time | New-weight input + Update button + error text, rendered as a second `<tr>` spanning all 8 columns |
| Today's Discussions card | 4th card | 0–3 `DiscussionPromptRow`s (text + "Discuss" button + hairline divider), then a free-text Ask input + Ask button + one-time "coming soon" note |

## 3.4 Interactions

- **Holdings table row click / Enter / Space** → `openInvestmentCase(ticker, existingCaseId)`: if the holding already has a linked Case, navigates straight there (`state: { origin: "portfolio" }`); otherwise creates a new Case via `POST /api/cases`, links it to the holding via `POST /api/alpha-portfolio/holdings/{ticker}/case-link`, then navigates. This is a **full route navigation**, not an overlay — leaving Portfolio unmounts the page and discards any expanded-row/scroll/ask-input state.
- **Reconcile toggle** (only visible when a holding is `AWAITING_RECONCILIATION`): expands an inline weight-update form for exactly one holding at a time (opening a second one closes the first). Clicking it calls `event.stopPropagation()` so it never also triggers row navigation. Submitting posts `POST /api/alpha-portfolio/reconcile` with `{ mode: "UPDATE_HOLDING_WEIGHT", ticker, weightPercent }`.
- **"Replace Allocation" button** (in the reconciliation banner) → opens a full replace-allocation form pre-filled with current holdings; Save posts `POST /api/alpha-portfolio/reconcile` with `{ mode: "REPLACE_ALLOCATION", holdings, cashWeightPercent, cashValueAbsolute }`.
- **Action Center row CTA** → same `openInvestmentCase` navigation, scoped to that action's ticker.
- **"Discuss" button** (Today's Discussions) → fills the free-text Ask input with that prompt's exact question text and focuses it; does **not** auto-submit.
- **Ask button / Enter in Ask input** → shows a one-time static "coming soon" note. No backend call, no real conversational engine wired to this input yet.
- **"Open a new Investment Case" button** (below the table) → creates and opens a brand-new, unlinked Case.

## 3.5 Data

Four independent fetches, each with its own loading/error state — a slow/failed one never blocks the others from rendering.

| Section | Source | Endpoint | ViewModel | Loading | Error | Empty |
|---|---|---|---|---|---|---|
| Core holdings state | `atlas/alpha/portfolio` | `GET /api/alpha-portfolio` | `PortfolioView { exists, entryMode, hasAbsoluteValues, holdings[], cashWeightPercent, cashValueAbsolute, totalValue, numberOfHoldings, concentrationLevel, objective, horizon, awaitingReconciliation }` | `common.loading` text | `portfolio.loadError` inline text | Two distinct empty states: "not established yet" (`portfolio.notEstablished` + setup link) vs. "established, zero holdings" (`portfolio.empty.*` + objective/horizon if set) |
| Workflow-completeness summary | `atlas/alpha/portfolio_status/service.py` | `GET /api/alpha-portfolio/status` | `PortfolioStatusView { exists, summary, attentionItems[], reviewQueue[], health }` | Silent (no visible loading text; consuming components just treat it as `null` until loaded) | Silent (`kind: "error"`, sections render as if data absent) | `exists: false` → treated as no data |
| Portfolio-wide analytical findings | `atlas/alpha/portfolio_intelligence/service.py` | `GET /api/alpha-portfolio/intelligence` | `PortfolioIntelligenceView { exists, overview, cashWeightPercent, cashValueAbsolute, keyFindings[], considerItems[], riskSignals[], missingEvidence[], portfolioFit }` | Silent | Silent | `exists: false` → treated as no data |
| Per-holding canonical analysis projection | `atlas/alpha/portfolio_cockpit/service.py` | `GET /api/alpha-portfolio/cockpit` | `PortfolioCockpitView { exists, holdings: [{ ticker, caseId, weightPercent, valueAbsolute, reconciliationStatus, conviction, analysisCoverage, valuation, business, riskProjection, riskFindings, confidence, isThesisStale, attention }], unresolvedHoldings[], summary, convictionDistribution[], analysisCoverageDistribution[], valuationDistribution[], priorityReviewCount }` | Silent | Silent | Holdings table renders `—` for every Cockpit-sourced cell when a row has no matching Cockpit holding |

**Action Center and Today's Discussions compute nothing new from the network** — both are pure client-side derivations (`derivePortfolioActions.ts`, `deriveDiscussionPrompts.ts`) over the already-fetched `PortfolioStatusView`/`PortfolioIntelligenceView`, capped and deduplicated for display. No additional backend call.

## 3.6 Business Rules

1. **Analysis Coverage and Conviction are deliberately two separate signals, never merged.** Conviction (`insufficient_evidence`/`low`/`moderate`/`high`/`very_high`) answers "has the investor built and evidenced a real conviction," and is gated on investor-recorded Observation/Decision evidence. Analysis Coverage (`no_coverage`/`partial_coverage`/`substantial_coverage`) answers "how much does Atlas actually know about this company" and is derived purely from company financial data — it reads no investor evidence at all. A holding can honestly show `substantial` Analysis Coverage and `insufficient_evidence` Conviction at the same time.
2. **Action Center caps at 2 items per severity tier** (not one flat cap across all tiers), so a portfolio with many High-priority items can never crowd out Medium-priority ones entirely.
3. **"Priority" column is an explicit placeholder, not a recommendation.** It shows `HoldingAttention.priority` (none/standard/evidence/priority review) because no real directional-recommendation capability (Buy/Hold/Reduce/Exit) exists yet in the backend — the column is documented in code as temporary.
4. **"Thesis" column shows staleness, not a timestamp**, because no per-holding "last updated" timestamp is exposed by any endpoint this page reads.
5. **Unallocated % is computed, never fabricated to 100%.** `100 − Σ(holding weights) − cash%`; only shown when it exceeds a small tolerance.
6. **At most one inline reconciliation form is expanded at a time.**
7. **Row navigation is real routing, not a modal/overlay** — leaving and returning to Portfolio resets scroll position and any expanded state (documented in code as a known, deliberate, unaddressed limitation).
8. Every enum value shown in the table (conviction level, analysis coverage level, valuation status, review priority) is a closed, backend-defined vocabulary — the frontend only translates it, never invents a new category.

## 3.7 Preserve

- The four-endpoint, independently-loading data architecture — no section should be made to block on another section's fetch.
- The Analysis Coverage vs. Conviction vs. Evidence three-column distinction — these must remain three visibly separate signals, never collapsed into one "score."
- Action Center's per-tier cap and severity ordering (Highest → High → Medium).
- The full-route (not overlay) navigation behavior from a holding row to its Investment Case, and the `state: { origin: "portfolio" }` passed along with it.
- The single-inline-reconciliation-at-a-time behavior.
- The honest "Priority is a placeholder" and "Thesis shows staleness, not a date" semantics — a redesign must not silently start implying these columns mean something the backend doesn't provide.
- "Unallocated %" and "Concentration" as computed facts shown next to the holdings they describe, never presented as user-editable fields.
- The distinct "not established" vs. "established but empty" empty states.

## 3.8 Technical Notes

- All four fetches use `AbortController` cleanup on unmount.
- The Holdings table is a plain HTML `<table>` with inline `CSSProperties` (no CSS framework/grid library) inside an `overflowX: auto` wrapper for small viewports.
- `derivePortfolioActions.ts` and `deriveDiscussionPrompts.ts` are pure TypeScript modules with no side effects — safe to test/reuse without touching the network.
- `MAX_ACTIONS_PER_SEVERITY = 2` and the un-ranked ticker-alphabetical fallback are literal constants in `PortfolioPage.tsx`.
- Case creation reuses the exact same `POST /api/cases` → `POST /api/alpha-portfolio/holdings/{ticker}/case-link` two-step flow used on the Investment Case and Discovery pages — not a separate code path.

## 3.9 Screenshot Map

```
Portfolio
Header (page title + Import link)
↓
Portfolio Summary
↓
Action Center ("Today's Priorities")
  ├─ 🔴 Highest
  ├─ 🟠 High
  └─ 🟡 Medium
↓
(conditional) Awaiting-Reconciliation Banner
↓
(conditional) Replace Allocation Form
↓
Holdings Table
  └─ Unallocated % / Concentration line
↓
Today's Discussions
  ├─ Discussion prompts
  └─ Ask input
```

---

# 4. Investment Case

Route: `/investment-case` (new, unlinked) or `/investment-case/:caseId`. File: `frontend/src/routes/InvestmentCasePage.tsx` (5144 lines — by far the largest and deepest page in the app; "Investment Case Workspace v2").

## 4.1 Purpose

The full analytical and decision record for one company/security: Atlas's own synthesized view (thesis, strengths, risks, growth, valuation, open questions), the complete underlying analysis (Business/Valuation/Risk/Evidence, each traceable to supporting/contradicting facts), automatically-ingested company financial data, the investor's own decision history and outcomes, and the primary place an investor records a real portfolio action (Add/Trim/Remove/Hold) and, later, reports the actual executed trade.

## 4.2 Current Information Hierarchy

```
Investment Case
├── Header
│   ├── Back link (to Portfolio / Discovery / Daily Brief / History — origin-dependent)
│   ├── Ticker (or "Untitled") as page title
│   ├── "In portfolio · current allocation: X%" (if linked)
│   ├── Status ("Fresh" / "Needs Review" / etc. — deriveCaseStatus)
│   ├── "Not linked to a portfolio holding" note (if applicable)
│   └── Case ID (secondary/technical)
├── Executive Summary
│   ├── Atlas Assessment (1–3 sentences)
│   ├── Current Priority
│   ├── Portfolio Impact (weight / largest-position-or-concentration / cash)
│   ├── (conditional) Outstanding Issues (up to 3, + "N more")
│   └── Discuss this Case (pre-written question + free-text Ask)
├── Divider
├── Canonical Analysis (all always-rendered together)
│   ├── Company Overview (identity + Financials table + Market Snapshot)
│   ├── Atlas View (Thesis / Strengths / Risks / Growth / Valuation Context / Open Questions)
│   ├── What Changed (only if Change Intelligence capability is available)
│   ├── Business (Portfolio Context, then Growth/Capital Allocation, then remaining categories)
│   ├── Valuation (FCF Yield + scenario placeholder note)
│   ├── Risk (four-category vector: Business/Financial/Valuation/Thesis Risk)
│   ├── Evidence (Current Thesis, Conviction, Confidence, Evidence Quality, Observations, Missing Evidence, Open Questions, Recommendation)
│   ├── Decision History
│   └── Outcomes
├── Divider
├── Last Activity (most recent Decision / Outcome / Trade + reconciliation status)
├── Divider
├── Decision Timeline (full chronological Decision/Outcome/Trade list + current status)
├── Divider
├── Outstanding Work (deterministic checklist: missing outcome / missing trade)
├── Divider
├── More Details (collapsed <details> disclosure)
│   └── Observations list, each expandable into: Evidence / Knowledge References / Reasoning Traces / Judgments / Decisions / Outcomes forms
├── Divider
└── Actions ("Add to Position" / "Trim" / "Remove" / "Leave as is")
    └── (per action) Reason + Confidence form → Decision recorded → "Report Transaction" → Outcome statement/note + optional trade-execution sub-form (security, type, quantity, price, fees, executed-at)
```

## 4.3 Components

| Component | Where | Notes |
|---|---|---|
| Status line | Header | One translated word derived from workflow/thesis/evidence gaps (`deriveCaseStatus`) |
| Executive Summary card | Top | Five labeled sub-blocks (`data-trace-source` attributes: `assessment`, `priority`, `portfolioImpact`, `outstandingIssues`, `discuss`), each a `Stack` of `Text` lines separated by hairline dividers |
| Company Overview card | Canonical section 1 | Identity fields (name/exchange/sector/industry/country/fiscal-year-end/description), then **Financials table**, then Market Snapshot |
| **Financials table** | Inside Company Overview | Dense analyst-style `<table>`: one row per financial metric (Revenue, Operating Income, Net Income, EPS, FCF, Capex, Buybacks, Dividends, Cash, Total Debt, Shares Outstanding), one column per fiscal period, **newest period first (left to right)**. Missing values render as `—`, never `0`. Horizontally scrollable. |
| Atlas View card | Canonical section 2 | 6 labeled subsections (Thesis/Strengths/Risks/Growth/Valuation Context/Open Questions), each a short synthesized read of the fuller analysis below it |
| What Changed card | Canonical section 3 | Conditionally rendered entirely (`null` if capability unavailable); otherwise one of: baseline note / "no material change" / a list of directional change lines (with ↑/↓/→ symbols) + a thesis-impact closing line |
| Business card | Canonical section 4 | Portfolio Context subsection (weight/largest-position/concentration/cash), then Growth+Capital Allocation highlighted, then remaining categories; each finding row: category, status, supporting/contradicting/missing evidence lines |
| Valuation card | Canonical section 5 | FCF Yield status + current yield %, supporting facts, missing evidence; separate "scenario valuation" note (explicitly a placeholder — no scenario capability exists) |
| Risk card | Canonical section 6 | Four independent category rows (no aggregate score) |
| Evidence card | Canonical section 7 | The densest single card: Current Thesis (investor-authored only, never AI-fabricated), Conviction (+ reasons list), Confidence (+ explanation), Evidence Quality (coverage level, supporting/challenging counts), Observations list, Missing Evidence (open questions filtered to evidence-gap kinds), remaining Open Questions, and finally Recommendation (always shown as "withheld" + a real reason — no directional recommendation exists yet) |
| Decision History / Outcomes cards | Canonical sections 8–9 | Simple reverse-chronological lists: type/reason/date, statement/date |
| Last Activity card | Below canonical sections | Up to 3 lines (last decision, last outcome, last trade), each with a relative-time phrase, plus reconciliation status |
| Decision Timeline card | Below Last Activity | Full oldest-first list of every Decision/Outcome/Trade event for this Case, ending in a current-status line |
| Outstanding Work card | Below Timeline | 0–2 plain-text checklist lines (missing outcome / missing trade); reconciliation is intentionally excluded here since Last Activity already shows it |
| **More Details** disclosure | Below Outstanding Work | Native `<details>`/`<summary>` (collapsed by default) wrapping the entire legacy granular Core-domain workflow — see 4.4 |
| Actions card | Bottom | Four primary/tertiary buttons (Add/Trim/Remove/Leave as is) → dynamic form → success state → optional "Report Transaction" sub-flow |

## 4.4 Interactions

**Executive Summary**
- "Discuss" button fills the Ask input with a pre-derived question and focuses it; Ask button/Enter shows a one-time static "coming soon" note (identical placeholder pattern to Portfolio's Today's Discussions — no real backend call).

**Actions (primary decision-recording flow)**
- Clicking **Add / Trim / Remove / Leave as is** opens a reason (`<textarea>`) + confidence (`<input type="number" min=0 max=100>`) form for that specific action. Only one action form is open at a time (`pendingAction` state).
- Submitting posts a real Decision (`POST /api/decisions`, `decisionType` mapped from the action: Add→BUY-family, Trim/Remove→SELL, Leave as is→HOLD). Trim and Remove both record a SELL-type Decision; only Leave-as-is skips the transaction-report step entirely (since nothing occurred).
- On success: shows "Decision recorded" confirmation. For Add/Trim/Remove (not Leave-as-is), a **"Report Transaction"** button appears, opening an Outcome form: statement (`<textarea>`), note (`<textarea>`), and an "external trade" checkbox.
- Checking "external trade" reveals a **trade-execution sub-form**: Security (`<input>`), Type (`<select>`: Buy/Add/Sell/Exit), Quantity (`<input>`), Execution Price (`<input>`), Fees (`<input>`), Executed-At (`<input type="datetime-local">`). Submitting this posts `POST /api/outcomes` then, for the trade fields, `POST /api/alpha-portfolio/apply-trade`.

**More Details (collapsed legacy workflow)**
- Expanding the `<details>` reveals the full Observation list (`GET /api/observations`). Each Observation row can independently expand forms to: attach Evidence (`POST /api/evidence`), attach a Knowledge Reference (`POST /api/knowledge-references`), attach a Reasoning Trace (`POST /api/reasoning-traces`), record a Judgment (`POST /api/judgments`), record a Decision (`POST /api/decisions`), and (per resulting Decision) record an Outcome (`POST /api/outcomes`) — the same granular, low-level record-keeping primitives that predate the Actions card above. This is the original, full-detail workflow; the Actions card is the newer, guided shortcut over the same underlying Decision/Outcome objects.

**Navigation**
- Back link at top returns to whichever page opened this Case (`origin` router state: `portfolio` / `discovery` / `daily-brief` / `history` / none → defaults to a generic label).
- No section-to-section in-page navigation (no sticky table of contents, no anchor jump links) — the page is one long scroll.

## 4.5 Data

The page makes ~13 independent, parallel fetches on mount (each its own `useEffect` + `AbortController`), so a single slow/failed one never blocks the rest of the page:

| Section(s) | Endpoint | ViewModel (top-level shape) |
|---|---|---|
| Case identity | `GET /api/cases/{caseId}` | `{ caseId, recordedAt }` (Case itself carries no business identity — ticker comes from the Portfolio link) |
| Canonical Analysis (Company Overview, Atlas View, What Changed, Business, Valuation, Risk, Evidence, Decision/Outcome history) | `GET /api/cases/{caseId}/analysis` | `InvestmentCaseAnalysisView` — the single largest response on the page: `holdingContext, currentThesis, isThesisStale, confidence, conviction, businessAnalysis, valuation, risk, evidenceQuality, openQuestions, recommendation, decisionHistory, observationHistory, outcomeHistory, tradeLog, companyProfile, financialHistory, marketSnapshot, strengths, risks, growthAnalysis, valuationContext, atlasThesis, keyOpenQuestions, changeIntelligenceAvailable, isBaselineCase, latestChanges, changeSummary, thesisChange, previousAnalysisAt, currentAnalysisAt, generatedAt` |
| Observations (More Details) | `GET /api/observations` | List of Observation records |
| Portfolio linkage (header, Last Activity, Timeline, Business's Portfolio Context, Executive Summary) | `GET /api/alpha-portfolio` | Same `PortfolioView` as the Portfolio page — used here to find `linkedHolding` and compute largest-position/concentration/cash facts |
| Trade log (Last Activity, Timeline) | `GET /api/alpha-portfolio/trade-log` | List of applied trades |
| Evidence / Knowledge References / Reasoning Traces / Judgments / Decisions / Outcomes (all Observations, all Cases) | `GET /api/evidence`, `GET /api/knowledge-references`, `GET /api/reasoning-traces`, `GET /api/judgments`, `GET /api/decisions`, `GET /api/outcomes` | Full unfiltered lists, filtered client-side to this Case/these Observations |

**Loading/error/empty pattern**: every section independently checks its own fetch's status; the page never shows one global spinner. Empty states are explicit, honest text (e.g. `investmentCase.analysis.companyOverview.empty`, `investmentCase.timeline.empty`, `investmentCase.outstandingWork.none`) rather than a blank card. Financial values that are genuinely unknown render as the literal `—` character — **never as `0` or a blank cell**, since a zero would visually imply the value is known to be zero.

## 4.6 Business Rules

1. **Financials table is newest-period-first**, matching how the API itself returns it (API returns oldest-first; the table reverses it once, client-side) — "how an analyst reads a spreadsheet."
2. **A missing financial value is always `—`, never `0` or blank.**
3. **Conviction, Confidence, and Analysis Coverage (surfaced on Portfolio) are three distinct, never-merged concepts**, each rendered with its own heading and its own explanation text on this page (Conviction requires both real analysis *and* real investor evidence; Confidence is "how trustworthy is Atlas's own analysis"; see Portfolio §3.6 rule 1 for Analysis Coverage).
4. **Recommendation is always shown as "withheld," with a real, specific reason** — the backend currently has no directional-recommendation capability (Buy/Hold/Reduce/Exit) that produces anything else; the UI never infers a recommendation from Valuation/Conviction/Risk on its own.
5. **Current Thesis is investor-authored only.** Atlas never fabricates a thesis narrative in this slot — it shows the investor's own most recent Decision reason and/or Observation statement, or an honest "none recorded" state.
6. **The four Risk categories are shown independently, with no aggregate/composite score.**
7. **Trim and Remove both record a SELL-type Decision**; only their reason/framing differs. Leave-as-is records a HOLD Decision and never opens the outcome/trade-report flow, since by definition no transaction occurred.
8. **What Changed renders nothing at all** (not even an empty-state card) when the underlying Change Intelligence capability isn't available for this Case — a deliberate "don't show a section that can't mean anything yet" choice, distinct from the empty-but-present-card pattern used elsewhere.
9. **Business analysis highlights Growth and Capital Allocation** ahead of the other four business categories, because those are the only two currently evaluated with real analysis; the other four still render (each independently correct/incomplete), never hidden.
10. Scenario-based valuation is explicitly labeled as unavailable — the FCF Yield method is the only real valuation method currently computed.

## 4.7 Preserve

- The independent-fetch, independent-failure-state architecture across all ~13 endpoints — no section should become blocking for another.
- The strict separation between Conviction / Confidence / Analysis Coverage / Evidence Quality as four distinct concepts with their own headings and explanations — a redesign must not visually collapse these into one "score" or "badge."
- The Financials table's newest-first column order and the `—` missing-value convention.
- The Actions flow's exact sequence: pick an action → reason+confidence form → Decision recorded → (unless Leave-as-is) optional "Report Transaction" → Outcome form → optional trade-execution sub-form. This sequence must not be compressed into fewer steps that could let a Decision be recorded without its own reason, or a trade be reported without a corresponding Decision.
- "Trim"/"Remove" both mapping to a SELL-type Decision, and "Leave as is" mapping to HOLD with no transaction-report step.
- The collapsed-by-default "More Details" disclosure preserving full access to the granular legacy workflow (Observation → Evidence/Knowledge Reference/Reasoning Trace/Judgment/Decision/Outcome) without deleting or hiding it permanently — it must remain reachable, even if visually de-emphasized.
- The honest "Recommendation: withheld, because {reason}" statement — never replace this with an inferred directional call.
- "What Changed" rendering nothing when unavailable (vs. an empty-state card) as a distinct, intentional pattern.
- Origin-aware back navigation (`origin` router state) across Portfolio / Discovery / Daily Brief / History.

## 4.8 Technical Notes

- This is a single 5144-line file with no internal route-splitting — all sections are functions within the same module, composed in one `InvestmentCasePage()` return tree plus one large `InvestmentCaseCanonicalSections()` sub-tree.
- Form state for the legacy "More Details" workflow is keyed **per Observation ID** (e.g. `evidenceForm[observation.observationId]`) — every Observation row has its own independent set of pending form inputs; opening one does not affect another's.
- Form state for the top-level Actions card is keyed by a single `CASE_LEVEL_DECISION_KEY` constant (only one Add/Trim/Remove/Leave-as-is flow can be in progress at a time) and, separately, per-`reportDecisionId` for the outcome/trade sub-form.
- `data-trace-source` attributes on Executive Summary sub-blocks (`assessment`, `priority`, `portfolioImpact`, `outstandingIssues`, `discuss`) are present in the DOM — likely used for analytics/debugging; a redesign should confirm whether these need to be preserved on the new markup.
- Several derivation helpers are imported from shared modules also used by Portfolio/History/Dashboard (`deriveActivity`, `deriveOutstandingWork`, `deriveCaseStatus`, `deriveAssessmentPoints`, `deriveCurrentPriority`, `deriveOutstandingIssues`, `deriveCaseDiscussionKind`) — these are pure, backend-data-only functions, not new computation introduced by this page.
- The Financials table and Company Overview section were the two areas most recently extended (added operating income/net income/EPS/cash/total debt/shares outstanding/market cap/currency/fiscal-year-end) — the underlying data model here is actively growing as company-data coverage improves; a redesign should leave room for additional financial metric rows without a fixed row count.

## 4.9 Screenshot Map

```
Investment Case
Header (back link, ticker, status, case id)
↓
Executive Summary
  ├─ Atlas Assessment
  ├─ Current Priority
  ├─ Portfolio Impact
  ├─ Outstanding Issues
  └─ Discuss this Case
↓
Company Overview
  ├─ Identity
  ├─ Financials Table
  └─ Market Snapshot
↓
Atlas View
  ├─ Thesis
  ├─ Strengths
  ├─ Risks
  ├─ Growth
  ├─ Valuation Context
  └─ Open Questions
↓
What Changed  (conditional)
↓
Business
  ├─ Portfolio Context
  ├─ Growth / Capital Allocation
  └─ Other Categories
↓
Valuation
↓
Risk
↓
Evidence
  ├─ Current Thesis
  ├─ Conviction
  ├─ Confidence
  ├─ Evidence Quality
  ├─ Observations
  ├─ Missing Evidence
  ├─ Open Questions
  └─ Recommendation
↓
Decision History
↓
Outcomes
↓
Last Activity
↓
Decision Timeline
↓
Outstanding Work
↓
More Details (collapsed)
  └─ Observations → Evidence / Knowledge References / Reasoning Traces / Judgments / Decisions / Outcomes
↓
Actions
  ├─ Add / Trim / Remove / Leave as is
  ├─ Reason + Confidence form
  ├─ Report Transaction
  └─ Outcome + Trade-execution form
```

---

## Cross-Page Notes (apply to all four pages)

- **No design system tokens are documented here** — colors, spacing scale, and typography live in `frontend/src/foundation` and its CSS custom properties (`--space-*`, `--color-*`, `--type-*`), consumed by every component listed above. A designer working from this document should pair it with a direct look at that token set, not infer visual values from this document.
- **Every enum-typed field described in this document is a closed backend vocabulary** — a redesign may change how a value is *displayed* (color, icon, position) but must not invent new values or silently drop existing ones, since the frontend's translation maps (`*_KEY` lookup tables in each page) are exhaustive and would need a matching backend change to support anything new.
- **All four pages share the same "honest empty/loading/error state per section" discipline** — no page ever shows a fabricated placeholder value while data is loading or missing; a redesign should preserve a distinct, calm empty-state treatment per section, not a generic global spinner or skeleton that implies "content is coming" when in fact none exists.
- **None of these four pages currently have a working real-time chat/recommendation engine.** The "Ask"/"Discuss" inputs on Portfolio and Investment Case, and the free-text chat on Discovery, are three separate, independently-implemented surfaces at three different levels of completeness (Discovery's is a real, working chat backend; Portfolio's and Investment Case's are UI-only placeholders that show a static "coming soon" note). A redesign should not assume these three are the same component today.

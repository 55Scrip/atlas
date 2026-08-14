# Atlas Alpha — Workspace System Migration Review

**Type:** Architecture and migration planning review. No implementation code was written or changed as part of this document.

**Status:** Sections 1–12 are approved. Section 13 (Investment Case Action Flow UX) is a **new proposal awaiting approval** — per explicit instruction, it must not be implemented until confirmed. Implementation of the rest of the migration is authorized to begin only once Section 13 is also approved.

**Inputs reviewed:** the current Atlas Alpha frontend (`DailyBriefPage.tsx`, `DiscoveryPage.tsx`, `PortfolioPage.tsx`, `InvestmentCasePage.tsx`) and its backing services/endpoints, cross-referenced directly against the code (not from memory) during the preceding documentation pass; eight supplied Figma screenshots covering the new Discovery, Daily Brief, History, Portfolio, and Investment Case designs.

**How to read this document.** Every claim about "the current implementation" below is grounded in code I read directly (file and endpoint names are given so they can be re-verified). Every claim about "the Figma design" is grounded in what is visible in the eight supplied screenshots — nothing beyond what those screenshots show is assumed. Section 11 is the load-bearing section of this review: several of the richest elements in the new designs correspond to backend capabilities that do not exist today. As of this revision, the largest of those gaps (§11.1) has been resolved by a finalized product decision — see the Decision Log below.

---

## Decision Log (this revision)

Four product decisions were made in response to the first version of this review. Each is reflected throughout the document below; this log exists only as a single at-a-glance summary.

| # | Decision | Status | Where reflected |
|---|---|---|---|
| 1 | Atlas will provide directional guidance, but only as **evidence-support statements** ("Current evidence supports increasing exposure"), never imperative commands ("Buy" / "Add" / "Trim" / "Sell"). This is a new, named capability: the **Decision Support Engine**. | **Finalized.** Ready to be scoped as a real build sprint. | §5, §8, §11.1, §12 |
| 2 | "Ask Atlas" is deprecated everywhere. Replace with the persistent, cross-workspace **Atlas Companion**. | **Finalized** (confirms and sharpens the original recommendation). | §6, §11.5, §12 |
| 3 | The Atlas View scorecard/dot visuals are presentation only. No parallel scoring/domain model may be introduced to support them — every dot must derive from an already-existing categorical assessment. | **Finalized.** | §8, §11.1 |
| 4 | The Investment Case Action Flow (decision recording) needs a UX proposal that fits the new information hierarchy. | **Proposal below (§13), not yet approved — do not implement.** | §13 |

---

## Executive Summary

The new designs are a genuine, well-considered redesign of the **presentation layer** — denser tables, a scorecard-style Atlas View, a richer Daily Brief narrative, a much deeper History page. Structurally, most of this can sit on top of the existing backend with no data-model change: Portfolio's Action Center, Holdings table, and per-holding Conviction/Risk data all have a real, already-shipped backend source.

But a meaningful minority of what the screenshots show is not a presentation change — it is new backend capability that does not exist in this codebase today: **scenario-based (Bull/Base/Bear) valuation with fair value and margin of safety**, **an Opportunities/candidate-generation engine**, **qualitative Business Analysis narrative** (competitive position, moat, management — categories the backend's own doctrine currently refuses to fabricate), **a market/macro context feed**, **an earnings/economic events calendar**, and **a decision-lesson / behavioral-pattern-learning engine** on History. None of these can be "migrated" — they must be built as their own scoped sprints (§10, §12).

The largest of the original open questions — whether Atlas should issue directional guidance at all, and if so how — is now **resolved** (Decision Log #1): Atlas will state what current evidence supports, in plain evidence-support language, never as an imperative command. This is a real, buildable capability (the **Decision Support Engine**, §11.1) built the same way every other categorical assessment in this codebase is built: a small, pure, deterministic function over signals that already exist (Conviction, Analysis Coverage, Risk, current holding status) — not a new scoring model, and not the numeric-implying "Action pill" the original screenshots showed. The categorical-enum-never-a-numeric-score doctrine (Conviction, Risk, Business status) is preserved, not overridden, by this decision.

The recommended sequencing (§10) is therefore: migrate the presentation layer for everything that has a real backend source first (this is the large majority of the visible surface area and delivers the most visible progress fastest), and treat every capability in §11 as its own, separately-scoped, separately-approved sprint — never bundled silently into "implement the Figma design."

---

## 1. Existing components/data that should be preserved

These map cleanly from current backend responses to what the Figma designs show, with no new capability required — only new presentation:

- **Portfolio Action Center → Priority banners.** Screenshot 6's colored-dot priority list ("Review META — Decision has no reported outcome," "Complete evidence for ABB — Missing evidence," "Review portfolio allocation — 22.07% unallocated," "View all 9") maps almost one-to-one onto the current `derivePortfolioActions.ts` output (`atlas/alpha/portfolio_status`, `atlas/alpha/portfolio_intelligence`). This is the cleanest, lowest-risk migration target in the whole set of designs.
- **Portfolio header stats.** Holdings count, Cash, Unallocated % all come directly from the existing `GET /api/alpha-portfolio` / `GET /api/alpha-portfolio/status` responses.
- **Holdings table core columns.** Ticker, Weight, Conviction, Risk (as a category, not a score) are all real, already-shipped `PortfolioCockpitView` fields (`atlas/alpha/portfolio_cockpit`).
- **Conviction as a categorical badge** ("High"/"Medium"/"Low"/"Insufficient evidence") — real, already-shipped, deliberately non-numeric (`atlas/analysis_engine/conviction.py`).
- **Financials table.** The new design's `Metric | Period | Period | YoY Change` layout is a genuine, compatible re-presentation of the current `FinancialsTable` (`InvestmentCasePage.tsx`), which already carries every metric shown (Revenue, Operating Income, Net Income, EPS, FCF, Capex, Share Buybacks, Dividends) plus several the new design doesn't show yet (Cash, Total Debt, Shares Outstanding). YoY Change is a simple derived percentage the frontend can compute from two adjacent already-real columns — no backend change needed for that part.
- **Company Overview identity fields that already exist**: Exchange, Sector/Industry, Country, Fiscal Year End, Description (`CompanyProfileView`, Company Data Foundation v1).
- **Current FCF Yield valuation** ("Slightly Cheap" / "Fairly Valued" / etc.) — real, already-shipped (`atlas/analysis_engine/valuation`).
- **Executive Summary structure** (assessment bullets → current priority → discuss prompt) — real, already-shipped derivation logic (`deriveAssessmentPoints`, `deriveCurrentPriority`, `deriveCaseDiscussionKind`).
- **Decision History / Outcomes / Last Activity / Timeline / Outstanding Work** as content — all real, already-shipped (`deriveActivity.ts`, `deriveOutstandingWork.ts`), even though the new design appears to present them as tabs rather than stacked cards (a layout change, not a data change — see §3/§4).
- **Watchlist as a list of tickers with linked Cases** — real, already-shipped (`atlas/alpha/watchlist`), though its per-row analytical richness in the new design (Conviction/Valuation/Risk/Catalyst) is not yet computed for Watchlist entries today — see §11.3.
- **Daily Brief's underlying change-detection engine** (`atlas/analysis_engine/daily_brief.py`, `investment_case_change.py`) — the *mechanism* that decides what counts as a meaningful change is real and should be reused as-is for the new design's "Portfolio Changes" and "Watchlist Updates" sections; only the presentation and the surrounding narrative are new.
- **The "record a real portfolio decision" flow** (Add/Trim/Remove/Leave-as-is → reason+confidence → Decision → Outcome → optional trade execution). This is the single most business-critical piece of existing functionality on the entire site and is not clearly visible in any supplied screenshot — see §9 (Potential Regressions) and §12 (Recommendations) for why this needs an explicit design answer before migration, not an assumption.

## 2. Existing components that should become shared Foundation components

Several patterns are currently implemented ad hoc, once per page, and should be promoted to `frontend/src/foundation` (or a new shared module) before the migration, so the new workspace layouts consume one implementation rather than four near-duplicates:

- **Status/enum badge rendering.** Today, Conviction/Risk/Valuation/Analysis Coverage/Review Priority are each rendered as plain colored `Text`, with a separate `*_KEY` translation lookup table per page (`PortfolioPage.tsx`, `InvestmentCasePage.tsx` each define their own). The new designs consistently render these as colored pill/badge components (e.g. "High" in a dark badge, "Attractive" in green text, risk level as a colored word). A single `<StatusBadge kind="conviction|risk|valuation|analysisCoverage" value={...} />` component, backed by one shared enum→color→translation mapping, replaces at least 6 duplicated lookup tables across the two files and gives the designer one place to control every badge's visual treatment.
- **The "action" pill** (HOLD/ADD/REVIEW/TRIM/WATCH in the new Holdings table) doesn't exist today in this form — the closest existing analog is the plain-text `HoldingAttention.priority` column. This should become a shared component *once its real data source is settled* (see §11.1 — this cannot be built as a true recommendation engine output yet).
- **The dense financial data table** (`FinancialsTable`, `InvestmentCasePage.tsx`) is already a good, reusable shape (metric rows × period columns) and should be extracted into Foundation as-is, parameterized by row set — it is currently defined inline in one 5000-line page file.
- **Discussion/Ask input pattern.** Three near-identical implementations exist today (Discovery's chat input, Portfolio's "Ask" placeholder, Investment Case's "Discuss"/"Ask" placeholder) — under the new Atlas Companion architecture (see §11.5) these three should collapse into **one** shared component, not be promoted as three separate Foundation components.
- **Empty/loading/error state presentation.** Every one of the four pages implements its own inline loading/error text per section rather than a shared `<AsyncSection status={...}>` wrapper. This is low-risk, high-value to extract before the redesign, since the new layouts introduce many more small data-driven blocks (per-holding scorecard dots, per-event calendar rows) that will otherwise each reinvent this pattern a fifth, sixth, seventh time.
- **The multi-column "dot rating" widget** shown in the new Investment Case Atlas View (Business Strength, Growth Outlook, etc., each shown as 5 dots with N filled) does not exist today in any form — see §11.1 for why this cannot simply be "extracted," since there is currently no numeric input to drive it.

## 3. Existing layouts that can remain

- **Portfolio's four-independent-fetch data architecture** (`GET /api/alpha-portfolio`, `.../status`, `.../intelligence`, `.../cockpit`, each with its own loading/error state) should remain exactly as-is under the new visual layout. It is the correct reason the current page never fully blocks on a single slow endpoint, and nothing in the new designs implies this should change.
- **Investment Case's independent-fetch pattern** (~13 parallel calls) should likewise remain the data layer under whatever new visual container replaces the current one-long-scroll page.
- **Daily Brief's single-endpoint, single-response model** is compatible with the new richer narrative — the new design needs more *fields* in the response (see §11.2), not a different fetch architecture.
- **Case creation / linking flow** (`POST /api/cases` → `POST /api/alpha-portfolio/holdings/{ticker}/case-link`), reused identically across Portfolio, Discovery, and Investment Case today, should remain the single implementation and simply be called from whatever new "Add to Watchlist" / "Create Investment Case" entry points the new design introduces (screenshot 1's "Create Investment Case →", screenshot 7's "+ Add to Watchlist").

## 4. Existing layouts that should be replaced

- **Investment Case's single, ~5000-line, one-long-scroll stacked-card layout.** The new design's greyed-out row of labels at the bottom of screenshot 8 ("Decision History · Timeline · Last Activity · Outstanding Work · Outcomes · More Details") strongly implies these become a **tabbed or collapsible secondary navigation**, not always-rendered stacked cards. This is the single largest layout change in the whole migration and should be scoped as its own workstream (§10).
- **Portfolio's Holdings table column set.** Today: Status / Ticker / Weight / Analysis Coverage / Conviction / Evidence / Priority / Thesis. New design: Ticker / Weight / Conviction / Fit / Exp. Return / Upside / Downside / Risk / Action. This is not a pure re-skin — three of today's columns (Analysis Coverage, Evidence, Thesis-freshness) disappear and five new ones appear, two of which (Exp. Return, Upside/Downside) require data the backend does not compute today (see §11.1). This needs a deliberate decision, not an automatic 1:1 swap.
- **Today's Discussions (Portfolio) / Discuss this Case (Investment Case) as separate, page-local "Ask" boxes.** Per the explicit instruction in this brief, both should be replaced by the new Atlas Companion, not carried forward as separate implementations (§11.5).
- **Discovery's plain free-text-first layout.** The new design reframes Discovery primarily as an Opportunities/Watchlist dashboard with chat-style research prompts as a secondary element, rather than today's chat-first layout with a small "review a company" utility below it. This is a real information-architecture inversion, not a visual refresh.
- **History's flat activity-timeline-first layout** becomes, in the new design, a narrative-first page with Decision Reviews, Learning Patterns, and Strategy Evolution ahead of the Recent Activity list that is closest to today's actual content.

## 5. Existing business logic that should remain untouched

These rules are backend doctrine, not presentation, and the migration must not alter them regardless of how the new UI chooses to visualize their output:

- **Conviction requires both real analysis and real investor-recorded evidence** — it is not a function of company data alone (`atlas/analysis_engine/conviction.py`). Do not let a "Conviction: High" badge in the new UI silently start meaning something the backend doesn't actually compute.
- **Analysis Coverage and Conviction are two deliberately separate signals** (`atlas/analysis_engine/analysis_coverage.py`), added specifically to stop the Portfolio UI from implying Atlas "knows nothing" about a well-covered company just because the investor hasn't logged evidence yet. If the new Holdings table drops the Analysis Coverage column (as the screenshots suggest), the underlying distinction must still exist somewhere reachable — likely on the Investment Case detail page — not be discarded.
- **Recommendation is always withheld today**, with an honest, specific reason (`atlas/analysis_engine/recommendation.py`). This module's real, decided replacement is the Decision Support Engine (§11.1) — the migration must not reintroduce an imperative Buy/Add/Hold/Trim/Exit vocabulary anywhere, including inside the module/variable names this eventually gets built into. See §11.1 for the full resolved specification.
- **Two vocabularies must stay distinct and must never be merged.** (1) **Atlas's own language** — the Decision Support Engine's evidence-support statements ("Current evidence supports increasing exposure"), always Atlas-voiced, always about evidence, never a command. (2) **The investor's own action vocabulary** — the existing Add-to-Position / Trim / Remove / Leave-as-is buttons on the Actions flow, which record what the *investor* chose to do. These already coexist correctly in the current implementation (Atlas states an assessment; the investor clicks their own button) — "Atlas owns the analysis, the investor owns the decision" is not a new requirement, it is what the existing Decision-recording flow already does. The risk is only in the *new* UI surfaces (Holdings table Action column, Investment Case header) that didn't exist before and need to be built to respect this split from the start, since the original screenshots showed Atlas's language and the investor's action blurred into one imperative-sounding pill.
- **Scenario valuation is a structurally locked, not-yet-implemented capability** (`UnavailableCapability(NOT_YET_IMPLEMENTED)`) — the only real valuation method is Current FCF Yield. See §11.1.
- **Four of six Business Analysis categories (Business Model, Competitive Position, Management Quality, Business Model Durability) stay honestly `insufficient_input`** by deliberate doctrine — Atlas does not fabricate qualitative judgments from financial statements alone. See §11.1.
- **Trim and Remove both record a SELL-type Decision; Leave-as-is records a HOLD and skips the transaction-report step entirely.** This exact mapping must survive any redesign of the Actions UI.
- **A missing financial value renders as `—`, never `0` or blank.** This convention must carry into whatever new financial-table component is built.
- **Daily Brief's alphabetical-by-ticker, no-invented-importance-ranking ordering rule** (`atlas/analysis_engine/daily_brief.py`) — if the new "Today's Priorities" numbered list on Daily Brief implies a ranked order, that ranking needs a real, agreed source (see §11.2), not a silent reuse of Daily Brief's deliberately-unranked entry list.
- **Provider/data-completeness honesty rules** across Company Data Foundation v1 (never fabricate a missing company data point, always attribute provenance, never silently merge conflicting provider values) — nothing in the visual redesign should create pressure to soften these when a "confident-looking" new UI has no real data to show.

## 6. UI elements that should be removed

- **The three separate, redundant "Ask Atlas" boxes** (Discovery's chat, Portfolio's "Today's Discussions" Ask input, Investment Case's "Discuss this Case" Ask input) — **finalized (Decision Log #2)**: all three are deprecated and replaced by the single, persistent, cross-workspace Atlas Companion. Removing three near-duplicate, inconsistently-capable implementations is a genuine simplification, not just a rename (§11.5).
- **Investment Case's "Priority" column placeholder note and "Thesis" staleness column**, if and only if the new Holdings table's real "Action" column ends up backed by real data — until then, these should not be removed, since they are the only two honest signals the current implementation has in that slot (see §11.1 — do not remove an honest placeholder in favor of a not-yet-real one).
- **Duplicated "Portfolio Impact" framing.** Today, Executive Summary (Investment Case) and Business Section both independently render "your weight / largest position / concentration / cash" facts. The new design's compact header stat row for the Investment Case page appears to absorb this into one place — the duplicate rendering in Business Analysis's "Portfolio Context" subsection should be removed once the new header carries it.
- **The former standalone Conviction/Valuation/Evidence "badge card"** was already removed from the current implementation in a prior sprint (per the code's own comment) in favor of Executive Summary — nothing further to do here, noted only so the migration doesn't accidentally reintroduce it.

## 7. Opportunities to simplify the current implementation

- **`InvestmentCasePage.tsx` at 5144 lines in one file** is itself a simplification opportunity independent of the visual redesign — the tabbed/collapsible structure implied by the new design is a natural forcing function to finally split this into per-tab modules (Overview, Financials, Atlas View, Business/Valuation/Risk/Evidence, Decision Record, More Details) rather than one monolithic component tree.
- **Collapsing the three Ask/Discuss implementations into Atlas Companion** (§6) removes real duplicated state-management code (`askInput`/`askSubmitted` pairs exist independently in `PortfolioPage.tsx` and twice in `InvestmentCasePage.tsx`).
- **Six duplicated enum→translation-key lookup tables** for Conviction/Risk/Valuation/Business status across `PortfolioPage.tsx` and `InvestmentCasePage.tsx` collapse into one shared badge-mapping module (§2).
- **The Financials table** is currently defined once, inline, inside `InvestmentCasePage.tsx`; extracting it (§2) also makes it trivially reusable if the new Portfolio Holdings table or a future Watchlist detail view wants a compact financial snippet.
- **`deriveActivity.ts` / `deriveOutstandingWork.ts`** are already correctly shared between History, Dashboard, and Investment Case — this is a good existing pattern worth extending to any new derivation logic the migration adds (e.g. a real "Today's Priorities" ranking, if that becomes real — §11.2), rather than each page computing its own version.

## 8. Architectural risks

- **Dot-rating visuals — RESOLVED as a decision, still a real implementation risk to manage.** Decision Log #3 settles the doctrine question: dots are presentation only, derived from existing categorical assessments, never a new parallel scoring system. The remaining risk is purely one of execution discipline: each dimension needs an explicit, documented ordinal mapping (e.g. `weak→2/5, moderate→3/5, strong→5/5`) reviewed the same way a translation key is reviewed, not invented ad hoc per component. **One dimension shown in the screenshots has no existing categorical source at all: "Expected Return."** Every other scorecard dimension (Business Strength, Growth Outlook, Valuation, Risk Level, Capital Allocation, Portfolio Fit) maps onto a real, already-shipped enum; Expected Return does not — it implies the scenario-valuation/numeric-return capability that is still unbuilt (§11.1). This dimension should be dropped from the scorecard or replaced with a real categorical field until scenario valuation exists as a real capability — it cannot be "derived from an existing assessment" because no such assessment exists yet.
- **The "Action" column/pill — RESOLVED at the language/doctrine level (Decision Log #1), open at the visual-treatment level.** Atlas will never say "Buy"/"Add"/"Trim" — but the pill/badge *styling* shown in the original screenshots (short, imperative-styled words in colored badges) is itself part of what made the design read as a command, independent of the words inside it. A short badge reading "Add" in green still reads as an instruction even if the backend's real output is a full evidence-support sentence truncated to fit. The Decision Support Engine's six states need their own short, non-imperative badge labels (e.g. "Entry supported" / "Thesis intact" / "Insufficient evidence" — see §11.1) designed explicitly to avoid reintroducing this problem through the visual treatment alone.
- **Watchlist analytical depth.** The new Discovery/Daily Brief designs assume Watchlist entries carry the same Conviction/Valuation/Risk richness as Portfolio holdings. Today's Portfolio Cockpit service (`atlas/alpha/portfolio_cockpit`) only iterates Portfolio holdings, not Watchlist entries — extending it to Watchlist is probably straightforward (the underlying Investment Case composition is ticker-agnostic) but is unbuilt and unscoped today.
- **Market/macro data has no provider today.** "Market Context" (S&P 500, sector performance, 10Y yield, VIX) requires a new data provider integration entirely outside the existing SEC EDGAR / Alpha Vantage company-fundamentals scope, with its own rate-limit and reliability characteristics to design for.
- **Earnings/economic events calendar has no provider today** and was explicitly named out-of-scope in a prior sprint ("Do not build earnings-event monitoring yet"). Building it now is a legitimate product direction but is a new, separately-scoped capability, not a migration task.
- **Tabbing/collapsing Investment Case's sections** (§4) changes what is indexable/scrollable/linkable — if any existing deep link, browser back-button behavior, or `data-trace-source` analytics attribute depends on all sections being simultaneously present in the DOM, that needs to be re-verified against the new tabbed structure before it ships.

## 9. Potential regressions

- **Loss of the visible Actions flow — addressed by proposal, not yet resolved.** None of the supplied Investment Case screenshots clearly show the Add/Trim/Remove/Leave-as-is → reason/confidence → Decision → Outcome → trade-execution flow — the single most business-critical interaction in the current product (it is how a real investment decision gets recorded at all). §13 below proposes a concrete UX for reintegrating this flow into the new information hierarchy. This regression risk remains open until that proposal is approved.
- **Loss of the "More Details" granular workflow's easy discoverability.** Today, Observation → Evidence → Knowledge Reference → Reasoning Trace → Judgment records are reachable (if collapsed by default) directly on the page. If the new tabbed design pushes this several clicks deeper, any existing Alpha-internal debugging/inspection workflow that relies on quick access should be explicitly re-confirmed as still reachable.
- **Loss of full financial history depth.** Today's Financials table shows every available period (16+ years for some real companies verified live). The new design shows 2 periods + "View all financial data →". If "View all" is a real expansion rather than a dead link, this is fine; if it's aspirational, real historical depth becomes harder to reach than it is today.
- **Silent downgrade of "Analysis Coverage" visibility.** If the new Holdings table's column set (§4) ships without carrying the Analysis Coverage vs. Conviction distinction (added specifically to fix a real, user-facing honesty problem — Portfolio previously showed "Insufficient evidence" for every holding regardless of how much real data existed underneath) *anywhere* reachable, that specific, recently-fixed problem effectively regresses.
- **Ask Atlas → Atlas Companion behavioral regression risk.** The current per-page placeholders are honest, static "coming soon" notices — never a fabricated reply. If Atlas Companion's first implementation is rushed to "look done" before its context-awareness (active workspace, conversation continuity) genuinely works, the regression is from "honest placeholder" to "unreliable feature," which is a worse trust outcome than the current honest non-functionality.
- **Trade log / reconciliation UI.** Portfolio's inline reconcile-weight flow (single-expanded-row-at-a-time) is not visible in the supplied Portfolio screenshot at all — confirm it has a home in the new design before assuming it disappears.

## 10. Recommended migration order

Ordered to front-load real, low-risk, backend-ready work and push every new-capability item (§11) to the end, each as its own explicitly-scoped sprint:

1. **Foundation extraction first, no visual change yet.** Build the shared `StatusBadge`, `AsyncSection`, and extracted `FinancialsTable` components (§2) against the *current* visual design, so the subsequent page migrations consume one already-tested implementation rather than building new presentation and new shared components simultaneously.
2. **Decision Support Engine — build early, in parallel with Foundation extraction (step 1), not deferred to the end.** Now that the language and shape are finalized (Decision Log #1, §11.1), this is no longer a blocked, open-doctrine item — it can and should be built as a small, self-contained backend sprint before Portfolio's Holdings table migration reaches its Action column, so that column ships with real data on day one rather than as a placeholder needing a fast-follow.
3. **Portfolio page migration.** Highest ratio of "real backend data already exists" to "new capability required" (§1, §3) of the four pages — Action Center, header stats, most Holdings table columns, and (once step 2 lands) the Action column all migrate directly. Exp. Return/Upside/Downside remain genuinely deferred (scenario valuation, still unbuilt — §11.1).
4. **Investment Case page — data-mapping and layout restructuring, plus the Action Flow reintegration once §13 is approved.** Migrate the tabbed/collapsible structure (§4) and every field that already exists (§1); wire in the header's evidence-support sentence and investor action buttons per §13; hold Valuation Scenarios and the qualitative Business Analysis narrative fields back (§11.1, §11 items below) — those remain genuinely unbuilt. This is the largest single piece of work in the migration given the current file's size (§7) and should be sequenced as its own multi-step effort, splitting the file as part of the work.
5. **Daily Brief migration — structure only.** Ship "Portfolio Changes" / "Watchlist Updates" (real data, §1) and the "Today's Priorities" list (reusing Portfolio's real Action Center data, §1) before attempting the narrative paragraph (needs a real synthesis step, §11.2), Upcoming Events (§11.4), or Market Context (§11.4).
6. **Discovery migration — Watchlist table and Review Company first.** The Watchlist section can ship once Portfolio Cockpit is extended to Watchlist entries (a real, scoped, but currently-unbuilt piece — §8); Opportunities (§11.3) and Research Ideas (folds into Atlas Companion, §11.5) come after.
7. **Atlas Companion, as its own cross-cutting workstream, in parallel with 3–6.** Since it replaces three existing UI elements at once (§6) and must be consistent everywhere, it should not be built three separate times inside each page's migration — build it once, wire it into each page as that page's migration reaches the point where its old Ask/Discuss box is being removed.
8. **New-capability sprints, each separately scoped and approved:** scenario valuation (fair value/margin of safety/Bull-Base-Bear), qualitative Business Analysis narrative, Opportunities/candidate generation, market/macro context, earnings calendar, History's lesson/pattern/strategy-evolution analytics (§11.2–§11.4). None of these should be scheduled as part of "the migration" — each is a real product decision with its own doctrine implications, the same way the Decision Support Engine was until Decision Log #1 resolved it.

## 11. Inconsistencies between the Figma designs and the current implementation

This is the section implementation planning most depends on getting right. Each item below is something the screenshots show as if it already works, that does not exist in the backend today.

### 11.1 The Decision Support Engine — RESOLVED by Decision Log #1 (still needs to be built)

**Original finding:** the backend's `atlas/analysis_engine/recommendation.py` always returns a withheld recommendation with an honest reason today — there is no Buy/Add/Hold/Trim/Exit capability. The new designs assumed this existed and was trustworthy enough to show as a per-row Action pill, a header "Action:" line, an "Atlas Recommendation" field on History, and a "Recommended Change" narrative on Portfolio.

**Resolution:** Atlas will provide directional guidance, but never as an imperative command. It states what the current evidence supports, using Atlas's own voice, never the investor's. This is now a named, scoped capability — the **Decision Support Engine** — with a finalized six-state vocabulary:

| State | Example sentence |
|---|---|
| Entry supported | "Current evidence supports initiating a position." |
| Increase supported | "Current evidence supports increasing exposure." |
| Thesis intact | "Current thesis remains intact." |
| Reduction supported | "Current evidence supports reducing exposure." |
| Exit supported | "Current evidence supports exiting the position." |
| Insufficient evidence | "Current evidence is insufficient to support any portfolio action." |

**How this must be built, to stay consistent with everything else in this codebase:** every other categorical assessment in the current system (Conviction, Analysis Coverage, Risk, Business status) is a small, pure, deterministic function over signals that are already computed elsewhere — never a new independent model, never a numeric score underneath a categorical label. The Decision Support Engine must be built the same way: a new pure function taking the case's already-real Conviction level, Analysis Coverage level, Risk findings, and current holding state (held / not held) as input, and returning one of the six states above plus its reasons — the same `{level, reasons}` shape `ConvictionAssessment`/`AnalysisCoverageAssessment` already use. It is **not** a new scoring/ranking/ML model, and it does not read anything the rest of the analysis doesn't already compute. This should be scoped as its own sprint (§10), with its own exact decision table specified and reviewed before implementation — this review is not that specification, only the doctrine and shape it must follow.

**Where this replaces existing/proposed UI:**
- Portfolio Holdings table's **Action** column — becomes a short, non-imperative badge for one of the six states (exact short labels still need to be designed — "Entry supported," "Thesis intact," "Insufficient evidence" are working examples, not final copy — see §8's note that the *badge styling itself*, not just the words, must avoid reading as a command).
- Investment Case header's **"Action:"** line — becomes the full evidence-support sentence, paired with the investor's own separate action buttons (§13).
- History's **"Atlas Recommendation"** field — becomes an evidence-support sentence, consistent with the above, shown alongside (not merged with) the investor's own recorded action ("Trimmed Aug 3").
- Portfolio's **"Recommended Change"** narrative — becomes a sentence generated from the same six-state vocabulary, not free-form advisory text.

**Two related items remain unresolved and out of scope for the Decision Support Engine itself:**
1. The new design's per-holding **Exp. Return / Upside / Downside** figures and the **Bull/Base/Bear scenario valuation with Fair Value and Margin of Safety** still require the scenario-valuation capability the backend currently marks `UnavailableCapability(NOT_YET_IMPLEMENTED)`. The Decision Support Engine's evidence-support sentences do not require a numeric return estimate to exist — the six states above are all reachable from categorical Conviction/Risk/Analysis Coverage alone — but the screenshots' numeric return figures are a separate, still-unbuilt capability and must not be assumed to arrive "for free" alongside the Decision Support Engine.
2. **Resolved by Decision Log #3:** the 5-dot rating scorecard is presentation-only and must derive from existing categorical assessments — see §8 for the one dimension ("Expected Return") that currently has no real source to derive from.

### 11.2 Daily Brief's narrative synthesis and ranked priorities

The current Daily Brief produces one deliberately unranked, alphabetical-by-ticker sentence-per-company summary (`atlas/analysis_engine/daily_brief.py`'s own docstring explicitly forbids an importance ranking). The new design shows:
- A **multi-sentence narrative paragraph** ("Good morning. Nothing in your portfolio requires immediate action today. Adobe has entered your preferred valuation range...") — this requires a real synthesis step across Portfolio + Watchlist + Opportunities that does not exist; today's `summary` field is one templated count sentence, not free narrative.
- A **numbered, ranked "Today's Priorities" list** (1 through 5) spanning Portfolio, Watchlist, and Discovery items together — today's closest analog (Portfolio's own Action Center) is scoped to Portfolio only and explicitly avoids cross-source ranking beyond its three severity tiers.

Both are real, buildable extensions of existing derivation logic (§1) — but the *ranking/synthesis* logic itself is new and should be written once, as a real backend capability, not implied by frontend layout choices.

### 11.3 Opportunities / candidate generation (Discovery, Daily Brief)

Discovery's current implementation has an explicit, honest "not yet available" disclosure for this exact capability (`discovery.opportunities.notYet`) — the code comment for it states plainly: "no candidate generator exists in this Alpha." The new design's Opportunities table (Company / Conviction / Fit / Valuation / Exp. Return / Why Now) is a fully-realized version of exactly the capability that placeholder exists to honestly disclaim. This is a new, non-trivial capability (screening logic against some notion of "your investment criteria," which doesn't have a defined data model today either) and should be scoped as its own sprint.

### 11.4 Market context and events calendar (Daily Brief)

"Market Context" (S&P 500 / sector performance / 10Y yield / VIX) and "Upcoming Events" (earnings dates, Fed minutes, capital markets days) both require new external data sources with no current provider integration in this codebase (`atlas/business_data_providers` today covers only SEC EDGAR company fundamentals and Alpha Vantage company/market-snapshot data — no macro index feed, no economic calendar feed). A prior sprint's own documentation explicitly named earnings-event monitoring as deliberately out of scope for the current architecture.

### 11.5 "Ask Atlas" → Atlas Companion — RESOLVED (Decision Log #2)

Every visible "Ask Atlas"/"Discuss with Atlas" box in the screenshots (Discovery's Research Ideas + free-text input, Portfolio's Discussion section, Investment Case's "Discuss with Atlas" panel) is **not** to be built as shown — each is replaced by the new cross-workspace Atlas Companion, which must: exist across all workspaces, preserve conversation context, understand the active workspace, provide contextual suggested prompts, and behave consistently everywhere it appears. Two things worth flagging here specifically:
- Discovery's chat (`POST /api/discovery/chat`) is the only one of the three current Ask-pattern implementations that is a **real, working backend integration** today (with honest degraded-mode handling for missing/failed providers) — the other two (Portfolio, Investment Case) are UI-only placeholders. Atlas Companion's initial implementation should be built as an evolution of Discovery's real backend integration (extended with workspace-context-awareness), not built from scratch alongside it.
- "Preserve conversation context" and "understand the active workspace" are real, non-trivial requirements (session/context management across route changes, not just visual persistence) — this needs its own design pass, not an assumption that it falls out naturally from making the chat UI visually persistent.

---

## 12. Recommendations before implementation begins

1. **Resolved:** the Decision Support Engine's language and shape are finalized (Decision Log #1, §11.1). The remaining task is to write its exact decision table (which combination of Conviction/Analysis Coverage/Risk/holding-state produces which of the six states) as a short, reviewable spec before the first line of code — the same way `calculate_conviction`'s own rule table exists as a reviewable artifact, not an implicit assumption baked into a component.
2. **§13 below is the proposal for where the Actions (decision-recording) flow lives in the new design — it must be approved before the Investment Case migration begins**, per the explicit instruction that implementation waits on this document's approval.
3. **Scope §11.2–§11.4 as separate, named sprints with their own product review**, explicitly not bundled into "the migration." Each has real doctrine, data-provider, or trust implications independent of any UI work.
4. **Decide the Investment Case tabbing/collapsing structure explicitly** (§4, §8, §13) — confirm with the design source exactly which sections become tabs, which stay always-visible, and whether URL/deep-linking behavior per tab is required, before splitting the 5144-line file.
5. **Resolve where Analysis Coverage (§5, §9) surfaces in the new Holdings table or Investment Case header** — this was a recent, deliberate fix to a real user-facing honesty problem and should not silently disappear because the new column set doesn't have an obvious slot for it.
6. **Build Atlas Companion as an extension of Discovery's existing real chat integration**, not as a new implementation built in parallel with it (§11.5) — and treat "preserve conversation context across workspaces" as its own design task, not an assumed side effect of shared visual chrome.
7. **Extend Portfolio Cockpit to Watchlist entries as an early, small, real backend task** (§8) — it unblocks a meaningful fraction of both the new Discovery and Daily Brief designs (§1) without requiring any of the higher-risk new-capability work in §11.
8. **Resolved:** the 5-dot rating visual language is presentation-only, derived from existing categorical assessments (Decision Log #3, §8, §11.1) — no new scoring system. The remaining task is documenting and reviewing the exact enum-to-dot-count mapping per dimension, and dropping or substituting the one dimension ("Expected Return") that currently has no real source (§8).
9. **Apply the "evidence-support, never imperative" language rule consistently, including in code and API naming, not only in rendered UI copy.** `atlas/analysis_engine/recommendation.py` and any new module built for the Decision Support Engine should be named and structured to make the distinction obvious to future engineers, not just to end users — e.g. a field or module literally named `recommendation` inviting an imperative reading should be reconsidered as part of that build, not left as a naming leftover from the old concept.
10. **Treat this review as input to planning, not as the plan itself.** With Decisions 1–3 now finalized, the remaining open item before implementation can be authorized is approval of §13.

---

## 13. Investment Case Action Flow — UX Proposal

> **Status: PROPOSAL ONLY — NOT APPROVED. Do not implement any part of this section until it is explicitly confirmed.**

### 13.1 What has to be reintegrated

The current decision-recording flow (`InvestmentCasePage.tsx`, "Actions" card) is a specific, ordered sequence and none of it is optional or simplifiable without losing real functionality:

1. Investor picks one of **Add to Position / Trim / Remove / Leave as is**.
2. A **reason** (free text) and **confidence** (0–100) form appears for that specific choice.
3. Submitting records a real Decision (`POST /api/decisions`) — Add maps to a BUY-type Decision, Trim/Remove both map to a SELL-type Decision, Leave-as-is maps to a HOLD-type Decision and stops here (no transaction occurred).
4. For Add/Trim/Remove, once the Decision is recorded, a **"Report Transaction"** action becomes available (not required immediately — this is often reported later, once the trade actually executes).
5. Reporting opens an **Outcome** form (statement, note) with an **"external trade" checkbox**.
6. If checked, a **trade-execution sub-form** appears (security, type, quantity, execution price, fees, executed-at) and posts to both `POST /api/outcomes` and `POST /api/alpha-portfolio/apply-trade`.

Steps 3–6 must remain in this order and must remain separable in time (an investor may record a Decision today and report its Outcome/trade days later) — this is existing, load-bearing business logic (§5), not a UI convenience.

### 13.2 Where this needs to live in the new hierarchy

The new Investment Case design (screenshots 7–8) already reserves a slot for this, just not a functioning one: the compact header row shows `Valuation: Slightly Cheap | Portfolio fit: Excellent | Portfolio weight: 6.14% | Action: Add / Review evidence`. This is the natural anchor point — it is the first thing visible on the page, before any scrolling, and it already sits directly next to where Atlas's own assessment (Valuation, Conviction dots, Fair Value) is shown. This placement also happens to be a better literal expression of "Atlas owns the analysis, the investor owns the decision" than the current implementation has today, since the current Actions card is buried after ~10 other cards of scrolling, disconnected from the assessment that motivates it.

The new design's greyed-out row at the bottom (`Decision History · Timeline · Last Activity · Outstanding Work · Outcomes · More Details`) is the other relevant anchor — this is where the *record* of past decisions lives, as distinct from the *action* of recording a new one.

### 13.3 Proposed design (recommended: Option A)

**Split the flow into two tiers, matching the two anchor points above, rather than reproducing today's single large always-visible card.**

**Tier 1 — Header, always visible, no scrolling required.**

```
MSFT · Microsoft Corporation
NASDAQ · Technology · Software – Infrastructure

Conviction: High ●●●●○   Fit: Excellent   +18% Annualized
Fair Value: 540 USD   Downside: 455 USD   Risk: Medium

Valuation: Slightly Cheap | Portfolio fit: Excellent | Portfolio weight: 6.14%

Current evidence supports increasing exposure.
[ Record a decision ▾ ]                    ⓘ 1 decision awaiting an outcome
```

- The evidence-support sentence (Decision Support Engine, §11.1) sits directly beneath Atlas's other assessment facts, in Atlas's own voice — never inside a button, never phrased as a command.
- `[ Record a decision ▾ ]` is the investor's own, clearly-separate action trigger — a single button, not four separate imperative-sounding buttons competing with Atlas's sentence for attention. Clicking it reveals the investor's real options (Initiate / Increase / Hold / Reduce / Exit position — wording still to be finalized, but investor-voiced, distinct from Atlas's sentence above it).
- The small `ⓘ 1 decision awaiting an outcome` note is a lightweight, always-visible nudge when a Decision has been recorded but its Outcome/trade hasn't been reported yet — carrying forward the same information today's "Report Transaction" button and "Outstanding Work" section provide, without requiring a scroll to discover it.

**Tier 2 — Inline expandable panel, directly beneath the header, not a separate page or modal.**

Clicking `[ Record a decision ▾ ]` (or an option from it) expands a panel in place — the same interaction pattern the current Portfolio page already uses for its single-row-at-a-time Reconcile form (§1, §3) — rather than introducing a new pattern:

```
┌─────────────────────────────────────────────────────────┐
│  Record decision: Increase position                     │
│                                                           │
│  Reason                                                  │
│  [_________________________________________________]    │
│                                                           │
│  Confidence          [___] / 100                         │
│                                                           │
│              [ Cancel ]         [ Record decision ]      │
└─────────────────────────────────────────────────────────┘
```

After submission, the panel transitions in place (no navigation) to the Outcome/transaction-report step exactly as today (statement, note, external-trade checkbox, conditional trade sub-form), then collapses once complete. This preserves every existing form field and every existing validation rule (§5) — only the container changes, from "always-visible bottom-of-page card" to "on-demand panel anchored to the header."

**Tier 2, later visits:** once a Decision has a pending Outcome, reopening `[ Record a decision ▾ ]` (or clicking the `ⓘ` nudge directly) resumes at the Outcome/transaction-report step, not back at "pick an action" — this matches today's behavior where `reportDecisionId`/`reportOutcomeStatus` already track this resumable state independent of the initial action choice.

**Decision History / Timeline / Last Activity / Outstanding Work / Outcomes tabs** (bottom row) remain purely read-only records of what this flow has produced — no change to their content or purpose, only their container (tabbed rather than always-stacked, per §4).

### 13.4 Alternative considered (Option B, not recommended)

A dedicated tab (e.g. "Decide") alongside Decision History/Timeline/etc. in the bottom tab row, containing the full flow.

**Why Option A is recommended over this:** the decision-recording action is not equivalent in kind to the read-only history tabs next to it — it is the single most important thing an investor can do on this page, and burying it as one tab among six (arguably the *least* discoverable position, since it would sort alphabetically/logically among historical-record tabs an investor is not always looking to update) works against "Atlas owns the analysis, the investor owns the decision" being visually obvious. Option A keeps the action physically adjacent to the analysis that motivates it. Option B is noted here only so it isn't silently assumed to have been rejected without reasoning.

### 13.5 What this proposal explicitly does not change

- The Decision/Outcome/trade data model, validation rules, or the ADD→BUY / TRIM,REMOVE→SELL / LEAVE-AS-IS→HOLD mapping (§5) — unchanged.
- The separability of recording a Decision now and reporting its Outcome later — unchanged.
- The existing `POST /api/decisions`, `POST /api/outcomes`, `POST /api/alpha-portfolio/apply-trade` endpoints and their payload shapes — unchanged.
- The "More Details" collapsed disclosure for the granular legacy Observation/Evidence/Knowledge-Reference/Reasoning-Trace/Judgment workflow — unchanged, remains reachable via the tab row, independent of this proposal.

### 13.6 Open questions this proposal needs answered before it can be treated as approved

1. Exact wording for the investor's own action options inside `[ Record a decision ▾ ]` — this review uses "Initiate / Increase / Hold / Reduce / Exit position" as a working placeholder, chosen only to stay clearly distinct from Atlas's evidence-support sentence; final copy is a product-language decision, not an engineering one.
2. Whether the `ⓘ N decision(s) awaiting an outcome` nudge should also appear anywhere on Portfolio's Holdings table (today's Outstanding Work concept already exists there via the Action Center — §1) or remain Investment-Case-local.
3. Whether "Record a decision" should be disabled/hidden entirely when a holding isn't linked to a Portfolio position at all (today's `!linkedHolding` case shows an explanatory note instead of the buttons) — Option A assumes this same guard carries forward unchanged, but it should be confirmed against the new header layout specifically.
4. Confirm this proposal against the actual Figma source (not just the eight screenshots supplied for this review), since the header's "Action: Add / Review evidence" text may already have a fuller intended design this review cannot see.

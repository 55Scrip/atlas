# Investment Case Engine v1 — Implementation Design

**Status:** Proposed. Not yet accepted or adopted by `APP-000`.
**Type:** Cross-cutting implementation design — spans `atlas/core/`, `atlas/domains/`, `atlas/business_data_providers/`, `atlas/analysis_engine/`, `atlas/alpha/`, and `frontend/`. Depends on, and does not attempt to re-govern, `docs/atlas_domain_object_architecture/OE-002-Domain-Object-Model.md` (Accepted) and `docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` + `docs/atlas_decision_engine/DE-001..DE-008` (Draft v0.1, not yet `APP-000`-adopted).

---

## 1. Executive Finding

Atlas already has most of the hard parts of this capability built, in five separate, currently-disconnected pieces:

1. A real, tested, swappable business-data layer (`atlas/business_data_providers/`: SEC EDGAR fundamentals + Alpha Vantage market data) — but it only runs when a human invokes a CLI.
2. A real recommendation/direction pipeline (`atlas/analysis_engine/recommendation.py`, `direction_selector.py`, `conviction.py`) governed by a real, detailed (if still Draft) doctrine (`DE-001`, `DE-002`, `DE-004`, `DE-005`, `DE-006`, `DE-007`, `DE-008`) — but most directions are structurally blocked because valuation isn't wired to it yet.
3. A real "Canonical Investment Case" analysis endpoint (`GET /cases/{case_id}/analysis`) and a 4,700-line frontend page (`InvestmentCasePage.tsx`) already rendering it — but nothing populates a Case automatically; a Case today is an empty two-field shell (`id`, `recorded_at`) until a human manually records Observations/Evidence/Decisions into it.
4. A real Portfolio↔Case linking endpoint (`/alpha-portfolio/holdings/{ticker}/case-link`) — but no equivalent exists for Watchlist, which today is just a bag of ticker strings with no Case at all.
5. A real, disciplined product doctrine (`ATLAS_CONSTITUTION.md`, `APP-000`, `APP-002`, `UX-000`, `ADR-003`) that already forbids the two shortcuts a naive implementation would reach for: a numeric confidence score (`UXD-R-064`), and a second priority/ranking model outside the Atlas Priority Model (`PFINV-004`).

**The Investment Case Engine is therefore not a new subsystem. It is the missing wiring between (1)–(4), built inside the guardrails already set by (5).** The single biggest functional gap is *automatic triggering*: nothing today fires when a company is added to Watchlist or Portfolio. Closing that gap, plus giving Watchlist the same Case-linkage Portfolio already has, plus adding the handful of genuinely new components (Company Identity, Business Quality, Risks, Strengths, Open Questions, Monitoring Plan, Change Log) that have no existing home, is the actual v1 scope.

---

## 2. Current Repository Capabilities Relevant to This Work

| Capability | Location | State |
|---|---|---|
| Case (ownership boundary, `id` + `recorded_at` only) | `atlas/core/domain/case/` | Final, OE-002-governed |
| Observation, Evidence, Decision, Judgment, Outcome, Knowledge Reference, Reasoning Trace | `atlas/core/domain/*` | Final, OE-002-governed, immutable, `case_id`-scoped |
| `TypedDomainObjectReference` | `atlas/core/domain/shared/typed_reference.py` | Final — structural pointer, no semantics |
| Company (persistence entity + financials) | `atlas/models/entities.py` (SQLAlchemy `Company`, `FinancialHistory`) | Implemented, not wired to Case |
| Company (lightweight identity) | `atlas/shared/entities.py` | Implemented, used by Portfolio/Watchlist |
| Portfolio (`Holding`, `Portfolio`) | `atlas/shared/entities.py`, `atlas/domains/portfolio/`, `atlas/alpha/portfolio/` | Implemented; has ticker→Case linking |
| Watchlist (`Watchlist(tickers: tuple[str,...])`) | `atlas/shared/entities.py`, `atlas/domains/watchlist/` | Implemented, but **no Case linkage, no dedicated frontend page found** |
| Business data providers (fundamentals + market data), independently swappable | `atlas/business_data_providers/{sec_edgar,alpha_vantage}.py` | Implemented, tested, **manually triggered only** (`atlas/alpha/business_data_refresh/cli.py`) |
| `CompanyDataProvider` protocol (legacy) | `atlas/providers/{base,yahoo,mock}.py` | Implemented, overlapping purpose with `business_data_providers` — needs reconciliation, not a third provider layer |
| Valuation modeling (facts, cash flow, scenarios) | `atlas/analysis_engine/valuation/` | Implemented, groundwork for scenario-based valuation already exists |
| Risk pipeline stub | `atlas/analysis_engine/risk/pipeline.py` | Present but not verified to be data-driven yet |
| Recommendation (direction, conviction) | `atlas/analysis_engine/{recommendation,direction_selector,conviction,recommendation_conviction}.py` | Implemented; BUY/ADD/EXIT structurally blocked pending valuation wiring; governed by `DE-007`/`DE-008` (Draft) |
| Decision Engine doctrine (Recommendation Framework, Reasoning Structure, Portfolio Intelligence, Honest Uncertainty, Decision Memory, Execution Guidance) | `docs/ATLAS_DECISION_ENGINE_DOCTRINE.md`, `docs/atlas_decision_engine/DE-001..008` | Draft v0.1, not `APP-000`-adopted, but detailed and internally consistent |
| Investment Case analysis endpoint + UI | `atlas/alpha/investment_case/api/router.py` (`GET /cases/{case_id}/analysis`), `atlas/alpha/case_intelligence/`, `frontend/src/routes/InvestmentCasePage.tsx` | Implemented, renders Core Loop objects + conviction/findings/open-questions/recommendation-state, **but nothing populates it automatically** |
| Portfolio row summary | `frontend/src/routes/PortfolioPage.tsx` (`HoldingsTable`) | Implemented; "Priority" column is an explicit placeholder for the not-yet-wired Recommendation output; "Insufficient evidence" is the honest, doctrine-correct fallback (`ConvictionLevel.INSUFFICIENT_EVIDENCE`), not a bug — it's simply the *default* today because nothing feeds it real evidence automatically |
| Activity feed | `frontend/src/activity/deriveActivity.ts` | Pure frontend cross-reference of Decision/Outcome/trade-log entries; reusable as-is for Change Log surfacing |
| Single Priority Model | `docs/atlas_product_architecture/APS-006-Portfolio.md` (`PFINV-004`) | Doctrine only — governs that no second ranking model may be invented |
| Recommendation terminology governance | `docs/atlas_ux/governance/ADR-003-*.md` (Accepted) | Reserves "Atlas Recommendation" (Concept A) vs. "Proposed Decision Candidate Content" (Concept B); neither is a Domain Object |

---

## 3. Current Gaps

1. **No automatic trigger.** Adding a ticker to Watchlist or Portfolio does not create a Case, does not call the business-data providers, and does not populate anything. This is the central gap the product principle is written against.
2. **Watchlist has no Case linkage at all.** Portfolio has `/holdings/{ticker}/case-link`; Watchlist has nothing analogous, and no dedicated Watchlist frontend page was found. This directly contradicts "Watchlist should be almost as analytically complete as Portfolio."
3. **Two `Company` definitions with no stated relationship** (`atlas/shared/entities.py` plain dataclass vs. `atlas/models/entities.py` SQLAlchemy ORM). A third "Company Identity" concept must not be added on top; the two existing ones need an explicit, disclosed boundary (see §4).
4. **Two overlapping provider abstractions**: `atlas/providers/base.py` (`CompanyDataProvider`, Yahoo/mock-backed, legacy) and `atlas/business_data_providers/` (SEC EDGAR + Alpha Vantage, current, tested, explicitly designed for swappability). The Engine must standardize on the latter and treat the former as legacy, not build a third.
5. **No scheduler/cron/event-ingestion layer exists anywhere in the repo.** Business-data refresh is CLI-only. "Continuous monitoring" (item 5 of the core loop) has zero existing infrastructure.
6. **No Business Quality, Risk, Strength, or Open Question generation exists as code.** `DE`-doctrine's §4 "Business Evaluation" is explicitly flagged in its own text as "genuinely new territory, written from first principles" — doctrine only, no implementation. The risk pipeline stub exists but isn't confirmed data-driven.
7. **No provenance/source-category model exists.** `TypedDomainObjectReference` is a structural pointer only, by explicit design (it "deliberately carries no ... provenance"). Nothing in the repo currently tags a fact as company-reported vs. regulatory-filing vs. market-data vs. analyst-estimate vs. news vs. Atlas-inference vs. user-provided.
8. **No change-detection / materiality-assessment layer exists.** Nothing currently distinguishes "new data arrived" from "something in the case materially changed."
9. **Rate-limit exposure.** Alpha Vantage's free tier is 25 calls/day. An engine that auto-triggers on every Watchlist/Portfolio add will exhaust this almost immediately at any real usage volume — this is a genuine, unresolved operational constraint, not a design detail to wave past.
10. **`ATLAS_DECISION_ENGINE_DOCTRINE.md` is not yet `APP-000`-adopted.** This design's Atlas Thesis / monitoring-attention components depend on that doctrine (recommendation, reasoning structure, honest uncertainty, decision memory). Building on a Draft dependency is a disclosed, accepted risk, not an oversight — see §20.

---

## 4. Proposed Investment Case Domain Model

**Core architectural decision: the Investment Case is not a new aggregate that replaces or wraps `Case`. It is the assembled, multi-component view over everything already attached to one `Case.id` — plus a small set of new, independently-owned reference-data components that currently have no home.**

This preserves OE-002's own explicit design choice to keep `Case` minimal ("no further field is canonically required... none is added here") and its closed six-object set — nothing here proposes a seventh OE-002 Domain Object. Company/Financial/Valuation/Business-Quality/Risk/Strength/Open-Question/Monitoring-Plan data are not epistemic acts of the kind OE-002 governs (an Observation, a Judgment, a Decision); they are reference data and Atlas-generated analysis *about* the same company the Case concerns. They are modeled as their own components, each `case_id`-scoped, each independently owned, versioned, and timestamped — exactly the "independently updateable components" the brief requires, and exactly analogous to how `DE-007` already treats `ComputedDirectionalRecommendation` (ephemeral, regenerated) vs. `HistoricalRecommendationSnapshot` (persisted only when it matters).

### Components

| Component | Owner (who writes it) | Nature | Existing code to build on |
|---|---|---|---|
| **Company Identity** | Atlas (automatic) | Reference data, replaceable on refresh | `atlas/models/entities.py::Company`, reconciled with `atlas/shared/entities.py::Company` |
| **Financial History** | Atlas (automatic) | Time series, append-only per fiscal period | `atlas/models/entities.py::FinancialHistory`, `atlas/business_data_providers/sec_edgar.py` |
| **Valuation** | Atlas (automatic + on-demand recompute) | Snapshot + scenario set (bear/base/bull), versioned | `atlas/analysis_engine/valuation/{models,facts,cash_flow,scenarios}.py` |
| **Growth Analysis** | Atlas (automatic) | Derived findings over Financial History | New — thin layer over Financial History + Valuation |
| **Business Quality Findings** | Atlas (automatic + Reasoning) | Evidence-linked findings, no composite score | New — grounded in `ATLAS_DECISION_ENGINE_DOCTRINE.md §4`, implemented for the first time here |
| **Risks** | Atlas (automatic + Reasoning), prioritized | Evidence-linked findings, ranked by relevance not checklist | Extends `atlas/analysis_engine/risk/pipeline.py` |
| **Strengths** | Atlas (automatic + Reasoning) | Evidence-linked findings | New — mirrors Risks |
| **Atlas Thesis** | Atlas (automatic), regenerated | *Is* `ComputedDirectionalRecommendation` + `DE-002` Reasoning Structure, rendered as prose — not a separate generator | `atlas/analysis_engine/recommendation.py`, `direction_selector.py` |
| **Investor Thesis** | User only | User-authored; never rewritten by Atlas | Existing Judgment/Decision entities + free-text; new `InvestorThesis` note component |
| **Open Questions** | Atlas (automatic) + user (can add/resolve) | List, each with a status (open/resolved/changed) | New |
| **Monitoring Plan** | Atlas (automatic, company-specific) | Rule set, not a fixed checklist | New — informed by which components exist/matter for this company |
| **Change Log** | Atlas (automatic, append-only) | Ordered history of material changes | New — feeds from `deriveActivity.ts` pattern, extended server-side |
| **Source Evidence / Provenance** | Atlas (automatic, attached to every fact) | Cross-cutting tag, not a separate screen | New — see §6 |
| **Decision History** | User (via Decision) | Already exists | `atlas/core/domain/decision/` |

Every component carries: `case_id`, `generated_at` / `recorded_at`, a `DataProvenance` tag (§6), and — where applicable — a link back to the specific Financial History period or Evidence/Observation it derives from. None of them are stored as one blob; each is independently fetchable, independently regenerable, and a change to one (e.g., Financial History after an earnings release) does not require regenerating the others unless they causally depend on it (Valuation and Growth Analysis depend on Financial History; Atlas Thesis depends on all of the above plus Reasoning Structure).

---

## 5. Information Architecture

```
Investment Case (view over one Case.id)
│
├─ Company Identity ─────────────┐
├─ Financial History             │  Atlas Knowledge layer
├─ Valuation                     │  (automatic, replaceable,
├─ Growth Analysis               │   sourced from providers +
├─ Business Quality Findings     │   analysis engines)
├─ Risks                         │
├─ Strengths                     │
├─ Atlas Thesis                  │
├─ Open Questions ────────────────┘
├─ Monitoring Plan
├─ Change Log
│
├─ Investor Thesis ───────────────┐  Investor Knowledge layer
├─ Decisions                      │  (user-authored, never
├─ Outcomes                       │   silently rewritten)
├─ Observations / Evidence        │  (mixed — see below)
└─ user notes / reflections ──────┘
```

Observation and Evidence are structurally Atlas Knowledge-adjacent (immutable OE-002 records) but their *content* is frequently user-supplied ("the investor noticed..."). They are tagged by provenance per-instance (§6), not by which layer they sit in — the layer split is about *authorship and mutability contract*, not storage location.

---

## 6. Data / Provenance Model

A single `DataProvenance` value object, attached to every fact and every generated finding:

```
DataProvenance:
  source_category: CompanyReported | RegulatoryFiling | MarketData
                  | AnalystEstimate | News | AtlasGenerated
                  | UserProvided | UserAuthoredThesis | UserDecision
  source_ref: free-text or URL (filing accession number, provider name, etc.)
  as_of: datetime            # when the underlying fact was true/reported
  retrieved_at: datetime     # when Atlas fetched/generated it
  provider: str | None       # "sec_edgar" | "alpha_vantage" | "atlas.analysis_engine.recommendation" | None for user-entered
```

This is deliberately a plain value object, not a new OE-002 Domain Object — it is metadata *about* a fact, carried alongside it, mirroring exactly how `TypedDomainObjectReference` is deliberately silent on provenance and leaves it to the owning object. `DataProvenance.source_category` gives Atlas the vocabulary the brief requires ("Atlas currently sees three risks. You previously identified one additional risk...") without inventing a scoring or confidence mechanism — categorization only, never a number.

**Confidence and quality language reuse existing reserved vocabulary, nothing new is invented:**
- Per-fact epistemic quality (is this fact solid or thin): `APP-002 §7`'s existing word-level categories — Known / Estimated / Possible / Unknown.
- Per-recommendation conviction (how strong is the Atlas Thesis): `DE-004`'s Atlas Confidence Level — High / Moderate / Low / Insufficient Evidence.
- No third scale is introduced. `UXD-R-064` explicitly forbids a numeric or new categorical scale without its own subordinate spec — this design does not attempt one.

---

## 7. Automatic Generation Pipeline

Triggered once, on first linkage of a ticker to either Watchlist or Portfolio (see §10/§11), and re-runnable on demand or on schedule (§8):

```
1. Resolve/verify ticker → identify company (exchange, listing status)
2. Ensure a Case exists for this (user, company) pair — create if absent, reuse if present
3. Fetch Company Identity + Financial History
     → atlas/business_data_providers/sec_edgar.py   (fundamentals)
     → atlas/business_data_providers/alpha_vantage.py (market data, price, shares out)
   Each result stamped with DataProvenance (RegulatoryFiling / MarketData)
4. Compute Valuation snapshot + scenario set
     → atlas/analysis_engine/valuation/*
   Stamped AtlasGenerated, derived_from = Financial History period
5. Compute Growth Analysis (trend + driver identification over Financial History)
6. Generate Business Quality Findings, Risks, Strengths
     → new analysis step, evidence-linked (each finding cites the Financial
       History period / Company fact it rests on) — no composite score
7. Generate Open Questions
     → derived from low-confidence/Unknown-tagged inputs surfaced in steps
       3-6 (e.g., no segment-level data available → open question, not a
       silent gap)
8. Generate Atlas Thesis
     → atlas/analysis_engine/recommendation.py + direction_selector.py
       + DE-002 Reasoning Structure, rendered to the required prose form
   Stamped AtlasGenerated
9. Generate Monitoring Plan (company-specific — see §8)
10. Write one Change Log entry: "Investment Case initially generated"
11. Investment Case is now visible; steps 3-9 are independently re-runnable
    without repeating the others
```

Steps 3-9 are separate application services, each idempotent and independently invocable — this is what makes "reprocess only affected sections" (§8/§9) possible rather than aspirational.

**On failure of an individual step** (e.g., SEC EDGAR has no filer for this ticker — non-US company): the corresponding component is marked `Insufficient Evidence` with an explicit reason, per `APP-002`'s already-adopted phrasing ("There isn't currently enough evidence for Atlas to form a view here") — this is the exception path the brief asks for, not the default path.

---

## 8. Monitoring / Update Architecture

No scheduler exists today; this is new infrastructure, kept intentionally small for v1:

- **Monitoring Plan is company-specific**, generated in pipeline step 9 from *what actually applies* to this company (e.g., a company with no debt gets no "leverage" monitor; a company with disclosed customer concentration gets one). This directly satisfies "Atlas should not simply watch every possible metric for every company" and avoids inventing a fixed checklist.
- **Trigger types**, each independently schedulable:
  - Scheduled refresh (e.g., weekly market-data pull; quarterly-aligned fundamentals pull) — new lightweight scheduler, or reuse of `atlas/alpha/business_data_refresh/cli.py`'s logic behind a scheduled job runner instead of manual invocation.
  - Earnings-event detection — new; can start as a scheduled poll against SEC EDGAR's filing index rather than a push feed.
  - Filing ingestion — extends `sec_edgar.py`.
  - Market-data update — extends `alpha_vantage.py`.
  - News ingestion — **not currently integrated anywhere**; explicitly out of v1 scope (see §16), Monitoring Plan can list "news" as a category without Atlas yet having a live feed for it.
- **Rate-limit-aware scheduling is mandatory, not optional**, given Alpha Vantage's 25/day free-tier ceiling (§3.9) — v1 must queue and prioritize refreshes (Portfolio before Watchlist, most-recently-viewed first) rather than fire-and-forget on every add.
- **Reprocessing only affected sections**: because each pipeline step (§7) is independently invocable and writes to its own component, an earnings-driven refresh re-runs steps 3→4→5→6→7→8→9 in dependency order but does not touch Company Identity (unchanged) or regenerate Open Questions that weren't affected — determined by the Change Detection layer (§9), not by blindly rerunning everything.

---

## 9. Change-Detection Model

Two distinct events, never conflated:

1. **New information arrived** — a provider returned a value different from what's stored (a new fiscal period, a changed share price, a changed estimate). This alone triggers a component update but nothing else.
2. **Something materially changed in the Investment Case** — a new-information event that crosses a threshold worth the user's attention: an Open Question was resolved or newly created; a Risk or Strength finding's evidence changed enough to add/remove/re-rank it; the Atlas Thesis's direction or conviction level changed; Valuation moved enough to change which scenario looks most supported.

The materiality judgment is **evidence-based and qualitative, per the brief's own instruction not to invent scores** — it is answered by re-running the same Reasoning Structure / finding-generation logic (§7 steps 6-8) and diffing the *output* (did the finding set change, did the direction change, did an Open Question's status change), not by a numeric delta threshold invented for this purpose. Where a genuine quantitative comparison is unavoidable (e.g., "margin was 240bps above consensus"), it is reported as a fact, not converted into a synthetic materiality score.

Every material change:
- Writes a Change Log entry (`what changed`, `which component`, `strengthens / weakens / unchanged` — reusing `DE-005`'s existing per-position thesis vocabulary rather than inventing new verbs).
- Updates the relevant Open Question's status if applicable.
- Is a candidate for Today's Priorities / Today's Discussions — **routed through the existing Atlas Priority Model** (`PFINV-004`), not a new ranking system. This design proposes the Investment Case Engine as a new *input* to that model, not a competing one.

---

## 10. Watchlist Integration

This is the largest concrete build item, since Watchlist currently has no Case linkage at all:

- Extend the Watchlist domain (`atlas/domains/watchlist/`, `atlas/shared/entities.py::Watchlist`) with a `WatchlistItem` value object per ticker (mirroring the pattern Portfolio already proved out via `/holdings/{ticker}/case-link`): `ticker`, `case_id`, `added_at`.
- Adding a ticker to Watchlist triggers the full pipeline in §7, identically to Portfolio — the brief's explicit requirement that "the difference is position context, not information availability" is enforced by using the *same* pipeline, not a lighter one.
- A dedicated Watchlist frontend surface is needed (none currently exists) — reuse `InvestmentCasePage.tsx`'s existing rendering plus a Portfolio-row-equivalent summary list, per §13.

---

## 11. Portfolio Integration

- Already has the linking primitive (`/alpha-portfolio/holdings/{ticker}/case-link`); the same pipeline trigger fires here on holding creation instead of being CLI-only.
- **Moving a company from Watchlist to Portfolio is a context change only**: because both reference the same `case_id`, moving means creating/updating the Holding (or Portfolio membership) and removing/retaining the WatchlistItem — the Investment Case itself, all its components, and its full Change Log are untouched. This is the direct payoff of anchoring the Investment Case on `Case.id` rather than on Watchlist- or Portfolio-specific storage.
- Portfolio-specific additions (position sizing, cost basis, weight) remain exactly where they are today (`Holding`) — the Investment Case Engine does not touch position/allocation math, which is `DE-003` Portfolio Intelligence's and `APS-006`'s territory.

---

## 12. Ask Atlas Integration

- Ask Atlas answers from the structured components (§4), not by reconstructing the company from scratch per message — each component is directly retrievable by `case_id` + component name, giving Ask Atlas a bounded, citable context window per question ("why is it expensive" → Valuation component; "what changed after earnings" → Change Log + affected components).
- Every answer Ask Atlas gives should be traceable to a `DataProvenance` tag, satisfying "explain where an important fact or conclusion came from" directly from §6's model — no new explanation mechanism is needed.
- Existing `atlas/ai/api/router.py` (`POST /discovery/chat`) is the natural integration point; this design does not propose a new chat endpoint, only a new context-retrieval layer it can call into.

---

## 13. UI/UX Implications

- **`InvestmentCasePage.tsx`** already renders most of the needed shape (Core Loop objects + a canonical analysis view) — extend it with the new components (Company Identity header, Financial History charts, Valuation scenarios, Business Quality/Risks/Strengths findings lists, Open Questions with status, Monitoring Plan, Change Log timeline), each visually distinguishing Atlas Knowledge from Investor Knowledge per §4's layer split.
- **`PortfolioPage.tsx`**'s `HoldingsTable` "Priority" column (currently an explicit placeholder) becomes real once the Atlas Thesis pipeline is wired; row summaries can show the brief's example shape ("Case updated today · 12 monitored signals · 3 open questions · 1 material change") sourced directly from Change Log + Monitoring Plan + Open Questions counts — no new aggregate needs computing beyond counting existing components.
- **A new Watchlist page** is required (genuinely missing today), styled analogously to `PortfolioPage.tsx`'s holdings table minus position-specific columns (weight, cost basis).
- **"Insufficient Evidence" becomes correctly rare** once §7's pipeline runs automatically — it remains, unchanged, the honest fallback for the disclosed real gaps (non-US filers, no analyst coverage, genuinely thin business-quality evidence), consistent with existing `APP-002` phrasing, not replaced by anything invented here.

---

## 14. Historical / Change-Tracking Strategy

- OE-002 Domain Objects (Observation, Evidence, Decision, Judgment, Outcome, Knowledge Reference, Reasoning Trace) are already immutable and append-only — nothing changes there.
- New Atlas-generated components (Financial History, Valuation, Findings, Atlas Thesis) are **not** mutated in place. Each regeneration writes a new versioned record (`generated_at`-stamped); the "current" view reads the latest, but prior versions remain queryable — directly mirroring `DE-007`'s already-adopted `ComputedDirectionalRecommendation` → `HistoricalRecommendationSnapshot` pattern, extended to every component rather than invented fresh.
- The Change Log (§9) is the primary answer to "what did Atlas believe three months ago / what changed after the last earnings report / when did this risk first appear" — it is an explicit, queryable, append-only ledger, not something reconstructed by diffing snapshots after the fact.
- "What did the user believe when they bought the stock" is already answerable from existing immutable Decision/Judgment records at their `recorded_at` timestamp — no new mechanism needed, only surfaced next to the Change Log in the UI.

---

## 15. Ownership Boundaries: Atlas-Generated vs. User-Generated

| | Atlas Knowledge | Investor Knowledge |
|---|---|---|
| Can Atlas overwrite it on refresh? | Yes (new version written, old retained) | **Never** |
| Examples | Company Identity, Financial History, Valuation, Growth Analysis, Business Quality Findings, Risks, Strengths, Atlas Thesis, Monitoring Plan | Investor Thesis notes, Decisions, Outcomes (user-recorded), user-added Open Questions, reflections |
| Enforcement mechanism | Component versioning (§14) | OE-002 immutability (Decision/Judgment/Outcome) + a hard rule: no automated write path exists that edits `InvestorThesis` content — only append (new note) or explicit user edit |
| Governing precedent | `DE-007`'s ephemeral/persisted split | `APP-000` PP-003 / `ADR-003` Concept A vs. B distinction — Atlas Thesis is always Concept-A-shaped advisory content, never silently promoted into a Decision |

Atlas may **reference** the user's Investor Thesis when generating the Atlas Thesis or a Change Log entry ("You previously identified customer concentration as a risk; the latest filing does not change that") but this is a read, never a write, into Investor Knowledge — matching the brief's own example verbatim.

---

## 16. Proposed Implementation Stages

The brief's suggested 6-stage sequence is directionally right but under-weights the two items that actually block everything else: Watchlist Case-linkage and automatic triggering. Reordered accordingly:

- **Stage 1 — Foundation & Linkage.** Reconcile the two `Company` entities (§3.3); add `WatchlistItem`/Case-linkage to Watchlist, mirroring Portfolio's existing pattern; define the component data model (§4) and `DataProvenance` (§6) as code.
- **Stage 2 — Automatic Trigger + Company Data.** Event-driven Case creation + enrichment on Watchlist/Portfolio add, replacing the CLI-only trigger; populate Company Identity + Financial History via existing providers.
- **Stage 3 — Valuation & Growth.** Wire `atlas/analysis_engine/valuation/*` into the pipeline; add Growth Analysis as a thin derived layer.
- **Stage 4 — Atlas Analysis.** Business Quality Findings, Risks, Strengths, Open Questions (all genuinely new); wire Atlas Thesis to the existing Recommendation/Direction pipeline.
- **Stage 5 — UI.** Extend `InvestmentCasePage.tsx` and `PortfolioPage.tsx`; build the new Watchlist page.
- **Stage 6 — Monitoring.** Scheduler, earnings/filing detection, rate-limit-aware refresh queueing.
- **Stage 7 — Change Intelligence.** Change Log, materiality assessment, Today's Priorities/Discussions routing through the Atlas Priority Model.

---

## 17. Exact First Implementation Slice

**Build the smallest end-to-end proof of the core loop's first two arrows, using only already-existing provider code:**

> When a ticker is added to Watchlist *or* Portfolio and no Case yet exists for that (user, ticker) pair: auto-create a Case, link it (`WatchlistItem`/Holding → `case_id`), and synchronously trigger the existing `atlas/business_data_providers/{sec_edgar,alpha_vantage}.py` refresh to populate Company Identity + Financial History, tagged with `DataProvenance`. Surface the result in the existing `InvestmentCasePage.tsx`/analysis endpoint.

This deliberately excludes Valuation, Findings, Atlas Thesis, Monitoring Plan, and Change Log — it proves "Atlas already knows a lot about this company" using zero new analysis logic, only new *wiring*, and de-risks the two open architectural questions (Watchlist linkage shape, Company reconciliation) before any analysis code is written on top of them.

---

## 18. Test Strategy

- **Unit**: enrichment trigger (event → correct provider calls → correctly provenance-tagged Company/FinancialHistory records), idempotency (adding the same ticker twice does not duplicate the Case or re-fetch unnecessarily), failure-path (`Insufficient Evidence` marking when SEC EDGAR has no filer).
- **Integration**: full pipeline against `atlas/providers/mock.py`-style fakes (extend to `business_data_providers` if no mock exists there yet) — end-to-end Case creation through Company/Financial population.
- **Contract**: Watchlist→Portfolio move preserves `case_id` and all component history (a regression test asserting no data loss is the direct, automatable version of the brief's own "moved without losing accumulated knowledge" requirement).
- **Doctrine-compliance tests**: grep-style tests asserting no numeric confidence field is introduced (`UXD-R-064`), no second priority/ranking field is introduced outside the Atlas Priority Model (`PFINV-004`), and Atlas Thesis output never appears in a field also writable as a user Decision (Concept A/B separation, `ADR-003`) — cheap, high-value guardrails given how explicit these constraints are.
- **Change-detection tests**: given two synthetic Financial History snapshots, assert the correct Change Log entry and Open-Question status transition, and assert a same-value refresh produces *no* Change Log entry (new-information vs. materiality distinction, §9).

---

## 19. Risks and Unresolved Architectural Questions

1. **Alpha Vantage's 25/day free-tier limit is incompatible with "auto-trigger on every add" at any real scale.** Needs an explicit product/business decision (paid tier, queueing with visible "enrichment pending" state, or a different market-data provider) before Stage 2 ships broadly — not resolved by this design.
2. **SEC EDGAR only covers US filers.** International-company Investment Cases will be structurally thinner (Company Identity + market data only, no fundamentals) — this is a disclosed, honest limitation, not a defect, but should be stated in-product rather than silently discovered.
3. **Two provider abstractions currently coexist** (`atlas/providers/` legacy vs. `atlas/business_data_providers/` current). This design assumes the latter is canonical and the former should be deprecated, but that deprecation itself is a decision this document doesn't have authority to make unilaterally — flagged for explicit sign-off.
4. **Whether Company should ever become a 7th OE-002 Domain Object.** This design's position (no — it's reference data, not an epistemic act) is a judgment call with real weight given how much doctrinal effort went into justifying OE-002's closed six-object set; worth an explicit, separate confirmation rather than assuming this document's framing is automatically correct.
5. **Business Quality Findings have no existing implementation precedent anywhere in the repo** — this is the least de-risked component in the whole design and should be prototyped early (Stage 4) against a small number of real companies before being trusted to run automatically at scale.
6. **News ingestion is explicitly out of v1 scope** despite being named in the brief's Monitoring examples — no existing integration point was found, and adding one is a separate, sizeable scope of its own.

---

## 20. Must Existing Architecture or Doctrine Change First?

- **No OE-002 change is required.** The design deliberately fits inside its existing closed six-object model rather than proposing a seventh Domain Object (see §19.4 for the residual judgment call, not a required change).
- **A small, additive Watchlist domain extension is required** (Case-linkage) — non-breaking, but real, and should land in Stage 1 before anything else.
- **The two `Company` entities require an explicit reconciliation decision** — not a rewrite, but a stated boundary (§3.3) — before Stage 2's population logic is built against either one.
- **This design takes a dependency on `ATLAS_DECISION_ENGINE_DOCTRINE.md` and `DE-001/002/004/005/006/007/008` while they are still Draft and not `APP-000`-adopted.** This is a disclosed risk, not a blocker — the same way those DE documents already depend on each other pre-adoption — but formal `APP-000` adoption of the DE doctrine should be sequenced alongside, not after, this Engine's Stage 4, so the Atlas Thesis component isn't built against doctrine that could still change materially.
- **No change to `APP-000`, `ATLAS_CONSTITUTION.md`, `APP-002`, `UX-000`, or `ADR-003` is proposed or required** — this design is built to fit inside their existing constraints (no numeric confidence scale, no second priority model, no Concept A/B conflation), not to loosen any of them.

---

## 21. Recommended Next Coding Task

Implement the Stage 1 + first half of Stage 2 slice from §17, scoped narrowly:

1. Add `WatchlistItem` (ticker, `case_id`, `added_at`) to the Watchlist domain, mirroring the existing Portfolio holding→case-link pattern found in `atlas/alpha/portfolio/api/router.py`.
2. Write the Company reconciliation boundary: `atlas/models/entities.py::Company`/`FinancialHistory` becomes the canonical persisted record; `atlas/shared/entities.py::Company` becomes a read-only projection built from it at the API boundary (no behavior change to existing Portfolio code that already depends on the shared one).
3. Implement a single application service, `atlas/alpha/investment_case/application/enrich_case.py` (new), that: given a `case_id` and `ticker`, calls the existing `sec_edgar.py` + `alpha_vantage.py` providers, persists the results with `DataProvenance` tags, and is idempotent.
4. Wire that service to fire synchronously from both the existing Portfolio holding-creation path and the new Watchlist-item-creation path.
5. Add the test coverage from §18's Unit and Integration bullets for this slice only.

Explicitly **not** in this task: Valuation, Growth Analysis, Business Quality/Risk/Strength findings, Atlas Thesis wiring, Monitoring Plan, Change Log, or any UI changes — those follow in Stages 3-7 once this slice proves the trigger and data model are sound.

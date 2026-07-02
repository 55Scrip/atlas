# Atlas Legacy Engine Consolidation Plan

**Created:** 2026-07-01 (Sprint 74)  
**Updated:** 2026-07-02 (Sprint 98)  
**Status:** Active — Sprint 98 complete; WatchlistEngine active caller count is now **0**. `_answer_watchlist_review()` migrated to Blueprint-aligned Watchlist Intelligence. `WatchlistEngine` and `atlas/analysis/watchlist.py` retained for Sprint 99 deletion. Type-only `Watchlist`/`WatchlistItem` imports in 5 modules documented for later cleanup.

This document inventories all legacy Atlas modules, maps their current runtime
usage, documents overlap with Blueprint-aligned domains and capabilities, and
identifies the safest first migration target for Sprint 75.

---

## Background

Atlas has two parallel layers:

**Blueprint-aligned (current):**
- `atlas/domains/` — canonical concepts and contracts
- `atlas/capabilities/` — product capabilities
- `atlas/adapters/` — bridges between legacy and domain types
- `atlas/shared/` — immutable canonical entities
- `atlas/providers/` — opt-in market data (not called by demo)

**Legacy (compatibility, not for expansion):**
- All other top-level modules under `atlas/` — original working engines
- Remain functional and fully tested
- CLI commands exist for many; some are actively used

The goal of consolidation is to reduce the legacy surface area over time,
not to delete working code abruptly. Each migration must be testable,
deterministic, and leave the CLI interface unchanged or clearly improved.

---

## Legacy Module Inventory

### Group A — Thin Shims / Re-exports

| Module | Files | Lines | Description | Runtime CLI usage | Status |
|---|---|---|---|---|---|
| ~~`atlas/daily/`~~ | ~~2~~ | ~~43~~ | ~~Re-exports `atlas.daily_brief` under a stable path~~ | ~~`atlas daily brief`~~ | **Removed Sprint 75** |
| ~~`atlas/daily_brief/`~~ | ~~2~~ | ~~353~~ | ~~Legacy DailyBriefEngine (provider-dependent, 11 sub-engines)~~ | ~~`atlas daily brief` (deprecated Sprint 76)~~ | **Removed Sprint 77** |

`atlas/daily/` is a pure re-export shim. It imports from `atlas/daily_brief/`
and re-exports under the `atlas.daily` name. The only CLI consumer is
`atlas daily brief` (the legacy command). `atlas daily summary` is the
Blueprint-aligned equivalent and does not touch either module.

`atlas/daily_brief/` is the legacy engine that:
- imports `atlas.analysis.portfolio`, `atlas.analysis.watchlist`
- calls a `CompanyDataProvider` (mock or Yahoo)
- composes 11 sub-engines at runtime
- is distinct from `atlas/capabilities/daily_brief/` (the current engine)

**Note:** `atlas/domains/daily_brief/__init__.py` currently imports from
`atlas.daily_brief` — a boundary violation. The domain layer should not import
from legacy modules. This is a known tech debt item.

### Group B — Provider-Dependent Legacy Commands (medium risk)

| Module | Files | Lines | Description | Runtime CLI usage |
|---|---|---|---|---|
| `atlas/analysis/` | 18 | 1985 | Company, portfolio, watchlist, memory, scoring engines | `atlas analyze`, `atlas watchlist analyze` (deprecated 78), `atlas portfolio analyze` (deprecated 79), etc. |
| `atlas/home/` | 2 | 625 | AtlasHomeEngine — top-level dashboard aggregator | `atlas home` |
| `atlas/dashboard/` | 2 | 528 | DashboardEngine — weekly dashboard | `atlas dashboard show` |
| `atlas/intelligence/` | 2 | 470 | IntelligenceEngine — company intelligence | `atlas intelligence analyze` |
| `atlas/watchlist_review/` | 2 | 901 | WatchlistReviewEngine | `atlas watchlist review` |
| `atlas/portfolio_review/` | 2 | 635 | PortfolioReviewEngine | `atlas portfolio review` |
| `atlas/comparison/` | 2 | 1032 | ComparisonEngine — multi-company comparison | `atlas compare` |
| `atlas/themes/` | 2 | 569 | ThemeEngine | `atlas theme analyze` |
| `atlas/market/` | 3 | 793 | MarketSnapshot, MarketHealthEngine, MarketRegimeEngine | `atlas market analyze`, `atlas market health` |

All Group B modules:
- require a `CompanyDataProvider` at runtime (mock or Yahoo Finance)
- are provider-coupled by design
- have no Blueprint-aligned equivalent capability yet
- are functional and tested

### Group C — Self-Contained Analytics (targeted migration candidates)

| Module | Files | Lines | Description | Runtime CLI usage |
|---|---|---|---|---|
| `atlas/evidence/` | 2 | 563 | EvidenceQualityEngine — scores evidence claims | `atlas evidence assess` |
| `atlas/reasoning/` | 2 | 591 | ReasoningEngine — structured reasoning output | `atlas reason analyze` |
| `atlas/risk/` | 2 | 469 | RiskEngine, PositionSizingInput | ~~`atlas risk size`~~ (deprecated Sprint 83) |
| `atlas/risk_drift/` | 2 | 682 | RiskDriftEngine — position drift detection | `atlas risk-drift analyze` |
| `atlas/economics/` | 2 | 532 | EconomicSignalsEngine | `atlas economics analyze` |
| `atlas/language/` | 2 | 493 | AtlasLanguageEngine — output language calibration | Used internally by `daily_brief` |
| `atlas/monitoring/` | 2 | 626 | MonitoringEngine — alert generation | `atlas monitor` |
| `atlas/principles/` | 2 | 360 | PrinciplesEngine — investment principle check | `atlas principles check` |
| `atlas/suitability/` | 2 | 635 | SuitabilityEngine — investor suitability | `atlas suitability analyze` |

Group C modules are largely self-contained: they do not depend on providers,
and they operate on structured input rather than live data. Several are good
candidates for a future Blueprint-aligned capability wrapper.

### Group D — Infrastructure / Support (leave unchanged)

| Module | Files | Lines | Description | Notes |
|---|---|---|---|---|
| `atlas/services/` | 4 | 164 | Database service, company service, financial import | SQLite persistence layer |
| `atlas/memory/` | 4 | 219 | MemoryEngine, MemoryStore — ticker-level memory entries | Used by `atlas memory save/show/compare` |
| `atlas/profile/` | 2 | 294 | InvestorProfile — investor context | Used widely across legacy commands |
| `atlas/decision_journal/` | 2 | ~200 | Journal entry logging | Used by `atlas journal create/list/review` |
| `atlas/conversation/` | 2 | 526 | ConversationEngine — Q&A sessions | `atlas ask` |

Group D provides foundation infrastructure. No migration needed; these serve
specific functions with no Blueprint-aligned equivalent in scope.

---

## Runtime Dependency Map

```
atlas daily brief
→ atlas.daily (re-export shim)
→ atlas.daily_brief.DailyBriefEngine
→ atlas.analysis.portfolio.Portfolio (legacy portfolio type)
→ atlas.analysis.watchlist.Watchlist (legacy watchlist type)
→ providers (mock/yahoo — opt-in)
→ 11 sub-engines at runtime (home, portfolio_review, watchlist_review, ...)
status: legacy — Blueprint-aligned equivalent is `atlas daily summary`

atlas daily summary
→ atlas.capabilities.daily_brief.DailyBriefCapability
→ atlas.capabilities.daily_brief.json_loader (JSON input)
→ atlas.adapters.* (portfolio, watchlist, knowledge, research, company_analysis)
→ atlas.domains.portfolio (portfolio concentration)
→ NO providers called
status: current (Blueprint-aligned)

atlas portfolio summary
→ atlas.analysis.portfolio.Portfolio.from_json_file (legacy type)
→ atlas.adapters.portfolio.legacy_portfolio_to_domain_portfolio
→ atlas.domains.portfolio.portfolio_summary
status: partially migrated (uses adapter bridge)

atlas portfolio review
→ atlas.analysis.portfolio.Portfolio (legacy type)
→ atlas.adapters.portfolio (bridge)
→ atlas.domains.portfolio.portfolio_summary (domain)
→ atlas.portfolio_review.PortfolioReviewEngine (legacy)
status: partially migrated (domain summary used; review engine still legacy)

atlas portfolio analyze
→ atlas.analysis.portfolio.Portfolio (legacy type)
→ atlas.adapters.portfolio (bridge)
→ atlas.domains.portfolio.portfolio_summary (domain)
status: partially migrated

atlas analyze <ticker>
→ providers (mock/yahoo — opt-in)
→ atlas.analysis.engine.AtlasInvestmentEngine
status: legacy — no Blueprint-aligned equivalent

atlas home
→ providers (mock/yahoo — opt-in)
→ atlas.home.AtlasHomeEngine (orchestrates many sub-engines)
status: legacy — no Blueprint-aligned equivalent

atlas watchlist intelligence
→ atlas.capabilities.watchlist_intelligence.WatchlistIntelligenceEngine
→ atlas.adapters.watchlist, atlas.adapters.knowledge
→ NO providers called
status: current (Blueprint-aligned)

atlas watchlist analyze
→ DEPRECATED (Sprint 78) — prints deprecation message, exits 0, no engine called
status: deprecated — no WatchlistEngine call, no provider call

atlas watchlist review
→ atlas.watchlist_review.WatchlistReviewEngine (legacy)
→ providers (mock/yahoo — opt-in)
status: legacy

atlas company-analysis export
→ atlas.capabilities.company_analysis.CompanyAnalysisEngine
→ atlas.adapters.knowledge, atlas.adapters.research_input
→ NO providers called
status: current (Blueprint-aligned)

atlas discovery export
→ atlas.capabilities.discovery.DiscoveryEngine
→ atlas.adapters.*
→ NO providers called
status: current (Blueprint-aligned)
```

---

## Blueprint Overlap Summary

| Legacy module | Blueprint equivalent | Overlap status |
|---|---|---|
| `atlas/daily/` + `atlas/daily_brief/` | `atlas/capabilities/daily_brief/` | Full overlap — two parallel implementations. CLI command `atlas daily brief` uses legacy; `atlas daily summary` uses Blueprint. |
| `atlas/analysis/portfolio.py` | `atlas/domains/portfolio/` + `atlas/adapters/portfolio.py` | Partial — Portfolio type bridged via adapter. Domain summary is the current path. |
| `atlas/analysis/watchlist.py` | `atlas/capabilities/watchlist_intelligence/` | Deprecated — `atlas watchlist analyze` deprecated Sprint 78; `WatchlistEngine` still used by monitoring, decision, intelligence, conversation, watchlist_review legacy engines. |
| `atlas/analysis/company_analysis.py` | `atlas/capabilities/company_analysis/` | Partial — new capability path exists for export pipeline. |
| `atlas/domains/daily_brief/` | `atlas/capabilities/daily_brief/` | **Boundary violation:** `atlas/domains/daily_brief/__init__.py` imports from `atlas.daily_brief` (legacy). The domain layer should not depend on legacy modules. |

### Boundary Violation Identified

`atlas/domains/daily_brief/__init__.py` imports from `atlas.daily_brief`:

```python
from atlas.daily_brief import DailyBriefEngine, DailyBriefInput, DailyBriefOutput
```

This makes a Blueprint domain depend on a legacy module — the reverse of the
intended dependency direction. No CLI command or test currently imports from
`atlas.domains.daily_brief` directly (confirmed by grep), so the violation
is dormant but should be resolved when the legacy daily_brief module is
eventually retired.

---

## Provider Safety Confirmation

- Providers (`atlas/providers/`) are never imported by:
  - `atlas/domains/`
  - `atlas/capabilities/`
  - `atlas/adapters/`
  - demo script (`scripts/run_daily_brief_demo.sh`)
  - release verification script (`scripts/verify_release_candidate.sh`)
- Providers are only called from legacy CLI commands that explicitly pass
  `--provider mock` or `--provider yahoo` at the command line
- Default for all legacy provider commands is `--provider mock`
- `atlas daily summary` (current path) makes zero provider calls

Provider safety: **confirmed**.

---

## Sprint 100 — Post-WatchlistEngine Architecture Checkpoint COMPLETED

### Completed: Deleted symbol audit; type-only import inventory; type migration plan created

**Sprint 100 result:**

**Goal:** Verify WatchlistEngine deletion state; audit remaining `Watchlist`/`WatchlistItem` type-only
imports; document recommended migration destination; create `docs/WatchlistTypeMigrationPlan.md`;
add guardrail tests for deleted symbols.

**Changes made:**
1. Added 6 guardrail tests to `tests/test_watchlist_analyze_deprecation.py`:
   - `test_watchlist_analysis_is_not_importable`
   - `test_watchlist_recommendation_is_not_importable`
   - `test_render_watchlist_analysis_is_not_importable`
   - `test_watchlist_module_contains_only_type_models` (source scan for all forbidden symbols)
   - `test_watchlist_module_exports_watchlist_and_item` (confirms Watchlist/WatchlistItem still present)
2. Created `docs/WatchlistTypeMigrationPlan.md` with:
   - Full type-only import inventory (7 production modules, 5 test files)
   - Documentation of the two distinct `Watchlist` families (legacy CLI input vs canonical entity)
   - Recommended destination: `WatchlistInput`/`WatchlistInputItem` in `atlas/capabilities/watchlist_intelligence/`
   - Step-by-step Sprint 101 migration sequence
   - Risk assessment
3. Updated `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`,
   `docs/DecisionLog.md`, `docs/WatchlistEngineMigrationPlan.md`.

**WatchlistEngine deletion audit — all confirmed:**

| Symbol | Status |
|---|---|
| `WatchlistEngine` | Deleted Sprint 99 — not importable ✓ |
| `WatchlistAnalysis` | Deleted Sprint 99 — not importable ✓ |
| `WatchlistSignal` (legacy analysis module) | Deleted Sprint 99 — not importable from `atlas.analysis.watchlist` ✓ |
| `WatchlistRecommendation` | Deleted Sprint 99 — not importable ✓ |
| `render_watchlist_analysis` | Deleted Sprint 99 — not importable ✓ |
| `Watchlist` | Retained — type-only, still importable from `atlas.analysis.watchlist` ✓ |
| `WatchlistItem` | Retained — type-only, still importable from `atlas.analysis.watchlist` ✓ |

**Note:** `WatchlistSignal` in `atlas/capabilities/watchlist_intelligence/` is a **different class** —
a Blueprint capability type used for explainable prioritisation signals. It was never part of the
legacy `atlas.analysis.watchlist` module and is unaffected by the Sprint 99 deletion.

**Tests: 1125 passing (3 skipped). Demo passed. Release verification green.**

**Sprint 101 target:** Move `Watchlist`/`WatchlistItem` to `atlas/capabilities/watchlist_intelligence/`
as `WatchlistInput`/`WatchlistInputItem`; delete `atlas/analysis/watchlist.py`.

---

## Sprint 99 — WatchlistEngine Deletion COMPLETED

### Completed: `WatchlistEngine` deleted; `atlas/analysis/watchlist.py` slimmed to types only

**Sprint 99 result:**

**Goal:** Delete `WatchlistEngine` now that all five callers were retired in Sprints 93–98. Resolve type-only import dependencies. Delete `tests/test_watchlist.py`. Flip guardrails.

**Changes made:**
1. Slimmed `atlas/analysis/watchlist.py` from ~277 lines to 33 lines — removed `WatchlistEngine`, `WatchlistAnalysis`, `WatchlistSignal`, `WatchlistRecommendation`, `render_watchlist_analysis`, and all private helpers. Removed engine-only imports (`AtlasInvestmentEngine`, `CompanyDataProvider`, `Enum`). Retained `Watchlist` and `WatchlistItem` (used by 7 production modules as input types).
2. Cleaned `atlas/analysis/__init__.py` — removed re-exports of `WatchlistEngine`, `WatchlistAnalysis`, `WatchlistRecommendation`, `WatchlistSignal`, `render_watchlist_analysis`. Retained `Watchlist`, `WatchlistItem`.
3. Deleted `tests/test_watchlist.py` — only tested `WatchlistEngine.analyze()` and `render_watchlist_analysis()`, both removed.
4. Flipped guardrails in `tests/test_watchlist_analyze_deprecation.py`:
   - `test_watchlist_engine_remains_importable` → `test_watchlist_engine_is_not_importable` (asserts `WatchlistEngine` not in module)
   - `test_watchlist_engine_module_remains_on_disk` → `test_watchlist_engine_is_deleted` (asserts `WatchlistEngine` not in source)
5. Updated `atlas/cli/deprecations.py` stale `removal_criteria` string to reflect Sprint 99 deletion.
6. Updated all 5 docs + `WatchlistEngineMigrationPlan.md` (marked DELETION COMPLETE).

**Why file not fully deleted:**
`atlas/analysis/watchlist.py` cannot be fully deleted because 7 production modules import `Watchlist`/`WatchlistItem` as input types (`atlas/cli/main.py`, `atlas/decision/decision_context.py`, `atlas/monitoring/engine.py`, `atlas/watchlist_review/engine.py`, `atlas/home/engine.py`, `atlas/intelligence/engine.py`, `atlas/conversation/engine.py`). `atlas/shared/entities.py` has a `Watchlist` class but with a different structure (`tickers: tuple[str, ...]` vs `items: tuple[WatchlistItem, ...]`). Full file deletion deferred to Sprint 100+ once type migration is complete.

**WatchlistEngine status after Sprint 99:**
- `WatchlistEngine` class: **DELETED**
- `atlas/analysis/watchlist.py`: retained as type-only module (33 lines)
- Active caller count: 0 (unchanged from Sprint 98)
- 1119 tests passing (3 skipped). All guardrails green.

---

## Sprint 98 Migration Target — COMPLETED

### Completed: WatchlistEngine removed from `atlas/conversation/engine.py`; active caller count 1 → 0

**Sprint 98 result:**

**Goal:** Migrate `_answer_watchlist_review()` from `WatchlistEngine / WatchlistAnalysis` to `WatchlistIntelligenceEngine / WatchlistIntelligenceReport`; reduce active WatchlistEngine caller count to zero.

**Changes made:**
1. Removed `WatchlistEngine` import from `atlas/conversation/engine.py`; added `WatchlistIntelligenceEngine`, `WatchlistIntelligenceInput`, `WatchlistItem as IntelligenceWatchlistItem`
2. Removed `watchlist_engine: WatchlistEngine | None = None` from `ConversationEngine.__init__`
3. Removed `self.watchlist_engine = watchlist_engine or WatchlistEngine(self.investment_engine)`
4. Rewrote `_answer_watchlist_review()`: now takes no `provider` argument; calls `WatchlistIntelligenceEngine().analyze(WatchlistIntelligenceInput(...))` using established conversion pattern
5. Updated `_answer_watchlist_review()` dispatch in `answer()` to remove `provider` argument
6. Output framing changed from score-ranking to research-attention (documented intentional change):
   - `short_answer`: "Atlas ranks X first in Y." → "Atlas highlights X for research attention in Y."
   - `supporting_reasoning`: `strongest_opportunity/cheapest_valuation/highest_quality_company` fields → `companies_needing_attention[0].detail / evidence_gaps[0].detail / observations[0].detail / overview`
   - `engines_used`: `("Watchlist Engine", "Investment Engine")` → `("Watchlist Intelligence Engine",)`
   - `confidence`: 80 → 70 (matching Blueprint monitoring pattern)
7. `WATCHLIST_ENGINE_CALLERS` frozen set reduced to empty tuple
8. Replaced Sprint 97 "remains a caller" test with Sprint 98 `test_conversation_engine_does_not_import_watchlist_engine` guardrail
9. `test_watchlist_engine_active_callers_remain` replaced with `test_watchlist_engine_active_callers_are_zero`
10. Updated `test_conversation_engine.py` WATCHLIST_REVIEW assertions: "Watchlist Engine" → "Watchlist Intelligence Engine"; added "highlights" phrase check
11. Updated all 5 docs + `WatchlistEngineMigrationPlan.md`

**Output change (documented — intentional):**
`atlas conversation` WATCHLIST_REVIEW response no longer uses score-ranking language. Output now uses research-attention framing, consistent with Blueprint principle that watchlist intelligence surfaces research gaps and coverage priorities rather than ranked scores. Behavior remains deterministic, local-only, provider-free.

**WatchlistEngine active caller count:**
- Before Sprint 98: 1 (conversation only)
- After Sprint 98: **0** — no active runtime callers remain
- `WatchlistEngine` and `atlas/analysis/watchlist.py` retained for Sprint 99 deletion verification
- `Watchlist`/`WatchlistItem` type-only imports remain in 5 modules — cleanup deferred

**Engine deletion criteria (Sprint 99):**
1. Run full deletion eligibility audit
2. Verify `test_watchlist_engine_callers_are_exactly_the_known_set` passes with empty set
3. Resolve `Watchlist`/`WatchlistItem` type-only imports (5 modules)
4. Migrate or remove `tests/test_watchlist.py` direct engine tests
5. Delete `atlas/analysis/watchlist.py` and `atlas/analysis/__init__.py` re-exports
6. Verify demo, release verification, and full test suite green

---

## Sprint 97 Migration Target — COMPLETED

### Completed: WatchlistEngine removed from `atlas/intelligence/engine.py`; caller count 2 → 1

**Sprint 97 result:**

**Goal:** Replace `atlas/intelligence/engine.py` direct `WatchlistEngine` dependency with Blueprint-aligned Watchlist Intelligence data; update `IntelligenceReport` to carry `WatchlistIntelligenceReport` instead of `WatchlistAnalysis`.

**Changes made:**
1. Removed `WatchlistEngine`, `WatchlistAnalysis` imports from `atlas/intelligence/engine.py`
2. Added `WatchlistIntelligenceEngine`, `WatchlistIntelligenceInput`, `WatchlistItem as IntelligenceWatchlistItem` from `atlas.capabilities.watchlist_intelligence`
3. Removed `watchlist_engine: WatchlistEngine | None = None` from `IntelligenceEngine.__init__`
4. Renamed `_optional_watchlist_analysis()` → `_optional_watchlist_intelligence()`; rewrote to use `WatchlistIntelligenceEngine().analyze()` (same conversion pattern as Sprint 95) — no provider argument needed
5. Updated `_confidence()` signature: `watchlist_analysis: WatchlistAnalysis | None` → `watchlist_intelligence: WatchlistIntelligenceReport | None`
6. Renamed `IntelligenceReport.watchlist_analysis` → `watchlist_intelligence` with type `WatchlistIntelligenceReport | None`
7. Removed `watchlist_engine=self.watchlist_engine` from `IntelligenceEngine(...)` construction in `atlas/conversation/engine.py` (parameter no longer accepted)
8. Updated `WATCHLIST_ENGINE_CALLERS` to 1 entry (removed intelligence)
9. Updated Sprint 96 "remains a caller" test → Sprint 97 `test_intelligence_engine_does_not_import_watchlist_engine` guardrail
10. Updated exclusivity guardrail comment (caller set now 1)

**Output change (documented):**
`IntelligenceReport.watchlist_intelligence` now carries `WatchlistIntelligenceReport | None` instead of `WatchlistAnalysis | None`. No user-visible rendering change: `render_intelligence_report()` never read any `WatchlistAnalysis` field content. Confidence bonus (+3 for non-None watchlist) is preserved unchanged. Provider no longer passed to watchlist analysis path — no provider boundary broadening.

**WatchlistEngine caller count:**
- Before Sprint 97: 2 (intelligence, conversation)
- After Sprint 97: **1** (conversation only)
- `atlas/intelligence/engine.py` no longer imports or instantiates WatchlistEngine
- `IntelligenceReport.watchlist_intelligence` holds `WatchlistIntelligenceReport | None`

**Engine deletion criteria (deferred to Sprint 98/99):**
1. Retire or migrate `atlas/conversation/` WatchlistEngine usage
2. Once conversation is retired, evaluate `Watchlist`/`WatchlistItem` type-only imports
3. Once all active imports are retired, `atlas/analysis/watchlist.py` can be deleted

---

## Sprint 96 Audit — COMPLETE (no runtime migration)

### Audit: Final WatchlistEngine caller migration plan — caller count remains 2

**Sprint 96 result:**

**Goal:** Audit the final two WatchlistEngine callers (`atlas/intelligence/`, `atlas/conversation/`), document runtime flows, choose migration order, and write `docs/WatchlistEngineMigrationPlan.md`.

**Findings:**

`atlas/intelligence/engine.py` — LOW migration risk:
- `WatchlistAnalysis` is used only as a confidence bonus check (`is not None` → +3) and a stored passthrough field in `IntelligenceReport.watchlist_analysis`
- No rendering function in `render_intelligence_report()` or any downstream caller reads `WatchlistAnalysis` content
- Conversion pattern from Sprint 95 applies directly
- `ConversationEngine.__init__` currently passes `watchlist_engine=self.watchlist_engine` into `IntelligenceEngine(...)` — this kwarg must be removed in Sprint 98 once Sprint 97 drops the parameter

`atlas/conversation/engine.py` — MEDIUM-HIGH migration risk:
- `_answer_watchlist_review()` reads six specific `WatchlistAnalysis` fields (`strongest_opportunity.ticker`, `strongest_opportunity.reasoning`, `cheapest_valuation.reasoning`, `highest_quality_company.reasoning`, `final_atlas_view`, `name`)
- Three fields (`strongest_opportunity`, `cheapest_valuation`, `highest_quality_company`) have no 1:1 Blueprint equivalents in `WatchlistIntelligenceReport`
- Semantic shift documented: score-ranked → research-gap-driven
- `WATCHLIST_REVIEW` response text will change materially — "Atlas ranks X first" → "Atlas highlights X for research attention"

**Migration order chosen:** intelligence first (Sprint 97), conversation second (Sprint 98)
**Rationale:** Intelligence has zero user-visible output from WatchlistAnalysis content; conversation has six. Intelligence also creates a dependency coupling — Sprint 97 must remove `watchlist_engine` from `IntelligenceEngine.__init__`, which Sprint 98 must then clean up in `ConversationEngine.__init__`.

**Plan document:** `docs/WatchlistEngineMigrationPlan.md` created

**WatchlistEngine caller count:**
- Before Sprint 96: 2 (intelligence, conversation)
- After Sprint 96: **2** (unchanged — audit sprint only)

**Sprint 97 target:** Migrate `atlas/intelligence/engine.py`; rename `IntelligenceReport.watchlist_analysis` → `watchlist_intelligence`; remove `watchlist_engine` from `IntelligenceEngine.__init__`
**Sprint 98 target:** Migrate `atlas/conversation/engine.py`; rewrite `_answer_watchlist_review()`; evaluate WatchlistEngine deletion readiness

---

## Sprint 95 Migration Target — COMPLETED

### Completed: WatchlistEngine removed from `atlas/decision/decision_engine.py`; caller count 3 → 2

**Sprint 95 result:**

**Goal:** Replace `atlas/decision/decision_engine.py` direct `WatchlistEngine` dependency with Blueprint-aligned Watchlist Intelligence data; update `DecisionResult` to carry `WatchlistIntelligenceReport` instead of `WatchlistAnalysis`.

**Changes made:**
1. Removed `WatchlistEngine` and `WatchlistAnalysis` imports from `atlas/decision/decision_engine.py`
2. Added `WatchlistIntelligenceEngine`, `WatchlistIntelligenceInput`, `WatchlistItem as IntelligenceWatchlistItem` imports from `atlas.capabilities.watchlist_intelligence`
3. Removed `watchlist_engine: WatchlistEngine | None` parameter from `AtlasDecisionEngine.__init__`
4. Renamed `_analyze_watchlist()` to `_watchlist_intelligence()`; rewrote to use `WatchlistIntelligenceEngine().analyze()` (same conversion pattern as Sprint 93)
5. Updated `_confidence()` and `_reasoning()` signatures: `watchlist_analysis: WatchlistAnalysis | None` → `watchlist_intelligence: WatchlistIntelligenceReport | None`
6. Updated `_reasoning()`: replaced `watchlist_analysis.strongest_opportunity.ticker` / `watchlist_analysis.final_atlas_view` with `report.companies_needing_attention[0].ticker` / `report.overview`
7. Updated `atlas/decision/decision_result.py`: replaced `WatchlistAnalysis` with `WatchlistIntelligenceReport`; renamed field `watchlist_analysis` → `watchlist_intelligence`
8. Removed `watchlist_engine=self.watchlist_engine` from `AtlasDecisionEngine(...)` construction in `atlas/intelligence/engine.py`
9. Updated `WATCHLIST_ENGINE_CALLERS` to 2 entries (removed decision)
10. Added `test_decision_engine_does_not_import_watchlist_engine` guardrail
11. Updated exclusivity guardrail comment (caller set now 2)
12. Updated `tests/test_decision_engine.py`: `result.watchlist_analysis` → `result.watchlist_intelligence`

**Output change (documented):**
`atlas decide` reasoning now uses `WatchlistIntelligenceReport.overview` and `companies_needing_attention[0].ticker` (or `observations[0].ticker`) instead of legacy `WatchlistAnalysis.final_atlas_view` and `strongest_opportunity.ticker`. Decision confidence score unchanged (+4 bonus when watchlist present). Output remains deterministic, local-only, provider-free.

**WatchlistEngine caller count:**
- Before Sprint 95: 3 (intelligence, decision, conversation)
- After Sprint 95: **2** (intelligence, conversation)
- `atlas/decision/decision_engine.py` no longer imports or instantiates WatchlistEngine
- `DecisionResult.watchlist_intelligence` now carries `WatchlistIntelligenceReport | None`

**Engine deletion criteria (deferred to Sprint 96+):**
1. Retire or migrate `atlas/intelligence/` WatchlistEngine usage
2. Retire or migrate `atlas/conversation/` WatchlistEngine usage
3. Once both callers are retired, `atlas/analysis/watchlist.py` can be deleted

---

## Sprint 94 Migration Target — COMPLETED

### Completed: WatchlistEngine removed from `atlas/watchlist_review/engine.py`; caller count 4 → 3

**Sprint 94 result:**

**Goal:** Replace `atlas/watchlist_review/engine.py` direct `WatchlistEngine` dependency with Blueprint-aligned Watchlist Intelligence data; remove `snapshot_watchlist_from_analysis` from `MonitoringEngine` if no longer needed.

**Changes made:**
1. Removed `WatchlistEngine` from import in `atlas/watchlist_review/engine.py` (`Watchlist`, `WatchlistItem` retained — still needed)
2. Removed `watchlist_engine: WatchlistEngine | None` parameter from `WatchlistReviewEngine.__init__`
3. In `WatchlistReviewEngine.review()`: removed `watchlist_analysis` computation entirely; replaced `monitoring_engine.snapshot_watchlist_from_analysis(watchlist_analysis)` with `monitoring_engine.snapshot_watchlist(supported_watchlist)` (Blueprint-aligned, Sprint 93)
4. `_review_items(watchlist_analysis=None, ...)` — company items default to `base_score=45` instead of `atlas_score`
5. Removed `snapshot_watchlist_from_analysis()` from `MonitoringEngine` — no runtime callers remain after step 3
6. Removed `WatchlistAnalysis` import from `atlas/monitoring/engine.py` — no longer needed
7. Updated `WATCHLIST_ENGINE_CALLERS` to 3 entries (removed watchlist_review)
8. Added `test_watchlist_review_engine_does_not_import_watchlist_engine` guardrail
9. Removed `test_monitoring_engine_snapshot_watchlist_from_analysis_uses_legacy_analysis` (method deleted)
10. Updated exclusivity guardrail comment (caller set now 3)

**Output change (documented):**
`atlas watchlist review` item `relevance_score` now uses `base_score=45` instead of `atlas_score` from WatchlistEngine. Items without WatchlistEngine scores have less differentiated rankings. Monitoring snapshot in review now uses Blueprint intelligence signals (confidence=70) rather than legacy analysis signals (confidence=80). Output remains deterministic, local-only, provider-free.

**WatchlistEngine caller count:**
- Before Sprint 94: 4 (intelligence, decision, watchlist_review, conversation)
- After Sprint 94: **3** (intelligence, decision, conversation)
- `atlas/watchlist_review/engine.py` no longer imports or instantiates WatchlistEngine
- `MonitoringEngine.snapshot_watchlist_from_analysis()` removed — bridge method no longer needed

**Engine deletion criteria (deferred to Sprint 95+):**
1. Retire or migrate `atlas/decision/` WatchlistEngine usage
2. Retire or migrate `atlas/intelligence/` WatchlistEngine usage
3. Retire or migrate `atlas/conversation/` WatchlistEngine usage
4. Once all three callers are retired, `atlas/analysis/watchlist.py` can be deleted

---

## Sprint 93 Migration Target — COMPLETED

### Completed: WatchlistEngine removed from `atlas/monitoring/engine.py`; caller count 5 → 4

**Sprint 93 result:**

**Goal:** Replace the `atlas monitor watchlist` CLI path with Blueprint-aligned Watchlist Intelligence data, removing `WatchlistEngine` from `monitoring/engine.py`.

**Changes made:**
1. Removed `WatchlistEngine` import from `atlas/monitoring/engine.py`
2. Added imports: `WatchlistIntelligenceEngine`, `WatchlistIntelligenceInput`, `WatchlistItem as IntelligenceWatchlistItem` from `atlas.capabilities.watchlist_intelligence`
3. Removed `watchlist_engine: WatchlistEngine | None` parameter from `MonitoringEngine.__init__`
4. Rewrote `snapshot_watchlist(watchlist, provider=None)` to use `WatchlistIntelligenceEngine.analyze()` — converts legacy `Watchlist` tickers to minimal `WatchlistIntelligenceInput` items, builds `MonitoringSnapshot` from research-driven signals (items needing attention, evidence gaps, open questions)
5. Made `provider` parameter optional in `snapshot_watchlist` and `monitor_watchlist` — no longer needed (Blueprint path is provider-free)
6. `snapshot_watchlist_from_analysis(analysis)` retained — still called by `atlas/watchlist_review/engine.py` for its own direct WatchlistEngine analysis result
7. Updated `atlas/watchlist_review/engine.py` to call `MonitoringEngine()` without `watchlist_engine=` arg (no longer accepted)
8. Updated `WATCHLIST_ENGINE_CALLERS` to 4 entries (removed monitoring)
9. Added `test_monitoring_engine_does_not_import_watchlist_engine` guardrail
10. Added `test_monitoring_engine_snapshot_watchlist_uses_blueprint_intelligence`
11. Added `test_monitoring_cli_monitors_watchlist` CLI behavior test

**Output change (documented):**
`atlas monitor watchlist` signals changed from company-score-based (atlas_score, valuation, quality from WatchlistEngine) to research-coverage-based (items needing attention, evidence gaps, open questions from WatchlistIntelligenceEngine). Output remains deterministic, local-only, provider-free. No recommendation language.

**WatchlistEngine caller count:**
- Before Sprint 93: 5 (intelligence, decision, monitoring, watchlist_review, conversation)
- After Sprint 93: **4** (intelligence, decision, watchlist_review, conversation)
- `atlas/monitoring/engine.py` no longer imports or instantiates WatchlistEngine

**Engine deletion criteria (deferred to Sprint 94+):**
1. Retire or migrate `atlas/intelligence/` WatchlistEngine usage
2. Retire or migrate `atlas/decision/` WatchlistEngine usage
3. Migrate `atlas/watchlist_review/` direct WatchlistEngine to Blueprint-aligned data → unblocks monitoring's `snapshot_watchlist_from_analysis` cleanup too
4. Retire or migrate `atlas/conversation/` WatchlistEngine usage
5. Once all four callers are retired, `atlas/analysis/watchlist.py` can be deleted

---

## Sprint 92 Migration Target — COMPLETED

### Completed: WatchlistEngine double-run eliminated; caller exclusivity guardrail added

**Sprint 92 result:**

**Audit findings:**
- `atlas/monitoring/engine.py`: `WatchlistEngine` is imported and used in `snapshot_watchlist()` and `monitor_watchlist()`. These methods power the active `atlas monitor watchlist` CLI command. Cannot retire.
- `atlas/watchlist_review/engine.py`: `WatchlistEngine` is imported and instantiated. Powers the active `atlas watchlist review` CLI command. Cannot retire.
- **Key finding:** `WatchlistReviewEngine.review()` was running `WatchlistEngine.analyze()` twice on the same input — once directly, and once again inside `MonitoringEngine.snapshot_watchlist()`. Redundant.

**Changes made:**
1. Added `snapshot_watchlist_from_analysis(analysis: WatchlistAnalysis) -> MonitoringSnapshot` to `MonitoringEngine` — builds a `MonitoringSnapshot` from a pre-computed `WatchlistAnalysis` without calling `WatchlistEngine` again
2. Refactored `MonitoringEngine.snapshot_watchlist()` to delegate to `snapshot_watchlist_from_analysis()` — eliminating code duplication
3. Updated `WatchlistReviewEngine.__init__` to share the same `WatchlistEngine` instance with its internal `MonitoringEngine(watchlist_engine=self.watchlist_engine)` — one object instead of two
4. Updated `WatchlistReviewEngine.review()` to call `monitoring_engine.snapshot_watchlist_from_analysis(watchlist_analysis)` — eliminates the redundant second WatchlistEngine run per review
5. Added `test_watchlist_engine_callers_are_exactly_the_known_set` guardrail — prevents new WatchlistEngine callers from being added without review
6. Added `test_monitoring_engine_snapshot_watchlist_from_analysis_matches_snapshot_watchlist`

**WatchlistEngine caller count:**
- Before Sprint 92: 5 (intelligence, decision, monitoring, watchlist_review, conversation)
- After Sprint 92: 5 (unchanged — both monitoring and watchlist_review still require WatchlistEngine for active CLI commands)

**Result:** Redundant double WatchlistEngine invocation in `review()` eliminated. Caller count frozen and guarded by exclusivity test.

**Engine deletion criteria (deferred to Sprint 93+):**
1. Retire or migrate `atlas/intelligence/` to use Blueprint-aligned watchlist capability
2. Retire or migrate `atlas/decision/` WatchlistEngine usage
3. Replace `atlas/monitoring/` watchlist snapshot methods with Blueprint-aligned data source
4. Replace `atlas/watchlist_review/` direct WatchlistEngine with Blueprint-aligned capability
5. Retire or migrate `atlas/conversation/` WatchlistEngine usage
6. Once all five callers are retired, `atlas/analysis/watchlist.py` can be deleted

---

## Sprint 91 Migration Target — COMPLETED

### Completed: `atlas watchlist analyze` command body retired; engine retained

**Sprint 91 result:**
- `atlas watchlist analyze` command body removed from `atlas/cli/main.py` — command no longer callable
- `atlas watchlist analyze` moved from active `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`
- Active `_REGISTRY` is now empty — CLI deprecated command retirement plan complete
- `atlas.analysis.watchlist` engine **intentionally retained** — confirmed active callers:
  - `atlas/intelligence/engine.py` — imports and instantiates `WatchlistEngine`
  - `atlas/decision/decision_engine.py` — imports and instantiates `WatchlistEngine`
  - `atlas/monitoring/engine.py` — imports and instantiates `WatchlistEngine`
  - `atlas/watchlist_review/engine.py` — imports and instantiates `WatchlistEngine`
  - `atlas/conversation/engine.py` — imports and instantiates `WatchlistEngine`
- Tests updated: `test_watchlist_analyze_deprecation.py` rewritten as retirement test; includes engine caller-presence assertions for all five callers; `test_active_deprecated_registry_is_now_empty` confirms the registry is empty
- 1116 tests passing (3 skipped — parametrized tests with empty EXPECTED_COMMANDS, by design)

**Engine deletion criteria (deferred to Sprint 92+):**
1. Retire or migrate `atlas/intelligence/` to use Blueprint-aligned watchlist capability
2. Retire or migrate `atlas/decision/` WatchlistEngine usage
3. Retire or migrate `atlas/monitoring/` WatchlistEngine usage
4. Retire or migrate `atlas/watchlist_review/` WatchlistEngine usage
5. Retire or migrate `atlas/conversation/` WatchlistEngine usage
6. Once all five callers are retired, `atlas/analysis/watchlist.py` can be deleted

---

## Sprint 90 Migration Target — COMPLETED

### Completed: `atlas portfolio review` command body retired; engine retained

**Sprint 90 result:**
- `atlas portfolio review` command body removed from `atlas/cli/main.py` — command no longer callable
- `atlas portfolio review` moved from active `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`
- `atlas.portfolio_review` engine **intentionally retained** — confirmed active caller:
  - `atlas/home/engine.py` (`AtlasHomeEngine`) — imports `PortfolioReviewEngine` and `PortfolioReviewInput`; instantiates `PortfolioReviewEngine()` at runtime
- `atlas.domains.portfolio.review.PortfolioReviewEngine` is a separate Blueprint-aligned class; not affected
- Tests updated: `test_portfolio_review_deprecation.py` rewritten as retirement test; includes `atlas/home/engine.py` caller-presence assertion; `test_portfolio_review_migration.py` updated with all CLI tests asserting `exit_code != 0`; legacy engine and adapter tests retained
- 1111 tests passing

**Engine deletion criteria (deferred):**
1. Retire or migrate `atlas/home/engine.py` (`AtlasHomeEngine`) to use `atlas.domains.portfolio.review.PortfolioReviewEngine` instead of the legacy `atlas.portfolio_review.PortfolioReviewEngine`
2. Confirm no other callers of `atlas.portfolio_review` remain
3. Once confirmed, `atlas.portfolio_review/` module can be deleted

---

## Sprint 89 Migration Target — COMPLETED

### Completed: `atlas portfolio analyze` command body retired; engine retained

**Sprint 89 result:**
- `atlas portfolio analyze` command body removed from `atlas/cli/main.py` — command no longer callable
- `atlas portfolio analyze` moved from active `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`
- `atlas/analysis/portfolio` engine **intentionally retained** — confirmed active callers:
  - `atlas/intelligence/engine.py`
  - `atlas/conversation/engine.py`
  - `atlas/decision/decision_engine.py`
  - `atlas/dashboard/engine.py`
  - `atlas/reasoning/engine.py`
  - `atlas/home/engine.py`
  - `atlas/suitability/engine.py`
  - `atlas/risk_drift/engine.py`
  - `atlas/monitoring/engine.py`
  - `atlas/portfolio_review/engine.py`
  - Plus `atlas/adapters/portfolio.py`, `atlas/providers/`, and several test files
- Engine deletion deferred until all those callers are retired
- Tests updated: `test_portfolio_analyze_deprecation.py` rewritten as retirement test; includes engine caller-presence assertions; `test_portfolio_analyze_migration.py` updated to assert `exit_code != 0` for all CLI tests
- 1106 tests passing

**Engine deletion criteria (deferred):**
1. All 10+ production callers of `atlas.analysis.portfolio` must stop importing `Portfolio`, `PortfolioAnalysis`, or `PortfolioIntelligenceEngine`
2. `atlas portfolio review` command body and `PortfolioReviewEngine` must also be retired (uses `Portfolio`)
3. `atlas/adapters/portfolio.py` bridge must be migrated or removed

---

## Sprint 88 Migration Target — COMPLETED

### Completed: `atlas risk size` command body retired; engine retained

**Sprint 88 result:**
- `atlas risk size` command body removed from `atlas/cli/main.py` — command no longer callable
- `atlas risk size` moved from active `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`
- `atlas/risk/` engine **intentionally retained** — `RiskAnalysis` (data type) is still actively imported by:
  - `atlas/conversation/engine.py`
  - `atlas/intelligence/engine.py`
  - `atlas/reasoning/engine.py`
- `RiskEngine` has no production instantiation points, but lives in the same file as `RiskAnalysis` (`atlas/risk/engine.py`). Separating them would require surgery to the engine file and `atlas/risk/__init__.py`; deferred.
- Tests updated: `test_risk_size_deprecation.py` rewritten as retirement test; includes `RiskAnalysis` caller-presence assertions
- 1101 tests passing

**Engine deletion criteria (deferred):**
1. Three `RiskAnalysis` callers (`atlas/conversation/`, `atlas/intelligence/`, `atlas/reasoning/`) must stop importing it, OR `RiskAnalysis` must be moved to a shared types module before `atlas/risk/` can be deleted
2. Once `RiskAnalysis` is no longer needed from `atlas/risk/`, confirm `RiskEngine` and `PositionSizingInput` also have no callers, then delete the module

---

## Sprint 87 Migration Target — COMPLETED

### Completed: `atlas reason analyze` command body retired; engine retained

**Sprint 87 result:**
- `atlas reason analyze` command body removed from `atlas/cli/main.py` — command no longer callable
- `atlas reason analyze` moved from active `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`
- `atlas/reasoning/` engine **intentionally retained** — `atlas/principles/engine.py` has:
  - A `TYPE_CHECKING`-only import of `ReasoningReport` (not a runtime dependency)
  - A lazy import of `render_reasoning_report` inside `check_reasoning_report()` — only fires if called
  - `check_reasoning_report()` has no external callers as of Sprint 87
- `atlas/domains/decision/engine.py` defines its own `ReasoningEngine` (Blueprint-aligned) — entirely separate from `atlas.reasoning.ReasoningEngine`; unaffected
- Tests updated: `test_reason_analyze_deprecation.py` rewritten as retirement test; includes lazy-import documentation assertion
- 1104 tests passing

**Engine deletion criteria (deferred to Sprint 88 or later):**
1. Remove `check_reasoning_report()` from `atlas/principles/engine.py` OR replace its lazy `atlas.reasoning` import with a non-legacy approach
2. Re-confirm `atlas.reasoning.ReasoningEngine` has no remaining instantiation points
3. The `TYPE_CHECKING`-only `ReasoningReport` import is not a runtime blocker but should also be removed when deleting the engine

---

## Sprint 86 Migration Target — COMPLETED

### Completed: `atlas evidence assess` command body retired; engine retained

**Sprint 86 result:**
- `atlas evidence assess` command body removed from `atlas/cli/main.py` — command no longer callable
- `atlas evidence assess` moved from active `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`
- `atlas/evidence/` engine **intentionally retained** — confirmed active callers:
  - `atlas/comparison/engine.py` — instantiates `EvidenceQualityEngine`
  - `atlas/decision_journal/engine.py` — instantiates `EvidenceQualityEngine`
  - `atlas/watchlist_review/engine.py` — instantiates `EvidenceQualityEngine`
- Engine deletion deferred until those three callers are retired
- Tests updated: `test_evidence_assess_deprecation.py` rewritten as retirement test; includes caller-presence assertions
- 1107 tests passing

**Engine deletion criteria (deferred):**
1. `atlas/comparison/` must be retired or migrated
2. `atlas/decision_journal/` must be retired or migrated
3. `atlas/watchlist_review/` must be retired or migrated
4. Re-confirm no remaining `EvidenceQualityEngine` instantiation

---

## Sprint 85 Migration Target — COMPLETED

### Completed: `atlas daily brief` command body retired

**Sprint 85 result:**
- `atlas daily brief` command body removed from `atlas/cli/main.py` — command is no longer registered in the CLI
- `atlas daily brief` moved from active `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`; `all_retired_commands()` accessor added
- `atlas daily summary` remains unchanged — the supported Daily Brief workflow
- All tests updated: regression tests that checked the command was deprecated now verify it is retired (exit non-zero)
- `test_daily_brief_deprecation.py` rewritten as a retirement confirmation test suite
- 1111 tests passing
- CLI surface area reduced by one command

**Retirement prerequisites that were met:**
1. `atlas.daily_brief` engine deleted in Sprint 77 — no engine dependency
2. Command body was a pure stub with no callers — removal was zero-risk
3. `atlas daily summary` provides complete replacement functionality

---

## Sprint 84 Migration Target — COMPLETED

### Completed: Deprecated command registry and cleanup plan

**Sprint 84 result:**
- Created `atlas/cli/deprecations.py` — a CLI-local registry of all 7 deprecated commands
- Each entry records: command name, Rich-formatted message, replacement command or consolidation direction, legacy module, and removal criteria
- All 7 deprecated CLI command bodies now route through `deprecated_command_message()` instead of inlining the message string
- No engine imports, no provider imports, no domain imports in the registry
- User-facing output is bit-for-bit identical to Sprint 83 output
- Created `docs/DeprecatedCommands.md` — human-readable registry with recommended retirement order
- 46 new Sprint 84 registry tests; 1114 tests passing
- Architecture boundary: registry is CLI-local only

**Future retirement checklist (see `docs/DeprecatedCommands.md`):**
1. `atlas daily brief` command body — engine already deleted, safest to remove
2. `atlas evidence assess` command body + engine — self-contained, no known dependents
3. `atlas risk size` command body — engine has no callers, but `RiskAnalysis` type dependency must be confirmed
4. `atlas reason analyze` command body — requires retiring `atlas/principles/` lazy import first
5. ~~`atlas portfolio analyze`~~ — **DONE Sprint 89** (command retired; 10+ engine callers remain)
6. ~~`atlas portfolio review`~~ — **DONE Sprint 90** (command retired; legacy engine retained — `atlas/home/engine.py` still instantiates it)
7. ~~`atlas watchlist analyze`~~ — **DONE Sprint 91** (command retired; engine retained — 5 active callers; CLI retirement plan complete)

---

## Sprint 83 Migration Target — COMPLETED

### Completed: `atlas risk size` command deprecated

**Sprint 83 result:**
- `atlas risk size` CLI command now prints a deprecation message and exits cleanly (exit 0)
- No replacement command invented — message directs toward Blueprint-aligned portfolio, decision and research capabilities (future)
- `RiskEngine`, `PositionSizingInput`, `render_risk_analysis` removed from `atlas/cli/main.py` imports
- `atlas/risk/` engine remains on disk; `RiskAnalysis` type is still imported by `atlas/intelligence/`, `atlas/reasoning/`, and `atlas/conversation/` engines
- 16 new Sprint 83 deprecation tests (including regression checks for all 6 prior deprecated commands); 1068 tests passing

**`RiskEngine` isolation note:** `RiskEngine` and `PositionSizingInput` are no longer called by any CLI command. Other legacy engines import only `RiskAnalysis` (a data type), not the engine class. The engine class itself is unused.

**Future removal criteria:**
1. Remove command body in a future sprint (or leave deprecated stub)
2. `atlas.risk.RiskEngine` deletion requires confirming no other engine instantiates it

---

## Sprint 82 Migration Target — COMPLETED

### Completed: `atlas reason analyze` command deprecated

**Sprint 82 result:**
- `atlas reason analyze` CLI command now prints a deprecation message and exits cleanly (exit 0)
- No replacement command invented — message directs toward Blueprint-aligned decision and research capabilities (future)
- `ReasoningEngine`, `ReasoningInput`, `ReasoningReport`, `render_reasoning_report` removed from `atlas/cli/main.py` imports
- `_build_reasoning_report` private helper (dead code after deprecation) also removed from CLI
- `atlas/reasoning/` engine remains on disk; used by `atlas/principles/engine.py` and `atlas/domains/decision/`
- 14 new Sprint 82 deprecation tests (including regression checks for all 5 prior deprecated commands); 1054 tests passing

**`ReasoningEngine` isolation note:** `atlas.reasoning.ReasoningEngine` (legacy, provider-coupled) is no longer
called by any CLI command. However, `atlas/domains/decision/engine.py` defines its own `ReasoningEngine` class
(a separate Blueprint-aligned type) — these are distinct. The legacy `atlas.reasoning.ReasoningEngine` is also
still referenced by `atlas/principles/engine.py` (lazy import).

**Future removal criteria:**
1. Remove command body in Sprint 83 or later (or leave deprecated stub)
2. `atlas.reasoning.ReasoningEngine` deletion requires retiring `atlas/principles/engine.py` lazy import

---

## Sprint 81 Migration Target — COMPLETED

### Completed: `atlas evidence assess` command deprecated

**Sprint 81 result:**
- `atlas evidence assess` CLI command now prints a deprecation message and exits cleanly (exit 0)
- No replacement command invented — message directs users toward Blueprint-aligned decision and research capabilities (future)
- `EvidenceQualityEngine` and `render_evidence_assessment` removed from `atlas/cli/main.py` imports
- `atlas/evidence/` engine remains on disk; still used by `decision_journal`, `comparison`, `watchlist_review` legacy engines
- 12 new Sprint 81 deprecation tests (including regression checks for all 4 prior deprecated commands); 1040 tests passing

**`EvidenceQualityEngine` isolation:** no longer called by any CLI command.
Still used by: `atlas/decision_journal/engine.py`, `atlas/comparison/engine.py`, `atlas/watchlist_review/engine.py`.
Full deletion requires retiring those engines.

**No Blueprint-aligned evidence capability exists yet.** The deprecation message correctly
avoids inventing a replacement command and instead points to future consolidation direction.

**Future removal criteria:**
1. Remove command body in Sprint 82 or later (or leave deprecated stub)
2. `EvidenceQualityEngine` deletion requires retiring 3 dependent legacy engines

---

## Sprint 80 Migration Target — COMPLETED

### Completed: `atlas portfolio review` command deprecated

**Sprint 80 result:**
- `atlas portfolio review` CLI command now prints a deprecation message and exits cleanly (exit 0)
- `PortfolioReviewEngine`, `PortfolioReviewInput`, `render_portfolio_review` removed from `atlas/cli/main.py` imports
- `atlas portfolio summary` (Blueprint-aligned) is the sole supported portfolio command
- `atlas portfolio analyze` remains deprecated from Sprint 79 — confirmed unchanged
- `atlas/portfolio_review/` engine remains on disk; no CLI command calls it
- 10 new Sprint 80 deprecation tests; 1028 tests passing, 0 failures

**`PortfolioReviewEngine` isolation:** module on disk, no longer imported by any CLI command.
Still referenced by `atlas/home/engine.py` (AtlasHomeEngine) — see Group B legacy engines.

**Future removal criteria for `atlas portfolio review` command:**
1. Remove command body entirely in Sprint 81 (or leave deprecated stub)
2. `PortfolioReviewEngine` deletion requires retiring `AtlasHomeEngine` (Group B)

---

## Sprint 79 Migration Target — COMPLETED

### Completed: `atlas portfolio analyze` command deprecated

**Sprint 79 result:**
- `atlas portfolio analyze` CLI command now prints a deprecation message and exits cleanly (exit 0)
- `PortfolioIntelligenceEngine` and `render_portfolio_analysis` removed from `atlas/cli/main.py` imports
- `atlas portfolio summary` (Blueprint-aligned, no provider calls) is the current supported command
- `atlas portfolio review` is **unchanged** — separate legacy path, not in Sprint 79 scope
- `atlas/analysis/portfolio.py` remains on disk; `Portfolio` type still used by summary and review commands
- 10 new Sprint 79 deprecation tests; 1018 tests passing, 0 failures

**`atlas portfolio review` status:** unchanged. It still uses the legacy `PortfolioReviewEngine`.
This is separate technical debt documented for a future sprint.

**Future removal criteria for `atlas portfolio analyze` command:**
1. Remove command body entirely in Sprint 80 (or leave deprecated stub)
2. `PortfolioIntelligenceEngine` deletion safe once `atlas portfolio review` and other consumers are retired

---

## Sprint 78 Migration Target — COMPLETED

### Completed: `atlas watchlist analyze` command deprecated

**Sprint 78 result:**
- `atlas watchlist analyze` CLI command now prints a deprecation message and exits cleanly (exit 0)
- `WatchlistEngine` and `render_watchlist_analysis` removed from `atlas/cli/main.py` module-level imports
- `atlas watchlist intelligence` (Blueprint-aligned) is the current supported command
- `atlas/analysis/watchlist.py` engine remains on disk — still used by 5 other legacy engines
  (`monitoring`, `decision`, `intelligence`, `conversation`, `watchlist_review`)
- 10 new Sprint 78 deprecation tests added; 1008 tests passing, 0 failures

**Note:** `WatchlistEngine` cannot be deleted yet — it has 5 active legacy engine consumers.
The CLI command deprecation reduces CLI surface area; full engine removal requires a broader
legacy consolidation plan for those dependent engines.

**Future removal criteria for `atlas watchlist analyze` command:**
1. Remove the command body entirely in Sprint 79 (or leave deprecated stub — low risk)
2. `WatchlistEngine` deletion requires retiring all 5 dependent legacy engines first

---

## Sprint 77 Migration Target — COMPLETED

### Completed: `atlas/daily_brief/` legacy engine deleted

**Sprint 77 result:**
- `atlas/daily_brief/` (2 files, 353 lines) deleted
- `tests/test_daily_brief.py` rewritten: 6 legacy engine tests removed; 1 CLI deprecation test retained
- 3 new architecture guardrail tests added to `test_architecture_boundaries.py`:
  - `test_atlas_daily_brief_engine_is_removed` — directory must not exist
  - `test_atlas_daily_brief_is_not_importable` — import must raise `ModuleNotFoundError`
  - `test_no_active_code_imports_atlas_daily_brief` — static scan of all source files
- 998 tests passing, 0 failures. Demo + RC verification both green.
- `atlas.daily_brief` is now fully removed from the codebase.

**Net reduction:** 353 lines of provider-coupled legacy code eliminated.

---

## Sprint 76 Migration Target — COMPLETED

### Completed: `atlas daily brief` command deprecated

**Sprint 76 result:**
- `atlas daily brief` CLI command now prints a deprecation message and exits cleanly (exit 0)
- Legacy `DailyBriefEngine` is no longer called by any CLI command
- `from atlas.daily_brief import ...` removed from `atlas/cli/main.py` module-level imports
- `atlas daily summary` (Blueprint-aligned) is the current supported command
- `atlas/daily_brief/` engine module remains on disk, isolated — no command calls it
- 10 new Sprint 76 deprecation tests added; 1001 tests passing, 0 failures

**Provider safety:** deprecated command makes zero provider calls (no `DailyBriefEngine` instantiated).

**Future removal criteria for `atlas/daily_brief/`:**
1. Confirm no external scripts import `atlas.daily_brief` directly (grep confirms only CLI did)
2. Remove `atlas daily brief` command entirely (not just deprecate)
3. Delete `atlas/daily_brief/` (2 files, 353 lines) in a future sprint
4. Suggested sprint: Sprint 77 or later

---

## Sprint 75 Migration Target — COMPLETED

### Completed: `atlas/daily/` shim removal + `atlas/domains/daily_brief/` boundary fix

**Sprint 75 result:**
- `atlas/daily/` deleted (2 files, 43 lines)
- `atlas/cli/main.py` updated to import from `atlas.daily_brief` directly
- `tests/test_daily_brief.py` updated to import from `atlas.daily_brief` directly
- `atlas/domains/daily_brief/__init__.py` rewritten as a minimal namespace stub
  (no imports from legacy OR capabilities — pure domain namespace placeholder)
- `test_domains_do_not_import_capabilities_or_providers_or_legacy` extended with
  explicit legacy prefix list (`atlas.daily`, `atlas.daily_brief`, `atlas.analysis`, etc.)
- 2 new Sprint 75 boundary tests added: `test_atlas_daily_shim_is_removed`,
  `test_domains_daily_brief_does_not_import_legacy`
- 991 tests passing, 0 failures. Demo + RC verification both green.

### Selected Target (original):

**Rationale:**

`atlas/daily/` is a two-file, 43-line pure re-export shim with no logic:

```python
# atlas/daily/__init__.py
from atlas.daily_brief import (
    DailyBriefEngine, DailyBriefInput, ...
)
```

It exists solely to give `atlas.daily` a stable import path. The only CLI
consumer is `atlas daily brief` (legacy command), which can import from
`atlas.daily_brief` directly without the shim.

**Simultaneously**, `atlas/domains/daily_brief/__init__.py` imports from
`atlas.daily_brief` — a boundary violation. Since no external code imports
from `atlas.domains.daily_brief`, this file can be updated to export from
`atlas.capabilities.daily_brief` instead (or left as-is if the domain
boundary module is removed entirely).

**What Sprint 75 would do:**

1. Update `atlas/cli/main.py` to import `DailyBriefEngine`, `DailyBriefInput`,
   `render_daily_brief` from `atlas.daily_brief` directly (removing the
   `atlas.daily` shim import)
2. Fix `atlas/domains/daily_brief/__init__.py` to either:
   - re-export from `atlas.capabilities.daily_brief` (correct direction), or
   - be removed if no code uses it
3. Delete `atlas/daily/` (2 files, 43 lines)
4. Update any test imports

**This does NOT:**
- Change the `atlas daily brief` command behavior
- Touch `atlas/daily_brief/` (the legacy engine itself)
- Change the `atlas daily summary` command (Blueprint-aligned, untouched)
- Introduce any new capability

**Risk level: LOW**
- 43 lines removed, 0 logic changed
- Full test suite confirms no regressions
- The shim has no logic — it is purely a re-export

### Runner-up Target: `atlas/domains/daily_brief/` boundary fix only

If the `atlas/daily/` removal is considered too broad for Sprint 75, the
boundary violation fix alone (updating `atlas/domains/daily_brief/__init__.py`
to not import from a legacy module) is an even smaller, safer change.

---

## Migration Risk Summary

| Risk | Description | Mitigation |
|---|---|---|
| Import breakage | `atlas.daily` removed; any external code using it breaks | Grep confirms only `atlas/cli/main.py` imports `atlas.daily`; fix is in same sprint |
| Test failures | Tests importing `atlas.daily` | Only `tests/test_daily_brief.py` imports from `atlas.daily_brief` (not `atlas.daily`); risk is low |
| Boundary re-introduction | Future sprint re-introduces domain → legacy import | Add architecture boundary test asserting domains do not import legacy modules |
| Scope creep | Sprint expands to touch `atlas/daily_brief/` engine | Sprint 75 explicitly excludes the daily_brief engine; only the shim is removed |

---

## Full Technical Debt Inventory (Updated)

| Area | Description | Priority | Suggested Sprint |
|---|---|---|---|
| ~~`atlas/daily/` shim~~ | ~~43-line re-export; removed~~ | ~~High~~ | **Done 75** |
| ~~`atlas/domains/daily_brief/` boundary violation~~ | ~~Fixed: namespace stub~~ | ~~High~~ | **Done 75** |
| ~~`atlas daily brief` command~~ | ~~Deprecated; no longer calls engine~~ | ~~High~~ | **Done 76** |
| ~~`atlas/daily_brief/` legacy engine~~ | ~~Provider-coupled; deleted~~ | ~~Medium~~ | **Done 77** |
| ~~`atlas/analysis/watchlist.py` — WatchlistEngine~~ | ~~`atlas watchlist analyze` deprecated; WatchlistEngine used by 5 legacy engines~~ | ~~Medium~~ | **Done 91/99** (CLI retired Sprint 91; engine deleted Sprint 99; file retained as types-only) |
| `atlas/analysis/portfolio.py` legacy type | Bridged via adapter; could be retired after full portfolio migration | Medium | Future |
| Group C self-contained modules | `evidence`, `reasoning`, `risk`, etc. — good candidates for Blueprint wrappers | Low | Multi-sprint |
| Provider-coupled Group B | `home`, `dashboard`, `comparison`, etc. — require provider architecture decision | Low | Long-term |
| Legacy engine consolidation (test coverage) | Ensure legacy commands retain tests during migration | Ongoing | Each sprint |

# Analysis Package Cleanup Plan

**Created:** 2026-07-02 (Sprint 102)  
**Status:** ACTIVE — Sprint 110 complete: `atlas/analysis/portfolio.py` migration plan written. 14 modules remain. Full caller map, Blueprint overlap, and 6-phase migration plan documented in `docs/PortfolioAnalysisMigrationPlan.md`. Sprint 111 is a pre-migration guardrail sprint.

---

## Background

After Sprints 99–101, the `atlas/analysis/watchlist.py` module was fully deleted and its types
migrated to `atlas/capabilities/watchlist_intelligence/`. `atlas/analysis/` still contains 16
remaining modules. This document tracks the cleanup roadmap for those modules.

---

## `atlas/analysis/` Inventory (Sprint 108 state)

**15 modules remain (3 deleted: `watchlist.py` Sprint 101, `comparison.py` Sprint 103, `memory.py` Sprint 104).**

| File | Lines | Public API | Re-exported from `__init__` | Production Callers | Category |
|---|---|---|---|---|---|
| `__init__.py` | 45 | Re-export hub | — | — | Shrinks with each migration |
| `company_analysis.py` | 45 | `CompanyAnalysis`, `MockCompanyAnalysisProvider`, `create_placeholder_company_analysis` | Yes | providers (mock, yahoo, base), 5 test files | Active foundation — heavily used |
| `engine.py` | 229 | `AtlasInvestmentEngine`, `InvestmentReport`, `ScoreCategory`, `ThresholdRecommendationPolicy`, `iter_score_categories`, `DEFAULT_CATEGORY_WEIGHTS` | Yes | 10 production files | **Foundational — leave for last** |
| `explanation.py` | 198 | `InvestmentExplanation`, `explain_investment_report`, `render_investment_explanation` | Partial | `atlas/decision/memory.py`, `atlas/analysis/report.py` | **Sprint 105 ✓ cleaned** — active free-function module |
| `growth.py` | 18 | `GrowthAnalysis`, `placeholder_growth_analysis` | No | Internal to `company_analysis.py` | Internal sub-module — leave unchanged |
| `macro.py` | 18 | `MacroAnalysis`, `placeholder_macro_analysis` | No | Internal to `company_analysis.py` | Internal sub-module — leave unchanged |
| `moat.py` | 18 | `MoatAnalysis`, `placeholder_moat_analysis` | No | Internal to `company_analysis.py` | Internal sub-module — leave unchanged |
| `portfolio.py` | 457 | `Portfolio`, `PortfolioPosition`, `PortfolioAnalysis`, `PortfolioIntelligenceEngine`, `PortfolioRecommendation`, `CompanyPortfolioProfile`, `get_mock_company_portfolio_profile`, `render_portfolio_analysis` | Yes | 17 production import sites, 16 test files | **Long-term high-coupling — do not migrate yet** |
| `quality.py` | 18 | `QualityAnalysis`, `placeholder_quality_analysis` | No | Internal to `company_analysis.py` | Internal sub-module — leave unchanged |
| `report.py` | 38 | `build_investment_report`, `render_investment_report` | Yes | `atlas/cli/main.py` (3 sites), `atlas/comparison/engine.py` (1 site) | **Sprint 107 ✓ cleaned** — active utility |
| `scores.py` | 2 | `clamp_score` | No | 9 production files across 6 packages | Shared utility — leave unchanged |
| `scoring.py` | — | — | — | — | **Sprint 109 ✓ DELETED** — zero production callers; test-only module removed |
| `sentiment.py` | 18 | `SentimentAnalysis`, `placeholder_sentiment_analysis` | No | Internal to `company_analysis.py` | Internal sub-module — leave unchanged |
| `technicals.py` | 18 | `TechnicalAnalysis`, `placeholder_technical_analysis` | No | Internal to `company_analysis.py` | Internal sub-module — leave unchanged |
| `valuation.py` | 18 | `ValuationAnalysis`, `placeholder_valuation_analysis` | No | Internal to `company_analysis.py` | Internal sub-module — leave unchanged |

### Deleted modules (confirmed absent)

| Module | Deleted Sprint | Status |
|---|---|---|
| `atlas/analysis/watchlist.py` | Sprint 101 | ✓ Gone — `ModuleNotFoundError` confirmed |
| `atlas/analysis/comparison.py` | Sprint 103 | ✓ Gone — `ModuleNotFoundError` confirmed |
| `atlas/analysis/memory.py` | Sprint 104 | ✓ Gone — `ModuleNotFoundError` confirmed |

---

## ComparisonEngine Audit (Sprint 102)

### What it does

`ComparisonEngine` accepts a dict of `{ticker: CompanyAnalysis}` (or a list of tickers + provider),
runs `AtlasInvestmentEngine.analyze()` on each, and ranks candidates across five dimensions
(Overall, Quality, Valuation, Growth, Risk). Returns a `ComparisonResult` with ranked
`ComparisonRanking` objects and a `final_conclusion` string.

### Caller map

**Production runtime callers — 2:**

| File | Usage | Type |
|---|---|---|
| `atlas/decision/decision_engine.py` | `self.comparison_engine = comparison_engine or ComparisonEngine(...)` then `compare_tickers(tickers, provider)` | Active engine instantiation + call |
| `atlas/decision/decision_result.py` | `comparison_result: ComparisonResult \| None` | Type annotation only |

**CLI callers — 0 (none):**
- `atlas/cli/main.py` imports `InvestmentComparisonEngine` from `atlas/comparison/` (Blueprint-aligned) for `atlas compare` command. `ComparisonEngine` (legacy) is NOT used by any CLI command.

**Test callers — 2 files:**
- `tests/test_comparison.py` — direct `ComparisonEngine` tests
- `tests/test_providers.py` — `ComparisonEngine().compare_tickers(...)` via provider path

### Provider dependency

**YES.** `ComparisonEngine.compare_tickers(tickers, provider)` accepts a `CompanyDataProvider`.
`compare(analyses)` accepts pre-fetched analyses — no direct provider call. The `decision_engine.py`
caller uses `compare_tickers(...)` which requires a provider.

### Blueprint overlap

`atlas/comparison/engine.py` contains `InvestmentComparisonEngine` — a Blueprint-aligned,
fully-featured comparison engine that:
- uses `EvidenceQualityEngine`, `ThemeEngine`, `PrinciplesEngine`, `SuitabilityEngine`
- produces rich `InvestmentComparisonReport` (research-framed, non-ranking)
- is already the CLI `atlas compare` command path

The legacy `ComparisonEngine` is a simpler score-ranking approach. The decision engine uses it to
rank candidates when multiple tickers are in context.

### Migration complexity

**LOW-MEDIUM.** Two production callers in `atlas/decision/`:

1. `decision_engine.py` — `ComparisonEngine` used to rank candidates during decision; replaces
   straightforward if callers are updated to use a simpler comparison approach or the ranking logic
   is inlined. The decision engine's ranking need (best-of-N by score) does not require the full
   `InvestmentComparisonEngine` — could be inlined or delegated to a helper.

2. `decision_result.py` — type annotation only; changes with whichever replacement type is chosen.

**`ComparisonResult`** is used as a type in `decision_result.py`. Removal requires choosing a
replacement type or inlining the ranking logic.

### Risk level: MEDIUM

The decision engine uses `ComparisonResult` fields actively (ranking dimensions). Output text may
change if the comparison logic is replaced or inlined. Requires careful output preservation.

### Recommended action: MIGRATE — Sprint 103 target (see decision below)

---

## MemoryEngine Audit (Sprint 102)

### What it does

`MemoryEngine` saves `InvestmentReport` snapshots (as `MemoryEntry`) to a local JSON file
(`MemoryStore`). Supports save, load, and cross-time comparison of two snapshots for the same
ticker. Produces `MemoryComparison` (score delta, category changes, recommendation change).

### Caller map

**Production runtime callers — 4 sites across 3 files:**

| File | Usage | Type |
|---|---|---|
| `atlas/cli/main.py` | `atlas memory save`, `atlas memory show`, `atlas memory compare` commands | Active CLI path (3 commands) |
| `atlas/decision/decision_context.py` | `historical_memory: MemoryStore \| None` | Type annotation only |
| `atlas/decision/decision_engine.py` | `self.memory_engine = MemoryEngine()` + `_compare_memory()` call | Active engine instantiation + call |
| `atlas/decision/decision_result.py` | `memory_comparison: MemoryComparison \| None` | Type annotation only |

**Also note:** `atlas/memory/` is a completely separate Blueprint-aligned module (`MemoryStore[T]`
generic ABC for snapshot history). This is NOT the same as `atlas/analysis/memory.py`'s
`MemoryStore` — they share a name but are different abstractions. `atlas/history/engine.py` uses
`atlas.memory.MemoryStore`, not `atlas.analysis.memory.MemoryStore`.

**Test callers — 2 files:**
- `tests/test_memory.py` — direct `MemoryEngine` tests
- `tests/test_providers.py` — `MemoryEngine().save_ticker(...)` via provider path
- `tests/test_decision_engine.py` — `MemoryEngine()` in decision context

### Provider dependency

**YES — partially.** `MemoryEngine.save_ticker(ticker, provider, ...)` accepts a
`CompanyDataProvider`. The core `save(store, ticker, report)` and `compare()` methods need no
provider. CLI commands `atlas memory save` use the provider path.

### Blueprint overlap

`atlas/memory/` (Blueprint) is a generic snapshot-history abstraction. `atlas/analysis/memory.py`
is an investment-score-specific tracker. No exact Blueprint equivalent exists.
`atlas/domains/decision_journal/` owns `JournalEntry` but is not the same concept.

No Blueprint-aligned engine provides the same score-delta tracking capability.

### Migration complexity

**MEDIUM-HIGH.** More callers than `ComparisonEngine`, and includes 3 active CLI commands
(`atlas memory save/show/compare`). Replacing or retiring requires:
- Deciding whether to keep the `memory` CLI commands or retire them
- Migrating `atlas/decision/decision_engine.py` `_compare_memory()` path
- Updating `decision_context.py` and `decision_result.py` type annotations
- No direct Blueprint equivalent exists — would need to be created or CLI commands retired

### Risk level: HIGH (relative to comparison)

Three active CLI commands. Historical memory files written to user's local filesystem. If
`MemoryEngine` behavior changes, existing saved memory files must still be readable.

### Outcome: COMPLETED Sprint 104 — moved to `atlas/decision/memory.py`; `atlas/analysis/memory.py` deleted

---

## Decision: Sprint 103 Target — `ComparisonEngine`

### Chosen: `atlas/analysis/comparison.py` — retire `ComparisonEngine`

**Rationale:**

1. **Fewer production callers.** `ComparisonEngine` has 2 production caller sites (both in
   `atlas/decision/`). `MemoryEngine` has 4 across 3 files.

2. **No active CLI commands use legacy `ComparisonEngine`.** The CLI `atlas compare` command already
   uses `InvestmentComparisonEngine` (Blueprint-aligned). The legacy engine is only used internally
   by `decision_engine.py`.

3. **Clear Blueprint overlap.** `atlas/comparison/engine.py` (`InvestmentComparisonEngine`) is the
   supported comparison path. The legacy `ComparisonEngine` is a simpler score-ranking tool that
   could be inlined or replaced.

4. **Lower risk than `MemoryEngine`.** No CLI commands depend on the legacy engine. No user-written
   data files depend on it. `MemoryEngine` has active CLI paths and user-data coupling.

5. **`ComparisonResult` is a narrow type.** Only used in 2 files (`decision_engine.py` and
   `decision_result.py`). Replacement or inlining is contained.

6. **Self-contained module.** `comparison.py` imports only from `atlas.analysis.company_analysis`,
   `atlas.analysis.engine`, and `atlas.providers.base`. No cross-domain dependencies.

### Sprint 103 approach options

**Option A (preferred): Inline ranking logic into decision engine**
- Remove `ComparisonEngine` and `ComparisonResult` imports from `decision_engine.py`
- Inline the ticker-ranking logic (sort candidates by `atlas_score`) directly in the decision engine
- Remove `comparison_result` from `DecisionResult` or replace with a lighter structure
- Delete `atlas/analysis/comparison.py`
- Risk: LOW — ranking logic is simple; inlining removes a level of indirection

**Option B: Route through `InvestmentComparisonEngine`**
- Replace `ComparisonEngine` with `InvestmentComparisonEngine` in decision engine
- `InvestmentComparisonReport` is much richer than `ComparisonResult` — decision engine would consume a subset
- Risk: MEDIUM — output format change; `InvestmentComparisonEngine` is much heavier (provider + evidence + themes)

**Option C: Retire the decision engine comparison path**
- Check whether `_compare(normalized_ticker, provider, context)` is ever exercised at runtime
- If only exercised when `context.comparison_tickers` is non-None (an optional field), assess actual
  usage frequency
- If comparison path is rarely/never used, retire it entirely from decision engine
- Risk: LOW — removes dead path

**Recommendation:** Audit Option C first. If the comparison path in decision engine is exercised
only when `context.comparison_tickers` is provided and that context field has no active callers,
retire the path entirely. If it is needed, use Option A (inline simple ranking).

---

## Remaining Analysis Cleanup Roadmap

| Sprint | Target | Action | Risk |
|---|---|---|---|
| 103 ✓ | `atlas/analysis/comparison.py` | Retired `ComparisonEngine`; types moved to `atlas/decision/comparison.py`; file deleted | DONE |
| 104 ✓ | `atlas/analysis/memory.py` | Retired `MemoryEngine`; types/logic moved to `atlas/decision/memory.py`; file deleted | DONE |
| 105 ✓ | `atlas/analysis/explanation.py` | `ExplanationEngine` class eliminated; file kept as free-function module | DONE |
| 106 ✓ | `atlas/analysis/scoring.py` | `RecommendationEngine` class eliminated; `ScoringEngine` retained | DONE |
| 107 ✓ | `atlas/analysis/report.py` | Retained in place; `render_company_analysis_report` removed (no callers); `build_investment_report` + `render_investment_report` kept (active callers) | DONE |
| 108 ✓ | Checkpoint | Full inventory audit; verified deleted modules remain gone; Blueprint `domains/` confirmed import-free from `atlas.analysis`; `scoring.py` identified as Sprint 109 target | DONE |
| 109 ✓ | `atlas/analysis/scoring.py` | Deleted — `ScoringEngine` and `score_company` had zero production callers; test-only module; `tests/test_scoring.py` stripped of dead tests | DONE |
| 110 ✓ | Planning sprint | `portfolio.py` migration plan written; 6-phase plan in `docs/PortfolioAnalysisMigrationPlan.md`; 3 pre-migration guardrail tests added | DONE |
| **111** | Pre-migration guardrails | **Already done in Sprint 110 — guardrails added; Sprint 111 may begin Phase 2 (type extraction) or defer to portfolio capability creation** | LOW |
| 112+ | `atlas/analysis/portfolio.py` Phase 2 | Extract `PortfolioSignal` type; create `atlas/capabilities/portfolio_intelligence/` stub | MEDIUM |
| 113–119 | Caller migration | One caller per sprint, lowest-coupling first | HIGH |
| ~120 | Provider migration | Remove `CompanyPortfolioProfile` from provider interface | HIGH |
| ~121 | Delete `portfolio.py` | After zero active callers remain | — |
| Future | `atlas/analysis/engine.py` | Core scoring engine; 10 production callers; foundational — leave for late cleanup | VERY HIGH |
| Leave | `scores.py`, `growth.py`, `macro.py`, `moat.py`, `quality.py`, `sentiment.py`, `technicals.py`, `valuation.py` | Internal sub-modules; no direct cleanup needed | — |

---

## High-Coupling Module Review (Sprint 108)

### `atlas/analysis/portfolio.py` — DO NOT MIGRATE YET

**Lines:** 457  
**Public classes/functions:** `Portfolio`, `PortfolioPosition`, `PortfolioAnalysis`, `PortfolioIntelligenceEngine`, `PortfolioRecommendation`, `CompanyPortfolioProfile`, `get_mock_company_portfolio_profile`, `render_portfolio_analysis`  
**Re-exported from `__init__.py`:** Yes (6 names)  
**Production import sites:** 17 (across `atlas/adapters/`, `atlas/cli/`, `atlas/conversation/`, `atlas/dashboard/`, `atlas/decision/`, `atlas/home/`, `atlas/intelligence/`, `atlas/monitoring/`, `atlas/portfolio_review/`, `atlas/providers/`, `atlas/reasoning/`, `atlas/risk_drift/`, `atlas/suitability/`)  
**Test files:** 16  
**CLI dependency:** Yes — `atlas/cli/main.py` imports `Portfolio` directly  
**Blueprint replacement:** Partial — `atlas/domains/portfolio/` owns canonical `Portfolio` types; `atlas/capabilities/` does not yet have a full `PortfolioIntelligenceEngine` replacement  
**Provider dependency:** Yes — `atlas/providers/base.py` and `atlas/providers/mock.py` import `CompanyPortfolioProfile`; changing this file would widen the provider surface  
**Migration direction:** Long-term migration to `atlas/domains/portfolio/` types with `atlas/capabilities/` intelligence layer; requires adapter layer expansion  
**Risk:** VERY HIGH — broadest legacy coupling in the codebase  
**Decision:** Do not touch until a dedicated multi-sprint migration plan is written

### `atlas/analysis/engine.py` — DO NOT MIGRATE YET

**Lines:** 229  
**Public classes/functions:** `AtlasInvestmentEngine`, `InvestmentReport`, `ScoreCategory`, `ThresholdRecommendationPolicy`, `iter_score_categories`, `DEFAULT_CATEGORY_WEIGHTS`, `clamp_score` (re-exports from `scores.py`)  
**Re-exported from `__init__.py`:** Yes (3 names)  
**Production import sites:** 10 (across `atlas/conversation/`, `atlas/decision/`, `atlas/intelligence/`, `atlas/models/`, `atlas/monitoring/`, `atlas/reasoning/`, `atlas/suitability/`)  
**Test files:** 5  
**CLI dependency:** Indirect (via `report.py` → `AtlasInvestmentEngine`)  
**Blueprint replacement:** None yet — `AtlasInvestmentEngine` is the foundational scoring engine; no equivalent exists in `atlas/capabilities/`  
**Provider dependency:** None — pure computation, no network calls  
**Migration direction:** Very long-term; would require a canonical scoring domain in `atlas/domains/` and full capability-layer replacement of `AtlasInvestmentEngine`  
**Risk:** EXTREME — changing this breaks scoring across the entire system  
**Decision:** Leave for last; cleanup of all other modules first

---

## Sprint 109 — COMPLETED: Delete `atlas/analysis/scoring.py`

**Outcome:**
- `atlas/analysis/scoring.py` deleted. `ScoringEngine` and `score_company` confirmed to have zero production callers before deletion.
- `atlas/analysis/__init__.py`: `ScoringEngine` and `score_company` removed from import and `__all__`.
- `tests/test_scoring.py`: 3 dead tests removed (`test_scoring_engine_calculates_weighted_score_for_nvda`, `test_scoring_engine_uses_configurable_weights`, `test_scoring_engine_rejects_unknown_weights`). 2 surviving tests kept (`ThresholdRecommendationPolicy`, `build_investment_report`).
- Guardrail tests updated: `test_recommendation_engine_class_is_deleted` → `test_scoring_module_is_deleted`; `test_scoring_engine_and_score_company_still_importable` → `test_scoring_engine_and_score_company_are_deleted`.
- 1136 tests passing (3 skipped). Demo passed. Release verification green.

**Sprint 110 recommendation:** `portfolio.py` migration planning sprint (read-only audit; no migration yet) — or architecture release checkpoint if no further cleanup is scheduled near-term.

---

## Provider Safety (Sprint 108 state)

- `atlas/analysis/scores.py` (`clamp_score`) — pure computation, no network calls — **9 production callers; leave unchanged**
- `atlas/analysis/engine.py` (`AtlasInvestmentEngine`) — pure computation engine; accepts provider indirectly (callers pass it in); does not make network calls itself
- `atlas/analysis/portfolio.py` — accepts `CompanyPortfolioProfile` from providers; does not call providers itself
- `atlas/providers/base.py` and `atlas/providers/mock.py` import from `atlas/analysis/company_analysis.py` and `atlas/analysis/portfolio.py` — these are TYPE_CHECKING imports in `base.py`; runtime in `mock.py`
- No remaining analysis module makes direct network calls
- Demo and release verification remain provider-free (mock provider only)

---

## Architecture Boundaries (Sprint 108 state)

- `atlas/domains/` does **not** import from `atlas.analysis` ✓ (confirmed by AST scan, Sprint 108 guardrail test)
- `atlas/capabilities/` does **not** import from `atlas.analysis` ✓
- `atlas.analysis.watchlist` is fully deleted ✓
- `atlas.analysis.comparison` is fully deleted ✓
- `atlas.analysis.memory` is fully deleted ✓
- No stale `WatchlistEngine`, `ComparisonEngine`, `MemoryEngine`, `ExplanationEngine`, `RecommendationEngine` re-exports in `atlas.analysis` ✓
- `render_company_analysis_report` is fully removed ✓
- Active deprecated CLI command count: 0 ✓

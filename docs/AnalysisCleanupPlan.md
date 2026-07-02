# Analysis Package Cleanup Plan

**Created:** 2026-07-02 (Sprint 102)  
**Status:** ACTIVE — Sprint 103 complete: `ComparisonEngine` retired. Next target: `MemoryEngine` (Sprint 104+)

---

## Background

After Sprints 99–101, the `atlas/analysis/watchlist.py` module was fully deleted and its types
migrated to `atlas/capabilities/watchlist_intelligence/`. `atlas/analysis/` still contains 16
remaining modules. This document tracks the cleanup roadmap for those modules.

---

## Remaining `atlas/analysis/` Inventory (Sprint 102 state)

| File | Lines | Public API | Re-exported from `__init__` | Cleanup Category |
|---|---|---|---|---|
| `__init__.py` | 74 | Re-export hub | — | Shrinks with each migration |
| `company_analysis.py` | 45 | `CompanyAnalysis`, `MockCompanyAnalysisProvider`, `create_placeholder_company_analysis` | Yes | Still active legacy — heavily used by providers, tests |
| `comparison.py` | 199 | `ComparisonEngine`, `ComparisonResult`, `ComparisonCandidate`, `ComparisonRanking`, `render_comparison_result` | Yes | **Sprint 103 candidate** |
| `engine.py` | 229 | `AtlasInvestmentEngine`, `InvestmentReport`, `ScoreCategory`, `iter_score_categories` | Yes | Still active legacy — core scoring engine, many callers |
| `explanation.py` | 204 | `ExplanationEngine`, `InvestmentExplanation`, `explain_investment_report`, `render_investment_explanation` | Yes | Still active legacy |
| `growth.py` | 18 | `GrowthAnalysis`, `placeholder_growth_analysis` | No | Sub-module of company_analysis; leave unchanged |
| `macro.py` | 18 | `MacroAnalysis`, `placeholder_macro_analysis` | No | Sub-module of company_analysis; leave unchanged |
| `memory.py` | 255 | `MemoryEngine`, `MemoryEntry`, `MemoryStore`, `MemoryComparison`, `render_memory_entries`, `render_memory_comparison` | Yes | Active CLI path — defer after ComparisonEngine |
| `moat.py` | 18 | `MoatAnalysis`, `placeholder_moat_analysis` | No | Sub-module of company_analysis; leave unchanged |
| `portfolio.py` | 457 | `Portfolio`, `PortfolioPosition`, `PortfolioAnalysis`, `PortfolioIntelligenceEngine`, `PortfolioRecommendation`, `CompanyPortfolioProfile`, `get_mock_company_portfolio_profile`, `render_portfolio_analysis` | Yes | Highest-coupling module — largest migration; leave for later |
| `quality.py` | 18 | `QualityAnalysis`, `placeholder_quality_analysis` | No | Sub-module; leave unchanged |
| `report.py` | 43 | `build_investment_report`, `render_investment_report` | Yes | Still active legacy |
| `scores.py` | 2 | `clamp_score` | No | Utility; used by 7+ modules; leave unchanged |
| `scoring.py` | 59 | `ScoringEngine`, `RecommendationEngine`, `score_company` | Yes | Still active legacy |
| `sentiment.py` | 18 | `SentimentAnalysis`, `placeholder_sentiment_analysis` | No | Sub-module; leave unchanged |
| `technicals.py` | 18 | `TechnicalAnalysis`, `placeholder_technical_analysis` | No | Sub-module; leave unchanged |
| `valuation.py` | 18 | `ValuationAnalysis`, `placeholder_valuation_analysis` | No | Sub-module; leave unchanged |

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

### Recommended action: DEFER — after ComparisonEngine

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
| 104+ | `atlas/analysis/memory.py` | Audit `atlas memory` CLI commands; consider retire or migrate | MEDIUM-HIGH |
| Future | `atlas/analysis/portfolio.py` | High-coupling migration; 10+ callers; long-term project | HIGH |
| Future | `atlas/analysis/engine.py` | Core scoring engine; 10+ callers; foundational — leave for late cleanup | VERY HIGH |
| Leave | `scores.py`, `growth.py`, `macro.py`, `moat.py`, `quality.py`, `sentiment.py`, `technicals.py`, `valuation.py` | Internal sub-modules; used only by `company_analysis.py`/`engine.py`; no direct cleanup needed | — |

---

## Provider Safety

- `ComparisonEngine.compare_tickers()` accepts a provider but does not make network calls — passes
  it to `AtlasInvestmentEngine` which calls `provider.get_company_analysis(ticker)`
- `MemoryEngine.save_ticker()` similarly passes provider to `AtlasInvestmentEngine`
- Both engines are **provider-accepting, not provider-calling** — they delegate to the investment engine
- Neither introduces new provider calls or broadens the provider boundary
- Demo and release verification remain provider-free (mock provider only)

---

## Architecture Boundaries (Sprint 102 state)

- `atlas/domains/` does not import from `atlas.analysis.comparison` or `atlas.analysis.memory` ✓
- `atlas/capabilities/` does not depend on either engine ✓
- `atlas.analysis.watchlist` is fully deleted ✓
- No stale `Watchlist`/`WatchlistItem` re-exports in `atlas.analysis` ✓
- Active deprecated CLI command count: 0 ✓

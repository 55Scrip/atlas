# Atlas Decision Package Cleanup Plan

**Created:** 2026-07-02 (Sprint 142)  
**Updated:** 2026-07-02 (Sprint 144)  
**Status:** CLOSED — Sprint 144. Decision cleanup track formally closed after Sprints 142–144.

## Final Stable State (Sprint 144)

`atlas/decision/` contains exactly 7 modules. No further cleanup planned until a new dead-code finding or a clear successor architecture emerges.

| Module | Status | Why it remains |
|---|---|---|
| `__init__.py` | Active re-export hub | 5 intentional exports, all healthy |
| `decision_engine.py` | Foundational — do not migrate | Composes portfolio fit, comparison, watchlist intelligence, memory; single external caller (`atlas/intelligence/engine.py`) |
| `decision_context.py` | Active DTO | Carries portfolio/watchlist/capital context; `Portfolio` TYPE_CHECKING-guarded |
| `decision_result.py` | Active DTO | Carries action, scores, optional rich context; `PortfolioFitResult` TYPE_CHECKING-guarded |
| `decision_renderer.py` | Active utility | `render_decision_result`; exported via `__init__` |
| `comparison.py` | Active — clean post-Sprint 143 | Canonical comparison location; `ComparisonCandidate`, `ComparisonRanking`, `ComparisonResult`, `compare_tickers`; dead renderer deleted |
| `memory.py` | Active — clean | Canonical memory location; 7 public symbols; `render_memory_entries` / `render_memory_comparison` used by CLI `atlas memory` commands |

## Active exports (`__init__.py` — 5 symbols)

`AtlasDecisionEngine` · `DecisionAction` · `DecisionContext` · `DecisionResult` · `render_decision_result`

## Deleted rendering path (Sprint 143)

`render_comparison_result` · `_render_ranking` · `_ranking_score` — all deleted Sprint 143, zero callers confirmed.

## Reopening condition

This track may be reopened when a new zero-caller dead function is found, when `decision_engine.py` has a clear Blueprint-aligned successor, or when the package accumulates new stale migration residue.

---

## Background

`atlas/decision/` is the primary decision reasoning package. It contains `AtlasDecisionEngine` and its supporting types, memory/history tracking, and score-ranking comparison. The package was cleaned in Sprints 103–104 (comparison and memory migrated here from `atlas/analysis/`). Sprint 142 is the first formal audit.

---

## `atlas/decision/` Inventory (Sprint 142 state)

**7 modules total (including `__init__.py`).**

| File | Lines | Public API | `__init__` export | External production callers | Category |
|---|---|---|---|---|---|
| `__init__.py` | 15 | 5 re-exports | — | `atlas/intelligence/engine.py` | Re-export hub — clean |
| `decision_context.py` | 23 | `DecisionContext` | Yes | `atlas/intelligence/engine.py` (via `__init__`) | DTO — active, clean |
| `decision_engine.py` | 474 | `AtlasDecisionEngine` | Yes | `atlas/intelligence/engine.py` | **Foundational engine** |
| `decision_renderer.py` | 32 | `render_decision_result` | Yes | `atlas/decision/__init__.py` (re-exported) | Renderer — active, clean |
| `decision_result.py` | 42 | `DecisionAction`, `DecisionResult` | Yes | `atlas/intelligence/engine.py` (via `__init__`) | DTO — active, clean |
| `comparison.py` | 186 | `ComparisonCandidate`, `ComparisonRanking`, `ComparisonResult`, `compare_tickers`, `render_comparison_result` | No | `decision_engine.py` (ComparisonResult, compare_tickers), `decision_result.py` (ComparisonResult) | Active — **one dead function** |
| `memory.py` | 238 | `MemoryEntry`, `MemoryComparison`, `MemoryStore`, `save_ticker`, `compare_memory`, `render_memory_entries`, `render_memory_comparison` | No | `atlas/cli/main.py`, `decision_context.py`, `decision_engine.py`, `decision_result.py` | Active — clean |

### Package exports (`__init__.py` — 5 symbols)

| Export | Source | Status |
|---|---|---|
| `AtlasDecisionEngine` | `decision_engine.py` | Active and intentional |
| `DecisionAction` | `decision_result.py` | Active and intentional |
| `DecisionContext` | `decision_context.py` | Active and intentional |
| `DecisionResult` | `decision_result.py` | Active and intentional |
| `render_decision_result` | `decision_renderer.py` | Active and intentional |

No stale exports. `comparison.py` and `memory.py` symbols are not in `__init__.py` — callers import from them directly (CLI for memory, `decision_engine.py` for both). This is correct.

---

## Module Details

### `decision_engine.py` (474 lines)

**Main responsibility:** `AtlasDecisionEngine.decide()` — the primary decision reasoning path. Composes portfolio fit analysis (`PortfolioIntelligenceCapability`), score-ranking comparison (`compare_tickers`), watchlist intelligence, historical memory comparison, and 8 private scoring helpers into a `DecisionResult`.

**Dependencies (all active):**
- `atlas.adapters.portfolio` — `legacy_portfolio_to_domain_portfolio`
- `atlas.analysis.engine` — `AtlasInvestmentEngine`, `InvestmentReport`
- `atlas.analysis.scores` — `clamp_score`
- `atlas.capabilities.portfolio_intelligence` — `PortfolioFitResult`, `PortfolioIntelligenceCapability`
- `atlas.capabilities.watchlist_intelligence` — `WatchlistIntelligenceEngine`, `WatchlistIntelligenceInput`, `WatchlistIntelligenceReport`, `WatchlistItem`
- `atlas.decision.comparison` — `ComparisonResult`, `compare_tickers`
- `atlas.decision.memory` — `MemoryComparison`, `compare_memory`
- `atlas.decision.decision_context` — `DecisionContext`
- `atlas.decision.decision_result` — `DecisionAction`, `DecisionResult`
- `atlas.providers.base` — `CompanyDataProvider`

**No stale imports. Foundational — do not migrate.**

### `decision_context.py` (23 lines)

Clean frozen dataclass. `Portfolio` annotation TYPE_CHECKING-guarded. `WatchlistInput` runtime import is active. `MemoryStore` runtime import is active. No stale fields.

### `decision_result.py` (42 lines)

`PortfolioFitResult` is TYPE_CHECKING-guarded (correct — only used as a type annotation for the optional `portfolio_analysis` field). All runtime imports active. `ComparisonResult` and `MemoryComparison` are optional fields. No stale fields.

### `comparison.py` (186 lines)

**Canonical comparison location** — migrated from `atlas.analysis.comparison` (deleted Sprint 103). `ComparisonCandidate`, `ComparisonRanking`, `ComparisonResult`, `compare_tickers` are all active. `render_comparison_result` is defined but has **zero external callers** — not used by CLI, decision engine, or any test. This is a dead function.

### `memory.py` (238 lines)

**Canonical memory/history location** — migrated from `atlas.analysis.memory` (deleted Sprint 104). All 7 public symbols are active. `render_memory_entries` and `render_memory_comparison` are called by `atlas/cli/main.py` (`atlas memory show` and `atlas memory compare` commands). `explain_investment_report` import from `atlas.analysis.explanation` is active.

### `decision_renderer.py` (32 lines)

Clean 32-line renderer. Only caller is `atlas/decision/__init__.py`. No issues.

---

## Stale Import Audit

**Result: zero stale production imports in `atlas/decision/`.**

All stale symbol hits repo-wide are:
- Docstrings/migration notes in `atlas/capabilities/portfolio_intelligence/models.py` and `engine.py` — historical documentation only
- `atlas/cli/deprecations.py` — deprecation tracking strings (intentional)
- `atlas/adapters/portfolio.py` — docstring reference only
- Guardrail tests in `tests/test_portfolio_analyze_deprecation.py`, `tests/test_watchlist_analyze_deprecation.py`, `tests/test_intelligence_engine.py`, `tests/test_portfolio_intelligence_engine.py`, `tests/test_analysis_package_sprint140.py` — all asserting deleted symbols remain gone (intentional)

None are active production imports of deleted symbols.

---

## Blueprint Overlap Review

| Legacy module | Blueprint-aligned equivalent | Overlap type | Recommended action |
|---|---|---|---|
| `atlas/decision/decision_context.py` (`DecisionContext`) | `atlas/domains/decision/models.py` (`DecisionContext`) | Same name, different purpose. Domains version is evidence/research-oriented. Legacy version holds portfolio/watchlist/capital context for `AtlasDecisionEngine`. | Leave both. Different responsibilities. |
| `atlas/decision/decision_result.py` (`DecisionResult`) | `atlas/domains/decision/models.py` (`DecisionResult`) | Same name, different shape. Domains version wraps `DecisionCard`, `Evidence`, etc. Legacy version holds scores and action. | Leave both. Different layers. |
| `atlas/decision/comparison.py` | `atlas/comparison/engine.py` (`InvestmentComparisonEngine`) | Different purpose. Decision comparison is lightweight score-ranking (best-of-N). Blueprint comparison is research-framed evidence analysis used by CLI `atlas compare`. | Leave both. No migration warranted. |
| `atlas/decision/memory.py` | No Blueprint equivalent | No overlap | Leave in place |

No immediate migration warranted for any module. The legacy and domain layers serve different consumers.

---

## Dead Code Removed (Sprint 143)

**Deleted:**
- `render_comparison_result` (`comparison.py`) — zero external callers confirmed
- `_render_ranking` (`comparison.py`) — only called by deleted `render_comparison_result`
- `_ranking_score` (`comparison.py`) — only called by deleted `_render_ranking`

**Zero-caller audit:** all hits were definitions and internal-only calls within `comparison.py`. No external production callers. No CLI surface. No active test assertions.

`comparison.py` reduced from 186 to ~141 lines. Active API (`ComparisonCandidate`, `ComparisonRanking`, `ComparisonResult`, `compare_tickers`) preserved unchanged.

---

## Sprint 144 Target

**Decision package release checkpoint** — verify the decision package is stable after Sprint 143, confirm no further cleanup is warranted, and close the decision cleanup track if the package is clean.

# Atlas Home Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 161)  
**Status:** ACTIVE — Sprint 161 audit complete. Package is clean. No actionable cleanup candidates found. Sprint 162 recommended: close home cleanup track.

---

## Background

`atlas/home/` is a Group B provider-coupled module containing `AtlasHomeEngine`. The `atlas home` CLI command is active. The package imports `CompanyDataProvider` and `MockCompanyAnalysisProvider` from `atlas/providers/`, with network access strictly opt-in via `--provider yahoo`. It orchestrates multiple engines (portfolio review, watchlist review, market, economics, decision journal, language) into a unified daily briefing. No Blueprint-aligned successor exists.

---

## `atlas/home/` Package Inventory (Sprint 161 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 19 | Re-export hub — 7 exports |
| `engine.py` | 611 | Core engine — all logic |

---

## `engine.py` — Public API

| Symbol | Kind | Active production callers | Test callers | Status |
|---|---|---|---|---|
| `AtlasHomePriority` | frozen dataclass | Via `AtlasHomeOutput.priorities` | `test_home_engine.py` | **Active — output sub-type** |
| `AtlasHomeMonitoring` | frozen dataclass | Via `AtlasHomeOutput.monitoring` | `test_home_engine.py` | **Active — output sub-type** |
| `AtlasHomeSummary` | frozen dataclass | Via `AtlasHomeOutput.summary` | `test_home_engine.py` | **Active — output sub-type** |
| `AtlasHomeInput` | frozen dataclass | CLI (`atlas home`) | `test_home_engine.py` | **Active** |
| `AtlasHomeOutput` | frozen dataclass | CLI (returned by `.build()`) | `test_home_engine.py` | **Active — main output type** |
| `AtlasHomeEngine` | class | CLI | `test_home_engine.py` | **Active — core engine** |
| `render_atlas_home` | function | CLI | `test_home_engine.py` | **Active — CLI output** |

### `engine.py` — Private Helpers

All private helpers are fully internal and active.

| Symbol | Purpose |
|---|---|
| `_summary` | Builds `AtlasHomeSummary` from profile, portfolio review, market signals |
| `_priorities` | Builds up to 3 `AtlasHomePriority` items from portfolio/watchlist/market |
| `_watchlist_highlights` | Extracts top-3 relevant watchlist items |
| `_journal_reminders` | Builds review reminders from decision journal entries |
| `_monitoring_items` | Builds up to 5 deduplicated monitoring items |
| `_meaningful_changes` | Filters non-empty previous review notes |
| `_is_quiet_day` | Boolean: all signals calm and no pending reviews |
| `_quiet_day_summary` | Overrides summary with calm-day message |
| `_quiet_day_priorities` | Returns single "no action" priority |
| `_quiet_day_monitoring` | Returns 3 calm-day monitoring items |
| `_language_report` | Builds `AtlasLanguageReport` for the home output |
| `_section_observation` | Extracts first observation from a named report section |
| `_fit_from_rating` | Atlas rating string → fit string |
| `_confidence_level` | Score → `ConfidenceLevel` enum |
| `_bounded_confidence` | Clamps market score to [35, 90] |
| `_dedupe_monitoring` | Deduplicates monitoring items by lowercase key |
| `_default_market_snapshot` | Deterministic placeholder `MarketSnapshot` |
| `_render_priorities` | Formats `AtlasHomePriority` tuples as text lines |
| `_render_monitoring` | Formats `AtlasHomeMonitoring` tuples as text lines |
| `_render_list` | Formats string tuples as bullet list |

---

## `engine.py` — Imports from Other Atlas Packages

| Import | Package | Classification |
|---|---|---|
| `atlas.capabilities.watchlist_intelligence.WatchlistInput` | `atlas/capabilities/watchlist_intelligence/` | **Blueprint-aligned dependency** — `WatchlistInput` is a capability type. Correct direction. |
| `atlas.adapters.portfolio.Portfolio` | `atlas/adapters/portfolio` | TYPE_CHECKING guard only — not a runtime import. Used for type annotation in `AtlasHomeInput.portfolio`. |
| `atlas.decision_journal.DecisionJournalEngine`, `DecisionJournalEntry` | `atlas/decision_journal/` | Active engine dependency. |
| `atlas.economics.EconomicSignalsEngine` | `atlas/economics/` | Active engine dependency. |
| `atlas.language.*` | `atlas/language/` | Active — 8 imports. |
| `atlas.market.*` | `atlas/market/` | Active — 4 imports. |
| `atlas.portfolio_review.PortfolioReviewEngine`, `PortfolioReviewInput` | `atlas/portfolio_review/` | Active engine dependency. |
| `atlas.profile.InvestorProfile`, `atlas.profile.InvestorProfileEngine` | `atlas/profile/` | Active. |
| `atlas.providers.CompanyDataProvider` | `atlas/providers/` | Type annotation in `AtlasHomeInput.provider` field. |
| `atlas.providers.MockCompanyAnalysisProvider` | `atlas/providers/` | Default provider in `.build()` — deterministic, local. |
| `atlas.watchlist_review.WatchlistReviewEngine`, `WatchlistReviewInput`, `demo_watchlist_review_input` | `atlas/watchlist_review/` | Active — orchestrates watchlist review. |

**Notable:** `atlas/home/` uses `WatchlistInput` from `atlas/capabilities/watchlist_intelligence/` — this is a correct Blueprint-direction import (home consumes a capability type).

**Zero imports from deleted packages.** No `atlas.reasoning`, `atlas.analysis.portfolio`, `atlas.analysis.comparison`, etc.

---

## Export Review (`__init__.py`)

7 exports. All active.

| Export | Active? | Direct external callers |
|---|---|---|
| `AtlasHomeEngine` | ✓ | CLI, tests |
| `AtlasHomeInput` | ✓ | CLI, tests |
| `AtlasHomeMonitoring` | ✓ (sub-type) | Tests; accessed via `.monitoring` in production |
| `AtlasHomeOutput` | ✓ | CLI (returned type), tests |
| `AtlasHomePriority` | ✓ (sub-type) | Tests; accessed via `.priorities` in production |
| `AtlasHomeSummary` | ✓ (sub-type) | Tests; accessed via `.summary` in production |
| `render_atlas_home` | ✓ | CLI, tests |

**Finding:** All 7 exports are intentional. `AtlasHomePriority`, `AtlasHomeMonitoring`, and `AtlasHomeSummary` have zero direct external production callers but are correct sub-types of `AtlasHomeOutput`. Not cleanup candidates.

---

## `AtlasHomeEngine` Review

| Detail | Value |
|---|---|
| Source file | `atlas/home/engine.py:88` |
| Public methods | `.build(home_input: AtlasHomeInput \| None) → AtlasHomeOutput` |
| Constructor dependencies | 8 optional engine parameters (all default to `None` → instantiate defaults) |
| Provider dependency | `provider` injected via `AtlasHomeInput.provider`; falls back to `MockCompanyAnalysisProvider()` if `None` |
| Direct provider call | Passed through to `WatchlistReviewInput` — not called directly by `AtlasHomeEngine`; provider is consumed by `WatchlistReviewEngine` |
| Production callers | `atlas/cli/main.py` — `home_command` |
| Test callers | `tests/test_home_engine.py` — 15 tests |
| CLI callers | `atlas home [--profile] [--portfolio] [--watchlist] [--journal] [--provider]` |
| Returns Blueprint-aligned data? | No — returns `AtlasHomeOutput` (legacy type); but consumes `WatchlistInput` from Blueprint capability layer |
| Zero-caller methods | None — `.build()` is the only public method and is active |
| Stale compatibility logic | None found |

---

## Production Caller Map

**2 callers: CLI + tests.**

| Caller | Import | Symbols Used |
|---|---|---|
| `atlas/cli/main.py` | `from atlas.home import AtlasHomeEngine, AtlasHomeInput, render_atlas_home` | 3 of 7 |
| `tests/test_home_engine.py` | `from atlas.home import AtlasHomeEngine, AtlasHomeInput, render_atlas_home` | 3 of 7 |

No production engine outside CLI imports from `atlas/home/`.

---

## CLI Caller Review

### `atlas home`

| Detail | Value |
|---|---|
| Command | `atlas home [--profile path] [--portfolio path] [--watchlist path] [--journal path] [--provider mock\|yahoo]` |
| Implementation | `atlas/cli/main.py:300–343` |
| Imports used | `AtlasHomeEngine`, `AtlasHomeInput`, `render_atlas_home` |
| Provider selection | `_provider_from_name(provider_name)` — `"mock"` → `MockCompanyAnalysisProvider()`, `"yahoo"` → `YahooFinanceProvider()`. Default: `"mock"`. |
| Runtime behavior | Instantiates `AtlasHomeEngine()`, builds `AtlasHomeInput` from CLI args, calls `.build()`, renders via `render_atlas_home(output)` |
| Output shape | Depends on `render_atlas_home` |
| CLI behavior | Active and unchanged |
| Deprecated commands | None — `atlas home` is the only home CLI command |

---

## Provider Boundary Review

`atlas/home/engine.py` imports from `atlas/providers/` at module level:

```python
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider
```

| Symbol | Where used | How | Network? | Classification |
|---|---|---|---|---|
| `CompanyDataProvider` | `AtlasHomeInput.provider: CompanyDataProvider \| None` | Type annotation only | No | **Acceptable — abstract type annotation** |
| `MockCompanyAnalysisProvider` | `AtlasHomeEngine.build()` line 112 | Instantiated as default when `provider=None` | **No** — mock is deterministic, local | **Acceptable — mock default keeps network opt-in** |
| `YahooFinanceProvider` | Not in `atlas/home/`; only in `atlas/cli/main.py` via `_provider_from_name()` | CLI-selected | **Yes — opt-in via `--provider yahoo`** | **Acceptable — network is CLI-opt-in only** |

**Conclusion:** Provider coupling is intentional and clean. Identical pattern to `atlas/comparison/`. `YahooFinanceProvider` is never imported by `atlas/home/` itself.

---

## Blueprint Overlap Review

| Target | Overlap with `atlas/home/`? |
|---|---|
| `atlas/domains/` | No `atlas/domains/home/` exists. |
| `atlas/capabilities/` | No home capability exists. `atlas/home/` **consumes** `WatchlistInput` from `atlas/capabilities/watchlist_intelligence/` — correct direction. |
| `atlas/domains/daily_brief/` + `atlas/capabilities/daily_brief/` | `atlas/capabilities/daily_brief/` is a Blueprint-aligned daily briefing capability. Conceptual overlap with home (both produce daily context), but different scope: daily_brief is a multi-engine briefing; home is a personalized investor dashboard. Not a successor. |
| `atlas/decision/` | Decision journal is a dependency of home (not the reverse). No overlap. |
| `atlas/intelligence/` | Intelligence is a dependency of the daily brief capability, not home. No overlap. |
| `atlas/portfolio_review/` | Used as a dependency inside `AtlasHomeEngine`. Not a successor. |

**Notable overlap observation:** `atlas/capabilities/daily_brief/` and `atlas/home/` both produce daily context for investors. However:
- `daily_brief` focuses on market + intelligence + themes with optional portfolio context.
- `home` focuses on portfolio alignment + watchlist + decision journal + monitoring priorities.
- They are complementary, not redundant. No migration warranted.

**Conclusion:** No Blueprint-aligned successor exists for `atlas/home/`. Home is standalone and its orchestration role is unique.

---

## Stale Import Audit

**Zero stale closed-track symbols found in `atlas/home/`.**

Checked for all closed-track symbols:
- `atlas.reasoning`, `ReasoningEngine`, `ReasoningReport` — absent ✓
- `check_reasoning_report`, `check_intelligence_report`, `check_suitability_assessment` — absent ✓
- `atlas.analysis.portfolio`, `PortfolioAnalysis`, `PortfolioSignal` — absent ✓
- `atlas.analysis.comparison`, `render_comparison_result` — absent ✓
- `YahooCompany`, `YahooFinancials`, `YahooMarketData` — absent ✓
- `PortfolioIntelligenceEngine`, `portfolio_fit_input_from_profile` — absent ✓

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Sprint 162? |
|---|---|---|---|---|
| `AtlasHomePriority` | 0 direct external production callers; accessed via `.priorities` | 0 direct | LOW — correct sub-type of `AtlasHomeOutput`; removing would break type access | **No — leave unchanged** |
| `AtlasHomeMonitoring` | 0 direct external production callers; accessed via `.monitoring` | 0 direct | LOW — same reasoning | **No — leave unchanged** |
| `AtlasHomeSummary` | 0 direct external production callers; accessed via `.summary` | 0 direct | LOW — same reasoning | **No — leave unchanged** |
| All other symbols | All active — CLI, tests, or output sub-types | Active | N/A | Leave unchanged |

**Overall assessment:** The home package is clean. No dead code, no stale exports, no closed-track residue, no Blueprint migration pressure. All 7 exports are intentional. Provider coupling is clean and opt-in. The engine is an active orchestration hub with no zero-caller methods.

---

## Final Stable Package State (Sprint 161)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 19 | 7 exports — all intentional |
| `engine.py` | 611 | Active — `AtlasHomeEngine` orchestration hub with clean provider boundary |

**Provider safety:** Network access is opt-in only (`--provider yahoo`). Default is `MockCompanyAnalysisProvider` (deterministic, local). ✓

---

## Recommended Sprint 162 Target

**Close the home cleanup track.**

After inventory (Sprint 161), the home package contains no actionable cleanup candidates:
- All 7 exports are active or intentional sub-types
- No dead code or stale exports
- No closed-track import residue
- No Blueprint successor exists
- Provider boundary is clean and opt-in
- CLI is active and unchanged

Sprint 162 should be a documentation-only sprint confirming the audit findings and closing the home cleanup track. No code changes are needed. Pattern matches Sprint 150, 155, 158, and 160.

**Reopening condition:** If a Blueprint-aligned home capability emerges in `atlas/capabilities/`, if the CLI command is deprecated, or if new dead code or stale provider imports appear, this track should be reopened.

---

## Closed-Track Summary

| Track | Status |
|---|---|
| `atlas/analysis/` cleanup | CLOSED Sprint 141 |
| `atlas/decision/` cleanup | CLOSED Sprint 144 |
| Provider boundary audit | CLOSED Sprint 146 |
| Portfolio boundary | CLOSED Sprint 148 |
| Evidence package | CLOSED Sprint 150 |
| Reasoning package | CLOSED Sprint 153 |
| Risk package | CLOSED Sprint 155 |
| Principles package | CLOSED Sprint 158 |
| Comparison package | CLOSED Sprint 160 |
| **Home package** | **ACTIVE — Sprint 162 closure planned** |

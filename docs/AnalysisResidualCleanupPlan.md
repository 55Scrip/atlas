# Analysis Residual Cleanup Plan

**Created:** 2026-07-03 (Sprint 192)  
**Updated:** 2026-07-03 (Sprint 193)  
**Status:** CLOSED — Sprint 193 closed the active residual analysis runtime audit track preserved by Sprint 141. Three zero-caller provider re-exports removed from `atlas/analysis/__init__.py`. No runtime behavior changed.

---

## Important Framing

This document audits the **active residual analysis runtime surface preserved by Sprint 141**.  
Sprint 141 closed the main `atlas/analysis/` cleanup track by removing legacy analysis modules.  
Sprint 192 does NOT reopen the Sprint 141 cleanup track.  
Sprint 193 closes the active residual analysis runtime audit track. This is not a reopening of any prior track.

The surviving surface is intentional legacy runtime — clean, active, and well-bounded.

---

## Executive Summary

`atlas/analysis/` contains exactly **5 surviving Python modules** (652 lines total), all active and intentional. All 12 `__all__` exports have production callers. No stale exports. No dead helpers. No stale imports from deleted modules. No cross-imports with `atlas/capabilities/company_analysis/`. No network behavior. Provider coupling is intentional legacy runtime with opt-in behavior.

One minor finding: `atlas/analysis/__init__.py` re-exports `CompanyDataProvider`, `MockCompanyAnalysisProvider`, and `YahooFinanceProvider` from `atlas.providers` — but no production code and no test code imports these three symbols from `atlas.analysis` (the package root). All actual callers import directly from submodules (`atlas.analysis.engine`, `atlas.analysis.company_analysis`) or from `atlas.providers`. The re-exports are convenience aliases with zero callers — a low-priority cleanup candidate, not urgent.

---

## Package Inventory

### Surviving Modules

| Module | Lines | Role | Active |
|---|---|---|---|
| `__init__.py` | 26 | Re-exports 12 public symbols + 3 provider convenience re-exports | ✓ |
| `company_analysis.py` | 159 | `CompanyAnalysis` dataclass, 7 sub-analysis dataclasses, placeholder factories, `__getattr__` shim | ✓ |
| `engine.py` | 229 | `AtlasInvestmentEngine`, `InvestmentReport`, `ScoreCategory`, 5 scorers, `ThresholdRecommendationPolicy`, Protocols | ✓ |
| `explanation.py` | 198 | `InvestmentExplanation`, `explain_investment_report`, `render_investment_explanation` (9 private helpers) | ✓ |
| `report.py` | 38 | `build_investment_report`, `render_investment_report` | ✓ |
| `scores.py` | 2 | `clamp_score` — shared utility, not in `__all__`, 11 cross-package callers | ✓ |

**Total:** 652 lines, 5 modules.

---

### `atlas/analysis/company_analysis.py` (159 lines)

**Public exports in `__all__` (via `__init__.py`):** `CompanyAnalysis`, `create_placeholder_company_analysis`

**Additional public symbols (not in `__all__`):**
- 7 sub-analysis dataclasses: `GrowthAnalysis`, `MacroAnalysis`, `MoatAnalysis`, `QualityAnalysis`, `SentimentAnalysis`, `TechnicalAnalysis`, `ValuationAnalysis`
- 7 placeholder factory functions: `placeholder_growth_analysis`, `placeholder_macro_analysis`, etc.
- `__getattr__` shim for `MockCompanyAnalysisProvider` compatibility

**Comment block (lines 4–6):** Documents the Sprint 139 consolidation — these 7 sub-analysis dataclasses were formerly in separate files (`growth.py`, `macro.py`, etc.) that were deleted Sprint 139 after consolidation. Accurate historical note.

**`__getattr__` shim:** `MockCompanyAnalysisProvider` is not in `__all__` and is not a direct class definition here. The shim redirects to `atlas.providers.mock.MockCompanyAnalysisProvider`. **4 active test callers** use `from atlas.analysis.company_analysis import MockCompanyAnalysisProvider`. Shim is live and needed.

**Callers:**
- `atlas/analysis/engine.py` — `CompanyAnalysis`
- `atlas/analysis/report.py` — `CompanyAnalysis`
- `atlas/providers/mock.py` — `CompanyAnalysis`, `create_placeholder_company_analysis`
- `atlas/providers/yahoo.py` — `CompanyAnalysis`, `create_placeholder_company_analysis`
- `atlas/providers/base.py` — `CompanyAnalysis` (type annotation, TYPE_CHECKING guard)
- `tests/test_explanation.py`, `tests/test_investment_engine.py`, `tests/test_memory.py`, `tests/test_scoring.py` — `MockCompanyAnalysisProvider` via shim

---

### `atlas/analysis/engine.py` (229 lines)

**Public exports in `__all__`:** `AtlasInvestmentEngine`, `InvestmentReport`, `ScoreCategory`

**Additional active public symbols (not in `__all__`):**
- `iter_score_categories` — imported by `report.py`, `explanation.py`, `decision/memory.py`, tests
- `ThresholdRecommendationPolicy` — imported by tests (`test_investment_engine.py`, `test_scoring.py`); used as default in `AtlasInvestmentEngine.__init__`
- `CategoryScorer` Protocol — type annotation only, internal
- `RecommendationPolicy` Protocol — type annotation only, internal
- `DEFAULT_CATEGORY_WEIGHTS`, `DEFAULT_CATEGORY_SCORERS` — module-level defaults
- 5 scorer classes: `QualityScorer`, `GrowthScorer`, `ValuationScorer`, `FinancialStrengthScorer`, `RiskScorer` — used in `DEFAULT_CATEGORY_SCORERS`

**Provider import:** `from atlas.providers.base import CompanyDataProvider` — used as type annotation for `analyze_ticker(self, ticker, provider: CompanyDataProvider)`. Type-only Protocol import. No runtime provider construction here.

**Callers:** `atlas/cli/main.py`, `atlas/comparison/engine.py`, `atlas/conversation/engine.py`, `atlas/decision/`, `atlas/intelligence/engine.py`, `atlas/monitoring/engine.py`, `atlas/models/investment_report.py`, `atlas/suitability/engine.py`, tests.

---

### `atlas/analysis/explanation.py` (198 lines)

**Public exports in `__all__`:** `InvestmentExplanation`, `explain_investment_report`

**Additional active symbol (not in `__all__`):** `render_investment_explanation` — imported by `report.py` and tests. Active.

**9 private helpers:** `_rank_categories`, `_bull_case`, `_bear_case`, `_category_strength`, `_category_risk`, `_key_risks`, `_valuation_concern`, `_mind_changers`, `_confidence_explanation`, `_format_bullets` — all internal. Active.

**No imports from deleted modules. No provider imports. No CLI imports.**

---

### `atlas/analysis/report.py` (38 lines)

**Public exports in `__all__`:** `build_investment_report`, `render_investment_report`

**Private helper:** `_score_line` — internal only.

**Callers:** `atlas/cli/main.py` (3 call sites: `atlas report`, `atlas analyze`, `atlas suitability` path), `atlas/comparison/engine.py`, `atlas/decision/memory.py`, tests.

---

### `atlas/analysis/scores.py` (2 lines)

**Not in `__all__`.** Single function: `clamp_score(score: int) -> int`.

**11 active callers across 11 packages:** `atlas/analysis/engine.py`, `atlas/adapters/portfolio.py`, `atlas/comparison/engine.py`, `atlas/decision/decision_engine.py`, `atlas/economics/engine.py`, `atlas/market/health.py`, `atlas/market/regime.py`, `atlas/monitoring/engine.py`, `atlas/risk/engine.py`, `atlas/risk_drift/engine.py`, `atlas/suitability/engine.py`.

`clamp_score` is the most widely-used non-exported utility in the codebase. It is a genuine shared utility that serves many packages. **No cleanup warranted.**

---

## Export Review

### `atlas/analysis/__init__.py` — `__all__` (12 exports)

| Export | Source | Active | Production callers |
|---|---|---|---|
| `AtlasInvestmentEngine` | `engine.py` | ✓ | cli, comparison, conversation, decision, intelligence, monitoring |
| `CompanyAnalysis` | `company_analysis.py` | ✓ | providers, engine, report, tests |
| `CompanyDataProvider` | `atlas.providers` re-export | ✓ | No caller imports from `atlas.analysis` root — callers use `atlas.providers` or `atlas.providers.base` directly |
| `InvestmentExplanation` | `explanation.py` | ✓ | tests |
| `InvestmentReport` | `engine.py` | ✓ | decision, models, suitability, intelligence, monitoring |
| `MockCompanyAnalysisProvider` | `atlas.providers` re-export | ✓ | No caller imports from `atlas.analysis` root — callers use `atlas.providers` or shim via `company_analysis` |
| `ScoreCategory` | `engine.py` | ✓ | decision, models, suitability, tests |
| `YahooFinanceProvider` | `atlas.providers` re-export | ✓ | No caller imports from `atlas.analysis` root — callers use `atlas.providers` |
| `build_investment_report` | `report.py` | ✓ | cli (3 paths), comparison, decision |
| `create_placeholder_company_analysis` | `company_analysis.py` | ✓ | providers (mock, yahoo) |
| `explain_investment_report` | `explanation.py` | ✓ | decision/memory, tests |
| `render_investment_report` | `report.py` | ✓ | cli |

### Provider re-export finding (cleanup candidate)

`atlas/analysis/__init__.py:11` re-exports `CompanyDataProvider`, `MockCompanyAnalysisProvider`, `YahooFinanceProvider` from `atlas.providers`:

```python
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider, YahooFinanceProvider
```

These three symbols appear in `__all__`, but **no production code and no test code imports them from `atlas.analysis` (the package root)**. All actual callers import from `atlas.providers`, `atlas.providers.base`, or `atlas.analysis.company_analysis` (via shim). The re-exports are convenience aliases with zero callers.

**Classification:** Zero-caller re-exports in `__init__.py`. Low-priority cleanup candidate. Safe to remove in a future sprint — removal would not break any caller.

**Risk level:** Low. No callers affected. However, this should be verified one final time before removal to avoid surprises.

---

## CLI Caller Review

### `atlas report` (`atlas/cli/main.py:200`)

```
atlas report <ticker> [--provider mock|yahoo]
```

- Calls `provider.get_company_analysis(ticker)` → `build_investment_report(analysis)` → `render_investment_report(report)`
- Provider: mock default (deterministic), yahoo opt-in
- Output: `InvestmentReport` rendered as text
- Active, unchanged

### `atlas analyze` (`atlas/cli/main.py:247`)

```
atlas analyze <ticker> [--provider mock|yahoo]
```

- Same pipeline as `atlas report` — identical logic, separate command
- Active, unchanged

### `build_investment_report` in `atlas suitability` path (`atlas/cli/main.py:1402`)

- Used in the suitability command when subject is a ticker
- Builds `InvestmentReport` for use in `SuitabilityEngine`
- Active, unchanged

### `atlas/comparison/engine.py`

- `build_investment_report` called per ticker to build `InvestmentReport` objects for comparison
- Active production caller

---

## Capability Boundary Review

| Direction | Status |
|---|---|
| `atlas/analysis/` → `atlas/capabilities/company_analysis/` | **Absent** ✓ — no cross-import |
| `atlas/capabilities/company_analysis/` → `atlas/analysis/` | **Absent** ✓ — confirmed Sprint 182, re-confirmed Sprint 192 |

**Two distinct output types on two distinct paths:**

| Layer | Input type | Output type | CLI path |
|---|---|---|---|
| Legacy residual (`atlas/analysis/`) | `CompanyAnalysis` | `InvestmentReport` | `atlas report`, `atlas analyze` |
| Blueprint capability (`atlas/capabilities/company_analysis/`) | `CompanyAnalysisInput` | `CompanyAnalysisReport` | `atlas company-analysis export`, `atlas daily summary --company-analysis` |

The two layers share the concept of "company analysis" but produce structurally different outputs for different purposes. The duplication is **intentional** — `InvestmentReport` is legacy scoring output; `CompanyAnalysisReport` is Blueprint capability output. No consolidation warranted.

---

## Provider Boundary Review

| Location | Provider import | Type | Network access |
|---|---|---|---|
| `atlas/analysis/__init__.py` | `CompanyDataProvider, MockCompanyAnalysisProvider, YahooFinanceProvider` from `atlas.providers` | Convenience re-exports only — zero callers use them from this location | None |
| `atlas/analysis/engine.py` | `CompanyDataProvider` from `atlas.providers.base` | Protocol type annotation for `analyze_ticker` param | None |
| `atlas/analysis/company_analysis.py` | `MockCompanyAnalysisProvider` via `__getattr__` shim | Lazy import in shim — only triggered if directly imported | None |
| `atlas/analysis/report.py` | None | — | None |
| `atlas/analysis/explanation.py` | None | — | None |
| `atlas/analysis/scores.py` | None | — | None |

**No module in `atlas/analysis/` performs network access.**  
`engine.py`'s `analyze_ticker(ticker, provider)` receives a provider as constructor argument — it does not construct or select the provider. Provider selection happens in `atlas/cli/main.py` via `_provider_from_name()`. Provider boundary is correctly maintained.

---

## Deleted Analysis Module Verification

All Sprint 141 deleted modules confirmed absent. **Unchanged from Sprint 191.**

| Deleted module | Status |
|---|---|
| `atlas/analysis/portfolio.py` | Absent ✓ |
| `atlas/analysis/growth.py` | Absent ✓ |
| `atlas/analysis/macro.py` | Absent ✓ |
| `atlas/analysis/moat.py` | Absent ✓ |
| `atlas/analysis/quality.py` | Absent ✓ |
| `atlas/analysis/sentiment.py` | Absent ✓ |
| `atlas/analysis/technicals.py` | Absent ✓ |
| `atlas/analysis/valuation.py` | Absent ✓ |

No surviving `atlas/analysis/` module imports from any deleted submodule. ✓

---

## Stale Import Audit

Searched all surviving `atlas/analysis/` modules for stale references from all closed cleanup tracks.

| Search term | Found in residual analysis? | Classification |
|---|---|---|
| `atlas.reasoning` | Not found | ✓ |
| `atlas.analysis.portfolio` | Not found | ✓ |
| `atlas.analysis.growth/.macro/.moat/.quality/.sentiment/.technicals/.valuation` | Not found | ✓ |
| `atlas.analysis.comparison/.memory/.scoring/.watchlist` | Not found | ✓ |
| `CompanyAnalysisProvider` | Found in `company_analysis.py:155` — **inside `__getattr__` shim only** | `__getattr__` shim string comparison, not an import — expected ✓ |
| `YahooCompany/YahooFinancials/YahooMarketData` | Not found in analysis modules | ✓ (defined in `atlas/providers/yahoo.py` — active) |
| `PortfolioAnalysis/PortfolioSignal/PortfolioRecommendation/CompanyPortfolioProfile` | Not found | ✓ |
| `ReasoningEngine` | Not found in analysis modules | ✓ (distinct active class in `atlas/domains/decision/engine.py`) |

**No stale active imports.** ✓

---

## Blueprint / Residual Analysis Model Review

| Criterion | Assessment |
|---|---|
| Is residual analysis intentionally legacy runtime? | ✓ Yes — preserved by Sprint 141, active CLI surface (`atlas report`, `atlas analyze`) |
| Is residual analysis Blueprint-aligned? | No — it is the legacy scoring layer. Intentional. |
| Does it duplicate `company_analysis` capability models? | No — `InvestmentReport` ≠ `CompanyAnalysisReport`. Different data shapes for different CLI paths. |
| Does it duplicate rendering? | No — `render_investment_report` produces a different output format than capability exporters |
| Does it duplicate scoring? | No — `AtlasInvestmentEngine` scoring is distinct from `CompanyAnalysisEngine` |
| Should provider coupling in `analyze_ticker` be moved? | No — `analyze_ticker` receives provider as argument (constructor-injected). The boundary is already correct. |
| Would migration change behavior? | Yes — migration is out of scope and would change the legacy CLI surface |
| Should residual analysis remain active? | Yes — it powers `atlas report`, `atlas analyze`, comparison, decision, monitoring pipelines |

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Outcome |
|---|---|---|---|---|
| `CompanyDataProvider`, `MockCompanyAnalysisProvider`, `YahooFinanceProvider` re-exports in `atlas/analysis/__init__.py` | These 3 of 12 `__all__` exports were provider convenience re-exports. Zero production callers and zero test callers imported them from `atlas.analysis` root. All actual callers import from `atlas.providers` or submodules directly. | 0 callers from root | Low | **Removed Sprint 193** |
| All other exports (`AtlasInvestmentEngine`, `CompanyAnalysis`, `InvestmentReport`, etc.) | Active production callers | Multiple | — | Leave unchanged |
| `clamp_score` in `scores.py` (not in `__all__`) | 11 active callers across 11 packages | 11 | — | Leave unchanged |
| `iter_score_categories` (not in `__all__`) | Active callers in `report.py`, `explanation.py`, `decision/memory.py`, tests | 4+ | — | Leave unchanged |
| `ThresholdRecommendationPolicy` (not in `__all__`) | Active test callers; used as default in engine | Tests + engine | — | Leave unchanged |
| `render_investment_explanation` (not in `__all__`) | Active callers in `report.py` and tests | 2+ | — | Leave unchanged |
| `__getattr__` shim for `MockCompanyAnalysisProvider` | 4 active test callers import from `atlas.analysis.company_analysis` | 4 | — | Leave unchanged |

**Summary:** Sprint 193 removed the 3 zero-caller provider re-exports. `__all__` reduced from 12 to 9. Everything else is active and intentional.

---

## Sprint 193 Closure

**Decision:** Close the active residual analysis runtime audit track preserved by Sprint 141.

**Provider re-export removal:** `CompanyDataProvider`, `MockCompanyAnalysisProvider`, and `YahooFinanceProvider` removed from `atlas/analysis/__init__.py` and `__all__`. All 3 removal conditions were satisfied:
- Zero production callers imported them from `atlas.analysis` root
- Zero test callers (guardrail tests updated to assert absence)
- Removal does not change runtime behavior — provider selection occurs at `atlas/cli/main.py` via `_provider_from_name()`
- Callers import from `atlas.providers`, `atlas.providers.base`, or `atlas.analysis.company_analysis` (shim) directly

**Exports after Sprint 193:** 9 active symbols (all have production callers):
`AtlasInvestmentEngine`, `CompanyAnalysis`, `InvestmentExplanation`, `InvestmentReport`, `ScoreCategory`, `build_investment_report`, `create_placeholder_company_analysis`, `explain_investment_report`, `render_investment_report`

**Tests updated:** `tests/test_analysis_residual_sprint192.py` (export count 12→9, added 3 absence assertions), `tests/test_analysis_package_sprint140.py` (export count 12→9, expected set updated).

**Final verification:** 1648 passed, 3 skipped | RC2 green | Demo passes ✓

---

## Reopening Conditions

This plan may be reopened if:
- A stale import from a deleted analysis module appears in surviving code
- A new export is added to `__all__` without production callers
- `atlas/capabilities/company_analysis/` begins importing from `atlas/analysis/`
- `clamp_score` is proposed for removal (would affect 11 callers)
- The `__getattr__` shim for `MockCompanyAnalysisProvider` is broken

---

## Sprint 193 Verification Table

| Check | Result |
|---|---|
| Surviving modules | 5 (.py files) + `__init__.py` ✓ |
| `__all__` export count | 9 (reduced from 12; 3 zero-caller provider re-exports removed) ✓ |
| All 9 remaining exports importable | ✓ |
| `CompanyDataProvider` absent from `atlas.analysis.__all__` | ✓ |
| `MockCompanyAnalysisProvider` absent from `atlas.analysis.__all__` | ✓ |
| `YahooFinanceProvider` absent from `atlas.analysis.__all__` | ✓ |
| `clamp_score` importable from `scores.py` | ✓ |
| Sprint 141 deleted modules absent | 8/8 ✓ |
| Stale imports from deleted modules | None ✓ |
| `atlas.analysis` → `atlas.capabilities.company_analysis` | Absent ✓ |
| `atlas.capabilities.company_analysis` → `atlas.analysis` | Absent ✓ |
| `atlas.domains` → `atlas.analysis` | Absent ✓ |
| `CompanyAnalysisProvider` absent from active namespace | ✓ |
| `MockCompanyAnalysisProvider` shim active | ✓ (4 test callers) |
| Network access in surviving modules | None ✓ |
| Provider boundary | Correct — `analyze_ticker` receives provider as argument ✓ |
| Capability boundary | Clean bidirectional separation ✓ |
| No runtime behavior changed | ✓ |
| Compile check | Green ✓ |
| Full test suite | **1648 passed, 3 skipped** ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Track status | **CLOSED Sprint 193** ✓ |

---

## Sprint 192 Verification Table

| Check | Result |
|---|---|
| Surviving modules | 5 (.py files) + `__init__.py` ✓ |
| Total lines | 652 ✓ |
| `__all__` export count | 12 ✓ |
| All 12 exports importable | ✓ |
| `clamp_score` importable from `scores.py` | ✓ |
| Sprint 141 deleted modules absent | 8/8 ✓ |
| Stale imports from deleted modules | None ✓ |
| `atlas.analysis` → `atlas.capabilities.company_analysis` | Absent ✓ |
| `atlas.capabilities.company_analysis` → `atlas.analysis` | Absent ✓ |
| `atlas.domains` → `atlas.analysis` | Absent ✓ |
| `CompanyAnalysisProvider` absent from active namespace | ✓ |
| `MockCompanyAnalysisProvider` shim active | ✓ (4 test callers) |
| Zero-caller provider re-exports in `__init__.py` | Found: 3 (low-priority candidate) |
| Network access in surviving modules | None ✓ |
| Provider boundary | Correct — `analyze_ticker` receives provider as argument ✓ |
| Capability boundary | Clean bidirectional separation ✓ |
| Compile check | Green ✓ |
| Full test suite | **1647 passed, 3 skipped** ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Behavior changes | None |

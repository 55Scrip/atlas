# Atlas Intelligence Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 164)  
**Status:** ACTIVE — audit-first sprint. No cleanup action taken. Sprint 165 recommended: close the intelligence cleanup track (documentation-only, no code changes warranted).

---

## Background

`atlas/intelligence/` is a self-contained orchestration hub that synthesizes outputs from multiple Atlas engines into a single deterministic `IntelligenceReport`. It is active, well-bounded, and has an active CLI command (`atlas intelligence analyze`). It has no deleted-module imports. Sprint 164 is the audit-first sprint following the 10 cleanup track closure sequence.

---

## `atlas/intelligence/` Package Inventory (Sprint 164 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 15 | Re-export hub — 5 exports |
| `engine.py` | 469 | Core engine + dataclasses + renderer + private helpers |

---

## `engine.py` — Public API

| Symbol | Kind | Active production callers | Test callers | Status |
|---|---|---|---|---|
| `IntelligenceContext` | frozen dataclass | CLI (`intelligence_analyze_command`, `daily_summary_command`), `atlas/conversation/engine.py` | `test_intelligence_engine.py` | **Active** |
| `IntelligenceInput` | frozen dataclass | CLI (2 call sites), `atlas/conversation/engine.py` | `test_intelligence_engine.py` | **Active** |
| `IntelligenceReport` | frozen dataclass | CLI, `atlas/conversation/engine.py`, `atlas/suitability/engine.py` | `test_intelligence_engine.py` | **Active — consumed by suitability and conversation** |
| `IntelligenceEngine` | class | CLI (2 call sites), `atlas/conversation/engine.py` | `test_intelligence_engine.py` | **Active — core orchestration engine** |
| `render_intelligence_report` | function | CLI (`intelligence_analyze_command`) | `test_intelligence_engine.py` | **Active** |

### `engine.py` — Private Helpers

All private helpers are internal and active — called by `IntelligenceEngine.analyze()` or `render_intelligence_report()`.

| Symbol | Purpose | Callers |
|---|---|---|
| `_optional_portfolio_analysis` | Runs `PortfolioIntelligenceCapability` if portfolio supplied | `analyze()` |
| `_optional_watchlist_intelligence` | Runs `WatchlistIntelligenceEngine` if watchlist supplied | `analyze()` |
| `_default_market_snapshot` | Returns deterministic placeholder `MarketSnapshot` | `analyze()` |
| `_confidence` | Weighted confidence score from 8 sub-signals | `analyze()` |
| `_executive_summary` | Builds text executive summary | `analyze()` |
| `_structural_tailwinds` | Builds tailwind tuple from `ThemeAnalysis` | `analyze()` |
| `_current_market_environment` | Builds environment tuple from market regime + health | `analyze()` |
| `_company_positioning` | Builds positioning tuple from `InvestmentReport` sub-scores | `analyze()` |
| `_portfolio_impact` | Builds impact tuple from `PortfolioFitResult` (or defaults) | `analyze()` |
| `_risk_assessment` | Builds risk tuple; optionally extends with `RiskAnalysis` fields | `analyze()` |
| `_atlas_conclusion` | Builds conclusion text | `analyze()` |
| `_monitoring_items` | Builds monitoring tuple; optionally appends `RiskAnalysis` field | `analyze()` |
| `_what_could_change_view` | Builds uncertainty tuple | `analyze()` |
| `_render_list` | Formats `tuple[str, ...]` as bullet lines | `render_intelligence_report()` |

**Zero zero-caller private helpers found.**

---

## `IntelligenceEngine` Review

| Detail | Value |
|---|---|
| Source file | `atlas/intelligence/engine.py:81` |
| Public methods | `.analyze(IntelligenceInput) → IntelligenceReport` |
| Constructor dependencies | 6 optional engine parameters (all default to `None` → instantiate defaults) |
| Provider dependency | `provider` injected via `IntelligenceInput.provider`; passed through to `AtlasInvestmentEngine`, `PortfolioIntelligenceCapability`, and `AtlasDecisionEngine` — never called directly by `IntelligenceEngine` |
| Provider: network? | No direct network calls. Network is CLI opt-in via `--provider yahoo`. |
| `RiskAnalysis` dependency | `RiskAnalysis` consumed from `IntelligenceContext.risk_analysis` (optional, caller-supplied). Not produced internally. |
| Production callers | CLI (`intelligence_analyze_command`, `daily_summary_command`), `atlas/conversation/engine.py` |
| Test callers | `tests/test_intelligence_engine.py` — multiple tests |
| CLI callers | `atlas intelligence analyze [TICKER]`, `atlas daily summary` (indirectly via `_report_command`) |
| Returns Blueprint-aligned data? | No — returns `IntelligenceReport` (legacy type). Consumes Blueprint-aligned types: `PortfolioFitResult`, `WatchlistIntelligenceReport`, `DecisionResult`. |
| Zero-caller public methods | None — `.analyze()` is the only public method and is active |
| Stale compatibility logic | None found |

---

## Export Review (`__init__.py`)

5 exports. All active.

| Export | Active? | Direct external callers |
|---|---|---|
| `IntelligenceContext` | ✓ | CLI, `atlas/conversation/engine.py` |
| `IntelligenceEngine` | ✓ | CLI, `atlas/conversation/engine.py` |
| `IntelligenceInput` | ✓ | CLI, `atlas/conversation/engine.py` |
| `IntelligenceReport` | ✓ | CLI, `atlas/conversation/engine.py`, `atlas/suitability/engine.py` |
| `render_intelligence_report` | ✓ | CLI, tests |

**Finding:** All 5 exports are active. No stale exports. No export removal candidates.

---

## Production Caller Map

**4 production callers: CLI (2 commands), conversation, suitability.**

| Caller | Import | Symbols Used |
|---|---|---|
| `atlas/cli/main.py:intelligence_analyze_command` | `from atlas.intelligence import IntelligenceContext, IntelligenceEngine, IntelligenceInput, render_intelligence_report` | 4 of 5 |
| `atlas/cli/main.py:daily_summary_command` (via `_report_command`) | Same import block | 3 of 5 (no `render_intelligence_report`) |
| `atlas/conversation/engine.py` | `from atlas.intelligence import IntelligenceContext, IntelligenceEngine, IntelligenceInput` | 3 of 5 |
| `atlas/suitability/engine.py` | `from atlas.intelligence import IntelligenceReport` | 1 of 5 |

---

## CLI Caller Review

### `atlas intelligence analyze`

| Detail | Value |
|---|---|
| Command | `atlas intelligence analyze TICKER [portfolio.json] [--provider mock\|yahoo] [--theme "..."]` |
| Implementation | `atlas/cli/main.py:484–505` |
| Imports used | `IntelligenceContext`, `IntelligenceEngine`, `IntelligenceInput`, `render_intelligence_report` |
| Provider selection | `_provider_from_name(provider_name)` — `"mock"` → `MockCompanyAnalysisProvider()`, `"yahoo"` → `YahooFinanceProvider()`. Default: `"mock"`. |
| Runtime behavior | Parses inputs, instantiates `IntelligenceEngine()`, builds `IntelligenceInput`, calls `.analyze()`, prints via `render_intelligence_report()` |
| CLI behavior | Active and unchanged |

### `atlas daily summary` (secondary caller)

`IntelligenceEngine` is also called from `_report_command` (line 1410), which backs `atlas daily summary`. This call passes no portfolio and no `risk_analysis` — pure theme + provider context only.

---

## Dependency Boundary Review

| Dependency | Import location | Classification | Direction acceptable? | Stable? |
|---|---|---|---|---|
| `atlas.adapters.portfolio` | `legacy_portfolio_to_domain_portfolio` (runtime), `Portfolio` (TYPE_CHECKING) | Adapter conversion function | ✓ | ✓ |
| `atlas.analysis.engine` | `AtlasInvestmentEngine`, `InvestmentReport` (runtime) | Investment engine dependency | ✓ (analysis engine, not deleted analysis modules) | ✓ |
| `atlas.capabilities.portfolio_intelligence` | `PortfolioIntelligenceCapability`, `PortfolioFitResult` (TYPE_CHECKING) | Blueprint-aligned capability | ✓ correct direction | ✓ |
| `atlas.capabilities.watchlist_intelligence` | `WatchlistInput`, `WatchlistIntelligenceEngine`, models (runtime) | Blueprint-aligned capability | ✓ correct direction | ✓ |
| `atlas.decision` | `AtlasDecisionEngine`, `DecisionContext`, `DecisionResult` (runtime) | Active decision layer | ✓ | ✓ |
| `atlas.market` | 6 types (runtime) | Market data types | ✓ | ✓ |
| `atlas.providers` | `CompanyDataProvider` (runtime type annotation) | Abstract type annotation | ✓ | ✓ |
| `atlas.risk` | `RiskAnalysis` (runtime) | Optional context field | ✓ intentional — see RiskAnalysis review | ✓ |
| `atlas.themes` | `ThemeAnalysis`, `ThemeEngine`, `ThemeInput` (runtime) | Theme engine dependency | ✓ | ✓ |

**No circular dependencies.** Intelligence imports from analysis, decision, capabilities, market, risk, themes, providers — all correct direction. Nothing imports back into intelligence at the engine level except callers (CLI, conversation, suitability).

**No deleted-module imports.** `atlas.reasoning`, `atlas.analysis.portfolio`, `atlas.analysis.comparison` — all absent ✓.

---

## `RiskAnalysis` Dependency Review

| Detail | Value |
|---|---|
| Import location | `atlas/intelligence/engine.py:28` — `from atlas.risk import RiskAnalysis` |
| Import type | **Runtime** — not TYPE_CHECKING-only. Required for dataclass field type annotations and runtime `isinstance`-style checks (`if risk_analysis is None`). |
| Fields accessed | `risk_analysis.position_sizing.liquidity_warning`, `risk_analysis.position_sizing.concentration_warning`, `risk_analysis.deployment_plan.market_regime_adjustment`, `risk_analysis.position_sizing.cash_reserve_status` |
| Where consumed | `_risk_assessment()`, `_monitoring_items()`, `_confidence()` |
| Dependency nature | Optional context — `IntelligenceContext.risk_analysis: RiskAnalysis | None = None`. Intelligence never creates `RiskAnalysis`; it is caller-supplied. |
| Intentional? | **Yes** — intentional optional enrichment. If caller supplies a `RiskAnalysis`, intelligence incorporates it into risk section and monitoring items. Otherwise, degrades gracefully with default text. |
| Should remain? | **Yes** — coupling is shallow (4 fields read), optional at call time, and provides meaningful output enrichment when supplied. |
| Output shape dependency | **MEDIUM** — depends on `.position_sizing.liquidity_warning`, `.position_sizing.concentration_warning`, `.position_sizing.cash_reserve_status`, `.deployment_plan.market_regime_adjustment`. If `RiskAnalysis` internal shape changes, intelligence rendering changes. |

---

## Stale Import Audit (repo-wide, intelligence focus)

All checked. Findings:

| Symbol | Hits in atlas/intelligence/? | Hits elsewhere (classified) |
|---|---|---|
| `atlas.reasoning` / `ReasoningEngine` from `atlas.reasoning` | **None** ✓ | Test guardrails, docs, `atlas/domains/decision/` (distinct Blueprint class), deprecations metadata |
| `check_reasoning_report` / `check_intelligence_report` / `check_suitability_assessment` | **None** ✓ | Test guardrails only |
| `atlas.analysis.portfolio` / `PortfolioAnalysis` / `PortfolioSignal` etc. | **None** ✓ | Test guardrails, docs, `atlas/capabilities/portfolio_intelligence/models.py` doc comments |
| `PortfolioIntelligenceEngine` | **None** ✓ | Test guardrails asserting absence |
| `portfolio_fit_input_from_profile` | **None** ✓ | Test guardrails asserting absence |
| `render_comparison_result` | **None** ✓ | Test guardrails asserting absence |
| `YahooCompany` / `YahooFinancials` / `YahooMarketData` | **None** ✓ | Historical docs only |

**No stale production imports in `atlas/intelligence/`.**

**Stale string corrected:** `atlas/cli/deprecations.py` `removal_criteria` for `atlas risk size` previously mentioned `atlas/reasoning engines` as a `RiskAnalysis` caller. Corrected to `atlas/conversation and atlas/intelligence engines (atlas/reasoning deleted Sprint 153)`. This is documentation/metadata only — no runtime impact.

---

## Blueprint Overlap Review

| Target | Overlap with `atlas/intelligence/`? |
|---|---|
| `atlas/domains/` | No `atlas/domains/intelligence/` exists. `atlas/domains/decision/` provides `ReasoningEngine` (Blueprint class, unrelated to deleted `atlas.reasoning`). |
| `atlas/capabilities/daily_brief/` | Conceptual adjacency — daily brief synthesizes multiple engine outputs. But different scope: `daily_brief` targets a daily overview; `intelligence` targets a single-ticker deep synthesis. Not a successor. |
| `atlas/capabilities/company_analysis/` | Company analysis is a source layer; intelligence consumes it via `AtlasInvestmentEngine`. Correct dependency direction. |
| `atlas/capabilities/portfolio_intelligence/` | Consumed as a dependency by intelligence (Blueprint-aligned, correct direction). |
| `atlas/capabilities/watchlist_intelligence/` | Consumed as a dependency by intelligence (Blueprint-aligned, correct direction). |
| `atlas/decision/` | Consumed as a dependency. `AtlasDecisionEngine` is called from `IntelligenceEngine.analyze()`. Correct direction. |
| `atlas/conversation/` | Conversation calls `IntelligenceEngine`. Intelligence is a dependency of conversation. Correct direction. |
| `atlas/dashboard/` | Dashboard is a parallel consumer alongside intelligence, not a successor. |

**Conclusion:** No Blueprint-aligned successor exists for `atlas/intelligence/`. The orchestration role is unique: it synthesizes investment, decision, portfolio fit, watchlist, market, theme, and optional risk analysis into a single `IntelligenceReport`. Migration would require a new Blueprint-aligned intelligence capability and consumer refactoring. Not warranted in Sprint 165.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Sprint 165? |
|---|---|---|---|---|
| All 5 exports | All active — CLI, conversation, suitability | Active | N/A | Leave unchanged |
| All 13 private helpers | All called by `analyze()` or `render_intelligence_report()` | Active | N/A | Leave unchanged |
| `RiskAnalysis` runtime import | Intentional optional enrichment — 4 field reads, graceful degradation | 3 internal call sites | N/A | Leave unchanged |
| Stale risk-size deprecation string | **Corrected in Sprint 164** — metadata-only, retired command record | N/A | None | Done ✓ |

**Overall assessment:** The intelligence package is clean. No dead code, no stale exports, no closed-track residue, no Blueprint migration pressure, no zero-caller symbols. The engine is an active orchestration hub. The `RiskAnalysis` dependency is intentional, shallow, and optional. All 5 exports are active.

---

## Final Stable Package State (Sprint 164)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 15 | 5 exports — all intentional |
| `engine.py` | 469 | Active — `IntelligenceEngine` orchestration hub |

**Provider safety:** Network access is opt-in only (`--provider yahoo`). Provider is passed in, never created internally by `IntelligenceEngine`. ✓

**No changes to `atlas/intelligence/` made in Sprint 164.** One deprecation metadata string corrected in `atlas/cli/deprecations.py` (non-runtime).

---

## Recommended Sprint 165 Target

**Close the intelligence cleanup track.**

After inventory (Sprint 164), the intelligence package contains no actionable cleanup candidates:
- All 5 exports are active
- All 13 private helpers are active
- No dead code or stale exports
- No closed-track import residue
- No Blueprint successor exists
- Provider boundary is clean and opt-in
- CLI is active and unchanged
- `RiskAnalysis` dependency is intentional and shallow

Sprint 165 should be a documentation-only sprint confirming the audit findings and closing the intelligence cleanup track. No code changes are needed. Pattern matches Sprint 150, 155, 158, 160, and 162.

**Reopening condition:** If a Blueprint-aligned intelligence capability emerges in `atlas/capabilities/`, if the CLI command is deprecated, or if new dead code or stale imports appear.

# Atlas Dashboard Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 168)  
**Status:** ACTIVE — audit-first sprint. No cleanup action taken. Sprint 169 recommended: close the dashboard cleanup track (documentation-only, no code changes warranted).

---

## Background

`atlas/dashboard/` is a self-contained application-facing aggregation layer that synthesizes investor profile, portfolio, market, economics, themes, suitability, risk drift, monitoring, and principles outputs into a deterministic `DashboardSummary`. It is active, well-bounded, and has one active CLI command (`atlas dashboard show`). It has no deleted-module imports. Sprint 168 is the audit-first sprint following the conversation track closure (Sprint 167).

---

## `atlas/dashboard/` Package Inventory (Sprint 168 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 17 | Re-export hub — 6 exports |
| `engine.py` | 516 | Core engine + dataclasses + renderer + private helpers |

---

## `engine.py` — Public API

| Symbol | Kind | Active production callers | Test callers | Status |
|---|---|---|---|---|
| `DashboardCard` | frozen dataclass | Via `DashboardSection.cards` | `test_dashboard_engine.py` | **Active — output sub-type** |
| `DashboardSection` | frozen dataclass | Via `DashboardSummary.sections` | `test_dashboard_engine.py` | **Active — output sub-type** |
| `DashboardInput` | frozen dataclass | CLI (`dashboard_show_command`) | `test_dashboard_engine.py` | **Active** |
| `DashboardSummary` | frozen dataclass | CLI (returned by `.build()`) | `test_dashboard_engine.py` | **Active — main output type** |
| `DashboardEngine` | class | CLI | `test_dashboard_engine.py` | **Active — core aggregation engine** |
| `render_dashboard` | function | CLI | `test_dashboard_engine.py` | **Active — CLI output** |

### `engine.py` — Private Helpers

All private helpers are internal and active.

| Symbol | Purpose | Callers |
|---|---|---|
| `_portfolio_section` | Builds portfolio `DashboardSection` (with or without portfolio) | `build()` |
| `_dashboard_text_without_principles` | Renders full dashboard text (used by `render_dashboard` and for principles pre-check) | `build()`, `render_dashboard()` |
| `_welcome_section` | Builds profile welcome `DashboardSection` | `build()` |
| `_market_section` | Builds market regime/health/economics `DashboardSection` | `build()` |
| `_themes_section` | Builds themes `DashboardSection` | `build()` |
| `_observations` | Builds `todays_observations` tuple | `build()` |
| `_monitoring_items` | Builds `monitoring_items` tuple | `build()` |
| `_suggested_questions` | Builds `suggested_questions` tuple | `build()` |
| `_default_market_snapshot` | Returns deterministic placeholder `MarketSnapshot` | `build()` |
| `_greeting` | Builds greeting string | `build()`, `_dashboard_text_without_principles` |
| `_theme_detail` | Formats theme bottleneck string | `_themes_section` |
| `_score_status` | Maps score → status string | `_portfolio_section` |
| `_concentration_level` | Maps weight → concentration label | `_portfolio_section` |
| `_concentration_status` | Maps weight → status string | `_portfolio_section` |
| `_first_or_default` | Returns first item or default | `_portfolio_section` |
| `_find_card` | Finds a `DashboardCard` by title in a `DashboardSection` | `_observations` |
| `_render_list` | Formats `tuple[str, ...]` as bullet lines | `_dashboard_text_without_principles` |

**Zero zero-caller private helpers found.**

---

## `DashboardEngine` Review

| Detail | Value |
|---|---|
| Source file | `atlas/dashboard/engine.py:69` |
| Public methods | `.build(DashboardInput | None) → DashboardSummary` |
| Constructor dependencies | 10 optional engine parameters (all default `None` → instantiate defaults) |
| Provider dependency | `DashboardInput.provider: CompanyDataProvider | None` — type annotation only; passed through to `PortfolioIntelligenceCapability.analyze()` only when `target_ticker` and `provider` are both supplied |
| Network calls? | No direct network calls. Provider is caller-supplied. Network is CLI opt-in via `--provider yahoo`. |
| Production callers | CLI (`dashboard_show_command`) |
| Test callers | `tests/test_dashboard_engine.py` |
| CLI callers | `atlas dashboard show [--profile] [--portfolio] [--provider] [--ticker]` |
| Returns Blueprint-aligned data? | No — returns `DashboardSummary` (legacy type). Consumes Blueprint-aligned types: `PortfolioFitResult` (via `PortfolioIntelligenceCapability`). |
| Zero-caller public methods | None — `.build()` is the only public method and is active. |
| Stale compatibility logic | None found. |

**Notable design pattern:** Dashboard calls `_dashboard_text_without_principles()` twice — once before the `PrinciplesEngine.check()` call (for principles pre-check), and once inside `render_dashboard()` for output. This is intentional: the principles check inspects the rendered draft text, then the final rendered output is generated via `render_dashboard()` at CLI time.

---

## Export Review (`__init__.py`)

6 exports. All active.

| Export | Active? | Direct external callers |
|---|---|---|
| `DashboardCard` | ✓ (sub-type) | Tests; accessed via `.sections[*].cards` in production |
| `DashboardEngine` | ✓ | CLI, tests |
| `DashboardInput` | ✓ | CLI, tests |
| `DashboardSection` | ✓ (sub-type) | Tests; accessed via `.sections` in production |
| `DashboardSummary` | ✓ | CLI (returned type), tests |
| `render_dashboard` | ✓ | CLI, tests |

**Finding:** All 6 exports are active. `DashboardCard` and `DashboardSection` have zero direct external production callers but are correct sub-types of `DashboardSummary`. Not cleanup candidates.

---

## Production Caller Map

**1 production caller: CLI only.**

| Caller | Import | Symbols used |
|---|---|---|
| `atlas/cli/main.py:dashboard_show_command` | `from atlas.dashboard import DashboardEngine, DashboardInput, render_dashboard` | 3 of 6 |

Dashboard is **not** imported by any other Atlas package at runtime. It is a terminal application layer: nothing depends on it. This is correct — dashboard is an output aggregator, not a shared dependency.

---

## CLI / Entrypoint Review

### `atlas dashboard show`

| Detail | Value |
|---|---|
| Command | `atlas dashboard show [--profile path] [--portfolio path] [--provider mock\|yahoo] [--ticker TICKER]` |
| Implementation | `atlas/cli/main.py:370–406` |
| Imports used | `DashboardEngine`, `DashboardInput`, `render_dashboard` |
| Provider selection | `_provider_from_name(provider_name)` — `"mock"` → `MockCompanyAnalysisProvider()`, `"yahoo"` → `YahooFinanceProvider()`. Default: `"mock"`. |
| Runtime behavior | Loads profile, optionally loads portfolio, instantiates `DashboardEngine()`, builds `DashboardInput`, calls `.build()`, renders via `render_dashboard()` |
| CLI behavior | Active and unchanged |

---

## Dependency Boundary Review

| Dependency | Import location | Classification | Direction acceptable? | Stable? |
|---|---|---|---|---|
| `atlas.adapters.portfolio` | `legacy_portfolio_to_domain_portfolio` (runtime), `Portfolio` (TYPE_CHECKING) | Adapter conversion | ✓ | ✓ |
| `atlas.capabilities.portfolio_intelligence` | `PortfolioIntelligenceCapability` (runtime) | Blueprint-aligned capability | ✓ correct direction | ✓ |
| `atlas.economics` | `EconomicSignalAnalysis`, `EconomicSignalsEngine` (runtime) | Economics engine dependency | ✓ | ✓ |
| `atlas.market` | 6 types (runtime) | Market data types | ✓ | ✓ |
| `atlas.monitoring` | `MonitoringEngine` (runtime) | Monitoring dependency | ✓ | ✓ |
| `atlas.principles` | `PrinciplesCheck`, `PrinciplesEngine` (runtime) | Principles pre-check on draft text | ✓ | ✓ — principles track CLOSED Sprint 158, engine active |
| `atlas.profile` | `InvestorProfile`, `InvestorProfileEngine` (runtime) | Profile dependency | ✓ | ✓ |
| `atlas.providers` | `CompanyDataProvider` (runtime type annotation in `DashboardInput.provider`) | Abstract type annotation only — no `MockCompanyAnalysisProvider` import | ✓ | ✓ |
| `atlas.risk_drift` | `RiskDriftEngine`, `RiskDriftInput` (runtime) | Risk drift dependency | ✓ | ✓ |
| `atlas.suitability` | `SuitabilityEngine`, `SuitabilityInput` (runtime) | Suitability dependency | ✓ | ✓ |
| `atlas.themes` | `ThemeAnalysis`, `ThemeEngine`, `ThemeInput` (runtime) | Theme engine dependency | ✓ | ✓ |

**No circular dependencies.** Nothing imports from `atlas/dashboard/` except CLI. ✓

**No deleted-module imports.** `atlas.reasoning`, `atlas.analysis.portfolio`, `atlas.analysis.comparison` — all absent. ✓

**Notable:** Dashboard does **not** import `atlas.intelligence` or `atlas.conversation`. It orchestrates independently at the application layer, consuming lower-level engines directly.

**Provider coupling note:** Unlike `atlas/comparison/` and `atlas/home/`, dashboard does NOT import `MockCompanyAnalysisProvider`. `CompanyDataProvider` is used only as a type annotation in `DashboardInput.provider`. The provider is passed in from the CLI. This is a clean, intentional design — provider selection lives entirely at the CLI layer.

---

## Provider Boundary Review

| Check | Result |
|---|---|
| `YahooFinanceProvider` in `atlas/dashboard/` | **Absent** ✓ |
| `MockCompanyAnalysisProvider` in `atlas/dashboard/` | **Absent** ✓ |
| `CompanyDataProvider` in `atlas/dashboard/` | Present — type annotation only in `DashboardInput.provider` field |
| Direct network calls | **None** ✓ |
| Provider usage | CLI-supplied; passed through to `PortfolioIntelligenceCapability.analyze()` only when `target_ticker` is also provided |
| Network behavior | Opt-in only via `--provider yahoo` in CLI |

Dashboard has the **cleanest provider boundary** of any provider-aware package audited so far — it neither imports nor instantiates any concrete provider.

---

## Stale Import Audit (repo-wide, dashboard focus)

All checked. All hits in `atlas/dashboard/` classified:

| Symbol | In `atlas/dashboard/`? | Elsewhere (classified) |
|---|---|---|
| `atlas.reasoning` / deleted reasoning symbols | **None** ✓ | Test guardrails, docs, `atlas/domains/decision/` Blueprint class |
| `PortfolioIntelligenceEngine` | **None** ✓ | Test guardrails asserting absence |
| `portfolio_fit_input_from_profile` | **None** ✓ | Test guardrails asserting absence |
| `PortfolioAnalysis` / `PortfolioSignal` etc. | **None** ✓ | Test guardrails, capability models doc comments |
| `render_comparison_result` | **None** ✓ | Test guardrails asserting absence |
| `YahooCompany` / `YahooFinancials` / `YahooMarketData` | **None** ✓ | Historical docs only |
| `check_intelligence_report` / `check_suitability_assessment` | **None** ✓ | Test guardrails asserting absence |

**No stale production imports in `atlas/dashboard/`.**

---

## Blueprint Overlap Review

| Target | Overlap with `atlas/dashboard/`? |
|---|---|
| `atlas/domains/` | No `atlas/domains/dashboard/` exists. |
| `atlas/capabilities/daily_brief/` | Conceptual adjacency — `daily_brief` capability produces a multi-engine briefing. Dashboard also produces a multi-engine briefing. However: `daily_brief` is intelligence-report-focused; `dashboard` is profile/portfolio/principles-first. Different scope. Not a successor. |
| `atlas/capabilities/portfolio_intelligence/` | Consumed as a dependency (Blueprint-aligned, correct direction). |
| `atlas/intelligence/` | Not imported by dashboard. Intelligence is a sibling orchestration layer, not a parent. |
| `atlas/conversation/` | Not imported by dashboard. Parallel application layers. |
| `atlas/home/` | Conceptual adjacency — `atlas/home/` also produces a personalized investor briefing. Sprint 162 confirmed home and dashboard are distinct (home focuses on portfolio alignment + decision journal; dashboard focuses on profile + suitability + risk drift + principles). Not redundant. |

**Conclusion:** No Blueprint-aligned successor exists for `atlas/dashboard/`. Dashboard's aggregation role (profile × portfolio × market × economics × themes × suitability × risk drift × monitoring × principles) is unique. No migration warranted.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Sprint 169? |
|---|---|---|---|---|
| All 6 exports | All active — CLI, tests, or correct sub-types | Active | N/A | Leave unchanged |
| All 17 private helpers | All called by `build()` or renderer | Active | N/A | Leave unchanged |
| `CompanyDataProvider` type annotation | Correct — abstract type only, no concrete provider import | Active | N/A | Leave unchanged |
| `_dashboard_text_without_principles` | Called twice (principles pre-check + render) — intentional pattern | Active | N/A | Leave unchanged |
| `DashboardCard`, `DashboardSection` | Zero direct external production callers — correct sub-types of `DashboardSummary` | 0 direct | LOW | Leave unchanged |

**Overall assessment:** The dashboard package is clean. No dead code, no stale exports, no closed-track residue, no Blueprint migration pressure, no zero-caller symbols, no provider boundary issues. Dashboard has the cleanest provider boundary of any audited package. All 6 exports are intentional.

---

## Final Stable Package State (Sprint 168)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 17 | 6 exports — all intentional |
| `engine.py` | 516 | Active — `DashboardEngine` application aggregation hub with clean boundaries |

**Provider safety:** Network access is opt-in only (`--provider yahoo`). Dashboard does not import any concrete provider class. Provider is passed in from CLI. `YahooFinanceProvider` and `MockCompanyAnalysisProvider` are both absent from `atlas/dashboard/`. ✓

---

## Recommended Sprint 169 Target

**Close the dashboard cleanup track.**

After inventory (Sprint 168), the dashboard package contains no actionable cleanup candidates:
- All 6 exports are active or intentional sub-types
- All 17 private helpers are active
- No dead code or stale exports
- No closed-track import residue
- No Blueprint successor exists
- Cleanest provider boundary audited so far — no concrete provider imported
- CLI is active and unchanged

Sprint 169 should be a documentation-only sprint confirming the audit findings and closing the dashboard cleanup track. No code changes are needed. Pattern matches Sprint 150, 155, 158, 160, 162, 165, and 167.

**Reopening condition:** If a Blueprint-aligned dashboard capability emerges in `atlas/capabilities/`, if the CLI command is deprecated, or if new dead code or stale imports appear.

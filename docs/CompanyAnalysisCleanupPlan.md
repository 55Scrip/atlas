# Atlas Company Analysis Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 179)
**Status:** AUDIT COMPLETE — one stale alias found (`CompanyAnalysisProvider`). Sprint 180 recommended: close `atlas/analysis/` cleanup track and remove the stale alias.

---

## Package Disambiguation

`atlas/company_analysis/` **does not exist** as a standalone top-level package.

The company analysis runtime surface is split across two distinct layers:

| Layer | Path | Purpose |
|---|---|---|
| Legacy scoring/investment-report layer | `atlas/analysis/` | Placeholder-based scoring, `AtlasInvestmentEngine`, `InvestmentReport`, `CompanyAnalysis` |
| Blueprint capability layer | `atlas/capabilities/company_analysis/` | Deterministic, non-advisory structured analysis using domain types |

Sprint 141 closed the `atlas/analysis/` cleanup track, deleting 12+ submodules. Five modules remain. This audit inventories those 5 modules and compares them against the Blueprint capability layer.

---

## `atlas/analysis/` — Inventory (5 Active Modules)

### Module Summary Table

| Module | Lines | Public Symbols | Role | Active? |
|---|---|---|---|---|
| `company_analysis.py` | 162 | `CompanyAnalysis`, `create_placeholder_company_analysis`, 7 `*Analysis` dataclasses, `CompanyAnalysisProvider` (alias) | Placeholder analysis types + provider alias | Yes (7 active + 1 stale alias) |
| `engine.py` | 229 | `AtlasInvestmentEngine`, `InvestmentReport`, `ScoreCategory`, `ThresholdRecommendationPolicy`, 5 `*Scorer` classes, `DEFAULT_*` constants | Investment scoring engine | Yes |
| `explanation.py` | 198 | `InvestmentExplanation`, `explain_investment_report`, `render_investment_explanation` | Qualitative explanation of `InvestmentReport` | Yes |
| `report.py` | 38 | `build_investment_report`, `render_investment_report` | Convenience orchestrator + text renderer | Yes |
| `scores.py` | 2 | `clamp_score` | Active utility: clamp int to [0, 100] | Yes |
| `__init__.py` | 26 | 12 re-exported symbols | Package re-export surface | Yes |

**Total: ~655 lines**

---

### `atlas/analysis/company_analysis.py` (162 lines)

**Public symbols (active):**
- `CompanyAnalysis` (frozen dataclass) — aggregate of 7 dimension dataclasses
- `GrowthAnalysis`, `MacroAnalysis`, `MoatAnalysis`, `QualityAnalysis`, `SentimentAnalysis`, `TechnicalAnalysis`, `ValuationAnalysis` — frozen dataclasses, each with `score`, `summary`, `strengths`, `weaknesses`
- `create_placeholder_company_analysis(company: str) → CompanyAnalysis` — factory used by providers
- 7 `placeholder_*_analysis()` factories — internal helpers used only by `create_placeholder_company_analysis`

**⚠️ Stale symbol — `CompanyAnalysisProvider` (line 154):**
```python
from atlas.providers.base import CompanyDataProvider as CompanyAnalysisProvider  # noqa: E402
```
This alias is defined at module level but:
- Has **zero external callers** in the entire codebase
- Is **not in `atlas.analysis.__all__`** — not re-exported
- Is defined only as a compatibility shim with no remaining consumer
- Sprint 141 cleanup did not remove it

This is the only cleanup candidate found in the entire legacy analysis surface.

**`__getattr__` lazy-import:**
```python
def __getattr__(name: str):
    if name == "MockCompanyAnalysisProvider":
        from atlas.providers.mock import MockCompanyAnalysisProvider
        return MockCompanyAnalysisProvider
    raise AttributeError(...)
```
This allows `from atlas.analysis.company_analysis import MockCompanyAnalysisProvider` to work via lazy import. Active — used by `test_investment_engine.py`, `test_explanation.py`, `test_memory.py`, `test_scoring.py`.

**Provider coupling:** `company_analysis.py` imports `CompanyDataProvider` from `atlas.providers.base` for the stale alias. The `__getattr__` also lazy-imports from `atlas.providers.mock`. This is the provider boundary — intentional for the legacy provider protocol.

**Production callers:**
- `atlas/analysis/engine.py` — `CompanyAnalysis` (type parameter)
- `atlas/analysis/report.py` — `CompanyAnalysis`
- `atlas/analysis/__init__.py` — re-exports `CompanyAnalysis`, `create_placeholder_company_analysis`
- `atlas/providers/mock.py` — `CompanyAnalysis`, `create_placeholder_company_analysis`
- `atlas/providers/yahoo.py` — `CompanyAnalysis`, `create_placeholder_company_analysis`
- `atlas/providers/base.py` — `CompanyAnalysis` (Protocol return type, TYPE_CHECKING guard)

---

### `atlas/analysis/engine.py` (229 lines)

**Public symbols:** `AtlasInvestmentEngine`, `InvestmentReport`, `ScoreCategory`, `ThresholdRecommendationPolicy`, `CategoryScorer` (Protocol), `RecommendationPolicy` (Protocol), `QualityScorer`, `GrowthScorer`, `ValuationScorer`, `FinancialStrengthScorer`, `RiskScorer`, `iter_score_categories`, `DEFAULT_CATEGORY_WEIGHTS`, `DEFAULT_CATEGORY_SCORERS`

**Re-exported via `atlas.analysis.__all__`:** `AtlasInvestmentEngine`, `InvestmentReport`, `ScoreCategory`

**⚠️ Note — recommendation language:**
`ThresholdRecommendationPolicy.recommend()` returns `"Strong Buy"`, `"Buy"`, `"Hold"`, `"Sell"`, `"Strong Sell"`. This is legacy code predating the no-recommendation-language constraint. It is not new code, and the sprint spec does not require removing it. It is confined to the legacy scoring layer and is not emitted by the Blueprint capability layer.

**Production callers:**
- `atlas/cli/main.py` — `build_investment_report`, `render_investment_report` (via `atlas.analysis.report`)
- `atlas/comparison/engine.py` — `build_investment_report`
- `atlas/conversation/engine.py` — `AtlasInvestmentEngine`
- `atlas/decision/comparison.py` — `AtlasInvestmentEngine`, `InvestmentReport`
- `atlas/decision/decision_engine.py` — `AtlasInvestmentEngine`, `InvestmentReport`
- `atlas/decision/memory.py` — `AtlasInvestmentEngine`, `InvestmentReport`, `iter_score_categories`
- `atlas/decision/decision_result.py` — `InvestmentReport`
- `atlas/intelligence/engine.py` — `AtlasInvestmentEngine`, `InvestmentReport`
- `atlas/monitoring/engine.py` — `AtlasInvestmentEngine`
- `atlas/suitability/engine.py` — `InvestmentReport`
- `atlas/models/investment_report.py` — `InvestmentReport`, `ScoreCategory` (thin re-export)
- `atlas/analysis/report.py` — `AtlasInvestmentEngine`, `InvestmentReport`, `iter_score_categories`
- `atlas/analysis/explanation.py` — `InvestmentReport`, `ScoreCategory`, `iter_score_categories`

**Test callers:** `test_investment_engine.py`, `test_scoring.py`, `test_providers.py`, `test_suitability_engine.py`, `test_watchlist_analyze_deprecation.py`

**Classification:** Active, foundational, runtime-facing. `AtlasInvestmentEngine` is the widest-used legacy analysis symbol (11+ production callers).

---

### `atlas/analysis/explanation.py` (198 lines)

**Public symbols:** `InvestmentExplanation`, `explain_investment_report`, `render_investment_explanation`

**Production callers:**
- `atlas/analysis/report.py` — `explain_investment_report`, `render_investment_explanation`
- `atlas/decision/memory.py` — `explain_investment_report`
- `atlas/analysis/__init__.py` — re-exports `InvestmentExplanation`, `explain_investment_report`

**Test callers:** `test_explanation.py`, `test_watchlist_analyze_deprecation.py`

**Classification:** Active, runtime-facing.

---

### `atlas/analysis/report.py` (38 lines)

**Public symbols:** `build_investment_report`, `render_investment_report`

**Production callers:**
- `atlas/cli/main.py` — `build_investment_report`, `render_investment_report` (used by `report` and `analyze` CLI commands)
- `atlas/comparison/engine.py` — `build_investment_report`
- `atlas/analysis/__init__.py` — re-exports both

**Test callers:** `test_explanation.py`, `test_memory.py`, `test_scoring.py`, `test_watchlist_analyze_deprecation.py`

**Classification:** Active, runtime-facing, CLI-facing.

---

### `atlas/analysis/scores.py` (2 lines)

**Public symbols:** `clamp_score(score: int) → int`

**Callers:** 12+ production modules including `atlas/adapters/portfolio.py`, `atlas/analysis/engine.py`, `atlas/comparison/engine.py`, `atlas/decision/decision_engine.py`, `atlas/economics/engine.py`, `atlas/market/health.py`, `atlas/market/regime.py`, `atlas/monitoring/engine.py`, `atlas/risk/engine.py`, `atlas/risk_drift/engine.py`, `atlas/suitability/engine.py`

**Classification:** Active utility. Intentionally retained as of Sprint 140.

---

### `atlas/analysis/__init__.py` (26 lines)

**Exports (12 symbols):**
```
AtlasInvestmentEngine, CompanyAnalysis, CompanyDataProvider, InvestmentExplanation,
InvestmentReport, MockCompanyAnalysisProvider, ScoreCategory, YahooFinanceProvider,
build_investment_report, create_placeholder_company_analysis, explain_investment_report,
render_investment_report
```

All 12 exports are active and have external callers. No stale exports in `__all__`.

Note: `CompanyAnalysisProvider` is **not** in `__all__` — the stale alias is correctly excluded from the export surface.

---

## CLI Caller Review

### Commands Using Legacy `atlas/analysis/` Layer

| CLI Command | Symbols Used | Source |
|---|---|---|
| `atlas report <ticker>` | `build_investment_report`, `render_investment_report` | `atlas.analysis.report` |
| `atlas analyze <ticker>` | `build_investment_report`, `render_investment_report` | `atlas.analysis.report` |
| `atlas memory save/compare` | `AtlasInvestmentEngine`, `build_investment_report` | via `atlas.decision.memory` |

### Commands Using Blueprint Capability Layer

| CLI Command | Symbols Used | Source |
|---|---|---|
| `atlas company-analysis export` | `CompanyAnalysisEngine`, `CompanyAnalysisInput` | `atlas.capabilities.company_analysis` |
| `atlas company-analysis merge` | `parse_company_analysis_json` | `atlas.capabilities.daily_brief.json_loader` |
| `atlas daily summary --company-analysis` | `parse_company_analysis_json` | `atlas.capabilities.daily_brief.json_loader` |

The two CLI surfaces are served by two separate layers. No CLI command imports from both layers simultaneously for the same operation. The `report` and `analyze` commands use the legacy scoring layer; the `company-analysis` group commands use the Blueprint capability layer.

**Provider behavior:** All `atlas analyze` / `atlas report` commands use `--provider` flag (default: `mock`). Yahoo is opt-in only. No new provider behavior was introduced.

---

## Caller Map Summary

| Symbol | Production Callers | Test Callers | Classification |
|---|---|---|---|
| `CompanyAnalysis` | providers (×3), engine.py, report.py, __init__.py | `test_company_analysis.py`, `test_provider_package_sprint145.py` | Active |
| `create_placeholder_company_analysis` | providers/mock.py, providers/yahoo.py, __init__.py | — | Active |
| `AtlasInvestmentEngine` | conversation, decision (×2), intelligence, monitoring, CLI, __init__.py | `test_investment_engine.py`, `test_providers.py` | Active |
| `InvestmentReport` | decision (×3), suitability, CLI, comparison, report.py, models, __init__.py | `test_suitability_engine.py` | Active |
| `ScoreCategory` | explanation.py, models, __init__.py | `test_suitability_engine.py` | Active |
| `build_investment_report` | CLI, comparison, report.py | `test_explanation.py`, `test_memory.py`, `test_scoring.py` | Active |
| `render_investment_report` | CLI | `test_watchlist_analyze_deprecation.py` | Active |
| `InvestmentExplanation` | __init__.py | `test_explanation.py` | Active |
| `explain_investment_report` | decision/memory, report.py, __init__.py | `test_explanation.py`, `test_watchlist_analyze_deprecation.py` | Active |
| `clamp_score` | 12+ modules | `test_adapters_package_sprint178.py`, `test_analysis_package_sprint140.py` | Active |
| `CompanyAnalysisProvider` | **zero external callers** | — | **STALE ALIAS** |
| `MockCompanyAnalysisProvider` (via `__getattr__`) | __init__.py | `test_investment_engine.py`, `test_explanation.py`, `test_memory.py`, `test_scoring.py` | Active (lazy import) |

---

## Capability Boundary Review

### `atlas/capabilities/company_analysis/` (4 files, 571 lines)

| Module | Lines | Role |
|---|---|---|
| `__init__.py` | 25 | Exports 9 Blueprint symbols |
| `models.py` | 88 | `CompanyAnalysisReport`, `CompanyAnalysisInput`, `CompanyAnalysisSection`, etc. |
| `engine.py` | 387 | `CompanyAnalysisEngine` — deterministic, non-advisory |
| `exporter.py` | 71 | `company_report_to_dict`, `company_reports_to_list` |

**Capability exports (9):** `CompanyAnalysisConfidence`, `CompanyAnalysisEngine`, `CompanyAnalysisEvidenceLink`, `CompanyAnalysisInput`, `CompanyAnalysisObservation`, `CompanyAnalysisReport`, `CompanyAnalysisRisk`, `CompanyAnalysisSection`, `CompanyAnalysisUnknown`

**Dependency direction:**
- `atlas/capabilities/company_analysis/` → `atlas.domains.decision` (Evidence), `atlas.domains.knowledge` (KnowledgeFact), `atlas.domains.research` (ResearchProject), `atlas.shared` (Company)
- `atlas/capabilities/company_analysis/` → **does NOT import from `atlas/analysis/`** ✓

The capability layer is completely decoupled from the legacy scoring layer. No import from `atlas.analysis` in any capability module. The boundary is clean and correct.

### Layer Comparison

| Dimension | `atlas/analysis/` (legacy) | `atlas/capabilities/company_analysis/` (Blueprint) |
|---|---|---|
| **Type of output** | `InvestmentReport` (scored, with recommendation language) | `CompanyAnalysisReport` (structured, non-advisory, non-scored) |
| **Recommendation language** | Yes — `ThresholdRecommendationPolicy` returns "Strong Buy"/"Buy"/etc. | No — explicitly non-advisory |
| **Data source** | `CompanyAnalysis` from provider (placeholder or Yahoo) | `CompanyAnalysisInput` built from domain types |
| **Provider coupling** | Injected provider (`CompanyDataProvider`) | None — deterministic, provider-free |
| **Domain dependency** | None — legacy model types only | Domain types (`Evidence`, `KnowledgeFact`, `ResearchProject`) |
| **CLI surface** | `atlas report`, `atlas analyze` | `atlas company-analysis export`, `atlas daily summary` |
| **Blueprint-aligned** | Partially — active but legacy | Yes — fully Blueprint-aligned |

**No duplicate modeling.** `CompanyAnalysis` (7 placeholder dimension scores) and `CompanyAnalysisReport` (structured sections + evidence links) are different types for different purposes. No migration warrants overlap removal.

---

## Provider Boundary Review

| Check | Finding |
|---|---|
| `atlas/analysis/` imports `atlas.providers.base` | ✓ — `CompanyDataProvider` Protocol only (`TYPE_CHECKING` in `base.py`) |
| `atlas/analysis/company_analysis.py` imports provider for stale alias | `from atlas.providers.base import CompanyDataProvider as CompanyAnalysisProvider` — stale, zero callers |
| `atlas/analysis/company_analysis.py` lazy-imports mock provider via `__getattr__` | Intentional — provider is not imported at module load time |
| Providers import from `atlas.analysis` | ✓ — `atlas/providers/mock.py` and `atlas/providers/yahoo.py` import `CompanyAnalysis` and `create_placeholder_company_analysis` |
| Network access in `atlas/analysis/` | No — all modules are deterministic, no network calls |
| Yahoo provider remains opt-in | ✓ — only activated via `--provider yahoo` CLI flag |
| No new provider behavior introduced | ✓ — audit-only sprint |

---

## Stale Import Audit

No stale active production imports found in `atlas/analysis/`.

| Symbol | Location | Classification |
|---|---|---|
| `atlas.analysis.portfolio` | `atlas/cli/deprecations.py:129` | Docs/retirement note — not an import |
| `atlas.analysis.portfolio` | `atlas/adapters/portfolio.py:57` | Historical docstring — not an import |
| `atlas.analysis.portfolio` | many test files | Migration guardrail tests — confirming deletion |
| `atlas.analysis.watchlist` | `atlas/cli/deprecations.py:162` | Retirement metadata — not an import |
| `atlas.analysis.comparison/memory/scoring` | test files | Deletion guardrail tests |
| `CompanyAnalysisProvider` | `atlas/analysis/company_analysis.py:154` | **Stale module-level alias — no external callers** |
| `atlas.reasoning` | — | Not imported anywhere in `atlas/analysis/` ✓ |

---

## Export Review

`atlas/analysis/__init__.py` exports 12 symbols — all active, all with external callers:

| Export | Active callers | Notes |
|---|---|---|
| `AtlasInvestmentEngine` | 8+ production modules | ✓ |
| `CompanyAnalysis` | providers, engine, report | ✓ |
| `CompanyDataProvider` | re-export from providers | ✓ |
| `InvestmentExplanation` | decision/memory | ✓ |
| `InvestmentReport` | 8+ production modules | ✓ |
| `MockCompanyAnalysisProvider` | via `__getattr__` + test callers | ✓ |
| `ScoreCategory` | explanation, models, suitability | ✓ |
| `YahooFinanceProvider` | re-export | ✓ (opt-in) |
| `build_investment_report` | CLI, comparison | ✓ |
| `create_placeholder_company_analysis` | providers | ✓ |
| `explain_investment_report` | decision, report | ✓ |
| `render_investment_report` | CLI | ✓ |

No stale exports. `CompanyAnalysisProvider` (stale alias) correctly excluded from `__all__`.

---

## Blueprint / Capability Model Review

`atlas/analysis/` is **legacy but active** — not Blueprint-aligned in its data model, but correctly decoupled from the Blueprint layer. The capability layer supersedes it for new features but does not replace it at the CLI `report`/`analyze` commands.

| Question | Finding |
|---|---|
| `atlas/analysis/` is Blueprint-aligned? | No — uses placeholder scoring; predates Blueprint |
| `atlas/analysis/` overlaps with capability? | No — different output types, different CLI surfaces |
| Capability wraps or duplicates legacy? | No — `CompanyAnalysisReport` is structurally different from `InvestmentReport` |
| Provider coupling belongs in analysis? | Partially — `CompanyAnalysisProvider` alias is stale; provider injection via `AtlasInvestmentEngine.analyze_ticker()` is intentional |
| Any migration warranted now? | No — runtime behavior must not change |

---

## Cleanup Candidate Classification

| Candidate | Evidence | Risk | Sprint 180? |
|---|---|---|---|
| `CompanyAnalysisProvider` alias in `atlas/analysis/company_analysis.py:154` | Module-level import, zero external callers, not in `__all__`, no other file references it | **LOW** — removing the alias line and the unused name from `company_analysis.py` has no effect on any caller | ✓ Yes — targeted single-line removal |

No other cleanup candidates found:
- All 12 `__all__` exports are active
- All 5 modules have production callers
- No deleted modules are imported
- `ThresholdRecommendationPolicy` recommendation language is pre-existing legacy code, not a new addition — not a cleanup target in this sprint
- `CompanyAnalysis` placeholder model is actively used by providers; no migration warranted

---

## Technical Debt Summary

`atlas/analysis/` has minimal technical debt:

- 5 modules, 655 lines
- 12 `__all__` exports — all active
- **1 stale alias** (`CompanyAnalysisProvider`) — zero callers, not exported
- Legacy recommendation language (`ThresholdRecommendationPolicy`) is pre-existing, confined to this layer, not emitted by Blueprint capability
- Clean boundary with `atlas/capabilities/company_analysis/` — capability does not import legacy analysis
- Sprint 141 closure verified — 12 deleted modules remain absent
- No stale imports from deleted analysis submodules
- Provider boundary correct — no direct network access in `atlas/analysis/`

---

## Recommended Sprint 180 Target

**Close `atlas/analysis/` cleanup track** — remove the `CompanyAnalysisProvider` stale alias from `atlas/analysis/company_analysis.py` and declare the track closed.

The alias is the only cleanup candidate. Its removal requires:
1. Delete line 154: `from atlas.providers.base import CompanyDataProvider as CompanyAnalysisProvider  # noqa: E402`
2. Confirm zero callers (already verified — grep finds no external references)
3. Update `tests/test_analysis_package_sprint140.py` or add a Sprint 180 guardrail asserting the alias is absent
4. Declare `atlas/analysis/` CLOSED — confirm Sprint 141 cleanup track is complete

This is the smallest safe step with the best architectural value: removes the one stale remnant, closes a long-open track, and confirms the legacy analysis layer is stable and complete.

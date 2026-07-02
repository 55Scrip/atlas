# Atlas Risk Package Cleanup Plan

**Created:** 2026-07-02 (Sprint 154)  
**Updated:** 2026-07-02 (Sprint 155)  
**Status:** CLOSED — Sprint 155 confirmed Sprint 154 findings unchanged. No cleanup work is warranted. Package is self-contained, actively used via `RiskAnalysis`, and stable. No further `atlas/risk/` cleanup work is planned until a Blueprint-aligned successor exists or new dead code / stale imports are discovered.

---

## Background

`atlas/risk/` is a Group C self-contained module. It provides deterministic risk and position-sizing calculations. The CLI command `atlas risk size` was deprecated in Sprint 83 and the command body retired in Sprint 88. The package was kept on disk because `RiskAnalysis` is still imported by two production engines (`atlas/conversation/` and `atlas/intelligence/`).

---

## `atlas/risk/` Package Inventory (Sprint 154 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 21 | Re-export hub |
| `engine.py` | 448 | Core engine — all logic |

### `engine.py` — Public API

| Symbol | Type | Active production callers | Status |
|---|---|---|---|
| `RiskProfile` | str Enum (4 values) | Engine-internal only | **Active — internal** |
| `CurrentPosition` | frozen dataclass | Engine-internal only | **Active — internal** |
| `PositionSizingInput` | frozen dataclass w/ JSON loader | Test-only external caller | **Test-only input type** |
| `CapitalDeploymentPlan` | frozen dataclass | Via `RiskAnalysis` | **Active — sub-field of RiskAnalysis** |
| `PositionSizingResult` | frozen dataclass | Via `RiskAnalysis` | **Active — sub-field of RiskAnalysis** |
| `RiskAnalysis` | frozen dataclass | **2 production engines** | **Active — shared production type** |
| `RiskEngine` | class | **Zero production callers** | **Dormant — test-only** |
| `render_risk_analysis` | function | Test-only (`test_risk_engine.py`) | **Test-only** |

### `engine.py` — Private Helpers

All private helpers are internal to `RiskEngine.analyze()` and `render_risk_analysis()`.

| Symbol | Purpose | Status |
|---|---|---|
| `_adjusted_investable_capital` | Capital after cash reserve and horizon checks | Active — internal |
| `_maximum_position_size` | Cap from risk profile + quality multiplier | Active — internal |
| `_risk_profile_position_cap` | Maps `RiskProfile` → position cap fraction | Active — internal |
| `_quality_multiplier` | Adjusts cap by confidence/risk/company scores | Active — internal |
| `_current_target_value` | Sum of existing exposure in target ticker | Active — internal |
| `_deployment_period` | Maps `MarketRegime` → deployment months | Active — internal |
| `_initial_deployment_rate` | Maps `MarketRegime` → initial deploy fraction | Active — internal |
| `_market_regime_adjustment` | Maps `MarketRegime` → human-readable string | Active — internal |
| `_cash_reserve_status` | Reserve adequacy string | Active — internal |
| `_concentration_warning` | Concentration check string | Active — internal |
| `_liquidity_warning` | Liquidity check string | Active — internal |
| `_final_recommendation` | Top-level sizing string | Active — internal |
| `_reasoning` | Builds 6-item reasoning tuple | Active — internal |
| `_parse_risk_profile` | String → `RiskProfile` enum | Active — internal |
| `_parse_market_regime` | String → `MarketRegime` enum | Active — internal |
| `_non_negative_float` | Validates non-negative float field | Active — internal |
| `_round_money` | Rounds to 2 decimal places | Active — internal |
| `_format_money` | Formats float as `$X,XXX.XX` | Active — internal |
| `_render_list` | Formats tuple of strings as bullet list | Active — internal |

---

## Export Review (`__init__.py`)

| Export | Active? | External production callers |
|---|---|---|
| `CapitalDeploymentPlan` | Via `RiskAnalysis` | 0 direct; accessed via `.deployment_plan` in `atlas/intelligence/engine.py` |
| `CurrentPosition` | Engine-internal only | 0 production |
| `PositionSizingInput` | Test-only | 0 production |
| `PositionSizingResult` | Via `RiskAnalysis` | 0 direct; accessed via `.position_sizing` in intelligence |
| `RiskAnalysis` | ✓ | 2 production engines |
| `RiskEngine` | Test-only | 0 production |
| `RiskProfile` | Engine-internal only | 0 production external |
| `render_risk_analysis` | Test-only | 0 production |

**Finding:** Only `RiskAnalysis` has active production callers outside the package. All other exports are either engine-internal or test-only.

**`render_risk_analysis` classification:** Test-only. The `atlas risk size` CLI command that previously called it was retired Sprint 88. Only `tests/test_risk_engine.py` calls it. Not a critical cleanup target.

---

## Production Caller Map

### Two active production callers.

### `atlas/conversation/engine.py`

| Detail | Value |
|---|---|
| Import | `from atlas.risk import RiskAnalysis` |
| Usage | `risk_analysis: RiskAnalysis \| None = None` field in `ConversationInput` dataclass |
| Runtime role | Optional input to conversation engine; enables risk context in Q&A responses |
| Fields accessed | None directly in caller (passed through as optional context) |
| Core to path? | No — optional context enrichment |
| Risk of changing `RiskAnalysis` shape | LOW — conversation engine passes the object through; does not access specific sub-fields |

### `atlas/intelligence/engine.py`

| Detail | Value |
|---|---|
| Import | `from atlas.risk import RiskAnalysis` |
| Usage | `risk_analysis: RiskAnalysis \| None` in `IntelligenceInput` and `IntelligenceReport`; accessed in 3 helper functions |
| Runtime role | Optional risk context block in intelligence report output |
| Fields accessed | `.position_sizing.liquidity_warning`, `.position_sizing.concentration_warning`, `.position_sizing.cash_reserve_status`, `.deployment_plan.market_regime_adjustment` |
| Core to path? | No — optional section in intelligence output |
| Risk of changing `RiskAnalysis` shape | **MEDIUM** — intelligence engine accesses 4 specific sub-fields; shape changes would break output |

---

## `RiskEngine` Caller Review

**Zero production instantiation points.** `RiskEngine` is only instantiated in `tests/test_risk_engine.py`.

The deprecated CLI command `atlas risk size` (retired Sprint 88) was the last production instantiation site. After command body retirement, no production code calls `RiskEngine().analyze()`.

**Blocker for `RiskEngine` deletion:** `RiskEngine` and `RiskAnalysis` are defined in the same file (`atlas/risk/engine.py`). `RiskAnalysis` is still an active production type used by 2 engines. Deleting `RiskEngine` without moving `RiskAnalysis` to a separate file would require surgery to `engine.py` and `__init__.py`. That surgery is:
- Non-trivial
- Would require a migration sprint
- Would not change any production behavior (only internal code organization)
- Carries non-zero risk of breaking the import chain for the 2 active callers

---

## Self-Contained Boundary Review

`atlas/risk/engine.py` imports from:

| Import | Package | Classification |
|---|---|---|
| `atlas.analysis.scores.clamp_score` | `atlas/analysis/scores.py` | **Expected — still active.** `atlas/analysis/scores.py` (2 lines) was not deleted in Sprint 141 (only `atlas/analysis/portfolio.py`, `comparison.py`, etc. were deleted). `clamp_score` is a utility function; legitimate dependency. |
| `atlas.market.MarketRegime` | `atlas/market/` | **Expected dependency** — Group B module type. `MarketRegime` is the market regime enum; risk engine uses it to determine deployment pacing. |

**Zero imports from:**
- `atlas/providers/` ✓ — no network calls
- `atlas/cli/` ✓
- `atlas/dashboard/` ✓
- `atlas/conversation/` ✓
- `atlas/intelligence/` ✓
- `atlas/decision/` (legacy) ✓
- `atlas/domains/` ✓
- `atlas/reasoning/` ✓ (deleted Sprint 153)

**Conclusion:** Boundary is clean. No upward dependency violations. Two legitimate dependencies: a utility function and a market type. Both are stable.

---

## Stale Import Audit

**Zero stale closed-track symbols found in `atlas/risk/`.**

No references to:
- `atlas.reasoning`, `ReasoningEngine`, `ReasoningReport`, `render_reasoning_report` (package deleted Sprint 153)
- `atlas.analysis.portfolio`, `PortfolioAnalysis`, `PortfolioSignal`, `CompanyPortfolioProfile`
- `atlas.analysis.comparison`, `atlas.analysis.memory`, `atlas.analysis.scoring`, `atlas.analysis.watchlist`
- `render_comparison_result`, `YahooCompany`, `YahooFinancials`, `YahooMarketData`
- `portfolio_fit_input_from_profile`, `PortfolioFitInput`, `PortfolioIntelligenceEngine`

---

## Blueprint Overlap Review

| Domain/Capability | Overlap with `atlas/risk/`? |
|---|---|
| `atlas/domains/` | No `atlas/domains/risk/` exists. No Blueprint-aligned risk domain. |
| `atlas/capabilities/` | No risk capability exists. No Blueprint wrapper for position sizing. |
| `atlas/domains/decision/` | Has an `Evidence`-based reasoning model, not position sizing. No overlap. |
| `atlas/capabilities/portfolio_intelligence/` | Provides `PortfolioFitResult` (sector concentration, overlap, fit score) — complementary but distinct from position sizing and deployment pacing. No overlap. |

**Conclusion:** No Blueprint-aligned successor exists for `atlas/risk/RiskEngine` or `RiskAnalysis`. The position-sizing and deployment-pacing logic in `atlas/risk/` is standalone with no equivalent in `atlas/domains/` or `atlas/capabilities/`. `RiskAnalysis` is best left as a standalone shared type.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Callers | Risk | Sprint 155? |
|---|---|---|---|---|
| `RiskEngine` | Zero production instantiation — CLI retired Sprint 88 | 0 production, test-only | **MEDIUM** — shares file with active `RiskAnalysis`; surgery required to separate | No — surgery risk outweighs value |
| `render_risk_analysis` | Test-only — zero production callers | 0 production | LOW | Possible future sprint but low value |
| `PositionSizingInput`, `CurrentPosition`, `RiskProfile` | Zero external production callers | 0 production | LOW — all used internally by `RiskEngine` | No — removing would require `RiskEngine` deletion first |
| `RiskAnalysis` | **2 active production callers** | 2 production | N/A | Leave unchanged — actively used |
| `CapitalDeploymentPlan`, `PositionSizingResult` | Sub-fields of active `RiskAnalysis` | N/A | N/A | Leave unchanged |

**Overall assessment:** The risk package is stable. `RiskAnalysis` is actively used and cannot be removed without migrating its 2 callers. `RiskEngine` cannot be removed without separating `RiskAnalysis` into its own file (surgery). There is no dead code that can be trivially removed. No Blueprint successor exists. No consolidation candidates exist. No stale migration residue.

---

## Recommended Sprint 155 Target

**Close the risk cleanup track.**

After inventory (Sprint 154), the risk package contains no actionable cleanup candidates:
- `RiskAnalysis` is actively used by 2 production engines and must stay
- `RiskEngine` shares a file with `RiskAnalysis` — deletion requires surgery with no current Blueprint migration target
- All private helpers are internal to the dormant engine or active type
- No stale imports, no dead exports, no Blueprint overlap requiring migration
- Boundary is clean: only `atlas.analysis.scores` and `atlas.market` dependencies

Sprint 155 should be a documentation-only sprint confirming the audit findings and closing the track. No code changes are needed.

**Reopening condition:** If a Blueprint-aligned risk capability emerges, or if `RiskAnalysis` callers are migrated away and the type becomes zero-caller, this track should be reopened for `RiskEngine` deletion.

---

## Final Stable Package State (Sprint 155)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 21 | Clean — 8 exports, all intentional |
| `engine.py` | 448 | Active — `RiskAnalysis` shared type; `RiskEngine` dormant but inseparable |

**Provider safety:** Zero provider imports. Zero network access. Deterministic, local-only. ✓

---

## Sprint 155 — Track Closure (COMPLETED)

**Risk cleanup track is CLOSED as of Sprint 155.**

Sprint 155 verified:
- All 8 `atlas.risk` exports remain importable.
- 2 known production callers confirmed (`conversation`, `intelligence`).
- Zero provider imports. Zero upward dependencies.
- Zero stale closed-track imports.
- No Blueprint-aligned successor introduced since Sprint 154.
- No cleanup action is warranted.

**Closure rationale:** After inventory (Sprint 154) and final verification (Sprint 155), the risk package contains only active, intentional code. `RiskAnalysis` is a live shared type; `RiskEngine` cannot be safely removed without it. Further cleanup would create churn without architectural benefit.

**Reopening condition:** If a Blueprint-aligned risk capability emerges, or if the 2 `RiskAnalysis` callers are migrated to a successor type, this track should be reopened.

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
| Risk package | **CLOSED Sprint 155** |

---

## Recommended Sprint 156 Target

**Audit `atlas/principles/` — Group C self-contained module.**

`atlas/principles/` is a natural next audit target after the reasoning package deletion:
- `check_reasoning_report()` was removed in Sprint 152, reducing the principles API
- The remaining exports (`check_conversation_response`, `check_intelligence_report`, `check_suitability_assessment`, `check_text_against_principles`, `PrinciplesEngine`, etc.) should be inventoried and caller-mapped
- The `atlas principles check` CLI command is active — confirming this boundary is well-understood before any future work
- Smallest safe Group C audit-first target after risk.

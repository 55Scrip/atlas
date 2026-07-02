# Portfolio Analysis Migration Plan

**Created:** 2026-07-02 (Sprint 110)  
**Updated:** 2026-07-02 (Sprint 122) — home Portfolio dependency moved to TYPE_CHECKING  
**Status:** IN PROGRESS — Phases 1–3 complete; Phase 4 in progress (8 of ~10 callers migrated: conversation, dashboard, portfolio_review, reasoning, risk_drift, suitability, monitoring, home)  
**Target module:** `atlas/analysis/portfolio.py`  
**Risk:** VERY HIGH — highest remaining coupling in `atlas/analysis/`  

---

## Background

`atlas/analysis/portfolio.py` is the largest legacy module in `atlas/analysis/` at 457 lines.
It has 17 production import sites across 13 packages. A parallel Blueprint-aligned
`atlas/domains/portfolio/` domain already exists, but it operates on a different type
hierarchy (`atlas.shared.Portfolio` with `Holding` objects) and covers structural
calculations only — not the portfolio-fit intelligence that `PortfolioIntelligenceEngine` provides.

Sprint 89 retired the `atlas portfolio analyze` CLI command. The underlying engine remains
because 5+ active runtime paths still depend on it.

---

## Public Symbol Inventory

### Types / Dataclasses

| Symbol | Type | Responsibility | Exported from `__init__` | Blueprint overlap |
|---|---|---|---|---|
| `Portfolio` | dataclass (frozen) | Holds a tuple of `PortfolioPosition` objects; loads from JSON | Yes | `atlas.shared.Portfolio` is the domain equivalent — different schema |
| `PortfolioPosition` | dataclass (frozen) | Single portfolio holding with ticker, sector, country, market_cap, weight, quality_score, risk_score | Yes | `atlas.shared.Holding` is the domain equivalent — no `quality_score`/`risk_score` |
| `PortfolioSignal` | dataclass (frozen) | Score + reasoning for a single portfolio dimension | No | None |
| `PortfolioRecommendation` | str Enum | STRONG_ADD / ADD / NEUTRAL / REDUCE / AVOID | Yes | None |
| `PortfolioAnalysis` | dataclass (frozen) | Full portfolio-fit result: 7 signals + portfolio_score + recommendation + final_reasoning | Yes | None |
| `CompanyPortfolioProfile` | dataclass (frozen) | Provider contract: ticker, company, sector, country, market_cap, quality_score, risk_score | No (TYPE_CHECKING only in `providers/base.py`) | None |
| `DEFAULT_TARGET_WEIGHT` | float constant | Default 5% position target weight | No | None |

### Classes / Engines

| Symbol | Type | Responsibility | Callers | Blueprint overlap |
|---|---|---|---|---|
| `PortfolioIntelligenceEngine` | class | Runs 7-dimension portfolio-fit analysis for a target ticker against a portfolio | 5 production engines | None — no equivalent in Blueprint |
| `PortfolioIntelligenceEngine.analyze()` | method | Accepts `Portfolio` + `CompanyPortfolioProfile` → `PortfolioAnalysis` | Called by `decision_engine`, `intelligence/engine`, `conversation/engine`, `dashboard/engine` | None |
| `PortfolioIntelligenceEngine.analyze_ticker()` | method | Accepts `Portfolio` + ticker + provider → calls `provider.get_portfolio_profile()` | Called by `intelligence/engine` | None |

### Functions

| Symbol | Responsibility | Callers | Pure? | User-facing output? |
|---|---|---|---|---|
| `get_mock_company_portfolio_profile(ticker)` | Returns mock `CompanyPortfolioProfile` via `MockCompanyAnalysisProvider` | `tests/test_portfolio.py`, `tests/test_providers.py` | Yes (deferred import) | No |
| `render_portfolio_analysis(analysis)` | **Sprint 111 ✓ DELETED** — zero production callers; `_score_line` and `_signal_line` helpers also removed | — | — | — |

### Private functions (all internal, pure calculations)

`_position_from_mapping`, `_diversification_impact`, `_sector_concentration`,
`_country_concentration`, `_market_cap_concentration`, `_overlap_with_existing_holdings`,
`_expected_quality_impact`, `_expected_risk_impact`, `_aggregate_portfolio_score`,
`_recommend`, `_final_reasoning`, `_weight_by_attribute`, `_mega_cap_weight`,
`_weighted_average`, `_pro_forma_average`, `_concentration_score`, `_normalize_weight`,
`_is_mega_cap`, `_score_line`, `_signal_line`

All private functions are pure calculations. None produce I/O. All are candidates for
extraction into a future `atlas/capabilities/portfolio_intelligence/` module.

---

## Production Caller Map

**17 production import sites across 13 packages:**

| File | What it imports | How it uses it | CLI path? |
|---|---|---|---|
| `atlas/analysis/__init__.py` | `Portfolio`, `PortfolioAnalysis`, `PortfolioIntelligenceEngine`, `PortfolioPosition`, `PortfolioRecommendation`, `get_mock_company_portfolio_profile` | Re-export hub | — |
| `atlas/adapters/portfolio.py` | `Portfolio as LegacyPortfolio` | Adapter: converts legacy `Portfolio` → domain `Portfolio` | `atlas portfolio summary` |
| `atlas/cli/main.py` | `Portfolio` | `Portfolio.from_json_file(path)` in 5+ commands | All portfolio-adjacent CLI commands |
| `atlas/conversation/engine.py` | `Portfolio`, `PortfolioIntelligenceEngine` | `atlas ask --portfolio` | `atlas ask` |
| `atlas/dashboard/engine.py` | `Portfolio`, `PortfolioIntelligenceEngine` | `atlas dashboard show` | `atlas dashboard show` |
| `atlas/decision/decision_context.py` | `Portfolio` | Type annotation in `DecisionContext.portfolio` field | `atlas decide`, `atlas intelligence` |
| `atlas/decision/decision_engine.py` | `PortfolioAnalysis`, `PortfolioIntelligenceEngine` | Runs portfolio-fit as part of decision scoring | `atlas decide` |
| `atlas/decision/decision_result.py` | `PortfolioAnalysis` | Type annotation in `DecisionResult` | `atlas decide` |
| `atlas/home/engine.py` | `Portfolio` | `atlas home` | `atlas home` |
| `atlas/intelligence/engine.py` | `Portfolio`, `PortfolioAnalysis`, `PortfolioIntelligenceEngine` | Full intelligence briefing with portfolio context | `atlas intelligence`, `atlas daily-brief` |
| `atlas/monitoring/engine.py` | `Portfolio` | Type annotation for monitoring input | `atlas monitor` |
| `atlas/portfolio_review/engine.py` | `Portfolio` | `atlas portfolio review` | `atlas portfolio review` |
| `atlas/providers/base.py` | `CompanyPortfolioProfile` | TYPE_CHECKING only — provider interface contract | All provider-using commands |
| `atlas/providers/mock.py` | `CompanyPortfolioProfile` | Mock data dict | All mock-provider commands |
| `atlas/providers/yahoo.py` | `CompanyPortfolioProfile` | Returns `CompanyPortfolioProfile` from Yahoo data | `--provider yahoo` paths |
| `atlas/reasoning/engine.py` | `PortfolioAnalysis` | Type annotation in `ReasoningContext` | Reasoning flows |
| `atlas/risk_drift/engine.py` | `Portfolio`, `PortfolioAnalysis` | Risk drift calculations with portfolio context | `atlas risk-drift` |
| `atlas/suitability/engine.py` | `Portfolio`, `PortfolioAnalysis` | Suitability analysis with portfolio context | `atlas decide`, suitability flows |

**Test callers:** 16 test files.

---

## Runtime Flow Map

### Flow 1: `atlas portfolio summary` (Blueprint-aligned — ALREADY MIGRATED)

```
atlas/cli/main.py: portfolio_summary_command()
  → Portfolio.from_json_file(path)                      [atlas.analysis.portfolio.Portfolio]
  → legacy_portfolio_to_domain_portfolio(legacy)         [atlas/adapters/portfolio.py]
  → domain_portfolio_summary(domain_portfolio)            [atlas/domains/portfolio/calculations.py]
  → _render_portfolio_domain_summary(summary)             [CLI helper]
```

**Status:** This flow already bypasses `PortfolioIntelligenceEngine` entirely.
`Portfolio` (legacy) is used only as the JSON-loading bridge; the adapter converts
it immediately to `atlas.shared.Portfolio`. This flow is the template for future migration.

### Flow 2: `atlas portfolio review` (active, uses legacy engine indirectly)

```
atlas/cli/main.py: portfolio_review_command()
  → Portfolio.from_json_file(path)                      [atlas.analysis.portfolio.Portfolio]
  → AtlasPortfolioReview().review(portfolio, provider)   [atlas/portfolio_review/engine.py]
     → PortfolioIntelligenceEngine().analyze_ticker()    [atlas.analysis.portfolio]
```

**Status:** Still uses legacy `PortfolioIntelligenceEngine`.

### Flow 3: `atlas decide` (active, uses `PortfolioIntelligenceEngine`)

```
atlas/cli/main.py: decide_command()
  → Portfolio.from_json_file(path)                      [atlas.analysis.portfolio.Portfolio]
  → AtlasDecisionEngine().decide(context)
     → PortfolioIntelligenceEngine().analyze(...)        [atlas.analysis.portfolio]
     → PortfolioAnalysis                                 [atlas.analysis.portfolio]
```

**Status:** Core decision path depends on `PortfolioIntelligenceEngine`.

### Flow 4: `atlas intelligence` / daily brief (active, uses `PortfolioIntelligenceEngine`)

```
atlas/cli/main.py: intelligence_command()
  → Portfolio.from_json_file(path)
  → IntelligenceEngine().analyze(...)
     → PortfolioIntelligenceEngine().analyze_ticker()    [atlas.analysis.portfolio]
     → PortfolioAnalysis                                 [atlas.analysis.portfolio]
```

**Status:** Core intelligence path depends on `PortfolioIntelligenceEngine`.

### Flow 5: `atlas ask --portfolio` (active)

```
atlas/cli/main.py: ask_command()
  → Portfolio.from_json_file(path)
  → ConversationEngine().answer(...)
     → PortfolioIntelligenceEngine().analyze(...)        [atlas.analysis.portfolio]
```

**Status:** Conversation depends on `PortfolioIntelligenceEngine`.

### Flow 6: Provider interface (active)

```
CompanyDataProvider.get_portfolio_profile(ticker)
  → CompanyPortfolioProfile                              [atlas.analysis.portfolio]

MockCompanyAnalysisProvider / YahooFinanceProvider
  → returns CompanyPortfolioProfile
  → consumed by PortfolioIntelligenceEngine.analyze_ticker()
```

**Status:** Provider interface is coupled to `CompanyPortfolioProfile`.
Migrating `CompanyPortfolioProfile` requires updating all 3 provider files.

---

## Blueprint Overlap Analysis

### What `atlas/domains/portfolio/` already covers

| Capability | Blueprint domain | Legacy equivalent | Overlap? |
|---|---|---|---|
| Portfolio structure (holdings, sectors, countries) | `atlas.shared.Portfolio` + `Holding` | `Portfolio` + `PortfolioPosition` | Same concept, different schema |
| Sector allocation | `sector_allocation()` in `calculations.py` | `_weight_by_attribute(...)` in `portfolio.py` | Similar but different inputs |
| Country allocation | `country_allocation()` | `_country_concentration(...)` | Similar but different inputs |
| Concentration scoring | `concentration_level()` | `_aggregate_portfolio_score()` | Similar concept, different scoring model |
| Portfolio summary | `portfolio_summary()` | (none — `atlas portfolio analyze` was retired) | Blueprint is the current path |
| Validation | `validate_portfolio()` | (none in legacy) | Blueprint only |
| Portfolio-fit scoring | None | `PortfolioIntelligenceEngine` | **No Blueprint equivalent** |
| 7-dimension fit analysis | None | `_diversification_impact`, `_sector_concentration`, etc. | **No Blueprint equivalent** |
| `CompanyPortfolioProfile` | None | `CompanyPortfolioProfile` — provider contract | **No Blueprint equivalent** |

### What has NO Blueprint equivalent

- `PortfolioIntelligenceEngine` and all 7-dimension analysis calculations
- `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation`
- `CompanyPortfolioProfile` — provider-level contract type
- `render_portfolio_analysis()` — **deleted Sprint 111** (zero callers)

These represent the core behavioral functionality. They cannot be deleted until a
Blueprint-aligned `atlas/capabilities/portfolio_intelligence/` capability is created.

### What CAN be migrated incrementally

- `Portfolio` loading: already handled via `atlas/adapters/portfolio.py` for `summary` command.
  CLI callers could use `Portfolio.from_json_file()` as a loading helper only, then convert
  immediately via `legacy_portfolio_to_domain_portfolio()`.
- `PortfolioPosition` → `atlas.shared.Holding`: the adapter already does this. The type itself
  could eventually be removed when all callers stop needing raw `PortfolioPosition`.

---

## Provider Safety

`atlas/analysis/portfolio.py` has **no direct network calls**.

- `PortfolioIntelligenceEngine.analyze_ticker()` accepts a `CompanyDataProvider` but does not
  call it directly — it calls `provider.get_portfolio_profile(ticker)` which is the provider's
  responsibility.
- `Portfolio.from_json_file()` reads a local JSON file (no network).
- All 7-dimension analysis functions are pure calculations.
- `get_mock_company_portfolio_profile()` makes a deferred import of `MockCompanyAnalysisProvider`
  but does not call external APIs.

Provider boundary change: migrating `CompanyPortfolioProfile` would require updating
`providers/base.py`, `providers/mock.py`, and `providers/yahoo.py` simultaneously. This is
a HIGH-RISK coordinated change and should be done as a dedicated sprint, not incidentally.

---

## Risk Assessment

| Risk | Level | Notes |
|---|---|---|
| Breaking `atlas decide` | CRITICAL | Decision engine's portfolio-fit scoring uses `PortfolioIntelligenceEngine` and `PortfolioAnalysis` directly |
| Breaking `atlas intelligence` / daily brief | CRITICAL | Intelligence engine generates portfolio-fit narrative from `PortfolioAnalysis` |
| Breaking provider contract (`CompanyPortfolioProfile`) | HIGH | 3 provider files must be updated atomically |
| Breaking test suite | MEDIUM | 16 test files reference `portfolio.py` symbols |
| Schema mismatch (legacy vs domain `Portfolio`) | HIGH | `PortfolioPosition` has `quality_score`/`risk_score`; `Holding` does not — adapter cannot carry these without extension |
| No Blueprint replacement for `PortfolioIntelligenceEngine` | BLOCKING | Must create `atlas/capabilities/portfolio_intelligence/` before engine can be retired |

---

## Migration Phases

### Phase 1 — Guardrail sprint ✓ COMPLETE (Sprints 110–111)

**Sprint 110:** Pre-migration guardrails added:
- `test_portfolio_domain_remains_importable` — Blueprint domain intact
- `test_portfolio_summary_command_uses_adapter_path` — already-migrated CLI path confirmed
- `test_render_portfolio_analysis_has_no_active_production_caller` → flipped to `test_render_portfolio_analysis_is_deleted`

**Sprint 111:** `render_portfolio_analysis` deleted. Zero production callers confirmed.
- `render_portfolio_analysis` removed from `atlas/analysis/portfolio.py`
- `_score_line` and `_signal_line` private helpers also removed (only used by `render_portfolio_analysis`)
- `render_portfolio_analysis` removed from `atlas/analysis/__init__.py` import and `__all__`
- `tests/test_portfolio.py` stripped of `render_portfolio_analysis` test and import
- Guardrail tests added: `test_render_portfolio_analysis_is_deleted`, `test_render_portfolio_analysis_not_in_atlas_analysis`

### Phase 2 — Capability stub ✓ COMPLETE (Sprint 112)

**Created `atlas/capabilities/portfolio_intelligence/` with:**

- `PortfolioFitDimension` — replaces `PortfolioSignal`; uses neutral `note` field instead of `reasoning`
- `PortfolioFitInput` — Blueprint-aligned equivalent of `CompanyPortfolioProfile`
- `PortfolioFitResult` — Blueprint-aligned equivalent of `PortfolioAnalysis`; omits `recommendation` enum (no advisory semantics in Blueprint layer); renames `portfolio_score` → `fit_score` and `final_reasoning` → `summary`

**No existing callers migrated.** All legacy `atlas.analysis.portfolio` imports unchanged.

**12 tests added** in `tests/test_portfolio_intelligence_capability.py` covering importability, instantiation, immutability, determinism, and boundary constraints (no provider imports, no legacy imports).

**Legacy type mapping (documented in models.py docstrings):**

| Legacy (`atlas.analysis.portfolio`) | Blueprint (`atlas.capabilities.portfolio_intelligence`) |
|---|---|
| `CompanyPortfolioProfile` | `PortfolioFitInput` |
| `PortfolioAnalysis` | `PortfolioFitResult` |
| `PortfolioSignal` | `PortfolioFitDimension` |
| `portfolio_score` field | `fit_score` (renamed) |
| `final_reasoning` field | `summary` (renamed) |
| `recommendation` (enum) | **omitted** — no advisory semantics |

### Phase 3 — Engine implementation ✓ COMPLETE (Sprint 113)

**Created `atlas/capabilities/portfolio_intelligence/engine.py` with:**
- `PortfolioIntelligenceCapability.analyze(portfolio, fit_input, target_weight)` → `PortfolioFitResult`
- 7-dimension scoring ported from legacy `_diversification_impact`, `_sector_concentration`,
  `_country_concentration`, `_market_cap_concentration`, `_overlap_with_existing_holdings`,
  `_expected_quality_impact`, `_expected_risk_impact`, `_aggregate_portfolio_score`
- Package exports updated: `PortfolioIntelligenceCapability` added to `__init__.py`
- 30 new tests in `tests/test_portfolio_intelligence_engine.py`
- All 1181 tests passing (3 skipped). Demo passed. RC2 green.

**Schema gap — resolved in Sprint 114:**

`atlas.shared.Holding` was extended with optional `quality_score: int | None`, `risk_score: int | None`,
and `market_cap: float | None` fields (all default `None`). All existing `Holding` instantiation sites
use keyword args — zero blast radius. The adapter (`atlas/adapters/portfolio.py`) now carries these
fields from legacy `PortfolioPosition` when converting.

| Dimension | Parity (Sprint 113) | Parity (Sprint 114+) |
|---|---|---|
| `sector_concentration` | ✓ Full | ✓ Full |
| `country_concentration` | ✓ Full | ✓ Full |
| `overlap_with_existing_holdings` | ✓ Full | ✓ Full |
| `diversification_impact` | Partial (mega-cap = 0) | ✓ Full (when `Holding.market_cap` present) |
| `market_cap_concentration` | Gap (score=50) | ✓ Full (when `Holding.market_cap` present) |
| `quality_impact` | Partial (target only) | ✓ Full (when `Holding.quality_score` present) |
| `risk_impact` | Partial (target only) | ✓ Full (when `Holding.risk_score` present) |

Fallback behavior retained for `Holding` instances without enriched fields (backwards compatible).

**Sprint 114 caller migrated:** `atlas/conversation/engine.py` portfolio-fit path now uses
`PortfolioIntelligenceCapability` via the adapter. Legacy `portfolio_engine` (PortfolioIntelligenceEngine)
retained for `IntelligenceEngine` injection (not migrated).

**Remaining legacy callers:** 16 production import sites still on `atlas.analysis.portfolio`.

### Phase 4 — Caller migration (Sprints 114+, one caller per sprint)
Migrate one production caller per sprint, in order of impact risk:

1. ✓ `atlas/conversation/engine.py` — **MIGRATED Sprint 114**; `portfolio_fit_capability` added; `_answer_portfolio_review` uses new capability via adapter
2. ✓ `atlas/dashboard/engine.py` — **MIGRATED Sprint 115**; `portfolio_fit_capability` added; `_portfolio_section` target-fit block uses new capability via adapter
3. ✓ `atlas/portfolio_review/engine.py` — **MIGRATED Sprint 116**; internal structural functions (`_average`, `_largest_position`, `_top_exposure`, `_strengths_section`, `_main_risks_section`, `_theme_exposure_section`, `_follow_up_questions_section`) now use `atlas.shared.Portfolio` via adapter; legacy `Portfolio` retained at input boundary for suitability/risk_drift/monitoring downstream

**Sprint 117 adapter checkpoint:** `portfolio_fit_input_from_profile` centralized in `atlas/adapters/portfolio.py` (Sprint 117). `legacy_portfolio_to_domain_portfolio` was already centralized. Conversation and dashboard both updated to use the shared builder. No new caller migrated.

4. ✓ `atlas/reasoning/engine.py` — **MIGRATED Sprint 118**; `from atlas.analysis.portfolio import PortfolioAnalysis` moved behind `TYPE_CHECKING` guard; `from __future__ import annotations` added; runtime field accesses (`analysis.final_reasoning`, `analysis.portfolio_score`, `analysis.sector_concentration.*`) remain as duck-typed attribute access — no import needed. No behavior change.

5. ✓ `atlas/risk_drift/engine.py` — **MIGRATED Sprint 119**; `Portfolio` moved to TYPE_CHECKING (duck-typed `.positions` access preserved for current callers); `PortfolioAnalysis` removed — `current_portfolio_analysis` field now typed as `PortfolioFitResult | None`; `_concentration_in_portfolio_analysis` updated to use `.overlap.score`. Dead code path — no behavior change.

6. ✓ `atlas/suitability/engine.py` — **MIGRATED Sprint 120**; `Portfolio` moved to TYPE_CHECKING (duck-typed access preserved); `PortfolioAnalysis` removed — `portfolio_analysis` field now typed as `PortfolioFitResult | None`; `_concentration_impact` updated to use `.overlap` instead of `.overlap_with_existing_holdings`. No caller passes `portfolio_analysis` — dead field, no behavior change.

7. ✓ `atlas/monitoring/engine.py` — **MIGRATED Sprint 121**; `Portfolio` moved to TYPE_CHECKING (Option D — annotation-only). No `PortfolioAnalysis` or `PortfolioIntelligenceEngine` imports present. Duck-typed `.positions`, `.ticker`, `.weight`, `.sector`, `.country`, `.quality_score`, `.risk_score` access preserved. All callers (cli, dashboard, portfolio_review) pass legacy Portfolio objects unchanged. No behavior change.

8. ✓ `atlas/home/engine.py` — **MIGRATED Sprint 122**; `Portfolio` moved to TYPE_CHECKING (Option D — pure annotation-only). `AtlasHomeInput.portfolio: Portfolio | None` is never field-accessed inside the engine — only None-checked and passed through to `PortfolioReviewInput`. Zero behavior change. 7 new guardrail tests.

**Recommended Sprint 123 target:** `atlas/decision/` — audit `decision_context.py` (Portfolio annotation), `decision_result.py` (PortfolioAnalysis annotation), `decision_engine.py` (PortfolioIntelligenceEngine runtime — highest coupling; audit before migrating).

9. `atlas/decision/decision_engine.py` + `decision_context.py` + `decision_result.py` — highest coupling; migrate last
10. `atlas/intelligence/engine.py` — highest integration surface; migrate after decision

### Phase 5 — Provider migration (Sprint ~120)
After all callers are migrated off `CompanyPortfolioProfile`:
- Remove `CompanyPortfolioProfile` from `providers/base.py`, `providers/mock.py`, `providers/yahoo.py`
- This requires defining a replacement provider contract in the capability layer first

### Phase 6 — Deletion (Sprint ~121)
After zero active callers remain:
- Delete `atlas/analysis/portfolio.py`
- Remove all re-exports from `atlas/analysis/__init__.py`
- Remove `Portfolio` import from `atlas/cli/main.py` (use domain `Portfolio` loading directly)
- Delete `atlas/adapters/portfolio.py` or repurpose as domain-to-domain adapter

**Deletion criteria:**
- `grep -rn "from atlas.analysis.portfolio" atlas/` returns zero results
- `atlas/analysis/portfolio.py` has no active callers
- All tests that use legacy portfolio types have been updated

---

## Recommended Sprint 111 Target

**Sprint 111: Pre-migration guardrail sprint (Phase 1 only).**

Add 3–4 lightweight guardrail tests:
1. Named production callers of `atlas.analysis.portfolio` still import from it (intent lock)
2. `atlas.domains.portfolio` is importable and core symbols are accessible
3. `atlas portfolio summary` command uses the adapter path (already-migrated path stays migrated)
4. `render_portfolio_analysis` is confirmed to have no active non-test production callers
   (prep for future removal of this rendering helper)

**Why guardrails first:**
- A 17-caller module is too risky to migrate without an explicit intent-lock test.
  If a caller accidentally stops importing from `atlas.analysis.portfolio` during an
  unrelated refactor, we need a guardrail that catches the drift — not in the deletion
  direction, but in the "confirm all callers still present" direction during Phase 1.
- No behavior change. No migration risk. Only test additions.

**Tentative Sprint 112:** `PortfolioSignal` type extraction.  
**Tentative Sprint 113–114:** `atlas/capabilities/portfolio_intelligence/` creation.  
**Tentative Sprint 115+:** Caller-by-caller migration.

---

## Why Not Migrate Now

1. **No Blueprint replacement for `PortfolioIntelligenceEngine`.** The 7-dimension
   portfolio-fit scoring has no equivalent in `atlas/domains/portfolio/` or
   `atlas/capabilities/`. Building it is a multi-sprint effort.

2. **Schema gap: `quality_score`/`risk_score` missing from `atlas.shared.Holding`.**
   The intelligence analysis depends on per-holding quality and risk scores. The domain
   `Holding` entity carries only market value and weight. Bridging this gap requires either
   extending `Holding` (risky for the domain layer) or creating a new `PortfolioFitProfile`
   type in the capability layer.

3. **Provider contract coupling.** `CompanyPortfolioProfile` is embedded in the provider
   interface (`CompanyDataProvider.get_portfolio_profile()`). Changing it requires updating
   all 3 provider implementations atomically.

4. **17 active import sites.** Migrating one or two callers at a time is the only safe
   approach. Each migration sprint must leave all other callers working unchanged.

5. **Existing deprecation guardrail.** `test_portfolio_analyze_deprecation.py` asserts
   that named callers still import from `atlas.analysis.portfolio` as a lock. Any migration
   sprint must update that guardrail in sync with the migration.

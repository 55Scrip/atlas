# Portfolio Analysis Migration Plan

**Created:** 2026-07-02 (Sprint 110)  
**Updated:** 2026-07-02 (Sprint 134) — Sprint 134 audit: `Portfolio`/`PortfolioPosition` caller map complete; Sprint 135 target selected.  
**Status:** IN PROGRESS — `portfolio.py` now 67 lines (2 active types + 2 private helpers). Remaining: `Portfolio` (CLI boundary, adapter input, 8 annotation callers) and `PortfolioPosition` (internal to `Portfolio`). Sprint 135 will lift both into `atlas/adapters/portfolio.py` and delete the file.  
**Target module:** `atlas/analysis/portfolio.py`  
**Risk:** MEDIUM — all remaining callers are known; changes are mechanical import-line updates  

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

## Public Symbol Inventory (Sprint 129 Audit)

### Types / Dataclasses — Remaining

| Symbol | Type | `__init__` export | Production runtime callers | Annotation-only callers | Blueprint destination |
|---|---|---|---|---|---|
| `Portfolio` | dataclass (frozen) | Yes | `cli/main.py` (JSON loading, 9 call sites), `adapters/portfolio.py` (adapter input), `portfolio_review/engine.py` (struct field) | `home`, `suitability`, `risk_drift`, `intelligence`, `dashboard`, `conversation`, `decision_context`, `monitoring` (TYPE_CHECKING — 8 engines) | `atlas/adapters/portfolio.py` (move in Sprint 135) |
| `PortfolioPosition` | dataclass (frozen) | Yes | None — constructed only by `_position_from_mapping` inside `portfolio.py` | None | `atlas/adapters/portfolio.py` (move with Portfolio in Sprint 135) |
| ~~`PortfolioSignal`~~ | ~~dataclass (frozen)~~ | No | None → **DELETED Sprint 132** | — | `PortfolioFitDimension` ✓ |
| ~~`PortfolioRecommendation`~~ | ~~str Enum~~ | ~~Yes~~ | None → **DELETED Sprint 132** | — | None — intentionally omitted from Blueprint layer |
| ~~`PortfolioAnalysis`~~ | ~~dataclass (frozen)~~ | ~~Yes~~ | None → **DELETED Sprint 132** | — | `PortfolioFitResult` ✓ |
| `CompanyPortfolioProfile` | dataclass (frozen) | No | `providers/mock.py`, `providers/yahoo.py`, `adapters/portfolio.py` | `providers/base.py` TYPE_CHECKING only | `PortfolioFitInput` (Blueprint equivalent exists) |

### Deleted symbols (prior sprints)

| Symbol | Deleted | Sprint |
|---|---|---|
| `PortfolioIntelligenceEngine` | ✓ | Sprint 128 |
| `DEFAULT_TARGET_WEIGHT` | ✓ | Sprint 128 (deleted with class) |
| `render_portfolio_analysis` | ✓ | Sprint 111 |
| `_score_line`, `_signal_line` | ✓ | Sprint 111 |

### Functions — Deleted Sprint 130

| Symbol | Deleted | Sprint |
|---|---|---|
| `get_mock_company_portfolio_profile(ticker)` | ✓ | Sprint 130 — zero active callers confirmed |

### Private functions — Active

| Symbol | Callers |
|---|---|
| `_position_from_mapping` | `Portfolio.from_mapping` (active) |
| `_normalize_weight` | `_position_from_mapping` (active) |

### Private functions — Deleted Sprint 130

These 16 functions were exclusively used by `PortfolioIntelligenceEngine` (deleted Sprint 128).
Zero callers confirmed repo-wide before deletion.

`_diversification_impact`, `_sector_concentration`, `_country_concentration`,
`_market_cap_concentration`, `_overlap_with_existing_holdings`, `_expected_quality_impact`,
`_expected_risk_impact`, `_aggregate_portfolio_score`, `_recommend`, `_final_reasoning`,
`_weight_by_attribute`, `_mega_cap_weight`, `_weighted_average`, `_pro_forma_average`,
`_concentration_score`, `_is_mega_cap`

Blueprint equivalents of all 16 were ported independently to
`atlas/capabilities/portfolio_intelligence/engine.py` in Sprint 113. The legacy copies
were fully superseded and have been removed.

---

## Production Caller Map (Sprint 129 — post-Sprint 128 state)

| File | What it imports | Runtime or annotation | CLI path |
|---|---|---|---|
| `atlas/analysis/__init__.py` | `Portfolio`, `PortfolioAnalysis`, `PortfolioPosition`, `PortfolioRecommendation`, `get_mock_company_portfolio_profile` | Re-export hub | — |
| `atlas/adapters/portfolio.py` | `Portfolio as LegacyPortfolio`, `CompanyPortfolioProfile` | **RUNTIME** — adapter boundary | `atlas portfolio summary`, `atlas portfolio review`, capability analyze flows |
| `atlas/cli/main.py` | `Portfolio` | **RUNTIME** — JSON loading | All portfolio CLI commands |
| `atlas/conversation/engine.py` | `Portfolio` | TYPE_CHECKING annotation only | `atlas ask` |
| `atlas/dashboard/engine.py` | `Portfolio` | TYPE_CHECKING annotation only | `atlas dashboard show` |
| `atlas/decision/decision_context.py` | `Portfolio` | TYPE_CHECKING annotation only | `atlas decide` |
| `atlas/home/engine.py` | `Portfolio` | TYPE_CHECKING annotation only | `atlas home` |
| `atlas/intelligence/engine.py` | `Portfolio` | TYPE_CHECKING annotation only | `atlas intelligence` |
| `atlas/monitoring/engine.py` | `Portfolio` | TYPE_CHECKING annotation only | `atlas monitor` |
| `atlas/portfolio_review/engine.py` | `Portfolio` (via LegacyPortfolio) | **RUNTIME** — structural analysis input | `atlas portfolio review` |
| `atlas/providers/base.py` | `CompanyPortfolioProfile` | TYPE_CHECKING only — provider protocol | All provider-using commands |
| `atlas/providers/mock.py` | `CompanyPortfolioProfile` | **RUNTIME** — mock data | Mock provider commands |
| `atlas/providers/yahoo.py` | `CompanyPortfolioProfile` | **RUNTIME** — returns profile from Yahoo | `--provider yahoo` |
| `atlas/reasoning/engine.py` | ~~`PortfolioAnalysis`~~ → `PortfolioFitResult` | **MIGRATED Sprint 131** — `ReasoningInput.portfolio_analysis` retyped; TYPE_CHECKING guard removed | Reasoning flows |
| `atlas/risk_drift/engine.py` | `Portfolio` | TYPE_CHECKING annotation only | `atlas risk-drift` |
| `atlas/suitability/engine.py` | `Portfolio` | TYPE_CHECKING annotation only + runtime `.positions` duck-typing | `atlas decide` |

**Test callers:** ~14 test files use at least one legacy portfolio symbol.

**Key finding (Sprint 129, confirmed Sprint 131):** `PortfolioAnalysis` has zero production runtime callers.
Sprint 131 completed the migration: `reasoning/engine.py` `ReasoningInput.portfolio_analysis` is now
typed as `PortfolioFitResult | None`. The TYPE_CHECKING guard for `PortfolioAnalysis` has been removed.
`PortfolioAnalysis`, `PortfolioSignal`, and `PortfolioRecommendation` are now test-only symbols.

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

### Flow 2: `atlas portfolio review` (active)

```
atlas/cli/main.py: portfolio_review_command()
  → Portfolio.from_json_file(path)                      [atlas.analysis.portfolio.Portfolio]
  → AtlasPortfolioReview().review(portfolio, provider)   [atlas/portfolio_review/engine.py]
     → legacy_portfolio_to_domain_portfolio(portfolio)  [atlas/adapters/portfolio.py]
     → domain structural analysis via atlas.domains.portfolio
```

**Status (Sprint 129):** `PortfolioIntelligenceEngine` no longer called here (was migrated Sprint 116). Only legacy `Portfolio` for JSON loading and adapter conversion.

### Flow 3: `atlas decide` (active — `PortfolioIntelligenceCapability` path)

```
atlas/cli/main.py: decide_command()
  → Portfolio.from_json_file(path)                      [atlas.analysis.portfolio.Portfolio]
  → AtlasDecisionEngine().decide(context)
     → portfolio_fit_input_from_profile(profile)        [atlas/adapters/portfolio.py]
     → legacy_portfolio_to_domain_portfolio(portfolio)  [atlas/adapters/portfolio.py]
     → PortfolioIntelligenceCapability.analyze(...)     [atlas.capabilities.portfolio_intelligence]
     → PortfolioFitResult                               [Blueprint-aligned]
```

**Status (Sprint 129):** Fully migrated to Blueprint capability (Sprint 124). Legacy `Portfolio` used only for JSON loading.

### Flow 4: `atlas intelligence` / daily brief (active — `PortfolioIntelligenceCapability` path)

```
atlas/cli/main.py: intelligence_command()
  → Portfolio.from_json_file(path)
  → IntelligenceEngine().analyze(...)
     → portfolio_fit_input_from_profile(profile)        [atlas/adapters/portfolio.py]
     → legacy_portfolio_to_domain_portfolio(portfolio)  [atlas/adapters/portfolio.py]
     → PortfolioIntelligenceCapability.analyze(...)     [atlas.capabilities.portfolio_intelligence]
     → PortfolioFitResult
```

**Status (Sprint 129):** Fully migrated (Sprint 125). Legacy `Portfolio` used only for JSON loading.

### Flow 5: `atlas ask --portfolio` (active — `PortfolioIntelligenceCapability` path)

```
atlas/cli/main.py: ask_command()
  → Portfolio.from_json_file(path)
  → ConversationEngine().answer(...)
     → PortfolioIntelligenceCapability.analyze(...)     [via adapter chain]
     → PortfolioFitResult
```

**Status (Sprint 129):** Fully migrated (Sprints 114/126). Legacy `Portfolio` used only for JSON loading.

### Flow 6: Provider interface (active)

```
CompanyDataProvider.get_portfolio_profile(ticker)
  → CompanyPortfolioProfile                              [atlas.analysis.portfolio]

MockCompanyAnalysisProvider / YahooFinanceProvider
  → returns CompanyPortfolioProfile
  → consumed by portfolio_fit_input_from_profile()      [atlas/adapters/portfolio.py]
  → PortfolioFitInput                                   [atlas.capabilities.portfolio_intelligence]
```

**Status (Sprint 129):** Provider interface remains coupled to `CompanyPortfolioProfile`.
The adapter (`portfolio_fit_input_from_profile`) converts to `PortfolioFitInput` immediately.
Migrating `CompanyPortfolioProfile` requires updating 3 provider files simultaneously — HIGH risk.

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

4. ✓ `atlas/reasoning/engine.py` — **MIGRATED Sprint 118 + Sprint 131**; Sprint 118: `PortfolioAnalysis` moved behind TYPE_CHECKING guard; Sprint 131: TYPE_CHECKING guard fully removed; `ReasoningInput.portfolio_analysis` retyped as `PortfolioFitResult | None`; field accesses updated: `.final_reasoning` → `.summary`, `.portfolio_score` → `.fit_score`, `.sector_concentration.reasoning` → `.sector_concentration.note`. `PortfolioAnalysis` import eliminated entirely.

5. ✓ `atlas/risk_drift/engine.py` — **MIGRATED Sprint 119**; `Portfolio` moved to TYPE_CHECKING (duck-typed `.positions` access preserved for current callers); `PortfolioAnalysis` removed — `current_portfolio_analysis` field now typed as `PortfolioFitResult | None`; `_concentration_in_portfolio_analysis` updated to use `.overlap.score`. Dead code path — no behavior change.

6. ✓ `atlas/suitability/engine.py` — **MIGRATED Sprint 120**; `Portfolio` moved to TYPE_CHECKING (duck-typed access preserved); `PortfolioAnalysis` removed — `portfolio_analysis` field now typed as `PortfolioFitResult | None`; `_concentration_impact` updated to use `.overlap` instead of `.overlap_with_existing_holdings`. No caller passes `portfolio_analysis` — dead field, no behavior change.

7. ✓ `atlas/monitoring/engine.py` — **MIGRATED Sprint 121**; `Portfolio` moved to TYPE_CHECKING (Option D — annotation-only). No `PortfolioAnalysis` or `PortfolioIntelligenceEngine` imports present. Duck-typed `.positions`, `.ticker`, `.weight`, `.sector`, `.country`, `.quality_score`, `.risk_score` access preserved. All callers (cli, dashboard, portfolio_review) pass legacy Portfolio objects unchanged. No behavior change.

8. ✓ `atlas/home/engine.py` — **MIGRATED Sprint 122**; `Portfolio` moved to TYPE_CHECKING (Option D — pure annotation-only). `AtlasHomeInput.portfolio: Portfolio | None` is never field-accessed inside the engine — only None-checked and passed through to `PortfolioReviewInput`. Zero behavior change. 7 new guardrail tests.

**Sprint 123 — Decision layer audit (COMPLETE):**
- ✓ `atlas/decision/decision_context.py` — `Portfolio` moved to TYPE_CHECKING (annotation-only).
- ✓ `atlas/decision/decision_result.py` — `PortfolioAnalysis` moved to TYPE_CHECKING (annotation-only).
- ✗ `atlas/decision/decision_engine.py` — runtime coupling documented; deferred to Sprint 124.

9. ✓ `atlas/decision/decision_engine.py` — **MIGRATED Sprint 124**; `PortfolioIntelligenceEngine` and `PortfolioAnalysis` removed; `PortfolioIntelligenceCapability` used via constructor injection; `_analyze_portfolio` calls `legacy_portfolio_to_domain_portfolio` + `portfolio_fit_input_from_profile` + `capability.analyze()`; `_decide_action` unified poor-fit guard: `fit_score < 55` replaces legacy `recommendation.value in {"Avoid","Reduce"}` + `portfolio_score < 55` double guard. Documented behavior change: scores in [50,54] now give WATCH or AVOID based on `atlas_score` (previously always WATCH). `decision_result.py` annotation updated from `PortfolioAnalysis` to `PortfolioFitResult`. `atlas/intelligence/engine.py` constructor call updated to drop stale `portfolio_engine=` kwarg. `tests/test_portfolio_analyze_deprecation.py` caller list updated to remove `decision_engine.py`. 11 new Sprint 124 guardrail tests.

10. ✓ `atlas/intelligence/engine.py` — **MIGRATED Sprint 125**; `PortfolioIntelligenceEngine` and `PortfolioAnalysis` removed; `PortfolioIntelligenceCapability` injected via constructor; `_optional_portfolio_analysis` uses adapter chain; `_portfolio_impact` updated to use `.note` (PortfolioFitDimension) instead of `.reasoning` (PortfolioSignal); `_atlas_conclusion` updated `.portfolio_score` → `.fit_score`; `_monitoring_items` updated `.overlap_with_existing_holdings.reasoning` → `.overlap.note`; `Portfolio` moved to TYPE_CHECKING; `IntelligenceReport.portfolio_analysis` annotation updated to `PortfolioFitResult`; `conversation/engine.py` IntelligenceEngine call updated to use `portfolio_fit_capability=` kwarg. 13 new Sprint 125 guardrail tests.

11. ✓ `atlas/conversation/engine.py` — **MIGRATED Sprint 126** (Option A); `portfolio_engine` constructor parameter removed; `self.portfolio_engine` dead attribute removed; `PortfolioIntelligenceEngine` import removed; `Portfolio` moved to TYPE_CHECKING; `from __future__ import annotations` added. `_answer_portfolio_review` already used `self.portfolio_fit_capability` since Sprint 114 — the legacy attribute was never referenced after that migration. 9 new Sprint 126 guardrail tests.

12. ✓ `atlas/dashboard/engine.py` — **MIGRATED Sprint 127** (Option A + B); `portfolio_engine` constructor parameter removed; `self.portfolio_engine` dead attribute removed; `PortfolioIntelligenceEngine` import removed; `Portfolio` moved to TYPE_CHECKING; `from __future__ import annotations` added. `_portfolio_section` target-fit block was already using `self.portfolio_fit_capability` since Sprint 115 — the legacy attribute was never referenced after that migration. 8 new Sprint 127 guardrail tests.

**`PortfolioIntelligenceEngine` runtime caller status: ZERO**
No production engine imports or instantiates `PortfolioIntelligenceEngine` after Sprint 127.

13. ✓ `PortfolioIntelligenceEngine` — **DELETED Sprint 128**. Confirmed zero repo-wide callers. Class removed from `atlas/analysis/portfolio.py`. Re-export removed from `atlas/analysis/__init__.py`. `DEFAULT_TARGET_WEIGHT` constant removed (only used by deleted class). 3 new Sprint 128 guardrail tests confirm not importable from module or `atlas.analysis` namespace.

**Sprint 129 — Remaining symbol audit (COMPLETE):**
- Full public symbol inventory documented (see table above).
- Dead private helpers identified: 16 functions exclusively used by deleted `PortfolioIntelligenceEngine`.
- `get_mock_company_portfolio_profile` confirmed zero active callers (stale import in one test).
- `PortfolioAnalysis` confirmed annotation-only in production (zero runtime callers).
- CLI boundary documented: `Portfolio.from_json_file` is the sole runtime coupling in `cli/main.py`.
- Adapter boundary documented: `adapters/portfolio.py` imports `LegacyPortfolio` and `CompanyPortfolioProfile` intentionally.
- Provider coupling documented: `CompanyPortfolioProfile` used by 3 provider files — HIGH risk to change.
- Sprint 130 target recommended: delete 16 dead private helpers + `get_mock_company_portfolio_profile`.

**Recommended Sprint 130 target:** Delete dead private helpers and `get_mock_company_portfolio_profile`.
See "Sprint 130 Target" section below.

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

**Tentative Sprint 112:** `PortfolioSignal` type extraction. ✓ SUPERSEDED by capability stub approach.  
**Tentative Sprint 113–114:** `atlas/capabilities/portfolio_intelligence/` creation. ✓ COMPLETE.  
**Tentative Sprint 115+:** Caller-by-caller migration. ✓ COMPLETE (Sprints 114–127).

---

## Sprint 130 ✓ COMPLETE

**Deleted: 16 dead private helpers + `get_mock_company_portfolio_profile`.**

Zero-caller audit confirmed before deletion. All 16 helpers had definition-only hits in
`atlas/capabilities/portfolio_intelligence/engine.py` (independently-named functions in a separate
module — not callers of the legacy symbols). `_weighted_average` hit in `suitability/engine.py`
is that file's own local function. No active callers anywhere.

**Changes:**
- Deleted 16 private helper functions from `atlas/analysis/portfolio.py`
- Deleted `get_mock_company_portfolio_profile` from `atlas/analysis/portfolio.py`
- Removed unused `from atlas.providers.base import CompanyDataProvider` import (only needed by deleted helpers)
- Removed `get_mock_company_portfolio_profile` from `atlas/analysis/__init__.py` (import + `__all__`)
- Removed stale `get_mock_company_portfolio_profile` and `PortfolioRecommendation` imports from `tests/test_portfolio.py`
- Flipped Sprint 129 guardrail `test_sprint129_portfolio_module_has_no_private_deleted_symbols` → `test_sprint130_dead_private_helpers_deleted` (now asserts gone)
- Added `test_sprint130_get_mock_company_portfolio_profile_deleted` and `test_sprint130_active_portfolio_helpers_still_present`
- `atlas/analysis/portfolio.py` reduced from ~350 lines to **109 lines**

**Result:** `portfolio.py` now contains only 6 public types + 2 active private helpers
(`_position_from_mapping`, `_normalize_weight`). Clean, minimal, easy to audit.

---

## Sprint 131 ✓ COMPLETE

**Migrated `ReasoningInput.portfolio_analysis` from `PortfolioAnalysis | None` to `PortfolioFitResult | None`.**

**Approach used: Option C (retype as `PortfolioFitResult | None`).**

**Changes made:**
- Removed `from typing import TYPE_CHECKING` (now unused after guard removal)
- Removed `if TYPE_CHECKING: from atlas.analysis.portfolio import PortfolioAnalysis` block
- Added `from atlas.capabilities.portfolio_intelligence import PortfolioFitResult` (runtime import)
- `ReasoningInput.portfolio_analysis: PortfolioAnalysis | None = None` → `PortfolioFitResult | None = None`
- `analysis.final_reasoning` → `analysis.summary` (PortfolioFitResult field)
- `analysis.portfolio_score` → `analysis.fit_score` (PortfolioFitResult field)
- `analysis.sector_concentration.reasoning` → `analysis.sector_concentration.note` (PortfolioFitDimension field)
- `tests/test_reasoning_engine.py`: replaced TYPE_CHECKING guard test with `test_sprint131_reasoning_engine_uses_portfolio_fit_result`; rewrote portfolio field acceptance test using `PortfolioFitResult` + `PortfolioFitDimension`; added 6 Sprint 131 guardrail tests
- `tests/test_portfolio_analyze_deprecation.py`: removed `reasoning/engine.py` from `PORTFOLIO_ENGINE_CALLERS`

**Result:** `PortfolioAnalysis`, `PortfolioSignal`, and `PortfolioRecommendation` are now test-only — zero production callers. Deletion candidates for Sprint 132.

---

## Sprint 132 ✓ COMPLETE

**Deleted `PortfolioAnalysis`, `PortfolioSignal`, and `PortfolioRecommendation` from `atlas/analysis/portfolio.py`.**

**Zero-caller audit result:**
- `PortfolioAnalysis`: zero active production callers. Hits in `atlas/capabilities/portfolio_intelligence/models.py` are docstring comments only (no import). All other hits were test fixtures and stale assertions.
- `PortfolioSignal`: zero active production callers. Only appeared as field types within `PortfolioAnalysis` (also deleted).
- `PortfolioRecommendation`: zero active production callers. Only appeared as a field type within `PortfolioAnalysis` (also deleted). Re-export in `atlas/analysis/__init__.py` was stale.

**Changes:**
- Removed `PortfolioSignal`, `PortfolioRecommendation`, `PortfolioAnalysis` from `atlas/analysis/portfolio.py`
- Removed unused `from enum import Enum` import (only needed by `PortfolioRecommendation`)
- Removed `PortfolioAnalysis` and `PortfolioRecommendation` from `atlas/analysis/__init__.py` (import + `__all__`)
- `portfolio.py` reduced from 109 to **69 lines** (3 active types: `Portfolio`, `PortfolioPosition`, `CompanyPortfolioProfile` + 2 private helpers)
- Flipped 7 stale test assertions from "is importable" to "is NOT importable" / removed stale imports
- Added Sprint 132 guardrail block in `test_portfolio_analyze_deprecation.py` (8 new tests)
- Added `test_sprint132_portfolio_analysis_deleted` in `test_portfolio_intelligence_engine.py`
- Added `test_sprint132_portfolio_analysis_signal_recommendation_deleted` in `test_reasoning_engine.py`

**Result:** `atlas/analysis/portfolio.py` is now a minimal boundary module — 3 active types only.

---

## Sprint 133 ✓ COMPLETE

**Migrated `CompanyDataProvider.get_portfolio_profile()` return type from `CompanyPortfolioProfile` to `PortfolioFitInput`. Deleted `CompanyPortfolioProfile` from `atlas/analysis/portfolio.py`.**

**Zero-caller audit result:**
- `CompanyPortfolioProfile`: zero active production callers after providers were updated. All remaining hits were tests, docstring comments, and stale strings.

**Changes:**
- `atlas/providers/base.py`: TYPE_CHECKING import changed from `CompanyPortfolioProfile` to `PortfolioFitInput`; return type annotation updated.
- `atlas/providers/mock.py`: import changed; `MOCK_COMPANY_PORTFOLIO_PROFILES` dict type and all 4 entries changed to `PortfolioFitInput`; `get_portfolio_profile` return type updated.
- `atlas/providers/yahoo.py`: import changed; `get_portfolio_profile` return type and constructor call changed to `PortfolioFitInput`.
- `atlas/adapters/portfolio.py`: `CompanyPortfolioProfile` import removed; `portfolio_fit_input_from_profile` changed to identity function (`PortfolioFitInput → PortfolioFitInput`) — retained to avoid touching 4 engine callers (Option A).
- `atlas/analysis/portfolio.py`: `CompanyPortfolioProfile` dataclass deleted. `portfolio.py` reduced from 69 to **59 lines** (2 active types: `Portfolio`, `PortfolioPosition` + 2 private helpers).
- `atlas/cli/deprecations.py`: stale string updated.
- 5 test files updated: stale "is importable" assertions flipped; `_profile()` fixture changed to return `PortfolioFitInput`; `isinstance(profile, PortfolioFitInput)` added to `test_providers.py`.
- Sprint 133 guardrail block added to `test_portfolio_analyze_deprecation.py` (4 new tests).
- 1352 tests passing (3 skipped). Demo passed. Release verification green.

**Result:** `atlas/analysis/portfolio.py` now contains only `Portfolio` and `PortfolioPosition` — the CLI JSON loading boundary. All portfolio intelligence types live in `atlas/capabilities/portfolio_intelligence/`.

---

## Sprint 133 (Original Target — now complete)

**Recommended Sprint 133 target: Migrate `CompanyPortfolioProfile` from providers to `PortfolioFitInput`.**

**Rationale:**
- `CompanyPortfolioProfile` is the last legacy result type in `portfolio.py` with active production callers.
- It is coupled to 3 provider files (`providers/base.py`, `providers/mock.py`, `providers/yahoo.py`) — coordinated change required.
- The Blueprint equivalent `PortfolioFitInput` already exists in `atlas/capabilities/portfolio_intelligence/`.
- The adapter `atlas/adapters/portfolio.py` already has `portfolio_fit_input_from_profile()` that converts `CompanyPortfolioProfile` → `PortfolioFitInput`.
- Migration requires: (1) update `CompanyDataProvider.get_portfolio_profile()` return type to `PortfolioFitInput`; (2) update `MockCompanyAnalysisProvider` and `YahooFinanceProvider` accordingly; (3) update `portfolio_fit_input_from_profile` in adapter (becomes identity or thinner); (4) remove `CompanyPortfolioProfile` from `portfolio.py` and `__init__.py`.
- After Sprint 133, only `Portfolio` and `PortfolioPosition` would remain in `portfolio.py` (CLI JSON loading boundary).

---

## Sprint 134 ✓ COMPLETE (Planning Sprint)

**Audited all remaining `Portfolio` and `PortfolioPosition` callers. Selected Sprint 135 target.**

### Sprint 134: Final portfolio.py state

`atlas/analysis/portfolio.py` — 67 lines, 2 public types, 2 private helpers:

```
Portfolio       — dataclass (frozen), positions: tuple[PortfolioPosition, ...],
                  classmethods: from_json_file(Path), from_mapping(dict)
PortfolioPosition — dataclass (frozen), 8 fields: ticker, company, sector, country,
                    market_cap, weight, quality_score, risk_score
_position_from_mapping(payload) -> PortfolioPosition   — supports Portfolio.from_mapping
_normalize_weight(weight) -> float                      — supports _position_from_mapping
```

### Sprint 134: `Portfolio` caller map (complete)

| File | Import style | Runtime/Annotation | Access pattern | CLI path |
|---|---|---|---|---|
| `atlas/cli/main.py` | `from atlas.analysis.portfolio import Portfolio` | **RUNTIME** — 9 call sites | `Portfolio.from_json_file(path)` | All portfolio CLI commands |
| `atlas/portfolio_review/engine.py` | `import Portfolio as LegacyPortfolio` | **RUNTIME** — struct field | `PortfolioReviewInput.portfolio: LegacyPortfolio` | `atlas portfolio review` |
| `atlas/adapters/portfolio.py` | `import Portfolio as LegacyPortfolio` | **RUNTIME** — conversion input | `legacy_portfolio_to_domain_portfolio(LegacyPortfolio) -> atlas.shared.Portfolio` | All adapter flows |
| `atlas/analysis/__init__.py` | re-export | Re-export | — | Public API |
| `atlas/conversation/engine.py` | `TYPE_CHECKING` | Annotation only | `portfolio: Portfolio \| None` — passed to adapter | `atlas ask` |
| `atlas/dashboard/engine.py` | `TYPE_CHECKING` | Annotation + `.positions` | `portfolio: Portfolio \| None`; accesses `.positions` (line 224) | `atlas dashboard show` |
| `atlas/decision/decision_context.py` | `TYPE_CHECKING` | Annotation only | `portfolio: Portfolio \| None` — passed through | `atlas decide` |
| `atlas/home/engine.py` | `TYPE_CHECKING` | Annotation only | `portfolio: Portfolio \| None` — passed to `PortfolioReviewInput` | `atlas home` |
| `atlas/intelligence/engine.py` | `TYPE_CHECKING` | Annotation only | `portfolio: Portfolio \| None` — passed to adapter | `atlas intelligence` |
| `atlas/monitoring/engine.py` | `TYPE_CHECKING` | Annotation + `.positions` | `portfolio: Portfolio \| None`; accesses `.positions` (lines 229-239) | `atlas monitor` |
| `atlas/risk_drift/engine.py` | `TYPE_CHECKING` | Annotation + `.positions` | `current_portfolio: Portfolio \| None`; accesses `.positions` (line 590) | `atlas risk-drift` |
| `atlas/suitability/engine.py` | `TYPE_CHECKING` | Annotation + `.positions` | `portfolio: Portfolio \| None`; accesses `.positions` (lines 594-611) | `atlas decide` |

**Total `atlas.analysis.portfolio` production import sites: 12** (3 runtime + 1 re-export + 8 annotation)

### Sprint 134: `PortfolioPosition` caller map (complete)

`PortfolioPosition` has **zero production runtime callers outside `atlas/analysis/portfolio.py`**.

- Constructed only by `_position_from_mapping()` inside `portfolio.py`.
- All `PortfolioPosition(...)` calls in codebase are test fixtures.
- `PortfolioPosition` is effectively internal to `Portfolio` — it cannot be migrated independently.

### Sprint 134: Private helper review

| Helper | Purpose | Called by | Move with Portfolio? |
|---|---|---|---|
| `_position_from_mapping(payload: dict)` | Parses one position dict → `PortfolioPosition` | `Portfolio.from_mapping()` | Yes — tightly coupled |
| `_normalize_weight(weight: float)` | Normalizes weight (÷100 if >1, clamp 0–1) | `_position_from_mapping` | Yes — tightly coupled |

Both helpers are required by `Portfolio.from_mapping` / `from_json_file`. They must move alongside `Portfolio` and `PortfolioPosition`.

### Sprint 134: Destination review

| Candidate | Verdict | Reason |
|---|---|---|
| `atlas.shared.Portfolio` | **Not a destination** — field mismatch | `atlas.shared.Portfolio` uses `.holdings: tuple[Holding, ...]` not `.positions`; no JSON loading methods; different schema. Cannot replace `LegacyPortfolio` directly. |
| `atlas.shared.Holding` | **Not a destination** for `PortfolioPosition` | Schema partially compatible (field names align) but `Holding` has extra required fields (`company_id`, etc.) and `quality_score`/`risk_score` are `int \| None` vs `int`. Not a drop-in. |
| `atlas/domains/portfolio/` | **Not a destination** | Domain layer is for business logic types; JSON loading does not belong here. |
| **`atlas/adapters/portfolio.py`** | **✓ RECOMMENDED destination** | Adapter is already the legacy compatibility boundary. Already imports `LegacyPortfolio`. Making it self-contained is the lowest-risk move. Adapters are designed to hold legacy types during migration. |

### Sprint 134: Sprint 135 target — recommended

**"Lift and shift" — Move `Portfolio`, `PortfolioPosition`, `_position_from_mapping`, and `_normalize_weight` from `atlas/analysis/portfolio.py` into `atlas/adapters/portfolio.py`. Update all callers in the same sprint. Delete `atlas/analysis/portfolio.py`.**

**Rationale for single-sprint completion:**
- All 12 production import sites are known (audited Sprint 134).
- All changes are mechanical: one import-line update per file, no behavior change.
- Splitting into two sprints (move + shim, then delete shim) adds a dead-code shim that needs its own guardrail tests and a second round of review.
- The adapter becomes self-contained — no more dependency on `atlas.analysis.portfolio`.

**Estimated Sprint 135 file changes:**

| File | Change | Risk |
|---|---|---|
| `atlas/adapters/portfolio.py` | Inline `Portfolio`, `PortfolioPosition`, helpers; remove `from atlas.analysis.portfolio import` | Medium — careful to preserve adapter behavior |
| `atlas/analysis/portfolio.py` | **Delete** | Zero risk after all callers updated |
| `atlas/analysis/__init__.py` | Remove `Portfolio`, `PortfolioPosition` re-exports | Low |
| `atlas/cli/main.py` | Import from `atlas.adapters.portfolio` | Low |
| `atlas/portfolio_review/engine.py` | Import from `atlas.adapters.portfolio` | Low |
| `atlas/conversation/engine.py` | Update TYPE_CHECKING import | Low |
| `atlas/dashboard/engine.py` | Update TYPE_CHECKING import | Low |
| `atlas/decision/decision_context.py` | Update TYPE_CHECKING import | Low |
| `atlas/home/engine.py` | Update TYPE_CHECKING import | Low |
| `atlas/intelligence/engine.py` | Update TYPE_CHECKING import | Low |
| `atlas/monitoring/engine.py` | Update TYPE_CHECKING import | Low |
| `atlas/risk_drift/engine.py` | Update TYPE_CHECKING import | Low |
| `atlas/suitability/engine.py` | Update TYPE_CHECKING import | Low |
| ~15 test files | Update imports | Low |

**Deletion criteria for `atlas/analysis/portfolio.py`:** zero import sites anywhere in codebase (excluding `__pycache__`).

---

## Why Not Migrate Now

(Historical context from earlier sprints — resolved by Sprint 134 planning)

1. **No Blueprint replacement for `PortfolioIntelligenceEngine`.** ✓ Resolved Sprint 128 — engine deleted.

2. **Schema gap: `quality_score`/`risk_score` missing from `atlas.shared.Holding`.**
   `atlas.shared.Holding` now carries `quality_score: int | None` and `risk_score: int | None`. The gap is bridged in the adapter.

3. **Provider contract coupling.** ✓ Resolved Sprint 133 — providers now return `PortfolioFitInput` directly.

4. **Active import sites.** Now 12 (down from 17). All remaining callers audited and mapped above.

5. **Existing deprecation guardrail.** `test_portfolio_analyze_deprecation.py` asserts that known callers still import from `atlas.analysis.portfolio`. Sprint 135 must update these guardrails in sync with the migration.

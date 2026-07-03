# Atlas Portfolio Intelligence Capability Cleanup Plan

**Created:** 2026-07-03 (Sprint 170)  
**Status:** ACTIVE — Sprint 170 audit-first inventory. No cleanup action identified yet.

---

## Background

The Sprint 170 target was described as `atlas/portfolio_intelligence/`. Repository reality reveals:

- **`atlas/portfolio_intelligence/` does NOT exist as a top-level package.** The legacy `PortfolioIntelligenceEngine` was deleted in Sprint 128, and `atlas.analysis.portfolio` was deleted in Sprint 135.
- The active Blueprint-aligned surface is `atlas/capabilities/portfolio_intelligence/` — a 3-module capability package with a clean architecture.
- A related but distinct domain lives at `atlas/domains/portfolio/` — portfolio structure, holdings, validation, and review. That is a separate domain package and is NOT part of this audit.

This audit focuses on `atlas/capabilities/portfolio_intelligence/`.

---

## `atlas/capabilities/portfolio_intelligence/` Package Inventory (Sprint 170 state)

**3 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 22 | Re-export hub — 4 exports |
| `engine.py` | 357 | Core capability engine + 10 private dimension calculators + 4 internal helpers |
| `models.py` | 93 | Blueprint-aligned frozen dataclasses — 3 types |

---

## `models.py` — Public Types

| Symbol | Kind | Description | Status |
|---|---|---|---|
| `PortfolioFitDimension` | frozen dataclass | Single scored dimension with neutral `note` field | **Active — used in all 7 dimensions of PortfolioFitResult** |
| `PortfolioFitInput` | frozen dataclass | Input type for portfolio fit analysis (replaces legacy `CompanyPortfolioProfile`) | **Active — used by 5 production callers + providers** |
| `PortfolioFitResult` | frozen dataclass | Output of portfolio fit analysis (replaces legacy `PortfolioAnalysis`) | **Active — consumed by decision, intelligence, conversation, dashboard, risk_drift, suitability** |

**Stale comment note:** `models.py:42–44` contains a "Future expansion" note referencing `themes` and `knowledge_context` fields for `PortfolioFitInput` that were never added. This is documentation metadata only — no runtime impact. Cleanup candidate for Sprint 171.

---

## `engine.py` — `PortfolioIntelligenceCapability` Review

| Detail | Value |
|---|---|
| Source file | `atlas/capabilities/portfolio_intelligence/engine.py:42` |
| Public methods | `.analyze(portfolio: Portfolio, fit_input: PortfolioFitInput, target_weight: float = 0.05) → PortfolioFitResult` |
| Constructor dependencies | None — stateless; `__init__` not defined (Python default) |
| Provider dependencies | **None** — no provider import anywhere in the package |
| Network calls | **None** — deterministic local calculation only |
| Production callers | 5 packages (decision, intelligence, conversation, dashboard, and providers — see Caller Map) |
| Test callers | `tests/test_portfolio_intelligence_capability.py` (162 lines, Sprint 113/114 coverage) |
| CLI callers | Indirect only — CLI calls decision/intelligence/conversation/dashboard engines which instantiate `PortfolioIntelligenceCapability` |
| Returns Blueprint-aligned data? | Yes — `PortfolioFitResult` is a Blueprint-aligned type |
| Zero-caller public methods | None — `.analyze()` is the sole public method and is active |
| Stale compatibility logic | None — engine was purpose-built as Blueprint replacement for deleted `PortfolioIntelligenceEngine` |

### Private Helpers (all active)

| Helper | Purpose | Caller |
|---|---|---|
| `_diversification_impact` | 3-factor diversification score | `.analyze()` |
| `_sector_concentration` | Pro forma sector concentration score | `.analyze()` |
| `_country_concentration` | Pro forma country concentration score | `.analyze()` |
| `_market_cap_concentration` | Pro forma mega-cap concentration score | `.analyze()` |
| `_overlap_with_existing_holdings` | Ticker/sector overlap detection | `.analyze()` |
| `_quality_impact` | Portfolio quality delta (with fallback when holdings lack enrichment) | `.analyze()` |
| `_risk_impact` | Portfolio risk delta (with fallback when holdings lack enrichment) | `.analyze()` |
| `_aggregate_fit_score` | Weighted 7-dimension aggregate | `.analyze()` |
| `_build_summary` | Neutral-framed fit score summary string | `.analyze()` |
| `_weight_by_attribute` | Weight lookup across holdings by attribute | `_diversification_impact`, `_sector_concentration`, `_country_concentration` |
| `_mega_cap_weight` | Portfolio mega-cap weight sum | `_diversification_impact`, `_market_cap_concentration` |
| `_weighted_average_optional` | Weighted average from enriched holdings | `_quality_impact`, `_risk_impact` |
| `_pro_forma_average` | Pro forma average after target added | `_quality_impact`, `_risk_impact` |
| `_concentration_score` | Penalized concentration scoring | `_sector_concentration`, `_country_concentration`, `_market_cap_concentration` |
| `_normalize_weight` | Normalizes target_weight (handles 0–1 and 0–100 range) | `.analyze()` |
| `_is_mega_cap` | Market cap >= $500B threshold | `_mega_cap_weight`, `_market_cap_concentration` |
| `_clamp` | Clamps score to 0–100 | All dimension calculators |

**Zero zero-caller private helpers found.**

---

## Export Review (`__init__.py`)

4 exports. All active.

| Export | Active? | Direct external callers |
|---|---|---|
| `PortfolioFitDimension` | ✓ (sub-type) | `test_portfolio_intelligence_capability.py`; accessed via `PortfolioFitResult` fields in production |
| `PortfolioFitInput` | ✓ | `atlas/providers/base.py`, `atlas/providers/mock.py`, `atlas/providers/yahoo.py`, `atlas/decision/decision_engine.py`, `atlas/intelligence/engine.py`, `atlas/conversation/engine.py`, tests |
| `PortfolioFitResult` | ✓ | `atlas/decision/`, `atlas/intelligence/`, `atlas/conversation/`, `atlas/dashboard/`, `atlas/risk_drift/`, `atlas/suitability/`, tests |
| `PortfolioIntelligenceCapability` | ✓ | `atlas/decision/decision_engine.py`, `atlas/intelligence/engine.py`, `atlas/conversation/engine.py`, `atlas/dashboard/engine.py`, tests |

**Finding:** All 4 exports are active. No stale exports.

---

## Production Caller Map

**5 production call sites for `PortfolioIntelligenceCapability.analyze()`:**

| Caller package | Import | Role |
|---|---|---|
| `atlas/decision/decision_engine.py` | `PortfolioIntelligenceCapability`, `PortfolioFitResult` (runtime) | Portfolio fit for decision scoring — 7 dimension scores, fit_score, concentration discussion |
| `atlas/intelligence/engine.py` | `PortfolioIntelligenceCapability` (runtime), `PortfolioFitResult` (TYPE_CHECKING) | Portfolio fit for intelligence analysis — 7 dimension notes, portfolio_impact output tuple |
| `atlas/conversation/engine.py` | `PortfolioIntelligenceCapability` (runtime) | Portfolio review intent branch — direct portfolio fit response |
| `atlas/dashboard/engine.py` | `PortfolioIntelligenceCapability` (runtime) | Portfolio section of dashboard — fit_score shown when target_ticker provided |
| `atlas/providers/base.py`, `mock.py`, `yahoo.py` | `PortfolioFitInput` | Provider contract — `get_portfolio_profile(ticker) → PortfolioFitInput` |

**Type-only callers (no runtime instantiation):**

| Caller | Symbol | Mode |
|---|---|---|
| `atlas/decision/decision_result.py` | `PortfolioFitResult` | TYPE_CHECKING only |
| `atlas/risk_drift/engine.py` | `PortfolioFitResult` | Runtime — `current_portfolio_analysis: PortfolioFitResult | None` field |
| `atlas/suitability/engine.py` | `PortfolioFitResult` | Runtime — `portfolio_analysis: PortfolioFitResult | None` field |

---

## CLI / Entrypoint Review

Portfolio intelligence is accessed via 4 CLI commands, all indirect:

| Command | Path | Portfolio intelligence role |
|---|---|---|
| `atlas decide` | `atlas/cli/main.py` → `decision_engine.py` | Full 7-dimension portfolio fit when `--portfolio` and `--ticker` provided |
| `atlas intelligence analyze` | `atlas/cli/main.py` → `intelligence/engine.py` | Optional portfolio fit when `--portfolio` and `--ticker` provided |
| `atlas ask` | `atlas/cli/main.py` → `conversation/engine.py` | Portfolio review intent path when `--portfolio` and `--ticker` provided |
| `atlas dashboard show` | `atlas/cli/main.py` → `dashboard/engine.py` | Portfolio section fit score when `--portfolio` and `--ticker` provided |

All 4 commands use `--portfolio` + `--ticker` together to activate portfolio intelligence. Without both flags, `PortfolioIntelligenceCapability.analyze()` is not called.

---

## Capability / Domain Boundary Review

| Dependency | Import location | Mode | Direction acceptable? | Stable? |
|---|---|---|---|---|
| `atlas.capabilities.portfolio_intelligence.models` | `engine.py` | Runtime — imports own sibling | ✓ internal | ✓ |
| `atlas.shared.entities` (Holding, Portfolio) | `engine.py` | Runtime — canonical entity types | ✓ correct: shared layer ← capability | ✓ |

**External dependencies of the capability itself:** exactly 2 — its own models module and `atlas.shared.entities`. This is the minimum possible dependency surface for a capability.

**Dependency direction:** `atlas/capabilities/portfolio_intelligence/` consumes only `atlas.shared` (entity types). It does NOT import from domains, adapters, providers, or any other runtime layer. This is exemplary Blueprint-aligned architecture.

**No circular dependencies.**

---

## Provider Boundary Review

| Check | Result |
|---|---|
| `YahooFinanceProvider` in `atlas/capabilities/portfolio_intelligence/` | **Absent** ✓ |
| `MockCompanyAnalysisProvider` in `atlas/capabilities/portfolio_intelligence/` | **Absent** ✓ |
| `CompanyDataProvider` in `atlas/capabilities/portfolio_intelligence/` | **Absent** ✓ |
| Direct network calls | **None** ✓ |
| Provider usage | Providers consume `PortfolioFitInput` (they supply it); capability does not instantiate or call providers |
| Network behavior | Capability is fully deterministic and local-only |

The relationship is correct: **providers supply `PortfolioFitInput` → CLI passes to engines → engines pass to capability**. The dependency flows toward the capability, not outward. The capability knows nothing about providers.

---

## Stale Import Audit (repo-wide, portfolio intelligence focus)

| Symbol | In `atlas/capabilities/portfolio_intelligence/`? | Elsewhere (classified) |
|---|---|---|
| `atlas.reasoning` / deleted reasoning symbols | **None** ✓ | Test guardrails, docs |
| `PortfolioIntelligenceEngine` (deleted Sprint 128) | **None** ✓ | Test guardrails asserting absence (Sprint 128 + later); docstring note in engine.py confirming non-wrapping |
| `portfolio_fit_input_from_profile` (deleted Sprint 135) | **None** ✓ | Test guardrails asserting absence |
| `atlas.analysis.portfolio` (deleted Sprint 135) | **None** — docstring reference only: "__init__.py" | Test guardrails asserting deletion |
| `PortfolioAnalysis` / `CompanyPortfolioProfile` | Docstring cross-references in models.py only | Historical migration notes — not imports |
| `PortfolioRecommendation` | Docstring only (models.py:80 — intentionally omitted field) | Not an import |
| `YahooCompany` / `YahooFinancials` / `YahooMarketData` | **None** ✓ | Historical docs only |

**No stale production imports in `atlas/capabilities/portfolio_intelligence/`.**

The docstring references to legacy types (`PortfolioAnalysis`, `CompanyPortfolioProfile`) in `models.py` are historical migration documentation — they record the field mapping from the deleted legacy type. These are comments, not imports.

---

## Blueprint Overlap Review

| Comparison | Overlap with `atlas/capabilities/portfolio_intelligence/`? |
|---|---|
| `atlas/domains/portfolio/` | Complementary, not overlapping. `domains/portfolio/` owns portfolio structure, validation, and review (PortfolioDomainReview, PortfolioSnapshot, etc.). `capabilities/portfolio_intelligence/` owns company-specific fit analysis against a portfolio. Different scope, different output types. |
| `atlas/capabilities/company_analysis/` | Different scope — company analysis assesses a company standalone; portfolio intelligence assesses fit against an existing portfolio. Not redundant. |
| `atlas/capabilities/daily_brief/` | Consumes outputs from portfolio intelligence indirectly; does not overlap. |
| `atlas/analysis/portfolio` (deleted) | Migration target — completed Sprint 135. Capability IS the Blueprint-aligned successor. Migration is complete. |
| `atlas/intelligence/` | Consumer, not overlapping. |
| `atlas/decision/` | Consumer, not overlapping. |

**Conclusion:** `atlas/capabilities/portfolio_intelligence/` is the settled Blueprint-aligned successor to the deleted `atlas.analysis.portfolio` and `PortfolioIntelligenceEngine`. No further migration is needed. No successor exists or is warranted.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Risk | Sprint 171? |
|---|---|---|---|
| Stale "Future expansion" note in `models.py:42–44` (`themes`, `knowledge_context`) | Fields never added; note references features that were not implemented as of Sprint 170 | LOW — docstring only, no runtime impact | Optional — remove or mark resolved |
| Historical field-mapping docstrings in `models.py` (`CompanyPortfolioProfile →`, `PortfolioAnalysis →`) | Migration documentation for a completed migration (Sprint 135). Future readers may be confused by references to deleted types. | LOW — docstring only | Optional — remove or condense |
| `__init__.py` docstring references to `atlas.analysis.portfolio` | Historically accurate; migration complete | LOW — docstring only | Optional |

**No runtime cleanup candidates.** No dead code. No zero-caller symbols. No stale exports. No provider boundary issues. No circular dependencies. No runtime coupling issues. The package is architecturally sound.

---

## Final Stable Package State (Sprint 170)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 22 | 4 exports — all active; docstring references to completed migration |
| `engine.py` | 357 | Active — `PortfolioIntelligenceCapability` Blueprint capability with minimum dependency surface |
| `models.py` | 93 | Active — 3 Blueprint-aligned frozen dataclasses; stale "future expansion" note in `PortfolioFitInput` docstring |

**Provider safety:** No provider imports. No network calls. Fully deterministic and local-only. Provider selection lives entirely at the CLI layer. ✓

**Architecture health:** Exemplary Blueprint-aligned capability. Depends only on `atlas.shared`. Consumed by 5 production packages. No deleted-module imports. No circular dependencies. Clean and stable.

---

## Recommended Sprint 171 Target

**Close the `atlas/capabilities/portfolio_intelligence/` cleanup track — documentation-only sprint.**

Sprint 170 audit found no runtime cleanup warranted. The package is clean, well-bounded, and architecturally exemplary. Sprint 171 should:

1. Optionally remove the stale "Future expansion" note from `models.py` (3 lines) — the fields were never added and the note is misleading
2. Optionally condense historical field-mapping docstrings in `models.py` (migration is complete)
3. Update docs to reflect the closed track
4. Run tests and RC verification

If the docstring cleanup is considered too minor to warrant a full sprint, Sprint 171 could instead target the next most valuable audit: `atlas/capabilities/company_analysis/` or `atlas/domains/portfolio/`.

**Primary recommendation:** Sprint 171 = Close `atlas/capabilities/portfolio_intelligence/` cleanup track (docstring cleanup + track closure). This closes a 14th track cleanly.

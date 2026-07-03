# Suitability Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 205)  
**Status:** OPEN — audit complete. No cleanup warranted. Sprint 206 target: close suitability cleanup track.

---

## Important Framing

Sprint 205 audits `atlas/suitability/` following the RC checkpoint confirming 24 closed cleanup tracks (Sprint 204). `atlas/suitability/` is active, CLI-exposed, and had not previously received a focused cleanup audit.

This sprint uses repository reality. No files were deleted or changed.

---

## Package Surface

`atlas/suitability/` contains exactly 2 modules and 642 total lines.

### `atlas/suitability/__init__.py` (19 lines)

Direct re-export of 7 symbols from `atlas.suitability.engine`:

```python
__all__ = [
    "OverallSuitability",
    "SuitabilityAssessment",
    "SuitabilityEngine",
    "SuitabilityFactor",
    "SuitabilityInput",
    "SuitabilityMismatch",
    "render_suitability_assessment",
]
```

No lazy shim — direct imports at module load time. All 7 symbols are active with production callers.

### `atlas/suitability/engine.py` (623 lines)

Single-file implementation. All logic is deterministic, local-only, provider-optional at the CLI level.

**Public symbols:**

| Symbol | Kind | Lines | Active | Description |
|---|---|---|---|---|
| `OverallSuitability` | `str, Enum` | 4 values | Yes | `EXCELLENT_FIT`, `GOOD_FIT`, `NEUTRAL`, `POOR_FIT` |
| `SuitabilityFactor` | frozen dataclass | 3 fields | Yes | Named positive fit factor with score + reasoning |
| `SuitabilityMismatch` | frozen dataclass | 3 fields | Yes | Named concern/conflict with severity + reasoning |
| `SuitabilityInput` | frozen dataclass | 16 fields | Yes | All inputs for suitability assessment; all optional except `investor_profile` |
| `SuitabilityAssessment` | frozen dataclass | 11 fields | Yes | Output of `SuitabilityEngine.assess()` |
| `SuitabilityEngine` | class | 1 method | Yes | `.assess(SuitabilityInput) -> SuitabilityAssessment` |
| `render_suitability_assessment` | function | ~45 lines | Yes | Renders `SuitabilityAssessment` to human-readable string |

**Private helpers (meaningful, not stale):**

| Helper | Purpose |
|---|---|
| `_derive_characteristics` | Extracts volatility, quality, valuation sensitivity, concentration, cyclicality, leverage, exposure from input |
| `_fit_factors` | Builds positive fit factors from profile + characteristics |
| `_mismatches` | Builds conflict/mismatch list from profile + characteristics |
| `_suitability_score` | `base(55) + factor_lift - mismatch_penalty` → `clamp_score` |
| `_overall_suitability` | Maps score → `OverallSuitability` enum (≥82 Excellent, ≥68 Good, ≥50 Neutral) |
| `_confidence` | Confidence 55 + presence bonuses − missing info penalties → `clamp_score` |
| `_missing_information` | Documents what Atlas lacks to improve confidence |
| `_assumptions` | Summarises what Atlas assumed in the absence of explicit data |
| `_questions` | Returns clarifying questions to increase confidence |
| `_compatibility_language` | Neutral descriptive phrase for overall suitability |
| `_volatility_from_risk`, `_valuation_sensitivity`, `_concentration_impact`, `_cyclicality`, `_leverage`, `_sector_exposure`, `_geographic_exposure` | Derive characteristics from available data |
| `_style_from_profile`, `_accepts_volatility`, `_is_exploration_or_high_conviction`, `_is_higher_risk`, `_capital_preservation_profile` | Profile classification helpers |
| `_severity_penalty` | High=24, Medium=14, Low=8 score penalties |
| `_weighted_average`, `_max_weight`, `_top_exposure` | Portfolio math utilities |
| `_render_list` | Formats `tuple[str, ...]` to bullet list |

No private helpers are stale or unreachable. All are called by `_fit_factors`, `_mismatches`, `_suitability_score`, `_derive_characteristics`, or `render_suitability_assessment`.

---

## Export Review

| Symbol | Source | In `__all__` | Active | Stale |
|---|---|---|---|---|
| `OverallSuitability` | `engine.py` | Yes | Yes | No |
| `SuitabilityAssessment` | `engine.py` | Yes | Yes | No |
| `SuitabilityEngine` | `engine.py` | Yes | Yes | No |
| `SuitabilityFactor` | `engine.py` | Yes | Yes | No |
| `SuitabilityInput` | `engine.py` | Yes | Yes | No |
| `SuitabilityMismatch` | `engine.py` | Yes | Yes | No |
| `render_suitability_assessment` | `engine.py` | Yes | Yes | No |

All 7 exports are active. No stale exports. No export removal warranted.

---

## Caller Map

### Production callers

| File | Symbols used | Classification |
|---|---|---|
| `atlas/cli/main.py` | `SuitabilityAssessment`, `SuitabilityEngine`, `SuitabilityInput`, `render_suitability_assessment` | Active CLI caller |
| `atlas/dashboard/engine.py` | `SuitabilityEngine`, `SuitabilityInput` | Active application caller |
| `atlas/comparison/engine.py` | `SuitabilityEngine`, `SuitabilityInput` | Active application caller |
| `atlas/watchlist_review/engine.py` | `SuitabilityEngine`, `SuitabilityInput` | Active application caller |
| `atlas/portfolio_review/engine.py` | `SuitabilityEngine`, `SuitabilityInput` | Active application caller |
| `atlas/risk_drift/engine.py` | `OverallSuitability`, `SuitabilityAssessment` | Active application caller |

### Test callers

| File | Symbols used | Classification |
|---|---|---|
| `tests/test_suitability_engine.py` | `SuitabilityAssessment`, `SuitabilityEngine`, `SuitabilityInput`, `render_suitability_assessment` | Test caller |

### Test guardrail references (retired symbol guards — not active runtime)

Multiple test files assert `check_suitability_assessment` is absent from `atlas.principles` (Sprint 157 guard). These are guardrail tests, not suitability callers:

- `tests/test_principles_package_sprint156.py` — asserts `check_suitability_assessment` absent from `atlas.principles`
- `tests/test_intelligence_package_sprint164.py`, `test_comparison_package_sprint159.py`, `test_portfolio_intelligence_capability_sprint170.py`, `test_conversation_package_sprint166.py`, `test_dashboard_package_sprint168.py`, `test_home_package_sprint161.py`, `test_rc_checkpoint_sprint163.py` — each asserts retired symbols absent from their respective package

Classification: **expected test guardrails — retired command records, never executed.** `check_suitability_assessment` does not appear as an active runtime export of `atlas.suitability`. ✓

### Zero callers

None. All 7 public symbols have at least one active production or CLI caller.

---

## CLI Suitability Review

### Registration

`atlas/cli/main.py` registers:

```python
suitability_app = typer.Typer(help="Investor suitability context commands")
app.add_typer(suitability_app, name="suitability")
```

### Active commands

| Command | Function | Arguments | Status |
|---|---|---|---|
| `atlas suitability analyze` | `suitability_analyze_command` | `subject` (positional), `--profile`, `--provider`, `--theme` | Active ✓ |

`atlas suitability --help` confirms one command: `analyze — Assess profile compatibility for a ticker or portfolio JSON file.`

### `_build_suitability_assessment` helper (CLI-private)

`atlas/cli/main.py:1385` — private helper that:
1. If `subject` ends in `.json`: loads a `Portfolio` from JSON, calls `SuitabilityEngine().assess(SuitabilityInput(investor_profile=profile, portfolio=portfolio))`
2. Otherwise: treats `subject` as ticker, calls `provider.get_company_analysis(ticker)` → `build_investment_report()`, creates `ThemeEngine().analyze()` and `IntelligenceEngine().analyze()`, then `SuitabilityEngine().assess(SuitabilityInput(...))`

Provider usage is via CLI `--provider` flag (defaults to `"mock"`). Mock provider makes no network calls. This is the established opt-in provider pattern.

### Output language

`render_suitability_assessment` emits:
- `"Suitability Assessment"` header
- `"Overall Suitability: Excellent Fit / Good Fit / Neutral / Poor Fit"`
- `"Compatibility View"` with one of three neutral phrases
- `"Why It Fits"` / `"Why It May Not Fit"` — deterministic reasoning only
- `"Research Framing: This evaluates profile compatibility only. It does not judge investment merit or provide personalized financial advice."`

No forbidden language. Output is explicitly framed as compatibility evaluation, not investment advice. ✓

---

## Suitability Behavior Review

**Input:** `SuitabilityInput` — 16 fields, only `investor_profile` is required. All others are optional and enrich the assessment when provided.

**Process:** deterministic, local-only:
1. `_derive_characteristics` → extracts volatility, quality, valuation, concentration, cyclicality, leverage, exposure from any combination of: `InvestmentReport`, `Portfolio`, `PortfolioFitResult`, `ThemeAnalysis`, or inline field overrides
2. `_fit_factors` → builds positive factors from profile × characteristics
3. `_mismatches` → builds conflicts from profile × characteristics
4. `_suitability_score` → `clamp_score(55 + factor_lift - mismatch_penalty)`
5. `_overall_suitability` → enum label based on score thresholds
6. `_confidence` → `clamp_score(55 + presence_bonuses - missing_penalty)`
7. Returns `SuitabilityAssessment` (frozen dataclass)

**Behavior properties:**
- Deterministic ✓
- Local-only (no network calls) ✓
- Provider-optional (CLI opt-in only) ✓
- Output is framed as "profile compatibility" not "investment advice" ✓
- No forbidden recommendation language ✓
- Evidence-aligned (uses risk score, quality score, financial strength from `InvestmentReport`) ✓
- Risk-aligned (uses `RiskCapacity`, `RiskTolerance`, `RiskPreference` from `InvestorProfile`) ✓
- Principles-aligned (no advice/recommendation output) ✓

---

## Boundary Review

### Imports into `atlas/suitability/engine.py`

| Import | Source | Direction | Classification |
|---|---|---|---|
| `InvestmentReport` | `atlas.analysis.engine` | analysis → suitability | Correct — uses analysis output as input ✓ |
| `clamp_score` | `atlas.analysis.scores` | analysis → suitability | Correct — shared utility ✓ |
| `PortfolioFitResult` | `atlas.capabilities.portfolio_intelligence` | capability → suitability | Correct — uses capability output as input ✓ |
| `Portfolio` | `atlas.adapters.portfolio` (TYPE_CHECKING only) | adapter → suitability (type annotation only) | Correct — no runtime dep ✓ |
| `IntelligenceReport` | `atlas.intelligence` | intelligence → suitability | Correct — uses intelligence output as input ✓ |
| `InvestorProfile`, `InvestmentGoal`, `PortfolioPurpose`, `RiskCapacity`, `RiskPreference`, `RiskTolerance`, `TimeHorizon` | `atlas.profile` | profile → suitability | Correct — suitability evaluates profiles ✓ |
| `ThemeAnalysis` | `atlas.themes` | themes → suitability | Correct — uses theme context ✓ |

### Imports from suitability (callers)

| File | Direction | Classification |
|---|---|---|
| `atlas/cli/main.py` | CLI → suitability | Correct ✓ |
| `atlas/dashboard/engine.py` | application → suitability | Correct ✓ |
| `atlas/comparison/engine.py` | application → suitability | Correct ✓ |
| `atlas/watchlist_review/engine.py` | application → suitability | Correct ✓ |
| `atlas/portfolio_review/engine.py` | application → suitability | Correct ✓ |
| `atlas/risk_drift/engine.py` | application → suitability | Correct ✓ |

### Boundary verdict

| Direction | Status |
|---|---|
| `atlas/suitability/` imports `atlas/cli/` | No — no upward CLI dependency ✓ |
| `atlas/suitability/` imports `atlas/providers/` | No — no provider coupling ✓ |
| `atlas/suitability/` imports `atlas/database/services/models/` | No — no persistence coupling ✓ |
| `atlas/suitability/` imports `atlas/decision/` | No ✓ |
| Circular dependencies | None ✓ |
| Boundary direction | Acceptable — suitability is a mid-layer engine consuming analysis, intelligence, capabilities, and profile inputs ✓ |

---

## Provider Boundary Review

Zero hits for `atlas.providers`, `CompanyDataProvider`, `MockCompanyAnalysisProvider`, `YahooFinanceProvider`, `requests`, `http`, `urlopen`, or `.fetch` in `atlas/suitability/`.

- `atlas/suitability/` is **fully provider-free** ✓
- Provider access occurs only at the CLI layer (`atlas/cli/main.py`) via opt-in `--provider` flag
- Mock provider is the default — no network calls
- `atlas/cli/main.py` passes a `CompanyDataProvider` to `_build_suitability_assessment` — this is the established CLI opt-in pattern, not a suitability-layer concern

---

## Recommendation-Language / Financial Advice Guardrail Review

Sole hit in `atlas/suitability/engine.py:147`:

```python
"This evaluates profile compatibility only. It does not judge investment "
"merit or provide personalized financial advice."
```

This is the explicit **anti-advice disclaimer** in `render_suitability_assessment`. It is a guardrail, not forbidden output. ✓

No `buy`, `sell`, `strong buy`, `price target`, `target price`, `urgent`, `recommend`, `should buy`, `should sell` in any suitability module. All output language describes compatibility, fitness, and alignment — not advice.

**Financial advice guardrail: CLEAN** ✓

---

## Closed Track / Deleted Module Guard

Full stale reference audit in `atlas/suitability/`:

| Search term | Found | Classification |
|---|---|---|
| `atlas.reasoning` / `ReasoningInput` / `ReasoningReport` / `render_reasoning_report` / `check_reasoning_report` | No | ✓ |
| `check_intelligence_report` / `check_suitability_assessment` | No | ✓ |
| `atlas.analysis.portfolio` / `PortfolioAnalysis` / `PortfolioSignal` / `PortfolioRecommendation` | No | ✓ |
| `CompanyPortfolioProfile` / `PortfolioIntelligenceEngine` / `portfolio_fit_input_from_profile` | No | ✓ |
| `CompanyAnalysisProvider` (standalone) | No | ✓ |
| `atlas.analysis.comparison/memory/scoring/watchlist/growth/macro/moat/quality/sentiment/technicals/valuation` | No | ✓ |
| `render_comparison_result` | No | ✓ |
| `YahooCompany` / `YahooFinancials` / `YahooMarketData` | No | ✓ |
| `InvestmentReport` from `atlas.models.investment_report` | No — imported from `atlas.analysis.engine` (active) | ✓ |
| `atlas.models.investment_report` | No | ✓ |
| `atlas.reports` / `atlas.storage` | No | ✓ |

**No stale active references.** `check_suitability_assessment` appears only in test guardrail files asserting its absence from `atlas.principles` (Sprint 157 removal guard) — never in active `atlas/suitability/` code. ✓

---

## Overlap Review

| Package | Overlap with suitability? | Classification |
|---|---|---|
| `atlas/decision/` | No — decision uses suitability output (`SuitabilityAssessment`) as input context, but does not duplicate suitability logic | Distinct — correct ✓ |
| `atlas/risk/` | No — `atlas/risk/` assesses risk dimensions; suitability uses risk score as one input characteristic | Complementary — correct ✓ |
| `atlas/principles/` | No — `atlas/principles/` validates investment principles; `check_suitability_assessment` was removed Sprint 157; no remaining overlap | Clean separation ✓ |
| `atlas/evidence/` | No — evidence assessment is distinct from suitability assessment | No overlap ✓ |
| `atlas/analysis/` | No — `atlas/suitability/` consumes `InvestmentReport` from analysis as an optional input; does not duplicate analysis logic | Correct consumer ✓ |
| `atlas/capabilities/` | No — consumes `PortfolioFitResult` as optional input; does not duplicate capability logic | Correct consumer ✓ |
| `atlas/domains/` | No — no domain imports in suitability | Clean ✓ |

`atlas/suitability/` is a distinct application-layer package. It is the only package in Atlas that:
1. Evaluates investor profile compatibility against investment characteristics
2. Produces a structured `SuitabilityAssessment` with factors, mismatches, confidence, and transparency fields
3. Renders profile-compatibility language explicitly framed as non-advice

No consolidation warranted.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Classification | Sprint 206 |
|---|---|---|---|
| 7 public exports | All have active production callers | `active_application_exports` | Leave unchanged |
| Private helpers | All called — none dead | `active_internal_helpers` | Leave unchanged |
| `render_suitability_assessment` output language | Anti-advice disclaimer present; no forbidden language | `guardrail_language` — acceptable | Leave unchanged |
| CLI `suitability analyze` command | Active, opt-in provider, neutral output | `active_CLI_command` | Leave unchanged |
| Imports from `atlas.analysis.engine`, `atlas.capabilities.portfolio_intelligence`, `atlas.intelligence`, `atlas.profile`, `atlas.themes` | All correct, active, expected consumer pattern | `acceptable_application_layer_dependencies` | Leave unchanged |
| `PortfolioFitResult` import | From `atlas.capabilities.portfolio_intelligence` — correct capability consumer | `acceptable_application_layer_dependency` | Leave unchanged |
| `TYPE_CHECKING` guard on `Portfolio` | Correct type-annotation-only pattern | `acceptable_type_annotation_pattern` | Leave unchanged |

**Summary: No cleanup warranted.** The package is clean, active, bounded, and correctly framed.

---

## Track Closure

**The `atlas/suitability/` cleanup track is OPEN as of Sprint 205. Recommended Sprint 206 action: close track (no cleanup warranted).**

---

## Sprint 205 Verification Table

| Check | Result |
|---|---|
| `atlas/suitability/` module count | 2 (`__init__.py`, `engine.py`) ✓ |
| Public exports | 7 — all active ✓ |
| Stale exports | None ✓ |
| Zero-caller symbols | None ✓ |
| CLI exposure | `atlas suitability analyze` — active ✓ |
| Provider coupling in `atlas/suitability/` | None ✓ |
| Network access in `atlas/suitability/` | None ✓ |
| Forbidden language | None — anti-advice disclaimer present ✓ |
| `check_suitability_assessment` in active `atlas.suitability` exports | No — correctly absent ✓ |
| Stale imports from closed cleanup tracks | None ✓ |
| `atlas.models.investment_report` reference | None ✓ |
| `atlas.reports` / `atlas.storage` reference | None ✓ |
| Circular dependencies | None ✓ |
| Overlap with decision/risk/principles/evidence | None — distinct layer ✓ |
| Compile check | Green ✓ |
| Full test suite | **1681 passed, 3 skipped** ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Behavior changes | None |
| Track status | **OPEN Sprint 205 — close in Sprint 206** |

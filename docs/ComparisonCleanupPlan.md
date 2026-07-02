# Atlas Comparison Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 159)  
**Updated:** 2026-07-03 (Sprint 160)  
**Status:** CLOSED — Sprint 160 confirmed Sprint 159 findings unchanged. No cleanup action is warranted. Package is provider-coupled, actively used via `InvestmentComparisonEngine`, and stable. No further `atlas/comparison/` cleanup work is planned until new dead code, stale exports, provider-boundary issues, or a Blueprint-aligned successor emerges.

---

## Background

`atlas/comparison/` is a provider-coupled module containing `InvestmentComparisonEngine`. The `atlas compare` CLI command is active. The package imports `CompanyDataProvider` and `MockCompanyAnalysisProvider` from `atlas/providers/`, with network access strictly opt-in via `--provider yahoo`. It has no Blueprint-aligned successor.

---

## `atlas/comparison/` Package Inventory (Sprint 159 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 23 | Re-export hub — 9 exports |
| `engine.py` | 1009 | Core engine — all logic |

---

## `engine.py` — Public API

| Symbol | Kind | Active production callers | Test callers | Status |
|---|---|---|---|---|
| `ComparisonRating` | str Enum (6 values) | CLI (via report), tests | `test_investment_comparison.py` | **Active** |
| `InvestmentComparisonCandidate` | frozen dataclass | Via `InvestmentComparisonReport.candidates` | `test_investment_comparison.py` | **Active — report sub-type** |
| `InvestmentComparisonEngine` | class | CLI (`atlas compare`) | `test_investment_comparison.py` | **Active — core engine** |
| `InvestmentComparisonInput` | frozen dataclass | CLI | `test_investment_comparison.py` | **Active** |
| `InvestmentComparisonObservation` | frozen dataclass | 0 direct external | 0 direct | **Active — internal sub-type of `InvestmentComparisonSection`** |
| `InvestmentComparisonReport` | frozen dataclass | CLI (returned by `.compare()`) | `test_investment_comparison.py` | **Active — main output type** |
| `InvestmentComparisonSection` | frozen dataclass | 0 direct external | 0 direct | **Active — internal sub-type of `InvestmentComparisonReport.sections`** |
| `demo_investment_comparison_input` | function | CLI (demo mode) | `test_investment_comparison.py` | **Active** |
| `render_investment_comparison` | function | CLI | `test_investment_comparison.py` | **Active — CLI output** |

### `engine.py` — Private Helpers

All private helpers are fully internal and active. None have stale residue.

| Symbol | Purpose |
|---|---|
| `_render_investment_comparison_without_principles` | Builds render string before principles check |
| `_candidate` | Constructs `InvestmentComparisonCandidate` with language report |
| `_sections` | Builds all 10 comparison sections |
| `_section` | Constructs one `InvestmentComparisonSection` |
| `_key_differences_section` | Quality, risk, evidence, valuation, cyclicality comparison |
| `_investor_fit_section` | Fit by profile archetype |
| `_evidence_quality_section` | Evidence strength per candidate |
| `_theme_market_section` | Theme exposure and market regime context |
| `_portfolio_role_section` | Role per candidate |
| `_change_view_section` | What would change Atlas' view |
| `_suggested_questions_section` | Conditional follow-up questions |
| `_full_reasoning_section` | Full reasoning: assumptions, engines, signals, counterarguments |
| `_language_report` | Builds `AtlasLanguageReport` for the comparison |
| `_bottom_line` | Human-readable summary sentence |
| `_comparison_rating` | Maps candidate spread → `ComparisonRating` |
| `_comparison_confidence` | Average confidence minus evidence penalty |
| `_candidate_confidence` | Base confidence + evidence impact |
| `_evidence_for_idea` | Lookup user-supplied `EvidenceInput` for idea |
| `_candidate_change_view` | Builds "what could change view" tuple |
| `_evidence_summary` | Human-readable evidence strength |
| `_missing_information` | Aggregates missing info from candidates |
| `_rating_from_score` | Score → Atlas rating string |
| `_view_from_confidence` | Confidence → Atlas view string |
| `_confidence_level` | Score → `ConfidenceLevel` enum |
| `_valuation_sensitivity` | Valuation score → sensitivity string |
| `_portfolio_role_for_company` | Quality + risk scores → portfolio role |
| `_theme_exposure_for_company` | Hardcoded ticker → theme tuple (5 tickers: NVDA, AMD, MSFT, AAPL, EVO) |
| `_highest_quality` | Max quality_score candidate |
| `_evidence_score` | `EvidenceStrength` → numeric score |
| `_section_summaries` | Extracts observation summaries from a named section |
| `_default_market_snapshot` | Deterministic placeholder `MarketSnapshot` |
| `STRONG_EVIDENCE` | Module-level constant — `{VERY_STRONG, STRONG}` |

---

## `engine.py` — Imports from Other Atlas Packages

| Import | Package | Classification |
|---|---|---|
| `atlas.analysis.report.build_investment_report` | `atlas/analysis/` | Active — `atlas/analysis/report.py` was not deleted in Sprint 141 (only portfolio/comparison/etc. were). Legitimate dependency. |
| `atlas.analysis.scores.clamp_score` | `atlas/analysis/` | Active utility function. |
| `atlas.economics.EconomicSignalsEngine` | `atlas/economics/` | Active engine dependency. |
| `atlas.evidence.*` | `atlas/evidence/` | Active — 7 imports. `atlas/evidence/` package is on disk (closed Sprint 150 = no new work, not deleted). |
| `atlas.language.*` | `atlas/language/` | Active — 8 imports. |
| `atlas.market.*` | `atlas/market/` | Active — 4 imports. |
| `atlas.monitoring.MonitoringEngine` | `atlas/monitoring/` | Active. |
| `atlas.principles.PrinciplesCheck`, `atlas.principles.PrinciplesEngine` | `atlas/principles/` | Active — principles guardrail on comparison output. |
| `atlas.profile.InvestorProfile`, `atlas.profile.InvestorProfileEngine` | `atlas/profile/` | Active. |
| `atlas.providers.CompanyDataProvider` | `atlas/providers/` | Active — type annotation for `InvestmentComparisonInput.provider` field. |
| `atlas.providers.MockCompanyAnalysisProvider` | `atlas/providers/` | Active — used as default provider in `.compare()` and `demo_investment_comparison_input()`. |
| `atlas.suitability.SuitabilityEngine`, `atlas.suitability.SuitabilityInput` | `atlas/suitability/` | Active. |
| `atlas.themes.ThemeEngine`, `atlas.themes.ThemeInput` | `atlas/themes/` | Active. |

**Zero imports from deleted packages.** No `atlas.reasoning`, `atlas.analysis.portfolio`, `atlas.analysis.comparison`, etc.

---

## Export Review (`__init__.py`)

9 exports. All active or intentional.

| Export | Active? | Direct external callers |
|---|---|---|
| `ComparisonRating` | ✓ | CLI (via report), tests |
| `InvestmentComparisonCandidate` | ✓ (sub-type) | Tests; accessed via `.candidates` in production |
| `InvestmentComparisonEngine` | ✓ | CLI, tests |
| `InvestmentComparisonInput` | ✓ | CLI, tests |
| `InvestmentComparisonObservation` | ✓ (sub-type) | 0 direct — accessed via `.sections[n].observations` |
| `InvestmentComparisonReport` | ✓ | CLI (returned type), tests |
| `InvestmentComparisonSection` | ✓ (sub-type) | 0 direct — accessed via `.sections` |
| `demo_investment_comparison_input` | ✓ | CLI (demo mode), tests |
| `render_investment_comparison` | ✓ | CLI, tests |

**Finding:** All 9 exports are intentional. `InvestmentComparisonObservation` and `InvestmentComparisonSection` have zero direct external callers but are sub-fields of the active report type. They are correctly exported for type-annotation and downstream access. Not cleanup candidates.

---

## `InvestmentComparisonEngine` Review

| Detail | Value |
|---|---|
| Source file | `atlas/comparison/engine.py:108` |
| Public methods | `.compare(InvestmentComparisonInput) → InvestmentComparisonReport` |
| Constructor dependencies | 10 optional engine parameters (all default to `None` → instantiate defaults) |
| Provider dependency | `provider` injected via `InvestmentComparisonInput.provider` field; falls back to `MockCompanyAnalysisProvider()` if `None` |
| Direct provider call | `provider.get_company_analysis(ticker)` inside `._candidate()` — **constructor-injected, not self-instantiated** |
| Production callers | `atlas/cli/main.py` — `compare_command` |
| Test callers | `tests/test_investment_comparison.py` |
| CLI callers | `atlas compare [ideas...]` |
| Returns Blueprint-aligned data? | No — returns `InvestmentComparisonReport` (legacy type) |
| Zero-caller methods | None — `.compare()` is the only public method and is active |
| Stale compatibility logic | None found |

**Private methods:** `._candidate()`, `._theme_candidate()`, `._idea_candidate()` — all active, called by `.compare()`.

---

## Production Caller Map

**2 callers: CLI + tests.**

| Caller | Import | Symbols Used |
|---|---|---|
| `atlas/cli/main.py` | `from atlas.comparison import InvestmentComparisonEngine, InvestmentComparisonInput, demo_investment_comparison_input, render_investment_comparison` | All 4 |
| `tests/test_investment_comparison.py` | `from atlas.comparison import ComparisonRating, InvestmentComparisonEngine, InvestmentComparisonInput, render_investment_comparison` | 4 of 9 |

No production engine outside CLI imports from `atlas/comparison/`.

---

## CLI Caller Review

### `atlas compare`

| Detail | Value |
|---|---|
| Command | `atlas compare [ideas...] [--provider mock\|yahoo]` |
| Implementation | `atlas/cli/main.py:346–367` |
| Imports used | `InvestmentComparisonEngine`, `InvestmentComparisonInput`, `demo_investment_comparison_input`, `render_investment_comparison` |
| Provider selection | `_provider_from_name(provider_name)` — `"mock"` → `MockCompanyAnalysisProvider()`, `"yahoo"` → `YahooFinanceProvider()`. Default: `"mock"`. |
| Demo mode | When no ideas are provided, falls back to `demo_investment_comparison_input(provider=provider)` |
| Runtime behavior | Instantiates `InvestmentComparisonEngine()`, calls `.compare(comparison_input)`, renders via `render_investment_comparison(result)` |
| Output shape | Depends on `render_investment_comparison` |
| CLI behavior | Active and unchanged |
| Deprecated commands | None — `atlas compare` is the only comparison CLI command |

---

## Provider Boundary Review

`atlas/comparison/engine.py` imports from `atlas/providers/` at module level:

```python
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider
```

| Symbol | Where used | How | Network? | Classification |
|---|---|---|---|---|
| `CompanyDataProvider` | `InvestmentComparisonInput.provider: CompanyDataProvider \| None` | Type annotation only | No | **Acceptable — abstract type annotation** |
| `MockCompanyAnalysisProvider` | `InvestmentComparisonEngine.compare()` line 139; `demo_investment_comparison_input()` line 368 | Instantiated as default when `provider=None` | **No** — mock is deterministic, local | **Acceptable — mock default keeps network opt-in** |
| `YahooFinanceProvider` | Not in `atlas/comparison/`; only in `atlas/cli/main.py` via `_provider_from_name()` | CLI-selected | **Yes — opt-in via `--provider yahoo`** | **Acceptable — network is CLI-opt-in only** |

**Conclusion:** Provider coupling is intentional and clean.
- `MockCompanyAnalysisProvider` as default keeps all non-CLI usage provider-free.
- `YahooFinanceProvider` is only reachable via explicit CLI flag — never imported by `atlas/comparison/` itself.
- Provider direction is acceptable: comparison depends on providers, not the reverse.

---

## Blueprint Overlap Review

| Target | Overlap with `atlas/comparison/`? |
|---|---|
| `atlas/domains/` | No `atlas/domains/comparison/` exists. No Blueprint-aligned comparison domain. |
| `atlas/capabilities/` | No comparison capability exists. No `atlas/capabilities/comparison/`. |
| `atlas/decision/comparison.py` | **Separate and distinct** — see below. |
| `atlas/analysis/report.py` | Used as a dependency (`build_investment_report`) — not a successor. |
| `atlas/evidence/` | Used as a dependency — not a successor. |

### `atlas/decision/comparison.py` vs `atlas/comparison/`

These are two independent comparison modules with completely different purposes:

| Dimension | `atlas/decision/comparison.py` | `atlas/comparison/engine.py` |
|---|---|---|
| Lines | 130 | 1009 |
| Input | `tickers: list[str]`, `CompanyDataProvider`, `AtlasInvestmentEngine` | `InvestmentComparisonInput` (ideas, optional provider, optional profile) |
| Output | `ComparisonResult` (score-based rankings: best quality, valuation, growth, risk) | `InvestmentComparisonReport` (narrative sections, evidence quality, investor fit) |
| Approach | Score-ranked table comparison | Narrative contextual comparison with principles check |
| Callers | `atlas/decision/decision_engine.py` | `atlas/cli/main.py` (standalone `atlas compare` command) |
| Purpose | Decision-support sub-comparison inside a full decision flow | Standalone multi-idea comparison for investor education |
| Blueprint migration target? | Potentially — `atlas/domains/decision/` exists | No Blueprint target |

**They serve different flows and should remain separate.** `atlas/decision/comparison.py` belongs to the decision track (CLOSED Sprint 144). `atlas/comparison/` is standalone.

---

## Stale Import Audit

**Zero stale closed-track symbols found in `atlas/comparison/`.**

Checked for all closed-track symbols:
- `atlas.reasoning`, `ReasoningEngine`, `ReasoningReport` — absent ✓
- `check_reasoning_report`, `check_intelligence_report`, `check_suitability_assessment` — absent ✓
- `atlas.analysis.portfolio`, `PortfolioAnalysis`, `PortfolioSignal` — absent ✓
- `atlas.analysis.comparison` — absent ✓ (note: `atlas/decision/comparison.py` is a different module)
- `atlas.analysis.memory`, `atlas.analysis.scoring`, `atlas.analysis.watchlist` — absent ✓
- `render_comparison_result` — absent ✓
- `YahooCompany`, `YahooFinancials`, `YahooMarketData` — absent ✓
- `PortfolioIntelligenceEngine`, `portfolio_fit_input_from_profile` — absent ✓

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Sprint 160? |
|---|---|---|---|---|
| `InvestmentComparisonObservation` | Zero direct external callers; accessed via `.observations` | 0 direct | LOW — correct sub-type of report; removing would break downstream type access | **No — leave unchanged** |
| `InvestmentComparisonSection` | Zero direct external callers; accessed via `.sections` | 0 direct | LOW — same reasoning | **No — leave unchanged** |
| `_theme_exposure_for_company` | Hardcoded ticker map (5 tickers: NVDA, AMD, MSFT, AAPL, EVO); falls back to `("Unclear",)` for all others | Internal only | LOW — stale data risk but graceful fallback; no semantic breakage | **No — leave unchanged; internal** |
| All other symbols | All active — CLI, tests, or report sub-types | Active | N/A | Leave unchanged |

**Overall assessment:** The comparison package is clean. No dead code, no stale exports, no closed-track residue, no Blueprint migration pressure. All 9 exports are intentional. Provider coupling is clean and opt-in.

---

## Final Stable Package State (Sprint 159)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 23 | 9 exports — all intentional |
| `engine.py` | 1009 | Active — `InvestmentComparisonEngine` with clean provider boundary |

**Provider safety:** Network access is opt-in only (`--provider yahoo`). Default is `MockCompanyAnalysisProvider` (deterministic, local). ✓

---

## Recommended Sprint 160 Target

**Close the comparison cleanup track.**

After inventory (Sprint 159), the comparison package contains no actionable cleanup candidates:
- All 9 exports are active or intentional sub-types
- No dead code or stale exports
- No closed-track import residue
- No Blueprint successor exists
- Provider boundary is clean and intentional
- CLI is active and unchanged

Sprint 160 should be a documentation-only sprint confirming the audit findings and closing the comparison cleanup track. No code changes are needed. Pattern matches Sprint 150, 155, and 158.

**Reopening condition:** If a Blueprint-aligned comparison capability emerges in `atlas/capabilities/`, or if the CLI command is deprecated, this track should be reopened.

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
| **Comparison package** | **CLOSED Sprint 160** |

---

## Sprint 160 — Track Closure (COMPLETED)

**Comparison cleanup track is CLOSED as of Sprint 160.**

Sprint 160 verified:
- All 9 `atlas.comparison` exports remain importable ✓
- `InvestmentComparisonEngine` active — `atlas compare` CLI caller confirmed ✓
- Provider coupling intentional — `MockCompanyAnalysisProvider` default (no network); `YahooFinanceProvider` CLI opt-in only ✓
- `YahooFinanceProvider` not imported by `atlas/comparison/` directly ✓
- Zero stale closed-track imports in `atlas/comparison/` ✓
- No Blueprint-aligned successor introduced since Sprint 159 ✓
- `atlas/decision/comparison.py` remains separate and distinct ✓
- No cleanup action is warranted ✓

**Closure rationale:** After inventory (Sprint 159) and final verification (Sprint 160), the comparison package contains only active, intentional code. `InvestmentComparisonEngine` is the sole engine, used by the active `atlas compare` CLI command. Provider coupling is clean and opt-in. No Blueprint successor exists. Further cleanup would create churn without architectural benefit.

**Reopening condition:** If a Blueprint-aligned comparison capability emerges in `atlas/capabilities/`, if the CLI command is deprecated, or if new dead code or stale provider imports appear, this track should be reopened.

---

## Recommended Sprint 161 Target

**Audit `atlas/home/` — Group B provider-coupled module.**

`atlas/home/` is the next natural audit target:
- Provider-coupled: known to import from `atlas/providers/`
- CLI command `atlas home` may be active or deprecated — status should be confirmed
- Audit-first: inventory modules, map callers, verify provider boundary, check Blueprint overlap, classify cleanup candidates, recommend one focused follow-on sprint
- No deletions in the audit sprint

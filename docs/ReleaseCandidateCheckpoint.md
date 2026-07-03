# Atlas Release Candidate Checkpoint

**Created:** 2026-07-03 (Sprint 163)  
**Updated:** 2026-07-03 (Sprint 172)  
**Status:** GREEN — Atlas RC2 is stable after 14 cleanup tracks closed.

---

## Sprint 163 Checkpoint Summary

Sprint 163 is a verification, documentation, and stabilization sprint confirming Atlas remains release-candidate stable after the cleanup closure sequence (Sprints 141–162).

No runtime behavior changed. No modules deleted. No CLI behavior changed.

---

## Closed Cleanup Tracks (10 total)

| Track | Closure Sprint | Outcome |
|---|---|---|
| `atlas/analysis/` cleanup | Sprint 141 | Multiple analysis submodules deleted over Sprints 100–141 |
| `atlas/decision/` cleanup | Sprint 144 | `render_comparison_result` deleted Sprint 143; track closed Sprint 144 |
| Provider boundary audit | Sprint 146 | Stale Yahoo re-exports removed; 4 clean public exports remain |
| Portfolio boundary | Sprint 148 | Stale `PortfolioFitInput` import removed from adapter |
| `atlas/evidence/` cleanup | Sprint 150 | No cleanup warranted; package clean and stable |
| `atlas/reasoning/` cleanup | Sprint 153 | `atlas/reasoning/` package deleted; `check_reasoning_report` removed Sprint 152 |
| `atlas/risk/` cleanup | Sprint 155 | No cleanup warranted; package clean and stable |
| `atlas/principles/` cleanup | Sprint 158 | `check_intelligence_report` + `check_suitability_assessment` removed Sprint 157 |
| `atlas/comparison/` cleanup | Sprint 160 | No cleanup warranted; package clean and stable |
| `atlas/home/` cleanup | Sprint 162 | No cleanup warranted; package clean and stable |

---

## Deleted Module Guard

All deleted modules confirmed absent:

| Module/Package | Status |
|---|---|
| `atlas/reasoning/` | Absent ✓ (deleted Sprint 153) |
| `atlas/analysis/portfolio.py` | Absent ✓ |
| `atlas/analysis/growth.py` | Absent ✓ |
| `atlas/analysis/macro.py` | Absent ✓ |
| `atlas/analysis/moat.py` | Absent ✓ |
| `atlas/analysis/quality.py` | Absent ✓ |
| `atlas/analysis/sentiment.py` | Absent ✓ |
| `atlas/analysis/technicals.py` | Absent ✓ |
| `atlas/analysis/valuation.py` | Absent ✓ |

All retired symbol references in active code classified:
- `atlas/domains/decision/engine.py` defines its own `ReasoningEngine` — a distinct Blueprint-layer class, unrelated to the deleted `atlas.reasoning.ReasoningEngine`. **Expected.**
- `atlas/capabilities/portfolio_intelligence/models.py` references deleted symbols in doc comments mapping legacy → Blueprint types. **Expected.**
- `atlas/cli/deprecations.py` references retired symbols in `removal_criteria` strings. **Expected — retired command records only, never executed.**
- All other hits are in test guardrail files asserting symbols remain absent. **Expected.**

No stale active runtime references found.

---

## CLI Verification

### Active deprecated CLI commands

`_REGISTRY` in `atlas/cli/deprecations.py` is empty — all deprecated commands were retired as of Sprint 91.

### Retired commands (in `_RETIRED_REGISTRY`, not callable)

| Command | Retired | Reason |
|---|---|---|
| `atlas daily brief` | Sprint 85 | Engine deleted Sprint 77 |
| `atlas evidence assess` | Sprint 86 | CLI body retired; engine active |
| `atlas reason analyze` | Sprint 87 | `atlas/reasoning/` deleted Sprint 153 |
| `atlas risk size` | Sprint 88 | CLI body retired; engine active |
| `atlas portfolio analyze` | Sprint 89 | Engine deleted Sprint 135 |
| `atlas portfolio review` | Sprint 90 | CLI body retired; engine active |
| `atlas watchlist analyze` | Sprint 91 | Engine deleted Sprint 99–101 |

None of these commands are registered or callable.

### Active CLI commands (sample)

`atlas home`, `atlas compare`, `atlas analyze`, `atlas daily summary`, `atlas intelligence analyze`, `atlas dashboard show`, `atlas journal create/list/review`, `atlas language explain`, `atlas memory save/show/compare`, `atlas economics analyze`, `atlas report`, `atlas monitor`, `atlas ask`, `atlas add-company`, `atlas list-companies`, `atlas import-financials`.

---

## Active Package Smoke Verification

| Package | Exports | Status |
|---|---|---|
| `atlas.evidence` | 9 | All importable ✓ |
| `atlas.risk` | 8 | All importable ✓ |
| `atlas.principles` | 9 | All importable ✓ |
| `atlas.comparison` | 9 | All importable ✓ |
| `atlas.home` | 7 | All importable ✓ |

---

## Provider Boundary

| Package | Default provider | Network provider | Import in package? |
|---|---|---|---|
| `atlas/comparison/` | `MockCompanyAnalysisProvider` | CLI opt-in `--provider yahoo` | No `YahooFinanceProvider` import ✓ |
| `atlas/home/` | `MockCompanyAnalysisProvider` | CLI opt-in `--provider yahoo` | No `YahooFinanceProvider` import ✓ |
| `atlas/cli/main.py` | — | `YahooFinanceProvider` via `_provider_from_name()` | Correct location — CLI only ✓ |

No new provider behavior introduced. No new network calls added. Demo remains provider-free.

---

## Release Candidate Verification

| Check | Result |
|---|---|
| `python -m compileall atlas tests` | Green ✓ |
| `python -m pytest` | 1460 passed, 3 skipped ✓ |
| `scripts/verify_release_candidate.sh` | RC2 green ✓ |
| `scripts/run_daily_brief_demo.sh` | Passes, provider-free ✓ |
| Forbidden language check | No violations ✓ |

---

## Stale Reference (Non-Blocking)

`atlas/cli/deprecations.py` `removal_criteria` for `atlas risk size` states that `RiskAnalysis` is imported by `atlas/reasoning engines`. `atlas/reasoning/` was deleted Sprint 153. The actual current callers are `atlas/intelligence/engine.py` and `atlas/conversation/engine.py`. This is inside a retired command record (`_RETIRED_REGISTRY`) — never executed at runtime. No impact. May be corrected as a housekeeping note during the Sprint 164 `atlas/intelligence/` audit.

---

## Recommended Sprint 164 Target

**Audit `atlas/intelligence/` package.**

`atlas/intelligence/` is a larger runtime surface (active CLI command `atlas intelligence analyze`, imports from multiple packages). It should be audited now that the cleanup closure sequence has been release-verified at Sprint 163. Pattern: audit-first (Sprint 164 inventory), then targeted action or documentation closure sprint (Sprint 165).

---

## Reopening Conditions

No closed track should be reopened unless:
- New dead code, stale imports, or stale exports appear in the package
- A Blueprint-aligned successor is introduced
- A CLI command is deprecated or retired
- A new provider boundary violation is introduced

---

## Sprint 172 Checkpoint Summary

Sprint 172 is a verification, documentation, and stabilization sprint confirming Atlas remains release-candidate stable after 14 cleanup track closures (Sprints 141–171).

No runtime behavior changed. No modules deleted. No CLI behavior changed.

---

## Closed Cleanup Tracks (14 total)

| Track | Closure Sprint | Outcome |
|---|---|---|
| `atlas/analysis/` cleanup | Sprint 141 | Multiple analysis submodules deleted over Sprints 100–141 |
| `atlas/decision/` cleanup | Sprint 144 | `render_comparison_result` deleted Sprint 143; track closed Sprint 144 |
| Provider boundary audit | Sprint 146 | Stale Yahoo re-exports removed; 4 clean public exports remain |
| Portfolio boundary | Sprint 148 | Stale `PortfolioFitInput` import removed from adapter |
| `atlas/evidence/` cleanup | Sprint 150 | No cleanup warranted; package clean and stable |
| `atlas/reasoning/` cleanup | Sprint 153 | `atlas/reasoning/` package deleted; `check_reasoning_report` removed Sprint 152 |
| `atlas/risk/` cleanup | Sprint 155 | No cleanup warranted; package clean and stable |
| `atlas/principles/` cleanup | Sprint 158 | `check_intelligence_report` + `check_suitability_assessment` removed Sprint 157 |
| `atlas/comparison/` cleanup | Sprint 160 | No cleanup warranted; package clean and stable |
| `atlas/home/` cleanup | Sprint 162 | No cleanup warranted; package clean and stable |
| `atlas/intelligence/` cleanup | Sprint 165 | No cleanup warranted; package clean and stable |
| `atlas/conversation/` cleanup | Sprint 167 | No cleanup warranted; package clean and stable |
| `atlas/dashboard/` cleanup | Sprint 169 | No cleanup warranted; cleanest provider boundary audited |
| `atlas/capabilities/portfolio_intelligence/` cleanup | Sprint 171 | Stale docstring removed; no runtime cleanup warranted; exemplary Blueprint capability |

---

## Deleted Module Guard (Sprint 172)

All deleted modules confirmed absent:

| Module/Package | Status |
|---|---|
| `atlas/reasoning/` | Absent ✓ (deleted Sprint 153) |
| `atlas/analysis/portfolio.py` | Absent ✓ |
| `atlas/analysis/growth.py` | Absent ✓ |
| `atlas/analysis/macro.py` | Absent ✓ |
| `atlas/analysis/moat.py` | Absent ✓ |
| `atlas/analysis/quality.py` | Absent ✓ |
| `atlas/analysis/sentiment.py` | Absent ✓ |
| `atlas/analysis/technicals.py` | Absent ✓ |
| `atlas/analysis/valuation.py` | Absent ✓ |
| `atlas/analysis/comparison.py` | Absent ✓ |
| `atlas/analysis/memory.py` | Absent ✓ |
| `atlas/analysis/scoring.py` | Absent ✓ |
| `atlas/analysis/watchlist.py` | Absent ✓ |

All retired symbol references in active code classified:
- `atlas/domains/decision/engine.py` defines its own `ReasoningEngine` — a distinct Blueprint-layer class, unrelated to the deleted `atlas.reasoning.ReasoningEngine`. **Expected.**
- `atlas/capabilities/portfolio_intelligence/models.py` references deleted types in doc comments. **Expected — docstring migration notes only.**
- `atlas/cli/deprecations.py` references retired symbols in `removal_criteria` strings. **Expected — retired command records, never executed.**
- `atlas/providers/yahoo.py` defines `YahooCompany`, `YahooFinancials`, `YahooMarketData` — active internal types in the opt-in Yahoo provider. **Expected — not stale.**
- All other hits are in test guardrail files. **Expected.**

No stale active runtime references found.

---

## CLI Verification (Sprint 172)

### Retired commands (in `_RETIRED_REGISTRY`, not callable) — unchanged since Sprint 163

| Command | Retired |
|---|---|
| `atlas daily brief` | Sprint 85 |
| `atlas evidence assess` | Sprint 86 |
| `atlas reason analyze` | Sprint 87 |
| `atlas risk size` | Sprint 88 |
| `atlas portfolio analyze` | Sprint 89 |
| `atlas portfolio review` | Sprint 90 |
| `atlas watchlist analyze` | Sprint 91 |

No retired command is callable. `_REGISTRY` (active deprecated commands) is empty.

### Active CLI commands (Sprint 172 confirmation)

`atlas home`, `atlas compare`, `atlas analyze`, `atlas daily summary`, `atlas intelligence analyze`, `atlas dashboard show`, `atlas ask`, `atlas decide`, `atlas journal create/list/review`, `atlas language explain`, `atlas memory save/show/compare`, `atlas economics analyze`, `atlas report`, `atlas monitor`, `atlas add-company`, `atlas list-companies`, `atlas import-financials`. All remain active.

---

## Active Package Smoke Verification (Sprint 172)

| Package | Export count | Status |
|---|---|---|
| `atlas.evidence` | 9 | All importable ✓ |
| `atlas.risk` | Active | Importable ✓ |
| `atlas.principles` | Active | Importable ✓ |
| `atlas.comparison` | 9 | All importable ✓ |
| `atlas.home` | 7 | All importable ✓ |
| `atlas.intelligence` | 5 | All importable ✓ |
| `atlas.conversation` | 6 | All importable ✓ |
| `atlas.dashboard` | 6 | All importable ✓ |
| `atlas.capabilities.portfolio_intelligence` | 4 | All importable ✓ |

---

## Provider Boundary (Sprint 172)

| Package | Default provider | Network access | Direct Yahoo import? |
|---|---|---|---|
| `atlas/comparison/` | `MockCompanyAnalysisProvider` (default) | CLI opt-in `--provider yahoo` | No `YahooFinanceProvider` ✓ |
| `atlas/home/` | `MockCompanyAnalysisProvider` (default) | CLI opt-in `--provider yahoo` | No `YahooFinanceProvider` ✓ |
| `atlas/conversation/` | `MockCompanyAnalysisProvider` (default) | CLI opt-in `--provider yahoo` | No `YahooFinanceProvider` ✓ |
| `atlas/intelligence/` | No direct provider import | Via constructor injection | None ✓ |
| `atlas/dashboard/` | No direct provider import | Via `DashboardInput.provider` type annotation only | None ✓ |
| `atlas/capabilities/portfolio_intelligence/` | No provider import | None — deterministic local only | None ✓ |
| `atlas/cli/main.py` | — | `YahooFinanceProvider` via `_provider_from_name()` | Correct — CLI layer only ✓ |

No new provider behavior introduced. No new network calls added. Demo remains provider-free.

---

## Release Candidate Verification (Sprint 172)

| Check | Result |
|---|---|
| `python -m compileall atlas tests` | Green ✓ |
| `python -m pytest` | 1524 passed, 3 skipped ✓ |
| `scripts/verify_release_candidate.sh` | RC2 green ✓ |
| `scripts/run_daily_brief_demo.sh` | Passes, provider-free ✓ |
| Forbidden language check | No violations ✓ |

---

## Recommended Sprint 173 Target

**Audit `atlas/cli/` deprecated command registry.**

After 14 closed cleanup tracks and two RC checkpoints (Sprint 163, Sprint 172), the next smallest high-leverage target is the CLI deprecated command registry and command surface. Auditing the CLI will confirm the retirement state is complete and identify any stale metadata or residual CLI coupling.

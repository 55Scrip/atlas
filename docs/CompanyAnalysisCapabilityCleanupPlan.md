# Atlas Company Analysis Capability Cleanup Plan

**Created:** 2026-07-03 (Sprint 182)
**Status:** AUDIT COMPLETE — no cleanup warranted. Sprint 183 recommended: close company analysis capability cleanup track.

---

## Package Overview

`atlas/capabilities/company_analysis/` is the Blueprint-aligned deterministic company analysis capability. It produces structured, non-advisory `CompanyAnalysisReport` objects from local domain inputs — no provider access, no network calls, no scoring/recommendation language.

| Module | Lines | Role |
|---|---|---|
| `__init__.py` | 25 | Re-exports 9 public symbols |
| `models.py` | 88 | Frozen dataclasses: domain types for capability I/O |
| `engine.py` | 387 | `CompanyAnalysisEngine` — deterministic analysis orchestrator |
| `exporter.py` | 71 | `company_report_to_dict`, `company_reports_to_list` — JSON serialization |

**Total: 571 lines**

This capability was audited from the outside during Sprint 179 (boundary-only). Sprint 182 performs a full internal inventory.

---

## Module Inventory

### `atlas/capabilities/company_analysis/__init__.py` (25 lines)

Re-exports all public symbols from `models.py` and `engine.py`. No logic.

**Exports (9):** `CompanyAnalysisConfidence`, `CompanyAnalysisEngine`, `CompanyAnalysisEvidenceLink`, `CompanyAnalysisInput`, `CompanyAnalysisObservation`, `CompanyAnalysisReport`, `CompanyAnalysisRisk`, `CompanyAnalysisSection`, `CompanyAnalysisUnknown`

All 9 exports are in `__all__`. All 9 have external callers (see Export Review).

---

### `atlas/capabilities/company_analysis/models.py` (88 lines)

**Public symbols (7 dataclasses):**

| Symbol | Role | External callers |
|---|---|---|
| `CompanyAnalysisEvidenceLink` | Traceable evidence link | adapter (`company_analysis.py`), tests |
| `CompanyAnalysisObservation` | Calm structured observation | `test_daily_brief_input_builder.py`, `test_capabilities_package_sprint176.py` |
| `CompanyAnalysisRisk` | Structured risk | `test_capabilities_package_sprint176.py` |
| `CompanyAnalysisUnknown` | Missing/unresolved information | adapter, tests |
| `CompanyAnalysisConfidence` | Categorical confidence | adapter, tests |
| `CompanyAnalysisSection` | Section in a report | adapter, tests |
| `CompanyAnalysisReport` | Non-advisory structured report | adapter, discovery, watchlist_intelligence, exporter, CLI, tests — **most-used type (29 refs)** |
| `CompanyAnalysisInput` | Input for deterministic analysis | CLI, tests |

**Imports:**
- `atlas.domains.decision` — `Evidence`
- `atlas.domains.knowledge` — `KnowledgeFact`
- `atlas.domains.research` — `ResearchProject`
- `atlas.shared` — `Company`

**Classification:** Active, Blueprint-aligned, foundational. Pure frozen dataclasses — no logic, no network, no provider coupling.

---

### `atlas/capabilities/company_analysis/engine.py` (387 lines)

**Public symbols:**
- `CompanyAnalysisEngine` — single public class with one public method: `analyze(analysis_input: CompanyAnalysisInput) → CompanyAnalysisReport`

**Private helpers (8):** All module-level functions, all called only from within `engine.py`:
- `_evidence_links` — builds evidence link tuples from knowledge facts, research, decision evidence
- `_unknowns` — surfaces missing company fields, open questions, unsupported thesis fragments
- `_risks` — identifies risk language in facts and decision evidence
- `_confidence` — computes categorical confidence from evidence completeness
- `_sections` — assembles 10 structured report sections
- `_research_observations` — builds observations from `ResearchProject`
- `_what_could_change_the_view` — derives change factors from unknowns and risks
- `_contains_risk_language` — keyword heuristic: "risk", "concentration", "uncertain", "dependency", "margin pressure"

All 8 private helpers are internal. None are imported or tested directly by external callers.

**Imports:**
- `atlas.capabilities.company_analysis.models` — 8 types
- `atlas.domains.research` — `ResearchQuestionStatus`, `summarize_research`

**Production callers of `CompanyAnalysisEngine`:**
- `atlas/cli/main.py` — `company_analysis_export_command` instantiates `CompanyAnalysisEngine()` and calls `.analyze()`

**Test callers:** `test_company_analysis_capability.py` (280 lines), `test_company_analysis_export.py` (516 lines)

**Classification:** Active, deterministic, provider-free. Architecturally clean — depends only on capability models and domain research types.

---

### `atlas/capabilities/company_analysis/exporter.py` (71 lines)

**Public symbols:**
- `company_report_to_dict(report: CompanyAnalysisReport) → dict` — serializes one report to Daily Brief–compatible dict
- `company_reports_to_list(reports: tuple[CompanyAnalysisReport, ...]) → list` — serializes a tuple of reports to JSON-serializable list

**Imports:**
- `atlas.capabilities.company_analysis.models` — `CompanyAnalysisReport`

**Production callers:**
- `atlas/cli/main.py` — `company_reports_to_list` (used in both `company-analysis export` and `company-analysis merge` commands)

**Test callers:** `test_company_analysis_export.py`

**Classification:** Active, serialization-only, no logic, no network. Produces the format consumed by `atlas daily summary --company-analysis`.

---

## Export Review

All 9 `__all__` exports reviewed:

| Export | Production callers | Test callers | Active? |
|---|---|---|---|
| `CompanyAnalysisEngine` | CLI (`company-analysis export`) | `test_company_analysis_capability.py`, `test_company_analysis_export.py` | ✓ |
| `CompanyAnalysisReport` | adapter, discovery, watchlist_intelligence, exporter, CLI | many test files | ✓ (29 external refs) |
| `CompanyAnalysisInput` | CLI (`company-analysis export`) | `test_company_analysis_capability.py`, `test_daily_brief_input_builder.py` | ✓ |
| `CompanyAnalysisConfidence` | adapter (`company_analysis.py`) | `test_company_analysis_capability.py`, `test_capabilities_package_sprint176.py` | ✓ |
| `CompanyAnalysisEvidenceLink` | adapter (`company_analysis.py`) | tests | ✓ |
| `CompanyAnalysisSection` | adapter (`company_analysis.py`) | tests | ✓ |
| `CompanyAnalysisUnknown` | adapter (`company_analysis.py`) | tests | ✓ |
| `CompanyAnalysisObservation` | `test_daily_brief_input_builder.py`, `test_capabilities_package_sprint176.py` | — | ✓ (test-accessible, not zero-caller) |
| `CompanyAnalysisRisk` | `test_capabilities_package_sprint176.py` | — | ✓ (test-accessible; used in engine internally) |

**Notes on low-count exports:**
- `CompanyAnalysisObservation` — 2 external references, both in test files. The type is also constructed internally by `engine.py` throughout `_sections()`. Legitimate dataclass in the domain model; tests verify the type is accessible. Not stale.
- `CompanyAnalysisRisk` — 1 external reference (Sprint 176 importability test). Also used extensively inside `engine.py`. Legitimate type. Not stale.

No stale exports. No exports to remove.

---

## CLI and Pipeline Caller Review

### `atlas company-analysis export` (`atlas/cli/main.py:1085`)

- Imports: `CompanyAnalysisEngine`, `CompanyAnalysisInput` from `atlas.capabilities.company_analysis`; `company_reports_to_list` from `atlas.capabilities.company_analysis.exporter`; `company_reports_from_dict` from `atlas.adapters.company_analysis`
- Two paths:
  1. **New analysis**: builds `CompanyAnalysisInput` from CLI args, runs `CompanyAnalysisEngine().analyze()`, serializes via `company_reports_to_list()`
  2. **Re-export**: loads existing JSON, parses with `company_reports_from_dict()`, re-serializes via `company_reports_to_list()`
- Provider: none — fully deterministic, no provider access
- Output: JSON file compatible with `atlas daily summary --company-analysis`

### `atlas company-analysis merge` (`atlas/cli/main.py:1222`)

- Validates input files with `parse_company_analysis_json()` (from `atlas.capabilities.daily_brief.json_loader`)
- Merges JSON lists — does not call `CompanyAnalysisEngine` directly
- Provider: none

### `atlas daily summary --company-analysis` (`atlas/cli/main.py:403`)

- Loads company analysis JSON via `parse_company_analysis_json()`
- Passes parsed reports to the daily brief pipeline
- `atlas/capabilities/daily_brief/engine.py:247` — `_company_analysis_opening_item(data.company_reports)` uses `company_reports` but does **not** directly import `CompanyAnalysisReport` type; it operates on the parsed JSON structure
- Provider: none

### Cross-capability usage

- `atlas/capabilities/discovery/models.py` — `DiscoveryResult.company_analysis_reports: tuple[CompanyAnalysisReport, ...]`
- `atlas/capabilities/discovery/engine.py` — `CompanyAnalysisReport` used in discovery ranking
- `atlas/capabilities/watchlist_intelligence/models.py` — `WatchlistItem.company_analysis: CompanyAnalysisReport | None`

All cross-capability usage is import-only (type dependency). No circular dependency.

---

## Legacy Analysis Boundary Review

| Check | Result |
|---|---|
| `atlas/capabilities/company_analysis/` imports `atlas.analysis` | ✗ — confirmed absent |
| `atlas/analysis/` imports `atlas.capabilities.company_analysis` | ✗ — confirmed absent |
| Two layers serve different CLI surfaces | ✓ |
| Two layers return different output types | ✓ (`InvestmentReport` vs. `CompanyAnalysisReport`) |
| No accidental shared mutable state | ✓ — all types are frozen dataclasses |
| No duplicate runtime orchestration warranting consolidation | ✓ — different models, different purposes |

**Layer comparison:**

| Dimension | `atlas/analysis/` (legacy) | `atlas/capabilities/company_analysis/` (Blueprint) |
|---|---|---|
| Output type | `InvestmentReport` (scored) | `CompanyAnalysisReport` (structured, non-advisory) |
| Recommendation language | Yes — `ThresholdRecommendationPolicy` | No |
| Data source | `CompanyAnalysis` placeholder types from provider | `CompanyAnalysisInput` from domain types |
| Provider coupling | Yes — provider-injected | None |
| CLI surface | `atlas report`, `atlas analyze` | `atlas company-analysis export/merge`, `atlas daily summary` |
| Blueprint-aligned | No — legacy | Yes |

Boundary is clean and intentional. No migration warranted.

---

## Domain / Shared Type Boundary Review

| Import | In module | Direction | Assessment |
|---|---|---|---|
| `atlas.domains.decision.Evidence` | `models.py` | capability → domain | ✓ Correct |
| `atlas.domains.knowledge.KnowledgeFact` | `models.py` | capability → domain | ✓ Correct |
| `atlas.domains.research.ResearchProject` | `models.py` | capability → domain | ✓ Correct |
| `atlas.shared.Company` | `models.py` | capability → shared entity | ✓ Correct |
| `atlas.domains.research.ResearchQuestionStatus` | `engine.py` | capability → domain | ✓ Correct |
| `atlas.domains.research.summarize_research` | `engine.py` | capability → domain function | ✓ Correct |

**No imports from:** `atlas.adapters`, `atlas.capabilities.*` (other capabilities), `atlas.decision`, `atlas.evidence`, `atlas.risk`, `atlas.principles`, `atlas.intelligence`, `atlas.conversation`, `atlas.dashboard`, `atlas.providers`, `atlas.cli`, `atlas.analysis`

Dependency direction is correct throughout: `atlas.shared → atlas.domains → atlas.capabilities`. No circular dependencies. No upward coupling.

---

## Provider Boundary Review

| Check | Finding |
|---|---|
| `atlas.providers` imported by capability | ✗ — no provider imports |
| `CompanyDataProvider` referenced | ✗ — not present |
| `MockCompanyAnalysisProvider` referenced | ✗ — not present |
| `YahooFinanceProvider` referenced | ✗ — not present |
| `requests`, `urllib`, `http` imported | ✗ — not present |
| Network access in any capability module | ✗ — none |

`atlas/capabilities/company_analysis/` is the cleanest provider boundary in the codebase — completely decoupled from providers. All inputs are domain types passed directly; no fetch, no network, no opt-in required.

---

## Stale Import Audit

No stale imports found in `atlas/capabilities/company_analysis/`. Full audit results:

| Symbol | Status in capability |
|---|---|
| `atlas.reasoning` | Not imported ✓ |
| Deleted `atlas.analysis.*` submodules | Not imported ✓ |
| `CompanyAnalysisProvider` | Not imported, not present ✓ |
| `PortfolioAnalysis`, `PortfolioSignal`, etc. | Not imported ✓ |
| `ReasoningInput`, `ReasoningReport` | Not imported ✓ |
| `render_comparison_result` | Not imported ✓ |
| `YahooCompany`, `YahooFinancials`, `YahooMarketData` | Not imported ✓ |

Zero stale imports in `atlas/capabilities/company_analysis/`.

---

## Blueprint / Capability Model Review

`atlas/capabilities/company_analysis/` is fully Blueprint-aligned:

| Question | Finding |
|---|---|
| Capability is Blueprint-aligned? | ✓ Yes — deterministic, non-advisory, domain-typed inputs |
| Capability models duplicate legacy `InvestmentReport`? | No — different type hierarchy, different purpose |
| Provider coupling in capability? | None — cleanest boundary audited |
| Capability should remain separate from legacy analysis? | Yes — different outputs, different CLI surfaces, intentional separation |
| Any migration would change behavior? | Yes — do not migrate |
| Any consolidation of shared structure warranted? | No — `CompanyAnalysis` (placeholder 7-dimension scores) and `CompanyAnalysisInput` (domain-typed evidence) are distinct concepts |

---

## Cleanup Candidate Classification

No cleanup candidates found.

| Area | Classification | Action |
|---|---|---|
| All 9 `__all__` exports | Leave unchanged | All active (internal usage or test-verified) |
| `CompanyAnalysisObservation` (2 external refs) | Leave unchanged | Used by `engine.py` internally + test-verified |
| `CompanyAnalysisRisk` (1 external ref) | Leave unchanged | Used by `engine.py` internally + test-verified |
| 8 private engine helpers | Leave unchanged | All called within `engine.py`; none dead |
| `exporter.py` | Leave unchanged | Both functions active, CLI-facing |
| No provider imports | Correct | No action |
| No legacy analysis imports | Correct | No action |

---

## Technical Debt Summary

`atlas/capabilities/company_analysis/` has no technical debt:

- 4 modules, 571 lines
- 9 `__all__` exports — all active
- 0 stale imports
- 0 provider coupling
- 0 CLI coupling
- 0 circular dependencies
- 0 upward dependencies
- Correct boundary: depends only on `atlas.domains` and `atlas.shared`
- Cleanest provider boundary of any capability
- Fully Blueprint-aligned — deterministic, non-advisory, no scoring, no recommendation language

---

## Recommended Sprint 183 Target

**Close the company analysis capability cleanup track** — confirm the audit is complete, no cleanup is warranted, and declare `atlas/capabilities/company_analysis/` closed.

After auditing `atlas/capabilities/` (Sprint 176), `atlas/capabilities/portfolio_intelligence/` (Sprints 170–171), and now `atlas/capabilities/company_analysis/` (Sprint 182), a short closure sprint will produce consistent documentation and a clean transition to the next audit target.

Following closure, the recommended next audit after Sprint 183 is `atlas/decision_journal/` — a package not yet audited and one of the smaller, more bounded runtime surfaces.

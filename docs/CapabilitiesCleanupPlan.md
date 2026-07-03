# Atlas Capabilities Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 176)
**Status:** AUDIT COMPLETE — no cleanup warranted. Sprint 177 recommended: Audit `atlas/domains/` package.

---

## Package Overview

`atlas/capabilities/` contains five subpackages totaling ~3,500 lines. Four are active production subtracks; one (`portfolio_intelligence`) is already closed as of Sprint 171.

| Subpackage | Lines | Status |
|---|---|---|
| `company_analysis/` | 571 | Active production capability |
| `daily_brief/` | 1,231 | Active production capability (primary demo target) |
| `discovery/` | 686 | Active production capability |
| `watchlist_intelligence/` | 545 | Active production capability |
| `portfolio_intelligence/` | 471 | CLOSED Sprint 171 — already-closed subtrack, do not reopen |
| `__init__.py` | 3 | Top-level namespace — `__all__` lists 4 active subpackages |

**Total (excluding portfolio_intelligence):** ~3,036 lines active

---

## Portfolio Intelligence Subtrack Status

`atlas/capabilities/portfolio_intelligence/` is **CLOSED Sprint 171** and remains closed. Sprint 176 verification confirms:

- 4 exports remain active: `PortfolioFitDimension`, `PortfolioFitInput`, `PortfolioFitResult`, `PortfolioIntelligenceCapability`
- All production callers active and unchanged
- No cleanup warranted
- **Do not reopen**

---

## Capabilities Package Inventory

### `atlas/capabilities/__init__.py` (3 lines)

- **Exports:** `__all__ = ["company_analysis", "daily_brief", "discovery", "watchlist_intelligence"]`
- Note: `portfolio_intelligence` is deliberately excluded from `__all__` since it is a closed subtrack — callers import directly from `atlas.capabilities.portfolio_intelligence`
- Status: Active, correct

---

### `atlas/capabilities/company_analysis/` (571 lines total)

**Modules:**

| File | Lines | Public Symbols |
|---|---|---|
| `__init__.py` | 25 | 9 exports |
| `engine.py` | 387 | `CompanyAnalysisEngine` + 7 private helpers |
| `models.py` | 88 | 7 public dataclasses |
| `exporter.py` | 71 | `company_report_to_dict`, `company_reports_to_list` |

**Public exports (9):** `CompanyAnalysisEngine`, `CompanyAnalysisInput`, `CompanyAnalysisReport`, `CompanyAnalysisConfidence`, `CompanyAnalysisSection`, `CompanyAnalysisObservation`, `CompanyAnalysisRisk`, `CompanyAnalysisUnknown`, `CompanyAnalysisEvidenceLink`

**Key method:** `CompanyAnalysisEngine.analyze(analysis_input) → CompanyAnalysisReport`

**Dependencies:**
- `atlas.domains.decision` — `Evidence` type (input field)
- `atlas.domains.knowledge` — `KnowledgeFact` type (input field)
- `atlas.domains.research` — `ResearchProject`, `ResearchQuestionStatus`, `summarize_research`
- `atlas.shared` — `Company` entity

**Production callers:**
- `atlas/cli/main.py` — `CompanyAnalysisEngine`, `CompanyAnalysisInput`, `company_reports_to_list`
- `atlas/adapters/company_analysis.py` — imports `CompanyAnalysisReport` and model types to build reports from JSON
- `atlas/capabilities/discovery/` — `CompanyAnalysisReport` used in `DiscoveryInput` and `DiscoveryEngine`
- `atlas/capabilities/watchlist_intelligence/models.py` — `CompanyAnalysisReport` as optional field on `WatchlistItem`

**Test callers:** `test_company_analysis_capability.py`, `test_company_analysis_export.py`, `test_company_analysis_engine_export.py`, `test_daily_brief_input_builder.py`, `test_discovery_capability.py`, `test_watchlist_intelligence_capability.py`

**Classification:** Active, foundational, runtime-facing, application-facing. No stale symbols. No provider coupling. Clean.

---

### `atlas/capabilities/daily_brief/` (1,231 lines total)

**Modules:**

| File | Lines | Public Symbols |
|---|---|---|
| `__init__.py` | 43 | 11 exports |
| `engine.py` | 626 | `DailyBriefCapability`, `render_daily_brief_report` + private helpers |
| `input_builder.py` | 66 | `build_daily_brief_input` (1 public function) |
| `json_loader.py` | 338 | Multiple JSON parsing functions |
| `models.py` | 103 | 8 public dataclasses/enums |
| `research_exporter.py` | 55 | `research_projects_to_dict` |

**Public exports (11):** `DailyBriefCapability`, `build_daily_brief_input`, `DailyBriefInput`, `DailyBriefReport`, `DailyBriefSection`, `DailyBriefItem`, `DailyBriefPriority`, `DailyBriefSummary`, `DailyBriefObservation`, `DailyBriefUnknown`, `DailyBriefEvidenceLink`

**Notable:** `render_daily_brief_report` is in `engine.py` but not exported from `__init__.py` — imported directly by CLI and tests. This is intentional (renderer is presentation-layer, not part of the capability contract).

**Key methods:** `DailyBriefCapability.generate(brief_input?) → DailyBriefReport`, `render_daily_brief_report(report) → str`, `build_daily_brief_input(**kwargs) → DailyBriefInput`

**Dependencies:**
- `atlas.domains.research` — `ResearchProject`, `ResearchQuestionStatus` (in input_builder and research_exporter)
- No other external Atlas imports — `DailyBriefInput` accepts `object | None` for portfolio_summary, company_reports, watchlist_report, discovery_report (loose coupling by design)

**Production callers:**
- `atlas/cli/main.py` — `DailyBriefCapability`, `build_daily_brief_input`, `render_daily_brief_report`, JSON loaders, `research_projects_to_dict`, `company_reports_to_list`
- `atlas/domains/daily_brief/__init__.py` — domain namespace placeholder; `__all__ = []`; does NOT re-export capability

**Test callers:** Many — primary capability tested in `test_daily_brief_capability.py`, `test_daily_brief_input_builder.py`, `test_daily_brief_priority_routing.py`, `test_daily_brief_output_readability.py`, `test_daily_brief_opening_summary.py`, `test_daily_brief_safely_wait.py`, `test_daily_brief_demo.py`, `test_evidence_gap_resolver.py`, `test_research_export.py`

**Domain overlap note:** `atlas/domains/daily_brief/__init__.py` exists as a domain namespace placeholder with `__all__ = []`. It does not re-export from the capability. The comment says: "The Blueprint-aligned Daily Brief implementation lives in atlas.capabilities.daily_brief." This boundary is clean and intentional.

**Classification:** Active, foundational, runtime-facing, application-facing, primary demo target. No stale symbols. No provider coupling. Clean.

---

### `atlas/capabilities/discovery/` (686 lines total)

**Modules:**

| File | Lines | Public Symbols |
|---|---|---|
| `__init__.py` | 29 | 11 exports |
| `engine.py` | 499 | `DiscoveryEngine` + private helpers |
| `models.py` | 111 | 9 public dataclasses/enums |
| `exporter.py` | 47 | `discovery_report_to_dict` |

**Public exports (11):** `DiscoveryEngine`, `DiscoveryInput`, `DiscoveryReport`, `DiscoveryCandidate`, `DiscoveryPriority`, `DiscoveryReason`, `DiscoverySignal`, `DiscoveryUnknown`, `DiscoveryQuestion`, `DiscoveryContext`, `DiscoveryEvidenceLink`

**Key method:** `DiscoveryEngine.discover(discovery_input) → DiscoveryReport`

**Dependencies:**
- `atlas.capabilities.company_analysis` — `CompanyAnalysisReport` (cross-capability)
- `atlas.capabilities.watchlist_intelligence` — `WatchlistIntelligenceReport` (cross-capability)
- `atlas.domains.knowledge` — `KnowledgeFact`
- `atlas.domains.research` — `ResearchProject`, `ResearchQuestionStatus`, `summarize_research`

**Cross-capability dependency note:** `DiscoveryInput` accepts `CompanyAnalysisReport` and `WatchlistIntelligenceReport` tuples. `DiscoveryEngine` synthesizes across capabilities. This is intentional architecture — discovery is the aggregating capability. No circular dependency (company_analysis and watchlist_intelligence do not import discovery).

**Production callers:**
- `atlas/cli/main.py` — `DiscoveryEngine`, `DiscoveryInput`, `discovery_report_to_dict`

**Test callers:** `test_discovery_capability.py`, `test_capability_export_inputs.py`, `test_capability_json_export.py`, `test_daily_brief_input_builder.py`

**Classification:** Active, runtime-facing, application-facing, aggregating capability. Cross-capability deps are intentional and stable. No stale symbols. No provider coupling. Clean.

---

### `atlas/capabilities/watchlist_intelligence/` (545 lines total)

**Modules:**

| File | Lines | Public Symbols |
|---|---|---|
| `__init__.py` | 33 | 13 exports |
| `engine.py` | 300 | `WatchlistIntelligenceEngine` + private helpers |
| `models.py` | 155 | 12 public dataclasses/enums + JSON file loading |
| `exporter.py` | 57 | `watchlist_report_to_dict` |

**Public exports (13):** `WatchlistIntelligenceEngine`, `WatchlistIntelligenceInput`, `WatchlistIntelligenceReport`, `WatchlistInput`, `WatchlistInputItem`, `WatchlistItem`, `WatchlistObservation`, `WatchlistPriority`, `WatchlistQuestion`, `WatchlistSignal`, `WatchlistStatus`, `WatchlistUnknown`, `WatchlistEvidenceLink`

**Notable:** `WatchlistInput.from_json_file()` and `from_mapping()` — JSON file loading is baked into the model. This is a minor boundary note: models have file I/O (`json.load`). Not a bug, but distinct from other capability models that are pure dataclasses.

**Key method:** `WatchlistIntelligenceEngine.analyze(watchlist_input) → WatchlistIntelligenceReport`

**Dependencies:**
- `atlas.capabilities.company_analysis` — `CompanyAnalysisReport` (cross-capability, optional field on `WatchlistItem`)
- `atlas.domains.knowledge` — `KnowledgeFact`
- `atlas.domains.research` — `ResearchProject`, `ResearchQuestionStatus`, `summarize_research`
- `atlas.shared` — `Company`

**Production callers:**
- `atlas/cli/main.py` — `WatchlistInput`, `WatchlistIntelligenceEngine`, `WatchlistIntelligenceInput`, `watchlist_report_to_dict`
- `atlas/conversation/engine.py` — `WatchlistIntelligenceEngine`, `WatchlistInput`, `WatchlistIntelligenceInput`
- `atlas/decision/decision_engine.py` — `WatchlistIntelligenceEngine`
- `atlas/decision/decision_context.py` — `WatchlistInput`
- `atlas/decision/decision_result.py` — `WatchlistIntelligenceReport`
- `atlas/intelligence/engine.py` — `WatchlistIntelligenceEngine`, `WatchlistInput`
- `atlas/monitoring/engine.py` — `WatchlistIntelligenceEngine`, `WatchlistInput`
- `atlas/home/engine.py` — `WatchlistInput`
- `atlas/watchlist_review/engine.py` — `WatchlistInput`, `WatchlistInputItem`
- `atlas/adapters/watchlist.py` — builds `WatchlistIntelligenceInput`, `WatchlistItem`, `WatchlistStatus`
- `atlas/capabilities/discovery/` — `WatchlistIntelligenceReport` used in discovery input/engine

**Classification:** Active, foundational, runtime-facing, domain-adjacent, heavily used across 9+ production modules. `WatchlistInput.from_json_file()` is a minor file-I/O coupling in models — low risk, leave unchanged. Clean.

---

## Caller Map Summary

| Capability | Production Callers | Test Files |
|---|---|---|
| `company_analysis` | CLI, adapters, discovery, watchlist_intelligence | 6+ test files |
| `daily_brief` | CLI (primary), demo | 9+ test files |
| `discovery` | CLI | 4+ test files |
| `watchlist_intelligence` | CLI, conversation, decision×3, intelligence, monitoring, home, watchlist_review, adapters, discovery | 6+ test files |
| `portfolio_intelligence` | CLI (indirect via portfolio_app), conversation, dashboard, decision, intelligence, risk_drift, suitability, providers×2 | 8+ test files |

---

## Capability / Domain Boundary Review

| Import | Direction | Assessment |
|---|---|---|
| `atlas.shared.Company` | capability → shared entity | ✓ Correct — shared entities flow into capabilities |
| `atlas.shared.entities.Holding/Portfolio` | capability → shared entity | ✓ Correct — portfolio_intelligence only |
| `atlas.domains.decision.Evidence` | capability → domain | ✓ Acceptable — company_analysis accepts decision context as input type |
| `atlas.domains.knowledge.KnowledgeFact` | capability → domain | ✓ Correct — foundational domain entity |
| `atlas.domains.research.ResearchProject` | capability → domain | ✓ Correct — capabilities consume domain research structures |
| `atlas.domains.research.summarize_research` | capability → domain function | ✓ Acceptable — domain utility function |
| `atlas.capabilities.company_analysis → watchlist_intelligence/discovery` | cross-capability | ✓ Intentional — discovery aggregates; watchlist optionally holds company analysis |
| `atlas.capabilities.watchlist_intelligence → discovery` | cross-capability | ✓ Intentional — discovery aggregates watchlist reports |

**No circular dependencies found.** Dependency direction is consistently: `domains/shared → capabilities`. No capability imports from `atlas.adapters`, `atlas.analysis`, `atlas.reasoning`, `atlas.providers`, `atlas.decision` (legacy), `atlas.intelligence`, `atlas.conversation`, or `atlas.dashboard`.

---

## Provider Boundary Review

- **No capability imports `atlas.providers` directly** ✓
- **No capability calls `requests`, `urllib.request`, or any network library** ✓
- `atlas/providers/base.py` and `atlas/providers/mock.py` and `atlas/providers/yahoo.py` import *from* `atlas.capabilities.portfolio_intelligence` (`PortfolioFitInput`) — dependency flows correctly from providers *into* capability types, not the reverse
- Provider boundary is unchanged and correct

---

## Stale Import Audit

All stale symbol hits in `atlas/capabilities/` are documentation-only (docstrings and comments in `atlas/capabilities/portfolio_intelligence/`). Classified:

| Hit | File | Classification |
|---|---|---|
| `atlas.analysis.portfolio` | `portfolio_intelligence/__init__.py` docstring | Migration history note — no import |
| `CompanyPortfolioProfile` | `portfolio_intelligence/models.py` docstring | Field mapping table — no import |
| `PortfolioAnalysis` | `portfolio_intelligence/models.py` docstring | Field mapping table — no import |
| `PortfolioSignal` | `portfolio_intelligence/models.py` docstring | Legacy context note — no import |
| `PortfolioRecommendation` | `portfolio_intelligence/models.py` docstring | Migration note — no import |
| `PortfolioIntelligenceEngine` | `portfolio_intelligence/engine.py` docstring | "Does NOT import" note — no import |

**No active stale runtime imports found anywhere in `atlas/capabilities/`.**

---

## Export Review

| Subpackage | Export count | All active? | Stale exports? |
|---|---|---|---|
| `capabilities/__init__.py` | 4 (subpackage names) | ✓ | None |
| `company_analysis` | 9 | ✓ | None |
| `daily_brief` | 11 | ✓ | None |
| `discovery` | 11 | ✓ | None |
| `watchlist_intelligence` | 13 | ✓ | None |
| `portfolio_intelligence` | 4 | ✓ | None (closed subtrack) |

All 52 total exports across all capability subpackages are active and used in production.

---

## Blueprint / Domain Overlap Review

| Capability | Blueprint-aligned? | Domain overlap? | Assessment |
|---|---|---|---|
| `company_analysis` | ✓ Yes | Consumes `atlas.domains.decision/knowledge/research` types | Clean — capability wraps domain types, no overlap |
| `daily_brief` | ✓ Yes | `atlas/domains/daily_brief/` is an empty placeholder | `domains/daily_brief` is intentionally empty; capability owns implementation |
| `discovery` | ✓ Yes | None | Clean |
| `watchlist_intelligence` | ✓ Yes | None | Clean |
| `portfolio_intelligence` | ✓ Yes | None | Clean (closed subtrack) |

No capability duplicates domain behavior. No capability should be moved or consolidated. All capability boundaries are clear.

---

## Cleanup Candidate Classification

After full inventory, no cleanup candidates were identified.

| Area | Classification | Evidence | Action |
|---|---|---|---|
| All exports | Leave unchanged | All 52 exports have active callers | None |
| `render_daily_brief_report` (not in `__init__`) | Leave unchanged | CLI/tests import directly — intentional presentation-layer separation | None |
| `WatchlistInput.from_json_file()` in models | Leave unchanged | File I/O in model is a minor boundary note, not a bug; removing would be behavioral | None |
| `portfolio_intelligence/` subtrack | Already closed (Sprint 171) | Verified stable | Do not reopen |
| Stale symbols in portfolio_intelligence docstrings | Leave unchanged | Documentation-only, no runtime impact, migration history is valuable | None |

**No zero-caller symbols, stale exports, dead private helpers, or provider boundary issues found.**

---

## Technical Debt Summary

`atlas/capabilities/` is in excellent shape:

- All 5 subpackages are structurally clean
- All 52 exports are active
- No stale imports anywhere
- No provider coupling
- No circular dependencies
- No duplicate functionality between capabilities
- No overlap with domain layer beyond correct dependency direction
- `WatchlistInput.from_json_file()` — minor note: file I/O in a model class, not a risk but slightly atypical. Low priority.

---

## Recommended Sprint 177 Target

**Audit `atlas/domains/` package.**

After completing the capabilities package audit with no cleanup warranted, the next high-leverage target is the domain layer that capabilities depend on. `atlas/domains/` is the foundational Blueprint layer; auditing it will identify whether any domain modules are stale, whether domain exports are clean, and whether any domain/capability boundary issues remain hidden. This follows the natural audit path: capabilities → domains → adapters → shared.

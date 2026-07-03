# Atlas Adapters Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 178)
**Status:** AUDIT COMPLETE — no cleanup warranted. Sprint 179 recommended: Audit `atlas/company_analysis/` package.

---

## Package Overview

`atlas/adapters/` contains 5 adapter modules totaling 750 lines. No subpackages — all modules are at the flat top level. The package is the translation layer between external/legacy JSON input formats and Blueprint-aligned domain/capability types.

| Module | Lines | Public Symbols | Role |
|---|---|---|---|
| `company_analysis.py` | 208 | `company_reports_from_dict` | JSON → `CompanyAnalysisReport` tuples |
| `portfolio.py` | 140 | `Portfolio`, `PortfolioPosition`, `legacy_portfolio_to_domain_portfolio` | Legacy JSON → domain portfolio types |
| `watchlist.py` | 198 | `watchlist_input_from_dict`, `assign_knowledge_facts` | JSON → `WatchlistIntelligenceInput` |
| `research_input.py` | 111 | `research_projects_from_dict` | JSON → `ResearchProject` tuples |
| `knowledge.py` | 93 | `knowledge_facts_from_dict` | JSON → `KnowledgeFact` tuples |
| `__init__.py` | 6 | (no exports — docstring only) | Namespace + design note |

**Total: 756 lines**

---

## `atlas/adapters/__init__.py` (6 lines)

Docstring only — no imports, no exports. States the adapter contract:
> "Adapters bridge legacy runtime data shapes to Blueprint-aligned domains. Adapters are the only layer allowed to import both legacy modules and `atlas.domains`/`atlas.shared`. They must stay deterministic, must not call external APIs, and must not mutate persisted data."

No `__all__` is defined — all adapters are imported by callers directly by module path.

---

## Module Inventory

### `atlas/adapters/company_analysis.py` (208 lines)

**Public symbols:** `company_reports_from_dict(data, source) → tuple[CompanyAnalysisReport, ...]`

**Private helpers:** `_parse_report`, `_parse_company`, `_parse_unknowns`, `_parse_evidence_links`, `_parse_confidence`, `_parse_string_list` — all internal parsing helpers (6 total)

**Imports:**
- `atlas.capabilities.company_analysis.models` — `CompanyAnalysisConfidence`, `CompanyAnalysisEvidenceLink`, `CompanyAnalysisReport`, `CompanyAnalysisSection`, `CompanyAnalysisUnknown`
- `atlas.shared` — `Company`

**Dependency direction:** adapter → capability models + shared entity. Acceptable — this adapter translates external JSON *into* capability types, not back to legacy types.

**Production callers:**
- `atlas/cli/main.py` — `company_reports_from_dict`

**Test callers:** `test_company_analysis_export.py`

**Classification:** Active, adapter/translation layer, CLI-facing. No stale symbols. No provider coupling. No network access. Clean.

---

### `atlas/adapters/portfolio.py` (140 lines)

**Public symbols:**
- `Portfolio` (dataclass) — legacy CLI portfolio boundary type; equivalent of former `atlas.analysis.portfolio.Portfolio` (deleted Sprint 135)
- `PortfolioPosition` (dataclass) — one position in a legacy CLI portfolio JSON file
- `legacy_portfolio_to_domain_portfolio(legacy_portfolio, portfolio_id?, portfolio_name?) → SharedPortfolio` — translation function

**Constants:** `DEFAULT_PORTFOLIO_ID`, `DEFAULT_PORTFOLIO_NAME`

**Private helpers:** `_position_from_mapping`, `_normalize_weight`

**Imports:**
- `atlas.analysis.scores` — `clamp_score`
- `atlas.shared` — `Holding`, `Portfolio as SharedPortfolio`

**⚠️ Notable import — `atlas.analysis.scores`:**
`atlas/adapters/portfolio.py` imports `clamp_score` from `atlas.analysis.scores`. This is **correct and intentional**:
- `atlas.analysis.scores` is a 2-line active utility module (`def clamp_score(score: int) -> int: return max(0, min(100, score))`)
- It was **not** deleted in the Sprint 141 analysis cleanup track — Sprint 140 explicitly established it as the active clamping utility, confirmed by `test_analysis_package_sprint140.py`
- `clamp_score` is used by 12+ modules across the codebase
- This is NOT a stale import

**Dependency direction:** adapter → `atlas.analysis.scores` (active utility) + `atlas.shared`. Acceptable.

**Portfolio boundary status:** CLOSED Sprint 148. Verified stable:
- `Portfolio` and `PortfolioPosition` remain importable ✓
- `legacy_portfolio_to_domain_portfolio` remains importable and callable ✓
- Deleted legacy symbols absent: `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation`, `CompanyPortfolioProfile`, `PortfolioIntelligenceEngine`, `portfolio_fit_input_from_profile` — none present ✓

**Production callers:**
- `atlas/cli/main.py` — `Portfolio`, `legacy_portfolio_to_domain_portfolio`
- `atlas/conversation/engine.py` — `legacy_portfolio_to_domain_portfolio`, `Portfolio` (type annotation)
- `atlas/dashboard/engine.py` — `legacy_portfolio_to_domain_portfolio`, `Portfolio` (type annotation)
- `atlas/decision/decision_context.py` — `Portfolio` (type annotation)
- `atlas/decision/decision_engine.py` — `legacy_portfolio_to_domain_portfolio`
- `atlas/home/engine.py` — `Portfolio` (type annotation)
- `atlas/intelligence/engine.py` — `legacy_portfolio_to_domain_portfolio`, `Portfolio` (type annotation)
- `atlas/monitoring/engine.py` — `Portfolio` (type annotation)
- `atlas/portfolio_review/engine.py` — `legacy_portfolio_to_domain_portfolio`, `Portfolio as LegacyPortfolio`
- `atlas/risk_drift/engine.py` — `Portfolio` (type annotation)
- `atlas/suitability/engine.py` — `Portfolio` (type annotation)

**Test callers:** Many — `test_portfolio.py`, `test_portfolio_adapter.py`, `test_portfolio_analyze_deprecation.py`, `test_portfolio_boundary_sprint147.py`, `test_portfolio_review.py`, `test_portfolio_review_migration.py`, `test_portfolio_runtime_migration.py`, `test_portfolio_analyze_migration.py`, `test_portfolio_intelligence_engine.py`, `test_daily_brief_demo.py`, `test_daily_brief_capability.py`, `test_daily_brief_input_builder.py`, `test_decision_engine.py`, `test_dashboard_engine.py`, `test_conversation_engine.py`, `test_home_engine.py`, `test_intelligence_engine.py`, `test_monitoring_engine.py`, `test_reasoning_engine.py`, `test_reasoning_package_sprint151.py`, `test_risk_drift_engine.py`, `test_risk_package_sprint154.py`, `test_suitability_engine.py`, `test_providers.py`, `test_evidence_package_sprint149.py`, `test_language_engine.py`

**Classification:** Active, foundational, adapter/translation layer. Most widely-used adapter (11 production callers). Portfolio boundary remains closed. Clean.

---

### `atlas/adapters/watchlist.py` (198 lines)

**Public symbols:**
- `watchlist_input_from_dict(data, source) → WatchlistIntelligenceInput`
- `assign_knowledge_facts(wi_input, knowledge_facts) → WatchlistIntelligenceInput`

**Private helpers:** `_parse_item`, `_parse_status`, `_node_id_matches_ticker` (note: `_node_id_matches_ticker` is also imported by tests directly — test-accessible private helper)

**Imports:**
- `atlas.capabilities.watchlist_intelligence.models` — `WatchlistIntelligenceInput`, `WatchlistItem`, `WatchlistStatus`
- `atlas.domains.knowledge.models` — `KnowledgeFact`
- `atlas.domains.research.models` — `ResearchProject`, `ResearchQuestion`, `ResearchQuestionStatus`, `ResearchStatus`

**Dependency direction:** adapter → capability models + domain models. Acceptable — this adapter translates watchlist JSON into capability input types, bridging domain types for open questions.

**Production callers:**
- `atlas/cli/main.py` — `assign_knowledge_facts`, `watchlist_input_from_dict`

**Test callers:** `test_capability_export_inputs.py`, `test_daily_brief_demo.py` (also imports `_node_id_matches_ticker` directly)

**Classification:** Active, adapter/translation layer, CLI-facing. No stale symbols. No provider coupling. Clean.

---

### `atlas/adapters/research_input.py` (111 lines)

**Public symbols:** `research_projects_from_dict(data, source) → tuple[ResearchProject, ...]`

**Private helpers:** `_parse_project`, `_parse_status`

**Imports:**
- `atlas.domains.research.models` — `ResearchProject`, `ResearchQuestion`, `ResearchQuestionStatus`, `ResearchStatus`

**Dependency direction:** adapter → domain models only. Cleanest dependency surface of any adapter.

**Production callers:**
- `atlas/cli/main.py` — `research_projects_from_dict`

**Test callers:** `test_capability_export_inputs.py`, `test_research_export.py`

**Classification:** Active, adapter/translation layer, CLI-facing. No stale symbols. No provider coupling. Clean.

---

### `atlas/adapters/knowledge.py` (93 lines)

**Public symbols:** `knowledge_facts_from_dict(data, source) → tuple[KnowledgeFact, ...]`

**Private helpers:** `_parse_fact`

**Imports:**
- `atlas.domains.knowledge.models` — `KnowledgeFact`, `KnowledgeReference`, `KnowledgeSource`

**Dependency direction:** adapter → domain models only. Clean.

**Production callers:**
- `atlas/cli/main.py` — `knowledge_facts_from_dict`

**Test callers:** `test_capability_export_inputs.py`, `test_daily_brief_demo.py`

**Classification:** Active, adapter/translation layer, CLI-facing. No stale symbols. No provider coupling. Clean.

---

## Adapter Export Review

`atlas/adapters/__init__.py` has no exports (`__all__` not defined, no imports). All adapters are consumed by callers importing directly from the module path (e.g., `from atlas.adapters.portfolio import Portfolio`). This is correct — adapters are not re-exported from a common namespace.

No stale exports. No exports to add or remove.

---

## Caller Map Summary

| Adapter | Production Callers | Test Callers |
|---|---|---|
| `company_analysis` | CLI (1) | 1 test file |
| `portfolio` | CLI + 10 runtime engines | 25+ test files |
| `watchlist` | CLI (2 symbols) | 2 test files |
| `research_input` | CLI (1) | 2 test files |
| `knowledge` | CLI (1) | 2 test files |

All adapter functions have active production callers. No zero-caller symbols.

---

## Portfolio Boundary Review

Portfolio boundary cleanup track — **CLOSED Sprint 148** — remains closed and stable.

| Check | Status |
|---|---|
| `Portfolio` importable from `atlas.adapters.portfolio` | ✓ |
| `PortfolioPosition` importable from `atlas.adapters.portfolio` | ✓ |
| `legacy_portfolio_to_domain_portfolio` importable and callable | ✓ |
| `PortfolioAnalysis` absent | ✓ |
| `PortfolioSignal` absent | ✓ |
| `PortfolioRecommendation` absent | ✓ |
| `CompanyPortfolioProfile` absent | ✓ |
| `PortfolioIntelligenceEngine` absent | ✓ |
| `portfolio_fit_input_from_profile` absent | ✓ |
| `atlas.analysis.portfolio` not imported by adapter | ✓ |

---

## Adapter / Domain / Capability Boundary Review

| Import | In module | Direction | Assessment |
|---|---|---|---|
| `atlas.capabilities.company_analysis.models` | `company_analysis.py` | adapter → capability | ✓ Acceptable — builds capability types from JSON |
| `atlas.capabilities.watchlist_intelligence.models` | `watchlist.py` | adapter → capability | ✓ Acceptable — builds capability types from JSON |
| `atlas.domains.knowledge.models` | `knowledge.py`, `watchlist.py` | adapter → domain | ✓ Correct |
| `atlas.domains.research.models` | `research_input.py`, `watchlist.py` | adapter → domain | ✓ Correct |
| `atlas.shared` | `company_analysis.py`, `portfolio.py` | adapter → shared entity | ✓ Correct |
| `atlas.analysis.scores` | `portfolio.py` | adapter → active utility | ✓ Correct — `clamp_score` is an active retained utility |

**No circular dependencies.** No adapter imports CLI, providers, or application orchestration packages. Boundary is clean.

---

## Provider Boundary Review

- **No adapter imports `atlas.providers`** ✓
- **No adapter imports `requests`, `urllib`, or any network library** ✓
- **No adapter performs network access** ✓

All adapters are explicitly documented as "deterministic, side-effect free, and make no network calls."

---

## Stale Import Audit

No stale imports found in `atlas/adapters/`. All stale symbol hits classified:

| Symbol | Location | Classification |
|---|---|---|
| `atlas.analysis.portfolio` | `portfolio.py` docstring | Migration history note — no import |
| `atlas.analysis.scores` | `portfolio.py` import | **Active utility** — not deleted, confirmed Sprint 140 |
| `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation` | test files | Migration guardrails confirming absence |
| `CompanyPortfolioProfile`, `portfolio_fit_input_from_profile` | test files | Migration guardrails confirming absence |

No active stale runtime imports.

---

## Blueprint / Adapter Model Review

All 5 adapter modules are Blueprint-aligned:

| Adapter | Blueprint-aligned? | Owns business logic? | Notes |
|---|---|---|---|
| `company_analysis` | ✓ | No — pure JSON parsing | Translates JSON → capability types |
| `portfolio` | ✓ | No — pure type mapping | Owns `Portfolio`/`PortfolioPosition` boundary types; `_normalize_weight` is normalization, not business logic |
| `watchlist` | ✓ | No — pure translation | Constructs `ResearchProject` from open questions — simple mapping |
| `research_input` | ✓ | No — pure JSON parsing | Cleanest boundary |
| `knowledge` | ✓ | No — pure JSON parsing | Cleanest boundary |

No adapter duplicates a domain model. No adapter owns business logic. No migration warranted.

---

## Cleanup Candidate Classification

No cleanup candidates found.

| Area | Classification | Action |
|---|---|---|
| All 7 public adapter functions/classes | Leave unchanged | All have active production callers |
| `atlas.analysis.scores` import in `portfolio.py` | Leave unchanged | Active utility, not deleted |
| `_node_id_matches_ticker` (test-accessible private) | Leave unchanged | Used in test; explicit matching logic; not dead |
| Portfolio boundary types | Leave unchanged | CLOSED Sprint 148, still needed by 11 runtime engines |
| No `__all__` in `__init__.py` | Leave unchanged | Correct — adapters consumed by direct module path |

---

## Technical Debt Summary

`atlas/adapters/` has no meaningful technical debt:

- 5 modules, all active, all with production callers
- 7 public symbols, all active
- No stale imports
- No provider coupling
- No CLI coupling
- No upward dependencies (no adapter imports from application orchestration)
- No business logic in adapters
- Portfolio boundary cleanup track remains closed and stable
- `atlas.analysis.scores.clamp_score` is an active utility correctly imported

---

## Recommended Sprint 179 Target

**Audit `atlas/company_analysis/` package.**

After auditing capabilities (Sprint 176), domains (Sprint 177), and adapters (Sprint 178) with no cleanup warranted across all three, the next highest-leverage audit target is `atlas/company_analysis/` — the legacy company analysis runtime package. This is part of `atlas/analysis/` adjacent territory that was partially cleaned up in Sprint 141 but may have remaining modules worth reviewing, and is directly referenced by CLI command `company-analysis`. Auditing it will establish whether any company analysis runtime symbols are stale, whether the boundary with `atlas/capabilities/company_analysis/` is clean, and whether any consolidation is warranted.

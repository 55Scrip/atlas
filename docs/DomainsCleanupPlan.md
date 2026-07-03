# Atlas Domains Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 177)
**Status:** AUDIT COMPLETE — no cleanup warranted. Sprint 178 recommended: Audit `atlas/adapters/` package.

---

## Package Overview

`atlas/domains/` contains 9 subpackages totaling ~1,730 lines. This is the Blueprint-aligned domain layer — the foundational contracts on which capabilities and runtime orchestration are built.

| Subpackage | Lines | Modules | Status |
|---|---|---|---|
| `decision/` | 375 | `__init__`, `engine.py`, `models.py` | Active, foundational |
| `knowledge/` | 348 | `__init__`, `models.py`, `query.py`, `relationships.py` | Active, foundational |
| `portfolio/` | 560 | `__init__`, `models.py`, `calculations.py`, `review.py`, `validation.py` | Active, foundational |
| `research/` | 380 | `__init__`, `models.py`, `summary.py`, `validation.py` | Active, foundational |
| `ai/` | 20 | `__init__` only | Active — re-exports Protocol interfaces from `atlas.ai` |
| `authentication/` | 8 | `__init__` only | Active — thin re-export of `User` from `atlas.shared` |
| `daily_brief/` | 10 | `__init__` only | Active — intentional empty placeholder |
| `decision_journal/` | 8 | `__init__` only | Active — thin re-export of `JournalEntry` from `atlas.shared` |
| `watchlist/` | 8 | `__init__` only | Active — thin re-export of `Watchlist` from `atlas.shared` |
| `__init__.py` | 13 | Top-level namespace | Active |

**Total: ~1,730 lines**

---

## Domain Inventory by Subpackage

### `atlas/domains/__init__.py` (13 lines)

- **Exports:** `__all__` = `["ai", "authentication", "decision", "daily_brief", "decision_journal", "knowledge", "portfolio", "research", "watchlist"]`
- Namespace-only — no symbols re-exported at top level
- Status: Active, correct

---

### `atlas/domains/decision/` (375 lines)

**Modules:**

| File | Lines | Public Symbols |
|---|---|---|
| `__init__.py` | 36 | 14 exports |
| `engine.py` | 192 | `EvidenceEngine`, `ReasoningEngine`, `DecisionEngine` + 6 private helpers |
| `models.py` | 147 | 10 public dataclasses/enums + 2 private helpers |

**Public exports (14):** `Confidence`, `Decision`, `DecisionCard`, `DecisionContext`, `DecisionEngine`, `DecisionResult`, `Evidence`, `EvidenceCategory`, `EvidenceEngine`, `EvidenceStrength`, `Observation`, `ReasoningEngine`, `ReasoningStep`, `Unknown`

**Key classes:**
- `EvidenceEngine.collect(context) → tuple[Evidence, ...]` — sorts and collects evidence
- `ReasoningEngine.reason(context) → DecisionResult` — deterministic reasoning from evidence
- `DecisionEngine.evaluate(context) → DecisionCard` — top-level non-advisory decision card

**⚠️ IMPORTANT — ReasoningEngine identity:**
`atlas.domains.decision.engine.ReasoningEngine` is a **distinct active Blueprint-layer class**. It is NOT the deleted `atlas.reasoning.ReasoningEngine`. All hits classified:
- `atlas/domains/decision/__init__.py` — exports active `ReasoningEngine` ✓
- `atlas/domains/decision/engine.py` — defines active `ReasoningEngine` ✓
- `tests/test_decision_domain.py` — tests active class ✓
- `tests/test_rc_checkpoint_sprint163.py` — Sprint 163 guardrail confirming it's distinct ✓
- `tests/test_reason_analyze_deprecation.py` — confirms CLI does NOT import it from `atlas.reasoning` ✓
- `tests/test_intelligence_package_sprint164.py` — documents the distinction in comments ✓

**Dependencies:**
- `atlas.shared` — none directly; all domain-internal
- `atlas.domains.decision.models` — internal sibling import only
- No external Atlas imports

**Production callers:**
- `atlas/capabilities/company_analysis/models.py` — `Evidence` type used as input field
- `atlas/cli/main.py` — indirectly via `atlas.decision.AtlasDecisionEngine` which wraps this domain
- `tests/test_decision_domain.py` — direct domain tests

**Classification:** Active, foundational, pure domain layer. No stale symbols. No provider coupling. No upward dependencies. Clean.

---

### `atlas/domains/knowledge/` (348 lines)

**Modules:**

| File | Lines | Public Symbols |
|---|---|---|
| `__init__.py` | 32 | 10 exports |
| `models.py` | 118 | 7 public dataclasses/enums + 2 private helpers |
| `query.py` | 104 | `KnowledgeQueryService` + 1 private helper |
| `relationships.py` | 94 | `KnowledgeRelationshipEngine` + 1 private helper |

**Public exports (10):** `KnowledgeCollection`, `KnowledgeEdge`, `KnowledgeFact`, `KnowledgeNode`, `KnowledgeNodeType`, `KnowledgeQueryService`, `KnowledgeReference`, `KnowledgeRelationship`, `KnowledgeRelationshipEngine`, `KnowledgeSource`

**Dependencies:**
- `atlas.shared` — `KnowledgeNode` (shared entity)
- `atlas.domains.knowledge.models` — internal sibling imports only

**Production callers:**
- `atlas/capabilities/company_analysis/models.py` — `KnowledgeFact`
- `atlas/capabilities/discovery/engine.py` — `KnowledgeFact`
- `atlas/capabilities/discovery/models.py` — `KnowledgeFact`
- `atlas/capabilities/watchlist_intelligence/models.py` — `KnowledgeFact`
- `atlas/adapters/knowledge.py` — `KnowledgeFact`, `KnowledgeReference`, `KnowledgeSource`
- `atlas/adapters/watchlist.py` — `KnowledgeFact`

**Test callers:** `test_knowledge_domain.py`, `test_capability_json_export.py`, `test_company_analysis_capability.py`, `test_discovery_capability.py`, `test_watchlist_intelligence_capability.py`, `test_capability_export_inputs.py`

**Classification:** Active, foundational, pure domain layer, most widely-consumed domain type (`KnowledgeFact`). No stale symbols. No provider coupling. Clean.

---

### `atlas/domains/portfolio/` (560 lines)

**Modules:**

| File | Lines | Public Symbols |
|---|---|---|
| `__init__.py` | 61 | 21 exports |
| `models.py` | 109 | 8 public dataclasses/enums |
| `calculations.py` | 174 | 10 public functions |
| `review.py` | 106 | `PortfolioReviewEngine` + 2 private helpers |
| `validation.py` | 110 | `validate_portfolio` + `ALLOWED_STATUS_TRANSITIONS` (not exported) |

**Public exports (21):** `Allocation`, `Concentration`, `ConcentrationLevel`, `Holding`, `Portfolio`, `PortfolioDomainReview`, `PortfolioIssueSeverity`, `PortfolioObservation`, `PortfolioReviewEngine`, `PortfolioSnapshot`, `PortfolioSummary`, `PortfolioValidationIssue`, `PortfolioValidationResult`, `cash_weight`, `concentration_level`, `country_allocation`, `holding_market_value`, `holding_weight`, `largest_position`, `portfolio_summary`, `sector_allocation`, `top_holdings`, `total_portfolio_value`, `validate_portfolio`

**Dependencies:**
- `atlas.shared` — `Holding`, `Portfolio`, `EntityValue`
- `atlas.domains.portfolio.{models,calculations,validation}` — internal sibling imports

**Production callers:**
- `atlas/cli/main.py` — `portfolio_summary` (imported as `domain_portfolio_summary`)
- `atlas/adapters/portfolio.py` — uses portfolio domain types (docs describe it)
- `tests/` — `test_portfolio_domain.py`, `test_portfolio_review_deprecation.py`, `test_portfolio_analyze_migration.py`, `test_portfolio_review_migration.py`, `test_portfolio_runtime_migration.py`, `test_daily_brief_capability.py`, `test_daily_brief_demo.py`, `test_daily_brief_input_builder.py`, `test_watchlist_analyze_deprecation.py`

**Note:** `atlas/cli/deprecations.py` references `atlas.domains.portfolio.review.PortfolioReviewEngine` in retirement metadata text — this is documentation of the Blueprint-aligned replacement, not a stale import.

**Classification:** Active, foundational, pure domain layer, most exports of any domain. No stale symbols. No provider coupling. Clean.

---

### `atlas/domains/research/` (380 lines)

**Modules:**

| File | Lines | Public Symbols |
|---|---|---|
| `__init__.py` | 44 | 15 exports |
| `models.py` | 137 | 11 public dataclasses/enums |
| `summary.py` | 66 | `summarize_research` + 3 private helpers |
| `validation.py` | 133 | `validate_research_project`, `is_valid_status_transition`, `ALLOWED_STATUS_TRANSITIONS` |

**Public exports (15):** `ResearchAssumption`, `ResearchEvidenceReference`, `ResearchIssueSeverity`, `ResearchNote`, `ResearchProject`, `ResearchQuestion`, `ResearchQuestionStatus`, `ResearchStatus`, `ResearchSummary`, `ResearchValidationIssue`, `ResearchValidationResult`, `ThesisFragment`, `is_valid_status_transition`, `summarize_research`, `validate_research_project`

**Dependencies:**
- `atlas.shared` — `ResearchNote`
- `atlas.domains.research.models` — internal sibling imports only

**Production callers:**
- `atlas/capabilities/company_analysis/engine.py` — `ResearchQuestionStatus`, `summarize_research`
- `atlas/capabilities/company_analysis/models.py` — `ResearchProject`
- `atlas/capabilities/daily_brief/input_builder.py` — `ResearchProject`, `ResearchQuestionStatus`
- `atlas/capabilities/daily_brief/research_exporter.py` — `ResearchProject`, `ResearchQuestionStatus`
- `atlas/capabilities/discovery/engine.py` — `ResearchProject`, `ResearchQuestionStatus`, `summarize_research`
- `atlas/capabilities/discovery/models.py` — `ResearchProject`
- `atlas/capabilities/watchlist_intelligence/engine.py` — `ResearchQuestionStatus`, `summarize_research`
- `atlas/capabilities/watchlist_intelligence/models.py` — `ResearchProject`
- `atlas/adapters/research_input.py` — research domain models
- `atlas/adapters/watchlist.py` — `ResearchProject`, `ResearchQuestion`, `ResearchQuestionStatus`, `ResearchStatus`

**Classification:** Active, foundational, pure domain layer, second-most-consumed domain (used by 4 capabilities and 2 adapters). No stale symbols. No provider coupling. Clean.

---

### `atlas/domains/ai/` (20 lines)

**Module:** `__init__.py` only.

**What it does:** Re-exports `atlas.ai` Protocol interfaces (`DecisionEngine`, `DiscoveryService`, `KnowledgeService`, `ReasoningService`, `SummaryService`) under the `atlas.domains.ai` namespace.

**`atlas.ai`:** Lives at `atlas/ai/interfaces.py` — 5 `@runtime_checkable` Protocol classes with stub methods. No implementation. No network calls. Pure interface contracts for future AI service integration.

**Production callers:** `tests/test_atlas_foundation.py` only — imports `atlas.ai` directly (not via `atlas.domains.ai`).

**Classification:** Active, interface-only, future-boundary placeholder. No implementations. No provider coupling. No stale symbols. **Test-adjacent** — only tested in `test_atlas_foundation.py`. No production runtime caller of `atlas.domains.ai` symbols. Leave unchanged.

---

### `atlas/domains/authentication/` (8 lines)

**What it does:** Thin namespace — re-exports `User` from `atlas.shared`.

**Production callers:** `tests/test_atlas_foundation.py` imports the `authentication` subpackage by name (namespace import only).

**Classification:** Active, thin namespace, shared entity boundary marker. No stale symbols. No production runtime caller (test-adjacent). Leave unchanged.

---

### `atlas/domains/daily_brief/` (10 lines)

**What it does:** Intentional empty placeholder. Comment states: "The Blueprint-aligned Daily Brief implementation lives in `atlas.capabilities.daily_brief`." `__all__ = []`.

**Classification:** Active intentional empty placeholder. Correct — the capability owns the implementation. Leave unchanged.

---

### `atlas/domains/decision_journal/` (8 lines)

**What it does:** Thin namespace — re-exports `JournalEntry` from `atlas.shared`.

**Production callers:** `tests/test_atlas_foundation.py` imports the `decision_journal` subpackage by name.

**Classification:** Active, thin namespace. No stale symbols. Leave unchanged.

---

### `atlas/domains/watchlist/` (8 lines)

**What it does:** Thin namespace — re-exports `Watchlist` from `atlas.shared`.

**Production callers:** `tests/test_atlas_foundation.py` imports the `watchlist` subpackage by name.

**Classification:** Active, thin namespace. No stale symbols. Leave unchanged.

---

## Domain Export Review

| Subpackage | Exports | All active? | Stale? |
|---|---|---|---|
| `domains/__init__.py` | 9 subpackage names | ✓ | None |
| `decision` | 14 | ✓ | None |
| `knowledge` | 10 | ✓ | None |
| `portfolio` | 21 | ✓ | None |
| `research` | 15 | ✓ | None |
| `ai` | 5 Protocol interfaces | ✓ (future boundary) | None |
| `authentication` | 1 (`User`) | ✓ | None |
| `daily_brief` | 0 (intentional empty) | ✓ | None |
| `decision_journal` | 1 (`JournalEntry`) | ✓ | None |
| `watchlist` | 1 (`Watchlist`) | ✓ | None |

All 68 domain exports are active. No stale exports found.

---

## Caller Map Summary

| Domain | Primary Production Callers |
|---|---|
| `decision` | `atlas/capabilities/company_analysis/models.py` (`Evidence`) |
| `knowledge` | 4 capabilities, 2 adapters (`KnowledgeFact` most consumed) |
| `portfolio` | `atlas/cli/main.py`, portfolio-domain tests |
| `research` | 4 capabilities, 2 adapters (`ResearchProject`, `summarize_research` most consumed) |
| `ai` | `tests/test_atlas_foundation.py` only |
| `authentication` | `tests/test_atlas_foundation.py` only |
| `daily_brief` | None (empty placeholder) |
| `decision_journal` | `tests/test_atlas_foundation.py` only |
| `watchlist` | `tests/test_atlas_foundation.py` only |

---

## Capability / Domain Boundary Review (from Domain Side)

**No domain module imports upward into capabilities, CLI, providers, or adapters.**

All external imports within `atlas/domains/` are either:
1. `atlas.shared` — correct (shared entities flow into domains)
2. `atlas.ai` — correct (`atlas/domains/ai/` re-exports Protocol interfaces from `atlas.ai`)
3. Internal sibling imports (e.g., `atlas.domains.portfolio.calculations`)

**Boundary direction is correct.** The domain layer is lower-level than capabilities/runtime/application packages. No violations found.

---

## Provider Boundary Review

- **No domain module imports `atlas.providers`** ✓
- **No domain module imports `requests`, `urllib`, or any network library** ✓
- **No domain module performs network access** ✓

Provider boundary is clean and unchanged.

---

## Stale Import Audit

No stale imports found anywhere in `atlas/domains/`. All search patterns (`atlas.reasoning`, `atlas.analysis.*`, deleted symbols) returned zero hits inside the domains package.

**`ReasoningEngine` classification:**
All hits of `ReasoningEngine` within domains are the **active** `atlas.domains.decision.engine.ReasoningEngine` — a distinct Blueprint-layer class. Not to be confused with the deleted `atlas.reasoning.ReasoningEngine`. Existing guardrail tests in `test_rc_checkpoint_sprint163.py` already document and verify this distinction.

---

## Blueprint / Domain Model Review

All 9 domain subpackages are Blueprint-aligned:

| Domain | Blueprint-aligned? | Used by capabilities? | Notes |
|---|---|---|---|
| `decision` | ✓ | ✓ (`Evidence` by company_analysis) | Foundation for `atlas.decision.AtlasDecisionEngine` runtime layer |
| `knowledge` | ✓ | ✓ (4 capabilities use `KnowledgeFact`) | Most consumed domain type |
| `portfolio` | ✓ | Indirectly via adapters | `portfolio_summary` used by CLI directly |
| `research` | ✓ | ✓ (4 capabilities) | Second-most consumed domain |
| `ai` | ✓ | No | Future-boundary Protocol interfaces only |
| `authentication` | ✓ | No | Thin namespace, `User` entity |
| `daily_brief` | ✓ | No (empty placeholder) | Implementation in `atlas.capabilities.daily_brief` |
| `decision_journal` | ✓ | No | Thin namespace, `JournalEntry` entity |
| `watchlist` | ✓ | No | Thin namespace, `Watchlist` entity |

No domain model duplicates a capability model. No domain module duplicates runtime-layer logic. All boundaries are clean.

---

## Cleanup Candidate Classification

After full inventory, no cleanup candidates were identified.

| Area | Classification | Evidence | Action |
|---|---|---|---|
| All domain exports (68 total) | Leave unchanged | All have active callers or are correct forward stubs | None |
| `atlas/domains/ai/` re-exports | Leave unchanged | Correct future-boundary namespace; Protocol interfaces are production-safe | None |
| `atlas/domains/daily_brief/` empty placeholder | Leave unchanged | Intentional design — implementation in `atlas.capabilities.daily_brief` | None |
| Thin re-export namespaces (`authentication`, `decision_journal`, `watchlist`) | Leave unchanged | Correct domain boundary markers for `atlas.shared` entities | None |
| `atlas.domains.decision.ReasoningEngine` | Leave unchanged | Active Blueprint-layer class; correctly exported; tested | None |
| All stale symbol searches | Leave unchanged (zero hits) | No stale imports in any domain module | None |

**No zero-caller symbols, stale exports, dead private helpers, upward dependencies, or provider boundary issues found.**

---

## Technical Debt Summary

`atlas/domains/` is in excellent architectural shape:

- 9 subpackages, all Blueprint-aligned
- 68 exports, all active (or correct future stubs)
- No stale imports
- No provider coupling
- No upward dependencies
- No circular dependencies
- Boundary direction correct throughout: `atlas.shared → atlas.domains → atlas.capabilities`
- `atlas/domains/ai/` is test-adjacent only but is a correct future-boundary namespace
- Thin re-export namespaces (`authentication`, `decision_journal`, `watchlist`) are correct pattern for shared entity domain ownership

No technical debt requiring cleanup.

---

## Recommended Sprint 178 Target

**Audit `atlas/adapters/` package.**

After auditing capabilities (Sprint 176) and domains (Sprint 177) with no cleanup warranted in either, the natural next audit target is the adapter layer that bridges domains and capabilities. `atlas/adapters/` sits at the boundary between domain types and application/capability consumers — auditing it will identify whether adapter modules are clean, whether any adapter has stale migration residue, and whether adapter/domain/capability boundaries are correct from the adapter side.

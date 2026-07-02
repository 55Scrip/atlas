# Atlas Portfolio Boundary Cleanup Plan

**Created:** 2026-07-02 (Sprint 147)  
**Updated:** 2026-07-02 (Sprint 148)  
**Status:** CLOSED — Sprint 148 removed the stale `PortfolioFitInput` import from `atlas/adapters/portfolio.py`. Adapter boundary is stable. `Portfolio` and `PortfolioPosition` remain intentionally in `atlas/adapters/portfolio.py`. `atlas.analysis.portfolio` remains deleted. No further portfolio boundary cleanup work is planned.

---

## Background

`atlas/analysis/portfolio.py` was deleted in Sprint 135. `Portfolio` and `PortfolioPosition` were moved to `atlas/adapters/portfolio.py` as permanent boundary types. All 12 production import sites were migrated in Sprint 135. The Sprint 147 audit verifies the caller surface is clean and identifies remaining technical debt.

Migration history:
- **Sprint 128:** Deleted `PortfolioIntelligenceEngine`
- **Sprint 132:** Deleted `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation`
- **Sprint 133:** Deleted `CompanyPortfolioProfile`; providers migrated to `PortfolioFitInput`
- **Sprint 135:** Moved `Portfolio` and `PortfolioPosition` to `atlas/adapters/portfolio.py`; deleted `atlas/analysis/portfolio.py`
- **Sprint 137:** Removed `portfolio_fit_input_from_profile` identity adapter
- **Sprint 141:** Closed `atlas/analysis/` cleanup track
- **Sprint 147:** Portfolio boundary caller audit (this document)

---

## Adapter Boundary Review (`atlas/adapters/portfolio.py`)

**Public symbols:**

| Symbol | Type | Responsibility |
|---|---|---|
| `PortfolioPosition` | frozen dataclass | One position from legacy CLI portfolio JSON |
| `Portfolio` | frozen dataclass | Legacy CLI portfolio; owns `from_json_file` and `from_mapping` |
| `legacy_portfolio_to_domain_portfolio` | function | Converts legacy `Portfolio` → `atlas.shared.Portfolio` |

**Private helpers:**

| Symbol | Responsibility |
|---|---|
| `_position_from_mapping` | Parse one position dict from JSON payload |
| `_normalize_weight` | Clamp weight to [0, 1] range |

**Imports:**
- `atlas.analysis.scores.clamp_score` — OK; `scores.py` is a retained analysis module
- `atlas.shared.Holding`, `Portfolio as SharedPortfolio` — OK; downstream domain types
- `atlas.capabilities.portfolio_intelligence.PortfolioFitInput` — **STALE** — imported but unused in the adapter body (line 33). Leftover from Sprint 133 `CompanyPortfolioProfile` → `PortfolioFitInput` migration.

**Boundary compliance:**
- Does NOT import from: CLI, decision, intelligence, dashboard, conversation, providers, monitoring
- Direction: adapter → shared → domains only ✓
- No upward dependencies ✓
- `Portfolio` and `PortfolioPosition` are the correct permanent home ✓

**Risk of moving Portfolio/PortfolioPosition now:** HIGH. 9 CLI call sites, 8 engine TYPE_CHECKING annotations, 6 runtime `legacy_portfolio_to_domain_portfolio` callers. The adapter is already the correct permanent home — no move warranted.

---

## Stale Import Audit

**Zero stale `atlas.analysis.portfolio` production imports.** All hits in grep output are:
- Test guardrails asserting module is NOT importable
- Docs/comment references
- `atlas/cli/deprecations.py` historical note string

**One stale import in adapter:**

| File | Import | Status |
|---|---|---|
| `atlas/adapters/portfolio.py:33` | `from atlas.capabilities.portfolio_intelligence import PortfolioFitInput` | **Stale — unused** |

`PortfolioFitInput` is not referenced anywhere in the adapter body. It was added during Sprint 133 when `CompanyPortfolioProfile` was replaced with `PortfolioFitInput` in the provider interface, but the adapter itself does not construct or consume `PortfolioFitInput`. Sprint 148 target: remove this import.

---

## Portfolio Caller Map (Sprint 147 state)

### CLI JSON-Loading Boundary Callers (`Portfolio.from_json_file`)

All 9 CLI call sites are active, intentional, and correct. `Portfolio.from_json_file` is the only JSON-loading path for legacy portfolio files.

| Command | File | Line | Also calls `legacy_portfolio_to_domain_portfolio`? |
|---|---|---|---|
| `atlas ask` | `atlas/cli/main.py:ask_command` | 281 | No — passes `Portfolio` to `ConversationEngine` |
| `atlas home` | `atlas/cli/main.py:home_command` | 328 | No — passes `Portfolio` to `AtlasHomeEngine` |
| `atlas dashboard show` | `atlas/cli/main.py:dashboard_show_command` | 393 | No — passes `Portfolio` to `DashboardEngine` |
| `atlas daily summary` | `atlas/cli/main.py:daily_summary_command` | 436–437 | **Yes** — converts to domain portfolio before capability |
| `atlas portfolio summary` | `atlas/cli/main.py:portfolio_summary_command` | 641–642 | **Yes** — converts to domain portfolio for summary |
| `atlas intelligence analyze` | `atlas/cli/main.py:_parse_intelligence_inputs` | 1357 | No — passes `Portfolio` to `IntelligenceEngine` |
| `atlas suitability analyze` | `atlas/cli/main.py:_build_suitability_assessment` | 1399 | No — passes `Portfolio` to `SuitabilityEngine` |
| `atlas risk-drift analyze` | `atlas/cli/main.py:_build_risk_drift_assessment` | 1440 | No — passes `Portfolio` to `RiskDriftEngine` |
| `atlas monitor` | `atlas/cli/main.py:_monitor_from_inputs` | 1492 | No — passes `Portfolio` to `MonitoringEngine` |

All 9 are correct. `Portfolio.from_json_file` is the user-facing JSON-loading boundary — it must remain.

### Engine Type-Annotation Callers (TYPE_CHECKING only)

All 8 engine files use `Portfolio` as a TYPE_CHECKING-only annotation. Zero runtime dependency.

| File | Annotation site | Migration status |
|---|---|---|
| `atlas/conversation/engine.py` | `ConversationInput.portfolio: Portfolio \| None` | Correct — type only |
| `atlas/decision/decision_context.py` | `DecisionContext.portfolio: Portfolio \| None` | Correct — type only |
| `atlas/dashboard/engine.py` | `DashboardInput.portfolio: Portfolio \| None` | Correct — type only |
| `atlas/home/engine.py` | `AtlasHomeInput.portfolio: Portfolio \| None` | Correct — type only |
| `atlas/intelligence/engine.py` | `IntelligenceInput.portfolio: Portfolio \| None` | Correct — type only |
| `atlas/monitoring/engine.py` | `snapshot_portfolio(portfolio: Portfolio)` signature | Correct — type only |
| `atlas/risk_drift/engine.py` | `RiskDriftInput.current_portfolio: Portfolio \| None` | Correct — type only |
| `atlas/suitability/engine.py` | `SuitabilityInput.portfolio: Portfolio \| None` | Correct — type only |

These are correct and should remain as-is. `Portfolio` is the input type these engines accept from CLI.

### Runtime Adapter Conversion Callers (`legacy_portfolio_to_domain_portfolio`)

| File | Call site | Purpose |
|---|---|---|
| `atlas/cli/main.py` | Lines 437, 642 | CLI converts before Blueprint capability calls |
| `atlas/conversation/engine.py` | Line 182 | Converts before `PortfolioIntelligenceCapability.analyze` |
| `atlas/dashboard/engine.py` | Line 260 | Converts before `PortfolioIntelligenceCapability.analyze` |
| `atlas/decision/decision_engine.py` | Line 125 | Converts before `PortfolioIntelligenceCapability.analyze` |
| `atlas/intelligence/engine.py` | Line 248 | Converts before `PortfolioIntelligenceCapability.analyze` |
| `atlas/portfolio_review/engine.py` | Line 99 | Converts for domain-aligned portfolio review |

All 6 are correct. `legacy_portfolio_to_domain_portfolio` is the centralized conversion function — callers are the right patterns.

**Note:** `atlas/portfolio_review/engine.py` imports `Portfolio as LegacyPortfolio` at **module runtime** (not behind `TYPE_CHECKING`), unlike all other engine files. This is intentional — the engine needs `LegacyPortfolio` to type its `review()` input parameter at runtime.

---

## CLI Boundary Review

All 9 CLI `Portfolio.from_json_file` call sites:
- Are user-facing JSON-loading boundaries
- Should keep adapter boundary types permanently — `Portfolio` is the JSON format contract
- No migration warranted — these are correct boundary callers
- Risk of migrating: HIGH (would require a new JSON-loading type or schema change)

**Conclusion:** CLI boundary is stable. No action needed.

---

## Domain / Shared Replacement Review

| Type | Location | Fields | JSON loading | Relationship to adapter `Portfolio` |
|---|---|---|---|---|
| `atlas.shared.Portfolio` | `atlas/shared/entities.py:50` | `id`, `name`, `holdings: tuple[Holding, ...]`, `owner_id`, `base_currency`, `metadata` | **No** | Domain entity; destination of `legacy_portfolio_to_domain_portfolio` |
| `atlas.shared.Holding` | `atlas/shared/entities.py:31` | `company_id`, `ticker`, `quantity`, `current_price`, `market_value`, `weight`, `sector`, `country`, `currency`, `asset_type`, `quality_score`, `risk_score`, `market_cap` | No | Domain entity; destination of each `PortfolioPosition` |
| `atlas.domains.portfolio.*` | `atlas/domains/portfolio/models.py` | `PortfolioSnapshot`, `PortfolioSummary`, `PortfolioValidationResult`, `PortfolioDomainReview` | No | Analysis output types — NOT input boundary types |
| `atlas.capabilities.portfolio_intelligence.PortfolioFitInput` | `atlas/capabilities/portfolio_intelligence/models.py:28` | Per-ticker fit input fields | No | Per-ticker input — not a portfolio-level type |

**Conclusion:** No Blueprint-aligned JSON-loading portfolio type exists. `atlas.shared.Portfolio` is the canonical domain entity but has no `from_json_file` and cannot replace the adapter for CLI use. The adapter `Portfolio` and `PortfolioPosition` are the correct permanent home for legacy JSON-loading boundary types.

---

## Final Stable Adapter State (Sprint 148)

`atlas/adapters/portfolio.py` is stable and clean:

| Symbol | Type | Status |
|---|---|---|
| `Portfolio` | frozen dataclass | Active — permanent JSON-loading boundary type |
| `PortfolioPosition` | frozen dataclass | Active — permanent JSON-loading boundary type |
| `legacy_portfolio_to_domain_portfolio` | function | Active — centralized conversion to `atlas.shared.Portfolio` |
| `_position_from_mapping` | private helper | Active |
| `_normalize_weight` | private helper | Active |

Imports (post Sprint 148):
- `atlas.analysis.scores.clamp_score` — OK
- `atlas.shared.Holding`, `Portfolio as SharedPortfolio` — OK
- ~~`atlas.capabilities.portfolio_intelligence.PortfolioFitInput`~~ — **Removed Sprint 148** (was unused)

---

## Sprint 148 — Stale Import Removal (COMPLETED)

**Removed `PortfolioFitInput` import from `atlas/adapters/portfolio.py`.**

- Zero behavior change — import was unused.
- Guardrail added: `test_sprint148_adapter_does_not_import_portfolio_fit_input`.
- Docs updated to CLOSED.

---

## Closed-Track Summary

| Track | Closed |
|---|---|
| `atlas/analysis/` cleanup | Sprint 141 |
| `atlas/decision/` cleanup | Sprint 144 |
| Provider boundary audit | Sprint 146 |
| Portfolio boundary | **Sprint 148** |

No further portfolio boundary cleanup work is planned.

**Reopening condition:** If a new caller of `atlas.analysis.portfolio` is discovered, or if `Portfolio`/`PortfolioPosition` are moved or deleted incorrectly, this track should be reopened.

---

## Recommended Sprint 149 Target

**Audit Group C self-contained module: `atlas/evidence/`.**

`atlas/evidence/` is self-contained (no provider dependency, no Blueprint-aligned successor yet). Audit its callers, classify cleanup candidates, and recommend a focused follow-on sprint. This matches the established audit-first pattern from Sprints 142, 145, 147.

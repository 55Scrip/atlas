# Atlas Legacy Engine Consolidation Plan

**Created:** 2026-07-01 (Sprint 74)  
**Updated:** 2026-07-01 (Sprint 76)  
**Status:** Active — Sprint 76 target complete; Sprint 77 target to be selected

This document inventories all legacy Atlas modules, maps their current runtime
usage, documents overlap with Blueprint-aligned domains and capabilities, and
identifies the safest first migration target for Sprint 75.

---

## Background

Atlas has two parallel layers:

**Blueprint-aligned (current):**
- `atlas/domains/` — canonical concepts and contracts
- `atlas/capabilities/` — product capabilities
- `atlas/adapters/` — bridges between legacy and domain types
- `atlas/shared/` — immutable canonical entities
- `atlas/providers/` — opt-in market data (not called by demo)

**Legacy (compatibility, not for expansion):**
- All other top-level modules under `atlas/` — original working engines
- Remain functional and fully tested
- CLI commands exist for many; some are actively used

The goal of consolidation is to reduce the legacy surface area over time,
not to delete working code abruptly. Each migration must be testable,
deterministic, and leave the CLI interface unchanged or clearly improved.

---

## Legacy Module Inventory

### Group A — Thin Shims / Re-exports

| Module | Files | Lines | Description | Runtime CLI usage | Status |
|---|---|---|---|---|---|
| ~~`atlas/daily/`~~ | ~~2~~ | ~~43~~ | ~~Re-exports `atlas.daily_brief` under a stable path~~ | ~~`atlas daily brief`~~ | **Removed Sprint 75** |
| `atlas/daily_brief/` | 2 | 353 | Legacy DailyBriefEngine (provider-dependent, 11 sub-engines) | `atlas daily brief` (deprecated Sprint 76) | Deprecated |

`atlas/daily/` is a pure re-export shim. It imports from `atlas/daily_brief/`
and re-exports under the `atlas.daily` name. The only CLI consumer is
`atlas daily brief` (the legacy command). `atlas daily summary` is the
Blueprint-aligned equivalent and does not touch either module.

`atlas/daily_brief/` is the legacy engine that:
- imports `atlas.analysis.portfolio`, `atlas.analysis.watchlist`
- calls a `CompanyDataProvider` (mock or Yahoo)
- composes 11 sub-engines at runtime
- is distinct from `atlas/capabilities/daily_brief/` (the current engine)

**Note:** `atlas/domains/daily_brief/__init__.py` currently imports from
`atlas.daily_brief` — a boundary violation. The domain layer should not import
from legacy modules. This is a known tech debt item.

### Group B — Provider-Dependent Legacy Commands (medium risk)

| Module | Files | Lines | Description | Runtime CLI usage |
|---|---|---|---|---|
| `atlas/analysis/` | 18 | 1985 | Company, portfolio, watchlist, memory, scoring engines | `atlas analyze`, `atlas watchlist analyze`, etc. |
| `atlas/home/` | 2 | 625 | AtlasHomeEngine — top-level dashboard aggregator | `atlas home` |
| `atlas/dashboard/` | 2 | 528 | DashboardEngine — weekly dashboard | `atlas dashboard show` |
| `atlas/intelligence/` | 2 | 470 | IntelligenceEngine — company intelligence | `atlas intelligence analyze` |
| `atlas/watchlist_review/` | 2 | 901 | WatchlistReviewEngine | `atlas watchlist review` |
| `atlas/portfolio_review/` | 2 | 635 | PortfolioReviewEngine | `atlas portfolio review` |
| `atlas/comparison/` | 2 | 1032 | ComparisonEngine — multi-company comparison | `atlas compare` |
| `atlas/themes/` | 2 | 569 | ThemeEngine | `atlas theme analyze` |
| `atlas/market/` | 3 | 793 | MarketSnapshot, MarketHealthEngine, MarketRegimeEngine | `atlas market analyze`, `atlas market health` |

All Group B modules:
- require a `CompanyDataProvider` at runtime (mock or Yahoo Finance)
- are provider-coupled by design
- have no Blueprint-aligned equivalent capability yet
- are functional and tested

### Group C — Self-Contained Analytics (targeted migration candidates)

| Module | Files | Lines | Description | Runtime CLI usage |
|---|---|---|---|---|
| `atlas/evidence/` | 2 | 563 | EvidenceQualityEngine — scores evidence claims | `atlas evidence assess` |
| `atlas/reasoning/` | 2 | 591 | ReasoningEngine — structured reasoning output | `atlas reason analyze` |
| `atlas/risk/` | 2 | 469 | RiskEngine, PositionSizingInput | `atlas risk size` |
| `atlas/risk_drift/` | 2 | 682 | RiskDriftEngine — position drift detection | `atlas risk-drift analyze` |
| `atlas/economics/` | 2 | 532 | EconomicSignalsEngine | `atlas economics analyze` |
| `atlas/language/` | 2 | 493 | AtlasLanguageEngine — output language calibration | Used internally by `daily_brief` |
| `atlas/monitoring/` | 2 | 626 | MonitoringEngine — alert generation | `atlas monitor` |
| `atlas/principles/` | 2 | 360 | PrinciplesEngine — investment principle check | `atlas principles check` |
| `atlas/suitability/` | 2 | 635 | SuitabilityEngine — investor suitability | `atlas suitability analyze` |

Group C modules are largely self-contained: they do not depend on providers,
and they operate on structured input rather than live data. Several are good
candidates for a future Blueprint-aligned capability wrapper.

### Group D — Infrastructure / Support (leave unchanged)

| Module | Files | Lines | Description | Notes |
|---|---|---|---|---|
| `atlas/services/` | 4 | 164 | Database service, company service, financial import | SQLite persistence layer |
| `atlas/memory/` | 4 | 219 | MemoryEngine, MemoryStore — ticker-level memory entries | Used by `atlas memory save/show/compare` |
| `atlas/profile/` | 2 | 294 | InvestorProfile — investor context | Used widely across legacy commands |
| `atlas/decision_journal/` | 2 | ~200 | Journal entry logging | Used by `atlas journal create/list/review` |
| `atlas/conversation/` | 2 | 526 | ConversationEngine — Q&A sessions | `atlas ask` |

Group D provides foundation infrastructure. No migration needed; these serve
specific functions with no Blueprint-aligned equivalent in scope.

---

## Runtime Dependency Map

```
atlas daily brief
→ atlas.daily (re-export shim)
→ atlas.daily_brief.DailyBriefEngine
→ atlas.analysis.portfolio.Portfolio (legacy portfolio type)
→ atlas.analysis.watchlist.Watchlist (legacy watchlist type)
→ providers (mock/yahoo — opt-in)
→ 11 sub-engines at runtime (home, portfolio_review, watchlist_review, ...)
status: legacy — Blueprint-aligned equivalent is `atlas daily summary`

atlas daily summary
→ atlas.capabilities.daily_brief.DailyBriefCapability
→ atlas.capabilities.daily_brief.json_loader (JSON input)
→ atlas.adapters.* (portfolio, watchlist, knowledge, research, company_analysis)
→ atlas.domains.portfolio (portfolio concentration)
→ NO providers called
status: current (Blueprint-aligned)

atlas portfolio summary
→ atlas.analysis.portfolio.Portfolio.from_json_file (legacy type)
→ atlas.adapters.portfolio.legacy_portfolio_to_domain_portfolio
→ atlas.domains.portfolio.portfolio_summary
status: partially migrated (uses adapter bridge)

atlas portfolio review
→ atlas.analysis.portfolio.Portfolio (legacy type)
→ atlas.adapters.portfolio (bridge)
→ atlas.domains.portfolio.portfolio_summary (domain)
→ atlas.portfolio_review.PortfolioReviewEngine (legacy)
status: partially migrated (domain summary used; review engine still legacy)

atlas portfolio analyze
→ atlas.analysis.portfolio.Portfolio (legacy type)
→ atlas.adapters.portfolio (bridge)
→ atlas.domains.portfolio.portfolio_summary (domain)
status: partially migrated

atlas analyze <ticker>
→ providers (mock/yahoo — opt-in)
→ atlas.analysis.engine.AtlasInvestmentEngine
status: legacy — no Blueprint-aligned equivalent

atlas home
→ providers (mock/yahoo — opt-in)
→ atlas.home.AtlasHomeEngine (orchestrates many sub-engines)
status: legacy — no Blueprint-aligned equivalent

atlas watchlist intelligence
→ atlas.capabilities.watchlist_intelligence.WatchlistIntelligenceEngine
→ atlas.adapters.watchlist, atlas.adapters.knowledge
→ NO providers called
status: current (Blueprint-aligned)

atlas watchlist analyze
→ atlas.analysis.watchlist.WatchlistEngine (legacy)
→ providers (mock/yahoo — opt-in)
status: legacy

atlas watchlist review
→ atlas.watchlist_review.WatchlistReviewEngine (legacy)
→ providers (mock/yahoo — opt-in)
status: legacy

atlas company-analysis export
→ atlas.capabilities.company_analysis.CompanyAnalysisEngine
→ atlas.adapters.knowledge, atlas.adapters.research_input
→ NO providers called
status: current (Blueprint-aligned)

atlas discovery export
→ atlas.capabilities.discovery.DiscoveryEngine
→ atlas.adapters.*
→ NO providers called
status: current (Blueprint-aligned)
```

---

## Blueprint Overlap Summary

| Legacy module | Blueprint equivalent | Overlap status |
|---|---|---|
| `atlas/daily/` + `atlas/daily_brief/` | `atlas/capabilities/daily_brief/` | Full overlap — two parallel implementations. CLI command `atlas daily brief` uses legacy; `atlas daily summary` uses Blueprint. |
| `atlas/analysis/portfolio.py` | `atlas/domains/portfolio/` + `atlas/adapters/portfolio.py` | Partial — Portfolio type bridged via adapter. Domain summary is the current path. |
| `atlas/analysis/watchlist.py` | `atlas/capabilities/watchlist_intelligence/` | Partial — legacy used by `atlas watchlist analyze`; new capability used by `atlas watchlist intelligence`. |
| `atlas/analysis/company_analysis.py` | `atlas/capabilities/company_analysis/` | Partial — new capability path exists for export pipeline. |
| `atlas/domains/daily_brief/` | `atlas/capabilities/daily_brief/` | **Boundary violation:** `atlas/domains/daily_brief/__init__.py` imports from `atlas.daily_brief` (legacy). The domain layer should not depend on legacy modules. |

### Boundary Violation Identified

`atlas/domains/daily_brief/__init__.py` imports from `atlas.daily_brief`:

```python
from atlas.daily_brief import DailyBriefEngine, DailyBriefInput, DailyBriefOutput
```

This makes a Blueprint domain depend on a legacy module — the reverse of the
intended dependency direction. No CLI command or test currently imports from
`atlas.domains.daily_brief` directly (confirmed by grep), so the violation
is dormant but should be resolved when the legacy daily_brief module is
eventually retired.

---

## Provider Safety Confirmation

- Providers (`atlas/providers/`) are never imported by:
  - `atlas/domains/`
  - `atlas/capabilities/`
  - `atlas/adapters/`
  - demo script (`scripts/run_daily_brief_demo.sh`)
  - release verification script (`scripts/verify_release_candidate.sh`)
- Providers are only called from legacy CLI commands that explicitly pass
  `--provider mock` or `--provider yahoo` at the command line
- Default for all legacy provider commands is `--provider mock`
- `atlas daily summary` (current path) makes zero provider calls

Provider safety: **confirmed**.

---

## Sprint 76 Migration Target — COMPLETED

### Completed: `atlas daily brief` command deprecated

**Sprint 76 result:**
- `atlas daily brief` CLI command now prints a deprecation message and exits cleanly (exit 0)
- Legacy `DailyBriefEngine` is no longer called by any CLI command
- `from atlas.daily_brief import ...` removed from `atlas/cli/main.py` module-level imports
- `atlas daily summary` (Blueprint-aligned) is the current supported command
- `atlas/daily_brief/` engine module remains on disk, isolated — no command calls it
- 10 new Sprint 76 deprecation tests added; 1001 tests passing, 0 failures

**Provider safety:** deprecated command makes zero provider calls (no `DailyBriefEngine` instantiated).

**Future removal criteria for `atlas/daily_brief/`:**
1. Confirm no external scripts import `atlas.daily_brief` directly (grep confirms only CLI did)
2. Remove `atlas daily brief` command entirely (not just deprecate)
3. Delete `atlas/daily_brief/` (2 files, 353 lines) in a future sprint
4. Suggested sprint: Sprint 77 or later

---

## Sprint 75 Migration Target — COMPLETED

### Completed: `atlas/daily/` shim removal + `atlas/domains/daily_brief/` boundary fix

**Sprint 75 result:**
- `atlas/daily/` deleted (2 files, 43 lines)
- `atlas/cli/main.py` updated to import from `atlas.daily_brief` directly
- `tests/test_daily_brief.py` updated to import from `atlas.daily_brief` directly
- `atlas/domains/daily_brief/__init__.py` rewritten as a minimal namespace stub
  (no imports from legacy OR capabilities — pure domain namespace placeholder)
- `test_domains_do_not_import_capabilities_or_providers_or_legacy` extended with
  explicit legacy prefix list (`atlas.daily`, `atlas.daily_brief`, `atlas.analysis`, etc.)
- 2 new Sprint 75 boundary tests added: `test_atlas_daily_shim_is_removed`,
  `test_domains_daily_brief_does_not_import_legacy`
- 991 tests passing, 0 failures. Demo + RC verification both green.

### Selected Target (original):

**Rationale:**

`atlas/daily/` is a two-file, 43-line pure re-export shim with no logic:

```python
# atlas/daily/__init__.py
from atlas.daily_brief import (
    DailyBriefEngine, DailyBriefInput, ...
)
```

It exists solely to give `atlas.daily` a stable import path. The only CLI
consumer is `atlas daily brief` (legacy command), which can import from
`atlas.daily_brief` directly without the shim.

**Simultaneously**, `atlas/domains/daily_brief/__init__.py` imports from
`atlas.daily_brief` — a boundary violation. Since no external code imports
from `atlas.domains.daily_brief`, this file can be updated to export from
`atlas.capabilities.daily_brief` instead (or left as-is if the domain
boundary module is removed entirely).

**What Sprint 75 would do:**

1. Update `atlas/cli/main.py` to import `DailyBriefEngine`, `DailyBriefInput`,
   `render_daily_brief` from `atlas.daily_brief` directly (removing the
   `atlas.daily` shim import)
2. Fix `atlas/domains/daily_brief/__init__.py` to either:
   - re-export from `atlas.capabilities.daily_brief` (correct direction), or
   - be removed if no code uses it
3. Delete `atlas/daily/` (2 files, 43 lines)
4. Update any test imports

**This does NOT:**
- Change the `atlas daily brief` command behavior
- Touch `atlas/daily_brief/` (the legacy engine itself)
- Change the `atlas daily summary` command (Blueprint-aligned, untouched)
- Introduce any new capability

**Risk level: LOW**
- 43 lines removed, 0 logic changed
- Full test suite confirms no regressions
- The shim has no logic — it is purely a re-export

### Runner-up Target: `atlas/domains/daily_brief/` boundary fix only

If the `atlas/daily/` removal is considered too broad for Sprint 75, the
boundary violation fix alone (updating `atlas/domains/daily_brief/__init__.py`
to not import from a legacy module) is an even smaller, safer change.

---

## Migration Risk Summary

| Risk | Description | Mitigation |
|---|---|---|
| Import breakage | `atlas.daily` removed; any external code using it breaks | Grep confirms only `atlas/cli/main.py` imports `atlas.daily`; fix is in same sprint |
| Test failures | Tests importing `atlas.daily` | Only `tests/test_daily_brief.py` imports from `atlas.daily_brief` (not `atlas.daily`); risk is low |
| Boundary re-introduction | Future sprint re-introduces domain → legacy import | Add architecture boundary test asserting domains do not import legacy modules |
| Scope creep | Sprint expands to touch `atlas/daily_brief/` engine | Sprint 75 explicitly excludes the daily_brief engine; only the shim is removed |

---

## Full Technical Debt Inventory (Updated)

| Area | Description | Priority | Suggested Sprint |
|---|---|---|---|
| ~~`atlas/daily/` shim~~ | ~~43-line re-export; removed~~ | ~~High~~ | **Done 75** |
| ~~`atlas/domains/daily_brief/` boundary violation~~ | ~~Fixed: namespace stub~~ | ~~High~~ | **Done 75** |
| ~~`atlas daily brief` command~~ | ~~Deprecated; no longer calls engine~~ | ~~High~~ | **Done 76** |
| `atlas/daily_brief/` legacy engine | Provider-coupled; no command calls it; safe to delete | Medium | 77 |
| `atlas/analysis/watchlist.py` duplication | Parallel to `capabilities/watchlist_intelligence` | Medium | Future |
| `atlas/analysis/portfolio.py` legacy type | Bridged via adapter; could be retired after full portfolio migration | Medium | Future |
| Group C self-contained modules | `evidence`, `reasoning`, `risk`, etc. — good candidates for Blueprint wrappers | Low | Multi-sprint |
| Provider-coupled Group B | `home`, `dashboard`, `comparison`, etc. — require provider architecture decision | Low | Long-term |
| Legacy engine consolidation (test coverage) | Ensure legacy commands retain tests during migration | Ongoing | Each sprint |

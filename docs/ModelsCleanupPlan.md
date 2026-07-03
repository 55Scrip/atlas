# Models Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 202)  
**Updated:** 2026-07-03 (Sprint 203)  
**Status:** CLOSED — `atlas/models/` is clean. Two active ORM models, zero stale exports, zero provider coupling, zero cleanup warranted. Track formally closed Sprint 203.

---

## Important Framing

Sprint 202 audits `atlas/models/` following the closure of `atlas/database/` + `atlas/services/` (Sprint 198), the storage boundary audit (Sprint 200), and two RC checkpoints (Sprint 199, Sprint 201).

Sprint 198 already removed `atlas/models/investment_report.py` (dead 3-line re-export shim with zero callers). The remaining surface — `entities.py` and `__init__.py` — has not had a dedicated audit until now.

This sprint uses repository reality. `atlas/models/` contains exactly 2 modules and 52 lines total.

---

## Package Surface

### `atlas/models/__init__.py` (11 lines)

```python
from typing import Any

__all__ = ["Company", "FinancialHistory"]

def __getattr__(name: str) -> Any:
    if name in __all__:
        from atlas.models.entities import Company, FinancialHistory
        return {"Company": Company, "FinancialHistory": FinancialHistory}[name]
    raise AttributeError(f"module 'atlas.models' has no attribute {name!r}")
```

- `__all__` contains exactly `["Company", "FinancialHistory"]`
- Lazy `__getattr__` shim — defers import from `atlas.models.entities`
- No reference to removed `investment_report.py`
- No stale exports
- Raises `AttributeError` for unknown names — no silent fallback

### `atlas/models/entities.py` (41 lines)

Two active SQLAlchemy ORM models:

**`Company(Base)`** — `__tablename__ = "companies"`, 9 columns + relationship:

| Column | Type | Constraint |
|---|---|---|
| `id` | `int` | primary key |
| `atlas_id` | `str` | unique |
| `ticker` | `str` | unique |
| `name` | `str` | — |
| `exchange` | `str \| None` | — |
| `country` | `str \| None` | — |
| `currency` | `str \| None` | — |
| `sector` | `str \| None` | — |
| `industry` | `str \| None` | — |
| `status` | `str \| None` | — |
| `financials` | relationship | back_populates="company" |

**`FinancialHistory(Base)`** — `__tablename__ = "financial_history"`, 13 columns + relationship + `UniqueConstraint("company_id", "fiscal_year")`:

| Column | Type | Constraint |
|---|---|---|
| `id` | `int` | primary key |
| `company_id` | `int` | ForeignKey("companies.id") |
| `fiscal_year` | `int` | — |
| `revenue` | `float \| None` | — |
| `gross_profit` | `float \| None` | — |
| `operating_income` | `float \| None` | — |
| `net_income` | `float \| None` | — |
| `operating_cashflow` | `float \| None` | — |
| `capex` | `float \| None` | — |
| `free_cashflow` | `float \| None` | — |
| `total_assets` | `float \| None` | — |
| `equity` | `float \| None` | — |
| `debt` | `float \| None` | — |
| `cash` | `float \| None` | — |
| `shares_outstanding` | `float \| None` | — |
| `company` | relationship | back_populates="financials" |

**Imports:** `Base` from `atlas.database.connection` — correct boundary direction (models → database). No service imports, no provider imports, no CLI imports, no network access.

---

## Caller Map

All production and test callers of `atlas.models`:

| File | Symbols imported | Purpose |
|---|---|---|
| `atlas/services/database_service.py` | `Company, FinancialHistory  # noqa: F401` | Registers ORM models with `Base.metadata` before `create_all` |
| `atlas/services/company_service.py` | `Company` | Active CRUD: `add_company`, `list_companies`, `get_company_by_ticker` |
| `atlas/services/financial_import_service.py` | `Company, FinancialHistory` | Active financial import pipeline: `import_financials` |
| `tests/test_financial_import_service.py` | `Company, FinancialHistory` | Test caller |
| `tests/test_database_services_sprint197.py` | `Company, FinancialHistory` | Importability tests; asserts `atlas.models.investment_report` absent |

All callers use `from atlas.models import ...` — the lazy shim in `__init__.py` is triggered correctly.

---

## InvestmentReport Reference Audit

`InvestmentReport` appears in active code across many files:

| File | Import source | Status |
|---|---|---|
| `atlas/analysis/engine.py` | defines `InvestmentReport` | Active definition ✓ |
| `atlas/suitability/engine.py` | `from atlas.analysis.engine import ...` | Active caller ✓ |
| `atlas/intelligence/engine.py` | `from atlas.analysis.engine import ...` | Active caller ✓ |
| `atlas/decision/decision_engine.py` | `from atlas.analysis.engine import ...` | Active caller ✓ |
| `atlas/decision/decision_result.py` | `from atlas.analysis.engine import ...` | Active caller ✓ |
| `atlas/comparison/engine.py` | `from atlas.analysis.engine import ...` | Active caller ✓ |
| `atlas/conversation/engine.py` | `from atlas.analysis.engine import ...` | Active caller ✓ |
| `atlas/analysis/__init__.py` | re-exports from `.engine` | Active re-export ✓ |
| `atlas/analysis/report.py` | `from .engine import ...` | Active caller ✓ |
| `atlas/analysis/explanation.py` | `from .engine import ...` | Active caller ✓ |
| `atlas/cli/main.py` | `from atlas.analysis.engine import ...` | Active caller ✓ |

**No file imports `InvestmentReport` from `atlas.models.investment_report`** — that file was deleted Sprint 198 and is confirmed absent. All `InvestmentReport` usage is correctly routed through `atlas.analysis.engine`. No stale references.

---

## Boundary Review

### Dependency direction

```
atlas/config.py ← atlas/database/connection.py ← atlas/models/entities.py ← atlas/services/ ← atlas/cli/
```

| Direction | Status |
|---|---|
| `atlas/models/` imports `Base` from `atlas/database/connection.py` | Correct — models depend on database infrastructure ✓ |
| `atlas/services/` imports from `atlas/models/` | Correct — services depend on models ✓ |
| `atlas/models/` imports from `atlas/services/` | None — no upward dependency ✓ |
| `atlas/models/` imports from `atlas/providers/` | None — no provider coupling ✓ |
| `atlas/models/` imports from `atlas/cli/` | None — no CLI coupling ✓ |
| Circular dependencies | None ✓ |

### Two `Company` classes — intentional architecture

There are two distinct `Company` classes in Atlas:

| Class | Source | Purpose |
|---|---|---|
| `atlas.models.entities.Company` | SQLAlchemy ORM model | Database persistence (companies table) |
| `atlas.shared.Company` | Blueprint canonical entity (dataclass) | Blueprint-layer in-memory entity |

These are not duplicates — they serve different layers. `atlas/services/` imports the ORM model; `atlas/capabilities/`, `atlas/domains/`, and `atlas/adapters/` import the shared entity. No confusion or conflict.

### Schema/ORM gap

`atlas/database/schema.sql` defines 8 tables. Only 2 have ORM models (`Company`, `FinancialHistory`). This gap is intentional — the 6 unmapped tables are managed via raw SQL in `database_service.py`. This was documented Sprint 197 and remains unchanged.

### `atlas/models/investment_report.py` — confirmed absent

Deleted Sprint 198. Was a 3-line dead re-export shim (`InvestmentReport`, `ScoreCategory` from `atlas.analysis.engine`) with zero callers. Confirmed absent via `ls`. No follow-up needed.

---

## Stale Import Audit

Full search of `atlas/models/` for stale references from closed cleanup tracks:

| Search term | Found | Classification |
|---|---|---|
| `atlas.reasoning` / `ReasoningInput` / `ReasoningReport` | No | ✓ |
| `atlas.analysis.portfolio` / `PortfolioAnalysis` | No | ✓ |
| `CompanyAnalysisProvider` | No | ✓ |
| `atlas.analysis.comparison/memory/scoring/watchlist` | No | ✓ |
| `render_comparison_result` | No | ✓ |
| `atlas.models.investment_report` (import anywhere in repo) | No | ✓ |
| `InvestmentReport` from `atlas.models` (import anywhere in repo) | No | ✓ |
| Provider imports in `atlas/models/` | None | ✓ |
| Network access in `atlas/models/` | None | ✓ |

**No stale references anywhere in `atlas/models/`.**

---

## Provider Boundary Verification

| Check | Result |
|---|---|
| `atlas/models/` imports any provider | No ✓ |
| `atlas/models/` triggers network call | No ✓ |
| `atlas/models/` has optional dependency on `atlas/providers/` | No ✓ |

`atlas/models/` is fully provider-free. The ORM models are pure data shape definitions with no runtime coupling to any provider.

---

## Sprint 198 Removal Guard Verification

All Sprint 198 removal targets confirmed absent:

| Target | Status |
|---|---|
| `atlas/models/investment_report.py` | Absent ✓ |
| `atlas/services/kpi_service.py` | Absent ✓ |
| `tests/test_kpi_service.py` | Absent ✓ |
| `atlas/reports/investment_card.py` | Absent ✓ |
| `atlas/reports/` directory | Absent ✓ |
| `atlas/storage/` directory | Absent ✓ |

All Sprint 198 and Sprint 200 removals remain stable.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Classification | Action |
|---|---|---|---|
| `atlas/models/__init__.py` lazy shim | 11 lines, clean, no stale references | `active_infrastructure` | Leave unchanged |
| `atlas/models/entities.py` `Company` model | 3 production callers, `companies` table | `active_orm_model` | Leave unchanged |
| `atlas/models/entities.py` `FinancialHistory` model | 2 production callers, `financial_history` table | `active_orm_model` | Leave unchanged |
| `atlas/models/investment_report.py` | Absent since Sprint 198 | `previously_deleted_sprint198` | No action |
| Schema/ORM gap (6 unmapped tables) | Intentional raw-SQL pattern | `intentional_architecture` | No action |
| Two `Company` classes | Blueprint entity vs. ORM model — different layers | `intentional_architecture` | No action |

**Summary: No cleanup warranted.** The package is clean, minimal, and correctly bounded.

---

## Track Closure

**The `atlas/models/` cleanup track is CLOSED as of Sprint 203.**

Sprint 202 performed the inventory audit. Sprint 203 confirmed all Sprint 202 findings unchanged and formally closed the track.

**Closure rationale:**
- `atlas/models/` contains exactly 2 modules (`__init__.py`, `entities.py`) and 52 lines
- Both ORM models (`Company`, `FinancialHistory`) are active with production callers
- `__init__.py` lazy shim is clean — no stale references, no stale exports
- `atlas/models/investment_report.py` (Sprint 198 target) confirmed absent
- No stale imports from any closed cleanup track
- No provider coupling, no network access, no CLI coupling
- Boundary direction is correct: models → database (no upward dependency)
- Schema/ORM gap (6 unmapped tables) is intentional and unchanged
- Two `Company` classes are architecturally intentional (ORM vs. Blueprint entity)
- Tests pass, demo passes, release verification passes
- No provider/network behavior introduced or changed

**Future reopening condition:** Reopen only if new ORM models are added, existing models are modified, `atlas/models/investment_report.py` is reintroduced, provider coupling is introduced, or the schema/ORM gap changes in a non-intentional way. No further models cleanup work is planned until new dead code, stale exports, schema boundary issues, model/database/services boundary issues, provider-boundary issues, persistence ownership changes, or a clear replacement/migration target emerges.

---

## Sprint 202 Verification Table

| Check | Result |
|---|---|
| `atlas/models/` module count | 2 (`__init__.py`, `entities.py`) ✓ |
| `atlas/models/__init__.__all__` | `["Company", "FinancialHistory"]` — no extras ✓ |
| Lazy shim references `investment_report` | No ✓ |
| `atlas/models/investment_report.py` exists | **No** — absent ✓ |
| `atlas/reports/` exists | **No** — absent ✓ |
| `atlas/storage/` exists | **No** — absent ✓ |
| `atlas.models.investment_report` imported anywhere | **Zero hits** ✓ |
| `Company` ORM model callers | 3 production + 2 test ✓ |
| `FinancialHistory` ORM model callers | 2 production + 2 test ✓ |
| `atlas/models/` imports providers | No ✓ |
| `atlas/models/` imports services | No ✓ |
| `atlas/models/` imports CLI | No ✓ |
| Boundary direction: models → database | ✓ (`Base` from `atlas.database.connection`) |
| Circular dependencies | None ✓ |
| No stale imports from closed cleanup tracks | ✓ |
| Schema/ORM gap (6 unmapped tables) | Intentional ✓ |
| Two `Company` classes | Architecturally intentional ✓ |
| Compile check | Green ✓ |
| Full test suite | **1671 passed, 3 skipped** ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Behavior changes | None |
| Sprint 203 confirmation | All Sprint 202 findings unchanged ✓ |
| Track status | **CLOSED Sprint 203** ✓ |

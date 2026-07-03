# Database and Services Cleanup Plan

**Created:** 2026-07-03 (Sprint 197)  
**Status:** OPEN — Audit complete. Sprint 198 recommended: Close database/services cleanup track and remove zero-caller dead code.

---

## Important Framing

`atlas/database/` and `atlas/services/` are the persistence and service orchestration layers for Atlas. They sit immediately above `atlas/config.py` in the dependency chain and immediately below `atlas/cli/main.py` and application layers.

Sprint 197 audits these layers as a unit because `atlas/services/database_service.py` imports from both `atlas.config` and `atlas.database.connection` — they are tightly coupled by design.

**Three adjacent zero-caller dead symbols were also discovered during this audit:**
- `atlas/models/investment_report.py` — zero callers anywhere
- `atlas/reports/investment_card.py` — zero callers anywhere
- `atlas/services/kpi_service.py` functions — zero *production* callers (test-only)

---

## Executive Summary

`atlas/database/` and `atlas/services/` are clean, well-bounded, and actively used. The database layer (20 lines, 1 module) owns SQLAlchemy connection/session/ORM infrastructure and correctly consumes `atlas.config.DATABASE_PATH`. The services layer (4 modules, 164 lines total) owns persistence orchestration and is correctly consumed by CLI. No provider coupling. No network access. No stale imports from closed cleanup tracks.

**Three cleanup candidates identified:**
1. `atlas/models/investment_report.py` — dead re-export shim, zero callers
2. `atlas/reports/investment_card.py` — dead function, zero callers
3. `atlas/services/kpi_service.py` — test-only; no production callers import from it

**One structural observation (not a bug):** `atlas/database/schema.sql` defines 8 tables but only 2 have ORM models (`Company`, `FinancialHistory`). The remaining 6 tables are created by schema.sql at `init_database()` time but not mapped via SQLAlchemy ORM — intentional for a tool with partial ORM adoption.

---

## Package Inventory

### `atlas/database/connection.py` (20 lines)

| Attribute | Value |
|---|---|
| File | `atlas/database/connection.py` |
| Lines | 20 |
| Public classes | `Base` (SQLAlchemy `DeclarativeBase`) |
| Public functions | `get_engine(db_path?)`, `get_session(db_path?)` |
| Public constants | None |
| Private helpers | None |
| `__init__.py` | None — no package init |
| Config import | `from atlas.config import DATABASE_PATH` |
| Atlas imports | `atlas.config` |
| Active | ✓ |
| Foundational | ✓ |
| Runtime-facing | ✓ |
| Service-facing | ✓ |
| Config-adjacent | ✓ |
| Provider-coupled | No |
| Network access | No |
| Schema owner | No — connection only |
| Connection/session owner | ✓ |
| Stale migration residue | None |
| Cleanup risk | None |

**Production callers:**
- `atlas/models/entities.py` → imports `Base`
- `atlas/services/database_service.py` → imports `get_engine`, `Base`
- `atlas/services/company_service.py` → imports `get_session`
- `atlas/services/financial_import_service.py` → imports `get_session`

**Test callers:**
- `tests/test_financial_import_service.py` → imports `get_session`

### `atlas/database/schema.sql`

SQLite schema: 8 tables created via `executescript()` in `init_database()`.

| Table | ORM model? | Active use |
|---|---|---|
| `companies` | ✓ `Company` in `atlas/models/entities.py` | ✓ Used by CLI and services |
| `financial_history` | ✓ `FinancialHistory` in `atlas/models/entities.py` | ✓ Used by import service and tests |
| `market_data` | No ORM model | Schema-only — not queried via ORM |
| `valuation` | No ORM model | Schema-only — not queried via ORM |
| `scoring` | No ORM model | Schema-only — not queried via ORM |
| `risk_register` | No ORM model | Schema-only — not queried via ORM |
| `sources` | No ORM model | Schema-only — not queried via ORM |
| `research_notes` | No ORM model | Schema-only — not queried via ORM |

**Observation:** 6 of 8 schema tables have no ORM model. These tables are created at `init_database()` time but are not currently accessed via SQLAlchemy ORM. This is a structural gap, not a bug — the schema reflects intended future use or reserved capacity. No cleanup warranted in Sprint 197 or 198.

---

## Services Inventory

### `atlas/services/database_service.py` (19 lines)

| Attribute | Value |
|---|---|
| Lines | 19 |
| Public functions | `init_database(db_path?)` |
| Private helpers | None |
| Imports | `atlas.config.DATABASE_PATH`, `atlas.database.connection.get_engine`, `atlas.database.connection.Base`, `atlas.models.Company`, `atlas.models.FinancialHistory` (noqa F401) |
| Production callers | `atlas/cli/main.py` (`atlas init` command) |
| Test callers | `tests/test_financial_import_service.py` |
| Active | ✓ |
| Database-facing | ✓ |
| Config-adjacent | ✓ |
| Provider access | None |
| Cleanup risk | None |

**Note:** `from atlas.models import Company, FinancialHistory  # noqa: F401` — these imports trigger SQLAlchemy model registration so `Base.metadata.create_all(engine)` discovers both ORM models. The `# noqa: F401` is correct and intentional.

### `atlas/services/company_service.py` (43 lines)

| Attribute | Value |
|---|---|
| Lines | 43 |
| Public functions | `add_company(...)`, `list_companies()`, `get_company_by_ticker(ticker)` |
| Private helpers | None |
| Imports | `atlas.database.connection.get_session`, `atlas.models.Company` |
| Production callers | `atlas/cli/main.py` (`add_company`, `list_companies`), `atlas/reports/investment_card.py` (`get_company_by_ticker`) |
| Test callers | None directly |
| Active | ✓ (CLI + reports) |
| Database-facing | ✓ |
| Config-adjacent | Indirect via `get_session` |
| Provider access | None |
| Cleanup risk | None |

### `atlas/services/financial_import_service.py` (86 lines)

| Attribute | Value |
|---|---|
| Lines | 86 |
| Public functions | `import_financials(ticker, csv_path, db_path?)` |
| Public constants | `REQUIRED_COLUMNS`, `NUMERIC_COLUMNS` |
| Private helpers | `_read_financial_rows`, `_parse_fiscal_year`, `_parse_float` |
| Imports | `atlas.database.connection.get_session`, `atlas.models.Company`, `atlas.models.FinancialHistory` |
| Production callers | `atlas/cli/main.py` (`atlas import-financials`) |
| Test callers | `tests/test_financial_import_service.py` |
| Active | ✓ |
| Database-facing | ✓ |
| Config-adjacent | Indirect via `get_session` |
| Provider access | None |
| Cleanup risk | None |

### `atlas/services/kpi_service.py` (16 lines)

| Attribute | Value |
|---|---|
| Lines | 16 |
| Public functions | `safe_divide`, `gross_margin`, `operating_margin`, `net_margin`, `fcf_margin` |
| Private helpers | None |
| Imports | None (pure Python — no imports at all) |
| Production callers | **None** — zero production callers import from `atlas.services.kpi_service` |
| Test callers | `tests/test_kpi_service.py` (3 tests: `gross_margin`, `operating_margin`, `fcf_margin`) |
| Active | Test-only |
| Database-facing | No |
| Config-adjacent | No |
| Provider access | No |
| Cleanup risk | Low — removal would require deleting `tests/test_kpi_service.py` |

**Finding:** `kpi_service.py` is a pure utility module (safe division, 4 margin calculations). It has zero production callers — no CLI command, no service, no application layer imports from it. It is tested but not wired into any production pipeline. The equivalent margin calculations in `atlas/providers/yahoo.py` use their own inline implementations on `YahooFinancials` fields — they do not call `kpi_service`.

**Classification:** Test-only service with zero production callers. Cleanup candidate for Sprint 198.

---

## Adjacent Zero-Caller Dead Code (Discovered in Audit)

These are in `atlas/models/` and `atlas/reports/` — not in `atlas/database/` or `atlas/services/` — but discovered during caller-map analysis.

### `atlas/models/investment_report.py` (3 lines)

```python
from atlas.analysis.engine import InvestmentReport, ScoreCategory
__all__ = ["InvestmentReport", "ScoreCategory"]
```

| Attribute | Value |
|---|---|
| Purpose | Re-export shim for `InvestmentReport` and `ScoreCategory` |
| Source | `atlas.analysis.engine` |
| Production callers | **None** — zero callers import from `atlas.models.investment_report` or `atlas.models` for these symbols |
| Test callers | None |
| Active | No |

**Classification:** Dead re-export shim. Zero callers. `atlas/models/__init__.py` does not include `InvestmentReport` or `ScoreCategory` in its `__all__` or `__getattr__`. All production callers of `InvestmentReport` import directly from `atlas.analysis` or `atlas.analysis.engine`. Safe to remove in Sprint 198.

### `atlas/reports/investment_card.py` (23 lines)

| Attribute | Value |
|---|---|
| Purpose | Generates a formatted investment card string for a ticker |
| Public functions | `generate_investment_card(ticker)` |
| Production callers | **None** — zero callers invoke `generate_investment_card` anywhere in atlas or tests |
| Test callers | None |
| Active | No |

**Classification:** Dead function. Zero callers (production or test). Safe to remove in Sprint 198, along with `atlas/reports/__init__.py` if it contains only this reference.

---

## Export Review

Neither `atlas/database/` nor `atlas/services/` define `__init__.py` files. Both packages export their symbols directly via submodule imports. This is correct for service/infrastructure layers.

`atlas/models/__init__.py` uses a `__getattr__` lazy loader exposing `Company` and `FinancialHistory` — active and intentional.

`atlas/models/investment_report.py` has `__all__ = ["InvestmentReport", "ScoreCategory"]` but is never imported — dead.

---

## Caller Map Summary

| Symbol | Package | Production callers | Test callers |
|---|---|---|---|
| `Base` | `atlas.database.connection` | `entities.py`, `database_service.py` | — |
| `get_engine` | `atlas.database.connection` | `database_service.py` | — |
| `get_session` | `atlas.database.connection` | `company_service.py`, `financial_import_service.py` | `test_financial_import_service.py` |
| `init_database` | `atlas.services.database_service` | `atlas/cli/main.py` | `test_financial_import_service.py` |
| `add_company` | `atlas.services.company_service` | `atlas/cli/main.py` | — |
| `list_companies` | `atlas.services.company_service` | `atlas/cli/main.py` | — |
| `get_company_by_ticker` | `atlas.services.company_service` | `atlas/reports/investment_card.py` | — |
| `import_financials` | `atlas.services.financial_import_service` | `atlas/cli/main.py` | `test_financial_import_service.py` |
| `gross_margin` | `atlas.services.kpi_service` | **None** | `test_kpi_service.py` |
| `operating_margin` | `atlas.services.kpi_service` | **None** | `test_kpi_service.py` |
| `net_margin` | `atlas.services.kpi_service` | **None** | — |
| `fcf_margin` | `atlas.services.kpi_service` | **None** | `test_kpi_service.py` |
| `safe_divide` | `atlas.services.kpi_service` | **None** | — |

---

## Config / Database / Services Boundary Review

| Direction | Status |
|---|---|
| `atlas/config.py` → `atlas/database/` | No ✓ |
| `atlas/config.py` → `atlas/services/` | No ✓ |
| `atlas/database/` → `atlas/config.py` | `connection.py` imports `DATABASE_PATH` ✓ correct direction |
| `atlas/database/` → `atlas/services/` | No ✓ — database does not import upward |
| `atlas/services/` → `atlas/config.py` | `database_service.py` imports `DATABASE_PATH` ✓ correct |
| `atlas/services/` → `atlas/database/` | `database_service.py`, `company_service.py`, `financial_import_service.py` all import from `atlas.database.connection` ✓ correct |
| `atlas/services/` → `atlas/models/` | `database_service.py`, `company_service.py`, `financial_import_service.py` all import from `atlas.models` ✓ correct |
| `atlas/cli/` → `atlas/services/` | `atlas/cli/main.py` imports `init_database`, `add_company`, `list_companies`, `import_financials` ✓ correct |

**All boundary directions are correct.** Config → database → services → CLI. No upward dependencies. No circular dependencies.

---

## SQLAlchemy / SQLite / Schema Review

| Aspect | Assessment |
|---|---|
| ORM base | `Base = DeclarativeBase()` in `atlas/database/connection.py` |
| Engine | SQLite (`sqlite:///...`), created with `future=True` per call via `get_engine()` |
| Session | `sessionmaker(bind=engine, future=True)()` — session returned per call by `get_session()` |
| Schema creation | Explicit: `Base.metadata.create_all(engine)` + `conn.executescript(schema_sql)` in `init_database()` |
| Migrations | None — schema is fixed; re-running `init_database()` is idempotent via `CREATE TABLE IF NOT EXISTS` |
| Database path | From `atlas.config.DATABASE_PATH`; overridable via `db_path` arg — deterministic ✓ |
| Schema/ORM gap | 6 of 8 schema tables have no ORM model — intentional, not a bug |
| Test coverage | `test_financial_import_service.py` exercises `init_database` + session ✓ |

**Observation on session lifecycle:** `get_session()` in `connection.py` does not use a context manager pattern internally — it returns a plain `Session`. Callers (`company_service.py`, `financial_import_service.py`) use it as a context manager via `with get_session() as session:`. This works because SQLAlchemy `Session` supports context manager protocol. Correct and stable.

---

## Services Behavior Review

| Service | Responsibility | Database access | Business logic | Cleanup warranted |
|---|---|---|---|---|
| `database_service.py` | Schema init and ORM model registration | ✓ | No | No |
| `company_service.py` | Company CRUD | ✓ | Minimal | No |
| `financial_import_service.py` | CSV import to `financial_history` | ✓ | CSV parsing, validation | No |
| `kpi_service.py` | Margin calculations | No | Yes — pure math | **Yes — zero production callers** |

`kpi_service.py` stands out: it is a pure math utility (no database access, no imports) with no production callers. Its test is `test_kpi_service.py`. It does not duplicate domain/capability logic — it is a standalone utility that was never wired into a production pipeline.

---

## Provider Boundary Review

| Search term | Found in `atlas/database/` | Found in `atlas/services/` | Classification |
|---|---|---|---|
| `atlas.providers` | No | No | ✓ |
| `CompanyDataProvider` | No | No | ✓ |
| `MockCompanyAnalysisProvider` | No | No | ✓ |
| `YahooFinanceProvider` | No | No | ✓ |
| `requests` / `fetch` / `http` / `urlopen` | No | No | ✓ |

**Neither package imports providers or performs network access.** Provider-free. ✓

---

## Storage Boundary Review

`atlas/storage/` does not exist. No `atlas.storage` import exists anywhere in the codebase. The database layer (`atlas/database/` + `atlas/services/`) is the storage layer for Atlas. No boundary conflict. No cleanup warranted.

---

## Stale Import Audit

Searched `atlas/database/` and `atlas/services/` for all stale references from closed cleanup tracks:

| Search term | Found | Classification |
|---|---|---|
| `atlas.reasoning` / `ReasoningInput` / `ReasoningReport` | No | ✓ |
| `atlas.analysis.portfolio/growth/macro/…` | No | ✓ |
| `PortfolioAnalysis/PortfolioSignal/…` | No | ✓ |
| `CompanyAnalysisProvider` | No | ✓ |
| `render_comparison_result` | No | ✓ |
| `YahooCompany/YahooFinancials/YahooMarketData` | No | ✓ |
| `ReasoningEngine` | No | ✓ |
| `check_reasoning_report` / `check_intelligence_report` | No | ✓ |

**No stale imports of any kind** in either package.

---

## Blueprint / Database-Services Model Review

| Criterion | Assessment |
|---|---|
| Is `atlas/database/` Blueprint-aligned as persistence infrastructure? | ✓ Yes — owns connection, ORM base, session lifecycle |
| Is `atlas/services/` Blueprint-aligned as orchestration/persistence? | ✓ Yes — services own persistence orchestration; business logic is minimal and appropriate |
| Do services duplicate domain/capability logic? | No ✓ |
| Does database duplicate storage behavior? | No — `atlas/storage/` doesn't exist; database IS the storage layer ✓ |
| Do database/services own provider behavior? | No ✓ |
| Should database/services remain active? | ✓ Yes — they power `atlas init`, `atlas add-company`, `atlas import-financials`, and the financial import pipeline |
| Would any migration change behavior? | Yes — no migration warranted |

---

## Cleanup Candidate Classification

| Candidate | Location | Evidence | Production callers | Test callers | Risk | Sprint 198 |
|---|---|---|---|---|---|---|
| `kpi_service.py` | `atlas/services/` | Zero production callers; pure math utility not wired to any pipeline | 0 | 3 (in `test_kpi_service.py`) | Low — delete file + test | Yes — primary candidate |
| `atlas/models/investment_report.py` | `atlas/models/` | Dead re-export shim; zero callers anywhere | 0 | 0 | Low — delete file | Yes — secondary candidate |
| `atlas/reports/investment_card.py` | `atlas/reports/` | Dead function; zero callers in production or tests | 0 | 0 | Low — delete file; check `atlas/reports/__init__.py` | Yes — tertiary candidate |
| Schema/ORM gap (6 unmapped tables) | `atlas/database/schema.sql` | 6 tables exist in SQL but no ORM models | N/A | N/A | — | Leave unchanged — intentional |
| All active database symbols | `atlas/database/` | All have active callers | Multiple | Multiple | — | Leave unchanged |
| All active service symbols | `atlas/services/` | All have active callers (except kpi_service) | Multiple | Multiple | — | Leave unchanged |

**Primary Sprint 198 recommendation:** Remove `atlas/services/kpi_service.py` + `tests/test_kpi_service.py` + the two adjacent dead symbols (`atlas/models/investment_report.py`, `atlas/reports/investment_card.py`).

---

## Sprint 198 Target Recommendation

**Recommended:** Remove zero-caller dead code discovered during database/services audit, then close the database/services cleanup track.

**Specific cleanup targets:**
1. Delete `atlas/services/kpi_service.py` — zero production callers, pure math utility not wired to any production pipeline
2. Delete `tests/test_kpi_service.py` — guardrail for dead code
3. Delete `atlas/models/investment_report.py` — dead re-export shim, zero callers
4. Delete `atlas/reports/investment_card.py` — dead function, zero callers
5. If `atlas/reports/` has only `investment_card.py`, delete the directory too (check for `__init__.py`)
6. Verify all active database and services exports remain unchanged
7. Close database/services cleanup track

**Rationale:** All 4 candidates have zero production callers. Removal creates no behavioral change. Cleanup improves the repository surface by eliminating test-confirmed-dead code. All active database, services, and models symbols are untouched.

---

## Reopening Conditions

This plan may be reopened if:
- A new service is added to `atlas/services/` without documentation
- A new Atlas package import is added to `atlas/database/` (boundary violation)
- `kpi_service.py` or `investment_card.py` equivalents are re-added
- A storage/repository layer is introduced that overlaps with `atlas/database/`
- ORM models are added for the 6 currently-unmodeled schema tables

---

## Sprint 197 Verification Table

| Check | Result |
|---|---|
| `atlas/database/connection.py` exists, 20 lines | ✓ |
| `atlas/database/schema.sql` exists, 8 tables | ✓ |
| `atlas/services/` has 4 modules, 164 lines total | ✓ |
| No `__init__.py` in database or services | ✓ |
| `Base`, `get_engine`, `get_session` importable | ✓ |
| All active service symbols have production callers | ✓ (except kpi_service) |
| `kpi_service.py` zero production callers identified | ✓ |
| `atlas/models/investment_report.py` zero callers identified | ✓ |
| `atlas/reports/investment_card.py` zero callers identified | ✓ |
| No Atlas imports in `atlas/database/` beyond `atlas.config` | ✓ |
| No provider coupling in database or services | ✓ |
| No network access in database or services | ✓ |
| No stale imports from closed cleanup tracks | ✓ |
| Boundary direction: config ← database ← services ← CLI | ✓ |
| `atlas/storage/` does not exist | ✓ |
| Compile check | Green ✓ |
| Full test suite | **1654 passed, 3 skipped** ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Behavior changes | None |

# Storage Boundary Cleanup Plan

**Created:** 2026-07-03 (Sprint 200)  
**Status:** CLOSED — `atlas/storage/` does not exist. Storage and persistence behavior are fully owned by `atlas/database/` and `atlas/services/`. No cleanup warranted. No runtime behavior changed.

---

## Important Framing

Sprint 200 audits the storage boundary following the closure of `atlas/config/` (Sprint 196) and `atlas/database/` + `atlas/services/` (Sprint 198). The storage boundary was noted as "does not exist" in every prior audit from Sprint 195 onward.

This sprint uses repository reality. `atlas/storage/` does not exist as a package directory or module. There is no `atlas.storage` import anywhere in the codebase. The storage layer for Atlas is fully owned by:

- `atlas/database/` — SQLAlchemy ORM, SQLite connection/session, schema creation
- `atlas/services/` — persistence orchestration and application workflows

---

## Storage Existence Check

**Classification: `does_not_exist`**

```text
ls atlas/storage/
ls: atlas/storage/: No such file or directory
```

`atlas/storage/` does not exist as a package directory, module file, or placeholder.

---

## Repo-Wide Storage Reference Search

### Python imports

Full repo-wide search for `atlas.storage` or `from atlas.storage`:

```
grep -rn "atlas\.storage\|from atlas\.storage" --include="*.py"
```

**Result: zero hits.** No Python file imports `atlas.storage`.

### Documentation references

Five documentation files reference `atlas/storage/` — all as historical confirmations that the package does not exist:

| File | Reference type | Content |
|---|---|---|
| `docs/ConfigCleanupPlan.md` | Storage boundary review | "`atlas/storage/` does not exist as a package" — confirmed Sprint 195 and Sprint 196 ✓ |
| `docs/DatabaseServicesCleanupPlan.md` | Storage boundary review | "`atlas/storage/` does not exist. No `atlas.storage` import exists anywhere." — confirmed Sprint 197 and Sprint 198 ✓ |
| `docs/DecisionLog.md` | Sprint notes | Multiple sprint entries note `atlas/storage/` does not exist ✓ |
| `docs/ReleaseCandidateCheckpoint.md` | Sprint 199 verification | `atlas/storage/ does not exist ✓` in Sprint 199 check table |
| `docs/LegacyConsolidationPlan.md` | Sprint status | Notes storage audits are next ✓ |

**Classification of all hits:** docs/historical notes. No active runtime code references `atlas.storage`. No stale references. No cleanup needed.

### Broader storage-term search

Searching for generic storage-adjacent terms in `atlas/` Python files:

| Term | Hits in `atlas/` | Classification |
|---|---|---|
| `Repository` | None as class/import | — |
| `Persistence` | None as class/import | — |
| `persistence` | `docs/` references only | Docs references to persistence concepts, not imports |
| `Storage` | None as class/import in atlas/ | — |
| `storage` | `docs/` references only | Docs references, not runtime imports |

No generic storage abstraction exists in the Atlas codebase.

---

## Database / Services Ownership Verification

Storage and persistence behavior is owned entirely by two packages:

### `atlas/database/` — persistence infrastructure

| Responsibility | Owner | Status |
|---|---|---|
| SQLAlchemy `DeclarativeBase` (`Base`) | `atlas/database/connection.py` | Active ✓ |
| SQLite engine creation (`get_engine`) | `atlas/database/connection.py` | Active ✓ |
| Session lifecycle (`get_session`) | `atlas/database/connection.py` | Active ✓ |
| Schema definition | `atlas/database/schema.sql` (8 tables) | Active ✓ |
| ORM model definitions | `atlas/models/entities.py` (`Company`, `FinancialHistory`) | Active ✓ |
| Schema/ORM registration | `atlas/services/database_service.py` (`# noqa: F401`) | Active ✓ |

### `atlas/services/` — persistence orchestration

| Responsibility | Owner | Status |
|---|---|---|
| Database initialization (`init_database`) | `atlas/services/database_service.py` | Active ✓ |
| Company CRUD | `atlas/services/company_service.py` | Active ✓ |
| Financial data import | `atlas/services/financial_import_service.py` | Active ✓ |

No hidden or undocumented storage layer exists. No duplication. No split ownership. The ownership picture is complete and clean.

---

## Config / Database / Services Boundary Verification

Sprint 199 findings remain unchanged.

| Direction | Status |
|---|---|
| `atlas/config.py` → `atlas/database/` | No — config consumed by database ✓ |
| `atlas/config.py` → `atlas/services/` | No — config consumed by services ✓ |
| `atlas/database/` → `atlas/config.py` | `DATABASE_PATH` import — correct direction ✓ |
| `atlas/database/` → `atlas/services/` | No upward dependency ✓ |
| `atlas/services/` → `atlas/config.py` | `DATABASE_PATH` import — correct direction ✓ |
| `atlas/services/` → `atlas/database/` | Session/engine imports — correct direction ✓ |
| Circular dependencies | None ✓ |
| Cleanup warranted | None ✓ |

---

## SQLAlchemy / SQLite / Schema Verification

Unchanged from Sprint 199.

| Check | Result |
|---|---|
| `Base = DeclarativeBase()` in `connection.py` | Unchanged ✓ |
| SQLite engine with `future=True` | Unchanged ✓ |
| `sessionmaker` session lifecycle | Unchanged ✓ |
| Schema creation: `create_all` + `executescript` | Unchanged ✓ |
| 8-table `schema.sql` | Unchanged ✓ |
| 2 ORM models (`Company`, `FinancialHistory`) | Unchanged ✓ |
| Schema/ORM gap (6 unmapped tables — intentional) | Unchanged ✓ |
| Database path from `atlas.config.DATABASE_PATH` | Unchanged ✓ |

---

## Services Persistence Verification

Unchanged from Sprint 199.

| Service | Active symbols | Status |
|---|---|---|
| `database_service.py` | `init_database` | Unchanged ✓ |
| `company_service.py` | `add_company`, `list_companies`, `get_company_by_ticker` | Unchanged ✓ |
| `financial_import_service.py` | `import_financials`, `REQUIRED_COLUMNS`, `NUMERIC_COLUMNS` | Unchanged ✓ |

---

## Provider Boundary Verification

| Package | Provider imports | Network access |
|---|---|---|
| `atlas/database/` | None ✓ | None ✓ |
| `atlas/services/` | None ✓ | None ✓ |
| `atlas/storage/` | Does not exist ✓ | N/A |

No new provider behavior. No network access in storage/database/services boundary.

---

## Sprint 198 Removal Guard Verification

All Sprint 198 removal targets confirmed absent:

| Target | Status |
|---|---|
| `atlas/services/kpi_service.py` | Absent ✓ |
| `tests/test_kpi_service.py` | Absent ✓ |
| `atlas/models/investment_report.py` | Absent ✓ |
| `atlas/reports/investment_card.py` | Absent ✓ |
| `atlas/reports/` directory | Absent ✓ |

`atlas/reports/` status matches Sprint 198/199 documentation exactly. No follow-up needed.

---

## Stale Import Audit

Full search of `atlas/database/`, `atlas/services/`, and storage-adjacent code for stale references from closed cleanup tracks:

| Search term | Found | Classification |
|---|---|---|
| `atlas.reasoning` / `ReasoningInput` / `ReasoningReport` | No | ✓ |
| `check_reasoning_report` / `check_intelligence_report` / `check_suitability_assessment` | No | ✓ |
| `atlas.analysis.portfolio` / `PortfolioAnalysis` / `PortfolioSignal` | No | ✓ |
| `PortfolioRecommendation` / `CompanyPortfolioProfile` / `PortfolioIntelligenceEngine` | No | ✓ |
| `portfolio_fit_input_from_profile` | No | ✓ |
| `CompanyAnalysisProvider` | No | ✓ |
| `atlas.analysis.comparison/memory/scoring/watchlist/growth/macro/moat/quality/sentiment/technicals/valuation` | No | ✓ |
| `render_comparison_result` | No | ✓ |
| `YahooCompany` / `YahooFinancials` / `YahooMarketData` | Active definitions in `atlas/providers/yahoo.py` only | Active, expected ✓ |

**No stale active references.** No cleanup warranted.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Classification | Sprint 201 |
|---|---|---|---|
| `atlas/storage/` package | Does not exist | `nonexistent_storage_package` — no action needed | No |
| `atlas.storage` imports | Zero hits in any Python file | `nonexistent_storage_package` — no stale imports | No |
| Storage docs references | 5 files — all historical confirmations | `docs/historical note` — correct and accurate | No |
| `atlas/database/` persistence ownership | SQLAlchemy ORM, connection, session, schema — all active | `acceptable_infrastructure_ownership` | Leave unchanged |
| `atlas/services/` orchestration | `init_database`, company CRUD, financial import — all active | `services-owned_orchestration` | Leave unchanged |
| Config/database/services boundary | Correct throughout Sprint 195–199 | `acceptable_infrastructure_ownership` | Leave unchanged |

**Summary:** No cleanup warranted. Storage boundary is clean, fully owned, and unduplicated.

---

## Track Closure

**The `atlas/storage/` boundary cleanup track is CLOSED as of Sprint 200.**

**Closure rationale:**
- `atlas/storage/` does not exist — classification: `nonexistent_storage_package`
- No active Python code imports `atlas.storage`
- No stale storage imports anywhere in the codebase
- Storage/persistence behavior is fully and cleanly owned by `atlas/database/` + `atlas/services/`
- Config/database/services boundary is stable and correct
- SQLAlchemy/SQLite/schema behavior is unchanged
- Sprint 198 removal targets remain absent
- Tests pass, demo passes, release verification passes
- No provider/network behavior introduced

**Future reopening condition:** Reopen only if a storage package is introduced, stale `atlas.storage` imports appear, database/services ownership changes, provider-boundary issues emerge in the persistence layer, persistence/schema behavior changes, or a clear storage/repository pattern migration target emerges.

---

## Sprint 200 Verification Table

| Check | Result |
|---|---|
| `atlas/storage/` exists | **No** — does not exist ✓ |
| Python imports of `atlas.storage` | **Zero** — no hits ✓ |
| Docs references to `atlas/storage/` | 5 files — all historical, all correct ✓ |
| Storage ownership: `atlas/database/` | ✓ SQLAlchemy ORM, connection, session, schema |
| Storage ownership: `atlas/services/` | ✓ init, CRUD, import orchestration |
| No hidden storage layer | ✓ |
| Config/database/services boundary stable | ✓ |
| SQLAlchemy/SQLite/schema unchanged | ✓ |
| Sprint 198 removals confirmed absent | ✓ (5 targets) |
| `atlas/reports/` absent | ✓ |
| No stale imports from closed cleanup tracks | ✓ |
| No provider coupling in database/services | ✓ |
| No network access in database/services | ✓ |
| Compile check | Green ✓ |
| Full test suite | **1671 passed, 3 skipped** ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Behavior changes | None |
| Track status | **CLOSED Sprint 200** ✓ |

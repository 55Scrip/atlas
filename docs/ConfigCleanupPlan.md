# Config Cleanup Plan

**Created:** 2026-07-03 (Sprint 195)  
**Updated:** 2026-07-03 (Sprint 196)  
**Status:** CLOSED — Sprint 196 confirmed Sprint 195 findings unchanged. No cleanup warranted. No runtime behavior changed.

---

## Important Framing

`atlas/config/` does not exist as a package directory. The configuration surface is a single module:

```text
atlas/config.py   (6 lines)
```

Sprint 195 audits this module as the Atlas configuration layer. No cleanup track was previously opened for `atlas/config.py`.

---

## Executive Summary

`atlas/config.py` is a **6-line infrastructure module**. It reads one environment variable (`ATLAS_HOME`), derives two path constants (`BASE_DIR`, `DATABASE_DIR`, `DATABASE_PATH`), and exposes them for use by the database layer. The module has zero imports from Atlas packages, zero provider coupling, zero network access, zero stale imports, and exactly 2 active production callers — both in the database/services layer. It is foundational infrastructure at its simplest: no cleanup warranted.

---

## Package Inventory

### `atlas/config.py` (6 lines)

```python
from pathlib import Path
import os

BASE_DIR = Path(os.environ.get("ATLAS_HOME", Path.cwd())).resolve()
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "atlas.db"
```

| Attribute | Value |
|---|---|
| File path | `atlas/config.py` |
| Line count | 6 |
| Type | Single-file module (not a package) |
| Public constants | `BASE_DIR`, `DATABASE_DIR`, `DATABASE_PATH` |
| Public classes | None |
| Public functions | None |
| Private helpers | None |
| `__all__` | None defined |
| Environment variable | `ATLAS_HOME` (falls back to `Path.cwd()` if unset) |
| Network access | None |
| File I/O | None — paths only, no reads/writes |
| Provider imports | None |
| Atlas package imports | None |
| Active | ✓ |
| Foundational infrastructure | ✓ |
| Runtime-facing | ✓ (via database layer) |
| CLI-facing | Indirect — CLI calls `init_database()` which uses `DATABASE_PATH` |
| Provider-adjacent | No |
| Storage-adjacent | ✓ — sole configuration source for database location |
| Blueprint-aligned | Yes — pure infrastructure constants, no runtime logic |

---

## Export Review

`atlas/config.py` defines no `__all__`. Three public module-level constants are importable:

| Symbol | Type | Active | Callers | Notes |
|---|---|---|---|---|
| `BASE_DIR` | `Path` | ✓ (indirectly — derived) | None directly | Used internally to compute `DATABASE_DIR` |
| `DATABASE_DIR` | `Path` | ✓ (indirectly — derived) | None directly | Used internally to compute `DATABASE_PATH` |
| `DATABASE_PATH` | `Path` | ✓ | 2 production callers | Default database file path |

No stale exports. No zero-caller public symbols intended as external API (the two intermediary constants `BASE_DIR` and `DATABASE_DIR` are module-internal derivations).

---

## Caller Map

Full repo-wide search for `atlas.config` references:

| Caller | Import | Role | Active |
|---|---|---|---|
| `atlas/database/connection.py:4` | `from atlas.config import DATABASE_PATH` | Default path for `get_engine()` and `get_session()` — overridable via `db_path` argument | ✓ Active production caller |
| `atlas/services/database_service.py:5` | `from atlas.config import DATABASE_PATH` | Default path for `init_database()` — overridable via `db_path` argument | ✓ Active production caller |

**Total: 2 active production callers. Zero test callers. Zero docs references to specific symbols.**

Neither `BASE_DIR` nor `DATABASE_DIR` are imported anywhere outside `atlas/config.py`.

### CLI dependency chain

```text
atlas/cli/main.py:107  → from atlas.services.database_service import init_database
atlas/cli/main.py:160  → init_database()  (called in `atlas init` command)
                       → uses DATABASE_PATH as default
                       → reads ATLAS_HOME environment variable
```

`atlas/cli/main.py` does not import `atlas.config` directly. The dependency is: CLI → `database_service` → `config`.

---

## Configuration / Provider / Runtime Boundary Review

### Imports INTO `atlas/config.py`

| Import | Source | Role | Acceptable? |
|---|---|---|---|
| `from pathlib import Path` | Python stdlib | Path construction | ✓ |
| `import os` | Python stdlib | Environment variable access | ✓ |

`atlas/config.py` imports **nothing from Atlas packages**. It is fully stdlib-only.

### Imports FROM `atlas/config.py` into Atlas packages

| Importer | Symbol used | Dependency direction | Acceptable? |
|---|---|---|---|
| `atlas/database/connection.py` | `DATABASE_PATH` | Config → consumed by database layer | ✓ |
| `atlas/services/database_service.py` | `DATABASE_PATH` | Config → consumed by services layer | ✓ |

**Dependency direction is correct.** Config is the lowest layer — it depends on nothing within Atlas. Database and services layer depend on config. CLI depends on services. This is the correct direction.

**No circular dependencies.** Config cannot create circular dependencies because it imports nothing from Atlas.

### Boundary assessment

| Boundary | Status |
|---|---|
| Config imports CLI | No ✓ |
| Config imports providers | No ✓ |
| Config imports domains | No ✓ |
| Config imports capabilities | No ✓ |
| Config imports adapters | No ✓ |
| Config imports analysis | No ✓ |
| Config imports storage | No ✓ |
| Config performs network access | No ✓ |
| Config performs file I/O | No ✓ — path construction only |
| Config selects providers | No ✓ |
| Config reads env vars | Yes — `ATLAS_HOME` (one var, deterministic) |

All boundaries are correct.

---

## Provider Boundary Review

Search results for provider-related terms in `atlas/config.py`:

| Search term | Found | Classification |
|---|---|---|
| `atlas.providers` | No | — |
| `CompanyDataProvider` | No | — |
| `MockCompanyAnalysisProvider` | No | — |
| `YahooFinanceProvider` | No | — |
| `provider` | No | — |
| `fetch` / `requests` / `http` / `urlopen` | No | — |
| `network` / `api` | No | — |

**No provider coupling. No network access.** Config is provider-free.

---

## Runtime Defaults Review

`atlas/config.py` defines one runtime default:

| Default | Value | Consumed by | Effect | Behavior-changing if modified? |
|---|---|---|---|---|
| `ATLAS_HOME` fallback | `Path.cwd()` | `BASE_DIR`, then `DATABASE_DIR`, then `DATABASE_PATH` | Database file location defaults to `./database/atlas.db` when `ATLAS_HOME` not set | Yes — changing fallback would change where database is created |

The default is deterministic: if `ATLAS_HOME` is unset, `Path.cwd()` resolves to the working directory at import time. This is expected behavior for a local-first database tool. No stale or unused defaults.

---

## Environment and File Loading Review

| Attribute | Value |
|---|---|
| Environment variable | `ATLAS_HOME` |
| Purpose | Override base directory for all Atlas data files |
| Fallback | `Path.cwd()` |
| File format | N/A — no config file loaded |
| Loading order | Single env var read at module import time |
| Error behavior | No error — silently falls back to `Path.cwd()` if unset |
| Writes | None — path constants only |
| Test coverage | No dedicated test for env var behavior |

**`ATLAS_HOME` is the only configuration knob.** No config file is read. No YAML/JSON/TOML loading. No dotenv. Simple and correct for a local SQLite tool.

**Observation (Sprint 195):** No test covered the `ATLAS_HOME` env var path. Sprint 195 added `test_atlas_home_env_var_respected` in `tests/test_config_sprint195.py`. Now covered.

---

## Storage Boundary Review

| Direction | Status |
|---|---|
| `atlas/config.py` → `atlas/storage/` | `atlas/storage/` does not exist as a package |
| `atlas/database/` → `atlas/config.py` | `connection.py` imports `DATABASE_PATH` ✓ — correct direction |
| `atlas/services/` → `atlas/config.py` | `database_service.py` imports `DATABASE_PATH` ✓ — correct direction |

**`atlas/storage/` does not exist.** The storage layer is `atlas/database/` (SQLAlchemy ORM, SQLite connection) and `atlas/services/` (higher-level database operations). Both depend on `atlas/config.py` for the database path — correct dependency direction.

**Sprint 196 implication:** If a future sprint audits `atlas/database/` or `atlas/services/`, the config boundary is already clean and requires no pre-work.

---

## Stale Import Audit

Searched `atlas/config.py` for all stale references from closed cleanup tracks:

| Search term | Found | Classification |
|---|---|---|
| `atlas.reasoning` | No | ✓ |
| `ReasoningInput/ReasoningReport` | No | ✓ |
| `atlas.analysis.portfolio/growth/macro/…` | No | ✓ |
| `PortfolioAnalysis/PortfolioSignal/…` | No | ✓ |
| `CompanyAnalysisProvider` | No | ✓ |
| `render_comparison_result` | No | ✓ |
| `YahooCompany/YahooFinancials/YahooMarketData` | No | ✓ |
| `ReasoningEngine` | No | ✓ |

**No stale imports of any kind.** The module has only stdlib imports.

---

## Blueprint / Config Model Review

| Criterion | Assessment |
|---|---|
| Is `atlas/config.py` Blueprint-aligned? | ✓ Yes — pure infrastructure constants, no runtime logic |
| Does config own only configuration structures/defaults/loading? | ✓ Yes — 6 lines, one env var, three path constants |
| Does config duplicate provider selection logic? | No ✓ |
| Does config duplicate storage settings? | No ✓ — it IS the canonical storage settings source |
| Does config own runtime orchestration that belongs elsewhere? | No ✓ |
| Should config remain as foundational infrastructure? | ✓ Yes |
| Would migration change behavior? | Yes — config is the canonical source; migration unnecessary |
| Is `atlas/config.py` the appropriate location for this? | ✓ Yes — single-file, stdlib-only, lowest layer |

`atlas/config.py` is architecturally exemplary for its role. It is the thinnest possible infrastructure module: one env var read, three derived path constants, no imports from Atlas, no logic beyond path derivation.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Sprint 196 |
|---|---|---|---|---|
| `BASE_DIR` | Intermediate path constant, no external callers | 0 external | — | Leave unchanged — internal derivation, not stale |
| `DATABASE_DIR` | Intermediate path constant, no external callers | 0 external | — | Leave unchanged — internal derivation, not stale |
| `DATABASE_PATH` | 2 active production callers | 2 | — | Leave unchanged — active and required |
| `ATLAS_HOME` env var | 1 read site | — | — | Leave unchanged — single authoritative config knob |
| Missing `__all__` | Not defined | — | — | Not a problem — single-module infrastructure; no `__all__` needed |
| No test for `ATLAS_HOME` env var | No test covers env var override path | Low | Low | Optional — guardrail test could verify env var is respected |

**Summary:** No cleanup warranted. Zero stale symbols. Zero dead helpers. Zero boundary issues. Zero provider coupling. The one observation (no env var test) is low-priority and optional.

---

## Guardrail Tests

Added `tests/test_config_sprint195.py` with 6 tests:

1. `test_config_database_path_importable` — `DATABASE_PATH` importable from `atlas.config`
2. `test_config_database_path_is_path_object` — `DATABASE_PATH` is a `pathlib.Path`
3. `test_config_database_path_ends_with_atlas_db` — filename is `atlas.db`
4. `test_config_does_not_import_atlas_packages` — `atlas.config` imports only stdlib (`pathlib`, `os`)
5. `test_config_does_not_import_providers` — no provider imports
6. `test_atlas_home_env_var_respected` — when `ATLAS_HOME` is set, `DATABASE_PATH` is derived from it

---

## Sprint 196 Closure

**Decision:** Close the config cleanup track.

**Rationale:** Sprint 196 confirmed all Sprint 195 findings unchanged. `atlas/config.py` is the thinnest possible infrastructure module — 6 lines, stdlib-only, zero Atlas imports, zero provider coupling, zero network access, 2 active production callers. All boundaries are correct. No stale imports from any closed cleanup track. No dead symbols. No cleanup warranted. Further cleanup would create churn without architectural benefit.

**Final verified state (Sprint 196):**
- `atlas/config.py` exists, 6 lines, unchanged ✓
- 3 public constants (`BASE_DIR`, `DATABASE_DIR`, `DATABASE_PATH`) — unchanged ✓
- 2 active production callers (`database/connection.py`, `services/database_service.py`) — unchanged ✓
- `ATLAS_HOME` env var: unchanged, tested by `test_atlas_home_env_var_respected` ✓
- No Atlas package imports ✓
- No provider imports ✓
- No network access ✓
- No stale imports from closed cleanup tracks ✓
- Boundary direction: config ← database ← services ← CLI — unchanged ✓
- `atlas/storage/` does not exist (storage layer is `atlas/database/` + `atlas/services/`) ✓
- **1654 passed, 3 skipped | RC2 green | Demo passes ✓**

---

## Reopening Conditions

This plan may be reopened if:
- A new environment variable is added to `atlas/config.py` without documentation
- A new Atlas package import is added to `atlas/config.py` (boundary violation)
- `DATABASE_PATH` behavior changes
- A new caller imports `BASE_DIR` or `DATABASE_DIR` directly (should be treated as internal)
- A config file loading mechanism is added

---

## Sprint 196 Verification Table

| Check | Result |
|---|---|
| `atlas/config.py` exists | ✓ (single-file module, unchanged) |
| Line count | 6 ✓ |
| Public constants | 3 (`BASE_DIR`, `DATABASE_DIR`, `DATABASE_PATH`) ✓ |
| Active production callers | 2 — unchanged ✓ |
| `ATLAS_HOME` env var behavior | Unchanged; covered by guardrail test ✓ |
| Atlas package imports | None ✓ |
| Provider imports | None ✓ |
| Network access | None ✓ |
| Stale imports from closed tracks | None ✓ |
| Boundary violations | None ✓ |
| No cleanup warranted | ✓ |
| Compile check | Green ✓ |
| Full test suite | **1654 passed, 3 skipped** ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Behavior changes | None |
| Track status | **CLOSED Sprint 196** ✓ |

---

## Sprint 195 Verification Table

| Check | Result |
|---|---|
| `atlas/config.py` exists | ✓ (single-file module, not a package directory) |
| Line count | 6 ✓ |
| Public constants | 3 (`BASE_DIR`, `DATABASE_DIR`, `DATABASE_PATH`) ✓ |
| Public classes | 0 ✓ |
| Public functions | 0 ✓ |
| Environment variable | `ATLAS_HOME` (1 env var) ✓ |
| Atlas package imports | None ✓ |
| Provider imports | None ✓ |
| Network access | None ✓ |
| Active production callers | 2 (`database/connection.py`, `services/database_service.py`) ✓ |
| Stale imports from closed tracks | None ✓ |
| Boundary violations | None ✓ |
| Circular dependencies | None ✓ |
| `atlas/storage/` package | Does not exist ✓ |
| Compile check | Green ✓ |
| Full test suite | **1648 passed, 3 skipped** (pre-guardrail) ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Behavior changes | None |

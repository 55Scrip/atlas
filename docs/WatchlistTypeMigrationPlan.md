# Watchlist Type Migration Plan

**Created:** 2026-07-02 (Sprint 100)  
**Updated:** 2026-07-02 (Sprint 101)  
**Status:** MIGRATION COMPLETE — `WatchlistInput`/`WatchlistInputItem` live in `atlas/capabilities/watchlist_intelligence/`. `atlas/analysis/watchlist.py` fully deleted Sprint 101.

---

## Background

Sprint 99 deleted `WatchlistEngine`, `WatchlistAnalysis`, `WatchlistSignal`, `WatchlistRecommendation`,
and `render_watchlist_analysis` from `atlas/analysis/watchlist.py`. The file was slimmed to 33 lines
containing only two type-only dataclasses:

```python
@dataclass(frozen=True)
class WatchlistItem:
    ticker: str

@dataclass(frozen=True)
class Watchlist:
    name: str
    items: tuple[WatchlistItem, ...]

    @classmethod
    def from_json_file(cls, path: Path) -> "Watchlist": ...

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "Watchlist": ...
```

These types are CLI input parsers: they parse `{"name": ..., "tickers": [...]}` JSON into a
typed container that engines convert to `WatchlistIntelligenceInput`.

Full file deletion is blocked because 7 production modules and 5 test files import from
`atlas.analysis.watchlist`. This plan documents the migration path.

---

## Type-Only Import Inventory (Sprint 100 state)

### Production modules

| File | Imported | Purpose | Input modeling | Long-term destination | Risk |
|---|---|---|---|---|---|
| `atlas/analysis/__init__.py` | `Watchlist`, `WatchlistItem` | Re-export to callers via `atlas.analysis` namespace | Yes — re-export only | Remove when source moves | LOW — follows source |
| `atlas/cli/main.py` | `Watchlist` | CLI JSON parsing: `Watchlist.from_json_file(path)` | Yes — CLI input adapter | `atlas/capabilities/watchlist_intelligence/` | LOW |
| `atlas/conversation/engine.py` | `Watchlist` | Type annotation in `ConversationInput.watchlist: Watchlist \| None` | Yes — engine input type | Same as CLI | LOW |
| `atlas/decision/decision_context.py` | `Watchlist` | Type annotation in `DecisionContext.watchlist: Watchlist \| None` | Yes — context input type | Same as CLI | LOW |
| `atlas/home/engine.py` | `Watchlist` | Type annotation in engine input | Yes — engine input type | Same as CLI | LOW |
| `atlas/intelligence/engine.py` | `Watchlist` | Type annotation in `IntelligenceContext.watchlist: Watchlist \| None` | Yes — context input type | Same as CLI | LOW |
| `atlas/monitoring/engine.py` | `Watchlist` | Type annotation in `MonitoringContext.watchlist: Watchlist \| None` | Yes — context input type | Same as CLI | LOW |
| `atlas/watchlist_review/engine.py` | `Watchlist`, `WatchlistItem` | `WatchlistReviewInput.watchlist: Watchlist`; `WatchlistItem` used in helper return type | Yes — review input type | Same as CLI | LOW |

### Test files

| File | Imported | Purpose |
|---|---|---|
| `tests/test_conversation_engine.py` | `Watchlist`, `WatchlistItem` | Test input construction |
| `tests/test_decision_engine.py` | `Watchlist`, `WatchlistItem` | Test input construction |
| `tests/test_home_engine.py` | `Watchlist` | Test input construction |
| `tests/test_monitoring_engine.py` | `Watchlist` | Test input construction |
| `tests/test_watchlist_analyze_deprecation.py` | (via `importlib`) | Guardrail — verifies module state |

---

## The Two Watchlist Type Families

There are **two distinct `Watchlist` types** in Atlas. They must not be confused:

### 1. Legacy CLI input type (to be migrated)

```
atlas/analysis/watchlist.py
  Watchlist: name + items: tuple[WatchlistItem, ...]
  WatchlistItem: ticker: str
```

- Simple input shape for parsing `{"name": ..., "tickers": [...]}` JSON
- Engines convert this to `WatchlistIntelligenceInput` via the established pattern
- Used as an entry-point container; never stored, never serialized, never returned from engines

### 2. Shared canonical entity (Blueprint-aligned — leave untouched)

```
atlas/shared/entities.py
  Watchlist: id + name + tickers: tuple[str, ...] + owner_id + metadata
```

- Canonical domain entity owned by `atlas/shared/`
- Re-exported by `atlas/domains/watchlist/__init__.py`
- Used for domain modeling, not CLI input parsing
- **Different structure** — cannot substitute for legacy type without changing all 7 callers

### 3. Blueprint capability input type (Blueprint-aligned — leave untouched)

```
atlas/capabilities/watchlist_intelligence/models.py
  WatchlistItem: id + ticker + name + status + company + research_project + ...  (rich type)
  WatchlistIntelligenceInput: name + items: tuple[WatchlistItem, ...]
```

- Rich typed input for the Blueprint Watchlist Intelligence capability
- All five engines already convert legacy `Watchlist` → `WatchlistIntelligenceInput` via the
  established conversion pattern

---

## Recommended Long-Term Destination

**Destination: `atlas/capabilities/watchlist_intelligence/`**

Specifically: add a new `WatchlistInput` / `WatchlistInputItem` type to
`atlas/capabilities/watchlist_intelligence/models.py` (or a dedicated `watchlist_input.py` file).

### Rationale

1. **Blueprint alignment.** The legacy `Watchlist` is an input to the Watchlist Intelligence
   capability. Placing the input type in the capability module is consistent with how
   `WatchlistIntelligenceInput` already lives there.

2. **Avoids naming conflict with `atlas/shared/entities.py`.** `atlas/shared` already owns a
   `Watchlist` with a different structure. Renaming the migrated type to `WatchlistInput` /
   `WatchlistInputItem` avoids confusion and makes the purpose explicit (CLI input parsing).

3. **Avoids bloating `atlas/shared/`.** `atlas/shared/entities.py` owns canonical domain entities.
   The CLI parsing logic (`from_json_file`, `from_mapping`) belongs at the capability input layer,
   not the shared entity layer.

4. **Avoids capability depending on legacy `analysis/`.** Currently the capability
   (`atlas/capabilities/watchlist_intelligence/`) is clean of legacy dependencies. Moving the
   input type there eliminates the last reason for any module to import from `atlas.analysis.watchlist`.

5. **Low migration risk.** All 7 production callers use only `Watchlist` as a type annotation or
   call `Watchlist.from_json_file()`. Renaming to `WatchlistInput` with identical behavior requires
   only import path updates — no logic changes.

### Rejected alternatives

| Option | Reason rejected |
|---|---|
| `atlas/shared/entities.py` | Already owns `Watchlist` with different structure; `from_json_file`/`from_mapping` are CLI concerns, not entity concerns |
| `atlas/domains/watchlist/` | Domain `__init__.py` already re-exports `atlas.shared.Watchlist`; adding a different `Watchlist` here creates an unresolvable namespace conflict |
| Keep in `atlas/analysis/watchlist.py` | Perpetuates legacy `analysis/` as a type source; blocks full deletion |
| `atlas/models/` | No such module; creating one for two types is premature |

---

## Proposed Migration Sequence

### Sprint 101: Migrate `Watchlist` / `WatchlistItem` to capability input layer

**Goal:** Move `Watchlist` and `WatchlistItem` from `atlas/analysis/watchlist.py` to
`atlas/capabilities/watchlist_intelligence/` as `WatchlistInput` / `WatchlistInputItem`.
Delete `atlas/analysis/watchlist.py`. Clean `atlas/analysis/__init__.py`.

**Step 1 — Add new types to capability module:**

Add to `atlas/capabilities/watchlist_intelligence/models.py` (or a new `watchlist_input.py`):

```python
@dataclass(frozen=True)
class WatchlistInputItem:
    ticker: str

@dataclass(frozen=True)
class WatchlistInput:
    name: str
    items: tuple[WatchlistInputItem, ...]

    @classmethod
    def from_json_file(cls, path: Path) -> "WatchlistInput": ...

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "WatchlistInput": ...
```

**Step 2 — Update all 7 production callers** (import path change + rename):

| File | Before | After |
|---|---|---|
| `atlas/cli/main.py` | `from atlas.analysis.watchlist import Watchlist` | `from atlas.capabilities.watchlist_intelligence import WatchlistInput` |
| `atlas/conversation/engine.py` | `from atlas.analysis.watchlist import Watchlist` | `from atlas.capabilities.watchlist_intelligence import WatchlistInput` |
| `atlas/decision/decision_context.py` | `from atlas.analysis.watchlist import Watchlist` | `from atlas.capabilities.watchlist_intelligence import WatchlistInput` |
| `atlas/home/engine.py` | `from atlas.analysis.watchlist import Watchlist` | `from atlas.capabilities.watchlist_intelligence import WatchlistInput` |
| `atlas/intelligence/engine.py` | `from atlas.analysis.watchlist import Watchlist` | `from atlas.capabilities.watchlist_intelligence import WatchlistInput` |
| `atlas/monitoring/engine.py` | `from atlas.analysis.watchlist import Watchlist` | `from atlas.capabilities.watchlist_intelligence import WatchlistInput` |
| `atlas/watchlist_review/engine.py` | `from atlas.analysis.watchlist import Watchlist, WatchlistItem` | `from atlas.capabilities.watchlist_intelligence import WatchlistInput, WatchlistInputItem` |

**Step 3 — Update type annotations** in all 7 callers:
- `watchlist: Watchlist | None` → `watchlist: WatchlistInput | None`
- `WatchlistItem` in helper returns → `WatchlistInputItem`

**Step 4 — Update conversion pattern** (engines already convert to `WatchlistIntelligenceInput`):
- `WatchlistItem(ticker=...)` → `WatchlistInputItem(ticker=...)`
- `Watchlist(name=..., items=...)` → `WatchlistInput(name=..., items=...)`

**Step 5 — Update 5 test files** (import path change, same construction pattern):

**Step 6 — Delete `atlas/analysis/watchlist.py`**

**Step 7 — Clean `atlas/analysis/__init__.py`** (remove `Watchlist`, `WatchlistItem` re-exports)

**Step 8 — Export `WatchlistInput`, `WatchlistInputItem` from `atlas/capabilities/watchlist_intelligence/__init__.py`**

**Step 9 — Update all docs and guardrails**

---

## Risk Assessment

| Risk | Description | Mitigation |
|---|---|---|
| Naming collision | `WatchlistItem` exists in both legacy and capability layer (different schemas) | Rename legacy to `WatchlistInputItem` — makes distinction explicit |
| Cascading import updates | 7 production modules + 5 test files need import path changes | All are mechanical find-and-replace; no logic changes |
| `WatchlistReviewEngine` regression | `WatchlistReviewInput.watchlist: Watchlist` field rename required | Type rename only; `WatchlistReviewEngine` logic unchanged |
| `atlas/capabilities/watchlist_intelligence/` becoming a CLI concern | Capability owns a CLI input parser | Acceptable: CLI input parsing (type + JSON deserialization) is a natural capability responsibility |
| `atlas/analysis/__init__.py` becomes empty | After removing all watchlist re-exports | Audit other re-exports; keep `__init__.py` for remaining exports |

---

## Architecture Boundaries After Sprint 101

After migration is complete:

- `atlas/analysis/watchlist.py` — **DELETED**
- `atlas/capabilities/watchlist_intelligence/` — owns `WatchlistInput`, `WatchlistInputItem`, `WatchlistIntelligenceInput`, `WatchlistItem`, `WatchlistIntelligenceReport`
- `atlas/shared/entities.py` — owns canonical `Watchlist` (domain entity, unchanged)
- `atlas/domains/watchlist/__init__.py` — re-exports canonical `Watchlist` from `atlas.shared` (unchanged)
- No module imports from `atlas.analysis.watchlist`

---

## Guardrail Tests to Add in Sprint 101

- `test_watchlist_input_is_importable_from_capability` — `WatchlistInput` accessible from `atlas.capabilities.watchlist_intelligence`
- `test_atlas_analysis_watchlist_module_does_not_exist` — `atlas.analysis.watchlist` raises `ModuleNotFoundError`
- `test_no_module_imports_from_atlas_analysis_watchlist` — source scan confirms zero imports

---

## Sprint 101 Recommendation

**Target:** Move `Watchlist` and `WatchlistItem` to `atlas/capabilities/watchlist_intelligence/`
as `WatchlistInput` / `WatchlistInputItem`. Delete `atlas/analysis/watchlist.py`.

**Rationale:** All 7 production callers use the types as CLI input containers that are immediately
converted to `WatchlistIntelligenceInput`. Placing the input type in the capability layer that owns
the conversion is architecturally correct, eliminates the last import from the legacy `analysis/`
package, and allows full deletion of the file.

**Estimated scope:** 7 production files + 5 test files + `atlas/capabilities/watchlist_intelligence/models.py`
+ `atlas/capabilities/watchlist_intelligence/__init__.py` + 4 docs. No logic changes. All changes
are import path updates and type renames.

**Migration risk: LOW.** Identical behavior; only import paths and type names change.

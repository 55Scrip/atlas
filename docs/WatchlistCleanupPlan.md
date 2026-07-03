# Watchlist Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 189)  
**Updated:** 2026-07-03 (Sprint 190)  
**Status:** CLOSED — Sprint 190 confirmed Sprint 189 findings unchanged. No cleanup warranted. No further watchlist cleanup work is planned until new dead code, stale exports, provider-boundary issues, watchlist/watchlist-review boundary issues, evidence/decision/watchlist boundary issues, persistence boundary issues, or a clear replacement/migration target emerges.

---

## Executive Summary

There is **no standalone `atlas/watchlist/` package**. The watchlist surface in Atlas is distributed cleanly across two Blueprint-aligned locations:

| Location | Lines | Role |
|---|---|---|
| `atlas/capabilities/watchlist_intelligence/` | 545 | Blueprint capability — 4 modules, 13 exports |
| `atlas/adapters/watchlist.py` | 198 | JSON adapter — 2 public functions, 1 private helper |

The legacy `atlas/analysis/watchlist.py` was deleted Sprint 101 and `WatchlistEngine` was deleted Sprint 99. Both migrations are complete. No stale watchlist code remains anywhere in the codebase.

---

## Package Inventory

### `atlas/capabilities/watchlist_intelligence/`

| File | Lines | Role |
|---|---|---|
| `__init__.py` | 33 | Re-exports 13 symbols |
| `models.py` | 155 | Data models — 2 enums, 8 dataclasses |
| `engine.py` | 300 | `WatchlistIntelligenceEngine` + 9 private helpers |
| `exporter.py` | 57 | `watchlist_report_to_dict` — JSON export for Daily Brief pipeline |

**Total:** 545 lines across 4 modules.

#### Public exports (13)

| Symbol | Type | Active | Production callers |
|---|---|---|---|
| `WatchlistEvidenceLink` | dataclass | ✓ | engine.py (internal) |
| `WatchlistIntelligenceEngine` | class | ✓ | cli/main.py, conversation/engine.py, decision/decision_engine.py, intelligence/engine.py, monitoring/engine.py |
| `WatchlistIntelligenceInput` | dataclass | ✓ | cli/main.py, adapters/watchlist.py, engine.py (internal) |
| `WatchlistIntelligenceReport` | dataclass | ✓ | capabilities/discovery/, decision/decision_result.py, exporter.py |
| `WatchlistInput` | dataclass | ✓ | cli/main.py, conversation/engine.py, decision/decision_context.py, home/engine.py, intelligence/engine.py, monitoring/engine.py, watchlist_review/engine.py |
| `WatchlistInputItem` | dataclass | ✓ | watchlist_review/engine.py |
| `WatchlistItem` | dataclass | ✓ | adapters/watchlist.py, engine.py (internal) |
| `WatchlistObservation` | dataclass | ✓ | engine.py (internal) |
| `WatchlistPriority` | enum | ✓ | engine.py (internal) |
| `WatchlistQuestion` | dataclass | ✓ | engine.py (internal) |
| `WatchlistSignal` | dataclass | ✓ | engine.py (internal) |
| `WatchlistStatus` | enum | ✓ | adapters/watchlist.py, engine.py (internal) |
| `WatchlistUnknown` | dataclass | ✓ | engine.py (internal) |

All 13 exports: active, foundational, runtime-facing.

#### Private helpers in `engine.py` (9)

`_observation_for_item`, `_evidence_links`, `_signals`, `_unknowns`, `_priority`, `_detail`, `_questions_from_observation`, `_overview`, `_research_steps`, plus module-level constant `_EVIDENCE_GAP_TITLES`.

All private helpers are internal to the engine — no external callers. All active.

#### `exporter.py` — `watchlist_report_to_dict`

Not in `__init__.py` `__all__`. Imported directly by `atlas/cli/main.py:53`. Active production caller. Exported via Direct path import, not re-exported from package root — intentional design (export-only utility).

---

### `atlas/adapters/watchlist.py`

| Symbol | Type | Public | Active | Production callers |
|---|---|---|---|---|
| `watchlist_input_from_dict` | function | ✓ | ✓ | cli/main.py (lines 924, 1001), tests/ |
| `assign_knowledge_facts` | function | ✓ | ✓ | cli/main.py (line 931), tests/ |
| `_parse_item` | function | private | ✓ | internal to watchlist_input_from_dict |
| `_parse_status` | function | private | ✓ | internal to _parse_item |
| `_node_id_matches_ticker` | function | private | ✓ | internal to assign_knowledge_facts; also tested directly in test_daily_brief_demo.py |
| `_STATUS_MAP` | constant | private | ✓ | internal to _parse_status |

All symbols active. No dead helpers. `_node_id_matches_ticker` is tested directly in `test_daily_brief_demo.py` (line 582) — private but behavior-covered.

---

## Export Review

### `atlas/capabilities/watchlist_intelligence/__init__.py`

```python
__all__ = [
    "WatchlistEvidenceLink",
    "WatchlistIntelligenceEngine",
    "WatchlistIntelligenceInput",
    "WatchlistIntelligenceReport",
    "WatchlistInput",
    "WatchlistInputItem",
    "WatchlistItem",
    "WatchlistObservation",
    "WatchlistPriority",
    "WatchlistQuestion",
    "WatchlistSignal",
    "WatchlistStatus",
    "WatchlistUnknown",
]
```

**13 exports. All active. No stale exports. No exports to remove.**

`watchlist_report_to_dict` (in `exporter.py`) is deliberately excluded from `__all__` — it is a pipeline utility imported directly by `atlas/cli/main.py:53`.

---

## Two Input Model Distinction

`models.py` contains two input-level models that serve distinct roles:

| Model | Purpose | Callers |
|---|---|---|
| `WatchlistInput` | Thin ticker-only container. Parsed from `{"tickers": [...]}` JSON format. CLI-level watchlist identity carrier. | cli/main.py, conversation, decision, home, intelligence, monitoring, watchlist_review |
| `WatchlistIntelligenceInput` | Rich items container. Parsed from `{"name": ..., "items": [...]}` format. Full research state. | cli/main.py (watchlist intelligence command), adapters/watchlist.py |

These are **distinct models for distinct data shapes** — not duplicates. `WatchlistInput` is the "what tickers" container; `WatchlistIntelligenceInput` is the "full research state" container. Both are active and correct.

---

## Caller Map

### Production callers of `atlas.capabilities.watchlist_intelligence`

| Caller | Symbols used | Role |
|---|---|---|
| `atlas/cli/main.py` | `WatchlistInput`, `WatchlistIntelligenceEngine`, `WatchlistIntelligenceInput`, `watchlist_report_to_dict` | `atlas watchlist intelligence` command; `--watchlist` flag |
| `atlas/conversation/engine.py` | `WatchlistInput`, `WatchlistIntelligenceEngine`, `WatchlistItem`, `WatchlistIntelligenceInput`, `WatchlistStatus` | Conversation context |
| `atlas/decision/decision_context.py` | `WatchlistInput` | Decision context type |
| `atlas/decision/decision_engine.py` | `WatchlistIntelligenceEngine`, `WatchlistItem`, `WatchlistStatus`, `WatchlistIntelligenceInput` | Decision engine |
| `atlas/home/engine.py` | `WatchlistInput` | Home engine context |
| `atlas/intelligence/engine.py` | `WatchlistInput`, `WatchlistIntelligenceEngine`, `WatchlistItem`, `WatchlistStatus`, `WatchlistIntelligenceInput` | Intelligence engine |
| `atlas/monitoring/engine.py` | `WatchlistInput`, `WatchlistIntelligenceEngine`, `WatchlistItem`, `WatchlistStatus`, `WatchlistIntelligenceInput` | Monitoring engine |
| `atlas/watchlist_review/engine.py` | `WatchlistInput`, `WatchlistInputItem` | Watchlist review engine (downward consumer) |
| `atlas/capabilities/discovery/engine.py` | `WatchlistIntelligenceReport` | Discovery capability |
| `atlas/capabilities/discovery/models.py` | `WatchlistIntelligenceReport` | Discovery models |
| `atlas/adapters/watchlist.py` | `WatchlistIntelligenceInput`, `WatchlistItem`, `WatchlistStatus` | JSON adapter |

### Production callers of `atlas.adapters.watchlist`

| Caller | Symbols used | Role |
|---|---|---|
| `atlas/cli/main.py` | `watchlist_input_from_dict`, `assign_knowledge_facts` | `atlas watchlist intelligence` command |

### CLI commands using watchlist

| Command | Module | Behavior |
|---|---|---|
| `atlas watchlist intelligence` | `cli/main.py:899` | Runs `WatchlistIntelligenceEngine` on local JSON. Active. |
| `atlas watchlist review` | `cli/main.py` | Runs `WatchlistReviewEngine`. Active. |
| `atlas watchlist analyze` | `cli/deprecations.py:153` | RETIRED Sprint 91. Non-callable. Metadata preserved. |
| `atlas daily summary --watchlist` | `cli/main.py:411` | Optionally parses watchlist JSON. Active. |
| `atlas discovery export --watchlist` | `cli/main.py` | Optionally uses WatchlistInput. Active. |

---

## Watchlist / Watchlist Review Boundary Review

**Boundary direction is correct and clean.**

| Direction | Status |
|---|---|
| `atlas.watchlist_review` → `atlas.capabilities.watchlist_intelligence` | ✓ Correct — `watchlist_review/engine.py:7` imports `WatchlistInput`, `WatchlistInputItem` as consumer |
| `atlas.capabilities.watchlist_intelligence` → `atlas.watchlist_review` | ✓ Absent — no upward dependency |
| `atlas.adapters.watchlist` → `atlas.watchlist_review` | ✓ Absent — no upward dependency |

`WatchlistInput` and `WatchlistInputItem` live in the capability layer, and `watchlist_review` consumes them. This is correct downward data flow. Documented as acceptable in Sprint 186 audit.

---

## Evidence / Decision / Watchlist Boundary Review

| Boundary | Import direction | Status |
|---|---|---|
| `atlas.capabilities.watchlist_intelligence` → `atlas.evidence` | Not present | ✓ Clean |
| `atlas.capabilities.watchlist_intelligence` → `atlas.decision` | Not present | ✓ Clean |
| `atlas.adapters.watchlist` → `atlas.evidence` | Not present | ✓ Clean |
| `atlas.adapters.watchlist` → `atlas.decision` | Not present | ✓ Clean |
| `atlas.decision` → `atlas.capabilities.watchlist_intelligence` | Present (WatchlistInput, WatchlistIntelligenceEngine, WatchlistItem, WatchlistStatus, WatchlistIntelligenceInput) | ✓ Acceptable — decision layer consumes capability types |
| `atlas.intelligence` → `atlas.capabilities.watchlist_intelligence` | Present (same) | ✓ Acceptable — intelligence layer consumes capability types |

All boundary directions are correct: capability provides types, application/legacy engines consume them.

---

## Provider Boundary Review

**Clean. No provider coupling anywhere in the watchlist surface.**

| Location | Provider import | Network access |
|---|---|---|
| `atlas/capabilities/watchlist_intelligence/engine.py` | None | None |
| `atlas/capabilities/watchlist_intelligence/models.py` | None | None |
| `atlas/capabilities/watchlist_intelligence/exporter.py` | None | None |
| `atlas/adapters/watchlist.py` | None | None |

`WatchlistItem.company_analysis: CompanyAnalysisReport | None` is a type field — it accepts an injected `CompanyAnalysisReport` object but does not perform provider calls. The capability receives company analysis as input data; it does not fetch it.

This is the cleanest provider boundary in the watchlist surface — cleaner than `atlas/watchlist_review/engine.py` which uses `MockCompanyAnalysisProvider` as a default (classified as acceptable legacy coupling in Sprint 187).

---

## Dependency Review (`atlas/capabilities/watchlist_intelligence/`)

| Dependency | Location | Type | Acceptable |
|---|---|---|---|
| `atlas.capabilities.company_analysis` | `models.py:7` | `CompanyAnalysisReport` type field | ✓ — capability-to-capability, downward |
| `atlas.domains.knowledge` | `models.py:8` | `KnowledgeFact` type field | ✓ — canonical domain type |
| `atlas.domains.research` | `models.py:9`, `engine.py:13` | `ResearchProject`, `summarize_research` | ✓ — canonical domain type + utility |
| `atlas.shared` | `models.py:10` | `Company` type field | ✓ — immutable shared entity |

No imports from: `atlas.cli`, `atlas.providers`, `atlas.watchlist_review`, `atlas.analysis.*`, `atlas.reasoning`, `atlas.risk`, `atlas.principles`, `atlas.intelligence`, `atlas.conversation`, `atlas.dashboard`.

Dependency surface is minimal and Blueprint-aligned.

---

## Dependency Review (`atlas/adapters/watchlist.py`)

| Dependency | Location | Type | Acceptable |
|---|---|---|---|
| `atlas.capabilities.watchlist_intelligence.models` | line 38 | `WatchlistIntelligenceInput`, `WatchlistItem`, `WatchlistStatus` | ✓ — adapter consumes capability types |
| `atlas.domains.knowledge.models` | line 43 | `KnowledgeFact` | ✓ — canonical domain type |
| `atlas.domains.research.models` | line 44 | `ResearchProject`, `ResearchQuestion`, `ResearchQuestionStatus`, `ResearchStatus` | ✓ — canonical domain types |

No imports from: `atlas.cli`, `atlas.providers`, `atlas.watchlist_review`, `atlas.analysis.*`, `atlas.reasoning`. Correct adapter pattern.

---

## Stale Import Audit

Searched all watchlist-surface files for stale imports from closed cleanup tracks:

| Deleted module | Found in watchlist surface? |
|---|---|
| `atlas.reasoning` | Not found ✓ |
| `atlas.analysis.watchlist` | Not found ✓ |
| `atlas.analysis.portfolio` | Not found ✓ |
| `atlas.analysis.comparison` | Not found ✓ |
| `atlas.analysis.scoring` | Not found ✓ |
| `atlas.analysis.growth` | Not found ✓ |
| `atlas.analysis.macro` | Not found ✓ |
| `atlas.analysis.moat` | Not found ✓ |
| `atlas.analysis.quality` | Not found ✓ |
| `atlas.analysis.sentiment` | Not found ✓ |
| `atlas.analysis.technicals` | Not found ✓ |
| `atlas.analysis.valuation` | Not found ✓ |

**No stale imports found.**

Legacy `atlas/analysis/watchlist.py` itself remains deleted (confirmed Sprint 101, re-confirmed Sprint 189 guardrail test).

---

## Persistence and Data Shape Review

`WatchlistIntelligenceInput` and `WatchlistInput` are **input-only dataclasses** — they carry parsed data in-memory and are not persisted. No serialization, no JSON write, no path handling in the capability or adapter.

Persistence notes:
- `WatchlistInput.from_json_file(path)` reads a file — path is injected by callers (CLI layer). Deterministic. Read-only.
- `WatchlistInput.from_mapping(payload)` parses an in-memory dict. Deterministic.
- `watchlist_input_from_dict(data, source)` in adapter parses a dict with error reporting. Deterministic.
- `watchlist_report_to_dict(report)` in exporter serializes to a dict (no file writes). Pure.

No hard-coded paths. No file writes. Paths are always injected by CLI callers. No behavior change risk.

---

## Blueprint / Model Review

| Criterion | Assessment |
|---|---|
| Blueprint-aligned | ✓ — lives in `atlas/capabilities/watchlist_intelligence/` (correct location) |
| Duplicates watchlist_review models? | No — `watchlist_review` owns `WatchlistReviewReport` (structured review result); `watchlist_intelligence` owns `WatchlistIntelligenceReport` (intelligence status summary). Distinct outputs. |
| Duplicates decision models? | No — `WatchlistInput` is consumed by decision engine, not duplicated in it |
| Duplicates evidence models? | No |
| Owns logic that belongs elsewhere? | No — logic is correctly scoped to watchlist intelligence |
| Should remain as watchlist data/record layer? | Yes — architecture is correct |
| Migration would change behavior? | N/A — no migration recommended |

The watchlist capability is among the most architecturally correct packages in the codebase:
- Capability layer only (no legacy module)
- Adapter layer correctly bridges JSON to capability types
- No provider coupling
- No CLI coupling
- Clean domain dependencies only
- Correct boundary with watchlist_review (watchlist_review consumes capability types)

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Sprint 190? |
|---|---|---|---|---|
| `WatchlistInput` / `WatchlistInputItem` model positioning | Both are input models in `watchlist_intelligence/models.py` but primarily used by `watchlist_review` and CLI (not by the intelligence engine itself). Minor semantic mismatch — models are correctly located for stability. | Multiple active callers | None — no behavior change required, relocation would break imports | No — leave unchanged |

**Conclusion: No cleanup candidates. No dead helpers, no stale exports, no provider boundary issues, no boundary violations, no stale imports from closed tracks, no circular dependencies.**

---

## Sprint 190 Target Recommendation

**Recommended:** Close watchlist cleanup track.

**Rationale:** The audit found no cleanup warranted anywhere in the watchlist surface. The capability is architecturally exemplary — Blueprint-aligned, provider-free, no stale imports, clean dependency surface, correct boundary direction with watchlist_review. Sprint 190 should close the watchlist cleanup track and document final state.

**Pattern:**
- Sprint 189: audit-first inventory (this sprint) — no cleanup warranted
- Sprint 190: close watchlist cleanup track

---

## Reopening Conditions

This plan may be reopened if:
- A new watchlist export is added without production callers
- A stale import from a deleted module appears in watchlist surface
- A provider import is added directly to the capability layer
- `WatchlistInput`/`WatchlistInputItem` location causes meaningful confusion

---

## Sprint 189 Verification Table

| Check | Result |
|---|---|
| `atlas/watchlist/` package exists | Not present — surface is distributed across capability + adapter (expected) |
| `watchlist_intelligence` exports importable | 13/13 ✓ |
| `__all__` count | 13 ✓ |
| Adapter functions importable | 2/2 ✓ |
| Stale import from deleted reasoning | Not found ✓ |
| Stale import from deleted analysis.* | Not found ✓ |
| Provider import in capability | Not found ✓ |
| Provider import in adapter | Not found ✓ |
| CLI import in capability | Not found ✓ |
| CLI import in adapter | Not found ✓ |
| Upward dep on watchlist_review | Not found ✓ |
| `atlas/analysis/watchlist.py` remains deleted | Confirmed ✓ |
| `CompanyAnalysisProvider` absent from analysis | Confirmed ✓ |
| Compile check | Green ✓ |
| Full test suite | **1637 passed, 3 skipped** ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |
| Behavior changes | None |

---

## Sprint 190 Closure Verification Table

Sprint 190 re-ran all Sprint 189 checks. All findings unchanged.

| Check | Sprint 189 | Sprint 190 | Δ |
|---|---|---|---|
| `watchlist_intelligence` exports importable | 13/13 ✓ | 13/13 ✓ | None |
| `__all__` count | 13 ✓ | 13 ✓ | None |
| Adapter functions importable | 2/2 ✓ | 2/2 ✓ | None |
| Production callers | 11 files ✓ | 11 files ✓ | None |
| Stale import from deleted reasoning | Not found ✓ | Not found ✓ | None |
| Stale import from deleted analysis.* | Not found ✓ | Not found ✓ | None |
| Provider import in capability | Not found ✓ | Not found ✓ | None |
| Provider import in adapter | Not found ✓ | Not found ✓ | None |
| CLI import in capability | Not found ✓ | Not found ✓ | None |
| CLI import in adapter | Not found ✓ | Not found ✓ | None |
| Upward dep on watchlist_review | Not found ✓ | Not found ✓ | None |
| `atlas/analysis/watchlist.py` remains deleted | Confirmed ✓ | Confirmed ✓ | None |
| `CompanyAnalysisProvider` absent from analysis | Confirmed ✓ | Confirmed ✓ | None |
| Compile check | Green ✓ | Green ✓ | None |
| Full test suite | 1637 passed, 3 skipped ✓ | **1637 passed, 3 skipped** ✓ | None |
| RC2 verification | Green ✓ | Green ✓ | None |
| Demo | Passes, provider-free ✓ | Passes, provider-free ✓ | None |
| Behavior changes | None | None | — |

**Sprint 190 closure decision: CLOSED.** No cleanup warranted. No further work planned.

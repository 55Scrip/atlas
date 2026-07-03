# Atlas Decision Journal Cleanup Plan

**Created:** 2026-07-03 (Sprint 184)
**Updated:** 2026-07-03 (Sprint 185)
**Status:** CLOSED — Sprint 185 confirmed Sprint 184 findings unchanged. No cleanup warranted. No further work planned until new dead code, stale exports, provider-boundary issues, evidence/decision boundary issues, persistence boundary issues, or a clear replacement/migration target emerges.

---

## Package Overview

`atlas/decision_journal/` is the decision journal engine. It creates, persists, loads, and reviews decision journal entries — capturing investment reasoning and thesis context at the time of consideration. All behavior is deterministic and local-only.

| Module | Lines | Role |
|---|---|---|
| `__init__.py` | 27 | Re-exports 11 public symbols |
| `engine.py` | 578 | Full engine: dataclasses, engine class, persistence, renderers, private helpers |

**Total: 605 lines**

---

## Module Inventory

### `atlas/decision_journal/__init__.py` (27 lines)

Re-exports all public symbols from `engine.py`. No logic.

**Exports (11):** `DecisionJournalEngine`, `DecisionJournalEntry`, `DecisionJournalInput`, `DecisionJournalLesson`, `DecisionJournalReview`, `DecisionJournalStatus`, `DecisionJournalTrigger`, `DecisionType`, `render_decision_journal_entries`, `render_decision_journal_entry`, `render_decision_journal_review`

All 11 exports are in `__all__`. All 11 have active callers (see Export Review).

---

### `atlas/decision_journal/engine.py` (578 lines)

**Public enums (2):**
- `DecisionJournalStatus` — `OPEN`, `REVIEW_DUE`, `REVIEWED`, `LESSON_CAPTURED`
- `DecisionType` — `CONSIDERING`, `ENTERED`, `EXITED`, `REVIEWED`, `PASSED`

**Public dataclasses (5):**

| Dataclass | Role | Fields |
|---|---|---|
| `DecisionJournalTrigger` | Review trigger with severity | 3 |
| `DecisionJournalLesson` | Lesson captured after review | 5 |
| `DecisionJournalInput` | Input to `create_entry()` | 18 |
| `DecisionJournalEntry` | Full persisted journal record | 22 |
| `DecisionJournalReview` | Review produced by `review_entry()` | 8 |

**Public class (1):**
- `DecisionJournalEngine` — 5 public methods:
  - `create_entry(journal_input) → DecisionJournalEntry`
  - `review_entry(entry, lessons) → DecisionJournalReview`
  - `save_entry(entry, path) → DecisionJournalEntry`
  - `load_entries(path) → tuple[DecisionJournalEntry, ...]`
  - `demo_entry() → DecisionJournalEntry`

**Public render functions (3):**
- `render_decision_journal_entry(entry) → str`
- `render_decision_journal_entries(entries) → str`
- `render_decision_journal_review(review) → str`

**Private helpers (9):** All module-level, all called only from within `engine.py`:
- `_entry_with_language` — attaches `AtlasLanguageReport` to an entry
- `_confidence_with_evidence` — adjusts base confidence via `EvidenceAssessment.confidence_impact`
- `_entry_id` — builds deterministic slug from date + decision title
- `_default_review_date` — returns today + 90 days as ISO string
- `_profile_context` — renders `InvestorProfile` fields as a string
- `_review_status` — computes `DecisionJournalStatus` from lesson presence and planned review date
- `_confidence_level` — maps int score to `ConfidenceLevel` enum
- `_entry_to_mapping` / `_entry_from_mapping` — JSON serialization helpers
- `_lesson_to_mapping` / `_lesson_from_mapping` — lesson serialization helpers
- `_render_lessons` / `_render_list` — list rendering helpers

All 9 private helpers are internal. None are dead. None are imported or tested directly by external callers.

**Imports:**
- `atlas.evidence` — `EvidenceAssessment`, `EvidenceClaim`, `EvidenceInput`, `EvidenceQualityEngine`, `EvidenceSource`
- `atlas.language` — `AtlasConfidence`, `AtlasFit`, `AtlasLanguageEngine`, `AtlasLanguageReport`, `AtlasRating`, `AtlasRationale`, `AtlasThesis`, `AtlasView`, `ConfidenceLevel`
- `atlas.principles` — `PrinciplesCheck`, `PrinciplesEngine`
- `atlas.profile` — `InvestorProfile`, `InvestorProfileEngine`
- Standard library: `json`, `dataclasses`, `datetime`, `enum`, `pathlib`, `typing`

**Classification:** Active, deterministic, local-only, persistence-capable. Runtime-facing, evidence-adjacent, decision-adjacent. Not provider-coupled. Not Blueprint-aligned (legacy layer, no domain type inputs). Clean provider boundary.

---

## Export Review

All 11 `__all__` exports reviewed:

| Export | Production callers | Test callers | Active? |
|---|---|---|---|
| `DecisionJournalEngine` | CLI (`atlas journal create/list/review`), `atlas/home/engine.py` | `test_decision_journal.py` | ✓ |
| `DecisionJournalEntry` | `atlas/home/engine.py` | `test_decision_journal.py`, `test_home_engine.py` | ✓ |
| `DecisionJournalInput` | CLI (`atlas journal create`) | `test_decision_journal.py` | ✓ |
| `DecisionJournalLesson` | — | `test_decision_journal.py` (lesson capture test) | ✓ |
| `DecisionJournalReview` | — | `test_decision_journal.py` | ✓ |
| `DecisionJournalStatus` | — | `test_decision_journal.py` | ✓ |
| `DecisionJournalTrigger` | — | `test_decision_journal.py` | ✓ (returned by `review_entry`) |
| `DecisionType` | — | `test_decision_journal.py` | ✓ |
| `render_decision_journal_entry` | CLI (`atlas journal review`), `test_decision_journal.py` | multiple | ✓ |
| `render_decision_journal_entries` | CLI (`atlas journal list`) | `test_decision_journal.py` | ✓ |
| `render_decision_journal_review` | CLI (`atlas journal review`) | `test_decision_journal.py` | ✓ |

**Notes on low-external-caller exports:** `DecisionJournalLesson`, `DecisionJournalReview`, `DecisionJournalStatus`, `DecisionJournalTrigger`, `DecisionType` have no direct production callers outside the engine — but all are returned by engine methods and tested via `test_decision_journal.py`. None are zero-caller types. Not stale.

No stale exports. No exports to remove.

---

## Caller Map

### Active CLI callers

| CLI command | Symbols used | File |
|---|---|---|
| `atlas journal create` | `DecisionJournalEngine`, `render_decision_journal_entry` | `atlas/cli/main.py:502` |
| `atlas journal list` | `DecisionJournalEngine`, `render_decision_journal_entries` | `atlas/cli/main.py:521` |
| `atlas journal review` | `DecisionJournalEngine`, `render_decision_journal_entry`, `render_decision_journal_review` | `atlas/cli/main.py:539` |
| `atlas home` | `DecisionJournalEngine` (via `atlas/home/engine.py`) | `atlas/cli/main.py:311` |

All CLI callers are active. The `journal` sub-app is registered at `atlas/cli/main.py:143`.

### Active application callers

| Caller | Symbols used | Role |
|---|---|---|
| `atlas/home/engine.py` | `DecisionJournalEngine`, `DecisionJournalEntry` | Loads journal entries for home view reminders |

### Test callers

| File | Role |
|---|---|
| `tests/test_decision_journal.py` (152 lines, 9 tests) | Full engine tests: create, render entry, render list, render review, no forbidden language, persistence (save/load roundtrip), demo entry, lesson capture, review status |
| `tests/test_evidence_package_sprint149.py` | Guard: `atlas/decision_journal/engine.py` imports `EvidenceQualityEngine` from `atlas.evidence` |
| `tests/test_evidence_assess_deprecation.py` | Guard: `EvidenceAssessment.assess` not deprecated while `decision_journal` still uses it |
| `tests/test_atlas_foundation.py` | Verifies `atlas.domains.decision_journal.JournalEntry is JournalEntry` (shared entity) |
| `tests/test_domains_package_sprint177.py` | Guards: `atlas.domains.decision_journal.JournalEntry` importable; `decision_journal` included in domains `__init__` |
| `tests/test_home_engine.py` | Tests `HomeEngine` behavior including `decision_journal_reminders` output |

### Deprecation tracking references

| File | Reference |
|---|---|
| `atlas/cli/deprecations.py:79` | Documents `atlas/decision_journal` as one of the engines that deferred deletion in earlier sprints — historical context only, not a live deprecation |

### Domains boundary re-export

`atlas/domains/decision_journal/__init__.py` re-exports `JournalEntry` from `atlas.shared`. This is a thin namespacing shim that makes `atlas.domains.decision_journal.JournalEntry` importable — it does NOT import from `atlas.decision_journal`. This is intentional: the domain boundary owns the canonical shared entity, not the legacy engine types.

---

## Evidence / Decision Boundary Review

| Dependency | Where imported | Direction | Role | Assessment |
|---|---|---|---|---|
| `atlas.evidence.EvidenceQualityEngine` | `engine.py:9` | decision_journal → evidence | `assess()` called in `create_entry()` to compute evidence quality and adjust confidence | ✓ Intentional |
| `atlas.evidence.EvidenceAssessment` | `engine.py:9` | decision_journal → evidence | Return type from `assess()` | ✓ Intentional |
| `atlas.evidence.EvidenceClaim` | `engine.py:9` | decision_journal → evidence | Constructs fallback `EvidenceInput` when no input is supplied | ✓ Intentional |
| `atlas.evidence.EvidenceInput` | `engine.py:9` | decision_journal → evidence | Input type for `EvidenceQualityEngine.assess()` | ✓ Intentional |
| `atlas.evidence.EvidenceSource` | `engine.py:9` | decision_journal → evidence | Enum value for fallback `EvidenceInput` construction | ✓ Intentional |
| `atlas.language.*` | `engine.py:15` | decision_journal → language | `AtlasLanguageEngine.build_report()` called in `_entry_with_language()` to attach `AtlasLanguageReport` to entries | ✓ Intentional |
| `atlas.principles.PrinciplesCheck` | `engine.py:26` | decision_journal → principles | Return type in `DecisionJournalReview` | ✓ Intentional |
| `atlas.principles.PrinciplesEngine` | `engine.py:26` | decision_journal → principles | `check()` called in `review_entry()` | ✓ Intentional |
| `atlas.profile.InvestorProfile` | `engine.py:27` | decision_journal → profile | Field in `DecisionJournalInput`; used in `_profile_context()` | ✓ Intentional |
| `atlas.profile.InvestorProfileEngine` | `engine.py:27` | decision_journal → profile | `create_default_profile()` called in `create_entry()` | ✓ Intentional |

**No imports from:** `atlas.decision` (the domain decision layer), `atlas.domains.*`, `atlas.capabilities.*`, `atlas.adapters.*`, `atlas.providers.*`, `atlas.cli.*`, `atlas.analysis.*`, `atlas.reasoning`, `atlas.intelligence`, `atlas.conversation`, `atlas.dashboard`, `atlas.risk`, `atlas.comparison`

**Dependency direction:** `atlas.decision_journal → atlas.evidence + atlas.language + atlas.principles + atlas.profile` — all lateral dependencies within the legacy layer. No upward coupling. No circular dependencies.

**Observation on dependency footprint:** The decision journal imports 4 sibling legacy packages. This is a wide lateral footprint for a journaling layer. However, all 4 dependencies are intentional and serve active runtime behavior:
- Evidence quality adjusts the stored confidence score.
- Language engine attaches a language report to every entry.
- Principles engine validates entry content during reviews.
- Profile engine provides default investor context when none is supplied.

No migration or cleanup is warranted in Sprint 184. Any future boundary simplification would require behavior changes (removing language report generation or principles checking from the journal flow) and should be scoped as a separate behavioral sprint, not a cleanup sprint.

---

## Provider Boundary Review

| Check | Finding |
|---|---|
| `atlas.providers` imported | ✗ — not present |
| `CompanyDataProvider` referenced | ✗ — not present |
| `MockCompanyAnalysisProvider` referenced | ✗ — not present |
| `YahooFinanceProvider` referenced | ✗ — not present |
| `requests`, `urllib`, `http` imported | ✗ — not present |
| Network access in any module | ✗ — none |
| Provider-injected constructor args | ✗ — none |

`atlas/decision_journal/` does not perform provider or network access. All inputs come from caller-supplied `DecisionJournalInput` or from local legacy engine dependencies (`atlas.evidence`, `atlas.language`, `atlas.principles`, `atlas.profile`). Clean provider boundary.

---

## Stale Import Audit

No stale imports found in `atlas/decision_journal/`:

| Symbol | Status in decision_journal |
|---|---|
| `atlas.reasoning` | Not imported ✓ |
| Deleted `atlas.analysis.*` submodules | Not imported ✓ |
| `CompanyAnalysisProvider` | Not imported, not present ✓ |
| `PortfolioAnalysis`, `PortfolioSignal`, etc. | Not imported ✓ |
| `ReasoningInput`, `ReasoningReport` | Not imported ✓ |
| `render_comparison_result` | Not imported ✓ |
| `YahooCompany`, `YahooFinancials`, `YahooMarketData` | Not imported ✓ |
| `atlas.capabilities.*` | Not imported ✓ |
| `atlas.adapters.*` | Not imported ✓ |

Zero stale imports in `atlas/decision_journal/`.

---

## Persistence and Data Shape Review

`atlas/decision_journal/` owns JSON persistence behavior:

| Aspect | Detail |
|---|---|
| File format | JSON array of `DecisionJournalEntry` dicts |
| Default path | `.atlas/decision_journal.json` (injected via CLI `--journal` option) |
| Path injection | Yes — `save_entry(entry, path)` and `load_entries(path)` accept caller-supplied `pathlib.Path` |
| Hard-coded path | No — the string `.atlas/decision_journal.json` is set in CLI option defaults, not in the engine class |
| Schema | 22 fields per entry: all serialized via `_entry_to_mapping()` / `_entry_from_mapping()` |
| Tuples | Serialized as JSON lists; deserialized back to tuples |
| `language_report` field | Not serialized — `_entry_to_mapping()` omits it; `_entry_from_mapping()` re-derives it via `_entry_with_language()` on load |
| Determinism | Fully deterministic — identical inputs produce identical entries and JSON output |
| Write behavior | Upsert by `entry_id`; existing entries with the same ID are replaced; path parent dirs created automatically |
| Coverage | `test_decision_journal.py` includes a `save_entry` / `load_entries` roundtrip test with `tmp_path` |

The `language_report` not-serialized pattern is intentional: it is derived on load, not stored. This avoids schema drift in the `AtlasLanguageReport` type from breaking stored JSON. Behavior-preserving.

---

## Blueprint / Decision Journal Model Review

| Question | Finding |
|---|---|
| Blueprint-aligned? | No — legacy layer engine; depends on `atlas.evidence`, `atlas.language`, `atlas.principles`, `atlas.profile` rather than `atlas.domains.*` |
| Duplicates `atlas.domains.decision` models? | No — `atlas.domains.decision` owns `Evidence`-related decision types; `atlas.decision_journal` owns the rich journaling dataclasses |
| Duplicates `atlas.shared.JournalEntry`? | Partially overlapping concept, intentionally different scope — `JournalEntry` is a thin canonical shared entity (7 fields); `DecisionJournalEntry` is the full engine record (22 fields including evidence, language, lessons) |
| Owns logic that belongs in evidence/decision layers? | No — the evidence layer does its work; decision_journal calls it as a dependency |
| Should remain as a journaling/record layer? | Yes — distinct runtime purpose: capturing reasoning at time of consideration, supporting review cycles and lesson capture |
| Any migration would change behavior? | Yes — any Blueprint migration would require designing domain-typed inputs; do not migrate in Sprint 184 |

**Two `JournalEntry` types clarification:**
- `atlas.shared.JournalEntry` (7 fields) — minimal canonical entity shared across system boundaries, owned by `atlas.shared.entities`. Accessible via `atlas.domains.decision_journal` re-export shim. Used in foundation tests.
- `atlas.decision_journal.DecisionJournalEntry` (22 fields) — rich engine dataclass with evidence, language, lessons, monitoring plan. Used by CLI, home engine, test suite.

These serve different purposes and should not be consolidated.

---

## Cleanup Candidate Classification

No cleanup candidates found.

| Area | Classification | Action |
|---|---|---|
| All 11 `__all__` exports | Leave unchanged | All active (CLI, home engine, or test-verified) |
| `DecisionJournalLesson`, `DecisionJournalStatus`, `DecisionJournalTrigger`, `DecisionType` (no direct production callers) | Leave unchanged | Returned by engine methods; tested in `test_decision_journal.py` |
| 9 private engine helpers | Leave unchanged | All called within `engine.py`; none dead |
| Wide lateral dependency footprint (4 sibling packages) | Note only — not a cleanup candidate | All 4 dependencies are intentional and runtime-active; simplification would change behavior |
| `language_report` not serialized to JSON | Leave unchanged | Intentional design: avoids schema drift; re-derived on load |
| No provider imports | Correct | No action |
| No CLI coupling | Correct | No action |
| No stale imports from any closed track | Correct | No action |

---

## Technical Debt Summary

`atlas/decision_journal/` has no technical debt:

- 2 modules, 605 lines
- 11 `__all__` exports — all active
- 0 stale imports
- 0 provider coupling
- 0 CLI coupling (CLI imports the package; the package does not import CLI)
- 0 circular dependencies
- 0 upward dependencies
- Correct lateral dependency direction: all 4 sibling dependencies are intentional runtime calls
- JSON persistence is injected-path, fully tested, deterministic
- `language_report` not-serialized pattern is intentional and behavior-preserving
- Clean provider boundary — no network access

---

## Reopening Conditions

This track should only be reopened if:
- A new zero-caller or stale export is introduced
- A provider import is added to the package
- A stale import from a closed cleanup track is introduced
- The `atlas.cli` upward coupling prohibition is violated
- A Blueprint successor changes the input/output type contract
- A behavioral sprint to simplify the 4-dependency footprint is proposed

## Sprint 185 — Closure Verification

Sprint 185 confirmed all Sprint 184 findings unchanged:

| Check | Result |
|---|---|
| All 11 exports importable, `__all__` exact match | ✓ |
| Capability does not import `atlas.providers` | ✓ |
| Capability does not import `atlas.cli` | ✓ |
| Capability does not import `atlas.capabilities` | ✓ |
| Capability does not import `atlas.adapters` | ✓ |
| Capability does not import deleted `atlas.reasoning` | ✓ |
| Capability does not import deleted `atlas.analysis.*` submodules | ✓ |
| No stale imports from any closed cleanup track | ✓ |
| `CompanyAnalysisProvider` absent from all active code | ✓ |
| CLI callers (`atlas journal create/list/review`) remain active | ✓ |
| `atlas/home/engine.py` caller remains active | ✓ |
| Evidence/decision boundary stable | ✓ |
| Provider boundary clean — no network access | ✓ |
| Persistence: injected-path, deterministic, `language_report` not-serialized (intentional) | ✓ |
| Sprint 184 guardrails (9 tests) | 9/9 passing ✓ |
| Full test suite | 1614 passed, 3 skipped ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |

**Track status: CLOSED as of Sprint 185.**

No further `atlas/decision_journal/` cleanup work is planned until new dead code, stale exports, provider-boundary issues, evidence/decision boundary issues, persistence boundary issues, or a clear replacement/migration target emerges.

## Reopening Conditions

This track should only be reopened if:
- A new zero-caller or stale export is introduced
- A provider import is added to the package
- A stale import from a closed cleanup track is introduced
- The `atlas.cli` upward coupling prohibition is violated
- A Blueprint successor changes the input/output type contract
- A behavioral sprint to simplify the 4-dependency footprint is proposed

## Recommended Sprint 186 Target

**Audit `atlas/watchlist_review/` package** — a focused active package referenced in `atlas/cli/deprecations.py` as one where engine deletion was deferred, making it the highest-probability next target for actual cleanup candidates. Pattern: audit-first inventory (Sprint 186), then targeted action or closure (Sprint 187).

# Atlas Watchlist Review Cleanup Plan

**Created:** 2026-07-03 (Sprint 186)
**Updated:** 2026-07-03 (Sprint 187)
**Status:** CLOSED — Sprint 187 assessed the provider boundary issue and classified it as acceptable legacy coupling. No code change made. No cleanup remains warranted. No further work planned until new dead code, stale exports, provider-boundary issues, evidence/watchlist/decision boundary issues, deferred engine deletion evidence, or a clear replacement/migration target emerges.

---

## Package Overview

`atlas/watchlist_review/` is the watchlist review engine. It produces structured, deterministic `WatchlistReviewReport` objects from a `WatchlistReviewInput` — ranking watchlist items by evidence quality, applying theme/market/profile context, and rendering a human-readable review. It is a legacy-layer engine with active CLI, home, and conversation callers.

| Module | Lines | Role |
|---|---|---|
| `__init__.py` | 27 | Re-exports 11 public symbols |
| `engine.py` | 867 | Full engine: enums, dataclasses, `WatchlistReviewEngine`, public functions, private helpers |

**Total: 894 lines**

---

## Module Inventory

### `atlas/watchlist_review/__init__.py` (27 lines)

Re-exports all public symbols from `engine.py`. No logic.

**Exports (11):** `WatchlistReviewEngine`, `WatchlistReviewInput`, `WatchlistReviewItem`, `WatchlistReviewObservation`, `WatchlistReviewRating`, `WatchlistReviewReport`, `WatchlistReviewSection`, `demo_watchlist_review_input`, `render_watchlist_review`, `watchlist_review_input_from_json_file`, `watchlist_review_input_from_mapping`

All 11 exports are in `__all__`. All 11 have active callers (see Export Review).

---

### `atlas/watchlist_review/engine.py` (867 lines)

**Public enums (1):**
- `WatchlistReviewRating` — `HIGH_QUALITY`, `FOCUSED`, `BALANCED`, `NOISY`, `UNCLEAR`

**Public dataclasses (5):**

| Dataclass | Role | Fields |
|---|---|---|
| `WatchlistReviewItem` | Single reviewed watchlist item with evidence assessment | 8 |
| `WatchlistReviewObservation` | Titled observation within a section | 3 |
| `WatchlistReviewSection` | Named section with narrative and observations | 3 |
| `WatchlistReviewInput` | Input to `WatchlistReviewEngine.review()` | 7 — includes `provider: CompanyDataProvider \| None` |
| `WatchlistReviewReport` | Full review report | 9 |

**Public class (1):**
- `WatchlistReviewEngine` — one public method: `review(review_input) → WatchlistReviewReport`
- Constructor injects 10 optional sub-engines: `language_engine`, `evidence_engine`, `theme_engine`, `market_health_engine`, `market_regime_engine`, `economic_signals_engine`, `monitoring_engine`, `suitability_engine`, `profile_engine`, `principles_engine`

**Public functions (4):**
- `render_watchlist_review(report) → str`
- `demo_watchlist_review_input(provider, investor_profile) → WatchlistReviewInput`
- `watchlist_review_input_from_json_file(path, provider, investor_profile) → WatchlistReviewInput`
- `watchlist_review_input_from_mapping(payload, provider, investor_profile) → WatchlistReviewInput`

**Private helpers (20+):** All module-level, all called from within `engine.py`:
- `_render_watchlist_review_without_principles` — text renderer used internally and by `render_watchlist_review`
- `_split_supported_items` — calls `provider.get_company_analysis()` per ticker to classify supported vs. unsupported items
- `_theme_analyses`, `_review_items`, `_review_item_from_assessment`, `_evidence_for_item` — item scoring
- `_evidence_inputs_from_mapping`, `_parse_evidence_source`, `_theme_names_from_mapping` — JSON deserialization
- `_watchlist_rating`, `_confidence`, `_bottom_line` — rating and confidence calculation
- `_sections`, `_section`, `_items_section`, `_items_narrative`, `_theme_section`, `_fit_section`, `_market_section`, `_monitoring_section`, `_change_view_section`, `_suggested_questions_section` — report section builders
- `_language_report`, `_section_summaries`, `_confidence_level`, `_item_summary`, `_idea_type`, `_evidence_score`, `_default_market_snapshot` — rendering and scoring helpers

All private helpers are internal. None are dead.

**Imports:**
- `atlas.capabilities.watchlist_intelligence` — `WatchlistInput`, `WatchlistInputItem`
- `atlas.economics` — `EconomicSignalsEngine`
- `atlas.evidence` — `EvidenceAction`, `EvidenceAssessment`, `EvidenceClaim`, `EvidenceInput`, `EvidenceQualityEngine`, `EvidenceSource`, `EvidenceStrength`
- `atlas.language` — `AtlasConfidence`, `AtlasFit`, `AtlasLanguageEngine`, `AtlasLanguageReport`, `AtlasRating`, `AtlasRationale`, `AtlasThesis`, `AtlasView`, `ConfidenceLevel`
- `atlas.market` — `MarketHealthEngine`, `MarketIndicators`, `MarketRegimeEngine`, `MarketSnapshot`
- `atlas.monitoring` — `MonitoringEngine`
- `atlas.principles` — `PrinciplesCheck`, `PrinciplesEngine`
- `atlas.profile` — `InvestorProfile`, `InvestorProfileEngine`
- **`atlas.providers` — `CompanyDataProvider`, `MockCompanyAnalysisProvider`** ← provider coupling (see Provider Boundary Review)
- `atlas.suitability` — `SuitabilityEngine`, `SuitabilityInput`
- `atlas.themes` — `ThemeAnalysis`, `ThemeEngine`, `ThemeInput`
- Standard library: `json`, `dataclasses`, `enum`, `pathlib`, `typing`

**Classification:** Active, runtime-facing, watchlist-adjacent, evidence-adjacent. **Provider-coupled** — directly imports `CompanyDataProvider` and `MockCompanyAnalysisProvider` from `atlas.providers`.

---

## Export Review

All 11 `__all__` exports reviewed:

| Export | Production callers | Test callers | Active? |
|---|---|---|---|
| `WatchlistReviewEngine` | CLI (`atlas watchlist review`), `atlas/home/engine.py` | `test_watchlist_review.py` | ✓ |
| `WatchlistReviewReport` | `atlas/home/engine.py`, `atlas/conversation/engine.py` | `test_watchlist_review.py` | ✓ |
| `WatchlistReviewInput` | `atlas/home/engine.py` | `test_watchlist_review.py` | ✓ |
| `WatchlistReviewItem` | — | `test_watchlist_review.py` | ✓ (returned by engine) |
| `WatchlistReviewObservation` | — | — | ✓ (returned by engine internally) |
| `WatchlistReviewRating` | — | `test_watchlist_review.py` | ✓ (returned by engine) |
| `WatchlistReviewSection` | — | — | ✓ (returned by engine internally) |
| `render_watchlist_review` | CLI (`atlas watchlist review`) | `test_watchlist_review.py` | ✓ |
| `demo_watchlist_review_input` | CLI, `atlas/home/engine.py` | — | ✓ |
| `watchlist_review_input_from_json_file` | CLI (`atlas watchlist review --watchlist <path>`) | — | ✓ |
| `watchlist_review_input_from_mapping` | — | `test_watchlist_review.py` | ✓ |

No stale exports. No exports to remove. `WatchlistReviewObservation` and `WatchlistReviewSection` have no direct production callers but are returned as fields of `WatchlistReviewReport.sections` — not stale.

---

## Deferred Engine Deletion Review

**Location:** `atlas/cli/deprecations.py:79` — within the `atlas evidence assess` `DeprecatedCommand` entry, `removal_criteria` field.

**Exact text:**
```
"atlas.evidence engine remains on disk — still used by atlas/comparison, "
"atlas/decision_journal, and atlas/watchlist_review. Engine deletion deferred "
"until those callers are retired."
```

**What was deferred:** Deletion of the `atlas.evidence` *engine* (not the `atlas/watchlist_review` engine). The deprecated `atlas evidence assess` CLI command was retired in Sprint 86. At that time, the `atlas.evidence` package could not be deleted because `atlas/comparison`, `atlas/decision_journal`, and `atlas/watchlist_review` all import from it. The deprecation note records that atlas.evidence engine deletion was deferred, not watchlist_review engine deletion.

**Current accuracy of the note:**
- `atlas/watchlist_review/engine.py` still imports from `atlas.evidence` ✓ — note is still accurate on this point
- `atlas/decision_journal/engine.py` still imports from `atlas.evidence` ✓
- `atlas/comparison` — not audited this sprint; assumed still importing atlas.evidence

**What the note does NOT say:** The deprecation note does not say `atlas/watchlist_review/engine.py` itself should be deleted. The "engine deletion deferred" refers to `atlas.evidence`, not `atlas.watchlist_review`.

**Conclusion:** The deprecation metadata is still accurate. `atlas.evidence` cannot be deleted while `atlas/watchlist_review` (and `atlas/decision_journal`) remain active callers. No modification to the deprecation entry is needed.

---

## Caller Map

### Active CLI callers

| CLI command | Symbols used | File |
|---|---|---|
| `atlas watchlist review` | `WatchlistReviewEngine`, `demo_watchlist_review_input`, `render_watchlist_review`, `watchlist_review_input_from_json_file` | `atlas/cli/main.py:1274` |

### Active application callers

| Caller | Symbols used | Role |
|---|---|---|
| `atlas/home/engine.py` | `WatchlistReviewEngine`, `WatchlistReviewInput`, `WatchlistReviewReport`, `demo_watchlist_review_input` | Runs watchlist review for the `atlas home` dashboard view |
| `atlas/conversation/engine.py` | `WatchlistReviewReport` (return type, line 205) | `_answer_watchlist_review()` responds to watchlist review conversation prompts |

### Test callers

| File | Role |
|---|---|
| `tests/test_watchlist_review.py` (188 lines) | Full engine tests: bottom line and rating, evidence inputs, rendering, noise classification, noisy rating |
| `tests/test_architecture_boundaries.py` | Guards `atlas.watchlist_review` package boundary |
| `tests/test_evidence_assess_deprecation.py` | Guards that `EvidenceAssessment.assess` is not deprecated while `watchlist_review` still uses it |
| `tests/test_evidence_package_sprint149.py` | Guards that `watchlist_review/engine.py` imports `EvidenceQualityEngine` |
| `tests/test_watchlist_analyze_deprecation.py:180` | Guards that `WatchlistEngine` has been removed from `watchlist_review/engine.py` (Sprint 94 deletion) |
| `tests/test_conversation_engine.py:121` | Tests `ConversationEngine` answers watchlist review questions |

---

## Evidence / Decision / Watchlist Boundary Review

| Dependency | Where imported | Direction | Role | Assessment |
|---|---|---|---|---|
| `atlas.capabilities.watchlist_intelligence` | `engine.py:7` | watchlist_review → capability | `WatchlistInput`, `WatchlistInputItem` — type inputs from a Blueprint capability | ⚠ Downward (legacy → capability) — unusual but not circular |
| `atlas.economics` | `engine.py:8` | watchlist_review → sibling | `EconomicSignalsEngine` — analyzes macro context | ✓ Lateral |
| `atlas.evidence` | `engine.py:9` | watchlist_review → sibling | `EvidenceQualityEngine.assess()`, evidence types — core to item scoring | ✓ Lateral, intentional |
| `atlas.language` | `engine.py:18` | watchlist_review → sibling | `AtlasLanguageEngine.build_report()` for language report | ✓ Lateral |
| `atlas.market` | `engine.py:29` | watchlist_review → sibling | Market regime, health, indicators | ✓ Lateral |
| `atlas.monitoring` | `engine.py:35` | watchlist_review → sibling | `MonitoringEngine.snapshot_watchlist()` | ✓ Lateral |
| `atlas.principles` | `engine.py:36` | watchlist_review → sibling | `PrinciplesEngine.check()` in `review()` | ✓ Lateral |
| `atlas.profile` | `engine.py:37` | watchlist_review → sibling | Investor profile context | ✓ Lateral |
| **`atlas.providers`** | **`engine.py:38`** | **watchlist_review → providers** | **`CompanyDataProvider` (field type), `MockCompanyAnalysisProvider` (default)** | **⚠ Provider coupling — see below** |
| `atlas.suitability` | `engine.py:39` | watchlist_review → sibling | `SuitabilityEngine.assess()` | ✓ Lateral |
| `atlas.themes` | `engine.py:40` | watchlist_review → sibling | Theme analysis | ✓ Lateral |

**No imports from:** `atlas.decision`, `atlas.domains.*`, `atlas.adapters.*`, `atlas.cli.*`, `atlas.analysis.*`, `atlas.reasoning`, `atlas.intelligence`, `atlas.conversation`, `atlas.dashboard`, `atlas.risk`, `atlas.comparison`, `atlas.home`

**Dependency notes:**

1. **`atlas.capabilities.watchlist_intelligence`** — `watchlist_review` depends on a Blueprint capability (`WatchlistInput` / `WatchlistInputItem`). This is an unusual downward dependency (legacy engine → capability). However, `WatchlistInput` is the canonical watchlist input type; `watchlist_review` is a higher-level consumer. No circular dependency. This is a known layering asymmetry — `atlas/watchlist_review/` is not Blueprint-aligned, but uses capability types as its data contract for inputs.

2. **`atlas.providers`** — `CompanyDataProvider` is used as a field type in `WatchlistReviewInput` and `MockCompanyAnalysisProvider` is instantiated as the default in `review()`, `demo_watchlist_review_input()`, and `watchlist_review_input_from_mapping()`. This is a **direct provider coupling** in a non-CLI, non-adapter module. See Provider Boundary Review.

---

## Provider Boundary Review

| Check | Finding |
|---|---|
| `atlas.providers` imported | ✓ — `from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider` at `engine.py:38` |
| `CompanyDataProvider` used as field type | ✓ — `WatchlistReviewInput.provider: CompanyDataProvider \| None` |
| `MockCompanyAnalysisProvider` instantiated | ✓ — default provider in `review()`, `demo_watchlist_review_input()`, `watchlist_review_input_from_mapping()` |
| `YahooFinanceProvider` imported | ✗ — not present |
| `requests`, `urllib`, `http` imported | ✗ — not present |
| Direct network call | ✗ — `MockCompanyAnalysisProvider` is mock; callers may pass a real provider |

**Provider coupling assessment:**

`atlas/watchlist_review/` imports `atlas.providers` directly — making it the only non-adapter, non-CLI legacy engine that directly references provider types in the audit sequence so far. The coupling is intentional in the sense that `WatchlistReviewInput.provider` allows callers to inject a real provider for live watchlist data, defaulting to `MockCompanyAnalysisProvider` for deterministic behavior.

The coupling pattern is: caller may supply `provider=YahooFinanceProvider(...)` (opt-in), otherwise `MockCompanyAnalysisProvider()` is used. The demo and RC use `MockCompanyAnalysisProvider` — so all verified paths remain provider-free.

**This is a cleanup candidate for Sprint 187.** The provider coupling is not broken, but it is architecturally inconsistent with the expected boundary principle: watchlist review (a review/analysis layer) importing directly from `atlas.providers` rather than receiving provider types via injection through the adapter layer. Removing the direct import by accepting `provider: Any | None` or using a protocol type would decouple the module, but this is a behavioral-adjacent change requiring careful scoping.

**Sprint 187 should assess whether:**
- The `CompanyDataProvider` import can be replaced with a structural protocol or `Any | None` (no behavior change)
- `MockCompanyAnalysisProvider()` default can be moved to the adapter or CLI layer
- Or: classify as acceptable legacy coupling and close the track

---

## Stale Import Audit

No stale imports from closed cleanup tracks found in `atlas/watchlist_review/`:

| Symbol | Status |
|---|---|
| `atlas.reasoning` | Not imported ✓ |
| Deleted `atlas.analysis.*` submodules | Not imported ✓ |
| `CompanyAnalysisProvider` | Not imported ✓ (the `CompanyDataProvider` import from `atlas.providers` is different and active) |
| `PortfolioAnalysis`, `PortfolioSignal`, etc. | Not imported ✓ |
| `ReasoningInput`, `ReasoningReport` | Not imported ✓ |
| `render_comparison_result` | Not imported ✓ |
| `YahooCompany`, `YahooFinancials`, `YahooMarketData` | Not imported ✓ |
| `WatchlistEngine` | Correctly absent (removed Sprint 94, guardrail in `test_watchlist_analyze_deprecation.py:180`) ✓ |

Zero stale imports from closed tracks.

---

## Persistence and Data Shape Review

`atlas/watchlist_review/` does not own JSON persistence. It reads JSON via `watchlist_review_input_from_json_file()` / `watchlist_review_input_from_mapping()` but does not write. The review output (`WatchlistReviewReport`) is rendered to text and printed; it is not persisted to disk by the engine.

Input deserialization:
- Reads a watchlist JSON dict (same format as `WatchlistInput.from_mapping`)
- Parses optional `evidence`, `themes`, `ideas`, `etfs` keys
- Evidence sources normalized via `_parse_evidence_source()` with alias table
- Fully deterministic: same JSON → same report

---

## Blueprint / Watchlist Review Model Review

| Question | Finding |
|---|---|
| Blueprint-aligned? | No — legacy layer engine; depends on `atlas.providers` directly |
| Duplicates `atlas.capabilities.watchlist_intelligence`? | Partially — uses `WatchlistInput` from that capability as its input type, but `WatchlistReviewEngine` is a higher-level review orchestrator, not a duplicate |
| Duplicates decision or evidence models? | No — uses them as dependencies |
| Should remain as a review layer? | Yes — distinct runtime purpose: opinionated ranked review with market, theme, profile, suitability context |
| Any migration would change behavior? | Yes — provider decoupling is the only structural candidate; any Blueprint migration would require new input types |
| Provider coupling is the only boundary issue | ✓ |

**`atlas.capabilities.watchlist_intelligence` vs. `atlas.watchlist_review/`:**
- `atlas.capabilities.watchlist_intelligence` — Blueprint-aligned, deterministic, provider-free, no scoring, no market context
- `atlas.watchlist_review/` — legacy layer, full review with market/theme/suitability context, provider-injectable

These are not duplicates. `watchlist_review` is a higher-level consumer of `WatchlistInput` types.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Sprint 187? |
|---|---|---|---|---|
| **Provider boundary issue** — `engine.py:38` imports `CompanyDataProvider`, `MockCompanyAnalysisProvider` directly from `atlas.providers` | Direct provider import in non-adapter, non-CLI module; `WatchlistReviewInput.provider` field typed to `CompanyDataProvider`; `MockCompanyAnalysisProvider()` instantiated as default | Provider types used in 4 locations in `engine.py` | Medium — no behavior change if decoupled via protocol/Any, but requires careful type annotation review | **Yes — assess in Sprint 187** |
| All 11 `__all__` exports | All have active callers or are returned by engine methods | Multiple | None | Leave unchanged |
| `WatchlistReviewObservation`, `WatchlistReviewSection` (no direct production callers) | Returned as fields of `WatchlistReviewReport.sections` | — | None | Leave unchanged |
| All private helpers | All called within `engine.py` | — | None | Leave unchanged |
| `atlas.capabilities.watchlist_intelligence` dependency | Unusual downward direction (legacy → capability), but no circular dependency | — | Low | Note only — not a cleanup candidate |

---

## Technical Debt Summary

`atlas/watchlist_review/` has no remaining technical debt after Sprint 187:

- 2 modules, 894 lines
- 11 `__all__` exports — all active
- `atlas.providers` import — **classified as acceptable legacy coupling** (see Sprint 187 resolution)
- 0 stale imports from closed cleanup tracks
- 0 dead private helpers
- 0 circular dependencies
- Wide lateral dependency footprint (10 sibling packages) — all intentional, all runtime-active
- `WatchlistEngine` correctly absent (guardrail in test suite)
- Persistence: read-only JSON input deserialization; no write behavior

---

## Sprint 187 — Provider Boundary Resolution

**Resolution: Option D — Acceptable Legacy Coupling. No code change.**

### Provider Coupling Audit

`engine.py:38`: `from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider`

Usage sites:
- `CompanyDataProvider` — type hint in `WatchlistReviewInput.provider` field and in 3 public function signatures (`demo_watchlist_review_input`, `watchlist_review_input_from_json_file`, `watchlist_review_input_from_mapping`) and 1 private helper (`_split_supported_items`). **Type-only. Zero runtime effect.**
- `MockCompanyAnalysisProvider()` — instantiated as default in `WatchlistReviewEngine.review()` (line 131), `demo_watchlist_review_input()` (line 229), `watchlist_review_input_from_mapping()` (line 266). **Runtime construction. Required for deterministic behavior.**

### Why Decoupling Is Not Safe Without Behavior Change

**Option A (Structural Protocol):** `CompanyDataProvider` in `atlas/providers/base.py` is already a `Protocol` — it is a pure structural interface. Replacing it with a locally-defined duplicate protocol would add complexity with zero architectural gain. The import already IS a protocol import.

**Option B (Loose Type Hint):** Replacing `CompanyDataProvider` with `Any | None` is possible but degrades type safety without removing the `atlas.providers` import (which is still needed for `MockCompanyAnalysisProvider`). Incomplete decoupling.

**Option C (Move Default Outward):** `MockCompanyAnalysisProvider()` is instantiated in 3 locations in `engine.py`. Moving all three defaults to callers would require changes to:
- `atlas/cli/main.py` — already imports `MockCompanyAnalysisProvider` directly (line 100)
- `atlas/home/engine.py` — already imports `MockCompanyAnalysisProvider` directly (line 32)
- `watchlist_review_input_from_mapping()` and `watchlist_review_input_from_json_file()` — public functions that produce a fully-formed `WatchlistReviewInput` with a default provider; removing the default from these functions would break their current API contract and require callers to supply a provider even for the common case

### Why the Coupling Is Acceptable

1. **Pattern is codebase-consistent:** `atlas/cli/main.py:100` and `atlas/home/engine.py:32` both contain `from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider`. This is the established pattern across all layers that need the provider — not a unique smell in `watchlist_review/engine.py`.

2. **`CompanyDataProvider` is already a Protocol:** The import is structurally equivalent to importing a type alias. No runtime behavior is coupled; any object satisfying `get_company_analysis()` and `get_portfolio_profile()` works.

3. **`MockCompanyAnalysisProvider` default is required for determinism:** The mock is the engine's deterministic default. Removing it would require callers to always supply a provider, changing the `WatchlistReviewEngine` API from "works with no configuration" to "requires explicit provider injection."

4. **No network access:** `MockCompanyAnalysisProvider` is local and deterministic. No network calls are made by default. The opt-in provider pattern is preserved.

5. **No circular dependency:** `atlas.watchlist_review` imports `atlas.providers`; `atlas.providers` does not import `atlas.watchlist_review`.

### Decoupling Options Evaluated

| Option | Assessment |
|---|---|
| A — Local structural Protocol | `CompanyDataProvider` is already a Protocol; local duplicate adds complexity, no gain |
| B — `Any \| None` type hint | Removes type safety; `atlas.providers` import still needed for `MockCompanyAnalysisProvider` |
| C — Move defaults outward | Changes API contract of 3 public functions; breaks "works with no configuration" behavior |
| **D — Accept Legacy Coupling** | **Selected.** No behavior change, no API change, consistent with existing codebase pattern |

### Deferred Engine Deletion Verification

`atlas/cli/deprecations.py:79` note: "atlas.evidence engine remains on disk — still used by atlas/comparison, atlas/decision_journal, and atlas/watchlist_review. Engine deletion deferred until those callers are retired."

Sprint 187 confirms:
- `atlas/watchlist_review/engine.py` still imports `EvidenceQualityEngine` from `atlas.evidence` ✓
- The deferred deletion note refers to `atlas.evidence` engine, not `atlas/watchlist_review` — still accurate ✓
- Provider boundary resolution (accepting the coupling) does not change this conclusion ✓
- Deprecation metadata unchanged ✓

### Sprint 187 Verification

| Check | Result |
|---|---|
| All 11 exports importable, `__all__` exact match | ✓ |
| Provider coupling classified as acceptable legacy coupling | ✓ |
| No code change to `engine.py` | ✓ |
| `CompanyDataProvider` is a Protocol — type-only import confirmed | ✓ |
| `MockCompanyAnalysisProvider` default required for determinism | ✓ |
| Codebase-consistent pattern (`cli/main.py`, `home/engine.py` same import) | ✓ |
| No stale imports from closed cleanup tracks | ✓ |
| Deferred engine deletion note remains accurate | ✓ |
| Sprint 186 guardrail test updated (docstring reflects Sprint 187 classification) | ✓ |
| Full test suite | 1622 passed, 3 skipped ✓ |
| RC2 verification | Green ✓ |
| Demo | Passes, provider-free ✓ |

**Track status: CLOSED as of Sprint 187.**

No further `atlas/watchlist_review/` cleanup work is planned until new dead code, stale exports, new provider-boundary issues, deferred engine deletion evidence, watchlist/evidence/decision boundary issues, or a clear replacement/migration target emerges.

---

## Reopening Conditions

This track should only be reopened if:
- A new zero-caller or stale export is introduced
- A stale import from a closed cleanup track is introduced
- A new uncoupled provider import is added beyond the documented `CompanyDataProvider`/`MockCompanyAnalysisProvider` coupling
- CLI upward coupling is introduced
- `atlas.evidence` callers (`atlas/comparison`, `atlas/decision_journal`, `atlas/watchlist_review`) are retired (opening `atlas.evidence` engine deletion)

## Recommended Sprint 188 Target

**Release candidate checkpoint** — after resolving or classifying the provider boundary issue in `atlas/watchlist_review/` and closing another cleanup track, Atlas should run a release candidate checkpoint to verify all closed tracks remain stable before the next broad audit.

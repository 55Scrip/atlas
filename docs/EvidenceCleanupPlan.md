# Atlas Evidence Package Cleanup Plan

**Created:** 2026-07-02 (Sprint 149)  
**Updated:** 2026-07-02 (Sprint 150)  
**Status:** CLOSED — Sprint 150 confirmed Sprint 149 findings unchanged. No cleanup work is warranted. Package is self-contained, actively used, and stable. No further `atlas/evidence/` cleanup work is planned until new dead code, stale imports, or a Blueprint-aligned successor emerges.

---

## Background

`atlas/evidence/` is a Group C self-contained module. It provides structured evidence quality assessment for investment decision support. The CLI command `atlas evidence assess` was deprecated in Sprint 81 and the command body retired in Sprint 86. The engine itself was retained because 3 production engines depend on it.

---

## `atlas/evidence/` Package Inventory (Sprint 149 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 23 | Re-export hub |
| `engine.py` | 540 | Core engine — all logic |

### `engine.py` — Public API

| Symbol | Type | Active callers | Status |
|---|---|---|---|
| `EvidenceSource` | str Enum (15 values) | All 3 production callers | **Active — foundational** |
| `EvidenceStrength` | str Enum (7 values) | All 3 production callers | **Active — foundational** |
| `EvidenceAction` | str Enum (7 values) | `comparison`, `watchlist_review` | **Active** |
| `EvidenceClaim` | frozen dataclass | All 3 production callers | **Active** |
| `EvidenceInput` | frozen dataclass | All 3 production callers | **Active** |
| `EvidenceRationale` | frozen dataclass | engine-internal only | **Active — internal output** |
| `EvidenceAssessment` | frozen dataclass | All 3 production callers | **Active** |
| `EvidenceQualityEngine` | class | All 3 production callers | **Active — core engine** |
| `render_evidence_assessment` | function | **Test-only** (`test_evidence_engine.py:122`) | **Test-only export** — no production caller |

### `engine.py` — Private Helpers

All private helpers are internal to `EvidenceQualityEngine.assess()` and `render_evidence_assessment()`. None are exported or called externally.

| Symbol | Purpose | Status |
|---|---|---|
| `_adjust_strength` | Adjusts base strength by flags (recency, verifiability, extraordinary) | Active |
| `_action_for_evidence` | Maps strength + source → `EvidenceAction` | Active |
| `_confidence_impact` | Maps action → confidence delta (int) | Active |
| `_rationale` | Builds `EvidenceRationale` from evidence + profile | Active |
| `_additional_data_needed` | Builds missing data list | Active |
| `_atlas_response` | Builds Atlas response string | Active |
| `_rating_label` | Maps `EvidenceStrength` → rating string | Active |
| `_confidence_level` | Maps int score → `ConfidenceLevel` enum | Active |
| `_render_list` | Formats a tuple of strings as bullet list | Active |
| `SourceProfile` | Private dataclass — internal data model for source classification | Active |
| `SOURCE_PROFILES` | Dict mapping `EvidenceSource` → `SourceProfile` | Active |
| `STRENGTH_ORDER` | Ordered tuple of strengths (used by `_adjust_strength`) | Active |
| `STRONG_ENOUGH_TO_UPDATE` | Set of strengths that can trigger view update | Active |
| `REQUEST_SOURCE_SOURCES` | Sources that trigger REQUEST_SOURCE action | Active |
| `SOCIAL_OR_SCREENSHOT_SOURCES` | Low-credibility sources for response routing | Active |

**`example_assessment()`** on `EvidenceQualityEngine` — public method, called only in `test_evidence_engine.py:122` via `render_evidence_assessment`. Test-only usage; however, it is a useful deterministic fixture method, not a cleanup target.

---

## Export Review (`__init__.py`)

| Export | Active? | External production callers |
|---|---|---|
| `EvidenceSource` | ✓ | All 3 engines |
| `EvidenceStrength` | ✓ | `comparison`, `watchlist_review` |
| `EvidenceAction` | ✓ | `comparison`, `watchlist_review` |
| `EvidenceClaim` | ✓ | All 3 engines |
| `EvidenceInput` | ✓ | All 3 engines |
| `EvidenceRationale` | ✓ | Engine-internal output; returned in `EvidenceAssessment` |
| `EvidenceAssessment` | ✓ | All 3 engines |
| `EvidenceQualityEngine` | ✓ | All 3 engines |
| `render_evidence_assessment` | Partial — test-only external caller | `tests/test_evidence_engine.py` only |

**Finding:** `render_evidence_assessment` has zero production callers. The CLI command `atlas evidence assess` that previously called it was deprecated Sprint 81 and retired Sprint 86. The guardrail test `test_evidence_assess_deprecation.py:54` explicitly asserts the CLI does NOT import `render_evidence_assessment`. It is currently exported and tested for its output format, but no production code calls it.

**Classification:** Test-only export. Not a critical cleanup target — leaving it exported is low-risk; removing it would not break production behavior but would lose a useful test fixture.

---

## Production Caller Map

**Three production engine callers, exactly as expected.** No additional callers found.

### `atlas/comparison/engine.py`

| Detail | Value |
|---|---|
| Imports | `EvidenceAction`, `EvidenceAssessment`, `EvidenceClaim`, `EvidenceInput`, `EvidenceQualityEngine`, `EvidenceSource`, `EvidenceStrength` |
| Runtime role | `EvidenceQualityEngine` injected in `__init__`; `assess()` called per evidence input during comparison |
| Core to path? | Yes — evidence quality scoring is integrated into comparison output |
| Output shape dependency | Uses `EvidenceAssessment.strength`, `.action`, `.confidence_impact`; changes would affect comparison scoring |
| Risk of changing evidence behavior | **HIGH** — comparison output depends on scoring values |

### `atlas/decision_journal/engine.py`

| Detail | Value |
|---|---|
| Imports | `EvidenceAssessment`, `EvidenceClaim`, `EvidenceInput`, `EvidenceQualityEngine`, `EvidenceSource` |
| Runtime role | `EvidenceQualityEngine` injected in `__init__`; assesses journal evidence entries |
| Core to path? | Yes — evidence assessment is embedded in journal entry output |
| Output shape dependency | Uses `EvidenceAssessment.confidence_impact`, `.should_change_view`, `.atlas_response` |
| Risk of changing evidence behavior | **MEDIUM-HIGH** — confidence delta and view-change fields drive journal output |

### `atlas/watchlist_review/engine.py`

| Detail | Value |
|---|---|
| Imports | `EvidenceAction`, `EvidenceAssessment`, `EvidenceClaim`, `EvidenceInput`, `EvidenceQualityEngine`, `EvidenceSource`, `EvidenceStrength` |
| Runtime role | `EvidenceQualityEngine` injected in `__init__`; assesses per-ticker evidence during watchlist review; routes output by action/strength |
| Core to path? | Yes — evidence quality gates watchlist item scoring and review narrative |
| Output shape dependency | Reads `.action`, `.strength`, `.confidence_impact`; `EvidenceAction` and `EvidenceStrength` values are used in set-membership checks |
| Risk of changing evidence behavior | **HIGH** — watchlist review routing depends on specific enum values |

---

## Self-Contained Boundary Review

`atlas/evidence/engine.py` imports from:

| Import | Package | Classification |
|---|---|---|
| `atlas.language.AtlasLanguageEngine` | `atlas/language/` | **Expected dependency** — Group D infrastructure/support; provides language calibration and report building |
| `atlas.language.AtlasLanguageReport` | `atlas/language/` | Expected |
| `atlas.language.AtlasRating`, `AtlasView`, `AtlasFit`, `AtlasConfidence`, `AtlasRationale`, `AtlasThesis` | `atlas/language/` | Expected |
| `atlas.language.ConfidenceLevel` | `atlas/language/` | Expected |

**Zero imports from:**
- `atlas/providers/` ✓
- `atlas/cli/` ✓
- `atlas/dashboard/` ✓
- `atlas/conversation/` ✓
- `atlas/intelligence/` ✓
- `atlas/decision/` ✓ (the legacy `atlas/decision/` package)
- `atlas/analysis/engine.py` ✓

**Conclusion:** The boundary is clean. `atlas.language` is a legitimate Group D dependency. No upward dependency violations.

---

## Stale Import Audit

**Zero stale closed-track symbols found in `atlas/evidence/`.**

No references to:
- `atlas.analysis.portfolio`, `PortfolioAnalysis`, `PortfolioSignal`, `CompanyPortfolioProfile`
- `atlas.analysis.comparison`, `atlas.analysis.memory`, `atlas.analysis.scoring`, `atlas.analysis.watchlist`
- `render_comparison_result`, `YahooCompany`, `YahooFinancials`, `YahooMarketData`
- `portfolio_fit_input_from_profile`, `PortfolioIntelligenceEngine`

---

## Blueprint Overlap Review

| Domain/Capability | Overlap with `atlas/evidence/`? |
|---|---|
| `atlas/domains/decision/` | **Naming overlap only** — has its own `Evidence`, `EvidenceStrength`, `EvidenceCategory` (STRONG/MODERATE/LIMITED/MISSING). These are Blueprint-aligned evidence items with category taxonomy; completely different from `atlas/evidence/`'s source-quality assessment engine. Different purpose, different fields, different callers. No migration warranted. |
| `atlas/domains/research/` | Has `ResearchEvidenceReference` — a reference-linking type. No overlap with evidence quality assessment. |
| `atlas/capabilities/` | No evidence capability exists. |
| `atlas/reasoning/` | Has its own evidence-handling (sorts by confidence/importance) but does not import `atlas.evidence`. |

**Conclusion:** No Blueprint-aligned successor exists for `atlas/evidence/EvidenceQualityEngine`. The `atlas/domains/decision/` evidence types are a parallel concept in a different layer with a different purpose. Evidence should remain as a standalone utility module. No migration is warranted.

---

## CLI Status

`atlas evidence assess` — **RETIRED Sprint 86.** Command body removed. Entry in `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`. CLI does not import `EvidenceQualityEngine` or `render_evidence_assessment` (guardrail test confirms).

The `evidence_app = typer.Typer(...)` sub-app still exists in `atlas/cli/main.py` but has no active commands registered to it (only the retired `assess` stub existed).

---

## Cleanup Candidate Classification

| Candidate | Evidence | Callers | Risk | Sprint 150? |
|---|---|---|---|---|
| `render_evidence_assessment` in `__init__.py` | Test-only external caller (`test_evidence_engine.py`) | 0 production | LOW | Possible — but low value |
| All other exports | All have active production callers | 3 production engines | N/A | Leave unchanged |
| Engine constants (`SOURCE_PROFILES`, etc.) | All active internal use | 0 external | N/A | Leave unchanged |
| Private helpers | All active internal use | 0 external | N/A | Leave unchanged |

**No zero-caller symbols in the strictest sense** — `render_evidence_assessment` has a test caller and is tested for its output format. Removing it from `__all__` is possible but would reduce test coverage of the renderer.

**Overall assessment:** The evidence package is clean, well-structured, and in active use. No consolidation candidates, no duplicated helpers, no dead code, no stale migration residue.

---

## Final Stable Package State (Sprint 150)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 23 | Clean — 9 exports, all intentional |
| `engine.py` | 540 | Active — 1 engine class, 9 private helpers, 5 data constants |

**Provider safety:** Zero provider imports. Zero network access. Deterministic, local-only. ✓

---

## Sprint 150 — Track Closure (COMPLETED)

**Evidence cleanup track is CLOSED as of Sprint 150.**

Sprint 150 verified:
- All 9 `atlas.evidence` exports remain importable.
- 3 known production callers confirmed (`comparison`, `decision_journal`, `watchlist_review`).
- Zero upward dependencies (no imports from providers, CLI, dashboard, conversation, intelligence).
- Zero stale closed-track imports.
- No Blueprint-aligned successor introduced since Sprint 149.
- No cleanup action is warranted.

**Closure rationale:** After inventory (Sprint 149) and final verification (Sprint 150), the evidence package contains only active, intentional code. Further cleanup would create churn without architectural benefit.

**Reopening condition:** If new dead code, stale imports, a Blueprint-aligned `EvidenceQualityEngine` successor, or a zero-caller symbol emerges, this track should be reopened.

---

## Closed-Track Summary

| Track | Status |
|---|---|
| `atlas/analysis/` cleanup | CLOSED Sprint 141 |
| `atlas/decision/` cleanup | CLOSED Sprint 144 |
| Provider boundary audit | CLOSED Sprint 146 |
| Portfolio boundary | CLOSED Sprint 148 |
| Evidence package | **CLOSED Sprint 150** |

---

## Recommended Sprint 151 Target

**Audit Group C self-contained module: `atlas/reasoning/`.**

`atlas/reasoning/` has known technical debt: `atlas/principles/engine.py` holds a lazy import of `render_reasoning_report` from `atlas.reasoning` (documented Sprint 87). `RiskAnalysis` type from `atlas/risk/` is also imported by `atlas/reasoning/`. An audit sprint maps these dependencies, classifies cleanup candidates, and recommends one focused follow-on sprint. Smallest safe Group C target after evidence.

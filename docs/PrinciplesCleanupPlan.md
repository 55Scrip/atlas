# Atlas Principles Package Cleanup Plan

**Created:** 2026-07-02 (Sprint 156)  
**Updated:** 2026-07-03 (Sprint 158)  
**Status:** CLOSED — Sprint 158 confirmed Sprint 157 findings unchanged. No cleanup action is warranted. Package is self-contained, actively used via `PrinciplesEngine` and `PrinciplesCheck`, and stable. No further `atlas/principles/` cleanup work is planned until new dead code, stale exports, or a Blueprint-aligned successor emerges.

---

## Background

`atlas/principles/` is a Group C self-contained module providing deterministic communication guardrail checking. The `atlas principles check` CLI command is active. The package was last modified in Sprint 152, when `check_reasoning_report()` was removed after `atlas/reasoning/` became zero-caller.

---

## `atlas/principles/` Package Inventory (Sprint 156 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 27 | Re-export hub |
| `engine.py` | 324 | Core engine — all logic |

---

## `engine.py` — Public API

| Symbol | Kind | Active production callers | Test callers | Status |
|---|---|---|---|---|
| `PrincipleCategory` | str Enum (10 values) | 0 direct production | `test_principles_engine.py` | **Active — type system** |
| `PrinciplesResult` | str Enum (3 values) | 0 direct production | `test_principles_engine.py` | **Active — type system** |
| `AtlasPrinciple` | frozen dataclass | 0 direct production | 0 | **Active — internal type** |
| `PrincipleEvaluation` | frozen dataclass | 0 direct production | 0 | **Active — internal type** |
| `PrinciplesCheck` | frozen dataclass | **5 production engines** | `test_principles_engine.py` | **Active — shared production type** |
| `PrinciplesEngine` | class | **5 production engines + CLI** | `test_principles_engine.py` | **Active — core engine** |
| `render_principles_check` | function | **CLI (`atlas principles check`)** | `test_principles_engine.py` | **Active — CLI output** |
| `check_text_against_principles` | function | 0 production (only called internally) | `test_principles_engine.py` | **Test-only direct caller** |
| `check_conversation_response` | function | **0 production** | `test_principles_engine.py` (1 test) | **Test-only** |
| `check_intelligence_report` | function | **0** | **0** | **Zero-caller** |
| `check_suitability_assessment` | function | **0** | **0** | **Zero-caller** |

### `engine.py` — Private Helpers

All private helpers are fully internal. None have stale residue.

| Symbol | Purpose | Status |
|---|---|---|
| `_evaluate_principle` | Scores one principle against normalized text | Active — internal |
| `_guardrail_warnings` | Detects prohibited language patterns | Active — internal |
| `_missing_context` | Identifies absent context signals | Active — internal |
| `_suggested_improvements` | Builds improvement list from audit results | Active — internal |
| `_overall_result` | Maps guardrails + missing count → PASS/WARNING/FAIL | Active — internal |
| `_confidence` | Computes confidence score 0–100 | Active — internal |
| `_remove_quoted_text` | Strips quoted text before guardrail scan | Active — internal |
| `_normalize` | Lowercases and normalizes hyphens | Active — internal |
| `_contains_any` | Checks for any needle in text | Active — internal |
| `_render_evaluations` | Formats principle evaluations as bullet list | Active — internal |
| `_render_list` | Formats tuple of strings as bullet list | Active — internal |
| `PROHIBITED_LANGUAGE` | Module-level constant — prohibited phrases | Active — internal |
| `DEFAULT_PRINCIPLES` | Module-level constant — 10 Atlas principles | Active — internal |

---

## Export Review (`__init__.py`)

11 exports. Current `__init__.py` post-Sprint-152 state:

| Export | Active production callers | Status |
|---|---|---|
| `AtlasPrinciple` | 0 direct | Essential — type system |
| `PrincipleCategory` | 0 direct | Essential — type system |
| `PrincipleEvaluation` | 0 direct | Essential — type system |
| `PrinciplesCheck` | 5 production engines | Essential — shared type |
| `PrinciplesEngine` | 5 production engines + CLI | Essential — core engine |
| `PrinciplesResult` | 0 direct | Essential — type system |
| `check_conversation_response` | 0 production, 1 test | **Test-only** |
| `check_intelligence_report` | **0** | **Zero-caller** |
| `check_suitability_assessment` | **0** | **Zero-caller** |
| `check_text_against_principles` | 0 production, 1 test (direct); called internally by 3 helpers | **Test-only direct** |
| `render_principles_check` | CLI | Essential — CLI output |

---

## Active Production Caller Map

### Five production callers + CLI.

| Caller | Import | Symbols Used | Usage Pattern |
|---|---|---|---|
| `atlas/cli/main.py` | `from atlas.principles import PrinciplesEngine, render_principles_check` | `PrinciplesEngine`, `render_principles_check` | `atlas principles check` command — instantiates engine, renders output |
| `atlas/comparison/engine.py` | `from atlas.principles import PrinciplesCheck, PrinciplesEngine` | `PrinciplesCheck`, `PrinciplesEngine` | Guardrail check on rendered comparison draft |
| `atlas/dashboard/engine.py` | `from atlas.principles import PrinciplesCheck, PrinciplesEngine` | `PrinciplesCheck`, `PrinciplesEngine` | Guardrail check on dashboard text draft |
| `atlas/decision_journal/engine.py` | `from atlas.principles import PrinciplesCheck, PrinciplesEngine` | `PrinciplesCheck`, `PrinciplesEngine` | Guardrail check on decision journal entry |
| `atlas/portfolio_review/engine.py` | `from atlas.principles import PrinciplesCheck, PrinciplesEngine` | `PrinciplesCheck`, `PrinciplesEngine` | Guardrail check on portfolio review draft |
| `atlas/watchlist_review/engine.py` | `from atlas.principles import PrinciplesCheck, PrinciplesEngine` | `PrinciplesCheck`, `PrinciplesEngine` | Guardrail check on watchlist review draft |

**Pattern:** All 5 production callers use only `PrinciplesEngine` and `PrinciplesCheck`. None use the three `check_*` convenience functions or `render_principles_check` (except CLI).

---

## CLI Caller Review

### `atlas principles check`

| Detail | Value |
|---|---|
| Command | `atlas principles check <text>` |
| Implementation | `atlas/cli/main.py:796–800` |
| Imports used | `PrinciplesEngine`, `render_principles_check` |
| Runtime behavior | Instantiates `PrinciplesEngine()`, calls `.check(text)`, renders via `render_principles_check` |
| Output | Prints guardrail check result to console |
| Deprecated commands | None — `atlas principles check` is the only active principles command |

CLI behavior is unchanged.

---

## Sprint 152 Removal Verification

**`check_reasoning_report` is fully removed.** Verified Sprint 156:

- `atlas/principles/engine.py` — no `check_reasoning_report`, no `atlas.reasoning`, no `ReasoningReport` reference.
- `atlas/principles/__init__.py` — no `check_reasoning_report` in imports or `__all__`.
- Multiple guardrail tests confirm removal: `test_reason_analyze_deprecation.py`, `test_reasoning_package_sprint151.py`.

**TYPE_CHECKING import for `ReasoningReport` also removed (Sprint 152).** The `TYPE_CHECKING` block now guards only:
- `from atlas.conversation import ConversationResponse`
- `from atlas.intelligence import IntelligenceReport`
- `from atlas.suitability import SuitabilityAssessment`

These remain valid non-runtime type annotations for the three `check_*` convenience functions.

---

## Self-Contained Boundary Review

`atlas/principles/engine.py` imports:

| Import | Kind | Runtime? | Classification |
|---|---|---|---|
| `re`, `dataclasses`, `enum`, `typing` | stdlib | Yes | Expected |
| `atlas.conversation.ConversationResponse` | TYPE_CHECKING guard | No (type only) | Expected — annotation for `check_conversation_response` |
| `atlas.intelligence.IntelligenceReport` | TYPE_CHECKING guard | No (type only) | Expected — annotation for `check_intelligence_report` |
| `atlas.suitability.SuitabilityAssessment` | TYPE_CHECKING guard | No (type only) | Expected — annotation for `check_suitability_assessment` |
| `atlas.intelligence.render_intelligence_report` | Lazy import inside `check_intelligence_report()` | Only if called | Expected — but function has zero callers |
| `atlas.suitability.render_suitability_assessment` | Lazy import inside `check_suitability_assessment()` | Only if called | Expected — but function has zero callers |

**Zero imports from:**
- `atlas/providers/` ✓ — no network calls
- `atlas/cli/` ✓
- `atlas/dashboard/` ✓
- `atlas/comparison/` ✓
- `atlas/portfolio_review/` ✓
- `atlas/watchlist_review/` ✓
- `atlas/decision_journal/` ✓
- `atlas/reasoning/` ✓ (deleted Sprint 153)
- `atlas/risk/` ✓
- `atlas/domains/` ✓

**Boundary is clean.** The lazy imports in the two zero-caller functions never executed in production. Sprint 157 removed those functions and their associated TYPE_CHECKING imports (`IntelligenceReport`, `SuitabilityAssessment`). Post-Sprint-157, the only TYPE_CHECKING import remaining is `ConversationResponse` (annotation for `check_conversation_response`).

---

## Stale Import Audit

**Zero stale closed-track symbols found in `atlas/principles/`.**

Checked for:
- `atlas.reasoning`, `ReasoningEngine`, `ReasoningInput`, `ReasoningReport`, `render_reasoning_report`, `check_reasoning_report` — all absent ✓
- `atlas.analysis.portfolio`, `PortfolioAnalysis`, `PortfolioSignal` — absent ✓
- `atlas.analysis.comparison`, `atlas.analysis.memory`, `atlas.analysis.scoring`, `atlas.analysis.watchlist` — absent ✓
- `YahooCompany`, `YahooFinancials`, `YahooMarketData` — absent ✓
- `PortfolioIntelligenceEngine`, `portfolio_fit_input_from_profile` — absent ✓

---

## Blueprint Overlap Review

| Domain/Capability | Overlap with `atlas/principles/`? |
|---|---|
| `atlas/domains/` | No `atlas/domains/principles/` exists |
| `atlas/capabilities/` | No principles capability exists |
| `atlas/domains/decision/` | Provides reasoning/evidence model — not guardrail checking. No overlap. |
| `atlas/capabilities/portfolio_intelligence/` | Portfolio fit scoring — orthogonal. No overlap. |

**Conclusion:** No Blueprint-aligned successor exists. Principles is best left as a standalone Group C module. The guardrail-checking role is unique; no domain model duplicates it. No migration is warranted.

---

## Cleanup Candidate Classification (Sprint 156 state)

| Candidate | Evidence | Caller count | Risk | Sprint 157? |
|---|---|---|---|---|
| `check_intelligence_report` | Zero callers — production or test | 0 | LOW — identical pattern to `check_reasoning_report` removed Sprint 152 | **DONE — Sprint 157** |
| `check_suitability_assessment` | Zero callers — production or test | 0 | LOW — same pattern | **DONE — Sprint 157** |
| `check_conversation_response` | Test-only (1 test); zero production callers | 1 test | LOW | Leave — has test coverage |
| `check_text_against_principles` | 1 test (direct); useful public utility | 1 test (direct) | LOW | Leave unchanged |
| `PrinciplesEngine`, `PrinciplesCheck`, `render_principles_check` | 5–6 active callers | Active | N/A | Leave unchanged |
| All 4 enums/dataclasses | Type system — essential to `PrinciplesCheck` | N/A | N/A | Leave unchanged |

**Post-Sprint-157 assessment:** No remaining cleanup candidates. Package is stable. No further cleanup work is planned.

---

## Sprint 157 — Cleanup (COMPLETED)

**Removed `check_intelligence_report` and `check_suitability_assessment`** — two zero-caller convenience functions. Pattern identical to Sprint 152's removal of `check_reasoning_report`.

Sprint 157 changes:
1. Removed `check_intelligence_report` from `atlas/principles/engine.py`
2. Removed `check_suitability_assessment` from `atlas/principles/engine.py`
3. Removed lazy imports: `render_intelligence_report`, `render_suitability_assessment`
4. Removed TYPE_CHECKING imports: `IntelligenceReport`, `SuitabilityAssessment`
5. Removed both from `atlas/principles/__init__.py` imports and `__all__`
6. Updated guardrail tests — added Sprint 157 deletion guards
7. Updated docs

**Result:** Principles public API reduced from 11 to 9 exports. No production behavior changed. All 5 active production callers unaffected. CLI unchanged.

---

## Final Stable Package State (Sprint 157)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 23 | 9 exports — all active or well-tested |
| `engine.py` | ~311 | Active — `PrinciplesEngine` core; no dormant helpers |

**Provider safety:** Zero provider imports. Zero network access. Deterministic, local-only. ✓

---

## Closed-Track Summary

| Track | Status |
|---|---|
| `atlas/analysis/` cleanup | CLOSED Sprint 141 |
| `atlas/decision/` cleanup | CLOSED Sprint 144 |
| Provider boundary audit | CLOSED Sprint 146 |
| Portfolio boundary | CLOSED Sprint 148 |
| Evidence package | CLOSED Sprint 150 |
| Reasoning package | CLOSED Sprint 153 |
| Risk package | CLOSED Sprint 155 |
| **Principles package** | **CLOSED Sprint 158** |

---

## Sprint 158 — Track Closure (COMPLETED)

**Principles cleanup track is CLOSED as of Sprint 158.**

Sprint 158 verified:
- All 9 `atlas.principles` exports remain importable.
- 5 known production callers confirmed (`comparison`, `dashboard`, `decision_journal`, `portfolio_review`, `watchlist_review`).
- `atlas principles check` CLI command active and unchanged.
- `check_reasoning_report` not importable from `atlas.principles` ✓
- `check_intelligence_report` not importable from `atlas.principles` ✓
- `check_suitability_assessment` not importable from `atlas.principles` ✓
- Zero references to `atlas.reasoning`, `IntelligenceReport`, `SuitabilityAssessment`, `ReasoningReport` in principles code ✓
- Zero provider imports ✓
- Zero stale closed-track imports ✓
- No Blueprint-aligned successor introduced since Sprint 156 ✓
- No cleanup action is warranted.

**Closure rationale:** After audit (Sprint 156), two zero-caller convenience functions were removed (Sprint 157), and Sprint 158 confirmed no remaining cleanup candidates. `PrinciplesEngine` and `PrinciplesCheck` are live shared types used by 5 production engines. `render_principles_check` serves the active CLI. All remaining exports are intentional. Further cleanup would create churn without architectural benefit.

**Reopening condition:** If new dead code or stale exports emerge, if a Blueprint-aligned principles capability is introduced, or if the 5 active callers migrate to a successor type, this track should be reopened.

---

## Recommended Sprint 159 Target

**Audit `atlas/comparison/` — provider-coupled module with Blueprint overlap.**

`atlas/comparison/` is a natural next audit target:
- Contains `InvestmentComparisonEngine` — a comparison engine that evaluates multiple companies
- Has known Blueprint overlap with `atlas/capabilities/` (comparison capability may belong there)
- Provider-coupled: may import from `atlas/providers/` — boundary should be verified
- CLI command `atlas comparison compare` may be active or deprecated — status should be confirmed
- Audit-first: inventory modules, map callers, verify provider boundary, check Blueprint overlap, classify cleanup candidates, recommend one focused follow-on sprint

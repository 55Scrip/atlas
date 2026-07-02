# WatchlistEngine Migration Plan

**Created:** 2026-07-02 (Sprint 96)  
**Updated:** 2026-07-02 (Sprint 97)  
**Status:** Active — 1 caller remaining; Sprint 97 COMPLETE (`atlas/intelligence/` migrated); Sprint 98 target: `atlas/conversation/`

---

## Current State (Sprint 96)

WatchlistEngine caller count: **2**

| Caller | File | Status |
|---|---|---|
| Intelligence Engine | `atlas/intelligence/engine.py` | **Migrated — Sprint 97** |
| Conversation Engine | `atlas/conversation/engine.py` | Active — Sprint 98 target |

Retired callers (Sprints 93–95):
- `atlas/monitoring/engine.py` — Sprint 93
- `atlas/watchlist_review/engine.py` — Sprint 94
- `atlas/decision/decision_engine.py` — Sprint 95

---

## Full Import Audit (Sprint 96)

### Active runtime imports — WatchlistEngine instantiated

| Location | Classification | Notes |
|---|---|---|
| `atlas/intelligence/engine.py:5` | Active runtime import | `from atlas.analysis.watchlist import Watchlist, WatchlistAnalysis, WatchlistEngine` |
| `atlas/intelligence/engine.py:70` | Engine parameter | `watchlist_engine: WatchlistEngine \| None = None` |
| `atlas/intelligence/engine.py:78` | Engine instantiation | `self.watchlist_engine = watchlist_engine or WatchlistEngine(self.investment_engine)` |
| `atlas/intelligence/engine.py:57` | Type-only field | `IntelligenceReport.watchlist_analysis: WatchlistAnalysis \| None` |
| `atlas/intelligence/engine.py:240` | Runtime call | `_optional_watchlist_analysis(engine: WatchlistEngine, ...)` |
| `atlas/intelligence/engine.py:243` | Return type annotation | `-> WatchlistAnalysis \| None` |
| `atlas/intelligence/engine.py:269` | Signature annotation | `_confidence(..., watchlist_analysis: WatchlistAnalysis \| None, ...)` |
| `atlas/conversation/engine.py:6` | Active runtime import | `from atlas.analysis.watchlist import Watchlist, WatchlistEngine` |
| `atlas/conversation/engine.py:80` | Engine parameter | `watchlist_engine: WatchlistEngine \| None = None` |
| `atlas/conversation/engine.py:89` | Engine instantiation | `self.watchlist_engine = watchlist_engine or WatchlistEngine(self.investment_engine)` |
| `atlas/conversation/engine.py:96` | Engine parameter pass | `watchlist_engine=self.watchlist_engine` into `IntelligenceEngine(...)` |
| `atlas/conversation/engine.py:208` | Runtime call | `self.watchlist_engine.analyze(conversation_input.watchlist, provider)` |

### Watchlist type imports (retained — not engine usage)

| Location | Classification | Notes |
|---|---|---|
| `atlas/analysis/watchlist.py` | Definition | Source of truth — must not be deleted yet |
| `atlas/analysis/__init__.py` | Re-export | Exposes `WatchlistEngine`, `WatchlistAnalysis` to callers via `atlas.analysis` |
| `atlas/cli/main.py:24` | Type-only import | `from atlas.analysis.watchlist import Watchlist` — CLI input parsing only |
| `atlas/decision/decision_context.py:5` | Type-only import | `from atlas.analysis.watchlist import Watchlist` — context type annotation |
| `atlas/monitoring/engine.py:6` | Type-only import | `from atlas.analysis.watchlist import Watchlist` — input type annotation |
| `atlas/watchlist_review/engine.py:7` | Type-only import | `from atlas.analysis.watchlist import Watchlist, WatchlistItem` — input types |
| `atlas/home/engine.py:5` | Type-only import | `from atlas.analysis.watchlist import Watchlist` |

### Test references

| Location | Classification | Notes |
|---|---|---|
| `tests/test_watchlist.py` | Direct engine test | Tests `WatchlistEngine().analyze()` — must remain until engine deleted |
| `tests/test_watchlist_analyze_deprecation.py` | Guardrail tests | Manages `WATCHLIST_ENGINE_CALLERS` frozen set |
| `tests/test_conversation_engine.py:6` | Type-only import | `Watchlist, WatchlistItem` for test input construction |
| `tests/test_decision_engine.py:5` | Type-only import | `Watchlist, WatchlistItem` for test input construction |
| `tests/test_monitoring_engine.py:115` | Type-only import | `Watchlist` for test input construction |
| `tests/test_home_engine.py:6` | Type-only import | `Watchlist` for test input construction |
| `tests/test_deprecation_registry.py:124` | Historical reference | `"atlas.analysis.watchlist"` as string in module path check |

### Docs/CLI references

| Location | Classification | Notes |
|---|---|---|
| `atlas/cli/deprecations.py:167–170` | Historical/registry | String reference in retired command registry — not an import |
| `docs/LegacyConsolidationPlan.md` | Docs | Sprint history |
| `docs/ArchitectureConsolidation.md` | Docs | Sprint history |
| `docs/DecisionLog.md` | Docs | Decision rationale |
| `docs/DeprecatedCommands.md` | Docs | Command retirement status |

---

## Runtime Flow: `atlas/intelligence/engine.py`

### Entry points
- `IntelligenceEngine.analyze(intelligence_input: IntelligenceInput) -> IntelligenceReport`
- CLI path: `atlas intelligence <ticker>` (via `atlas/cli/main.py`)
- Also called by `ConversationEngine._answer_company_analysis()` and `ConversationEngine._answer_general_guidance()`

### WatchlistEngine usage
- `IntelligenceEngine.__init__` accepts `watchlist_engine: WatchlistEngine | None = None`
- Instantiates `WatchlistEngine(self.investment_engine)` if not provided
- In `analyze()`: calls `_optional_watchlist_analysis(engine=self.watchlist_engine, watchlist=context.watchlist, provider=provider)`
- `_optional_watchlist_analysis` returns `WatchlistAnalysis | None`

### Input shape passed to WatchlistEngine
- `watchlist: Watchlist | None` from `IntelligenceContext.watchlist`
- `provider: CompanyDataProvider` — **provider IS passed; WatchlistEngine uses it to score tickers**

### Output fields consumed
- `watchlist_analysis` is used **only** in:
  - `_confidence()`: `if item is not None` check → adds 3 to context bonus
  - `IntelligenceReport.watchlist_analysis: WatchlistAnalysis | None` — stored in report as passthrough
- **No rendering function** in `render_intelligence_report()` uses any `WatchlistAnalysis` fields
- The conversation engine's `_answer_company_analysis()` and `_answer_general_guidance()` do not read `report.watchlist_analysis` from `IntelligenceReport`

### Provider involvement
- `WatchlistEngine.analyze(watchlist, provider)` — provider is passed, but only used to call `investment_engine.analyze_ticker(ticker, provider)` per item
- After migration, `WatchlistIntelligenceEngine().analyze(input)` requires no provider

### Migration difficulty: LOW
- `WatchlistAnalysis` content is not rendered or surfaced in any output string
- `watchlist_analysis` field in `IntelligenceReport` is stored but not consumed by any downstream caller
- Confidence bonus is purely a `is not None` check — easily preserved with `WatchlistIntelligenceReport`
- Conversion pattern from Sprint 95 applies directly

### Migration risk: LOW
- No output text changes from removing `WatchlistAnalysis` content (it was never rendered)
- Confidence score changes by 0 as long as watchlist is non-None — bonus +3 is preserved
- Only field name changes: `watchlist_analysis` → `watchlist_intelligence` in `IntelligenceReport`

### Dependency coupling
- `ConversationEngine.__init__` passes `watchlist_engine=self.watchlist_engine` into `IntelligenceEngine(...)`. After Sprint 97 removes `watchlist_engine` from `IntelligenceEngine.__init__`, Sprint 98 must also remove this kwarg from `ConversationEngine`.

---

## Runtime Flow: `atlas/conversation/engine.py`

### Entry points
- `ConversationEngine.answer(conversation_input: ConversationInput) -> ConversationResponse`
- CLI path: `atlas conversation` (if CLI command exists)
- `_answer_watchlist_review()` is triggered when intent classifier detects "watchlist", "opportunities", or "rank" keywords

### WatchlistEngine usage — two separate uses

**Use 1 — direct watchlist review answer:**
- `ConversationEngine.__init__` accepts `watchlist_engine: WatchlistEngine | None = None`
- Instantiates `WatchlistEngine(self.investment_engine)` if not provided
- `_answer_watchlist_review()` calls `self.watchlist_engine.analyze(conversation_input.watchlist, provider)` directly
- Consumes **specific WatchlistAnalysis fields**:
  - `analysis.strongest_opportunity.ticker` — in `short_answer`
  - `analysis.name`
  - `analysis.strongest_opportunity.reasoning` — in `supporting_reasoning`
  - `analysis.cheapest_valuation.reasoning` — in `supporting_reasoning`
  - `analysis.highest_quality_company.reasoning` — in `supporting_reasoning`
  - `analysis.final_atlas_view` — in `supporting_reasoning`

**Use 2 — cascade into IntelligenceEngine:**
- `ConversationEngine.__init__` passes `watchlist_engine=self.watchlist_engine` into `IntelligenceEngine(...)`
- After Sprint 97, `IntelligenceEngine` will no longer accept `watchlist_engine`; this kwarg must be removed in Sprint 98

### Input shape passed to WatchlistEngine
- `conversation_input.watchlist: Watchlist | None`
- `provider: CompanyDataProvider` — **provider IS passed**

### Output fields consumed — semantic mapping for Sprint 98
| WatchlistAnalysis field | Used in | WatchlistIntelligenceReport equivalent |
|---|---|---|
| `analysis.name` | `short_answer` | `report.name` — **direct match** |
| `analysis.strongest_opportunity.ticker` | `short_answer` | `report.companies_needing_attention[0].ticker` if non-empty, else `report.observations[0].ticker` |
| `analysis.strongest_opportunity.reasoning` | `supporting_reasoning[0]` | `report.companies_needing_attention[0].detail` if non-empty, else `report.overview` |
| `analysis.cheapest_valuation.reasoning` | `supporting_reasoning[1]` | `report.evidence_gaps[0].detail` if non-empty, else `report.observations[0].detail` — **semantic gap** |
| `analysis.highest_quality_company.reasoning` | `supporting_reasoning[2]` | `report.observations[0].detail` if non-empty, else `report.overview` — **semantic gap** |
| `analysis.final_atlas_view` | `supporting_reasoning[3]` | `report.overview` — **direct equivalent** |

### Provider involvement
- `WatchlistEngine.analyze(watchlist, provider)` — provider is passed
- After migration, `WatchlistIntelligenceEngine().analyze(input)` requires no provider

### Migration difficulty: MEDIUM-HIGH
- `_answer_watchlist_review()` uses specific legacy fields (`strongest_opportunity`, `cheapest_valuation`, `highest_quality_company`) with no 1:1 Blueprint equivalents
- `cheapest_valuation` and `highest_quality_company` are scoring/ranking concepts not present in research-coverage-based `WatchlistIntelligenceReport`
- The semantic shift is real: legacy output is score-ranked; Blueprint output is research-gap-driven
- Output text in `short_answer` and `supporting_reasoning` will change materially
- `confidence` is hardcoded at 80 in current conversation response — can be preserved or updated

### Migration risk: MEDIUM
- User-visible output for WATCHLIST_REVIEW intent will change: from "Atlas ranks X first" to "Atlas highlights X for research attention"
- No recommendation behavior changes — both are research-framing only
- The two semantically gapped fields (`cheapest_valuation`, `highest_quality_company`) need documented substitution choices
- `watchlist_engine=self.watchlist_engine` kwarg passed to `IntelligenceEngine` will need removal (blocked on Sprint 97)

---

## Reuse of Existing Migration Pattern

The Sprint 93–95 pattern is:

```python
# Sprint 95 example (decision engine)
# Before:
self.watchlist_engine.analyze(context.watchlist, provider)  # → WatchlistAnalysis

# After:
WatchlistIntelligenceInput(
    name=context.watchlist.name,
    items=tuple(
        IntelligenceWatchlistItem(id=item.ticker.lower(), ticker=item.ticker)
        for item in context.watchlist.items
    ),
)
WatchlistIntelligenceEngine().analyze(intelligence_input)  # → WatchlistIntelligenceReport
```

**Sprint 97 (intelligence):** Pattern applies directly. `_optional_watchlist_intelligence()` replaces `_optional_watchlist_analysis()`. No output fields are consumed beyond `is not None`. Easiest migration.

**Sprint 98 (conversation — `_answer_watchlist_review`):** Pattern applies for the engine call, but the response construction must be rewritten:

```python
# Proposed Sprint 98 short_answer:
first_ticker = (
    report.companies_needing_attention[0].ticker
    if report.companies_needing_attention
    else report.observations[0].ticker
    if report.observations
    else "the watchlist"
)
short_answer = f"Atlas highlights {first_ticker} for research attention in {report.name}."

# Proposed Sprint 98 supporting_reasoning:
first_observation = report.companies_needing_attention[0] if report.companies_needing_attention else None
supporting_reasoning = (
    first_observation.detail if first_observation else report.overview,
    report.evidence_gaps[0].detail if report.evidence_gaps else report.overview,
    report.suggested_next_research_steps[0] if report.suggested_next_research_steps else report.overview,
    report.overview,
)
```

---

## Migration Order Decision

**Sprint 97 target: `atlas/intelligence/engine.py`**  
**Sprint 98 target: `atlas/conversation/engine.py`**

### Rationale for intelligence first

1. **Smaller scope.** Intelligence uses `WatchlistAnalysis` only for a confidence bonus check and a stored passthrough field. No rendering of any WatchlistAnalysis content occurs.

2. **Fewer output dependencies.** No user-visible output string in `IntelligenceReport` reads `WatchlistAnalysis` fields. The stored `watchlist_analysis` field in `IntelligenceReport` is not read by any downstream caller.

3. **Easier test coverage.** `tests/test_intelligence_engine.py` has no references to `watchlist_analysis`. No test assertion will need updating for the field content — only the field name.

4. **Closer to Sprint 95 pattern.** Same structure as `AtlasDecisionEngine` migration: remove engine param, replace `_analyze_*` helper with Blueprint intelligence call, rename field in result dataclass.

5. **Unlocks Sprint 98.** Conversation engine currently passes `watchlist_engine=self.watchlist_engine` into `IntelligenceEngine(...)`. Sprint 97 must remove this parameter, which forces Sprint 98 to also fix that kwarg. This makes Sprint 97 a prerequisite for Sprint 98 being clean.

6. **Lower behavioral risk.** Intelligence output text does not include any WatchlistAnalysis content. Behavior change is zero on user-visible output.

### Why conversation is deferred to Sprint 98

`_answer_watchlist_review()` reads `strongest_opportunity`, `cheapest_valuation`, and `highest_quality_company` — three WatchlistAnalysis fields with no 1:1 Blueprint equivalents. The `short_answer` text changes from score-ranking language ("ranks X first") to research-attention language ("highlights X for research attention"). This is a more deliberate semantic shift that warrants its own sprint for careful output design and test coverage.

---

## WatchlistEngine Deletion Criteria

WatchlistEngine (`atlas/analysis/watchlist.py`) may be deleted when ALL of the following are true:

1. **No active runtime imports of `WatchlistEngine`** — `grep "WatchlistEngine"` across `atlas/` (excluding `cli/` string references) returns zero import or instantiation hits.

2. **No active runtime imports of `WatchlistAnalysis`** — `grep "WatchlistAnalysis"` across `atlas/` returns zero hits outside `atlas/analysis/watchlist.py` itself. Type-only annotation uses in tests are acceptable if they do not survive module deletion.

3. **No CLI/runtime path calls `atlas.analysis.watchlist`** — the module is not reachable from any `atlas` CLI command or engine `analyze()` call.

4. **`WATCHLIST_ENGINE_CALLERS` frozen set is empty** — the guardrail in `test_watchlist_engine_callers_are_exactly_the_known_set` must pass with an empty tuple.

5. **`test_watchlist_engine_active_callers_remain` is removed or vacuously passes** — with zero callers in the frozen set, the assertion loop does nothing.

6. **All type-only `Watchlist` / `WatchlistItem` imports are resolved** — modules importing `Watchlist` for type annotations (`cli/main.py`, `decision/decision_context.py`, `monitoring/engine.py`, `watchlist_review/engine.py`, `home/engine.py`) must either migrate to a Blueprint domain type or retain the import from a non-deleted source. If `atlas/analysis/watchlist.py` is deleted, `Watchlist` must be re-exported from a surviving module or the callers must switch to a Blueprint equivalent.

7. **`tests/test_watchlist.py` tests are migrated or removed** — direct engine tests cannot pass if the module is deleted.

8. **Blueprint-aligned Watchlist Intelligence (`atlas/capabilities/watchlist_intelligence/`) remains unchanged.**

9. **`atlas watchlist intelligence` CLI command passes end-to-end.**

10. **Demo passes** — `scripts/run_daily_brief_demo.sh` completes without errors.

11. **Release verification passes** — `scripts/verify_release_candidate.sh` is green.

12. **All 4 docs updated** with deletion sprint record.

**Note on `Watchlist` type:** `Watchlist` is a legacy data class used as input shape for multiple engines and CLI commands. Even after `WatchlistEngine` is deleted, `Watchlist` may still be needed as a legacy input type for the conversation and watchlist_review entry points. The deletion of `WatchlistEngine` does not automatically imply deletion of `Watchlist` and `WatchlistItem`. Evaluate separately in Sprint 99+.

---

## Provider Safety

| Sprint | Provider involvement | Safety |
|---|---|---|
| Sprint 97 (intelligence) | `WatchlistEngine.analyze(watchlist, provider)` currently receives provider. After migration, `WatchlistIntelligenceEngine().analyze(input)` needs no provider. Provider is still used by other calls in `IntelligenceEngine.analyze()` (portfolio, investment report). No provider boundary change. | Safe |
| Sprint 98 (conversation) | Same — provider passed to watchlist_engine in `_answer_watchlist_review()` only. After migration, no provider passed to watchlist intelligence. Provider still used for portfolio and investment paths in same engine. No broadening. | Safe |

Both remaining callers currently pass provider to `WatchlistEngine`. After migration, neither will. This is a provider boundary **reduction**, not an expansion. Demo and release verification remain provider-free.

---

## Active Deprecated Command Status

All deprecated CLI commands have been retired as of Sprint 91. Active `_REGISTRY` is empty.

Retired commands: `atlas watchlist analyze`, `atlas evidence assess`, `atlas reason analyze`, `atlas risk size`, `atlas portfolio analyze`, `atlas portfolio review`, `atlas daily brief`.

No deprecated commands will be reintroduced by Sprint 97 or Sprint 98 migrations.

---

## Sprint 97 Implementation Plan (Intelligence Engine)

**Files to change:**
1. `atlas/intelligence/engine.py`
   - Change import: `from atlas.analysis.watchlist import Watchlist, WatchlistAnalysis, WatchlistEngine` → `from atlas.analysis.watchlist import Watchlist` + add capability imports
   - Add: `from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceEngine` and `from atlas.capabilities.watchlist_intelligence.models import WatchlistIntelligenceInput, WatchlistIntelligenceReport, WatchlistItem as IntelligenceWatchlistItem`
   - Remove `watchlist_engine: WatchlistEngine | None = None` from `IntelligenceEngine.__init__`
   - Remove `self.watchlist_engine = watchlist_engine or WatchlistEngine(self.investment_engine)`
   - Rename `_optional_watchlist_analysis()` → `_optional_watchlist_intelligence()` returning `WatchlistIntelligenceReport | None`
   - Update `_confidence()` signature: `watchlist_analysis: WatchlistAnalysis | None` → `watchlist_intelligence: WatchlistIntelligenceReport | None`
   - Rename field in `IntelligenceReport`: `watchlist_analysis: WatchlistAnalysis | None` → `watchlist_intelligence: WatchlistIntelligenceReport | None`

2. `atlas/conversation/engine.py`
   - Remove `watchlist_engine=self.watchlist_engine` from `IntelligenceEngine(...)` construction in `__init__` (parameter no longer accepted after Sprint 97)
   - `WatchlistEngine` import and `self.watchlist_engine` instantiation remain — still needed for `_answer_watchlist_review()`

3. `tests/test_watchlist_analyze_deprecation.py`
   - Remove `atlas/intelligence/engine.py` from `WATCHLIST_ENGINE_CALLERS`
   - Add `test_intelligence_engine_does_not_import_watchlist_engine` guardrail
   - Update caller count: 2 → 1
   - Update docstring

4. `tests/test_intelligence_engine.py`
   - Update any `report.watchlist_analysis` reference to `report.watchlist_intelligence` (audit shows zero references — likely no changes needed)

5. **Docs:** LegacyConsolidationPlan, ArchitectureConsolidation, DecisionLog, DeprecatedCommands

**Expected output change:** None. `IntelligenceReport.watchlist_intelligence` stores a `WatchlistIntelligenceReport` instead of `WatchlistAnalysis`, but no rendering function uses either field's content. Confidence score unchanged (+3 bonus for non-None watchlist).

---

## Sprint 98 Implementation Plan (Conversation Engine)

**Files to change:**
1. `atlas/conversation/engine.py`
   - Change import: `from atlas.analysis.watchlist import Watchlist, WatchlistEngine` → `from atlas.analysis.watchlist import Watchlist`
   - Add: `from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceEngine` + input/report models
   - Remove `watchlist_engine: WatchlistEngine | None = None` from `ConversationEngine.__init__`
   - Remove `self.watchlist_engine = watchlist_engine or WatchlistEngine(self.investment_engine)`
   - Rewrite `_answer_watchlist_review()` to use `WatchlistIntelligenceEngine().analyze(input) → WatchlistIntelligenceReport`
   - Update `engines_used` in response: `("Watchlist Engine", "Investment Engine")` → `("Watchlist Intelligence Engine",)`

2. `tests/test_watchlist_analyze_deprecation.py`
   - Remove `atlas/conversation/engine.py` from `WATCHLIST_ENGINE_CALLERS` (reduces to empty)
   - Add `test_conversation_engine_does_not_import_watchlist_engine` guardrail
   - Update caller count: 1 → 0
   - Update docstring

3. `tests/test_conversation_engine.py`
   - Update WATCHLIST_REVIEW intent test to expect new response text
   - `confidence=80` can be preserved or updated to 70 (matching monitoring pattern)

4. **Docs:** All four + evaluate WatchlistEngine deletion readiness

**Expected output change:** `_answer_watchlist_review()` response text changes:
- Before: "Atlas ranks NVDA first in My Watchlist."
- After: "Atlas highlights NVDA for research attention in My Watchlist."
- `supporting_reasoning` shifts from score fields to research observation/gap fields

**Open question for Sprint 98:** Should `confidence` in the WATCHLIST_REVIEW response stay at 80 (hardcoded legacy) or change to 70 (matching Blueprint monitoring pattern)?

---

## Architecture Boundaries — Confirmed

- `atlas/domains/` does not import from `atlas.analysis.watchlist` (no domain boundary violation)
- `atlas/capabilities/watchlist_intelligence/` does not depend on `WatchlistEngine`
- Both remaining callers are in `atlas/intelligence/` and `atlas/conversation/` — these are allowed to import from legacy modules
- Provider boundary is not broadened by either sprint

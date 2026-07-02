# Atlas Reasoning Package Cleanup Plan

**Created:** 2026-07-02 (Sprint 151)  
**Updated:** 2026-07-02 (Sprint 153)  
**Status:** CLOSED — Sprint 153 deleted `atlas/reasoning/` package. No legacy module remains. Reasoning cleanup track is complete.

---

## Background

`atlas/reasoning/` is a Group C self-contained module. It provided structured
reasoning synthesis for investment thesis analysis. The CLI command
`atlas reason analyze` was deprecated in Sprint 82 and the command body retired
in Sprint 87. The engine itself was kept on disk because `atlas/principles/engine.py`
holds a lazy import of `render_reasoning_report` inside `check_reasoning_report()`.
That function was documented as having zero external callers as of Sprint 87.

---

## `atlas/reasoning/` Package Inventory (Sprint 151 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 19 | Re-export hub |
| `engine.py` | 575 | Core engine — all logic |

### `engine.py` — Public API

| Symbol | Type | Active callers | Status |
|---|---|---|---|
| `Evidence` | frozen dataclass | Engine-internal only | **Active — internal only** |
| `SupportingFactor` | frozen dataclass | Engine-internal only | **Active — internal only** |
| `ContradictingFactor` | frozen dataclass | Engine-internal only | **Active — internal only** |
| `ReasoningInput` | frozen dataclass | Test-only | **Test-only** |
| `ReasoningReport` | frozen dataclass | TYPE_CHECKING in principles | **No runtime production caller** |
| `ReasoningEngine` | class | Test-only | **Test-only** |
| `render_reasoning_report` | function | Lazy import in `atlas/principles/engine.py` | **Indirect — zero-caller path** |

### `engine.py` — Private Helpers

All private helpers are internal to `ReasoningEngine.analyze()` and `render_reasoning_report()`.

| Symbol | Purpose | Status |
|---|---|---|
| `_collect_evidence` | Builds `Evidence` tuple from all input fields | Active — internal |
| `_bullish_factors` | Derives `SupportingFactor` from positive signals | Active — internal |
| `_bearish_factors` | Derives `ContradictingFactor` from negative signals | Active — internal |
| `_areas_of_uncertainty` | Builds uncertainty list for missing/sparse signals | Active — internal |
| `_confidence` | Computes confidence score from evidence + uncertainty | Active — internal |
| `_executive_summary` | Builds summary string | Active — internal |
| `_alternative_scenarios` | Derives scenario strings | Active — internal |
| `_thesis_invalidation` | Builds invalidation list | Active — internal |
| `_monitor_next` | Builds monitoring priority list | Active — internal |
| `_render_supporting` | Formats `SupportingFactor` for text output | Active — internal |
| `_render_contradicting` | Formats `ContradictingFactor` for text output | Active — internal |
| `_render_evidence` | Formats `Evidence` for text output | Active — internal |
| `_render_list` | Formats string tuples as bullet list | Active — internal |

---

## Export Review (`__init__.py`)

| Export | Active? | External production callers |
|---|---|---|
| `Evidence` | Partial — test-only external caller | `tests/test_reasoning_engine.py` only |
| `SupportingFactor` | Partial — test-only external caller | `tests/test_reasoning_engine.py` only |
| `ContradictingFactor` | Partial — test-only external caller | `tests/test_reasoning_engine.py` only |
| `ReasoningInput` | Partial — test-only external caller | `tests/test_reasoning_engine.py` only |
| `ReasoningReport` | Partial — TYPE_CHECKING + lazy path in principles | Zero runtime production calls |
| `ReasoningEngine` | Partial — test-only external caller | `tests/test_reasoning_engine.py` only |
| `render_reasoning_report` | Indirect — lazy import | Only reachable via `check_reasoning_report()` which has zero external callers |

**Finding:** Every export has zero active production runtime callers. The only
production-code reference is in `atlas/principles/engine.py`:
- Line 9: `TYPE_CHECKING`-only import of `ReasoningReport` — not a runtime dependency
- Line 147: lazy runtime import of `render_reasoning_report` inside `check_reasoning_report()`

`check_reasoning_report()` itself has zero external callers.

---

## Production Caller Map

### Zero runtime production callers confirmed.

The `atlas reason analyze` CLI command that previously called `ReasoningEngine.analyze()` was:
- Deprecated Sprint 82
- Command body retired Sprint 87
- Confirmed not registered: `atlas reason analyze` returns exit code != 0

**`atlas/principles/engine.py` — sole production code reference:**

| Detail | Value |
|---|---|
| File | `atlas/principles/engine.py` |
| TYPE_CHECKING import | Line 9: `from atlas.reasoning import ReasoningReport` (not a runtime dep) |
| Lazy runtime import | Line 147: `from atlas.reasoning import render_reasoning_report` |
| Location of lazy import | Inside `check_reasoning_report(report: "ReasoningReport") -> PrinciplesCheck` |
| External callers of `check_reasoning_report` | **Zero** — confirmed in Sprint 87, still zero Sprint 151 |
| Is `check_reasoning_report` exported? | Yes — `atlas/principles/__init__.py` line 10, 25 |
| Does `atlas/principles/__init__.py` import `ReasoningReport` at runtime? | No — it only imports `check_reasoning_report` (the function wrapper) |

---

## Lazy Import Review

### Location

`atlas/principles/engine.py`, line 146–149:

```python
def check_reasoning_report(report: "ReasoningReport") -> PrinciplesCheck:
    from atlas.reasoning import render_reasoning_report

    return check_text_against_principles(render_reasoning_report(report))
```

### Why the import is lazy

`atlas/reasoning/engine.py` imports from several modules:
- `atlas.analysis.engine` (`InvestmentReport`)
- `atlas.capabilities.portfolio_intelligence` (`PortfolioFitResult`)
- `atlas.economics`, `atlas.market`, `atlas.monitoring`, `atlas.risk`, `atlas.themes`

If `atlas/principles/engine.py` imported `render_reasoning_report` at module level,
importing `atlas.principles` would transitively import `atlas.analysis.engine` and
`atlas.capabilities.portfolio_intelligence`, creating a wide import chain with risk
of circular dependency. The lazy import defers this chain until `check_reasoning_report()`
is actually called — which never happens in practice.

The `TYPE_CHECKING`-only import of `ReasoningReport` on line 9 is also a guard
against this: it prevents `ReasoningReport` from being a runtime type dependency
(using a string annotation in the function signature instead).

### Is the lazy import still needed?

**No — but only because `check_reasoning_report()` can be deleted.**

If `check_reasoning_report()` is removed, both the TYPE_CHECKING import and the
lazy import disappear. That makes `atlas.principles` independent of `atlas.reasoning`.

If `check_reasoning_report()` were to remain, the lazy import would still be the
correct pattern (avoids the transitive import chain risk).

### Safe migration path (Sprint 152)

1. Remove `check_reasoning_report()` from `atlas/principles/engine.py` (lines 146–149).
2. Remove the TYPE_CHECKING import of `ReasoningReport` from line 9 (now unused).
3. Remove `check_reasoning_report` from `atlas/principles/__init__.py` (line 10, 25).
4. Update `atlas/cli/deprecations.py` removal_criteria for `atlas reason analyze`
   to note that the `check_reasoning_report()` blocker has been resolved.
5. Update `tests/test_reason_analyze_deprecation.py`:
   - `test_principles_engine_lazy_import_is_still_present` — must be inverted
     (assert that `atlas.reasoning` reference is GONE from principles).
   - `test_reasoning_engine_module_remains_on_disk` — remove (or update to document
     that engine is now a deletion candidate).

After Sprint 152, `atlas.reasoning` will have zero production code references,
making the entire package a safe deletion target for Sprint 153.

### Risk level

**LOW.** `check_reasoning_report()` has zero external callers. Removing it cannot
break any production path. The only callers are in deprecation guardrail tests
(which document it, not call it). No runtime behavior changes.

---

## Self-Contained Boundary Review

`atlas/reasoning/engine.py` imports from:

| Import | Package | Classification |
|---|---|---|
| `atlas.analysis.engine.InvestmentReport` | `atlas/analysis/` | **Legacy dependency** — `atlas/analysis/engine.py` still exists (not deleted in Sprint 141; only `portfolio.py`, `comparison.py`, `memory.py` etc. were deleted). `InvestmentReport` is the legacy company score model. |
| `atlas.capabilities.portfolio_intelligence.PortfolioFitResult` | `atlas/capabilities/portfolio_intelligence/` | **Blueprint-aligned input** — `PortfolioFitResult` is the Sprint 131 migration result; `ReasoningInput.portfolio_analysis` accepts it. |
| `atlas.economics.EconomicSignalAnalysis` | `atlas/economics/` | **Expected dependency** — Group C sibling module |
| `atlas.market.MarketHealthReport, MarketRegimeAnalysis` | `atlas/market/` | **Expected dependency** — Group B module types |
| `atlas.monitoring.MonitoringAlert` | `atlas/monitoring/` | **Expected dependency** — Group B module type |
| `atlas.risk.RiskAnalysis` | `atlas/risk/` | **Expected dependency** — Group C sibling module |
| `atlas.themes.ThemeAnalysis` | `atlas/themes/` | **Expected dependency** — Group B module type |

**Zero imports from:**
- `atlas/providers/` ✓ — no network calls
- `atlas/cli/` ✓
- `atlas/dashboard/` ✓
- `atlas/conversation/` ✓
- `atlas/intelligence/` ✓
- `atlas/decision/` (legacy) ✓
- `atlas/domains/` ✓

**Classification:** The reasoning engine imports are coherent (aggregates inputs from multiple
legacy engines), but the entire import tree is dormant — no production path triggers
`ReasoningEngine.analyze()`. The `atlas.analysis.engine.InvestmentReport` import is
a live legacy dependency (not stale — `atlas/analysis/engine.py` exists), but irrelevant
in practice since the engine is never called.

---

## Stale Import Audit

Zero stale closed-track symbols found in `atlas/reasoning/`:

No references to:
- `atlas.analysis.portfolio`, `PortfolioAnalysis`, `PortfolioSignal`, `CompanyPortfolioProfile`
- `atlas.analysis.comparison`, `atlas.analysis.memory`, `atlas.analysis.scoring`, `atlas.analysis.watchlist`
- `render_comparison_result`, `YahooCompany`, `YahooFinancials`, `YahooMarketData`
- `portfolio_fit_input_from_profile`, `PortfolioFitInput`, `PortfolioIntelligenceEngine`

---

## Blueprint Overlap Review

| Domain/Capability | Overlap with `atlas/reasoning/`? |
|---|---|
| `atlas/domains/decision/` | **Name collision** — `atlas/domains/decision/engine.py` defines its own `ReasoningEngine` (line 24) and `Evidence` class (line 39). These are Blueprint-aligned constructs: `Evidence` holds facts + category; Blueprint `ReasoningEngine.reason()` builds a `Reasoning` model from `DecisionContext`. Completely different purpose, different fields, different callers. No migration warranted. |
| `atlas/capabilities/` | No reasoning capability exists. No Blueprint wrapper planned. |
| `atlas/principles/` | Holds `check_reasoning_report()` — the only production-code reference to `atlas.reasoning`. See Lazy Import Review. |
| `atlas/analysis/` | `atlas/analysis/engine.py` (`InvestmentReport`) is imported by `atlas.reasoning`. Not a successor — a dependency. `atlas/analysis/engine.py` itself was NOT deleted in Sprint 141. |

**Naming overlap — `ReasoningEngine` and `Evidence`:**
`atlas.reasoning.ReasoningEngine` and `atlas/domains/decision/engine.py:ReasoningEngine` share a name but are completely different:
- `atlas.reasoning.ReasoningEngine.analyze(ReasoningInput) -> ReasoningReport` — legacy multi-signal synthesis
- `atlas/domains/decision/engine.py:ReasoningEngine.reason(DecisionContext) -> Reasoning` — Blueprint decision reasoning

These do not interfere. Deletion of `atlas.reasoning.ReasoningEngine` in a future sprint
will not affect the Blueprint `ReasoningEngine`.

**Conclusion:** No Blueprint-aligned successor exists for `atlas/reasoning/ReasoningEngine`.
The decision domain has its own reasoning model for a different purpose. The reasoning
package should be deleted (Sprint 153) after the blocking lazy import is removed (Sprint 152).

---

## Cleanup Candidate Classification

| Candidate | Evidence | Callers | Risk | Status |
|---|---|---|---|---|
| ~~`check_reasoning_report()` in `atlas/principles/engine.py`~~ | ~~Zero external callers~~ | ~~0~~ | ~~LOW~~ | **DONE Sprint 152** |
| ~~TYPE_CHECKING import of `ReasoningReport` in principles~~  | ~~Unused after removal~~ | ~~0~~ | ~~LOW~~ | **DONE Sprint 152** |
| ~~`check_reasoning_report` in `atlas/principles/__init__.py`~~ | ~~Exported, zero callers~~ | ~~0~~ | ~~LOW~~ | **DONE Sprint 152** |
| All `atlas.reasoning` exports | Zero production runtime callers | 0 production | LOW | **Sprint 153** |

---

## Sprint 152 — Completed

**Removed `check_reasoning_report()` from `atlas/principles/engine.py`.** (Sprint 152)

Changes made:
- `atlas/principles/engine.py` — deleted `check_reasoning_report()`, TYPE_CHECKING import of `ReasoningReport`, lazy import of `render_reasoning_report`.
- `atlas/principles/__init__.py` — removed `check_reasoning_report` import and `__all__` entry.
- `atlas/cli/deprecations.py` — updated `atlas reason analyze` removal_criteria.
- `tests/test_reason_analyze_deprecation.py` — replaced lazy-import presence test with removal confirmation tests.
- `tests/test_reasoning_package_sprint151.py` — updated Sprint 151 guardrails to Sprint 152 state.

**Result:** No production-code dependency on `atlas.reasoning` remains.

---

## Sprint 153 — Track Closure (COMPLETED)

**`atlas/reasoning/` package deleted Sprint 153.**

- `atlas/reasoning/engine.py` — deleted (575 lines)
- `atlas/reasoning/__init__.py` — deleted (19 lines)
- Zero production callers. Zero runtime behavior changes.
- `atlas reason analyze` remains retired.
- Reasoning cleanup track **CLOSED**.
- Unblocks Sprint 153: full deletion of `atlas/reasoning/` package

After Sprint 152, Sprint 153 can delete `atlas/reasoning/` entirely (engine.py + __init__.py),
removing 594 lines of dormant code.

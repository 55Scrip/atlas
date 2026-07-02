# Atlas Deprecated Commands

**Created:** 2026-07-01 (Sprint 84)  
**Updated:** 2026-07-02 (Sprint 91)  
**Status:** Active registry — all entries reflected in `atlas/cli/deprecations.py`

This document is the human-readable counterpart to the code registry at
`atlas/cli/deprecations.py`. When a command is removed, update both.

---

## Retired Commands (no longer callable)

### ~~`atlas daily brief`~~ — RETIRED Sprint 85

| Field | Value |
|---|---|
| **Status** | **Retired** (command body removed Sprint 85) |
| **Replacement** | `atlas daily summary` |
| **Legacy module** | `atlas.daily_brief` (engine deleted Sprint 77; command body retired Sprint 85) |
| **Notes** | Entry preserved in `_RETIRED_REGISTRY` for audit. Not callable. |

---

### ~~`atlas evidence assess`~~ — RETIRED Sprint 86

| Field | Value |
|---|---|
| **Status** | **Retired** (command body removed Sprint 86) |
| **Replacement** | None — being consolidated into Blueprint-aligned decision and research capabilities |
| **Legacy module** | `atlas.evidence` (`EvidenceQualityEngine`) — **engine remains on disk** |
| **Engine callers** | `atlas/comparison/`, `atlas/decision_journal/`, `atlas/watchlist_review/` — all three must be retired before engine deletion |
| **Notes** | Entry preserved in `_RETIRED_REGISTRY` for audit. Not callable. |

---

### ~~`atlas reason analyze`~~ — RETIRED Sprint 87

| Field | Value |
|---|---|
| **Status** | **Retired** (command body removed Sprint 87) |
| **Replacement** | None — being consolidated into Blueprint-aligned decision and research capabilities |
| **Legacy module** | `atlas.reasoning` (`ReasoningEngine`) — **engine remains on disk** |
| **Engine blocker** | `atlas/principles/engine.py` has a lazy import of `render_reasoning_report` inside `check_reasoning_report()`. That function has no external callers, but the import statement must be removed before engine deletion. |
| **Notes** | Entry preserved in `_RETIRED_REGISTRY` for audit. Not callable. |

---

### ~~`atlas portfolio review`~~ — RETIRED Sprint 90

| Field | Value |
|---|---|
| **Status** | **Retired** (command body removed Sprint 90) |
| **Replacement** | `atlas portfolio summary` |
| **Legacy module** | `atlas.portfolio_review` (`PortfolioReviewEngine`, `PortfolioReviewInput`) — **engine remains on disk** |
| **Engine blocker** | `atlas/home/engine.py` (`AtlasHomeEngine`) still imports and instantiates `PortfolioReviewEngine` from `atlas.portfolio_review`. Engine deletion deferred until `AtlasHomeEngine` is retired or migrated to use `atlas.domains.portfolio.review.PortfolioReviewEngine`. |
| **Notes** | Entry preserved in `_RETIRED_REGISTRY` for audit. Not callable. A Blueprint-aligned `PortfolioReviewEngine` exists separately at `atlas.domains.portfolio.review` — unaffected. |

---

### ~~`atlas portfolio analyze`~~ — RETIRED Sprint 89

| Field | Value |
|---|---|
| **Status** | **Retired** (command body removed Sprint 89) |
| **Replacement** | `atlas portfolio summary` |
| **Legacy module** | `atlas.analysis.portfolio` (`Portfolio`, `PortfolioAnalysis`, `PortfolioIntelligenceEngine`) — **engine remains on disk** |
| **Engine blockers** | `atlas.analysis.portfolio` is still imported by `atlas/intelligence`, `atlas/conversation`, `atlas/decision`, `atlas/dashboard`, `atlas/reasoning`, `atlas/home`, `atlas/suitability`, `atlas/risk_drift`, `atlas/monitoring`, and `atlas/portfolio_review`. Engine deletion deferred until all callers are retired. |
| **Notes** | Entry preserved in `_RETIRED_REGISTRY` for audit. Not callable. |

---

### ~~`atlas risk size`~~ — RETIRED Sprint 88

| Field | Value |
|---|---|
| **Status** | **Retired** (command body removed Sprint 88) |
| **Replacement** | None — being consolidated into Blueprint-aligned portfolio, decision and research capabilities |
| **Legacy module** | `atlas.risk` (`RiskEngine`, `RiskAnalysis`, `PositionSizingInput`) — **engine remains on disk** |
| **Engine blocker** | `RiskAnalysis` type still imported by `atlas/conversation/`, `atlas/intelligence/`, `atlas/reasoning/`. `RiskEngine` cohabitates with `RiskAnalysis` in the same file; engine deletion deferred pending type migration or file split. |
| **Notes** | Entry preserved in `_RETIRED_REGISTRY` for audit. Not callable. |

---

### ~~`atlas watchlist analyze`~~ — RETIRED Sprint 91

| Field | Value |
|---|---|
| **Status** | **Retired** (command body removed Sprint 91) |
| **Replacement** | `atlas watchlist intelligence` |
| **Legacy module** | `atlas.analysis.watchlist` (`WatchlistEngine`) — **engine remains on disk** |
| **Engine blockers** | `WatchlistEngine` is still imported and instantiated by `atlas/conversation` only (Sprint 97 state). Sprint 98 target: `atlas/conversation/`. See `docs/WatchlistEngineMigrationPlan.md` for deletion criteria. |
| **Notes** | Entry preserved in `_RETIRED_REGISTRY` for audit. Not callable. Sprint 91 completes the CLI deprecated command retirement plan — active `_REGISTRY` is now empty. |

---

## Active Deprecated Commands (still callable, emit deprecation message)

**Sprint 91:** All deprecated commands have been retired. The active `_REGISTRY` is now empty.
No deprecated commands remain. `atlas/cli/deprecations.py` is retained for retired-command
history and audit via `all_retired_commands()`.

---

## Completed Retirement Order

All originally deprecated commands retired as of Sprint 91:

1. ~~**`atlas daily brief`**~~ — **DONE Sprint 85** (engine deleted Sprint 77; command body retired Sprint 85)
2. ~~**`atlas evidence assess`**~~ — **DONE Sprint 86** (command body retired; engine retained pending 3 caller retirements)
3. ~~**`atlas reason analyze`**~~ — **DONE Sprint 87** (command body retired; engine retained pending `atlas/principles/engine.py` cleanup)
4. ~~**`atlas risk size`**~~ — **DONE Sprint 88** (command body retired; engine retained pending RiskAnalysis type migration)
5. ~~**`atlas portfolio analyze`**~~ — **DONE Sprint 89** (command body retired; engine retained — 10+ active callers)
6. ~~**`atlas portfolio review`**~~ — **DONE Sprint 90** (command body retired; legacy engine retained — `atlas/home/engine.py` still instantiates it)
7. ~~**`atlas watchlist analyze`**~~ — **DONE Sprint 91** (command body retired; engine retained — 5 active callers)

---

## Architecture Boundary Rules

- The deprecation registry (`atlas/cli/deprecations.py`) is **CLI-local only**
- It must not import legacy engines, providers, or domains
- Deprecated commands must not call legacy engines (they call only `deprecated_command_message()`)
- Providers remain opt-in; deprecated commands make no provider calls
- Blueprint-aligned commands (`atlas daily summary`, `atlas watchlist intelligence`, `atlas portfolio summary`) are unaffected by deprecation registry

---

## See Also

- `atlas/cli/deprecations.py` — code registry (source of truth)
- `docs/LegacyConsolidationPlan.md` — full migration history and per-sprint decisions
- `docs/ArchitectureConsolidation.md` — sprint-by-sprint architecture notes
- `docs/DecisionLog.md` — decision rationale per sprint

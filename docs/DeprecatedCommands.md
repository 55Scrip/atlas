# Atlas Deprecated Commands

**Created:** 2026-07-01 (Sprint 84)  
**Status:** Active registry — all entries reflected in `atlas/cli/deprecations.py`

This document is the human-readable counterpart to the code registry at
`atlas/cli/deprecations.py`. When a command is removed, update both.

---

## Deprecated Command Registry

### `atlas daily brief`

| Field | Value |
|---|---|
| **Status** | Deprecated (Sprint 76) |
| **Replacement** | `atlas daily summary` |
| **Legacy module** | `atlas.daily_brief` (engine **deleted** Sprint 77) |
| **Removal criteria** | Command body only — engine is already gone. Safe to remove any sprint. |

---

### `atlas watchlist analyze`

| Field | Value |
|---|---|
| **Status** | Deprecated (Sprint 78) |
| **Replacement** | `atlas watchlist intelligence` |
| **Legacy module** | `atlas.analysis.watchlist` (`WatchlistEngine`) |
| **Removal criteria** | `WatchlistEngine` is still imported by `atlas/home`, `atlas/monitoring`, `atlas/decision`, `atlas/watchlist_review`, `atlas/conversation`, `atlas/intelligence`. All those modules must be retired before engine deletion. |

---

### `atlas portfolio analyze`

| Field | Value |
|---|---|
| **Status** | Deprecated (Sprint 79) |
| **Replacement** | `atlas portfolio summary` |
| **Legacy module** | `atlas.analysis.portfolio` (`PortfolioIntelligenceEngine`) |
| **Removal criteria** | Confirm `PortfolioIntelligenceEngine` has no non-deprecated callers, then delete. |

---

### `atlas portfolio review`

| Field | Value |
|---|---|
| **Status** | Deprecated (Sprint 80) |
| **Replacement** | `atlas portfolio summary` |
| **Legacy module** | `atlas.portfolio_review` (`PortfolioReviewEngine`) |
| **Removal criteria** | Confirm `PortfolioReviewEngine` has no non-deprecated callers, then delete. |

---

### `atlas evidence assess`

| Field | Value |
|---|---|
| **Status** | Deprecated (Sprint 81) |
| **Replacement** | None — being consolidated into Blueprint-aligned decision and research capabilities |
| **Legacy module** | `atlas.evidence` (`EvidenceQualityEngine`) |
| **Removal criteria** | Confirm `EvidenceQualityEngine` has no non-deprecated callers, then delete engine and command body. |

---

### `atlas reason analyze`

| Field | Value |
|---|---|
| **Status** | Deprecated (Sprint 82) |
| **Replacement** | None — being consolidated into Blueprint-aligned decision and research capabilities |
| **Legacy module** | `atlas.reasoning` (`ReasoningEngine`) |
| **Removal criteria** | `ReasoningEngine` lazy import in `atlas/principles/engine.py` must be removed first. Then confirm no remaining non-deprecated callers before deletion. |

---

### `atlas risk size`

| Field | Value |
|---|---|
| **Status** | Deprecated (Sprint 83) |
| **Replacement** | None — being consolidated into Blueprint-aligned portfolio, decision and research capabilities |
| **Legacy module** | `atlas.risk` (`RiskEngine`, `PositionSizingInput`) |
| **Removal criteria** | `RiskAnalysis` type is still imported by `atlas/intelligence`, `atlas/reasoning`, `atlas/conversation`. Confirm `RiskEngine` itself has no callers. `RiskAnalysis` type may need to remain. |

---

## Recommended Retirement Order

Based on isolation analysis:

1. **`atlas daily brief`** command body — safest first (engine already deleted Sprint 77)
2. **`atlas evidence assess`** command body + `atlas.evidence` engine — self-contained, no known dependents
3. **`atlas risk size`** command body — engine has no direct callers, but `RiskAnalysis` type dependency must be confirmed
4. **`atlas reason analyze`** command body — requires retiring `atlas/principles/engine.py` lazy import first
5. **`atlas portfolio analyze`** + **`atlas portfolio review`** command bodies — share `atlas.analysis.portfolio` consumers, retire together
6. **`atlas watchlist analyze`** command body — most coupled; six other engines import `WatchlistEngine`

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

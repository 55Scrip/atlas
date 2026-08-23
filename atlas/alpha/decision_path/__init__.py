"""Decision Path & Required Progress (Atlas Decision Layer, Sprint 3).
Alpha-only, no Core change.

**Deliverable 1 (Decision Path Audit) -- every one of the 13
`DecisionBlockerKind` members (Sprint 11), classified by which of
Deliverable 4's own six `RequiredProgressKind` categories it belongs
to, and whether a real, already-existing pathway to resolve it exists
in this codebase today (`ReachabilityStatus`)**:

- `NEVER_EVALUATED` / `MONITORING_PENDING` / `MONITORING_FAILED` /
  `OPERATIONAL_FRESHNESS_OUTDATED` -- **Operational, Reachable**. A
  real `POST /monitoring/run` (or a fresh ingestion) is always
  attemptable; nothing about this codebase's own machinery prevents
  it.
- `NO_DATA_SOURCE` -- **Operational, NOT Reachable**. This Alpha has
  no external data connector at all -- a freshly imported holding
  genuinely has no data source, and no mechanism in this codebase
  today can supply one. This is also the one blocker whose absence
  gates *everything else*: while it persists, Coverage cannot expand,
  Evidence cannot be recorded, Monitoring has nothing new to check --
  `engine.py`'s own `_effective_reachability` downgrades every other
  present step to `BLOCKED` while this one is present, a real,
  disclosed dependency rather than a judgment call.
- `CONFLICTING_EVIDENCE` / `INSUFFICIENT_EVIDENCE` / `MISSING_OBSERVATION`
  / `MISSING_THESIS_EVIDENCE` -- **Evidence, Reachable**. The Core
  Observation/Evidence recording pathway already exists and is real;
  these blockers name real gaps in *using* it, not a missing
  capability.
- `UNKNOWN_VALUATION` -- **Evidence, Reachable**. Atlas Intelligence
  Sprint 12's own audit already narrowed this blocker to exactly the
  genuine-data-shortfall `ValuationSupportGapKind` members (more
  historical FCF-yield observations would resolve it); the two
  "conclusive but mixed" gap kinds that Sprint 12 found were never
  genuine gaps are already excluded from ever raising this blocker at
  all (`decision_readiness.engine`'s own fix). This package does not
  re-litigate that fix.
- `COVERAGE_INCOMPLETE` -- **Coverage, Reachable**. More ingested
  `BusinessRecord`s is a real, already-existing pathway.
- `CRITICAL_DEPENDENCY_UNRESOLVED` -- **Dependency, conditionally
  Reachable**. Resolving it means recording supporting evidence for
  the specific node many conclusions depend on -- real and reachable,
  *unless* that node is itself a business-quality category or
  valuation method Atlas Intelligence Sprint 12 already found is
  permanently `INSUFFICIENT_INPUT` by architectural design (no
  semantic/NLP parsing; no fabricated scenario assumptions). That one
  case is this package's own honest "permanent dependency gap" --
  **NOT Reachable** (`engine.py`'s own `_critical_dependency
  _is_permanently_locked`).
- `AVOID_DECISION_SIGNAL` -- **Decision, Reachable**. A real Stance red
  flag; it resolves only once the underlying evidence that produced it
  changes through the same real Evidence-recording channels above --
  Atlas never overrides it directly.

**`RequiredProgressKind.READINESS`** has no `DecisionBlockerKind` of
its own -- `DecisionReadinessStatus.ALMOST_READY`'s own documented
meaning ("the same real conclusion exists, but confidence is not yet
established") already names the one real, missing positive fact
(`DecisionReadinessReasonKind.CONFIDENCE_ESTABLISHED`); this package
surfaces its *absence* using the same reused vocabulary, never a new
one.

**Monitoring** is folded in entirely via Decision Readiness's own
blockers (`MONITORING_FAILED`/`MONITORING_PENDING`/
`OPERATIONAL_FRESHNESS_OUTDATED`) -- this package never calls
`MonitoringService` itself, the same "never duplicate Monitoring"
discipline every prior Decision Layer sprint already established.
**Decision Support** anchors the action this path is about
(`InvestmentDecisionService`, unmodified); **Recommendation
Conviction** supplies the strength this path is about
(`RecommendationConvictionService`, unmodified); neither is re-derived.

Re-exports: `RequiredProgressKind`, `ReachabilityStatus`,
`DependencySource`, `DependencyReference`, `DecisionStep`,
`FinalReachableState`, `DecisionPath`, `DecisionPathSummary`,
`DecisionPathComparison`, `DecisionPathChange`,
`PortfolioDecisionPathBreakdown`, `DecisionPathService`.
"""
from __future__ import annotations

from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionPathChange,
    DecisionPathComparison,
    DecisionPathSummary,
    DecisionStep,
    DependencyReference,
    DependencySource,
    FinalReachableState,
    PortfolioDecisionPathBreakdown,
    ReachabilityStatus,
    RequiredProgressKind,
)
from atlas.alpha.decision_path.service import DecisionPathService

__all__ = [
    "RequiredProgressKind",
    "ReachabilityStatus",
    "DependencySource",
    "DependencyReference",
    "DecisionStep",
    "FinalReachableState",
    "DecisionPath",
    "DecisionPathSummary",
    "DecisionPathComparison",
    "DecisionPathChange",
    "PortfolioDecisionPathBreakdown",
    "DecisionPathService",
]

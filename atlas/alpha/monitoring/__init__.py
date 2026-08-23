"""Monitoring & Change Detection (Atlas Intelligence Sprint 7).

**Deliverable 1 -- Monitoring Audit, findings.** Read fresh from disk
before writing anything here:

- **Change Intelligence** (`atlas.analysis_engine.investment_case_change`
  + `atlas.alpha.investment_case_change`) already produces real
  before/after comparisons (`compare_snapshots`), persisted, idempotent
  by content hash, already filtered to non-baseline real changes only
  (`atlas.analysis_engine.daily_brief.build_daily_brief_entry`).
- **Evidence Timeline** (`atlas.alpha.evidence_timeline`) already
  produces real before/after comparisons for Coverage/Confidence/
  Stance/Evidence Quality/Freshness/Conflict, each transition already
  tagged `is_material` (Sprint 6, reusing Materiality's own judgment).
- **Evidence Quality**, **Coverage**, **Confidence**, **Stance**,
  **Materiality** are all pure, current-state-only computations with no
  persistence of their own -- their *history* is what Evidence Timeline
  exists to capture; this package never re-derives any of them.
- **Portfolio Fit**'s own `FitTrend` is not independent history -- it is
  a direct relabeling of `ChangeIntelligence.thesis_impact`
  (`atlas.alpha.portfolio_fit.engine._TREND_BY_THESIS_IMPACT`), and that
  package's own docstring says so explicitly ("this engine stores no
  history of its own"). Monitoring therefore does not source a category
  from it -- see `models.py`'s own `MonitoringChangeCategory` docstring.
- **CaseCondition** already exposes a current-state `status`, evaluated
  only on explicit investor/API action
  (`POST /case-conditions/{id}/evaluate`); there is no automatic
  evaluation anywhere, and this sprint does not add one (Deliverable 16:
  "preserve the existing CaseCondition lifecycle exactly"). Monitoring
  reads the current `status`/`role`, the same current-state gate
  `daily_brief_agenda.engine.case_condition_signal` already applies.
- **Daily Brief Agenda** (`atlas.alpha.daily_brief_agenda`) already
  consolidates several independent signal sources into one item per
  ticker (`_item_for_ticker`), already discloses "each of these composes
  `InvestmentCaseCompositionService.build(case_id)` independently" as an
  accepted cost, and already has no cross-call "already seen" tracking
  of its own -- every call recomputes from currently-true facts. This is
  the one real, disclosed gap Monitoring exists to fill for six
  capabilities Daily Brief did not previously consume at all (Coverage,
  Confidence, Stance, Evidence Quality, Evidence Timeline, Materiality).
- **Portfolio Status**/**Portfolio Cockpit attention** are pure
  current-state structural checks (e.g. "a Decision exists with no
  matching Outcome today") -- never a transition, nothing to reuse for
  change detection specifically.
- **`atlas/monitoring`** (the pre-existing, differently-named legacy
  package) is a stateless scoring utility over an older, pre-Alpha
  domain model (`atlas.adapters.portfolio.Portfolio`, `atlas.themes`,
  `atlas.market`), with **zero persistence** and a "previous baseline"
  that is **synthetically fabricated** (`_previous_baseline()` applies
  hardcoded score deltas to the current snapshot, never reads real
  history). This is independently confirmed by this repository's own
  `docs/ADR-Investigation-005-Review-Trigger-vs-Monitoring-vs
  -Invalidation.md` (Phase 2, 17, 20), which already investigated this
  exact package for an unrelated but adjacent purpose and reached the
  identical conclusion: kept unchanged, kept fully separate, not
  reused, not extended, not wrapped. This Sprint 7 package deliberately
  shares no code, no name collision beyond coincidence, and no
  relationship with `atlas/monitoring`.

**Deliverable 2 -- Monitoring Boundary.** Monitoring in Atlas is
comparing newly available state against previously known state and
identifying material changes. It is not a cron system (no scheduler is
introduced -- `MonitoringService.run()` is an explicit operation, not a
background loop), not a notification system (no delivery mechanism of
any kind), not a price alert, not a news feed, not a prediction (every
`MonitoringChange` classifies something that already, genuinely
happened), not a recommendation engine (it never produces a Stance,
Recommendation, or investment conclusion of its own), and not a new
`CaseCondition` implementation (it reads CaseCondition's existing
`status` current-state, exactly as `daily_brief_agenda` already does,
and adds no new predicate/evaluation mechanism).

Continuing the ADR-Investigation-005 vocabulary directly: that
investigation left open, as its own third unresolved question, "what is
the actual scheduling/evaluation mechanism for state-based conditions,
given `atlas/monitoring` cannot currently serve this role?" This
package is one part of the answer for the six capabilities that were
already comparing real before/after state (Evidence Timeline, Change
Intelligence) -- surfacing what they already detect, on an explicit,
investor/operator-triggered run, not a scheduler. It does not attempt
to answer that question for CaseCondition's own state-based predicates
specifically (those remain investor-authored and API-evaluated, per
that investigation's own Phase 11/17 findings, unchanged here).

**Internal Alpha Fix Sprint 1 -- Automatic Monitoring & Continuous
Refresh, Deliverable 1/2 audit findings.** Read fresh from disk before
writing anything: `run()` was already exactly this deterministic,
explicit operation described above -- the gap was never in `run()`
itself, it was that nothing called it. Confirmed by grep across the
entire frontend and backend: `POST /monitoring/run` had no caller
anywhere except its own router; no `@app.on_event`/`lifespan` hook
exists in `atlas.core.infrastructure.api.app`; no cron, no
`APScheduler`, no `asyncio` periodic task, no polling loop existed
anywhere in this codebase. One piece of reusable "run work without
blocking the response" infrastructure *did* already exist and this
sprint reuses it rather than inventing a second one: Starlette's
`BackgroundTasks`, already used by `atlas.alpha.portfolio.api.router
._run_bulk_enrichment_in_background` (Internal Alpha Fix Sprint 1,
Part 1) to defer bulk enrichment past the response. This sprint's own
automatic triggering is exactly that same mechanism, at three real
data-mutation call sites (Watchlist add, a new-position trade, bulk
Portfolio enrichment) -- never a scheduler, never a loop, never a
second job system. See `service.py`'s own module docstring for exactly
how (`trigger_automatic_run`, the non-blocking sibling of `run`, and
the one process-wide lock both now share).
"""
from __future__ import annotations

from .engine import (
    DAILY_BRIEF_EXCLUDED_CATEGORIES,
    HIGH_IMPORTANCE_CATEGORIES,
    build_monitoring_result,
    classify_case_condition,
    classify_evidence_history,
    classify_material_risk,
    derive_status,
)
from .models import (
    MonitoringChange,
    MonitoringChangeCategory,
    MonitoringMateriality,
    MonitoringResult,
    MonitoringRun,
    MonitoringScope,
    MonitoringStatus,
)
from .service import MonitoringService

__all__ = [
    "DAILY_BRIEF_EXCLUDED_CATEGORIES",
    "HIGH_IMPORTANCE_CATEGORIES",
    "build_monitoring_result",
    "classify_case_condition",
    "classify_evidence_history",
    "classify_material_risk",
    "derive_status",
    "MonitoringChange",
    "MonitoringChangeCategory",
    "MonitoringMateriality",
    "MonitoringResult",
    "MonitoringRun",
    "MonitoringScope",
    "MonitoringStatus",
    "MonitoringService",
]

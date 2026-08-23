"""Decision Memory (Atlas Decision Layer, Sprint 5). Alpha-only, no
Core change.

**Deliverable 1 (Decision Memory Audit) -- every persistent
decision-related object in this codebase, and what it actually
remembers**:

- **Investment Decision** (`investment_decision_results`, Sprint 1),
  **Decision Readiness** (`decision_readiness_results`, Sprint 11),
  **Recommendation Conviction** (`recommendation_conviction_results`,
  Sprint 2), **Decision Path** (`decision_path_results`, Sprint 3),
  **Opportunity Cost** (`opportunity_cost_results`, Sprint 4) --
  **each persists exactly one row per Case, upserted (delete-then-
  insert) on every fresh computation.** Every one of these tables
  exists *solely* so that specific sprint's own `change_for_case` can
  read the immediately-previous computation back before overwriting
  it -- confirmed by reading each repository's own `upsert`, which
  always deletes the existing row first. **This is the central finding
  of this audit**: none of the five prior Decision Layer sprints
  persists more than one snapshot per Case. The moment a second
  real change happens, the *first* change is gone forever -- there has
  never been a way to ask "what did this decision look like three
  changes ago," only "what changed since the single most recent
  computation." This package exists to close exactly that gap, and
  only that gap.
- **Monitoring** (`monitoring_run_record_table`/`monitoring_result_table`,
  Atlas Intelligence Sprint 7) -- **already append-only**, but at the
  wrong grain for this package's own purpose: it records *when a
  monitoring run happened* and *what raw Coverage/Confidence/Stance/
  Evidence facts it found*, never the Decision Layer's own downstream
  conclusions (action, conviction, path, alternatives). Read
  transitively (via Decision Readiness's own blockers), never
  duplicated here.
- **`atlas.alpha.investment_case_change`**
  (`investment_case_snapshots`, Atlas Intelligence Sprint 6) -- **the
  one genuinely append-only precedent in this codebase**, and the
  direct template this package's own `table.py`/`repository.py`
  mirror line-for-line (synthetic `f"{case_id}:{timestamp}"` id,
  `content_hash`-idempotent `add`, persisted-not-recomputed change
  transition per row). It snapshots *raw analytical facts*
  (`business_category_states`, `risk_category_states`, ...), never the
  Decision Layer's own synthesized conclusions -- genuinely
  complementary, never duplicated.

**No new investment analysis is introduced anywhere in this package.**
`DecisionSnapshotInputs` (`engine.py`) is a direct, compact read of
five already-computed values from Investment Decision, Decision
Readiness, Recommendation Conviction, Decision Path, and Opportunity
Cost; nothing here re-derives any of them.

Re-exports: `DecisionSnapshot`, `ChangeDirection`, `DecisionMemoryChange`,
`DecisionTimelineEntry`, `DecisionTimeline`, `DecisionMemory`,
`DecisionMemoryComparison`, `PortfolioDecisionMemoryBreakdown`,
`DecisionMemoryService`.
"""
from __future__ import annotations

from atlas.alpha.decision_memory.models import (
    ChangeDirection,
    DecisionMemoryChange,
    DecisionMemory,
    DecisionMemoryComparison,
    DecisionSnapshot,
    DecisionTimeline,
    DecisionTimelineEntry,
    PortfolioDecisionMemoryBreakdown,
)
from atlas.alpha.decision_memory.service import DecisionMemoryService

__all__ = [
    "DecisionSnapshot",
    "ChangeDirection",
    "DecisionMemoryChange",
    "DecisionTimelineEntry",
    "DecisionTimeline",
    "DecisionMemory",
    "DecisionMemoryComparison",
    "PortfolioDecisionMemoryBreakdown",
    "DecisionMemoryService",
]

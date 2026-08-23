"""Investment Decision Synthesis (Atlas Decision Layer, Sprint 1).
Alpha-only, no Core change.

**Deliverable 1 (Decision Audit) -- summary of the findings this
package is built on**:

- **Decision Support** (`atlas.alpha.decision_support
  .DecisionSupportLevel`) -- **influences**. The final synthesis's own
  anchor: a direct, one-to-one re-expression into `DecisionAction`
  (`engine.py`'s own `ACTION_BY_DECISION_SUPPORT_LEVEL`). Already the
  "what does current evidence support" signal every prior sprint
  audited and reused (Sprint 11's own finding).
- **Stance** (`atlas.alpha.stance.Stance`) -- **influences (one trigger)
  and explains**. `StanceLevel.AVOID_DECISION` is folded in as a
  `decision_blocked` qualifier trigger (a real red flag strong enough
  to qualify any action); `StanceLevel.REVIEW` triggers
  `careful_decision`. Every other Stance fact (the top gating reason)
  is explanation only -- Stance is never a second, competing action
  signal (see `engine.py`'s own docstring for why).
- **Decision Readiness** (`atlas.alpha.decision_readiness
  .DecisionReadiness`) -- **qualifies and explains**. Every blocker/
  supporting reason it already computed is reused verbatim as this
  package's own blockers/supporting reasons (`DecisionReason` is a
  tagged pointer, never a new code); `DecisionReadinessStatus` drives
  three of the six qualifiers (`decision_blocked`/`operationally_delayed`/
  `careful_decision`).
- **Coverage/Confidence** -- **qualifies indirectly**, already folded
  into Decision Readiness's own status and Stance's own confidence;
  never re-read directly here.
- **Evidence Quality** -- **explains indirectly**, already folded into
  Decision Readiness's own `conflicting_evidence`/`missing_thesis_evidence`
  blockers (via Evidence Graph, Sprint 10); never re-read directly.
- **Materiality** -- **explains only**. Classifies how much attention a
  Stance reason deserves; adds no fact this package's `DecisionReason`
  vocabulary needs.
- **Monitoring** -- **qualifies indirectly**, already folded into
  Decision Readiness's own `UNAVAILABLE`/`monitoring_pending` facts;
  this package never calls `MonitoringService` itself (Deliverable 11's
  own "never duplicate Monitoring").
- **Evidence Timeline** -- **explains only**. A historical record;
  synthesis needs the Case's *current* state, not its history.
- **Portfolio Fit** -- **excluded entirely**, the same deliberate
  exclusion Sprint 11 already established: Fit describes portfolio
  suitability, not whether the security itself deserves an action.
- **Explainability** -- **explains only**. Restates Stance's own
  supporting/limiting signals in structured form; this package reads
  Stance's `reasoning` directly instead of a second, redundant layer.

**No new investment analysis is introduced anywhere in this package.**
Every field `SynthesisInputs` (`engine.py`) carries is a direct read of
an already-computed value from Decision Support, Decision Readiness, or
Stance; nothing here re-derives any of them.

Re-exports: `DecisionAction`, `DecisionReasonSource`, `DecisionReason`,
`DecisionQualifierKind`, `DecisionQualifier`, `InvestmentDecision`,
`DecisionSummary`, `DecisionComparison`, `DecisionChange`,
`InvestmentDecisionService`.
"""
from __future__ import annotations

from atlas.alpha.investment_decision.models import (
    DecisionAction,
    DecisionChange,
    DecisionComparison,
    DecisionQualifier,
    DecisionQualifierKind,
    DecisionReason,
    DecisionReasonSource,
    DecisionSummary,
    InvestmentDecision,
)
from atlas.alpha.investment_decision.service import InvestmentDecisionService

__all__ = [
    "DecisionAction",
    "DecisionReasonSource",
    "DecisionReason",
    "DecisionQualifierKind",
    "DecisionQualifier",
    "InvestmentDecision",
    "DecisionSummary",
    "DecisionComparison",
    "DecisionChange",
    "InvestmentDecisionService",
]

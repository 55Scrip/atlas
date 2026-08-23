"""Decision Readiness & Decision Eligibility (Atlas Intelligence Sprint
11). Alpha-only, no Core change.

**Deliverable 1 (Audit Existing Decision Signals) -- summary of the
findings this package is built on** (full detail in this sprint's own
Final Report):

For every existing signal, whether it drives *readiness* (does Atlas
have enough to responsibly decide) or only *explanation* (why Atlas
believes what it believes, once it has decided):

- **Coverage** (`CanonicalAnalysis.analysis_coverage.level`,
  `AnalysisCoverageLevel`) -- **readiness**. The most direct "has Atlas
  looked at enough" signal that already exists; `NO_COVERAGE`/
  `PARTIAL_COVERAGE`/`SUBSTANTIAL_COVERAGE` map almost one-to-one onto
  this sprint's own `UNKNOWN`/`WAITING`/(further checks) ladder.
- **Confidence** (`Stance.confidence`, itself a verbatim copy of
  `CoverageAssessment.overall_confidence`) -- **readiness**. How much
  Atlas trusts its own understanding; separates `READY` from
  `ALMOST_READY` once coverage and decision support are both real.
- **Stance** (`Stance.level`) -- **mostly explanation, one readiness
  signal**. Stance answers "what does Atlas currently believe," a
  different question from readiness (see `models.py`'s own docstring).
  Only `StanceLevel.AVOID_DECISION` (a real red flag strong enough that
  Atlas should not support any decision right now) feeds readiness
  directly, as a `BLOCKED` trigger; every other Stance level is
  explanation only.
- **Explainability** (`atlas.alpha.explainability`) -- **explanation
  only**. Restates Stance's own supporting/limiting signals in
  structured form; adds no new fact readiness could use.
- **Materiality** (`atlas.alpha.materiality`) -- **explanation only**.
  Classifies *how much attention* a Stance reason deserves, not whether
  a decision is justified.
- **Evidence Quality** (`atlas.alpha.evidence_quality`) -- **partially
  readiness, reused via Evidence Graph rather than recomputed**. Its
  `conflict_status`/`unsupported_findings` are real readiness-relevant
  facts, but this package never calls `assess_evidence_quality` itself
  (which would need its own `BusinessRecord` fetch) -- Sprint 10's
  Evidence Graph already surfaces the identical facts more cheaply: a
  `contradicting_evidence`-kind `FINDING` node (Evidence Quality's own
  "conflicting" case) and `NO_SUPPORT` weak dependencies ("missing
  thesis evidence"). Reusing Evidence Graph avoids a second, redundant
  `BusinessRecord` read for the same underlying fact.
- **Monitoring / Operational Freshness** (`MonitoringService
  .freshness_for_case`) -- **readiness**. `is_pending`/
  `last_monitored_at`/`last_run_failed_for_case`/`data_freshness_status`
  are the direct source of `WAITING` (still checking) versus
  `UNAVAILABLE` (Atlas's own machinery has no trustworthy read).
- **Evidence Timeline** (`atlas.alpha.evidence_timeline`) --
  **explanation only**. A historical record of what changed and when;
  readiness needs the Case's *current* state, not its history --
  reused already, indirectly, wherever Monitoring itself reads it.
- **Portfolio Fit** (`atlas.alpha.portfolio_fit`) -- **explanation
  only, deliberately excluded from readiness**. Fit describes how a
  position suits *the portfolio*, not whether the underlying
  investment case itself is understood well enough to decide about the
  security on its own terms -- a Case can be fully `READY` with a
  `WEAK` Fit (a good understanding of a bad fit) exactly as easily as
  the reverse. Never a readiness input; still an independent factor an
  investor weighs alongside readiness (kept fully separate, the same
  "operational status is not investment status" discipline
  Monitoring/Ingestion already established for their own boundary).
- **Decision Support** (`atlas.alpha.decision_support
  .describe_recommendation`) -- **readiness**. `DecisionSupportLevel
  .INSUFFICIENT_EVIDENCE` already means "no directional conclusion was
  reachable at all" -- the single closest existing signal to "is a
  decision justified," and the anchor `WAITING`/`READY` are built on
  when combined with Coverage/Confidence.

**No new investment analysis is introduced anywhere in this package.**
Every field `ReadinessInputs` (`engine.py`) carries is a direct read of
an already-computed value from one of the six services above; nothing
here re-derives Coverage, Confidence, Stance, Evidence Quality,
Monitoring, or Decision Support.

Re-exports: `DecisionReadinessStatus`, `DecisionBlockerKind`,
`DecisionBlocker`, `DecisionReadinessReasonKind`,
`DecisionReadinessReason`, `DecisionReadiness`,
`DecisionReadinessSummary`, `DecisionReadinessComparison`,
`DecisionReadinessChange`, `DecisionReadinessService`.
"""
from __future__ import annotations

from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadiness,
    DecisionReadinessChange,
    DecisionReadinessComparison,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
    DecisionReadinessSummary,
)
from atlas.alpha.decision_readiness.service import DecisionReadinessService

__all__ = [
    "DecisionReadinessStatus",
    "DecisionBlockerKind",
    "DecisionBlocker",
    "DecisionReadinessReasonKind",
    "DecisionReadinessReason",
    "DecisionReadiness",
    "DecisionReadinessSummary",
    "DecisionReadinessComparison",
    "DecisionReadinessChange",
    "DecisionReadinessService",
]

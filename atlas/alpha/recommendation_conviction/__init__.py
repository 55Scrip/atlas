"""Recommendation Conviction & Strength (Atlas Decision Layer, Sprint
2). Alpha-only, no Core change.

**Deliverable 1 (Recommendation Audit) -- summary of the findings this
package is built on**:

- **`atlas.analysis_engine.conviction.ConvictionAssessment`** (five
  levels: VERY_HIGH/HIGH/MODERATE/LOW/INSUFFICIENT_EVIDENCE) --
  **already reflected, this package's primary input**. Already real,
  already computed by `pipeline.py`'s own `calculate_conviction` for
  every Case, already exposed today in the Investment Case page's
  Evidence section (`ConvictionAssessmentView`). This already answers
  "how strongly does available analysis support an investment
  conclusion" -- exactly this sprint's own question -- so
  `ConvictionStrength` (`models.py`) is a direct, six-level
  re-expression of it, never a second independent computation.
- **`atlas.analysis_engine.recommendation_conviction`** (three levels:
  HIGH/MEDIUM/LOW, `DE-004` §3) -- **deliberately never read here**.
  That module's own docstring establishes it as a genuinely separate
  scale, "never merged, never presented under the same label, never
  interchangeable" with the five-level one above; it is also, by its
  own admission, "not yet consumed anywhere" -- no stage computes real
  `EvaluationState.EVALUATED` values for all four of its required
  inputs today, so it has no real Case to read from even if this
  package wanted to. Reading it would mean depending on permanently-
  dead-for-now inputs; this package follows the same disambiguation
  discipline instead of merging a third scale into either existing
  one.
- **Decision Readiness** (`atlas.alpha.decision_readiness
  .DecisionReadiness`, Sprint 11) -- **qualifies (caps) and explains**.
  `DecisionReadinessStatus` caps how strong the analysis-derived base
  value is allowed to read (`engine.py`'s own `_READINESS_CAP`) -- the
  same "one signal must never contradict another" discipline that
  fixed Sprint 11's own READY-with-blockers bug; every blocker/
  supporting reason it already computed is reused verbatim as this
  package's own limiting/supporting reasons (`ConvictionReason` is a
  tagged pointer, never a new code), and a fixed blocker-kind subset
  also drives `RecommendationStability`.
- **Investment Decision** (`atlas.alpha.investment_decision
  .InvestmentDecision`, Sprint 1) -- **gates and anchors**.
  `DecisionAction.NO_DECISION` is the only path to `ConvictionStrength
  .UNAVAILABLE` -- there is no recommendation yet to hold a conviction
  about. Every other field of `RecommendationConviction` describes
  *that* action, never a second, independently-reasoned action.
- **Coverage/Confidence** -- **qualifies indirectly**, already folded
  into both `ConvictionAssessment` (`evidence_coverage`) and Decision
  Readiness's own status; never re-read directly here.
- **Evidence Quality** -- **explains indirectly**, already folded into
  `ConvictionAssessment`'s own `contradicting_evidence`/`open_questions`
  reasons and into Decision Readiness's `conflicting_evidence` blocker;
  never re-read directly.
- **Materiality** -- **never influences**. Classifies attention on a
  Stance reason; adds no fact this package's reason vocabulary needs
  (same exclusion Sprint 1 already made).
- **Monitoring** -- **qualifies indirectly**, already folded into
  Decision Readiness's own `UNAVAILABLE`/operational blockers; this
  package never calls `MonitoringService` itself, the same "never
  duplicate Monitoring" discipline Sprint 1 already established.
- **Evidence Graph** (`atlas.alpha.evidence_graph`, Sprint 10) --
  **qualifies (Stability) and explains**. `WeaknessKind` facts are a
  real, structural signal Decision Readiness's own blockers do not
  carry (a weak link can exist even when nothing is formally
  "blocked") -- read directly here for the first time in the Decision
  Layer, driving `RecommendationStability.FRAGILE` and a real limiting
  reason.
- **Stance** -- **never influences here, explicitly**. Sprint 1 already
  folds Stance's own top reasoning code into the Investment Decision's
  supporting reasons; re-reading it here would duplicate that instead
  of adding a new fact, so this package's `ConvictionReasonSource` has
  no `STANCE` member at all.
- **Portfolio Fit** -- **excluded entirely**, the same deliberate
  exclusion Sprint 1 and Sprint 11 both already made: Fit describes
  portfolio suitability, not the security's own recommendation
  strength.

**No new investment analysis is introduced anywhere in this package.**
Every field `ConvictionInputs` (`engine.py`) carries is a direct read
of an already-computed value from Investment Decision, Decision
Readiness, `ConvictionAssessment`, or Evidence Graph; nothing here
re-derives any of them.

Re-exports: `ConvictionStrength`, `RecommendationStability`,
`ConvictionReasonSource`, `ConvictionReason`, `RecommendationConviction`,
`ConvictionSummary`, `ConvictionComparison`, `ConvictionChange`,
`PortfolioConvictionBreakdown`, `RecommendationConvictionService`.
"""
from __future__ import annotations

from atlas.alpha.recommendation_conviction.models import (
    ConvictionChange,
    ConvictionComparison,
    ConvictionReason,
    ConvictionReasonSource,
    ConvictionStrength,
    ConvictionSummary,
    PortfolioConvictionBreakdown,
    RecommendationConviction,
    RecommendationStability,
)
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService

__all__ = [
    "ConvictionStrength",
    "RecommendationStability",
    "ConvictionReasonSource",
    "ConvictionReason",
    "RecommendationConviction",
    "ConvictionSummary",
    "ConvictionComparison",
    "ConvictionChange",
    "PortfolioConvictionBreakdown",
    "RecommendationConvictionService",
]

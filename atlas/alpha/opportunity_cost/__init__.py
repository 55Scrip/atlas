"""Decision Alternatives & Opportunity Cost (Atlas Decision Layer,
Sprint 4). Alpha-only, no Core change.

**Deliverable 1 (Alternative Audit) -- every place this codebase
already compares companies, and what this package reuses vs. adds**:

- **`atlas.alpha.investment_decision.engine.compare_decisions`**
  (Sprint 1) -- **already reflected, never re-read here**. Its own
  `shared_blocker_codes`/`shared_supporting_reason_codes` describe
  which real facts two Cases share, not which Case is "stronger" --
  this package's own alternatives already carry each other Case's own
  action/reason directly (`DecisionAlternative.action`/`.reason`),
  so re-comparing qualifiers here would duplicate, not add, a fact.
- **`atlas.alpha.recommendation_conviction.engine.compare_convictions`**
  (Sprint 2) -- **reused verbatim**, the primary "which side is
  stronger" signal `AlternativeComparison.conviction` embeds directly.
- **`atlas.alpha.decision_path.engine.compare_decision_paths`**
  (Sprint 3) -- **reused verbatim**, the primary "which side has less
  left to resolve" signal `AlternativeComparison.path` embeds
  directly. This package adds exactly one new, small comparison of its
  own (`more_dependency_blocked_case_id`), read directly from each
  side's own already-computed `DecisionPath.steps` -- never a new
  scoring algorithm, just one more real fact those steps already
  carry that neither prior sprint's own `compare_*` happened to
  surface.
- **Portfolio Fit's own comparison** (`atlas.alpha.portfolio_fit
  .compare_portfolio_fit`) -- **never influences opportunity cost**.
  Sprint 1 and Sprint 11 both already excluded Portfolio Fit from
  their own synthesis on the same grounds this package inherits: Fit
  describes portfolio *suitability*, not whether a security competes
  for the same capital as another. Two Cases can be genuine
  Opportunity Cost alternatives (both `BUY`-rated) while having wildly
  different Fit profiles -- conflating the two would silently turn
  "which company competes for capital" into "which company fits the
  portfolio better," a different, unrequested question.
- **Stance's/Evidence Graph's/Explainability's own `compare_*`
  functions** -- **never read here**, the same reasoning: each answers
  a real but different question (directional belief, dependency
  structure, explanation overlap) than "does this compete for the same
  capital," and Compare's own page already surfaces each independently
  (Deliverable 9 extends Compare by adding one more independent
  section, never by merging into an existing one).
- **Discovery's own ranking** (`atlas.alpha.portfolio_fit
  .rank_candidates`) -- **never influenced, never read for ranking
  purposes**. This package is read *from* Discovery (Deliverable 8),
  never the reverse.

**No new investment analysis is introduced anywhere in this package.**
`DecisionAlternative` never references a company Atlas has not already
built a real Case for (`atlas.alpha.case_membership.known_cases`, the
same closed universe every sibling Decision Layer service already
uses); every alternative's own reason is a direct, 1:1 conversion of
an already-real `DecisionReason` (Sprint 1) or Decision Path
`DependencyReference` (Sprint 3) -- never a new reason code.

Re-exports: `AlternativeKind`, `AlternativeReasonSource`,
`AlternativeReason`, `DecisionAlternative`, `AlternativeComparison`,
`DecisionTradeoff`, `OpportunityCost`, `DecisionAlternativeSummary`,
`PortfolioOpportunityCostBreakdown`, `OpportunityCostChange`,
`OpportunityCostService`.
"""
from __future__ import annotations

from atlas.alpha.opportunity_cost.models import (
    AlternativeComparison,
    AlternativeKind,
    AlternativeReason,
    AlternativeReasonSource,
    DecisionAlternative,
    DecisionAlternativeSummary,
    DecisionTradeoff,
    OpportunityCost,
    OpportunityCostChange,
    PortfolioOpportunityCostBreakdown,
)
from atlas.alpha.opportunity_cost.service import OpportunityCostService

__all__ = [
    "AlternativeKind",
    "AlternativeReasonSource",
    "AlternativeReason",
    "DecisionAlternative",
    "AlternativeComparison",
    "DecisionTradeoff",
    "OpportunityCost",
    "DecisionAlternativeSummary",
    "PortfolioOpportunityCostBreakdown",
    "OpportunityCostChange",
    "OpportunityCostService",
]

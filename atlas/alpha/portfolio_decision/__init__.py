"""Portfolio Decision Synthesis (Atlas Decision Layer Sprint 8).

DELIVERABLE 1 -- PORTFOLIO DECISION AUDIT
============================================

Every existing portfolio-related decision input in this codebase,
audited before any new code was written.

**Portfolio Fit** (`atlas.alpha.portfolio_fit`) -- `PortfolioFitAssessment
.dimensions[ALLOCATION]` already answers, per-holding, whether its own
weight is too large relative to the portfolio (`FitRating.WEAK`/
`POOR` at real, already-declared 25%/35% thresholds -- see
`atlas.alpha.portfolio_intelligence.thresholds`, the shared, centralized
copy of the same numbers `portfolio_fit.engine` itself uses).
**Genuinely influences portfolio decisions and already synthesized**
-- reused directly as this package's own overweight signal, never
re-thresholded.

**Portfolio Health** (`atlas.alpha.portfolio_status.PortfolioHealthMetrics`)
-- audited and found **presentation-only for this package's purpose**:
its own fields (holdings-with-Case count, outstanding workflow items,
unknown-instrument tickers) describe data completeness, not a real
per-decision portfolio tension. Not composed here.

**Investment Decision** (`atlas.alpha.investment_decision`, Sprint 1)
-- `InvestmentDecision.action` is this package's own primary input:
"what does this decision mean for my portfolio" is meaningless without
first knowing what the decision *is*. Reused directly, never
recomputed.

**Recommendation Conviction** (`atlas.alpha.recommendation_conviction`,
Sprint 2) -- audited and found **not composed directly**: this
package's own reliability question is already answered more precisely
by Decision Reliability (Sprint 7), which itself already reads
Conviction's own real facts one layer down. Composing Conviction here
too would duplicate a fact Reliability already carries.

**Decision Path** (`atlas.alpha.decision_path`, Sprint 3) -- audited
and found **not composed directly**: "what still needs to happen" is
a different question from "what does this decision mean for my
portfolio right now." No portfolio-context fact in this sprint's own
brief needs it.

**Opportunity Cost** (`atlas.alpha.opportunity_cost`, Sprint 4) --
**this is Deliverable 4's own Capital Competition, already built.**
`OpportunityCost.tradeoffs` already names every real, already-computed
alternative competing for the same capital (`INCREASE_EXISTING_HOLDING`
/`OPEN_NEW_POSITION` -- "real capital competition from inside/outside
the portfolio," per that package's own docstring). This package
reclassifies those tradeoffs into competing/non-competing buckets; it
invents no new alternative and recomputes no comparison.

**Decision Reliability** (`atlas.alpha.decision_reliability`, Sprint
7) -- `DecisionReliability.level` is this package's own second primary
input, reused verbatim for the `OPERATIONALLY_LIMITED`/`UNKNOWN`
classification floor states -- the same floor-state pattern Reliability
itself inherited from Decision Readiness one layer down.

**Portfolio Intelligence** (`atlas.alpha.portfolio_intelligence`,
Atlas Intelligence Sprint 16) -- `PortfolioIntelligenceReport
.key_findings` (`HIGH_CONCENTRATION`/`ELEVATED_CONCENTRATION`/
`LARGE_UNALLOCATED`) is this package's own third input, for the
portfolio-wide (not holding-specific) concentration/cash-availability
context. Reused verbatim, never re-derived; this package does not
recompute concentration thresholds a second time (see `engine.py`'s
own module docstring).

**Review Queue** (`atlas.alpha.portfolio_status.ReviewQueueItem`) --
audited and found **presentation-only for this package's purpose**:
it answers "which holding has an unfinished workflow step," not "does
this decision fit the portfolio." Not composed here.

**Duplication found and avoided**: a second concentration-threshold
check (mirroring `portfolio_fit.engine`'s own private
`_HIGH_CONCENTRATION_WEIGHT_PERCENT`/`_ELEVATED_CONCENTRATION_WEIGHT_PERCENT`)
was deliberately NOT written here -- this package reads Portfolio
Fit's own already-classified `FitRating` instead. A second "large cash"
threshold was also NOT invented -- `KeyFindingKind.LARGE_UNALLOCATED`
(Portfolio Intelligence's own already-computed fact) is reused as-is.

**Presentation-only found**: `PortfolioFitAssessment.overall_reasoning`/
`.dimensions[*].reasoning` are free-form English sentences (not a
closed reason-code vocabulary, unlike every other Decision Layer
input) -- this package therefore reads Portfolio Fit's own `FitRating`
enum values only, never its free-text reasoning, keeping every
`PortfolioDecisionReason` a real tagged pointer.

**Two brief examples audited and found to have no real, already-
computed data source anywhere in this codebase: "Already diversified"
and "Already duplicated exposure."** Neither is fabricated here --
`PortfolioDecisionImpact` deliberately does not carry either fact; see
`models.py`'s own docstring. This mirrors this whole program's
standing discipline (Sprint 4's own "Consider Increase Conviction"/
"Consider Wait" were identically excluded for the identical reason).

This package computes no new portfolio analysis. It is a pure
reclassification and composition layer over five already-real,
already-validated judgments, exactly as the brief's own opening
states.
"""
from atlas.alpha.portfolio_decision.models import (
    CapitalCompetition,
    PortfolioDecision,
    PortfolioDecisionCategory,
    PortfolioDecisionChange,
    PortfolioDecisionComparison,
    PortfolioDecisionImpact,
    PortfolioDecisionReason,
    PortfolioDecisionReasonSource,
    PortfolioDecisionReference,
    PortfolioDecisionSummary,
    PortfolioSynthesisBreakdown,
)
from atlas.alpha.portfolio_decision.service import PortfolioDecisionService

__all__ = [
    "PortfolioDecisionCategory",
    "PortfolioDecisionReasonSource",
    "PortfolioDecisionReference",
    "PortfolioDecisionReason",
    "PortfolioDecisionImpact",
    "CapitalCompetition",
    "PortfolioDecision",
    "PortfolioDecisionSummary",
    "PortfolioDecisionComparison",
    "PortfolioDecisionChange",
    "PortfolioSynthesisBreakdown",
    "PortfolioDecisionService",
]

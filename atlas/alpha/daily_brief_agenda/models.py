"""Result shapes for the Daily Brief Agenda. See this package's own
`__init__.py` for the full design rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = [
    "PriorityLevel",
    "AgendaItemKind",
    "AgendaGroup",
    "AgendaSource",
    "SignalNature",
    "AgendaItem",
    "PortfolioSummary",
    "DailyBriefAgenda",
]


class SignalNature(str, Enum):
    """Fix Sprint 4 (Daily Brief Signal Quality) -- the one new
    vocabulary this sprint adds, and the only thing it adds: whether a
    signal represents something that just happened, or a state that
    has simply not stopped being true. Never a third "mixed" value at
    the signal level -- `engine.py`'s own `portfolio_fit_signal` is the
    one source whose real firing condition can be either, and it
    resolves to exactly one of these two for each signal it actually
    constructs, the same way every other source already resolves to
    exactly one `PriorityLevel`."""

    CHANGE_EVENT = "change_event"
    """A real transition was detected between two consecutive
    computations -- `engine.py`'s own "no event, no timestamp" sources
    (Decision Readiness, Investment Decision, Recommendation
    Conviction, Decision Path, Opportunity Cost, Decision Memory,
    Decision Explanation, Decision Reliability, Portfolio Decision,
    Change Intelligence, Monitoring), plus Portfolio Fit specifically
    when its own `trend` (itself reused, real change information --
    see that source's own docstring) is what fired the signal."""

    PERSISTENT_CONDITION = "persistent_condition"
    """A state that is still true, evaluated fresh on every read, with
    no "did this change since last time" check behind it -- Case
    Condition, Assumption, Portfolio Status (the review queue),
    Portfolio Intelligence (concentration, missing evidence), and
    Portfolio Fit specifically when its own current rating (not trend)
    is what fired the signal."""


class PriorityLevel(str, Enum):
    """The one qualitative vocabulary the whole agenda uses -- never a
    number, never a percentage. Deliverable 3's own suggested four
    levels, used verbatim."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class AgendaItemKind(str, Enum):
    """The closed set of recommended next steps (Deliverable 6) -- each
    one an existing product workflow, never a free-form suggestion."""

    REVIEW_INVESTMENT_CASE = "review_investment_case"
    REVIEW_PORTFOLIO_POSITION = "review_portfolio_position"
    REVIEW_WATCHLIST_CANDIDATE = "review_watchlist_candidate"
    COMPARE_CANDIDATE = "compare_candidate"
    REVISIT_ASSUMPTION = "revisit_assumption"
    EVALUATE_CASE_CONDITION = "evaluate_case_condition"
    PORTFOLIO_RISK = "portfolio_risk"
    PORTFOLIO_OPPORTUNITY = "portfolio_opportunity"


class AgendaGroup(str, Enum):
    """Presentation-only (Deliverable 7) -- never used to reorder
    items; priority always wins. `DISCOVERY` is reserved: Product
    Sprint 5 established Discovery has no candidate source independent
    of Watchlist, so every real item today lands in `WATCHLIST` instead
    -- disclosed here rather than populated with a fabricated
    distinction."""

    PORTFOLIO = "portfolio"
    WATCHLIST = "watchlist"
    DISCOVERY = "discovery"
    SYSTEM = "system"


class AgendaSource(str, Enum):
    """Which existing engine produced this item -- Deliverable 5's own
    "Source" field, so every item stays traceable to a real capability,
    never an opaque "Atlas thinks."""

    CHANGE_INTELLIGENCE = "change_intelligence"
    PORTFOLIO_FIT = "portfolio_fit"
    CASE_CONDITION = "case_condition"
    ASSUMPTION = "assumption"
    PORTFOLIO_STATUS = "portfolio_status"
    PORTFOLIO_INTELLIGENCE = "portfolio_intelligence"
    MONITORING = "monitoring"
    """Atlas Intelligence Sprint 7 -- Coverage/Confidence/Stance/
    Evidence Quality/Evidence Timeline change detection, the one real
    gap the other five sources never covered (`ChangeIntelligence`'s
    own `AnalyticalSnapshot` deliberately excludes all of it -- see
    that module's own "Investor Model boundary" docstring). Never
    duplicates `CHANGE_INTELLIGENCE`/`CASE_CONDITION`'s own territory
    -- see `atlas.alpha.monitoring.engine.DAILY_BRIEF_EXCLUDED_CATEGORIES`."""

    DECISION_READINESS = "decision_readiness"
    """Atlas Intelligence Sprint 11 -- "has Atlas reached the point
    where a decision is justified" changing, never the underlying
    Stance/Coverage/Monitoring facts themselves (those still fire
    their own signals above, unchanged); this source only fires on a
    real transition between two consecutive `DecisionReadinessStatus`
    computations for the same Case (`atlas.alpha.decision_readiness
    .engine.detect_readiness_change`'s own "no event, no timestamp"
    contract)."""

    INVESTMENT_DECISION = "investment_decision"
    """Atlas Decision Layer Sprint 1 -- the synthesized action itself
    changing (e.g. Hold -> Add, or becoming Decision Blocked), never
    the underlying Readiness/Stance facts those already have their own
    sources above for. Only fires on a real transition
    (`atlas.alpha.investment_decision.engine.detect_decision_change`'s
    own "no event, no timestamp" contract)."""

    RECOMMENDATION_CONVICTION = "recommendation_conviction"
    """Atlas Decision Layer Sprint 2 -- how strongly Atlas stands
    behind the already-recommended action changing (conviction
    strengthened/weakened, or stability changing, e.g. becoming
    operationally blocked), never the action itself (Investment
    Decision already has its own source above for that) and never the
    underlying Readiness/Evidence facts those already have their own
    sources for. Only fires on a real transition
    (`atlas.alpha.recommendation_conviction.engine
    .detect_conviction_change`'s own "no event, no timestamp"
    contract)."""

    DECISION_PATH = "decision_path"
    """Atlas Decision Layer Sprint 3 -- what would need to change
    before Atlas recommends something different: the decision path
    shortened, became blocked, or a real dependency (operational,
    evidence, or structural) was resolved or newly appeared. Never
    the action or conviction themselves (their own sources above
    already cover that). Only fires on a real transition
    (`atlas.alpha.decision_path.engine.detect_decision_path_change`'s
    own "no event, no timestamp" contract)."""

    OPPORTUNITY_COST = "opportunity_cost"
    """Atlas Decision Layer Sprint 4 -- what a decision genuinely
    competes against changing: a new alternative became available, an
    alternative disappeared or strengthened/weakened, or waiting
    became the primary alternative. Never the action, conviction, or
    path themselves (their own sources above already cover that).
    Only fires on a real transition (`atlas.alpha.opportunity_cost
    .engine.detect_opportunity_cost_change`'s own "no event, no
    timestamp" contract)."""

    DECISION_MEMORY = "decision_memory"
    """Atlas Decision Layer Sprint 5 -- a real, structured change was
    just durably recorded to this Case's own append-only decision
    history: the recommendation changed, conviction/readiness/decision
    path direction moved, a blocker resolved or appeared, or the
    alternative set changed. Fires only when a *new* snapshot was
    actually appended this exact call (`atlas.alpha.decision_memory
    .service.DecisionMemoryService.change_for_case`'s own "no event,
    no timestamp" contract, grounded in the append-only history table
    itself rather than a separate ephemeral cache)."""

    DECISION_EXPLANATION = "decision_explanation"
    """Atlas Decision Layer Sprint 6 -- a real, structured change to
    *why* Atlas holds this Case's own decision: a new supporting
    finding, a resolved or new blocker, or conviction that strengthened
    or weakened. Never the decision itself (source above already
    covers that) -- this names what changed about the explanation for
    it. Only fires on a real transition (`atlas.alpha.decision_explanation
    .engine.detect_decision_explanation_change`'s own "no event, no
    timestamp" contract)."""

    DECISION_RELIABILITY = "decision_reliability"
    """Atlas Decision Layer Sprint 7 -- a real, structured change to
    *how trustworthy* this Case's own decision currently is:
    reliability improved or weakened, an operational issue resolved,
    or evidence strengthened. Never the decision or its explanation
    (the sources above already cover those) -- this names what changed
    about the trust an investor should place in the decision. Only
    fires on a real transition (`atlas.alpha.decision_reliability
    .engine.detect_reliability_change`'s own "no event, no timestamp"
    contract)."""

    PORTFOLIO_DECISION = "portfolio_decision"
    """Atlas Decision Layer Sprint 8 -- a real, structured change to
    what this decision means for the investor's actual portfolio: the
    portfolio category changed, capital competition changed, a
    portfolio conflict resolved, or a new portfolio opportunity
    appeared. Never the decision, its explanation, or its reliability
    (the sources above already cover those) -- this names what changed
    about the decision's own place inside the portfolio. Only fires on
    a real transition (`atlas.alpha.portfolio_decision.engine
    .detect_portfolio_decision_change`'s own "no event, no timestamp"
    contract)."""

    EXECUTIVE_CHANGE = "executive_change"
    """Product Intelligence Sprint 1 (Portfolio Intelligence Activation)
    -- a real leadership change `executive_change_intelligence.py`
    already detected from earnings-call speaker/title metadata (Capability
    Expansion Sprint 10), disclosed in the most recent transcript Atlas
    has for this ticker. Never a new detector: this source only reads
    `ExecutiveChangeKnowledge.leadership_changes`, already computed as
    part of the same `InvestmentCaseComposition` every other Investment-
    Case-derived source here already builds."""

    MANAGEMENT_CREDIBILITY = "management_credibility"
    """Product Intelligence Sprint 1 -- management's own follow-through
    on prior commitments deteriorating (`CredibilityFindingKind.
    INCONSISTENT_FOLLOW_THROUGH`) or guidance being revised downward
    (`GUIDANCE_REVISED_DOWNWARD`), both already computed by
    `management_credibility_intelligence.py` (Capability Expansion
    Sprint 8) from real, disclosed commitment outcomes and guidance
    revisions -- never a new judgment about credibility, only reading
    that module's own existing, closed finding vocabulary. Re-evaluated
    fresh on every read from the current full evidence history, the
    same `PERSISTENT_CONDITION` shape `concentration_signal` already
    uses, since no persisted "prior credibility reading" exists
    anywhere in this codebase to compare against."""

    BUSINESS_QUALITY = "business_quality"
    """Product Intelligence Sprint 1 -- the business's own fundamentals
    weakening (`BusinessQualityFindingKind.WEAKENING_BUSINESS`), already
    computed by `business_quality_intelligence.py` (Capability Expansion
    Sprint 7) from real financial-statement trends -- never a new
    judgment about quality, only reading that module's own existing,
    closed finding vocabulary. `PERSISTENT_CONDITION`, the same
    reasoning as `MANAGEMENT_CREDIBILITY` above."""


@dataclass(frozen=True)
class AgendaItem:
    id: str
    priority: PriorityLevel
    kind: AgendaItemKind
    group: AgendaGroup
    source: AgendaSource
    headline: str
    reason: tuple[str, ...]
    """Every real contributing fact, from every signal that fired for
    this item -- not just the one that decided `kind`/`priority`
    (Deliverable 8: consolidated, not dropped). Unchanged by Fix Sprint
    4 -- the same strings, same order, as every prior sprint."""
    nature: SignalNature
    """Fix Sprint 4 -- the nature of the one signal that decided this
    item's own `headline`/`kind`/`priority` (the "winner", same signal
    `_item_for_ticker` already picks for those fields). Never guessed:
    every signal already carries its own `nature`, computed at the
    exact point in `engine.py` that already knows why it fired."""
    reason_nature: tuple[SignalNature, ...]
    """Parallel to `reason` -- same length, same order, one `nature`
    per contributing fact. A single item can honestly combine both
    kinds (e.g. a Decision Readiness change alongside an ongoing high-
    concentration finding); `nature` above alone would silently imply
    every reason is as fresh as the winning one, which is exactly the
    dishonesty this sprint exists to remove."""
    since: datetime | None
    """Fix Sprint 4 -- when the winning signal's own condition began,
    reusing already-computed data (`CaseConditionView.updated_at`/
    `AssumptionView.updated_at`) rather than inventing a new timestamp.
    Populated only for the two sources that actually carry one; `None`
    is an honest "Atlas does not track since-when for this," never a
    fabricated stand-in -- see `engine.py`'s own signal constructors."""
    ticker: str | None
    case_id: str | None
    portfolio_context: str | None
    generated_at: datetime


@dataclass(frozen=True)
class PortfolioSummary:
    """Deliverable 9 -- a concise, real-data-only opening summary.
    Every field is read verbatim from an existing endpoint; nothing
    here is computed by this package."""

    holdings_count: int
    critical_count: int
    high_count: int
    watchlist_opportunity_count: int
    cash_weight_percent: float | None
    concentration_level: str | None


@dataclass(frozen=True)
class DailyBriefAgenda:
    generated_at: datetime
    summary: PortfolioSummary
    items: tuple[AgendaItem, ...]
    """Already sorted: priority (Critical to Low), then group, then
    ticker -- deterministic and stable (Deliverable 17's own "tie
    handling")."""

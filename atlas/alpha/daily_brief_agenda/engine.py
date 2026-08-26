"""The Priority Engine itself -- pure, deterministic, no I/O.

Every function here is a total function of its arguments. Given the
exact same signals, `build_agenda` always returns the exact same
`DailyBriefAgenda` (Deliverable 17's own "priority ordering" /
"tie handling" tests hold this to account).

**One item per ticker (Deliverable 8, noise reduction).** A ticker can
have several real signals firing at once (a Case Condition satisfied,
the thesis weakened, Portfolio Fit declining). This engine never emits
one agenda item per signal -- it collects every signal that fired for
a ticker into one `_TickerSignal` bundle, picks the single
highest-priority signal to decide the item's own `kind`/`headline`
(deterministic tie-break: `_SOURCE_TIE_RANK`, most-specific-reasoning
source first), and folds every other real signal's own reason text
into that one item's `reason` tuple -- disclosed, never dropped.

**Two kinds are deliberately never engine-triggered.** `COMPARE_CANDIDATE`
and `AgendaGroup.DISCOVERY` have no independent signal of their own --
"you should compare two things" is not a fact Atlas observes, it is an
action offered *alongside* a real item (every Watchlist/Opportunity
item's own frontend action row already offers "Compare" -- see
`daily_brief_agenda`'s own API consumers). Manufacturing a synthetic
"time to compare" signal here would violate this sprint's own "do not
fabricate a new signal" rule.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.daily_brief_agenda.models import (
    AgendaGroup,
    AgendaItem,
    AgendaItemKind,
    AgendaSource,
    DailyBriefAgenda,
    PortfolioSummary,
    PriorityLevel,
    SignalNature,
)
from atlas.alpha.daily_brief_agenda.reason_facts import ReasonFact
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.investment_decision.models import DecisionAction, DecisionQualifierKind
from atlas.alpha.monitoring.engine import DAILY_BRIEF_EXCLUDED_CATEGORIES, HIGH_IMPORTANCE_CATEGORIES
from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.recommendation_conviction.models import RecommendationStability
from atlas.alpha.monitoring.models import MonitoringChangeCategory, MonitoringMateriality
from atlas.alpha.portfolio_fit.models import FitRating, FitTrend
from atlas.alpha.portfolio_intelligence.models import KeyFindingKind
from atlas.alpha.portfolio_status.models import AttentionCategory
from atlas.analysis_engine.investment_case_change import ThesisImpact
from atlas.alpha.investment_case.executive_change_intelligence import ExecutiveRoleCategory
from atlas.alpha.investment_case.management_credibility_intelligence import CredibilityFindingKind
from atlas.alpha.investment_case.business_quality_intelligence import BusinessQualityFindingKind

__all__ = ["Signal", "TickerContext", "build_agenda"]

_PRIORITY_RANK = {PriorityLevel.LOW: 0, PriorityLevel.NORMAL: 1, PriorityLevel.HIGH: 2, PriorityLevel.CRITICAL: 3}

# Lower rank wins a tie on priority -- the most specific, investor-
# authored reasoning source is preferred as the item's own headline
# over Atlas's own derived analysis, which is preferred over
# structural/administrative facts.
_SOURCE_TIE_RANK = {
    AgendaSource.CASE_CONDITION: 0,
    AgendaSource.ASSUMPTION: 1,
    AgendaSource.PORTFOLIO_FIT: 2,
    AgendaSource.CHANGE_INTELLIGENCE: 3,
    AgendaSource.MONITORING: 4,
    AgendaSource.DECISION_READINESS: 5,
    AgendaSource.INVESTMENT_DECISION: 6,
    AgendaSource.RECOMMENDATION_CONVICTION: 7,
    AgendaSource.DECISION_PATH: 8,
    AgendaSource.OPPORTUNITY_COST: 9,
    AgendaSource.DECISION_MEMORY: 10,
    AgendaSource.DECISION_EXPLANATION: 11,
    AgendaSource.DECISION_RELIABILITY: 12,
    AgendaSource.PORTFOLIO_DECISION: 13,
    AgendaSource.PORTFOLIO_STATUS: 14,
    AgendaSource.PORTFOLIO_INTELLIGENCE: 15,
    AgendaSource.EXECUTIVE_CHANGE: 16,
    AgendaSource.MANAGEMENT_CREDIBILITY: 17,
    AgendaSource.BUSINESS_QUALITY: 18,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------
# One `Signal` per real fact that fired -- never constructed for a
# non-event (e.g. a `supported` Assumption or an `active` Condition
# produces no `Signal` at all).
# ---------------------------------------------------------------------


class Signal:
    __slots__ = ("priority", "kind", "source", "reason", "nature", "since", "attention_category", "attention_count", "fact")

    def __init__(
        self,
        priority: PriorityLevel,
        kind: AgendaItemKind,
        source: AgendaSource,
        reason: str,
        nature: SignalNature,
        since: datetime | None = None,
        *,
        attention_category: AttentionCategory | None = None,
        attention_count: int | None = None,
        fact: ReasonFact | None = None,
    ) -> None:
        self.priority = priority
        self.kind = kind
        self.source = source
        self.reason = reason
        self.nature = nature
        self.since = since
        # Localization fix (Portfolio live-verification follow-up):
        # `reason` above stays a raw, English, backend-composed string
        # (unchanged, for any consumer reading it directly), but only
        # `workflow_signal` also populates these two so the frontend can
        # compose and translate its own version of the same sentence --
        # see `AgendaItem.attention_category`'s own docstring.
        self.attention_category = attention_category
        self.attention_count = attention_count
        # Implementation Sprint B1.1: the generalized successor to the
        # pair above -- see `AgendaItem.reason_facts`'s own docstring.
        # Populated by every signal source this sprint converts;
        # `None` everywhere else (unchanged behavior).
        self.fact = fact


# -- Workflow (ported verbatim from `derivePortfolioActions.ts`'s own
# `WORKFLOW_SEVERITY`, three tiers relabeled onto this engine's four --
# `highest`->CRITICAL, `high`->HIGH, `medium`->NORMAL) ------------------
_WORKFLOW_PRIORITY: dict[AttentionCategory, PriorityLevel] = {
    AttentionCategory.DECISION_WITHOUT_OUTCOME: PriorityLevel.CRITICAL,
    AttentionCategory.OUTCOME_WITHOUT_EXECUTION: PriorityLevel.CRITICAL,
    AttentionCategory.AWAITING_RECONCILIATION: PriorityLevel.CRITICAL,
    AttentionCategory.MISSING_CASE: PriorityLevel.HIGH,
    AttentionCategory.OBSERVATION_WITHOUT_DECISION: PriorityLevel.HIGH,
    AttentionCategory.VERY_OLD_CASE: PriorityLevel.NORMAL,
}


def workflow_signal(category: AttentionCategory, reason: str, *, count: int, fact: ReasonFact | None = None) -> Signal:
    """Fix Sprint 4: `PERSISTENT_CONDITION` -- `status_report
    .review_queue` (`service.py`'s own source 4) is membership in a
    structural gap that stays true until resolved (a Decision still
    lacking an Outcome, a very old Case), evaluated fresh on every
    read, never a "did this change since last time" check. No existing
    per-category timestamp is available to compose here beyond
    `VERY_OLD_CASE`'s own `age_days` (a portfolio-status-page-only
    field this package's own `ReviewQueueItem` does not carry through)
    -- see this sprint's own Final Report for why extending that is
    left to a future, narrower sprint rather than done here.

    `count` (`ReviewQueueItem.reason_count`, already computed by the
    caller) is threaded through alongside `category` purely so the
    frontend can compose a translated headline -- see `attention
    _category`/`attention_count` on `Signal`/`AgendaItem`."""
    return Signal(
        _WORKFLOW_PRIORITY[category],
        AgendaItemKind.REVIEW_PORTFOLIO_POSITION,
        AgendaSource.PORTFOLIO_STATUS,
        reason,
        SignalNature.PERSISTENT_CONDITION,
        attention_category=category,
        attention_count=count,
        fact=fact,
    )


def case_condition_signal(role: str, status: str, reason: str, since: datetime, *, fact: ReasonFact | None = None) -> Signal | None:
    """Fix Sprint 4: `PERSISTENT_CONDITION`, with a real `since` --
    `status == "satisfied"` is this Condition's own current state
    (re-evaluated fresh every call, no transition check), but
    `CaseConditionView.updated_at` (the timestamp of the event that
    made it `satisfied`) already exists and is threaded straight
    through from `service.py`'s own caller -- composed, not
    invented."""
    if status != "satisfied":
        return None
    priority = PriorityLevel.CRITICAL if role == "invalidation" else PriorityLevel.HIGH
    return Signal(
        priority,
        AgendaItemKind.EVALUATE_CASE_CONDITION,
        AgendaSource.CASE_CONDITION,
        reason,
        SignalNature.PERSISTENT_CONDITION,
        since=since,
        fact=fact,
    )


def assumption_signal(status: str, reason: str, since: datetime, *, fact: ReasonFact | None = None) -> Signal | None:
    """Fix Sprint 4: `PERSISTENT_CONDITION`, with a real `since` --
    identical reasoning to `case_condition_signal` above, using
    `AssumptionView.updated_at`."""
    if status == "invalidated":
        return Signal(
            PriorityLevel.CRITICAL,
            AgendaItemKind.REVISIT_ASSUMPTION,
            AgendaSource.ASSUMPTION,
            reason,
            SignalNature.PERSISTENT_CONDITION,
            since=since,
            fact=fact,
        )
    if status == "challenged":
        return Signal(
            PriorityLevel.HIGH,
            AgendaItemKind.REVISIT_ASSUMPTION,
            AgendaSource.ASSUMPTION,
            reason,
            SignalNature.PERSISTENT_CONDITION,
            since=since,
            fact=fact,
        )
    return None


def portfolio_fit_signal(overall: FitRating, trend: FitTrend, is_holding: bool, reason: str) -> Signal | None:
    """Fix Sprint 4: the one source whose real firing condition is
    genuinely `Mixed` at the source level -- resolved to exactly one
    `SignalNature` per branch below, never a third value. The first
    three branches fire on `overall` (Portfolio Fit's own *current*
    rating, re-evaluated fresh every call) -- `PERSISTENT_CONDITION`.
    The remaining branches fire on `trend`, which is not independently
    computed here: `FitTrend` is itself a direct relabeling of
    `ChangeIntelligence.thesis_impact` (see `atlas.alpha.monitoring
    .__init__`'s own documented reuse) -- genuine, already-real change
    information, so those branches are `CHANGE_EVENT`."""
    concern_kind = AgendaItemKind.REVIEW_PORTFOLIO_POSITION if is_holding else AgendaItemKind.REVIEW_WATCHLIST_CANDIDATE
    if overall is FitRating.POOR:
        return Signal(PriorityLevel.CRITICAL, concern_kind, AgendaSource.PORTFOLIO_FIT, reason, SignalNature.PERSISTENT_CONDITION)
    if overall is FitRating.WEAK and trend is FitTrend.DECLINING:
        return Signal(PriorityLevel.HIGH, concern_kind, AgendaSource.PORTFOLIO_FIT, reason, SignalNature.CHANGE_EVENT)
    if overall is FitRating.WEAK:
        return Signal(PriorityLevel.NORMAL, concern_kind, AgendaSource.PORTFOLIO_FIT, reason, SignalNature.PERSISTENT_CONDITION)
    if trend is FitTrend.DECLINING:
        return Signal(PriorityLevel.NORMAL, concern_kind, AgendaSource.PORTFOLIO_FIT, reason, SignalNature.CHANGE_EVENT)
    if not is_holding and overall in (FitRating.EXCELLENT, FitRating.GOOD) and trend is FitTrend.IMPROVING:
        return Signal(
            PriorityLevel.LOW, AgendaItemKind.PORTFOLIO_OPPORTUNITY, AgendaSource.PORTFOLIO_FIT, reason, SignalNature.CHANGE_EVENT
        )
    if trend is FitTrend.IMPROVING:
        return Signal(PriorityLevel.LOW, concern_kind, AgendaSource.PORTFOLIO_FIT, reason, SignalNature.CHANGE_EVENT)
    return None


_THESIS_IMPACT_PRIORITY = {
    ThesisImpact.WEAKENED: PriorityLevel.HIGH,
    ThesisImpact.MIXED: PriorityLevel.NORMAL,
    ThesisImpact.UNCHANGED: PriorityLevel.LOW,
    ThesisImpact.STRENGTHENED: PriorityLevel.LOW,
}


def change_intelligence_signal(thesis_impact: ThesisImpact, reason: str, *, affected_finding_count: int = 0) -> Signal:
    """`affected_finding_count` -- Atlas Intelligence Sprint 10
    (Evidence Graph & Dependency Understanding, Deliverable 10):
    "detta påverkar tre slutsatser." `0` (the default) appends nothing
    -- never a fabricated "this affects 0 conclusions" clause. The
    count itself is real, computed by `EvidenceGraphService`'s own
    dependency-graph traversal, never estimated here."""
    if affected_finding_count > 0:
        noun = "conclusion" if affected_finding_count == 1 else "conclusions"
        reason = f"{reason} This affects {affected_finding_count} other {noun}."
    return Signal(
        _THESIS_IMPACT_PRIORITY[thesis_impact],
        AgendaItemKind.REVIEW_INVESTMENT_CASE,
        AgendaSource.CHANGE_INTELLIGENCE,
        reason,
        SignalNature.CHANGE_EVENT,
    )


def monitoring_signal(
    category: MonitoringChangeCategory, materiality: MonitoringMateriality, is_holding: bool, reason: str
) -> Signal | None:
    """Atlas Intelligence Sprint 7 (Monitoring & Change Detection,
    Deliverable 10/11). `None` for a `MINOR` change (Deliverable 11's
    own noise suppression -- a change that exists but was not judged
    worth investor attention never becomes an agenda item) and for
    `category in DAILY_BRIEF_EXCLUDED_CATEGORIES` (Deliverable 12 --
    `MATERIAL_RISK_APPEARED`/`CASE_CONDITION_TRIGGERED` already have
    their own, non-duplicative Daily Brief signal; see
    `atlas.alpha.monitoring.engine`'s own module docstring)."""
    if materiality is not MonitoringMateriality.MATERIAL or category in DAILY_BRIEF_EXCLUDED_CATEGORIES:
        return None
    priority = PriorityLevel.HIGH if category in HIGH_IMPORTANCE_CATEGORIES else PriorityLevel.NORMAL
    kind = AgendaItemKind.REVIEW_PORTFOLIO_POSITION if is_holding else AgendaItemKind.REVIEW_WATCHLIST_CANDIDATE
    return Signal(priority, kind, AgendaSource.MONITORING, reason, SignalNature.CHANGE_EVENT)


_READINESS_CHANGE_PRIORITY: dict[DecisionReadinessStatus, PriorityLevel] = {
    DecisionReadinessStatus.BLOCKED: PriorityLevel.HIGH,
    DecisionReadinessStatus.READY: PriorityLevel.NORMAL,
    DecisionReadinessStatus.ALMOST_READY: PriorityLevel.NORMAL,
    DecisionReadinessStatus.WAITING: PriorityLevel.LOW,
    DecisionReadinessStatus.UNAVAILABLE: PriorityLevel.LOW,
    DecisionReadinessStatus.UNKNOWN: PriorityLevel.LOW,
}
"""A fixed, declared priority per *new* status -- becoming `BLOCKED` is
the one readiness change genuinely worth elevated attention; becoming
`READY`/`ALMOST_READY` is real, positive news at ordinary priority;
every other transition is a normal, unalarming step, never inflated."""


def decision_readiness_signal(current_status: DecisionReadinessStatus, reason: str) -> Signal:
    """Atlas Intelligence Sprint 11 (Decision Readiness & Decision
    Eligibility, Deliverable 10). Always fires -- the caller
    (`service.py`'s own loop) only calls this when `atlas.alpha
    .decision_readiness.engine.detect_readiness_change` already found a
    real transition; there is no "minor, suppress" tier here the way
    `monitoring_signal` has, since a status *change* is inherently the
    material fact, not a graded one."""
    return Signal(
        _READINESS_CHANGE_PRIORITY[current_status],
        AgendaItemKind.REVIEW_INVESTMENT_CASE,
        AgendaSource.DECISION_READINESS,
        reason,
        SignalNature.CHANGE_EVENT,
    )


_ACTION_CHANGE_PRIORITY: dict[DecisionAction, PriorityLevel] = {
    DecisionAction.BUY: PriorityLevel.NORMAL,
    DecisionAction.ADD: PriorityLevel.NORMAL,
    DecisionAction.REDUCE: PriorityLevel.NORMAL,
    DecisionAction.EXIT: PriorityLevel.NORMAL,
    DecisionAction.HOLD: PriorityLevel.LOW,
    DecisionAction.WAIT: PriorityLevel.LOW,
    DecisionAction.NO_DECISION: PriorityLevel.LOW,
}
"""A fixed, declared priority per *new* action -- every actionable
transition (Buy/Add/Reduce/Exit) is real, ordinary-priority news;
settling into Hold/Wait/No decision is never alarming. Becoming
`decision_blocked` overrides this to `HIGH` below, mirroring
`_READINESS_CHANGE_PRIORITY`'s own "one elevated case, everything else
ordinary" shape."""


def investment_decision_signal(current_action: DecisionAction, current_qualifier_kinds: tuple[DecisionQualifierKind, ...], reason: str) -> Signal:
    """Atlas Decision Layer Sprint 1 (Investment Decision Synthesis,
    Deliverable 10). Always fires -- the caller (`service.py`'s own
    loop) only calls this when `atlas.alpha.investment_decision.engine
    .detect_decision_change` already found a real transition (action or
    qualifier set)."""
    priority = (
        PriorityLevel.HIGH
        if DecisionQualifierKind.DECISION_BLOCKED in current_qualifier_kinds
        else _ACTION_CHANGE_PRIORITY[current_action]
    )
    return Signal(priority, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.INVESTMENT_DECISION, reason, SignalNature.CHANGE_EVENT)


def recommendation_conviction_signal(current_stability: RecommendationStability, reason: str) -> Signal:
    """Atlas Decision Layer Sprint 2 (Recommendation Strength &
    Conviction, Deliverable 10). Always fires -- the caller
    (`service.py`'s own loop) only calls this when `atlas.alpha
    .recommendation_conviction.engine.detect_conviction_change` already
    found a real transition (strength or stability). Becoming
    `OPERATIONALLY_BLOCKED` is the one elevated case, the same
    "one elevated case, everything else ordinary" shape
    `_READINESS_CHANGE_PRIORITY`/`_ACTION_CHANGE_PRIORITY` above
    already establish -- a real strength change alone (e.g. Strong ->
    Weak) is genuine, ordinary-priority news, never inflated."""
    priority = PriorityLevel.HIGH if current_stability is RecommendationStability.OPERATIONALLY_BLOCKED else PriorityLevel.NORMAL
    return Signal(
        priority, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.RECOMMENDATION_CONVICTION, reason, SignalNature.CHANGE_EVENT
    )


def decision_path_signal(current_final_reachable_state: FinalReachableState, reason: str) -> Signal:
    """Atlas Decision Layer Sprint 3 (Decision Path & Required
    Progress, Deliverable 10). Always fires -- the caller (`service.py`'s
    own loop) only calls this when `atlas.alpha.decision_path.engine
    .detect_decision_path_change` already found a real transition.
    Becoming `NOT_REACHABLE` (no real path forward exists today) is the
    one elevated case, the same "one elevated case, everything else
    ordinary" shape every prior signal in this module already
    establishes; every other real transition (a path shortening, a
    dependency resolving) is genuine, ordinary-priority news."""
    priority = PriorityLevel.HIGH if current_final_reachable_state is FinalReachableState.NOT_REACHABLE else PriorityLevel.NORMAL
    return Signal(priority, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.DECISION_PATH, reason, SignalNature.CHANGE_EVENT)


def opportunity_cost_signal(reason: str) -> Signal:
    """Atlas Decision Layer Sprint 4 (Decision Alternatives &
    Opportunity Cost, Deliverable 10). Always fires -- the caller
    (`service.py`'s own loop) only calls this when `atlas.alpha
    .opportunity_cost.engine.detect_opportunity_cost_change` already
    found a real transition. Deliberately never elevated: a new/lost/
    strengthened/weakened alternative, or waiting becoming preferable,
    is genuine, informational news about what the decision competes
    against -- never itself an alarm the way an operational block or
    an unreachable path is for the decision's own sources above."""
    return Signal(
        PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.OPPORTUNITY_COST, reason, SignalNature.CHANGE_EVENT
    )


def decision_memory_signal(reason: str) -> Signal:
    """Atlas Decision Layer Sprint 5 (Decision Memory, Deliverable 10).
    Always fires -- the caller (`service.py`'s own loop) only calls
    this when `atlas.alpha.decision_memory.service.DecisionMemoryService
    .change_for_case` already confirms a *new*, non-baseline snapshot
    was durably appended this call. Deliberately never elevated: this
    source announces that a real change was successfully recorded to
    history, a fact about durability, never itself an alarm -- the
    underlying content changes (recommendation, conviction, blockers,
    path, alternatives) already have their own sources above for
    that, and `_ensure`'s own per-ticker consolidation folds this
    source's own reason into the same item, never a duplicate one."""
    return Signal(
        PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.DECISION_MEMORY, reason, SignalNature.CHANGE_EVENT
    )


def decision_explanation_signal(reason: str) -> Signal:
    """Atlas Decision Layer Sprint 6 (Decision Explanation &
    Traceability, Deliverable 10). Always fires -- the caller
    (`service.py`'s own loop) only calls this when `atlas.alpha
    .decision_explanation.engine.detect_decision_explanation_change`
    already found a real transition. Deliberately never elevated: a
    new supporting finding, a resolved/new blocker, or conviction that
    strengthened/weakened is genuine, informational news about *why*
    the decision stands as it does -- the underlying decision/
    conviction/path changes already have their own sources above for
    the alarm-worthy content itself; this source only ever announces
    that the explanation for it moved."""
    return Signal(
        PriorityLevel.NORMAL,
        AgendaItemKind.REVIEW_INVESTMENT_CASE,
        AgendaSource.DECISION_EXPLANATION,
        reason,
        SignalNature.CHANGE_EVENT,
    )


def decision_reliability_signal(reason: str) -> Signal:
    """Atlas Decision Layer Sprint 7 (Decision Reliability, Deliverable
    11). Always fires -- the caller (`service.py`'s own loop) only
    calls this when `atlas.alpha.decision_reliability.engine
    .detect_reliability_change` already found a real transition.
    Deliberately never elevated: reliability improving/weakening,
    resolving/newly-arising limitations is genuine, informational news
    about how much trust to place in the decision -- the underlying
    facts it reflects (Coverage/Confidence, Evidence Quality, Decision
    Readiness) already have their own sources above for the alarm-
    worthy content itself; this source only ever announces that the
    reliability reading built from them moved."""
    return Signal(
        PriorityLevel.NORMAL,
        AgendaItemKind.REVIEW_INVESTMENT_CASE,
        AgendaSource.DECISION_RELIABILITY,
        reason,
        SignalNature.CHANGE_EVENT,
    )


def portfolio_decision_signal(reason: str) -> Signal:
    """Atlas Decision Layer Sprint 8 (Portfolio Decision Synthesis,
    Deliverable 11). Always fires -- the caller (`service.py`'s own
    loop) only calls this when `atlas.alpha.portfolio_decision.engine
    .detect_portfolio_decision_change` already found a real
    transition. Deliberately never elevated: what a decision means for
    the portfolio changing -- capital competition, a portfolio
    conflict resolving, a real opportunity appearing -- is genuine,
    informational news about the decision's own place inside the
    portfolio, not a new alarm-worthy fact of its own; the underlying
    decision/reliability facts it composes already have their own
    sources above for that."""
    return Signal(
        PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.PORTFOLIO_DECISION, reason, SignalNature.CHANGE_EVENT
    )


_CONCENTRATION_PRIORITY = {
    KeyFindingKind.HIGH_CONCENTRATION: PriorityLevel.HIGH,
    KeyFindingKind.ELEVATED_CONCENTRATION: PriorityLevel.NORMAL,
}


def concentration_signal(kind: KeyFindingKind, reason: str, *, fact: ReasonFact | None = None) -> Signal | None:
    """Fix Sprint 4: `PERSISTENT_CONDITION` -- a position's own share of
    the portfolio, recomputed fresh from current weights on every read,
    with no persisted prior-weight history anywhere in this codebase to
    compare against (confirmed by audit: no "since when has this
    holding been concentrated" timestamp exists to compose). Honestly
    left without a `since` rather than inventing one."""
    priority = _CONCENTRATION_PRIORITY.get(kind)
    if priority is None:
        return None
    return Signal(
        priority, AgendaItemKind.PORTFOLIO_RISK, AgendaSource.PORTFOLIO_INTELLIGENCE, reason, SignalNature.PERSISTENT_CONDITION, fact=fact
    )


def evidence_gap_signal(reason: str, *, fact: ReasonFact | None = None) -> Signal:
    """Product Sprint 8 (Portfolio Excellence, Deliverable 4 -- Unify
    Attention Surfaces): before this, a missing-evidence gap
    (`PortfolioIntelligenceReport.missing_evidence`) was the one signal
    `derivePortfolioActions.ts`'s "Needs Your Attention" surfaced (at its
    "high" tier, same as `MISSING_CASE`/`OBSERVATION_WITHOUT_DECISION")
    that this engine had no equivalent for -- every other frontend
    "Needs Your Attention" signal already had a real counterpart here.
    Matches that same tier (`PriorityLevel.HIGH`); reuses
    `REVIEW_PORTFOLIO_POSITION` (the same kind `workflow_signal` already
    uses -- a missing-evidence gap is resolved the same way a workflow
    item is, by reviewing the position) and `PORTFOLIO_INTELLIGENCE`
    (the source that already owns `missing_evidence` on
    `PortfolioIntelligenceReport`) -- no new `AgendaItemKind` or
    `AgendaSource` member."""
    return Signal(
        PriorityLevel.HIGH,
        AgendaItemKind.REVIEW_PORTFOLIO_POSITION,
        AgendaSource.PORTFOLIO_INTELLIGENCE,
        reason,
        SignalNature.PERSISTENT_CONDITION,
        fact=fact,
    )


def portfolio_level_signal(priority: PriorityLevel, reason: str, *, fact: ReasonFact | None = None) -> Signal:
    """Fix Sprint 4: `PERSISTENT_CONDITION` -- large unallocated capital
    is a current-state fact about today's portfolio composition, not a
    detected transition; no existing "since when has cash sat
    unallocated" timestamp exists to compose."""
    return Signal(
        priority, AgendaItemKind.PORTFOLIO_RISK, AgendaSource.PORTFOLIO_INTELLIGENCE, reason, SignalNature.PERSISTENT_CONDITION, fact=fact
    )


# -- Product Intelligence Sprint 1 (Portfolio Intelligence Activation) --
# three new sources, each reading an Investment Case capability that was
# already computed as part of the same `InvestmentCaseComposition` every
# `CHANGE_INTELLIGENCE`/`DECISION_READINESS`/etc. source above already
# builds -- never a new detector, never new investment reasoning, only a
# fixed, declared priority for an already-closed finding vocabulary, the
# identical shape `_ACTION_CHANGE_PRIORITY`/`_READINESS_CHANGE_PRIORITY`
# above already establish.

_EXECUTIVE_CHANGE_PRIORITY: dict[ExecutiveRoleCategory, PriorityLevel] = {
    ExecutiveRoleCategory.CEO: PriorityLevel.HIGH,
    ExecutiveRoleCategory.CFO: PriorityLevel.NORMAL,
}
"""A CEO change is real, well-known, market-moving news; a CFO change is
real but ordinarily less so. Every other role (Chair, COO, CTO, board
directors, ...) is genuine news but not elevated -- `PriorityLevel.LOW`,
the `.get(..., LOW)` default below."""


def executive_change_signal(
    role_category: ExecutiveRoleCategory, reason: str, since: datetime | None, *, fact: ReasonFact | None = None
) -> Signal:
    """Fires only for a `LeadershipChangeEvent` disclosed in the most
    recent earnings-call transcript Atlas has for this ticker (the
    caller's own responsibility -- see `service.py`'s own source 17) --
    a real, mechanical "is this still current news" bound reusing
    already-real transcript-ordering data, never a persisted "since
    last agenda run" comparison this codebase has nowhere to store.
    `since` is the event's own real `effective_date`/`observed_date`,
    threaded through, never invented (mirrors `case_condition_signal`'s
    own "a real `since`, already exists, composed not invented")."""
    return Signal(
        _EXECUTIVE_CHANGE_PRIORITY.get(role_category, PriorityLevel.LOW),
        AgendaItemKind.REVIEW_INVESTMENT_CASE,
        AgendaSource.EXECUTIVE_CHANGE,
        reason,
        SignalNature.CHANGE_EVENT,
        since=since,
        fact=fact,
    )


def management_credibility_signal(kind: CredibilityFindingKind, reason: str, *, fact: ReasonFact | None = None) -> Signal | None:
    """`None` for every finding that is not itself a deterioration --
    `CONSISTENT_FOLLOW_THROUGH`/`MIXED_FOLLOW_THROUGH`/`COMMUNICATION_
    REMAINED_CONSISTENT`/`COMMUNICATION_SHIFTED`/`INSUFFICIENT_HISTORY`
    are real, disclosed findings too, but none of them is the
    "credibility deterioration" this source exists for -- surfacing a
    neutral or positive finding as an attention item would be exactly
    the "no ambiguous warnings" instruction this sprint's own Phase 5
    forbids."""
    if kind is CredibilityFindingKind.INCONSISTENT_FOLLOW_THROUGH:
        return Signal(
            PriorityLevel.HIGH, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.MANAGEMENT_CREDIBILITY, reason, SignalNature.PERSISTENT_CONDITION, fact=fact
        )
    if kind is CredibilityFindingKind.GUIDANCE_REVISED_DOWNWARD:
        return Signal(
            PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.MANAGEMENT_CREDIBILITY, reason, SignalNature.PERSISTENT_CONDITION, fact=fact
        )
    return None


def business_quality_signal(kind: BusinessQualityFindingKind, reason: str, *, fact: ReasonFact | None = None) -> Signal | None:
    """`None` for every finding except `WEAKENING_BUSINESS` -- the one
    member this sprint's own Phase 3 names ("business quality
    deterioration"); every other member (`CONSISTENT_VALUE_CREATION`,
    `STRENGTHENING_BUSINESS`, `DURABLE_GROWTH`, ...) is real, disclosed,
    and genuinely positive or neutral news, never surfaced as an
    attention item."""
    if kind is BusinessQualityFindingKind.WEAKENING_BUSINESS:
        return Signal(
            PriorityLevel.HIGH, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.BUSINESS_QUALITY, reason, SignalNature.PERSISTENT_CONDITION, fact=fact
        )
    return None


# ---------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------


class TickerContext:
    """What the service already knows about one ticker before handing
    it to the engine -- purely descriptive, carries no logic."""

    __slots__ = ("ticker", "case_id", "is_holding", "portfolio_context")

    def __init__(self, ticker: str, case_id: str, is_holding: bool, portfolio_context: str | None) -> None:
        self.ticker = ticker
        self.case_id = case_id
        self.is_holding = is_holding
        self.portfolio_context = portfolio_context


def _item_for_ticker(context: TickerContext, signals: list[Signal], now: datetime) -> AgendaItem | None:
    if not signals:
        return None
    winner = max(signals, key=lambda s: (_PRIORITY_RANK[s.priority], -_SOURCE_TIE_RANK[s.source]))
    group = AgendaGroup.PORTFOLIO if context.is_holding else AgendaGroup.WATCHLIST
    # Every real reason, winner first, then the rest in the same
    # specificity order -- never silently dropped (Deliverable 8).
    ordered = sorted(signals, key=lambda s: _SOURCE_TIE_RANK[s.source])
    reasons = tuple(dict.fromkeys(s.reason for s in ordered))
    # Fix Sprint 4: one `SignalNature` per `reasons` entry, same order,
    # same dedup-by-text -- the first signal to contribute a given
    # reason string decides that reason's own nature (matching
    # `dict.fromkeys`'s own "first occurrence wins" rule above, so the
    # two tuples can never disagree about which signal a given reason
    # text came from).
    nature_by_reason: dict[str, SignalNature] = {}
    fact_by_reason: dict[str, ReasonFact | None] = {}
    for signal in ordered:
        nature_by_reason.setdefault(signal.reason, signal.nature)
        if signal.reason not in fact_by_reason:
            fact_by_reason[signal.reason] = signal.fact
    reason_nature = tuple(nature_by_reason[text] for text in reasons)
    reason_facts = tuple(fact_by_reason[text] for text in reasons)
    return AgendaItem(
        id=f"{winner.kind.value}:{context.ticker}",
        priority=winner.priority,
        kind=winner.kind,
        group=group,
        source=winner.source,
        headline=winner.reason,
        reason=reasons,
        nature=winner.nature,
        reason_nature=reason_nature,
        since=winner.since,
        ticker=context.ticker,
        case_id=context.case_id,
        portfolio_context=context.portfolio_context,
        generated_at=now,
        attention_category=winner.attention_category,
        attention_count=winner.attention_count,
        reason_facts=reason_facts,
    )


def build_agenda(
    ticker_signals: dict[str, tuple[TickerContext, list[Signal]]],
    portfolio_level_signals: list[Signal],
    *,
    holdings_count: int,
    cash_weight_percent: float | None,
    concentration_level: str | None,
    now: datetime | None = None,
) -> DailyBriefAgenda:
    """`ticker_signals` is keyed by ticker; `portfolio_level_signals`
    covers the no-ticker findings (e.g. large unallocated cash).
    `PortfolioSummary`'s own Critical/High/Opportunity counts are
    derived from the final, already-consolidated item list itself
    (never passed in) -- they must always agree with what `items`
    actually contains, by construction, not by two call sites staying
    in sync."""
    resolved_now = now or _utc_now()
    items: list[AgendaItem] = []

    for context, signals in ticker_signals.values():
        item = _item_for_ticker(context, signals, resolved_now)
        if item is not None:
            items.append(item)

    for index, signal in enumerate(portfolio_level_signals):
        items.append(
            AgendaItem(
                id=f"portfolio-level:{index}",
                priority=signal.priority,
                kind=signal.kind,
                group=AgendaGroup.PORTFOLIO,
                source=signal.source,
                headline=signal.reason,
                reason=(signal.reason,),
                nature=signal.nature,
                reason_nature=(signal.nature,),
                since=signal.since,
                ticker=None,
                case_id=None,
                portfolio_context=None,
                generated_at=resolved_now,
                attention_category=signal.attention_category,
                attention_count=signal.attention_count,
                reason_facts=(signal.fact,),
            )
        )

    items.sort(key=lambda i: (-_PRIORITY_RANK[i.priority], i.group.value, i.ticker or ""))

    summary = PortfolioSummary(
        holdings_count=holdings_count,
        critical_count=sum(1 for i in items if i.priority is PriorityLevel.CRITICAL),
        high_count=sum(1 for i in items if i.priority is PriorityLevel.HIGH),
        watchlist_opportunity_count=sum(1 for i in items if i.kind is AgendaItemKind.PORTFOLIO_OPPORTUNITY),
        cash_weight_percent=cash_weight_percent,
        concentration_level=concentration_level,
    )
    return DailyBriefAgenda(generated_at=resolved_now, summary=summary, items=tuple(items))

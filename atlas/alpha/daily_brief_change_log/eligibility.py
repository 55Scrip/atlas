"""Daily Brief 2.0, Phase 2/3 -- the one explicit eligibility rule this
sprint's own product doctrine requires: "a change should qualify only
if it materially affects the recommendation, investment rating,
portfolio rating, expected upside, risk, horizon, confidence/evidence
interpretation, core thesis, or a critical assumption."

This module is the ONE place that rule is encoded, built entirely from
a fresh, first-principles read of the real `daily_brief_agenda` engine
(all 22 signal producers, every `ReasonCode` each one can emit) rather
than from any prior sprint's own summary. Every source classified A
(decision-relevant) below is A because the underlying engine already
computes a real semantic transition or a genuinely case-level finding
-- never because of its name alone. Every source left out is left out
for a stated reason, not by omission.

Deliberately excluded, and why (bucket letters per this sprint's own
brief):
- WORKFLOW_GAP (bucket D) -- Atlas's own decision-hygiene bookkeeping
  (a Decision missing an Outcome, a Case awaiting reconciliation).
  Never an investment fact. Same discipline `bookkeepingFilter.ts`
  already established for Portfolio/Daily Brief 1.0's own Critical
  count (Atlas UX Phase 7B) -- this sprint extends it to full
  exclusion from the change log, not merely demotion.
- MISSING_EVIDENCE, CONCENTRATION, WORKFLOW_GAP's siblings (bucket D/C)
  -- Atlas's own epistemic/operational state, or a real but non-
  comparable portfolio fact (concentration has no persisted prior-
  weight history anywhere in this codebase to diff against -- see
  `portfolio_intelligence`'s own `concentration_signal` docstring).
- EXECUTIVE_CHANGE (bucket C, this sprint's own literal example) --
  real, but no field anywhere links a leadership change to thesis,
  risk, conviction, or recommendation. Classifying it as material
  would be inventing a judgment the backend does not make.
- DECISION_READINESS_TRANSITION, DECISION_PATH_TRANSITION,
  DECISION_RELIABILITY_TRANSITION (bucket D) -- these describe whether
  Atlas has enough basis to decide, and how trustworthy Atlas's own
  process is. Internal readiness/reliability bookkeeping, exactly the
  "Decision Reliability" this sprint's own Phase 11 names as language
  that must never reach the user.
- Decision Memory, Decision Explanation, Opportunity Cost (no
  ReasonFact at all -- see the sprint's own backend audit) -- Decision
  Memory in particular is a verbatim duplicate of Investment Decision's
  own transition, re-announced as "this was recorded to history";
  Investment Decision already covers the same real fact once.
- PORTFOLIO_FIT_VERDICT -- carries only the *current* rating, never a
  previous one (`FitTrend` is a direct relabel of Change Intelligence's
  own `thesis_impact`, not an independent signal), so it can only ever
  restate a current state, never report a change.
- CASE_CONDITION_STATUS -- included, but narrowly: the underlying
  `CaseConditionRole` (investor-authored "invalidation" vs merely
  "monitoring") is dropped before it reaches the agenda item; the
  item's own `priority` is the only surviving proxy (CRITICAL iff
  `role == "invalidation"`, per `case_condition_signal`), so this
  module gates on that instead of inventing a new backend field.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.daily_brief_agenda.models import AgendaItem, DailyBriefAgenda, PriorityLevel
from atlas.alpha.daily_brief_agenda.reason_facts import ReasonCode, ReasonFact

__all__ = ["EligibleChange", "extract_eligible_changes"]


@dataclass(frozen=True)
class EligibleChange:
    """One eligible fact, extracted but not yet persisted -- `store.py`
    assigns `id`/`detected_at`/`seen_at`. Never itself a Daily Brief
    presentation object; `headline` is the one already-real sentence
    kept as an honest fallback, not a synthesized one."""

    ticker: str
    case_id: str | None
    reason_code: str
    value: str | None
    secondary_value: str | None
    label: str | None
    headline: str
    priority_rank: int
    """Lower is more severe -- see `_REASON_CODE_SEVERITY` below. Real,
    fixed, disclosed ordering (the recommendation itself outranks a
    conviction-only shift, which outranks a business-quality finding),
    never a numeric materiality score. Used only to pick the one
    primary fact when a single ticker has more than one eligible
    change (Phase 10, "one company = one message"), never to decide
    eligibility itself."""


# A ReasonCode maps to `True` (always eligible once present -- the
# upstream engine has already restricted when it fires), a set of
# eligible `value`s (eligible only for those specific transitions), or
# is absent entirely (never eligible). No numeric threshold anywhere:
# every gate here is a real, existing categorical value the backend
# already computes, per this sprint's own Phase 3 instruction to
# "prefer semantic state transitions" over invented numbers.
_ALWAYS_ELIGIBLE = frozenset(
    {
        # The recommendation itself changed (Buy/Add/Hold/Reduce/Exit/
        # Wait) -- the single most decision-relevant fact in the file.
        ReasonCode.INVESTMENT_DECISION_TRANSITION,
        # How strongly Atlas holds its own recommendation changed.
        ReasonCode.RECOMMENDATION_CONVICTION_TRANSITION,
        # What this position means for the portfolio as a whole changed.
        ReasonCode.PORTFOLIO_DECISION_TRANSITION,
        # An investor-authored critical assumption was challenged or
        # invalidated -- `assumption_signal` only ever fires for those
        # two statuses (never "supported"), so presence alone qualifies.
        ReasonCode.ASSUMPTION_STATUS,
        # Real, case-level business-quality deterioration -- the one
        # `BusinessQualityFindingKind` this source ever reports.
        ReasonCode.BUSINESS_QUALITY,
        # Management's own prior commitments went unfulfilled, or
        # guidance was walked back -- the only two finding kinds this
        # source ever reports; both are case-relevant by construction.
        ReasonCode.MANAGEMENT_CREDIBILITY,
    }
)

_ELIGIBLE_VALUES: dict[ReasonCode, frozenset[str]] = {
    # Change Intelligence's own aggregate thesis verdict -- eligible
    # whenever it says something actually moved; "unchanged" is the
    # source's own honest "nothing to report" state, not a change.
    ReasonCode.CHANGE_INTELLIGENCE_THESIS_IMPACT: frozenset({"strengthened", "weakened", "mixed"}),
    # Monitoring's own change taxonomy: only the three categories that
    # describe the investment view itself (Atlas's Stance) qualify.
    # Every other reachable category (coverage/confidence/evidence
    # freshness) is a statement about Atlas's own epistemic state, not
    # the investment case -- bucket D, deliberately excluded.
    ReasonCode.MONITORING_CHANGE: frozenset({"stance_strengthened", "stance_weakened", "stance_became_uncertain"}),
}


# Fixed, disclosed severity order -- most decision-relevant first.
# The recommendation transition itself outranks everything else, since
# it is the one fact that most directly answers "what should I do";
# an invalidated assumption/critical-condition is next, since it
# threatens the thesis outright; conviction/portfolio-level shifts and
# the aggregate thesis verdict follow; company-quality findings and
# Monitoring's own stance read are last among eligible facts, since
# they are real but one step removed from the recommendation itself.
_REASON_CODE_SEVERITY: dict[ReasonCode, int] = {
    ReasonCode.INVESTMENT_DECISION_TRANSITION: 0,
    ReasonCode.CASE_CONDITION_STATUS: 1,
    ReasonCode.ASSUMPTION_STATUS: 1,
    ReasonCode.RECOMMENDATION_CONVICTION_TRANSITION: 2,
    ReasonCode.PORTFOLIO_DECISION_TRANSITION: 2,
    ReasonCode.CHANGE_INTELLIGENCE_THESIS_IMPACT: 3,
    ReasonCode.BUSINESS_QUALITY: 4,
    ReasonCode.MANAGEMENT_CREDIBILITY: 4,
    ReasonCode.MONITORING_CHANGE: 5,
}


def _is_case_condition_eligible(item: AgendaItem) -> bool:
    """`CaseConditionRole` ("invalidation" vs "monitoring") is dropped
    before it reaches `AgendaItem` -- `priority` is the only surviving
    proxy, since `case_condition_signal` sets CRITICAL iff
    `role == "invalidation"` and HIGH otherwise (`engine.py`). A
    monitoring-role condition being satisfied is a real observation,
    but not by itself a case-changing one -- this sprint does not
    invent a new backend field to recover `role` when the item's own
    existing priority already discloses the fact honestly."""
    return item.priority is PriorityLevel.CRITICAL


def _is_fact_eligible(item: AgendaItem, fact: ReasonFact) -> bool:
    if fact.code is ReasonCode.CASE_CONDITION_STATUS:
        return _is_case_condition_eligible(item)
    if fact.code in _ALWAYS_ELIGIBLE:
        return True
    eligible_values = _ELIGIBLE_VALUES.get(fact.code)
    if eligible_values is None:
        return False
    return fact.value in eligible_values


def extract_eligible_changes(agenda: DailyBriefAgenda) -> tuple[EligibleChange, ...]:
    """Scans every contributing fact on every item -- not only the
    "winning" signal that decided the item's own `headline`/`source`.
    This matters: `_item_for_ticker`'s own tie-break
    (`_SOURCE_TIE_RANK`) can let a Portfolio Fit restatement or a
    Case Condition win the headline over a real Investment Decision
    transition for the same ticker, folding the real change into
    `reason_facts` without promoting it. Reading the whole bundle,
    not just the winner, is what makes this module honest regardless
    of which signal happened to win that tie-break.

    A single ticker can produce more than one `EligibleChange` in one
    call (e.g. both a recommendation change and an assumption
    invalidation) -- `store.py::record_if_new` is the layer that
    decides whether each is genuinely new; grouping down to "one
    company, one message" (Phase 10) happens at read time
    (`store.py::list_recent`), never by discarding real facts here."""
    changes: list[EligibleChange] = []
    for item in agenda.items:
        if item.ticker is None:
            continue
        for fact in item.reason_facts:
            if fact is None or not _is_fact_eligible(item, fact):
                continue
            changes.append(
                EligibleChange(
                    ticker=item.ticker,
                    case_id=item.case_id,
                    reason_code=fact.code.value,
                    value=fact.value,
                    secondary_value=fact.secondary_value,
                    label=fact.label,
                    headline=item.headline,
                    priority_rank=_REASON_CODE_SEVERITY[fact.code],
                )
            )
    return tuple(changes)

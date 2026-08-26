"""Semantic reason payloads (Implementation Sprints B1.1/B1.2: Backend
Language Cleanup / Engine Reason Localization Contract) -- the
permanent boundary these sprints establish: **the backend produces
meaning, the frontend produces language.**

`Signal.reason`/`AgendaItem.reason` (a plain `str`) predates this
module and is *not* removed here -- every source in `engine.py` still
constructs one, and it remains the wire format for any consumer that
has not adopted `ReasonFact` yet (internal logging, the raw fallback
text below). What this module adds is a second, additive, structured
channel: a closed `ReasonCode` naming *what kind* of fact fired, plus
the real, already-computed data (a closed enum's own `.value`, a
count, a real proper noun) needed to translate it -- never a rendered
sentence, never an English label, never a raw enum name concatenated
into English prose.

**Scope -- what B1.1 converted, what B1.2 adds, what stays deferred.**
Every source in `daily_brief_agenda` was audited twice (B1.1's own
Final Report Phase 1, then re-verified rather than assumed for B1.2 --
see that sprint's own Final Report). Three kinds of source exist:

1. Sources whose reason text is built *here*, in this package, from a
   closed, local vocabulary (`AttentionCategory`, `EvidenceGapKind`,
   `KeyFindingKind`, `LeadershipChangeEventType`/`ExecutiveRoleCategory`,
   `CredibilityFindingKind`, `BusinessQualityFindingKind`, Case
   Condition/Assumption status). Converted in B1.1.
2. Sources whose reason text is built from *another* engine's own
   `*Change` dataclass, but where that dataclass's own primary fact is
   itself already a closed enum transition (`previous_X`/`current_X`,
   both real, already-typed enum members -- never re-derived here):
   Change Intelligence (`ThesisImpact`), Portfolio Fit (a new,
   dedicated `FitVerdictReasonCode` -- see `atlas.alpha.portfolio_fit
   .models`, B1.2's own Phase 3 addition, since `_overall_fit`'s 8
   branches previously produced text only, no code), Monitoring
   (`MonitoringChangeCategory`, already a real field on
   `MonitoringChange`), Decision Readiness (`DecisionReadinessStatus`),
   Investment Decision (`DecisionAction`), Recommendation Conviction
   (`ConvictionStrength`), Decision Path (`FinalReachableState`),
   Decision Reliability (`ReliabilityLevel`), Portfolio Decision
   (`PortfolioDecisionCategory`). Converted in B1.2 -- but only each
   source's own *primary transition*, not the secondary "Resolved:
   .../New: ..." clauses that list individual blocker/reference-id
   labels (see 3 below).
3. Everything else: the itemized "Resolved: X, Y. New: Z." clauses on
   every source in (2) above (each draws from a different, small,
   per-engine vocabulary of blocker kinds/reference ids -- cataloguing
   and translating all of them is a distinct, larger follow-up, not
   attempted here), Decision Memory/Decision Explanation/Opportunity
   Cost (no single dominant closed-enum transition the way (2)'s
   sources have -- each is dominated by exactly these same itemized
   lists), and Portfolio Fit's own per-dimension reasoning (`_business
   _fit`/`_valuation_fit`/`_risk_fit`'s individual sentences -- only
   the *overall* verdict was converted). Left as fixed English text,
   unchanged; see B1.2's own Final Report, "Remaining implementation
   leaks" / Phase 10, for the precise, current list.

**Never a rendered sentence.** A `ReasonFact` is data, not prose --
`value`/`secondary_value` are always a closed enum's own `.value`
string (frontend translates via its own key map, the same convention
`api/schemas.py` already documents for every other enum on the wire).
`label` is the one deliberate exception: a real, already-real proper
noun (a person's name, an investor-authored predicate/assumption
statement) that was never English-language "system speak" in the
first place and must never be translated -- passed through verbatim,
the same way a ticker already is.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["ReasonCode", "ReasonFact"]


class ReasonCode(str, Enum):
    """One member per distinct semantic fact shape this sprint converts
    -- never one per literal sentence. Each maps to exactly one
    canonical frontend translation (Phase 6: "the same reason must
    never appear differently depending on where it is rendered")."""

    WORKFLOW_GAP = "workflow_gap"
    """A structural gap `atlas.alpha.portfolio_status.AttentionCategory`
    already names (Decision without Outcome, Missing Case, ...).
    `value` = the category's own `.value`; `count` = how many real
    facts it summarizes (`ReviewQueueItem.reason_count`)."""

    MISSING_EVIDENCE = "missing_evidence"
    """A gap `atlas.decision_engine.contracts.EvidenceGapKind` already
    names. `value` = the gap kind's own `.value` -- the identical
    vocabulary Investment Case's own `investmentCase.intelligence
    .missingEvidence.*` keys already translate (Sprint B1's own
    "one truth, one place" finding, reused here rather than a second,
    parallel vocabulary)."""

    CONCENTRATION = "concentration"
    """A position-size finding `atlas.alpha.portfolio_intelligence
    .KeyFindingKind` already names (`HIGH_CONCENTRATION`/
    `ELEVATED_CONCENTRATION`). `value` = the finding kind's own
    `.value`."""

    LARGE_UNALLOCATED_CAPITAL = "large_unallocated_capital"
    """Portfolio-level, no entity ticker. `count` = the number of real
    considerations this capital could support
    (`KeyFinding.count`)."""

    EXECUTIVE_CHANGE = "executive_change"
    """A `LeadershipChangeEvent` already disclosed in a real transcript.
    `value` = `LeadershipChangeEventType.value` (the verb -- appointed/
    departed/...); `secondary_value` = `ExecutiveRoleCategory.value`
    (the role); `label` = the executive's own real name, never
    translated."""

    MANAGEMENT_CREDIBILITY = "management_credibility"
    """A deterioration `CredibilityFindingKind` already names
    (`INCONSISTENT_FOLLOW_THROUGH`/`GUIDANCE_REVISED_DOWNWARD` -- the
    only two members this source ever fires for; see
    `engine.py::management_credibility_signal`). `value` = the
    finding kind's own `.value`."""

    BUSINESS_QUALITY = "business_quality"
    """A deterioration `BusinessQualityFindingKind` already names
    (`WEAKENING_BUSINESS` -- the only member this source ever fires
    for; see `engine.py::business_quality_signal`). `value` = the
    finding kind's own `.value`."""

    CASE_CONDITION_STATUS = "case_condition_status"
    """A Case Condition that reached `status == "satisfied"`. `value` =
    the status string; `label` = the condition's own investor-authored
    `predicate_text` -- real free text, never translated, the same way
    a ticker or a person's name is not "system language" and stays
    exactly as written."""

    ASSUMPTION_STATUS = "assumption_status"
    """An Assumption that reached `status in ("invalidated",
    "challenged")`. `value` = the status string; `label` = the
    assumption's own investor-authored `statement` -- real free text,
    never translated, same reasoning as `CASE_CONDITION_STATUS`."""

    # ---- Implementation Sprint B1.2 (Engine Reason Localization
    # Contract) -- each of the following exposes one engine's own
    # *primary* transition, already a closed enum pair on that
    # engine's `*Change` dataclass; see this module's own "Scope"
    # section above for exactly what remains unconverted on each. ----

    CHANGE_INTELLIGENCE_THESIS_IMPACT = "change_intelligence_thesis_impact"
    """`atlas.analysis_engine.investment_case_change.ThesisImpact`
    (`WEAKENED`/`MIXED`/`UNCHANGED`/`STRENGTHENED`), already the real
    field `DailyBriefEntry.thesis_impact` reads. `value` = the impact's
    own `.value`."""

    PORTFOLIO_FIT_VERDICT = "portfolio_fit_verdict"
    """`atlas.alpha.portfolio_fit.models.FitVerdictReasonCode` (new in
    B1.2) -- names *why* `_overall_fit` reached its verdict, not just
    the verdict itself (`FitRating` alone can't distinguish "Risk Fit
    is Poor, a gate" from "2 dimensions rated Poor" -- both produce
    `FitRating.POOR`). `value` = the code's own `.value`."""

    MONITORING_CHANGE = "monitoring_change"
    """`atlas.alpha.monitoring.models.MonitoringChangeCategory`,
    already the real field `MonitoringChange.category`. `value` = the
    category's own `.value`. Never populated for
    `CASE_CONDITION_TRIGGERED` -- its own sentence embeds the
    investor's real predicate text, not currently threaded onto the
    wire as a separate field; left as the raw fallback string rather
    than translating a template around a value this module cannot see."""

    DECISION_READINESS_TRANSITION = "decision_readiness_transition"
    """`atlas.alpha.decision_readiness.models.DecisionReadinessStatus`.
    `value` = `DecisionReadinessChange.current_status.value`;
    `secondary_value` = `.previous_status.value`."""

    INVESTMENT_DECISION_TRANSITION = "investment_decision_transition"
    """`atlas.alpha.investment_decision.models.DecisionAction`. `value`
    = `DecisionChange.current_action.value`; `secondary_value` =
    `.previous_action.value`."""

    RECOMMENDATION_CONVICTION_TRANSITION = "recommendation_conviction_transition"
    """`atlas.alpha.recommendation_conviction.models.ConvictionStrength`.
    `value` = `ConvictionChange.current_strength.value`;
    `secondary_value` = `.previous_strength.value`."""

    DECISION_PATH_TRANSITION = "decision_path_transition"
    """`atlas.alpha.decision_path.models.FinalReachableState`. `value`
    = `DecisionPathChange.current_final_reachable_state.value`;
    `secondary_value` = `.previous_final_reachable_state.value`."""

    DECISION_RELIABILITY_TRANSITION = "decision_reliability_transition"
    """`atlas.alpha.decision_reliability.models.ReliabilityLevel`.
    `value` = `ReliabilityChange.current_level.value`;
    `secondary_value` = `.previous_level.value`. Only ever populated
    when the two differ -- `ReliabilityChange` can fire on a resolved/
    new limiting reason alone, with `previous_level == current_level`;
    that case has no real transition to name and is left unconverted
    (raw fallback), never a fabricated "unchanged" fact."""

    PORTFOLIO_DECISION_TRANSITION = "portfolio_decision_transition"
    """`atlas.alpha.portfolio_decision.models.PortfolioDecisionCategory`.
    `value` = `PortfolioDecisionChange.current_category.value`;
    `secondary_value` = `.previous_category.value`."""


@dataclass(frozen=True)
class ReasonFact:
    """One semantic fact -- never a rendered sentence. `entity` is the
    real ticker/subject the fact is about (never embedded in prose,
    unlike the legacy `reason: str` field this is threaded alongside).
    `value`/`secondary_value` are always a closed enum's own `.value`;
    `label` is real, already-real free text (a name, an investor's own
    words) that was never system language and is passed through
    verbatim, never translated. `count` is a real, already-computed
    number, never estimated here."""

    code: ReasonCode
    entity: str
    value: str | None = None
    secondary_value: str | None = None
    label: str | None = None
    count: int | None = None

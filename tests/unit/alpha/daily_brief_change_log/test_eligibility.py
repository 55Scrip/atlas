"""Tests for `atlas.alpha.daily_brief_change_log.eligibility`.

Covers Daily Brief 2.0's own required scenarios 2-9 (see the sprint's
own "Testing Requirements"): no material changes, recommendation
changed, thesis materially changed with recommendation unchanged,
minor/non-comparable facts excluded, internal bookkeeping excluded,
informational events excluded, and the "unchanged" verdict itself
excluded even though it comes from an otherwise-eligible source.
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
from atlas.alpha.daily_brief_agenda.reason_facts import ReasonCode, ReasonFact
from atlas.alpha.daily_brief_change_log.eligibility import extract_eligible_changes

_NOW = datetime(2026, 8, 27, 9, 0, tzinfo=timezone.utc)
_EMPTY_SUMMARY = PortfolioSummary(
    holdings_count=1, critical_count=0, high_count=0, watchlist_opportunity_count=0, cash_weight_percent=None, concentration_level=None
)


def _item(
    *,
    ticker: str = "NVDA",
    priority: PriorityLevel = PriorityLevel.NORMAL,
    source: AgendaSource = AgendaSource.INVESTMENT_DECISION,
    headline: str = "NVDA: Investment decision changed from hold to reduce.",
    reason: tuple[str, ...] = (),
    reason_facts: tuple[ReasonFact | None, ...] = (),
    nature: SignalNature = SignalNature.CHANGE_EVENT,
) -> AgendaItem:
    reason = reason or (headline,)
    reason_nature = tuple(nature for _ in reason)
    reason_facts = reason_facts or (None,) * len(reason)
    return AgendaItem(
        id=f"{AgendaItemKind.REVIEW_INVESTMENT_CASE.value}:{ticker}",
        priority=priority,
        kind=AgendaItemKind.REVIEW_INVESTMENT_CASE,
        group=AgendaGroup.PORTFOLIO,
        source=source,
        headline=headline,
        reason=reason,
        nature=nature,
        reason_nature=reason_nature,
        since=None,
        ticker=ticker,
        case_id=f"case-{ticker.lower()}",
        portfolio_context=None,
        generated_at=_NOW,
        reason_facts=reason_facts,
    )


def _agenda(items: tuple[AgendaItem, ...]) -> DailyBriefAgenda:
    return DailyBriefAgenda(generated_at=_NOW, summary=_EMPTY_SUMMARY, items=items)


class TestNoMaterialChanges:
    def test_an_item_with_no_reason_facts_at_all_produces_nothing(self):
        item = _item(reason_facts=(None,))
        assert extract_eligible_changes(_agenda((item,))) == ()

    def test_an_agenda_with_no_items_produces_nothing(self):
        assert extract_eligible_changes(_agenda(())) == ()

    def test_a_portfolio_level_item_with_no_ticker_is_skipped(self):
        item = _item(ticker="NVDA")
        # Simulate a portfolio-level item by overriding ticker to None post-construction
        # (dataclass is frozen, so build directly).
        portfolio_item = AgendaItem(
            id="portfolio-level:0",
            priority=PriorityLevel.NORMAL,
            kind=AgendaItemKind.PORTFOLIO_RISK,
            group=AgendaGroup.PORTFOLIO,
            source=AgendaSource.PORTFOLIO_INTELLIGENCE,
            headline="Large unallocated capital across 3 consideration(s)",
            reason=("Large unallocated capital across 3 consideration(s)",),
            nature=SignalNature.PERSISTENT_CONDITION,
            reason_nature=(SignalNature.PERSISTENT_CONDITION,),
            since=None,
            ticker=None,
            case_id=None,
            portfolio_context=None,
            generated_at=_NOW,
            reason_facts=(None,),
        )
        assert extract_eligible_changes(_agenda((item, portfolio_item))) == ()
        # (item itself has no reason_facts either, so total is still zero)


class TestRecommendationChanged:
    def test_investment_decision_transition_is_eligible(self):
        fact = ReasonFact(ReasonCode.INVESTMENT_DECISION_TRANSITION, "NVDA", value="reduce", secondary_value="hold")
        item = _item(reason_facts=(fact,))
        changes = extract_eligible_changes(_agenda((item,)))
        assert len(changes) == 1
        assert changes[0].reason_code == "investment_decision_transition"
        assert changes[0].value == "reduce"
        assert changes[0].secondary_value == "hold"
        assert changes[0].priority_rank == 0


class TestThesisChangedRecommendationUnchanged:
    def test_change_intelligence_weakened_is_eligible_even_with_no_investment_decision_fact(self):
        fact = ReasonFact(ReasonCode.CHANGE_INTELLIGENCE_THESIS_IMPACT, "AZN", value="weakened")
        item = _item(ticker="AZN", source=AgendaSource.CHANGE_INTELLIGENCE, reason_facts=(fact,))
        changes = extract_eligible_changes(_agenda((item,)))
        assert len(changes) == 1
        assert changes[0].reason_code == "change_intelligence_thesis_impact"
        assert changes[0].value == "weakened"

    def test_change_intelligence_unchanged_is_not_eligible(self):
        """The source's own honest 'nothing to report' state -- must
        never register as a change just because the source itself is
        otherwise eligible."""
        fact = ReasonFact(ReasonCode.CHANGE_INTELLIGENCE_THESIS_IMPACT, "AZN", value="unchanged")
        item = _item(ticker="AZN", source=AgendaSource.CHANGE_INTELLIGENCE, reason_facts=(fact,), nature=SignalNature.CHANGE_EVENT)
        assert extract_eligible_changes(_agenda((item,))) == ()


class TestMinorFactsExcluded:
    def test_monitoring_confidence_change_is_not_eligible(self):
        """Confidence/coverage/evidence-freshness changes are Atlas's
        own epistemic state, not the investment view -- excluded even
        though Monitoring is a partially-eligible source."""
        fact = ReasonFact(ReasonCode.MONITORING_CHANGE, "NVDA", value="confidence_increased")
        item = _item(source=AgendaSource.MONITORING, reason_facts=(fact,))
        assert extract_eligible_changes(_agenda((item,))) == ()

    def test_monitoring_stance_weakened_is_eligible(self):
        fact = ReasonFact(ReasonCode.MONITORING_CHANGE, "NVDA", value="stance_weakened")
        item = _item(source=AgendaSource.MONITORING, reason_facts=(fact,))
        changes = extract_eligible_changes(_agenda((item,)))
        assert len(changes) == 1
        assert changes[0].reason_code == "monitoring_change"

    def test_case_condition_satisfied_at_normal_priority_is_not_eligible(self):
        """No surviving `role` field -- HIGH priority is the monitoring-
        role case (a real observation, not by itself case-changing)."""
        fact = ReasonFact(ReasonCode.CASE_CONDITION_STATUS, "NVDA", value="satisfied", label="Gross margin stays above 70%")
        item = _item(priority=PriorityLevel.HIGH, source=AgendaSource.CASE_CONDITION, reason_facts=(fact,))
        assert extract_eligible_changes(_agenda((item,))) == ()

    def test_case_condition_satisfied_at_critical_priority_is_eligible(self):
        """CRITICAL is the invalidation-role proxy."""
        fact = ReasonFact(ReasonCode.CASE_CONDITION_STATUS, "NVDA", value="satisfied", label="Thesis invalidation trigger")
        item = _item(priority=PriorityLevel.CRITICAL, source=AgendaSource.CASE_CONDITION, reason_facts=(fact,))
        changes = extract_eligible_changes(_agenda((item,)))
        assert len(changes) == 1
        assert changes[0].reason_code == "case_condition_status"


class TestInternalBookkeepingExcluded:
    def test_workflow_gap_is_never_eligible(self):
        fact = ReasonFact(ReasonCode.WORKFLOW_GAP, "MSFT", value="decision_without_outcome", count=1)
        item = _item(ticker="MSFT", priority=PriorityLevel.CRITICAL, source=AgendaSource.PORTFOLIO_STATUS, reason_facts=(fact,))
        assert extract_eligible_changes(_agenda((item,))) == ()

    def test_missing_evidence_is_never_eligible(self):
        fact = ReasonFact(ReasonCode.MISSING_EVIDENCE, "MSFT", value="no_evidence_recorded")
        item = _item(ticker="MSFT", priority=PriorityLevel.HIGH, source=AgendaSource.PORTFOLIO_INTELLIGENCE, reason_facts=(fact,))
        assert extract_eligible_changes(_agenda((item,))) == ()

    def test_decision_readiness_transition_is_never_eligible(self):
        """Internal process/readiness bookkeeping, not an investment fact."""
        fact = ReasonFact(ReasonCode.DECISION_READINESS_TRANSITION, "NVDA", value="blocked", secondary_value="waiting")
        item = _item(source=AgendaSource.DECISION_READINESS, reason_facts=(fact,))
        assert extract_eligible_changes(_agenda((item,))) == ()

    def test_decision_reliability_transition_is_never_eligible(self):
        """Phase 11's own named example of language that must never
        reach the user -- excluded at the eligibility layer too."""
        fact = ReasonFact(ReasonCode.DECISION_RELIABILITY_TRANSITION, "NVDA", value="limited", secondary_value="moderate")
        item = _item(source=AgendaSource.DECISION_RELIABILITY, reason_facts=(fact,))
        assert extract_eligible_changes(_agenda((item,))) == ()


class TestInformationalEventsExcluded:
    def test_executive_change_is_never_eligible(self):
        """This sprint's own literal 'CEO appointed' example."""
        fact = ReasonFact(ReasonCode.EXECUTIVE_CHANGE, "NVDA", value="appointed", secondary_value="ceo", label="Jane Doe")
        item = _item(source=AgendaSource.EXECUTIVE_CHANGE, priority=PriorityLevel.HIGH, reason_facts=(fact,))
        assert extract_eligible_changes(_agenda((item,))) == ()

    def test_concentration_is_never_eligible(self):
        fact = ReasonFact(ReasonCode.CONCENTRATION, "NVDA", value="high_concentration")
        item = _item(source=AgendaSource.PORTFOLIO_INTELLIGENCE, priority=PriorityLevel.HIGH, reason_facts=(fact,))
        assert extract_eligible_changes(_agenda((item,))) == ()


class TestBusinessQualityAndManagementCredibility:
    def test_business_quality_weakening_is_eligible(self):
        fact = ReasonFact(ReasonCode.BUSINESS_QUALITY, "NVDA", value="weakening_business")
        item = _item(source=AgendaSource.BUSINESS_QUALITY, priority=PriorityLevel.HIGH, nature=SignalNature.PERSISTENT_CONDITION, reason_facts=(fact,))
        changes = extract_eligible_changes(_agenda((item,)))
        assert len(changes) == 1
        assert changes[0].reason_code == "business_quality"

    def test_management_credibility_guidance_revised_is_eligible(self):
        fact = ReasonFact(ReasonCode.MANAGEMENT_CREDIBILITY, "NVDA", value="guidance_revised_downward")
        item = _item(source=AgendaSource.MANAGEMENT_CREDIBILITY, nature=SignalNature.PERSISTENT_CONDITION, reason_facts=(fact,))
        changes = extract_eligible_changes(_agenda((item,)))
        assert len(changes) == 1
        assert changes[0].reason_code == "management_credibility"


class TestScansEveryContributingFactNotOnlyTheWinner:
    def test_a_real_change_buried_behind_a_bookkeeping_winner_is_still_found(self):
        """`_item_for_ticker`'s own tie-break can let bookkeeping win
        the headline over a real recommendation change for the same
        ticker -- this module must still find the real fact."""
        bookkeeping_fact = ReasonFact(ReasonCode.WORKFLOW_GAP, "NVDA", value="decision_without_outcome", count=1)
        real_fact = ReasonFact(ReasonCode.INVESTMENT_DECISION_TRANSITION, "NVDA", value="reduce", secondary_value="hold")
        item = _item(
            priority=PriorityLevel.CRITICAL,
            source=AgendaSource.PORTFOLIO_STATUS,
            headline="NVDA: decision without outcome (1 item(s))",
            reason=("NVDA: decision without outcome (1 item(s))", "NVDA: Investment decision changed from hold to reduce."),
            reason_facts=(bookkeeping_fact, real_fact),
        )
        changes = extract_eligible_changes(_agenda((item,)))
        assert len(changes) == 1
        assert changes[0].reason_code == "investment_decision_transition"

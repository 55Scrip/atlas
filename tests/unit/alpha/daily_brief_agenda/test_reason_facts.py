"""Implementation Sprint B1.1 (Backend Language Cleanup) -- `ReasonFact`
threading through `engine.py`'s own signal constructors and
consolidation. Mirrors `test_engine.py`'s own style and fixtures;
`_item_for_ticker`/`build_agenda` themselves are exercised via
`build_agenda`, never re-implemented here.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.daily_brief_agenda.engine import (
    business_quality_signal,
    case_condition_signal,
    concentration_signal,
    evidence_gap_signal,
    executive_change_signal,
    management_credibility_signal,
    portfolio_level_signal,
    workflow_signal,
    _item_for_ticker,
    TickerContext,
)
from atlas.alpha.daily_brief_agenda.models import PriorityLevel
from atlas.alpha.daily_brief_agenda.reason_facts import ReasonCode, ReasonFact
from atlas.alpha.investment_case.business_quality_intelligence import BusinessQualityFindingKind
from atlas.alpha.investment_case.management_credibility_intelligence import CredibilityFindingKind
from atlas.alpha.portfolio_intelligence.models import KeyFindingKind
from atlas.alpha.portfolio_status.models import AttentionCategory

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestReasonFactCarriedBySignalConstructors:
    """Every converted source's own `*_signal()` function accepts and
    carries a `fact` through unchanged -- construction only, no
    translation, no rendering (that boundary belongs to the frontend)."""

    def test_workflow_signal_carries_fact(self):
        fact = ReasonFact(ReasonCode.WORKFLOW_GAP, "MSFT", value="DECISION_WITHOUT_OUTCOME", count=2)
        signal = workflow_signal(AttentionCategory.DECISION_WITHOUT_OUTCOME, "raw reason", count=2, fact=fact)
        assert signal.fact is fact

    def test_workflow_signal_defaults_to_no_fact(self):
        signal = workflow_signal(AttentionCategory.MISSING_CASE, "raw reason", count=1)
        assert signal.fact is None

    def test_concentration_signal_carries_fact(self):
        fact = ReasonFact(ReasonCode.CONCENTRATION, "NVDA", value="high_concentration")
        signal = concentration_signal(KeyFindingKind.HIGH_CONCENTRATION, "raw reason", fact=fact)
        assert signal.fact is fact

    def test_portfolio_level_signal_carries_fact(self):
        fact = ReasonFact(ReasonCode.LARGE_UNALLOCATED_CAPITAL, "portfolio", count=3)
        signal = portfolio_level_signal(PriorityLevel.NORMAL, "raw reason", fact=fact)
        assert signal.fact is fact

    def test_evidence_gap_signal_carries_fact(self):
        fact = ReasonFact(ReasonCode.MISSING_EVIDENCE, "AZN", value="no_evidence_recorded")
        signal = evidence_gap_signal("raw reason", fact=fact)
        assert signal.fact is fact

    def test_executive_change_signal_carries_fact(self):
        fact = ReasonFact(ReasonCode.EXECUTIVE_CHANGE, "AMD", value="appointment", secondary_value="ceo", label="Lisa Su")
        from atlas.alpha.investment_case.executive_change_intelligence import ExecutiveRoleCategory

        signal = executive_change_signal(ExecutiveRoleCategory.CEO, "raw reason", _NOW, fact=fact)
        assert signal.fact is fact

    def test_management_credibility_signal_carries_fact(self):
        fact = ReasonFact(ReasonCode.MANAGEMENT_CREDIBILITY, "TSLA", value="inconsistent_follow_through")
        signal = management_credibility_signal(CredibilityFindingKind.INCONSISTENT_FOLLOW_THROUGH, "raw reason", fact=fact)
        assert signal.fact is fact

    def test_business_quality_signal_carries_fact(self):
        fact = ReasonFact(ReasonCode.BUSINESS_QUALITY, "META", value="weakening_business")
        signal = business_quality_signal(BusinessQualityFindingKind.WEAKENING_BUSINESS, "raw reason", fact=fact)
        assert signal.fact is fact

    def test_case_condition_signal_carries_fact(self):
        fact = ReasonFact(ReasonCode.CASE_CONDITION_STATUS, "NVDA", value="satisfied", label="Capex growth decelerates")
        signal = case_condition_signal("monitoring", "satisfied", "raw reason", _NOW, fact=fact)
        assert signal is not None
        assert signal.fact is fact


class TestReasonFactsThreadedThroughAgendaItem:
    """`_item_for_ticker` builds `reason_facts` parallel to `reason` --
    same length, same order, same first-occurrence-wins dedup key
    `reason_nature` already establishes, generalized to a second
    parallel tuple rather than a second, independently-ordered one."""

    def test_single_signal_with_fact_appears_at_matching_index(self):
        fact = ReasonFact(ReasonCode.MISSING_EVIDENCE, "AZN", value="no_evidence_recorded")
        signal = evidence_gap_signal("AZN: missing evidence (no evidence recorded)", fact=fact)
        item = _item_for_ticker(TickerContext("AZN", "case-1", True, None), [signal], _NOW)
        assert item is not None
        assert item.reason == ("AZN: missing evidence (no evidence recorded)",)
        assert item.reason_facts == (fact,)

    def test_signal_without_fact_leaves_none_at_matching_index(self):
        signal = evidence_gap_signal("AZN: missing evidence (no evidence recorded)")
        item = _item_for_ticker(TickerContext("AZN", "case-1", True, None), [signal], _NOW)
        assert item is not None
        assert item.reason_facts == (None,)

    def test_two_signals_keep_facts_aligned_with_their_own_reason_text(self):
        fact_a = ReasonFact(ReasonCode.CONCENTRATION, "NVDA", value="high_concentration")
        signal_a = concentration_signal(KeyFindingKind.HIGH_CONCENTRATION, "NVDA: high concentration", fact=fact_a)
        signal_b = evidence_gap_signal("NVDA: missing evidence (no evidence recorded)")  # no fact -- not converted here
        item = _item_for_ticker(TickerContext("NVDA", "case-1", True, None), [signal_a, signal_b], _NOW)
        assert item is not None
        assert len(item.reason) == len(item.reason_facts) == 2
        facts_by_reason = dict(zip(item.reason, item.reason_facts))
        assert facts_by_reason["NVDA: high concentration"] is fact_a
        assert facts_by_reason["NVDA: missing evidence (no evidence recorded)"] is None

    def test_default_reason_facts_is_empty_tuple(self):
        """An item built with no signals at all never reaches `AgendaItem`
        (`_item_for_ticker` returns `None`) -- this only guards the
        dataclass's own default stays an empty tuple, not `None`,
        matching `reason`/`reason_nature`'s own empty-tuple defaults."""
        from atlas.alpha.daily_brief_agenda.models import AgendaItem

        assert AgendaItem.__dataclass_fields__["reason_facts"].default == ()

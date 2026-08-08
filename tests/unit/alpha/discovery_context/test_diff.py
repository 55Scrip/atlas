"""Unit tests for the deterministic Portfolio/Case Intelligence diff
utilities (ATLAS-018 Phase 5). Pure dataclass construction -- no
database, no HTTP -- since `diff_portfolio_intelligence`/
`diff_case_intelligence` are pure functions over already-real report
objects.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_intelligence.models import (
    CaseIntelligenceReport,
    ConvictionStatus,
    CurrentThesis,
    CurrentView,
    KeyRiskItem,
    KeyRiskKind,
    PortfolioContextSummary,
    ReviewStatus,
)
from atlas.alpha.discovery_context.diff import diff_case_intelligence, diff_portfolio_intelligence
from atlas.alpha.portfolio_intelligence.models import (
    ConsiderItem,
    ConsiderKind,
    KeyFinding,
    KeyFindingKind,
    PortfolioFitStatus,
    PortfolioFitUnavailableReason,
    PortfolioIntelligenceReport,
    PortfolioSummaryMetrics,
    RiskSignal,
    RiskSignalKind,
)
from atlas.decision_engine.contracts import EvidenceCoverageLevel


def _summary(**overrides) -> PortfolioSummaryMetrics:
    defaults = dict(
        holdings_count=1,
        largest_position_ticker="AMD",
        largest_position_weight_percent=20.0,
        number_of_investment_cases=1,
        open_decisions=0,
        pending_outcomes=0,
        pending_executions=0,
        concentration_level="Low",
        unallocated_percent=0.0,
    )
    defaults.update(overrides)
    return PortfolioSummaryMetrics(**defaults)


def _portfolio_report(**overrides) -> PortfolioIntelligenceReport:
    defaults = dict(
        exists=True,
        overview=_summary(),
        cash_weight_percent=None,
        cash_value_absolute=None,
        key_findings=(),
        consider_items=(),
        risk_signals=(),
        missing_evidence=(),
        portfolio_fit=PortfolioFitStatus(available=False, reason=PortfolioFitUnavailableReason.NOT_YET_IMPLEMENTED),
    )
    defaults.update(overrides)
    return PortfolioIntelligenceReport(**defaults)


class TestDiffPortfolioIntelligence:
    def test_identical_reports_have_no_changes(self):
        report = _portfolio_report()
        diff = diff_portfolio_intelligence(report, report)
        assert not diff.has_changes
        assert diff.key_findings_added == ()
        assert diff.key_findings_removed == ()

    def test_new_key_finding_is_added_not_removed(self):
        previous = _portfolio_report()
        finding = KeyFinding(kind=KeyFindingKind.HIGH_CONCENTRATION, count=1, tickers=("AMD",))
        current = _portfolio_report(key_findings=(finding,))

        diff = diff_portfolio_intelligence(previous, current)
        assert diff.key_findings_added == (finding,)
        assert diff.key_findings_removed == ()
        assert diff.has_changes

    def test_resolved_key_finding_is_removed_not_added(self):
        finding = KeyFinding(kind=KeyFindingKind.HIGH_CONCENTRATION, count=1, tickers=("AMD",))
        previous = _portfolio_report(key_findings=(finding,))
        current = _portfolio_report(key_findings=())

        diff = diff_portfolio_intelligence(previous, current)
        assert diff.key_findings_removed == (finding,)
        assert diff.key_findings_added == ()

    def test_consider_and_risk_signal_diffs(self):
        consider = ConsiderItem(
            kind=ConsiderKind.GATHER_EVIDENCE,
            ticker="AMD",
            case_id="case-1",
            confidence=EvidenceCoverageLevel.NONE,
            related_holdings=("AMD",),
            evidence_gap_count=1,
        )
        risk = RiskSignal(kind=RiskSignalKind.MISSING_EVIDENCE, ticker="AMD", case_id="case-1")
        previous = _portfolio_report()
        current = _portfolio_report(consider_items=(consider,), risk_signals=(risk,))

        diff = diff_portfolio_intelligence(previous, current)
        assert diff.consider_items_added == (consider,)
        assert diff.risk_signals_added == (risk,)

    def test_holdings_count_changed_flag(self):
        previous = _portfolio_report(overview=_summary(holdings_count=1))
        current = _portfolio_report(overview=_summary(holdings_count=2))

        diff = diff_portfolio_intelligence(previous, current)
        assert diff.holdings_count_changed is True
        assert diff.has_changes

    def test_concentration_level_changed_flag(self):
        previous = _portfolio_report(overview=_summary(concentration_level="Low"))
        current = _portfolio_report(overview=_summary(concentration_level="High"))

        diff = diff_portfolio_intelligence(previous, current)
        assert diff.concentration_level_changed is True

    def test_unchanged_overview_reports_no_changed_flags(self):
        previous = _portfolio_report()
        current = _portfolio_report()

        diff = diff_portfolio_intelligence(previous, current)
        assert diff.holdings_count_changed is False
        assert diff.concentration_level_changed is False
        assert not diff.has_changes


def _case_report(**overrides) -> CaseIntelligenceReport:
    defaults = dict(
        case_id="case-1",
        current_view=CurrentView(
            ticker="AMD", held=True, weight_percent=20.0, value_absolute=None, reconciliation_status="NONE"
        ),
        current_thesis=CurrentThesis(
            latest_decision_reason=None, latest_decision_type=None, latest_observation_statement=None
        ),
        evidence_quality=None,
        supporting_evidence=None,
        contradicting_evidence=None,
        missing_evidence=(),
        open_questions=(),
        key_risks=(),
        decision_history=(),
        observation_timeline=(),
        portfolio_context=PortfolioContextSummary(
            held=True,
            facts=(),
            weight_percent=20.0,
            concentration_level="Low",
            most_recent_trade_transaction_type=None,
            most_recent_trade_at=None,
        ),
        portfolio_fit=PortfolioFitStatus(available=False, reason=PortfolioFitUnavailableReason.NOT_YET_IMPLEMENTED),
        conviction=ConvictionStatus(available=False),
        confidence=EvidenceCoverageLevel.NOT_APPLICABLE,
        review_status=ReviewStatus(is_stale=False, age_days=None),
        consider_items=(),
    )
    defaults.update(overrides)
    return CaseIntelligenceReport(**defaults)


class TestDiffCaseIntelligence:
    def test_identical_reports_have_no_changes(self):
        report = _case_report()
        diff = diff_case_intelligence(report, report)
        assert not diff.has_changes
        assert diff.confidence_changed is False

    def test_confidence_change_is_detected(self):
        previous = _case_report(confidence=EvidenceCoverageLevel.NONE)
        current = _case_report(confidence=EvidenceCoverageLevel.FULL)

        diff = diff_case_intelligence(previous, current)
        assert diff.confidence_changed is True
        assert diff.previous_confidence is EvidenceCoverageLevel.NONE
        assert diff.current_confidence is EvidenceCoverageLevel.FULL
        assert diff.has_changes

    def test_new_key_risk_is_added(self):
        risk = KeyRiskItem(kind=KeyRiskKind.HIGH_CONCENTRATION)
        previous = _case_report()
        current = _case_report(key_risks=(risk,))

        diff = diff_case_intelligence(previous, current)
        assert diff.key_risks_added == (risk,)
        assert diff.key_risks_removed == ()

    def test_new_decision_by_id_not_already_seen(self):
        from atlas.alpha.case_intelligence.models import DecisionHistoryEntry

        existing = DecisionHistoryEntry(
            decision_id="d1",
            decision_type="BUY",
            reason="Initial.",
            investor_confidence=70,
            decided_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            outcome_id=None,
            outcome_statement=None,
            outcome_occurred_at=None,
        )
        new = DecisionHistoryEntry(
            decision_id="d2",
            decision_type="SELL",
            reason="Trimmed.",
            investor_confidence=60,
            decided_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            outcome_id=None,
            outcome_statement=None,
            outcome_occurred_at=None,
        )
        previous = _case_report(decision_history=(existing,))
        current = _case_report(decision_history=(existing, new))

        diff = diff_case_intelligence(previous, current)
        assert diff.new_decisions == (new,)

    def test_new_observation_by_id_not_already_seen(self):
        from atlas.alpha.case_intelligence.models import ObservationTimelineEntry

        existing = ObservationTimelineEntry(
            observation_id="o1",
            subject="AMD",
            statement="Existing.",
            observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            evidence_count=0,
            epistemic_status=None,
        )
        new = ObservationTimelineEntry(
            observation_id="o2",
            subject="AMD",
            statement="New note.",
            observed_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            evidence_count=0,
            epistemic_status=None,
        )
        previous = _case_report(observation_timeline=(existing,))
        current = _case_report(observation_timeline=(existing, new))

        diff = diff_case_intelligence(previous, current)
        assert diff.new_observations == (new,)

    def test_missing_evidence_added_and_removed(self):
        from atlas.decision_engine.contracts import EvidenceGap, EvidenceGapKind

        removed_gap = EvidenceGap(kind=EvidenceGapKind.NO_EVIDENCE_RECORDED)
        added_gap = EvidenceGap(kind=EvidenceGapKind.OBSERVATION_WITHOUT_EVIDENCE, reference="o1")
        previous = _case_report(missing_evidence=(removed_gap,))
        current = _case_report(missing_evidence=(added_gap,))

        diff = diff_case_intelligence(previous, current)
        assert diff.missing_evidence_added == (added_gap,)
        assert diff.missing_evidence_removed == (removed_gap,)

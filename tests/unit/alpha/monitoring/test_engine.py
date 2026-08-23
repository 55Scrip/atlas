"""Tests for `atlas.alpha.monitoring.engine` -- `EvidenceHistory`/
`EvidenceTransition`/`ChangeIntelligence`/`ChangeFinding` are hand-built,
controlled stand-ins for already-tested-elsewhere upstream engines,
mirroring `tests/unit/alpha/evidence_timeline/test_engine.py`'s own
module docstring convention exactly, since this module's whole job is
reclassifying their already-real output, never recomputing it.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.coverage.models import ConfidenceLevel
from atlas.alpha.daily_brief_agenda.models import AgendaItemKind
from atlas.alpha.evidence_timeline.models import EvidenceHistory, EvidenceTransition, EvidenceTransitionCategory, SourceEvidenceEvent
from atlas.alpha.monitoring.engine import (
    CaseConditionSignal,
    build_monitoring_result,
    classify_case_condition,
    classify_evidence_history,
    classify_material_risk,
    derive_operational_status,
    derive_status,
    needs_recompute,
    recommended_action,
)
from atlas.alpha.monitoring.models import (
    MonitoringChangeCategory,
    MonitoringFailure,
    MonitoringMateriality,
    MonitoringRunRecord,
    MonitoringScope,
    MonitoringStatus,
    OperationalMonitoringStatus,
    OperationalRunStatus,
)
from atlas.analysis_engine.investment_case_change import ChangeCategory, ChangeDirection, ChangeFinding, ChangeIntelligence

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
PREVIOUS = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _transition(category, direction, *, current_state="x", is_material_hint=None) -> EvidenceTransition:
    # `current_state` matters only for FRESHNESS_CHANGED (materiality
    # depends on it being exactly "stale" -- see `is_material_transition`).
    return EvidenceTransition(
        id=f"{category.value}:{direction.value}",
        category=category,
        direction=direction,
        previous_state="y",
        current_state=current_state,
        details={},
    )


def _history(transitions=(), new_source_evidence=(), *, is_baseline=False) -> EvidenceHistory:
    return EvidenceHistory(
        is_baseline=is_baseline,
        transitions=transitions,
        new_source_evidence=new_source_evidence,
        previous_captured_at=None if is_baseline else PREVIOUS,
        current_captured_at=NOW,
    )


def _change_intelligence(changes=(), *, is_baseline=False) -> ChangeIntelligence:
    return ChangeIntelligence(
        is_baseline=is_baseline,
        changes=changes,
        thesis_impact=None,
        summary_narrative="",
        previous_captured_at=None if is_baseline else PREVIOUS,
        current_captured_at=NOW,
    )


def _finding(category, direction=ChangeDirection.NEGATIVE, finding_id="f1") -> ChangeFinding:
    return ChangeFinding(
        id=finding_id,
        category=category,
        direction=direction,
        previous_state="absent",
        current_state="growth_deceleration",
        details={},
        evidence_references=(),
        source_finding_id=None,
    )


class TestBaselineNeverProducesChanges:
    """Critical requirement (Deliverable 25): unchanged recomputation --
    and a genuine baseline -- must never fabricate a MonitoringChange."""

    def test_a_baseline_evidence_history_produces_no_changes_even_with_real_transitions_passed_in(self):
        history = _history(
            transitions=(_transition(EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.POSITIVE),),
            new_source_evidence=(SourceEvidenceEvent(fact_kind="revenue", period="FY2024"),),
            is_baseline=True,
        )
        assert classify_evidence_history(history, ticker="NVDA") == ()

    def test_a_baseline_change_intelligence_produces_no_material_risk_change(self):
        ci = _change_intelligence(changes=(_finding(ChangeCategory.RISK_ADDED),), is_baseline=True)
        assert classify_material_risk(ci, ticker="NVDA") == ()

    def test_an_empty_evidence_history_produces_no_changes(self):
        assert classify_evidence_history(_history(), ticker="NVDA") == ()

    def test_no_change_intelligence_produces_no_material_risk_change(self):
        assert classify_material_risk(None, ticker="NVDA") == ()


class TestEvidenceTransitionTaxonomy:
    def test_stance_positive_maps_to_stance_strengthened(self):
        history = _history(transitions=(_transition(EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.POSITIVE),))
        changes = classify_evidence_history(history, ticker="NVDA")
        assert len(changes) == 1
        assert changes[0].category is MonitoringChangeCategory.STANCE_STRENGTHENED
        assert changes[0].materiality is MonitoringMateriality.MATERIAL

    def test_stance_negative_maps_to_stance_weakened(self):
        history = _history(transitions=(_transition(EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.NEGATIVE),))
        changes = classify_evidence_history(history, ticker="NVDA")
        assert changes[0].category is MonitoringChangeCategory.STANCE_WEAKENED

    def test_stance_neutral_maps_to_stance_became_uncertain(self):
        history = _history(transitions=(_transition(EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.NEUTRAL),))
        changes = classify_evidence_history(history, ticker="NVDA")
        assert changes[0].category is MonitoringChangeCategory.STANCE_BECAME_UNCERTAIN

    def test_coverage_positive_and_negative(self):
        pos = classify_evidence_history(
            _history(transitions=(_transition(EvidenceTransitionCategory.COVERAGE_CHANGED, ChangeDirection.POSITIVE),)), ticker=None
        )
        neg = classify_evidence_history(
            _history(transitions=(_transition(EvidenceTransitionCategory.COVERAGE_CHANGED, ChangeDirection.NEGATIVE),)), ticker=None
        )
        assert pos[0].category is MonitoringChangeCategory.COVERAGE_IMPROVED
        assert neg[0].category is MonitoringChangeCategory.COVERAGE_DETERIORATED

    def test_confidence_positive_is_material_but_negative_is_more_material_by_convention(self):
        # Materiality is reused from `is_material_transition`, which
        # treats CONFIDENCE_CHANGED as material only when NEGATIVE.
        pos = classify_evidence_history(
            _history(transitions=(_transition(EvidenceTransitionCategory.CONFIDENCE_CHANGED, ChangeDirection.POSITIVE),)), ticker=None
        )
        neg = classify_evidence_history(
            _history(transitions=(_transition(EvidenceTransitionCategory.CONFIDENCE_CHANGED, ChangeDirection.NEGATIVE),)), ticker=None
        )
        assert pos[0].category is MonitoringChangeCategory.CONFIDENCE_IMPROVED
        assert pos[0].materiality is MonitoringMateriality.MINOR
        assert neg[0].category is MonitoringChangeCategory.CONFIDENCE_DETERIORATED
        assert neg[0].materiality is MonitoringMateriality.MATERIAL

    def test_evidence_quality_positive_and_negative(self):
        pos = classify_evidence_history(
            _history(transitions=(_transition(EvidenceTransitionCategory.EVIDENCE_QUALITY_CHANGED, ChangeDirection.POSITIVE),)), ticker=None
        )
        neg = classify_evidence_history(
            _history(transitions=(_transition(EvidenceTransitionCategory.EVIDENCE_QUALITY_CHANGED, ChangeDirection.NEGATIVE),)), ticker=None
        )
        assert pos[0].category is MonitoringChangeCategory.MATERIAL_EVIDENCE_STRENGTHENED
        assert neg[0].category is MonitoringChangeCategory.MATERIAL_EVIDENCE_WEAKENED

    def test_conflict_status_appeared_and_resolved(self):
        appeared = classify_evidence_history(
            _history(transitions=(_transition(EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED, ChangeDirection.NEGATIVE),)), ticker=None
        )
        resolved = classify_evidence_history(
            _history(transitions=(_transition(EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED, ChangeDirection.POSITIVE),)), ticker=None
        )
        assert appeared[0].category is MonitoringChangeCategory.EVIDENCE_CONFLICT_APPEARED
        assert resolved[0].category is MonitoringChangeCategory.EVIDENCE_CONFLICT_RESOLVED

    def test_freshness_changed_to_stale_becomes_evidence_became_stale(self):
        transition = _transition(EvidenceTransitionCategory.FRESHNESS_CHANGED, ChangeDirection.NEGATIVE, current_state="stale")
        changes = classify_evidence_history(_history(transitions=(transition,)), ticker=None)
        assert len(changes) == 1
        assert changes[0].category is MonitoringChangeCategory.EVIDENCE_BECAME_STALE
        assert changes[0].materiality is MonitoringMateriality.MATERIAL

    def test_freshness_changed_to_something_other_than_stale_is_suppressed(self):
        transition = _transition(EvidenceTransitionCategory.FRESHNESS_CHANGED, ChangeDirection.POSITIVE, current_state="fresh")
        changes = classify_evidence_history(_history(transitions=(transition,)), ticker=None)
        assert changes == ()


class TestNewMaterialEvidence:
    def test_new_source_evidence_alone_with_no_material_transition_is_not_reported(self):
        history = _history(new_source_evidence=(SourceEvidenceEvent(fact_kind="revenue", period="FY2024"),))
        assert classify_evidence_history(history, ticker="NVDA") == ()

    def test_new_source_evidence_combined_with_a_material_transition_is_reported(self):
        history = _history(
            transitions=(_transition(EvidenceTransitionCategory.COVERAGE_CHANGED, ChangeDirection.POSITIVE),),
            new_source_evidence=(SourceEvidenceEvent(fact_kind="revenue", period="FY2024"),),
        )
        categories = {c.category for c in classify_evidence_history(history, ticker="NVDA")}
        assert MonitoringChangeCategory.NEW_MATERIAL_EVIDENCE in categories
        assert MonitoringChangeCategory.COVERAGE_IMPROVED in categories


class TestMaterialRisk:
    def test_risk_added_becomes_material_risk_appeared(self):
        ci = _change_intelligence(changes=(_finding(ChangeCategory.RISK_ADDED),))
        changes = classify_material_risk(ci, ticker="NVDA")
        assert len(changes) == 1
        assert changes[0].category is MonitoringChangeCategory.MATERIAL_RISK_APPEARED
        assert changes[0].materiality is MonitoringMateriality.MATERIAL
        assert changes[0].direction is ChangeDirection.NEGATIVE

    def test_a_different_change_category_is_never_reclassified_as_material_risk(self):
        ci = _change_intelligence(changes=(_finding(ChangeCategory.VALUATION_CHANGED),))
        assert classify_material_risk(ci, ticker="NVDA") == ()


class TestCaseConditionIntegration:
    def test_a_satisfied_invalidation_condition_is_material(self):
        row = CaseConditionSignal(condition_id="c1", role="invalidation", status="satisfied", predicate_text="Debt/EBITDA exceeds 3x")
        change = classify_case_condition(row, ticker="NVDA")
        assert change is not None
        assert change.category is MonitoringChangeCategory.CASE_CONDITION_TRIGGERED
        assert change.materiality is MonitoringMateriality.MATERIAL

    def test_a_satisfied_monitoring_condition_is_minor(self):
        row = CaseConditionSignal(condition_id="c1", role="monitoring", status="satisfied", predicate_text="Next earnings report")
        change = classify_case_condition(row, ticker="NVDA")
        assert change is not None
        assert change.materiality is MonitoringMateriality.MINOR

    def test_an_active_unsatisfied_condition_produces_no_event(self):
        row = CaseConditionSignal(condition_id="c1", role="invalidation", status="active", predicate_text="Debt/EBITDA exceeds 3x")
        assert classify_case_condition(row, ticker="NVDA") is None

    def test_a_retired_condition_produces_no_event(self):
        row = CaseConditionSignal(condition_id="c1", role="monitoring", status="retired", predicate_text="x")
        assert classify_case_condition(row, ticker="NVDA") is None


class TestStatusDerivation:
    def test_no_changes_and_ample_confidence_is_up_to_date(self):
        assert derive_status((), ConfidenceLevel.HIGH) is MonitoringStatus.UP_TO_DATE

    def test_no_changes_and_very_limited_confidence_is_waiting_for_better_evidence(self):
        assert derive_status((), ConfidenceLevel.VERY_LIMITED) is MonitoringStatus.WAITING_FOR_BETTER_EVIDENCE

    def test_a_minor_only_change_never_promotes_status_above_up_to_date(self):
        history = _history(transitions=(_transition(EvidenceTransitionCategory.CONFIDENCE_CHANGED, ChangeDirection.POSITIVE),))
        changes = classify_evidence_history(history, ticker=None)
        assert derive_status(changes, ConfidenceLevel.HIGH) is MonitoringStatus.UP_TO_DATE

    def test_a_material_stance_weakened_change_is_high_importance(self):
        history = _history(transitions=(_transition(EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.NEGATIVE),))
        changes = classify_evidence_history(history, ticker=None)
        assert derive_status(changes, ConfidenceLevel.MODERATE) is MonitoringStatus.CHANGED_HIGH_IMPORTANCE

    def test_a_material_but_non_high_importance_change_is_review_suggested(self):
        history = _history(transitions=(_transition(EvidenceTransitionCategory.COVERAGE_CHANGED, ChangeDirection.POSITIVE),))
        changes = classify_evidence_history(history, ticker=None)
        assert derive_status(changes, ConfidenceLevel.MODERATE) is MonitoringStatus.CHANGED_REVIEW_SUGGESTED

    def test_an_invalidation_condition_trigger_is_always_high_importance(self):
        row = CaseConditionSignal(condition_id="c1", role="invalidation", status="satisfied", predicate_text="x")
        change = classify_case_condition(row, ticker=None)
        assert derive_status((change,), ConfidenceLevel.HIGH) is MonitoringStatus.CHANGED_HIGH_IMPORTANCE


class TestRecommendedAction:
    def test_no_material_changes_recommends_nothing(self):
        assert recommended_action((), is_holding=True) is None

    def test_a_material_change_for_a_holding_recommends_review_portfolio_position(self):
        history = _history(transitions=(_transition(EvidenceTransitionCategory.COVERAGE_CHANGED, ChangeDirection.NEGATIVE),))
        changes = classify_evidence_history(history, ticker=None)
        assert recommended_action(changes, is_holding=True) is AgendaItemKind.REVIEW_PORTFOLIO_POSITION

    def test_a_material_change_for_a_watchlist_company_recommends_review_watchlist_candidate(self):
        history = _history(transitions=(_transition(EvidenceTransitionCategory.COVERAGE_CHANGED, ChangeDirection.NEGATIVE),))
        changes = classify_evidence_history(history, ticker=None)
        assert recommended_action(changes, is_holding=False) is AgendaItemKind.REVIEW_WATCHLIST_CANDIDATE

    def test_a_triggered_case_condition_always_recommends_evaluating_it(self):
        row = CaseConditionSignal(condition_id="c1", role="invalidation", status="satisfied", predicate_text="x")
        change = classify_case_condition(row, ticker=None)
        assert recommended_action((change,), is_holding=True) is AgendaItemKind.EVALUATE_CASE_CONDITION


class TestBuildMonitoringResult:
    def test_a_fully_stable_result_reports_up_to_date_with_no_recommended_action(self):
        result = build_monitoring_result(
            case_id="case-1",
            ticker="NVDA",
            scope=MonitoringScope.PORTFOLIO,
            is_holding=True,
            evidence_history=_history(),
            change_intelligence=None,
            case_condition_rows=(),
            stance_level="maintain",
            confidence_level=ConfidenceLevel.HIGH,
            coverage_level="substantial_coverage",
            latest_evidence_captured_at=NOW,
            generated_at=NOW,
        )
        assert result.status is MonitoringStatus.UP_TO_DATE
        assert result.changes == ()
        assert result.recommended_action is None

    def test_a_material_change_rolls_up_into_a_non_up_to_date_status_and_a_real_recommended_action(self):
        result = build_monitoring_result(
            case_id="case-1",
            ticker="NVDA",
            scope=MonitoringScope.WATCHLIST,
            is_holding=False,
            evidence_history=_history(transitions=(_transition(EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.NEGATIVE),)),
            change_intelligence=None,
            case_condition_rows=(),
            stance_level="reduce",
            confidence_level=ConfidenceLevel.MODERATE,
            coverage_level="substantial_coverage",
            latest_evidence_captured_at=NOW,
            generated_at=NOW,
        )
        assert result.status is MonitoringStatus.CHANGED_HIGH_IMPORTANCE
        assert result.recommended_action is AgendaItemKind.REVIEW_WATCHLIST_CANDIDATE
        assert len(result.changes) == 1


def _run_record(
    status=OperationalRunStatus.COMPLETED, forced=False, evaluated_count=1, skipped_count=0, failures=()
) -> MonitoringRunRecord:
    return MonitoringRunRecord(
        run_id="run-1",
        status=status,
        started_at=PREVIOUS,
        completed_at=NOW,
        forced=forced,
        evaluated_count=evaluated_count,
        skipped_count=skipped_count,
        failures=failures,
    )


class TestNeedsRecompute:
    """Sprint 8, Deliverable 4/5 -- the one incremental-monitoring
    rule, and the critical negative test proving it never fabricates
    dirtiness from the mere passage of time."""

    def test_a_case_with_no_checkpoint_at_all_always_needs_recompute(self):
        assert needs_recompute(checkpoint_at=None, latest_signal_at=None) is True
        assert needs_recompute(checkpoint_at=None, latest_signal_at=PREVIOUS) is True

    def test_a_signal_newer_than_the_checkpoint_needs_recompute(self):
        assert needs_recompute(checkpoint_at=PREVIOUS, latest_signal_at=NOW) is True

    def test_a_signal_older_than_or_equal_to_the_checkpoint_does_not_need_recompute(self):
        assert needs_recompute(checkpoint_at=NOW, latest_signal_at=PREVIOUS) is False
        assert needs_recompute(checkpoint_at=NOW, latest_signal_at=NOW) is False

    def test_no_signal_at_all_with_a_real_checkpoint_never_needs_recompute(self):
        """Critical requirement: mere elapsed time is never, by itself,
        a reason to recompute -- there is no "N days since last run"
        branch in this function at all."""
        assert needs_recompute(checkpoint_at=PREVIOUS, latest_signal_at=None) is False


class TestDeriveOperationalStatus:
    def test_no_run_ever_is_unknown(self):
        assert derive_operational_status(None, pending_count=0) is OperationalMonitoringStatus.UNKNOWN

    def test_a_running_run_always_wins_even_with_pending_work(self):
        record = _run_record(status=OperationalRunStatus.RUNNING)
        assert derive_operational_status(record, pending_count=5) is OperationalMonitoringStatus.RUNNING

    def test_a_failed_last_run_wins_over_pending_work(self):
        record = _run_record(status=OperationalRunStatus.FAILED, failures=(MonitoringFailure("c1", "NVDA", "boom"),))
        assert derive_operational_status(record, pending_count=0) is OperationalMonitoringStatus.FAILED

    def test_a_completed_run_with_pending_work_is_pending(self):
        record = _run_record(status=OperationalRunStatus.COMPLETED)
        assert derive_operational_status(record, pending_count=2) is OperationalMonitoringStatus.PENDING

    def test_a_completed_run_with_no_pending_work_is_up_to_date(self):
        record = _run_record(status=OperationalRunStatus.COMPLETED)
        assert derive_operational_status(record, pending_count=0) is OperationalMonitoringStatus.UP_TO_DATE

"""Tests for `atlas.alpha.decision_readiness.engine` -- every rule
exercised in isolation, plus the full priority-waterfall ordering
(each higher-priority condition must win over every lower one it's
combined with)."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.decision_readiness.engine import (
    READINESS_PROXIMITY_RANK,
    ReadinessInputs,
    compare_readiness,
    derive_decision_readiness,
    detect_blockers,
    detect_readiness_change,
    detect_supporting_reasons,
    summarize_readiness,
)
from atlas.alpha.decision_readiness.models import (
    DecisionBlockerKind,
    DecisionReadiness,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
)
from atlas.alpha.decision_support import DecisionSupportLevel
from atlas.alpha.coverage.models import ConfidenceLevel
from atlas.alpha.ingestion.engine import DataFreshnessStatus
from atlas.alpha.stance.models import StanceLevel
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.analysis_engine.valuation.support import ValuationSupportGapKind, ValuationSupportStatus

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _inputs(**overrides) -> ReadinessInputs:
    """A fully "healthy, ready" baseline -- every test overrides only
    the field(s) it actually cares about."""
    base = dict(
        coverage_level=AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE,
        confidence_level=ConfidenceLevel.HIGH,
        decision_support_level=DecisionSupportLevel.THESIS_INTACT,
        valuation_support_status=ValuationSupportStatus.SUPPORTED,
        valuation_support_gap=None,
        stance_level=StanceLevel.MAINTAIN,
        observation_count=3,
        has_conflicting_evidence_finding=False,
        no_support_finding_count=0,
        has_critical_dependency=False,
        is_monitoring_pending=False,
        last_monitored_at=NOW,
        last_run_failed_for_case=False,
        data_freshness_status=DataFreshnessStatus.WAITING_FOR_NEW_DATA,
    )
    base.update(overrides)
    return ReadinessInputs(**base)


class TestDeriveDecisionReadiness:
    def test_healthy_baseline_is_ready(self):
        assert derive_decision_readiness(_inputs()) is DecisionReadinessStatus.READY

    def test_no_coverage_is_unknown_regardless_of_everything_else(self):
        inputs = _inputs(coverage_level=AnalysisCoverageLevel.NO_COVERAGE, has_conflicting_evidence_finding=True)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.UNKNOWN

    def test_never_monitored_is_unavailable(self):
        inputs = _inputs(last_monitored_at=None)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.UNAVAILABLE

    def test_last_run_failed_is_unavailable(self):
        inputs = _inputs(last_run_failed_for_case=True)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.UNAVAILABLE

    def test_no_data_source_is_unavailable(self):
        inputs = _inputs(data_freshness_status=DataFreshnessStatus.NO_DATA_SOURCE)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.UNAVAILABLE

    def test_unavailable_outranks_blocked(self):
        inputs = _inputs(last_monitored_at=None, has_conflicting_evidence_finding=True)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.UNAVAILABLE

    def test_conflicting_evidence_is_blocked(self):
        inputs = _inputs(has_conflicting_evidence_finding=True)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.BLOCKED

    def test_avoid_decision_stance_is_blocked(self):
        inputs = _inputs(stance_level=StanceLevel.AVOID_DECISION)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.BLOCKED

    def test_critical_dependency_is_blocked(self):
        inputs = _inputs(has_critical_dependency=True)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.BLOCKED

    def test_blocked_outranks_waiting(self):
        inputs = _inputs(has_conflicting_evidence_finding=True, is_monitoring_pending=True)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.BLOCKED

    def test_monitoring_pending_is_waiting(self):
        inputs = _inputs(is_monitoring_pending=True)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.WAITING

    def test_waiting_for_analysis_is_waiting(self):
        inputs = _inputs(data_freshness_status=DataFreshnessStatus.WAITING_FOR_ANALYSIS)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.WAITING

    def test_partial_coverage_is_waiting(self):
        inputs = _inputs(coverage_level=AnalysisCoverageLevel.PARTIAL_COVERAGE)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.WAITING

    def test_insufficient_evidence_decision_support_is_waiting(self):
        inputs = _inputs(decision_support_level=DecisionSupportLevel.INSUFFICIENT_EVIDENCE)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.WAITING

    def test_waiting_outranks_almost_ready(self):
        inputs = _inputs(is_monitoring_pending=True, confidence_level=ConfidenceLevel.LIMITED)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.WAITING

    def test_limited_confidence_is_almost_ready(self):
        inputs = _inputs(confidence_level=ConfidenceLevel.LIMITED)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.ALMOST_READY

    def test_very_limited_confidence_is_almost_ready(self):
        inputs = _inputs(confidence_level=ConfidenceLevel.VERY_LIMITED)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.ALMOST_READY

    def test_missing_confidence_is_almost_ready(self):
        inputs = _inputs(confidence_level=None)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.ALMOST_READY

    def test_moderate_confidence_is_ready(self):
        inputs = _inputs(confidence_level=ConfidenceLevel.MODERATE)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.READY

    def test_a_real_blocker_never_coexists_with_ready_or_almost_ready(self):
        """Live Verification finding (Deliverable 15) -- `detect_blockers`
        checks conditions (`unknown_valuation`/`missing_thesis_evidence`)
        that `derive_decision_readiness` did not originally consider,
        so a Case could be reported `READY` while real blockers were
        still listed -- an incoherent, untrustworthy result. Status
        must always be derived from the same blocker set."""
        inputs = _inputs(valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT)
        status = derive_decision_readiness(inputs)
        assert status not in (DecisionReadinessStatus.READY, DecisionReadinessStatus.ALMOST_READY)
        assert status is DecisionReadinessStatus.WAITING

    def test_missing_thesis_evidence_alone_produces_waiting_not_ready(self):
        inputs = _inputs(no_support_finding_count=1)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.WAITING

    def test_missing_observation_alone_produces_waiting_not_ready(self):
        inputs = _inputs(observation_count=0)
        assert derive_decision_readiness(inputs) is DecisionReadinessStatus.WAITING


class TestDetectBlockers:
    def test_healthy_baseline_has_no_blockers(self):
        assert detect_blockers(_inputs()) == ()

    def test_each_real_condition_produces_its_own_named_blocker(self):
        cases = [
            (dict(last_monitored_at=None), DecisionBlockerKind.NEVER_EVALUATED),
            (dict(last_run_failed_for_case=True), DecisionBlockerKind.MONITORING_FAILED),
            (dict(data_freshness_status=DataFreshnessStatus.NO_DATA_SOURCE), DecisionBlockerKind.NO_DATA_SOURCE),
            (dict(has_conflicting_evidence_finding=True), DecisionBlockerKind.CONFLICTING_EVIDENCE),
            (dict(stance_level=StanceLevel.AVOID_DECISION), DecisionBlockerKind.AVOID_DECISION_SIGNAL),
            (dict(has_critical_dependency=True), DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),
            (dict(is_monitoring_pending=True), DecisionBlockerKind.MONITORING_PENDING),
            (dict(data_freshness_status=DataFreshnessStatus.WAITING_FOR_ANALYSIS), DecisionBlockerKind.OPERATIONAL_FRESHNESS_OUTDATED),
            (dict(coverage_level=AnalysisCoverageLevel.PARTIAL_COVERAGE), DecisionBlockerKind.COVERAGE_INCOMPLETE),
            (dict(decision_support_level=DecisionSupportLevel.INSUFFICIENT_EVIDENCE), DecisionBlockerKind.INSUFFICIENT_EVIDENCE),
            (dict(valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT), DecisionBlockerKind.UNKNOWN_VALUATION),
            (dict(observation_count=0), DecisionBlockerKind.MISSING_OBSERVATION),
            (dict(no_support_finding_count=2), DecisionBlockerKind.MISSING_THESIS_EVIDENCE),
        ]
        for overrides, expected_kind in cases:
            blockers = detect_blockers(_inputs(**overrides))
            assert any(b.kind is expected_kind for b in blockers), f"{overrides} did not produce {expected_kind}"

    def test_missing_thesis_evidence_carries_the_real_count(self):
        blockers = detect_blockers(_inputs(no_support_finding_count=3))
        matching = [b for b in blockers if b.kind is DecisionBlockerKind.MISSING_THESIS_EVIDENCE]
        assert matching[0].detail == 3

    def test_multiple_real_blockers_are_all_reported_together(self):
        inputs = _inputs(is_monitoring_pending=True, coverage_level=AnalysisCoverageLevel.PARTIAL_COVERAGE)
        blockers = detect_blockers(inputs)
        kinds = {b.kind for b in blockers}
        assert kinds == {DecisionBlockerKind.MONITORING_PENDING, DecisionBlockerKind.COVERAGE_INCOMPLETE}

    def test_a_genuinely_mixed_scenario_envelope_is_never_unknown_valuation(self):
        """Atlas Intelligence Sprint 12 (Analysis Coverage Expansion,
        Deliverable 5) -- audited against a real company (AAPL):
        `SCENARIO_ENVELOPE_INCONCLUSIVE` means Atlas built a real,
        complete forward-return range that genuinely straddles zero,
        not an unanswered question. Flagging it `unknown_valuation`
        would overstate the gap."""
        inputs = _inputs(
            valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT,
            valuation_support_gap=ValuationSupportGapKind.SCENARIO_ENVELOPE_INCONCLUSIVE,
        )
        blockers = detect_blockers(inputs)
        assert not any(b.kind is DecisionBlockerKind.UNKNOWN_VALUATION for b in blockers)

    def test_conflicting_valuation_proofs_is_also_never_unknown_valuation(self):
        inputs = _inputs(
            valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT,
            valuation_support_gap=ValuationSupportGapKind.CONFLICTING_VALUATION_PROOFS,
        )
        blockers = detect_blockers(inputs)
        assert not any(b.kind is DecisionBlockerKind.UNKNOWN_VALUATION for b in blockers)

    def test_a_genuine_data_shortfall_gap_still_blocks_as_unknown_valuation(self):
        inputs = _inputs(
            valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT,
            valuation_support_gap=ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA,
        )
        blockers = detect_blockers(inputs)
        assert any(b.kind is DecisionBlockerKind.UNKNOWN_VALUATION for b in blockers)


class TestDetectSupportingReasons:
    def test_healthy_baseline_has_every_positive_reason(self):
        reasons = detect_supporting_reasons(_inputs())
        kinds = {r.kind for r in reasons}
        assert kinds == {
            DecisionReadinessReasonKind.SUBSTANTIAL_COVERAGE_REACHED,
            DecisionReadinessReasonKind.CONFIDENCE_ESTABLISHED,
            DecisionReadinessReasonKind.NO_CONFLICTS_FOUND,
            DecisionReadinessReasonKind.MONITORING_CURRENT,
            DecisionReadinessReasonKind.DECISION_SUPPORT_REACHED,
            DecisionReadinessReasonKind.NO_CRITICAL_DEPENDENCIES,
        }

    def test_a_real_problem_removes_its_own_positive_reason(self):
        reasons = detect_supporting_reasons(_inputs(has_conflicting_evidence_finding=True))
        kinds = {r.kind for r in reasons}
        assert DecisionReadinessReasonKind.NO_CONFLICTS_FOUND not in kinds


class TestSummarizeReadiness:
    def test_primary_blocker_is_the_first_entry(self):
        readiness = DecisionReadiness(
            case_id="c1",
            status=DecisionReadinessStatus.WAITING,
            blockers=detect_blockers(_inputs(is_monitoring_pending=True, coverage_level=AnalysisCoverageLevel.PARTIAL_COVERAGE)),
            supporting_reasons=(),
            generated_at=NOW,
        )
        summary = summarize_readiness(readiness)
        assert summary.primary_blocker == readiness.blockers[0]

    def test_no_blockers_means_no_primary_blocker(self):
        readiness = DecisionReadiness(case_id="c1", status=DecisionReadinessStatus.READY, blockers=(), supporting_reasons=(), generated_at=NOW)
        assert summarize_readiness(readiness).primary_blocker is None


class TestCompareReadiness:
    def _readiness(self, case_id: str, status: DecisionReadinessStatus, blockers=()) -> DecisionReadiness:
        return DecisionReadiness(case_id=case_id, status=status, blockers=blockers, supporting_reasons=(), generated_at=NOW)

    def test_ready_is_closer_than_waiting(self):
        a = self._readiness("a", DecisionReadinessStatus.READY)
        b = self._readiness("b", DecisionReadinessStatus.WAITING)
        comparison = compare_readiness(a, b)
        assert comparison.closer_case_id == "a"

    def test_identical_status_is_an_honest_tie(self):
        a = self._readiness("a", DecisionReadinessStatus.WAITING)
        b = self._readiness("b", DecisionReadinessStatus.WAITING)
        comparison = compare_readiness(a, b)
        assert comparison.closer_case_id is None

    def test_differing_blocker_kinds_is_the_symmetric_difference(self):
        from atlas.alpha.decision_readiness.models import DecisionBlocker

        a = self._readiness("a", DecisionReadinessStatus.BLOCKED, blockers=(DecisionBlocker(DecisionBlockerKind.CONFLICTING_EVIDENCE),))
        b = self._readiness(
            "b",
            DecisionReadinessStatus.BLOCKED,
            blockers=(DecisionBlocker(DecisionBlockerKind.CONFLICTING_EVIDENCE), DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING)),
        )
        comparison = compare_readiness(a, b)
        assert comparison.differing_blocker_kinds == (DecisionBlockerKind.MONITORING_PENDING,)

    def test_proximity_rank_is_fully_ordered(self):
        assert list(READINESS_PROXIMITY_RANK.keys()) == list(DecisionReadinessStatus)


class TestDetectReadinessChange:
    def _readiness(self, status: DecisionReadinessStatus, blockers=()) -> DecisionReadiness:
        return DecisionReadiness(case_id="c1", status=status, blockers=blockers, supporting_reasons=(), generated_at=NOW)

    def test_no_previous_computation_produces_no_change(self):
        current = self._readiness(DecisionReadinessStatus.READY)
        assert detect_readiness_change(None, current, detected_at=NOW) is None

    def test_identical_status_and_blockers_produces_no_change(self):
        previous = self._readiness(DecisionReadinessStatus.WAITING)
        current = self._readiness(DecisionReadinessStatus.WAITING)
        assert detect_readiness_change(previous, current, detected_at=NOW) is None

    def test_a_resolved_blocker_is_reported_even_when_status_stays_the_same(self):
        """Live Verification finding (Deliverable 15) -- a real
        transition can happen without any overall status change (e.g.
        `UNAVAILABLE` before and after, but `monitoring_pending`
        resolved underneath a persisting `no_data_source`)."""
        from atlas.alpha.decision_readiness.models import DecisionBlocker

        previous = self._readiness(
            DecisionReadinessStatus.UNAVAILABLE,
            blockers=(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE), DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING)),
        )
        current = self._readiness(DecisionReadinessStatus.UNAVAILABLE, blockers=(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),))
        change = detect_readiness_change(previous, current, detected_at=NOW)
        assert change is not None
        assert change.previous_status is DecisionReadinessStatus.UNAVAILABLE
        assert change.current_status is DecisionReadinessStatus.UNAVAILABLE
        assert change.resolved_blockers == (DecisionBlockerKind.MONITORING_PENDING,)
        assert change.new_blockers == ()

    def test_a_real_transition_is_reported(self):
        from atlas.alpha.decision_readiness.models import DecisionBlocker

        previous = self._readiness(DecisionReadinessStatus.WAITING, blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),))
        current = self._readiness(DecisionReadinessStatus.READY, blockers=())
        change = detect_readiness_change(previous, current, detected_at=NOW)
        assert change is not None
        assert change.previous_status is DecisionReadinessStatus.WAITING
        assert change.current_status is DecisionReadinessStatus.READY
        assert change.resolved_blockers == (DecisionBlockerKind.MONITORING_PENDING,)
        assert change.new_blockers == ()

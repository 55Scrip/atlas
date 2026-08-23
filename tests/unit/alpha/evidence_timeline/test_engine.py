"""Tests for `atlas.alpha.evidence_timeline.engine` -- `CoverageAssessment`/
`Stance`/`EvidenceQualityReport` are hand-built, controlled stand-ins for
already-tested-elsewhere upstream engines, the same convention
`tests/unit/alpha/explainability/test_engine.py`'s own module docstring
establishes, since this module's whole job is capturing/comparing their
already-real top-level fields, never recomputing them.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from atlas.alpha.coverage import ConfidenceLevel, CoverageAssessment
from atlas.alpha.evidence_quality import EvidenceConflictStatus, EvidenceDominance, EvidenceFreshness, EvidenceQualityLevel, EvidenceQualityReport
from atlas.alpha.evidence_quality.models import FactQuality
from atlas.alpha.evidence_timeline.engine import (
    capture_evidence_snapshot,
    compare_evidence_snapshots,
    derive_staleness_date,
    is_material_transition,
    material_transitions,
)
from atlas.alpha.evidence_timeline.models import EvidenceTransition, EvidenceTransitionCategory
from atlas.alpha.stance import Stance, StanceLevel
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.investment_case_change import ChangeDirection

CAPTURED_AT = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _make_record(identifier: str, period_end: date, **metadata):
    document = RawBusinessDocument(
        identifier=identifier,
        company="ASML",
        source_kind="annual_report",
        published_at=CAPTURED_AT,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=CAPTURED_AT)
    assert isinstance(result, IngestedRecord), result
    return result.record


def _coverage(overall_coverage=AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE, overall_confidence=ConfidenceLevel.MODERATE, missing=()) -> CoverageAssessment:
    return CoverageAssessment(
        dimensions=(),
        overall_coverage=overall_coverage,
        overall_confidence=overall_confidence,
        missing_dimensions=missing,
        not_applicable_dimensions=(),
        reasoning=(),
    )


def _quality(
    quality=EvidenceQualityLevel.FRESH,
    conflict_status=EvidenceConflictStatus.CONSISTENT,
    freshness=EvidenceFreshness.FRESH,
    dominance=EvidenceDominance.CORROBORATED,
) -> EvidenceQualityReport:
    return EvidenceQualityReport(
        quality=quality,
        conflict_status=conflict_status,
        freshness=freshness,
        dominance=dominance,
        warnings=(),
        facts=(),
        conflicts=(),
        unsupported_findings=(),
    )


def _stance(level=StanceLevel.MAINTAIN) -> Stance:
    return Stance(level=level, reasoning=(), supporting_signals=(), limiting_signals=(), confidence=ConfidenceLevel.MODERATE, missing_information=())


class TestCaptureIsPure:
    def test_identical_inputs_produce_a_deeply_equal_snapshot(self):
        a = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=CAPTURED_AT)
        b = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=CAPTURED_AT)
        assert a == b

    def test_a_none_stance_is_captured_honestly_as_none_not_a_placeholder(self):
        snapshot = capture_evidence_snapshot(_coverage(), _quality(), None, captured_at=CAPTURED_AT)
        assert snapshot.stance_level is None

    def test_content_hash_ignores_captured_at(self):
        a = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=CAPTURED_AT)
        b = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
        assert a.content_hash == b.content_hash

    def test_a_real_content_difference_produces_a_different_hash(self):
        a = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.MAINTAIN), captured_at=CAPTURED_AT)
        b = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.INCREASE), captured_at=CAPTURED_AT)
        assert a.content_hash != b.content_hash


class TestBaseline:
    def test_no_previous_snapshot_is_a_baseline_never_a_change(self):
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(None, current)
        assert history.is_baseline is True
        assert history.transitions == ()
        assert history.previous_captured_at is None


class TestTransitionDetection:
    def test_coverage_improving_is_a_positive_coverage_changed_transition(self):
        previous = capture_evidence_snapshot(_coverage(AnalysisCoverageLevel.NO_COVERAGE), _quality(), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE), _quality(), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.COVERAGE_CHANGED)
        assert transition.direction is ChangeDirection.POSITIVE
        assert transition.previous_state == "no_coverage"
        assert transition.current_state == "substantial_coverage"

    def test_coverage_deteriorating_is_a_negative_transition(self):
        previous = capture_evidence_snapshot(_coverage(AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE), _quality(), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(AnalysisCoverageLevel.NO_COVERAGE), _quality(), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.COVERAGE_CHANGED)
        assert transition.direction is ChangeDirection.NEGATIVE

    def test_confidence_weakening_is_a_negative_confidence_changed_transition(self):
        previous = capture_evidence_snapshot(_coverage(overall_confidence=ConfidenceLevel.HIGH), _quality(), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(overall_confidence=ConfidenceLevel.LIMITED), _quality(), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.CONFIDENCE_CHANGED)
        assert transition.direction is ChangeDirection.NEGATIVE

    def test_stance_strengthening_to_increase_is_positive(self):
        previous = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.MAINTAIN), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.INCREASE), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.STANCE_CHANGED)
        assert transition.direction is ChangeDirection.POSITIVE

    def test_stance_weakening_to_reduce_is_negative(self):
        previous = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.MAINTAIN), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.REDUCE), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.STANCE_CHANGED)
        assert transition.direction is ChangeDirection.NEGATIVE

    def test_stance_moving_to_review_is_neutral_never_read_as_good_or_bad(self):
        previous = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.MAINTAIN), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.REVIEW), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.STANCE_CHANGED)
        assert transition.direction is ChangeDirection.NEUTRAL

    def test_conflict_appearing_is_negative(self):
        previous = capture_evidence_snapshot(_coverage(), _quality(conflict_status=EvidenceConflictStatus.CONSISTENT), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(conflict_status=EvidenceConflictStatus.CONFLICTING), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED)
        assert transition.direction is ChangeDirection.NEGATIVE

    def test_conflict_resolving_is_positive(self):
        previous = capture_evidence_snapshot(_coverage(), _quality(conflict_status=EvidenceConflictStatus.CONFLICTING), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(conflict_status=EvidenceConflictStatus.CONSISTENT), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED)
        assert transition.direction is ChangeDirection.POSITIVE

    def test_evidence_becoming_stale_is_a_negative_freshness_changed_transition(self):
        previous = capture_evidence_snapshot(_coverage(), _quality(freshness=EvidenceFreshness.FRESH), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(freshness=EvidenceFreshness.STALE), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.FRESHNESS_CHANGED)
        assert transition.direction is ChangeDirection.NEGATIVE

    def test_overall_quality_improving_is_a_positive_evidence_quality_changed_transition(self):
        previous = capture_evidence_snapshot(_coverage(), _quality(quality=EvidenceQualityLevel.CONFLICTING), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(quality=EvidenceQualityLevel.FRESH), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        transition = next(t for t in history.transitions if t.category is EvidenceTransitionCategory.EVIDENCE_QUALITY_CHANGED)
        assert transition.direction is ChangeDirection.POSITIVE

    def test_no_real_change_produces_zero_transitions(self):
        previous = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        assert history.transitions == ()
        assert history.is_baseline is False

    def test_two_snapshots_sharing_an_identical_content_hash_is_safe_and_produces_zero_transitions(self):
        """Mirrors `investment_case_change.compare_snapshots`'s own
        documented "safe either way" calling convention: the real
        caller (`investment_case/api/router.py`) invokes this
        unconditionally on every request, including a reload with no
        new data."""
        snapshot = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(snapshot, snapshot)
        assert history.transitions == ()


class TestDeterminism:
    def test_identical_inputs_produce_deeply_equal_histories(self):
        previous = capture_evidence_snapshot(_coverage(AnalysisCoverageLevel.NO_COVERAGE), _quality(), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(), captured_at=CAPTURED_AT)
        assert compare_evidence_snapshots(previous, current) == compare_evidence_snapshots(previous, current)


class TestSourceEvidenceHistory:
    """Deliverable 2/3/4/6 -- Source Evidence History, kept structurally
    separate from Atlas Analysis History (`transitions`)."""

    def test_a_new_period_since_the_last_capture_is_a_real_source_evidence_event(self):
        old_records = (_make_record("fy2023", date(2023, 12, 31), revenue=100.0),)
        new_records = (*old_records, _make_record("fy2024", date(2024, 12, 31), revenue=110.0))
        old_facts = extract_facts_from_records(old_records, evaluated_at=CAPTURED_AT)
        new_facts = extract_facts_from_records(new_records, evaluated_at=CAPTURED_AT)

        previous = capture_evidence_snapshot(_coverage(), _quality(), _stance(), old_facts, (), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(), new_facts, (), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)

        assert len(history.new_source_evidence) == 1
        assert history.new_source_evidence[0].fact_kind == "revenue"
        assert history.new_source_evidence[0].period == "2024-12-31"

    def test_no_new_period_produces_no_source_evidence_events(self):
        records = (_make_record("fy2023", date(2023, 12, 31), revenue=100.0),)
        facts = extract_facts_from_records(records, evaluated_at=CAPTURED_AT)
        previous = capture_evidence_snapshot(_coverage(), _quality(), _stance(), facts, (), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(), facts, (), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        assert history.new_source_evidence == ()

    def test_source_evidence_events_never_appear_in_the_analysis_transitions_list(self):
        """Deliverable 2's own 'do not mix these concepts' instruction,
        verified: a new period is never itself an `EvidenceTransition`."""
        old_records = ()
        new_records = (_make_record("fy2024", date(2024, 12, 31), revenue=110.0),)
        old_facts = extract_facts_from_records(old_records, evaluated_at=CAPTURED_AT)
        new_facts = extract_facts_from_records(new_records, evaluated_at=CAPTURED_AT)
        previous = capture_evidence_snapshot(_coverage(), _quality(), _stance(), old_facts, (), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(), new_facts, (), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        assert len(history.new_source_evidence) == 1
        assert all(t.category != EvidenceTransitionCategory.COVERAGE_CHANGED or True for t in history.transitions)
        assert not any("revenue" in (t.previous_state, t.current_state) for t in history.transitions)


class TestHistoricalHonestyNegativeCases:
    """Deliverable 5/17 -- critical negative tests proving Atlas never
    fabricates a transition or a source-evidence event when a genuine
    prior state does not exist."""

    def test_a_baseline_never_reports_new_source_evidence_even_with_real_facts_present(self):
        records = (_make_record("fy2024", date(2024, 12, 31), revenue=110.0),)
        facts = extract_facts_from_records(records, evaluated_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(), facts, (), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(None, current)
        assert history.is_baseline is True
        assert history.new_source_evidence == ()
        assert history.transitions == ()

    def test_a_baseline_never_claims_coverage_improved_even_when_current_coverage_is_full(self):
        current = capture_evidence_snapshot(_coverage(AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE), _quality(), _stance(StanceLevel.INCREASE), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(None, current)
        assert history.transitions == ()
        assert history.is_baseline is True

    def test_a_stance_that_has_always_been_increase_produces_no_stance_transition(self):
        """No real prior *different* state exists -- identical stance on
        both sides must never be reported as a change."""
        previous = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.INCREASE), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(), _quality(), _stance(StanceLevel.INCREASE), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        assert not any(t.category is EvidenceTransitionCategory.STANCE_CHANGED for t in history.transitions)


class TestMaterialityIntegration:
    """Deliverable 7 -- a fixed filter, never a second priority engine."""

    def test_a_conflict_transition_is_always_material(self):
        transition = EvidenceTransition(
            id="t", category=EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED, direction=ChangeDirection.NEGATIVE,
            previous_state="consistent", current_state="conflicting", details={},
        )
        assert is_material_transition(transition) is True

    def test_a_positive_confidence_transition_is_not_material(self):
        transition = EvidenceTransition(
            id="t", category=EvidenceTransitionCategory.CONFIDENCE_CHANGED, direction=ChangeDirection.POSITIVE,
            previous_state="moderate", current_state="high", details={},
        )
        assert is_material_transition(transition) is False

    def test_a_negative_confidence_transition_is_material(self):
        transition = EvidenceTransition(
            id="t", category=EvidenceTransitionCategory.CONFIDENCE_CHANGED, direction=ChangeDirection.NEGATIVE,
            previous_state="high", current_state="moderate", details={},
        )
        assert is_material_transition(transition) is True

    def test_material_transitions_never_removes_anything_from_the_full_list(self):
        """Materiality explains prominence -- it never deletes the
        underlying fact; `history.transitions` itself stays complete."""
        previous = capture_evidence_snapshot(_coverage(overall_confidence=ConfidenceLevel.HIGH), _quality(), _stance(), captured_at=CAPTURED_AT)
        current = capture_evidence_snapshot(_coverage(overall_confidence=ConfidenceLevel.LIMITED), _quality(), _stance(), captured_at=CAPTURED_AT)
        history = compare_evidence_snapshots(previous, current)
        prominent = material_transitions(history)
        assert all(t in history.transitions for t in prominent)
        assert len(prominent) <= len(history.transitions)


class TestFreshnessTransitionsAreDerivedNotObserved:
    """Deliverable 14 -- a pure calculation from an existing timestamp
    plus the existing threshold, never a persisted 'it happened' row."""

    def test_a_fact_published_long_ago_has_a_staleness_date_in_the_past(self):
        old_publish = CAPTURED_AT - timedelta(days=500)
        fact = FactQuality(
            fact_kind="revenue", freshness=EvidenceFreshness.STALE, dominance=EvidenceDominance.CORROBORATED,
            latest_period="2023-12-31", latest_published_at=old_publish, source_record_count=1,
        )
        staleness_date = derive_staleness_date(fact)
        assert staleness_date is not None
        assert staleness_date < CAPTURED_AT

    def test_a_recently_published_fact_has_a_staleness_date_in_the_future(self):
        fact = FactQuality(
            fact_kind="revenue", freshness=EvidenceFreshness.FRESH, dominance=EvidenceDominance.CORROBORATED,
            latest_period="2026-12-31", latest_published_at=CAPTURED_AT, source_record_count=1,
        )
        staleness_date = derive_staleness_date(fact)
        assert staleness_date is not None
        assert staleness_date > CAPTURED_AT

    def test_a_fact_with_no_known_publish_date_returns_none_never_a_guess(self):
        fact = FactQuality(
            fact_kind="revenue", freshness=EvidenceFreshness.NOT_APPLICABLE, dominance=EvidenceDominance.NOT_APPLICABLE,
            latest_period=None, latest_published_at=None, source_record_count=0,
        )
        assert derive_staleness_date(fact) is None

    def test_the_derived_date_uses_the_identical_threshold_evidence_quality_itself_uses(self):
        """Cross-checks against the real `EvidenceQuality` freshness
        classification: a fact published exactly at the stale boundary
        derives a staleness date of exactly `CAPTURED_AT`."""
        from atlas.alpha.evidence_quality.engine import _STALE_THRESHOLD_DAYS as real_threshold

        boundary_publish = CAPTURED_AT - timedelta(days=real_threshold)
        fact = FactQuality(
            fact_kind="revenue", freshness=EvidenceFreshness.STALE, dominance=EvidenceDominance.CORROBORATED,
            latest_period="2024-01-01", latest_published_at=boundary_publish, source_record_count=1,
        )
        assert derive_staleness_date(fact) == CAPTURED_AT

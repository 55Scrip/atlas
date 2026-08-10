"""Tests for `atlas.analysis_engine.investment_case_change` (Investment
Case Monitoring & Change Intelligence v1).

Two layers, mirroring `test_investment_case_synthesis.py`'s own split:

- `TestCompareSnapshots*` classes build `AnalyticalSnapshot`s directly
  (via `_snapshot`) to exercise every documented transition rule with
  exact, deterministic control -- `content_hash` is irrelevant to
  `compare_snapshots` itself (only the repository layer's own
  idempotency check reads it; see `_snapshot`'s own docstring), so a
  placeholder value is used throughout.
- `TestCaptureSnapshotEndToEnd` exercises `capture_snapshot` through the
  real `assemble_analysis` entry point with real `BusinessRecord`s, the
  same "full BusinessRecord -> ... -> CanonicalAnalysis chain" style
  `test_investment_case_synthesis.py` already establishes -- never a
  hand-built fake `CanonicalAnalysis`.
"""
from __future__ import annotations

import dataclasses
from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.investment_case_change import (
    AnalyticalSnapshot,
    ChangeCategory,
    ChangeDirection,
    ThesisImpact,
    capture_snapshot,
    compare_snapshots,
)
from atlas.analysis_engine.pipeline import assemble_analysis
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)

_ALL_INSUFFICIENT_BUSINESS = (
    ("business_model", "insufficient_input", "business_finding:business_model"),
    ("capital_allocation", "insufficient_input", "business_finding:capital_allocation"),
    ("competitive_position", "insufficient_input", "business_finding:competitive_position"),
    ("durability", "insufficient_input", "business_finding:durability"),
    ("growth", "insufficient_input", "business_finding:growth"),
    ("management", "insufficient_input", "business_finding:management"),
)
_ALL_INSUFFICIENT_RISK = (
    ("business_risk", "insufficient_input", "risk_finding:business_risk"),
    ("financial_risk", "insufficient_input", "risk_finding:financial_risk"),
    ("valuation_risk", "insufficient_input", "risk_finding:valuation_risk"),
)


def _snapshot(
    *,
    business=_ALL_INSUFFICIENT_BUSINESS,
    risk=_ALL_INSUFFICIENT_RISK,
    valuation_status="insufficient_input",
    current_yield=None,
    strengths=(),
    risk_highlights=(),
    open_questions=(),
    captured_at=_T0,
) -> AnalyticalSnapshot:
    """`content_hash` is a fixed placeholder -- `compare_snapshots` never
    reads it (only `atlas.alpha.investment_case_change`'s own repository
    does, for its own, separately-tested idempotency check)."""
    return AnalyticalSnapshot(
        business_category_states=tuple(sorted(business)),
        risk_category_states=tuple(sorted(risk)),
        valuation_status=valuation_status,
        valuation_finding_id="valuation_finding:fcf_yield_relative",
        current_yield=current_yield,
        strength_kinds=tuple(sorted(strengths)),
        risk_highlight_kinds=tuple(sorted(risk_highlights)),
        open_question_origins=tuple(sorted(open_questions)),
        atlas_thesis_narrative="placeholder thesis narrative",
        atlas_thesis_posture="strengths_and_risks",
        content_hash="placeholder",
        captured_at=captured_at,
    )


def _with_business(base: AnalyticalSnapshot, category: str, status: str, finding_id: str | None = None) -> AnalyticalSnapshot:
    finding_id = finding_id or f"business_finding:{category}"
    updated = tuple((c, status if c == category else s, finding_id if c == category else fid) for c, s, fid in base.business_category_states)
    return dataclasses.replace(base, business_category_states=updated)


def _with_risk(base: AnalyticalSnapshot, category: str, status: str, finding_id: str | None = None) -> AnalyticalSnapshot:
    finding_id = finding_id or f"risk_finding:{category}"
    updated = tuple((c, status if c == category else s, finding_id if c == category else fid) for c, s, fid in base.risk_category_states)
    return dataclasses.replace(base, risk_category_states=updated)


class TestBaselineBehaviour:
    """Scenario 1: first analysis creates a baseline but zero change findings."""

    def test_no_previous_snapshot_is_a_baseline_with_zero_changes(self):
        current = _snapshot()
        result = compare_snapshots(None, current)
        assert result.is_baseline is True
        assert result.changes == ()
        assert result.thesis_impact is ThesisImpact.UNCHANGED
        assert result.previous_captured_at is None
        assert result.current_captured_at == _T0

    def test_baseline_narrative_says_baseline_not_a_change(self):
        result = compare_snapshots(None, _snapshot())
        assert "baseline" in result.summary_narrative.lower()


class TestUnchangedAnalysis:
    """Scenario 2: re-running unchanged analysis creates zero meaningful changes."""

    def test_identical_snapshots_produce_zero_changes(self):
        previous = _snapshot(captured_at=_T0)
        current = _snapshot(captured_at=_T1)
        result = compare_snapshots(previous, current)
        assert result.is_baseline is False
        assert result.changes == ()
        assert result.thesis_impact is ThesisImpact.UNCHANGED
        assert "no material change" in result.summary_narrative.lower()

    def test_identical_populated_snapshots_produce_zero_changes(self):
        populated = _snapshot(
            business=tuple(
                (c, "strong", fid) if c == "growth" else (c, s, fid) for c, s, fid in _ALL_INSUFFICIENT_BUSINESS
            ),
            strengths=("growth",),
            open_questions=("scenario_valuation_unavailable",),
        )
        result = compare_snapshots(populated, populated)
        assert result.changes == ()


class TestGrowthTransitions:
    """Scenarios 3-4: Growth STRONG<->MODERATE."""

    def test_strong_to_moderate_is_negative(self):
        previous = _with_business(_snapshot(), "growth", "strong")
        current = _with_business(_snapshot(), "growth", "moderate")
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.GROWTH_CHANGED
        assert change.direction is ChangeDirection.NEGATIVE
        assert change.previous_state == "strong"
        assert change.current_state == "moderate"

    def test_moderate_to_strong_is_positive(self):
        previous = _with_business(_snapshot(), "growth", "moderate")
        current = _with_business(_snapshot(), "growth", "strong")
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.GROWTH_CHANGED
        assert change.direction is ChangeDirection.POSITIVE


class TestCapitalAllocationTransition:
    """Scenario 5: Capital Allocation category transition."""

    def test_strong_to_weak_is_negative(self):
        previous = _with_business(_snapshot(), "capital_allocation", "strong")
        current = _with_business(_snapshot(), "capital_allocation", "weak")
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.CAPITAL_ALLOCATION_CHANGED
        assert change.direction is ChangeDirection.NEGATIVE

    def test_weak_to_strong_is_positive(self):
        previous = _with_business(_snapshot(), "capital_allocation", "weak")
        current = _with_business(_snapshot(), "capital_allocation", "strong")
        [change] = compare_snapshots(previous, current).changes
        assert change.direction is ChangeDirection.POSITIVE


class TestFinancialRiskTransition:
    """Scenario 6: Financial Risk MODERATE -> HIGH is negative."""

    def test_moderate_to_high_is_negative(self):
        previous = _with_risk(_snapshot(), "financial_risk", "moderate")
        current = _with_risk(_snapshot(), "financial_risk", "high")
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.FINANCIAL_RISK_CHANGED
        assert change.direction is ChangeDirection.NEGATIVE
        assert change.previous_state == "moderate"
        assert change.current_state == "high"

    def test_high_to_low_is_positive(self):
        previous = _with_risk(_snapshot(), "financial_risk", "high")
        current = _with_risk(_snapshot(), "financial_risk", "low")
        [change] = compare_snapshots(previous, current).changes
        assert change.direction is ChangeDirection.POSITIVE


class TestValuationTransitions:
    """Scenarios 7-8: Valuation direction."""

    def test_expensive_to_undervalued_is_positive(self):
        previous = _snapshot(valuation_status="expensive")
        current = _snapshot(valuation_status="undervalued")
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.VALUATION_CHANGED
        assert change.direction is ChangeDirection.POSITIVE

    def test_undervalued_to_expensive_is_negative(self):
        previous = _snapshot(valuation_status="undervalued")
        current = _snapshot(valuation_status="expensive")
        [change] = compare_snapshots(previous, current).changes
        assert change.direction is ChangeDirection.NEGATIVE

    def test_yield_movement_alone_within_the_same_category_is_not_a_change(self):
        """Raw numeric FCF-yield movement is deliberately excluded from
        the snapshot's own comparison identity -- see `AnalyticalSnapshot`'s
        own docstring."""
        previous = _snapshot(valuation_status="fairly_valued", current_yield=0.03)
        current = _snapshot(valuation_status="fairly_valued", current_yield=0.031)
        assert compare_snapshots(previous, current).changes == ()


class TestStrengthAddedRemoved:
    """Scenarios 9-10."""

    def test_new_strength_produces_strength_added(self):
        previous = _snapshot(strengths=())
        current = _snapshot(strengths=("growth",))
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.STRENGTH_ADDED
        assert change.direction is ChangeDirection.POSITIVE
        assert change.current_state == "growth"

    def test_lost_strength_produces_strength_removed(self):
        previous = _snapshot(strengths=("growth",))
        current = _snapshot(strengths=())
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.STRENGTH_REMOVED
        assert change.direction is ChangeDirection.NEGATIVE
        assert change.previous_state == "growth"


class TestRiskAddedRemoved:
    """Scenarios 11-12."""

    def test_new_risk_produces_risk_added(self):
        previous = _snapshot(risk_highlights=())
        current = _snapshot(risk_highlights=("financial_risk",))
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.RISK_ADDED
        assert change.direction is ChangeDirection.NEGATIVE

    def test_removed_risk_produces_risk_removed(self):
        previous = _snapshot(risk_highlights=("financial_risk",))
        current = _snapshot(risk_highlights=())
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.RISK_REMOVED
        assert change.direction is ChangeDirection.POSITIVE


class TestOpenQuestionChanges:
    """Scenarios 13-14."""

    def test_new_open_question_is_detected(self):
        previous = _snapshot(open_questions=())
        current = _snapshot(open_questions=("growth_mixed",))
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.OPEN_QUESTION_ADDED
        assert change.direction is ChangeDirection.NEGATIVE

    def test_genuinely_resolved_open_question_is_detected(self):
        """`growth_mixed` disappears because Growth moved from MODERATE
        (the condition that produced the question) to STRONG (still a
        real conclusion) -- a genuine resolution, not a coverage loss."""
        previous = _with_business(_snapshot(open_questions=("growth_mixed",)), "growth", "moderate")
        current = _with_business(_snapshot(open_questions=()), "growth", "strong")
        categories = {c.category for c in compare_snapshots(previous, current).changes}
        assert ChangeCategory.OPEN_QUESTION_RESOLVED in categories
        resolved = next(
            c for c in compare_snapshots(previous, current).changes if c.category is ChangeCategory.OPEN_QUESTION_RESOLVED
        )
        assert resolved.direction is ChangeDirection.POSITIVE
        assert resolved.previous_state == "growth_mixed"


class TestAnalyticalCoverageChanges:
    """Scenarios 15-16: coverage changes must never be read as company
    quality changes, in either direction."""

    def test_insufficient_to_evaluable_is_coverage_improvement_not_company_improvement(self):
        previous = _with_business(_snapshot(), "capital_allocation", "insufficient_input")
        current = _with_business(_snapshot(), "capital_allocation", "moderate")
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.ANALYTICAL_COVERAGE_CHANGED
        assert change.category is not ChangeCategory.CAPITAL_ALLOCATION_CHANGED
        assert change.direction is ChangeDirection.NEUTRAL

    def test_evaluable_to_insufficient_does_not_claim_the_company_deteriorated(self):
        previous = _with_business(_snapshot(), "growth", "strong")
        current = _with_business(_snapshot(), "growth", "insufficient_input")
        [change] = compare_snapshots(previous, current).changes
        assert change.category is ChangeCategory.ANALYTICAL_COVERAGE_CHANGED
        assert change.direction is ChangeDirection.NEUTRAL

    def test_coverage_loss_is_never_reported_as_a_resolved_open_question(self):
        """The open question tied to Growth disappears only because
        Growth itself regressed to `INSUFFICIENT_INPUT` -- Atlas lost
        the data, the underlying gap did not close."""
        previous = _with_business(_snapshot(open_questions=("growth_mixed",)), "growth", "moderate")
        current = _with_business(_snapshot(open_questions=()), "growth", "insufficient_input")
        categories = {c.category for c in compare_snapshots(previous, current).changes}
        assert ChangeCategory.OPEN_QUESTION_RESOLVED not in categories
        assert ChangeCategory.ANALYTICAL_COVERAGE_CHANGED in categories

    def test_not_evaluated_to_insufficient_input_is_not_a_change(self):
        """Both sides are "no real signal" -- must not fire at all."""
        previous = _with_business(_snapshot(), "durability", "not_evaluated")
        current = _with_business(_snapshot(), "durability", "insufficient_input")
        assert compare_snapshots(previous, current).changes == ()


class TestThesisImpact:
    """Scenarios 17-18: thesis impact derives from structured changes,
    and one negative change never invalidates the whole thesis."""

    def test_only_positive_changes_strengthen_the_thesis(self):
        previous = _with_business(_snapshot(), "growth", "moderate")
        current = _with_business(_snapshot(), "growth", "strong")
        result = compare_snapshots(previous, current)
        assert result.thesis_impact is ThesisImpact.STRENGTHENED

    def test_only_negative_changes_weaken_but_do_not_invalidate(self):
        previous = _with_risk(_snapshot(), "financial_risk", "moderate")
        current = _with_risk(_snapshot(), "financial_risk", "high")
        result = compare_snapshots(previous, current)
        assert result.thesis_impact is ThesisImpact.WEAKENED
        assert "remains intact" in result.summary_narrative.lower()

    def test_mixed_positive_and_negative_changes_produce_mixed_impact(self):
        previous = _with_risk(_with_business(_snapshot(), "growth", "moderate"), "financial_risk", "moderate")
        current = _with_risk(_with_business(_snapshot(), "growth", "strong"), "financial_risk", "high")
        result = compare_snapshots(previous, current)
        assert result.thesis_impact is ThesisImpact.MIXED
        assert "remains intact" in result.summary_narrative.lower()

    def test_thesis_impact_never_reads_thesis_prose(self):
        """`AnalyticalSnapshot` carries no thesis narrative field at all
        -- `compare_snapshots` structurally cannot compare prose."""
        assert not hasattr(AnalyticalSnapshot, "narrative")
        assert not hasattr(AnalyticalSnapshot, "atlas_thesis")


class TestSummaryNarrativeIsStructuredFirst:
    def test_summary_lists_one_bullet_per_change(self):
        previous = _with_risk(_with_business(_snapshot(), "growth", "strong"), "financial_risk", "moderate")
        current = _with_risk(_with_business(_snapshot(), "growth", "moderate"), "financial_risk", "high")
        result = compare_snapshots(previous, current)
        assert len(result.changes) == 2
        assert result.summary_narrative.count("- ") == 2


def _make_record(source_kind, period_end, identifier, *, published_at=GENERATED_AT, **metadata):
    document = RawBusinessDocument(
        identifier=identifier,
        company="ASML",
        source_kind=source_kind,
        published_at=published_at,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=GENERATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _strong_growth_records():
    return (
        _make_record("annual_report", date(2022, 12, 31), "fy22", revenue=1000.0, free_cash_flow=200.0),
        _make_record("annual_report", date(2023, 12, 31), "fy23", revenue=1100.0, free_cash_flow=240.0),
        _make_record("annual_report", date(2024, 12, 31), "fy24", revenue=1250.0, free_cash_flow=300.0),
    )


def _assemble(records=()):
    engine_input, output = run_minimal()
    return assemble_analysis(
        engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
    )


class TestCaptureSnapshotEndToEnd:
    """`capture_snapshot` derives correctly from a real, fully-assembled
    `CanonicalAnalysis` -- never a hand-built fake."""

    def test_capture_snapshot_reflects_real_growth_status(self):
        analysis = _assemble(_strong_growth_records())
        snapshot = capture_snapshot(analysis)
        real_growth_finding = next(f for f in analysis.business_analysis.findings if f.kind.value == "growth")
        growth_state = next(s for c, s, _ in snapshot.business_category_states if c == "growth")
        assert growth_state == real_growth_finding.status.value == "strong"

    def test_capture_snapshot_is_deterministic(self):
        first = capture_snapshot(_assemble(_strong_growth_records()))
        second = capture_snapshot(_assemble(_strong_growth_records()))
        assert first.content_hash == second.content_hash
        assert first.business_category_states == second.business_category_states

    def test_capture_snapshot_excludes_current_yield_from_content_hash(self):
        analysis = _assemble(_strong_growth_records())
        snapshot = capture_snapshot(analysis)
        mutated = dataclasses.replace(snapshot, current_yield=999.0)
        assert mutated.content_hash == snapshot.content_hash

    def test_no_records_produces_an_all_insufficient_snapshot_with_a_stable_hash(self):
        first = capture_snapshot(_assemble(()))
        second = capture_snapshot(_assemble(()))
        assert first.content_hash == second.content_hash
        assert all(status == "insufficient_input" for _, status, _ in first.business_category_states)

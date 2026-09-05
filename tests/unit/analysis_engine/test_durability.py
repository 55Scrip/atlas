"""Tests for `atlas.analysis_engine.durability.evaluate_durability` --
the documented rule table, branch by branch, plus determinism.

Fixtures use realistic shapes only: revenue in the tens of billions,
margins in plausible ranges, net debt that can go negative (net cash,
which several real holdings genuinely have). No impossible histories.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from atlas.analysis_engine.business_contracts import (
    BusinessCategory,
    BusinessCategoryStatus as Status,
    BusinessDataGapKind,
)
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind as Kind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.durability import evaluate_durability
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.business_facts._fixtures import EVALUATED_AT

_COUNTER = iter(range(1000000))


def fact(kind: Kind, value: float, period: str, *, published_offset_days: int = 0) -> BusinessFact:
    i = next(_COUNTER)
    return BusinessFact(
        id=f"fact-{i}",
        company="ASML",
        kind=kind,
        value=value,
        unit="usd",
        period=period,
        source_record_id=f"record-{i}",
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=(),
            dependencies=(),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=(),
            computed_at=EVALUATED_AT,
        ),
        extracted_at=EVALUATED_AT,
        published_at=EVALUATED_AT + timedelta(days=published_offset_days),
    )


def series(kind: Kind, values: list[float], start: int = 2018) -> list[BusinessFact]:
    return [fact(kind, value, str(start + offset)) for offset, value in enumerate(values)]


def run(*groups: list[BusinessFact]):
    facts = tuple(f for group in groups for f in group)
    return evaluate_durability(facts, evaluated_at=EVALUATED_AT)


# Reusable healthy components, so a test that targets one sub-assessment
# is not silently graded by another one's absence.
def _healthy_margins():
    return series(Kind.REVENUE, [100.0, 110.0, 120.0]) + series(Kind.NET_INCOME, [20.0, 23.0, 27.0])


def _healthy_balance_sheet():
    return (
        series(Kind.FREE_CASH_FLOW, [15.0, 17.0, 19.0])
        + series(Kind.TOTAL_DEBT, [50.0, 45.0, 40.0])
        + series(Kind.CASH, [30.0, 35.0, 40.0])
    )


class TestOverallStatus:
    def test_all_three_strong_is_strong(self):
        finding = run(_healthy_margins(), _healthy_balance_sheet())
        assert finding.status is Status.STRONG
        assert finding.confidence is EvidenceCoverageLevel.FULL

    def test_declining_everything_is_weak(self):
        finding = run(
            series(Kind.REVENUE, [120.0, 110.0, 100.0]),
            series(Kind.NET_INCOME, [30.0, 20.0, 10.0]),
            series(Kind.FREE_CASH_FLOW, [-5.0, -8.0, -12.0]),
            series(Kind.TOTAL_DEBT, [40.0, 60.0, 90.0]),
            series(Kind.CASH, [30.0, 25.0, 20.0]),
        )
        assert finding.status is Status.WEAK

    def test_stable_flat_history_is_strong_because_nothing_deteriorated(self):
        """Durability is persistence, not growth: flat revenue never
        fell, so demand held. This is the case a growth evaluator would
        call MIXED and durability must not."""
        finding = run(
            series(Kind.REVENUE, [100.0, 100.0, 100.0]),
            series(Kind.NET_INCOME, [20.0, 20.0, 20.0]),
            _healthy_balance_sheet(),
        )
        assert finding.status is Status.STRONG

    def test_mixed_signals_are_moderate(self):
        """Revenue dipped and recovered above its start; everything else
        healthy. Neither STRONG (something fell) nor WEAK (no erosion)."""
        finding = run(
            series(Kind.REVENUE, [100.0, 90.0, 105.0]),
            series(Kind.NET_INCOME, [20.0, 18.0, 22.0]),
            _healthy_balance_sheet(),
        )
        assert finding.status is Status.MODERATE

    def test_two_strong_sub_assessments_alone_do_not_reach_strong(self):
        """The deliberate rule: STRONG requires all three clauses
        answered, not one or two answered well."""
        finding = run(_healthy_margins())
        assert finding.status is Status.MODERATE
        assert finding.confidence is EvidenceCoverageLevel.PARTIAL


class TestDemandDurability:
    def test_revenue_that_never_fell_is_not_contradicting(self):
        finding = run(series(Kind.REVENUE, [100.0, 100.0, 120.0]))
        assert finding.contradicting_evidence == ()

    def test_net_erosion_across_the_span_is_recorded(self):
        finding = run(series(Kind.REVENUE, [120.0, 130.0, 100.0]))
        assert finding.contradicting_evidence != ()
        assert finding.status is Status.WEAK

    def test_dip_with_recovery_above_start_is_moderate(self):
        finding = run(series(Kind.REVENUE, [100.0, 80.0, 110.0]))
        assert finding.status is Status.MODERATE


class TestMarginDurability:
    def test_operating_income_absent_still_grades_on_net_margin(self):
        finding = run(_healthy_margins(), _healthy_balance_sheet())
        assert finding.status is Status.STRONG

    def test_operating_income_present_is_also_read(self):
        """Adding an eroding operating margin to otherwise healthy input
        must pull the result off STRONG -- proving the optional series is
        genuinely consulted, not ignored."""
        healthy = run(_healthy_margins(), _healthy_balance_sheet())
        with_operating = run(
            _healthy_margins(),
            _healthy_balance_sheet(),
            series(Kind.OPERATING_INCOME, [30.0, 20.0, 10.0]),
        )
        assert healthy.status is Status.STRONG
        assert with_operating.status is Status.MODERATE

    def test_margin_needs_positive_revenue(self):
        """A margin on zero revenue is meaningless, so the period is
        skipped and no margin series survives."""
        finding = run(
            series(Kind.REVENUE, [0.0, 0.0, 0.0]),
            series(Kind.NET_INCOME, [10.0, 20.0, 30.0]),
        )
        assert BusinessDataGapKind.INSUFFICIENT_HISTORICAL_PERIODS in finding.missing_evidence

    def test_margin_needs_both_facts_in_the_same_period(self):
        finding = run(
            series(Kind.REVENUE, [100.0, 110.0], start=2018),
            series(Kind.NET_INCOME, [20.0, 22.0], start=2030),
        )
        assert BusinessDataGapKind.INSUFFICIENT_HISTORICAL_PERIODS in finding.missing_evidence

    def test_shrinking_margin_on_growing_revenue_is_caught(self):
        """Revenue rises every period while net margin collapses --
        durability must not be fooled by the top line alone."""
        finding = run(
            series(Kind.REVENUE, [100.0, 200.0, 400.0]),
            series(Kind.NET_INCOME, [30.0, 20.0, 12.0]),
            _healthy_balance_sheet(),
        )
        assert finding.status is Status.MODERATE


class TestBalanceSheetResilience:
    def test_every_period_cash_generative_is_strong(self):
        finding = run(_healthy_margins(), _healthy_balance_sheet())
        assert finding.status is Status.STRONG

    def test_never_cash_generative_is_weak(self):
        finding = run(series(Kind.FREE_CASH_FLOW, [-1.0, -2.0, -3.0]))
        assert finding.status is Status.WEAK

    def test_mixed_cash_generation_is_moderate(self):
        finding = run(series(Kind.FREE_CASH_FLOW, [10.0, -2.0, 8.0]))
        assert finding.status is Status.MODERATE

    def test_rising_net_debt_is_adverse(self):
        finding = run(
            series(Kind.TOTAL_DEBT, [40.0, 60.0, 90.0]),
            series(Kind.CASH, [30.0, 25.0, 20.0]),
        )
        assert finding.status is Status.WEAK

    def test_net_cash_position_is_handled(self):
        """Debt below cash is negative net debt -- a real position for
        several holdings, and falling further must read as improving."""
        finding = run(
            series(Kind.TOTAL_DEBT, [30.0, 20.0, 10.0]),
            series(Kind.CASH, [50.0, 60.0, 70.0]),
        )
        assert finding.status is Status.MODERATE  # strong component, but only one clause answered
        assert finding.contradicting_evidence == ()

    def test_net_debt_needs_both_cash_and_debt(self):
        finding = run(series(Kind.TOTAL_DEBT, [40.0, 50.0]))
        assert BusinessDataGapKind.MISSING_DEBT_DATA in finding.missing_evidence


class TestInsufficientInput:
    def test_no_facts_at_all_is_not_applicable(self):
        finding = evaluate_durability((), evaluated_at=EVALUATED_AT)
        assert finding.status is Status.INSUFFICIENT_INPUT
        assert finding.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_one_period_grades_nothing(self):
        finding = run(series(Kind.REVENUE, [100.0]), series(Kind.NET_INCOME, [20.0]))
        assert finding.status is Status.INSUFFICIENT_INPUT
        assert finding.confidence is EvidenceCoverageLevel.NONE
        assert BusinessDataGapKind.INSUFFICIENT_HISTORICAL_PERIODS in finding.missing_evidence

    def test_missing_revenue_is_named(self):
        finding = run(series(Kind.FREE_CASH_FLOW, [10.0, 12.0]))
        assert BusinessDataGapKind.MISSING_REVENUE_HISTORY in finding.missing_evidence

    def test_missing_cash_flow_is_named(self):
        finding = run(series(Kind.REVENUE, [100.0, 110.0]))
        assert BusinessDataGapKind.MISSING_CASH_FLOW_HISTORY in finding.missing_evidence

    def test_gaps_are_not_duplicated(self):
        finding = run(series(Kind.REVENUE, [100.0]))
        assert len(finding.missing_evidence) == len(set(finding.missing_evidence))


class TestFindingShape:
    def test_identity_and_category(self):
        finding = run(_healthy_margins(), _healthy_balance_sheet())
        assert finding.id == "business_finding:durability"
        assert finding.kind is BusinessCategory.DURABILITY

    def test_provenance_names_every_fact_it_read(self):
        facts = _healthy_margins() + _healthy_balance_sheet()
        finding = run(facts)
        assert set(finding.provenance.dependencies) == {f.id for f in facts}

    def test_gross_profit_is_never_required(self):
        """The sufficiency decision, pinned: durability must reach a real
        status without gross profit, which exists for 9 of 30 companies."""
        finding = run(_healthy_margins(), _healthy_balance_sheet())
        assert finding.status is not Status.INSUFFICIENT_INPUT


class TestDeterminismAndProperties:
    def test_input_ordering_does_not_affect_output(self):
        facts = _healthy_margins() + _healthy_balance_sheet()
        forward = evaluate_durability(tuple(facts), evaluated_at=EVALUATED_AT)
        reversed_ = evaluate_durability(tuple(reversed(facts)), evaluated_at=EVALUATED_AT)
        assert forward == reversed_

    def test_repeated_evaluation_is_identical(self):
        facts = tuple(_healthy_margins() + _healthy_balance_sheet())
        assert evaluate_durability(facts, evaluated_at=EVALUATED_AT) == evaluate_durability(
            facts, evaluated_at=EVALUATED_AT)

    def test_a_restatement_supersedes_the_original_for_its_period(self):
        """Two facts, same kind, same period. The later-published one
        wins, so the series reads 100 -> 90 (erosion), not 100 -> 120."""
        original = fact(Kind.REVENUE, 120.0, "2019", published_offset_days=1)
        restated = fact(Kind.REVENUE, 90.0, "2019", published_offset_days=2)
        base = [fact(Kind.REVENUE, 100.0, "2018")]
        finding = evaluate_durability(tuple(base + [original, restated]), evaluated_at=EVALUATED_AT)
        assert finding.status is Status.WEAK
        assert original.id not in finding.provenance.dependencies
        assert restated.id in finding.provenance.dependencies

    def test_duplicate_resolution_does_not_depend_on_input_order(self):
        original = fact(Kind.REVENUE, 120.0, "2019", published_offset_days=1)
        restated = fact(Kind.REVENUE, 90.0, "2019", published_offset_days=2)
        base = [fact(Kind.REVENUE, 100.0, "2018")]
        one = evaluate_durability(tuple(base + [original, restated]), evaluated_at=EVALUATED_AT)
        two = evaluate_durability(tuple(base + [restated, original]), evaluated_at=EVALUATED_AT)
        assert one == two

    def test_exact_duplicates_do_not_create_a_spurious_delta(self):
        duplicated = series(Kind.REVENUE, [100.0, 120.0])
        finding = evaluate_durability(tuple(duplicated + duplicated), evaluated_at=EVALUATED_AT)
        assert finding.status is Status.MODERATE  # one clause answered, strong
        assert finding.contradicting_evidence == ()

    def test_unrelated_fact_kinds_are_ignored(self):
        """Built once and reused: a fresh `run()` per call would mint new
        fact ids and the two findings could never compare equal."""
        base = tuple(_healthy_margins() + _healthy_balance_sheet())
        noise = tuple(series(Kind.DIVIDENDS, [1.0, 50.0, 2.0]))
        clean = evaluate_durability(base, evaluated_at=EVALUATED_AT)
        with_noise = evaluate_durability(base + noise, evaluated_at=EVALUATED_AT)
        assert with_noise == clean

    @pytest.mark.parametrize("status", [Status.STRONG, Status.MODERATE, Status.WEAK])
    def test_every_reachable_status_has_matching_severity(self, status):
        from atlas.analysis_engine.business_contracts import severity_for_status

        assert severity_for_status(status) is not None

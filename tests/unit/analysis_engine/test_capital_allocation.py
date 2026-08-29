"""Tests for `atlas.analysis_engine.capital_allocation
.evaluate_capital_allocation` (ATLAS-023 Phase 6; redesigned
Calibration Phase 4 -- Conviction & Capital Allocation Repair) -- the
v2 four-signal rule table (`capital_return`/`leverage_trend`/
`dividend`/`cash_generation`) and its combination rule."""
from __future__ import annotations

from atlas.analysis_engine.business_contracts import BusinessCategory, BusinessCategoryStatus, BusinessDataGapKind
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.capital_allocation import evaluate_capital_allocation
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.business_facts._fixtures import EVALUATED_AT

_COUNTER = iter(range(100000))


def fact(kind: BusinessFactKind, value: float, period: str = "2024") -> BusinessFact:
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
        published_at=EVALUATED_AT,
    )


# A falling TOTAL_DEBT history -> leverage_trend POSITIVE (deleveraging).
_DELEVERAGING_DEBT = (
    fact(BusinessFactKind.TOTAL_DEBT, 500, period="2022"),
    fact(BusinessFactKind.TOTAL_DEBT, 300, period="2023"),
    fact(BusinessFactKind.TOTAL_DEBT, 100, period="2024"),
)
# A rising TOTAL_DEBT history -> leverage_trend NEGATIVE (worsening).
_WORSENING_DEBT = (
    fact(BusinessFactKind.TOTAL_DEBT, 100, period="2022"),
    fact(BusinessFactKind.TOTAL_DEBT, 300, period="2023"),
    fact(BusinessFactKind.TOTAL_DEBT, 500, period="2024"),
)


class TestCapitalReturnSignal:
    def test_buybacks_exceeding_issuance_is_positive(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 500),
            fact(BusinessFactKind.SHARE_ISSUANCE, 50),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE  # one signal alone never reaches STRONG

    def test_issuance_exceeding_buybacks_is_negative(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 10),
            fact(BusinessFactKind.SHARE_ISSUANCE, 400),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.WEAK

    def test_only_buybacks_without_issuance_is_insufficient_not_assumed_zero(self):
        """Absence of issuance data must never be treated as zero
        issuance."""
        facts = (fact(BusinessFactKind.SHARE_BUYBACKS, 500),)
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        assert BusinessDataGapKind.MISSING_BUYBACK_DATA in result.missing_evidence

    def test_only_the_three_most_recent_periods_per_side_are_compared(self):
        """An old, large issuance outside the recency window no longer
        weighs against sustained recent buyback activity."""
        facts = (
            fact(BusinessFactKind.SHARE_ISSUANCE, 10_000, period="2010"),  # outside the window
            fact(BusinessFactKind.SHARE_BUYBACKS, 100, period="2022"),
            fact(BusinessFactKind.SHARE_BUYBACKS, 100, period="2023"),
            fact(BusinessFactKind.SHARE_BUYBACKS, 100, period="2024"),
            fact(BusinessFactKind.SHARE_ISSUANCE, 10, period="2022"),
            fact(BusinessFactKind.SHARE_ISSUANCE, 10, period="2023"),
            fact(BusinessFactKind.SHARE_ISSUANCE, 10, period="2024"),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE  # positive, not WEAK from the old issuance


class TestLeverageTrendSignal:
    def test_debt_falling_every_period_is_positive(self):
        result = evaluate_capital_allocation(_DELEVERAGING_DEBT, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE  # one signal alone never reaches STRONG

    def test_debt_rising_every_period_is_negative(self):
        result = evaluate_capital_allocation(_WORSENING_DEBT, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.WEAK

    def test_fewer_than_two_debt_periods_is_insufficient(self):
        facts = (fact(BusinessFactKind.TOTAL_DEBT, 500),)
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        assert BusinessDataGapKind.MISSING_DEBT_DATA in result.missing_evidence

    def test_a_mixed_debt_trend_is_insufficient_not_guessed(self):
        facts = (
            fact(BusinessFactKind.TOTAL_DEBT, 100, period="2022"),
            fact(BusinessFactKind.TOTAL_DEBT, 300, period="2023"),
            fact(BusinessFactKind.TOTAL_DEBT, 200, period="2024"),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT

    def test_an_old_acquisition_funded_raise_still_visible_in_the_full_history_reads_insufficient_not_negative(self):
        """`classify_metric_trend` requires *every* consecutive period
        to agree -- a single old rise (the acquisition-funded raise)
        followed by years of real deleveraging is honestly `MIXED`
        (`INSUFFICIENT`), not fabricated as `POSITIVE` from a partial
        read of only the recent periods. Reused verbatim from
        `financial_risk._debt_trend_signal`, whose own already-shipped
        behavior has the identical property: a real, disclosed
        limitation (a distant one-time blip can suppress the signal for
        as long as it remains in the available history), not a defect
        introduced by this evaluator -- INSUFFICIENT is still strictly
        better than v1's old static comparison, which would have read
        this same company as WEAK forever with no path to recovery."""
        facts = (
            fact(BusinessFactKind.TOTAL_DEBT, 50, period="2019"),
            fact(BusinessFactKind.TOTAL_DEBT, 900, period="2020"),  # the acquisition-funded raise
            fact(BusinessFactKind.TOTAL_DEBT, 600, period="2022"),
            fact(BusinessFactKind.TOTAL_DEBT, 300, period="2023"),
            fact(BusinessFactKind.TOTAL_DEBT, 100, period="2024"),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT


class TestDividendSignal:
    def test_a_real_current_dividend_is_positive(self):
        facts = (
            *_DELEVERAGING_DEBT,
            fact(BusinessFactKind.DIVIDENDS, 25),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.STRONG  # deleveraging + dividend = 2 positives, 0 negatives

    def test_no_dividend_is_insufficient_never_negative(self):
        """Declining to pay a dividend is a legitimate strategy, not a
        penalized one -- absence must never read as a negative signal."""
        result = evaluate_capital_allocation(_DELEVERAGING_DEBT, evaluated_at=EVALUATED_AT)
        assert BusinessDataGapKind.MISSING_DIVIDEND_DATA in result.missing_evidence
        assert result.status is BusinessCategoryStatus.MODERATE  # never WEAK from dividend absence alone

    def test_a_zero_dividend_is_insufficient_never_negative(self):
        facts = (*_DELEVERAGING_DEBT, fact(BusinessFactKind.DIVIDENDS, 0))
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE


class TestCashGenerationSignal:
    def test_positive_free_cash_flow_is_positive(self):
        facts = (*_DELEVERAGING_DEBT, fact(BusinessFactKind.FREE_CASH_FLOW, 200))
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.STRONG

    def test_negative_free_cash_flow_is_negative(self):
        facts = (*_DELEVERAGING_DEBT, fact(BusinessFactKind.FREE_CASH_FLOW, -50))
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE  # one positive (debt), one negative (cash)

    def test_no_free_cash_flow_fact_is_insufficient(self):
        result = evaluate_capital_allocation(_DELEVERAGING_DEBT, evaluated_at=EVALUATED_AT)
        assert BusinessDataGapKind.MISSING_CASH_FLOW_DATA in result.missing_evidence

    def test_only_the_most_recent_free_cash_flow_period_is_read(self):
        facts = (
            *_DELEVERAGING_DEBT,
            fact(BusinessFactKind.FREE_CASH_FLOW, -500, period="2022"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 100, period="2024"),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.STRONG


class TestCombinationRule:
    def test_no_computable_signal_is_insufficient_input(self):
        result = evaluate_capital_allocation((), evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        assert result.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_negatives_outweighing_positives_is_weak(self):
        facts = (
            *_WORSENING_DEBT,
            fact(BusinessFactKind.SHARE_ISSUANCE, 400),
            fact(BusinessFactKind.SHARE_BUYBACKS, 10),
            fact(BusinessFactKind.FREE_CASH_FLOW, 100),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.WEAK  # 2 negatives > 1 positive

    def test_equal_negatives_and_positives_is_moderate_not_weak(self):
        """Negatives must genuinely *outweigh* positives to reach WEAK
        -- a tie is honestly mixed, not disqualifying."""
        facts = (*_WORSENING_DEBT, fact(BusinessFactKind.FREE_CASH_FLOW, 100))
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE  # 1 negative, 1 positive

    def test_one_negative_against_one_positive_is_moderate_not_weak(self):
        """The v1 defect this sprint fixes: a single negative used to
        unconditionally disqualify to WEAK, never offset. v2 requires
        negatives to genuinely outweigh positives."""
        facts = (*_DELEVERAGING_DEBT, fact(BusinessFactKind.FREE_CASH_FLOW, -50))
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE

    def test_two_positives_and_zero_negatives_is_strong(self):
        facts = (*_DELEVERAGING_DEBT, fact(BusinessFactKind.DIVIDENDS, 25))
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.STRONG

    def test_a_single_positive_signal_alone_is_moderate_not_strong(self):
        """STRONG requires at least two independently-corroborating
        positive signals -- a higher bar than a lone positive."""
        result = evaluate_capital_allocation(_DELEVERAGING_DEBT, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE

    def test_all_four_signals_positive_is_strong_with_full_confidence(self):
        facts = (
            *_DELEVERAGING_DEBT,
            fact(BusinessFactKind.SHARE_BUYBACKS, 500),
            fact(BusinessFactKind.SHARE_ISSUANCE, 50),
            fact(BusinessFactKind.DIVIDENDS, 25),
            fact(BusinessFactKind.FREE_CASH_FLOW, 200),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.STRONG
        assert result.confidence is EvidenceCoverageLevel.FULL


class TestCapexAndSharesOutstandingAreInformationalOnly:
    def test_capex_presence_does_not_change_status(self):
        without_capex = evaluate_capital_allocation((), evaluated_at=EVALUATED_AT)
        with_capex = evaluate_capital_allocation(
            (fact(BusinessFactKind.CAPITAL_EXPENDITURE, 200),), evaluated_at=EVALUATED_AT
        )
        assert without_capex.status == with_capex.status is BusinessCategoryStatus.INSUFFICIENT_INPUT

    def test_capex_absence_is_still_recorded_in_missing_evidence(self):
        result = evaluate_capital_allocation(_DELEVERAGING_DEBT, evaluated_at=EVALUATED_AT)
        assert BusinessDataGapKind.MISSING_CAPEX_DATA in result.missing_evidence

    def test_share_count_presence_does_not_change_status_or_confidence(self):
        without_shares = evaluate_capital_allocation(_DELEVERAGING_DEBT, evaluated_at=EVALUATED_AT)
        with_shares = evaluate_capital_allocation(
            (
                *_DELEVERAGING_DEBT,
                fact(BusinessFactKind.SHARES_OUTSTANDING, 1_000_000, period="2023"),
                fact(BusinessFactKind.SHARES_OUTSTANDING, 950_000, period="2024"),
            ),
            evaluated_at=EVALUATED_AT,
        )
        assert without_shares.status is with_shares.status
        assert without_shares.confidence is with_shares.confidence
        assert BusinessDataGapKind.MISSING_SHARE_COUNT_HISTORY not in with_shares.missing_evidence
        assert BusinessDataGapKind.MISSING_SHARE_COUNT_HISTORY in without_shares.missing_evidence

    def test_share_count_alone_with_no_other_facts_is_still_insufficient_input(self):
        facts = (
            fact(BusinessFactKind.SHARES_OUTSTANDING, 1_000_000, period="2023"),
            fact(BusinessFactKind.SHARES_OUTSTANDING, 950_000, period="2024"),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        # Real facts exist (just not ones that drive a signal) --
        # confidence reads as NONE, not the "nothing at all" NOT_APPLICABLE.
        assert result.confidence is EvidenceCoverageLevel.NONE


class TestNoFabrication:
    def test_no_numeric_score_anywhere(self):
        result = evaluate_capital_allocation((), evaluated_at=EVALUATED_AT)
        assert not hasattr(result, "score")
        assert isinstance(result.status.value, str)


class TestDeterminism:
    def test_identical_facts_produce_a_deeply_equal_finding(self):
        first = evaluate_capital_allocation(_DELEVERAGING_DEBT, evaluated_at=EVALUATED_AT)
        second = evaluate_capital_allocation(_DELEVERAGING_DEBT, evaluated_at=EVALUATED_AT)
        assert first == second

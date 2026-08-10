"""Tests for `atlas.analysis_engine.capital_allocation
.evaluate_capital_allocation` (ATLAS-023 Phase 6) -- the documented
rule table, and Scenarios E-G from Phase 14."""
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


class TestScenarioE_DisciplinedAllocation:
    def test_buybacks_exceed_issuance_and_repayment_exceeds_new_debt_is_strong(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 500),
            fact(BusinessFactKind.SHARE_ISSUANCE, 50),
            fact(BusinessFactKind.DEBT_REPAYMENT, 300),
            fact(BusinessFactKind.DEBT_ISSUANCE, 100),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.STRONG
        assert result.kind is BusinessCategory.CAPITAL_ALLOCATION
        assert result.confidence is EvidenceCoverageLevel.FULL


class TestScenarioF_DilutionAndLeverageDeterioration:
    def test_issuance_exceeding_buybacks_is_weak(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 10),
            fact(BusinessFactKind.SHARE_ISSUANCE, 400),
            fact(BusinessFactKind.DEBT_REPAYMENT, 300),
            fact(BusinessFactKind.DEBT_ISSUANCE, 100),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.WEAK

    def test_a_single_negative_signal_is_never_offset_by_a_positive_one(self):
        """No hidden weighting: one adverse signal is disqualifying
        regardless of how positive the other is."""
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 5000),
            fact(BusinessFactKind.SHARE_ISSUANCE, 10),
            fact(BusinessFactKind.DEBT_ISSUANCE, 5000),
            fact(BusinessFactKind.DEBT_REPAYMENT, 10),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.WEAK

    def test_increasing_leverage_alone_is_weak(self):
        facts = (
            fact(BusinessFactKind.DEBT_ISSUANCE, 500),
            fact(BusinessFactKind.DEBT_REPAYMENT, 50),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.WEAK


class TestScenarioG_MissingData:
    def test_no_facts_at_all_is_insufficient_input(self):
        result = evaluate_capital_allocation((), evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        assert result.confidence is EvidenceCoverageLevel.NOT_APPLICABLE
        assert BusinessDataGapKind.MISSING_BUYBACK_DATA in result.missing_evidence
        assert BusinessDataGapKind.MISSING_DEBT_DATA in result.missing_evidence
        assert BusinessDataGapKind.MISSING_CAPEX_DATA in result.missing_evidence
        assert BusinessDataGapKind.MISSING_DIVIDEND_DATA in result.missing_evidence

    def test_only_buybacks_without_issuance_is_insufficient_not_assumed_zero(self):
        """Absence of issuance data must never be treated as zero
        issuance."""
        facts = (fact(BusinessFactKind.SHARE_BUYBACKS, 500),)
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        assert BusinessDataGapKind.MISSING_BUYBACK_DATA in result.missing_evidence


class TestOneComputableSignalCapsAtModerate:
    def test_one_positive_signal_and_the_other_insufficient_is_moderate(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 500),
            fact(BusinessFactKind.SHARE_ISSUANCE, 50),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE
        assert result.confidence is EvidenceCoverageLevel.PARTIAL

    def test_both_signals_flat_is_moderate(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 100),
            fact(BusinessFactKind.SHARE_ISSUANCE, 100),
            fact(BusinessFactKind.DEBT_REPAYMENT, 50),
            fact(BusinessFactKind.DEBT_ISSUANCE, 50),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE


class TestCapexAndDividendsAreInformationalOnly:
    def test_capex_presence_does_not_change_status(self):
        without_capex = evaluate_capital_allocation((), evaluated_at=EVALUATED_AT)
        with_capex = evaluate_capital_allocation(
            (fact(BusinessFactKind.CAPITAL_EXPENDITURE, 200),), evaluated_at=EVALUATED_AT
        )
        assert without_capex.status == with_capex.status is BusinessCategoryStatus.INSUFFICIENT_INPUT

    def test_capex_absence_is_still_recorded_in_missing_evidence(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 500),
            fact(BusinessFactKind.SHARE_ISSUANCE, 50),
            fact(BusinessFactKind.DEBT_REPAYMENT, 300),
            fact(BusinessFactKind.DEBT_ISSUANCE, 100),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.STRONG
        assert BusinessDataGapKind.MISSING_CAPEX_DATA in result.missing_evidence
        assert BusinessDataGapKind.MISSING_DIVIDEND_DATA in result.missing_evidence


class TestNoFabrication:
    def test_no_numeric_score_anywhere(self):
        result = evaluate_capital_allocation((), evaluated_at=EVALUATED_AT)
        assert not hasattr(result, "score")
        assert isinstance(result.status.value, str)


class TestDeterminism:
    def test_identical_facts_produce_a_deeply_equal_finding(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 500),
            fact(BusinessFactKind.SHARE_ISSUANCE, 50),
        )
        first = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        second = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert first == second


class TestSharesOutstandingIsInformationalOnly:
    """Company Data Foundation v1: `SHARES_OUTSTANDING` is recorded in
    `missing_evidence` when absent, exactly like CAPEX/dividends, but
    never drives `status` or changes `confidence`'s own two-signal
    computation."""

    def test_missing_share_count_is_recorded_when_absent(self):
        facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 500),
            fact(BusinessFactKind.SHARE_ISSUANCE, 50),
            fact(BusinessFactKind.DEBT_REPAYMENT, 300),
            fact(BusinessFactKind.DEBT_ISSUANCE, 100),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert BusinessDataGapKind.MISSING_SHARE_COUNT_HISTORY in result.missing_evidence

    def test_share_count_presence_does_not_change_status_or_confidence(self):
        """A real, disciplined-allocation company (STRONG, FULL
        confidence per Scenario E) stays exactly the same whether or
        not `SHARES_OUTSTANDING` facts happen to also be present --
        proving share-count data is genuinely never folded into either
        computation."""
        base_facts = (
            fact(BusinessFactKind.SHARE_BUYBACKS, 500),
            fact(BusinessFactKind.SHARE_ISSUANCE, 50),
            fact(BusinessFactKind.DEBT_REPAYMENT, 300),
            fact(BusinessFactKind.DEBT_ISSUANCE, 100),
        )
        without_shares = evaluate_capital_allocation(base_facts, evaluated_at=EVALUATED_AT)
        with_shares = evaluate_capital_allocation(
            (*base_facts, fact(BusinessFactKind.SHARES_OUTSTANDING, 1_000_000, period="2023"),
             fact(BusinessFactKind.SHARES_OUTSTANDING, 950_000, period="2024")),
            evaluated_at=EVALUATED_AT,
        )
        assert without_shares.status is with_shares.status is BusinessCategoryStatus.STRONG
        assert without_shares.confidence is with_shares.confidence is EvidenceCoverageLevel.FULL
        assert BusinessDataGapKind.MISSING_SHARE_COUNT_HISTORY not in with_shares.missing_evidence
        assert BusinessDataGapKind.MISSING_SHARE_COUNT_HISTORY in without_shares.missing_evidence

    def test_share_count_alone_with_no_other_facts_is_still_insufficient_input(self):
        """Share-count data alone never unblocks a real conclusion --
        it is informational, not a third signal the status rule reads."""
        facts = (
            fact(BusinessFactKind.SHARES_OUTSTANDING, 1_000_000, period="2023"),
            fact(BusinessFactKind.SHARES_OUTSTANDING, 950_000, period="2024"),
        )
        result = evaluate_capital_allocation(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        # Real facts exist (just not the ones that drive a signal) --
        # confidence reads as NONE, not the "nothing at all" NOT_APPLICABLE.
        assert result.confidence is EvidenceCoverageLevel.NONE

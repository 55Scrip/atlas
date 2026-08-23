"""Tests for `atlas.alpha.evidence_quality.engine`.

Conflict/freshness/dominance tests use real `BusinessRecord`s built
through the real `ingest()` pipeline (the same convention
`tests/unit/alpha/coverage/test_engine.py` already establishes -- never
a hand-built fake `BusinessRecord`). `_unsupported_findings` is tested
directly against hand-built `BusinessFinding`/`RiskFinding`/
`ValuationFinding` tuples (plain, unvalidated dataclasses), since that
function takes the three finding tuples directly rather than a whole
`CanonicalAnalysis` -- see the function's own docstring for why.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.evidence_quality.engine import _detect_conflicts, _fact_quality_by_kind, _unsupported_findings, assess_evidence_quality
from atlas.alpha.evidence_quality.models import (
    EvidenceConflictStatus,
    EvidenceDominance,
    EvidenceFreshness,
    EvidenceQualityLevel,
    EvidenceWarningCode,
)
from atlas.analysis_engine.business_contracts import BusinessCategory, BusinessCategoryStatus, BusinessFinding
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.analysis_engine.valuation.models import ValuationFinding
from atlas.decision_engine.contracts import EvidenceCoverageLevel

EVALUATED_AT = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

_PROVENANCE = Provenance(
    source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
    source_references=(),
    dependencies=(),
    update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
    consumers=(),
    computed_at=EVALUATED_AT,
)


def _make_record(
    identifier: str, period_end: date, *, source_kind: str = "annual_report", published_at: datetime = EVALUATED_AT, **metadata
) -> "BusinessRecord":
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
    result = ingest(document, evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord), result
    return result.record


def _business_finding(status: BusinessCategoryStatus, *, supporting: tuple[str, ...] = ()) -> BusinessFinding:
    return BusinessFinding(
        id="finding-1",
        kind=BusinessCategory.GROWTH,
        status=status,
        severity=FindingSeverity.INFO,
        supporting_evidence=supporting,
        contradicting_evidence=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=_PROVENANCE,
        updated_at=EVALUATED_AT,
    )


def _valuation_finding(status: ValuationStatus, *, supporting: tuple[str, ...] = ()) -> ValuationFinding:
    return ValuationFinding(
        id="finding-2",
        kind=ValuationMethodKind.FCF_YIELD_RELATIVE,
        status=status,
        severity=FindingSeverity.INFO,
        supporting_facts=supporting,
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=_PROVENANCE,
        evaluated_at=EVALUATED_AT,
    )


def _risk_finding(category: RiskCategory, status: RiskStatus, *, supporting: tuple[str, ...] = (), contradicting: tuple[str, ...] = ()) -> RiskFinding:
    return RiskFinding(
        id="finding-3",
        category=category,
        status=status,
        severity=FindingSeverity.INFO,
        supporting_facts=supporting,
        contradicting_facts=contradicting,
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=_PROVENANCE,
        evaluated_at=EVALUATED_AT,
    )


class TestConflictDetection:
    def test_two_records_with_the_same_value_are_not_a_conflict(self):
        records = (_make_record("a", date(2024, 12, 31), revenue=1000.0), _make_record("b", date(2024, 12, 31), revenue=1000.0))
        assert _detect_conflicts(records, evaluated_at=EVALUATED_AT) == ()

    def test_two_records_disagreeing_on_the_same_period_is_a_real_conflict(self):
        records = (_make_record("a", date(2024, 12, 31), revenue=1000.0), _make_record("b", date(2024, 12, 31), revenue=1200.0))
        conflicts = _detect_conflicts(records, evaluated_at=EVALUATED_AT)
        assert len(conflicts) == 1
        assert conflicts[0].fact_kind == "revenue"
        assert conflicts[0].period == "2024-12-31"
        assert set(conflicts[0].values) == {1000.0, 1200.0}
        assert len(conflicts[0].source_record_ids) == 2

    def test_mirrors_exactly_what_core_extraction_silently_drops(self):
        """The whole point of this engine: what `_detect_conflicts`
        finds must be exactly what `extract_facts_from_records` (Core,
        unmodified) silently excludes -- never a different rule."""
        records = (_make_record("a", date(2024, 12, 31), revenue=1000.0), _make_record("b", date(2024, 12, 31), revenue=1200.0))
        conflicts = _detect_conflicts(records, evaluated_at=EVALUATED_AT)
        surviving = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        assert conflicts[0].fact_kind == "revenue"
        assert not any(f.kind.value == "revenue" and f.period == "2024-12-31" for f in surviving)

    def test_different_periods_never_conflict(self):
        records = (_make_record("a", date(2023, 12, 31), revenue=1000.0), _make_record("b", date(2024, 12, 31), revenue=1200.0))
        assert _detect_conflicts(records, evaluated_at=EVALUATED_AT) == ()

    def test_valuation_facts_are_checked_too(self):
        records = (
            _make_record("a", date(2024, 3, 1), source_kind="market_data_snapshot", share_price=50.0),
            _make_record("b", date(2024, 3, 1), source_kind="market_data_snapshot", share_price=55.0),
        )
        conflicts = _detect_conflicts(records, evaluated_at=EVALUATED_AT)
        assert any(c.fact_kind == "share_price" for c in conflicts)


class TestFreshnessAndDominance:
    def test_a_recently_published_fact_is_fresh(self):
        records = (_make_record("a", date(2024, 12, 31), published_at=EVALUATED_AT, revenue=1000.0),)
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        facts = _fact_quality_by_kind(business_facts, (), evaluated_at=EVALUATED_AT)
        assert facts[0].freshness is EvidenceFreshness.FRESH

    def test_a_fact_published_over_a_year_ago_is_stale(self):
        old = datetime(2024, 1, 1, tzinfo=timezone.utc)
        records = (_make_record("a", date(2023, 12, 31), published_at=old, revenue=1000.0),)
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        facts = _fact_quality_by_kind(business_facts, (), evaluated_at=EVALUATED_AT)
        assert facts[0].freshness is EvidenceFreshness.STALE

    def test_a_single_source_record_is_flagged_single_source(self):
        records = (_make_record("a", date(2024, 12, 31), revenue=1000.0),)
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        facts = _fact_quality_by_kind(business_facts, (), evaluated_at=EVALUATED_AT)
        assert facts[0].dominance is EvidenceDominance.SINGLE_SOURCE

    def test_two_independent_records_reporting_the_same_kind_are_corroborated(self):
        records = (
            _make_record("a", date(2023, 12, 31), revenue=900.0),
            _make_record("b", date(2024, 12, 31), revenue=1000.0),
        )
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        facts = _fact_quality_by_kind(business_facts, (), evaluated_at=EVALUATED_AT)
        assert facts[0].dominance is EvidenceDominance.CORROBORATED
        assert facts[0].source_record_count == 2


class TestUnsupportedFindings:
    def test_a_real_conclusion_with_no_supporting_evidence_is_flagged(self):
        found = _unsupported_findings((_business_finding(BusinessCategoryStatus.STRONG),), (), ())
        assert len(found) == 1
        assert found[0].category == "growth"

    def test_a_real_conclusion_with_supporting_evidence_is_not_flagged(self):
        found = _unsupported_findings((_business_finding(BusinessCategoryStatus.STRONG, supporting=("fact-1",)),), (), ())
        assert found == ()

    def test_insufficient_input_status_is_never_flagged_even_without_evidence(self):
        """Insufficient input already honestly says 'no real
        conclusion' -- flagging it again as unsupported would be a
        duplicate, misleading signal."""
        found = _unsupported_findings((_business_finding(BusinessCategoryStatus.INSUFFICIENT_INPUT),), (), ())
        assert found == ()

    def test_valuation_findings_are_checked_by_their_own_supporting_facts_field(self):
        found = _unsupported_findings((), (_valuation_finding(ValuationStatus.FAIRLY_VALUED),), ())
        assert len(found) == 1
        assert found[0].category == "fcf_yield_relative"

    def test_thesis_risk_low_is_never_flagged_even_with_no_supporting_facts(self):
        """Live-verification finding (Deliverable 13): `thesis_risk`'s
        own real evaluator always constructs `supporting_facts=()`, for
        a genuine LOW conclusion exactly as much as HIGH -- confirmed
        against real ingested company data. Checking `supporting_facts`
        against this one evaluator's shape produced a false positive on
        every real Case reaching this status; excluded, see the
        function's own docstring."""
        found = _unsupported_findings((), (), (_risk_finding(RiskCategory.THESIS_RISK, RiskStatus.LOW),))
        assert found == ()

    def test_thesis_risk_high_is_never_flagged_even_though_supporting_facts_is_empty(self):
        """HIGH's real evidentiary backing lives in `contradicting_facts`
        instead, per the same evaluator; also excluded, not just LOW."""
        found = _unsupported_findings((), (), (_risk_finding(RiskCategory.THESIS_RISK, RiskStatus.HIGH, contradicting=("obs-1",)),))
        assert found == ()

    def test_a_non_thesis_risk_category_is_still_checked_normally(self):
        found = _unsupported_findings((), (), (_risk_finding(RiskCategory.FINANCIAL_RISK, RiskStatus.HIGH),))
        assert len(found) == 1
        assert found[0].category == "financial_risk"


class TestOverallQualityPriority:
    def test_no_evidence_at_all_is_not_applicable(self):
        report = assess_evidence_quality((), (), (), _bare_analysis(), evaluated_at=EVALUATED_AT)
        assert report.quality is EvidenceQualityLevel.NOT_APPLICABLE
        assert EvidenceWarningCode.NO_EVIDENCE in report.warnings

    def test_a_real_conflict_outranks_everything_else(self):
        records = (_make_record("a", date(2024, 12, 31), revenue=1000.0), _make_record("b", date(2024, 12, 31), revenue=1200.0))
        report = assess_evidence_quality(records, (), (), _bare_analysis(), evaluated_at=EVALUATED_AT)
        assert report.quality is EvidenceQualityLevel.CONFLICTING
        assert report.conflict_status is EvidenceConflictStatus.CONFLICTING
        assert EvidenceWarningCode.CONFLICTING_SOURCE_VALUES in report.warnings

    def test_fresh_evidence_with_no_conflicts_reads_fresh(self):
        """A broad, evenly-populated fact base -- enough distinct kinds
        that `INCOMPLETE` does not also apply -- so this isolates
        freshness specifically."""
        records = (
            _make_record(
                "a", date(2024, 12, 31),
                revenue=1000.0, free_cash_flow=200.0, operating_income=150.0, net_income=100.0,
                eps=1.5, cash=300.0, total_debt=50.0, shares_outstanding=100.0,
                capital_expenditure=40.0, share_buybacks=20.0, share_issuance=5.0,
                dividends=10.0, debt_issuance=5.0, debt_repayment=5.0,
            ),
        )
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        report = assess_evidence_quality(records, business_facts, (), _bare_analysis(), evaluated_at=EVALUATED_AT)
        assert report.quality is EvidenceQualityLevel.FRESH
        assert report.conflict_status is EvidenceConflictStatus.CONSISTENT

    def test_a_thin_single_kind_evidence_base_reads_incomplete(self):
        records = (_make_record("a", date(2024, 12, 31), revenue=1000.0),)
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        report = assess_evidence_quality(records, business_facts, (), _bare_analysis(), evaluated_at=EVALUATED_AT)
        assert report.quality is EvidenceQualityLevel.INCOMPLETE
        assert EvidenceWarningCode.PARTIAL_COVERAGE in report.warnings


class TestDeterminism:
    def test_identical_inputs_produce_deeply_equal_reports(self):
        records = (_make_record("a", date(2024, 12, 31), revenue=1000.0),)
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        analysis = _bare_analysis()
        first = assess_evidence_quality(records, business_facts, (), analysis, evaluated_at=EVALUATED_AT)
        second = assess_evidence_quality(records, business_facts, (), analysis, evaluated_at=EVALUATED_AT)
        assert first == second


def _bare_analysis():
    """A minimal stand-in exposing only the three attributes
    `assess_evidence_quality` reads (`.business_analysis.findings`,
    `.valuation_engine.findings`, `.risk_analysis.findings`) -- never a
    full, wrapper-validated `CanonicalAnalysis`, matching
    `_unsupported_findings`'s own "take the tuples directly" design."""

    class _Section:
        findings: tuple = ()

    class _Analysis:
        business_analysis = _Section()
        valuation_engine = _Section()
        risk_analysis = _Section()

    return _Analysis()

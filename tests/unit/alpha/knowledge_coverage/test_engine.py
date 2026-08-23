"""Tests for `atlas.alpha.knowledge_coverage.engine.assess_knowledge_coverage`
-- exercised through the real, top-level `assemble_analysis`/extraction
entry points with real `BusinessRecord`s, the same convention
`tests/unit/alpha/coverage/test_engine.py` already establishes.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from atlas.alpha.coverage.models import DimensionCoverageLevel
from atlas.alpha.evidence_quality import assess_evidence_quality
from atlas.alpha.evidence_quality.models import EvidenceDominance, EvidenceFreshness
from atlas.alpha.investment_case.capital_allocation_intelligence import extract_capital_allocation_history
from atlas.alpha.investment_case.company_profile import extract_company_profile
from atlas.alpha.investment_case.earnings_call import extract_earnings_call_knowledge
from atlas.alpha.investment_case.financial_history import extract_financial_history
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.growth_intelligence import extract_growth_knowledge
from atlas.alpha.investment_case.historical_valuation import extract_historical_valuation
from atlas.alpha.investment_case.regulatory_filings import extract_regulatory_filings
from atlas.alpha.investment_case.models import CurrentThesis, InvestmentCaseComposition
from atlas.alpha.knowledge_coverage import DOMAIN_GROUP, KnowledgeDomain, MissingKnowledgeReason, assess_knowledge_coverage
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal

EVALUATED_AT = GENERATED_AT


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
    result = ingest(document, evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _full_records():
    return (
        _make_record(
            "company_profile", None, "profile1", name="ASML", sector="Technology", industry="Semiconductors",
            country="Netherlands",
        ),
        _make_record("financial_statement", date(2022, 12, 31), "fy22", revenue=1000.0, free_cash_flow=200.0),
        _make_record("financial_statement", date(2023, 12, 31), "fy23", revenue=1100.0, free_cash_flow=240.0),
        _make_record("financial_statement", date(2024, 12, 31), "fy24", revenue=1250.0, free_cash_flow=300.0),
        _make_record("market_data_snapshot", date(2024, 12, 31), "mkt1", share_price=700.0, shares_outstanding=400.0),
        _make_record(
            "company_filing", date(2024, 12, 31), "filing1", form_type="10-K", accession_number="0001-24-000001",
        ),
    )


def _composition(records) -> InvestmentCaseComposition:
    engine_input, output = run_minimal()
    canonical_analysis = assemble_analysis(
        engine_input, output, is_thesis_stale=False, business_records=records, generated_at=EVALUATED_AT
    )
    business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
    market_facts = extract_valuation_facts_from_records(records, evaluated_at=EVALUATED_AT)
    financial_statement_intelligence = extract_financial_statement_history(records)
    return InvestmentCaseComposition(
        case_id="00000000-0000-0000-0000-0000000000aa",
        holding_context=None,
        canonical_analysis=canonical_analysis,
        current_thesis=CurrentThesis(
            latest_decision_reason=None, latest_decision_type=None, latest_observation_statement=None
        ),
        decision_history=(),
        observation_history=(),
        outcome_history=(),
        trade_log=(),
        is_thesis_stale=False,
        generated_at=EVALUATED_AT,
        company_profile=extract_company_profile("ASML", records),
        financial_history=extract_financial_history(records),
        business_facts=business_facts,
        market_facts=market_facts,
        regulatory_filings=extract_regulatory_filings(records),
        historical_valuation=extract_historical_valuation(business_facts, market_facts),
        earnings_call=extract_earnings_call_knowledge(records),
        financial_statement_intelligence=financial_statement_intelligence,
        capital_allocation_intelligence=extract_capital_allocation_history(records),
        growth_intelligence=extract_growth_knowledge(financial_statement_intelligence),
    )


def _assess(records):
    composition = _composition(records)
    evidence_quality = assess_evidence_quality(
        records, composition.business_facts, composition.market_facts, composition.canonical_analysis,
        evaluated_at=EVALUATED_AT,
    )
    return assess_knowledge_coverage(composition, evidence_quality, records, evaluated_at=EVALUATED_AT)


def _domain(coverage, domain):
    return next(d for d in coverage.domains if d.domain is domain)


class TestFullDataIsAvailable:
    def test_company_profile_is_available(self):
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.COMPANY_PROFILE).level is DimensionCoverageLevel.AVAILABLE

    def test_financial_history_is_available_with_three_periods(self):
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.FINANCIAL_HISTORY).level is DimensionCoverageLevel.AVAILABLE

    def test_valuation_is_available(self):
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.VALUATION).level is DimensionCoverageLevel.AVAILABLE

    def test_regulatory_filings_is_available(self):
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.REGULATORY_FILINGS).level is DimensionCoverageLevel.AVAILABLE

    def test_governance_is_available_when_a_10k_is_ingested(self):
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.GOVERNANCE).level is DimensionCoverageLevel.AVAILABLE

    def test_governance_is_unavailable_when_only_a_non_governance_relevant_filing_is_ingested(self):
        """Capability Expansion Sprint 15: `REGULATORY_FILINGS` itself
        would still report `AVAILABLE` for an 8-K-only Case (any filing
        counts), but `GOVERNANCE` genuinely cannot derive anything from
        an 8-K that isn't Item 5.02 -- and Coverage's own cheap
        presence check does not open the filing to find out, so it
        honestly reports `UNAVAILABLE` rather than assume."""
        records = (
            _make_record(
                "company_filing", date(2024, 6, 1), "filing2", form_type="8-K", accession_number="0001-24-000002",
            ),
        )
        coverage = _assess(records)
        assert _domain(coverage, KnowledgeDomain.REGULATORY_FILINGS).level is DimensionCoverageLevel.AVAILABLE
        assert _domain(coverage, KnowledgeDomain.GOVERNANCE).level is DimensionCoverageLevel.UNAVAILABLE
        assert _domain(coverage, KnowledgeDomain.GOVERNANCE).missing_reasons == (
            MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,
        )

    def test_risk_factors_is_available_when_a_10k_is_ingested(self):
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.RISK_FACTORS).level is DimensionCoverageLevel.AVAILABLE

    def test_risk_factors_is_unavailable_when_only_a_non_risk_relevant_filing_is_ingested(self):
        """Capability Expansion Sprint 17: mirrors the identical
        `GOVERNANCE` guard above -- an 8-K carries no Item 1A/7 at all,
        and Coverage's own cheap presence check does not open the
        filing to find out."""
        records = (
            _make_record(
                "company_filing", date(2024, 6, 1), "filing2", form_type="8-K", accession_number="0001-24-000002",
            ),
        )
        coverage = _assess(records)
        assert _domain(coverage, KnowledgeDomain.RISK_FACTORS).level is DimensionCoverageLevel.UNAVAILABLE
        assert _domain(coverage, KnowledgeDomain.RISK_FACTORS).missing_reasons == (
            MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,
        )

    def test_risk_factors_is_available_when_only_a_10q_is_ingested(self):
        """Unlike `GOVERNANCE` (10-K/DEF 14A only), `RISK_FACTORS` also
        recognizes a 10-Q -- Part II Item 1A/Part I Item 2 carry real
        risk-factor-relevant content Filing Content Intelligence
        already detects."""
        records = (
            _make_record(
                "company_filing", date(2024, 6, 1), "filing3", form_type="10-Q", accession_number="0001-24-000003",
            ),
        )
        coverage = _assess(records)
        assert _domain(coverage, KnowledgeDomain.RISK_FACTORS).level is DimensionCoverageLevel.AVAILABLE

    def test_legal_proceedings_is_available_when_a_10k_is_ingested(self):
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.LEGAL_PROCEEDINGS).level is DimensionCoverageLevel.AVAILABLE

    def test_legal_proceedings_is_unavailable_when_only_a_non_legal_relevant_filing_is_ingested(self):
        """Capability Expansion Sprint 18: mirrors the identical
        `RISK_FACTORS`/`GOVERNANCE` guards above."""
        records = (
            _make_record(
                "company_filing", date(2024, 6, 1), "filing2", form_type="8-K", accession_number="0001-24-000002",
            ),
        )
        coverage = _assess(records)
        assert _domain(coverage, KnowledgeDomain.LEGAL_PROCEEDINGS).level is DimensionCoverageLevel.UNAVAILABLE
        assert _domain(coverage, KnowledgeDomain.LEGAL_PROCEEDINGS).missing_reasons == (
            MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,
        )

    def test_legal_proceedings_is_available_when_only_a_10q_is_ingested(self):
        """A 10-Q's own Part II Item 1 has no reliable section boundary
        in this build of Filing Content Intelligence, but Coverage's
        own cheap presence check is filing-metadata-level only -- it
        cannot see that limitation, and honestly shouldn't need to: a
        10-Q's own Risk Factors Update/MD&A sections (both reliably
        mapped) may still carry real, incidental legal disclosures."""
        records = (
            _make_record(
                "company_filing", date(2024, 6, 1), "filing3", form_type="10-Q", accession_number="0001-24-000003",
            ),
        )
        coverage = _assess(records)
        assert _domain(coverage, KnowledgeDomain.LEGAL_PROCEEDINGS).level is DimensionCoverageLevel.AVAILABLE

    def test_ownership_is_unavailable_when_only_a_10k_is_ingested(self):
        """Unlike `GOVERNANCE`/`RISK_FACTORS`/`LEGAL_PROCEEDINGS`,
        `OWNERSHIP`'s own real, reachable evidence is DEF 14A only --
        10-K's own real Item 12 has no item-map entry either (a smaller
        practical gap, since most real 10-Ks incorporate it by
        reference to the proxy rather than reprint it)."""
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.OWNERSHIP).level is DimensionCoverageLevel.UNAVAILABLE

    def test_ownership_is_available_when_a_def_14a_is_ingested(self):
        records = (
            _make_record(
                "company_filing", date(2024, 6, 1), "filing4", form_type="DEF 14A", accession_number="0001-24-000004",
            ),
        )
        coverage = _assess(records)
        assert _domain(coverage, KnowledgeDomain.OWNERSHIP).level is DimensionCoverageLevel.AVAILABLE

    def test_executive_compensation_is_unavailable_when_only_a_10k_is_ingested(self):
        """Mirrors `OWNERSHIP` exactly -- the Summary Compensation Table
        is DEF 14A-only, real, reachable evidence."""
        coverage = _assess(_full_records())
        assert _domain(coverage, KnowledgeDomain.EXECUTIVE_COMPENSATION).level is DimensionCoverageLevel.UNAVAILABLE

    def test_executive_compensation_is_available_when_a_def_14a_is_ingested(self):
        records = (
            _make_record(
                "company_filing", date(2024, 6, 1), "filing5", form_type="DEF 14A", accession_number="0001-24-000005",
            ),
        )
        coverage = _assess(records)
        assert _domain(coverage, KnowledgeDomain.EXECUTIVE_COMPENSATION).level is DimensionCoverageLevel.AVAILABLE

    def test_available_count_is_five(self):
        coverage = _assess(_full_records())
        # `_full_records()` carries revenue/free_cash_flow in all three
        # periods, meeting GROWTH's own >= 3 threshold for both --
        # AVAILABLE, the fifth domain alongside COMPANY_PROFILE/
        # FINANCIAL_HISTORY/VALUATION/REGULATORY_FILINGS.
        # `_full_records()`'s own COMPANY_FILING record is a 10-K, so
        # GOVERNANCE (Capability Expansion Sprint 15) is AVAILABLE too
        # -- the sixth domain. RISK_FACTORS (Capability Expansion
        # Sprint 17) is also AVAILABLE for the same 10-K -- the seventh.
        # LEGAL_PROCEEDINGS (Capability Expansion Sprint 18) is
        # AVAILABLE too (the same 10-K) -- the eighth.
        assert coverage.available_count == 8
        # `_full_records()` carries exactly one MARKET_DATA_SNAPSHOT
        # date, so HISTORICAL_VALUATION resolves to PARTIALLY_AVAILABLE
        # (a real current FCF yield, no history yet to range it against)
        # -- applicable (it has a real extractor now), just not AVAILABLE.
        # No TRANSCRIPT record exists in `_full_records()` at all, so
        # EARNINGS_CALL_ANALYSIS is UNAVAILABLE -- also applicable.
        # `_full_records()`'s own FINANCIAL_STATEMENT periods carry
        # revenue/free_cash_flow only -- no net_income/operating_cash_
        # flow/equity -- so PROFITABILITY/CASH_FLOW/BALANCE_SHEET each
        # resolve to PARTIALLY_AVAILABLE (real periods exist, the one
        # required field does not) -- also applicable.
        # `_full_records()` has no share_buybacks/share_issuance/debt_
        # issuance/debt_repayment either, so CAPITAL_ALLOCATION is
        # PARTIALLY_AVAILABLE too -- also applicable. GROWTH (newly
        # wired this sprint) is AVAILABLE, one more applicable domain.
        # GOVERNANCE (Capability Expansion Sprint 15) is AVAILABLE too
        # (a 10-K is ingested) -- one more applicable domain.
        # RISK_FACTORS (Capability Expansion Sprint 17) is AVAILABLE
        # too (the same 10-K) -- one more applicable domain.
        # LEGAL_PROCEEDINGS (Capability Expansion Sprint 18) is
        # AVAILABLE too (the same 10-K) -- one more applicable domain.
        # OWNERSHIP (Capability Expansion Sprint 19) is UNAVAILABLE for
        # this fixture (no DEF 14A ingested here) but still applicable
        # (it has a real extractor now) -- one more applicable domain,
        # not an available one. EXECUTIVE_COMPENSATION (Capability
        # Expansion Sprint 20) is the same story -- UNAVAILABLE for this
        # fixture, still applicable.
        assert coverage.applicable_count == 16

    def test_not_applicable_count_is_twenty_three(self):
        coverage = _assess(_full_records())
        # GROWTH moved out of NOT_APPLICABLE this sprint (it now has a
        # real extractor), so the previous 26 drops to 25. GOVERNANCE
        # (Capability Expansion Sprint 15) also gained a real extractor,
        # but it also added one to `total_domain_count` -- 37 - 12 == 25,
        # the same not-applicable count as before, unchanged. RISK_
        # FACTORS (Capability Expansion Sprint 17) gained a real
        # extractor too, but `RISK_FACTORS` already existed in the base
        # enum -- no new domain this time -- so 37 - 13 == 24, one lower.
        # LEGAL_PROCEEDINGS (Capability Expansion Sprint 18) is a
        # genuinely new domain, same as GOVERNANCE's own precedent --
        # both the wired count and the total go up by one, so
        # 38 - 14 == 24, unchanged again. OWNERSHIP (Capability
        # Expansion Sprint 19) already existed in the base enum, same
        # as RISK_FACTORS's own precedent -- so 38 - 15 == 23, one lower.
        # EXECUTIVE_COMPENSATION (Capability Expansion Sprint 20) is a
        # genuinely new domain, same as GOVERNANCE/LEGAL_PROCEEDINGS's
        # own precedent -- both counts go up by one, so 39 - 16 == 23,
        # unchanged again.
        assert coverage.not_applicable_count == 23
        assert coverage.total_domain_count == 39


class TestEmptyCaseIsHonestlyUnavailable:
    def test_company_profile_is_unavailable_with_no_records(self):
        coverage = _assess(())
        domain = _domain(coverage, KnowledgeDomain.COMPANY_PROFILE)
        assert domain.level is DimensionCoverageLevel.UNAVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,)

    def test_financial_history_is_unavailable_with_no_records(self):
        coverage = _assess(())
        domain = _domain(coverage, KnowledgeDomain.FINANCIAL_HISTORY)
        assert domain.level is DimensionCoverageLevel.UNAVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,)

    def test_valuation_is_unavailable_with_no_records(self):
        coverage = _assess(())
        domain = _domain(coverage, KnowledgeDomain.VALUATION)
        assert domain.level is DimensionCoverageLevel.UNAVAILABLE

    def test_regulatory_filings_is_unavailable_with_no_records(self):
        coverage = _assess(())
        domain = _domain(coverage, KnowledgeDomain.REGULATORY_FILINGS)
        assert domain.level is DimensionCoverageLevel.UNAVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,)

    def test_historical_valuation_is_unavailable_with_no_records(self):
        coverage = _assess(())
        domain = _domain(coverage, KnowledgeDomain.HISTORICAL_VALUATION)
        assert domain.level is DimensionCoverageLevel.UNAVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,)

    def test_earnings_call_is_unavailable_with_no_records(self):
        coverage = _assess(())
        domain = _domain(coverage, KnowledgeDomain.EARNINGS_CALL_ANALYSIS)
        assert domain.level is DimensionCoverageLevel.UNAVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,)

    def test_profitability_cash_flow_and_balance_sheet_are_unavailable_with_no_records(self):
        coverage = _assess(())
        for domain in (KnowledgeDomain.PROFITABILITY, KnowledgeDomain.CASH_FLOW, KnowledgeDomain.BALANCE_SHEET):
            domain_coverage = _domain(coverage, domain)
            assert domain_coverage.level is DimensionCoverageLevel.UNAVAILABLE
            assert domain_coverage.missing_reasons == (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,)

    def test_capital_allocation_is_unavailable_with_no_records(self):
        coverage = _assess(())
        domain = _domain(coverage, KnowledgeDomain.CAPITAL_ALLOCATION)
        assert domain.level is DimensionCoverageLevel.UNAVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,)

    def test_growth_is_unavailable_with_no_records(self):
        coverage = _assess(())
        domain = _domain(coverage, KnowledgeDomain.GROWTH)
        assert domain.level is DimensionCoverageLevel.UNAVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,)

    def test_every_not_yet_wired_domain_is_not_applicable_with_domain_not_yet_wired_reason(self):
        coverage = _assess(())
        for domain_coverage in coverage.domains:
            if domain_coverage.domain in (
                KnowledgeDomain.COMPANY_PROFILE, KnowledgeDomain.FINANCIAL_HISTORY, KnowledgeDomain.VALUATION,
                KnowledgeDomain.REGULATORY_FILINGS, KnowledgeDomain.HISTORICAL_VALUATION,
                KnowledgeDomain.EARNINGS_CALL_ANALYSIS, KnowledgeDomain.PROFITABILITY, KnowledgeDomain.CASH_FLOW,
                KnowledgeDomain.BALANCE_SHEET, KnowledgeDomain.CAPITAL_ALLOCATION, KnowledgeDomain.GROWTH,
                KnowledgeDomain.GOVERNANCE, KnowledgeDomain.RISK_FACTORS, KnowledgeDomain.LEGAL_PROCEEDINGS,
                KnowledgeDomain.OWNERSHIP, KnowledgeDomain.EXECUTIVE_COMPENSATION,
            ):
                continue
            assert domain_coverage.level is DimensionCoverageLevel.NOT_APPLICABLE
            assert domain_coverage.missing_reasons == (MissingKnowledgeReason.DOMAIN_NOT_YET_WIRED,)


class TestPartialCoverage:
    def test_company_profile_missing_sector_is_partially_available(self):
        records = (
            _make_record("company_profile", None, "profile1", name="ASML"),
            *[r for r in _full_records() if r.document_type.value != "company_profile"],
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.COMPANY_PROFILE)
        assert domain.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE
        assert MissingKnowledgeReason.DESCRIPTIVE_FIELDS_INCOMPLETE in domain.missing_reasons

    def test_financial_history_with_two_periods_is_partially_available(self):
        records = (
            _make_record("financial_statement", date(2023, 12, 31), "fy23", revenue=1100.0),
            _make_record("financial_statement", date(2024, 12, 31), "fy24", revenue=1250.0),
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.FINANCIAL_HISTORY)
        assert domain.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.INSUFFICIENT_HISTORY,)


class TestHistoricalValuationCoverage:
    """(Capability Expansion Sprint 1) `HISTORICAL_VALUATION`'s own
    three-tier presence: no market data at all -> `UNAVAILABLE`; a
    single market observation (real current FCF yield, no history to
    range it against) -> `PARTIALLY_AVAILABLE`; six or more distinct,
    valid observations -> `AVAILABLE` (mirrors `_data_quality`'s own
    `SUFFICIENT` threshold in `historical_valuation.py`)."""

    def test_a_single_market_observation_is_partially_available(self):
        records = (
            _make_record(
                "financial_statement", date(2024, 12, 31), "fy24", published_at=datetime(2024, 12, 31, tzinfo=timezone.utc),
                free_cash_flow=300.0,
            ),
            _make_record("market_data_snapshot", date(2024, 12, 31), "mkt1", share_price=700.0, shares_outstanding=400.0),
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.HISTORICAL_VALUATION)
        assert domain.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.INSUFFICIENT_HISTORY,)

    def test_six_distinct_observations_are_available(self):
        records = tuple(
            _make_record(
                "financial_statement", date(2018 + i, 12, 31), f"fy{i}", published_at=datetime(2018 + i, 12, 31, tzinfo=timezone.utc),
                free_cash_flow=100.0 + 10.0 * i,
            )
            for i in range(7)
        ) + tuple(
            _make_record(
                "market_data_snapshot", date(2018 + i, 12, 31), f"mkt{i}", share_price=50.0 + i, shares_outstanding=400.0,
            )
            for i in range(7)
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.HISTORICAL_VALUATION)
        assert domain.level is DimensionCoverageLevel.AVAILABLE
        assert domain.missing_reasons == ()


class TestEarningsCallCoverage:
    """(Capability Expansion Sprint 2) `EARNINGS_CALL_ANALYSIS`'s own
    three-tier presence: no transcript at all -> `UNAVAILABLE`; exactly
    one quarter's transcript (real knowledge, no Change Intelligence
    possible yet) -> `PARTIALLY_AVAILABLE`; two or more quarters ->
    `AVAILABLE`."""

    def _transcript_records(self, quarter: str, period_end: date, published_at: datetime, statement_count: int = 3):
        return tuple(
            _make_record(
                "transcript", period_end, f"{quarter}-{i}", published_at=published_at,
                quarter=quarter, statement_index=i, speaker="CEO", title="Chief Executive Officer",
                content=f"Statement number {i} for {quarter}.", sentiment=0.5,
            )
            for i in range(statement_count)
        )

    def test_one_quarter_is_partially_available(self):
        records = self._transcript_records("2026Q1", date(2026, 3, 31), GENERATED_AT)
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.EARNINGS_CALL_ANALYSIS)
        assert domain.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.INSUFFICIENT_HISTORY,)

    def test_two_quarters_are_available(self):
        records = self._transcript_records(
            "2025Q4", date(2025, 12, 31), GENERATED_AT
        ) + self._transcript_records("2026Q1", date(2026, 3, 31), GENERATED_AT)
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.EARNINGS_CALL_ANALYSIS)
        assert domain.level is DimensionCoverageLevel.AVAILABLE
        assert domain.missing_reasons == ()


class TestFinancialStatementIntelligenceCoverage:
    """(Capability Expansion Sprint 3) `PROFITABILITY`/`CASH_FLOW`/
    `BALANCE_SHEET` each need >= 3 periods with their own required
    field to reach `AVAILABLE` -- `_full_records()`'s own 3 periods
    lack `net_income`/`operating_cash_flow`/`equity` entirely, so they
    stay `PARTIALLY_AVAILABLE` (covered by `TestFullDataIsAvailable`'s
    own count assertions); this class exercises the real `AVAILABLE`
    case with a dedicated fixture."""

    def _records_with(self, **extra_metadata):
        return tuple(
            _make_record(
                "financial_statement", date(2020 + i, 12, 31), f"fy{i}", revenue=1000.0, **extra_metadata,
            )
            for i in range(3)
        )

    def test_profitability_is_available_with_three_periods_of_net_income(self):
        coverage = _assess(self._records_with(net_income=100.0))
        domain = _domain(coverage, KnowledgeDomain.PROFITABILITY)
        assert domain.level is DimensionCoverageLevel.AVAILABLE

    def test_cash_flow_is_available_with_three_periods_of_operating_cash_flow(self):
        coverage = _assess(self._records_with(operating_cash_flow=150.0))
        domain = _domain(coverage, KnowledgeDomain.CASH_FLOW)
        assert domain.level is DimensionCoverageLevel.AVAILABLE

    def test_balance_sheet_is_available_with_three_periods_of_equity(self):
        coverage = _assess(self._records_with(equity=700.0))
        domain = _domain(coverage, KnowledgeDomain.BALANCE_SHEET)
        assert domain.level is DimensionCoverageLevel.AVAILABLE


class TestCapitalAllocationCoverage:
    """(Capability Expansion Sprint 4) `CAPITAL_ALLOCATION` needs >= 3
    periods with at least one of its core signal facts (buybacks/
    issuance/debt activity) to reach `AVAILABLE`."""

    def test_available_with_three_periods_of_share_buybacks(self):
        records = tuple(
            _make_record("financial_statement", date(2020 + i, 12, 31), f"fy{i}", revenue=1000.0, share_buybacks=100.0)
            for i in range(3)
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.CAPITAL_ALLOCATION)
        assert domain.level is DimensionCoverageLevel.AVAILABLE


class TestGrowthCoverage:
    """(Capability Expansion Sprint 6) `GROWTH` needs >= 3 periods of
    BOTH revenue and free_cash_flow to reach `AVAILABLE` -- reusing the
    same generic `_freshness_dominance_from_facts` path as FINANCIAL_
    HISTORY/VALUATION/HISTORICAL_VALUATION/CAPITAL_ALLOCATION, since
    GROWTH's own underlying facts (REVENUE/FREE_CASH_FLOW) are already
    real `BusinessFactKind` members -- no dedicated freshness function
    was needed."""

    def test_available_with_three_periods_of_revenue_and_free_cash_flow(self):
        records = tuple(
            _make_record(
                "financial_statement", date(2020 + i, 12, 31), f"fy{i}", revenue=1000.0, free_cash_flow=200.0,
            )
            for i in range(3)
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.GROWTH)
        assert domain.level is DimensionCoverageLevel.AVAILABLE

    def test_partially_available_with_fewer_than_three_periods(self):
        records = (
            _make_record("financial_statement", date(2023, 12, 31), "fy23", revenue=1000.0, free_cash_flow=200.0),
            _make_record("financial_statement", date(2024, 12, 31), "fy24", revenue=1100.0, free_cash_flow=220.0),
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.GROWTH)
        assert domain.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE
        assert domain.missing_reasons == (MissingKnowledgeReason.INSUFFICIENT_HISTORY,)

    def test_partially_available_when_free_cash_flow_is_missing(self):
        records = tuple(
            _make_record("financial_statement", date(2020 + i, 12, 31), f"fy{i}", revenue=1000.0)
            for i in range(3)
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.GROWTH)
        assert domain.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE


class TestFreshnessRollup:
    def test_stale_financial_facts_roll_up_to_stale_freshness(self):
        old_published = GENERATED_AT - timedelta(days=400)
        records = tuple(
            _make_record("financial_statement", date(2020 + i, 12, 31), f"fy{i}", published_at=old_published, revenue=1000.0)
            for i in range(3)
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.FINANCIAL_HISTORY)
        assert domain.freshness is EvidenceFreshness.STALE
        assert MissingKnowledgeReason.EVIDENCE_STALE in domain.missing_reasons

    def test_fresh_financial_facts_roll_up_to_fresh_freshness(self):
        coverage = _assess(_full_records())
        domain = _domain(coverage, KnowledgeDomain.FINANCIAL_HISTORY)
        assert domain.freshness is EvidenceFreshness.FRESH

    def test_stale_filing_rolls_up_to_stale_freshness(self):
        old_published = GENERATED_AT - timedelta(days=400)
        records = (
            _make_record(
                "company_filing", date(2024, 12, 31), "filing1", published_at=old_published,
                form_type="10-K", accession_number="0001-24-000001",
            ),
        )
        coverage = _assess(records)
        domain = _domain(coverage, KnowledgeDomain.REGULATORY_FILINGS)
        assert domain.freshness is EvidenceFreshness.STALE
        assert MissingKnowledgeReason.EVIDENCE_STALE in domain.missing_reasons

    def test_fresh_filing_rolls_up_to_fresh_freshness(self):
        coverage = _assess(_full_records())
        domain = _domain(coverage, KnowledgeDomain.REGULATORY_FILINGS)
        assert domain.freshness is EvidenceFreshness.FRESH


class TestExhaustiveness:
    def test_every_domain_appears_exactly_once(self):
        coverage = _assess(_full_records())
        domains_seen = [d.domain for d in coverage.domains]
        assert len(domains_seen) == len(KnowledgeDomain)
        assert set(domains_seen) == set(KnowledgeDomain)

    def test_domain_group_mapping_is_exhaustive(self):
        assert set(DOMAIN_GROUP.keys()) == set(KnowledgeDomain)

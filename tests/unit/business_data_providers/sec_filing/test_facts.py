"""Reading one SEC filing's XBRL instance as dimensional evidence.

Every fragment below is copied verbatim out of a real cached filing --
GOOGL, VST and AMAT 10-Ks fetched during SEC Inline XBRL Evidence
Ingestion v1. Invented fixtures would agree with whatever the reader
happened to do; these disagree when it is wrong, and each one is here
because it caught something.
"""
import pytest

from atlas.business_data_providers.dimensional_evidence import AxisClass, PeriodKind, ValueStatus
from atlas.business_data_providers.sec_filing.axes import classify_sec_axis
from atlas.business_data_providers.sec_filing.facts import (
    FilingIdentity,
    filing_facts,
    typed_members,
)

HEAD = """<?xml version="1.0" encoding="utf-8"?>
<xbrl xml:lang="en-US"
  xmlns="http://www.xbrl.org/2003/instance"
  xmlns:dei="http://xbrl.sec.gov/dei/2025"
  xmlns:goog="http://www.google.com/20251231"
  xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
  xmlns:srt="http://fasb.org/srt/2025"
  xmlns:us-gaap="http://fasb.org/us-gaap/2025"
  xmlns:xbrldi="http://xbrl.org/2006/xbrldi">
  <unit id="usd"><measure>iso4217:USD</measure></unit>
  <unit id="shares"><measure>shares</measure></unit>
"""
TAIL = "</xbrl>"

# GOOGL's own two-axis segment context, verbatim.
CTX_SEGMENT = """
  <context id="c-57">
    <entity><identifier scheme="http://www.sec.gov/CIK">0001652044</identifier>
      <segment>
        <xbrldi:explicitMember dimension="srt:ProductOrServiceAxis">goog:GoogleSearchOtherMember</xbrldi:explicitMember>
        <xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">goog:GoogleServicesMember</xbrldi:explicitMember>
      </segment>
    </entity>
    <period><startDate>2023-01-01</startDate><endDate>2023-12-31</endDate></period>
  </context>
"""
CTX_PLAIN = """
  <context id="c-1">
    <entity><identifier scheme="http://www.sec.gov/CIK">0001652044</identifier></entity>
    <period><startDate>2025-01-01</startDate><endDate>2025-12-31</endDate></period>
  </context>
"""
CTX_INSTANT = """
  <context id="c-19">
    <entity><identifier scheme="http://www.sec.gov/CIK">0001652044</identifier></entity>
    <period><instant>2025-12-31</instant></period>
  </context>
"""
# VST files its revenue backlog by year as a TYPED member. The shared
# instance reader reports only that a context had one.
CTX_TYPED_A = """
  <context id="c-375">
    <entity><identifier scheme="http://www.sec.gov/CIK">0001692819</identifier>
      <segment><xbrldi:typedMember dimension="us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis"><us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis.domain>2026-01-01</us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis.domain></xbrldi:typedMember></segment>
    </entity>
    <period><instant>2025-12-31</instant></period>
  </context>
"""
CTX_TYPED_B = CTX_TYPED_A.replace("c-375", "c-376").replace("2026-01-01", "2027-01-01")

F_SEGMENT = ('<us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax contextRef="c-57" '
             'decimals="-6" id="f-482" unitRef="usd">175033000000'
             '</us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax>')
F_EXTENSION = ('<goog:OtherBetsMember contextRef="c-1" decimals="-6" id="f-9" unitRef="usd">1234000000'
               '</goog:OtherBetsMember>')
F_DEI = ('<dei:EntityCentralIndexKey contextRef="c-1" id="f-2">0001652044'
         '</dei:EntityCentralIndexKey>')
F_DOCTYPE = '<dei:DocumentType contextRef="c-1" id="f-3">10-K</dei:DocumentType>'
F_PERIOD_END = ('<dei:DocumentPeriodEndDate contextRef="c-1" id="f-4">2025-12-31'
                '</dei:DocumentPeriodEndDate>')
F_INSTANT = ('<us-gaap:UnrecognizedTaxBenefits contextRef="c-19" decimals="-6" id="f-7" '
             'unitRef="usd">12619000000</us-gaap:UnrecognizedTaxBenefits>')
# GOOGL files the same figure twice, once exact and once rounded.
F_ROUNDED = F_INSTANT.replace('decimals="-6"', 'decimals="-8"').replace(
    ">12619000000<", ">12600000000<").replace('id="f-7"', 'id="f-8"')
F_UNPARSABLE = ('<us-gaap:PropertyPlantAndEquipmentUsefulLife contextRef="c-1" id="f-11">P7Y'
                '</us-gaap:PropertyPlantAndEquipmentUsefulLife>')
F_TYPED_A = ('<us-gaap:RevenueRemainingPerformanceObligation contextRef="c-375" decimals="-6" '
             'id="f-20" unitRef="usd">1768000000</us-gaap:RevenueRemainingPerformanceObligation>')
F_TYPED_B = ('<us-gaap:RevenueRemainingPerformanceObligation contextRef="c-376" decimals="-6" '
             'id="f-21" unitRef="usd">1665000000</us-gaap:RevenueRemainingPerformanceObligation>')

IDENTITY = FilingIdentity(
    cik="0001652044", accession="0001652044-26-000018",
    primary_document="goog-20251231.htm",
    primary_document_url="https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm",
    instance_document="goog-20251231_htm.xml",
    instance_url="https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231_htm.xml",
    form_type="10-K",
)


def instance(*parts):
    return HEAD + "".join(parts) + TAIL


def read(*parts, identity=IDENTITY):
    return filing_facts(instance(*parts), identity)


def one(*parts):
    _, facts = read(*parts)
    return facts[0]


# ------------------------------------------------------------ 7,8,9,10
def test_the_filing_keeps_its_accession_and_document_identity():
    resolved, _ = read(CTX_PLAIN, F_DEI, F_DOCTYPE, F_PERIOD_END)
    assert resolved.accession == "0001652044-26-000018"
    assert resolved.primary_document == "goog-20251231.htm"
    assert resolved.instance_document == "goog-20251231_htm.xml"
    assert resolved.source_locator == "0001652044-26-000018:goog-20251231.htm"
    assert resolved.form_type == "10-K"
    assert resolved.period_end == "2025-12-31"


def test_the_filer_is_the_cik_never_the_ticker():
    resolved, facts = read(CTX_PLAIN, F_DEI)
    assert resolved.cik == "0001652044"
    assert all(f.entity == "0001652044" for f in facts)
    assert not any("GOOG" in f.entity.upper() for f in facts)


def test_the_cik_comes_from_the_filing_itself_when_it_states_one():
    wrong = FilingIdentity(
        cik="0000000000", accession=IDENTITY.accession, primary_document=IDENTITY.primary_document,
        primary_document_url=IDENTITY.primary_document_url,
        instance_document=IDENTITY.instance_document, instance_url=IDENTITY.instance_url)
    resolved, _ = read(CTX_PLAIN, F_DEI, identity=wrong)
    assert resolved.cik == "0001652044"


# --------------------------------------------------------------- 10-13
def test_a_standard_us_gaap_fact_keeps_its_raw_qname():
    _, facts = read(CTX_PLAIN, F_DEI, F_INSTANT.replace('contextRef="c-19"', 'contextRef="c-1"'))
    assert any(f.concept == "us-gaap:UnrecognizedTaxBenefits" for f in facts)


def test_an_issuer_extension_concept_is_not_mapped_to_a_standard_one():
    _, facts = read(CTX_PLAIN, F_DEI, F_EXTENSION)
    extension = next(f for f in facts if f.concept.startswith("goog:"))
    assert extension.concept == "goog:OtherBetsMember"


def test_a_dei_fact_is_read_like_any_other():
    _, facts = read(CTX_PLAIN, F_DEI, F_DOCTYPE)
    assert any(f.concept == "dei:DocumentType" and f.value_text == "10-K" for f in facts)


# --------------------------------------------------------------- 14-16
def test_a_fact_with_no_dimensions_is_kept():
    _, facts = read(CTX_PLAIN, F_DEI)
    assert facts and all(f.dimensions == () for f in facts)


def test_a_fact_carries_every_dimension_its_context_declares():
    fact = one(CTX_SEGMENT, F_SEGMENT)
    assert len(fact.dimensions) == 2
    assert {d.axis_qname for d in fact.dimensions} == {
        "srt:ProductOrServiceAxis", "us-gaap:StatementBusinessSegmentsAxis"}


def test_a_second_dimension_is_never_dropped():
    # The segment axis alone would say "Google Services revenue"; with
    # the product axis it says "Google Services, Search and other".
    fact = one(CTX_SEGMENT, F_SEGMENT)
    assert any(d.axis_class is AxisClass.BUSINESS_SEGMENT for d in fact.dimensions)
    assert any(d.axis_class is AxisClass.PRODUCT_OR_SERVICE for d in fact.dimensions)


# --------------------------------------------------------------- 17-21
def test_the_segment_axis_is_classified_as_a_business_segment():
    assert classify_sec_axis("us-gaap:StatementBusinessSegmentsAxis") is AxisClass.BUSINESS_SEGMENT


def test_the_consolidation_axis_is_not_a_segment_axis():
    # The same trap ESEF sets: the name contains segment-adjacent words
    # and its members are OperatingSegments / CorporateAndReconciling,
    # a consolidation vocabulary rather than a list of businesses.
    assert classify_sec_axis("srt:ConsolidationItemsAxis") is AxisClass.CONSOLIDATION_SCOPE


def test_three_axes_that_share_a_prefix_are_classified_apart():
    # `StatementBusinessSegmentsAxis`, `StatementEquityComponentsAxis`
    # and `StatementGeographicalAxis` all begin the same way and mean
    # three different things. Any rule that matches on a prefix or a
    # substring collapses them into whichever is listed first, which
    # would file every equity component and every geography as a
    # business segment -- the single worst error this module can make.
    assert classify_sec_axis("us-gaap:StatementBusinessSegmentsAxis") is AxisClass.BUSINESS_SEGMENT
    assert classify_sec_axis("us-gaap:StatementEquityComponentsAxis") is AxisClass.EQUITY_COMPONENT
    assert classify_sec_axis("srt:StatementGeographicalAxis") is AxisClass.GEOGRAPHY
    assert len({
        classify_sec_axis("us-gaap:StatementBusinessSegmentsAxis"),
        classify_sec_axis("us-gaap:StatementEquityComponentsAxis"),
        classify_sec_axis("srt:StatementGeographicalAxis"),
    }) == 3


def test_a_product_axis_is_not_a_segment_axis():
    # 298 facts across the four filings, and 15 of GOOGL's 81 segment
    # facts carry both -- so treating a product as a segment would
    # double count the segment it sits inside.
    assert classify_sec_axis("srt:ProductOrServiceAxis") is AxisClass.PRODUCT_OR_SERVICE


def test_a_legal_entity_is_not_a_business_segment():
    # A subsidiary is neither an elimination nor a reportable segment.
    assert classify_sec_axis("srt:ConsolidatedEntitiesAxis") is AxisClass.LEGAL_ENTITY


def test_an_axis_the_table_has_never_seen_is_unknown_not_guessed():
    # 75 axes appear across four filings; 9 are classified. This one is
    # among the 66 that are not, and it must stay that way rather than
    # being matched on the word "Instrument" or "Risk".
    assert classify_sec_axis("us-gaap:DerivativeInstrumentRiskAxis") is AxisClass.UNKNOWN


def test_an_unknown_axis_is_preserved_in_full_not_discarded():
    context = CTX_SEGMENT.replace(
        "us-gaap:StatementBusinessSegmentsAxis", "us-gaap:DerivativeInstrumentRiskAxis")
    fact = one(context, F_SEGMENT)
    unknown = next(d for d in fact.dimensions if d.axis_class is AxisClass.UNKNOWN)
    assert unknown.axis_qname == "us-gaap:DerivativeInstrumentRiskAxis"


def test_a_member_keeps_its_namespace_and_spelling():
    fact = one(CTX_SEGMENT, F_SEGMENT)
    member = next(d for d in fact.dimensions if d.axis_class is AxisClass.BUSINESS_SEGMENT)
    assert member.member_qname == "goog:GoogleServicesMember"
    assert member.member_namespace == "goog"
    assert member.member_is_issuer_extension


# --------------------------------------------------------------- 22-24
def test_a_duration_period_is_read_as_filed():
    # No following-midnight correction, unlike ESEF: an SEC context
    # writes the real end date, and subtracting a day would move every
    # figure into the wrong year.
    fact = one(CTX_SEGMENT, F_SEGMENT)
    assert fact.period_kind is PeriodKind.DURATION
    assert fact.period_raw == "2023-01-01/2023-12-31"
    assert fact.period_end == "2023-12-31"


def test_an_instant_period_is_read_as_filed():
    fact = one(CTX_INSTANT, F_INSTANT)
    assert fact.period_kind is PeriodKind.INSTANT
    assert fact.period_end == "2025-12-31"


def test_the_unit_keeps_its_namespace():
    # `iso4217:USD` is a currency by construction; `USD` is a string
    # that happens to look like one.
    fact = one(CTX_SEGMENT, F_SEGMENT)
    assert fact.unit == "iso4217:USD"


def test_a_per_share_unit_is_not_flattened_to_nothing():
    # The shared reader returns None for any unit built from a divide,
    # which is the same answer it gives for a fact with no unit at all.
    # Every benchmark filing has exactly one such unit, and 229 facts
    # across the four hang off it.
    eps_unit = ('<unit id="usdPerShare"><divide>'
                '<unitNumerator><measure>iso4217:USD</measure></unitNumerator>'
                '<unitDenominator><measure>shares</measure></unitDenominator>'
                '</divide></unit>')
    eps = ('<us-gaap:EarningsPerShareBasic contextRef="c-1" decimals="2" id="f-30" '
           'unitRef="usdPerShare">9.57</us-gaap:EarningsPerShareBasic>')
    _, facts = filing_facts(HEAD + eps_unit + CTX_PLAIN + F_DEI + eps + TAIL, IDENTITY)
    per_share = next(f for f in facts if f.concept.endswith("EarningsPerShareBasic"))
    assert per_share.unit == "iso4217:USD/shares"


def test_one_concept_and_context_filed_in_two_currencies_keeps_both():
    # MA files eight figures in both USD and INR under one context.
    # Collapsing them would put a rupee number under a dollar unit.
    inr_unit = '<unit id="inr"><measure>iso4217:INR</measure></unit>'
    usd = ('<us-gaap:ShortTermBorrowings contextRef="c-1" decimals="-6" id="f-40" '
           'unitRef="usd">19000000</us-gaap:ShortTermBorrowings>')
    inr = ('<us-gaap:ShortTermBorrowings contextRef="c-1" decimals="-6" id="f-41" '
           'unitRef="inr">1600000000</us-gaap:ShortTermBorrowings>')
    _, facts = filing_facts(HEAD + inr_unit + CTX_PLAIN + F_DEI + usd + inr + TAIL, IDENTITY)
    borrowings = [f for f in facts if f.concept.endswith("ShortTermBorrowings")]
    assert {f.unit for f in borrowings} == {"iso4217:USD", "iso4217:INR"}
    assert len({f.semantic_key for f in borrowings}) == 2


# --------------------------------------------------------------- 25,26
def test_a_numeric_value_is_marked_numeric():
    assert one(CTX_SEGMENT, F_SEGMENT).value_status is ValueStatus.NUMERIC


def test_a_value_that_is_not_a_number_is_kept_and_marked_unusable():
    # `P7Y` is a real filed value -- an ISO duration, not a failure --
    # and the guarantee is only that nothing can read it as a quantity.
    _, facts = read(CTX_PLAIN, F_DEI, F_UNPARSABLE)
    life = next(f for f in facts if f.concept.endswith("UsefulLife"))
    assert life.value_text == "P7Y"
    assert life.value_status is ValueStatus.UNPARSABLE


# ------------------------------------------------------------------ 27
def test_the_same_figure_at_two_precisions_is_two_observations():
    # GOOGL files unrecognised tax benefits as both 12,619m and 12,600m
    # against one context. They are one measurement stated twice, and
    # the exact one is only recoverable if the rounded one did not
    # overwrite it.
    _, facts = read(CTX_INSTANT, F_INSTANT, F_ROUNDED)
    assert len({f.semantic_key for f in facts}) == 2
    assert {f.value_text for f in facts} == {"12619000000", "12600000000"}


def test_two_filings_of_the_same_coordinates_are_two_facts():
    later = FilingIdentity(
        cik=IDENTITY.cik, accession="0001652044-27-000001",
        primary_document="goog-20261231.htm", primary_document_url="x", instance_document="y",
        instance_url="z")
    a = one(CTX_SEGMENT, F_SEGMENT)
    b = one(CTX_SEGMENT, F_SEGMENT.replace("175033000000", "180000000000"))
    b_later = filing_facts(instance(CTX_SEGMENT, F_SEGMENT), later)[1][0]
    assert a.semantic_key != b_later.semantic_key
    assert a.semantic_key == b.semantic_key      # same filing, same coordinates


# --------------------------------------------------------------- typed
def test_a_typed_member_is_read_although_the_shared_reader_drops_it():
    members = typed_members(instance(CTX_TYPED_A, F_TYPED_A))
    assert members["c-375"] == ((
        "us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis",
        "2026-01-01"),)


def test_two_facts_differing_only_by_a_typed_member_are_two_facts():
    # VST's revenue backlog by year. Without the typed value in the
    # dimension set these collapse and five of six years disappear.
    _, facts = read(CTX_TYPED_A, CTX_TYPED_B, F_TYPED_A, F_TYPED_B)
    assert len({f.semantic_key for f in facts}) == 2
    assert {f.value_text for f in facts} == {"1768000000", "1665000000"}


def test_a_typed_member_is_classified_unknown():
    fact = one(CTX_TYPED_A, F_TYPED_A)
    assert fact.dimensions[0].axis_class is AxisClass.UNKNOWN


# --------------------------------------------------- reader dependency
def test_this_module_does_not_reach_into_the_share_class_adapter():
    # The plumbing lives in `xbrl_instance` precisely so that it does
    # not. An existing firewall enumerates who may import the
    # share-class adapter, and reading an XBRL instance is not a reason
    # to be on that list.
    import ast
    import pathlib

    source = pathlib.Path(
        "atlas/business_data_providers/sec_filing/facts.py").read_text(encoding="utf-8")
    imported = {n.module for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ImportFrom)}
    assert "atlas.business_data_providers.xbrl_instance" in imported
    assert not any("share_classes" in (m or "") for m in imported)


def test_a_malformed_instance_raises_rather_than_returning_nothing():
    from atlas.business_data_providers.errors import MalformedProviderResponse

    with pytest.raises(MalformedProviderResponse):
        filing_facts("<xbrl><unclosed>", IDENTITY)

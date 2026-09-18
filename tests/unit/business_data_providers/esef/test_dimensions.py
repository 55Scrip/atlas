"""Dimensional ESEF evidence -- the facts normalization discards.

Every fact in this file is copied verbatim from a cached real report, so
a test that passes here passes against the corpus. The two Volvo identity
problems are real and are the point of several tests: the issuer's 2022
taxonomy declares `FinancialServciesMember` and `FinancialServicesMember`
as separate elements, and labels the first "Financial Servcies (member)"
-- the misspelling reproduced in the issuer's own label.
"""
from atlas.business_data_providers.esef.dimensions import (
    AxisClass,
    PeriodKind,
    ValueStatus,
    classify_axis,
    dimensional_facts,
)
from atlas.business_data_providers.esef.normalization import duration_facts, instant_facts

# --- real facts, verbatim from the cached corpus ----------------------
SEGMENT_RND = {
    "value": "30957000000.0", "decimals": -6,
    "dimensions": {
        "concept": "ifrs-full:ResearchAndDevelopmentExpense",
        "entity": "scheme:549300HGV012CNC8JD22",
        "period": "2024-01-01T00:00:00/2025-01-01T00:00:00",
        "ifrs-full:SegmentConsolidationItemsAxis": "ifrs-full:OperatingSegmentsMember",
        "ifrs-full:SegmentsAxis": "abvolvo:IndustriverksamhetenMember",
        "unit": "iso4217:SEK"}}
SEGMENT_CAPEX = {
    "value": "4416000000.0", "decimals": -6,
    "dimensions": {
        "concept": "ifrs-full:PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",
        "entity": "scheme:549300HGV012CNC8JD22",
        "period": "2024-01-01T00:00:00/2025-01-01T00:00:00",
        "ifrs-full:SegmentConsolidationItemsAxis": "ifrs-full:OperatingSegmentsMember",
        "ifrs-full:SegmentsAxis": "abvolvo:IndustriverksamhetenMember",
        "unit": "iso4217:SEK"}}
EQUITY = {
    "value": "4795000000", "decimals": -6,
    "dimensions": {
        "concept": "ifrs-full:Equity", "entity": "scheme:549300VEBQPHRZBKUX38",
        "period": "2021-01-01T00:00:00",
        "ifrs-full:ComponentsOfEquityAxis": "ifrs-full:IssuedCapitalMember",
        "unit": "iso4217:SEK"}}
# Copied verbatim from the cache: the issuer's own inline-XBRL
# transform failed and the report carries this where the figure
# should be. 19 facts in the corpus look like this.
TRANSFORM_ERROR = {
    "value": "(ixTransformValueError)", "decimals": -6,
    "dimensions": {
        "concept": "ifrs-full:Equity", "entity": "scheme:549300VEBQPHRZBKUX38",
        "period": "2021-01-01T00:00:00",
        "ifrs-full:ComponentsOfEquityAxis": "ifrs-full:IssuedCapitalMember",
        "unit": "iso4217:SEK"}}
MULTI = {
    "value": "1505000000", "decimals": -6,
    "dimensions": {
        "concept": "ifrs-full:Equity", "entity": "scheme:5299008ZUAXN43LVZF54",
        "period": "2022-01-01T00:00:00",
        "ifrs-full:ComponentsOfEquityAxis": "ifrs-full:IssuedCapitalMember",
        "ifrs-full:RetrospectiveApplicationAndRetrospectiveRestatementAxis":
            "ifrs-full:PreviouslyStatedMember",
        "unit": "iso4217:SEK"}}
TYPO = {
    "value": "848000000", "decimals": -6,
    "dimensions": {
        "concept": "ifrs-full:ProfitLossFromOperatingActivities",
        "entity": "scheme:549300HGV012CNC8JD22",
        "period": "2022-01-01T00:00:00/2023-01-01T00:00:00",
        "ifrs-full:SegmentConsolidationItemsAxis": "abvolvo:FinancialServciesMember",
        "unit": "iso4217:SEK"}}
CORRECT_SPELLING = {
    "value": "900000000", "decimals": -6,
    "dimensions": {
        "concept": "ifrs-full:ProfitLossFromOperatingActivities",
        "entity": "scheme:549300HGV012CNC8JD22",
        "period": "2022-01-01T00:00:00/2023-01-01T00:00:00",
        "ifrs-full:SegmentConsolidationItemsAxis": "abvolvo:FinancialServicesMember",
        "unit": "iso4217:SEK"}}
CONSOLIDATED_REVENUE = {
    "value": "552764000000", "decimals": -6,
    "dimensions": {
        "concept": "ifrs-full:Revenue", "entity": "scheme:549300HGV012CNC8JD22",
        "period": "2023-01-01T00:00:00/2024-01-01T00:00:00", "unit": "iso4217:SEK"}}


def document(*facts):
    return {"facts": {f"f-{i}": fact for i, fact in enumerate(facts)}}


def one(fact):
    return dimensional_facts(document(fact))[0]


# --------------------------------------------------------------- 1,2,30
def test_a_dimensioned_fact_is_preserved():
    facts = dimensional_facts(document(SEGMENT_RND))
    assert len(facts) == 1
    assert facts[0].concept == "ifrs-full:ResearchAndDevelopmentExpense"
    assert facts[0].value_text == "30957000000.0"


def test_an_undimensioned_fact_is_not_taken_by_this_reader():
    assert dimensional_facts(document(CONSOLIDATED_REVENUE)) == ()


def test_the_two_readers_partition_the_document_exactly():
    # The guarantee that makes double counting impossible: a fact belongs
    # to the consolidated reader or to this one, never both.
    doc = document(CONSOLIDATED_REVENUE, SEGMENT_RND, EQUITY, MULTI)
    consolidated = duration_facts(doc, "ifrs-full:Revenue")
    assert consolidated, "the consolidated reader still sees its own fact"
    taken = {f.concept for f in dimensional_facts(doc)}
    assert "ifrs-full:Revenue" not in taken


def test_the_consolidated_reader_is_untouched_by_dimensioned_facts():
    # Volvo's real numbers: the consolidated revenue is 552,764 MSEK and
    # a segment figure must never be able to answer in its place.
    doc = document(CONSOLIDATED_REVENUE, SEGMENT_RND, SEGMENT_CAPEX)
    assert duration_facts(doc, "ifrs-full:Revenue") == {
        "2023-12-31": (552764000000.0, "iso4217:SEK")
    }
    assert instant_facts(doc, "ifrs-full:Equity") == {}


# ------------------------------------------------------------- 3,4,5,28
def test_an_equity_axis_is_never_a_business_segment():
    # 4,016 facts in the cached corpus sit on this axis -- the largest of
    # all. Reading "has dimensions" as "has segments" would turn a
    # statement of changes in equity into eight business units.
    fact = one(EQUITY)
    assert AxisClass.EQUITY_COMPONENT in fact.axis_classes
    assert not fact.is_business_segment


def test_the_segments_axis_is_a_business_segment():
    assert one(SEGMENT_RND).is_business_segment


def test_the_segment_consolidation_axis_is_not_a_segment_axis():
    # It contains "Segment" and is a consolidation vocabulary: its
    # standard members are eliminations and entity totals. The same axis
    # carries a business unit and the elimination that cancels part of
    # it, so summing its members as peers would be wrong.
    assert classify_axis("ifrs-full:SegmentConsolidationItemsAxis") is (
        AxisClass.CONSOLIDATION_SCOPE
    )
    assert not one(TYPO).is_business_segment


def test_an_unrecognised_axis_is_preserved_as_unknown():
    fact = one({"value": "1", "dimensions": {
        "concept": "ifrs-full:Revenue", "entity": "e", "period": "2024-01-01T00:00:00",
        "acme:SomeNovelAxis": "acme:SomeMember"}})
    assert fact.dimensions[0].axis_class is AxisClass.UNKNOWN
    assert fact.dimensions[0].axis_qname == "acme:SomeNovelAxis"
    assert fact.dimensions[0].member_qname == "acme:SomeMember"


def test_classification_is_by_exact_name_not_substring():
    # "SegmentConsolidationItemsAxis" contains "Segments"... nearly. A
    # substring rule would get the single most important distinction in
    # this module backwards.
    assert classify_axis("ifrs-full:SegmentsAxis") is AxisClass.BUSINESS_SEGMENT
    assert classify_axis("acme:SegmentsAxis") is AxisClass.UNKNOWN
    assert classify_axis("acme:MySegmentsAxisExtension") is AxisClass.UNKNOWN


# ------------------------------------------------------------ 6,7,8,9,23
def test_raw_axis_and_member_identity_survive_intact():
    dimension = one(SEGMENT_RND).dimensions[1]
    assert dimension.axis_qname == "ifrs-full:SegmentsAxis"
    assert dimension.member_qname == "abvolvo:IndustriverksamhetenMember"
    assert dimension.axis_namespace == "ifrs-full"
    assert dimension.member_namespace == "abvolvo"
    assert dimension.member_is_issuer_extension


def test_an_issuer_extension_member_is_marked_as_one():
    assert one(TYPO).dimensions[0].member_is_issuer_extension
    assert not one(EQUITY).dimensions[0].member_is_issuer_extension


# ------------------------------------------------------------------ 25
def test_a_misspelled_member_is_not_corrected():
    # Volvo's 2022 schema declares `FinancialServciesMember` and
    # `FinancialServicesMember` as two separate elements, and labels the
    # first "Financial Servcies (member)". The taxonomy therefore offers
    # no evidence they are one segment -- it says the opposite -- so
    # correcting the spelling here would overwrite the filing.
    assert one(TYPO).dimensions[0].member_qname == "abvolvo:FinancialServciesMember"


def test_a_misspelled_member_is_a_different_fact_from_the_correct_one():
    typo, correct = dimensional_facts(document(TYPO, CORRECT_SPELLING))
    assert typo.semantic_key != correct.semantic_key
    assert one(TYPO).dimensions[0].member_qname != one(CORRECT_SPELLING).dimensions[0].member_qname


# ------------------------------------------------------------------ 24
def test_a_swedish_named_member_is_not_merged_with_its_english_counterpart():
    # `IndustriverksamhetenMember` is a *different element* from
    # `IndustrialOperationsMember`, on a different axis, in a later year
    # range. The English package labels `IndustrialOperationsMember`
    # "Industrial Operations (member)" and the Swedish package labels the
    # same element "Industriverksamheten (member)" -- which makes the
    # names suggestive and proves nothing about the other element.
    swedish = one(SEGMENT_RND).dimensions[1].member_qname
    assert swedish == "abvolvo:IndustriverksamhetenMember"
    english = one({"value": "1", "dimensions": {
        "concept": "ifrs-full:ResearchAndDevelopmentExpense", "entity": "e",
        "period": "2021-01-01T00:00:00/2022-01-01T00:00:00",
        "ifrs-full:SegmentsAxis": "abvolvo:IndustrialOperationsMember"}}).dimensions[0].member_qname
    assert swedish != english


# ------------------------------------------------------------------- 10
def test_a_fact_can_carry_several_axes():
    # 430 of the 6,177 dimensioned facts in the corpus do.
    fact = one(MULTI)
    assert len(fact.dimensions) == 2
    assert fact.axis_classes == {AxisClass.EQUITY_COMPONENT, AxisClass.RESTATEMENT_BASIS}


def test_a_second_axis_is_never_dropped():
    assert [d.axis_qname for d in one(MULTI).dimensions] == [
        "ifrs-full:ComponentsOfEquityAxis",
        "ifrs-full:RetrospectiveApplicationAndRetrospectiveRestatementAxis",
    ]


# ------------------------------------------------------------ 11,12,13,14
def test_duration_and_instant_periods_are_distinguished_and_corrected():
    duration = one(SEGMENT_RND)
    assert duration.period_kind is PeriodKind.DURATION
    assert duration.period_end == "2024-12-31"
    instant = one(EQUITY)
    assert instant.period_kind is PeriodKind.INSTANT
    # XBRL writes a closing balance as the following midnight.
    assert instant.period_raw == "2021-01-01T00:00:00"
    assert instant.period_end == "2020-12-31"


def test_unit_is_preserved_verbatim():
    assert one(SEGMENT_RND).unit == "iso4217:SEK"


def test_the_same_figure_in_two_currencies_is_two_facts():
    sek = dict(SEGMENT_RND)
    eur = {**SEGMENT_RND, "dimensions": {**SEGMENT_RND["dimensions"], "unit": "iso4217:EUR"}}
    a, b = dimensional_facts(document(sek, eur))
    assert a.semantic_key != b.semantic_key


def test_two_facts_differing_only_by_period_are_two_facts():
    # Everything identical except the period. If period left the
    # identity, one year's figure would overwrite another's.
    later = {**EQUITY, "dimensions": {**EQUITY["dimensions"],
                                      "period": "2022-01-01T00:00:00"}}
    a, b = dimensional_facts(document(EQUITY, later))
    assert a.period_end != b.period_end
    assert a.semantic_key != b.semantic_key


def test_an_instant_and_a_duration_ending_on_one_date_are_two_facts():
    duration = {**EQUITY, "dimensions": {
        **EQUITY["dimensions"], "period": "2020-01-01T00:00:00/2021-01-01T00:00:00"}}
    a, b = dimensional_facts(document(EQUITY, duration))
    assert a.period_end == b.period_end == "2020-12-31"
    assert a.semantic_key != b.semantic_key


# ---------------------------------------------------------- 15,19,20,21
def test_provenance_travels_with_every_fact():
    fact = dimensional_facts(document(SEGMENT_RND), source_locator="report-A.json")[0]
    assert fact.entity == "scheme:549300HGV012CNC8JD22"
    assert fact.source_locator == "report-A.json"
    assert fact.decimals == -6
    assert fact.period_raw == "2024-01-01T00:00:00/2025-01-01T00:00:00"
    assert fact.fact_id


def test_the_same_fact_twice_has_one_identity():
    a, b = dimensional_facts(document(SEGMENT_RND, dict(SEGMENT_RND)))
    assert a.semantic_key == b.semantic_key


def test_a_transform_error_is_kept_verbatim_and_marked_unusable():
    # Preserved, not dropped and not coerced to zero -- the source said
    # something, and what it said is that its own transform failed.
    fact = one(TRANSFORM_ERROR)
    assert fact.value_text == "(ixTransformValueError)"
    assert fact.value_status is ValueStatus.UNPARSABLE


def test_a_real_figure_is_marked_numeric():
    assert one(EQUITY).value_status is ValueStatus.NUMERIC
    assert one(SEGMENT_RND).value_status is ValueStatus.NUMERIC


def test_an_unrecognised_sentinel_is_unparsable_rather_than_assumed_numeric():
    # Decided by whether it parses, not by matching a list of sentinels
    # this reader happens to know.
    odd = {**TRANSFORM_ERROR, "value": "(someFutureErrorNobodyHasSeen)"}
    assert one(odd).value_status is ValueStatus.UNPARSABLE


def test_a_transform_error_does_not_take_a_real_figure_s_identity():
    # The two differ only by value, so they collide unless the report is
    # in the key -- which is exactly the case that used to let a broken
    # value overwrite a good one.
    good, = dimensional_facts(document(EQUITY), source_locator="2022.json")
    broken, = dimensional_facts(document(TRANSFORM_ERROR), source_locator="2023.json")
    assert good.semantic_key != broken.semantic_key


def test_the_same_coordinates_in_two_reports_are_two_facts():
    # A restated comparative is not the original figure, and the layer
    # that stores it must not be able to lose one behind the other.
    a = one(EQUITY)
    b, = dimensional_facts(document(EQUITY), source_locator="2024.json")
    assert a.semantic_key != b.semantic_key


def test_axis_order_does_not_change_identity():
    # Asserted on the key itself, with dimensions handed over unsorted.
    # Reading a document already sorts them, so a test that only goes
    # through the reader cannot tell whether the key sorts as well -- and
    # the key is what a second report's ordering would hit.
    from dataclasses import replace

    fact = one(MULTI)
    shuffled = replace(fact, dimensions=tuple(reversed(fact.dimensions)))
    assert shuffled.semantic_key == fact.semantic_key
    assert [d.axis_qname for d in shuffled.dimensions] != [
        d.axis_qname for d in fact.dimensions
    ]


def test_reading_is_deterministic_and_order_independent():
    forward = dimensional_facts(document(SEGMENT_RND, EQUITY, MULTI))
    backward = dimensional_facts(document(MULTI, EQUITY, SEGMENT_RND))
    assert sorted(f.semantic_key for f in forward) == sorted(f.semantic_key for f in backward)


# ------------------------------------------------------------- 26,27,29
def test_segment_research_spending_is_now_readable():
    # Sprint 8 reported research spending as having no channel at all.
    fact = one(SEGMENT_RND)
    assert fact.is_business_segment
    assert fact.concept == "ifrs-full:ResearchAndDevelopmentExpense"
    assert fact.period_end == "2024-12-31"


def test_segment_capital_purchases_are_now_readable():
    fact = one(SEGMENT_CAPEX)
    assert fact.is_business_segment
    assert "PurchaseOf" in fact.concept


def test_a_malformed_fact_is_skipped_without_losing_the_rest():
    doc = document(SEGMENT_RND, {"value": "1", "dimensions": {"acme:Axis": "acme:M"}}, EQUITY)
    facts = dimensional_facts(doc)
    # The fact with no concept cannot be identified and is left out; the
    # two around it are unaffected.
    assert len(facts) == 2

"""The dimensional attribution channel, held to the corpus that falsified it.

Every passage and every fact below is copied verbatim from VST's or
GOOGL's 2025 10-K, or from the transcript evidence behind a real
strategy node. The channel accepts nothing on the real corpus, so the
first test here is the one that proves it *could* -- a channel that
rejects everything because it rejects everything is not a standard.
"""
from dataclasses import dataclass

import pytest

from atlas.analysis_engine.strategy_attribution.contracts import (
    AttributionBasis,
    AttributionResolution,
)
from atlas.analysis_engine.strategy_attribution.dimensional import (
    EntityReference,
    MeasureKind,
    RejectionReason,
    classify_measure,
    compose,
    dimensional_candidates,
    entity_display_name,
    node_entity_edge,
)


@dataclass(frozen=True)
class Dim:
    axis_qname: str
    member_qname: str


@dataclass(frozen=True)
class Fact:
    fact_key: str
    concept: str
    value_text: str
    unit: str | None
    period_end: str | None
    source_locator: str
    dimensions: tuple


VST = "0001692819-26-000006:vistra-20251231.htm"
SEGMENT = "us-gaap:StatementBusinessSegmentsAxis"
PROPERTY = "srt:RealEstateAndAccumulatedDepreciationDescriptionOfPropertyAxis"
COMANCHE = "vistra:ComanchePeakNuclearPowerPlantMember"
MOSS = "vistra:MossLandingBatteryEnergyStorageSystemPhaseIMember"

# Management's own words behind VST's "data center" dependency.
COMANCHE_PASSAGE = ("However, our immediate priority is to ensure that everything necessary "
                    "for the data center at Comanche Peak is completed on schedule.")
# ... and behind "project financing".
WEST_TEXAS_PASSAGE = ("In addition to our planned solar and energy storage investments, we will "
                      "be allocating capital to our new gas-fired units in West Texas, which we "
                      "estimate will require approximately $900 million before any tax credits.")


def entity(member=COMANCHE, axis=PROPERTY):
    return EntityReference(member_qname=member, axis_qname=axis,
                           display_name=entity_display_name(member), source_locator=VST)


def fact(concept, value, unit=None, member=COMANCHE, axis=PROPERTY, period="2025-12-31"):
    return Fact(fact_key=f"k-{concept}-{value}", concept=concept, value_text=value, unit=unit,
                period_end=period, source_locator=VST, dimensions=(Dim(axis, member),))


def node(subject, passage, kind="dependency", node_id="n-1"):
    return (node_id, kind, subject, [(passage, "rec:v1", "2025Q4")])


# ------------------------------------------------- the channel can accept
def test_a_full_chain_is_accepted():
    # Constructed, not found: management names the asset, the filing
    # tags a megawatt figure to that asset, and the node is about
    # capacity. If this ever fails the rejections below prove nothing.
    passage = ("We completed the uprate at Comanche Peak, which now provides additional "
               "generation capacity to the grid.")
    (accepted,) = [c for c in dimensional_candidates(
        [node("nuclear uprates", passage)],
        [fact("vistra:ElectricGenerationFacilityCapacity", "2400", "utr:MW")],
    ) if c.accepted]
    assert accepted.basis is AttributionBasis.DERIVED_STRUCTURAL
    assert accepted.resolution is AttributionResolution.CAPACITY_ASSET
    assert accepted.entity.display_name == "Comanche Peak"
    assert "2400" in accepted.establishes
    assert "was added by the initiative" in accepted.does_not_establish
    assert "management's own statement, not independent" in accepted.does_not_establish


def test_an_accepted_chain_still_refuses_the_four_bigger_claims():
    passage = ("We completed the uprate at Comanche Peak, which now provides additional "
               "generation capacity to the grid.")
    (accepted,) = [c for c in dimensional_candidates(
        [node("nuclear uprates", passage)],
        [fact("vistra:ElectricGenerationFacilityCapacity", "2400", "utr:MW")],
    ) if c.accepted]
    for refused in ("added by the initiative", "changed", "caused", "not independent"):
        assert refused in accepted.does_not_establish


# ------------------------------------------- the real corpus, case by case
def test_comanche_peak_has_both_edges_and_is_still_rejected():
    # The strongest real candidate in the corpus. Management names the
    # plant; the filing tags six facts to it. Every one of them is a
    # decommissioning obligation, a trust's fair value, a regulatory
    # liability or an insurance limit -- nothing about a data centre.
    candidates = dimensional_candidates(
        [node("data center", COMANCHE_PASSAGE)],
        [fact("us-gaap:AssetRetirementObligation", "1838000000", "iso4217:USD"),
         fact("us-gaap:AssetsFairValueDisclosure", "2589000000", "iso4217:USD"),
         fact("us-gaap:RegulatoryLiabilities", "751000000", "iso4217:USD")],
    )
    assert candidates and not any(c.accepted for c in candidates)
    assert {c.rejection for c in candidates} == {RejectionReason.MEASURE_MISMATCH}
    assert all(c.node_edge is not None and c.fact_edge is not None for c in candidates)


def test_west_texas_does_not_name_the_texas_segment():
    # VST reports a Texas segment and management says "West Texas".
    # West Texas is a place inside ERCOT; the segment is a reporting
    # unit. Matching them would put Permian gas spending on a segment
    # that does not contain it.
    candidates = dimensional_candidates(
        [node("project financing", WEST_TEXAS_PASSAGE)],
        [fact("us-gaap:Revenues", "5000000000", "iso4217:USD",
              member="vistra:TexasSegmentMember", axis=SEGMENT)],
    )
    assert candidates == ()


def test_an_asset_the_strategy_never_names_yields_no_candidate():
    # Moss Landing carries ten facts and no VST strategy node mentions
    # it. Evidence without a strategy is not an attribution looking for
    # a home.
    assert dimensional_candidates(
        [node("data center", COMANCHE_PASSAGE)],
        [fact("us-gaap:ImpairmentOfLongLivedAssetsHeldForUse", "155000000", "iso4217:USD",
              member=MOSS, axis=SEGMENT)],
    ) == ()


# ---------------------------------------------- the three measure traps
def test_capacity_revenue_in_dollars_is_not_physical_capacity():
    # VST reports `NetCapacitySold` of $793m. The word is "capacity",
    # the unit is dollars, and only the unit is evidence.
    assert classify_measure("vistra:NetCapacitySold", "iso4217:USD") is not MeasureKind.PHYSICAL_CAPACITY
    assert classify_measure("vistra:NetCapacityPurchased", "iso4217:USD") is not MeasureKind.PHYSICAL_CAPACITY
    assert classify_measure("vistra:BatteryEnergyStorageSystemCapacity",
                            "utr:MW") is MeasureKind.PHYSICAL_CAPACITY


def test_borrowing_capacity_is_not_physical_capacity():
    # 20 of VST's 73 capacity-named facts are credit facilities.
    assert classify_measure("us-gaap:LineOfCreditFacilityMaximumBorrowingCapacity",
                            "iso4217:USD") is MeasureKind.BORROWING_CAPACITY
    passage = "We are adding generation capacity at Comanche Peak."
    candidates = dimensional_candidates(
        [node("megawatts", passage)],
        [fact("us-gaap:LineOfCreditFacilityMaximumBorrowingCapacity", "5890000000", "iso4217:USD")],
    )
    assert candidates and not any(c.accepted for c in candidates)


def test_retired_capacity_never_evidences_an_initiative_that_builds():
    assert classify_measure("vistra:ElectricGenerationFacilityCapacityAnnouncedRetirement",
                            "utr:MW") is MeasureKind.CAPACITY_RETIREMENT
    passage = "We are adding generation capacity at Comanche Peak."
    candidates = dimensional_candidates(
        [node("megawatts", passage)],
        [fact("vistra:ElectricGenerationFacilityCapacityAnnouncedRetirement", "1108", "utr:MW")],
    )
    assert candidates and not any(c.accepted for c in candidates)
    assert {c.rejection for c in candidates} == {RejectionReason.CONTRARY_EVIDENCE}


def test_an_impairment_never_evidences_progress():
    assert classify_measure("us-gaap:ImpairmentOfLongLivedAssetsHeldForUse",
                            "iso4217:USD") is MeasureKind.IMPAIRMENT
    passage = "We are adding generation capacity at Comanche Peak."
    candidates = dimensional_candidates(
        [node("megawatts", passage)],
        [fact("us-gaap:ImpairmentOfLongLivedAssetsHeldForUse", "155000000", "iso4217:USD")],
    )
    assert candidates and not any(c.accepted for c in candidates)
    # Named for what it is: the evidence points the other way, rather
    # than merely failing to point this way.
    assert {c.rejection for c in candidates} == {RejectionReason.CONTRARY_EVIDENCE}


def test_a_capacity_level_is_reported_as_a_level_and_never_as_an_addition():
    # Moss Landing Phase I reads 300 MW in January 2025 and 100 MW in
    # December, because of a fire. Two levels are not a change.
    passage = "We are adding generation capacity at Comanche Peak."
    (accepted,) = [c for c in dimensional_candidates(
        [node("megawatts", passage)],
        [fact("vistra:BatteryEnergyStorageSystemCapacity", "300", "utr:MW")],
    ) if c.accepted]
    assert "was reported" in accepted.establishes
    assert "that this capacity was added by the initiative, that it changed" in accepted.does_not_establish


def test_revenue_is_never_execution():
    passage = "We are investing capital at Comanche Peak."
    candidates = dimensional_candidates(
        [node("capital", passage)],
        [fact("us-gaap:Revenues", "17000000000", "iso4217:USD")],
    )
    assert candidates and not any(c.accepted for c in candidates)
    assert {c.rejection for c in candidates} == {RejectionReason.MEASURE_MISMATCH}


# ------------------------------------------------------- the two edges
def test_a_missing_node_entity_edge_is_named_as_such():
    result = compose(node_id="n", node_kind="initiative", subject_text="x",
                     entity=entity(), node_edge=None, fact_edge=None)
    assert result.rejection is RejectionReason.NO_NODE_ENTITY_LINK


def test_a_missing_entity_fact_edge_is_named_as_such():
    edge = node_entity_edge(node_id="n", passages=[(COMANCHE_PASSAGE, "r", "2025Q4")],
                            entity=entity())
    assert edge is not None
    result = compose(node_id="n", node_kind="initiative", subject_text="x",
                     entity=entity(), node_edge=edge, fact_edge=None)
    assert result.rejection is RejectionReason.NO_ENTITY_FACT_LINK


def test_an_ambiguous_entity_is_never_chosen_for():
    # VST files Comanche Peak alone and in two combined members. A name
    # that resolves to more than one member resolves to none.
    edge = node_entity_edge(node_id="n", passages=[(COMANCHE_PASSAGE, "r", "2025Q4")],
                            entity=entity())
    result = compose(node_id="n", node_kind="initiative", subject_text="capacity",
                     entity=entity(), node_edge=edge,
                     fact_edge=None, entity_is_ambiguous=True)
    assert result.rejection is RejectionReason.AMBIGUOUS_ENTITY


def test_a_passage_supporting_another_node_does_not_link_this_one():
    # Passages come from the node's own evidence, never the company's
    # whole transcript corpus.
    assert node_entity_edge(node_id="n", passages=[("We repurchased shares.", "r", "2025Q4")],
                            entity=entity()) is None


# -------------------------------------------------------- identity rules
def test_an_accounting_member_is_not_a_named_asset():
    # `CurrentAssetsMember` and `LandMember` split into title-cased
    # words exactly as a plant name does; management writes them in
    # lower case, which is the evidence that they are not names.
    assert dimensional_candidates(
        [node("capital", "We are disciplined in how we allocate capital across current assets and land.")],
        [fact("us-gaap:Revenues", "1", "iso4217:USD", member="vistra:CurrentAssetsMember"),
         fact("us-gaap:Revenues", "1", "iso4217:USD", member="us-gaap:LandMember")],
    ) == ()


def test_no_fuzzy_match_establishes_identity():
    # A near spelling is not the same asset.
    assert node_entity_edge(
        node_id="n", passages=[("the data center at Comanche Peek is on schedule", "r", "2025Q4")],
        entity=entity()) is None


def test_the_display_name_drops_the_asset_class_not_the_name():
    assert entity_display_name(COMANCHE) == "Comanche Peak"
    assert entity_display_name("vistra:KincaidGenerationMember") == "Kincaid"
    assert entity_display_name("goog:TechnicalInfrastructureMember") == "Technical Infrastructure"


# --------------------------------------------------------- invariants
def _corpus():
    nodes = [node("data center", COMANCHE_PASSAGE, node_id="a"),
             node("project financing", WEST_TEXAS_PASSAGE, kind="objective", node_id="b")]
    facts = [fact("us-gaap:AssetRetirementObligation", "1838000000", "iso4217:USD"),
             fact("vistra:BatteryEnergyStorageSystemCapacity", "300", "utr:MW"),
             fact("us-gaap:Revenues", "5000000000", "iso4217:USD",
                  member="vistra:TexasSegmentMember", axis=SEGMENT)]
    return nodes, facts


def _fingerprint(candidates):
    return sorted((c.node_id, c.entity.member_qname, c.accepted,
                   c.rejection.value if c.rejection else "",
                   c.fact_edge.fact_key if c.fact_edge else "") for c in candidates)


def test_the_channel_is_deterministic():
    nodes, facts = _corpus()
    assert _fingerprint(dimensional_candidates(nodes, facts)) == \
           _fingerprint(dimensional_candidates(nodes, facts))


def test_duplicate_evidence_does_not_duplicate_an_attribution():
    nodes, facts = _corpus()
    once = _fingerprint(dimensional_candidates(nodes, facts))
    twice = _fingerprint(dimensional_candidates(nodes, facts + facts))
    assert once == twice


def test_the_channel_is_order_independent():
    nodes, facts = _corpus()
    forward = _fingerprint(dimensional_candidates(nodes, facts))
    reverse = _fingerprint(dimensional_candidates(list(reversed(nodes)), list(reversed(facts))))
    assert forward == reverse


def test_the_channel_reads_no_clock():
    import ast
    import pathlib

    source = pathlib.Path(
        "atlas/analysis_engine/strategy_attribution/dimensional.py").read_text(encoding="utf-8")
    names = {n.attr for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Attribute)}
    assert "now" not in names and "today" not in names
    assert "datetime" not in source


def test_no_company_or_ticker_appears_in_the_channel():
    import pathlib

    source = pathlib.Path(
        "atlas/analysis_engine/strategy_attribution/dimensional.py").read_text(encoding="utf-8")
    code = "\n".join(line for line in source.splitlines()
                     if not line.lstrip().startswith("#"))
    code = code.split('"""')[0] + "".join(code.split('"""')[2::2])
    for ticker in ("VST", "GOOGL", "vistra:", "goog:", "Vistra", "Comanche", "Moss Landing"):
        assert ticker not in code, f"{ticker} appears in executable code"

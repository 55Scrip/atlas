"""Strategic Action Attribution v1 -- what may be placed, and what may not.

The audit behind this layer found that Atlas has no dimensional data of
any kind, sixteen quantified-purpose sentences across four benchmark
companies, and named projects for one of them. So most of these tests
assert that an attribution does *not* appear: the failure mode here is
not missing a link, it is inventing one out of a strategy and an action
that merely coexist.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from atlas.analysis_engine.strategy import compose_company_strategy
from atlas.analysis_engine.strategy_attribution import (
    ActionTense,
    AttributionBasis,
    AttributionResolution,
    AttributionStatus,
    EvidenceRef,
    EvidenceRole,
    LinkingFact,
    UNAVAILABLE_CHANNELS,
    company_attribution,
    extract_linking_facts,
)
from tests.unit.analysis_engine.strategy_corroboration._fixtures import financials
from tests.unit.analysis_engine.strategy_salience._fixtures import ANALYST, CEO, CFO, call

AT = datetime(2026, 9, 18, tzinfo=timezone.utc)

# AMAT's real sentence -- the only fully attributed node in the corpus.
ARIZONA = ("As part of this endeavor, we plan to invest more than $200 million in Arizona "
           "to establish a facility for manufacturing specialized components.")
BUILD = "We are building additional data center capacity to support demand."


def attribute(transcripts, statements=(), company="VST"):
    strategy = compose_company_strategy(transcripts, composed_at=AT)
    return company_attribution(strategy, tuple(transcripts) + tuple(statements), evaluated_at=AT)


def node_for(result, fragment):
    found = [n for n in result.nodes if fragment in n.subject_text]
    assert found, f"no node matching {fragment!r} in {[n.subject_text for n in result.nodes]}"
    return found[0]


# --------------------------------------------------------------- 1,2,33
def test_an_action_in_the_same_period_is_not_attribution():
    # The whole reason this layer exists. Reported capital expenditure
    # rising while management describes a build-out is corroboration;
    # nothing in it says where the money went.
    result = attribute(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q3"),
        [financials({"capital_expenditure": 52.53e9}, period_end=date(2024, 12, 31)),
         financials({"capital_expenditure": 91.45e9}, period_end=date(2025, 12, 31))],
    )
    node = node_for(result, "data center")
    assert node.status is AttributionStatus.NO_ATTRIBUTION_EVIDENCE
    assert node.links == ()


def test_sharing_a_canonical_factor_is_not_attribution():
    # Factor equality finds candidates. Matching on it alone gave VST's
    # nuclear, megawatt and PPA strategies the same six linking facts --
    # six strategies cannot each own the same 4,500 megawatts.
    result = attribute(
        call((CEO, "Pat Lee", BUILD),
             (CFO, "Sam Ray", "Separately, we added 860 megawatts of generation capacity."),
             quarter="2025Q3"),
    )
    for node in result.nodes:
        assert node.status is not AttributionStatus.ATTRIBUTED, node.subject_text


def test_no_narrative_chain_becomes_an_attribution():
    # The adversarial shape: a strategy that mentions the theme, an
    # action, revenue moving, and analysts asking. Each is real; none
    # links the action to the strategy.
    result = attribute(
        call((CEO, "Pat Lee", "We are building additional data center capacity for AI."),
             (CFO, "Sam Ray", "Capital expenditure increased materially this year."),
             (CFO, "Sam Ray", "Revenue also grew strongly."),
             (ANALYST, "Chris Vale", "How much of the AI data center spend is incremental?"),
             quarter="2025Q3"),
        [financials({"capital_expenditure": 52.53e9}, period_end=date(2024, 12, 31)),
         financials({"capital_expenditure": 91.45e9}, period_end=date(2025, 12, 31))],
    )
    assert all(n.status is not AttributionStatus.ATTRIBUTED for n in result.nodes)


# ------------------------------------------------------------- 4,5,7,32
def test_explicit_management_quantification_is_recorded_with_its_amount():
    result = attribute(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q3"), company="AMAT")
    node = next(n for n in result.nodes if n.links)
    link = node.links[0]
    assert link.basis is AttributionBasis.EXPLICIT_MANAGEMENT_QUANTIFICATION
    assert link.amount is not None
    # Management's hedge is part of the claim and is kept verbatim.
    assert link.amount.value_text == "more than $200 million"
    assert link.resolution is AttributionResolution.GEOGRAPHY
    assert link.target_name == "Arizona"


def test_management_attribution_is_never_independent_verification():
    result = attribute(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q3"), company="AMAT")
    node = next(n for n in result.nodes if n.links)
    assert node.attribution_is_management_authored
    assert not node.has_independent_action_evidence
    assert any("management's own account" in claim for claim in node.may_not_conclude)


def test_stated_intent_is_not_observed_action():
    # "we plan to invest" is an allocation of a plan. Turning it into an
    # allocation of spending is the most tempting error here: most
    # quantified statements in the corpus are future tense.
    result = attribute(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q3"), company="AMAT")
    node = next(n for n in result.nodes if n.links)
    assert node.links[0].tense is ActionTense.STATED_INTENT
    assert any("actually spent" in claim for claim in node.may_not_conclude)


def test_a_past_allocation_is_distinguished_from_an_intended_one():
    past = extract_linking_facts(
        call((CEO, "Pat Lee", "We invested $200 million in Arizona to build the facility."),
             quarter="2025Q3")[0]
    )
    future = extract_linking_facts(
        call((CEO, "Pat Lee", "We will invest $200 million in Arizona to build the facility."),
             quarter="2025Q3")[0]
    )
    assert past and past[0].tense is ActionTense.OBSERVED_PAST
    assert future and future[0].tense is ActionTense.STATED_INTENT


def test_a_sentence_that_is_both_past_and_forward_is_treated_as_intent():
    facts = extract_linking_facts(
        call((CEO, "Pat Lee",
              "We have invested $100 million in Arizona and expect to invest $200 million more."),
             quarter="2025Q3")[0]
    )
    assert facts and facts[0].tense is ActionTense.STATED_INTENT


# ------------------------------------------------------------ 8,9,10,11
def test_resolution_names_the_thing_it_resolves_to():
    with pytest.raises(ValueError, match="names the thing"):
        LinkingFact(
            basis=AttributionBasis.MANAGEMENT_NAMED_LINK,
            resolution=AttributionResolution.PROJECT, target_name="",
            evidence=EvidenceRef(role=EvidenceRole.LINKING, source_record_id="r",
                                 source_kind="transcript", period="2025Q3",
                                 published_at=None, semantic_owner="x"),
            tense=ActionTense.OBSERVED_PAST,
        )


def test_there_is_no_segment_resolution_to_mistake_for_an_initiative():
    # No dimensional key exists on any record in the corpus, so a
    # SEGMENT member would be a capability Atlas does not have -- and
    # the first segment figure it ever saw would be filed as though a
    # segment were an initiative.
    values = {r.value for r in AttributionResolution}
    assert "segment" not in values
    assert "business_line" not in values
    assert "initiative" not in values


def test_the_absent_channels_are_named_on_every_result():
    result = attribute(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"))
    assert result.unavailable_channels == UNAVAILABLE_CHANNELS
    joined = " ".join(result.unavailable_channels)
    assert "segment" in joined and "esef" in joined and "customer_contracts" in joined


# ------------------------------------------------------------- 12,13,30
def test_an_attributed_amount_never_allocates_the_residual():
    result = attribute(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q3"), company="AMAT")
    amount = next(n for n in result.nodes if n.links).links[0].amount
    assert amount.residual_is_unallocated
    assert any("beyond the attributed one" in claim for claim in amount.may_not_conclude)


def test_a_candidate_link_is_never_published_as_an_attribution():
    # A strategy about generation capacity and, in a different sentence,
    # a named megawatt addition: same canonical factor, no fact joining
    # them. Asserted as a count first, because a loop that finds no
    # candidate passes without executing its body.
    result = attribute(
        call((CEO, "Pat Lee", "We are expanding generation capacity across the fleet."),
             (CFO, "Sam Ray", "We added 860 megawatts at our Texas sites."),
             quarter="2025Q3"),
    )
    candidates = [n for n in result.nodes if n.status is AttributionStatus.CANDIDATE_ONLY]
    assert candidates, [n.status.value for n in result.nodes]
    for node in candidates:
        assert node.links == ()
        assert "no linking fact" in node.may_conclude
    assert not any(n.status is AttributionStatus.ATTRIBUTED for n in result.nodes)


def test_a_linking_fact_in_a_different_sentence_does_not_attribute():
    # A1 and A2 together: the fact and the strategy share a factor and a
    # call, and are different sentences. Attribution requires the
    # passage, not the topic.
    result = attribute(
        call((CEO, "Pat Lee", "We are expanding generation capacity across the fleet."),
             (CFO, "Sam Ray", "We invested $300 million in 860 megawatts of new capacity."),
             quarter="2025Q3"),
    )
    assert not any(n.status is AttributionStatus.ATTRIBUTED for n in result.nodes)


def test_a_node_gets_no_candidate_from_an_unrelated_factor():
    result = attribute(
        call((CEO, "Pat Lee", "We are building additional data center capacity."),
             (CFO, "Sam Ray", "Separately, we added 860 megawatts of generation capacity."),
             quarter="2025Q3"),
    )
    node = node_for(result, "data center")
    assert node.status is AttributionStatus.NO_ATTRIBUTION_EVIDENCE


def test_a_link_that_resolves_no_further_than_the_company_has_narrowed_nothing():
    # A5. An amount and a purpose with no named target leaves the
    # observation exactly where it already was.
    result = attribute(
        call((CEO, "Pat Lee",
              "We are expanding generation capacity, investing $300 million to do so."),
             quarter="2025Q3"),
    )
    placed = [n for n in result.nodes if n.links]
    assert placed, [n.status.value for n in result.nodes]
    for node in placed:
        assert node.status is AttributionStatus.AMBIGUOUS
        assert node.resolutions == (AttributionResolution.COMPANY,)


def test_a_category_word_is_not_a_place():
    # A13, and the Sprint 7 lesson restated: "in the market" names no
    # place, so it cannot carry a geography resolution.
    for text in ("We invested $300 million in the market to expand capacity.",
                 "We invested $300 million in the region to expand capacity."):
        facts = extract_linking_facts(call((CEO, "Pat Lee", text), quarter="2025Q3")[0])
        assert all(f.resolution is not AttributionResolution.GEOGRAPHY for f in facts), text


def test_an_attributed_amount_defaults_to_leaving_the_residual_alone():
    # A7. The default matters as much as the call site: a future caller
    # that omits the flag must still not allocate what it was not told.
    from atlas.analysis_engine.strategy_attribution import AttributedAmount

    assert AttributedAmount(value_text="$4 billion").residual_is_unallocated is True


def test_only_a_transcript_can_carry_a_linking_fact():
    # A11. Asserted at the guard, because a filed statement in this
    # corpus has no content for the extractor to reach anyway -- so the
    # behavioural test would pass with the guard removed.
    from atlas.analysis_engine.strategy_attribution import analysis

    statement = financials({"capital_expenditure": 91.45e9}, period_end=date(2025, 12, 31))
    assert statement.document_type.value != "transcript"
    assert analysis.extract_linking_facts(statement) == ()
    source = (analysis.__file__)
    with open(source, encoding="utf-8") as handle:
        body = handle.read()
    assert "is not SourceKind.TRANSCRIPT" in body


def test_no_attribution_evidence_is_not_a_claim_that_nothing_happened():
    result = attribute(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"))
    node = node_for(result, "data center")
    assert node.status is AttributionStatus.NO_ATTRIBUTION_EVIDENCE
    assert any("which is different" in claim for claim in node.may_not_conclude)
    assert "no evidence allocating" in node.may_conclude


# ---------------------------------------------------------------- 15,16
def test_two_named_targets_for_one_strategy_are_reported_as_conflicting():
    from atlas.analysis_engine.strategy_attribution.analysis import _status

    def link(name):
        return LinkingFact(
            basis=AttributionBasis.MANAGEMENT_NAMED_LINK,
            resolution=AttributionResolution.PROJECT, target_name=name,
            evidence=EvidenceRef(role=EvidenceRole.LINKING, source_record_id="r",
                                 source_kind="transcript", period="2025Q3",
                                 published_at=None, semantic_owner="x"),
            tense=ActionTense.OBSERVED_PAST,
        )

    assert _status([link("Comanche Peak"), link("Martin Lake")], []) is AttributionStatus.CONFLICTING


def test_one_passage_repeated_is_one_linking_fact():
    once = attribute(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q3"), company="AMAT")
    twice = attribute(
        tuple(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q3"))
        + tuple(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q4")),
        company="AMAT",
    )
    assert (len(next(n for n in once.nodes if n.links).links)
            == len(next(n for n in twice.nodes if n.links).links))


# ------------------------------------------------------------- 19,20,34
def test_an_analyst_cannot_supply_a_linking_fact():
    records = call((ANALYST, "Chris Vale",
                    "You plan to invest more than $200 million in Arizona, correct?"),
                   quarter="2025Q3")
    assert extract_linking_facts(records[0]) == ()


def test_a_filed_statement_supplies_no_linking_fact():
    # Filings are stored in this corpus as accession references without
    # content, and a consolidated figure names no purpose in any case.
    statement = financials({"capital_expenditure": 91.45e9}, period_end=date(2025, 12, 31))
    assert extract_linking_facts(statement) == ()


def test_no_causal_or_success_or_materiality_claim_exists_anywhere():
    from atlas.analysis_engine.strategy_attribution import contracts, models

    forbidden = ("caused", "causal", "success", "material", "score", "confidence",
                 "strength", "rank", "weight", "proof")
    for enum_name in ("AttributionResolution", "AttributionBasis", "AttributionStatus",
                      "EvidenceRole", "ActionTense"):
        for member in getattr(contracts, enum_name):
            assert not any(w in member.value.lower() for w in forbidden), f"{enum_name}.{member.name}"
    for name in models.__all__:
        for attribute_name in dir(getattr(models, name)):
            if attribute_name.startswith("_") or attribute_name == "may_not_conclude":
                continue
            assert not any(w in attribute_name.lower() for w in forbidden), f"{name}.{attribute_name}"


def test_every_result_disclaims_causation_materiality_and_success():
    result = attribute(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q3"), company="AMAT")
    node = next(n for n in result.nodes if n.links)
    disclaimed = " ".join(node.may_not_conclude)
    assert "caused" in disclaimed and "material" in disclaimed and "succeeding" in disclaimed


# ------------------------------------------------------------- 38,39,41
def test_every_link_carries_its_passage_and_provenance():
    result = attribute(call((CEO, "Pat Lee", ARIZONA), quarter="2025Q3"), company="AMAT")
    link = next(n for n in result.nodes if n.links).links[0]
    assert link.evidence.source_record_id
    assert link.evidence.text
    assert link.evidence.period == "2025Q3"
    assert link.evidence.role is EvidenceRole.LINKING
    assert link.evidence.speaker_title == CEO
    assert link.evidence.is_management_authored


def test_attribution_is_deterministic_idempotent_and_order_independent():
    records = call((CEO, "Pat Lee", ARIZONA), (CFO, "Sam Ray", BUILD), quarter="2025Q3")

    def shape(rec, at=AT):
        strategy = compose_company_strategy(rec, composed_at=AT)
        result = company_attribution(strategy, rec, evaluated_at=at)
        return sorted((n.node_id, n.status.value, len(n.links)) for n in result.nodes)

    assert shape(records) == shape(records)
    assert shape(records) == shape(tuple(reversed(records)))
    assert shape(records) == shape(records, AT + timedelta(days=400))
    assert shape(records) == shape(tuple(records) * 2)

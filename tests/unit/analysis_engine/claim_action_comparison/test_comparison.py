"""Claim-Action Comparison v1 -- the frozen Sprint 25 pair benchmark.

Every claim passage and every action sentence below is verbatim from the held
corpus. The negatives carry most of the weight: a false "this action supports
this claim" is worse than missing a true pair, so each control names the
overlap that makes it tempting and the dimension that must refuse it.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.action_evidence import SourceParagraph, extract_actions
from atlas.analysis_engine.claim_action_comparison import (
    Compatibility, EntityBasis, Relation, TemporalRelation, compare, compare_many,
    render_comparison,
)
from atlas.analysis_engine.strategy_claim import ClaimProvenance, read_claim

# ---------------------------------------------------------------- claims
PPAS = ("This is just the beginning, as we aim to secure customer PPAs for both new generation and "
        "our existing assets, continuing on this growth path.")
WEST_TEXAS = ("In addition to our planned solar and energy storage investments, we will be allocating "
              "capital to our new gas-fired units in West Texas, which we estimate will require "
              "approximately $900 million before any offsets from project financing.")
PJM = ("The PJM nuclear uprates will require growth capital over an 8-year period, with the majority "
       "of the spend occurring after 2028.")
COMANCHE = ("However, our immediate priority is to ensure that everything necessary for the data "
            "center at Comanche Peak is completed on schedule.")
CHIPS = "In fiscal Q1, we repurchased $300 million of shares as permitted by the terms of the CHIPS agreement."
SINGAPORE = ("In NAND, the combination of a higher demand outlook and our decision to colocate R&D "
             "cleanroom in our manufacturing fab underpins our decision to break ground for a new "
             "NAND fab at our Singapore site.")
NEW_YORK = ("We plan to break ground on our first New York fab in early calendar 2026, which we "
            "expect will provide supply in 2030 and beyond.")
SHOP_CHANNELS = ("And with new channels added in Q1, including ChatGPT, Pinterest and Microsoft "
                 "monetize, we're bringing more services and more reach and more buyers into the ecosystem.")

# ---------------------------------------------------------------- actions
META_PPA = ("In January 2026, we announced that we had entered into 20-year PPAs with Meta Platforms, "
            "Inc. (Meta) to supply 2,609 MW of carbon-free power and capacity from our PJM nuclear "
            "power plants, including 2,176 MW of operating energy and capacity and 433 of uprate "
            "energy and capacity to be constructed.")
AWS_PPA = ("In September 2025, we announced that we had entered into a 20-year power purchase "
           "agreement (PPA) (with options to extend for up to an additional 20 years) with Amazon "
           "Web Services (AWS) to supply 1,200 MW of carbon-free power from our Comanche Peak "
           "Nuclear Power Plant.")
WEST_TEXAS_ACTION = ("Executed disciplined capital allocation through targeted natural gas expansion, "
                     "including the development of an 860 MW facility in West Texas and the "
                     "acquisition of 2,600 MW of natural gas generation capacity from Lotus.")
ENERGY_HARBOR = ("Acquisition of Nuclear Generation Facilities — In 2024, we acquired 4,048 MW of "
                 "nuclear generation facilities in PJM from Energy Harbor.")
EH_COMPLETED = "In March 2024, we completed the acquisition of Energy Harbor."
BALDWIN = "We have completed closure activities at those ponds at our Baldwin facility."
COGENTRIX = ("In December 2025, we executed definitive agreements to acquire Cogentrix Energy, "
             "consisting of 10 natural gas generation facilities totaling approximately 5,500 MW of capacity.")
LOTUS = ("On October 22, 2025, pursuant to a purchase and sale agreement dated May 15, 2025, Vistra "
         "Operations acquired 100% of the membership interests of certain subsidiaries of Lotus "
         "(Lotus Acquisition).")
CHIPS_FUNDING = ("For example, in December 2024, we entered into direct funding agreements, providing "
                 "funds for the construction of fab facilities in Idaho and New York, with the United "
                 "States Department of Commerce (the “Department”) under the Department’s CHIPS "
                 "Incentives Program established pursuant to the CHIPS Act.")
MU_SWAPS = ("In 2021, we entered into fixed-to-floating interest rate swaps on the 2027 Notes with an "
            "aggregate notional amount of $900 million.")
SG_PPA = ("In 2023, we entered into an 18-year power purchase agreement in Singapore to purchase up "
          "to 450 megawatts of power at predominantly variable prices.")
WAYMO = ("In Other Bets, our fully autonomous driving technology company, Waymo, is now providing "
         "fully autonomous, paid ride-hailing services to customers in multiple cities.")
DELIVERR = ("The Company acquired 100% of the outstanding shares of Deliverr in exchange for cash "
            "consideration of $1,962 million and $10 million in Shopify Class A subordinate voting shares.")


def claim(passage, issuer="VST", period="2025Q4"):
    c = read_claim(passage, ClaimProvenance(issuer=issuer, node_id="n", node_kind="dependency",
                                            source_record_id="r", source_period=period,
                                            speaker_title="CEO"))
    assert c is not None, passage[:40]
    return c


def action(sentence, issuer="VST"):
    acts = extract_actions([SourceParagraph(issuer=issuer, accession="acc", section="S",
                                            ordinal=0, text=sentence)])
    assert acts, f"no action read from {sentence[:50]}"
    return acts[0]


def rel(claim_passage, action_sentence, issuer="VST", period="2025Q4", surfaces=()):
    return compare(claim(claim_passage, issuer, period), action(action_sentence, issuer), surfaces)


# ================================================================ positives
def test_a_customer_ppa_entered_after_the_claim_is_execution_evidence():
    r = rel(PPAS, META_PPA, surfaces=("PPAs",))
    assert r.relation is Relation.RELEVANT_EXECUTION
    assert r.entity_basis is EntityBasis.ASSERTED_ROLE
    assert r.event is Compatibility.MATCH
    assert r.temporal_relation is TemporalRelation.ACTION_AFTER_CLAIM
    assert r.refusal_reasons == ()


def test_west_texas_is_the_pair_the_old_subject_text_gate_missed():
    r = rel(WEST_TEXAS, WEST_TEXAS_ACTION, period="2025Q3", surfaces=("West Texas",))
    assert r.relation is Relation.RELEVANT_EXECUTION
    # the action's object stops before the adjunct, so the place survives only
    # in the sentence -- a weaker basis, and the record says so
    assert r.entity_basis is EntityBasis.SOURCE_SPAN and "West Texas" in r.entity_surfaces
    assert r.temporal_relation is TemporalRelation.UNKNOWN


def test_a_capital_claim_survives_a_mismatched_measure():
    # the claim is stated in dollars, the action reports megawatts; gating on
    # the measure would throw away the corpus's one true capital pair
    r = rel(WEST_TEXAS, WEST_TEXAS_ACTION, period="2025Q3", surfaces=("West Texas",))
    assert r.measure is Compatibility.MISMATCH and r.relation is Relation.RELEVANT_EXECUTION


def test_the_chips_funding_bears_on_the_dependency_and_never_on_the_repurchase():
    r = rel(CHIPS, CHIPS_FUNDING, issuer="MU", period="2026Q1", surfaces=("CHIPS",))
    assert r.relation is Relation.RELEVANT_DEPENDENCY
    assert r.event is Compatibility.MISMATCH and r.dependency is Compatibility.MATCH
    assert "dependency" in render_comparison(r).lower()
    assert r.relation is not Relation.RELEVANT_EXECUTION


def test_a_dependency_may_predate_the_claim_it_conditions():
    r = rel(CHIPS, CHIPS_FUNDING, issuer="MU", period="2026Q1", surfaces=("CHIPS",))
    assert r.temporal_relation is TemporalRelation.ACTION_BEFORE_CLAIM
    assert r.relation is Relation.RELEVANT_DEPENDENCY


# ================================================================ temporal
def test_a_deal_already_done_is_background_not_evidence_of_a_forward_aim():
    r = rel(PPAS, AWS_PPA, surfaces=("PPAs",))
    assert r.event is Compatibility.MATCH          # it really is a PPA entered
    assert r.temporal_relation is TemporalRelation.ACTION_BEFORE_CLAIM
    assert r.relation is Relation.NOT_RELEVANT
    assert "temporal_action_before_claim" in r.refusal_reasons


# ================================================================ same entity, wrong event
def test_comanche_peak_in_both_does_not_make_a_contract_into_a_completion():
    r = rel(COMANCHE, AWS_PPA, surfaces=("Comanche Peak", "Amazon"))
    assert r.entity is Compatibility.MATCH
    assert r.relation is Relation.NOT_RELEVANT and "event_mismatch" in r.refusal_reasons


def test_pjm_in_the_actions_own_object_does_not_make_an_acquisition_into_uprate_capital():
    r = rel(PJM, ENERGY_HARBOR, surfaces=("PJM",))
    assert r.entity_basis is EntityBasis.ASSERTED_ROLE
    assert r.relation is Relation.NOT_RELEVANT and "event_mismatch" in r.refusal_reasons


def test_the_meta_ppa_mentions_pjm_uprates_and_still_is_not_capital_deployment():
    # the sharpest false-support risk in the corpus: the action names PJM and
    # uprate capacity, and the claim is about PJM uprate capital
    r = rel(PJM, META_PPA, surfaces=("PJM",))
    assert r.relation is Relation.NOT_RELEVANT and "event_mismatch" in r.refusal_reasons


def test_a_shared_place_is_not_a_shared_act():
    r = rel(SINGAPORE, SG_PPA, issuer="MU", period="2026Q2", surfaces=("Singapore",))
    assert r.entity is Compatibility.MATCH
    assert r.relation is Relation.NOT_RELEVANT and "event_mismatch" in r.refusal_reasons


# ================================================================ same event, wrong entity
@pytest.mark.parametrize("sentence", [EH_COMPLETED, BALDWIN])
def test_a_completion_of_something_else_cannot_evidence_this_completion_claim(sentence):
    r = rel(COMANCHE, sentence, surfaces=("Comanche Peak",))
    assert r.relation is Relation.NOT_RELEVANT
    assert "entity_issuer_only" in r.refusal_reasons


# ================================================================ same measure / adjacency
def test_a_matching_currency_amount_is_not_a_share_repurchase():
    r = rel(CHIPS, MU_SWAPS, issuer="MU", period="2026Q1", surfaces=("CHIPS",))
    assert r.relation is Relation.NOT_RELEVANT


def test_an_acquisition_named_in_the_same_sentence_as_the_claims_object_is_still_not_the_claim():
    # Lotus sits beside West Texas inside the true action's sentence; read on
    # its own it shares nothing with the claim but the issuer
    r = rel(WEST_TEXAS, LOTUS, period="2025Q3", surfaces=("West Texas",))
    assert r.relation is Relation.NOT_RELEVANT and "entity_issuer_only" in r.refusal_reasons


def test_another_executed_action_in_the_same_quarter_is_not_the_claimed_allocation():
    r = rel(WEST_TEXAS, COGENTRIX, period="2025Q3", surfaces=("West Texas",))
    assert r.relation is Relation.NOT_RELEVANT


# ================================================================ not comparable
def test_a_continuing_state_cannot_be_compared_with_a_claim_about_acting():
    r = rel("We are investing in TPU capacity to meet the tremendous demand we are seeing from "
            "customers and partners.", WAYMO, issuer="GOOGL", period="2025Q3",
            surfaces=("Other Bets",))
    assert r.relation is Relation.NOT_COMPARABLE
    assert "no_shared_event_vocabulary" in r.refusal_reasons


def test_a_claim_naming_nothing_observable_is_refused_before_any_entity_is_matched():
    # "Shopify" appears in the action only as part of a share-class name
    r = rel(SHOP_CHANNELS, DELIVERR, issuer="SHOP", period="2026Q1", surfaces=("Shopify",))
    assert r.relation is Relation.NOT_COMPARABLE
    assert r.refusal_reasons == ("insufficient_claim_semantics",)


# ================================================================ firewall behaviour
def test_same_issuer_alone_never_licenses_relevance():
    r = rel(PPAS, BALDWIN, surfaces=("PPAs",))
    assert r.relation is Relation.NOT_RELEVANT and r.entity_basis is EntityBasis.ISSUER_ONLY


def test_direction_is_never_asserted_because_no_action_states_one():
    r = rel(PPAS, META_PPA, surfaces=("PPAs",))
    assert r.direction is Compatibility.NOT_APPLICABLE


def test_neither_input_is_modified():
    c, a = claim(PPAS), action(META_PPA)
    before = (c, a)
    compare(c, a, ("PPAs",))
    assert (c, a) == before and c.source_passage == PPAS and a.sentence == META_PPA


def test_comparison_is_deterministic_and_idempotent():
    c, a = claim(WEST_TEXAS, period="2025Q3"), action(WEST_TEXAS_ACTION)
    assert compare(c, a, ("West Texas",)) == compare(c, a, ("West Texas",))


def test_pair_order_does_not_change_any_pairs_verdict():
    cs = [(claim(PPAS), ("PPAs",)), (claim(PJM), ("PJM",))]
    acts = [action(META_PPA), action(ENERGY_HARBOR)]
    a = {(r.claim.passage, r.action.sentence): r.relation for r in compare_many(cs, acts)}
    b = {(r.claim.passage, r.action.sentence): r.relation
         for r in compare_many(list(reversed(cs)), list(reversed(acts)))}
    assert a == b


def test_pairs_are_only_generated_within_an_issuer():
    cs = [(claim(PPAS), ("PPAs",))]
    assert compare_many(cs, [action(CHIPS_FUNDING, issuer="MU")]) == ()


def test_the_renderer_states_no_verdict_on_the_claim():
    out = render_comparison(rel(PPAS, META_PPA, surfaces=("PPAs",))).lower()
    for word in ("confirmed", "validated", "successful", "on track", "caused", "because of",
                 "proves", "material"):
        assert word not in out


# ================================================================ dimensions must stay honest
CHIPS_FUNDING_WITH_AMOUNT = (
    "On December 9, 2024, we entered into direct funding agreements with the U.S. Department of "
    "Commerce for up to $6.1 billion in direct funding pursuant to the CHIPS Act for a planned fab "
    "in Idaho and two planned fabs in New York.")


def test_a_matching_measure_does_not_turn_a_dependency_into_execution():
    # both sides carry a currency amount and the entity matches, so the only
    # thing standing between this and a false support claim is the event
    r = rel(CHIPS, CHIPS_FUNDING_WITH_AMOUNT, issuer="MU", period="2026Q1", surfaces=("CHIPS",))
    assert r.measure is Compatibility.MATCH
    assert r.event is Compatibility.MISMATCH
    assert r.relation is Relation.RELEVANT_DEPENDENCY


def test_an_undated_action_records_unknown_time_rather_than_claiming_a_match():
    # West Texas is relevant *despite* unknown timing; saying "match" here
    # would tell a reader the timing had been checked when it never was
    r = rel(WEST_TEXAS, WEST_TEXAS_ACTION, period="2025Q3", surfaces=("West Texas",))
    assert r.temporal is Compatibility.UNKNOWN
    assert r.temporal_relation is TemporalRelation.UNKNOWN


def test_an_entity_seen_only_in_the_sentence_is_not_enough_without_the_event():
    # "Singapore" is in the action's object, the claim is to break ground
    r = rel(SINGAPORE, SG_PPA, issuer="MU", period="2026Q2", surfaces=("Singapore",))
    assert r.entity is Compatibility.MATCH and r.relation is Relation.NOT_RELEVANT


def test_absence_of_any_action_produces_no_relation_at_all():
    # The comparator only ever sees one claim and one action, so it has no
    # way to reason from absence: a claim with no matching action yields no
    # comparison, never a contradiction. There is no contradiction relation
    # in v1 -- the corpus holds no action that runs against a claim.
    assert compare_many([(claim(PPAS), ("PPAs",))], []) == ()
    assert not hasattr(Relation, "RELEVANT_CONTRADICTION")
    assert {r.value for r in Relation} == {
        "relevant_execution", "relevant_dependency", "not_relevant", "not_comparable"}


def test_an_actions_quantities_can_never_change_the_relation():
    """Sprint 26 found four new records that over-capture a neighbouring
    figure -- a dividend paid in the same sentence, an average price per
    share, a prior-year comparison. Those values are wrong and known to be
    wrong, so the thing that matters is that no relation can rest on them.
    Measure is recorded; it is never allowed to decide."""
    import dataclasses

    claim_action_pairs = [
        (claim(CHIPS, issuer="MU", period="2026Q1"), action(CHIPS_FUNDING_WITH_AMOUNT, issuer="MU"), ("CHIPS",)),
        (claim(PPAS), action(META_PPA), ("PPAs",)),
        (claim(WEST_TEXAS, period="2025Q3"), action(WEST_TEXAS_ACTION), ("West Texas",)),
        (claim(PJM), action(ENERGY_HARBOR), ("PJM",)),
        (claim(COMANCHE), action(AWS_PPA), ("Comanche Peak",)),
    ]
    for c, a, surfaces in claim_action_pairs:
        with_quantities = compare(c, a, surfaces)
        without = compare(c, dataclasses.replace(a, quantities=()), surfaces)
        assert with_quantities.relation is without.relation
        assert with_quantities.refusal_reasons == without.refusal_reasons
        # and a fabricated quantity cannot rescue or strengthen one either
        invented = compare(c, dataclasses.replace(a, quantities=a.quantities * 3), surfaces)
        assert invented.relation is with_quantities.relation


# ================================================================ self-directed acts
MU_REPURCHASE_CLAIM = ("In fiscal Q1, we repurchased $300 million of shares as permitted by the terms "
                       "of the CHIPS agreement.")
MU_REPURCHASE_ACTION = "We repurchased 3.2 million shares of our common stock for $300 million in 2024."
VST_ALLOCATION_CLAIM = ("We have allocated approximately $3 billion to our equity holders in 2026 and "
                        "2027 through share repurchases and common and preferred dividends.")
VST_REPURCHASE_ACTION = ("During the year ended December 31, 2024, we repurchased 16.6 million shares "
                         "for $1.2 billion under the program.")
CRM_REPURCHASE_ACTION = ("During the fiscal year ended January 31, 2025, we repurchased approximately "
                         "30 million shares of our common stock for approximately $7.8 billion.")


class TestACompanyActingOnItsOwnShares:
    """A buyback has no counterparty, no site and no partner: its object is
    the filer's own stock. The comparator normally insists on an external
    entity, so these pairs were refused even when claim and action named the
    identical act. The licence granted here is narrow -- same issuer on its
    own still proves nothing."""

    def test_a_reported_buyback_is_execution_evidence_for_a_reported_buyback_claim(self):
        r = rel(MU_REPURCHASE_CLAIM, MU_REPURCHASE_ACTION, issuer="MU", period="2026Q1",
                surfaces=("CHIPS",))
        assert r.relation is Relation.RELEVANT_EXECUTION
        assert r.entity_basis is EntityBasis.SELF_DIRECTED_ACT
        assert r.event is Compatibility.MATCH
        assert r.entity_surfaces == ()        # there is no third party to name

    def test_the_relation_never_rests_on_the_amounts_agreeing(self):
        import dataclasses
        from atlas.analysis_engine.action_evidence import Quantity, QuantityKind

        c, a = claim(MU_REPURCHASE_CLAIM, "MU", "2026Q1"), action(MU_REPURCHASE_ACTION, "MU")
        base = compare(c, a, ("CHIPS",))
        emptied = compare(c, dataclasses.replace(a, quantities=()), ("CHIPS",))
        unrelated = compare(c, dataclasses.replace(a, quantities=(
            Quantity(value_text="99", unit="$", kind=QuantityKind.MONETARY, qualifier=""),)), ("CHIPS",))
        assert base.relation is emptied.relation is unrelated.relation is Relation.RELEVANT_EXECUTION

    def test_a_forward_allocation_is_not_evidenced_by_a_buyback_already_done(self):
        # Vistra allocates capital to holders IN 2026 AND 2027; the action is a
        # 2024 repurchase. Same issuer, same act type, and still not evidence,
        # because the claim states an intention rather than reporting a deed.
        r = rel(VST_ALLOCATION_CLAIM, VST_REPURCHASE_ACTION, issuer="VST", period="2026Q2",
                surfaces=("share repurchases",))
        assert r.relation is Relation.NOT_RELEVANT
        assert r.entity_basis is not EntityBasis.SELF_DIRECTED_ACT

    def test_a_buyback_does_not_evidence_a_claim_about_investing_in_the_business(self):
        r = rel("We will invest in distribution to capture the opportunity and continue to innovate.",
                CRM_REPURCHASE_ACTION, issuer="CRM", period="2026Q1")
        assert r.relation is Relation.NOT_RELEVANT

    def test_the_same_act_at_a_different_company_is_never_self_directed(self):
        # built side by side on purpose: Micron's claim against Salesforce's
        # buyback. compare() is called directly, so nothing but the rule
        # itself stops two different issuers being matched.
        micron_claim = claim(MU_REPURCHASE_CLAIM, "MU", "2026Q1")
        salesforce_action = action(CRM_REPURCHASE_ACTION, "CRM")
        r = compare(micron_claim, salesforce_action, ("CHIPS",))
        assert r.relation is Relation.NOT_RELEVANT
        assert r.entity_basis is not EntityBasis.SELF_DIRECTED_ACT

    def test_the_right_entity_with_the_wrong_act_still_fails(self):
        # a reported buyback claim against the CHIPS funding agreement: the
        # self-directed licence needs the action to BE the claimed act
        r = rel(MU_REPURCHASE_CLAIM, CHIPS_FUNDING_WITH_AMOUNT, issuer="MU", period="2026Q1",
                surfaces=("CHIPS",))
        assert r.entity_basis is not EntityBasis.SELF_DIRECTED_ACT
        assert r.relation is Relation.RELEVANT_DEPENDENCY   # unchanged from Sprint 25

    def test_issuer_only_remains_insufficient_for_ordinary_claims(self):
        r = rel(PPAS, BALDWIN, surfaces=("PPAs",))
        assert r.entity_basis is EntityBasis.ISSUER_ONLY
        assert r.relation is Relation.NOT_RELEVANT

    def test_the_relation_vocabulary_did_not_grow(self):
        assert {r.value for r in Relation} == {
            "relevant_execution", "relevant_dependency", "not_relevant", "not_comparable"}


class TestTheSelfDirectedLicenceIsNarrow:
    """The held corpus has no claim that is both an observational report and
    about a non-self-directed event, so these two fixtures are built at the
    contract level -- clearly synthetic, and the only way to pin what the
    licence must refuse."""

    @staticmethod
    def _claim(status, events):
        import dataclasses
        from atlas.analysis_engine.strategy_claim import (
            ClaimType, Direction, Observability, StrategyClaim)

        base = claim(MU_REPURCHASE_CLAIM, "MU", "2026Q1")
        return dataclasses.replace(base, status=status, event_kinds=events,
                                   claim_type=ClaimType.DELIVERY, direction=Direction.COMPLETE,
                                   observability=Observability.QUALITATIVELY_OBSERVABLE)

    def test_only_a_self_directed_event_kind_earns_the_licence(self):
        # SYNTHETIC: an observational completion claim against a real
        # completion action. Everything else about it looks self-directed --
        # same issuer, filer actor, matching event -- but completing an
        # acquisition is something a company does to another company.
        from atlas.analysis_engine.strategy_claim import ClaimStatus, EventKind

        c = self._claim(ClaimStatus.OBSERVATIONAL_STATEMENT, (EventKind.COMPLETION,))
        a = action("In March 2024, we completed the acquisition of Energy Harbor.", issuer="MU")
        r = compare(c, a, ())
        assert r.entity_basis is not EntityBasis.SELF_DIRECTED_ACT
        assert r.relation is not Relation.RELEVANT_EXECUTION

    def test_an_action_whose_actor_is_not_established_earns_nothing(self):
        # SYNTHETIC: the Micron buyback with its filer actor withdrawn. Every
        # record in the corpus says "we" or "the Company", so this case can
        # only be built by hand -- and it must still refuse, because a
        # repurchase by somebody unnamed is not the company acting on itself.
        import dataclasses
        from atlas.analysis_engine.action_evidence import ActorKind

        a = action(MU_REPURCHASE_ACTION, issuer="MU")
        anonymous = dataclasses.replace(a, actor_is_filer=None, actor_kind=ActorKind.IMPLICIT,
                                        actor_text=None)
        r = compare(claim(MU_REPURCHASE_CLAIM, "MU", "2026Q1"), anonymous, ("CHIPS",))
        assert r.entity_basis is not EntityBasis.SELF_DIRECTED_ACT
        assert r.relation is not Relation.RELEVANT_EXECUTION

    def test_the_self_directed_set_holds_only_what_the_corpus_earned(self):
        import atlas.analysis_engine.claim_action_comparison.comparison as module
        from atlas.analysis_engine.strategy_claim import EventKind

        assert module._SELF_DIRECTED == frozenset({EventKind.SHARE_REPURCHASE})


class TestWhatAnEarlierActionMeansDependsOnTheClaim:
    """One temporal rule served two opposite cases. An aim states something
    not yet done, so a deal already closed cannot be its execution. A
    statement *reporting* a buyback is the reverse: the act it describes
    necessarily came first, and refusing the earlier action would refuse the
    only evidence such a claim can ever have."""

    def test_a_report_of_a_buyback_is_evidenced_by_the_earlier_buyback(self):
        r = rel(MU_REPURCHASE_CLAIM, MU_REPURCHASE_ACTION, issuer="MU", period="2026Q1",
                surfaces=("CHIPS",))
        assert r.relation is Relation.RELEVANT_EXECUTION
        assert r.temporal_relation is TemporalRelation.ACTION_BEFORE_CLAIM
        assert r.temporal is Compatibility.MATCH
        # the ordering is still reported honestly -- only its meaning changed
        assert "temporal_action_before_claim" not in r.refusal_reasons

    def test_an_aim_is_still_not_evidenced_by_a_deal_already_done(self):
        # THE load-bearing negative: the Vistra/AWS pair Sprint 25 earned
        r = rel(PPAS, AWS_PPA, surfaces=("PPAs",))
        assert r.event is Compatibility.MATCH
        assert r.temporal_relation is TemporalRelation.ACTION_BEFORE_CLAIM
        assert r.temporal is Compatibility.MISMATCH
        assert r.relation is Relation.NOT_RELEVANT
        assert "temporal_action_before_claim" in r.refusal_reasons

    def test_a_forward_allocation_is_still_not_evidenced_by_a_past_buyback(self):
        r = rel(VST_ALLOCATION_CLAIM, VST_REPURCHASE_ACTION, issuer="VST", period="2026Q2",
                surfaces=("share repurchases",))
        assert r.relation is Relation.NOT_RELEVANT

    def test_an_action_after_the_claim_is_unaffected(self):
        r = rel(PPAS, META_PPA, surfaces=("PPAs",))
        assert r.temporal_relation is TemporalRelation.ACTION_AFTER_CLAIM
        assert r.relation is Relation.RELEVANT_EXECUTION

    def test_unknown_time_is_still_unknown_and_not_assumed_compatible(self):
        r = rel(WEST_TEXAS, WEST_TEXAS_ACTION, period="2025Q3", surfaces=("West Texas",))
        assert r.temporal is Compatibility.UNKNOWN
        assert r.temporal_relation is TemporalRelation.UNKNOWN

    def test_being_earlier_never_proves_it_is_the_same_transaction(self):
        # same issuer, same act, same amount, compatible timing -- and still
        # only evidence that the kind of act happened, never that these two
        # sentences describe one buyback
        r = rel(MU_REPURCHASE_CLAIM, MU_REPURCHASE_ACTION, issuer="MU", period="2026Q1",
                surfaces=("CHIPS",))
        assert r.relation is Relation.RELEVANT_EXECUTION
        assert {x.value for x in Relation} == {
            "relevant_execution", "relevant_dependency", "not_relevant", "not_comparable"}


class TestTheComparatorReadsTheRecordNotTheProse:
    """A year-level period carries the words "December 31" because that is
    when the period closed. The record says month is unknown; the comparator
    used to recover December from the prose anyway."""

    def test_a_year_level_period_stays_year_level(self):
        import atlas.analysis_engine.claim_action_comparison.comparison as module

        a = action("During the year ended December 31, 2024, we repurchased 16.6 million shares "
                   "for $1.2 billion under the program.", issuer="VST")
        assert (a.date.year, a.date.month) == (2024, None)
        assert module._action_ym(a) == (2024, 0)      # never (2024, 12)

    def test_an_exact_event_date_keeps_its_month(self):
        import atlas.analysis_engine.claim_action_comparison.comparison as module

        a = action("On December 9, 2024, we entered into direct funding agreements with a department.",
                   issuer="MU")
        assert module._action_ym(a) == (2024, 12)

    def test_an_undated_action_reads_as_no_date_at_all(self):
        import atlas.analysis_engine.claim_action_comparison.comparison as module

        a = action("Through August 28, 2025, we had repurchased an aggregate of $7.19 billion "
                   "under the authorization.", issuer="MU")
        assert a.date is None and module._action_ym(a) is None

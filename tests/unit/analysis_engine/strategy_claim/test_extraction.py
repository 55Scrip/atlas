"""Strategy Claim v1 -- the frozen Sprint 24 benchmark.

Every passage is verbatim from the held strategy corpus (earnings-call
evidence already attached to a strategy node). The controls exist to stop the
two failures that matter: a number nearby becoming a claim's measure, and a
qualitative priority being forced into a quantitative one.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.strategy_claim import (
    ClaimProvenance, ClaimStatus, ClaimType, Direction, EventKind, MeasureKind, Observability,
    claims_for_node, read_claim,
)

PROV = ClaimProvenance(issuer="X", node_id="n1", node_kind="dependency", source_record_id="r1",
                       source_period="2025Q4", speaker_title="CEO")


def claim(passage, **kw):
    r = read_claim(passage, kw.pop("provenance", PROV), kw.pop("entities", ()))
    assert r is not None, "expected a claim"
    return r


def measures(r):
    return {m.value for m in r.measure_kinds}


def events(r):
    return {e.value for e in r.event_kinds}


# ------------------------------------------------------------------ the ten frozen claims
COMANCHE = ("However, our immediate priority is to ensure that everything necessary for the data center "
            "at Comanche Peak is completed on schedule.")
PPAS = ("This is just the beginning, as we aim to secure customer PPAs for both new generation and our "
        "existing assets, continuing on this growth path.")
PJM = ("The PJM nuclear uprates will require growth capital over an 8-year period, with the majority of "
       "the spend occurring after 2028.")
WEST_TEXAS = ("In addition to our planned solar and energy storage investments, we will be allocating "
              "capital to our new gas-fired units in West Texas, which we estimate will require "
              "approximately $900 million before any offsets from project financing.")
CHIPS = "In fiscal Q1, we repurchased $300 million of shares as permitted by the terms of the CHIPS agreement."
NEW_YORK = ("We plan to break ground on our first New York fab in early calendar 2026, which we expect "
            "will provide supply in 2030 and beyond.")
SINGAPORE = ("In NAND, the combination of a higher demand outlook and our decision to colocate R&D "
             "cleanroom in our manufacturing fab underpins our decision to break ground for a new NAND "
             "fab at our Singapore site.")
GOOGL = ("We're investing in AI compute capacity to support frontier model development by Google "
         "DeepMind, ongoing efforts to improve the user experience, and drive higher advertiser ROI in "
         "Google services, significant cloud customer demand, as well as strategic investments in Other Bets.")
SHOP_PRIORITY = ("We will always lean into growth because as we grow, we invest more in driving success "
                 "for our merchants and for Shopify.")
ARIZONA = ("As part of this endeavor, we plan to invest more than $200 million in Arizona to establish a "
           "state-of-the-art facility for manufacturing specialized components.")
AMAT_BUYBACK = ("We allocated $4.9 billion to our share repurchase program and reduced shares outstanding "
                "by more than 3%.")


def test_the_comanche_peak_claim_is_a_completion_not_a_capacity_claim():
    r = claim(COMANCHE)
    assert r.claim_type is ClaimType.DELIVERY and r.direction is Direction.COMPLETE
    assert events(r) == {"completion"} and measures(r) == set()
    assert r.observability is Observability.QUALITATIVELY_OBSERVABLE
    assert r.horizon.raw_text.lower() == "on schedule"
    assert r.magnitude is None


def test_securing_ppas_licenses_contract_evidence_and_no_measure():
    r = claim(PPAS)
    assert r.claim_type is ClaimType.CONTRACTING and r.status is ClaimStatus.FORWARD_INTENT
    assert events(r) == {"contract_entered"} and measures(r) == set()


def test_a_capital_requirement_keeps_its_horizon_and_states_no_magnitude():
    r = claim(PJM)
    assert measures(r) == {"capital_deployment"} and r.magnitude is None
    assert r.status is ClaimStatus.FORWARD_INTENT
    assert "8-year period" in r.horizon.raw_text


def test_west_texas_keeps_its_magnitude_qualifier_and_dependency():
    r = claim(WEST_TEXAS)
    assert measures(r) == {"capital_deployment"}
    assert (r.magnitude.value_text, r.magnitude.unit, r.magnitude.qualifier) == ("900 million", "$", "approximately")
    assert any("project financing" in d.raw_text for d in r.dependencies)


def test_the_chips_node_is_a_buyback_claim_with_the_agreement_as_a_constraint():
    # Sprint 23 called subject_text "repurchased" lossy. It is not: the claim
    # is a share repurchase and CHIPS is the constraint on it.
    r = claim(CHIPS)
    assert r.claim_type is ClaimType.CAPITAL_RETURN and events(r) == {"share_repurchase"}
    assert measures(r) == {"capital_returned"}
    assert (r.magnitude.value_text, r.magnitude.unit) == ("300 million", "$")
    assert any("CHIPS" in d.raw_text for d in r.dependencies)


def test_breaking_ground_is_observable_without_being_measurable():
    r = claim(NEW_YORK)
    assert r.claim_type is ClaimType.BUILD and events(r) == {"construction_started"}
    assert measures(r) == set() and r.magnitude is None
    assert r.observability is Observability.QUALITATIVELY_OBSERVABLE
    assert "early calendar 2026" in r.horizon.raw_text


def test_the_singapore_claim_is_fab_construction_not_power_supply():
    r = claim(SINGAPORE)
    assert events(r) == {"construction_started"} and measures(r) == set()
    assert any("higher demand outlook" in d.raw_text for d in r.dependencies)


def test_investing_in_capacity_licenses_both_capital_and_capacity():
    r = claim(GOOGL)
    assert measures(r) == {"capital_deployment", "capacity"} and r.magnitude is None


def test_a_quantitative_claim_keeps_its_stated_amount():
    r = claim(ARIZONA)
    assert (r.magnitude.value_text, r.magnitude.qualifier) == ("200 million", "more than")
    assert measures(r) == {"capital_deployment"}


def test_money_allocated_to_a_buyback_is_capital_returned_not_deployed():
    r = claim(AMAT_BUYBACK)
    assert r.claim_type is ClaimType.CAPITAL_RETURN and measures(r) == {"capital_returned"}
    assert r.magnitude.value_text == "4.9 billion"   # a decimal point is not a clause end


# ------------------------------------------------------------------ controls
def test_a_priority_to_invest_more_is_not_a_quantitative_claim():
    r = claim(SHOP_PRIORITY)
    assert measures(r) == set() and r.magnitude is None
    assert r.observability is not Observability.QUANTITATIVELY_OBSERVABLE
    assert r.direction is Direction.DEPLOY


@pytest.mark.parametrize("passage", [
    # a number and the word megawatt appear; no company claim is made
    "Depending on where people are with their cost of equipment and EPC and when they got some of that "
    "locked down, the 555, there's going to probably need to be a spread around that $555 a megawatt day "
    "for certain projects to work.",
    "It is early days in the adoption cycle, but we're confident in our strategy to monetize AI.",
    "The loss of access to DRAM has significantly affected us.",
    "Additional clean room space is necessary to address this increased demand, and lead times for clean "
    "room build-out are lengthening across geographies.",
])
def test_passages_that_state_no_management_predicate_yield_no_claim(passage):
    assert read_claim(passage, PROV) is None


def test_a_nearby_number_never_becomes_a_measure():
    # the hedge "need to be ... around that $555" must not attach as a magnitude
    assert read_claim("there's going to probably need to be a spread around that $555 a megawatt day "
                      "for certain projects to work.", PROV) is None


def test_an_amount_stated_before_the_verb_is_not_the_claims_magnitude():
    # "the more than $400 million we have invested" states a cumulative total,
    # not the amount of this claim. Reading any nearby number as the magnitude
    # is the failure this refuses; leaving it unread is the conservative loss.
    r = claim("This builds on the more than $400 million we have invested in our U.S.")
    assert r.magnitude is None


def test_no_falsifier_or_horizon_is_invented():
    r = claim(PPAS)
    assert r.horizon is None          # the passage states none
    assert r.dependencies == ()       # and marks no dependency


# ------------------------------------------------------------------ provenance and behaviour
def test_provenance_and_passage_are_preserved_verbatim():
    r = claim(COMANCHE)
    assert r.source_passage == COMANCHE
    assert (r.provenance.issuer, r.provenance.node_id, r.provenance.source_period) == ("X", "n1", "2025Q4")
    assert r.predicate == "completed" and r.predicate in COMANCHE


def test_entities_are_kept_as_source_surfaces_and_never_resolved():
    r = read_claim(COMANCHE, PROV, entities=("Comanche Peak", "Amazon"))
    assert r.entities == ("Comanche Peak", "Amazon")


def test_a_node_yields_one_claim_per_passage_that_states_one():
    passages = [(COMANCHE, "r1", "2025Q4", "EVP"),
                ("Additionally, the site has access to gas.", "r1", "2025Q4", "EVP")]
    out = claims_for_node("n1", "VST", "dependency", passages)
    assert len(out) == 1 and out[0].source_passage == COMANCHE


def test_extraction_is_deterministic_and_idempotent():
    a = read_claim(WEST_TEXAS, PROV)
    b = read_claim(WEST_TEXAS, PROV)
    assert a == b


def test_order_independence_across_a_nodes_passages():
    ps = [(PJM, "r1", "2025Q4", "CEO"), (WEST_TEXAS, "r2", "2025Q3", "CFO")]
    assert {c.source_passage for c in claims_for_node("n", "VST", "dependency", ps)} == \
           {c.source_passage for c in claims_for_node("n", "VST", "dependency", list(reversed(ps)))}


# ------------------------------------------------------------------ renderer
def test_the_renderer_states_what_evidence_would_bear_on_a_claim():
    from atlas.analysis_engine.strategy_claim import render_claim
    out = render_claim(claim(WEST_TEXAS))
    assert "currency committed or spent" in out
    assert "900 million" in out and "project financing" in out


def test_the_renderer_never_states_a_verdict():
    from atlas.analysis_engine.strategy_claim import render_claim
    out = render_claim(claim(PPAS)).lower()
    assert not any(w in out for w in ("supported", "contradicted", "confirmed", "true", "false", "verdict"))
    assert "a contract entered" in out


def test_a_claim_with_nothing_countable_states_no_measure_and_no_magnitude():
    from atlas.analysis_engine.strategy_claim import render_claim
    out = render_claim(claim(SHOP_PRIORITY))
    assert "Magnitude: not stated" in out and "Horizon: not stated" in out
    assert "currency" not in out          # no measure was licensed
    assert "capital reported as spent" in out   # but the act of spending would still show

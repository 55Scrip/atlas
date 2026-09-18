"""Named things in strategy evidence, held to four real corpora.

Every passage is copied verbatim from a VST, GOOGL, MA or AMAT earnings
call already in the corpus. The controls matter more than the
extractions: this sprint exists because Sprint 13 could not join a
strategy to a filing, and the way to make that join worthless is to
manufacture entities.
"""
import pytest

from atlas.analysis_engine.strategy.entities import (
    EntityKind,
    EntityRelationship,
    entity_mentions,
)

# -- VST -------------------------------------------------------------
COMANCHE = ("However, our immediate priority is to ensure that everything necessary for the "
            "data center at Comanche Peak is completed on schedule.")
WEST_TEXAS = ("In addition to our planned solar and energy storage investments, we will be "
              "allocating capital to our new gas-fired units in West Texas, which we estimate "
              "will require approximately $900 million before any tax credits.")
MEGAWATTS = ("I think this 4,500 megawatts was as much a reminder to ourselves as it was to the "
             "market that we are developing a fair amount of assets.")
UPRATES = ("The PJM nuclear uprates will require growth capital over an 8-year period, with the "
           "majority of the spend occurring after 2028.")
ENERGY_FUND = ("Both units remain part of the Texas Energy Fund due diligence process, and we "
               "plan to make a final decision on financing in the coming months.")
PERMIAN = ("Having an existing site there, our Permian gas site, which we are expanding by "
           "adding turbines, makes this opportunity even more compelling.")
# -- GOOGL -----------------------------------------------------------
NVIDIA = ("We are scaling the most advanced chips in our data centers, including GPUs from our "
          "partner, NVIDIA, as well as our own purposeful TPUs.")
ANTHROPIC = ("We are investing in TPU capacity to meet the tremendous demand we are seeing from "
             "customers and partners, and we are excited that Anthropic recently shared plans "
             "to access up to 1 million TPUs.")
INFRASTRUCTURE = ("We've been working hard to ensure we're running a productive and efficient "
                  "organization, and it's not just how we operate the business, but even in "
                  "areas such as our technical infrastructure where we are investing significant "
                  "CapEx in data centers and servers.")
SPEAKER = "Philipp will talk more about monetization and share how AI is helping people."
SPEAKER_MIDSENTENCE = "Perhaps Philip can comment on the monetization."
AI_POSSESSIVE = ("And as I've shared before, for AI Overviews, even at our current baseline of "
                 "ads below and within the AI's response, overall, we see the monetization at "
                 "approximately the same rate.")
EVENT = ("At Google Marketing Live, we showcased how Gemini improves query understanding, "
         "allowing us to find relevant ads for longer searches previously difficult to monetize.")
# -- MA --------------------------------------------------------------
DISTRIBUTION = ("In addition to directly engaging with customers, we're scaling our services "
                "through distribution partners, one to many, including FIS, WPP, and Comcast "
                "advertising, which will be added this quarter.")
CLIP = ("This quarter, we're expanding this partnership in Mexico with Clip, a leading fintech "
        "with a small and micro business network approaching 1 million merchants.")
BUYBACK = ("During the quarter, we repurchased $3.3 billion worth of stock, and an additional "
           "$1.2 billion through October 27, 2025.")
# -- AMAT ------------------------------------------------------------
ARIZONA = ("As part of this endeavor, we plan to invest more than $200 million in Arizona to "
           "establish a state-of-the-art facility for manufacturing specialized components for "
           "our equipment.")
CHINA = "The headwind that we have, we do still expect some digestion in China and in ICAPS."


def names(passage, node_id="n-1"):
    return {m.mention_text for m in entity_mentions(
        node_id=node_id, passages=[(passage, "rec:v1", "2025Q4", None)])}


def one(passage, name, node_id="n-1"):
    return next(m for m in entity_mentions(
        node_id=node_id, passages=[(passage, "rec:v1", "2025Q4", None)])
        if m.mention_text == name)


# ------------------------------------------------- the entity survives
def test_comanche_peak_survives_with_its_relationship():
    # The case Sprint 13 needed and could not get: extraction reduced
    # this sentence to the factor `data center` and the plant vanished.
    mention = one(COMANCHE, "Comanche Peak")
    assert mention.relationship is EntityRelationship.LOCATED_AT
    assert mention.entity_kind is EntityKind.UNKNOWN
    assert mention.source_passage == COMANCHE
    assert mention.source_period == "2025Q4"
    assert mention.is_management_authored


def test_arizona_survives_as_something_invested_in():
    mention = one(ARIZONA, "Arizona")
    assert mention.relationship is EntityRelationship.INVESTS_IN


def test_a_partner_is_named_as_a_partner_because_the_passage_says_so():
    mention = one(NVIDIA, "NVIDIA")
    assert mention.entity_kind is EntityKind.PARTNER
    assert mention.relationship is EntityRelationship.PARTNERS_WITH


def test_a_list_of_partners_yields_each_one_separately():
    # One passage, three counterparties, each its own row.
    assert {"FIS", "WPP", "Comcast"} <= names(DISTRIBUTION)
    for name in ("FIS", "WPP", "Comcast"):
        assert one(DISTRIBUTION, name).relationship is EntityRelationship.INCLUDES


# ------------------------------------------- quantity safety (Phase O)
def test_a_quantity_is_never_an_entity():
    assert names(MEGAWATTS) == set(), names(MEGAWATTS)


def test_money_and_dates_are_never_entities():
    found = names(BUYBACK)
    assert not any(ch.isdigit() for name in found for ch in name), found
    assert "October" not in found


def test_a_year_is_not_an_entity():
    assert not any(n.isdigit() for n in names(UPRATES))


# ------------------------------------------ geography safety (Phase P)
def test_west_texas_is_preserved_whole_and_never_as_texas():
    found = names(WEST_TEXAS)
    assert "West Texas" in found
    assert "Texas" not in found
    # and the mention asserts nothing about any reporting segment
    assert one(WEST_TEXAS, "West Texas").entity_kind is EntityKind.UNKNOWN


def test_west_texas_and_texas_do_not_share_a_continuity_key():
    west = one(WEST_TEXAS, "West Texas")
    texas = entity_mentions(node_id="n", passages=[
        ("Our Texas segment delivered strong results.", "r", "2025Q4", None)])
    assert west.continuity_key != next(m for m in texas if m.mention_text == "Texas").continuity_key


# --------------------------------------- program/fund safety (Phase Q)
def test_texas_energy_fund_stays_one_named_object():
    found = names(ENERGY_FUND)
    assert "Texas Energy Fund" in found
    assert "Texas" not in found and "Energy" not in found and "Fund" not in found


def test_pjm_is_preserved_and_is_not_turned_into_a_plant():
    # "The PJM nuclear uprates" names a market; "nuclear uprates" is the
    # node's own subject. Neither becomes a facility.
    found = names(UPRATES)
    assert "PJM" in found
    assert not any("Comanche" in n or "Plant" in n for n in found)
    assert one(UPRATES, "PJM").entity_kind is EntityKind.UNKNOWN


def test_permian_is_preserved():
    assert "Permian" in names(PERMIAN)


# ----------------------------------- proper-noun safety (Phase N/F)
def test_ai_is_never_an_entity():
    for passage in (NVIDIA, SPEAKER, INFRASTRUCTURE, AI_POSSESSIVE):
        assert "AI" not in names(passage)


def test_a_possessive_does_not_smuggle_an_excluded_word_back_in():
    # "the AI's response" -- the apostrophe makes "AI's" survive a plain
    # exclusion list, which is how an excluded word becomes an entity.
    found = names(AI_POSSESSIVE)
    assert "AI's" not in found and "AI" not in found
    # and a real name keeps its identity when possessive
    youtube = names("Looking at monetization across YouTube's business, momentum continues.")
    assert "YouTube" in youtube and "YouTube's" not in youtube


def test_technical_infrastructure_does_not_become_an_entity():
    # A common noun phrase, however strategically central.
    assert "Technical Infrastructure" not in names(INFRASTRUCTURE)
    assert "CapEx" not in names(INFRASTRUCTURE)


def test_a_person_being_introduced_is_not_an_entity():
    assert "Philipp" not in names(SPEAKER)
    # Mid-sentence, where the sentence-start rule cannot help: only the
    # speaking verb after the name says this is a person.
    assert "Philip" not in names(SPEAKER_MIDSENTENCE)


def test_a_sentence_opening_word_is_not_an_entity():
    for passage in (COMANCHE, PERMIAN, CHINA):
        for opener in ("However", "Having", "The", "We", "During", "As"):
            assert opener not in names(passage)


def test_an_event_venue_is_not_a_site_an_initiative_sits_on():
    # "At Google Marketing Live, we showcased ..." places the telling,
    # not the thing.
    mention = one(EVENT, "Google Marketing Live")
    assert mention.relationship is not EntityRelationship.LOCATED_AT


# ------------------------------------------- node ownership (Phase L/S)
def test_a_name_in_another_nodes_passage_does_not_attach_here():
    # Extraction sees only the passages handed to it, which are the
    # node's own evidence.
    assert entity_mentions(node_id="n", passages=[(BUYBACK, "r", "2025Q4", None)]) == () or \
        "Comanche Peak" not in names(BUYBACK)


def test_every_mention_carries_the_node_it_belongs_to():
    mentions = entity_mentions(node_id="node-42", passages=[(COMANCHE, "r", "2025Q4", None)])
    assert mentions and all(m.node_id == "node-42" for m in mentions)


def test_one_passage_supporting_two_nodes_yields_a_row_for_each():
    a = entity_mentions(node_id="a", passages=[(COMANCHE, "r", "2025Q4", None)])
    b = entity_mentions(node_id="b", passages=[(COMANCHE, "r", "2025Q4", None)])
    assert {m.node_id for m in a} == {"a"} and {m.node_id for m in b} == {"b"}
    assert {m.mention_text for m in a} == {m.mention_text for m in b}


# ------------------------------------ alias / continuity (Phase T/X)
def test_two_spellings_of_one_plant_are_not_merged():
    short = one(COMANCHE, "Comanche Peak")
    longer = entity_mentions(node_id="n", passages=[
        ("We completed work at Comanche Peak Nuclear Power Plant.", "r", "2025Q4", None)])
    long_key = next(m for m in longer if m.mention_text.startswith("Comanche Peak")).continuity_key
    assert short.continuity_key != long_key


def test_a_mention_never_becomes_a_filing_member_identity():
    mention = one(COMANCHE, "Comanche Peak")
    assert ":" not in mention.mention_text
    assert "Member" not in mention.mention_text


def test_google_cloud_and_cloud_do_not_collide():
    cloud = entity_mentions(node_id="n", passages=[
        ("We are growing Google Cloud across regions.", "r", "2025Q4", None)])
    key = next(m for m in cloud if m.mention_text == "Google Cloud").continuity_key
    assert key != "cloud"


def test_the_same_name_in_two_periods_is_two_observations():
    mentions = entity_mentions(node_id="n", passages=[
        (COMANCHE, "r1", "2025Q3", None), (COMANCHE, "r2", "2025Q4", None)])
    peaks = [m for m in mentions if m.mention_text == "Comanche Peak"]
    assert len(peaks) == 2
    assert {m.source_period for m in peaks} == {"2025Q3", "2025Q4"}
    assert len({m.continuity_key for m in peaks}) == 1


# ------------------------------------------ relationship discipline
def test_an_unmarked_mention_gets_no_relationship_rather_than_a_plausible_one():
    assert one(ANTHROPIC, "Anthropic").relationship is EntityRelationship.UNKNOWN_RELATIONSHIP


def test_relationships_are_not_guessed_from_kind():
    # Everything UNKNOWN-kind must not collapse onto one relationship.
    found = {one(p, n).relationship for p, n in
             ((COMANCHE, "Comanche Peak"), (ARIZONA, "Arizona"), (ANTHROPIC, "Anthropic"))}
    assert len(found) == 3


def test_no_mention_is_labelled_independent_evidence():
    assert all(m.is_management_authored for m in entity_mentions(
        node_id="n", passages=[(COMANCHE, "r", "2025Q4", None)]))


# ------------------------------------------------------- invariants
def _fingerprint(ms):
    return sorted((m.node_id, m.mention_text, m.entity_kind.value,
                   m.relationship.value, m.source_period) for m in ms)


def test_extraction_is_deterministic():
    ps = [(COMANCHE, "r", "2025Q4", None), (ARIZONA, "r2", "2025Q3", None)]
    assert _fingerprint(entity_mentions(node_id="n", passages=ps)) == \
           _fingerprint(entity_mentions(node_id="n", passages=ps))


def test_duplicate_evidence_does_not_duplicate_a_relation():
    ps = [(COMANCHE, "r", "2025Q4", None)]
    once = _fingerprint(entity_mentions(node_id="n", passages=ps))
    twice = _fingerprint(entity_mentions(node_id="n", passages=ps + ps))
    assert once == twice


def test_extraction_is_order_independent():
    ps = [(COMANCHE, "r", "2025Q4", None), (ARIZONA, "r2", "2025Q3", None)]
    assert _fingerprint(entity_mentions(node_id="n", passages=ps)) == \
           _fingerprint(entity_mentions(node_id="n", passages=list(reversed(ps))))


def test_extraction_reads_no_clock():
    import pathlib

    source = pathlib.Path("atlas/analysis_engine/strategy/entities.py").read_text(encoding="utf-8")
    assert "datetime" not in source and "now(" not in source


def test_no_company_or_ticker_appears_in_executable_code():
    import pathlib

    source = pathlib.Path("atlas/analysis_engine/strategy/entities.py").read_text(encoding="utf-8")
    parts = source.split('"""')
    code = parts[0] + "".join(parts[2::2])
    code = "\n".join(l for l in code.splitlines() if not l.lstrip().startswith("#"))
    for token in ("VST", "GOOGL", "AMAT", "Vistra", "Comanche", "NVIDIA", "Arizona", "Clip"):
        assert token not in code, f"{token} appears in executable code"


def test_the_module_imports_nothing_from_atlas():
    # Entity representation is a read over passages. It must not reach
    # for filings, dimensional evidence or any decision layer.
    import ast
    import pathlib

    source = pathlib.Path("atlas/analysis_engine/strategy/entities.py").read_text(encoding="utf-8")
    modules = {n.module for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ImportFrom)}
    assert not any((m or "").startswith("atlas") for m in modules)

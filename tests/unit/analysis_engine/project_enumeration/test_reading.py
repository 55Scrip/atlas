"""Project Enumeration v1 -- the frozen Sprint 34 falsification set.

Sprint 33 measured that a bulleted list settles nothing: of the 40 lists in the
held filings whose entries name a plant, 6 enumerate projects and 34 enumerate
risks, factors, forward-looking statements, spending categories, financing
activities and audit procedures. The question this suite holds the reader to is
whether an independently extracted observed action separates them -- and whether
each of the two conditions is doing real work, measured against the lists that
come closest to passing without them.

Every paragraph is verbatim from a held 10-K at 620a767.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.action_evidence import SourceParagraph as ActionParagraph
from atlas.analysis_engine.action_evidence import extract_actions
from atlas.analysis_engine.project_enumeration import SourceParagraph, read_enumerations

# --------------------------------------------------------------- true lists
MU_LEAD = ("Outside the U.S., we are investing in manufacturing technologies, facilities and "
           "equipment, and R&D, and advancing our global back-end assembly and test network. These "
           "investments support our product portfolio and extend our ability to meet global market "
           "demand in the future. Planned investments and those underway include the following:")
MU_ENTRIES = [
    "•India: our construction is progressing for the assembly and test facility in Gujarat to "
    "address demand in the latter half of this decade;",
    "•Japan: we are modernizing our Hiroshima manufacturing facility to support the production "
    "of DRAM using EUV lithography;",
    "•Singapore: we broke ground on an HBM advanced packaging facility to meaningfully expand "
    "our total advanced packaging capacity beginning in calendar 2027; and",
    "•Taiwan: we are modernizing our production capacity for DRAM and HBM products to meet "
    "rising market demand."]
VST_LEAD = ("We have already taken or announced significant steps to transform our generation "
            "portfolio with the goal of maintaining reliability while also reducing the emissions "
            "intensity of our generation fleet, including:")
VST_ENTRIES = [
    "•Acquisition of Nuclear Generation Facilities — In 2024, we acquired Energy Harbor, "
    "including 4,048 MW of nuclear generation facilities in PJM.",
    "•Acquisition of Natural Gas Generation Facilities — In 2025, we acquired 2,557 MW of "
    "natural gas generation facilities in Delaware and Pennsylvania (PJM), Rhode Island (ISO-NE), "
    "New York (NYISO), and California (CAISO).",
    "•Re-powered generation assets — We intend to repower the Coleto Creek Power Plant in "
    "Texas and the Miami Fort Power Plant in Illinois to natural-gas fueled plants upon their "
    "retirements as coal-fueled facilities in 2027 and 2028, respectively.",
    "•Solar Projects — As of December 31, 2025, we owned solar generations facilities "
    "totaling 538 MW in Texas and 112 MW in Illinois."]
# -------------------------------------------------------------- false lists
RISK_LEAD = ("Our financial performance could be materially and negatively affected by matters "
             "arising from our ownership and operation of nuclear facilities, including any "
             "prolonged unavailability of any of our nuclear generation facilities. The following "
             "are among the more significant related risks:")
RISK_ENTRIES = [
    "•Operational Risk. Operations at any generation facility could degrade to the point where "
    "the facility would have to be shut down.",
    "•Spent Nuclear Fuel Storage. Our nuclear operations produce various types of nuclear "
    "waste materials, including spent nuclear fuel stored at our facilities."]
FINANCING_LEAD = ("Our significant financing activities during the years ended December 31, 2025 "
                  "and 2024 are as follows:")
FINANCING_ENTRIES = [
    "•In 2025, we paid (i) $1.744 billion to redeem senior secured and unsecured notes, (ii) "
    "$1.028 billion to repurchase common stock, (iii) $803 million to repay debt assumed in the "
    "Lotus Acquisition.",
    "•In 2024, we paid (i) $2.247 billion to redeem senior secured notes, (ii) $1.748 billion "
    "to purchase the noncontrolling interests in Vistra Vision."]
CAPEX_LEAD = ("Estimated 2026 capital expenditures and nuclear fuel purchases as of December 31, "
              "2025 total approximately $2.587 billion and include:")
CAPEX_ENTRIES = ["•$1.087 billion for investments in generation and mining facilities "
                 "inclusive of LTSA prepayments;"]
# ------------------------------------- the runs that have no lead-in at all
NO_LEAD_HEADING = "Disciplined capital allocation."
NO_LEAD_ENTRIES = [
    "•Executed disciplined capital allocation through targeted natural gas expansion, "
    "including the development of an 860 MW facility in West Texas and the acquisition of 2,600 MW "
    "of natural gas generation capacity from Lotus.",
    "•In December 2025, we executed definitive agreements to acquire Cogentrix Energy, "
    "consisting of 10 natural gas generation facilities totaling approximately 5,500 MW of capacity."]
REPURCHASE_HEADING = "Highlights from Fiscal 2026"
REPURCHASE_ENTRIES = [
    "•Share Repurchase Program: For fiscal 2026, we repurchased approximately 50 million "
    "shares of our common stock for $9.3 billion."]


def read(texts, issuer="ZZ", accession="ZZ-1", section="BUSINESS", period="2025-10"):
    paras = [SourceParagraph(issuer=issuer, accession=accession, section=section, ordinal=i,
                             text=t, period=period) for i, t in enumerate(texts)]
    actions = list(extract_actions(
        [ActionParagraph(issuer=issuer, accession=accession, section=section, ordinal=i, text=t)
         for i, t in enumerate(texts)]))
    return read_enumerations(paras, actions), actions


class TestAListOfProjectsIsRead:
    def test_a_country_by_country_investment_list(self):
        (e,), actions = read([MU_LEAD] + MU_ENTRIES)
        assert e.lead_in == MU_LEAD
        assert len(e.entries) == 4
        assert e.grounded_positions == (3,), "only the Singapore entry reports an observed action"
        assert e.entries[2].surface.startswith("Singapore:")
        assert [x.names_a_plant for x in e.entries] == [True, True, True, False]

    def test_a_captioned_portfolio_list(self):
        (e,), _ = read([VST_LEAD] + VST_ENTRIES)
        assert e.grounded_positions == (1, 2), "both acquisitions are reported as done"
        assert len(e.entries) == 4

    def test_an_entry_without_an_action_is_still_an_entry(self):
        (e,), _ = read([MU_LEAD] + MU_ENTRIES)
        assert [x.position for x in e.entries] == [1, 2, 3, 4]
        assert e.entries[0].action_keys == () and e.entries[0].names_a_plant

    def test_provenance_is_kept_for_the_container_and_every_entry(self):
        (e,), _ = read([VST_LEAD] + VST_ENTRIES, issuer="ZZ", accession="ZZ-9",
                       section="BUSINESS", period="2026-02")
        assert e.container.accession == "ZZ-9" and e.container.paragraph_ordinal == 0
        assert [x.span.paragraph_ordinal for x in e.entries] == [1, 2, 3, 4]
        assert e.source_period == "2026-02"

    def test_surfaces_are_the_sources_own_words_without_the_bullet(self):
        (e,), _ = read([MU_LEAD] + MU_ENTRIES)
        for x, raw in zip(e.entries, MU_ENTRIES):
            assert x.surface == raw.lstrip("•").strip()


class TestAListOfSomethingElseIsNotRead:
    @pytest.mark.parametrize("lead,entries", [
        (RISK_LEAD, RISK_ENTRIES), (FINANCING_LEAD, FINANCING_ENTRIES),
        (CAPEX_LEAD, CAPEX_ENTRIES)])
    def test_lists_that_mention_plants_without_enumerating_them(self, lead, entries):
        records, _ = read([lead] + entries)
        assert records == ()

    def test_the_financing_list_is_the_control_that_matters(self):
        """It is a list, its entries are things the filer did, and it is about
        money. Nothing in it reports an observed action in the action
        vocabulary, and nothing in it names a plant as the thing being done."""
        records, actions = read([FINANCING_LEAD] + FINANCING_ENTRIES)
        assert records == ()


class TestBothConditionsDoWork:
    def test_without_a_lead_in_there_is_no_enumeration_to_belong_to(self):
        """Verbatim from a held filing: a heading with no colon, then bullets
        whose first entry names a facility and reports an execution."""
        records, actions = read([NO_LEAD_HEADING] + NO_LEAD_ENTRIES, section="MDA")
        assert actions, "the entries do carry observed actions"
        assert records == (), "but nothing says what they are entries of"

    def test_with_a_lead_in_the_same_bullets_would_be_read(self):
        records, _ = read([NO_LEAD_HEADING.rstrip(".") + ":"] + NO_LEAD_ENTRIES, section="MDA")
        assert len(records) == 1, "the lead-in is the only difference"

    def test_an_action_that_names_no_plant_does_not_ground_a_list(self):
        """Verbatim shape from a held filing: a highlights list whose entry
        reports a real repurchase. An action is not enough on its own."""
        records, actions = read([REPURCHASE_HEADING + ":"] + REPURCHASE_ENTRIES, section="MDA")
        assert actions, "the repurchase is a real observed action"
        assert records == (), "and shares are not a plant"


class TestNothingIsConcludedAboutProjects:
    def test_no_identity_is_offered(self):
        import atlas.analysis_engine.project_enumeration as pkg
        banned = ("same", "not_same", "identi", "equal", "match", "resolve", "alias", "canonical",
                  "distinct_project", "different")
        offered = [n for n in dir(pkg) if not n.startswith("_")]
        assert not [n for n in offered if any(w in n.lower() for w in banned)], offered

    def test_position_is_source_order_and_not_a_project_ordinal(self):
        (e,), _ = read([VST_LEAD] + VST_ENTRIES)
        assert [x.position for x in e.entries] == [1, 2, 3, 4]
        for x in e.entries:
            assert not hasattr(x, "ordinal")

    def test_one_entry_with_several_action_records_is_still_one_entry(self):
        (e,), _ = read([MU_LEAD] + MU_ENTRIES)
        assert len(e.entries) == len(MU_ENTRIES)
        assert sum(1 for x in e.entries if x.action_keys) == 1

    def test_a_forward_entry_is_not_grounded(self):
        (e,), _ = read([VST_LEAD] + VST_ENTRIES)
        repower = e.entries[2]
        assert repower.surface.startswith("Re-powered")
        assert repower.action_keys == (), "'We intend to repower' reports nothing done"


class TestTheSameAnswerEveryTime:
    def test_deterministic(self):
        assert read([MU_LEAD] + MU_ENTRIES)[0] == read([MU_LEAD] + MU_ENTRIES)[0]

    def test_idempotent(self):
        texts = [VST_LEAD] + VST_ENTRIES
        paras = [SourceParagraph("ZZ", "ZZ-1", "BUSINESS", i, t, "2025-10")
                 for i, t in enumerate(texts)]
        actions = list(extract_actions(
            [ActionParagraph(issuer="ZZ", accession="ZZ-1", section="BUSINESS", ordinal=i, text=t)
             for i, t in enumerate(texts)]))
        assert read_enumerations(paras, actions) == read_enumerations(paras, actions)

    def test_document_order_does_not_change_the_records(self):
        texts = [MU_LEAD] + MU_ENTRIES
        paras = [SourceParagraph("ZZ", "ZZ-1", "BUSINESS", i, t, "2025-10")
                 for i, t in enumerate(texts)]
        actions = list(extract_actions(
            [ActionParagraph(issuer="ZZ", accession="ZZ-1", section="BUSINESS", ordinal=i, text=t)
             for i, t in enumerate(texts)]))
        assert read_enumerations(paras, actions) == read_enumerations(list(reversed(paras)), actions)

    def test_a_list_cannot_span_two_documents(self):
        lead = [SourceParagraph("ZZ", "ZZ-2024", "BUSINESS", 0, VST_LEAD, "2025-02")]
        entries = [SourceParagraph("ZZ", "ZZ-2025", "BUSINESS", 1, t, "2026-02")
                   for t in VST_ENTRIES]
        actions = list(extract_actions(
            [ActionParagraph(issuer="ZZ", accession="ZZ-2025", section="BUSINESS", ordinal=1, text=t)
             for t in VST_ENTRIES]))
        assert read_enumerations(lead + entries, actions) == ()


class TestBoundariesTheCorpusOnlyAlmostReaches:
    def test_an_entry_whose_only_plant_word_is_a_line_of_credit(self):
        """SYNTHETIC. The held filings contain 14 bulleted entries whose only
        plant word is a credit facility, and none of them reports an observed
        action, so the corpus never puts the two together. The shape is ordinary
        English -- entering into a revolving credit facility is exactly the kind
        of thing a filer reports -- and the same guard is already needed by the
        two layers below this one."""
        records, actions = read([
            "Our significant financing arrangements include the following:",
            "•In 2023, we entered into a $2.0 billion revolving credit facility with a "
            "syndicate of banks."], section="MDA")
        assert actions, "entering into a credit facility is a real observed action"
        assert records == (), "and a line of credit is not a plant"

    def test_an_entry_reporting_two_actions_is_still_one_entry(self):
        """SYNTHETIC. No entry in the 433 the corpus offers carries two action
        records, because each of its bullets reports at most one thing. A bullet
        with two sentences does, and a list entry is a place in the list, not a
        count of what happened there."""
        (e,), actions = read([
            "We have already taken the following steps:",
            "•Generation: In 2024, we acquired 4,048 MW of nuclear generation facilities in "
            "PJM. In 2025, we acquired 2,557 MW of natural gas generation facilities."])
        assert len(actions) == 2
        assert len(e.entries) == 1, "one bullet is one entry"
        assert len(e.entries[0].action_keys) == 2, "and it names both actions"
        assert e.grounded_positions == (1,)

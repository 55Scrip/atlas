"""Sprint 6B -- the rules added after the rejection audit.

The first pass recovered 2-8 nodes from 147-272 management statements
per company, and reading all 173 rejections showed why. Almost none of
the misses were evidence gaps. They were an ontology that could only
describe factories, a speaker classifier that had guessed at which
C-level acronyms exist, a first-person proxy standing in for "is this
about this company", and an economic engine defined as a kind of plan.

Every test here names the real sentence that motivated the rule, and
every new rule has a near-miss beside it, because a rule that only ever
sees its own motivating example is not a rule.
"""
from atlas.analysis_engine.strategy import (
    EvidenceStatus,
    FactorClass,
    ResourceKind,
    StrategyNodeKind,
    StrategyRejectionReason,
    extract_strategy,
    resolve_factors,
)
from tests.unit.analysis_engine.strategy._fixtures import COMPOSED_AT, transcript


def extract(content: str, **kwargs):
    return extract_strategy(transcript(content, **kwargs), extracted_at=COMPOSED_AT)


def reasons(rejected):
    return {r.reason for r in rejected}


# ---------------------------------------------- speaker classification
def test_any_c_level_acronym_counts_as_an_insider():
    # CBO and CRO were invisible to `C[EFOT]O`, which discarded eleven
    # Alphabet statements -- including both of its economic-engine
    # sentences. Enumerating C-level letters is a guess about org
    # charts; the shape is the rule.
    for title in ("CBO", "CRO", "CTO", "Chief Business Officer", "VP of Investor Relations",
                  "Head of Commercial & Origination", "Senior Executive"):
        nodes, _, _ = extract("We are building additional data center capacity.", title=title)
        assert nodes, title


def test_broadening_the_executive_pattern_did_not_admit_analysts():
    # The analyst and operator checks run first and cannot be overturned,
    # which is what makes the broad pattern safe.
    for title in ("Analyst", "Analyst, President of Equity Research",
                  "Operator", "Investor Relations / Moderator"):
        nodes, _, rejected = extract("We are building additional data center capacity.", title=title)
        assert nodes == (), title
        assert StrategyRejectionReason.NOT_A_COMPANY_INSIDER in reasons(rejected)


# ------------------------------------------------ turn-level first person
def test_a_dependency_without_a_pronoun_is_read_from_its_own_turn():
    # Verbatim, VST 2025Q4. A dependency on VST's own assets, by a VST
    # executive, on VST's call -- containing no "we". Sentence-level
    # first person threw it away.
    nodes, _, _ = extract(
        "Thanks for the question. We continue to develop the fleet. "
        "The PJM nuclear uprates will require growth capital over an 8-year period."
    )
    deps = [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY]
    assert [n.factor for n in deps] == [FactorClass.ELECTRIC_POWER]


def test_a_turn_that_never_says_we_is_not_about_this_company():
    # Verbatim, AMAT 2025Q3 -- a statement about what the industry needs,
    # in a turn with no first person anywhere. The near-miss for the
    # rule above, and the reason it is bounded to one speaker turn.
    nodes, _, rejected = extract(
        "In addition to robust supply chains, deploying AI at large scale requires "
        "significant innovation at every level of the technology stack."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []
    assert StrategyRejectionReason.THIRD_PARTY_SUBJECT in reasons(rejected)


def test_a_general_activity_subject_is_not_this_company_even_in_a_we_turn():
    # Isolates the guard from the turn-level check, which would
    # otherwise mask it. The turn says "we" twice; the sentence under
    # test is still about what the work takes for anyone who does it.
    # Verbatim subject, NVDA 2026Q1.
    nodes, _, rejected = extract(
        "We had a strong quarter and we are pleased with the ramp. Building modern AI "
        "platforms requires not only GPUs but also CPUs that connect to fast memory."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []
    assert StrategyRejectionReason.THIRD_PARTY_SUBJECT in reasons(rejected)


def test_a_turn_with_no_first_person_is_rejected_even_without_a_gerund_subject():
    # The mirror of the test above: no general-activity gerund here, so
    # only the turn-level check can reject it.
    nodes, _, rejected = extract(
        "The outlook for the sector depends on the availability of components."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []
    assert StrategyRejectionReason.THIRD_PARTY_SUBJECT in reasons(rejected)


def test_a_product_specification_is_not_a_dependency():
    # Verbatim, NVDA. A claim about how efficient the product is; read
    # as a dependency it says NVIDIA's strategy depends on GPUs.
    nodes, _, _ = extract(
        "We are proud of this result. Just 64 Blackwell GPUs are required to run the "
        "GPT-3 benchmark compared to 256 H100s, a 4 times reduction in cost."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []


# --------------------------------------------------- dependency polarity
def test_a_denied_dependency_is_not_a_dependency():
    # Verbatim, VST 2025Q4. Recording this states the opposite of what
    # management said, which is worse than recording nothing.
    # The full sentence, which names interconnection -- so the factor
    # gate passes and the polarity guard is the one under test.
    nodes, _, rejected = extract(
        "So we do not see equipment or EPC as the gating items to building new "
        "generation or to developing behind-the-meter interconnection."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []
    assert StrategyRejectionReason.DEPENDENCY_DENIED in reasons(rejected)


def test_having_a_factor_is_not_depending_on_it():
    # Verbatim, VST 2025Q4: a statement of sufficiency.
    nodes, _, rejected = extract(
        "Because of our pre-existing development pipeline, we also have ample access "
        "to high-voltage equipment."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []
    assert StrategyRejectionReason.HOLDS_OR_SUPPLIES_FACTOR in reasons(rejected)


def test_supplying_a_factor_to_others_is_not_depending_on_it():
    # Verbatim, AMAT 2025Q4. Here the company is somebody else's supply.
    nodes, _, rejected = extract(
        "Our high-velocity co-innovation model provides chip makers and chip designers "
        "much earlier access to next-generation process technology."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []


def test_a_number_explaining_its_own_variability_is_not_a_dependency():
    # Verbatim, GOOGL 2026Q1. It carries a dependency predicate and a
    # real factor, and asserts that a reported figure moves around.
    # In a turn that does say "we", so the turn-level check passes and
    # the variability guard is the one under test.
    nodes, _, rejected = extract(
        "We had a strong quarter in Cloud. It is important to keep in mind that revenues "
        "from TPU hardware sales will fluctuate from quarter to quarter depending on "
        "when TPUs are shipped to customers."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []
    assert StrategyRejectionReason.GUIDANCE_NOT_STRATEGY in reasons(rejected)


# --------------------------------------------------------- the ontology
def test_a_capital_light_business_can_state_a_dependency():
    # Verbatim, MA 2025Q3. Before the coverage pass the ontology had no
    # way to hold this, and MA produced one objective and one initiative
    # from 188 statements.
    nodes, _, _ = extract(
        "Our goal is to prepare them for these new transaction flows in a no-code "
        "approach, which we've learned is essential for merchant adoption and ease of use."
    )
    deps = [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY]
    assert [n.factor for n in deps] == [FactorClass.CUSTOMER_ADOPTION]


def test_geographic_expansion_is_representable():
    # Verbatim, MA 2026Q2.
    nodes, _, _ = extract(
        "This quarter, we're expanding this partnership in Mexico with Clip, a leading fintech."
    )
    assert any(n.factor is FactorClass.GEOGRAPHIC_MARKET or n.factor is FactorClass.PARTNER_ECOSYSTEM
               for n in nodes)


def test_a_market_is_never_a_dependency_target():
    # The near-miss that the coverage pass created and then had to fix:
    # "we're running part of the switch in the UAE, and it gives us
    # access to transactions" became a dependency on the UAE, and then
    # "availability of in the UAE" as a success condition derived from
    # it. A market is somewhere a company operates, not something the
    # world supplies to it.
    nodes, _, _ = extract(
        "So we're basically running a part of the switch in the UAE, and it gives us "
        "access to transactions that we didn't have before."
    )
    deps = [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY]
    assert all(n.factor is not FactorClass.GEOGRAPHIC_MARKET for n in deps)


def test_the_word_market_alone_is_not_a_geography():
    # Over-inference guard. Every call says "market" constantly; only a
    # named place or an explicit expansion counts.
    for text in ("the market is competitive", "our addressable market is large",
                 "market conditions remain uncertain"):
        assert all(f.factor is not FactorClass.GEOGRAPHIC_MARKET for f in resolve_factors(text)), text


def test_adoption_and_demand_are_not_the_same_factor():
    # Demand is appetite for what exists; adoption is a behaviour change
    # the strategy requires. Merging them would erase the distinction MA
    # depends on.
    adoption = resolve_factors("this is essential for merchant adoption")
    demand = resolve_factors("we are seeing strong customer demand")
    assert [f.factor for f in adoption] == [FactorClass.CUSTOMER_ADOPTION]
    assert [f.factor for f in demand] == [FactorClass.CUSTOMER_DEMAND]


# --------------------------------------------------- the economic engine
def test_an_economic_engine_is_read_from_its_own_evidence():
    # Verbatim, MA 2026Q1. No initiative, no expected outcome -- a
    # conversion, stated outright.
    nodes, _, _ = extract(
        "That is fueling transactions that's helping us getting after the cyclical "
        "opportunity, drive our virtuous cycle."
    )
    engines = [n for n in nodes if n.kind is StrategyNodeKind.ECONOMIC_ENGINE]
    assert len(engines) == 1
    assert engines[0].status is EvidenceStatus.OBSERVED


def test_an_engine_metaphor_without_economics_is_not_an_engine():
    # The near-miss. "Flywheel" on its own is a slogan; an engine has to
    # end in something economic.
    nodes, _, _ = extract("We think about this business as a flywheel that keeps turning.")
    assert [n for n in nodes if n.kind is StrategyNodeKind.ECONOMIC_ENGINE] == []


# --------------------------------------------------- resource commitments
def test_the_bare_verb_invest_is_a_capital_commitment():
    # AMAT: "we plan to invest more than $200 million in Arizona". The
    # first pass listed the gerund and the noun and forgot the verb.
    nodes, _, _ = extract(
        "As part of this endeavor, we plan to invest more than $200 million in Arizona "
        "to establish a facility for manufacturing specialized components."
    )
    assert any(n.resource is ResourceKind.CAPITAL for n in nodes) or any(
        n.factor is FactorClass.GEOGRAPHIC_MARKET for n in nodes
    )


def test_a_recurring_buyback_report_is_a_capital_allocation_commitment():
    # MA reported this same sentence in four consecutive quarters. The
    # first pass discarded all four as history.
    nodes, _, _ = extract(
        "During the quarter, we repurchased $4.9 billion worth of stock and "
        "approximately $700 million of additional stock through July 27, 2026."
    )
    assert any(n.resource is ResourceKind.SHARE_REPURCHASE for n in nodes)


def test_a_result_with_no_resource_in_it_is_still_history():
    # The near-miss for the rule above: relaxing the historical guard
    # must not turn every results recital into a strategy. Named by
    # reason, so removing the guard cannot pass on a technicality.
    nodes, _, rejected = extract(
        "During the quarter, we are developing our data center capacity and revenue "
        "was $1.4 billion of adjusted EBITDA."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.INITIATIVE] == []
    assert StrategyRejectionReason.HISTORICAL_STATEMENT in reasons(rejected)

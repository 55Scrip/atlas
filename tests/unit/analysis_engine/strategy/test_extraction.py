"""Strategy & Dependency Intelligence v1 -- what Atlas will and will not
read out of a sentence.

Most of these tests are about refusal. That is the point: the corpus
offers a keyword-matching layer thirty-seven "dependency" sentences per
four companies, of which the most common is safe-harbour boilerplate, so
a layer that accepts easily is worse than no layer at all. Each refusal
below names the real sentence that motivated it.
"""
from atlas.analysis_engine.strategy import (
    EvidenceStatus,
    FactorClass,
    OutcomeKind,
    ResourceKind,
    StrategyNodeKind,
    StrategyRejectionReason,
    extract_strategy,
)
from tests.unit.analysis_engine.strategy._fixtures import (
    ANALYST,
    COMPOSED_AT,
    EXECUTIVE,
    OPERATOR,
    filing,
    transcript,
)


def extract(content: str, **kwargs):
    return extract_strategy(transcript(content, **kwargs), extracted_at=COMPOSED_AT)


def reasons(rejected):
    return {r.reason for r in rejected}


# --------------------------------------------------------------- 3,5,6
def test_objective_observed_from_an_explicit_goal():
    nodes, _, _ = extract(
        "Our goal is to expand manufacturing capacity across the fleet this decade."
    )
    objectives = [n for n in nodes if n.kind is StrategyNodeKind.OBJECTIVE]
    assert len(objectives) == 1
    assert objectives[0].status is EvidenceStatus.OBSERVED
    assert objectives[0].factor is FactorClass.PRODUCTION_CAPACITY


def test_initiative_observed_and_kept_apart_from_the_objective():
    nodes, _, _ = extract("We are building additional data center capacity in West Texas.")
    kinds = {n.kind for n in nodes}
    assert StrategyNodeKind.INITIATIVE in kinds
    assert StrategyNodeKind.OBJECTIVE not in kinds


# ----------------------------------------------------------------- 7,8
def test_resource_commitment_is_its_own_node():
    nodes, _, _ = extract("We have allocated approximately $3 billion of capital to growth projects.")
    commitments = [n for n in nodes if n.kind is StrategyNodeKind.RESOURCE_COMMITMENT]
    assert [n.resource for n in commitments] == [ResourceKind.CAPITAL]


def test_guidance_is_referenced_never_restated_as_strategy():
    # The real shape of a guidance sentence: a measure, a range, a year,
    # and no strategic object. `ForwardClaim` owns this; if the strategy
    # layer accepted it, Atlas would hold guidance in two places and
    # they would drift.
    nodes, _, rejected = extract(
        "We plan to deliver adjusted EBITDA of $6.8 billion to $7.6 billion in 2027."
    )
    assert nodes == ()
    assert StrategyRejectionReason.GUIDANCE_NOT_STRATEGY in reasons(rejected)


def test_an_expectation_is_not_an_objective():
    # Verbatim, VST 2026Q2. "we expect to" was an objective marker on the
    # first benchmark run and turned this guidance remark into a
    # strategic objective about power purchase agreements.
    nodes, _, _ = extract(
        "As a reminder, that range excludes any contribution from the pending acquisition of "
        "Cogentrix and the premium above market we expect to receive under the long-term power "
        "purchase agreements at our PJM nuclear sites with Meta."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.OBJECTIVE] == []


# ------------------------------------------------------------ 9,10,11,12
def test_expected_outcome_observed_only_when_management_links_it():
    nodes, edges, _ = extract(
        "We are expanding manufacturing capacity to lower unit costs across the network."
    )
    outcomes = [n for n in nodes if n.kind is StrategyNodeKind.EXPECTED_OUTCOME]
    assert [n.outcome for n in outcomes] == [OutcomeKind.COST_REDUCTION]
    assert [e.status for e in edges] == [EvidenceStatus.OBSERVED]


def test_dependency_observed_from_a_real_dependency_sentence():
    # Verbatim, AMAT 2026Q2 -- the clearest genuine dependency statement
    # in the whole four-company corpus.
    nodes, _, _ = extract(
        "Last quarter, we said the availability of clean room space was a key factor pacing "
        "the rate of our industry investment."
    )
    deps = [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY]
    assert [n.factor for n in deps] == [FactorClass.PRODUCTION_CAPACITY]
    assert deps[0].status is EvidenceStatus.OBSERVED


def test_dependency_wins_over_initiative_when_a_sentence_carries_both():
    nodes, _, _ = extract(
        "We are investing heavily, but our build depends on the availability of components."
    )
    assert {n.kind for n in nodes} == {StrategyNodeKind.DEPENDENCY}


# ------------------------------------------------------------------- 13
def test_a_dependency_keyword_without_a_factor_creates_nothing():
    # Verbatim, VST 2026Q2. An executive, a dependency verb, and no
    # object at all.
    nodes, _, rejected = extract("Depends on what you're measuring off of.")
    assert nodes == ()
    assert StrategyRejectionReason.NO_CANONICAL_FACTOR in reasons(rejected)


def test_the_corpus_topic_word_resolves_to_no_factor_at_all():
    # 266-446 occurrences per benchmark company. Pinned at the resolver
    # rather than at the extractor, because a factor that universal
    # would join every company to every other one through
    # `find_cross_company_adjacencies` regardless of what the extractor
    # did with it.
    from atlas.analysis_engine.strategy import resolve_factors

    for text in ("AI", "we are investing in AI", "the AI opportunity", "our AI products"):
        assert resolve_factors(text) == (), text


def test_a_sentence_whose_only_object_is_the_topic_word_produces_nothing():
    nodes, _, rejected = extract("We are investing in AI.")
    assert [n for n in nodes if n.factor is not None] == []


def test_shared_topic_words_do_not_create_a_dependency():
    # "AI" appears 266-446 times per benchmark company. If it were a
    # factor, every company would depend on every other one.
    nodes, _, _ = extract(
        "We are investing in AI and we are excited about the AI opportunity ahead of us."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.DEPENDENCY] == []


# ---------------------------------------------------------------- 14,15
def test_success_condition_needs_a_conditional_construction():
    nodes, _, _ = extract(
        "We are adding generation capacity, as long as we can secure the interconnection queue positions."
    )
    assert any(n.kind is StrategyNodeKind.SUCCESS_CONDITION for n in nodes)


def test_failure_mode_needs_a_named_threat_and_a_factor():
    nodes, _, _ = extract(
        "The risk is that regulatory approvals slip and our construction permits arrive late."
    )
    failures = [n for n in nodes if n.kind is StrategyNodeKind.FAILURE_MODE]
    assert [n.factor for n in failures] == [FactorClass.REGULATORY_APPROVAL]


# ------------------------------------------------------------------- 16
def test_boilerplate_risk_language_is_not_a_failure_mode():
    nodes, _, rejected = extract(
        "We require regulatory approvals, and delays could adversely affect our business, "
        "financial condition and results of operations."
    )
    assert [n for n in nodes if n.kind is StrategyNodeKind.FAILURE_MODE] == []
    assert StrategyRejectionReason.GENERIC_RISK_FACTOR in reasons(rejected)


def test_safe_harbour_recitation_is_never_a_dependency():
    # The single most frequent dependency-marker sentence in the corpus,
    # present in every call of every benchmark company.
    nodes, _, rejected = extract(
        "Before we begin, I'd like to remind you that today's call includes forward-looking "
        "statements which are subject to risks and uncertainties that could cause our actual "
        "results to differ."
    )
    assert nodes == ()
    assert StrategyRejectionReason.SAFE_HARBOUR_BOILERPLATE in reasons(rejected)


# ------------------------------------------------------------------- 17
def test_marketing_language_creates_no_strategy():
    # Verbatim, MA 2025Q4.
    nodes, _, rejected = extract("Our strategy is clear, and we're executing against it.")
    assert nodes == ()
    # Named exactly, not "one of these two". Both reasons end in the
    # same refusal, and only one of them says Atlas recognised the
    # sentence as a claim about having a strategy rather than a strategy.
    assert reasons(rejected) == {StrategyRejectionReason.MARKETING_LANGUAGE}


def test_enthusiasm_about_a_real_factor_still_needs_a_predicate():
    nodes, _, _ = extract("We are excited and well-positioned in data centers.")
    assert nodes == ()


# ------------------------------------------------------------------- 32
def test_speaker_must_be_a_company_insider():
    for title in (ANALYST, OPERATOR):
        nodes, _, rejected = extract(
            "Our goal is to expand manufacturing capacity.", title=title
        )
        assert nodes == ()
        assert StrategyRejectionReason.NOT_A_COMPANY_INSIDER in reasons(rejected)


def test_an_analyst_title_wins_over_an_executive_word_inside_it():
    # Sell-side titles routinely contain executive words -- "Analyst,
    # President of Equity Research". The analyst reading has to be
    # checked first, or the most confident speaker on the call becomes
    # a source of company strategy.
    nodes, _, rejected = extract(
        "Our goal is to expand manufacturing capacity.",
        title="Analyst, President of Equity Research",
    )
    assert nodes == ()
    assert StrategyRejectionReason.NOT_A_COMPANY_INSIDER in reasons(rejected)


def test_another_companys_plans_are_not_this_companys_strategy():
    nodes, _, rejected = extract(
        "Our customers require manufacturing capacity, and we are watching that closely."
    )
    assert nodes == ()
    assert StrategyRejectionReason.THIRD_PARTY_SUBJECT in reasons(rejected)


# ------------------------------------------------------------------- 35
def test_every_node_carries_a_locatable_verbatim_passage():
    sentence = "We are building additional data center capacity in West Texas."
    record = transcript(sentence)
    nodes, _, _ = extract_strategy(record, extracted_at=COMPOSED_AT)
    assert nodes
    for node in nodes:
        for item in node.evidence:
            assert item.source_text in record.metadata["content"]
            assert item.source_record_id == record.id
            assert item.source_period == "2026Q2"
            assert item.speaker_title == EXECUTIVE


def test_extraction_produces_only_observed_nodes():
    # Composition is where Atlas is allowed to conclude something nobody
    # said. Reading is not.
    nodes, edges, _ = extract(
        "We are expanding manufacturing capacity to lower unit costs, and our build "
        "depends on the availability of components."
    )
    assert {n.status for n in nodes} <= {EvidenceStatus.OBSERVED}
    assert {e.status for e in edges} <= {EvidenceStatus.OBSERVED}


# ------------------------------------------------------------------- 44
def test_a_non_transcript_record_produces_nothing_in_v1():
    # Filings are in the corpus and are not yet read: their risk-factor
    # sections are boilerplate at a density this layer has no rule for,
    # and a half-working filing reader would quietly become the main
    # source of failure modes.
    nodes, edges, rejected = extract_strategy(
        filing("We depend on the availability of clean room space."), extracted_at=COMPOSED_AT
    )
    assert (nodes, edges, rejected) == ((), (), ())

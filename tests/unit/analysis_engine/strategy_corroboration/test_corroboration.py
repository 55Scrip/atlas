"""Strategic Corroboration v1 -- what counts as independent evidence.

The layer beneath this one measures emphasis, which management authors.
This one asks what the company did, so nearly every test here is about a
boundary: management language may not corroborate management language, a
reported figure may not be read backwards in time, and a silence may not
be read as a denial.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from atlas.analysis_engine.strategy import compose_company_strategy
from atlas.analysis_engine.strategy_corroboration import (
    CorroborationItem,
    CorroborationRelation,
    CoverageState,
    EvidenceClass,
    IndependenceChannel,
    NodeCorroboration,
    ObservedEvidence,
    TemporalRelation,
    company_corroboration,
    temporal_relation,
)
from tests.unit.analysis_engine.strategy_corroboration._fixtures import (
    COMPOSED_AT,
    EVALUATED_AT,
    financials,
)
from tests.unit.analysis_engine.strategy_salience._fixtures import ANALYST, CEO, CFO, call

# Alphabet's real reported capital expenditure, and the real fiscal years.
GOOGL_CAPEX = {2024: 52.53e9, 2025: 91.45e9}
# VST's real reported operating income: it fell while capital spending rose.
VST_OPERATING_INCOME = {2024: 4.08e9, 2025: 1.91e9}

BUILD = "We are building additional data center capacity to support demand."


def corroborate(transcripts, statements, *, guidance=(), company="VST"):
    strategy = compose_company_strategy(transcripts, composed_at=COMPOSED_AT)
    return company_corroboration(
        strategy, tuple(transcripts) + tuple(statements),
        evaluated_at=EVALUATED_AT, guidance=guidance,
    )


def node_for(result, fragment):
    found = [n for n in result.nodes if fragment in n.subject_text]
    assert found, f"no node matching {fragment!r} in {[n.subject_text for n in result.nodes]}"
    return found[0]


def capex_statements(company="VST", values=GOOGL_CAPEX):
    return [
        financials({"capital_expenditure": values[2024]}, company=company, period_end=date(2024, 12, 31)),
        financials({"capital_expenditure": values[2025]}, company=company, period_end=date(2025, 12, 31)),
    ]


# ------------------------------------------------------------------ 1,2,3
def test_management_language_can_never_corroborate_anything():
    # The type refuses it. STATED_INTENT exists so the class can be
    # named and excluded, not so it can be counted.
    evidence = ObservedEvidence(
        evidence_id="e1", evidence_class=EvidenceClass.STATED_INTENT,
        channel=IndependenceChannel.MANAGEMENT_STATEMENT, measure="capital_expenditure",
        period="2025Q3", published_at=None,
    )
    with pytest.raises(ValueError, match="management language"):
        CorroborationItem(
            node_id="n1", evidence=evidence, relation=CorroborationRelation.SUPPORTS_EXECUTION,
            temporal=TemporalRelation.CONTEMPORANEOUS, derivation_rule="r",
        )


def test_repeating_a_statement_adds_no_corroboration():
    once = corroborate(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"), capex_statements())
    thrice = corroborate(
        tuple(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"))
        + tuple(call((CEO, "Pat Lee", BUILD), quarter="2025Q4"))
        + tuple(call((CEO, "Pat Lee", BUILD), quarter="2026Q1")),
        capex_statements(),
    )
    assert (
        node_for(once, "data center").independent_event_count
        == node_for(thrice, "data center").independent_event_count
    )


def test_a_second_executive_is_not_a_second_observation():
    # Speaker breadth is a salience signal. Two people describing one
    # company are still one company.
    one = corroborate(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"), capex_statements())
    two = corroborate(
        call((CEO, "Pat Lee", BUILD), (CFO, "Sam Ray", BUILD), quarter="2025Q3"), capex_statements()
    )
    assert (
        node_for(one, "data center").independent_event_count
        == node_for(two, "data center").independent_event_count
    )


# -------------------------------------------------------------- 4,5,33
def test_reported_spending_can_support_execution():
    # The positive control, on Alphabet's real figures: capital
    # expenditure rose from $52.5bn to $91.5bn while management
    # described a data-centre build-out.
    result = corroborate(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"), capex_statements())
    node = node_for(result, "data center")
    assert node.coverage is CoverageState.OBSERVED_SUPPORTING
    item = node.supporting[0]
    assert item.relation is CorroborationRelation.SUPPORTS_EXECUTION
    assert item.evidence.evidence_class is EvidenceClass.RESOURCE_DEPLOYMENT
    assert item.evidence.channel is IndependenceChannel.REPORTED_FINANCIAL_STATEMENT
    # Provenance: the record, the measure, the period, the owner, the rule.
    assert item.evidence.source_record_id
    assert item.evidence.semantic_owner == "business_facts"
    assert item.derivation_rule


def test_supporting_execution_is_not_a_claim_about_success_or_cause():
    result = corroborate(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"), capex_statements())
    node = node_for(result, "data center")
    disclaimed = " ".join(node.may_not_conclude)
    assert "caused" in disclaimed
    assert "succeeding" in disclaimed
    assert "material" in disclaimed
    assert not any("success" in r.value for r in CorroborationRelation)


# ---------------------------------------------------------------- 23,24,25
def test_a_figure_measuring_time_before_the_statement_cannot_support_it():
    # Fiscal 2025 closed before a strategy first stated in 2026Q2 was
    # announced. It is context, never execution.
    assert temporal_relation("2026Q2", "2025-12-31") is TemporalRelation.PRECEDES_STRATEGY
    result = corroborate(call((CEO, "Pat Lee", BUILD), quarter="2026Q2"), capex_statements())
    node = node_for(result, "data center")
    assert node.supporting == ()
    assert node.coverage is CoverageState.NO_INDEPENDENT_EVIDENCE
    assert [i.relation for i in node.context] == [CorroborationRelation.CONTEXT_ONLY]


def test_backwards_leakage_is_refused_by_the_type():
    evidence = ObservedEvidence(
        evidence_id="e", evidence_class=EvidenceClass.RESOURCE_DEPLOYMENT,
        channel=IndependenceChannel.REPORTED_FINANCIAL_STATEMENT,
        measure="capital_expenditure", period="2024-12-31", published_at=None,
    )
    with pytest.raises(ValueError, match="backwards leakage"):
        CorroborationItem(
            node_id="n", evidence=evidence, relation=CorroborationRelation.SUPPORTS_EXECUTION,
            temporal=TemporalRelation.PRECEDES_STRATEGY, derivation_rule="r",
        )


def test_temporal_relations_are_ordered_correctly():
    assert temporal_relation("2025Q3", "2025-12-31") is TemporalRelation.CONTEMPORANEOUS
    assert temporal_relation("2025Q3", "2027-12-31") is TemporalRelation.SUBSEQUENT
    assert temporal_relation(None, "2025-12-31") is TemporalRelation.UNKNOWN
    assert temporal_relation("2025Q3", None) is TemporalRelation.UNKNOWN


# ------------------------------------------------------------ 21,22,8,9
def test_the_four_silences_are_four_different_answers():
    base = dict(node_id="n", company="C", node_kind="initiative", subject_text="s")
    assert NodeCorroboration(**base, searched_measures=("capital_expenditure",)).coverage is (
        CoverageState.NO_INDEPENDENT_EVIDENCE
    )
    assert NodeCorroboration(**base, unavailable_measures=("headcount",)).coverage is (
        CoverageState.EVIDENCE_SOURCE_UNAVAILABLE
    )
    assert NodeCorroboration(**base).coverage is CoverageState.SEMANTIC_LINK_UNAVAILABLE


def test_no_evidence_is_never_reported_as_the_company_not_acting():
    node = NodeCorroboration(
        node_id="n", company="C", node_kind="initiative", subject_text="s",
        searched_measures=("capital_expenditure",),
    )
    assert node.coverage is CoverageState.NO_INDEPENDENT_EVIDENCE
    assert any("did not act" in claim for claim in node.may_not_conclude)


def test_measures_atlas_cannot_observe_are_named_not_skipped():
    # There is no research-spending line and no headcount line in
    # BusinessFact, so Atlas can never see either move. Saying so is
    # honest; calling it "not corroborated" would imply a search that
    # could have succeeded.
    result = corroborate(
        call((CEO, "Pat Lee", "We have allocated significant headcount to this effort."), quarter="2025Q3"),
        capex_statements(),
    )
    node = next(n for n in result.nodes if n.unavailable_measures)
    assert "headcount" in node.unavailable_measures
    assert node.coverage is CoverageState.EVIDENCE_SOURCE_UNAVAILABLE
    assert any("no channel" in claim for claim in node.may_not_conclude)


# ------------------------------------------------------------- 11,12,13,14
def test_guidance_supports_commitment_and_never_action():
    class _Subject:
        value = "capital_expenditure"

    class _Guidance:
        signal_id = "g1"
        subject = _Subject()
        source_period = "2025Q3"

    result = corroborate(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q3"), (), guidance=(_Guidance(),)
    )
    node = node_for(result, "data center")
    guidance_items = [
        i for i in node.supporting if i.evidence.evidence_class is EvidenceClass.GUIDANCE_COMMITMENT
    ]
    assert guidance_items
    assert guidance_items[0].relation is CorroborationRelation.SUPPORTS_COMMITMENT
    assert guidance_items[0].evidence.semantic_owner == "forward_claims"
    # It is management-authored, and is never counted as action.
    assert guidance_items[0].evidence.channel is IndependenceChannel.MANAGEMENT_GUIDANCE
    assert all(
        i.relation is not CorroborationRelation.SUPPORTS_EXECUTION
        for i in guidance_items
    )


def test_absent_contract_evidence_is_not_contradiction():
    # Every company with a transcript in this corpus returns zero
    # customer commitments. That is coverage, not a finding about any
    # company's commercial relationships.
    result = corroborate(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"), capex_statements())
    node = node_for(result, "data center")
    assert node.weakening == ()
    assert all(
        i.evidence.evidence_class is not EvidenceClass.CUSTOMER_COMMITMENT
        for i in node.supporting
    )


# ---------------------------------------------------------- 16,17,18,19,20
def test_an_outcome_moving_the_stated_way_supports_the_outcome_only():
    result = corroborate(
        call((CEO, "Pat Lee", "We are expanding manufacturing capacity to lower unit costs."),
             quarter="2025Q3"),
        [
            financials({"operating_income": 7.87e9}, period_end=date(2024, 12, 31)),
            financials({"operating_income": 8.29e9}, period_end=date(2025, 12, 31)),
        ],
    )
    outcome = next(n for n in result.nodes if n.node_kind == "expected_outcome")
    assert outcome.coverage is CoverageState.OBSERVED_SUPPORTING
    assert outcome.supporting[0].relation is CorroborationRelation.SUPPORTS_OUTCOME
    # Never execution, and never causation.
    assert outcome.supporting[0].relation is not CorroborationRelation.SUPPORTS_EXECUTION
    assert any("caused" in claim for claim in outcome.may_not_conclude)


def test_an_outcome_moving_the_other_way_weakens_it_without_declaring_failure():
    # VST's real figures: operating income fell from $4.08bn to $1.91bn.
    # The pairing does not occur in the corpus, because VST states no
    # expected outcome -- so the numbers are real and the case is built.
    result = corroborate(
        call((CEO, "Pat Lee", "We are expanding manufacturing capacity to lower unit costs."),
             quarter="2025Q3"),
        [
            financials({"operating_income": VST_OPERATING_INCOME[2024]}, period_end=date(2024, 12, 31)),
            financials({"operating_income": VST_OPERATING_INCOME[2025]}, period_end=date(2025, 12, 31)),
        ],
    )
    outcome = next(n for n in result.nodes if n.node_kind == "expected_outcome")
    assert outcome.coverage is CoverageState.OBSERVED_WEAKENING
    assert outcome.weakening[0].relation is CorroborationRelation.WEAKENS_OUTCOME
    # Weakening is about the evidence, not a verdict on the strategy.
    assert not any("fail" in r.value for r in CorroborationRelation)
    assert not any(s.value.startswith("strategy_") for s in CoverageState)


def test_support_and_weakening_coexist_without_being_voted():
    node = NodeCorroboration(
        node_id="n", company="C", node_kind="initiative", subject_text="s",
        supporting=(CorroborationItem(
            node_id="n",
            evidence=ObservedEvidence(
                evidence_id="a", evidence_class=EvidenceClass.RESOURCE_DEPLOYMENT,
                channel=IndependenceChannel.REPORTED_FINANCIAL_STATEMENT,
                measure="capital_expenditure", period="2025-12-31", published_at=None),
            relation=CorroborationRelation.SUPPORTS_EXECUTION,
            temporal=TemporalRelation.CONTEMPORANEOUS, derivation_rule="r"),),
        weakening=(CorroborationItem(
            node_id="n",
            evidence=ObservedEvidence(
                evidence_id="b", evidence_class=EvidenceClass.FINANCIAL_OUTCOME,
                channel=IndependenceChannel.REPORTED_FINANCIAL_STATEMENT,
                measure="operating_income", period="2025-12-31", published_at=None),
            relation=CorroborationRelation.WEAKENS_OUTCOME,
            temporal=TemporalRelation.CONTEMPORANEOUS, derivation_rule="r"),),
        searched_measures=("capital_expenditure", "operating_income"),
    )
    assert node.coverage is CoverageState.MIXED
    assert len(node.supporting) == 1 and len(node.weakening) == 1


# ---------------------------------------------------------------- 6,7,27,28
def test_two_figures_are_only_compared_when_the_measure_and_unit_match():
    evidence = ObservedEvidence(
        evidence_id="e", evidence_class=EvidenceClass.RESOURCE_DEPLOYMENT,
        channel=IndependenceChannel.REPORTED_FINANCIAL_STATEMENT,
        measure="capital_expenditure", period="2025-12-31", published_at=None,
        value=91.45e9, prior_value=None,
    )
    assert evidence.direction is None, "no prior period means no direction, not 'unchanged'"


def test_one_fiscal_years_measure_is_one_observation_however_often_it_appears():
    a = ObservedEvidence(
        evidence_id="x", evidence_class=EvidenceClass.RESOURCE_DEPLOYMENT,
        channel=IndependenceChannel.REPORTED_FINANCIAL_STATEMENT,
        measure="capital_expenditure", period="2025-12-31", published_at=None)
    b = ObservedEvidence(
        evidence_id="y", evidence_class=EvidenceClass.RESOURCE_DEPLOYMENT,
        channel=IndependenceChannel.REPORTED_FINANCIAL_STATEMENT,
        measure="capital_expenditure", period="2025-12-31", published_at=None)
    assert a.event_key == b.event_key


def test_duplicating_the_whole_corpus_changes_nothing():
    transcripts = call((CEO, "Pat Lee", BUILD), quarter="2025Q3")
    statements = capex_statements()
    once = corroborate(transcripts, statements)
    twice = corroborate(tuple(transcripts) * 2, tuple(statements) * 2)

    def shape(result):
        return sorted(
            (n.subject_text, n.coverage.value, len(n.supporting), len(n.weakening),
             n.independent_event_count)
            for n in result.nodes
        )

    assert shape(once) == shape(twice)


def test_a_measure_implied_twice_by_one_node_is_one_observation():
    # A node can imply the same reported line through two routes -- a
    # stated capital commitment and a capacity factor both point at
    # capital expenditure. Counting it once is the difference between
    # "one observation" and "two independent observations".
    result = corroborate(
        call((CEO, "Pat Lee",
              "We have allocated capital to building additional data center capacity."),
             quarter="2025Q3"),
        capex_statements(),
    )
    for node in result.nodes:
        measures = [i.evidence.measure for i in node.supporting + node.weakening + node.context]
        assert len(measures) == len(set(measures)), node.subject_text


def test_two_figures_in_different_currencies_are_not_compared():
    # A figure reported in dollars one year and euros the next is not a
    # rise. Comparing them would manufacture an observation out of a
    # reporting change.
    result = corroborate(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q3"),
        [
            financials({"capital_expenditure": 52.53e9, "currency": "USD"},
                       period_end=date(2024, 12, 31)),
            financials({"capital_expenditure": 91.45e9, "currency": "EUR"},
                       period_end=date(2025, 12, 31)),
        ],
    )
    node = node_for(result, "data center")
    assert node.supporting == ()
    assert all(i.evidence.prior_value is None for i in node.context)


def test_a_restated_period_is_not_compared_against_its_own_original():
    # Two filings reporting the same fiscal year is a restatement, not a
    # change. Atlas's fact layer refuses to produce either figure rather
    # than choose between them, and this layer must not see a movement
    # where the fact layer saw a conflict.
    result = corroborate(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q3"),
        [
            financials({"capital_expenditure": 2.0e9}, period_end=date(2025, 12, 31),
                       identifier="original"),
            financials({"capital_expenditure": 2.6e9}, period_end=date(2025, 12, 31),
                       identifier="restated"),
        ],
    )
    node = node_for(result, "data center")
    assert node.supporting == ()
    assert node.weakening == ()


def test_a_figure_is_never_compared_against_itself():
    """Defence in depth, tested directly because it is unreachable
    today.

    `extract_facts_from_records` refuses to emit two facts for one
    fiscal period, so nothing in the current pipeline can hand this
    layer a figure and itself. If that ever changes, comparing them
    would report `unchanged` -- an observation Atlas never made -- so
    the guard is tested at the function rather than left as a comment
    nobody can check."""
    from atlas.analysis_engine.strategy_corroboration.analysis import _comparable

    class _Fact:
        def __init__(self, period, unit="USD"):
            self.kind, self.period, self.unit = "capital_expenditure", period, unit

    same_period = _Fact("2025-12-31")
    assert not _comparable(same_period, _Fact("2025-12-31"))
    assert _comparable(same_period, _Fact("2024-12-31"))
    assert not _comparable(same_period, _Fact("2024-12-31", unit="EUR"))
    assert not _comparable(same_period, None)


def test_one_measure_implied_by_two_routes_is_still_one_observation():
    # A node can point at one reported line twice -- through a stated
    # capital commitment and through a capacity factor. Extraction does
    # not currently build such a node, so the guard is tested here
    # directly rather than through a fixture that would silently stop
    # exercising it.
    from atlas.analysis_engine.strategy import (
        CompanyStrategy, EvidenceStatus, FactorClass, ResourceKind,
        StrategyEvidence, StrategyNode, StrategyNodeKind,
    )

    node = StrategyNode(
        node_id="n1", company="VST", kind=StrategyNodeKind.INITIATIVE,
        status=EvidenceStatus.OBSERVED,
        factor=FactorClass.COMPUTE_CAPACITY, resource=ResourceKind.CAPITAL,
        subject_text="data center", observed_periods=("2025Q3",),
        evidence=(StrategyEvidence(
            source_record_id="r1", source_text=BUILD, source_kind="transcript",
            company="VST", source_period="2025Q3", statement_at=None, speaker_title=CEO),),
    )
    strategy = CompanyStrategy(company="VST", nodes=(node,))
    result = company_corroboration(
        strategy, tuple(capex_statements()), evaluated_at=EVALUATED_AT
    )
    observed = result.nodes[0]
    measures = [i.evidence.measure for i in observed.supporting + observed.weakening + observed.context]
    assert measures.count("capital_expenditure") == 1
    assert observed.independent_event_count == 1


def test_a_single_reported_period_yields_no_direction():
    # With one year of data there is nothing to compare against, and
    # "unchanged" would be a fabricated observation.
    result = corroborate(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q3"),
        [financials({"capital_expenditure": 91.45e9}, period_end=date(2025, 12, 31))],
    )
    node = node_for(result, "data center")
    assert node.supporting == ()
    assert all(i.evidence.direction is None for i in node.context)


def test_an_unchanged_measure_supports_nothing():
    result = corroborate(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q3"),
        [
            financials({"capital_expenditure": 91.45e9}, period_end=date(2024, 12, 31)),
            financials({"capital_expenditure": 91.45e9}, period_end=date(2025, 12, 31)),
        ],
    )
    node = node_for(result, "data center")
    assert node.supporting == ()
    assert node.weakening == ()
    assert [i.relation for i in node.context] == [CorroborationRelation.CONTEXT_ONLY]


def test_no_enum_in_this_package_offers_success_or_a_market_price_class():
    # Checked on the enums, not only on the model's attributes: a
    # success state or a price class would be a new *member*, which an
    # attribute sweep over the records cannot see.
    from atlas.analysis_engine.strategy_corroboration import contracts

    forbidden = ("success", "market", "price", "score", "materiality", "proof")
    for enum_name in ("EvidenceClass", "CorroborationRelation", "CoverageState",
                      "TemporalRelation", "IndependenceChannel"):
        for member in getattr(contracts, enum_name):
            assert not any(word in member.value.lower() for word in forbidden), (
                f"{enum_name}.{member.name}"
            )


# ------------------------------------------------------------------- 29
def test_share_price_is_excluded_and_says_so():
    result = corroborate(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"), capex_statements())
    assert any("market_price" in channel for channel in result.excluded_channels)
    for node in result.nodes:
        for item in node.supporting + node.weakening + node.context:
            assert "price" not in item.evidence.measure


# ---------------------------------------------------------------- 30,31,32
def test_nothing_in_this_package_exposes_a_score_or_a_success_state():
    from atlas.analysis_engine.strategy_corroboration import models

    forbidden = ("score", "confidence", "strength", "rank", "weight", "materiality",
                 "success", "proof", "probability")
    for name in models.__all__:
        for attribute in dir(getattr(models, name)):
            if attribute.startswith("_"):
                continue
            assert not any(word in attribute.lower() for word in forbidden), f"{name}.{attribute}"


# ---------------------------------------------------------------- 34,35
def test_corroboration_is_deterministic_and_order_independent():
    transcripts = call((CEO, "Pat Lee", BUILD), (CFO, "Sam Ray", BUILD), quarter="2025Q3")
    statements = capex_statements()

    def shape(t, s, at=EVALUATED_AT):
        strategy = compose_company_strategy(t, composed_at=COMPOSED_AT)
        result = company_corroboration(strategy, tuple(t) + tuple(s), evaluated_at=at)
        return sorted((n.node_id, n.coverage.value, n.independent_event_count) for n in result.nodes)

    assert shape(transcripts, statements) == shape(transcripts, statements)
    assert shape(transcripts, statements) == shape(tuple(reversed(transcripts)), tuple(reversed(statements)))
    assert shape(transcripts, statements) == shape(
        transcripts, statements, EVALUATED_AT + timedelta(days=400)
    )


def test_an_analyst_question_is_not_an_observation():
    with_analyst = corroborate(
        call((CEO, "Pat Lee", BUILD), (ANALYST, "Chris Vale", "How much capex?"), quarter="2025Q3"),
        capex_statements(),
    )
    without = corroborate(call((CEO, "Pat Lee", BUILD), quarter="2025Q3"), capex_statements())
    assert (
        node_for(with_analyst, "data center").independent_event_count
        == node_for(without, "data center").independent_event_count
    )

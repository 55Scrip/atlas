"""Composition -- where Atlas is allowed to conclude something nobody
said, and where it must say so.

The temporal tests carry most of the weight. A strategy layer that
overwrites last year's strategy with this year's, or that counts four
quarters of the same rehearsed sentence as four pieces of evidence, is
worse than no strategy layer: the first loses history, the second
rewards repetition.
"""
from datetime import timedelta

from atlas.analysis_engine.strategy import (
    ContinuityState,
    EvidenceStatus,
    FactorClass,
    RelationKind,
    StrategyNodeKind,
    compose_company_strategy,
    find_cross_company_adjacencies,
)
from tests.unit.analysis_engine.strategy._fixtures import COMPOSED_AT, transcript

BUILD = "We are building additional data center capacity to support our platform."
NEED = "Our roadmap depends on the availability of components from our suppliers."


def compose(*records):
    return compose_company_strategy(records, composed_at=COMPOSED_AT)


# --------------------------------------------------------------- 20,21,22
def test_a_restated_strategy_is_one_node_with_several_observations():
    strategy = compose(
        transcript(BUILD, quarter="2025Q3", index=0),
        transcript(BUILD, quarter="2025Q4", index=1),
        transcript(BUILD, quarter="2026Q1", index=2),
    )
    initiatives = strategy.of_kind(StrategyNodeKind.INITIATIVE)
    assert len(initiatives) == 1, "repetition is how a strategy is communicated, not four strategies"
    assert initiatives[0].observed_periods == ("2025Q3", "2025Q4", "2026Q1")
    assert initiatives[0].continuity is ContinuityState.CONTINUING


def test_repetition_does_not_multiply_evidence_weight():
    once = compose(transcript(BUILD, quarter="2026Q1", index=0))
    thrice = compose(
        transcript(BUILD, quarter="2025Q3", index=0),
        transcript(BUILD, quarter="2025Q4", index=1),
        transcript(BUILD, quarter="2026Q1", index=2),
    )
    assert len(once.of_kind(StrategyNodeKind.INITIATIVE)) == len(
        thrice.of_kind(StrategyNodeKind.INITIATIVE)
    )
    # The extra observations are visible as periods, which is a fact
    # about when it was said -- never as a stronger status.
    assert thrice.of_kind(StrategyNodeKind.INITIATIVE)[0].status is EvidenceStatus.OBSERVED


def test_history_stays_queryable_and_the_node_is_dated_from_first_statement():
    strategy = compose(
        transcript(BUILD, quarter="2025Q3", index=0),
        transcript(BUILD, quarter="2026Q2", index=1),
    )
    node = strategy.of_kind(StrategyNodeKind.INITIATIVE)[0]
    assert node.observed_periods[0] == "2025Q3", "a strategy is dated from when it was first stated"
    assert {e.source_period for e in node.evidence} == {"2025Q3", "2026Q2"}


def test_an_old_statement_does_not_silently_become_current():
    # Only one period was ever observed, and nothing here pretends the
    # 2025Q3 statement is a 2026 one. The consumer reads the periods.
    strategy = compose(transcript(BUILD, quarter="2025Q3", index=0))
    node = strategy.of_kind(StrategyNodeKind.INITIATIVE)[0]
    assert node.observed_periods == ("2025Q3",)
    assert node.continuity is ContinuityState.NEW


def test_a_reworded_restatement_reads_as_modified_not_new():
    strategy = compose(
        transcript(BUILD, quarter="2025Q3", index=0),
        transcript(
            "We are building more server capacity for the platform.", quarter="2026Q2", index=1
        ),
    )
    initiatives = strategy.of_kind(StrategyNodeKind.INITIATIVE)
    assert len(initiatives) == 1
    assert initiatives[0].continuity is ContinuityState.MODIFIED
    # And the surviving node is the *earlier* one. If the latest
    # statement won, the 2026Q2 wording would silently become the whole
    # history of this strategy, which is the overwrite this layer
    # exists to avoid.
    assert initiatives[0].subject_text == "data center"
    assert initiatives[0].observed_periods[0] == "2025Q3"


# ------------------------------------------------------------------- 23
def test_continuity_has_no_abandoned_state():
    # Silence is not abandonment. A strategy that stops being mentioned
    # is a strategy that stopped being mentioned, and the corpus has no
    # sentence in which management says it stopped doing something.
    assert not hasattr(ContinuityState, "ABANDONED")
    assert {s.value for s in ContinuityState} == {"new", "continuing", "modified"}


# ---------------------------------------------------------------- 1,2,10def test_an_economic_engine_is_not_an_initiative_plus_an_outcome():
    """Superseded by the coverage pass.

    The first definition composed an engine from an initiative and an
    expected outcome. That describes a *strategy* -- something the
    company is doing and hopes will work -- and it returned UNKNOWN for
    all four benchmarks while both MA and Alphabet were describing their
    actual engines in plain words. An engine is how the business that
    already exists converts something it holds into money, so it has its
    own evidence and is never assembled out of plans."""
    strategy = compose(
        transcript(
            "We are expanding manufacturing capacity to lower unit costs.",
            quarter="2025Q4", index=0,
        ),
        transcript(
            "We are expanding manufacturing capacity to lower unit costs further.",
            quarter="2026Q1", index=1,
        ),
    )
    assert strategy.of_kind(StrategyNodeKind.INITIATIVE)
    assert strategy.of_kind(StrategyNodeKind.EXPECTED_OUTCOME)
    assert strategy.of_kind(StrategyNodeKind.ECONOMIC_ENGINE) == ()


def test_derived_success_condition_and_failure_mode_from_one_dependency():
    # Zero of each across four benchmarks, because management states the
    # dependency and never spells out its two restatements. Both are
    # direct transformations of the same observed sentence -- so both
    # are derivable, and both must stay DERIVED.
    strategy = compose(
        transcript("Our build depends on the availability of components.", quarter="2026Q1")
    )
    dependency = strategy.of_kind(StrategyNodeKind.DEPENDENCY)[0]
    condition = strategy.of_kind(StrategyNodeKind.SUCCESS_CONDITION)[0]
    failure = strategy.of_kind(StrategyNodeKind.FAILURE_MODE)[0]

    for node, rule in (
        (condition, "success-condition-from-observed-dependency"),
        (failure, "failure-mode-from-observed-dependency"),
    ):
        assert node.status is EvidenceStatus.DERIVED
        assert node.derivation_rule == rule
        assert node.derived_from == (dependency.node_id,)
        assert node.factor is dependency.factor
        assert node.evidence == dependency.evidence


def test_no_condition_is_derived_without_a_dependency_to_derive_it_from():
    # Exactly one condition and one failure mode per dependency, and
    # nothing at all otherwise. No path invents a second condition.
    strategy = compose(
        transcript("We are building additional data center capacity.", quarter="2026Q1")
    )
    assert strategy.of_kind(StrategyNodeKind.DEPENDENCY) == ()
    assert strategy.of_kind(StrategyNodeKind.SUCCESS_CONDITION) == ()
    assert strategy.of_kind(StrategyNodeKind.FAILURE_MODE) == ()


def test_unknown_is_carried_explicitly_not_as_an_empty_graph():
    strategy = compose(transcript(BUILD, quarter="2026Q1"))
    # An unexamined company and one whose corpus supports nothing must
    # not look alike.
    assert StrategyNodeKind.FAILURE_MODE.value in strategy.unknowns
    assert StrategyNodeKind.SUCCESS_CONDITION.value in strategy.unknowns


# ------------------------------------------------------------------- 17
def test_a_node_with_no_contradicting_passage_reports_no_contradiction():
    # Not "reports agreement". Almost every assertion Atlas holds has no
    # contradicting passage, and if emptiness here were ever read as
    # confirmation, silence would be Atlas's strongest evidence.
    strategy = compose(transcript(BUILD, quarter="2026Q1"))
    node = strategy.of_kind(StrategyNodeKind.INITIATIVE)[0]
    assert node.supporting
    assert node.contradicting == ()


def test_supporting_and_contradicting_evidence_stay_separate():
    # Phase O. A node may carry both, and the two partitions must never
    # overlap: a consumer counting "the evidence for this" has to be
    # unable to count a refutation among it.
    from atlas.analysis_engine.strategy import StrategyEvidence, StrategyNode, SupportPolarity

    def item(text, polarity):
        return StrategyEvidence(
            source_record_id="r1", source_text=text, source_kind="transcript",
            company="ACME", source_period="2026Q1", statement_at=None,
            speaker_title="Chief Executive Officer", polarity=polarity,
        )

    node = StrategyNode(
        node_id="n1", company="ACME", kind=StrategyNodeKind.INITIATIVE,
        status=EvidenceStatus.OBSERVED, factor=FactorClass.ELECTRIC_POWER,
        evidence=(
            item("We are adding generation capacity.", SupportPolarity.SUPPORTS),
            item("We have paused that generation capacity build.", SupportPolarity.CONTRADICTS),
            item("Generation capacity is discussed on slide nine.", SupportPolarity.CONTEXT),
        ),
    )
    assert len(node.supporting) == 1
    assert len(node.contradicting) == 1
    assert set(node.supporting).isdisjoint(node.contradicting)
    # Context is neither. It is in `evidence` and in neither partition,
    # which is the whole reason there are three polarities.
    assert len(node.evidence) == 3


def test_an_observed_node_cannot_be_built_without_its_source():
    import pytest

    from atlas.analysis_engine.strategy import StrategyNode

    with pytest.raises(ValueError, match="carries that source"):
        StrategyNode(
            node_id="x", company="ACME", kind=StrategyNodeKind.INITIATIVE,
            status=EvidenceStatus.OBSERVED, factor=FactorClass.ELECTRIC_POWER,
        )


def test_a_derived_node_cannot_be_built_without_naming_its_rule():
    import pytest

    from atlas.analysis_engine.strategy import StrategyNode

    with pytest.raises(ValueError, match="names the rule"):
        StrategyNode(
            node_id="x", company="ACME", kind=StrategyNodeKind.ECONOMIC_ENGINE,
            status=EvidenceStatus.DERIVED,
        )


# ------------------------------------------------------------------- 18
def test_a_derived_edge_is_never_labelled_observed():
    strategy = compose(
        transcript("Our goal is to expand data center capacity.", quarter="2026Q1", index=0),
        transcript(BUILD, quarter="2026Q1", index=1),
    )
    pursued = [e for e in strategy.edges if e.relation is RelationKind.PURSUED_BY]
    assert pursued and all(e.status is EvidenceStatus.DERIVED for e in pursued)
    assert all(e.derivation_rule for e in pursued)


# ------------------------------------------------------------------- 33
def test_composition_is_deterministic():
    records = (
        transcript(BUILD, quarter="2025Q3", index=0),
        transcript(NEED, quarter="2026Q1", index=1),
    )
    first = compose_company_strategy(records, composed_at=COMPOSED_AT)
    second = compose_company_strategy(records, composed_at=COMPOSED_AT)
    assert [n.node_id for n in first.nodes] == [n.node_id for n in second.nodes]
    assert [n.subject_text for n in first.nodes] == [n.subject_text for n in second.nodes]
    assert [(e.source_id, e.target_id) for e in first.edges] == [
        (e.source_id, e.target_id) for e in second.edges
    ]


def test_a_later_clock_does_not_change_the_graph():
    records = (transcript(BUILD, quarter="2026Q1"),)
    early = compose_company_strategy(records, composed_at=COMPOSED_AT)
    late = compose_company_strategy(records, composed_at=COMPOSED_AT + timedelta(days=400))
    assert [n.node_id for n in early.nodes] == [n.node_id for n in late.nodes]


# ------------------------------------------------------------------- 34
def test_composition_is_idempotent_over_duplicate_records():
    record = transcript(BUILD, quarter="2026Q1")
    once = compose_company_strategy((record,), composed_at=COMPOSED_AT)
    twice = compose_company_strategy((record, record), composed_at=COMPOSED_AT)
    assert [n.node_id for n in once.nodes] == [n.node_id for n in twice.nodes]
    assert len(once.nodes[0].evidence) == len(twice.nodes[0].evidence)
    assert len(once.edges) == len(twice.edges)


# ------------------------------------------------------------ 24,25,26,27
def test_two_companies_meet_at_a_canonical_factor():
    needs = compose_company_strategy(
        (transcript("Our expansion depends on the availability of components.", company="ACME"),),
        composed_at=COMPOSED_AT,
    )
    builds = compose_company_strategy(
        (transcript("We are expanding our supply chain footprint.", company="ZENITH"),),
        composed_at=COMPOSED_AT,
    )
    adjacencies = find_cross_company_adjacencies([needs, builds])
    assert len(adjacencies) == 1
    found = adjacencies[0]
    assert found.factor is FactorClass.SUPPLY_CHAIN_INPUTS
    assert (found.requiring_company, found.building_company) == ("ACME", "ZENITH")


def test_a_cross_company_match_is_a_hypothesis_and_disclaims_supply():
    needs = compose_company_strategy(
        (transcript("Our expansion depends on the availability of components.", company="ACME"),),
        composed_at=COMPOSED_AT,
    )
    builds = compose_company_strategy(
        (transcript("We are expanding our supply chain footprint.", company="ZENITH"),),
        composed_at=COMPOSED_AT,
    )
    found = find_cross_company_adjacencies([needs, builds])[0]
    assert found.status is EvidenceStatus.HYPOTHESIS
    disclaimed = " ".join(found.may_not_conclude)
    assert "supplies" in disclaimed
    assert "benefits" in disclaimed
    assert "revenue" in disclaimed


def test_no_relation_exists_that_could_express_a_beneficiary():
    # The firewall against beneficiary inference is structural, not a
    # rule someone has to remember: there is no edge type for it.
    assert not any("benefit" in relation.value for relation in RelationKind)
    assert not any("supplies" in relation.value for relation in RelationKind)


def test_a_company_is_not_adjacent_to_itself():
    both = compose_company_strategy(
        (
            transcript("Our expansion depends on the availability of components.", index=0),
            transcript("We are expanding our supply chain footprint.", index=1),
        ),
        composed_at=COMPOSED_AT,
    )
    assert find_cross_company_adjacencies([both]) == ()


def test_similar_sounding_factors_are_not_merged_by_resemblance():
    # "compute capacity" and "manufacturing capacity" share a word and
    # are different factors. Nothing in the resolver measures string
    # distance, so they cannot drift together.
    compute = compose_company_strategy(
        (transcript("Our plan depends on access to compute capacity.", company="ACME"),),
        composed_at=COMPOSED_AT,
    )
    manufacturing = compose_company_strategy(
        (transcript("We are expanding manufacturing capacity.", company="ZENITH"),),
        composed_at=COMPOSED_AT,
    )
    assert find_cross_company_adjacencies([compute, manufacturing]) == ()

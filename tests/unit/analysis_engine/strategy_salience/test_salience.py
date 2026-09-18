"""Strategic Salience v1 -- what the signals mean, and what they refuse
to mean.

Half of these tests assert that a number does *not* move. That is the
shape of the sprint: the risk in a salience layer is not that it counts
wrongly, it is that a count quietly becomes a verdict -- repetition
becoming truth, an analyst's interest becoming management's priority, a
node with six edges becoming "important".
"""
from datetime import timedelta

import pytest

from atlas.analysis_engine.strategy import compose_company_strategy
from atlas.analysis_engine.strategy_salience import (
    CallSection,
    SalienceEvidence,
    SpeakerRole,
    classify_role,
    company_salience,
    speaker_identity,
)
from tests.unit.analysis_engine.strategy_salience._fixtures import (
    ANALYST,
    CEO,
    CFO,
    COMPOSED_AT,
    IR,
    OPERATOR,
    call,
)

BUILD = "We are building additional data center capacity to support demand."
DEPEND = "Our build depends on the availability of components from our suppliers."


def salience(*record_groups):
    records = tuple(r for group in record_groups for r in group)
    strategy = compose_company_strategy(records, composed_at=COMPOSED_AT)
    return company_salience(strategy, records)


def by_subject(evidence, fragment):
    found = [e for e in evidence if fragment in e.subject_text]
    assert found, f"no node matching {fragment!r} in {[e.subject_text for e in evidence]}"
    return found[0]


# ------------------------------------------------------------------ 1,2
def test_period_recurrence_counts_distinct_periods():
    ev = salience(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q4"),
        call((CEO, "Pat Lee", BUILD), quarter="2026Q1"),
        call((CEO, "Pat Lee", BUILD), quarter="2026Q2"),
    )
    node = by_subject(ev, "data center")
    assert node.periods == ("2025Q4", "2026Q1", "2026Q2")
    assert node.period_count == 3


def test_the_same_statement_twice_in_one_period_is_one_period():
    ev = salience(
        call((CEO, "Pat Lee", BUILD), (CFO, "Sam Ray", BUILD), quarter="2026Q2"),
    )
    assert by_subject(ev, "data center").period_count == 1


def test_duplicating_the_entire_corpus_changes_no_signal():
    records = call((CEO, "Pat Lee", BUILD), (CFO, "Sam Ray", BUILD), quarter="2026Q2")
    once = salience(records)
    twice = salience(records, records)

    def shape(evidence):
        return sorted(
            (e.subject_text, e.period_count, e.management_speaker_count,
             len(e.prepared_remark_refs), len(e.qa_refs), e.priority_language.count,
             e.analyst_attention.analyst_count, e.graph_linkage.degree)
            for e in evidence
        )

    assert shape(once) == shape(twice)


# -------------------------------------------------------------------- 3
def test_speaker_breadth_counts_people_not_titles():
    # The provider spells one office several ways across quarters. VST's
    # CEO is "President and CEO" in one call and "President and Chief
    # Executive Officer" in the next, and is also "Jim Burke" and "James
    # Burke". Counting spellings turned a two-voice node into four.
    ev = salience(
        call((CEO, "James Burke", BUILD), quarter="2025Q4"),
        call(("President and CEO", "Jim Burke", BUILD), quarter="2026Q1"),
    )
    assert by_subject(ev, "data center").management_speaker_count == 1


def test_two_different_executives_are_two_voices():
    ev = salience(call((CEO, "Pat Lee", BUILD), (CFO, "Sam Ray", BUILD), quarter="2026Q2"))
    node = by_subject(ev, "data center")
    assert node.management_speaker_count == 2
    assert {m.role for m in node.speakers} == {SpeakerRole.CHIEF_EXECUTIVE, SpeakerRole.CHIEF_FINANCIAL}


def test_speaker_identity_separates_two_people_sharing_a_surname():
    assert speaker_identity("Pat Lee", CEO) != speaker_identity("Sam Lee", CFO)


# -------------------------------------------------------------------- 4
def test_an_analyst_is_never_a_management_speaker():
    ev = salience(
        call((CEO, "Pat Lee", BUILD), (ANALYST, "Chris Vale", BUILD), quarter="2026Q2")
    )
    node = by_subject(ev, "data center")
    assert node.management_speaker_count == 1
    assert all(m.role.is_management for m in node.speakers)
    assert SpeakerRole.ANALYST not in {m.role for m in node.speakers}


def test_investor_relations_counts_as_management_but_analysts_never_do():
    assert classify_role(IR).is_management
    assert classify_role("Corporate Vice President, Investor Relations").is_management
    assert not classify_role(ANALYST).is_management
    assert not classify_role("Analyst, President of Equity Research").is_management
    assert not classify_role(OPERATOR).is_management


# -------------------------------------------------------------------- 5
def test_analyst_attention_is_recorded_separately_and_never_added():
    ev = salience(
        call(
            (CEO, "Pat Lee", BUILD),
            (ANALYST, "Chris Vale", "Can you talk about data center capacity?"),
            (CEO, "Pat Lee", "Yes, demand is strong."),
            quarter="2026Q2",
        )
    )
    node = by_subject(ev, "data center")
    assert node.analyst_attention.analyst_count == 1
    assert node.analyst_attention.periods == ("2026Q2",)
    # The management count is untouched by the analyst's interest.
    assert node.management_speaker_count == 1
    # And there is no field anywhere that adds the two.
    assert not hasattr(node, "total_attention")
    assert not hasattr(node, "combined_speakers")


def test_analyst_attention_without_management_mention_creates_no_node():
    # A topic only analysts raise cannot become a management priority,
    # because it never becomes a strategy node in the first place.
    ev = salience(
        call(
            (CEO, "Pat Lee", "Results were solid this quarter."),
            (ANALYST, "Chris Vale", "What about regulatory approvals and permits?"),
            quarter="2026Q2",
        )
    )
    assert [e for e in ev if "regulator" in e.subject_text.lower()] == []


# ------------------------------------------------------------------ 6,7
def test_explicit_priority_language_is_recorded():
    ev = salience(
        call((CEO, "Pat Lee",
              "We are building additional data center capacity, and that is our top priority."),
             quarter="2026Q2")
    )
    node = by_subject(ev, "data center")
    assert node.priority_language.count == 1
    assert "top priority" in node.priority_language.refs[0].text


@pytest.mark.parametrize(
    "sentence",
    [
        "We are building additional data center capacity and we are excited about it.",
        "We are building additional data center capacity, an important opportunity.",
        "We are building additional data center capacity and remain well positioned.",
    ],
)
def test_vague_enthusiasm_is_not_priority_language(sentence):
    # 277 sentences in the benchmark corpus contain one of these words,
    # against 15 explicit priority statements. At eighteen to one they
    # would drown every real one.
    ev = salience(call((CEO, "Pat Lee", sentence), quarter="2026Q2"))
    assert by_subject(ev, "data center").priority_language.count == 0


# -------------------------------------------------------------- 8,9,10
def test_resource_commitment_linkage_is_exposed():
    ev = salience(
        call(
            (CEO, "Pat Lee", "We are building additional manufacturing capacity."),
            (CFO, "Sam Ray", "We have allocated capital to our manufacturing capacity build."),
            quarter="2026Q2",
        )
    )
    initiative = by_subject(ev, "manufacturing capacity")
    assert initiative.resource_commitment_links


def test_forward_evidence_links_are_supplied_by_the_caller_not_fetched():
    # The forward-evidence layer owns guidance and customer commitments.
    # This package never imports it, so the only way such a link reaches
    # a node is if a caller hands it over. On the benchmark corpus every
    # one of these is empty, which is a finding, not a gap.
    ev = salience(call((CEO, "Pat Lee", BUILD), quarter="2026Q2"))
    assert by_subject(ev, "data center").forward_links == ()


# ------------------------------------------------------------------- 11
def test_graph_linkage_is_reported_by_relation_and_is_not_a_ranking():
    ev = salience(call((CEO, "Pat Lee", DEPEND), quarter="2026Q2"))
    node = by_subject(ev, "components")
    assert node.graph_linkage.degree >= 1
    assert node.graph_linkage.by_relation
    # Degree is a field, never a verdict: no aggregate exists to hold one.
    assert not hasattr(node, "salience_score")
    assert not hasattr(node, "salience_label")


# ------------------------------------------------------------- 12,13,14
def test_continuity_travels_from_strategy_intelligence():
    ev = salience(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q4"),
        call((CEO, "Pat Lee", BUILD), quarter="2026Q1"),
    )
    assert by_subject(ev, "data center").continuity == "continuing"


def test_a_node_last_seen_before_the_latest_call_is_not_called_current():
    ev = salience(
        call((CEO, "Pat Lee", BUILD), quarter="2025Q4"),
        call((CEO, "Pat Lee", "We have allocated capital to the fleet."), quarter="2026Q2"),
    )
    stale = by_subject(ev, "data center")
    assert stale.latest_period == "2025Q4"
    assert stale.corpus_latest_period == "2026Q2"
    assert stale.is_current is False


def test_a_node_in_the_latest_call_is_marked_current():
    ev = salience(call((CEO, "Pat Lee", BUILD), quarter="2026Q2"))
    assert by_subject(ev, "data center").is_current is True


# ---------------------------------------------------------------- 15,16
def test_no_type_in_this_package_exposes_a_score_or_a_verdict():
    # Salience is not truth, not materiality and not conviction. The
    # check walks every public name on every type -- properties
    # included, since a score added as a property would be invisible to
    # a check over instance fields, which is exactly how the first
    # version of this test missed it.
    from atlas.analysis_engine.strategy_salience import models

    forbidden = ("confidence", "certainty", "conviction", "probability", "likelihood",
                 "score", "rank", "weight", "importance", "label", "central", "materiality")
    types = [getattr(models, name) for name in models.__all__]
    for type_ in types:
        for attribute in dir(type_):
            if attribute.startswith("_"):
                continue
            assert not any(word in attribute.lower() for word in forbidden), (
                f"{type_.__name__}.{attribute}"
            )


def test_no_field_combines_management_and_analyst_signals():
    from atlas.analysis_engine.strategy_salience import models

    fields = set(vars(SalienceEvidence("n", "C", "k", "s")))
    assert "speakers" in fields and "analyst_attention" in fields
    for type_ in (getattr(models, name) for name in models.__all__):
        for attribute in dir(type_):
            if attribute.startswith("_"):
                continue
            assert not any(word in attribute.lower() for word in ("total", "combined", "aggregate")), (
                f"{type_.__name__}.{attribute}"
            )


def test_the_management_filter_holds_even_if_a_node_cites_an_analyst_passage():
    # Extraction already refuses analyst statements, so this can only be
    # reached by a future change upstream. That is the point: the guard
    # is defence in depth, and a test that relies on extraction to hold
    # the line is not testing this layer at all.
    from atlas.analysis_engine.strategy import (
        EvidenceStatus, FactorClass, StrategyEvidence, StrategyNode, StrategyNodeKind,
    )
    from atlas.analysis_engine.strategy_salience.models import SalienceEvidence as _

    records = call(
        (CEO, "Pat Lee", BUILD),
        (ANALYST, "Chris Vale", "A question about data center capacity."),
        quarter="2026Q2",
    )
    analyst_record = records[1]
    node = StrategyNode(
        node_id="n1", company="VST", kind=StrategyNodeKind.INITIATIVE,
        status=EvidenceStatus.OBSERVED, factor=FactorClass.COMPUTE_CAPACITY,
        subject_text="data center",
        evidence=(
            StrategyEvidence(
                source_record_id=analyst_record.id,
                source_text="A question about data center capacity.",
                source_kind="transcript", company="VST", source_period="2026Q2",
                statement_at=None, speaker_title=ANALYST,
            ),
        ),
        observed_periods=("2026Q2",),
    )
    strategy = compose_company_strategy((), composed_at=COMPOSED_AT)
    strategy = type(strategy)(company="VST", nodes=(node,), edges=(), rejected=(), unknowns=())
    evidence = company_salience(strategy, records)[0]
    assert evidence.management_speaker_count == 0
    assert evidence.speakers == ()


def test_geography_is_excluded_from_analyst_attention():
    # GEOGRAPHIC_MARKET is a category, not a subject: Arizona and China
    # resolve to the same class. Matching analyst attention on it
    # credited an analyst asking about China as attention on AMAT's
    # Arizona facility, and reported eight analysts for a node nobody
    # had asked about.
    ev = salience(
        call(
            (CEO, "Pat Lee", "We are expanding our operations in Arizona."),
            (ANALYST, "Chris Vale", "What is happening with your business in China?"),
            quarter="2026Q2",
        )
    )
    geographic = [e for e in ev if "Arizona" in e.subject_text]
    assert geographic, [e.subject_text for e in ev]
    assert geographic[0].analyst_attention.analyst_count == 0


# ---------------------------------------------------------- prepared/Q&A
def test_prepared_remarks_and_qa_are_split_by_the_first_analyst_turn():
    # The analyst turn deliberately avoids the word "question", and a
    # management turn deliberately contains it. A boundary inferred from
    # wording would put the split in the wrong place; one derived from
    # the speaker's role puts it in the right one.
    ev = salience(
        call(
            (IR, "Dana Ito", "Welcome. We will take your questions shortly."),
            (CEO, "Pat Lee", BUILD),                       # prepared
            (ANALYST, "Chris Vale", "Thanks, and on capacity, how are you thinking about it?"),
            (CEO, "Pat Lee", "We are building data center capacity there too."),  # Q&A
            quarter="2026Q2",
        )
    )
    node = by_subject(ev, "data center")
    assert len(node.prepared_remark_refs) == 1
    assert len(node.qa_refs) == 1
    assert node.prepared_remark_refs[0].section is CallSection.PREPARED_REMARKS
    assert node.qa_refs[0].section is CallSection.QUESTION_AND_ANSWER


def test_a_call_with_no_analyst_has_no_section_boundary_to_find():
    # Reported as unknown rather than guessed. The boundary is a
    # structural fact about a call, and a call without one has none.
    ev = salience(call((CEO, "Pat Lee", BUILD), quarter="2026Q2"))
    node = by_subject(ev, "data center")
    assert node.prepared_remark_refs == ()
    assert all(r.section is CallSection.UNKNOWN for r in node.all_refs)


# ------------------------------------------------------ 17,18,19 + 20
def test_salience_is_deterministic_and_clock_independent():
    records = call((CEO, "Pat Lee", BUILD), (CFO, "Sam Ray", DEPEND), quarter="2026Q2")

    def shape(at):
        strategy = compose_company_strategy(records, composed_at=at)
        return [(e.node_id, e.period_count, e.management_speaker_count) for e in company_salience(strategy, records)]

    assert shape(COMPOSED_AT) == shape(COMPOSED_AT)
    assert shape(COMPOSED_AT) == shape(COMPOSED_AT + timedelta(days=400))


def test_salience_is_order_independent():
    records = call((CEO, "Pat Lee", BUILD), (CFO, "Sam Ray", DEPEND), quarter="2026Q2")
    forward = salience(records)
    backward = salience(tuple(reversed(records)))
    assert sorted(e.node_id for e in forward) == sorted(e.node_id for e in backward)
    assert sorted(e.management_speaker_count for e in forward) == sorted(
        e.management_speaker_count for e in backward
    )


def test_every_signal_carries_the_passage_it_was_counted_from():
    ev = salience(
        call(
            (CEO, "Pat Lee",
             "We are building additional data center capacity, and that is our top priority."),
            (ANALYST, "Chris Vale", "How much data center capacity?"),
            quarter="2026Q2",
        )
    )
    node = by_subject(ev, "data center")
    assert node.all_refs
    for ref in node.all_refs:
        assert ref.source_record_id
        assert ref.text
        assert ref.role is not None
    assert node.priority_language.refs[0].source_record_id
    assert node.analyst_attention.refs[0].speaker == "Chris Vale"


# ------------------------------------------------------------------- 26
def test_a_single_mention_is_not_dismissed():
    # One-off evidence keeps every signal it has. Nothing marks a
    # one-period node as peripheral, because there is no label to mark
    # it with -- which is the point of shipping signals rather than a
    # verdict.
    ev = salience(
        call(
            (CEO, "Pat Lee",
             "We are building additional data center capacity, and that is our top priority."),
            (ANALYST, "Chris Vale", "On data center capacity, what is the timeline?"),
            quarter="2026Q2",
        )
    )
    node = by_subject(ev, "data center")
    assert node.period_count == 1
    assert node.priority_language.count == 1
    assert node.analyst_attention.analyst_count == 1

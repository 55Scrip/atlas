"""Tests for `atlas.alpha.evidence_graph.engine` -- every node is built
from a real domain object constructed through its own real `.capture`/
`.register` factory (never hand-faked), the same discipline
`tests/unit/alpha/ingestion/test_engine.py` already established."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.evidence_graph.engine import (
    CRITICAL_DEPENDENCY_THRESHOLD,
    build_evidence_graph,
    compute_impact_summary,
    detect_weak_dependencies,
    downstream_impact,
    upstream_support,
)
from atlas.analysis_engine.investment_case_change import ChangeCategory, ChangeDirection, ChangeFinding
from atlas.alpha.evidence_graph.models import DependencyKind, GraphNodeKind, WeaknessKind
from atlas.analysis_engine.findings import Finding, FindingKind, FindingProducer, FindingSeverity
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.entity import CaseConditionView
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.assumption.entity import AssumptionView
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import Confidence, DecisionType, InvestmentCase, Subject, UserId
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.value_objects import Statement as EvidenceStatement
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement as ObservationStatement
from atlas.core.domain.observation.value_objects import Subject as ObservationSubject
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import Statement as OutcomeStatement
from atlas.decision_engine.contracts import EvidenceCoverageLevel

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
CASE_ID = CaseId()


def _observation(statement: str = "Revenue grew 20% YoY") -> Observation:
    return Observation.capture(
        case_id=CASE_ID,
        subject=ObservationSubject(value="NVDA"),
        statement=ObservationStatement(value=statement),
        observed_at=NOW,
    )


def _evidence(observation: Observation, direction: str = "SUPPORTS") -> Evidence:
    return Evidence.capture(
        observation_id=observation.id,
        statement=EvidenceStatement(value="Q2 filing confirms"),
        direction=direction,
        observed_at=NOW,
    )


def _decision(observation: Observation | None = None) -> Decision:
    return Decision.register(
        case_id=CASE_ID,
        user_id=UserId(value="investor-1"),
        decision_type=DecisionType.BUY,
        subject=Subject(value="NVDA"),
        investment_case=InvestmentCase(reason="Strong growth"),
        confidence=Confidence(value=80),
        observation_id=observation.id if observation is not None else None,
    )


def _outcome(decision: Decision) -> Outcome:
    return Outcome.capture(
        case_id=CASE_ID,
        decision_id=decision.id,
        statement=OutcomeStatement(value="Thesis played out"),
        occurred_at=NOW,
    )


def _case_condition(decision: Decision | None = None, status: str = "active") -> CaseConditionView:
    return CaseConditionView(
        condition_id=CaseConditionId(),
        case_id=CASE_ID,
        decision_id=decision.id if decision is not None else None,
        status=status,
        predicate_text="Capex growth decelerates below 10% YoY",
        role="thesis_risk",
        authorship=None,
        structured_kind=None,
        threshold_date=None,
        threshold_metric=None,
        threshold_operator=None,
        threshold_value=None,
        last_observed_value=None,
        superseded_by_condition_id=None,
        latest_event_id="event-1",
        created_at=NOW,
        updated_at=NOW,
    )


def _assumption(
    decision: Decision, *, linked_case_condition_ids: tuple[str, ...] = (), last_challenge_evidence_id: str | None = None
) -> AssumptionView:
    return AssumptionView(
        assumption_id=AssumptionId(),
        decision_id=decision.id,
        case_id=CASE_ID,
        status="challenged" if last_challenge_evidence_id is not None else "supported",
        statement="Data center demand stays strong",
        authorship=None,
        linked_case_condition_ids=linked_case_condition_ids,
        last_challenge_evidence_id=last_challenge_evidence_id,
        last_challenge_note=None,
        superseded_by_assumption_id=None,
        latest_event_id="event-1",
        created_at=NOW,
        updated_at=NOW,
    )


def _finding(
    finding_id: str,
    *,
    kind: FindingKind = FindingKind.BUSINESS_CATEGORY_ASSESSED,
    evidence_references: tuple[str, ...] = (),
    dependencies: tuple[str, ...] = (),
    details: dict | None = None,
) -> Finding:
    return Finding(
        id=finding_id,
        kind=kind,
        severity=FindingSeverity.INFO,
        details=details if details is not None else {},
        evidence_references=evidence_references,
        confidence=EvidenceCoverageLevel.FULL,
        producer=FindingProducer.BUSINESS_ANALYSIS,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=(),
            dependencies=dependencies,
            update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
            consumers=(Consumer.INVESTMENT_CASE_PAGE,),
            computed_at=NOW,
        ),
    )


def _empty_graph_kwargs(**overrides):
    base = dict(
        case_id=str(CASE_ID),
        observations=(),
        evidence=(),
        decisions=(),
        outcomes=(),
        case_conditions=(),
        assumptions=(),
        findings=(),
        generated_at=NOW,
    )
    base.update(overrides)
    return base


class TestBuildEvidenceGraphNodes:
    def test_builds_one_node_per_real_object(self):
        observation = _observation()
        evidence = _evidence(observation)
        decision = _decision(observation)
        outcome = _outcome(decision)
        condition = _case_condition(decision)
        assumption = _assumption(decision)
        finding = _finding("f1")

        graph = build_evidence_graph(
            **_empty_graph_kwargs(
                observations=(observation,),
                evidence=(evidence,),
                decisions=(decision,),
                outcomes=(outcome,),
                case_conditions=(condition,),
                assumptions=(assumption,),
                findings=(finding,),
            )
        )

        assert len(graph.nodes) == 7
        kinds = {n.kind for n in graph.nodes}
        assert kinds == {
            GraphNodeKind.OBSERVATION,
            GraphNodeKind.EVIDENCE,
            GraphNodeKind.DECISION,
            GraphNodeKind.OUTCOME,
            GraphNodeKind.CASE_CONDITION,
            GraphNodeKind.ASSUMPTION,
            GraphNodeKind.FINDING,
        }

    def test_never_duplicates_a_node_id(self):
        observation = _observation()
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation, observation)))
        assert len(graph.nodes) == 1

    def test_finding_details_are_forwarded_onto_the_node(self):
        """Sprint 12 (Analysis Coverage Expansion, Deliverable 6) --
        `Finding.details` is real, already-computed structured fact;
        this graph now surfaces it rather than discarding it."""
        finding = _finding("f1", details={"risk_category": "thesis_risk", "status": "low"})
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        node = graph.nodes[0]
        assert node.details["risk_category"] == "thesis_risk"
        assert node.details["status"] == "low"


class TestBuildEvidenceGraphEdges:
    def test_evidence_supports_observation_when_direction_is_supports(self):
        observation = _observation()
        evidence = _evidence(observation, direction="SUPPORTS")
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation,), evidence=(evidence,)))
        assert graph.edges == (
            type(graph.edges[0])(
                id=f"{evidence.id}:supports:{observation.id}",
                source_id=str(evidence.id),
                target_id=str(observation.id),
                kind=DependencyKind.SUPPORTS,
            ),
        )

    def test_evidence_contradicts_observation_when_direction_is_challenges(self):
        observation = _observation()
        evidence = _evidence(observation, direction="CHALLENGES")
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation,), evidence=(evidence,)))
        assert graph.edges[0].kind is DependencyKind.CONTRADICTS

    def test_decision_depends_on_observation_only_when_anchored(self):
        observation = _observation()
        anchored = _decision(observation)
        unanchored = _decision(None)
        graph = build_evidence_graph(
            **_empty_graph_kwargs(observations=(observation,), decisions=(anchored, unanchored))
        )
        depends_on_edges = [e for e in graph.edges if e.kind is DependencyKind.DEPENDS_ON]
        assert len(depends_on_edges) == 1
        assert depends_on_edges[0].source_id == str(anchored.id)

    def test_outcome_derived_from_decision(self):
        decision = _decision()
        outcome = _outcome(decision)
        graph = build_evidence_graph(**_empty_graph_kwargs(decisions=(decision,), outcomes=(outcome,)))
        assert graph.edges == (
            type(graph.edges[0])(
                id=f"{outcome.id}:derived_from:{decision.id}",
                source_id=str(outcome.id),
                target_id=str(decision.id),
                kind=DependencyKind.DERIVED_FROM,
            ),
        )

    def test_case_condition_depends_on_decision_only_when_anchored(self):
        decision = _decision()
        anchored = _case_condition(decision)
        unanchored = _case_condition(None)
        graph = build_evidence_graph(
            **_empty_graph_kwargs(decisions=(decision,), case_conditions=(anchored, unanchored))
        )
        assert len(graph.edges) == 1
        assert graph.edges[0].source_id == str(anchored.condition_id)

    def test_assumption_depends_on_decision(self):
        decision = _decision()
        assumption = _assumption(decision)
        graph = build_evidence_graph(**_empty_graph_kwargs(decisions=(decision,), assumptions=(assumption,)))
        assert graph.edges[0].kind is DependencyKind.DEPENDS_ON
        assert graph.edges[0].source_id == str(assumption.assumption_id)
        assert graph.edges[0].target_id == str(decision.id)

    def test_case_condition_feeds_linked_assumption(self):
        decision = _decision()
        condition = _case_condition(decision)
        assumption = _assumption(decision, linked_case_condition_ids=(str(condition.condition_id),))
        graph = build_evidence_graph(
            **_empty_graph_kwargs(decisions=(decision,), case_conditions=(condition,), assumptions=(assumption,))
        )
        feeds_edges = [e for e in graph.edges if e.kind is DependencyKind.FEEDS]
        assert len(feeds_edges) == 1
        assert feeds_edges[0].source_id == str(condition.condition_id)
        assert feeds_edges[0].target_id == str(assumption.assumption_id)

    def test_challenging_evidence_contradicts_assumption_when_it_resolves(self):
        observation = _observation()
        evidence = _evidence(observation, direction="CHALLENGES")
        decision = _decision()
        assumption = _assumption(decision, last_challenge_evidence_id=str(evidence.id))
        graph = build_evidence_graph(
            **_empty_graph_kwargs(
                observations=(observation,), evidence=(evidence,), decisions=(decision,), assumptions=(assumption,)
            )
        )
        contradicts_to_assumption = [
            e for e in graph.edges if e.kind is DependencyKind.CONTRADICTS and e.target_id == str(assumption.assumption_id)
        ]
        assert len(contradicts_to_assumption) == 1
        assert contradicts_to_assumption[0].source_id == str(evidence.id)

    def test_unresolvable_challenge_evidence_id_produces_no_edge(self):
        decision = _decision()
        assumption = _assumption(decision, last_challenge_evidence_id="not-a-real-evidence-id")
        graph = build_evidence_graph(**_empty_graph_kwargs(decisions=(decision,), assumptions=(assumption,)))
        assert all(e.kind is not DependencyKind.CONTRADICTS for e in graph.edges)

    def test_finding_depends_on_finding_via_provenance(self):
        upstream = _finding("evidence_coverage")
        downstream = _finding("conviction_assessed", dependencies=("evidence_coverage",))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(upstream, downstream)))
        assert graph.edges == (
            type(graph.edges[0])(
                id="conviction_assessed:depends_on:evidence_coverage",
                source_id="conviction_assessed",
                target_id="evidence_coverage",
                kind=DependencyKind.DEPENDS_ON,
            ),
        )

    def test_unresolvable_finding_dependency_produces_no_edge(self):
        finding = _finding("f1", dependencies=("some_other_finding_never_built",))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        assert graph.edges == ()

    def test_observation_supports_finding_via_evidence_reference(self):
        observation = _observation()
        finding = _finding("business_category_assessed:growth", evidence_references=(str(observation.id),))
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation,), findings=(finding,)))
        assert graph.edges[0].kind is DependencyKind.SUPPORTS
        assert graph.edges[0].source_id == str(observation.id)
        assert graph.edges[0].target_id == finding.id

    def test_contradicting_evidence_finding_kind_produces_contradicts_edge(self):
        observation = _observation()
        finding = _finding(
            f"{FindingKind.CONTRADICTING_EVIDENCE.value}:{observation.id}",
            kind=FindingKind.CONTRADICTING_EVIDENCE,
            evidence_references=(str(observation.id),),
        )
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation,), findings=(finding,)))
        assert graph.edges[0].kind is DependencyKind.CONTRADICTS

    def test_evidence_reference_to_a_business_fact_id_is_silently_skipped(self):
        finding = _finding("f1", evidence_references=("some-business-fact-id:revenue:2025",))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        assert graph.edges == ()


class TestDetectWeakDependencies:
    def test_finding_with_exactly_one_supporter_is_single_support(self):
        observation = _observation()
        finding = _finding("f1", evidence_references=(str(observation.id),))
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation,), findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert any(w.node_id == finding.id and w.kind is WeaknessKind.SINGLE_SUPPORT for w in weak)

    def test_finding_with_two_supporters_is_not_single_support(self):
        obs_a, obs_b = _observation("A"), _observation("B")
        finding = _finding("f1", evidence_references=(str(obs_a.id), str(obs_b.id)))
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(obs_a, obs_b), findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert not any(w.node_id == finding.id and w.kind is WeaknessKind.SINGLE_SUPPORT for w in weak)

    def test_finding_with_no_evidence_at_all_is_no_support(self):
        finding = _finding("f1")
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert any(w.node_id == finding.id and w.kind is WeaknessKind.NO_SUPPORT for w in weak)

    def test_a_finding_kind_that_is_never_expected_to_carry_evidence_is_never_no_support(self):
        """Live Verification finding (Deliverable 14) -- `CONVICTION_ASSESSED`
        is always constructed with `evidence_references=()` by
        `atlas.analysis_engine.pipeline`, so flagging it `NO_SUPPORT`
        would overstate a weakness that is structural, not real."""
        finding = _finding("conviction_assessed", kind=FindingKind.CONVICTION_ASSESSED)
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert not any(w.node_id == finding.id for w in weak if w.kind in (WeaknessKind.NO_SUPPORT, WeaknessKind.SINGLE_SUPPORT))

    def test_open_question_is_never_no_support(self):
        """Sprint 12 (Analysis Coverage Expansion, Deliverable 6) -- an
        open question already discloses its own gap by existing;
        flagging it `NO_SUPPORT` too double-counts the same fact."""
        finding = _finding("f1", kind=FindingKind.OPEN_QUESTION)
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert not any(w.node_id == finding.id for w in weak if w.kind in (WeaknessKind.NO_SUPPORT, WeaknessKind.SINGLE_SUPPORT))

    def test_thesis_risk_low_with_no_evidence_is_never_no_support(self):
        """Sprint 12 (Analysis Coverage Expansion, Deliverable 6) --
        audited against a real company (AAPL): `evaluate_thesis_risk`
        constructs `RiskStatus.LOW` ("checked, none contradicts") with
        `supporting_facts=()` unconditionally, by design."""
        finding = _finding(
            "risk_finding:thesis_risk",
            kind=FindingKind.RISK_CATEGORY_ASSESSED,
            details={"risk_category": "thesis_risk", "status": "low"},
        )
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert not any(w.node_id == finding.id for w in weak if w.kind in (WeaknessKind.NO_SUPPORT, WeaknessKind.SINGLE_SUPPORT))

    def test_thesis_risk_high_with_no_evidence_is_still_no_support(self):
        """The exclusion is narrowly scoped to `(thesis_risk, low)` --
        every other real `(risk_category, status)` combination for
        `risk_category_assessed` keeps the ordinary check."""
        finding = _finding(
            "risk_finding:thesis_risk",
            kind=FindingKind.RISK_CATEGORY_ASSESSED,
            details={"risk_category": "thesis_risk", "status": "high"},
        )
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert any(w.node_id == finding.id and w.kind is WeaknessKind.NO_SUPPORT for w in weak)

    def test_a_different_risk_category_with_no_evidence_is_still_no_support(self):
        finding = _finding(
            "risk_finding:business_risk",
            kind=FindingKind.RISK_CATEGORY_ASSESSED,
            details={"risk_category": "business_risk", "status": "low"},
        )
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert any(w.node_id == finding.id and w.kind is WeaknessKind.NO_SUPPORT for w in weak)

    def test_node_at_or_above_threshold_in_degree_is_critical_dependency(self):
        root = _finding("root")
        dependents = tuple(_finding(f"f{i}", dependencies=("root",)) for i in range(CRITICAL_DEPENDENCY_THRESHOLD))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(root,) + dependents))
        weak = detect_weak_dependencies(graph)
        assert any(w.node_id == "root" and w.kind is WeaknessKind.CRITICAL_DEPENDENCY for w in weak)

    def test_node_below_threshold_in_degree_is_not_critical_dependency(self):
        root = _finding("root")
        dependents = tuple(_finding(f"f{i}", dependencies=("root",)) for i in range(CRITICAL_DEPENDENCY_THRESHOLD - 1))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(root,) + dependents))
        weak = detect_weak_dependencies(graph)
        assert not any(w.node_id == "root" and w.kind is WeaknessKind.CRITICAL_DEPENDENCY for w in weak)

    def test_observation_never_used_by_a_decision_or_finding_is_isolated_chain(self):
        observation = _observation()
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation,)))
        weak = detect_weak_dependencies(graph)
        assert any(w.node_id == str(observation.id) and w.kind is WeaknessKind.ISOLATED_CHAIN for w in weak)

    def test_observation_used_by_a_decision_is_not_isolated_chain(self):
        observation = _observation()
        decision = _decision(observation)
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation,), decisions=(decision,)))
        weak = detect_weak_dependencies(graph)
        assert not any(w.node_id == str(observation.id) and w.kind is WeaknessKind.ISOLATED_CHAIN for w in weak)

    def test_a_finding_citing_only_an_unresolvable_business_fact_id_is_never_no_support(self):
        """Live Verification finding (Deliverable 14) -- a
        `business_category_assessed` Finding citing a real
        `BusinessFact` id (never a node in this graph) has real
        evidence; it must not be misclassified `NO_SUPPORT` just
        because that evidence isn't itself resolvable here."""
        finding = _finding("f1", evidence_references=("some-business-fact-id:revenue:2025",))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        weak = detect_weak_dependencies(graph)
        assert not any(w.node_id == finding.id and w.kind is WeaknessKind.NO_SUPPORT for w in weak)
        assert any(w.node_id == finding.id and w.kind is WeaknessKind.SINGLE_SUPPORT for w in weak)

    def test_observation_only_used_by_evidence_is_still_isolated_chain(self):
        observation = _observation()
        evidence = _evidence(observation)
        graph = build_evidence_graph(**_empty_graph_kwargs(observations=(observation,), evidence=(evidence,)))
        weak = detect_weak_dependencies(graph)
        assert any(w.node_id == str(observation.id) and w.kind is WeaknessKind.ISOLATED_CHAIN for w in weak)


def _change_finding(change_id: str, source_finding_id: str | None) -> ChangeFinding:
    return ChangeFinding(
        id=change_id,
        category=ChangeCategory.GROWTH_CHANGED,
        direction=ChangeDirection.NEGATIVE,
        previous_state="strong",
        current_state="moderate",
        details={"dimension": "growth"},
        evidence_references=(),
        source_finding_id=source_finding_id,
    )


class TestComputeImpactSummary:
    def test_a_change_with_downstream_findings_reports_their_count(self):
        root = _finding("root")
        dependent = _finding("dependent", dependencies=("root",))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(root, dependent)))
        change = _change_finding("change-1", source_finding_id="root")

        summary = compute_impact_summary(graph, (change,))
        assert len(summary) == 1
        assert summary[0].change_id == "change-1"
        assert summary[0].affected_finding_count == 1

    def test_a_change_with_no_downstream_findings_is_omitted(self):
        finding = _finding("f1")
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        change = _change_finding("change-1", source_finding_id="f1")

        assert compute_impact_summary(graph, (change,)) == ()

    def test_a_change_with_no_source_finding_id_is_omitted(self):
        finding = _finding("f1")
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        change = _change_finding("change-1", source_finding_id=None)

        assert compute_impact_summary(graph, (change,)) == ()

    def test_a_change_whose_source_finding_id_is_not_in_this_graph_is_omitted(self):
        finding = _finding("f1")
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        change = _change_finding("change-1", source_finding_id="never-built")

        assert compute_impact_summary(graph, (change,)) == ()


class TestTraversal:
    def test_downstream_impact_finds_transitive_dependents(self):
        root = _finding("root")
        mid = _finding("mid", dependencies=("root",))
        leaf = _finding("leaf", dependencies=("mid",))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(root, mid, leaf)))
        assert set(downstream_impact(graph, "root")) == {"mid", "leaf"}

    def test_upstream_support_finds_transitive_dependencies(self):
        root = _finding("root")
        mid = _finding("mid", dependencies=("root",))
        leaf = _finding("leaf", dependencies=("mid",))
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(root, mid, leaf)))
        assert set(upstream_support(graph, "leaf")) == {"mid", "root"}

    def test_downstream_impact_of_a_leaf_is_empty(self):
        finding = _finding("f1")
        graph = build_evidence_graph(**_empty_graph_kwargs(findings=(finding,)))
        assert downstream_impact(graph, "f1") == ()

"""Tests for `atlas.alpha.evidence_graph.portfolio.find_shared_weak_points`
-- pure, structural grouping over already-built graphs."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.evidence_graph.models import EvidenceGraph, GraphNode, GraphNodeKind, WeakDependency, WeaknessKind
from atlas.alpha.evidence_graph.portfolio import find_shared_weak_points
from atlas.alpha.evidence_graph.service import CaseEvidenceGraph

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _graph_with_assumption(case_id: str, statement: str, status: str = "challenged") -> CaseEvidenceGraph:
    node = GraphNode(
        id=f"assumption-{case_id}",
        kind=GraphNodeKind.ASSUMPTION,
        case_id=case_id,
        recorded_at=NOW,
        details={"statement": statement, "status": status},
    )
    graph = EvidenceGraph(case_id=case_id, generated_at=NOW, nodes=(node,), edges=())
    return CaseEvidenceGraph(graph=graph, weak_dependencies=())


def _graph_with_condition(case_id: str, predicate_text: str) -> CaseEvidenceGraph:
    node = GraphNode(
        id=f"condition-{case_id}",
        kind=GraphNodeKind.CASE_CONDITION,
        case_id=case_id,
        recorded_at=NOW,
        details={"predicate_text": predicate_text, "status": "active", "role": "thesis_risk"},
    )
    graph = EvidenceGraph(case_id=case_id, generated_at=NOW, nodes=(node,), edges=())
    return CaseEvidenceGraph(graph=graph, weak_dependencies=())


def _graph_with_no_support_finding(case_id: str, finding_kind: str) -> CaseEvidenceGraph:
    finding_id = f"finding-{case_id}"
    node = GraphNode(
        id=finding_id,
        kind=GraphNodeKind.FINDING,
        case_id=case_id,
        recorded_at=NOW,
        details={"kind": finding_kind, "severity": "info", "producer": "business_analysis"},
    )
    graph = EvidenceGraph(case_id=case_id, generated_at=NOW, nodes=(node,), edges=())
    weak = (WeakDependency(node_id=finding_id, kind=WeaknessKind.NO_SUPPORT, detail=0),)
    return CaseEvidenceGraph(graph=graph, weak_dependencies=weak)


class TestSharedWeakAssumptions:
    def test_two_holdings_with_the_same_challenged_assumption_are_grouped(self):
        graphs = {
            "case-a": _graph_with_assumption("case-a", "Demand stays strong"),
            "case-b": _graph_with_assumption("case-b", "Demand Stays Strong  "),
        }
        result = find_shared_weak_points(graphs, {"case-a": "NVDA", "case-b": "AMD"})
        assert len(result.shared_weak_assumptions) == 1
        point = result.shared_weak_assumptions[0]
        assert set(point.case_ids) == {"case-a", "case-b"}
        assert set(point.tickers) == {"NVDA", "AMD"}

    def test_a_single_holding_never_produces_a_shared_group(self):
        graphs = {"case-a": _graph_with_assumption("case-a", "Demand stays strong")}
        result = find_shared_weak_points(graphs, {"case-a": "NVDA"})
        assert result.shared_weak_assumptions == ()

    def test_a_supported_not_challenged_assumption_is_never_grouped(self):
        graphs = {
            "case-a": _graph_with_assumption("case-a", "Demand stays strong", status="supported"),
            "case-b": _graph_with_assumption("case-b", "Demand stays strong", status="supported"),
        }
        result = find_shared_weak_points(graphs, {"case-a": "NVDA", "case-b": "AMD"})
        assert result.shared_weak_assumptions == ()

    def test_different_statements_are_never_grouped_together(self):
        graphs = {
            "case-a": _graph_with_assumption("case-a", "Demand stays strong"),
            "case-b": _graph_with_assumption("case-b", "Margins hold up"),
        }
        result = find_shared_weak_points(graphs, {"case-a": "NVDA", "case-b": "AMD"})
        assert result.shared_weak_assumptions == ()


class TestSharedConditions:
    def test_two_holdings_with_the_same_condition_predicate_are_grouped(self):
        graphs = {
            "case-a": _graph_with_condition("case-a", "Capex growth decelerates below 10% YoY"),
            "case-b": _graph_with_condition("case-b", "Capex growth decelerates below 10% YoY"),
        }
        result = find_shared_weak_points(graphs, {"case-a": "NVDA", "case-b": "AMD"})
        assert len(result.shared_conditions) == 1
        assert set(result.shared_conditions[0].tickers) == {"NVDA", "AMD"}


class TestSharedMissingEvidence:
    def test_two_holdings_missing_the_same_finding_kind_are_grouped(self):
        graphs = {
            "case-a": _graph_with_no_support_finding("case-a", "valuation_method_assessed"),
            "case-b": _graph_with_no_support_finding("case-b", "valuation_method_assessed"),
        }
        result = find_shared_weak_points(graphs, {"case-a": "NVDA", "case-b": "AMD"})
        assert len(result.shared_missing_evidence) == 1
        assert result.shared_missing_evidence[0].signature == "valuation_method_assessed"

    def test_different_missing_finding_kinds_are_never_grouped_together(self):
        graphs = {
            "case-a": _graph_with_no_support_finding("case-a", "valuation_method_assessed"),
            "case-b": _graph_with_no_support_finding("case-b", "risk_category_assessed"),
        }
        result = find_shared_weak_points(graphs, {"case-a": "NVDA", "case-b": "AMD"})
        assert result.shared_missing_evidence == ()

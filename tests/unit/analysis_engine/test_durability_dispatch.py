"""Stage 3: `BusinessCategory.DURABILITY` is produced by the Core
evaluator inside real Business Analysis.

The point of these is the *wiring*, not the rule table -- `test_durability`
covers the rules. What can only fail here is the dispatch entry going
missing, durability acquiring a special path, or the Core/alpha boundary
being crossed to make it work.
"""
from __future__ import annotations

import ast
from pathlib import Path

from atlas.analysis_engine.business import BusinessCategory, evaluate_business_analysis
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as Status
from atlas.analysis_engine.provenance import SourceKind
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal


def _finding(result, category):
    return next(f for f in result.findings if f.kind is category)


def _analyse(**kwargs):
    _, output = run_minimal()
    return evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT, **kwargs)


class TestDispatch:
    def test_durability_is_produced_by_the_core_evaluator(self):
        """Fails if the dispatch entry is removed: only
        `evaluate_durability` produces these fact-specific gaps, the
        generic path reports `no_external_data_source_connected`."""
        durability = _finding(_analyse(), BusinessCategory.DURABILITY)
        gaps = {gap.value for gap in durability.missing_evidence}
        assert "no_external_data_source_connected" not in gaps
        assert {"missing_revenue_history", "missing_cash_flow_history"} <= gaps

    def test_durability_matches_the_isolated_evaluator_for_identical_facts(self):
        """No dispatch-specific semantics: routing through Business
        Analysis must not change what the evaluator would have said."""
        from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
        from atlas.analysis_engine.durability import evaluate_durability

        records = ()
        direct = evaluate_durability(
            extract_facts_from_records(records, evaluated_at=GENERATED_AT), evaluated_at=GENERATED_AT)
        dispatched = _finding(_analyse(business_records=records), BusinessCategory.DURABILITY)
        assert dispatched.status is direct.status
        assert dispatched.missing_evidence == direct.missing_evidence
        assert dispatched.confidence is direct.confidence

    def test_growth_and_capital_allocation_dispatch_are_unchanged(self):
        result = _analyse()
        for category in (BusinessCategory.GROWTH, BusinessCategory.CAPITAL_ALLOCATION):
            finding = _finding(result, category)
            assert finding.provenance.source_kind is SourceKind.ANALYSIS_ENGINE_STAGE
            assert finding.missing_evidence != ()

    def test_categories_without_an_evaluator_stay_insufficient(self):
        """Stage 3 activated exactly one category, not four."""
        result = _analyse()
        for category in (BusinessCategory.BUSINESS_MODEL, BusinessCategory.COMPETITIVE_POSITION,
                         BusinessCategory.MANAGEMENT):
            assert _finding(result, category).status is Status.INSUFFICIENT_INPUT

    def test_business_analysis_shape_is_unchanged(self):
        result = _analyse()
        assert len(result.findings) == len(BusinessCategory)
        assert {f.kind for f in result.findings} == set(BusinessCategory)

    def test_dispatch_is_deterministic(self):
        assert _analyse() == _analyse()

    def test_absent_facts_stay_honest(self):
        """A real evaluator must not manufacture a conclusion from
        nothing -- no facts is still INSUFFICIENT_INPUT, not WEAK."""
        assert _finding(_analyse(), BusinessCategory.DURABILITY).status is Status.INSUFFICIENT_INPUT


class TestBoundary:
    def test_neither_durability_nor_business_analysis_imports_alpha(self):
        """The Core -> alpha one-way boundary. Dispatch must not have
        required alpha's own BusinessDurability."""
        for path in ("atlas/analysis_engine/durability.py", "atlas/analysis_engine/business.py"):
            tree = ast.parse(Path(path).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith("atlas.alpha"), f"{path} imports {node.module}"
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith("atlas.alpha"), f"{path} imports {alias.name}"

    def test_durability_does_not_reach_direction(self):
        """Stage 3 is dispatch only: `select_direction` takes no
        durability parameter, so no Direction can depend on it yet."""
        import inspect

        from atlas.analysis_engine.direction_selector import select_direction

        assert "durability" not in inspect.signature(select_direction).parameters

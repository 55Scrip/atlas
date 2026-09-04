"""Structural boundary guards for the `DE-016` implementation sprint
(wiring `DE-015`'s `ValuationSupport` into Direction Selection).

Two guarantees this sprint must not disturb, proven directly against the
real module namespaces/signatures rather than asserted from memory:

1. Recommendation Conviction (`DE-004` §3) stays completely independent
   of `ValuationSupport` -- it is a Direction *prerequisite*, never
   Conviction evidence, a score, or a confidence multiplier (`DE-016`
   Phase 10).
2. The only new edge this sprint adds is `ValuationSupport.status` ->
   `select_direction` -- Outlook is not, and must not become, reachable
   from any Recommendation-side function (`DE-016` Phase 11; `DE-012`
   §9/§13, `DE-014` §16).
"""
from __future__ import annotations

import inspect

from atlas.analysis_engine.recommendation_conviction import calculate_recommendation_conviction
from atlas.analysis_engine.direction_selector import select_direction
from atlas.analysis_engine.recommendation import evaluate_recommendation_gate


class TestConvictionBoundary:
    def test_calculate_recommendation_conviction_has_no_valuation_support_parameter(self):
        params = inspect.signature(calculate_recommendation_conviction).parameters
        assert "valuation_support" not in params
        assert "valuation_support_status" not in params

    def test_recommendation_conviction_module_never_imports_valuation_support(self):
        import atlas.analysis_engine.recommendation_conviction as module

        assert not hasattr(module, "ValuationSupport")
        assert not hasattr(module, "ValuationSupportStatus")

    def test_recommendation_conviction_module_source_has_no_valuation_support_reference(self):
        import pathlib

        path = pathlib.Path(inspect.getfile(calculate_recommendation_conviction))
        source = path.read_text(encoding="utf-8")
        assert "ValuationSupport" not in source
        assert "valuation_support" not in source


class TestOutlookBoundary:
    def test_select_direction_has_no_outlook_parameter(self):
        params = inspect.signature(select_direction).parameters
        assert "outlook" not in params

    def test_evaluate_recommendation_gate_has_no_outlook_parameter(self):
        params = inspect.signature(evaluate_recommendation_gate).parameters
        assert "outlook" not in params

    def test_calculate_recommendation_conviction_has_no_outlook_parameter(self):
        params = inspect.signature(calculate_recommendation_conviction).parameters
        assert "outlook" not in params

    def test_direction_selector_module_never_imports_outlook(self):
        import atlas.analysis_engine.direction_selector as module

        assert not hasattr(module, "Outlook")
        assert not hasattr(module, "build_outlook")

    def test_recommendation_module_never_imports_outlook(self):
        import atlas.analysis_engine.recommendation as module

        assert not hasattr(module, "Outlook")
        assert not hasattr(module, "build_outlook")

    def test_direction_selector_source_has_no_real_outlook_import(self):
        """Real `import` statements only -- prose mentions of "Outlook"
        inside docstrings (e.g. explaining the sibling relationship) are
        expected and legitimate; only an executable import would be a
        boundary violation."""
        import pathlib

        path = pathlib.Path(inspect.getfile(select_direction))
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("from ") or stripped.startswith("import "):
                assert "outlook" not in stripped.lower()


class TestOnlyStatusCrossesTheNewEdge:
    """`DE-015` §18: Recommendation may consume only the public `status`
    field. Checked against the real, executable attribute-access
    patterns (never against raw docstring prose, which legitimately
    names `.reasoning`/`.gap` while explaining why they are avoided --
    the same "real namespace, not text" discipline
    `eligibility.py`'s own boundary test already established)."""

    def test_select_direction_never_reads_valuation_support_reasoning_or_gap(self):
        import pathlib

        path = pathlib.Path(inspect.getfile(select_direction))
        source = path.read_text(encoding="utf-8")
        assert "valuation_support.reasoning" not in source
        assert "valuation_support.gap" not in source
        assert "valuation_support_status.reasoning" not in source
        assert "valuation_support_status.gap" not in source

    def test_recommendation_module_never_reads_valuation_support_reasoning(self):
        """`reasoning` is diagnostic prose and never crosses.

        `gap` is no longer prohibited here: `DE-015` §18, amended under
        its own §22.7, permits it to cross for explanatory projection
        only. `select_direction` remains status-only -- asserted by the
        sibling test above, which is deliberately unchanged -- and the
        structural proof that the gate passes `gap` to nothing but the
        key-unknowns projection lives in
        `valuation/test_support.py::TestArchitecturalBoundary`.
        """
        import pathlib

        source = pathlib.Path(inspect.getfile(evaluate_recommendation_gate)).read_text(encoding="utf-8")
        assert "valuation_support.reasoning" not in source

"""Cross-module consistency test (Cleanup Sprint 1, Phase 5).

Seven capability modules each independently duplicate the identical
"later-half vs. earlier-half average, threshold-gated" trend algorithm
rather than importing a protected sibling's own private helper -- a
deliberate, disclosed pattern (see each module's own docstring). The
Consolidation Review found that one of the seven had silently drifted
its own minimum-periods gate (`historical_valuation.py` requires 4
observations; the other six require 3) while every module's own
docstring implies the algorithm is identical everywhere.

This test does not reconcile that drift -- Cleanup Sprint 1's own
non-goals forbid changing a threshold, since doing so changes real
classification output for real inputs, a product decision this sprint
is not authorized to make. Its job is narrower: turn the *known* drift
into one explicit, named exception, and fail loudly if any *further*
drift (in either the shared 0.1 threshold, wrongly assumed universal,
or a *second* minimum-periods mismatch) is ever introduced without
a matching update here.
"""
from __future__ import annotations

import importlib

import pytest

_MODULES_WITH_TREND_ALGORITHM = (
    "atlas.alpha.investment_case.financial_statement_intelligence",
    "atlas.alpha.investment_case.capital_allocation_intelligence",
    "atlas.alpha.investment_case.financial_quality_intelligence",
    "atlas.alpha.investment_case.growth_intelligence",
    "atlas.alpha.investment_case.historical_valuation",
    "atlas.alpha.investment_case.management_credibility_intelligence",
    "atlas.alpha.investment_case.management_guidance_intelligence",
)

#: The private module-level name each module gives its own
#: minimum-observations gate -- not identical across modules (naming
#: itself drifted too: `_MIN_PERIODS_FOR_TREND` vs.
#: `_MIN_OBSERVATIONS_FOR_TREND` vs. `_MIN_PERIODS_FOR_OUTCOME_TREND`),
#: so this test resolves whichever one each module actually defines
#: rather than assuming one shared name.
_MIN_PERIODS_CONSTANT_NAMES = (
    "_MIN_PERIODS_FOR_TREND", "_MIN_OBSERVATIONS_FOR_TREND", "_MIN_PERIODS_FOR_OUTCOME_TREND",
)

#: The one, currently-known, currently-undisclosed-reconciliation
#: exception: `historical_valuation.py` requires 4 periods before
#: classifying a trend; every other module requires 3. See the
#: Consolidation Review (Section 3a) for the full analysis. Reconciling
#: this is a product decision (it changes real classification output
#: for a real 3-period series), not cleanup -- out of scope here.
_KNOWN_MIN_PERIODS_EXCEPTIONS = {
    "atlas.alpha.investment_case.historical_valuation": 4,
}
_STANDARD_MIN_PERIODS = 3


def _min_periods_constant(module) -> tuple[str, int]:
    for name in _MIN_PERIODS_CONSTANT_NAMES:
        if hasattr(module, name):
            return name, getattr(module, name)
    raise AssertionError(
        f"{module.__name__} is listed as sharing the trend algorithm but defines none of "
        f"{_MIN_PERIODS_CONSTANT_NAMES} -- update this test's own constant-name list or module list."
    )


class TestTrendThresholdConsistency:
    """`_TREND_THRESHOLD` (the relative-change cutoff for RISING/FALLING
    vs. STABLE) has no known exception -- every module should agree."""

    def test_trend_threshold_is_identical_across_every_module(self):
        values: dict[str, float] = {}
        for module_name in _MODULES_WITH_TREND_ALGORITHM:
            module = importlib.import_module(module_name)
            values[module_name] = module._TREND_THRESHOLD

        distinct = set(values.values())
        assert distinct == {0.1}, (
            f"_TREND_THRESHOLD has drifted -- expected 0.1 everywhere, found: {values}"
        )


class TestMinimumPeriodsConsistency:
    """`historical_valuation.py`'s own 4-period gate is the one, known,
    currently-unreconciled exception -- everything else must agree."""

    def test_every_module_matches_the_standard_or_a_documented_exception(self):
        mismatches: dict[str, tuple[str, int]] = {}
        for module_name in _MODULES_WITH_TREND_ALGORITHM:
            module = importlib.import_module(module_name)
            constant_name, value = _min_periods_constant(module)
            expected = _KNOWN_MIN_PERIODS_EXCEPTIONS.get(module_name, _STANDARD_MIN_PERIODS)
            if value != expected:
                mismatches[module_name] = (constant_name, value)

        assert not mismatches, (
            "A minimum-periods constant does not match the standard (3) or a documented "
            f"exception in _KNOWN_MIN_PERIODS_EXCEPTIONS: {mismatches}. If this is a genuine, "
            "new, intentional exception, add it to _KNOWN_MIN_PERIODS_EXCEPTIONS with a reason "
            "-- if it is accidental drift, fix the module instead of this test."
        )

    def test_the_documented_exception_still_only_covers_historical_valuation(self):
        """Guards against the exception list quietly growing without
        review -- if a second module ever needs an exception, this
        test forces a human to look at it rather than the allowlist
        silently absorbing new drift."""
        assert _KNOWN_MIN_PERIODS_EXCEPTIONS == {
            "atlas.alpha.investment_case.historical_valuation": 4,
        }


@pytest.mark.parametrize("module_name", _MODULES_WITH_TREND_ALGORITHM)
def test_every_listed_module_actually_defines_a_trend_threshold(module_name):
    """Guards the module list itself: if a module is renamed or its
    constant is removed, this fails immediately rather than the two
    tests above silently iterating over fewer modules than intended."""
    module = importlib.import_module(module_name)
    assert hasattr(module, "_TREND_THRESHOLD"), f"{module_name} no longer defines _TREND_THRESHOLD"
    _min_periods_constant(module)  # raises AssertionError itself if missing


#: The two modules that independently bucket a coefficient-of-variation
#: into a "how stable" classification -- `financial_quality_
#: intelligence.StabilityLevel` and `historical_valuation.
#: ValuationStability` -- share the identical `0.15` "stable" cutoff
#: today (Consolidation Review, Section 3c). `financial_quality_
#: intelligence.py` additionally has its own `_MODERATE_VOLATILITY_
#: THRESHOLD` for a third tier the sibling doesn't have -- that is an
#: enum-shape difference, not a threshold drift, and reconciling it is
#: explicitly out of this sprint's scope ("do not change enums for
#: semantic reasons"). This test only guards the one number both
#: modules genuinely share.
_MODULES_WITH_VOLATILITY_THRESHOLD = (
    "atlas.alpha.investment_case.historical_valuation",
    "atlas.alpha.investment_case.financial_quality_intelligence",
)


def test_shared_stability_volatility_threshold_is_identical():
    values: dict[str, float] = {}
    for module_name in _MODULES_WITH_VOLATILITY_THRESHOLD:
        module = importlib.import_module(module_name)
        values[module_name] = module._VOLATILITY_THRESHOLD

    distinct = set(values.values())
    assert distinct == {0.15}, (
        f"_VOLATILITY_THRESHOLD has drifted -- expected 0.15 in both modules, found: {values}"
    )

"""Stance Engine (Atlas Intelligence Sprint 2 -- Recommendation Quality
& Actionability).

Answers "how favorable is Atlas's current view of this Case, and how
confident should the investor be in it" -- explicitly **not** a trade-
sizing engine. `StanceLevel.INCREASE`/`REDUCE` name the *direction* of
Atlas's view (strengthening/weakening), never a position-size
instruction; no member of this package's vocabulary is ever rendered
alongside a share count anywhere in the product. Actual buy/sell
sizing remains out of scope for this Sprint, explicitly deferred to a
future, dedicated portfolio-action sprint (per product direction).

This is a pure orchestration layer over already-real signals --
Conviction, Decision Support, Coverage & Confidence (Atlas Intelligence
Sprint 1), Change Intelligence, Portfolio Fit, and Risk -- never a
second analysis engine, never a second Decision Support, never a
second Portfolio Fit. See `engine.py`'s own module docstring for the
full derivation and gating rules.
"""
from __future__ import annotations

from .engine import compare_stance, determine_stance
from .models import (
    Stance,
    StanceComparison,
    StanceComparisonReason,
    StanceComparisonReasonCode,
    StanceLevel,
    StanceReason,
    StanceReasonCode,
)

__all__ = [
    "determine_stance",
    "compare_stance",
    "Stance",
    "StanceComparison",
    "StanceComparisonReason",
    "StanceComparisonReasonCode",
    "StanceLevel",
    "StanceReason",
    "StanceReasonCode",
]

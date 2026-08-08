"""Shared Portfolio Cockpit vocabulary (ATLAS-028 Phase 19/20) --
`AttentionReasonKind`, `ReviewPriority`. See `attention.py` for the
deterministic rule table that produces these; see this package's own
`__init__.py` for why nothing here is, or implies, a recommendation.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["AttentionReasonKind", "ReviewPriority"]


class AttentionReasonKind(str, Enum):
    """A closed, named set of real analytical/workflow signals --
    never a free-text reason. Each member traces back to exactly one
    already-computed canonical value; none is invented for this
    package."""

    HIGH_FINANCIAL_RISK = "high_financial_risk"
    """`risk_analysis`'s own `FINANCIAL_RISK` category is `HIGH`."""

    HIGH_VALUATION_RISK = "high_valuation_risk"
    """`risk_analysis`'s own `VALUATION_RISK` category is `HIGH`."""

    LOW_CONVICTION = "low_conviction"
    """`conviction.level` is `ConvictionLevel.LOW`."""

    CONTRADICTING_EVIDENCE = "contradicting_evidence"
    """`risk_analysis`'s own `THESIS_RISK` category is `HIGH` --
    unresolved contradicting evidence against the recorded thesis,
    reused verbatim, never a second contradiction scan."""

    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    """Case-wide `confidence` is `NOT_APPLICABLE` or `NONE`."""


class ReviewPriority(str, Enum):
    """Categorical, four levels, never numeric. Describes *where to
    look first*, never *what to do* -- `PRIORITY_REVIEW` is not a SELL
    signal, `NONE` is not a BUY signal. See `attention.py`'s own
    decision table for the exact, deterministic rule that assigns
    this."""

    NONE = "none"
    STANDARD_REVIEW = "standard_review"
    EVIDENCE_REVIEW = "evidence_review"
    PRIORITY_REVIEW = "priority_review"

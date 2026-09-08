"""What one Discovery candidate is, and why it qualified."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["CandidateExclusionReason", "DiscoveryCandidate"]


class CandidateExclusionReason(str, Enum):
    """Why a bound Case did not become a candidate. Reported rather
    than silently dropped, so the universe can be audited."""

    HELD_IN_PORTFOLIO = "held_in_portfolio"
    """Already owned. Portfolio shows its current state; presenting it
    as a new idea would be wrong."""

    ON_WATCHLIST = "on_watchlist"
    """Already explicitly monitored. Watchlist is where the investor
    tracks it, and echoing it back as a discovery is the exact defect
    this package replaces."""

    NO_ANALYSIS = "no_analysis"
    """Atlas has no company data for it. An idea it cannot say anything
    about is not one worth surfacing -- though Search can still reach
    it honestly."""

    NO_COMPOSITION = "no_composition"
    """The Case id does not resolve. Honest absence, never a guess."""


@dataclass(frozen=True)
class DiscoveryCandidate:
    """A security Atlas knows about that the investor is not following.

    Every field is a canonical categorical value read from the Case's
    own composition -- nothing is scored, weighted or combined here.
    `fit_rating` and `stance_level` are `None` when the underlying
    engine genuinely could not evaluate them, never defaulted to a
    neutral-looking value.
    """

    ticker: str
    case_id: str
    company_name: str | None
    decision_support_level: str
    analysis_coverage_level: str
    fit_rating: str | None
    stance_level: str | None

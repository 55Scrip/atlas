"""Wire format for the Discovery candidate universe.

Canonical enum values only, never rendered text -- the same discipline
the Watchlist summary follows, so one canonical state keeps one
investor-facing label across every surface. `fitRating` and
`stanceLevel` are nullable because "the engine could not evaluate this"
is a real answer that must not be dressed up as a middling one.

Deliberately absent: conviction, expected return, upside, downside and
any aggregate risk or opportunity score. Atlas computes none of those
concepts, and Discovery is not where they get invented.
"""
from __future__ import annotations

from atlas.alpha.discovery_candidates.models import DiscoveryCandidate
from atlas.core.infrastructure.api.serialization import CamelModel


class DiscoveryCandidateView(CamelModel):
    ticker: str
    case_id: str
    company_name: str | None
    decision_support_level: str
    analysis_coverage_level: str
    fit_rating: str | None
    stance_level: str | None

    @classmethod
    def from_domain(cls, candidate: DiscoveryCandidate) -> "DiscoveryCandidateView":
        return cls(
            ticker=candidate.ticker,
            case_id=candidate.case_id,
            company_name=candidate.company_name,
            decision_support_level=candidate.decision_support_level,
            analysis_coverage_level=candidate.analysis_coverage_level,
            fit_rating=candidate.fit_rating,
            stance_level=candidate.stance_level,
        )

"""HTTP schema for Security Discovery (Sprint 21). CamelCase via the
shared Core `CamelModel` (ADR-004). One view type -- discovery has no
request body, only a query string, and no envelope: the response is a
bare array, deliberately (Sprint 21 Phase 4): 0 candidates -> `[]`, 1
candidate -> `[one]`, N -> all N, unranked. No `confidence`/`score`/
`recommended` field exists anywhere in this schema -- see
`atlas.alpha.security_discovery.models.SecurityCandidate`'s own
docstring for why none is invented.
"""
from __future__ import annotations

from atlas.alpha.security_discovery.models import SecurityCandidate
from atlas.core.infrastructure.api.serialization import CamelModel


class SecurityCandidateView(CamelModel):
    ticker: str
    display_name: str
    cik: int | None
    discovery_method: str
    source: str
    status: str

    @classmethod
    def from_domain(cls, candidate: SecurityCandidate) -> "SecurityCandidateView":
        return cls(
            ticker=candidate.ticker,
            display_name=candidate.display_name,
            cik=candidate.cik,
            discovery_method=candidate.discovery_method,
            source=candidate.source,
            status=candidate.status,
        )

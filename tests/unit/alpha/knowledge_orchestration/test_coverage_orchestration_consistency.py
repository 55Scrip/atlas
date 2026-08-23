"""Cross-registry consistency test (Cleanup Sprint 1, Phase 5).

Knowledge Coverage (`atlas.alpha.knowledge_coverage.engine.
_DOMAIN_EXTRACTORS`) and Knowledge Orchestration (`atlas.alpha.
knowledge_orchestration.capability.DOMAIN_CRITICALITY`) are two
separate registries, in two separate packages, with no shared code
path forcing them to stay in sync -- each new capability sprint has
had to remember to update both by hand. The Consolidation Review
confirmed the two happen to agree exactly today (11 domains each), but
found nothing that would catch the two drifting apart in a future
sprint. This test is that guard.

It intentionally does *not* assert anything about which specific
domains are wired (that would make this a change-detector for every
future capability sprint, not a consistency guard) -- only that the two
registries' own key sets are identical to each other, whatever they are.
"""
from __future__ import annotations

from atlas.alpha.knowledge_coverage.engine import _DOMAIN_EXTRACTORS
from atlas.alpha.knowledge_orchestration.capability import DOMAIN_CRITICALITY


def test_every_domain_with_a_coverage_extractor_has_an_orchestration_criticality_entry():
    wired_in_coverage = set(_DOMAIN_EXTRACTORS)
    rated_in_orchestration = set(DOMAIN_CRITICALITY)
    missing_from_orchestration = wired_in_coverage - rated_in_orchestration
    assert not missing_from_orchestration, (
        f"Domain(s) wired in Knowledge Coverage but never rated in Knowledge Orchestration's "
        f"own DOMAIN_CRITICALITY: {missing_from_orchestration}. Every domain a Coverage extractor "
        f"can resolve should have an explicit CRITICAL/OPTIONAL opinion so Orchestration's own "
        f"acquisition planning can reason about it."
    )


def test_every_domain_with_an_orchestration_criticality_entry_has_a_coverage_extractor():
    wired_in_coverage = set(_DOMAIN_EXTRACTORS)
    rated_in_orchestration = set(DOMAIN_CRITICALITY)
    missing_from_coverage = rated_in_orchestration - wired_in_coverage
    assert not missing_from_coverage, (
        f"Domain(s) rated in Knowledge Orchestration's own DOMAIN_CRITICALITY but never wired "
        f"in Knowledge Coverage's own _DOMAIN_EXTRACTORS: {missing_from_coverage}. A criticality "
        f"opinion with no Coverage extractor to resolve it is a dangling registry entry."
    )

"""Forward-looking claim evidence (Stage 1).

Narrative source evidence -> `ForwardClaim` -> **nothing yet**. This
package is deliberately a leaf: no module in `analysis_engine`'s
analysis path or in `decision_engine` imports it, so a management
expectation cannot reach Growth, Capital Allocation, Valuation, FCF
Yield, Financial Risk, Outlook, Conviction or Recommendation. The
boundary is enforced by
`tests/unit/analysis_engine/forward_claims/test_integration_safety.py`,
not by convention.
"""
from atlas.analysis_engine.forward_claims.contracts import (
    ClaimBound,
    ClaimRejectionReason,
    ClaimSubject,
    ClaimType,
    ClaimantRole,
)
from atlas.analysis_engine.forward_claims.extraction import (
    EXTRACTOR_VERSION,
    RejectedCandidate,
    classify_claimant,
    extract_forward_claims,
)
from atlas.analysis_engine.forward_claims.models import ForwardClaim
from atlas.analysis_engine.forward_claims.revisions import (
    REVISION_ENGINE_VERSION,
    ClaimComparison,
    GuidanceRevision,
    NonRevisionReason,
    RevisionBasis,
    RevisionType,
    compare_claims,
    detect_revisions,
    group_claims,
)

__all__ = [
    "REVISION_ENGINE_VERSION",
    "ClaimBound",
    "ClaimComparison",
    "GuidanceRevision",
    "NonRevisionReason",
    "RevisionBasis",
    "RevisionType",
    "compare_claims",
    "detect_revisions",
    "group_claims",
    "ClaimRejectionReason",
    "ClaimSubject",
    "ClaimType",
    "ClaimantRole",
    "EXTRACTOR_VERSION",
    "ForwardClaim",
    "RejectedCandidate",
    "classify_claimant",
    "extract_forward_claims",
]

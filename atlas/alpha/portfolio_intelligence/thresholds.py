"""Shared, deterministic thresholds reused across Portfolio Intelligence
(ATLAS-016) and Case Intelligence (ATLAS-017).

Every value here already existed before being centralized -- moving them
to one importable location is the fix for "no duplicated logic," not a
new number invented for either sprint. See each constant's own comment
for its original source.
"""
from __future__ import annotations

from atlas.alpha.portfolio_status.models import AttentionCategory

# Reused directly from `atlas.domains.portfolio.calculations.concentration_level`
# -- not new numbers. `HIGH` mirrors that function's `>= 0.35` branch,
# `ELEVATED` its `>= 0.25` branch, both expressed on the 0-100 scale
# `AlphaHolding.weight_percent` already uses.
HIGH_CONCENTRATION_WEIGHT_PERCENT = 35.0
ELEVATED_CONCENTRATION_WEIGHT_PERCENT = 25.0

# Matches `frontend/src/routes/PortfolioPage.tsx`'s own
# `UNALLOCATED_TOLERANCE` -- the same threshold already used to decide
# whether to show an "Unallocated: X%" line, not a new number.
UNALLOCATED_TOLERANCE_PERCENT = 0.01

# The three `AttentionCategory` members (ATLAS-015) that represent an
# unfinished Decision/Outcome/Observation chain rather than a missing
# Case or a stale review -- reused verbatim by both
# `PortfolioIntelligenceService` (ATLAS-016) and `CaseIntelligenceService`
# (ATLAS-017) to derive `ConsiderKind.UPDATE_CASE`.
PENDING_WORKFLOW_CATEGORIES = frozenset(
    {
        AttentionCategory.DECISION_WITHOUT_OUTCOME,
        AttentionCategory.OUTCOME_WITHOUT_EXECUTION,
        AttentionCategory.OBSERVATION_WITHOUT_DECISION,
    }
)

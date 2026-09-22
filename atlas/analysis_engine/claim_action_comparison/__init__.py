"""Whether an observed action bears on a management claim. Shadow only."""
from atlas.analysis_engine.claim_action_comparison.contracts import (
    CLAIM_ACTION_COMPARISON_VERSION, REFUSAL_REASONS, ActionRef, ClaimActionComparison, ClaimRef,
    Compatibility, EntityBasis, Relation, TemporalRelation,
)
from atlas.analysis_engine.claim_action_comparison.comparison import compare, compare_many
from atlas.analysis_engine.claim_action_comparison.render import render_comparison

__all__ = ["CLAIM_ACTION_COMPARISON_VERSION", "REFUSAL_REASONS", "ActionRef",
           "ClaimActionComparison", "ClaimRef", "Compatibility", "EntityBasis", "Relation",
           "TemporalRelation", "compare", "compare_many", "render_comparison"]

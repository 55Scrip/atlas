"""Which source units a governing phrase introduces. Shadow only.

Layout, not meaning: nothing here says what a governing phrase means or what
its units are about, and nothing consumes it.
"""
from atlas.analysis_engine.structural_scope.contracts import (
    STRUCTURAL_SCOPE_VERSION, BoundaryKind, GovernedUnit, GovernedUnitKind, GovernorKind,
    SourceParagraph, SourceSpan, StructuralScopeEvidence,
)
from atlas.analysis_engine.structural_scope.reading import read_scopes

__all__ = ["STRUCTURAL_SCOPE_VERSION", "BoundaryKind", "GovernedUnit", "GovernedUnitKind",
           "GovernorKind", "SourceParagraph", "SourceSpan", "StructuralScopeEvidence",
           "read_scopes"]

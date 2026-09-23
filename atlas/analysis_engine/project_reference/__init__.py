"""What thing a claim or an action is about, in the source's own words.

A read model with no consumers. It deliberately exposes no way to ask whether
two references are the same project: the corpus holds no true pair against
which such an answer could be falsified.
"""
from atlas.analysis_engine.project_reference.contracts import (
    PROJECT_REFERENCE_VERSION, ProjectKind, ProjectReference, ReferenceProvenance, SourceRole,
)
from atlas.analysis_engine.project_reference.derivation import (
    references_from_action, references_from_claim,
)

__all__ = ["PROJECT_REFERENCE_VERSION", "ProjectKind", "ProjectReference",
           "ReferenceProvenance", "SourceRole", "references_from_action",
           "references_from_claim"]

"""Relationships a filing declares between the things it names. Shadow only.

Nothing here answers whether two references are the same project: the layer
below it preserves what each reference says, this layer preserves what the
source says about how they relate, and the identity question belongs to
neither.
"""
from atlas.analysis_engine.project_relationship.contracts import (
    PROJECT_RELATIONSHIP_VERSION, ContextForm, Direction, EndpointRole,
    ProjectRelationshipEvidence, RelationshipEndpoint, RelationshipKind, SourceParagraph,
    SourceSpan, StructuralContext,
)
from atlas.analysis_engine.project_relationship.reading import (
    read_relationships, relationships_from_enumerations,
)

__all__ = ["PROJECT_RELATIONSHIP_VERSION", "ContextForm", "Direction", "EndpointRole",
           "ProjectRelationshipEvidence", "RelationshipEndpoint", "RelationshipKind",
           "SourceParagraph", "SourceSpan", "StructuralContext", "read_relationships",
           "relationships_from_enumerations"]

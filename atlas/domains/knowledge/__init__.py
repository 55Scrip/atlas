"""Knowledge domain boundary.

Owns attributed facts, explicit relationships, and deterministic knowledge
queries.
"""

from atlas.shared import KnowledgeNode

from atlas.domains.knowledge.models import (
    KnowledgeCollection,
    KnowledgeEdge,
    KnowledgeFact,
    KnowledgeNodeType,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
)
from atlas.domains.knowledge.query import KnowledgeQueryService
from atlas.domains.knowledge.relationships import KnowledgeRelationshipEngine

__all__ = [
    "KnowledgeCollection",
    "KnowledgeEdge",
    "KnowledgeFact",
    "KnowledgeNode",
    "KnowledgeNodeType",
    "KnowledgeQueryService",
    "KnowledgeReference",
    "KnowledgeRelationship",
    "KnowledgeRelationshipEngine",
    "KnowledgeSource",
]

"""Knowledge Coverage Engine (Automatic Investment Case Builder
Foundation). See `engine.py`'s module docstring for the full design
rationale."""
from __future__ import annotations

from .engine import assess_knowledge_coverage
from .models import (
    DOMAIN_GROUP,
    InvestmentCaseKnowledgeCoverage,
    KnowledgeDomain,
    KnowledgeDomainCoverage,
    KnowledgeDomainGroup,
    MissingKnowledgeReason,
)

__all__ = [
    "assess_knowledge_coverage",
    "DOMAIN_GROUP",
    "InvestmentCaseKnowledgeCoverage",
    "KnowledgeDomain",
    "KnowledgeDomainCoverage",
    "KnowledgeDomainGroup",
    "MissingKnowledgeReason",
]

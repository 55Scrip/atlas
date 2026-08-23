"""The Knowledge Provider contract (Automatic Knowledge Ingestion
Framework, Phase 1).

A `KnowledgeProvider` is a `BusinessDataProvider` (`atlas.analysis_engine
.business_data.providers`) that additionally *declares itself* --
which `KnowledgeDomain`s it can populate, which `SourceKind`s it
produces, and a stable `provider_id` it owns rather than one the
caller derives from `type(provider).__name__`. `fetch()`'s own
signature is byte-identical to `BusinessDataProvider.fetch()` on
purpose: any real `KnowledgeProvider` structurally satisfies
`BusinessDataProvider` too (Python's `Protocol`/`isinstance` duck
typing), so it drops into `refresh_company_data`'s existing
per-provider loop, `get_default_business_data_providers()`'s tuple,
and `enrich_holdings` completely unmodified -- this contract adds
metadata, it never replaces the existing ingestion call path.

A concrete provider needs to implement exactly four things (three
declarative properties plus the one already-familiar `fetch` method)
to become a `KnowledgeProvider` -- "minimal implementation beyond the
provider contract," per this sprint's own Phase 1 instruction.
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["KnowledgeProvider"]


@runtime_checkable
class KnowledgeProvider(Protocol):
    @property
    def provider_id(self) -> str:
        """A stable, provider-owned identity -- never derived by a
        caller from the provider's own class name."""
        ...

    @property
    def supported_domains(self) -> tuple[KnowledgeDomain, ...]:
        """Every `KnowledgeDomain` this provider can, in principle,
        populate. Purely declarative -- a single run may still produce
        fewer documents than this promises (a real company may simply
        have nothing to report for one supported domain)."""
        ...

    @property
    def supported_source_kinds(self) -> tuple[SourceKind, ...]:
        """Every `SourceKind` this provider's own `fetch()` can tag a
        `RawBusinessDocument` with."""
        ...

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        """Byte-identical to `atlas.analysis_engine.business_data
        .providers.BusinessDataProvider.fetch` -- see that Protocol's
        own docstring for the full contract (raise a typed
        `atlas.business_data_providers.errors` exception on failure,
        never silently return `()` for an operational problem)."""
        ...

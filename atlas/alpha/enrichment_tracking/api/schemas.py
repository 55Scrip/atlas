"""HTTP response schema for the enrichment progress polling endpoint."""
from __future__ import annotations

from atlas.alpha.enrichment_tracking.models import EnrichmentProgressBatch
from atlas.core.infrastructure.api.serialization import CamelModel


class EnrichmentProgressView(CamelModel):
    exists: bool
    total: int = 0
    done_count: int = 0
    currently_analyzing: str | None = None
    complete: bool = True

    @classmethod
    def empty(cls) -> "EnrichmentProgressView":
        return cls(exists=False)

    @classmethod
    def from_domain(cls, batch: EnrichmentProgressBatch) -> "EnrichmentProgressView":
        return cls(
            exists=True,
            total=batch.total,
            done_count=batch.done_count,
            currently_analyzing=batch.currently_analyzing,
            complete=batch.complete,
        )

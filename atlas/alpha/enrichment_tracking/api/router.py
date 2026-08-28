"""REST controller for enrichment progress.

GET /enrichment-progress/{batch_id} - poll one batch's real state; a
                                       plain read of the progress table,
                                       nothing simulated.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.enrichment_tracking.api.dependencies import get_enrichment_progress_store
from atlas.alpha.enrichment_tracking.api.schemas import EnrichmentProgressView
from atlas.alpha.enrichment_tracking.store import EnrichmentProgressStore

router = APIRouter(prefix="/enrichment-progress", tags=["enrichment-progress"])


@router.get("/{batch_id}", response_model=EnrichmentProgressView)
def get_enrichment_progress(
    batch_id: str,
    store: EnrichmentProgressStore = Depends(get_enrichment_progress_store),
) -> EnrichmentProgressView:
    batch = store.get_batch(batch_id)
    if batch is None:
        return EnrichmentProgressView.empty()
    return EnrichmentProgressView.from_domain(batch)

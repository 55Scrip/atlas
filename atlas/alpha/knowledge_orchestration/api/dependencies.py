"""Composition wiring for the Knowledge Orchestration API. Reuses
every sibling package's own existing provider directly -- mirrors
`atlas.alpha.ingestion.api.dependencies`'s own convention exactly, no
second provider-construction path. Never imports `atlas.business_data
_providers` directly (that boundary is confined to `business_data_
refresh` alone, enforced by `tests/test_architecture_boundaries.py`).
"""
from __future__ import annotations

from atlas.alpha.business_data_refresh.api.dependencies import (
    get_business_record_repository,
    get_canonical_security_identity_gate,
    get_default_business_data_providers_by_id,
)

__all__ = [
    "get_business_record_repository",
    "get_canonical_security_identity_gate",
    "get_default_business_data_providers_by_id",
]

"""Composition wiring for security-level share-class evidence.

Unlike most Alpha stores, resolving this repository creates no table:
only the operator's backfill command writes these tables, and the read
path treats their absence as "no evidence" -- so serving a page never
changes the database's schema.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.canonical_security_gate.factory import build_listing_mic_reader
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_security_share_evidence_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemySecurityShareEvidenceRepository:
    return SqlAlchemySecurityShareEvidenceRepository(engine, listing_mics=build_listing_mic_reader(engine))

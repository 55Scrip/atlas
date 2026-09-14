"""Composition wiring for the issuer valuation basis (fiscal_epoch_v3).

Read-only: resolving it creates no table, and every read treats absent
evidence tables as "no evidence" -- serving a page never changes the
database's schema. One builder per request (its reader memoizes what it
reads within that request only).
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.issuer_equity.valuation_basis import IssuerValuationBasisBuilder
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_issuer_valuation_basis_builder(engine: Engine = Depends(get_decision_engine)) -> IssuerValuationBasisBuilder:
    return IssuerValuationBasisBuilder.from_engine(engine)

"""Composition wiring for the issuer valuation basis (fiscal_epoch_v3).

Read-only: resolving it creates no table, and every read treats absent
evidence tables as "no evidence" -- serving a page never changes the
database's schema. One builder per request (its reader memoizes what it
reads within that request only).
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import date

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.issuer_equity.reader import IssuerEquityReader
from atlas.alpha.issuer_equity.valuation_basis import IssuerValuationBasisBuilder
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

#: A security -> the other listed classes of its issuer a current valuation
#: must price on the same date (`IssuerEquityReader.listed_siblings`).
ListedSiblingResolver = Callable[[str, date], tuple[str, ...]]


def get_issuer_valuation_basis_builder(engine: Engine = Depends(get_decision_engine)) -> IssuerValuationBasisBuilder:
    return IssuerValuationBasisBuilder.from_engine(engine)


def get_listed_sibling_resolver(engine: Engine = Depends(get_decision_engine)) -> ListedSiblingResolver:
    """Resolved only when a price refresh actually runs, never on the page
    path: each call reads with a fresh reader, so a refresh sees the count
    evidence as it stands when it runs."""
    from atlas.alpha.canonical_security_gate.factory import build_listing_mic_reader

    def resolve(ticker: str, evaluated_on: date) -> tuple[str, ...]:
        return IssuerEquityReader(engine, listing_mics=build_listing_mic_reader(engine)).listed_siblings(ticker, evaluated_on)

    return resolve

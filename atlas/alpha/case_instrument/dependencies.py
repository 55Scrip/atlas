"""Composition wiring for the Case -> instrument binding.

One provider, reusing the shared Core engine like every other Alpha
dependencies module. `create_case_instrument_binding_table` is the same
create-or-safely-add call each Alpha store makes on resolution, so the
table appears on first use without a separate migration step -- the
convention `create_alpha_watchlist_entry_table` and
`create_business_record_table` already established.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.case_instrument.table import create_case_instrument_binding_table
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_case_instrument_binding_repository(
    engine: Engine = Depends(get_decision_engine),
) -> CaseInstrumentBindingRepository:
    create_case_instrument_binding_table(engine)
    return CaseInstrumentBindingRepository(engine)

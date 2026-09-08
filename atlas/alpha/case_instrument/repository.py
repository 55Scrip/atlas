"""Persistence for the Case -> operative-instrument binding.

Reads and writes rows. It resolves nothing, normalizes nothing and
calls no provider: establishing *which* instrument a ticker names is
the enrichment pipeline's job, and this table only records the answer
Atlas already acted on.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.case_instrument.exceptions import ConflictingCaseInstrumentBindingError
from atlas.alpha.case_instrument.models import CaseInstrumentBinding
from atlas.alpha.case_instrument.table import case_instrument_binding_table

__all__ = ["CaseInstrumentBindingRepository"]


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


class CaseInstrumentBindingRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def bind(self, binding: CaseInstrumentBinding) -> CaseInstrumentBinding:
        """Idempotent get-or-set for one Case.

        Re-binding a Case to the same instrument returns the existing
        row unchanged -- identity does not get a new timestamp for
        being asked about twice. Re-binding it to a *different*
        instrument raises: a Case is about one company, and quietly
        rewriting which one would move a thesis, its Decision history
        and its evidence onto a different security.
        """
        existing = self.get_by_case_id(binding.case_id)
        if existing is not None:
            if existing.instrument_key != binding.instrument_key:
                raise ConflictingCaseInstrumentBindingError(
                    f"Case {binding.case_id} is already bound to "
                    f"{existing.instrument_key!r}; refusing to rebind it to "
                    f"{binding.instrument_key!r}."
                )
            return existing

        with self._engine.begin() as connection:
            connection.execute(
                insert(case_instrument_binding_table).values(
                    case_id=binding.case_id,
                    instrument_key=binding.instrument_key,
                    bound_at=binding.bound_at.isoformat(),
                    canonical_security_id=binding.canonical_security_id,
                )
            )
        return binding

    def get_by_case_id(self, case_id: str) -> CaseInstrumentBinding | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(case_instrument_binding_table).where(
                    case_instrument_binding_table.c.case_id == case_id
                )
            ).mappings().first()
        return self._to_binding(row) if row is not None else None

    def get_by_instrument_key(self, instrument_key: str) -> CaseInstrumentBinding | None:
        """The Case already bound to this instrument, if any -- what
        makes `ensure_case_id` reuse rather than duplicate.

        `.first()` over a deterministic order rather than an assertion:
        the schema permits several rows per instrument (see `table.py`),
        so this reads the oldest binding, and `bind` is what keeps a
        second one from being written in the first place.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(case_instrument_binding_table)
                .where(case_instrument_binding_table.c.instrument_key == instrument_key)
                .order_by(case_instrument_binding_table.c.bound_at, case_instrument_binding_table.c.case_id)
            ).mappings().first()
        return self._to_binding(row) if row is not None else None

    def list_all(self) -> tuple[CaseInstrumentBinding, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(case_instrument_binding_table).order_by(
                    case_instrument_binding_table.c.instrument_key
                )
            ).mappings().all()
        return tuple(self._to_binding(row) for row in rows)

    def unbind(self, case_id: str) -> None:
        """Only for test/repair harnesses. Nothing in the product
        lifecycle removes a binding: neither leaving the Watchlist nor
        selling out of a position changes which company a Case was
        about.
        """
        with self._engine.begin() as connection:
            connection.execute(
                delete(case_instrument_binding_table).where(
                    case_instrument_binding_table.c.case_id == case_id
                )
            )

    @staticmethod
    def _to_binding(row) -> CaseInstrumentBinding:
        return CaseInstrumentBinding(
            case_id=row["case_id"],
            instrument_key=row["instrument_key"],
            bound_at=_parse(row["bound_at"]),
            canonical_security_id=row["canonical_security_id"],
        )

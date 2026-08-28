"""Persistence for learned name-to-ticker resolutions."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from atlas.alpha.portfolio_import.alias_table import resolved_alias_table
from atlas.alpha.portfolio_import.instrument_registry import normalize_for_lookup


class ResolvedAliasStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def lookup(self, name: str) -> str | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(resolved_alias_table.c.ticker).where(
                    resolved_alias_table.c.normalized_name == normalize_for_lookup(name)
                )
            ).first()
        return row[0] if row is not None else None

    def remember(self, name: str, ticker: str) -> None:
        normalized = normalize_for_lookup(name)
        if not normalized:
            return
        statement = sqlite_insert(resolved_alias_table).values(
            normalized_name=normalized,
            ticker=ticker.strip().upper(),
            learned_at=datetime.now(timezone.utc).isoformat(),
        )
        statement = statement.on_conflict_do_update(
            index_elements=[resolved_alias_table.c.normalized_name],
            set_={"ticker": statement.excluded.ticker, "learned_at": statement.excluded.learned_at},
        )
        with self._engine.begin() as connection:
            connection.execute(statement)

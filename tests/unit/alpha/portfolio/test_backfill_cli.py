"""Tests for `atlas.alpha.portfolio.cli.main` (ATLAS-029, Phase 45) --
the thin CLI wrapper around `backfill_missing_portfolio_cases`, exercised
end to end against an isolated in-memory engine (never the real
`atlas.db` file)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio.cli import main
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, EntryMode
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime.now(timezone.utc)


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    return engine


class TestCliMain:
    def test_returns_zero_and_no_failures_for_a_clean_run(self, capsys):
        engine = _new_engine()
        create_alpha_portfolio_state_table(engine)
        AlphaPortfolioStore(engine).replace(
            AlphaPortfolioState(
                established_at=_NOW,
                updated_at=_NOW,
                entry_mode=EntryMode.IMPORTED,
                holdings=(
                    AlphaHolding(ticker="AMD", weight_percent=50.0, case_id=None),
                    AlphaHolding(ticker="NVDA", weight_percent=50.0, case_id=None),
                ),
            )
        )

        exit_code = main(engine)
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Holdings scanned:    2" in captured.out
        assert "Cases created:       2" in captured.out
        assert "Failures:            0" in captured.out

    def test_creates_the_table_on_a_fresh_engine_without_error(self):
        """The CLI is often the very first thing to touch the Alpha
        portfolio table in a given process -- `main` must create it
        itself rather than assume some other code path already did."""
        engine = _new_engine()
        exit_code = main(engine)
        assert exit_code == 0

    def test_rerun_is_idempotent_through_the_cli_too(self, capsys):
        engine = _new_engine()
        create_alpha_portfolio_state_table(engine)
        AlphaPortfolioStore(engine).replace(
            AlphaPortfolioState(
                established_at=_NOW,
                updated_at=_NOW,
                entry_mode=EntryMode.IMPORTED,
                holdings=(AlphaHolding(ticker="AMD", weight_percent=100.0, case_id=None),),
            )
        )
        main(engine)
        capsys.readouterr()

        exit_code = main(engine)
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Cases created:       0" in captured.out
        assert "Cases preserved:     1" in captured.out

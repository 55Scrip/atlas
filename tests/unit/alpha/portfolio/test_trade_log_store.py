"""Tests for `atlas.alpha.portfolio.trade_log_store.AlphaTradeLogStore`."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio.models import AlphaTradeLogEntry, TransactionType
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table

_NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


@pytest.fixture
def store() -> AlphaTradeLogStore:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_alpha_trade_log_table(engine)
    return AlphaTradeLogStore(engine)


def _entry(**overrides) -> AlphaTradeLogEntry:
    defaults = dict(
        outcome_id="outcome-1",
        decision_id="decision-1",
        security="NVDA",
        transaction_type=TransactionType.BUY,
        quantity=10.0,
        execution_price=118.5,
        executed_at=_NOW,
        fees=1.2,
    )
    defaults.update(overrides)
    return AlphaTradeLogEntry(**defaults)


class TestAlphaTradeLogStore:
    def test_get_by_outcome_id_returns_none_when_absent(self, store):
        assert store.get_by_outcome_id("missing") is None

    def test_add_then_get_round_trips(self, store):
        store.add(_entry())
        fetched = store.get_by_outcome_id("outcome-1")
        assert fetched.security == "NVDA"
        assert fetched.transaction_type == TransactionType.BUY
        assert fetched.quantity == 10.0
        assert fetched.execution_price == 118.5
        assert fetched.fees == 1.2
        assert fetched.executed_at == _NOW

    def test_fees_is_optional_and_round_trips_as_none(self, store):
        store.add(_entry(outcome_id="outcome-2", fees=None))
        fetched = store.get_by_outcome_id("outcome-2")
        assert fetched.fees is None

    def test_list_all_returns_every_entry_in_executed_at_order(self, store):
        later = _NOW.replace(year=2027)
        store.add(_entry(outcome_id="outcome-2", executed_at=later))
        store.add(_entry(outcome_id="outcome-1", executed_at=_NOW))

        entries = store.list_all()
        assert [entry.outcome_id for entry in entries] == ["outcome-1", "outcome-2"]

    def test_sell_transaction_type_round_trips(self, store):
        store.add(_entry(transaction_type=TransactionType.SELL))
        fetched = store.get_by_outcome_id("outcome-1")
        assert fetched.transaction_type == TransactionType.SELL

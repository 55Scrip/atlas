"""Tests for `atlas.alpha.portfolio_import.alias_store.ResolvedAliasStore`."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio_import.alias_store import ResolvedAliasStore
from atlas.alpha.portfolio_import.alias_table import create_resolved_alias_table


@pytest.fixture
def store() -> ResolvedAliasStore:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_resolved_alias_table(engine)
    return ResolvedAliasStore(engine)


class TestLookup:
    def test_a_name_never_remembered_returns_none(self, store: ResolvedAliasStore):
        assert store.lookup("Zelkova Materials Group") is None

    def test_a_remembered_name_is_found_by_lookup(self, store: ResolvedAliasStore):
        store.remember("Zelkova Materials Group", "ZKVA")
        assert store.lookup("Zelkova Materials Group") == "ZKVA"

    def test_lookup_is_normalized_like_the_instrument_registry(self, store: ResolvedAliasStore):
        store.remember("Zelkova Materials Group", "ZKVA")
        assert store.lookup("  zelkova   materials, group.  ") == "ZKVA"


class TestRemember:
    def test_remembering_the_same_name_again_overwrites_the_ticker(self, store: ResolvedAliasStore):
        store.remember("Zelkova Materials Group", "ZKVA")
        store.remember("Zelkova Materials Group", "ZKVB")
        assert store.lookup("Zelkova Materials Group") == "ZKVB"

    def test_a_stored_ticker_is_upper_cased(self, store: ResolvedAliasStore):
        store.remember("Zelkova Materials Group", "zkva")
        assert store.lookup("Zelkova Materials Group") == "ZKVA"

    def test_a_blank_name_is_silently_ignored(self, store: ResolvedAliasStore):
        store.remember("   ", "ZKVA")
        assert store.lookup("   ") is None

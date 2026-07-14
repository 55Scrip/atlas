"""Tests for the InvestorIdentity domain fact (ATLAS-009B)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from atlas.core.domain.investor_identity.entity import InvestorIdentity


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestInvestorIdentityRegister:
    def test_assigns_a_user_id(self):
        identity = InvestorIdentity.register()
        assert identity.user_id is not None

    def test_assigns_a_fresh_user_id_each_call(self):
        first = InvestorIdentity.register()
        second = InvestorIdentity.register()
        assert first.user_id != second.user_id

    def test_established_at_comes_from_the_clock(self):
        now = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc)
        identity = InvestorIdentity.register(clock=_fixed_clock(now))
        assert identity.established_at == now

    def test_is_immutable(self):
        identity = InvestorIdentity.register()
        with pytest.raises(dataclasses.FrozenInstanceError):
            identity.established_at = datetime.now(timezone.utc)  # type: ignore[misc]

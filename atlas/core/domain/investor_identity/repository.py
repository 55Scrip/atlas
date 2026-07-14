"""Repository interface for InvestorIdentity.

Exactly one method, matching the one real operation this capability
performs. There is no separate `get`/`add` pair: nothing ever needs to
read the identity without the atomic first-use reconciliation guarantee,
and nothing ever needs to create it without first checking whether it
already exists. `resolve` is that single, caller-facing verb.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from atlas.core.domain.decision.value_objects import UserId


class InvestorIdentityRepository(Protocol):
    def resolve(self, clock: Callable[[], datetime] = ...) -> UserId:
        """Resolve this store's single durable Investor Identity.

        On first use, atomically establishes a new InvestorIdentity and
        reconciles every existing Decision's `user_id` to it. On every
        later call, returns the same value already established —
        idempotent, regardless of caller.
        """
        ...

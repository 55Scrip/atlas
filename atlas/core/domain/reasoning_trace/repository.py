"""Repository interface for the Reasoning Trace aggregate.

Insert-only: no update, no delete, matching every other aggregate in
this codebase. No `list_all`: nothing within DO-IMP-009's approved
scope needs to enumerate every Reasoning Trace yet.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId


class ReasoningTraceRepository(Protocol):
    def add(self, reasoning_trace: ReasoningTrace) -> None:
        """Insert a new Reasoning Trace."""
        ...

    def get(self, reasoning_trace_id: ReasoningTraceId) -> ReasoningTrace | None:
        """Return a single Reasoning Trace by id, or None if it does not exist."""
        ...

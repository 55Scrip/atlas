"""Scheduled Case composition -- see `service.py` for the full rationale.

Atlas accumulates its own decision history only when Cases are composed. This
package walks the Cases the investor holds or watches so that record builds
itself, without anyone opening twenty-six pages by hand and without asking any
provider for anything.

`factory` is deliberately not re-exported here: it wires the whole
composition object graph, and importing this package should not drag that in.
"""
from atlas.alpha.scheduled_composition.cadence import (
    DEFAULT_INTERVAL_SECONDS,
    configured_interval,
    is_due,
)
from atlas.alpha.scheduled_composition.service import (
    CaseCompositionOutcome,
    ScheduledCompositionResult,
    ScheduledCompositionService,
    scheduled_scope,
)

__all__ = [
    "CaseCompositionOutcome",
    "DEFAULT_INTERVAL_SECONDS",
    "ScheduledCompositionResult",
    "ScheduledCompositionService",
    "configured_interval",
    "is_due",
    "scheduled_scope",
]

"""The Reasoning Trace aggregate root (DO-IMP-009).

Reasoning Trace records exactly one semantic fact (OE-002 §5.3): within
a Case, an accepted Reasoning Trace records that one or more specified,
already-accepted, same-Case Domain Objects provide epistemic support
for the Reasoning Trace itself. It does not assert a stepwise process,
chronology, narrative rationale, execution telemetry, truth, validity,
reliability, completeness, or proof of another proposition — see
docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Sections 8 and 14.

Unlike Knowledge Reference (exactly one target, INV-014), Reasoning
Trace's supporting-object collection is "one or more" (INV-013) — a
`frozenset[TypedDomainObjectReference]`, never empty. Because a
collection field does not structurally guarantee non-emptiness the way
Knowledge Reference's single scalar `target` field guarantees "exactly
one," `__post_init__` enforces INV-013 directly, on every construction
path (both `.capture()` and ordinary persistence reconstruction —
Design Section 30).

Reasoning Trace is not root-eligible (OE-002 §5.3, INV-012): since its
supports collection is always required and non-empty, this is
structurally guaranteed by construction — there is no code path that
omits it.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.reasoning_trace.exceptions import EmptySupportError
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ReasoningTrace:
    """A single, immutable record that one or more supporting Domain
    Objects provide epistemic support for this Reasoning Trace itself.

    Valid only if it carries an id, the Case it belongs to, a non-empty
    set of typed supporting-object references, and the moment Atlas
    recorded it.
    """

    id: ReasoningTraceId
    case_id: CaseId
    supports: frozenset[TypedDomainObjectReference]
    recorded_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "supports", frozenset(self.supports))
        if len(self.supports) == 0:
            raise EmptySupportError(
                "A Reasoning Trace requires at least one supporting Domain Object (INV-013)"
            )

    @classmethod
    def capture(
        cls,
        *,
        case_id: CaseId,
        supports: Iterable[TypedDomainObjectReference],
        clock: _Clock = _utc_now,
    ) -> ReasoningTrace:
        """Capture a brand-new Reasoning Trace.

        This is the only path that assigns identity and `recorded_at`.
        Whether each entry in `supports` refers to an already-accepted,
        same-Case Domain Object (INV-004, INV-005) is an application-
        layer concern, verified before this classmethod is called — see
        `atlas/core/application/reasoning_trace/
        capture_reasoning_trace.py`.
        """
        return cls(
            id=ReasoningTraceId(),
            case_id=case_id,
            supports=frozenset(supports),
            recorded_at=clock(),
        )

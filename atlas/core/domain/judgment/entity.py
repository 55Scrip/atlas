"""The Judgment aggregate root (DO-IMP-004).

Judgment records the Case's settled, Case-relative characterization of
an identified subject, without asserting that the characterization is
objectively true (OE-002 §5.4). The subject may be realized either as
content held internally within `characterization` itself
(internal-content form, `subject` is `None`) or as a reference to
another same-Case, already-accepted Domain Object (referential form,
`subject` populated) — both forms are independently valid, and
`characterization` is required in either case (Judgment-Implementation-Design.md
Section 11: without it, the object collapses into Knowledge Reference).

Root eligibility (INV-012) requires no separate check: the internal-content
form (`subject is None`) is unconditionally permitted to be first in a
Case; the referential form can never be first, because INV-005 already
requires its subject to be an already-accepted, same-Case object —
which itself entails at least one prior Domain Object in that Case.

Self-reference and cycles are structurally impossible for the identical
reason already established for Knowledge Reference and Reasoning Trace:
`JudgmentId()` is generated inside `capture()` only after
`JudgmentService._verify_subject()` has already completed, so a caller
cannot supply, as a subject target id, the identity of an object that
does not yet exist.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.judgment.exceptions import JudgmentError
from atlas.core.domain.judgment.value_objects import Characterization, JudgmentId
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_subject(
    subject: TypedDomainObjectReference | None,
) -> TypedDomainObjectReference | None:
    if subject is not None and not isinstance(subject, TypedDomainObjectReference):
        raise JudgmentError(
            f"Judgment.subject must be a TypedDomainObjectReference or None, "
            f"got {type(subject).__name__}"
        )
    return subject


@dataclass(frozen=True)
class Judgment:
    """A single, immutable Case characterization.

    Valid only if it carries an id, the Case it belongs to, a
    non-empty characterization, and the moment Atlas recorded it. The
    subject reference is optional — present only for the referential
    form — and, when present, is a fully-formed typed pointer, never a
    partially populated pair.
    """

    id: JudgmentId
    case_id: CaseId
    characterization: Characterization
    recorded_at: datetime
    subject: TypedDomainObjectReference | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject", _validated_subject(self.subject))

    @classmethod
    def capture(
        cls,
        *,
        case_id: CaseId,
        characterization: Characterization,
        subject: TypedDomainObjectReference | None = None,
        clock: _Clock = _utc_now,
    ) -> Judgment:
        """Capture a brand-new Judgment.

        This is the only path that assigns identity and `recorded_at`.
        Whether `subject` (when present) refers to an already-accepted,
        same-Case Domain Object (INV-004, INV-005) is an
        application-layer concern, verified before this classmethod is
        called — see `atlas/core/application/judgment/capture_judgment.py`.
        """
        return cls(
            id=JudgmentId(),
            case_id=case_id,
            characterization=characterization,
            recorded_at=clock(),
            subject=subject,
        )

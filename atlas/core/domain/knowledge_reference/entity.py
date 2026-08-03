"""The Knowledge Reference aggregate root (DO-IMP-003).

Knowledge Reference records exactly one semantic fact (OE-002 §5.2):
within a Case, an accepted Knowledge Reference records that the Case
relies upon one accepted target Domain Object as knowledge for its own
purposes, without asserting that the referenced object's content is
true, verified, reliable, authoritative, or externally correct. It does
not evaluate truth, quality, confidence, or authority; does not explain
reasoning; does not record chronology; and does not perform inference.

Unlike Judgment, Decision, and Outcome, Knowledge Reference has no
internal-content alternative form — OE-002 §5.2 names only the
referential form ("identifies another permanent Domain Object"), with
no "content held internally" clause. Its target is therefore always
required, never nullable, and "exactly one" (INV-014) follows directly
from `target` being a single `TypedDomainObjectReference` field, not a
collection — no additional cardinality constraint is needed.

Knowledge Reference is not root-eligible (OE-002 §5.2, INV-012): since
its target is always required, this is structurally guaranteed by
construction — there is no code path that omits it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class KnowledgeReference:
    """A single, immutable record of the Case's reliance on one target
    Domain Object as knowledge.

    Valid only if it carries an id, the Case it belongs to, exactly one
    typed target reference, and the moment Atlas recorded it.
    """

    id: KnowledgeReferenceId
    case_id: CaseId
    target: TypedDomainObjectReference
    recorded_at: datetime

    @classmethod
    def capture(
        cls,
        *,
        case_id: CaseId,
        target: TypedDomainObjectReference,
        clock: _Clock = _utc_now,
    ) -> KnowledgeReference:
        """Capture a brand-new Knowledge Reference.

        This is the only path that assigns identity and `recorded_at`.
        Whether `target` refers to an already-accepted, same-Case
        Domain Object (INV-004, INV-005) is an application-layer
        concern, verified before this classmethod is called — see
        `atlas/core/application/knowledge_reference/
        capture_knowledge_reference.py`.
        """
        return cls(
            id=KnowledgeReferenceId(),
            case_id=case_id,
            target=target,
            recorded_at=clock(),
        )

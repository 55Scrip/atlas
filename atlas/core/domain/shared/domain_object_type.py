"""The closed set of adopted Domain Object types (DO-IMP-002).

This enum represents exactly OE-002 §4's own closed Domain Object Set —
Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision,
and Outcome — which is also, under OE-002's own text (§3, §5.1, §6),
the closed set of valid typed-reference targets, since OE-002 defines
reference eligibility as a property of being "a Domain Object" (§3)
with no separate, independently-scoped reference-target set ever
defined. See
docs/atlas_domain_object_architecture/Domain-Object-Type-Set-Discrepancy-Investigation.md
for the full analysis distinguishing these two concepts and confirming
they coincide today.

**Case is deliberately excluded.** OE-002 §3.1 defines Case separately,
as the ownership boundary underlying the Domain Object Set, not as a
member of the §4 enumeration — Case does not itself "belong to exactly
one Case" the way every Domain Object does (§3), so it is not, and
under the current architecture cannot be, a reference target: doing so
would require applying INV-004's same-Case rule to Case itself, which
is undefined. Case's own committed aggregate implementation
(`atlas/core/domain/case/`, DO-IMP-001) is unaffected by this: it
implements only Case's ownership-boundary role and was never reference-
eligible in the first place.

No alias, no legacy-term mapping, no runtime registration mechanism,
and no dependency on any API framework type exists here. Parsing an
unrecognized value raises UnknownDomainObjectTypeError rather than
silently accepting it or coercing it.
"""
from __future__ import annotations

from enum import Enum

from atlas.core.domain.shared.exceptions import UnknownDomainObjectTypeError


class DomainObjectType(str, Enum):
    """One of the six adopted Domain Objects, admitted as a reference target.

    Values are stable, canonical, PascalCase strings — matching this
    codebase's own precedent for multi-word enum values (e.g.
    `DecisionSource.BROKER_SYNC = "BrokerSync"`, atlas/core/domain/
    decision/value_objects.py) — and are exactly what is stored,
    serialized, and parsed; there is no separate wire-format mapping.
    """

    OBSERVATION = "Observation"
    KNOWLEDGE_REFERENCE = "KnowledgeReference"
    REASONING_TRACE = "ReasoningTrace"
    JUDGMENT = "Judgment"
    DECISION = "Decision"
    OUTCOME = "Outcome"

    @classmethod
    def parse(cls, value: str) -> DomainObjectType:
        """Parse a canonical string into a DomainObjectType.

        Raises UnknownDomainObjectTypeError for anything outside the six
        adopted values — never returns a partial match, never coerces a
        legacy or rejected term (Reasoning Act, Candidate, Hypothesis,
        Evaluation, Learning, Evidence, Case, Question, Interpretation,
        Conclusion, reasoning_link, or any arbitrary string), and never
        accepts an unrecognized future value.
        """
        try:
            return cls(value)
        except ValueError as exc:
            raise UnknownDomainObjectTypeError(
                f"{value!r} is not an adopted Domain Object type"
            ) from exc

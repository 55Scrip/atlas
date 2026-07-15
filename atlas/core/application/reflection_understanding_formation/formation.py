"""Formation act data model (ATLAS-013A).

A Formation act is the exercise that forms or restates a
ReflectionUnderstanding. Authorship and epistemic authority attach to
the act, not to the Understanding (ATLAS-013A-D Chapter 9): two separate
acts may form or restate the very same extensional Reflection
Understanding while carrying different authorship modes and different
epistemic qualification, and neither may be projected backward as a
single, permanent property of the Understanding.

Substance-authorship ("whose interpretive judgment") and
articulation-authorship ("whose act rendered it into explicit form") are
kept as two separately typed fields — ArticulationAuthorshipMode is a
distinct enum from SubstanceAuthorshipMode, not a reuse of it, because
the two answer conceptually different questions even where, in this
increment's only operative path, they coincide.

FormationAct has no identity criterion of its own beyond numerical
distinctness of occurrence (ATLAS-013A-D Chapter 7): two acts remain two
even when every field — including two ReflectionUnderstanding values
that are themselves extensionally equal to each other — happens to
match. `eq=False` here suppresses dataclass-generated equality entirely,
with no replacement __eq__/__hash__ written, so Python's own
identity-based comparison (`is`) is what's left — the correct behavior,
not an oversight.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.core.application.reflection_understanding_formation.exceptions import (
    MissingEpistemicQualificationError,
)
from atlas.core.application.reflection_understanding_formation.understanding import (
    ReflectionUnderstanding,
)


class SubstanceAuthorshipMode(Enum):
    """Whose interpretive judgment an act's proposition expresses.

    ATLAS-013A-D Chapter 9 authorizes all three values as a deliberate
    domain decision. Only INVESTOR_SUBSTANCE_AUTHORED is exercised by
    this increment's own CLI — the other two remain structurally
    representable for any future, appropriately authorized caller.
    """

    INVESTOR_SUBSTANCE_AUTHORED = "investor_substance_authored"
    ATLAS_SUBSTANCE_AUTHORED = "atlas_substance_authored"
    JOINTLY_SUBSTANCE_AUTHORED = "jointly_substance_authored"


class ArticulationAuthorshipMode(Enum):
    """Whose act rendered an interpretive proposition into the explicit,
    traceable form Reflection Understanding requires.

    Deliberately a separate type from SubstanceAuthorshipMode, even
    though its three values mirror the same three parties — conflating
    the two types would answer two different questions with one enum,
    exactly the category error this document has refused elsewhere.
    """

    INVESTOR_ARTICULATED = "investor_articulated"
    ATLAS_ARTICULATED = "atlas_articulated"
    JOINTLY_ARTICULATED = "jointly_articulated"


@dataclass(frozen=True)
class EpistemicQualification:
    """An act-scoped statement of how hedged, tentative, or confident its
    interpretive judgment was.

    Mirrors ResponseText's and InterpretiveContent's own discipline:
    validation only, `value` never reassigned. None is a distinct,
    separate case (see FormationAct) meaning no qualification was
    articulated at all — it is not represented by this type and must
    never be read as implying any particular confidence level.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingEpistemicQualificationError(
                "EpistemicQualification.value must not be empty or whitespace-only"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, eq=False)
class FormationAct:
    """One occurrence of the Reflection Understanding Formation
    capability — bounded, terminating, and numerically distinct from
    every other act purely by virtue of being its own occurrence.

    `occurred_at` records when this particular act occurred. It is a
    property of the act alone, never of the Reflection Understanding it
    formed or restated: separate acts, occurring at different times, may
    form or restate the very same extensional Understanding, each with
    its own `occurred_at` (ATLAS-013A-D Chapter 8). No id field is
    introduced — numerical distinctness is ordinary object identity.

    epistemic_qualification of None means no separate qualification was
    articulated for this act. It is the absence of a recorded statement,
    not a claim of certainty or high confidence (ATLAS-013A-D Chapter 9
    §9's own preservation requirement extends to this field's absence,
    not only to its presence).
    """

    understanding: ReflectionUnderstanding
    substance_authorship: SubstanceAuthorshipMode
    articulation_authorship: ArticulationAuthorshipMode
    epistemic_qualification: EpistemicQualification | None
    occurred_at: datetime

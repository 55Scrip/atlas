"""ReflectionUnderstandingFormationQuery — assembles a FormationAct (ATLAS-013).

Depends only on an already-built ReflectionHistory value — never on a
SQLAlchemy Engine, a repository, or ReflectionResponseRepository.get(id).
The owner-scoped reachability check is the same all-or-nothing
entries_by_id membership idiom already used by ReflectionComparisonQuery
and ReflectionExplorationQuery: "is this id reachable" is answered by one
question only — is it present among history.entries.

This class is a generic constructor: it records whatever
already-authorized substance_authorship and articulation_authorship
attribution its caller supplies, and performs only structural
validation — non-empty concerns, reachability, an explicit request
confirmed independently of content, and non-empty content/qualification.
It does not, and cannot, verify that an asserted attribution
semantically holds (that a claimed Atlas-substance-authored act really
introduced a proposition the investor hadn't already supplied, or that a
claimed joint act's proposition really depends on both contributions) —
that determination is external to this query, resting entirely on
whichever caller constructs the act. Constructing a FormationAct through
this query with ATLAS_SUBSTANCE_AUTHORED or JOINTLY_SUBSTANCE_AUTHORED
demonstrates only that the type system can structurally represent those
modes; it does not constitute, authorize, or set precedent for an
operative Formation pathway using them. The only operative pathway this
increment authorizes is cli.py's own, which asserts
INVESTOR_SUBSTANCE_AUTHORED / INVESTOR_ARTICULATED unconditionally.

Never calls .add(...) anywhere — there is no repository reachable from
this module at all, and nothing here is persisted.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone

from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.application.reflection_understanding_formation.exceptions import (
    FormationNotExplicitlyRequestedError,
    NoConcernedMaterialError,
    UnreachableReflectionResponseError,
)
from atlas.core.application.reflection_understanding_formation.formation import (
    ArticulationAuthorshipMode,
    EpistemicQualification,
    FormationAct,
    SubstanceAuthorshipMode,
)
from atlas.core.application.reflection_understanding_formation.understanding import (
    InterpretiveContent,
    ReflectionUnderstanding,
)
from atlas.core.domain.reflection_response.value_objects import ReflectionResponseId


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReflectionUnderstandingFormationQuery:
    def __init__(self, history: ReflectionHistory) -> None:
        self._history = history

    def build(
        self,
        *,
        concerns: Sequence[ReflectionResponseId],
        explicitly_requested: bool,
        substance_authorship: SubstanceAuthorshipMode,
        articulation_authorship: ArticulationAuthorshipMode,
        content: str,
        epistemic_qualification: str | None = None,
        clock: Callable[[], datetime] = _utc_now,
    ) -> FormationAct:
        if not concerns:
            raise NoConcernedMaterialError(
                "Formation requires at least one Reflection Response"
            )

        entries_by_id = {entry.id: entry for entry in self._history.entries}
        distinct_ids = dict.fromkeys(concerns)
        if any(concerned_id not in entries_by_id for concerned_id in distinct_ids):
            raise UnreachableReflectionResponseError(
                "One or more concerned Reflection Responses are not in "
                "this investor's own Reflection History"
            )

        # Explicit request is checked independently of concerns and of
        # content — a substance contribution must never be treated as
        # proof that Formation was explicitly requested.
        if explicitly_requested is not True:
            raise FormationNotExplicitlyRequestedError(
                "Formation requires a separate, explicit request beyond "
                "merely selecting material — selection alone is never an "
                "implicit request for Formation"
            )

        interpretive_content = InterpretiveContent(content)
        qualification = (
            EpistemicQualification(epistemic_qualification)
            if epistemic_qualification is not None
            else None
        )

        matched = [entries_by_id[concerned_id] for concerned_id in distinct_ids]
        ordered = tuple(
            sorted(matched, key=lambda entry: (entry.recorded_at, entry.id.value))
        )
        understanding = ReflectionUnderstanding(content=interpretive_content, concerns=ordered)

        return FormationAct(
            understanding=understanding,
            substance_authorship=substance_authorship,
            articulation_authorship=articulation_authorship,
            epistemic_qualification=qualification,
            occurred_at=clock(),
        )

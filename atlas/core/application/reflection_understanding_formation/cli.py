"""Standalone CLI entry point for Reflection Understanding Formation (ATLAS-013).

    python -m atlas.core.application.reflection_understanding_formation.cli

Deliberately separate from atlas/cli/main.py and atlas/conversation/ —
same independence discipline as every other standalone CLI in this
lineage. Read-only aside from the one explicit, disclosed Investor
Identity bootstrap step, reused verbatim, and produces no persisted
output at all: every invocation is independent and ephemeral.

Exposes only investor-substance-authored Formation. No authorized source
of an Atlas-originated interpretive proposition exists anywhere in this
codebase, and no validator can verify semantic joint-dependence from raw
text — soliciting investor-typed text and labeling it Atlas- or
jointly-authored would misattribute authorship, exactly what
ATLAS-013A-D Chapter 9 forbids. This CLI therefore never presents a
mode-selection prompt, never asks for an "Atlas contribution" or "joint
content," and always asserts INVESTOR_SUBSTANCE_AUTHORED /
INVESTOR_ARTICULATED — the one attribution this increment has an honest,
verifiable source for.

Selection and the explicit request for Formation are two separate,
sequential prompts. A substance contribution (the investor's own
interpretive text) is never solicited, and never treated as evidence of,
an explicit request — the request is confirmed first, independently.
"""
from __future__ import annotations

from collections.abc import Callable

from atlas.core.application.investor_identity.composition import (
    resolve_investor_identity,
)
from atlas.core.application.reflection_history.composition import (
    build_reflection_history_query,
    create_reflection_history_tables,
)
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.application.reflection_understanding_formation.exceptions import (
    ReflectionUnderstandingFormationError,
)
from atlas.core.application.reflection_understanding_formation.formation import (
    ArticulationAuthorshipMode,
    FormationAct,
    SubstanceAuthorshipMode,
)
from atlas.core.application.reflection_understanding_formation.query import (
    ReflectionUnderstandingFormationQuery,
)
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import ReflectionResponseId
from atlas.core.infrastructure.config.database import create_database_engine


def _sorted_entries(history: ReflectionHistory) -> tuple[ReflectionResponse, ...]:
    return tuple(
        sorted(history.entries, key=lambda response: (response.recorded_at, response.id.value))
    )


def _print_pointer_line(number: int, entry: ReflectionResponse) -> None:
    print(f"{number}. Recorded: {entry.recorded_at.isoformat()} — {entry.response_text.value}")


def _prompt_for_selection(
    ordered_entries: tuple[ReflectionResponse, ...],
    input_fn: Callable[[str], str] = input,
) -> tuple[ReflectionResponseId, ...]:
    prompt = (
        "\nType the numbers of the Reflection Responses to concern this "
        "Formation, separated by spaces, or press enter for none > "
    )
    while True:
        answer = input_fn(prompt).strip()
        if not answer:
            return ()

        tokens = answer.split()
        choices: list[int] | None = []
        for token in tokens:
            try:
                choices.append(int(token))
            except ValueError:
                choices = None
                break
        if choices is None or any(
            not (1 <= choice <= len(ordered_entries)) for choice in choices
        ):
            print("Please type only the numbers shown above, separated by spaces.")
            continue

        return tuple(ordered_entries[choice - 1].id for choice in choices)


def _prompt_for_explicit_request(input_fn: Callable[[str], str] = input) -> bool:
    answer = input_fn(
        "\nDo you want to request that Formation occur concerning these "
        "entries? (yes/no) > "
    ).strip().lower()
    return answer in ("y", "yes")


def _prompt_for_content(input_fn: Callable[[str], str] = input) -> str:
    prompt = "\nType your own interpretation of these entries > "
    while True:
        answer = input_fn(prompt)
        if answer.strip():
            return answer
        print("An interpretation is required to proceed.")


def _prompt_for_qualification(input_fn: Callable[[str], str] = input) -> str | None:
    answer = input_fn(
        "\nHow qualified or confident do you consider this interpretation? "
        "(optional, press enter to skip) > "
    )
    return answer if answer.strip() else None


def _print_result(act: FormationAct) -> None:
    print(f"\nSubstance authorship: {act.substance_authorship.value}")
    print(f"Articulation authorship: {act.articulation_authorship.value}")
    print(f"Interpretation: {act.understanding.content.value}")
    if act.epistemic_qualification is not None:
        print(f"Qualification: {act.epistemic_qualification.value}")
    else:
        print("Qualification: (none recorded)")
    print(f"Occurred at: {act.occurred_at.isoformat()}")
    print(f"Concerns ({len(act.understanding.concerns)} Reflection Response(s)):")
    for entry in act.understanding.concerns:
        print(f"  - Recorded: {entry.recorded_at.isoformat()} — {entry.response_text.value}")


def run(input_fn: Callable[[str], str] = input) -> None:
    engine = create_database_engine()
    create_reflection_history_tables(engine)
    owner_user_id = resolve_investor_identity(engine)
    history = build_reflection_history_query(engine, owner_user_id).build()

    if not history.entries:
        print("No Reflection Responses recorded yet.")
        return

    ordered_entries = _sorted_entries(history)
    print("Your preserved Reflection Responses:")
    for number, entry in enumerate(ordered_entries, start=1):
        _print_pointer_line(number, entry)

    concerns = _prompt_for_selection(ordered_entries, input_fn)
    if not concerns:
        print("\nFormation requires at least one Reflection Response.")
        return

    if not _prompt_for_explicit_request(input_fn):
        print("\nNo Formation requested.")
        return

    content = _prompt_for_content(input_fn)
    qualification = _prompt_for_qualification(input_fn)

    try:
        act = ReflectionUnderstandingFormationQuery(history).build(
            concerns=concerns,
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
            content=content,
            epistemic_qualification=qualification,
        )
    except ReflectionUnderstandingFormationError as error:
        print(f"\n{error}")
        return

    _print_result(act)


if __name__ == "__main__":
    run()

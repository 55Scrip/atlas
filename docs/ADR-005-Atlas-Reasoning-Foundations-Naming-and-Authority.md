# ADR-005 — Atlas Reasoning Foundations Naming and Authority

**Status:** Accepted.
**Type:** Repository-level governance record — outside the ontology ADR series (see [docs/atlas_reasoning_foundations/Doctrine.md](atlas_reasoning_foundations/Doctrine.md), whose ADR template is for ontological primitives, not naming/governance decisions). Follows the precedent of [docs/ADR-004-API-Serialization-Standard.md](ADR-004-API-Serialization-Standard.md).

## Context

A naming collision existed: "Atlas Core" named two unrelated things in this repository — `atlas/core/`, the implemented, tested Clean Architecture codebase (the ten-step Question→Learning Foundation Core Loop, with production orchestrators, persistence, REST interfaces, and tests), and `docs/atlas_core/`, a newer, unimplemented, ontology-first ADR track (Reasoning, Judgment). No document in either referenced the other; no roadmap, sprint, or release document established precedence or migration intent between them. This was investigated in ENG-001 (Kernel Architecture Review) and resolved in ARC-001 (Authority and Naming Resolution, Option D).

## Decision

1. **`atlas/core/` remains the sole current authority** for runtime behavior, the implemented ten-step reasoning cycle, and the domain semantics currently embodied in code. It is not renamed — it is an established package path with no practical alternative to a costly, unjustified rename.
2. **The ontology-first ADR track is renamed** from `docs/atlas_core/` to **`docs/atlas_reasoning_foundations/`**, and is referred to as **Atlas Reasoning Foundations**. It remains a separate, pre-implementation ontology track, authoritative only for its own settled or in-progress questions (currently: Reasoning, Final; Judgment, Draft).
3. **Neither track currently governs, supersedes, reinterprets, or implies future convergence with the other.** Whether any relationship between them will exist in the future is explicitly undecided by this ADR and is not to be inferred from either track's content.
4. **"Atlas Kernel" remains deferred and unestablished.** It has no justified architectural meaning under either track today and must not be treated as referring to anything settled until a dedicated, separate architecture decision addresses it.
5. **Future documents must not use the bare term "Atlas Core" ambiguously.** Where "core" business logic under `atlas/core/` is meant, name it explicitly (e.g., "the `atlas/core/` implementation," "the Foundation Core Loop"). Where the ontology track is meant, use "Atlas Reasoning Foundations."

## Consequences

- `docs/atlas_core/` no longer exists; its five files (Doctrine.md, ADR-001, ADR-002, README.md, Dependency-Graph.md) now live under `docs/atlas_reasoning_foundations/` with internal self-references updated to the new name. No ontological statement, ADR status, or open question was altered.
- The root `README.md` documentation index now lists this track under its new name, described as ontology-first and pre-implementation.
- Any future work proposing a relationship between `atlas/core/` and Atlas Reasoning Foundations, or proposing an "Atlas Kernel," requires its own explicit decision — neither is authorized by this ADR.

## Related

ENG-001 — Kernel Architecture Review. ARC-001 — Authority and Naming Resolution (Option D adopted). [docs/atlas_reasoning_foundations/](atlas_reasoning_foundations/README.md).

# Atlas Reasoning Foundations

This document is the entry point for Atlas Reasoning Foundations. It is purely navigational: it orients a reader to what exists, in what order to read it, and how the pieces relate to one another. It introduces no ontology, no primitives, and no architectural or implementation content of its own — all of that lives in the documents it points to.

## Purpose

Atlas Reasoning Foundations is the line of work that defines, from first principles, the concepts underlying Atlas's reasoning capabilities — starting with Reasoning itself and the concepts it depends on. It is developed under a fixed, normative doctrine rather than ad hoc convention, so that its foundations remain sound as its scope grows.

## Scope

Atlas Reasoning Foundations currently consists of:

- a **Development Doctrine** governing how all Atlas Reasoning Foundations work is conducted, and
- a series of **Architecture Decision Records (ADRs)**, each settling exactly one ontological primitive.

Atlas Reasoning Foundations does not yet contain any architecture or implementation work. Per the Doctrine's own ordering (Ontology Before Architecture, Architecture Before Implementation), that work is gated behind the ontology it would depend on reaching Final status.

## Relationship Between Doctrine, Foundations, Architecture, and Implementation

Four distinct layers, each resting on the one before it:

1. **Doctrine** — [Doctrine.md](Doctrine.md). Defines *how* Atlas Reasoning Foundations is developed: method, discipline, ADR structure, acceptance criteria. Governs every layer below it, including itself as it is revised.
2. **Foundations (ontology)** — the ADR series. Defines *what things are*: Reasoning, Judgment, Knowledge, and whatever further primitives later ADRs establish. Each ADR is Draft until it meets the Doctrine's Definition of Done, at which point it becomes Final.
3. **Architecture** — not yet begun. Will define how the ontology's settled (Final) primitives are structured, related, and organized into components, once there is sufficient Final ontology to build on.
4. **Implementation** — not yet begun. Will implement whatever Architecture settles, per the Doctrine's Architecture Before Implementation principle.

No work currently exists at the Architecture or Implementation layers.

## Reading Order

1. [Doctrine.md](Doctrine.md) — read first. Defines the standard every document below it is expected to meet, and how to read an ADR's own status.
2. [ADR-001-The-Nature-of-Reasoning.md](ADR-001-The-Nature-of-Reasoning.md) — Final. Foundational: establishes Reasoning, the Reasoning Act, Reasoning's relationship to Knowledge, and the existence (but not full definition) of Judgment.
3. [ADR-002-The-Nature-of-Judgment.md](ADR-002-The-Nature-of-Judgment.md) — Draft. Depends on ADR-001. Attempts to settle what Judgment is; currently carries an open, unresolved contradiction and several open dependencies, recorded rather than resolved.
4. [ADR-003-The-Nature-of-Knowledge.md](ADR-003-The-Nature-of-Knowledge.md) — Final. Depends on ADR-001 and ADR-002. Characterizes Knowledge's established standing — material available for Reasoning's examination and free of current active revision — without settling Knowledge's intrinsic category, without settling whether Knowledge decomposes into portions, without resolving Knowledge's relationship to Evidence, Observation, or Reality, and without asserting that its current dependence on Reasoning is necessarily essential rather than provisional. These are recorded as explicit, stated boundaries of a Final document, not as open contradictions.

Further ADRs, as they are written, are added to this list in the order a new reader should encounter them — which is not necessarily their numeric order, if a later ADR is more foundational to a given reading path than its number suggests.

## Atlas Reasoning Foundations Roadmap

This section reports actual status; it does not commit to a plan for work that has not yet been decided.

**Completed:**
- Development Doctrine established.
- ADR-001 — The Nature of Reasoning — Final.
- ADR-003 — The Nature of Knowledge — Final, carrying four explicitly stated open boundaries (Knowledge's intrinsic category; whether Knowledge decomposes into portions; whether its Reasoning-dependence is essential or provisional; its relationship to Evidence, Observation, and Reality) rather than unresolved contradictions.

**In progress:**
- ADR-002 — The Nature of Judgment — Draft, with one open contradiction (process vs. object) and three open dependencies (*Candidate*, *Confidence*, *Agent*) identified but not yet defined.

**Not yet scheduled:**
- Any ADR addressing *Candidate*, *Confidence*, or *Agent* — these are open dependencies surfaced by ADR-002, not commitments to future ADRs in any particular order or timeframe.
- Any ADR addressing *Evidence*, *Observation*, or *Reality*, or otherwise resolving Knowledge's relationship to them — these are open boundaries surfaced by ADR-003, not commitments to future ADRs in any particular order or timeframe.
- All Architecture and Implementation work, gated behind further ontology reaching Final status.

## ADR Status Table

| ADR | Title | Status | Depends On |
|---|---|---|---|
| [ADR-001](ADR-001-The-Nature-of-Reasoning.md) | The Nature of Reasoning | Final | — |
| [ADR-002](ADR-002-The-Nature-of-Judgment.md) | The Nature of Judgment | Draft | ADR-001 |
| [ADR-003](ADR-003-The-Nature-of-Knowledge.md) | The Nature of Knowledge | Final | ADR-001, ADR-002 |

## Dependency Graph Overview

```
Doctrine.md
   (governs all ADRs)

ADR-001 — The Nature of Reasoning [Final]
   |
   +--> ADR-002 — The Nature of Judgment [Draft]
   |         |
   |         +--> Candidate   (undefined — no ADR yet)
   |         +--> Confidence  (undefined — no ADR yet)
   |         +--> Agent       (undefined — no ADR yet)
   |
   +--> ADR-003 — The Nature of Knowledge [Final] (also depends on ADR-002 directly; see below)
              |
              +--> Evidence     (undefined — no ADR yet; relationship to Knowledge unresolved)
              +--> Observation  (undefined — no ADR yet)
              +--> Reality      (undefined — no ADR yet)
```

The three dangling edges under ADR-002 are recorded as open dependencies in ADR-002 itself, not resolved here or anywhere else yet. The three dangling edges under ADR-003 are recorded as open dependencies in ADR-003 itself, likewise not resolved here or anywhere else yet. ADR-003 also depends directly on ADR-002 (not only via ADR-001, per ADR-003's own Dependency Graph), and carries two further boundaries that are not separate primitives awaiting their own ADR: whether Knowledge has a settled intrinsic category, and whether Knowledge decomposes into determinate portions. Both are recorded in ADR-003 as open questions about Knowledge itself, not as dangling edges to some other, not-yet-named primitive.

## Contribution Guidelines

All Atlas Reasoning Foundations work is governed by [Doctrine.md](Doctrine.md); this section only orients a contributor to where to look, not what the rules are. In brief, before contributing:

- Read the Doctrine in full — particularly Standard ADR Structure, Acceptance Criteria, and Definition of Done.
- A new ADR settles exactly one primitive, reasoned from first principles, with genuine falsification attempts recorded, not merely asserted.
- Any contradiction with an existing Final ADR is recorded explicitly, never silently resolved or omitted.
- New ADRs start as Draft. Promotion to Final follows the Doctrine's Definition of Done, not author confidence.
- This README is updated whenever an ADR's status changes, or a new ADR is added, so it continues to accurately reflect the state above.

## Repository Structure

```
docs/atlas_reasoning_foundations/
    README.md                          — this document; entry point and index
    Doctrine.md                        — normative development doctrine
    ADR-001-The-Nature-of-Reasoning.md — Final
    ADR-002-The-Nature-of-Judgment.md  — Draft
    ADR-003-The-Nature-of-Knowledge.md — Final
```

`docs/atlas_reasoning_foundations/` is a self-contained directory, distinct from the flat `docs/` structure used by Atlas Foundation's own ATLAS-0XX documents, and distinct from the unrelated, pre-existing `docs/ADR-004-API-Serialization-Standard.md` (a one-off Foundation record, on its own separate numbering track). Nothing outside `docs/atlas_reasoning_foundations/` is part of Atlas Reasoning Foundations.

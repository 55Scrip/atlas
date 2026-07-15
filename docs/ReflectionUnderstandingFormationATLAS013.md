# ATLAS-013 — Reflection Understanding Formation

**Status:** Implemented, pending review.
**Scope:** Standalone, read-only-except-for-one-act CLI letting an investor explicitly select Reflection Response material and, through a separate explicit request, form new interpretive content about it — an operative act of Reflection Understanding Formation.
**Depends on:** ATLAS-013-D's authoritative Reflection Understanding definition (Chapters 1–9) and ATLAS-013A-D's authoritative Reflection Understanding Formation definition (Chapters 1–10), both fixed and unrevised by this increment; `ReflectionHistoryQuery`/`ReflectionHistory` (ATLAS-010), consumed completely unmodified; `resolve_investor_identity` (ATLAS-009B), reused verbatim.

---

## 1. Purpose

ATLAS-013-D established what a Reflection Understanding *is* — new, explicit, traceable interpretive content about relationships within Reflection Response material — without deciding how one comes to exist. ATLAS-013A-D closed that gap: it authorizes three substance-authorship modes, attaches authorship and epistemic authority to the *act* of Formation rather than to the Understanding it produces, and fixes the Understanding's own identity as purely extensional. This increment implements the smallest operative slice that doctrine supports: an investor may explicitly select material, explicitly request that Formation occur concerning it, and record their own interpretation — the one authorship path this codebase currently has an honest source for.

## 2. Capability, Act, and Result — Three Distinct Layers

Reflection Understanding Formation is implemented as three deliberately distinct layers, matching ATLAS-013A-D's own capability/act/result distinction exactly:

- **The capability** is the standing, always-available domain capability within which a Reflection Understanding may come into being — it is not itself a class or a stored value; nothing in this codebase represents it as an object, because a standing authorization is not the kind of thing that needs one.
- **An act** is represented by `FormationAct` — one bounded, terminating exercise of the capability, carrying the authorship and epistemic attribution *for that exercise alone*.
- **The result** is `ReflectionUnderstanding` — the interpretive content and the material it concerns, held by (not equal to) the act that produced it.

No single type conflates these three questions; each has its own file (`formation.py` for the act, `understanding.py` for the result).

## 3. Explicit Selection and a Separate Explicit Request

Every operative act requires **two independent facts**, checked separately, in a fixed order: explicit selection of Reflection Response material, and a **separate**, explicit request that Formation occur concerning it. `ReflectionUnderstandingFormationQuery.build()` checks `explicitly_requested is True` **before it examines any content**, entirely independent of whatever `concerns` or interpretive text is supplied — a substance contribution can never substitute as proof that Formation was requested, and an empty selection is rejected outright (a deliberate, disclosed difference from Reflection Exploration, whose own zero-selection outcome is valid: Formation constitutively requires Response material to concern). The CLI mirrors this as two sequential, independent prompts — a selection prompt, then a separate yes/no confirmation — with no content ever solicited before both are satisfied.

## 4. Reflection Understanding's Extensional Identity

`ReflectionUnderstanding` carries no synthetic id. Per ATLAS-013-D Chapter 6, its identity is purely extensional — content and concerned material, nothing else — so equality and hash are hand-written over `(content, frozenset(concerned ids))` rather than generated from all fields positionally. `concerns` itself holds the complete, verbatim `ReflectionResponse` objects (not just ids), captured once at construction for full traceability with no later re-lookup, while its own `__post_init__` independently rejects empty, duplicate, or non-canonically-ordered concerned material — a defense the value object enforces itself, rather than trusting the query alone to have gotten it right.

## 5. Formation Acts Are Numerically Distinct by Object Identity

`FormationAct` has no identity criterion beyond numerical distinctness of occurrence (ATLAS-013A-D Chapter 7). It is declared `eq=False` with **no** hand-written replacement, so Python's own identity-based `__eq__`/`__hash__` are what remain in effect: two acts are equal only if they are the same object. This is proven directly by test — two acts built from identical arguments, including two `ReflectionUnderstanding` values that are themselves extensionally equal to one another, still compare unequal to each other and equal only to themselves.

## 6. Authorship and Epistemic Qualification Belong to the Act

`FormationAct`, not `ReflectionUnderstanding`, carries `substance_authorship`, `articulation_authorship`, and `epistemic_qualification`. Substance-authorship ("whose interpretive judgment") and articulation-authorship ("whose act rendered it into explicit form") are two separately typed enums — `SubstanceAuthorshipMode` and `ArticulationAuthorshipMode` — kept distinct even where, in this increment's only operative path, they coincide. `epistemic_qualification: EpistemicQualification | None` is likewise act-scoped: `None` means no qualification was articulated for *this* act — it is the absence of a recorded statement, never a claim of confidence or certainty. None of the three participates in `ReflectionUnderstanding`'s own identity, so separate acts forming or restating the same extensional Understanding may carry different authorship or different qualification without that difference implying they produced different Understandings.

## 7. Architecture — No New Infrastructure Layer

```
atlas/core/application/reflection_understanding_formation/
    understanding.py   InterpretiveContent, ReflectionUnderstanding
    formation.py         SubstanceAuthorshipMode, ArticulationAuthorshipMode,
                          EpistemicQualification, FormationAct
    exceptions.py         error hierarchy
    query.py              ReflectionUnderstandingFormationQuery(history).build(...)
    cli.py                standalone CLI — investor-substance-authored only
```

Like Reflection Comparison and Reflection Exploration, this module has no `domain/`, no `infrastructure/persistence/`, and no `composition.py`. `understanding.py`, `formation.py`, `exceptions.py`, and `query.py` import no SQLAlchemy at all; only `cli.py` reaches infrastructure, and only by reusing ATLAS-009B/ATLAS-010's existing composition functions verbatim. **Nothing this module produces is persisted anywhere** — every CLI invocation is independent and ephemeral, exactly like Comparison's and Exploration's own results; ATLAS-013-D Chapter 8 leaves persistence external to Reflection Understanding's nature and undecided, and implementing none here preserves that silence rather than resolving it.

## 8. The Query Records Attribution; It Does Not Verify It

`ReflectionUnderstandingFormationQuery.build()` is a generic constructor: it performs only structural validation (non-empty `concerns`, all-or-nothing reachability against `ReflectionHistory`, the explicit-request check, non-empty content/qualification) and **records** whatever `substance_authorship`/`articulation_authorship` its caller supplies — it cannot, and does not attempt to, verify that an asserted attribution semantically holds. This is what keeps `SubstanceAuthorshipMode.ATLAS_SUBSTANCE_AUTHORED` and `.JOINTLY_SUBSTANCE_AUTHORED` real, structurally representable values (proven directly by test, constructing acts with each) while remaining **operatively unreachable through this increment's CLI**: no authorized source of an Atlas-originated or jointly-formed interpretive proposition exists anywhere in this codebase yet, and soliciting investor-typed text under either label would misattribute authorship — exactly what ATLAS-013A-D Chapter 9 forbids. Both modes are authorized by doctrine and supported by the types; only `INVESTOR_SUBSTANCE_AUTHORED` / `INVESTOR_ARTICULATED` has an honest, operative source today.

## 9. CLI

Bootstrap identical to every sibling CLI (`create_database_engine()` → `create_reflection_history_tables(engine)` → `resolve_investor_identity(engine)` → `build_reflection_history_query(...).build()`). An empty store prints an honest message without prompting. Otherwise: print a numbered pointer list → select material (empty selection aborts with an honest message) → a separate, explicit yes/no request confirmation (declining aborts before any content is solicited) → prompt for the investor's own interpretation (required, reprompts on blank) → an optional qualification prompt (blank means `None`, displayed as "(none recorded)", never a confidence claim) → build and print the resulting act's full attribution, content, qualification, timestamp, and complete concerned material verbatim. The CLI never presents a mode-selection menu and never asks for an "Atlas contribution" or "joint content" — it always asserts `INVESTOR_SUBSTANCE_AUTHORED` / `INVESTOR_ARTICULATED` unconditionally.

## 10. Test Summary

52 new tests, regression-clean:

- **`test_understanding.py`** (13) — `InterpretiveContent` validation; `ReflectionUnderstanding` construction rejecting empty/duplicate/non-canonically-ordered concerns; extensional equality and hash.
- **`test_formation.py`** (7) — `EpistemicQualification` validation; `FormationAct` object-identity proof, including that two acts with identical fields (and extensionally-equal Understandings) remain unequal and hash as distinct set members.
- **`test_query.py`** (16) — empty concerns; unreachable ids (nonexistent and different-owner, indistinguishably); explicit-request-false failing even with otherwise-valid content; content/qualification validation; successful builds including duplicate-id dedup and input-order independence; direct construction with Atlas-/joint-mode attribution, documented as proving structural representability only; input immutability.
- **`test_module_isolation.py`** (2) — AST-based: no import from any sibling capability including `reflection_comparison`/`reflection_exploration`; no `sqlalchemy` import outside `cli.py`.
- **`test_cli.py`** (14) — prompt-level unit tests for selection, explicit-request, content, and qualification; end-to-end runs covering empty store, empty selection, declining the explicit request, a full successful Formation, and blank-qualification display.
- **Manual verification:** a real SQLite store seeded with one Decision and two Reflection Responses via the actual repositories; the real CLI run three times — empty selection, declining the explicit request, and a full successful investor-substance-authored Formation with a recorded qualification — each behaving exactly as designed; row counts confirmed unchanged (1 Decision, 2 Reflection Responses, 1 Investor Identity) before and after all three runs.

**Regression:** full repository suite: **7,783 passed, 3 skipped** (7,731 pre-existing + 52 new). Scoped lint: clean. Whole-repo `ruff check .` count unchanged at 1,202.

## 11. Architectural Decisions

1. **No new repository method, no new SQL, no new table, no aggregate** — identical conclusion to Reflection Comparison and Reflection Exploration, and to ATLAS-013-D Chapter 8's own conclusion that persistence is not constitutive of Reflection Understanding.
2. **No synthetic identity anywhere** — `ReflectionUnderstanding`'s extensional identity and `FormationAct`'s numerical distinctness are both realized through dataclass equality semantics (`eq=False` used two different ways for two different reasons), never an id field.
3. **Substance-authorship is recorded, not derived or verified** — the query trusts its caller's assertion; only the CLI's own investor-only path is operative today.
4. **Only investor-substance-authored Formation is exposed** — a deliberate, disclosed restriction, not an oversight: Atlas- and jointly-formed modes remain fully authorized by doctrine and fully representable by the types, awaiting a future increment that defines an authorized source for either.
5. **Explicit request is checked independently of content** — structurally prevents a contribution from ever being treated as proof of request.

## 12. Anything That Feels Overengineered

Nothing. Every additional field and check beyond the prior draft (separate articulation-authorship type, act-scoped qualification, self-validating construction invariants, object-identity-only acts) was added in direct response to a specific, named doctrinal requirement, not speculatively.

## 13. What Can Be Simplified

Nothing further at this stage.

## 14. Genuine Risks / Unresolved Questions

- **Only one of three authorized authorship modes is operative.** This is correct given today's constraints, not a gap to silently work around — a future increment must define an authorized source before Atlas- or joint-formation can be honestly exposed through any interface.
- **No persistence** means every Formation act is lost once the CLI process ends. This is a disclosed, deliberate consequence of ATLAS-013-D Chapter 8's own undecided persistence question, not an oversight.
- **Same disclosed simplifications ATLAS-010/011/012 already accepted carry over unchanged** (no filtering/search/pagination in the pointer list, etc.).

## 15. Future Backlog

- Carried forward, unaffected by this increment: a retrieval interface for Investor Identity itself; re-evaluating `reasoning_link`'s placement and permanence; a REST API layer for the Core Loop; the shared structured Error Contract; the brittle hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`.
- New: defining an authorized source for Atlas-substance-authored and jointly substance-authored Formation, which this increment's types already support without requiring any change.

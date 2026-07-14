# ATLAS-012 — Reflection Exploration

**Status:** Implemented, pending review.
**Scope:** Standalone, read-only CLI letting an investor explicitly enumerate zero or more Reflection Response identities from their own owner-scoped Reflection History (ATLAS-010) and receive a temporary, complete, unmodified scope containing exactly those owned Responses.
**Depends on:** ATLAS-012-D's authoritative Reflection Exploration definition; `ReflectionHistoryQuery`/`ReflectionHistory` (ATLAS-010), consumed completely unmodified; `resolve_investor_identity` (ATLAS-009B), reused verbatim.

---

## 1. Purpose

Reflection History lets an investor see every preserved Reflection Response; Reflection Comparison (ATLAS-011) lets them arrange exactly two side by side. Reflection Exploration fills the space between: an arbitrary, investor-named set — zero, one, several, or all of them — examined together, without Atlas ever inferring which ones belong together.

## 2. Inspection Finding That Shaped This Design

Before choosing a repository interface, `ReflectionHistoryQuery.build()` was inspected directly, exactly as it was for ATLAS-011: it already returns the complete, owner-scoped `ReflectionHistory.entries` in memory. Resolving any number of explicitly-named ids against that tuple — checking membership, deduplicating, ordering — is a pure in-memory operation that cannot violate ownership, because the collection was already reduced to exactly one investor's own Responses before Reflection Exploration ever sees it.

**Conclusion: no new repository method, no new SQL, and no dependency on `ReflectionResponseRepository.get(id)`** — identical to ATLAS-011's own conclusion, generalized from a fixed pair to an arbitrary-size, deduplicated set.

## 3. Architecture — No New Infrastructure Layer

```
atlas/core/application/reflection_exploration/
    exploration.py   ReflectionExploration(entries: tuple[ReflectionResponse, ...])
    exceptions.py    ReflectionExplorationError, UnreachableReflectionResponseError
    query.py         ReflectionExplorationQuery(history) — .build(selected_ids)
    cli.py           standalone CLI
```

Like Reflection Comparison, this module has no `domain/`, no `infrastructure/persistence/`, and no `composition.py`. `exploration.py`, `exceptions.py`, and `query.py` import no SQLAlchemy at all; only `cli.py` reaches infrastructure, and only by reusing ATLAS-009B/ATLAS-010's existing composition functions verbatim.

## 4. Selection, Validation, Deduplication, and Ordering

`ReflectionExplorationQuery.build(selected_ids: Sequence[ReflectionResponseId])`:

1. **Deduplicates first.** Reflection Exploration is defined over set membership, not occurrence count — naming the same Reflection Response more than once conveys no additional domain information, so duplicates are silently collapsed with no exception. This is a deliberate difference from Reflection Comparison, where duplicate selection was itself invalid: Comparison has a fixed arity of two distinct positions a duplicate cannot coherently fill, while Exploration's scope has no fixed arity at all.
2. **Validates against `history.entries` as one all-or-nothing check.** If any named id is absent — whether it doesn't exist at all or belongs to a different investor, deliberately indistinguishable — the *entire* request raises `UnreachableReflectionResponseError`. No partial scope is ever returned; silently dropping an unreachable id and returning the rest would itself be a silent narrowing of the investor's explicit membership, which ATLAS-012-D forbids.
3. **Orders the result** by `(recorded_at, id.value)` ascending, regardless of the order the ids were supplied in — the same rule `ReflectionHistoryQuery` and `ReflectionComparisonQuery` already use.

An empty `selected_ids` sequence requires no special-casing: zero ids means zero lookups, so the result is simply `ReflectionExploration(entries=())` — a valid, non-error outcome.

## 5. Input Immutability

`ReflectionHistory` and its contained `ReflectionResponse` objects are already frozen dataclasses. `ReflectionExplorationQuery.build()` constructs a new `ReflectionExploration` value on every call; it never mutates the supplied `history` or any Response reachable through it. Tested directly: the supplied `history` and its entries are unchanged, by both equality and object identity, after a successful build and after one that raises `UnreachableReflectionResponseError`.

## 6. CLI

Mirrors `reflection_comparison/cli.py`'s list-then-select shape, generalized from exactly two selections to any number. Builds the engine, calls `create_reflection_history_tables`, the explicit `resolve_investor_identity` bootstrap step, then `build_reflection_history_query(...).build()`. Prints a numbered pointer line per entry — explicitly sorted by `(recorded_at, id.value)` before numbering, a presentation-consistency decision only, so the numbers line up with the order the resulting Exploration will itself display — then prompts once for a space-separated list of numbers, with empty input producing an empty scope. Malformed or out-of-range tokens cause a reprompt rather than being silently dropped, keeping the CLI's own honesty discipline consistent with the query's all-or-nothing behavior. On success, every entry in the resulting scope prints complete and verbatim. `UnreachableReflectionResponseError` can never actually be triggered through this CLI's own legitimate selection mechanism, by construction — `_prompt_for_selection` only ever returns ids drawn from the already-displayed, already-owned entries — the same situation Reflection Comparison's "not owned" path is in.

## 7. Test Summary

28 new tests, regression-clean:

- **`test_exploration.py`** (3) — construction, empty-entries validity, immutability.
- **`test_query.py`** (14) — empty selection; single and multiple valid selections; ordering independent of input order; equal-timestamp tie-breaking; full verbatim provenance; duplicate ids silently deduplicated (alone and mixed with other selections); a nonexistent id and one belonging to a synthetic *different* owner both raise `UnreachableReflectionResponseError` indistinguishably; no partial scope is returned when one of several ids is unreachable; the supplied history and its entries are unchanged after both a successful and a failed build.
- **`test_module_isolation.py`** (2) — AST-based: no import from `pattern_recognition`/`strategy_signature`/`decision_reflection`/`decision_coach`/`decision_timeline`/**`reflection_comparison`**; `exploration.py`/`exceptions.py`/`query.py` import no `sqlalchemy` at all.
- **`test_cli.py`** (9) — list-position mapping including duplicates and reprompt on malformed/out-of-range input; verbatim field display; deterministic sort-before-display; an empty store prints an honest message without ever prompting; selecting a subset produces exactly that subset, verbatim, with excluded entries absent from the detail section; an empty selection prints an honest "exploration is empty" message.
- **Manual verification:** five real conversations recorded via `conversation/cli.py` (building a recognized pattern and preserving three separate Reflection Responses across three later conversations); `reflection_exploration/cli.py` run against the same store — selecting two entries with a repeated number produced exactly two entries, verbatim, correctly deduplicated; an empty selection produced the honest empty-exploration message; a malformed token reprompted correctly before accepting a valid one; the store's row counts were confirmed unchanged before and after every run.

**Regression:** full repository suite: **7,731 passed, 3 skipped** (7,703 pre-existing + 28 new). Scoped lint: clean. Whole-repo `ruff check .` count unchanged at 1,202.

## 8. Architectural Decisions

1. **No new repository method, no `ReflectionResponseRepository.get(id)` reuse** — identical to ATLAS-011, generalized to arbitrary cardinality.
2. **Duplicates are deduplicated, not rejected** — a deliberate, disclosed difference from Reflection Comparison, justified by Exploration's set semantics versus Comparison's fixed two-position arity.
3. **All-or-nothing failure on any unreachable id** — never a silent partial scope, per ATLAS-012-D's explicit prohibition on Atlas narrowing the investor's stated membership.
4. **Structural isolation extends to `reflection_comparison` itself** — enforcing ATLAS-012-D Ch5's boundary that Exploration must never construct, call, or collapse into repeated Comparisons.
5. **No `composition.py`** — nothing to wire, identical justification to Reflection Comparison.

## 9. Anything That Feels Overengineered

Nothing. The query is a deduplicate-then-validate-then-sort function over an already-in-memory tuple.

## 10. What Can Be Simplified

Nothing further at this stage.

## 11. Genuine Risks / Unresolved Questions

- **Failing the entire request on any single unreachable id** is a real, disclosed usability cost: an investor who selects nine valid entries and one mistyped number gets nothing back, not eight-of-nine. This is the correct, honest behavior per ATLAS-012-D, not an oversight — but a future CLI could soften it with a reprompt loop without changing the query's own domain-level all-or-nothing contract.
- **No filtering/search/pagination** in the initial pointer list — an investor with many preserved Reflection Responses sees all of them listed at once. Explicitly out of scope per ATLAS-012-D.
- **Same disclosed simplifications ATLAS-010/011 already accepted carry over unchanged.**

## 12. Future Backlog

- Carried forward, unaffected by this increment: a retrieval interface for Investor Identity itself; re-evaluating `reasoning_link`'s placement and permanence; a REST API layer for the Core Loop; the shared structured Error Contract; the brittle hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`.

# ATLAS-011 — Reflection Comparison

**Status:** Implemented, pending review.
**Scope:** Standalone, read-only CLI letting an investor explicitly select exactly two distinct, already-preserved Reflection Responses from their own owner-scoped Reflection History (ATLAS-010) and view them together, complete and unmodified.
**Depends on:** ATLAS-011-D's authoritative Reflection Comparison definition; `ReflectionHistoryQuery`/`ReflectionHistory` (ATLAS-010), consumed completely unmodified; `resolve_investor_identity` (ATLAS-009B), reused verbatim.

---

## 1. Purpose

Reflection History lets an investor see every preserved Reflection Response, in order. Nothing let them hold two specific moments up against each other. Reflection Comparison closes that gap — not by drawing any connection between two Responses itself, but by letting the investor place two of their own choosing side by side.

## 2. Inspection Finding That Shaped This Design

Before choosing a repository interface, `ReflectionHistoryQuery.build()` was inspected directly: it already returns a `ReflectionHistory(entries: tuple[ReflectionResponse, ...])` containing the *complete, owner-scoped* set of one investor's preserved Reflection Responses — the join `list_all_for_owner` performs (ATLAS-010) already gets ownership right. Once that tuple exists in memory, selecting two named members from it is a pure in-memory lookup that cannot violate ownership, because the collection was already reduced to exactly this investor's own Responses before Reflection Comparison ever sees it.

**Conclusion: no new repository method, no new SQL, and no use of `ReflectionResponseRepository.get(id)` (ATLAS-009's plain, unscoped point lookup) were needed.** Using `get(id)` would have reintroduced a second, independent, unscoped path to a Reflection Response — exactly the risk this inspection was meant to rule out.

## 3. Architecture — No New Infrastructure Layer

```
atlas/core/application/reflection_comparison/
    comparison.py    ReflectionComparison(first, second)
    exceptions.py    ReflectionComparisonError, DuplicateReflectionResponseSelectionError,
                      ReflectionResponseNotOwnedError
    query.py         ReflectionComparisonQuery(history) — .build(first_id, second_id)
    cli.py           standalone CLI
```

This is the first capability in this lineage with **no `domain/`, no `infrastructure/persistence/`, and no `composition.py`** — a direct consequence of composing entirely from an already-assembled, already-owner-scoped, in-memory `ReflectionHistory` rather than touching a database. `comparison.py`, `exceptions.py`, and `query.py` import no SQLAlchemy at all, not even `Engine`; only `cli.py` reaches infrastructure, and only by reusing ATLAS-009B/ATLAS-010's own composition functions verbatim.

## 4. Selection, Validation, and Ordering

`ReflectionComparisonQuery.build(first_id: ReflectionResponseId, second_id: ReflectionResponseId)`:

1. Identical ids → `DuplicateReflectionResponseSelectionError`, no lookup attempted.
2. Either id absent from `history.entries` → `ReflectionResponseNotOwnedError` — **the same exception, same message, whether the id doesn't exist at all or belongs to a different investor.** Reflection Comparison never distinguishes these, and never leaks which applies.
3. Both found: the two matched entries are placed into `first`/`second` ordered by `(recorded_at, id.value)` ascending, **regardless of the order the two ids were supplied in** — the same ordering rule `ReflectionHistoryQuery` already uses for its own full history.

The query's own input contract is two `ReflectionResponseId` values — never a raw list-position integer, keeping presentation-specific indexing entirely inside `cli.py`.

## 5. CLI

Mirrors `decision_timeline`'s list → detail shape and `reflection_history`'s bootstrap discipline: builds the engine, calls `create_reflection_history_tables`, the explicit `resolve_investor_identity` bootstrap step, then `build_reflection_history_query(...).build()`. Prints a short numbered pointer line per entry, prompts for two numbers, maps each to a `ReflectionResponseId`, and calls `ReflectionComparisonQuery(history).build(...)`. On success, both entries print complete and verbatim (reusing the same field-by-field display approach as `reflection_history/cli.py`). On either exception, a plain message is printed; nothing is retried, defaulted, or persisted. Atlas never suggests, infers, ranks, or pre-selects either half — both numbers must come from the investor's own input.

## 6. Test Summary

18 new tests, regression-clean:

- **`test_comparison.py`** (2) — construction, immutability.
- **`test_query.py`** (8) — two distinct owned ids produce a correct comparison; ordering is independent of input order; equal-`recorded_at` entries tie-broken by ascending `id.value`; full provenance returned exactly as persisted; identical ids raise `DuplicateReflectionResponseSelectionError`; an absent id raises `ReflectionResponseNotOwnedError`; an id belonging to a synthetic *different* owner is indistinguishable from a nonexistent one; both ids absent raises the same error.
- **`test_module_isolation.py`** (2) — AST-based: no import from `pattern_recognition`/`strategy_signature`/`decision_reflection`/`decision_coach`/`decision_timeline`; `comparison.py`/`exceptions.py`/`query.py` import no `sqlalchemy` at all.
- **`test_cli.py`** (6) — list-position → `ReflectionResponseId` mapping, including reprompt on non-numeric and out-of-range input; verbatim field display; an end-to-end run selecting the same entry twice prints the honest duplicate-selection message with the store's `investor_identity`/`decisions`/`reflection_responses` rows byte-identical before and after; a store with fewer than two preserved Responses prints an honest message without ever prompting for input.
- **Manual verification:** four real conversations recorded via `conversation/cli.py` (building a `same_subject_and_type`/`same_confidence` pattern, then preserving two separate Reflection Responses across two later conversations); `reflection_comparison/cli.py` run against the same store — selecting the two preserved entries displayed both complete and verbatim in deterministic chronological order; selecting the same entry twice produced the honest duplicate-selection message with the store confirmed unchanged before and after.

**Regression:** full repository suite: **7,703 passed, 3 skipped** (7,685 pre-existing + 18 new). Scoped lint: clean. Whole-repo `ruff check .` count unchanged at 1,202.

## 7. Architectural Decisions

1. **No new repository method, no `ReflectionResponseRepository.get(id)` reuse** — Reflection Comparison composes entirely from the already-owner-scoped `ReflectionHistory` value.
2. **No `composition.py`** — there is nothing to wire; `ReflectionComparisonQuery(history)` is a trivial, dependency-free constructor call.
3. **Two distinct exception types**, not one combined — "you selected the same entry twice" and "one of your selections doesn't match anything you own" are reported honestly and separately, while still never distinguishing nonexistent-from-another-investor's within the second case.
4. **Deterministic ordering is independent of selection order** — selecting B then A produces the identical result as selecting A then B.

## 8. Anything That Feels Overengineered

Nothing. The query is a single validate-then-sort function over an already-in-memory tuple.

## 9. What Can Be Simplified

Nothing further at this stage.

## 10. Genuine Risks / Unresolved Questions

- **No filtering/search/pagination** in the initial pointer list — an investor with many preserved Reflection Responses sees all of them listed at once. Explicitly out of scope per ATLAS-011-D.
- **Same disclosed simplifications ATLAS-010 already accepted carry over unchanged** — no CLI-visible reconciliation notice beyond what `resolve_investor_identity` itself already does.

## 11. Future Backlog

- Carried forward, unaffected by this increment: a retrieval interface for Investor Identity itself; re-evaluating `reasoning_link`'s placement and permanence; a REST API layer for the Core Loop; the shared structured Error Contract; the brittle hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`.

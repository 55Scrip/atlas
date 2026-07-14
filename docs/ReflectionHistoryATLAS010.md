# ATLAS-010 — Reflection History

**Status:** Implemented, pending review.
**Scope:** Standalone, read-only CLI letting an investor see every Reflection Response they've chosen to preserve (ATLAS-009), in chronological order, scoped strictly to their own durable Investor Identity (ATLAS-009B).
**Depends on:** ATLAS-010-D's authoritative Reflection History definition; `resolve_investor_identity` (ATLAS-009B), reused exactly as implemented; `ReflectionResponse`'s `add`/`get` (ATLAS-009), unchanged.

---

## 1. Purpose

Reflection Response (ATLAS-009) gave investors a way to preserve their own words against a Decision Coach question. Nothing let them look back at what they'd preserved. Reflection History closes that gap — the first genuinely new retrieval surface in this lineage, deferred once already (this session's revised ATLAS-010-P feasibility assessment) because no durable ownership boundary existed yet to scope it by.

## 2. Why This Increment Was Previously Blocked, and What Unblocked It

`Decision.user_id` — the only candidate scoping field — was populated from `ConversationSession.session_id`, re-randomized every process invocation. Scoping Reflection History by it would have fragmented one investor's own history across arbitrary per-conversation identities: a subtler, more dangerous failure than an honestly-disclosed unscoped read, because it would look correct while being wrong. ATLAS-009B removed this by making `Decision.user_id` durable, store-scoped, and reconciled for every pre-existing record. This increment is the first to build directly on that capability.

## 3. Repository Boundary

`ReflectionResponseRepository` gains exactly one additive method:

```python
class ReflectionResponseRepository(Protocol):
    def add(self, reflection_response: ReflectionResponse) -> None: ...
    def get(self, reflection_response_id: ReflectionResponseId) -> ReflectionResponse | None: ...
    def list_all_for_owner(self, user_id: UserId) -> list[ReflectionResponse]:
        """Return every ReflectionResponse anchored to a Decision owned
        by this investor. Read-only; unordered."""
        ...
```

`add`/`get` are untouched. `SqlAlchemyReflectionResponseRepository.list_all_for_owner` performs a single, read-only SQL join against `decisions_table` (`decisions.id == reflection_responses.decision_id`, filtered by `decisions.user_id`) — ownership is transitive through `decision_id`, exactly as ATLAS-009B-D §6 established; `ReflectionResponse` itself carries no `user_id`. No method was added to `DecisionRepository`. Denormalizing a `user_id` column onto `reflection_responses` directly was considered and rejected: it would duplicate data with a single source of truth and require its own migration, for no benefit a join doesn't already provide.

## 4. Bootstrap Kept Strictly Separate From Read-Only Retrieval

An early draft called `resolve_investor_identity(engine)` from inside `build_reflection_history_query` — conflating ATLAS-009B's legitimate, one-time write-capable store bootstrap (creating the identity, reconciling legacy Decisions) with what should be a purely read-only capability. Corrected before implementation:

- `reflection_history/composition.py::create_reflection_history_tables(engine)` — schema-existence only, mirroring `decision_timeline`/`pattern_recognition`'s own established `create_x_tables` convention exactly.
- `reflection_history/composition.py::build_reflection_history_query(engine, owner_user_id)` — pure object wiring given an *already-resolved* owner. Performs no writes, and cannot resolve or bootstrap Investor Identity itself — there is no code path in this module that calls `resolve_investor_identity`.
- The caller (`cli.py`) is the one place that sequences both: `resolve_investor_identity(engine)` as its own explicit, visible line, before `build_reflection_history_query(...).build()`.

A test (`test_composition.py::TestBootstrapReadOnlySeparation`) monkeypatches `SqlAlchemyInvestorIdentityRepository.resolve` to raise, then calls `build_reflection_history_query(...).build()` and confirms no exception — proving the read path never touches identity resolution at all. A second test snapshots every row in `investor_identity`, `decisions`, and `reflection_responses` before and after a `build()` call following bootstrap, asserting byte-identical state.

## 5. Application Layer

```
atlas/core/application/reflection_history/
    history.py       ReflectionHistory(entries: tuple[ReflectionResponse, ...])
    query.py         ReflectionHistoryQuery(repository, owner_user_id)
    composition.py    create_reflection_history_tables / build_reflection_history_query
    cli.py            standalone, read-only CLI
```

`ReflectionHistory.entries` holds `ReflectionResponse` directly — no `ReflectionHistoryEntry` wrapper, a real, disclosed trade-off (a future wrapper would be a breaking change to this field's element type). `ReflectionHistoryQuery` depends only on `ReflectionResponseRepository` and a plain `UserId`, never on `Engine`, mirroring `DecisionTimelineQuery`'s own established shape; it owns final `(recorded_at, id.value)` ascending ordering, never trusting repository or SQL row order.

## 6. CLI Display

Prints every persisted field of each entry completely and verbatim, under fixed, neutral labels ("Grounding Pattern:", "Strategy Signature Patterns:", etc.) — including the words "Pattern" and "Strategy Signature" themselves, since the CLI must legitimately display the stored provenance that uses those names. Nothing is truncated, reworded, or summarized; no new sentence is synthesized; no call is ever made into `pattern_recognition` or `strategy_signature` to recompute or enrich what was captured at Reflection Response's own capture time. No filtering, search, pagination, grouping, or Decision Timeline integration.

An earlier draft proposed forbidding the words "pattern"/"signature" in CLI output — rejected before implementation as self-contradictory, since the CLI must display those exact stored field values. Replaced with direct verification of actual behavior (§7).

## 7. Test Summary

26 new tests, regression-clean:

- **`test_list_all_for_owner.py`** (6) — returns only responses owned by the given investor (a differently-owned Decision/Response, inserted directly, is excluded); empty result for an owner with none; no duplicates; multiple Responses for one Decision remain separate; `response_text` round-trips byte-for-byte through the join; `provenance` round-trips exactly as persisted.
- **`test_query.py`** (4) — empty repository → empty history; out-of-order results sorted ascending by `(recorded_at, id.value)`; equal-`recorded_at` entries tie-broken by ascending `id.value`; only the injected `owner_user_id` is ever requested from the repository.
- **`test_composition.py`** (5) — end-to-end: only the current investor's own entries appear against a real engine, with a synthetic other-owner's data present but excluded; the resolved owner matches an independent call to `resolve_investor_identity`; building history after bootstrap performs no further writes (snapshot-equality proof); `build_reflection_history_query`/`.build()` never invoke `resolve_investor_identity` (monkeypatch-raises proof); later Decisions never change a previously-built entry's stored provenance.
- **`test_module_isolation.py`** (2) — AST-based (not source-text): no import from `pattern_recognition`/`strategy_signature`/`decision_reflection`/`decision_coach`/`decision_timeline`; `composition.py` imports no raw SQLAlchemy Core constructs.
- **`test_cli.py`** (6) — every persisted field appears completely and verbatim; entire per-entry output is exactly reproducible from persisted fields plus static labels (proving no interleaved generated commentary); no generated-commentary vocabulary ("trend," "conclusion," etc.) appears; `response_text` is displayed unstripped; an empty `strategy_signature_patterns` is displayed as an explicit "(none)," never silently omitted.
- **Manual verification:** three real conversations run via `conversation/cli.py` against the same `ATLAS_HOME` (two establishing a `same_subject_and_type`/`same_confidence` pattern, the third triggering Decision Reflection/Coach and an explicit "yes" to preserve the response); `reflection_history/cli.py` run directly against the same store, confirmed to display the one preserved Reflection Response with every field intact and correct owner scoping.

**Regression:** full repository suite: **7,685 passed, 3 skipped** (7,663 pre-existing + 22 new — plus the manual verification above was run against a temporary, separate database, not counted in the automated suite). Scoped lint: clean. Whole-repo `ruff check .` count unchanged at 1,202.

## 8. Architectural Decisions

1. **The owner-scoped join lives entirely inside `SqlAlchemyReflectionResponseRepository`**, not spread across an application-layer filter or a new `DecisionRepository` method — the smallest interface expressing "this owner's Reflection Responses" as one atomic read.
2. **Store bootstrap and read-only retrieval are two separate function calls, never one** — `create_reflection_history_tables`/`build_reflection_history_query` perform no writes and cannot resolve Investor Identity; only the CLI sequences both.
3. **`resolve_investor_identity` is consumed exactly as ATLAS-009B built it** — never wrapped, never re-invoked from inside a nominally read-only function, never duplicated by a parallel identity mechanism.
4. **CLI display is verbatim, not vocabulary-filtered** — correctness is verified by proving complete, unmodified field display and the absence of generated commentary, not by forbidding words the CLI must legitimately use as labels.

## 9. Anything That Feels Overengineered

Nothing. The join is a single `SELECT ... JOIN ... WHERE`; the bootstrap/read-only split adds one extra explicit line to the CLI, not a new abstraction.

## 10. What Can Be Simplified

Nothing further at this stage.

## 11. Genuine Risks / Unresolved Questions

- **No filtering/search/pagination** — an investor with many preserved Reflection Responses sees all of them at once. Explicitly out of scope per ATLAS-010-D.
- **No CLI-visible reconciliation notice** — if the first `resolve_investor_identity(engine)` call in this CLI's own run happens to be a store's first-ever use, legacy Decisions are silently reconciled (ATLAS-009B behavior, unchanged); this CLI does not add its own notice for that.
- **Single-investor local mode** — the join filters by the one durable `UserId` this store has; a future multi-investor system would need the persistence evolution ATLAS-009B-D §11 already disclaims responsibility for, not a change to this module.

## 12. Future Backlog

- A retrieval interface for Investor Identity itself, letting an investor inspect their own resolved `UserId` — not required by this or the prior increment.
- Carried forward, unaffected by this increment: re-evaluating `reasoning_link`'s placement and permanence, a REST API layer for the Core Loop, the shared structured Error Contract, the brittle hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`.
